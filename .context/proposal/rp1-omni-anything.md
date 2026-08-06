# RP1：omni-anything

更新：2026-08-06

状态：**进行中；当前唯一有实验支撑的研究点。**

## 一句话

面向「前台 omni 双工模型 + 后台 agent 结果回注」的持续交互负载，研究 KV cache 带来的显存装不下问题，并探索按时间表迁移 tail KV：用闲置 H2D 带宽，换更大的同时在线容量。

## 权威入口

- 当前结论与文档地图：仓库根 `AGENTS.md`
- 问题定义：`PROBLEM.md`
- 逐条发现：`FINDINGS.md`
- 方案候选：`IDEA-KV-CONVEYOR.md`
- 论文级实验计划：`PAPER-EXPERIMENTS.md`

## 边界

- 本仓库是 RP1 的唯一事实源；本说明不复制实验数字、推导或进度
- RP1 不是旧的 rollout 调度、streaming RL 或跨模型迁移故事
- 判断前先读根 `AGENTS.md` 的当前 / 历史文档标记
