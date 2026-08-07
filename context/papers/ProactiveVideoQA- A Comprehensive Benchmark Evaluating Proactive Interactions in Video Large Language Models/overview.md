- **Title:** ProactiveVideoQA: A Comprehensive Benchmark Evaluating Proactive Interactions in Video Large Language Models
- **Summary:** ProactiveVideoQA and PAUC recast video QA evaluation as a time-varying, open-ended answer-quality curve so models are rewarded for deciding when to speak as well as what to say.
- **Paper Type:** benchmark
- **Venue:** arXiv preprint 2025 (v2, 15 Jul 2025)
- **Authors:** Yueqian Wang (Wangxuan Institute of Computer Technology, Peking University), Xiaojun Meng (Huawei Noah's Ark Lab), Yifan Wang (School of Intelligence Science and Technology, University of Science and Technology Beijing), Huishuai Zhang (Peking University; National Key Laboratory of General Artificial Intelligence), Dongyan Zhao (Peking University; National Key Laboratory of General Artificial Intelligence)
- **Keywords:** proactive video QA, video multimodal large language models, benchmark, PAUC, time-aware evaluation, open-ended QA, streaming video, human preference alignment
- ## Quick Reference
    - **Why Read:** Read this if you need an evaluation lens for video multimodal large language models (Video MLLMs) that must choose when to respond during playback, not merely answer after seeing a full clip.
      claim_kind:: analyst_assessment
      evidence:: E2, E3
    - **One-Sentence Contribution:** ProactiveVideoQA improves evaluation of Video MLLMs in proactive question answering by scoring, over annotated answer spans, how quickly the accumulated answer stream becomes correct rather than only grading the final text.
      evidence:: E2, E4, E8
    - **Mental Model:** Think of a proactive answer stream as a user-experience curve: silence starts above being wrong, correct early information lifts the curve sooner, and wrong early information drags later judgments down.
      claim_kind:: analyst_assessment
      evidence:: E4, E6
    - **Best Evidence:** The strongest evidence is a combination of benchmark coverage, main-model stress tests, and a human-preference comparison between time-aware and time-agnostic scoring.
      evidence:: E9, E13, E17
        - Supports C2: human preference over GPT-4.1-mini versus Gemini-2.0-Flash predictions; baseline is PAUC with timeliness weight ω=1; Cohen's kappa improves at ω=0.5 on web-video ([WEB]) from 0.23/0.30 to 0.37/0.40 and on video anomaly detection ([VAD]) from 0.31/0.36 to 0.45/0.49; moderate support because absolute kappa remains low.
          evidence:: E16, E17
        - Supports C1: benchmark comparison; baseline is prior video QA and streaming benchmarks; ProactiveVideoQA reports video/audio inputs, 1,377 videos, 1,427 questions, multi-answer/open-ended/proactive status, and four task families; direct dataset support.
          evidence:: E8, E9
        - Supports C3: default ω=0.5 benchmark; baseline is the best adapted offline model per task; best proactive model MMDuet with removed assistant turns trails by 11.5 [WEB], 13.6 egocentric ([EGO]), 26.8 television-series ([TV]), and 5.2 [VAD] PAUC points; moderate support without reported uncertainty.
          evidence:: E13
        - Supports C3: duplicate-output analysis; baseline is all predicted turns excluding the first turn in each ground-truth answer turn; MMDuet duplicate proportions are 81.3%, 99.4%, 92.8%, and 99.2% across [WEB]/[EGO]/[TV]/[VAD]; supports redundancy as a failure mode.
          evidence:: E15
    - **Main Caveat:** The metric is only as objective as its annotated answer spans and GPT-4.1 large-language-model judge; the human-preference study itself shows low agreement, so PAUC is a useful proxy rather than a definitive user-experience measure.
      claim_kind:: analyst_assessment
      evidence:: E4, E5, E17
- ## Argument Map
    - **Problem and Stakes:** Video MLLMs are moving from offline or user-triggered online QA toward proactive interaction, where the system continuously monitors playback and autonomously decides when to answer. The stakes are practical real-time settings such as live stream understanding, surveillance, egocentric assistants, and socially interactive agents.
      evidence:: E2, E3
    - **Prior Gap:** Existing evaluations often do not require autonomous response timing: they are offline, multiple-choice, immediate-response streaming tasks, overly simple timing alerts, or single-turn tasks. Conventional text metrics also grade final outputs and miss the temporal evolution of a proactive answer stream.
      evidence:: E3, E4
    - **Key Insight:** The paper's core insight is to evaluate proactive interaction as a time-score curve over each answer span, analogous to a user journey map. Area under this curve rewards earlier correct accumulated responses, while accumulated wrong responses can continue to depress later scores.
      evidence:: E4, E6, E7
    - **Claims:** The paper advances three linked claims about benchmark scope, time-aware metric validity, and the current weakness of evaluated proactive systems.
      evidence:: E2
        - C1: ProactiveVideoQA is a comprehensive benchmark for proactive video QA because it requires open-ended, potentially multi-turn answers across video/audio tasks spanning web videos, egocentric videos, TV-series clips, and surveillance anomaly videos.
          evidence:: E8, E9, E10
        - C2: Proactive Area Under Curve (PAUC) is a better proactive-interaction metric than final-answer evaluation because it jointly scores timing and content, supports task-dependent timeliness through ω, and aligns more closely with human preferences than ω=1 scoring.
          evidence:: E4, E7, E17
        - C3: Existing evaluated systems remain weak at proactive interaction: adapted offline models often beat proactive-specific models, and proactive models frequently repeat prior content.
          evidence:: E13, E14, E15
- ## Mechanism and Design
    - **Core Mechanism:** For each ground-truth reply span, PAUC evaluates the accumulated predictions available at each model response timestamp with GPT-4.1 on a 0/1/2 correctness scale, inserts a starting no-answer score of 0.5 and an end point with the last score, then normalizes the area by span length and maximum score. The video-level PAUC is the average over all ground-truth reply turns.
      evidence:: E5, E6
    - **Data / Control Flow:** A question is presented at the start of the video; the system emits timestamped free-form answers as playback progresses; evaluation groups responses by annotated answer span and scores accumulated answer prefixes. For adapted offline models, the runtime approximation is chunked inference rather than native streaming control.
      evidence:: E5, E8, E11
        - Dataset flow: source videos and annotations are converted into question, answer text, and reply timespan triples, with Ego4D QAs generated from dense captions and [VAD] answers manually written.
          evidence:: E8, E10
        - Offline-model flow: each fixed-length video chunk is paired with the question and, for proprietary models, the previous response so the model can say no answer, same answer, or new answer.
          evidence:: E11, E12
        - Metric flow: for each response timestamp inside a reply span, the judge sees the question, gold answer, and all predictions up to that timestamp, producing the score used in the PAUC curve.
          evidence:: E5, E6
    - **Design Decisions:** The benchmark narrows proactive interaction to QA with annotated answer spans to keep evaluation more objective than fully open-ended dialogue, while still requiring autonomous response timing and free-form multi-turn answers. The metric deliberately exposes a tunable timing-content tradeoff rather than baking in one universal preference.
      claim_kind:: analyst_assessment
      evidence:: E2, E7, E8
        - Need: final-answer metrics ignore when information arrived; design choice: area under an accumulated correctness curve; closest alternative: static BLEU/CIDEr/semantic/LLM scoring; tradeoff: dependence on ground-truth spans and an LLM judge.
          claim_kind:: analyst_assessment
          evidence:: E4, E5, E6
        - Need: applications differ in timeliness pressure; design choice: ω shifts response times left, with ω=0 emphasizing timeliness and ω=1 ignoring time; tradeoff: model rankings can depend on the chosen ω.
          claim_kind:: analyst_assessment
          evidence:: E7, E13
        - Need: few proactive models are open-sourced; design choice: adapt offline Video MLLMs with fixed chunks; closest reported alternative: gradually increasing chunk prefixes; tradeoff: current open-source models often fail the interaction protocol.
          claim_kind:: analyst_assessment
          evidence:: E11, E18
    - **Implementation Surface:** The reported implementation surface includes dataset conversion, timestamped answer spans, chunked offline inference settings, subtitles for TV-series models lacking audio, and GPT-4.1 as the PAUC judge. The paper text gives enough to understand the protocol but not all low-level evaluation parameters needed for exact reproduction.
      claim_kind:: analyst_assessment
      evidence:: E5, E10, E12
        - Reported inference settings include 2-second chunks and 2 fps for [WEB], 5-second chunks and 1 fps for other datasets, and text subtitles injected at utterance timestamps for [TV] when a model lacks audio input.
          evidence:: E12
        - Reported annotation processing includes direct reuse of Shot2story-MAGQA-39k and TVQA spans, generated Ego4D QA pairs, manually written UCF-Crime anomaly descriptions, and merging of near-duplicate adjacent ground-truth turns.
          evidence:: E10
        - For open-source offline models, the paper uses a simplified prompt that asks whether the current chunk contains sufficient information, then performs another inference round for the answer if affirmative.
          evidence:: E11
- ## Evaluation and Evidence
    - **Setup:** Experiments compare proprietary offline Video MLLMs, open-sourced offline Video MLLMs, open-sourced proactive Video MLLMs, and human performance under PAUC. Offline baselines use fixed chunks, [TV] subtitles for models without audio, and human performance is measured with four annotators on 60 videos per dataset.
      evidence:: E12
    - **Claim-Evidence Matrix:** Evidence is strongest for benchmark existence and PAUC's mechanistic definition, moderate for human-preference alignment, and weakest for broad model conclusions because results are point estimates without reported statistical uncertainty.
      claim_kind:: analyst_assessment
      evidence:: E9, E13, E17
        - C1: Directly supported by dataset sources, task definitions, and Tables 1-2; annotation quality for generated/manual QA is less independently validated in the provided text.
          claim_kind:: analyst_assessment
          evidence:: E8, E9, E10
        - C2: Mechanistically supported by PAUC's timestamped accumulated scoring and empirically supported by higher human-preference kappa at ω=0.5 than at ω=1, but the absolute agreement remains low.
          claim_kind:: analyst_assessment
          evidence:: E4, E7, E17
        - C3: Supported by Table 3 and duplicate-turn analysis; validity caveat is that proactive and offline systems differ in training goals and prompting, and no variance or significance tests are reported.
          claim_kind:: analyst_assessment
          evidence:: E13, E15
    - **Headline Results:** At the recommended default ω=0.5, the benchmark reveals a mixed landscape: strong offline models can score well on some tasks, humans are not an easy ceiling under the annotation protocol, and proactive-specific models do not dominate. The results should be read as point estimates because repeat counts, confidence intervals, and statistical tests are not reported in the table.
      claim_kind:: analyst_assessment
      evidence:: E13, E14
        - Task-best default scores in Table 3 are LLaVA-OV 7B at 55.0 on [WEB], GPT-4.1-mini at 65.8 on [EGO], GPT-4.1-mini at 59.4 on [TV], and human annotators at 53.6 on [VAD].
          claim_kind:: analyst_assessment
          evidence:: E13
        - Human-preference alignment improves when timing is included: ω=0.5 beats ω=1 on every task under reported Cohen's kappa, with the largest shown jump on [VAD] from 0.31/0.36 to 0.45/0.49.
          claim_kind:: analyst_assessment
          evidence:: E17
        - Best proactive default scores from MMDuet with removed assistant turns trail best adapted offline scores by 11.5 [WEB], 13.6 [EGO], 26.8 [TV], and 5.2 [VAD] PAUC points.
          claim_kind:: analyst_assessment
          evidence:: E13
    - **Ablations and Sensitivity:** The paper's main sensitivity axis is ω, which changes how much late correctness is discounted; Table 3 shows many scores increasing as ω approaches 1 because timing is de-emphasized. Additional analyses probe MMDuet repetition and an alternative chunk-prefix strategy for offline models.
      claim_kind:: analyst_assessment
      evidence:: E7, E13, E18
        - ω sensitivity is not just cosmetic: for GPT-4.1-mini, [TV] rises from 48.5 at ω=0 to 59.4 at ω=0.5 and 70.3 at ω=1, showing how final-answer quality gains weight as timing is relaxed.
          claim_kind:: analyst_assessment
          evidence:: E7, E13
        - Removing assistant turns from MMDuet improves default PAUC on [TV] from 21.1 to 32.6 and [VAD] from 27.4 to 42.5, while duplicate proportions remain high at 61.2% and 80.9%.
          claim_kind:: analyst_assessment
          evidence:: E13, E15
        - The appendix reports that gradually increasing the number of chunks usually fails for open-source models because they generate an answer in the first round and then emit only EOS later.
          evidence:: E18
    - **Reproducibility Gaps:** The paper provides a project homepage and reports the major dataset sources, model categories, chunk sizes, frame rates, and human-study sampling. Exact reproduction is still under-specified in the provided text for judge prompts, model/API versions, decoding settings, seeds, hardware, and uncertainty estimation.
      claim_kind:: analyst_assessment
      evidence:: E1, E8, E12, E16
        - Reported reuse anchors are the GitHub project homepage, source datasets, task-level statistics, and coarse offline-inference settings.
          claim_kind:: analyst_assessment
          evidence:: E1, E8, E9, E12
        - Not reported in the provided text: exact GPT-4.1 judge prompt, API snapshot, temperature/decoding settings, open-source inference hardware, random seeds, and confidence intervals or error bars.
          claim_kind:: analyst_assessment
        - Human-preference sampling and duplicated annotation for 50 examples per task are reported, but the paper gives only kappa summaries and not full adjudication logs or per-annotator calibration.
          claim_kind:: analyst_assessment
          evidence:: E16, E17
- ## Technical Judgment
    - **What Holds Up:** The main conceptual move holds up: proactive systems should be evaluated as time-indexed streams, and accumulated-response scoring is a reasonable way to credit refinement while making early hallucinations costly. The human-preference study is not decisive, but it supports the intuition that a timing-aware metric is more faithful than final-answer scoring alone.
      claim_kind:: analyst_assessment
      evidence:: E4, E5, E6, E17
        - The benchmark scope is broad enough to expose qualitatively different failure modes: short web spans, long egocentric procedures, subtitle-heavy TV reasoning, and surveillance anomalies.
          claim_kind:: analyst_assessment
          evidence:: E8, E9
        - PAUC's prefix-based judge input is technically important because it evaluates what the user would have heard so far, not isolated per-turn snippets.
          claim_kind:: analyst_assessment
          evidence:: E5, E6
    - **Where It May Fail:** PAUC may fail when gold answer spans are ambiguous, when the LLM judge over- or under-penalizes partial/hallucinated information, or when the chosen ω does not match a user's real tolerance for delay. The low human-human and metric-human agreement levels indicate that timeliness-versus-correctness preferences are noisy, especially on borderline examples.
      claim_kind:: analyst_assessment
      evidence:: E5, E7, E17
        - Frequent low-quality responses could still be an issue if the judge does not consistently penalize verbosity or contradictions; the paper's duplicate-turn findings show this failure mode is already present.
          claim_kind:: analyst_assessment
          evidence:: E6, E15
        - Human performance is not a clean ceiling because the protocol asks annotators to pause and write precisely during playback, which the paper says is cumbersome and unnatural.
          claim_kind:: analyst_assessment
          evidence:: E14
        - Offline-model adaptation is a pragmatic baseline, not a fully fair substitute for native proactive inference, because prompt-following failures and chunk granularity affect when answers can appear.
          claim_kind:: analyst_assessment
          evidence:: E11, E12, E18
    - **Relation to Other Work:** Compared with MVBench, VideoMME, StreamingBench, OVO-Bench, and OmniMMI as described by the paper, the technical distinction is not just video QA coverage but autonomous response timing plus open-ended multi-answer outputs. Compared with proactive model papers such as VideoLLM-Online, MMDuet, Dispider, and TimeChat-Online, this work contributes an evaluation target rather than a new proactive model architecture.
      claim_kind:: analyst_assessment
      evidence:: E3, E8, E9, E14
    - **Transferable Lesson:** For interactive multimodal systems, define evaluation as a time-indexed utility curve over accumulated user-visible state, then expose a tunable discount for delay instead of hiding the timing/content tradeoff in a single final transcript score. This pattern should transfer to proactive agents beyond video QA whenever answers arrive incrementally and user value changes over time.
      claim_kind:: analyst_assessment
      evidence:: E4, E6, E7, E17
- ## Glossary
  collapsed:: true
    - Video multimodal large language model: A large language model system that consumes video, and sometimes audio or subtitles, to answer or converse about visual temporal content.
    - Proactive interaction: An interaction mode where the model autonomously decides when to respond during video playback instead of only answering user-triggered turns.
    - Proactive Area Under Curve: The paper's metric: for each ground-truth answer span, score accumulated responses over time and normalize the area under the timestamp-score curve.
    - Timeliness weight: A hyperparameter in [0,1] that controls how much PAUC discounts late responses; ω=0 emphasizes timeliness, while ω=1 ignores response time.
    - Ground-truth reply turn: A reference answer paired with a start and end time indicating when the user is expected to receive that information.
    - Accumulated responses: The set of all model responses emitted before or at a given timestamp; PAUC judges this prefix rather than each response in isolation.
    - ProactiveVideoQA task tags: [WEB] is web-video QA, [EGO] is egocentric video QA, [TV] is TV-series QA with speech/subtitle reasoning, and [VAD] is video anomaly detection.
    - LLM-as-judge: An evaluator model that scores the semantic correctness of accumulated responses against the question and gold answer; in this paper it uses GPT-4.1 with a 0/1/2 scale.
    - Cohen's kappa: An agreement statistic used in the human-preference study; the paper reports no-weighting and linear-weighting variants as paired values.
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
