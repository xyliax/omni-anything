# 双工模型 + 后台 Agent 的 Serving 问题

*写给熟悉大模型 serving（continuous batching、chunked prefill、PagedAttention、KV cache 管理）的读者，但对「双工语音前台 + 后台 agent」这一产品形态还不熟。目标：讲清这个负载为什么被显存先卡住、现有引擎为什么在容量远没到头时就崩坏，以及由此收敛出的方案方向（见 `IDEA-KV-CONVEYOR.md`）。*

> **⚠️ 存档声明（2026-08-06 仓库清理）**：本文写于问题发现阶段，数字来自当时的模拟器与标定谱系——**该谱系已整体删除**（git 5020583 及之前可溯）。显存成为瓶颈、三类瓶颈等核心主张，现由 **E1 真机证据**支撑且更强（见 `PAPER-EXPERIMENTS.md` 执行记录），**本文中的模拟器数字不应再被引用**。**例外：§5 补充证据（双工产品与文献查证）仍为现行内容。**

---

## 1. 这个负载和你熟悉的 serving 差在哪

**产品形态**：类似 GPT-Live 的「会打电话的 AI」。前台是全双工语音模型——边听边说，没有回合边界；复杂任务交给后台 agent（别的卡或 API），结果返回后拼进前台模型的上下文（由前台模型为这段文本计算 KV cache），前台才能把答案说出来。

**前台的执行结构**：交互切成固定 tick。真实模型谱系分三类——Moshi 系锁步 80ms/帧（输入并入自回归步，无独立 prefill）；SyncLLM 系时间分块 160–240ms（每块追加用户 token，并生成约 13 个 token）；Qwen-Omni / Freeze-Omni 系 thinker 架构（音频编码器分块输入 = 增量 prefill，主干出文本，轻量语音头合成）。本工作对标第三类：**每 480ms 一 tick = 约 8 个 token 的增量 prefill + 2–4 次 decode**。硬约束：一 tick 内做不完 = 音频断裂 = 正确性事故（miss，超时漏拍）；引擎不会丢弃迟到的 tick，只会往后压。

**后台注入**：工具结果长度为 L 个 token，真实分布是「多数几百（函数调用）+ 少数几千（搜索/文档，约 10% 长尾 4–8k）」。**40% 的对话含打断**：在飞的、已返回的、甚至已拼入的结果随时作废。

于是同一张卡上出现两种特征相反的计算——这是全部问题的起点：

| | 每 tick 的语音工作 | 工具结果注入 |
|---|---|---|
| 形态 | 周期性，每次约 10 个 token | 突发，一次数百到数千 token |
| 时限 | 480ms 硬 deadline，迟到即事故 | 无 deadline，可推迟、可切块 |
| 生命周期 | 永远有效 | 随时可能整段作废 |
| 大小可知性 | 已知且恒小 | **到达时精确已知** |

对 serving 读者的第一句提醒：**你的全部直觉都以「请求是短暂的、无 deadline 的、不可作废的」为前提**。这个负载三条全破。

## 2. 一条贯穿全文的物理（标定结果，直接引用）

一步 decode 的时间在 21 个实测格子上拟合为（平均残差 1.4%）：

```
步时 ≈ 6.52ms（权重搬运，全 batch 共享）+ 0.106ms×B（每行元数据）+ 0.155µs×Σctx（KV 字节，每序列私有）
```

外加一条**混合步固定开销**：步里只要掺任何 prefill token，整步掉出 CUDA graph，付约 **13ms 固定开销（CUDA graph overhead），与掺入量无关**（batch 大小 B=8 时纯 decode 12.35ms；掺 64/128/256 个 token 恒为约 25.1ms；从 512 起按 0.054ms/token 线性增长）。三个推论后文反复用到：**batch 大小 B 能摊薄权重项、没有任何东西能摊薄 KV 项、开销按引擎步计不按 token 计**。KV 主导区的算力利用率上限约等于 309/ctx（%），与 B 无关——decode 引擎本质上是 memory-bandwidth-bound。

## 3. 问题清单：四个实测事实，指向同一个结构

> 下列 P1–P4 中的模拟器数字（S1–S3 等）来自已删除的早期试跑谱系，**已被 E1 真机证据取代**；结构判断仍有效，数字勿当现行引用。

### P1 显存先成为瓶颈约一个数量级，而卡大部分时间在空转

