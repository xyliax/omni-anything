# 问题定义：周期交互中的长期 KV 状态

<a id="background"></a>
<a id="interaction-sessions-and-their-timing"></a>
## 应用背景

持续双工会话允许模型在输出期间继续处理输入，并根据新信息选择回应、沉默或调整输出。本文关注其中按固定 micro-turn 推进、跨周期复用历史的会话。每个周期处理新增输入，并按需要生成输出；具体执行阶段由模型决定。是否存在可利用的空闲区间取决于实际执行时间和 KV 访问。

<a id="why-model-level-full-duplex-is-worth-studying"></a>
<a id="time-sensitive-interaction-tasks"></a>
实时翻译、发言中的语义提示、连续视频中的事件报告都可能要求系统在完整话轮结束前作出决策。固定时间片提供规律的更新机会；这些任务并不证明固定周期是唯一实现，也不证明它总比事件触发更高效。任务依据见[外部调研](references/micro-turn-versus-endpoint-interaction.md)。

| 触发方式 | 对话模型何时工作 | 下一次计算的时间信息 |
| --- | --- | --- |
| 显式消息 | 用户或应用提交消息后处理有限响应 | 通常无法提前确定 |
| 语音端点 | 检测到话轮结束后处理有限响应 | 取决于端点事件 |
| 固定 micro-turn | 每个时间片处理输入并推进状态 | 周期与 phase 给出计划释放时刻 |

原生或级联描述组件架构，双工描述输入输出能否重叠，周期描述计算的释放规律；三者应分别判断。前端定期检测不等于下游对话模型定期计算。

<a id="representative-models-and-work"></a>
代表模型与来源见[外部模型综述](references/full-duplex-model-product-serving-landscape-2026-08.md)。模型例子用于解释计算节奏和历史保留方式，不自动确定实验矩阵或论文范围。

<a id="why-historical-kv-state-can-limit-capacity"></a>
## 容量问题

完整保留历史时，模型为新增上下文位置保存 KV，状态规模随历史增长。时间对齐训练使典型输出量随周期对应的交付时长变化，但不保证每周期计算时间恒定：生成量仍有波动，注意力成本也随上下文、批形状与平台变化。单会话提前完成也不等于 GPU 全局空闲。

