- **Title:** Omni-DuplexEval: Evaluating Real-time Duplex Omni-modal Interaction
  **标题:** Omni-DuplexEval：评测实时双工全模态交互
- **Summary:** Omni-DuplexEval turns real-time multimodal interaction into an evaluable benchmark by pairing continuous description and proactive reminder tasks with timestamp-aware judging, exposing that current duplex models still miss both sustained content coverage and response timing.
  **一句话总结:** Omni-DuplexEval 把实时多模态交互变成一个可评测的基准：它将「持续描述」和「主动提醒」两类任务与「时间戳感知」的评判方法结合起来，揭示出当前双工模型在持续内容覆盖和响应时机这两方面都仍有欠缺。
- **Paper Type:** benchmark
  **论文类型:** 基准（benchmark）
- **Venue:** arXiv preprint 2026
  **发表:** arXiv 预印本 2026
- **Authors:** Chaoqun He, Mingyang Xiang, Yingjing Xu, Bokai Xu, Junbo Cui, Jie Zhou, Yuan Yao, Lijie Wen; Tsinghua University, Tongji University, ModelBest Inc.
  **作者:** Chaoqun He、Mingyang Xiang、Yingjing Xu、Bokai Xu、Junbo Cui、Jie Zhou、Yuan Yao、Lijie Wen；清华大学、同济大学、ModelBest Inc.
- **Keywords:** real-time duplex interaction, multimodal large language models, streaming video understanding, omni-modal interaction, LLM-as-a-Judge, temporal alignment
  **关键词:** 实时双工交互、多模态大语言模型、流式视频理解、全模态交互、以大语言模型作为评判者（LLM-as-a-Judge）、时间对齐
