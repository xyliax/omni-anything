# 问题定义

## 一句话

双工语音 serving 是 **capacity-bound**：容量先于算力耗尽，与 bandwidth-bound 意义上的 memory-bound 是两回事。
KV cache 每 tick 都必须参与 attention，常驻显存只增不减，request 之间也没有空隙把历史换出。
于是计算远未饱和时 KV pool 就已饱和崩溃（本仓 E1 在 RTX 3090 上实测此顺序，FINDINGS A3；Metronome 真机同构，paper 原话 "memory kills sessions whose compute the GPU could easily carry"）——容量是稀缺资源，而每一 tick 内的 H2D 带宽和计算时间大量闲置。

方向性回答：**用闲置的数据搬运带宽换更大的并发容量**，即按 tick 时间表调度的 **KV conveyor**（scheduled tail-KV offloading）。
收益是纯硬件比值：3090 + 7B 预测 N=15–16（2×，封顶在 compute 而非链路，FINDINGS D4）；H100 + PCIe 5 / 480 ms tick 上净增约 20%（公式推演的线性外推）。
方案的真机判据是 E2 的稳态容量与 E3 的相位三臂。

## 负载的三要素

| 要素 | 内容 | 去掉它变成什么 |
|---|---|---|
| ① 硬 tick | 固定周期 T 的硬 deadline 帧（Metronome 的 frame budget B）：每 480 ms 一次约 8 token 的增量 prefill 加 2–4 步 decode；deadline miss = 音频断裂 = 正确性事故 | 普通对话 serving（Sarathi / Niyama 已解决） |
| ② 弹性注入 | 后台 agent 的 tool 结果，数百到数千 token，约 10% 落在 4–8k 长尾；40% 概率被用户打断而作废。delay-tolerant，对照 inelastic 的硬 tick 前台 | 纯双工锁步（moshi-server / Metronome 已解决） |
| ③ 单卡多路 | concurrent session 数 N 是目标函数（受成本约束），不是外部给定 | 单会话工程问题 |

要素 ① 每 tick 取 8 token（Qwen3-Omni 的 `position_id_per_seconds: 13` 折算为约 6 token/片，本工作取谱系中位 12.5–25 tok/s 的偏高值）；要素 ② 的长度分布与 40% cancellation 概率同为冻结先验，E4 按此实测注入与作废。
前台模型谱系按 tick 结构分三类：Moshi 系 80 ms 锁步帧（输入并入自回归步，无独立 prefill）；SyncLLM 系 160–240 ms 时间分块；Qwen-Omni / Freeze-Omni 系 thinker 架构 480 ms 切片（音频编码器分块输入 = 增量 prefill，主干出文本，轻量语音头合成）。
本工作对标第三类：论文主配置 tick = 480 ms（与 DuplexOmni §3.1.2 的固定时间片逐字一致，FINDINGS E4），E1 真机栈 tick = 2 s。
三要素同时出现在产品层：GPT-Live（OpenAI，2026-07）把 invoke a tool 做成 tick 内决策、复杂问题委托后台 frontier 模型再把结果送回对话；Seeduplex（字节，2026-04，豆包全量）同为 ①+②+③。两家服务侧均闭源。

## 四个实测事实

