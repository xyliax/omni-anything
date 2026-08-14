# conveyor 下一批机制的实现方案研究：KV 预取、主动调度、运行时相位调整

未进入事实层的设计研究；快照日期：2026-08-13。三个机制均为现行 conveyor 主线（错开相位 + 取现货交付 + park）之上的增量，采纳后结论上移 `docs/`。文中实测数字均来自 `docs/findings.md` 与 `docs/experiment-log.md` 的保留 run；标注「推算」的数字是线性外推，仅用于定方向，不作主张。

## 共同设计原则（先于一切机制）

1. **每个机制一个开关，off = 现行行为逐字节不变**。off 位就是消融实验的对照臂；不存在「写死在主路径里的新逻辑」。三个开关正交，2³ 组合全部可跑。
2. **正确性永不依赖新机制**。预取失败退回按需回载；调度门超时自动放行；相位控制器失效退回静态槽轮。新机制只优化时序，不承担正确性。
3. **落点顺着现有分层**：gateway 机制进 conveyor gateway fork，worker 机制进 conveyor worker，引擎机制进 engine_patch 的 utility/wrapper 面。`lab/`、`tracekit/`、baseline 一律不动（tracekit 只按既有语法扩展解析）。
4. **每个机制自带证据与失效扫描**：新行为必须落在既有日志语法或其兼容扩展里，runner 的 issue 扫描同步覆盖「开了但没生效」（与 park 的零 park 扫描同形）。

---

## 机制一：KV 预取（prefetch）

### 目标

现状（FINDINGS H5）：回载由 chunk 到达调度器触发，即 FE 之后——tick→计算片 = FE 272ms + 调度 15ms + 回载 70ms ≈ 358ms 串行。预取把回载提前到与 FE 重叠，关键路径缩短一个回载时长（当前 70ms @ 330MB 尾巴，随上下文线性增长），全部让给 deadline 裕量。

### 触发点：push 触发为主，定时预测为辅（开关的两个档位）

- **push 触发**（推荐默认档）：worker 收到 chunk（`P` 事件、FE 开始前）立即发预取。回载窗口只要 ≤ FE 时长就完全藏进 FE。当前口径下 FE 272ms、回载 70ms@330MB——按实测速率推算，尾巴到 ~1GB 量级（约 2 万 token）回载才逼近 FE 窗口，接近 max_model_len 的操作域上限。**不需要预测，就有全额收益**。
- **定时预测触发**（第二档，为 FE 进程池铺路）：H5 的根治方案（FE 进程池）落地后 FE 降至 ~90ms，push 触发的重叠窗口收窄，尾巴 >~400MB（约 7500 token）就藏不完。此时在 `预计下次 push − lead` 时刻预取。**可行性依据**：槽轮走绝对网格、源头晚醒 max 1.2ms（run `20260810_183303`），下次 push 时刻在 worker 侧从历史 push 即可预测到毫秒级，无需 gateway 参与、无需协议变更。lead = 预计回载时长 + 余量，从该会话上次回载窗口自适应。
- **预取过早的代价要计入**：提前量 × 尾巴字节 = 额外驻留字节·秒。push 触发的提前量 ≈ FE（272ms / 2s 周期 = 13.6% 的尾巴驻留时间回涨）；定时触发要把 lead 压在回载时长的 1.5 倍以内，否则蚕食 park 的驻留收益（这正是 H4 驻留核算要继续覆盖的量）。

### 引擎侧实现：两个候选，推荐「匿名预载」

预取的本质是 park 的逆操作。两条路线：

**候选 A：请求态逆转（un-park）**。utility 对闲置已 park 的请求重演调度器的按需加载序列：`get_num_new_matched_tokens`（CPU 命中并 pin）→ `allocate_slots` → `update_state_after_alloc`（发起拷贝）→ 置 `WAITING_FOR_REMOTE_KVS`；完成时经 `_update_waiting_for_remote_kv`（engine_patch 已有 wrapper）把请求放回闲置态而不是进入计算。请求重新持有全部块、`num_computed_tokens` 有效，下一 chunk 走全驻留路径（十站表 5b）。
优点：完全复用既有拷贝事件与 L/R 打点。缺点：请求状态机多出「预取中」第三态（park → 预取中 → 驻留），`_omni_parked` 标志的消费逻辑、加载完成后防止被调度成 1-token 伪 prefill 的拦截，都要精确处理——状态面手术多，出错模式是请求卡死或空转一步。

