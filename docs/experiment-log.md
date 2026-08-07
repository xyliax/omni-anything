# E 系列执行记录

本文 = E 系列真机运行的 append-only 过程记录：每条 = 日期 + run + 观测 + 产物路径。
新 run 只 append 本文；提炼出的结论改 `docs/findings.md`（条目码 A1..G 是全仓引用锚点），本文条目不随结论回改。
条目按时间序，后文条目可更正前文，更正就地留指针。
历史条目迁入本文时统一过术语与代号写法；数字、判定与时间戳未动。
κ = decode step 时间膨胀系数 (slowdown factor, κ = t_with/t_without)。
## 2026-08-04：M0 完成（环境 + 冒烟 + E0），E1 由并行会话执行中

**环境与冒烟（任务 #1–#4）**：vLLM 0.23.0 虚拟环境（`~/vllm023-venv`）+ Go 1.22.5（`~/goroot`）
+ gateway 编译 + Qwen2.5-Omni-7B 权重。上游状态核查：FIX 1 已进 0.23.0 上游，FIX 4 只影响
Qwen3-Omni（本实验不适用）——**vanilla baseline 零补丁**
（本条不成立：见下条 2026-08-04 E1 vanilla 条目的环境核查更正——上游 0.23.0 无 FIX 1，
需手工打入 `mm_encoder_attention.py:720`）。新踩的坑（复现者需知）：
flashinfer 0.6.12 在 SM86 也 JIT 编译采样内核，且 CUDA 13 wheel 缺 `lib64` / `libcudart.so`
布局 → 两个符号链接修复（`ln -s lib lib64; ln -s libcudart.so.13 lib/libcudart.so`）。
冒烟通过：GPU3 / N=1 / 30s / 2s tick，15/15 帧节奏 100%，miss 0%，零漂移
（`results/paper/baseline/smoke_van7b_gpu3.json`）。

**多会话协同**：另一会话（job bdc51189）在 GPU1 执行 E1 vanilla 配置扫描
（N=2/4/6 已产出，五件套日志入 `results/paper/baseline/e1van_*`）。本会话让出 E1，转执行 E0。
跨会话进程隔离约定：worker 用独立文件名副本 + `VLLM_PROCESS_NAME_PREFIX=<jobid>`，
勿用 `pkill -f` 模式杀（已发生两次误杀）。

**E0 结果（`results/paper/e0/E0_dma_interference.{csv,json}`，3090 / GPU3 / Qwen3-1.7B fp16）**：

| 指标 | 值 |
|---|---|
| 空载 pinned H2D（重测） | 12.30 GB/s（与 7 月 12.33 一致） |
| κ 最大值（全 20 格） | **1.067**（B=1 / ctx=4k 小算量格；大格 1.01–1.03） |
| 拷贝实效带宽（decode 并发时） | 目标的 94–99% |
| 干扰形态 | decode 绝对加时约 2–2.5ms/step（近常数），κ 随 step time 变长而缩小 |

**判定：继续（κ=1.067 ≪ 门槛 1.15）**。KV conveyor 物理前提在 3090 上成立；η=0.7 假设偏保守
（实测计算期链路可用率约 0.94+）。conveyor 时刻表建模建议：干扰按每 step 加性约 2.5ms 计，
而非乘性折损。

**下一步**：M2——conveyor worker v1（fork `third_party/metronome/metronome/engine.py` 底子，
决策 D1），先 conveyor off 对齐 vLLM step time，再上固定时刻表搬运。

## 2026-08-04：E1 vanilla 配置 capacity bottleneck（job bdc51189，GPU1）——300s 初扫 + 600s 补拍

**更正上一节的「FIX 1 已进 0.23.0 上游 / vanilla baseline 零补丁」**：不成立。上游 0.23.0 **没有**
FIX 1；是本会话 06:16 手工打入虚拟环境（`mm_encoder_attention.py:720`，注释标记
`METRONOME FIX 1`）。本机所有成功的 omni 运行（含 GPU3 冒烟，06:49）都在补丁之后。
「Qwen2.5-Omni / SM86 不需要 FIX 1」未经检验——复现者装新虚拟环境时仍需打 FIX 1
（或先行验证）。FIX 4 确认不需要（崩溃点仅存在于 `qwen3_omni_moe_thinker.py`）。

**配置**：Qwen2.5-Omni-7B / vLLM 0.23 streaming（`WINDOW=0` vanilla 配置）/ 2s tick /
max_model_len MML=16384 / GPU_MEM=0.9 / 每点新起进程 / llama-questions 真音频相位错开。
驱动：`harness/run_vanilla_baseline.sh`（已按共机约定改为 setsid 进程组定向 kill）。

