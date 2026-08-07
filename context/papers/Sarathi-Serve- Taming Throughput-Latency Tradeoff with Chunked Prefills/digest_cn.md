# SARATHI / Sarathi-Serve 中文精读：chunked prefill 与 stall-free hybrid batching

## 文献范围与证据约定

- **[S23] 机制原型：** Amey Agrawal et al., `SARATHI: Efficient LLM Inference by Piggybacking Decodes with Chunked Prefills`, arXiv:2308.16369v1, 2023。固定版本：https://arxiv.org/abs/2308.16369v1
- **[SS24] serving 系统：** Amey Agrawal et al., `Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve`, OSDI '24, pp.117-134。正式版：https://www.usenix.org/conference/osdi24/presentation/agrawal
- 下文严格区分两篇论文。`token budget`、Algorithm 3 的 stall-free admission、TBT-SLO 配置和在线 trace 评估属于 **[SS24]**，不能倒灌为 **[S23]** 的贡献。
- “无”表示论文设计或原文明示不存在该机制；“未提及/未找到”表示两篇论文文本没有足够证据，不能据此推断代码或后续系统也没有。

## A. 机制精确描述

### A1. Chunked prefill 的切块规则

#### [S23] 固定 chunk size，不是 token-budget scheduler

- [S23] 把一个请求的单次 prompt prefill 切成固定的、等计算量的 token chunks；摘要称为 `equal sized chunks`，正文示例为 `1K -> 4 x 256`。切分单位是 prompt token，论文没有词、句子或对话轮次边界规则。[S23 Abstract；§4.2，Figure 6]
- 固定 chunk size `C` 由给定 model/hardware/workload 上的一次性 profiling 和预期 `P:D` 决定：小 `C` 能创造更多 piggyback 机会，但降低 prefill arithmetic intensity 并增加历史 KV 重读；大 `C` 的 prefill 更高效，但能覆盖的 decode 较少。[S23 §4.2；§4.4]
- [S23] 没有 [SS24] 的“每 iteration 最大 token budget `tau`”概念，也没有基于 TBT SLO 的 `compute_token_budget` 算法。[S23 §4 全节]
- 为减少 tile quantization，论文要求 fused linear operation 的总 token 维度，即 `prefill chunk tokens + piggybacked decode tokens`，尽量是 tile size 的整数倍。实验 tile size 为 128；若目标 fused width 为 256、最多有 `B-1` 个 decode，则文中建议实际 prefill chunk 取 `256-(B-1)`。[S23 §4.4，Figure 7；Table 2 的 `1021 prefill + 3 decode = 1024` 示例]
- **最后一个余数块：未在 [S23] 中找到明确规则。** 论文明确的切分示例 `1K -> 4 x 256` 可以整除，但没有给出 `ceil`、padding、余数均摊或“最后一块取剩余 token”公式；Table 2 的 `1021 prefill + 3 decode` 是 fused-width 的 tile-alignment 示例，不是 prompt 尾块规则。因此不能把任何具体 remainder policy 写成论文贡献。[S23 §4.2；§4.4；Table 2]

#### [SS24] 每步 token budget，chunk 取 decode 后的剩余额度

- [SS24] 定义每个 scheduling iteration 的 token budget `tau`，表示该 batch 最多执行多少 token；每个 running decode 消耗一个 token 额度，prefill chunk 使用剩余预算。[SS24 §4.2，Algorithm 3]
- `tau` 不是解析公式直接算出。论文建议：对不同 batch token count 做一次性 profiling，取不违反用户 TBT SLO 的最大 token 数；同时考虑 chunk overhead、tile quantization、pipeline bubble、model/hardware/parallelism，并用 Vidur simulator 选择特定部署下使 capacity 最大的 budget。[SS24 §4.3]
- 运行时 `get_next_chunk_size(R, tau, nt)` 选择当前剩余 budget 能容纳的最大 chunk；因此 chunk 边界是连续 prompt token 的动态边界，并会受当前 running-decode 数量影响。[SS24 §4.2，Algorithm 3 lines 9-15]
- 摘要称 prompt 被切成 `near equal sized chunks`，但 Algorithm 3 只把具体规则封装在 `get_next_chunk_size` 中，没有定义如何均摊余数。**最后 remainder 的精确处理同样未在 [SS24] 论文中找到。** 能确认的只有：每块不得超过当步 leftover budget，直到 `is_prefill_complete`。[SS24 Abstract；§4.2，Algorithm 3]
- 论文实际 capacity 实验一般在 strict SLO 使用 budget 512、relaxed SLO 使用 2048；LLaMA2-70B relaxed 配置使用 1536 以降低 pipeline bubbles。[SS24 §5.1，Figures 10-11 后的设置说明]

