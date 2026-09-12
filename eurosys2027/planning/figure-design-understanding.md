# Conveyor 图形设计前的机制理解审计

日期：2026-09-08。历史审计说明：本文记录重画前的理解校正，下文“现有/原图”指被审计的上一版；后续预览与复现契约见 [Figure 1 spec](figure-1-motivated-example.md) 和 [Figure 2 spec](figure-2-design-overview.md)。用途：校正作者反馈后用于绘图的理解，作为各图 spec 的前置阅读；不是问题、机制、协议或 finding 的新 owner。本文是对现有 owner 与源码的阅读映射，涉及当前状态时回到原 owner。**现有两张 SVG 为待替换草稿，本次不继续润色或宣称已通过技术审阅。**

## 1. 图必须解释的科研因果链

依据：[Problem](../../docs/problem.md)、[System](../../docs/system.md)、[Paper outline](../../docs/PAPER.md)。

长期会话的逻辑 KV working set 随交互增长；保存完整历史的要求使“删掉上下文”不能被当作等价实现。会话又只在周期的一部分需要继续执行。服务层可知的下一次使用时刻，使系统有机会安排 idle KV 的 GPU 驻留与恢复：释放过早可能增加恢复/重算，恢复过晚把等待放到关键路径，恢复过早又提前占用稀缺 GPU 空间。释放偏移改变多个会话的需求重叠结构，为这些安排提供稳定时序。

所以图中的科研对象是 **有时间要求的 KV 驻留与恢复决策**。三项候选机制的作用必须可区分：释放偏移改变多会话需求相遇的位置，部分逐出改变物理驻留，预取改变恢复时机。搬运接口、hash 注册、同步执行与观测代码的差异不能各自包装成贡献。

原图的问题并非方块少：它缺少上述决策的输入、结果、依赖与代价。添加更多重复的 Idle 行、更多会话或标签不会补足论证。

## 2. 时间对象不能合并

