# Engines（系统层）

两个可执行 serving system。它们只被 runner 按路径 spawn，不被 `experiments` import；第一方 experiment→engine 边界使用 argv、env、gRPC 和 run artifacts。worker 与 vLLM EngineCore 之间另有 msgpack/ZMQ utility IPC。完整动态边见 `docs/agent/dynamic-edges.json`。

| 目录 | 系统身份 | 驱动方 |
| --- | --- | --- |
| [`baseline/`](baseline/) | matched Metronome baseline；`vanilla` 仅为 upstream artifact target | `experiments/baseline/` |
| [`conveyor/`](conveyor/) | Conveyor：release offsets、partial KV eviction、KV prefetch | `experiments/conveyor/` |

正式比较候选统一使用 `infra/trace/collectors/`。当前 matched baseline 的 per-segment decode cap 仍为 \(M+8\)，Conveyor 为 \(M\)；修复并重跑前不得称为完全相同的 executed workload。
