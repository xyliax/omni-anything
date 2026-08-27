- **Title:** MiniCPM-o 4.5: Towards Real-Time Full-Duplex Omni-Modal Interaction
  **标题:** MiniCPM-o 4.5：迈向实时全双工全模态交互
- **Summary:** MiniCPM-o 4.5 treats live multimodal interaction as one time-aligned stream so a compact 9B model can watch, listen, and speak at once while keeping deployable edge efficiency.
  **一句话总结:** MiniCPM-o 4.5 把实时的多模态交互当作一条按时间对齐的数据流来处理，使得一个仅有 9B 参数的紧凑模型能够同时观看、聆听和说话，同时保持在边缘设备上可部署的高效率。
- **Paper Type:** system
  **论文类型:** 系统
- **Venue:** arXiv preprint 2026
  **发表:** arXiv 预印本 2026
- **Authors:** Junbo Cui, Bokai Xu, Chongyi Wang, Tianyu Yu, Weiyue Sun, Yingjing Xu, Tianran Wang, Zhihui He, Wenshuo Ma, Tianchi Cai, Jiancheng Gui, Luoyuan Zhang, Xian Sun, Fuwei Huang, Moye Chen, Zhuo Lin, Hanyu Liu, Qingxin Gui, Qingzhe Han, Yuyang Wen, Huiping Liu, Rongkang Wang, Yaqi Zhang, Hongliang Wei, Chi Chen, You Li, Kechen Fang, Jie Zhou, Yuxuan Li, Guoyang Zeng, Chaojun Xiao, Yankai Lin, Xu Han, Maosong Sun, Zhiyuan Liu, Yuan Yao; affiliations Unknown
  **作者:** Junbo Cui、Bokai Xu、Chongyi Wang、Tianyu Yu、Weiyue Sun、Yingjing Xu、Tianran Wang、Zhihui He、Wenshuo Ma、Tianchi Cai、Jiancheng Gui、Luoyuan Zhang、Xian Sun、Fuwei Huang、Moye Chen、Zhuo Lin、Hanyu Liu、Qingxin Gui、Qingzhe Han、Yuyang Wen、Huiping Liu、Rongkang Wang、Yaqi Zhang、Hongliang Wei、Chi Chen、You Li、Kechen Fang、Jie Zhou、Yuxuan Li、Guoyang Zeng、Chaojun Xiao、Yankai Lin、Xu Han、Maosong Sun、Zhiyuan Liu、Yuan Yao；所属机构未知
- **Keywords:** omni-modal interaction, full-duplex streaming, multimodal large language model, speech generation, edge inference, Omni-Flow
  **关键词:** 全模态交互、全双工流式处理、多模态大语言模型、语音生成、边缘推理、Omni-Flow
