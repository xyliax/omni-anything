# Experiments（测量层）

本目录持有配置、runner、公平性常量与 validation；引擎本体在 `engines/`。协议唯一 owner 是 [`docs/experiments.md`](../docs/experiments.md)。

| 目录 | 内容 | 对应系统 |
| --- | --- | --- |
| [`shared/`](shared/) | offered workload、model、platform 常量 | 两个系统共同读取 |
| [`baseline/`](baseline/) | Upstream/Matched Metronome 配置和 runner | `engines/baseline/` 与 third-party pin |
| [`conveyor/`](conveyor/) | Pilarius 配置和 runner | `engines/conveyor/` |

## 公共规则

- `shared/` 只保存必须共同读取的 offered-load、model 和 platform 常量。system-specific mechanism 和 implementation knobs 留在各自 `config.py`。
- offered input 同源不等于 executed decode work 相同；任何公平性陈述必须同时检查 worker command 与 manifest。
- runner 只声明 command、environment 和 issue scanner；生命周期由 `infra/run/workflow.py` 单份实现。
- experiment 只产 raw logs；解析、时钟对齐和 Perfetto 属于 `infra/trace/`。
- validation 扫描器的行为由 `tests/test_run_validation.py` 覆盖。
- 当前未实现的 evaluation 只写在 `docs/experiments.md` 的计划中，不创建假配置。
