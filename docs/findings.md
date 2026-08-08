# FINDINGS：E 系列真机实验发现清单

*每条 = 一句话发现 + 关键数字 + 证据指针。全部可复现：日志在 `results/paper/baseline/`，图在 `results/figures/`，工具在 `harness/`。配置基线：vLLM 0.23 + Qwen2.5-Omni-7B + RTX 3090 (24GB) + tick = 2s + N = 8 concurrent sessions。机制推演与跑次修订过程写在 `docs/experiment-log.md`，本文只收结论。*

---

## A. 失效模式（默认 vLLM-realtime 如何失效）

**A1 · multimodal input processing 跟不上（此前无人报告的第三类瓶颈）**
vLLM realtime 的 multimodal input processing 是单线程的（`async_llm.py` 的 `handle_inputs` 在 event loop 线程上同步执行 `process_inputs`）。本机约 265ms/chunk；N=8 时 load factor ρ（每 tick 到达工作量 ÷ 每 tick 处理能力）= 1.06，backlog 无界增长（从 1 涨到 8 个 chunk），服务退化为约 15s 一轮的自发 round-robin，content staleness 线性上涨。**ingest 饱和的并发度是 host-dependent 的**：能撑住的最大路数 N_ingest = tick / t_chunk（我们是 7.5 路；Metronome 主机 ≥ 128 路——其 wall-clock time t_wall 随 N 缩短，证明它没有成为 input processing 瓶颈）。
证据：`E1_service_timeline.png`（round-robin 楼梯）；N=4/6 对照点（ρ < 1 时 backlog 恒为 1）；修复即证明（见下条）。

**A2 · 一个语句修复 input processing 瓶颈**
把 `process_inputs` 移入 8 线程线程池（重活恰好都释放 GIL），frame-to-process（F−P）排队由 1015ms 降到 **3ms**，backlog 恒为 1。这是工程债，不是物理极限。
证据：`harness/stream_server_paringest.py`（monkeypatch，venv 零改动）；e1paringest 运行全套。

**A3 · KV cache 装不下有三种失效形态，由「耗尽时刻落在 tick 内还是 tick 间 × input 是否积压」决定**
① **两类瓶颈叠在一起导致全部 session 死锁**（serial input processing）：一次 preemption 后，被抢占 session 带着「整段序列必须装得下」的 re-admission 条件（`full_sequence_must_fit`）插到队列头，FCFS（First-Come-First-Served）的 `break` 造成 head-of-line blocking，把全体锁死（running 队列为空 `run=0`、waiting 队列 8 人 `wait=8`，5% KV cache 空置却永远不可用）。② **preemption cascade**（parallel input processing）：池打满 100% 后一路路被 preempt，间隔按 1/N_alive 拉长（30→41→58→87→144s），终态 2 个仍在 running 的 session 各占 25.8k token。③ **admission deadlock under synchronized fill**（种子锁步）：池恰好在 tick 间隙打满 → 无人在跑、无从 preempt → 全员滞留在 `skipped_waiting`（kv=1.000 / run=0 / wait=0 / pre=0）。
证据：`E1_deadlock_anatomy.png`、`E1_cascade_anatomy.png`、`E1_cascade_lanes.png`、e1paringest_n8_d180。

**A4 · preemption cascade 的时刻确定、被抢占 session 任意**
两次独立运行中，六次 preemption 时刻吻合 **±0.4s**（600s 全程），被抢占 session 名单完全不同（取决于 `running.pop()` 的瞬时排列）；被抢占那一刻，被抢占 session 与仍在 running 的 session 的 context 差仅 **2–3 token（0.03%）**。「何时 preempt 由池算术决定，preempt 谁纯属任意。」
证据：e1paringest vs e1schtr 两组 600s 运行的 kv.log 对照。

**A5 · 被抢占的 session 永不复活（permanent starvation）**
被抢占 session 复活所需的 re-admission 条件 = 整段序列必须装得下（`full_sequence_must_fit` 默认开启），且 starve 后前端仍持续追加 context（9.4k→24.9k token）；空闲从未超过约 12% → 全部 running 中复活次数为零。
证据：per-request T/F 事件时间线；`scheduler.py:995` prepend + `kv_cache_manager.py:354`。

