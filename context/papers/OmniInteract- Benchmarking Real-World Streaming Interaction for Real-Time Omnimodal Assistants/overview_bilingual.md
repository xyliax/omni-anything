- **Title:** OmniInteract: Benchmarking Real-World Streaming Interaction for Real-Time Omnimodal Assistants
  **标题:** OmniInteract：面向实时全模态助手、评测真实世界流式交互能力的基准
- **Summary:** OmniInteract turns real-time audio-visual assistance into a measurable benchmark by preserving spoken queries and stream timing, showing that current omnimodal assistants still struggle with when to speak, when to wait, when to stop, and when to resume.
  **一句话总结:** OmniInteract 保留口语提问与流的时间信息，把实时的音视频辅助任务变成可量化的基准。它揭示出，当前的全模态助手在何时开口、何时等待、何时停止、何时恢复这几件事上仍然做得不好。
- **Paper Type:** benchmark
  **论文类型:** 基准（benchmark）
- **Venue:** arXiv preprint 2026
  **发表:** arXiv 预印本 2026
- **Authors:** Xudong Lu (CUHK MMLab), Xueying Li (SJTU), Annan Wang (NTU), Yang Bo (McMaster), Jinpeng Chen (CityUHK), Zengliang Li (JUFE), Nianzu Yang (SJTU), Rui Liu (CUHK MMLab), Xue Yang (SJTU), Jingwen Hou (JUFE), Hongsheng Li (CUHK MMLab)
  **作者:** Xudong Lu（CUHK MMLab）、Xueying Li（SJTU）、Annan Wang（NTU）、Yang Bo（McMaster）、Jinpeng Chen（CityUHK）、Zengliang Li（JUFE）、Nianzu Yang（SJTU）、Rui Liu（CUHK MMLab）、Xue Yang（SJTU）、Jingwen Hou（JUFE）、Hongsheng Li（CUHK MMLab）
- **Keywords:** omnimodal assistants, streaming interaction, audio-visual benchmark, full-duplex interaction, response timing, interruption handling, nested interaction, 1QnA monitoring
  **关键词:** 全模态助手、流式交互、音视频基准、全双工交互、应答时机、打断处理、嵌套交互、1QnA 监控
