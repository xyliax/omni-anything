- **Title:** RIVER: A Real-Time Interaction Benchmark for Video LLMs
  **标题:** RIVER：面向视频大语言模型的实时交互基准
- **Summary:** RIVER reframes video-LLM evaluation around timed human interaction, showing that models need memory, live perception, and future-triggered responses rather than only whole-video question answering.
  **一句话总结:** RIVER 把视频大语言模型的评测重新定位到「有明确时间点的人机交互」上，指出模型不仅要能对整段视频做问答，还需要具备记忆、实时感知能力，以及在未来某个条件出现时才触发的应答能力。
- **Paper Type:** benchmark
  **论文类型:** 基准（benchmark）
- **Venue:** ICLR 2026
  **发表:** ICLR 2026
- **Authors:** Yansong Shi (University of Science and Technology of China; Shanghai Artificial Intelligence Laboratory), Qingsong Zhao (Fudan University; Shanghai Artificial Intelligence Laboratory), Tianxiang Jiang (University of Science and Technology of China; Shanghai Artificial Intelligence Laboratory), Xiangyu Zeng (Nanjing University; Shanghai Artificial Intelligence Laboratory), Yi Wang (Shanghai Artificial Intelligence Laboratory), Limin Wang (Nanjing University; Shanghai Artificial Intelligence Laboratory)
  **作者:** Yansong Shi（中国科学技术大学；上海人工智能实验室）、Qingsong Zhao（复旦大学；上海人工智能实验室）、Tianxiang Jiang（中国科学技术大学；上海人工智能实验室）、Xiangyu Zeng（南京大学；上海人工智能实验室）、Yi Wang（上海人工智能实验室）、Limin Wang（南京大学；上海人工智能实验室）
- **Keywords:** video LLM, online multimodal interaction, streaming video understanding, retrospective memory, live perception, proactive response, benchmark, long-short term memory
  **关键词:** 视频大语言模型、在线多模态交互、流式视频理解、回溯记忆、实时感知、主动应答、基准、长短期记忆
