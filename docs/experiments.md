# EXPERIMENTS：KV conveyor 实验设计

目标：按可投 MLSys / OSDI / EuroSys 的标准验证尾部 KV conveyor 方案。

被试方案 KV conveyor（scheduled tail-KV offloading），等效 KV 容量 = resident M + staging P。

本文持有实验的设计与协议层：主张、平台决策、冻结负载、E0–E6 协议与门槛、方法论规范、效度威胁、执行顺序。
结论层是 `docs/findings.md`，本文以其条目码作证据锚点。
引用记法：`FINDINGS D4` 指该文条目；本文另有主张编号 C1–C7、实验编号 E0–E6、平台决策编号（决策 D1–D3）。四个编号空间互不相通，决策编号引用时带「决策」前缀。

数据纪律：进论文的数字全部来自 E 系列新测；更早的问题发现期试跑只支撑动机叙事，不作为论文实验数据。

## 一、主张与实验矩阵

| # | 主张 | 实验 | 已有锚点（证据或预测） |
|---|---|---|---|
| C1 | 全双工 serving 在真机上 capacity-bound（受 KV 池容量约束，区别于 bandwidth-bound 义的 memory-bound）：KV cache 池涨满即饱和，此时 GPU 时间大量空闲；后台注入使饱和更早到来 | E1 | FINDINGS A3 / A5 / D1 |
| C2 | 一 tick 内 H2D 可与 decode 计算并行，κ（decode step 减速系数 slowdown factor，κ = t_with/t_without）小到可用：机制物理可行 | E0 | FINDINGS E3 |
| C3 | 主结果：KV conveyor 把等效 KV 容量扩到 M+P，收益约 P/M 且内容无损（饱和时刻延后 (M+P)/M 倍；N* 提升 P/M） | E2 | FINDINGS D4（公式预测，E2 待实测） |
| C4 | 收益依赖编排：相位指派 (phase-offset assignment，TDM 式错开) 按时间表错开各路占用，能把链路利用率 η 从随机相位的低值拉回来，指派收益可单独测量 | E3 | FINDINGS D3 |
| C5 | commit / cancel 语义 + 注入走链路第二优先级：stale resident KV（已作废仍常驻的 KV）从源头消除，注入不打爆一 tick 的 deadline | E4 | FINDINGS E4（负载保真背书，非机制证据） |
| C6 | 无损性：分钟尺度外的内容召回，KV conveyor 正确且不饱和，windowed KV（sliding window）窗外必错 | E5 | E5 首次产出 |
| C7 | 收益比 **P/M = η·B_link·T/M_bytes** 是纯硬件比值：跨 tick 长 T、链路带宽 B_link、模型档位的收益地形与公式吻合 | E6 | FINDINGS D1 / D3 / D4 |

C6 是相对 Metronome windowed KV 的正面差异（有损 vs 无损）。
C5 的两列能力（注入 + cancellation 语义）现有系统均未覆盖：Metronome 无注入、无 cancellation。

## 二、平台决策与 Metronome 资产复用

### 决策 D1：KV conveyor 宿主 = 自研 paged-KV worker，不先改 vLLM 内核

KV conveyor 需要逐步操纵 block table，并在独立 CUDA copy stream 上按 tick 预取、算完即释放 staging block。
在 vLLM 内部做这件事要同时对抗 scheduler、CUDA graph、混合 KV manager 三层（Metronome 仅为 sliding window 就打了 FIX 5/6 两个内核补丁）。
主路线：以 `third_party/metronome/metronome/engine.py`（FlashAttention paged-KV 多租户 decode 循环，产出了他们论文的主结果数字）为底子，写我们自己的 conveyor worker，实现同一 gRPC 协议，挂在同一 gateway 后面。
模型小（1.7B），自研循环完全可控。

公平性按三层设计，预答「自研引擎 vs vLLM 不可比」：

