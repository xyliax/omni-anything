- **Title:** DuplexOmni: Real-Time Listening, Seeing, Thinking, and Speaking for Full-Duplex Interaction
- **Summary:** DuplexOmni frames real-time multimodal assistants as two cooperating processes: a low-latency interaction model keeps listening and speaking while a pluggable thinking layer performs slower reasoning or tool use in the background.
- **Paper Type:** system
- **Venue:** arXiv preprint 2026
- **Authors:** Muye Huang (Xi'an Jiaotong University / MOE KLNN Lab), Lingling Zhang (Xi'an Jiaotong University / MOE KLNN Lab), Xingyu Yu (MOE KLNN Lab), Lei Shi (Meituan), Zhanyu Ma (Meituan), Jun Xu (Meituan), Jiuchong Gao (Meituan), Jinghua Hao (Meituan), Renqing He (Meituan), Jun Liu (Xi'an Jiaotong University / MOE KLNN Lab)
- **Keywords:** full-duplex interaction, omni model, streaming speech generation, multimodal dialogue, asynchronous reasoning, training data construction
- ## Orientation
    - **Background:** This paper lives in voice and vision assistants that try to hear, see, reason, and answer in one system. The key setting is a conversation where both sides can listen and speak at the same time, rather than taking clean turns.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A helpful assistant should not go silent every time it needs to search, calculate, or look more carefully. It should keep the user engaged while new speech or visual information may still arrive.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** Speaking quickly, listening for interruptions, watching the scene, and doing slow reasoning compete for attention and time. If they are forced through one queue, slow work blocks live conversation.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Let one part handle the live conversation and another part think in the background, then stream useful pieces back into later replies.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a real-time multimodal-assistant systems paper: it targets the gap between models that can listen and speak at once (full-duplex interaction) and models that can do slower reasoning or tool use without freezing the conversation.
      claim_kind:: analyst_assessment
      evidence:: E2, E3
    - **One-Sentence Contribution:** DuplexOmni improves continuous audio-video dialogue by letting a fast interaction model keep the conversation alive while a separate background thinking process returns information later.
      evidence:: E1, E4
    - **Mental Model:** Picture a front-desk helper who keeps talking, listening, and watching the visitor while a specialist in the back room searches, calculates, or plans and passes notes forward.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is the combination of realtime benchmark gains and ablations showing that interaction quality and reasoning strength come from different parts of the system.
      evidence:: E11, E12
        - Supports C4: full DuplexOmni with Gemini-3.1-Flash-Lite thinking layer; realtime omni baselines; Full DuplexBench ToR; 72.6% versus 36.3% for MiniCPM-o 4.5 at similar latency; supported, but no variance or repeat count is reported.
          evidence:: E10, E11
        - Supports C4: full system; ablations without the default thinking layer; Big Bench Audio; 77.2% versus 50.3% with weak thinking and 22.2% without thinking; supported, but statistical uncertainty is not reported.
          evidence:: E12
        - Supports C3: Writer-Director annotated corpus; no direct baseline; coverage of delayed reasoning, silence, assistant initiation, overlap, and reset patterns; broad coverage is supported, but human annotation quality is not independently audited.
          evidence:: E8, E16
    - **Main Caveat:** Trust is bounded by preprint-style evidence: the paper reports benchmark tables without error bars, admits weak video and English coverage, and shows short utterances remain hard under streaming full-duplex speech recognition.
      claim_kind:: analyst_assessment
      evidence:: E13, E14
- ## Argument Map
    - **Problem and Stakes:** The paper argues that real-time audio-video dialogue fails when listening, speaking, reasoning, and tool use are serialized: slow reasoning blocks speech, while stripping reasoning away makes the assistant less useful. The stake is not just lower latency, but keeping the social rhythm of a conversation while still allowing hard tasks.
      evidence:: E2
    - **Prior Gap:** The prior-work gap is between broad all-modal models, which often remain request-response systems, and full-duplex speech models, which listen while speaking but still have trouble when a dialogue needs longer reasoning. The paper positions DuplexOmni as a coordination design rather than only a larger model.
      evidence:: E3
    - **Key Insight:** The key insight is to split live interaction from slow cognition: a low-latency interaction layer handles audio, video, dialogue rhythm, and speech output, while a pluggable thinking layer runs stronger language models or tools asynchronously. This makes reasoning a background service rather than a blocking stage.
      evidence:: E4
    - **Claims:** The paper's claim chain has four falsifiable parts: the architecture should preserve live interaction, the interaction model should implement that architecture at streaming granularity, the data pipeline should teach temporal behavior, and the benchmark evidence should separate interaction quality from reasoning strength.
      evidence:: E1, E4, E11
        - C1: Decoupling a realtime interaction layer from an asynchronous thinking layer lets the system continue listening, seeing, speaking, and updating the dialogue while slower reasoning or tool use proceeds.
          evidence:: E1, E4
        - C2: The DuplexOmni model can implement the interaction layer by processing fixed speech-video slices and generating text plus speech for each slice with a Thinker-Talker architecture.
          evidence:: E5, E6
        - C3: A Writer-Director data pipeline can convert ordinary dialogue content into temporally annotated training samples for interruption, overlap, waiting, thinking triggers, delayed feedback, and silence.
          evidence:: E7, E8, E16
        - C4: On the reported benchmarks, DuplexOmni improves full-duplex interaction and streaming audio reasoning under realtime settings, and ablations attribute these gains to both the interaction layer and the thinking layer.
          evidence:: E10, E11, E12
- ## Mechanism and Design
    - **Core Mechanism:** DuplexOmni is organized as an interaction layer plus a thinking layer. The interaction layer continuously consumes user speech, video frames, dialogue history, and returned thinking fragments, while the thinking layer acts as a background source of deeper reasoning or tool results.
      evidence:: E4, E5
        - The interaction layer owns live dialogue control: it decides when to respond, wait, stop, request help, and fold returned results into later speech.
          evidence:: E4
        - The thinking layer is pluggable: the paper says it may be a strong language model, a multimodal large language model (MLLM), or a task-specific agent for reasoning, tool use, or planning.
          evidence:: E4
        - The join point is streaming feedback: thinking results arrive as intermediate fragments with control tokens, and the interaction layer may continue, revise, or stop that stream as the conversation changes.
          evidence:: E4, E8
    - **Data / Control Flow:** Execution is time-sliced: at each fixed slice, the model reads the previous slice's audio-video input, dialogue history, and thinking feedback, then emits a thinking-control signal, an interpretation of new user input, assistant text, and assistant speech. This turns full-duplex behavior into a repeated streaming update rather than a turn-level transaction.
      evidence:: E5, E6
        - The Thinker, the text-and-context part of the model, generates assistant text tokens and hidden states from the current multimodal context.
          evidence:: E6
        - The Talker, the speech-generating part, conditions on Thinker outputs and previous speech-code history to autoregressively produce residual vector quantization (RVQ) codec tokens, which are discrete audio codes decoded into waveform.
          evidence:: E6
        - For realtime inference, Thinker text generation and Talker speech generation run as an asynchronous pipeline, with cache-based incremental decoding and graph execution optimization used to reduce repeated speech-generation work.
          evidence:: E9
    - **Design Decisions:** The main design choices all serve the same pressure point: preserve conversational immediacy while allowing computation that may take longer than a speech chunk. The tradeoff is that correctness now depends on clean coordination signals, realistic temporal data, and robust handling of stale or interrupted thinking results.
      claim_kind:: analyst_assessment
      evidence:: E4, E7, E8, E9
        - Need: avoid blocking speech during tool use; choice: decouple live interaction from background reasoning; closest alternative: one serial model pipeline; tradeoff: the interaction layer must decide when returned reasoning is still relevant.
          evidence:: E2, E4
        - Need: train and infer on continuous streams; choice: fixed speech-video slices with carried history; closest alternative: ordinary turn-based dialogue; tradeoff: slice-level state is easier to schedule but short fragments can be hard to recognize.
          evidence:: E5, E13
        - Need: supervise timing behaviors absent from ordinary dialogue; choice: generate a script, then add temporal control tokens; closest alternative: raw multi-turn text; tradeoff: the training signal is explicit but synthetic annotation quality becomes load-bearing.
          evidence:: E7, E8, E16
    - **Implementation Surface:** The reported implementation initializes from Qwen3-Omni, trains with two-stage supervised fine-tuning, alternates Thinker and Talker optimization, synthesizes speech with Qwen3-TTS, encodes speech with the Mimi codec, and trains on a large H20 GPU cluster. The paper states it will release model weights, training data, and training and inference implementation, but the provided text does not give repository links or exact reproduction scripts.
      evidence:: E1, E15, E16
- ## Evaluation and Evidence
    - **Setup:** The comparison covers realtime omni and speech-to-speech systems under streaming or realtime settings, using Full DuplexBench for turn-taking interaction, Big Bench Audio for streaming audio understanding, Daily-Omni for general omni capability, LibriSpeech word error rate (WER) for speech recognition quality, and latency for response delay. The default full system uses DuplexOmni as the interaction layer and Gemini-3.1-Flash-Lite as the thinking layer.
      evidence:: E10
    - **Claim-Evidence Matrix:** The evidence is strongest for C4's benchmark and ablation claims, reasonably direct for C1-C2's implementation claims, and supportive but less independently validated for C3's synthetic data-pipeline claim. No reported result includes confidence intervals, repeated-run statistics, or human preference uncertainty.
      claim_kind:: analyst_assessment
      evidence:: E10, E11, E12, E16
        - C1 is supported by the described non-blocking interaction/thinking split and by ablations where replacing thinking barely changes Full DuplexBench ToR, but the paper does not isolate failure cases where stale thinking feedback harms dialogue.
          claim_kind:: analyst_assessment
          evidence:: E4, E12
        - C2 is supported by the model's slice-level architecture and reported latency, but the paper gives limited profiling detail for the exact scheduler, cache reuse, or graph optimization contribution.
          claim_kind:: analyst_assessment
          evidence:: E5, E6, E9, E11
        - C3 is supported by the control-token design and corpus statistics; C4 is supported by benchmark tables and ablations, with the caveat that baseline API settings and evaluation variance are only partly observable from the paper text.
          claim_kind:: analyst_assessment
          evidence:: E8, E10, E11, E12, E16
    - **Headline Results:** The headline result is that DuplexOmni reports the best Full DuplexBench ToR among realtime baselines while maintaining around half-second latency, and also reports the best Big Bench Audio score in the table. The closest directly comparable interaction baseline by latency is MiniCPM-o 4.5, where DuplexOmni reports much higher ToR but lower Daily-Omni accuracy.
      evidence:: E11
        - Supported claim: C4; configuration: full DuplexOmni; baseline: MiniCPM-o 4.5; metric: Full DuplexBench ToR, higher is better; delta: 72.6% versus 36.3%; uncertainty: not reported; caveat: benchmark details and human-rating variance are not shown in the excerpt.
          evidence:: E10, E11
        - Supported claim: C2 and C4; configuration: realtime full system; baseline: MiniCPM-o 4.5 and Qwen realtime variants; metric: latency, lower is better; delta: 0.506 s versus 0.502 s for MiniCPM-o 4.5 and 1.25-1.28 s for Qwen realtime variants; uncertainty: not reported.
          evidence:: E10, E11
        - Supported claim: C4; configuration: full DuplexOmni; baseline: Gemini-3.1-Flash-Lite thinking-only and Gemini Live; metric: Big Bench Audio, higher is better; delta: 77.2% versus 58.9% and 57.9%; uncertainty: not reported; caveat: the full system uses a Gemini thinking layer.
          evidence:: E10, E11, E12
    - **Ablations and Sensitivity:** The ablations support the layered interpretation: weakening the thinking layer leaves Full DuplexBench nearly unchanged but sharply reduces Big Bench Audio, while removing thinking reduces reasoning further. The ASR analysis shows sensitivity to utterance length, with short user fragments much harder than longer ones.
      evidence:: E12, E13
        - Supported claim: C1 and C4; configuration: weak thinking versus full thinking; baseline: full system; metric: Full DuplexBench ToR and Big Bench Audio; delta: ToR 72.6% to 72.1%, Big Bench Audio 77.2% to 50.3%; support status: supports separation of interaction and reasoning strength.
          evidence:: E12
        - Supported claim: C4; configuration: no thinking layer; baseline: full system; metric: Big Bench Audio; delta: 77.2% to 22.2%; support status: supports the claim that the thinking layer sets the reasoning ceiling.
          evidence:: E12
        - Supported claim: boundary on C2 and C4; configuration: full-duplex ASR by utterance length; baseline: longer utterances; metric: WER, lower is better; delta: 25.1% for 1-5 words versus 8.8% for 21+ words; support status: shows short low-context speech is a weakness.
          evidence:: E13
    - **Reproducibility Gaps:** The paper promises release of weights, training data, and training and inference implementation, but the provided text itself does not include a repository, exact evaluation scripts, random seeds, repeated runs, cost budget, or enough proprietary API details to rerun all baselines. Reuse is also constrained by the large training stack, synthetic speech generation, and dependence on a strong external thinking model in the default configuration.
      claim_kind:: analyst_assessment
      evidence:: E1, E10, E15, E16
- ## Technical Judgment
    - **What Holds Up:** The architecture is coherent because the paper identifies a real scheduling conflict and assigns the fast, user-facing loop and slow reasoning loop to different execution spaces. The ablation pattern is also internally consistent: interaction quality mostly follows the DuplexOmni model, while streaming audio reasoning follows the thinking layer plus the interaction layer's filtering and organization.
      claim_kind:: analyst_assessment
      evidence:: E2, E4, E11, E12
    - **Where It May Fail:** The system may fail when user intent changes faster than thinking feedback can be invalidated, when visual grounding matters more than the small video-call corpus can support, or when short speech fragments carry the decisive cue. Benefits should diminish in low-latency tasks that require no external reasoning, and in languages or accents underrepresented in the training data.
      claim_kind:: analyst_assessment
      evidence:: E8, E13, E14, E16
    - **Relation to Other Work:** Relative to broad omni models, DuplexOmni emphasizes interaction scheduling rather than only modality unification. Relative to full-duplex speech systems such as Moshi-like or flattened speech-text approaches, it adds an explicit asynchronous reasoning/tool layer and temporal supervision for when to wait, cut off, reset, or incorporate delayed results.
      claim_kind:: analyst_assessment
      evidence:: E3, E4, E8
    - **Transferable Lesson:** The transferable pattern is to split latency-critical interaction from accuracy-critical deliberation, then train the boundary explicitly with control signals rather than hoping a single sequence model learns the timing protocol implicitly. This applies beyond voice assistants to any interactive AI system where the user-facing loop must remain responsive while deeper computation continues.
      claim_kind:: analyst_assessment
      evidence:: E4, E7, E8, E9
- ## Glossary
  collapsed:: true
    - full-duplex interaction: A dialogue mode where the assistant can keep receiving user speech while it is speaking, so overlap, interruption, and backchannels are part of normal operation.
    - omni model: A model that handles multiple modalities such as speech, text, image, video, and sometimes speech output in one unified interaction system.
    - interaction layer: The fast layer responsible for live listening, watching, dialogue rhythm, immediate text response, and speech output.
    - thinking layer: A pluggable slower layer that can run a strong language model, multimodal model, or tool agent and stream useful results back to the interaction layer.
    - Thinker-Talker architecture: A speech-generation design where a text/context model produces linguistic states and a speech model converts those states into audio codec tokens.
    - time-sliced inference: A streaming inference schedule that repeatedly processes fixed-duration chunks of input and emits the next chunk of control, text, and speech output.
    - residual vector quantization: An audio representation that stores speech as multiple layers of discrete codes; the Talker predicts these codes before a decoder turns them back into waveform.
    - MTP module: The module used after the first codec layer prediction to fill the remaining residual codebooks for each speech frame.
    - Director control tokens: Special annotations that mark when background thinking starts, when returned thinking is injected, where overlap begins, where speech stops, when thinking resets, and when shared silence occurs.
    - real-time factor: The ratio between generation time and audio duration; below one means a chunk can be generated before it finishes playing.
    - KV cache: Saved attention state from earlier tokens that lets an autoregressive model avoid recomputing the whole prefix during incremental decoding.
    - word error rate: A speech recognition error metric; lower is better, and the paper uses it to show that short utterances are difficult under full-duplex streaming.
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/paper_statement | Abstract and Introduction | high
      locator:: Abstract; Section 1 contributions
      quote:: We present DuplexOmni, a method for real-time multimodal full-duplex interaction. DuplexOmni separates model capability into an interaction layer and a thinking layer, which collaborate asynchronously in parallel.
    - **E2:** problem/paper_statement | Introduction | high
      locator:: Section 1, Figure 1 discussion
      quote:: When interaction involves deep thinking or tool use, the model often pauses the ongoing dialogue. It then waits for reasoning or tool results before continuing its response. This causes clear interruptions.
    - **E3:** gap/paper_statement | Related work | high
      locator:: Sections 2.1 and 2.2
      quote:: Most of these models still organize interaction in a request-driven manner: user input is collected, the model performs understanding and generation, and then a response is returned. This mode is suitable for single-turn or multi-turn task processing, but cannot handle user interaction in real time.
    - **E4:** system_design/implementation_detail | Method | high
      locator:: Section 3 and Section 3.1.1
      quote:: The interaction layer handles real-time dialogue, while the thinking layer performs background reasoning. When the current interaction requires external assistance, the interaction layer passes the user context to the thinking layer... This request does not block real-time interaction.
    - **E5:** algorithm/implementation_detail | DuplexOmni Model | high
      locator:: Section 3.1.2, Time-Sliced Full-Duplex Modeling
      quote:: We divide continuous interaction into fixed 480 ms slices. At slice t, the model consumes the dialogue history, the intermediate results returned by the thinking layer, and the inputs from slice t-1.
    - **E6:** implementation/implementation_detail | DuplexOmni Model | high
      locator:: Section 3.1.2, Model Architecture
      quote:: DuplexOmni model follows the Thinker-Talker speech generation structure in the Qwen-Omni family. The Thinker is the internal MLLM backbone that processes the current context and generates Assistant text tokens. The Talker converts the generated linguistic states into streaming speech.
    - **E7:** method/paper_statement | Data Construction | high
      locator:: Section 3.2 opening
      quote:: Existing multi-turn dialogue data is mostly turn-based. It only records user and assistant utterances, and lacks temporal information. Therefore, it cannot describe when the model should speak, stop, wait, trigger background thinking, or use returned information.
    - **E8:** method/implementation_detail | Writer-Director Data Pipeline | high
      locator:: Section 3.2.2 and Appendix A, Table 4
      quote:: The Director converts this script into a structured sample with temporal control signals... [THINK] triggers background reasoning... [CUT] marks the actual stopping point... [WAIT] means that the user adds a new condition, so the background reasoning should pause or revise.
    - **E9:** optimization/implementation_detail | Real-Time Duplex Inference | high
      locator:: Section 3.3
      quote:: DuplexOmni uses RTF < 1 as the latency target for speech generation... DuplexOmni decouples Thinker-based text generation from Talker-based speech generation and runs them as an asynchronous pipeline.
    - **E10:** experiment_setup/paper_statement | Experiments | medium
      locator:: Section 4.1 Settings
      quote:: We compare DuplexOmni with recent real-time omni models and speech-to-speech systems, including MiniCPM-o, Doubao, Qwen-Omni realtime variants, and Gemini live variants. All models are evaluated under their streaming or realtime settings.
    - **E11:** result/experiment_result | Performance Comparison | medium
      locator:: Section 4.4 and Table 1
      quote:: DuplexOmni achieves 72.6% ToR on Full DuplexBench, substantially outperforming all realtime baselines, while keeping a response latency of 0.506s. DuplexOmni achieves the best Big Bench Audio score of 77.2% and remains competitive on Daily-Omni.
    - **E12:** ablation/ablation | Ablation Study | medium
      locator:: Section 4.5 and Table 2
      quote:: When the thinking layer is replaced by a weaker model, Big Bench Audio drops from 77.2% to 50.3%; removing the thinking layer further reduces it to 22.2%.
    - **E13:** result/experiment_result | Full-Duplex ASR Analysis | medium
      locator:: Section 4.6 and Table 3
      quote:: Table 3 shows that DuplexOmni performs worse on short utterances, with WER dropping from 25.1% for 1-5 words to 8.8% for 21+ words. This suggests that short, low-context speech fragments in full-duplex interaction remain a key challenge.
    - **E14:** limitation/limitation | Limitations | high
      locator:: Limitations
      quote:: First, its video capability remains limited because the amount of video-call and visually grounded interaction data is relatively small. Second, its English speech ability is weaker than desired, partly due to the training data being dominated by Chinese speech.
    - **E15:** experiment_setup/implementation_detail | Training | high
      locator:: Section 4.3 Training
      quote:: Initialized from Qwen3-Omni, it is trained with two-stage SFT... The learning rate is 1e-5 for the Thinker and 1e-4 for the Talker, with a batch size of 128. Training is conducted with Megatron-swift-3.12 on 128 Nvidia H20 GPUs.
    - **E16:** experiment_setup/paper_statement | Data and Appendix C | high
      locator:: Sections 4.2, C.1-C.3, Tables 5-7
      quote:: We build about 620K scenario seeds... The dialogue content contains about 3.02M raw conversations, including 10K video-call conversations... delayed reasoning 94.3... Samples containing >=2 patterns 90.7.
