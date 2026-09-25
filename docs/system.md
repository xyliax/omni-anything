# 系统设计：周期 KV 驻留与恢复

<a id="design-goals"></a>
## 设计目标

Pilarius 的目标是通过安排会话 phase、部分 KV 逐出和下一周期前的恢复，降低 GPU 峰值驻留并扩展可承载会话数。本文描述设计及其约束，具体预算算法仍待确定。已验证的内容见[已有证据](findings.md#current-state)。

<a id="logical-architecture"></a>
Pilarius 位于推理引擎之上，负责跨周期的会话推进与 KV 驻留管理。当前设计图将 planner、session manager、KV memory manager 和 KV transfer engine 画为 Pilarius 内的四个逻辑组件，并单独呈现下层 inference backend。组件边界描述职责，不规定进程数、通信协议或已有同名代码模块。

| 逻辑组件 | 拥有的决策与状态 | 输入与输出 |
| --- | --- | --- |
| Residency planner | 准入可行性、group assignment、eviction budgets 与 restoration timing；负责 admission planning 和低频 plan revision | 根据会话需求和资源状态产生 residency plan；不逐周期重新选择全部预算 |
| Session manager | 会话与组的周期进度、下一 tick 与计划中的恢复顺序；承接周期调度职责 | 消费 plan、执行事件与 KV readiness；请求 KV 准备或回收，并在满足周期与就绪条件时向后端提交工作 |
| KV memory manager | KV 映射、有效副本与安全操作条件；与后端的块分配及引用状态协调 | 按预算安全释放或完整分配本次恢复目标，为新增 KV 发起增量备份；提交具备源和目标的复制请求，消费完成事件并发布有效状态与 readiness |
| KV transfer engine | 已提交复制的排队、在途与完成事件；负责异步复制执行 | 执行 incremental host backing (D2H) 与 scheduled KV restoration (H2D)，保持依赖和顺序，向内存管理器报告完成或失败 |
| Inference backend（Pilarius 外部） | 请求执行调度与模型计算；若使用 batching，其策略也归后端 | 接收已满足提交条件的工作，按自身策略执行；提供执行事件以及 KV 分配、引用和就绪状态的对接能力 |

Residency plan 由 planner 产生、session manager 执行。周期调度与运行状态由相应组件维护；组件间请求和反馈的含义见[接口契约](#component-interface-contracts)。

异步备份不自动释放 GPU 空间，复制完成后须发布有效状态，KV 就绪后仍须等待执行条件。恢复采用逐 session 完整目标分配与逐 session 就绪，选择理由及代价见[恢复分配决策](#group-restoration-allocation)。本节描述所选设计，不表示实现或性能已经验证。

<a id="inference-backend-boundary"></a>
### 推理后端边界

Pilarius 调节周期请求何时具备提交条件及其历史 KV 的驻留安排；推理后端负责请求执行调度与模型执行；使用 batching 时，其 batch 组织也由后端负责。Continuous batching 不是后端必须采用的固定策略。session group 是 phase 与驻留调度对象，不是强制一起执行的 batch。Pilarius 改变可提交工作的时间可能影响后端形成的 batch，但不因此拥有后端的组 batch 策略。设计图的 Compute 颜色表示活动阶段，不保证相关 session 或 group 同时执行。

Inference backend 以可替换的职责边界呈现；具体运行时与当前实现覆盖分别见[实验配置](experiments.md)及[实现核验边界](findings.md#implementation-audit-boundaries)。可替换性要求后端支持请求提交、执行完成事件，以及 KV 身份、有效性、引用、目标分配、安全释放和复制完成的协调。仅有文本生成 API 不足以实现该对接；图示不宣称已支持多个后端，也不宣称可无改动替换。KV memory manager 是驻留决策与后端资源操作的协调职责，不表示复制另一套物理块分配器；实际分配与引用状态须保持一致的权威来源。

<a id="component-interface-contracts"></a>
### 组件接口与事件语义

以下是待实现和验证的逻辑契约；调用方式、类名、进程边界和字段编码由实现决定。设计图省略的错误反馈及生命周期事件仍须处理。

| 图中标签／逻辑交互 | 方向 | 必须表达的语义 |
| --- | --- | --- |
| Residency plan | Planner → Session manager | 会话与 group/phase 的关系、逐会话逐出预算、恢复时机及所用最大上下文配置。运行期消费带版本的计划，不默认逐周期重新求解 |
| Evict / Restore | Session manager → KV memory manager | 针对具体会话和逻辑 KV 范围请求逐出或恢复，受当前计划、预算和时机约束；这是两个操作，箭头不表示接收请求就立即执行成功 |
| Transfer requests | KV memory manager → KV transfer engine | 已确定的 D2H/H2D 方向、源与目标、逻辑范围和依赖；提交前保证源有效、目标已分配并保护复制引用 |
| Transfer completion（图中省略） | KV transfer engine → KV memory manager | 指定传输已成功完成；仅提交、排队或启动均不构成完成。失败应作为失败结果报告，不得伪装成功 |
| KV readiness（图中省略） | KV memory manager → Session manager | 对应会话本次执行所需 KV 范围已在 GPU 上有效；内存管理器应先核验身份、范围与完成状态并发布有效内容，再通知就绪。局部复制完成不自动形成整体 readiness |
| Requests（图中省略） | Session manager → Inference backend | 满足周期提交条件且所需 KV 就绪的执行工作；携带会话历史和本次输入的关联，不强制后端按 session group 组 batch |
| Request state | Inference backend → Session manager | 返回指定会话本次请求的执行进度、完成或失败状态，供更新周期进度并判断后续驻留操作；计算完成不代表所有 KV 引用已解除。后端自己组织 batch 并推进执行 step，不要求 session manager 逐 step 发起执行；状态通知粒度由对接协议确定 |
| Allocate / Free | KV memory manager → Inference backend | 请求分配恢复所需的 GPU 目标或安全释放已有 GPU 块；通过后端分配与引用权威状态执行，不能绕过在途使用条件 |
| Block state | Inference backend → KV memory manager | 返回块映射、实际分配与可用空间、有效范围及执行/共享/复制引用状态，并报告相应操作结果。计算结束不直接替代这些状态检查；不维护互相矛盾的影子分配状态 |
| 运行反馈（图中省略） | Session manager → Planner | 会话变化、实际资源需求及计划风险，供按需修正；不意味着每个 tick 都产生新计划 |

事件与请求至少须能关联到正确会话、逻辑 KV 范围及本次操作，避免取消、重复请求、计划修正或空间复用后，旧完成事件更新新的状态。计划使用单调递增版本，操作保留创建时的版本及独立身份；具体字段编码与去重实现可替换。切换规则见[规划与修正](#planning-updates)，旧版本完成事件仍须完成资源结算，不能仅因版本过期而丢弃。

新增 KV 的 incremental host backing 由 memory manager 根据可复制范围发起，成功完成后才扩展有效 host coverage。图中 Evict / Restore 只简写周期驻留操作，不涵盖或取代这条增量备份路径。恢复启动遇到空间或服务不足时返回阻塞状态，不发布 readiness；重试和过载处理遵循[恢复分配决策](#group-restoration-allocation)与[规划与修正](#planning-updates)。

<a id="figure-semantics"></a>
### 设计图的编码含义

- **左侧位置列**：CPU 对应四个组件的主机端管理逻辑，CPU + GPU 对应推理后端的调度与设备计算，GPU memory 对应各 session 的设备驻留 KV，PCIe link 对应示例中的主机—设备复制路径，Host memory 对应共享备份池。这是图示部署的定位说明，不将硬件或互连类型冻结为论文范围；transfer engine 的 CPU 逻辑负责提交和跟踪复制，不表示数据搬运本身由 CPU 逐字节执行。
- **细灰色实线箭头**：逻辑请求或状态反馈，按箭头方向和标签区分；不再用虚线编码反馈，也不表示同步调用。仅保留 backend → session manager 的单向 Request state，表达请求执行状态反馈；后端自行组织 batch 和推进执行 step，图中省略请求提交／可执行条件对接，不删除 KV readiness 与执行条件约束。backend → memory manager 的 Block state 保留独立反馈。
- **省略的反馈**：Transfer completion、KV readiness 与 planner 的运行反馈从总览图中省略以减少连线；[接口契约](#component-interface-contracts)和[运行流程](#operational-flow)仍要求这些交互，代码不得据图省掉它们。
- **彩色实线箭头**：实际 KV 复制方向。多个蓝色细箭头表示计算期间分批进行的 incremental host backing (D2H)，适用于所有正在产生新增 KV 的会话；当前快照的 A、B 均在计算，因此均绘制多个箭头。紫色粗箭头表示按计划执行的 scheduled KV restoration (H2D)。线宽区分后台增量镜像与集中恢复，不表示实测带宽或规定固定速率；两个方向均可异步执行。
- **Group state（组框与转盘）**：蓝色 Compute、紫色 Restoring、灰色 Waiting。灰色表示该组本轮计算已结束、仍有 session 的所需 KV 尚未恢复，等待计划时机或资源；不表示已就绪等待 tick，不表示 H2D 链路或整个 GPU 空闲。
- **H2D link（右侧活动条）**：紫色 Transfer 表示正在为字母所指的组传输 KV，与转盘中同一组的紫色恢复状态相对应；白色 No H2D 表示没有 H2D 复制在运行。此时 D2H 或计算仍可能运行。白色链路空档与灰色组等待不是同一状态，分别设置图例；瞬时组状态与时间区间活动也不是同一量。
- **Session 与 KV 小块**：每个 group 内保留两个独立的 session 内框，省略 s1/s2 名字以容纳更多块；实心块表示驻留有效状态，带纹理块表示恢复中的范围，空心块表示缺失。块数与组数均为示意，不是固定配置或容量比例。
- **Planner 图标**：显存占用随时间变化的示意轮廓及容量上界，表示驻留规划同时考虑时机与空间；不是实测曲线，也不代表已选定求解算法。正式名称是 Residency planner。
- **转盘与活动条**：扇区身份固定，恢复状态按 C → D → A → B 变化；间隙表示 No H2D。比例不代表实测持续时间、吞吐或利用率；转盘省略提前就绪等待 tick 的阶段，不是完整状态机。

图中 Inference Engine 对应本文的 inference backend 职责。按作者确认的后端选择，展示 vLLM-Omni 标识；右侧以 `AsyncLLM.generate()`、`StreamingInput` 与内部请求标记 `resumable=True` 标注当前流式会话接入方式，不再使用 “We use …” 说明句或将该路径泛称为 Realtime WebSocket API。`resumable=True` 不是 `generate()` 的直接参数，也不是 `StreamingInput` 的构造参数。具体调用见[当前原型接口](experiments.md#prototype-streaming-interface)，官方命名见[外部系统索引](references/duplex-serving-systems-landscape-2026-09.md#realtime-ecosystem)。后端标识与底层核心接口属于不同层次，不能仅凭 `AsyncLLM` 或 `StreamingInput` 的调用将 vLLM-Omni 标识改为 vLLM。这些是实现接口注记，不是研究机制或冻结的论文范围，亦不代替 Pilarius KV 对接的实现核验。

<a id="research-mechanisms"></a>
| 设计组成 | 预期作用 | 待验证问题 |
| --- | --- | --- |
| 均匀 phase 分配 | 分散恢复需求与活跃驻留 | 能否降低峰值，批处理代价多大 |
| 按预算部分逐出 | 在恢复能力允许的范围内回收空间 | 释放字节与空闲时长如何转化为容量收益 |
| 时间与空间约束下的提前恢复 | 在下一 tick 前准备 KV，控制提前占用 | 共享链路、增长和抖动下是否仍可及时完成 |

各组成是否构成独立贡献须由因果论证与消融确定。主动周期性重算留作 [future work](#future-recomputation)。

<a id="one-session-cycle"></a>
## 一个周期

1. tick 到达，处理可用输入；编码与 prefill 连续推进，随后 decode。
2. 本轮计算完成，确认目标 KV 的执行与传输引用均允许安全回收，且所需主机副本有效。
3. 释放选定 KV 的 GPU 空间，保留下一轮的恢复计划。
4. 当计划启动时机和 GPU 空间同时满足，预分配目标空间并发起 H2D。
5. 传输完成后发布有效状态，在下一 tick 前准备好下一轮所需 KV。

下一 tick 同时是本轮 soft deadline。KV 提前就绪只消除恢复造成的额外等待；下一轮按时完成仍依赖计算和排队预算。

<a id="operational-flow"></a>
## 四组件的运行流程与伪代码

本节将[组件职责](#logical-architecture)和[接口契约](#component-interface-contracts)展开为设计级执行流程，供写作与实现共同使用。函数名、事件名和记录结构只是表达方式，不是已有 API、进程拓扑或实现证明。伪代码中的策略函数须按[未决设计](#open-design-decisions)完成决策；不能将占位函数当成已确定算法。

### 状态归属与执行约定

| 状态 | 逻辑负责人 | 至少需要区分的内容 |
| --- | --- | --- |
| Residency plan | Planner 产生，Session manager 消费 | session-to-group/phase 关系、逐会话逐出预算、恢复时机、最大上下文及计划适用范围 |
| 会话周期进度 | Session manager | 工作与输入关联、周期/tick、原 deadline、待提交工作、正在执行的工作及阻塞原因 |
| KV 状态 | KV memory manager 与后端权威状态协调 | 逻辑范围、GPU 分配、有效 GPU 内容、有效 host coverage、执行/共享/复制引用、待回收与待恢复操作 |
| 复制进度 | KV transfer engine | 操作身份、方向、源与目标、依赖、排队/在途/成功/失败，以及对应完成事件 |

系统由时间事件与运行事件推进，不要求单一线程或单一消息队列。所有“检查条件后提交／释放／发布”的操作都必须与后端引用和状态更新协调，不能把伪代码中相邻两行理解为允许竞态的独立操作。图中的 group 颜色不能替代这些状态。

<a id="planner-flow"></a>
### Residency planner：产生可复用的驻留安排

触发来源是准入和会话集合变化。Planner 按配置的最大上下文估计 KV 需求，结合给定负载下候选分组的执行成本及资源状态，输出候选计划或不可行结果；不直接申请物理块或发起复制。具体约定见[最大上下文规划](#maximum-context-planning)。

```python
def build_candidate_plan(session_changes, sessions, resources):
    demand = estimate_at_max_context(sessions, session_changes, resources)
    candidate = choose_joint_plan(demand, resources)  # 求解方法待定
    # candidate 包括 phase/group、逐会话预算和周期内恢复时机
    if not compute_and_deadline_constraints_hold(candidate, demand):
        return INFEASIBLE
    if not shared_transfer_schedule_fits(candidate, demand):
        return INFEASIBLE
    if not gpu_allocation_fits_over_time(candidate, demand):
        return INFEASIBLE
    if not host_capacity_fits(candidate, demand):
        return INFEASIBLE
    return candidate
```

GPU 检查计入恢复目标从完整分配时开始的占用，不能只检查准入瞬间的空闲空间。按最大上下文核算每个会话的 KV 需求，再检查周期内的分配轨迹，不要求这些 KV 同时常驻 GPU。候选搜索、成本估计与恢复安排仍待确定。正常周期沿用已生效计划；会话集合变化时按[规划与修正](#planning-updates)衔接新旧计划。

<a id="session-manager-flow"></a>
### Session manager：按时间和事件推进计划

Session manager 保存周期进度、安排计划中的恢复触发，并处理 tick、KV readiness、执行完成和阻塞反馈。新增 KV 可复制事件交给 memory manager；原始复制结果也先交给 memory manager，不能直接作为执行许可。

```python
def on_session_event(event):
    if event.kind == RESTORATION_TIME:
        memory.request_restore(event.target, active_plan)
    elif event.kind == SESSION_TICK:
        work = record_periodic_work(event)  # 保留原 tick/deadline 和输入关联
        try_submit(work)
    elif event.kind == KV_READY:
        for work in affected_pending_work(event):
            try_submit(work)
    elif event.kind == EXECUTION_COMPLETED:
        work = resolve_current_work(event)  # 校验身份，忽略重复状态变更
        record_execution_completion(work)
        memory.request_eviction(work.session, active_plan)
        retry_eligible_pending_work(work.session)
    elif event.kind == RESOURCE_BLOCKED:
        record_blocked_operation(event)
        report_deadline_risk_if_needed(event)
    elif event.kind == RESOURCE_CHANGED:
        memory.retry_eligible_pending_operations(active_plan)


def try_submit(work):
    if not is_pending(work) or not release_time_has_arrived(work):
        return
    if conflicting_execution_is_in_flight(work):
        return
    if not memory.required_kv_is_ready(work):
        return
    # 就绪核验、获取执行引用与提交须协调；不能检查后被并发逐出。
    result = submit_with_valid_kv_references(backend, work)
    record_submission_result(work, result)
```

提前恢复完成只使 KV 就绪，不提前释放尚未到 tick 的工作；tick 到达而 KV 缺失时也不允许计算。提交失败须保留正确的待处理与引用状态，不能标为正在执行。后端决定实际执行顺序和 batching 策略，Session manager 不构造强制执行 batch。阻塞操作由符合条件的资源变化或重试事件推进；不能忙等，也不能每次空间空出就绕过恢复时机。资源阻塞按[恢复分配决策](#group-restoration-allocation)重试，超出计划余量时触发[修正](#planning-updates)；这些策略尚待实现验证。

<a id="memory-manager-flow"></a>
### KV memory manager：备份、逐出、恢复与有效状态发布

该组件把驻留请求转为满足引用与覆盖条件的内存操作。它使用后端的分配与引用权威状态，不以另一份独立计数替代物理池。下面的保护操作表示逻辑安全要求，不规定锁、事件或具体接口实现。

**增量备份。** 每个正在推理的 session 都可在累计新增、可安全复制的 blocks 后触发一次异步 D2H；不等待整轮完成。后端报告新增 KV 已可安全复制时，仅处理尚无有效主机副本且未被在途复制覆盖的范围，具体触发与合并粒度未冻结。

```python
def on_new_kv_available(session, ranges):
    copyable = select_stable_unbacked_ranges(session, ranges)
    if not copyable:
        return
    destination = allocate_host_destination(copyable)
    if destination is None:
        report_backing_blocked(session, copyable)
        return
    request = protect_and_describe_copy(D2H, copyable, destination)
    enqueue_or_settle_failure(request)
```

`protect_and_describe_copy` 须保护源、目标及相关复制引用；提交失败须安全处理已取得资源。在 D2H 成功完成前，不扩展有效 host coverage，也不因已安排备份就释放源 GPU 空间。

**部分逐出。** 计算完成仅触发检查，不构成整组或整份历史可以释放的证明。

```python
def request_eviction(session, plan):
    candidates = choose_eviction_ranges(session, plan)  # 选择规则待定
    for block in candidates:
        if not host_copy_is_valid(block):
            defer_eviction(block)
        elif has_conflicting_execution_shared_or_transfer_references(block):
            defer_eviction(block)
        elif not eviction_still_fits_plan(block, plan):
            report_plan_risk(block)
        else:
            release_and_mark_missing_under_state_guard(block)
    report_actual_released_capacity(session)
```

实际释放量与计划预算分别记账，共享物理块不重复计数。主机备份完成或引用解除后，待逐出操作可重新检查；仍须检查计划适用性与后续恢复条件，不能因延后执行而在已不合适的时刻盲目逐出。

**恢复。** `target` 表示一个 session 的一次恢复，覆盖其本次执行所缺的全部历史 KV。Session manager 按计划时机和次序发起恢复；每个入队 session 都先获得完整目标。可有多个完整目标等待复制或完成，全部立即计入容量；分配受阻时不持有部分目标，也不越序为后续 session 预留。

```python
def request_restore(target, plan):
    if not restoration_is_eligible_now(target, plan):
        record_deferred_restoration(target)
        return
    missing = required_ranges(target) - valid_gpu_ranges(target)
    if not missing:
        publish_readiness_if_complete(target)
        return
    if matching_restore_is_in_flight(target):
        attach_to_existing_operation(target)
        return
    if not valid_host_ranges(target).covers(missing):
        report_missing_backing(target)
        return
    destination = allocate_full_restore_destination(target, missing)
    if destination is None:
        report_resource_blocked(target)
        return
    # 整个目标已计入 GPU 占用，其内容尚未因此有效。
    request = protect_and_describe_copy(H2D, missing, destination)
    enqueue_or_settle_failure(request)
```

范围查询、重复操作处理、分配和复制引用保护须保持一致状态；上例不指定合并部分重叠恢复的算法。目标分配成功也不代表传输服务必然及时可用，排队须计入计划风险。

**完成处理。** 先将结果关联回正确操作，再发布对应范围的有效状态；原始 copy event 不能直接解锁模型计算。

```python
def on_transfer_result(result):
    operation = resolve_transfer_identity(result)
    if not result_is_publishable_for_current_state(operation, result):
        settle_without_publishing_to_new_state(operation, result)
        return
    if result.failed:
        settle_failed_transfer_safely(operation)
        report_transfer_failure(operation)
        return
    if operation.direction == D2H:
        publish_valid_host_ranges(operation.ranges)
    else:
        publish_valid_gpu_ranges(operation.ranges)
    release_completed_transfer_references(operation)
    for work in affected_pending_work(operation):
        if all_required_gpu_ranges_are_valid(work):
            notify_session_manager(KV_READY, work)
    retry_eligible_pending_operations(active_plan)
```

失败、取消或旧事件的处理同样需要等待复制不再访问相关资源后才能释放引用或复用空间；“不发布”不能简化为丢弃事件而泄漏资源。`Transfer completion` 只说明某次复制成功，`KV readiness` 要求对应工作所需全部范围有效。Ready 按 session 的工作和 KV 范围核验；不设置全组就绪屏障。

<a id="transfer-engine-flow"></a>
### KV transfer engine：提交异步复制并报告结果

该组件拥有复制队列、在途记录和完成事件。它不选择逐出预算、不独立改写组级恢复顺序、不发布 KV readiness，也不决定释放哪些 GPU 块。

```python
def enqueue_copy(request):
    validate_descriptor_and_protected_resources(request)
    pending_transfers.add(request)


def progress_transfers():
    for request in transfers_eligible_under_assigned_order_and_dependencies():
        result = launch_async_copy(request)
        track_launch_or_report_failure(request, result)
    for result in newly_observed_transfer_results():
        notify_memory_manager(result)
```

队列和完成检测可由后端支持的异步方式实现，不要求忙轮询。D2H 与 H2D 都可能异步执行；不得为了让队列更忙而擅自突破已安排的依赖或恢复顺序。入队和启动成功均不等于传输完成。

<a id="group-restoration-walkthrough"></a>
### 串联示例：一次 Group C 恢复

假设 C 的待恢复范围已有有效主机副本，当前计划已安排恢复时机：

1. 计划中的恢复时间事件到达，Session manager 向 memory manager 请求恢复 C 的相应对象。
2. Memory manager 核验 C 中计划所指 session 的缺失范围与主机覆盖，为该 session 获取完整目标；空间不足则报告阻塞，不提交无目标的复制，也不提前为后续 session 占空间。
3. Transfer engine 执行 H2D。目标空间已计入占用，但尚未完成的内容不可被模型访问；后端可执行其他具备条件的工作。
4. Transfer engine 报告结果，memory manager 发布成功范围的有效性，并向 manager 通知满足条件的工作已就绪。
5. Session manager 同时检查周期释放、输入与执行条件后提交工作。后端按自己的执行调度策略运行，不被强制将 C 作为一个 batch。
6. 新增 KV 进入增量备份路径；计算完成触发逐出检查，安全范围释放后供后续恢复使用。下一组仍要独立满足计划、空间与传输条件，不能因 C 完成就无条件立即启动。

该链路与[接口契约](#component-interface-contracts)、[验收场景](#implementation-handoff)共同描述设计；已实现与已验证的范围仍由对应实现审计和证据说明。

<a id="release-offset-scheduling"></a>
## Phase 与准入

周期 `T` 划分为若干均匀 slot，phase offset 间隔为 `T/S`。新会话准入时分配 slot；均匀网格是当前设计选择，不声称最优，也不限定一 slot 一 session。已有会话不需要因新会话加入而重新排相位。

phase assignment 可通过 session-to-slot assignment 具体实现，将会话组织为 session group 后形成 group schedule。一个 group 可以包含多个会话；组级安排不要求合并历史、统一每会话逐出量或将整组作为原子复制单位，底层仍按每会话和每 block 的安全条件执行。成员选择与组大小仍由联合规划确定；组内恢复按计划次序推进，实际执行顺序由后端决定。session group 首先是调度对象，其是否形成独立贡献仍需分组算法与消融证据；机制名称继续使用 phase assignment、partial KV eviction 和 cyclic KV restoration。

准入不能仅检查空闲 slot。配置规划需要联合选择承载规模、slot 分配与每会话恢复预算，并检查整周期的瞬时显存、链路和计算安排。规划输入包括周期、上下文上限、模型计算成本、有效 GPU KV 池、主机容量及有效带宽。求解算法尚未确定。

<a id="maximum-context-planning"></a>
### 按最大上下文规划

使用模型与后端配置已有的最大上下文长度作为会话上限，不另设增长预测范围或工作量声明。规划按所有候选会话达到各自上下文上限时的 KV 需求核算 GPU、主机和恢复预算；给定负载的计算与传输成本仍须检查。实际执行按当前有效历史备份、逐出和恢复，不为尚未生成的历史建立 KV。

上限计入参考历史保留的输入和生成位置。提交新增输入及推进生成时须遵守后端的上下文长度限制，不允许会话越界，也不通过隐式缩短参考历史继续增长。具体长度限制沿用后端已有能力，仍须核验对接是否正确；不新增迁移、降级或重新协商服务范围的流程。

按上限规划不要求所有最大历史同时常驻 GPU，仍通过周期内的逐出与恢复复用空间。它省去对未来增长的预测与滚动续期，但可能少接纳一些当前历史较短的会话；这是当前选择的简单性与容量利用率取舍。该选择是设计约定，不是已实现或已验证的性能保证。

<a id="planning-updates"></a>
### 规划与修正

主要规划在准入时按最大上下文完成，运行中沿用计划；上下文在上限内增长不触发滚动续期。每周期按实际 KV 状态执行逐出、空间检查和恢复，不重新求解全部预算。

采用以下修正规则作为当前设计选择，不将其作为独立研究机制：

1. **触发。** 新会话申请或会话结束时更新计划。重复触发可合并，候选计算期间继续执行当前有效计划；不引入预测时域或定期续期参数。
2. **调整范围。** 已接纳会话的 phase 和 slot 网格保持不变；调整尚未开始的逐出预算及恢复时机，新会话分配到已有网格。网格大小作为候选配置参数，在没有存量会话时才更换。
3. **切换。** 候选就绪后暂停发起新的恢复，等待已分配目标的 H2D 操作完成或安全结算。以当前物理分配、有效内容和执行/D2H 引用重新核验候选；计入核验及切换开销。通过后增加计划版本，只替换未开始的操作。现有计算与 D2H 继续结算，核验失败则不发布候选。
4. **不可行或阻塞。** 新增会话使候选不可行时拒绝本次准入并保留存量计划。运行时恢复空间不足则等待资源事件，复制或执行错误通过原有错误路径报告；延迟从原 tick 计量。保留 KV 安全检查，不新增违约容忍、持续落后或自动降级策略。

计划版本区分未来调度安排，不能替代 session、逻辑范围与复制操作的身份核验。旧计划中已完成恢复的驻留内容仍有效，除非实际发生逐出或失效；新的预算不得追溯地改变在途引用。上述切换策略先排空已经分配目标的 H2D 操作，再发布新版本，可能引入队列等待，需测量其代价。

候选搜索、成本估计与恢复安排仍属[联合规划待决项](#open-design-decisions)。最大上下文约束只限定状态规模，周期完成表现仍由实验测量，不由该上限单独保证。

<a id="offset-resource-rationale"></a>
在会话同质、每次恢复及时获得空间、传输耗时等于相邻 phase 间隔的理想条件下，相同恢复量可以使传输首尾衔接。异质状态、不同完成时刻及资源竞争会破坏这些条件。各会话逐出量可以不同，但共享预算相互耦合；不能宣称均匀 phase 自动保证满带宽或最小峰值驻留。

phase 的权限由应用允许的时间安排给出。首次对齐等待、推迟提交和切块变化带来的等待均需计量，不能用提交后的延迟隐藏输入积压。

<a id="batching-tradeoff"></a>
### 错相位与批处理代价

同相位让更多工作同时具备执行资格，有利于后端形成大 batch，但会集中 KV 驻留与恢复需求。错开 session group 能分散需求，也可能因 batch 变小、模型迭代和权重访问次数增加而延长整组周期工作。每个 slot 可含多个 session，保留组内批处理机会；实际 batch 仍由后端决定。均衡分组时，每组可提交规模随 slot 数增加从 `N` 向 `N/S` 变化，不预先保证 batch 的最小规模或某个固定减速比例。

固定历史长度与工作量，分别测得同相位和分组错相位的周期执行成本 `C_aligned` 与 `C_grouped`。新增成本 `C_grouped-C_aligned` 加上传输干扰和调度等待须落在原余量 `T-C_aligned` 内，并满足逐会话 deadline。[播放节奏对应的短生成工作](problem.md#playback-paced-work)解释为何适度的批处理损失可能被吸收；它不能代替候选分组下的测量与准入检查。

<a id="partial-kv-eviction"></a>
## 部分逐出与主机后备

<a id="incremental-host-backing"></a>
新增 KV 在推理过程中分批异步建立主机副本，不要求等待整轮计算结束；所有正在生成新增 KV 的 session 都可触发这条镜像路径。累计可安全复制的新增 blocks 后发起一次 D2H，触发粒度、阈值与复制合并方式尚未固定，不由图中箭头数量推定。已备份的有效历史无需每轮重新 D2H。副本在主机上占用容量，未完成的复制仍可能持有 GPU 引用。备份本身不释放显存。

<a id="idle-session-eviction"></a>
逐出范围与粒度仍待确定。逐出量按会话决定，上界由可用恢复窗口、有效传输服务和安全可回收状态共同限制；它还需足够大以产生容量收益。窗口预算是必要约束，不能独立证明可行性。

H2D 路径只选择已有有效主机副本且无冲突引用的状态。逐出之前应检查后续恢复的时间与空间安排；单靠“现在有压力”不能保证下一周期可恢复。精确预算分配规则仍待制定；实际逐出量不超过当前安全可回收状态。

全量逐出可能超过整个周期的传输预算，也可能无法满足单次恢复窗口或目标空间要求；约束及容量收益上界见[资源分析](problem.md#bandwidth-memory-bound)。部分逐出保留不能及时恢复的历史，让恢复量可独立于总历史长度选择；保留部分仍会占用并可能最终耗尽 GPU 空间。规划目标是降低峰值驻留并满足服务目标，不能用满带宽直接代替容量收益。

<a id="kv-prefetching"></a>
## 恢复调度

Residency planner 根据下一 tick、恢复量及有效传输时间估计安排启动时机并留出余量；session manager 运行时沿用计划，核对当前缺失状态与执行条件，必要时报告计划风险。一次恢复须同时满足：

- **时间条件：** 到达预定启动时刻，H2D 队列有相应服务预算，预计能在下一 tick 前完成。
- **空间条件：** GPU 有足够空间一次性预分配目标；前序会话逐出后释放的空间可供后续恢复使用。

目标预分配后立即计入占用，不能按已传字节渐增记账。即使空间已空出，也不必立刻恢复；过早恢复会缩短显存节省的区间。若到最晚启动时刻空间或链路仍不可用，就存在 deadline 风险，需要可观测的异常处理。

预算应涵盖 H2D 排队、有效传输、完成通知以及安全余量，并考虑 D2H 与计算对链路的影响。soft deadline 不意味着可以省略这些开销。

<a id="on-demand-restoration"></a>
### 按需回载

若提前恢复未完成，计算必须等待有效状态；不能读取未完成 KV。按需回载仍遵守逐 session 完整目标和有序恢复规则，恢复缺失状态的延迟可能导致 deadline miss；按原 tick 记录这一延迟，不增加独立的降级策略。

<a id="future-recomputation"></a>
### Future work：在 Planner 中加入重算决策

当前设计通过 H2D 恢复 KV，主动周期性重算留作后续工作。后端回退不代表 Pilarius 已将重算纳入规划。

扩展方向是在 residency planner 中增加一个决策维度，选择逐出 KV 中通过计算重建的部分，其余缺失状态通过 H2D 恢复。可用重算量或两种恢复方式的分配来表达这个维度，具体参数化与区间选择留待后续研究。规划仍可沿用 phase、逐出预算和最大上下文规划的框架；重算参与的是周期内的主动恢复，不仅是失败后的回退。

执行需要保留重放所需的输入和位置，并由后端执行重算、报告有效 KV。规划须计入与正常会话共享的计算时间、恢复目标和工作区，使用整组已接纳会话的可调度余量，并满足逐会话 deadline。

重算区间、与 H2D 的配比、启用条件及后端执行支持均留作后续工作。传输与重算组合已有相关工作，不将这一组合本身写成原创，也不预先声称容量收益。

<a id="kv-state-model"></a>
## 状态与正确性

| 状态维度 | 必须区分的内容 |
| --- | --- |
| 活动与引用 | 等待、执行、共享引用、复制引用 |
| GPU 分配 | 物理块与目标预留；共享块不重复计数 |
| GPU 内容 | 状态身份、有效范围和就绪事件 |
| 主机覆盖 | 已完成且有效的副本；cursor 不是覆盖证明 |
| 传输 | 计划、排队、在途、完成、失败 |
| 缓存索引 | 可查找不等于永久驻留或无引用冲突 |

<a id="correctness-and-failure-analysis"></a>
设计须保持参考历史，禁止过早复用空间，并在状态就绪后才允许相关计算。取消、重复恢复、主机替换、覆盖缺口和需求超越预取都需验证。若执行接口只支持连续前缀复用，早期缺口可能迫使后续区间一起重算；不能把这种接口限制误写成重算的一般规律。

<a id="output-delivery"></a>
输入处理、生成完成和用户交付是不同事件。计量遵循[服务协议](experiments.md#measurement-semantics)，不能把从缓冲取出旧输出当成本周期已经完成。

<a id="open-design-decisions"></a>
## 未决设计

| 问题 | 所需决策或验证 |
| --- | --- |
| 容量、slot 与预算联合规划 | 按最大上下文选择承载规模、分组与预算的候选检查或求解方法；给定负载下的成本估计 |
| 每会话逐出量 | 安全状态选择、有效传输窗口、预算分配与候选恢复顺序的选择 |
| 已选执行策略的实现与验证 | [逐 session 恢复](#group-restoration-allocation)、[最大上下文规划](#maximum-context-planning)和[会话变化时修正](#planning-updates)已选定；仍需验证上下文限制、队首阻塞与切换开销 |

<a id="group-restoration-allocation"></a>
### 恢复分配：逐 session 完整目标，逐 session 就绪

根据作者授权，当前设计选用逐 session 分配和就绪，作为可替换的 implementation choice；其依据是后端不要求整组共同执行。下表是条件分析，未产生实测优劣结论。

| 方案 | 分配与推进条件 | 主要代价 |
| --- | --- | --- |
| 整组预分配 | 整组所有缺失 KV 的目标可用后才开始；后续本组复制无需再等目标 | 首个 session 也要等待全组空间，并提前占用排在后面的 session 的目标；若要求全组执行屏障，这种预留更直接 |
| 逐 session 完整分配（采用） | 按计划顺序，为当前 session 的全部缺失 KV 分配目标；复制完成后可独立就绪 | 分配次数更多，后续 session 仍可能等空间；就绪分散可能影响 batching，不能预设一定降低峰值 |

执行规则如下：

1. 计划给出跨组及组内的 session 恢复次序和启动时机。H2D 复制按该次序排队推进；各 session 的目标完整分配后才可入队，故可有多个完整目标等待复制或完成，均立即计入占用。单个 session 内可包含多个 block 复制，不要求物理连续空间或单条 DMA。D2H 仍可并行，干扰计入有效带宽。
2. 到达计划时机且轮到该 session 分配时，检查缺失范围及有效主机覆盖，完整分配所有缺失历史的目标，再提交 H2D。空间不足则不保留部分目标，也不越过它为后续 session 分配；已经入队的复制继续推进。通过资源释放/就绪事件重试，等待时间计入本周期延迟。
3. 所需历史全部有效时发布该 session 的 readiness；满足 tick、输入和前次执行条件后即可提交，不等待本组其他 session。恢复完成但尚未到 tick 的状态仍占用 GPU 空间，规划必须计入。
4. 传输失败或取消后，必须先确认复制不再访问目标，才能释放引用或回收失效目标；不能用队列前进替代资源结算。后续 session 必须再次检查实际空间，不能从前序复制完成推断空间增加。

完整 session 目标和独立就绪避免了“多个未完成的 session 各占一部分恢复空间，同时等待剩余部分”的分配方式；它不保证无等待或所有 deadline 均可满足。固定顺序会产生队首阻塞，早就绪的 session 也可能占住空间等待 tick。联合规划仍须检查整条分配时间线，包括已恢复、保留和新增 KV。若未来需要改变计划内复制次序或引入整组计算屏障，应重新评估该选择。

<a id="implementation-boundary"></a>
## 实现核验入口

实现覆盖及旧测量的限制见[已有证据](findings.md#implementation-audit-boundaries)；组件定位与代码修改说明见 [Agent 导航](agent/README.md)。

<a id="implementation-handoff"></a>
### 实现交接与验收入口

实现先读[四组件运行流程与伪代码](#operational-flow)，再以[组件接口](#component-interface-contracts)、[状态维度](#kv-state-model)、[安全逐出](#idle-session-eviction)和[恢复条件](#kv-prefetching)为契约；图形、颜色或回调到达顺序不能代替状态判断。代码入口与改动流程见 [Modify Engine](agent/tasks/modify-engine.md)。以下为待实现验收场景，不表示已有测试或证据覆盖：

| 场景 | 必须验证的结果 |
| --- | --- |
| D2H 未完成时请求逐出 | 不把未完成副本当成有效 host coverage；不提前释放仍有执行或复制引用的块 |
| 目标分配失败或传输服务不可用 | 为一个 session 完整分配或完全不分配；不向未分配目标提交 H2D，不发布 readiness，不预留后续 session 目标；按资源事件重试并报告风险 |
| 目标已分配、H2D 只完成一部分 | 从完整目标分配时计入 GPU 占用；缺失范围未全部有效前，禁止依赖它的计算 |
| H2D 提前完成或晚于计划 | 提前完成仍遵守请求释放时机；迟到如实计入服务延迟，不移动原 deadline 掩盖等待 |
| 取消、重复恢复、旧完成事件与空间复用 | 保持身份、引用和操作关联；不将旧事件发布到新状态，不重复释放或提前复用空间 |
| 一个 group 含多个 session | 历史与逐出预算保持逐会话独立，逐 block 检查安全；复制按序、逐 session 就绪，后续分配阻塞不阻止前序已就绪且到 tick 的工作提交 |
| 共享物理块与后端执行并发 | 物理容量不重复记账，所有冲突引用安全后才可回收；后端与驻留管理看到一致的有效状态 |
| 计划复用与修正 | 触发事件可合并、既有 phase 不变；新计划仅在无未结算 H2D 目标且重检通过后发布，计算与 D2H 引用继续保护；旧事件仍结算，不重新解释为新操作 |
| 最大上下文与新准入 | 按最大上下文核算需求；输入与生成均不得使会话超过长度上限，不隐式裁剪参考历史；上限内增长不触发滚动续期 |
| 无可行修正 | 新增负载不可行则拒绝准入；分配阻塞等待资源事件，复制或执行错误通过原有路径报告，保留真实延迟与错误结果 |

可按上述接口、状态区分、恢复分配与修正规则实现并验证执行路径。联合预算求解、分组选择、候选恢复顺序及成本余量仍须按[未决设计](#open-design-decisions)完成决策，不能从图中的四组、等间距示意或箭头先后顺序推定默认答案。主动周期性重算按[future work](#future-recomputation)处理，不扩入当前 H2D 主路径。

<a id="session-manager-execution"></a>
### Session Manager 执行结构

以下为当前代码的执行说明；与前文最新规划要求尚有差距，见下方旧原型边界。

当前保守实现以显式配置的 `restore_lead_s` 指定窗口长度，planner 用整组逐出上限和成本 profile 检查其可行性；Session Manager 在 `next_tick - restore_lead_s` 到达后检查空间并提交恢复。它尚未根据每周期实际字节自动缩短或重新标定启动提前量。逐出上限限制后续 H2D 的工作量，不是到时强行截断在途 DMA；超窗时依然等待有效状态，并记录完成迟到。配置预测可行与实测按时完成必须分别验收，运行期低频 review 不代替成本标定或不可行计划的修复。

当前音频输入实现中，gateway 发送自上次采样以来的缓冲后清空，worker 将该段音频作为新的 streaming input。迟到 tick 可能积累比名义周期更长的输入。两个 first-party worker 共用按实际输入长度限制补齐的前处理实现，保留 STFT 边界和特征帧对齐；参数仅属于本次调用，不修改线程共享对象。模型的原始输入上限保持有效，超长输入仍遵循原截断行为。前处理完成后，vLLM 再按 mask 取有效特征送往 encoder。历史固定长窗口问题及验证结果见 [FINDING-E5](findings.md#finding-e5)。

当前可选的 manager 路径把计划执行放在 EngineCore 内的独立控制线程；另一个 copy 线程持有 H2D、D2H 各自的 CUDA stream，负责提交及完成轮询。gateway 提供绝对网格上的下一 tick，worker 经 utility IPC 安装计划。计算结束和输入恢复只交接活动状态；timer、copy 提交、完成确认和状态发布不要求再运行一个模型 step。线程划分与 utility IPC 属于 implementation choice，不构成独立研究机制。

manager 恢复路径先按物理地址排列刚分配、尚未绑定内容的目标块及主机源块，逐对绑定原始 block hash；逻辑上下文仍由 hash 对应关系恢复。这样避免空闲队列反序返回连续目标时人为拆碎复制；已绑定内容的目标映射不改写。copy 提交合并源地址和目标地址都相邻的物理范围，再按有界数量的描述符逐批入流，使已提交的 DMA 能与后续提交重叠。源／目的引用持续持有至结束 event 完成；合并不改变字节、布局或已绑定映射。短小的非阻塞 driver 提交和 event 操作保持 Python GIL，避免多次释放／重新获取解释器锁造成的提交间隙；不在此路径同步等待 DMA。该实现选择的测量协议见[copy 提交实验](experiments.md#copy-submission-experiment)，不构成新的研究机制。

这里的独立性有明确边界：每次 managed input 在 worker 的 `_managed_push` 中先等待 `session_plan` utility 返回，之后才入输入队列；utility 由 EngineCore 主循环在模型迭代之间处理。因此新输入进入预处理仍受该循环的长 batch 或同步收尾影响。原生按需回载与增量备份的描述生成也仍依赖 scheduler；独立的是描述交给 CopyService 之后的提交、轮询与完成回调，以及 manager 已安装计划的 timer 执行。输入恢复与 idle 状态通知仍由 scheduler 生命周期触发。

每会话计划包含下一 tick、恢复提前量、保留前缀、可选逻辑块区间及逐出块数上限。区间为半开区间，可以不连续；默认候选为保留前缀之后的完整块。manager 仅从 idle 请求选择已有有效主机副本、且 GPU 上只有该请求引用的块；共享块、未完成 D2H 引用、未满块和主机覆盖缺口不进入本次选择。未逐出的完整块与选中块的主机副本分别持有引用。恢复窗口开始后，不再新建本轮逐出缺口。

恢复启动前一次性分配目的块，并检查空闲空间余量；容量不足保留主机引用并重试。只有 CUDA 完成事件可查询为完成后，目的块才进入有效缓存索引。完成且仍 idle 的会话保留目的引用，直至输入恢复。取消释放 idle 引用，在途引用交由完成回调释放。未启用准入的给定计划模式中，输入若先于恢复完成到达，则走原生按需恢复/重算路径；未完成的目的块不可查找，可能发生重复恢复，当前实现不保证去重或截止时间。

vLLM adapter 用同一锁保护 scheduler 元数据和 block pool 操作，不在模型执行或等待 GPU 输出时持锁。原生 connector 仍生成已确认计算的存储描述和按需装载描述；adapter 将描述移交 copy 线程，完成回调执行原生引用清理和主机覆盖发布。因此按需 H2D 和增量 D2H 也不依赖下一次模型输出触发提交或轮询。当前适配要求同进程执行器、同步 scheduler、单 KV group，且无 speculative decoding 和 worker 侧 KV zeroing；这些边界不限定研究设计。

该执行路径消费给定计划；启用准入时，由[保守 planner](#conservative-admission)下发 slot 和固定预算，并在输入提交前核验上一轮执行及所需 KV readiness。恢复在途时不重复发起回载；就绪引用保留到后端分配执行引用后才交接。原有不启用准入的诊断模式保持给定计划路径。该实现尚未自动标定成本或求解最优预算，其性能验证状态仍以[已有证据](findings.md#implementation-audit-boundaries)为准。

<a id="conservative-admission"></a>

**旧原型边界：** 下列有限前瞻与排队实现用于已登记诊断，尚未对齐本轮最大上下文规划、准入拒绝和带版本切换要求；不能作为前文设计已完成的证明。

### 当前实现：可替换的保守准入策略

作者确定采用按组恢复窗口封顶的逐出规则。一个 slot 对应一个 session group，可以含多个 session；组成员保持共同 phase，但不要求后端把它们组成一个执行 batch。组的恢复区间为每次 tick 前的 `[tick − lead, tick)`。窗口容量来自该区间内扣除提交、完成与安全余量后的有效复制服务，不按每个成员重复计算带宽。

设组窗口能够恢复的总量为 `C_g`，成员分配的逐出上限为 `q_i`，须满足 `Σ q_i ≤ C_g`。当历史增长时，本周期实际逐出量为不超过 `q_i` 的安全可回收块数：只能选择保留前缀以外、已有有效 host backing 且没有其他执行／传输引用的完整块。实际量可以逐渐增加，达到上限后保持封顶；不因历史继续增长扩大搬运窗口。当前保守实现给成员配置固定上限，并在准入时检查整组上限，即使当前短历史尚未用满，也不能提前透支未来带宽。

这里封顶的是计划中的恢复量，不是在窗口结束时截断已启动的 DMA。实际复制因竞争或成本低估超窗时，仍完成字节复制并持有引用，直到有效 KV 发布；报告恢复迟到，输入继续受 readiness 约束。H2D 恢复上限也不禁止推理中新增 KV 的增量 D2H。

窗口封顶使传输需求有界，不使 GPU 驻留需求永久有界。历史超过可逐出上限后的增长仍留在 GPU，须继续计入容量预测；有限前瞻检查与长期服务保证仍须区分。无需为这种上限内增长每周期重排 phase；改变既有上限或跨组重排属于另外的计划切换问题。

作者已选择先实现一个保守的可行性检查器，作为联合求解接口的首个实现；它不声称最优分组或最大容量。配置固定周期、slot 数、恢复提前量与逐会话逐出上限，既有会话保持 phase 和预算。Planner 按当前组成员数、再按 slot 编号尝试候选位置；计数只决定搜索顺序，每个候选仍须通过资源检查。

资源估计必须由配置显式提供：有限前瞻范围、单会话每周期计算上界、初始状态与增长上界、双向有效复制服务、提交与完成开销、余量和并发上限。物理 GPU/host 容量和当前引用占用从后端读取；GPU 预留取配置余量与实际恢复分配门槛的较大值，不能在准入时花掉 copy 路径要求保留的空间。当前策略将一组的计算与 D2H 保守串行安排在该 slot 区间内，H2D 放在该组 tick 前的独立窗口；检查每组共享服务总量，不能给每个成员重复分配同一份带宽。其适用域要求恢复提前量不超过 slot 间隔。成本估计必须包含对应负载、后端 batching 和传输干扰，未标定配置不构成服务能力证据。

显存预测按区间检查峰值：恢复目标从完整预分配时计入，计算及备份后才计入逐出收益；新会话在首轮执行和备份完成前不享有逐出收益。检查预留前瞻范围内的增长和在途物理占用，主机覆盖使用保守的完整历史容量预算。逐出预算只是上限；运行期显存收益还受当前完整块的已确认 host coverage 和非共享 GPU 引用约束，新会话不提前获得尚未形成的可回收收益。传输服务仍按前瞻内可能发生的最大恢复量预留，不能随当前可回收收益减少而少算将来的复制负载。预测采用逐会话不共享的上界，不将潜在共享计为容量收益；真实物理计数仍由后端唯一维护。该检查器不按应用最大上下文预留整个生命周期的状态。

Gateway 的 Session Manager 维护 FIFO 等待队列。未准入会话不创建模型请求，也不上传音频；客户端收到 `session.admitted` 后才按实时速度发送。队首不可行时保留等待并记录原因，不绕过队首。新到达、退出及定时重试触发候选检查，周期执行沿用已安装计划。低频 review 以当前历史和引用状态重新检查相同安排，发布风险反馈；不可行的 review 不移动既有会话，也不伪造新的服务保证。更一般的计划重排与风险恢复策略仍待确定。

结束分为排空与资源归还：客户端结束输入后，最后的输入仍执行，输出按周期 cap 排空；Session Manager 要同时看到模型执行结束与前端末尾输出。随后取消后端持久请求并等待所有复制引用释放，planner 才删除 reservation，gateway 才发送 `session.completed` 并重试下一会话。异常断连走取消与清理路径，不能冒充完成；取消幂等，旧输入和旧计划不能复活已关闭的身份。一个 session 退出只改变该 slot 的成员，不改变其他会话的 phase。

该实现目前消费同质工作量的显式成本上界，并保留原有逐 session 恢复适配路径；这不关闭[整组／逐 session 分配的比较](#group-restoration-allocation)。异质需求估计、自动选择 slot 数和上限、运行期不可行计划的恢复属于后续扩展；上限内随安全可回收历史增长的逐出已由上述规则执行。


<a id="initial-context-preloading"></a>
初始上下文预加载属于实验准备，协议与已登记行为见 [实验设计](experiments.md#initial-context-preloading)，不属于研究机制。

<a id="state-transparency-argument"></a>
### 状态搬运的语义透明性

按作者要求，以不变量和归纳论证说明透明性，不增加模型回答质量或大规模输出对照实验。固定每个会话的输入切片、逻辑顺序、保留历史、位置索引及参考模型的算子与采样语义。假设第 `k` 次更新前，恢复后的 KV 与参考执行的逻辑 KV 一致；字节无损的 D2H/H2D 只改变存放位置，且 readiness 阻止模型读取未完成的目标。因此本次更新读取相同输入与逻辑状态，得到相同状态转移和 token；更新后的新 KV 再按相同规则保留，归纳假设延续。初始状态一致给出归纳起点。

有效副本、完整映射、位置不变、引用生命周期和完成后才能使用是此论证的实现义务。改变数值精度、采样语义或输入边界不属于仅改变驻留位置的变换。固定采样数切片使一次 gateway 迟到不会合并更多音频为一个不同的模型输入；相关观测和协议见[实验入口](experiments.md#finite-cohort-runner)。
