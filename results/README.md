# Results

代码与证据共享实验名：

```text
results/<experiment>/runs/<run-id>/          # 当前保留的一次运行证据
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
| baseline | `results/baseline/runs/` | 端到端 Qwen-Omni/vLLM/metronome 真实执行 |
| conveyor | `results/conveyor/runs/` | 新引擎（错开相位 gateway + 取现货 worker），与 baseline 同模型同栈同 workload |

每个稳定入口下只保留一个当前有效 run。需要引用证据时引用上表中的实验级目录；具体 run ID、配置、状态和 artifact hash 从该目录内唯一 run 的 `manifest.json` / `status.json` 读取。

## 保留规则

- runner 创建唯一目录，从不复用既有路径，也不自动删除 run。
- 正式 run 的判据是 `status.json` 的 `state=success` 且 validation 通过；exit 0 本身不构成成功。
- 终态有三种：`success` / `failed` / `interrupted`。操作者 SIGINT/SIGTERM 由 runner 自动落成 `interrupted`；只有 SIGKILL 级别的硬杀会把 run 遗留在 `running`，此时由人把 `status.json` 的 `state` 手工订正为 `interrupted`。
- 版本库对每个实验只保留最新且仍有效的一次运行证据。新证据验收后，由人删除同实验的旧 run；失败、被中断或已被更新证据取代的目录不长期留在版本库中，历史需要时从 git 恢复。
- 文档只引用实验级稳定入口，不引用时间戳 run ID。替换当前证据不应触发文档路径修改。
- 跨 run 分析只住 `aggregates/`，且记录全部输入 run ID 与 hash；若输入 run 被清理，聚合也必须一并清理或重建，不能留下悬空来源。
