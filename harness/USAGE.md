# USAGE：工具链使用手册（任务导向）

*索引在 `README.md`（每个文件是什么）；本文回答"依次敲什么"。发现清单见 `../FINDINGS.md`，
口径与订正史见 `../PAPER-EXPERIMENTS.md` 执行记录。*

## 0. 前置

- venv：`~/vllm023-venv`（vLLM 0.23 + FIX 1 已打；新装 venv 必须重打 FIX 1，见执行记录）。
- 共机纪律：跑前 `nvidia-smi` 确认目标 GPU 空闲、`ss -tln | grep -E "50054|8907"` 确认端口空闲；
  **杀进程只用 driver 内建的 setsid 进程组定向 kill，绝不 `pkill -f`**（本机有并行会话，已发生过误杀）。
- 所有 driver 都是 fresh-per-point：每次调用起全新 worker，跑完自动清理进程组。

## 1. 跑一个实验

```bash
# 全仪器（推荐默认）：五件套日志 + 每请求 P/F/T + 逐步 PERITER + 调度器 trace
GPUS=3 N=8 DUR=600 MML=32768 bash harness/run_e1_schedtrace.sh

# 快车道重复/ctx 受控实验：加暖启动种子（单位≈token，会话开局即带 K token 上下文）
SEED_TOKENS=6000 GPUS=3 N=8 DUR=180 MML=32768 bash harness/run_e1_paringest.sh

# 复现"原样部署"的串行摄入形态（复合死锁）
GPUS=3 N=8 DUR=600 bash harness/run_e1_perreq.sh
```

产物落在 `results/paper/baseline/<TAG>_*`，TAG 自动为 `<系列>_n<N>_d<DUR>`。可调 env：
`SEED_TOKENS`（暖启动）、`INGEST_WORKERS`（摄入线程池，默认 8）、`MML`（600s 运行必须 ≥32768，
否则触发 MML 僵尸）、`WPORT/GPORT`（默认 50054/8907，避让并行会话的 50051/8904）。

## 2. 快速判读（跑完 30 秒内）

```bash
T=e1schtr_n8_d600; O=results/paper/baseline
tail -4 $O/${T}_client.txt                 # 客户端 verdict（注意：miss=0% 不代表健康，见 §4）
grep -E "pre=[1-9]" $O/${T}_kv.log | head  # 有无抢占、何时
tail -3 $O/${T}_kv.log                     # 终态：kv/run/wait/pre 判死法形态（FINDINGS A3）
grep -ciE "error|traceback" $O/${T}_worker.log   # 应为 0
```

三种死法速判：`run=0 wait=8 pre=1` 复合死锁；kv 锯齿+pre 递增 = 级联；`kv=1.000 run=0 wait=0 pre=0`
= 同步冻结（wait= 不含 skipped_waiting 队列）。

## 3. 可视化

```bash
python3 harness/viz/export_perfetto.py <TAG>     # → results/viz/<TAG>.trace.json.gz
```
下载该 .gz（不解压）→ 浏览器开 **ui.perfetto.dev** → Open trace file（本地 WASM 处理，不上传）。
轨道含义：`engine steps` 进程 = 每会话一条线程轨，格子=引擎步（橙 prefill+enc / 蓝 decode，点击看
tokens/batch/步时），STARVED 即饿死点；`gateway` = 真实拍边界；`scheduler` = 抢占标记 + KV 池/等待
队列/累计抢占 counter；`batch (concurrent sessions)` counter = 21ms 分辨率的真实并发。
论文静态图：`python3 harness/plots/plot_e1_*.py`（各图脚本头部注明数据源与窗口参数）。

## 4. 判读口径（不知道这些会被数据骗）

1. **客户端 miss=0% ≠ 健康**：worker 等待帽 1.6s < 2s 死线，崩溃状态读作"1601ms 准时空帧"。
   健康判据用 kv.log 的饥饿信号（该拍零新 token）而非 client verdict。
2. **步间隔 = 纯 GPU 步时**（全系列 async scheduling 默认开启）；**拍开场首步是上界**（流水线排空
   后含 CPU 串行段）；换 vLLM 版本/配置先验间隔分布再信数字。
3. **限流采样禁做快尺度推断**：statlog 是 1Hz 节流的，run= 直方图会混叠（教训见 FINDINGS F1）。
4. **跨时钟对齐**：perf/unix/statlog 三时钟偏移逐 run 不同；`harness/viz/bundle.py` 已内置 warmup
   锚定 + "min(prefill−tick)=+3ms" 不变量对齐——自己写分析时复用它，别手算偏移。
5. **每拍配额恒 33**（per-segment max_tokens 语义），tpt=25 只是取货节流。

## 5. 扩展工具链

- 新增每请求事件：worker 里 `_pev("X", sid, ...)` 一行（PERREQ 日志自动收）。
- 新增引擎内观测：仿 `sched_trace/sitecustomize.py` 模式（PYTHONPATH 注入 EngineCore 子进程，
  env 不设即完全休眠）；前端进程的 monkeypatch 到不了调度器，必须走这条路。
- 新增 Perfetto 轨道：`export_perfetto.py` 里加一段 slice/counter 映射（M2 的 KV 搬运事件预留位）。
- 数据层唯一真源是 `viz/bundle.py`——新格式先进 bundle，再进各前端。
