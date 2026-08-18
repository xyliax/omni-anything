- **Title:** Omni-DuplexEval: Evaluating Real-time Duplex Omni-modal Interaction
- **Summary:** Omni-DuplexEval turns real-time multimodal interaction into an evaluable benchmark by pairing continuous description and proactive reminder tasks with timestamp-aware judging, exposing that current duplex models still miss both sustained content coverage and response timing.
- **Paper Type:** benchmark
- **Venue:** arXiv preprint 2026
- **Authors:** Chaoqun He, Mingyang Xiang, Yingjing Xu, Bokai Xu, Junbo Cui, Jie Zhou, Yuan Yao, Lijie Wen; Tsinghua University, Tongji University, ModelBest Inc.
- **Keywords:** real-time duplex interaction, multimodal large language models, streaming video understanding, omni-modal interaction, LLM-as-a-Judge, temporal alignment
- ## Orientation
    - **Background:** This paper sits in video-and-audio AI evaluation. A real-time assistant sees a stream bit by bit, so its answer is judged not only by what it says but by whether it says it while the relevant moment is happening.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A model can look smart after watching a full video, yet still be a poor live helper if it waits too long, talks at the wrong time, or misses the event the user asked about.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** The system must keep watching and listening, remember the user's goal, decide whether the current moment matters, and speak without having future context.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Evaluate live behavior directly by checking both continuous descriptions and event-triggered reminders against the video timeline.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a benchmark paper for multimodal large language models (MLLMs), where the missing evaluation gap is not final video understanding but whether a system can speak at the right moments while video and audio are still arriving.
      claim_kind:: analyst_assessment
      evidence:: E2, E15
    - **One-Sentence Contribution:** Omni-DuplexEval improves evaluation of real-time video-and-audio assistants by scoring open-ended streaming responses against both their content and their timestamps.
      evidence:: E1, E6
    - **Mental Model:** Imagine judging a live tour guide: it is not enough that the guide eventually names everything correctly; each sentence must match what the viewer can see or hear at that moment, and reminders must fire when the requested event happens.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is the benchmark run showing a large human-model gap, plus diagnostic metrics that separate local timing from global content coverage.
      evidence:: E10, E11, E12
        - Supports C3: Omni-DuplexEval full benchmark; Human-Duplex as real-time human baseline; average score higher is better; MiniCPM-o 4.5 reaches 39.6 versus 81.8 for Human-Duplex; supported, but no variance or repeat count is reported.
          evidence:: E10
        - Supports C4: Real-Time Description metric split; model content and temporal scores compared with human scores; MiniCPM-o 4.5 has 79.9 temporal sensitivity but 38.3 content consistency; supported as a diagnostic gap, with judge-dependence caveat.
          evidence:: E11
        - Supports C3: Proactive Reminder error analysis; error types are No Answer, Partially Correct, and Wrong; MiniCPM-o 4.5 has 49.2% No Answer and MMDuet2 has 75.8% No Answer; supported, but the cause is inferred from their outputs rather than controlled intervention.
          evidence:: E12
    - **Main Caveat:** The benchmark is most trustworthy as a short-interaction diagnostic: the paper itself limits claims about long-term conversation, judge bias, and breadth across real-time public systems.
      claim_kind:: analyst_assessment
      evidence:: E14
- ## Argument Map
    - **Problem and Stakes:** The paper argues that offline video benchmarks miss real-time duplex interaction, meaning a model's ability to process evolving inputs while producing responses at appropriate moments. This matters because practical assistants must coordinate perception, user intent, and speaking time rather than answer after the full clip is known.
      evidence:: E2, E1
    - **Prior Gap:** Prior benchmarks cover offline video QA, streaming inputs, open-ended answers, or proactive event detection in pieces, but the paper claims they do not jointly test open-ended streaming response quality, proactiveness, and temporal alignment. The gap is therefore an evaluation gap, not a new model architecture gap.
      evidence:: E15, E2
    - **Key Insight:** The key insight is to split real-time duplex behavior into two observable patterns: continuous narration that must track a changing stream, and event-triggered reminders that must fire when the requested condition occurs. The evaluation then scores both semantic content and timing instead of treating a final answer as sufficient.
      evidence:: E1, E6, E7
    - **Claims:** The paper's claim chain is that a purpose-built benchmark can expose failures hidden by final-answer video evaluation and can diagnose whether failures come from content, timing, or event-triggering.
      evidence:: E1, E10
        - C1: Omni-DuplexEval covers real-time duplex interaction through 660 open-ended video-and-audio samples, two scenarios, and nine sub-tasks with human timestamp annotations.
          evidence:: E1, E5, E15
        - C2: Its automatic evaluation can score both what the model says and when it says it by combining global content consistency, sentence-level temporal sensitivity, and event-window reminder judgment.
          evidence:: E6, E7, E8
        - C3: Current duplex multimodal models remain far below human real-time performance, especially on Proactive Reminder where deciding when to answer is the dominant failure.
          evidence:: E10, E12
        - C4: In Real-Time Description, models show a timeliness-coverage tradeoff: locally timed sentences can still be too sparse to preserve coherent, holistic video understanding.
          evidence:: E11