| 对象 | 必须怎样理解 | 对照入口 |
| --- | --- | --- |
| Period / release offset | 同一会话的重复节奏与周期内位置；稳定网格约束未来输入释放，不给模型执行独占槽 | [Problem workload](../../docs/problem.md#workload-model)；`engines/conveyor/gateway/main.go::handle,tickLoop` |
| Input release / push | 输入变为可提交或进入 worker；input chunk 的处理可以尚未完成 | `tickLoop`；`StreamingEngine.step`；观测 `P` |
| Input processing | 每会话顺序保持，跨会话可并行；该路径提供当前 push-prefetch 可用的提前量 | `stream_server.py::_patch_parallel_ingest`；`IQ/IS/IE/IR/IA` |
| Scheduler admission | 会话重新变 active，但可能仍要等 KV 或重算 | `omni_evict.py::_update_request_as_session`；`omni_state.Registry.on_session_resumed` |
| Compute segment | 一段 prefill/decode 进度；可能在多个 batch/iteration 中推进，跨越其他会话 release | [dependency audit](../../docs/references/vllm-023-execution-and-capture.md)；scheduler trace |
| Idle transition | 该段停止并等待后续输入；不是“某一迭代没调度它”，也不是 frontend 调用返回 | `omni_evict.py::_handle_stopped_request` wrapper |
| Deadline / user-visible output | 独立的评价对象；不能把 period、slot 边界、Step 返回、最后一次 scheduler 日志自动当作交付 deadline | [measurement semantics](../../docs/experiments.md#measurement-semantics) |

实际执行不是 `release=compute_start` 的必然等式。图可以选择简化的例子，但必须明确省略哪些阶段，不能靠移动结束点来使所有会话刚好按 slot 完成。

## 3. KV 不是四态 session 标签

依据：[KV state model](../../docs/system.md#kv-state-model)、[omni_state](../../engines/conveyor/worker/engine_patch/omni_state.py)。

每个剖面至少要在语义数据中区分：

1. 会话是否 active/idle；
2. 逻辑历史中哪些 block 已经产生、哪些是新尾块；
3. 哪些物理 GPU block 有可复用内容；
4. 哪些 block 有已确认主机后备，哪些尚未覆盖；
5. 是否有 D2H/H2D 在途及其源、目标；
6. GPU block 被活动请求或传输持有，还是仅留在可回收的 prefix cache。

可用的关键组合包括：active 且等待缺失 KV；idle 且已逐出中段；idle 且正在预取；idle 且预取已完成、等待下次准入。单一 `Compute/Offload/Prefetch/Idle` 枚举不能表达这些正交维度。

**完整上下文不等于每一步必须再次搬运全部 KV。** GPU prefix 可复用，host-backed 缺口可恢复，没有有效后备的缺口要重算；必须先构造正确历史状态才能执行依赖它的 attention。最新未完整 block 不一定可 hash/备份。

## 4. 单周期动作：触发 → 条件 → 状态变化

| 动作 | 触发与检查 | 真正改变什么 | 必须在图里保留的关系 |
| --- | --- | --- | --- |
| Input release | gateway 绝对网格；同 slot 可包含多个会话 | 当前输入进入处理；不保证立刻计算 | release marker 与服务开始分开 |
| Incremental host backing | 完成的 block 随模型进展被 connector 处理；确认可能滞后 | 主机可恢复覆盖向前推进；此时 GPU 内容可以仍然存在 | D2H 不应只画在 compute 结束之后；已有历史不应每次全部重写 |
| Idle partial eviction | resumable segment 停止、处于 idle；当前主路径还检查调度/组配置 | 先释放 request ownership，再逐出选定 cache blocks；保留 prefix 与实现尾部 margin | host copy 不消失；GPU 所选中段变成可复用空间 |
| Prefetch request | 当前 worker 在 input push 发命令；设计可考虑提前网格触发 | 检查 idle、缺口、host source、在途状态与容量；可能 defer | “知道 next use”到“何时可以发出恢复”之间存在决策 |
| Prefetch issue | 缺口可恢复且通过容量 gate | 分配 GPU 目标、pin 主机源，再排进 connector load event | 传输未完成时已占用目标容量，不能标成可读 KV |
| Prefetch complete | connector 报告传输完成 | 注册可复用 GPU cache 内容并释放临时引用；副本仍在 GPU/Host | 会话仍可 idle；cache 可被正常回收，并非保证保留到 next use |
| Resume / admission | 新输入经过处理到 scheduler | 使用普通 GPU prefix match；清除 deferred 状态 | 预取成功无需特殊执行算法 |
| Demand restore / recompute | 仍缺少可用历史 | 恢复连续 host-backed 缺口；遇不可恢复缺口及依赖后缀重算 | 是 correctness fallback，不能在图中删掉后仍宣称完整覆盖 |

源码映射：[`omni_evict.py`](../../engines/conveyor/worker/engine_patch/omni_evict.py) 的 `_evict_idle_kv`、`_handle_stopped_request`、`_reset_store_cursor` 与 `_update_request_as_session`；[`omni_prefetch.py`](../../engines/conveyor/worker/engine_patch/omni_prefetch.py) 的 `prefetch_kv`、`_capacity_for`、`_issue`、`_retry_deferred`；[`omni_prefetch_transport.py`](../../engines/conveyor/worker/engine_patch/omni_prefetch_transport.py) 的 `enqueue`、`build_connector_meta`、`_complete`。

需要特别纠正的原图细节：

- 固定的一段“compute 后 full-tail offload DMA”不是自动逐出主路径。当前 incremental backing 与 idle eviction 分离，不能为画面整齐发明一个固定复制阶段。
- 主路径尾部 margin 是实现启发式，不等于逐出集合已经严格与 confirmed host coverage 求交。源码在选择/逐出后检查并记录 host coverage；coverage gate 是后续计划的一部分。
- retained prefix 在普通 cache 中可以被回收；图可以画它在成功路径幸存，但不能标为永远 pin 住的 guarantee。
- prefetch 目标在 `_issue` 就分配；内容在 `_complete` 后才进入可命中的 cache。仅凭 `prefetched=True` 表示 issue 接受，不是恢复完成。
- deferred prefetch 由其他 idle eviction 后的 hook 重试；这是“一个会话释放容量支持另一个会话预取”的直接因果边。当前不是 deadline 排序的全局恢复调度器。
- deferred 在自身 admission 时取消；已经在途的预取是另一个状态，不能说所有 input overtaking 都撤销了 DMA。

## 5. 资源账要先成立，曲线才能画

图中“GPU 占用”至少有三种可能口径，必须选择而不能互换：

- 保存了有效 KV 内容的物理 blocks，包括 cached-free 内容；
- 被请求/传输引用、当前不可回收的分配；
- 为达到准入状态所需的工作集，包括提前恢复所需目标空间。

`free(request)` 释放所有权与 `evict_blocks` 使缓存内容失效不是同一件事。预取完成后释放临时引用，也不表示内容已经离开 GPU。若图把它们都编码成“蓝色面积减少”，读者会得到错误的容量模型。

构图阶段应先列出每个时刻：执行中的完整历史、预取在途目标、已预取但尚未使用的 cache 内容、idle prefix、可能保留的 fresh tail，再计算所选择口径的 aggregate。同一物理 block 在多种角色出现只计一次；共享 prefix 需要去重。模型图可明确假设会话历史不共享，但不可以在真实 trace 中直接把 request-held 总和当作唯一物理占用。

资源上的因果与代价：

- 部分逐出降低空闲期间驻留；不保证单个完整工作集停止随上下文增长。
- 预取缩短准入后的恢复等待，但越早发出，目标空间占用越早开始；它也可能被普通 cache replacement 提前回收。
- 增量 D2H 主要推进新产生的历史后备，H2D 恢复可能每周期重复搬运被逐出的旧历史，两方向流量并不对称。
- 错开不减少给定逐出选择下的恢复总字节数；它改变峰值与截止窗口，并可能减少 batch 聚合、增加权重读与迭代成本。
- 多会话恢复共用有限链路；只画四条独立 H2D 箭头而不检查时间窗口与资源冲突，不能说明恢复可行。
- 会话 compute segment 重叠可以来自同批/交错执行，不是每个会话占有一台独立 GPU。源 trace 已可见同一 scheduler step 推进多个会话；没有必要为展示这一事实增加 GPU kernel 的虚构持续时间。

## 6. 当前实现、候选设计与证据分开

| 项目 | 源码/owner 支持 | 图能怎样使用 |
| --- | --- | --- |
| 绝对 release grid | gateway 固定网格；实际 Step/输入处理可能迟到 | 画 scheduled release，执行窗口可偏移与重叠 |
| 在整个 idle 区间中提前预取 | [Paper outline](../../docs/PAPER.md) 的改进计划；当前 worker 是 push 触发 | 用户可授权画候选机制，不应标为当前 measured trace |
| 预取保护/恢复排序/水位逐出 | outline 提议；当前 gate 与 eviction hook 不能等价替代 | 若要加入，必须标明待实现/待验证，不能暗画成现有保障 |
| retained-prefix eviction | 当前主路径有 idle hook；fixed-tail timer 是另一配置 | 主图不混用两套 trigger |
| 完整 host coverage | 当前策略不作普遍保证；尾部缺口与恢复限制见 System / FINDING-E4 | 完整覆盖可作为示例假设；单独表示缺口与 fallback |
| 性能证据 | [Findings](../../docs/findings.md) 与 [Evidence registry](../../docs/agent/evidence.json) 持有 | diagram 不升级为正式结果 |

既有 trace 读取纪律：

- `EVIDENCE-STEP-TIMING-RETAINED`、`EVIDENCE-H4-RESIDENCY` 和 `EVIDENCE-H5-CRITICAL-PATH` 的 retained domain 只能承担诊断参考。此次复查 status/validation 与原始 artifact/export hash，未运行新实验。
- `EVIDENCE-H7-PREFETCH` 不提供本地保留的 raw prefetch performance run；不能从 retained demand reload trace 验证预取净收益。
- `B` 事件是 eager-store cursor 前进，可能包含 dedup/null 跳过，不是已经完成 D2H 字节的直接计数。检查点见 `_traced_store_specs`。
- `E` 的 `host_backed` 是对选中集合的事后查询；不是驱逐前的覆盖许可。
- `L/R` 是 issue/report window，含提交/轮询/调度等待，不是 CUDA event DMA 时长。
- [当前 residency sampler](../../infra/trace/collectors/vllm_scheduler_trace/sitecustomize.py) 优先读 request-owned blocks，否则沿 GPU cached prefix 走；缺口之后的 cached tail 和不属于 request 的在途预取不自动包含在这个值里。它不等价于完整 physical residency census。
- retained Conveyor 没有该连续 sampler，旧 exporter 使用 eviction/reload 事件推估。不能据此前沿补出精确 Host block 地图或完整 allocator total。

## 7. 原图具体错在哪里

| 原图简化 | 丢掉的机制内容 | 后续要求 |
| --- | --- | --- |
| 一相位一会话执行，其余全可逐出 | release 与执行长度的区别、batch overlap | 时间点来自合理事件关系；允许多个会话同时依赖 KV |
| 只挑事件剖面再等距排 | idle 时间、周期分母 | 保持实际比例或明确分段；全文周期在视觉上可见 |
| 直接改为 raw trace 图 | 论文机制例子被实验 profile 绑住，prefetch 主张退成角落备注 | 保留作者指定的 1 s / 4 slots 示例，trace 用作约束，不用作所有图参数 |
| 所有 Host 永远画同样实心覆盖 | backing frontier、fresh tail、coverage gap | 指定某份 KV 怎样增长、复制和恢复；不是重复复制四个图标 |
| compute 后固定全量 offload | 增量 D2H 与即时 idle eviction 的分离 | 画物理块生命周期，不发明延迟阶段 |
| prefetch 完成即 compute | cache-ready 等待、提前驻留代价 | 画有意义的完成到使用间隔，且计入容量 |
| 底部总量几乎固定 | 只由标签推数值、没有物理资源模型 | 选择峰值变化/容量释放/预取接受的因果剖面再算总量 |
| 所有传输和计算互不干扰 | 共享链路、批处理与 deadline 约束 | 至少一处展示“为什么此时安排这份恢复” |
| 两图都展示轮转 | 缺少动机对照和设计决策 | Intro 展示问题/机会，Design 解释如何利用机会 |

## 8. 下一次画图必须携带的信息

作者指定的 1 s、4 slots、4 会话继续有效；每会话 compute 小于半周期，允许局部重叠。其余参数是示意，不自动继承实验配置，也不是论文最终 workload contract。

**Intro 的任务**：让读者看到长期历史要求、GPU capacity 与恢复等待之间的冲突，并理解 next-use timing 提供的机会。可以以相同逻辑 KV 显示全驻留、idle eviction + demand reload、Conveyor planned recovery 的局部对照。若涉及 offsets 独有收益，必须考虑“同步输入 + 引擎内部流水线”这一对照，不能把普通流水线已有的资源收益全归于 offset。理想对照不是未经测量的性能曲线。

**Design 的任务**：保留用户的纵向时间剖面，但选取能回答机制问题的时刻：

- 一个会话仍计算，另一个已完成主机后备、进入 idle 并释放所选 GPU blocks；
- 被释放的空间使另一个会话的预取通过容量 gate；
- 预取在途目标不可读但已占用空间，别的会话继续计算；
- 预取完成进入可复用 cache，该会话尚未到使用时刻；
- 下一次准入利用恢复后的历史并追加新 KV，后备 frontier 再向前推进；
- 一个有代表性的分支说明：容量不足 defer，或覆盖缺口 recompute。不要用许多失败分支淹没主路径。

同一图里让“时间安排 → GPU/Host 块变化 → 全局容量/传输占用”对齐。额外的信息密度来自这些联系；不来自增加术语或装饰。

## 9. 审计范围与未完成事项

已逐模块阅读当前 gateway、worker ingestion/Step/session path、状态 registry、idle eviction、prefetch policy 与 transport、loader、观测 producer/parser/exporter，并对照问题/机制/实验/结论 owner 和论文工作大纲。代码入口使用符号引用以减少行号漂移。

本机没有安装锁定的 vLLM runtime，未在 GPU 上动态验证。外部 scheduler/cache/connector 行为以仓内锁定版本的 source-audit 资料和调用点交叉检查；不能称为已重新验证每个外部依赖分支。尤其需要后续实测确认：高压 prefetch 与 admission overtaking、host store 在途与 eviction、cached-free replacement、真实资源账与 prefetch 净收益。

当前图片及旧 spec 的固定 offload window、单一状态枚举与 occupancy 口径不足，均标为待替换。本次理解审计不改引擎实现、不修改 accepted findings、不再生成一版仅调整外观的图片。