**事实 1 · 显存先于算力成为瓶颈。** E1 真机（vLLM 0.23 + Qwen2.5-Omni-7B + RTX 3090，tick 2 s，N=8）下 KV pool 饱和有三种失效形态：`full_sequence_must_fit` 的 re-admission 条件加 FCFS `break` 造成 head-of-line blocking 全员死锁、preemption cascade、同步填充下的 admission deadlock（FINDINGS A3）。
被抢占的 session 永不复活：re-admission 要求整段序列装得下，而 starve 后前端仍持续追加 context（9.4k→24.9k token），空闲从未超过约 12%，复活次数为零（FINDINGS A5）。
capacity-bound 时算力恒有约一半空闲：busy/T ≈ 38–55%，对模型、tick 长、显卡代际三重不变（FINDINGS D1）。
Metronome 真机交叉验证同一顺序：vanilla 触达 memory cliff 时计算远未饱和。
历史量化形态（早期模拟器标定，方向已由 E1 独立确证）：KV 侧的可调度并发数 N*（schedulable concurrency，判据 miss rate ≤ 1%）= 12，远小于 deadline 侧的 N* = 192 / 208（随机相位 / 相位对齐）；每会话子 tick 占用比例 4–9%。
E1 另暴露一类 host-dependent 的 ingest 饱和（multimodal input processing 单线程，能撑住的路数 N_ingest = tick / t_chunk，本机 7.5 路，FINDINGS A1），一个语句移入线程池即修复（frame-to-process 排队 1015 ms → 3 ms，FINDINGS A2）——那是工程债，不是本问题的结构瓶颈。

**事实 2 · 相位从没被当成可调度资源。** 早期模拟器标定：随机相位比相位对齐多花 **4.96 倍** GPU 时间，其中到达碰巧凑 batch 产生的额外开销占全卡忙时 **64.7%**。
batch size 由会话到达的巧合决定，调度器没有话语权（引擎 work-conserving：有活就干、从不等待）。
真机侧的相位打散 (desync) 守恒律已定：平均 batch 大小 B̄ ≥ N×配额×t_step/T ≈ 2.8，上界 T·BW/(配额×W) ≈ 3.4（3090 + 7B）；相位差 T/N 的连续旋转优于离散槽；同步 tick 下 conveyor 无收益，时间排他性是 capacity 扩展的必要条件（FINDINGS D3）。
E3 的三臂（全常驻 / conveyor + 随机相位 / conveyor + 指派相位）给出这条事实的真机数。

**事实 3 · 不分片 prefill 与 tick deadline 正面冲突，伤害由相位 1:1 决定。** 早期模拟器标定：最坏相位下 **L\* = 6144** token 即 deadline 超限，同样的注入落在 tick 初、**L = 8192** token 都安全；冲击宽度正好一 tick，下一 tick 回基线。
机制：不分片 prefill (one-shot / unchunked prefill) 是不可 preemption 的原子步，落在 tick 尾整段溢出；注入只要走引擎 step，就与 tick 内计算抢同一资源。
chunked prefill（Sarathi-Serve）让每块重付一次「掉出 CUDA graph capture」的固定开销（早期标定），且仍在消耗引擎步——出路是让注入的 KV 生成不走前台引擎步。
E4 按注入相位分桶实测这条 1:1 关系。

**事实 4 · 打断后的 stale resident KV。** 早期模拟器标定（40% 打断为冻结先验）：峰值 **24.2%** 的 resident KV 是已作废内容，平均驻留 **35.6 s**，每分钟 **2.2 次**陈旧拼接 (stale context splice)——用户已否决的答案照样被拼进上下文说出，是正确性事故而不只是浪费。
机制：cancellation 信号只存在于应用层（打断事件），引擎 API 没有它的入口；PagedAttention 支持按块 reclaim，但没有任何机制知道哪些块该释放。
已作废仍常驻的 KV 每步 decode 仍按原价付带宽。E4 实测这条比例，并验证 commit / cancel 能否从源头消灭它。

## 三类瓶颈与可行域

- **Capacity 瓶颈**：KV pool 字节数 / 单路 working set，vanilla 默认语义下最先饱和（E1 的 N=8 三形态，FINDINGS A3；Metronome 高并发 memory cliff，亚稳）。
- **Deadline 瓶颈**：state 被 windowed 或换出后才成为主导约束（Metronome 加 **W=1024** sliding window 后 **N\*≈209**，小于显存外推的**约 500**；早期模拟器标定给 N* = 192 / 208）。
- **注入瓶颈**：效率地板上，一 tick 内计算加注入的总需求 = 1 时 **N≈57**（早期模拟器线性外推：baseline N=48 已两头坏，48→57 是调度器可争取的空间，超过 57 进入 admission control 领域）。

