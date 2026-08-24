# Experiments

## Evaluation Readiness

当前仓库可以运行 Upstream Metronome、matched Metronome baseline 和 Conveyor，但还不能直接写论文 Evaluation。最重要的阻塞项是 matched baseline 每段配置的 decode cap 为 \(M+8\)，而 Conveyor 为 \(M\)。两者接收相同 offered input，当前却不执行相同 decode work。正式比较必须在独立实验事务中统一该行为、保留新 manifest，并重新运行全部论文数据；本次术语清理不静默改变已有执行结果。

当前 Qwen2.5-Omni runner 只产生 Thinker 文本 token，不含 Talker、Code2Wav 或 PCM 输出。因此以下 output cap 与交付计数都是 serving-harness 变量，不能解释为音频播放率或最低媒体交付要求。

## Configuration Domains

项目区分三个配置域：

| 配置域 | 用途 | 证据地位 |
| --- | --- | --- |
| Abstract Model | 使用 \(T,D,M,N,K\) 表达周期、延迟目标、输出上限、会话数和保留前缀 | 问题与资源模型 |
| Measured Stack | 本仓锁定模型、runtime、device 和 client 的真机实例 | 当前可运行、结论必须带域限定 |
| Analytical Reference Scenario | 用于多资源 roofline 或外部硬件 profile 的参数场景 | 只有校准与验证后才能支持外推 |

Analytical Reference Scenario 不因计划写入论文就自动成为实测配置。线性外推必须明确标为推导，不能称作已经验证的 roofline。

### Measured Stack

| 参数 | 当前值 |
| --- | --- |
| 模型 | Qwen2.5-Omni-7B |
| 执行路径 | Thinker text only |
| 运行时 | vLLM 0.23 |
| 设备 | RTX 3090, 24 GiB, PCIe Gen3 |

model revision、依赖锁和 GPU index 仍以 executable config 与 run manifest 为准；表中设备是当前证据域，不是系统成立的硬件要求。

### Measured Workload

| 参数 | 当前值 | 语义 |
| --- | --- | --- |
| 周期 \(T\) | 2000 ms | 同一会话相邻两次应用级 release 的间隔 |
| 默认会话数 | 8 | 单个 run 的默认并发点，不是容量结论 |
| run horizon | 600 s | 默认持续时间 |
| 输入块 | 20 ms PCM chunks，由 client 在一个周期内累计 | offered input |
| 每周期输出 token 上限 \(M\) | 25 | harness cap 和 gateway consumption limit，不是最低交付量 |
| measured context growth | 78 token/period | 当前栈标定值，用于容量模型，不驱动 client |
| 单 token KV bytes | 56 KiB | 当前模型和精度下的几何 |

这些值由 `experiments/shared/workload.py`、`model.py` 与 `platform.py` 单份持有。文档测试校验表格与代码一致。

### Executed Decode Difference

| Evaluated system | offered input | gateway consumption cap | worker per-segment decode cap | 当前比较资格 |
| --- | --- | --- | --- | --- |
| Upstream Metronome | 当前音频输入 | \(M\) | 上游行为 | 参考，不作主要公平对比 |
| matched Metronome baseline | 与 Conveyor 同源 | \(M\) | \(M+8\) | 不合格；需修复并重跑 |
| Conveyor | 与 matched baseline 同源 | \(M\) | \(M\) | 可做机制诊断，暂不可作最终跨系统结论 |

两个当前 first-party worker 都设置 `ignore_eos=True`。因此在正常 measured path 上，生成不会因 EOS 提前结束：matched Metronome baseline 运行到每段 \(M+8\) 的 cap，Conveyor 运行到每段 \(M\) 的 cap；只有 model-length 边界或异常终止等例外会提前结束。33-vs-25 的差异会改变 decode work，并可能造成未交付输出 backlog，不能只把它描述为交付层的小误差。这个 harness 不提供模型自然短输出或 learned silent-token behavior 的证据。

## Evaluated Systems

### Upstream Metronome

