# System

## Design Goals

Conveyor 在普通 continuous-batching 接口之外使用两个工作负载事实：会话是周期性的，以及每个会话预计在何时再次使用 KV cache。系统目标是在保持完整上下文的同时降低空闲会话的 GPU KV 驻留，并避免把大量恢复流量集中到同一短窗口。

设计遵循以下不变量：

1. 每个会话保留完整逻辑上下文，不用有损滑动窗口换取容量；
2. 每个会话的周期保持为 \(T\)，释放偏移只改变周期内的位置；
3. KV 逐出只发生在 resumable request 已进入 idle 后；
4. GPU block pool 是物理驻留的唯一真相，控制 registry 不复制 block 状态；
5. 主机后备覆盖必须显式记录；没有主机副本的逐出块只能在恢复时重算；
6. KV 预取只能改善时序，拒绝、迟到或被 LRU 逐出时必须安全退化为按需恢复或重算；
7. 初始上下文构造在开始周期输入之前完成，不与普通周期更新交错；
8. 每个已启用机制必须产生独立观测事件，patch 加载失败必须终止 run。

实验配置和当前结果分别由 [`Experiments`](experiments.md) 与 [`Findings`](findings.md) 持有；本文不复制性能数字。

## System Topology

```text
   ┌───────────────────────────────────────────────────────────┐
   │ Runner: experiments/{baseline|conveyor}/runner.py         │
   │ config -> RunPlan -> infra/run/workflow.execute()         │
   │ manifest first, watchdog, process-group cleanup, verdict  │
   └───┬────────────────┬─────────────────┬────────────────┬───┘
 spawn │          spawn │           spawn │          spawn │
       ▼                ▼                 ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌───────────────┐ ┌─────────────┐
│ Client       │ │ Gateway (Go) │ │ Worker (Py)   │ │ GPU monitor │
│ controller   │ │ absolute grid│ │ feature extr. │ │ nvidia-smi  │
│ + N shards   │ │ T, phi(i)    │ │ output buffer │ │ -> gpu.csv  │
└──────────────┘ └──────────────┘ └───────┬───────┘ └─────────────┘
                                          │ spawns (vLLM internal)
                                          ▼
                          ┌───────────────────────────────┐
                          │ EngineCore (vLLM subprocess)  │
                          │ Scheduler + GPU KV block pool │
                          │ sitecustomize patches attach  │
                          └───────────────────────────────┘

在线请求路径: shards ──WebSocket──► gateway ──gRPC Step──► worker ──msgpack/ZMQ──► EngineCore
```

