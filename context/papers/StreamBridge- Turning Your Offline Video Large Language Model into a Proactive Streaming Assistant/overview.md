- **Title:** StreamBridge: Turning Your Offline Video Large Language Model into a Proactive Streaming Assistant
- **Summary:** StreamBridge adapts offline Video-LLMs into streaming assistants by buffering interleaved frame/text embeddings, compressing old visual tokens, and using a lightweight external activation model, improving multi-turn and proactive video interaction while mostly preserving offline video understanding.
- **Paper Type:** system
- **Venue:** NeurIPS 2025; arXiv:2505.05467v2
- **Authors:** Haibo Wang (Apple, Fudan University), Bo Feng (Apple), Zhengfeng Lai (Apple), Mingze Xu (Apple), Shiyu Li (Apple), Weifeng Ge (Fudan University), Afshin Dehghan (Apple), Meng Cao (Apple), Ping Huang (Apple)
- **Keywords:** streaming video understanding, Video-LLM, online multimodal assistant, memory buffer, token compression, proactive response, Stream-IT, activation model
- ## Quick Reference
    - **Why Read:** Read this for a practical adaptation recipe: keep a strong offline Video-LLM, add streaming state/compression, and separate proactive timing into a small side model. It is also useful for understanding why many nominal streaming evaluations reduce to single-turn offline QA.
      claim_kind:: analyst_assessment
      evidence:: E3, E4, E10
    - **One-Sentence Contribution:** StreamBridge turns offline Video-LLMs into 1-FPS multi-turn and proactive streaming assistants by buffering interleaved embeddings, round-decay-compressing old visual tokens, using an external activation classifier, and fine-tuning on Stream-IT.
      evidence:: E1, E4, E7, E8
    - **Mental Model:** Think of it as a video-chat event loop: an encoder keeps appending frames to a rolling notebook, a janitor compresses old pictures first, and a small alarm model decides when the large narrator should speak.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest support is the triangle of cross-model streaming gains, proactive ET-Bench generation results, and compression/latency ablations.
      evidence:: E10, E12, E13, E14
        - C1: Qwen2-VL-7B + StreamBridge + Stream-IT at 1 FPS reaches OVO/Streaming averages 71.30/77.04 versus its offline single-turn 55.98/69.04 and GPT-4o 64.46/73.28; uncertainty is not reported and evaluation modes differ.
          evidence:: E10
        - C3: On ET-Bench, Qwen2-VL under StreamBridge improves generation-based DVC/SLC over VideoLLM-Online and Dispider, e.g. DVC_F1 38.3 versus 24.0/33.8; timing localization is not best versus Dispider.
          evidence:: E12
        - C4: Round-decayed compression beats truncation and round-uniform on OVO/Streaming/ET similarities and keeps A100 latency near-constant beyond MaxLen, whereas no compression OOMs at 2048 frames.
          evidence:: E13, E14
    - **Main Caveat:** Generality beyond the paper's 1-FPS, mostly visual-only benchmark setting remains uncertain: Stream-IT is partly synthetic/concatenated, very long videos are capped by uniform sampling, and code/data/repeat information is not fully reported in the provided text.
      claim_kind:: analyst_assessment
      evidence:: E16, E17
