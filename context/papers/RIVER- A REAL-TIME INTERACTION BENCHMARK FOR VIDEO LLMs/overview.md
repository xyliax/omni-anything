- **Title:** RIVER: A Real-Time Interaction Benchmark for Video LLMs
- **Summary:** RIVER reframes video-LLM evaluation around timed human interaction, showing that models need memory, live perception, and future-triggered responses rather than only whole-video question answering.
- **Paper Type:** benchmark
- **Venue:** ICLR 2026
- **Authors:** Yansong Shi (University of Science and Technology of China; Shanghai Artificial Intelligence Laboratory), Qingsong Zhao (Fudan University; Shanghai Artificial Intelligence Laboratory), Tianxiang Jiang (University of Science and Technology of China; Shanghai Artificial Intelligence Laboratory), Xiangyu Zeng (Nanjing University; Shanghai Artificial Intelligence Laboratory), Yi Wang (Shanghai Artificial Intelligence Laboratory), Limin Wang (Nanjing University; Shanghai Artificial Intelligence Laboratory)
- **Keywords:** video LLM, online multimodal interaction, streaming video understanding, retrospective memory, live perception, proactive response, benchmark, long-short term memory
- ## Orientation
    - **Background:** Video language models answer questions about moving visual scenes. A streaming interaction is harder than a normal video quiz because the model sees the video over time while a person may ask, wait, or expect an interruption.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A helpful assistant should remember where something was, describe what is happening now, and speak up only when the right future event appears.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** The model must keep useful past details without storing everything, notice current evidence quickly, and avoid answering too early when the visual clue has not happened yet.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Turn live video dialogue into timed questions about past, present, and future visual clues, then score both answer correctness and response timing.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a benchmark paper for online video-language systems: it targets the gap between whole-video QA and interaction where a model must remember past visual evidence, answer about the current scene, and wait for future visual cues.
      claim_kind:: analyst_assessment
      evidence:: E2, E3, E18
    - **One-Sentence Contribution:** RIVER improves evaluation of video large language models in streaming interaction by anchoring questions, visual cues, and responses to explicit times instead of treating the whole video as one offline input.
      evidence:: E3, E4
    - **Mental Model:** Picture a person watching a live camera feed for you: sometimes you ask what just happened, sometimes what is happening now, and sometimes you ask the watcher to interrupt only when a named event appears.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is the cross-model evaluation showing that strong offline QA performance does not transfer cleanly to real-time memory and proactive response.
      evidence:: E12, E13, E14
        - Supports C1: RIVER is compared with prior online-video benchmarks; baseline benchmarks lack several temporal-memory intervals and instant-stream anticipation; metric coverage is broader; support is direct but based on the authors' benchmark taxonomy.
          evidence:: E4, E18
        - Supports C2: offline video MLLMs adapted to 1 fps streaming are compared with fixed-frame variants; retro-memory and live-perception scores change by task and model; support is moderate because no uncertainty is reported.
          evidence:: E10, E12, E14
        - Supports C3: VideoLLM-Online plus RIVER training at 4 fps is compared with VideoLLM-Online at 2 fps; pro-response localization rises from 23.88 to 35.16 and MC from 6.67 to 10.53; support is moderate because repeat counts are not reported.
          evidence:: E13
    - **Main Caveat:** The benchmark is video-only and the reported results mostly lack variance, repeat counts, and error bars, so it is better read as a useful stress test than as a fully calibrated estimate of deployment reliability.
      claim_kind:: analyst_assessment
      evidence:: E12, E17
