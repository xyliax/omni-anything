# Results Evidence

代码与证据共享实验名：

```text
results/<experiment>/<run-id>/               # 一次运行证据（可同时保留多个 run）
results/<experiment>/aggregates/<id>/        # 跨 run 数据聚合（记录全部输入 run 与 hash）
```

Run ID 格式 `<YYYYMMDD>_<HHMMSS>_<label>`；参数细节全部在该 run 的 `manifest.json` 里，不进目录名。Run ID 只用于证据内部的 provenance，文档不得写死具体 ID。

Perfetto 导出（写入 run 的 `derived/`，只写一次）：

```bash
python -m infra.trace.perfetto <run-id-or-path>
```

## Evidence Boundary

| Experiment | 浏览入口 | 证据性质 |
| --- | --- | --- |
| baseline | `results/baseline/` | Upstream/Matched Metronome 或共享 worker 的全驻留 control；身份由 manifest `mode` / `evaluated_system` 区分 |
| conveyor | `results/conveyor/` | Conveyor 真实执行；机制与实现边界以 `docs/system.md` 为准 |

两个目录共享 offered-input、model 和 platform 常量，但历史 worker 的 per-segment decode cap 不同。当前代码统一 cap 不改变旧证据，公平比较必须重跑，不得把旧跨系统 run 描述为相同 executed workload。

上表目录用于维护者浏览，不直接构成 finding citation。引用已接受证据时先使用 `docs/agent/evidence.json` 中的 `EVIDENCE-*` alias，再由 alias 解析到 exact run；分析某次运行时才直接读取其 `manifest.json`、`status.json` 和 artifact hash。

## Retention Rules

- 新 run 的 raw 与 derived 文件保留在产出机器，默认不加入 Git；源码迁移不携带大型 GPU capture。已登记证据的 `distribution` 字段注明此边界。需要异机复算时另行传输对应完整目录并核验 registry hash，不能把源码 checkout 中缺少 raw 解释为证据不存在。结构化 record、索引与保留纪律仍随代码提交。

- runner 创建唯一目录，从不复用既有路径；先完成终态与验证，再由 Agent 按以下规则清理。保留中的 raw artifacts 不改写，目录不可复用不等于必须永久保留。
- 一次 run 只有 `status.json` 为 `state=success` 且 validation 通过才算执行成功；exit 0 本身不构成成功。升级为 formal evidence 还要满足 clean source、比较协议和重复次数要求。
- 终态有三种：`success` / `failed` / `interrupted`。操作者 SIGINT/SIGTERM 由 runner 自动记为 `interrupted`；SIGKILL 遗留的 `running` 不得手工覆盖原状态，恢复工具应追加带 operator、reason、timestamp 和原状态 hash 的 `recovery.json`。
- **Bug 修复后清旧结果。** 发现运行存在实现 bug，修复并验证后，Agent 必须删除对应的旧 bug 结果目录及其派生产物，不再要求用户手工删除或重复确认。必要的故障原因与修复验证保留在简短 record / 回归测试中。
- **每次报告前检查结果目录。** 每次向用户报告前，Agent 必须检查整个 `results/`，确认每个保留目录和派生产物都有明确的当前用途：有效实验依据、用户正在查看的交付物，或仍需定位的未解决问题。清掉无用途、已被替代和重复的产物；不能因为已经生成、已经登记 alias 或文件较小就保留。正在运行的目录须确认用途，不在进程仍写入时删除。
- **自行调试结果直接清理。** Agent 自己调试、检查 warmup、smoke test、探测环境或临时插桩产生的结果，在完成用途后直接删除，不混入交付结果；用户明确要求保留或已成为当前有效交付物的除外。按实际用途判断，不能仅按目录名是否包含 warmup / debug 判断。
- 清理是用户已授权的日常工作。同步处理 evidence alias、依赖聚合和可视化引用；已引用的历史 record 保留原观察，registry 明确标记原始产物已移除、不可再复算，不能继续声称其 raw artifacts 可用。保留中的诊断证据仍遵守原有 provenance 和 hash 约束。
- 人类核心文档和 Agent record 只引用 `EVIDENCE-*` alias，不引用实验级目录或时间戳 run ID；exact run 只由 evidence registry 与本证据层持有。
- 跨 run 分析只放在 `aggregates/`，且记录全部输入 run ID 与 hash；若输入 run 被清理，聚合也必须一并清理或重建，不能留下悬空来源。

## Evidence Registry

人类文档只引用稳定的 `EVIDENCE-*` alias。alias 到 exact run、证据等级和重建能力的映射在 `docs/agent/evidence.json`；run ID 不写进人类 prose。新 formal evidence 必须来自 clean worktree；dirty diagnostic run 必须保存 patch artifact。历史 run 不满足新纪律时在 registry 中显式标为 `legacy-unreconstructable`。
