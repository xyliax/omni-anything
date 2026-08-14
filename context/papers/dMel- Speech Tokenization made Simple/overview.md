- **Title:** dMel: Speech Tokenization made Simple
- **Summary:** dMel shows that directly binning log-mel spectrogram energies can serve as a simple, training-free speech tokenization interface for decoder-only ASR and TTS, reducing dependence on learned speech codecs and task-specific token stacks.
- **Paper Type:** system
- **Venue:** arXiv preprint 2024, v3 May 2025
- **Authors:** Richard He Bai, Zijin Gu, Tatiana Likhomanenko, Zakaria Aldeneh, Ruixiang Zhang, Navdeep Jaitly; Apple
- **Keywords:** speech tokenization, log-mel spectrogram, text-to-speech, automatic speech recognition, decoder-only transformer, speech-text modeling
- ## Orientation
    - **Background:** Speech systems often convert sound into a compact sequence before a model can process it. A log-mel spectrogram is a time-by-frequency picture of speech energy, and a speech token is a discrete symbol intended to make that picture usable by language-model-style predictors.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** If we want one model to both listen and speak, we need a representation that keeps the words, the speaker, and the sound quality without requiring a fragile extra model just to make the tokens.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** Representations that keep meaning often drop acoustic detail, while representations that reconstruct sound well can be awkward for simple next-token modeling.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Instead of learning a speech code, round each log-mel energy value into a small ordered bin and model those rounded spectrogram frames directly.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a speech-tokenization paper that challenges the assumption that language-model-style speech systems need learned semantic or neural-codec tokens before modeling speech.
      claim_kind:: analyst_assessment
      evidence:: E1, E2
    - **One-Sentence Contribution:** dMel improves language-model-style speech recognition and synthesis by replacing learned speech tokenizers with a direct discretization of log-mel spectrogram energy values.
      evidence:: E1, E2
    - **Mental Model:** Treat speech like a heat map over time and pitch: dMel rounds each cell's brightness to a small set of levels, then asks a text-like next-token model to predict future heat-map columns.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is the controlled comparison where the same decoder-only model is trained with different speech tokenizers, and dMel wins for both TTS intelligibility and ASR WER.
      evidence:: E7, E9
        - Supports C2: RichTTS Base on LibriSpeech 960h; HuBERT+KM and SpeechTokenizer inside the same LM-style model plus prior VOX-TLM/USLM; WER/CER lower is better; dMel reports 4.3 WER and 1.8 CER versus 9.5/4.3 for HuBERT+KM and 11.4/5.9 for SpeechTokenizer; supported, with automatic ASR evaluation caveat.
          evidence:: E7
        - Supports C3: RichASR Base on LibriSpeech 960h; same 258M architecture with SpeechTokenizer and HuBERT+KM; WER lower is better; dMel reports 4.2 test-clean and 10.4 test-other versus 5.8/13.8 for HuBERT+KM and 6.9/17.5 for SpeechTokenizer; supported with two-run standard deviations.
          evidence:: E9
        - Supports C1: reconstruction on 300 LibriSpeech test-clean samples; neural tokenizers and mel-vocoder baselines; WER/MOS-LQO/MOS; dMel-HifiGAN is close to Mel-HifiGAN and competitive with acoustic codecs while needing no speech-to-unit encoder; supported, but sample size is small.
          evidence:: E5
    - **Main Caveat:** The paper demonstrates ASR and TTS on mostly English speech benchmarks, but does not establish general audio modeling, complex speech understanding, or large-scale pretrained multimodal LLM behavior.
      claim_kind:: analyst_assessment
      evidence:: E14
