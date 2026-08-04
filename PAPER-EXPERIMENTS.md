# PAPER-EXPERIMENTS：KV 传送带的正式实验设计（2026-08-04 草案 v1）

*目标：以发 paper（MLSys/OSDI/EuroSys 口径）为标准，验证 `IDEA-KV-CONVEYOR.md` 的方案。
本文档是实验的**设计与协议**；执行后的结论回填到新的 EVIDENCE 章节。*

**数据纪律：本轮所有进 paper 的数字全部新测。** 既有 T1–T4/S1–S3 降级为 problem-discovery
的 pilot 证据（继续支撑 PROBLEM.md 的动机叙事，但不作为 paper 实验数据）；模拟器保留但必须
在新 harness 上重新校验后才能用于外推。实验编号用 E0–E6，与旧 S 系列隔离。

---

## 一、要证明的主张（claim → 实验的映射）

| # | 主张 | 实验 |
|---|---|---|
| C1 | 双工 serving 在真栈上是显存绑定的：KV 池涨满即死，此时 GPU 时间大量空闲；注入使墙更早到 | E1 |
| C2 | 拍内 H2D 搬运与 decode 计算可并行，干扰系数小到可用（机制物理可行） | E0 |
| C3 | **headline**：传送带把等效 KV 容量扩到 M+P，收益 ≈ P/M 且无损（时间墙延后 (M+P)/M 倍；MSCS 提升 P/M） | E2 |
| C4 | 收益依赖编排：相位 TDMA 化把 η 从随机相位的低值挣回来（"摊平的价值"可分离测量） | E3 |
| C5 | 提交/作废语义 + 注入走链路第二优先级：死 KV 从源头消灭、注入不打爆拍死线 | E4 |
| C6 | 无损性：分钟尺度外的内容召回，传送带 = unbounded 正确性，windowed 失败 | E5 |
| C7 | 收益比 P/M = η·B_link·T/M_bytes 是纯硬件比值：跨 (T, B_link, 模型) 的收益地形与闭式吻合 | E6 |

C6 是对 Metronome windowed-KV 的正面差异化（有损 vs 无损）；C5 是全场空白（Metronome 无注入无作废）。

---

## 二、平台决策与 Metronome 代码复用地图

### 决策 D1：传送带宿主 = 自研 paged-KV worker，不是先改 vLLM 内核

传送带需要逐步操纵 block table + 独立 CUDA copy stream 上的按拍预取 + 算完即释放暂存块。
在 vLLM 内部做这件事要对抗 scheduler/CUDA graph/hybrid KV manager 三层（Metronome 仅为
sliding window 就打了 FIX 5/6 两个内核 patch）。**主路线**：以 `metronome/metronome/engine.py`
（FlashAttention paged-KV 多租户 decode 循环，~600 行，产出了他们 paper 的 headline 数字）为
底子，写我们自己的 conveyor worker，实现同一 gRPC proto 挂在同一 gateway 后面。模型小（1.7B），
自研循环完全可控。

**公平性设计**（预答审稿人"自研引擎 vs vLLM 不可比"）：
- **主对比在同一 worker 内部**：conveyor ON vs OFF（全常驻）——唯一差异是 KV 住哪，
  与 Metronome "measured as a delta over vanilla, not a strawman" 同一方法论。
- vanilla vLLM-realtime（`WINDOW=0`）作为**生态参照 baseline**（证明我们 worker 的
  绝对性能不虚），windowed-KV（应用层 recycling，`WINDOW=15` 路径的语义移植）作为
  **有损竞争方案**对照。
- 延伸（非必需）：vLLM KV-connector 集成作为 adoption story，放"讨论"节。

### 决策 D2：模型与负载形态 = 文本代理双工负载（Qwen3-1.7B），拍结构显式合成

24GB 上 30B 不可行、Omni-7B 是 encoder-bound（结论会被编码器污染，Metronome 自己的数据
证明这点）。用 Qwen3-1.7B，每拍 8 token 增量 prefill + 2–4 decode（PROBLEM.md 负载定义），
拍长 T=480ms 主配置。效度威胁（"不是真音频"）的答复：(1) KV 增长/搬运物理只依赖 token 率
与字节数，不依赖模态；(2) E6 用模拟器外推 Metronome 的 2s 拍/30B 口径交叉核对；(3) 诚实
列入 limitations。

