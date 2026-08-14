- **标题:** Dispider：通过解耦感知、决策与反应，让视频大语言模型实现主动实时交互
- **一句话总结:** Dispider 把实时视频对话拆分成独立的「观看」「决策」和「回答」三个循环，让视频大语言模型（video LLM）的交互不再被答案生成过程阻塞，同时在长视频问答上保持有竞争力的准确率。
- **论文类型:** 系统类论文
- **发表:** arXiv 预印本 2025
- **作者:** Rui Qian、Shuangrui Ding、Xiaoyi Dong、Pan Zhang、Yuhang Zang、Yuhang Cao、Dahua Lin、Jiaqi Wang；香港中文大学与上海人工智能实验室
- **关键词:** 视频大语言模型（video LLM）、流式视频理解、实时交互、异步回答生成、时间定位、长视频问答
- ## Orientation
    - **背景:** 这篇论文属于视频语言模型领域：这类系统把视觉画面帧与语言模型连接起来，让用户可以询问一段时间内正在发生什么。研究场景是流式视频，也就是画面帧持续不断地到达，而不是作为一段已经完成的完整片段一次性给出。
      claim_kind:: analyst_assessment
    - **通俗问题:** 观看实时画面的人可能在重要时刻还没发生时就发出求助，因此助手必须持续观看，并判断自己何时已经掌握了足够的证据可以开口回答。
      claim_kind:: analyst_assessment
    - **为何困难:** 同一个模型通常要同时负责观看、抉择和撰写；当它在撰写时，可能会停止观看，而这一停顿可能会错过下一个有用的视觉线索。
      claim_kind:: analyst_assessment
    - **一句话核心思路:** 把观看者、决策者和答案撰写者分开，这样在生成答案的同时观看仍能继续进行。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **阅读价值:** 把这篇论文当作一篇视频-语言系统方向的工作来读，它关注的是这样一个差距：理解一段已经播完的视频，与在视频还在持续到来的过程中充当实时视觉助手，二者之间存在鸿沟。
      claim_kind:: analyst_assessment
      evidence:: E2
    - **一句话贡献:** Dispider 让模型在一个独立的答案生成器负责说话的同时，仍持续观看和决策，从而改善流式视频问答的表现。
      evidence:: E3, E7
    - **记忆模型:** 可以想象一个现场助手：一名工作人员负责观察房间，另一名负责判断某件事是否值得说出来，还有一名负责组织句子，而且不会让负责观察的人分心移开视线。
      claim_kind:: analyst_assessment
    - **最佳证据:** 最有力的证据是：相比以往的流式模型，本文在流式基准测试上取得了明显优势；此外消融实验表明，场景分割和回答状态标记（response-state token）都起到了作用。
      evidence:: E11, E14, E15
        - 支持论点 C1：StreamingBench 以 1 fps 运行；最接近的流式基线是以 2 fps 运行的 VideoLLM-online；总分为 53.12 对 32.48，主动输出（Proactive Output）为 25.34 对 3.92；论点得到支持，但未报告方差。
          evidence:: E11
        - 支持论点 C2：使用 ETBench 的流式子集；基线为 VideoLLM-online；时序视频定位（temporal video grounding）的 F1 为 36.1 对 13.2，密集视频描述（dense video captioning）的 F1 为 33.8 对 24.0；论点得到支持，但基准的构建选择由论文自行定义。
          evidence:: E12
        - 支持论点 C3：在 ETBench 和长视频上做消融实验；基线为均匀切分和去除特殊标记两种做法；三个特殊标记合起来把时序定位（TVG）的 F1 从 20.1 提升到 36.1，基于场景的切分也改善了多项指标；论点得到支持，但敏感性分析的覆盖范围有限。
          evidence:: E14, E15
    - **主要边界:** 这篇论文展示了基准准确率的提升，但没有报告端到端延迟、硬件配置、重复实验次数或不确定性，因此主动交互在真实部署中的性能边界仍有一部分没有被测量。
      claim_kind:: analyst_assessment
