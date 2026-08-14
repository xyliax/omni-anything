- **Title:** Streaming Video Instruction Tuning
- **Summary:** Streamo turns offline video LLMs into streaming assistants by training them to emit Silence/Standby/Response state tokens on multi-task temporally annotated data, improving open-ended streaming instruction following while exposing long-context efficiency limits.
- **Paper Type:** system
- **Venue:** arXiv preprint 2026; arXiv:2512.21334v2
- **Authors:** Jiaer Xia (Hong Kong Baptist University); Peixian Chen (Tencent Youtu Lab); Mengdan Zhang (Tencent Youtu Lab); Xing Sun (Tencent Youtu Lab); Kaiyang Zhou (Hong Kong Baptist University)
- **Keywords:** streaming video understanding, video LLM, instruction tuning, response timing, temporal grounding, time-sensitive QA, online multimodal assistants
- ## Quick Reference
    - **Why Read:** Read this for a concrete recipe for converting offline video LLMs into interactive streaming models: represent response timing as tokens, train on temporally aligned multi-task dialogues, and rebalance sparse response states.
      claim_kind:: analyst_assessment
      evidence:: E2, E4, E5
    - **One-Sentence Contribution:** Streamo improves streaming video instruction following by interleaving one-second video turns with three response-state tokens and training on Streamo-Instruct-465K with state-aware focal/frequency weighting.
      evidence:: E2, E4, E5, E7
    - **Mental Model:** Think of the model as a live commentator with a built-in traffic light: red Silence for irrelevant context, yellow Standby for relevant-but-incomplete events, and green Response for the moment the answer should be emitted.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest support is the combination of Streamo-Bench breadth, offline-retention results, and targeted ablations showing that both adaptive loss weighting and the Standby state matter.
      evidence:: E11, E12, E13, E14
        - C1: Streamo-Bench; Streamo-7B vs listed online baselines; average score 55.3 vs best baseline 24.6; supports multi-instruction streaming generalization.
          evidence:: E12
        - C2: Offline conversion; Qwen2.5-VL-7B base; average 63.9 vs 60.6 (+3.3); supports preserving or improving general video understanding after streaming tuning.
          evidence:: E11
        - C3: Loss ablation; Qwen2.5-VL-3B on OVO forward-active tasks; focal loss raises REC/SSR/CRR from 6.45/20.99/41.67 under CE to 27.94/50.72/82.5.
          evidence:: E13
    - **Main Caveat:** The method still inherits unbounded-stream memory/latency growth, and the broad SOTA framing should be read carefully because Table 2 includes a ViSpeak row with higher OVO overall than Streamo-7B.
      claim_kind:: analyst_assessment
      evidence:: E10, E16
- ## Argument Map
    - **Problem and Stakes:** Offline video LLMs assume a bounded clip and answer after seeing the whole video, whereas streaming assistants must decide continuously, from partial observations, both whether enough evidence has arrived and what to say. The stakes are latency-sensitive interactive tasks such as narration, proactive alerts, event grounding, and answers whose truth changes over time.
      evidence:: E2, E3
    - **Prior Gap:** The paper frames prior online adaptations as either decoupled controller-plus-offline-model pipelines or narrow EOS-style response-timing training, which can trade accuracy for latency, lose coupling between perception and generation, or cover only limited task formats.
      evidence:: E3, E14
    - **Key Insight:** Instead of adding an external streaming controller, make response timing part of the language-modeling target: the same decoder predicts Silence, Standby, or Response tokens and then generates the answer when the Response state is reached. Because these state tokens are sparse and imbalanced, the paper couples this representation with focal and per-batch frequency weighting.
      evidence:: E4, E5
    - **Claims:** The paper's supportable claim chain is that Streamo's state-token formulation plus Streamo-Instruct-465K improves streaming instruction following, preserves offline video ability, and benefits materially from the proposed loss and three-state design.
      evidence:: E10, E11, E12, E13
        - C1: Streamo improves open-ended streaming instruction following on Streamo-Bench, reaching 55.3 average versus 24.6 for the strongest listed existing online baseline.
          evidence:: E12
        - C2: Streaming tuning does not simply sacrifice offline ability; Streamo-7B improves the Qwen2.5-VL-7B average from 60.6 to 63.9 across the paper's offline-oriented suite.
          evidence:: E11
        - C3: State-aware focal/frequency weighting improves proactive response learning under the reported 12:3:2 state-label imbalance.
          evidence:: E13
        - C4: The Standby state is useful beyond a binary answer/silence or EOS design, especially for forward-active and grounding tasks.
          evidence:: E14
