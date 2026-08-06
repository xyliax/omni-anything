- **Title:** MiniCPM-o 4.5: Towards Real-Time Full-Duplex Omni-Modal Interaction
- **Summary:** MiniCPM-o 4.5 treats live multimodal interaction as one time-aligned stream so a compact 9B model can watch, listen, and speak at once while keeping deployable edge efficiency.
- **Paper Type:** system
- **Venue:** arXiv preprint 2026
- **Authors:** Junbo Cui, Bokai Xu, Chongyi Wang, Tianyu Yu, Weiyue Sun, Yingjing Xu, Tianran Wang, Zhihui He, Wenshuo Ma, Tianchi Cai, Jiancheng Gui, Luoyuan Zhang, Xian Sun, Fuwei Huang, Moye Chen, Zhuo Lin, Hanyu Liu, Qingxin Gui, Qingzhe Han, Yuyang Wen, Huiping Liu, Rongkang Wang, Yaqi Zhang, Hongliang Wei, Chi Chen, You Li, Kechen Fang, Jie Zhou, Yuxuan Li, Guoyang Zeng, Chaojun Xiao, Yankai Lin, Xu Han, Maosong Sun, Zhiyuan Liu, Yuan Yao; affiliations Unknown
- **Keywords:** omni-modal interaction, full-duplex streaming, multimodal large language model, speech generation, edge inference, Omni-Flow
- ## Orientation
    - **Background:** This paper lives in interactive AI: systems that take in what a person sees, says, types, and hears, then answer back. The key prerequisite is streaming, where information arrives continuously instead of as one finished prompt.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** Most assistants still behave like walkie-talkies: one side talks, then the other side talks. Real conversation needs an assistant that can keep watching and listening while it is already responding.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** The model must decide what happened, whether to speak, what to say, and how to vocalize it while the world keeps changing. If any part runs ahead or falls behind, the answer can become stale.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Put every incoming signal and every outgoing word on one shared clock, then let the next response be conditioned on the newest moment rather than an old turn boundary.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a model-systems paper for omni-modal interaction, meaning one assistant processes vision, sound, text, and speech together; its useful gap is not adding one more input type, but keeping input and output active in the same moment.
      claim_kind:: analyst_assessment
      evidence:: E2, E3
    - **One-Sentence Contribution:** MiniCPM-o 4.5 improves real-time assistant interaction by replacing turn taking with a shared timeline that lets new visual and audio input affect the response while the model is still speaking.
      evidence:: E3, E5, E7
    - **Mental Model:** Picture a live commentator who keeps one eye on the field, one ear on the crowd, and a finger on the microphone; every short moment, the next words are chosen from what just happened, not only from the scene at the start.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is triangulated across capability tables, one full-duplex benchmark, and deployment measurements, with the important caveat that the result tables do not report statistical uncertainty.
      claim_kind:: analyst_assessment
      evidence:: E11, E13, E16
        - Supports C4: instruct vision-language setting; Gemini 2.5 Flash and Qwen3-Omni baselines; OpenCompass score; MiniCPM-o 4.5 reaches 77.6 versus 78.5 and 75.7; support is broad but table-only.
          evidence:: E11
        - Supports C4: vision-only full-duplex LiveSports-3K-CC; LiveCC and StreamingVLM baselines; win rate; MiniCPM-o 4.5 scores 54.4 versus 41.5 and 45.6; support is direct but not audio-inclusive.
          evidence:: E13
        - Supports C3: SeedTTS speech-generation modes; no-interleave and fixed-text baselines; CER/WER and speaker-similarity metrics; Time-Aligned Interleaving trades lower temporal staleness for worse English WER; support is mixed.
          evidence:: E15
        - Supports C4: single RTX 4090 vLLM INT4 setting; Qwen3-Omni-30B-A3B baseline; throughput, first-token latency, and memory; MiniCPM-o 4.5 reports 212.3 tokens/s, 0.58 s, and 11 GB versus 147.8, 0.98 s, and 20 GB.
          evidence:: E16
    - **Main Caveat:** The paper's full-duplex evidence is still narrow: the quantitative real-time benchmark is audio-free and vision-only, qualitative omni-stream demos are not standardized, and the authors report speech instability plus network-sensitive missing fragments.
      claim_kind:: analyst_assessment
      evidence:: E13, E17
