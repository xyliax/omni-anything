# FINDINGS：真机实验发现清单（E 系列 = baseline 病理；H 系列 = conveyor 机制）

*每条 = 一句话发现 + 关键数字 + 证据指针。配置基线：vLLM 0.23 + Qwen2.5-Omni-7B + RTX 3090 (24GB) + tick = 2s + N = 8 concurrent sessions。产出这些结论的 E 系列运行证据与工具在 2026-08-07 实验体系重构（旧代号映射见 `docs/experiments.md` 附表）中整理：原始日志与图存于 git 历史（`109db82` 及更早的 `results/` 树），工具的后继实现在 `experiments/baseline/` 与 `tracekit/`；新证据一律落 `results/<experiment>/runs/`。机制推演与逐 run 修订过程写在 `docs/experiment-log.md`，本文只收结论。*

---

## A. 系统病理（默认 vLLM-realtime 如何失效）

**A1 · multimodal input processing 跟不上（此前无人报告的第三类瓶颈）**
vLLM realtime 的 multimodal input processing 是单线程的（`async_llm.py` 的 `handle_inputs` 在 event loop 线程上同步执行 `process_inputs`）。本机约 265ms/chunk；N=8 时 load factor ρ（每 tick 到达工作量 ÷ 每 tick 处理能力）= 1.06，backlog 无界增长（从 1 涨到 8 个 chunk），服务退化为约 15s 一轮的自发 round-robin，content staleness 线性上涨。**ingest 饱和的并发度是 host-dependent 的**：能撑住的最大路数 N_ingest = tick / t_chunk（我们是 7.5 路；Metronome 主机 ≥ 128 路——其 wall-clock time t_wall 随 N 缩短，证明它没有成为 input processing 瓶颈）。
证据：`E1_service_timeline.png`（round-robin 楼梯）；N=4/6 对照点（ρ < 1 时 backlog 恒为 1）；修复即证明（见下条）。

**A2 · 一个语句修复 input processing 瓶颈**
把 `process_inputs` 移入 8 线程线程池（重活恰好都释放 GIL），frame-to-process（F−P）排队由 1015ms 降到 **3ms**，backlog 恒为 1。这是工程债，不是物理极限。
证据：instrumented worker fork（monkeypatch，venv 零改动；现为 `experiments/baseline/worker/stream_server.py`）；e1paringest 运行全套（git 历史）。
附注（2026-08-10 站点插桩 run + 隔离 bench 实测，替代 08-09 附注的组件级归因）：并行化后的每 chunk `process_inputs` 在系统内实测成本 **~279ms（238~528）**，五站分解证明 executor 派发/线程池排队/回循环等待/add_request 合计 <3ms，**全部时间与方差都在 FE 计算段内部**。隔离基准测试归因（单发 59ms 对照）：+同进程一个 Python 忙线程 → **630ms（10.7×，GIL 分时是首要原因）**；+一个并发 FE → 122ms（槽重叠，次要原因）；+16 个外部忙进程 → 86ms（排除跨进程核心竞争）。系统内 3× 膨胀 = 持续繁忙的事件循环的部分 GIL 占用 + 轻度槽重叠（279ms > 250ms 槽距）。线程钉扎无效、关逐步 detokenize 无效且略负（两次重复证伪）——因为都不减少循环的 GIL 占用。彻底修复 = FE 进程池（脱离共享 GIL，预期回到 ~90ms 且方差收紧）；方差本质是"循环瞬时 GIL 占用率"的涨落，非外生噪声，可消除。

