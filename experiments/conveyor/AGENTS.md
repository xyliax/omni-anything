# conveyor（测量装置）

本目录只持有 Conveyor runner、system-specific config 和 validation。机制状态回到 `docs/findings.md`，协议回到 `docs/experiments.md`。

## Invariants

- 当前 offered input 和 output-cap source 与 matched baseline 共用，但 executed decode work 仍不同，不能称完全相同 workload。
- partial KV eviction 强制 synchronous scheduling；control configuration 必须钉住相同 mode。
- initial-context preloading 当前依赖 EngineCore patch 中的 streaming `max_tokens` fix；barrier 超时使 run 失败。
- preloading barrier 期间暂停 automatic eviction；结束时只解除暂停，第一次正常 idle transition 再建立 retained-prefix 状态。
- KV eviction 开启时必须有 `kv_events.log` 的 `E` 行；prefetch 开启时必须有 `L ... trigger=prefetch`。

## Usage

```bash
python -m experiments.conveyor --trace --duration 120
python -m experiments.conveyor --trace --initial-context-tokens 4096 --retained-prefix-blocks 128
python -m experiments.conveyor --trace --initial-context-tokens 4096 --retained-prefix-blocks 128 --prefetch push
python -m experiments.conveyor --trace --evict-tail-blocks 64
```

速查：release offsets 看 `gateway_ticks.log` 的间距与 `late_ms`；partial eviction 看 `E` 行、`host_backed` 和 residency；prefetch 看 `L/R trigger=prefetch`；输出缓冲看 `output_backlog` 是否持续增长。实际交付少于 cap 是诊断事实，不是自动 correctness failure。
