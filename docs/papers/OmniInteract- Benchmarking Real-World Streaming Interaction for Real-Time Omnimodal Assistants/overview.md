- **Title:** OmniInteract: Benchmarking Real-World Streaming Interaction for Real-Time Omnimodal Assistants
- **Summary:** OmniInteract turns real-time audio-visual assistance into a measurable benchmark by preserving spoken queries and stream timing, showing that current omnimodal assistants still struggle with when to speak, when to wait, when to stop, and when to resume.
- **Paper Type:** benchmark
- **Venue:** arXiv preprint 2026
- **Authors:** Xudong Lu (CUHK MMLab), Xueying Li (SJTU), Annan Wang (NTU), Yang Bo (McMaster), Jinpeng Chen (CityUHK), Zengliang Li (JUFE), Nianzu Yang (SJTU), Rui Liu (CUHK MMLab), Xue Yang (SJTU), Jingwen Hou (JUFE), Hongsheng Li (CUHK MMLab)
- **Keywords:** omnimodal assistants, streaming interaction, audio-visual benchmark, full-duplex interaction, response timing, interruption handling, nested interaction, 1QnA monitoring
- ## Orientation
    - **Background:** Some assistants now combine video, sound, speech, and text in one system. A live assistant must treat the world as a stream, not as a finished clip.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A person may ask a question aloud, point the camera somewhere, get interrupted, or wait for something to happen. The assistant has to decide whether now is the moment to speak.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** The evidence arrives over time, and speaking too early can be as wrong as saying the wrong thing. The assistant must also remember paused requests while handling new ones.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Mark the moments when a response becomes possible, then judge both the answer and the timing around those moments.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as an evaluation paper for real-time omnimodal large language models, systems that process vision, audio, speech, and text together; it targets the gap between recognizing video content offline and managing a live interaction loop.
      claim_kind:: analyst_assessment
      evidence:: E1, E2
    - **One-Sentence Contribution:** OmniInteract benchmarks live audio-visual assistants by converting a continuous stream into timed response opportunities where the model must detect intent, wait for evidence, answer, and control its speech.
      evidence:: E1, E6
    - **Mental Model:** Picture a person helping while watching a video with you: the hard part is not only knowing the answer, but noticing the right cue, speaking at the right time, pausing when interrupted, and returning to unfinished business.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is that four representative native real-time models remain weak on the benchmark, especially on long-horizon monitoring and nested resumption.
      evidence:: E10, E11, E12, E14
        - Supports C1: benchmark comparison; prior streaming benchmarks mainly use text queries, offline inference, or custom protocols; coverage dimensions add spoken audio queries, native online inference, 1QnA, nested interaction, and interruption; support status: direct design comparison.
          evidence:: E2
        - Supports C3: four native real-time models; closest baseline is the best competing model in the same table; All Global IA-QTF1 tops out at 0.368 and best 1QnA IA-QTF1 at 0.052; support status: moderate because no variance or repeat counts are reported.
          evidence:: E10, E12
        - Supports C4: MiniCPM-o 4.5 mathematical reasoning; baseline is offline full-input inference; pure quality score drops from 0.6833 to 0.3475, a -0.3358 absolute change; support status: moderate because it covers one model and task family.
          evidence:: E14
    - **Main Caveat:** The benchmark is informative but not yet broad enough to establish general real-time assistant capability across languages, domains, model families, or speech conditions.
      claim_kind:: analyst_assessment
      evidence:: E15
- ## Argument Map
    - **Problem and Stakes:** The paper argues that offline video question answering and text-prompted streaming tests miss the live interaction loop of omnimodal large language models, systems that combine visual, audio, speech, and text inputs. The stake is whether a model can detect spoken intent, ground it in unfolding audio-visual evidence, answer at the right time, and avoid disruptive outputs.
      evidence:: E1, E2
    - **Prior Gap:** Prior streaming video benchmarks often keep the video stream but remove the natural query channel by giving text prompts, or they evaluate pre-segmented clips rather than the model's native real-time interface. This decouples perception from spoken intent recognition, timing control, interruption handling, and context resumption.
      evidence:: E2
    - **Key Insight:** A continuous interaction can be evaluated if each expected response is represented as a temporally grounded response opportunity (interaction slot) with a trigger, the first valid answer time, the window close, and a target answer. That turns fuzzy live dialogue into aligned decisions about whether, when, and what to say.
      evidence:: E6
    - **Claims:** The paper's claim chain is best read as four falsifiable claims about benchmark coverage, scoring, model weakness, and offline-online transfer.
      claim_kind:: analyst_assessment
        - C1: OmniInteract covers a missing evaluation setting by preserving spoken audio queries, visual events, ambient sounds, native online inference, 1Q1A local interactions, 1QnA continuous monitoring, nested interactions, and interruptions.
          evidence:: E1, E2, E3
        - C2: The interaction slot formulation plus Interaction-Aware Quality-Timeliness F1 (IA-QTF1), Interruption Diagnostic Suite (IDS), and Nested Chain Completion Score (NCCS) makes content quality, timing, spillover, interruption behavior, and resumption measurable in one benchmark.
          evidence:: E6, E7, E8
        - C3: Current native real-time omnimodal models are weak on this setting, with the best All Global IA-QTF1 reaching 0.368 and the best 1QnA IA-QTF1 reaching only 0.052.
          evidence:: E10, E12
        - C4: Offline multimodal reasoning quality does not reliably transfer to full-duplex real-time interaction, where a model listens and generates at the same time; MiniCPM-o 4.5 loses 0.3358 pure-quality points in the paper's online math setting.
          evidence:: E14