- 主对比在同一 worker 内部：conveyor on vs off（全常驻），唯一差异是 KV 住哪，与 Metronome「相对未改动配置测差值，而非和不具代表性的 baseline 比」同一方法论。
- vanilla vLLM-realtime 路径（`WINDOW=0`）作参照 baseline，证明我们 worker 的绝对性能不虚。
- windowed KV（应用层回收，`WINDOW=15` 路径的语义移植）作有损竞争方案对照。
- 延伸（非必需）：vLLM KV-connector 集成作为落地故事，放讨论节。

### 决策 D2：模型与负载形态 = 文本代理双工负载（Qwen3-1.7B），tick 结构显式合成

24GB 上 30B 不可行；Omni-7B 由 encoder 成为瓶颈，结论会被 encoder 污染（Metronome 自己的数据证明这点）。
用 Qwen3-1.7B，每 tick 8 token 增量 prefill + 2–4 次 decode，tick 长 T=480ms 为主配置。

效度威胁「不是真音频」的答复：KV 增长与搬运物理只依赖 token 率与字节数，不依赖模态；E6 用公式外推 Metronome 的 2s tick / 30B 定义做交叉核对；诚实列入 limitations。

### 决策 D3：两个池配置都测（3090 的池大小 M 是自由参数）

| 配置 | M（KV 池） | 预测 P/M（η=0.7，12.33GB/s，T=480ms） | 用途 |
|---|---|---|---|
| full-pool | 约 18GiB（24GiB − 权重 3.4GiB − 开销） | **~+23%**（恰与 H100+PCIe5 同量级） | 主结果，最诚实 |
| capped-pool | 约 5GiB（压低 `gpu_memory_utilization`） | **~+83%** | 高信噪比机制验证 + 模拟 capacity-scarce 区间 |

该表是纯链路公式推演（P = η·B_link·T），未含 compute 封顶。
FINDINGS D4 是同一张卡的真机预测（Qwen2.5-Omni-7B / T=2s / M≈4.0GiB，最精标定 74.3k token = 3.97GiB）：N=15–16、约 2×、封顶在 compute 而非链路，PCIe 利用率仅约 26%。
E2 的验收带取两者的 min()（见 E2 判据）。

### Metronome 资产复用地图

| Metronome 资产 | 用法 |
|---|---|
| `gateway-go/`（tick 循环、AIMD admission、WebSocket 协议） | 原样复用 + 加一个 `conversation.item.create`→`SessionInput.text` 事件分支（注入用，约 30 行 Go） |
| `proto/inference.proto` | 原样（`text` 字段已存在） |
| `experiments/sustained_fd.py`（相位错开、分片、节奏校验、漂移分桶） | 原样复用 + 加注入 / cancellation 事件发生器 |
| `bench/metrics.py`（N*、连续失败段 miss-run、Jain fairness） | 原样复用 |
| `experiments/run_fresh_sweep.sh` / `run_variance_rand.sh` 模式 | 方法论移植（每点新起进程、乱序重复批） |
| `third_party/metronome/metronome/engine.py`（paged-KV decode 循环） | fork 为 conveyor worker 的底子，副本放本仓库 |
| `bench/gpu_probe.py` 的 `wait_for_window` + 本仓库 `harness/wait_quiet.sh` | 共享 GPU 空闲检测（防污染） |
| `worker/stream_server.py` | 参照实现（vanilla baseline 直接用它 + 文本分支约 20 行） |
| FIX 1 / FIX 4（通用 vLLM bug） | 仅 vanilla baseline 需要 |

第三方 pin 与引用纪律的 owner 是 `docs/metronome.md`。
我们的 worker、gateway 补丁、实验脚本全部放本仓库 `harness/`，gateway 改动以补丁文件管理。

## 三、负载协议（冻结）

