# harness — E 系列真机实验组件

`../third_party/metronome/` 是固定版本的第三方代码，只读；所有改动以副本或补丁形式放在本目录。
运行产物写入 `../results/paper/baseline/`（证据，不清理）；图写入 `../results/figures/`；交互可视化产物写入 `../results/viz/`。

## 前置

- 虚拟环境：`~/vllm023-venv`（vLLM 0.23，且已打 FIX 1；新装环境必须重打 FIX 1，见 `../docs/experiment-log.md`）。
- 共用机器纪律：跑前用 `nvidia-smi` 确认目标 GPU 空闲，用 `ss -tln | grep -E "50054|8907"` 确认端口空闲；
  **杀进程只用 driver 内建的 setsid 进程组定向 kill，绝不 `pkill -f`**（本机有并行会话，已发生过误杀）。
- 所有 driver 都是「每个数据点起新进程」：每次调用启动全新 worker，跑完自动清理整个进程组。

## 跑一个实验

```bash
# 全套观测（推荐默认）：五件套日志 + 每请求 P/F/T + 逐步 PERITER + scheduler trace
GPUS=3 N=8 DUR=600 MML=32768 bash harness/run_e1_schedtrace.sh

# 快速重复 / 受控上下文实验：加 seed-token 预热（单位≈token，会话开局即带 K token 上下文）
SEED_TOKENS=6000 GPUS=3 N=8 DUR=180 MML=32768 bash harness/run_e1_paringest.sh

# 复现 vanilla baseline 的串行 ingest（HOL blocking 把全体锁死）
GPUS=3 N=8 DUR=600 bash harness/run_e1_perreq.sh
```

产物落在 `results/paper/baseline/<TAG>_*`，TAG 自动为 `<系列>_n<N>_d<DUR>`。可调环境变量：
`SEED_TOKENS`（seed-token 预热）、`INGEST_WORKERS`（ingest 线程池，默认 8）、`MML`（max_model_len；
600s 运行必须 ≥32768，否则会话会 max_model_len stall）、`WPORT`/`GPORT`（默认 50054/8907，
避让并行会话的 50051/8904）。

## 快速判读（跑完 30 秒内）

```bash
T=e1schtr_n8_d600; O=results/paper/baseline
tail -4 $O/${T}_client.txt                 # 客户端结论（注意：miss=0% 不代表健康，见判读陷阱）
grep -E "pre=[1-9]" $O/${T}_kv.log | head  # 有无 preemption、何时
tail -3 $O/${T}_kv.log                     # 终态：kv/run/wait/pre 判失效形态（FINDINGS A3）
grep -ciE "error|traceback" $O/${T}_worker.log   # 应为 0
```

三种失效形态速判（FINDINGS A3）：

- `run=0 wait=8 pre=1`：running 空、waiting=8、发生过 preemption → HOL blocking 把全体锁死（串行 ingest × KV 耗尽）
- kv 锯齿 + pre 递增：preemption cascade（一路路被 preempt，幸存者工作集越来越大）
- `kv=1.000 run=0 wait=0 pre=0`：admission deadlock under synchronized fill（刚好在 tick 间隙池满，无人可 preempt，全员卡住；
  注意 wait= 不含 skipped_waiting 队列）

## 可视化

```bash
python3 harness/viz/export_perfetto.py <TAG>     # → results/viz/<TAG>.trace.json.gz
```

下载该 `.gz`（不解压）→ 浏览器打开 **ui.perfetto.dev** → Open trace file（本地 WASM 处理，不上传）。

轨道含义：

- `engine steps`：每会话一条线程轨，格子 = 引擎步（橙 prefill+enc / 蓝 decode，点击看 tokens / batch / 步时）；STARVED 即该会话 starvation 的时刻
- `gateway`：真实的 tick 边界（固定时长的一轮，如 2 秒）
- `scheduler`：preemption 标记 + KV 池 / waiting 队列 / 累计 preemption 计数
- `batch (concurrent sessions)`：21ms 分辨率的真实并发计数