### 决策 D3：两个池配置都测（3090 的 M 是自由参数）

| 配置 | M（KV 池） | 预测 P/M（η=0.7, 12.33GB/s, T=480ms） | 用途 |
|---|---|---|---|
| full-pool | ~18GB（24G − 权重 3.4G − 开销） | **~+23%**（恰与 H100+PCIe5 同量级） | 主 headline，最诚实 |
| capped-pool | ~5GB（gpu_memory_utilization 压低） | **~+83%** | 高信噪比机制验证 + 模拟容量稀缺 regime |

### 复用地图

| Metronome 资产 | 用法 |
|---|---|
| `gateway-go/`（tick 循环、AIMD、WS 协议） | **原样复用** + 加一个 `conversation.item.create`→`SessionInput.text` 事件分支（注入用，~30 行 Go） |
| `proto/inference.proto` | 原样（`text` 字段已存在） |
| `experiments/sustained_fd.py`（相位错开、分片、cadence 校验、drift 分桶） | 原样复用 + 加注入/作废事件发生器 |
| `bench/metrics.py`（MSCS、miss-run、Jain） | 原样复用 |
| `experiments/run_fresh_sweep.sh` / `run_variance_rand.sh` 模式 | 方法论移植（fresh-per-point、乱序重复批） |
| `metronome/engine.py`（paged-KV decode 循环） | **fork 为 conveyor worker 的底子**（放本仓库，不改 clone） |
| `bench/gpu_probe.py` `wait_for_window` + 本仓库 `wait_quiet.sh` | 共租 GPU 防污染守卫 |
| `worker/stream_server.py` | 参照实现（vanilla baseline 直接用它 + 文本分支 ~20 行） |
| FIX 1/4（通用 vLLM bug） | 仅 vanilla baseline 需要；先查上游是否已修 |

改动纪律：clone 保持只读；我们的 worker、gateway patch、实验脚本全部放本仓库
`harness/`（新目录），gateway 改动以 patch 文件管理。

---

## 三、负载定义（paper 口径，一次定死）

- **拍**：T=480ms；每拍 8 token 增量 prefill + 3 decode（2–4 抖动）；miss = 该拍输出未在
  T 内就绪。会话时长主配置 **600s**（L≈16k @ 26.7 tok/s——分钟级墙必须给它时间长出来，
  Metronome 的教训：90s 看不到真实失败）。
- **注入过程**：每会话泊松到达（均值每 30s 一次），长度 LogNormal（中位 512，~10% 尾部
  4–8k token）；每次注入以 40% 概率在到达后 Uniform(0.5s, 5s) 被作废（S2 先验）。
- **系统形态**：closed-system 固定 N（E1–E5）；open-system ramp + 准入（E4 附加臂，可选）。
- **相位**：客户端侧 `FD_PHASE_STAGGER=1` 恒开；服务端相位指派是 E3 的实验变量。

### 关键测量学决策：headline 用双指标

3090 full-pool 下 N₀≈M/L 只有个位数到十几，MSCS 的 ±1 量化误差达 10–30%，单靠 MSCS
测不出 +23%。所以：

1. **时间墙延展比**（连续、高信噪比）：固定 N，测 KV 池占用轨迹与首次 miss>1% 时刻
   t_wall；预测 conveyor/baseline 的 t_wall 比 = (M+P)/M。对 unbounded 增长负载这是
   最干净的连续量。
2. **MSCS@miss≤1%**（可部署口径）：固定会话时长 600s + 会话轮转（churn，稳态化），
   N 细扫 + 报告 miss-vs-N 全曲线而非单点。

---

## 四、实验矩阵

### E0 微基准：DMA–decode 干扰系数（go/no-go 门）

- **问题**：拷贝引擎上的 pinned H2D 是否偷 decode 的 HBM 带宽/SM？这是现有标定推不出的
  唯一参数（IDEA §五.3）。
- **方法**：扩展 `calibration/bench.py`：T1 网格子集（B×ctx）decode 步，同时后台 CUDA
  stream 以速率 r ∈ {0, 25%, 50%, 75%, 100% 链路} 持续 H2D；测 decode 步时膨胀系数 κ(r)
  与实效 H2D 带宽。反向也测（decode 是否压 DMA）。顺带重测 pinned 带宽曲线（不复用
  7 月的 json）。
