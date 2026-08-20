# Problem

## Thesis

全双工语音 serving 的首要稀缺资源是 KV capacity，而不一定是算力。每个活跃会话都以固定周期追加 context，并要求在下一个播放 deadline 前产出一帧；KV working set 持续增长、每个 tick 都参与 attention。默认引擎因此可能在计算仍有显著余量时先撞上 KV pool 的容量墙。

本项目研究如何利用 tick 内可预测的空隙和闲置 PCIe 带宽，在不截断上下文的前提下扩展可调度并发数，并最终容纳 delay-tolerant 的后台 agent 结果注入。当前量化证据与限制只在 [`Findings`](findings.md) 维护。

这里的 capacity-bound 指“可分配 KV 容量先耗尽”，不是 bandwidth-bound 意义上的 memory-bound；两者不能混用。

## Workload Model

### Abstract Tick

双工会话是一条持续的双向音频流，没有离散的 request-response 边界。服务侧把流离散成固定长度为 `T` 的切片，一个周期称为 tick。每到边界，每路活跃会话必须：

1. 对刚结束的输入切片做 feature extraction 与增量 prefill；
2. 续写该会话的持久 context；
3. 生成下一播放片所需的 delivery quota；
4. 在本周期 deadline 内完成，否则产生静音、陈旧内容或其他用户可闻错误。

引擎本身不知道 tick、相位或 deadline；这些语义由 gateway 和 worker 在普通 continuous batching 接口之外塑形。这种结构性信息缺失是默认调度失效的共同根源。

### Configuration Domains

项目同时讨论三个配置域，数字不得跨域混用：