- ## Argument Map
    - **Problem and Stakes:** The paper frames full-duplex interaction, meaning input and output happen at the same time, as the next bottleneck for multimodal large language models (MLLMs), which are language-model systems connected to image, audio, and speech modules. The stake is whether assistants can move from passive turn-taking toward ambient help that responds to changing scenes.
      evidence:: E2
    - **Prior Gap:** Prior interactive multimodal systems can process several media types, but the paper argues that they still serialize perception and response or let generated text drift away from speech playback. This leaves two gaps: blocked information flow during speaking and stale spoken output in changing scenes.
      evidence:: E2, E7
    - **Key Insight:** The key insight is to represent the live environment and the assistant's own output as time-aligned streams, meaning short pieces placed on the same clock. Once the data has that shape, a standard causal language model, which predicts the next unit from previous units, can model seeing, listening, deciding, and speaking in one sequence.
      evidence:: E3, E4
    - **Claims:** The paper's thesis rests on four claims: a streaming formulation, an end-to-end architecture, speech timing control, and capability-efficiency evidence.
      claim_kind:: analyst_assessment
        - C1: Omni-Flow turns multimodal interaction into a full-duplex time-aligned process in which perception, output, and proactive behavior share one temporal structure.
          evidence:: E3, E4
        - C2: A 9B end-to-end omni-modal architecture can preserve visual, speech, and text abilities while adding streaming interaction because the components exchange compact token-level representations.
          evidence:: E5, E6, E8
        - C3: Timely speech in full-duplex mode requires explicit timing choices, especially chunk granularity, listen-speak control, and Time-Aligned Interleaving (TAIL), which adapts text generation to speech playback.
          evidence:: E7, E9, E15
        - C4: MiniCPM-o 4.5 is competitive with or ahead of named baselines across vision-language, speech, omni-modal, full-duplex, and efficiency evaluations at its scale.
          evidence:: E11, E12, E13, E16
- ## Mechanism and Design
    - **Core Mechanism:** MiniCPM-o 4.5 uses compact tokens, meaning small model-readable units for text, audio, or visual features, as the common currency between encoders, the language backbone, and speech decoders. Omni-Flow then schedules these units in short time chunks so each output can depend on newly arrived visual and audio input.
      evidence:: E3, E5, E6
        - Visual frames are encoded and resampled into fewer visual tokens, while audio is encoded in chunks and temporally compressed before entering the language backbone.
          evidence:: E6
        - The Qwen3-8B backbone emits text-speed outputs and hidden states, and a smaller speech-token decoder uses those hidden states to produce S3 speech tokens for waveform synthesis.
          evidence:: E5, E6
        - A streaming flow-matching decoder, a neural audio generator that converts speech tokens into waveform segments, uses reference audio from the multimodal system prompt for voice-conditioned synthesis.
          evidence:: E5
    - **Data / Control Flow:** Each time chunk collects environment visual tokens, environment audio tokens, and output-stream tokens; if the assistant should stay silent, the output part contains a listen token, a special control token meaning no spoken/text content now. The sequence is still causal: past and current chunk content condition the next output, so the model can decide both whether to speak and what to say.
      evidence:: E3, E4, E9
        - The three load-bearing streams are env-visual for live scene observations, env-audio for acoustic context and user speech, and out-stream for generated text and speech.
          evidence:: E4
        - The Listen-Speak (LS) formulation separates the binary decision to listen or speak from content generation, instead of mixing listen and text tokens in one output space.
          evidence:: E9
    - **Design Decisions:** The main design choices all protect timing stability: one-second chunks give more context per decision, explicit group boundaries reduce parsing burden, and separated listen-speak control avoids asking one prediction step to decide both action and content. TAIL adds a second timing layer for speech so text generation does not outrun audio playback.
      evidence:: E7, E9, E15
        - Need: responsiveness and coherence compete; choice: use one-second chunks in the reported setting; alternative: shorter chunks; tradeoff: shorter windows react faster but degrade decision stability.
          evidence:: E9
        - Need: speech should match the current scene; choice: TAIL adapts text count from accumulated playback progress; alternative: fixed text-speech ratio; tradeoff: better temporal alignment can reduce speech-recognition accuracy.
          evidence:: E7, E15
        - Need: avoid making the large backbone emit high-rate speech tokens; choice: delegate speech-token generation to a small decoder conditioned by backbone hidden states; tradeoff: extra decoder surface but lower text-generation burden.
          evidence:: E5, E6
    - **Implementation Surface:** The reported system is a deployable stack rather than only a modeling idea: it specifies component sizes, precision, token rates, quantized inference, and a custom llama.cpp-omni runtime for real-time factor (RTF), meaning generated audio time divided by wall-clock time. The implementation surface spans model architecture, training data alignment, inference framework, and local demo deployment.
      evidence:: E16, E18
