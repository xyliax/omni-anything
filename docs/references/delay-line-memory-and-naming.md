# 延迟线存储：历史称呼与命名启发

本文件是外部历史资料与编辑意见，不是项目事实、机制或术语 owner。核对日期：2026-09-15。项目类比沿用 `docs/problem.md` 与 `docs/system.md`；本文不修改研究范围、机制状态或论文标题。

## 可直接核对的历史来源

| 来源 | 核对内容 | 证据用途 |
| --- | --- | --- |
| [Eckert 与 Mauchly，Memory system，US2629827A](https://patents.google.com/patent/US2629827A/en)；[原始专利 PDF](https://patentimages.storage.googleapis.com/f7/97/cd/c2e4049f574d4d/US2629827.pdf) | 1947 年申请、1953 年授权；本次读取专利页元数据与 description 的原文转录。原文描述脉冲沿路径传播、输出反馈到输入并重复循环 | 证明 recirculation 与 regeneration 是当时实际使用的过程用语；专利正式题名为 Memory system |
| [Computer History Museum：1949: EDSAC computer employs delay-line storage](https://www.computerhistory.org/storageengine/edsac-computer-employs-delay-line-storage/) | 介绍 Eckert 将战时雷达中的水银延迟线用于数据存储，以及 EDSAC、UNIVAC 的使用；描述转换、传播、接收、放大与回送 | 历史背景及 delay-line storage / memory 的器件称呼 |
| [Computer History Museum：Delay Lines](https://www.computerhistory.org/revolution/memory-storage/8/309) | 描述数据转换为声波后再转回比特，持续循环；串行比特流在单一位置被访问 | 说明循环存储与串行访问的工作方式 |
| [Samuel Lubkin，Cyclic memory system，US2832064A](https://patents.google.com/patent/US2832064A/en) | 1955 年申请、1958 年授权。原文把 magnetic drums、delay line registers 与 shift registers 列为 cyclic type memories | 证明 Cyclic memory system 是实际历史题名，并且 cyclic memory 是比延迟线更宽的类别 |
| [剑桥大学：A brief informal history of the Computer Laboratory](https://www.cl.cam.ac.uk/events/EDSAC99/history.html) | EDSAC 展开为 Electronic Delay Storage Automatic Calculator；记载 1946 年开始建设、1949 年运行 | 说明 Delay Storage 直接进入了机器名称 |

CHM 还列出 Eckert 的 A Survey of Digital Computer Memory Systems（Proceedings of the IRE，1953）作为同期文献。本次未读取该论文原文，不以它证明额外的历史术语或首创归属。

## 原始用语

US2629827A 的 description 使用以下可定位短句：

> “continuous recirculation of a pattern of acoustic pulses”

> “The regeneration at the input of a circulatory pulse system of the signals emitted at its output”

原文还把这种过程描述为沿路径传播、经反馈重新输入并 “repetition of the cycle”。这些词的层级需要区分：

- **Delay-line memory / delay-line storage**：实际器件或存储技术的称呼。
- **Recirculation**：输出回送输入，使信息模式持续循环的操作。
- **Regeneration**：在反馈端重新形成信号的过程；不是从无信息状态凭空恢复数据。
- **Cyclic memory**：历史上已有的类别，包含延迟线、移位寄存器和磁鼓等。

Recirculating delay-line memory 可以作为根据上述过程形成的技术描述，但不能声称它是 US2629827A 的正式题名。此次直接证明了 regeneration 的过程用语，未证明 Regenerative Memory 是该项发明唯一或正式的名称。

## 工作方式与类比边界

延迟线把电信号转换为沿介质传播的脉冲序列。脉冲到达另一端后，被接收、放大或整形，并反馈回输入，形成持续循环。多个比特可同时处于传播路径的不同位置；可存容量取决于传播时延、可分辨脉冲速率及电路开销，读取需要等待对应位置到达访问点。

因此，当时的收益是用延迟线介质和反馈电路提供存储，降低对昂贵电子存储单元的需求。循环维持已经编码的信息，不会使有限延迟线容量随循环次数无限增长。

| 比较项 | 延迟线存储 | Conveyor 的候选设计空间 |
| --- | --- | --- |
| 历史如何保留 | 信息模式由传播介质与反馈循环维持 | 应用指定的历史由有效后备或可重建历史保留 |
| 昂贵资源的使用 | 输入、输出与再生电路接续处理传播中的脉冲，多个比特共享配套电路 | GPU 在需要状态的窗口中驻留所需内容，更新间可回收部分空间 |
| 时间为什么重要 | 比特到达访问点的时机决定串行访问 | 预计使用时间与可用余量约束迁移、恢复及重建安排 |
| 容量来自什么 | 介质能同时容纳的脉冲位置及配套电路 | 给定 GPU 空间、传输与计算预算下可满足服务目标的会话规模 |

共同的设计启发是：**长期保留状态与持续占用昂贵的快速存储可以分别设计，状态使用的时间结构因而进入容量分析。** 这是一项有边界的历史类比，不声称 Conveyor 将数据保存在传输链路中，或实现了物理延迟线。

更具体的映射是：延迟线由物理传播介质保留比特，共享输入输出和再生电路按时间接续处理脉冲；Conveyor 的候选设计让历史保持可恢复，并在不同状态使用窗口中复用实际 GPU 空间。因此，共同点是信息持续保留与昂贵硬件按时间复用的结合；被复用的资源、状态载体和容量决定因素不同。延迟线的数据一直占据介质中的可分辨位置，不能表述为它不需要物理存储，或只在处理器访问时才占用存储。

延迟线的循环由传播时延与电路时钟形成，串行访问可能需要等待目标位置到达。Conveyor 的准备机会来自应用更新契约以及有界工作完成后的余量，预计下一次需求用于约束准备时间。具体空闲窗口与多会话可用预算仍取决于配置和竞争；历史类比不证明固定周期、恢复及时性或承载收益。

## 传播时延、容量与抛球类比

作者提出了声波传播与“两只手抛三个苹果”的直觉。延迟线的容量可用一个忽略电路开销的一阶关系说明：`可存比特数 ≈ 可分辨比特速率 × 传播时延`；固定长度下，传播时延约为 `介质长度 / 声波传播速度`。声波较慢，使多个可分辨脉冲能同时处于传播路径的不同位置。因此，声速与光速的差异可以帮助解释选择声学介质的直觉，但不能直接作为存储容量倍数：脉冲分辨率、可用带宽及线路开销同样约束容量。循环反馈延长信息的保留时间，有限介质可同时承载的信息量仍有上限。上述历史来源不支持无比较基准的“扩展几十倍”数字。

抛球类比更直接地解释 GPU 空间的时间复用：

| 抛球中的要素 | 对应的设计含义 |
| --- | --- |
| 有限的手部容量 | 有限的 GPU KV 物理空间 |
| 持续掌控的苹果 | 跨更新需要保留的会话状态；实际可以只逐出其中一部分 |
| 苹果暂时在空中 | 状态暂时不占据相应 GPU 空间，仍由有效后备保存或由保留历史支持重建 |
| 抛出与接回 | 安全逐出，以及在后续使用前分配并准备所需状态 |
| 抛接节奏 | 预计使用时间、KV 空闲区间，以及不同会话需求的重叠情况 |
| 抛接能力 | 传输与计算预算、完成延迟及其竞争 |

类比成立需要同时满足：所有被移除状态仍可恢复；任意时刻的实际 GPU 分配不超容量；每次使用前依赖的内容已经就绪。状态“在空中”不能按字面理解为仅保存在 PCIe 在途数据中。建立主机副本时 GPU 源空间可能仍被引用；回载开始前就要分配 GPU 目标空间。实际占用窗口应按[问题 owner 的资源边界](../problem.md#resource-frontier)计入准备与安全回收过程，不能只按模型执行时长估算复用倍数。某会话的空闲也不证明多会话条件下 GPU 有同等计算余量；可用余量须与已有工作及恢复竞争一起核算。主动历史重算的状态以[系统 owner](../system.md#on-demand-restoration)为准。

这两种设计的共同启发可表述为：**让需要长期保留的信息在不同载体上维持，并按使用节奏复用有限的昂贵资源。** 延迟线的物理脉冲间隔和再生电路决定其串行节奏；现代设计的状态访问契约、传输与计算成本决定可回收和准备的机会。抛球展示了“保留状态总量可以大于同时 GPU 驻留量”的可能性，但具体收益仍须通过资源模型与实验裁决。

可用于论文的编辑草句为：

> Retaining a session's history does not require keeping its KV state continuously resident on the GPU. Between predictable updates, recoverable state can leave GPU memory so that other sessions can reuse the space. Realizing this opportunity requires coordinating eviction and state preparation: physical allocations must remain within capacity, and the required state must be ready before its next use, subject to transfer and compute budgets.

这段使用已定义的驻留与恢复语义描述候选设计，不声明性能结果或已实现的统一策略。

## 延迟线与状态恢复的逐项对应

为进一步判断历史类比能否支撑 Cyclic State Restoration，较具体的对应应同时包含信息载体、可访问形式和返回时序。延迟线中的信息在声学介质内持续存在，脉冲返回端口时被接收为电信号，并经过整形重新输入；候选设计的历史在 GPU 外仍可恢复，后续需求到来前再准备成执行可访问的 GPU KV。这里对应的是“信息的保留与执行侧可用状态分别安排”的架构关系；电子再生电路与 GPU 空间不是同一种被复用资源。

| 延迟线中的过程或要素 | 候选设计中的功能对应 | 对应的边界 |
| --- | --- | --- |
| 传播介质内的声学脉冲 | GPU 外的有效副本，或足以支持重建的保留历史 | 后备通常静态保存信息，链路不是延迟线存储介质 |
| 脉冲离开输入端并沿介质传播 | 使用后安全回收部分 GPU 驻留，在 GPU 外保持可恢复性 | 延迟线脉冲持续传播，现代后备可以静态保存；安全释放 GPU 分配还依赖引用与副本有效性 |
| 脉冲返回输出端、转为电信号并整形反馈 | 将缺失历史准备为 GPU 上可使用的 KV | 历史信号再生修复信号形态，现代恢复准备计算依赖；回载与重算也须区分，重算条件与机制状态由系统 owner 定义 |
| 多个脉冲接续经过共享端口与电路 | 多个会话接续占用有限的 GPU KV 空间 | 实际状态窗口可重叠，准备和回收均计入占用 |
| 传播时延与时钟决定返回节奏 | 更新契约给出预计使用时间，资源策略安排准备 | 延迟线每圈反馈不等于每圈都有处理器访问；候选设计不要求物理循环传输全部历史 |

两种概念流程可分别写为：

```text
延迟线：电信号输入 -> 声学传播与存储 -> 电信号接收、整形 -> 反馈再输入
候选设计：GPU KV 使用 -> 安全回收部分驻留（历史仍可恢复） -> 后续状态准备 -> GPU KV 使用
```

在恢复以传输为主的简化模型下，状态准备也具有吞吐与时间的联合约束：`待恢复字节量 <= 有效传输速率 × 可用准备窗口`。这与延迟线的 `可存比特数 ≈ 脉冲速率 × 传播时延` 有相似的量纲形式，但左侧含义不同：前者约束一次状态准备任务，后者描述介质内同时保存的信息量。准备窗口、目标分配、双向竞争和多会话峰值须按[资源边界](../problem.md#resource-frontier)联立检查，不能把两式直接等同为显存扩展公式。

对标题的编辑结论是：这一对应可以解释 Cyclic State Restoration 的历史意象，且 Restoration 比 Regeneration 更能兼容回载及有条件的重建；它不证明 Cyclic State Restoration 是历史术语，也不代替当代相关工作的比较。名称需描述最终设计真实具有的跨更新反复回收和准备过程。历史启发适合在 Introduction 中解释，技术贡献与容量收益仍来自实际资源规划和评估。

可用于 Introduction 的进一步编辑草句为：

> Delay-line memories kept information in acoustic form between successive passages through shared electronic regeneration circuitry. Conveyor draws a conceptual parallel: it preserves recoverable history outside the GPU between state-use windows and prepares the required KV state before subsequent computation, allowing sessions to reuse limited GPU memory. The opportunity depends on coordinating state preparation and residency within transfer, compute, and timing constraints.

这段是候选设计叙事，不是已实现能力或实测结果。

## 第九个候选的解释要求

作者进一步澄清讨论的是候选清单第九项中的 Cyclic State Restoration。该词组是现代描述性候选，强调反复回收和准备状态的过程；它不是原始延迟线文献的术语。若采用，应先按问题 owner 的术语规则正式定义。建议定义的语义为：在相邻模型更新之间反复回收部分 GPU KV 驻留，并在下一次使用前准备所需的保留历史。其循环对应更新间的状态使用与准备，不要求逐周期恢复全部历史或相同字节集合。

正文应区分术语解释和历史类比：摘要首次使用时可用短语给出核心含义；Introduction 可用一小段对照延迟线的循环与再生、现代状态驻留与准备；Design 展示状态有效性、空间占用、恢复时间及传输与计算预算的实际关系。历史背景一两句通常足够，机制定义和论证需要具体。名称本身不构成额外 research mechanism。

可用于 Introduction 的编辑草句为：

> Early delay-line memories maintained information as circulating pulse patterns in a physical medium, using shared circuitry for signal regeneration. Our design draws a conceptual parallel: it keeps history recoverable while reusing GPU memory across successive state-use windows. Predictable update times and execution slack provide opportunities to plan state preparation within transfer and compute budgets before the next use.

这段是设计思想的表达，不是当前代码路径或性能结果的陈述。状态准备若包含主动重建，仍须维持 owner 中的扩展状态与验证要求。

## 命名启发

历史名称优先描述器件或维持状态的过程，没有要求用宽泛性能形容词命名。最有依据的词根是 recirculation、regeneration 与 cyclic。它们分别强调返回、重新形成和反复出现的使用过程。

若保留作者已认可的 Memory Multiplexing，较准确的历史启发候选为：

> Conveyor: Memory Multiplexing through Cyclic State Restoration for Interactive Model Serving

Cyclic State Restoration 是此处提出的描述性候选，概括跨更新反复准备所需状态，使 GPU 空间能够在会话间复用；它不是从原始文献直接继承的术语，不表示逐周期恢复全部历史，也不保证会话窗口完全不重叠。若采用，须由问题 owner 正式定义，并由最终设计说明恢复与驻留如何受传输、计算和时间预算共同约束。

更贴近历史词根的候选为：

> Conveyor: Memory Multiplexing through State Recirculation for Interactive Model Serving

该版本历史辨识度更强，但 Recirculation 容易让读者预期字面上的数据闭环搬运。若最终设计包含迁移与重建混合，必须解释它描述的是逻辑状态跨更新的使用和准备过程；仅回载与主动重算仍是不同路径，后者当前是扩展。就机制准确性而言，Restoration 比直接把系统称作 Recirculating Memory 或 Regenerative Memory 更稳妥。

Conveyor 可以继续作为系统名：传送与反复准备状态的意象与此类比相容。不能据此推断早期延迟线技术曾以 Conveyor 命名，或把历史类比作为独立机制、创新证明或性能证据。