Upstream Metronome 是 `third_party/metronome/` 的只读 pin，保留其原始 gateway 与 worker。它提供方法和代码来源映射，但 host-side input processing、观测字段和 runtime 行为与 Conveyor 不完全匹配。

### Matched Metronome Baseline

`experiments/baseline` 的默认 `paringest` 配置是正式对比候选。它保留 Metronome 的 resumable request 和默认 GPU KV residency，只修复 host-side input processing、initial-context 场景下冻结的 `session.max_tokens`，并接入共同 observation producer。`vanilla` 和 `paringest` 是 artifact/implementation identifiers，不是论文中的两个系统贡献。

### Conveyor

Conveyor 的可执行配置包含以下研究开关和实现控制：

| 配置 | 类型 | 当前接口 |
| --- | --- | --- |
| release-offset scheduling | research mechanism | gateway `--slots` |
| partial KV eviction, fixed-tail mode | mechanism experiment | `--evict-tail-blocks` |
| partial KV eviction, retained-prefix mode | main mechanism configuration | `--retained-prefix-blocks` |
| KV prefetching | research mechanism candidate | `--prefetch push` |
| synchronous scheduling | matched-control requirement for current eviction implementation | `sync_scheduling` |
| no-wait `Step` | implementation choice | Conveyor worker behavior |

KV eviction 当前要求 synchronous scheduling，以避免 speculative engine iteration 与 block free 竞态。评估逐出机制时，control configuration 必须钉住相同 scheduling mode；否则一次比较同时改变两项因素。

## Initial-Context Preloading

`--initial-context-tokens` 在测量前为每个 session 构造指定长度的 context，用于把 context length 变成可控实验变量。全部 initial-context prefills 完成后 runner 才开始周期输入；初始化产生的单 token 不进入输出交付缓冲。

Conveyor 在 initialization barrier 期间暂停 automatic KV eviction，并在 barrier 结束时只解除暂停。matched baseline 使用独立 engine fix 刷新后续 segment 的 `session.max_tokens`。任何 `initialization barrier timed out` 日志都使 run validation 失败。

这项设置是 workload state construction，不是研究机制。论文实验应报告 initial context length，而不是把它写成系统设计。

## Measurement Semantics

### Repository Health Gates

以下条件可以直接判定 run 无法作为证据：

- process、worker session 或 service RPC 出错；
- client 没有收到周期事件，或 client artifact 报错；
- initialization barrier 超时；
- manifest、required artifact、hash 或 terminal status 不完整；
- 启用 KV eviction 或 prefetch 却没有对应 `E` 或 `L trigger=prefetch` 事件；
- 日志语法损坏，无法解析实际交付量或时序。

### Implementation Diagnostics

以下字段只用于诊断，不能单独充当论文 correctness 或 QoE gate：

| 字段 | 当前含义 | 禁止解释 |
| --- | --- | --- |
| protobuf `tokens_per_tick` / internal `tpt` | 继承的 wire identifier，项目把它解释为 output cap \(M\) | 每周期必须交付的 token 数 |
| `deadline_met` | Upstream Metronome 与 Conveyor 当前含义不同；Conveyor 仅表示 service RPC 是否在 period 内返回 | 模型响应完成、音频未卡顿 |
| `deliv` | 某次 release 实际从未交付输出缓冲取出的 token 数；可以为 0 到 \(M\)，且不等于 \(m_{i,k}\) | 单独等于 content freshness，或归属于当前输入 |
| `output_backlog` | 已生成未交付 token 数 | 固定阈值即论文 SLO |
| `gpu_ms` | worker 返回的实现字段；无等待 Conveyor 路径不包含本次 GPU 工作 | 统一的端到端 latency |
| large prefill | 可能发生重算的诊断指纹 | 未结合 host coverage 就证明 reload 失败 |

单次 `deliv` 少于 \(M\) 不再使 run 自动失败。当前实现中的低交付可能来自启动期尚无可消费输出、缓冲时序、服务落后、异常终止或 malformed execution；它不能作为当前 harness 已观察到自然短输出或 learned silence 的证据。论文级 latency、freshness、jitter-buffer stall 与最大可调度并发的 operational definitions 仍待 evaluation design 确定。

