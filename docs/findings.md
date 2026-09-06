# Findings

## Current State

| 候选机制 | 已实现语义 | 当前证据支持 | 尚未支持 |
| --- | --- | --- | --- |
| 释放偏移调度（release-offset scheduling） | 稳定 release offset 与绝对时间网格 | 配置域限定的 offered-arrival burst 缓解 | KV restore demand 的平滑收益与外部有效性 |
| 带主机后备的 KV 部分逐出（partial KV eviction with host backing） | 增量 host backing、idle eviction、reload/recompute fallback | 诊断证据中的 idle-session GPU residency 降低 | 公平 workload 下的 capacity frontier 与 formal performance evidence |
| KV 预取（KV prefetching） | capacity deferral、提前恢复、on-demand fallback | 源码语义审计 | 稳定净延迟收益与高压资源协调 |

上表只列可能支撑 paper claim 且可以独立消融的机制。output-delivery polling、transport identity、cache-key registration、runtime compatibility fix 和 observation instrumentation 是 implementation choices 或测量修复，不进入机制列表。

## Evidence Scope

当前已登记的 paper-relevant evidence 由 `legacy-unreconstructable` 与 `source-audit` 构成，只能承担诊断或语义审计作用；目前没有可直接升级为最终性能主张的 formal evidence。每条 finding 必须通过其 `EVIDENCE-*` alias 解析精确模型、输入与输出路径、平台、参数、source state 和 provenance；本文不手工复制这些易变配置。

这种配置域限定是对结论强度的约束，不是对研究范围的定义。当前 prototype 没有覆盖某个 modality、output architecture、硬件或拓扑，只能说明该维度尚无证据，不能自动把它改写成论文 non-goal。正式实验矩阵、evaluated systems、公平性缺陷和指标协议只由 [`Experiments`](experiments.md) 持有。

## Paper-Relevant Findings

<a id="finding-a1"></a>
### FINDING-A1：串行输入处理会掩盖 KV 容量瓶颈

如果不同会话的输入准备被一个串行执行点限制，host-side queue 可能先于 GPU KV capacity 限制 offered load。容量实验必须隔离这一混淆因素；否则测得的是输入管线瓶颈，而不是长期 KV working set 的容量边界。该瓶颈不是 Conveyor 的研究机制。

证据：`EVIDENCE-LEGACY-BASELINE`。

<a id="finding-a2"></a>
### FINDING-A2 — 跨会话并行输入处理可以消除该混淆因素

在保持单会话输入顺序的同时并行处理不同会话，可以移除已观察到的串行输入瓶颈。共享 runtime contention 仍可能扩大 tail，因此 matched comparison 必须使用等价的 input-processing semantics。这个公平性修复不构成研究贡献。

证据：`EVIDENCE-LEGACY-BASELINE` 与 `EVIDENCE-H1-COMPARISON`。

<a id="finding-b1"></a>
### FINDING-B1：周期事件正常不等于模型仍在产生新 token

应用 release 和 frontend 调用可以持续发生，即使某个会话已经停止产生新的模型进度。调用 cadence 只能证明控制或传输路径仍然活着，不能替代逐会话 liveness、model progress 和 scheduler-state 观测。

证据：`EVIDENCE-LEGACY-BASELINE`。

<a id="finding-b2"></a>
### FINDING-B2 — Frontend 调用延迟不等于输出新鲜度

当前 delivery path 的调用延迟在本次输入完成模型工作之前结束，且缓冲输出没有足以把可见结果唯一关联到当前输入的 identity。论文若需要 content freshness，必须定义跨层关联和明确的终点，不能从调用返回、引擎活动或单次消费量反推。

证据：`EVIDENCE-H2-METRICS`。

<a id="finding-c1"></a>
### FINDING-C1 — 引擎迭代本身不知道应用周期

周期结构由引擎外部的 release pattern 塑形。serving engine 看到 scheduler iterations、prefill 与 decode，却不天然知道应用的 \(T\)、\(\phi_i\) 或 \(D\)。trace 和论文必须区分 application tick、frontend invocation 与 engine iteration。

证据：`EVIDENCE-LEGACY-BASELINE`。

<a id="finding-c2"></a>
### FINDING-C2 — 当前跨系统诊断没有执行相同的模型工作

