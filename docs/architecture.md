# architecture：代码架构

本文维护仓库代码的层级结构与功能分工。**改动代码结构时必须同步更新本文**（过时是 bug；守卫测试会扫本文里的路径）。数字与结论不住这里——那是 `docs/findings.md` 的事。

## 〇、三分钟总览（写给第一次打开本仓库的人）

**这个系统在做什么**：想象 8 个人同时和一个语音助手打电话。每个人的语音每 2 秒切成一小段送进来，助手必须在下一个 2 秒内为每个人生成 25 个 token 的回应——这是硬 deadline，迟到就是事故。所有人共用一张 24GB 的消费级显卡，而每个人的对话历史（KV cache）会无限增长。**显存不够是核心矛盾，算力反而有富余。**

**一次请求的旅程**（30 秒版）：

```
用户音频 → client（模拟 8 个用户，20ms 一小块持续推流）
        → gateway（Go 程序：缓冲满 2 秒切一片，按固定节拍转发）
        → worker（Python + vLLM：语音转特征 → prefill → decode 生成 25 个 token）
        → 原路返回给用户
```

**本项目的核心思路一句话**：每个会话每 2 秒里只有零点几秒真正在计算，其余时间它的 KV 闲置占用显存——把闲置会话的 KV 大部分搬到主机内存，轮到它计算之前再搬回来，用空闲的 PCIe 带宽赎回显存容量。

**两个实验目录**：`experiments/baseline/` 是「现状」——直接用现有 vLLM 栈服务这个负载，用来展示它如何失败（已冻结，不再改）；`experiments/conveyor/` 是我们的新引擎，在 baseline 之上做了三件事：

1. **错开相位**：baseline 里 8 个会话在同一毫秒同时发起请求，形成惊群；conveyor 把它们均匀排开——每 250ms 只服务一个会话（称为一个「槽」），按固定顺序轮转。
2. **取现货交付**：不等待本周期的计算完成，而是立即交付上一周期已生成的库存 token。代价是交付内容恰好滞后一片，换来的是发射节拍不被慢会话拖慢。
3. **park 驻留管理**：会话每算完一片就立即释放其 KV 的大部分（「尾巴」）——释放前内容已异步备份到主机内存（「镜像」），下次轮到它计算前再搬回显存（「回载」）。显存里常驻的只剩一个固定大小的「底座」。

**术语表**（本仓库文档与代码注释的固定用词，均有严格定义）：

| 术语 | 含义 |
| --- | --- |
| tick / 周期 | 2 秒的硬节拍。每个 tick 每会话送进一片音频、要求交出 25 个 token |
| 片 (chunk) | 一个 tick 的音频输入（2 秒 ≈ 53 个音频 token） |
| 错开相位 (staggered phase) | conveyor 机制一：把各会话的发射时刻均匀铺在周期内（槽轮实现），消除同步到达的惊群 |
| 取现货交付 (take-from-stock) | conveyor 机制二：每 tick 立即交付上一周期生成的库存 token，不等待本片计算完成 |
| 段 (segment/slice) | 引擎为一片音频做的一轮计算：prefill 该片 + decode 出 25 个 token |
| tpt | tokens per tick = 25，每周期的交付配额 |
| FE (feature extraction) | 音频转频谱特征的 CPU 计算，每片 ~272ms，是计算前的固定门槛 |
| KV 块 (block) | vLLM 显存管理的最小单位 = 16 个 token 的 KV（本机 896KB/块） |
| 槽 (slot) / 槽轮 | conveyor gateway 把周期均分成 8 个发射时刻，每会话固定占一个槽 |
| 库存 (inventory) | 取现货模式下已生成、还没交付的 token 缓冲；健康深度恒等于一片（~25） |
| park | 我们给 vLLM 打的补丁提供的原语：释放一个闲置会话的 KV 块（详见十站表第 10 站） |
| 底座 (K) / 尾巴 | park 后留在显存的固定前缀（K 块）/ 被释放、轮转于内存-显存之间的其余部分 |
| 镜像 (mirror, S) | 每个 KV 块算好后自动异步备份到主机内存池；只备份新增量 |
| 回载 (reload, L/R) | 会话要算下一片时，把被 park 掉的尾巴从主机内存按内容哈希搬回显存 |
| seed / warm start | 让每个会话开局就带 N 个 token 的上下文（模拟长对话），全部就位后 tick 才开始 |
| run / artifact | 一次实验执行 / 它落在 `results/` 不可变目录里的证据文件 |
| pin | `third_party/` 里锁定版本的第三方仓库，只读 |