摊平拐点 B\*（amortization knee：batch 大到能摊平权重搬运，越过后 MLP 转 compute-bound）在 3090 + 7B 上约 40–80（FINDINGS D1）。
哪类瓶颈先到是硬件与负载参数的函数：3090 上 capacity 先饱和（E1 确证），80 G 卡上注入瓶颈先到（早期公式推演）。
但在所有现实配置下 capacity 瓶颈都远早于卡的计算能力耗尽，D1 的 busy/T ≈ 38–55% 不变量是这条结论的硬件无关形式——这是全部机会所在。
瓶颈以内由调度负责，超出瓶颈只能靠 admission control：那不是本问题的失败，是它的边界。

silent failure 让上述三条都测不出来：cadence 指标全绿而内容已过时。
崩溃状态下 worker 等待帽 1.6 s < 2 s deadline，每 tick 仍准时返回空帧，miss 恒 0%、frame delivery 100%（FINDINGS B1）；client latency 恒 1 ms 而 semantic response lag 最多约 16 s（FINDINGS B2）。
duplex serving 因此需要独立的 content freshness SLO（按 SRE 意义给内容陈旧度阈值），容量决策不能只看利用率。

## 为什么难：结构性信息缺失与跨层耦合

**信息是结构性缺失，不是没调好。** 决策需要的字段——deadline、相位、可延性、cancellation 信号——在任何引擎的请求模型里都不存在。
调度器眼里 8-token 唤醒和 8192-token 注入是同一种对象，显存管理器眼里已作废的 KV 和马上要 attend 的 KV 是同一种字节。
eviction 按 LRU，而这个负载的正确信号是「预计下次使用」且精确可知（下 tick = 上 tick + T，静默 / 播放状态可预测）——LRU 恰好逐掉马上要用的。
这些信息物理上全部可得：注入大小到达即知、tick 周期精确可预测、内容按帧冻结、cancellation 信号即时。
缺的是引擎数据结构里放这些信息的位置，以及围绕它们的四个决策：相位指派 (phase-offset assignment)、H2D 搬运时刻表（release time = 内容冻结点，deadline = 计算槽 − τ_lead，即 prefetch lead time）、commit / cancel 语义（uncommitted 停 DRAM）、静默停泊 (idle-session offload)。
E1 给出代码级实例：何时 preempt 由池算术决定（两次独立运行的六次 preemption 时刻吻合 ±0.4 s），preempt 谁纯属 `running.pop()` 的瞬时排列，被抢占者与仍在 running 者的 context 差仅 2–3 token（FINDINGS A4）。

**跨层耦合，单层局部最优可能全局反向。** CUDA graph capture 这一内核层实现属性，决定调度层「切块是否可行」。
显存层 eviction 的恢复路径本身制造或不制造一次注入：重算一个 4k token 会话 = 330 ms prefill（早期标定），等于自己给自己造一次注入；swap 实测只要 38.1 ms（4k token，pinned H2D 12.33 GB/s，`calibration/data/pcie_h2d_bench.json`）且走 DMA 引擎可与计算重叠——引擎步对拷贝引擎，这对数字既是「用闲置带宽换更大容量」的成本基础，也是重算路径被否掉的原因。
有界 sliding window 解开 KV 压力，却使注入无法驻留：几千 token 的工具结果可能还没被说出来就滚出窗外。
KV 方案与注入方案必须联合设计，这是把「链路调度」与「提交语义」做成一体的原因。

## 领域空白

- **Serving 文献**：截至 2026-08，全双工 GPU serving 论文只有 Metronome 一篇（无注入、无作废，负载最温顺）；它对 KV 装不下的答案是 sliding window 截断，有损，且与注入需要长期驻留冲突。
- **模型层在为服务侧的缺位买单**：MoshiRAG 明知插入式注入精度更好却弃用，理由是 "to constrain sequence length"；全部开源双工模型的上下文折合会话时长 ≤20 分钟——领域对 KV 增长的现行答案是「忘掉」。
- **产品层证词**：Seeduplex 自述克服了「高并发下的延迟尖刺与稳定性问题」，解法不公开；GPT-Live 单会话 ≥1 小时（社区实测），手段不公开。
- **能力矩阵**：五列（tick deadline / batching / KV cache / 注入安放 / 作废语义）里，「注入的 deadline-aware 安放」与「输入侧作废回收」两列现有系统均未覆盖——恰好是要素 ② 的两半。