**A3 · KV cache 装不下有三种失效形态，由「耗尽时刻落在 tick 内还是 tick 间 × input 是否积压」决定**
① **两类瓶颈叠在一起导致全部 session 死锁**（serial input processing）：一次 preemption 后，被抢占 session 带着「整段序列必须装得下」的 re-admission 条件（`full_sequence_must_fit`）插到队列头，FCFS（First-Come-First-Served）的 `break` 造成 head-of-line blocking，把全体锁死（running 队列为空 `run=0`、waiting 队列 8 人 `wait=8`，5% KV cache 空置却永远不可用）。② **preemption cascade**（parallel input processing）：池占用达 100% 后会话逐一被 preempt，间隔按 1/N_alive 拉长（30→41→58→87→144s），终态 2 个仍在 running 的 session 各占 25.8k token。③ **admission deadlock under synchronized fill**（种子锁步）：池恰好在 tick 间隙占满 → 无会话在运行、无从 preempt → 全部会话滞留在 `skipped_waiting`（kv=1.000 / run=0 / wait=0 / pre=0）。
证据：`E1_deadlock_anatomy.png`、`E1_cascade_anatomy.png`、`E1_cascade_lanes.png`、e1paringest_n8_d180。

**A4 · preemption cascade 的时刻确定、被抢占 session 任意**
两次独立运行中，六次 preemption 时刻吻合 **±0.4s**（600s 全程），被抢占 session 名单完全不同（取决于 `running.pop()` 的瞬时排列）；被抢占那一刻，被抢占 session 与仍在 running 的 session 的 context 差仅 **2–3 token（0.03%）**。「何时 preempt 由池算术决定，preempt 谁纯属任意。」
证据：e1paringest vs e1schtr 两组 600s 运行的 kv.log 对照。

**A5 · 被抢占的 session 永不复活（irreversible starvation）**
被抢占 session 复活所需的 re-admission 条件 = 整段序列必须装得下（`full_sequence_must_fit` 默认开启），且 starve 后前端仍持续追加 context（9.4k→24.9k token）；空闲从未超过约 12% → 全部 running 中复活次数为零。
证据：per-request T/F 事件时间线；`scheduler.py:995` prepend + `kv_cache_manager.py:354`。

**A6 · 双 waiting 队列是形态①与②的分野**
挂起等 input 的 session 走 `skipped_waiting`（FCFS 下绝对优先，`scheduler.py:1667`），等 KV cache 的走 `waiting`。input backlog 把全部会话推进 `waiting`、排在「HOL-blocked 的被抢占 request」后面 → 全部 session 死锁；input 健康则存活 session 绕过被抢占 session → 只 starve 被抢占的那几路。
附：statlog 的 `wait=` 不含 skipped 队列（这就是形态③读数 wait=0 的原因）。

## B. 帧级指标看不出已经坏了（silent failure）

**B1 · silent failure：帧级指标仍显示 real-time，内容已过时**
worker 等待帽 1.6s < 2s deadline → 崩溃状态下每 tick 仍准时返回空帧（双工通道里静音帧是合法帧），miss 恒 0%、frame delivery 100%——cadence 指标度量传输而非语义。失效在引擎侧信号（kv.log 池占用、队列状态）可见，但那些是诊断信号而非对外 SLO。这是 Metronome「崩溃是静默的」（其原文：the collapse is silent）的 per-session 粒度版本。

**B2 · frame latency ≠ content latency**
input backlog 期间，client latency 恒为 1ms（burst 预存了 8 个 tick 的 token buffer），而 semantic response lag 最多约 16s——cadence 指标结构性测不出 content staleness。duplex serving 需要独立的 content freshness SLO。

**B3 · 触达 max_model_len 后停滞的 session**
context 触达 max_model_len（MML）后，session 假稳定（0–1ms「健康」）。

**B4 · 1601ms 等待上限特征读数是简并的**
compute-bound 和 memory-bound 透过同一个等待帽都读作 1601ms——定性必须配合 KV 轨迹 + SM util（streaming multiprocessor 利用率）：SM 高位 = compute-bound，归零 = memory-bound。

**B5 · harness 的交付滞后在正常运行时也线性无界增长（0.32 s/s）**
worker 每段生成 33 token（配额公式 25n+8 的段内退化，FINDINGS C2）而 gateway 每 tick 只取走 25，净积压 +8 token/tick——按播放率折算，交付内容的陈旧度每秒增长 0.32 秒，正常运行 5 分钟即约 96 秒滞后，且 FIFO 队列永不作废。这是负载发生器的结构性质（Metronome 的 cadence-only 指标 by design 看不见它），不是引擎性质；对容量测量无害，但任何 content freshness 类指标必须先扣除此伪影。另：worker 的 text 流全量交付、token 流限流 25，同一响应的两条流互相漂移。
证据：当前 baseline 证据见 `results/baseline/runs/`；机制在 `experiments/baseline/worker/stream_server.py` 的 `step()`。

