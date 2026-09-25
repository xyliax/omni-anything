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
| Background and Motivation | 时间对齐训练和播放节奏为何使周期工作较小；显存先受限的条件；全量恢复的限制及带宽到容量收益的关系 | [播放节奏](problem.md#playback-paced-work)、[计算余量](problem.md#slack-conditions)、[带宽与容量](problem.md#bandwidth-memory-bound)；Q1 |
| System Design | 架构与周期流程、组与 phase、联合驻留规划、安全逐出与恢复、计划修正和后端对接；说明批处理代价如何计入余量 | [System](system.md#planning-updates)、[批处理取舍](system.md#batching-tradeoff) |
| Evaluation | 达标承载能力、延迟代价、独立消融、正确性及失效边界 | Experiments；Findings |
| Discussion | 假设放宽、未覆盖维度和重算的 future work | [重算扩展方向](system.md#future-recomputation)；评估覆盖 |
| Related Work | 与最近工作的条件、信息、控制动作和结果差异 | 一手论文及外部核验笔记 |
| Conclusion | 重述经过验证的贡献、收益与适用条件 | 已完成的主结果 |

不单列 Implementation 章节。后端接口与正确性所需的对接约束作为 System Design 的简短 Backend Integration 小节；实现版本和实验设置随经核验材料进入评估设置，未实现部分不写成既成事实。

## Introduction 的进入顺序

1. 用双工交互的发展、代表模型及其能力引出 interaction session，再过渡到 time-aligned 的周期更新与历史延续；避免重复摘要开头。
2. 给出第一个可追溯的资源量级，解释历史驻留与周期计算的差异。模型参数推导与实测分开标注。
3. 用少量代表工作解释已有方法的取舍；完整文献分类留给 Related Work。
4. 引出 phase、恢复窗口与峰值空间的耦合，给出设计需要解决的具体困难。
5. 介绍系统如何回应这些困难，避免把实现接口列为贡献。
6. 给出经过验证的结果和贡献；结果未就绪时保留明确占位。

每段推进一个主要信息，并给出下一段所需的前提。正文只保留问题、设计与证据，不写作者备忘或审稿预判。

具体例子不限定最终实验范围；模型、负载和硬件覆盖仍由实验设计确定。引用来源与推导见[外部模型参数核验](references/minicpm-o-4.5-kv-geometry.md)。

<a id="abstract-outline"></a>
## 摘要

按应用与资源问题、关键困难、设计、结果顺序写。结果句只能使用正式测量；不保留倍率模板，不把待设计的联合规划或主动重算写成已完成贡献。

<a id="figure-plan"></a>
## 图件

图件由作者维护。示意图解释因果关系，不能作为容量或 deadline 已达标的测量证据。

| 图件 | 内容 | 状态 |
| --- | --- | --- |
| 图 1 | 周期计算、空闲区间与历史 KV 增长 | 作者图件已接入 Intro；`eurosys2027/figures/figure.drawio` 第二页及 `figure-intro.pdf`。当前整页宽度下图中文字仍偏小，需在源图调整 |
| 图 2 | phase 与恢复时机对传输和峰值驻留的影响 | 已接入 Intro，单栏；`figure.drawio` 第三页及 `figure-comparison.pdf` |
| 动机测量 | 容量、计算与进度的联合观察 | 等待 Q1 数据 |
| 跨硬件容量边界表 | 相同负载下的 KV 池、容量边界、预测周期成本范围与证据类型 | Background 已加入表框架；数值与瓶颈判断均待填，按 [跨硬件预测协议](experiments.md#cross-hardware-projections)完成校准、独立验证及敏感性分析 |
| 设计总览（讨论稿） | 架构与跨周期驻留流程；语义见 [System](system.md#logical-architecture) | [Draw.io](../eurosys2027/figures/figure.drawio) 的 `design` 页与[导出 PDF](../eurosys2027/figures/figure-design-draft.pdf)；待接入正文并复核可读性 |
| 评估图 | 主结果、代价、消融、正确性及失效边界 | 按 Experiments 的评估问题生成 |

<a id="material-dependencies"></a>
## 剩余工作

| 待完成项 | 影响的正文 | 材料位置 |
| --- | --- | --- |
| 联合规划的具体算法 | Intro 技术支点、Design、贡献列表 | [System 未决设计](system.md#open-design-decisions) |
| session group 恢复分配方案的比较与选择 | Design 正文、设计图和相关评估；论文收尾时必须复核 | [恢复分配决策](system.md#group-restoration-allocation)，未决 |
| 违约比例、观察期限和失败判据 | Evaluation 与结果句 | [测量语义](experiments.md#measurement-semantics) |
| 受控资源观察与正式主结果 | Motivation、Evaluation、Abstract、Conclusion | [实验设计](experiments.md#evaluation-questions)、[已有证据](findings.md#current-state) |
| 容量边界处的完整周期成本及分组代价 | Motivation 与 Design 的余量论证 | [计算余量条件](problem.md#slack-conditions)、[批处理取舍](system.md#batching-tradeoff)；外部阶段耗时只解释量级 |
| 跨硬件预测表的参数与验证 | Background 的容量边界表 | [预测协议](experiments.md#cross-hardware-projections)；区分实测与预测，不以峰值规格直接证明全部硬件均有余量 |
| 随算法确定细化最近工作差异 | Intro、Related Work | [外部比较笔记](references/closest-work-gap-analysis-2026-09.md)；按最终算法重新核验 |

<a id="submission-material-to-complete"></a>
## 提交前

核对标题、摘要、机制、图和实验是否描述同一系统；清除正文占位与作者注释；检查引用、匿名性、图中文字和页面。规则与命令见 [写作入口](../eurosys2027/AGENTS.md) 和 [投稿清单](../eurosys2027/planning/submission-checklist.md)。

<a id="writing-references"></a>
写作参照按需阅读 [vLLM](https://arxiv.org/pdf/2309.06180) 与 [DistServe](https://www.usenix.org/system/files/osdi24-zhong-yinmin.pdf)：用资源代价引入问题，按约束解释设计，先报告服务能力再分析原因。
