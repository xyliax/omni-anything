# engines/baseline

baseline 引擎本体：metronome 式 vLLM-realtime worker（paringest 模式）+ seed run 的 engine_fix 补丁。由 `experiments/baseline/` 按路径 spawn（argv+env 驱动，无 Python import）。

- **`worker/stream_server.py`** 复制自 `third_party/metronome/worker/stream_server.py` 后**永久分道**（文件名刻意与 metronome 一致；不追上游更新；与来源的行为差异清单见其 docstring 的 ORIGIN 节）。不允许任何实验再造第二份拷贝。
- **`worker/engine_fix/`** 只在 seed run 注入（`OMNI_SESSION_MAXTOKENS_FIX` 门控，PYTHONPATH 前置 sitecustomize）：刷新被上游冻结的 `session.max_tokens`，非机制改动；随后链式加载 `infra/trace` 的 scheduler-trace 采集器。
- 引擎观测统一 import `infra/trace/collectors/worker_obs.py`（两臂同一份仪器产出方，`tests/test_run_validation.py` 钉住）。