### A2. 混批组成与 stall-free admission

#### [S23] decode-maximal batching

- 每个 hybrid batch 由 **一个请求的一个 prefill chunk** 加上尽可能多的 decode tokens 构成；若最大可驻留 request batch 为 `B`，则最多 piggyback `B-1` 个 decode requests。[S23 §4.3；§4.3.1]
- `B` 由显存容量、模型参数、最大 sequence length 和每 token KV 大小给出的容量公式决定；它是 request/KV 容量上限，不是每 iteration token budget。[S23 §4.3.1]
- 当 `P:D` 不平衡时，论文只说可以换 chunk size，或退化为 prefill-only/decode-only batch；没有定义在线 admission、queue priority、preemption 或 fairness policy。[S23 §5.1.3；§6]

#### [SS24] decode-first 的 stall-free batching

- Algorithm 3 的准入顺序明确是：**先放入全部 running decodes；再放入已经开始但尚未完成的 partial prefill；最后才从等待队列 admit new requests。** 新请求还必须同时满足 `can_allocate_request` 的内存条件和 `nt < tau` 的 token-budget 条件。[SS24 §4.2，Algorithm 3 lines 6-20]
- 对 partial/new prefill，scheduler 只放入 leftover budget 能容纳的最大 chunk。[SS24] §1 写 `one (or more) prefill chunks from new requests`，§4.2 正文与 Algorithm 3 caption 也描述加入 `new requests`，因此设计意图允许一个或多个新 prefill；但印刷版伪代码有两处缺陷：line 18 写成 `B <- Rnew`，按字面会覆盖已有 running batch，而不是像 Algorithms 1/2 那样追加；循环内也没有 `Rnew <- get_next_request()` 来推进到下一请求。因此只能由正文确认 admission 顺序和多请求意图，具体循环实现未被伪代码完整定义。[SS24 §1；§2.5，Algorithms 1-2；§4.2，Algorithm 3 lines 13-20]
- 如果 running decode 数本身超过 `tau`，Algorithm 3 没有给出降载、抢占或 budget 修正规则。[SS24 §4.2，Algorithm 3 全文核查]
- `stall-free` 的含义是 ongoing decode 不会为了完整 prefill 而跳过 scheduling iteration；它不表示 prefill 对 TBT 完全零影响。prefill chunk 仍会延长 hybrid iteration，只是 `tau` 把增量 latency 限制在目标范围内。[SS24 §4.2，Figure 9]
- 论文报告 naive full-prefill hybrid batching 可使 TBT 相对 decode-only 增加最多 28.3 倍；chunking 给出更紧的 latency bound。[SS24 §4.2，Figure 9]

### A3. Attention 如何计算

- [S23] 只把 prefill rows 与 decode rows 的 **linear operations** 合到同一 matrix-matrix operation，以共享一次 model-weight fetch。论文明确说 attention `happen separately`：所有 decode requests 的 attention 彼此 batch，prefill chunk 的 attention 另行处理；`attention cost remains unchanged`。[S23 §4.3.1]
- 因而 [S23] 不是一个 fused prefill-decode attention kernel。论文没有报告这两个 attention computation 是否用 CUDA streams 并发，也没有声称其 latency 相互 overlap；能确认的是逻辑上分开计算，不能进一步脑补 kernel launch 拓扑。[S23 §4.3.1]
- [S23] prototype 以 xFormers attention 为实现后端；作者称其在该实验环境优于 PyTorch 2.0 的 flash、memory-efficient 和 math attention variants。[S23 §4.5]
- [SS24] 在 vLLM 基础上加入 paged chunk prefill，支持 FlashAttention v2 和 FlashInfer，并在论文全部评估中使用 FlashAttention backend。[SS24 §4.4]
- [SS24] 只披露 paged chunk-prefill backend，没有说明 hybrid batch 的 prefill/decode attention 是一次 fused kernel 还是多次调用，也没有 CUDA stream/CTA overlap 设计。因此不能把 [SS24] 引作 attention fusion 先例；其明确论证的资源互补与收益机制集中在线性层的 arithmetic intensity/weight amortization。[SS24 §3.1，Figures 4-6；§4.4]