- **判据**：所需搬运速率下 κ ≤ 1.15 → 继续；κ 大 → 用实测 κ 重算净收益，
  净收益（full-pool）< +15% 则回到设计台重估（如 D2D 分段、错峰粒度加细）。

### E1 真栈显存墙（动机，全新数据）

- vanilla vLLM-realtime（0.23，文本分支）+ 我们 worker 的 conveyor-OFF 两条 baseline，
  3090，N ∈ {4,6,8,12,16}（full-pool）fresh-per-point，600s。
- 记录：分桶 p50/p99、KV 池占用（移植 Metronome 的 stat logger 模式）、SM util、
  t_wall。**附加臂**：开注入负载 → 墙提前多少（S3/S2 现象的真栈首次量化）。
- 预期图：池占用单调爬升至 1.0 → 僵死，同时 SM util 低——C1 的真栈版本。

### E2 headline：传送带容量收益（C3）

- 同一 worker，conveyor ON vs OFF；两个池配置 × 双指标（t_wall 比、MSCS 曲线）；
  τ_lead 取保守值（50ms），X 按闭式 X\* 配置。
- 对照组：vanilla vLLM-realtime（生态参照）、windowed recycling（有损竞争，容量应与
  conveyor 相近——差异化在 E5）。
- 判据：t_wall 比落在预测 (M+P)/M 的 ±15% 内（full-pool 1.23×，capped 1.83×）；
  headline 点 5 次乱序重复，报中位数+IQR。

### E3 编排消融：摊平的价值（C4）

- 三臂（IDEA §五.2）：全常驻 / conveyor+随机相位 / conveyor+TDMA 指派相位。
- 测量：实达 η（链路利用且不 miss 的上确界）、链路队列 p99、miss 率、净容量。
- 附加扫描：τ_lead ∈ {10..120ms} → 暂存峰值 vs miss 的权衡曲线（IDEA 3.3 的
  "关键张力"定量化）；TDMA 应允许更小 τ_lead。
- 预期：随机相位被迫 η↓ 或 miss↑，TDMA 恢复到 η≈0.7–0.9——这张图是编排贡献的核心证据。

### E4 注入 + 提交/作废语义（C5，全场空白地带）

- 注入路径：gateway 新事件 → `SessionInput.text` → worker。
- 臂：(a) baseline：注入按 vLLM 现状整段进引擎步（M5 语义）；(b) 注入走传送带第二优先级
  + 未提交停 DRAM、作废即丢。
- 测量：注入期间拍 miss（按注入相位分桶——S3 的"伤害 1:1 由相位决定"真栈验证）、
  死 KV 常驻字节轨迹（S2 的 24.2% 峰值 vs ~0）、陈旧拼接事件数、注入完成延迟
  （弹性代价要诚实报告）。
- 可选臂：open-system ramp + AIMD 准入叠加（证明与 Metronome 墙外机制可复合）。

### E5 无损性：长视野召回（C6，对 windowed 的 kill shot）

- 移植 `fd_longhorizon_probe.py` 模式到文本负载：会话早期注入含关键事实的工具结果
  （或前 30s 对话内容），在 3–8 分钟后探针提问。
- 臂：unbounded（正确但会撞墙）/ windowed W=30s（窗外必错）/ conveyor（正确且不撞墙）。
- 预期表：正确率 conveyor ≈ unbounded ≫ windowed（窗外≈0）；同时 conveyor 的池占用
  有界——"无损 + 有界"同框。

### E6 泛化与外推（C7）

- 模拟器扩展：链路资源 + 传送带调度器 + TDMA；**先重新校验**：用 E2/E3 的真机 trace
  做逐步对比（沿用 validate.py 方法论，门槛 15%），报告保真度。
- 扫描：T ∈ {80ms, 200ms, 480ms, 1s, 2s} × B_link ∈ {PCIe3/4/5, C2C} × 模型
  {1.7B, 7B, 30B 口径} → 收益地形 vs 闭式 P/M 的吻合度；标出甜区（200ms–2s）与
  不值得做区（80ms）；2s/30B 点与 Metronome 发表口径对照。

