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
| baseline | `results/baseline/` | Upstream/Matched Metronome 的真实执行；身份由 manifest `mode` 区分 |
| conveyor | `results/conveyor/` | Conveyor 真实执行；机制与实现边界以 `docs/system.md` 为准 |

两个目录共享 offered-input、model 和 platform 常量，但历史 worker 的 per-segment decode cap 不同。统一 cap 并重跑前，不得把旧跨系统 run 描述为相同 executed workload。

上表目录用于维护者浏览，不直接构成 finding citation。引用已接受证据时先使用 `docs/agent/evidence.json` 中的 `EVIDENCE-*` alias，再由 alias 解析到 exact run；分析某次运行时才直接读取其 `manifest.json`、`status.json` 和 artifact hash。

## Retention Rules

- runner 创建唯一目录，从不复用既有路径，也不自动删除 run。
- 一次 run 的执行状态成功要求 `status.json` 为 `state=success` 且 validation 通过；exit 0 本身不构成成功。升级为 formal evidence 还要满足 clean source、比较协议和重复次数要求。
- 终态有三种：`success` / `failed` / `interrupted`。操作者 SIGINT/SIGTERM 由 runner 自动落成 `interrupted`；SIGKILL 遗留的 `running` 不得手工覆盖原状态，恢复工具应追加带 operator、reason、timestamp 和原状态 hash 的 `recovery.json`。
- run 不做自动清理，版本库允许每个实验同时保留多个 run。删除旧 run 只发生在讨论定案之后：确认产生该 run 的实现 bug 已修复、且新证据已验收，才删除对应 bug 版本的 run；删除动作由人执行，历史需要时从 git 恢复。
- 人类核心文档和 Agent record 只引用 `EVIDENCE-*` alias，不引用实验级目录或时间戳 run ID；exact run 只由 evidence registry 与本证据层持有。
- 跨 run 分析只住 `aggregates/`，且记录全部输入 run ID 与 hash；若输入 run 被清理，聚合也必须一并清理或重建，不能留下悬空来源。

## Evidence Registry

人类文档只引用稳定的 `EVIDENCE-*` alias。alias 到 exact run、证据等级和重建能力的映射在 `docs/agent/evidence.json`；run ID 不写进人类 prose。新 formal evidence 必须来自 clean worktree；dirty diagnostic run 必须保存 patch artifact。历史 run 不满足新纪律时在 registry 中显式标为 `legacy-unreconstructable`。