### A4. Chunked prefill 的代价

- 数学计算方面，chunking 不重新执行已经完成 chunk 的 FFN，也没有重新生成既有 K/V。每个新 chunk 只为新 query 做 causal attention；Figure 6 的 mask 保证结果与 full prefill 数学等价。[S23 §4.2，Figure 6]
- 内存流量方面，每个后续 chunk 的 attention 都要从 HBM 重读本请求所有 earlier chunks 的 KV。若共 `N` chunks，[S23] 按总 load 次数表述为第一块 load `N` 次、第二块 `N-1` 次；[SS24] 按额外 reload 次数表述为 `N-1`、`N-2` 次。两种说法一致。[S23 §4.2；SS24 §4.3]
- [SS24] 明确说 attention 的数学 computational cost 不变，增加的是 memory reads；除此之外，小 chunk 还有较低 GPU utilization/arithmetic intensity、kernel-launch 等 fixed overhead，以及不整除 tile 时的 extraneous computation。[SS24 §4.3]
- [S23] 的原型 ablation：chunk 64 使 attention 约 3 倍、整个 prefill 约 5 倍慢；chunk 256/512 把完整 prefill loss 分别限制在 20%/10% 内。chunk 128 的 prefill 虽超过 2 倍慢，组合 decode-maximal batching 后端到端仍最多 1.16 倍于 baseline；chunk 64 端到端大致追平 baseline。[S23 §5.4，Figure 13]
- [SS24] 的 serving-system ablation：Yi-34B TP2 上，chunk 512 的 overall prefill overhead 最多约 25%；budget/chunk 2048 时几乎可忽略。[SS24 §5.4.1，Figure 14]
- 两篇论文都没有把 kernel-launch overhead 单独量化。[S23 §5.4；SS24 §4.3、§5.4.1]

## B. 收益归因

### B5. 收益来自哪里，是否隔离了权重摊销

#### 机制归因

- **线性层权重读取摊销：** decode-only 的小 GEMV/batch 主要时间用于从 HBM 取模型权重；把 decode token rows 与 prefill chunk rows 合成矩阵运算后，同一次 weight fetch 同时服务两类 token，提高 arithmetic intensity，使 decode 的边际成本显著降低。attention 不参与这项共享。[S23 §4.3.1；SS24 §3.1，Figures 5-6]
- **GEMM/tile 效率：** fused token dimension 较大时可形成更高效的 matrix-matrix operation；若总 token 维度不对齐 tile，则会产生浪费计算，因此 chunk 与 decode 数量需要共同考虑。[S23 §4.3.1、§4.4，Figure 7；SS24 §4.3]
- **消除 generation stall：** [SS24] 的 decode-first admission 与 SLO-constrained budget 避免完整新 prompt 暂停已有 decode，使系统能在严格 P99 TBT 下使用更大 batch。[SS24 §3.2，Figure 7；§4.2；§5.2，Figure 12]
- **减少 pipeline bubble：** chunk/budget 使相邻 microbatch 的计算量更均匀，降低 PP stage idle time。[S23 §3.2、§5.3，Figure 12；SS24 §3.3、§5.3，Figure 13]

#### 论文实际给出的分解证据