## C. tick 内执行剖面（引擎每 2 秒在干什么）

**C1 · 稳态剖面**（43 个 tick 一致）
8 路在 84ms 内全部进 batch（p95 164ms，无任何跨 session 屏障——先完成 prefill 的立即 decode）→ **89% 的 step 是纯 batch=8 的 decode，21.0ms/step** → 收尾 2–3 step 配额领完退场 → busy 811ms/2000ms。encoder **152/152 与该 session prefill 同步共排**，从无独立 encoder step。
证据：`E1_exec_lanes.png`；e1periter/e1schtr 逐步日志。

**C2 · 每 tick 33 token 的真实出处**
vLLM 对 resumable request 的 max_tokens 语义是**每段独立**的（段边界清零输出计数，`scheduler.py:1058`），worker 的累计式公式 `25n+8` 实际退化为恒定 33/段（仍在 running 的 session 9900 token = 33×300 段，精确）。tick 结构完全由 audio 到达节奏从外部塑形，引擎对「tick」零感知。
2026-08-12 追记（conveyor 实现过程中回溯发现的两条限定）：①33/段 × 交付 25/tick = **+8/段的库存漂移**（F7 的同一病理）——baseline 数字里凡涉及「交付内容对应哪段音频」的口径须加此限定；②`session.max_tokens` 曾冻结在构造值（H3 上游 bug ②），旧实现中带 seed 的 baseline 每段会固定为 1 token、不能作为有效证据；当前 baseline 已通过 `worker/engine_fix` 在每个 chunk 刷新该字段，conveyor 侧则由 park 补丁处理并用 config 校验约束组合。

**C3 · 本系列全部运行处于 async scheduling 模式**
vLLM 0.23 对 `None` 默认启用 async scheduling，相关日志被 WARNING 吞掉。step interval = pipeline tick = 纯 GPU step time（两家项目口径一致）；tick 开场首 step 在 pipeline drain 后含 CPU 串行成分，「encoder+prefill 耗时 48–86ms」应读作上界。

## D. 硬件上可用公式直接算的关系（可跨代际外推的部分）

**D1 · capacity-bound 时的 step-time 不变量**
池满时每 step 读 (W+M)/BW ≈ **0.9×显存/带宽**——模型大小只改 weight 与 KV 的占比，不改总字节（预测 25.4ms vs 实测 24.8–27.2ms）。而「整卡读一遍」跨五代硬件恒为 24–36ms → **capacity-bound 时 busy/T ≈ token率×0.9×(V/BW)，对模型、tick 长、显卡代际三重不变，约 38–55%**：「KV cache 不足 starve session 时，compute 恒有约一半空闲」是结构性质。边界：当 B > B* ≈ 字节/参数×TFLOPS/(2BW)（3090 约 40–80）后，MLP 变为 compute-bound；MoE 反向偏离；超语音级 token 率正向侵蚀。

**D2 · busy 是总 resident 字节的函数，而非 session 数的函数**
六次 preemption 时刻，N×ctx 恒等于 74.3k token（双曲线守恒：8×9.3k = 3×24.8k），busy 均约 1050–1090ms。附注：M 的最精标定 74.3k token = 3.97GiB。

**D3 · 相位打散（desync）守恒律**
平均 batch 大小 B̄ ≥ N×配额×t_step/T ≈ 2.8——去同步 = 用 compute headroom 购买 KV resident 缩减（代价是 weight 每 step 重读），上界 T·BW/(配额×W) ≈ 3.4（3090+7B）。**连续旋转优于离散槽**：相位差 T/N 铺开 → 链路双向各约 2.1GB/s 恒定（对比 12.3GB/s 容量）。同步 tick 下 KV 搬运无收益（busy 窗内每 step 读全部会话的 KV，峰值 resident 不降）——时间排他性是 capacity 扩展的必要条件。

