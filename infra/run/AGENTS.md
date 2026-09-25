# infra/run

实验无关的运行基础设施。**不引用任何实验的名字**——由 runner 调用，自己不导入实验；复用 `infra/env/verify.py` 的探测函数（`capture` / `collect_software`）。

| 文件 | 职责 | 关键契约 |
| --- | --- | --- |
| `workflow.py` | 全仓唯一的运行时间线：实验 runner 声明 `RunPlan`（命令、环境、证据名、issue 扫描），`execute` 负责执行顺序与安全——manifest 先于一切进程、worker 等 ready、辅助进程、client、收尾判定终态 | client 有看门狗；固定 shard scratch 在启动前清旧、逐 shard 验新、退出时清理；SIGINT/SIGTERM 记为 `interrupted`；任何退出路径都经 `finally` 杀进程组 + finalize；行为由 `tests/test_run.py` 在假子进程上覆盖 |
| `artifacts.py` | 不可变 run 目录的唯一实现（`RunStore`）：创建、写状态、收证据、finalize 判定终态 | `mkdir` 无 `exist_ok`（目录绝不复用）；元数据原子替换、证据只写一次；`finalize` 校验必需 artifact——**缺失或空文件即 issue，exit 0 本身不能让带 issue 的 run 算成功**；三种终态 success / failed / interrupted，全部保留。共享 scanner 统一解释 client health，并用收窄的匹配模式扫描 OOM、EngineCore/trace 初始化失败和 initialization-barrier timeout |
| `probes.py` | provenance 快照：git 状态、third_party pin、主机、GPU、模型 snapshot 路径 | 只读探测、错误记录不抛；例外是 `resolve_model_snapshot`——模型 revision 锁定在这里生效（锁定 snapshot 路径直接进 worker argv），snapshot 不在缓存时 fail-fast，而不是静默返回 None |
| `process.py` | 进程组编排：启动子进程（stdout/stderr 重定向到 run 目录）、`cleanup()` 终止整组、`tail_text` 取日志尾部 | 使用 `start_new_session=True` 建立进程组，workflow 在 `finally` 中按 PGID 清理，包括组内 EngineCore 子进程；日志以 `"xb"` 模式创建，不追加旧文件 |

新实验按 `docs/agent/tasks/run-experiment.md` 和 `docs/agent/system-map.json` 接入共享运行设施，不在实验目录复制运行生命周期。