| 证据 | 隔离了什么 | 数字 | 不能推出什么 |
| --- | --- | --- | --- |
| [S23 Table 2，§4.3.1] | prefill-only、decode-only 与 decode-maximal 单步对照 | decode-only 12.49 ms/token；piggybacked marginal decode 1.2 ms/token | 没有硬件 counter 证明全部差值只来自 weight traffic。 |
| [S23 Figure 10，§5.1.4] | 分 operator runtime | FFN 降低 1.3-1.6 倍；preproj/postproj 降低 1.05-1.38 倍；小 batch 时收益主要来自 FFN | 没有“关闭 weight reuse 但保留同一 GEMM shape”的反事实。 |
| [S23 Figure 12，§5.3] | PP uniformity 的端到端作用 | median bubble time 降低 6.29 倍；TP+PP 比 Orca-style TP+PP 快 1.91 倍 | 组合包含 chunking 与 decode-maximal batching，不能完全拆开两者。 |
| [SS24 Table 4，§5.4.2] | hybrid-batching-only、chunked-prefills-only、combined | combined 在两个维度间取得折中：openchat 为 0.76s/0.14s；相比 chunk-only 的 1.04s/0.17s 降低 TTFT/TBT，相比 hybrid-only 的 0.53s/0.68s 显著降低 TBT、但 TTFT 更高 | 是 scheduler-level latency ablation，不是 weight-read micro-ablation，也不能说 combined 的两项数值都在三者中最优。 |

- **结论：** 有接近权重摊销的局部量化（[S23] Table 2、Figure 10），也有两项系统技巧的 component ablation（[SS24] Table 4）；但没有严格单独关闭“混批权重读取复用”的实验，也没有把 weight amortization、GEMM shape、cache effect 与 stall removal 做完整 factorial decomposition。[S23 §5；SS24 §5.4]

### B6. 收益出现和消失的 regime

- **Chunk size：** [S23] 的环境中 256/512 通常优于 128；64/128 虽创造更多 decode coverage，但 prefill arithmetic intensity 和 KV reload overhead 很高。[S23 §5.1.3，Figure 9；§5.4，Figure 13]
- **P:D 与 batch：** prototype 的理论峰值出现在 `P:D = C/(B-1)`，即 prefill chunks 数刚好覆盖所需 decode iterations。过度 decode-heavy 会先耗尽 prefill chunks，过度 prefill-heavy 会缺少可 piggyback decodes，收益两边都下降。[S23 §5.1.3，Figure 9]
- **Batch size：** baseline decode 会随 batch 变大而更高效，所以 Sarathi 的 decode speedup 随 batch size 增大而下降；但在 [S23] 覆盖范围内仍报告 2.8-10 倍 decode gain。[S23 §5.1.1，Figure 8]
- **Context length：** 长 context 提高 quadratic attention 占比，而两篇工作主要优化 linear operations，因此 [S23] 观察到 speedup 随 sequence length 增大而下降。[S23 §5.1.1]
- **固定-budget 下的 TBT 扰动：** [SS24] 报告 chunked prefill 相对 decode-only 的 latency 增量占比会随 decode batch size 和 context length 增大而下降。这衡量的是固定 budget 下的相对 TBT 扰动，不等同于上一条的端到端吞吐 speedup。[SS24 §4.1-4.2，Figure 9]
- **硬件：** [S23] 报告 A100 的 FLOPs/Bandwidth 约 156、A6000 约 53（忽略 cache），认为 A100 需要更大的 chunk 或更大的 hidden size 才不损失 prefill efficiency。该比较同时更换了模型，不是同一模型的纯硬件 ablation。[S23 §5.1.2，Table 4]
- **SLO regime：** [SS24] 用小 budget 512 换严格 TBT，用大 budget 2048 换更高 prefill efficiency。Figure 12 图注及曲线把严格 SLO 下约 3.5 倍的结果归于 Yi-34B（0.2s，budget 512），§5.2 正文却写成 Mistral-7B（0.1s），两处内部矛盾；图中 Mistral-7B 0.1s 的提升约为 2.6 倍，与 Abstract 一致。Yi-34B 1s、budget 2048 的 1.65 倍在正文与曲线间一致。这里只能转述其 2024 基线结果，并保留这项勘误边界。[SS24 Abstract；§5.2，Figure 12]
- **Arithmetic intensity：** [S23] Figure 4 在 LLaMA-13B/A6000 上显示 prefill 主要算子即使 batch 1 也有高 AI，decode 低两个数量级，约 batch 256 才进入 compute-intensive 区域，但完整模型在 1K context 只能容纳 batch 18。[S23 §3.1，Figure 4]
- **Arithmetic intensity（OSDI 版）：** [SS24] Figure 5-6 用 LLaMA2-70B/4 A100 展示 linear ops 随 batch token count 从 memory-bound 进入 compute-bound；理论约 200 token，实测在高 TP 下因 fixed overhead 约 500-600 token 才转折。[SS24 §3.1，Figures 5-6 及 footnote 2]
- **Tile quantization：** [S23] Figure 7 的 tile=128 实验中，128 到 256 token 的时间从 55ms 到 69.8ms，而 256 到 257 token 反而跳到 92.33ms，即只多一 token 带来 32% 增幅。[S23 §4.4，Figure 7]
- [SS24] 复述同一风险：在某些配置下 chunk 257 比 256 的 prefill time 高 32%，因此 `tau` 不能只由 SLO 决定，还需考虑 tile、PP bubble 和 fixed overhead。[SS24 §4.3]

