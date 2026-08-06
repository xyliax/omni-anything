- **标题:** VideoLLM 知道何时开口：用视频-文本二重奏交互格式增强对时间敏感的视频理解（VideoLLM Knows When to Speak: Enhancing Time-Sensitive Video Comprehension with Video-Text Duet Interaction Format）
- **一句话总结:** 本文把视频与语言的交互重新表述为一个流式轮流发言的问题，展示了视频大语言模型（VideoLLM）在播放过程中自行决定何时开口，而不是等整段视频结束后再作答，从而能更自然地回答对时间敏感的问题。
- **论文类型:** 系统
- **发表:** arXiv 预印本 2025
- **作者:** Yueqian Wang、Xiaojun Meng、Yuxuan Wang、Jianxin Liang、Jiansheng Wei、Huishuai Zhang、Dongyan Zhao；北京大学、华为诺亚方舟实验室、北京通用人工智能研究院、通用人工智能国家重点实验室
- **关键词:** 视频大语言模型、流式视频理解、对时间敏感的视频理解、时间定位、密集视频描述、多答案时间定位视频问答
- ## Orientation
    - **背景:** 视频-语言系统的目标是描述动态场景并回答关于这些场景的问题。难点不仅在于识别画面中出现了什么，还在于把文字和事件发生的那个时刻对应起来。
      claim_kind:: analyst_assessment
    - **通俗问题:** 大多数系统的做法像一个人看完整段片子之后再作答。当视频还在持续播放，或者答案本应在相关时刻就给出时，这种做法就显得很别扭。
      claim_kind:: analyst_assessment
    - **为何困难:** 模型必须在还没看到后续画面之前，既判断出发生了什么变化，又判断出这个变化是否与用户的问题相关。
      claim_kind:: analyst_assessment
    - **一句话核心思路:** 把视频当作一个正在说话的一方，当当前画面足以支持一条回复时，就让助手打断播放来作答。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **阅读价值:** 把本文当作一篇关于交互格式的视频大语言模型（VideoLLM）论文来读：它主张对于实时或需要定位到具体时间点的理解任务而言，等待整段视频看完是一种错误的交互方式。
      claim_kind:: analyst_assessment
      evidence:: E2, E3
    - **一句话贡献:** MMDuet 让模型把视频帧当作一个数据流来观看，并在看完每一帧后判断是否应当输出回复，从而提升了对时间敏感的视频理解能力。
      evidence:: E3, E4, E5
    - **记忆模型:** 可以把视频想象成对话中的第三位说话者：它通过持续展示视频帧不断进行发言，而用户和助手在有话要说时可以插话打断。
      claim_kind:: analyst_assessment
      evidence:: E3
    - **最佳证据:** 最有力的证据在于，同一套流式表示方法能同时提升多项需要定位到具体时间点的任务，包括判断视频帧的相关性、密集描述的文本质量、多答案实时问答，以及主动输出。
      evidence:: E8, E9, E11, E12
        - 支持结论 C2：在零样本（zero-shot）设置下测试 QVHighlights 和 Charades-STA 两个数据集；受控条件下最接近的对比基线是 LLaVA-OV-VT；mAP 为 31.3，对比 19.0，R@IoU=0.5 为 42.4，对比 36.5；支持力度为中等，因为文中没有报告方差。
          evidence:: E8
        - 支持结论 C4：在 YouCook2 密集描述（dense captioning）任务上，去掉了此前助手轮次的内容；这是文中列出的、非 MMDuet 系统里文本质量最强的对比基线；CIDEr 为 8.8，对比 5.0；支持力度为中等，因为时间维度上的 F1 表现依然好坏参半。
          evidence:: E9
        - 支持结论 C1：在 Shot2Story-MAGQA 的长视频上测试；受控条件下最接近的对比基线是 LLaVA-OV-TC 和 LLaVA-OV-VT，它们都是在看完整段视频之后才作答；MMDuet 在 t=0.3 时的区间内得分（in-span score）为 2.63/2.45，对比 1.67/1.62 和 1.64/1.60；支持力度为中等，因为它是以牺牲准确率、换来大量重复轮次为代价的。
          evidence:: E11
        - 支持结论 C4：在 StreamingBench 的主动输出（Proactive Output）任务上测试；流式对比基线为 VideoLLM-Online 和 Dispider；MMDuet 在 t=0.4 时的准确率为 31.85，对比 3.92 和 25.34；支持力度为中等，因为在另一套评测协议下，非流式的商用系统得分更高。
          evidence:: E12
    - **主要边界:** 本文展示的是一种有用的交互模式，而不是一个完全成熟的实时系统：时机的把控仍然依赖阈值、平滑处理以及重复回复的抑制，而且结果表格没有报告统计上的不确定性。
      claim_kind:: analyst_assessment
      evidence:: E10, E14
