# Agent 导航

根 `AGENTS.md` 是唯一项目入口。本目录只维护代码导航、操作约束与证据索引，不保存第二套研究结论。用户最新说明优先；缺少机制细节时询问用户，不能从旧稿或旧实现猜测。

## 最小读取范围

| 任务 | 读取 |
| --- | --- |
| 论文措辞与结构 | 目标正文、`docs/PAPER.md`、`eurosys2027/AGENTS.md`；事实按域查 owner |
| Design 写作或实现交接 | [系统设计](../system.md#logical-architecture) → [运行流程与伪代码](../system.md#operational-flow) → [未决设计](../system.md#open-design-decisions)；代码任务继续按 modify-engine 读取实现入口与验收要求 |
| 问题或设计讨论 | `docs/problem.md` 或 `docs/system.md` 的相关节；证据按需查 Findings |
| 理解运行路径 | [understand-runtime](tasks/understand-runtime.md) |
| 修改引擎 | [modify-engine](tasks/modify-engine.md) |
| 设计或运行实验 | `docs/experiments.md`；实际运行再读 [run-experiment](tasks/run-experiment.md) |
| 分析 run | [analyze-results](tasks/analyze-results.md) |
| 接受新结论 | [update-findings](tasks/update-findings.md) |

修改路径前读取最近 `AGENTS.md`。组件和动态绑定分别查 `system-map.json`、`dynamic-edges.json`；不根据静态 import 猜跨进程调用。运行前核验代码和配置，旧审计不是当前功能证明。

## Registry

| 文件 | 职责 |
| --- | --- |
| [ownership.json](ownership.json) | 事实域与唯一 owner |
| [system-map.json](system-map.json) | 组件、入口及外部运行节点 |
| [dynamic-edges.json](dynamic-edges.json) | subprocess、IPC、注入与 artifact 边 |
| [contracts.json](contracts.json) | 不变量与验证入口；注明设计要求与实现事实 |
| [change-impact.json](change-impact.json) | 改动需同步的文档和检查 |
| [evidence.json](evidence.json) | 按 `EVIDENCE-*` 定位 exact run、hash 和 provenance |

历史材料只按目标 ID 或具体问题读取：`records/` 与 `legacy-experiment-log.md` 保留实验历史，后者已冻结。`docs/papers/` 与 `docs/references/` 是外部资料，不加入默认 read-set，不以其旧比较结论约束新设计。新记录按 [records/README.md](records/README.md) 创建。