- ## Evaluation and Evidence
    - **Setup:** The evaluation is broad rather than deeply controlled: it spans vision-language reasoning, OCR, hallucination, video, speech recognition, speech question answering, text-only benchmarks, omni-modal understanding, full-duplex streaming, and inference efficiency. Baselines include proprietary models, open multimodal models, speech systems, and streaming video-language systems, but the paper does not report repeat counts or confidence intervals.
      claim_kind:: analyst_assessment
      evidence:: E10, E11, E12, E13, E16
    - **Claim-Evidence Matrix:** The evidence is strongest for capability and deployment efficiency, moderate for design choices, and weakest for real-world full-duplex generality because the benchmark coverage is still narrow.
      claim_kind:: analyst_assessment
      evidence:: E9, E11, E13, E16, E17
        - C1: Supported mainly by method formulation and one streaming benchmark; the formulation is clear, but fully standardized full-duplex audio-visual evaluation is missing.
          claim_kind:: analyst_assessment
          evidence:: E3, E4, E13
        - C2: Supported by architecture details plus broad capability results; the causal link between compact token interfaces and retained capability is plausible but not isolated by a full architecture ablation.
          claim_kind:: analyst_assessment
          evidence:: E5, E6, E11, E12
        - C3: Supported by direct design and speech-mode ablations; the tradeoff is explicit because dynamic TAIL is temporally motivated but not the best recognition-quality mode.
          claim_kind:: analyst_assessment
          evidence:: E7, E9, E15
        - C4: Supported by many benchmark tables and efficiency measurements; support is table-based and lacks reported variance, so it is useful for recall but not a statistical dominance claim.
          claim_kind:: analyst_assessment
          evidence:: E11, E12, E13, E16
    - **Headline Results:** Headline results show a compact model that is unusually broad: strong vision-language and OCR scores, competitive speech understanding and generation, top scores on several omni-modal benchmarks, and much lower memory than Qwen3-Omni in the reported INT4 setup. These results support scale-efficiency as much as raw quality.
      evidence:: E11, E12, E13, E16
        - Vision-language: MiniCPM-o 4.5 is close to Gemini 2.5 Flash on OpenCompass and exceeds listed open baselines on several instruct-mode metrics, while lagging on some hard reasoning entries such as MMMU.
          evidence:: E11
        - Speech and omni-modal: the paper reports leading entries on selected speech QA/generation metrics and best results on five of seven simplex omni-modal benchmarks, plus a LiveSports-3K-CC win-rate lead.
          evidence:: E12, E13
        - Efficiency: MiniCPM-o 4.5 fits the reported RTX 4090 settings where Qwen3-Omni BF16 runs out of memory, and INT4 reduces memory to 11 GB in both vLLM and llama.cpp-omni measurements.
          evidence:: E16
    - **Ablations and Sensitivity:** The ablations are useful because they test the paper's own timing assumptions rather than only final benchmark scores. Their shared message is that the system works by balancing time pressure against model stability: too-short chunks, over-aggressive length rewards, or stricter temporal speech alignment can reduce quality.
      claim_kind:: analyst_assessment
      evidence:: E9, E14, E15
        - Omni-Flow design: explicit boundaries and LS control beat implicit or LT variants, and the reported one-second chunk gives the best table balance.
          evidence:: E9
        - Length reward: the smooth reward reduces thinking length less aggressively than Kimi K1.5-style reward while improving the benchmark average in the reported lightweight RL experiment.
          evidence:: E14
        - Speech mode: fixed-text interleaving wins CER/WER, while dynamic TAIL is justified as the full-duplex timing mode despite worse English WER.
          evidence:: E15
    - **Reproducibility Gaps:** Model, code, data, and scripts are not specified as available in the supplied paper text; the paper mentions a web demo, a lightweight demo system, and llama.cpp-omni, but not enough release detail to reproduce training or every benchmark. Hardware is partially specified for inference, while training compute, data licenses, variance, and benchmark prompts are not reported.
      claim_kind:: analyst_assessment
      evidence:: E16, E17