- ## Argument Map
    - **问题与重要性:** 这篇论文针对的是主动实时交互：视频大语言模型（video LLM），也就是一个连接了视觉视频特征的语言模型，必须在只看到目前为止的视频流的情况下，判断何时该回答。其关键意义在于实用的响应能力：离线模型可以在视频结束后再回答，但实时助手既要避免开口太早，也要避免错过有用的时刻。
      evidence:: E2, E4
    - **已有方法缺口:** 以往的流式系统要么侧重于长视频记忆，要么用单个自回归的大语言模型（LLM）同时完成感知和回答；这里的自回归指的是文本一次生成一个 token。这种单循环设计会导致反应阻塞：生成答案会打断视频处理和决策更新。
      evidence:: E3
    - **关键洞见:** 核心洞见是：判断是否要作答可以简化为一个小规模的状态跟踪问题，只需在紧凑的视频记忆和动作标记上进行跟踪，而更丰富的回答文本则可以由一个独立的模块来生成。这种分离把生成的回答 token 从决策循环中移除，因此决策循环不必等待回答循环。
      claim_kind:: analyst_assessment
      evidence:: E6, E7
    - **核心主张:** 论文的核心主张涉及非阻塞式的流式交互、时间定位（temporal grounding）、组件的必要性，以及对常规视频问答能力的保持。
      claim_kind:: analyst_assessment
        - C1：一种将感知、决策与反应解耦的架构，能够实现比以往流式视频大语言模型（video LLM）更强的主动流式视频交互。
          evidence:: E3, E7, E11
        - C2：Dispider 提升了流式视频问答中的主动时间定位和按事件时机作答的能力。
          evidence:: E4, E12
        - C3：基于场景的切分和显式的回答状态 token 是真正发挥作用的组成部分，而不仅仅是表面上的实现细节。
          evidence:: E5, E14, E15
        - C4：这种流式架构不会导致常规长视频问答性能崩溃。
          evidence:: E13
- ## Mechanism and Design
    - **核心机制:** Dispider 把主动流式处理拆分为感知、决策与反应三部分。感知把传入的视频片段压缩成特征，决策根据当前问题和记忆预测应当等待还是作答，反应则异步地写出详细回答，从而不阻塞对新视频的处理。
      evidence:: E4, E7
    - **数据/控制流:** 视频流首先被切分成基于场景的、长度不均匀的片段；这里「基于场景」是指由画面的视觉变化来确定片段边界，而不是按固定的帧数来划分。每个片段被转换成一个紧凑的特征，决策模块在其后附加问题和一个 TODO 标记，而一旦作出作答的决定，就会启动反应模块，与此同时视频流继续处理。
      evidence:: E5, E6, E7
        - 场景边界是通过预训练视觉嵌入之间的相似度变化来确定的，随后生成片段特征和片段指示符，供后续决策使用。
          evidence:: E5
        - TODO token 标记尚未解决的决策点，ANS token 则记录已经给出过回答，这样决策模块无需读取生成的回答文本，就能跟踪回答状态。
          evidence:: E6, E7, E15
        - 反应模块（reaction module）先把一个 TODO token 的嵌入向量与各视频片段的指示器作比较，从而检索出相关的历史片段；随后利用当前问题、之前给出的答案以及找到的这些片段来作答，或者选择保持沉默。
          evidence:: E8, E9
    - **设计决策:** 这些主要的设计选择都在保护同一个不变量：决策路径应当保持轻量、有状态，并且与答案解码相互独立；与此同时，答案路径可以更大、更精确。
      claim_kind:: analyst_assessment
      evidence:: E7, E10
        - 需求：长视频流中包含大量冗余帧；选择：采用基于场景的非均匀切分片段；文中报告的最接近的替代方案：均匀切成 16 帧的片段；权衡：结构更好，但代价是需要一个边界检测器。
          evidence:: E5, E14
        - 需求：在单个大语言模型中，生成回复会阻塞感知；选择：使用一个紧凑的决策模块，再加上一个更大的异步反应模块；权衡：用两个模块之间的协调与训练上的复杂度，换掉了更简单的单一循环。
          evidence:: E3, E7, E10
        - 需求：决策模块可能会不必要地触发；选择：训练负样本，并用一个 SILENT token 作为第二阶段「不作答」的输出；权衡：反应模块能抑制误触发，但也可能把那些不确定却其实有用的答案一并隐藏掉。
          evidence:: E9, E15
    - **实现边界:** 该实现使用经过缩放的视频帧、CLIP-L/14 视觉特征、用于流式决策的紧凑模型 Qwen2-1.5B，以及用于生成最终回复的 Qwen2-7B 模型。训练阶段整合了多个带时间信息的问答数据源，并在第二阶段冻结视频编码器和紧凑大语言模型，只训练交互模块。
      evidence:: E10
