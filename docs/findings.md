# 发现与证据缺口

<a id="current-state"></a>
## 当前状态与证据范围

已有材料包括历史诊断、源码检查、前处理修复（FINDING-E5）、copy 提交修复（FINDING-T2）、容量工具链功能验证（FINDING-T3）、长程分组验证（FINDING-T4）、全业务 GPU 观测（FINDING-T5）和第二模型按所选周期预算的执行验证（FINDING-T6），尚无公平比较下的正式性能主结果。下表给出其支持范围；设计见[系统设计](system.md)。 当前代码仍有有限前瞻准入、排队和固定 cohort 的历史工具路径；远端最新设计要求的最大上下文规划、计划版本切换及开放到达拒绝协议尚未全部对齐。已有诊断不表示本轮三组正式实验已可完整执行。

| 候选机制 | 已有依据 | 仍需完成的证据 |
| --- | --- | --- |
| 释放偏移调度 | 已检查的源码包含绝对目标网格；历史诊断记录输入处理突发减弱 | 统一时间基准下的用户代价、批处理代价和恢复峰值测量 |
| 有主机副本的部分 KV 逐出 | 源码路径及有限时程诊断支持减少 空闲期驻留 | 匹配工作量下的达标承载能力；覆盖缺口与并发正确性 |
| KV 预取 | 独立 Session Manager 已执行未来 tick 恢复计划；多成员 group 的预算封顶、生命周期与窗口约束准入有实际验证。长程诊断暴露恢复成本预测偏乐观，见 FINDING-T4；全业务设备观测见 FINDING-T5 | 正式成本标定、不可行计划处理、高压并发、观测开销及可复现净延迟收益 |

<a id="evidence-scope"></a>目前登记的相关依据主要是来源不完整的历史诊断与源码审计：诊断材料用于形成待检验假设，正式性能主张须依据匹配协议下的有效测量；源码审计能够解释所审路径，不能代替并发正确性验证或性能测量；历史日志可复算也不自动意味着运行可重建。每个 `EVIDENCE-*` 的模型、平台、配置与可重建程度由 [证据索引](agent/evidence.json) 解析；最终实验配置与指标见 [实验设计](experiments.md)，当前未测维度仍是证据空缺。

<a id="paper-relevant-findings"></a>
## 论文相关发现

以下观察按其共同回答的研究问题分组，可用于规划论证；形成正式主张仍需相应证据。

**容量动机与资源统计**