- ## Argument Map
    - **Problem and Stakes:** Offline Video-LLMs assume full-video access, but online settings need causal, timely, temporally coherent interaction. The paper frames the stakes around two streaming patterns: multi-turn real-time QA over accumulating history and proactive responses without an immediate user prompt.
      evidence:: E2
    - **Prior Gap:** The paper argues that existing evaluations often discard prior visual/dialogue history and reduce streaming to independent offline queries, while prior proactive designs tend to entangle timing decisions with the main model. It also claims that existing data lacks long interleaved multi-turn/proactive supervision, motivating Stream-IT.
      evidence:: E3, E7, E8
    - **Key Insight:** Streaming adaptation can be decomposed without rebuilding the base Video-LLM: persist multimodal history as embeddings, spend context budget preferentially on recent frames, and move speaking-time decisions to an external lightweight classifier.
      evidence:: E4, E6, E7
    - **Claims:** The paper's empirical claims are falsifiable along four axes: multi-turn streaming adaptation, Stream-IT data value, proactive activation, and compression efficiency.
      evidence:: E1, E10, E11, E12, E13
        - C1: StreamBridge alone equips offline Video-LLMs for multi-turn streaming; Qwen2-VL improves from 55.98 to 63.35 on OVO and 69.04 to 72.01 on Streaming before Stream-IT fine-tuning.
          evidence:: E10
        - C2: Stream-IT fine-tuning materially improves streaming performance and is intended to retain or improve general video ability; Qwen2-VL+Stream-IT reaches 71.30/77.04 on OVO/Streaming.
          evidence:: E8, E10, E11, E15
        - C3: Decoupling activation from generation supports proactive response without burdening the main LLM; ET-Bench generation metrics exceed VideoLLM-Online and Dispider.
          evidence:: E7, E12
        - C4: Round-decayed compression is the best tested memory-budget mechanism and lowers latency/memory pressure while preserving recent context.
          evidence:: E6, E13, E14
- ## Mechanism and Design
    - **Core Mechanism:** At each time step, a frame encoder appends visual embeddings to a memory buffer; when a query is pending and the activation model fires, the system flattens accumulated visual/text history, optionally compresses it to MaxLen, and lets the base LLM decode. The generated response is appended back into the buffer so later turns see conversational history.
      evidence:: E4, E5, E6, E7
    - **Data / Control Flow:** The execution order is producer-consumer: frame encoder produces per-frame embeddings, the activation model decides whether the LLM should consume the buffer, and compression enforces a bounded input sequence before decoding.
      evidence:: E5, E6, E7
        - Ingest: each incoming frame is encoded independently and appended; queries and generated responses are also stored, preserving multi-turn visual/text history.
          evidence:: E5
        - Trigger: after a query or initial proactive prompt, ACT emits a binary decision, and only a positive decision routes the flattened buffer to the main LLM.
          evidence:: E5, E7
        - Budget: if flattened input length exceeds MaxLen, COM merges earlier visual tokens frame-by-frame while preserving recent visual detail.
          evidence:: E6
    - **Design Decisions:** The design trades exact long-history retention for deployable latency and modularity: recency-biased compression, sidecar activation, and mixed streaming/offline data replace full streaming-model retraining.
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E8, E15
        - Need: infinite streams exceed context; choice: compress earliest rounds first by average pooling; tested alternatives are truncation and uniform per-round compression; tradeoff is loss of older visual detail.
          evidence:: E6, E13, E15
        - Need: proactive speaking time; choice: external LLaVA-OV-0.5B classifier with score head and <ACT> token; alternative is backbone-integrated activation; tradeoff is an extra model and threshold.
          evidence:: E7, E12, E18
        - Need: interleaved streaming supervision without forgetting offline skills; choice: Stream-IT plus 600K offline video samples; ablations show offline-only loses streaming, Stream-IT-only hurts general video, and removing StreamingQA-120K degrades both.
          evidence:: E8, E9, E15
    - **Implementation Surface:** The reported implementation exposes the main cost knobs: per-frame visual token counts, MaxLen, frame sampling, and which weights are trainable. The main models keep frozen image encoders but tune projectors and LLMs, while the activation model pools frames aggressively and trains only lightweight adaptation components.
      evidence:: E16, E7
        - Main-model per-frame visual tokens after downsampling are LLaVA-OV 49, Oryx 33-59, and Qwen2-VL 36-64; MaxLen defaults to 16384.
          evidence:: E16
        - Main Video-LLMs are fine-tuned for one epoch at lr 2e-5 with AdamW/cosine; the activation model trains for 5 epochs with separate learning rates for projector versus LoRA, score head, and <ACT>.
          evidence:: E16
        - Streaming and long-video evaluations mostly use 1 FPS; videos longer than 256 seconds are uniformly sampled to 256 frames, and experiments use H100/A100 GPUs.
          evidence:: E16, E9