- ## Evaluation and Evidence
    - **实验设置:** 评测涵盖一个流式基准测试、一个由事件级时间任务转换而来的流式子集，以及常规的长视频问答。在流式设置中，问题被放在视频开头，模型需要在未来合适的时间戳处作答；而常规推理则把问题放在视频之后，以便进行公平比较。
      evidence:: E10, E12, E13
    - **主张-证据矩阵:** 证据在「基准测试层面优于此前的流式模型」这一点上最为有力；而在「部署层面的实时表现」上则较弱，因为所提供的文本中没有报告延迟、硬件条件和方差。
      claim_kind:: analyst_assessment
        - 论断 C1 由 StreamingBench 的总体表现以及在主动输出（Proactive Output）上相较 VideoLLM-online 的提升所支持，但需注意一个前提：两者模型输入的帧率不同。
          evidence:: E11
        - 论断 C2 由 ETBench 上的流式时间指标所支持，尤其是相较 VideoLLM-online 在时间视频定位（temporal video grounding）和密集视频描述（dense video captioning）上的表现。
          evidence:: E12
        - C3 由分割实验和词元消融实验（token ablations）支撑，C4 则由在 EgoSchema、MLVU 和 VideoMME 上的长视频问答准确率支撑。
          evidence:: E13, E14, E15
    - **关键结果:** 流式处理方面最主要的结果是：Dispider 在 StreamingBench 上取得 53.12 的总分，而 VideoLLM-online 为 32.48，其中主动输出（Proactive Output）从 3.92 提升到 25.34。在 ETBench 流式任务上，可直接对比的最大时序性能提升是时序定位（TVG）的 F1 值达到 36.1，而 VideoLLM-online 仅为 13.2。
      evidence:: E11, E12
        - StreamingBench：配置为 Dispider 7B、1 fps；基线为 VideoLLM-online 8B、2 fps；指标为总分和主动输出（PO）；方向为越高越好；差值为总分 +20.64、PO +21.42；未报告不确定性。
          evidence:: E11
        - ETBench 流式任务：配置为问题置于开头；基线为 VideoLLM-online；指标为时序定位（TVG）的 F1 值；方向为越高越好；差值为 +22.9；未报告重复次数。
          evidence:: E12
        - 传统长视频问答：配置为 7B、1 FPS；指标为准确率；Dispider 报告在 EgoSchema 上为 55.6、MLVU 上为 61.7、VideoMME 上为 57.2；其支撑属于对比性质，但并非在所列的每个基准上都达到了最先进水平。
          evidence:: E13
    - **消融与敏感性:** 消融实验支撑了本文的架构论述：基于场景的片段优于均匀切分的片段，而移除 ANS、TODO 和 SILENT 三个标记会严重损害时序和字幕生成指标。不过敏感性分析范围仍然狭窄，因为论文只测试了组件移除的影响，而没有测试很多部署相关的维度，例如延迟、流速、硬件或阈值校准。
      evidence:: E14, E15
    - **可复现性缺口:** 论文报告了代码和模型的发布，列出了主要模型、数据集以及推理时机的放置规则，但所提供的正文并未报告硬件、实际运行的延迟（wall-clock latency）、内存占用、随机种子、重复次数或置信区间。这些缺失很重要，因为该工作的核心承诺是实时交互，而不仅仅是离线基准上的准确率。
      claim_kind:: analyst_assessment
      evidence:: E10, E16