- ## Orientation
    - **Background:** Video language models answer questions about moving visual scenes. A streaming interaction is harder than a normal video quiz because the model sees the video over time while a person may ask, wait, or expect an interruption.
      **背景:** 视频语言模型用来回答关于动态视觉场景的问题。流式交互比普通的视频问答更难，因为模型是随时间逐步看到视频的，而使用者可能会提问、等待，或期望模型主动打断。
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A helpful assistant should remember where something was, describe what is happening now, and speak up only when the right future event appears.
      **通俗问题:** 一个有用的助手应当记住某样东西曾经出现在哪里，描述此刻正在发生什么，并且只在恰当的未来事件出现时才开口说话。
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** The model must keep useful past details without storing everything, notice current evidence quickly, and avoid answering too early when the visual clue has not happened yet.
      **为何困难:** 模型必须在不存下所有内容的前提下保留有用的过往细节，快速察觉当前的证据，并且在视觉线索还没出现时避免过早作答。
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Turn live video dialogue into timed questions about past, present, and future visual clues, then score both answer correctness and response timing.
      **一句话核心思路:** 把实时视频对话转化为围绕过去、当前和未来视觉线索的定时提问，然后同时对答案的正确性和响应的时机进行评分。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a benchmark paper for online video-language systems: it targets the gap between whole-video QA and interaction where a model must remember past visual evidence, answer about the current scene, and wait for future visual cues.
      **阅读价值:** 把它当作一篇面向在线视频语言系统的基准论文来读：它针对的是「对整段视频做问答」与「真正的交互」之间的差距——在交互场景下，模型必须记住过去出现过的视觉证据，回答当前画面里的问题，并等待未来的视觉线索出现。
      claim_kind:: analyst_assessment
      evidence:: E2, E3, E18
    - **One-Sentence Contribution:** RIVER improves evaluation of video large language models in streaming interaction by anchoring questions, visual cues, and responses to explicit times instead of treating the whole video as one offline input.
      **一句话贡献:** RIVER 改进了对视频大语言模型在流式交互中的评测方式：它把问题、视觉线索和应答都锚定到明确的时间点上，而不是把整段视频当作一次离线输入来处理。
      evidence:: E3, E4
    - **Mental Model:** Picture a person watching a live camera feed for you: sometimes you ask what just happened, sometimes what is happening now, and sometimes you ask the watcher to interrupt only when a named event appears.
      **记忆模型:** 可以把它想象成有一个人替你盯着实时摄像头画面：有时你问刚刚发生了什么，有时你问现在正在发生什么，有时你让这个盯画面的人只在某个指定事件出现时才打断你。
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is the cross-model evaluation showing that strong offline QA performance does not transfer cleanly to real-time memory and proactive response.
      **最佳证据:** 最有力的证据是跨模型评测的结果，它表明：在离线问答上表现强的模型，其能力并不能顺畅地迁移到实时记忆和主动应答上。
      evidence:: E12, E13, E14
        - Supports C1: RIVER is compared with prior online-video benchmarks; baseline benchmarks lack several temporal-memory intervals and instant-stream anticipation; metric coverage is broader; support is direct but based on the authors' benchmark taxonomy.
          支持结论 C1：论文把 RIVER 与已有的在线视频基准做了对比；基线基准缺少若干时间记忆区间以及即时流预判能力；指标覆盖面更广；这一支持是直接的，但依据的是作者自己制定的基准分类体系。
          evidence:: E4, E18
        - Supports C2: offline video MLLMs adapted to 1 fps streaming are compared with fixed-frame variants; retro-memory and live-perception scores change by task and model; support is moderate because no uncertainty is reported.
          支持结论 C2：论文把适配到 1 fps 流式输入的离线视频多模态大语言模型（MLLM）与固定帧数的变体做了对比；回顾记忆（Retro-Memory）和实时感知（Live-Perception）的得分随任务和模型不同而变化；由于没有报告不确定性，这一支持的强度只能算中等。
          evidence:: E10, E12, E14
        - Supports C3: VideoLLM-Online plus RIVER training at 4 fps is compared with VideoLLM-Online at 2 fps; pro-response localization rises from 23.88 to 35.16 and MC from 6.67 to 10.53; support is moderate because repeat counts are not reported.
          支持结论 C3：论文把「VideoLLM-Online 加上 RIVER 在 4 fps 下的训练」与「VideoLLM-Online 在 2 fps 下」做了对比；主动响应（Pro-Response）的定位得分从 23.88 提升到 35.16，MC 从 6.67 提升到 10.53；由于没有报告重复实验次数，这一支持的强度只能算中等。
          evidence:: E13
    - **Main Caveat:** The benchmark is video-only and the reported results mostly lack variance, repeat counts, and error bars, so it is better read as a useful stress test than as a fully calibrated estimate of deployment reliability.
      **主要边界:** 该基准只涉及视频，且所报告的结果大多缺少方差、重复实验次数和误差棒，因此它更适合被看作一次有用的压力测试，而不是对部署可靠性的完全校准估计。
      claim_kind:: analyst_assessment
      evidence:: E12, E17
