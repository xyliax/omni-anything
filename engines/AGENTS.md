# 引擎层

引擎由 runner 按路径启动，禁止 import `experiments`。仓内启动与 IPC 的索引见 `docs/agent/dynamic-edges.json`。

| 目录 | 系统 | 启动方 |
| --- | --- | --- |
| `baseline/` | matched Metronome baseline | `experiments/baseline/` |
| `conveyor/` | Pilarius 的实现目录 | `experiments/conveyor/` |

正式比较共用 `infra/trace/collectors/`。生成工作量、调度及副本路径的匹配要求见 `docs/experiments.md#executed-decode-difference`；不能由配置名称推定公平。局部说明用于定位，改代码前核验实际路径。