- ## Orientation
    - **Background:** This paper sits in video-and-audio AI evaluation. A real-time assistant sees a stream bit by bit, so its answer is judged not only by what it says but by whether it says it while the relevant moment is happening.
      **背景:** 本文属于视频与音频人工智能评测领域。实时助手是逐段接收数据流的，因此评判它的答案时，不仅要看它说了什么，还要看它是否在相关时刻正在发生时把话说出来。
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A model can look smart after watching a full video, yet still be a poor live helper if it waits too long, talks at the wrong time, or misses the event the user asked about.
      **通俗问题:** 一个模型在看完整段视频后可能显得很聪明，但如果它等得太久、在错误的时间开口，或者错过了用户询问的事件，它仍然算不上一个好的实时助手。
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** The system must keep watching and listening, remember the user's goal, decide whether the current moment matters, and speak without having future context.
      **为何困难:** 系统必须持续地观看和聆听，记住用户的目标，判断当前时刻是否重要，并在没有未来上下文的情况下开口说话。
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Evaluate live behavior directly by checking both continuous descriptions and event-triggered reminders against the video timeline.
      **一句话核心思路:** 一句话概括核心思路：直接评估实时行为，方法是对照视频时间线，同时检验连续描述和由事件触发的提醒。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a benchmark paper for multimodal large language models (MLLMs), where the missing evaluation gap is not final video understanding but whether a system can speak at the right moments while video and audio are still arriving.
      **阅读价值:** 把它当作一篇面向多模态大语言模型（Multimodal Large Language Model，MLLM）的基准论文来读。它要填补的评测空白不是对视频的最终理解，而是在视频和音频还在持续到来的过程中，系统能否在恰当的时刻开口说话。
      claim_kind:: analyst_assessment
      evidence:: E2, E15
    - **One-Sentence Contribution:** Omni-DuplexEval improves evaluation of real-time video-and-audio assistants by scoring open-ended streaming responses against both their content and their timestamps.
      **一句话贡献:** Omni-DuplexEval 改进了对实时视频与音频助手的评测：它同时依据流式响应的内容和时间戳来打分。
      evidence:: E1, E6
    - **Mental Model:** Imagine judging a live tour guide: it is not enough that the guide eventually names everything correctly; each sentence must match what the viewer can see or hear at that moment, and reminders must fire when the requested event happens.
      **记忆模型:** 想象一下评判一位现场导游：仅仅让导游最终把所有东西的名字都说对是不够的；每一句话都必须与观众此刻能看到或听到的内容相符，而且提醒必须在被要求关注的事件发生时才触发。
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is the benchmark run showing a large human-model gap, plus diagnostic metrics that separate local timing from global content coverage.
      **最佳证据:** 最有力的证据是基准测试结果显示人类与模型之间存在巨大差距，此外还有能把局部时机与全局内容覆盖分开衡量的诊断性指标。
      evidence:: E10, E11, E12
        - Supports C3: Omni-DuplexEval full benchmark; Human-Duplex as real-time human baseline; average score higher is better; MiniCPM-o 4.5 reaches 39.6 versus 81.8 for Human-Duplex; supported, but no variance or repeat count is reported.
          支持 C3：使用 Omni-DuplexEval 完整基准；以 Human-Duplex 作为实时人类基线；平均分越高越好；MiniCPM-o 4.5 得 39.6，而 Human-Duplex 得 81.8；结论成立，但文中没有报告方差或重复实验次数。
          evidence:: E10
        - Supports C4: Real-Time Description metric split; model content and temporal scores compared with human scores; MiniCPM-o 4.5 has 79.9 temporal sensitivity but 38.3 content consistency; supported as a diagnostic gap, with judge-dependence caveat.
          支持 C4：对实时描述（Real-Time Description，RTD）指标进行拆分；将模型的内容得分与时间得分和人类得分作对比；MiniCPM-o 4.5 的时间敏感度（Temporal Sensitivity）为 79.9，但内容一致性（Content Consistency）仅为 38.3；作为一种诊断性的差距，结论成立，但需注意其依赖评判模型这一点。
          evidence:: E11
        - Supports C3: Proactive Reminder error analysis; error types are No Answer, Partially Correct, and Wrong; MiniCPM-o 4.5 has 49.2% No Answer and MMDuet2 has 75.8% No Answer; supported, but the cause is inferred from their outputs rather than controlled intervention.
          支持 C3：对主动提醒（Proactive Reminder，PR）做错误分析；错误类型分为「无答复」「部分正确」和「错误」三种；MiniCPM-o 4.5 有 49.2% 属于「无答复」，MMDuet2 有 75.8% 属于「无答复」；结论成立，但原因是从它们的输出中推断出来的，而非通过受控干预实验得到。
          evidence:: E12
    - **Main Caveat:** The benchmark is most trustworthy as a short-interaction diagnostic: the paper itself limits claims about long-term conversation, judge bias, and breadth across real-time public systems.
      **主要边界:** 最主要的注意事项：该基准作为一种针对短时交互的诊断工具最为可信；论文本身对以下方面的结论有所保留：长期对话、评判模型偏差，以及覆盖各类实时公开系统的广度。
      claim_kind:: analyst_assessment
      evidence:: E14
