# 图件手绘指南：图 1 动机与图 3 设计总览

## 0. 用途与边界

本文供作者用 Draw.io 手绘图 1（动机实例时间轴）与图 3（设计总览）使用，是这两张图唯一的画图指南；它合并了此前的中文工作指南（2026-09-20）、两份 v4 英文绘图契约与 2026-09-08 的机制理解审计。本文记录已定与待定的设计决策、两图的事件模型与参数表、共享视觉规范、caption 草稿与审阅流程。

本文不是事实 owner。问题定义、周期、release 偏移与全历史语义以 [docs/problem.md](../../docs/problem.md) 为准；KV 状态、逐出与恢复语义以 [docs/system.md](../../docs/system.md) 为准；实现成熟度与证据以 [docs/findings.md](../../docs/findings.md) 为准；图号、图件计划与叙事分工以 [docs/PAPER.md 图件计划](../../docs/PAPER.md#figure-plan)为准。与 owner 冲突时先改 owner，再改本文，最后改图。

两图都是作者选定的机制示意，不是实测结果、重标定的 trace、模拟器结果或性能预测。图中画的是候选的、面向下一次使用时刻的恢复安排，不表明当前实现已经按图中方式在 release 前调度恢复；不得由图推断实现状态，也不得由图推断永久的 cache 保护、普遍的主机覆盖门控、全局按期限排序的恢复队列或已测得的预取收益。

<a id="figure-numbering"></a>
## 1. 图号与文件名

图号统一按 PAPER.md 图件计划：图 1 为动机实例时间轴，图 2 为张力测量（待 Q1 数据的实测图，不在本指南范围），图 3 为设计总览。文件名保持不变：`figures/figure1-motivated-example.*` 对应图 1，`figures/figure2-design-overview.*` 对应图 3；文件名中的 2 是历史编号，本文所有"图 3"均指后者。

<a id="decision-status"></a>
## 2. 决策状态

判定标准：v4 契约的 layout 与 caption 已按该决策写成即为已定；契约未采纳的标为待定，并注明契约当前的做法。待定项不进入当前画法，需作者拍板后先改本文相应小节，再改图。

| 编号 | 内容 | 状态 | 依据或当前做法 |
| --- | --- | --- | --- |
| D1 | 图 1(a) 聚合条合并为"归一化 + idle/computing 堆叠面积"一条 | 待定 | 契约当前为单条驻留 KV 总量阶梯对容量虚线，无数值刻度，不归一化、不按状态堆叠；越线处只用 "exceeds" 短注释 |
| D2 | 图 1(a) 相位对齐（共享 tick），同时作为图 1 baseline 与图 3 对照线 | 已定 | 契约 Panel (a) 为 aligned rounds，四会话 release 在 0、T、2T 纵向对齐；图 3 pool 子图的浅灰对照阶梯即同一对齐 baseline |
| D3 | 图 1(b) 对照为通用 reactive restoration，不点名系统；Metronome 不进图 1 | 已定 | 契约行标签与 caption 均用 reactive，图 1 不出现任何系统名 |
| D4 | 图 1(b) 行标签 `Reactive` 对 `Pilarius` | 已定 | 契约两行标签为 Reactive 与 Pilarius；`Cyclic (Pilarius)` 变体未采用 |
| D5 | 图 1(a) 横轴右端预留、画下一 release 的虚线幽灵菱形并注 "releases known ahead" | 待定 | 契约横轴止于 3T，无幽灵菱形，"release 已知"的信息由 caption 承载 |
| D6 | 两图统一"色相=会话、明度/纹理=状态"配色（Okabe-Ito 四色相），代价与失败用红色警示 | 待定 | 契约为单色相编码（深蓝计算、浅蓝 idle 驻留、橙 hatch 在途），会话身份由泳道标签承担，无红色警示色；见 §5 |
| D7 | 图 3 pool 条按会话堆叠面积并放宽数值轴至 15–35 | 待定 | 契约 pool 子图为总量阶梯，无数值刻度（数字纪律不允许数值轴）；对齐对照阶梯这一部分已落地，堆叠与数值轴未采纳 |
| D8 | 图 3 因果链 ①→②→③→④ 用细弧线箭头串联 | 待定 | 契约用带圈序号 1–4 各配一个锚点圆点，不画箭头；因果由 caption 叙述 |
| D9 | 图 1(a) 计算条口径改为"每周期 GPU 计算时间对周期预算"，取消"并发会话数对上限 4" | 部分已定 | 取消旧条已落地：契约已无并发会话数条。新口径的独立计算时间条尚未画入契约，时间余量目前由各泳道内约 0.35T 的同步爆发段与 caption 的 "compute is idle most of each period" 承载；是否另设该条待作者拍板 |

<a id="figure-division"></a>
## 3. 两图分工

| 图 | 位置 | 一句话 takeaway |
| --- | --- | --- |
| 图 1 动机 | Intro（§1②④） | 多会话周期负载下，历史 KV 的驻留需求先于计算需求触及 GPU 容量；周期负载提前承诺下一次使用时刻，恢复可移出关键路径且逐周期重复 |
| 图 3 设计总览 | §4① | 统一相位网格摊开峰值、空闲逐出在链路预算内回收容量、预取在下次 release 前恢复；容量因果链（deferred→evict→prefetch→ready）证明三机制协同 |

减负事实：张力的实测版本由图 2（张力测量，待 Q1）承担，块级状态语义由图 4（状态机）承担；两张叙事图不承载测量与状态机细节。两图 caption 均保留"authored illustration, not measurements"声明。图 1 的对照维度是恢复时机，不出现容量门控、共享链路预算或均匀相位网格，这些属于图 3，不得由图 1 反推。

<a id="phase-structure"></a>
## 4. 相位结构：三种取值、依据与叙事桥

图 1 与图 3 涉及三种相位结构，各有明确位置，不得互换：

| 相位结构 | 谁决定 | 图中角色 |
| --- | --- | --- |
| 任意到达相位 | 负载到达自然给定，无人控制 | 只在 caption caveat 里点明，不作为画面主体 |
| 全对齐（共享 tick） | tick 式引擎的结构性默认（见下） | **图 1(a) baseline 主体** + 图 3 pool 子图的对照阶梯（同一 baseline，两图一致）；Q4 消融的对照条件 |
| 均匀网格（slot） | Pilarius 机制：接纳时一次指派、终身固定（release-offset scheduling，第三级时间信息） | 图 3 主体 |

**图 1(a) 画对齐相位的依据（2026-09-20 修订，替代原"画随机相位"建议）：**

1. **越线与相位无关，所以对齐安全。** 全驻留参照下，每会话驻留是只升不降的阶梯，聚合为阶梯之和；改变相位只把每会话那一小级台阶挪到周期内不同位置，不改变爬升高度，也不改变它在第几个周期穿过容量线。对齐与随机在同一周期越线，只是周期内纹波形状不同。故"memory binds before compute"这一核心主张在两种相位下完全相同，不存在"挑了有利相位"的问题。
2. **对齐是诚实的默认对手。** 共享 tick 的引擎（Metronome，及任何带全局 tick 的 continuous-batching 网关）把所有会话对齐；随机相位是"每会话独立时钟"的引擎才有的样子。本文最接近的 baseline 是 tick 式服务，对齐才是诚实的对手。对齐归因于服务侧而非负载：轮次式周期服务把所有会话的更新放在同步轮次里执行，因为对齐最大化 batch 效率，这是既有系统面向吞吐的默认，不是为本图构造的产物；caption 必须把对齐归因于 baseline 调度器。任意到达相位这一事实退入 caption 一句 caveat（"到达是任意的，是共享 tick 引擎把它们对齐的"），使持纯 continuous-batching baseline 的 reviewer 也无从指控藏匿。
3. **对齐给 staggering 一个天然的 "before"，且铺垫其深层动机。** 相位机制的收益（摊开峰值与恢复需求）只有对着集中的 baseline 才读得出；对齐即集中（所有会话驻留峰值与空闲间隙重合），随机自身已部分摊开，对比会糊。更关键：对齐下所有会话一起算、一起 idle，要复用显存就得在共享空闲间隙里同时逐出、又在下个 tick 前同时恢复所有会话，形成一个同时砸向共享链路的恢复突发。错开就是去同步它，使任一时刻只有少量会话临近恢复期限，链路可逐个服务。这是错开的真正理由（不只降峰值，而是把恢复需求在链路上摊开），对齐的 Panel (a) 恰好把它铺垫出来。
4. **一步干净的动作 + 两图 baseline 一致。** 对齐→错开是一个故事；随机→对齐→再错开是两个让人困惑的动作。Panel (a) 对齐后与图 3 pool 子图的对照阶梯是同一 baseline，全程一致。
5. 画均匀网格仍不可：那是本文机制本身（Pilarius 的 slot 指派）。

**使对齐诚实的三个条件：**

- **计算条口径（D9，部分已定）。** "并发会话数对上限 4"在对齐下会打满（4 个一起 batch），且虚构每会话独占 GPU，该条已取消。若要单独表现时间余量，只能用"每周期 GPU 计算时间对周期预算"的口径，它与相位无关，也正是机制审计早已要求的口径；是否加这一条见 §2。
- **对齐等待的代价不画成免费。** 把分散到达对齐到共享轮次，每会话首次提交最多付出一个周期的对齐等待；该代价由测量语义（owner：docs/experiments.md）追踪，在 caption 里用一个从句点明，不占像素。
- **别让读者以为"错开就够了"。** 不够：全驻留在任何相位下都越线（第 1 点），错开只有和逐出配合才有用。Panel (a) 的信息保持为"容量在任何相位下都先 binds，因此必须逐出 idle KV"，图 3 再展示错开如何让逐出与恢复在共享链路上可行。

**Metronome 的相位处理（已核验，2026-09-20，来源：arXiv 2607.02640 全文与 `third_party/metronome` pin）：**

- 全部会话共享单一全局 tick，每 tick 一次 batched Step 服务所有 due 会话（论文 Fig 2 caption "one batch of all due sessions"；§4 "once per tick issues a single batched Step over gRPC for all due sessions"；pin 中的网关为单一全局定时循环）。其负载中每会话每帧都 due，即所有会话相位完全对齐。
- 论文提到的 "phase-staggered real-audio streams"（§3、§5.1）是错开音频内容以防 prefix-cache 去重虚增容量，属测量方法学，与 tick 调度无关。
- 对齐没有被作为决策论证：它从 continuous batching 作为服务原语、以及逐 tick 可调度性判定的实时任务框架中结构性地落出；batch 共享只在 admission control 的论证中被引用为前提。论文从未考虑去同步或错开 tick 的替代方案。
- Metronome 也确实不需要错开：windowed KV 使每会话状态有界，峰值重叠不威胁容量，且无恢复流量需要摊开。相位结构在"全历史保留 + 逐出/恢复"的设定下才开始起作用，这正是本文的设计空间。

上述核验结论取代早先契约中"对齐属性为作者回忆、尚未核验"的说法；正文引用前仍应对照论文最新版本复核一次。

**叙事桥（对齐 baseline 贯穿两图 → 图 3 错开）：** 正文 §4.2 按一个递进展开：负载到达给出任意相位（caption caveat 点明，问题与之无关）；既有周期式引擎把所有会话量化到一个共享 tick 上，这是结构性默认而非对抗性选择，它最大化 batch 聚合，代价是同步了所有会话的驻留峰值与恢复期限（图 1(a) 的 baseline 与图 3 对照阶梯是同一条对齐 baseline，图 3 中标签写 "aligned"）；Pilarius 在接纳时把会话指派到错开的 slot 网格，去同步那个砸向共享链路的恢复突发（图 3 主体）。全弧只有一个动作，即从对齐到错开。同时保留审计的告诫：对齐 batch 聚合的收益真实存在（错开可能增加权重读与迭代成本），offset 收益的归因须由 Q4 的"同步输入 + 引擎内部流水线"对照裁决，图不预支该结论。

<a id="visual-vocabulary"></a>
## 5. 两图共享的视觉规范（当前）

以下为两份 v4 契约已落地的规范，两图一致；Okabe-Ito 四色相与红色警示色属于待定决策 D6，不在此列，不得与当前规范混用。

| 元素 | 编码 |
| --- | --- |
| 计算中的 GPU KV | 深蓝 `#28769B` 实心 |
| idle 驻留 KV | 浅蓝 `#EAF2F7` 实心；带高 = 驻留块数 |
| 在途传输（H2D/D2H） | 橙 `#B87519` 斜纹 hatch，底色 `#FFF0D9` |
| 曲线与文字 | 墨 `#263642` |
| 坐标轴、相位竖线、次要记号、图 3 对齐对照线 | 灰 `#9CA9B2` |
| KV capacity | 橙色虚线（图 1）；虚线并标注单词 "capacity"（图 3） |
| release | 空心菱形 |
| 新追加 KV | 小 + 号（图 3） |
| caption 叙述的事件 | 带圈序号，每个序号在其事件坐标处配一个小锚点圆点 |
| 字号 | 注释 8 pt，轴、泳道与 panel 标签 9 pt；无衬线字体（Arial/Helvetica） |
| 版式 | 白底，无阴影，无圆角装饰，线宽约 1 pt |

灰度可读性来自 hatch 与明度对比，不依赖色相；彩色与灰度各审一遍（见 §13）。

<a id="numeric-discipline"></a>
## 6. 数字纪律

- 图内不出现任何实例数值：不写块数、毫秒数、会话数上限或容量值。
- 时间轴只用符号周期标注：图 1(a) 为 0、T、2T、3T，图 1(b) 为 0、T、2T，图 3 为 0、T/4、T/2、3T/4、T。
- 容量线只写单词 "capacity"，不写数值；聚合子图与 pool 子图不设数值刻度。
- 块数只以带高或阶梯高度表现；比例相对。
- 下文参数表中的毫秒（或以 T = 1000 单位计的坐标）与块数只是固定比例的内部绘图坐标，用于保证画面比例一致，它们回响的是当前一种模型配置，不得渲染成图内文字。真实量级属于带证据绑定的测量图（图 2，待 Q1）。
- 定量比例（计算段远短于周期、每周期 KV 增长）在 v2/v3 阶段按诊断性 finding 标定；除 owner 变更外保持这些比例。

<a id="figure-1"></a>
## 7. 图 1 详细画法：动机实例时间轴

### 7.1 版面与文字预算

整幅 7.0 × 2.6 in，双 panel 并排，(a) 宽约 60%，(b) 宽约 40%。图内文字预算：除刻度、轴/泳道标签与共享图例外，最多六条短注释（每条不超过三个词；建议：T、shared idle、capacity、exceeds、evict、ready）加两个带圈事件序号；所有完整句子进 caption。Panel 小标题可用论断式，例如 "(a) KV binds before compute"。

### 7.2 Panel (a)：对齐轮次的多会话周期负载

四会话、三周期，横轴 0–3T。

| 参数 | 内部坐标（仅定比例） |
| --- | --- |
| 周期 T 与轮次 | 1000 单位；所有会话的 release 对齐于 0、T、2T，同一轮次的四个菱形纵向对齐成一列 |
| 计算爆发 | 每轮一次同步 batched 爆发，自轮次起点起约 0.35T，逐泳道画出；爆发长度为示意（batching） |
| 共享空闲尾 | 每轮约 0.65T，四泳道共有，即直接可见的多会话空闲窗；第一周期标注一次 "shared idle" |
| t = 0 驻留 KV | 4、4、5、5 块（带高逐泳道，相对高度，不渲染数字） |
| 增长 | 每会话每次爆发结束 +1 块；四条带同步抬升 |
| 聚合子图 | 驻留 KV 总量阶梯对容量虚线（不标数值）；阶梯起点约为容量的 0.7 倍，在第二轮增长或更晚穿越，绝不在第一周期，使读者先看到增长再看到墙；越线处注 "exceeds" |

画法要点：

- 四条泳道，不多画；规模感（N 个会话）放 caption。带高 = 驻留块数，release 空心菱形，release 后深色计算段，其余浅色，计算尾 +1 块。同步本身就是画面信息：对齐下任一时刻全部会话同态，共同计算约 0.35T、共同 idle 约 0.65T。
- S1 首周期上方画 `⟵ T ⟶` 尺寸标注；idle 最长的泳道标注一次 KV-idle 区间（植入论文 §3 Formulation 的核心对象），计入文字预算。
- 聚合子图把越线交点放在 idle 窗内读：交点处全部会话都处于 idle，"此刻全部 KV 都 idle，却已耗尽容量"为论文 §4.3（空闲 KV 状态管理）铺垫。
- 计算时间余量按 D9 口径理解：每周期 GPU 计算时间对周期预算约三分之一，与相位无关。契约当前不设独立计算时间条，该信息由泳道内的爆发段与 caption 承载；若作者决定加条，先在 §2 把 D9 改为已定再改图。
- 待定的 D1（归一化堆叠面积）与 D5（幽灵菱形）不画。

### 7.3 Panel (b)：恢复时机对比

单会话、两周期，横轴 0–2T，上下两行共享时间轴。

| 参数 | 内部坐标（仅定比例） |
| --- | --- |
| release | T/2 与 3T/2（菱形） |
| 上行 Reactive | 恢复约 0.06T，自 release 处开始（带圈 1），计算随后才开始 |
| 下行 Pilarius | 同等恢复量在 release 前约 0.1T 完成，驻留就绪等待（带圈 2），计算于 release 准时开始；计算结束后的下落台阶注 "evict" |
| 历史 / idle 保留 | 9 块 / 3 块；H2D 目标块自恢复开始即计入驻留 |
| 两行均跨完整两周期 | 逐周期重复是 "cyclic" 一词的图形依据 |

画法要点：

- 上行 Reactive：release 菱形处才开始恢复（hatch），计算在恢复结束后开始；第二周期原样重复（每周期都付这段延迟）。
- 下行 Pilarius：恢复提前完成，浅色驻留等到 release，计算从菱形准时开始；计算尾台阶下落注 "evict"（保留 3 块）；第二周期画面全等。
- 代价对称呈现：上行代价 = release 到计算开始的时间段；下行代价 = 从恢复开始到 release 的提前驻留（空间 × 时间），可用极浅底纹标出，caption 一句 "at the cost of occupying GPU capacity earlier"。
- 一条细虚线竖穿两行、落在每个 release 上，读者沿线上下对比"同一时刻，上面计算未开始、下面恰好开始"。这是 (b) 最重要的一根线。

### 7.4 30 秒阅读路径（完成判据）

浅色带在涨 → 聚合阶梯爬坡、在 idle 窗内越线 → 右边：reactive 每周期在 release 后等待，Pilarius 沿已知 release 提前恢复、计算准时、逐周期重复。三步各有唯一视觉焦点，无一步依赖 caption。

### 7.5 Scope guards

相位对齐（共享 tick），release 落在周期边界，同期菱形纵向对齐；caption 一句 caveat 点明"到达是任意的，是共享 tick 引擎把它们对齐的"，并保留"越线与相位无关"一句作为正面防御；(b) 不出现容量门控与传输竞争（图 3 内容）；对照标签用通用词 reactive，不点名系统；caption 保留 illustration 声明。

### 7.6 Caption 草稿（英文原文，进论文）

Multi-session periodic serving exhausts GPU KV capacity while a shared idle window recurs every round, and known release times let restoration move off the critical path. (a) Existing periodic serving executes all sessions in synchronized rounds — alignment maximizes batch efficiency at the cost of an up-to-one-period alignment wait on first submission; each round's bounded burst ends well before the next release, leaving a shared idle tail, while retained KV (band height) grows every round, so aggregate demand crosses the capacity line although compute is idle most of each period. (b) One session across two periods under the same restore volume: (1) reactive restoration places the restore on the critical path after each release and pays that delay every period; (2) restoring against the known next release completes early, so computation starts at the release — at the cost of occupying GPU capacity earlier — and the idle-time eviction/restore cycle repeats identically each period. Axes are in periods and heights are relative: the illustration is authored and schematic, and carries no measured magnitudes.

### 7.7 待决项

- Panel (a) 的测量对照（图 2）待 Q1；本示意图不得被引作容量受限主张的证据。
- 最终双栏排版位置与 caption 在印刷字号下的篇幅待定。
- D1、D5、D6 待作者拍板（见 §2）。

<a id="figure-3"></a>
## 8. 图 3 详细画法：设计总览

### 8.1 论点与版面

Takeaway：三项机制协同，即均匀相位网格摊开每会话峰值、空闲尾部逐出在每窗口链路预算所限的深度内回收容量、面向期限的预取在下一次 release 前恢复 KV。容量门控因果链（S3 被 defer → S1 逐出 → S3 预取 → release 前就绪）由带圈序号 1–4 承载并在 caption 叙述。对照图 1 的对齐轮次 baseline，错开网格把 pool 峰值压在容量之下，而对齐会超出。

整幅 7.0 × 3.2 in，三个纵向堆叠区域共享一条横轴，横轴跨 0–1.16T；四个相位处画浅色虚线竖线，顶部标注一次 φ1–φ4；刻度为 0、T/4、T/2、3T/4、T。图内文字预算：除刻度、泳道标签（S1–S4、H2D、D2H、Pool）与图例外，最多两条短标签（"capacity"、"aligned"）、φ 标签、KV 增长处的小 + 号与带圈序号 1–4；所有句子进 caption。

### 8.2 事件模型假设

四会话，release 偏移 φ = 0、T/4、T/2、3T/4（release 时刻，不是独占执行的预留槽）；初始历史 8、8、8、9 块；S4 的上一次更新跨越 t = 0；会话间不共享 KV；空闲逐出在主机后备完成后保留最早两块与最新一块作为示例 cache 结果；预取需要会话 idle、缺口有主机后备、pool 有容量、共享 H2D 通道空闲，且目标块自发出起即占用容量；H2D 一次一条，D2H 可重叠；传输窗口为作者给定的 50–60 单位，不声称带宽模型。

### 8.3 时序表（内部坐标，T = 1000 单位）

| 会话 | 执行包络 | 预取窗口 | 增长时刻 / D2H 窗口 |
| --- | --- | --- | --- |
| S1 | 30–380；1030–1380（裁切） | 900–960 | 140 / 160–210 |
| S2 | 280–620 | 160–220 | 420 / 450–490 |
| S3 | 530–850 | 300 处被 defer；380 发出，440 完成 | 600 / 615–665 |
| S4 | −220–120；780–1120 | 650–710 | 900 / 915–965；上一尾部后备至 20 |

因果链：300 时 pool 占用 23，S3 需要 5 块而余量只有 2，故被 defer；380 时 S1 进入 idle 并逐出 6 块，S3 预留 5 块（23 − 6 + 5 = 22）；S3 预取于 440 完成，其输入于 500 release，计算于 530 开始。完成、release 与使用三者保持区分。

Pool 参考值（块，含 H2D 目标）：0、180、300、500 处为 23；400 处为 22；620 处为 18；750 处为 24；920 与 1100 处为 25。

### 8.4 Layout 要点

- **会话泳道**（上部）：带高 = GPU 驻留块数（0–10，含有效块与已分配的 H2D 目标），计算中深蓝，idle 浅蓝，在途目标 hatch；逐出画为下落台阶；release 处空心菱形；每个带圈序号在其精确事件坐标处配小锚点圆点（1 在 S3 被 defer 的请求处 300；2 在 S1 的逐出台阶处 380；3 在 S3 的预取窗口；4 在 S3 release 前就绪的窗口）。
- **Pool 子图**（约 0.6 in）：由各泳道求和得到的占用阶梯，对虚线容量线（只写 "capacity"，无数值刻度）。另加一条浅色虚线阶梯作为**对齐轮次对照**：同一逐出机制、所有相位对齐，其峰值在共享的爆发与恢复窗口内明显超出容量线，在共享 idle 期间有深谷；标签 "aligned"，浅灰、视觉上从属。它隔离出相位机制（同一逐出、不同相位），是 GPU 空间对偶论证的示意对应（owner：docs/problem.md 资源边界；消融待 Q4）。两条线重合处把实际曲线画在容量线略下方，保证两者都可见。
- **链路子图**：H2D 与 D2H 两条细轨道，hatch 窗口标注会话名；H2D 窗口串行，保留其间的真实间隙。
- 不画块级 inset；逐出内容语义（保留前缀与最新块，主机保留全部块）由 caption 与 Design 正文承担。
- 待定的 D7（按会话堆叠与数值轴）与 D8（弧线箭头）不画。

### 8.5 Caption 草稿（英文原文，进论文）

Pilarius spreads sessions over a uniform release grid (φ1–φ4, diamonds), evicts idle KV tails, and restores them before the next release. Each lane shows one session's GPU-resident KV blocks over time; hatched spans are in-flight transfers whose destination blocks already count toward pool occupancy, and + marks newly appended KV. (1) S3's prefetch is deferred while the pool cannot hold its missing span; (2) S1's idle transition evicts its mid-history — the prefix and newest blocks stay resident and the host retains every block; (3) the freed capacity admits S3's prefetch on the shared H2D link, whose serialized windows bound how deeply a session may evict per period; (4) S3's history is fully resident before its release, so computation starts on time while S2 computes throughout. The pool subplot sums the lanes against capacity; the light dashed staircase shows the same eviction machinery under the aligned rounds of Figure 1, whose peak exceeds capacity where the staggered grid stays below it (schematic; phase ablation pending). Axes are in periods and heights are relative: the schedule is an authored mechanism illustration carrying no measured magnitudes, and it does not guarantee that prefetched contents always survive until use.

### 8.6 待决项

- 对齐对照阶梯是所画策略的示意反事实：其谷深是自由的绘图选择，其峰值必须超出容量，对应消融（Q4）尚无证据。
- 最终双栏排版位置与 caption 在印刷字号下的篇幅待定。
- 正式的预取收益、替换与高压下的行为、精确的部署调度均不由本图确立。
- D6、D7、D8 待作者拍板（见 §2）。

<a id="semantic-red-lines"></a>
## 9. 语义红线

以下四条浓缩自 2026-09-08 的机制理解审计，画任何元素前对照一次：

1. **时间对象不能合并。** release 不等于计算开始，计算开始不等于交付。release 是输入变为可提交的时刻，计算段可以晚于它开始、可以跨越其他会话的 release 推进；idle 转换是该段停止并等待后续输入；用户可见的交付是独立的评价对象。图可以选择简化的例子，但必须明确省略了哪些阶段，不能靠移动结束点使所有会话刚好按 slot 完成。
2. **KV 状态不是四态会话标签。** 会话是否 active、逻辑历史中哪些块已产生、哪些物理 GPU 块有可复用内容、哪些块有已确认的主机后备、是否有传输在途、GPU 块被请求或传输引用还是仅留在可回收的 cache，这些是正交维度，单一的计算/卸载/预取/空闲枚举不能表达。预取在途的目标块已占用空间但不可读；预取完成后内容进入可复用 cache，会话仍可 idle，且该内容可被正常回收，不保证保留到下一次使用。完整上下文不等于每一步必须再次搬运全部 KV：GPU 前缀可复用，有主机后备的缺口可恢复，没有有效后备的缺口要重算。
3. **GPU 占用只能选一种口径并全图一致。** 至少三种口径互不等价：保存了有效 KV 内容的物理块（含 cache 中可回收的内容）、被请求或传输引用而当前不可回收的分配、为达到准入状态所需的工作集（含提前恢复的目标空间）。释放请求的所有权与使缓存内容失效不是同一件事；预取完成后释放临时引用也不表示内容离开 GPU。构图前先列出每个时刻各角色的块数，同一物理块在多种角色中只计一次，再按所选口径求聚合。两图当前口径为"有效块与已分配的传输目标之和"。
4. **候选设计与已实现路径分开画，图不承载实测。** 图中的面向下一次使用时刻的提前预取是候选机制，当前实现为输入推送触发；预取保护、恢复排序、水位逐出等提议若要入图必须标明待实现或待验证，不能暗画成现有保障。性能证据由 findings 与证据登记持有，示意图不升级为正式结果；错开不减少给定逐出选择下的恢复总字节数，它改变峰值与截止窗口，图不得暗示相反。

<a id="retired-practices"></a>
## 10. 不要回退的旧做法

以下做法已在历次审计中否决，重画时不得恢复：

- 计算结束后固定一段 30 ms 的全尾部 offload：增量主机后备与空闲逐出是分离的两件事，不为画面整齐发明固定复制阶段。
- 主机侧永远画成恒定实心覆盖：后备前沿随模型进展推进，最新未完整块不一定可备份。
- 2 s 周期、8 slots 的旧参数：作者指定的示例为一个周期四个 slot。
- release 等于计算开始。
- 未计入容量的预取目标空间：目标块自发出起即占用 pool。
- 快照卡片布局（按剖面排列的块级卡片）：改为连续泳道。
- 幻灯片式整句注释：图内只留短标签，句子进 caption。

<a id="quality-gate"></a>
## 11. 图件质量门槛

- [ ] 每张图有一句可作 caption 首句的 takeaway。
- [ ] 每张图有可编辑的矢量源文件（`.drawio`）。
- [ ] 坐标轴标明单位、证据类别与配置域；机制示意图以符号周期与相对高度替代，并在 caption 声明为 authored illustration。
- [ ] 适用处显示误差棒或不确定性。
- [ ] 图例在灰度下仍可区分。
- [ ] 最终双栏版面中文字不小于印刷可读字号（本指南两图为注释 8 pt、标签 9 pt，属作者硬预算）。
- [ ] 图中不含可识别元数据、本地路径或非匿名 URL。

<a id="reference-figures"></a>
## 12. 参考图库（体裁对标，2026-09-19 逐篇核验图注）

| 参考 | 借什么 |
| --- | --- |
| InferCept (ICML'24) Fig 1 | 时间×资源×策略三合一；hatch 编码被浪费的资源；警示色只给代价 |
| HCache (EuroSys'25) Fig 1/4/5 | 恢复方式并排时序对比；layer-wise overlap 流水线画法 |
| Metronome Fig 3/5 | 概念时间线对比的克制画法；occupancy 爬容量线的曲线叙事（同时是需要视觉差异化的 baseline） |
| CachedAttention (ATC'24) Fig 6–8 | 双 stream 泳道的 preload/save overlap；buffer 不足的"不完美 overlap"对照版本 |
| GPipe/1F1B 一族 pipeline 图 | 色相=身份跨泳道追踪；bubble 留白即信息 |
| RT 调度教科书 Gantt | release/deadline/period 记号系统 |

近邻文献（Metronome/LiveServe/Pensieve/VoxServe/vLLM-Omni）均无多会话 KV Gantt；该体裁是本文的叙事资产，保留多会话画法，不退回单会话。

<a id="workflow"></a>
## 13. 制作与审阅流程

1. 源文件为 `figures/figure1-motivated-example.drawio` 与 `figures/figure2-design-overview.drawio`，作者用 Draw.io 手绘，一页一图，元素按泳道、子图、图例等分组并命名。
2. 先改指南（决策状态、参数表、事件模型），再改图；caption 与语义不得偏离 owner 文档。不加测量坐标轴或性能主张，除非先完成证据 owner 的事务。
3. 导出 crop 后的矢量 PDF 供 LaTeX，导出 PNG 供审阅，与 `figures/` 中现有基名一致，替换冻结的 v3 预览。
4. 每轮导出后做视觉审查：彩色一遍、灰度一遍，对照 §7.4 阅读路径、§9 语义红线与 §12 参考图；参数表与事件模型逐项核对。
5. 文档改动从仓库根运行 `python -m pytest tests/test_narrative_scope.py`。

## 变更日志

- 2026-09-20：建档。录入两图分工、相位结构论证与 Metronome 调研（全局 tick 对齐为结构性默认，未论证、未考虑错开替代；phase-staggered 仅指音频内容防 prefix-cache 去重）、叙事桥、共享视觉系统、图 1 详细画法、图 3 要点、参考图库与工作流。决策 D1–D8 待作者拍板。
- 2026-09-20 修订：作者 push——既然对齐是自然默认，Panel A 就该画对齐。据"全驻留越线与相位无关"（对齐安全）+ 对齐是诚实默认对手 + 对齐给 staggering 天然 before 并铺垫其"去同步共享链路恢复突发"的深层动机 + 两图 baseline 一致，D2 从"不规则相位"翻为"对齐（共享 tick）"；新增 D9（compute 条改"每周期 GPU 时间 vs 预算"）。同步改写 §2 依据与叙事桥、§4 Panel(a) 相位/聚合条/compute 条/scope guards。任意到达相位退为 caption caveat。
- 2026-09-21：合并。将两份 v4 英文绘图契约（figure-1-motivated-example、figure-2-design-overview）、2026-09-08 机制理解审计（figure-design-understanding）与旧图件计划（figures）并入本文并删除原件；图号统一为 PAPER.md 编号（图 1 动机、图 3 设计总览，文件名不变）；D1–D9 逐条对照契约判定已定/待定（D9 因契约未画出新口径的独立计算条，判为部分已定）；Metronome 对齐属性统一为已核验，删除契约中"作者回忆、未核验"的说法；视觉规范以契约色值为当前规范，Okabe-Ito 提案归入 D6 待定；新增数字纪律、语义红线、不回退旧做法与质量门槛小节；工作流改为 Draw.io 手绘，删除旧生成器相关内容。
