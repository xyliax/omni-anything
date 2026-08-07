# AGENTS.md

Agent 工作入口。先读本文件，再按任务打开下列权威文档。

## 项目一句话

在单张 GPU 上同时跑两类负载：双工语音前台（固定时长的硬 tick）与后台 agent 结果回注。真实软件栈是 vLLM 0.23 + Qwen2.5-Omni-7B + RTX 3090。当前候选方案是**按时间表调度的尾部 KV conveyor**：用闲置 H2D 带宽换更大的同时在线容量。

## 权威文档（事实层）

| 文档 | 状态 | 用途 |
| --- | --- | --- |
| `docs/FINDINGS.md` | 结论 | E 系列发现清单与证据指针；**看结论从这里开始** |
| `docs/PROBLEM.md` | 结论 | 问题定义、三要素、实测事实、三类瓶颈、方案摘要 |
| `docs/IDEA-KV-CONVEYOR.md` | 设计历史（机制已测，集成未验证） | 方案演化、旧预测及验证计划；现行数字看 FINDINGS |
| `docs/PAPER-EXPERIMENTS.md` | 实验设计（执行中） | 主张到实验的对应、平台决策、Metronome 可复用代码对照 |
| `docs/STORY.md` | 历史叙事（部分仍有效） | 发现过程；**P1–P4 数字以 E1 真机数据为准**，§5 产品与文献仍可用 |
| `docs/METRONOME-NOTE.md` | 第三方使用纪律 | 为何、如何使用 `third_party/metronome/` |

已删除材料（模拟器、`EVIDENCE.md`、`TIMELINES.md`、旧 FINDINGS 等）只能从 git 历史找回，**不得当作现状引用**。E4 的先验设定（40% cancellation、LogNormal 注入）以 `docs/PAPER-EXPERIMENTS.md` §三为准。

当前证据边界：E0 是 CUDA 微基准，E1 是真实端到端 baseline；E2/E3 是使用 E1 compute trace
和新鲜 H2D 实测的机制实验，**尚未改变 vLLM active KV block ownership，不得写成端到端 conveyor**。

## 目录边界

| 路径 | 角色 | 读写 |
| --- | --- | --- |
| `docs/` | 结论、问题、候选设计、实验计划和研究历史；权威层级见 `docs/README.md` | 任务要求时改 |
| `environment/` | 项目级可重建环境；按 runtime profile 管理锁、模型和补丁 | 任务要求时改 |
| `experiments/` | 按 E 编号与目的组织的自研实验代码；全局索引见 `experiments/README.md` | 任务要求时改 |
| `observability/` | 跨实验的日志解析、vLLM trace 注入、确定性 replay 和 Perfetto 导出 | 与实验证据格式同步维护 |
| `results/` | 与实验同名的精选 run 证据；布局、保留和清理规则见 `results/README.md` | 保留 run 内容不改；过时 run 可显式清理 |
| `tests/`、`.github/` | 无 GPU 项目测试和 CI | 随自研代码同步维护 |
| `third_party/` | 第三方代码（git-subrepo pin）；约束见 `third_party/AGENTS.md` | **只读**；实验改动不写回 pin |
| `.context/` | 文档、digest、proposal、slides；见 `.context/README.md` | 非事实来源；按题目打开，不默认批量阅读 |
| 根 `README.md`、`AGENTS.md` | 人类入口与仓库契约 | 保持简洁；不要平行再造 STATE/CATCHUP 类文档 |

`third_party/metronome/` 是 E1 baseline 的直接依赖；其余 pin 仅供对照阅读。

## 行为约束

- 不要根据 `.context/slides/` 或第三方 pin 反推项目进展状态与数字；数字以 `docs/FINDINGS.md`、`results/`、`docs/PAPER-EXPERIMENTS.md` 为准。
- 不要把已清理的 streaming-RL、Jiuwen 落地、模拟器叙事恢复为当前主线。
- 外部「现状如何」类断言要注意查证日期；本领域大约按月更新。
- `README.md` 是人类入口和操作地图，不复制完整项目契约；契约仍以本文件为准。