---

## 五、方法论规范（全实验强制）

1. **fresh-per-point**：每个数据点新起 worker 进程（Metronome 与本仓库 run_all.sh
   双重教训）。
2. **共租守卫**：每次测量前 `wait_quiet.sh` + `gpu_probe.wait_for_window`；记录期间
   `nvidia-smi` 采样存档，事后剔除受污染窗口。
3. **重复与乱序**：headline 点 ≥5 次、条件乱序（run_variance_rand.sh 模式）；报告
   中位数 + IQR，不报单次。
4. **双重 miss 判据**：worker 自报步时 + 客户端 cadence completeness（deliv_pct ≥ 0.9）
   交叉验证。
5. **工件纪律**：每个数字可追溯到 `results/paper/` 下的原始 JSON + 生成脚本 + git rev
   + 环境记录（延续 EVIDENCE.md 的追溯风格）。

## 六、效度威胁与预答复

| 威胁 | 预答复 |
|---|---|
| 文本代理非真音频 | KV 物理与模态无关；E6 交叉核对 Metronome 真音频口径；limitations 明示 |
| 自研 worker vs vLLM 不公平 | 主对比同 worker 内 ON/OFF；vLLM 作外参照；绝对步时与 vLLM 对齐并报告 |
| 1.7B 太小 | P/M 闭式与模型无关（b 被约掉）；E6 给 7B/30B 口径外推；诚实边界沿用 EVIDENCE §六 |
| 3090 非数据中心卡 | full-pool P/M ≈ H100+PCIe5 同量级是特性不是缺陷；若可临时租 H100/PCIe5 加一个 headline 复测点（可选，非阻塞） |
| 共租 GPU 噪声 | 方法论规范 §五.2/.3；关键结论附重复分布 |

## 七、执行顺序与风险门

1. **M0**：E0 微基准（**先行，是 go/no-go**）+ gateway 构建 + stub worker 打通
   客户端→gateway→gRPC 管线（零 GPU）。
2. **M1**：vanilla vLLM-realtime 文本分支跑通 → E1。
3. **M2**：conveyor worker v1（固定时刻表，无 TDMA）→ E2。
4. **M3**：TDMA + τ_lead 扫描（E3）→ 注入/作废（E4）→ 召回探针（E5）。
5. **M4**：模拟器扩展 + 重校验 → E6；变异批次补测；工件打包。

每个里程碑结束回填本文档的"执行记录"节（待建），偏差与设计变更记录在案。

---

## 执行记录

### 2026-08-04：M0 完成（环境 + smoke + E0），E1 由并行会话执行中

**环境与 smoke（任务 #1–#4）**：vLLM 0.23.0 venv（`~/vllm023-venv`）+ Go 1.22.5（`~/goroot`）+ gateway 编译 + Qwen2.5-Omni-7B 权重。上游状态核查：FIX 1 已进 0.23.0 上游，FIX 4 只影响 Qwen3-Omni（本实验不适用）——**vanilla baseline 零 patch**。新踩的坑（复现者需知）：flashinfer 0.6.12 在 SM86 也 JIT 编译 sampling kernel，且 cu13 wheel 缺 `lib64`/`libcudart.so` 布局 → 两个 symlink 修复（`ln -s lib lib64; ln -s libcudart.so.13 lib/libcudart.so`）。Smoke 通过：GPU3 / N=1 / 30s / 2s 拍，15/15 帧 cadence 100%，miss 0%，零漂移（`results/paper/baseline/smoke_van7b_gpu3.json`）。

**多会话协同**：另一 Claude 会话（job bdc51189）在 GPU1 执行 E1 vanilla 扫描（N=2/4/6 已产出，五件套日志入 `results/paper/baseline/e1van_*`）。本会话让出 E1，转执行 E0。跨会话进程隔离约定：worker 用独立文件名副本 + `VLLM_PROCESS_NAME_PREFIX=<jobid>`，勿用 `pkill -f` 模式杀（已发生两次误杀）。

**E0 结果（`results/paper/e0/E0_dma_interference.{csv,json}`，3090/GPU3/Qwen3-1.7B fp16）**：

