# KV conveyor 设计

## 动机

全双工 serving 在真机上是 capacity-bound（因 KV 池装不下而失败，区别于 bandwidth-bound 意义上的 memory-bound）：池打满即多数会话 starve，而同一时刻 GPU 约有一半时间空闲（FINDINGS H1、D1）。
tick 内的 H2D 链路同样大量闲置，本设计的全部内容就是用这两份闲置资源赎回 HBM 容量。
KV conveyor：按 tick 时间表把每路会话的尾部 KV 母本 (authoritative host copy) 从 host DRAM 经 DMA 预取入 HBM 暂存、算完即释放（scheduled tail-KV offloading，谱系为 FlexGen / InfiniGen / vLLM offloading connector / LMCache），等效 KV 容量 = resident M + staging P。

## 方案演化

### v1（否证）：阈值转正 + 重算

尾部不 resident，每 tick decode 前重新 prefill 尾部、用完即弃，攒满阈值 C 才转 resident。
否证是重算次数的算术：每个 token 在 commit 前被重算约 C/(2a) 次（a≈10 token/tick，C=2048 时约 100 次），代价按 tick 重复支付。
合并两类瓶颈 N = min(N_comp(C), N_mem(C))，对任意 C 都不优于 baseline：C 小省不下显存，C 大算力先塌。
本质是拿每 tick 重复消耗的引擎步时间去换一次性的字节存量，而引擎步是 tick 内最稀缺的资源：稳态纯 decode 实测 21.0ms/step（batch=8，FINDINGS H1），一个 2s tick 只放得下几十步。

### v2（现行）：阈值转正 + 按时间表的 H2D

机制从「重算」换成「搬运」，换掉的是链路而非算力：走 copy engine、与计算并行、不污染 batch 组成。
成本基础是同一段 4k token 的两条恢复路径，重算需 330ms prefill（早期标定实测），pinned H2D 只要 38.1ms（`calibration/data/pcie_h2d_bench.json`）。

## 设计规格

母本住 host DRAM，是唯一权威副本；HBM 里的 staging 是它的一份短命拷贝，该会话本 tick 算完即释放指针。
尾部累计到阈值 C 就转正 (promote) 为 resident，于是每 tick 的搬运量有界，长会话不会把链路吃穿。
注入 (injection) 结果先以 uncommitted 态停在 DRAM，确认说出后才 commit；cancellation 就是丢掉 DRAM 里那一份，既不产生 stale resident KV，也没有 eviction 决策要做。
这借用 two-phase commit 的形状，不是 two-phase commit：没有跨节点投票，母本始终只有一个 owner。
本 tick 每路新生的 a 个 token 在后台追加进母本（全场约 100MB/s 出向，可忽略）。
与静默停泊 (idle-session offload) 复合：停泊省整路（只适用于静默会话，占比假设约 30%，无实测来源），尾部搬运省尾部（适用全部会话），两者消费同一份链路预算。
与 KV 量化复合：fp8/int4 使 M 与 P 同乘 2–4，绝对路数翻倍，收益比不变。

| 符号 | 含义 | 取值与出处 |
|---|---|---|
| L | 单会话上下文长度（token） | 16k @10min（26.7 tok/s：音频 25 tok/s + 文本输出）；L 不影响收益比例 |
| b | 每 token 的 KV 字节 | 56 KiB（Qwen2.5-Omni-7B thinker：2×28 层×4 KV 头×128×2B）；1.7B 实测 112KiB 反而更大（其 GQA KV 头 8，为 7B 的两倍） |
| M | resident KV 池容量（token；M_bytes 为同一量的字节形式） | 本机实测 74.3k token = 3.97GiB（FINDINGS D2、D5）；H100 级示例 55GB/b ≈ 959k |
| P | 一 tick 可搬入的 token 量 = η·B_link·T/b | H100 级示例 234k |
| X | 每路非常驻的尾部长度，均值 X = C/2 | 由 C 决定 |
| X* | 使可调度并发数最大的 X | 示例 ≈3.1k token（约 170MiB/路） |
| C | 转正阈值 | C ≈ 2X*（示例 6–8k） |
| a | 每路每 tick 新生 token 数 | ≈10（480ms tick）；本机 2s tick 实测约 78（53 音频 + 约 25 生成） |
| η | H2D 预算系数：设计允许占用的链路带宽比例 | 工程假设 0.7（余量留给注入 / 停泊 / 抖动）；E0 实测计算期链路可用率约 0.94；实达值由 E3 测 |
| B_link | H2D 可用带宽 | 本机实测 12.30–12.33GB/s（E0 复测与 `calibration/data/pcie_h2d_bench.json`，Gen3 档）；示例 PCIe5 约 40GB/s |
| T | tick 长（硬 tick） | 本机 E 系列 2s；示例 480ms |
| N / N* | 并发路数 / 可调度并发数 (schedulable concurrency，判据 deadline miss rate ≤ 1%) | 见收益表 |
| τ_lead | prefetch lead time | 40–60ms |
| t_x | 单路一 tick 的 H2D 搬运时间 | 示例 6.4ms |
| t_c | 单路一 tick 的计算时间 | 示例 10–30ms |

