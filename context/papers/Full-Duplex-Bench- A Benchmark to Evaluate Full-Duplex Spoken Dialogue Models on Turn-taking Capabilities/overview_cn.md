- **标题:** Full-Duplex-Bench：一个用于评估全双工口语对话模型轮流发言能力的基准测试
- **一句话总结:** Full-Duplex-Bench 把口语对话模型中的实时轮流发言行为变成了一个可自动运行的基准测试，结果表明各模型在等待、及时接过话头、附和时机以及打断后的连贯性这几方面各有取舍。
- **论文类型:** 基准测试
- **发表:** arXiv/预印本 2025
- **作者:** Guan-Ting Lin（台湾大学）、Jiachen Lian（加州大学伯克利分校）、Tingle Li（加州大学伯克利分校）、Qirui Wang（华盛顿大学）、Gopala Anumanchipalli（加州大学伯克利分校）、Alexander H. Liu（MIT CSAIL）、Hung-yi Lee（台湾大学）
- **关键词:** 全双工口语对话、轮流发言、附和、语音基准测试、口语对话模型、打断处理
- ## Orientation
    - **背景:** 背景：口语对话模型（Spoken Dialogue Model，SDM）是能理解语音并以语音作出回应的语音系统。全双工（Full-duplex）指系统可以一边听一边说，而不是等对方说完一整轮再回应。
      claim_kind:: analyst_assessment
    - **通俗问题:** 用大白话说清问题：语音智能体必须判断什么时候保持沉默，什么时候给出一个简短的回应，什么时候正式回答，以及在用户插话时该怎么办。
      claim_kind:: analyst_assessment
    - **为何困难:** 为什么难：同样一段短暂的沉默，可能表示犹豫，可能是一句话的自然停顿，也可能是邀请对方说话，模型必须根据时间节奏和音频上下文来判断到底是哪一种。
      claim_kind:: analyst_assessment
    - **一句话核心思路:** 一句话讲清核心思路：用受控的对话场景来测试模型，并对可观察到的音频行为进行评分，而不是只看回答内容好不好。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **阅读价值:** 把这篇论文当作面向全双工口语对话模型的语音交互基准测试来读，这里的全双工指的是能一边说话一边聆听的语音系统；它填补了一个缺失的评估层面，也就是介于任务准确率与那些让对话显得自然的时机行为之间的部分。
      claim_kind:: analyst_assessment
      evidence:: E1, E2
    - **一句话贡献:** Full-Duplex-Bench 把倾听时机、说话权交接以及打断后的恢复,变成可自动评分的音频流测试,从而改进了对实时口语对话的评估。
      evidence:: E1, E4
    - **记忆模型:** 可以把它想象成为语音智能体设计的一场路考：这个基准测试制造出一些尴尬但真实的情境，记录智能体是插话、等待、简短地应和一声，还是改变思路，然后根据音频轨迹给它的时机把握打分。
      claim_kind:: analyst_assessment
    - **最佳证据:** 最有力的证据是：使用相同的流式输入和自动化的时机度量指标，在四个交互维度上对四个系统做了统一比较。
      evidence:: E9, E10, E11, E12, E13
        - 支持 C3：表 III 中的 Gemini Live；最接近的开源基线是 Freeze-Omni；停顿接管率（Takeover Rate）更低，回应信号的 Jensen-Shannon 散度（JSD）也更低；合成停顿场景的接管率为 0.255，对比之下为 0.642，回应信号的 JSD 为 0.896，对比之下为 0.997；由于没有报告方差，因此支持度为中等。
          evidence:: E11
        - 支持 C3：Candor 数据集展现出流畅的话轮转换（turn-taking）；把 dGSLM 和 Moshi 与 Freeze-Omni、Gemini Live 作对比；指标为响应延迟和接管率（Takeover Rate）；Moshi 最快，为 0.265 秒，而 Freeze-Omni 和 Gemini 的接管率更低；由于速度和正确性之间存在取舍，因此支持度为中等。
          evidence:: E12
        - 支持 C3：合成打断任务；把 Freeze-Omni 与 Gemini Live、Moshi、dGSLM 作对比；指标为 GPT-4o 给出的响应质量评分和延迟；Freeze-Omni 得分 3.615，Gemini 得分 3.376，但 Freeze-Omni 延迟更高；由于评判模型和重复实验的统计量未经审核，因此支持度为中等。
          evidence:: E13
    - **主要边界:** 主要保留意见：该基准是诊断性的，而不是按用户偏好校准的，也就是说，它能指出模型在何时的打断、延迟或回应信号方式有所不同，但无法判断这种行为对某个用户、某种语言或某类应用是否最优。
      claim_kind:: analyst_assessment
      evidence:: E13, E14
