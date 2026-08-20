# Experiment Records

新实验过程每次一个 JSON 文件，命名为 `<date>-<short-question>.json`；不要继续追加 `legacy-experiment-log.md`。record 保存问题、配置、改动、结果和判断，exact run 仍由 `evidence.json` 持有。

创建时复制 [`template.json`](template.json)，满足 `../contracts.json` 的 `experiment_record_v1.required_fields`。规则：

- `record_id` 使用稳定大写 ID；
- `verdict` 区分 diagnostic、accepted、superseded 和 rejected；
- `evidence` 只写已登记或准备登记的 `EVIDENCE-*`；
- `affects_findings` 使用完整 `FINDING-*`；
- failed run 的机制教训可以保留，但不能自动成为性能结论；
- record 一经被 finding 引用，不原地改写历史结果；后续记录通过 `supersedes` 连接。
