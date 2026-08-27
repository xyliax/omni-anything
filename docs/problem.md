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

GPU 上可分配给 KV blocks 的资源是有限的，而且会话还要与模型权重、activation 和其他运行时状态共享 GPU memory。把每个会话的完整 KV 都保留在 GPU 上可以避免恢复开销，却会让总驻留量随会话数和上下文长度增长。相反，释放历史状态也不是免费的：丢弃后重新计算会把更大的 prefill 放回下一次更新的关键路径，主机回载会消耗 host-to-device 带宽和传输时间，截断上下文则改变了模型可见的交互历史。

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

随着上下文增长，每个会话的 KV cache 工作集也持续增长。当有限的 GPU KV pool 在周期计算预算之前耗尽时，系统进入 KV 容量受限区间：系统仍可能有计算余量，却无法让更多完整工作集同时驻留。该区间是否出现以及边界在哪里取决于模型、工作负载和平台；当前证据只负责证明已登记配置域中的问题实例，而不把某个实例写成问题定义。

本项目研究如何利用周期性提供的可预测下次使用时刻，在不截断上下文的前提下减少空闲会话的 GPU KV 驻留，并将释放和恢复流量安排到可用的主机链路窗口。当前原型系统暂称 **Conveyor**。已测结论、证据强度和外推边界只由 [`Findings`](findings.md) 持有。

本文中的 KV 容量受限（KV-capacity-bound）专指可分配的 GPU KV-cache 容量先耗尽，不等同于通常描述算子数据搬运强度的 memory-bound，也不等同于已经证明了跨硬件的普遍规律。

## Workload Model

### Periodic Interaction Session

会话 \(i\) 的周期为 \(T\)。第 \(k\) 次应用级更新称为 tick，其释放时刻为

\[
r_{i,k} = r_{i,0} + kT,
\]

释放偏移为 \(\phi_i = r_{i,0} \bmod T\)。一次 tick 只表示一个输入块（input chunk）在应用层变为可提交；它不规定 serving frontend 的调用方式，也不等同于引擎的一次调度迭代。

在抽象负载中，模型为更新 \((i,k)\) 生成的 token 数为 \(m_{i,k}\)，并受每周期生成上限 \(M\) 约束：

\[
0 \le m_{i,k} \le M.
\]

\(M\) 是抽象模型中的生成上限，不是最低交付量；\(m_{i,k}\) 只表示模型为该次更新生成的 token 数。模型生成进度与用户可见交付是两个不同对象：输出可以同步返回、异步推送、缓冲后消费，或经过额外的媒体处理。问题定义不选择其中一种 output architecture，也不能把一次传输或消费事件直接归属于当前输入。精确生成与交付口径由 [`Experiments`](experiments.md) 定义。

每个输入块对应一个每周期延迟目标（per-period latency target）\(D\)。这是软实时目标：偶发迟到会增加响应延迟，持续迟到会使增量结果落后于输入流。不同 output architecture 如何把这种滞后映射为 freshness、播放连续性或其他用户可见指标，属于 evaluation 定义，而不是 workload 的先验假设。

### Intrinsic Reuse Interval

若一次会话更新只占周期 \(T\) 的一部分，则该会话在相邻两次使用之间天然存在复用间隔。这个间隔来自周期性工作负载本身，不由释放偏移调度创造。

同步释放会把多会话的输入准备、计算和 KV 恢复需求集中在同一短窗口。为不同会话分配释放偏移，只是把这些需求分散到整个周期，从而提供降低瞬时并发和峰值恢复带宽的机会。它带来的实际资源收益与批处理代价都必须通过资源模型和实验验证。

## Empirical Motivation

### Capacity Before Compute

