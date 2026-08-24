# Problem

## Background

### From Turn-Based Requests to Streaming Interaction

大多数语言模型服务系统首先面对的是一次性的 request/response 工作流：客户端提交一段 prompt，服务端执行 prefill 和 autoregressive decode，返回一个完成结果，然后释放或复用这次请求的运行状态。continuous batching、prefix caching 和 paged KV allocation 都是在这类请求流上提高 GPU 利用率的关键基础设施。它们通常把请求到达、批处理和缓存块分配作为主要调度信息；请求何时结束，往往也决定了这份状态何时可以回收。

越来越多的交互式模型却不再以“一次输入、一次完整回答”为边界。典型场景包括持续聆听的语音助手、实时视频理解与辅助、在线字幕或其他连续多模态交互：输入在新内容产生时以小块到达，系统可以在输入流结束前开始处理并返回增量结果，而不必等待一个完整 turn。对这些应用而言，输出是一系列面向用户的增量结果，而不是等到输入结束后才生成的单个 completion；会话必须保留先前上下文，才能在下一次更新中继续理解同一段交互。

这不是说所有语音、视频或多模态产品都使用相同的模型、采样率或输出协议；它们只是共享一个对 serving system 重要的形状：请求长期保持打开，输入以小块增量到达，模型状态跨更新复用。本文把这种服务形状称为流式交互会话（streaming interaction session），并在需要刻画释放节奏时进一步抽象为周期性交互会话（periodic interaction session）。

| 服务形态 | 输入与输出边界 | 状态生命周期 | 主要 serving 关注点 |
| --- | --- | --- | --- |
| turn-based request | 一次输入对应一次完整响应 | 响应结束后通常可以回收请求状态 | 单次 latency、batching 和吞吐 |
| streaming interaction session | 输入和输出都由连续的小块组成 | 会话保持打开，历史状态跨更新复用 | 增量处理、连续服务和长期状态容量 |

### Why KV Cache Becomes a Capacity Constraint

Transformer 的增量执行依赖此前上下文的 attention key/value。prefill 为已经到达的上下文计算这些中间状态，后续 decode 或新的输入更新可以直接复用 KV cache，而不必每次重新计算完整历史。对一次性短请求而言，这份 cache 的生命周期通常与请求相近；对持续交互会话而言，每次新增输入经过模型的 feature extraction 和 prefill 后，都会使逻辑上下文以及对应的 KV working set 继续增长。

GPU 上的 KV block pool 是有限资源，而且多个会话要与模型权重、activation 和其他运行时状态共同使用同一张卡。把每个会话的完整 KV 都保留在 GPU 上可以避免恢复开销，却会让总驻留量随会话数和上下文长度增长。相反，释放历史状态也不是免费的：丢弃后重新计算会把更大的 prefill 放回下一次更新的关键路径，主机回载会消耗 host-to-device 带宽和传输时间，截断上下文则改变了模型可见的交互历史。

因此，持续交互引出了一个普通短请求中不明显的资源矛盾：系统需要在“保留足够状态以便低延迟继续服务”和“有限 GPU KV capacity 能承受多少长期会话”之间做选择。这个矛盾是内存容量问题，不等同于算子是否 memory-bandwidth-bound；在某些配置下，GPU KV capacity 可能先于每周期计算预算成为并发上限。

### Why Request-Level Serving Control Is Insufficient

通用 serving engine 能够根据当前到达的请求做 batching、KV block allocation 和 prefix matching，但通常不知道一个长期会话下一次何时会再次提交输入。对 streaming session 来说，这个 next-use information 很重要：会话暂时没有输入时，部分 KV 可以成为可回收空间；但如果恢复动作只能等到输入已经到达才开始，回载或重算就会直接进入该次更新的服务路径。

三个直观选择都暴露了代价：

1. **Keep everything resident.** 不增加恢复延迟，但总 KV working set 最终受 GPU capacity 限制。
2. **Recompute the history.** 不需要长期保存完整 GPU 状态，但下一次更新必须重新执行更大的 prefill，并可能超过软实时 latency target。
3. **Reload on demand.** 可以把部分状态移出 GPU，但 host-to-device transfer 发生在请求已经到达之后；多个会话同时恢复时，还可能形成瞬时链路压力。

