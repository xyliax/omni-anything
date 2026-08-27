- **Title:** ROMA: Real-time Omni-Multimodal Assistant with Interactive Streaming Understanding
- **Summary:** ROMA shows that a streaming audio-video assistant can combine proactive response timing and reactive question answering by separating when to speak from what to generate while keeping audio and video aligned over time.
- **Paper Type:** system
- **Venue:** arXiv preprint 2026
- **Authors:** Xueyun Tian (University of Chinese Academy of Sciences), Wei Li, Bingbing Xu (Institute of Computing Technology, CAS), Heng Dong (Tsinghua University), Yuanzhuo Wang (Institute of Computing Technology, CAS), Huawei Shen (University of Chinese Academy of Sciences)
- **Keywords:** streaming multimodal understanding, omni-multimodal assistants, proactive interaction, audio-video alignment, response timing, streaming evaluation
- ## Orientation
    - **Background:** This paper sits in live assistant models that process speech, images, and text as events unfold. The key prerequisite is streaming: the model must use only what has already happened, not the whole recording.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A useful assistant should not only answer questions after being asked; it should also keep watching and listening, then speak when something requested actually happens.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** Sound arrives continuously, images arrive as separate snapshots, and the assistant must decide when to interrupt without seeing the future.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Keep sound and images on the same timeline, then use a small gate to decide when the main speaker should talk.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a streaming multimodal-systems paper about the gap between models that answer after being asked and assistants that must watch, listen, wait, and speak at the right moment.
      claim_kind:: analyst_assessment
      evidence:: E2, E3
    - **One-Sentence Contribution:** ROMA improves real-time audio-video assistance by making response timing an explicit online decision before text generation, rather than forcing the language model to express silence or speech as ordinary words.
      evidence:: E1, E6
    - **Mental Model:** Picture a live commentator with a mute button: one part keeps watching and listening, another part decides whether the moment is worth speaking about, and only then does the speaker produce the sentence.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is not one benchmark score but the pattern: ROMA improves proactive alert and narration timing, while reactive question answering remains competitive.
      evidence:: E10, E11, E12
        - Supports C3: QVHighlights and Charades-STA static grounding plus PA/PO/REC dynamic alerts; streaming-capable baselines; localization and success metrics; large gains on QVHighlights mAP and PO/REC, mixed on CRR; supported without variance reporting.
          evidence:: E10
        - Supports C3: YouCook2 and OVO-Bench SSR narration; VideoLLM-online and MMDuet baselines; F1, BERTScore, and GPT-4o judging; best F1 and GPT scores, similar BERTScore; supported without statistical uncertainty.
          evidence:: E11
        - Supports C4: ablations replace the speak head or reduce the layer aggregation; token-based triggering and K=1 variants; dynamic alert and narration metrics drop sharply; supported as a component ablation without repeat counts.
          evidence:: E13
    - **Main Caveat:** The paper's evidence is strongest for curated streaming tasks and finite clips; it explicitly leaves degraded signals, audio-video asynchrony, very long dependencies, and strict efficiency-quality tradeoffs as open risks.
      claim_kind:: analyst_assessment
      evidence:: E15