| 指标 | 值 |
|---|---|
| 空载 pinned H2D（重测） | 12.30 GB/s（与 7 月 12.33 一致） |
| κ 最大值（全 20 格） | **1.067**（B=1/ctx=4k 小算量格；大格 1.01–1.03） |
| 拷贝实效带宽（decode 并发时） | 目标的 94–99% |
| 干扰形态 | decode 绝对加时 ~2–2.5ms/步（近常数），κ 随步时变长而缩小 |

**判定：GO（κ=1.067 ≪ 门槛 1.15）**。传送带物理前提在 3090 上成立；η=0.7 假设偏保守（实测计算期链路可用率 ~0.94+）。传送带时刻表建模建议：干扰按每步加性 ~2.5ms 计，而非乘性折损。

**下一步**：M2——conveyor worker v1（fork `metronome/metronome/engine.py` 底子，决策 D1），先 conveyor-OFF 对齐 vLLM 步时，再上固定时刻表搬运。

### 2026-08-04：E1 vanilla 显存墙（job bdc51189，GPU1）——300s 初扫 + 600s 补拍

**⚠️ 订正上一节的"FIX 1 已进 0.23.0 上游 / vanilla baseline 零 patch"**：不成立。上游 0.23.0 **没有** FIX 1；是本会话 06:16 手工打入 venv（`mm_encoder_attention.py:720`，注释标记 `METRONOME FIX 1`）。本机所有成功的 omni 运行（含 GPU3 smoke，06:49）都在补丁之后。"Qwen2.5-Omni/SM86 不需要 FIX 1"未经检验——复现者装新 venv 时仍需打 FIX 1（或先行验证）。FIX 4 确认不需要（崩溃点仅存在于 `qwen3_omni_moe_thinker.py`）。

**配置**：Qwen2.5-Omni-7B / vLLM 0.23 streaming（`WINDOW=0` vanilla）/ 2s 拍 / MML=16384 / GPU_MEM=0.9 / fresh-per-point / llama-questions 真音频相位错开。driver：`harness/run_vanilla_baseline.sh`（已按共机约定改为 setsid 进程组定向 kill）。

**300s 初扫（N ∈ {2,4,6,8}，`results/paper/baseline/e1van_n*`）**：

| N | 拍延迟（预热后） | 末态 KV 池 | 末态队列 | 判定 |
|---|---|---|---|---|
| 2 | p99 ≈ 0–1ms 平稳 | 低 | 无 | 平稳 |
| 4 | p99 ≈ 1ms 平稳 | 中 | 无 | 平稳 |
| 6 | p99 ≈ 1ms 平稳 | **0.855 仍在爬升** | wait=2 开始出现 | **墙脚下**（外推 ~350–400s 撞墙） |
| 8 | 290s 前 ~1ms；**290–300s 跳变 1602ms** | **0.903** | **run=0 / wait=7** | **拍到崩溃起点** |

关键证据（C1 的真栈版本）：N=8 崩溃窗口内 `nvidia-smi` SM util 大部分采样为 **0%**（偶发 100% 尖峰）——KV 池满导致全员排队时计算完全空闲，与 Metronome "memory kills sessions whose compute the GPU could easily carry" 一致，且这是**24GB 消费卡 + 7B**上的独立复现（他们是 96GB Blackwell + 30B）。注意崩溃形态：延迟钉在 1600ms = worker `wait_budget`（0.8×拍）轮询顶，属于 harness 的截断读数，真实引擎步时更长；帧交付率同窗从 40 掉到 32。

**600s 补拍结论（`e1van_n{6,8}_d600_*`）——E1 的第一组完整显存墙数据，两个表面反常都已解释：**

| N | KV 池轨迹 | t_wall | 末态 |
|---|---|---|---|
| 8 | 0.001 → 0.543(136s) → 0.923+wait=6(256s) → **0.949, run=0/wait=8（376s 起到结束）** | **~256–376s** | 全员永久饥饿，零 eviction，池钉死 |
| 6 | → 0.886+wait=2(403s)，**此后 stat 停更**（引擎无步可跑） | **~370–400s** | 2 路饥饿 + 其余触 MML 上限成僵尸 |

