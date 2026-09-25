# infra/trace

独立 trace 套件，负责 raw-log 解析、时钟对齐、bundle 和 Perfetto。实验目录不得复制 trace 或画图实现。

## Contracts

- `collect.py` 与 `collectors/` 注入 EngineCore；指定的 collector 初始化失败时 exit 78。
- `parse.py` 把 `gateway_ticks.log` 和 `kv_events.log` 当作 epoch-clock artifacts 解析。`kv_events.log` 新 schema 为 `E` partial eviction、`B` host backing、`L` load issue、`R` load completion；`parse_kv_events` 按 `(request, trigger)` 配对 L/R。
- `bundle.py` 用 `C <perf> <epoch>` 精确对齐 worker perf clock；缺少配对行的历史 run 才回退到启发式对齐，并标记警告。
- `perfetto.py` 只呈现已有证据：engine scheduling lanes、input pipeline、KV eviction/backing/reload/prefetch、gateway releases 和 residency counters。相邻 `schedule()` 调用间距不是精确 GPU kernel duration。
- KV load slice 标为 `KV reload window` / `KV prefetch window`，表示 scheduler 观察的 L–R 窗口。demand R 对应请求恢复调度的处理入口，prefetch R 对应完成通知处理；均不是 DMA 结束时间戳。`logical_kv_bytes` 仅在 manifest 提供 KV geometry 时按 token 数换算，不代表实际总线流量，不据此计算 DMA 带宽。未配对 L 标记 completion unobserved。
- `collectors/gpu_activity.py` 使用 PyTorch profiler/CUPTI 捕获原始设备活动，观测所有线程以覆盖独立 copy service。原始 `gpu_activity.json` 不改写；`gpu_activity.py` 解析设备 timestamp/duration、bytes、device/context/stream 和显式 CUDA/Kineto 身份关联。缺失关联须标 unattributed，缺失 epoch 基准拒绝合并，CPU-only capture 验收失败。
- `transfer_events.jsonl` 保存 CPU 排队/提交/完成观察/发布与 CUDA event interval。后者不是纯 DMA 时间。Perfetto 的 GPU execution 轨道只用设备活动、保留亚微秒 duration；CPU 控制单独呈现，manager 模式的 prefetch R 可由独立回调产生。
- 提交事件还保存物理描述符数量、连续 run 数、首 batch 返回、enqueue wall/thread CPU 时间和总提交 thread CPU 时间；不能将 first batch API 返回当作 GPU first byte 的精确时刻。短 driver 调用通过 PyDLL/PYFUNCTYPE 保持 GIL，不增加设备同步。
- `collectors/service_events.py` 在固定预算流式段的真实停止处理入口记录模型完成，并与 gateway/worker/ingest 身份关联。`service.py` 从固定输入、绝对网格和完成事件验收稳定并发，未完成输入保留在分母；RPC tick 不参与完成判断。具体 SLO 与观察期限由每次 manifest 显式提供，协议 owner 是 `docs/experiments.md#stable-concurrency-runner`。
- GPU 轨道使用英文名称，根据已观测的 compute/copy 身份生成，不硬编码 stream 数字。只有显式关联 Session Manager transfer 的 copy 才标 `KV restore H2D` / `KV backup D2H`；未关联传输标 `Copy (unattributed)`。原始 device/context/stream 标识保存在事件属性，同角色的不同 stream 分轨。会话事件显示 `decode` / `prefill` / `prefill+encoder`，不加 sched 前缀；按 `timing_scope` 属性识别 CPU 调度观察轨道，名称不能改变计时语义。
- capture 要么关闭，要么覆盖完整业务运行；runner 在客户端开始前完成启动，客户端结束后才停止并导出，禁止业务中途按秒截断；同名 GPU annotation 只用于关联，不替代 memcpy/kernel 的实际区间。GPU profiler 会扰动运行，不能未经标定直接用于正式性能比较。
- 当前 residency 是 schedule hook 中受最小间隔限制的快照；空闲或长迭代期间无独立采样。曲线时间是观察时刻，同一快照的共同下降不证明同时逐出。计数为 request block 列表长度或释放引用后的连续 cache 前缀，不能据此统计任意不连续驻留和在途分配；逐出时刻以原始 E 事件为准。
- `profile.py` / `profile_view.html` 将已校验的 Perfetto 导出呈现为本地自包含 `derived/profile.html`，支持缩放、session 筛选和 transfer 详情。保留原始区间与字节；GPU 观测范围外用斜线标记，不补画 GPU 执行。以首个正常周期输入为零点，预热在负时间；CPU 调度和设备活动分轨。`profile.metadata.json` 记录输入、生成器、模板和输出 hash，禁止覆盖既有导出。
- cohort profile 的总耗时取 `client.json` 的实际 makespan，不能用 runner watchdog 配置时长代替；源 client hash 单独记录。首末设备活动的间隔与 capture 生命周期、cohort 总耗时是不同概念。
- profile 可切换至 Perfetto 时钟，并定位业务阶段连续 CPU 调度记录的最长间隔；间隔不等于 GPU 空闲或故障判定。重新呈现既有证据使用 `--variant <name>`，在 `derived/<name>/` 写新导出，不覆盖旧文件；新导出验证后，按 results 保留规则清理已被替代的展示版本。Perfetto 与 profile 使用相同 variant。
- 新 parser 只解释当前 schema。不可变旧 run 需要重解析时使用产生该 evidence 的旧 commit，不在新代码中保留废弃术语 adapter。

## Usage

```bash
python -m infra.trace.perfetto <run-dir | experiment/run-id | unique-run-id>
python -m infra.trace.perfetto --all
python -m infra.trace.profile <run-dir | unique-run-id>
python -m infra.trace.perfetto <run-dir> --variant named-streams
python -m infra.trace.profile <run-dir> --variant named-streams
```

`python -m infra.trace.groups <run>` 从 admission、eviction 与 copy-control 原始事件生成只写一次的 `derived/group_windows.json`；分别报告组成员、预算超量、发布时间超窗、planner review 与无法关联的 H2D。排队到发布是 CPU 控制窗口，不称作 DMA 时间。
