# engines/conveyor

Pilarius 的引擎实现（目录标识 `conveyor`），由 `experiments/conveyor/` 按路径 spawn。本文件只用于代码定位，不证明新设计已实现；修改前核验目标路径。论文术语和机制语义见 `docs/problem.md#terminology` 与 `docs/system.md`。

## Local Workflow

- `gateway/main.go` / `gateway/session_manager.go`：绝对 release grid；旧 cohort 使用 FIFO，开放回放由 `replay.go` 保留源时钟、自然 phase 或稳定 assigned slot 并拒绝一次，结束时等待 worker 清理确认。`--output-token-cap` 是 gateway 最多消费的 token 数，不是最低交付要求。继承的 `deadline_met` wire field 只报告当前 service RPC 是否在 period 内返回。
- `worker/stream_server.py`：把 input chunk 入队后快照 undelivered-output buffer，不等待本次计算；`output_backlog` 记录缓冲深度。当前路径只输出 Thinker text。
- `worker/engine_patch/omni_evict.py`：incremental host backing、idle-session partial KV eviction、on-demand reload instrumentation 和 streaming bug fixes。新事件写 `kv_events.log`：`E` eviction、`B` host backing、`L/R` load window。
- `omni_state.py`：只保存 session activity、prefetch control 和时间戳；GPU/host block coverage 每次查询 pools，不维护伪 lifecycle。
- `omni_prefetch.py` / `omni_prefetch_transport.py`：KV prefetch command、capacity deferral 和 transport adapter。synthetic ID 与 hash registration 是 implementation choices。
- `session_manager.py`：独立 timer/event loop、每会话计划与活动状态；不依赖模型 step 推进。`SessionPlan` 接收保留前缀、逻辑块区间与逐出预算。
- `residency_planner.py`：显式成本 profile 下的保守候选检查器；固定既有 phase 和预算，新路径按实际最大上下文校验计算、备份、整组恢复窗口、完整目标 GPU 峰值与 host 容量；旧有限前瞻模式仅供历史诊断。它只规划，不分配物理块。
- `manager_adapter.py` 中的 `VllmKVMemoryManager`：vLLM block pool 引用、confirmed host coverage、独立完成回调和 scheduler 锁边界。单进程执行器、同步 scheduler、单 KV-cache layout group、无 speculative decoding/worker KV zeroing；此处 KV group 不是 session group，不限制多个 slot 及每组多会话。锁不得覆盖模型执行。managed 模式禁用旧自动逐出和旧 prefetch。
- `copy_service.py`：独立传输线程与 H2D/D2H CUDA streams；提交与完成轮询不经 model output。取消/输入超越不能释放在途源或目的引用；失败保留不确定引用并使引擎报错。
- `copy_descriptors.py`：源／目的双连续映射合并、有界 batch 提交、保持 GIL 的非阻塞 CUDA driver event/submit 调用。`copy_submission=native` 仅为旧路径诊断对照，默认 optimized；独立 thread CPU time 与 wall time 分开记录。
- `resident_adapter.py`：全驻留 cohort control 的生命周期和 readiness；不创建 KV connector 或 host backing。共享 worker、gateway 与固定输入协议，身份在 manifest 中明确区分。

gateway 将 planned next tick/period 放进 gRPC metadata；worker 经 `session_plan` utility 安装计划后交付输入。设备观测实现只在 `infra/trace/collectors/gpu_activity.py`，此处只标注 compute/copy 身份。修改 manager 需运行 `tests/test_session_manager.py`；物理多层 KV 往返使用 `tests/test_session_manager_gpu.py` 的显式 GPU 命令。

partial eviction 当前强制 synchronous scheduling。initial-context preloading 期间 `OMNI_HOLD_KV_EVICTION` 暂停 automatic eviction；`initial_context_finalize` 只解除暂停，不在 barrier 处立即逐出。patch 加载失败 exit 78。

## Admission Lifecycle

四组件映射：ResidencyPlanner 产生准入计划；gateway/EngineCore 的两个 Session Manager 分别持有连接与周期／KV 执行进度；VllmKVMemoryManager 统一协调后端 block pool；CopyService 执行传输。职责是逻辑边界，不强制合并进程。

`Step` control metadata `x-pilarius-control=admit|close` 承载生命周期，普通 tick 携带绝对 next-tick 与 ending session IDs。admit 返回 `x-pilarius-admission` JSON；不修改 third-party protobuf。关闭 RPC 不持有普通 Step 的锁等待 DMA。EngineCore utilities 为 `session_admit`、`session_plan`、`session_ready`、`session_drained`、`session_release`；取消先阻止新输入，reservation 只在 backend request 和复制引用都清理后释放。

新输入需等所需历史就绪；pending-work 标识保护就绪引用直到 connector 分配执行引用，不以提交 copy 作为 ready。输出 drain 目前使用固定 generation-cap harness 的累计 token 数和 EngineCore idle 双重确认，变更为自然可变长生成时必须改为确切的完成事件关联。

验证：`tests/test_residency_planner.py`、`tests/test_session_manager.py`、`tests/test_admission_worker.py`、`tests/test_cohort_client.py`，以及在 gateway 目录用锁定 Go 执行 `go test -race ./...`。CPU worker/client 协议测试需 grpcio、protobuf、numpy、websockets（锁定 worker 环境已提供）。

cohort 模式的 `service_events.go` 按采样数切片，记录原定 release/deadline 并通过 metadata 传递输入身份；与 `infra/trace/collectors/service_events.py` 对接。vLLM utility 参数反序列化检查函数签名，utility 不可用可变参数代替固定参数列表。

开放回放的 `InputGate` 区分前处理后的 on-demand readiness、提交后与前处理重叠的 readiness、定时器提前恢复。每会话锁保持到后端 enqueue，避免多个未入引擎的输入覆盖下一 tick；输入与生成累计超过后端上限时拒绝提交，不裁短历史。`service_events` 记录前处理、enqueue、固定预算完成、实际上下文与输出 token hash。

`OMNI_VERIFY_COPIES=1` 在 copy service 的 device-complete 与 publish 之间调用共享物理检查器；逐字节不一致使复制服务失败并保留引用。该选项会同步 GPU，只供正确性诊断。已逐出历史的恢复时刻由 `missing_tick` 保存，后续迟到输入安装下一计划不能移动它。

managed 路径保存完整逻辑块表和未满块尾部；`prepare_input` 核验 hash 与计算进度后，将 pins 直接移交 `kv_cache_manager.coordinator.single_type_managers[0]` 的请求块表。禁止对该请求重置 `num_computed_tokens` 再从 prefix cache 重入；旧非 managed 诊断路径仍保留原行为。