runner 只负责启动、终态判决和 artifact 登记，不进入数据面。全部进程的日志与观测输出写入不可变 run 目录，文件布局与离线解析见 [Observability Model](#observability-model)。机制补丁与 trace 观测都由 worker Python 的 `sitecustomize` 在进程启动时注入。精确组件和动态调用边分别由 [`system-map.json`](agent/system-map.json) 与 [`dynamic-edges.json`](agent/dynamic-edges.json) 持有。

## Conveyor Mechanisms

evaluated systems 的完整清单、配置与比较资格由 [`Experiments`](experiments.md#evaluated-systems) 持有；本节只定义 Conveyor 的机制语义。matched Metronome baseline 保留默认的全 GPU KV 驻留语义，是机制对照的参照系。

Conveyor 当前研究三项候选机制：

| 机制 | 对象与动作 | 所属层 |
| --- | --- | --- |
| 释放偏移调度（release-offset scheduling） | 为周期会话分配不同释放偏移，分散多会话需求 | Gateway |
| 带主机后备的 KV 部分逐出（partial KV eviction with host backing） | 增量复制完成块，并在会话 idle 后逐出选定 GPU KV 尾块 | EngineCore |
| KV 预取（KV prefetching） | 在预计复用前把 host-backed blocks 放入 GPU prefix cache | Worker + EngineCore |

worker 的无等待 `Step` 是当前实现选择：它提交当前输入后快照未交付输出缓冲，不等待本次计算。该选择避免一个慢 RPC 阻塞之后的释放槽，但可以被独立输出流等实现替代，因此不进入机制或贡献列表。

## Release-Offset Scheduling

会话 (i) 的第 (k) 次释放发生在：

```text
r(i, k) = r(i, 0) + kT
phi(i) = r(i, 0) mod T
```

gateway 使用绝对时间网格，并在会话建立时分配稳定的 \(\phi_i\)。一次晚醒只影响当前 firing，下一次仍回到原绝对网格，不累积重锚漂移。

每个周期会话在两次使用之间本来就有复用间隔。释放偏移不创造该间隔；它把原本同步的 input processing、engine admission、compute 和潜在 KV restore demand 分散到周期内。各项收益的证据状态由 [`FINDING-D3`](findings.md#finding-d3) 与 [`FINDING-H1`](findings.md#finding-h1) 持有。

## KV State Model

系统不用一个单一 lifecycle 混合多个对象。一次会话的状态由以下正交事实描述：

| 对象 | 状态或属性 | 真相来源 |
| --- | --- | --- |
| Session | `active`：当前输入已进入 scheduler；`idle`：本段停止并等待下一输入 | scheduler transition |
| GPU KV block | GPU-resident 或不在 GPU prefix cache | GPU block pool |
| Host KV block | host-backed 或尚无主机副本 | host block pool |
| Transfer | none、prefetch in flight、on-demand reload in flight | connector event + control registry |
| Request ownership | request-owned，或 cached-free 可由 prefix match 复用 | KV cache manager |

GPU-resident 与 host-backed 不是互斥状态：同一个 block 可以同时存在于两处。`active` 也不保证所有历史 blocks 已经 GPU-resident，因为 scheduler admission 后仍可能进行 on-demand reload 或重算。控制 registry 只保存 session activity、prefetch 是否在途/延迟以及时间戳；物理 block 状态始终实时查询 pool。

## Partial KV Eviction

一个 idle 会话在逐出后的 block 视图（block 从旧到新，`F` 为 host-backing frontier）：

```text
              0            K                         F            n
              │            │                         │            │
GPU pool      │████████████│░░░░░░░░░░░░░░░░░░░░░░░░░│████████████│
host pool     │████████████│█████████████████████████│░░░░░░░░░░░░│
next input    │ prefix hit │ prefetch / reload L..R  │ resident   │
```

`[0, K)` 是保留前缀，下次输入直接由 GPU prefix match 命中；`[K, F)` 在 idle 后被逐出且主机已有副本，可在复用前预取或在 admission 后按需回载；`[F, n]` 是 host copy 尚未确认的最新尾部，逐出时作为 margin 保留在 GPU。以下小节分别定义 host 后备前沿的推进、逐出的选择规则和恢复路径。

### Incremental Host Backing

vLLM 的 `SimpleCPUOffloadConnector` 随引擎迭代把已完成 KV blocks 复制到 host block pool。Conveyor 修复 streaming re-entry 下的 store cursor，使复制前沿继续覆盖新增的完整 blocks。由于 copy confirmation 滞后于生成，最新 block 可能尚未 host-backed；系统为此记录 host coverage，而不假定后备总是完整。

### Idle-Session Eviction

当 resumable request 完成本段生成并进入 idle 时，主路径执行：

1. `free(request)` 释放 request 对所有 GPU blocks 的所有权，使仍有 hash 的 blocks 成为 cached-free；
2. 保留最多 \(K\) 个 GPU prefix blocks，并为尚未发出 host copy 的最新尾部保留实现级 margin；
3. 对选定尾块调用 `evict_blocks`，移除其 GPU cache entry；
4. 记录逐出数量、逐出前所有权、GPU pool 变化和其中已有主机副本的数量。

逐出操作当前不会先把目标集合裁剪到 host-backed blocks。若某个逐出块尚无主机副本，下一次恢复在该缺口处退化为重算。这是已知实现限制，不能把“with host backing”读成所有逐出块都已得到恢复保证。

固定尾块模式通过延迟 utility RPC 逐出指定数量，只用于受控实验。retained-prefix 主路径直接挂在 scheduler 的 idle transition 上，不依赖 worker timer。

### On-Demand KV Reload

下一输入进入 scheduler 时，vLLM 按 block hash 先复用仍在 GPU prefix cache 的前缀，再从 host block pool 加载连续命中的缺失 blocks。首个既不 GPU-resident 也不 host-backed 的 gap 之后只能重算。加载中的 request 使用原生 `WAITING_FOR_REMOTE_KVS` 状态；Conveyor 只增加观测，不改该正确性路径。

## KV Prefetching

当 gateway 释放一个会话输入时，worker 可以调用 `prefetch_kv`。EngineCore 实时查询 block pools；若存在 host-backed 的 GPU 缺口且容量闸允许，就在输入 feature extraction 同期发起 host-to-device copy。完成后 blocks 以原 hash 注册到 GPU prefix cache，下一次 scheduler admission 使用普通 prefix match。

合成 transport ID、如何接入 load event 以及 hash registration 都是当前实现选择，不是独立研究机制。若容量不足，prefetch 被延迟到后续 partial eviction 释放空间；若真正输入先到，则取消延迟项并交给 on-demand path。已完成但尚未复用的 prefetched blocks 仍可被 LRU 逐出，因此预取不改变正确性。

## Output Delivery

matched baseline 和 Conveyor 都维护每会话未交付输出缓冲 `st.tokens[st.consumed:]`。差异是：matched baseline 在没有可交付 token 时最多等待配置的 RPC budget，Conveyor 当前只做一次快照并立即返回。如果生成速率长期高于 gateway 消费速率，未交付输出缓冲会持续增长。交付相关字段的诊断语义与禁止解释由 [`Experiments`](experiments.md#measurement-semantics) 持有。

## Initial-Context Preloading

初始上下文预加载（initial-context preloading）是实验状态构造，不是 Conveyor 机制。runner 在开始周期输入前预建指定会话，完成所有 initial-context prefills，并把初始化产生的单个输出 token 从交付游标中跳过。

Conveyor 在该屏障期间暂停 automatic KV eviction。屏障结束时只解除暂停，不立即逐出，因为 host-backing frontier 可能尚未覆盖整个初始上下文；第一次正常周期计算后，scheduler 的 idle transition 再建立 retained-prefix 状态。

## One Session Cycle

单个会话在一个周期内各阶段的先后与重叠如下（示意，不按比例）；各阶段的 artifact 与健康检查见下表。

```text
        r(i,k)                                            r(i,k)+T
          │                                                   │
gateway   █ release + Step RPC                                █ 下一次释放
worker    █ 快照未交付输出并返回，交付语义见 Output Delivery
worker    ├────────┤ feature extraction，线程池跨会话并行
worker    ├─┤ [Conveyor] 发出 prefetch_kv utility RPC
engine      ├────┤ [Conveyor] host 到 GPU 的预取拷贝，与特征提取重叠
engine             ├─┤ scheduler admission + prefix match
engine                ├────┤ on-demand reload L..R，gap 之后改为重算
engine                     ├──────────┤ prefill + decode，每段至多 M token
engine                                ├──┤ host backing B 前沿推进
engine                                    █ [Conveyor] idle 后 partial eviction E
```

| 阶段 | 对象与动作 | 新 artifact | 健康检查 |
| --- | --- | --- | --- |
| Release | gateway 在绝对网格释放会话输入 | `gateway_ticks.log` | 周期不漂移，offset 稳定 |
| Input and output | worker 入队 input chunk，并快照当前未交付输出 | `P`、`deliv` | RPC 不阻塞后续 release slot |
| Feature extraction | input 进入线程池并生成模型特征 | `IQ/IS/IE/IR/IA` | queue、FE、handoff 可分解 |
| Scheduler admission | 新特征追加到 resumable request | scheduler/request events | session ID 连续有效 |
| KV restore | prefix match 后执行 prefetch hit、on-demand reload 或重算 | `L/R`、large prefill | 缺失历史最终恢复 |
| Prefill and decode | 引擎执行当前 input 与最多 \(M\) 个输出 token | `scheduler.log` | 无 session death |
| Host backing | 新完成 blocks 推进 host-backing frontier | `B` in `kv_events.log` | 前沿继续增长 |
| Partial eviction | session idle 后逐出选定 GPU tail | `E` + residency counter | idle prefix 有界、coverage 可审计 |

## Observability Model

新 run 的 artifact 布局与各文件语义如下；解析、时钟对齐与 Perfetto 导出由 `infra/trace/` 离线完成：

```text
results/<experiment>/<run_id>/           # 不可变 run 目录，绝不复用
├── manifest.json                        # 先于一切进程落盘：展开配置、进程 argv、provenance
├── status.json                          # 终态判决：success / failed / interrupted
├── gateway_ticks.log                    # 绝对释放网格、RPC 延迟与实际交付量
├── per_request.log                      # 连接 release、feature extraction 与 admission
├── scheduler.log                        # 引擎调度迭代
├── residency.log                        # 从 GPU pool 采样的逐会话 block 数
├── kv_events.log                        # E 逐出 / B 后备前沿推进 / L 加载发起（按需或预取）/ R 加载完成
├── gpu.csv                              # nvidia-smi 采样
├── client.json                          # client controller 聚合结果
├── *.log                                # 各进程 stdout/stderr
└── derived/timeline.trace.json.gz       # 解析与时钟对齐后导出的 Perfetto timeline
```

Perfetto 只可视化这些已采集事件，不能把相邻 scheduler 调用间隔伪装成精确 GPU kernel 时间。

旧 `results/` 中的历史 artifact 仍由其产生时的 commit 和 schema 解释；新 parser 不用废弃术语为旧日志维持第二套当前语义。
