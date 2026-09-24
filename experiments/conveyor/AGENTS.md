# conveyor（测量入口）

本目录只持有 Pilarius runner、system-specific config 和 validation。机制状态见 `docs/findings.md`，协议见 `docs/experiments.md`。

## Invariants

- 公平性按 `docs/experiments.md#executed-decode-difference` 核验实际工作量与路径，不能由共用 offered-load 常量推定。
- partial KV eviction 强制 synchronous scheduling；control configuration 必须固定为相同 mode。
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

速查：release offsets 看 `gateway_ticks.log` 的间距与 `late_ms`；partial eviction 看 `E` 行、`host_backed` 和 residency；prefetch 看 `L/R trigger=prefetch`；输出缓冲看 `output_backlog` 是否持续增长。实际交付少于 cap 是诊断事实，不自动构成 correctness failure。