- ## Orientation
    - **Background:** This paper lives in interactive AI: systems that take in what a person sees, says, types, and hears, then answer back. The key prerequisite is streaming, where information arrives continuously instead of as one finished prompt.
      **背景:** 这篇论文属于交互式人工智能领域，也就是那些能接收一个人所看、所说、所打字、所听内容，并给出回应的系统。其关键前提是流式处理，即信息是持续不断到达的，而不是作为一个完整的提示一次性给出。
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** Most assistants still behave like walkie-talkies: one side talks, then the other side talks. Real conversation needs an assistant that can keep watching and listening while it is already responding.
      **通俗问题:** 大多数助手仍然像对讲机一样工作：一方说话，然后另一方说话。真正的对话需要助手在自己已经开始回应时，还能继续观看和聆听。
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** The model must decide what happened, whether to speak, what to say, and how to vocalize it while the world keeps changing. If any part runs ahead or falls behind, the answer can become stale.
      **为何困难:** 在世界不断变化的同时，模型必须判断发生了什么、是否要开口、说什么，以及如何把它说出来。如果其中任何一环跑得太快或落后，回答就可能变得陈旧。
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Put every incoming signal and every outgoing word on one shared clock, then let the next response be conditioned on the newest moment rather than an old turn boundary.
      **一句话核心思路:** 把每一个输入信号和每一个输出词语都放到同一个共享的时钟上，然后让下一个回应以最新的时刻为条件，而不是以某个旧的对话回合边界为条件。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a model-systems paper for omni-modal interaction, meaning one assistant processes vision, sound, text, and speech together; its useful gap is not adding one more input type, but keeping input and output active in the same moment.
      **阅读价值:** 把这篇论文当作一篇面向全模态交互的模型系统论文来读，也就是让一个助手同时处理视觉、声音、文本和语音。它真正有价值的突破，不在于再多支持一种输入类型，而在于让输入和输出能在同一时刻都保持活跃。
      claim_kind:: analyst_assessment
      evidence:: E2, E3
    - **One-Sentence Contribution:** MiniCPM-o 4.5 improves real-time assistant interaction by replacing turn taking with a shared timeline that lets new visual and audio input affect the response while the model is still speaking.
      **一句话贡献:** MiniCPM-o 4.5 用一条共享的时间线取代了传统的轮流对话方式，让新的视觉和音频输入在模型还在说话的过程中就能影响回应，从而改善了实时助手交互体验。
      evidence:: E3, E5, E7
    - **Mental Model:** Picture a live commentator who keeps one eye on the field, one ear on the crowd, and a finger on the microphone; every short moment, the next words are chosen from what just happened, not only from the scene at the start.
      **记忆模型:** 想象一位现场解说员：一只眼睛盯着球场，一只耳朵听着人群，一根手指按在麦克风上。每一个短暂的时刻，接下来要说的话都取决于刚刚发生的事，而不仅仅取决于开场时看到的画面。
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is triangulated across capability tables, one full-duplex benchmark, and deployment measurements, with the important caveat that the result tables do not report statistical uncertainty.
      **最佳证据:** 最有力的证据来自三方面的相互印证：能力对比表格、一个全双工基准测试，以及部署实测数据。但需要注意一个重要前提，即这些结果表格并未报告统计上的不确定性。
      claim_kind:: analyst_assessment
      evidence:: E11, E13, E16
        - Supports C4: instruct vision-language setting; Gemini 2.5 Flash and Qwen3-Omni baselines; OpenCompass score; MiniCPM-o 4.5 reaches 77.6 versus 78.5 and 75.7; support is broad but table-only.
          支持 C4：指令式视觉-语言场景；对比基线为 Gemini 2.5 Flash 与 Qwen3-Omni；采用 OpenCompass 得分；MiniCPM-o 4.5 得分为 77.6，两个基线分别为 78.5 与 75.7；支持面较广，但仅有表格数据。
          evidence:: E11
        - Supports C4: vision-only full-duplex LiveSports-3K-CC; LiveCC and StreamingVLM baselines; win rate; MiniCPM-o 4.5 scores 54.4 versus 41.5 and 45.6; support is direct but not audio-inclusive.
          支持 C4：纯视觉全双工的 LiveSports-3K-CC；对比基线为 LiveCC 与 StreamingVLM；采用胜率指标；MiniCPM-o 4.5 得分为 54.4，两个基线分别为 41.5 与 45.6；支持较为直接，但未纳入音频。
          evidence:: E13
        - Supports C3: SeedTTS speech-generation modes; no-interleave and fixed-text baselines; CER/WER and speaker-similarity metrics; Time-Aligned Interleaving trades lower temporal staleness for worse English WER; support is mixed.
          支持 C3：SeedTTS 语音生成模式；对比基线为不交错（no-interleave）与固定文本（fixed-text）；采用字符错误率（CER）/词错误率（WER）与说话人相似度指标；时间对齐交错（Time-Aligned Interleaving）以更低的时间陈旧度换取更差的英文词错误率；支持效果好坏参半。
          evidence:: E15
        - Supports C4: single RTX 4090 vLLM INT4 setting; Qwen3-Omni-30B-A3B baseline; throughput, first-token latency, and memory; MiniCPM-o 4.5 reports 212.3 tokens/s, 0.58 s, and 11 GB versus 147.8, 0.98 s, and 20 GB.
          支持 C4：单张 RTX 4090 上运行 vLLM 的 INT4 场景；对比基线为 Qwen3-Omni-30B-A3B；指标为吞吐、首个 token 延迟与显存占用；MiniCPM-o 4.5 报告为 212.3 tokens/s、0.58 s 与 11 GB，基线为 147.8、0.98 s 与 20 GB。
          evidence:: E16
    - **Main Caveat:** The paper's full-duplex evidence is still narrow: the quantitative real-time benchmark is audio-free and vision-only, qualitative omni-stream demos are not standardized, and the authors report speech instability plus network-sensitive missing fragments.
      **主要边界:** 该论文关于全双工的证据仍然有限：定量的实时基准测试不含音频、只有视觉，定性的全模态流演示未经标准化，作者还报告了语音不稳定以及对网络敏感的片段缺失问题。
      claim_kind:: analyst_assessment
      evidence:: E13, E17
