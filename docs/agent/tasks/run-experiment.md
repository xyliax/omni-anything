# Run Experiment

## Read Set

1. `docs/experiments.md`
2. `experiments/AGENTS.md`
3. 目标 arm 的 `AGENTS.md`
4. `results/README.md`（Agent/维护者契约）
5. `docs/agent/contracts.json`

## Before Running

- 确认 measured 与 paper configuration 没有混用；
- 确认 controlled variables 与比较对象一致；
- 检查 GPU 空闲和模型 snapshot；
- 确认同一宿主没有另一仓库实验在运行；固定端口与 `/tmp/sfd_<index>.json` 不支持重叠 run；必须走受管 runner，让 workflow 清除旧 shard 文件并验证每个 shard 生成了本次结果；
- formal run 必须 clean；diagnostic dirty run 必须准备 source patch artifact；
- 为机制选择足够的 required artifacts 和 validation strings。

## After Running

1. 先读 `status.json` 和 issues；
2. 验证 required artifacts；
3. 生成或检查 Perfetto；
4. 写结构化 experiment record；
5. 只有证据被接受时才登记 `EVIDENCE-*`；
6. 只有结论发生变化时才修改 finding。

smoke 只能证明迁移后主路径可运行；controlled variables 不同的两臂 smoke 不得用于跨臂比较。