**上手路径**：运行入口看 `README.md` 的 quickstart；每个机制"为什么"看 `docs/findings.md` H 系列；逐周期发生了什么、时间线怎么读，看本文「一个会话的一个周期」十站表。

## 一、代码分层：五层单向依赖

```
入口层      experiments/<exp>/__main__.py         argv → 关键字参数，纯翻译
配置层      experiments/<exp>/config/             全部参数的唯一声明处（纯 Python 常量 + 逐 run 旋钮）
声明层      experiments/<exp>/runner.py           本实验有什么不同：命令、环境、issue 扫描，组装成 RunPlan
共享设施    lab/  +  tracekit/(采集侧)            实验无关的零件：运行工作流（lab/workflow 执行 RunPlan：
                                                  就绪等待、client 看门狗、收尾判决）、证据目录、进程组、
                                                  探针、trace 注入
─────────── 进程边界 ───────────
执行层      experiments/<exp>/worker/             GPU 进程本体（venv python，被 argv+env 生出、被 gRPC 驱动）
            gateway（Go）与 client（负载生成器）   baseline 用 pin 原样；conveyor 自带 gateway fork
─────────── 文件边界 ───────────
离线层      tracekit/(解析导出侧)                 事后读 run 目录：解析、时钟对齐、Perfetto 导出
```

两条结构性约束：

1. **依赖单向向下**。`lab/`、`tracekit/`、`environment/` 不认识任何实验的名字；实验目录之间互不引用。唯一的反向边：`lab/` 复用 `environment/verify.py` 的探测函数（`capture` / `collect_software`）。
2. **跨越进程边界只有三种通道**：argv+环境变量（runner → 子进程，启动时一次性）、gRPC（gateway ↔ worker，运行期）、run 目录里的文件（一切 → 离线层）。没有任何跨进程的 Python import。

## 二、目录与文件职责

### experiments/baseline/（现状对照臂，已冻结，~900 行）

| 文件 | 行数 | 职责 |
| --- | --- | --- |
| `__main__.py` | ~46 | `python -m experiments.baseline` 入口。七个参数（mode/trace/label/sessions/duration/seed-tokens/gpu），零配置知识，`run(argv, **vars(args))` 转发 |
| `config/__init__.py` | ~146 | `BaselineConfig`（逐 run 旋钮 + 引擎常量如 MML=32768）、`MODES` 表、`required_artifact_names()`、`manifest_config()` |
| `config/model.py` | ~28 | Qwen2.5-Omni-7B：id、锁定 revision、KV 几何（56KiB/token 及推导） |
| `config/platform.py` | ~23 | 这台机器：默认卡号、venv 路径、两个端口、GPU 采样周期（与解析端耦合，只在此改） |
| `config/workload.py` | ~28 | 2s tick、8 路、600s、tpt=25、实测 growth=78/tick |
| `runner.py` | ~188 | 本实验的差异声明：worker/gateway/client 的命令与环境、issue 扫描（scheduler trace 错误、engine-fatal、client err），组装成 `RunPlan` 交 `lab/workflow` 执行 |
| `worker/stream_server.py` | ~449 | GPU 进程本体。复制自 pin 内同名文件后永久分道（与来源的差异清单见其文件头 ORIGIN 节）。核心：每会话一个常驻可续 (resumable) 请求，每片只追加新音频、复用已有 KV；ingest 线程池补丁；观测插桩（kv.log / per_request.log 的产出方）。引擎几何参数全部必填——config/ 是唯一默认值声明处 |

