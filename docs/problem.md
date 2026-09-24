# 问题定义：周期交互中的长期 KV 状态

<a id="background"></a>
<a id="interaction-sessions-and-their-timing"></a>
## 应用背景

持续双工会话允许模型在输出期间继续处理输入，并根据新信息选择回应、沉默或调整输出。本文关注其中按固定 micro-turn 推进、跨周期复用历史的会话。每个周期处理新增输入，执行编码、prefill 与 decode，然后等待后续输入；是否存在可利用的空闲区间取决于实际执行时间和 KV 访问。

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

完整保留历史时，模型为新增上下文位置保存 KV，状态规模随历史增长。周期限制新增输入与可交付输出的工作量，但不保证每周期计算时间恒定：注意力成本仍会随上下文、批形状与平台变化。单会话提前完成也不等于 GPU 全局空闲。

全驻留策略将保留历史的 KV 持续放在 GPU，避免缺失状态的恢复等待；其服务能力仍受容量、计算和排队限制。本文检验的命题是：**存在计算预算尚有余量、GPU KV 容量已先限制承载能力的配置域。** 该命题由 [Q1](experiments.md#evaluation-questions) 验证，不能由周期性或模型名直接推出。

<a id="the-gap-in-existing-approaches"></a>
已有系统支持分层缓存、部分逐出、预取以及传输与重算组合。本文需要回答的是：在周期会话中，如何共同安排 phase、逐出量和恢复时机，使这些操作在共享资源约束下带来服务收益。相关工作的具体差异仍需结合方案核验，来源见[外部文献笔记](references/closest-work-gap-analysis-2026-09.md)。

<a id="why-timing-information-matters"></a>
周期提供三种不同信息：更新反复发生、计划释放时刻可知、应用允许服务系统选择 phase。前两者帮助安排恢复，第三者允许分散多会话需求。计划释放不等于实际计算开始；排队、迟到和资源竞争仍会改变执行时刻。phase 调整不增加物理带宽，也不创造计算余量。

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

目标为 `c(i,k) <= r(i,k+1)`，即从计划 tick 计量的完成延迟不超过周期。允许偶发违约，违约率、持续落后与观测期限由[实验协议](experiments.md#measurement-semantics)确定。`c-a` 可诊断提交后的服务时间，但推迟提交不能使 deadline 随之顺延。首次 phase 对齐等待和后续输入积压需另外记录。

当前分析暂把网络传输视为固定延迟，不据此推断网络抖动或用户可见延迟。不同输出路径应明确完成事件与交付事件的映射。

每周期保留的输入和生成位置决定历史增量；控制与沉默位置按模型的历史保留规则计入。输出播放量、主干生成 token 和实际保留位置不能互换。有限输出缓冲限制长期生成领先，但不能单凭播放速度推出每周期 decode 上限。每个位置所需的 KV 字节与实验配置见[实验设计](experiments.md)。

<a id="intrinsic-reuse-interval"></a>
### KV 空闲区间

若 `q(i,k)` 到 `s(i,k+1)` 之间没有其他执行访问目标状态，就存在可回收 GPU 驻留的区间。实际收益还要求副本已完成、引用可释放，并能在后续使用前恢复。长计算、积压或重叠访问会缩短这一窗口。

<a id="slack-conditions"></a>
### 显存受限时的全局计算余量

作者确认主要论证整组已接纳会话的计算余量；单会话 KV 空闲只是逐出与恢复的前提。令 `ell = q-r`，无中间访问时的 KV 空闲窗口为 `max(0,T-ell)`，不能据此推断 GPU 全局空闲。

以下是待校准的条件分析，不是实测结论或新增调度机制。分析例子采用 `N` 个同周期会话、输入在同一 tick 可用、无 KV 共享，每个会话在周期内的最大保留长度为 `L`，每位置占 `kappa` 字节。忽略分配取整，填满 KV 池的长度为 `L_mem=G_KV/(N*kappa)`。

`C_N(L)` 表示指定执行策略下整组工作所需的时间，包含输入处理、模型执行与调度开销，不能把孤立会话耗时直接相加。固定每周期工作量后，若在给定上下文范围内成立上界 `C_N(L)<=A_N+B_N*L`，且 `L_mem` 在该范围内，则内存上限处剩余时间至少为 `T-A_N-B_N*G_KV/(N*kappa)`。该值为正是存在全局余量的充分条件；达到 `eta*T` 才支持相应比例的余量下界。

仿射上界是待建立的分析前提，周期性本身不保证它成立。拟合参数只能给出待验证预测；模型、硬件、批处理及工作量改变时须重新检查。增加会话或重算还需满足恢复成本、干扰和逐会话 deadline，不能把全部余量直接换算为并发增益。

<a id="resource-frontier"></a>
## 资源约束

- **瞬时空间：** 任意时刻的物理分配不得超过可用 GPU KV 容量。共享块只计一次；恢复目标在传输开始前整块预分配，即使内容未就绪也已占空间。
- **传输时间：** 各会话恢复共享链路和 H2D 调度。有效带宽需包含并发及双向传输影响，不能只用标称值。周期总字节预算满足只是必要条件，还须检查每次恢复窗口。
- **计算时间：** 正常模型工作、重算与其他会话共同占用计算资源。重算只能使用全局可调度余量。

从安全逐出到恢复目标重新分配之间，GPU 才真正节省该部分空间。增加逐出量会增加释放字节，也可能迫使恢复提前、延长重新驻留时间。因此每周期搬运量、平均驻留节省和峰值驻留节省不等价；均匀 phase 也不保证峰值等于平均值。

slot 密度、逐出量、恢复时间及准入规模相互影响，须联合检查容量、传输与计算可行性。长期准入还需覆盖承诺的上下文增长范围，不能按初始短上下文推出整个会话生命周期的容量。

<a id="observability"></a>
验证需关联 tick、输入提交、计算、传输和输出事件，分别测量分配空间、有效内容、主机覆盖、DMA 与调度等待。协议见 [实验设计](experiments.md)，已有证据见 [已有证据](findings.md)。

<a id="terminology"></a>
## 术语表

| 术语 | 定义 |
| --- | --- |
| interaction session | 围绕共同历史持续推进的交互，可跨多个请求、话轮或连接 |
| request / turn | 指定接口层的一次请求／应用交互的一轮；使用时说明层级 |
| micro-turn | 同一交互时间线上的短时间片，可包含输入、输出或沉默；沿用 [Thinking Machines Lab](https://thinkingmachines.ai/blog/interaction-models/) 的术语，具体时长与状态推进由各模型规定 |
| full-duplex session | 输入输出可重叠的会话；本文关注其中按固定 micro-turn 推进的部分，不将周期性定义为所有双工模型的属性 |
| periodic interaction session | 计算按可描述周期释放，并跨周期保留历史的会话 |
| tick / period / deadline | 周期起点／相邻 tick 的时间间隔／本周期期望完成时刻；本文 deadline 为下一 tick，且为 soft deadline |
| phase / phase offset / release offset | 周期内的位置／相对共同时间原点的偏移；后两者指同一量 `phi_i` |
| slot | session manager 分配的 phase 位置；不预设一个 slot 只能承载一个 session |
| release time | 计划获得执行资格的时刻 `r(i,k)`，区别于实际提交和计算开始 |
| input chunk | 一个周期携带的新增输入块，单位由模型规定决定 |
| generated-token count / output token cap | 本周期生成量及上限；区别于交付量与实际保留量 |
| logical context / historical KV state | 参考执行保留的历史／对应可复用的 attention key/value |
| KV working set | 指定计算或访问窗口需要的 KV 集合；必须说明窗口 |
| GPU-resident KV / allocated KV space | GPU 中有效 KV／已分配物理空间；分配不等于内容就绪 |
| host-backed KV / confirmed host coverage | 已有有效主机副本的状态／其已确认覆盖集合 |
| KV-idle interval | 同一状态相邻使用之间不被执行访问的区间 |
| per-period compute slack | 整组会话完成规定周期工作后剩余的时间预算；区别于单会话 KV 空闲和设备利用率计数，能否容纳额外工作须另行验证 |
| partial KV eviction | 释放选定 GPU KV 的物理空间；不改变参考逻辑历史 |
| incremental host backing | 随新增状态建立主机副本，副本完成与 GPU 空间释放分开处理 |
| restoration / H2D restoration | 本设计中从主机向 GPU 恢复 KV；需要先分配空间，再传输和确认就绪 |
| cyclic KV restoration | 每轮计算后逐出部分 KV，并在下一轮计算前恢复的重复过程；不表示全量往返或固定逐出比例 |
| KV prefetching | 在预计使用前发起恢复；本文按下一 tick 安排的路径区别于提交后预取 |
| recomputation | 用保留的模型输入重建历史 KV；区别于从主机复制 KV |
| retained GPU prefix | 策略保留的历史前缀；不等于整个会话的驻留上限或永久保护 |
| memory multiplexing | 不同会话在各自需要状态时复用有限 GPU 空间；不假定窗口互不重叠 |
| release-offset scheduling | 在应用允许的范围内给会话安排 phase |
| KV-cache capacity limit / KV-capacity-bound | KV 物理容量上限／该容量先限制服务的配置域 |
| Pilarius | 系统名称；实现目录和既有运行文件的 `conveyor` 标识不随论文命名变化 |

<a id="scope"></a>
## 研究范围与来源

研究范围由周期、历史复用和资源条件描述。模型、模态、输出架构、硬件及设备拓扑仍属实验变量；当前原型和已测路径不自动成为最终论文边界。是否使用窗口、压缩或摘要由参考历史策略规定，驻留管理保持给定语义。

<a id="sources-and-remaining-background-work"></a>
背景来源包括：[模型与产品](references/full-duplex-model-product-serving-landscape-2026-08.md)、[交互任务](references/micro-turn-versus-endpoint-interaction.md)、[KV 管理工作](references/kv-offload-restore-landscape-2026-08.md)。引用所支持的属性以原始来源为准。