## C. 边界核查

### C7-C11 结论表

| 编号 | 结论 | 论文证据与边界 |
| --- | --- | --- |
| **C7 Attention KV 读共享** | **[S23] 无；[SS24] 未提及新增机制。** | [S23] 明确把 prefill attention 与 batched decode attention 分开，`attention cost remains unchanged`；唯一共享的是 linear-layer model weights。chunking 反而重复读取同一请求 earlier-chunk KV。[S23 §4.2、§4.3.1] [SS24] 只说每个 chunk 访问 `the same prompt` 的历史 KV，未报告“一次 KV scan 服务多组 query/request”的机制。[SS24 §4.3-4.4] |
| **C8 CUDA Graph / static graph / AOT** | **未提及。** | 两篇均未找到 CUDA Graph、静态执行图、AOT compilation 或 `torch.compile` 设计。[S23 §4.5；SS24 §4.4、Artifact Appendix] [SS24] §6 的 `ahead-of-time prefill recomputation` 是对 APIServe related work 的描述，不是编译；本文只定性提到小 chunk 有 kernel-launch 等 fixed overhead，未单独量化。[SS24 §4.3、§6] |
| **C9 调度自由度** | **有 chunk/budget 与 batch composition；跨请求全局规划和动态设备映射未在论文中找到。** | [S23] 的 `B` 是显存容量决定的上限，`P:D` 是预期 workload 特征；系统据此以及 prefill efficiency/tile alignment 选择 `C`，运行单元是一个 chunk 加至多 `B-1` 个 decode，`B`/`P:D` 不是在线调度器主动控制的变量。[S23 §4.3.1-4.4、§5.1.3-5.1.4] [SS24] 调 `tau`，每步按 running decode -> partial prefill -> new request 组成 batch。[SS24 Algorithm 3] 请求选择只写 `get_next_request`，未定义重排序、未来窗口规划、preemption、request-device mapping 或 per-request cost objective。 |
| **C9 “代价可预估”** | **仅配置期 profiling。** | [SS24] 用 profiling/Vidur 预测不同 batch token count 的 iteration cost并选 `tau`；运行时的计算量 proxy 是总 token 数，不是逐请求 context-sensitive attention cost，也不利用已知未来请求序列做计划。[SS24 §4.3] [S23] §5.3 的 regression cost model只用于 PP 评估模拟器，不是在线 scheduler。[S23 §5.3] |
| **C10 Workload 到达假设** | **[SS24] 在线 Poisson；[S23] 未给随机到达分布。** | [SS24] 从 openchat/arxiv 长度分布生成 trace，arrival time 服从 Poisson。[SS24 §5 Workloads] [S23] 是固定 sequence/batch/P:D 参数扫描与 Zipf-length PP simulation，没有说明 arrival distribution。[S23 §5.1-5.3] |
| **C10 离线/batch/提前已知输入** | **未作为本系统场景研究。** | [S23] 主实验是固定 sequence/batch/P:D 的 controlled throughput experiments，论文没有声明 all-requests-known，也没有把“未来输入已知”转化为调度自由度。[S23 §5.1-5.3] [SS24] 明确面向 online serving；§6 只把 FlexGen 描述为 offline resource-constrained related work，没有 Sarathi-Serve offline/known-future evaluation。[SS24 §1、§6] |
| **C11 增量多轮 prefill** | **未覆盖。** | 两篇模型都是“每 request 一个 prompt prefill，内部切 chunks，然后 autoregressive decode”。[S23 Introduction；SS24 §2.2、§4.1] openchat 数据虽含多轮对话，但每个 interaction round 被作为 separate request；跨轮 KV 保留或只追加新输入的 session 机制未在论文中找到。[SS24 §5 Workloads] |