- ## Evaluation and Evidence
    - **Setup:** Experiments adapt LLaVA-OV-7B, Qwen2-VL-7B, and Oryx-1.5-7B; benchmarks cover OVO-Bench/Streaming-Bench real-time MCQA, seven offline video MCQA benchmarks, and ET-Bench proactive F1/similarity tasks. The default in-depth model is Qwen2-VL-7B, with LLaVA-OV-0.5B as the activation model.
      evidence:: E9
    - **Claim-Evidence Matrix:** Evidence is strongest for benchmarked streaming adaptation and the compression policy; evidence is weaker for open-ended deployment because the paper does not report statistical uncertainty or natural live-stream field tests.
      claim_kind:: analyst_assessment
      evidence:: E10, E13, E17
        - C1 Multi-turn adaptation: supported by Qwen2-VL and Oryx gains under StreamBridge/Stream-IT, but base-model compatibility varies because LLaVA-OV initially drops when only wrapped for streaming.
          evidence:: E10
        - C2 Stream-IT value: supported by main results and data ablation showing Stream-IT and StreamingQA-120K improve streaming, while offline data is still needed to preserve general video ability.
          evidence:: E10, E15
        - C3 Proactive activation: supported for generation-quality tasks on ET-Bench, but timing/localization is only partly supported because Dispider has higher TVG_F1 and TAL_F1.
          claim_kind:: analyst_assessment
          evidence:: E12
        - C4 Compression efficiency: supported by direct ablations over truncation/uniform compression and by A100 latency results showing bounded latency beyond MaxLen.
          evidence:: E13, E14
    - **Headline Results:** The headline results show large streaming gains after Stream-IT, competitive offline video performance, and proactive generation gains; however, uncertainty, repeat count, and confidence intervals are not reported.
      evidence:: E10, E11, E12
        - Streaming result: Qwen2-VL-7B + StreamBridge + Stream-IT at 1 FPS scores 71.30 OVO and 77.04 Streaming, improving over Qwen2-VL offline single-turn by +15.32/+8.00 and over GPT-4o by +6.84/+3.76; caveat: evaluation protocols differ.
          evidence:: E10
        - Offline-video result: Oryx-1.5-7B gains +6.7 on VideoMME after StreamBridge+Stream-IT, while LLaVA-OV mostly improves but drops on LongVideoBench and Qwen2-VL drops on MVBench; the non-degradation claim is therefore model/benchmark dependent.
          evidence:: E11
        - Proactive result: Qwen2-VL StreamBridge reports DVC_F1/DVC_Sim 38.3/25.1 and SLC_F1/SLC_Sim 22.6/17.1, exceeding VideoLLM-Online and Dispider on generation metrics; it is below Dispider on TVG_F1/TAL_F1 localization.
          evidence:: E12
    - **Ablations and Sensitivity:** Ablations validate the major design knobs: compression policy, Stream-IT data composition, MaxLen, and activation threshold alpha. The paper reports point estimates only, so sensitivity conclusions should be treated as directional.
      evidence:: E13, E15, E18
        - Compression: Round-Decayed beats Truncation and Round-Uniform on OVO Avg. 71.30 versus 68.88/69.91 and Streaming Avg. 77.04 versus 72.79/74.18, supporting recency-biased compression.
          evidence:: E13
        - Data/MaxLen: removing StreamingQA-120K or offline auxiliary data hurts complementary capabilities; OVO is fairly stable across MaxLen 4k-32k, while VideoMME improves with larger MaxLen.
          evidence:: E15
        - Activation threshold: too-low alpha over-triggers and too-high alpha suppresses responses; the default is 0.35, with Figure 5 showing degradation at both extremes.
          evidence:: E18
    - **Reproducibility Gaps:** The paper reports base models, data source families, sampling rates, token counts, optimizer/lr choices, GPU classes, and benchmark metrics, but the provided text does not report code/model/data release URLs, seeds, run counts, or statistical uncertainty. Reproducing Stream-IT also depends on GPT-4o generation and large filtered video-source pipelines.
      claim_kind:: analyst_assessment
      evidence:: E8, E9, E16
        - Reported: base models, sampling, optimizer/lr, token counts, MaxLen, and hardware class; not reported in the provided text: release artifacts, random seeds, repeat count, or confidence intervals.
          claim_kind:: analyst_assessment
          evidence:: E9, E16
        - Dataset reproducibility is a concrete blocker because StreamingQA-120K requires filtering 1.28M clips, semantic concatenation, GPT-4o QA generation, and source clip availability.
          claim_kind:: analyst_assessment
          evidence:: E8
