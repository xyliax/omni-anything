# AGENTS.md

Agent 工作入口。先读本文件，再按任务打开下列权威文档。

## 项目一句话

单卡上 serve「双工语音前台（硬拍）+ 后台 agent 结果回注」负载：真栈（vLLM 0.23 + Qwen2.5-Omni-7B + RTX 3090）收敛到候选方案——**时刻表化的尾部 KV 传送带**（H2D 带宽换等效显存）。

## 权威文档（事实层）

| 文档 | 状态 | 用途 |
| --- | --- | --- |
| `FINDINGS.md` | 现行结论 | E 系列发现清单 + 证据指针；**看结论从这里开始** |
| `PROBLEM.md` | 现行结论 | 问题定义、三要素、实测事实、三面墙、方案摘要 |
| `IDEA-KV-CONVEYOR.md` | 方案候选（未验证） | 方案收敛记录与验证计划 |
| `PAPER-EXPERIMENTS.md` | 实验设计（执行中） | claim→实验、平台决策、Metronome 复用地图 |
| `STORY.md` | 历史叙事（部分现行） | 发现过程；**P1–P4 数字以 E1 真栈为准**，§5 产品/文献仍可用 |
| `METRONOME-NOTE.md` | 第三方纪律 | 为何/如何用 `third_party/metronome/` |

已删除材料（模拟器、`EVIDENCE.md`、`TIMELINES.md`、旧 FINDINGS 等）仅 git 可溯，**不得当现状引用**。E4 先验（40% 作废、LogNormal 注入）以 `PAPER-EXPERIMENTS.md` §三为准。

## 目录边界

| 路径 | 角色 | 读写 |
| --- | --- | --- |
| `harness/` | E 系列真栈组件；索引 `harness/README.md`，手册 `harness/USAGE.md` | 任务要求时改 |
| `calibration/` | E0 DMA 微基准 | 任务要求时改 |
| `results/` | 运行证据（`paper/`、`figures/`、`viz/`） | 证据只增不 scrub 现行结论 |
| `third_party/` | 第三方代码（git-subrepo）；约束见 `third_party/AGENTS.md` | **只读**；实验改动不进 pin |
| `.context/` | 文档/digest/proposal/slides；见 `.context/README.md` | 非事实源；按题打开，不默认批量读 |
| 根 `*.md`（本表） | 结论与设计 | 任务要求时改；勿平行再造 STATE/CATCHUP |

`third_party/metronome/` 是 harness 直接依赖的 baseline；其余 pin 仅对照阅读。

## 行为约束

- 不以 `.context/slides/` 或第三方 pin 反推 RP 状态与数字；数字回 `FINDINGS` / `results/` / `PAPER-EXPERIMENTS`。
- 不恢复已清理的 streaming-RL / Jiuwen 落地 / 模拟器叙事为当前主线。
- 外部「现状如何」类断言注意查证日期；领域按月翻页。
- `README.md` 仅为仓库占位，**不含**项目契约；契约以本文件为准。
