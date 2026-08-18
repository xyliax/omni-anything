- **Title:** Live CC: Learning Video LLM with Streaming Speech Transcription at Scale
- **Summary:** LiveCC shows that timestamp-aligned automatic speech recognition captions can cheaply train a streaming video large language model to comment frame by frame while improving several video question-answering benchmarks.
- **Paper Type:** system
- **Venue:** arXiv preprint 2025
- **Authors:** Joya Chen, Ziyun Zeng, Yiqi Lin, and Mike Zheng Shou (Show Lab, National University of Singapore); Wei Li and Zejun Ma (ByteDance)
- **Keywords:** video large language model, streaming video understanding, automatic speech recognition, closed captions, real-time commentary, video question answering
- ## Orientation
    - **Background:** Many video assistants learn by looking at finished clips and then writing an answer. Live use is different: the model sees the scene unfold and must speak while new frames are still arriving.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A live commentator cannot wait for the whole video. It must say useful words now, using only what has happened so far and the speech-like context already produced.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** Natural speech is messy, partial, and unevenly timed, while video events change continuously. Cheap captions are abundant but noisy, so the model must learn alignment without carefully written labels.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Train on the web's existing spoken captions by matching small bursts of words to the frames that occurred at the same time.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a streaming video-language modeling paper: it asks whether cheap automatic speech recognition (ASR), text automatically transcribed from video audio or captions, can replace expensive human or GPT-style training data for live commentary.
      claim_kind:: analyst_assessment
      evidence:: E2
    - **One-Sentence Contribution:** LiveCC improves live video commentary by training a video large language model (Video LLM), a language model conditioned on video frames, to predict the caption words aligned with each incoming frame instead of waiting to caption the whole clip.
      evidence:: E3, E6
    - **Mental Model:** Picture a sports announcer reading a ticker that reveals only the current moment: after each glimpse of the field, the announcer says the next few words and carries the previous words forward.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest support is that streaming-style pre-training raises commentary win rate over caption-style training, and the final small model beats several larger baselines on commentary while staying competitive on question answering.
      evidence:: E12, E15, E16
        - Supports C1: 5M pre-training clips; caption-style ASR baseline; LiveSports-3K-CC win rate; 32.9 versus 14.0; supported, with no variance reported.
          evidence:: E12
        - Supports C3: LiveCC-7B-Instruct; Qwen2-VL-7B-Instruct and LLaVA-Video-7B baselines; VideoMME without subtitles and OVOBench average; 64.1 versus 63.3 and 59.8 versus 52.9; supported, without uncertainty estimates.
          evidence:: E15
        - Supports C4: LiveCC-7B-Instruct; LLaVA-Video-72B closest open commentary baseline; LiveSports-3K-CC win rate; 41.5 versus 35.0; supported, but judge-based.
          evidence:: E16
    - **Main Caveat:** The main trust boundary is that free-form commentary is judged by GPT-4o against ASR-derived ground truth, so the strongest result mixes visual correctness, human-commentary style, and judge preference.
      claim_kind:: analyst_assessment
      evidence:: E10, E16
- ## Argument Map
    - **Problem and Stakes:** Training real-time video large language models (Video LLMs), language models that condition on video frames, with human or LLM-written streaming conversations is expensive and small-scale. Treating automatic speech recognition (ASR), machine speech-to-text from video audio or captions, as one global caption wastes the timing signal needed for live assistants.
      evidence:: E2
    - **Prior Gap:** Prior video-ASR learning usually predicted paragraph-level or clip-level captions, while streaming Video LLM work often depended on manually crafted or GPT-crafted data. The missing piece was a scalable way to use word timestamps as supervision for causal video-language learning, where the model only uses past and current input.
      evidence:: E2, E3
    - **Key Insight:** If ASR words are aligned to the frame intervals in which they were spoken, next-word prediction becomes a stream-local supervision signal rather than a clip-level captioning task. This turns cheap captions into training data for frame-by-frame commentary.
      evidence:: E3, E6
    - **Claims:** The paper's main claims are falsifiable through sequence-style ablations, data-scaling ablations, benchmark construction, and cross-model evaluation.
      claim_kind:: analyst_assessment
        - C1: Dense interleaving of frame tokens and timestamped ASR words improves streaming commentary over caption-style video-ASR pre-training while preserving short-video question-answering (QA) performance.
          evidence:: E3, E12
        - C2: Scaling curated YouTube closed-caption pre-training improves commentary quality, but the paper observes QA decline beyond the chosen scale because the data source is narrow.
          evidence:: E5, E13
        - C3: Adding high-quality WhisperX speech-transcriber data for supervised fine-tuning (SFT), the step that adapts a base model to instructions, and general video QA data improves commentary formatting while producing competitive 7B-level general video QA.
          evidence:: E14, E15
        - C4: LiveSports-3K provides a benchmark for visually grounded sports commentary and event QA, separating free-form commentary quality from Who, When, and What multiple-choice behavior.
          evidence:: E9, E10, E16