- ## Orientation
    - **Background:** Some assistants now combine video, sound, speech, and text in one system. A live assistant must treat the world as a stream, not as a finished clip.
      **背景:** 如今有些助手把视频、声音、语音和文本整合在一个系统里。一个实时助手必须把外部世界当作持续到来的数据流来处理，而不是当作一段已经录好的完整片段。
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A person may ask a question aloud, point the camera somewhere, get interrupted, or wait for something to happen. The assistant has to decide whether now is the moment to speak.
      **通俗问题:** 用户可能会开口提问、把摄像头对准某处、中途被打断，或者在等待某件事发生。助手必须判断此刻是不是开口回应的时机。
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** The evidence arrives over time, and speaking too early can be as wrong as saying the wrong thing. The assistant must also remember paused requests while handling new ones.
      **为何困难:** 证据是随时间陆续到来的，开口太早和说错话一样都是错误。助手还必须记住那些被暂停的请求，同时处理新的请求。
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Mark the moments when a response becomes possible, then judge both the answer and the timing around those moments.
      **一句话核心思路:** 标记出可以给出回应的那些时刻，然后围绕这些时刻同时评判答案本身和回应的时机。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as an evaluation paper for real-time omnimodal large language models, systems that process vision, audio, speech, and text together; it targets the gap between recognizing video content offline and managing a live interaction loop.
      **阅读价值:** 把它当作一篇针对实时全模态大语言模型（omnimodal large language model）的评测论文来读。这类模型能同时处理视觉、音频、语音和文本；本文关注的是一个空白：模型离线识别视频内容是一回事，管理一个实时的交互回路又是另一回事。
      claim_kind:: analyst_assessment
      evidence:: E1, E2
    - **One-Sentence Contribution:** OmniInteract benchmarks live audio-visual assistants by converting a continuous stream into timed response opportunities where the model must detect intent, wait for evidence, answer, and control its speech.
      **一句话贡献:** OmniInteract 通过把连续的音视频流转换成带时间标注的应答机会，来评测实时的音视频助手——模型必须在这些机会中识别意图、等待证据、给出回答，并控制自己的说话行为。
      evidence:: E1, E6
    - **Mental Model:** Picture a person helping while watching a video with you: the hard part is not only knowing the answer, but noticing the right cue, speaking at the right time, pausing when interrupted, and returning to unfinished business.
      **记忆模型:** 可以想象有个人陪你一起看视频、随时帮你：难点不只是知道答案，还在于捕捉到对的提示、在对的时机开口、被打断时暂停下来，以及回过头去把没做完的事继续做完。
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is that four representative native real-time models remain weak on the benchmark, especially on long-horizon monitoring and nested resumption.
      **最佳证据:** 最有力的证据是：四个有代表性的原生实时模型在该基准上表现依然薄弱，尤其是在长时间跨度的持续监控以及嵌套任务的恢复上。
      evidence:: E10, E11, E12, E14
        - Supports C1: benchmark comparison; prior streaming benchmarks mainly use text queries, offline inference, or custom protocols; coverage dimensions add spoken audio queries, native online inference, 1QnA, nested interaction, and interruption; support status: direct design comparison.
          支持 C1：基准对比；此前的流式基准主要使用文本查询、离线推理或自定义协议；本研究在覆盖维度上新增了口语音频查询、原生在线推理、1QnA、嵌套交互与打断；支持状态：直接的设计对比。
          evidence:: E2
        - Supports C3: four native real-time models; closest baseline is the best competing model in the same table; All Global IA-QTF1 tops out at 0.368 and best 1QnA IA-QTF1 at 0.052; support status: moderate because no variance or repeat counts are reported.
          支持 C3：四个原生实时模型；最接近的基线是同一表格中表现最好的竞争模型；All Global IA-QTF1（交互感知质量-时效 F1，Interaction-Aware Quality-Timeliness F1）的最高值为 0.368，最佳的 1QnA IA-QTF1 为 0.052；支持状态：中等，因为没有报告方差或重复次数。
          evidence:: E10, E12
        - Supports C4: MiniCPM-o 4.5 mathematical reasoning; baseline is offline full-input inference; pure quality score drops from 0.6833 to 0.3475, a -0.3358 absolute change; support status: moderate because it covers one model and task family.
          支持 C4：MiniCPM-o 4.5 的数学推理；基线为离线全输入推理；纯质量得分从 0.6833 下降到 0.3475，绝对变化为 -0.3358；支持状态：中等，因为它只覆盖了一个模型和一类任务。
          evidence:: E14
    - **Main Caveat:** The benchmark is informative but not yet broad enough to establish general real-time assistant capability across languages, domains, model families, or speech conditions.
      **主要边界:** 该基准很有参考价值，但覆盖面还不足以证明模型在跨语言、跨领域、跨模型家族或跨语音条件下具备通用的实时助手能力。
      claim_kind:: analyst_assessment
      evidence:: E15
