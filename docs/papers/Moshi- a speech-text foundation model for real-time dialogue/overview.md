- **Title:** Moshi: a speech-text foundation model for real-time dialogue
- **Summary:** Moshi shows that real-time spoken dialogue can be modeled as streaming speech-to-speech generation by combining a text language-model backbone, a causal semantic-acoustic audio codec, parallel speaker streams, and time-aligned text scaffolding.
- **Paper Type:** system
- **Venue:** arXiv preprint 2024
- **Authors:** Alexandre Defossez; Laurent Mazare; Manu Orsini; Amelie Royer; Patrick Perez; Herve Jegou; Edouard Grave; Neil Zeghidour; Kyutai
- **Keywords:** speech-to-speech dialogue, full-duplex interaction, audio language modeling, neural audio codec, residual vector quantization, streaming inference, Inner Monologue
- ## Orientation
    - **Background:** Spoken dialogue systems connect speech with language models. The usual path turns audio into text, lets a text model answer, then turns text back into audio; a speech-to-speech model instead treats sound itself as the object to model.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A voice assistant that waits for tidy turns feels unlike conversation. People interrupt, overlap, pause, laugh, hesitate, and communicate meaning through tone as well as words.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** Speech carries words, timing, silence, voice, emotion, and background sound at once. A model must react quickly without throwing away these signals or confusing who is speaking.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Let one model keep listening while it speaks by representing both sides as parallel streams of small sound-and-text symbols.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a speech-systems view of conversational agents: it attacks the gap between text-centered voice assistants and live spoken conversation, where timing, overlap, silence, and voice information matter.
      claim_kind:: analyst_assessment
      evidence:: E2, E17
    - **One-Sentence Contribution:** Moshi improves real-time spoken dialogue by representing both speakers as parallel streams of small audio-and-text symbols so one model can listen and speak without waiting for clean turns.
      evidence:: E1, E7, E8
    - **Mental Model:** Picture two people on open phone lines: Moshi keeps a running notebook of what it is about to say while also hearing the other line, and it updates both sound and words in small time slices.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is the combination of component ablations, human codec evaluation, spoken question answering, and generated-dialogue tests rather than any single benchmark.
      claim_kind:: analyst_assessment
      evidence:: E5, E11, E12, E13
        - Supports C2: Mimi at 24kHz, 12.5Hz, and 1.1kbps with adversarial-only training; closest semantic-codec baseline SemantiCodec; human MUSHRA, a listening quality test; +16.2 points; strong support within the reported listening setup.
          evidence:: E5
        - Supports C3: reduced-latency acoustic-delay setting; independent classification heads as baseline; token perplexity; 135.4 to 36.8 with RQ-Transformer; strong support for the modeling choice, with perplexity tied to that delay pattern.
          evidence:: E11
        - Supports C4: spoken question answering after instruction tuning; SpeechGPT and Spectron as baselines; accuracy; Moshi reaches 26.6 Web Questions, 62.3 LlaMA Questions, and 22.8 Audio Trivia QA; strong comparative support, but still below text-only Helium.
          evidence:: E12
    - **Main Caveat:** The paper proves a convincing integrated prototype, but broad trust still depends on hard-to-reproduce ingredients: massive private-scale audio, synthetic conversation generation, voice conditioning, and safety analyses that are narrower than the deployment surface.
      claim_kind:: analyst_assessment