论文静态图：`python3 harness/plots/plot_e1_*.py`（各图脚本头部注明数据源与窗口参数）。

## 判读陷阱（不知道这些会被数据骗）

1. **客户端 miss=0% ≠ 健康（silent failure）**：worker 的等待上限 1.6s 小于 2s deadline，崩溃状态会被读成「1601ms 表面准时的空帧」。
   健康判据用 `kv.log` 的 starvation 信号（该 tick 零新 token），而不是客户端结论。
2. **步间隔 = 纯 GPU 步时**（全系列默认开启 async scheduling）；**一拍开场的首步是上界**（流水线排空后含 CPU 串行段）；
   换 vLLM 版本或配置时，先验间隔分布再信数字。
3. **限流采样禁做快尺度推断**：statlog 是 1Hz 节流的，run= 直方图会混叠（教训见 FINDINGS F1）。
4. **跨时钟对齐**：perf / unix / statlog 三时钟偏移逐次运行不同；`harness/viz/bundle.py` 已内置 warmup
   锚定与 `min(prefill−tick)=+3ms` 不变量对齐——自己写分析时复用它，别手算偏移。
5. **每拍配额恒为 33**（按 segment 的 max_tokens 语义），tpt=25 只是取货节流。

## 组件索引

### Workers（Metronome worker 的 instrumented 副本）

| 文件 | 相对上游的行为差异 | 用途 |
|---|---|---|
| `stream_server_perreq.py` | **无行为改动**（只加日志：P/F/T 每请求事件、`pre=` preemption 计数）| vanilla baseline（串行 ingest）|
| `stream_server_paringest.py` | ① `process_inputs` 改用 8 线程池（缓解 ingest 瓶颈，唯一语义差异）② 关闭多模态 processor 缓存 ③ 支持 `--seed-tokens` 预热上下文 | E2 公平对比臂 / 快速重复实验 |

### Drivers（一条命令 = 一次完整运行）

| 脚本 | worker | 额外观测 |
|---|---|---|
| `run_vanilla_baseline.sh` | Metronome 原版 | 五件套日志（E1 初版数据的来源）|
| `run_e1_perreq.sh` | perreq | + 每请求事件 |
| `run_e1_paringest.sh` | paringest | 同上（`SEED_TOKENS=` 启用 seed-token 预热）|
| `run_e1_periter.sh` | paringest | + `PERITER_LOG` 按引擎步聚合 |
| `run_e1_schedtrace.sh` | paringest | + scheduler 逐步 trace（全套观测，时间线图数据源）|

### 观测与工具

- `sched_trace/sitecustomize.py`：经 `PYTHONPATH` 注入 EngineCore 子进程，记录 scheduler 每一步（仅设置 `SCHED_TRACE=` 时启用）。
- `viz/bundle.py`：数据层——解析五件套日志并做跨时钟对齐，产出 bundle；数据层唯一真源，新格式先进 bundle，再进各前端。
- `viz/export_perfetto.py`：由 bundle 导出 `results/viz/<tag>.trace.json.gz`（已 gitignore，可重新生成）。
- `plots/`：论文静态图生成脚本（每张已提交的图对应一个脚本——工件纪律，勿删）。
- `wait_quiet.sh`：共享 GPU 空闲检测，测量前与 `third_party/metronome/bench/gpu_probe.py` 的 `wait_for_window` 连用。

## 扩展工具链

- 新增每请求事件：在 worker 里加一行 `_pev("X", sid, ...)`（PERREQ 日志自动收录）。
- 新增引擎内观测：仿 `sched_trace/sitecustomize.py` 模式（经 `PYTHONPATH` 注入 EngineCore 子进程；
  不设 env 即完全休眠）。前端进程的 monkeypatch 到不了 scheduler，必须走这条路。
- 新增 Perfetto 轨道：在 `viz/export_perfetto.py` 里加一段 slice / counter 映射（M2 的 KV 搬运事件预留位）。