- ## Argument Map
    - **Problem and Stakes:** The paper frames full-duplex interaction, meaning input and output happen at the same time, as the next bottleneck for multimodal large language models (MLLMs), which are language-model systems connected to image, audio, and speech modules. The stake is whether assistants can move from passive turn-taking toward ambient help that responds to changing scenes.
      **问题与重要性:** 这篇论文把全双工交互（full-duplex interaction，指输入和输出同时发生）视为多模态大语言模型（multimodal large language model，MLLM，即连接了图像、音频和语音模块的语言模型系统）的下一个瓶颈。关键意义在于：助手能否从被动的轮流对话，转向能够对不断变化的场景做出回应的环境式辅助。
      evidence:: E2
    - **Prior Gap:** Prior interactive multimodal systems can process several media types, but the paper argues that they still serialize perception and response or let generated text drift away from speech playback. This leaves two gaps: blocked information flow during speaking and stale spoken output in changing scenes.
      **已有方法缺口:** 以往的交互式多模态系统能处理多种媒体类型，但本文指出，它们仍然把感知和响应分成先后两步串行进行，或者让生成的文字与语音播放脱节。这带来了两个缺口：说话过程中信息流被阻塞，以及在场景不断变化时说出的内容已经过时。
      evidence:: E2, E7
    - **Key Insight:** The key insight is to represent the live environment and the assistant's own output as time-aligned streams, meaning short pieces placed on the same clock. Once the data has that shape, a standard causal language model, which predicts the next unit from previous units, can model seeing, listening, deciding, and speaking in one sequence.
      **关键洞见:** 核心洞见是把实时环境和助手自身的输出都表示成时间对齐的流，也就是把一段段短小的片段放到同一个时钟上。数据一旦具备这种形式，一个标准的因果语言模型（即根据前面的单元预测下一个单元的模型）就能在一条序列中同时对看、听、决策和说话进行建模。
      evidence:: E3, E4
    - **Claims:** The paper's thesis rests on four claims: a streaming formulation, an end-to-end architecture, speech timing control, and capability-efficiency evidence.
      **核心主张:** 本文的论点建立在四项主张之上：一种流式的问题表述、一种端到端架构、语音时序控制，以及能力与效率的实证证据。
      claim_kind:: analyst_assessment
        - C1: Omni-Flow turns multimodal interaction into a full-duplex time-aligned process in which perception, output, and proactive behavior share one temporal structure.
          C1：Omni-Flow 把多模态交互转变为一个全双工的、时间对齐的过程，在这个过程中，感知、输出和主动行为共享同一套时间结构。
          evidence:: E3, E4
        - C2: A 9B end-to-end omni-modal architecture can preserve visual, speech, and text abilities while adding streaming interaction because the components exchange compact token-level representations.
          C2：一个 9B 参数的端到端全模态架构能够在增加流式交互能力的同时，保留视觉、语音和文本能力，因为各组件之间交换的是紧凑的 token 级表示。
          evidence:: E5, E6, E8
        - C3: Timely speech in full-duplex mode requires explicit timing choices, especially chunk granularity, listen-speak control, and Time-Aligned Interleaving (TAIL), which adapts text generation to speech playback.
          C3：要在全双工模式下实现及时的语音，需要做出明确的时序选择，尤其是分块粒度、听说控制（Listen-Speak control），以及时间对齐交错（Time-Aligned Interleaving，TAIL）——TAIL 让文本生成与语音播放相适配。
          evidence:: E7, E9, E15
        - C4: MiniCPM-o 4.5 is competitive with or ahead of named baselines across vision-language, speech, omni-modal, full-duplex, and efficiency evaluations at its scale.
          C4：在其参数规模下，MiniCPM-o 4.5 在视觉-语言、语音、全模态、全双工和效率等多项评测中，与所列出的基线方法相比要么持平，要么更优。
          evidence:: E11, E12, E13, E16
