# 图 1 与图 3 手绘指南

本文告诉你两张机制示意图长什么样、按什么顺序画。两张图都是作者构造的示意，不是测量结果；语义上有疑问时回到 [docs/problem.md](../../docs/problem.md) 与 [docs/system.md](../../docs/system.md)，图号与图件计划见 [docs/PAPER.md](../../docs/PAPER.md#figure-plan)。

| 图 | 论文位置 | 源文件 | 尺寸 |
| --- | --- | --- | --- |
| 图 1 动机图 | Introduction | `figures/figure1-motivated-example.drawio` | 7.0 × 2.6 in |
| 图 3 设计总览 | Design 开头 | `figures/figure2-design-overview.drawio`（文件名沿用旧编号 2） | 7.0 × 3.2 in |

图 2 不用手绘。它是 Background 里的实测图：横轴扫并发会话数或上下文长度，两条曲线分别是 KV 分配占容量的比例和每周期计算时间占周期预算的比例，用来显示 KV 先到达容量线而计算仍有余量。数据来自 Q1 实验（[docs/experiments.md](../../docs/experiments.md#evaluation-questions)），Q1 跑完后由脚本从结果直接画出，颜色与字号沿用本文的通用规则；正文里它的位置已用占位框留好（`fig:tension`）。

## 从哪里开始画

`figures/` 下已有两份由脚本按下文坐标生成的起点文件 `figure1-motivated-example.drawio` 与 `figure2-design-overview.drawio`：泳道、带、菱形、参考线、标签都已按比例摆好并分组命名，用 Draw.io 打开后直接调整即可，不必从空白画布开始。旧的 SVG 预览也可以在 Draw.io 里通过 File → Import 载入作为底图对照，但导入后是整体图片，不能逐元素编辑。

## 通用规则

- 工具 Draw.io，一页一图。元素按泳道、子图、图例分组并命名。导出 crop 后的 PDF 给 LaTeX，另导 PNG 用于审阅，与 `figures/` 里现有基名一致。
- **图内不出现任何数字。** 时间轴只标 0、T、2T 这类符号刻度；容量线只写单词 capacity；块数用带的高度表现。下文表格中的块数与时间都只是帮你定比例的内部坐标，不要写到图上。
- 图内只放不超过三个词的短标签，完整句子放 caption。
- 字体无衬线（Arial 或 Helvetica）；注释 8 pt，坐标轴、泳道与 panel 标签 9 pt。白底，无阴影，无圆角，线宽约 1 pt。
- 颜色与记号两图统一：

| 含义 | 画法 |
| --- | --- |
| 会话正在计算 | 深蓝 `#28769B` 实心带 |
| 会话 idle，KV 仍驻留 GPU | 浅蓝 `#EAF2F7` 实心带 |
| 传输在途（H2D 或 D2H） | 橙 `#B87519` 斜纹，底色 `#FFF0D9` |
| release（输入变为可提交的时刻） | 空心菱形 |
| KV 容量 | 虚线，标 capacity |
| 新追加的 KV | 小 + 号（仅图 3） |
| caption 要讲的事件 | 带圈序号，落在事件坐标上加一个小圆点 |
| 坐标轴、相位参考线、对照线 | 灰 `#9CA9B2` |
| 曲线与文字 | 墨 `#263642` |

带的高度始终等于该会话此刻占用的 GPU 块数，含传输在途的目标块。灰度下靠斜纹和深浅区分，不靠色相。

<a id="figure-1"></a>
## 图 1：动机图

### 长什么样

左右两个 panel，左 (a) 占宽 60%，右 (b) 占 40%。

```text
(a) KV binds before compute                  (b) Restoration timing
 S1 ◇▓▓░░░░░░◇▓▓░░░░░░◇▓▓░░░░░░               Reactive  ░░░◇▒▓▓▓░░░░░░░░◇▒▓▓▓░░░░
 S2 ◇▓▓░░░░░░◇▓▓░░░░░░◇▓▓░░░░░░               Pilarius  ░▒▒░◇▓▓▓░░░░░░▒▒░◇▓▓▓░░░░
 S3 ◇▓▓░░░░░░◇▓▓░░░░░░◇▓▓░░░░░░                         0       T       2T
 S4 ◇▓▓░░░░░░◇▓▓░░░░░░◇▓▓░░░░░░
 Σ  ▁▁▁▁▁▁▁▁▂▂▂▂▂▂▂▂▃▃▃▃▃▃▃▃  - - capacity
    0        T        2T       3T
```

读者 30 秒内应看到三件事：四条浅蓝带在一级级抬高；底部总和阶梯爬过 capacity 线，穿越点落在大家都 idle 的时段；右边上行的计算每周期都晚开始，下行准时开始。

### Panel (a)：四个会话，三个周期

定比例用的内部坐标（T = 1000 单位）：

| 项 | 取值 |
| --- | --- |
| 横轴 | 0 到 3T，刻度 0、T、2T、3T |
| release | 四个会话都在 0、T、2T，同一列 |
| 计算段 | 每个 release 后紧接 0.35T 深蓝 |
| idle 段 | 其余 0.65T 浅蓝 |
| 起始带高 | S1 4、S2 4、S3 5、S4 5 |
| 增长 | 每个计算段结束时带高 +1 |
| 容量线 | 总和阶梯起点约为容量的 0.7 倍 |

画法：

1. 画横轴，四个刻度；在 0、T、2T 画灰色细虚线竖参考线穿过所有泳道。
2. 从上到下画 S1 到 S4 四条泳道，左侧标 S1–S4。每条是一条水平的带，起始高度按上表。
3. 在每条泳道的 0、T、2T 处画空心菱形。四个菱形纵向对齐成一列；对齐本身就是要传达的信息。
4. 每个菱形之后画 0.35T 的深蓝段，然后是 0.65T 的浅蓝段。深蓝段结束处带高抬一级（向上台阶），之后保持。
5. 在 S1 第一个周期上方画一条 `⟵ T ⟶` 尺寸线，标 T。
6. 第一个周期的 idle 时段上方，用一个跨四条泳道的括号标 shared idle。
7. 最下方画总和子图：把四条带同一时刻的高度相加，画成阶梯。画一条虚线 capacity，位置使阶梯起点约在它的 0.7 倍高。阶梯必须在第二个周期的增长处或更晚才穿过 capacity，绝不能在第一个周期就穿过；穿越点要落在 idle 时段内。穿越处标 exceeds，可以加一个小实心点。
8. Panel 小标题写成论断，例如 (a) KV binds before compute。

可选：在总和子图旁再加一条低位的水平条，表示每周期 GPU 计算时间约占周期预算三分之一，配一条 100% 虚线。这样"内存到达容量时计算仍有余量"可以直接读出。若加，只能用"计算时间对周期预算"这个口径，不要画"并发会话数对上限"，后者在对齐下恒为满。建议加。

不要：让四个会话的 release 错开（错开是 Pilarius 的机制，属于图 3）；在图上写块数或毫秒；在这个 panel 里出现容量门控、链路、预取。

### Panel (b)：一个会话，两个周期，两种恢复时机

内部坐标：

| 项 | 取值 |
| --- | --- |
| 横轴 | 0 到 2T，刻度 0、T、2T |
| release | T/2 与 3T/2 |
| 历史总量 | 9 块；idle 时保留 3 块 |
| 恢复时长 | 0.06T |
| 计算段 | 约 0.35T |

画法：

1. 上下两行共享横轴。两个 release 处各画一条细虚线竖穿两行，这是这个 panel 最重要的线。
2. 上行标 Reactive。带高从 3 起。到 release 菱形时才开始恢复：画 0.06T 橙色斜纹，同时带高升到 9。斜纹结束后画深蓝计算段。计算结束后带高降回 3，浅蓝。第二个周期原样重复。在第一个斜纹处标带圈 1。
3. 下行标 Pilarius。恢复提前：橙色斜纹在 release 前 0.16T 开始、前 0.1T 结束，带高升到 9；斜纹结束到菱形之间是浅蓝等待段，标 ready 与带圈 2。菱形处立即开始深蓝计算段。计算结束后带高降回 3，下落台阶处标 evict。第二个周期原样重复，两个周期画得完全一样。
4. 下行从恢复开始到 release 的那段提前驻留，可以用极浅的底纹衬一下，表示它占了空间；caption 会说这是代价。

读者沿虚线上下看：同一时刻，上行还在斜纹里，下行已经进入深蓝。

### 图 1 caption（英文，进论文）

Multi-session periodic serving exhausts GPU KV capacity while a shared idle window recurs every round, and known release times let restoration move off the critical path. (a) Existing periodic serving executes all sessions in synchronized rounds — alignment maximizes batch efficiency at the cost of an up-to-one-period alignment wait on first submission; each round's bounded burst ends well before the next release, leaving a shared idle tail, while retained KV (band height) grows every round, so aggregate demand crosses the capacity line although compute is idle most of each period. (b) One session across two periods under the same restore volume: (1) reactive restoration places the restore on the critical path after each release and pays that delay every period; (2) restoring against the known next release completes early, so computation starts at the release — at the cost of occupying GPU capacity earlier — and the idle-time eviction/restore cycle repeats identically each period. Axes are in periods and heights are relative: the illustration is authored and schematic, and carries no measured magnitudes.

### 图 1 为什么这样画

- Panel (a) 四个会话对齐，是因为共享 tick 的周期式引擎（Metronome 是已核对论文与代码的实例）确实把所有会话放在同一轮次里执行，这是既有系统的默认行为，不是负载的性质。caption 要把对齐归因于 baseline 调度器，并点一句到达本身是任意的。
- 在全驻留下，总和曲线与相位无关：怎么排相位都在同一个周期越线。所以画对齐不会替我们制造出内存墙，它只是让共享的 idle 窗口直接可见。
- 对齐还给图 3 的错开一个自然的"之前"：对齐意味着所有会话同时 idle、同时要恢复，恢复需求会同时到达共享链路；错开就是把这个突发分散开。这个理由留给正文与图 3，图 1 不画。
- 图 1(b) 的对照叫 reactive，不点任何系统名。

<a id="figure-3"></a>
## 图 3：设计总览

### 长什么样

三层上下堆叠，共享一条横轴：上层四条会话泳道，中层 pool 总量，下层链路轨道。

```text
        φ1        φ2        φ3        φ4
 S1  ▓▓▓▓▓▓▓░░↓░░░░░░░░░░░░░░░░░░░░░░░░▒▒▓▓▓▓      ↓ = 逐出台阶  ▒ = 预取在途
 S2  ░░░▒▒░░░░▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░
 S3  ░░░░░░░①░▒▒░░░░░░▓▓▓▓▓▓▓░░░░░░░░░░░░░░░
 S4  ▓▓░░░░░░░░░░░░░░░░░░░░░░▒▒░░▓▓▓▓▓▓▓░░░░
 Pool ▔▔▔▔▔▔▔▔▁▁▁▁▁▁▂▂▂▂▂▂▂▂▂▔▔▔  - - capacity   ·-·-· aligned
 H2D      [S2]      [S3]          [S4]      [S1]
 D2H    [S1]        [S2]      [S3]       [S4]
      0        T/4       T/2       3T/4        T
```

读者应看到：四个会话的 release 均匀错开；每个会话计算完就把中段历史逐出（带高下落），在下一次 release 前又被斜纹恢复回来；pool 总量始终压在 capacity 之下，而灰色的对齐对照线会冲过去；H2D 轨道上四个会话的恢复窗口轮流出现、互不重叠。带圈 1 到 4 讲一条因果链：S3 想预取但空间不够、S1 逐出腾出空间、S3 预取通过、S3 在 release 前就绪。

### 内部坐标（T = 1000 单位）

假设：四个会话，release 偏移 φ = 0、T/4、T/2、3T/4；起始历史 S1 8、S2 8、S3 8、S4 9 块；S4 的上一次更新跨过 t = 0；会话之间不共享 KV；idle 逐出后保留最早两块与最新一块共 3 块；预取的目标块从发出那一刻起就算占用；H2D 一次只能有一个窗口，D2H 可以与之重叠。

| 会话 | 深蓝计算段 | 橙色预取窗口（H2D） | 计算中 KV 增长（+）与 D2H 后备窗口 |
| --- | --- | --- | --- |
| S1 | 30–380；1030–1380（画到右边界截断） | 900–960 | + 在 140；D2H 160–210 |
| S2 | 280–620 | 160–220 | + 在 420；D2H 450–490 |
| S3 | 530–850 | 300 处请求被拒（①）；380 发出，440 完成 | + 在 600；D2H 615–665 |
| S4 | −220–120（左边界截断）；780–1120 | 650–710 | + 在 900；D2H 915–965；t≈0–20 有上一尾部的 D2H |

带圈序号的位置：① 在 S3 泳道 300 处（预取请求被拒）；② 在 S1 泳道 380 处的下落台阶（逐出 6 块）；③ 在 S3 泳道 380–440 的斜纹上（预取通过）；④ 在 S3 泳道 440–500 的浅蓝等待段上（release 前就绪）。

Pool 总量参考高度（含在途目标块）：0、180、300、500 处为 23；400 处为 22；620 处为 18；750 处为 24；920 与 1100 处为 25。capacity 画在 25。总量阶梯应由四条泳道求和得到，用这些值校对。

### 画法

1. 画横轴，范围 0 到 1.16T，刻度 0、T/4、T/2、3T/4、T。在四个相位处画灰色细虚线竖参考线穿过三层，顶部各标一次 φ1–φ4。
2. 上层画 S1–S4 四条泳道。每条带的高度随时间变化：计算中深蓝；idle 浅蓝；预取在途橙色斜纹，斜纹一出现带高就升上去；逐出画成向下台阶；每次计算段结束带高 +1 并放一个小 + 号；在各自 release（φ 所在时刻）画空心菱形。逐会话按上表把段落摆到位置上。S1 在 380 处从 9 块下落到 3 块，S3 在 380 处斜纹升 5 块。
3. 把四个带圈序号放到上面写的坐标上，各配一个小圆点。
4. 中层画 pool 子图，高约 0.6 in：四条泳道求和的阶梯，配一条虚线 capacity。再画一条浅灰虚线阶梯作对照，表示同样的逐出机制、但四个会话相位对齐时的总量：它在共享的计算加恢复窗口内明显冲过 capacity，在共享 idle 时段有一个深谷；标一个词 aligned，视觉上退后。实际阶梯与 capacity 重合的地方，把阶梯画在线下方一点，让两者都看得见。
5. 下层画两条细轨道，标 H2D 与 D2H。每个窗口是一段橙色斜纹，里面标会话名。H2D 窗口按上表严格串行、保留窗口之间的空隙；D2H 窗口按上表摆放，可以与 H2D 重叠。
6. 图内文字只有：刻度、S1–S4、H2D、D2H、Pool、φ1–φ4、capacity、aligned、+ 号、带圈 1–4、图例。

### 图 3 caption（英文，进论文）

Pilarius spreads sessions over a uniform release grid (φ1–φ4, diamonds), evicts idle KV tails, and restores them before the next release. Each lane shows one session's GPU-resident KV blocks over time; hatched spans are in-flight transfers whose destination blocks already count toward pool occupancy, and + marks newly appended KV. (1) S3's prefetch is deferred while the pool cannot hold its missing span; (2) S1's idle transition evicts its mid-history — the prefix and newest blocks stay resident and the host retains every block; (3) the freed capacity admits S3's prefetch on the shared H2D link, whose serialized windows bound how deeply a session may evict per period; (4) S3's history is fully resident before its release, so computation starts on time while S2 computes throughout. The pool subplot sums the lanes against capacity; the light dashed staircase shows the same eviction machinery under the aligned rounds of Figure 1, whose peak exceeds capacity where the staggered grid stays below it (schematic; phase ablation pending). Axes are in periods and heights are relative: the schedule is an authored mechanism illustration carrying no measured magnitudes, and it does not guarantee that prefetched contents always survive until use.

### 图 3 不要画成

- release 等于计算开始。菱形是输入可提交的时刻，深蓝段可以晚于它开始，也可以跨过别的会话的菱形。
- 计算结束后紧跟一段固定的全量 offload。主机后备是随计算进展增量完成的（D2H 窗口在计算段内），逐出是 idle 后另一件事（下落台阶）。
- 预取斜纹不占空间。目标块从发出就占 pool，带高要在斜纹开始时升起。
- 预取完成就等于开始计算。S3 从 440 就绪到 530 开始计算之间有一段浅蓝等待，要留着。
- 四条 H2D 窗口互相重叠。链路是共享的，串行才成立。
- 把这张图画成实测。所有数字只定比例。

### 图 3 里对齐对照线的意思

灰色 aligned 阶梯是"如果四个会话相位对齐、其余机制不变"的反事实：它的谷深随你画，峰值必须冲过 capacity。它的作用是让读者把图 1(a) 的对齐世界和图 3 的错开世界连起来，隔离出相位这一个变量。对应的消融实验（Q4）还没有数据，所以 caption 写 schematic。

## 尚可选择的画法

以下几处你可以换一种画法。换了就把上文对应步骤改掉，再动图。

| 位置 | 上文默认 | 另一种 | 得失与建议 |
| --- | --- | --- | --- |
| 图 1(a) 总和子图 | 一条总量阶梯 | 分两层堆叠：下层深色是正在计算会话的 KV，上层浅色是 idle 会话的 KV | 能直接显示"越线时全是 idle 的 KV"，但对齐下深浅整体切换、信息不多，还多一层图例。建议不换 |
| 图 1(a) 计算余量条 | 不画 | 加一条低位条 | 见 Panel (a) 可选项。建议加 |
| 图 1(a) 横轴右端 | 止于 3T | 多留 0.2T，画下一次 release 的虚线菱形，标 releases known ahead | 把"下一次使用时刻可知"放进问题面板，但多占一条标签。建议不加，这层意思由 (b) 承担 |
| 两图配色 | 单色相，会话身份靠标签 | 每个会话一个色相（Okabe-Ito 四色），深浅或纹理表示状态，代价与失败处用红色 | 图 3 里 S1 逐出到 S3 预取的因果可以由颜色的先后出现表达，H2D 轨道四色轮流出现即自明；代价是灰度可读性要逐色校验，两图必须同换。建议在图 3 先试一版再定 |
| 图 3 pool 子图 | 总量阶梯 | 按会话堆叠面积 | 能看出各会话对峰值的贡献；仍不能加数值轴。建议不换 |
| 图 3 因果链 | 带圈序号加圆点 | 用细弧线箭头把 1→2→3→4 串起来 | 不读 caption 也能顺着走，但四条弧线穿泳道会与斜纹和菱形相互干扰。建议先画序号版，排版后有空间再加 |

## 导出后自查

- [ ] 彩色看一遍，转灰度再看一遍，深蓝、浅蓝、斜纹三者仍能分开。
- [ ] 图上没有任何数字，容量线只有 capacity 一个词。
- [ ] 每个带圈序号都能在 caption 里找到对应句子。
- [ ] 印到双栏宽度后，8 pt 注释仍可读。
- [ ] 图 1 总和阶梯不在第一个周期越线；图 3 实际 pool 阶梯不越线、aligned 对照线越线。
- [ ] 文件里没有作者信息、本机路径或仓库 URL。
- [ ] 改完文档跑 `python -m pytest tests/test_narrative_scope.py`。

## 参考图（体裁对标）

InferCept (ICML'24) Fig 1：时间、资源与策略画在一起，斜纹表示被浪费的资源。HCache (EuroSys'25) Fig 1/4/5：两种恢复方式并排的时序对比。Metronome Fig 3/5：占用曲线爬容量线的克制画法。CachedAttention (ATC'24) Fig 6–8：双 stream 泳道上 preload 与 save 的重叠。GPipe 一族的 pipeline 图：颜色表示身份、留白表示 bubble。实时调度教材的 Gantt 图：release、deadline、period 的记号。近邻文献都没有多会话 KV 的 Gantt 图，这个体裁是本文自己的。