## Planned EuroSys Evaluation

正式 Evaluation 建议围绕六个 reviewer question 组织；每个问题对应一个主图或表，而不是按代码模块罗列 microbenchmark。

### Q1: Does KV Capacity Limit Concurrency Before Compute?

- 在统一 decode cap 后，对 matched baseline 扫描 \(N\) 与 context length；
- 同时报告 GPU KV occupancy、每周期 busy time、SM utilization、HBM bandwidth、queue state 和 session liveness；
- 展示容量边界出现时仍有多少 compute headroom；
- 将 host-side feature extraction 隔离，避免把工程拥堵误归因于 KV capacity。

主结果应是 capacity frontier，而不是某个 baseline 队列故障的复现。

### Q2: How Much Concurrency Does Conveyor Recover?

- 在同模型、输入、decode cap、scheduler mode 和 observation 下扫描 \(N\)；
- 报告 matched baseline 与 Conveyor 的可持续区间、GPU KV occupancy 和每会话 GPU-resident blocks；
- 同时报告 host memory footprint、H2D/D2H bytes 和 context-length sensitivity；
- 分开给出测量区间与资源模型预测，不用短 run 线性外推代替稳定性实验。

最大可调度并发的正式 gate 必须在 latency/QoE 指标确定后再冻结。

### Q3: What Is the Latency Cost of Capacity Expansion?

- 从 input release 分解 feature extraction、scheduler admission、on-demand reload、prefill 和 decode；
- 报告每会话分布和 tail，而不仅是聚合均值；
- 对 context length、retained prefix \(K\) 和 session count 做敏感性分析；
- 若加入完整音频输出链，再报告 jitter-buffer consumption 或 playback stall；当前 Thinker-only 路径不得代报。

### Q4: Which Mechanism Provides Which Benefit?

采用正交消融：

1. matched baseline；
2. 仅 release offsets；
3. release offsets + host backing + partial eviction；
4. 加 KV prefetch；
5. retained-prefix \(K\) sweep；
6. matched synchronous-scheduling control。

release offsets 的 input-processing 收益与 restore-bandwidth 平滑收益要分别测量；后者不能只由机制直觉推断。

### Q5: Does the Resource Model Generalize?

- 标定 KV bytes/token、decode/prefill compute、HBM traffic 和 PCIe copy throughput；
- 用这些 primitive 构建 capacity / compute / restore-bandwidth roofline；
- 在至少一个额外 GPU 或不同互连 profile 上验证预测误差；
- 清楚区分实测点、模拟器标定和 analytical scenario。

### Q6: What Are the Overheads and Failure Boundaries?

- host-backing CPU memory 与 D2H overhead；
- partial eviction 和 prefix-match bookkeeping overhead；
- prefetch 的命中、迟到、capacity deferral 和 LRU eviction；
- host coverage 缺口引发的 recomputation；
- 长时间稳定性、context-length limit、session churn 和异常路径。

## Run Protocol

每个正式数据点至少要求：

1. clean source 和唯一 commit；
2. fresh worker、固定 model revision 和环境 profile；
3. 完整 manifest，记录 expanded config；
4. 足够长的 steady-state window，排除 warmup 与 initialization；
5. 重复运行、方差或置信区间；
6. 成功的 terminal `status.json` 和全部 required artifact hashes；
7. finding card 明确配置域、指标定义、样本数和限制。

成功进程退出不等于成功 run；验证规则由 runner 和 `results/README.md` 执行。

## Evidence Acceptance

论文主结果只能使用 clean-source formal evidence。dirty run 可用于诊断，但必须保留可重建 patch artifact；缺少原始 artifact 的历史数字只能标为 legacy-unreconstructable，不能在新图中伪装为可复算结果。

旧 `results/` 与旧 manifest 使用产生它们时的 schema，不改写。新 run 使用 `kv_events.log`、`initial_context_tokens`、`output_token_cap`、`retained_prefix_blocks` 等当前接口。
