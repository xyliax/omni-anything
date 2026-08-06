- **Title:** ProactiveVideoQA: A Comprehensive Benchmark Evaluating Proactive Interactions in Video Large Language Models
  **标题:** ProactiveVideoQA：一个评估视频大语言模型中主动交互的综合基准
- **Summary:** ProactiveVideoQA and PAUC recast video QA evaluation as a time-varying, open-ended answer-quality curve so models are rewarded for deciding when to speak as well as what to say.
  **一句话总结:** ProactiveVideoQA 和 PAUC 将视频问答评估重新构建为一条随时间变化、开放式的答案质量曲线，从而不仅奖励模型决定「说什么」，也奖励其决定「何时开口」。
- **Paper Type:** benchmark
  **论文类型:** 基准
- **Venue:** arXiv preprint 2025 (v2, 15 Jul 2025)
  **发表:** arXiv 预印本 2025 (v2, 2025年7月15日)
- **Authors:** Yueqian Wang (Wangxuan Institute of Computer Technology, Peking University), Xiaojun Meng (Huawei Noah's Ark Lab), Yifan Wang (School of Intelligence Science and Technology, University of Science and Technology Beijing), Huishuai Zhang (Peking University; National Key Laboratory of General Artificial Intelligence), Dongyan Zhao (Peking University; National Key Laboratory of General Artificial Intelligence)
  **作者:** Yueqian Wang（北京大学王选计算机研究所）, Xiaojun Meng（华为诺亚方舟实验室）, Yifan Wang（北京科技大学智能科学与技术学院）, Huishuai Zhang（北京大学；通用人工智能全国重点实验室）, Dongyan Zhao（北京大学；通用人工智能全国重点实验室）
- **Keywords:** proactive video QA, video multimodal large language models, benchmark, PAUC, time-aware evaluation, open-ended QA, streaming video, human preference alignment
  **关键词:** 主动视频问答, 视频多模态大语言模型, 基准, PAUC, 时间感知评估, 开放式问答, 流视频, 人类偏好对齐
- ## Quick Reference
    - **Why Read:** Read this if you need an evaluation lens for video multimodal large language models (Video MLLMs) that must choose when to respond during playback, not merely answer after seeing a full clip.
      **阅读价值:** 如果你需要一种评估视角，来评价那些必须在视频播放过程中选择何时做出响应，而不是仅在观看完整片段后才回答的视频多模态大语言模型（Video MLLMs），请阅读本文。
      claim_kind:: analyst_assessment
      evidence:: E2, E3
    - **One-Sentence Contribution:** ProactiveVideoQA improves evaluation of Video MLLMs in proactive question answering by scoring, over annotated answer spans, how quickly the accumulated answer stream becomes correct rather than only grading the final text.
      **一句话贡献:** ProactiveVideoQA 改进了对 Video MLLMs 在主动问答中的评估，它通过在标注的答案跨度上，对累积答案流变得正确的速度进行评分，而不是仅对最终文本打分。
      evidence:: E2, E4, E8
    - **Mental Model:** Think of a proactive answer stream as a user-experience curve: silence starts above being wrong, correct early information lifts the curve sooner, and wrong early information drags later judgments down.
      **记忆模型:** 可以将主动答案流看作一条用户体验曲线：沉默的起点高于错误答案，早期正确的信息会更早地提升曲线，而早期错误的信息会拖累后续的判断。
      claim_kind:: analyst_assessment
      evidence:: E4, E6
    - **Best Evidence:** The strongest evidence is a combination of benchmark coverage, main-model stress tests, and a human-preference comparison between time-aware and time-agnostic scoring.
      **最佳证据:** 最强的证据结合了基准覆盖度、主模型压力测试以及时间感知与时间无关评分之间的人类偏好比较。
      evidence:: E9, E13, E17
        - Supports C2: human preference over GPT-4.1-mini versus Gemini-2.0-Flash predictions; baseline is PAUC with timeliness weight ω=1; Cohen's kappa improves at ω=0.5 on web-video ([WEB]) from 0.23/0.30 to 0.37/0.40 and on video anomaly detection ([VAD]) from 0.31/0.36 to 0.45/0.49; moderate support because absolute kappa remains low.
          支持 C2：人类对 GPT-4.1-mini 与 Gemini-2.0-Flash 预测的偏好；基线为时效性权重 ω=1 下的 PAUC；当 ω=0.5 时，Cohen's kappa 在 web-video ([WEB]) 上从 0.23/0.30 提升至 0.37/0.40，在 video anomaly detection ([VAD]) 上从 0.31/0.36 提升至 0.45/0.49；支持力度中等，因为绝对 kappa 值仍然偏低。
          evidence:: E16, E17
        - Supports C1: benchmark comparison; baseline is prior video QA and streaming benchmarks; ProactiveVideoQA reports video/audio inputs, 1,377 videos, 1,427 questions, multi-answer/open-ended/proactive status, and four task families; direct dataset support.
          支持 C1：benchmark 对比；基线为已有的 video QA 和 streaming benchmark；ProactiveVideoQA 报告了 video/audio 输入、1,377 个视频、1,427 个问题、多答案/开放式/proactive 状态以及四个任务族；直接的 dataset 支持。
          evidence:: E8, E9
        - Supports C3: default ω=0.5 benchmark; baseline is the best adapted offline model per task; best proactive model MMDuet with removed assistant turns trails by 11.5 [WEB], 13.6 egocentric ([EGO]), 26.8 television-series ([TV]), and 5.2 [VAD] PAUC points; moderate support without reported uncertainty.
          支持 C3：默认 ω=0.5 benchmark；基线为每个任务上最佳的 adapted offline model；最佳 proactive model MMDuet 在移除 assistant turns 后落后 11.5 [WEB]、13.6 egocentric ([EGO])、26.8 television-series ([TV]) 和 5.2 [VAD] PAUC 分；支持力度中等，未报告不确定性。
          evidence:: E13
        - Supports C3: duplicate-output analysis; baseline is all predicted turns excluding the first turn in each ground-truth answer turn; MMDuet duplicate proportions are 81.3%, 99.4%, 92.8%, and 99.2% across [WEB]/[EGO]/[TV]/[VAD]; supports redundancy as a failure mode.
          支持 C3：duplicate-output 分析；基线为每个 ground-truth answer turn 中排除首轮后的所有 predicted turns；MMDuet 在 [WEB]/[EGO]/[TV]/[VAD] 上的重复比例分别为 81.3%、99.4%、92.8% 和 99.2%；支持冗余作为一种 failure mode。
          evidence:: E15
    - **Main Caveat:** The metric is only as objective as its annotated answer spans and GPT-4.1 large-language-model judge; the human-preference study itself shows low agreement, so PAUC is a useful proxy rather than a definitive user-experience measure.
      **主要边界:** 该 metric 的客观性仅取决于其标注的 answer spans 和 GPT-4.1 large-language-model judge；human-preference 研究本身显示一致性较低，因此 PAUC 是一个有用的代理指标，而非最终的用户体验度量。
      claim_kind:: analyst_assessment
      evidence:: E4, E5, E17
- ## Argument Map
    - **Problem and Stakes:** Video MLLMs are moving from offline or user-triggered online QA toward proactive interaction, where the system continuously monitors playback and autonomously decides when to answer. The stakes are practical real-time settings such as live stream understanding, surveillance, egocentric assistants, and socially interactive agents.
      **问题与重要性:** Video MLLM 正从 offline 或 user-triggered online QA 转向 proactive interaction，即系统持续监听播放并自主决定何时回答。其现实意义在于 live stream 理解、监控、egocentric 助手和社交交互代理等实时场景。
      evidence:: E2, E3
    - **Prior Gap:** Existing evaluations often do not require autonomous response timing: they are offline, multiple-choice, immediate-response streaming tasks, overly simple timing alerts, or single-turn tasks. Conventional text metrics also grade final outputs and miss the temporal evolution of a proactive answer stream.
      **已有方法缺口:** 现有评估通常不要求自主响应时机：它们是 offline、multiple-choice、immediate-response streaming 任务、过于简单的 timing alerts 或单轮任务。传统文本 metric 也只对最终输出打分，忽略了 proactive answer stream 的时序演化过程。
      evidence:: E3, E4
    - **Key Insight:** The paper's core insight is to evaluate proactive interaction as a time-score curve over each answer span, analogous to a user journey map. Area under this curve rewards earlier correct accumulated responses, while accumulated wrong responses can continue to depress later scores.
      **关键洞见:** 论文的核心 insight 是将 proactive interaction 评估为每个 answer span 上的 time-score 曲线，类似于 user journey map。曲线下面积奖励更早出现的正确 accumulated responses，而累积的错误响应会持续压低后续得分。
      evidence:: E4, E6, E7
    - **Claims:** The paper advances three linked claims about benchmark scope, time-aware metric validity, and the current weakness of evaluated proactive systems.
      **核心主张:** 论文提出三个相互关联的 claim，分别关于 benchmark 范围、time-aware metric 的有效性以及当前被评估的 proactive 系统的不足。
      evidence:: E2
        - C1: ProactiveVideoQA is a comprehensive benchmark for proactive video QA because it requires open-ended, potentially multi-turn answers across video/audio tasks spanning web videos, egocentric videos, TV-series clips, and surveillance anomaly videos.
          C1：ProactiveVideoQA 是一个面向 proactive video QA 的综合 benchmark，因为它要求跨 video/audio 任务给出开放式、可能多轮的答案，涵盖 web video、egocentric video、TV-series 片段和 surveillance anomaly video。
          evidence:: E8, E9, E10
        - C2: Proactive Area Under Curve (PAUC) is a better proactive-interaction metric than final-answer evaluation because it jointly scores timing and content, supports task-dependent timeliness through ω, and aligns more closely with human preferences than ω=1 scoring.
          C2：Proactive Area Under Curve (PAUC) 相比最终答案评估是更好的主动交互指标，因为它联合评分时机与内容，通过 ω 支持任务相关的时效性，且比 ω=1 评分更贴近人类偏好。
          evidence:: E4, E7, E17
        - C3: Existing evaluated systems remain weak at proactive interaction: adapted offline models often beat proactive-specific models, and proactive models frequently repeat prior content.
          C3：现有被评估的系统在主动交互方面仍然较弱：经过适配的离线模型往往优于专门设计为主动的模型，且主动模型常重复先前内容。
          evidence:: E13, E14, E15
- ## Mechanism and Design
    - **Core Mechanism:** For each ground-truth reply span, PAUC evaluates the accumulated predictions available at each model response timestamp with GPT-4.1 on a 0/1/2 correctness scale, inserts a starting no-answer score of 0.5 and an end point with the last score, then normalizes the area by span length and maximum score. The video-level PAUC is the average over all ground-truth reply turns.
      **核心机制:** 对于每个 ground-truth 回复区间，PAUC 在每个模型响应时间点上以 GPT-4.1 按 0/1/2 正确性量表评估截至该时刻累积的预测，在曲线起点插入无答案的分数 0.5、终点插入最后一次得分，随后按区间长度和最大分数对面积进行归一化。视频级 PAUC 为所有 ground-truth 回回复轮次的平均值。
      evidence:: E5, E6
    - **Data / Control Flow:** A question is presented at the start of the video; the system emits timestamped free-form answers as playback progresses; evaluation groups responses by annotated answer span and scores accumulated answer prefixes. For adapted offline models, the runtime approximation is chunked inference rather than native streaming control.
      **数据/控制流:** 问题在视频开始时给出；系统在播放推进过程中输出带时间戳的自由格式答案；评估将响应按标注的答案区间分组，并评分累积的答案前缀。对于适配后的离线模型，运行时近似采用的是分块推理而非原生流式控制。
      evidence:: E5, E8, E11
        - Dataset flow: source videos and annotations are converted into question, answer text, and reply timespan triples, with Ego4D QAs generated from dense captions and [VAD] answers manually written.
          数据集流程：源视频与标注被转换为问题、答案文本和回复时间区间三元组，其中 Ego4D QA 由 dense captions 生成，[VAD] 答案为人工撰写。
          evidence:: E8, E10
        - Offline-model flow: each fixed-length video chunk is paired with the question and, for proprietary models, the previous response so the model can say no answer, same answer, or new answer.
          离线模型流程：将每个固定长度的视频块与问题配对；对于专有模型还会附带先前回复，使模型可以输出无答案、相同答案或新答案。
          evidence:: E11, E12
        - Metric flow: for each response timestamp inside a reply span, the judge sees the question, gold answer, and all predictions up to that timestamp, producing the score used in the PAUC curve.
          指标流程：对于落在回复区间内的每个响应时间戳，评判器接收问题、gold answer 以及截至该时间戳的所有预测，产出用于 PAUC 曲线的分数。
          evidence:: E5, E6
    - **Design Decisions:** The benchmark narrows proactive interaction to QA with annotated answer spans to keep evaluation more objective than fully open-ended dialogue, while still requiring autonomous response timing and free-form multi-turn answers. The metric deliberately exposes a tunable timing-content tradeoff rather than baking in one universal preference.
      **设计决策:** 该基准将主动交互限定为带标注答案区间的 QA，以使评估比完全开放式对话更具客观性，同时仍要求自主决定响应时机及自由格式的多轮答案。该指标有意暴露一个可调的时机-内容权衡，而非将某种单一通用偏好固化在内。
      claim_kind:: analyst_assessment
      evidence:: E2, E7, E8
        - Need: final-answer metrics ignore when information arrived; design choice: area under an accumulated correctness curve; closest alternative: static BLEU/CIDEr/semantic/LLM scoring; tradeoff: dependence on ground-truth spans and an LLM judge.
          需求：最终答案指标忽略了信息到达时机；设计选择：累积正确性曲线下的面积；最接近的替代方案：静态 BLEU/CIDEr/语义/LLM 评分；权衡：依赖 ground-truth 区间与 LLM 评判器。
          claim_kind:: analyst_assessment
          evidence:: E4, E5, E6
        - Need: applications differ in timeliness pressure; design choice: ω shifts response times left, with ω=0 emphasizing timeliness and ω=1 ignoring time; tradeoff: model rankings can depend on the chosen ω.
          需求：不同应用在时效压力上存在差异；设计选择：ω 将响应时间左移，ω=0 强调时效性，ω=1 忽略时间；权衡：模型排名可能取决于所选的 ω。
          claim_kind:: analyst_assessment
          evidence:: E7, E13
        - Need: few proactive models are open-sourced; design choice: adapt offline Video MLLMs with fixed chunks; closest reported alternative: gradually increasing chunk prefixes; tradeoff: current open-source models often fail the interaction protocol.
          需求：开源的 proactive 模型很少；设计选择：用固定 chunk 适配 offline Video MLLM；最接近的已报告替代方案：逐步增加 chunk 前缀；权衡：当前开源模型常无法满足 interaction protocol。
          claim_kind:: analyst_assessment
          evidence:: E11, E18
    - **Implementation Surface:** The reported implementation surface includes dataset conversion, timestamped answer spans, chunked offline inference settings, subtitles for TV-series models lacking audio, and GPT-4.1 as the PAUC judge. The paper text gives enough to understand the protocol but not all low-level evaluation parameters needed for exact reproduction.
      **实现边界:** 已报告的实现层面包括数据集转换、带时间戳的回答区间、分块的 offline inference 设置、为缺少音频的 TV-series 模型提供字幕，以及使用 GPT-4.1 作为 PAUC judge。论文正文提供了足以理解 protocol 的信息，但未给出精确复现所需的全部底层评估参数。
      claim_kind:: analyst_assessment
      evidence:: E5, E10, E12
        - Reported inference settings include 2-second chunks and 2 fps for [WEB], 5-second chunks and 1 fps for other datasets, and text subtitles injected at utterance timestamps for [TV] when a model lacks audio input.
          已报告的 inference 设置包括：[WEB] 使用 2 秒 chunk 和 2 fps，其他数据集使用 5 秒 chunk 和 1 fps；当模型缺少音频输入时，[TV] 在 utterance 时间戳处注入文本字幕。
          evidence:: E12
        - Reported annotation processing includes direct reuse of Shot2story-MAGQA-39k and TVQA spans, generated Ego4D QA pairs, manually written UCF-Crime anomaly descriptions, and merging of near-duplicate adjacent ground-truth turns.
          已报告的标注处理包括直接复用 Shot2story-MAGQA-39k 和 TVQA 的区间、生成 Ego4D QA pair、人工撰写 UCF-Crime 异常描述，以及合并近似重复的相邻 ground-truth turn。
          evidence:: E10
        - For open-source offline models, the paper uses a simplified prompt that asks whether the current chunk contains sufficient information, then performs another inference round for the answer if affirmative.
          对于开源自 offline 模型，论文使用简化 prompt 询问当前 chunk 是否包含足够信息，若肯定则再进行一轮 inference 以生成答案。
          evidence:: E11
- ## Evaluation and Evidence
    - **Setup:** Experiments compare proprietary offline Video MLLMs, open-sourced offline Video MLLMs, open-sourced proactive Video MLLMs, and human performance under PAUC. Offline baselines use fixed chunks, [TV] subtitles for models without audio, and human performance is measured with four annotators on 60 videos per dataset.
      **实验设置:** 实验在 PAUC 下对比了 proprietary offline Video MLLM、开源自 offline Video MLLM、开源自 proactive Video MLLM 以及人类表现。Offline baseline 使用固定 chunk，无音频模型使用 [TV] 字幕，人类表现通过四名标注者对每个数据集 60 个视频进行测量。
      evidence:: E12
    - **Claim-Evidence Matrix:** Evidence is strongest for benchmark existence and PAUC's mechanistic definition, moderate for human-preference alignment, and weakest for broad model conclusions because results are point estimates without reported statistical uncertainty.
      **主张-证据矩阵:** benchmark 存在性及 PAUC 的机制性定义证据最强，与人类偏好对齐的证据中等，而关于模型的广泛结论证据最弱，因为结果为点估计且未报告统计不确定性。
      claim_kind:: analyst_assessment
      evidence:: E9, E13, E17
        - C1: Directly supported by dataset sources, task definitions, and Tables 1-2; annotation quality for generated/manual QA is less independently validated in the provided text.
          C1：由数据集来源、任务定义及 Tables 1-2 直接支持；生成/人工 QA 的标注质量在提供的正文中缺乏独立验证。
          claim_kind:: analyst_assessment
          evidence:: E8, E9, E10
        - C2: Mechanistically supported by PAUC's timestamped accumulated scoring and empirically supported by higher human-preference kappa at ω=0.5 than at ω=1, but the absolute agreement remains low.
          C2：由 PAUC 的时间戳累积评分机制支持，并由 ω=0.5 时人类偏好 kappa 高于 ω=1 时的事实经验性支持，但绝对一致性仍然较低。
          claim_kind:: analyst_assessment
          evidence:: E4, E7, E17
        - C3: Supported by Table 3 and duplicate-turn analysis; validity caveat is that proactive and offline systems differ in training goals and prompting, and no variance or significance tests are reported.
          C3：由 Table 3 和 duplicate-turn 分析支持；有效性局限在于 proactive 与 offline 系统在训练目标和 prompting 上存在差异，且未报告方差或显著性检验。
          claim_kind:: analyst_assessment
          evidence:: E13, E15
    - **Headline Results:** At the recommended default ω=0.5, the benchmark reveals a mixed landscape: strong offline models can score well on some tasks, humans are not an easy ceiling under the annotation protocol, and proactive-specific models do not dominate. The results should be read as point estimates because repeat counts, confidence intervals, and statistical tests are not reported in the table.
      **关键结果:** 在推荐的默认 ω=0.5 下，基准测试呈现出参差不齐的格局：强离线模型在部分任务上可以获得较高分数，在标注协议下人类并非易于突破的天花板，而专门为 proactive 交互设计的模型并未占据主导。由于表中未报告重复次数、置信区间和统计检验，结果应作为点估计阅读。
      claim_kind:: analyst_assessment
      evidence:: E13, E14
        - Task-best default scores in Table 3 are LLaVA-OV 7B at 55.0 on [WEB], GPT-4.1-mini at 65.8 on [EGO], GPT-4.1-mini at 59.4 on [TV], and human annotators at 53.6 on [VAD].
          表 3 中各任务的默认最佳分分别为：LLaVA-OV 7B 在 [WEB] 上 55.0，GPT-4.1-mini 在 [EGO] 上 65.8，GPT-4.1-mini 在 [TV] 上 59.4，人类标注者在 [VAD] 上 53.6。
          claim_kind:: analyst_assessment
          evidence:: E13
        - Human-preference alignment improves when timing is included: ω=0.5 beats ω=1 on every task under reported Cohen's kappa, with the largest shown jump on [VAD] from 0.31/0.36 to 0.45/0.49.
          当纳入时机因素后，人类偏好一致性有所提升：在报告的 Cohen's kappa 下，ω=0.5 在每个任务上均优于 ω=1，增幅最大的是 [VAD]，从 0.31/0.36 上升至 0.45/0.49。
          claim_kind:: analyst_assessment
          evidence:: E17
        - Best proactive default scores from MMDuet with removed assistant turns trail best adapted offline scores by 11.5 [WEB], 13.6 [EGO], 26.8 [TV], and 5.2 [VAD] PAUC points.
          MMDuet 去除 assistant turns 后的最佳 proactive 默认分落后于最佳适配离线分数，差距为 [WEB] 11.5、[EGO] 13.6、[TV] 26.8、[VAD] 5.2 个 PAUC 点。
          claim_kind:: analyst_assessment
          evidence:: E13
    - **Ablations and Sensitivity:** The paper's main sensitivity axis is ω, which changes how much late correctness is discounted; Table 3 shows many scores increasing as ω approaches 1 because timing is de-emphasized. Additional analyses probe MMDuet repetition and an alternative chunk-prefix strategy for offline models.
      **消融与敏感性:** 论文的主要敏感性轴是 ω，它调节对延迟正确性的折扣程度；表 3 显示当 ω 趋近 1 时许多得分上升，因为时机因素被弱化。附加分析考察了 MMDuet 的重复以及离线模型的替代 chunk-prefix 策略。
      claim_kind:: analyst_assessment
      evidence:: E7, E13, E18
        - ω sensitivity is not just cosmetic: for GPT-4.1-mini, [TV] rises from 48.5 at ω=0 to 59.4 at ω=0.5 and 70.3 at ω=1, showing how final-answer quality gains weight as timing is relaxed.
          ω 的敏感性不仅是表面层面：对于 GPT-4.1-mini，[TV] 从 ω=0 时的 48.5 上升至 ω=0.5 时的 59.4 和 ω=1 时的 70.3，表明随着时机约束放松，最终答案质量的权重逐步增大。
          claim_kind:: analyst_assessment
          evidence:: E7, E13
        - Removing assistant turns from MMDuet improves default PAUC on [TV] from 21.1 to 32.6 and [VAD] from 27.4 to 42.5, while duplicate proportions remain high at 61.2% and 80.9%.
          从 MMDuet 中去除 assistant turns 使 [TV] 的默认 PAUC 从 21.1 提升至 32.6，[VAD] 从 27.4 提升至 42.5，而重复比例仍高达 61.2% 和 80.9%。
          claim_kind:: analyst_assessment
          evidence:: E13, E15
        - The appendix reports that gradually increasing the number of chunks usually fails for open-source models because they generate an answer in the first round and then emit only EOS later.
          附录报告，逐步增加 chunk 数量通常对开源模型失效，因为它们会在第一轮就生成答案，之后只输出 EOS。
          evidence:: E18
    - **Reproducibility Gaps:** The paper provides a project homepage and reports the major dataset sources, model categories, chunk sizes, frame rates, and human-study sampling. Exact reproduction is still under-specified in the provided text for judge prompts, model/API versions, decoding settings, seeds, hardware, and uncertainty estimation.
      **可复现性缺口:** 论文提供了项目主页，并报告了主要数据集来源、模型类别、chunk 大小、帧率以及人类研究的采样方式。但在所供文本中，judge prompts、模型/API 版本、解码设置、随机种子、硬件和不确定性估计等方面仍规格不足，难以精确复现。
      claim_kind:: analyst_assessment
      evidence:: E1, E8, E12, E16
        - Reported reuse anchors are the GitHub project homepage, source datasets, task-level statistics, and coarse offline-inference settings.
          已报告的可复用锚点包括 GitHub 项目主页、源数据集、任务级统计信息以及粗粒度的离线推理设置。
          claim_kind:: analyst_assessment
          evidence:: E1, E8, E9, E12
        - Not reported in the provided text: exact GPT-4.1 judge prompt, API snapshot, temperature/decoding settings, open-source inference hardware, random seeds, and confidence intervals or error bars.
          所提供文本中未报告以下内容：GPT-4.1 judge 的确切提示词、API 快照、temperature/decoding 设置、开源推理硬件、随机种子，以及置信区间或误差棒。
          claim_kind:: analyst_assessment
        - Human-preference sampling and duplicated annotation for 50 examples per task are reported, but the paper gives only kappa summaries and not full adjudication logs or per-annotator calibration.
          论文报告了人工偏好采样与每任务 50 个样本的重复标注，但仅给出了 kappa 汇总，未提供完整的裁定日志或逐标注者校准数据。
          claim_kind:: analyst_assessment
          evidence:: E16, E17
- ## Technical Judgment
    - **What Holds Up:** The main conceptual move holds up: proactive systems should be evaluated as time-indexed streams, and accumulated-response scoring is a reasonable way to credit refinement while making early hallucinations costly. The human-preference study is not decisive, but it supports the intuition that a timing-aware metric is more faithful than final-answer scoring alone.
      **站得住的结论:** 核心概念主张成立：proactive 系统应以时间索引流的方式评估，accumulated-response 评分是合理的方式——既能为精炼信息给予功劳，也让早期幻觉承担代价。人工偏好研究虽非决定性证据，但支持了 timing-aware 指标比仅看最终答案评分更忠实的直觉判断。
      claim_kind:: analyst_assessment
      evidence:: E4, E5, E6, E17
        - The benchmark scope is broad enough to expose qualitatively different failure modes: short web spans, long egocentric procedures, subtitle-heavy TV reasoning, and surveillance anomalies.
          benchmark 范围足够广泛，能够暴露质地上不同的失败模式：短 web 片段、长 egocentric 流程、字幕密集的 TV 推理，以及 surveillance 异常。
          claim_kind:: analyst_assessment
          evidence:: E8, E9
        - PAUC's prefix-based judge input is technically important because it evaluates what the user would have heard so far, not isolated per-turn snippets.
          PAUC 基于 prefix 的 judge 输入在技术上很重要，因为它评估的是用户到目前为止已听到的全部内容，而非孤立的逐轮片段。
          claim_kind:: analyst_assessment
          evidence:: E5, E6
    - **Where It May Fail:** PAUC may fail when gold answer spans are ambiguous, when the LLM judge over- or under-penalizes partial/hallucinated information, or when the chosen ω does not match a user's real tolerance for delay. The low human-human and metric-human agreement levels indicate that timeliness-versus-correctness preferences are noisy, especially on borderline examples.
      **可能失效之处:** 当 gold answer span 含糊不清、LLM judge 对部分/幻觉信息过度或不足惩罚、或所选 ω 不匹配用户对延迟的真实容忍度时，PAUC 可能失效。较低的人与人、指标与人一致性水平表明，时效性与正确性之间的偏好噪声较大，尤其在边界样本上。
      claim_kind:: analyst_assessment
      evidence:: E5, E7, E17
        - Frequent low-quality responses could still be an issue if the judge does not consistently penalize verbosity or contradictions; the paper's duplicate-turn findings show this failure mode is already present.
          如果 judge 不能一致地惩罚冗长或矛盾，频繁输出低质量回复仍可能成为问题；论文的 duplicate-turn 发现表明该失败模式已经存在。
          claim_kind:: analyst_assessment
          evidence:: E6, E15
        - Human performance is not a clean ceiling because the protocol asks annotators to pause and write precisely during playback, which the paper says is cumbersome and unnatural.
          人类表现并非干净的上限，因为协议要求标注者在播放过程中暂停并精确书写，论文称这一过程繁琐且不自然。
          claim_kind:: analyst_assessment
          evidence:: E14
        - Offline-model adaptation is a pragmatic baseline, not a fully fair substitute for native proactive inference, because prompt-following failures and chunk granularity affect when answers can appear.
          Offline-model 的适配是一个务实的 baseline，并非对原生 proactive 推理的完全公平替代，因为 prompt-following 失败和 chunk 粒度会影响答案出现的时机。
          claim_kind:: analyst_assessment
          evidence:: E11, E12, E18
    - **Relation to Other Work:** Compared with MVBench, VideoMME, StreamingBench, OVO-Bench, and OmniMMI as described by the paper, the technical distinction is not just video QA coverage but autonomous response timing plus open-ended multi-answer outputs. Compared with proactive model papers such as VideoLLM-Online, MMDuet, Dispider, and TimeChat-Online, this work contributes an evaluation target rather than a new proactive model architecture.
      **与已有工作的关系:** 与论文所述的 MVBench、VideoMME、StreamingBench、OVO-Bench 和 OmniMMI 相比，技术差异不仅在于 video QA 覆盖范围，更在于自主响应时机加上开放式的多答案输出。与 VideoLLM-Online、MMDuet、Dispider、TimeChat-Online 等 proactive 模型论文相比，本工作贡献的是一个评测目标，而非新的 proactive 模型架构。
      claim_kind:: analyst_assessment
      evidence:: E3, E8, E9, E14
    - **Transferable Lesson:** For interactive multimodal systems, define evaluation as a time-indexed utility curve over accumulated user-visible state, then expose a tunable discount for delay instead of hiding the timing/content tradeoff in a single final transcript score. This pattern should transfer to proactive agents beyond video QA whenever answers arrive incrementally and user value changes over time.
      **可迁移启发:** 对于交互式多模态系统，应将评估定义为基于累积用户可见状态的时间索引效用曲线，然后暴露一个可调的延迟折扣，而不是将时序与内容的权衡隐藏在单一的最终转录评分中。当答案增量到达且用户价值随时间变化时，这种模式应当能超越视频问答，迁移到 proactive agents。
      claim_kind:: analyst_assessment
      evidence:: E4, E6, E7, E17
- ## Glossary
  collapsed:: true
    - Video multimodal large language model: A large language model system that consumes video, and sometimes audio or subtitles, to answer or converse about visual temporal content.
      Video multimodal large language model：一种消耗视频（有时包括音频或字幕）以回答或探讨视觉时序内容的大语言模型系统。
    - Proactive interaction: An interaction mode where the model autonomously decides when to respond during video playback instead of only answering user-triggered turns.
      Proactive interaction：一种交互模式，模型在视频播放期间自主决定何时响应，而不是仅回答用户触发的回合。
    - Proactive Area Under Curve: The paper's metric: for each ground-truth answer span, score accumulated responses over time and normalize the area under the timestamp-score curve.
      Proactive Area Under Curve：本文提出的指标：对于每个 ground-truth answer span，随时间对 accumulated responses 进行评分，并对 timestamp-score 曲线下方的面积进行归一化。
    - Timeliness weight: A hyperparameter in [0,1] that controls how much PAUC discounts late responses; ω=0 emphasizes timeliness, while ω=1 ignores response time.
      Timeliness weight：[0,1] 区间内的一个超参数，控制 PAUC 对延迟回复的折扣程度；ω=0 强调时效性，而 ω=1 忽略回复时间。
    - Ground-truth reply turn: A reference answer paired with a start and end time indicating when the user is expected to receive that information.
      Ground-truth reply turn：带有开始和结束时间的参考答案，指示用户预期接收到该信息的时间。
    - Accumulated responses: The set of all model responses emitted before or at a given timestamp; PAUC judges this prefix rather than each response in isolation.
      Accumulated responses：在给定时间戳之前或当时发出的所有模型回复的集合；PAUC 评判的是这一前缀而非孤立评判每个回复。
    - ProactiveVideoQA task tags: [WEB] is web-video QA, [EGO] is egocentric video QA, [TV] is TV-series QA with speech/subtitle reasoning, and [VAD] is video anomaly detection.
      ProactiveVideoQA task tags：[WEB] 是网络视频问答，[EGO] 是第一人称视角视频问答，[TV] 是带有语音/字幕推理的电视剧问答，[VAD] 是视频异常检测。
    - LLM-as-judge: An evaluator model that scores the semantic correctness of accumulated responses against the question and gold answer; in this paper it uses GPT-4.1 with a 0/1/2 scale.
      LLM-as-judge：一种评估器模型，根据问题和 gold answer 对 accumulated responses 的语义正确性进行评分；在本文中使用 GPT-4.1 并采用 0/1/2 分制。
    - Cohen's kappa: An agreement statistic used in the human-preference study; the paper reports no-weighting and linear-weighting variants as paired values.
      Cohen's kappa：人类偏好研究中使用的一致性统计量；论文报告了无加权和线性加权变体作为成对值。
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/metadata | Title page | high
      locator:: title/authors and intro footnote
      quote:: ProactiveVideoQA: A Comprehensive Benchmark Evaluating Proactive Interactions in Video Large Language Models. Yueqian Wang, Xiaojun Meng, Yifan Wang, Huishuai Zhang, Dongyan Zhao; affiliations include Peking University, Huawei Noah's Ark Lab, University of Science and Technology Beijing, and the National Key Laboratory of General Artificial Intelligence. Project homepage: https://github.com/yellow-binarytree/ProactiveVideoQA
    - **E2:** method/paper_statement | Abstract | medium
      locator:: Abstract
      quote:: we introduce ProactiveVideoQA, the first comprehensive benchmark to evaluate a system's ability to engage in proactive interaction. Since model responses are generated at varying timestamps, we further propose PAUC, the first metric that accounts for the temporal dynamics of model responses.
    - **E3:** gap/paper_statement | 1 Introduction | high
      locator:: gap discussion after interaction paradigms
      quote:: While several models claim to have proactive response capabilities, their evaluations are often conducted on benchmarks that do not actually require such novel interaction. For example, most experiments are performed in offline settings where models are not required to autonomously determine when to respond, and are evaluated using multiple-choice questions rather than open-ended dialogue.
    - **E4:** method/paper_statement | 3 The PAUC Metric | high
      locator:: opening definition and formal setup
      quote:: PAUC plots a timestamp-score curve based on the model's outputs and computes the area under the resulting polyline to represent the model's proactive capabilities. Formally, suppose there are G turns of ground-truth replies in a video, where each reply consists of a textual content gold_g and an associated timespan.
    - **E5:** implementation/implementation_detail | 3 The PAUC Metric | high
      locator:: LLM evaluator scoring paragraph
      quote:: we input the question, the ground-truth answer gold, and the set of model responses generated before τ_p, i.e., {pred_1, pred_2, ..., pred_p}, into a large language model (GPT-4.1 in our implementation). The model is instructed to assign a score reflecting how well this set of accumulated responses aligns with the ground-truth answer.
    - **E6:** formula/paper_statement | 3 The PAUC Metric | high
      locator:: Eq. 1 and following discussion
      quote:: we add two additional points as endpoints of the polyline: (t_start, 0.5) as the initial point and (t_end, s_P) as the final point. The initial score of 0.5 reflects the intuition that providing no response is preferable to giving entirely incorrect answers.
    - **E7:** method/paper_statement | 3.1 Adjusting the Importance of Timeliness | high
      locator:: omega hyperparameter discussion
      quote:: we introduce a hyperparameter ω in [0,1] to balance the importance of timeliness and correctness. When ω = 0 ... timeliness is very important ... In the extreme case of ω = 1 ... equivalent to directly evaluating the correctness of the concatenated responses while completely ignoring their reply times. Here we recommend using ω = 0.5 as the default setting.
    - **E8:** experiment_setup/paper_statement | 4 The ProactiveVideoQA Benchmark | high
      locator:: task list and 4.1.1 Data Source
      quote:: ProactiveVideoQA focuses on four key tasks: proactive web-video QA ([WEB]), proactive ego-centric video QA ([EGO]), proactive TV-series video QA ([TV]), and proactive video anomaly detection ([VAD]). We source video and annotations from Shot2story-MAGQA-39k, Ego4D Goalstep, TVQA, and UCF-Crime.
    - **E9:** experiment_setup/metadata | 4 The ProactiveVideoQA Benchmark | high
      locator:: Tables 1 and 2
      quote:: Table 2 lists ProactiveVideoQA as Video, Audio with 1,377 videos and 1,427 questions, and marks Multi-Answer, Open-Ended, and Proactive. Table 1 reports reply turns: [WEB] 1,328, [EGO] 1,575, [TV] 500, and [VAD] 107.
    - **E10:** implementation/implementation_detail | 4.1.2 Question and Answers in ProactiveVideoQA | high
      locator:: annotation construction paragraph
      quote:: For Shot2story-MAGQA-39k and TVQA, questions, answers, and relevant timespans are already provided ... For Ego4D Goalstep only dense video descriptions are provided ... generate QAs from dense captions. For the [VAD] task ... we manually write a description for each anomaly event as the answer.
    - **E11:** system_design/implementation_detail | 5 Employing Offline Video-Text LLMs for Proactive Interaction | medium
      locator:: offline adaptation strategy
      quote:: we segment each video into fixed-length chunks and, at each timestep, provide the model with the current video chunk, the associated question, and the model's previous response as input. The model is first required to determine whether the current video chunk can answer the question ... only proprietary models are capable of reliably following these multi-step instructions.
    - **E12:** experiment_setup/paper_statement | 6 Experiments | medium
      locator:: experimental setup paragraph
      quote:: We report PAUC metric on ProactiveVideoQA for the following methods: proprietary offline video MLLMs, open-sourced offline video MLLMs, open-sourced proactive video MLLMs, and human performance. For offline models, we use a video chunk size of 2 seconds for [WEB] and 5 seconds for other datasets.
    - **E13:** result/experiment_result | 6.1 Main Results | medium
      locator:: Table 3
      quote:: At ω = 0.5, Table 3 reports Human 38.6/38.2/47.0/53.6; GPT-4.1-mini 47.8/65.8/59.4/47.7; LLaVA-OV 7B 55.0/61.6/45.1/25.6; MMDuet+rm.ass.turns 43.5/52.2/32.6/42.5; and VideoLLM-Online 25.9/25.0/18.3/25.0 for [WEB]/[EGO]/[TV]/[VAD].
    - **E14:** result/paper_statement | 6.1 Main Results | medium
      locator:: observations below Table 3
      quote:: On [TV] and [VAD] tasks, proprietary models significantly outperform both open-source and proactive models. This performance gap can be attributed to the complexity of these tasks ... Proactive models do not demonstrate better results than offline models ... these models tend to repeat previously generated content.
    - **E15:** result/experiment_result | 6.1 Main Results | medium
      locator:: Table 5
      quote:: Table 5 reports the proportion of duplicate predicted turns to all predicted turns excluding the first predicted turn in each ground-truth answer turn: MMDuet 81.3, 99.4, 92.8, 99.2; MMDuet with removed assistant turns 81.1, 92.6, 61.2, 80.9 across [WEB], [EGO], [TV], [VAD].
    - **E16:** experiment_setup/paper_statement | 6.2 Alignment with Human Preferences | medium
      locator:: human study setup paragraph
      quote:: we sample 100 ground-truth reply turns from each task (and 50 answer turns from [VAD]) ... collect two model predictions per sample using the Incremental Chunks method from GPT-4.1-mini and Gemini-2.0-Flash. Human annotators are then asked to indicate their preference between the two predictions.
    - **E17:** result/experiment_result | 6.2 Alignment with Human Preferences | medium
      locator:: Table 4 and discussion
      quote:: Table 4: agreement with human for ω = 1 versus ω = 0.5 is [WEB] 0.23/0.30 versus 0.37/0.40, [EGO] 0.26/0.32 versus 0.30/0.35, [TV] 0.29/0.37 versus 0.34/0.37, [VAD] 0.31/0.36 versus 0.45/0.49. Metrics are Cohen's kappa with no-weighting/linear-weighting.
    - **E18:** limitation/limitation | A.1 Gradually Increasing Number of Chunks | medium
      locator:: appendix alternative offline adaptation
      quote:: in our experiments we found that in almost all cases existing open-source models only generate answers in the first interaction round for each video. In subsequent rounds the models almost never extended their output and simply emitted an EOS token to end their turn instead.
