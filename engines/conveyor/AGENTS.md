# engines/conveyor

新双工推理引擎本体（项目负责人设计，增量实现）。由 `experiments/conveyor/` 按路径 spawn（argv+env 驱动，无 Python import）。机制结论在 `docs/findings.md` H 系列；全链路读图指南在 `docs/architecture.md`「一个会话的一个周期」。

## 机制（三个增量）

- **gateway 槽轮**（`gateway/`，Go，复制自 pin 的 gateway-go 后永久分道）：全局单节拍器换成 slot wheel——每 `period/slots`（默认 2000/8 = 250ms）在**绝对网格**上醒一次、只服务本槽会话；会话在 admission 时按到达顺序轮转指派槽位。任意到达模式都被均匀铺到周期上；每次发射打一行 `gateway_ticks.log`（网格晚醒量、每会话交付量）。
- **worker 取现货交付**（`worker/stream_server.py`，复制自 baseline worker 后永久分道）：Step 推入新 chunk 后立即返回该会话的库存 token（上一片的产出），不再等待——阻塞式 Step 会在 Servicer 锁后面把错开的槽重新串行化。交付恰好滞后生成一片，首片返回空。**指标口径随之重建**：`deadline_met` = 本 tick 交付 ≥ tpt（miss = 引擎未跟上）；每段生成配额 = tpt 精确值（任何松弛会累积成库存漂移，`inv_backlog` 监控）。
- **park 驻留管理**（`worker/engine_patch/sitecustomize.py`，vLLM 调度器轻量补丁，经 PYTHONPATH 注入 EngineCore）：vLLM 自带 connector 持续把满块增量镜像到主机内存池；**quota 模式（主路径）**在每个会话 decode 结束的瞬间引擎侧 auto-park——释放块引用并销毁驻留配额 K 之外的尾块；下一 chunk 到达时尾巴按 hash 从镜像异步回载。闲置底座固定在 K，稳态驻留降 66%（K=128；证据见 `results/conveyor/`）。证据写 `park.log`（park/S/L/R 四种行）。

engine_patch 另含预取链路（omni_state 状态权威 / omni_reload 指令面 / omni_transfer 匿名搬运；FINDINGS H7，净收益待 FE 膨胀根因解决）。补丁加载失败一律 exit 78 硬失败，防止「没生效的机制」伪装成证据；随后链式加载 `infra/trace` 的 scheduler-trace 采集器。