- ## Argument Map
    - **问题与重要性:** 本文针对的是时间敏感的视频理解（time-sensitive video comprehension）：即模型必须把语言和视频中特定时刻对应起来的任务，而不只是在所有帧都可用之后做个总结。看完整段视频再交互的方式，会阻碍诸如安防监控或直播辅助这类实时应用，还会迫使时间定位（temporal grounding）依赖脆弱的文本输出来完成。
      evidence:: E2
    - **已有方法缺口:** 以往的视频大语言模型（VideoLLM，即把视频的视觉特征与语言模型结合、从而能用文本回答或描述视频内容的模型）研究，大多改动的是模型架构、训练数据，或对时间的文本表示方式（例如用秒数、百分比或特殊标记来表示时间）；而交互形式本身却很少被深入研究。与本文最接近的是 VideoLLM-Online，但作者指出，它并没有广泛测试流式交互如何改变模型的零样本时间敏感能力（零样本指模型无需针对该任务专门训练即可完成任务）。
      evidence:: E16
    - **关键洞见:** 如果把视频流本身当作对话中的一个参与者，那么回应的时机就成了建模问题的一部分，而不再只是事后附加的一串时间戳字符串。这样一来，模型可以从局部的帧级证据中学习，并让生成的回应紧贴正在被描述的那个时刻。
      evidence:: E3, E4
    - **核心主张:** 本文的论点链条是：改变对话的轮流发言方式（turn-taking），能为时间敏感的视频推理提供更好的监督目标；而且这套做法只需适度的训练，就能加到一个已有的强大骨干模型上。
      evidence:: E3, E4, E6, E8
        - 论点 C1：视频-文本二重奏交互形式（video-text duet interaction format，指本文提出的一种交互规则：视频流、用户和助手轮流发言，且文本可以在视频播放过程中插入）能够实现实时回应，因为模型可以在处理完任意一帧之后就打断发言，而不必等到整段视频播放结束才轮到自己。
          evidence:: E3, E5, E10
        - 论点 C2：设置独立的信息量头（informative head）和相关性头（relevance head）来判断回应时机，比只让语言模型头去输出一个特殊的「打断」标记，能提供更好的时机信号。
          evidence:: E4, E8
        - 论点 C3：MMDuetIT 是一个包含 10.9 万条样本的指令微调数据集，由密集字幕（dense captioning）、有依据的问答（grounded QA）和时间定位（temporal grounding）等来源的数据改写而成；它足以把 LLaVA-OneVision 骨干模型适配到二重奏形式。
          evidence:: E6, E7
        - 论点 C4：MMDuet 在多项时间敏感任务上都有提升，但提升最明显的场景，是那些「帧级相关性」或「及时输出」比「精确生成起止时间段」更重要的任务。
          evidence:: E8, E9, E11, E12