| 配置域 | 作用 | 权威定义 |
| --- | --- | --- |
| 抽象模型 | 用 `T`、delivery quota 和 session 数 `N` 推导机制与边界 | 本文 |
| 实测栈 | 本仓锁定真机 profile 的问题实例；model、runtime 与 device 不在此复制 | [`Experiments`](experiments.md#configuration-domains) |
| 论文配置 | 文本代理双工、较短 tick 与不同 KV 几何的论文外推 | [`Experiments`](experiments.md#configuration-domains) |

delivery quota、baseline 实际每段生成量和 conveyor 实际每段生成量是三个不同概念；精确口径由 [`Experiments`](experiments.md#configuration-domains) 唯一持有。

### Required Properties

| 属性 | 定义 | 删除该属性后 |
| --- | --- | --- |
| 硬 tick 前台 | 固定周期 `T` 的 inelastic deadline frame；miss 是正确性事故 | 普通对话 serving |
| 弹性注入 | 数百到数千 token 的后台 tool/agent 结果；允许延迟，且可能因用户打断作废 | 纯双工锁步 |
| 单 GPU 并发 | `N` 是要最大化的 schedulable concurrency，而不是固定输入 | 单会话工程问题 |

本项目的目标负载要求三者同时存在。当前可执行主路径已经覆盖 full-duplex foreground 和 KV capacity 机制；injection 的联合端到端协议仍待接入，不能把冻结的 injection 先验误写成当前 runner 已经执行的负载。

## Empirical Motivation

### Capacity Before Compute

baseline 真机已经观察到 KV pool 饱和后出现 head-of-line blocking、preemption cascade 和 admission deadlock；被抢占会话还可能无法重新进入调度。与此同时，capacity-bound 区域仍保留显著计算余量。具体失效形态和数字见 [FINDING-A3](findings.md#finding-a3)、[FINDING-A5](findings.md#finding-a5) 与 [FINDING-D1](findings.md#finding-d1)。

host-dependent 的 feature extraction 拥堵也曾限制并发，但它可以通过正确的并行 ingest 修复，因此属于必须排除的工程瓶颈，不是本研究要主张的结构性瓶颈；见 [FINDING-A1](findings.md#finding-a1) 与 [FINDING-A2](findings.md#finding-a2)。

### Phase Is a Resource

不同会话在周期内的相位决定它们是否同步争用 feature extraction、KV residency 和计算窗口。默认 work-conserving 调度只响应到达，不把相位作为可分配资源；同步到达还会把原本可以分散的工作重新聚合。相位与 residency 的关系见 [FINDING-D3](findings.md#finding-d3)。

### Injection Conflicts With the Deadline

大段 injection prefill 如果作为普通引擎 step 执行，会与硬 tick 前台竞争同一个不可抢占计算区间。最坏影响由 injection 到达相位决定；单纯 chunking 仍会占用前台引擎步，并可能重复支付固定开销。

因此 injection 不能只被视为“更长的一次前台请求”。设计必须显式表达它的可延性、大小和 deadline 关系。

### Cancellation Has No Engine Semantics

用户打断意味着未提交的后台结果已经作废，但默认引擎只看 token 和 block，不知道应用层 cancellation。若作废 KV 继续 resident，它既浪费 capacity，也可能被错误拼接进后续上下文。系统需要明确的 commit/cancel 状态和可回收边界。

## Structural Information Gap

系统真正需要的四类信息在物理上都可得，却没有进入普通请求模型：

| 缺失字段 | 必须做出的决策 | 默认行为 | 后果 |
| --- | --- | --- | --- |
| per-session deadline 与 phase | 谁占用周期内哪个子槽 | 按偶然到达组成 batch | 惊群与不可控 batch |
| KV 的预计下次使用时刻 | 何时回收、搬回和认领（claim） | LRU 或重算 | 逐出马上要用的内容 |
| injection 的可延性与大小 | 放进哪个安全窗口 | 与普通请求同等调度 | 挤占硬 tick |
| cancellation / commit | 哪些 KV 仍有语义价值 | 所有 KV 同等常驻 | stale residency 与错误拼接 |

这不是继续调几个 scheduler 参数就能消除的问题，而是需要 gateway、worker、引擎状态和观测共同补齐信息面。当前系统如何补齐这些语义见 [`System`](system.md)。

## Feasible Region

系统存在三个依次可能成为主导的边界：

- **Capacity boundary**：KV pool 字节数除以单路 working set；当前消费卡实测首先触达。
- **Deadline boundary**：当 residency 受到控制后，单周期内可完成的前台工作成为约束。
- **Injection boundary**：前台与后台总计算需求填满周期后，需要 admission control，而不是继续依赖调度优化。

本项目研究瓶颈以内的 capacity 与 scheduling；超过生产能力后的 admission control 是边界条件，不是机制失败。

## Observability Gap

双工通道没有天然的请求完成事件，静音帧也可能是合法输出。cadence、frame delivery 和 transport latency 因而可能全部正常，而模型内容已经停止更新或严重陈旧。容量决策不能只看 client miss 和 GPU utilization，必须同时观察：

- content freshness；
- engine starvation 与 queue state；
- per-session residency；
- 生成速率与交付库存是否配平；
- tick、ingest、prefill、decode、KV 驻留变化和回载的同轴时序。

这一 silent-failure 结论见 [FINDING-B1](findings.md#finding-b1) 与 [FINDING-B2](findings.md#finding-b2)。观测如何覆盖完整周期见 [`System`](system.md#observability-model)。

## Research Context

Metronome 是本项目 baseline 的直接方法与代码来源之一，并独立观察到 memory cliff 先于 compute saturation。它研究纯 full-duplex 负载，并以 sliding window 和 admission control 处理边界；本项目增加 elastic injection、cancellation 语义和无损 residency 扩展。baseline 角色、pin 纪律和可引用数字统一写在 [`Experiments`](experiments.md#metronome-baseline)。

当前公开 full-duplex serving 工作仍很少；模型层常以有限上下文或有损窗口规避 KV 无界增长，产品侧实现通常闭源。外部材料原文与时效性整理保存在 `.context/references/`，不构成本项目事实。

## Scope

本项目不研究语音合成头和 audio tokenization，不把多卡 prefill/decode 分离作为贡献，也不覆盖极短锁步帧家族。超过系统总产能后的 admission control 属正交问题。任何模拟器或线性外推只用于解释边界，主系统结论必须回到真机证据，并在 finding 中明确配置域。