**300s 初扫（N ∈ {2,4,6,8}，`results/paper/baseline/e1van_n*`）**：

| N | tick latency（预热后） | 末态 KV 池 | 末态队列 | 判定 |
|---|---|---|---|---|
| 2 | p99 ≈ 0–1ms 平稳 | 低 | 无 | 平稳 |
| 4 | p99 ≈ 1ms 平稳 | 中 | 无 | 平稳 |
| 6 | p99 ≈ 1ms 平稳 | **0.855 仍在爬升** | waiting 队列开始出现 2 人 | **接近饱和**（外推约 350–400s 池饱和） |
| 8 | 290s 前约 1ms；**290–300s 跳变 1602ms** | **0.903** | **running 为空、waiting 7 人（run=0 / wait=7）** | **拍到崩溃起点** |

关键证据（C1 的真机版本）：N=8 崩溃窗口内 `nvidia-smi` SM util 大部分采样为 **0%**
（偶发 100% 尖峰）——KV 池满导致全员排队时计算完全空闲，与 Metronome
「memory kills sessions whose compute the GPU could easily carry」一致，且这是
**24GB 消费卡 + 7B** 上的独立复现（他们是 96GB Blackwell + 30B）。注意崩溃形态：
latency 钉在 1600ms = worker `wait_budget`（0.8×tick）轮询顶，属于 harness 的截断读数，
真实引擎 step time 更长；帧交付率同窗从 40 掉到 32。

**600s 补拍结论（`e1van_n{6,8}_d600_*`）——E1 的第一组完整 capacity bottleneck 数据，两个表面反常都已解释：**

| N | KV 池轨迹 | t_wall | 末态 |
|---|---|---|---|
| 8 | 0.001 → 0.543(136s) → 0.923+wait=6(256s) → **0.949，running 空 / waiting 8 人（376s 起到结束）** | **约 256–376s** | 全员永久 starvation，零 eviction，池占用钉住 |
| 6 | → 0.886+wait=2(403s)，**此后统计停更**（引擎无 step 可跑） | **约 370–400s** | 2 路 starvation + 其余触达 max_model_len 后停滞 |

- **池容量实测 M ≈ 90k token ≈ 5.1GB**（kv 占比 × 会话 token 数反推，N=6/8 两点交叉一致）；
  t_wall ≈ M/(N×约 40.5 tok/s) 公式吻合两点。**[更正，见每请求粒度重跑节]** 每请求粒度直接标定
  给出 M ≈ 74–79k token ≈ 4.3–4.5GB；90k 是间接反推的高估。显存账目
  （gpu_mem=0.9 → 21.6GiB 预算）：thinker 权重 16.64GiB（LLM 13.17 + 视觉塔 1.26
  **（本负载纯浪费）** + 音频塔 1.19 + lm_head 1.02，safetensors 头逐张量实算）
  + 激活 / graph 约 0.5 + KV 池约 4.4。
- **GPU 空转的直接测量证据**：N=8 崩溃后 `nvidia-smi` 采样 **105/123（85%）为 SM util 0%**——
  池满 → 全员排队 → 计算完全闲置。C1 在 24GB/7B 上成立。
- **Harness 陷阱 ①（silent failure：metrics 仍显示 realtime，内容已过时）**：worker `wait_budget=0.8×tick=1.6s` 截断了
  观测 latency，1.6s < 2s 预算 → **崩溃状态下 miss rate 恒为 0%、客户端判为 realtime**。
  Metronome Experiment A 的 1601ms 等待上限特征读数即此上限。我们的 E1 正式定义改用**starvation 判据**
  （该 tick 零新 token = miss）+ KV 统计轨迹，不能只信 `sustained_fd` 的 verdict。
- **Harness 陷阱 ②（触达 max_model_len 后停滞的会话）**：MML=16384 在约 81 token/tick 下约 400s 触顶，会话生成结束、
  后续 tick 0-1ms「稳定」是**会话已停滞的假象**（N=6 后半段即此）。600s 运行需 MML≥32768。
- 顺带：本配置（2s tick × 5.1GB 小池）对 conveyor 是极端适用工作点——P/M = η·12.3GB/s·2s/5.1GB，
  η=0.3 都翻倍；E2 在同配置下的预测增益非常可观，但主结果仍以 480ms tick 文本负载为主定义
  （D2/D3）。
  （该推算沿用初测 M=5.1GB；M 后订正为 74.3k token = 3.97GiB（FINDINGS D2），现行预测见 FINDINGS D4）