- ## Argument Map
    - **问题与重要性:** 问题与意义：全双工口语对话模型有望带来更自然的交互，但现有评测大多衡量的是回答内容、指令遵循或语料库的整体统计特征，而不是系统是否尊重真实对话中的实时时间节奏。
      evidence:: E1, E2
    - **已有方法缺口:** 先前研究的空白：这一空白在方法层面上体现出来。dGSLM 那类基于语料库的统计量难以解读，Talking-Turns 依赖一个训练出来的评判模型和用户研究，而许多语音基准都假定半双工交互，也就是同一时刻只有一方在说话。
      evidence:: E2
    - **关键洞见:** 论文的核心洞见是：轮流发言（turn-taking，即决定谁下一个说话、说话人何时把话语权让出或保留的时机问题）可以拆解成一系列与具体场景相关、可观测的事件；随后基于时间对齐后的模型输出，用描述性指标来打分，而不是用单一的整体对话质量分。
      evidence:: E1, E4, E5, E6, E7, E8
    - **核心主张:** 论文的逻辑主张是以下四条可证伪的陈述。
      claim_kind:: analyst_assessment
        - C1：一个由场景驱动的基准测试能够覆盖区分全双工（full-duplex，即听和说可以同时进行、不同于半双工那种一问一答的交互）语音对话模型（Spoken Dialogue Model，SDM）的主要实时行为，包括停顿处理、附和回应（backchannel，即听者发出的简短反馈，例如「嗯」这类表示在听、但不抢过话语权的信号）、平滑的轮流发言，以及对用户打断的管理。
          evidence:: E1, E4
        - C2：这些行为可以借助针对同步的用户音频与模型音频计算的自动指标来量化，包括接管率（Takeover Rate）、附和回应频率、Jensen-Shannon 散度（Jensen-Shannon Divergence，JSD），响应延迟，以及用 GPT-4o 对打断处理进行打分。
          evidence:: E3, E4, E5, E6, E7, E8
        - C3：把该基准测试应用到 dGSLM、Moshi、Freeze-Omni 和 Gemini Live 上，揭示出的是各有取舍的差异，而不是某一个模型在所有轮流发言行为上都最好。
          evidence:: E10, E11, E12, E13
        - C4：该基准测试是一个可复现的诊断工具，但它的分数目前还没有建立在人类偏好之上，也没有验证跨语言的通用性。
          evidence:: E14, E15