- ## Argument Map
    - **Problem and Stakes:** The paper targets speech tokenization for language-model-style automatic speech recognition (ASR, speech-to-text) and text-to-speech (TTS, text-to-speech) systems: learned tokenizers add complexity, cost, and domain sensitivity, while unified speech-text modeling needs tokens that preserve both content and acoustics.
      evidence:: E1, E2
    - **Prior Gap:** Prior speech tokenizers split into semantic tokens from self-supervised speech encoders, which preserve content but lose acoustic details, and acoustic tokens from neural audio compression, which reconstruct sound but often require residual vector quantization (RVQ, a stack of codebooks that encode successive reconstruction errors) and specialized hierarchical models.
      evidence:: E2
    - **Key Insight:** The paper's central bet is that a log-mel spectrogram already contains enough content and acoustic information, so scalar quantization (rounding each continuous value to the nearest discrete bin) can make it token-like without training a tokenizer.
      evidence:: E1, E3
    - **Claims:** The paper makes four falsifiable claims about dMel as a tokenizer and as an interface to decoder-only models.
      evidence:: E5, E7, E9, E12
        - C1: Discretizing log-mel spectrograms into dMel preserves enough acoustic information for waveform reconstruction and is more robust to noisy out-of-domain reconstruction than several learned tokenizers.
          evidence:: E5, E6
        - C2: In a language-model-style TTS setting, dMel enables more intelligible generated speech than HuBERT-KM or SpeechTokenizer under the paper's comparable decoder-only training setup.
          evidence:: E7, E8
        - C3: In a language-model-style ASR setting, dMel preserves semantic content better than the compared speech tokenizers, as measured by WER in the same architecture.
          evidence:: E9, E10
        - C4: dMel's per-channel independence lets the model predict multiple channels and nearby frames in parallel, improving efficiency without the same residual-code dependency problem as RVQ tokenizers.
          evidence:: E4, E12
- ## Mechanism and Design
    - **Core Mechanism:** dMel computes a log-mel spectrogram, builds a shared scalar codebook from dataset-wide minimum and maximum energy values, and replaces each time-frequency cell with the nearest bin index; detokenization maps indices back through the codebook and uses a separately trained mel vocoder (a model that converts mel spectrograms into waveforms).
      evidence:: E3, E4
    - **Data / Control Flow:** For speech input, each frame contains many frequency-channel bin IDs; each bin is embedded, the channel embeddings are concatenated and linearly projected to the transformer's hidden dimension, and the decoder-only transformer predicts future text tokens for ASR or future dMel speech tokens for TTS.
      evidence:: E4
        - For TTS, the input sequence concatenates a speaker embedding, character-level text tokens, and speech tokens, and the loss is applied to the speech-token outputs rather than the text prefix.
          evidence:: E13
        - For ASR, the input sequence concatenates speech tokens and character-level text tokens, and the loss is applied to the text-token outputs rather than the speech prefix.
          evidence:: E13
    - **Design Decisions:** The design repeatedly chooses simple, shared, and parallelizable representations over learned compression structure, accepting higher bitrate in exchange for tokenizer simplicity and easier decoder-only modeling.
      claim_kind:: analyst_assessment
      evidence:: E4, E11, E12
        - Need: make continuous mel values discrete; choice: 16 shared ordinal bins across 80 channels; alternative: larger or smaller codebooks; tradeoff: 8 bins lose too much information, while 32 bins can help some ASR cases but hurts TTS in the paper's setting.
          evidence:: E4, E11
        - Need: avoid sequential dependence across residual code channels; choice: predict dMel frequency channels independently and in parallel; alternative: RVQ-style residual channels; tradeoff: dMel has more raw bits but avoids residual hierarchy in the downstream model.
          evidence:: E4, E12
        - Need: reduce copying of locally redundant audio frames and exposure bias; choice: span-mask speech context during training; tradeoff: this adds a training heuristic whose benefit is empirically reported but not theoretically analyzed.
          evidence:: E13
    - **Implementation Surface:** The implementation surface includes a deterministic tokenizer, a mel vocoder outside the transformer, character text tokens, d-vector speaker embeddings for TTS, RoPE relative position encoding, and Small/Base/Large decoder-only transformer configurations.
      evidence:: E4, E13
        - Reported training uses Adam, mixed precision BF16, A100/H100 80GB GPUs, 8 GPUs, 80k ASR steps, 100k TTS steps, and less than a day for ASR versus 2-4 days for TTS.
          evidence:: E13