- ## Mechanism and Design
    - **Core Mechanism:** Streamo reformulates streaming video as interleaved multi-turn supervised fine-tuning: each video segment is paired with an assistant turn whose target begins with a response-state token. The state token acts as an inline control signal, so the model learns both temporal readiness and natural-language output in the same next-token prediction objective.
      evidence:: E4
    - **Data / Control Flow:** Training simulates a stream by splitting a video into one-second turns with absolute time markers, inserting task instructions at appropriate turns, and requiring the assistant to emit Silence, Standby, or Response at every step. The Response token gates answer generation; Silence and Standby continue accumulation without final output.
      evidence:: E4, E9
        - Step 1: Convert an offline clip into ordered segments with time tags such as <2s-3s>, so every training turn has an explicit temporal boundary.
          evidence:: E4
        - Step 2: Predict <Silence> for irrelevant or insufficient context, <Standby> for relevant but incomplete evidence, and <Response> when the model should answer.
          evidence:: E4
        - Step 3: For state tokens, the loss applies `$w_{\mathrm{focal}}(x_i)=(1-p_{c_i})^{\gamma}$` and `$\alpha_k=\frac{1}{|\mathcal{S}|}\frac{\sum_{j\in\mathcal{S}} n_j}{n_k}$` to cross-entropy, while ordinary tokens keep standard CE.
          evidence:: E5
    - **Design Decisions:** The major design decisions all target the same bottleneck: sparse, temporally precise response decisions must be learned without detaching them from language generation. The paper's ablations most directly support the Standby token and adaptive state-loss choices.
      claim_kind:: analyst_assessment
      evidence:: E3, E13, E14
        - Need: avoid latency and decoupling from an auxiliary controller; choice: integrate response-state tokens into the decoder's normal token stream; tradeoff: the LLM context now carries continuous control history.
          evidence:: E3, E4
        - Need: distinguish irrelevant frames from relevant-but-unfinished events; choice: add <Standby>; alternative: EOS-only timing; evidence shows EOS lowers OVOBench FAR and forward-grounding scores.
          evidence:: E14
        - Need: prevent the model from collapsing toward Silence under imbalanced labels; choice: dynamic focal plus per-batch frequency weighting; alternative: vanilla CE or fixed loss scaling, both weaker in Table 4.
          evidence:: E5, E13
    - **Implementation Surface:** The reported implementation is deliberately close to standard SFT: Qwen2.5-VL 3B/7B bases, frozen vision encoder, trainable connector and LLM, one epoch, batch size 512, learning rate 1e-5, one-second turns, 1 fps sampling, and gamma 2. Streamo-Instruct-465K supplies the temporal multi-task supervision rather than requiring architectural surgery.
      evidence:: E7, E9
        - Training surface: the vision encoder is frozen, while the connector and LLM are updated under a unified setup across models.
          evidence:: E9
        - Data surface: each video can carry multiple task annotations with unified temporal response boundaries, addressing heterogeneous labeling across source datasets.
          evidence:: E6, E7
        - Artifact surface: the paper promises public release of code, models, and datasets, but the provided text states this as future availability.
          evidence:: E17