- ## Argument Map
    - **Problem and Stakes:** The paper argues that offline video question answering and text-prompted streaming tests miss the live interaction loop of omnimodal large language models, systems that combine visual, audio, speech, and text inputs. The stake is whether a model can detect spoken intent, ground it in unfolding audio-visual evidence, answer at the right time, and avoid disruptive outputs.
      **问题与重要性:** 论文提出，离线视频问答和以文本提示为主的流式测试忽略了全模态大语言模型（omnimodal large language model，指把视觉、音频、语音和文本输入整合在一个系统里的模型）的实时交互循环。关键在于：模型能否识别口语中的意图、把意图落实到不断展开的视听证据上、在正确的时机作答，并避免产生扰乱性的输出。
      evidence:: E1, E2
    - **Prior Gap:** Prior streaming video benchmarks often keep the video stream but remove the natural query channel by giving text prompts, or they evaluate pre-segmented clips rather than the model's native real-time interface. This decouples perception from spoken intent recognition, timing control, interruption handling, and context resumption.
      **已有方法缺口:** 此前的流式视频基准往往保留了视频流，却通过给出文本提示的方式去掉了自然的查询通道，或者它们评估的是预先切好的片段，而不是模型原生的实时接口。这样就把感知与口语意图识别、时机控制、打断处理和上下文恢复割裂开来。
      evidence:: E2
    - **Key Insight:** A continuous interaction can be evaluated if each expected response is represented as a temporally grounded response opportunity (interaction slot) with a trigger, the first valid answer time, the window close, and a target answer. That turns fuzzy live dialogue into aligned decisions about whether, when, and what to say.
      **关键洞见:** 只要把每一个预期的回答表示成一个「有时间锚定的回答机会」（即交互槽，interaction slot），就可以对一段连续交互进行评测；这个交互槽包含触发条件、第一个有效的回答时刻、窗口关闭时刻以及目标答案。这样一来，模糊不清的实时对话就转化为一系列对齐的判断，即要不要回答、什么时候回答、以及回答什么。
      evidence:: E6
    - **Claims:** The paper's claim chain is best read as four falsifiable claims about benchmark coverage, scoring, model weakness, and offline-online transfer.
      **核心主张:** 这篇论文的论证链条最好理解为四个可证伪的主张，分别关于基准的覆盖范围、评分方式、模型的弱点，以及从离线到在线的能力迁移。
      claim_kind:: analyst_assessment
        - C1: OmniInteract covers a missing evaluation setting by preserving spoken audio queries, visual events, ambient sounds, native online inference, 1Q1A local interactions, 1QnA continuous monitoring, nested interactions, and interruptions.
          C1：OmniInteract 覆盖了一种此前缺失的评测场景，它保留了口语音频提问、视觉事件、环境声音、原生的在线流式推理（native online inference）、1Q1A 局部交互、1QnA 连续监测、嵌套交互以及打断行为。
          evidence:: E1, E2, E3
        - C2: The interaction slot formulation plus Interaction-Aware Quality-Timeliness F1 (IA-QTF1), Interruption Diagnostic Suite (IDS), and Nested Chain Completion Score (NCCS) makes content quality, timing, spillover, interruption behavior, and resumption measurable in one benchmark.
          C2：交互槽这一建模方式，再加上「交互感知的质量-时效性 F1」（Interaction-Aware Quality-Timeliness F1，IA-QTF1）、「打断诊断套件」（Interruption Diagnostic Suite，IDS）和「嵌套链完成度评分」（Nested Chain Completion Score，NCCS），使得内容质量、时机、溢出、打断行为以及恢复行为都可以在同一个基准中被测量。
          evidence:: E6, E7, E8
        - C3: Current native real-time omnimodal models are weak on this setting, with the best All Global IA-QTF1 reaching 0.368 and the best 1QnA IA-QTF1 reaching only 0.052.
          C3：当前原生的实时全模态模型在这一场景中表现薄弱，最好的 All Global IA-QTF1 只达到 0.368，而最好的 1QnA IA-QTF1 仅达到 0.052。
          evidence:: E10, E12
        - C4: Offline multimodal reasoning quality does not reliably transfer to full-duplex real-time interaction, where a model listens and generates at the same time; MiniCPM-o 4.5 loses 0.3358 pure-quality points in the paper's online math setting.
          C4：离线多模态推理的质量并不能可靠地迁移到全双工实时交互（full-duplex real-time interaction，即模型一边听一边生成的场景）；在论文设定的在线数学场景中，MiniCPM-o 4.5 损失了 0.3358 个纯质量分。
          evidence:: E14
