# Experiments（测量层）

两臂对比的测量装置：协议入口、runner、公平性常量。**引擎本体在 `engines/`**（被 runner 按路径 spawn，不被 import）；协议的唯一权威是 [`../docs/experiments.md`](../docs/experiments.md)。每臂目录与 `results/` 下同名目录对应。

| 目录 | 内容 | 对应引擎 | 证据 |
| --- | --- | --- | --- |
| [`shared/`](shared/) | 公平性定义域：workload / model / platform 常量（单份，两臂 import） | — | — |
| [`baseline/`](baseline/) | `__main__.py` + `config.py` + `runner.py` | `engines/baseline/` | `results/baseline/` |
| [`conveyor/`](conveyor/) | `__main__.py` + `config.py` + `runner.py` | `engines/conveyor/` | `results/conveyor/` |

## 公共规则

- **常量的归属判据**：负载/模型/平台常量住 `shared/`——公平性要求两臂相同，改一处即改两臂，由结构保证；臂行为常量（park、prefetch、slots、mode 这类被比较的机制参数）住各臂 `config.py`，各臂独立声明、互不知晓。每个默认值只声明一次——worker 的引擎几何参数因此全部必填，不设第二套 argparse 默认值；CLI 只暴露逐 run 会变的旋钮。
- **引擎不认识测量**：runner 按路径引用 `engines/`；第一方 experiment→engine 边界使用 argv+env、gRPC 和 run artifact，引擎侧没有任何对 experiments 的 import。worker→EngineCore 的 vLLM 内部 msgpack/ZMQ utility IPC 见 `docs/agent/dynamic-edges.json`。
- **trace 归 `infra/trace/`**：实验只产出原始日志；解析、对齐、Perfetto 导出全在 trace 套件。临时画图是一次性行为，产物不入库。
- **运行工作流归 `infra/run/workflow.py`**：runner 只声明本臂差异（命令、环境、issue 扫描，组装 `RunPlan`）；就绪等待、client 看门狗、interrupted 语义、收尾判决全仓只有一份。
- **run 目录归 `infra/run/artifacts.py`**：全仓库唯一实现；运行时完整落盘，成功判据是 validation 通过，exit 0 本身不算数。run 不做自动清理，旧 run 的删除经讨论定案后由人执行（规则见 `results/README.md`）。
- **判 run 成败的日志字符串是契约**：产出方（含 Go gateway）与扫描方由 `tests/test_run_validation.py` 钉在一起，改措辞必须让测试红。
- **文件系统只代表已存在的代码**：未实现的实验臂写在 `docs/experiments.md` 的路线图里。