- ## Mechanism and Design
    - **Core Mechanism:** MiniCPM-o 4.5 uses compact tokens, meaning small model-readable units for text, audio, or visual features, as the common currency between encoders, the language backbone, and speech decoders. Omni-Flow then schedules these units in short time chunks so each output can depend on newly arrived visual and audio input.
      **核心机制:** MiniCPM-o 4.5 使用紧凑的 token（即用于表示文本、音频或视觉特征的、模型可读的小单元），作为编码器、语言主干网络和语音解码器之间的通用载体。随后，Omni-Flow 把这些单元按短小的时间块（time chunk）来调度，使得每一个输出都能依赖新到达的视觉和音频输入。
      evidence:: E3, E5, E6
        - Visual frames are encoded and resampled into fewer visual tokens, while audio is encoded in chunks and temporally compressed before entering the language backbone.
          视觉帧先被编码，再重采样成数量更少的视觉 token；音频则按块进行编码，并在进入语言主干网络之前做时间维度上的压缩。
          evidence:: E6
        - The Qwen3-8B backbone emits text-speed outputs and hidden states, and a smaller speech-token decoder uses those hidden states to produce S3 speech tokens for waveform synthesis.
          Qwen3-8B 主干网络输出文本速率的内容和隐藏状态，一个更小的语音 token 解码器利用这些隐藏状态生成 S3 语音 token（S3 speech token），用于合成波形。
          evidence:: E5, E6
        - A streaming flow-matching decoder, a neural audio generator that converts speech tokens into waveform segments, uses reference audio from the multimodal system prompt for voice-conditioned synthesis.
          流匹配解码器（flow-matching decoder，一种把语音 token 转换成波形音频片段的神经音频生成器）以流式方式工作，它利用多模态系统提示中的参考音频，实现基于声音条件的合成，也就是让生成的语音带上指定的音色。
          evidence:: E5
    - **Data / Control Flow:** Each time chunk collects environment visual tokens, environment audio tokens, and output-stream tokens; if the assistant should stay silent, the output part contains a listen token, a special control token meaning no spoken/text content now. The sequence is still causal: past and current chunk content condition the next output, so the model can decide both whether to speak and what to say.
      **数据/控制流:** 每个时间块（time chunk）都会收集三类内容：环境视觉 token、环境音频 token，以及输出流 token；如果助手此刻应当保持沉默，输出部分就包含一个 listen token，这是一种特殊的控制 token，表示当前不生成任何语音或文字内容。整个序列仍然是因果的：过去和当前时间块的内容会作为下一步输出的条件，因此模型既能决定要不要说话，也能决定说什么。
      evidence:: E3, E4, E9
        - The three load-bearing streams are env-visual for live scene observations, env-audio for acoustic context and user speech, and out-stream for generated text and speech.
          三条承载信息的关键数据流分别是：env-visual 流负责实时场景观察，env-audio 流负责声学环境与用户语音，out-stream 流负责生成的文字和语音。
          evidence:: E4
        - The Listen-Speak (LS) formulation separates the binary decision to listen or speak from content generation, instead of mixing listen and text tokens in one output space.
          Listen-Speak（LS）控制方案把「要听还是要说」这个二元判断与内容生成分开处理，而不是把 listen token 和文字 token 混在同一个输出空间里。
          evidence:: E9
    - **Design Decisions:** The main design choices all protect timing stability: one-second chunks give more context per decision, explicit group boundaries reduce parsing burden, and separated listen-speak control avoids asking one prediction step to decide both action and content. TAIL adds a second timing layer for speech so text generation does not outrun audio playback.
      **设计决策:** 主要的设计选择都是为了保护时序稳定性：使用一秒的时间块，让每次决策拥有更多上下文；显式标出分组边界，减轻解析负担；把「听/说」控制分离出来，避免让同一个预测步骤同时决定动作和内容。TAIL 为语音额外增加了一层时序控制，让文字生成不至于跑到音频播放前面去。
      evidence:: E7, E9, E15
        - Need: responsiveness and coherence compete; choice: use one-second chunks in the reported setting; alternative: shorter chunks; tradeoff: shorter windows react faster but degrade decision stability.
          需求：响应速度与连贯性之间存在冲突；选择：在论文所报告的设置中使用一秒的时间块；替代方案：使用更短的时间块；权衡：更短的窗口反应更快，但会降低决策的稳定性。
          evidence:: E9
        - Need: speech should match the current scene; choice: TAIL adapts text count from accumulated playback progress; alternative: fixed text-speech ratio; tradeoff: better temporal alignment can reduce speech-recognition accuracy.
          需求：语音应当与当前场景相匹配；选择：TAIL 根据累计的播放进度来动态调整文字的数量；替代方案：采用固定的文字与语音比例；权衡：更好的时间对齐可能会降低语音识别的准确率。
          evidence:: E7, E15
        - Need: avoid making the large backbone emit high-rate speech tokens; choice: delegate speech-token generation to a small decoder conditioned by backbone hidden states; tradeoff: extra decoder surface but lower text-generation burden.
          需求：避免让庞大的主干模型直接产出高速率的语音 token；选择：把语音 token 的生成任务交给一个小型解码器，由主干模型的隐藏状态为其提供条件；权衡：多出了一个解码器组件，但降低了文字生成的负担。
          evidence:: E5, E6
    - **Implementation Surface:** The reported system is a deployable stack rather than only a modeling idea: it specifies component sizes, precision, token rates, quantized inference, and a custom llama.cpp-omni runtime for real-time factor (RTF), meaning generated audio time divided by wall-clock time. The implementation surface spans model architecture, training data alignment, inference framework, and local demo deployment.
      **实现边界:** 论文报告的系统是一套可部署的技术栈，而不仅仅是一个建模思路：它明确给出了各组件的规模、精度、token 速率、量化推理，以及一个定制的 llama.cpp-omni 运行时，用于优化实时因子（real-time factor，RTF），即生成音频的时长除以实际耗时（挂钟时间）。整个实现层面涵盖了模型架构、训练数据对齐、推理框架，以及本地演示部署。
      evidence:: E16, E18