**A6 · 双 waiting 队列是形态①与②的分野**
挂起等 input 的 session 走 `skipped_waiting`（FCFS 下绝对优先，`scheduler.py:1667`），等 KV cache 的走 `waiting`。input backlog 把全员赶进 `waiting`、排在「HOL-blocked 的被抢占 request」后面 → 全部 session 死锁；input 健康则活 session 绕过被抢占 session → 只 starve 被抢占的那几路。
附：statlog 的 `wait=` 不含 skipped 队列（这就是形态③读数 wait=0 的原因）。

## B. 监控指标看不出已经坏了

**B1 · silent failure：指标仍显示 real-time，内容已过时**
worker 等待帽 1.6s < 2s deadline → 崩溃状态下每 tick 仍准时返回空帧，miss 恒 0%、frame delivery 100%。这是 Metronome「崩溃是静默的」（其原文：the collapse is silent）的 per-session 粒度版本。

**B2 · frame latency 测不出 content staleness**
input backlog 期间，client latency 恒为 1ms（burst 预存了 8 个 tick 的 token buffer），而 semantic response lag 最多约 16s——cadence 指标结构性测不出 content staleness。duplex serving 需要独立的 content freshness SLO。

**B3 · 触达 max_model_len 后停滞的 session**
context 触达 max_model_len（MML）后，session 假稳定（0–1ms「健康」）。

**B4 · 1601ms 等待上限特征读数无法区分成因**
compute-bound 和 memory-bound 透过同一个等待帽都读作 1601ms——定性必须配合 KV 轨迹 + SM util（streaming multiprocessor 利用率）：SM 高位 = compute-bound，归零 = memory-bound。

## H. tick 内执行剖面（引擎每 2 秒在干什么）

**H1 · 稳态剖面**（43 个 tick 一致）
8 路在 84ms 内全部进 batch（p95 164ms，无任何跨 session 屏障——先完成 prefill 的立即 decode）→ **89% 的 step 是纯 batch=8 的 decode，21.0ms/step** → 收尾 2–3 step 配额领完退场 → busy 811ms/2000ms。encoder **152/152 与该 session prefill 同步共排**，从无独立 encoder step。
证据：`E1_exec_lanes.png`；e1periter/e1schtr 逐步日志。

**H2 · 每 tick 33 token 的真实出处**
vLLM 对 resumable request 的 max_tokens 语义是**每段独立**的（段边界清零输出计数，`scheduler.py:1058`），worker 的累计式公式 `25n+8` 实际退化为恒定 33/段（仍在 running 的 session 9900 token = 33×300 段，精确）。tick 结构完全由 audio 到达节奏从外部塑形，引擎对「tick」零感知。

**H3 · 本系列全部运行处于 async scheduling 模式**
vLLM 0.23 对 `None` 默认启用 async scheduling，相关日志被 WARNING 吞掉。step interval = pipeline tick = 纯 GPU step time（两家项目口径一致）；tick 开场首 step 在 pipeline drain 后含 CPU 串行成分，「encoder+prefill 耗时 48–86ms」应读作上界。

## D. 硬件上可用公式直接算的关系（可跨代际外推的部分）

**D1 · capacity-bound 时的 step-time 不变量**
池满时每 step 读 (W+M)/BW ≈ **0.9×显存/带宽**——模型大小只改 weight 与 KV 的占比，不改总字节（预测 25.4ms vs 实测 24.8–27.2ms）。而「整卡读一遍」跨五代硬件恒为 24–36ms → **capacity-bound 时 busy/T ≈ token率×0.9×(V/BW)，对模型、tick 长、显卡代际三重不变，约 38–55%**：「KV cache 不足 starve session 时，compute 恒有约一半空闲」是结构性质。边界：当 B > B* ≈ 字节/参数×TFLOPS/(2BW)（3090 约 40–80）后，MLP 变为 compute-bound；MoE 反向偏离；超语音级 token 率正向侵蚀。

**D2 · busy 是总 resident 字节的函数，而非 session 数的函数**
六次 preemption 时刻，N×ctx 恒等于 74.3k token（双曲线守恒：8×9.3k = 3×24.8k），busy 均约 1050–1090ms。附注：M 的最精标定 74.3k token = 3.97GiB。