- 不应把 [SS24] §6 对 APIServe 的一句 related-work 描述算成 Sarathi-Serve 自身能力：论文说 APIServe 采用 Sarathi chunked prefill 做 multi-turn API 的 ahead-of-time prefill recomputation；Sarathi-Serve 本文没有实现或评估它。[SS24 §6]
- 不应把 §6 对 multi-query attention 的介绍算成 C7 的 KV-sharing 贡献；那是模型结构 related work，不是 Sarathi scheduler 机制。[SS24 §6]

## D. 与后续工作的关系

### D12. Orca、vLLM、Splitwise 与 PD disaggregation

#### Orca

- [S23] 把 Orca 看作 iteration-level scheduling：请求可逐 iteration 进入/退出，但 full prefill 与 decode 的 overlap 是到达时序的副作用，且 full prompt 限制 piggyback coverage。作者构造 Orca best/worst case；在 1K 上 best-case 最高 1.11 倍，2K/3K 时接近 baseline，而 Sarathi 报告 1.27/1.25/1.23 倍。[S23 §5.2，Figure 11]
- [SS24] 进一步把论文年份 2024 时的 Orca描述为 FCFS、prefill-prioritizing、支持 hybrid batch；但完整长 prefill 仍会延迟 running decode，因此不能消除 generation stall。[SS24 §3.2，Figure 7]

#### vLLM

- [S23] 只把 vLLM 作为 iteration-level scheduling/KV memory-management 背景，没有 vLLM 实验结果。[S23 §4.1、§7.1]
- [SS24] 基于当时的开源 vLLM 实现，并把论文年份 2024 时的 vLLM描述为 prefill-prioritizing：prefill 与 decode 使用同质 batch而非同一 hybrid batch；PagedAttention 提高可驻留 batch size，但完整 prefill 会造成 TBT stall。[SS24 §2.5、§3.2、§4.4]
- [SS24] 的对比逻辑是：vLLM优先 TTFT/后续 decode batch size，可能牺牲 P99 TBT；Sarathi-Serve先保护 running decode，再用剩余 budget 加 prefill，以 token budget调节 throughput-latency tradeoff。[SS24 §3.2、§4.2、§5.1-5.2，Figures 10-12]
- 上述只代表论文在 2024 年对其基线版本的陈述，不能当作当前 vLLM 状态。

#### Splitwise / DistServe / TetriInfer 与 PD 分离

- [S23] 完全未讨论 Splitwise 或 prefill/decode disaggregation，不能从机制原型引用任何“反 PD”论据。[S23 全文核查]
- [SS24] 承认 disaggregation 能完全消除 prefill/decode interference，并让 full prefill 以最高效率执行，因此 TTFT 可能优于 chunked prefill。[SS24 §6]
- [SS24] 提出的代价有两项：prefill 完成后必须把请求 KV cache 迁移到 decode replica，在缺少高带宽 interconnect 时可能困难；prefill replicas 的 GPU memory capacity 利用不足，因为只有 decode replicas 负责长期存 KV cache。[SS24 §6]
- 论文没有做与 Splitwise/DistServe/TetriInfer 的定量对比，并明确留作 future work。因此准确措辞应是“指出 PD 分离的迁移/内存权衡”，不是“证明 co-location 优于 PD 分离”。[SS24 §6]

### D13. 评估设置与外推边界

#### [S23] 机制原型设置

| 模型 | GPU/方式 | 范围 |
| --- | --- | --- |
| LLaMA-13B | 1 x A6000 48GB，physical deployment | 单 GPU；sequence 1K/2K/3K；主要 chunk 128/256/512，overhead ablation 64-512。[S23 Table 3；§5.1、§5.4] |
| LLaMA-33B | 1 x A100 80GB，physical deployment | sequence 1K/2K/3K，Table 4 使用 chunk 256。[S23 Table 3-4] |
| GPT-3 | 64 x A100 80GB，profile-driven simulation | 8 servers/InfiniBand；TP8 x PP8、Sarathi同配置、8个TP8 replicas；10K requests；length 1K-4K Zipf `theta=0.4`；固定 `P:D=10`、chunk 256。[S23 §5.3，Figure 12] |