- ## Argument Map
    - **Problem and Stakes:** The paper argues that multimodal large language models (MLLMs), models that combine language reasoning with visual input, are mostly evaluated as offline whole-video question answerers, while practical assistants need online multimodal language models (oMLLMs), models that react while a video stream is still arriving.
      **问题与重要性:** 论文认为，多模态大语言模型（MLLM）——即把语言推理与视觉输入结合起来的模型——目前大多是作为离线的整段视频问答器来评估的，而实用的助手需要的是在线多模态大语言模型（oMLLM）——即在视频流仍在到来的过程中就作出反应的模型。
      evidence:: E2, E3
    - **Prior Gap:** Prior online-video benchmarks cover pieces of the problem but do not jointly formalize memory intervals, live perception, proactive response, and fine-grained timing between cue, question, and answer.
      **已有方法缺口:** 已有的在线视频基准只覆盖了问题的一部分，并没有把记忆区间、实时感知、主动响应，以及线索、提问和答案之间的细粒度时机联合形式化。
      evidence:: E2, E18
    - **Key Insight:** The useful unit of evaluation is not just whether a model can answer a video question, but whether it answers from the correct temporal relationship: past cue, current cue, or future cue.
      **关键洞见:** 有价值的评测单位不只是模型能否回答视频问题，还包括它是否依据正确的时间关系来作答：即依据过去的线索、当前的线索还是未来的线索。
      claim_kind:: analyst_assessment
      evidence:: E5, E8
    - **Claims:** The paper's core argument is captured by four falsifiable claims.
      **核心主张:** 本文的核心论点由四条可证伪的主张构成。
      claim_kind:: analyst_assessment
        - C1: RIVER Bench formalizes online video interaction as Retrospective Memory, Live-Perception, and Proactive Response tasks with explicit temporal relationships and broader coverage than prior benchmarks.
          C1：RIVER Bench 把在线视频交互形式化为三类任务，即回溯记忆（Retrospective Memory）、实时感知（Live-Perception）和主动响应（Proactive Response）；这些任务带有明确的时间关系，覆盖范围也比以往的基准测试更广。
          evidence:: E3, E4, E5
        - C2: A sliding-window online adaptation with long-short term visual memory can make offline video MLLMs operate in streaming settings and reduce degradation on medium-to-long memory questions.
          C2：一种带有长短期视觉记忆的滑动窗口在线适配方法，能让离线的视频多模态大语言模型（MLLM）在流式场景下工作，并减少其在中长期记忆类问题上的性能下降。
          evidence:: E10, E14, E15
        - C3: Training with RIVER-style proactive interaction data improves VideoLLM-Online on Pro-Response localization and answer metrics.
          C3：用 RIVER 风格的主动交互数据进行训练，能提升 VideoLLM-Online 在主动响应任务上的定位指标与答案指标。
          evidence:: E11, E13
        - C4: Questions requiring causal visual cues, where the answer depends on event dynamics and temporal dependencies, are harder than fine-grained object cues or background cues for the evaluated models.
          C4：对于所评测的模型而言，那些需要因果视觉线索的问题（答案取决于事件动态和时间上的依赖关系）比需要细粒度物体线索或背景线索的问题更难。
          evidence:: E16
- ## Mechanism and Design
    - **Core Mechanism:** RIVER's benchmark mechanism is a timed video-text-to-text interaction: each item specifies a visual cue time, a user query time, and an expected response time, then evaluates whether the model answers correctly and at the right moment.
      **核心机制:** RIVER 基准测试的机制是一种带时间的「视频加文本到文本」交互：每个题目都会指定一个视觉线索出现的时刻、一个用户提问的时刻，以及一个期望的响应时刻，然后评估模型是否既回答正确、又在恰当的时刻作答。
      evidence:: E5, E8
    - **Data / Control Flow:** The data flow starts from existing video QA and dense timestamped event annotations, filters out language-only and ambiguous cases, rewrites them into timed interaction formats, and evaluates model outputs with task-specific answer and timing rules.
      **数据/控制流:** 数据流从已有的视频问答数据和带时间戳的密集事件标注出发，先过滤掉仅靠语言即可作答的情形和有歧义的情形，再把它们改写成带时间的交互格式，最后用针对各任务的答案规则和时间规则来评估模型的输出。
      evidence:: E6, E7, E8
        - For Retrospective Memory and Live-Perception, RIVER samples a query time after or around the referenced event so the same visual fact becomes either a memory test or a current-perception test.
          对于回溯记忆和实时感知任务，RIVER 会在被引用事件之后或其附近采样一个提问时刻，从而让同一个视觉事实既可以作为记忆测试，也可以作为当前感知测试。
          evidence:: E6
        - For Pro-Response, instant questions require a single future-triggered answer, while stream questions require repeated descriptions or guidance over time.
          对于主动响应任务，即时类问题只需给出一次由未来事件触发的答案，而流式类问题则需要随时间推移反复给出描述或指引。
          evidence:: E6
        - Multiple-choice answers are extracted with regular expressions when possible, open-ended answers are judged by Qwen2.5-72B, and proactive timing is scored with early false alarms set to zero and late answers decayed.
          选择题答案在可行时用正则表达式提取，开放式答案由 Qwen2.5-72B 评判；主动响应的时机则这样打分：过早的误报计为零分，过晚的答案则按衰减处理。
          evidence:: E8
    - **Design Decisions:** The design choices mainly protect temporal validity: force one grounded visual moment per answer, separate past/current/future relationships, and compress old visual context instead of letting the model see an unlimited stream.
      **设计决策:** 这些设计选择主要用来保证时间上的有效性：每个答案都必须锚定在某一个具体的视觉时刻上；把过去、当前、未来这三种关系分开处理；并对旧的视觉上下文进行压缩，而不是让模型看到无限长的画面流。
      evidence:: E6, E7, E10
        - Need: avoid questions answerable from broad context; choice: require precise cue, query, and response times; closest alternative: conventional whole-video QA; tradeoff: higher annotation burden.
          需求：避免那些仅凭宽泛上下文就能回答的问题；做法：要求精确标注线索时间、提问时间和回答时间；最接近的替代方案：传统的整段视频问答；代价：标注负担更重。
          evidence:: E6, E7
        - Need: keep old visual evidence under bounded memory; choice: a sliding window plus long-term compressed tokens selected by nearest-neighbor averaging; closest alternative: keep only recent frames; tradeoff: compression may blur fine details.
          需求：在有限的内存下保留旧的视觉证据；做法：采用一个滑动窗口（sliding window），再加上通过最近邻平均法筛选出的长期压缩词元；最接近的替代方案：只保留最近的若干帧；代价：压缩可能会模糊掉细节。
          evidence:: E10
        - Need: distinguish useful waiting from premature alerts; choice: score responses inside the tolerance window fully, early responses as zero, and late responses with linear decay; tradeoff: the window encodes a human-tolerance assumption.
          需求：区分有价值的等待和过早发出的提醒；做法：对落在容忍窗口之内的响应给满分，对过早的响应计为零分，对过晚的响应按线性衰减打分；代价：这个窗口内含了一个关于人类容忍度的假设。
          evidence:: E8
    - **Implementation Surface:** The evaluated surface includes closed-source models, native streaming models, offline open-source video MLLMs adapted with 1 fps sliding windows, and a VideoLLM-Online-style trained model using SigLIP visual features, an MLP connector, LLaMA3-8B, and LoRA.
      **实现边界:** 被评测的模型范围包括：闭源模型、原生流式模型、用 1 fps 滑动窗口（sliding window）改造过的离线开源视频多模态大语言模型（MLLM），以及一个 VideoLLM-Online 风格的训练模型，后者使用了 SigLIP 视觉特征、一个 MLP 连接器、LLaMA3-8B，并配合低秩适配（Low-Rank Adaptation，LoRA）。
      evidence:: E9, E10, E11
