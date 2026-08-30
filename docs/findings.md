# Findings

## Current State

| 候选机制 | 已实现语义 | 当前证据支持 | 尚未支持 |
| --- | --- | --- | --- |
| 释放偏移调度（release-offset scheduling） | 绝对网格与稳定 release offset | 缓解当前栈的 input-processing burst | KV restore bandwidth 平滑、跨硬件收益 |
| 带主机后备的 KV 部分逐出（partial KV eviction with host backing） | 增量 host backing、idle-transition eviction、on-demand reload/recompute fallback | 当前测量点的 GPU-residency 降低 | 统一 decode work 后的容量 frontier 与正式重复实验 |
| KV 预取（KV prefetching） | release-time issue、capacity deferral、prefix-cache reuse、on-demand fallback | 源码语义可审计 | 稳定净延迟收益、高压 pacing 和 formal evidence |

上表只列可能支撑 paper claim 且可以独立消融的机制。Conveyor 的 no-wait `Step`、合成 transport ID、hash registration、streaming `max_tokens` 修复和 observation patch 都是 implementation choices 或测量修复，不进入机制列表。

## Evidence Scope

当前保留证据主要来自单张 RTX 3090、Qwen2.5-Omni Thinker-only 路径和历史诊断 run。部分 run 不满足现在的 clean-source formal 标准，registry 已按 `diagnostic` 或 `legacy-unreconstructable` 降级。以下数字只能在各 finding 的配置域内使用；它们不能直接组成论文 Evaluation。

正式论文结果仍缺少：

- matched baseline 与 Conveyor 统一的 per-segment decode cap；
- 面向 \(N\)、context length 和 retained prefix \(K\) 的完整 sweep；
- 重复运行与统计不确定性；
- capacity / compute / HBM / PCIe 的多资源 roofline；
- 至少一个额外 hardware profile 的校准或验证；
- 论文级 latency、freshness 和 schedulability 定义。

当前 runner 只返回 Thinker 文本 token。本仓证据还不支持任何关于 audio playback、jitter-buffer stall、静音 token 或端到端全双工语音体验的结论。

## Paper-Relevant Findings

<a id="finding-a1"></a>
### FINDING-A1 — 串行输入处理会掩盖 KV 容量瓶颈

旧 worker 把每个 audio chunk 的 input processing 串行放在事件循环上，多会话到达时会先形成 host-side queue。这个瓶颈能在 GPU KV capacity 之前限制并发，因此正式容量实验必须使用 matched input-processing path。它是需要排除的工程混淆因素，不是 Conveyor 的容量机制。

证据：`EVIDENCE-LEGACY-BASELINE`。

<a id="finding-a2"></a>
### FINDING-A2 — 并行输入处理消除了该混淆因素

`paringest` 把不同会话的 input processing 移到线程池，并保持单会话输入顺序。隔离测量表明 feature extraction 可以跨会话并发；共享进程中的 GIL 和 event-loop contention 仍可能扩大 tail。该修复定义 matched Metronome baseline 的公平性前提，不构成研究机制。

证据：`EVIDENCE-LEGACY-BASELINE` 与 `EVIDENCE-H1-COMPARISON`。

<a id="finding-b1"></a>
### FINDING-B1 — 周期事件正常不等于模型仍在产生新 token

周期事件和 service RPC 可以持续正常返回，即使某个 session 已停止产生新 token。client cadence 因而只证明 transport loop 仍在运转；它不能替代 session liveness、token growth 和 scheduler-state 观测。当前 runner 已把 session death、RPC error 和 client artifact failure 作为 repository health gate。

证据：`EVIDENCE-LEGACY-BASELINE`。

<a id="finding-b2"></a>
### FINDING-B2 — Service RPC 延迟不等于输出新鲜度

Conveyor 的 no-wait `Step` 在提交当前输入后立即快照未交付输出，因此 RPC latency 不包含该输入对应的 GPU work。未交付输出缓冲也没有显式的 input-output identity。论文若需要 content freshness，必须增加可操作的关联方法，不能从 `deadline_met`、`gpu_ms` 或单次 `deliv` 反推。

证据：`EVIDENCE-H2-METRICS`。

<a id="finding-c1"></a>
### FINDING-C1 — 引擎只看到迭代而不知道应用周期

持续 session 的周期结构由引擎外部的 gateway release 和 streaming input 决定。EngineCore 只看到 scheduler iterations、prefill 与 decode，不知道应用的 \(T\)、\(\phi_i\) 或 \(D\)。trace 和论文必须区分 application tick、service RPC 与 engine iteration。

