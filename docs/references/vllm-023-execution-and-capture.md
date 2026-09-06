# vLLM 0.23 执行与 CUDA Graph 捕获行为

外部依赖行为整理。Updated: 2026-09-01

本文不是项目事实源，不定义本项目的 workload、机制或术语。依据是 `infra/env/profiles/cuda13_vllm023` 锁定的 vllm==0.23.0 wheel 源码，并对照 retained run 的引擎启动日志核验；vLLM 升级后本文全部内容必须重新核验。本仓负载下的量化后果由 [`docs/findings.md`](../findings.md) 的 FINDING-E1 至 FINDING-E4 持有，本文只记录引擎语义。

## 调度与组批

- v1 Scheduler 每步用单一 token 预算（`max_num_batched_tokens`，本栈默认 2048）组一个批：先遍历 running 队列（decode 与未完成的 chunked prefill 续段），剩余预算再从 waiting 队列接纳新请求，全部进入同一个 `SchedulerOutput`、一次模型 forward（`vllm/v1/core/sched/scheduler.py`，`Scheduler.schedule`）。chunked prefill 默认开启，超预算的 prefill 按预算切段。
- 引擎没有内置的 prefill/decode 分步开关。`scheduler_cls` 可注入自定义调度器类而无需 fork（`vllm/config/scheduler.py`，`get_scheduler_cls`）。`long_prefill_token_threshold` 限制单请求单步推进的 token 数；`disable_chunked_mm_input` 禁止把一个多模态 item 切进两步。
- asynchronous scheduling 在没有不兼容特性（pooling、部分 speculative 配置、不支持的 executor）时默认启用（`vllm/config/vllm.py` 的解析链）。启用后 `max_concurrent_batches=2`，引擎以 `step_with_batch_queue` 流水线执行：步 N+1 已调度并可能在 GPU 上执行时才处理步 N 的输出（`vllm/v1/engine/core.py`）。异步调度下，基础调度器对即将到达 max_tokens 的请求拒绝再调度下一步（`vllm/v1/core/sched/scheduler.py` 中由 `num_output_placeholders` 触发的检查，占位计数由 `async_scheduler.py` 维护）；该检查只覆盖 max-tokens 停止，不覆盖 EOS 或 stop-string 停止。

## CUDA Graph 捕获与分派

- 默认 `cudagraph_mode=FULL_AND_PIECEWISE`。捕获尺寸列表未显式给出时由内置阶梯生成，上限 `max_cudagraph_capture_size = min(2 * max_num_seqs, 512)`（`vllm/config/compilation.py`）。显式传入 `cudagraph_capture_sizes` 时完全替换阶梯：列表去重、剔除超过 `max_num_batched_tokens` 的项、以最大值覆盖上限（`vllm/config/vllm.py`，`_set_cudagraph_sizes`）。FULL decode 键取自同一列表过滤到 `[uniform_decode_query_len, uniform_decode_query_len * max_num_seqs]`，因此显式列表若丢弃小尺寸项会静默失去全部 FULL decode 图。
- 运行时分派（`vllm/v1/cudagraph_dispatcher.py`，`dispatch`）分三类：uniform decode 批且尺寸有 FULL 键 → 回放 FULL 整图（attention 在图内）；其余批 token 总数不超过捕获上限 → 回放 PIECEWISE 图，pad 到最近捕获尺寸；总数超过上限 → NONE，以 torch.compile 编译产物按精确形状 eager 执行，没有回退图。PIECEWISE 下 attention 元数据按未 pad 的真实 token 数构建，pad 浪费只落在非 attention 段。
- `uniform_decode_query_len` 是引擎级标量，等于 `1 + num_speculative_tokens`（`vllm/v1/worker/gpu_model_runner.py` 与 dispatcher 各自计算）。FULL 图对 query 长度大于 1 的 uniform 批的支持被绑定在这一个常量上，没有多种 query 长度并存的入口。
- attention 后端声明 FULL 图的可用面（`AttentionCGSupport`）：FlashAttention 3 为 ALWAYS，FlashAttention 2 为 UNIFORM_BATCH（对混合批请求 FULL 时被降级回 FULL_AND_PIECEWISE，`vllm/config/compilation.py` 的 resolve 链），TRITON_ATTN 为 ALWAYS（`vllm/v1/attention/backends/triton_attn.py`）。sm_86（RTX 3090）默认解析到 FlashAttention 2。
- 图显存在 KV pool 定容之前预扣：`profile_cudagraph_memory` 的估计值从可用显存中减去（`vllm/v1/worker/gpu_worker.py`），受 `VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS` 门控。PIECEWISE 按 splitting_ops 在 attention 与 KV 更新两处切分，每层约两段，每个捕获尺寸各录一份，按尺寸由大到小共享同一显存池捕获。
- 捕获在启动时一次完成，随后 `set_cudagraph_capturing_enabled(False)` 禁止运行期捕获（`vllm/compilation/monitor.py`）；wrapper 本身按首次分派惰性捕获（`vllm/compilation/cuda_graph.py`，`CUDAGraphWrapper`）。

