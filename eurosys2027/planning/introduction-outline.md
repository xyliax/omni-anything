# Six-Paragraph Introduction Contract

本文件只规定 Introduction 的逻辑与段落职责，不是英文成稿。所有表述均为 provisional；论文类型、closest-work gap、SLO 和结果仍需冻结。

## Type Positioning

- Candidate type: **New Problem/Setting Paper**，以 systems technique 作为构造性解决方案。
- Rationale: 最强主线是长期周期性交互会话形成新的 KV capacity regime；Conveyor 证明 next-use information 可以被系统利用。
- Condition: closest-work matrix 完成后才能冻结。若已有工作覆盖同一 setting，应改为 Technique Paper。
- Paragraph implication: Paragraph 3 是承重段，必须清楚定义 setting、hard constraints 和 goal，不能只作为引入 Conveyor 的过渡句。

## Running Example Candidates

| Candidate | Evidence proximity | Benefit | Risk | Current choice |
| --- | --- | --- | --- | --- |
| 长期交互助手 session，具体 input/output modality 与 user-visible delivery path 待定 | Open | 直接展示长期 session、增量更新、上下文复用与 KV 增长 | 必须与最终 end-to-end evaluation 对齐 | Open |
| Continuous captioning/meeting assistant sessions | Open | 容易解释周期输入、长期上下文与增量交付 | 产品 cadence、输出路径和 QoE 指标尚未冻结 | Open |
| Interactive multimodal/video assistant sessions | Open | 直观展示长期 streaming context | 必须由最终模型与 workload matrix 支持 | Open |

当前不设置 provisional default。最终 running example 需要在实验矩阵和 Figure 1 的 formal motivating evidence 冻结后由用户确认，并在 Section 2、Design walkthrough 和 Evaluation 中复用。

## Paragraph 1 — Background and Motivation

**Purpose:** 从有限 request/response 转向长期 streaming interaction session，并用一个具体失败展示 growing KV working set 为什么成为 serving 问题。

**Writing points:**

1. 先描述持续追加输入、复用历史状态的交互 workload，不先介绍 Conveyor。
2. 实验矩阵冻结后再选择具体 running example；不得把当前原型的 modality、output path 或 hardware 提前写成论文边界。
3. 对比每周期计算需求与长期 KV residency，提出 capacity-before-compute 的可能 regime。
4. 说明系统受益对象是需要在固定资源预算上维持更多长期会话的 serving operator；modality-specific QoE 只在最终 end-to-end path 实测后表述。
5. 用 Figure 1 的 baseline failure 和 idle interval 结束该段。

**Gaps:**

- MAJOR：需要 3–5 个最新系统、模型或部署来源证明该 workload 的现实性。
- MAJOR：running example 的正式 motivating point 尚需 clean evidence。
- MAJOR：running example、output delivery 和 QoE 口径必须与最终实验矩阵共同冻结。

## Paragraph 2 — Limitations of Existing Work

**Purpose:** 用不超过三项 capability gap 说明现有 request-centric control 和粗粒度 KV 管理为何没有利用该 setting。

**Writing points:**

1. Request-centric serving 根据当前 arrivals、batch 和 cache match 做决策，但不直接表达长期 session 的预计 next use。
2. Full GPU residency 受 growing working set 的 capacity 限制；完整 recomputation 把随 context 增长的 prefill 放回下一次更新路径。
3. Pure on-demand reload 在 input 到达后才恢复，并可能让同步 session 形成瞬时 restore demand。

**Gaps:**

- MAJOR：每项 limitation 必须绑定 named closest work，而不是只比较抽象 capability。
- MAJOR：尚未证明 Metronome 是唯一或最强 baseline。

## Paragraph 3 — Problem Essence and Goal

**Purpose:** 定义 periodic interaction serving 的核心资源矛盾、hard constraints 和单一研究目标。

**Hard constraints:**

- 保留完整逻辑上下文，不以有损截断换取容量。
- 维持每会话周期与预先冻结的 per-period service target。
- 同时核算 GPU KV capacity、period compute、HBM effects 和 host-device restore bandwidth。
- 超过总资源 frontier 时仍需要 admission control；机制不消除物理上限。

**Goal sentence candidate:**

> Increase the schedulable concurrency of long-lived periodic interaction sessions by exploiting predictable next-use times to manage GPU KV residency, without truncating context or blindly moving restoration onto the next update's critical path.

