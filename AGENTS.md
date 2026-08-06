# AGENTS.md

Agent 工作入口。先读本文件，再按任务打开下列权威文档。

## 项目一句话

在单张 GPU 上同时跑两类负载：双工语音前台（固定时长的硬 tick）与后台 agent 结果回注。真实软件栈是 vLLM 0.23 + Qwen2.5-Omni-7B + RTX 3090。当前候选方案是**按时间表调度的尾部 KV conveyor**：用闲置 H2D 带宽换更大的同时在线容量。

## 权威文档（事实层）

| 文档 | 状态 | 用途 |
| --- | --- | --- |
| `FINDINGS.md` | 结论 | E 系列发现清单与证据指针；**看结论从这里开始** |
| `PROBLEM.md` | 结论 | 问题定义、三要素、实测事实、三类瓶颈、方案摘要 |
| `IDEA-KV-CONVEYOR.md` | 方案候选（未验证） | 方案如何落到当前形态的记录与验证计划 |
| `PAPER-EXPERIMENTS.md` | 实验设计（执行中） | 主张到实验的对应、平台决策、Metronome 可复用代码对照 |
| `STORY.md` | 历史叙事（部分仍有效） | 发现过程；**P1–P4 数字以 E1 真机数据为准**，§5 产品与文献仍可用 |
| `METRONOME-NOTE.md` | 第三方使用纪律 | 为何、如何使用 `third_party/metronome/` |

已删除材料（模拟器、`EVIDENCE.md`、`TIMELINES.md`、旧 FINDINGS 等）只能从 git 历史找回，**不得当作现状引用**。E4 的先验设定（40% cancellation、LogNormal 注入）以 `PAPER-EXPERIMENTS.md` §三为准。

## 目录边界

| 路径 | 角色 | 读写 |
| --- | --- | --- |
| `harness/` | E 系列真机实验组件；索引见 `harness/README.md`，手册见 `harness/USAGE.md` | 任务要求时改 |
| `calibration/` | E0 DMA 微基准 | 任务要求时改 |
| `results/` | 运行证据（`paper/`、`figures/`、`viz/`） | 证据只增不删，不改写结论 |
| `third_party/` | 第三方代码（git-subrepo pin）；约束见 `third_party/AGENTS.md` | **只读**；实验改动不写回 pin |
| `.context/` | 文档、digest、proposal、slides；见 `.context/README.md` | 非事实来源；按题目打开，不默认批量阅读 |
| 根目录 `*.md`（本表所列） | 结论与设计 | 任务要求时改；不要平行再造 STATE/CATCHUP 类文档 |

`third_party/metronome/` 是 harness 直接依赖的 baseline；其余 pin 仅供对照阅读。

## 行为约束

- 不要根据 `.context/slides/` 或第三方 pin 反推项目进展状态与数字；数字以 `FINDINGS`、`results/`、`PAPER-EXPERIMENTS` 为准。
- 不要把已清理的 streaming-RL、Jiuwen 落地、模拟器叙事恢复为当前主线。
- 外部「现状如何」类断言要注意查证日期；本领域大约按月更新。
- `README.md` 只是仓库占位，**不含**项目契约；契约以本文件为准。
