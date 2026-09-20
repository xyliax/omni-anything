# 图件重设计工作指南（讨论迭代中）

作用：指导图 1（动机）与图 3（设计总览，现文件名 `figure2-design-overview.*`）的重画，记录已讨论定案的设计决策、理由与待决项，随作者讨论持续迭代。本文不是事实 owner：语义与事件模型以 [figure-1 spec](figure-1-motivated-example.md)、[figure-2 spec](figure-2-design-overview.md) 和[机制理解审计](figure-design-understanding.md)为准；叙事分工以 [PAPER.md 图件计划](../../docs/PAPER.md#figure-plan)为准。设计决策冻结后同步进对应 spec 的 layout/visual-vocabulary 节，本文保留讨论记录。

## 0. 决策状态

已定（作者确认后打钩，未打钩为本指南的当前建议）：

- [ ] D1 图 1(a) 聚合条：合并为一条"归一化 + idle/computing 堆叠面积"条（替代两条绝对数值小条）
- [ ] D2 图 1(a) 相位：**对齐（共享 tick 默认）**，依据全驻留下容量越线的相位无关性（2026-09-20 修订，替代原"不规则相位"建议）；对齐同时作为 Panel A baseline 与图 3 反事实，两图 baseline 一致
- [ ] D3 图 1(b) 对照：reactive restoration（通用路线，不点名系统）；Metronome 不进图 1
- [ ] D9 图 1(a) compute 条口径：改为"每周期 GPU 计算时间 vs 周期预算"（替代"并发会话数 vs ceiling=4"，后者在对齐下打满且虚构每会话独占 GPU）
- [ ] D4 图 1(b) 标签：`Reactive` vs `Cyclic (Pilarius)`，或 `Reactive` vs `Pilarius`
- [ ] D5 图 1(a) 幽灵菱形（releases known ahead 的前瞻虚线菱形）：加 / 不加
- [ ] D6 两图统一"色相=会话、明度/纹理=状态"配色（Okabe-Ito 四色相）
- [ ] D7 图 3 pool 条改按会话堆叠面积，并绘出 aligned-phase 反事实包络（y 轴放宽至 15–35）
- [ ] D8 图 3 因果链 ①→②→③→④ 加细弧线箭头串联（全图唯一一组箭头）

## 1. 两图分工

| 图 | 位置 | 一句话 takeaway |
| --- | --- | --- |
| 图 1 动机 | Intro（§1②④） | 多会话周期负载下，历史 KV 的驻留需求先于计算需求触及 GPU 容量；周期负载提前承诺下一次使用时刻，恢复可移出关键路径且逐周期重复 |
| 图 3 设计总览 | §4① | 统一相位网格摊开峰值、空闲逐出在链路预算内回收容量、预取在下次 release 前恢复；容量因果链（deferred→evict→prefetch→ready）证明三机制协同 |

减负事实：张力的实测版本由图 2（张力测量，待 Q1）承担，块级状态语义由图 4（状态机）承担；两张叙事图不承载测量与状态机细节。两图 caption 均保留 "authored illustration, not measurements" 声明。

## 2. 相位结构：三种取值、依据与叙事桥

图 1 与图 3 涉及三种相位结构，各有明确位置，不得互换：

| 相位结构 | 谁决定 | 图中角色 |
| --- | --- | --- |
| 任意到达相位 | 负载到达自然给定，无人控制 | 只在 caption caveat 里点明，不作为画面主体 |
| 全对齐（共享 tick） | tick 式引擎的结构性默认（见下） | **图 1(a) baseline 主体** + 图 3 反事实包络（同一 baseline，两图一致）；Q4 消融的对照条件 |
| 均匀网格（slot） | Pilarius 机制：接纳时一次指派、终身固定（release-offset scheduling，第三级时间信息） | 图 3 主体 |

**图 1(a) 画对齐相位的依据（2026-09-20 修订，替代原"画随机相位"建议）：**

1. **越线与相位无关，所以对齐安全。** 全驻留参照下，每会话驻留是只升不降的阶梯，聚合为阶梯之和；改变相位只把每会话那一小级台阶挪到周期内不同位置，不改变爬升高度，也不改变它在第几个周期穿过容量线。对齐与随机在同一周期越线，只是周期内纹波形状不同。故 "memory binds before compute" 这一核心主张在两种相位下完全相同，不存在"挑了有利相位"的问题——怎么排都越线。
2. **对齐是诚实的默认对手。** 共享 tick 的引擎（Metronome，及任何带全局 tick 的 continuous-batching 网关）确实把所有会话对齐（`gateway-go/main.go::tickLoop` 单一全局循环）；随机相位是"每会话独立时钟"的引擎才有的样子。我们最接近的 baseline 是 tick 式服务，对齐才是诚实的对手。任意到达相位这一事实退入 caption 一句 caveat（"到达是任意的，是共享 tick 引擎把它们对齐的"），使纯 continuous-batching baseline 的 reviewer 也无从指控藏匿。
3. **对齐给 staggering 一个天然的 "before"，且铺垫其深层动机。** 相位机制的收益（spread peaks / 摊开恢复需求）只有对着**集中**的 baseline 才读得出；对齐=集中（所有会话驻留峰值与空闲间隙重合），随机自身已部分摊开，对比会糊。更关键：对齐下所有会话一起算、一起 idle，要复用显存就得在共享空闲间隙里同时逐出、又在下个 tick 前同时恢复所有会话——一个同时砸向共享链路的恢复突发。错开就是去同步它，使任一时刻只有少量会话临近恢复期限，链路可逐个服务。这是错开的真正理由（不只降峰值，而是把恢复需求在链路上摊开），对齐的 Panel A 恰好把它铺垫出来。
4. **一步干净的动作 + 两图 baseline 一致。** 对齐→错开是一个故事；随机→对齐(Metronome)→再错开是两个让人困惑的动作。且 Panel A 对齐后与图 3 反事实包络是同一 baseline（对齐/共享 tick），全程贯穿一致（原设计里 Panel A 随机、图 3 反事实对齐，两图 baseline 不一致，本次修订顺带消除）。
5. 画均匀网格仍不可：那是本文机制本身（Pilarius 的 slot 指派）。

**使对齐诚实的两个条件（落进 spec）：**

- **compute 条改口径（D9）。** "并发会话数 vs ceiling=4" 在对齐下会打满（4 个一起 batch），且虚构每会话独占 GPU。换成"每周期 GPU 计算时间 vs 周期预算"——诚实显示时间余量，与相位无关，也正是机制审计早就要求的口径。
- **别让读者以为"错开就够了"。** 不够：全驻留在任何相位下都越线（第 1 点），错开只有和逐出配合才有用。Panel A 的信息保持为"容量在任何相位下都先 binds → 必须逐出 idle KV"，图 3 再展示错开如何让逐出+恢复在共享链路上可行。

**Metronome 的相位处理（调研结论，2026-09-20，来源：arXiv 2607.02640 HTML 全文 + `third_party/metronome` pin）：**

- 全部会话共享单一全局 tick，每 tick 一次 batched Step 服务所有 due 会话（论文 Fig 2 caption "one batch of all due sessions"；§4 "once per tick issues a single batched Step over gRPC for all due sessions"；代码 `gateway-go/main.go::tickLoop` 单一全局定时循环）。其负载中每会话每帧都 due，即所有会话相位完全对齐。
- 论文提到的 "phase-staggered real-audio streams"（§3、§5.1）是错开音频**内容**以防 prefix-cache 去重虚增容量，属测量方法学，与 tick 调度无关。
- 对齐没有被作为决策论证：它从 continuous batching 作为服务原语、以及逐 tick 可调度性判定（T_k(N) ≤ B）的实时任务框架中结构性地落出；batch 共享只在 admission control 的论证中被引用为前提。论文从未考虑去同步/错开 tick 的替代方案。
- Metronome 也确实不需要错开：windowed KV 使每会话状态有界（~0.2% pool），峰值重叠不威胁容量，且无恢复流量需要摊开。相位结构在"全历史保留 + 逐出/恢复"的设定下才开始起作用——这正是本文的设计空间。

**叙事桥（对齐 baseline 贯穿两图 → 图 3 错开）：** 正文 §4.2 按一个递进展开——负载到达给出任意相位（caption caveat 点明，问题与之无关）；现有周期式引擎把所有会话量化到一个共享 tick 上，这是结构性默认而非对抗性选择，它最大化 batch 聚合，代价是同步了所有会话的驻留峰值与恢复期限（图 1(a) 的 baseline 与图 3 反事实是**同一条对齐 baseline**，标签统一写 "aligned (shared tick)" 而非 "random"）；Pilarius 在接纳时把会话指派到错开的 slot 网格，去同步那个砸向共享链路的恢复突发（图 3 主体）。全弧只有一个动作——从对齐到错开——不再有"随机→对齐"的多余跳转。同时保留审计的告诫：对齐 batch 聚合的收益真实存在（错开可能增加权重读与迭代成本），offset 收益的归因须由 Q4 的"同步输入 + 引擎内部流水线"对照裁决，图不预支该结论。

## 3. 共享视觉系统（两图一致）

| 元素 | 编码 | 备注 |
| --- | --- | --- |
| 会话身份 | Okabe-Ito 四色相（D6） | 图 1(b) 单会话用中性蓝 |
| 计算 / idle 驻留 / in-flight | 同色相深 / 浅 / hatch | 明度差保证灰度可读；泳道身份由标签兜底 |
| release | 空心菱形 + 细虚线竖参考线 | RT 调度标准记法 |
| 代价/失败 | 红色，全图唯一警示色 | 仅图 1 越线点、越线区与 reactive stall 段使用 |
| capacity / ceiling | 黑（或深灰）虚线 | 橙色让位给会话色相 |
| 字号 | 注释 8 pt，轴/泳道标签 9 pt | 沿用 spec 硬预算 |
| 工具 | matplotlib + 事件模型断言 | 聚合曲线永远由 lane 事件模型推导并断言，不手画 |

## 4. 图 1 详细画法

### Panel (a)：多会话周期负载（宽 ~60%）

多会话要传达的四个事实与视觉证据一一对应：每会话历史逐周期上涨（泳道内 +1 台阶）；任意时刻多数会话 idle 而 KV 仍驻留（浅色带占泳道大部）；阶梯之和越过容量（聚合条红点）；计算从未饱和（聚合条低位线）。

- 4 条泳道，不多画；规模感（N 个会话）放 caption。带高=驻留块数（初始 4/4/4/5），release 空心菱形，release 后 330 ms 深色计算段，其余浅色，计算尾 +1 块。**相位对齐（共享 tick）：4 会话的 release 都落在周期边界 0/1000/2000 ms**，同一周期的 4 个菱形纵向对齐成一列——同步本身就是画面信息。横轴 0–3000 ms。（后果：对齐下任一时刻全部会话同态——共 330 ms 全在计算、其余 670 ms 全 idle；"多数会话 idle 而 KV 仍驻留"从"跨会话同时"变为"每周期 67% 时间"，见下条聚合条处理。）
- S1 首周期上方 `⟵ T ⟶` 尺寸箭头；idle 最长的泳道标注一次 `KV-idle interval` 括号（植入 §3 核心对象）。
- D5（可选）：横轴右端留 ~200 ms，画各泳道下一菱形的虚线幽灵版，注释 "releases known ahead"，把机会埋进问题面板。
- 聚合条（D1）：y 轴为占各自上限的比例（0–110%），100% 一条黑虚线。KV 需求画堆叠面积——下层深色=正在计算会话的 KV、上层浅色=idle 会话的 KV，色调与泳道严格一致。对齐下深/浅随时间整体切换（共享计算窗全深、共享 idle 窗全浅），面积高度=总驻留块数的阶梯，逐周期上涨、第三周期穿 100% 线；**把越线交点放在 idle 窗内读**——交点处整条面积全是浅色，"此刻全部 KV 都 idle，却已耗尽容量" 比跨会话版本更无歧义地铺垫 §4.3。交点红色实心点注 "exceeds"，越线段浅红渐变。
- 计算占用条（D9 改口径）：不再画"并发会话数 vs ceiling=4"（对齐下打满且虚构每会话独占 GPU）。改画**每周期 GPU 计算时间 vs 周期预算**——330/1000 ≈ 33%，一条低位线配 100% 预算虚线，诚实显示时间余量且与相位无关。一眼两结论：面积到顶（memory 越线）时计算时间条仍在山脚（compute 有余量，memory binds first）；越线面积全是浅色（容量被 idle KV 吃掉）。绝对数（capacity = 25 blocks）移入 caption。
- Panel 小标题改论断式：如 "(a) KV binds before compute"。

### Panel (b)：恢复时机对比（宽 ~40%）

单会话、两周期（release 500/1500 ms）、上下两条 band 共享时间轴，历史 9 块、恢复 60 ms、idle 保留 3 块：

- 上 Reactive：release 菱形处才开始恢复（500–560 hatch），计算 560 起。release→计算开始的段用红色 hatch/描边强调（全图第二处警示红，与 (a) 红点同族语义：付出的代价）；第二周期原样重复（paid every period）。
- 下 Cyclic (Pilarius)：恢复 340–400 提前完成，浅色驻留等到 release，计算从菱形准时开始；计算尾台阶下落注 "evict"（保留 3 块）；第二周期画面全等——重复本身是 "cyclic" 的图形定义。
- 代价对称呈现：下方从恢复开始到 release 的提前驻留段用极浅底纹标出，caption 一句 "at the cost of occupying capacity earlier"。上方代价=红色时间段，下方代价=浅色空间×时间段。
- 一条细虚线竖穿两 band、落在每个 release 上——读者沿线上下对比"同一时刻，上面计算未开始、下面恰好开始"。这是 (b) 最重要的一根线。

### 30 秒阅读路径（完成判据）

浅色带在涨 → 堆叠面积爬坡、红点越线、越线部分几乎全是浅色 → 右边：reactive 每周期在红色里等待 vs 沿已知 release 提前恢复、计算准时、逐周期重复。三步各有唯一视觉焦点，无一步依赖 caption。

### Scope guards（沿用 spec 并强化）

相位对齐（共享 tick），断言从 non-uniform 翻为 aligned（releases 落在周期边界，同期菱形纵向对齐）；caption 一句 caveat 点明"到达是任意的，是共享 tick 引擎把它们对齐的"，并保留"越线与相位无关"一句作为正面防御（reviewer 换纯 continuous-batching baseline 也无从指控）；(b) 不出现容量门控、传输竞争（图 3 内容）；对照标签用通用词 reactive，不点名系统；caption 保留 illustration 声明。注意：spec（figure-1-motivated-example.md）与 render 脚本当前仍断言 non-uniform，冻结 D2 后需同步翻转断言，勿遗留矛盾。

## 5. 图 3 重设计要点（待逐项细化讨论）

1. D6 配色统一后：H2D 轨道四色窗口轮流出现，"共享链路时分复用"无字自明；S1 逐出→S3 预取的因果由颜色接力讲述。
2. D7 pool 条：按会话堆叠面积 + aligned-phase 反事实包络（灰虚线，峰值 33 越线），y 轴放宽 15–35（顺带消除截断轴顾虑）。反事实标签 "aligned (shared tick)"。
3. D8 因果链细弧线箭头 ①→②→③→④，全图唯一箭头组。
4. 机制短标签与 §4 小节词汇一致："offset grid"（顶部）、"evict"（②处）、"prefetch"（③处）。
5. H2D 串行窗口保留真实间隙；caption 点一句 serialized windows bound eviction depth。

## 6. 参考图库（体裁对标，2026-09-19 逐篇核验图注）

| 参考 | 借什么 |
| --- | --- |
| InferCept (ICML'24) Fig 1 | 时间×资源×策略三合一；hatch 编码被浪费的资源；警示色只给代价 |
| HCache (EuroSys'25) Fig 1/4/5 | 恢复方式并排时序对比；layer-wise overlap 流水线画法 |
| Metronome Fig 3/5 | 概念时间线对比的克制画法；occupancy 爬容量线的曲线叙事（同时是需要视觉差异化的 baseline） |
| CachedAttention (ATC'24) Fig 6–8 | 双 stream 泳道的 preload/save overlap；buffer 不足的"不完美 overlap"对照版本 |
| GPipe/1F1B 一族 pipeline 图 | 色相=身份跨泳道追踪；bubble 留白即信息 |
| RT 调度教科书 Gantt | release/deadline/period 记号系统 |

近邻文献（Metronome/LiveServe/Pensieve/VoxServe/vLLM-Omni）均无多会话 KV Gantt；该体裁是本文的叙事资产，保留多会话画法，不退回单会话。

## 7. 渲染与审查工作流

1. 改 spec（参数、事件模型）→ 改 `scripts/render-kv-figures.py` 渲染层 → `python eurosys2027/scripts/render-kv-figures.py` 重生成。
2. 每轮渲染后做视觉审查：彩色 + 灰度（`build/kv-figure-review/`）对照本指南的阅读路径与 §6 参考图；机制正确性对照[理解审计](figure-design-understanding.md)。
3. 文档改动跑 `python -m pytest tests/test_narrative_scope.py`；代码/spec 改动从仓库根跑全量 `python -m pytest` 并在 `eurosys2027/` 跑 `make check`。

## 变更日志

- 2026-09-20：建档。录入两图分工、相位结构论证与 Metronome 调研（全局 tick 对齐为结构性默认，未论证、未考虑错开替代；phase-staggered 仅指音频内容防 prefix-cache 去重）、叙事桥、共享视觉系统、图 1 详细画法、图 3 要点、参考图库与工作流。决策 D1–D8 待作者拍板。
- 2026-09-20 修订：作者 push——既然对齐是自然默认，Panel A 就该画对齐。据"全驻留越线与相位无关"（对齐安全）+ 对齐是诚实默认对手 + 对齐给 staggering 天然 before 并铺垫其"去同步共享链路恢复突发"的深层动机 + 两图 baseline 一致，D2 从"不规则相位"翻为"对齐（共享 tick）"；新增 D9（compute 条改"每周期 GPU 时间 vs 预算"）。同步改写 §2 依据与叙事桥、§4 Panel(a) 相位/聚合条/compute 条/scope guards。任意到达相位退为 caption caveat。spec 与 render 脚本的 non-uniform 断言待 D2 冻结后同步翻转。