**候选 B：匿名预载（推荐）**。utility 不触碰请求：按该请求的 block_hashes 找 CPU 镜像命中，从池里分配空闲块、发起 CPU→GPU 拷贝、完成后把块以原 hash 注册进 GPU prefix cache——块属于 cache，不属于请求。下一 chunk 走现有 resume 路径时 GPU hash match 直接全额认领（这正是 park 后底座的认领方式，一行都不用改）。
优点：请求状态机零改动；**天然降级**——预载块只是 cached-free，池压力下被 LRU 逐出就退回按需回载，正确性不可能受损。缺点：拷贝不能搭请求的 load event 机制，要在 engine_patch 里走一小段自定义拷贝（复用 `simple_kv_offload` 的 copy backend 与低优先流），完成回调里注册 hash。
两候选都封在 engine_patch 的 utility 面之后，worker 只管在触发点调 `prefetch(request_id)`。

### 已知麻烦与解法

| 麻烦 | 解法 |
| --- | --- |
| 拷贝在飞行中 chunk 就到了 | 候选 B 下无害：hash 尚未注册的块 match 不到，调度器照常走 CPU 按需补载；已注册的部分直接命中。规则「同一块的二次拷贝」由 CPU 侧 hash 命中判定去重 |
| 空闲引擎不轮询完成事件 | 已核实 vLLM 0.23 `_process_engine_step`：只要调度器还有请求（含 WAITING 态），无模型执行时也会 1ms 让步轮询；utility 调用本身经 input queue 唤醒主循环。N=1 极端场景下预载完成最迟在下一 chunk 的步进被确认——仍不劣于现状 |
| 预载分配挤占池、LRU 误逐他人底座 | utility 内置预算闸：池空闲低于阈值（旋钮）即拒绝预取并计数——被拒绝是正常读数，不是错误；机制二的准入门同时约束并发预载数 |
| 「开了但没生效」静默失效 | park.log 的 `L` 行加 `trigger=prefetch|demand` 键（解析端是 dict，向后兼容）；runner 增加扫描：预取开启的 run 里 demand 加载占比超阈值即 issue |
| 收益核验 | Perfetto 上回载 slice 应整体移进 FE 窗口、不再与计算 slice 相邻串行；tick→计算片中位数应缩短 ~一个回载时长 |

### 配置面

`ConveyorConfig`：`prefetch: str = "off"`（`off | push | timer`）、`prefetch_lead_s: float | None`（timer 档）、`prefetch_min_free: float`（池空闲预算闸）。校验：prefetch ≠ off 时必须 park_enabled（无 park 则无可预取）；timer 档要求 lead 落在一个周期内。CLI 暴露 `--prefetch`（逐 run 消融旋钮）。

---

## 机制二：主动调度（驻留准入门，residency governor）

### 目标与原理

现状是 tick 触发的被动串行工作流：chunk 一到就进引擎，全驻留窗口（回载→prefill→decode→park）的并发数由到达抖动决定。实测形态（H4）：全驻留会话数典型 3 个，但 FE 方差（238~528ms）偶发把 5/8 叠在一起。**容量预算必须按峰值全驻留数设计**，所以把峰值从 5 压到 4 直接兑换成 N 扫描里的容量余量；而代价只是让个别 chunk 在门口等一小段（等到某个在算的会话 park、许可证释放）。取现货交付下 deadline 裕量 ≈ 周期 − 片时长 ≈ 1.4s，等待几十毫秒不构成风险。

机制：M 张驻留许可证（asyncio 信号量）。会话的 chunk 要进入「GPU 驻留阶段」（预取/回载 + prefill + decode）前先取证；该会话本段配额完成（auto-park 发生点）即还证。M < 实测峰值即产生「稍等一小会」的整形效果。

### 落点：worker 的 IR→IA 交接点（明确否决引擎侧方案）

- **选定：worker 侧、五站流水线的 IR→IA 之间**（FE 完成后、`_add_request` 递交引擎前）。理由：FE 是 CPU 线程池资源、不参与显存争用，不应被门挡住——门只该罩住 GPU 驻留阶段；此处天然是 asyncio 单线程域（无锁问题）、每会话顺序性由 handle_inputs 自身保证；且完全不触碰引擎。
- **否决：引擎调度器内门控**。虽已核实 vLLM 0.23 的 waiting 循环对阻塞态是 skip-not-break（不会复现 FINDINGS A3 的 head-of-line 死锁），但在最热的 `schedule()` 循环里加策略态，手术面与回归面都远大于 worker 侧十几行；A3 的教训是队列语义的细节代价极高，能不进调度器就不进。

### 许可证生命周期与安全

