# 图件手绘指南

本文记录论文示意图的分工、已画完的图的定稿记号，以及尚未画的图应当长什么样。示意图不是测量结果；语义有疑问时回到 [docs/problem.md](../../docs/problem.md) 与 [docs/system.md](../../docs/system.md)，图号与位置以 [docs/PAPER.md 图件计划](../../docs/PAPER.md#figure-plan) 为准。源文件与导出方式见 [figures/README.md](../figures/README.md)。

## 图的分工

| 图 | 位置 | 回答的问题 | 状态 |
| --- | --- | --- | --- |
| 图 1 动机图 | Introduction，第二步 | 问题存在：会话按周期推进，每轮只增量计算，KV 却逐轮累积，显存先于计算到顶 | 已画完，`figures/figure.drawio`，双栏引用 |
| 图 2 相位与恢复时机 | Introduction，第三、四、六步 | 现有路线为何失败：对齐的多会话下反应式换入同时压向共享链路、落在关键路径上；我们为何可行：deadline 已知可提前恢复，相位可错开 | 未开始 |
| 实测图 | Background and Motivation | 图 1 论点的测量版本：KV 分配随会话数逼近容量而计算占比仍低 | 待 Q1 数据，脚本出图，不手绘 |
| 设计总览图 | Design 开头 | 怎么做：均匀相位网格、逐出深度与链路预算、容量门控预取、接纳 | 未开始 |

范本依据：vLLM 与 Sarathi-Serve 的 Intro 各有两张图，Sarathi 的第二张把现有系统与自己并排；跨双栏的大图在两篇里都出现在 §2 或 §3。Intro 放两张图有先例，但图 2 应比图 1 更简。

## 通用规则

- Draw.io 手绘，一页一图，元素分组命名。字体 Inter，与全文图件统一；标签 8 px，图例可到 7 px；双栏引用放大约 1.25 倍后分别为 10 pt 与 8.8 pt，这是下限。
- 图内不写具体数值。时间轴用符号刻度，容量线只写名称。
- 图内只放不超过三个词的短标签，完整句子放 caption；图例已解释的颜色，caption 不再重复。
- 图内词汇用实时调度与本文术语表的词：period T、deadline d_k、micro-turn、idle、resident、capacity。不用 recurring deadline、frame budget、tick、update。
- caption 三到五句，现在时陈述句，不加"schematic"一类声明，图没有刻度本身说明它是示意。
- 颜色语义全文统一：

| 含义 | 颜色 |
| --- | --- |
| 输入侧：音频流带、prefill 段、input tokens | 蓝 `#1BA1E2`；带底色 `#E3F2FB` |
| 输出侧：decode 段、语音输出带、output tokens | 橙 `#FF9933`；带底色 `#FFF0D9` |
| 音频编码段 | 浅蓝 `#99CCFF` |
| 计算空闲 | 灰 `#CCCCCC`，虚线边 |
| 历史 KV | 蓝灰 `#C9D6E3`，边 `#5B7083` |
| 主机副本（已逐出） | 白底、`#5B7083` 边 |
| 传输在途 | `#FFF0D9` 底加 `#B87519` 斜纹 |
| 容量线 | 墨色 `#263642` 虚线 |
| 容量触顶 | 红 `#C0392B`，全图唯一 |

<a id="figure-1"></a>
## 图 1：动机图（已定稿）

**结构。** 一条会话时间线，六个 micro-turn，第三与第四个之间省略。五行：输入流带（按 T 分格）；deadline 竖线 d_0 到 d_2、d_k 到 d_{k+2}，第一段上方尺寸线标 T，中间虚线箭头标 periodic micro-turns；计算行，每轮三段 encoding、prefill、decode 加虚线灰 idle；输出流带；KV token 行，每轮在历史块后追加一个 input 块与一个 output 块，省略号后历史块画成一条长矩形。右半下方一条折线表示驻留 KV 随轮次增长，在最后一轮触到容量虚线，红点标 reach limit，虚线右端标 GPU memory capacity。左下角图例两行：compute 一行四项，tokens 一行三项。

**读法。** 每轮计算段宽度不变而 KV 行逐轮变长；折线在 idle 段水平、prefill 段陡升、decode 段缓升；最后触顶。

**caption（已进正文）。**

> A full-duplex session advances in periodic micro-turns. The k-th micro-turn begins at d_k and is due by d_{k+1} = d_k + T: the model encodes the audio received over the previous period, prefills the resulting input tokens, and decodes a bounded output segment for playback, after which the GPU idles until the next deadline. Input and output tokens are appended to the KV history, which remains resident across periods. Decoding work per period is bounded by the chunk length and the output budget, whereas resident KV grows with every period; across concurrent sessions, GPU memory is exhausted long before compute is saturated.

**尚可调整。** 两处 T 标签仍是 Helvetica，应改为 Inter；图例字号 6.67 px 应提到 8 px；输出流带若只在说话的轮次画格、格长随 decode 变化，能解释 decode 段宽度为何不同，可选。

<a id="figure-2"></a>
## 图 2：相位与恢复时机（待画）

**结构。** 左右两个 panel，共用记号，各画三条会话与一条链路轨道，一个半周期。

- 左 panel，反应式换入，会话相位对齐：deadline 之前每条会话只剩少量实心块，其余为主机副本；deadline 一到三条会话同时发起换入，在链路轨道上首尾相接排队，S2、S3 等待；计算段被推到 deadline 之后，越线部分描红边。
- 右 panel，提前恢复且相位错开：三条会话的 deadline 按 T/3 错开；换入在各自 deadline 前发起并完成，随后一小段浅色等待，计算段从 deadline 准时开始；链路轨道上三段换入互不重叠。

**不画。** pool 曲线、带圈因果链、slot 一词、逐出深度与链路预算。这些属于设计总览图。

**caption 要落的三件事。** 反应式换入把恢复放在关键路径上且多会话同时到达链路；下一次 deadline 已知，恢复可以提前到空闲期；相位由服务栈在接纳时通过会话时钟起点设定，代价上界为一个周期的等待或等量的前置静音。

<a id="figure-3"></a>
## 设计总览图（待画）

三层堆叠共用横轴：上层四条会话泳道，均匀相位 φ_1 到 φ_4；中层 pool 总量阶梯对容量线，另加一条浅灰的对齐对照阶梯；下层 H2D 与 D2H 两条链路轨道，H2D 窗口串行。带圈序号 1 到 4 讲一条容量门控的因果链：S3 预取被拒、S1 逐出腾出空间、S3 预取通过、S3 在 deadline 前就绪。内部坐标以 T = 1000 单位计，四会话相位 0、250、500、750，起始历史 8、8、8、9 块，逐出后保留 3 块，预取窗口 60 单位，pool 容量 25 块。此图画之前先与 [docs/system.md](../../docs/system.md) 的机制卡核对一次，策略若有变动以 owner 为准。

## 导出后自查

- [ ] `pdffonts` 显示图内字体为所选字体并已嵌入，没有 Helvetica 回退。
- [ ] 彩色与灰度各看一遍，蓝、橙、蓝灰、灰四类在灰度下可分。
- [ ] 图内无数值；容量线只有名称。
- [ ] 双栏放大后最小文字不低于 8.8 pt。
- [ ] 无作者信息、本机路径、仓库 URL、模型或设备名。
- [ ] 改完文档从仓库根运行 `python -m pytest tests/test_narrative_scope.py`。

## 参考图（体裁对标）

InferCept (ICML'24) Fig 1：时间、资源与策略画在一起，斜纹表示被浪费的资源。HCache (EuroSys'25) Fig 1/4/5：两种恢复方式并排的时序对比。CachedAttention (ATC'24) Fig 6–8：双流泳道上 preload 与 save 的重叠。Sarathi-Serve (OSDI'24) Fig 1/2：Intro 两张单栏图，第二张把现有系统与自己并排。实时调度教材的 Gantt 图：release、deadline、period 的记号。
