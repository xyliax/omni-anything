# Agent Entry Point

本文件是 Agent 的唯一根入口，`CLAUDE.md` 是它的兼容 symlink。项目研究单张 GPU 上的周期性交互模型服务：持续增长的 KV 工作集可能在每周期计算饱和前先耗尽 GPU KV capacity；当前实测 runner 是 Qwen2.5-Omni audio-input、Thinker-only 路径。

会话开始或用户提示远端有更新时检查远端；用户允许同步时使用 fast-forward pull。若远端变化涉及文档或代码结构，重读本文件和任务路径上的局部 `AGENTS.md`。

## Task Router

按下方 map 的注释选择最小 read-set，不要默认读完整个仓库。`owner:` 标记该路径唯一持有的事实域：其余文档只能链接 owner、写无数字摘要，或包含由测试校验的生成内容，易变的数字、状态、协议和路径不得手工复制。目录操作约束由最近一层 `AGENTS.md` 持有；`results/README.md` 是证据操作的显式例外。机器可检验的所有权全集见 `docs/agent/ownership.json`。

```text
.
├── README.md                        # 最小落地页；只保留 Getting Started 环境搭建
├── AGENTS.md                        # 本文件；owner: 任务路由、跨目录约束、Research Classification
├── CLAUDE.md -> AGENTS.md           # 兼容 symlink
├── pyproject.toml                   # 包与 pytest 配置
├── docs/                            # 人类事实层与 Agent 索引；人类核心文档仅此四份
│   ├── problem.md                   # owner: 问题定义、研究范围、术语词表
│   ├── system.md                    # owner: 机制语义、状态机、端到端流程；不保存结果数字
│   ├── experiments.md               # owner: 实验配置域、evaluated systems、指标与协议；不保存结论
│   ├── findings.md                  # owner: 当前状态、结论、数字与限制；不重复完整协议
│   ├── papers/                      # 论文摘要与阅读笔记；不是项目事实
│   ├── references/                  # 外部规格整理与版图调研；不是项目事实
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
├── engines/                         # baseline 与 conveyor 引擎本体；被 runner 按路径 spawn，禁止 import experiments
├── experiments/                     # 实验配置与 runner；负载/模型/平台公平性常量单份在 shared/
├── infra/                           # 与具体实验解耦的运行与观测设施
│   ├── run/                         # 运行工作流、进程与 artifact；不认识具体实验名
│   ├── trace/                       # 观测生产、解析、对齐与 Perfetto；实验不得私建 trace/画图
│   └── env/                         # 锁定运行环境；操作契约见本目录 AGENTS.md
├── results/                         # 不可变运行证据；操作规则见 results/README.md
├── tests/                           # 契约与布局守卫；提交前从仓库根运行 python -m pytest
├── third_party/                     # git-subrepo pin；只读，除非用户明确授权 pin 操作
│   └── metronome/                   # baseline 依赖 pin；复制后永久分道，不追随上游
├── eurosys2027/                     # 论文写作工作区；不是事实 owner；写作规则见本目录 AGENTS.md
└── .github/                         # CI 工作流
```

除隐藏配置文件外，根目录只保留 map 所列条目。结构修改必须在同一事务内更新本 map、owner registry 与守卫测试，不能通过放宽断言隐藏不一致。

## Research Classification

论文叙事、文档评审和命名统一使用以下三层；本节是分类标准的唯一文字 owner，其他文档只应用分类结果，不复制整套规则。

| 层级 | 判定标准 | 文档位置 |
| --- | --- | --- |
| Research mechanism | 直接支撑 paper claim，具有明确因果假设，可独立 ablation，并有证据或明确的待验证状态 | 可进入 `docs/system.md` 的机制表和 `docs/findings.md` 的机制状态表 |
| System requirement | 研究设计成立所需的不变量或约束；规定系统必须满足什么，但不声称创新 | 写入 `docs/system.md` 的设计不变量或约束 |
| Implementation choice | 当前代码对 requirement 的一种可替换实现；用于 workflow、维护和诊断 | 写入实现流程、局部 `AGENTS.md` 或 registry，不进入贡献或机制列表 |

代码差异、独有开关或 matched baseline/Conveyor configuration 差异本身不构成 research mechanism。若替换某项接口、缓冲或同步实现而不改变 paper claim 与对应 ablation，该项应归为 implementation choice；由实现变化引出的测量口径可以形成 finding，但不能反向包装为机制创新。

## Change Transactions

机制语义、状态机、进程拓扑、IPC、实验协议或指标口径的改动，必须在同一事务内同步对应 owner 文档、registry 与测试；路径级映射见 [`docs/agent/change-impact.json`](docs/agent/change-impact.json)。新诊断 run 保留 raw artifacts 和结构化 record，有保留价值时登记 evidence；接受新结论同步 evidence alias、record、finding card 与 current-state table；仅实现尚未验证的优化不得提前修改 findings 的性能状态。

## Evidence Discipline

- 文档引用 `FINDING-*`、`CLAIM-*`、`EXP-*` 和 `EVIDENCE-*` 的完整命名空间，不使用裸 `C1`、`E1` 或 `H7`。
- 人类文档和结构化 record 不写具体时间戳 run ID；record 只引用 `EVIDENCE-*`，精确 ID 由 `docs/agent/evidence.json` 解析。
- 结论性数字标明实测、模拟器标定、线性外推或冻结先验，并带模型/配置域限定。
- formal evidence 要求 clean source；diagnostic evidence 可以 dirty，但必须保留可重建的 patch artifact；不满足新纪律的旧证据必须在 registry 中显式降级。
- 成功以 `status.json` 终态和 validation 为准，exit 0 本身不构成成功。

## Documentation Style

- [`docs/problem.md`](docs/problem.md#terminology) 是论文核心术语的唯一 canonical glossary：新增 paper-facing 核心词先更新词表、迁移旧同义词；实现 identifier 和 repository-governance vocabulary 不得进入 contribution 或 mechanism narrative。
- Agent JSON 使用稳定 ID、repo-relative path、symbol、owner 和 verification；不要使用易漂移的行号。