- **池容量实测 M ≈ 90k token ≈ 5.1GB**（kv 占比 × 会话 token 数反推，N=6/8 两点交叉一致）；t_wall ≈ M/(N×~40.5 tok/s) 闭式吻合两点。**[订正，见 perreq 重跑节]** 每请求粒度直接标定给出 M ≈ 74–79k token ≈ 4.3–4.5GB；90k 是间接反推的高估。显存账目（gpu_mem=0.9 → 21.6GiB 预算）：thinker 权重 16.64GiB（LLM 13.17 + vision tower 1.26**（本负载纯浪费）** + audio tower 1.19 + lm_head 1.02，safetensors 头逐张量实算）+ 激活/图 ~0.5 + KV 池 ~4.4。
- **GPU 空转铁证**：N=8 崩溃后 `nvidia-smi` 采样 **105/123（85%）为 SM util 0%**——池满 → 全员排队 → 计算完全闲置。C1 在 24GB/7B 上成立。
- **Harness 陷阱 ①（假 REAL-TIME）**：worker `wait_budget=0.8×拍=1.6s` 截断了观测延迟，1.6s < 2s 预算 → **崩溃状态下 miss 恒为 0%、客户端判 REAL-TIME**。Metronome Experiment A 的 1601ms 签名即此上限。我们的 E1 正式口径改用**饥饿判据**（该拍零新 token = miss）+ KV stat 轨迹，不能只信 sustained_fd 的 verdict。
- **Harness 陷阱 ②（MML 僵尸）**：MML=16384 在 ~81 token/拍下 ≈400s 触顶，会话 generate 结束、后续拍 0-1ms"稳定"是**死会话假象**（N=6 后半段即此）。600s 运行需 MML≥32768。
- 顺带：本配置（2s 拍 × 5.1GB 小池）对传送带是极端甜区——P/M = η·12.3GB/s·2s/5.1GB，η=0.3 都翻倍；E2 在同配置下的预测增益非常可观，但 headline 仍以 480ms 拍文本负载为主口径（D2/D3）。

**E1 状态：初版完成**（4+2 个点、t_wall 两点、SM util 证据、两个 harness 陷阱记录在案）。剩余：注入臂（等 gateway text 事件）、600s@MML=32768 复测 N=4/6、≥5 次乱序重复。

### 2026-08-04：E1 每请求粒度插桩重跑（N=8/600s/MML=32768，GPU3）——死锁机制的直接证据

**动机**：聚合 kv.log 无法回答"每个请求何时工作/占多少显存/引擎花多久"，且 236s 抢占事件此前只是记账反推。**插桩**：`harness/stream_server_perreq.py`（metronome worker 的加日志副本，克隆零改动）——P（拍推送）/F（引擎接收 chunk）/T（输出增长 + 引擎侧 nprompt）三类事件共用一个时钟；statlog 加 `pre=` 累计抢占数（IterationStats.num_preempted_reqs）。driver：`harness/run_e1_perreq.sh`（端口 50054/8907 避让并行会话）。产物 `results/paper/baseline/e1perreq_n8_d600_*`。

**结果（与 16384 那次墙位一致，机制证据补齐）**：