- ## Mechanism and Design
    - **核心机制:** MMDuet 保留了通常的视频大语言模型（VideoLLM）技术栈，但为每一帧的最后一个视觉标记，在其最终隐藏状态上额外加了两个二分类器。信息量头（informative head）用来估计这一帧是否带来了足够多的新内容，相关性头（relevance head）则用来估计这一帧是否与用户的提问相关。
      evidence:: E4
        - 信息量分数是根据「片段-字幕」的时间信息来训练的：在某个片段已经被看到足够多、并且在插入回应之前的那些帧，被标为正样本。
          evidence:: E13
        - 相关性分数是根据时间定位（temporal grounding）标注来训练的，并且可以直接复用于高光片段检测（highlight detection）和时间定位（temporal localization）任务。
          evidence:: E4, E6, E8
    - **数据/控制流:** 在推理阶段，MMDuet 按时间戳顺序处理用户的文本轮次和视频帧，并更新键值注意力缓存（KV cache），也就是保存下来的 Transformer 注意力状态，用它来避免重新计算之前已经处理过的词元。每处理完一帧，MMDuet 会计算信息量分数（informative score）和相关性分数（relevance score），调用针对具体任务的 need_response 规则，只有当该规则触发时才生成一个文本轮次。
      evidence:: E5
        - 在密集视频字幕（dense video captioning）任务中，need_response 会持续累加信息量分数，直到达到某个阈值，此时输出一条字幕，然后把累加和清零。
          evidence:: E9
        - 在多答案定位视频问答（Multi-Answer Grounded Video Question Answering，MAGQA）任务中，当前帧的信息量分数与相关性分数之和超过阈值 t 时，need_response 就会触发。
          evidence:: E10
        - 在精彩片段检测（highlight detection）和时序定位（temporal grounding）任务中，相关性分数序列会先做归一化或阈值处理，然后再与邻近帧一起做平滑。
          evidence:: E8
    - **设计决策:** 最主要的设计选择，是把时间上的判断从生成的时间戳文本转移到帧级分数上，同时仍然用语言模型来生成自然语言内容。这是一种务实的折中：它避免了强迫模型去精确地数时间，但也引入了针对具体任务的阈值和平滑处理。
      claim_kind:: analyst_assessment
      evidence:: E4, E8, E14
        - 需求：支持实时视频流；选择：把视频流当作除用户和助手之外的第三个角色；最接近的替代方案：对整段视频进行一次性的问答式交互；代价：模型在实时说话时无法访问未来的视频帧。
          claim_kind:: analyst_assessment
          evidence:: E2, E3, E14
        - 需求：判断什么时候该说话；选择：用有监督训练的信息量分类头（informative head）和相关性分类头（relevance head）；最接近的替代方案：像 VideoLLM-Online 那样使用一个特殊的语言词元；代价：可控性更好，但需要额外的标注和阈值。
          evidence:: E4, E16
        - 需求：教会模型及时回应，但又不要过早回应；选择：在每个标注片段的中点之后随机插入回应，并把多个帧标注为信息量帧；代价：这依赖于经验性的时机假设，而不是学出来的、能感知未来的边界。
          evidence:: E13
    - **实现边界:** 该实现在 LLaVA-OneVision 主干模型的基础上做了改动，加入了可训练的投影层、信息量分类头、相关性分类头，以及低秩适配（Low-rank adaptation，LoRA），即对选定的语言模型权重施加一个小规模的可训练更新，同时让大部分参数保持冻结。它还减少了每帧的视觉词元数量，并对采样帧数设置上限，以便在受控的显存条件下进行训练和推理。
      evidence:: E7
        - 据报告，训练在 MMDuetIT 数据集上进行了一个 epoch，在八块 Tesla V100 GPU 上大约耗时一天，推理则在一块 Tesla V100 GPU 上完成。
          evidence:: E7
        - 流式循环依赖对视频帧和文本轮次的键值缓存（KV cache）更新，这是必要的，因为在处理每一帧之后，都会复用同一个不断增长的对话状态。
          evidence:: E5