- ## Evaluation and Evidence
    - **Setup:** The evaluation compares model families under RIVER's three task types, using recommended frame sampling for offline models, streaming frame rates for online models, multiple-choice and open-ended answer metrics, and proactive localization scores.
      **实验设置:** 该评测在 RIVER 的三种任务类型下对比不同的模型系列：离线模型采用各自推荐的抽帧方式，在线模型采用流式帧率；答案方面使用选择题指标和开放式指标，并对主动响应任务给出定位得分。
      evidence:: E8, E9, E12
    - **Claim-Evidence Matrix:** The evidence is strongest for benchmark coverage and moderately strong for model conclusions because the paper reports broad comparisons but not statistical uncertainty.
      **主张-证据矩阵:** 证据在基准覆盖度方面最为充分，在模型结论方面则只是中等强度，因为论文报告了大范围的对比，却没有给出统计上的不确定性。
      claim_kind:: analyst_assessment
      evidence:: E4, E12, E13, E14
        - C1: supported by Table 1, task definitions, and comparison to OVO-Bench; the caveat is that coverage categories are the authors' taxonomy rather than an external standard.
          C1：由表 1、任务定义以及与 OVO-Bench 的对比所支持；需要说明的是，覆盖类别是作者自己划分的分类体系，而非某个外部标准。
          evidence:: E4, E5, E18
        - C2: supported by the long-short term memory design, retro-memory duration table, and memory curve; the caveat is no reported variance or controlled model-by-model ablation for every architecture.
          C2：由长短期记忆模块的设计、回溯记忆时长表以及记忆曲线所支持；需要说明的是，论文没有报告方差，也没有对每种架构逐一做受控的消融实验。
          evidence:: E10, E14, E15
        - C3 and C4: supported by proactive training results and clue-category breakdown; the caveat is that generated proactive questions and LLM-judged open-ended metrics add evaluator dependence.
          C3 与 C4：由主动式训练结果和线索类别细分数据提供支撑；需要注意的是，生成的主动式问题以及由大语言模型评判的开放式指标增加了对评判器的依赖。
          evidence:: E13, E16
    - **Headline Results:** The headline pattern is that whole-video strength does not imply online interaction strength: GPT-4o leads the aggregate table, adapted offline models become competitive on live perception, and native streaming models remain weak on RIVER's interactive QA.
      **关键结果:** 最突出的规律是：在完整视频上的能力强，并不意味着在线交互能力也强。GPT-4o 在综合排行榜上领先；经过适配的离线模型在实时感知任务上变得有竞争力；而原生流式模型在 RIVER 的交互式问答上仍然表现薄弱。
      evidence:: E12, E13, E14
        - VideoLLM-Online+RIVER at 4 fps improves Pro-Response Loc by 11.28 points over VideoLLM-Online at 2 fps, with smaller gains on MC and OE, but the table does not report repeat counts.
          VideoLLM-Online+RIVER 在 4 fps 下的主动式响应定位（Pro-Response Loc）比 2 fps 下的 VideoLLM-Online 高出 11.28 分，在多项选择（MC）和开放式评估（OE）上的提升较小，但表中并未报告重复实验次数。
          evidence:: E13
        - Retro-memory performance generally declines as the recall interval grows, while memory-based designs are presented as stabilizing retrieval over longer windows.
          回溯记忆（Retro-Memory）性能通常随召回间隔的增大而下降，而基于记忆的设计被认为能在更长的时间窗口上稳定检索表现。
          evidence:: E14, E15
    - **Ablations and Sensitivity:** The paper's main sensitivity evidence is not a dense ablation grid but two targeted probes: memory versus no-memory decay, and performance by visual cue type.
      **消融与敏感性:** 论文的主要敏感性证据并非密集的消融网格，而是两个有针对性的探测：有记忆与无记忆的性能衰减对比，以及按视觉线索类型划分的性能。
      evidence:: E15, E16
        - Memory modules reduce the reported decay slope by 12%, suggesting that explicit compressed memory helps when the queried evidence is no longer in the current visual window.
          记忆模块使报告中的衰减斜率降低了 12%，这表明当被询问的证据已不在当前视觉窗口内时，显式的压缩记忆能够起到帮助作用。
          evidence:: E15
        - Causal cues remain difficult across methods, implying that online evaluation exposes event-attribution weaknesses beyond object or scene recognition.
          因果类线索在各种方法下都仍然很难处理，这意味着在线评估会暴露出超越物体识别或场景识别之外的、在事件归因方面的弱点。
          evidence:: E16
    - **Reproducibility Gaps:** The paper states that code, data processing, benchmark simulation, and evaluation will be released, but original videos follow index-only release rules; not reported: statistical uncertainty, repeated runs, detailed cost budgets, and full prompt sensitivity.
      **可复现性缺口:** 论文声明将发布代码、数据处理流程、基准仿真和评估方法，但原始视频遵循仅发布索引的规则；未报告的内容包括：统计不确定性、重复运行结果、详细的成本预算以及完整的提示词敏感性分析。
      claim_kind:: analyst_assessment
      evidence:: E8, E11, E17