配置的读写规则：**两个设置入口**（命令行旋钮；改 config/ 常量文件），**一个消费者**（runner）。worker/gateway/client 不读 config——它们只收 runner 翻译后的 argv 和环境变量。

### experiments/conveyor/（新引擎，~2000 行，含 gateway 与 engine_patch）

骨架与 baseline 逐文件同形（`__main__.py` / `config/` / `runner.py` / `worker/`），差异全部是三个机制本身。每个文件先说一句它是干嘛的，再列细节：

| 文件 | 职责与差异 |
| --- | --- |
| `gateway/`（baseline 没有的层） | **实现错开相位的 Go 网关**，复制自 pin 的 gateway-go 后永久分道。要点：① 全局节拍器换成槽轮——每 250ms 醒一次、只服务本槽的会话，发射时刻钉在绝对网格 `t0+k×250ms` 上（晚醒自动回弹，不累积漂移）；② 会话按到达顺序轮流分配槽位；③ 指标口径适配取现货语义——`deadline_met` = 本 tick 交付 ≥ tpt 个 token，交付不足打 `[starve]` 日志；④ 每次发射写一行 `gateway_ticks.log`（发射晚了多少、给每个会话交付了多少）；⑤ 本仓库栈不可达的继承路径已剪除（turn-based 响应生命周期、vision 附件、AIMD 在线准入——pin 为 baseline 臂原样保留），只服务全双工槽轮一种形状，worker 永不健康则直接 fatal。差异全清单见文件头 ORIGIN 节 |
| `worker/stream_server.py` | **实现取现货交付的 GPU 进程**，复制自 baseline worker 后永久分道。要点：① Step 收到新音频片后立即返回库存中的 token，不等待本片计算完成（阻塞式等待会把错开的槽重新串行化）；② 每段生成配额精确等于 tpt（任何多余产出都会在库存中累积，交付内容与音频的对应关系持续后移）；③ warm start 屏障——seed run 先完成全部会话的 seed prefill 才宣布就绪；④ 接入 vLLM 自带的 `SimpleCPUOffloadConnector` 做主机镜像池（`--host-offload-gib`）。差异全清单见文件头 ORIGIN 节 |
| `worker/engine_patch/sitecustomize.py` | **park 原语本体**：给 vLLM 调度器打的轻量补丁（~300 行，经 PYTHONPATH 注入 vLLM 的 EngineCore 子进程）。核心动作两步：释放会话对全部 KV 块的引用（内容原地保留、可被按哈希认领回来）+ 精确销毁底座 K 之外的尾部块（下次由镜像回载）。主路径是 auto-park：会话每算完一片、转入闲置态的那一瞬间原地执行。同时修复两个 vLLM 上游 bug（镜像游标漂移、每段配额被冻结）。完整机制、时序与正确性论证都在该文件的 docstring——它是本仓库注释最重的文件，值得整篇读 |
| `config/__init__.py` | `ConveyorConfig`：机制旋钮集中地——`slots`（槽数）、`park_keep_blocks`（底座 K，设置即启用 auto-park）、`host_offload_gib`（镜像池大小）、`sync_scheduling`（对照臂钉住同步调度用）等，每个旋钮的含义和取值理由都写在字段旁注释里；model/platform/workload 三个常量文件与 baseline 一致（同栈对比的前提） |
| `runner.py` | 与 baseline runner 同形的差异声明（组装 `RunPlan` 交 `lab/workflow` 执行）：gateway 加 `--slots` 并写 `gateway_ticks.log`；worker 加镜像与 park 参数；park 开启时把 `engine_patch/` 前置到 PYTHONPATH 并设 `OMNI_PARK_KEEP` 等环境变量；issue 扫描多三类静默失败（会话死亡、交付饥饿、park 未生效），扫描字符串与产出方由 `tests/test_run_validation.py` 钉住 |