**现象**（S1 密度，早期模拟）：KV 可行密度 N=12，超时瓶颈在 N=192/208（随机/对齐相位，判据 miss>1%，模拟外推）——**显存先成为瓶颈约 16 倍**。单会话占空比仅 4–9%：每 tick 只有约 20–45ms 在算，其余约 440ms 这一路对 GPU 无所求。Metronome（arXiv:2607.02640）在真实软件栈（Qwen3-Omni-30B FP8 / 96G / 2s tick）上独立复现同一瓶颈出现顺序：vanilla 配置下常驻 KV 在 N=128 触达 memory cliff 时，GPU 时间占用仅约 13–32%——原话 "memory kills sessions whose compute the GPU could easily carry"。

**机制**：双工会话的 KV 每 tick 必被 attend，没有轮次间隙可换出重算；KV 常驻单调涨，而每 tick 只碰每路状态几次。时间占用上限约等于 每 tick 触碰次数 × (容量/带宽) / tick 时长 ≈ 20%（H100/480ms）——**卡是先装不下，远没跑满**。这也是 `IDEA-KV-CONVEYOR.md` 的问题定义原文。

**顺带的 under-batching 事实**：N=12 随机相位时平均 batch 大小 avgB=1.46；66 对会话里 47 对在 60 秒内从未同 batch；同样的工作比对齐相位多花 **4.96 倍 GPU 时间**，其中 CUDA graph overhead 占全卡忙时 64.7%（每路每 tick 独开一个 prefill 步、独付 13ms）。引擎是 work-conserving（有活就干、从不等待），batch 大小 = 到达碰巧重叠的量——**相位从没被当成资源管理**。这条事实在方案里升级为编排设计的第一对象（相位指派）。

### P2 整段注入与 tick deadline 正面冲突，伤害由相位 1:1 决定

**现象**（S3 注入冲击，早期模拟）：最坏相位下 **L\*=6144** 即 miss deadline；同一个 L=8192 落在 tick 初却完全安全（最大一 tick 257ms）——阈值是相位函数，不是常数。最大 tick 时与注入偏移 **1:1 线性**（L=5120：偏移 5ms→71.7ms，偏移 470ms→441.3ms）：纯溢出，不是计算变多。冲击只有一 tick 宽，下一 tick 即回基线。

**机制**：L≥4096 的整段 prefill 是 330–720ms 的原子步（步不可 preemption + 成员冻结），deadline 只有 480ms。落在 tick 头无 deadline 压力，落在 tick 尾整段溢出。

**为什么修不掉**：注入落点相位不受控（工具返回时刻由后台 agent 决定）；切块让每块重付 13ms CUDA graph overhead（§2），且仍在消耗引擎步。指向的出路是**不让注入的 KV 生成走前台引擎步**：注入 KV 经 DMA 链路搬运，以 uncommitted 态停在 DRAM 里，只有「说出它」的那一 tick 才需要引擎（`IDEA-KV-CONVEYOR.md` §3.4）。

### P3 打断后的无效缓存占用：打断的代价以带宽开销的形式每 tick 重复支付

**现象**（S2 作废，40% 打断先验，早期模拟）：19.6% 的调用结果在返回前已失效；峰值时**引擎常驻 KV 的 24.2% 是已知作废内容**，平均驻留 35.6s；每分钟 2.2 次陈旧拼接——用户已否决的答案照样进上下文，模型会把它说出来（正确性事故，不只是浪费）。

**机制**：引擎没有作废语义（结果到达即拼、无检查；KV 只增不减）。按 §2 的定律，已作废但仍常驻的缓存不只占显存——**该会话之后每个 decode token 都为这些字节付 0.155µs/token 的带宽原价**，是每步持续支付、无法收回的带宽开销。

**为什么修不掉**：作废信号存在于应用层（打断事件），引擎 API 没有它的入口；PagedAttention 支持按块释放，但没有任何机制知道**哪些块**该释放。方案对应：提交语义——uncommitted 的注入停在 DRAM，确认说出才进常驻池，作废 = DRAM 直接丢，24.2% 的无效常驻占用从源头消灭。

### P4 KV 与「满载」的双重误判

**KV 信号全反**：显存吃紧时，eviction 按 LRU（最近最少使用），而这个负载里正确信号是「预计下次使用」——且**精确可知**（下 tick = 上 tick + 480ms；静默/播放状态可预测）：LRU 恰好会逐掉马上要用的。恢复默认走重算——重算一个 4k 会话 = 330ms 的 prefill = **自己给自己制造一次 L=4096 注入**；而 swap 实测只要 38.1ms（4k token，pinned H2D 12.33GB/s，`calibration/data/pcie_h2d_bench.json`，2026-08 落盘复测）、走 DMA 引擎可与计算重叠、prefetch 可全藏。**330ms 对 38ms、引擎步对拷贝引擎——这对数字就是「用闲置带宽换更大容量」方案的成本基础，也是其 v1（重算版）被否掉的原因**（`IDEA-KV-CONVEYOR.md` §二）。