**E1 状态：初版完成**（4+2 个点、t_wall 两点、SM util 证据、两个 harness 陷阱记录在案）。
剩余清单及其完成态：

- injection 臂（等 gateway text 事件）：未跑。
- 600s@MML=32768 复测 N=4/6：已跑变体——`results/paper/baseline/e1perreq_n{4,6}_d300_*`
  （300s / GPU3 / 每请求粒度插桩），非清单所列的 600s@MML=32768 配置。
- ≥5 次乱序重复：2/5——`e1schtr_n8_d600` 为第 2 次（见 2026-08-06 capacity cascade 重复条目）。

## 2026-08-04：E1 每请求粒度插桩重跑（N=8/600s/MML=32768，GPU3）——死锁机制的直接证据

**动机**：聚合 kv.log 无法回答「每个请求何时工作 / 占多少显存 / 引擎花多久」，且 236s preemption 事件
此前只是记账反推。**插桩**：`harness/stream_server_perreq.py`（metronome worker 的加日志副本，
克隆零改动）——P（tick 推送）/ F（引擎接收分片）/ T（输出增长 + 引擎侧 nprompt）三类事件共用一个时钟；
统计日志加 `pre=` 累计 preempt 数（`IterationStats.num_preempted_reqs`）。驱动：
`harness/run_e1_perreq.sh`（端口 50054/8907 避让并行会话）。产物
`results/paper/baseline/e1perreq_n8_d600_*`。

**结果（与 16384 那次饱和的时刻一致，机制证据补齐）**：

- **preemption 直接证据：`pre` 恒 0 → 全程恰好 1 次**（271.2–287.2s 窗口内），伴随 kv 0.951→0.884，
  此后 0.884 / run=0 / wait=8 冻结到 600s。上次「236s KV 整块消失 = preemption」的反推证实
  （该次在 230s，本次 271s——饱和窗口内的具体倒下顺序有随机性，t_wall 时刻稳定）。
- **每会话存活区间**：8 路全部在实验前 2s 内开工（相位错开 0–1.9s）；会话 4–8 于 **255.6s**
  同时 starve，会话 1–3 多活一个配额到 **271.6s**。starve 后音频仍被前端持续接收
  （F 事件到约 595s，输入被缓冲）但零产出——连接仍在、会话已停滞。
- **每会话显存轨迹**：严格线性，**每 tick +53 音频 token + 约 25-29 生成 token ≈ 78 token/tick
  = 4.4MB/tick（56KB/token，Qwen2.5-7B GQA 4KV 头 ×128×28 层）≈ 2.2MB/s/会话**；
  终态各持 9.1–9.8k token = 496–534MB，8 路合计约 75k token ≈ 4.2GB。
  8×2.2MB/s 吃 4.2–4.7GB 池 ≈ 250s——t_wall 公式再吻合。
- **引擎节奏（每请求「处理时长」的正确定义）**：batch 引擎无独占时间；实测
  **F−P 排队 latency p50≈1015ms 全程稳定**——每 tick 的量恰在下一 tick 到达后约 1s 消化完，
  pipeline 满载但不落后（饱和前 SM util 79–100% 佐证）；等效摊分 ≈2s/8=250ms GPU 时间/会话/tick。
  首 token 时间（TTFA）p50 1608ms（首 tick 含预热）。
- **测量学注记**：AsyncLLM 前端输出合批（374 个 T 事件覆盖 28.8k token），T 时间戳不可用于
  tick 内细粒度区间；F 事件是可靠的引擎侧时序信号。更细的每 step 耗时要到 M2 自有 worker 里拿
  （decode 循环自持，天然可测）。