- ## Argument Map
    - **Problem and Stakes:** The paper targets three failures of voice assistants built as cascades, meaning separate speech recognition, text dialogue, and text-to-speech modules: accumulated response delay, loss of non-written meaning, and forced speaker turns. The stakes are not only faster interaction but a model class that can represent overlap, interruption, backchanneling, and expressive speech as first-class behavior.
      evidence:: E1, E2
    - **Prior Gap:** Prior speech-text systems either generate a full text answer before speech, rely on automatic speech recognition as a bottleneck, or model dialogue as one segmented stream. The closest full-duplex prior category, systems that can listen and speak at the same time, lacked online operation, text-language-model knowledge, or acoustic-token generation according to the paper.
      evidence:: E17
    - **Key Insight:** The core insight is to keep the language-model strengths of text while making speech the native input and output: text tokens guide Moshi's own speech, while semantic-acoustic audio tokens preserve what text would discard. Separating user and system streams turns overlap from an exception into ordinary sequence modeling.
      evidence:: E7, E8
    - **Claims:** The paper's technical argument reduces to four falsifiable claims.
      claim_kind:: analyst_assessment
        - C1: Moshi is a real-time full-duplex speech-to-speech dialogue model because it represents the user and system as separate audio streams and samples system speech while conditioning on actual user audio.
          evidence:: E1, E7
        - C2: Mimi, Moshi's neural audio codec that compresses waveforms into discrete symbols and reconstructs them, produces causal semantic-acoustic tokens suitable for low-latency audio language modeling.
          evidence:: E4, E5
        - C3: A hierarchical Residual Quantization Transformer (RQ-Transformer), a large model over time plus a smaller model over codec levels inside each frame, is needed to model many audio tokens per moment under strict latency constraints.
          evidence:: E6, E11
        - C4: Inner Monologue, the time-aligned text stream predicted before Moshi's own audio stream, improves linguistic and factual speech generation while remaining compatible with streaming automatic speech recognition and text-to-speech variants.
          evidence:: E8, E11, E12, E14
- ## Mechanism and Design
    - **Core Mechanism:** Moshi starts from Helium, a text Transformer language model, and extends it to predict audio tokens, which are discrete symbols from the Mimi codec. Mimi uses residual vector quantization, a stack of codebooks where later codebooks encode what earlier ones missed, so Moshi can generate both coarse linguistic content and fine acoustic detail.
      evidence:: E3, E4, E6
    - **Data / Control Flow:** At each time frame, previous joint tokens enter the Temporal Transformer, the component that carries long conversation context; then the Depth Transformer predicts the current frame's ordered text, semantic, and acoustic tokens. During inference, predictions for the user stream are ignored and replaced by the real encoded user audio, while Moshi's text and audio tokens are sampled.
      evidence:: E6, E7, E8
    - **Design Decisions:** The main design pattern is to move expensive temporal reasoning to a slow frame rate, then handle within-frame token dependencies locally. Each component removes one serialized bottleneck: codec causality removes offline audio features, acoustic delay reduces same-frame dependence, multi-stream modeling removes turn segmentation, and Inner Monologue removes the choice between text reasoning and speech output.
      claim_kind:: analyst_assessment
      evidence:: E4, E6, E7, E8
        - Need: one tokenizer must provide both linguistic content and reconstructable sound; choice: Mimi distills WavLM semantic information into one quantizer and uses a split residual quantizer for acoustic reconstruction; tradeoff: semantic quality and acoustic quality compete, so the split design is a compromise.
          evidence:: E4, E5
        - Need: many codec tokens per frame would be too costly as one flat sequence; choice: RQ-Transformer plus acoustic delay; tradeoff: a small amount of latency buys easier token prediction and better generated speech.
          evidence:: E6, E11
        - Need: audio-only generation struggles with long, factual, syntactically coherent speech; choice: put aligned text tokens before Moshi's own audio tokens; tradeoff: it adds one stream and marginal inference work but makes content planning explicit.
          evidence:: E8, E11, E12
    - **Implementation Surface:** The implementation surface is large: a 7B-parameter Helium backbone, a causal Mimi codec at 24kHz and 12.5 frames per second, a Depth Transformer with per-codebook parameters, and Moshi's joint sequence with 2Q+1 streams when Q=8 codec levels. Training is staged across text pretraining, single-stream audio pretraining, simulated multi-stream post-training, Fisher conversation fine-tuning, and synthetic instruction tuning.
      evidence:: E3, E4, E8, E9, E10