- ## Evaluation and Evidence
    - **Setup:** The evaluation is broad rather than deeply controlled: it spans vision-language reasoning, OCR, hallucination, video, speech recognition, speech question answering, text-only benchmarks, omni-modal understanding, full-duplex streaming, and inference efficiency. Baselines include proprietary models, open multimodal models, speech systems, and streaming video-language systems, but the paper does not report repeat counts or confidence intervals.
      **实验设置:** 评估范围很广，但控制并不深入：它涵盖视觉-语言推理、光学字符识别（OCR）、幻觉、视频、语音识别、语音问答、纯文本基准、全模态理解、全双工流式交互，以及推理效率。对比基线包括闭源专有模型、开源多模态模型、语音系统，以及流式视频-语言系统，但论文没有报告重复实验的次数或置信区间。
      claim_kind:: analyst_assessment
      evidence:: E10, E11, E12, E13, E16
    - **Claim-Evidence Matrix:** The evidence is strongest for capability and deployment efficiency, moderate for design choices, and weakest for real-world full-duplex generality because the benchmark coverage is still narrow.
      **主张-证据矩阵:** 证据对能力和部署效率的支撑最为有力，对设计选择的支撑属于中等，对真实场景下全双工交互（full-duplex）的普适性支撑最弱，因为基准测试的覆盖范围仍然狭窄。
      claim_kind:: analyst_assessment
      evidence:: E9, E11, E13, E16, E17
        - C1: Supported mainly by method formulation and one streaming benchmark; the formulation is clear, but fully standardized full-duplex audio-visual evaluation is missing.
          C1：主要由方法本身的表述和一项流式基准测试来支撑；表述清晰，但缺少完全标准化的全双工音视频评测。
          claim_kind:: analyst_assessment
          evidence:: E3, E4, E13
        - C2: Supported by architecture details plus broad capability results; the causal link between compact token interfaces and retained capability is plausible but not isolated by a full architecture ablation.
          C2：由架构细节以及广泛的能力测试结果来支撑；紧凑的 token 接口与能力保持之间的因果联系是合理的，但没有通过完整的架构消融实验单独加以验证。
          claim_kind:: analyst_assessment
          evidence:: E5, E6, E11, E12
        - C3: Supported by direct design and speech-mode ablations; the tradeoff is explicit because dynamic TAIL is temporally motivated but not the best recognition-quality mode.
          C3：由直接的设计消融实验和语音模式消融实验来支撑；这里的权衡很明确，因为动态的 TAIL 是出于时间因素的考虑而设计的，但它并不是识别质量最好的模式。
          claim_kind:: analyst_assessment
          evidence:: E7, E9, E15
        - C4: Supported by many benchmark tables and efficiency measurements; support is table-based and lacks reported variance, so it is useful for recall but not a statistical dominance claim.
          C4：由大量基准测试表格和效率测量来支撑；这些支撑基于表格数据，且没有报告方差，因此可用于对结果的整体把握，但不能作为统计意义上的全面领先结论。
          claim_kind:: analyst_assessment
          evidence:: E11, E12, E13, E16
    - **Headline Results:** Headline results show a compact model that is unusually broad: strong vision-language and OCR scores, competitive speech understanding and generation, top scores on several omni-modal benchmarks, and much lower memory than Qwen3-Omni in the reported INT4 setup. These results support scale-efficiency as much as raw quality.
      **关键结果:** 核心结果显示，这是一个能力异常广泛的紧凑模型：视觉-语言和光学字符识别（OCR）得分很高，语音理解与生成具有竞争力，在多项全模态基准测试上得分领先，并且在所报告的 INT4 配置下内存占用远低于 Qwen3-Omni。这些结果既证明了原始质量，也同样证明了规模效率。
      evidence:: E11, E12, E13, E16
        - Vision-language: MiniCPM-o 4.5 is close to Gemini 2.5 Flash on OpenCompass and exceeds listed open baselines on several instruct-mode metrics, while lagging on some hard reasoning entries such as MMMU.
          视觉-语言方面：MiniCPM-o 4.5 在 OpenCompass 上接近 Gemini 2.5 Flash，并在若干指令模式指标上超过所列出的开源基线，但在 MMMU 等一些高难度推理项目上有所落后。
          evidence:: E11
        - Speech and omni-modal: the paper reports leading entries on selected speech QA/generation metrics and best results on five of seven simplex omni-modal benchmarks, plus a LiveSports-3K-CC win-rate lead.
          语音与全模态方面：论文报告在选定的语音问答/生成指标上取得领先，在七项单工全模态基准测试中的五项上取得最佳结果，并在 LiveSports-3K-CC 上取得胜率领先。
          evidence:: E12, E13
        - Efficiency: MiniCPM-o 4.5 fits the reported RTX 4090 settings where Qwen3-Omni BF16 runs out of memory, and INT4 reduces memory to 11 GB in both vLLM and llama.cpp-omni measurements.
          效率方面：MiniCPM-o 4.5 能够在所报告的 RTX 4090 配置下运行，而 Qwen3-Omni 的 BF16 版本在该配置下会内存不足；采用 INT4 后，在 vLLM 和 llama.cpp-omni 两种测量中，内存均降至 11 GB。
          evidence:: E16
    - **Ablations and Sensitivity:** The ablations are useful because they test the paper's own timing assumptions rather than only final benchmark scores. Their shared message is that the system works by balancing time pressure against model stability: too-short chunks, over-aggressive length rewards, or stricter temporal speech alignment can reduce quality.
      **消融与敏感性:** 这些消融实验很有价值，因为它们检验的是论文自身关于时间的假设，而不仅仅是最终的基准测试得分。它们共同传达的信息是：该系统的工作方式是在时间压力与模型稳定性之间取得平衡；过短的时间片、过于激进的长度奖励，或者更严格的时间对齐语音对齐，都会降低质量。
      claim_kind:: analyst_assessment
      evidence:: E9, E14, E15
        - Omni-Flow design: explicit boundaries and LS control beat implicit or LT variants, and the reported one-second chunk gives the best table balance.
          Omni-Flow 设计：明确的时间边界与 Listen-Speak 控制（LS）胜过隐式方案或 LT 变体，而论文所报告的一秒时间窗（time chunk）在整张表格上取得了最佳的平衡。
          evidence:: E9
        - Length reward: the smooth reward reduces thinking length less aggressively than Kimi K1.5-style reward while improving the benchmark average in the reported lightweight RL experiment.
          长度奖励：在论文报告的轻量级强化学习实验中，平滑奖励对思考长度的压缩不像 Kimi K1.5 式奖励那样激进，同时还提升了基准测试的平均得分。
          evidence:: E14
        - Speech mode: fixed-text interleaving wins CER/WER, while dynamic TAIL is justified as the full-duplex timing mode despite worse English WER.
          语音模式：固定文本交织在字符错误率（CER）和词错误率（WER）上占优；而动态的 Time-Aligned Interleaving（TAIL）尽管英文 WER 更差，但作为全双工交互（full-duplex）的时序模式仍有其合理性。
          evidence:: E15
    - **Reproducibility Gaps:** Model, code, data, and scripts are not specified as available in the supplied paper text; the paper mentions a web demo, a lightweight demo system, and llama.cpp-omni, but not enough release detail to reproduce training or every benchmark. Hardware is partially specified for inference, while training compute, data licenses, variance, and benchmark prompts are not reported.
      **可复现性缺口:** 在提供的论文文本里，没有说明模型、代码、数据和脚本是否公开；论文提到了一个网页演示、一个轻量级演示系统以及 llama.cpp-omni，但发布细节不足以复现训练过程或每一项基准测试。推理部分给出了部分硬件信息，而训练算力、数据许可、方差以及基准测试所用的提示词都没有报告。
      claim_kind:: analyst_assessment
      evidence:: E16, E17
