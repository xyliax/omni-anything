# Agent Entry Point

本文件是 Agent 的唯一根入口。先判断任务类型，再打开对应的权威文档和最近一层 `AGENTS.md`；不要默认读完整个仓库。

## Project Scope

项目研究单张 GPU 上的周期性交互模型服务：持续增长的 KV 工作集可能在每周期计算饱和前先耗尽 GPU KV capacity。当前实测 runner 是 Qwen2.5-Omni audio-input、Thinker-only 路径；研究范围、术语、实现边界和证据成熟度分别以 [`docs/problem.md`](docs/problem.md) 与 [`docs/findings.md`](docs/findings.md) 为准。

每次开始实质任务时先检查远端是否更新；用户允许同步时使用 fast-forward pull。若远端变化涉及文档或代码结构，重新读取本文件和任务路径上的局部 `AGENTS.md`。

## Task Router

| 任务 | 必读入口 |
| --- | --- |
| 理解研究问题 | [`docs/problem.md`](docs/problem.md) |
| 理解机制与端到端流程 | [`docs/system.md`](docs/system.md) |
| 设计、运行或比较实验 | [`docs/experiments.md`](docs/experiments.md) + `experiments/AGENTS.md` |
| 引用当前状态、数字或结论 | [`docs/findings.md`](docs/findings.md) + [`docs/agent/evidence.json`](docs/agent/evidence.json) |
| 理解 IPC、subprocess、monkeypatch | [`docs/agent/dynamic-edges.json`](docs/agent/dynamic-edges.json) |
| 修改代码 | [`docs/agent/README.md`](docs/agent/README.md) + 最近一层 `AGENTS.md` |
| 分析历史实验过程 | [`docs/agent/legacy-experiment-log.md`](docs/agent/legacy-experiment-log.md) |
| 操作运行证据 | `results/README.md`（Agent/维护者契约） |
| 修改第三方 pin | `third_party/AGENTS.md`；仅限用户明确要求 |

更细的任务 read-set 和交付要求由 [`docs/agent/README.md`](docs/agent/README.md) 持有。

## Single-Owner Rule

| 事实域 | 唯一 owner |
| --- | --- |
| 问题定义、研究范围、术语 | [`docs/problem.md`](docs/problem.md) |
| 机制语义、状态机、端到端流程 | [`docs/system.md`](docs/system.md) |
| 实验配置域、evaluated systems、指标与协议 | [`docs/experiments.md`](docs/experiments.md) |
| 当前状态、结论、数字与限制 | [`docs/findings.md`](docs/findings.md) |
| research mechanism / system requirement / implementation choice 的分类纪律 | 本文件「Research Classification」 |
| 组件、代码入口与动态调用边 | `docs/agent/*.json` |
| 历史实验过程 | `docs/agent/legacy-experiment-log.md` 与后续结构化 record |
| 精确 run、hash 与 provenance | `docs/agent/evidence.json` + `results/` |
| 目录操作约束 | 最近一层 `AGENTS.md`；`results/README.md` 是证据操作的显式例外 |

完整且机器可检验的所有权声明见 [`docs/agent/ownership.json`](docs/agent/ownership.json)。概念解释可以自洽；易变的数字、状态、协议和路径不得手工复制。其他文档只能链接 owner、写无数字摘要，或包含由测试校验的生成内容。

## Research Classification

论文叙事、文档评审和命名统一使用以下三层；本节是分类标准的唯一文字 owner，其他文档只应用分类结果，不复制整套规则。

| 层级 | 判定标准 | 文档位置 |
| --- | --- | --- |
| Research mechanism | 直接支撑 paper claim，具有明确因果假设，可独立 ablation，并有证据或明确的待验证状态 | 可进入 README、`docs/system.md` 的机制表和 `docs/findings.md` 的机制状态表 |
| System requirement | 研究设计成立所需的不变量或约束；规定系统必须满足什么，但不声称创新 | 写入 `docs/system.md` 的设计不变量或约束 |
| Implementation choice | 当前代码对 requirement 的一种可替换实现；用于 workflow、维护和诊断 | 写入实现流程、局部 `AGENTS.md` 或 registry，不进入贡献或机制列表 |

代码差异、独有开关或 matched baseline/Conveyor configuration 差异本身不构成 research mechanism。若替换某项接口、缓冲或同步实现而不改变 paper claim 与对应 ablation，该项应归为 implementation choice；由实现变化引出的测量口径可以形成 finding，但不能反向包装为机制创新。

## Terminology Discipline

