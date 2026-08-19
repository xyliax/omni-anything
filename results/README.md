# Results

代码与证据共享实验名：

```text
results/<experiment>/<run-id>/               # 一次运行证据（可同时保留多个 run）
results/<experiment>/aggregates/<id>/        # 跨 run 数据聚合（记录全部输入 run 与 hash）
```

Run ID 格式 `<YYYYMMDD>_<HHMMSS>_<label>`；参数细节全部在该 run 的 `manifest.json` 里，不进目录名。Run ID 只用于证据内部的 provenance，文档不得写死具体 ID。

Perfetto 导出（写入 run 的 `derived/`，只写一次）：

```bash
python -m tracekit.perfetto <run-id-or-path>
```

## 证据边界

| Experiment | 稳定证据入口 | 证据性质 |
| --- | --- | --- |
| baseline | `results/baseline/` | 端到端 Qwen-Omni/vLLM/metronome 真实执行 |
| conveyor | `results/conveyor/` | 新引擎（错开相位 gateway + 取现货 worker），与 baseline 同模型同栈同 workload |

需要引用证据时引用上表中的实验级目录；具体 run ID、配置、状态和 artifact hash 从 run 目录内的 `manifest.json` / `status.json` 读取。

## 保留规则

- runner 创建唯一目录，从不复用既有路径，也不自动删除 run。
- 正式 run 的判据是 `status.json` 的 `state=success` 且 validation 通过；exit 0 本身不构成成功。
- 终态有三种：`success` / `failed` / `interrupted`。操作者 SIGINT/SIGTERM 由 runner 自动落成 `interrupted`；只有 SIGKILL 级别的硬杀会把 run 遗留在 `running`，此时由人把 `status.json` 的 `state` 手工订正为 `interrupted`。
- run 不做自动清理，版本库允许每个实验同时保留多个 run。删除旧 run 只发生在讨论定案之后：确认产生该 run 的实现 bug 已修复、且新证据已验收，才删除对应 bug 版本的 run；删除动作由人执行，历史需要时从 git 恢复。
- 文档只引用实验级稳定入口，不引用时间戳 run ID。替换当前证据不应触发文档路径修改。
- 跨 run 分析只住 `aggregates/`，且记录全部输入 run ID 与 hash；若输入 run 被清理，聚合也必须一并清理或重建，不能留下悬空来源。