- **服务时序发现（`results/figures/E1_service_timeline.png`，脚本
  `harness/plots/plot_e1_service_timeline.py`）**：输入端零相位——gateway 每 tick 一个批量 Step，
  8 路 P 事件相差 <0.1ms；引擎端**自发形成无控制的粗粒度轮转**：每会话获得独占服务窗、
  连续处理完全部积压分片，随后等一整圈。**定量更正（分片间间隔分箱分析）**：
  每分片串行服务时间 **约 265ms 且与 context length 无关（30–240s 全程平坦）** →
  N×t_chunk = 8×265ms = 2.12s > 2s tick → **到达强度 ρ≈1.06，ingest 管线从约 30s 起就过载**；
  积压因此单调增长（分片/访问：1→2→4→5→7→8，对应内容陈旧度 2s→16s），不是稳态。
  若 capacity bottleneck 不在 255s 先使系统崩溃，积压会无界增长——**这是独立于 capacity bottleneck 和 compute bottleneck 的第三类瓶颈
  （ingest 串行瓶颈）**。嫌疑定位：t_chunk 与 context 无关 + 引擎停转后（255s+）前端仍以
  约 240ms/分片 的节奏继续拉取音频 → 瓶颈**已定位至代码行**
  （`vllm/v1/engine/async_llm.py` 的 `handle_inputs`，约 L458）：每个 StreamingInput 分片的
  `input_processor.process_inputs`（特征提取 + 分词 + 多模态哈希 + 序列化）**同步跑在
  AsyncLLM 前端的单条 event loop 线程上，无线程池、无对引擎进度的 backpressure（`async for` 贪婪拉取）**；
  单线程吞吐 1000/265ms≈3.8 分片/s < 到达 4 分片/s。突发轮转的成因：asyncio 任务仅在真挂起时让出，
  `process_inputs` 同步、非空 `queue.get()` 与缓冲未满的 IPC 发送均不挂起 → 每个会话的 ingest 任务
  连续排空自己的队列才让出 → 自发形成每会话独占突发。引擎停转后节奏不变（前端不看引擎是否仍在推进，继续预处理
  并塞核内缓冲——也解释了 worker 日志 tot_tokens 冻结而 resident_frames 持续上涨）。
  实测本机 HuggingFace 处理器单 2s 分片全程 55ms（特征提取 52ms）——占 265ms 的约 1/5，
  其余约 200ms 为分词 / 多模态哈希 / msgpack / zmq / GIL 竞争等逐分片前端常数，M2 可逐段计时。
  GPU 侧的账：每 tick 全部 GPU 工作（8×encoder + 424 prefill token + 约 200 decode token）≈1.0–1.3s
  < 2s——**GPU 有能力按 tick 完成，是单线程串行 ingest 路径吞吐不够；实现债而非物理极限**
  （线程池 / 批量 ingest / ingest 下沉均可修）；另注意本机为 12 用户共享服务器，CPU 侧常数可能被环境放大，
  且 Metronome N=96 未报告此瓶颈——**已用其论文数据裁决（更正先前猜测）**：其 t_wall 随 N 缩短
  （N=96 约 240s → N=128 约 148s，且早期线性拟合预测饱和时刻误差仅几个百分点）→
  其池填充速率随 N 线性扩展、未被 ingest 吞吐封顶 → **其主机上前端每分片 ≤ 2000/128 ≈ 15.6ms，
  ingest 未饱和，其「健康期」是真健康（内容新鲜），先前「其陈旧度或也隐性增长」的猜测撤回**。
  同一段单线程串行 ingest 路径代码两家都在跑，差别只在常数：本机 265ms/分片（HF 处理器 52ms + 约 210ms
  主机侧开销：老共享 Xeon 单核慢 / GIL 竞争 / swap 在用 38GB 疑似加重）vs 现代服务器 CPU 的
  约 10-20ms。**正确的论文表述：ingest 瓶颈是结构性的（单线程、无 backpressure、无指标暴露），
  但成为瓶颈的并发度 N_ingest = tick / t_chunk 是主机相关的**——任何主机都存在一个 N 使 ingest 先于 GPU
  饱和且 silent；我们的 N=8 恰好骑在本机的线上。以本机数字入稿前必须：N=4/6 对照点（ρ<1 验证）
  + 干净主机复测 t_chunk。**N=4/6 对照已完成（`e1perreq_n{4,6}_d300_*`，GPU3/300s）：模型全中**——
  N=4（ρ=0.53）603 次访问积压全部恒为 1、零突发；N=6（ρ=0.80）积压 p50=1/max=2 且末段 60s
  不增长（稳定队列）；F−P 排队 latency 随 N 单调上升（p50 366ms→591ms→N=8 的 1015ms）。
  ingest 排队诊断因果闭环：ρ<1 不积压，ρ>1（N=8）无界积压。E2 与 vanilla 配置对比的操作点据此选 N≤6。
  三个推论：① 客户端 latency 恒 1ms 的真因——突发一次产出约 8 tick 的 token 存货，帧交付永不断供；
  ② **真实的内容时效服务目标（本 tick 音频本 tick 处理完）从约 60s 起对所有会话持续违约且违约量线性增长**——
  按此定义 N=8 在本硬件上根本不可行（ingest 容量 ≈ 2000/265 ≈ 7.5 路），节奏指标对此完全失明；
  ③ 对 E3：vanilla 配置已在付轮转的全部代价（突发期间其余 7 路 KV 白白占用显存）却没拿到任何好处
  （无控制、无法配合搬运窗口）——TDM 相位指派 (phase-offset assignment，按时间表错开各路占用)
  是把它变成 tick 级、确定性、可与 conveyor prefetch 对齐的版本。