- ## Argument Map
    - **Problem and Stakes:** The paper argues that multimodal large language models (MLLMs), models that combine language reasoning with visual input, are mostly evaluated as offline whole-video question answerers, while practical assistants need online multimodal language models (oMLLMs), models that react while a video stream is still arriving.
      evidence:: E2, E3
    - **Prior Gap:** Prior online-video benchmarks cover pieces of the problem but do not jointly formalize memory intervals, live perception, proactive response, and fine-grained timing between cue, question, and answer.
      evidence:: E2, E18
    - **Key Insight:** The useful unit of evaluation is not just whether a model can answer a video question, but whether it answers from the correct temporal relationship: past cue, current cue, or future cue.
      claim_kind:: analyst_assessment
      evidence:: E5, E8
    - **Claims:** The paper's core argument is captured by four falsifiable claims.
      claim_kind:: analyst_assessment
        - C1: RIVER Bench formalizes online video interaction as Retrospective Memory, Live-Perception, and Proactive Response tasks with explicit temporal relationships and broader coverage than prior benchmarks.
          evidence:: E3, E4, E5
        - C2: A sliding-window online adaptation with long-short term visual memory can make offline video MLLMs operate in streaming settings and reduce degradation on medium-to-long memory questions.
          evidence:: E10, E14, E15
        - C3: Training with RIVER-style proactive interaction data improves VideoLLM-Online on Pro-Response localization and answer metrics.
          evidence:: E11, E13
        - C4: Questions requiring causal visual cues, where the answer depends on event dynamics and temporal dependencies, are harder than fine-grained object cues or background cues for the evaluated models.
          evidence:: E16
- ## Mechanism and Design
    - **Core Mechanism:** RIVER's benchmark mechanism is a timed video-text-to-text interaction: each item specifies a visual cue time, a user query time, and an expected response time, then evaluates whether the model answers correctly and at the right moment.
      evidence:: E5, E8
    - **Data / Control Flow:** The data flow starts from existing video QA and dense timestamped event annotations, filters out language-only and ambiguous cases, rewrites them into timed interaction formats, and evaluates model outputs with task-specific answer and timing rules.
      evidence:: E6, E7, E8
        - For Retrospective Memory and Live-Perception, RIVER samples a query time after or around the referenced event so the same visual fact becomes either a memory test or a current-perception test.
          evidence:: E6
        - For Pro-Response, instant questions require a single future-triggered answer, while stream questions require repeated descriptions or guidance over time.
          evidence:: E6
        - Multiple-choice answers are extracted with regular expressions when possible, open-ended answers are judged by Qwen2.5-72B, and proactive timing is scored with early false alarms set to zero and late answers decayed.
          evidence:: E8
    - **Design Decisions:** The design choices mainly protect temporal validity: force one grounded visual moment per answer, separate past/current/future relationships, and compress old visual context instead of letting the model see an unlimited stream.
      evidence:: E6, E7, E10
        - Need: avoid questions answerable from broad context; choice: require precise cue, query, and response times; closest alternative: conventional whole-video QA; tradeoff: higher annotation burden.
          evidence:: E6, E7
        - Need: keep old visual evidence under bounded memory; choice: a sliding window plus long-term compressed tokens selected by nearest-neighbor averaging; closest alternative: keep only recent frames; tradeoff: compression may blur fine details.
          evidence:: E10
        - Need: distinguish useful waiting from premature alerts; choice: score responses inside the tolerance window fully, early responses as zero, and late responses with linear decay; tradeoff: the window encodes a human-tolerance assumption.
          evidence:: E8
    - **Implementation Surface:** The evaluated surface includes closed-source models, native streaming models, offline open-source video MLLMs adapted with 1 fps sliding windows, and a VideoLLM-Online-style trained model using SigLIP visual features, an MLP connector, LLaMA3-8B, and LoRA.
      evidence:: E9, E10, E11