- ## Argument Map
    - **Problem and Stakes:** The paper argues that offline video benchmarks miss real-time duplex interaction, meaning a model's ability to process evolving inputs while producing responses at appropriate moments. This matters because practical assistants must coordinate perception, user intent, and speaking time rather than answer after the full clip is known.
      **问题与重要性:** 论文认为，离线视频基准无法衡量实时的双工交互（duplex interaction），也就是模型在处理不断变化的输入的同时，在恰当的时刻给出响应的能力。这一点很重要，因为实用的助手必须协调感知、用户意图和开口说话的时机，而不是等到整段视频都已知晓之后才作答。
      evidence:: E2, E1
    - **Prior Gap:** Prior benchmarks cover offline video QA, streaming inputs, open-ended answers, or proactive event detection in pieces, but the paper claims they do not jointly test open-ended streaming response quality, proactiveness, and temporal alignment. The gap is therefore an evaluation gap, not a new model architecture gap.
      **已有方法缺口:** 以往的基准分别覆盖了离线视频问答、流式输入、开放式作答，或主动的事件检测，但论文指出，它们并没有联合起来同时检验开放式流式响应的质量、主动性和时间对齐。因此，这里存在的是一个评测上的空白，而不是一个新的模型架构上的空白。
      evidence:: E15, E2
    - **Key Insight:** The key insight is to split real-time duplex behavior into two observable patterns: continuous narration that must track a changing stream, and event-triggered reminders that must fire when the requested condition occurs. The evaluation then scores both semantic content and timing instead of treating a final answer as sufficient.
      **关键洞见:** 核心洞见是把实时双工行为拆成两种可观测的模式：一种是必须跟踪不断变化的输入流的持续叙述，另一种是必须在所请求的条件出现时才触发的事件触发提醒。评测据此同时对语义内容和时机打分，而不是把给出最终答案就当作足够好。
      evidence:: E1, E6, E7
    - **Claims:** The paper's claim chain is that a purpose-built benchmark can expose failures hidden by final-answer video evaluation and can diagnose whether failures come from content, timing, or event-triggering.
      **核心主张:** 本文的论证链条是：一个专门构建的基准测试能够暴露那些被「只看最终答案」的视频评测方式所掩盖的失败，并且能诊断出失败到底源自内容、时机还是事件触发。
      evidence:: E1, E10
        - C1: Omni-DuplexEval covers real-time duplex interaction through 660 open-ended video-and-audio samples, two scenarios, and nine sub-tasks with human timestamp annotations.
          C1：Omni-DuplexEval 通过 660 个开放式的视频加音频样本、两种场景以及九个子任务（配有人工标注的时间戳）覆盖了实时双工交互。
          evidence:: E1, E5, E15
        - C2: Its automatic evaluation can score both what the model says and when it says it by combining global content consistency, sentence-level temporal sensitivity, and event-window reminder judgment.
          C2：它的自动评测能够同时评估模型「说了什么」和「什么时候说」，方法是把全局内容一致性、句子级的时间敏感度以及事件窗口内的提醒判定结合起来。
          evidence:: E6, E7, E8
        - C3: Current duplex multimodal models remain far below human real-time performance, especially on Proactive Reminder where deciding when to answer is the dominant failure.
          C3：当前的双工多模态模型仍然远远落后于人类的实时表现，尤其是在「主动提醒（Proactive Reminder）」上，判断何时该回答是最主要的失败来源。
          evidence:: E10, E12
        - C4: In Real-Time Description, models show a timeliness-coverage tradeoff: locally timed sentences can still be too sparse to preserve coherent, holistic video understanding.
          C4：在「实时描述（Real-Time Description）」中，模型表现出时效性与覆盖度之间的权衡：即便每句话在局部时间上都对得上，句子仍可能过于稀疏，以至于无法保持连贯、整体的视频理解。
          evidence:: E11
