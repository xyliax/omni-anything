# conveyor（测量装置）

conveyor 的测量臂，引擎本体在 `engines/conveyor/`。本目录只持有 runner、arm-private config、用法和 validation，不重复机制成熟度或结果数字；当前状态见 `docs/findings.md`，证据规则见 `results/README.md`。

## 不变量

- 与 baseline **同模型、同 workload、同 vLLM 栈**（公平性常量由 `experiments/shared/` 单份保证）。注意 park run 强制同步调度——无 park 对照臂要用 `sync_scheduling` 旋钮钉住同一模式，否则对比同时改两个变量。
- `mode` 概念不存在：conveyor 只有一个 worker。`trace` 是观测开关。
- `runner.py` 只声明本臂的差异（命令、环境、issue 扫描），组装 `RunPlan` 交 `infra/run/workflow` 执行；配置只被 runner 读。
- **seed 必须配 park**（config 校验强制）：停止判定读的 `max_tokens` 冻结在构造值，只有 engine_patch 会逐 chunk 刷新——无补丁的 seed run 每段固定为 1 token 而指标全部正常。
- **warm start 是屏障式状态构造**（seed run 自动生效）：正常路径上 worker 预建 sid 1..N、跑完全部 seed prefill 后才写 ready（期间 auto-park 挂起、无任何机制交错、不做收尾 park——seed 刚结束时镜像结构上不可能完整）；第 1 周期全驻留，首次 auto-park 自然转入稳态。`warm-start barrier timed out` 即使随后 ready 也会被共享 issue scanner 判为 failed run。

## 用法

```bash
python -m experiments.conveyor --trace --duration 120                      # 相位/交付，无 park
python -m experiments.conveyor --trace --seed-tokens 4096 --park-keep-blocks 128   # park 驻留管理（quota 主路径）
python -m experiments.conveyor --trace --seed-tokens 4096 --park-keep-blocks 128 --prefetch push  # prefetch diagnostic
python -m experiments.conveyor --trace --park-tail-blocks 64              # park 固定尾块（实验路径，worker 定时 RPC）
```

槽数、主机镜像池（`host_offload_gib`）、池帽（`kv_pool_gib`）、`park_delay_s`、`sync_scheduling` 是 `config.py` 的源码级旋钮；公平性常量在 `experiments/shared/`。gateway 由 `infra/env/setup.sh` 编译到 `.build/conveyor-gateway`。

## 验收判读

读图顺序在 `docs/system.md` 的 `One Session Cycle`。速查：相位看 gateway_ticks 的间距与 late_ms；交付要求每个 manifest session 至少一次 `deliv >= quota`，首次足额后 gateway.log 零 `[starve]`；park 看 park.log 的 `cpu_covered ≈ evicted`、Perfetto 无稳态 `LARGE` prefill、驻留底座有界；漂移看 worker.log 的 `inv_backlog` 长期无斜率。容量判读与 baseline 同纪律：kv.log 为准，不以客户端指标正常作为健康判据。
