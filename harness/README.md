# harness/ — E 系列真栈实验的全部自研组件

**使用手册（依次敲什么）见 `USAGE.md`**；本文是文件索引。

克隆纪律：`../metronome/` 只读；一切改动以副本/补丁形式放在这里。运行产物入
`../results/paper/baseline/`（证据，永不清理）；图入 `../results/figures/`；交互产物入 `../results/viz/`。

## Workers（metronome worker 的插桩副本）

| 文件 | 相对上游的行为差异 | 用途 |
|---|---|---|
| `stream_server_perreq.py` | **零**（纯加日志：P/F/T 每请求事件、`pre=` 抢占计数）| "原样部署"基线（串行摄入）|
| `stream_server_paringest.py` | ① `process_inputs` → 8 线程池（摄入墙修复，语义差异一处）② mm processor cache 关闭 ③ `--seed-tokens` 暖启动 | E2 公平对比臂 / 快车道重复实验 |

## Drivers（一次运行 = 一条命令，fresh-per-point + setsid 进程组纪律）

| 脚本 | worker | 额外仪器 |
|---|---|---|
| `run_vanilla_baseline.sh` | metronome 原版 | 五件套日志（E1 初版数据的来源）|
| `run_e1_perreq.sh` | perreq | + perreq 事件 |
| `run_e1_paringest.sh` | paringest | 同上（`SEED_TOKENS=` 启用暖启动）|
| `run_e1_periter.sh` | paringest | + `PERITER_LOG` 逐引擎步聚合 |
| `run_e1_schedtrace.sh` | paringest | + 调度器逐步 trace（全仪器，泳道图数据源）|

## 仪器与工具

- `sched_trace/sitecustomize.py`：经 PYTHONPATH 注入 EngineCore 子进程的调度器逐步记录（仅 `SCHED_TRACE=` 设置时激活）。
- `viz/bundle.py`：数据层——解析五件套日志并做跨时钟对齐，产出 bundle。
- `viz/export_perfetto.py` → `results/viz/<tag>.trace.json.gz`（已 gitignore，可再生）：ui.perfetto.dev 打开。
  自研 HTML 查看器已退役（需要时见 git 历史 build_viewer.py/timeline_template.html）。
- `plots/`：论文静态图的生成脚本（每张已提交的图对应一个脚本——工件纪律，勿删）。

时钟对齐约定：三类日志（perf/unix/statlog）逐 run 用 warmup 锚点重算偏移；泳道类对齐用物理不变量
`min(prefill_start − preceding_tick) = +3ms`。