- ## Mechanism and Design
    - **核心机制:** Full-Duplex-Bench 给每个模型输入相同的用户音频流，记录模型与之时间同步的语音输出，用自动语音识别（Automatic Speech Recognition，ASR，即把语音转成带时间标记文本的软件）把输出转换成词级别的时间戳，再计算针对具体任务的行为指标。
      evidence:: E4
        - 接管率（Takeover Rate，TOR）把「模型是否抢占了对话话语权」这个问题转化为一个二值信号，并在所有样本上取平均。
          evidence:: E3
        - Jensen-Shannon 散度（Jensen-Shannon Divergence，JSD，一种取值有界的、衡量两个概率分布之间距离的度量）用来比较模型附和回应的时机与人类附和回应的时机。
          evidence:: E6
        - 打断处理被拆分为三个方面：模型是否作出回应、回应的质量如何，以及在用户打断之后模型需要多久才作出回应。
          evidence:: E8
    - **数据/控制流:** 整个流程依次是：选取样本、构造用户音频、模型流式输出、对齐输出、行为分类、指标汇总；这样就把模型推理和评分规则分离开来。
      evidence:: E4, E9
        - 对于停顿和平滑轮换这两类情况，Candor 提供了自然的双声道对话，并用语音活动检测（Voice Activity Detection，VAD，一种标记何时有语音出现的软件）加人工复核来筛选候选片段。
          evidence:: E9
        - 对话语料库（In Conversation Corpus，ICC）在较小的时间窗口内提供了人类反馈语（backchannel）的时机数据，从而为该基准提供了一个可用于 Jensen-Shannon 散度（Jensen-Shannon Divergence，JSD）比较的人类时机分布。
          evidence:: E9
        - 对于合成的打断和停顿情况，采用 GPT-4o 文本生成加文本转语音（Text-to-Speech，TTS，一种把文本转成语音音频的软件）来制造受控事件，因为这类事件在公开对话数据中很稀缺。
          evidence:: E9
    - **设计决策:** 该基准选择了简单的描述性指标，使每个分数都对应一种可观察到的行为；这样做放弃了直接得出人类偏好判定的能力，换来了可复现性和诊断上的清晰度。
      claim_kind:: analyst_assessment
      evidence:: E5, E6, E7, E8, E14
        - 需求：避免把完整回答当成确认性的反馈语；设计选择：以时长短、词数极少来定义反馈语；权衡取舍：不符合这一形态、更丰富的听者信号会被排除在外。
          evidence:: E3
        - 需求：让时机错误可被诊断；设计选择：对停顿、反馈语、话权交接和打断分别使用不同的指标；备选方案：使用一个学习得到的全局评判器，但论文认为这种方案的可复现性更差。
          claim_kind:: analyst_assessment
          evidence:: E2, E5, E6, E7, E8
        - 需求：评估罕见的打断情况；设计选择：生成受控的合成对话；权衡取舍：这些事件的分布可能与真实用户的插话不同。
          claim_kind:: analyst_assessment
          evidence:: E9
    - **实现边界:** 该实现接口刻意设计得对外部模型友好：每个受测系统只需消费流式的用户音频，并输出可以对齐回原始时间线的音频即可。
      evidence:: E4, E10, E15
        - dGSLM、Moshi 和 Freeze-Omni 通过已发布的实现或服务器进行评估，而 Gemini Live 则通过厂商的实时服务、以 16 kHz 音频流的方式进行评估。
          evidence:: E10
        - 作者称已公开发布该基准测试与代码，这一点很重要，因为许多候选的全双工（Full-duplex）系统并未公开完整的语音到语音处理流程。
          evidence:: E15