- ## Technical Judgment
    - **What Holds Up:** The decomposition is technically plausible because it changes the input/state path rather than requiring a new streaming backbone, and each major component has either cross-model or ablation evidence. The compression mechanism is especially well supported because it improves accuracy and bounds latency under the same memory budget.
      claim_kind:: analyst_assessment
      evidence:: E4, E10, E13, E14
        - Cross-base results on Qwen2-VL, Oryx, and LLaVA-OV reduce the risk that the framework is a single-model trick, although base-model pretraining still matters.
          claim_kind:: analyst_assessment
          evidence:: E9, E10
        - Round-decayed compression has a clear systems rationale: keep high-fidelity recent evidence, average-pool older visual tokens, and prevent latency/OOM growth.
          claim_kind:: analyst_assessment
          evidence:: E6, E13, E14
    - **Where It May Fail:** The method's benefit should diminish when tasks require fine-grained old-frame details, higher frame rates, audio cues, or naturally evolving long videos unlike concatenated clips. Proactive timing also remains threshold-sensitive and not uniformly superior on localization.
      claim_kind:: analyst_assessment
      evidence:: E12, E16, E17, E18
        - Paper-provided limitation: synthetic QA generation and clip concatenation may cause domain shift; low-rate 1-FPS visual streaming does not cover denser frame rates or audio-visual-text inputs.
          evidence:: E17
        - The 256-frame cap for videos longer than 256 seconds means the evaluated long-stream setting is not full-resolution temporal accumulation for arbitrarily long live video.
          claim_kind:: analyst_assessment
          evidence:: E16
        - Activation is useful but not solved: alpha changes response frequency, and Table 3 shows StreamBridge below Dispider on TVG_F1 and TAL_F1 despite stronger generation scores.
          claim_kind:: analyst_assessment
          evidence:: E12, E18
    - **Relation to Other Work:** Technically, StreamBridge sits between offline Video-LLM inference and fully specialized streaming assistants: it adapts strong offline models with a buffer/compression wrapper rather than replacing the backbone. Relative to backbone-integrated activation approaches, the decoupled sidecar reduces optimization interference but adds a second model and threshold tuning.
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E10, E12
    - **Transferable Lesson:** For adapting offline foundation models to online interaction, split the problem into state retention, context-budget policy, and actuation policy; each can then be ablated and tuned independently. The broader pattern is to protect the base generator's learned capabilities while adding small, task-specific online control surfaces such as MaxLen and alpha.
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E15, E18
- ## Glossary
  collapsed:: true
    - StreamBridge: Framework that wraps offline Video-LLMs with a memory buffer, round-decayed compression, and a decoupled activation model to support streaming interaction.
    - Memory Buffer (MB): Persistent sequence of visual and textual embeddings accumulated over time; stores incoming frame features, user queries, and generated responses.
    - Round-Decayed Compression (COM): Context-budget policy that compresses visual tokens from earlier dialogue rounds first, usually by average pooling frames, while preserving recent context at higher fidelity.
    - Activation Model (ACT): Small external MLLM, implemented with LLaVA-OV-0.5B in the paper, trained as a binary classifier to decide when the main LLM should respond.
    - Stream-IT: Streaming instruction-tuning dataset with interleaved video-text sequences for multi-turn real-time QA and proactive response formats.
    - StreamingQA-120K / SQA-120K: Synthetic Stream-IT subset built by semantically concatenating short clips into long videos and generating multi-turn QA pairs with GPT-4o.
    - MaxLen: Maximum allowed input-embedding sequence length before compression; default reported value is 16384, with ablations over 4k to 32k.
    - Activation threshold alpha: Score threshold for ACT to trigger a response; lower values increase response frequency and higher values suppress it.