- ## Technical Judgment
    - **What Holds Up:** The strongest part of the paper is the data representation: aligning environment input and assistant output on one clock is the right abstraction for breaking turn-taking without inventing a new backbone. The efficiency story also holds up better than most capability-only model reports because the paper gives memory, latency, throughput, and RTF measurements on named hardware.
      **站得住的结论:** 论文最强的部分是它的数据表示方式：把环境输入和助手输出对齐到同一个时钟上，是打破轮流对话（turn-taking）的正确抽象，而且无需发明新的主干网络。效率方面的论述也比大多数只谈能力的模型报告更站得住脚，因为论文在指名的硬件上给出了内存、延迟、吞吐和实时率（RTF）的测量结果。
      claim_kind:: analyst_assessment
      evidence:: E3, E4, E9, E16
    - **Where It May Fail:** The main failure boundary is long, noisy, truly bidirectional real-world use: the quantitative full-duplex test is vision-only, TAIL trades away speech quality, and the authors acknowledge robustness, speech instability, code-mixing, latency, missing fragments, and simple proactive behavior. Benefits may diminish when network conditions are unstable, when speech timing is harder than the benchmark captures, or when proactive behavior needs planning rather than local scene reactions.
      **可能失效之处:** 主要的失效边界在于长时间、嘈杂、真正双向的真实世界使用场景：定量的全双工（full-duplex）测试只覆盖视觉，Time-Aligned Interleaving（TAIL）以牺牲语音质量为代价，作者也承认存在鲁棒性、语音不稳定、代码混合（code-mixing）、延迟、片段缺失以及主动行为过于简单等问题。当网络条件不稳定、当语音时序比基准测试所反映的更难处理、或者当主动行为需要规划而不仅仅是对局部场景做出反应时，这些好处可能会减弱。
      claim_kind:: analyst_assessment
      evidence:: E13, E15, E17
    - **Relation to Other Work:** Compared with Qwen3-Omni, Kimi-Audio, CosyVoice2, LiveCC, and StreamingVLM as presented here, MiniCPM-o 4.5 is positioned less as a specialist speech or video model and more as an integrated real-time interaction stack. The technical difference is the shared temporal stream plus deployable runtime, not just better scores on the same offline multimodal benchmarks.
      **与已有工作的关系:** 与本文所呈现的 Qwen3-Omni、Kimi-Audio、CosyVoice2、LiveCC 和 StreamingVLM 相比，MiniCPM-o 4.5 与其说是一个专精语音或视频的模型，不如说是一套集成的实时交互系统栈。技术上的区别在于共享的时间流加上可部署的运行时，而不仅仅是在相同的离线多模态基准上取得更好的分数。
      claim_kind:: analyst_assessment
      evidence:: E2, E7, E11, E12, E13, E16
    - **Transferable Lesson:** When an AI system must act while sensing, first make time an explicit data dimension, then separate control decisions from content decisions. This pattern transfers beyond speech assistants: streaming agents, robotics interfaces, and live monitoring systems can often improve by aligning observation, action, and silence decisions before adding model capacity.
      **可迁移启发:** 当一个 AI 系统必须在感知的同时采取行动时，首先要把时间作为一个显式的数据维度，然后再把控制决策与内容决策分开。这种模式的适用范围超出语音助手：流式智能体、机器人接口和实时监控系统往往可以通过先对齐观测、行动和保持沉默这些决策，再增加模型容量，来获得改进。
      claim_kind:: analyst_assessment
      evidence:: E3, E4, E9
