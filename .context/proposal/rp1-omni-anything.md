# RP1：omni-anything

Updated: 2026-08-06

Status: **Active；当前唯一已经收敛并有实验支撑的 research point。**

## 一句话

面向“前台 omni 双工模型 + 后台 agent 结果回注”的持续交互负载，研究会话 KV 导致的显存容量墙，并以时刻表化的尾部 KV 传送带探索“用空闲 H2D 带宽换等效显存容量”。

## 权威入口

- 当前结论与文档地图：仓库根 `AGENTS.md`
- 问题定义：`PROBLEM.md`
- 逐条发现：`FINDINGS.md`
- 方案候选：`IDEA-KV-CONVEYOR.md`
- paper 级实验计划：`PAPER-EXPERIMENTS.md`

## 边界

- 本仓库是 RP1 的唯一事实源；本 dossier 不复制实验数字、推导或进度
- RP1 不是旧的 rollout scheduling、streaming RL 或跨模型迁移故事
- 判断前先读根 README 的现行/历史文档标记
