# KV offload 与恢复系统综述（2026-08）

外部文献整理。Updated: 2026-08-29

本文是截至标注日期的外部系统机制与出版态势整理，不是项目事实源，不定义本项目的 workload、机制或术语；任何内容进入 paper 前必须重新核验原始论文。图内文字沿用各论文自身的表述，未映射到本项目词表。

## 出版态势（截至 2026-08-28）

| 工作 | 状态 | 会议 / 日期 |
| --- | --- | --- |
| Metronome | arXiv-only | arXiv:2607.02640，2026-07-02 首发 |
| CacheFlow | arXiv-only | arXiv:2604.25080，2026-04-28 首发 |
| LMCache | arXiv-only（另有 MLSys'26 非存档邀请报告） | arXiv:2510.09665，2025-10-08 首发 |
| Staggered Asynchronous Inference | arXiv-only（OpenReview 无确认接收） | arXiv:2412.14355，2024-12-18 首发 |
| CachedAttention | 已发表 | USENIX ATC 2024 |
| Pensieve | 已发表 | EuroSys 2025 |
| InfiniGen | 已发表 | USENIX OSDI 2024 |
| InferCept | 已发表 | ICML 2024 |
| FlashGen | 已发表 | ASPLOS 2025 |
| HCache | 已发表 | EuroSys 2025 |
| Cake | 已发表 | ICML 2025 |
| NEO | 已发表 | MLSys 2025 |
| KVFlow | 已发表 | NeurIPS 2025 |
| Learned Prefix Caching | 已发表 | NeurIPS 2025 |
| Mooncake | 已发表 | USENIX FAST 2025 |
| SYMPHONY | 已发表 | USENIX NSDI 2026 |
| Bidaw | 已发表 | USENIX FAST 2026 |
| Strata | 已发表 | USENIX OSDI 2026 |
| OrbitFlow | 已发表 | PVLDB 19(5), 2026 |
| Clockwork | 已发表 | USENIX OSDI 2020 |
| CacheGen | 已发表 | ACM SIGCOMM 2024 |

Concurrent-work 惯例：OSDI/SOSP/EuroSys 的 CFP 都允许 arXiv 先发（EuroSys 2027 明确 arXiv 不计为 concurrent submission），对 concurrent 工作的要求是匿名引用并讨论关系，并没有任何条款允许略过对比实验；ML 会议（NeurIPS）把三个月内上线的工作视为 contemporaneous，不因未对比而拒稿，但仍要求引用与讨论。实务解读：arXiv-only 预印本本身不会否定 novelty，也不意味着必须与其做直接对比实验，但近似度高的预印本是审稿人查引用遗漏最严的对象。

## 逐系统机制

各系统的核心差别是“提前多久、凭什么信号知道某份 KV 将被使用”，以及逐出/恢复的粒度与失败路径。

### CachedAttention（ATC'24）

多轮对话的会话 KV 分层存放；提前量来自调度器队列深度，该量由负载决定，系统无法指定；逐出与恢复以会话为粒度、全有全无。

```text
tiers   GPU HBM ◄─ layer by layer ─► host DRAM ◄─ whole session ─► SSD
signal  the scheduler's queue of waiting jobs = visible future KV demand
        job j executing | job j+1 waiting | job j+2 waiting ...
                          └─ prefetch j+1's session SSD -> DRAM now
pipeline  load layer i+1 (DRAM -> HBM) while layer i computes;
          write freshly produced KV back during the same turn's decode
evict   scan the queue window tail to head: furthest-future session first
miss    recompute the whole history from stored text (positions re-applied)
```

预取窗口长度由 DRAM 容量除以单会话 KV 大小决定；future-based 淘汰对 LRU 的命中率是 86% 对 58%（论文自报）。

### Pensieve（EuroSys'25）

该工作支持部分逐出：先丢头部、保护尾部；恢复在轮次已入批后才开始。

```text
unit    32-token KV chunks; tiers GPU + host DRAM; raw text kept as source
evict   when free GPU slots < 25%: rank chunks by V = rebuild_cost / idle_time
        -> old conversations and LEADING chunks go first, tails protected
restore at batch formation (the turn has already arrived): swap in per
        layer; dropped leading chunks are recomputed from text
attend  custom kernel reads GPU-resident + swapped-in + recomputed pieces
        in place, scattered, no compaction
```

### vLLM swap（内建）

纯反应式：块分配失败时才把整个序列的 KV 换出到 CPU，重新调度时整段换回；全有全无、零提前量。当重算延迟不超过换入延迟的 20% 时选择重算而非换入。

### InfiniGen（OSDI'24）

最典型的推测式预取系统；提前量只有一层，且注意力跑在预测子集上，不是无损保留。

```text
home    the full KV lives in host DRAM; GPU keeps a low-rank sketch
loop    while layer i-1 computes:
          sketch-multiply layer i's partial queries x partial keys
          -> tokens predicted important for layer i
          -> fetch ONLY those tokens' K/V over PCIe
lead    one layer inside one decode step (microseconds of lead time)
note    attention runs on a predicted subset: not lossless retention
```