- ## Mechanism and Design
    - **Core Mechanism:** Omni-DuplexEval defines two task families: Real-Time Description (RTD), where the model continuously describes a requested aspect of a changing video, and Proactive Reminder (PR), where the model waits for a specified event or correction opportunity before responding. This makes the benchmark test both always-on tracking and trigger-based decision making.
      **核心机制:** Omni-DuplexEval 定义了两大任务族：一是实时描述（Real-Time Description，RTD），模型要对一段不断变化的视频中被要求关注的某个方面进行持续描述；二是主动提醒（Proactive Reminder，PR），模型要等到某个指定的事件或纠正时机出现后才做出响应。这使得该基准既能测试「常开式」的持续跟踪能力，也能测试基于触发条件的决策能力。
      evidence:: E3, E4
    - **Data / Control Flow:** A sample starts with a user instruction, then the model receives streaming visual and audio input and emits timestamped text. RTD sends each sentence into content and timing judges, while PR extracts model text in a fixed window after each annotated event and judges whether the reminder or correction succeeded.
      **数据/控制流:** 一个样本从用户指令开始，随后模型接收流式的视觉和音频输入，并输出带时间戳的文本。对于 RTD，模型的每一句话都会送入内容判定器和时机判定器；对于 PR，则在每个被标注的事件之后的固定窗口内提取模型文本，并判定其提醒或纠正是否成功。
      evidence:: E5, E6, E7
    - **Design Decisions:** The design choices mostly convert qualitative live interaction into bounded, judgeable units: task taxonomy, human timestamp annotations, sentence-level timing, and strict event success. These choices make the benchmark practical, but they also bind it to short clips and to the reliability of judge prompts.
      **设计决策:** 这些设计选择基本上都是把定性的实时交互转化为有边界、可判定的单元：任务分类体系、人工标注的时间戳、句子级的时机判定，以及严格的事件成功判定。这些选择让基准变得可操作，但也把它绑定在了短视频片段上，并依赖于判定提示词（judge prompts）的可靠性。
      evidence:: E3, E4, E6, E7, E14
        - Need: final-answer multiple choice hides timing and free-form response quality; choice: use open-ended questions with human-curated timestamp annotations; closest alternative: offline or discrete QA benchmarks; tradeoff: richer behavior but harder automatic judging.
          需求：只看最终答案的多项选择题会掩盖时机以及自由形式回答的质量；选择：采用开放式问题，并配以人工整理的时间戳标注；最接近的替代方案：离线的或离散的问答类基准；权衡：能考察更丰富的行为，但自动判定更困难。
          evidence:: E5, E15
        - Need: live systems alternate between narration and waiting; choice: split RTD from PR; closest alternative: one generic streaming QA task; tradeoff: clearer diagnosis, but only these two interaction patterns are covered.
          需求：实时系统会在「叙述」和「等待」两种状态之间交替；选择：把实时描述（Real-Time Description，RTD）和主动提醒（Proactive Reminder，PR）拆分开；最接近的替代方案：合并成一个通用的流式问答任务；权衡：拆分后诊断更清晰，但只覆盖了这两种交互模式。
          evidence:: E3, E4
        - Need: a good live answer may lag perception slightly; choice: Temporal Sensitivity, a metric for whether a sentence matches its local time window, uses multiple shifted candidate windows and takes the best judge score; tradeoff: tolerant to small latency but dependent on window design.
          需求：一个好的实时回答可能会比感知稍微滞后一点；选择：采用时间敏感度（Temporal Sensitivity），这是一个用来衡量某句话是否与其所处的局部时间窗口相匹配的指标，它会使用多个经过平移的候选窗口，并取其中评判分数最高的那个；权衡：这种做法能容忍小幅延迟，但依赖于窗口的设计方式。
          evidence:: E6, E8
    - **Implementation Surface:** The paper reports a project URL, native duplex inference protocols for evaluated models, and single-GPU evaluation on NVIDIA A100 hardware; it also gives model-specific streaming details such as chunked audio/video processing and key-value cache (KV cache), the saved attention state reused across turns. The implementation surface is enough to understand benchmark operation, but judge-service versions, seeds, and end-to-end scripts are not fully specified in the text.
      **实现边界:** 论文给出了一个项目网址、所评估模型的原生双工推理协议，以及在 NVIDIA A100 硬件上的单卡评测；论文还提供了各模型的流式处理细节，例如分块的音频/视频处理，以及键值缓存（KV cache）——即在多轮对话之间复用的、已保存的注意力状态。这些实现层面的信息足以让人理解基准测试的运行方式，但文中没有完整说明评判服务的版本、随机种子以及端到端的脚本。
      evidence:: E9, E13, E14