## 2026-08-04：并行 ingest 补丁实验（e1paringest，N=8/600s/GPU3）——ingest 瓶颈证实后即修复，capacity bottleneck 改换形态

**补丁**：`harness/stream_server_paringest.py`——用 monkeypatch 改写
`AsyncLLM._add_streaming_input_request`，唯一改动是每分片的 `process_inputs` 进
`ThreadPoolExecutor(8)`（会话内顺序保持；`mm_processor_cache_gb=0` 消除跨线程共享态）。
虚拟环境与克隆零改动。驱动 `harness/run_e1_paringest.sh`。

**修复验证（一行补丁的因果证明）**：积压全程恒 1（含崩溃期，零轮转）；F−P 从 1015ms → **3ms**
（p95 9ms）；时间线图（`harness/plots/plot_e1_service_timeline.py e1paringest_n8_d600` 出图，
该 tag 输出 `results/figures/e1paringest_n8_d600_service_timeline.png`，未留存；
库内 `E1_service_timeline.png` 是 vanilla 串行 ingest `e1perreq_n8_d600` 的版本）显示
8 路每 tick 同步推进、紧贴推送线。健康期引擎出现真空闲（running 队列呼吸式 7↔0，SM 相位均值 35.6%）——
GPU 余量直接可见。代价：首 token 时间 18ms→751ms（t=0 八路首 prefill 同时压 GPU，无害）。

**新故障形态：capacity cascade（`results/figures/E1_cascade_anatomy.png`，脚本
`harness/plots/plot_e1_cascade.py`）**：池打满 kv=1.000 → preempt 一个会话 → 仍在运行的会话以
N_alive×78tok/2s 回填 → 再满再 preempt。6 次 preemption（216.8/247.1/288.4/346.1/432.8/577.1s，
间隔 30→41→58→87→144s 精确按 1/N_alive 拉长），终态 2 路仍在运行（context 25.8k≈1.4GB each）。
被 preempt 的会话此后不可恢复：再 admission 条件 = 整段序列必须装得下（`full_sequence_must_fit`），starve 后前端仍持续追加 context（9.4k→24.9k），空闲从未超约 12%。
客户端这次可见 DEGRADING（p99 漂 +861ms）但 miss rate 仍 0%。

**旧「全员死锁」的机制更正（两个缺陷咬合）**：v1 scheduler 双 waiting 队列——挂起等输入的会话
（`WAITING_FOR_STREAMING_REQ`）入 `skipped_waiting`，等显存 admission 的入 `waiting`，
FCFS 下 **skipped 绝对优先**（`scheduler.py:1667`）。串行 ingest 时代人人有积压 →
人人在 `waiting` 排在队头被 preempt 请求之后 → 一次 preemption 后全部会话 starve；ingest 健康时会话走 skipped 通道绕过被 preempt 请求 →
只 starve 被 preempt 的那几路。**即 e1perreq 的 run=0/wait=8 全员死锁 = ingest 瓶颈 × capacity bottleneck 叠在一起的产物**；
单独的 capacity bottleneck 表现为 cascade 而非死锁。两种形态都终结于大部分会话 starve + 算力闲置，
windowed KV / conveyor 的必要性不变，但论文的机制分析叙事要按此分层。

**注意力成本斜率的直接测量（更正：不是「瓶颈显现」——本次运行从未 compute-bound）**：修好 ingest 后
每 tick 的活全程在 tick 内完成（存活会话每 tick 足额 25 token、终态 2 路时 SM 忙碌仅 50.8% ≈ 每 tick 约 1s/2s）。
测到的是斜率：每会话每 tick GPU 忙碌约 0.09s（ctx约 4k）→ 约 0.51s（25k），随 context 近线性。
**外推**（两点线性 + 未计 batch 摊薄，仅数量级）：8 路齐长时 8×busy(ctx) 在 ctx≈11–12k
越过 2s tick 预算才 compute-bound；实际 capacity bottleneck 在 ctx≈8.6k（217s）先动手，当时计算余量约 3×。
compute-bound 判据以「一 tick 的活 > tick 长」为准，SM util 只是代理。三类瓶颈状态：ingest（实测生效，已修）、
capacity（实测生效，conveyor 的靶）、attention / compute（仅测得斜率与外推越界点，未成为瓶颈）。

