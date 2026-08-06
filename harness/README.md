# harness/ — E 系列真机实验的自研组件

**怎么跑实验见 `USAGE.md`**；本文只做文件索引。

`../third_party/metronome/` 是固定版本的第三方代码，只读；所有改动以副本或补丁形式放在本目录。
运行产物写入 `../results/paper/baseline/`（证据，不清理）；图写入 `../results/figures/`；
交互可视化产物写入 `../results/viz/`。

## Workers（Metronome worker 的 instrumented 副本）

| 文件 | 相对上游的行为差异 | 用途 |
|---|---|---|
| `stream_server_perreq.py` | **无行为改动**（只加日志：P/F/T 每请求事件、`pre=` preemption 计数）| vanilla baseline（串行 ingest）|
| `stream_server_paringest.py` | ① `process_inputs` 改用 8 线程池（缓解 ingest 瓶颈，唯一语义差异）② 关闭多模态 processor 缓存 ③ 支持 `--seed-tokens` 预热上下文 | E2 公平对比臂 / 快速重复实验 |

## Drivers（一条命令 = 一次完整运行；每个数据点起新进程，并用 setsid 进程组统一清理）

| 脚本 | worker | 额外观测 |
|---|---|---|
| `run_vanilla_baseline.sh` | Metronome 原版 | 五件套日志（E1 初版数据的来源）|
| `run_e1_perreq.sh` | perreq | + 每请求事件 |
| `run_e1_paringest.sh` | paringest | 同上（`SEED_TOKENS=` 启用 seed-token 预热）|
| `run_e1_periter.sh` | paringest | + `PERITER_LOG` 按引擎步聚合 |
| `run_e1_schedtrace.sh` | paringest | + scheduler 逐步 trace（全套观测，时间线图数据源）|

## 观测与工具

- `sched_trace/sitecustomize.py`：经 `PYTHONPATH` 注入 EngineCore 子进程，记录 scheduler 每一步（仅设置 `SCHED_TRACE=` 时启用）。
- `viz/bundle.py`：数据层——解析五件套日志并做跨时钟对齐，产出 bundle。
- `viz/export_perfetto.py` → `results/viz/<tag>.trace.json.gz`（已 gitignore，可重新生成）：用 ui.perfetto.dev 打开。
  自研 HTML 查看器已退役（需要时见 git 历史中的 `build_viewer.py` / `timeline_template.html`）。
- `plots/`：论文静态图生成脚本（每张已提交的图对应一个脚本——工件纪律，勿删）。

时钟对齐约定：三类日志（perf / unix / statlog）在每次运行里用 warmup 锚点重算偏移；
时间线类对齐用物理不变量 `min(prefill_start − preceding_tick) = +3ms`。