- ## Evaluation and Evidence
    - **Setup:** The experiments evaluate four streaming or duplex multimodal baselines, LiveCC, StreamingVLM, MMDuet2, and MiniCPM-o 4.5, using each model's native real-time inference protocol on one NVIDIA A100 GPU. Human-Duplex and Human-Offline provide real-time and offline human reference points rather than trained model baselines.
      **实验设置:** 实验评测了四个流式或双工多模态基线模型：LiveCC、StreamingVLM、MMDuet2 和 MiniCPM-o 4.5，每个模型都在一块 NVIDIA A100 GPU 上使用其原生的实时推理协议运行。Human-Duplex 和 Human-Offline 分别提供实时和离线的人类参考水平，它们不是经过训练的模型基线。
      evidence:: E9, E13
    - **Claim-Evidence Matrix:** The evidence is strongest for benchmark construction and diagnostic failure patterns, and weaker for broad generalization because the model set is small and the evaluation is judge-based.
      **主张-证据矩阵:** 证据在基准测试的构建方式和诊断出的失败模式上最为充分，而在广泛泛化能力上较弱，因为参与评测的模型数量较少，且评测本身基于评判打分。
      claim_kind:: analyst_assessment
      evidence:: E5, E8, E10, E14
        - Supports C1: the dataset includes 660 short videos, two scenarios, nine sub-tasks, open-ended questions, and human-curated temporal annotations.
          支持论点 C1：数据集包含 660 段短视频、两种场景、九个子任务、开放式问题，以及人工精心整理的时间标注。
          evidence:: E1, E5
        - Supports C2: the paper defines content, timing, and event-window judges, then calibrates Content Consistency above 0.9 Spearman correlation, a rank-correlation measure, and Temporal Sensitivity near 0.8.
          支持论点 C2：论文定义了内容评判器、时机评判器和事件窗口评判器，随后进行校准，使内容一致性（Content Consistency）的 Spearman 相关系数（Spearman correlation，一种基于排名的相关性度量）高于 0.9，时间敏感度接近 0.8。
          evidence:: E6, E7, E8
        - Supports C3 and C4: Table 2 shows the overall human-model gap, Table 3 separates temporal and content scores, and Table 4 attributes PR failures to no-answer or wrong-answer modes.
          支持论点 C3 和 C4：表 2 展示了人类与模型之间的总体差距，表 3 把时间分数和内容分数分开列出，表 4 则把 PR 场景的失败归因于「不作答」或「答错」两种模式。
          evidence:: E10, E11, E12
    - **Headline Results:** MiniCPM-o 4.5 is the best model overall at 39.6, still far below Human-Duplex at 81.8, and its PR average is only 20.0 despite stronger RTD performance. The reported results support the paper's central diagnosis, but they lack uncertainty intervals or repeated-run statistics.
      **关键结果:** MiniCPM-o 4.5 是总体表现最好的模型，得分为 39.6，但仍远低于 Human-Duplex 的 81.8；尽管它在 RTD 上表现更强，其 PR 场景的平均分却只有 20.0。所报告的结果支持了论文的核心诊断，但缺少不确定性区间或多次重复运行的统计数据。
      evidence:: E10, E11, E12
        - C3 result: full benchmark; baseline Human-Duplex; score higher is better; MiniCPM-o 4.5 gets 39.6 versus 81.8; no uncertainty reported.
          C3 的结果：完整基准测试；基线为 Human-Duplex；分数越高越好；MiniCPM-o 4.5 得到 39.6，对比 81.8；未报告不确定性。
          evidence:: E10
        - C4 result: RTD metric split; MiniCPM-o 4.5 gets 79.9 Temporal Sensitivity but 38.3 Content Consistency, while MMDuet2 gets 79.2 and 37.6; timing can look good while global content remains weak.
          C4 结果：RTD（Real-Time Description，实时描述）指标出现分化。MiniCPM-o 4.5 的时间敏感度（Temporal Sensitivity）得分为 79.9，但内容一致性（Content Consistency）只有 38.3；MMDuet2 则分别为 79.2 和 37.6。这说明时间上的表现可能看起来不错，而整体内容的质量仍然偏弱。
          evidence:: E11
        - C3 result: PR error table; MMDuet2 has 75.8% No Answer and MiniCPM-o 4.5 has 49.2% No Answer, while LiveCC and StreamingVLM are dominated by Wrong outputs; support for event-triggering weakness.
          C3 结果：PR（Proactive Reminder，主动提醒）错误统计表显示，MMDuet2 有 75.8% 的「无回答」（No Answer），MiniCPM-o 4.5 有 49.2% 的「无回答」，而 LiveCC 和 StreamingVLM 的错误主要是「回答错误」（Wrong）。这些数据支持了模型在事件触发方面较弱的判断。
          evidence:: E12
    - **Ablations and Sensitivity:** The paper reports evaluator-design sensitivity rather than model ablations: Content Consistency works best with two ground-truth references and low frame sampling, while Temporal Sensitivity improves through four-window sampling, sentence-level units, refined prompts, and an irrelevant-sentence penalty. Not applicable: no controlled ablation of model architectures or training choices is reported.
      **消融与敏感性:** 论文报告的是评测器设计的敏感性分析，而非模型的消融实验：内容一致性（Content Consistency）在使用两条标准参考答案且低帧采样时表现最好，而时间敏感度（Temporal Sensitivity）则通过四窗口采样、以句子为单位、优化提示词以及对无关句子的惩罚而得到提升。不适用：论文没有报告针对模型架构或训练选择的受控消融实验。
      evidence:: E8
    - **Reproducibility Gaps:** The paper gives a project URL, baseline identities, hardware class, and several inference settings, but the text does not fully report seeds, repeated runs, judge model version stability, dataset access details, or scripts sufficient to reproduce every number from the paper alone. The scarcity of public real-time multimodal systems also narrows the external validity of the benchmark comparison.
      **可复现性缺口:** 论文给出了项目网址、基线模型的具体名称、硬件类别以及若干推理设置，但正文没有完整报告随机种子、重复运行结果、评判模型版本的稳定性、数据集获取细节，也没有提供仅凭论文本身就足以复现每一个数字的脚本。此外，公开的实时多模态系统本就稀少，这也缩小了本基准对比结果的外部有效性。
      claim_kind:: analyst_assessment
      evidence:: E9, E13, E14
