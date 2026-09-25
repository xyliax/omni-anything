# Agent Entry Point

本文件是 Agent 的唯一根入口，`CLAUDE.md` 是它的兼容 symlink。

## Project Scope

项目研究周期性交互模型服务中的长期 KV 状态管理：随上下文增长的历史 KV 状态可能在周期计算预算用尽前先耗尽有限的 GPU KV capacity。研究范围与术语以 [`docs/problem.md`](docs/problem.md) 为准，当前可执行配置与证据覆盖分别以 [`docs/experiments.md`](docs/experiments.md) 和 [`docs/findings.md`](docs/findings.md) 为准。prototype、measured path 和 evidence coverage 只描述仓库当前事实，不自动成为最终论文的 workload、modality、output、hardware 或 topology scope；除非实验矩阵和 paper contract 明确冻结，否则不得把它们写成论文边界。

用户最新说明优先于旧文档。文档冲突或缺少机制细节时询问用户，不从旧稿补猜；设计说明不等于代码实现证明。项目记忆只维护在对应 owner，不另建隐藏角色规则或重复的 current-state 文档。

会话开始或用户提示远端有更新时检查远端；用户允许同步时使用 fast-forward pull。若远端变化涉及文档或代码结构，重读本文件和任务路径上的局部 `AGENTS.md`。

## Task Router

按下方 map 的注释选择最小 read-set，不要默认读完整个仓库。`owner:` 标记该路径唯一持有的事实域：其余文档只能链接 owner 或写无数字摘要，易变的数字、状态、协议和路径不得手工复制。owner 表示维护职责，不代表内容已经验证；假设、设计要求、实现事实与实验结果必须区分。目录操作约束由最近一层 `AGENTS.md` 持有；`results/README.md` 是证据操作的显式例外。机器可检验的完整所有权声明见 `docs/agent/ownership.json`。

```text
.
├── README.md                        # 最小入口页；只保留 Getting Started 环境搭建
├── AGENTS.md                        # 本文件；owner: 任务路由、跨目录约束、Research Classification
├── CLAUDE.md -> AGENTS.md           # 兼容 symlink
├── pyproject.toml                   # 包与 pytest 配置
├── docs/                            # 投稿研究底稿与 Agent 索引；四份核心文档分域维护
│   ├── problem.md                   # owner: 问题定义、研究范围、术语词表
│   ├── system.md                    # owner: 机制语义、状态机、端到端流程；不保存结果数字
│   ├── experiments.md               # owner: 实验配置域、evaluated systems、指标与协议；不保存结论
│   ├── findings.md                  # owner: 当前状态、结论、数字与限制；不重复完整协议
│   ├── PAPER.md                     # 章节任务、图件状态与剩余写作；不是事实 owner
│   ├── papers/                      # 论文摘要与阅读笔记；不是项目事实
│   ├── references/                  # 带来源的外部参数与文献笔记；不默认读取
│   └── agent/                       # Agent 导航层，不是第二套项目事实
│       ├── README.md                # 任务 read-set 与交付要求；修改代码前必读
│       ├── ownership.json           # 机器可检验的所有权声明
│       ├── system-map.json          # owner: 组件与代码入口
│       ├── dynamic-edges.json       # owner: subprocess、IPC 与 monkeypatch 动态调用边
│       ├── contracts.json           # owner: 不变量与 verification
│       ├── change-impact.json       # owner: 修改到必查文档与测试的映射
│       ├── evidence.json            # owner: EVIDENCE-* 到精确 run、hash 与 provenance 的解析
│       ├── records/                 # 结构化实验过程记录（experiment_record_v1）
│       └── legacy-experiment-log.md # owner: 历史实验过程；已冻结，只读
├── engines/                         # baseline、conveyor 与共享音频前处理；引擎被 runner 按路径 spawn，禁止 import experiments
├── experiments/                     # 实验配置与 runner；负载/模型/平台公平性常量单份在 shared/
├── infra/                           # 与具体实验解耦的运行与观测设施
│   ├── run/                         # 运行工作流、进程与 artifact；不认识具体实验名
│   ├── trace/                       # 观测生产、解析、对齐与 Perfetto；实验不得私建 trace/画图
│   └── env/                         # 锁定运行环境；操作契约见本目录 AGENTS.md
├── results/                         # 不可变运行证据；操作规则见 results/README.md
├── tests/                           # 运行、配置与 trace 的单元测试；提交前从仓库根运行 python -m pytest
├── third_party/                     # git-subrepo pin；只读，除非用户明确授权 pin 操作
│   └── metronome/                   # baseline 依赖 pin；复制后永久分道，不追随上游
├── eurosys2027/                     # 论文写作工作区；不是事实 owner；写作规则见本目录 AGENTS.md
└── .github/                         # CI 工作流
```

除隐藏配置文件外，根目录只保留 map 所列条目。结构修改必须在同一事务内更新本 map 与 owner registry。

## Research Classification