逐产品规格、moshi-server 源码级核实、逐模型会话时长换算的原始整理在 `.context/references/full-duplex-model-product-serving-landscape-2026-08.md`。

## 与 Metronome 的关系

Metronome（arXiv:2607.02640）是截至 2026-08 唯一的全双工 GPU serving 论文，其归因原话是 "The failure is a memory cliff, not a compute drift"。本仓库与它的关系有六重，性质各不相同，引用时不要混：

| # | 关系 | 内容 |
|---|---|---|
| 1 | 交叉验证 | 真机（Qwen3-Omni-30B FP8 / 96 G / tick 2 s）独立测得同一瓶颈出现顺序：vanilla 下 memory cliff 先到（计算远未饱和），KV 受限后 deadline 瓶颈 N\*≈209 小于显存外推约 500，与本仓「显存先于算力」同构（数值巧合不构成校准）；引用其数字前先过 `docs/metronome.md` 的订正纪律 |
| 2 | 对照负载 | 它测的是最温顺的双工负载：每帧存活量恒定、无注入、无作废——要素 ② 的两半它全空 |
| 3 | 方案种子 | 刻意错开相位的实验设置升级为相位指派；sliding window 的 state-bounded 世界是有损对照 |
| 4 | 竞争方案 | 它对「KV 装不下」用 W=1024 sliding window（有损，与注入驻留冲突）；conveyor 目标是无损保全上下文 |
| 5 | 互补可叠加 | 它管 capacity 上限之外（AIMD admission）与有损 cap；conveyor 在瓶颈约束内扩张 capacity |
| 6 | 实验脚手架 | 开源栈（vLLM 0.23 resumable request + 共享 tick gateway）是本仓真机 baseline 的来源 |

它 §2 以「resident 是唯一预算兼容的选择」分析性排除 swap，两个假设可证伪：全量轮换不是真实设计点（真实设计点是 partial residency 加链路扩容），以及「无空隙可藏」——每会话子 tick 占用比例 1/N 就是空隙，E0 实测 decode step 时间膨胀系数 κ = 1.067，H2D 几乎不拖慢计算（FINDINGS E3）。

## 方案方向（摘要）

每路尾部 KV 的母本住在 host DRAM，按时间表每一 tick 经 DMA 搬入 HBM 暂存、算完即释放，攒满阈值才 commit 为 resident（借用 two-phase commit 的形状）。
等效容量 = resident M + staging P，收益比是纯硬件比值。
可行的前提是周期已知、相位可指派、内容按帧冻结（搬运作业的 release time = 内容冻结点，deadline = 计算槽 − τ_lead）。
与四个事实一一对应：事实 1 是收益来源；事实 2 → 相位指派把「刻意错开相位」从实验设置升级为调度资源；事实 3 → 注入走同一链路的第二优先级、不进引擎 step；事实 4 → commit / cancel 从源头消灭 stale resident KV。
与 Metronome 的 AIMD 准入和有损 cap 正交可叠加。公式、增益表、编排细节与诚实边界属于方案记录，不在本文展开。

## 明确不做什么

语音合成头与音频 tokenization；过载区 N 超过产能上限（admission control，Metronome 的地盘）；多卡 prefill / decode 分离（作参照 baseline 对比，不作贡献）；80 ms 锁步家族（tick 短 6 倍，收益除以 6）。
早期模拟器标定用较小标定模型推演增益，其数字是乐观上界；真机栈（RTX 3090、tick 2 s）与论文主配置（tick 480 ms）不同，数字以 `results/paper/` 的运行记录为准。
