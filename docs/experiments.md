# Experiments

## Purpose

本文是实验语义和比较协议的唯一 owner：定义配置域、实验 arms、controlled variables、指标、运行纪律、证据等级和 Metronome baseline 角色。当前结果与机制状态只在 [`Findings`](findings.md) 维护，本文不根据某次 run 改写协议。

## Configuration Domains

### Measured Stack

当前真机测量栈的可执行常量在 `experiments/shared/`，arm-private 行为在各自 `config.py`。下表明确区分 delivery quota 与实际生成行为：

| 配置项 | 共享负载值 | Baseline 行为 | Conveyor 行为 |
| --- | ---: | ---: | ---: |
| 模型 | Qwen2.5-Omni-7B | 共享 | 共享 |
| 运行时 | vLLM 0.23 | 共享 | 共享 |
| 设备 | RTX 3090 | 共享 | 共享 |
| 会话周期 | 2000 ms | 每周期推进 | 每会话仍为 2000 ms；gateway 在周期内分 slot |
| 默认会话数 | 8 | 共享 | 共享 |
| 交付配额 `tpt` | 25 token/tick | gateway 每 tick 消费 25 | gateway 每 tick 消费 25 |
| 实际每段生成量 | 由实验臂决定 | `tpt + 8 = 33` | 精确 `tpt = 25` |
| 每 token KV 字节数 | 56 KiB | 共享 | 共享 |

baseline 的 33 token 是历史 harness 行为，不是负载要求；它会造成库存漂移，但为了保持对照语义仍需显式记录。conveyor 必须精确生成 delivery quota，否则交付流水线会无界积压。

如表中数值与代码不一致，以评审确认后的协议修改为准，并在同一 change transaction 中同步 `experiments/shared/`、arm config 和配置测试；不得静默让文档或代码单方面成为新版本。

### Paper Configuration

论文外推配置使用 Qwen3-1.7B 的 112 KiB/token 标定口径和 480 ms tick，用于公式、roofline 与文本代理负载讨论，不进入当前真机主对比。它与 measured stack 是两套 profile：

- 不能把 480 ms 写成真机 runner 的周期；
- 不能把 112 KiB/token 用于 Qwen2.5-Omni-7B retained run；
- 不能把模拟器或线性外推数字写成真机实测；
- 引用时必须显式标明 `measured`、`paper extrapolation`、`simulator calibration` 或 `frozen prior`。

## Experimental Arms

### Baseline

`PROTOCOL-BASELINE` 使用 metronome 式 vLLM-realtime 栈：

- 每个 session 是持续的 resumable request；
- context 和 GPU KV residency 持续增长；
- gateway 以全局 tick 推进会话；
- `vanilla` 使用 pin 内 worker，保留上游参考行为和上游 logger；
- `paringest` 使用本仓 worker，修复 input processing 并加入与 conveyor 统一的观测；它是正式跨臂测量使用的 baseline target；
- seed run 使用最小 engine fix 刷新被上游冻结的 `session.max_tokens`，这不是 conveyor 机制。

baseline 允许为公平性、可观测性和上游 bug 修复而变化，但每次变化必须说明为什么不改变被比较语义。不能把“baseline”理解成永远禁止修复 silent failure 的旧快照。

### Conveyor