- ## Evaluation and Evidence
    - **Setup:** The evaluation combines reconstruction tests, decoder-only TTS, decoder-only ASR, ablations, and a preliminary joint ASR+TTS model, mostly on LibriSpeech with additional TTS datasets LibriTTS, VCTK, and LJSpeech; metrics include word error rate (WER, lower is better), character error rate (CER), objective MOS-LQO, and human mean opinion score (MOS).
      evidence:: E5, E7, E9, E13
    - **Claim-Evidence Matrix:** The evidence is strongest where tokenizer is varied under a shared model architecture, and weaker where comparisons cross different model families, datasets, or evaluation protocols.
      claim_kind:: analyst_assessment
      evidence:: E5, E7, E9, E10
        - C1 is supported by reconstruction WER/MOS-LQO/MOS on clean LibriSpeech and a noisy reconstruction stress test, but the clean reconstruction sample is only 300 utterances and noisy results rely on automatic ASR WER.
          claim_kind:: analyst_assessment
          evidence:: E5, E6
        - C2 and C3 are supported by same-architecture comparisons against HuBERT-KM and SpeechTokenizer; external comparisons to VOX-TLM, USLM, Tacotron2, FastSpeech2, and VITS are useful context but less controlled.
          claim_kind:: analyst_assessment
          evidence:: E7, E8, E9, E10
        - C4 is supported by k-frame ablations that trade theoretical FLOPs for WER, but the paper reports theoretical inference time rather than full wall-clock serving measurements.
          claim_kind:: analyst_assessment
          evidence:: E12
    - **Headline Results:** The headline results are that dMel closely preserves reconstruction quality, substantially improves TTS intelligibility over the tested tokenizers in the same LM-style model, and improves ASR WER over HuBERT-KM and SpeechTokenizer in the same Base architecture.
      evidence:: E5, E7, E9
        - C1: on 300 LibriSpeech test-clean samples, dMel-HifiGAN reports WER 2.11 and MOS-LQO 4.47 versus Mel-HifiGAN WER 2.08 and MOS-LQO 4.52, indicating small discretization loss under this vocoder.
          evidence:: E5
        - C2: RichTTS(dMel) trained on LibriSpeech 960h reports WER 4.3 and CER 1.8, while RichTTS(HuBERT+KM) reports 9.5/4.3 and RichTTS(SpeechTokenizer) reports 11.4/5.9.
          evidence:: E7
        - C3: RichASR(dMel) Base reports test-clean/test-other WER 4.2 ±0.2 and 10.4 ±0.1 versus HuBERT+KM 5.8 ±0.1 and 13.8 ±0.1 and SpeechTokenizer 6.9 ±0.4 and 17.5 ±0.5.
          evidence:: E9
    - **Ablations and Sensitivity:** Ablations identify the bin count, frame aggregation, ASR architecture choice, and augmentation/masking choices as important sensitivity axes rather than treating dMel as a universally sufficient drop-in.
      evidence:: E11, E12, E13
        - The paper selects 16 bins as the overall best tradeoff; 8 bins lose too much information, while 32 bins are mixed, slightly helping ASR test-other but degrading TTS.
          evidence:: E11
        - k-frame parallel decoding works best up to moderate aggregation: the paper reports similar results for k ≤ 4 with improved theoretical efficiency, while very aggressive aggregation increases WER.
          evidence:: E12
        - The ASR ablation argues that discretization itself causes only small degradation relative to continuous mel features, while much of the remaining gap comes from switching to an LM-style decoder-only ASR model.
          evidence:: E10
    - **Reproducibility Gaps:** The paper reports a public code URL and detailed training settings, but states that pretrained models will not be released and that code release was planned upon acceptance; absence of released checkpoints limits exact reproduction and reuse.
      evidence:: E13, E14
