# 带宽换显存：尾部 KV 传送带（方案记录，2026-08-01）

> 文中早期模拟器试跑数字（如 KV 可行密度 N=12）的原始数据已随仓库清理删除；对应主张现由 E1 真机证据支撑（含触及容量上限时余量的公式关系、三种失效形态的机制分析），见 `PAPER-EXPERIMENTS.md`。

从问题定义到方案定稿的完整记录，含被否掉的中间版本与相关工作对比。配套：`PROBLEM.md`（问题定位）、`STORY.md` §5–6（瓶颈顺序与相关工作矩阵）。**本方案尚未真机验证。**

**方案名**：尾部 KV 传送带（KV conveyor）。下文用机制术语描述，不再重复产品名。

## 一、问题定义

**双工语音 serving 是 capacity-bound：GPU 因 KV cache 装不下而失败时，大部分时间在空转。**证据链：

1. **本仓库实测**（RTX 3090 / 1.7B）：KV cache 可行密度 N=12，而超时瓶颈要到 N=192/208 才触发（判据：超时比例 miss>1%）——显存先成为瓶颈，大约早一个数量级（早期证据，现由 E1 真机支撑）；单会话占空比仅 4–9%。
2. **Metronome 独立实测**（[arXiv:2607.02640](https://arxiv.org/pdf/2607.02640)，Qwen3-Omni-30B FP8 / 96G Blackwell）：vanilla vLLM-realtime（resident KV）在 N=128 于约 148 秒触及 memory cliff——每帧延迟从 2–5ms 一步钉死在 1.6s，全部会话僵死；崩溃时刻 GPU 时间占用仅约 13–32%（由其每帧延迟与 phase offset 设置推得）。原文："memory kills sessions whose compute the GPU could easily carry"。
3. **结构原因**：双工会话的 KV 每 tick（固定时长的一轮，如 480ms）必被 attend，没有 turn 间隙可换出再重算（重算 4k token = 330ms prefill = 自我注入，本仓库实测）；每 tick 只碰每路状态几次，时间占用上限 ≈ 每 tick 触碰次数 × (容量/带宽) / tick 长 ≈ 20%（H100、480ms tick）——**卡是先装不下，远没跑满**。

因此的机会：**HBM 容量是稀缺资源，而 tick 内的 H2D 带宽和计算时间都大量闲置——能否用闲置资源赎回容量？**

## 二、方案演化（含被否版本，保留否证过程）

### v1（已否）：阈值 commit + 重算

尾部不 resident；每 tick decode 前重新 prefill 尾部、用完即弃；攒满阈值 C 才转 resident。

**否证**：重算代价按 tick 重复支付——每 token 在 commit 前被重算约 C/(2a) 次（a≈10 token/tick，C=2048 时约 100 次）。合并两类瓶颈：N = min(N_comp(C), N_mem(C))，对任意 C 都 ≤ baseline（C 小省不了显存，C 大算力瓶颈先塌；7B/H100 代入：C=512 时 N 从约 60 **跌到**约 26）。本质：用**每 tick 重复消耗的引擎步时间**（最稀缺的 tick 内资源）去换**一次性的字节存量**，成本差约三个数量级；且每次重算都要付约 13ms 固定开销（STORY §2：CUDA graph 因掺入 prefill 而退出的固定代价），等于把"重算=自我注入"制度化。

### v2（定稿）：阈值 commit + 按时间表的 H2D

尾部 KV 的**canonical copy 住主机 DRAM**；每 tick 按时间表用 DMA 搬入 HBM 作 staging，该会话算完即释放；攒满 C 才 commit 为 resident。机制从"重算"换成"搬运"：单价从约 0.035ms/token 引擎步时间降到约 2µs/token DMA 时间，且走 copy engine、与计算并行、不污染 batch 组成。

## 三、方案细节

### 3.1 符号与假设

| 符号 | 含义 | 基准取值（出处） |
|---|---|---|
| L | 单会话上下文（token） | 16k @10min（26.7 tok/s：Qwen2.5-Omni 音频 25 tok/s + 文本输出；按 Qwen3-Omni 13 tok/s 则 11.4k——**L 不影响收益比例**） |
| b | 每 token KV 字节 | 56 KiB（Qwen2.5-Omni-7B thinker config：2×28 层×4 KV 头×128×2B。本仓库 1.7B 实测 112 KB 反而更大——其 KV 头数 8 是 7B 的两倍，GQA 配置差异，非笔误） |
| M | KV 池容量（token） | 55GB/b ≈ 959k（H100 80G − 权重约 22GB − 开销） |
| B_link, η | H2D 可用带宽及可用率 | PCIe5 实效约 40GB/s，η=0.7 → 28GB/s |
| T | tick 长 | 480ms |
| P | **一 tick 可搬入 token 量** = η·B_link·T/b | 234k |
| C | commit 阈值；尾部均值 X = C/2 | C ≈ 2X\*（下） |
| N | 并发路数 | — |

### 3.2 可用公式直接算的关系

```
显存约束:  N·(L − X) ≤ M        带宽约束:  N·X ≤ P
最优:      X* = L·P/(M+P)       N* = (M+P)/L
收益比:    N*/N₀ − 1 = P/M = η·B_link·T / M_bytes   ← 模型参数 b 被约掉，纯硬件比值
```

**语义：等效 KV 容量 = M + P——一个 token 的 KV 要么占一个 resident 位（花 M），要么每 tick 花一份 H2D 配额（花 P），在 tick 尺度上两种住法等价。**

| 平台 × tick 长 | 收益比 P/M | N（L=16k，扣 staging 后净值） |
|---|---|---|
| H100+PCIe4，480ms | +10% | 60→66 |
| **H100+PCIe5，480ms** | **+24%（净约 20%）** | **60→约 72** |
| 本仓库 3090+PCIe3（实测 12.33GB/s，`calibration/data/pcie_h2d_bench.json`），480ms | **+83%**（池仅 4.97GB，相对带宽富裕） | 原型验证信噪比最高 |
| GH200 C2C，480ms | +260%（超时瓶颈先到，封顶） | — |
| 任意卡，80ms tick | ÷6（不值得做） | — |
| 任意卡，2s tick（Metronome 口径） | 约 +100% | — |

代入示例（PCIe5/480ms/L=16k）：X\*≈3.1k token（180MB/路），C≈6–8k，单路 H2D 6.4ms，单路计算 10–30ms。

### 3.3 编排设计（方案的贡献主体）

核心认识：**η 不是硬件给的，是调度挣的**——随机 phase 的需求聚簇造成链路瞬时尖峰，要么 H2D 迟到（miss）要么被迫压低 η（收益缩水）。设计目标 = 把 H2D 需求摊平成近恒定速率。四个对象：

1. **Phase assignment（准入时）**：phase offset 从"刻意的实验设置"（Metronome 如此）升级为**调度资源**——准入把新会话插进最空的 phase 槽（TDMA：按时间表错开各路占用），同时摊平计算 batch 到达与 DMA 到达两条需求曲线。
2. **按时间表的 H2D**：每路每 tick 一个搬运作业。释放 = 上 tick 计算完（**内容冻结点**：帧边界后尾部不再变）；deadline = 本 tick 计算槽 − τ_lead（约 40–60ms，覆盖链路排队 p99；对 6.4ms 的服务时间是约 10× 余量）。链路 EDF（Earliest Deadline First）+ 令牌桶。周期 / phase / 大小全部先验已知 ⇒ **周期任务集，可静态验证可调度性**（Liu-Layland 式判据可直接写出）。
3. **Staging 与 commit**：算完即释放 staging 指针（DRAM 有 canonical copy）；本 tick 新生约 11 token/路 后台写回（全场约 100MB/s 出向，可忽略）；staging 峰值 N·X·(t_x+t_c+τ_lead)/T ≈ 1.8GB（占池 3%，已计入净收益）。**关键张力**：显存收益 ∝ 预取多晚——提前整 tick=零收益，零提前=零容错；TDMA 把排队近似确定化，允许把 τ_lead 压到收益折损 ≤15%。
4. **链路三级混合关键性**：尾部 H2D（硬周期）> 注入 KV 搬运（弹性）> 静默停泊（后台）。η 留的 30% 即后两类与抖动的预算——**链路调度与计算侧的注入安放同构，一套 deadline-aware 语义在两种资源上各证一次。**

### 3.4 与其他机制的复合

- **Commit 语义 × 作废**：注入结果以 uncommitted 态停在 DRAM，确认说出后才 commit——40% 被打断的注入从未进 resident 池，作废 = DRAM 直接丢（早期证据中 24.2% 已作废但仍 resident 的缓存占用从源头消灭）。
- **× 静默停泊**：停泊省整路（仅适用约 30% 静默会话），尾部 H2D 省尾部（适用全部）——同一链路预算的互补消费者。
- **× KV 量化**：fp8/int4 使 M、P 同乘 2–4，绝对路数翻倍，收益比不变。

## 四、相关工作对比：为什么这块是空的、为什么有价值

| 工作 | 对"KV 装不下"的答案 | 局限（本方案的差异点） |
|---|---|---|
| **Metronome'26** | 砍：W=1024 sliding window + sink（架构失忆搬到 serving 层） | **有损**（窗外内容不可恢复，与注入驻留冲突——几千 token 结果没说完就滚出窗）；本方案**无损**保全上下文 |
| **LiveServe'26** | 轮级 offload + 语义预取（预测下次使用） | 依赖 turn-based 的**轮间空隙**；双工无空隙、回归时刻无需预测（下 tick=上 tick+T 精确已知）——本方案把 offload 推进到**帧粒度、全体会话** |
| **vLLM resumable / SGLang streaming sessions** | resident 机制，无策略（"bounds nothing"，Metronome 语） | 提供机制不提供"谁 resident 谁流动"的决策——本方案即该决策 |
| **Kyutai 槽位环形 / Qwen Realtime drop-oldest（480–600s）** | 架构级/API 级失忆 | 有损；产品层证明市场在朝长记忆推 |
| **MoshiRAG（ICML'26）** | 模型层回避：弃 insertive 注入（精度更好）改加法叠加，"to constrain sequence length" | **模型侧为 serving 缺位买单的直接证据**；本方案的 commit 语义正面接住 insertive 注入 |
| 通用 KV offload（KServe/LMCache 等） | 跨请求缓存/卸载 | 面向 ephemeral 请求与轮间隙；无周期硬 deadline 概念 |

**价值论证**：(1) 无损 +20–24%（PCIe5/480ms）的密度是直接可售商品（语音平台按"线"计价，$8–10/线/月）；(2) 可行性建立在双工负载三个**独有**性质上——周期精确已知、phase 可指派、内容按帧冻结——通用 serving 不具备，故这是该负载形态的原生机制而非技巧移植，现有工作无人利用；(3) 它把 deadline-aware 调度从引擎步扩展到 DMA 队列，与本工作的注入安放构成同一混合关键性问题的双资源实例——机制上独立成块，叙事上强化主线。

## 五、验证计划

1. **模拟器扩展**：加链路资源 + H2D 调度器（标定现成：pinned H2D 12.33GB/s、4k swap 38.1ms、多尺寸 64MB–1GB 平坦——`calibration/data/pcie_h2d_bench.json`，2026-08 GPU3 实测）。
2. **三条对照隔离"摊平的价值"**：全 resident baseline / 随机 phase 的 H2D（η 被迫低）/ 指派 phase 的 H2D（η≈0.7–0.9）。
3. **唯一需要的真机微基准**：DMA 与 decode 步重叠时的干扰系数（copy engine 是否偷计算核带宽）——现有标定推不出的唯一参数。
4. 3090 上原型（收益比 +83%，信噪比最高），H100/PCIe5 外推。

## 六、诚实边界

- 收益 ∝ tick 长：80ms tick 不值得做（+4%）；本方案的适用工作点区间是 200ms–2s tick 的 thinker 家族。
- 不解寿命瓶颈：L 增长时收益比不变但绝对 N 照样滑坡——需与停泊/压缩/已作废缓存回收组合。
- η=0.7 是工程假设，真实值取决于 H2D 调度质量——恰是实验要测的东西。
- 干扰系数未标定（验证计划第 3 条）；与 paged KV / CUDA graph 的工程摩擦未评估（vLLM 的 HBM–DRAM offload connector 是现成起点）。