**方法论教训（时间线工具）**：kv / smi / 每请求三时钟的偏移必须逐次运行用预热锚点重算
（本次 −25.7s vs 上次 −15.6s）——初判「会话 7 在 preemption 之前就已 starve」即目测偏移伪象，对齐后
216.988s vs 216.8s 严丝合缝。

## 2026-08-05：tick 内执行剖面实测（e1periter，N=8/90s，逐引擎 step 日志）——两处猜测被数据纠正

**方法**：`_StatLog` 加 `PERITER_LOG`（每引擎 step 记录 t/run/gen/ptok，不限流），90s 短点
（`harness/run_e1_periter.sh`），43 个稳态 tick。

**tick 内真实剖面（43 tick 一致）**：8 路在 **84ms（p50，p95 164ms）内全部进入 batch**（2–4 step）→
**89% 的 step 是纯 batch=8 decode，21.0ms/step** → 收尾 2–3 step 8→5→0（配额几乎同时用完）→
忙碌窗合计 811ms/2000ms，其余纯空闲。逐步回放样例在 `e1periter_n8_d90_periter.log`
（t=57.55 tick：dt 序列 60/85ms 起步后稳定 21ms×35 step）。

**纠正两处此前说法**：① 「encoder 每 step 预算导致 tick 内错峰 admission」——错，admission 84ms 内完成，
无错峰（预算 2048 ≫ 需求，理论账与实测一致）；② 「瞬时并发典型 3–5、batch=8 仅 2%」——错，
那是 1Hz 限流采样的相位混叠 + 长跑后期各会话配额漂移的合成伪象；
**稳态真实 decode batch size = 8（忙碌 step 的 89%）**。教训入册：限流采样的直方图不可用于 tick 内结构推断，
逐步日志才可以。

**顺带**：ptok 统计对流式追加的 prefill 不计数（53×8 的 prefill 耗时隐在 tick 首 2–3 个 60–128ms 的长 step 里）——
vLLM 统计定义备忘。忙碌窗 811ms 中 batch-8 decode ≈ 735ms：decode 吞吐 8×(1000/21)=381 tok/s；
每 step 21ms ≈ 权重读取下界 15ms + 开销，GPU 侧健康。

## 2026-08-05：scheduler 级逐步追踪（e1schtr，N=8/60s）——tick 内每请求执行泳道，全部猜测清零

**方法**：`harness/sched_trace/sitecustomize.py` 经 PYTHONPATH 注入 EngineCore 子进程
（前端 monkeypatch 到不了 scheduler 所在进程；仅 SCHED_TRACE 设置时激活），包裹
`Scheduler.schedule` 逐步记录每请求的调度 token 数与 encoder 输入标记；请求 ID 自带 s{sid}
前缀直接映射会话。驱动 `harness/run_e1_schedtrace.sh`；图
`results/figures/E1_exec_lanes.png`（脚本 `harness/plots/plot_e1_lanes.py`），
Nsight 风格每请求泳道，格边=真实调度 step 时间戳。

**20 个稳态 tick 的实测结构**：① 8 个 prefill（53 tok）分 3–4 个 step 进入、跨度 112ms（p50）——
错峰源自**ingest 线程池完成抖动**（先到先排），非引擎排队 / 预算；② **encoder 152/152 与该会话
prefill 同一步共同调度**，从无独立 encoder step——「开场是不是 encoder 为主」的答案：encoder 搭车在
prefill step 内，prefill step 48–86ms vs 纯 decode step 21ms，多出的部分为 encoder 前向 +53×k token 计算
+ 多模态嵌入装配（step 内切分需 CUDA event，M2）；③ **无跨会话屏障**：会话 3 在 +48ms 已在产
token 时会话 1/2 尚未进场——「等 8 个编码完才 decode」不存在；④ 收尾=各会话配额差几个 token
先后领完，batch 8→0 就地变薄；⑤ 三 tick 全景：约 870ms 忙 / 约 1130ms 闲。
**并行 ingest 服务时间线图的块宽（250ms 回退占位）由本图取代**——旧图左边缘（ingest 时刻）仍有效，
宽度无效。

## 补注：每 tick decode 步数由谁决定（E1 系列通用）

