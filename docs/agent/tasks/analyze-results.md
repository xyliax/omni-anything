# Analyze Results

## Read Set

1. `results/README.md`；
2. 目标 run 的 `manifest.json`、`status.json` 与 raw artifacts；
3. `docs/experiments.md` 的 measurement semantics；
4. `infra/trace/AGENTS.md` 与 parser/exporter；
5. 需要与已接受结论比较时，再读 `docs/findings.md` 与 `docs/agent/evidence.json`。

## Analysis Order

1. 先验证 terminal state、required artifact hashes、git provenance 与 evidence role。
2. 检查 workload、model、GPU、initial context、scheduling mode、output cap 和 observation 配置。
3. 检查 session death、RPC/client error、初始化超时、缺失或畸形 delivery records，以及已启用 KV 机制是否真正产生事件。
4. 把观察到的事件对齐到 one-session cycle 的各阶段：gateway release、input processing、scheduler admission、KV reload/prefetch、prefill、decode、partial eviction。
5. 分开解释 application release latency、service-RPC latency、engine iteration time、模型生成量、保留历史量、交付量和 output backlog；它们不可相互替代。
6. 使用 `kv_events.log` 的 `E/B/L/R` 事件解释逐出、存储 cursor 推进、装载发起与完成上报。B 可含跳过存储的块，不是已确认 D2H 字节；L–R 可含调度等待，不是纯 DMA 时长。结合 producer、有效主机覆盖与实际调度识别缺口后的重算。
7. 分别判断执行状态、观测有效性、机制是否实际被使用和服务目标；失败 run 可以支持失效边界，零预取须区分无需求、门控和故障。
8. 标记数字是实测、模拟器标定、线性外推还是冻结先验，并写清配置域。

## Field Semantics

以下为纯读数语义字段的逐项解释。`deadline_met` 与 `gpu_ms` 因跨系统语义或执行路径差异直接影响公平性与结果解释，由 [docs/experiments.md](../../experiments.md#implementation-diagnostics) 持有；`E/B/L/R` 事件的解释见上文 Analysis Order 第 6 步，不在此重复。

| 字段 | 当前解释及限制 |
| --- | --- |
| `tokens_per_tick` / `tpt` | 继承接口字段，解释为 cap，不是每周期最低交付量 |
| `deliv` | 当次从缓冲取出的 token 数，不等于本次输入生成量或新鲜度 |
| `output_backlog` | 已生成未交付量，不能自行充当论文 SLO |

## Output Discipline

单个 run 的新观察先进入结构化 record；只有被接受的结论才能更新 finding card 和 evidence alias。不要仅凭 cadence 检查通过、单次 `deadline_met`、输出达到上限或 short output 就推断 correctness、freshness 或 playback QoE。
