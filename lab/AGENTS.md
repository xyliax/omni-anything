# lab

实验无关的运行基础设施（~500 行，四个文件）。**不认识任何实验的名字**——被两个实验的 runner 导入，自己不导入实验；唯一的反向边是复用 `environment/verify.py` 的探测函数（`capture` / `collect_software`）。

| 文件 | 职责 | 关键契约 |
| --- | --- | --- |
| `workflow.py` | 全仓唯一的运行时间线：实验 runner 声明 `RunPlan`（命令、环境、证据名、issue 扫描），`execute` 负责先后与安全——manifest 先于一切进程、worker 等 ready、辅助进程、client、收尾判决 | client 有看门狗（超时杀进程并记 issue，无人值守扫描不悬挂）；SIGINT/SIGTERM 落成 `interrupted` 终态；任何退出路径都经 `finally` 杀进程组 + finalize；行为由 `tests/test_lab_workflow.py` 在假子进程上钉住 |
| `artifacts.py` | 不可变 run 目录的唯一实现（`RunStore`）：创建、写状态、收证据、finalize 判决 | `mkdir` 无 `exist_ok`（目录绝不复用）；元数据原子替换、证据只写一次；`finalize` 校验必需 artifact——**缺失或空文件即 issue，exit 0 救不了带 issue 的 run**；三种终态 success / failed / interrupted，全部保留。`scan_worker_fatal` 用窄模式（OOM / EngineCore 启动失败 / trace 初始化失败）扫 worker 日志 |
| `probes.py` | provenance 快照：git 状态、third_party pin、主机、GPU、模型 snapshot 路径 | 只读探测、错误记录不抛；例外是 `resolve_model_snapshot`——模型 revision 锁定的执行点（锁定 snapshot 路径直接进 worker argv），snapshot 不在缓存时 fail-fast 而非静默 None |
| `process.py` | 进程组编排：启动子进程（stdout/stderr 重定向到 run 目录）、`cleanup()` 终止整组、`tail_text` 取日志尾部 | `start_new_session=True`，按 PGID 杀是收掉 vLLM EngineCore 子进程的唯一可靠办法；日志 `"xb"` 模式绝不追加；workflow 的 `finally` 依赖 `cleanup()` 兜底——任何路径退出都不留孤儿 GPU 进程 |

新实验接入时按 `docs/architecture.md`「新实验的接入形状」使用这四件；不要在实验目录里复制它们的功能。