- ## Argument Map
    - **Problem and Stakes:** The paper frames streaming audio-video understanding as a unified interaction problem: reactive question answering (QA), where the model answers after a query, and proactive monitoring, where it must trigger alerts or narration from the stream prefix only. This matters because a real assistant must combine perception, timing, and language rather than solve isolated offline video tasks.
      evidence:: E2, E9
    - **Prior Gap:** The paper argues that prior systems split along the wrong axes: speech-first streaming models often lack visual perception, video-streaming models often ignore synchronized audio, and many benchmark protocols test question injection rather than autonomous response timing.
      evidence:: E3, E17
    - **Key Insight:** The load-bearing insight is to separate the two jobs hidden inside live interaction: keep multimodal evidence causally aligned as it arrives, and make the speak-or-wait decision through a dedicated timing signal before generating text.
      evidence:: E4, E5, E6
    - **Claims:** The paper's argument reduces to four falsifiable claims about unified streaming interaction, training, evaluation, and the timing module.
      claim_kind:: analyst_assessment
        - C1: ROMA can represent live audio and video as causally ordered aligned units, enabling one model to support proactive alerting, real-time narration, and reactive QA.
          evidence:: E1, E4, E9
        - C2: A curated streaming dataset plus two-stage fine-tuning can transfer a strong offline omni-multimodal foundation model into an online model with calibrated response timing.
          evidence:: E7, E13
        - C3: Under the paper's unified evaluation suite, ROMA achieves state-of-the-art proactive alert and narration results while remaining competitive on reactive and full-modality QA.
          evidence:: E10, E11, E12
        - C4: Decoupling response timing into a speak head, especially with information from multiple upper layers, is important for proactive triggering and not merely an implementation detail.
          evidence:: E6, E13
- ## Mechanism and Design
    - **Core Mechanism:** ROMA splits the stream into fixed-duration audio-video chunks, packages dense audio tokens and sparse video-frame tokens together, and assigns them aligned time positions through Time-aligned Multimodal RoPE (TMRoPE, a position-coding scheme that tells the transformer which audio and visual tokens share time). A separate speak head then scores each stream prefix for whether a response should begin, while the normal language modeling head generates content only after that trigger.
      evidence:: E4, E5, E6
    - **Data / Control Flow:** At inference time, each new unit is encoded, appended to the ongoing temporal sequence, and evaluated by the speak head; if the probability crosses the task threshold, the language model emits a response, otherwise ROMA stays silent and consumes the next unit. The system keeps a key-value cache (KV cache, stored attention state from earlier tokens) so each step can reuse prior context instead of re-encoding the whole stream.
      evidence:: E6, E8
        - Packaging step: audio and video from the same interval are wrapped in the base Qwen2.5-Omni token format, preserving compatibility with the foundation model while imposing a streaming order.
          evidence:: E4
        - Timeline step: video tokens inside a unit share the unit's time position, audio tokens keep finer temporal positions, and later units continue from the previous maximum position ID.
          evidence:: E5
        - Trigger step: the speak head reads a learned weighted combination of the last K hidden layers, with K set to four in the reported experiments, and converts it into a binary speak probability.
          evidence:: E6
    - **Design Decisions:** The major design choices all reduce interference: align modalities before reasoning, score timing outside generation, and train streaming format adaptation before timing specialization. The tradeoff is more task-specific supervision and threshold calibration rather than a purely prompt-only use of the base model.
      evidence:: E5, E6, E7, E14
        - Need: audio is dense and video is sparse; choice: synchronized chunks plus chunked TMRoPE; closest alternative in the paper is treating modalities or full videos less causally; tradeoff: video timing is coarser inside each unit while audio keeps fine positions.
          evidence:: E4, E5
        - Need: the model must decide when to speak without confusing timing with content; choice: a two-layer neural timing classifier parallel to the language head; closest alternative is a silence token; tradeoff: explicit probabilities require thresholds and positive-label balancing.
          evidence:: E6, E13, E14
        - Need: the base model was optimized for complete inputs; choice: first adapt to streaming templates, then learn time-aware decisions while mixing QA data; closest alternative is single-stage mixed training; tradeoff: more pipeline complexity but better proactive calibration.
          evidence:: E7, E13
    - **Implementation Surface:** ROMA is implemented as an adaptation of Qwen2.5-Omni with frozen encoders, fine-tuned remaining parameters, two-stage training, and streaming decoding that samples video at 2 fps, caps frame size at 65,536 pixels, and uses a persistent KV cache. Appendix details report LLaMA-Factory training with sequence length 32K, 32 H20 GPUs, global batch size 512, and a 25-token per-segment generation budget for the pipelined real-time approximation.
      evidence:: E8, E16