当前两个 first-party evaluated systems 的每次更新生成上限并不相同，因此实际 decode work 和未交付输出增长也不同。现有跨系统 run 只能用于诊断，不能称作相同 workload 下的公平性能比较；精确差异和修复协议见 [`Experiments`](experiments.md#executed-decode-difference)。旧证据必须保留原语义，不能通过改文档伪装成已经匹配。

证据：`EVIDENCE-LEGACY-BASELINE` 与当前 source audit。

<a id="finding-c3"></a>
### FINDING-C3 — 调度并发语义必须在比较中匹配

会改变 KV ownership 或 residency 的 policy 可能与并发 scheduler iteration 发生竞态。当前实现需要一种明确的调度语义来保证逐出安全，因此所有 control configuration 必须使用等价 scheduler mode。具体 runtime 设置属于实验协议，而不是机制定义。

source audit 对风险面的细化：retained-prefix 主路径的逐出在 scheduler 线程内执行，不经过 worker utility RPC；vLLM 0.23 的异步调度对 max-tokens 停止自带保护检查（基础调度器按输出占位计数拒绝多调度一步），而 measured path 只使用 max-tokens 停止。该检查未覆盖 EOS/stop-string 停止、fixed-tail utility RPC 模式与在途 host store 拷贝。异步调度对主路径的安全性因此是待 clean run 验证的命题，而不是已排除的选项；验证之前同步强制与匹配要求不变。

证据：`EVIDENCE-LEGACY-BASELINE`、`EVIDENCE-H3-KV-EVICTION-SEMANTICS` 与 `EVIDENCE-EXEC-MODEL-AUDIT`。

<a id="finding-d1"></a>
### FINDING-D1 — 已登记诊断域中出现了容量先于计算的区间

至少一个已登记诊断配置在 GPU KV pool 接近耗尽时仍保留周期计算余量。这支持“capacity before compute”作为一个真实问题实例，但不证明所有模型、工作负载、平台或设备拓扑都会落入同一区间。

跨配置主张必须同时核算 KV capacity、period compute、HBM traffic 和 host-to-device restore bandwidth。

证据：`EVIDENCE-LEGACY-BASELINE`。

<a id="finding-d2"></a>
### FINDING-D2：KV 工作集字节数能够解释容量边界

历史测量中，不同 session-count/context-length 组合在接近相同总 KV token 数时触及 GPU pool 边界。这支持以总 KV working-set bytes 作为 capacity axis，而不是把 session count 本身当作物理资源。正式结论仍需要在公平协议下重新测量。

证据：`EVIDENCE-LEGACY-BASELINE`。

<a id="finding-d3"></a>
### FINDING-D3：Release offsets 以批处理聚合换取更低瞬时需求

将 release 分散到周期内可能减小同步 batch，并增加权重重复读取的机会；同时它为降低同时 GPU-resident 的 session 数和分散 restore demand 提供时序条件。这个 trade-off 必须由 compute、HBM 和 host-to-device restoration 三类资源共同核算。

当前证据支持 offered-arrival burst 的降低，尚不足以单独支持 KV restore bandwidth 已经被平滑的性能主张。

证据：`EVIDENCE-H1-COMPARISON` 与 `EVIDENCE-LEGACY-BASELINE`。

<a id="finding-d5"></a>
### FINDING-D5：非 KV 显存占用决定可用 KV 池大小

GPU memory budget 同时包含模型权重、activation、runtime reserve 和 KV pool。任何 capacity 模型都必须从实测可用 KV pool bytes 出发，不能用设备标称显存直接除以每会话 KV bytes。

证据：`EVIDENCE-LEGACY-BASELINE`。

<a id="finding-e1"></a>
### FINDING-E1：decode 步在 CUDA graph 内执行，含 prefill 的步实际全部图外执行

baseline worker 在引擎几何参数之外只设置 `enforce_eager=False`；Conveyor worker 另外启用 prefix caching、CPU offload connector，并强制同步调度（[`FINDING-C3`](#finding-c3)）。两者的组批与 CUDA graph 行为一致，来自 vLLM 0.23 默认值：调度器把 prefill 与 decode 聚合进同一 token 预算，CUDA graph 捕获上限按 `min(2*max_num_seqs, 512)` 推导，本配置为 32。uniform decode 步回放 FULL graph；单个 2 s 输入 chunk 的增量 prefill 为 53 token，已超过捕获上限，因此含 prefill 的步以 torch.compile eager 方式按精确形状执行。含 prefill 的步指存在单请求调度量大于 1 token 的步，包括启动期的 initial-context 文本块。retained 的两个 run 中，超过上限的这类步分别为 200/202（baseline）与 499/507（Conveyor）。两系统行为一致，图覆盖差异不构成跨系统混淆因素。引擎默认行为的完整整理见 [`vLLM 0.23 执行与捕获行为`](references/vllm-023-execution-and-capture.md)。

证据：`EVIDENCE-EXEC-MODEL-AUDIT` 与 `EVIDENCE-STEP-TIMING-RETAINED`。

<a id="finding-e2"></a>
### FINDING-E2：decode 步时长被每步全量权重读取决定，对 batch size 几乎不敏感

retained 诊断 run 中，decode-only 步 p50 约 23.5-23.7 ms（Conveyor 同步调度下测得的是步延迟；baseline 异步调度下测得的是吞吐归因下界），每增加一个并发 decode 序列仅 +0.66 ms。该形状与每步完整读取一遍 bf16 权重（约 15 GB）的带宽下限一致；decode 步已在 FULL graph 内，该下限不是 launch 开销，图类优化无法降低它。它同时量化了 [`FINDING-D3`](#finding-d3) 中“错开释放增加权重重复读取次数”的单步代价：Conveyor retained run 每周期 62.1 个 decode 步，baseline 为 32.3 个。配置域限定于 retained 诊断 run，精确模型、平台与参数由 `EVIDENCE-STEP-TIMING-RETAINED` 解析；跨系统 decode cap 不同（[`FINDING-C2`](#finding-c2)），不构成公平比较。

证据：`EVIDENCE-STEP-TIMING-RETAINED`。

<a id="finding-e3"></a>
### FINDING-E3：含 prefill 的步带有固定成本与 64-token 形状台阶；Conveyor retained 点每周期无空闲

Conveyor 同步调度测量（n=487）：不超过 64 总 token 的单 chunk 恢复步 p50 约 60 ms，总 token 跨过 64 后每步再 +10.67 ms（形状台阶，分解拟合 R²=0.944），每 chunk 边际计算 10-12 ms，超出已入图 decode 下限的固定成本约 18-20 ms/步。每周期占用分解：Conveyor 为 1480 ms decode 加 520 ms prefill，空闲为 0（占用 100%）；baseline 约 1024 ms 活跃加 970 ms 空闲。Conveyor 每周期支付 8 次 prefill 步固定成本（错开释放使每 chunk 单独成步），baseline 约 3 次（同步到达聚合成 burst）。限制：单 run；跨系统 cap 与调度模式不同（C2/C3），该占用分解是各自的诊断性成本结构，不能读作容量或公平比较结论。

证据：`EVIDENCE-STEP-TIMING-RETAINED`。

<a id="finding-e4"></a>
### FINDING-E4：Conveyor 恢复 prefill 的可变余量有精确算术，实测每周期净增长与 workload 常数差 1

Conveyor 每次恢复的增量 prefill 等于 chunk 长度 + 1 + ((C−1) mod 16)，C 为该段停止时的 computed token 数；余量取值 [1,16]，retained run 62 个稳态周期中 58 个严格命中该式。机制来源是 vLLM 0.23 的三条语义（见 [`vLLM 0.23 执行与捕获行为`](references/vllm-023-execution-and-capture.md)）：未写满的尾 block 无 hash、不可注册或 host 备份，`free` 后销毁；恰好写满的末 block 因 eager store 滞后一步错过备份；段末已采样未回喂的 token 在流式折叠时被引擎丢弃，因此 baseline 恢复恰为 chunk 长度、无余量。丢弃语义还意味着每周期净上下文增长为 53+(M−1)=77 token，而 `experiments/shared/workload.py` 的 `CONTEXT_GROWTH_TOKENS_PER_PERIOD=78` 按 53+M 记，二者差 1；余量在 16 个取值上均匀轮转（77 与 16 互素）与实测分布一致，且逐会话相邻恢复尺寸之差恒 ≡ 13 (mod 16)（8 会话共 465 组间隔中 464 组吻合）。修正该常数属于实验协议变更，须另行事务。余量叠加同批 decode 后使 43% 的恢复步跨过 [`FINDING-E3`](#finding-e3) 的 64-token 台阶。

证据：`EVIDENCE-EXEC-MODEL-AUDIT` 与 `EVIDENCE-STEP-TIMING-RETAINED`。

<a id="finding-f7"></a>
### FINDING-F7 — 生成与消费不匹配会积累未交付输出

当模型生成进度长期快于 output path 的消费或交付进度时，未交付结果会持续积累。该现象说明生成与消费配置必须成对报告，也说明 frontend cadence 不能代表输出对应的输入年龄。当前生成与消费配置的具体差异由 [`Experiments`](experiments.md#executed-decode-difference) 持有。

backlog 是实现诊断量；论文是否采用 freshness 指标以及如何定义，仍由 Evaluation 决定。

证据：`EVIDENCE-H2-METRICS`。

<a id="finding-h1"></a>
### FINDING-H1：Release offsets 降低了实测输入处理突发

保留的诊断比较显示，绝对 release grid 能把同步到达分散到周期内，并降低 input-processing contention。该证据说明 release offsets 能控制 offered-arrival structure；它没有直接测得 KV restore bandwidth 峰值，也不满足当前 formal provenance 标准。

证据：`EVIDENCE-H1-COMPARISON`。

<a id="finding-h2"></a>
### FINDING-H2 — 当前交付路径改变了指标含义

当前 frontend latency 只覆盖输入提交与当时可见输出的取得，不覆盖当前输入后续的完整模型工作。继承的成功字段也只能表示调用是否及时返回，不能升级为论文级 latency、freshness 或 QoE 结论；各交付相关字段的当前语义与禁止解释由 [`Experiments`](experiments.md#measurement-semantics) 持有。

证据：`EVIDENCE-H2-METRICS`。本条是测量语义发现，不是研究机制。

<a id="finding-h3"></a>
### FINDING-H3 — 现有引擎原语能够实现部分 KV 逐出与恢复

源码审计表明，现有 request ownership、GPU prefix reuse 和 host offload 原语足以组合出所需语义：idle 后释放所有权，逐出选定 GPU tail，下一次使用先复用 GPU prefix，再恢复连续 host-backed blocks；coverage gap 之后通过重算恢复。

Conveyor 增加的是 idle-transition policy、持续会话下的 host-coverage 维护、状态观测和控制接口；它不声称发明 prefix caching 或 host offload。

证据：`EVIDENCE-H3-KV-EVICTION-SEMANTICS`。

<a id="finding-h4"></a>
### FINDING-H4 — 保留前缀逐出降低了诊断点的闲置会话 GPU 驻留

保留的诊断 run 中，启用 retained-prefix eviction 后，GPU KV occupancy 从接近 pool 极限的增长转为明显更低的锯齿稳态。这支持机制能够释放 idle-session residency，但现有证据不满足当前 formal 标准，跨系统 model work 也未匹配，因此不能直接作为论文容量提升主结果；精确配置与数值由 `EVIDENCE-H4-RESIDENCY` 解析。

证据：`EVIDENCE-H4-RESIDENCY`。

<a id="finding-h5"></a>
### FINDING-H5 — 按需恢复会进入更新关键路径

on-demand restore 只能在真实 demand 出现之后开始，因此 copy cost 和链路排队会进入该次更新的 admission critical path；任何先于恢复完成的必要输入工作还会与其串行累积。随着需恢复 KV 增加，这些成本必须进入 restore-bandwidth frontier。预取的潜在价值正是改变恢复时序，而不是消除其资源成本。

证据：`EVIDENCE-H5-CRITICAL-PATH`。

<a id="finding-h6"></a>
### FINDING-H6 — 测量状态构造必须与稳态机制分离

为了从指定上下文状态开始测量，状态构造必须在周期输入开始前完成，并与正常 idle eviction 的状态转换分开。构造屏障只建立合法起点，不能被包装成 Conveyor 机制；其精确协议与失败条件由 [`Experiments`](experiments.md#initial-context-preloading) 持有。

证据：`EVIDENCE-H6-INITIAL-CONTEXT`。本条属于 evaluation state construction。

<a id="finding-h7"></a>
### FINDING-H7：KV 预取语义已完整但性能结论未定

源码审计支持以下正确性语义：host-backed blocks 可以提前进入 GPU cache，并由之后的正常 cache reuse 使用；capacity deferral、input overtaking 和 later eviction 都安全退化为 on-demand restore 或 recomputation。具体 transport 和 cache registration 方式是实现细节。

历史性能 artifacts 不完整，现有证据只能支持语义检查。输入准备、copy overlap、capacity pressure 与 cache reuse 的共同作用尚未形成可复现的净延迟结论。

证据：`EVIDENCE-H7-PREFETCH`，registry 角色为 `legacy-unreconstructable`；当前源码只能补充 semantic audit，不能补出遗失的性能证据。

## Diagnostic Boundary

旧队列故障、一次性调试参数和过时 workload story 只保存在冻结的 [`legacy-experiment-log.md`](agent/legacy-experiment-log.md) 或不可变 `results/` 中。它们不能作为当前 paper prose source，也不能用于定义研究范围或证明研究问题的重要性。

Agent 引用 finding 时必须保留完整 `FINDING-*` ID、证据角色、配置域和限制，并通过 evidence registry 解析精确配置。若 finding 与新的 clean run 冲突，应更新本 owner 和 registry，而不是在 README、Problem 或 System 中复制第二个版本。
