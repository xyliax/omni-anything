# Experiments

主实验（定义与协议的唯一权威是 [`../docs/experiments.md`](../docs/experiments.md)）：baseline 引擎可运行且冻结；conveyor 引擎增量实现中。每个目录有自己的 AGENTS.md 与单一入口，与 `results/` 下同名目录对应。

| 目录 | 角色 | 状态 | 证据 |
| --- | --- | --- | --- |
| [`baseline/`](baseline/) | baseline 引擎：metronome 的 vLLM 栈 + paringest 模式 | 可运行，有正式 run；**已冻结** | `results/baseline/` |
| [`conveyor/`](conveyor/) | 新引擎：错开相位 gateway + 取现货 worker + 镜像/park/回载全链路 | 三个机制增量已验证（FINDINGS H 系列）；容量主张待正式 run | `results/conveyor/` |

## 公共规则

- **trace 归 `tracekit/`**：实验只产出原始日志；解析、对齐、Perfetto 导出全在 trace 套件。临时画图是一次性行为，产物不入库。
- **配置是实验私有的**：每个实验目录自带 `config/`（纯 Python 常量文件），每个默认值只声明一次——worker 的引擎几何参数因此全部必填，不设第二套 argparse 默认值。CLI 只暴露逐 run 会变的旋钮。
- **运行工作流归 `lab/workflow.py`**：runner 只声明本实验的差异（命令、环境、issue 扫描，组装 `RunPlan`）；就绪等待、client 看门狗、interrupted 语义、收尾判决全仓只有一份。
- **run 目录归 `lab/artifacts.py`**：全仓库唯一实现；失败 run 一律保留；成功判据是 validation 通过，exit 0 本身不算数。
- **判 run 成败的日志字符串是契约**：产出方（含 Go gateway）与扫描方由 `tests/test_run_validation.py` 钉在一起，改措辞必须让测试红。
- **文件系统只代表已存在的代码**：未实现的实验臂写在 `docs/experiments.md` 的路线图里。