- ## Evaluation and Evidence
    - **Setup:** The evaluation reorganizes fragmented streaming benchmarks into proactive interaction and reactive interaction: proactive covers event-driven alerts and real-time narration, while reactive covers causal-history QA. Baselines are limited to streaming-capable video models for proactive tasks and include open-source omni-modal models for full-modality QA with spoken queries.
      evidence:: E9, E12
    - **Claim-Evidence Matrix:** The evidence is strongest where the same mechanism is tested through both benchmark comparisons and ablations; it is weaker where results rely on single reported runs, judge prompts, or benchmark reformulations.
      claim_kind:: analyst_assessment
      evidence:: E10, E11, E13
        - C1 is supported by the framework coverage and implementation path: the paper tests alert, narration, and QA under one streaming protocol, but the strongest proof is functional rather than a formal systems invariant.
          claim_kind:: analyst_assessment
          evidence:: E8, E9
        - C3 is supported by headline proactive gains on QVHighlights, dynamic alerts, and narration, plus competitive QA; support is medium because the paper does not report variance, seeds, or confidence intervals.
          claim_kind:: analyst_assessment
          evidence:: E10, E11, E12
        - C4 is supported most directly by the speak-head and K=1 ablations: proactive timing drops more sharply than timestamp-conditioned understanding, matching the claimed role of the timing module.
          claim_kind:: analyst_assessment
          evidence:: E13
    - **Headline Results:** The main result pattern is proactive strength: ROMA reports 53.7 mean average precision (mAP) on QVHighlights, 44.3/19.9 recall at 0.5/0.7 overlap on Charades-STA, best reported dynamic alert scores on PA and PO, and best recurring-alert score on REC. For narration, it reports 35.21 F1 on YouCook2 and 14.54 F1 on OVO-Bench SSR, with the highest GPT-4o judge averages but BERTScore close to baselines.
      evidence:: E10, E11
        - Supported claim: better temporal grounding; configuration: QVHighlights and Charades-STA; closest baseline: MMDuet on the same tables; metric direction: higher is better; delta: QVHighlights mAP 53.7 vs 31.3, Charades R@0.5 44.3 vs 42.4.
          evidence:: E10
        - Supported claim: better online narration timing; configuration: YouCook2 and OVO-Bench SSR; closest baseline: MMDuet or VideoLLM-online depending metric; metric direction: higher is better; delta: YouCook2 F1 35.21 vs 18.82 for VideoLLM-online and 17.81 for MMDuet.
          evidence:: E11
        - Supported claim: reactive competence is mostly retained; configuration: OVO-Bench, StreamingBench, Video-MME, and EgoSchema; baselines include Dispider and omni-modal models; caveat: some subcategories remain close or below baselines.
          evidence:: E12
    - **Ablations and Sensitivity:** The ablations support the curriculum and timing design: single-stage mixed training degrades online triggering, removing the speak head hurts proactive alert and narration most, and using only the last layer weakens temporal grounding and dynamic triggering. The positive-class weight w_pos, the multiplier on rare speak labels in the binary timing loss, matters for proactive tasks but has little effect on reactive QA.
      evidence:: E13, E14
    - **Reproducibility Gaps:** The paper reports training hardware, sequence length, batch size, data sources, evaluation prompts, and several decoding thresholds, which helps audit the setup. Not reported in the provided text: model-weight availability, exact re-annotated timestamp data, training seeds, repeat counts, variance, and a full script-level reproduction path for every benchmark reformulation.
      claim_kind:: analyst_assessment
      evidence:: E14, E16, E17
