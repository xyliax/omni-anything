# engines/baseline

matched Metronome baseline 的仓库自有引擎代码，由 `experiments/baseline/` 按路径 spawn。

- `worker/stream_server.py` 从第三方 Metronome worker 分叉后加入 parallel input processing、initial-context preloading 和共同观测。它当前每 segment 配置 \(M+8\) 的 decode cap；这是待修实验缺陷，不是 workload requirement。
- `worker/engine_fix/` 只在 initial-context run 注入，通过 `OMNI_SESSION_MAXTOKENS_FIX` 刷新 upstream 冻结的 `session.max_tokens`。这是 implementation bug fix，不是研究机制。
- worker observation 统一使用 `infra/trace/collectors/worker_obs.py`；不得为某个 system 复制私有 collector。
- `third_party/metronome/` 的 `vanilla` worker 保持只读，只作 Upstream Metronome reference。
