# conveyor

新双工推理引擎（项目负责人设计，增量实现）。三个机制增量均已实现并有权威证据（结论在 `docs/findings.md` H 系列，run 索引在 `results/README.md`）：**错开相位**、**取现货交付**、**park 驻留管理**（镜像/park/回载全链路）。每次运行起一个全新 worker，证据落入 `results/conveyor/runs/<run-id>/` 的不可变目录。

## 机制（三个增量）

- **gateway 槽轮**（`gateway/`，复制自 pin 的 gateway-go 后永久分道）：全局单节拍器换成 slot wheel——每 `period/slots`（默认 2000/8 = 250ms）在**绝对网格**上醒一次、只服务本槽会话；会话在 admission 时按到达顺序轮转指派槽位。任意到达模式都被均匀铺到周期上；每次发射打一行 `gateway_ticks.log`（网格晚醒量、每会话交付量）。
- **worker 取现货交付**（`worker/stream_server.py`，复制自 baseline worker 后永久分道）：Step 推入新 chunk 后立即返回该会话的库存 token（上一片的产出），不再等待——阻塞式 Step 会在 Servicer 锁后面把错开的槽重新串行化。交付恰好滞后生成一片，首片返回空。**指标口径随之重建**：`deadline_met` = 本 tick 交付 ≥ tpt（miss = 引擎未跟上）；每段生成配额 = tpt 精确值（任何松弛会累积成库存漂移，`inv_backlog` 监控）。
- **park 驻留管理**（`worker/engine_patch/sitecustomize.py`，vLLM 调度器轻量补丁，经 PYTHONPATH 注入 EngineCore）：vLLM 自带 connector 持续把满块增量镜像到主机内存池；**quota 模式（主路径）**在每个会话 decode 结束的瞬间引擎侧 auto-park——释放块引用并销毁驻留配额 K 之外的尾块；下一 chunk 到达时尾巴按 hash 从镜像异步回载。闲置底座固定在 K，稳态池占用降 66%（K=128，run `20260811_193634_park-onstop`）。证据写 `park.log`（park/S/L/R 四种行）。

## 不变量

- 与 baseline **同模型、同 workload、同 vLLM 栈**（`config/` 三个常量文件与 baseline 一致）。注意 park run 强制同步调度——无 park 对照臂要用 `sync_scheduling` 旋钮钉住同一模式，否则对比同时改两个变量。
- `mode` 概念不存在：conveyor 只有一个 worker。`trace` 是观测开关。
- `runner.py` 只声明本实验的差异（命令、环境、issue 扫描），组装 `RunPlan` 交 `lab/workflow` 执行；配置只被 runner 读。
- **seed 必须配 park**（config 校验强制）：停止判定读的 `max_tokens` 冻结在构造值，只有 engine_patch 会逐 chunk 刷新——无补丁的 seed run 每段固定为 1 token 而指标全部正常。
- **warm start 是屏障式状态构造**（seed run 自动生效）：worker 预建 sid 1..N、跑完全部 seed prefill 后才写 ready（期间 auto-park 挂起、无任何机制交错、不做收尾 park——seed 刚结束时镜像结构上不可能完整）；第 1 周期全驻留，首次 auto-park 自然转入稳态。tick 从第一拍起就是稳态形状。

## 用法

```bash
python -m experiments.conveyor --trace --duration 120                      # 相位/交付，无 park
python -m experiments.conveyor --trace --seed-tokens 4096 --park-keep-blocks 128   # park 驻留管理（quota 主路径）
python -m experiments.conveyor --trace --park-tail-blocks 64              # park 固定尾块（实验路径，worker 定时 RPC）
```

槽数（`slots = 8`）、主机镜像池（`host_offload_gib`）、池帽（`kv_pool_gib`）、`park_delay_s`、`sync_scheduling` 是 `config/__init__.py` 的源码级旋钮。gateway 由 `environment/setup.sh` 编译到 `.build/conveyor-gateway`。

## 验收判读

读图指南（每站的证据与健康形态、九种失效模式指纹）在 `docs/architecture.md`「一个会话的一个周期」。速查：相位看 gateway_ticks 的间距与 late_ms；交付看 `deliv=` 满额与 gateway.log 零 `[starve]`（饥饿从会话首次足额交付起算，warm start 后无启动豁免需求）；park 看 park.log 的 `cpu_covered ≈ evicted`、Perfetto 无 `LARGE` prefill（seed 分块除外）、驻留锯齿底座平直；漂移看 worker.log 的 `inv_backlog` 恒 ~tpt。容量判读与 baseline 同纪律：kv.log 为准，不以客户端指标正常作为健康判据。
