# baseline（测量装置）

真机 baseline 臂：现有 vLLM-realtime 栈如何 serve 双工负载。引擎本体在 `engines/baseline/`。每次运行起一个全新 worker，证据先落入 `results/baseline/<run-id>/` 的不可变目录；run 不做自动清理，旧 run 的删除经讨论定案后由人执行（规则见 `results/README.md`），人类文档通过 `EVIDENCE-*` alias 引用。

## 不变量

- **`mode` 是行为，`trace` 是观测**：观测开关绝不表示为另一个实现模式。
- `runner.py` 只声明本臂的差异（命令、环境、issue 扫描），组装 `RunPlan` 交 `infra/run/workflow` 执行；config / artifacts 不导入编排。
- `worker_python` 不做 `resolve()`：Python 靠被调用的 venv 路径找 `pyvenv.cfg`。
- runner 会完整保留本次运行现场；exit 0 不能救有 issue 的 run；操作者中断（SIGINT/SIGTERM）落成 `interrupted` 终态。长期保留规则见 `results/README.md`。
- `paringest` worker 每个 Step 写逐会话 `delivery tpt=... deliv=...`；首次足额前允许 TTFA ramp，但每个会话必须在 run 内至少足额一次，首次足额后的 short delivery、session death、gateway Step error 和 client-health failure 都判为 issue。`vanilla` 没有这条第一方 completeness 记录，只作参考 target。

## 模式

| mode | worker | 说明 |
| --- | --- | --- |
| `vanilla` | `third_party/metronome/worker/stream_server.py`（pin 内，原样） | 参照 baseline |
| `paringest` | `engines/baseline/worker/stream_server.py` | 并行 ingest 修复 + 插桩（出处与分道纪律见 `engines/baseline/AGENTS.md`） |

## 用法

```bash
python -m experiments.baseline --trace --label my-label   # paringest 是默认 mode
python -m experiments.baseline --mode vanilla
python -m experiments.baseline --trace --sessions 16 --duration 120 --seed-tokens 4000
```

参数来源两处、各司其职：`experiments/shared/`（model / platform / workload——本栈的固定事实，两臂共享）与本目录 `config.py`（逐 run 旋钮与引擎常量）。命令行只暴露逐 run 会变的旋钮（mode / trace / label / sessions / duration / seed-tokens / gpu）。

## 判读

健康判据看 `kv.log` 的 starvation 信号，不要只看客户端 miss=0%（silent failure：会话崩溃后 cadence 指标仍全部正常）。Perfetto 导出：`python -m infra.trace.perfetto baseline/<run-id>`。
