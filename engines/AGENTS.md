# Engines（系统层）

两个被比较的引擎本体。**只被 spawn，不被 import**——这是架构约束，由守卫测试钉住（扫描全仓 `import engines` 形），不靠机制强制：不放 `__init__.py` 只是标记（Python 3 的 namespace package 机制下没有它照样可以 import）。跨进程通道只有 argv+env、gRPC、run 目录文件三种；引擎不认识 `experiments/`（测量装置在那边，按路径引用这里）；引擎运行时唯一的第一方依赖是 `infra/trace` 的共享观测产出方（worker 经 sys.path 导入，两臂同一份仪器）。

| 目录 | 引擎 | 驱动方 |
| --- | --- | --- |
| [`baseline/`](baseline/) | metronome 式 vLLM-realtime 栈（paringest worker + engine_fix） | `experiments/baseline/` |
| [`conveyor/`](conveyor/) | 新双工引擎（槽轮 gateway + 取现货 worker + engine_patch） | `experiments/conveyor/` |

引擎观测统一走 `infra/trace/collectors/`（worker 经 sys.path 导入 worker_obs，engine 补丁链式加载 scheduler-trace 采集器）；两臂必须使用同一份仪器产出方，不允许私有拷贝（`tests/test_run_validation.py` 钉住）。