- ## Evaluation and Evidence
    - **实验设置:** 评测涵盖以下任务：在 QVHighlights 上的高亮检测、在 Charades-STA 上的时序定位、在 YouCook2 上的密集视频描述、在 Shot2Story-MAGQA-39k 上的多答案定位视频问答（MAGQA），以及在 StreamingBench 上的主动输出。论文与三类方法作比较：基于时间戳的视频大语言模型（VideoLLM）、流式基线，以及在相同数据上训练但采用类 TimeChat 或类 VTimeLLM 格式的受控 LLaVA-OneVision 变体。
      evidence:: E7, E8, E10, E12
    - **主张-证据矩阵:** 证据在两方面最为充分：C2 关于帧级相关性、C4 关于流式输出。在 C1 关于实时问答方面证据中等，因为基线获得了更简单的离线设置。在密集描述的精确时序区间方面证据最弱。
      claim_kind:: analyst_assessment
      evidence:: E8, E9, E11, E12
        - C1 由 MAGQA 和 StreamingBench 支持，因为 MMDuet 在播放过程中即时输出；但随着阈值 t 减小，MAGQA 分数会提高，代价是产生更多重复轮次、每个样例耗时更长。
          claim_kind:: analyst_assessment
          evidence:: E10, E11, E12
        - C2 由 QVHighlights 和 Charades-STA 支持，其中直接的帧级相关性打分优于受控基线以文本形式输出的区间。
          evidence:: E8
        - C3 得到部分支持：论文报告了从强骨干网络出发、使用少量数据、单轮（one-epoch）适配的结果，但除了受控的 LLaVA-OneVision 变体之外，并未把源自骨干网络本身能力的所有收益单独区分出来。
          claim_kind:: analyst_assessment
          evidence:: E6, E7
        - C4 在多个任务上都得到支持，但密集描述展现了其边界：去除先前的响应之后，文本指标有所提升，而时序分割的 F1 并未明显更好。
          claim_kind:: analyst_assessment
          evidence:: E9
    - **关键结果:** 最清晰的定量优势体现在帧相关性上：MMDuet 在 QVHighlights 上报告的 mAP/HIT@1 为 31.3/49.6，在 Charades-STA 上的 R@IoU=0.5/0.7 为 42.4/18.0，在两个数据集上均超过受控的 LLaVA-OV-VT 基线。在 MAGQA 上，MMDuet 能够实时运行，并在长视频上有大幅提升；StreamingBench 则显示它与流式/主动式的开源基线相当或更优。
      evidence:: E8, E11, E12
        - 支持的论点：C2；配置：零样本帧相关性；基线：LLaVA-OV-VT；指标与方向：更高的 QVHighlights mAP/HIT@1 与 Charades-STA R@IoU；差值：mAP +12.3、R@0.5 +5.9。
          evidence:: E8
        - 支持的论点：C1；配置：5 倍时长延长的 MAGQA；基线：LLaVA-OV-TC；指标与方向：更高的区间内（in-span）分数；在 t=0.3 时的差值：+0.96/+0.83，未报告重复次数。
          evidence:: E11
        - 支持的论断：C4；配置：StreamingBench Proactive Output（主动输出）；基线：流式系统中的 Dispider；指标与方向：准确率越高越好；差值：MMDuet 在 t=0.4 时比 Dispider 高出 6.51 个百分点。
          evidence:: E12
    - **消融与敏感性:** 消融实验的证据虽然范围有限，但很有价值：在 YouCook2 数据集上，关闭随机回答位置或多帧信息性标签，都会损害论文报告的密集字幕（dense-captioning）指标。敏感性分析的数据还表明，平滑窗口 w 和密集字幕阈值 s 存在可容忍的取值范围，但这些仍然是靠经验调节的旋钮，而非通过学习得到的策略。
      evidence:: E13, E14
        - 去掉随机回答位置后，YouCook2 上的指标从 2.9/8.8/21.7 降到 2.1/7.3/19.0，这支持了「回答时机的多样性很重要」这一论断。
          evidence:: E13
        - 去掉多帧信息性标签后，YouCook2 上的指标从 2.9/8.8/21.7 变为 2.9/8.0/16.5，这支持了「预测头应当学习一个回答区间，而不是单个触发帧」这一论断。
          evidence:: E13
    - **可复现性缺口:** 论文报告了主干网络、训练资源、超参数、采样设置、指标定义，以及对 MAGQA 的一次人工质量检查，但所提供的文本没有报告代码、模型检查点、随机种子、重复实验次数、置信区间，也没有报告完整的提示词或评估器稳定性——只提到用两个打分模型来计算区间内得分（in-span score）。因此，这些结果在方向上是有参考价值的，但统计上的可靠性和端到端的可复现性仍未解决。
      claim_kind:: analyst_assessment
      evidence:: E7, E10, E15
- ## Technical Judgment
    - **站得住的结论:** 核心机制之所以令人信服，是因为它改变了被预测的对象：帧级别的「有用性」和「相关性」比生成的时间戳字符串更容易监督和使用。受控的基线实验让「交互格式很重要」这一论点比单纯的模型规模比较更有说服力，在 QVHighlights 和 Charades-STA 上尤其如此。
      claim_kind:: analyst_assessment
      evidence:: E4, E7, E8
    - **可能失效之处:** 当正确的回答需要依赖未来的证据、需要精确的片段起始点，或需要抑制几乎重复的多轮回答时，该方法表现最弱。它还依赖于手工设定的 need_response 阈值和平滑窗口，因此部署时的效果可能会随视频节奏和任务的不同而变化。
      claim_kind:: analyst_assessment
      evidence:: E9, E10, E14
    - **与已有工作的关系:** 与基于时间戳数字或百分比的视频大语言模型（VideoLLM）相比，MMDuet 把时间外化为流位置和帧得分，从而减轻了语言模型去计数并输出精确数字的负担。与 VideoLLM-Online 相比，它把「为什么要发言」拆分成信息性得分和相关性得分，而不是用单一的生成式打断信号来表示。
      claim_kind:: analyst_assessment
      evidence:: E4, E16
    - **可迁移启发:** 对于多模态系统，接口格式本身可以成为一个学习目标：当任务需要及时行动时，就在系统必须做决策的生命周期节点上训练显式的状态信号，然后让生成过程只负责内容。这一模式的适用范围不止于视频，还能推广到那些必须在数据流中决定何时通知、何时提问、何时行动的智能体（agent）。
      claim_kind:: analyst_assessment
      evidence:: E3, E4, E5
