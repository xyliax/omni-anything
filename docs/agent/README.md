# Agent Task Router

本目录是面向 Agent 的导航和操作层，不构成第二套项目事实。研究语义必须回到 `docs/problem.md`、`docs/system.md`、`docs/experiments.md` 和 `docs/findings.md`；本目录只持有组件定位、动态边、修改影响、验证方法和 evidence alias。

## Read Policy

1. 先从根 `AGENTS.md` 判断任务；
2. 只加载对应 task guide 指定的 read-set；
3. 修改目录前读取最近一层 `AGENTS.md`；
4. 遇到数字或机制状态，回到 `docs/findings.md`；
5. 遇到 exact run 或 provenance，查询 `evidence.json`；
6. 不根据静态 import 图猜测 subprocess、gRPC、ZMQ 或 monkeypatch，查询 `dynamic-edges.json`。
7. 判断代码差异能否进入 paper 机制列表时，只读取根 [`AGENTS.md`](../../AGENTS.md#research-classification) 的 `Research Classification`，本目录不另建分类标准。
8. paper-facing 命名必须先查 [`docs/problem.md`](../problem.md#terminology)；实现 identifier 不得反向成为论文术语。

## Registries

| Registry | Owns |
| --- | --- |
| [`ownership.json`](ownership.json) | 事实域 owner 与禁止复制规则 |
| [`system-map.json`](system-map.json) | 仓内组件的 source path/entrypoint，以及外部 runtime node 的 locator/process role |
| [`dynamic-edges.json`](dynamic-edges.json) | subprocess、gRPC、ZMQ、sitecustomize、runtime patch 与 artifact 边 |
| [`contracts.json`](contracts.json) | 不变量、failure behavior 与 verification |
| [`change-impact.json`](change-impact.json) | path change 到必查文档/测试的映射 |
| [`evidence.json`](evidence.json) | `FINDING-*` 到 evidence alias、exact run 与重建能力 |

## Task Guides

| Task | Guide |
| --- | --- |
| 从零理解完整 runtime | [`understand-runtime.md`](tasks/understand-runtime.md) |
| 修改 engine 或机制 | [`modify-engine.md`](tasks/modify-engine.md) |
| 新增、修改或运行实验 | [`run-experiment.md`](tasks/run-experiment.md) |
| 解释一次 run 或 Perfetto | [`analyze-results.md`](tasks/analyze-results.md) |
| 接受新结论或更新证据 | [`update-findings.md`](tasks/update-findings.md) |

## Historical Records

[`legacy-experiment-log.md`](legacy-experiment-log.md) 由旧 append-only 日志迁移而来并已冻结，不是 current-state owner，也不是 paper prose source。它保留历史术语和过时的研究表述；只有用户明确要求分析历史实验时才读取。后续 experiment record 按 [`records/README.md`](records/README.md) 创建，使用 `contracts.json` 中的 `experiment_record_v1` 字段；只有被接受的结论才进入 findings。