- ## Technical Judgment
    - **What Holds Up:** The strongest part of the paper is the data representation: aligning environment input and assistant output on one clock is the right abstraction for breaking turn-taking without inventing a new backbone. The efficiency story also holds up better than most capability-only model reports because the paper gives memory, latency, throughput, and RTF measurements on named hardware.
      claim_kind:: analyst_assessment
      evidence:: E3, E4, E9, E16
    - **Where It May Fail:** The main failure boundary is long, noisy, truly bidirectional real-world use: the quantitative full-duplex test is vision-only, TAIL trades away speech quality, and the authors acknowledge robustness, speech instability, code-mixing, latency, missing fragments, and simple proactive behavior. Benefits may diminish when network conditions are unstable, when speech timing is harder than the benchmark captures, or when proactive behavior needs planning rather than local scene reactions.
      claim_kind:: analyst_assessment
      evidence:: E13, E15, E17
    - **Relation to Other Work:** Compared with Qwen3-Omni, Kimi-Audio, CosyVoice2, LiveCC, and StreamingVLM as presented here, MiniCPM-o 4.5 is positioned less as a specialist speech or video model and more as an integrated real-time interaction stack. The technical difference is the shared temporal stream plus deployable runtime, not just better scores on the same offline multimodal benchmarks.
      claim_kind:: analyst_assessment
      evidence:: E2, E7, E11, E12, E13, E16
    - **Transferable Lesson:** When an AI system must act while sensing, first make time an explicit data dimension, then separate control decisions from content decisions. This pattern transfers beyond speech assistants: streaming agents, robotics interfaces, and live monitoring systems can often improve by aligning observation, action, and silence decisions before adding model capacity.
      claim_kind:: analyst_assessment
      evidence:: E3, E4, E9