## 公式与收益

```
显存约束:  N·(L − X) ≤ M        带宽约束:  N·X ≤ P
最优:      X* = L·P/(M+P)       N* = (M+P)/L
收益比:    P/M = η·B_link·T/M_bytes    ← 模型参数 b 被约掉，纯硬件比值
```

语义：等效 KV 容量 = M + P。一个 token 的 KV 要么占一个 resident 位（花 M），要么每 tick 花一份 staging 预算（花 P），在 tick 尺度上两种住法等价。
实际收益 = min((M+P)/M, 算力倍数)（FINDINGS D4）：链路给一条容量上界，算力给另一条，取小者。

| 平台 × tick 长 | 公式上界 | 实际口径 |
|---|---|---|
| 本机 3090 × 2s（池约 4.0GiB） | (M+P)/M = 4.9× | N=15–16（2×），封顶在 compute 而非链路，PCIe 利用率约 26%；4.9× 需 N≈39、4.7s compute 预算，本卡给不出（D4 真机预测） |
| H100 级 + PCIe5 × 480ms | P/M = +24% | 扣 staging 后净约 +20%（公式外推） |
| GH200 C2C × 480ms | P/M = +260% | 超时先于容量成为瓶颈，收益封顶（公式外推） |
| 任意卡 × 80ms tick | P/M 缩为 1/6 | 不值得做 |

两种写法是同一式：(M+P)/M = 1 + P/M。
代入 H100 级示例配置（PCIe5 / 480ms / L=16k）：X*≈3.1k token（约 170MiB/路），C≈6–8k，t_x=6.4ms，t_c=10–30ms，staging 峰值 N·X·(t_x+t_c+τ_lead)/T ≈ 1.7GiB（占池 3%，已计入净收益）。

## 编排

η 不是硬件给的，是调度挣的：随机相位下需求聚簇造成链路瞬时尖峰，要么 H2D 迟到，要么被迫压低 η（收益缩水）。设计目标是把 H2D 需求摊平成近恒定速率。

- 相位指派 (phase-offset assignment)：准入时把新会话插进最空的相位位置，同时摊平计算 batch 到达与 DMA 到达两条需求曲线。连续旋转优于离散槽：相位差取 T/N 均匀铺开，每 T/N 一路进、一路出，链路负载近恒定且余量数倍；离散分 G 组则是 G 倍峰值的脉冲（数字见 FINDINGS D3）。
- 非重叠忙碌窗 (time-multiplexed residency) 是容量扩展的必要条件：同步 tick 下 conveyor 无收益，因为忙碌窗内每个 step 都读全员 KV，峰值 resident 不降（D3）。相位打散 (phase desynchronization) 用算力余量换常驻容量，代价是权重每 step 重读；守恒律与上界见 FINDINGS D3。
- 按时间表的 H2D：每路每 tick 一个搬运作业，release time = 内容冻结点（上 tick 计算完，帧边界后尾部不再变），deadline = 本 tick 计算槽 − τ_lead。τ_lead 取 40–60ms 覆盖链路排队 p99，对 6.4ms 的服务时间是约 10× 余量。链路侧用 EDF (Earliest Deadline First) + 令牌桶；周期、相位、大小三者先验已知，因此是周期任务集，可调度性可静态验证（Liu-Layland 式判据直接写得出）。
- 关键张力：显存收益随预取时刻推迟而增大，提前整 tick 等于零收益，零提前等于零容错。相位指派把排队近似确定化，允许把 τ_lead 压到收益折损 ≤15% 的位置。
- 链路三级混合关键性：尾部 H2D（硬 tick，inelastic）> 注入 KV 搬运（弹性注入，delay-tolerant）> 静默停泊（后台）。η 留出的 30% 就是后两类与抖动的预算。链路调度与计算侧的注入安放 (injection placement) 同构，一套 deadline-aware 语义在两种资源上各证一次。

## 宿主