- ## Glossary
  collapsed:: true
    - 视频大语言模型（Video large language model）：一种把视频的视觉特征与语言模型结合起来的模型，从而能够用文本回答或描述视频内容。
    - 视频-文本二重奏交互格式（Video-text duet interaction format）：论文提出的交互规则，让视频流、用户和助手轮流发言，并允许在视频播放过程中插入文本。
    - 时间敏感的视频理解（Time-sensitive video comprehension）：一类视频理解任务，其答案必须与事件发生的时间相绑定，例如时间定位、精彩片段检测或密集字幕生成。
    - MMDuetIT：一个指令微调数据集，通过把密集字幕生成、多答案有依据问答和时间定位等数据重新改写成二重奏交互格式而构建。
    - 多答案有依据视频问答（Multi-Answer Grounded Video Question Answering）：一类任务，用户提出的同一个问题可能需要在同一段视频的不同相关时刻给出多个答案。
    - 信息量头与相关性头（Informative head and relevance head）：为 MMDuet 添加的两个二分类器，其中一个判断当前帧是否带来新信息，另一个判断当前帧是否与用户查询相关。
    - 键值注意力缓存（Key-value attention cache）：保存下来的、来自先前词元或帧的注意力状态，使 Transformer 能够在不断增长的流上继续处理，而无需重新计算此前的全部上下文。
    - need_response：一条与具体任务相关的规则，它把当前及此前的信息量分数或相关性分数转化为一个判断，即助手此刻是否应该发言。
    - 任务指标（Task metrics）：论文使用了检索/定位类指标、字幕质量指标和主动输出指标；本笔记引用的所有指标均为数值越高越好。
    - 区间内分数（In-span score）：MAGQA 的一个指标，仅当预测答案的预测时间落在某个真实答案时间区间内时才对该答案打分，并使用一个语言模型来评估文本相似度。
    - 低秩适配（Low-rank adaptation）：一种参数高效的微调方法，只训练小规模的低秩更新，同时保持模型的大部分权重不变。
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/metadata | Title and author block | high
      locator:: arXiv header and title block
      quote:: arXiv:2411.17991v2 [cs.CV] 23 Nov 2025. VideoLLM Knows When to Speak: Enhancing Time-Sensitive Video Comprehension with Video-Text Duet Interaction Format. Yueqian Wang, Xiaojun Meng, Yuxuan Wang, Jianxin Liang, Jiansheng Wei, Huishuai Zhang, Dongyan Zhao.
    - **E2:** problem/paper_statement | 1 Introduction | high
      locator:: intro discussion of whole video interaction
      quote:: this limits its usage in more scenarios like live broadcasts or surveillance videos, in which the video does not end at a specific time. Even if we can segment the video into multiple fixed-length clips for input, the model still cannot generate responses in a real-time manner when necessary
    - **E3:** method/paper_statement | 3 The Video-Text Duet Interaction Format | high
      locator:: Section 3 formal definition
      quote:: we consider the video stream as a conversation participant just like the role of user/assistant, and the input sequence consists of alternating turns among these three roles. When each single frame is consumed, both the user and the assistant role can interrupt the video stream at any time
    - **E4:** implementation/implementation_detail | 4.1 Model Structure | high
      locator:: two added heads paragraph
      quote:: The only difference in model structure between our MMDuet and existing VideoLLMs is that we add two more heads in addition to the language modeling head, namely the informative head and the relevance head, for determining whether to start a response after each frame.
    - **E5:** algorithm/implementation_detail | 4.2 Inference Procedure | high
      locator:: inference procedure paragraph and Listing 1
      quote:: When consuming every single sampled frame of the video, we first check if there is a user query happening at this time. Then the sampled frame is input to the model, after which the informative score and relevance score are calculated. We use a function need_response to estimate whether the model should generate an assistant response
    - **E6:** method/paper_statement | 5 MMDuetIT: Dataset for Training MMDuet | high
      locator:: Sections 5.1 to 5.4
      quote:: MMDuetIT is composed of three different types of tasks that benefit our model training: dense captioning, multi-answer grounded video question answering, and temporal video grounding. The data distribution of MMDuetIT is shown in Fig. 3. Note that this dataset only contains 109k examples
    - **E7:** experiment_setup/paper_statement | 6 Experiments | high
      locator:: implementation and baselines paragraphs
      quote:: MMDuet is initialized with LLaVA-OneVision. We train the model on MMDuetIT for one epoch. The training takes about one day on a node with 8 Tesla V100 GPUs, and the inference runs on 1 Tesla V100 GPU. Since the initialization of MMDuet is stronger than that of the baselines, for a fair comparison we also conduct a controlled experiment
    - **E8:** result/experiment_result | 6.1 Highlight Detection and Temporal Video Grounding | medium
      locator:: Table 1 and Section 6.1 discussion
      quote:: Table 1: Zero-shot performance on highlight detection, temporal video grounding, and dense video captioning. LLaVA-OV-VT reports QVHighlights 19.0/40.0 and Charades-STA 36.5/12.3, while MMDuet reports QVHighlights 31.3/49.6 and Charades-STA 42.4/18.0.
    - **E9:** result/experiment_result | 6.2 Dense Video Captioning | medium
      locator:: Table 1 and dense captioning discussion
      quote:: MMDuet does not show significant improvements on F1 metric, likely due to the simple solution we use to derive the start and end time based on responses. Even so, the CIDEr and SODA_c metric of MMDuet is still higher than all baselines. Table 1 reports + rm. prev. resp. as 2.9/8.8/21.7.
    - **E10:** experiment_setup/paper_statement | 6.3 Multi-Answer Grounded Video QA | high
      locator:: task and metric definition paragraphs
      quote:: MAGQA requires the answers to be both informative and related to the question, we set need_response as: if the sum of informative score and relevance score of a frame is larger than a threshold t, then the model needs to generate a response right after this frame.
    - **E11:** result/experiment_result | 6.3 Multi-Answer Grounded Video QA | medium
      locator:: Table 2 and prolonged-video discussion
      quote:: MMDuet t = 0.3 reports original in-span score 3.13/2.93 and 5-time prolonged video score 2.63/2.45. LLaVA-OV-TC reports 2.77/2.64 original and 1.67/1.62 prolonged, while LLaVA-OV-VT reports 2.54/2.42 original and 1.64/1.60 prolonged.
    - **E12:** result/experiment_result | 6.4 Proactive Output on StreamingBench | medium
      locator:: Tables 3 and 6
      quote:: Table 3: Performance on the Proactive Output task of StreamingBench. Flash-VStream 1.96, VLLM-Online 3.92, Dispider 25.34, MMDuet 29.44. Table 6 reports MMDuet t = 0.4 at 31.85.
    - **E13:** ablation/ablation | 6.5 Ablation Studies | medium
      locator:: Table 4 and ablation paragraph
      quote:: We conduct ablation studies on YouCook2 dense video captioning to assess two empirical yet important findings: randomly inserting the response at a position from 50% to 75% of the corresponding video segment, and setting informative head's label to TRUE for all frames between 50% of the segment and the response time. Table 4 reports MMDuet 2.9/8.8/21.7, w/o rand. resp. pos. 2.1/7.3/19.0, and w/o multi informative 2.9/8.0/16.5.
    - **E14:** limitation/limitation | Limitations | high
      locator:: Limitations paragraph
      quote:: Some hyperparameters are required during inference. Information from subsequent frames is not incorporated when generating in-time responses for the current frame. Slow inference speed. A better inference process is needed for avoid generating duplicate responses. Real-time response datasets with longer live-streaming videos are required
    - **E15:** experiment_setup/case_study | A Data Quality Check of Shot2Story-MAGQA-39k | medium
      locator:: Appendix A
      quote:: We sample 100 examples with 290 answers from our test set for manual quality assessment. Among the sampled examples, we find 1 example with a question unanswerable from the video, 5 examples have 6 answers that contradict the video content, and 5 examples have 7 answers unrelated to the question.
    - **E16:** prior_work/paper_statement | 2 Related Works | high
      locator:: related work comparison paragraphs
      quote:: Recent works attempt to empower VideoLLMs with the ability to localize and represent segments in videos. These works explore new ways on how to easily represent video clips with texts, such as second numbers of timestamp, timeline percentage or using special textual tokens. The work most similar to our motivation is VideoLLM-Online