- ## Mechanism and Design
    - **Core Mechanism:** LiveCC represents each stream interval as visual tokens, compact frame representations consumed by the language model, followed by the ASR words assigned to that interval. The model predicts only text tokens, so frame information is conditioning input and the word sequence becomes the supervised target.
      evidence:: E3, E6, E7
    - **Data / Control Flow:** The system collects YouTube videos with closed captions (CC), filters for English and visually useful speech, converts caption chunks into word timestamps, trains Qwen2-VL-7B-Base on interleaved streams, then fine-tunes with cleaner WhisperX transcripts plus general video QA.
      evidence:: E4, E5, E11
        - Pre-training data aggregates HD-VILA, YT-Temporal-1B, VidChapters, and HowTo100M, filters to 10.7M candidate IDs and then 5.7M English-captioned videos, and segments them into Live-CC-5M clips.
          evidence:: E5
        - SFT data keeps selected YouTube categories, reruns WhisperX large-v3-turbo for word-level timestamps, removes active-speaker talking-head clips, and asks GPT-4o to generate prompts that match the transcript style without revealing content.
          evidence:: E4, E7
        - At inference, LiveCC processes frames sequentially, stores Key-Value (KV) cache entries, the transformer attention state reused from previous tokens, and periodically drops old visual tokens while keeping text context.
          evidence:: E8
    - **Design Decisions:** The major design choices all reduce ambiguity in cheap, messy ASR supervision: align words locally to frames, provide context when a clip starts mid-sentence, mark silence explicitly, and filter speech that is not visually grounded.
      evidence:: E4, E6, E7, E13
        - Need: teach live speech instead of offline captioning; choice: densely interleave frames and words; closest reported alternative: concatenate all ASR after frames; tradeoff: stronger commentary but still bounded by noisy timestamps.
          evidence:: E3, E12
        - Need: clips may begin mid-thought and include pauses; choice: use title or previous ASR as context and an ellipsis as an end-of-sequence (EOS) marker for silent frames; tradeoff: context helps commentary but title context can hurt QA.
          evidence:: E7, E13
        - Need: captions are useful only when speech follows visible events; choice: language, text-loss, speech-rate, and active speaker detection (ASD), a filter for people speaking on camera; tradeoff: cheaper scale but restricted to English and selected visual speech patterns.
          evidence:: E4, E5
    - **Implementation Surface:** The implementation is a direct adaptation of Qwen2-VL-7B-Base using PyTorch and Transformers, with larger frame and context limits for formal training than ablations. The paper reports batch size, GPU count, learning rates, inference cache policy, and latency comparisons.
      evidence:: E8, E11, E17
        - Pre-training ablations reduce the frame limit to 120 and visual context to 16K tokens for efficiency, so medium and long VideoMME results are intentionally not emphasized there.
          evidence:: E11, E12
        - Formal pre-training and SFT use a 480-frame limit and 24K visual context, with 30 to 240 second Live-CC-5M clips and Live-WhisperX-526K plus LLaVA-Video-178K for SFT.
          evidence:: E11
        - The reported streaming latency is 0.17 seconds for LiveCC-7B-Instruct with frame input, compared with 5.62 and 20.51 seconds for LLaVA-Video clip-captioning baselines.
          evidence:: E17