- ## Glossary
  collapsed:: true
    - multimodal large language model: A language-model backbone connected to encoders or decoders for non-text signals such as images, video, audio, and speech.
    - full-duplex interaction: An interaction mode where the assistant can receive new input and produce output at the same time, rather than alternating turns.
    - token: A small unit the model reads or writes; in this paper tokens can represent text, visual features, audio features, or speech-code units.
    - Omni-Flow: The paper's framework for placing visual input, audio input, and assistant output on a shared time axis.
    - time chunk: A short interval of the live interaction; Omni-Flow groups the visual, audio, and output tokens belonging to the same interval.
    - Listen-Speak control: A control formulation where the model first decides whether to listen or speak, then generates content if it chooses to speak.
    - Time-Aligned Interleaving: The paper's speech-generation strategy that adapts how much text to generate so speech playback stays close to the current time boundary.
    - S3 speech token: A discrete speech-code unit generated by the speech-token decoder before waveform synthesis.
    - flow-matching decoder: A neural audio generator that converts speech tokens into waveform audio in a streaming way.
    - real-time factor: An inference-speed measure for audio generation; lower values mean the system generates faster than playback time.
    - Group Relative Policy Optimization: The reinforcement-learning method the paper uses to improve reasoning and instruction following with accuracy and auxiliary rewards.
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/metadata | Title and Abstract | high
      locator:: title block and abstract
      quote:: The paper is titled MiniCPM-o 4.5: Towards Real-Time Full-Duplex Omni-Modal Interaction, appears as arXiv:2604.27393v1 in cs.CL on 30 Apr 2026, and presents MiniCPM-o 4.5 with a total of 9B parameters.
    - **E2:** problem/paper_statement | 1 Introduction | high
      locator:: Introduction, paragraphs 1-2 and Figure 3
      quote:: The authors argue that modality coverage and latency are no longer the only bottlenecks. Existing models still alternate perception and response, cannot update during generation, and remain request-driven rather than context-driven.
    - **E3:** method/paper_statement | 3 Omni-Flow | high
      locator:: Section 3 opening
      quote:: Omni-Flow coordinates omni-modal input and output streams on a shared temporal axis. It divides continuous interaction into fine-grained time windows and processes newly arrived signals while producing the next output.
    - **E4:** algorithm/paper_statement | 3.1 Time-Aligned Streams and 3.2 Unified Serialization | medium
      locator:: Sections 3.1-3.2
      quote:: The framework identifies env-visual, env-audio, and out-stream. For each chunk, visual tokens, audio tokens, and output tokens are grouped, with a special listen token when the assistant should produce no content.
    - **E5:** system_design/implementation_detail | 2 End-to-End Omni-Modal Architecture | high
      locator:: Section 2 opening and Figure 4
      quote:: The model combines streaming visual and audio encoders, a Qwen3-8B language backbone, an interleaved speech-token decoder, and a streaming flow-matching waveform decoder, with learnable components connected through token-level hidden states.
    - **E6:** optimization/implementation_detail | 2 End-to-End Omni-Modal Architecture | high
      locator:: Visual Encoding, Audio Encoding, Text Decoding
      quote:: The visual path compresses each encoded slice from 1024 tokens to 64 tokens. The audio path produces 50 feature tokens per second then compresses to 10 audio tokens per second. The backbone only emits text-speed tokens.
    - **E7:** algorithm/paper_statement | 3.4 Time-Aligned Interleaving for Timely Speech Generation | high
      locator:: Section 3.4 and Figure 5
      quote:: Time-Aligned Interleaving adaptively chooses how much text to generate so speech playback approaches the current chunk boundary. It can generate fewer tokens after earlier delay and defers a bounded look-ahead for pronunciation and prosody.
    - **E8:** experiment_setup/paper_statement | 4 Data and 5 Training | high
      locator:: Sections 4.3, 5.1-5.4
      quote:: Full-duplex samples contain visual input, audio input, output text, and output speech tagged with time indices. Training proceeds through speech pretraining, joint pretraining, supervised fine-tuning, and reinforcement learning.
    - **E9:** ablation/ablation | 3.3 Design Tradeoffs | medium
      locator:: Table 1 and surrounding analysis
      quote:: The design ablation varies chunk size, explicit boundaries, and listen-speak versus listen-text control. The authors report 1.0 s chunks, explicit boundaries, and separated listen-speak control as the best stability-responsiveness balance.
    - **E10:** experiment_setup/paper_statement | 6.1 Modalities and Domains | high
      locator:: Section 6.1
      quote:: Evaluation covers vision-language understanding, speech understanding and generation, text capability, omni-modal streaming interaction, and full-duplex streaming. Benchmarks span STEM reasoning, OCR, hallucination, video, ASR, speech QA, and audio-visual tasks.
    - **E11:** result/experiment_result | 6.2 Vision-Language Results | medium
      locator:: Tables 2-3
      quote:: In instruct mode MiniCPM-o 4.5 reports OpenCompass 77.6, MMBench EN 87.6, MathVista 80.1, HallusionBench 63.2, Mantis-Eval 79.7, and several document/OCR scores competitive with larger or proprietary baselines.
    - **E12:** result/experiment_result | 6.3 Speech Results | medium
      locator:: Tables 4-5
      quote:: On speech tasks the model leads selected semantic benchmarks such as CoVoST 2 en-to-zh, MELD, VoiceBench AlpacaEval, and Speech TriviaQA; for generation it reports lowest SeedTTS ZH CER and EN WER among listed baselines.
    - **E13:** result/experiment_result | 6.5 Omni-modal and Streaming Results | medium
      locator:: Tables 7-8
      quote:: MiniCPM-o 4.5 reports best results on five of seven simplex omni-modal benchmarks. On LiveSports-3K-CC, an audio-free full-duplex benchmark, it scores 54.4 versus 41.5 for LiveCC and 45.6 for StreamingVLM.
    - **E14:** ablation/ablation | 6.6 Analysis | medium
      locator:: Table 9 and Figure 6
      quote:: The smooth length reward reports a thinking benchmark average of 74.3 with 35.3 percent length reduction, compared with 73.5 for no length reward and 73.0 with the more aggressive Kimi K1.5-style reward.
    - **E15:** ablation/ablation | 6.6 Analysis | medium
      locator:: Table 10
      quote:: The speech-mode comparison shows fixed-text interleaving gives best SeedTTS CER/WER, while dynamic Time-Aligned Interleaving has worse EN WER but is presented as the mode designed for temporally aligned full-duplex interaction.
    - **E16:** result/experiment_result | 7 Efficient Real-Time Inference | medium
      locator:: Tables 11-12
      quote:: On a single RTX 4090 with vLLM, MiniCPM-o 4.5 INT4 reports 212.3 tokens/s, 0.58 s first-token latency, and 11 GB memory. llama.cpp-omni INT4 reports real-time factor 0.21 with 11 GB memory.
    - **E17:** limitation/limitation | 8 Conclusion | high
      locator:: Limitations paragraph
      quote:: The authors call the work an early exploration, note that long dynamic real-world robustness needs more validation, and report occasional streaming speech instability, English-Chinese mixing, web-demo latency, missing fragments, and simple proactive behavior.
    - **E18:** implementation/implementation_detail | Appendix A Model Configuration | high
      locator:: Table 13
      quote:: The appendix lists 9.34B learnable parameters in bfloat16, including a SigLIP visual encoder, visual resampler, Whisper Medium audio encoder, Qwen3-8B backbone, projector layers, and a speech-token decoder.