## torch.compile 相关面

- `compile_sizes`（只能经 `compilation_config` 传入）对给定 token 数生成常量形状特化编译。与显式捕获列表并用时，处于捕获上限内的 compile size 必须同时出现在捕获列表，否则启动报错。每个 compile size 触发全部子图的 inductor 重编译与专用 warmup，冷缓存下代价为分钟级；`compile_sizes` 与 `compile_ranges_endpoints` 进入编译缓存键，改动即失效热缓存。
- `compile_ranges_endpoints` 按 token 数区间生成分段编译产物（`vllm/compilation/piecewise_backend.py`），一个区间一份产物，适合覆盖窄带内的可变形状。
- `use_inductor_graph_partition=True` 把图切分从 Dynamo FX 层移到 inductor codegen 之后；Dynamo 路径会把 `unified_kv_cache_update` 等算子追加进 splitting_ops，而 inductor 分区把它们留在分区内，每步回放的段更少（`vllm/config/compilation.py`）。
- `VLLM_USE_BREAKABLE_CUDAGRAPH=1` 启用第二条捕获路径：整个 forward 一次 stream capture，在 attention 与 KV 更新自定义算子处断开、eager 执行后续接捕获，产物是按序回放的可调用列表（`vllm/compilation/breakable_cudagraph.py`）。

## 多模态 encoder

encoder 输入在引擎步内调度并 eager 执行。encoder CUDA graph 机制（`vllm/v1/worker/encoder_cudagraph.py`）只对实现 `SupportsEncoderCudaGraph` 协议的模型生效；0.23 内的实现者是 Qwen2-VL、Qwen2.5-VL、Qwen3-VL、InternVL 与 Step3-VL 的视觉塔。`Qwen2_5OmniThinkerForConditionalGeneration` 未实现该协议，对音频塔设置 `cudagraph_mm_encoder=True` 或 `encoder_cudagraph_token_budgets` 是静默 no-op，没有告警或日志。

## 流式恢复与 KV 逐出的交互语义

- 流式输入的每个新 chunk 经 `AsyncLLM._add_streaming_input_request` 与 `process_inputs(resumable=True)` 进入同一内部请求；`Scheduler._update_request_as_session` 折叠时丢弃上一段末尾已采样、未回喂的 token（停止瞬间 `num_computed_tokens == num_tokens - 1`，截断后二者相等）。因此保持 `num_computed_tokens` 的恢复路径恰好调度新 chunk 的 token 数。
- `num_computed_tokens == 0` 的请求走重匹配分支：GPU prefix hash 命中加 connector 后缀命中，两者都只按完整 block 计数。未写满的 block 从不进入 hash 表（`cache_full_blocks` 只处理满块），也无法 host 备份（`SimpleCPUOffloadConnector` 的 eager store 按 `confirmed_tokens // block_size * block_size` 对齐存储，且当前步写满的块要到下一步才发出存储）；`update_state_after_alloc` 断言外部命中 token 数按 block 对齐。connector 只匹配紧接 GPU 前缀之后的连续后缀，位于 CPU 覆盖段之后的 GPU 缓存块不可达。
- 由此，`free(request)` 之后重入的请求可恢复前缀恰为 `16 * floor((C - 1) / 16)` 个 token（C 为停止时的 computed 数，block size 16）：C 非整块时缺口是被销毁的尾部残块，C 整块时缺口是错过存储窗口的最后一个满块。

## 与本仓库的关系

baseline worker 在引擎几何参数（模型、显存比例、`max_model_len`、`max_num_seqs`）之外只设置 `enforce_eager=False`；Conveyor worker 另外启用 prefix caching 与 CPU offload connector，并在 eviction 模式下强制同步调度。两者的组批与 CUDA graph 行为一致，全部来自上述默认值。本仓负载下的实测后果（图覆盖、步耗时结构、恢复 prefill 余量）由 [`docs/findings.md`](../findings.md) 的 FINDING-E1 至 FINDING-E4 持有。