- ## Evaluation and Evidence
    - **Setup:** General QA is evaluated on VideoMME, MVBench, OVOBench, and LiveSports-3K-QA using multiple-choice logits. Commentary is evaluated as conditioned caption completion with video title and previous ASR, then pairwise judged by GPT-4o against ASR ground truth.
      evidence:: E10, E11
    - **Claim-Evidence Matrix:** The evidence is strongest where the paper gives controlled ablations, and weaker where results rely on open-ended judge preference without confidence intervals.
      claim_kind:: analyst_assessment
      evidence:: E10, E12, E13
        - C1 is supported by a direct caption-versus-streaming ablation with nearly identical VideoMME overall scores and a large commentary win-rate difference.
          evidence:: E12
        - C2 is supported by a data-scale ablation where commentary improves monotonically from 1M to 10M clips while VideoMME peaks near 5M.
          evidence:: E13
        - C3 and C4 are supported by SFT initialization ablations and LiveSports-3K model comparisons, but the commentary side remains tied to GPT-4o judging and ASR-style ground truth.
          evidence:: E14, E16
    - **Headline Results:** The headline result is not just better commentary: LiveCC-7B-Instruct reports better VideoMME and OVOBench scores than its Qwen2-VL-7B-Instruct starting family while also beating larger open commentary models on LiveSports-3K-CC. The strongest latency claim is that frame-wise streaming lowers response delay relative to clip-captioning models.
      evidence:: E15, E16, E17
        - General QA: LiveCC-7B-Instruct scores 64.1 on VideoMME without subtitles and 59.8 on OVOBench average, above Qwen2-VL-7B-Instruct on both reported comparisons.
          evidence:: E15
        - Commentary: LiveCC-7B-Instruct reaches 41.5 LiveSports-3K-CC win rate, above LLaVA-Video-72B at 35.0 and Qwen2.5-VL-72B-Instruct at 30.4.
          evidence:: E16
        - Latency: LiveCC-7B-Instruct reports 0.17 seconds response latency with frame input, versus LLaVA-Video-7B at 5.62 seconds and LLaVA-Video-72B at 20.51 seconds with clip input.
          evidence:: E17
    - **Ablations and Sensitivity:** The ablations isolate three sensitive factors: sequence format, context source, and data scale. The most important pattern is that commentary needs streaming supervision and previous-ASR context more than it needs ordinary caption-style training.
      evidence:: E12, E13, E14
        - Sequence format: streaming pre-training gives 32.9 commentary win rate versus 14.0 for caption-style training, while VideoMME overall stays about 61.
          evidence:: E12
        - Context: previous ASR gives 32.0 commentary win rate versus 14.7 with no context, while title-only context improves commentary but weakens VideoMME relative to previous ASR.
          evidence:: E13
        - Data and SFT: commentary improves as pre-training grows to 10M clips, but general QA drops past 5M, and adding Live-WhisperX-526K during SFT roughly doubles the base SFT commentary win rate.
          evidence:: E13, E14
    - **Reproducibility Gaps:** Reported reuse signals include a project page, dataset and model names, main hardware scale, batch size, learning rates, and judge prompt details. Not reported in the paper text are random seeds, training wall-clock, confidence intervals or repeat counts for win rates, and a full audit of GPT-4o judge reliability beyond position swapping.
      claim_kind:: analyst_assessment
      evidence:: E1, E10, E11
- ## Technical Judgment
    - **What Holds Up:** The core mechanism is well matched to the goal: frame-local word prediction is exactly the training signal needed for low-delay commentary, and the caption-versus-streaming ablation directly tests that choice. The paper also shows that the approach does not merely overfit a new benchmark, because it improves or stays competitive on several external QA benchmarks.
      claim_kind:: analyst_assessment
      evidence:: E3, E12, E15, E17
    - **Where It May Fail:** Benefits are most plausible when spoken captions are visually grounded, English, and temporally aligned; talking-head, off-screen narration, noisy captions, or domains without useful speech break the supervision assumption. Commentary quality may also be overestimated when the judge rewards ASR-like style rather than independently verified visual correctness.
      claim_kind:: analyst_assessment
      evidence:: E4, E5, E10, E13
    - **Relation to Other Work:** Against Vid2Seq-style video-ASR pre-training, the technical shift is from predicting a timestamped paragraph for an event to predicting short incomplete word bursts causally after frame intervals. Against streaming Video LLM systems trained from manual or GPT-crafted conversations, LiveCC trades annotation richness for web-scale weak supervision and a commentary-specific benchmark.
      evidence:: E2, E3
    - **Transferable Lesson:** A reusable systems pattern is to preserve the natural timing of weak labels instead of collapsing them into global labels: the timestamp can be as important as the text content when the deployment interface is streaming. This suggests looking for cheap, naturally aligned supervision before paying for synthetic instruction data.
      claim_kind:: analyst_assessment
      evidence:: E2, E3, E6
