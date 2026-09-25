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

异步备份不自动释放 GPU 空间，复制完成后须发布有效状态，KV 就绪后仍须等待执行条件。整组预分配还是按 session 分配尚未确定，见[恢复分配决策](#group-restoration-allocation)。

<a id="inference-backend-boundary"></a>
### 推理后端边界

Pilarius 调节周期请求何时具备提交条件及其历史 KV 的驻留安排；推理后端负责请求执行调度与模型执行；使用 batching 时，其 batch 组织也由后端负责。Continuous batching 不是后端必须采用的固定策略。session group 是 phase 与驻留调度对象，不是强制一起执行的 batch。Pilarius 改变可提交工作的时间可能影响后端形成的 batch，但不因此拥有后端的组 batch 策略。设计图的 Compute 颜色表示活动阶段，不保证相关 session 或 group 同时执行。

Inference backend 以可替换的职责边界呈现；具体运行时与当前实现覆盖分别见[实验配置](experiments.md)及[实现核验边界](findings.md#implementation-audit-boundaries)。可替换性要求后端支持请求提交、执行完成事件，以及 KV 身份、有效性、引用、目标分配、安全释放和复制完成的协调。仅有文本生成 API 不足以实现该对接；图示不宣称已支持多个后端，也不宣称可无改动替换。KV memory manager 是驻留决策与后端资源操作的协调职责，不表示复制另一套物理块分配器；实际分配与引用状态须保持一致的权威来源。

<a id="component-interface-contracts"></a>
### 组件接口与事件语义

以下是待实现和验证的逻辑契约；调用方式、类名、进程边界和字段编码由实现决定。设计图省略的错误反馈及生命周期事件仍须处理。

| 图中标签／逻辑交互 | 方向 | 必须表达的语义 |
| --- | --- | --- |
| Residency plan | Planner → Session manager | 会话与 group/phase 的关系、逐会话逐出预算、恢复时机及其适用范围；规划考虑的有限前瞻范围应可识别。运行期消费计划，不默认逐周期重新求解 |
| Evict / Restore | Session manager → KV memory manager | 针对具体会话和逻辑 KV 范围请求逐出或恢复，受当前计划、预算和时机约束；这是两个操作，箭头不表示接收请求就立即执行成功 |
| Transfer requests | KV memory manager → KV transfer engine | 已确定的 D2H/H2D 方向、源与目标、逻辑范围和依赖；提交前保证源有效、目标已分配并保护复制引用 |
| Transfer completion（图中省略） | KV transfer engine → KV memory manager | 指定传输已成功完成；仅提交、排队或启动均不构成完成。失败应作为失败结果报告，不得伪装成功 |
| KV readiness（图中省略） | KV memory manager → Session manager | 对应会话本次执行所需 KV 范围已在 GPU 上有效；内存管理器应先核验身份、范围与完成状态并发布有效内容，再通知就绪。局部复制完成不自动形成整体 readiness |
| Requests（图中省略） | Session manager → Inference backend | 满足周期提交条件且所需 KV 就绪的执行工作；携带会话历史和本次输入的关联，不强制后端按 session group 组 batch |
| Request state | Inference backend → Session manager | 返回指定会话本次请求的执行进度、完成或失败状态，供更新周期进度并判断后续驻留操作；计算完成不代表所有 KV 引用已解除。后端自己组织 batch 并推进执行 step，不要求 session manager 逐 step 发起执行；状态通知粒度由对接协议确定 |
| Allocate / Free | KV memory manager → Inference backend | 请求分配恢复所需的 GPU 目标或安全释放已有 GPU 块；通过后端分配与引用权威状态执行，不能绕过在途使用条件 |
| Block state | Inference backend → KV memory manager | 返回块映射、实际分配与可用空间、有效范围及执行/共享/复制引用状态，并报告相应操作结果。计算结束不直接替代这些状态检查；不维护互相矛盾的影子分配状态 |
| 运行反馈（图中省略） | Session manager → Planner | 会话变化、实际资源需求及计划风险，供按需修正；不意味着每个 tick 都产生新计划 |

事件与请求至少须能关联到正确会话、逻辑 KV 范围及本次操作，避免取消、重复请求、计划修正或空间复用后，旧完成事件更新新的状态。具体关联标识、去重方式与新旧计划切换协议尚未冻结；保持正确关联与状态安全是要求。

新增 KV 的 incremental host backing 由 memory manager 根据可复制范围发起，成功完成后才扩展有效 host coverage。图中 Evict / Restore 只简写周期驻留操作，不涵盖或取代这条增量备份路径。恢复启动遇到空间或服务不足时须向 session manager 返回可观察状态；是否重试、延期或拒绝属于待定异常策略，不得在失败路径上发布 readiness。

<a id="figure-semantics"></a>
### 设计图的编码含义

- **左侧位置列**：CPU 对应四个组件的主机端管理逻辑，CPU + GPU 对应推理后端的调度与设备计算，GPU memory 对应各 session 的设备驻留 KV，PCIe link 对应示例中的主机—设备复制路径，Host memory 对应共享备份池。这是图示部署的定位说明，不将硬件或互连类型冻结为论文范围；transfer engine 的 CPU 逻辑负责提交和跟踪复制，不表示数据搬运本身由 CPU 逐字节执行。
- **细灰色实线箭头**：逻辑请求或状态反馈，按箭头方向和标签区分；不再用虚线编码反馈，也不表示同步调用。仅保留 backend → session manager 的单向 Request state，表达请求执行状态反馈；后端自行组织 batch 和推进执行 step，图中省略请求提交／可执行条件对接，不删除 KV readiness 与执行条件约束。backend → memory manager 的 Block state 保留独立反馈。
- **省略的反馈**：Transfer completion、KV readiness 与 planner 的运行反馈从总览图中省略以减少连线；[接口契约](#component-interface-contracts)和[运行流程](#operational-flow)仍要求这些交互，代码不得据图省掉它们。
- **彩色实线箭头**：实际 KV 复制方向。多个蓝色细箭头表示计算期间分批进行的 incremental host backing (D2H)，适用于所有正在产生新增 KV 的会话；当前快照的 A、B 均在计算，因此均绘制多个箭头。紫色粗箭头表示按计划执行的 scheduled KV restoration (H2D)。线宽区分后台增量镜像与集中恢复，不表示实测带宽或规定固定速率；两个方向均可异步执行。
- **Group state（组框与转盘）**：蓝色 Compute、紫色 Restoring、灰色 Waiting。灰色表示该组本轮计算已结束、所需 KV 尚未恢复，等待计划时机或资源；不表示已就绪等待 tick，不表示 H2D 链路或整个 GPU 空闲。
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
| Residency plan | Planner 产生，Session manager 消费 | session-to-group/phase 关系、逐会话逐出预算、恢复时机、有限预测范围及计划适用范围 |
| 会话周期进度 | Session manager | 工作与输入关联、周期/tick、原 deadline、待提交工作、正在执行的工作及阻塞原因 |
| KV 状态 | KV memory manager 与后端权威状态协调 | 逻辑范围、GPU 分配、有效 GPU 内容、有效 host coverage、执行/共享/复制引用、待回收与待恢复操作 |
| 复制进度 | KV transfer engine | 操作身份、方向、源与目标、依赖、排队/在途/成功/失败，以及对应完成事件 |

系统由时间事件与运行事件推进，不要求单一线程或单一消息队列。所有“检查条件后提交／释放／发布”的操作都必须与后端引用和状态更新协调，不能把伪代码中相邻两行理解为允许竞态的独立操作。图中的 group 颜色不能替代这些状态。

<a id="planner-flow"></a>
### Residency planner：产生可复用的驻留安排

触发来源是准入和按需修正。Planner 读取会话需求、预计增长、候选分组下的执行成本及资源状态，输出候选计划或不可行结果；不直接申请物理块或发起复制。

```python
def build_candidate_plan(session_changes, sessions, resources):
    demand = estimate_demand(sessions, session_changes, resources)
    candidate = choose_joint_plan(demand, resources)  # 求解方法待定
    # candidate 包括 phase/group、逐会话预算、恢复时机和预测范围
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

GPU 检查计入恢复目标从完整分配时开始的占用，不能只检查准入瞬间的空闲空间。检查应考虑有限范围内的历史增长，而非将所有会话的最长上下文同时预留。候选计划如何搜索、资源估计与余量如何取得、新旧计划如何安全衔接仍待确定；生成候选不等于可以立即替换正在执行的计划。正常周期沿用已生效计划。

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

提前恢复完成只使 KV 就绪，不提前释放尚未到 tick 的工作；tick 到达而 KV 缺失时也不允许计算。提交失败须保留正确的待处理与引用状态，不能标为正在执行。后端决定实际执行顺序和 batching 策略，Session manager 不构造强制执行 batch。阻塞操作由符合条件的资源变化或重试事件推进；不能忙等，也不能每次空间空出就绕过恢复时机。重试、延期、拒绝与计划修正的具体策略尚未冻结。

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

**恢复。** `target` 表示本次恢复的分配对象；整组或逐 session 的边界仍待比较决定，不从函数名推定。

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

失败、取消或旧事件的处理同样需要等待复制不再访问相关资源后才能释放引用或复用空间；“不发布”不能简化为丢弃事件而泄漏资源。`Transfer completion` 只说明某次复制成功，`KV readiness` 要求对应工作所需全部范围有效。Ready 按工作和 KV 范围核验，不要求预先采用全组共同执行的边界。

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
2. Memory manager 核验缺失范围与主机覆盖，按尚待选定的分配边界获取完整目标；空间不足则报告阻塞，不提交无目标的复制。
3. Transfer engine 执行 H2D。目标空间已计入占用，但尚未完成的内容不可被模型访问；后端可执行其他具备条件的工作。
4. Transfer engine 报告结果，memory manager 发布成功范围的有效性，并向 manager 通知满足条件的工作已就绪。
5. Session manager 同时检查周期释放、输入与执行条件后提交工作。后端按自己的执行调度策略运行，不被强制将 C 作为一个 batch。
6. 新增 KV 进入增量备份路径；计算完成触发逐出检查，安全范围释放后供后续恢复使用。下一组仍要独立满足计划、空间与传输条件，不能因 C 完成就无条件立即启动。

该链路与[接口契约](#component-interface-contracts)、[验收场景](#implementation-handoff)共同描述设计；已实现与已验证的范围仍由对应实现审计和证据说明。

<a id="release-offset-scheduling"></a>
## Phase 与准入

周期 `T` 划分为若干均匀 slot，phase offset 间隔为 `T/S`。新会话准入时分配 slot；均匀网格是当前设计选择，不声称最优，也不限定一 slot 一 session。已有会话不需要因新会话加入而重新排相位。

phase assignment 可通过 session-to-slot assignment 具体实现，将会话组织为 session group 后形成 group schedule。一个 group 可以包含多个会话；组级安排不要求合并历史、统一每会话逐出量或将整组作为原子复制单位，底层仍按每会话和每 block 的安全条件执行。成员选择、组大小与组内执行顺序尚未确定。session group 首先是调度对象，其是否形成独立贡献仍需分组算法与消融证据；机制名称继续使用 phase assignment、partial KV eviction 和 cyclic KV restoration。

准入不能仅检查空闲 slot。配置规划需要联合选择承载规模、slot 分配与每会话恢复预算，并检查整周期的瞬时显存、链路和计算安排。规划输入包括周期、上下文上限、模型计算成本、有效 GPU KV 池、主机容量及有效带宽。求解算法尚未确定。

<a id="planning-updates"></a>
### 规划与修正

主要规划在准入时完成，运行中沿用计划。其前提是单会话 KV 增长相对平稳，能够预测累计变化；这一前提仍需所选负载的测量支持。

长期历史增长可能需要低频修正；会话加入或结束是较大调整的主要时机。每周期的逐出、空间检查和恢复仍按实际状态执行，这些动作不等于重新选择全部预算。修正的触发条件、影响哪些会话及新旧计划如何衔接尚未确定。

准入规划覆盖有限的未来时间范围，根据预计的历史增长检查资源安排，不按所有会话增长到最长上下文后的需求预留全部预算。预测范围、误差余量与后续修正策略仍待确定；预测范围内的可行性不构成整个会话生命周期的服务保证。

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

H2D 路径只选择已有有效主机副本且无冲突引用的状态。逐出之前应检查后续恢复的时间与空间安排；单靠“现在有压力”不能保证下一周期可恢复。精确预算分配与增长适配规则仍待制定。

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

若提前恢复未完成，计算必须等待有效状态；不能读取未完成 KV。按需回载可以恢复缺失状态，但可能错过 deadline。具体失败处理仍待确定。

<a id="future-recomputation"></a>
### Future work：在 Planner 中加入重算决策

当前设计通过 H2D 恢复 KV，主动周期性重算留作后续工作。重算基线或后端回退不代表 Pilarius 已将重算纳入规划。

扩展方向是在 residency planner 中增加一个决策维度，选择逐出 KV 中通过计算重建的部分，其余缺失状态通过 H2D 恢复。可用重算量或两种恢复方式的分配来表达这个维度，具体参数化与区间选择留待后续研究。规划仍可沿用 phase、逐出预算、有限前瞻和低频修正的框架；重算参与的是周期内的主动恢复，不仅是失败后的回退。

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
| 容量、slot 与预算联合规划 | 候选配置检查或求解方法；有限预测范围的长度与误差余量，以及加入退出和异质会话的处理 |
| 每会话逐出量 | 安全状态选择、有效传输窗口、预算分配；低频修正的触发条件、影响范围及计划衔接 |
| session group 的恢复分配边界 | 作者要求先比较两种方案，尚未选择；详见下方[恢复分配决策](#group-restoration-allocation) |
| 时间与空间冲突 | 恢复顺序、安全余量、错过启动窗口和迟到输入的处理 |

<a id="group-restoration-allocation"></a>
### 待决：整组预分配与按 session 分配

分配方案尚未确定，须完成以下比较并由作者选择。当前图中的 group schedule 不表示已选定分配边界。

- **整组预分配（group-wide allocation）**：整组本次恢复所需的全部 GPU 目标空间可用后，再启动复制。后续不再等待本次恢复的目标分配，但可能因空间未凑齐而推迟启动，并提前占住尚未复制的目标空间。
- **按 session 分配（per-session allocation）**：沿用组级计划，各 session 在自己的恢复启动前获得完整目标空间。可能利用其他组逐步释放的空间，但后续分配仍可能受阻；须检查多个部分恢复的组是否会相互等待空间。
- 两种方案都遵守先完整分配本次恢复目标、再复制的要求；不能按已传字节渐增记账。整组分配不意味着物理连续空间或一条 DMA，按 session 分配也不意味着逐次重新规划。
- 初步比较固定 group 成员、逐出量、复制顺序与计算工作，并暂以全组所需 KV 就绪后开始批计算作为共同分析前提；该前提不是已确认的执行策略。比较分配等待、全组就绪时间、峰值显存、部分恢复占用、控制开销及 deadline miss。全组共同计算时的必要 KV 工作集不能因分阶段分配而省略。
- **关闭条件**：作者根据比较决定分配边界及计算就绪边界，明确后续空间不可用时的处理，并同步 Design 正文、图件、契约与相关评估。尚未决定时，本项必须保持未完成，不能把任一方案写成已确定或已验证的机制。

<a id="implementation-boundary"></a>
## 实现核验入口

实现覆盖及旧测量的限制见[已有证据](findings.md#implementation-audit-boundaries)；组件定位与代码修改说明见 [Agent 导航](agent/README.md)。

<a id="implementation-handoff"></a>
### 实现交接与验收入口

实现先读[四组件运行流程与伪代码](#operational-flow)，再以[组件接口](#component-interface-contracts)、[状态维度](#kv-state-model)、[安全逐出](#idle-session-eviction)和[恢复条件](#kv-prefetching)为契约；图形、颜色或回调到达顺序不能代替状态判断。代码入口与改动流程见 [Modify Engine](agent/tasks/modify-engine.md)。以下为待实现验收场景，不表示已有测试或证据覆盖：

| 场景 | 必须验证的结果 |
| --- | --- |
| D2H 未完成时请求逐出 | 不把未完成副本当成有效 host coverage；不提前释放仍有执行或复制引用的块 |
| 目标分配失败或传输服务不可用 | 不向未分配目标提交 H2D，不发布 readiness，向协调组件报告阻塞或失败 |
| 目标已分配、H2D 只完成一部分 | 从完整目标分配时计入 GPU 占用；缺失范围未全部有效前，禁止依赖它的计算 |
| H2D 提前完成或晚于计划 | 提前完成仍遵守请求释放时机；迟到如实计入服务延迟，不移动原 deadline 掩盖等待 |
| 取消、重复恢复、旧完成事件与空间复用 | 保持身份、引用和操作关联；不将旧事件发布到新状态，不重复释放或提前复用空间 |
| 一个 group 含多个 session | 历史与逐出预算保持逐会话独立，逐 block 检查安全；不强制固定执行 batch 或原子整组复制 |
| 共享物理块与后端执行并发 | 物理容量不重复记账，所有冲突引用安全后才可回收；后端与驻留管理看到一致的有效状态 |
| 计划复用与修正 | 周期执行不自动变成全量重新规划；修正的适用范围可辨认，在途操作不会因切换丢失安全约束 |

可先实现上述接口、状态区分与安全执行路径。联合预算求解、分组选择、整组／逐 session 目标分配、修正切换及异常处理策略仍须按[未决设计](#open-design-decisions)完成决策，不能从图中的四组、等间距示意或箭头先后顺序推定默认答案。主动周期性重算按[future work](#future-recomputation)处理，不扩入当前 H2D 主路径。

<a id="initial-context-preloading"></a>
初始上下文预加载属于实验准备，协议与已登记行为见 [实验设计](experiments.md#initial-context-preloading)，不属于研究机制。