- ## Mechanism and Design
    - **Core Mechanism:** OmniInteract's core mechanism is the interaction slot: a time window from observation start to window close, with an answer becoming valid at a specific moment inside it. Generated chunks are assigned to slots by timestamp, split around the valid-answer time when necessary, and then scored for answer quality and timing.
      evidence:: E6, E7
    - **Data / Control Flow:** The benchmark flow is: construct audio-visual recordings, annotate slots, replay each recording chronologically through the model's native real-time interface, timestamp model chunks, align chunks to slots, and score each slot. The model receives only past and current stream content, not future frames, future audio, or slot boundaries.
      evidence:: E4, E5, E9
        - The 1Q1A split is self-recorded and covers explicit real-time queries, proactive requests whose evidence appears later, and nested cases where an inserted query interrupts an ongoing proactive request.
          evidence:: E3, E4
        - The 1QnA split converts procedural or task-oriented videos into one initial spoken instruction followed by multiple timed response slots for guidance or error detection.
          evidence:: E5
        - Open-ended outputs are judged against ground-truth answers, with the judge also identifying the earliest answer-bearing phrase used to compute the timeliness factor.
          evidence:: E16
    - **Design Decisions:** The benchmark chooses native audio-visual replay over converted text QA, slot-level annotation over free-form transcript review, and targeted diagnostics over one aggregate score. These choices make the benchmark harder to run but closer to the behavior expected from a live assistant.
      claim_kind:: analyst_assessment
      evidence:: E1, E2, E6, E8
        - Need: test whether intent can be recognized from the stream; choice: keep user queries in the audio track; alternative: external text prompts; tradeoff: more realistic but more sensitive to speech recognition and audio conditions.
          evidence:: E1, E2, E15
        - Need: score continuous streams without fixed turns; choice: annotate each response slot with trigger, valid-answer moment, window close, and target answer; alternative: answer-only accuracy; tradeoff: more annotation burden but captures timing failures.
          evidence:: E6, E7
        - Need: distinguish silence, useful partial answers, spillover, and failed resumption; choice: add IDS and NCCS beside IA-QTF1; alternative: one global F1; tradeoff: clearer diagnosis but more judge and timestamp dependence.
          evidence:: E8, E11, E13
    - **Implementation Surface:** The implementation surface implied by the paper includes replaying audio and frames through each model's native real-time interface, capturing timestamped output chunks, running slot alignment, and using external judge prompts for semantic scoring. The paper promises public code and datasets, but the provided text does not establish released artifact state, hardware budgets, or run-script completeness.
      claim_kind:: analyst_assessment
      evidence:: E1, E9, E16