- ## Evidence Index
  collapsed:: true
    - **E1:** method/paper_statement | Abstract | high
      locator:: Abstract
      quote:: We present StreamBridge, a simple yet effective framework that seamlessly transforms offline Video-LLMs into streaming-capable models. It addresses two fundamental challenges: limited capability for multi-turn real-time understanding, and lack of proactive response mechanisms....
    - **E2:** problem/paper_statement | Introduction | high
      locator:: Section 1, opening paragraphs and Figure 1 discussion
      quote:: Video Large Language Models typically process entire pre-recorded videos at once. However, emerging applications, such as robotics and autonomous driving, require causal perception and interpretation of visual information online. Figure 1 highlights two representative patterns...
    - **E3:** gap/paper_statement | Methodology - Preliminary Analysis | high
      locator:: Section 3.1
      quote:: For a query Q_i at time t_i, the visual input is restricted to the uniformly sampled frames under segment V_[0:t_i], and prior dialogue history is completely discarded. As a result, the multi-turn streaming scenario is reduced to a series of independent, single-turn offline ta...
    - **E4:** system_design/paper_statement | Methodology - StreamBridge | high
      locator:: Section 3.2 and Algorithm 1
      quote:: StreamBridge proposes three key components to enable streaming capabilities: a memory buffer responsible for storing and retrieving frame tokens over time, a round-decayed compression strategy that efficiently prunes redundant tokens from earlier rounds while preserving the mo...
    - **E5:** system_design/implementation_detail | Methodology - Memory Buffer | high
      locator:: Section 3.2.1
      quote:: Each incoming frame is independently encoded and appended to the buffer alongside any associated query embeddings. Upon the arrival of a user query and a positive activation decision, the buffer content, including both visual and textual embeddings, is flattened into a single...
    - **E6:** algorithm/implementation_detail | Methodology - Round-Decayed Compression | high
      locator:: Section 3.2.2
      quote:: Before each response generation, the model checks whether the current input embedding exceeds MaxLen. If so, starting from the earliest dialogue rounds, visual tokens are progressively merged frame-by-frame until the total length falls below MaxLen. The merging is implemented...
    - **E7:** system_design/implementation_detail | Methodology - Plug-and-play Activation Model | high
      locator:: Section 3.2.3, Figure 3, Appendix A
      quote:: The activation model uses a compact external MLLM such as LLaVA-OV-0.5B. The standard LM head is replaced with a score head for binary classification, and a learnable <ACT> token is appended to visual embeddings. A score above threshold alpha triggers response generation. Trai...
    - **E8:** other/paper_statement | Stream-IT Dataset | high
      locator:: Section 4 and Appendix B
      quote:: Stream-IT is designed for streaming instruction tuning with interleaved multi-turn dialogue. StreamingQA-120K filters approximately 1.28 million clips from WebVid-10M, Panda-70M, and InternVid-10M; each constructed video contains roughly 10 clips with average length exceeding...
    - **E9:** experiment_setup/paper_statement | Experiments - Settings | high
      locator:: Section 5.1 and Appendix D
      quote:: The framework is evaluated using LLaVA-OV-7B, Qwen2-VL-7B, and Oryx-1.5-7B. Stream-IT is supplemented with approximately 600K samples from LLaVA-178K, VCG-Plus, and ShareGPT4Video. The activation model is LLaVA-OV-0.5B, videos are sampled at 1 FPS, OVO/Streaming use multiple-c...
    - **E10:** result/experiment_result | Experiments - Main Results | high
      locator:: Section 5.2, Table 1
      quote:: Qwen2-VL under StreamBridge improves average OVO-Bench from 55.98 to 63.35 and Streaming-Bench from 69.04 to 72.01. LLaVA-OV shows a slight drop from 64.02 to 61.64 and 71.12 to 68.39. Fine-tuning gives Oryx-1.5 gains of +11.92 and +4.2. Qwen2-VL + Stream-IT reaches 71.30 on O...
    - **E11:** result/experiment_result | Experiments - Main Results | high
      locator:: Section 5.2, Table 2
      quote:: Table 2: Oryx-1.5-7B (ours) gets VideoMME 65.5, an increase of 6.7. LLaVA-OV-7B (ours) improves MVBench 56.7 to 59.4, PerceptionTest 57.1 to 63.9, EgoSchema 60.1 to 67.0, but LongVideoBench 56.3 to 54.3. Qwen2-VL (ours) is 64.4 on MVBench versus 67.0 base and 64.4 VideoMME ver...
    - **E12:** result/experiment_result | Experiments - Main Results | high
      locator:: Section 5.2, Table 3
      quote:: On ET-Bench, the question is presented at the beginning and the model must autonomously decide when to respond. Qwen2-VL (ours) reports TVG_F1 34.3, TAL_F1 24.3, DVC_F1 38.3, DVC_Sim 25.1, SLC_F1 22.6, SLC_Sim 17.1. Dispider has TVG_F1 36.1 and TAL_F1 27.3 but lower DVC/SLC ge...
    - **E13:** ablation/ablation | Experiments - In-Depth Analysis | high
      locator:: Section 5.3, Table 4
      quote:: Table 4 compares compression: Truncation scores 68.88/72.79/22.1/16.7; Round-Uniform scores 69.91/74.18/23.8/15.9; Round-Decayed scores 71.30/77.04/25.1/17.1 on OVO Avg., Streaming Avg., DVC_Sim, and SLC_Sim. The text says uniform compression harms latest visual tokens critica...
    - **E14:** result/experiment_result | Experiments - In-Depth Analysis | high
      locator:: Section 5.3, Figure 4
      quote:: The paper evaluates inference latency on a single A100-80G GPU with MaxLen 8k, 16k, and 32k. Its compression method maintains near-constant latency when input tokens exceed MaxLen, whereas models without compression suffer sharply increasing delays and eventually trigger out-o...
    - **E15:** ablation/ablation | Experiments - In-Depth Analysis | high
      locator:: Section 5.3, Tables 5 and 6
      quote:: Training on LLaVA-178K alone causes a marked drop on OVO-Bench and Streaming-Bench; using only Stream-IT without LLaVA-178K leads to declines in general video understanding; removing StreamingQA-120K degrades both streaming and offline benchmarks. MaxLen ablation shows OVO sta...
    - **E16:** implementation/implementation_detail | Appendix C - More Implementation Details | high
      locator:: Appendix C
      quote:: LLaVA-OV-7B uses 49 tokens per frame; Oryx uses 33-59; Qwen2-VL uses 36-64. Main models are fine-tuned for one epoch with learning rate 2e-5; the image encoder is frozen while projector and LLM are trainable. The activation model pools to 16 tokens per frame. Videos longer tha...
    - **E17:** limitation/limitation | Appendix G - Limitations | high
      locator:: Appendix G
      quote:: Stream-IT relies partially on synthetic QA generation and clip concatenation, which may introduce domain shift compared to truly continuous real-world video streams. StreamBridge currently focuses on frame-by-frame streaming under relatively low sampling rates such as 1 FPS; e...
    - **E18:** ablation/ablation | Experiments - In-Depth Analysis | high
      locator:: Section 5.3, Figure 5
      quote:: The compact activation model makes a per-frame decision with frequency determined by threshold alpha; the default alpha is 0.35. Figure 5 shows both excessively low and high alpha decrease DVC_F1 and SLC_F1: low thresholds trigger overly frequent responses, while high threshol...