- **取证**：机会主义两段式。push 时 `try_acquire`——拿到就立即预取（与 FE 全重叠，机制一收益保全）；没拿到则 FE 照常做，FE 完成后在门口 `await acquire`（此时才触发预取/递交）。无争用时两机制零互扰，有争用时驻留上界成立。
- **还证**：worker 观测该会话本段 token 计数到达配额（tpt）即还——这与引擎侧 auto-park 的发生点（配额停止的同一瞬间）在语义上对齐，worker 无需感知引擎事件。会话异常结束（`ended:` 路径）立即还证。
- **防泄漏（关键安全阀）**：任何许可证持有超过一个周期即强制回收 + `worker.log` 打一行 `governor reclaim`（异常信号，runner 扫描计 issue）。这是把 A3 型「一个卡死拖垮全体」挡在门外的兜底。
- **M 的下界校验**：config 校验 `M ≥ ceil(N × 片时长 / 周期) + 1`（片时长用配置的名义值），否则等待级联把片推过周期边界、必然饥饿。给出公式而不是魔法数。

### 已知麻烦与解法

| 麻烦 | 解法 |
| --- | --- |
| 门等待挤占 deadline 裕量 | 等待上界 = 最早一张证的剩余片时长（典型 ~百 ms）；验收指标里加 gate wait p99，超过周期的 10% 即黄灯 |
| 与预取的顺序矛盾（预取想早、门想晚） | 上述机会主义两段式取证：证先到手才允许预取，驻留上界严格成立 |
| 库存瞬时欠额造成假饥饿 | 门只延迟生成开始，交付仍从库存出；只要 等待+片时长 < 周期，库存回到 ~tpt。验收盯 `inv_backlog` 恒 ~tpt 不变 |
| 观测缺口 | 五站打点扩展一站：`IG <t> <sid>`（取证完成），IR→IG 即门等待时长；tracekit 的 ingest 三段扩为四段（解析端 zip 顺序加一项即可） |
| 「开了但没生效」 | manifest 记 M；tracekit 从 park.log 派生「并发全驻留数」曲线，验收断言 max ≤ M；runner 扫描 reclaim 行 |

### 配置面

`governor_permits: int | None = None`（None = off = 现行）；CLI 暴露 `--governor-permits`。与 park 无硬依赖（无 park 时门仍能整形计算重叠，但主要收益来自驻留，文档注明推荐组合）。

---

## 机制三：运行时相位调整（adaptive phase）

### 目标与理想形态

现状：slot = 到达序 mod slots，250ms 均匀间隔，admission 后永不变。均匀间隔隐含「各会话计算成本相同」；实际成本 ∝ 上下文长度（prefill+回载随 L 增长），会话间异构时均匀相位不再最优。

理想目标有明确的数学形态：设各会话预期占用 busy_i，Σbusy_i < T 时存在零重叠的**链式排布**（fire_{i+1} = fire_i + busy_i，计算窗口首尾相接，全驻留并发恒 1）；Σbusy_i > T 时退化为按 busy_i 加权的间隔（重叠率均匀化）。这与机制二互为表里：**相位是前馈（按预测排开需求），准入门是反馈（预测失准时兜底封顶）**——相位调得越好，门越少绑定。

### 成本信号：先用零协议改动的年龄模型，再上协议扩展

- **第一档（无协议变更）：gateway 侧年龄模型**。本负载下 L(t) = L0 + 增长率 × t 是确定函数，gateway 知道每个会话的 admission 时刻与（若有）重连历史——busy_i 可由年龄直接估计。对当前合成负载（同龄同 seed）这退化为均匀相位 = 现状，异构性只来自不同入场时刻，恰好是模型能覆盖的部分。
- **第二档：协议扩展回传实测**。`SessionOutput` 增加 `slice_ms`（上段实测时长）与 `context_tokens` 字段。protobuf 加字段向后兼容（旧读方忽略未知字段），且 gRPC 契约只存在于 conveyor gateway ↔ conveyor worker 之间——两端都是本仓 fork，pin 的 proto 与 baseline 臂不受影响。做法：conveyor 拥有自己的 proto 副本（fork 自 pin，只加字段），Go/Python stub 各自重新生成；ORIGIN 节记录分歧。这一步同时为将来的注入语义铺协议路。

### 相位移动的安全语义（本机制最大的坑，必须先想清楚）

移动一个会话的发射时刻，等价于制造一个非 2s 的过渡周期，三条约束：