conveyor 要逐步操纵 block table，并在独立 CUDA copy stream 上按 tick 预取、算完即释放 staging block。
宿主是自研 paged-KV worker：以 `third_party/metronome/metronome/engine.py`（FlashAttention paged-KV 多租户 decode 循环）为底子 fork 进本仓库 `harness/`，实现同一 gRPC 协议、挂在同一 gateway 之后；vLLM 内核与第三方 pin 保持只读。
公平性设计：主对比在同一 worker 内做 conveyor on vs off，唯一差异是 KV 住哪；vanilla vLLM realtime 路径作参照 baseline，证明自研 worker 的绝对性能不虚；windowed KV 作有损竞争方案对照。

## 相关工作

| 工作 | 对「KV 装不下」的答案 | 差异点 |
|---|---|---|
| Metronome'26 | 砍：W=1024 sliding window + sink（架构失忆搬到 serving 层：模型侧靠定长窗口自限的失忆策略，被原样搬进 serving 做容量控制） | 有损，窗外内容不可恢复，且与注入驻留冲突（几千 token 的结果没说完就滚出窗）；本设计无损保全上下文 |
| LiveServe'26 | 轮级 offload + 语义预取（预测下次使用） | 依赖 turn-based 的轮间空隙；双工无空隙，且回归时刻无需预测（下 tick = 上 tick + T 精确已知）。本设计把 offload 推进到帧粒度、全体会话 |
| vLLM resumable request / SGLang streaming sessions | resident 机制，无策略 | 提供机制而不提供「谁 resident、谁流动」的决策，本设计即该决策 |
| Kyutai 槽位环形 / Qwen Realtime drop-oldest（480–600s） | 架构级与 API 级失忆 | 有损；产品层证明市场在朝长记忆推 |
| MoshiRAG（ICML'26） | 模型层回避：弃插入式注入 (token-insertion) 改加法叠加，"to constrain sequence length" | 模型侧为 serving 缺位买单的直接证据；本设计的 commit 语义正面接住插入式注入 |
| 通用 KV offload（LMCache 等） | 跨请求缓存与卸载 | 面向 ephemeral 请求与轮间隙，没有周期性硬 tick deadline 的概念 |

价值论证三条：
1. 无损扩容是直接可售商品，语音平台按「线」计价（$8–10/线/月）。
2. 可行性建立在双工负载的三个独有性质上：周期精确已知、相位可指派、内容按帧冻结。通用 serving 不具备这三条，所以这是该负载形态的原生机制而非技巧移植。现有系统均未覆盖两列能力：按硬 tick deadline 的 KV 搬运调度，以及注入的 commit/cancel 语义。
3. 它把 deadline-aware 调度从引擎步扩展到 DMA 队列，与注入安放构成同一个混合关键性问题的双资源实例。

## 边界与未决

可证伪面是四条：搬运与计算可并行、相位摊平确有收益、扩容对内容无损、cancel 之后不留 stale resident KV。

- 并行性已实测：E0 二十格网格上 κ（decode step 减速系数 slowdown factor，κ = t_with/t_without）最大 1.067，大格 1.01–1.03，干扰按每 step 加性约 2.5ms 建模而非乘性折损（FINDINGS K3）。DMA 与 decode 重叠这一物理前提在本机成立。
- η=0.7 是保守的工程假设，实测计算期链路可用率约 0.94；真实值由搬运时间表的调度质量决定，E3 三臂（全常驻 / 随机相位 / 指派相位）测的就是它。
- 待测一，E2 收益带：固定 N 测 t_wall 比是否落在 (M+P)/M 的 ±15% 内，并给出 N* 全曲线而非单点。
- 待测二，注入臂：对照不分片 prefill (one-shot/unchunked prefill，对照 chunked prefill / Sarathi-Serve) 直接进引擎步与走链路第二优先级两种安放，测已作废但仍常驻的 KV 字节轨迹、陈旧拼接 (stale context splice) 次数、注入完成延迟。
- 待测三，480ms 与 2s 的收益口径对账：本卡两个 tick 长的实际收益都被算力封顶在约 2×，公式上 4 倍的 P/M 差异不显形，需要同卡双 tick 长实测或更高算力倍数的卡把两条上界拆开。
- 收益正比于 tick 长，80ms tick 不值得做，适用工作点是 200ms–2s tick 的 thinker 家族。
- 不解寿命瓶颈：L 增长时收益比不变，绝对 N 照样滑坡，须与静默停泊、KV 量化、已作废 KV 回收组合。
- 工程摩擦：staging block 的生命周期要与 shape specialization 下的 CUDA graph capture 边界对齐，vLLM 的 offloading connector 是现成的形状参考。