[`docs/problem.md`](docs/problem.md#terminology) 是论文核心术语的唯一 canonical glossary。新增 paper-facing 核心词前必须先更新词表，声明对象、定义与类别，迁移旧同义词，并通过 terminology guard。实现 identifier 和 repository-governance vocabulary 不得进入 contribution 或 mechanism narrative。

## Repository Boundaries

| 路径 | 角色 | 约束 |
| --- | --- | --- |
| `docs/` | 人类事实层与 Agent 索引 | 人类核心文档只保留 problem/system/experiments/findings |
| `engines/` | baseline/conveyor 引擎本体 | 被 runner 按路径 spawn；不 import `experiments` |
| `experiments/` | 配置、runner 与公平性常量 | 负载/模型/平台常量在 `shared/` 单份持有 |
| `infra/run/` | 运行工作流、进程与 artifact | 不认识具体实验名 |
| `infra/trace/` | 观测生产、解析、对齐与 Perfetto | 实验不得私建 trace/画图实现 |
| `infra/env/` | 锁定运行环境 | 操作契约见本目录 `AGENTS.md` |
| `results/` | 不可变运行证据 | 规则见 `results/README.md` |
| `third_party/` | git-subrepo pin | 只读，除非用户明确授权 pin 操作 |
| `eurosys2027/` | EuroSys 2027 论文写作工作区 | 不是事实 owner；写作规则和 source-of-truth 边界见本目录 `AGENTS.md` |
| `.context/` | 讨论、外部整理和表达草稿 | 不是项目事实；被采纳内容单向提升到 owner |

除上述正式顶层目录外，根目录只保留 `README.md`、本文件和兼容 symlink `CLAUDE.md`。`third_party/metronome/` 是 baseline 直接依赖的 pin；本仓 worker 从其复制后永久分道，不追随上游文件更新。

## Change Transactions

| 改动类型 | 同一事务内必须检查 |
| --- | --- |
| 机制语义或状态机 | 代码、`docs/system.md`、contracts、dynamic edges、对应测试 |
| 进程拓扑或 IPC | runner/engine、system map、dynamic edges、manifest/trace 覆盖 |
| 实验协议或配置 | `docs/experiments.md`、可执行 config、manifest、协议测试 |
| 新诊断 run | raw artifacts、结构化 record；有保留价值时登记 evidence |
| 接受新结论 | evidence alias、record、finding card、current-state table |
| 仅实现尚未验证的优化 | 不得提前修改 findings 的性能状态 |

修改影响的机器可读版本见 [`docs/agent/change-impact.json`](docs/agent/change-impact.json)。

## Evidence Discipline

- 文档引用 `FINDING-*`、`CLAIM-*`、`EXP-*` 和 `EVIDENCE-*` 的完整命名空间，不使用裸 `C1`、`E1` 或 `H7`。
- 人类文档和结构化 record 不写具体时间戳 run ID；record 只引用 `EVIDENCE-*`，精确 ID 由 `docs/agent/evidence.json` 解析到 run manifest、provenance 和 aggregates。
- 每个数字标明实测、模拟器标定、线性外推或冻结先验，并带模型/配置域限定。
- formal evidence 要求 clean source；diagnostic evidence 可以 dirty，但必须保留可重建的 patch artifact。旧证据若不满足新纪律，必须在 registry 中显式降级，不能伪装成可复现 formal evidence。
- 成功以 `status.json` 终态和 validation 为准，exit 0 本身不构成成功。

## Documentation Style

- 人类核心文档的论文式章节标题使用英文，正文使用中文；稳定 heading 用于 deep link。`docs/findings.md` 的 `FINDING-*` claim card 保留稳定 ID，标题说明使用中文。
- 专有机制首次出现时使用“中文名称（英文术语）+ 简短定义”，后文优先使用中文；通用系统术语可以保留英文。
- `README.md` 只做落地页，不保存实验数字。
- `docs/system.md` 不保存结果数字；`docs/experiments.md` 不保存结论；`docs/findings.md` 不重复完整协议。
- Agent JSON 使用稳定 ID、repo-relative path、symbol、owner 和 verification；不要使用易漂移的行号。
- 新的实验过程记录使用结构化 schema；`legacy-experiment-log.md` 已冻结，只读。

## Required Checks

从仓库根运行：

```bash
python -m pytest
```

文档契约、路径、链接、ID、Agent registry 和 evidence 关系由 `tests/test_documentation.py` 与 `tests/test_repository_layout.py` 守卫。修改结构时必须同步更新 owner 和测试，不能通过放宽断言隐藏不一致。