**Writing points:**

1. 区分 application release、service RPC 和 engine iteration。
2. 把 predictable next use 写成 setting 提供的信息，而不是 release-offset scheduling 创造的资源。
3. 把 capacity/compute/restore-bandwidth frontier 作为 claim 的条件，而不是事后解释失败的附加模型。

**Gaps:**

- CRITICAL for final paper：`schedulable concurrency` 和论文级 latency/freshness 尚未冻结 operational definition。
- MAJOR：resource frontier 尚未完成 primitive calibration 和跨 profile 验证。

## Paragraph 4 — Key Challenges

**Purpose:** 给出三个由 goal 自然导出的障碍，并解释直接方法为什么失败。

**Writing points:**

1. **Demand shaping:** 分散 releases 可能缓解瞬时 demand，但也可能削弱 batching、增加权重读取；不能假设 staggering 免费。
2. **Safe partial residency:** session activity、request ownership、GPU residency、host coverage 和 in-flight transfer 是不同状态；粗粒度 free/offload 不能保证可恢复性。
3. **Timely restoration:** prefetch 可能因 capacity 被推迟、因 input overtaking 变迟或在复用前被 LRU 逐出；正确性不能依赖 prefetch 必定命中。

**Gaps:**

- MINOR：正式措辞需在 resource model 和 ablation plan 冻结后压缩。

## Paragraph 5 — Solution Overview

**Purpose:** 给出一个统一的 next-use-aware KV residency design，并把三个挑战一一映射到三个模块。

**Challenge-to-module mapping:**

- Demand shaping → release-offset scheduling。
- Safe partial residency → incremental host backing + idle-transition partial KV eviction。
- Timely restoration → capacity-aware KV prefetch + on-demand reload/recompute fallback。

**Writing points:**

1. Topic sentence 必须先写统一设计原则，再列机制。
2. 在 provisional running example 中复用同一 session timeline：release、compute、idle eviction、restore、next reuse。
3. 明确 release offsets 不创造 idle interval，prefetch 也不承担 correctness。
4. Forward-reference Section 3 的模块和 Section 4 的实现边界。

**Gaps:**

- MAJOR：release offsets 的 restore-bandwidth benefit 与 prefetch 的稳定净收益仍需 formal evidence；最终 overview 必须与结果一致。

## Paragraph 6 — Contributions

**Purpose:** 只列三项可由具体章节交付的贡献，并把经验贡献保留为无数字 placeholder。

1. `<periodic-interaction capacity regime and resource formulation>`（Section 2；pending novelty and model validation）。
2. `<next-use-aware Conveyor design with demand shaping, partial residency, and safe restoration>`（Sections 3–4；pending final mechanism wording）。
3. `<matched empirical characterization of schedulable concurrency, latency cost, mechanism attribution, and resource-frontier validity>`（Sections 5–6；pending formal evidence）。

**Gaps:**

- CRITICAL for final paper：Contribution 3 尚未交付，不能添加倍数或 headline result。
- MAJOR：Contribution 1 是否是新 setting 依赖 closest-work audit。

## Flowchart Consistency

| Check | Structural status | Readiness note |
| --- | --- | --- |
| Running-example loop | Open | No default is selected before the experimental matrix and formal motivating point are frozen |
| Limitations → challenges | Pass | Named prior-work citations missing |
| Goal → contribution 1 | Pass provisionally | New-setting novelty not frozen |
| Challenges → modules | Pass | One-to-one mapping established |
| Modules → contributions | Pass structurally | Contribution 3 lacks formal evidence |
| Contribution → section | Pass | Section numbers assigned |

## Integrity Result

The outline is **needs user attention**, not complete. Its causal chain is structurally coherent, but final-paper integrity is blocked by the schedulability definition, closest-work novelty audit, calibrated resource model and formal empirical contribution.

## Severity Summary

- 2 CRITICAL-for-final-paper gaps: metric definition and undelivered empirical contribution.
- 8 MAJOR gaps: deployment citations, motivating evidence, running-example/evaluation alignment, named closest work, baseline coverage, resource-model validation, mechanism performance evidence, and new-setting novelty.
- 1 MINOR gap: challenge wording compression.

Top actions before prose expansion:

1. Freeze the paper contract and schedulability definition.
2. Complete the closest-work matrix and confirm the running example.
3. Pre-register the decisive experiment and mechanism-to-ablation map.