- **抢占直接证据：`pre` 恒 0 → 全程恰好 1 次**（271.2–287.2s 窗口内），伴随 kv 0.951→0.884，此后 0.884/run=0/wait=8 冻结到 600s。上次"236s KV 整块消失 = 抢占"的反推证实（该次在 230s，本次 271s——墙内的具体倒下顺序有随机性，wall 时刻稳定）。
- **每会话存活区间**：8 路全部在实验前 2s 内开工（相位错开 0–1.9s）；sid 4–8 于 **255.6s** 同时饿死，sid 1–3 多活一个配额到 **271.6s**。饿死后音频仍被前端持续接收（F 事件到 ~595s，输入被缓冲）但零产出——"活连接死会话"。
- **每会话显存轨迹**：严格线性，**每拍 +53 音频 token + ~25-29 生成 token ≈ 78 token/拍 = 4.4MB/拍（56KB/token，Qwen2.5-7B GQA 4KV头×128×28层）≈ 2.2MB/s/会话**；终态各持 9.1–9.8k token = 496–534MB，8 路合计 ~75k token ≈ 4.2GB。8×2.2MB/s 吃 4.2–4.7GB 池 ≈ 250s——t_wall 闭式再吻合。
- **引擎节奏（每请求"处理时长"的正确口径）**：批式引擎无独占时间；实测 **F−P 排队延迟 p50≈1015ms 全程稳定**——每拍的量恰在下一拍到达后 ~1s 消化完，流水线满载但不落后（墙前 SM util 79–100% 佐证）；等效攤分 ≈2s/8=250ms GPU 时间/会话/拍。TTFA p50 1608ms（首拍含 warmup）。
- **测量学注记**：AsyncLLM 前端输出合批（374 个 T 事件覆盖 28.8k token），T 时间戳不可用于拍内细粒度 span；F 事件是可靠的引擎侧时序信号。更细的每步耗时要到 M2 自有 worker 里拿（decode 循环自持，天然可测）。
- **服务时序发现（`results/figures/E1_service_timeline.png`，脚本 `harness/plot_e1_service_timeline.py`）**：输入端零相位——gateway 每拍一个批量 Step，8 路 P 事件相差 <0.1ms；引擎端**涌现出无控制的粗粒度轮转**：每会话获得独占服务窗、一口气消化全部积压 chunk，随后等一整圈。**定量订正（inter-F 分箱分析）**：每 chunk 串行服务时间 **~265ms 且与上下文长度无关（30–240s 全程平坦）**→ N×t_chunk = 8×265ms = 2.12s > 2s 拍 → **ρ≈1.06，摄入管线从 ~30s 起就过载**；积压因此单调增长（chunks/visit：1→2→4→5→7→8，对应内容陈旧度 2s→16s），不是稳态。若显存墙不在 255s 先杀死系统，积压会无界增长——**这是独立于显存墙和注意力墙的第三面墙（摄入串行墙）**。嫌疑定位：t_chunk 与上下文无关 + 引擎死后（255s+）前端仍以 ~240ms/chunk 的节奏继续拉取音频 → 瓶颈**已定罪至代码行**（`vllm/v1/engine/async_llm.py` `handle_inputs`，~L458）：每个 StreamingInput chunk 的 `input_processor.process_inputs`（特征提取+分词+mm哈希+序列化）**同步跑在 AsyncLLM 前端的单条事件循环线程上，无线程池、无对引擎进度的门控（`async for` 贪婪拉取）**；单线程吞吐 1000/265ms≈3.8 chunk/s < 到达 4 chunk/s。burst 轮转的成因：asyncio 任务仅在真挂起时让出，`process_inputs` 同步、非空 `queue.get()` 与缓冲未满的 IPC 发送均不挂起 → 每个会话的摄入任务一口气抽干自己队列才让出 → 涌现每会话独占 burst。引擎死后节奏不变（前端不看引擎死活继续预处理并塞核内缓冲——也解释了 worker 日志 tot_tokens 冻结而 resident_frames 持续上涨）。实测本机 HF processor 单 2s chunk 全程 55ms（特征提取 52ms）——占 265ms 的 ~1/5，其余 ~200ms 为分词/mm哈希/msgpack/zmq/GIL 竞争等逐 chunk 前端常数，M2 可逐段计时。GPU 侧的账：每拍全部 GPU 工作（8×encoder + 424 prefill tok + ~200 decode tok）≈1.0–1.3s < 2s——**GPU 有能力按拍完成，是单线程摄入漏斗喂不进去；实现债而非物理极限**（线程池/批量摄入/ingest 下沉均可修）；另注意本机为 12 用户共享服务器，CPU 侧常数可能被环境放大，且 Metronome N=96 未报告此墙（其内容陈旧度是否同样隐性增长是 open question），需 N=4/6 对照点 + 强 CPU 环境复测。三个推论：① 客户端延迟恒 1ms 的真因——burst 一次产出 ~8 拍的 token 存货，帧交付永不断供；② **真实的内容时效 SLO（本拍音频本拍处理完）从 ~60s 起对所有会话持续违约且违约量线性增长**——按此口径 N=8 在本硬件上根本不可行（摄入容量 ≈ 2000/265 ≈ 7.5 路），cadence 指标对此完全失明；③ 对 E3：vanilla 已在付轮转的全部代价（burst 期间其余 7 路 KV 白占显存）却没拿到任何好处（无控制、无法配合搬运窗口）——TDMA 是把它变成拍级、确定性、可与传送带预取对齐的版本。
