# 论文工作大纲

<a id="source-map-and-writing-discipline"></a>
本大纲安排章节、图件和剩余写作。研究材料见[问题定义](problem.md)、[系统设计](system.md)、[实验设计](experiments.md)和[已有证据](findings.md)。

<a id="central-question"></a>
中心问题：在周期交互中，怎样安排 KV 驻留与恢复，利用共享传输和计算资源降低峰值显存，并提高满足 soft deadline 的会话承载能力？

<a id="proposed-contributions-and-proof-obligations"></a>
候选论证分为资源问题、联合调度设计与评估三部分。最终贡献必须对应已定义机制和验证结果；相位、offload 或预取开关本身不是新颖性证明。当前算法待决项见 [系统设计](system.md#open-design-decisions)；重算定位与扩展方向见 [Future work](system.md#future-recomputation)。

<a id="narrative-skeleton"></a>
## 章节任务

| 章节 | 读者应获得的信息 | 取材入口 |
| --- | --- | --- |
| Introduction | 双工交互的发展与能力如何引出 interaction session、周期工作和容量问题，进而解释为何需要该设计 | Problem；外部模型来源；正式结果到手后引用 Findings |
| Background and Motivation | 时间对齐训练和播放节奏为何使周期工作较小；显存先受限的条件；全量恢复的限制及带宽到容量收益的关系 | [播放节奏](problem.md#playback-paced-work)、[计算余量](problem.md#slack-conditions)、[带宽与容量](problem.md#bandwidth-memory-bound)；[实验一](experiments.md#capacity-experiment) |
| System Design | 架构与周期流程、组与 phase、联合驻留规划、安全逐出与恢复、计划修正和后端对接；说明批处理代价如何计入余量 | [System](system.md#planning-updates)、[批处理取舍](system.md#batching-tradeoff) |
| Evaluation | 容量与服务代价、自然错峰下的动态加入退出、简单成对消融；同一批运行覆盖上下文增长与低负载开销 | [本轮评估协议](experiments.md#evaluation-questions)；Findings |
| Discussion | 假设放宽、未覆盖维度和重算的 future work | [重算扩展方向](system.md#future-recomputation)；评估覆盖 |
| Related Work | 与最近工作的条件、信息、控制动作和结果差异 | 一手论文及外部核验笔记 |
| Conclusion | 重述经过验证的贡献、收益与适用条件 | 已完成的主结果 |

不单列 Implementation 章节。后端接口与正确性所需的对接约束作为 System Design 的简短 Backend Integration 小节；实现版本和实验设置随经核验材料进入评估设置，未实现部分不写成既成事实。

## Introduction 的进入顺序

1. 用双工交互的发展、代表模型及其能力引出 interaction session，再过渡到 time-aligned 的周期更新与历史延续；避免重复摘要开头。
2. 给出第一个可追溯的资源量级，解释历史驻留与周期计算的差异。模型参数推导与实测分开标注。
3. 用少量代表工作解释已有方法的取舍；完整文献分类留给 Related Work。
4. 围绕 [H2D 持续服务与容量收益的因果关系](system.md#offset-resource-rationale)，引出 phase、恢复窗口与峰值空间的耦合。
5. 介绍系统如何回应这些困难，避免把实现接口列为贡献。
6. 给出经过验证的结果和贡献；结果未就绪时保留明确占位。

每段推进一个主要信息，并给出下一段所需的前提。正文只保留问题、设计与证据，不写作者备忘或审稿预判。

具体例子不限定最终实验范围；模型、负载和硬件覆盖仍由实验设计确定。引用来源与推导见[外部模型参数核验](references/minicpm-o-4.5-kv-geometry.md)。

<a id="abstract-outline"></a>
## 摘要

按应用与资源问题、[核心容量机制](system.md#design-goals)、设计、结果顺序写。结果句只能使用正式测量；不保留倍率模板，不把待设计的联合规划或主动重算写成已完成贡献。

<a id="figure-plan"></a>
## 图件

图件由作者维护。示意图解释因果关系，不能作为容量或 deadline 已达标的测量证据。

| 图件 | 内容 | 状态 |
| --- | --- | --- |
| 图 1 | 周期计算、空闲区间与历史 KV 增长 | 作者图件已接入 Intro；`eurosys2027/figures/figure.drawio` 第二页及 `figure-intro.pdf`。当前整页宽度下图中文字仍偏小，需在源图调整 |
| 图 2 | phase 与恢复时机对传输和峰值驻留的影响 | 已接入 Intro，单栏；`figure.drawio` 第三页及 `figure-comparison.pdf` |
| 动机测量 | 容量、计算与进度的联合观察 | 复用实验一容量边界附近的数据 |
| 跨硬件容量边界表 | 固定模型最大上下文，按全驻留内存上限形成完整 batch，比较显存带宽、主干执行时间和周期占比 | Background 已填显式效率假设下的解析估算，来源、逐阶段计账及敏感性见[表内估算及预测协议](experiments.md#cross-hardware-projections)；周期占比仅覆盖主干执行，完整管线与实际 batching 仍需标定和独立验证 |
| 跨模型周期占比矩阵 | 在容量边界处改变模型几何与周期工作量，检查主干余量的覆盖与边界 | Background 接在容量估算说明后；参数、逐格 batch、公开实测代理核查与限制见[跨模型协议](experiments.md#cross-model-projections)。主表统一使用显式效率假设，敏感性保留超过周期的组合，不据解析矩阵声称普遍余量 |
| 设计总览 | 架构与跨周期驻留流程；语义见 [System](system.md#logical-architecture) | 作者现有[导出 PDF](../eurosys2027/figures/figure-design.pdf) 已接入 System Design；正文解释逐 session 恢复与独立就绪，caption 说明右侧恢复序列如何分散 H2D 需求。源图及导出内容未修改；整页宽度下接口及状态文字偏小，需作者在源图调整 |
| 评估图 | 容量与代价曲线、动态到达时间轨迹、phase 与恢复时机的成对比较 | 依照[已确认实验](experiments.md#evaluation-questions)生成；结果仍待测量 |

<a id="material-dependencies"></a>
## 剩余工作

| 待完成项 | 影响的正文 | 材料位置 |
| --- | --- | --- |
| 按最大上下文联合规划的具体算法 | Intro 技术支点、Design、贡献列表 | [最大上下文规划](system.md#maximum-context-planning)、[System 未决设计](system.md#open-design-decisions) |
| 已选恢复与修正策略的实现核验 | Design 的 Backend Integration、评估与图文复核 | [恢复分配决策](system.md#group-restoration-allocation)、[计划修正](system.md#planning-updates)及[验收场景](system.md#implementation-handoff)；设计选择不代表已有实现或结果 |
| 同上下文上限的会话数、延迟与超期测量 | Evaluation 与结果句 | [测量语义](experiments.md#measurement-semantics) |
| 共用会话时间表回放与原始输入时钟、真实完成事件对齐 | Evaluation 的动态到达与自然 phase 对照 | [动态到达协议](experiments.md#dynamic-arrival-experiment)、[运行前核验](experiments.md#correctness-and-quality-protocol) |
| 受控资源观察与正式主结果 | Motivation、Evaluation、Abstract、Conclusion | [实验设计](experiments.md#evaluation-questions)、[已有证据](findings.md#current-state) |
| 容量边界处的完整周期成本及分组代价 | Motivation 与 Design 的余量论证 | [计算余量条件](problem.md#slack-conditions)、[批处理取舍](system.md#batching-tradeoff)；外部阶段耗时只解释量级 |
| 跨硬件完整周期预测与验证 | Background 的容量边界表 | [预测协议](experiments.md#cross-hardware-projections)；容量上限 batch 的 prefill/decode 条件估算已填，仍需实测非 KV 分配、有效效率、KV 复用和其余管线成本，不以解析剩余预算证明完整服务均有余量 |
| 随算法确定细化最近工作差异 | Intro、Related Work | [外部比较笔记](references/closest-work-gap-analysis-2026-09.md)；按最终算法重新核验 |

<a id="submission-material-to-complete"></a>
## 提交前

核对标题、摘要、机制、图和实验是否描述同一系统；清除正文占位与作者注释；检查引用、匿名性、图中文字和页面。规则与命令见 [写作入口](../eurosys2027/AGENTS.md) 和 [投稿清单](../eurosys2027/planning/submission-checklist.md)。

<a id="writing-references"></a>
写作参照按需阅读 [vLLM](https://arxiv.org/pdf/2309.06180) 与 [DistServe](https://www.usenix.org/system/files/osdi24-zhong-yinmin.pdf)：用资源代价引入问题，按约束解释设计，先报告服务能力再分析原因。
