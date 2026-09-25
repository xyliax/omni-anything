# engines/baseline

matched Metronome baseline 的仓库自有引擎代码，由 `experiments/baseline/` 按路径 spawn。

- `worker/stream_server.py` 从第三方 Metronome worker 分叉后加入 parallel input processing、initial-context preloading 和共同观测。生成上限差异及公平性资格见 `docs/experiments.md#executed-decode-difference`。
- `worker/engine_fix/` 只在 initial-context run 注入，通过 `OMNI_SESSION_MAXTOKENS_FIX` 刷新 upstream 冻结的 `session.max_tokens`。这是 implementation bug fix，不是研究机制。
- worker observation 统一使用 `infra/trace/collectors/worker_obs.py`；不得为某个 system 复制私有 collector。
- `third_party/metronome/` 的 `vanilla` worker 保持只读，只作 Upstream Metronome reference。

新增 cohort 全驻留参照使用 `engines/conveyor/worker/stream_server.py` 的 resident control 路径和 `resident_adapter.py`，共享周期输入、排空及指标协议；它不加载 KV offload connector。该参照由 `experiments.conveyor` 的显式 resident-control 配置启动，manifest 使用独立 evaluated-system 身份，不能称为未经改动的 Metronome。
