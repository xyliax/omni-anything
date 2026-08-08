# 术语表

全仓术语的唯一完整定义处。各文档首次使用只留短注（中文名 + 英文对照），完整判据、边界与词源以本表为准。

| 术语 | 英文 | 定义 |
| --- | --- | --- |
| 全双工 | full-duplex | 听说同时、无轮次边界的语音交互形态；本仓的前台负载 |
| 硬 tick | hard tick | 固定周期 T 的硬 deadline 帧，inelastic；即 Metronome 的 frame budget B（tick 与 frame budget 均为其论文自用词） |
| deadline miss | — | 该 tick 输出未在 T 内就绪。H2D 搬运晚点写「迟到」，不占用 miss 一词 |
| N* | schedulable concurrency（可调度并发数） | deadline miss rate ≤ 1% 判据下的最大并发路数；承自 Metronome |
| 饱和 | saturation | KV 池占满导致会话 starve 的状态 |
| capacity-bound | — | KV 池容量先于算力耗尽；区别于 bandwidth-bound 意义上的 memory-bound |
| KV conveyor | scheduled tail-KV offloading | 按 tick 时间表把每路尾部 KV 母本从 host DRAM 经 DMA 预取入 HBM 暂存、算完即释放；谱系 FlexGen / InfiniGen / vLLM offloading connector / LMCache |
| 等效 KV 容量 | — | resident M + staging P |
| 母本 | authoritative host copy | host DRAM 中该会话 KV 的唯一权威副本；HBM staging 是它的短命拷贝 |
| 注入 | injection | 后台 agent 结果写回对话；delay-tolerant 弹性负载，对照 inelastic 的硬 tick 前台 |
| 插入式注入 | token-insertion injection | 注入内容逐 token 插进序列的路径（MoshiRAG 弃用的那条） |
| commit / cancel | — | 注入语义：结果以 uncommitted 态停 DRAM，确认说出才 commit，打断即 cancel；借 two-phase commit 之形，非 2PC |
| 转正 | promote to resident | 尾部攒满阈值 C 后转 resident；与注入的 commit 分词，避免混用 |
| 相位指派 | phase-offset assignment | 服务端准入时指派会话相位的调度机制（TDM 式错开） |
| 相位错开 | stagger（`FD_PHASE_STAGGER`） | 客户端测量卫生：各路音频窗口互不重合，防 prefix cache 使容量读数虚高 |
| 相位打散 | phase desynchronization | 打散后的执行状态：用算力余量换常驻缩减，守恒律与上界见 FINDINGS D3 |
| 非重叠忙碌窗 | time-multiplexed residency | 各会话计算窗互不重叠、KV 不同时常驻；conveyor 容量收益的必要条件 |
| token 配额 | per-tick token quota | 每路每 tick 的 decode token 上限（E1 栈实测语义恒 33/段）；裸写「配额」即此义，H2D 侧写「staging 预算 P」 |
| κ | slowdown factor（减速系数） | DMA 并发下 decode step 时间比，κ = t_with/t_without |
| η | H2D 预算系数 | 设计允许占用的链路带宽比例（工程假设 0.7）；与实测链路可用率、E3 实达值是三个不同的量 |
| compute-bound 拐点 B* | roofline ridge point | batch 大到摊平权重搬运、MLP 转 compute-bound 的阈值 ≈ 字节/参数×TFLOPS/(2BW) |
| 静默停泊 | idle-session offload | 静默会话整路 KV 下放 host |
| stale resident KV | — | 已作废仍常驻显存的 KV |
| 陈旧拼接 | stale context splice | 已作废内容被拼进上下文说出的正确性事故 |
| content staleness | — | 内容陈旧度（semantic response lag 为同义旧称）；其服务目标是 content freshness SLO（SRE freshness 义） |
| silent failure | — | cadence 指标全绿而内容已过时（FINDINGS B1/B2） |
| preemption cascade | — | 池满后一路路被 preempt、幸存者工作集越滚越大（FINDINGS A3②） |
| admission deadlock | — | 池恰在 tick 间隙打满、无人可 preempt 的全员冻结（FINDINGS A3③） |
| permanent starvation | — | 被抢占后因 re-admission 条件永不复活（FINDINGS A5） |
| 冻结负载参数 | frozen workload parameters | E4 预注册的负载常量（40% cancellation、LogNormal 注入等）；设计决定，非统计先验 |