决定链：harness 的 `--tpt 25` → worker 给每个分片的 SamplingParams 设 `max_tokens=25n+8` →
**vLLM 对 resumable request 的 max_tokens 语义是每段独立**（`scheduler.py:1058` 段边界
`_output_token_ids.clear()`，`check_stop` 按段内计数），且实际生效的是首段的 33——worker 里
`25n+8` 的累计式公式在引擎语义下等效为 **恒定 33/段**（数值实证：并行 ingest 下仍在运行的会话
9900 tok ÷ 300 段 = 精确 33.0）。引擎对「tick」零感知：decode 到 33 停 → 队列有下一分片则立即续段、
无则挂起（WAITING_FOR_STREAMING_REQ）——tick 结构完全由音频到达节奏从外部塑形。两个衍生注记：
① tpt=25 的来源是语音级 token 率（12.5 tok/s），+8 是余量；② 生产 33/tick vs 客户端取 25/tick
的差额在 worker 文本缓冲累积（无害但存在，harness 语义备忘）。

## 补注：TDM 相位打散 (desync) 的守恒律与粒度上界（E3/M2 设计参数，2026-08-05）

同步程度是连续旋钮，服从守恒：平均 batch size B̄ × 每 tick 步数 = N × 配额（264 tok），
步数 ≤ T/t_step ≈ 95 ⟹ **B̄ ≥ N×配额×t_step/T ≈ 2.8**。
两端点：完全同步（E1 实测：B̄=8、35 step、忙碌 35%、峰值常驻=全部会话、链路无用）↔
最大 desync（B̄≈3、95 step 铺满 tick、忙碌→100%、任意时刻仅约 3 路 KV 常驻、链路全程可用）。
**desync = 用算力余量购买常驻缩减**（权重每 step 重读是代价），
上界 = T·BW/(配额×权重字节) ≈ 3.4（3090+7B）；MoE / HBM 卡上界大幅放宽
（30B-A3B step time 4.8-14ms → 10+）→ 进 E6 地形。
**连续旋转优于离散组**：相位差 T/N=250ms 均匀铺开 → 每 250ms 一路进 / 一路出 →
链路双向各约 2.1GB/s 恒定（vs 12.3GB/s 容量，6× 余量；离散 G 组则为 G 倍峰值的脉冲）。
E3 三臂坐标：全常驻=B̄8 端点、随机相位=旋钮失控、TDM 相位指派=主动选 B̄≈3 均匀旋转。
M2 时刻表参数：相位间隔、τ_lead、B̄ 目标 + 守恒律可行性检查。同步 tick 下 conveyor 无收益的根因：
忙碌窗内 batch decode 每 step 读全部会话 KV → 峰值常驻不降，时间排他性是容量扩展的必要条件
（D1 自研 worker 的调度动机）。

## 2026-08-06：capacity cascade 重复 2/5（e1schtr_n8_d600，全程 scheduler 追踪）——确定性时钟、被 preempt 会话任意

**复现强度**：六次 preemption 时刻两次运行逐点吻合 ±0.4s
（run1: 217.0/247.1/288.4/346.1/432.8/577.1 vs run2: 216.8/247.2/288.4/346.1/432.9/577.2），
间隔序列 30→41→58→87→144s 完全一致——本配置填池远快于会话时长，
cascade **时钟完全确定性**（Metronome 亚稳态谱系的确定性端点）。**但被 preempt 会话身份完全不同**
（run1 preempt 7,2,6,1,8,3；run2 preempt 3,8,1,5,7,6）——`running.pop()` 的瞬时排列决定，
**「何时挤掉会话」由池算术决定、「挤掉谁」任意**——公平性叙事素材（用户无法预知也无法影响自己是否被 preempt）。
step time 随 context 增长直接测得：23.7ms（早期）→26.2ms（末期 2 路 25k context）。
**cascade 泳道图** `results/figures/E1_cascade_lanes.png`
（脚本 `harness/plots/plot_e1_cascade_lanes.py`）：
三窗（健康满员时段 / preemption #1 瞬间会话 3 泳道停止 / 终局两路仍在运行、step 变宽），
21ms step 分辨率的完整失效过程记录。

## 2026-08-06：种子功能验证通过（冒烟 #2，SEED=6k/N=8/180s）+ capacity bottleneck 第三形态

**种子校准后全部达标**（产物 `results/paper/baseline/e1paringest_n8_d180_*`）：8 路种子 5867–5989 tok
（目标 6k，±2%），3.4–12.3s 完成 seed prefill 预热（约 1.2s/路），池起步约 0.68，**约 125s 池饱和**
（vs 自然生长 217s，含 seed prefill 开销净省约 40%；种子越大压缩越多）。重复实验与 context 扫描自此走快车道。