**D5 · 显存预算构成**
21.6GiB 预算 = thinker weight 16.64（含 **vision tower 1.26GiB 未参与推理的占用**，折合 +30% 池容量）+ activation 约 0.5 + KV pool 约 4.0GiB。

## E. 与生态对照

**E1 · Metronome paper 归因正确，repo 笔记的 attention drift 作废**
paper 明写 "memory cliff, not a compute drift"（含 stat-logger 图与亚稳态竞速模型）；其 repo 工作笔记里的 "attention drift" 是废弃旧说。我们的增量 = scheduler 代码级死锁机制分析 + per-request 粒度 + 消费卡复现 + 三形态分层。

**E2 · 他们的 30B 每 step decode 4.8–14ms**
（fused FP8 MoE probe）→ 其 capacity-bound 时的 compute headroom 比我们更大（MoE 偏离 D1 不变量的方向）。

**E3 · 「resident 是唯一预算兼容选择」（其 §2 对 swap 的分析性排除）有两个可证伪假设**
① 全量轮换是不具代表性的 baseline（真实设计点是 partial residency + 链路扩容；我们的操作点即便全量轮换也只需 4.2GB/s）；② 「无空隙可藏」（每会话子 tick 占用比例 1/N 就是空隙；E0 实测 decode step 时间膨胀系数 κ=1.067（slowdown factor），H2D 几乎不拖慢计算）。chip-to-chip（C2C）900GB/s 加速使此论断过期。

**E4 · DuplexOmni 的 480ms 切片 = 论文主配置的 tick 长**
（负载保真背书）；其「延迟推理」通道（[THINK] → 异步云端推理 → 结果注入后续切片）= 实验 E4 注入负载的生产形态。而其论文零 serving 数字（无并发 / 每卡 session）——模型论文止步于 N=1、real-time factor RTF < 1，serving 层是空白。

## H. conveyor 机制（新引擎增量的已验证结论，证据在 results/conveyor 保留 run 与 experiment-log）

**H1 · 错开相位消除 ingest 惊群，无额外代价**
gateway 槽轮（8 槽，250ms 间距）把 8 路同步到达铺成 247-252ms 等间距，各会话自身周期不变；ingest 从同步惊群（push→prefill 20-260ms 散布）收敛到接近无竞争的本征值。发射走**绝对网格**后每会话周期精确 2000.0ms（继承的重锚循环曾累积 +4ms/周期），534 次发射源头晚醒 max 1.2ms。
2026-08-14 追记（观测统一后的首次同仪器直接对比，两臂同负载 N=8/seed=4096/120s）：五站插桩下 FE 段（IS→IE）baseline p50 **383ms** vs conveyor p50 **221ms**——惊群使 FE 膨胀 73%，惊群消除的收益首次有两臂同口径的直接测量；push→prefill p50 相应为 426ms vs 316ms。
证据：当前 conveyor 与 baseline 证据见 `results/conveyor/runs/`、`results/baseline/runs/`。

**H2 · 取现货交付使 client 侧全部实时指标失效，必须重建交付口径**
Step 不再含 GPU 等待后，latency p50 退化为 0.15ms、TTFA 错误读数 2ms（真值 ≥ 一个周期）、饥饿完全不可见。重建：`deadline_met` = 本 tick 交付 ≥ tpt（miss = 引擎未跟上），TTFA 如实包含一片流水线滞后（~2005ms），latency 分布永久改走 trace 侧。教训同 F 系列：**评估协议必须随交付语义重建，否则指标全部正常与系统完全失效可以并存**。
证据：experiment-log 2026-08-10 metricfix 条目；口径实现在 conveyor gateway 分歧清单第 3 条。

