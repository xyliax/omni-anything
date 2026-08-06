# FINDINGS：E 系列真栈实验的发现清单（2026-08-04 ~ 08-06）

*每条 = 一句话发现 + 关键数字 + 证据指针。全部可复现：日志在 `results/paper/baseline/`，图在
`results/figures/`，工具在 `harness/`（用法见 `harness/README.md`），机制细节与订正史在
`PAPER-EXPERIMENTS.md` 执行记录。配置基线：vLLM 0.23 + Qwen2.5-Omni-7B + RTX 3090(24GB) + 2s 拍 + N=8。*

---

## A. 系统病理（vanilla vLLM-realtime 怎么死）

**A1 · 摄入墙（此前无人报告的第三面墙）**
vLLM realtime 的多模态摄入是单线程的（`async_llm.py handle_inputs` 在事件循环线程上同步执行
`process_inputs`），本机 ~265ms/chunk → N=8 时 ρ=1.06，积压无界增长（1→8 chunk），服务退化为
~15s 周期的涌现轮转，内容陈旧度线性上涨。**绑定点主机相关**：N_ingest = 拍长/t_chunk（我们 7.5 路，
Metronome 主机 ≥128 路——其 t_wall 随 N 缩短证明其未被摄入封顶）。
证据：`E1_service_timeline.png`（轮转楼梯）；N=4/6 对照点（ρ<1 积压恒 1）；修复即证明（下条）。

**A2 · 一个语句修复摄入墙**
把 `process_inputs` 移入 8 线程池（重活恰好都释放 GIL），F−P 排队 1015ms→**3ms**，积压恒 1。
工程债非物理极限。证据：`harness/stream_server_paringest.py`（monkeypatch，venv 零改动）；
e1paringest 运行全套。

**A3 · 显存墙有三种死法，由"耗尽时刻落在拍内/拍间 × 摄入是否积压"决定**
① **复合死锁**（串行摄入）：一次抢占 → 受害者带着"全序列准入门票"插队头 → FCFS `break` 锁死全体
（run=0/wait=8，5% 显存空置永不可用）；② **幸存者通吃级联**（并行摄入）：池打满 100% → 逐个抢占，
间隔按 1/N_alive 拉长（30→41→58→87→144s），终态 2 幸存者各揣 25.8k tok；③ **同步准入冻结**（种子
锁步）：池恰在拍间打满 → 无人在跑无从抢占 → 全员滞留 skipped_waiting（kv=1.000/run=0/wait=0/pre=0）。
证据：`E1_deadlock_anatomy.png`、`E1_cascade_anatomy.png`、`E1_cascade_lanes.png`、e1paringest_n8_d180。

**A4 · 级联的时钟确定、受害者任意**
两次独立运行六次抢占时刻吻合 **±0.4s**（600s 全程），受害者名单完全不同（`running.pop()` 瞬时排列）；
行刑瞬间受害者与幸存者上下文差仅 **2–3 token（0.03%）**。"何时杀人由池算术决定，杀谁纯属任意。"
证据：e1paringest vs e1schtr 两组 600s 运行的 kv.log 对照。

**A5 · 死者永不复活的棘轮**
受害者复活门票=全序列（`full_sequence_must_fit` 默认开），且饿死后仍被贪婪前端持续喂大
（9.4k→24.9k tok）；空闲从未超 ~12% → 全部运行中复活次数为零。
证据：per-request T/F 事件时间线；`scheduler.py:995` prepend + `kv_cache_manager.py:354`。

**A6 · 双等待队列是形态①/②的分野**
挂起等输入的会话走 `skipped_waiting`（FCFS 下绝对优先，`scheduler.py:1667`），等显存的走 `waiting`；
摄入积压把全员赶进 `waiting` 排在毒丸后 → 全灭；摄入健康则活会话绕过毒丸 → 只死受害者。
附：statlog 的 `wait=` 不含 skipped 队列（形态③读数 wait=0 的原因）。

## B. 仪表盘失明（为什么运维看不见死亡）

**B1 · 假 REAL-TIME**：worker 等待帽 1.6s < 2s 死线 → 崩溃状态下每拍准时返回空帧，miss 恒 0%、
帧交付 100%。Metronome "silent collapse" 的每会话粒度版。
**B2 · 帧延迟 ≠ 内容延迟**：摄入积压期客户端延迟恒 1ms（burst 预存 8 拍 token 存货），而语义回应
滞后最多 ~16s——cadence 指标结构性测不出内容陈旧度，双工 serving 需要独立的内容时效 SLO。
**B3 · MML 僵尸**：上下文触 max_model_len 后会话假稳定（0-1ms"健康"）。
**B4 · 1601ms 签名是简并的**：计算墙和显存墙透过同一个等待帽都读作 1601ms——定性必须配
KV 轨迹 + SM util（SM 高位=计算墙，归零=显存墙）。

## C. 拍内执行剖面（引擎每 2 秒在干什么）

**C1 · 稳态剖面**（43 拍一致）：8 路 84ms 内全部进 batch（p95 164ms，无任何跨会话屏障——先完成
prefill 的立即 decode）→ **89% 的步是纯 batch=8 decode，21.0ms/步** → 收尾 2–3 步配额领完退场 →
忙碌 811ms/2000ms。encoder **152/152 与该会话 prefill 同步共排**，从无独立 encoder 步。
证据：`E1_exec_lanes.png`；e1periter/e1schtr 逐步日志。

**C2 · 每拍 33 token 的真实出处**：vLLM 对 resumable 请求的 max_tokens 语义是**每段独立**
（段边界清零输出计数，`scheduler.py:1058`），worker 的累计式公式 `25n+8` 实际退化为恒定 33/段
（幸存者 9900 tok = 33×300 段，精确）。拍结构完全由音频到达节奏外部塑形，引擎对"拍"零感知。