- ## Evaluation and Evidence
    - **Setup:** The evaluation compares model families under RIVER's three task types, using recommended frame sampling for offline models, streaming frame rates for online models, multiple-choice and open-ended answer metrics, and proactive localization scores.
      evidence:: E8, E9, E12
    - **Claim-Evidence Matrix:** The evidence is strongest for benchmark coverage and moderately strong for model conclusions because the paper reports broad comparisons but not statistical uncertainty.
      claim_kind:: analyst_assessment
      evidence:: E4, E12, E13, E14
        - C1: supported by Table 1, task definitions, and comparison to OVO-Bench; the caveat is that coverage categories are the authors' taxonomy rather than an external standard.
          evidence:: E4, E5, E18
        - C2: supported by the long-short term memory design, retro-memory duration table, and memory curve; the caveat is no reported variance or controlled model-by-model ablation for every architecture.
          evidence:: E10, E14, E15
        - C3 and C4: supported by proactive training results and clue-category breakdown; the caveat is that generated proactive questions and LLM-judged open-ended metrics add evaluator dependence.
          evidence:: E13, E16
    - **Headline Results:** The headline pattern is that whole-video strength does not imply online interaction strength: GPT-4o leads the aggregate table, adapted offline models become competitive on live perception, and native streaming models remain weak on RIVER's interactive QA.
      evidence:: E12, E13, E14
        - VideoLLM-Online+RIVER at 4 fps improves Pro-Response Loc by 11.28 points over VideoLLM-Online at 2 fps, with smaller gains on MC and OE, but the table does not report repeat counts.
          evidence:: E13
        - Retro-memory performance generally declines as the recall interval grows, while memory-based designs are presented as stabilizing retrieval over longer windows.
          evidence:: E14, E15
    - **Ablations and Sensitivity:** The paper's main sensitivity evidence is not a dense ablation grid but two targeted probes: memory versus no-memory decay, and performance by visual cue type.
      evidence:: E15, E16
        - Memory modules reduce the reported decay slope by 12%, suggesting that explicit compressed memory helps when the queried evidence is no longer in the current visual window.
          evidence:: E15
        - Causal cues remain difficult across methods, implying that online evaluation exposes event-attribution weaknesses beyond object or scene recognition.
          evidence:: E16
    - **Reproducibility Gaps:** The paper states that code, data processing, benchmark simulation, and evaluation will be released, but original videos follow index-only release rules; not reported: statistical uncertainty, repeated runs, detailed cost budgets, and full prompt sensitivity.
      claim_kind:: analyst_assessment
      evidence:: E8, E11, E17
- ## Technical Judgment
    - **What Holds Up:** The benchmark framing is the durable part: explicit cue, question, and response times give a cleaner test of streaming behavior than whole-video QA, and the three-task split maps to concrete assistant use cases.
      claim_kind:: analyst_assessment
      evidence:: E3, E5, E8
    - **Where It May Fail:** RIVER may understate multimodal interaction needs because it excludes audio, relies partly on generated proactive QA and LLM-based open-ended judging, and reports tables without variance or repeat-count evidence.
      claim_kind:: analyst_assessment
      evidence:: E7, E8, E12, E17
    - **Relation to Other Work:** Relative to offline video benchmarks, RIVER changes the unit of evaluation from holistic video understanding to timed interaction; relative to OVO-Bench and related online benchmarks, it emphasizes finer response and clue intervals plus memory curves.
      evidence:: E2, E18
    - **Transferable Lesson:** For streaming AI systems, evaluation should encode when evidence becomes available and when an answer becomes useful; adding time to the task definition can expose failures that static accuracy hides.
      claim_kind:: analyst_assessment
      evidence:: E5, E8, E12
- ## Glossary
  collapsed:: true
    - Multimodal large language model: A language model that can condition on non-text inputs such as images or video frames; in this note, it usually means a video-capable model.
    - Online multimodal large language model: A multimodal model expected to process a stream as it arrives and answer during the stream, not only after seeing the whole video.
    - Temporal interaction: An evaluation format where the visual cue, user question, and model answer each have positions on the video timeline.
    - Retrospective Memory: A task where the model answers a current question using evidence from an earlier moment in the video.
    - Live-Perception: A task where the referenced visual evidence is in the current or very recent video window, so the model should answer immediately.
    - Proactive Response: A task where the model must wait for a future visual condition and respond when that condition is observed.
    - Sliding window: A streaming strategy that processes only a recent span of frames at each step, then advances the span as time moves forward.
    - Long-short term memory module: RIVER's adaptation pattern: keep current-window frame tokens as short-term memory and compressed earlier tokens as long-term memory.
    - Open-ended evaluation: A model-judged answer-consistency check used when the output is not cleanly extractable as a multiple-choice option.
    - Low-Rank Adaptation: A parameter-efficient fine-tuning method that trains small low-rank updates inside a larger neural network instead of updating all parameters.
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
