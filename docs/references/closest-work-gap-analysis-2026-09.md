# KV 管理与周期服务：外部文献核验笔记

保留 2026-09-21 调研的逐工作来源与机制记录；本轮仅清理文档，未重做全文核验。发表状态、代码可用性和论文版本均以原核验日期为界，正式引用前检查一手来源。

本笔记记录外部工作的属性，不能据此断言本项目新颖性；具体比较需结合[系统设计](../system.md)和[实验设置](../experiments.md#comparison-families)。

阅读时按工作名定位。优先核验的比较维度是时间信息何时产生、phase 是否可控、逐出量如何决定、恢复是否需预分配空间，以及计算、传输和 deadline 如何共同约束。已有部分逐出、提前预取和传输重算组合不能单独作为本项目原创性主张。

## 2. 逐系统分析

各条目记录来源、负载、时间信息、逐出、恢复与期限属性。

### 2.1 会话级分层与恢复

#### CachedAttention（ATC'24）

- 一手来源：arXiv:2403.19708v3（2024-06-30），全文已读；USENIX ATC'24 页面无 artifact 徽章或代码链接。作者 Gao, He, Sharma 等（NUS/SJTU/Huawei Cloud）。
- 负载与状态对象：多轮对话（ShareGPT，73% 多轮）；对象是每会话全部历史 KV，存于 host DRAM + SSD 的 AttentionStore（§3.1，Fig. 3/5）。GPU 不跨轮保留 KV，一轮结束即写出。
- 下一次使用信息：作业队列内容（已到达、排队中的请求），非到达时刻预测："the job scheduler maintains a job queue, thus having the full knowledge of waiting jobs"（§3.3.1）。可靠性为观测事件；无会话回归时刻估计，唯一时间量是 1 小时 TTL（§4.3.6）。
- 逐出粒度与依据：整会话，一个 item 即该会话全部 KV，"the minimal eviction and fetching granularity"（§3.3.2），理由是会话 KV "is either all used or none of it is used"。逐出由 host 空闲阈值触发，按 look-ahead eviction window（长度 (C_mem+C_disk)/S_kv）尾部优先（§3.3.2，Fig. 9）。无部分驻留。
- 恢复触发：host→GPU 在该作业执行时逐层流水（§3.2.1，Fig. 6–7）；disk→host 在作业进入队列且落入 look-ahead 窗口（长度 C_mem/S_kv）时预取（§3.3.1）。提前量由队列位置与空闲内存决定，与期限无关。
- 相位与期限：无相位控制；无逐次更新期限模型；到达为 Poisson（λ=0.5–2.0 会话/s，§4.1/§4.3.8）。

#### Pensieve（EuroSys'25）

- 一手来源：正确标题为 "Stateful Large Language Model Serving with Pensieve"（Yu, Lin, Li，NYU）；arXiv:2312.05516v3（2024-10-07），全文已读；ACM DOI 10.1145/3689031.3696086。
- 负载与状态对象：多轮对话；对象是每会话历史 KV-token，两层（GPU KV cache 兼作近期会话缓存 + CPU 内存），可部分丢弃后重算（§1，§3.1，§4.3；Fig. 5 四段布局：dropped / CPU / GPU / new prompt）。
- 下一次使用信息：无预测、无到达前预取。唯一启发式为后续请求"usually arrive within a reasonably short time period"（§1）；逐出评分使用最后活跃时间（观测事件）。
- 逐出粒度与依据：32 token chunk，"we group KV-tokens into chunks and make eviction decisions at the granularity of chunks"（§4.3.1）；评分 V = Cost(s,l)/T（重算代价除以距上次活跃时间）升序逐出，偏好逐出前导 token（Fig. 4）。支持部分驻留：上下文"might span both tiers of the cache and may be partially dropped"（§1）。触发：GPU 空闲槽 <25% 即开始 GPU→CPU 复制（§4.3.2）；深度由容量压力决定，无链路预算。
- 恢复触发：批次组装时，"Before handing off a batch of requests to the worker, the scheduler tries to ensure that any new request's past KV-tokens will reside in the GPU"（§4.3）；随后逐层流水（§4.3.3）。提前量为零。
- 相位与期限：无；明言"we aim to optimize throughput instead of latency SLA"（§7）；Poisson 到达加指数思考时间（均值 60 s，§6.1/§6.7）。

#### HCache（EuroSys'25）

- 一手来源：arXiv:2410.05004v1（2024-10-07，注 EuroSys 2025），全文已读；EuroSys 2025 accepted list 确认（Gao, Chen, Shu，清华）。
- 负载与状态对象：多轮对话（ShareGPT4）与长上下文/RAG（L-Eval）（§2.3）；对象是历史 token 的 hidden states（各层输入激活，体积为 KV 一半），存 SSD（默认）或 host DRAM（§3.1，§4）。GPU 不跨轮保留："we do not cache and reuse KV cache in GPU"（§4）。
- 下一次使用信息：无；缓存与预取被归为正交工作，AttentionStore 式预取"orthogonal to our work"（§4）。
- 逐出粒度与依据：主实验"The KV cache are evicted when one round of conversation ends"（§6.1.1）；§6.4 长上下文实验加 GPU LRU；无 host/SSD 逐出策略描述。"部分"仅指按层混合（部分层用 hidden state 重建、部分层直接载 KV 或重算），不是部分上下文。
- 恢复触发：请求到达时，位于关键路径："When a user request arrives, the inference engine first decides whether the request's history states should be restored"（§4）；"HCache adds an extra restoration phase"（§5）。唯一"预取"在恢复过程内部：前 L_O 层重算时"The hidden states of the latter layers are prefetched"（§4.1.2）。
- 相位与期限：无；指标 TTFT/TBT；Poisson 到达，"The interval between conversation rounds in one session is set to 30s"（§6.1.1）。

#### Strata（OSDI'26）

- 一手来源：arXiv:2508.18572v1（2025-08-26）与 USENIX OSDI'26 PDF（Xie, Xu, Zhao, An, Mailthody, Mahlke, Garland, Kozyrakis；Stanford/NVIDIA 等），全文已读。USENIX 页面无 artifact 徽章或代码链接；正文称"Built on SGLang and deployed in production"。
- 负载与状态对象：长上下文、prefill 主导负载（RAG、多轮 agent 对话，§3）；对象是前缀 radix 树上的 KV page（HiRadixTree，默认 1 token/page，§4.1/§5.1），非会话对象；层级 GPU/host/disk。
- 下一次使用信息：等待队列中请求对 HiRadixTree 的查找结果（已到达，观测事件）："the scheduler obtains the load and compute requirements of each request using the HiRadixTree"（§4.3.2）；另有 delay-hit 追踪（§4.3.1）。无到达前预测。
- 逐出粒度与依据：page；支持部分驻留（Fig. 7 区分 device hit 与 host hit）。"For all memory layers, the Least Recently Used (LRU) algorithm serves as the default eviction policy"（§4.2 末）；逐出量由容量压力决定。Balanced Batch Formation（Algorithm 1）限制批次 load/compute 比 ≤100，是每批加载量的旋钮，不是逐出深度的旋钮（§4.3.2）。
- 恢复触发：host→GPU 在批次派发时，"The Scheduler then sends this batch to GPU executor and initiates a KV cache loading request to the Cache Controller"（§4.1），逐层同步覆盖；disk→host 在排队期机会性预取，"opportunistically prefetches data from storage into host memory whenever a cache hit is detected at the storage layer. The prefetch latency is overlapped with the request's queuing delay"（§4.2.1）。提前量等于排队时长，由负载决定。
- 相位与期限：无相位控制；无 per-request 期限。§6 Discussion 自认调度器"can still treat requests unevenly, risking Service-level objective (SLO) violations for individual requests"。

#### Bidaw（FAST'26）

- 一手来源：USENIX FAST'26 PDF（fast26-hu-shipeng.pdf，2026-02，pp. 101–116；Hu, Zhang, Zhou, Wei, Zhong, Chen，清华等），全文已读。未见 arXiv 版本。唯一链接为 trace 仓库 github.com/ShipengHu-777/Interactive-conversation-workload（脚注 1）；系统代码未发布。
- 负载与状态对象：交互式多轮对话（百万轮工业 trace，平均 22.4 轮，query 36 / answer 45 token，§2.2）；对象是每用户历史 KV（MHA 模型下改缓存 storage-efficient tensor，§4），两层 host DRAM（performance layer）+ SSD（capacity layer）。
- 下一次使用信息：有估计——用上一轮模型回答长度预测下一次访问的 weighted reuse distance 下界（Spearman 0.94–0.98，§3.3.1，Fig. 12），在回答生成完成时产生（§3.1 步骤 3）；结合每用户历史分布与 ghost cache 的命中率（§3.3.3，Eq. 2）。可靠性为估计；只用于逐出选择，不用于预取时机。
- 逐出粒度与依据：整用户 KV，"the eviction manager will evict certain users' KVs to the capacity layer"（§3.1）；"The KV with the lowest calculated hit potential is selected for eviction"（§3.3.3）。触发：performance layer 空闲低于阈值（§3.1 步骤 4）；inclusive caching。无部分驻留。
- 恢复触发：请求到达，"Upon the arrival of each request, the compute engine captures its KV's I/O status"（§1）；SSD 上的 KV 进 preparing queue，按 disk-HRRN（Eq. 1）发起 SSD→host 读，完成后按原始到达时间插入 ready queue；host→GPU 在调度时（§3.2，Fig. 10）。论文明确否定逐层重叠对慢层有效："the I/O can only be overlapped with the first iteration ... Such a large time gap renders overlapping ineffective"（§3.2）。
- 相位与期限：无；指标为平均响应延迟与吞吐；工业 trace 真实时间戳加 ShareGPT Poisson 模拟（§5）。

#### LMCache（arXiv:2510.09665）

- 一手来源：arXiv:2510.09665v2（2025-12-05；Liu, Cheng, Yao 等，UChicago 等），全文已读。代码 github.com/LMCache/LMCache（Apache）。
- 负载与状态对象：跨查询前缀复用（context caching）与 PD 分离传输（§1，§2.3，Fig. 2）；对象是按 token hash 键控的 KV chunk（默认 256 token，跨层打包，§5.1），非会话对象；层级 CPU/本地盘/远端/Redis/S3。
- 下一次使用信息：到达请求的前缀匹配（观测事件）："the scheduler first calls get_num_new_matched_tokens which queries LMCache to see cache hit tokens in the backend"（§6，Table 2）。无到达前预测。
- 逐出粒度与依据：chunk；支持部分命中（§4/§6）。逐出算法未命名（全文无 LRU 字样），仅有 batched_admit/batched_evict 上报与 pin/unpin/clear API（§7，Table 3）；容量为配置上限（500 GB，§8.2）。逐出深度决定机制未描述。
- 恢复触发：请求到达/调度时，"start_load_kv is called to start loading KV cache of the first layer to GPU memory"（§6），逐层流水（§5.2）。排队期预取："LMCache exploits this idle interval to prefetch the queued queries' KV cache from slower storage tiers into faster ones"（§5.2）；get_num_new_matched_tokens 返回 None 可让请求回队列，"overlapping this request's I/O with other requests' computation"（§6）——与他人重叠，非移出自身关键路径。
- 相位与期限：无；无期限模型（仅让用户按"latency SLO and resource constraints"选预取目标层，§5.2）。

#### Mooncake（FAST'25）

- 一手来源：arXiv:2407.00079v4（2025-09-03，题 "Mooncake: A KVCache-centric Disaggregated Architecture for LLM Serving"），全文已读；FAST'25 页面题 "Mooncake: Trading More Storage for Less Computation — A KVCache-centric Architecture for Serving LLM Chatbot"（Best Paper；作者含 Cui、Ren，比 arXiv 多两位）。代码 github.com/kvcache-ai/Mooncake 开源 Transfer Engine、Mooncake Store 与 trace；仓库有 mooncake-conductor 目录但 README 未描述，Conductor 完整性不确定。
- 负载与状态对象：Kimi 生产长上下文负载（平均输入 7590 / 输出 182，§4.2）；对象是按前缀 hash 键控的 512-token KVCache block，分布式 CPU DRAM/SSD 池（§3，§4.1，Fig. 3）。
- 下一次使用信息：到达请求的前缀匹配（观测事件，Algorithm 1 FindBestPrefixMatch）；§1.1 声称预测"future usage of KVCache blocks"做复制与换出，但 §6.2 承认"it is impossible to accurately predict future usage"，实际为调度时触发的启发式热点迁移。
- 逐出粒度与依据：block；部分前缀命中原生支持；逐出策略可插拔，trace 上 LRU 最佳（Table 1，§4.2）；"specialized eviction policies for partial hits and expiration scenarios"为未来工作（§10）；量由 DRAM 容量决定。
- 恢复触发：Conductor 调度时（请求到达后），"It loads the prefix cache from remote CPU memory into GPU memory based on the prefix cache block IDs"（§3 Step 1）；逐层重叠："the load and store operations of the KVCache layer are performed layer-by-layer and in parallel with the prefill computation"（Fig. 4 caption）。无到达前预取。
- 相位与期限：无相位控制。SLO 为集群级 P90 TTFT/TBT 阈值用于拒绝（Algorithm 1 L27–28），非 per-request 期限；不同优先级/SLO 列为未来工作（§10）。§4.2 无会话轮间隔分析。

### 2.2 提前信号与预取

#### SYMPHONY（NSDI'26）

- 一手来源：USENIX NSDI '26 camera-ready，"SYMPHONY: Enabling Compute-Memory Disaggregation in LLM Serving Systems"（Agarwal, Hu, Mao, Akella, Venkataraman），全文已读。arXiv:2412.16434v1（2024-12-21，唯一版本）题名不同（"Improving Memory Management for LLM Inference Workloads"）且作者列表不同；引用 NSDI'26 时不应沿用预印本题名。
- 负载与状态对象：多轮 chatbot（ShareGPT、BurstGPT）与多 agent 流水线（MetaGPT）；对象是整会话 KV，在"unpredictable gaps between requests"（§1）间持久化于 GPU / host / disk / remote disk / blob 五层（§3.3）。
- 下一次使用信息：应用发出的 advisory request（§3.1）。chatbot 场景由前端在用户开始输入时触发（§3.1，Fig. 10）；agent 场景由离线 profile 的调用图对所有 next-hop agent 发出（§3.1，Fig. 8）。实测提前量 ShareGPT 派生 11.3 s、MetaGPT 5.8 s（§1）。hint 格式含 `expected_arrival: None, ordered: False`（Fig. 7），论文明示 hint "provide no guarantees about the timing of its arrival or its order relative to other ongoing sessions"，且"convey no information about memory requirements"（§3.2）。可靠性属估计：60% 假 advisory 造成 2.1% 吞吐损失（Fig. 20）；10% 漏 advisory 使 TPOT 由 21.3 ms 升至 24.4 ms（Fig. 19）。
- 逐出粒度与依据：按层 KV 块，在 vLLM block manager 内实现（§4.1）。压力下"remove the last layer of KV cache associated with the least recently used request"（§3.4）；逐出量由 serving 框架按需 purge 决定（cooperative memory management，§3.4），可无代价丢弃是因为最慢层始终持有完整副本，由后台线程持续写入（§3.4）。即 GPU 驻留可按层部分保留，但深度由分配压力与 LRU 决定，无链路时间或期限模型。
- 恢复触发：advisory 到达即贪心"moves it to the fastest memory tier possible"（§3.3）；提前量由用户或 agent 行为给出，系统不计算所需提前量。到达时未全驻留则回退到逐层异步读（§3.4 Cases 2–3）。`expected_arrival` 字段存在但未描述任何消费它的算法。
- 相位与期限：无 per-request 期限模型，指标为 TPOT/TTFT/req/s（§4）。多会话竞争仅启发式处理：两个 advisory 并发时"places lower-layer caches from both sessions in HBM first, deferring higher layers"（§3.4）；论文明言跨会话次序不可知（§3.2）。

#### InferCept（ICML'24）

- 一手来源：arXiv:2402.01869v2（2024-05-30），HTML 与 PDF 全文已读；ICML 2024，PMLR 235:81–95。代码 https://github.com/WukLab/InferCept（§1）。
- 负载与状态对象：augmented LLM 在 interception（工具/API/人类/环境调用）处暂停解码；Table 1 六类，平均暂停时长自 0.2 ms（Math）至数十秒（Chatbot，按阅读加输入时间估计，§2.2）。对象是暂停请求持有的 KV 上下文："the context (i.e., KV caches) cannot be used for a paused request during interceptions but will be needed upon the end"（§1）。chatbot 轮次被建模为一次 interception，是六类中最接近会话暂停的形态。
- 下一次使用信息：暂停时长估计（§4.4）T̂_INT = t_now − t_call，每迭代重算，不按类型 profile。可靠性："achieves 93% of the performance compared with using an oracle providing exact interception durations"（§4.4）。代价模型 §3.2 Eqs. 1–3 与 §4.2 Eq. 4：WastePreserve = T_INT·C·M，WasteSwap = 2·T_swap(C)·C_batch·M 等。swap 预算（§4.1）：迭代 i 令 T_swap(N_i) = T_fwd(B_i) 求 N_i，即"the number of tokens that can be swapped for free (i.e., hidden behind model forwarding)"；预算在换出与换入之间按三条约束分配。
- 逐出粒度与依据：token 分块、按层流水线："chunk swap-out and swap-in across multiple iterations so that in each iteration, the swap latency can be hidden"（§4.1）。每迭代换出量为 N_i，即链路在一次 forward 内可搬运的量；请求按 waste 排序换出"until we run out of the swap-out budget"，其余按 Eq. 5 保留或丢弃（§4.3；Appendix）。
- 恢复触发：interception 返回时反应式触发："When an API call finishes, InferCept determines how many swapped-out or discarded tokens to swap in or recompute in the next iteration"（Appendix）；换入队列 FCFS 至预算耗尽（§4.3）。T̂_INT 不用于提前换入，提前量按设计为零。
- 相位与期限：多请求耦合仅通过 C_other / C_batch 停顿项与共享预算（§3.2，§4.3）；无期限或 SLO 模型，目标为 normalized latency 与 req/s（§5.1）；无会话相位概念。

#### KVFlow（NeurIPS'25）

- 一手来源：arXiv:2507.07400v1（2025-07-10，唯一版本），HTML 与 PDF 全文已读；NeurIPS 2025 Main Track（DOI 10.52202/085713-4208）。代码 https://github.com/PanZaifeng/KVFlow（Apache-2.0，论文未链接，为 SGLang fork）。
- 负载与状态对象：SGLang 上的多 agent 工作流；对象是 radix tree 中各 agent 固定 prompt 的前缀 KV，CPU 内存作为"secondary cache for storing the fixed prompt KV of evicted agents"（§3.2）；动态后缀总是先被逐出（§3.1）。保护的是跨调用复用的静态前缀，不是会话历史。
- 下一次使用信息：Agent Step Graph 上的 steps-to-execution（§3.1，Fig. 3a），join 取 max+1，either-branch 取 min+1，只追踪"the earliest possible execution step"。由前端在每次 LLM 调用时以 HTTP 元数据嵌入（§3.3）。可靠性：由结构预先确定（图已知），但到执行的时间未估计；分支通过在并发预取数上限内预取所有候选处理（§3.2）。
- 逐出粒度与依据：radix tree 节点级；agent 的 step 值赋给其固定 prompt 末节点并向上传播，共享节点取"the minimum (i.e., least evictable) priority among its children"（§3.1，Fig. 3b）；顺序为后缀先、再按优先级降序。触发与量："When GPU memory becomes constrained"（§3.1），即容量压力，无水位或链路时间约束。
- 恢复触发：携带 step 元数据的请求到达触发下一步 agent 的预取，条件是"if the evictable GPU memory is large enough"（§3.3）。提前量隐含为一个 agent 的执行时长；论文承认"When the current agent's execution time is shorter than the prefetch duration, generation may still be blocked"（§3.2），以 status-aware 重排（Fig. 4）缓解，而非更早预取。
- 相位与期限：多工作流重叠仅通过共享节点取最小优先级与 per-client ID 处理（§3.1，§3.3）；无期限模型，以整工作流延迟评估（§4）；并发过高时"the system can no longer maintain reusable prefix caches, placing it beyond the scope of our optimization"（§4.2）。

#### InfiniGen（OSDI'24）

- 一手来源：arXiv:2406.19707v1（2024-06-28，唯一版本，注 OSDI 2024），HTML 与 PDF 全文已读。代码 https://github.com/snu-comparch/InfiniGen。
- 负载与状态对象：基于 offloading 的长上下文生成（FlexGen、UVM 基线），单请求或小批（4–20，§5.3）。对象是单请求按层 KV，整体置于 CPU："the majority of the tokens for the KV cache are kept in the CPU memory"（§4.1），"we explicitly locate all the KV cache in the CPU memory"（§5.1）；GPU 仅持预取子集与部分 query 权重、部分 key cache（§4.3）。
- 下一次使用信息：forward 内部的观测事件——"At Layer i−1 of the decoding stage, InfiniGen speculates"第 i 层的重要 token（§1，§4.3，Fig. 8）。提前量固定为一个 Transformer 层。非无损：SVD skewing 精确（§4.2），但 token 选择为阈值近似 top-k（§4.3），未选 token 该步不被 attend（"ephemeral pruning"，§1），无 miss 路径。
- 逐出粒度与依据：token 级、按层按 head 组每步选择；量由 alpha 决定（OPT 4、Llama-2 5），平均"less than 10% of the KV cache"，上限 20%（§5.1）；CPU 池容量用户设定，victim 策略基于计数器（§4.4，Table 2）。
- 恢复触发：每个 decode step 于 i−1 层由 KV Selection Controller 触发（Fig. 6）；提前量由模型结构固定，调度器不可调。
- 相位与期限：无。批内各请求独立 KV 池，无会话复用、无 SLO（§5，§7）。

#### ECHO（OSDI'26）

- 一手来源：USENIX OSDI '26 camera-ready，"ECHO: Efficient KV Cache Offloading with Lossless Prefetching for Serving Native Sparse Attention LLMs"（Liu, Chen, Li, Ning 等，SJTU/Huawei），pp. 17–37，全文已读。代码 https://github.com/sjtu-zhao-lab/ECHO（§1），Zenodo artifact（Appendix A）。
- 负载与状态对象：DeepSeek-V3.2 与 DeepSeek Sparse Attention 的长上下文 serving（InfiniteBench 80K–100K token；ShareGPT 测延迟，§2.2，§6.1）。对象是活跃请求的 MLA KV，"in both the host and GPU pools, where the GPU pool serves as a cache for selected tokens"（§3）；indexer K cache 留在 GPU；GPU 池按层管理（§4.1）；host 池 1.8M token 约 1000 GB（§6.1）。
- 下一次使用信息：模型内部观测——indexer 的 top-k 选择。decode（intra-query prefetching，§5.1）以 EMA 预测第 k 高分阈值（α = 0.5，Fig. 7），在 indexer kernel 计算分数期间预取超阈值 token；indexer 完成后"a guaranteed recall is launched for the selected tokens that are not yet in the GPU pool"（§3），因而无损。提前量为同层同步的 indexer kernel 时长，上下文近 100K 且命中率达 90% 时二者可重叠（§2.4，Fig. 4）。prefill 为 inter-query prefetching（§5.2）。
- 逐出粒度与依据：token 级 GPU 池槽位、按层；逐出只改元数据，因"the KV cache of all tokens has already been backed up to the host pool during generation"（§4.2 Free）；优先级计数器形成"LRU-like eviction policy"（§4.2）；量由固定 GPU 池大小与当前选择决定，即容量压力。实测按层命中率 0.88–0.99（Fig. 17）。
- 恢复触发：作为 attention 一部分的按层按步 recall，无请求到达概念；PD 分离部署下 decode 实例先把 prefill KV 收入 host，再"launches decoding to prefetch and recall KV cache of selected tokens"（§3）。
- 相位与期限：无。吞吐导向，自陈 offloading "is most beneficial for throughput-oriented long-context serving"，ITL 开销 +2.7% 至 +27.8%（§6.3，§7）。

#### Learned Prefix Caching（NeurIPS'25）

- 一手来源：NeurIPS 2025 Main Track，"Learned Prefix Caching for Efficient LLM Inference"（Yang, Li, Li, Lloyd，Princeton），papers.nips.cc PDF 全文已读。代码 https://github.com/yangdsh/LPC（§1）。OpenReview 页面因人机验证未能打开，不影响论文内容。
- 负载与状态对象：vLLM 上的多轮 chat（LMSys、ShareGPT、Chatbot-Arena，§4.2）；对象是 GPU 内存中已完成会话的前缀 KV 块："The prefix cache has limited capacity as it uses precious GPU memory"（§2）。单层：全文未描述 CPU/host 副本，逐出即丢弃后重算。数据集平均输入 36–113 token、输出 155–305 token（Table 1），上下文很短。
- 下一次使用信息：学习到的会话是否继续的估计。预测器（§3.2）解析当前与前 N=4 条用户 prompt，multilingual-e5-small 嵌入 384 维，拼接轮数，3 层 MLP 输出继续概率 p；每请求运行一次，按数据集离线训练（§3.3）。时间以衰减折入：p_cur = p·decay / (p·decay + 1 − p)，decay = exp(−(t_cur − t_last)·scale)，scale = 1/平均轮间隔（约 100 s），每 10 s 重估（§3.4.2）。只逐出、不预取："LPC uses a predictor to inform the replacement algorithm about which blocks to evict"（§3.1）。
- 逐出粒度与依据：约 16 token 的 KV 块，按衰减后 p 组成最小堆，"When the prefix cache reaches its capacity, or when memory needs to be reclaimed (e.g., due to expansion of the KV cache)"逐出堆顶（§3.4.1）；量纯由容量压力决定；同一会话所有块共享一个 p，实际按整会话逐出；共享块取 max-pooled 概率（§3.5）。
- 恢复触发：无。miss 时下一请求重新 prefill（§2），无下层可恢复。
- 相位与期限：无。到达模型为指数思考时间、并发会话上限 200（§4.2）；无期限；指标为命中率、TTFT、prefill 吞吐（§4.1）。

### 2.3 恢复与重算混合

#### Cake（ICML'25）

- 一手来源：arXiv:2410.03065v2（2025-02-20；v1 2024-10-04），HTML 全文已读。正确题名为 "Compute Or Load KV Cache? Why Not Both?"（Jin, Liu, Zhang, Mao，U. Michigan）；PMLR 确认 ICML 2025，vol. 267，pp. 28031–28043。早期匿名 OpenReview 提交（cK0kUzocJW）的 venue 页面因人机验证未能打开。
- 负载与状态对象：多轮 chat 与 RAG 的长上下文前缀缓存（§1）；对象是预计算的前缀 KV，存于"high-capacity, low-bandwidth storage layers, such as local disks and remote storage"（§4，Fig. 1）。评估预先计算并存储全部请求的 KV（§5.1），I/O 以按 chunk 与带宽延迟模拟（7/25/32/56/100 Gbps，§5.1，Table 2）。
- 下一次使用信息：无。加载"upon receiving a request"开始（§4 Part 2；App. A 步骤 1）。
- 逐出粒度与依据：不处理。Fig. 1 标题："Cake operates during the KV cache loading phase"；写回交给 LMCache 的异步 put（App. B.1）。
- 恢复触发：请求到达。分割点运行时发现而非预测：compute 指针自 chunk 0 向前 prefill，I/O 线程自末端向后加载，compute 线程以 `IsInCPUMemory` 检查下一 chunk，相遇即停止 I/O worker（§4 Part 2，Fig. 2，Alg. 1 第 3–5 行）；compute chunk 512 token、I/O chunk 128（§5.1）。§5.3 把"an estimation mechanism"与单资源回退列为未来工作，证实无模型化分割。并发：扩展 vLLM token-budget chunked prefill，优先级 decode > non-prefix prefill > prefix-cache prefill（§4 Part 3）；无期限或 SLO，指标为 TTFT（§5.1）。
- 相位与期限：无。唯一并发实验为一个 16K 前缀请求加 22 个突发请求（§5.7，Fig. 6）。

#### CacheFlow（arXiv:2604.25080）

- 一手来源：arXiv:2604.25080v1（2026-04-28，唯一版本，cs.DC，"11 pages, 10 figures"，无 venue），HTML 全文已读。题 "CacheFlow: Efficient LLM Serving with 3D-Parallel KV Cache Restoration"（Nian, Fang, Feng, Wu, Lai）。
- 负载与状态对象：长上下文多轮 chat、RAG、agentic 流水线（Abstract，§1）；trace 为 LMSYS-Chat、WildChat、SWE-Bench（§4.1）。对象是请求的缓存前缀（N_c token），位于"CPU memory, SSD, or remote nodes"（§1，§2）；pipeline-parallel 下各 GPU 另存"boundary hidden states"（§3.2）。层级仅以 I/O 带宽 10/40/80 Gbps 表达（§4.1，§4.3，Fig. 7）。
- 下一次使用信息：无。Alg. 1 只依赖当前 pending batch、各请求 N_c、离线阈值 L_Δ 与指针状态。§5 对比 Continuum（复用预测）与 KVFlow（预取）但均未采用。
- 逐出粒度与依据：不处理，仅恢复。§2 把"offload KV cache to lower tiers ... or discard and recompute"作为背景。
- 恢复触发：请求到达（"given a request with a cached prefix of N_c tokens"，§3）。token 维双指针（chunk C 对齐 FlashAttention block，约 512）与 layer 维双指针（cutover layer ℓ），按离线 profile 的阈值 L_Δ 切换（§3.1，Fig. 3，Alg. 1 第 3 行）；解析界 T* = T_comp·T_io/(T_comp+T_io)，S 级流水线除以 S（§3.2，Eq. 1–2）。batch-aware 调度器：每步 I/O 分给"in descending order of their length to restore"的请求（最大剩余重算代价，Alg. 1 第 7 行，§3.3），compute 推进所有请求（第 11 行）。无期限或 SLO；TTFT 为目标（§4.1）；约 200 ms 仅作动机（§2）。
- 相位与期限：感知的是并发恢复对共享算力与 I/O 的竞争，非到达相位；无 per-request 期限。

### 2.4 双工与实时语音 serving

#### Metronome（arXiv:2607.02640）

- 一手来源：arXiv:2607.02640v1（2026-07-02，Meng, Li），HTML 全文含 Appendix A–D 已读；另核对公开仓库 github.com/19PINE-AI/metronome（README、gateway-go/main.go、metronome/session.py、scheduler.py、kv_manager.py）。
- 负载与状态对象：全双工"real-time interaction models"（Qwen3-Omni-30B-A3B FP8、Qwen2.5-Omni-7B、MiniCPM-o-4.5、Moshi）作为周期实时任务；每会话持续增长的 KV 整段 pinned。§2 "The task model"："A session presents a new audio chunk once per frame; we take the frame period equal to the frame budget B"；可调度条件"iff the per-frame wall time satisfies T_k(N) ≤ B for every k"。
- 下一次使用信息：不需要也不使用——每会话每帧均到期（§2："An interaction session has no lull: every session is due on every frame"）。主机 offload：无。§2 "Recompute, swap, or stay resident"：swap 是"a bandwidth toll that likewise grows"，每帧换出所有到期会话"would move tens of gigabytes per second within minutes"，结论"residency is the only budget-compatible choice"。§8：vLLM/FlexGen 的"state-movement machinery — reclamation, swapping, offload ... — presumes idle gaps that a periodic session never has"。跨周期的 per-session 调度：无。§4：Go gateway "once per tick issues a single batched Step over gRPC for all due sessions"；Fig. 2 "one tick = one batch of all due sessions"；Fig. 3 "with no idle gap, for the whole conversation"。释放偏移或错开：仅作为负载性质出现——§3 "N distinct, phase-staggered real-audio streams"，§5.1 "each session is a distinct, phase-staggered stream, so prefix-cache deduplication cannot inflate capacity"；无处表明服务端利用该偏移。仓库核对：gateway-go/main.go 为单一全局 ticker（`--period-ms`，周期等于预算），每 tick 一次 `client.Step`，phase/offset/stagger/jitter 均不出现。附带说明：仓库早期 Python 原型 metronome/session.py 的 `PeriodicSession` 有 `phase_s`（"wall-clock phase offset within the period"）字段与 EDF `TickScheduler`，但调度器消费外部给定的 `due` 列表、无错开逻辑，README 标其为"earlier synthetic-cost study, superseded by the real end-to-end evaluation"，不属论文实测路径。
- 逐出粒度与依据：整块落在固定滑动窗口 W 之后的 KV block（W=1024 工作点，W=2048 等价，W=512 过小，§5.4，Fig. 11），加 S 个 pinned sink token（S=16 最佳）。Appendix A："The KV manager then frees blocks that fall entirely behind the window, which is what bounds resident memory"；`sliding_window=W` 在模型构造时设定。量由静态 W 决定，非压力或链路预算；有损，§5.4 "Recall beyond the horizon is impossible under any fixed bound"。
- 恢复触发：无（从未换出，被丢弃 token 不可恢复）。应用级"recycling"基线在窗口边界重编码（§4.1，§5.2，Fig. 10），属重算而非恢复。
- 相位与期限：不感知相位——设计前提是所有会话每 tick 同时到期（ρ(t)=ρ0+Nrt 模型的前提，§3.1）。期限模型：每帧预算 B，周期等于 B；deadline-miss 计数器存在，但 §3 指出 worker 对 tick 等待封顶 0.8B 后返回空帧，崩塌期间"the deadline-miss counter reads zero"。接纳：AIMD 按每帧延迟对 B 的目标比例调节（§4.2；Fig. 7 中 2 s 预算取 600 ms 目标；仓库默认 0.7·B，乘性降 ×0.9，加性升 +1）；不驱逐已接纳会话（§5.3："shedding late cannot rescue sessions that are already resident"）。

#### LiveServe（arXiv:2606.22983）

- 一手来源：arXiv:2606.22983v1（2026-06-22；Zhi, Yin, Guan, Zheng, Cheng, Yan），HTML 全文与 PDF 文本已读。注：§3 标题字面为"OmniCast Architecture"（遗留名，正文称 LiveServe）。
- 负载与状态对象：半双工、按 turn 的多轮语音/omni 会话含 barge-in，Qwen3-Omni 与 Ming-Flash-Omni 2.0（§7.1；8×H200）。对象是跨 turn 的每会话多轮 KV（"idle-resident multi-turn KV"），跨 HBM 与 DRAM 管理（Fig. 9）。trace 记录含"session ID, a request timestamp, query and response token lengths, and a turn index"（§7.1）；到达 Poisson 或 BurstGPT，barge-in 为 Bernoulli。全文不出现 full-duplex、per-frame、periodic，未引 Moshi。
- 下一次使用信息（§5.1 "Next-use estimate"，Eq. 4）：T_next,i = T_play,i + T_reply,i，T_play 为剩余播放时长，T_reply "estimates the interval from playback completion to the next completed user input using a per-session moving average when available and a workload-level prior otherwise"。可靠性为估计，且"used only to order eviction candidates, so it need not be an exact wall-clock prediction"；speech start 或 barge-in 时"treats the session as immediate reuse and protects its resident KV from normal eviction"。先验数值未给出。预取触发（§5.2）："LiveServe starts preload at speech start or barge-in, before the full user input reaches the model"；§3：VAD 检测用户开始新话语。接纳条件（§5.2，散文无不等式）："admits an asynchronous DRAM-to-HBM transfer only when the remaining time before LLM-stage execution is enough to hide the transfer cost under current pressure"；"remaining time"如何估计未说明；失败时"skips the preload and lets the normal LLM-stage path load missing KV"。逐出顺序（§5.1）：按 T_next 降序从最远者扫描；会话内"gives suffix blocks higher eviction priority than prefix blocks"（后缀先于前缀，理由是前缀被更多后续 turn 共享）。
- 逐出粒度与依据：block 级、按会话排序，"evicts blocks from that session until enough HBM is released or the session has no evictable blocks left"再转下一会话。量由当前需要释放的 HBM 决定，非链路或窗口预算；触发是压力而非空闲："When HBM pressure requires freeing KV capacity, the KV manager considers only idle-resident multi-turn KV"（§5.1）；§6 保留"the original LRU allocator as a fallback on every allocation"。
- 恢复触发：speech onset / barge-in 事件（§5.2），早于请求到达；提前量由对 LLM-stage 执行前剩余时间的接纳检查决定；预取为"best-effort background work rather than foreground work"，可取消（§6），受保护 KV 总量有上限。恢复量未分级，以"the session KV"为单位，无部分或前缀优先预取。结果（§7.3，Fig. 16 右）："The offloading baseline spends 71.0 ms on on-path KV reload and reaches 302.1 ms text TTFP"，LiveServe "reduces text TTFP to 127.8 ms, a 57.7% reduction"（单个 warm-hit 请求，无聚合隐藏比例）。
- 相位与期限：不控制相位。调度为逐轮严格类优先 U0（underrun，P_i ≤ P_safe，按缓冲升序）> U1（首音，最老优先）> U2（效用 U = β·U_kv − α·C_barge，Eq. 1–3，Algorithm 1）；无 per-request 期限模型，U 是"a lightweight ordering heuristic rather than a global optimum or an exact knapsack solution"；"KV-pressure-aware deferral"（Fig. 8/17）是 Eq. 3 U_kv = K_i·R_occ 偏向驻留大 KV 请求先完成以释放 HBM，非对到达会话的接纳门。HTML 与 PDF 文本均无 stagger/phase/release offset 的调度意义用法。

#### VoxServe（arXiv:2602.00269）

- 一手来源：arXiv:2602.00269v1（2026-01-30，Kamahori 等），HTML 全文含 Appendix A/B 已读。代码 github.com/vox-serve/vox-serve（Apache-2.0）。
- 负载与状态对象：单次每请求 TTS/STS 生成（LibriTTS、VoiceBench；60 s Poisson 到达，§4.1），CosyVoice 2.0、Orpheus 3B、Step-Audio 2 等。状态是每请求 KV 加每请求 detokenizer cache，"initialized in the preprocess method and stored per request"（§3.1）；README API 为单一 POST /generate，无 session ID。
- 下一次使用信息：无；不存在跨请求 KV 驻留决策。全文不提 swap、offload、eviction、preemption；内存压力以静态最大批处理（Step-Audio 为 32，"due to the KV cache's higher memory consumption"，App. A）。期限模型（§2.3，Eq. 2）："the (i+1)-th chunk must be delivered no later than the end of playback of the i-th chunk"；streaming viability 为每 chunk 二元指标。调度（§3.2.1）：startup 阶段优先至首音产出，受并发上限约束；steady-state 请求按"a soft deadline based on its chunk duration and the accumulated timestamp lag"排序，"within 1 second of the deadline"者优先。无接纳/拒绝策略。full-duplex 仅出现于所引题名（PersonaPlex，§4.3.3）。
- d./e. 逐出与恢复：不适用，KV 生命周期即请求。
- 相位与期限：不控制相位；每 chunk 软期限仅用于批内优先排序。

### 2.5 周期与错开

下列工作研究实时强化学习中的错开执行，需按其任务与状态对象判断可比较性。

#### Staggered Asynchronous Inference（arXiv:2412.14355）

- 一手来源：arXiv:2412.14355v1（2024-12-18；Riemer, Subbaraj, Berseth, Rish），HTML 主文与 PDF 附录 A–C 已读。代码 github.com/CERC-AAI/realtime_rl（MIT）。
- 负载与状态对象：单环境实时 RL（Game Boy Pokémon/Tetris、Atari）；"状态"是环境观测；策略为 15/30 层 ResNet DQN，逐调用无状态。无 KV cache、无 transformer。
- 错开对象：同一策略的 N_I 个推理进程在同一条流上按时间偏移，使动作以规则间隔执行；这些进程是一个策略的复制品，不是独立流。§1："even models with high inference times can act at every step using sufficiently many staggered inference processes"；§3："with no offset between them, all additional actions in the environment would be overwritten"，"staggering processes to maintain regular intervals is essential"；§4："a more challenging real-world setup with a single environment"。Algorithm 1 "Maximum Time Inference Staggering" 初始化 delay[p] = ε(p−1)/N_I，观察到新最大延迟时调整其他进程延迟"to preserve the spacing between actions"；Algorithm 2（App. A）用均值。界 τ̄_I ≤ min(τ_θ^max/N_I, τ̄_M)；App. B：N_I* = ⌈τ_θ^max/τ̄_M⌉；§5.3 "N*_I scales roughly linearly with τ̄_θ"。内存/KV 管理：无。§3.2："we run each process on its own dedicated CPU such that resource constraints like memory capacity, and memory bandwidth do not present significant issues"，单 GPU 多进程留作未来工作；§6："Memory bandwidth is a primary bottleneck in allowing for asynchronous computation with current hardware"。App. C 无 LLM、KV 或多租户硬件共享内容。
- d./e. 逐出与恢复：无。
- 相位与期限：错开是有意的相位指派，但对象是一条流内的复制品以填满单一动作时间线；无多会话需求、无内存维度、无期限（无动作就绪时环境取默认动作；τ_M 为环境步时间）。

### 2.6 2026 年新条目（本次检索发现，核对日期 2026-09-21）

以下条目均不在任务单原列表中，按同一字段做压缩分析；除标注者外均读到全文。共同点：全部面向 agent 工具调用或人类批准的不规则空闲窗口，无一处理周期释放、相位指派或 per-update 期限。

#### UNISON（arXiv:2609.09643，2026-09-09，cs.AR；He, Li, Zeng）

- v1；agent 会话，每会话 KV 前缀；两层 SRAM + HBM（Eq. 3），host/SSD 仅见于相关工作。
- Spear：每会话回归间隔 EMA（Eq. 4，gap_end 时更新）加按 turn 索引的 hazard/survival 查找表（Eq. 5–6），复合评分 Eq. 7；明确排除 agent 角色身份与未来到达（§III-A）。估计；5 折 CV 内 0.85 pp（Table IV）。
- 会话粒度逐出（argmax 评分，Alg. 1 第 9–10 行）；触发为容量违约而非空闲；无部分逐出（token 剪枝称互补，§II-C）。
- Tide：gap_start 时以 DMA 预算 B_tokens = Δ·B（Eq. 8）在等待期把 HBM→SRAM 提升，使 KV "already in the fast tier when the next request arrives"（§IV）；Δ 来源仅述"estimated remaining duration"。Tide 未在 vLLM 上实施（"no tier-placement API"，§V-G）。
- 单一 DMA 预算门；无期限（仅 TTFT p50）。

#### Cascade（arXiv:2608.06557，2026-08-06；Adnan 等）

- v1；按请求类（ChatBot/Tool&Agent/Coder/Reasoning）；层级 HBM / DRAM / NVMe（§IV-A）；Aliyun Bailian 生产 trace（§V-A）。
- 每请求延迟预算 B_r = S^TTFT − 离线模型预测的 L_r（Eq. 3–4），每 chunk 按流逝时间刷新（Eq. 5）。
- 各层 LRU 回收；HBM 溢出时抢占预算最大的 prefill 请求，若预算允许则溢至 DRAM（§IV-D）；无预算驱动的降级策略。
- 恢复仅在请求出队入批时（Alg. 1）；显式部分恢复：字节 ≤ M_r,k = [B_rem − Σδ]⁺/Σ(1/B_eff)，余量重算（Eq. 6–7）。
- 类级 TTFT + TPOT SLO（Table III）；无周期期限；链路竞争仅经 B_eff 与保护带 γ。

#### TokenCake（arXiv:2510.18586v4，2026-08-21；EuroSys '27 已接收；Bian 等）

- v1 为 2025-10，2026 修订并接收；多 agent DAG 应用；每请求 16-token KV block；GPU HBM + CPU DRAM（§7.1）。
- 函数调用时长：用户提供的 `predict_time` 与每函数 EWMA 混合（Eq. 1，§4.1）；应用发出 `call_start`/`call_finish` 事件（§6.2）；误差敏感性 §7.5。
- 触发为 `call_start` 事件（主动，Table 2 "FC Start"），受 GPU 压力阈值、有等待请求可用、T_window = T_FC − T_transfer > 0 三重门控（Alg. 1，§4.2）；每请求全有全无。
- 预测式上载"as the predicted completion time approaches"（§4.1）；预算 B_upload（Eq. 3）与每步预留（Eq. 4）；紧迫度项 U（§4.3）；工具提前返回则立即上载。无显式提前量公式。
- 共享压力快照（§3.2）；承认 PCIe 饱和但无仲裁（§7.6）；无 SLO/期限。

#### Adaptive KV Retention at Human-Approval Timescales（arXiv:2608.30830，2026-08-31；Choi, Joshi）

- 因人类批准挂起数分钟至数小时的 agent 请求（τ²-bench）；明确不做每请求等待预测，控制器只用 offered load λ 与离线标定等待样本（§3.4，Fig. 1）。
- 挂起事件时整上下文移至 host DRAM（§3.4）；host TTL t2(λ) 由 GPU 时间机会成本模型给出（Eq. 3，§3.3）；仅在 resume 时恢复，无预取（§3.1）。

#### Ask the Tool, Don't Guess（arXiv:2609.18849，2026-09-16；Liu, Zhang, Li, Zhang）

- 运行中工具经 harness 侧信道发出的进度报告（剩余比例或即将完成信号，§2.2，§3.1–3.2，Table 2），线性换算剩余时间（§4.1）；调用 90% 处中位误差 <10%（§4.2，Fig. 7）。
- 调用中内存压力下逐出（§4）；有 host 层时"refreshes the context one lead time before the predicted return"（§5.1），恢复预算测 2 s 与 0.5 s（§4.2，Fig. 8）；阈值来源未述；整段或部分未说明。

#### 其余条目（压缩）

- MORI（arXiv:2606.00866，2026-05-30；Xia ... Stoica）：agent 程序按最近 5 周期 idleness ι 排序，5 s 控制 tick（Eq. 1，§4.2，§5）；程序粒度降级、GPU 容量恢复时才重载且请求阻塞至提升（§4.3.1）；无预取、无 SLO。ThunderAgent + SGLang v0.5.10；未见代码。
- CacheWise（arXiv:2606.16824，2026-06-15）：以 tool_name/args 聚类预测条件期望复用时间（§5.2），block 级压力触发逐出，无预取（§6.4）。
- CacheScout（arXiv:2605.27744v2 APSys '26；全文版 arXiv:2608.14624，2026-07-16）：一阶 Markov agent 转移矩阵，recency 以调度步计非墙钟（§3.2–3.3）；`BetweenStep` 中预热预测 agent 的 anchor（系统 prompt/工具），非会话历史（§3.4，Alg. 1）。vLLM v0.11。
- ScaleSim（arXiv:2601.21473，2026-01-29）：多 agent 仿真的"invocation distance"（§3.2，Eq. 1–2），明确为序而非时刻；阈值下预取（§3.3）。SGLang v0.5.2。
- Talaria（arXiv:2607.17181，2026-07-19）：固定 τ=1 s 软预留（§3.3）；HKVR 在请求完成或进入工具间隔时异步 checkpoint 对齐 KV block（§3.5）；返回时 H2D 恢复，无预取。SGLang。
- PBKV（arXiv:2605.06472，2026-05-07）：GraphSAGE 预测下一 agent（§4.1）；仅在纯 decode 批中预取、量以一步 decode 可隐藏为限、提前一步（§4.3）。SGLang + HiCache。
- Pythia（arXiv:2604.25899v2，2026-05-14）：`app_metadata` 三个工作流 ID（§4.1）；未来路径 block 留 L3，下一 prompt 预取至 L2 host DRAM 而非 HBM（§4.2.1，Alg. 1）；无时间预测器。
- SuperInfer（arXiv:2601.20309v2，2026-05-18；MLSys '26）：SLO 驱动整请求主动轮转到 Grace DRAM（VLT 指标，§4.2.2，Alg. 1）；DuplexKV 后台急切复制已同步 block，抢占时只搬最后脏块（§4.3.2）；仅单轮负载（App. E.2.3）。vLLM v0.6.6.post1，GH200 NVL2；代码公开。
- Pallas（arXiv:2608.16477，2026-08-17）：蜂窝切换场景，非 KV serving，但为"期限锚定的预取窗口"最近类比：T_w = t̂_HO − t_trig 以网格搜索最小化 α·SIT + (1−α)·早暴露（Eq. 8，Alg. 1）；残差项惩罚超出 B·T_w 的字节（Eq. 5）但无硬上限；多用户竞争评估但未联合分配（§4.5，§6.4）。
- AgentServeSim（arXiv:2606.09613v3，2026-09-05）：模拟器，Retention Plane 仅 protect/release/evict，不建模 host offload 与预取（§3.4，App. E）；策略搜索工具，非竞争者。
- Where Should the KV Cache Live?（arXiv:2609.16215，2026-09-14）：离散事件模拟；block 级 LRU/频率/EWMA 策略；报告预取"uniformly negative"，甚至 oracle "never beats no prefetch on migration traffic"（§V-E）；无期限、无会话时序。该结论限于所述模拟负载，引用前核验其适用条件。
- llmovoice（arXiv:2609.04288，2026-09；SOSP '26）：托管 Realtime API 之上的语音会话 serving；按 turn 非双工（§1，Fig. 1）；每 turn 重建有界文本/音频上下文；无 KV 管理、无 GPU（§3.5，§4）；引 Moshi/Qwen3-Omni 但未引 Metronome/LiveServe。同会议语音 serving 论文，供 scope 对照引用，非 KV 驻留竞争者。
- Stateful Transformers / "Attention Once"（arXiv:2605.13784，2026-05-13，单作者）：周期市场数据流（1–60 s tick，§3.9.1）的持久每会话 KV；仅 GPU 驻留；空闲逐出到盘为未来工作（§6.3）；无预取。周期摄入但无容量机制。
- TOPAS（arXiv:2608.25523）、HyMCache（arXiv:2607.18141v3）、GitHub Copilot characterization（arXiv:2608.00101）：分别为接纳时 GPU↔CPU 前缀迁移无预取、CXL 混合远端层查找时触发预取、turn 边界空闲时间生存预测器（LightGBM，ROC-AUC 0.73 对 >60 s，§9.2）但不建机制（§12）。
- 相邻已知项确认：Continuum arXiv:2511.02230 最新 v7（2026-09-08），另有 UC Berkeley EECS-2026-234 硕士论文版；Waxing-and-Waning arXiv:2608.22704v2（2026-08-29，EMNLP 2026）为请求内 CPU 驻留音频 KV 的 chunk 级召回，非会话驻留；OrbitFlow arXiv:2601.10729v2（VLDB 2026）为单请求按层 ILP 放置；NEO（MLSys 2025，arXiv:2411.01142）确认。FlashGen（ASPLOS 2025）三次检索未能确认该名下论文存在，既有综述中该条目待核。
- 内部相邻工作（不作分析对象）：Conflux / "The Model in the Middle"（arXiv:2607.25792），摘要确认为 position paper。