**C3 · 本系列全部运行处于 async scheduling 模式**（0.23 对 None 默认启用，日志被 WARNING 吞掉）：
步间隔 = 流水线节拍 = 纯 GPU 步时（两家项目口径一致）；拍开场首步在流水线排空后含 CPU 串行成分,
"encoder+prefill 耗时 48–86ms"应读作上界。

## D. 硬件闭式（可跨代际外推的部分）

**D1 · 撞墙步时不变量**：池满时每步读 (W+M)/BW ≈ **0.9×显存/带宽**——模型大小只改权重/KV 分账不改
总字节（预测 25.4ms vs 实测 24.8–27.2ms）。而"整卡读一遍"跨五代硬件恒为 24–36ms →
**撞墙时 busy/T ≈ token率×0.9×(V/BW)，对模型、拍长、显卡代际三重不变 ≈ 38–55%**：
"显存杀死会话时算力恒有约一半空闲"是结构性质。边界：B > B* ≈ 字节/参数×TFLOPS/(2BW)（3090 约
40–80）后 MLP 计算 bound 化；MoE 反向偏离；超语音级 token 率正向侵蚀。

**D2 · 忙碌是总驻留字节的函数而非会话数的函数**：六次抢占时刻 N×ctx 恒 = 74.3k tok（双曲线守恒，
8×9.3k=3×24.8k），busy 均 ~1050–1090ms。附赠 M 的最精标定 74.3k tok = 3.97GiB。

**D3 · TDMA 去同步守恒律**：B̄ ≥ N×配额×t_step/T ≈ 2.8——去同步 = 用算力 slack 购买 KV 常驻缩减
（权重每步重读为代价），上界 T·BW/(配额×W) ≈ 3.4（3090+7B）。**连续旋转优于离散槽**：相位差 T/N
铺开 → 链路双向各 ~2.1GB/s 恒定（vs 12.3GB/s 容量）。同步拍下传送带无收益（忙碌窗内每步读全员 KV，
峰值常驻不降）——时间排他性是容量扩展的必要条件。

**D4 · 3090 稳态容量预测（E2 预告）**：conveyor 后 N=15–16（**2×**），封顶在算力而非链路
（PCIe 利用率仅 ~26%；理论 (M+P)/M=4.9× 要 N≈39，需 4.7s 算力预算，本卡给不出）。
收益闭式 = min((M+P)/M, 算力倍数)。

**D5 · 显存台账**：21.6GiB 预算 = thinker 权重 16.64（含 **vision tower 1.26GiB 纯白占**，折合
+30% 池容量）+ 激活 ~0.5 + KV 池 ~4.0GiB。

## E. 生态对表

**E1 · Metronome paper 归因正确、repo 笔记已被取代**：paper 明写 "memory cliff, not a compute
drift"（含 stat-logger 图与亚稳态竞速模型）；其 repo 工作笔记的 "attention drift" 是废弃旧说。
我们的增量 = 调度器代码级死锁解剖 + 每请求粒度 + 消费卡复现 + 三形态分层。
**E2 · 他们的 30B 每步 decode 4.8–14ms**（fused FP8 MoE probe）→ 其撞墙 slack 比我们更大（MoE 偏离
D1 不变量的方向）。
**E3 · "residency is the only budget-compatible choice"（其 §2 对 swap 的分析性排除）的两个可证伪
假设**：全量轮换 strawman（真实设计点是部分驻留+链路扩容；我们操作点全量轮换都只需 4.2GB/s）与
"无空隙可藏"（子拍占空比 1/N 就是空隙；E0 实测 κ=1.067 搬运近乎白嫖）。C2C 900GB/s 加速此论断过期。
**E4 · DuplexOmni 的 480ms 切片 = 我们 D2 拍长**（负载保真背书）；其"延迟推理"通道（[THINK]→异步
云端推理→结果织回后续切片）= E4 注入负载的量产形态，而其论文零 serving 数字（无并发/每卡会话）——
模型论文止步于 N=1 RTF<1，serving 层是空白。

## F. 测量学教训（本战役自己踩出来的）

**F1 · 限流采样不可用于快尺度结构推断**：1Hz statlog 把 89% batch=8 混叠成"典型 3–5"；同类修复：
Perfetto 导出的并发 counter 改由逐步 trace 派生。
**F2 · 跨时钟必须逐 run 锚定**：三类日志（perf/unix/statlog）偏移每次不同（−15.6 vs −25.7s）；
泳道对齐用物理不变量 min(prefill_start−tick)=+3ms。
**F3 · 图的分辨率不得超过仪器分辨率**：块宽占位值事件（服务时长无数据时禁止画宽度）；
时间轴图必须画真实拍边界（坐标整数刻度会被读成节拍）。
**F4 · 残差归因前先验前提**：同步模式假设未验证 → "2–4ms 空泡"过度归因（残差小于带宽假设误差带）；
async 默认开启这一前提本身就是发现（C3）。
**F5 · 默认值语义要查解析代码**：`bool|None=None` 实为"自动开"。
**F6 · 前提性 bug 的杠杆**：种子单位失准（1.6 tok/词）意外发现"越界启动=零秒复现准入死锁"——
现为最快的死锁 repro。

## G. 工具资产（复用入口）

暖启动种子（`--seed-tokens`，撞墙时间 217→125s，ctx 成为受控变量）；调度器逐步 trace（sitecustomize
注入 EngineCore）；每请求 P/F/T 事件；Perfetto 导出（`harness/viz/export_perfetto.py`，泳道+counter
一条命令）；共租守卫 `harness/wait_quiet.sh`。