- ## Evaluation and Evidence
    - **Setup:** The evaluation is componentized: Helium is tested on text benchmarks, Mimi on phonetic discriminability and audio quality, the audio model on ablations and textless speech metrics, Moshi on spoken question answering and dialogue generation, plus safety, voice consistency, watermarking, and compression analyses. Baselines vary by component, which makes the evidence broad but not one unified end-to-end user study.
      claim_kind:: analyst_assessment
      evidence:: E5, E11, E12, E13, E14, E15, E16
    - **Claim-Evidence Matrix:** C2 and C4 receive the most direct evidence because the paper reports controlled ablations and clear benchmark deltas; C1 is supported by architecture and generated-dialogue behavior, but less by live human-interaction measurement. C3 is well supported inside the chosen codec and delay regime, not as a universal claim about all audio tokenizers.
      claim_kind:: analyst_assessment
      evidence:: E5, E11, E12, E13
        - C1: supported by the multi-stream architecture and generated-dialogue turn-taking metrics, but the paper does not report a controlled live-user study measuring naturalness under interruptions.
          claim_kind:: analyst_assessment
          evidence:: E7, E13
        - C2: supported by causal-codec design, ABX phonetic discriminability discussion, and human MUSHRA audio-quality results against codec baselines.
          evidence:: E4, E5
        - C3: supported by the low-delay ablation where RQ-Transformer sharply improves perplexity over independent heads, while longer-delay patterns reduce the need for the same mechanism.
          evidence:: E11
        - C4: supported by generative-model ablations, spoken question answering gains, and the streaming automatic speech recognition and text-to-speech demonstrations.
          evidence:: E11, E12, E14
    - **Headline Results:** The headline evidence is strongest when it connects mechanism to measurable behavior: Mimi improves perceived codec quality, RQ-Transformer and Inner Monologue improve generation, Moshi improves spoken question answering, and generated dialogues approach cascaded-model linguistic scores. These results are mostly benchmark and proxy based, so they establish feasibility more than final product quality.
      claim_kind:: analyst_assessment
      evidence:: E5, E11, E12, E13, E14
        - Mimi with adversarial-only training reports Multiple Stimuli with Hidden Reference and Anchor (MUSHRA) 81.0 +/- 1.3, compared with 64.8 +/- 1.5 for SemantiCodec at a higher frame rate and 45.1 +/- 1.5 for low-bitrate SpeechTokenizer.
          evidence:: E5
        - On spoken question answering, Moshi reports 26.6 on Web Questions, 62.3 on LlaMA Questions, and 22.8 on Audio Trivia QA, above SpeechGPT's 6.5, 21.6, and 14.8 on the same listed tasks.
          evidence:: E12
        - On generated Fisher continuations, Moshi at temperature 1.0 reports conditional perplexity 79.3, gap 4.5s, and overlap 4.1s, close in turn-taking shape to the reported 1000-sample ground truth gap 4.2s and overlap 3.3s.
          evidence:: E13
    - **Ablations and Sensitivity:** The ablations show that low latency is not free: reducing acoustic delay makes independent audio-token heads fail, so the RQ-Transformer becomes necessary; Inner Monologue then gives the largest jump in generated transcript quality and length. Compression results add a separate sensitivity: audio quality stays relatively robust down to 4-bit weights, but text reasoning measured by Massive Multitask Language Understanding (MMLU) drops more noticeably below 6 bits.
      evidence:: E11
        - With acoustic delay [0,2,2,2,2,2,2,2], the RQ-Transformer reduces reported perplexity from 135.4 to 36.8 relative to independent heads, while the longer Copet-style delay pattern gives only a small improvement.
          evidence:: E11
        - Adding Inner Monologue to the weighted, depthwise model lowers generated transcript negative log-likelihood from 3.65 to 2.77 and raises transcript length from 602 to 1920 characters in the paper's proxy test.
          evidence:: E11
        - Changing only the text-audio delay turns the same Inner Monologue idea into streaming text-to-speech with 4.7% Word Error Rate (WER) and streaming automatic speech recognition with 5.7% WER on LibriSpeech test-clean.
          evidence:: E14
    - **Reproducibility Gaps:** The paper states Moshi is available on GitHub, but the reproduced system depends on ingredients that are not described as a turnkey public recipe in the provided text: a 7-million-hour audio collection, staged H100 training, synthetic interaction generation, actor voice conditioning, and several evaluation scripts. Code availability helps reuse, but data, compute, and safety-evaluation coverage remain the practical blockers.
      claim_kind:: analyst_assessment
      evidence:: E1, E9, E10, E15, E16