同族后继：ArkVale（页粒度可召回逐出）、ECHO（原生稀疏注意力模型的无损预取）。

### InferCept（ICML'24）

暂停请求的驻留决策；“知道确切恢复时刻能带来多大收益”的关键对照：用已流逝时间估计暂停时长即可达到精确时长 oracle 的 93%。

```text
event   a request emits an external call (tool, API) -> paused at the
        end of the current engine iteration
decide  per paused request: min(waste_preserve, waste_swap, waste_discard),
        waste = GPU memory held-or-blocked x unproductive time
budget  per-iteration swap volume capped so T_swap <= T_forward: transfers
        ride entirely under foreground compute
resume  external result arrives -> swap back or chunked recompute;
        generation waits until the FULL prior context is present again
```

### FlexGen（ICML'23）

离线吞吐系统：线性规划一次性决定权重/KV/激活在 GPU、DRAM、SSD 间的放置，zig-zag 块调度分摊权重读取，长序列（512 以上）把注意力计算交给 CPU。没有到达事件也没有 deadline，与在线服务不同类。

### SYMPHONY（NSDI'26）

计算-内存分离的多级 KV 存放（五层），提前量来自应用层行为提示（如“用户开始打字”，实测平均提前 5.8-11.3 s），提示可能出错；层优先级清除，无重算路径。

### KVFlow（NeurIPS'25）

多 agent 工作流的前缀缓存管理：从 Agent Step Graph 计算每个 radix-tree 节点的 steps-to-execution，按距离执行还差几步、而不是按实际时间决定逐出与预取；保护的是静态共享 prompt，不是逐周期增长的会话上下文。

### OrbitFlow（PVLDB'26）

SLO 驱动的层级驻留规划，面向活跃 decode 中的请求：

```text
plan    online ILP per batch: pick each request's offload distance
        (every k-th layer's KV lives on host); replan on drift or churn
run     every decode iteration, per layer: a per-request transfer stream
        prefetches the next offloaded layer while the current one computes
write   KV of offloaded layers is generated straight into host slots
overload  infeasible plan -> pause the largest request, evict lazily,
          bank early tokens and release one per SLO interval
```

控制环由正在执行的 decode 迭代驱动；两次使用之间不在 decode 的空闲会话没有可藏传输的逐层计算。

### HCache（EuroSys'25）

存 hidden state 而非 KV（字节约为 KV 一半），SSD 经 GPUDirect 读回后用 GEMM 重建 KV；按层切分使传输与重建无气泡；恢复完全由请求到达触发、整段重建。

### Cake（ICML'25）

恢复与重算的双指针混合，处理请求到达时的长前缀冷启动：

```text
goal    one cold prefill of a long stored prefix, at request arrival
        compute_ptr -> chunk 0, 1, 2, ...      recompute from the front
        ..., n-2, n-1  <- io_ptr               load stored KV from the back
meet    after each engine step: is my next compute chunk already loaded?
        yes -> stop prefilling, go decode; the split point is discovered
why     early chunks are cheap to recompute (short attention), late chunks
        are cheap to load (constant bytes); the pointers meet at the cross
```

分割点是发现出来的而非预测的；其缺口是从头开始的整段前缀，与“前缀与新尾在卡上、缺中段”的情形不同。

### CacheFlow（arXiv 2604.25080）

把恢复统一为沿 token、layer、GPU 三个维度并行的重算与 I/O 混合：batch-aware 双指针调度器在并发请求间联合分配计算与传输，优先执行边际重算收益最大的操作；相对既有方案 TTFT 降低 10-62%。定位是把恢复与重算的混合方案推广到批级工程实现（Cake 的多请求、多维度版本），触发仍是请求到达。

### LMCache（arXiv 2510.09665）

vLLM/SGLang 之下的生产级 KV 缓存层：KV 按内容哈希分块存放于 GPU、CPU、本地盘与远端后端，服务前缀复用与 prefill-decode 分离的跨实例传输；性能依赖批量搬运与计算-I/O 流水线；多轮 QA 等负载上与 vLLM 组合可达 15 倍吞吐。加载由已到达的查询触发（队列等待窗内流水线化）。企业部署数据自报：上下文截断这一常见工程实践会使缓存命中率下降约 50%。

### Staggered Asynchronous Inference（arXiv 2412.14355）

实时强化学习：当推理延迟超过环境动作间隔时，对同一模型并行运行多个错开启动的推理进程，使每个环境步都有动作产出；所需进程数随推理时长线性增长。理论部分论证在序贯交互范式下 regret 最小化不可行，除非有足够的异步算力。与释放偏移同样用相位错开把延迟安排进周期内，但错开的对象是单流上的复制推理，不是多会话的 KV 驻留。