**D3 · 相位打散（phase desynchronization）守恒律**
平均 batch 大小 B̄ ≥ N×配额×t_step/T ≈ 2.8——打散 = 用 compute headroom 购买 KV resident 缩减（代价是 weight 每 step 重读），上界 T·BW/(配额×W) ≈ 3.4（3090+7B）。**连续旋转优于离散槽**：相位差 T/N 铺开 → 链路双向各约 2.1GB/s 恒定（对比 12.3GB/s 容量）。同步 tick 下 conveyor 无收益（busy 窗内每 step 读全员 KV，峰值 resident 不降）——非重叠忙碌窗 (time-multiplexed residency) 是 capacity 扩展的必要条件。

**D4 · 3090 稳态容量预测（E2 预告）**
接入 tail KV conveyor 后 N=15–16（**2×**），封顶在 compute 而非链路（PCIe 利用率仅约 26%；理论 (M+P)/M = 4.9× 要 N≈39，需 4.7s compute 预算，本卡给不出）。收益可用公式直接算：min((M+P)/M, 算力倍数)。

**D5 · 显存预算构成**
21.6GiB 预算 = thinker weight 16.64GiB（含 **vision tower 1.26GiB 未参与推理的占用**，折合 +30% 池容量）+ activation 约 0.5GiB + KV pool 约 4.0GiB。

## K. 与生态对照

**K1 · Metronome paper 归因正确，repo 笔记的 attention drift 作废**
paper 明写 "memory cliff, not a compute drift"（含 stat-logger 图与亚稳态竞速模型）；其 repo 工作笔记里的 "attention drift" 是废弃旧说。我们的增量 = scheduler 代码级死锁机制分析 + per-request 粒度 + 消费卡复现 + 三形态分层。

**K2 · 他们的 30B 每 step decode 4.8–14ms**
（fused FP8 MoE probe）→ 其 capacity-bound 时的 compute headroom 比我们更大（MoE 偏离 D1 不变量的方向）。

**K3 · 「resident 是唯一预算兼容选择」（其 §2 对 swap 的分析性排除）有两个可证伪假设**
① 全量轮换是不具代表性的 baseline（真实设计点是 partial residency + 链路扩容；我们的操作点即便全量轮换也只需 4.2GB/s）；② 「无空隙可藏」（每会话子 tick 占用比例 1/N 就是空隙；E0 实测 decode step 减速系数 κ=1.067（slowdown factor），H2D 几乎不拖慢计算）。chip-to-chip（C2C）900GB/s 加速使此论断过期。

**K4 · DuplexOmni 的 480ms 切片 = 论文主配置的 tick 长**
（负载保真背书）；其「延迟推理」通道（[THINK] → 异步云端推理 → 结果注入后续切片）= 实验 E4 注入负载的量产形态。而其论文零 serving 数字（无并发 / 每卡 session）——模型论文止步于 N=1、real-time factor RTF < 1，serving 层是空白。

## F. 测量方法教训（本系列自己踩出来的）

**F1 · 限流采样不可用于快尺度结构推断**
1Hz statlog 把 89% batch=8 混叠成「典型 3–5」；同类修复：Perfetto 导出的 concurrency counter 改由逐步 trace 派生。

**F2 · 跨时钟必须逐 run 锚定**
三类日志（perf / unix / statlog）偏移每次不同（−15.6 vs −25.7s）；泳道对齐用物理不变量 min(prefill_start − tick) = +3ms。

**F3 · 图的分辨率不得超过仪器分辨率**
块宽占位值事件（service duration 无数据时禁止画宽度）；时间轴图必须画真实 tick 边界（坐标整数刻度会被读成节拍）。

**F4 · 残差归因前先验前提**
同步模式假设未验证 → 「2–4ms bubble」过度归因（残差小于带宽假设误差带）；async 默认开启这一前提本身就是发现（H3）。

**F5 · 默认值语义要查解析代码**
`bool|None=None` 实为「自动开」。

**F6 · 前提性 bug 的放大效应**
种子单位失准（1.6 token/词）意外发现「oversized seed 启动 = 零秒复现 admission deadlock」——现为最快的死锁复现路径。