- ## Evaluation and Evidence
    - **实验设置:** 该基准测试在 Candor、ICC 和合成数据上评估了 dGSLM、Moshi、Freeze-Omni 和 Gemini Live。评估中，停顿场景使用越低越好的接管率（Takeover Rate，TOR），反馈语（Backchannel）时机使用越低越好的 JSD，话轮交接使用越低越好的延迟，打断响应质量则使用越高越好的 GPT-4o 评分。
      evidence:: E5, E6, E7, E8, E9, E10
        - 报告的样本数量为：Candor 停顿样本 216 个、Candor 平滑话轮样本 119 个、ICC 反馈语样本 55 个、合成打断样本 200 个、合成停顿样本 137 个。
          evidence:: E9
        - 基线的公平性只是部分成立：各系统使用了相同的基准测试输入和相同的指标，但模型的访问方式并不一致，本地的开源处理流程与 Gemini Live 服务之间存在差异。
          claim_kind:: analyst_assessment
          evidence:: E10
        - 论文没有报告统计不确定性：表格只给出了汇总分数，没有方差、置信区间或重复次数分析。
          claim_kind:: analyst_assessment
          evidence:: E11, E12, E13
    - **主张-证据矩阵:** C1 和 C2 主要由基准测试的设计来支撑；C3 由模型对比表来支撑；C4 则由作者自己的局限性陈述和发布讨论来支撑。
      claim_kind:: analyst_assessment
      evidence:: E1, E4, E11, E12, E13, E14, E15
        - C1—C2：论文直接描述了场景覆盖范围和自动化指标，但并未证明这四个维度就穷尽了全双工对话质量的全部内容。
          claim_kind:: analyst_assessment
          evidence:: E1, E4, E5, E6, E7, E8
        - C3：表 III 支持了「存在权衡取舍」的观点，因为最佳模型会随维度不同、以及随指标方向（越高越好还是越低越好）不同而变化。
          claim_kind:: analyst_assessment
          evidence:: E11, E12, E13
        - C4：发布代码和采用自动化指标有助于可复现性，但用户偏好和语言边界问题被明确地留作未决。
          claim_kind:: analyst_assessment
          evidence:: E14, E15
    - **关键结果:** 核心结论并不是某个模型在排行榜上胜出，而是勾勒出一幅行为画像：端到端语音模型（E2E）可以做到反应迅速，显式的控制有助于打断时的连贯性，而在报告的这些指标上，商业服务更少出现过早接管话语权的情况。
      claim_kind:: analyst_assessment
      evidence:: E11, E12, E13
        - 支持的论断：C3；配置：表 III 的停顿任务与回话反馈（backchannel）任务；最接近的基线：Freeze-Omni 对应 Gemini Live；指标与方向：更低的接管率（TOR）/JSD 更好；差值：合成停顿场景下 TOR 为 0.255，对比基线 0.642；回话反馈场景下 JSD 为 0.896，对比基线 0.997；不确定度：未报告；注意事项：闭源服务的细节无法获取。
          evidence:: E11
        - 支持的论断：C3；配置：Candor 数据集上的平滑轮流发言（smooth turn-taking）；基线：所有被评估的系统；指标与方向：更高的接管率（TOR）但更低的延迟；差值：Moshi 的 TOR 为 0.941，延迟为 0.265 秒，而 Gemini 的 TOR 为 0.655，延迟为 1.301 秒；不确定度：未报告；注意事项：响应的及时性与接过话语权的意愿之间存在冲突。
          evidence:: E12
        - 支持的论断：C3；配置：合成打断场景；基线：Gemini Live 与端到端系统；指标与方向：更高的 GPT-4o 质量评分与更低的延迟；差值：Freeze-Omni 在 1.409 秒处得分 3.615，而 Gemini 在 1.183 秒处得分 3.376；不确定度：未报告；注意事项：由 GPT-4o 来评判并不等同于人类偏好研究。
          evidence:: E13
    - **消融与敏感性:** 不适用：该论文报告了跨模型和跨数据集的比较，但没有做移除基准组件或改变指标定义的消融实验。
      claim_kind:: analyst_assessment
    - **可复现性缺口:** 基准测试和代码已经开源，但要精确复现仍然依赖外部的模型发布、闭源服务的行为、自动语音识别（ASR）流水线、用于评判打断质量的 GPT-4o，以及缺失的方差或重复次数报告。
      claim_kind:: analyst_assessment
      evidence:: E8, E10, E11, E12, E13, E15
        - 许多参与比较的全双工（full-duplex）系统没有完整公开语音到语音的模型发布，也没有披露内部细节，因此这套基准测试比被评估的模型集合更具可复用性。
          claim_kind:: analyst_assessment
          evidence:: E15
        - 打断质量指标使用 GPT-4o 作为评判者，因此它的校准情况、对提示词的敏感度，以及与人类判断的一致性都没有被报告。
          claim_kind:: analyst_assessment
          evidence:: E8, E14