- ## Technical Judgment
    - **What Holds Up:** The central technical point holds up: if the task is ASR/TTS over speech, direct scalar-quantized mel features are a surprisingly strong baseline and remove a large learned-tokenizer dependency that prior systems often treat as necessary.
      claim_kind:: analyst_assessment
      evidence:: E3, E5, E7, E9
    - **Where It May Fail:** Benefits may diminish when the target is compact audio compression, non-speech audio, complex speech understanding, highly multilingual or adverse-domain pretraining, or production TTS quality that requires prosody and style control beyond intelligibility and naturalness scores reported here.
      claim_kind:: analyst_assessment
      evidence:: E14
    - **Relation to Other Work:** Compared with HuBERT-KM semantic tokens, dMel keeps more acoustic detail; compared with EnCodec/SpeechTokenizer-style neural codecs, it avoids RVQ residual structure and tokenizer training; compared with AudioLM/VOX-TLM/VioLA-style unified modeling, it pushes complexity out of tokenization rather than adding stages or modality-specific hierarchy.
      claim_kind:: analyst_assessment
      evidence:: E2, E4, E10
    - **Transferable Lesson:** Before designing a learned discrete representation, test whether a physics-grounded continuous representation plus simple scalar quantization preserves the task-relevant information; the simpler token boundary can make downstream modeling and failure analysis easier even if it is not bitrate-optimal.
      claim_kind:: analyst_assessment
- ## Glossary
  collapsed:: true
    - log-mel spectrogram: A time-by-frequency representation of audio energy where frequency bands follow a perceptual mel scale and amplitudes are log-transformed; it is the continuous representation dMel discretizes.
    - speech tokenization: The conversion of a continuous speech waveform or spectrogram into discrete symbols that can be modeled like text tokens.
    - dMel: The paper's tokenizer: each log-mel spectrogram cell is rounded to one of a small number of shared intensity bins, producing a matrix of discrete time-frequency token IDs.
    - vocoder: A model that converts acoustic features such as mel spectrograms back into waveform audio; in this paper it is trained independently and sits outside the transformer.
    - semantic token: A discrete speech unit usually obtained by clustering hidden states from a self-supervised speech model; it tends to preserve linguistic content better than fine acoustic detail.
    - acoustic token: A discrete token produced by an audio compression model, intended to preserve enough low-level acoustic information to reconstruct the waveform.
    - residual vector quantization: A multi-codebook quantization method where each later codebook encodes the reconstruction error left by earlier codebooks; common in neural audio codecs but creates ordered residual channels.
    - decoder-only transformer: A transformer architecture that predicts the next token from previous tokens using causal masking, similar to GPT-style language models.
    - ASR and TTS: ASR maps speech to text; TTS maps text to speech. The paper uses both tasks to test whether dMel preserves semantic content and acoustic reconstructability.
    - WER, CER, and MOS: WER and CER measure transcription errors and are lower-is-better; MOS is a human naturalness score and MOS-LQO is an objective listening-quality estimate, both higher-is-better.
