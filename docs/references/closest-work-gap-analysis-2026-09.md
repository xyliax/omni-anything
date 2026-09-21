# 最接近工作的缺口分析：为何非 naive 的 KV 换出/换入方案仍未解决周期双工会话的驻留问题（2026-09）

外部文献调研。核对日期：2026-09-21。

## 核对日期与证据边界

本报告是外部调研，不是项目事实源：不定义本项目的 workload、机制、术语或贡献；机制描述沿用各论文自身表述，未映射到本项目词表。所有断言标注来源位置（章节、图表或算法号）；读不到全文的条目标注"仅据摘要，待核验"，不从摘要推断机制细节。任何内容进入论文前必须再核原文。仓库内既有综述（[KV offload 综述](kv-offload-restore-landscape-2026-08.md)，核对 2026-08-29；[双工 serving 综述](duplex-serving-systems-landscape-2026-09.md)，核对 2026-09-02）与 [closest-work 矩阵](../../eurosys2027/planning/related-work-matrix.md) 只作起点，本报告的每条结论均按本次一手核验重写。

分析所针对的负载与缺陷编号取自本项目当前文档（[问题定义](../problem.md#the-gap-in-existing-approaches)、[设计目标](../system.md#design-goals)），在此仅复述以便对照：负载是按固定 micro-turn 推进的双工会话，每会话每周期 `T` 释放一次更新，更新计算时长远小于 `T`，更新之间该会话 KV 不被访问，历史跨更新保留并每周期增长，每次更新有软实时期限。对 naive 方案（更新后整段换出、请求到达时整段换入）的四个缺陷：

- D1 相位对齐时容量收益为零：所有会话同时活跃，峰值仍是状态之和；
- D2 整段往返的链路需求随会话数线性增长且全有全无，没有"换多少"的旋钮；
- D3 请求到达时才换入，换入落在期限内的关键路径上；
- D4 现有 swap 由分配失败触发而非空闲触发，D2H 也进关键路径。

用户纪律：论文与对外材料不引用 Conflux（arXiv:2607.25792）；本报告只在"内部相邻工作"处记一行，不作分析对象。

## 1. 一页结论

### 1.1 审稿人问题的回答

最近的 KV 换出/换入系统确已越过 naive 方案：部分驻留（Pensieve、Strata、LMCache、LiveServe、ECHO）、链路时间约束的分块搬运（InferCept）、到达前预取（SYMPHONY、KVFlow、LiveServe、TokenCake、UNISON）、事件触发而非分配失败触发的换出（InferCept、TokenCake、Talaria、Human-Approval Retention）都各有先例。它们仍未解决本文问题的原因可归为三条，每条对应一手原文：

1. 信息来源不同。所有系统的下一次使用信息属于三类：已到达请求的队列或前缀匹配（CachedAttention §3.3.1、Strata §4.3.2、LMCache §6、Mooncake Alg. 1）、外部估计或事件（SYMPHONY §3.2 明言 hint 无时序与次序保证；LiveServe §5.1 next-use 为播放加 turn 间隔均值的估计；InferCept §4.4 以流逝时间估计暂停时长；Bidaw §3.3.1 以回答长度估计回归；TokenCake Eq. 1 以 EWMA 估计工具时长）、或模型内部结构（InfiniGen §4.3、ECHO §5.1）。没有一个消费负载预先给定的、跨更新反复出现的释放时刻。在固定周期负载上，这些估计器要么退化为常数（Bidaw、InferCept、LiveServe 的 T_reply），要么冗余（SYMPHONY 的 advisory）。
2. 动作域不同。部分驻留的深度由容量压力或 LRU 决定（Pensieve §4.3.2 的 25% 阈值、Strata §4.2、LiveServe §5.1 "until enough HBM is released"、KVFlow §3.1），或由重算代价决定（Pensieve V = Cost/T、Cascade Eq. 6–7 作用于恢复侧）；唯一以链路时间界定搬运量的 InferCept（§4.1 N_i）把界设为一次 forward 的时长以隐藏在他人计算后，UNISON（Eq. 8）把界设为估计的空闲时长以做 SRAM/HBM 提升。没有一个把"偏移窗口内链路可搬运量"作为空闲逐出深度的上界，也没有一个按期限排序跨会话预取。
3. 根本假设不同。会话级系统以不规则人类到达与吞吐/TTFT 为前提（Pensieve §7 "throughput instead of latency SLA"、CachedAttention Poisson 到达、Bidaw 工业 trace）；agent 系统以工具调用间隔为前提（TokenCake Table 1 的 100 ms–30 s 窗口、MORI §2.2 把 chatbot 间隔视为"数十秒"而排除）；双工系统中唯一采用周期实时任务框架的 Metronome 断言周期会话"has no lull"（§2）并据此拒绝 swap，以有损窗口约束状态。没有一个同时假设"更新按周期预先给定的时刻释放、更新间 KV 不被访问、每次更新有软期限、历史必须完整保留"。

因此本文的空间不是"提前预取"或"部分逐出"本身，而是把三者——相位指派、以预先给定的释放时刻推出的逐出深度界、按期限排序的空间门控预取——建立在同一条预先给定的时间轴上。这一定位在本次核验后成立，但须按第 3 节缩窄措辞。

### 1.2 D1–D4 汇总表

判定沿用第 2 节各条目 g 字段；"部分"表示在其负载域内实现了同类动作但缺本文所需的输入或作用点。

| 系统 | D1 相位对齐无容量收益 | D2 整段往返、无深度旋钮 | D3 到达时才换入 | D4 分配失败触发换出 |
| --- | --- | --- | --- | --- |
| CachedAttention（ATC'24） | 未处理 | 未处理 | 部分（disk→host 排队期预取） | 部分（decode 中异步写回；GPU 不跨轮保留） |
| Pensieve（EuroSys'25） | 未处理 | 部分（chunk 级、代价模型、逐前导） | 未处理 | 部分（25% 阈值，仍是容量压力） |
| HCache（EuroSys'25） | 未处理 | 部分（层维 I/O–算力平衡，作用于恢复） | 未处理 | 部分（生成中异步写 NVMe） |
| Strata（OSDI'26） | 未处理 | 部分（page 级 LRU、批次 load/compute 比） | 部分（disk→host 排队期预取） | 部分（write-through；write-back 自认阻塞） |
| Bidaw（FAST'26） | 未处理 | 未处理 | 部分（SSD→host 排队期） | 部分（写存储不在关键路径） |
| LMCache（arXiv:2510.09665） | 未处理 | 部分（chunk 级，无量旋钮） | 部分（排队期跨层预取） | 部分（生成中异步存储、主动 offload） |
| Mooncake（FAST'25） | 未处理 | 部分（block 级；路由决定拉多少） | 未处理 | 部分（prefill 中逐层写回） |
| SYMPHONY（NSDI'26） | 未处理 | 部分（按层优先级，压力/LRU 定深度） | 部分（hint 提前 5.8–11.3 s，无时序保证） | 部分（慢层持续写回；GPU 侧压力 purge） |
| InferCept（ICML'24） | 未处理 | 粒度已解决、规模部分（N_i 以 T_fwd 为界） | 未处理 | 已解决（暂停事件触发） |
| KVFlow（NeurIPS'25） | 未处理 | 部分（节点级，压力驱动） | 部分（提前一步，提前量不可控） | 未处理 |
| InfiniGen（OSDI'24） | 未处理 | 部分（有损子集，阈值定量） | 范围内已解决（层内预取，有损） | 不适用 |
| ECHO（OSDI'26） | 未处理 | 部分（DSA 性质而非调度决策） | 部分（indexer 内重叠，仍在步内） | 已解决（生成即备份，逐出零拷贝） |
| Learned Prefix Caching（NeurIPS'25） | 未处理 | 未处理 | 未处理 | 未处理 |
| Cake（ICML'25） | 未处理 | 部分（每请求 compute/load 分割） | 未处理 | 未处理 |
| CacheFlow（arXiv:2604.25080） | 未处理 | 部分（batch 内 I/O 仲裁） | 未处理 | 未处理 |
| Metronome（arXiv:2607.02640） | 未处理（假设同时到期） | 未处理（拒绝 swap，有损窗口） | 未处理（无恢复路径） | 未处理（回避压力） |
| LiveServe（arXiv:2606.22983） | 未处理 | 部分（block 级后缀先，量按需释放） | 部分（speech-onset 预取，可隐藏才接纳） | 未处理（HBM 压力触发） |
| VoxServe（arXiv:2602.00269） | 不适用 | 不适用 | 不适用 | 不适用 |
| Staggered Async. Inference（arXiv:2412.14355；RL 论文，非 serving 系统，仅作概念先例） | 概念相邻（复制品错开，无内存维度） | 不适用 | 不适用 | 不适用 |
| UNISON（arXiv:2609.09643，新） | 未处理 | 部分（Δ·B 预算，整会话） | 部分（gap 内提升） | 未处理 |
| Cascade（arXiv:2608.06557，新） | 未处理 | 部分（时间预算→恢复字节上限） | 未处理 | 未处理 |
| TokenCake（arXiv:2510.18586v4，新） | 未处理 | 部分（窗口覆盖传输才 offload，整请求） | 部分（预测返回前上载） | 触发上已解决（`call_start` 事件） |
| Human-Approval Retention（arXiv:2608.30830，新） | 未处理 | 未处理 | 未处理 | 已解决（挂起事件） |
| Ask the Tool（arXiv:2609.18849，新） | 未处理 | 未处理 | 部分（返回前一提前量） | 部分 |
| MORI / CacheWise / CacheScout / Talaria / PBKV / Pythia / ScaleSim（新） | 未处理 | 未处理或部分 | 部分（CacheScout、PBKV、Pythia、ScaleSim） | 部分（MORI）、已解决（Talaria） |

D1 一列全空是本次核验最稳固的结论：被检 40 余篇中无一把多会话需求的相位作为控制量。D4 一列中"已解决"的系统（InferCept、ECHO、TokenCake、Talaria、Human-Approval Retention）触发事件均为工具调用、暂停或生成完成，非周期 KV 空闲区间。

### 1.3 最接近的系统与单句差异

- LiveServe（arXiv:2606.22983）：同为语音会话的跨 turn KV 驻留，具备 next-use 感知逐出与到达前预取；差异在于其 next-use 是播放时长加人类 turn 间隔均值的估计（§5.1 Eq. 4）、预取由用户语音事件触发（§5.2）、逐出深度由当前需释放的 HBM 决定（§5.1），本文的三者均由负载预先给定的释放偏移推出。
- Metronome（arXiv:2607.02640）：同为周期实时任务框架下的双工 serving，且是唯一直接否认本文前提的工作（§2 "no lull"，§8 "presumes idle gaps that a periodic session never has"）；差异在于它以有损窗口约束状态并拒绝任何状态搬运，本文保留完整历史并在更新间的 KV 空闲区间内分级驻留。
- InferCept（ICML'24）：唯一以链路时间界定部分换出深度并由事件触发换出的系统（§4.1 N_i，Appendix）；差异在于其界服务于把搬运隐藏在其他请求的 forward 之后、换入仍在返回后开始（D3 未处理），本文的界由预先给定的偏移窗口给出并驱动期限排序的提前恢复。

若只许点名一个最接近工作，取 LiveServe；若须回应"周期负载已被处理"的质疑，取 Metronome。

## 2. 逐系统分析

各条目字段：a 一手来源；b 目标负载与状态对象；c 下一次使用的信息来源、产生时刻与可靠性；d 逐出粒度与逐出量的决定依据；e 恢复触发与提前量归属；f 相位重叠感知与 per-update 期限模型；g D1–D4 逐条判定；h 迁移到本文负载的具体障碍；i 基线可用性与适配障碍。

### 2.1 会话级分层与恢复

#### CachedAttention（ATC'24）

- a. 一手来源：arXiv:2403.19708v3（2024-06-30），全文已读；USENIX ATC'24 页面无 artifact 徽章或代码链接。作者 Gao, He, Sharma 等（NUS/SJTU/Huawei Cloud）。
- b. 负载与状态对象：多轮对话（ShareGPT，73% 多轮）；对象是每会话全部历史 KV，存于 host DRAM + SSD 的 AttentionStore（§3.1，Fig. 3/5）。GPU 不跨轮保留 KV，一轮结束即写出。
- c. 下一次使用信息：作业队列内容（已到达、排队中的请求），非到达时刻预测："the job scheduler maintains a job queue, thus having the full knowledge of waiting jobs"（§3.3.1）。可靠性为观测事件；无会话回归时刻估计，唯一时间量是 1 小时 TTL（§4.3.6）。
- d. 逐出粒度与依据：整会话，一个 item 即该会话全部 KV，"the minimal eviction and fetching granularity"（§3.3.2），理由是会话 KV "is either all used or none of it is used"。逐出由 host 空闲阈值触发，按 look-ahead eviction window（长度 (C_mem+C_disk)/S_kv）尾部优先（§3.3.2，Fig. 9）。无部分驻留。
- e. 恢复触发：host→GPU 在该作业执行时逐层流水（§3.2.1，Fig. 6–7）；disk→host 在作业进入队列且落入 look-ahead 窗口（长度 C_mem/S_kv）时预取（§3.3.1）。提前量由队列位置与空闲内存决定，与期限无关。
- f. 相位与期限：无相位控制；无逐次更新期限模型；到达为 Poisson（λ=0.5–2.0 会话/s，§4.1/§4.3.8）。
- g. D1 未处理（无相位概念，§3.3 仅基于队列）。D2 未处理（整会话为最小单位，§3.3.2）。D3 部分解决（仅 disk→host 在排队期预取；host→GPU 仍在执行时，目标是 TTFT 而非期限，§3.3.1/§3.2.1）。D4 部分解决（异步保存："the write stream writes back the KV cache layer by layer while decoding"，§3.2.2，Fig. 8；D2H 不由分配失败触发，但代价是 GPU 不跨轮保留，无容量收益可言）。
- h. 迁移障碍：信息不可得（无周期性或相位信号；低排队场景队列近空，Bidaw §2.1 亦指出此点）；动作域不同（整会话搬运，无"搬多少"旋钮）；基础假设是不规则到达加吞吐/TTFT 目标。
- i. 基线可用性：仅分析参照。代码闭源（Bidaw §5 明言 "CachedAttention and FlashGen are closed-source, we implement ... based on vLLM"）；如需实测须自行复现，模型需相对位置编码以支持其截断（§3.4）。

#### Pensieve（EuroSys'25）

- a. 一手来源：正确标题为 "Stateful Large Language Model Serving with Pensieve"（Yu, Lin, Li，NYU）；arXiv:2312.05516v3（2024-10-07），全文已读；ACM DOI 10.1145/3689031.3696086。
- b. 负载与状态对象：多轮对话；对象是每会话历史 KV-token，两层（GPU KV cache 兼作近期会话缓存 + CPU 内存），可部分丢弃后重算（§1，§3.1，§4.3；Fig. 5 四段布局：dropped / CPU / GPU / new prompt）。
- c. 下一次使用信息：无预测、无到达前预取。唯一启发式为后续请求"usually arrive within a reasonably short time period"（§1）；逐出评分使用最后活跃时间（观测事件）。
- d. 逐出粒度与依据：32 token chunk，"we group KV-tokens into chunks and make eviction decisions at the granularity of chunks"（§4.3.1）；评分 V = Cost(s,l)/T（重算代价除以距上次活跃时间）升序逐出，偏好逐出前导 token（Fig. 4）。支持部分驻留：上下文"might span both tiers of the cache and may be partially dropped"（§1）。触发：GPU 空闲槽 <25% 即开始 GPU→CPU 复制（§4.3.2）；深度由容量压力决定，无链路预算。
- e. 恢复触发：批次组装时，"Before handing off a batch of requests to the worker, the scheduler tries to ensure that any new request's past KV-tokens will reside in the GPU"（§4.3）；随后逐层流水（§4.3.3）。提前量为零。
- f. 相位与期限：无；明言"we aim to optimize throughput instead of latency SLA"（§7）；Poisson 到达加指数思考时间（均值 60 s，§6.1/§6.7）。
- g. D1 未处理。D2 部分解决（chunk 级部分驻留、代价模型决定逐出哪一段；但恢复时缺失部分整体搬回，深度由容量而非链路窗口决定，§4.3.1–4.3.2）。D3 未处理（恢复在批次组装时，§4.3）。D4 部分解决（25% 阈值提前于分配失败；但触发源是容量压力而非空闲，§4.3.2；另有 swap-out 让路 swap-in 的 PCIe 策略，§5）。
- h. 迁移障碍：信息不可得（无周期或相位）；逐出深度目标函数是重算代价而非链路可搬量；吞吐目标假设。
- i. 基线可用性：仅分析参照。自研引擎（约 7K 行 C++/CUDA，非 vLLM，§5）；公开检索未见代码仓库；模型 OPT-13B/66B、Llama2-13B/70B（Table 1）。

#### HCache（EuroSys'25）

- a. 一手来源：arXiv:2410.05004v1（2024-10-07，注 EuroSys 2025），全文已读；EuroSys 2025 accepted list 确认（Gao, Chen, Shu，清华）。
- b. 负载与状态对象：多轮对话（ShareGPT4）与长上下文/RAG（L-Eval）（§2.3）；对象是历史 token 的 hidden states（各层输入激活，体积为 KV 一半），存 SSD（默认）或 host DRAM（§3.1，§4）。GPU 不跨轮保留："we do not cache and reuse KV cache in GPU"（§4）。
- c. 下一次使用信息：无；缓存与预取被归为正交工作，AttentionStore 式预取"orthogonal to our work"（§4）。
- d. 逐出粒度与依据：主实验"The KV cache are evicted when one round of conversation ends"（§6.1.1）；§6.4 长上下文实验加 GPU LRU；无 host/SSD 逐出策略描述。"部分"仅指按层混合（部分层用 hidden state 重建、部分层直接载 KV 或重算），不是部分上下文。
- e. 恢复触发：请求到达时，位于关键路径："When a user request arrives, the inference engine first decides whether the request's history states should be restored"（§4）；"HCache adds an extra restoration phase"（§5）。唯一"预取"在恢复过程内部：前 L_O 层重算时"The hidden states of the latter layers are prefetched"（§4.1.2）。
- f. 相位与期限：无；指标 TTFT/TBT；Poisson 到达，"The interval between conversation rounds in one session is set to 30s"（§6.1.1）。
- g. D1 未处理。D2 部分解决（bubble-free 调度器在层维度求解 min-max，以离线 profile 的 IO_H/IO_KV/C_Token/C_H 平衡 I/O 与算力，§4.1.2 闭式解——这是"搬多少对算多少"的旋钮，但作用于恢复方式而非逐出深度，且按层而非按 token）。D3 未处理（§4，§5）。D4 部分解决（保存在 prefill/decode 中逐层异步，两阶段 host daemon 写 NVMe，§4.2.2；前提同 CachedAttention，GPU 不保留）。
- h. 迁移障碍：动作域不同（优化的是"恢复代价"而非"何时、多深逐出"）；无周期信息；固定 30 s 轮间隔仅为评测设定，机制未加利用。
- i. 基线可用性：仅分析参照。基于 DeepSpeed-MII v0.2.0（5731 行，SPDK + GDRCopy，§5）；未见代码发布声明；模型 Llama2-7B/13B、OPT-30B。

#### Strata（OSDI'26）

- a. 一手来源：arXiv:2508.18572v1（2025-08-26）与 USENIX OSDI'26 PDF（Xie, Xu, Zhao, An, Mailthody, Mahlke, Garland, Kozyrakis；Stanford/NVIDIA 等），全文已读。USENIX 页面无 artifact 徽章或代码链接；正文称"Built on SGLang and deployed in production"。
- b. 负载与状态对象：长上下文、prefill 主导负载（RAG、多轮 agent 对话，§3）；对象是前缀 radix 树上的 KV page（HiRadixTree，默认 1 token/page，§4.1/§5.1），非会话对象；层级 GPU/host/disk。
- c. 下一次使用信息：等待队列中请求对 HiRadixTree 的查找结果（已到达，观测事件）："the scheduler obtains the load and compute requirements of each request using the HiRadixTree"（§4.3.2）；另有 delay-hit 追踪（§4.3.1）。无到达前预测。
- d. 逐出粒度与依据：page；支持部分驻留（Fig. 7 区分 device hit 与 host hit）。"For all memory layers, the Least Recently Used (LRU) algorithm serves as the default eviction policy"（§4.2 末）；逐出量由容量压力决定。Balanced Batch Formation（Algorithm 1）限制批次 load/compute 比 ≤100，是每批加载量的旋钮，不是逐出深度的旋钮（§4.3.2）。
- e. 恢复触发：host→GPU 在批次派发时，"The Scheduler then sends this batch to GPU executor and initiates a KV cache loading request to the Cache Controller"（§4.1），逐层同步覆盖；disk→host 在排队期机会性预取，"opportunistically prefetches data from storage into host memory whenever a cache hit is detected at the storage layer. The prefetch latency is overlapped with the request's queuing delay"（§4.2.1）。提前量等于排队时长，由负载决定。
- f. 相位与期限：无相位控制；无 per-request 期限。§6 Discussion 自认调度器"can still treat requests unevenly, risking Service-level objective (SLO) violations for individual requests"。
- g. D1 未处理。D2 部分解决（page 级部分驻留加批次 load/compute 平衡；逐出仍是 LRU/容量驱动，无链路预算约束的深度）。D3 部分解决（仅 disk→host 与排队重叠；host→GPU 在派发时；§6 把"为慢层预取创造调度余量"列为未来工作）。D4 部分解决（write-through / selective-write-through 在请求完成时异步备份；write-back 仅在临逐出时备份且"can introduce additional runtime blocking"，§4.2 末——论文自认 write-back 模式存在 D4）。
- h. 迁移障碍：信息不可得（无周期性）；目标为聚合吞吐/TTFT；前缀共享假设（delay hit、bundle hit）在单会话独占状态下无效。
- i. 基线可用性：候选实测基线，但需确认代码。论文未给链接；SGLang 开源的 HiCache 是同团队方向的层级缓存实现，但论文将"SGLang-HiCache"列为对照基线（§5.1），二者不等同。引擎 SGLang；模型 Llama-3.1-8B 等（§5.1）。

#### Bidaw（FAST'26）

- a. 一手来源：USENIX FAST'26 PDF（fast26-hu-shipeng.pdf，2026-02，pp. 101–116；Hu, Zhang, Zhou, Wei, Zhong, Chen，清华等），全文已读。未见 arXiv 版本。唯一链接为 trace 仓库 github.com/ShipengHu-777/Interactive-conversation-workload（脚注 1）；系统代码未发布。
- b. 负载与状态对象：交互式多轮对话（百万轮工业 trace，平均 22.4 轮，query 36 / answer 45 token，§2.2）；对象是每用户历史 KV（MHA 模型下改缓存 storage-efficient tensor，§4），两层 host DRAM（performance layer）+ SSD（capacity layer）。
- c. 下一次使用信息：有估计——用上一轮模型回答长度预测下一次访问的 weighted reuse distance 下界（Spearman 0.94–0.98，§3.3.1，Fig. 12），在回答生成完成时产生（§3.1 步骤 3）；结合每用户历史分布与 ghost cache 的命中率（§3.3.3，Eq. 2）。可靠性为估计；只用于逐出选择，不用于预取时机。
- d. 逐出粒度与依据：整用户 KV，"the eviction manager will evict certain users' KVs to the capacity layer"（§3.1）；"The KV with the lowest calculated hit potential is selected for eviction"（§3.3.3）。触发：performance layer 空闲低于阈值（§3.1 步骤 4）；inclusive caching。无部分驻留。
- e. 恢复触发：请求到达，"Upon the arrival of each request, the compute engine captures its KV's I/O status"（§1）；SSD 上的 KV 进 preparing queue，按 disk-HRRN（Eq. 1）发起 SSD→host 读，完成后按原始到达时间插入 ready queue；host→GPU 在调度时（§3.2，Fig. 10）。论文明确否定逐层重叠对慢层有效："the I/O can only be overlapped with the first iteration ... Such a large time gap renders overlapping ineffective"（§3.2）。
- f. 相位与期限：无；指标为平均响应延迟与吞吐；工业 trace 真实时间戳加 ShareGPT Poisson 模拟（§5）。
- g. D1 未处理。D2 未处理（整用户 KV 全量搬运；调度按 KV size 排序不切分）。D3 部分解决（SSD→host 在到达后排队期并行加载；host→GPU 仍在调度点，且放弃逐层重叠）。D4 部分解决（写存储"is not on the critical path"，§2.1；逐出为阈值触发）。
- h. 迁移障碍：核心信号（回答长度→人类阅读时间→回归延迟）在固定周期 `T` 的全双工微轮次下退化为常数，估计价值为零；动作域是 host↔SSD 两层逐出选择，不是 GPU 驻留深度；不规则人类到达是基础假设。
- i. 基线可用性：仅分析参照。系统代码未发布；基于 vLLM 自建（作者亦基于 vLLM 复现 CachedAttention/FlashGen，§5）；模型 OPT-6.7B/13B/30B、Qwen-7B/14B；A800 + 200 GB host + 1.5 GB/s SATA RAID-5。

#### LMCache（arXiv:2510.09665）

- a. 一手来源：arXiv:2510.09665v2（2025-12-05；Liu, Cheng, Yao 等，UChicago 等），全文已读。代码 github.com/LMCache/LMCache（Apache）。
- b. 负载与状态对象：跨查询前缀复用（context caching）与 PD 分离传输（§1，§2.3，Fig. 2）；对象是按 token hash 键控的 KV chunk（默认 256 token，跨层打包，§5.1），非会话对象；层级 CPU/本地盘/远端/Redis/S3。
- c. 下一次使用信息：到达请求的前缀匹配（观测事件）："the scheduler first calls get_num_new_matched_tokens which queries LMCache to see cache hit tokens in the backend"（§6，Table 2）。无到达前预测。
- d. 逐出粒度与依据：chunk；支持部分命中（§4/§6）。逐出算法未命名（全文无 LRU 字样），仅有 batched_admit/batched_evict 上报与 pin/unpin/clear API（§7，Table 3）；容量为配置上限（500 GB，§8.2）。逐出深度决定机制未描述。
- e. 恢复触发：请求到达/调度时，"start_load_kv is called to start loading KV cache of the first layer to GPU memory"（§6），逐层流水（§5.2）。排队期预取："LMCache exploits this idle interval to prefetch the queued queries' KV cache from slower storage tiers into faster ones"（§5.2）；get_num_new_matched_tokens 返回 None 可让请求回队列，"overlapping this request's I/O with other requests' computation"（§6）——与他人重叠，非移出自身关键路径。
- f. 相位与期限：无；无期限模型（仅让用户按"latency SLO and resource constraints"选预取目标层，§5.2）。
- g. D1 未处理。D2 部分解决（chunk 级部分驻留；无逐出量旋钮）。D3 部分解决（排队期跨层预取；仍以到达为起点）。D4 部分解决（Delayed Decode KV Cache Storing 在生成中按 chunk 异步存储，§5.1；Dynamic Offloading 主动把空闲 GPU page 复制到 CPU，§5.3——不依赖分配失败）。
- h. 迁移障碍：信息不可得（无周期性）；目标为吞吐；chunk/hash 抽象无"会话"与"期限"概念；可用 move/pin API 做外部编排但无 prefetch 原语（§7）。
- i. 基线可用性：可作实测基线（vLLM/SGLang connector，开源，模型支持广）。障碍：需自写外部编排器用 move/pin 模拟相位预取；其 CPU offload 路径默认无空闲驱动的部分逐出。

#### Mooncake（FAST'25）

- a. 一手来源：arXiv:2407.00079v4（2025-09-03，题 "Mooncake: A KVCache-centric Disaggregated Architecture for LLM Serving"），全文已读；FAST'25 页面题 "Mooncake: Trading More Storage for Less Computation — A KVCache-centric Architecture for Serving LLM Chatbot"（Best Paper；作者含 Cui、Ren，比 arXiv 多两位）。代码 github.com/kvcache-ai/Mooncake 开源 Transfer Engine、Mooncake Store 与 trace；仓库有 mooncake-conductor 目录但 README 未描述，Conductor 完整性不确定。
- b. 负载与状态对象：Kimi 生产长上下文负载（平均输入 7590 / 输出 182，§4.2）；对象是按前缀 hash 键控的 512-token KVCache block，分布式 CPU DRAM/SSD 池（§3，§4.1，Fig. 3）。
- c. 下一次使用信息：到达请求的前缀匹配（观测事件，Algorithm 1 FindBestPrefixMatch）；§1.1 声称预测"future usage of KVCache blocks"做复制与换出，但 §6.2 承认"it is impossible to accurately predict future usage"，实际为调度时触发的启发式热点迁移。
- d. 逐出粒度与依据：block；部分前缀命中原生支持；逐出策略可插拔，trace 上 LRU 最佳（Table 1，§4.2）；"specialized eviction policies for partial hits and expiration scenarios"为未来工作（§10）；量由 DRAM 容量决定。
- e. 恢复触发：Conductor 调度时（请求到达后），"It loads the prefix cache from remote CPU memory into GPU memory based on the prefix cache block IDs"（§3 Step 1）；逐层重叠："the load and store operations of the KVCache layer are performed layer-by-layer and in parallel with the prefill computation"（Fig. 4 caption）。无到达前预取。
- f. 相位与期限：无相位控制。SLO 为集群级 P90 TTFT/TBT 阈值用于拒绝（Algorithm 1 L27–28），非 per-request 期限；不同优先级/SLO 列为未来工作（§10）。§4.2 无会话轮间隔分析。
- g. D1 未处理（旁证：§7.3 Fig. 10 观察到 prefill/decode 池负载反相振荡，源于预测滞后，是相位现象但未作设计对象）。D2 部分解决（block 级部分命中；调度用 T_transfer 估计权衡本地重算与远端拉取，Algorithm 1——是"拉多少"的路由决策，非逐出深度）。D3 未处理。D4 部分解决（prefill 中逐层异步写回 CPU，§5.2；不依赖分配失败）。
- h. 迁移障碍：目标是过载下的 goodput 与早拒绝；无周期信息；分布式 RDMA 池假设与单机 host-backed 场景不同；动作域为跨节点路由与复制。
- i. 基线可用性：部分可作实测基线——Transfer Engine/Store 可经 vLLM MooncakeStoreConnector 或 SGLang HiCache 后端接入；Conductor 调度逻辑不确定可复现。

### 2.2 提前信号与预取

#### SYMPHONY（NSDI'26）

- a. 一手来源：USENIX NSDI '26 camera-ready，"SYMPHONY: Enabling Compute-Memory Disaggregation in LLM Serving Systems"（Agarwal, Hu, Mao, Akella, Venkataraman），全文已读。arXiv:2412.16434v1（2024-12-21，唯一版本）题名不同（"Improving Memory Management for LLM Inference Workloads"）且作者列表不同；引用 NSDI'26 时不应沿用预印本题名。
- b. 负载与状态对象：多轮 chatbot（ShareGPT、BurstGPT）与多 agent 流水线（MetaGPT）；对象是整会话 KV，在"unpredictable gaps between requests"（§1）间持久化于 GPU / host / disk / remote disk / blob 五层（§3.3）。
- c. 下一次使用信息：应用发出的 advisory request（§3.1）。chatbot 场景由前端在用户开始输入时触发（§3.1，Fig. 10）；agent 场景由离线 profile 的调用图对所有 next-hop agent 发出（§3.1，Fig. 8）。实测提前量 ShareGPT 派生 11.3 s、MetaGPT 5.8 s（§1）。hint 格式含 `expected_arrival: None, ordered: False`（Fig. 7），论文明示 hint "provide no guarantees about the timing of its arrival or its order relative to other ongoing sessions"，且"convey no information about memory requirements"（§3.2）。可靠性属估计：60% 假 advisory 造成 2.1% 吞吐损失（Fig. 20）；10% 漏 advisory 使 TPOT 由 21.3 ms 升至 24.4 ms（Fig. 19）。
- d. 逐出粒度与依据：按层 KV 块，在 vLLM block manager 内实现（§4.1）。压力下"remove the last layer of KV cache associated with the least recently used request"（§3.4）；逐出量由 serving 框架按需 purge 决定（cooperative memory management，§3.4），可无代价丢弃是因为最慢层始终持有完整副本，由后台线程持续写入（§3.4）。即 GPU 驻留可按层部分保留，但深度由分配压力与 LRU 决定，无链路时间或期限模型。
- e. 恢复触发：advisory 到达即贪心"moves it to the fastest memory tier possible"（§3.3）；提前量由用户或 agent 行为给出，系统不计算所需提前量。到达时未全驻留则回退到逐层异步读（§3.4 Cases 2–3）。`expected_arrival` 字段存在但未描述任何消费它的算法。
- f. 相位与期限：无 per-request 期限模型，指标为 TPOT/TTFT/req/s（§4）。多会话竞争仅启发式处理：两个 advisory 并发时"places lower-layer caches from both sessions in HBM first, deferring higher layers"（§3.4）；论文明言跨会话次序不可知（§3.2）。
- g. D1 未处理：评估使用随机错开的人类思考时间（§4 Trace Generation），不控制也不利用释放相位。D2 部分解决：按层优先级提供部分驻留旋钮（§3.4），但深度由压力/LRU 决定而非链路可搬运量；写回最慢层是持续的全量写，链路写需求仍随生成 token 总量增长。D3 部分解决：hint 足够早时恢复移出关键路径，但论文自陈"SYMPHONY assumes that advisory requests arrive early enough"（§3.6 Limitations），否则回退逐层按需读（Fig. 17：关闭逐层加载在重负载下损失约 18.4% 吞吐，§4.5）。D4 部分解决：写回慢层持续且非压力驱动（§3.4），但从 GPU 移除仅在框架需要时发生，GPU 侧逐出仍为压力触发；trace 生成器假设"evicts the key–value cache immediately after request completion"（§4 Trace Generation）是断言而非机制。
- h. 迁移障碍：信息域不同——hint 是外部发出的、时刻与次序未知的二元"即将到来"信号（§3.2），周期负载中下一释放时刻是调度器预先已知的量，advisory 机制冗余而其启发式（贪心填充、按层 LRU purge）忽略期限结构；动作域亦不同——目标是跨节点负载均衡（Fig. 1，Fig. 15），非单卡容量复用。
- i. 基线可用性：仅分析参照。全文未见代码链接或 artifact 声明；实现约 2400 行 Python 与 gRPC，挂接 vLLM scheduler（§4.1）；模型 LLaMA-3.1-8B、LLaMA-2-13B（§4）。注意内部不一致：Fig. 11 标题写 4 倍用户（64 vs 256），§4.2 正文写"up to 8×"（64 vs 512），摘要写 4 倍。

#### InferCept（ICML'24）

- a. 一手来源：arXiv:2402.01869v2（2024-05-30），HTML 与 PDF 全文已读；ICML 2024，PMLR 235:81–95。代码 https://github.com/WukLab/InferCept（§1）。
- b. 负载与状态对象：augmented LLM 在 interception（工具/API/人类/环境调用）处暂停解码；Table 1 六类，平均暂停时长自 0.2 ms（Math）至数十秒（Chatbot，按阅读加输入时间估计，§2.2）。对象是暂停请求持有的 KV 上下文："the context (i.e., KV caches) cannot be used for a paused request during interceptions but will be needed upon the end"（§1）。chatbot 轮次被建模为一次 interception，是六类中最接近会话暂停的形态。
- c. 下一次使用信息：暂停时长估计（§4.4）T̂_INT = t_now − t_call，每迭代重算，不按类型 profile。可靠性："achieves 93% of the performance compared with using an oracle providing exact interception durations"（§4.4）。代价模型 §3.2 Eqs. 1–3 与 §4.2 Eq. 4：WastePreserve = T_INT·C·M，WasteSwap = 2·T_swap(C)·C_batch·M 等。swap 预算（§4.1）：迭代 i 令 T_swap(N_i) = T_fwd(B_i) 求 N_i，即"the number of tokens that can be swapped for free (i.e., hidden behind model forwarding)"；预算在换出与换入之间按三条约束分配。
- d. 逐出粒度与依据：token 分块、按层流水线："chunk swap-out and swap-in across multiple iterations so that in each iteration, the swap latency can be hidden"（§4.1）。每迭代换出量为 N_i，即链路在一次 forward 内可搬运的量；请求按 waste 排序换出"until we run out of the swap-out budget"，其余按 Eq. 5 保留或丢弃（§4.3；Appendix）。这是六个系统中唯一以链路时间约束部分逐出深度的系统。
- e. 恢复触发：interception 返回时反应式触发："When an API call finishes, InferCept determines how many swapped-out or discarded tokens to swap in or recompute in the next iteration"（Appendix）；换入队列 FCFS 至预算耗尽（§4.3）。T̂_INT 不用于提前换入，提前量按设计为零。
- f. 相位与期限：多请求耦合仅通过 C_other / C_batch 停顿项与共享预算（§3.2，§4.3）；无期限或 SLO 模型，目标为 normalized latency 与 req/s（§5.1）；无会话相位概念。
- g. D1 未处理：容量收益依赖 interception 时长的不规则与分散，无相位控制。D2 粒度上解决、规模上部分解决：分块 swap 给出以 T_fwd(B_i) 为界的"换多少"旋钮（§4.1），但每 token 代价模型仍假设每次暂停整上下文往返（Eq. 3 的因子 2），总链路需求仍随暂停请求数乘上下文增长，只是被限速。D3 未处理：换入仅在返回后开始（Appendix），预算只是把它藏在其他请求的 forward 之后，不是在本请求期限之前。D4 已解决：换出由暂停事件触发，"At the end of each iteration, the scheduler gathers all requests that trigger API calls ... swaps as much context ... as allowed"（Appendix），与分配失败无关；压力逐出的请求另属独立等待队列（§4.3）。
- h. 迁移障碍：根本假设不成立——interception 时长未知且不规则，故需流逝时间估计器与最小 waste 选择；周期 `T` 已知时估计器失去意义，Preserve/Discard/Swap 退化为确定性决策。目标为吞吐（waste 以 GB·min 计），无理由按期限排序换入。
- i. 基线可用性：可作实测基线候选。代码公开、基于 vLLM，模型 GPT-J-6B、Vicuna-13B、Llama-3-70B 于 A100（§5）。障碍：2024 年代的 vLLM fork；chatbot interception 模型已近似多轮会话，可构造"每 T 暂停一次"驱动器，但六类混合数据集与 FCFS 调度固化在评估 harness 中。

#### KVFlow（NeurIPS'25）

- a. 一手来源：arXiv:2507.07400v1（2025-07-10，唯一版本），HTML 与 PDF 全文已读；NeurIPS 2025 Main Track（DOI 10.52202/085713-4208）。代码 https://github.com/PanZaifeng/KVFlow（Apache-2.0，论文未链接，为 SGLang fork）。
- b. 负载与状态对象：SGLang 上的多 agent 工作流；对象是 radix tree 中各 agent 固定 prompt 的前缀 KV，CPU 内存作为"secondary cache for storing the fixed prompt KV of evicted agents"（§3.2）；动态后缀总是先被逐出（§3.1）。保护的是跨调用复用的静态前缀，不是会话历史。
- c. 下一次使用信息：Agent Step Graph 上的 steps-to-execution（§3.1，Fig. 3a），join 取 max+1，either-branch 取 min+1，只追踪"the earliest possible execution step"。由前端在每次 LLM 调用时以 HTTP 元数据嵌入（§3.3）。可靠性：由结构预先确定（图已知），但到执行的时间未估计；分支通过在并发预取数上限内预取所有候选处理（§3.2）。
- d. 逐出粒度与依据：radix tree 节点级；agent 的 step 值赋给其固定 prompt 末节点并向上传播，共享节点取"the minimum (i.e., least evictable) priority among its children"（§3.1，Fig. 3b）；顺序为后缀先、再按优先级降序。触发与量："When GPU memory becomes constrained"（§3.1），即容量压力，无水位或链路时间约束。
- e. 恢复触发：携带 step 元数据的请求到达触发下一步 agent 的预取，条件是"if the evictable GPU memory is large enough"（§3.3）。提前量隐含为一个 agent 的执行时长；论文承认"When the current agent's execution time is shorter than the prefetch duration, generation may still be blocked"（§3.2），以 status-aware 重排（Fig. 4）缓解，而非更早预取。
- f. 相位与期限：多工作流重叠仅通过共享节点取最小优先级与 per-client ID 处理（§3.1，§3.3）；无期限模型，以整工作流延迟评估（§4）；并发过高时"the system can no longer maintain reusable prefix caches, placing it beyond the scope of our optimization"（§4.2）。
- g. D1 未处理：并发被视为带宽竞争（§3.2），不视为相位对齐。D2 部分解决：节点级逐出天然部分，但深度由压力驱动，无链路容量约束；论文自报 PCIe 链路因 SGLang 碎片化布局而利用不足，KVFlow"does not resolve"（§4.2）。D3 部分解决：预取提前一步（§3.2），但提前量不可控，status-aware 调度是提前量不足的补救，不是按期限排序的恢复。D4 未处理：CPU offload 是内存压力下的逐出（§3.1–3.2）；异步备份属基线 HiCache 的行为。
- h. 迁移障碍：状态对象不匹配——KVFlow 保护字节不变的静态共享前缀，周期会话的历史每周期增长且不共享；steps 是序数（图距离）而非时刻，固定周期下"提前一步"恰为一个 `T`，该度量不携带额外信息；无逐出深度选择机制。
- i. 基线可用性：需适配后可实测。代码公开但为 SGLang fork（论文称 v0.4.4，§3.3），模型 Llama-3.1-8B（A10G）、Qwen2.5-32B（H100）（§4.1）；前端元数据路径假设 `sgl.function` 定义的 agent，周期会话驱动器需合成该 HTTP 元数据；未报告独立的逐出对预取消融。

#### InfiniGen（OSDI'24）

- a. 一手来源：arXiv:2406.19707v1（2024-06-28，唯一版本，注 OSDI 2024），HTML 与 PDF 全文已读。代码 https://github.com/snu-comparch/InfiniGen。
- b. 负载与状态对象：基于 offloading 的长上下文生成（FlexGen、UVM 基线），单请求或小批（4–20，§5.3）。对象是单请求按层 KV，整体置于 CPU："the majority of the tokens for the KV cache are kept in the CPU memory"（§4.1），"we explicitly locate all the KV cache in the CPU memory"（§5.1）；GPU 仅持预取子集与部分 query 权重、部分 key cache（§4.3）。
- c. 下一次使用信息：forward 内部的观测事件——"At Layer i−1 of the decoding stage, InfiniGen speculates"第 i 层的重要 token（§1，§4.3，Fig. 8）。提前量固定为一个 Transformer 层。非无损：SVD skewing 精确（§4.2），但 token 选择为阈值近似 top-k（§4.3），未选 token 该步不被 attend（"ephemeral pruning"，§1），无 miss 路径。
- d. 逐出粒度与依据：token 级、按层按 head 组每步选择；量由 alpha 决定（OPT 4、Llama-2 5），平均"less than 10% of the KV cache"，上限 20%（§5.1）；CPU 池容量用户设定，victim 策略基于计数器（§4.4，Table 2）。
- e. 恢复触发：每个 decode step 于 i−1 层由 KV Selection Controller 触发（Fig. 6）；提前量由模型结构固定，调度器不可调。
- f. 相位与期限：无。批内各请求独立 KV 池，无会话复用、无 SLO（§5，§7）。
- g. D1 未处理（单请求或批 decode，无请求间相位）。D2 另一意义上的部分解决：驻留部分且很小（<10%），但深度由注意力分数阈值决定而非链路容量；完整 KV 从不回到 GPU。D3 在其范围内解决：恢复是与计算重叠的按层预取（§4.3，Fig. 3d），但无"请求到达"概念，且有损选择不重建状态。D4 不适用：KV 生成即写 CPU（§4.1），无空闲期概念。
- h. 迁移障碍：根本假设不成立——InfiniGen 是 offloading 下对稠密注意力的有损近似，周期负载要求每次更新对保留历史做完整注意力；其提前信号（层间相似性）与会话级释放时刻正交。
- i. 基线可用性：仅分析参照。基于 FlexGen（§5.1），OPT 与 Llama-2，RTX A6000 PCIe 3.0；非 serving 系统（ECHO Table 1 亦标注其无 serving 框架、无 continuous batching）。

#### ECHO（OSDI'26）

- a. 一手来源：USENIX OSDI '26 camera-ready，"ECHO: Efficient KV Cache Offloading with Lossless Prefetching for Serving Native Sparse Attention LLMs"（Liu, Chen, Li, Ning 等，SJTU/Huawei），pp. 17–37，全文已读。代码 https://github.com/sjtu-zhao-lab/ECHO（§1），Zenodo artifact（Appendix A）。
- b. 负载与状态对象：DeepSeek-V3.2 与 DeepSeek Sparse Attention 的长上下文 serving（InfiniteBench 80K–100K token；ShareGPT 测延迟，§2.2，§6.1）。对象是活跃请求的 MLA KV，"in both the host and GPU pools, where the GPU pool serves as a cache for selected tokens"（§3）；indexer K cache 留在 GPU；GPU 池按层管理（§4.1）；host 池 1.8M token 约 1000 GB（§6.1）。
- c. 下一次使用信息：模型内部观测——indexer 的 top-k 选择。decode（intra-query prefetching，§5.1）以 EMA 预测第 k 高分阈值（α = 0.5，Fig. 7），在 indexer kernel 计算分数期间预取超阈值 token；indexer 完成后"a guaranteed recall is launched for the selected tokens that are not yet in the GPU pool"（§3），因而无损。提前量为同层同步的 indexer kernel 时长，上下文近 100K 且命中率达 90% 时二者可重叠（§2.4，Fig. 4）。prefill 为 inter-query prefetching（§5.2）。
- d. 逐出粒度与依据：token 级 GPU 池槽位、按层；逐出只改元数据，因"the KV cache of all tokens has already been backed up to the host pool during generation"（§4.2 Free）；优先级计数器形成"LRU-like eviction policy"（§4.2）；量由固定 GPU 池大小与当前选择决定，即容量压力。实测按层命中率 0.88–0.99（Fig. 17）。
- e. 恢复触发：作为 attention 一部分的按层按步 recall，无请求到达概念；PD 分离部署下 decode 实例先把 prefill KV 收入 host，再"launches decoding to prefetch and recall KV cache of selected tokens"（§3）。
- f. 相位与期限：无。吞吐导向，自陈 offloading "is most beneficial for throughput-oriented long-context serving"，ITL 开销 +2.7% 至 +27.8%（§6.3，§7）。
- g. D1 未处理：并发收益来自稀疏选择的工作集，非会话时序错开。D2 另一机制的部分解决：按 token 部分驻留且有池大小旋钮，每步链路需求以每请求 k 为界而非上下文长度，但该界是 DSA 的性质而非调度决策。D3 部分解决：预取与 indexer 重叠，但恢复仍在步内关键路径，仅在 indexer 时长超过 recall 时被隐藏（Fig. 4，Fig. 18）。D4 按设计解决：host 备份在生成中完成（"KV offload writes one newly generated token per active request"，§6.3），GPU 逐出只改元数据，分配路径上不需要 D2H。
- h. 迁移障碍：两重根本假设不成立——需要原生稀疏注意力模型提供 indexer 选择信号；目标是长单请求上下文的吞吐。稠密注意力的双工会话无 indexer 可预取，按步 recall 将每次更新搬运整段历史。可迁移的只有"始终备份的主机副本"这一思想，与 SYMPHONY 共享。
- i. 基线可用性：仅分析参照。代码公开且经 artifact 评估，但需 DeepSeek-V3.2（AWQ）于 8×H20、1.5 TB DRAM、SGLang v0.5.4 + DeepGEMM（§4.3，§6.1，Appendix A），不可移植到小型稠密模型。

#### Learned Prefix Caching（NeurIPS'25）

- a. 一手来源：NeurIPS 2025 Main Track，"Learned Prefix Caching for Efficient LLM Inference"（Yang, Li, Li, Lloyd，Princeton），papers.nips.cc PDF 全文已读。代码 https://github.com/yangdsh/LPC（§1）。OpenReview 页面因人机验证未能打开，不影响论文内容。
- b. 负载与状态对象：vLLM 上的多轮 chat（LMSys、ShareGPT、Chatbot-Arena，§4.2）；对象是 GPU 内存中已完成会话的前缀 KV 块："The prefix cache has limited capacity as it uses precious GPU memory"（§2）。单层：全文未描述 CPU/host 副本，逐出即丢弃后重算。数据集平均输入 36–113 token、输出 155–305 token（Table 1），上下文很短。
- c. 下一次使用信息：学习到的会话是否继续的估计。预测器（§3.2）解析当前与前 N=4 条用户 prompt，multilingual-e5-small 嵌入 384 维，拼接轮数，3 层 MLP 输出继续概率 p；每请求运行一次，按数据集离线训练（§3.3）。时间以衰减折入：p_cur = p·decay / (p·decay + 1 − p)，decay = exp(−(t_cur − t_last)·scale)，scale = 1/平均轮间隔（约 100 s），每 10 s 重估（§3.4.2）。只逐出、不预取："LPC uses a predictor to inform the replacement algorithm about which blocks to evict"（§3.1）。
- d. 逐出粒度与依据：约 16 token 的 KV 块，按衰减后 p 组成最小堆，"When the prefix cache reaches its capacity, or when memory needs to be reclaimed (e.g., due to expansion of the KV cache)"逐出堆顶（§3.4.1）；量纯由容量压力决定；同一会话所有块共享一个 p，实际按整会话逐出；共享块取 max-pooled 概率（§3.5）。
- e. 恢复触发：无。miss 时下一请求重新 prefill（§2），无下层可恢复。
- f. 相位与期限：无。到达模型为指数思考时间、并发会话上限 200（§4.2）；无期限；指标为命中率、TTFT、prefill 吞吐（§4.1）。
- g. D1 未处理（单 GPU 层，无 offload）。D2 未处理（无 swap，"旋钮"只是丢弃哪个会话）。D3 未处理（恢复即到达时重算，Fig. 7 量化 miss 的 TTFT 代价至 73%）。D4 未处理（逐出由容量或 KV 扩张触发，§3.4.1）。
- h. 迁移障碍：信息域与动作域均不同——LPC 预测会话是否回归，周期负载中这是确定事实；唯一动作是丢弃。按流逝时间衰减是周期调度器已知量（到下次使用的时间）的反面，可迁移的只有"conversational 负载下 recency 是差代理"的观察（§2）。
- i. 基线可用性：仅分析参照。代码公开，vLLM main（2025-03-10，§4.1），Qwen3-32B-FP8 单 H100；吞吐/延迟结果来自 prefill-only 仿真与合成 1000 token 上下文（§4.5），作者自列"synthetic timestamps"与"comparison primarily against LRU"为限制（§6）。

### 2.3 恢复与重算混合

#### Cake（ICML'25）

- a. 一手来源：arXiv:2410.03065v2（2025-02-20；v1 2024-10-04），HTML 全文已读。正确题名为 "Compute Or Load KV Cache? Why Not Both?"（Jin, Liu, Zhang, Mao，U. Michigan）；PMLR 确认 ICML 2025，vol. 267，pp. 28031–28043。早期匿名 OpenReview 提交（cK0kUzocJW）的 venue 页面因人机验证未能打开。
- b. 负载与状态对象：多轮 chat 与 RAG 的长上下文前缀缓存（§1）；对象是预计算的前缀 KV，存于"high-capacity, low-bandwidth storage layers, such as local disks and remote storage"（§4，Fig. 1）。评估预先计算并存储全部请求的 KV（§5.1），I/O 以按 chunk 与带宽延迟模拟（7/25/32/56/100 Gbps，§5.1，Table 2）。
- c. 下一次使用信息：无。加载"upon receiving a request"开始（§4 Part 2；App. A 步骤 1）。
- d. 逐出粒度与依据：不处理。Fig. 1 标题："Cake operates during the KV cache loading phase"；写回交给 LMCache 的异步 put（App. B.1）。
- e. 恢复触发：请求到达。分割点运行时发现而非预测：compute 指针自 chunk 0 向前 prefill，I/O 线程自末端向后加载，compute 线程以 `IsInCPUMemory` 检查下一 chunk，相遇即停止 I/O worker（§4 Part 2，Fig. 2，Alg. 1 第 3–5 行）；compute chunk 512 token、I/O chunk 128（§5.1）。§5.3 把"an estimation mechanism"与单资源回退列为未来工作，证实无模型化分割。并发：扩展 vLLM token-budget chunked prefill，优先级 decode > non-prefix prefill > prefix-cache prefill（§4 Part 3）；无期限或 SLO，指标为 TTFT（§5.1）。
- f. 相位与期限：无。唯一并发实验为一个 16K 前缀请求加 22 个突发请求（§5.7，Fig. 6）。
- g. D1 未处理（无容量管理，KV 假定已在 GPU 外，§5.1）。D2 部分解决（每请求 compute/load 分割给出跨链路字节的运行时旋钮，但恢复仍是每请求整前缀，无跨会话链路预算，§4 Part 2）。D3 未处理（按构造在 TTFT 关键路径，§4）。D4 未处理（无 D2H 路径）。
- h. 迁移障碍：无逐出侧、无时间模型、无期限。双向技巧仅在前缀重算相对加载耗时较长时收益（§4 Part 2，Fig. 4）；本文负载每次更新短、历史即全部状态，compute 指针须重新 prefill 已算过的历史。前缀 hash 寻址（App. A 步骤 2）假设不变前缀。
- i. 基线可用性：仅分析参照。无代码发布（唯一 GitHub 链接是 LMCache 本身；antgroup/cakekv 是另一个同名 "CAKE"）。基于 LMCache v0.1.4 + vLLM v0.6.2 chunked-prefill，约 1000 行（App. B）；模型 LongAlpaca-7B/13B、LLaMA 3.1-8B/70B FP8；2×A100 80GB 与 1×H100（§5.1，Table 1）。

#### CacheFlow（arXiv:2604.25080）

- a. 一手来源：arXiv:2604.25080v1（2026-04-28，唯一版本，cs.DC，"11 pages, 10 figures"，无 venue），HTML 全文已读。题 "CacheFlow: Efficient LLM Serving with 3D-Parallel KV Cache Restoration"（Nian, Fang, Feng, Wu, Lai）。
- b. 负载与状态对象：长上下文多轮 chat、RAG、agentic 流水线（Abstract，§1）；trace 为 LMSYS-Chat、WildChat、SWE-Bench（§4.1）。对象是请求的缓存前缀（N_c token），位于"CPU memory, SSD, or remote nodes"（§1，§2）；pipeline-parallel 下各 GPU 另存"boundary hidden states"（§3.2）。层级仅以 I/O 带宽 10/40/80 Gbps 表达（§4.1，§4.3，Fig. 7）。
- c. 下一次使用信息：无。Alg. 1 只依赖当前 pending batch、各请求 N_c、离线阈值 L_Δ 与指针状态。§5 对比 Continuum（复用预测）与 KVFlow（预取）但均未采用。
- d. 逐出粒度与依据：不处理，仅恢复。§2 把"offload KV cache to lower tiers ... or discard and recompute"作为背景。
- e. 恢复触发：请求到达（"given a request with a cached prefix of N_c tokens"，§3）。token 维双指针（chunk C 对齐 FlashAttention block，约 512）与 layer 维双指针（cutover layer ℓ），按离线 profile 的阈值 L_Δ 切换（§3.1，Fig. 3，Alg. 1 第 3 行）；解析界 T* = T_comp·T_io/(T_comp+T_io)，S 级流水线除以 S（§3.2，Eq. 1–2）。batch-aware 调度器：每步 I/O 分给"in descending order of their length to restore"的请求（最大剩余重算代价，Alg. 1 第 7 行，§3.3），compute 推进所有请求（第 11 行）。无期限或 SLO；TTFT 为目标（§4.1）；约 200 ms 仅作动机（§2）。
- f. 相位与期限：感知的是并发恢复对共享算力与 I/O 的竞争，非到达相位；无 per-request 期限。
- g. D1 未处理。D2 部分解决（混合重算/加载减少每请求字节、I/O 在 batch 内仲裁，但每请求仍恢复整前缀，优先级按重算节省而非链路时间预算，§3.3）。D3 未处理（按设计在 TTFT 路径）。D4 未处理（无 offload 侧）。
- h. 迁移障碍：与 Cake 同类——无逐出、无时间、无期限；优先长前缀的排序在期限驱动的周期负载中并非正确顺序。
- i. 基线可用性：仅分析参照。无代码发布（唯一 GitHub 链接为 vLLM）。基于 vLLM（版本未述）+ LMCache（v0.3.1 为基线）（§4.1）；模型 Qwen3-8B、Llama-3.1-8B、Qwen3-30B-A3B；L40S 46GB、A100 40GB、H100 80GB（§4.1）。无 Discussion/Limitations 节。

### 2.4 双工与实时语音 serving

#### Metronome（arXiv:2607.02640）

- a. 一手来源：arXiv:2607.02640v1（2026-07-02，Meng, Li），HTML 全文含 Appendix A–D 已读；另核对公开仓库 github.com/19PINE-AI/metronome（README、gateway-go/main.go、metronome/session.py、scheduler.py、kv_manager.py）。
- b. 负载与状态对象：全双工"real-time interaction models"（Qwen3-Omni-30B-A3B FP8、Qwen2.5-Omni-7B、MiniCPM-o-4.5、Moshi）作为周期实时任务；每会话持续增长的 KV 整段 pinned。§2 "The task model"："A session presents a new audio chunk once per frame; we take the frame period equal to the frame budget B"；可调度条件"iff the per-frame wall time satisfies T_k(N) ≤ B for every k"。
- c. 下一次使用信息：不需要也不使用——每会话每帧均到期（§2："An interaction session has no lull: every session is due on every frame"）。主机 offload：无。§2 "Recompute, swap, or stay resident"：swap 是"a bandwidth toll that likewise grows"，每帧换出所有到期会话"would move tens of gigabytes per second within minutes"，结论"residency is the only budget-compatible choice"。§8：vLLM/FlexGen 的"state-movement machinery — reclamation, swapping, offload ... — presumes idle gaps that a periodic session never has"。跨周期的 per-session 调度：无。§4：Go gateway "once per tick issues a single batched Step over gRPC for all due sessions"；Fig. 2 "one tick = one batch of all due sessions"；Fig. 3 "with no idle gap, for the whole conversation"。释放偏移或错开：仅作为负载性质出现——§3 "N distinct, phase-staggered real-audio streams"，§5.1 "each session is a distinct, phase-staggered stream, so prefix-cache deduplication cannot inflate capacity"；无处表明服务端利用该偏移。仓库核对：gateway-go/main.go 为单一全局 ticker（`--period-ms`，周期等于预算），每 tick 一次 `client.Step`，phase/offset/stagger/jitter 均不出现。附带说明：仓库早期 Python 原型 metronome/session.py 的 `PeriodicSession` 有 `phase_s`（"wall-clock phase offset within the period"）字段与 EDF `TickScheduler`，但调度器消费外部给定的 `due` 列表、无错开逻辑，README 标其为"earlier synthetic-cost study, superseded by the real end-to-end evaluation"，不属论文实测路径。
- d. 逐出粒度与依据：整块落在固定滑动窗口 W 之后的 KV block（W=1024 工作点，W=2048 等价，W=512 过小，§5.4，Fig. 11），加 S 个 pinned sink token（S=16 最佳）。Appendix A："The KV manager then frees blocks that fall entirely behind the window, which is what bounds resident memory"；`sliding_window=W` 在模型构造时设定。量由静态 W 决定，非压力或链路预算；有损，§5.4 "Recall beyond the horizon is impossible under any fixed bound"。
- e. 恢复触发：无（从未换出，被丢弃 token 不可恢复）。应用级"recycling"基线在窗口边界重编码（§4.1，§5.2，Fig. 10），属重算而非恢复。
- f. 相位与期限：不感知相位——设计前提是所有会话每 tick 同时到期（ρ(t)=ρ0+Nrt 模型的前提，§3.1）。期限模型：每帧预算 B，周期等于 B；deadline-miss 计数器存在，但 §3 指出 worker 对 tick 等待封顶 0.8B 后返回空帧，崩塌期间"the deadline-miss counter reads zero"。接纳：AIMD 按每帧延迟对 B 的目标比例调节（§4.2；Fig. 7 中 2 s 预算取 600 ms 目标；仓库默认 0.7·B，乘性降 ×0.9，加性升 +1）；不驱逐已接纳会话（§5.3："shedding late cannot rescue sessions that are already resident"）。
- g. D1 未处理：把同时活跃视为给定（§2 引文），以约束状态代替利用偏移。D2 未处理：正因链路需求随 N 增长而拒绝整段 swap（§2 引文），除有损截断外无部分旋钮。D3 未处理：无恢复路径。D4 未处理：唯一压力响应是 vLLM 分配失败时的 preemption，Fig. 5 显示为"a hard stall that never recovers under open-loop audio"，Metronome 以不触及压力回避之。
- h. 迁移障碍：状态界有损（丢弃历史），本文负载保留历史；无周期内空闲的概念，无法承载 offload/prefetch；tick 模型假设同时释放，相位指派按构造缺席。§8 "presumes idle gaps that a periodic session never has"是对本文前提的直接否定，须在正文中以本文的 KV 空闲区间定义（q(i,k) 到 s(i,k+1)）回应，而不是以帧间无对话停顿回应。
- i. 基线可用性：可作实测基线（Apache-2.0；vLLM 0.23 patch 含 Blackwell omni 初始化修复与经 `SlidingWindowSpec` 的窗口化 KV；Go gateway + Python gRPC worker；单卡 RTX PRO 6000 Blackwell）。障碍：实测路径绑定 vLLM 0.23 与 Blackwell 修复集（Appendix B）；sink mask 仅在 Triton kernel 路径存在，serving 实验用"the window half alone on the FlashAttention path"（§7）；turn-taking 与 barge-in "are out of scope by design"（§7）。它是本文"保留并分级驻留"路线对面的"约束状态"路线的直接代表。

#### LiveServe（arXiv:2606.22983）

- a. 一手来源：arXiv:2606.22983v1（2026-06-22；Zhi, Yin, Guan, Zheng, Cheng, Yan），HTML 全文与 PDF 文本已读。注：§3 标题字面为"OmniCast Architecture"（遗留名，正文称 LiveServe）。
- b. 负载与状态对象：半双工、按 turn 的多轮语音/omni 会话含 barge-in，Qwen3-Omni 与 Ming-Flash-Omni 2.0（§7.1；8×H200）。对象是跨 turn 的每会话多轮 KV（"idle-resident multi-turn KV"），跨 HBM 与 DRAM 管理（Fig. 9）。trace 记录含"session ID, a request timestamp, query and response token lengths, and a turn index"（§7.1）；到达 Poisson 或 BurstGPT，barge-in 为 Bernoulli。全文不出现 full-duplex、per-frame、periodic，未引 Moshi。
- c. 下一次使用信息（§5.1 "Next-use estimate"，Eq. 4）：T_next,i = T_play,i + T_reply,i，T_play 为剩余播放时长，T_reply "estimates the interval from playback completion to the next completed user input using a per-session moving average when available and a workload-level prior otherwise"。可靠性为估计，且"used only to order eviction candidates, so it need not be an exact wall-clock prediction"；speech start 或 barge-in 时"treats the session as immediate reuse and protects its resident KV from normal eviction"。先验数值未给出。预取触发（§5.2）："LiveServe starts preload at speech start or barge-in, before the full user input reaches the model"；§3：VAD 检测用户开始新话语。接纳条件（§5.2，散文无不等式）："admits an asynchronous DRAM-to-HBM transfer only when the remaining time before LLM-stage execution is enough to hide the transfer cost under current pressure"；"remaining time"如何估计未说明；失败时"skips the preload and lets the normal LLM-stage path load missing KV"。逐出顺序（§5.1）：按 T_next 降序从最远者扫描；会话内"gives suffix blocks higher eviction priority than prefix blocks"（后缀先于前缀，理由是前缀被更多后续 turn 共享）。
- d. 逐出粒度与依据：block 级、按会话排序，"evicts blocks from that session until enough HBM is released or the session has no evictable blocks left"再转下一会话。量由当前需要释放的 HBM 决定，非链路或窗口预算；触发是压力而非空闲："When HBM pressure requires freeing KV capacity, the KV manager considers only idle-resident multi-turn KV"（§5.1）；§6 保留"the original LRU allocator as a fallback on every allocation"。
- e. 恢复触发：speech onset / barge-in 事件（§5.2），早于请求到达；提前量由对 LLM-stage 执行前剩余时间的接纳检查决定；预取为"best-effort background work rather than foreground work"，可取消（§6），受保护 KV 总量有上限。恢复量未分级，以"the session KV"为单位，无部分或前缀优先预取。结果（§7.3，Fig. 16 右）："The offloading baseline spends 71.0 ms on on-path KV reload and reaches 302.1 ms text TTFP"，LiveServe "reduces text TTFP to 127.8 ms, a 57.7% reduction"（单个 warm-hit 请求，无聚合隐藏比例）。
- f. 相位与期限：不控制相位。调度为逐轮严格类优先 U0（underrun，P_i ≤ P_safe，按缓冲升序）> U1（首音，最老优先）> U2（效用 U = β·U_kv − α·C_barge，Eq. 1–3，Algorithm 1）；无 per-request 期限模型，U 是"a lightweight ordering heuristic rather than a global optimum or an exact knapsack solution"；"KV-pressure-aware deferral"（Fig. 8/17）是 Eq. 3 U_kv = K_i·R_occ 偏向驻留大 KV 请求先完成以释放 HBM，非对到达会话的接纳门。HTML 与 PDF 文本均无 stagger/phase/release offset 的调度意义用法。
- g. D1 未处理：turn 间隔是外生用户行为，无机制塑造会话何时重合。D2 部分解决：逐出按 block、后缀先、量按需求（§5.1），但恢复整会话且量不与链路容量关联。D3 部分解决：预取在可隐藏时把恢复移出到达路径（§5.2，Fig. 16），但依赖足够早的 speech-onset 事件，否则回退在路加载。D4 未处理：逐出仅在分配时的 HBM 压力下运行（§5.1 引文），非会话空闲触发，D2H 仍可能与前台工作重合。
- h. 迁移障碍：next-use 信号是播放加人类 turn 间隔的估计，本文负载有预先给定的释放时刻；触发是用户语音事件，固定 micro-turn 节奏中不存在；逐出反应式；预取无部分深度旋钮、无跨会话期限排序；负载是半双工按 turn 而非周期。
- i. 基线可用性：当前仅分析参照。论文无代码或 artifact 声明（查 §6、§9、脚注与参考文献；作者页仅 arXiv 链接）。引擎"built on top of vLLM-Omni"，"developed based on vLLM 0.20.0 and vLLM-Omni 0.20.1"，约 6000 行 Python，扩展"the paged KV block pool and the existing HBM-DRAM offload connector"（§6）；模型 Qwen3-Omni、Ming-Flash-Omni 2.0 于 8×H200。复现需 vLLM-Omni offload connector 路径加 VAD/播放遥测管线。

#### VoxServe（arXiv:2602.00269）

- a. 一手来源：arXiv:2602.00269v1（2026-01-30，Kamahori 等），HTML 全文含 Appendix A/B 已读。代码 github.com/vox-serve/vox-serve（Apache-2.0）。
- b. 负载与状态对象：单次每请求 TTS/STS 生成（LibriTTS、VoiceBench；60 s Poisson 到达，§4.1），CosyVoice 2.0、Orpheus 3B、Step-Audio 2 等。状态是每请求 KV 加每请求 detokenizer cache，"initialized in the preprocess method and stored per request"（§3.1）；README API 为单一 POST /generate，无 session ID。
- c. 下一次使用信息：无；不存在跨请求 KV 驻留决策。全文不提 swap、offload、eviction、preemption；内存压力以静态最大批处理（Step-Audio 为 32，"due to the KV cache's higher memory consumption"，App. A）。期限模型（§2.3，Eq. 2）："the (i+1)-th chunk must be delivered no later than the end of playback of the i-th chunk"；streaming viability 为每 chunk 二元指标。调度（§3.2.1）：startup 阶段优先至首音产出，受并发上限约束；steady-state 请求按"a soft deadline based on its chunk duration and the accumulated timestamp lag"排序，"within 1 second of the deadline"者优先。无接纳/拒绝策略。full-duplex 仅出现于所引题名（PersonaPlex，§4.3.3）。
- d./e. 逐出与恢复：不适用，KV 生命周期即请求。
- f. 相位与期限：不控制相位；每 chunk 软期限仅用于批内优先排序。
- g. D1–D4 均未处理：无跨请求保留状态，故无 swap、无恢复、无空闲（§3.1；§5 "none of these systems address the challenge of serving SpeechLMs for high-throughput, real-time streaming generation"）。
- h. 迁移障碍：无会话抽象、无保留历史、无 KV 分层；其期限概念是单请求的输出 chunk，非持久会话的周期更新。
- i. 基线可用性：期限/viability 指标与每 chunk 流式调度器的分析参照；加会话层后可作输出节拍基线，不能作 KV 管理基线。代码 PyTorch + FlashInfer + CUDA graphs，约 20k 行（§3.3，§3.1.1），非 vLLM 基。

### 2.5 周期与错开

本节唯一条目不是推理服务系统，而是实时强化学习论文；按作者 2026-09-21 意见，它不作为正式比较对象，只在"周期任务与 deadline 调度"一族保留一句作为"错开相位以填满节拍"的概念先例，与 Liu & Layland 并列。以下分析保留为核对记录。

#### Staggered Asynchronous Inference（arXiv:2412.14355）

- a. 一手来源：arXiv:2412.14355v1（2024-12-18；Riemer, Subbaraj, Berseth, Rish），HTML 主文与 PDF 附录 A–C 已读。代码 github.com/CERC-AAI/realtime_rl（MIT）。
- b. 负载与状态对象：单环境实时 RL（Game Boy Pokémon/Tetris、Atari）；"状态"是环境观测；策略为 15/30 层 ResNet DQN，逐调用无状态。无 KV cache、无 transformer。
- c. 错开对象：同一策略的 N_I 个推理进程在同一条流上按时间偏移，使动作以规则间隔执行；这些进程是一个策略的复制品，不是独立流。§1："even models with high inference times can act at every step using sufficiently many staggered inference processes"；§3："with no offset between them, all additional actions in the environment would be overwritten"，"staggering processes to maintain regular intervals is essential"；§4："a more challenging real-world setup with a single environment"。Algorithm 1 "Maximum Time Inference Staggering" 初始化 delay[p] = ε(p−1)/N_I，观察到新最大延迟时调整其他进程延迟"to preserve the spacing between actions"；Algorithm 2（App. A）用均值。界 τ̄_I ≤ min(τ_θ^max/N_I, τ̄_M)；App. B：N_I* = ⌈τ_θ^max/τ̄_M⌉；§5.3 "N*_I scales roughly linearly with τ̄_θ"。内存/KV 管理：无。§3.2："we run each process on its own dedicated CPU such that resource constraints like memory capacity, and memory bandwidth do not present significant issues"，单 GPU 多进程留作未来工作；§6："Memory bandwidth is a primary bottleneck in allowing for asynchronous computation with current hardware"。App. C 无 LLM、KV 或多租户硬件共享内容。
- d./e. 逐出与恢复：无。
- f. 相位与期限：错开是有意的相位指派，但对象是一条流内的复制品以填满单一动作时间线；无多会话需求、无内存维度、无期限（无动作就绪时环境取默认动作；τ_M 为环境步时间）。
- g. D1 概念相邻（偏移指派以避免重合工作）但未针对内存容量——目标是动作节拍，进程是复制品而非有保留状态的租户。D2–D4 未处理（无状态搬运）。
- h. 迁移障碍：无持久 per-process 状态、无容量约束建模、无期限语义；错开用于填补间隙而非分散峰值需求。
- i. 基线可用性：仅分析参照——"错开复制品使慢模型满足快周期"的思想与 N_I ∝ τ_θ 的线性标度。代码为 RL 专用（PyTorch multiprocessing，Game Boy/Atari），不可改作 serving 基线。

### 2.6 2026 年新条目（本次检索发现，核对日期 2026-09-21）

以下条目均不在任务单原列表中，按同一字段做压缩分析；除标注者外均读到全文。共同点：全部面向 agent 工具调用或人类批准的不规则空闲窗口，无一处理周期释放、相位指派或 per-update 期限。

#### UNISON（arXiv:2609.09643，2026-09-09，cs.AR；He, Li, Zeng）

- a/b. v1；agent 会话，每会话 KV 前缀；两层 SRAM + HBM（Eq. 3），host/SSD 仅见于相关工作。
- c. Spear：每会话回归间隔 EMA（Eq. 4，gap_end 时更新）加按 turn 索引的 hazard/survival 查找表（Eq. 5–6），复合评分 Eq. 7；明确排除 agent 角色身份与未来到达（§III-A）。估计；5 折 CV 内 0.85 pp（Table IV）。
- d. 会话粒度逐出（argmax 评分，Alg. 1 第 9–10 行）；触发为容量违约而非空闲；无部分逐出（token 剪枝称互补，§II-C）。
- e. Tide：gap_start 时以 DMA 预算 B_tokens = Δ·B（Eq. 8）在等待期把 HBM→SRAM 提升，使 KV "already in the fast tier when the next request arrives"（§IV）；Δ 来源仅述"estimated remaining duration"。Tide 未在 vLLM 上实施（"no tier-placement API"，§V-G）。
- f. 单一 DMA 预算门；无期限（仅 TTFT p50）。
- g. D1 未处理。D2 部分（迁移量以 gap×带宽为界，Eq. 8，但整会话单位）。D3 部分（在 gap 内提前提升）。D4 未处理（压力触发）。
- h. agentic 工具间隔（中位 3.7–7.2 s，最小 1 ms，§VI-E）；无周期、实时或语音内容；SRAM/HBM 层而非 host-backed。
- i. trace 驱动模拟器 + vLLM v1 前缀缓存 patch + 28 nm RTL 综合；未见代码链接。仅分析参照。与本文最接近的一点：Eq. 8 把"空闲时长乘链路带宽"作为搬运预算，与本文"偏移窗口内链路可搬运量"同型，但作用于 SRAM/HBM 提升而非 GPU 驻留逐出深度，且时长是估计而非预先给定。

#### Cascade（arXiv:2608.06557，2026-08-06；Adnan 等）

- a/b. v1；按请求类（ChatBot/Tool&Agent/Coder/Reasoning）；层级 HBM / DRAM / NVMe（§IV-A）；Aliyun Bailian 生产 trace（§V-A）。
- c. 每请求延迟预算 B_r = S^TTFT − 离线模型预测的 L_r（Eq. 3–4），每 chunk 按流逝时间刷新（Eq. 5）。
- d. 各层 LRU 回收；HBM 溢出时抢占预算最大的 prefill 请求，若预算允许则溢至 DRAM（§IV-D）；无预算驱动的降级策略。
- e. 恢复仅在请求出队入批时（Alg. 1）；显式部分恢复：字节 ≤ M_r,k = [B_rem − Σδ]⁺/Σ(1/B_eff)，余量重算（Eq. 6–7）。这是 2026 年唯一给出"由时间预算推导恢复多少"旋钮的论文。
- f. 类级 TTFT + TPOT SLO（Table III）；无周期期限；链路竞争仅经 B_eff 与保护带 γ。
- g. D1 未处理。D2 部分（时间预算推出字节上限）。D3 未处理（出队时恢复）。D4 未处理（LRU/分配失败）。
- i. vLLM-v1 + LMCache，经扩展 Vidur 模拟器以 GB200 NVL72 profile 评估（§V-A）。仅分析参照。风险点：其"预算→恢复字节"的推导与本文"窗口→逐出深度"的推导互为对偶，正文须说明本文的界作用于逐出侧、以预先给定的释放时刻而非预测的 TTFT 余量为输入。

#### TokenCake（arXiv:2510.18586v4，2026-08-21；EuroSys '27 已接收；Bian 等）

- a/b. v1 为 2025-10，2026 修订并接收；多 agent DAG 应用；每请求 16-token KV block；GPU HBM + CPU DRAM（§7.1）。
- c. 函数调用时长：用户提供的 `predict_time` 与每函数 EWMA 混合（Eq. 1，§4.1）；应用发出 `call_start`/`call_finish` 事件（§6.2）；误差敏感性 §7.5。
- d. 触发为 `call_start` 事件（主动，Table 2 "FC Start"），受 GPU 压力阈值、有等待请求可用、T_window = T_FC − T_transfer > 0 三重门控（Alg. 1，§4.2）；每请求全有全无。
- e. 预测式上载"as the predicted completion time approaches"（§4.1）；预算 B_upload（Eq. 3）与每步预留（Eq. 4）；紧迫度项 U（§4.3）；工具提前返回则立即上载。无显式提前量公式。
- f. 共享压力快照（§3.2）；承认 PCIe 饱和但无仲裁（§7.6）；无 SLO/期限。
- g. D1 未处理。D2 部分（仅在有等待请求且窗口覆盖传输时 offload；仍整请求）。D3 部分（在预测返回前上载）。D4 触发上已解决（空闲事件而非分配失败，但受压力门控）。
- i. 约 9k 行复用 vLLM 组件，重加 vLLM V1 移除的 CPU block pool（§6.3）；基线 vLLM v0.8.6、Mooncake v0.3.0-beta、Parrot；Qwen2.5-14B/32B/72B 于 A100/H20；实测 4096 token offload 32 ms 对重算 1815 ms（§7.6）。未见代码链接。仅分析参照。风险点：D4 的"空闲事件触发换出"与 D3 的"预测返回前换入"已被其在工具调用域覆盖；本文须把区别落在"事件与估计"对"预先给定的周期释放"，以及"整请求"对"链路预算界定的部分深度"。

#### Adaptive KV Retention at Human-Approval Timescales（arXiv:2608.30830，2026-08-31；Choi, Joshi）

- b/c. 因人类批准挂起数分钟至数小时的 agent 请求（τ²-bench）；明确不做每请求等待预测，控制器只用 offered load λ 与离线标定等待样本（§3.4，Fig. 1）。
- d/e. 挂起事件时整上下文移至 host DRAM（§3.4）；host TTL t2(λ) 由 GPU 时间机会成本模型给出（Eq. 3，§3.3）；仅在 resume 时恢复，无预取（§3.1）。
- g. D1 未处理。D2 未处理（整段）。D3 未处理。D4 已解决（挂起事件触发 offload，量化 break-even t1≈1 s，Table 3）。
- i. vLLM v0.27.1 TP4 OffloadingConnector，Llama-3.1-70B 于 4×H100 NVL（App. F）；基线含 MORI 移植与 Continuum fork。仅分析参照。

#### Ask the Tool, Don't Guess（arXiv:2609.18849，2026-09-16；Liu, Zhang, Li, Zhang）

- c. 运行中工具经 harness 侧信道发出的进度报告（剩余比例或即将完成信号，§2.2，§3.1–3.2，Table 2），线性换算剩余时间（§4.1）；调用 90% 处中位误差 <10%（§4.2，Fig. 7）。
- d/e. 调用中内存压力下逐出（§4）；有 host 层时"refreshes the context one lead time before the predicted return"（§5.1），恢复预算测 2 s 与 0.5 s（§4.2，Fig. 8）；阈值来源未述；整段或部分未说明。
- g. D1 未处理。D2 未处理。D3 部分（预测返回前一个提前量重载）。D4 部分（压力触发，但排序用实时剩余时间）。
- h. 需要合作的工具；人类等待明确出界（§2.2，Limitations）。
- i. vLLM（版本未述），数百行（App. D）；4×H100。仅分析参照。

#### 其余条目（压缩）

- MORI（arXiv:2606.00866，2026-05-30；Xia ... Stoica）：agent 程序按最近 5 周期 idleness ι 排序，5 s 控制 tick（Eq. 1，§4.2，§5）；程序粒度降级、GPU 容量恢复时才重载且请求阻塞至提升（§4.3.1）；无预取、无 SLO。D4 部分（相对 idleness 排序而非分配失败，仍由容量失配触发）；其余未处理。ThunderAgent + SGLang v0.5.10；未见代码。
- CacheWise（arXiv:2606.16824，2026-06-15）：以 tool_name/args 聚类预测条件期望复用时间（§5.2），block 级压力触发逐出，无预取（§6.4）。D2 部分；其余未处理。
- CacheScout（arXiv:2605.27744v2 APSys '26；全文版 arXiv:2608.14624，2026-07-16）：一阶 Markov agent 转移矩阵，recency 以调度步计非墙钟（§3.2–3.3）；`BetweenStep` 中预热预测 agent 的 anchor（系统 prompt/工具），非会话历史（§3.4，Alg. 1）。D3 部分；其余未处理。vLLM v0.11。
- ScaleSim（arXiv:2601.21473，2026-01-29）：多 agent 仿真的"invocation distance"（§3.2，Eq. 1–2），明确为序而非时刻；阈值下预取（§3.3）。D2/D3/D4 部分；D1 未处理。SGLang v0.5.2。
- Talaria（arXiv:2607.17181，2026-07-19）：固定 τ=1 s 软预留（§3.3）；HKVR 在请求完成或进入工具间隔时异步 checkpoint 对齐 KV block（§3.5）；返回时 H2D 恢复，无预取。D2 部分、D4 已解决（turn 结束即发 D2H）；D1/D3 未处理。SGLang。
- PBKV（arXiv:2605.06472，2026-05-07）：GraphSAGE 预测下一 agent（§4.1）；仅在纯 decode 批中预取、量以一步 decode 可隐藏为限、提前一步（§4.3）。D3 部分。SGLang + HiCache。
- Pythia（arXiv:2604.25899v2，2026-05-14）：`app_metadata` 三个工作流 ID（§4.1）；未来路径 block 留 L3，下一 prompt 预取至 L2 host DRAM 而非 HBM（§4.2.1，Alg. 1）；无时间预测器。D3 部分。
- SuperInfer（arXiv:2601.20309v2，2026-05-18；MLSys '26）：SLO 驱动整请求主动轮转到 Grace DRAM（VLT 指标，§4.2.2，Alg. 1）；DuplexKV 后台急切复制已同步 block，抢占时只搬最后脏块（§4.3.2）；仅单轮负载（App. E.2.3）。D4 部分。vLLM v0.6.6.post1，GH200 NVL2；代码公开。
- Pallas（arXiv:2608.16477，2026-08-17）：蜂窝切换场景，非 KV serving，但为"期限锚定的预取窗口"最近类比：T_w = t̂_HO − t_trig 以网格搜索最小化 α·SIT + (1−α)·早暴露（Eq. 8，Alg. 1）；残差项惩罚超出 B·T_w 的字节（Eq. 5）但无硬上限；多用户竞争评估但未联合分配（§4.5，§6.4）。
- AgentServeSim（arXiv:2606.09613v3，2026-09-05）：模拟器，Retention Plane 仅 protect/release/evict，不建模 host offload 与预取（§3.4，App. E）；策略搜索工具，非竞争者。
- Where Should the KV Cache Live?（arXiv:2609.16215，2026-09-14）：离散事件模拟；block 级 LRU/频率/EWMA 策略；报告预取"uniformly negative"，甚至 oracle "never beats no prefetch on migration traffic"（§V-E）；无期限、无会话时序。作为反向发现须在正文回应（其结论建立在无期限、无预先给定释放时刻的负载上）。
- llmovoice（arXiv:2609.04288，2026-09；SOSP '26）：托管 Realtime API 之上的语音会话 serving；按 turn 非双工（§1，Fig. 1）；每 turn 重建有界文本/音频上下文；无 KV 管理、无 GPU（§3.5，§4）；引 Moshi/Qwen3-Omni 但未引 Metronome/LiveServe。同会议语音 serving 论文，供 scope 对照引用，非 KV 驻留竞争者。
- Stateful Transformers / "Attention Once"（arXiv:2605.13784，2026-05-13，单作者）：周期市场数据流（1–60 s tick，§3.9.1）的持久每会话 KV；仅 GPU 驻留；空闲逐出到盘为未来工作（§6.3）；无预取。周期摄入但无容量机制。
- TOPAS（arXiv:2608.25523）、HyMCache（arXiv:2607.18141v3）、GitHub Copilot characterization（arXiv:2608.00101）：分别为接纳时 GPU↔CPU 前缀迁移无预取、CXL 混合远端层查找时触发预取、turn 边界空闲时间生存预测器（LightGBM，ROC-AUC 0.73 对 >60 s，§9.2）但不建机制（§12）。
- 相邻已知项确认：Continuum arXiv:2511.02230 最新 v7（2026-09-08），另有 UC Berkeley EECS-2026-234 硕士论文版；Waxing-and-Waning arXiv:2608.22704v2（2026-08-29，EMNLP 2026）为请求内 CPU 驻留音频 KV 的 chunk 级召回，非会话驻留；OrbitFlow arXiv:2601.10729v2（VLDB 2026）为单请求按层 ILP 放置；NEO（MLSys 2025，arXiv:2411.01142）确认。FlashGen（ASPLOS 2025）三次检索未能确认该名下论文存在，既有综述中该条目待核。
- 内部相邻工作（不作分析对象）：Conflux / "The Model in the Middle"（arXiv:2607.25792），摘要确认为 position paper。

## 3. 对本文主张的风险表

按本文四项主张列出可能已部分覆盖的系统，以及正文须如何限定。"覆盖"指对方在其负载域内实现了同类动作，不表示在本文负载上成立。

| 本文主张 | 可能已覆盖部分的系统（来源位置） | 覆盖的成分 | 未覆盖的成分 | 正文限定方式 |
| --- | --- | --- | --- | --- |
| 相位指派与 slot 接纳（回应 D1） | Staggered Asynchronous Inference（§3，Alg. 1）；Metronome（§3/§5.1 "phase-staggered streams"）；Mooncake（§7.3 反相振荡观察） | 有意错开时间偏移以避免重合工作（Riemer）；负载天然错开的观察（Metronome）；相位现象的观测（Mooncake） | 错开对象是单流复制品而非有保留状态的多租户；Metronome 服务端单一全局 tick 不利用偏移（仓库 gateway-go/main.go 亦无 offset）；Mooncake 视为预测滞后副作用 | 引 Riemer 为"偏移填补节拍"的思想来源并指出对象差异；引 Metronome 说明"负载错开"与"服务栈利用错开"是两件事；不宣称"首个错开"，只宣称"首个把偏移作为 KV 驻留的控制量" |
| 主机后备的尾部部分逐出，深度以偏移窗口内链路可搬运量为界（回应 D2） | InferCept（§4.1 swap limit N_i = 链路在 T_fwd 内可搬量）；UNISON（Eq. 8 B_tokens = Δ·B）；Cascade（Eq. 6–7 时间预算→恢复字节上限）；Pensieve（§4.3.1 chunk 级部分逐出）；LiveServe（§5.1 block 级、后缀先）；HCache（§4.1.2 层维 I/O–算力平衡） | "链路时间界定搬运量"的旋钮（InferCept 以 forward 时长、UNISON 以估计空闲时长、Cascade 以 TTFT 余量）；部分驻留与后缀先逐出（Pensieve、LiveServe） | 无一以预先给定的释放偏移窗口为界；InferCept 的界服务于隐藏在他人 forward 后而非本请求期限；UNISON 作用于 SRAM/HBM 提升；Cascade 作用于恢复侧非逐出侧；Pensieve 逐前导而非尾部、深度由容量压力定；LiveServe 深度由当前需释放 HBM 定 | 正文须明写三点差异：界的输入是预先给定的释放时刻而非估计或 forward 时长；界作用于空闲逐出深度而非恢复字节；界与相位指派耦合（slot 密度改变窗口）。不得宣称"首个部分逐出"或"首个链路预算界" |
| 空间门控预取按期限排序（回应 D3） | SYMPHONY（§3.1 advisory 提前 5.8–11.3 s）；LiveServe（§5.2 speech-onset 预取、可隐藏才接纳）；TokenCake（§4.1 预测返回前上载）；Ask the Tool（§5.1 返回前一个提前量重载）；KVFlow（§3.2 提前一步）；UNISON（§IV gap 内提升）；CachedAttention/Strata/LMCache/Bidaw（排队期慢层→快层预取） | 到达前预取已被多系统实现，提前量来源分别为应用提示、语音事件、工具时长估计、进度报告、图距离、空闲估计、队列 | 提前量均为外生信号或估计，无一由预先给定的周期推出；无一按期限排序跨会话预取；无一以"前序会话逐出释放空间"为门控；SYMPHONY 自陈 hint 无时序与次序保证（§3.2）并"assumes that advisory requests arrive early enough"（§3.6） | 不得宣称"首个提前预取"；主张应限定为"提前量由负载预先给定的释放时刻推出、按期限排序、以空间释放为门控"。须回应 arXiv:2609.16215 §V-E 的"预取一律为负"结论：其负载无期限亦无预先给定的释放时刻 |
| 空闲触发的换出（回应 D4） | InferCept（Appendix：暂停事件触发换出）；TokenCake（Alg. 1 `call_start` 触发）；Human-Approval Retention（§3.4 挂起事件）；Talaria（§3.5 turn 结束 checkpoint）；ECHO（§4.2 生成即备份，逐出仅改元数据）；SYMPHONY/CachedAttention/HCache/Strata/LMCache/Mooncake（生成中异步写回） | 事件触发（非分配失败）的 D2H 在工具调用域已成惯例；"始终备份、逐出零拷贝"已有 ECHO 与 SYMPHONY 先例 | 事件是工具/挂起而非周期性 KV 空闲区间；写回后的 GPU 侧移除仍多为压力触发（SYMPHONY §3.4、LiveServe §5.1、Strata write-back）；Metronome §8 明确否认周期会话存在空闲间隙 | 正文须区分"D2H 何时发生"与"GPU 空间何时回收"两个动作，只对后者宣称空闲触发；须以 q(i,k) 到 s(i,k+1) 的 KV 空闲区间定义正面回应 Metronome §8 的"presumes idle gaps that a periodic session never has" |
| 总体定位："尚无已知工作利用周期负载预先给定的下一次使用时刻驱动驻留回收与状态恢复" | Metronome（周期实时任务框架，§2）；Stateful Transformers（周期数据流的持久 KV，§3.9.1）；Kairos physical AI（arXiv:2605.11381，周期 generate-execute 循环） | 周期负载框架已被占据（Metronome）；周期摄入的持久 KV 已有实例 | Metronome 以窗口约束状态、拒绝 swap；Stateful Transformers 无容量机制；Kairos 无 KV 管理 | 定位句在本次核验后仍成立，但须缩为"利用预先给定的释放时刻同时驱动逐出深度、预取时机与相位指派"，并把 Metronome 列为"同一负载框架下的对立路线"而非"未涉及周期" |

补充风险：

- 词汇碰撞。LiveServe 已使用 "next-use aware eviction"，UNISON 使用 "idle gap DMA budget"，Cascade 使用 "restoration budget"；本文核心词表（[问题定义术语表](../problem.md#terminology)）若采用相近词须在 Related Work 中显式区分。
- 基线选择被质疑。审稿人可能要求与 LiveServe 或 TokenCake 直接比较；两者均无公开代码（见第 4 节），正文须提前说明并给出重实现或分析参照的理由。
- "无空闲区间"反驳。Metronome §2 与 §8 是最可能被引用来否定本文前提的原文；本文须以实测的 KV 访问端点（而非对话停顿）证明空闲区间存在，该证据属 [Findings](../findings.md) 域。

## 4. 基线建议

对应 [评估计划](../experiments.md#comparison-families) 中"最接近的持续会话/KV 管理系统"一行的待选项。分级依据：代码是否公开、引擎基座是否与本文实测路径兼容、模型与负载是否可对齐。以下为建议，不是实验矩阵的冻结。

### 4.1 可实测（代码公开且引擎兼容或可接入）

| 系统 | 代码 | 引擎与版本 | 作为何种基线 | 适配障碍 |
| --- | --- | --- | --- | --- |
| Metronome | github.com/19PINE-AI/metronome（Apache-2.0） | vLLM 0.23 patch + Go gateway + Python gRPC worker；单卡 RTX PRO 6000 Blackwell | "约束状态"路线的对立基线：窗口化 KV + AIMD 接纳；同为周期实时任务框架，是最直接的定位对照 | 实测路径绑定 vLLM 0.23 与 Blackwell 修复集（Appendix B）；sink mask 仅 Triton 路径，serving 实验用 FlashAttention 窗口半侧（§7）；语义不同（有损），须按 [评估计划](../experiments.md#comparison-families) 作为保留策略参数而非"必败基线"进入比较；本仓库已有 matched Metronome baseline 配置（见 [评估计划复现附录](../experiments.md#measured-stack)），公平性差异已登记 |
| LMCache | github.com/LMCache/LMCache（Apache） | vLLM/SGLang connector，模型支持广 | "生产级分层缓存 + 排队期预取"基线，代表 D3 部分解决、D4 部分解决的工业现状 | 需自写外部编排器用 move/pin API 模拟相位预取（§7 无 prefetch 原语）；CPU offload 路径默认无空闲驱动的部分逐出；chunk/hash 抽象无会话与期限概念 |
| InferCept | github.com/WukLab/InferCept | 2024 年代 vLLM fork；A100 | "链路时间界定的分块 swap + 事件触发换出"基线，是 D2 旋钮与 D4 触发的最强先例 | 需构造"每 T 暂停一次"的 chatbot interception 驱动器；六类混合数据集与 FCFS 固化在 harness；换入仍在返回后（D3 未处理），可作提前恢复价值的隔离对照 |
| Mooncake Store / Transfer Engine | github.com/kvcache-ai/Mooncake | vLLM MooncakeStoreConnector 或 SGLang HiCache 后端 | 传输与存储层基线，非调度基线 | Conductor 调度逻辑不确定可复现（仓库有目录但 README 未述）；分布式 RDMA 假设与单机 host-backed 不同 |
| vLLM 内建 swap / OffloadingConnector | 引擎自带 | 与本文实测路径同引擎 | naive 方案的直接实现，D1–D4 四缺陷的参照 | 无；已是本文 [消融矩阵](../experiments.md#ablation-matrix) 中"按需恢复控制"的基础 |

### 4.2 需适配后可实测

| 系统 | 障碍 |
| --- | --- |
| KVFlow | SGLang fork（论文 v0.4.4）；前端元数据假设 `sgl.function` agent，需合成 HTTP 元数据；保护对象为静态前缀，与增长的会话历史不匹配 |
| Strata | 论文未给代码；SGLang 开源 HiCache 与其不等同（论文将 SGLang-HiCache 列为对照，§5.1）；需先确认代码可得 |
| SuperInfer | 代码公开但仅 GH200 NVL2 与单轮负载（App. E.2.3） |

### 4.3 仅分析参照

| 系统 | 原因 |
| --- | --- |
| LiveServe | 无代码或 artifact 声明；基于 vLLM 0.20.0 + vLLM-Omni 0.20.1 约 6000 行；复现需 offload connector 路径加 VAD/播放遥测。是 next-use 感知逐出与事件预取的最接近参照，须在 Related Work 逐句区分 |
| CachedAttention、Pensieve、HCache、Bidaw | 均无公开系统代码（Bidaw 仅 trace；Bidaw §5 明言 CachedAttention 闭源）；Pensieve 与 HCache 为自研或 DeepSpeed-MII 引擎 |
| SYMPHONY | 无代码；约 2400 行 vLLM scheduler 挂接；hint 机制在周期负载中冗余 |
| Cake、CacheFlow | 无代码；恢复侧混合，无逐出侧；Cake 基于 LMCache v0.1.4 + vLLM v0.6.2 |
| InfiniGen、ECHO | 有损近似或需原生稀疏注意力模型（DeepSeek-V3.2 于 8×H20），与稠密全注意力的双工模型不兼容 |
| Learned Prefix Caching | GPU 单层丢弃策略，无 offload |
| VoxServe | 无会话与 KV 分层；可作输出节拍与 viability 指标参照 |
| Staggered Asynchronous Inference | 实时 RL 论文，非 serving 系统；不作比较对象，仅在周期调度一族引作偏移思想来源 |
| 2026 新条目（UNISON、Cascade、TokenCake、MORI、CacheWise、CacheScout、Talaria、Human-Approval Retention、Ask the Tool、ScaleSim、PBKV、Pythia） | 均面向 agent 工具间隔；多数无代码链接；Cascade 为模拟器评估；作为 D2/D3/D4 各成分的"已有先例"在 Related Work 引用，不作实测对照 |

### 4.4 建议

- 实测对照取三类：naive（vLLM swap/OffloadingConnector）、工业分层（LMCache 排队期预取）、对立路线（Metronome 窗口化）。三者代码公开、引擎相近，可满足 [公平性要求](../experiments.md#comparison-families)。
- InferCept 作为"链路预算旋钮但无提前恢复"的隔离对照价值最高，若资源允许优先于 KVFlow。
- LiveServe 作为最接近的分析参照，Related Work 须逐条对照其 §5.1/§5.2 原文；若审稿人要求实测，说明无代码且负载为半双工按 turn。
- 所有基线的 generation 工作量、保留规则与调度差异须按 [评估计划](../experiments.md#executed-decode-difference) 登记，不能以配置名替代路径核对。

## 5. 检索记录

检索日期 2026-09-21。引擎：通用网页检索、arXiv advanced search（2026-01-01 至 2026-09-21，全字段）、Semantic Scholar 引用图、会议接收列表页。已知系统（任务单所列 20 项与 Conflux）不计入"新命中"。

### 5.1 网页检索（关键词 → 考虑的命中 → 处置）

| # | 关键词 | 新命中（接受） | 拒绝或已知 |
| --- | --- | --- | --- |
| 1 | multi-turn conversation KV cache offload prefetch arXiv 2026 | HyMCache（相邻） | ContiguousKV、SwiftCache、VAMP、ConServe、RelayCaching（拒：共享前缀 I/O 或调度无驻留）；Continuum（已知） |
| 2 | arXiv 2026 KV cache periodic inference real-time deadline speech | 无 | Metronome（已知）；Bottlenecked Transformers、VLA unified KV、KVP、ScoutAttention、PaFu-KV（拒：模型或请求内） |
| 3 | full-duplex speech LLM serving KV cache offload arXiv 2026 | SuperInfer | LiveServe、VoxServe（已知）；WnW（相邻）；LWS、BayLing-Duplex（拒：模型）；Unified KV Pooling（拒） |
| 4 | periodic KV cache prefetch LLM serving arXiv 2026 | PBKV；Pallas（类比） | PRESERVE、L2 prefetch 2504.06319、Elastic KV、GroupKV（拒）；InfiniGen（已知） |
| 5 | proactive KV cache offload idle session LLM serving arXiv 2026 | TokenCake、MORI、Copilot characterization（部分） | Keepalive Economics（拒：客户端） |
| 6 | next-use aware KV cache eviction LLM serving 2026 | PBKV | randomized caching 2601.18999、AgentKV、Leyline（拒） |
| 7 | streaming speech LLM serving KV cache host memory arXiv 2026 | 无 | FlexiCache、AudioKV、DéjàVu、SpeechKV、2606.06302（拒：请求内压缩）；WnW（相邻） |
| 8 | arXiv 2026 KV cache duplex conversational model serving | 无 | Metronome（已知）；Nexus、Recency/Frequency、Persistent Q4（拒） |
| 9 | real-time KV cache prefetch deadline LLM serving 2026 | 无 | SYMPHONY（已知）；py-kvcache（拒：排队期预载）；EECS-2026-234（= Continuum 论文版）；kv_deadline_scheduler GitHub（拒：无论文） |
| 10 | staggered release LLM inference sessions phase staggering serving | 无 | SBS 2512.16134（拒：批处理）、AMPD、STAR、StagFormer（拒） |
| 11 | session KV cache scheduling deadline LLM serving arXiv 2026 | 无 | OrbitFlow（相邻）；SAGA 2605.00528（仅据摘要，待核验）；2502.07115（拒） |
| 12 | idle-triggered KV cache offload LLM serving arXiv 2026 | MORI、TokenCake | 2605.00831（拒：容错） |
| 13 | omni-modal LLM serving system KV cache offload audio playback arXiv 2026 | 无 | LiveServe、vLLM-Omni（已知）；Omni-Flow、M* 2606.12688（拒） |
| 14 | arXiv 2026 real-time interaction model serving KV cache Moshi Qwen-Omni scheduling | 无 | TokenFlow 2510.02758、MorphServe（拒）；Conflux（已知，不分析） |
| 15 | voice agent serving system KV cache session idle host memory prefetch 2026 | 无 | 无新命中 |
| 16 | clocked KV cache prefetch LLM serving deadline arXiv | Where Should the KV Cache Live?（反向发现） | Echo 2504.03651（已知） |
| 17 | LLM serving sessions release offset OR phase offset OR time-division KV memory capacity multiplexing arXiv 2026 | 无 | JustFit、2608.21719（拒）；无相位指派命中 |
| 18 | multi-turn KV cache prefetch idle user think time predictor serving arXiv 2026 | Copilot characterization | 无 |
| 19 | KV cache swap deadline LLM serving real-time sessions arXiv 2026 host memory prefetch lead time | 无 | 无新命中 |
| 20 | streaming ASR audio LLM serving system KV cache multi-session GPU memory arXiv 2026 | 无 | Prism ballooning（拒） |
| 21 | long-lived sessions KV cache placement GPU CPU SSD arXiv 2026 | Where Should the KV Cache Live? | KVDrive、2604.26968（拒） |
| 22 | time-triggered OR just-in-time KV cache prefetch host memory LLM serving arXiv 2026 | CacheScout（APSys） | 无 |
| 23–25 | speech LM serving RTF concurrent sessions；think time inter-turn offload；phase staggering peak memory | 无 | 2601.22996 理论（拒：重启流水线） |
| 26 | EuroSys 2027 / SOSP 2026 / OSDI 2026 / NSDI 2027 KV cache offload multi-turn prefetch | 无 | ECHO、Strata、SYMPHONY（已知）；DirectKV、Prism、DroidSpeak、FastServe（拒） |
| 27 | tail eviction OR partial eviction OR partial offload KV cache session LLM serving arXiv 2026 | 无 | 仅 token 级逐出论文；未见会话尾部逐出工作 |
| 28 | full-duplex dialogue model inference serving system batching multiple sessions GPU 2026 Moshi serving | 无 | MoshiRAG、SOMA（拒） |
| 29 | prefetch KV cache before the request arrives predicted arrival time | CacheScout | OasisKV、2607.26475（拒：decode 内） |
| 30 | LLM serving hibernate OR suspend OR park idle conversation sessions | Human-Approval Retention、UNISON | 无 |
| 31–32 | AGSERVE；CacheWise | CacheWise | AGSERVE = Ren 等 NeurIPS 2025（2025，未取） |
| 33 | venue/ID 核对 | Cake ICML/PMLR 确认；NEO 确认；Stream2LLM MLSys'26（拒） | OpenReview cK0kUzocJW 被拦；Cake/CacheFlow 无代码；FlashGen ASPLOS 2025 三次未找到；UniCache、CompQ、TransformKV、"Latency-SLO-Aware Memory Offloading"、"Elastic Memory Remapping"、Pegasus 仅见题名 |

### 5.2 arXiv advanced search（2026-01-01 至 09-21）

| 词组 | 命中数 | 相关项 |
| --- | --- | --- |
| "KV cache" + deadline | 6 | Metronome、Cascade；FairInference、DiLaServe、Edge governors、StreamDiffusionV2（拒） |
| + "real-time" + serving | 15 | 仅 Metronome |
| + speech + serving | 2 | 无 |
| + periodic | 31 | ContiguousKV、2601.22996、Copilot（PulseCol、Bottlenecked 仅字面） |
| + duplex | 4 | Metronome、SuperInfer、Aero、VoiceChat-TTS |
| + prefetch + session | 2 | Where Should the KV Cache Live?、CacheScout |
| + idle | 21 | MORI、TokenCake、SwiftCache、Copilot、HERALD |
| + "multi-turn" + offload | 7 | VAMP、py-kvcache、SmoothAgent、SwiftCache、CacheFlow、ContiguousKV、Continuum |
| + "next use" | 1 | FPGA linear attention（拒） |
| + session + serving | 15 | UNISON 未出现于此查询（经 Semantic Scholar 发现），说明 arXiv 全文检索有遗漏 |
| + swap + serving；+ voice；+ conversational + offload | 5 / 4 / 7 | 无新 |
| + prefetch + turn | 4 | CacheScout、OasisKV、HyMCache、ContiguousKV |
| + stagger* | 1 | 2601.22996 |
| + offload + idle | 6 | MORI、TokenCake、HERALD、SwiftCache |
| + audio + serving；+ Moshi；+ omni | 5 / 1 / 10 | Metronome、EPD-Serve、Aero；Metronome；全为压缩/量化或 Omni-Flow |

### 5.3 Semantic Scholar 引用图（2026 年引用者）

- Continuum（52）：UNISON、Ask the Tool、TOPAS、Human-Approval、ScaleSim、SMetric、CompQ、UniCache。
- TokenCake（18）：CacheScout 全文版、TokenDance、ForkKV。MORI（5）：AOSpec、PASTE。
- CachedAttention（100+23）：Talaria、SMetric、ConServe-memory、TransformKV、Latency-SLO-Aware、HyMCache、CommitKV。Pensieve（43）：ReCache、CacheSolidarity。KVFlow（60）：Pythia、PolyKV、KEEP、FATE、LRAgent。InferCept（17）：ScaleSim、HeraSys、Kairos。Cake（16）：ObjectCache、SparKV。CacheFlow（2）：BSR、ObjectCache。
- LiveServe（0）；Metronome（1，ASR 论文 2609.04225）。二者引用图仍近空，与 [双工综述](duplex-serving-systems-landscape-2026-09.md) 2026-09-02 的观察一致。

### 5.4 会议接收列表

EuroSys 2026（无驻留/时序竞争者；KUNSERVE、adaptive KV caching、TokenFlow）；SOSP 2026（llmovoice、SANDHI、Janus；无驻留竞争者）；OSDI'26 / NSDI'26 technical sessions（页面截断；ECHO、DirectKV、Strata、Prism、SYMPHONY、DroidSpeak、FastServe）；MLSys 2026（SuperInfer、FlexiCache、OPKV、MorphServe、Stream2LLM、FlashAgents；无会话驻留工作）。MLSys virtual 页与 USENIX accepted-papers 页为 JS-only 或 404。

### 5.5 未能读到全文的条目

- OpenReview cK0kUzocJW（Cake 的 ICML 前匿名提交）：forum、pdf、API 均被人机验证拦截；venue 与决定未核。
- SAGA（arXiv:2605.00528）：全文获取遇网络错误；仅据摘要，待核验（摘要称经工作流图预测 next-use、达 Bélády 的 1.31 倍）。
- UC Berkeley EECS-2026-234 PDF（Continuum 论文版）：仅二进制；不影响分析。
- UniCache（SIGMETRICS/POMACS 2026）、CompQ（ICWS 2026）、"Latency-SLO-Aware Memory Offloading for LLM Inference"、"Elastic Memory Remapping for Multi-tenant LLM Serving"、TransformKV、Pegasus：仅见于引用元数据，未找到可访问来源。
- AGSERVE（Ren 等，NeurIPS 2025）：在 2026 窗口外，未取；经 UNISON Table II 以 "ETA" 引用。
- Learned Prefix Caching 的 OpenReview 页面（Vj48eXaQDM）：人机验证拦截；论文 PDF 已读，不影响内容。
- 任务单原列 20 项与 Cake、CacheFlow 均读到全文；arXiv 派生的章节号经工具抽取，入稿前建议按 §x.y 再对一次原文。