| 发现 | 观察与限定 | 依据 | 待补 |
| --- | --- | --- | --- |
| <a id="finding-d1"></a>FINDING-D1 | 历史记录报告 GPU KV 池接近耗尽而周期计算仍有余量的配置点；支持继续检验容量动机，不足以给出公平协议下的可行区间或普遍结论 | `EVIDENCE-LEGACY-BASELINE`（历史诊断，复现资格受限） | [实验一受控容量扫描](experiments.md#capacity-experiment)，同步观测实际分配、模型进度、排队与计算 |
| <a id="finding-d2"></a>FINDING-D2 | 不同会话数与上下文组合在接近相同总 KV token 数时触及池边界，提示固定模型几何下以字节需求解释容量；共享、碎片、目标预分配与实际历史长度仍需单独记账 | `EVIDENCE-LEGACY-BASELINE`（历史诊断） | 实际物理分配与状态字节的对应及预测误差 |
| <a id="finding-d5"></a>FINDING-D5 | 可用 KV 池受模型权重、activation 与运行时保留空间影响，应使用实际池预算与分配轨迹而非设备标称显存；数值依赖运行配置 | `EVIDENCE-LEGACY-BASELINE`（资源统计解释） | 正式配置下的内存分解 |

**需求分散与计算取舍**

| 发现 | 观察与限定 | 依据 | 待补 |
| --- | --- | --- | --- |
| <a id="finding-d3"></a>FINDING-D3 | 分散释放可能减小批量并增加模型迭代或权重访问，也可能减少同时驻留的状态与恢复突发；不能由输入侧观察推断恢复带宽已被平滑，该取舍是需要消融的解释而非一般定律 | `EVIDENCE-LEGACY-BASELINE`（输入侧诊断由 FINDING-H1 持有） | 固定工作量的批形状、GPU 工作与双向传输对照 |
| <a id="finding-h1"></a>FINDING-H1 | 历史比较记录显示偏移释放分散了输入处理需求；原始目录已按清理纪律移除，只保留历史诊断摘要，不具备当前正式来源资格，未测恢复带宽峰值或用户结果延迟 | `EVIDENCE-H1-COMPARISON` | 匹配对照与端到端事件关联 |

**驻留节省与恢复代价**

| 发现 | 观察与限定 | 依据 | 待补 |
| --- | --- | --- | --- |
| <a id="finding-h4"></a>FINDING-H4 | 历史轨迹摘要中逐出后的 GPU KV 占用呈较低锯齿形态，支持该路径能回收空闲状态占用；原始目录已清理，有限轨迹不证明长期有界，工作量差异使其不能直接成为容量提升主结果 | `EVIDENCE-H4-RESIDENCY` | 给定会话分布与观测期限下的达标容量、主机开销与失败边界 |
| <a id="finding-h5"></a>FINDING-H5 | 计算等待按需恢复完成时，传输及相关排队进入依赖路径；其他输入工作是否与之串行应由实际依赖判断，装载发起至完成上报的窗口可能包含引擎等待，不能当作纯链路占用 | `EVIDENCE-H5-CRITICAL-PATH`（历史诊断及路径解释） | 提交、DMA、完成上报与再调度的分解及可重叠部分 |

**实现可行性与验证缺口**

| 发现 | 观察与限定 | 依据 | 待补 |
| --- | --- | --- | --- |
| <a id="finding-h3"></a>FINDING-H3 | 所审路径在 idle 后解除请求引用、逐出选定状态，并在后续使用中组合 GPU 连续前缀、主机回载与缺口后重算；不代表共享、在途复制、取消和全部停止条件下的完备证明，历史保持还依赖参考输入与生成保留语义 | `EVIDENCE-H3-KV-EVICTION-SEMANTICS`（源码审计） | 策略整合的性能价值证明 |
| <a id="finding-h7"></a>FINDING-H7 | 已检查的源码包含主机状态提前装入、容量不足延后与后续正常复用的路径，目标先分配、完成后发布索引；缓存仍可能在使用前被替换，不足以宣称所有并发回退均已验证 | `EVIDENCE-H7-PREFETCH`（历史性能原始数据不完整，源码只补语义审查） | 需求超越、重复恢复、引用生命周期、高压竞争与净延迟实验 |

<a id="diagnostic-appendix-fairness-and-measurement"></a>
## 诊断附录：公平性与测量

本附录保留后续实验必须知道的测量限制和可追溯观察，按测量问题分组。

**事件与进度关联**

| 发现 | 教训与限定 | 依据 |
| --- | --- | --- |
| <a id="finding-b1"></a>FINDING-B1 | 周期调用可以继续而会话不再产生新模型进度，活性与已处理输入必须独立观测 | `EVIDENCE-LEGACY-BASELINE` |
| <a id="finding-b2"></a>FINDING-B2 | 缓冲取出结果缺少归因当前输入的身份，调用返回也早于本次完整模型执行；用户可见延迟需要新的事件关联 | `EVIDENCE-H2-METRICS` |
| <a id="finding-f7"></a>FINDING-F7 | 生成超过消费会积累未交付输出，需要成对记录生成与消费进度；backlog 不能单独代表内容年龄 | `EVIDENCE-H2-METRICS` |
| <a id="finding-h2"></a>FINDING-H2 | 所审 RPC 延迟、成功字段和消费计数具有实现相关语义，不能代表当前输入的完整模型工作或应用 QoE；定义统一由 [测量语义](experiments.md#measurement-semantics) 持有 | `EVIDENCE-H2-METRICS` |
| <a id="finding-c1"></a>FINDING-C1 | 所审引擎接口未显式接收应用时间要求，不能由迭代事件推断应用周期或未来 deadline；该判断限于本仓路径，核验入口见 [动态边](agent/dynamic-edges.json) | `EVIDENCE-LEGACY-BASELINE`（历史接口诊断） |
| <a id="finding-t1"></a>FINDING-T1 | 可重建诊断验证了独立 manager/copy 线程的执行路径及 GPU copy 关联；捕获的 KV memcpy 字节与实际提交量一致，CPU 控制窗口与设备活动时长不同。多层不连续块的独立 GPU 往返测试逐元素一致；这些验证不等于完整模型语义、deadline 或容量收益证明 | `EVIDENCE-COPY-SUBMISSION-FIX`、`EVIDENCE-WHOLE-RUN-PROFILE`；当前设备观测见 FINDING-T5；早期诊断保留为历史记录 |

**公平性与比较资格**

| 发现 | 教训与限定 | 依据 |
| --- | --- | --- |
| <a id="finding-a1"></a>FINDING-A1 | 历史诊断中跨会话串行输入准备可以先限制负载，容量实验应隔离该因素 | `EVIDENCE-LEGACY-BASELINE` |
| <a id="finding-a2"></a>FINDING-A2 | 保持单会话顺序、并行处理不同会话是针对已观察串行瓶颈的实现修正；共享 runtime 竞争仍可能影响尾延迟，不能声称所有输入瓶颈已消除 | `EVIDENCE-LEGACY-BASELINE` |
| <a id="finding-c2"></a>FINDING-C2 | 旧对照所用 first-party 系统的生成上限不同，相关旧运行不构成相同模型工作的公平比较；精确参数与控制缺口见 [生成工作量差异](experiments.md#executed-decode-difference) | `EVIDENCE-LEGACY-BASELINE` |
| <a id="finding-c3"></a>FINDING-C3 | 所审逐出实现固定调度模式，但这不是异步调度必然不安全的证明；主路径与 utility 触发路径不同，主路径保护检查不能推广到全部停止与传输场景，正式消融需要等价调度控制及引用生命周期验证 | `EVIDENCE-EXEC-MODEL-AUDIT`、`EVIDENCE-LEGACY-BASELINE` |

**执行成本诊断**

下列旧步时长结果来自 `EVIDENCE-STEP-TIMING-RETAINED`（历史诊断）。原始对照目录已按清理纪律移除，现仅保留历史记录；正式比较须重新采集并统一统计定义。

| 发现 | 观察与限定 | 待补 |
| --- | --- | --- |
| <a id="finding-e1"></a>FINDING-E1 | 按“有请求被调度多于一个 token”识别的步中，超过捕获上限者 baseline 200/202、Pilarius 499/507（计数含初始化）；不证明全部 prefill 均在图外，`EVIDENCE-EXEC-MODEL-AUDIT` 解释默认图选择规则但不保证实际批形状与图覆盖相同 | 逐步实际模式、有效测量窗口与跨系统分布 |
| <a id="finding-e2"></a>FINDING-E2 | 旧汇总与结构化记录的 decode 步时长统计定义尚未统一，数值保留在历史记录中，待复算。同步路径的步延迟与异步路径的吞吐归因也不能直接比较；权重带宽解释仍是假说 | 统一统计窗口与工作量，补充 HBM 测量及因果对照 |
| <a id="finding-e3"></a>FINDING-E3 | Pilarius 同步路径旧分解（487 样本）报告 64-token 附近成本台阶及拟合 R²=0.944，周期墙钟归因 1480 ms decode 与 520 ms prefill；归因区间包含等待可能，合计覆盖周期不代表 kernel 满载；单运行且跨系统 cap 与调度模式不匹配 | 传输和 kernel 事件验证，检查台阶是否跨配置保持 |
| <a id="finding-e4"></a>FINDING-E4 | 有限窗口中 62 个被检周期有 58 个符合尾部余量公式、465 组相邻间隔中 464 组符合模差规律，未命中样本尚待解释；该路径诊断净增长为 77 token，与登记配置常数相差 1 token（常数由 [已登记配置](experiments.md#measured-workload)与 `experiments/shared/workload.py` 持有），统计定义差异待修正——修改常数与重跑属后续协议实现工作；候选解释（未满块、备份滞后、段末采样未保留）由 `EVIDENCE-EXEC-MODEL-AUDIT` 关联，主机覆盖更大缺口仍可能引发更长后缀重算 | 未命中样本解释；输入、生成、保留与重算分别记账 |

<a id="finding-e5"></a>**FINDING-E5 — 已消除短音频按固定长窗口计算的默认前处理开销。** 在[登记模型与运行环境](experiments.md#measured-workload)中，旧实现把 2 秒、32,000 个采样点补零到 4,800,000 个采样点后提取特征。当前两个 first-party worker 按本次长度加 STFT 边界补齐，同一输入只计算 32,320 个采样点，仍保留 200 个有效特征帧。锁定环境下的随机信号、静音、末尾脉冲及不同长度批量测试均保持有效特征一致（绝对/相对容差各 1e-6）和音频 token IDs 相同。一次修复后的 8-session、30 秒 GPU 诊断通过验收；完整 CPU 输入处理区间 IS→IE 的 127 个样本实测 p50/p95 为 10/41 ms，旧同配置诊断摘要为 288/462 ms。此为短时诊断对比，不是 GPU encoder 耗时或端到端服务加速；该次旧运行仍受业务中途 profiler 收尾暂停影响；当前控制已由 FINDING-T5 修正。旧问题依据为 `EVIDENCE-AUDIO-FEATURE-PADDING`；历史诊断摘要见 `EVIDENCE-AUDIO-FEATURES-BOUNDED` 和[修复记录](agent/records/2026-09-25-audio-features-bounded.json)。该原始目录因随后修复 copy 提交问题而清理，数值现不可独立复算；数值回归仍可运行，当前执行 profile 由 FINDING-T2 持有。

<a id="finding-t2"></a>**FINDING-T2 — copy 提交的主要额外耗时已定位并修复。** 在[登记模型与共享平台](experiments.md#measured-workload)的短时诊断中，原路径按 block × layer 展开描述符；空闲队列反序返回目标还阻止了连续范围合并。修复采用新目标物理配对、双地址连续合并和有界异步提交。同配置、关闭 GPU profiler 的两次运行各有 31 次 H2D，字节范围均为 112–142.625 MiB；CPU 提交 p50/p95 从 10.84/14.35 ms 降至 2.11/4.12 ms。原路径线程 CPU 与墙钟近似相同，支持描述符提交工作是本次主要成本；解释器锁竞争是独立扰动实验观察到的放大因素。当时的 GPU profile 中 5 次可关联 H2D 从提交到首个 DMA 为 1.04–1.33 ms，其中 112 MiB 的设备活动为 9.56 ms，物理字节一致。此为单次成对诊断，不是净吞吐收益或正式性能结论；故障对照 raw 已按清理纪律删除，优化后的 profiler-off 证据保留，旧截断 GPU profile 已由 FINDING-T5 的全业务观测替代；上述旧设备数值仅保留历史摘要。见 `EVIDENCE-COPY-SUBMISSION-FIX` 与[修复记录](agent/records/2026-09-25-copy-submission-fix.json)。

<a id="finding-t3"></a>**FINDING-T3 — 最大稳定并发的固定预算工具链已有真实执行验证，容量边界尚未测得。** 配对入口已关联固定输入身份、源端可用时钟、计划 deadline 与真实模型完成，保留未提交／未完成输入在分母中，并检查完整并发屏障、排空、逐会话 miss 与连续落后。一次[登记共享平台](experiments.md#measured-workload)上 12-session／4-slot 的功能检查，两系统均实际形成每组 3 个会话；预热后共同观测 6 秒，各 36 个周期输入、零 miss、12 个会话全部排空。其成本配置未标定，仅一个 seed，也未测试失败边界，不能据此声称最大并发为 12 或容量提升。Agent 调试目录及聚合已清理，历史验收摘要见 `EVIDENCE-CAPACITY-TOOLCHAIN-CHECK` 与[验证记录](agent/records/2026-09-25-capacity-toolchain.json)；协议与入口由[实验文档](experiments.md#stable-concurrency-runner)持有。

<a id="finding-t4"></a>**FINDING-T4 — 多成员分组的预算封顶和生命周期已长程执行，恢复时间预测仍需标定。** 在[登记配置域](experiments.md#measured-workload)的共享平台诊断中，合成音频 cohort 实测持续 695.940 秒，16 个会话分批完成，最多同时 4 个，每个 slot 2 个。368 个饱和恢复窗口均停在每组 384 blocks，无预算超量、未关联或未发布的 H2D；174 次有限前瞻 review 均预测可行。但其中 297 个饱和窗口晚于配置的 40 ms 恢复截止，排队至有效状态发布 p50/p95 为 48.02/60.15 ms。1,360 个输入均完成固定文本预算且未错过各自模型周期 deadline；模型 deadline 达标不消除恢复计划偏差。业务 D2H 的 3,408 次提交均发生在对应会话该轮输入处理至模型完成之间，支持增量备份路径已执行。GPU profiler 关闭，以上恢复时长是 CPU 控制观察，不是纯 DMA；成本配置未经标定，分批会话也不等于单会话连续增长同样时长。该结果证明执行行为，并暴露标定与风险恢复缺口，不支持最大并发或吞吐收益。见 `EVIDENCE-GROUP-WINDOW-LONG` 与[长程记录](agent/records/2026-09-25-group-window-long.json)。 后续按实测设置更保守的成本与恢复提前量，保持逐出上限不变的一次复验中，92 个饱和组窗口均按时发布、340 个模型输入全部完成；调试目录已清理，仅保留 `EVIDENCE-GROUP-WINDOW-MARGIN` 与[复验记录](agent/records/2026-09-25-group-window-margin.json)。该复验不构成跨设备成本上界。

<a id="finding-t5"></a>**FINDING-T5 — GPU profiler 已改为全业务开启或关闭，并验证窗口约束准入。** 在相同[登记配置域](experiments.md#measured-workload)的一次合成音频诊断中，capture 在客户端启动前开启、全部会话结束后停止导出。6 个会话均完成，cohort 实测总耗时 46.650 秒；首末设备活动间隔为 43.932 秒，二者不能混为捕获缺失。60 次业务 H2D 全部关联到设备活动，207 次已关联 KV copy 的物理字节均与提交一致。准入数量上限放宽后，第五个会话仍因共享恢复窗口不可行而排队，已有组成员释放后才接纳后续会话。全程采集避免定时收尾在业务中途引入暂停，但不代表 profiler 没有持续开销；正式性能运行仍须关闭或单独标定观测开销。见 `EVIDENCE-WHOLE-RUN-PROFILE` 与[验证记录](agent/records/2026-09-25-whole-run-profile.json)。

<a id="finding-t6"></a>**FINDING-T6 — 第二模型已按所选周期预算通过共享管理路径的实际执行验证。** 按[第二模型接入配置](experiments.md#candidate-model-integration)锁定权重、输入适配器与输出预算后，两个合成音频会话共用一个 slot，在真实 GPU 上完成准入、多周期生成、部分逐出、恢复与资源释放。当前诊断的 14 个输入均生成 8 个文本 token，每会话交付 56 个，所有交付周期均未超预算；14 次 H2D 均完成发布，无组预算超量、晚发布或未完成恢复。生成、交付和运行记录使用同一模型预算的回归覆盖 Pilarius 与 matched resident control。该测试使用 eager 执行和短上下文，尚未验证该模型的长程容量、图执行、其他设备或原生语音输出。见 `EVIDENCE-MINICPM-PERIOD-BUDGET` 与[周期预算记录](agent/records/2026-09-25-minicpm-period-budget.json)。此前接入时的权重、物理 block 几何与前处理数值验证保留在 `EVIDENCE-MINICPM-GROUP-SERVING` 的[历史记录](agent/records/2026-09-25-minicpm-group-serving.json)中；旧预算运行及其可视化已由当前结果替代并清理。

**实验初始状态**

| 发现 | 教训与限定 | 依据 |
| --- | --- | --- |
| <a id="finding-h6"></a>FINDING-H6 | 预加载及其完成屏障用于构造可解释起点，不能计为研究机制；目标长度不自动等于实际长度；操作与失败统计定义见 [初始上下文预加载](experiments.md#initial-context-preloading) | `EVIDENCE-H6-INITIAL-CONTEXT` |

<a id="implementation-audit-boundaries"></a>
## 实现验证与历史审计边界

Session Manager 的当前执行结构见 [系统设计](system.md#session-manager-execution)，功能诊断由 FINDING-T1 持有。新增路径使用 planned tick、独立 copy streams、确认过的主机副本及传输引用；此前的闭包身份错误已由同时提交双向传输的回归测试和重跑修复。当前 planner 已实现显式成本配置下的保守有限前瞻准入、共享 group 窗口封顶与排队重试；未实现一般联合优化或不可行计划的自动修复，性能状态不据此升级。Profiler 会扰动执行，且日志中有外部回调线程初始化警告；已观察的设备活动与字节经过核查，不据此假定捕获完整或零开销。

以下限制对应旧源码检查，用于解释旧测量，不能代表新设计的实现状态。来源见[证据索引](agent/evidence.json)中的 `EVIDENCE-H3-KV-EVICTION-SEMANTICS`、`EVIDENCE-H7-PREFETCH`、`EVIDENCE-EXEC-MODEL-AUDIT` 等条目解析。

- 绝对目标网格中的同步等待可推迟实际提交；旧预取由输入 push 触发，未使用未来 release 信息。
- idle transition 的保留前缀逐出与 utility 入口的固定尾部诊断是不同路径；安全检查不能互相推广。
- 旧选择集合使用固定尾部余量，未与已确认主机覆盖求交；缺口可能引出后缀重算。
- 恢复先分配目标，完成后发布索引；缓存仍可能被替换。
- 所审流式执行存在段末生成保留差异和输入失败处理风险；KV 往返一致不等于完整历史语义已验证。