论文叙事、文档评审和命名统一使用以下三层；本节是分类标准的唯一文字 owner，其他文档只应用分类结果，不复制整套规则。

| 层级 | 判定标准 | 文档位置 |
| --- | --- | --- |
| Research mechanism | 直接支撑 paper claim，具有明确因果假设，可独立 ablation，并有证据或明确的待验证状态 | 可进入 `docs/system.md` 的机制表和 `docs/findings.md` 的机制状态表 |
| System requirement | 研究设计成立所需的不变量或约束；规定系统必须满足什么，但不声称创新 | 写入 `docs/system.md` 的设计不变量或约束 |
| Implementation choice | 当前代码对 requirement 的一种可替换实现；用于 workflow、维护和诊断 | 写入实现流程、局部 `AGENTS.md` 或 registry，不进入贡献或机制列表 |

代码差异、独有开关或 matched baseline/Pilarius configuration 差异本身不构成 research mechanism。若替换某项接口、缓冲或同步实现而不改变 paper claim 与对应 ablation，该项应归为 implementation choice；由实现变化引出的测量口径可以形成 finding，但不能反向包装为机制创新。

## Narrative Scope Guard

根入口、README、核心 human docs 和论文 planning 必须保持同一条 scope 纪律：当前 prototype、measured path、模型/模态、输出链、硬件、设备拓扑和实验 profile 都是可变配置或证据边界，除非 paper contract 与实验矩阵已明确冻结，否则不得把它们写成研究问题、论文 workload 或 non-goal。`docs/experiments.md`、`docs/agent/evidence.json`、`results/` 以及标明 external reference 的资料目录可以记录这些细节，但其他文档只能链接其 owner 或使用不绑定实例的抽象表述。任何改变 scope 的文档重组都必须同时更新 [`docs/problem.md`](docs/problem.md)、`eurosys2027/` 的写作规则和 narrative-scope guard；不能只通过移动、压缩或删除文字来改变 scope。

## Change Transactions

机制语义、状态机、进程拓扑、IPC、实验协议或指标口径的改动，必须在同一事务内同步对应 owner 文档、registry 与测试；路径级映射见 [`docs/agent/change-impact.json`](docs/agent/change-impact.json)。新诊断 run 在分析期间保存 raw artifacts；是否保留与何时清理遵循 [`results/README.md`](results/README.md#retention-rules)，有保留价值时登记 record 与 evidence；接受新结论同步 evidence alias、record、finding card 与 current-state table；仅实现尚未验证的优化不得提前修改 findings 的性能状态。

## Evidence Discipline

- 文档引用 `FINDING-*`、`CLAIM-*`、`EXP-*` 和 `EVIDENCE-*` 的完整命名空间，不使用裸 `C1`、`E1` 或 `H7`。
- 人类文档和结构化 record 不写具体时间戳 run ID；record 只引用 `EVIDENCE-*`，精确 ID 由 `docs/agent/evidence.json` 解析。
- 结论性数字标明实测、模拟器标定、线性外推或冻结先验，并带模型/配置域限定。
- formal evidence 要求 clean source；diagnostic evidence 可以 dirty，但必须保留可重建的 patch artifact；不满足新纪律的旧证据必须在 registry 中显式降级。
- 成功以 `status.json` 终态和 validation 为准，exit 0 本身不构成成功。
- 每次向用户报告前，必须执行 [`results/README.md` 的结果检查与清理纪律](results/README.md#retention-rules)；该文件是结果保留操作的唯一 owner。

## Documentation Style

- 人类文档简洁、准确、专业；Agent 文档只保留有效路由和必要约束。过期评审、重复清单和已无用途的草稿删除，不用新建历史层保存；不可变证据按各自规则保留并定向读取。
- 核心文档服务于投稿：解释问题、论证设计、定义评估、呈现有依据的结果。缺少内容可保留具体待补提纲，不用无依据的结论填满章节。
- 命令、接口、兼容修补与仓库治理集中在复现附录或 Agent 层；只有影响正确性、公平性或结果解释时才进入研究正文。历史证据不因正文清理而改写或删除。
- 外部原始文献可在背景与相关工作中按需引用；明确其支持的属性，不将文献实例或当前原型转为未经冻结的论文边界。

- [`docs/problem.md`](docs/problem.md#terminology) 是论文核心术语的唯一 canonical glossary：新增 paper-facing 核心词先更新词表、迁移旧同义词；实现 identifier 和 repository-governance vocabulary 不得进入 contribution 或 mechanism narrative。
- Agent JSON 使用稳定 ID、repo-relative path、symbol、owner 和 verification；不要使用易漂移的行号。

## Required Checks

检查按改动类型分级：仅改动文档时，只需运行 `python -m pytest tests/test_narrative_scope.py`；改动代码、测试或配置，以及提交前，从仓库根运行完整 `python -m pytest`。`tests/test_narrative_scope.py` 是 scope anti-narrowing 的必要回归检查；修改根入口、核心 human docs、论文 planning 或外部资料目录边界时，不得删除或绕过它。CI 始终运行全量测试。