- ## Technical Judgment
    - **What Holds Up:** The benchmark framing is the durable part: explicit cue, question, and response times give a cleaner test of streaming behavior than whole-video QA, and the three-task split maps to concrete assistant use cases.
      **站得住的结论:** 基准的构建框架是站得住脚的部分：显式地给出线索、问题和响应的时间点，相比针对完整视频的问答，能更清晰地测试流式行为；而且这三类任务的划分对应到具体的助手使用场景。
      claim_kind:: analyst_assessment
      evidence:: E3, E5, E8
    - **Where It May Fail:** RIVER may understate multimodal interaction needs because it excludes audio, relies partly on generated proactive QA and LLM-based open-ended judging, and reports tables without variance or repeat-count evidence.
      **可能失效之处:** RIVER 可能低估了多模态交互的需求，因为它排除了音频，部分依赖生成的主动式问答以及基于大语言模型的开放式评判，并且在报告表格时缺少方差或重复实验次数方面的证据。
      claim_kind:: analyst_assessment
      evidence:: E7, E8, E12, E17
    - **Relation to Other Work:** Relative to offline video benchmarks, RIVER changes the unit of evaluation from holistic video understanding to timed interaction; relative to OVO-Bench and related online benchmarks, it emphasizes finer response and clue intervals plus memory curves.
      **与已有工作的关系:** 与离线视频基准相比，RIVER 把评测单元从整体的视频理解改为带时间标记的交互；与 OVO-Bench 及相关在线基准相比，它更强调更细粒度的响应区间和线索区间，并加入了记忆曲线。
      evidence:: E2, E18
    - **Transferable Lesson:** For streaming AI systems, evaluation should encode when evidence becomes available and when an answer becomes useful; adding time to the task definition can expose failures that static accuracy hides.
      **可迁移启发:** 对于流式 AI 系统，评测应当刻画证据何时变得可用、答案何时变得有用；把时间纳入任务定义，可以暴露出静态准确率所掩盖的失败情形。
      claim_kind:: analyst_assessment
      evidence:: E5, E8, E12