- ## Technical Judgment
    - **What Holds Up:** The most durable contribution is the decomposition of live multimodal behavior into timestamped units that can be audited separately for global content, local timing, and event-trigger success. The benchmark construction and judge calibration make the paper more useful than a single aggregate leaderboard, even though the judge remains an imperfect proxy.
      **站得住的结论:** 最经得起时间考验的贡献，是把实时多模态行为分解为带时间戳的单元，从而能分别审查整体内容、局部时间以及事件触发的成功率。基准构建和评判校准让这篇论文比单一的综合排行榜更有用，尽管评判器仍然是一个并不完美的替代指标。
      claim_kind:: analyst_assessment
      evidence:: E5, E6, E7, E8
    - **Where It May Fail:** The conclusions may weaken for longer conversations, memory-heavy tasks, richer interaction styles, or deployments where automatic judge bias matters more than benchmark comparability. Model rankings are also fragile because the evaluated public duplex model set is small and no statistical uncertainty is reported.
      **可能失效之处:** 对于更长的对话、依赖记忆的任务、更丰富的交互方式，或者那些自动评判偏差比基准可比性更重要的部署场景，本文的结论可能会变弱。模型排名也比较脆弱，因为被评测的公开双工（duplex）模型集合很小，而且论文没有报告统计上的不确定性。
      claim_kind:: analyst_assessment
      evidence:: E10, E14
    - **Relation to Other Work:** Against offline video benchmarks, Omni-DuplexEval adds streaming and temporal alignment; against streaming QA benchmarks, it emphasizes open-ended continuous output; against proactive video benchmarks, it adds fine-grained response timing and content checking. The paper positions itself as a unifying evaluation surface rather than as a replacement for long-video comprehension, hallucination, or spoken-dialogue turn-taking benchmarks.
      **与已有工作的关系:** 与离线视频基准相比，Omni-DuplexEval 增加了流式处理和时间对齐；与流式问答基准相比，它强调开放式的连续输出；与主动式视频基准相比，它增加了细粒度的响应时间和内容检查。论文把自己定位为一个统一的评测界面，而不是要取代长视频理解、幻觉检测或口语对话轮流发言等基准。
      evidence:: E15, E2
    - **Transferable Lesson:** For real-time AI systems, evaluate behavior as a time-indexed policy rather than a final answer: attach timestamps to outputs, score local timing and global content separately, and make event-triggered tasks require all target events to be handled. This pattern transfers to live assistants, robotics narration, monitoring alerts, and interactive accessibility tools.
      **可迁移启发:** 对于实时 AI 系统，应把行为当作一个按时间索引的策略来评测，而不是只看最终答案：给输出附上时间戳，分别为局部时间和整体内容打分，并让事件触发类任务要求处理所有目标事件。这一模式可以迁移到实时助手、机器人解说、监控告警以及交互式无障碍工具等场景。
      claim_kind:: analyst_assessment
      evidence:: E6, E7