- [S23] 单 GPU主实验没有真实数据集或 arrival trace；除 PP simulation 外，论文假设 batch 内请求有相同 prefill/decode token 数，并承认未知 `P:D` 下选最优 chunk 是 future work。[S23 §6]
- [S23] 只研究到 3K（PP simulation 到 4K），明确说 10K-100K context 会因 quadratic attention 带来新挑战。因此不能把其 decode speedup、最佳 chunk 或 linear-layer 占比直接外推到长历史。[S23 §6]
- [S23] 未报告 dtype/precision。[S23 implementation/evaluation 全文核查]

#### [SS24] OSDI serving 设置

| 模型 | 部署 | Attention |
| --- | --- | --- |
| Mistral-7B | 1 x A100 80GB | GQA + sliding window |
| Yi-34B | 2 x A100 80GB，TP2 | GQA |
| LLaMA2-70B | 8 x A40 48GB，TP4-PP2 | GQA |
| Falcon-180B | 2 nodes x 4 A100 80GB，node 内 TP4、node 间 PP2 | GQA |

上述模型/GPU映射来自 [SS24 Table 1]。除 LLaMA2-70B 外，实验使用 Azure NC96ads v4（每机 4 x A100、pairwise NVLink），跨机为 100Gbps Ethernet；LLaMA2-70B 使用 8 x A40。[SS24 §5 Models and Environment]

- 数据集 `openchat_sharegpt4`：prompt median/P90/std = 1730/5696/2088，output = 415/834/101；过滤 total length >8192。[SS24 Table 2；§5 Workloads]
- 数据集 `arxiv_summarization`：prompt median/P90/std = 7059/12985/3638，output = 208/371/265；过滤 total length >16384。[SS24 Table 2；§5 Workloads]
- Arrival time 按 Poisson distribution 生成；指标为 median TTFT、P99 TBT 和满足 SLO 且 median scheduling delay 不超过 2s 的最大 sustainable QPS/capacity。[SS24 §5 Workloads、Metrics；§5.1]
- strict/relaxed P99 TBT SLO 分别是基准 decode iteration latency 的 5倍/25倍；该基准条件是 prefill/context length 4K、decode batch size 32、且没有 prefill interference。绝对值见 Table 3：Mistral 0.1/0.5s、Yi 0.2/1s、LLaMA2-70B 1/5s、Falcon 1/5s。[SS24 §5.1，Table 3]
- Artifact Appendix 说明实现测试于 CUDA 12.1、A100/A40；论文未报告 dtype/precision，也未评估 RTX 3090。[SS24 Artifact Appendix；全文核查]

#### 对 StreamingRL 所关心 regime 的证据边界

- **RTX 3090：没有直接证据。** 两文的最接近单卡数据来自 A6000 48GB、A100 80GB；`B/C/tau` 都依赖显存、FLOPs/Bandwidth、tile 和 model shape，论文自身要求重新 profiling，不能直接搬数字。[S23 §4.2-4.4、§5.1.2；SS24 §4.3]
- **小 chunk：有机制证据，但 serving 证据有限。** [S23] 测到 64 并显示严重 overhead；[SS24] Figure 9 有 budget 256/512 的 incremental-latency结果，但 capacity 主实验主要用 512-2048。[S23 §5.4，Figure 13；SS24 Figure 9、§5.1、Figure 14]
- **长历史：最多约 16K trace filter。** [SS24] 的 arxiv workload覆盖到 total length 16K 上限，但没有 10K-100K streaming history 或反复追加小 chunk 的同 session 评估；[S23] 更明确把超长 context 列为开放挑战。[SS24 §5 Workloads；S23 §6]
- **增量多轮：未覆盖。** openchat 的每一轮是 separate request，不能证明跨轮 KV 保留、追加 prefill 或同一请求的长期 history 行为。[SS24 §5 Workloads]

## E. 150 字内总结

Sarathi 已覆盖按预算切分 prefill、与 decode 混批摊销线性层权重读取，以及在线 SLO 下的 stall-free 调度；两文未报告 attention KV 单次扫描共享、CUDA Graph/AOT 静态专化，也未报告利用提前已知请求做跨请求顺序或设备映射规划。