这说明问题不只是“是否支持 KV offload”。系统还需要利用应用层已经存在的 recurrence：识别会话何时暂时空闲、为下一次使用保留哪些 GPU 状态、何时建立主机后备，以及能否在真正的输入到达之前安排恢复。本文研究的是这个 serving-systems 问题，而不是重新定义具体模型的语音、视频或对话协议。

## Problem Statement

周期性交互会话（periodic interaction session）是持续存在并按目标周期追加输入的长生命周期请求。它是上一节 streaming interaction session 在 serving 研究中的一个可分析实例：第 (k) 次更新在预定的 release time 到达，更新完成后会话不会结束，而是等待下一次输入。周期是对 workload release pattern 的抽象，不要求所有真实产品都具有完全相同的计时器或媒体协议。

随着上下文增长，每个会话的 KV cache 工作集也持续增长；在当前实测栈上，GPU KV 容量会在每周期计算饱和之前限制可并发会话数。结果是系统仍有计算余量，却无法让更多完整工作集同时驻留在 GPU 上。

本项目研究如何利用周期性提供的可预测下次使用时刻，在不截断上下文的前提下减少空闲会话的 GPU KV 驻留，并将释放和恢复流量安排到可用的主机链路窗口。当前原型系统暂称 **Conveyor**。已测结论、证据强度和外推边界只由 [`Findings`](findings.md) 持有。

本文中的 KV 容量受限（KV-capacity-bound）专指可分配的 GPU KV-cache 容量先耗尽，不等同于通常描述算子数据搬运强度的 memory-bound，也不等同于已经证明了跨硬件的普遍规律。

## Workload Model

### Periodic Interaction Session

会话 \(i\) 的周期为 \(T\)。第 \(k\) 次应用级更新称为 tick，其释放时刻为

\[
r_{i,k} = r_{i,0} + kT,
\]

释放偏移为 \(\phi_i = r_{i,0} \bmod T\)。一次 tick 只表示应用向该会话提交一个输入块（input chunk）并获得当时可交付的输出；它不表示引擎的一次调度迭代，也不等同于一次 `Step` 服务 RPC。

在抽象负载中，模型为更新 \((i,k)\) 生成的 token 数为 \(m_{i,k}\)，并受每周期生成上限 \(M\) 约束：

\[
0 \le m_{i,k} \le M.
\]

\(M\) 是抽象模型中的生成上限，不是最低交付量；\(m_{i,k}\) 只表示该次更新的模型生成量，不表示 gateway 在某次 release 实际取出的 token 数。当前 no-wait 实现记录的 `deliv` 是从未交付输出缓冲中消费的数量，取值可以为 0 到 \(M\)，而且缓冲没有 input-output identity，因而不能把 `deliv` 归属于当前输入。当前 runner 也没有证明所有交互模型都以相同方式产生静音或媒体 token。

每个输入块对应一个每周期延迟目标（per-period latency target）\(D\)。这是软实时目标：偶发迟到会增加响应延迟；在包含播放端的完整系统中，连续迟到可能逐步耗尽客户端 jitter buffer 并产生可感知卡顿。当前 Thinker-only runner 没有实现音频播放链，因此不能把 token 数或单次迟到直接宣称为已测的播放故障。

### Intrinsic Reuse Interval

若一次会话更新只占周期 \(T\) 的一部分，则该会话在相邻两次使用之间天然存在复用间隔。这个间隔来自周期性工作负载本身，不由释放偏移调度创造。

同步释放会把多会话的输入处理、计算和 KV 恢复需求集中在同一短窗口。为不同会话分配释放偏移，只是把这些需求分散到整个周期，降低瞬时并发和峰值恢复带宽需求。是否真正降低了恢复流量峰值仍需 trace 和资源模型验证；当前证据首先支持它对输入处理惊群的缓解。

### Current Measured Instance