- ## Technical Judgment
    - **What Holds Up:** The most credible part is the architectural separation between timing and generation: it directly matches the problem structure and is backed by large proactive-task drops when replaced by token-level silence behavior. The aligned-chunk representation is also plausible because it addresses the concrete audio-video granularity mismatch rather than relying only on prompting.
      claim_kind:: analyst_assessment
      evidence:: E4, E6, E13
    - **Where It May Fail:** Benefits may diminish when audio and video are badly desynchronized, when important evidence lies beyond the finite context window, or when the assistant needs long, high-quality responses under a strict real-time budget. The 25-token per-segment decoding cap and finite-context training setup make this boundary concrete rather than hypothetical.
      claim_kind:: analyst_assessment
      evidence:: E15, E16
    - **Relation to Other Work:** Compared with memory or KV-cache based streaming video QA systems, ROMA is less about compressing long histories and more about deciding whether the current prefix warrants action. Compared with proactive video-only assistants, its technical distinction is synchronized audio-video input; compared with omni-modal reactive models, its distinction is explicit proactive response timing.
      evidence:: E3, E17
    - **Transferable Lesson:** For live multimodal systems, do not hide control policy inside generation tokens when the product behavior is a timing decision; represent the control signal directly, supervise it at the lifecycle point where it is used, and keep the content generator trained on ordinary language quality.
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E13
- ## Glossary
  collapsed:: true
    - Streaming understanding: Processing a time-ordered input as it arrives, using only past and current context rather than the full future recording.
    - Proactive vs reactive interaction: Reactive means answer after a query; proactive means monitor continuously and respond only when the requested condition is met.
    - Omni-multimodal large language model: A large language model that accepts or generates across several modalities such as text, audio, speech, and vision.
    - Multimodal unit: ROMA's per-step input package: audio and video tokens from the same time interval, processed as one causal unit.
    - Time-aligned Multimodal RoPE: A rotary position encoding variant that gives audio and video tokens time-aware positions so the transformer can align modalities on a shared timeline.
    - Speak head: A small classifier parallel to the language head that predicts whether the model should begin responding at the current stream step.
    - Key-value cache: Stored attention state from previous tokens, reused so a transformer can continue from prior context without recomputing the whole prefix.
    - Question answering: The reactive setting where a model answers a user question from the available stream history.
    - Streaming evaluation metrics: Metrics used for ranking event times, top timestamp accuracy, temporal overlap recall, trigger-window alignment, and semantic similarity.
    - Dynamic alert task names: Benchmark subtask abbreviations used by the paper for proactive alert and streaming narration settings; keep the original abbreviations when comparing tables.
    - Weighted binary cross-entropy: A binary classification loss where rare positive speak labels receive a larger weight so the model does not learn to stay silent too often.
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/paper_statement | Abstract | high
      locator:: Abstract, lines 20-23
      quote:: We present ROMA, a real-time omni-multimodal assistant for unified reactive and proactive interaction. ROMA processes continuous inputs as synchronized multimodal units, aligning dense audio with discrete video frames to handle granularity mismatches.
    - **E2:** problem/paper_statement | Introduction | high
      locator:: Section 1, reactive and proactive definition
      quote:: In the reactive setting, the model answers after the query, whereas in the proactive setting, it follows an instruction to continuously monitor the input stream and respond only when conditions are met.
    - **E3:** gap/paper_statement | Introduction | high
      locator:: Section 1, prior gap paragraph
      quote:: Speech-centric streaming models focus on audio generation but lack visual perception. Conversely, while some approaches address streaming video understanding, they typically neglect synchronized audio and are confined to specific tasks.
    - **E4:** method/implementation_detail | Method | high
      locator:: Section 3.1, Multimodal units
      quote:: We treat all audio and video signals within each one-second interval as a unit. We align audio with video frames sampled from the same interval, extract their features, and wrap them with special tokens.
    - **E5:** algorithm/implementation_detail | Method | high
      locator:: Section 3.1, Chunk-Level Temporal Position Encoding
      quote:: Each one-second unit interleaves visual and auditory tokens, assigning time-aligned 3D position IDs to preserve their cross-modal correspondence. Audio tokens retain fine-grained temporal IDs at a 40ms resolution.
    - **E6:** system_design/implementation_detail | Method | high
      locator:: Section 3.1, Speak Head
      quote:: This module is implemented as a two-layer MLP, parallel to the LM head, on top of the streaming backbone. Upon processing each multimodal unit, the speak head evaluates the current stream prefix and outputs a probability.
    - **E7:** method/implementation_detail | Method | high
      locator:: Section 3.2.1 and 3.2.2, dataset and training recipe
      quote:: We construct a comprehensive streaming dataset structured into two categories and three sub-tasks. Stage 1 adapts the model to the streaming multimodal input format, while Stage 2 learns precise response timing and proactive policies.
    - **E8:** implementation/implementation_detail | Method | high
      locator:: Section 3.2.3, Inference Procedure
      quote:: Video frames are uniformly sampled at 2 fps, and each frame is resized so that the number of pixels does not exceed 65,536. We maintain a persistent KV cache across the stream.
    - **E9:** experiment_setup/paper_statement | Unified Streaming Evaluation Framework | high
      locator:: Section 4, framework overview
      quote:: We establish a unified framework comprising two primary settings: proactive interaction, where the model autonomously monitors the stream to trigger responses, and reactive interaction, where it answers queries based on accumulated context.
    - **E10:** result/experiment_result | Experiment | medium
      locator:: Section 5.2, Tables 2 and 3, Event-Driven Alert
      quote:: ROMA advances temporal localization on QVHighlights (53.7 mAP) and Charades-STA (44.3/19.9 R@0.5/0.7). In the dynamic setting, ROMA demonstrates strong efficacy on single-alert tasks.
    - **E11:** result/experiment_result | Experiment | medium
      locator:: Section 5.2, Table 4, Real-Time Narration
      quote:: ROMA achieves the best temporal triggering accuracy, obtaining an F1 score of 35.21 on YouCook2 and 14.54 on OVO-Bench (SSR). It also achieves the highest GPT-4o score on both benchmarks.
    - **E12:** result/experiment_result | Experiment | medium
      locator:: Section 5.2, Tables 5-7, Reactive QA
      quote:: ROMA leads in both Real-time Visual Perception and Backward Tracing. On Streaming-Bench, ROMA maintains high accuracy and secures the top rank on Omni-Source Understanding benchmark.
    - **E13:** ablation/ablation | Experiment | medium
      locator:: Section 5.3, Ablation Study
      quote:: This variant consistently degrades on tasks that require online timing and triggering. We replace the speak head with a silence token. Last-layer aggregation notably degrades temporal grounding and dynamic triggering.
    - **E14:** ablation/ablation | Experiment | medium
      locator:: Section 5.4 and Appendix A.2, Sensitivity analysis
      quote:: We observe that w_pos is critical for proactive tasks, while reactive understanding and full-modality QA remain insensitive. Sensitivity analysis confirms robust performance and a broad operating regime with smooth degradation.
    - **E15:** limitation/limitation | Limitations | high
      locator:: Limitations section
      quote:: The model remains susceptible to distortions such as signal degradation and audio-video asynchrony. Capturing extremely long-term dependencies spanning hours remains constrained by finite context windows and memory.
    - **E16:** implementation/implementation_detail | Appendix | high
      locator:: Appendix A.5, Implementation Details
      quote:: The model is trained using LLaMA-Factory with a sequence length of 32K on 32 H20 GPUs using a global batch size of 512. Proactive samples are specifically formatted as multi-turn dialogues.
    - **E17:** prior_work/paper_statement | Appendix | medium
      locator:: Appendix A.1 and Table 10, Related Works
      quote:: Many works described as streaming in fact adopt a question-injection protocol. Overall, Table 10 shows that our method is the first open-source model to enable full omni-modal streaming while natively supporting proactive response, real-time narration, and reactive QA.