- ## Mechanism and Design
    - **Core Mechanism:** OmniInteract's core mechanism is the interaction slot: a time window from observation start to window close, with an answer becoming valid at a specific moment inside it. Generated chunks are assigned to slots by timestamp, split around the valid-answer time when necessary, and then scored for answer quality and timing.
      **核心机制:** OmniInteract 的核心机制是交互槽：这是一个从观察开始到窗口关闭的时间窗口，在窗口内部的某个特定时刻，答案开始变得有效。模型生成的文本片段（chunk）会按时间戳被分配到各个交互槽中，必要时会在有效回答时刻处进行切分，然后再对答案质量和时机进行评分。
      evidence:: E6, E7
    - **Data / Control Flow:** The benchmark flow is: construct audio-visual recordings, annotate slots, replay each recording chronologically through the model's native real-time interface, timestamp model chunks, align chunks to slots, and score each slot. The model receives only past and current stream content, not future frames, future audio, or slot boundaries.
      **数据/控制流:** 基准的流程如下：构建视听录制内容，标注交互槽，按时间顺序把每段录制内容回放给模型的原生实时接口，为模型生成的片段打上时间戳，将这些片段对齐到相应的交互槽，最后对每个交互槽评分。模型只能接收到过去和当前的流内容，无法看到未来的画面帧、未来的音频或交互槽的边界。
      evidence:: E4, E5, E9
        - The 1Q1A split is self-recorded and covers explicit real-time queries, proactive requests whose evidence appears later, and nested cases where an inserted query interrupts an ongoing proactive request.
          1Q1A 子集是自行录制的，覆盖三类情形：显式的实时提问、证据在稍后才出现的主动式请求，以及嵌套情形（即一个插入的提问打断了正在进行的主动式请求）。
          evidence:: E3, E4
        - The 1QnA split converts procedural or task-oriented videos into one initial spoken instruction followed by multiple timed response slots for guidance or error detection.
          1QnA 子集把流程性或任务导向的视频转化为一条初始的口语指令，随后跟着多个带时间约束的回答槽，用于提供指导或检测错误。
          evidence:: E5
        - Open-ended outputs are judged against ground-truth answers, with the judge also identifying the earliest answer-bearing phrase used to compute the timeliness factor.
          开放式输出会与标准答案（ground-truth answer）进行比对评判，评判器同时找出最早出现的、包含答案的短语，用来计算时效性系数。
          evidence:: E16
    - **Design Decisions:** The benchmark chooses native audio-visual replay over converted text QA, slot-level annotation over free-form transcript review, and targeted diagnostics over one aggregate score. These choices make the benchmark harder to run but closer to the behavior expected from a live assistant.
      **设计决策:** 该基准测试选择了原生的音视频回放，而不是转换后的文本问答；选择了槽位级别（slot-level）的标注，而不是自由格式的转录文本审阅；选择了有针对性的诊断，而不是单一的总分。这些选择让基准测试更难运行，但更贴近真实场景中一个实时助手应有的行为。
      claim_kind:: analyst_assessment
      evidence:: E1, E2, E6, E8
        - Need: test whether intent can be recognized from the stream; choice: keep user queries in the audio track; alternative: external text prompts; tradeoff: more realistic but more sensitive to speech recognition and audio conditions.
          需求：测试模型能否从数据流中识别出用户意图；做法：把用户的提问保留在音频轨道中；备选方案：使用外部文本提示；权衡：更真实，但对语音识别和音频条件更敏感。
          evidence:: E1, E2, E15
        - Need: score continuous streams without fixed turns; choice: annotate each response slot with trigger, valid-answer moment, window close, and target answer; alternative: answer-only accuracy; tradeoff: more annotation burden but captures timing failures.
          需求：在没有固定轮次的连续流上进行打分；做法：为每个响应槽位（response slot）标注触发时刻、有效答案时刻、窗口关闭时刻以及目标答案；备选方案：只看答案是否正确的准确率；权衡：标注负担更重，但能捕捉到时序上的失误。
          evidence:: E6, E7
        - Need: distinguish silence, useful partial answers, spillover, and failed resumption; choice: add IDS and NCCS beside IA-QTF1; alternative: one global F1; tradeoff: clearer diagnosis but more judge and timestamp dependence.
          需求：区分沉默、有用的部分答案、溢出（spillover）以及恢复失败；做法：在 IA-QTF1 之外再加入 IDS 和 NCCS；备选方案：只用一个全局 F1 分数；权衡：诊断更清晰，但更依赖评判器和时间戳。
          evidence:: E8, E11, E13
    - **Implementation Surface:** The implementation surface implied by the paper includes replaying audio and frames through each model's native real-time interface, capturing timestamped output chunks, running slot alignment, and using external judge prompts for semantic scoring. The paper promises public code and datasets, but the provided text does not establish released artifact state, hardware budgets, or run-script completeness.
      **实现边界:** 论文所隐含的实现工作包括：通过每个模型自带的实时接口回放音频和画面帧、捕获带时间戳的输出片段、运行槽位对齐（slot alignment），以及使用外部评判器提示进行语义打分。论文承诺会公开代码和数据集，但所提供的正文并未说明已发布产物的具体状态、硬件预算，也未说明运行脚本是否完整。
      claim_kind:: analyst_assessment
      evidence:: E1, E9, E16