- 一 tick：T=480ms 的硬 tick（固定周期 T 的硬 deadline 帧，Metronome 的 frame budget B）；每 tick 8 token 增量 prefill + 3 次 decode（2–4 抖动）；miss = 该 tick 输出未在 T 内就绪。
- 会话时长主配置 600s：约 11 token/tick ≈ 22.9 tok/s，600s ≈ 13.7k token。分钟级瓶颈必须给它时间长出来，Metronome 的教训是 90s 看不到真实失败。
- 注入过程（弹性注入，delay-tolerant，对照 inelastic 的硬 tick 前台）：每会话泊松到达（均值每 30s 一次），长度 LogNormal（中位 512，约 10% 尾部 4–8k token）；每次注入以 40% 概率在到达后 Uniform(0.5s, 5s) 被 cancel。这四个数是冻结的负载参数（设计决定，预注册）。
- 系统形态：closed-system 固定会话数 N（E1–E5）；open-system 爬坡 + admission（E4 附加臂，可选）。
- 相位：客户端侧 `FD_PHASE_STAGGER=1` 恒开；服务端相位指派是 E3 的实验变量。

### 主结果用双指标

3090 full-pool 下，可承载会话数 N₀ ≈ M/L 只有个位数到十几，N* 的 ±1 量化误差达 10–30%，单靠 N* 测不出 +23%。所以主结果同时报两个量：

1. 饱和时刻延展比（连续、高信噪比）：固定 N，测 KV 池占用轨迹与首次 miss rate > 1% 的时刻 t_wall；预测 conveyor / baseline 的 t_wall 比 = (M+P)/M。对无界增长负载，这是最干净的连续量。
2. N*（可调度并发数，schedulable concurrency，判据 deadline miss rate ≤ 1%）：固定会话时长 600s + 会话 churn 稳态化，N 细扫，报告 miss rate–N 全曲线而非单点。

## 四、实验矩阵

### E0 微基准：DMA 与 decode 的干扰系数（继续 / 停手的门槛）

- 问题：copy engine 上的 pinned H2D 是否偷 decode 的 memory bandwidth / SM？这是既有标定推不出的唯一参数。
- 方法（工具 `calibration/bench_dma_interference.py`）：在 (batch size B × context length ctx) 网格上跑 decode step，同时后台 CUDA stream 以速率 r ∈ {0, 25%, 50%, 75%, 100% 链路} 持续 H2D；测 κ(r) 与实效 H2D 带宽。反向也测（decode 是否压 DMA）。顺带重测 pinned 带宽曲线。
- 判据：所需搬运速率下 κ ≤ 1.15 → 继续；κ 偏大 → 用实测 κ 重算净收益，净收益（full-pool）< +15% 则回到设计台重估（如 device-to-device 分段拷贝、错峰粒度加细）。

### E1 真机 capacity bottleneck（动机）

- 两条 baseline：vanilla vLLM-realtime 路径（0.23，文本分支）+ 我们 worker 的 conveyor off；3090，N ∈ {4,6,8,12,16}（full-pool），每点新起进程，600s。
- 记录：分桶 p50/p99、KV 池占用轨迹、SM util、t_wall。
- 附加臂：开注入负载 → 饱和提前多少（首次真机量化）。
- 预期图：池占用单调爬升至 1.0 → 系统卡死，同时 SM util 低，即 C1 的真机版本（FINDINGS A3 的三种失效形态给出判读口径）。

### E2 主结果：KV conveyor 容量收益（C3）

- 同一 worker，conveyor on vs off；两个池配置 × 双指标（t_wall 比、N* 曲线）；prefetch lead time τ_lead 取保守值 50ms，resident window X 按公式最优 X* 配置。
- 对照组：vanilla vLLM-realtime 路径（参照 baseline）、windowed KV 回收（有损竞争，容量应与 conveyor 相近，差异化在 E5）。
- 判据：t_wall 比与 N* 提升同时落在预测带 min((M+P)/M, 算力倍数) 的 ±15% 内。链路侧上界取决策 D3 表（full-pool 1.23×、capped-pool 1.83×）；算力倍数 = compute 预算允许的会话数倍数（FINDINGS D4 在本卡给约 2×，链路侧理论 4.9× 因 compute 不可达）。
- 主结果点 5 次乱序重复，报中位数 + IQR。
- 对账检验：每个配置报出 (M, P, 算力倍数) 三元组，T=480ms 与 T=2s 的收益由这组三元组统一到同一 min() 口径后比较，而非由任一侧的单独预测下结论。