全驻留策略将保留历史的 KV 持续放在 GPU，避免缺失状态的恢复等待；其服务能力仍受容量、计算和排队限制。本文检验的命题是：**存在计算预算尚有余量、GPU KV 容量已先限制承载能力的配置域。** 该命题由 [实验一](experiments.md#capacity-experiment) 验证，不能由周期性或模型名直接推出。

<a id="the-gap-in-existing-approaches"></a>
已有系统支持分层缓存、部分逐出、预取以及传输与重算组合。本文需要回答的是：在周期会话中，如何共同安排 phase、逐出量和恢复时机，使这些操作在共享资源约束下带来服务收益。相关工作的具体差异仍需结合方案核验，来源见[外部文献笔记](references/closest-work-gap-analysis-2026-09.md)。

<a id="why-timing-information-matters"></a>
周期使更新反复发生，并让计划释放时刻可提前确定。若应用还允许服务系统选择 phase，就可以分散多会话需求；这一权限不是周期性本身保证的。计划释放不等于实际计算开始，排队、迟到和资源竞争仍会改变执行时刻。phase 调整不增加物理带宽或计算余量。

若恢复需求集中在很短的时段，其余时段空闲的 H2D 链路不能自动转化为更多恢复量。在固定带宽下，扩大周期内可实际用于恢复的时间，才能支持更多 KV 在下次使用前搬回 GPU，并为更大的逐出量提供传输预算；具体安排见[系统设计](system.md#offset-resource-rationale)。

<a id="problem-statement"></a>
研究目标是在保持参考历史语义和给定软实时目标的条件下，利用周期信息降低 GPU 峰值驻留，增加可承载会话数。带宽利用率和平均驻留是解释指标，不能替代容量与服务达标判定。

<a id="workload-model"></a>
<a id="from-model-timing-to-periodic-updates"></a>
<a id="periodic-interaction-session"></a>
## 时间与状态模型

会话 `i` 的周期为 `T_i`，phase offset 为 `phi_i`。其第 `k` 次 tick 为 `r(i,k) = t0 + phi_i + k*T_i`。tick 是周期起点；本周期 soft deadline 取下一次 tick。各时间事件分开记录：

| 记号 | 事件 |
| --- | --- |
| `r(i,k)` | 周期开始，计算获得执行资格 |
| `a(i,k)` | 本周期输入实际提交 |
| `s(i,k)` | 依赖历史 KV 的计算开始 |
| `c(i,k)` | 本周期模型生成完成 |
| `q(i,k)` | 本周期最后一次访问目标 KV |

<a id="service-objective"></a>
### 服务目标

目标为 `c(i,k) <= r(i,k+1)`，即从计划 tick 计量的完成延迟不超过周期。实验直接报告完成延迟和超期情况，不给系统增加允许违约比例或持续落后阈值。`c-a` 可诊断提交后的服务时间，但推迟提交不能使 deadline 随之顺延。首次 phase 对齐等待和后续输入积压需另外记录，测量口径见[实验协议](experiments.md#measurement-semantics)。

会话上下文不得超过配置的最大长度，容量规划按该上限进行，见[最大上下文规划](system.md#maximum-context-planning)。上下文限制不构成任意工作量下的时延保证；周期完成表现由给定负载下的测量说明。

当前分析暂把网络传输视为固定延迟，不据此推断网络抖动或用户可见延迟。不同输出路径应明确完成事件与交付事件的映射。

每周期保留的输入和生成位置决定历史增量；控制与沉默位置按模型的历史保留规则计入。输出播放量、主干生成 token 和实际保留位置不能互换。每个位置所需的 KV 字节与实验配置见[实验设计](experiments.md)。

<a id="playback-paced-work"></a>
### 播放节奏与周期工作量

时间对齐训练使生成内容随交互时间线推进。语音例子中，一次更新通常生成对应播放时长的内容，长回复跨多个周期推进；模型计算这部分内容可能快于实际播放。时间对齐监督、生成量及公开阶段耗时见[外部参数核验](references/minicpm-o-4.5-kv-geometry.md#playback-and-execution)。这个例子解释计算与交付速度的差异，不将语音输出冻结为论文范围。

训练形成的是工作量特征，不是每周期 token 数的严格上界。单个文本 token 的发音时长不同，控制位置、生成波动和积压也影响周期成本。论证应使用实际生成量分布和目标负载下的完整执行时间；若声称最坏情况保证，还需另行建立可验证的工作量与执行时间上界，不能把正常语速直接当作硬限制。

<a id="intrinsic-reuse-interval"></a>
### KV 空闲区间

若 `q(i,k)` 到 `s(i,k+1)` 之间没有其他执行访问目标状态，就存在可回收 GPU 驻留的区间。实际收益还要求副本已完成、引用可释放，并能在后续使用前恢复。长计算、积压或重叠访问会缩短这一窗口。

<a id="slack-conditions"></a>
### 显存受限时的全局计算余量

容量论证需要整组已接纳会话的计算余量。令 `ell = q-r`，以下一 tick 为恢复目标且中间没有 KV 访问时，本轮最后访问后可用的时间为 `max(0,T-ell)`。这是单会话的恢复窗口，不能据此推断 GPU 全局空闲。

以下是待校准的条件分析，不是实测结论或新增调度机制。分析例子采用 `N` 个同周期会话、无 KV 共享，每个会话在周期内的最大保留长度为 `L`，每位置占 `kappa` 字节。忽略分配取整，填满 KV 池的长度为 `L_mem=G_KV/(N*kappa)`。

`C_N(L)` 表示指定执行策略下整组周期工作所需的时间，包含输入处理、生成及调度开销，并计入实际分组和批处理，不能把孤立会话耗时直接相加。容量边界处若 `C_N(L_mem)<T`，则仍有 `T-C_N(L_mem)` 的全局时间预算。这是显存先于周期计算预算成为限制的条件；还须独立检查各会话的 deadline。单会话的外部阶段耗时只能解释量级，不能替代该条件在目标并发与上下文长度下的测量。

执行成本模型的校准与验证须分开；拟合只给出待验证预测，最坏情况保证需要经验证的上界。模型、平台、批处理或生成分布改变时须重新检查。增加会话、错开 phase 或重算还需计入恢复成本与干扰，不能把全部余量直接换算为并发增益。

<a id="resource-frontier"></a>
## 资源约束

- **瞬时空间：** 任意时刻的物理分配不得超过可用 GPU KV 容量。共享块只计一次；恢复目标在传输开始前整块预分配，即使内容未就绪也已占空间。
- **传输时间：** 各会话恢复共享链路和 H2D 调度。有效带宽需包含并发及双向传输影响，不能只用标称值。周期总字节预算满足只是必要条件，还须检查每次恢复窗口。
- **计算时间：** 正常模型工作、重算与其他会话共同占用计算资源。重算只能使用全局可调度余量。

从安全逐出到恢复目标重新分配之间，GPU 才真正节省该部分空间。增加逐出量会增加释放字节，也可能迫使恢复提前、延长重新驻留时间。因此每周期搬运量、平均驻留节省和峰值驻留节省不等价；均匀 phase 也不保证峰值等于平均值。

slot 密度、逐出量、恢复时间及准入规模相互影响，须联合检查容量、传输与计算可行性。容量规划使用配置的最大上下文，不能仅按初始短上下文接纳更多会话；实际驻留仍可随周期变化。

<a id="bandwidth-memory-bound"></a>
### 传输预算与容量收益上界

在同周期、固定历史大小、无 KV 共享的稳态分析中，令 `e_i` 为会话每周期逐出且恢复一次的字节数，`B_eff` 为考虑其他流量后可供恢复使用的有效 H2D 带宽。必要条件是 `E=sum(e_i)<=B_eff*T`，传输预算利用率为 `E/(B_eff*T)`。全量逐出时，`E` 等于全部会话的历史状态；若超过周期传输预算，即使链路全时工作也无法持续恢复。总量满足时，单次恢复仍可能因窗口过短或目标空间不足而失败。因此全量逐出在相应长历史配置下不可行，不是对所有配置的一概判断；部分逐出保留来不及恢复的状态。具体假设数值仅见[实验设计中的容量与传输估算](experiments.md)。

令 `w_i` 为该会话逐出字节在本周期内没有 GPU 分配的平均时长，从实际释放算到恢复目标预分配，故 `0<=w_i<=T`。平均驻留节省为 `sum(e_i*w_i)/T`；相对于固定全驻留基线的峰值节省是各时刻节省量的最小值，因而 `peak_saving<=average_saving<=E<=B_eff*T`。周期乘带宽给出理想上界，不等于必然新增的可用显存；区间长度和重叠决定实际峰值收益，提前预分配会缩短节省时间。

<a id="observability"></a>
验证需关联 tick、输入提交、计算、传输和输出事件，分别测量分配空间、有效内容、主机覆盖、DMA 与调度等待。协议见 [实验设计](experiments.md)，已有证据见 [已有证据](findings.md)。

<a id="terminology"></a>
## 术语表

| 术语 | 定义 |
| --- | --- |
| interaction session | 持续进行并保留交互历史的会话，可跨多个请求、话轮或连接 |
| request / turn | 指定接口层的一次请求／应用交互的一轮；使用时说明层级 |
| micro-turn | 同一交互时间线上的短时间片，可包含输入、输出或沉默；沿用 [Thinking Machines Lab](https://thinkingmachines.ai/blog/interaction-models/) 的术语，具体时长与状态推进由各模型规定 |
| full-duplex session | 输入输出可重叠的会话；本文关注其中按固定 micro-turn 推进的部分，不将周期性定义为所有双工模型的属性 |
| periodic interaction session | 计算按可描述周期释放，并跨周期保留历史的会话 |
| tick / period / deadline | 周期起点／相邻 tick 的时间间隔／本周期期望完成时刻；本文 deadline 为下一 tick，且为 soft deadline |
| phase / phase offset / release offset | 周期内的位置／相对共同时间原点的偏移；后两者指同一量 `phi_i` |
| slot | phase 分配所使用的周期内位置；不预设一个 slot 只能承载一个 session |
| session group | 为组级调度组织的会话集合，可包含多个 session；分组不合并逻辑历史，也不等同于固定执行 batch |
| phase assignment / session-to-slot assignment | 在应用允许的范围内为会话分配 phase；session-to-slot assignment 具体描述会话到 phase slot 的分配，同一 slot 可以承载多个会话 |
| group schedule | 面向 session group 的调度安排；底层状态检查与操作仍可按 session 和 KV block 执行 |
| session manager | 消费 residency plan，维护会话与组的周期进度，协调 KV 准备与请求提交；不负责推理后端的执行调度或 batching 策略 |
| residency planner / residency plan | 负责 admission planning 与 plan revision 的逻辑组件／其输出的组分配、逐出预算与恢复时机安排 |
| KV memory manager | 维护 KV 块分配、有效覆盖与引用条件，执行安全释放、恢复目标分配和完成后的有效状态发布 |
| KV transfer engine | 执行已授权的异步 D2H / H2D 复制并报告完成；不决定逐出预算或组级恢复时机 |
| inference backend | 承担请求执行调度与模型计算的推理引擎（使用 batching 时也拥有其策略）；Pilarius 在其上协调周期请求与 KV 驻留，可替换性以满足对接契约为前提 |
| release time | 计划获得执行资格的时刻 `r(i,k)`，区别于实际提交和计算开始 |
| input chunk | 一个周期携带的新增输入块，单位由模型规定决定 |
| generated-token count / output token cap | 本周期生成量及上限；区别于交付量与实际保留量 |
| playback pacing | 生成进度随输出播放进度推进；时间对齐训练使每次更新通常生成对应时长的内容，本身不表示固定 token cap |
| logical context / historical KV state | 参考执行保留的历史／对应可复用的 attention key/value |
| KV working set | 指定计算或访问窗口需要的 KV 集合；必须说明窗口 |
| GPU-resident KV / allocated KV space | GPU 中有效 KV／已分配物理空间；分配不等于内容就绪 |
| host-backed KV / confirmed host coverage | 已有有效主机副本的状态／其已确认覆盖集合 |
| KV-idle interval | 同一状态相邻使用之间不被执行访问的区间 |
| per-period compute slack | 整组会话完成规定周期工作后剩余的时间预算；区别于单会话 KV 空闲和设备利用率计数，能否容纳额外工作须另行验证 |
| partial KV eviction | 释放选定 GPU KV 的物理空间；不改变参考逻辑历史 |
| incremental host backing | 随新增状态建立主机副本，副本完成与 GPU 空间释放分开处理 |
| restoration / H2D restoration | 本设计中从主机向 GPU 恢复 KV；需要先分配空间，再传输和确认就绪 |
| scheduled KV restoration (H2D) | 按计划时机执行的 H2D 恢复；图中统一使用此动作名称，启动仍需满足时间、空间与传输约束 |
| cyclic KV restoration | 每轮计算后逐出部分 KV，并在下一轮计算前恢复的重复过程；不表示全量往返或固定逐出比例 |
| KV prefetching | 在预计使用前发起恢复；本文按下一 tick 安排的路径区别于提交后预取 |
| recomputation | 用保留的模型输入重建历史 KV；区别于从主机复制 KV |
| retained GPU prefix | 策略保留的历史前缀；不等于整个会话的驻留上限或永久保护 |
| memory multiplexing | 不同会话在各自需要状态时复用有限 GPU 空间；不假定窗口互不重叠 |
| effective KV capacity | 固定 GPU KV 预算在给定工作量、上下文需求与周期服务目标下可支撑的跨会话历史状态容量；通过主机后备和周期复用扩展，不指物理显存或同时 GPU 驻留量增加；收益仍受计算、传输与主机容量约束，须经匹配条件的评估验证 |
| release-offset scheduling | 在应用允许的范围内给会话安排 phase |
| KV-cache capacity limit / KV-capacity-bound | KV 物理容量上限／该容量先限制服务的配置域 |
| Pilarius | 系统名称；实现目录和既有运行文件的 `conveyor` 标识不随论文命名变化 |

<a id="scope"></a>
## 研究范围与来源

研究范围由周期、历史复用和资源条件描述。模型、模态、输出架构、硬件及设备拓扑仍属实验变量；当前原型和已测路径不自动成为最终论文边界。是否使用窗口、压缩或摘要由参考历史策略规定，驻留管理保持给定语义。

容量目标是在给定上下文需求下支持更多并发会话；应用是否裁剪历史与驻留管理正交。完整历史不是采用本设计的前提，也不以“不裁剪历史”作为与其他系统的机制区别。

<a id="sources-and-remaining-background-work"></a>
背景来源包括：[模型与产品](references/full-duplex-model-product-serving-landscape-2026-08.md)、[交互任务](references/micro-turn-versus-endpoint-interaction.md)、[KV 管理工作](references/kv-offload-restore-landscape-2026-08.md)。引用所支持的属性以原始来源为准。