**utilization paradox**（high utilization without useful progress）：利用率有三个定义——时间占用 / 带宽（约 77%）/ 模型浮点利用率 MFU（个位数，约等于 309/ctx）。N=24 时利用率 0.98 里**约一半来自可避免的低效**（under-batching + CUDA graph overhead），必要需求只有 0.49。更隐蔽的是**用 queueing delay 换更大 batch**（queueing delay traded for larger batches）：高 N 下积压自发凑 batch（avgB 从 1.46 到 59），平均 batch 变大，但代价是排队延迟上升。对照：对齐相位 N=96（利用率 0.51、p99 延迟 258ms、零 miss、半张卡待命）与随机相位 N=192（利用率 1.0、p99 532ms、1.7% miss）到达同一个约 2.3–2.6 GPU-ms/tick 的摊薄地板——工作点差异很大。**不能只凭利用率做容量决策。**

## 4. 为什么难，以及出路的形状

1. **信息是结构性缺失，不是没调好**。决策需要的字段——deadline、相位、可延性、作废信号——在任何引擎的请求模型里都不存在。调度器眼里 8-token 唤醒和 8192-token 注入是同一种对象；显存管理器眼里已作废的 KV 和马上要 attend 的 KV 是同一种字节。而这些信息物理上全部可得：注入大小到达即知、tick 周期精确可预测（下 tick = 上 tick + 480ms）、内容按帧冻结、作废信号即时——**缺的从来不是信息或算力，是引擎数据结构里放这些信息的位置，以及围绕它们的四个决策**：相位指派（准入时）、H2D 搬运时刻表（释放 = 内容冻结点、截止 = 计算槽 − 提前量）、commit/cancel 语义（uncommitted 停 DRAM）、静默停泊。这四个决策即 `IDEA-KV-CONVEYOR.md` §3.3–3.4 的编排设计。
2. **跨层耦合，单层局部最优可能全局反向**：CUDA graph overhead（内核层实现属性）决定调度层「切块是否可行」；KV eviction（显存层）的恢复路径选择（重算 vs swap）本身制造或不制造注入（调度层问题）；有界 sliding window（Metronome 式）解开 KV 压力却使注入无法驻留——几千 token 的工具结果可能还没被说出来就滚出窗外。**KV 方案与注入方案必须联合设计**，这正是方案把「链路调度」与「提交语义」做成一体的原因。

## 5. 相关工作：为什么说这两列是空白

2026 上半年该领域快速围拢（问题本身已被同行验证），但按能力矩阵：

| | tick deadline | batching | KV 显存 | **注入调度** | **作废语义** |
|---|---|---|---|---|---|
| moshi-server（400 路 STT/H100） | ✓ 锁步 | ✓†仅 STT/TTS | 环形窗口封顶 | ✗ | ✗ |
| Metronome'26（tick + AIMD 准入） | ✓ | ✓ | sliding window + sink 封顶 | ✗ | ✗ |
| LiveServe'26（swap + 语义 prefetch） | 轮级软目标 | — | ✓ 卸载 + prefetch | ✗ | 半（仅输出侧未听 token） |
| VoxServe'26（流式调度） | 首音频时间 TTFA 级 | ✓ | — | ✗ | ✗ |
| Sarathi / Niyama | 软 ITL（token 间隔） | — | — | ✗ | ✗ |
| vLLM-Omni（现状对照） | ✗ | ✗ | ✗ | ✗（整段拼） | ✗ |