- ## Technical Judgment
    - **站得住的结论:** 这套基准测试最有力的部分，是它把杂乱的对话拆解成可核查的信号：谁在说话、什么时候说、这段话是否只是一个简短的听者提示，以及模型反应有多快。
      claim_kind:: analyst_assessment
      evidence:: E3, E4, E5, E6, E7, E8
        - 同一套框架在 dGSLM、Moshi、Freeze-Omni 和 Gemini Live 上暴露出不同的失败模式，这比一个单一的对话综合评分更有用。
          claim_kind:: analyst_assessment
          evidence:: E11, E12, E13
    - **可能失效之处:** 当任务要求微妙的社交偏好判断、而不是可观测的时序时，它可能会失效：较低的接管率（TOR）既可能意味着有耐心，也可能意味着错过了应答的时机；而较高的回话反馈频率，视具体情境而定，既可能有帮助，也可能令人厌烦。
      claim_kind:: analyst_assessment
      evidence:: E3, E6, E12, E14
        - 反馈信号（backchannel，指听者用来表示自己在关注的简短回应）检测器所用的时长与词数规则容易复现，但可能漏掉较长的应答、非语言的暗示，或某种语言特有的听者信号。
          claim_kind:: analyst_assessment
          evidence:: E3, E14
        - 人工合成的打断样本和停顿样本使受控测试成为可能，但它们可能无法充分代表真实用户那种杂乱的插话、说话时的自我纠正，以及多语言场景下的行为。
          claim_kind:: analyst_assessment
          evidence:: E9, E14
    - **与已有工作的关系:** 与考察内容或指令遵循能力的语音基准相比，本文评估的是交互中的时序把握；与 dGSLM 使用的语音活动统计量、或 Talking-Turns 采用的训练式评判器相比，本文更倾向于使用明确设定的场景，以及更便于重复运行的自动化指标。
      claim_kind:: analyst_assessment
      evidence:: E2, E5, E6, E7, E8
        - 被评估的各类模型在技术上有重要差别：端到端系统直接对音频流建模，而级联系统则组合了多个组件，例如自动语音识别（ASR）、文本生成和文本转语音（TTS），这会改变延迟和控制行为。
          evidence:: E10, E12, E13
    - **可迁移启发:** 对于交互式人工智能系统，应先对用户能直接感受到的各类微观行为分别做基准测试，再把它们汇总成一个整体分数；把描述性的诊断指标与偏好性的评判分开，这样开发者就能为自己的应用选择所需的行为特征组合。
      claim_kind:: analyst_assessment
      evidence:: E1, E5, E6, E7, E8, E14