**H3 · KV 部分释放原语（park）在 vLLM 既有原语上闭合，被动方案不存在**
vLLM 抢占只作用于 RUNNING 请求、闲置 resumable 会话持块无任何释放路径，且 LRU 逐出序对循环负载反 Belady（先逐最快要用的）——被动「池满触发轮转」不可行。主动原语 = `free(request)`（与抢占共用的释放路径，前缀经 prefix cache 免费恢复）+ `evict_blocks`（精确销毁尾块）+ connector hash-match 回载，全部为引擎既有能力，补丁只新增状态转移。实现中修复两个上游 bug：eager-store 游标在 streaming 重入时漂移（CPU 镜像永远覆盖不到尾部）；`session.max_tokens` 冻结在构造值（C2 的同源现象，seed 时每段固定为 1 token）。
证据：experiment-log 2026-08-10/11 park 系列条目；补丁在 `experiments/conveyor/worker/engine_patch/`。

**H4 · 驻留核算：decode 结束瞬间 park + 常量底座 K，稳态驻留降 66%**
auto-park-on-stop（在调度器停止转移处原地执行，零延迟零 RPC）+ keep-K 配额（闲置底座固定为 K+2 余量+1 未满块）：稳态池占用 **0.29 vs 全驻留假设 0.860**（保留 run 的 tick 窗重算口径 0.292），同时全驻留会话数 3 个占 79%（≈ slice 时长 × N / 周期的物理下界），回载窗口 p50=70ms、被逐尾块 CPU 覆盖率 100%，交付零恶化。镜像是增量 write-through：稳态 PCIe 上行 ≈ 增长率（~5 块/周期/会话），下行 ≈ 尾巴大小（随 L 线性涨——容量 roofline 的带宽线）。
2026-08-14 追记（实测对实测，替代「全驻留假设」的外推口径）：同负载 baseline 公平对照 run（N=8/seed=4096/120s）末池占用 **0.993**、斜率 0.458%/s、自身外推 t≈145s 占满（pre=0，恰在墙脚）；同一时刻 conveyor 稳态 ~0.29——**同负载实测驻留比 ≈ 3.4×（省 71%）**，且 baseline 是有限时间内必撞墙的单调轨迹，conveyor 是有界锯齿。
证据：当前 conveyor 与 baseline 证据见 `results/conveyor/runs/`、`results/baseline/runs/`。

**H5 · 回载与 FE 串行是当前关键路径的已知浪费**
回载由 chunk 到达调度器触发（FE 之后），tick→计算片 = FE 272ms + 调度 15ms + 回载 70ms = 358ms 串行；FE 膨胀（本征 87ms → 系统内 272ms）根因为与事件循环分时 GIL（A2 附注的隔离基准测试 + 本轮微基准一致）。优化排序：FE 进程池（−185ms）> 预取原语（−70ms 且随尾巴增长）> Whisper 30s padding 消除（待验证音频塔约定）。
证据：当前 conveyor 证据的 ingest 泳道分解见 `results/conveyor/runs/`；experiment-log 2026-08-12 条目。

**H6 · warm start 的正确语义是屏障式状态构造，且不得在 seed 刚结束时 park**
warm start 模拟「请求自带上下文」，正确形态：全部会话 seed prefill 完成后引擎才开始接收 tick（结构性屏障：ready 文件晚于最后一个 seed，gateway/client 晚于 ready），期间无任何机制交错。两个结构性事实决定屏障收尾**不能 park**：①镜像拷贝的发起只依赖各请求自身的调度步——已停止会话余下的 seed 块永远不会发起（实测 ~130/256）；②低优先级拷贝流被连续 seed prefill 完全占用（已发起仅确认 0-27/256）。收尾 park 会销毁无副本块 → 首 tick 全部会话重算整段 seed → 首段迟到 1-1.65s → 取现货库存永久偏移（+38 token）。正确收尾 = 只解除 auto-park 挂起：第 1 周期全驻留（无回载无重算），首次 auto-park 在正常调度中自然完成状态转换（覆盖率 8/8 全 100%），库存恒 25 = 设计值。同批口径精化：饥饿从会话**首次足额交付**起算（流水线爬坡阶段的欠额不算落后），与 TTFA 的首 token 语义分离；seed 输出 token 跳过消费指针（上下文不是回应）。warm start 属**负载状态构造**而非机制——baseline 公平对照臂已移植同一屏障（2026-08-14，惰性 seed 与 tick 混跑属同型错误）。
证据：当前 conveyor 证据见 `results/conveyor/runs/`；三轮根因链在 experiment-log 2026-08-12 条目。

