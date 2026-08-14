# tracekit

独立 trace 套件。实验只产出原始日志，其余全部由本套件负责：解析、时钟对齐、bundle 组装、Perfetto 导出。实验目录里不允许再出现画图或 trace 代码；临时画图属于一次性行为，产物不入库。

## 契约

- **采集**（`collect.py` + `collectors/`）：scheduler trace 经 `sitecustomize` 注入 EngineCore 子进程，init 失败即 `os._exit(78)`——被要求的 trace 是主证据，宁可显式失败也不能产出引擎泳道为空的"看似正常"运行。GPU 采样周期由实验的 platform 常量决定；gpu.csv 每行自带 nvidia-smi 墙钟时间戳，与 scheduler.log 的 epoch 时钟同源，解析端直接对齐、无合成时间基。
- **解析**（`parse.py`）：KV 日志的 `pre=` 组可选；scheduler 行首 `!` 是标记行；warmup 哨兵会话（10^9）不进任何统计但其 push 时间是 StatLogger 时钟与 worker 时钟的桥；`gateway_ticks.log`（conveyor gateway 每发射一行）与 `park.log`（engine_patch，park/S/L/R 四种行：park 事实 / 镜像发出 / 回载准入 / 回载完成）自带 epoch 时钟、无需时钟配对；L/R 由 parse_park 配对成回载窗口。
- **对齐**（`bundle.py`）：worker 在 per_request.log 首行写双时钟配对行（`C <perf> <epoch>`），perf 家族到 scheduler epoch 时钟的映射**精确**（`worker_clock_fix`）。无配对行的历史 run 回退 `min_prefill_after_push` 启发式锚定——已知偏差：它把 ~240ms 的 ingest 延迟地板折进时钟偏移，显示的 push→prefill 间隔是相对值。bundle 里出现哪些键只取决于 run 目录里实际存在哪些 artifact。
- **导出**（`perfetto.py`）：scheduler.log → 每会话调度步泳道（进程名 "engine schedule steps"，slice 标签带 `sched` 前缀，>400 token 的 prefill 标 `LARGE` = 疑似重算）+ 会话泳道上的 ingest 三段（queue/FE/handoff+admit）、PARK instant、KV mirror instant、KV reload slice + gateway 发射泳道（gateway_ticks 实测；无此文件回退 P 行聚类并如实标注 inferred）+ 每会话驻留锯齿 counter（pid 4）+ batch/KV/GPU counter + tick 标记。**逐泳道读图指南与健康形态在 `docs/architecture.md`「一个会话的一个周期」**。**读图注意**：slice 宽 = 相邻两次 schedule() 调用的间距（调度时间轴，非 GPU 执行时间轴）；异步调度下仅稳态等于 GPU step 时长，prefill 附近的 2-3ms 窄片是流水线回填，与邻片合看才是真实时长（FINDINGS C3/F3）。证据中不存在执行时间戳——需要执行轴时须加 CUDA event 级采集器。派生物写入 run 目录 `derived/`，只写一次、失败即清理、gzip 字节可复现，metadata 记录全部源文件的 hash。

## 用法

```bash
python -m tracekit.perfetto <run-dir | experiment/run-id | unique-run-id>
python -m tracekit.perfetto --all
```