- ## Mechanism and Design
    - **Core Mechanism:** Omni-DuplexEval defines two task families: Real-Time Description (RTD), where the model continuously describes a requested aspect of a changing video, and Proactive Reminder (PR), where the model waits for a specified event or correction opportunity before responding. This makes the benchmark test both always-on tracking and trigger-based decision making.
      evidence:: E3, E4
    - **Data / Control Flow:** A sample starts with a user instruction, then the model receives streaming visual and audio input and emits timestamped text. RTD sends each sentence into content and timing judges, while PR extracts model text in a fixed window after each annotated event and judges whether the reminder or correction succeeded.
      evidence:: E5, E6, E7
    - **Design Decisions:** The design choices mostly convert qualitative live interaction into bounded, judgeable units: task taxonomy, human timestamp annotations, sentence-level timing, and strict event success. These choices make the benchmark practical, but they also bind it to short clips and to the reliability of judge prompts.
      evidence:: E3, E4, E6, E7, E14
        - Need: final-answer multiple choice hides timing and free-form response quality; choice: use open-ended questions with human-curated timestamp annotations; closest alternative: offline or discrete QA benchmarks; tradeoff: richer behavior but harder automatic judging.
          evidence:: E5, E15
        - Need: live systems alternate between narration and waiting; choice: split RTD from PR; closest alternative: one generic streaming QA task; tradeoff: clearer diagnosis, but only these two interaction patterns are covered.
          evidence:: E3, E4
        - Need: a good live answer may lag perception slightly; choice: Temporal Sensitivity, a metric for whether a sentence matches its local time window, uses multiple shifted candidate windows and takes the best judge score; tradeoff: tolerant to small latency but dependent on window design.
          evidence:: E6, E8
    - **Implementation Surface:** The paper reports a project URL, native duplex inference protocols for evaluated models, and single-GPU evaluation on NVIDIA A100 hardware; it also gives model-specific streaming details such as chunked audio/video processing and key-value cache (KV cache), the saved attention state reused across turns. The implementation surface is enough to understand benchmark operation, but judge-service versions, seeds, and end-to-end scripts are not fully specified in the text.
      evidence:: E9, E13, E14