`PROTOCOL-CONVEYOR` 与正式对比使用的 `paringest` baseline 共享模型、workload、client 和 observation producer，只改变以下机制；直观定义见 [`System`](system.md#experimental-arms)：

- gateway 错开相位（phase staggering）：把会话发射分散到周期内；
- worker 取现货交付（take-from-stock delivery）：立即返回上一周期库存；
- EngineCore KV 部分释放（park）：回收可由主机镜像恢复的闲置尾部；
- 可选的 KV 预取（prefetch）：在请求进入引擎前提前搬回尾部。

KV 部分释放 run 当前要求 synchronous scheduling；相应对照如果用于量化该机制，也必须钉住同一 scheduling mode，避免一次比较同时改变两个变量。

### Injection Status

注入负载的冻结先验是：Poisson 到达均值 30 s、LogNormal 长度中位 512 token、40% cancellation。它们属于未来联合协议的输入分布，不表示当前 runner 已经执行 injection producer。

在 injection 端到端接入以前，项目可以验证 foreground、KV lifecycle 和 capacity 机制，但不能做以下主张：

- foreground 与 injection 的最终联合吞吐；
- cancellation 对真实后台结果的端到端收益；
- injection latency distribution；
- 前后台 admission policy 的最终性能。

## Fairness Contract

两臂直接比较时必须共享：

| 受控变量 | 可执行权威 |
| --- | --- |
| Model ID、revision、KV geometry | `experiments/shared/model.py` |
| Tick、sessions、duration、delivery quota、audio chunk | `experiments/shared/workload.py` |
| Device、ports、worker Python、sampling period | `experiments/shared/platform.py` |
| Client implementation 和输入音频 | Metronome pin + runner command |
| Observation producer 和时钟语义 | `paringest` baseline 与 conveyor 共用 `infra/trace/collectors/`；vanilla 保留上游观测，只作参考 |
| Warm-start barrier semantics | 两臂 worker/runner 的对应实现 |

arm-private config 只包含真正被比较的行为，例如 mode、slot、`park`、`prefetch` 和 scheduling mode。worker 的引擎参数由 runner 必填；gateway 虽保留独立启动所需的 CLI fallback，受管 run 一律显式传入协议值。runner 把最终展开值写进 manifest，运行证据不从进程内 fallback 反推配置。

若一次 smoke 两臂使用不同 seed、GPU 或外部负载条件，它们只能证明各自迁移后可运行，不能构成跨臂对照。

## Workload Protocol

### Fresh Process Per Point

每个数据点重新启动 worker、EngineCore、gateway 和 client。长活进程顺序扫点会继承 KV、allocator、cache 和 host 状态，形成 sweep contamination。

同一宿主上的仓库实验不得并行运行：两臂共享固定端口/GPU，pinned client shard 还通过未按 run ID 隔离的 `/tmp/sfd_<index>.json` 汇总结果；重叠运行会发生端口冲突或互删输出。受管 workflow 在启动 client 前删除本次 shard 集合和 controller aggregate 的旧文件，要求每个 shard 及 controller 重新生成结果，并在所有退出路径清理；直接绕过 runner 不具备这条新鲜度保证。

### Warm Start

seed 表示请求进入测量时已经拥有 context。全部 session 的 seed prefill 完成后，gateway/client 才能开始 tick；seed output 不进入 delivery inventory。warm-start 阶段不计作普通 tick，也不能与 KV 部分释放交错。任何 `warm-start barrier timed out` 日志都是 validation failure，即使 worker 随后写出了 ready file。详细状态语义见 [`System`](system.md#warm-start)。

### Phase

输入 phase 必须由协议显式控制或记录。关闭错开相位时，相同音频同步进入多路会话还可能触发 prefix-cache 去重，制造虚高容量；任何此类运行必须在 manifest 和 finding scope 中说明。

### Repetition

主结果点要求乱序重复至少三次并报告中位数，同时保留每次 run 的离散度。单次 smoke、故障复现和语义验证可以作为 diagnostic evidence，但不能自动升级为正式性能结论。

## Metric Semantics

| 指标 | 定义 | 禁止误用 |
| --- | --- | --- |
| `deadline_met` | conveyor 按实际交付量定义；pin baseline 的同名字段仍只比较 `gpu_ms` 与 budget，不能作为 correctness gate | 正式 paringest baseline 由 worker `delivery` 记录和 runner validation 检查；首次足额前属于 TTFA，但每个会话必须在 run 内至少足额一次，之后任何欠额都是 starvation |
| TTFA | 第一个非 seed、非空交付；取现货交付包含固有 pipeline latency | 不能用旧的“首个 Step 返回”口径 |
| Client latency | transport/Step latency | conveyor 下不包含 GPU 工作，不能当计算延迟 |
| Tick-to-prefill | gateway/worker 时钟对齐后的 input 到 prefill | 旧 run 的启发式对齐必须标记偏差 |
| Content freshness | 生成内容与对应输入的逻辑距离 | cadence 正常不代表 freshness 正常 |
| Inventory depth | 已生成未交付 token | 应长期有界；斜率不为零即 drift |
| KV occupancy | pool 已使用比例 | 必须结合 per-session residency 和 starvation |
| Schedulable concurrency `N*` | 在定义的 deadline/freshness/health gates 下可持续的最大 `N` | 不能只用 GPU utilization 或短 run 外推 |

silent failure 判读必须联合使用 client、worker、EngineCore 和 trace。client miss=0 不能覆盖 session death、stale content、inventory drift 或 irreversible starvation。

## Saturation and Acceptance

capacity saturation 由 KV occupancy、re-admission、starvation 和长期 backlog 共同判定；deadline saturation 由完工时刻逐 tick 后移或 delivery failure 判定。GPU utilization 不是任一边界的充分条件。

一个 run 至少满足以下条件才能进入 evidence registry：

1. `status.json` 为终态；
2. required artifacts 全部存在且非空；
3. issue scanner 没有被 exit code 掩盖，并已检查 Step error、session death、client health、从未足额的会话与首次足额后的 short delivery；
4. manifest 足以恢复配置、命令、软件和模型 revision；
5. 与比较对象的 controlled variables 一致，或明确标为不可比较；
6. finding 所依赖的观测事件真实出现；
7. 证据等级和 source provenance 满足下一节要求。

## Evidence Levels

### Formal Evidence

formal evidence 可以支撑论文性能、容量和跨臂主张，要求：

- clean worktree；
- 运行 commit、third-party pin、模型 revision、命令和配置完整；
- protocol-compatible comparison；
- validation 通过；
- 需要重复的结果完成规定 repetitions；
- exact run 通过 `EVIDENCE-*` alias 登记，而不是写入人类 prose。

### Diagnostic Evidence

diagnostic evidence 可以支撑机制语义、故障指纹和根因探索。它允许 failed run 或 dirty worktree，但 dirty 运行必须保存可重建的 binary diff、untracked source bundle 和 hash。没有 patch artifact 的历史 dirty run必须在 registry 中标为 `legacy-unreconstructable`，不能称作 formal。

### Experiment Records

新实验过程使用结构化 record，记录 question、configuration profile、change、result、verdict、evidence alias、affected findings、supersedes 和 remaining uncertainty。旧的 append-only 日志已冻结在 [`legacy-experiment-log.md`](agent/legacy-experiment-log.md)，只用于历史追溯。

## Metronome Baseline

`third_party/metronome/` 是只读 git-subrepo pin，精确 commit 以其 `.gitrepo` 为准。它在本项目中有四个角色：

| 角色 | 含义 |
| --- | --- |
| 主 baseline | vanilla resumable-request serving，context 无界增长 |
| 有损对照 | request recycling 或 in-engine sliding-window KV |
| 正交机制 | AIMD admission control，处理 capacity 之外的过载 |
| 实验脚手架 | gateway、proto、client 与 worker 的来源 |

必须继承的两条方法论是 fresh process per point，以及显式控制 phase；但本项目不继承 pin 中已经被论文订正的旧归因。

引用纪律：

- 归因以 paper 的 “memory cliff, not a compute drift” 为准；repo 旧笔记中的 attention drift 不作为现行结论；
- 上游等待帽读数同时混合 compute-bound 与 memory-bound，不能单独定性；
- 可引用的 `N*`、显存外推和论文配置必须说明设备与方法，不能拿来校准本仓消费卡数字；
- Metronome 没有覆盖真实 injection producer 和应用层 cancellation；proto 中存在字段不等于协议已实现；
- pin 的升级和只读规则由 `third_party/AGENTS.md` 持有。

## Legacy Identifiers

跨文档引用必须使用完整命名空间：

```text
FINDING-H7     当前发现
CLAIM-C1       论文主张
EXP-E1         历史实验代号
EVIDENCE-H7-*  精确证据 alias
```

旧 `E0–E6` 只属于历史语境，其中 `EXP-E1` 对应当前 baseline 病理实验；其他映射保留在 git 历史和 legacy experiment log，不再把裸 `E1` 当成现行实验名。