### E3 编排消融：相位指派的收益（C4）

- 三臂：全常驻 / conveyor + 随机相位 / conveyor + 指派相位。
- 测量：实达链路利用率 η（链路利用且不 miss 的上确界）、链路队列 p99、miss rate、净容量。
- 附加扫描：τ_lead ∈ {10..120ms} → staging 峰值 vs miss 的权衡曲线；相位指派应允许更小的 τ_lead。
- 预期：随机相位被迫 η 下降或 miss rate 上升，相位指派恢复到 η ≈ 0.7–0.9。这张图是编排贡献的核心证据。

### E4 注入 + commit / cancel 语义（C5）

- 注入路径：gateway 新事件 → `SessionInput.text` → worker。
- 臂 (a) baseline：注入按 vLLM 现状以不分片 prefill (one-shot/unchunked prefill) 进引擎 step，对照面是 chunked prefill（Sarathi-Serve）。
- 臂 (b)：注入走 conveyor 第二优先级，uncommitted 内容停在 host DRAM、cancel 即丢（借用 two-phase commit 的形状）。
- 测量：注入期间的 tick miss 按注入相位分桶（检验伤害是否由相位决定）、stale resident KV 的字节轨迹（目标降到约 0）、陈旧拼接 (stale context splice) 事件数、注入完成 latency（弹性代价要诚实报告）。
- 可选臂：open-system 爬坡 + AIMD admission 叠加，证明与 admission 一类外围机制可复合。

### E5 无损性：长视野召回（C6，对 windowed KV 的决定性对照）

- 移植 `third_party/metronome/experiments/fd_longhorizon_probe.py` 的模式到文本负载：会话早期注入含关键事实的工具结果（或前 30s 对话内容），在 3–8 分钟后用探针提问。
- 三臂：无界（正确但会饱和）/ sliding window W=30s（窗外必错）/ conveyor（正确且不饱和）。
- 预期表：正确率 conveyor ≈ 无界 ≫ sliding window（窗外 ≈ 0）；同时 conveyor 的池占用有界，「无损 + 有界」同框。

### E6 泛化与外推（C7）：公式地形 + 实测锚点

解析公式直接绘制地形，多锚点验证。六个公式各有实测锚点：

1. P/M = η·B_link·T/M_bytes（E0 锚定 η 与 B_link）。
2. 池满时 step time = 0.9×显存/带宽的不变量，V/BW 跨五代恒为 24–36ms（FINDINGS D1）。
3. busy(ctx) 斜率：busy 是总 resident 字节的函数而非会话数的函数（FINDINGS D2）。
4. compute-bound 拐点 B*（roofline ridge point）≈ 字节每参数 × TFLOPS/(2BW)，3090 约 40–80（FINDINGS D1）。
5. 相位打散守恒律：用算力余量换常驻容量，上界 T·BW/(配额×W)（FINDINGS D3）。
6. 收益 = min((M+P)/M, 算力倍数)（FINDINGS D4）。

扫描轴：T ∈ {80ms..2s} × B_link ∈ {PCIe3 / PCIe4 / PCIe5, C2C 900GB/s} × 模型档位 → 等高线由公式绘制。

T 轴四点均有真实系统锚定：80ms = Moshi / PersonaPlex（音频原生 12.5Hz）；480ms = DuplexOmni（文本–文本切片，决策 D2 主结果定义）；~1s = MiniCPM-o；2s = Qwen-Omni（音频 encoder 2s 块 + TMRoPE 每 2s 时间交织，arXiv:2503.20215）。