**第三种失效形态（同步耗尽导致的 admission 死锁）**：终态 `kv=1.000 run=0 wait=0 pre=0`——
池精确打满于 tick 边界（种子使 8 路 context 完全同步），无人在跑故无 preemption 触发，
8 路全部滞留 skipped_waiting（统计日志的 wait= 只计 waiting 队列，不含 skipped——测量学备忘），
每 tick 被 promotion（提升回 waiting 队列）→admission 失败→退回，零 eviction 的全员冻结。
至此 capacity bottleneck 三形态齐全：
① 两种瓶颈叠在一起导致全体卡死（串行 ingest × capacity，run=0/wait=8）；
② capacity cascade（并行 ingest + context 异步耗尽，pre=6，2 路仍在运行）；
③ 同步耗尽导致的 admission 死锁（并行 ingest + context 同步，pre=0，全员冻结）——
形态由「池耗尽时刻落在 tick 内还是 tick 间」与「ingest 是否积压」二维决定，全部终结于多数 / 全部会话 starve
+ GPU 闲置。论文的机制分析节按此三分。**静态图规范追加**：时间轴图必须画真实 tick 边界
（P 事件锚定），坐标整数刻度会被误读为节拍（E1_cascade_lanes 已补虚线；跨时钟锚定法：
min(prefill_start−preceding_tick)=+3ms，查看器与图共用）。

## 补注：capacity-bound 时空闲的硬件不变量与适用边界（E6 建模，2026-08-06）

capacity-bound = KV 池容量先于算力饱和（区别于 bandwidth-bound 义的 memory-bound）。
**池满时 step time 不变量**：池满时每 decode step 读 (W+M)/BW ≈ 0.9×显存/BW——模型大小只改变权重 / KV 分账，
不改总字节。验证：3090 预测 25.4ms vs 六次 preemption 实测 24.8–27.2ms。结合 V/BW 五代恒定
（24–36ms）与配额随 tick 长缩放（r×T）：
**busy_wall/T ≈ r×0.9×(V/BW) + 开场占比 ≈ 38–55%（r=语音级）——对模型、tick 长、显卡代际三重不变**。
「capacity-bound 时算力恒有约一半空闲」（C1 最强形式）。适用边界：
① B > B*（摊平拐点 amortization knee）≈ 字节/参数×TFLOPS/(2×BW)
（3090+bf16 约 40–80，H100+bf16 约 200，B200+FP8 约 280）后 MLP 变为 compute-bound
（缓降非跳变，attention 项恒为 memory-bandwidth-bound）；
② MoE 反向偏离（等效权重小 → 空闲更多，Metronome 30B-A3B 即此）；
③ token 率远超语音级则正向侵蚀。我们全部工作区间（N≤16）远低于 3090 的 B*。
忙碌是总驻留字节的函数而非会话数的函数
（六次 preemption 时刻忙碌均约 1050–1090ms、总驻留均 3.97GiB——N×ctx=74.3k tok 双曲线守恒）。

## 更正：本系列所有运行均处于 async scheduling 模式（2026-08-06）

vLLM 0.23 对 `async_scheduling=None` 的解析是**默认启用**（`config/vllm.py:958`，
仅 pooling / 部分 speculative decoding / 不支持的 executor 例外——我们与 Metronome 均不命中；
确认日志为 info 级被 WARNING 吞掉）。测量语义随之修正：
**调度追踪的 step 间隔 = pipeline 节拍 = GPU 瓶颈侧纯执行时间**（CPU 调度藏于 GPU 影子内），
21.0ms 无需气泡项即与物理公式闭合（权重 17.5–18.7 + KV 约 1 + 开销约 1-2ms）；
此前基于同步假设的「每 step 2–4ms 空泡」估计作废（SM util 占用差应归因 nvidia-smi 采样粗糙）。
两家 step time 数字（我们 21ms、Metronome 4.8–14ms）定义一致均为纯 GPU step time。
AsyncScheduler 继承 schedule() 未重写，追踪钩子有效性不受影响；异步的停止滞后 + cancel 机制
在运行中活跃（收尾偶发第 34 step 的候选解释）。**间隔语义细则**：间隔=每 step 关键路径
=max(GPU 总工作, CPU 工作)。稳态 decode step GPU 侧为瓶颈（间隔均匀 + 物理闭合 + 双探针一致）
→ ≈GPU step 总时（含采样 / 拷贝杂项）；**tick 开场首 step 在 pipeline 排空后 CPU 串行回到关键路径——
48–86ms 的开场 step 含未知比例 CPU 成分，「encoder + prefill 耗时」降级为上界**（nsys 标定项）；
超前调度可产生不对应 GPU 时间的超短间隔伪影，本系列追踪实证无此模式，但换版本 / 配置后
应先验间隔分布。