- ## Evaluation and Evidence
    - **Setup:** The experiments test AURA, Gemini 2.5 Flash Live, MiniCPM-o 4.5, and Qwen3.5-Omni Flash Realtime under chronological replay through their native real-time pipelines. GPT-4o is used as an external semantic judge for open-ended answers, while timing and slot alignment are computed from replay timestamps.
      **实验设置:** 实验对 AURA、Gemini 2.5 Flash Live、MiniCPM-o 4.5 和 Qwen3.5-Omni Flash Realtime 进行了测试，方式是通过它们各自原生的实时管线（pipeline）按时间顺序回放。GPT-4o 被用作外部语义评判器来评判开放式答案，而时序和槽位对齐则根据回放的时间戳来计算。
      evidence:: E9, E16
    - **Claim-Evidence Matrix:** The evidence most directly supports the benchmark-definition claims, moderately supports model-performance claims, and weakly supports broad generalization beyond the tested models, domains, and languages.
      **主张-证据矩阵:** 证据最直接地支持了关于基准测试定义的论断，中等程度地支持了关于模型性能的论断，而对于超出所测模型、领域和语言范围的更宽泛的推广性，支持则较弱。
      claim_kind:: analyst_assessment
      evidence:: E2, E3, E10, E15
        - C1 is supported by the benchmark comparison and dataset composition: OmniInteract adds spoken audio queries, native online inference, 1QnA monitoring, nested slots, and interruption cases relative to prior categories.
          论断 C1 由基准测试对比和数据集构成所支持：相较于以往的类别，OmniInteract 新增了口语音频提问、原生的在线推理、1QnA 持续监控、嵌套槽位以及打断（interruption）场景。
          evidence:: E2, E3
        - C2 is supported by formal slot definitions and metric definitions for soft true positives, false positives, no-output rate, partial answer quality, conditional spill, and nested chain completion.
          论断 C2 由形式化的槽位定义以及一系列指标定义所支持，这些指标涵盖软真阳性（soft true positive）、假阳性（false positive）、无输出率、部分答案质量、条件溢出（conditional spill）和嵌套链完成度。
          evidence:: E6, E7, E8
        - C3 and C4 are supported by reported model tables, but the support is bounded because the paper reports point estimates rather than statistical uncertainty, and the offline-online degradation analysis is limited to MiniCPM-o 4.5 mathematical reasoning.
          C3 和 C4 有论文中给出的模型结果表作为支撑，但支撑力度有限：论文只报告了点估计（单一数值），没有给出统计上的不确定性；而且离线到在线的性能退化分析只覆盖了 MiniCPM-o 4.5 的数学推理任务。
          claim_kind:: analyst_assessment
          evidence:: E10, E12, E14, E15
    - **Headline Results:** The headline result is not a single winning model but a pattern: models that do reasonably on explicit real-time queries still fail on monitoring, resumption, interruption control, or online reasoning. MiniCPM-o has the best All Global IA-QTF1 at 0.368, while AURA has the best 1QnA IA-QTF1 at only 0.052.
      **关键结果:** 最主要的结论不是某个模型胜出，而是一种普遍规律：那些在显式实时问答上表现尚可的模型，仍然会在监控、任务恢复、打断控制或在线推理上失败。MiniCPM-o 的全局 IA-QTF1（Interaction-Aware Quality-Timeliness F1，兼顾质量与时效的交互感知 F1 分数）最高，为 0.368；而 AURA 的 1QnA IA-QTF1 最高，却只有 0.052。
      evidence:: E10, E12, E13, E14
        - Supported claim: explicit questions are easier than proactive monitoring for some models; configuration: 1Q1A categories; baseline: other tested models; metric: IA-QTF1; direction: Gemini leads real-time at 0.553, MiniCPM-o leads proactive at 0.607; caveat: no uncertainty reported.
          支撑的结论：对某些模型来说，回答显式提问比主动监控更容易。实验配置：1Q1A（单次响应交互，即一次触发对应一个预期答案）类别。对照对象：其他被测模型。评估指标：IA-QTF1。结果方向：Gemini 在实时任务上领先，得分 0.553；MiniCPM-o 在主动任务上领先，得分 0.607。需注意：论文未报告不确定性。
          evidence:: E10
        - Supported claim: local inner-query answering does not guarantee outer-task resumption; configuration: 120 nested pairs; baseline: other tested models; metric: NCCS and missed outer count; direction: Gemini and Qwen3.5-Omni miss 119 and 116 outer resumptions; caveat: benchmark-specific pair design.
          支撑的结论：能回答局部的内层提问，并不保证能恢复外层任务。实验配置：120 组嵌套问答对。对照对象：其他被测模型。评估指标：NCCS（Nested Chain Completion Score，嵌套链完成度分数）以及漏掉的外层任务数量。结果方向：Gemini 和 Qwen3.5-Omni 分别漏掉了 119 次和 116 次外层任务恢复。需注意：这一设计是针对该基准专门构造的问答对。
          evidence:: E11
        - Supported claim: interruption behavior has a quality-control tradeoff; configuration: interrupted slots and MiniCPM-o math comparison; metrics: NOR, PAQ, CSM, pure quality score; direction: MiniCPM-o gives better partial answers but spills more, and online reasoning drops by 0.3358; caveat: one full-duplex model in the degradation test.
          支撑的结论：打断行为存在质量与控制之间的取舍。实验配置：被打断的交互槽位（interaction slot），以及 MiniCPM-o 的数学任务对比。评估指标：NOR、PAQ、CSM，以及纯质量分数。结果方向：MiniCPM-o 给出的部分回答质量更好，但溢出（spillover，即输出越过槽位边界并干扰后续交互）更多；在线推理性能下降了 0.3358。需注意：性能退化测试中只用了一个全双工模型。
          evidence:: E13, E14
    - **Ablations and Sensitivity:** Not applicable: no controlled ablation or statistical sensitivity study is reported; the paper instead provides diagnostic breakdowns by interaction type, interruption behavior, nested resumption, and offline-online setting.
      **消融与敏感性:** 不适用：论文没有报告受控消融实验或统计上的敏感性分析；作者转而按交互类型、打断行为、嵌套任务恢复和离线/在线设置，给出了诊断性的分项拆解。
      claim_kind:: analyst_assessment
    - **Reproducibility Gaps:** The paper gives useful reuse hooks, including data-license notes and judge prompt templates, and says code and datasets will be public. Missing trust fields in the provided text include confirmed released repository state, exact hardware/resource budgets, repeat counts, confidence intervals, and end-to-end scripts for all native model interfaces.
      **可复现性缺口:** 论文提供了一些便于复用的抓手，包括数据许可说明和评判用的提示词模板，并表示代码和数据集将会公开。但在所提供的文本中，缺少一些用于建立信任的关键信息：已确认发布的代码仓库状态、确切的硬件/资源预算、实验重复次数、置信区间，以及覆盖所有原生模型接口的端到端脚本。
      claim_kind:: analyst_assessment
      evidence:: E1, E15, E16
