# 半成品论文审阅：范围、定义与论证

本文件是修改建议，不是项目事实 owner，也不冻结论文范围或实验矩阵。审阅覆盖当前主稿的 Introduction、Background、Problem Formulation、Design、Implementation、Evaluation Methodology、Evaluation、Related Work、Discussion 和 Conclusion；摘要沿用本轮此前的评审。依据问题、系统、实验和发现 owner 检查文字一致性，未重新审计代码或逐篇核验外部原始论文。

## 总体评价与修改顺序

当前章节骨架可以继续推进：micro-turn 与组件架构已分开，保留策略被作为负载参数，计算空闲和状态复用的关联已有解释，评估问题覆盖收益、代价、因果与边界。正常的半成品空位包括结果、图、算法细节、实验实例和待核验引用；这些空位本身不作为现阶段错误。

优先修复定义与推理，其次校准范围和新颖性，最后压缩重复并润色英文。主线应为：周期更新和跨更新复用产生可利用的驻留窗口；利用时间信息协调 GPU 空间、传输与计算；在相同参考历史和服务标准下验证承载能力。下面 CRITICAL 指应在正式实验和主张定稿之前解决的定义或推理问题，并非要求半成品立即满足投稿完整性。

## R1 · CRITICAL：服务目标、测量起点与相位代价尚未一致

原句：`02b-formulation.tex` 的 “The soft real-time objective is $c(i,k) - r(i,k) \le D_i$”，随后又说 “The latency baseline is the actual submission $a(i,k)$”；`05-evaluation-methodology.tex` 的 “Update service latency runs from actual submission $a(i,k)$ to generation completion”。`03-design.tex` 还写 “steady-state operation adds no user-visible cost”，而 `04-implementation.tex` 明确同步等待可能推迟后续提交。

释放到完成与提交到完成只有在 a=r 时相同，积压不能自动消除这一区别。修改者应明确三个层次：生成侧服务延迟 c-a；释放到提交的等待 a-r；原始输入到相关结果的用户可见延迟。明确达标承载能力由哪些指标共同判定，以及迟到、违约、持续积压和首次对齐的处理。相位设定的用户代价须包括切块与缓冲影响，不能由时序权限或 c-a 达标直接推出零代价。

“generation completion”是已选定的测量事件，但还需要补充沉默、零生成及输出不能逐更新归因时的完成判据。用户交付为常数偏移的假设，应说明对哪些执行路径适用；系统引入的播放排队、缓冲和输出阶段差异需要单列测量或映射。网络与客户端因素的协议边界本身不作为错误，但生成侧结果不足以自动支持完整交付链的端到端主张。

依据：`docs/problem.md` 的服务目标与事件定义；`docs/experiments.md` 的测量语义。主稿与 owner 中共同存在的歧义须先澄清 owner，再同步主稿。

## R2 · CRITICAL：传输预算上界被推成了充分利用与不变收益

原句：`03-design.tex` 的 “As long as each session's eviction depth is capped by its window budget, the link budget is fully used and the total reclaim does not depend on how shares are distributed”。`02b-formulation.tex` 随后由每周期回收字节的界，推测容量扩展主要取决于链路与时序，而非保留策略。

逐出量不超过窗口预算只保证不超额，不保证利用满预算。说明性反例：两个窗口各可恢复 10 单位，可逐出状态分别为 1 与 100；固定等分窗口下实际恢复需求至多为 1+10=11，并非链路总预算 20。这个反例只说明推理所缺的条件，不构成项目测量或对替代算法的性能结论。

应分别定义可逐出字节、实际逐出字节、恢复流量、平均驻留和峰值分配，说明备份及其他传输如何消耗预算。满利用、份额分配无关性、峰值接近均值及保留策略不变性都需要各自的成立条件。恢复流量预算不能单独确定容量扩展，因为恢复后状态占空间的时长也重要。可以保留候选假设；不能依赖未成立的推理排除其他设计。公式未补是正常空位，上述无条件推断应现在修正。

## R3 · MAJOR：全驻留消除的是 KV 恢复等待，不能保证整体服务只在容量上失败

原句：`01-introduction.tex` 的 “the only axis on which it can fail is capacity”；`02-background-motivation.tex` 的 “The policy can fail only on the capacity axis”以及 “Retention semantics survive; timeliness does not”。

GPU 状态全驻留时仍可能由于计算、排队、批处理或输入处理错过服务目标；按需恢复增加等待也不等于必然违约。应限定为：在计算与输入处理仍可达标的工作点，KV 容量可能先限制承载；全驻留避免缺失 KV 的恢复等待。容量动机需要看多会话汇总的计算可行性，不能仅由单会话计算小于周期推出。

## R4 · MAJOR：范围应由复用与时序界定，避免完整历史及话轮级对比造成误读

原句：`01-introduction.tex` 的 “That history grows on a clock”；`02b-formulation.tex` 的 “adjacent updates depend on the same growing history”；`02-background-motivation.tex` 的 “A turn-based request … its state can then step aside as a whole”。

前两句与后文允许窗口或摘要的范围描述未完全一致。跨更新复用是必要性质，增长是加剧压力的一种情形。轮次型会话也可能长期保留历史 KV，周期会话在容量和恢复期限允许时也可以整段 offload；两者真正相关的差异是下一次复用的节奏、提前信息和恢复期限。第三类允许沉默及级联架构的现有说明应保留。共同周期是起始分析模型；不同周期、抖动和状态异构通过模型条件和评估矩阵交代，当前实例不决定论文边界。

