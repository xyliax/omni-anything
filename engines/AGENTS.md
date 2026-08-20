# Engines（系统层）

两个被比较的引擎本体。**只被 spawn，不被 import**——这是仓库边界约束，由守卫测试扫描 `import engines`，不靠缺少 `__init__.py` 强制（PEP 420 namespace package 仍可被 import）。第一方 experiment→engine 边界使用 argv+env、gRPC 和 run artifact；worker 与 vLLM EngineCore 子进程内部另有 msgpack/ZMQ utility IPC。引擎不认识 `experiments/`；引擎运行时唯一的第一方 Python 依赖是 `infra/trace` 的共享观测产出方。完整动态边见 `docs/agent/dynamic-edges.json`。

| 目录 | 引擎 | 驱动方 |
| --- | --- | --- |
| [`baseline/`](baseline/) | metronome 式 vLLM-realtime 栈（paringest worker + engine_fix） | `experiments/baseline/` |
| [`conveyor/`](conveyor/) | 新双工引擎（槽轮 gateway + 取现货 worker + engine_patch） | `experiments/conveyor/` |

正式比较使用的 paringest baseline 与 conveyor 统一走 `infra/trace/collectors/`（worker 经 sys.path 导入 worker_obs，engine 补丁链式加载 scheduler-trace 采集器）；不允许私有拷贝（`tests/test_run_validation.py` 钉住）。pin 内 vanilla worker 保留上游 logger，只作参考 target。