**H7 · KV 预取（匿名具现化）：语义闭合成立，净收益暂被 FE 膨胀抵消**
回载的可复用核心是「让内容在 GPU prefix cache 里存在」而非「回载某请求的尾巴」——据此把机制立成四层：状态权威（会话生命周期 resident/parked/materializing + 时序 + 延迟队列，块级事实不复制、按需查池）、指令面（`reload_kv`/`kv_state` utility + 发射策略）、传输（匿名块搬运，搭现有 offload load-event 机制，完成后按原 hash 注册、块转 cached-free = LRU 可弃 = 失败自动退回按需回载）、认领（vLLM 现有 resume hash match，零改动）。push 触发下首轮真机验证（N=8/seed=4096/K=128/120s，两次复跑一致）：**逐周期预取全部成功完成**（477-478 次，拷贝窗口 p50≈96ms，完整藏进 FE），**demand 大回载消失**（剩余 demand 全是 1-2 块的镜像前沿零头）；但 tick→prefill p50 仅 316→297ms（−19ms ≪ 理论 −70ms）——同 run FE 从 221 膨胀到 270ms（+50ms）把收益吃掉，疑与预取拷贝跨进程竞争 CPU/内存带宽，根因未定（FE 进程池方向可能一石二鸟）；末尾两次短交付在两次复跑中精确复现（同槽同会话同位置），是 prefetch 臂在最大上下文处的确定性签名，待解。发射策略已升级为事件驱动 pacing：池紧的 reload 延迟到下一次 park（容量释放事件）重评发射、chunk 认领即取消——本轮负载未触发（预算闸零触发），待更高压负载验证。
证据：experiment-log 2026-08-15 条目；实现在 `experiments/conveyor/worker/engine_patch/`。

## F. 测量方法论教训（来自本系列实测）

**F1 · 限流采样不可用于快尺度结构推断**
1Hz statlog 把 89% batch=8 混叠成「典型 3–5」；同类修复：Perfetto 导出的 concurrency counter 改由逐步 trace 派生。

**F2 · 跨时钟必须逐 run 锚定**
三类日志（perf / unix / statlog）偏移每次不同（−15.6 vs −25.7s）；泳道对齐用物理不变量 min(prefill_start − tick) = +3ms。

**F3 · 图的分辨率不得超过仪器分辨率**
块宽占位值事件（service duration 无数据时禁止画宽度）；时间轴图必须画真实 tick 边界（坐标整数刻度会被读成节拍）。

**F4 · 残差归因前先验前提**
同步模式假设未验证 → 「2–4ms bubble」过度归因（残差小于带宽假设误差带）；async 默认开启这一前提本身就是发现（C3）。

**F5 · 默认值语义要查解析代码**
`bool|None=None` 实为「自动开」。

**F6 · 前提性 bug 的放大效应**
种子单位失准（1.6 token/词）意外发现「oversized seed 启动 = 零秒复现 admission deadlock」——现为最快的死锁复现路径。

**F7 · 交付与生成解耦后，速率配平错误以「库存漂移」形态静默积累**
每段 max_tokens 带 +8 松弛 → 松弛每段累积进取现货库存，第 55 帧交付的 token 对应 ~13 周期前的音频，而 miss/cadence 指标全部正常。修复 = 每段配额精确 tpt + `inv_backlog` 常驻监控（健康恒 ~tpt）。通则：**流水线两端速率必须精确配平，任何单边松弛都是无界漂移**。

## G. 工具资产（复用入口）

暖启动种子（`--seed-tokens`，KV 池饱和时间 217→125s，context 成为受控变量）；scheduler 逐步 trace（sitecustomize 注入 EngineCore，现居 `tracekit/collectors/`）；每 request P/F/T 事件；Perfetto 导出（`python -m tracekit.perfetto`，泳道 + counter 一条命令）。
