# engines/conveyor

Pilarius 的引擎实现（目录标识 `conveyor`），由 `experiments/conveyor/` 按路径 spawn。本文件只用于代码定位，不证明新设计已实现；修改前核验目标路径。论文术语和机制语义见 `docs/problem.md#terminology` 与 `docs/system.md`。

## Local Workflow

- `gateway/main.go`：绝对 release grid；会话建立时分配稳定 slot。`--output-token-cap` 是 gateway 最多消费的 token 数，不是最低交付要求。继承的 `deadline_met` wire field 只报告当前 service RPC 是否在 period 内返回。
- `worker/stream_server.py`：把 input chunk 入队后快照 undelivered-output buffer，不等待本次计算；`output_backlog` 记录缓冲深度。当前路径只输出 Thinker text。
- `worker/engine_patch/omni_evict.py`：incremental host backing、idle-session partial KV eviction、on-demand reload instrumentation 和 streaming bug fixes。新事件写 `kv_events.log`：`E` eviction、`B` host backing、`L/R` load window。
- `omni_state.py`：只保存 session activity、prefetch control 和时间戳；GPU/host block coverage 每次查询 pools，不维护伪 lifecycle。
- `omni_prefetch.py` / `omni_prefetch_transport.py`：KV prefetch command、capacity deferral 和 transport adapter。synthetic ID 与 hash registration 是 implementation choices。

partial eviction 当前强制 synchronous scheduling。initial-context preloading 期间 `OMNI_HOLD_KV_EVICTION` 暂停 automatic eviction；`initial_context_finalize` 只解除暂停，不在 barrier 处立即逐出。patch 加载失败 exit 78。