- ## Glossary
  collapsed:: true
    - Multimodal Large Language Model: A language-model-centered system that can process non-text inputs such as images, video, and audio alongside text.
      多模态大语言模型（Multimodal Large Language Model，MLLM）：一种以语言模型为核心的系统，除了文本之外，还能处理图像、视频、音频等非文本输入。
    - real-time duplex interaction: Interaction where the model keeps receiving streaming inputs and can respond during the stream instead of after all input is complete.
      实时双工交互（real-time duplex interaction）：一种交互方式，模型持续接收流式输入，并且可以在输入流进行的过程中就作出响应，而不是等到全部输入结束之后才响应。
    - omni-modal: A model or task setting that combines multiple modalities, especially visual and audio signals in this paper.
      omni-modal（全模态）：一种结合多种模态的模型或任务设定，本文中特指同时处理视觉与音频信号。
    - Real-Time Description: The benchmark scenario where the model continuously describes a requested aspect of a changing video as it unfolds.
      Real-Time Description（实时描述）：一种基准测试场景，模型在视频不断变化、逐步展开时，持续描述用户所要求关注的某个方面。
    - Proactive Reminder: The benchmark scenario where the model monitors the stream and responds only when a user-specified event or correction condition is met.
      Proactive Reminder（主动提醒）：一种基准测试场景，模型持续监测输入流，只有在满足用户指定的事件或纠正条件时才做出响应。
    - Content Consistency: A global semantic correctness score for whether the model's response matches the instruction and the video-audio content.
      Content Consistency（内容一致性）：一个全局语义正确性评分，用于衡量模型的响应是否与指令以及视频音频内容相符。
    - Temporal Sensitivity: A timing score for whether each substantive sentence matches the video-audio segment around its timestamp.
      Temporal Sensitivity（时间敏感度）：一个时机评分，用于衡量每一句有实质内容的句子是否与其时间戳附近的视频音频片段相匹配。
    - LLM-as-a-Judge: An evaluation method where a large language model scores or classifies another model's output using a prompt and reference context.
      LLM-as-a-Judge（大语言模型充当评判者）：一种评估方法，让大语言模型借助一段提示词和参考上下文，对另一个模型的输出进行打分或分类。
    - event window: For Proactive Reminder, the fixed time span after an annotated event during which model output is collected for judging.
      event window（事件窗口）：在主动提醒（Proactive Reminder）场景中，指某个已标注事件发生之后的一段固定时间跨度，在此期间收集模型的输出用于评判。
    - Spearman correlation: A rank-based agreement measure used here to compare automatic judge scores with human judgments.
      Spearman correlation（斯皮尔曼相关）：一种基于排名的一致性度量方法，此处用于比较自动评判者的评分与人工评判之间的吻合程度。