**机制现状**（2026-08-12）：三个机制全链路已实现并有权威证据——稳态显存占用 0.296 vs 全驻留假设的 0.860（66% 的 KV 换到了主机内存），回载中位 70ms，交付零恶化（run `20260811_193634_park-onstop`）。结论提炼在 `docs/findings.md` H 系列；实现过程的完整问题与根因记录在 `docs/experiment-log.md` 2026-08-10 起的条目。**指标可信度**：client 侧的 `deadline_met`（miss = 引擎未跟上）与 TTFA（含固有的一片滞后）可以引用；latency p50/p99 永久无效（取现货的 Step 不含任何 GPU 等待），延迟分布一律以 trace 侧为准。

**已知未决**：回载与 FE 串行——回载要等音频片完成 FE 后才触发，在关键路径上多付一个回载时长（当前 70ms，随尾巴变大而增长）；彻底解决需要「预取」原语（提前把尾巴搬回显存、与 FE 并行执行）；预取过早会延长显存驻留、抵消 park 的收益。

#### 一个会话的一个周期：机制解说与仪器对照

下表沿一个会话的一个 2s 周期走完全链路。每一站回答四件事：发生什么、为什么这样设计、哪个仪器记录了它、健康时长什么样。Perfetto 时间线（run 目录 `derived/timeline.trace.json.gz`，导入 ui.perfetto.dev）把全部泳道对齐在同一时钟上——**本表就是读图指南**。

| # | 站点 | 发生什么、为什么 | 证据在哪 | 健康形态 |
| --- | --- | --- | --- | --- |
| 1 | 槽轮发射 | gateway 在绝对网格 `t0+k×250ms` 准时醒来，只服务本槽会话。会话之间的**相对**间距是错开机制的全部内容 | gateway_ticks.log 的 `late_ms`；Perfetto gateway 泳道 | 晚醒 p50≈0.6ms 无离群；发射间距 249-251ms |
| 2 | 交付（取现货） | 缓冲好的 2 秒音频经 gRPC 送 worker；worker 把它放入会话队列后**立即**返回库存 token。交付内容因此恰好滞后一片 | per_request.log `P` 行；gateway_ticks 的 `deliv=` | 每 tick 交付满额 25；会话的第一片交付 0（豁免） |
| 3 | FE（音频转特征） | 线程池并行执行各会话的特征提取；这是每片计算前 ~272ms 的固定门槛 | `IQ/IS/IE/IR/IA` 五站插桩；Perfetto 会话泳道的 ingest 三段 slice | FE 本征 87ms、系统内 272ms（膨胀根因：与事件循环竞争 GIL——见 FINDINGS H5）；其余各段 ≤3ms |
| 4 | 递交引擎 | 处理好的音频片进入 vLLM 调度器，接到该会话的常驻请求上（上一片的输出折入对话历史）。park 补丁的会话更新钩子在此生效 | scheduler.log 中该会话下一行的出现 | 音频送出到 prefill 开始，中位 ~291ms（≈FE 门槛） |
| 5a | 回载（若已 park） | 调度器发现该会话的 KV 有缺口：留在显存的底座按哈希直接认领回来（零拷贝），被销毁的尾巴从主机镜像异步搬回。搬完才开始算 | park.log `L` 行（开始，`cpu_tok`=回载量）与 `R` 行（完成）；Perfetto 的 KV reload slice | 回载 ~70ms（330MB 尾巴）。已知问题：它排在 FE 之后串行（见已知未决） |
| 5b | 直接续算（未 park） | KV 完整在显存，直接从断点继续，无任何额外动作 | （无事件即证据） | — |
| 6 | prefill | 计算新音频片（~53 个音频 token），音频塔的 encoder 在同一步执行 | scheduler.log 带 `E` 的多 token 行 | 每片 50-200 token；**超过 400 token 会被标成 `LARGE` = 疑似在重算本该回载的内容**（warm start 期的 seed prefill 除外） |
| 7 | decode | 生成本段的 25 个 token，配额精确等于 tpt，不允许任何超出——多余产出会在库存中累积，交付内容对应的音频越来越旧（见指纹表「库存漂移」） | scheduler.log 单 token 行；worker.log 的 `inv_backlog` | 生成速率 12.5 tok/s/会话；`inv_backlog` 恒 ≈25 |
| 8 | 停止、闲置 | 本段配额用完，会话进入等待下一片的闲置态。注意：vLLM 自己**永远不会**释放闲置会话的 KV（这正是要自建 park 的原因，论证见 FINDINGS H3） | kv.log 的 `run=` 在段间回落 | 每周期闲置 ≈(2s − 段时长) |
| 9 | 镜像（后台备份） | 每个新写满的 KV 块被异步复制到主机内存池。只复制**新增量**——尾巴反复 park/回载不产生重复拷贝。注意它不是「搬走」：显存副本原地不动，真正释放显存的是 park | park.log `S` 行；Perfetto 的 KV mirror 标记 | 每周期备份量 ≈ 上下文增长量（个位数块）。每周期第一个 S 记的是上一段的收尾（预期行为） |
| 10 | park（decode 结束瞬间） | 会话转入闲置态的那一行代码里，补丁原地释放它全部 KV 块的引用、销毁底座 K 之外的尾部（留 2 块余量给尚未备份完成的最新块，永不销毁块 0——它是所有会话共享的系统提示词）。显存占用随之下降；物理显存从不归还 CUDA，「释放」的含义是池内槽位可复用 | park.log park 行；Perfetto 的 PARK 标记 + 每会话驻留锯齿 counter；kv.log `kv=` 下降 | 稳态池占用 0.296 vs 全驻留 0.860（run `20260811_193634_park-onstop`） |