## R5 · MAJOR：候选设计、当前实现与验证保证应在一个位置对齐

原句：`03-design.tex` 写 “v1 triggers prefetch by space gating”以及 “evicts only blocks with confirmed host copies”；`04-implementation.tex` 写 “prefetching is currently triggered by input push”和 “fixed tail margin … not yet intersected with confirmed host coverage”。Design 的开头已声明其为候选设计，因此这里是容易被误读的版本混用，不能据此声称代码满足候选规则。

建议用小表对齐每项机制的设计规则、当前实现、缺口与实验资格；其余章节围绕同一版本叙述。满足副本有效性与引用安全的设计不变量、实现路径存在、并发正确性验证及性能收益分别表述。`08-discussion.tex` 的 “Aperiodic input, absent idle intervals, short sessions, or insufficient host capacity degrade the mechanisms to the on-demand path”也应拆开：预测价值减少、收益不足、资源不可行与功能失败不是同一种退化。主机不足时能否重算、继续全驻留或拒绝接纳，必须有明确前提。

## R6 · MAJOR：相关工作的新颖性表述超过现有核验状态

原句：`01-introduction.tex` 的 “No existing route on the residency dimension achieves timely readiness”；`07-related-work.tex` 的 “Their restoration triggers are queue depth or request arrival; none consumes the release times a clocked workload commits”。

已有提前恢复方法可能及时准备状态。应逐项比较信息来源、可获得时刻、状态粒度、逐出规则、相位权限与服务目标，避免以信号不同推出方法普遍无效。Background 的任务例子与固定时间步已有真实来源说明，应补一手引用，并保留增强事件系统也能满足任务的限定。

本次未逐篇重核外部论文，不能认证所有系统的具体边界。现有笔记中 InferCept 涉及暂停期间驻留动作选择与暂停时长估计，主稿将其统一放入混合恢复重算类也应核对，避免分类遗漏决定性的机制。优先核验最接近的周期服务与 next-use KV 管理工作，然后冻结本文的增量定位。

## R7 · MAJOR：研究对象和优化目标还需独立说明

原文 Background 直接进入 “Historical KV and the Capacity Problem”，没有解释 key–value 缓存与 attention 历史复用的基本关系。Formulation 以 “This section fixes the objects and the objective”开头，但目前主要列服务不等式和资源约束，没有独立定义最大化什么。

Background 补简短定义：历史 KV 用于后续 attention 复用；应用保留的逻辑状态、GPU 驻留状态和主机副本不同；复制不等于释放空间。Formulation 明确给定模型、保留策略、生命周期分布与观测期限，目标是最大化满足统一服务标准的承载能力，受空间、计算、恢复和合法时序变化约束。长期增长负载的容量是有限观测域中的能力，不能默认为无限时长稳定。

## R8 · MAJOR：贡献应围绕结果与因果设计，章节分工应减少重复

原句：`01-introduction.tex` 将 “an evaluation protocol with matched generation work and a uniform service verdict”列为贡献。匹配工作与统一判定是可信比较的要求；它们本身通常不足以成为技术论文的独立贡献。

贡献建议围绕资源问题刻画、时间信息驱动的联合驻留恢复设计、经验证的承载收益及边界；资源模型是否独立列贡献由留出预测证据决定。Design 需要下一轮补充可执行决策：输入、触发、选块/定深度、空间与期限检查、预取竞态及回退，不宜仅重复机制名称。

Introduction 聚焦动机、矛盾、洞察与贡献；Background 提供概念、时间任务和负载依据；Related Work 集中逐系统差异。现有三处重复列举相关工作可压缩。Evaluation Methodology 保留协议与变量，Evaluation 以后写发现和解释；目前明确的结果空位是合理半成品状态。Conclusion 保留证据到位后的结果空位。

## 次级写作检查

完整扫描了 main.tex 递归引入的 13 个 TeX 文件，忽略注释，检查技能词表及 Unicode/LaTeX 破折号。破折号命中 28 个 token；词表仅命中 yet，位于 `02-background-motivation.tex`、`03-design.tex`、`04-implementation.tex`。这是写作约定的机械命中，常规语法中的 yet 本身不构成技术问题；按技能约定词表重复与破折号标为 MAJOR 写作项，处理顺序低于以上定义与论证问题。完整命中位置可用源文件搜索复核。当前正文无 citation command，引用空位已显式标识；引用未完成是阶段性工作，强烈的普遍性定位需同步降级。

具体英文问题：`02b-formulation.tex` 的 “not a established law”应改为 “not an established law”（G1，MINOR）；`03-design.tex` 的 “the interval … is the restoration byte budget”把时间间隔直接说成字节预算，应写为该间隔决定可恢复字节预算（MINOR）；“shallow the feasible eviction depth”改为 “reduce the feasible eviction depth”（MINOR）。Design 开头在一句中列七项不变量，按 G4 建议用列表或状态表拆开。

本审阅不作最终投稿评分：缺失结果和图形是已知半成品状态，图的可读性与最终版面尚不能据占位框评定。现阶段判定为骨架可继续推进，但应先解决 R1、R2，再统一 R3–R8。