- ## Technical Judgment
    - **What Holds Up:** The most durable part is the representation design: separate streams for participants, causal semantic-acoustic tokens, and hierarchical per-frame generation are coherent answers to the latency and turn-taking problem. The paper also earns trust by tying those choices to ablations rather than presenting one monolithic system result.
      claim_kind:: analyst_assessment
      evidence:: E4, E7, E8, E11
    - **Where It May Fail:** The weakest generalization is from benchmark feasibility to robust open-world dialogue: Moshi still trails text-only Helium on knowledge-heavy spoken QA, safety is narrower than deployment risk, signal watermarking fails after codec compression, and the data recipe is hard to audit. Benefits should diminish when conversations require exact factual recall, rare syntax, adversarial audio, or deployment constraints below the tested quantization range.
      claim_kind:: analyst_assessment
      evidence:: E12, E14, E16
    - **Relation to Other Work:** Technically, Moshi sits between speech-token language models and cascaded voice assistants: unlike Chain-of-Modality systems such as Spectron and SpeechGPT, it does not wait for a full text answer before speaking; unlike semantic-token-only systems, it models acoustic detail inside the generative model. Compared with prior full-duplex dialogue work, the distinguishing axis is online streaming plus text-model knowledge plus acoustic-token output.
      evidence:: E17, E7, E8
    - **Transferable Lesson:** For low-latency multimodal generation, avoid serializing modalities into a pipeline when the interaction itself is simultaneous. A reusable pattern is to choose a frame-level representation where slow semantic decisions can prefix fine detail inside the same streaming step, while different real-world actors remain separate state streams.
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E8
- ## Glossary
  collapsed:: true
    - speech-to-speech generation: A model consumes spoken audio and directly produces spoken audio, rather than using text as the only internal dialogue representation.
    - full-duplex dialogue: Both sides can listen and speak at the same time; the system does not require explicit speaker-turn boundaries.
    - audio token: A discrete symbol representing a short slice or level of audio after compression by a neural audio codec.
    - neural audio codec: An encoder-decoder model that maps waveforms to compact latent tokens and reconstructs waveforms from those tokens.
    - residual vector quantization: A quantization scheme with multiple codebooks; each later codebook encodes the residual error left by earlier codebooks.
    - semantic token: In this paper, the first Mimi token level is trained to carry phonetic or linguistic content, not only waveform detail.
    - acoustic token: A codec token level used mainly to reconstruct voice quality, timbre, noise, and other fine audio properties.
    - Residual Quantization Transformer: A two-level autoregressive model: the Temporal Transformer models time steps, while the Depth Transformer models token levels inside the current step.
    - Inner Monologue: Moshi's aligned text-token stream for its own speech; it is generated before the audio tokens in each frame to guide linguistic content.
    - acoustic delay: A deliberate offset that makes acoustic detail depend on earlier semantic or text decisions, reducing difficult same-frame dependencies at the cost of latency.
    - Multiple Stimuli with Hidden Reference and Anchor: A human listening test for perceived audio quality; higher scores indicate closer or better perceived quality in the tested setup.
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/paper_statement | Abstract | high
      locator:: Abstract, opening and closing claims
      quote:: We introduce Moshi, a speech-text foundation model and full-duplex spoken dialogue framework. Current systems for spoken dialogue rely on pipelines of independent components, namely voice activity detection, speech recognition, textual dialogue and text-to-speech.
    - **E2:** problem/paper_statement | 1 Introduction | high
      locator:: Introduction, limitations of current interfaces
      quote:: First, latency compounds along the many components of these pipelines, resulting in a typical global latency of several seconds. Second, as language understanding and generation happens in the textual domain, any non-written information is ignored by the model.
    - **E3:** implementation/implementation_detail | 3.2 The Helium Text Language Model | high
      locator:: Sections 3.2.1 and 4.4, Helium architecture and training
      quote:: Helium is an autoregressive language model, based on the Transformer architecture. The text-only language model, Helium, is trained for 500k steps, with a batch size of 4.2M tokens, using a cosine learning rate schedule.
    - **E4:** method/implementation_detail | 3.3 Audio Tokenization | high
      locator:: Sections 3.3.1 and 3.3.2, Mimi codec
      quote:: Mimi uses distillation to transfer non-causal, high-level semantic information into the tokens produced by a causal model, allowing for streaming encoding and decoding of semantic-acoustic tokens. With Q = 8 quantizers, each with a codebook size of 2048.
    - **E5:** result/experiment_result | 5.2 Audio Tokenization | high
      locator:: Table 4 and Results - Acoustic tokens
      quote:: This human evaluation shows a significant improvement from using adversarial losses only, with a MUSHRA score of 81.0 against 58.8 when using the mix of loss functions used in Encodec.
    - **E6:** algorithm/implementation_detail | 3.4.1 Hierarchical Autoregressive Modeling with RQ-Transformer | high
      locator:: Section 3.4.1, RQ-Transformer definition
      quote:: The RQ-Transformer consists in two Transformer models, as illustrated in Figure 3. It consists of a Temporal Transformer, e.g. with the same architecture as the one described for Helium, and a smaller Depth Transformer.
    - **E7:** system_design/implementation_detail | 3.4.3 Multi-stream Modeling | high
      locator:: Sections 3.4.3 and Inference of Moshi
      quote:: Modeling a single stream of audio is not sufficient to fully model a conversation. Our framework can be extended to modeling a two-speaker conversation: given two streams of audios, we simply apply the acoustic delay to both, and concatenate them into V.
    - **E8:** method/implementation_detail | 3.4.4 Inner Monologue | high
      locator:: Section 3.4.4, text stream and delay
      quote:: We insert W as the first sub-sequence in V, such that it acts as a prefix to the generation of semantic tokens. This can be seen as an extension of the hierarchical semantic-to-acoustic generation introduced by Borsos et al.
    - **E9:** experiment_setup/paper_statement | 4 Datasets and Training | medium
      locator:: Sections 4.2 and 4.3, audio and instruction data
      quote:: We use an audio collection of 7 million hours, which we call the unsupervised audio dataset, of readily available audio content, the majority of which contains English speech. We transcribe this set with Whisper.
    - **E10:** experiment_setup/implementation_detail | 4.4 Training Stages and Hyper-parameters | high
      locator:: Section 4.4, staged Moshi training
      quote:: Then, we initialize the Temporal Transformer in Moshi with Helium, while the Depth Transformer described in Section 3.4.1 is randomly initialized. We first train on the unsupervised audio dataset presented in Section 4.2.
    - **E11:** ablation/ablation | 5.3 Ablations on Generative Modeling | medium
      locator:: Tables 5 and 6, RQ-Transformer and Inner Monologue ablations
      quote:: In that context, modeling RVQ tokens with an RQ-Transformer significantly improves perplexity over using separate classification heads. Thus, the RQ-Transformer becomes a critical component of generative models of RVQ tokens under strict latency constraints.
    - **E12:** result/experiment_result | 5.5 Spoken Question Answering | medium
      locator:: Table 8 and Results
      quote:: Table 8 reports accuracies on the three benchmarks. While audio-only Moshi significantly outperforms baselines in its categories, the most striking result is the impact of Inner Monologue on Moshi's performance, almost tripling its accuracy on all benchmarks.
    - **E13:** result/experiment_result | 5.6 Dialogue Evaluation | medium
      locator:: Table 9 and Results
      quote:: Table 9 shows that Moshi performs as well as the cascaded model in terms of linguistic quality, despite being an audio-to-audio model. Both have a perplexity that is better than the ground truth.
    - **E14:** result/experiment_result | 5.7 Streaming ASR and TTS | medium
      locator:: Section 5.7, LibriSpeech results
      quote:: Our streaming TTS model obtains 4.7% of WER on LibriSpeech test-clean, which outperforms Vall-E's 5.9% WER but is worse than NaturalSpeech 3 with 1.81%. Our ASR system yields 5.7% WER.
    - **E15:** result/experiment_result | 6.3 System Voice Consistency | high
      locator:: Section 6.3 and Table 14
      quote:: Over the generated datasets, there are 10 249 occurrences (98.7%) where the voice of the main speaker is closer to the reference segment of the main speaker and 133 occurrences (1.3%) where the voice is closer to the reference segment of the other speaker.
    - **E16:** limitation/limitation | 6.4 Identification of the Content Generated by Moshi | high
      locator:: Table 15 and watermarking discussion
      quote:: As a result, our Mimi codec removes the mark to a level that makes a watermarked audio indistinguishable from a non-watermarked audio, making such a signal-based watermarking useless in this context.
    - **E17:** prior_work/paper_statement | 2 Related Work | high
      locator:: Related Work, Spoken Dialogue Models
      quote:: While Spectron benefits from its underlying text LLM, it is not compatible with real-time generation due to Chain-of-Modality. PSLM proposes generating speech and text tokens in parallel to reduce this latency, however it reduces the quality of answers.
