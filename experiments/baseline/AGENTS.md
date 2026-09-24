# baseline（测量入口）

`paringest` 是 matched Metronome baseline 的 implementation identifier；`vanilla` 直接指向第三方 pin，只作 upstream reference。两者的每个数据点都启动 fresh worker，并把证据写入不可变 run 目录。

## Invariants

- `mode` 选择实现行为，`trace` 只选择观测。
- `paringest` 记录 `delivery output_token_cap=... deliv=...`。记录损坏、session death、RPC error 和 client failure 是 run issue；`deliv < output cap` 本身不再作为 correctness failure。
- initial-context preloading 只允许 `paringest`；EngineCore fix 逐 segment 刷新冻结的 `session.max_tokens`。
- 生成工作量差异与对照资格见 `docs/experiments.md#executed-decode-difference`，运行前核验实际 worker 配置。

## Usage

```bash
python -m experiments.baseline --trace --label my-label
python -m experiments.baseline --mode vanilla
python -m experiments.baseline --trace --sessions 16 --duration 120 --initial-context-tokens 4000
```

容量判读必须综合 `kv.log`、scheduler、session liveness 与 GPU utilization；client cadence 正常不证明模型仍在推进计算。
