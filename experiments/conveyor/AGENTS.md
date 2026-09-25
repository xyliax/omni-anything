# conveyor（测量入口）

本目录只持有 Pilarius runner、system-specific config 和 validation。机制状态见 `docs/findings.md`，协议见 `docs/experiments.md`。

## Invariants

- 公平性按 `docs/experiments.md#executed-decode-difference` 核验实际工作量与路径，不能由共用 offered-load 常量推定。
- partial KV eviction 强制 synchronous scheduling；control configuration 必须固定为相同 mode。
- initial-context preloading 当前依赖 EngineCore patch 中的 streaming `max_tokens` fix；barrier 超时使 run 失败。
- preloading barrier 期间暂停 automatic eviction；结束时只解除暂停，第一次正常 idle transition 再建立 retained-prefix 状态。
- KV eviction 开启时必须有 `kv_events.log` 的 `E` 行；prefetch 开启时必须有 `L ... trigger=prefetch`。
- Session Manager 模式要求 retained-prefix，拒绝 fixed-tail/legacy push prefetch；必须有完成的 H2D 和无错误的 `transfer_events.jsonl`。
- GPU capture 必须含 CUDA kernels；managed capture 还须有已关联的 H2D，设备 copy 字节与提交一致。capture 在业务客户端启动前开启、客户端退出后停止并导出；删除按秒定时截断，性能主实验默认关闭；时钟与活动语义见 `docs/experiments.md#profiling`。

## Usage

```bash
python -m experiments.conveyor --trace --duration 120
python -m experiments.conveyor --trace --initial-context-tokens 4096 --retained-prefix-blocks 128
python -m experiments.conveyor --trace --initial-context-tokens 4096 --retained-prefix-blocks 128 --prefetch push
python -m experiments.conveyor --trace --evict-tail-blocks 64
python -m experiments.conveyor --session-manager --retained-prefix-blocks 128 --initial-context-tokens 4096 --gpu-trace --sessions 2 --duration 30
```

速查：release offsets 看 `gateway_ticks.log` 的间距与 `late_ms`；partial eviction 看 `E` 行、`host_backed` 和 residency；prefetch 看 `L/R trigger=prefetch`；输出缓冲看 `output_backlog` 是否持续增长。实际交付少于 cap 是诊断事实，不自动构成 correctness failure。

## Legacy Finite Cohort

`--admission-profile /path/profile.json --cohort-manifest /path/cohort.json` 与 `--session-manager --retained-prefix-blocks 1` 一起使用；JSON 语义与未完成的评估内容见 `docs/experiments.md#finite-cohort-runner`。`--duration` 是整个 cohort 的 watchdog；offered session 数来自 manifest，准入并发上限属于 profile，两者不同。当前禁止 initial-context 全员 barrier。客户端在 admission 后才播放，结束后等待最后输出及清理确认，不以音频发送完毕作为成功。

`cohort_client.py` 是实际 WebSocket 客户端，使用真实 worker；无 audio_path 时显式记录 synthetic PCM。成本 profile 需按模型、资源、周期与历史范围标定，测试参数不能直接当论文配置。Go 源码修改后先在 gateway 目录重建 `.build/conveyor-gateway` 再运行。

`--resident-control --resident-limit N --cohort-manifest ...` 使用同一协议运行全驻留参照，结果写入 `results/baseline/`，manifest 标识 `matched_resident_control`，不传 admission profile 或 eviction 参数。它不改变旧 `experiments.baseline` 的 Metronome 入口。

`--capacity-slo slo.json` 启用全部目标会话准入 barrier 和 `infra.trace.service` 验收，禁止 GPU profiler。自动配对扫描：

```bash
python -m experiments.conveyor.capacity --profile costs.json --slo slo.json --concurrency 4,8,12 --seeds 11,22,33 --slots 4 --gpu 3
```

配置字段、指标与容量边界含义只由 `docs/experiments.md#stable-concurrency-runner` 持有。汇总保留各点来源 hash；测量 invalid 不成为容量失败上界。复制实现控制用 `--copy-submission native|optimized`，禁止把 native 对照当当前优化实现。

多模型入口：`--model-preset qwen25_omni|minicpm_o45`；两者当前均为固定预算 audio-input/text-output。`--max-model-len`、`--max-num-seqs`、`--gpu-memory-utilization`、`--max-num-batched-tokens`、`--enforce-eager` 显式记录运行配置，容量扫描支持相同选择。新 preset 的 checkpoint/revision/geometry 单份在 `experiments/shared/model.py`；部署前须缓存完整权重。实际 GPU 型号由 provenance probe 读取，不复用旧卡名称。

显式 KV pool 若连所选模型的一条最大长度请求都容纳不了，config 在启动前拒绝；该检查只是按 BF16 geometry 算出的下界，不能替代 backend 对齐、权重和 workspace 的显存检查。

每周期输出预算由 `experiments/shared/workload.py` 按 model preset 选择；worker、gateway 和 manifest 必须使用同一选值，容量配对的两种系统也必须一致。数值与选择依据见 `docs/experiments.md#candidate-model-integration`，禁止在 runner 中重新固定为默认模型预算。

## Exogenous Schedule

`python -m experiments.conveyor.schedule --seed 11 --arrival-rate 0.1 --session-duration 60 --arrival-window 120 --period 2 --audio /data/conversation.wav --output /tmp/arrival-schedule.json` 生成独立于系统的动态输入时间表，拒绝覆盖文件。WAV 必须是 mono PCM16/16 kHz 且足够长；素材 hash、sample offset、seed 和时间参数均保存。

使用 `--open-loop --cohort-manifest <schedule>` 选择 `replay_client.py`，支持 `--phase-policy natural|assigned`。旧 `cohort_client.py` 的准入后播放不接受该格式。原定 source clock、rejection 和 completion 在 `client.json` 保存；`replay_metrics.json` 由共享 trace 层生成，超期与未完成是结果而非仪器错误。协议由 `docs/experiments.md#open-loop-runner` 持有。

`python -m experiments.conveyor.check --gpu 0 --model-preset all` 是新机器功能检查入口，先核验 runtime、模型文件与物理 KV 往返，再执行两个模型的多成员组；成功调试目录自动清理，摘要在 `.build/checks/`。它不标定 admission profile，也不声称已实现本轮最大上下文规划及开放到达协议。

成本 profile 的 `planning_mode=maximum_context` 使用真实后端上限，要求 assigned/pre_tick；`static_limit` 用于独立校准的回载基线和固定会话集消融，不借用主动 phase 预测的容量信用。`--restore-policy on_demand|after_submit|pre_tick` 选择恢复触发时机。禁止将未标定功能检查的 profile 用作容量证据。

录音素材：`python -m experiments.conveyor.material --archive /data/dev-clean.tar.gz --output /data/speech-streams` 校验官方 archive 后构建不循环的同 speaker 流，保存逐 clip hash 与转换 provenance；输出目录必须不存在。固定队列时间表由 `schedule.generate_fixed_schedule` 生成。素材选择和连接录音的解释由实验 owner 持有。

`python -m experiments.conveyor.evaluate prepare --spec <spec.json> --output <new-dir>` 冻结矩阵，随后 `run <new-dir>/plan.json` 顺序执行并保留检查点；formal 要求同一 clean commit。分析与成本提取只调用共享 `infra.trace.evaluation` 和 `infra.trace.calibration`。`--verify-copies` 逐层检查实际复制内容，会同步 GPU，只供诊断，不能用于 formal 性能。

开放回放先有界等待 gateway `/clock` 就绪，再固定源时钟；listener 启动竞态不能使有效工作丢失，服务开始后不重设时钟。