失效模式指纹（每种失效在仪器上的表现，按站点索引）：

| 失效 | 指纹 | 站点 |
| --- | --- | --- |
| 引擎跟不上（饥饿） | gateway_ticks `deliv<25` → gateway.log `[starve]` → client miss>0；`T` 行斜率 <12.5 tok/s | 2/7 |
| 库存漂移（交付内容越来越旧，而指标全部正常） | worker.log `inv_backlog` 随时间增长（健康 = 恒 ≈25） | 2/7 |
| 回载退化为重算 | Perfetto 出现 `LARGE` prefill；`L` 行 `cpu_tok` 偏小 | 5a/6 |
| 镜像缺口 | park.log `cpu_covered ≪ evicted` 持续出现 | 9 |
| 段配额异常 | 总 token 数每片只涨 ~1；示例文本停滞 | 7 |
| 会话死亡 | worker.log ` ended: `（runner 判 issue）；其余指标仍显示正常 | — |
| 槽轮失稳 | gateway_ticks `late_ms` 尖峰；每会话周期漂离 2000ms | 1 |
| FE 拥堵 | IS→IE 段膨胀（GIL 竞争）或 IQ→IS 排队（线程池满） | 3 |
| 回载压进计算 | Perfetto 的 reload slice 与计算 slice 重叠 | 5a |

### lab/（实验无关的运行设施，~500 行）

| 文件 | 职责 | 关键契约 |
| --- | --- | --- |
| `workflow.py` | 全仓唯一的运行时间线（`RunPlan` 声明 → `execute` 执行）：manifest → 建 run 目录 → worker 等 ready → 辅助进程 → client → 收尾判决 | client 有看门狗（duration + 裕量，超时杀进程并记 issue，无人值守扫描不悬挂）；SIGINT/SIGTERM 落成 `interrupted` 终态；任何退出路径都经 `finally` 杀进程组 + finalize |
| `artifacts.py` | 不可变 run 目录的唯一实现 | `mkdir` 无 `exist_ok`（绝不复用）；元数据原子替换、证据只写一次；`finalize`：**exit 0 救不了缺失/空文件/带 issue 的 run**；三种终态 success / failed / interrupted，全部保留 |
| `probes.py` | provenance 快照（git / pin / 主机 / GPU / 模型 snapshot 路径） | 只读探测，错误记录不抛；例外是 `resolve_model_snapshot`——revision 锁定的执行点，snapshot 不在缓存时 fail-fast（它直接进 worker argv，静默 None 曾造出 `--model None`） |
| `process.py` | 进程组编排 | `start_new_session=True`，按 PGID 杀是收掉 vLLM EngineCore 子进程的唯一可靠办法；日志 `"xb"` 模式绝不追加 |

