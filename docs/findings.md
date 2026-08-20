# Findings

本文是当前状态、量化结论和限制条件的唯一 owner。每条 finding 使用稳定 ID；精确 run 与 provenance 通过 [`evidence.json`](agent/evidence.json) 解析。配置、指标和证据等级由 [`Experiments`](experiments.md) 定义，历史推演保存在冻结的 [`legacy-experiment-log.md`](agent/legacy-experiment-log.md)。

## Current State

| Mechanism | Implementation | Semantic Validation | Performance Conclusion | Evidence |
| --- | --- | --- | --- | --- |
| Phase staggering | complete | validated | accepted at the measured point；formal rerun required | `EVIDENCE-H1-COMPARISON` |
| Take-from-stock delivery | complete | validated | metric semantics validated | `EVIDENCE-H2-METRICS` |
| KV park | complete | validated | accepted at the measured point；formal rerun required | `EVIDENCE-H4-RESIDENCY` |
| KV prefetch | complete | source-auditable；raw diagnostic unavailable | open：FE 膨胀使净收益尚未闭合 | `EVIDENCE-H7-PREFETCH` |

容量主张仍需 protocol-compatible 的 `N` 扫描和 roofline 正式对比；injection 端到端联合协议尚未接入。上表只陈述证据支持的成熟度，不把“代码已实现”自动升级为“性能已验证”。

## Evidence Scope

- FINDING-A/B/C 系列来自 measured stack 的历史 baseline 真机运行；原始 artifacts 位于 git 历史，当前 registry 将其标为 `legacy-unreconstructable`。
- FINDING-D 系列组合真机测量与解析公式；每条只在正文声明的模型和硬件边界内成立。
- FINDING-E 系列是外部 paper、pin 和 dated reference 的对照，不是本仓运行结果。
- FINDING-F 系列是测量方法论，其中现代时钟对齐规则已经取代旧启发式。
- FINDING-H 系列来自 conveyor 真机增量；retained manifests 的 dirty source 无法按当前纪律重建，且 H1/H4 的 baseline half 早于逐会话 delivery-completeness 记录，不能通过当前验收。因此 accepted 结论与 formal paper evidence 必须区分。