- ## Evidence Index
  collapsed:: true
    - **E1:** method/paper_statement | Abstract | high
      locator:: Abstract
      quote:: we propose Omni-DuplexEval, a benchmark for systematically evaluating real-time duplex interaction. The benchmark consists of two complementary scenarios: (1) Real-Time Description ... and (2) Proactive Reminder
    - **E2:** gap/paper_statement | Introduction | high
      locator:: Section 1, motivation
      quote:: most of existing models are designed for static images or offline video processing and must observe the entire video before producing a response. This offline setting differs fundamentally from real-world interaction
    - **E3:** method/paper_statement | Omni-DuplexEval | high
      locator:: Section 3.1.1, Real-Time Description
      quote:: Real-Time Description evaluates the ability to generate responses that follow evolving video content in real time. At the beginning of each sample, the model receives a user instruction that specifies a particular subject or aspect of interest
    - **E4:** method/paper_statement | Omni-DuplexEval | high
      locator:: Section 3.1.2, Proactive Reminder
      quote:: Proactive Reminder evaluates the ability to identify relevant events and determine when to respond based on streaming video inputs. The model receives a user instruction that specifies a clear and well-defined event
    - **E5:** experiment_setup/paper_statement | Benchmark Construction | high
      locator:: Section 3.2 and Figure 4
      quote:: Omni-DuplexEval consists of 660 videos paired with human-curated question-answer annotations, spanning diverse domains such as education, entertainment, sports, and daily activities... All videos are under one minute in length, with an average duration of 34 seconds
    - **E6:** algorithm/implementation_detail | Evaluation Pipeline | high
      locator:: Section 3.3.1 and Figure 5
      quote:: we adopt a two-dimensional evaluation framework consisting of Content Consistency and Temporal Sensitivity. Given a user query q and a model's streaming output S, each sentence is associated with a time interval
    - **E7:** algorithm/implementation_detail | Evaluation Pipeline | high
      locator:: Section 3.3.2 and Appendix A.3
      quote:: During evaluation, we extract the model's responses within a fixed 10-second window following each event timestamp and assess them using an LLM-as-a-Judge framework... the model must correctly respond to all occurrences
    - **E8:** ablation/ablation | Iterative Design and Human Alignment Analysis | medium
      locator:: Appendix B.3 and B.3.3
      quote:: The final Spearman correlation between automatic evaluation and human judgments exceeds 0.9 for Content Consistency, and approaches 0.8 for Temporal Sensitivity, demonstrating strong alignment with human perception.
    - **E9:** experiment_setup/paper_statement | Experiments | high
      locator:: Section 4.1, Baselines
      quote:: we include LiveCC (Base/Instruct), MMDuet2, StreamingVLM, and MiniCPM-o 4.5. All experiments are conducted on a single NVIDIA A100 GPU. For each model, we follow its native duplex inference protocol
    - **E10:** result/experiment_result | Main results | medium
      locator:: Table 2 and Section 4.2
      quote:: current duplex models fall substantially short of human performance on Omni-DuplexEval, with the best model achieving 39.6 compared to 81.8 for Human-Duplex... performance is noticeably higher on Real-Time Description than on Proactive Reminder
    - **E11:** result/experiment_result | Main results | medium
      locator:: Table 3, Figure 6, Section 4.2
      quote:: models achieve relatively strong performance in Temporal Sensitivity but consistently underperform in Content Consistency... they tend to generate sparse and intermittent responses, remaining silent for a large portion of the video
    - **E12:** result/experiment_result | Main results | medium
      locator:: Table 4, Section 4.2
      quote:: MiniCPM-o 4.5 and MMDuet2 are dominated by No Answer cases... LiveCC and StreamingVLM mainly produce Wrong outputs... these models often generate continuous caption-like descriptions without following the instruction
    - **E13:** implementation/implementation_detail | Experimental Settings | high
      locator:: Appendix C.2
      quote:: All inference experiments are conducted on an internal cluster equipped with NVIDIA A100-SXM4 (80GB) GPUs. We employ a single NVIDIA A100 GPU per evaluation run.
    - **E14:** limitation/limitation | Limitations | high
      locator:: Appendix D
      quote:: the current benchmark mainly focuses on relatively short streaming interactions and does not fully capture long-term conversational scenarios... our evaluation framework relies on LLM-as-a-Judge... the number of evaluated duplex models remains limited
    - **E15:** prior_work/paper_statement | Introduction | high
      locator:: Table 1 and Section 2.2
      quote:: existing benchmarks do not comprehensively evaluate real-time duplex interaction-the ability to generate continuous responses while maintaining temporal alignment with evolving video streams. They largely focus on discrete question-answering