- ## Evaluation and Evidence
    - **Setup:** The experiments evaluate four streaming or duplex multimodal baselines, LiveCC, StreamingVLM, MMDuet2, and MiniCPM-o 4.5, using each model's native real-time inference protocol on one NVIDIA A100 GPU. Human-Duplex and Human-Offline provide real-time and offline human reference points rather than trained model baselines.
      evidence:: E9, E13
    - **Claim-Evidence Matrix:** The evidence is strongest for benchmark construction and diagnostic failure patterns, and weaker for broad generalization because the model set is small and the evaluation is judge-based.
      claim_kind:: analyst_assessment
      evidence:: E5, E8, E10, E14
        - Supports C1: the dataset includes 660 short videos, two scenarios, nine sub-tasks, open-ended questions, and human-curated temporal annotations.
          evidence:: E1, E5
        - Supports C2: the paper defines content, timing, and event-window judges, then calibrates Content Consistency above 0.9 Spearman correlation, a rank-correlation measure, and Temporal Sensitivity near 0.8.
          evidence:: E6, E7, E8
        - Supports C3 and C4: Table 2 shows the overall human-model gap, Table 3 separates temporal and content scores, and Table 4 attributes PR failures to no-answer or wrong-answer modes.
          evidence:: E10, E11, E12
    - **Headline Results:** MiniCPM-o 4.5 is the best model overall at 39.6, still far below Human-Duplex at 81.8, and its PR average is only 20.0 despite stronger RTD performance. The reported results support the paper's central diagnosis, but they lack uncertainty intervals or repeated-run statistics.
      evidence:: E10, E11, E12
        - C3 result: full benchmark; baseline Human-Duplex; score higher is better; MiniCPM-o 4.5 gets 39.6 versus 81.8; no uncertainty reported.
          evidence:: E10
        - C4 result: RTD metric split; MiniCPM-o 4.5 gets 79.9 Temporal Sensitivity but 38.3 Content Consistency, while MMDuet2 gets 79.2 and 37.6; timing can look good while global content remains weak.
          evidence:: E11
        - C3 result: PR error table; MMDuet2 has 75.8% No Answer and MiniCPM-o 4.5 has 49.2% No Answer, while LiveCC and StreamingVLM are dominated by Wrong outputs; support for event-triggering weakness.
          evidence:: E12
    - **Ablations and Sensitivity:** The paper reports evaluator-design sensitivity rather than model ablations: Content Consistency works best with two ground-truth references and low frame sampling, while Temporal Sensitivity improves through four-window sampling, sentence-level units, refined prompts, and an irrelevant-sentence penalty. Not applicable: no controlled ablation of model architectures or training choices is reported.
      evidence:: E8
    - **Reproducibility Gaps:** The paper gives a project URL, baseline identities, hardware class, and several inference settings, but the text does not fully report seeds, repeated runs, judge model version stability, dataset access details, or scripts sufficient to reproduce every number from the paper alone. The scarcity of public real-time multimodal systems also narrows the external validity of the benchmark comparison.
      claim_kind:: analyst_assessment
      evidence:: E9, E13, E14
- ## Technical Judgment
    - **What Holds Up:** The most durable contribution is the decomposition of live multimodal behavior into timestamped units that can be audited separately for global content, local timing, and event-trigger success. The benchmark construction and judge calibration make the paper more useful than a single aggregate leaderboard, even though the judge remains an imperfect proxy.
      claim_kind:: analyst_assessment
      evidence:: E5, E6, E7, E8
    - **Where It May Fail:** The conclusions may weaken for longer conversations, memory-heavy tasks, richer interaction styles, or deployments where automatic judge bias matters more than benchmark comparability. Model rankings are also fragile because the evaluated public duplex model set is small and no statistical uncertainty is reported.
      claim_kind:: analyst_assessment
      evidence:: E10, E14
    - **Relation to Other Work:** Against offline video benchmarks, Omni-DuplexEval adds streaming and temporal alignment; against streaming QA benchmarks, it emphasizes open-ended continuous output; against proactive video benchmarks, it adds fine-grained response timing and content checking. The paper positions itself as a unifying evaluation surface rather than as a replacement for long-video comprehension, hallucination, or spoken-dialogue turn-taking benchmarks.
      evidence:: E15, E2
    - **Transferable Lesson:** For real-time AI systems, evaluate behavior as a time-indexed policy rather than a final answer: attach timestamps to outputs, score local timing and global content separately, and make event-triggered tasks require all target events to be handled. This pattern transfers to live assistants, robotics narration, monitoring alerts, and interactive accessibility tools.
      claim_kind:: analyst_assessment
      evidence:: E6, E7
- ## Glossary
  collapsed:: true
    - Multimodal Large Language Model: A language-model-centered system that can process non-text inputs such as images, video, and audio alongside text.
    - real-time duplex interaction: Interaction where the model keeps receiving streaming inputs and can respond during the stream instead of after all input is complete.
    - omni-modal: A model or task setting that combines multiple modalities, especially visual and audio signals in this paper.
    - Real-Time Description: The benchmark scenario where the model continuously describes a requested aspect of a changing video as it unfolds.
    - Proactive Reminder: The benchmark scenario where the model monitors the stream and responds only when a user-specified event or correction condition is met.
    - Content Consistency: A global semantic correctness score for whether the model's response matches the instruction and the video-audio content.
    - Temporal Sensitivity: A timing score for whether each substantive sentence matches the video-audio segment around its timestamp.
    - LLM-as-a-Judge: An evaluation method where a large language model scores or classifies another model's output using a prompt and reference context.
    - event window: For Proactive Reminder, the fixed time span after an annotated event during which model output is collected for judging.
    - Spearman correlation: A rank-based agreement measure used here to compare automatic judge scores with human judgments.
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