本文关注的资源区间是：持续增长的 KV working set 先逼近可用 GPU KV pool，而周期计算预算仍有余量。完整驻留在该区间中受到容量约束；整段重算或按需回载又会把恢复成本放到更新关键路径上。这个因果假设及其当前证据见 [`Findings`](findings.md#paper-relevant-findings)；其他工程瓶颈必须在实验中隔离，不能用来替代或反向定义 KV 容量主张。

### Predictable Next Use

周期 \(T\) 和释放偏移 \(\phi_i\) 让系统知道一个空闲会话预计何时再次使用 KV cache。这个信息允许系统在会话空闲时逐出部分 GPU KV，并在下次释放前或请求到达后恢复。传统请求接口只暴露当前到达和缓存命中，不直接表达应用周期及预计下次使用时刻。

## Resource Frontier

问题需要用多资源 frontier 来解释适用区间，而不是把任一测量点线性外推为普遍规律。该模型至少同时表达：

- GPU KV 容量上限；
- 周期 \(T\) 内的 prefill/decode 计算预算；
- 权重与 KV 访问造成的 HBM 带宽需求；
- host-to-device KV 恢复的链路带宽与时延包络；
- 会话数 \(N\)、上下文长度、保留 GPU 前缀 \(K\) 与释放偏移。

该模型的目标是划定 capacity、compute 和 restore-bandwidth 三类边界。如何选择平台、参数范围和校准方法由 [`Experiments`](experiments.md) 持有；[`Findings`](findings.md) 只报告已经得到证据支持的范围。

## Observability

长期会话没有可直接代表整段交互完成的单一 request-completion 事件，frontend 调用正常也不能证明模型持续推进。问题定义只固定必须可区分的语义对象，不提前冻结论文最终采用的 QoE 指标：

- 应用级输入释放与引擎准入；
- 模型执行进度与用户可见交付进度；
- GPU KV 驻留、主机后备覆盖、逐出、预取、恢复与重算；
- 会话活性、失败和观测完整性。

论文级 latency、freshness 和最大可调度并发的 operational definition 必须在 evaluation 设计中单独确定，不能从某个实现字段直接升级。

## Terminology

本节是论文核心术语的唯一词表。标准领域术语可直接使用；项目自定义术语必须在首次出现处给出对象和定义。实现标识符只用于复现与代码映射，repository-governance 词只用于证据维护，两者都不得被包装成论文贡献。

| Preferred term | 对象与精确定义 | 符号或类别 | Deprecated aliases in this project |
| --- | --- | --- | --- |
| Conveyor | 当前原型系统的暂定 proper noun，正文首字母大写 | proper noun | `conveyor` 仅限目录、配置和进程标识；`Conveyer` 拼写错误 |
| streaming interaction session | 输入和输出以连续小块到达、会话跨更新保持打开的广义服务形态；不是本文的形式化 workload | standard descriptive term | streaming request（作为一次性 request 的同义词） |
| periodic interaction session | 按目标周期持续追加输入并保留上下文、可用固定 release cadence 分析的会话 | paper-defined workload | duplex request、hard-tick foreground |
| period | 同一会话相邻两次逻辑释放之间的时间 | \(T\) | frame interval、engine tick |
| tick | 一次应用级周期更新；不指 frontend 调用或引擎调度 | application event | engine tick、RPC tick |
| release time | 会话一次输入可被提交的逻辑时刻 | \(r_{i,k}\) | phase firing time |
| release offset | 会话在周期内的稳定释放位置 | \(\phi_i\) | phase as a resource |
| release-offset scheduling | 为会话分配不同释放偏移以分散多会话需求 | research mechanism | phase staggering、phase-offset scheduling |
| input chunk | 一次应用级更新携带的新增输入 | standard term | frame（除非确为 codec frame） |
| per-period output token cap | 抽象负载中模型为一次 update 最多生成的 token 数；不定义用户可见交付量 | \(M\) | delivery quota、tokens required per tick |
| actual model output amount | 模型为会话 \(i\) 的第 \(k\) 次 update 实际生成的 token 数 | \(m_{i,k}\) | actual delivery、quota met |
| per-period latency target | 一次周期更新期望满足的软实时延迟目标 | \(D\) | hard tick deadline、inelastic deadline frame |
| engine iteration | 引擎一次 scheduler/execution 迭代 | standard implementation term | engine tick |
| GPU-resident KV blocks | 当前可在 GPU block pool 中解析和复用的 KV blocks | block coverage | resident session |
| host-backed KV blocks | 已有主机内存副本的 KV blocks；可同时仍在 GPU | block coverage | mirror、mirrored blocks |
| incremental host backing | 随上下文增长逐步把完成的 KV blocks 复制到主机 | system operation | write-through mirror |
| partial KV eviction | 释放请求所有权并逐出所选 GPU KV 尾块 | research mechanism | park、partial release、KV rotation |
| KV-cache capacity limit | GPU KV block pool 可分配容量的物理上限 | resource bound | capacity wall、capacity boundary、capacity saturation、memory cliff |
| retained GPU prefix | 空闲会话仍保留或可由 GPU prefix cache 命中的前缀 | \(K\) | resident floor、keep-K quota |
| on-demand KV reload | 输入到达后从主机恢复缺失的 KV blocks | fallback operation | wake、unpark |
| KV prefetching | 在预计复用前把 host-backed blocks 放入 GPU prefix cache | research mechanism | anonymous materialization、anonymous preload |
| evaluated system | 一个具有完整可执行语义的端到端系统身份 | evaluation term | arm（论文叙事） |
| configuration / variant | 同一系统的参数点或消融变体 | evaluation term | arm（论文叙事） |
| analytical reference scenario | 仅用于模型分析且尚未实测的参数场景 | evidence class | Paper Configuration |

`formal evidence`、`diagnostic evidence`、dirty source 和 run alias 等是 repository-governance 或 artifact 标识，不属于论文术语。具体接口、配置字段和环境变量是实现标识，论文只在复现说明中映射一次。

新增论文核心术语必须先修改本表：给出对象、定义和类别，迁移已有同义词，并通过术语防回归测试。不得先在其他文档发明新叫法，再让词表追认。

## Scope

研究聚焦周期性交互会话的 KV 驻留与恢复调度，以及可预测 next use 如何改变容量—计算—恢复带宽之间的边界。问题定义不绑定特定 modality、模型家族、output architecture、GPU 数量或设备拓扑；这些维度可以改变资源 frontier 和外部有效性，但当前 prototype 是否覆盖某一维度，不自动把它变成论文 non-goal。

机制不能消除系统总产能边界：当 offered load 超过计算、KV capacity、主机后备或恢复链路的可承载范围时，系统仍需要 admission control 或更高层的负载管理。本文不把这个物理边界包装成 KV 管理能够解决的问题。

任何模拟器、分析场景或线性外推只能帮助解释资源边界。论文主张必须回到明确配置域的真机证据，并在 [`Findings`](findings.md) 中标出实测、推导和未验证部分。
