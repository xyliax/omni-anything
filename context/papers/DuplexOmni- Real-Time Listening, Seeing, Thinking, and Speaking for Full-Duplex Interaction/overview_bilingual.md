- **Title:** DuplexOmni: Real-Time Listening, Seeing, Thinking, and Speaking for Full-Duplex Interaction
  **标题:** DuplexOmni：面向全双工交互的实时听、看、思考与说话系统
- **Summary:** DuplexOmni frames real-time multimodal assistants as two cooperating processes: a low-latency interaction model keeps listening and speaking while a pluggable thinking layer performs slower reasoning or tool use in the background.
  **一句话总结:** DuplexOmni 把实时多模态助手看作两个协作运行的进程：一个低延迟的交互模型持续保持听和说，同时一个可插拔的思考层在后台执行更慢的推理或工具调用。
- **Paper Type:** system
  **论文类型:** 系统
- **Venue:** arXiv preprint 2026
  **发表:** arXiv 预印本 2026
- **Authors:** Muye Huang (Xi'an Jiaotong University / MOE KLNN Lab), Lingling Zhang (Xi'an Jiaotong University / MOE KLNN Lab), Xingyu Yu (MOE KLNN Lab), Lei Shi (Meituan), Zhanyu Ma (Meituan), Jun Xu (Meituan), Jiuchong Gao (Meituan), Jinghua Hao (Meituan), Renqing He (Meituan), Jun Liu (Xi'an Jiaotong University / MOE KLNN Lab)
  **作者:** Muye Huang（西安交通大学 / 教育部 KLNN 实验室），Lingling Zhang（西安交通大学 / 教育部 KLNN 实验室），Xingyu Yu（教育部 KLNN 实验室），Lei Shi（美团），Zhanyu Ma（美团），Jun Xu（美团），Jiuchong Gao（美团），Jinghua Hao（美团），Renqing He（美团），Jun Liu（西安交通大学 / 教育部 KLNN 实验室）
- **Keywords:** full-duplex interaction, omni model, streaming speech generation, multimodal dialogue, asynchronous reasoning, training data construction
  **关键词:** 全双工交互、omni 模型、流式语音生成、多模态对话、异步推理、训练数据构建
- ## Orientation
    - **Background:** This paper lives in voice and vision assistants that try to hear, see, reason, and answer in one system. The key setting is a conversation where both sides can listen and speak at the same time, rather than taking clean turns.
      **背景:** 本文属于语音与视觉助手领域，这类助手试图在同一个系统里完成听、看、推理和回答。关键的场景是这样一种对话：双方可以同时听和说，而不是干净利落地轮流发言。
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A helpful assistant should not go silent every time it needs to search, calculate, or look more carefully. It should keep the user engaged while new speech or visual information may still arrive.
      **通俗问题:** 一个好用的助手，不应该每次需要搜索、计算或更仔细地观察时就陷入沉默。在新的语音或视觉信息可能还在不断到来的同时，它应该持续与用户保持互动。
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** Speaking quickly, listening for interruptions, watching the scene, and doing slow reasoning compete for attention and time. If they are forced through one queue, slow work blocks live conversation.
      **为何困难:** 快速说话、监听打断、观察画面，以及进行慢速推理，这几件事会争抢注意力和时间。如果把它们都挤进同一条队列，慢速的工作就会阻塞实时对话。
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Let one part handle the live conversation and another part think in the background, then stream useful pieces back into later replies.
      **一句话核心思路:** 让一个部分负责实时对话，另一个部分在后台思考，然后把有用的片段流式地送回，融入后续的回复中。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a real-time multimodal-assistant systems paper: it targets the gap between models that can listen and speak at once (full-duplex interaction) and models that can do slower reasoning or tool use without freezing the conversation.
      **阅读价值:** 可以把它当作一篇实时多模态助手的系统论文来读：它针对的是这样一个空白——既能同时听和说的模型（也就是全双工交互，指助手在说话的同时仍能持续接收用户语音，因此重叠、打断、附和都是正常运作的一部分），与既能做更慢的推理或工具调用又不让对话卡住的模型，二者之间的鸿沟。
      claim_kind:: analyst_assessment
      evidence:: E2, E3
    - **One-Sentence Contribution:** DuplexOmni improves continuous audio-video dialogue by letting a fast interaction model keep the conversation alive while a separate background thinking process returns information later.
      **一句话贡献:** DuplexOmni 让一个快速的交互模型持续维持对话不中断，同时由一个独立的后台思考进程稍后返回信息，从而改进连续的音视频对话。
      evidence:: E1, E4
    - **Mental Model:** Picture a front-desk helper who keeps talking, listening, and watching the visitor while a specialist in the back room searches, calculates, or plans and passes notes forward.
      **记忆模型:** 可以想象一位前台接待员一直在说话、倾听并注视着来访者，而后台的一位专家则在检索、计算或规划，并把记录传递到前台。
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is the combination of realtime benchmark gains and ablations showing that interaction quality and reasoning strength come from different parts of the system.
      **最佳证据:** 最有力的证据是两方面的结合：一是在实时基准测试上的性能提升，二是消融实验表明交互质量与推理能力来自系统中不同的部分。
      evidence:: E11, E12
        - Supports C4: full DuplexOmni with Gemini-3.1-Flash-Lite thinking layer; realtime omni baselines; Full DuplexBench ToR; 72.6% versus 36.3% for MiniCPM-o 4.5 at similar latency; supported, but no variance or repeat count is reported.
          支持 C4：完整的 DuplexOmni，搭配 Gemini-3.1-Flash-Lite 思考层；对比对象为实时全模态基线模型；使用 Full DuplexBench ToR；在相近延迟下，成绩为 72.6% 对 MiniCPM-o 4.5 的 36.3%；该结论得到支持，但论文未报告方差或重复次数。
          evidence:: E10, E11
        - Supports C4: full system; ablations without the default thinking layer; Big Bench Audio; 77.2% versus 50.3% with weak thinking and 22.2% without thinking; supported, but statistical uncertainty is not reported.
          支持 C4：完整系统；对照实验去掉了默认的思考层；使用 Big Bench Audio；完整系统得分 77.2%，弱思考层为 50.3%，无思考层为 22.2%；该结论得到支持，但论文未报告统计不确定性。
          evidence:: E12
        - Supports C3: Writer-Director annotated corpus; no direct baseline; coverage of delayed reasoning, silence, assistant initiation, overlap, and reset patterns; broad coverage is supported, but human annotation quality is not independently audited.
          支持 C3：使用 Writer-Director 标注语料；没有直接对比的基线；覆盖了延迟推理、静默、助手主动发起、重叠以及重置等模式；广泛覆盖这一点得到支持，但人工标注质量未经独立审核。
          evidence:: E8, E16
    - **Main Caveat:** Trust is bounded by preprint-style evidence: the paper reports benchmark tables without error bars, admits weak video and English coverage, and shows short utterances remain hard under streaming full-duplex speech recognition.
      **主要边界:** 可信度受限于预印本式的证据：论文给出的基准测试表格没有误差条，承认在视频和英语方面覆盖较弱，并且显示在流式全双工（full-duplex）语音识别下，短语句仍然难以处理。
      claim_kind:: analyst_assessment
      evidence:: E13, E14
- ## Argument Map
    - **Problem and Stakes:** The paper argues that real-time audio-video dialogue fails when listening, speaking, reasoning, and tool use are serialized: slow reasoning blocks speech, while stripping reasoning away makes the assistant less useful. The stake is not just lower latency, but keeping the social rhythm of a conversation while still allowing hard tasks.
      **问题与重要性:** 论文认为，当把听、说、推理和工具使用串行排列时，实时音视频对话就会失败：慢速推理会阻塞说话，而把推理去掉又会让助手变得没那么有用。这里的关键不只是降低延迟，而是要在保持对话社交节奏的同时，仍然能够完成困难的任务。
      evidence:: E2
    - **Prior Gap:** The prior-work gap is between broad all-modal models, which often remain request-response systems, and full-duplex speech models, which listen while speaking but still have trouble when a dialogue needs longer reasoning. The paper positions DuplexOmni as a coordination design rather than only a larger model.
      **已有方法缺口:** 以往工作的空白介于两类模型之间：一类是广泛的全模态模型，它们往往仍然是请求-响应式的系统；另一类是全双工（full-duplex）语音模型，它们能一边说一边听，但当对话需要较长的推理时仍然会遇到困难。论文把 DuplexOmni 定位为一种协调机制的设计，而不仅仅是一个更大的模型。
      evidence:: E3
    - **Key Insight:** The key insight is to split live interaction from slow cognition: a low-latency interaction layer handles audio, video, dialogue rhythm, and speech output, while a pluggable thinking layer runs stronger language models or tools asynchronously. This makes reasoning a background service rather than a blocking stage.
      **关键洞见:** 核心洞见是把实时交互与慢速认知分离开：一个低延迟的交互层负责处理音频、视频、对话节奏和语音输出，同时一个可插拔的思考层异步地运行更强的语言模型或工具。这样一来，推理就成了后台服务，而不再是阻塞式的处理阶段。
      evidence:: E4
    - **Claims:** The paper's claim chain has four falsifiable parts: the architecture should preserve live interaction, the interaction model should implement that architecture at streaming granularity, the data pipeline should teach temporal behavior, and the benchmark evidence should separate interaction quality from reasoning strength.
      **核心主张:** 这篇论文的论点链条包含四个可证伪的部分：该架构应当保持实时交互；交互模型应当在流式粒度上实现这一架构；数据流水线应当教会模型时间性行为；基准测试的证据应当把交互质量与推理能力区分开。
      evidence:: E1, E4, E11
        - C1: Decoupling a realtime interaction layer from an asynchronous thinking layer lets the system continue listening, seeing, speaking, and updating the dialogue while slower reasoning or tool use proceeds.
          C1：把实时交互层与异步思考层解耦，使系统能够在较慢的推理或工具使用进行的同时，继续听、看、说并更新对话。
          evidence:: E1, E4
        - C2: The DuplexOmni model can implement the interaction layer by processing fixed speech-video slices and generating text plus speech for each slice with a Thinker-Talker architecture.
          C2：DuplexOmni 模型可以实现交互层，做法是处理固定的语音—视频切片，并借助 Thinker-Talker 架构为每个切片生成文本和语音。
          evidence:: E5, E6
        - C3: A Writer-Director data pipeline can convert ordinary dialogue content into temporally annotated training samples for interruption, overlap, waiting, thinking triggers, delayed feedback, and silence.
          C3：一条 Writer-Director 数据流水线可以把普通的对话内容转换成带时间标注的训练样本，用于覆盖打断、重叠、等待、思考触发、延迟反馈和沉默等情形。
          evidence:: E7, E8, E16
        - C4: On the reported benchmarks, DuplexOmni improves full-duplex interaction and streaming audio reasoning under realtime settings, and ablations attribute these gains to both the interaction layer and the thinking layer.
          C4：在论文报告的基准测试中，DuplexOmni 在实时设定下提升了全双工交互（full-duplex interaction）和流式音频推理的表现，消融实验把这些提升归因于交互层和思考层两者。
          evidence:: E10, E11, E12
- ## Mechanism and Design
    - **Core Mechanism:** DuplexOmni is organized as an interaction layer plus a thinking layer. The interaction layer continuously consumes user speech, video frames, dialogue history, and returned thinking fragments, while the thinking layer acts as a background source of deeper reasoning or tool results.
      **核心机制:** DuplexOmni 由一个交互层加一个思考层组成。交互层持续接收用户语音、视频帧、对话历史以及返回的思考片段，思考层则充当更深层推理或工具结果的后台来源。
      evidence:: E4, E5
        - The interaction layer owns live dialogue control: it decides when to respond, wait, stop, request help, and fold returned results into later speech.
          交互层掌控实时对话：它决定何时回应、等待、停止、请求帮助，以及如何把返回的结果融入后续的语音输出。
          evidence:: E4
        - The thinking layer is pluggable: the paper says it may be a strong language model, a multimodal large language model (MLLM), or a task-specific agent for reasoning, tool use, or planning.
          思考层是可插拔的：论文指出它可以是一个强语言模型、一个多模态大语言模型（MLLM），或者一个用于推理、工具使用或规划的特定任务智能体。
          evidence:: E4
        - The join point is streaming feedback: thinking results arrive as intermediate fragments with control tokens, and the interaction layer may continue, revise, or stop that stream as the conversation changes.
          两层的衔接点是流式反馈：思考结果以带控制标记的中间片段的形式陆续到达，交互层可以随着对话的变化选择继续、修改或停止这一片段流。
          evidence:: E4, E8
    - **Data / Control Flow:** Execution is time-sliced: at each fixed slice, the model reads the previous slice's audio-video input, dialogue history, and thinking feedback, then emits a thinking-control signal, an interpretation of new user input, assistant text, and assistant speech. This turns full-duplex behavior into a repeated streaming update rather than a turn-level transaction.
      **数据/控制流:** 执行过程按时间切片进行：在每个固定切片上，模型读取上一切片的音视频输入、对话历史和思考反馈，然后输出一个思考控制信号、对新用户输入的理解、助手文本和助手语音。这样一来，全双工交互（full-duplex interaction，即助手在说话的同时仍能持续接收用户语音，因此重叠、打断和附和都是正常操作的一部分）就变成了不断重复的流式更新，而不是以整个回合为单位的一次性交易。
      evidence:: E5, E6
        - The Thinker, the text-and-context part of the model, generates assistant text tokens and hidden states from the current multimodal context.
          Thinker 是模型中负责文本和上下文的部分，它根据当前的多模态上下文生成助手的文本词元（token）和隐藏状态。
          evidence:: E6
        - The Talker, the speech-generating part, conditions on Thinker outputs and previous speech-code history to autoregressively produce residual vector quantization (RVQ) codec tokens, which are discrete audio codes decoded into waveform.
          Talker 是负责生成语音的部分，它以 Thinker 的输出和此前的语音编码历史为条件，自回归地生成残差向量量化（residual vector quantization，RVQ）编解码器词元。这些词元是离散的音频编码，随后被解码为波形。
          evidence:: E6
        - For realtime inference, Thinker text generation and Talker speech generation run as an asynchronous pipeline, with cache-based incremental decoding and graph execution optimization used to reduce repeated speech-generation work.
          为实现实时推理，Thinker 的文本生成与 Talker 的语音生成以异步流水线的方式运行，并借助基于缓存的增量解码和图执行优化来减少语音生成中的重复计算。
          evidence:: E9
    - **Design Decisions:** The main design choices all serve the same pressure point: preserve conversational immediacy while allowing computation that may take longer than a speech chunk. The tradeoff is that correctness now depends on clean coordination signals, realistic temporal data, and robust handling of stale or interrupted thinking results.
      **设计决策:** 主要的设计选择都服务于同一个关键难题：既要保持对话的即时性，又要允许那些可能比一段语音更耗时的计算。由此带来的权衡是，系统的正确性如今取决于是否有干净的协调信号、贴近真实的时间数据，以及对过期或被打断的思考结果的稳健处理。
      claim_kind:: analyst_assessment
      evidence:: E4, E7, E8, E9
        - Need: avoid blocking speech during tool use; choice: decouple live interaction from background reasoning; closest alternative: one serial model pipeline; tradeoff: the interaction layer must decide when returned reasoning is still relevant.
          需求：在使用工具时避免阻塞语音；选择：把实时交互与后台推理解耦；最接近的替代方案：使用单一串行的模型流水线；权衡：交互层必须判断返回的推理结果是否仍然相关。
          evidence:: E2, E4
        - Need: train and infer on continuous streams; choice: fixed speech-video slices with carried history; closest alternative: ordinary turn-based dialogue; tradeoff: slice-level state is easier to schedule but short fragments can be hard to recognize.
          需求：在连续的流式数据上进行训练和推理；选择：使用固定的语音—视频切片，并携带历史信息；最接近的替代方案：普通的以回合为单位的对话；权衡：切片级别的状态更容易调度，但过短的片段可能难以识别。
          evidence:: E5, E13
        - Need: supervise timing behaviors absent from ordinary dialogue; choice: generate a script, then add temporal control tokens; closest alternative: raw multi-turn text; tradeoff: the training signal is explicit but synthetic annotation quality becomes load-bearing.
          需求：监督普通对话中不存在的时序行为；选择：先生成一个脚本，然后加入时间控制词元；最接近的替代方案：原始的多轮文本；权衡：训练信号变得明确，但合成标注的质量因此成为承重环节。
          evidence:: E7, E8, E16
    - **Implementation Surface:** The reported implementation initializes from Qwen3-Omni, trains with two-stage supervised fine-tuning, alternates Thinker and Talker optimization, synthesizes speech with Qwen3-TTS, encodes speech with the Mimi codec, and trains on a large H20 GPU cluster. The paper states it will release model weights, training data, and training and inference implementation, but the provided text does not give repository links or exact reproduction scripts.
      **实现边界:** 论文中所述的实现从 Qwen3-Omni 初始化，采用两阶段监督微调进行训练，交替优化 Thinker 和 Talker，用 Qwen3-TTS 合成语音，用 Mimi 编解码器对语音进行编码，并在一个大型 H20 GPU 集群上训练。论文声明将发布模型权重、训练数据以及训练和推理实现，但所提供的文本没有给出代码仓库链接或确切的复现脚本。
      evidence:: E1, E15, E16
- ## Evaluation and Evidence
    - **Setup:** The comparison covers realtime omni and speech-to-speech systems under streaming or realtime settings, using Full DuplexBench for turn-taking interaction, Big Bench Audio for streaming audio understanding, Daily-Omni for general omni capability, LibriSpeech word error rate (WER) for speech recognition quality, and latency for response delay. The default full system uses DuplexOmni as the interaction layer and Gemini-3.1-Flash-Lite as the thinking layer.
      **实验设置:** 对比涵盖了在流式或实时设置下的实时全模态（omni）系统和语音到语音系统，使用 Full DuplexBench 评估轮流发言（turn-taking）交互，用 Big Bench Audio 评估流式音频理解，用 Daily-Omni 评估通用全模态能力，用 LibriSpeech 的词错误率（word error rate，WER）评估语音识别质量，并用延迟衡量响应时延。默认的完整系统以 DuplexOmni 作为交互层，以 Gemini-3.1-Flash-Lite 作为思考层。
      evidence:: E10
    - **Claim-Evidence Matrix:** The evidence is strongest for C4's benchmark and ablation claims, reasonably direct for C1-C2's implementation claims, and supportive but less independently validated for C3's synthetic data-pipeline claim. No reported result includes confidence intervals, repeated-run statistics, or human preference uncertainty.
      **主张-证据矩阵:** 对 C4 的基准测试与消融实验相关论断，证据最为充分；对 C1 至 C2 的实现相关论断，证据也相当直接；对 C3 关于合成数据流水线的论断，证据虽有支持，但独立验证程度较弱。文中报告的所有结果都没有给出置信区间、多次重复运行的统计数据，也没有给出人类偏好判断的不确定性。
      claim_kind:: analyst_assessment
      evidence:: E10, E11, E12, E16
        - C1 is supported by the described non-blocking interaction/thinking split and by ablations where replacing thinking barely changes Full DuplexBench ToR, but the paper does not isolate failure cases where stale thinking feedback harms dialogue.
          C1 得到以下证据支持：文中所描述的交互与思考之间互不阻塞的拆分方式；以及消融实验中「替换掉思考部分几乎不改变完整 DuplexBench 的对话转换合理性（ToR）」这一结果。但文中并未单独分析那些「陈旧的思考反馈损害对话」的失败案例。
          claim_kind:: analyst_assessment
          evidence:: E4, E12
        - C2 is supported by the model's slice-level architecture and reported latency, but the paper gives limited profiling detail for the exact scheduler, cache reuse, or graph optimization contribution.
          C2 得到该模型的分片级架构以及所报告的延迟数据支持，但文中对具体调度器、缓存复用或图优化各自贡献了多少，只给出了有限的性能剖析细节。
          claim_kind:: analyst_assessment
          evidence:: E5, E6, E9, E11
        - C3 is supported by the control-token design and corpus statistics; C4 is supported by benchmark tables and ablations, with the caveat that baseline API settings and evaluation variance are only partly observable from the paper text.
          C3 得到控制标记（control token）的设计以及语料统计数据支持；C4 得到基准测试表格与消融实验支持，但需要说明的是：从论文正文中只能部分看出基线的 API 设置以及评测结果的方差。
          claim_kind:: analyst_assessment
          evidence:: E8, E10, E11, E12, E16
    - **Headline Results:** The headline result is that DuplexOmni reports the best Full DuplexBench ToR among realtime baselines while maintaining around half-second latency, and also reports the best Big Bench Audio score in the table. The closest directly comparable interaction baseline by latency is MiniCPM-o 4.5, where DuplexOmni reports much higher ToR but lower Daily-Omni accuracy.
      **关键结果:** 最主要的结果是：在各个实时基线中，DuplexOmni 报告出最优的完整 DuplexBench 对话转换合理性（ToR），同时把延迟维持在约半秒；在表格中它还报告出最优的 Big Bench Audio 分数。按延迟计算最接近、可直接对比的交互基线是 MiniCPM-o 4.5——相比之下，DuplexOmni 报告的 ToR 高出许多，但 Daily-Omni 准确率则更低。
      evidence:: E11
        - Supported claim: C4; configuration: full DuplexOmni; baseline: MiniCPM-o 4.5; metric: Full DuplexBench ToR, higher is better; delta: 72.6% versus 36.3%; uncertainty: not reported; caveat: benchmark details and human-rating variance are not shown in the excerpt.
          支持的论断：C4；配置：完整 DuplexOmni；基线：MiniCPM-o 4.5；指标：完整 DuplexBench 对话转换合理性（ToR），越高越好；差距：72.6% 对比 36.3%；不确定性：未报告；注意事项：摘录中未展示基准测试细节以及人类评分的方差。
          evidence:: E10, E11
        - Supported claim: C2 and C4; configuration: realtime full system; baseline: MiniCPM-o 4.5 and Qwen realtime variants; metric: latency, lower is better; delta: 0.506 s versus 0.502 s for MiniCPM-o 4.5 and 1.25-1.28 s for Qwen realtime variants; uncertainty: not reported.
          支持的论断：C2 与 C4；配置：实时完整系统；基线：MiniCPM-o 4.5 以及 Qwen 的实时变体；指标：延迟，越低越好；差距：0.506 秒对比 MiniCPM-o 4.5 的 0.502 秒，以及 Qwen 实时变体的 1.25–1.28 秒；不确定性：未报告。
          evidence:: E10, E11
        - Supported claim: C4; configuration: full DuplexOmni; baseline: Gemini-3.1-Flash-Lite thinking-only and Gemini Live; metric: Big Bench Audio, higher is better; delta: 77.2% versus 58.9% and 57.9%; uncertainty: not reported; caveat: the full system uses a Gemini thinking layer.
          支持的论断：C4；配置：完整 DuplexOmni；基线：仅思考版的 Gemini-3.1-Flash-Lite 以及 Gemini Live；指标：Big Bench Audio，越高越好；差距：77.2% 对比 58.9% 和 57.9%；不确定性：未报告；注意事项：完整系统使用了一个 Gemini 思考层。
          evidence:: E10, E11, E12
    - **Ablations and Sensitivity:** The ablations support the layered interpretation: weakening the thinking layer leaves Full DuplexBench nearly unchanged but sharply reduces Big Bench Audio, while removing thinking reduces reasoning further. The ASR analysis shows sensitivity to utterance length, with short user fragments much harder than longer ones.
      **消融与敏感性:** 消融实验支持这种分层的解释：削弱思考层几乎不改变完整 DuplexBench 的结果，却大幅降低 Big Bench Audio；而完全移除思考则进一步削弱推理能力。ASR 分析显示结果对话语长度较为敏感——较短的用户语音片段比较长的片段难处理得多。
      evidence:: E12, E13
        - Supported claim: C1 and C4; configuration: weak thinking versus full thinking; baseline: full system; metric: Full DuplexBench ToR and Big Bench Audio; delta: ToR 72.6% to 72.1%, Big Bench Audio 77.2% to 50.3%; support status: supports separation of interaction and reasoning strength.
          支持的论断：C1 与 C4；配置：弱思考对比完整思考；基线：完整系统；指标：完整 DuplexBench 对话转换合理性（ToR）以及 Big Bench Audio；差距：ToR 从 72.6% 变为 72.1%，Big Bench Audio 从 77.2% 变为 50.3%；支持状态：支持「交互能力与推理能力可以分离」这一结论。
          evidence:: E12
        - Supported claim: C4; configuration: no thinking layer; baseline: full system; metric: Big Bench Audio; delta: 77.2% to 22.2%; support status: supports the claim that the thinking layer sets the reasoning ceiling.
          支持的论点：C4；配置：去掉思考层；基线：完整系统；指标：Big Bench Audio；变化幅度：从 77.2% 降到 22.2%；支持情况：支持「思考层决定推理能力上限」这一论点。
          evidence:: E12
        - Supported claim: boundary on C2 and C4; configuration: full-duplex ASR by utterance length; baseline: longer utterances; metric: WER, lower is better; delta: 25.1% for 1-5 words versus 8.8% for 21+ words; support status: shows short low-context speech is a weakness.
          支持的论点：C2 与 C4 的边界情形；配置：按说话内容长度划分的全双工自动语音识别（ASR）；基线：较长的说话内容；指标：词错误率（WER），数值越低越好；变化幅度：1 至 5 个词的说话内容为 25.1%，而 21 个词及以上的为 8.8%；支持情况：表明短促且缺乏上下文的语音是一个薄弱环节。
          evidence:: E13
    - **Reproducibility Gaps:** The paper promises release of weights, training data, and training and inference implementation, but the provided text itself does not include a repository, exact evaluation scripts, random seeds, repeated runs, cost budget, or enough proprietary API details to rerun all baselines. Reuse is also constrained by the large training stack, synthetic speech generation, and dependence on a strong external thinking model in the default configuration.
      **可复现性缺口:** 论文承诺公开模型权重、训练数据以及训练和推理的实现代码，但所提供的正文本身并未包含代码仓库、确切的评测脚本、随机种子、重复运行结果、成本预算，也没有足够的专有 API 细节来重跑所有基线。此外，庞大的训练技术栈、合成语音的生成过程，以及默认配置下对一个强大外部思考模型的依赖，都进一步限制了成果的复用。
      claim_kind:: analyst_assessment
      evidence:: E1, E10, E15, E16
- ## Technical Judgment
    - **What Holds Up:** The architecture is coherent because the paper identifies a real scheduling conflict and assigns the fast, user-facing loop and slow reasoning loop to different execution spaces. The ablation pattern is also internally consistent: interaction quality mostly follows the DuplexOmni model, while streaming audio reasoning follows the thinking layer plus the interaction layer's filtering and organization.
      **站得住的结论:** 该架构是自洽的，因为论文识别出了一个真实存在的调度冲突，并把面向用户的快速循环与缓慢的推理循环分配到不同的执行空间。消融实验的模式在内部也保持一致：交互质量主要取决于 DuplexOmni 模型，而流式音频推理则取决于思考层，再加上交互层对结果的筛选与组织。
      claim_kind:: analyst_assessment
      evidence:: E2, E4, E11, E12
    - **Where It May Fail:** The system may fail when user intent changes faster than thinking feedback can be invalidated, when visual grounding matters more than the small video-call corpus can support, or when short speech fragments carry the decisive cue. Benefits should diminish in low-latency tasks that require no external reasoning, and in languages or accents underrepresented in the training data.
      **可能失效之处:** 在以下情形下系统可能失效：用户意图的变化速度快于思考反馈被作废的速度；视觉定位的重要性超出了规模较小的视频通话语料所能支撑的范围；或者关键线索恰好藏在短促的语音片段里。在无需外部推理的低延迟任务中，以及在训练数据中代表性不足的语言或口音上，系统的收益应当会减弱。
      claim_kind:: analyst_assessment
      evidence:: E8, E13, E14, E16
    - **Relation to Other Work:** Relative to broad omni models, DuplexOmni emphasizes interaction scheduling rather than only modality unification. Relative to full-duplex speech systems such as Moshi-like or flattened speech-text approaches, it adds an explicit asynchronous reasoning/tool layer and temporal supervision for when to wait, cut off, reset, or incorporate delayed results.
      **与已有工作的关系:** 与覆盖面宽泛的全模态模型（omni model）相比，DuplexOmni 更强调交互调度，而不仅仅是把各种模态统一起来。与类似 Moshi 或把语音与文本压平处理的全双工语音系统相比，它额外增加了一个显式的异步推理／工具层，以及关于何时等待、打断、重置或纳入延迟结果的时序监督。
      claim_kind:: analyst_assessment
      evidence:: E3, E4, E8
    - **Transferable Lesson:** The transferable pattern is to split latency-critical interaction from accuracy-critical deliberation, then train the boundary explicitly with control signals rather than hoping a single sequence model learns the timing protocol implicitly. This applies beyond voice assistants to any interactive AI system where the user-facing loop must remain responsive while deeper computation continues.
      **可迁移启发:** 可迁移的模式是：把对延迟敏感的交互与对准确性敏感的深思熟虑分离开，然后用控制信号显式地训练二者之间的边界，而不是指望单个序列模型隐式地学会这套时序协议。这一做法不限于语音助手，任何交互式 AI 系统都适用——只要它面向用户的循环必须保持响应灵敏，同时更深层的计算仍在继续进行。
      claim_kind:: analyst_assessment
      evidence:: E4, E7, E8, E9
- ## Glossary
  collapsed:: true
    - full-duplex interaction: A dialogue mode where the assistant can keep receiving user speech while it is speaking, so overlap, interruption, and backchannels are part of normal operation.
      全双工交互（full-duplex interaction）：一种对话模式，助手在自己说话的同时仍能持续接收用户的语音，因此重叠说话、打断和附和（如「嗯」「对」这类回应）都属于正常运行的一部分。
    - omni model: A model that handles multiple modalities such as speech, text, image, video, and sometimes speech output in one unified interaction system.
      全模态模型（omni model）：一种在单一统一交互系统中处理多种模态的模型，这些模态包括语音、文本、图像、视频，有时还包括语音输出。
    - interaction layer: The fast layer responsible for live listening, watching, dialogue rhythm, immediate text response, and speech output.
      交互层：负责实时聆听、观看、对话节奏、即时文本回应以及语音输出的快速层。
    - thinking layer: A pluggable slower layer that can run a strong language model, multimodal model, or tool agent and stream useful results back to the interaction layer.
      thinking layer（思考层）：一个可插拔的较慢层，可以运行强语言模型、多模态模型或工具智能体，并把有用的结果以流式方式回传给交互层。
    - Thinker-Talker architecture: A speech-generation design where a text/context model produces linguistic states and a speech model converts those states into audio codec tokens.
      Thinker-Talker 架构：一种语音生成设计，其中文本/上下文模型产生语言状态，而语音模型把这些状态转换成音频编解码 token。
    - time-sliced inference: A streaming inference schedule that repeatedly processes fixed-duration chunks of input and emits the next chunk of control, text, and speech output.
      time-sliced inference（分时推理）：一种流式推理调度方式，反复处理固定时长的输入片段，并输出下一段控制信息、文本和语音。
    - residual vector quantization: An audio representation that stores speech as multiple layers of discrete codes; the Talker predicts these codes before a decoder turns them back into waveform.
      residual vector quantization（残差矢量量化，RVQ）：一种音频表示方法，把语音存储为多层离散编码；Talker 先预测这些编码，随后由解码器把它们还原成波形。
    - MTP module: The module used after the first codec layer prediction to fill the remaining residual codebooks for each speech frame.
      MTP 模块（多 token 预测模块）：在预测出第一个编解码层之后使用的模块，用于为每个语音帧填补剩余的残差码本。
    - Director control tokens: Special annotations that mark when background thinking starts, when returned thinking is injected, where overlap begins, where speech stops, when thinking resets, and when shared silence occurs.
      Director 控制 token：一些特殊标注，用来标记何时开始后台思考、何时注入返回的思考结果、何处开始语音重叠、何处停止语音、何时重置思考，以及何时出现双方共同的静默。
    - real-time factor: The ratio between generation time and audio duration; below one means a chunk can be generated before it finishes playing.
      real-time factor（实时率，RTF）：生成时间与音频时长的比值；小于 1 意味着一个片段能在它播放完毕之前就生成出来。
    - KV cache: Saved attention state from earlier tokens that lets an autoregressive model avoid recomputing the whole prefix during incremental decoding.
      键值缓存（KV cache）：从早先 token 保存下来的注意力状态，使自回归模型在逐步解码时无需重新计算整个前缀。
    - word error rate: A speech recognition error metric; lower is better, and the paper uses it to show that short utterances are difficult under full-duplex streaming.
      word error rate（词错误率，WER）：一种语音识别的错误度量指标，数值越低越好；论文用它来说明在全双工流式场景下短句很难识别。
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/paper_statement | Abstract and Introduction | high
      locator:: Abstract; Section 1 contributions
      quote:: We present DuplexOmni, a method for real-time multimodal full-duplex interaction. DuplexOmni separates model capability into an interaction layer and a thinking layer, which collaborate asynchronously in parallel.
    - **E2:** problem/paper_statement | Introduction | high
      locator:: Section 1, Figure 1 discussion
      quote:: When interaction involves deep thinking or tool use, the model often pauses the ongoing dialogue. It then waits for reasoning or tool results before continuing its response. This causes clear interruptions.
    - **E3:** gap/paper_statement | Related work | high
      locator:: Sections 2.1 and 2.2
      quote:: Most of these models still organize interaction in a request-driven manner: user input is collected, the model performs understanding and generation, and then a response is returned. This mode is suitable for single-turn or multi-turn task processing, but cannot handle user interaction in real time.
    - **E4:** system_design/implementation_detail | Method | high
      locator:: Section 3 and Section 3.1.1
      quote:: The interaction layer handles real-time dialogue, while the thinking layer performs background reasoning. When the current interaction requires external assistance, the interaction layer passes the user context to the thinking layer... This request does not block real-time interaction.
    - **E5:** algorithm/implementation_detail | DuplexOmni Model | high
      locator:: Section 3.1.2, Time-Sliced Full-Duplex Modeling
      quote:: We divide continuous interaction into fixed 480 ms slices. At slice t, the model consumes the dialogue history, the intermediate results returned by the thinking layer, and the inputs from slice t-1.
    - **E6:** implementation/implementation_detail | DuplexOmni Model | high
      locator:: Section 3.1.2, Model Architecture
      quote:: DuplexOmni model follows the Thinker-Talker speech generation structure in the Qwen-Omni family. The Thinker is the internal MLLM backbone that processes the current context and generates Assistant text tokens. The Talker converts the generated linguistic states into streaming speech.
    - **E7:** method/paper_statement | Data Construction | high
      locator:: Section 3.2 opening
      quote:: Existing multi-turn dialogue data is mostly turn-based. It only records user and assistant utterances, and lacks temporal information. Therefore, it cannot describe when the model should speak, stop, wait, trigger background thinking, or use returned information.
    - **E8:** method/implementation_detail | Writer-Director Data Pipeline | high
      locator:: Section 3.2.2 and Appendix A, Table 4
      quote:: The Director converts this script into a structured sample with temporal control signals... [THINK] triggers background reasoning... [CUT] marks the actual stopping point... [WAIT] means that the user adds a new condition, so the background reasoning should pause or revise.
    - **E9:** optimization/implementation_detail | Real-Time Duplex Inference | high
      locator:: Section 3.3
      quote:: DuplexOmni uses RTF < 1 as the latency target for speech generation... DuplexOmni decouples Thinker-based text generation from Talker-based speech generation and runs them as an asynchronous pipeline.
    - **E10:** experiment_setup/paper_statement | Experiments | medium
      locator:: Section 4.1 Settings
      quote:: We compare DuplexOmni with recent real-time omni models and speech-to-speech systems, including MiniCPM-o, Doubao, Qwen-Omni realtime variants, and Gemini live variants. All models are evaluated under their streaming or realtime settings.
    - **E11:** result/experiment_result | Performance Comparison | medium
      locator:: Section 4.4 and Table 1
      quote:: DuplexOmni achieves 72.6% ToR on Full DuplexBench, substantially outperforming all realtime baselines, while keeping a response latency of 0.506s. DuplexOmni achieves the best Big Bench Audio score of 77.2% and remains competitive on Daily-Omni.
    - **E12:** ablation/ablation | Ablation Study | medium
      locator:: Section 4.5 and Table 2
      quote:: When the thinking layer is replaced by a weaker model, Big Bench Audio drops from 77.2% to 50.3%; removing the thinking layer further reduces it to 22.2%.
    - **E13:** result/experiment_result | Full-Duplex ASR Analysis | medium
      locator:: Section 4.6 and Table 3
      quote:: Table 3 shows that DuplexOmni performs worse on short utterances, with WER dropping from 25.1% for 1-5 words to 8.8% for 21+ words. This suggests that short, low-context speech fragments in full-duplex interaction remain a key challenge.
    - **E14:** limitation/limitation | Limitations | high
      locator:: Limitations
      quote:: First, its video capability remains limited because the amount of video-call and visually grounded interaction data is relatively small. Second, its English speech ability is weaker than desired, partly due to the training data being dominated by Chinese speech.
    - **E15:** experiment_setup/implementation_detail | Training | high
      locator:: Section 4.3 Training
      quote:: Initialized from Qwen3-Omni, it is trained with two-stage SFT... The learning rate is 1e-5 for the Thinker and 1e-4 for the Talker, with a batch size of 128. Training is conducted with Megatron-swift-3.12 on 128 Nvidia H20 GPUs.
    - **E16:** experiment_setup/paper_statement | Data and Appendix C | high
      locator:: Sections 4.2, C.1-C.3, Tables 5-7
      quote:: We build about 620K scenario seeds... The dialogue content contains about 3.02M raw conversations, including 10K video-call conversations... delayed reasoning 94.3... Samples containing >=2 patterns 90.7.