- ## Technical Judgment
    - **站得住的结论:** 本文对架构的诊断很有说服力：单一的自回归模型在生成内容时会阻塞感知过程，而把生成的回答文本从决策序列中移除是一种干净利落的系统级修复。消融实验把性能提升归因于场景分割和响应状态标记，而不仅仅归因于更大的回答模型，从而让这一设计不再显得含糊其辞。
      claim_kind:: analyst_assessment
      evidence:: E3, E7, E14, E15
    - **可能失效之处:** 在以下情况下收益可能减弱：场景边界不清晰时；正确的响应需要某些细微线索、而紧凑的决策模块无法保留这些线索时；或者部署延迟主要由检索和更大的反应模型主导时。论文目前的基准证据尚不足以证伪这些情形，因为它缺少硬件和延迟测量。
      claim_kind:: analyst_assessment
      evidence:: E5, E8, E10
    - **与已有工作的关系:** 与 VideoLLM-online 相比，技术上的差别不仅在于准确率，还在于并发能力：VideoLLM-online 使用同一个大语言模型循环来完成处理和响应，而 Dispider 把紧凑的决策循环与异步的响应生成分离开来。与 VideoStream 或 Flash-VStream 等长视频记忆系统相比，本文的侧重点不只是保持长上下文，还在于决定何时进行交互。
      claim_kind:: analyst_assessment
      evidence:: E3, E7, E11
    - **可迁移启发:** 对于实时多模态智能体，要把两个循环分开：一个是成本低的循环，负责维护状态并判断是否需要采取行动；另一个是成本高的循环，负责生成打磨过的输出。可复用的模式是在两个循环之间传递紧凑的行动标记和有依据的记忆，而不是传递完整的生成文本，因为在生成文本会阻塞感知的场景下这样做才行得通。
      claim_kind:: analyst_assessment