### tracekit/（观测全链路，~790 行）

采集侧（run 时活着）：

| 文件 | 职责 |
| --- | --- |
| `collect.py` | 两个函数：`apply_scheduler_trace`（环境变量 + PYTHONPATH 前置）与 `gpu_monitor_command`（nvidia-smi 命令行） |
| `collectors/vllm_scheduler_trace/sitecustomize.py` | 借"每个 Python 进程启动必 import sitecustomize"钩进 vLLM EngineCore 子进程，记录每个调度步；init 失败 `os._exit(78)`——被要求的 trace 是主证据，宁可显式失败 |

离线侧（`python -m tracekit.perfetto <run>` 时才运行）：

| 文件 | 职责 |
| --- | --- |
| `parse.py` | 六个解析器（per_request / kv / scheduler / gpu / gateway_ticks / park），保存全部行格式知识（各解析器 docstring 给出精确 grammar） |
| `bundle.py` | 按 run 目录里实际存在的文件组装数据包；时钟对齐（worker 写的双时钟配对行使对齐精确；旧 run 回退启发式并如实记录偏差） |
| `perfetto.py` | 全部泳道的导出：引擎调度步、ingest 三段、KV 管理（PARK/mirror/reload）、gateway 发射、驻留与池占用 counter。只写一次、失败即清理、metadata 记全部源文件 hash。**读图陷阱**（slice 宽是调度轴不是 GPU 执行轴等）见 `tracekit/AGENTS.md` |

### environment/（锁定运行时，~270 行）

`setup.sh`（建 venv、hash 锁安装、打补丁、编译两个 gateway、下载锁定模型）、`verify.py`（环境校验：探测库与 CLI 合一，runner 经它把软件快照写进 manifest）。`profiles/cuda13_vllm023/` 是唯一 profile。vLLM 升级前的重审清单在 `environment/README.md`。

### third_party/metronome/（只读 pin）

baseline 复用四块：**gateway**（Go；全局节拍器每 2s 收集所有会话缓冲、发一次 gRPC `Step`）、**worker**（vanilla 模式原样运行；也是我们两个 worker 的复制来源）、**proto**（`Step`/`Health` 契约；`SessionInput.text` 与 `.cancel` 字段闲置，是将来注入/打断语义的现成接口）、**client**（`sustained_fd.py`，20ms 小块 WebSocket 持续推流，`FD_PHASE_STAGGER` 防 prefix cache 去重虚高容量）。

### tests/（37 个契约钉，~700 行；从仓库根 `python -m unittest discover` 运行）

不测显而易见的代码，只钉会无声回归的决定：仓库布局一致性（`test_repository_layout.py`，扫描面含 `.github/`，含"每个保留 run 必须在 results 索引里"）、证据纪律与三种终态（artifacts）、运行工作流（`test_lab_workflow.py`：就绪 / 看门狗 / worker 早死 / SIGTERM→interrupted，跑在假子进程上）、run 判决的日志字符串契约与 warmup 哨兵三处一致（`test_run_validation.py`，含 Go 侧 `[starve]` 产出方）、trace 格式知识与导出契约（tracekit）、venv 符号链接与 manifest 键契约（两个实验的 config）。GPU 路径的验收门是真实 run，不是这些测试。

## 三、运行时进程拓扑

```
runner（系统 python，编排进程）
 ├─ 生成→ worker（.venv-vllm023 python）── 派生→ EngineCore（vLLM 子进程，sitecustomize 在此生效）
 ├─ 生成→ metronome-gateway（Go 二进制）
 ├─ 生成→ nvidia-smi --loop（旁路采样）
 └─ 生成→ sustained_fd client（venv python）
运行期数据面：client ══20ms 音频══▶ gateway ══每 2s 一次 Step(8 路合批)══▶ worker ══token══▶ 原路返回
```