- ## Glossary
  collapsed:: true
    - multimodal large language model: A language-model backbone connected to encoders or decoders for non-text signals such as images, video, audio, and speech.
      多模态大语言模型（multimodal large language model，MLLM）：一个语言模型主干，连接了用于处理图像、视频、音频和语音等非文本信号的编码器或解码器。
    - full-duplex interaction: An interaction mode where the assistant can receive new input and produce output at the same time, rather than alternating turns.
      全双工交互（full-duplex interaction）：一种交互模式，助手可以在接收新输入的同时产生输出，而不是轮流交替进行。
    - token: A small unit the model reads or writes; in this paper tokens can represent text, visual features, audio features, or speech-code units.
      token（词元）：模型读取或写出的小单位；在本文中，token 可以表示文本、视觉特征、音频特征或语音编码单元。
    - Omni-Flow: The paper's framework for placing visual input, audio input, and assistant output on a shared time axis.
      Omni-Flow：本文提出的框架，用于把视觉输入、音频输入和助手的输出放在一条共享的时间轴上。
    - time chunk: A short interval of the live interaction; Omni-Flow groups the visual, audio, and output tokens belonging to the same interval.
      time chunk（时间块）：实时交互中的一小段时间间隔；Omni-Flow 会把属于同一间隔的视觉、音频和输出 token 归为一组。
    - Listen-Speak control: A control formulation where the model first decides whether to listen or speak, then generates content if it chooses to speak.
      Listen-Speak control（听说控制）：一种控制方式，模型先决定是「听」还是「说」，如果选择「说」再生成具体内容。
    - Time-Aligned Interleaving: The paper's speech-generation strategy that adapts how much text to generate so speech playback stays close to the current time boundary.
      Time-Aligned Interleaving（时间对齐交错）：本文的语音生成策略，会自适应调整生成多少文本，使语音的播放时间尽量贴近当前的时间边界。
    - S3 speech token: A discrete speech-code unit generated by the speech-token decoder before waveform synthesis.
      S3 speech token（S3 语音 token）：在合成波形之前，由语音 token 解码器生成的离散语音编码单元。
    - flow-matching decoder: A neural audio generator that converts speech tokens into waveform audio in a streaming way.
      flow-matching decoder（流匹配解码器）：一种神经音频生成器，以流式方式把语音 token 转换成波形音频。
    - real-time factor: An inference-speed measure for audio generation; lower values mean the system generates faster than playback time.
      real-time factor（实时因子）：衡量音频生成推理速度的指标；数值越低，表示系统的生成速度快于播放时间。
    - Group Relative Policy Optimization: The reinforcement-learning method the paper uses to improve reasoning and instruction following with accuracy and auxiliary rewards.
      Group Relative Policy Optimization（分组相对策略优化）：本文使用的强化学习方法，借助准确率奖励和辅助奖励来提升推理能力和指令遵循能力。
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/metadata | Title and Abstract | high
      locator:: title block and abstract
      quote:: The paper is titled MiniCPM-o 4.5: Towards Real-Time Full-Duplex Omni-Modal Interaction, appears as arXiv:2604.27393v1 in cs.CL on 30 Apr 2026, and presents MiniCPM-o 4.5 with a total of 9B parameters.
    - **E2:** problem/paper_statement | 1 Introduction | high
      locator:: Introduction, paragraphs 1-2 and Figure 3
      quote:: The authors argue that modality coverage and latency are no longer the only bottlenecks. Existing models still alternate perception and response, cannot update during generation, and remain request-driven rather than context-driven.
    - **E3:** method/paper_statement | 3 Omni-Flow | high
      locator:: Section 3 opening
      quote:: Omni-Flow coordinates omni-modal input and output streams on a shared temporal axis. It divides continuous interaction into fine-grained time windows and processes newly arrived signals while producing the next output.
    - **E4:** algorithm/paper_statement | 3.1 Time-Aligned Streams and 3.2 Unified Serialization | medium
      locator:: Sections 3.1-3.2
      quote:: The framework identifies env-visual, env-audio, and out-stream. For each chunk, visual tokens, audio tokens, and output tokens are grouped, with a special listen token when the assistant should produce no content.
    - **E5:** system_design/implementation_detail | 2 End-to-End Omni-Modal Architecture | high
      locator:: Section 2 opening and Figure 4
      quote:: The model combines streaming visual and audio encoders, a Qwen3-8B language backbone, an interleaved speech-token decoder, and a streaming flow-matching waveform decoder, with learnable components connected through token-level hidden states.
    - **E6:** optimization/implementation_detail | 2 End-to-End Omni-Modal Architecture | high
      locator:: Visual Encoding, Audio Encoding, Text Decoding
      quote:: The visual path compresses each encoded slice from 1024 tokens to 64 tokens. The audio path produces 50 feature tokens per second then compresses to 10 audio tokens per second. The backbone only emits text-speed tokens.
    - **E7:** algorithm/paper_statement | 3.4 Time-Aligned Interleaving for Timely Speech Generation | high
      locator:: Section 3.4 and Figure 5
      quote:: Time-Aligned Interleaving adaptively chooses how much text to generate so speech playback approaches the current chunk boundary. It can generate fewer tokens after earlier delay and defers a bounded look-ahead for pronunciation and prosody.
    - **E8:** experiment_setup/paper_statement | 4 Data and 5 Training | high
      locator:: Sections 4.3, 5.1-5.4
      quote:: Full-duplex samples contain visual input, audio input, output text, and output speech tagged with time indices. Training proceeds through speech pretraining, joint pretraining, supervised fine-tuning, and reinforcement learning.
    - **E9:** ablation/ablation | 3.3 Design Tradeoffs | medium
      locator:: Table 1 and surrounding analysis
      quote:: The design ablation varies chunk size, explicit boundaries, and listen-speak versus listen-text control. The authors report 1.0 s chunks, explicit boundaries, and separated listen-speak control as the best stability-responsiveness balance.
    - **E10:** experiment_setup/paper_statement | 6.1 Modalities and Domains | high
      locator:: Section 6.1
      quote:: Evaluation covers vision-language understanding, speech understanding and generation, text capability, omni-modal streaming interaction, and full-duplex streaming. Benchmarks span STEM reasoning, OCR, hallucination, video, ASR, speech QA, and audio-visual tasks.
    - **E11:** result/experiment_result | 6.2 Vision-Language Results | medium
      locator:: Tables 2-3
      quote:: In instruct mode MiniCPM-o 4.5 reports OpenCompass 77.6, MMBench EN 87.6, MathVista 80.1, HallusionBench 63.2, Mantis-Eval 79.7, and several document/OCR scores competitive with larger or proprietary baselines.
    - **E12:** result/experiment_result | 6.3 Speech Results | medium
      locator:: Tables 4-5
      quote:: On speech tasks the model leads selected semantic benchmarks such as CoVoST 2 en-to-zh, MELD, VoiceBench AlpacaEval, and Speech TriviaQA; for generation it reports lowest SeedTTS ZH CER and EN WER among listed baselines.
    - **E13:** result/experiment_result | 6.5 Omni-modal and Streaming Results | medium
      locator:: Tables 7-8
      quote:: MiniCPM-o 4.5 reports best results on five of seven simplex omni-modal benchmarks. On LiveSports-3K-CC, an audio-free full-duplex benchmark, it scores 54.4 versus 41.5 for LiveCC and 45.6 for StreamingVLM.
    - **E14:** ablation/ablation | 6.6 Analysis | medium
      locator:: Table 9 and Figure 6
      quote:: The smooth length reward reports a thinking benchmark average of 74.3 with 35.3 percent length reduction, compared with 73.5 for no length reward and 73.0 with the more aggressive Kimi K1.5-style reward.
    - **E15:** ablation/ablation | 6.6 Analysis | medium
      locator:: Table 10
      quote:: The speech-mode comparison shows fixed-text interleaving gives best SeedTTS CER/WER, while dynamic Time-Aligned Interleaving has worse EN WER but is presented as the mode designed for temporally aligned full-duplex interaction.
    - **E16:** result/experiment_result | 7 Efficient Real-Time Inference | medium
      locator:: Tables 11-12
      quote:: On a single RTX 4090 with vLLM, MiniCPM-o 4.5 INT4 reports 212.3 tokens/s, 0.58 s first-token latency, and 11 GB memory. llama.cpp-omni INT4 reports real-time factor 0.21 with 11 GB memory.
    - **E17:** limitation/limitation | 8 Conclusion | high
      locator:: Limitations paragraph
      quote:: The authors call the work an early exploration, note that long dynamic real-world robustness needs more validation, and report occasional streaming speech instability, English-Chinese mixing, web-demo latency, missing fragments, and simple proactive behavior.
    - **E18:** implementation/implementation_detail | Appendix A Model Configuration | high
      locator:: Table 13
      quote:: The appendix lists 9.34B learnable parameters in bfloat16, including a SigLIP visual encoder, visual resampler, Whisper Medium audio encoder, Qwen3-8B backbone, projector layers, and a speech-token decoder.