- ## Glossary
  collapsed:: true
    - 视频大语言模型（video large language model）：一种与视频特征相连的语言模型，因而能够回答关于随时间变化的视觉事件的问题。
    - 流式视频理解（streaming video understanding）：随着视频帧陆续到达就即时处理，而不是等到拿到完整的视频文件后才作答。
    - 主动实时交互（active real-time interaction）：在这种场景中，模型会在直播流进行的过程中自行决定何时开口，而不是只在最后等用户提问后才回答。
    - 感知、决策与反应（perception, decision, and reaction）：Dispider 的三种职责，即监控视频、判断是否需要回应，以及生成回应。
    - 自回归解码（autoregressive decoding）：逐个生成文本词元（token），在单循环设计中这一过程会占用大语言模型，从而阻塞其他工作。
    - 基于场景的切分（scene-based segmentation）：在视觉发生变化的边界处切分视频，使得切出的片段比固定长度的分块更贴近有意义的场景转换。
    - TODO 词元（TODO token）：一个特殊标记，用它的最终嵌入向量来判断系统应当继续等待还是作出回应。
    - ANS 词元（ANS token）：一个特殊标记，用于记录在某个时间戳生成过一个答案，同时不把生成的答案文本插入决策流中。
    - SILENT 词元（SILENT token）：反应模块输出的一个特殊标记，表示当触发并无必要时模型应当保持沉默。
    - 时间定位（temporal grounding）：把答案或事件描述关联到视频中正确的时间段。
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/metadata | Abstract | high
      locator:: Abstract and title block
      quote:: Dispider: Enabling Video LLMs with Active Real-Time Interaction via Disentangled Perception, Decision, and Reaction. Rui Qian, Shuangrui Ding, Xiaoyi Dong, Pan Zhang, Yuhang Zang, Yuhang Cao, Dahua Lin, Jiaqi Wang.
    - **E2:** problem/paper_statement | 1. Introduction | high
      locator:: Introduction, offline versus real-time setting
      quote:: The majority of current video LLMs are designed around an offline setting, where models are required to view the entire video before generating a single response. This offline approach is impractical for real-time, interactive scenarios.
    - **E3:** gap/paper_statement | 1. Introduction | high
      locator:: Introduction, VideoLLM-online limitation
      quote:: Since it uses a single LLM for video processing and response generation, it cannot perform perception and answer reaction simultaneously. The autoregressive nature of next-token prediction forces VideoLLM-online to alternate between perception and reaction.
    - **E4:** formula/paper_statement | 3.1. Problem Formulation | high
      locator:: Problem formulation, decision and reaction functions
      quote:: At each time t, the model observes context and video frames up to that time. It defines a decision function pi that chooses wait or respond, and a reaction function f that generates a response if responding.
    - **E5:** method/implementation_detail | 3.2. Proactive Streaming Video Processing | high
      locator:: Scene-based Perception Module
      quote:: We begin by adaptively segmenting the video into non-uniform clips based on scene boundaries. This segmentation strategy preserves the structural information of the video, allowing the model to focus on the most informative parts.
    - **E6:** algorithm/implementation_detail | 3.2. Proactive Streaming Video Processing | high
      locator:: Real-time Response Decision Module, sequence construction
      quote:: The module dynamically determines when to respond during video streaming by segmenting the video into non-uniform clips and utilizing historical memory to capture context. It combines memory features, clip features, question text, and special tokens.
    - **E7:** system_design/implementation_detail | 3.2. Proactive Streaming Video Processing | high
      locator:: Decision module after multi-answer input format
      quote:: None of the tokens we utilize originate from the responses generated by the Reaction module. This design ensures that the Decision module remains unblocked by the response generation process, allowing it to continuously monitor the video stream.
    - **E8:** algorithm/implementation_detail | 3.3. Asynchronous Interaction | high
      locator:: Temporal retrieval and KL loss
      quote:: Relevant historical clips are retrieved by computing their cosine similarity with the embedding of a designated TODO token. This procedure supports multi-hop reasoning, where relevant evidence may be distributed across multiple temporal segments.
    - **E9:** method/implementation_detail | 3.3. Asynchronous Interaction | high
      locator:: Positive and negative samples with SILENT token
      quote:: We introduce both positive and negative samples when training the interaction module. The model learns to either generate incremental, contextually enriched responses or produce a special SILENT token to indicate silence when appropriate.
    - **E10:** implementation/implementation_detail | 4.1. Implementation Details | high
      locator:: Implementation details, models and training data
      quote:: Dispider uses Qwen2-1.5B as the compact LLM for streaming decisions and Qwen2-7B for final responses. Training combines GroundVQA, ET-Instruct, 50K implicit QA pairs, and 122K streaming video QA pairs.
    - **E11:** result/experiment_result | 4.3. Streaming Video Understanding | medium
      locator:: Table 1, StreamingBench
      quote:: On StreamingBench, Dispider scores 53.12 overall, compared with VideoLLM-online at 32.48 and Flash-VStream at 24.04. On Proactive Output, Dispider reaches 25.34 while VideoLLM-online reaches 3.92.
    - **E12:** result/experiment_result | 4.3. Streaming Video Understanding | medium
      locator:: Table 3, streaming video QA inference
      quote:: In ETBench streaming video QA inference, Dispider reports TVG F1 36.1, EPM F1 15.5, TAL F1 27.3, VHD F1 54.2, DVC F1 33.8, and SLC F1 18.8.
    - **E13:** result/experiment_result | 4.4. Conventional Video Understanding | medium
      locator:: Table 2, long-video benchmarks
      quote:: On long-video benchmarks, Dispider reports 55.6 on EgoSchema, 61.7 on MLVU, and 57.2 on VideoMME using a 7B LLM and 1 FPS input, with fair-comparison columns for model size and sampled frames.
    - **E14:** ablation/ablation | 4.5. Ablation Study | medium
      locator:: Table 4, clip segmentation
      quote:: Scene-based segmentation improves over uniform segmentation: MLVU 61.7 versus 59.8, VideoMME 57.2 versus 55.4, TVG F1 36.1 versus 34.5, and DVC similarity 18.9 versus 18.1.
    - **E15:** ablation/ablation | 4.5. Ablation Study | medium
      locator:: Table 5, special token designs
      quote:: With ANS, TODO, and SILENT enabled, the model obtains TVG F1 36.1, DVC F1 33.8, and DVC similarity 18.9. With all three removed, the scores are 20.1, 19.7, and 12.3.
    - **E16:** metadata/paper_statement | Abstract | medium
      locator:: Abstract, release statement
      quote:: The code and model are released at https://github.com/Mark12Ding/Dispider. Experiments show that Dispider maintains strong performance in conventional video QA and surpasses previous online models in streaming scenario responses.