- ## Technical Judgment
    - **What Holds Up:** The benchmark's main technical contribution holds up because it evaluates the whole live loop rather than only answer correctness: spoken-query recognition, temporal grounding, answer content, spillover, interruptions, and resumption are all represented in the scoring design. The case is strongest for defining a benchmark gap and weakest for ranking model families definitively.
      **站得住的结论:** 该基准最主要的技术贡献是站得住脚的，因为它评估的是完整的实时交互闭环，而不只是答案是否正确：口头提问的识别、时间上的定位（temporal grounding）、答案内容、溢出、打断和任务恢复，都被纳入了评分设计。它在「定义一个此前缺失的基准任务」这一点上最有说服力，而在「明确给模型家族排名」这一点上最薄弱。
      claim_kind:: analyst_assessment
      evidence:: E2, E6, E7, E8, E9
    - **Where It May Fail:** Generality may fail when moving beyond the covered languages, domains, speech styles, and model set, especially because 1QnA uses synthesized initial instructions and the full-duplex degradation study is limited to one open-source model on mathematical reasoning. The judge-based scoring also makes semantic evaluation depend on prompt stability and external model behavior.
      **可能失效之处:** 一旦超出论文所覆盖的语言、领域、说话风格和模型集合，其通用性可能就会失效，尤其是因为 1QnA 使用的是合成的初始指令，而全双工性能退化研究只覆盖了一个开源模型的数学推理任务。此外，基于评判模型的打分方式，也让语义评估依赖于提示词的稳定性和外部模型的行为。
      claim_kind:: analyst_assessment
      evidence:: E15, E16
    - **Relation to Other Work:** Relative to offline and text-prompted streaming video benchmarks, OmniInteract shifts the evaluation axis from understanding a video to managing a spoken, audio-visual interaction over time. Relative to full-duplex voice benchmarks, it adds visual grounding and temporally annotated response opportunities rather than focusing only on speech turn-taking.
      **与已有工作的关系:** 相比离线的、以文本提示为输入的流式视频基准，OmniInteract 把评估的重心从「理解一段视频」转向了「随时间管理一场口头的、视听交互的对话」。相比全双工语音基准，它增加了视觉定位和带时间标注的响应机会，而不只是聚焦于语音的轮次切换。
      claim_kind:: analyst_assessment
      evidence:: E2, E8
    - **Transferable Lesson:** For streaming-agent evaluation, expose the hidden control problem by annotating when an answer becomes valid and when it becomes disruptive. A benchmark that scores only final answer text can miss the failures that make a live assistant unusable.
      **可迁移启发:** 针对流式智能体（streaming-agent）的评测，应当通过标注「答案何时开始有效」以及「答案何时变得具有干扰性」，把隐藏的控制问题暴露出来。如果一个基准（benchmark）只对最终答案文本打分，就可能漏掉那些让实时助手无法使用的失败情形。
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E8
- ## Glossary
  collapsed:: true
    - omnimodal large language model: A model family that handles multiple interaction channels, especially vision, audio, speech, and text, in one system.
      全模态大语言模型（omnimodal large language model）：这类模型能在一个系统里处理多种交互通道，尤其是视觉、音频、语音和文本。
    - online streaming inference: Running the model as the audio-visual stream unfolds, so it can use past and current inputs but not future content.
      在线流式推理（online streaming inference）：在音视频流不断展开的过程中运行模型，因此模型可以利用过去和当前的输入，但无法使用未来的内容。
    - interaction slot: A temporally grounded response opportunity with an observation start, earliest valid answer time, window close, and target answer.
      交互槽（interaction slot）：一个有时间定位的应答机会，包含观察起点、最早可给出有效答案的时间、窗口关闭时间以及目标答案。
    - 1Q1A: A setting where one trigger corresponds to one expected answer; OmniInteract includes real-time, proactive, and nested variants.
      1Q1A：一种设定，其中一个触发对应一个预期答案；OmniInteract 包含实时、主动和嵌套三种变体。
    - 1QnA: A setting where one spoken instruction can require multiple timed responses as a task unfolds.
      1QnA：一种设定，其中一条口头指令随着任务的展开可能需要多次按时给出的应答。
    - full-duplex real-time interaction: Interaction where the model processes incoming input while generating output, so listening and speaking overlap.
      全双工实时交互（full-duplex real-time interaction）：模型在生成输出的同时处理传入的输入，因此聆听和说话是重叠进行的。
    - Interaction-Aware Quality-Timeliness F1: The paper's global score combining soft true positives for quality and timeliness with penalties for missing or disruptive outputs.
      交互感知质量-时效性 F1（Interaction-Aware Quality-Timeliness F1）：本文提出的全局评分，它把质量与时效性上的软真正例（soft true positive）结合起来，并对遗漏或具有干扰性的输出施加惩罚。
    - Interruption Diagnostic Suite: A diagnostic set separating no output, useful partial answer quality, and conditional spillover during interrupted slots.
      打断诊断套件（Interruption Diagnostic Suite）：一组诊断指标，用于在被打断的交互槽期间区分「无输出」「有用的部分答案质量」以及「条件性溢出」三种情况。
    - Nested Chain Completion Score: A geometric-mean score for nested interactions that requires both the inserted inner answer and resumed outer answer to be correct.
      嵌套链完成得分（Nested Chain Completion Score）：一种用于嵌套交互的几何平均得分，要求插入的内层答案和恢复后的外层答案都正确。
    - spillover: Model output that continues beyond a slot boundary and can disrupt the next interaction context.
      spillover（溢出）：模型输出在超出某个时段（slot）边界后仍继续生成，可能干扰下一次交互的上下文。
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/paper_statement | Abstract | high
      locator:: Abstract
      quote:: We introduce OmniInteract, a streaming benchmark for real-time omnimodal large language models evaluated through native online inference over audio-visual streams. Unlike offline video understanding or text-prompted streaming QA, OmniInteract preserves the original audio-visual stream and requires models to process it online, without access to future content.
    - **E2:** gap/paper_statement | Introduction | high
      locator:: Section 1 and Table 1
      quote:: Existing benchmarks are evaluated on pre-segmented video clips with offline inference, or rely on custom streaming protocols distinct from the models' native real-time inference. As a result, they only partially evaluate the interaction loop required by native real-time assistants.
    - **E3:** experiment_setup/paper_statement | OmniInteract Benchmark | high
      locator:: Section 3.1 and Table 2
      quote:: The 1Q1A split contains 1,062 response slots across real-time, proactive, and nested interactions, while 1QnA contains 368 response slots. The 147 interruptions in 1Q1A and 45 interruptions in 1QnA are annotated as cross-cutting cases within these splits.
    - **E4:** experiment_setup/paper_statement | Data Curation | high
      locator:: Section 3.2
      quote:: We self-record 210 videos in two groups of scenarios. The first group covers daily-life interactions in Chinese, including home activities, gym exercises, museums, shopping, and other common situated interactions (150 videos). The second group covers English mathematical problem-solving.
    - **E5:** experiment_setup/paper_statement | Data Curation | high
      locator:: Section 3.2
      quote:: For the 1QnA split, we construct continuous monitoring instances from existing procedural and task-oriented video benchmarks (40 videos), including live step-by-step task guidance and egocentric error detection.
    - **E6:** method/paper_statement | Slot Construction and Chunk Matching | high
      locator:: Section 3.3.1
      quote:: Continuous streams do not provide explicit turn boundaries, so we discretize evaluation into interaction slots: slot=[t_start,t_a,t_end), where t_start is the onset of observation, t_a is the earliest moment for a valid core response, and t_end is the window's close.
    - **E7:** method/paper_statement | Interaction-Aware Scoring | high
      locator:: Section 3.3.2
      quote:: A false positive (FP) aggregates four unwarranted behaviors: 1) unmatched chunks, 2) early hallucinations, 3) low-quality responses, and 4) spill, where output exceeds the boundary t_end to disrupt conversational continuity.
    - **E8:** method/paper_statement | Extended Metrics | high
      locator:: Section 3.3.3
      quote:: IDS addresses this gap with three complementary diagnostics: No-Output Rate (NOR), the proportion of interrupted slots with no model output for the preempted query; Partial Answer Quality (PAQ), an LLM-judged usefulness score for already-spoken content without incompleteness penalties; and Conditional Spill Metrics (CSM).
    - **E9:** experiment_setup/paper_statement | Experiments | high
      locator:: Section 4 and 4.1
      quote:: During inference, each recording is replayed chronologically to the model through its native real-time interface, so that frames and audio are exposed only according to their original timestamps. The model can therefore condition on past and current inputs, but cannot access future video frames, future audio, or ground-truth slot boundaries.
    - **E10:** result/experiment_result | 1Q1A Interaction | medium
      locator:: Section 4.2 and Table 3
      quote:: For explicit real-time queries, Gemini obtains the best score (0.553), followed by Qwen3.5-Omni (0.524). In contrast, proactive interaction favors MiniCPM-o (0.607) and AURA (0.549).
    - **E11:** result/experiment_result | 1Q1A Interaction | medium
      locator:: Section 4.2 and Table 4
      quote:: MiniCPM-o achieves the best NCCS of 0.284, followed by AURA at 0.270. Although Gemini and Qwen3.5-Omni answer many inner queries correctly, they fail to resume the outer query in 119 and 116 of 120 cases, respectively.
    - **E12:** result/experiment_result | 1QnA Interaction | medium
      locator:: Section 4.3 and Table 3
      quote:: All models perform substantially worse on 1QnA than on 1Q1A. AURA obtains the highest IA-QTF1 score of 0.052, but the absolute score remains low.
    - **E13:** result/experiment_result | More Interruption Analyses | medium
      locator:: Section 4.4 and Table 5
      quote:: MiniCPM-o shows the opposite pattern: it responds more often, with a lower NOR of 53.65% and the best PAQ of 0.571, but spills severely when it responds, with CSM of 83.15% and 10.067 s.
    - **E14:** result/experiment_result | Full-duplex Capability Degradation | medium
      locator:: Section 4.5 and Table 6
      quote:: MiniCPM-o drops from 0.6833 offline to 0.3475 online, an absolute decrease of 0.3358. This suggests that continuous listening, visual processing, and concurrent response generation can substantially degrade reasoning quality.
    - **E15:** limitation/limitation | Limitations | high
      locator:: Limitations
      quote:: First, we evaluate four representative models, but the landscape of omnimodal systems is evolving rapidly. Second, the online capability degradation analysis is limited to MiniCPMo on mathematical reasoning tasks. Third, the 1QnA split uses TTS-synthesized speech for initial instructions.
    - **E16:** experiment_setup/implementation_detail | LLM Judge Evaluation Protocol | medium
      locator:: Appendix A.4
      quote:: All open-ended answer assessments use GPT-4o as an external judge to avoid evaluator bias from the tested models. Core-stage assessment receives: (1) the ground-truth target answer, (2) the concatenated model-generated chunks within the core segment, and (3) a structured instruction.