- ## Glossary
  collapsed:: true
    - Multimodal large language model: A language model that can condition on non-text inputs such as images or video frames; in this note, it usually means a video-capable model.
      多模态大语言模型（Multimodal large language model，MLLM）：一种能够以非文本输入（如图像或视频帧）为条件进行处理的语言模型；在本笔记中，它通常指具备视频处理能力的模型。
    - Online multimodal large language model: A multimodal model expected to process a stream as it arrives and answer during the stream, not only after seeing the whole video.
      在线多模态大语言模型（Online multimodal large language model，oMLLM）：一种被要求在数据流到达时就逐步处理并在流进行过程中作答的多模态模型，而不是只在看完整段视频之后才作答。
    - Temporal interaction: An evaluation format where the visual cue, user question, and model answer each have positions on the video timeline.
      时序交互（Temporal interaction）：一种评测形式，其中视觉提示、用户问题和模型答案各自在视频时间轴上都有对应的位置。
    - Retrospective Memory: A task where the model answers a current question using evidence from an earlier moment in the video.
      回溯记忆（Retrospective Memory）：一类任务，模型需要利用视频中较早时刻的证据来回答当前的问题。
    - Live-Perception: A task where the referenced visual evidence is in the current or very recent video window, so the model should answer immediately.
      实时感知（Live-Perception）：一类任务，其所引用的视觉证据位于当前或非常近期的视频窗口中，因此模型应当立即作答。
    - Proactive Response: A task where the model must wait for a future visual condition and respond when that condition is observed.
      主动响应（Proactive Response）：一类任务，模型必须等待某个未来的视觉条件出现，并在观察到该条件时作出响应。
    - Sliding window: A streaming strategy that processes only a recent span of frames at each step, then advances the span as time moves forward.
      滑动窗口（Sliding window）：一种流式处理策略，每一步只处理最近一段范围内的帧，随着时间推进再向前移动这段范围。
    - Long-short term memory module: RIVER's adaptation pattern: keep current-window frame tokens as short-term memory and compressed earlier tokens as long-term memory.
      长短期记忆模块（Long-short term memory module）：RIVER 的适配模式，即把当前窗口的帧 token 作为短期记忆保留，并把压缩后的较早 token 作为长期记忆保留。
    - Open-ended evaluation: A model-judged answer-consistency check used when the output is not cleanly extractable as a multiple-choice option.
      开放式评测（Open-ended evaluation）：一种由模型担任评判、检查答案一致性的方法，用于输出无法直接提取为某个选择题选项的场景。
    - Low-Rank Adaptation: A parameter-efficient fine-tuning method that trains small low-rank updates inside a larger neural network instead of updating all parameters.
      低秩适配（Low-Rank Adaptation）：一种参数高效的微调方法，它在较大的神经网络内部训练小规模的低秩更新，而不是更新全部参数。
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/metadata | Title and metadata | high
      locator:: title block and arXiv header
      quote:: arXiv:2603.03985v1 [cs.CV] 4 Mar 2026. Published as a conference paper at ICLR 2026. RIVER: A REAL-TIME INTERACTION BENCHMARK FOR VIDEO LLMs.
    - **E2:** problem/paper_statement | Introduction | high
      locator:: Section 1, online interaction motivation
      quote:: Existing benchmarks inadequately address the dynamic requirements of online applications such as augmented reality navigation or robotic task supervision, creating bottlenecks for systematic progress in online interaction research.
    - **E3:** method/paper_statement | Abstract and Introduction | high
      locator:: Abstract; Section 1 contribution paragraph
      quote:: RIVER Bench introduces a novel evaluation framework comprising Retrospective Memory, Live-Perception, and Proactive Response tasks, closely mimicking interactive dialogues with humans rather than understanding the entire videos at once.
    - **E4:** experiment_setup/metadata | RIVER Bench | high
      locator:: Table 1 and Section 3
      quote:: Table 1 reports RIVER (ours) with 1,067 videos and 4,278 questions, covering General, Short, Medium, Long, Very Long memory and perception categories plus Instant Stream anticipation.
    - **E5:** method/paper_statement | Interactive Task Types | high
      locator:: Section 3.1
      quote:: We summarize three main task types of RIVER Bench as retro-memory, live-perception, and pro-response, according to the happening time of the queried event or target.
    - **E6:** experiment_setup/paper_statement | Data Construction | high
      locator:: Section 3.2, Retro-Memory and Pro-Response
      quote:: Retro-memory queries are categorized into short (15-30s), medium (30-60s), long (300-900s), and very long (1800-3600s). Pro-response instant-type questions are further classified into short, medium, long, and very long.
    - **E7:** system_design/paper_statement | Quality Control | medium
      locator:: Section 3.3 and Appendix A.1
      quote:: We employ a multi-stage filtering process combining open-source large language models and rigorous human evaluation. First, we use LLMs to identify and remove questions that can be answered correctly without visual input.
    - **E8:** experiment_setup/paper_statement | Metrics | high
      locator:: Section 3.4
      quote:: The metric assigns a full score to responses falling inside this interval, reflecting acceptable anticipation. It strictly penalizes early responses with a score of zero and applies a linear decay to late responses.
    - **E9:** experiment_setup/paper_statement | Experiments | high
      locator:: Section 4, setup paragraph
      quote:: We evaluate four categories of video-processing multimodal large language models: commercial closed-source models, open-source models with native online inference support, open-source video multimodal models, and our proposed video multimodal model adapted for online inference.
    - **E10:** system_design/implementation_detail | Making Offline Models Work Online | high
      locator:: Section 4.1 and Appendix A.3
      quote:: We employ a sliding window approach with a sampling rate of 1 frame per second for processing long video inputs. The long-term memory module comprises compressed tokens from video frames prior to the current window.
    - **E11:** implementation/implementation_detail | Training the Online Models | high
      locator:: Section 4.2 and Table 6
      quote:: We employ the SigLIP-Large-Patch16 encoder coupled with a two-layer MLP connector to extract video frame representations at a rate of 4 frames per second. We integrate Low-Rank Adaptation into all linear layers of the LLaMA3-8B backbone.
    - **E12:** result/experiment_result | Evaluation Results and Analysis | medium
      locator:: Table 2 and Section 4.3
      quote:: Table 2 compares native online inference models and enhanced non-native MLLMs. GPT-4o achieves the best performance, excelling in live-perception, retro-memory, and pro-response tasks.
    - **E13:** result/experiment_result | Evaluation Results and Analysis | medium
      locator:: Table 3 and Section 4.3
      quote:: VideoLLM-Online reports 23.88 Loc, 6.67 MC, and 4.41 OE. VideoLLM-Online+RIVER at 4 fps reports 35.16 Loc, 10.53 MC, and 5.47 OE for Pro-Response.
    - **E14:** result/experiment_result | Model Memory Capability | medium
      locator:: Table 4 and Section 4.3.1
      quote:: As recall duration increases, most models exhibit declining visual memory retrieval and reasoning abilities. Flash-VStream is an exception. While its overall performance remains modest, it maintains consistent accuracy across all durations.
    - **E15:** ablation/ablation | Model Memory Curve | medium
      locator:: Figure 5 and Section 4.3.2
      quote:: Adding memory modules significantly boosts retrieval, cutting the performance drop-off (decay slope) by 12% compared to models without memory.
    - **E16:** result/experiment_result | Performance Across Different Clue Categories | medium
      locator:: Table 5 and Section 4.3.3
      quote:: All methods perform poorly on CC questions, revealing their greater difficulty and highlighting the need for future work on visual perception integrated with event attribution.
    - **E17:** limitation/limitation | Conclusion and Reproducibility Statement | high
      locator:: Section 5, Reproducibility Statement, Appendix C
      quote:: Currently, our dataset does not include audio data. Given that sound is one of the most readily available modalities for real-time interaction, integrating audio into the evaluation of online video content is crucial.
    - **E18:** prior_work/paper_statement | Related Works | medium
      locator:: Section 2, Online Video Benchmarks
      quote:: OVO-Bench represents the most relevant existing work for defining online video understanding tasks but it lacks fine-grained temporal segmentation of the response or clue intervals.