配置域的精确定义见 [`Experiments`](experiments.md#configuration-domains)。任何 claim 如果没有在本节、正文或 evidence registry 中说明来源等级，不得外推到另一模型、tick 或设备。

---

## System Pathologies

<a id="finding-a1"></a>
### FINDING-A1 — Multimodal Input Processing Becomes a Host Bottleneck

vLLM realtime 的 multimodal input processing 是单线程的：`AsyncLLM.handle_inputs` 在 event loop 线程上同步执行 `process_inputs`。本机约 265ms/chunk；N=8 时 load factor ρ（每 tick 到达工作量 ÷ 每 tick 处理能力）= 1.06，backlog 从 1 涨到 8 个 chunk，服务退化为约 15s 一轮的自发 round-robin，content staleness 线性上涨。

**ingest 饱和的并发度是 host-dependent 的**。最大路数约为 N_ingest = tick / t_chunk：本机为 7.5 路，而 Metronome 主机至少支持 128 路；其 wall-clock time 随 N 缩短，说明 input processing 没有成为该主机的瓶颈。

证据：`EVIDENCE-LEGACY-BASELINE`；原图与对照点位于历史 results tree，引用前需按 registry 限制复核。

<a id="finding-a2"></a>
### FINDING-A2 — Parallel Ingest Removes the Host Bottleneck

把 `process_inputs` 移入 8 线程线程池（重活恰好都释放 GIL），frame-to-process（F−P）排队由 1015ms 降到 **3ms**，backlog 恒为 1。这是工程债，不是物理极限。

统一五站插桩和隔离 benchmark 进一步把剩余成本定位到 FE 计算段：系统内每 chunk 约 **279ms（238–528ms）**，executor 派发、排队、回循环等待和 `add_request` 合计 <3ms。单发对照为 59ms；加入同进程 Python 忙线程后升至 **630ms（10.7×）**，一个并发 FE 时为 122ms，16 个外部忙进程时为 86ms。

首要原因是事件循环与 FE 线程的 GIL 分时，轻度槽重叠次之；线程钉扎和关闭逐步 detokenize 均未改善。彻底隔离方向是 FE 进程池。

证据：`EVIDENCE-LEGACY-BASELINE`；现行修复实现在 `engines/baseline/worker/stream_server.py`。

<a id="finding-a3"></a>
### FINDING-A3 — KV Exhaustion Has Three Failure Modes

KV exhaustion 表现为三种可区分的失效：

1. **两类瓶颈叠加导致全部 session 死锁**。serial input processing 下，一次 preemption 后，被抢占 session 带着“整段序列必须装得下”的 re-admission 条件（`full_sequence_must_fit`）进入队头；FCFS 的 `break` 形成 head-of-line blocking。终态是 `run=0`、`wait=8`，仍有 5% KV cache 空置却不可用。
2. **Preemption cascade**。parallel input processing 下，池占用达到 100% 后会话逐一被 preempt，间隔按 1/N_alive 拉长（30→41→58→87→144s）；终态仅 2 个 running session，各占 25.8k token。
3. **Admission deadlock under synchronized fill**。种子锁步使池恰好在 tick 间隙占满，此时没有 running session 可供 preempt，全部会话滞留在 `skipped_waiting`（kv=1.000 / run=0 / wait=0 / pre=0）。

证据：`EVIDENCE-LEGACY-BASELINE`；原始 anatomy 图与运行位于历史 results tree。

<a id="finding-a4"></a>
### FINDING-A4 — Preemption Timing Is Deterministic but Victim Choice Is Not

两次独立运行中，六次 preemption 时刻吻合 **±0.4s**（600s 全程），被抢占 session 名单完全不同（取决于 `running.pop()` 的瞬时排列）；被抢占那一刻，被抢占 session 与仍在 running 的 session 的 context 差仅 **2–3 token（0.03%）**。「何时 preempt 由池算术决定，preempt 谁纯属任意。」
证据：`EVIDENCE-LEGACY-BASELINE`；两组长运行的 kv.log 位于历史 results tree。

<a id="finding-a5"></a>
### FINDING-A5 — Preempted Sessions Can Starve Irreversibly

被抢占 session 复活所需的 re-admission 条件 = 整段序列必须装得下（`full_sequence_must_fit` 默认开启），且 starve 后前端仍持续追加 context（9.4k→24.9k token）；空闲从未超过约 12% → 全部 running 中复活次数为零。
证据：`EVIDENCE-LEGACY-BASELINE`；代码行号属于历史 vLLM 0.23 pin，当前引用以 symbol 和 source audit 为准。

<a id="finding-a6"></a>
### FINDING-A6 — Two Waiting Queues Separate the Failure Regimes

挂起等 input 的 session 走 `skipped_waiting`（`Scheduler.schedule` 的 FCFS 路径下绝对优先），等 KV cache 的走 `waiting`。input backlog 把全部会话推进 `waiting`、排在「HOL-blocked 的被抢占 request」后面 → 全部 session 死锁；input 健康则存活 session 绕过被抢占 session → 只 starve 被抢占的那几路。
附：statlog 的 `wait=` 不含 skipped 队列（这就是形态③读数 wait=0 的原因）。

## Silent Failures

<a id="finding-b1"></a>
### FINDING-B1 — Frame-Level Health Can Hide Stale Content

worker 等待帽 1.6s < 2s deadline → 崩溃状态下每 tick 仍准时返回空帧（双工通道里静音帧是合法帧），miss 恒 0%、frame delivery 100%——cadence 指标度量传输而非语义。失效在引擎侧信号（kv.log 池占用、队列状态）可见，但那些是诊断信号而非对外 SLO。这是 Metronome「崩溃是静默的」（其原文：the collapse is silent）的 per-session 粒度版本。

当前正式比较使用的 paringest baseline 会额外记录逐会话 delivery count；runner 将 short delivery、session death、Step error 和 client-health failure 判为 failed run。pin 内 vanilla 保留原始字段，只作参考 target。

<a id="finding-b2"></a>
### FINDING-B2 — Frame Latency Is Not Content Latency

input backlog 期间，client latency 恒为 1ms（burst 预存了 8 个 tick 的 token buffer），而 semantic response lag 最多约 16s——cadence 指标结构性测不出 content staleness。duplex serving 需要独立的 content freshness SLO。

<a id="finding-b3"></a>
### FINDING-B3 — Sessions Stall at the Model-Length Boundary

context 触达 max_model_len（MML）后，session 假稳定（0–1ms「健康」）。

<a id="finding-b4"></a>
### FINDING-B4 — The Wait-Cap Signature Is Degenerate

compute-bound 和 memory-bound 透过同一个等待帽都读作 1601ms——定性必须配合 KV 轨迹 + SM util（streaming multiprocessor 利用率）：SM 高位 = compute-bound，归零 = memory-bound。

<a id="finding-b5"></a>
### FINDING-B5 — Baseline Delivery Lag Grows Without Bound

worker 每段生成 33 token（配额公式 `25n+8` 的段内退化，FINDING-C2），gateway 每 tick 只取走 25，净积压为 +8 token/tick。按播放率折算，交付内容的陈旧度每秒增长 0.32 秒，正常运行 5 分钟即约 96 秒滞后，且 FIFO 队列永不作废。

这是负载发生器而非引擎的结构性质；Metronome 的 cadence-only 指标看不见它。它不影响 KV 容量测量，但任何 content freshness 指标都必须先扣除此伪影。worker 的 text 流全量交付、token 流限流 25，同一响应的两条流也会互相漂移。

证据：`EVIDENCE-LEGACY-BASELINE`；当前机制仍可在 `engines/baseline/worker/stream_server.py` 复核。

## Tick Execution Profile

<a id="finding-c1"></a>
### FINDING-C1 — Steady-State Tick Profile

8 路在 84ms 内全部进 batch（p95 164ms，无任何跨 session 屏障——先完成 prefill 的立即 decode）→ **89% 的 step 是纯 batch=8 的 decode，21.0ms/step** → 收尾 2–3 step 配额领完退场 → busy 811ms/2000ms。encoder **152/152 与该 session prefill 同步共排**，从无独立 encoder step。
证据：`EVIDENCE-LEGACY-BASELINE`；执行泳道与逐步日志位于历史 results tree。

<a id="finding-c2"></a>
### FINDING-C2 — Origin of the Baseline 33-Token Segment

vLLM 对 resumable request 的 `max_tokens` 语义是**每段独立**的：段边界会清零输出计数，所以 worker 的累计式公式 `25n+8` 实际退化为恒定 33/段（仍在 running 的 session 为 9900 token = 33×300 段）。tick 结构完全由 audio 到达节奏从外部塑形，引擎对 tick 零感知。

该结论有两条限定：33/段而交付 25/tick 会产生 **+8/段的库存漂移**（FINDING-F7）；旧 seeded baseline 还会因 `session.max_tokens` 冻结而退化为每段 1 token，不能作为有效证据。当前 baseline 通过 `worker/engine_fix` 在每个 chunk 刷新该字段，conveyor 由 park patch 处理并通过 config 约束组合。

<a id="finding-c3"></a>
### FINDING-C3 — Legacy Runs Used Async Scheduling

vLLM 0.23 对 `None` 默认启用 async scheduling，相关日志被 WARNING 吞掉。step interval = pipeline tick = 纯 GPU step time（两家项目口径一致）；tick 开场首 step 在 pipeline drain 后含 CPU 串行成分，「encoder+prefill 耗时 48–86ms」应读作上界。

## Hardware Relations

<a id="finding-d1"></a>
### FINDING-D1 — Capacity-Bound Step-Time Invariant

池满时每 step 读 (W+M)/BW ≈ **0.9×显存/带宽**。模型大小只改变 weight 与 KV 的占比，不改变总字节；预测为 25.4ms，实测为 24.8–27.2ms。

“整卡读一遍”跨五代硬件稳定在 24–36ms，因此 **capacity-bound 时 busy/T ≈ token率×0.9×(V/BW)，对模型、tick 长和显卡代际近似不变，约 38–55%**。KV cache 不足而 starve session 时，compute 仍约有一半空闲，这是结构性质。

边界是 B > B* ≈ 字节/参数×TFLOPS/(2BW)：RTX 3090 上约为 40–80，超过后 MLP 转为 compute-bound；MoE 反向偏离，超语音级 token 率会正向侵蚀该余量。

<a id="finding-d2"></a>
### FINDING-D2 — Busy Time Tracks Resident Bytes, Not Session Count

六次 preemption 时刻，N×ctx 恒等于 74.3k token（双曲线守恒：8×9.3k = 3×24.8k），busy 均约 1050–1090ms。附注：M 的最精标定 74.3k token = 3.97GiB。

<a id="finding-d3"></a>
### FINDING-D3 — Phase-Desynchronization Conservation Law

平均 batch 大小 B̄ ≥ N×配额×t_step/T ≈ 2.8——去同步 = 用 compute headroom 购买 KV resident 缩减（代价是 weight 每 step 重读），上界 T·BW/(配额×W) ≈ 3.4（3090+7B）。**连续旋转优于离散槽**：相位差 T/N 铺开 → 链路双向各约 2.1GB/s 恒定（对比 12.3GB/s 容量）。同步 tick 下 KV 搬运无收益（busy 窗内每 step 读全部会话的 KV，峰值 resident 不降）——时间排他性是 capacity 扩展的必要条件。

<a id="finding-d5"></a>
### FINDING-D5 — GPU-Memory Budget Composition

21.6GiB 预算 = thinker weight 16.64（含 **vision tower 1.26GiB 未参与推理的占用**，折合 +30% 池容量）+ activation 约 0.5 + KV pool 约 4.0GiB。

## Ecosystem Comparison

<a id="finding-e1"></a>
### FINDING-E1 — Metronome's Paper Attribution Supersedes the Repo Note

paper 明写 "memory cliff, not a compute drift"（含 stat-logger 图与亚稳态竞速模型）；其 repo 工作笔记里的 "attention drift" 是废弃旧说。我们的增量 = scheduler 代码级死锁机制分析 + per-request 粒度 + 消费卡复现 + 三形态分层。

<a id="finding-e2"></a>
### FINDING-E2 — Metronome's 30B Decode Step Leaves More Headroom

（fused FP8 MoE probe）→ 其 capacity-bound 时的 compute headroom 比我们更大（MoE 偏离 FINDING-D1 不变量的方向）。

<a id="finding-e3"></a>
### FINDING-E3 — The Resident-Only Argument Relies on Two Refutable Assumptions

① 全量轮换是不具代表性的 baseline（真实设计点是 partial residency + 链路扩容；我们的操作点即便全量轮换也只需 4.2GB/s）；② 「无空隙可藏」（每会话子 tick 占用比例 1/N 就是空隙；EXP-E0 实测 decode step 时间膨胀系数 κ=1.067（slowdown factor），H2D 几乎不拖慢计算）。chip-to-chip（C2C）900GB/s 加速使此论断过期。

<a id="finding-e4"></a>
### FINDING-E4 — DuplexOmni Supports the Paper Tick Configuration

（负载保真背书）；其「延迟推理」通道（[THINK] → 异步云端推理 → 结果注入后续切片）= 历史 EXP-E4 注入负载的生产形态。而其论文零 serving 数字（无并发 / 每卡 session）——模型论文止步于 N=1、real-time factor RTF < 1，serving 层是空白。

## Measurement Lessons

<a id="finding-f1"></a>
### FINDING-F1 — Rate-Limited Samples Cannot Recover Fast Structure

1Hz statlog 把 89% batch=8 混叠成「典型 3–5」；同类修复：Perfetto 导出的 concurrency counter 改由逐步 trace 派生。

<a id="finding-f2"></a>
### FINDING-F2 — Every Run Requires Explicit Clock Alignment

perf、epoch 与 statlog 时钟的偏移逐 run 变化。现代 run 使用 per-request.log 的 `C <perf> <epoch>` 双时钟配对行精确对表；只有缺少 C 行的历史 run 才回退 `min_prefill_after_push` 启发式，并必须标记其把 ingest 延迟折入偏移的已知误差。

<a id="finding-f3"></a>
### FINDING-F3 — Visualization Resolution Cannot Exceed Instrument Resolution

块宽占位值事件（service duration 无数据时禁止画宽度）；时间轴图必须画真实 tick 边界（坐标整数刻度会被读成节拍）。

<a id="finding-f4"></a>
### FINDING-F4 — Validate Priors Before Attributing Residuals

同步模式假设未验证 → 「2–4ms bubble」过度归因（残差小于带宽假设误差带）；async 默认开启这一前提本身就是发现（FINDING-C3）。

<a id="finding-f5"></a>
### FINDING-F5 — Read Parsing Code Before Trusting Defaults

`bool|None=None` 实为「自动开」。

<a id="finding-f6"></a>
### FINDING-F6 — Prerequisite Bugs Can Amplify Into Useful Reproducers

种子单位失准（1.6 token/词）意外发现「oversized seed 启动 = 零秒复现 admission deadlock」——现为最快的死锁复现路径。

<a id="finding-f7"></a>
### FINDING-F7 — Delivery/Generation Mismatch Produces Silent Inventory Drift

每段 max_tokens 带 +8 松弛 → 松弛每段累积进取现货库存，第 55 帧交付的 token 对应 ~13 周期前的音频，而 miss/cadence 指标全部正常。修复 = 每段配额精确 tpt + `inv_backlog` 常驻监控（健康恒 ~tpt）。通则：**流水线两端速率必须精确配平，任何单边松弛都是无界漂移**。

## Reusable Instrumentation

暖启动种子（`--seed-tokens`，使 context 成为受控变量）；scheduler 逐步 trace（sitecustomize 注入 EngineCore，现居 `infra/trace/collectors/`）；每 request P/F/T 事件；Perfetto 导出（`python -m infra.trace.perfetto`，泳道 + counter 一条命令）。工具入口和格式契约由 `infra/trace/AGENTS.md` 持有，本文只记录由仪器得出的结论。

## Conveyor Mechanisms

<a id="finding-h1"></a>
### FINDING-H1 — Phase Staggering Removes the Ingest Thundering Herd

gateway 槽轮（8 槽，250ms 间距）把 8 路同步到达铺成 247-252ms 等间距，各会话自身周期不变；ingest 从同步惊群（push→prefill 20-260ms 散布）收敛到接近无竞争的本征值。发射走**绝对网格**后每会话周期精确 2000.0ms（继承的重锚循环曾累积 +4ms/周期），534 次发射源头晚醒 max 1.2ms。

统一观测下的同负载直接对比（N=8、seed=4096、120s）显示，FE 段（IS→IE）baseline p50 **383ms**，conveyor p50 **221ms**；同步惊群使 FE 膨胀 73%。push→prefill p50 相应为 426ms 与 316ms。

证据：`EVIDENCE-H1-COMPARISON`。当前 retained manifests 不满足新的 clean-source formal 标准，registry 已显式降级。

<a id="finding-h2"></a>
### FINDING-H2 — Take-From-Stock Delivery Requires New Metrics

Step 不再含 GPU 等待后，latency p50 退化为 0.15ms、TTFA 错误读数 2ms（真值 ≥ 一个周期）、饥饿完全不可见。重建：`deadline_met` = 本 tick 交付 ≥ tpt（miss = 引擎未跟上），TTFA 如实包含一片流水线滞后（~2005ms），latency 分布永久改走 trace 侧。教训同 F 系列：**评估协议必须随交付语义重建，否则指标全部正常与系统完全失效可以并存**。
证据：`EVIDENCE-H2-METRICS`；口径实现在 conveyor gateway 的 delivery contract。

<a id="finding-h3"></a>
### FINDING-H3 — Active KV Park Closes on Existing vLLM Primitives

vLLM 抢占只作用于 RUNNING 请求，闲置 resumable 会话没有释放路径；其 LRU 逐出序对循环负载近似反 Belady，会先逐出最快再次使用的内容。因此，被动等待池满再轮转不可行。

主动原语组合 `free(request)`、`evict_blocks` 与 connector hash-match reload：前两者释放 request grip 并精确销毁尾块，后者按原 hash 恢复。它们都是引擎既有能力，补丁新增的是状态转移。

实现还修复两个上游 bug：eager-store 游标在 streaming 重入时漂移，使 CPU mirror 无法覆盖尾部；`session.max_tokens` 冻结在构造值，使 seeded run 每段固定为 1 token。

证据：`EVIDENCE-H3-PARK-SEMANTICS`；补丁在 `engines/conveyor/worker/engine_patch/`。

<a id="finding-h4"></a>
### FINDING-H4 — Auto-Park With a Constant Floor Bounds Steady-State Residency

auto-park-on-stop 在调度器停止转移处原地执行，无额外 RPC。keep-K 配额把闲置底座固定为 K+2 余量加 1 个未满块：稳态池占用 **0.29**，全驻留假设为 0.860（保留 run 的 tick-window 重算值为 0.292）。同时全驻留会话数为 3，占 79%，接近 slice 时长 × N / 周期给出的物理下界；回载窗口 p50 为 70ms，被逐尾块 CPU 覆盖率 100%，交付未恶化。

mirror 是增量 write-through：稳态 PCIe 上行约等于增长率（约 5 块/周期/会话），下行约等于尾部大小并随 context 长度线性增长，形成容量 roofline 的带宽线。

同负载公平对照（N=8、seed=4096、120s）中，baseline 末池占用 **0.993**、斜率 0.458%/s，自身外推约 145s 占满；同一时刻 conveyor 稳态约 0.29，即**实测驻留比约 3.4×（省 71%）**。baseline 是有限时间内撞墙的单调轨迹，conveyor 是有界锯齿。

证据：`EVIDENCE-H4-RESIDENCY`。当前 retained manifests 不满足新的 clean-source formal 标准，正式论文主张需 clean rerun。

<a id="finding-h5"></a>
### FINDING-H5 — Demand Reload Serializes With Feature Extraction

回载由 chunk 到达调度器触发（FE 之后），tick→计算片 = FE 272ms + 调度 15ms + 回载 70ms = 358ms 串行；FE 膨胀（本征 87ms → 系统内 272ms）根因为与事件循环分时 GIL（FINDING-A2 附注的隔离基准测试 + 本轮微基准一致）。优化排序：FE 进程池（−185ms）> 预取原语（−70ms 且随尾巴增长）> Whisper 30s padding 消除（待验证音频塔约定）。
证据：`EVIDENCE-H5-CRITICAL-PATH`。

<a id="finding-h6"></a>
### FINDING-H6 — Warm Start Is Barriered State Construction

warm start 模拟“请求自带上下文”，属于**负载状态构造**而非 conveyor 机制。正常路径要求全部 seed prefill 完成后才写 ready，gateway/client 再开始 tick；seed output 跳过消费指针。当前 timeout 会继续 ready，但 validation 必须将该 run 判为 failed。

屏障收尾**不能 park**：镜像发起依赖各请求自身的调度步，已停止会话的剩余 seed 块不会继续发起；低优先级拷贝流还会被连续 seed prefill 占用。观测中只覆盖约 130/256 块，已发起拷贝仅确认 0–27/256。此时 park 会销毁无副本块，导致首 tick 重算整段 seed、迟到 1–1.65s，并让库存永久偏移 38 token。

正确收尾只解除 auto-park 挂起：第一周期全驻留，首次正常 segment stop 再进入 park 稳态；观测中 8/8 会话覆盖率达到 100%，库存保持 25。饥饿从会话**首次足额交付**起算，与 TTFA 的首 token 语义分离。baseline 公平对照臂已采用同一屏障。

证据：`EVIDENCE-H6-WARM-START`；完整根因链保存在 legacy experiment record。

<a id="finding-h7"></a>
### FINDING-H7 — KV Prefetch Is Semantically Closed but Performance-Open

回载的可复用核心是“让内容存在于 GPU prefix cache”，而不是“回载某个 request 的尾巴”。实现分为四层：registry 保存控制阶段、时序和延迟队列，块级真相按需查 pool；`reload_kv` / `kv_state` 提供指令面；匿名传输完成后按原 hash 注册并转为 LRU 可弃的 cached-free block；真实 request 仍通过 vLLM 原生 resume hash match 认领。失败、迟到或被逐出只会退化为 demand reload。

历史诊断中（N=8、seed=4096、K=128、120s，两次复跑），477–478 次预取均完成，拷贝窗口 p50 约 96ms，并消除了大段 demand reload；但 tick→prefill p50 仅从 316ms 降至 297ms，远小于理论 70ms，因为 FE 同时从 221ms 膨胀到 270ms。末尾两次短交付也稳定复现，根因仍未闭合。

当前发射策略在 pool 紧张时把 reload 延迟到下一次 park 事件重评，chunk 被 demand path 认领后取消延迟项；历史 workload 没有触发预算闸，尚不能说明高压 pacing 已验证。raw prefetch run 未保留，registry 将本条标为 `legacy-unreconstructable`；当前源码只能支持语义审查，不能独立重算性能数字。

证据：`EVIDENCE-H7-PREFETCH`；实现在 `engines/conveyor/worker/engine_patch/`。
