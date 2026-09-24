# 论文工作大纲

<a id="source-map-and-writing-discipline"></a>
本大纲安排章节、图件和剩余写作。研究材料见[问题定义](problem.md)、[系统设计](system.md)、[实验设计](experiments.md)和[已有证据](findings.md)。

<a id="central-question"></a>
中心问题：在周期交互中，怎样安排 KV 驻留与恢复，利用共享传输和计算资源降低峰值显存，并提高满足 soft deadline 的会话承载能力？

<a id="proposed-contributions-and-proof-obligations"></a>
候选论证分为资源问题、联合调度设计与评估三部分。最终贡献必须对应已定义机制和验证结果；相位、offload 或预取开关本身不是新颖性证明。算法与重算的待决项只在 [系统设计](system.md#open-design-decisions) 维护。

<a id="narrative-skeleton"></a>
## 章节任务

| 章节 | 读者应获得的信息 | 取材入口 |
| --- | --- | --- |
| Introduction | 具体会话如何运行、容量问题何时出现、为何需要该设计 | Problem；外部模型来源；正式结果到手后引用 Findings |
| Background and Motivation | 周期与状态模型、soft deadline、显存上限处的全局计算余量及其条件；KV 空闲窗口作为恢复前提 | [计算余量分析](problem.md#slack-conditions)；Experiments 的时间事件；Q1 |
| Design | 准入规划、每周期执行和低频修正分别负责什么；phase、逐出量与恢复时刻如何共同确定；正确性与失败处理 | [System](system.md#planning-updates) |
| Implementation | 实现如何落实设计，以及影响正确性或结果解释的限制 | 经核验的路径与证据，不从旧实现反推设计边界 |
| Evaluation | 达标承载能力、延迟代价、独立消融、正确性及失效边界 | Experiments；Findings |
| Discussion | 假设放宽、未覆盖维度和重算扩展 | System 未决项；评估覆盖 |
| Related Work | 与最近工作的条件、信息、控制动作和结果差异 | 一手论文及外部核验笔记 |
| Conclusion | 重述经过验证的贡献、收益与适用条件 | 已完成的主结果 |

## Introduction 的进入顺序

1. 用一个具体双工会话解释一周期做什么，以及历史如何延续；只引入读者理解例子必需的词。
2. 给出第一个可追溯的资源量级，解释历史驻留与周期计算的差异。模型参数推导与实测分开标注。
3. 用少量代表工作解释已有方法的取舍；完整文献分类留给 Related Work。
4. 引出 phase、恢复窗口与峰值空间的耦合，给出设计需要解决的具体困难。
5. 介绍系统如何回应这些困难，避免把实现接口列为贡献。
6. 给出经过验证的结果和贡献；结果未就绪时保留明确占位。

每段新增一个主要信息，不在正文写作者备忘、审稿预判或“我们谨慎声明”等元话语。目标是让非本方向审稿人逐步理解问题，篇幅由具体例子、证据和必要解释支撑。

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
| 图 2 | phase 与恢复时机对传输和峰值驻留的影响 | 作者图件已接入 Intro；同一 Draw.io 第三页及 `figure-comparison.pdf`。单栏显示，图注已补全 |
| 动机测量 | 容量、计算与进度的联合观察 | 等待 Q1 数据 |
| 设计总览（讨论稿） | 有限前瞻规划与周期执行的分工；完整恢复目标分配和 KV 内容有效性的区别 | 可编辑源文件 [figure-design-draft.drawio](../eurosys2027/figures/figure-design-draft.drawio) 和 [PDF](../eurosys2027/figures/figure-design-draft.pdf) 已保存，尚未接入正文；预算算法与异常策略确定后由作者复核 |
| 评估图 | 主结果、代价、消融、正确性及失效边界 | 按 Experiments 的评估问题生成 |

<a id="material-dependencies"></a>
## 剩余工作

| 待完成项 | 影响的正文 | 材料位置 |
| --- | --- | --- |
| 联合规划与主动重算的具体算法 | Intro 技术支点、Design、贡献列表 | [System 未决设计](system.md#open-design-decisions) |
| 违约比例、观察期限和失败判据 | Evaluation 与结果句 | [测量语义](experiments.md#measurement-semantics) |
| 受控资源观察与正式主结果 | Motivation、Evaluation、Abstract、Conclusion | [实验设计](experiments.md#evaluation-questions)、[已有证据](findings.md#current-state) |
| 随算法确定细化最近工作差异 | Intro、Related Work | 已核验原文并加入引用；具体算法确定后继续检查比较是否成立 |

<a id="submission-material-to-complete"></a>
## 提交前

核对标题、摘要、机制、图和实验是否描述同一系统；清除正文占位与作者注释；检查引用、匿名性、图中文字和页面。规则与命令见 [写作入口](../eurosys2027/AGENTS.md) 和 [投稿清单](../eurosys2027/planning/submission-checklist.md)。

<a id="writing-references"></a>
写作参照只按具体需求阅读原始论文，不把历史审阅、写作建议或外部笔记当成当前项目事实。

本轮全文修订对照 [vLLM](https://arxiv.org/pdf/2309.06180) 与 [DistServe](https://www.usenix.org/system/files/osdi24-zhong-yinmin.pdf)：用具体资源代价引入问题，按约束解释设计动作，先给服务能力主结果再做归因。Related Work 已加入 Orca、vLLM、InferCept、Cake、DistServe 和 Metronome 的原始引用；未确定的算法与结果保留显式占位。