- ## Evaluation and Evidence
    - **Setup:** Evaluation spans online OVO-Bench, offline/general video benchmarks, and Streamo-Bench, a 300-video/3,000-task mixed instruction benchmark. Streamo-Bench mixes mIoU for grounding, Qwen2.5-VL-72B pairwise win rate for narration/caption, and TSQA content-plus-time correctness with a 3-second timestamp tolerance.
      evidence:: E8, E9, E15
    - **Claim-Evidence Matrix:** The evidence is strongest where the paper combines controlled architecture/training comparisons with task-specific benchmarks, and weakest where broad SOTA claims depend on baseline selection or LLM-judge evaluation.
      claim_kind:: analyst_assessment
      evidence:: E10, E12, E15
        - C1 multi-task streaming: supported by Streamo-Bench, where Streamo-7B is highest among listed models across a heterogeneous average, though the average combines different metric types.
          evidence:: E12, E15
        - C2 offline retention: supported by Table 3, where Streamo-7B improves the Qwen2.5-VL-7B average and exceeds StreamingVLM on the reported offline benchmark columns.
          evidence:: E11
        - C3 response-state training: supported by ablations showing focal loss over CE/fixed scaling and three-state design over EOS-only on response-timing-sensitive tasks.
          evidence:: E13, E14
    - **Headline Results:** The headline results support Streamo as a strong streaming-instruction model, but not every broad comparison is clean: the OVO table itself contains a higher ViSpeak overall score. No statistical uncertainty, repeat counts, or hardware-normalized latency numbers are reported in the supplied text.
      claim_kind:: analyst_assessment
      evidence:: E10, E11, E12
        - Online OVO: Streamo-7B 1fps scores 55.61 overall vs Dispider-7B 41.78 (+13.83), and 2fps evaluation scores 57.86; caveat: ViSpeak-7B is listed at 61.08 overall.
          claim_kind:: analyst_assessment
          evidence:: E10
        - Offline/general benchmarks: Streamo-7B averages 63.9 vs Qwen2.5-VL-7B 60.6 (+3.3), with reported gains on MVBench, VideoMME, and LongVideoBench.
          evidence:: E11
        - Streamo-Bench: Streamo-7B scores 55.3 average vs 24.6 for the strongest listed existing online baseline, with especially large margins on grounding and dense captioning.
          evidence:: E12
    - **Ablations and Sensitivity:** The ablations are important because they isolate two non-obvious pieces of the method: adaptive reweighting for sparse state tokens and the Standby state for relevant-but-incomplete events. The 2fps evaluation suggests some test-time sampling-rate robustness, but it is only reported for the OVO configuration in the main table.
      evidence:: E10, E13, E14
        - Loss ablation: on Qwen2.5-VL-3B, focal loss improves REC/SSR/CRR to 27.94/50.72/82.5 from CE's 6.45/20.99/41.67 and fixed scaling's 18.62/41.02/49.17.
          evidence:: E13
        - State-design ablation: replacing the three-state design with EOS-only drops OVOBench average from 52.33 to 48.52 and forward grounding from 14.7 to 9.3.
          evidence:: E14
        - Sampling-rate sensitivity: the table reports Streamo-7B trained at 1fps and evaluated at 2fps improving OVO overall from 55.61 to 57.86, but broader frame-rate sweeps are not reported.
          evidence:: E10
    - **Reproducibility Gaps:** The paper gives enough high-level training and metric detail to understand the recipe, but several fields needed for robust reproduction or systems comparison remain unspecified in the supplied text. The largest practical blocker is that public artifacts are promised rather than evidenced as already available.
      claim_kind:: analyst_assessment
      evidence:: E9, E15, E17
        - Artifact availability: code, models, and datasets are stated as future public releases; exact repository state, licenses, preprocessing scripts, and checkpoints are not reported here.
          claim_kind:: analyst_assessment
          evidence:: E17
        - Training resources: batch size, learning rate, epoch count, frozen modules, and sampling rate are reported, but GPU type/count, wall-clock time, memory use, and serving latency are not reported.
          claim_kind:: analyst_assessment
          evidence:: E9, E16
        - Evaluation uncertainty: Streamo-Bench caption/narration uses an LLM judge and TSQA uses a 3-second tolerance, but judge agreement, repeated runs, and confidence intervals are not reported.
          claim_kind:: analyst_assessment
          evidence:: E12, E15
- ## Technical Judgment
    - **What Holds Up:** The central reframing is technically plausible and useful: response timing becomes a supervised token prediction problem compatible with standard multimodal SFT, not a separate controller. The ablations give credible mechanism-level evidence that both adaptive state-token weighting and the Standby state improve timing-sensitive behavior.
      claim_kind:: analyst_assessment
      evidence:: E4, E13, E14
        - The three-token control interface is simple enough to port across base models because it lives in the dialogue format and loss rather than a new perception architecture.
          claim_kind:: analyst_assessment
          evidence:: E4, E9
        - The loss and EOS ablations are more convincing than aggregate benchmark wins because they directly perturb the proposed response-timing mechanisms.
          claim_kind:: analyst_assessment
          evidence:: E13, E14
    - **Where It May Fail:** The approach does not solve the systems problem of truly unbounded streams: accumulating dialogue/video context without specialized cache or token management can make memory and latency prohibitive. It also depends heavily on the quality and temporal precision of generated annotations and on evaluation protocols that include heterogeneous metrics and LLM judging.
      claim_kind:: analyst_assessment
      evidence:: E6, E15, E16
        - Systems boundary: benefits should diminish as stream length exceeds feasible context or KV-cache budgets unless pruning, compression, or sliding-window attention is added.
          claim_kind:: analyst_assessment
          evidence:: E16
        - Baseline boundary: the paper's SOTA wording should be narrowed because Table 2 lists ViSpeak-7B with 61.08 OVO overall, above Streamo-7B's 55.61 and 2fps 57.86.
          claim_kind:: analyst_assessment
          evidence:: E10
        - Evaluation boundary: averaging mIoU, LLM-judge win rates, and TSQA accuracy/recall is useful diagnostically but not a single clean operational metric for latency-quality tradeoffs.
          claim_kind:: analyst_assessment
          evidence:: E12, E15
    - **Relation to Other Work:** Relative to controller-based streaming adapters such as Dispider and StreamBridge, Streamo moves the decision policy into the same decoder that generates text. Relative to EOS-only approaches such as VideoLLM-Online or StreamingVLM, the Standby token provides an intermediate temporal state; relative to QA-centric streaming benchmarks, Streamo-Bench tests mixed open-ended tasks.
      claim_kind:: analyst_assessment
      evidence:: E3, E14, E15
    - **Transferable Lesson:** For interactive streaming tasks, model readiness as an explicit sequence of latent states, not as a binary answer/no-answer event; an intermediate relevant-but-incomplete state can preserve temporal alignment until sufficient evidence arrives. When such states are rare, rebalance them dynamically rather than relying on vanilla next-token CE.
      claim_kind:: analyst_assessment
      evidence:: E4, E5, E13, E14
