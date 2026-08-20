# Analyze Results

## Read Set

1. `docs/experiments.md#metric-semantics`
2. `docs/system.md#one-session-cycle`
3. `infra/trace/AGENTS.md`
4. 对应 `status.json`、`manifest.json` 和 raw artifacts
5. `docs/agent/evidence.json`

## Analysis Order

1. 按 `evidence.json.role_definitions` 判断证据是 formal、diagnostic、source audit、external audit 还是 legacy-unreconstructable；
2. 检查 workload、model、GPU、seed、scheduling 与 observation；
3. 检查 session death、从未足额的 session、首次足额后的 starvation、inventory drift 和 missing artifacts；
4. 使用 C 双时钟行；仅历史 run 允许启发式对齐；
5. 沿 one-session cycle 对齐 gateway、ingest、prefill、decode、reload、park；
6. 将结论限制在证据实际支持的 scope。

## Forbidden Inferences

- client miss=0 不等于系统健康；
- conveyor 的 Step latency 不等于 GPU latency；
- scheduler slice 不等于 CUDA execution duration；
- 单次 smoke 不等于性能结论；
- dirty 且没有 patch artifact 的 run 不等于可复现 formal evidence。
- `legacy-unreconstructable` 和 `source-audit` 都不能支撑新的性能数字。