1. **提前移**：过渡周期变短 → 该次采到的音频 < 2s → 音频 token 变少（合法，但改变负载形状）；且上一段的完成余量必须盖住提前量。约束：单次移动 ≤ min(完成余量, 一个槽距)；实测完成余量 ~1.4s，绑定约束是槽距。
2. **推后移**：过渡周期变长 → 该次音频 > 2s，而段配额仍是 tpt=25 → **内容对应关系永久滞后一个移动量**（B5/F7 的同族现象，速率上无害、语义上要记账）。约束：把单次移动量与累计移动量都记进 gateway_ticks，作废「无声漂移」的可能。
3. **限速与迟滞**：每会话每 k 个周期至多移一步、每步 ≤ 槽距/2；控制器目标函数变化小于迟滞带宽时不动作——防振荡（会话互相追逐）。饥饿豁免逻辑（fdFull）不因移动重置。

### 分两期实现

- **一期：槽位重指派（推荐先做）**。保留槽轮结构，只允许会话在周期边界换槽（粒度 250ms）。gateway_ticks 语法不变，加 `moved=<sid>:<from>:<to>` 注记。控制器：每 10 个周期重解一次指派（贪心：按 busy 估计降序，放到预测重叠峰最小的槽），每周期最多移一个会话。N ≤ 16 时槽粒度足够表达链式排布的近似。
- **二期：连续相位**。槽轮换成每会话 next-fire 最小堆（fire_s = t0 + k×T + phase_s，仍是绝对网格、晚醒自纠），phase_s 连续可调。触发条件：一期证据显示槽粒度是残余重叠的主因时才做。trace 语法变更（slot 字段语义扩展）与 tracekit 解析同步走。

### 已知麻烦与解法

| 麻烦 | 解法 |
| --- | --- |
| 控制器振荡 | 限速 + 迟滞 + 每周期至多动一个会话；控制器只看滑动窗口均值不看瞬时 |
| 与定时预取互扰（worker 按历史 push 预测下次 push） | 移动限速 ≤ 槽距/2 保证预测误差有界；push 触发档完全不受影响；worker 观测到 push 偏离预测超阈值时自动降级到 push 档一个周期 |
| 短音频片踩到编码器下限 | 现有首片守卫已有 ~40ms 下限检查；移动量约束（≤ 槽距）远离该下限 |
| 评估口径被移动污染 | 每会话周期指标（间距、late_ms）按移动事件分段统计；验收要求非移动周期的间距仍精确 T |
| 「开了但没生效 / 开了变坏」 | manifest 记策略与参数；验收对照静态臂：全驻留峰值下降且零 starve、tick→prefill 分布不劣化 |

### 配置面

gateway flag `--phase-policy static|adaptive`（默认 static = 现行），`--phase-step-ms`、`--phase-epoch-ticks`（限速参数）。runner 从 `ConveyorConfig.phase_policy` 翻译；manifest 全记录。

---

## 三机制关系与实施顺序

```
相位（前馈：把需求按成本排开）──减少──▶ 门等待（反馈：峰值封顶）
        │                                    │
        └──── 都缩短/稳定驻留窗口 ────────────┘
                        │
              预取（把回载挪出关键路径，驻留窗口起点提前、终点不变）
```

建议顺序：**预取 → 准入门 → 相位**。预取独立且收益确定（−70ms 起）；准入门给出全驻留并发的硬上界与新观测（IG 站、并发全驻留曲线），相位控制器的验收正需要这些仪器；相位最后做，先一期后二期。每步都是独立开关、独立消融臂。

## 结构影响审计

| 触碰面 | 内容 | 不变量保持 |
| --- | --- | --- |
| `experiments/conveyor/config/` | 三组新旋钮 + 校验 | 默认值只声明一次；off 默认 |
| `experiments/conveyor/worker/stream_server.py` | 预取触发点、准入门（IR→IA 十几行）、IG 打点 | 取现货语义、库存口径、哨兵约定不动 |
| `experiments/conveyor/worker/engine_patch/` | prefetch utility（候选 B）+ L 行 trigger 键 | park 语义不动；utility 面扩展与 park 同形 |
| `experiments/conveyor/gateway/` | phase-policy 控制器（一期槽位重指派） | 绝对网格、取现货指标口径、`[starve]` 契约不动 |
| `tracekit/` | ingest 四段、L 行新键、moved 注记、并发全驻留派生曲线 | 既有行语法向后兼容 |
| runner issue 扫描 | 预取未生效 / governor reclaim / 移动记账缺失 | 与零 park 扫描同形，`tests/test_run_validation.py` 加样例行钉住 |
| `lab/`、baseline、pin | 零触碰 | — |

消融矩阵：`--prefetch off|push|timer` × `--governor-permits ∅|M` × `--phase-policy static|adaptive`，全组合经 CLI 可跑，manifest 完整记录，对照臂就是全 off。