- ## Glossary
  collapsed:: true
    - Streamo: The paper's streaming video LLM framework/model; the name's 'o' is described as 'omni' for multi-task and multimodal capabilities.
    - Streamo-Instruct-465K: A temporally annotated multi-task instruction-tuning dataset for streaming video; built from 400K curated samples plus offline video QA, over 135,875 videos.
    - Streamo-Bench: A 300-video, 3,000-task benchmark for mixed streaming instructions including grounding, narration, dense captioning, and time-sensitive QA.
    - <Silence>, <Standby>, <Response>: Special response-state tokens inserted into assistant turns: no output, relevant-but-incomplete context, and answer-ready output respectively.
    - Standby state: The intermediate state that marks an event as relevant before it is complete; it is the key difference from EOS-only timing formulations.
    - Time-Sensitive QA (TSQA): Questions whose answers change over time; evaluation requires matching both answer content and timestamp within a specified tolerance.
    - mIoU: Mean temporal Intersection over Union between predicted and ground-truth event intervals; used for Streamo-Bench grounding tasks.
    - Focal/frequency state-token loss: A modified cross-entropy for the three state tokens that combines token hardness via focal weighting with inverse batch-frequency alpha weights.
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/metadata | Title block | high
      locator:: paper header
      quote:: arXiv:2512.21334v2 [cs.CV] 10 Apr 2026. Streaming Video Instruction Tuning. Jiaer Xia, Peixian Chen, Mengdan Zhang, Xing Sun, Kaiyang Zhou. Hong Kong Baptist University; Tencent Youtu Lab.
    - **E2:** method/paper_statement | Abstract | high
      locator:: Abstract
      quote:: We present Streamo, a real-time streaming video LLM that serves as a general-purpose interactive assistant. Unlike existing online video models that focus narrowly on question answering or captioning, Streamo performs a broad spectrum of streaming video tasks, including real-t...
    - **E3:** gap/paper_statement | 1. Introduction | high
      locator:: paragraphs on streaming requirements and prior controllers
      quote:: Existing offline models struggle to meet the demands of the streaming setting because they are designed to process entire clips before producing a single output. Recent studies have attempted to extend offline video models for streaming by introducing a separate decision modul...
    - **E4:** method/implementation_detail | 3.2 Data Structure | high
      locator:: state-token formulation and Table 1
      quote:: To simulate streaming scenarios during training, we reformulate the single-turn offline format into a multi-turn dialogue structure. A complete video is temporally segmented into N contiguous segments, each annotated with temporal boundaries using special markers. Three discre...
    - **E5:** algorithm/implementation_detail | 3.3 Training | high
      locator:: loss definition
      quote:: The multi-turn streaming format introduces severe class imbalance among the three response states. In typical streaming scenarios, <Silence> tokens dominate the distribution, often more than 80% of the time, while <Response> tokens are sparse. To mitigate this, we apply focal...
    - **E6:** method/paper_statement | 4.1 Data Construction | high
      locator:: annotation protocol overview
      quote:: We predefined multiple tasks spanning different response granularities, assigning each video several types of task annotations. A unified annotation protocol is applied across datasets, avoiding inconsistencies and biases. Each video carries multiple task types with clearly de...
    - **E7:** metadata/paper_statement | 4.2 Statistics | high
      locator:: dataset statistics paragraph and Figure 3
      quote:: Using a unified annotation standard and protocol, we labeled and curated a total of 400K valid samples and additionally merged offline video QA data from the LLaVA-Video dataset, culminating in Streamo-Instruct-465K. We integrated multiple open-source video datasets as sources...
    - **E8:** experiment_setup/paper_statement | 5.2 Benchmarks | high
      locator:: benchmark setup paragraph
      quote:: We evaluated our model across three dimensions of benchmarks: Online, Offline, and Stream Instruction. For the online setting, we adopted OVO-Bench. The offline evaluation used MVBench, TempCompass, VideoMME, and LongVideoBench. We constructed StreamoBench, which includes 300...
    - **E9:** implementation/implementation_detail | 5.3 Implementation Details | high
      locator:: training setup paragraph
      quote:: Across all models, we use a unified training setup. Full parameter tuning is applied with the vision encoder frozen, and only the connector and the LLM will be updated. Training runs for a single epoch with a batch size of 512 and a learning rate of 1 x 10^-5. Each video is sp...
    - **E10:** result/experiment_result | 5.4 Main Results | high
      locator:: Table 2 and accompanying text
      quote:: Table 2 reports Dispider-7B Overall Avg. 41.78, ViSpeak-7B Overall Avg. 61.08, Streamo-7B at 1fps Overall Avg. 55.61, and Streamo-7B at 2fps Overall Avg. 57.86. The text states that Streamo-7B exceeds Dispider by +13.83 average performance.
    - **E11:** result/experiment_result | 5.4 Main Results | high
      locator:: Table 3
      quote:: Table 3 reports Qwen2.5-VL-7B Avg 60.6 and Streamo-7B Avg 63.9 (+3.3), with MVBench 72.3 (+2.7), VideoMME 67.9 (+2.8), and LongVideoBench 59.2 (+3.2). StreamingVLM-7B reports MVBench 69.2, VideoMME 65.1, and LongVideoBench 59.0.
    - **E12:** result/experiment_result | 5.4 Main Results | high
      locator:: Table 5
      quote:: Table 5 reports Streamo-Bench results: Streamo-7B reaches Forward Grounding 29.4, Backward Grounding 38.3, Narration 75.9, Dense Caption 72.8, TSQA Accuracy 51.6, TSQA Recall 63.9, Average 55.3. The strongest listed existing online baseline average is StreamingVLM-7B at 24.6.
    - **E13:** ablation/ablation | 5.5 Ablation | high
      locator:: Table 4 and ablation discussion
      quote:: In Streamo-Instruct-465K, the empirical ratio of state labels is approximately <Silence>:<Standby>:<Response> = 12:3:2. Table 4 shows Qwen2.5-VL-3B on OVO Forward Active tasks: CrossEntropy 6.45/20.99/41.67, Loss Scale 18.62/41.02/49.17, and Focal Loss 27.94/50.72/82.5 for REC...
    - **E14:** ablation/ablation | A.5 Further Analysis of the Three-State Design | high
      locator:: Table 7
      quote:: Table 7 compares Streamo-3B with an EOS-only variant on the same Streamo-Instruct dataset: Streamo-3B has OVOBench RTVP 61.51, BT 41.76, FAR 53.72, AVG 52.33, Forward Grounding 14.7; the EOS variant has 60.93, 39.43, 45.22, 48.52, and 9.3.
    - **E15:** experiment_setup/paper_statement | C.2 Metric | high
      locator:: Streamo-Bench metric definitions
      quote:: For grounding tasks, performance is measured using mean Intersection over Union. Narration and caption quality are assessed via pairwise comparison against Qwen2.5-VL-72B. For Time-Sensitive QA, a prediction must be correct in both its content and its timestamp; the timestamp...
    - **E16:** limitation/limitation | 7. Limitations and Future Work | high
      locator:: limitations paragraph
      quote:: Our current pipeline lacks specialized long-sequence optimizations, leading to significant memory and latency costs that become prohibitive as sequence length grows. The paper proposes integrating KV-cache management, visual token pruning, sliding-window attention, and adaptiv...
    - **E17:** metadata/paper_statement | 1. Introduction | high
      locator:: contributions paragraph
      quote:: We establish a comprehensive benchmark for streaming video instruction-following and provide strong baseline models for future research. All research resources including code, models, and datasets will be made publicly available.