适用域声明：80ms 音频原生端没有会话 churn 窗口，这是不值得做该区的架构学原因；conveyor 是文本–文本切片家族（480ms–2s）的设计，恰为可做注入 / tool call 的那一支。
本卡上 T=480ms 与 T=2s 的实际收益被 compute 封顶压到接近，T 的差别要在算力倍数更高的卡上才显形；两个 T 的收益口径由 E2 的 (M, P, 算力倍数) 三元组统一。

硬件锚点：本机 PCIe 实测 12.30 GB/s（Gen3 档，`calibration/data/pcie_h2d_bench.json` 的标定曲线同档记 12.33 GB/s）；Metronome Blackwell + 30B-A3B 的发表数字（step time 4.8–14ms、饱和时刻 t_sat 模型）；H200 / GB300 规格注记点。

预期形状是 U 形收益地形：memory-bound 消费端与片间互联旗舰端高，PCIe + 胖显存中段低。
公式组可被审稿人直接复算。

呈现形态（方法论榜样：FasterMoE / PPoPP'22 的 DDL-Roofline 范式）：定制 Deadline-Capacity Roofline，横轴每会话 context length，纵轴可承载 N*，三条屋顶（算力 / HBM 容量 / conveyor 抬升后容量），E1 实测轨迹为运动点；论文 Figure-1 候选。
里程碑 M2（§七）的调度决策（平均 batch size B̄、τ_lead）从该模型推导。

## 五、方法论规范（全实验强制）

1. 每点新起进程（fresh-per-point）：每个数据点新起 worker 进程。
2. 共享 GPU 空闲检测：每次测量前跑 `harness/wait_quiet.sh` + `gpu_probe.wait_for_window`；测量期间的 `nvidia-smi` 采样存档，事后剔除受污染窗口。
3. 重复与乱序：主结果点 ≥5 次、条件乱序（`run_variance_rand.sh` 模式），报告中位数 + IQR，不报单次。
4. 双重 miss 判据：worker 自报 step time 与客户端节奏完整度（交付率 deliv_pct ≥ 0.9）交叉验证。
5. 工件纪律：每个数字可追溯到 `results/paper/` 下的原始 JSON + 生成脚本 + git 版本 + 环境记录。

## 六、效度威胁与预答复

| 威胁 | 预答复 |
|---|---|
| 文本代理非真音频 | KV 物理与模态无关；E6 交叉核对 Metronome 的真音频定义；limitations 明示 |
| 自研 worker vs vLLM 不公平 | 主对比在同一 worker 内 on / off；vLLM 作参照 baseline；绝对 step time 与 vLLM 对齐并报告 |
| 1.7B 太小 | P/M 公式与模型无关（每 token 字节数 b 被约掉）；E6 给 7B / 30B 定义的外推；边界在 limitations 声明 |
| 3090 非数据中心卡 | full-pool P/M 与 H100+PCIe5 同量级是特性不是缺陷；若可临时租 H100 / PCIe5，加一个主结果复测点（可选，非阻塞） |
| 共享 GPU 噪声 | 方法论规范第 2、3 条；关键结论附重复分布 |

## 七、执行顺序与风险门

1. M0：E0 微基准（先行，是继续 / 停手的门槛）+ gateway 构建 + 占位 worker 打通客户端→gateway→gRPC 管线（零 GPU）。
2. M1：vanilla vLLM-realtime 路径文本分支跑通 → E1。
3. M2：conveyor worker v1（固定时刻表，无相位指派）→ E2。
4. M3：相位指派 + τ_lead 扫描（E3）→ 注入 / cancellation（E4）→ 召回探针（E5）。
5. M4：E6 公式地形 + 锚点核对；变异批次补测；工件打包。

里程碑推进时，结论条目进 `docs/findings.md`，设计变更就地改本文，两边共用同一套实验编号。