证据：`EVIDENCE-LEGACY-BASELINE`。

<a id="finding-c2"></a>
### FINDING-C2 — 当前 matched baseline 执行了更大的 decode 上限

vLLM resumable request 的 `max_tokens` 在每个 streaming segment 重新计数。两个当前 first-party worker 都设置 `ignore_eos=True`，正常 measured path 因而运行到各自每段 cap，而不是用来观测自然短输出；两个 evaluated systems 的 cap 当前不同，具体数值与比较资格由 [`Experiments`](experiments.md#executed-decode-difference) 持有。该差异改变实际 decode work，并使 matched baseline 的未交付输出缓冲以固定差额增长。model-length 边界和异常终止等例外必须另行诊断。

因此，现有跨系统 run 只能用于诊断，不能称作相同 workload 下的最终公平比较。修复必须在新的实验事务中统一 cap 并重跑，不能改写旧证据。

证据：`EVIDENCE-LEGACY-BASELINE` 与当前 source audit。

<a id="finding-c3"></a>
### FINDING-C3 — 调度模式必须显式匹配

当前 vLLM 版本在未显式设置时可能启用 asynchronous scheduling。Conveyor 的 block eviction 与正在执行的 speculative iteration 存在竞态，因此当前实现强制 synchronous scheduling。任何 eviction ablation 都必须给 control configuration 使用相同 scheduling mode。

证据：`EVIDENCE-LEGACY-BASELINE` 与 `EVIDENCE-H3-KV-EVICTION-SEMANTICS`。

<a id="finding-d1"></a>
### FINDING-D1 — 当前实测栈在计算尚有余量时触及 KV 容量边界

在当前 RTX 3090 与 Qwen2.5-Omni Thinker 配置上，GPU KV pool 接近耗尽时，每周期仍存在明显 compute headroom。该 observation 支持“capacity before compute”作为本硬件上的问题实例，但不能单独证明所有硬件和模型都如此。

跨硬件主张需要把 KV capacity、period compute、HBM traffic 和 PCIe restore bandwidth 放入统一 roofline，并用额外 profile 校准。

证据：`EVIDENCE-LEGACY-BASELINE`。

<a id="finding-d2"></a>
### FINDING-D2 — KV 工作集字节数能够解释容量边界

历史测量中，不同 session-count/context-length 组合在接近相同总 KV token 数时触及 GPU pool 边界。这支持以总 KV working-set bytes 作为 capacity axis，而不是把 session count 本身当作物理资源。

证据：`EVIDENCE-LEGACY-BASELINE`。正式结论需要统一 decode cap 后重新 sweep。

<a id="finding-d3"></a>
### FINDING-D3 — Release offsets 以批处理聚合换取更低瞬时需求

将 release 分散到周期内会减小同步 batch，并增加权重重复读取的机会；同时它为降低同时 GPU-resident 的 session 数和分散 restore demand 提供时序条件。这个 trade-off 必须由 compute、HBM 和 PCIe 三类资源共同核算。

当前证据直接支持 input-processing release burst 的降低，不足以单独支持“KV restore bandwidth 已被平滑”这一性能主张。

证据：`EVIDENCE-H1-COMPARISON` 与 `EVIDENCE-LEGACY-BASELINE`。

<a id="finding-d5"></a>
### FINDING-D5 — 非 KV 显存占用决定可用 KV 池大小

当前 GPU memory budget 同时包含模型权重、未参与本路径输出的模型组件、activation 和 KV pool。任何 capacity 模型都必须从实测可用 KV pool bytes 出发，不能用物理显存总量直接除以每会话 KV bytes。

证据：`EVIDENCE-LEGACY-BASELINE`。

<a id="finding-f7"></a>
### FINDING-F7 — 生成与消费上限不一致会积累未交付输出

当 worker 的每段生成上限高于 gateway 的每周期消费上限时，未交付输出缓冲可以持续增长；当前配置差异由 [`Experiments`](experiments.md#executed-decode-difference) 持有。该现象说明生成与消费配置必须一起报告，也说明 RPC cadence 不能反映输出对应的输入已经过去多久。

`output_backlog` 是实现诊断量；论文最终是否采用 freshness 指标以及如何定义仍由 Evaluation 决定。

证据：`EVIDENCE-LEGACY-BASELINE`。

<a id="finding-h1"></a>
### FINDING-H1 — Release offsets 降低了实测输入处理突发

在历史 \(N=8\)、initial context length=4096、120 s 诊断配置中，绝对 release grid 把同步到达分散到周期内，并降低了 feature-extraction contention。该证据说明 release offsets 能控制 offered-arrival structure；它没有直接测得 KV restore bandwidth 峰值。

证据：`EVIDENCE-H1-COMPARISON`。保留 manifest 不满足新的 clean-source formal 标准，需重跑。

<a id="finding-h2"></a>
### FINDING-H2 — 无等待交付改变了指标含义

Conveyor 的 `Step` latency 测量入队与输出快照，不包含当前 input 的 feature extraction、KV restore、prefill 或 decode。历史 `deadline_met = delivered >= M` 把 output cap 错当成最低 requirement，已经从新 run 的 correctness gate 中删除。

新 gateway 的继承字段 `deadline_met` 只报告 service RPC 是否在 period 内返回；它仍不是论文级 latency 或 QoE 结论。

证据：`EVIDENCE-H2-METRICS`。本条是测量语义发现，不是研究机制。

<a id="finding-h3"></a>
### FINDING-H3 — 现有 vLLM 原语能够实现部分 KV 逐出与恢复

当前补丁组合 `free(request)`、`evict_blocks`、GPU prefix match 与 `SimpleCPUOffloadConnector`：先释放 request ownership，再逐出选定 GPU tail，下一输入先复用仍在 GPU 的 prefix，再加载连续 host-backed blocks。首个 host-coverage gap 之后退化为 recomputation。

补丁新增的是 idle-transition policy、streaming cursor 修复、状态观测和配置接口；它不声称发明 prefix caching 或 CPU offload。

证据：`EVIDENCE-H3-KV-EVICTION-SEMANTICS`。

<a id="finding-h4"></a>
### FINDING-H4 — 保留前缀逐出在实测点限制了闲置会话的 GPU 驻留

在历史 \(N=8\)、initial context length=4096、retained prefix \(K=128\)、120 s 诊断配置中，Conveyor 的 GPU KV occupancy 进入约 0.29 的锯齿稳态；未做 partial eviction 的历史对照末值接近 0.99。该数据点支持“该机制能降低 idle-session GPU residency”的判断。

这些 run 不满足新的 formal 标准，且当前跨系统 decode work 不同。数字只能作为诊断性 effect-size 线索，不能直接成为论文容量提升主结果。

证据：`EVIDENCE-H4-RESIDENCY`。

<a id="finding-h5"></a>
### FINDING-H5 — 按需回载会增加请求关键路径延迟

当前 on-demand reload 在 input feature extraction 之后由 scheduler admission 触发，因此两段延迟串行。历史诊断点上的 reload window p50 约 70 ms；tail 随 context 增长时，copy cost 也应进入 PCIe roofline。

证据：`EVIDENCE-H5-CRITICAL-PATH`。

<a id="finding-h6"></a>
### FINDING-H6 — 初始上下文需要初始化屏障而非机制状态转换

initial-context preloading 必须在周期输入开始前完成。barrier 结束时 host-backing frontier 可能仍不完整，因此 Conveyor 只解除 automatic-eviction hold，不在 barrier 原地逐出；第一次正常 segment 完成后再建立 retained-prefix 状态。

证据：`EVIDENCE-H6-INITIAL-CONTEXT`。该设置是 evaluation state construction。

<a id="finding-h7"></a>
### FINDING-H7 — KV 预取语义已完整但性能结论未定

当前实现能把 host-backed blocks 提前复制到 GPU prefix cache；真正 input 随后通过原生 prefix match 复用。capacity deferral、input overtaking 和 LRU eviction 都安全退化到 on-demand reload/recomputation。合成 ID 和 hash registration 是 transport 实现细节。

历史预取 run 的原始 artifacts 未保留，现有 source audit 只能支持语义检查。历史结果还显示 feature-extraction 膨胀可能抵消 copy overlap，净延迟收益尚未确认。

证据：`EVIDENCE-H7-PREFETCH`，角色为 `legacy-unreconstructable` / source audit。

## Diagnostic Boundary

未出现在本文的旧队列故障、单次调试技巧和过时 workload story 只保存在冻结的 [`legacy-experiment-log.md`](agent/legacy-experiment-log.md) 或不可变 `results/` 中。它们不能作为当前 paper prose source，也不能用于证明研究问题的重要性。

Agent 引用 finding 时必须保留完整 `FINDING-*` ID、证据角色、配置域和限制。若一个 finding 与新的 clean run 冲突，应更新本 owner 和 evidence registry，而不是在其他文档复制第二个版本。
