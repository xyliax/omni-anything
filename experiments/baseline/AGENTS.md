# baseline

真机 baseline：现有 vLLM-realtime 栈如何 serve 双工负载。每次运行起一个全新 worker，证据先落入 `results/baseline/runs/<run-id>/` 的不可变目录；版本库只保留最新且有效的一份，文档引用稳定入口 `results/baseline/runs/`。

## 不变量

- **`mode` 是行为，`trace` 是观测**：观测开关绝不表示为另一个实现模式。
- `runner.py` 只声明本实验的差异（命令、环境、issue 扫描），组装 `RunPlan` 交 `lab/workflow` 执行；config / artifacts 不导入编排。
- `worker_python` 不做 `resolve()`：Python 靠被调用的 venv 路径找 `pyvenv.cfg`。
- runner 会完整保留本次运行现场；exit 0 不能救有 issue 的 run；操作者中断（SIGINT/SIGTERM）落成 `interrupted` 终态。版本库的长期保留规则见 `results/README.md`。

## 模式

| mode | worker | 说明 |
| --- | --- | --- |
| `vanilla` | `third_party/metronome/worker/stream_server.py`（pin 内，原样） | 参照 baseline |
| `paringest` | `worker/stream_server.py` | 并行 ingest 修复 + 插桩 |

`worker/stream_server.py` 复制自 pin 内同名 worker 后**永久分道**（文件名刻意与 metronome 一致；不追上游更新；与来源的行为差异清单见其 docstring 的 ORIGIN 节）。不允许任何实验再造第二份拷贝。

## 用法

```bash
python -m experiments.baseline --trace --label my-label   # paringest 是默认 mode
python -m experiments.baseline --mode vanilla
python -m experiments.baseline --trace --sessions 16 --duration 120 --seed-tokens 4000
```

参数唯一来源是 `config/`：`model.py` / `platform.py` / `workload.py` 是本栈的固定事实（纯常量），`__init__.py` 持有逐 run 旋钮与引擎常量。命令行只暴露逐 run 会变的旋钮（mode / trace / label / sessions / duration / seed-tokens / gpu）；改常量直接改 `config/` 下对应文件。

## 判读

健康判据看 `kv.log` 的 starvation 信号，不要只看客户端 miss=0%（silent failure：会话崩溃后 cadence 指标仍全部正常）。Perfetto 导出：`python -m tracekit.perfetto baseline/<run-id>`。