- ## Evidence Index
  collapsed:: true
    - **E1:** method/paper_statement | Abstract | medium
      locator:: Abstract
      quote:: we introduce a novel speech representation (dMel) that discretizes mel-filterbank channels into intensity bins, creating a simpler yet more effective representation compared to existing speech tokenization methods.
    - **E2:** insight/paper_statement | Introduction | medium
      locator:: Section 1, motivation and advantages
      quote:: By operating on the log mel-filterbanks and preserving the frequency and intensity information (with some loss of resolution from discretization), dMel inherently preserves both semantic and acoustic information in a unified representation, without the need for separate tokenization or additional pretraining of a tokenization model.
    - **E3:** algorithm/implementation_detail | Method | high
      locator:: Section 2.1, Tokenization
      quote:: In practice, we compute the minimum m and maximum M values of log mel-filterbanks across the entire dataset to define the codebook C. Then we map a magnitude M_t,i of every frequency channel i = 1 ... N for the time frame t = 1 ... T into a bin index of the codebook C
    - **E4:** system_design/paper_statement | Method | high
      locator:: Table 2 and Section 2.1 comparison
      quote:: For dMel we use N = 80 log-mel-filterbanks (50ms window, 25ms hop distance), and 2^K = 16 values of the codebook C... dMel has a much smaller vocabulary, as it is discretized mel-filterbanks energies, allowing all 80 channels to share the same vocabulary
    - **E5:** result/experiment_result | Experiments | medium
      locator:: Table 3 and Section 3.1
      quote:: Speech reconstruction results on 300 random samples from LibriSpeech test-clean set... dMel-HifiGAN ... WER 2.11 ... MOS-LQO 4.47 ... MOS 3.68 ±0.13... By comparing Mel and dMel, we can see that discretization has little impact on WER and MOS-LQO scores.
    - **E6:** result/experiment_result | Experiments | medium
      locator:: Figure 4 and Section 3.2
      quote:: Results are shown in Figure 4: both HuBERT-KM and SpeechTokenizer fail in out-of-domain setting while EnCodec, Mel and dMel show robustness for noisy speech reconstruction. This supports our motivation to explore dMel, training-free and deterministic tokenization
    - **E7:** result/experiment_result | Experiments | medium
      locator:: Table 4 and Section 3.3.2
      quote:: our LM-style model with dMel tokenization achieves a WER of 4.3 and a CER of 1.8, significantly outperforming the baseline methods. This indicates that our model can generate more accurate speech with less hallucination and distortion.
    - **E8:** result/experiment_result | Experiments | medium
      locator:: Table 5, Table 6, Section 3.3.2
      quote:: RichTTS achieves competitive performance on the TTS task in terms of both MOS and WER... Table 6 shows the WER results... our model achieves competitive performance across different text lengths, demonstrating its robustness and generalization ability
    - **E9:** result/experiment_result | Experiments | medium
      locator:: Table 7 and Section 3.4
      quote:: Our LM-style model with dMel speech tokenization achieves 4.2% WER on the test-clean and 10.4% WER on the test-other sets outperforming both HuBERT-KM and SpeechTokenizer.
    - **E10:** result/experiment_result | Experiments | medium
      locator:: Table 8 and Section 3.4
      quote:: RichASR with dMel outperforms VOX-TLM; it also outperforms [11] on clean sets and a bit behind it on other sets.
    - **E11:** ablation/ablation | Ablations | medium
      locator:: Section 3.5 and Figure 5
      quote:: The 16-bin configuration used in the paper demonstrates the best overall performance across tasks. While the 32-bin setup slightly outperforms on the ASR test-other set, it shows degraded performance in TTS... And 8-bin configuration looses too much information with discretization.
    - **E12:** ablation/ablation | Ablations | medium
      locator:: Section 3.5 and Figure 6
      quote:: As we can see from this figure, k ≤ 4 yield similar results to single-frame model, while improves both the training and inference efficiency significantly. In contrast, for SpeechTokenizer, even K = 1 is worse than dMel with k = 6.
    - **E13:** experiment_setup/implementation_detail | Appendix E | high
      locator:: Appendix E.2, Training Details
      quote:: We train TTS models for 100k steps and ASR models 80k steps with mixed precision training and BF16 on A100 and H100 GPUs with 80GB. Both ASR models and TTS models are trained with 8GPUs
    - **E14:** limitation/limitation | Limitations and Reproducibility | high
      locator:: Appendix B and C
      quote:: we did not train on larger model sizes (>1B parameters), larger datasets (>1k hours), or using pretrained models... While dMel may potentially support non-speech tasks, our current exploration and verification focus solely on speech, not general audio... We do not plan to open-source any pre-trained models