（† 双工语言模型主干在官方栈里 batch 大小 B=1、无 batch，见下文 (a) 源码证据。）各家分别解决了 tick（锁步 / tick）、KV（封顶或 swap + prefetch）、准入（AIMD 拥塞控制）——**「注入的 deadline 感知放置」与「输入侧作废回收」两列全场空白**，而 P2/P3 恰好全部落在这两列。另注意 Metronome 的 sliding window 封顶与注入天然冲突（几千 token 的结果可能还没被说出来就滚出窗外）——KV 方案与注入方案必须联合设计，这本身是尚未有人系统解决的问题。Metronome（[arXiv:2607.02640](https://arxiv.org/pdf/2607.02640)）的实测数字与本工作的瓶颈出现顺序分析同构，可作「无注入」上界参照：其负载形态为真双工工况（20ms 音频持续流入、常驻会话、每帧硬 deadline、KV 常驻单调涨；模型侧 Moshi 为原生真双工，Qwen-Omni / MiniCPM-o 为被自由运行连续驱动的时间片型），栈为 Qwen3-Omni-30B FP8 等四模型 + RTX PRO 6000 96GB + **2s 帧预算**（比本工作的 480ms 粗 4 倍，比 Moshi 原生 80ms 粗 25 倍）。实测：**vanilla 配置（KV 无界常驻）= memory cliff**——N=128 时每帧延迟从几 ms 一步跳至 1.6s 引擎僵死，且亚稳（20 次运行 14 次崩）；**W=1024 sliding window 使状态有界后瓶颈出现顺序反转**——显存上限外推约 500 路，AIMD 准入实测可调度 N\*≈209，deadline 先于显存。但其每帧工作为恒定形状（分块进、τ 个 token 出，无 m_t 异质），且不含注入、不含作废——**它测的是双工 serving 工况里最温顺的负载，两列依旧全空**。

### 补充证据：Kyutai 两条线各覆盖了问题的一半（2026-08 调研，源码级核实）

**(a) 双工主干「无人 batch」有源码级证据。** Kyutai 生产服务端 [moshi-server](https://github.com/kyutai-labs/moshi)（Rust）中，batch 推理仅实现于语音识别 / 语音合成模块（`batched_asr.rs` 带 `batch_size` + `StreamMask` 槽位管理；TTS Python 模块同）；**全双工语言模型模块的 `LmConfig` 无 `batch_size` 字段，每条 websocket 会话独立 clone 流式状态、B=1 串行**（`moshi-server/src/main.rs` 模块枚举、`stream_both.rs` 每会话采样配置 / 种子）。demo 用的 `moshi-backend` 独立部署同样是单会话固定缓冲。故上表 moshi-server 行的「✓ batching」仅指 STT/TTS；双工主干在官方栈里不可 batch。

**(b) Kyutai 官方自证「双工 + 工具」是缺口。** [kyutai.org/unmute](https://kyutai.org/unmute) 原话："While Moshi provides unmatched latency and naturalness, it **doesn't yet match the extended abilities of text models such as function-calling**... Unmute allows us to directly bring all of these from text to real-time voice conversations."——做出双工原生模型的实验室，因工具调用缺位主动退回级联。两条产品线恰好各覆盖一半：**Moshi 砍工具保双工**（定长环形 KV、无注入、每 tick 恒定 1 步——靠架构自限维持锁步可 batch 的前提，却连这个 batch 也没实现）；**Unmute 砍双工保工具**（级联 STT→任意 LLM→TTS，MIT 开源；对话无硬 tick，回合制；工具调用发生在文本 LLM 侧，由 vLLM 按普通聊天负载处理，「注入回 tick 流」问题不存在）。两半的组合——本工作的负载——无人服务。

**(c) Unmute 的 tick 只存在于组件内部。** STT/TTS 均为延迟流模型（DSM）12.5Hz 锁步（80ms/步，[arXiv:2509.08753](https://arxiv.org/html/2509.08753) §3.1–3.2）：每流每步工作恒定 → 可 batch（H100：ASR batch 256 时实时因子 RTF 1.49 / 吞吐 380×；TTS batch 64 时 RTF 2.1、首音频 403ms，Table 6/10）。TTS 文本流设计延迟 16 步 = 1.28s，B=1 时首音频 150ms。级联端到端亚秒级。**这印证 batching 可行性的边界：工作恒定则 400 路，工作不定长（双工主干 m_t、注入）则连 Kyutai 也没 batch。**

**(d) 双工并发的社区数字只能作轶事引用。** Moshi 7B 多路并发无任何官方数字（论文全文 / README / FAQ 均无）；两个第三方博客给 4–10 路/H100（localaimaster、spheron，均无方法学，其一把 4090 与 H100 并列同一数字——恰说明「无 batching」工况下瓶颈不随硬件档次移动，是软件上限不是硅片上限）。引用时标注来源性质。

**(e) 真双工已于 2026 年上半年双双量产，serving 层均不公开。** ①**Seeduplex**（字节 Seed，[2026-04-09](https://seed.bytedance.com/en/blog/introducing-seed-full-duplex-speech-llm-attentive-listening-robust-interference-suppression-enabling-more-natural-interaction)，全球首个）：原生全双工语音大模型，"listen while speaking"，模型逐步决策 start replying / continue listening / respond to interruptions；已全量部署豆包 App（数亿用户）。公开数字全为相对值（端点延迟 −250ms、打断响应 −300ms、误响应 / 误打断减半、抢话 −40%、流畅 MOS +12%）；无 tick 长 / 尺寸 / API。**工程自述极有价值：投机解码 + 量化控成本，且明确承认克服了「高并发下的延迟尖刺与稳定性问题」**——双工 serving 之难的第一手产品界证词，解法未公开。②**GPT-Live**（OpenAI，[2026-07-08](https://openai.com/index/introducing-gpt-live/)）：真双工——"continuously processes input while generating output"，每秒多次决策 "whether to speak, continue listening, pause, interrupt, **or invoke a tool**"；**复杂问题委托 GPT-5.5 后台执行、结果送回对话**——「双工前台 + 后台 frontier 回注」与本负载逐项对应；已取代 AVM 成 ChatGPT 语音默认（每周 1.5 亿语音用户）；[系统卡](https://deploymentsafety.openai.com/gpt-live)零架构数字，API 未开放；社区实测单次会话 ≥1 小时（Simon Willison, HN）。对照组（回合制产品面）：gpt-realtime-2（128K 上下文，`turn_detection` + truncate 对账，快进生成囤缓冲）、Gemini Live（音频 15min / 音视频 2min + sliding window 压缩）、Nova 2 Sonic（约 8min 流硬上限，生产靠提前轮换）、Qwen3.5-Omni Realtime（120min 会话上限；**上下文只保留最近 480–600s 音频，最旧优先丢弃 drop-oldest**——环形封顶上移到 API 语义层；思考模式与音频输出互斥）。结论：闭源两家已进入生产部署（一家把注入做成 tick 内决策，一家自述高并发尾延迟之痛），开源侧无桥——两列空白的价值被产品事实抬高。

**(f) 负载假设的外部对标（全部实测配置 / 论文原文核验）。** [DuplexOmni](https://arxiv.org/html/2606.09186v1)（arXiv 2606.09186，Qwen3-Omni 家族）§3.1.2 用**固定 480ms 时间片**——与本工作 tick 长逐字一致；每片 thinker 产出 "mₜ Assistant tokens"（**符号即 m_t，论文未给数**，上界由「480ms 内必须说完」锁定 ≈1.5–4）；talker 每片 6 个 codec 帧（12.5Hz，第 0 层自回归 + 多 token 预测 MTP），本工作不建模语音头 = 乐观方向（已在效度威胁 3 声明）；输入率继承 Qwen3-Omni 配置 `position_id_per_seconds: 13` → 约 6 token/片（本工作取 8，居谱系中位 12.5–25 tok/s）；**thinking 层异步回注是其官方设计**——注入通道已在模型侧标准化。权重现实：Qwen3-Omni-30B-A3B bf16 实测 70.5GB（Hugging Face 15 个分片加总）——80G 卡上 bf16 权重即近吃满，**FP8 是双工部署的起点而非优化**（Metronome 亦用 FP8）。

**(g) 全场通用的「会话时长上限」：现有双工对输入侧 KV 增长的唯一答案是忘掉。** 按各工作官方配置 / 论文换算成会话时长：hertz-dev 2048 token ≈ **4.3 分钟**、Moshi 环形 3000 步 ≈ **4 分钟**（FAQ 的 5 分钟上限即此）、SyncLLM 8192 ≈ **4.5 分钟**（论文自认 limitation）、GLM-4-Voice 8192 ≈ **10 分钟**、Qwen2.5-Omni 32k ≈ **20 分钟**——**无一开源双工模型能撑过 20 分钟对话**；产品层同构（Nova 8min 流上限、Qwen Realtime 只留最近 480–600s 音频、Gemini 靠 sliding window 压缩、GPT-Live 1 小时实测但手段不公开）。瓶颈出现顺序的跨工作规律：**每 tick decode 轻且常开摄入（家族一锁步、家族三 thinker）→ 显存先成为瓶颈**（Moshi 定长 2GiB/路 → 96G 卡约 30 路；7B thinker 增长约 0.8GiB/10min → 80G 卡从 64 路滑到 21 路随时长滑坡）；**decode 重（家族二 SyncLLM 约 7 个 token 串行 / 160ms）→ 算力瓶颈升至与显存瓶颈同高**（约 58 对约 60）；**语音活动检测（VAD）门控摄入（Freeze-Omni）→ 显存最不缺、延迟先成为瓶颈**——印证「哪类瓶颈先到是负载 / 硬件参数的函数」。

**(h) 注入问题的三方证词（2026-08 增补）。** ①产品层：GPT-Live 把 invoke a tool 做成每秒多次的 tick 内决策（见 e）。②模型层：[MoshiRAG](https://arxiv.org/html/2604.12928v3)（Kyutai，ICML 2026）给全双工模型加异步检索——`⟨ret⟩` 触发、检索期间继续生成 pre-RAG 填充内容；**注入机制刻意回避 prefill**：检索文本 4× 压缩后按帧**加法叠进输入嵌入**，附录 B.1.1 明说插入式注入精度更好但被弃，"to constrain sequence length"——**模型侧对「注入 → KV 增长是要害」的直接供认，现行解法是牺牲精度绕行**；其时序数字首次量化了注入的语义藏身窗：检索预算 ≤2s、关键信息前 ≥1.0s 缓冲、实测端到端关键词延迟 3.1s（vanilla 基线 2.1s）——延迟类策略的语义可行性上界。同模式另有 KAME（Sakana，[arXiv:2510.02327](https://arxiv.org/abs/2510.02327)，实时语音到语音 + 后台 frontier 串联）。③serving 层：专项检索（2026-08-01）确认除 Metronome 外**真双工 GPU serving 文献为零**（[Awesome-Full-Duplex-SDM](https://github.com/Ruiqi-Yan/Awesome-Full-Duplex-SDM) 全列表无一 serving 论文）。评测平台展望：[Nemotron 3 VoiceChat](https://build.nvidia.com/nvidia/nemotron-voicechat/modelcard)（NVIDIA 2026-03，12B 开源真双工 + NeMo 官方推理管线 / NIM）是本工作走出模拟器时最现实的宿主，其文档同样无并发 / 批量规格——连 NVIDIA 也未发布双工 serving 数字。

## 6. 空间有多大：三类瓶颈与方案指针

**三类瓶颈全有可用公式直接算的关系**（可行域清晰）：摊薄平点 N≳32；注入瓶颈 gap(N) ≥ 注入需求(N) → N≈57（历史模拟外推）；KV 瓶颈 = 池字节 / working set（哪类先到是硬件参数的函数：3090 上 KV 先成为瓶颈、80G 卡上注入先成为瓶颈）。瓶颈以内由调度负责；超出瓶颈只能靠准入控制——那不是本问题的失败，是它的边界。瓶颈出现顺序已获独立实测印证：Metronome 在真实软件栈上测得 vanilla 配置的 memory cliff 先到（N=128 亚稳崩溃），有界 sliding window 使 KV 状态有界后才反转为 deadline 先到（N\*≈209 < 显存外推约 500）；真机结论见 `FINDINGS.md`。

**收敛出的方案**（`IDEA-KV-CONVEYOR.md`）：既然显存先成为瓶颈约一个数量级、而 H2D 链路与计算时间大量闲置，就**用带宽换更大容量**——每路尾部 KV 母本住 DRAM，按时间表每 tick 经 DMA 搬入、算完即释放；等效 KV 容量 = M + P（P = 一 tick 能搬入的量），收益比 P/M 是纯硬件比值（PCIe5 / 480ms tick +24%，净约 20%；3090 / PCIe3 +83%；2s tick 约 +100%）。相位指派把 Metronome 的「刻意错相实验设置」升级为调度资源；提交语义把 P3 的无效常驻缓存从源头消灭；注入 KV 走同一条链路的第二优先级——P1–P4 四个事实在方案里各对应一个设计组件。

---

## 证据索引

| 主张 | 来源 |
|---|---|
| E 系列真机结论（现行） | `FINDINGS.md`、`results/paper/`、`results/figures/` |
| H2D / DMA 标定 | `calibration/data/pcie_h2d_bench.json`；E0 论文证据 `results/paper/e0/` |
| 方案收益公式 / 相关工作对比 | `IDEA-KV-CONVEYOR.md` §3.2 / §四 |
| 产品 / 文献查证（§5） | 本文 §5；`.context/references/` 白名单 notes |
| 已删模拟器试跑 / `EVIDENCE.md` / `TIMELINES.md` / `T1–T4` | **仅 git 可溯**；不得当现状证据 |