- ## Glossary
  collapsed:: true
    - Video large language model: A language model that answers or generates text while conditioning on video frames; in this note it is the model family LiveCC belongs to.
    - Automatic speech recognition: Machine-produced or platform-provided speech-to-text from video audio; LiveCC uses it as cheap supervision.
    - Streaming video understanding: A setting where the model must respond as frames arrive, without seeing the full future clip.
    - Dense interleaving sequence: The LiveCC training format that alternates frame tokens and the ASR words assigned to the same time interval.
    - Visual tokens: Compact frame representations produced by the vision encoder and consumed by the language model as conditioning input.
    - Supervised fine-tuning: The post-pretraining stage that adapts the base model with curated prompt-response or task data.
    - Key-Value cache: Saved transformer attention state from previous tokens; reusing it avoids recomputing the entire history during streaming decoding.
    - LLM-as-a-judge: An evaluation method where a language model compares two generated commentaries against a reference and chooses the better one.
    - Active speaker detection: A video analysis filter that detects people speaking on camera; LiveCC uses it to remove talking-head clips that are weakly visually grounded.
    - End-of-sequence indicator: A token that marks no more words for a frame interval; LiveCC uses an ellipsis for silent frames and pauses.
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/metadata | Title and Abstract | high
      locator:: title block, abstract
      quote:: Live CC: Learning Video LLM with Streaming Speech Transcription at Scale. Joya Chen, Ziyun Zeng, Yiqi Lin, Wei Li, Zejun Ma, Mike Zheng Shou. All resources of this paper have been released at showlab.github.io/livecc.
    - **E2:** gap/paper_statement | Introduction and Related Work | high
      locator:: Section 1; Section 2 Training Video LLMs
      quote:: Previous studies on streaming video LLMs either rely on LLMs to generate hallucinated streaming conversations from video annotations, or fine-tune on small-scale dense caption datasets. Prior works explored large-scale video-ASR learning but typically treat ASR transcriptions as global video captions.
    - **E3:** method/paper_statement | Abstract and Methodology | high
      locator:: abstract; Section 3.2 Modeling
      quote:: We propose a novel streaming training approach that densely interleaves the ASR words and video frames according to their timestamps. The model is trained to generate frame assigned ASR words in an autoregressive manner.
    - **E4:** system_design/implementation_detail | Video-ASR Data Curation | high
      locator:: Section 3.1
      quote:: This pipeline enables the construction of the Live-CC-5M pretraining set and the Live-WhisperX-526K SFT set. The SFT dataset comprises 526K video clips, each paired with word-level timestamped ASR transcripts and a user prompt.
    - **E5:** experiment_setup/implementation_detail | Video-ASR Data Curation | high
      locator:: Section 3.1, YT-CC-Source-5.7M
      quote:: We aggregate HD-VILA, YT-Temporal-1B, VidChapters, and HowTo100M as our video sources. Applying these filtering criteria results in a curated set of 10.7 million YouTube video IDs. Applying language and caption-density filters, we download these 5.7 million videos with English CC.
    - **E6:** algorithm/implementation_detail | Modeling | high
      locator:: Section 3.2, Training with Dense Interleaving Sequence
      quote:: The training sequence is formatted as [Con] followed by alternating frame spans and word spans. [Con] denotes context information of the video, F denotes a frame, W denotes the words, and by default the method uses 2 FPS frame rate and k = 1 as the time interval.
    - **E7:** implementation/implementation_detail | Modeling | high
      locator:: Section 3.2, Sequence Pre-processing
      quote:: For pre-training, the original YouTube ASR transcripts use fixed timestamps, so the authors uniformly distribute each segment's duration across its constituent words. During SFT, WhisperX provides precise word-level timestamps. Silent frames directly predict the ellipsis token.
    - **E8:** implementation/implementation_detail | Modeling | high
      locator:: Section 3.2, Inference
      quote:: During inference, LiveCC processes input frames sequentially. To accelerate language decoding, it caches the Key-Value pairs of previous prompts, visual frames, and generated text. For long sequences, it discards visual tokens every 240 seconds while retaining text tokens.
    - **E9:** experiment_setup/paper_statement | The LiveSports-3K Benchmark | high
      locator:: Section 4.1
      quote:: The benchmark spans a broader range of common sports. The authors selected the top 50 sports categories, sampled candidate videos, filtered visually grounded events, curated 416 videos across 49 sports categories, and removed these videos from the training dataset.
    - **E10:** experiment_setup/paper_statement | Crafting LiveSports-3K-CC/QA and Experiments Setup | high
      locator:: Sections 4.2 and 5.1
      quote:: LiveSports-3K-CC consists of 1,702 events with high-quality live CCs. LiveSports-3K-QA contains 1,174 multiple-choice questions after removing speech-recognition questions. Commentary is evaluated by pairwise GPT-4o judging for semantic alignment and stylistic consistency.
    - **E11:** experiment_setup/implementation_detail | Experiments Setup | high
      locator:: Section 5.1
      quote:: The model initializes from Qwen2-VL-7B-Base. Formal pre-training uses 30 to 240 second Live-CC-5M, and SFT uses Live-Whisper-526K plus LLaVA-Video-178K. The batch size is 512 on 128 GPUs, with learning rates 2e-5 and 1e-5.
    - **E12:** ablation/ablation | Ablation Study | medium
      locator:: Table 1a and Section 5.2
      quote:: Caption-style pre-training on 5M gives LiveSports-3K-CC win rate 14.0 and Video-MME overall 61.1. Streaming-style pre-training on 5M gives win rate 32.9 and Video-MME overall 61.0, indicating a large commentary gain with similar QA.
    - **E13:** ablation/ablation | Ablation Study | medium
      locator:: Table 1b, Table 1c, Section 5.2
      quote:: Previous ASR context improves LiveSports-3K-CC win rate to 32.0, versus 14.7 with no context. Scaling data from 1M to 10M improves commentary win rate from 29.1 to 36.0, while Video-MME overall falls from 61.0 at 5M to 58.0 at 10M.
    - **E14:** ablation/ablation | Ablation Study | medium
      locator:: Table 2
      quote:: Adding Live-WhisperX-526K to LLaVA-Video-178K during SFT improves the Qwen2-VL-7B-Base row's LiveSports-3K-CC win rate from 16.7 to 33.7. Starting from LiveCC-7B-Base and SFT data gives 41.5 on commentary.
    - **E15:** result/experiment_result | Overall Results | medium
      locator:: Table 3 and Section 5.3
      quote:: LiveCC-7B-Instruct scores 64.1 on VideoMME without subtitles and 70.3 with subtitles, compared with Qwen2-VL-7B-Instruct at 63.3 and 69.0. It scores 59.8 on OVOBench average, above LLaVA-Video-7B at 52.9.
    - **E16:** result/experiment_result | Overall Results | medium
      locator:: Table 4
      quote:: On LiveSports-3K-CC, LiveCC-7B-Instruct reaches 41.5 win rate and LiveCC-7B-Base reaches 43.2. LLaVA-Video-72B reaches 35.0, Qwen2.5-VL-72B-Instruct reaches 30.4, and Qwen2-VL-7B-Instruct reaches 9.3.
    - **E17:** result/experiment_result | Additional Experiments | medium
      locator:: Table 5, Section 9.1
      quote:: Response latency is defined as the time a user waits to see the model's output. LLaVA-Video-72B has 20.51 seconds latency, LLaVA-Video-7B has 5.62 seconds, and LiveCC-7B-Instruct has 0.17 seconds with frame input and streaming inference.