- ## Glossary
  collapsed:: true
    - 口语对话模型（Spoken Dialogue Model，SDM）：一种以语音作为对话输入、并生成语音回应的系统；在本篇笔记中，SDM 指被评估的那一类模型。
    - 全双工（Full-duplex）：一种可以同时进行倾听和说话的通信方式，不同于半双工那种轮流交替的交互。
    - 话轮转换（Turn-taking）：一个关于时序的问题，即判断接下来该由谁说话，以及说话者何时让出发言权或继续保持发言权。
    - 反馈信号（Backchannel，BC）：听者发出的简短暗示，例如一句应答，用来表示自己在关注，但并不接管对话。
    - 接管率（Takeover Rate，TOR）：TOR 是对一个二值的接管信号取平均得到的；在停顿任务和反馈信号任务中，该值越低越好，而当模型应当在话轮结束或被打断后作出回应时，则希望该值越高越好。
    - Jensen-Shannon 散度（Jensen-Shannon Divergence，JSD）：一种衡量两个概率分布之间差异的有界指标；这里用它来比较模型产生反馈信号（backchannel，即听者的简短应答）的时机与人类产生反馈信号的时机。
    - 自动语音识别（Automatic Speech Recognition，ASR）：把语音音频转换成文本的软件，通常还会给出用于对齐的时间戳。
    - 语音活动检测（Voice Activity Detection，VAD）：用于标记音频流中何时出现语音的软件；常用于过滤和分段。
    - 文本转语音（Text-to-Speech，TTS）：从文本合成语音音频的软件；这里用它来生成合成的基准测试输入。
    - 对话语料库（In Conversation Corpus，ICC）：这里用于提供人类反馈信号（backchannel）时机分布的数据集。
    - 端到端语音模型（End-to-end speech model，E2E）：直接对语音流建模的模型，不主要依赖显式的文本处理流程。
    - 级联式语音系统（Cascaded speech system）：一种模块化的语音系统，把自动语音识别（ASR）、语言模型、文本转语音（TTS）等组件串联起来；这种模块化设计能提升可控性，但会增加延迟。
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/paper_statement | Abstract and Introduction | high
      locator:: Abstract; Introduction near contribution paragraph
      quote:: The paper introduces Full-Duplex-Bench for full-duplex spoken dialogue models and centers evaluation on pause handling, backchanneling, turn-taking, and interruption management with automatic metrics.
    - **E2:** gap/paper_statement | Introduction and Related Works | medium
      locator:: Introduction prior benchmark discussion; II.B Evaluation Benchmarks
      quote:: Prior speech benchmarks mainly cover content, instruction following, or paralinguistic perception under turn-based assumptions; dGSLM statistics and Talking-Turns expose reproducibility and generalization limits.
    - **E3:** method/paper_statement | Full-Duplex-Bench Framework | high
      locator:: III, key term definitions before III.A
      quote:: Backchanneling is operationalized as brief listener speech under one second and fewer than two words; takeover is non-silent non-backchannel speech, and TOR averages that binary variable.
    - **E4:** system_design/implementation_detail | Full-Duplex-Bench Framework | high
      locator:: III.A Overview; Figure 1
      quote:: The framework streams input.wav to each SDM, records output.wav, uses Nvidia parakeet-tdt-0.6b-v2 ASR for word-level timing, and applies dedicated metrics by dimension.
    - **E5:** method/paper_statement | Full-Duplex-Bench Framework | high
      locator:: III.B.1 Pause Handling
      quote:: Pause handling asks whether the model recognizes that the user still holds the floor; the metric is Takeover Rate, where lower values mean fewer premature interruptions.
    - **E6:** formula/paper_statement | Full-Duplex-Bench Framework | high
      locator:: III.B.2 Backchanneling
      quote:: Backchanneling is measured with TOR, backchannel events per second, and Jensen-Shannon Divergence between model and human timing distributions over aligned time windows.
    - **E7:** method/paper_statement | Full-Duplex-Bench Framework | high
      locator:: III.B.3 Smooth Turn Taking
      quote:: Smooth turn-taking measures average response latency from the end of user speech to the start of model speech, calculated only when takeover occurs.
    - **E8:** method/paper_statement | Full-Duplex-Bench Framework | medium
      locator:: III.B.4 User Interruption
      quote:: User interruption evaluation uses TOR, a GPT-4o score from 0 to 5 for coherence and relevance, and latency after interruption when the model takes the turn.
    - **E9:** experiment_setup/implementation_detail | Data Curation | high
      locator:: III.C; Table II
      quote:: The benchmark uses Candor for pause and smooth-turn data, ICC for backchannel timing, and synthetic GPT-4o plus ChatTTS data for interruptions and synthetic pauses.
    - **E10:** experiment_setup/implementation_detail | Models Under Evaluation | high
      locator:: IV Models Under Evaluation
      quote:: The evaluated systems are dGSLM, Moshi, Freeze-Omni, and Gemini Live, using official implementations or official service access where available.
    - **E11:** result/experiment_result | Results | medium
      locator:: V Results; Table III pause and backchannel columns
      quote:: Table III shows Gemini Live with the lowest pause TORs and best backchannel JSD; dGSLM has the highest open-source backchannel frequency, while Moshi often takes over.
    - **E12:** result/experiment_result | Results | medium
      locator:: V Results; Table III smooth turn-taking columns
      quote:: For Candor smooth turn-taking, dGSLM and Moshi have high TOR and low latency, while Freeze-Omni and Gemini Live have lower takeover rates and slower responses.
    - **E13:** result/experiment_result | Results | medium
      locator:: V Results; Table III user interruption columns
      quote:: On synthetic interruptions, Freeze-Omni gets the highest GPT-4o quality score, Gemini Live is close, and the end-to-end systems struggle with semantic coherence.
    - **E14:** limitation/limitation | Limitation and Future Work | high
      locator:: VII Limitation and Future Work
      quote:: The authors state that the framework does not yet connect measured behaviors to human preferences and that the present analysis is limited to English.
    - **E15:** implementation/paper_statement | Introduction and Related Works | medium
      locator:: Contribution footnote; Table I
      quote:: The paper reports a public data and code release, while Table I shows many full-duplex systems lack complete public speech-to-speech releases or architectural details.