- ## Evaluation and Evidence
    - **Setup:** The experiments test AURA, Gemini 2.5 Flash Live, MiniCPM-o 4.5, and Qwen3.5-Omni Flash Realtime under chronological replay through their native real-time pipelines. GPT-4o is used as an external semantic judge for open-ended answers, while timing and slot alignment are computed from replay timestamps.
      evidence:: E9, E16
    - **Claim-Evidence Matrix:** The evidence most directly supports the benchmark-definition claims, moderately supports model-performance claims, and weakly supports broad generalization beyond the tested models, domains, and languages.
      claim_kind:: analyst_assessment
      evidence:: E2, E3, E10, E15
        - C1 is supported by the benchmark comparison and dataset composition: OmniInteract adds spoken audio queries, native online inference, 1QnA monitoring, nested slots, and interruption cases relative to prior categories.
          evidence:: E2, E3
        - C2 is supported by formal slot definitions and metric definitions for soft true positives, false positives, no-output rate, partial answer quality, conditional spill, and nested chain completion.
          evidence:: E6, E7, E8
        - C3 and C4 are supported by reported model tables, but the support is bounded because the paper reports point estimates rather than statistical uncertainty, and the offline-online degradation analysis is limited to MiniCPM-o 4.5 mathematical reasoning.
          claim_kind:: analyst_assessment
          evidence:: E10, E12, E14, E15
    - **Headline Results:** The headline result is not a single winning model but a pattern: models that do reasonably on explicit real-time queries still fail on monitoring, resumption, interruption control, or online reasoning. MiniCPM-o has the best All Global IA-QTF1 at 0.368, while AURA has the best 1QnA IA-QTF1 at only 0.052.
      evidence:: E10, E12, E13, E14
        - Supported claim: explicit questions are easier than proactive monitoring for some models; configuration: 1Q1A categories; baseline: other tested models; metric: IA-QTF1; direction: Gemini leads real-time at 0.553, MiniCPM-o leads proactive at 0.607; caveat: no uncertainty reported.
          evidence:: E10
        - Supported claim: local inner-query answering does not guarantee outer-task resumption; configuration: 120 nested pairs; baseline: other tested models; metric: NCCS and missed outer count; direction: Gemini and Qwen3.5-Omni miss 119 and 116 outer resumptions; caveat: benchmark-specific pair design.
          evidence:: E11
        - Supported claim: interruption behavior has a quality-control tradeoff; configuration: interrupted slots and MiniCPM-o math comparison; metrics: NOR, PAQ, CSM, pure quality score; direction: MiniCPM-o gives better partial answers but spills more, and online reasoning drops by 0.3358; caveat: one full-duplex model in the degradation test.
          evidence:: E13, E14
    - **Ablations and Sensitivity:** Not applicable: no controlled ablation or statistical sensitivity study is reported; the paper instead provides diagnostic breakdowns by interaction type, interruption behavior, nested resumption, and offline-online setting.
      claim_kind:: analyst_assessment
    - **Reproducibility Gaps:** The paper gives useful reuse hooks, including data-license notes and judge prompt templates, and says code and datasets will be public. Missing trust fields in the provided text include confirmed released repository state, exact hardware/resource budgets, repeat counts, confidence intervals, and end-to-end scripts for all native model interfaces.
      claim_kind:: analyst_assessment
      evidence:: E1, E15, E16
- ## Technical Judgment
    - **What Holds Up:** The benchmark's main technical contribution holds up because it evaluates the whole live loop rather than only answer correctness: spoken-query recognition, temporal grounding, answer content, spillover, interruptions, and resumption are all represented in the scoring design. The case is strongest for defining a benchmark gap and weakest for ranking model families definitively.
      claim_kind:: analyst_assessment
      evidence:: E2, E6, E7, E8, E9
    - **Where It May Fail:** Generality may fail when moving beyond the covered languages, domains, speech styles, and model set, especially because 1QnA uses synthesized initial instructions and the full-duplex degradation study is limited to one open-source model on mathematical reasoning. The judge-based scoring also makes semantic evaluation depend on prompt stability and external model behavior.
      claim_kind:: analyst_assessment
      evidence:: E15, E16
    - **Relation to Other Work:** Relative to offline and text-prompted streaming video benchmarks, OmniInteract shifts the evaluation axis from understanding a video to managing a spoken, audio-visual interaction over time. Relative to full-duplex voice benchmarks, it adds visual grounding and temporally annotated response opportunities rather than focusing only on speech turn-taking.
      claim_kind:: analyst_assessment
      evidence:: E2, E8
    - **Transferable Lesson:** For streaming-agent evaluation, expose the hidden control problem by annotating when an answer becomes valid and when it becomes disruptive. A benchmark that scores only final answer text can miss the failures that make a live assistant unusable.
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E8
- ## Glossary
  collapsed:: true
    - omnimodal large language model: A model family that handles multiple interaction channels, especially vision, audio, speech, and text, in one system.
    - online streaming inference: Running the model as the audio-visual stream unfolds, so it can use past and current inputs but not future content.
    - interaction slot: A temporally grounded response opportunity with an observation start, earliest valid answer time, window close, and target answer.
    - 1Q1A: A setting where one trigger corresponds to one expected answer; OmniInteract includes real-time, proactive, and nested variants.
    - 1QnA: A setting where one spoken instruction can require multiple timed responses as a task unfolds.
    - full-duplex real-time interaction: Interaction where the model processes incoming input while generating output, so listening and speaking overlap.
    - Interaction-Aware Quality-Timeliness F1: The paper's global score combining soft true positives for quality and timeliness with penalties for missing or disruptive outputs.
    - Interruption Diagnostic Suite: A diagnostic set separating no output, useful partial answer quality, and conditional spillover during interrupted slots.
    - Nested Chain Completion Score: A geometric-mean score for nested interactions that requires both the inserted inner answer and resumed outer answer to be correct.
    - spillover: Model output that continues beyond a slot boundary and can disrupt the next interaction context.
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