当前可执行实例使用音频输入驱动 Qwen2.5-Omni 的持续 resumable request。worker 只读取 Thinker 文本输出；Talker、Code2Wav 和 PCM 音频交付均不在当前路径中。因此，本仓库目前测量的是“具有音频输入的周期性交互模型实例”，而不是已经闭合的端到端全双工语音产品。

其他交互模型、视频输入或语音输出是否满足同一资源关系仍是待验证的外部有效性问题。未来系统可以把异步外部结果追加到会话上下文并执行 prefill，但该功能当前未实现，也不是当前问题定义、机制或贡献的一部分。

## Empirical Motivation

### Capacity Before Compute

当前实测栈显示：持续增长的 KV 工作集先逼近 GPU KV pool 容量，而每周期 GPU 计算仍有余量。默认全驻留方式因容量不足无法增加并发会话；整会话换入换出或整段重算又可能把恢复成本放到请求关键路径上。需要解决的核心矛盾是“容量先于计算限制并发”，不是某个未修改 baseline 出现的特定队列故障。

host-side feature extraction 也可能造成拥堵，但它可以通过并行 input processing 修复，属于实验必须排除的工程瓶颈，不是 KV 容量主张本身。具体证据和限定见 [`Findings`](findings.md#paper-relevant-findings)。

### Predictable Next Use

周期 \(T\) 和释放偏移 \(\phi_i\) 让系统知道一个空闲会话预计何时再次使用 KV cache。这个信息允许系统在会话空闲时逐出部分 GPU KV，并在下次释放前或请求到达后恢复。传统请求接口只暴露当前到达和缓存命中，不直接表达应用周期及预计下次使用时刻。

## Resource Frontier

论文最终需要一个经实测 primitive 校准的多资源 roofline 模型，而不是把当前 GPU 上的线性外推称作普遍证明。模型至少需要同时表达：

- GPU KV 容量上限；
- 周期 \(T\) 内的 prefill/decode 计算预算；
- 权重与 KV 访问造成的 HBM 带宽需求；
- host-to-device KV 恢复的 PCIe 带宽包络；
- 会话数 \(N\)、上下文长度、保留 GPU 前缀 \(K\) 与释放偏移。

该模型的目标是划定 capacity、compute 和 restore-bandwidth 三类边界，并用多种硬件 profile 或至少额外硬件上的 primitive 测量校准。目前它是明确的 evaluation requirement，不是已经完成的理论结果。

## Observability

周期性通道没有天然的请求完成事件，服务 RPC 正常返回也不能证明模型输出持续更新。当前阶段只固定必须观察的对象，不提前冻结论文最终采用的 QoE 指标：

- 每会话输入释放与引擎准入；
- prefill、decode 和引擎调度迭代；
- GPU KV block 驻留、主机后备覆盖、逐出与恢复；
- 生成量、实际交付量与未交付输出缓冲增长；
- session death、RPC error 和 artifact 完整性。

论文级 freshness、播放卡顿和最大可调度并发的 operational definition 必须在 evaluation 设计中单独确定，不能从当前诊断字段直接升级。

## Terminology

本节是论文核心术语的唯一词表。标准领域术语可直接使用；项目自定义术语必须在首次出现处给出对象和定义。实现标识符只用于复现与代码映射，repository-governance 词只用于证据维护，两者都不得被包装成论文贡献。

| Preferred term | 对象与精确定义 | 符号或类别 | Deprecated aliases in this project |
| --- | --- | --- | --- |
| Conveyor | 当前原型系统的暂定 proper noun，正文首字母大写 | proper noun | `conveyor` 仅限目录、配置和进程标识；`Conveyer` 拼写错误 |
| streaming interaction session | 输入和输出以连续小块到达、会话跨更新保持打开的广义服务形态；不是本文的形式化 workload | standard descriptive term | streaming request（作为一次性 request 的同义词） |
| periodic interaction session | 按目标周期持续追加输入并保留上下文、可用固定 release cadence 分析的会话 | paper-defined workload | duplex request、hard-tick foreground |
| period | 同一会话相邻两次逻辑释放之间的时间 | \(T\) | frame interval、engine tick |
| tick | 一次应用级周期更新；不指引擎调度 | application event | engine tick、Step tick |
| release time | 会话一次输入可被提交的逻辑时刻 | \(r_{i,k}\) | phase firing time |
| release offset | 会话在周期内的稳定释放位置 | \(\phi_i\) | phase as a resource |
| release-offset scheduling | 为会话分配不同释放偏移以分散多会话需求 | research mechanism | phase staggering、phase-offset scheduling |
| input chunk | 一次应用级更新携带的新增输入 | standard term | frame（除非确为 codec frame） |
| per-period output token cap | 抽象负载中模型为一次 update 最多生成的 token 数；不定义 gateway 的实际交付量 | \(M\) | delivery quota、tokens required per tick |
| actual model output amount | 模型为会话 \(i\) 的第 \(k\) 次 update 实际生成的 token 数 | \(m_{i,k}\) | actual delivery、quota met |
| per-period latency target | 一次周期更新期望满足的软实时延迟目标 | \(D\) | hard tick deadline、inelastic deadline frame |
| engine iteration | 引擎一次 scheduler/execution 迭代 | standard implementation term | engine tick |
| service RPC | gateway 与 worker 之间的一次调用；当前方法名为 `Step` | implementation term | tick（作为 RPC 同义词） |
| GPU-resident KV blocks | 当前可在 GPU block pool 中解析和复用的 KV blocks | block coverage | resident session |
| host-backed KV blocks | 已有主机内存副本的 KV blocks；可同时仍在 GPU | block coverage | mirror、mirrored blocks |
| incremental host backing | 随上下文增长逐步把完成的 KV blocks 复制到主机 | system operation | write-through mirror |
| partial KV eviction | 释放请求所有权并逐出所选 GPU KV 尾块 | research mechanism | park、partial release、KV rotation |
| KV-cache capacity limit | GPU KV block pool 可分配容量的物理上限 | resource bound | capacity wall、capacity boundary、capacity saturation、memory cliff |
| retained GPU prefix | 空闲会话仍保留或可由 GPU prefix cache 命中的前缀 | \(K\) | resident floor、keep-K quota |
| on-demand KV reload | 输入到达后从主机恢复缺失的 KV blocks | fallback operation | wake、unpark |
| KV prefetching | 在预计复用前把 host-backed blocks 放入 GPU prefix cache | research mechanism | anonymous materialization、anonymous preload |
| initial-context preloading | 测量前通过 prefill 构造指定长度的初始上下文 | evaluation setup | seed、warm-start seed |
| undelivered-output buffer | 已生成但尚未交付给 gateway 的输出队列 | implementation state | inventory、stock |
| evaluated system | 端到端实现身份，例如 matched Metronome baseline 或 Conveyor | evaluation term | arm（论文叙事） |
| configuration / variant | 同一系统的参数点或消融变体 | evaluation term | arm（论文叙事） |
| analytical reference scenario | 仅用于模型分析且尚未实测的参数场景 | evidence class | Paper Configuration |

`formal evidence`、`diagnostic evidence`、dirty source、run alias 和 `paringest` 等是 repository-governance 或 artifact 标识，不属于论文术语。`Step`、protobuf 字段和环境变量是实现接口，论文只在复现说明中映射一次。

新增论文核心术语必须先修改本表：给出对象、定义和类别，迁移已有同义词，并通过术语防回归测试。不得先在其他文档发明新叫法，再让词表追认。

## Scope

当前研究聚焦单 GPU 上的周期性交互会话、KV 容量和恢复调度。它不把语音合成头、音频 tokenization、多卡 prefill/decode 分离、后台结果追加、应用级 cancellation 或 admission control 作为当前贡献。超过系统总产能时仍需要 admission control；该边界不由 KV 管理机制消除。

任何模拟器、分析场景或线性外推只能帮助解释资源边界。论文主张必须回到明确配置域的真机证据，并在 [`Findings`](findings.md) 中标出实测、推导和未验证部分。