时间语义的分工：**tick 与 deadline 只存在于 gateway**；worker 与 vLLM 引擎对 tick 零感知，按通用 serving 语义连续批处理。这种"引擎不知道节拍"的结构性信息缺失，是 baseline 各种失败的共同根源，也是 conveyor 全部机制实施改动的位置。

## 四、文件格式契约（写方 → 读方）

| 文件 | 写方 | 读方 | 备注 |
| --- | --- | --- | --- |
| `manifest.json` / `status.json` | `lab/workflow`（经 `lab/artifacts`） | tracekit bundle、人、守卫测试 | bundle 从 manifest 读 `period_ms`、`gpu_sample_period_s`——**跨模块键名契约**，有测试钉住 |
| `kv.log` | worker 的 `_StatLog`（节流可配：`OMNI_STATLOG_PERIOD_S`，conveyor 默认 0.2s = 每 tick 10 采样） | `parse_kv` | 判读容量墙/starvation 的主证据；`pre=` 为累计抢占（evict 字段不捕获） |
| `per_request.log`（P/F/T/SEED + 五站） | worker 的 `_pev()` | `parse_per_request` | warmup 哨兵会话的 push 时间是双时钟桥 |
| `per_iteration.log` | worker 的 `_StatLog`（逐步） | 人（ad-hoc） | 行格式 `<t_rel> run=N wait=N gen=N ptok=N`（每引擎步一行，无节流）；无 tracekit 消费者 |
| `scheduler.log` | sitecustomize（EngineCore 内） | `parse_scheduler` | 请求 id 必须是 `s<sid>e<n>` 形状（`SESSION_PATTERN`），worker 侧有注释钉住 |
| `gpu.csv` | nvidia-smi | `parse_gpu` | 采样周期经 manifest 传递，样本居中 |
| `gateway_ticks.log` | conveyor gateway（`GW_TICKLOG`，每发射一行） | `parse_gateway_ticks` | epoch 时钟直接对齐 scheduler.log；每会话交付量在交付点测得，是取现货 deadline 口径的原始事实 |
| `park.log` | engine_patch（EngineCore 内） | `parse_park` | epoch 时钟；四种行：park 行（held/evicted/cpu_covered/池占用前后，cpu_covered 是下界）、`S` 行（镜像发出）、`L` 行（回载开始）、`R` 行（回载完成）；park 开启时为必需 artifact，空文件即 issue |
| `client.json` / `client.txt` | pin 的 client（结果文件由 `lab/workflow` 移入 run 目录） | finalize 校验、人 | 字段：`ev` = [已过秒数, latency_ms, miss01] 列表（latency 在取现货引擎下无意义，miss 为交付口径）、`ttfa`[ms]、`err`、`audio_out`、`total/duration/budget_ms`；pin 硬编码输出位置，一次 `replace` 调用是无法移除的适配 |
| `derived/*` | tracekit 导出 | Perfetto UI、人 | 只写一次 |

## 五、新实验的接入形状

复用既有骨架：`experiments/<name>/{__main__.py, config/, runner.py, worker/}`（conveyor 就是按此接入的现成例子）。runner 只写差异（命令、环境、issue 扫描），组装 `RunPlan` 交 `lab/workflow.execute`——就绪等待、看门狗、收尾判决直接继承；lab 其余三件与 tracekit 直接复用；worker 只要继续实现 metronome 的 proto，client 原样复用。**负载同构的边界**：两臂必须共享同一个 client 与全部 workload 常量（音频节奏、tpt、时长）——这保证「进入系统的负载」同构；gateway 与 worker 的差异**属于被比较的机制本身**（conveyor 的槽轮 gateway 正是三增量之一），不违反同构。证据落进 `results/<name>/runs/`，解析与可视化链路随之继承。
