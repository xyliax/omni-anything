arXiv:2510.09608v2 [cs.CV] 31 May 2026

Published as a conference paper at ICLR 2026

# STREAMINGVLM: REAL-TIME UNDERSTANDING FOR INFINITE VIDEO STREAMS

Ruyi Xu $ ^{1*} $ Guangxuan Xiao $ ^{1*} $

Yukang Chen $ ^{2} $ Liuning He $ ^{1} $ Yao Lu $ ^{2} $ Song Han $ ^{1,2} $

 $ ^{1} $MIT  $ ^{2} $NVIDIA

https://github.com/mit-han-lab/streaming-vlm

## ABSTRACT

Vision-language models (VLMs) could power real-time assistants and autonomous agents, but they face a critical challenge: understanding near-infinite video streams without escalating latency and memory usage. Processing entire videos with full attention leads to quadratic computational costs and poor performance on long videos. Meanwhile, simple sliding window methods are also flawed, as they either break coherence or suffer from high latency due to redundant recomputation. In this paper, we introduce StreamingVLM, a model designed for real-time, stable understanding of infinite visual input. Our approach is a unified framework that aligns training with streaming inference. During inference, we maintain a compact KV cache by reusing states of attention sinks, a short window of recent vision tokens, and a long window of recent text tokens. This streaming ability is instilled via a simple supervised fine-tuning (SFT) strategy that applies full attention on short, overlapped video chunks, which effectively mimics the inference-time attention pattern without training on prohibitively long contexts. For evaluation, we build Inf-Streams-Eval, a new benchmark with videos averaging over two hours that requires dense, per-second alignment between frames and text. On Inf-Streams-Eval, StreamingVLM achieves a 66.18% win rate against GPT-4O mini and maintains stable, real-time performance at up to 8 FPS on a single NVIDIA H100. Notably, our SFT strategy also enhances general VQA abilities without any VQA-specific fine-tuning, improving performance on LongVideoBench by +4.30 and OVOBench Realtime by +5.96.

## 1 INTRODUCTION

VLMs could power autonomous driving, embodied agents, and real-time assistants, but they face critical challenges: understanding near-infinite video, responding in real time stably. To accept infinite input, common ideas are Sliding Window Attention with or without overlapping. As shown in Figure 1: (a) Full Attention suffers from heavy memory and latency; (b) Sliding Window (w/o Overlapping) resets context frequently and breaks coherence; (c) Sliding Window Attention (w/ Overlapping) keeps recent tokens but recomputes attention many times, which hurts efficiency.

Aligning training with inference adds further challenges. Real streaming requires taking infinite visual input in real time and replying with very low delay, but training cannot use extremely long videos. Current approaches to KV cache eviction often lack alignment with the training phase. How to train on short videos and still enable the model to reason over very long streams remains underexplored. This leads to our core question: How can we train VLMs to understand video chunks in real time and reason stably over infinite video, moving toward human-like intelligence?

In this paper, we propose StreamingVLM, a unified framework that aligns training with streaming inference and a dataset curation pipeline. The key ideas are: (1) Train the VLM with full attention on short, overlapped video chunks. (2) At inference, use an attention sink and a sliding window with

 $ ^{*} $Equal contribution

1

Published as a conference paper at ICLR 2026

<div style="text-align: center;"><img src="imgs/img_in_image_box_216_161_1008_418.jpg" alt="Image" width="64%" />

(a) Full Attention
Quickly exceed training length. Poor efficiency and OOM on long video.
(b) Sliding Window (w/o Overlapping)
Need large chunks for coherence. Cannot serve realtime at peak context length.
(c) Sliding Window (w/ Overlapping)
Each sliding window requires recomputing attention. Latency prevents real-time inference.
(d) StreamingVLM (Sliding Window + Reuse KV)
Keep latency stably low. Reuse states as compact KV with contiguous RoPE.
(e) T(T2) Win Rate: 3.89 %
(f) T(TW) Win Rate: 23.54 %
(g) T(TW2) Win Rate: 66.54 %
(h) T(TW) Win Rate: 66.18 %

</div>


<div style="text-align: center;">Figure 1: Illustration of StreamingVLM vs. existing VLMs. Let T be video length and W the sliding-window size. (a) Full Attention:  $ O(T^{2}) $ cost; unbounded memory; degrades beyond training length. (b) Sliding Window (no overlap): bounded memory but short chunks break coherence; long chunks raise latency. (c) Sliding Window (overlap): recomputation per window yields high latency. (d) StreamingVLM (Sliding Window + Reuse KV): reuses states of attention sinks, a short vision window and long text window, preserving history at low latency. “Win rate” is the pairwise win share vs. GPT-4o mini (judge: GPT-5).</div>


to handle infinite video, aligned with training. (3) Reuse past KV states and use contiguous position IDs to keep inference stable.

Using this framework, we build Inf-Streams-Train, a sports commentary SFT dataset of over 4000 hours and Inf-Streams-Eval, a new benchmark with videos averaging over two hours that requires dense, per-second alignment between frames and text. Then, we fine-tune Qwen-2.5-VL-7B-Instruct for real-time commentary, yielding StreamingVLM that can understand infinite video and response in real time. We evaluate StreamingVLM on captioning and VQA tasks, including LiveCC-Sports3K CC and Inf-Streams-Eval for captioning, and LongVideoBench (and related VQA benchmarks) for video understanding (Chen et al., 2025a; Wang et al., 2025a).

On captioning tasks, StreamingVLM, with its infinite video understanding, outperforms existing models such as Livecc-7B-Instruct. As shown in Figure 2, StreamingVLM performs well on practical tasks: it can provide continuous commentary for more than two hours on sports games. On VQA tasks, even without any VQA fine-tuning, StreamingVLM still improves on LongVideoBench by +4.30. In terms of efficiency, StreamingVLM maintains a low and stable latency, making it highly suitable for real-world streaming understanding tasks.

<div style="text-align: center;"><img src="imgs/img_in_image_box_213_1023_1007_1185.jpg" alt="Image" width="64%" />

Qwen2.5-VL-7B-Instruct (w/o SFT): ✗Cannot Generate Coherently
00:00:00 Players are warming up before kickoff. (50 m/tok)
00:00:02 Players from both teams are on the field, warming up ...
00:00:04 Players from both teams are on the field, warming up ...

StreamingVLM (Sliding Window + Reuse KV): ✓ (50 m/tok)
00:00:00 Fans will have fun tonight, so let's take a look at the kickoff.
00:00:02 On the right-hand side, we've got Portugal in Red.
00:00:04 And then at the other end, it's Spain setting up for kickoff.

LiveCC-7B-Instruct (Full Attention): ✗Exceed Training Length
00:03:30 shot shot shot shot shot shot shot shot ... (531 m/tok)

StreamingVLM (Sliding Window + Reuse KV): ✓ (50 m/tok)
00:03:30 Ronaldo against David De Gea. A heart-stopping penalty.

LiveCC-7B-Instruct (Sliding Window): ✗Lose Long-term Memory
01:31:31 Will Ronaldo be able to score the first penalty? (180 m/tok)

StreamingVLM (Sliding Window + Reuse KV): ✓ (50 m/tok)
01:31:31 Portugal got three points with Ronaldo's three goals!

</div>


<div style="text-align: center;">Figure 2: Issues with existing VLMs. (1) Without SFT, models cannot generate cross-round content coherently. (2) With full attention, the context exceeds the training length after processing 2-5 minutes of video and latency becomes prohibitive. (3) With a sliding window, models cannot retain enough context to benefit from efficiency. In contrast, StreamingVLM addresses these issues, enabling coherent commentary, real-time generation, and long-term history.</div>


## 2 METHOD

In this section, we introduce our method for the model and the data. This part has three components: (1) inference scheme for vision-language processing that supports low-latency updates on infinite

2

Published as a conference paper at ICLR 2026

<div style="text-align: center;"><img src="imgs/img_in_image_box_211_161_1006_333.jpg" alt="Image" width="64%" />

Round 1 1 2 3 4 5 6 7 0 1 2 ... RoPE Index ◇ Attention Sink
Round 2 1 2 3 4 5 6 7 8 ◇ Evicted Token ▶ Vision Token
Round 3 1 2 3 4 5 6 7 8 9 ◇ Previous Text
Round 4 1 2 3 4 5 6 7 8 9 ◇ Current Text

</div>


<div style="text-align: center;">Figure 3: Inference scheme of StreamingVLM. We keep 512 attention-sink tokens to stabilize attention, a long text window of 512 recent tokens to preserve long-term memory, and a short vision window covering 16 seconds to track ongoing actions. We use Contiguous RoPE: indices are shifted to stay within a fixed range, keeping positions in-distribution and within the training length.</div>


video used by StreamingVLM; (2) a training strategy that equips StreamingVLM with streaming inference capability; and (3) the data curation pipelines that provide long-horizon, real-time data for training and a new benchmark, Inf-Streams.

### 2.1 INFERENCE SCHEME OF STREAMING VLM

This section describes the StreamingVLM inference structure shown in Figure 3. These design choices reduce the computation in Figure 1(c) while maintaining comparable performance.

Streaming-aware KV Cache The key idea is to maintain a compact and stable KV cache by reusing previous states during streaming inference. As new video frames arrive, we reuse the states of (i) a set of sink text tokens — including the system and previous text — of length  $ T_{\text{sink}} $; (ii) a long window of the most recent text tokens of length  $ T_{\text{window}} $; and (iii) a short window of the most recent vision tokens of length  $ V_{\text{window}} $. In Figure 3, the cache lengths are  $ T_{\text{sink}} = 1 $,  $ T_{\text{window}} = 3 $, and  $ V_{\text{window}} = 4 $.

With this structure, older vision tokens are evicted first; early text is evicted only when the budget is exceeded. Instead of recomputing previous tokens, this asymmetric retention keep the lowest computation while maintaining sufficient context for coherent generation over time, yielding comparable performance with Sliding Window with Overlapping (Figure 1(c)).

Contiguous RoPE To prevent positional drift after eviction, we apply contiguous rotary positional embeddings (RoPE). When earlier tokens are removed, the RoPE indices of subsequent and incoming tokens are shifted so that their positions remain numerically contiguous with the last retained token. Once the video length surpasses the total window size, the effective RoPE indices stop growing and remain within a bounded range. This keeps positional values in-distribution and stabilizes long-horizon streaming inference.

When applied to the Qwen-VL family, which uses 3D positional embeddings for visual tokens, we use contiguous 3D RoPE. The RoPE index is still left-shifted to stay contiguous; for vision tokens, we build 3D indices (time, height, width) and assemble them by the 3D rule, matching the interleaved vision–text layout.

### 2.2 TRAINING STRATEGY

To endow the model with the ability to follow the streaming inference pattern in Figure 3 while keeping training simple, we adopt an overlapped-chunk, full-attention strategy (see Figure 4). The left panel of Figure 4 illustrates the attention at inference time. In this Figure 4, the cache lengths are the same as in Figure 3, with  $ T_{sink}=1 $,  $ T_{window}=3 $, and  $ V_{window}=4 $.

During training (middle panel of Figure 4), rather than replicating the exact sliding-window schedule used at inference, we split a long video stream into consecutive chunks  $ \{C_1, C_2, \ldots\} $ of length  $ W $ frames, with temporal overlap  $ O $ frames between  $ C_i $ and  $ C_{i+1} $ ( $ 0 < O < W $). Each chunk is treated as a training instance in which vision and text tokens (V/T) are sampled and interleaved at  $ 1 $ s intervals. We apply full attention within a chunk, i.e., every token may attend to all tokens inside the same chunk.

3

Published as a conference paper at ICLR 2026

As highlighted in the right panel of Figure 4, this overlapped full-attention supervision closely approximates the effective attention pattern at inference — attention sink, a longer window of recent text, and a shorter window of recent vision retained in the compact KV cache. Aligning training supervision with the test-time context teaches the model the intended recency bias and yields stable streaming behavior without training on prohibitively long, quadratic-cost contexts.

Importantly, mirroring the inference-time schedule, we interleave vision and text tokens within each training chunk — rather than adopting the common VLM paradigm that places all vision tokens before text. We compute loss only on text positions aligned to the per-second narration; when a second has no narration, we insert a placeholder token "..." in that slot while keeping the interleaved V/T layout. This supervision teaches the model to synchronize generation with the stream—learning when to speak and when to remain silent—and consequently endows StreamingVLM with reliable streaming narration behavior at inference.

<div style="text-align: center;"><img src="imgs/img_in_image_box_641_315_1008_470.jpg" alt="Image" width="29%" />

Inference Attention Map
SFT Attention Map

</div>


<div style="text-align: center;">Figure 4: Training Strategy. We train with overlapped full attention that mimics test-time attention. (1), (2), (3) and (4) are four training samples, both keeping the attention sinks and overlap later in time.</div>


### 2.3 DATA CURATION PIPELINE

<div style="text-align: center;"><img src="imgs/img_in_image_box_213_645_1007_761.jpg" alt="Image" width="64%" />

Video Collection and ASR
Data Cleaning with LLM
Data Segmentation
Min Words Filtering
SFT & Eval Data
QHT Filtering
Stephen Curry pulls up!
Stephen Curry pulls up!
Stephen Curry pulls up!
QHT Filtering
HQ Annealing Data

</div>


<div style="text-align: center;">Figure 5: Data Curation Pipeline. We collect games from five sports—basketball, soccer, American football, ice hockey, and baseball. We use GPT to edit or reject low-quality segments, yielding 2,449 full games. We then build two datasets through separate pipelines: an SFT dataset using overlapped chunking, and a high-quality annealing dataset focused on real-time actions.</div>


#### 2.3.1 VIDEO COLLECTION AND ASR

As shown in Figure 5, we collected game videos from five sports: basketball, soccer, ice hockey, baseball, and American football, including 712 basketball games, 544 soccer games, 402 ice hockey games, 399 baseball games, and 392 American football games. The commentary language is English. To ensure video quality and read speed, we constrained the video resolution to 360P–720P with a frame rate of 24 FPS. First, we used the WhisperX model to extract real-time speech (ASR) from these games, obtaining an initial corpus of videos with a total duration of over 6,000 hours and their corresponding real-time commentary.

#### 2.3.2 DATA CLEANING

In complete commentary videos, there are often many useless segments, such as advertisements and host monologues. These segments have weak connections between visual content and ASR semantics, making it impossible for the model to infer content from the footage. In addition, the ASR model sometimes fails to correctly recognize details such as player names and team names.

Therefore, we set rules and used GPT to clean these data. We first split a game into 120-second segments and concatenate the commentary within each segment, then split it into sentences. Using the segment and the video title (including game time and both teams) as context, we ask the GPT-5 model to make a decision according to the rules, with options “keep,” “delete,” and “edit” each sentence in one chunk. “Keep” means the content is game commentary and is correct. “Edit” means it is commentary but needs to modify some details, such as incorrect names, and the corrected complete sentence is returned. “Delete” means non-compliant content that should not appear in the training data.

For kept sentences, the timestamps are consistent with the ASR results; for edited sentences, we evenly distribute the original sentence duration over each word of the edited sentence (since a sen-

4

Published as a conference paper at ICLR 2026

tence typically lasts about 3–5 seconds, the error is within a tolerable range). In the original ASR data, 46.32% were kept, 37.89% were edited, and 15.79% were deleted, ultimately forming the raw video-commentary pairs of our data.

#### 2.3.3 SFT AND EVALUATION DATA SEGMENTATION

For the train and validation sets, we build the data as follows. Under the training setup in Section 2.2, we split videos with  $ W = 24 $ s and  $ O = 12 $ s. To ensure enough commentary labels per sample, we require at least  $ 2*W $ words as min words filtering. All commentary before the segment is treated as previous text. During training, we take the first  $ T_{sink} $ tokens and the last  $ T_{window} $ tokens from this previous text to match the inference setup.

For evaluation, we create a new benchmark, Inf-Streams-Eval. It contains 20 full games with an average length of 2.12 hours. We split each game into 100 s segments, selecting those with at least 200 words. Commentaries of these segments are considered as ground truth. For scoring, a larger model (we use gpt-5) votes between two model outputs with access to ground-truth references. The model with more votes (higher win rate) is judged to provide better commentary.

Inf-Streams-Eval has two settings: chunk and infinite, denoted by  $ \dagger $ and  $ \infty $, respectively in following tables. In Figure 1, the chunk mode is panel (b), and the infinite mode is panel (d). For models that cannot do infinite inference, we cut the video into chunks; the model receives the previous text and the current chunk to produce a caption. For models that support infinite inference, the model runs on the full stream; we keep its past outputs as previous text and continue captioning until the video ends.

#### 2.3.4 HIGH-QUALITY ANNEALING DATA

The above dataset can sft the model's ability for real-time video understanding. However, it contains a lot of content such as team information and season history; for the human experience of the commentary task, we prefer the model to provide real-time commentary on on-field events. Therefore, we created a high-quality annealing data.

We first slice all data without overlap, requiring each clip to be 16–64 seconds long with internal silence no longer than 3 seconds; each clip must also contain at least  $ 2 \times D $ (duration in seconds) words. Across all games, we obtained 52,530 new samples. Then, we define the standard of “real-time commentary.” For each sample, we use GPT-5 to determine whether the proportion of “real-time commentary” exceeds 80% to decide whether to keep it. In the end, only 14,786 samples were retained. Subsequent experiments in Table 6 show that after applying this portion of data for sft, the model’s capability and commentary quality further improved.

## 3 EXPERIMENTS

In this section, we first describe the implementation details, then evaluate on video captioning and VQA against strong baselines. We next test the efficiency of StreamingVLM. Finally, we run ablations to better understand its behavior.

### 3.1 EXPERIMENTAL SETUP

Training We fine-tune StreamingVLM from Qwen2.5-VL-Instruct-7B (Bai et al., 2025). Step 1 teaches the model the infinite streaming inference pattern. We train on our SFT set (525K streaming samples) and on LiveCC's Live-WhisperX-526K (526K streaming samples) (Chen et al., 2025a). Step 2 uses our high-quality annealing data (14K streaming samples, each 16–64 s with detailed actions) to boost real-time action commentary and improve human experience. After these two stages, we obtain StreamingVLM. The total compute is about 128 H100-days.

Baselines We select strong baselines to compare with StreamingVLM. For the captioning task, we use GPT-4o mini to show commentary strength, and Livecc-7B-Instruct, which is trained on 5.5M YouTube video clips (30 – 240 s) and 178K Video-Question-Answer samples, working well on short videos commentary (OpenAI, 2024; Chen et al., 2025a). We also include ReKV, a strong training-free streaming-inference method (Di et al., 2025). Due to design limits, GPT-4o mini is evaluated

5

Published as a conference paper at ICLR 2026

<div style="text-align: center;">Table 1: Captioning accuracy (win rate vs. baselines). Baselines with/without chunking fall short; StreamingVLM surpasses strong models such as GPT-4o and produces compelling commentary.(Superscripts for Inf-Streams-Eval:  $ \infty = \text{infinite} $;  $ \dagger = \text{chunk} $ length 100s. On Livecc-Sports-3K CC, LiveCC has only one mode and cannot be compared against itself, so we show “-”.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Win Rate A vs. B\nModel A</td><td colspan="3">Inf-Streams-Eval</td><td colspan="4">Livecc-Sports-3K cc</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>GPT-4o $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>Livecc $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>Livecc $ ^{\infty} $</td><td style='text-align: center; word-wrap: break-word;'>LLaVA</td><td style='text-align: center; word-wrap: break-word;'>GPT-4o</td><td style='text-align: center; word-wrap: break-word;'>Gemini</td><td style='text-align: center; word-wrap: break-word;'>Livecc</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen-2.5-VL-7B-Instruct $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>0.01</td><td style='text-align: center; word-wrap: break-word;'>20.44</td><td style='text-align: center; word-wrap: break-word;'>95.97</td><td style='text-align: center; word-wrap: break-word;'>24.50</td><td style='text-align: center; word-wrap: break-word;'>16.25</td><td style='text-align: center; word-wrap: break-word;'>28.38</td><td style='text-align: center; word-wrap: break-word;'>34.11</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Livecc-7B-Instruct $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>15.73</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Livecc-7B-Instruct $ ^{\infty} $</td><td style='text-align: center; word-wrap: break-word;'>1.82</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>41.50</td><td style='text-align: center; word-wrap: break-word;'>40.06</td><td style='text-align: center; word-wrap: break-word;'>39.73</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>StreamingVLM $ ^{\infty} $</td><td style='text-align: center; word-wrap: break-word;'>66.18</td><td style='text-align: center; word-wrap: break-word;'>87.81</td><td style='text-align: center; word-wrap: break-word;'>99.12</td><td style='text-align: center; word-wrap: break-word;'>47.33</td><td style='text-align: center; word-wrap: break-word;'>45.59</td><td style='text-align: center; word-wrap: break-word;'>44.21</td><td style='text-align: center; word-wrap: break-word;'>56.19</td></tr></table>

<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Chunk Size</th><th style='text-align: center;'>LiveCC</th><th style='text-align: center;'>StreamingVLM</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>25</td><td style='text-align: center;'>8.4</td><td style='text-align: center;'>66.5</td></tr>
    <tr><td style='text-align: center;'>50</td><td style='text-align: center;'>13.2</td><td style='text-align: center;'>68.4</td></tr>
    <tr><td style='text-align: center;'>100</td><td style='text-align: center;'>15.7</td><td style='text-align: center;'>66.8</td></tr>
    <tr><td style='text-align: center;'>500</td><td style='text-align: center;'>4.0</td><td style='text-align: center;'>67.4</td></tr>
    <tr><td style='text-align: center;'>∞</td><td style='text-align: center;'>1.8</td><td style='text-align: center;'>66.2</td></tr>
  </tbody>
</table>

<div style="text-align: center;">Figure 6: For existing VLMs, balancing cross-chunk coherence with training-length limits is challenging.</div>


on Inf-Streams-Eval in the chunk setting, not the infinite mode used by StreamingVLM. LiveCC7B-Instruct is tested in both chunked and infinite settings. For the VQA task, we use Qwen2.5-VL7B-Instruct, which is the base model before SFT for StreamingVLM, to show that our SFT pipeline improves the base ability (Bai et al., 2025).

Benchmark We evaluate real-time captioning and video understanding across a broad set of tasks. For captioning, we use our Inf-Streams-Eval (average length 2.12 hours), which tests long-horizon commentary and the LiveSports3K-CC benchmark (49 sports, 416 clips, each  $ \geq $ 10 s) (Chen et al., 2025a). For video understanding, we evaluate StreamingVLM on four public suites. VideoMME: a multi-task set (QA, caption, grounding) covering short and long videos for general comprehension (Fu et al., 2025). MVBench: fine-grained skills on short clips (actions, objects, counting, temporal order) (Li et al., 2024b). LongVideoBench: long-video QA that requires long-term memory and cross-segment reasoning (Wang et al., 2025a). OVOBench: video QA that tests real-time understanding and streaming perception (Li et al., 2025).

### 3.2 ACCURACY RESULTS

#### 3.2.1 CAPTIONING

We first compare our inference strategy with ReKV on the captioning task. We observe a paradox for training-free ReKV: models without task-specific fine-tuning perform poorly, yet models that are specially fine-tuned (e.g., StreamingVLM) rely on a fixed context format that ReKV's eviction policy disrupts, often yielding no output. In contrast, StreamingVLM's training-inference consistent design resolves this issue.

Then, we evaluate StreamingVLM, Qwen-2.5-VL-7B-Instruct, and LiveCC-7B-Instruct on LiveCC-3K-Sports-CC and Inf-Streams-Eval. As shown in Table 1, on Inf-Streams-Eval, Qwen-2.5-VL-7B-Instruct cannot keep continuous commentary and thus performs poorly. LiveCC-7B-Instruct works.

<div style="text-align: center;">Table 2: Training–inference consistency surpasses ReKV. Non-fine-tuned models lack capability of real-time captioning, while with fine-tuning models ReKV's eviction policy disrupts context, frequently resulting in no output. (Superscripts for Inf-Streams-Eval:  $ \infty $ = infinite;  $ \dagger $ = chunk length 100s.)</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Win Rate\nModel B\nModel A</td><td colspan="3">Inf-Streams-Eval</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>GPT-4o $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>Livecc $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>Livecc $ ^{\infty} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen (+ ReKV) $ ^{\infty} $</td><td style='text-align: center; word-wrap: break-word;'>0.00</td><td style='text-align: center; word-wrap: break-word;'>19.56</td><td style='text-align: center; word-wrap: break-word;'>63.57</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>StreamingVLM (+ ReKV) $ ^{\infty} $</td><td style='text-align: center; word-wrap: break-word;'>0.00</td><td style='text-align: center; word-wrap: break-word;'>0.00</td><td style='text-align: center; word-wrap: break-word;'>0.00</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>StreamingVLM (+ Ours) $ ^{\infty} $</td><td style='text-align: center; word-wrap: break-word;'>66.18</td><td style='text-align: center; word-wrap: break-word;'>87.81</td><td style='text-align: center; word-wrap: break-word;'>99.12</td></tr></table>

better with chunked inference. Figure 6 further shows that short chunks break coherence; these designs do not support infinite inference, and with long chunks they soon exceed the training length and degrade.

In contrast, StreamingVLM runs in infinite mode; its long-term memory and streaming video perception give it a clear edge, surpassing GPT-4o mini in commentary quality. Figure 2 (the figure shown) illustrates a real case where StreamingVLM maintains coherent output, real-time latency, and long-term memory, addressing the core challenge of real-time perception for infinite video streams. On LiveCC-3K-Sports-CC, StreamingVLM also performs better than baselines, showing stable streaming captioning on videos of various length.

6

Published as a conference paper at ICLR 2026

<div style="text-align: center;">Table 3: VQA results comparing StreamingVLM with its base model. Without any VQA fine-tuning, StreamingVLM delivers consistent accuracy gains across all tasks, with the strongest improvements on long-horizon and real-time settings.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>MVBench</td><td style='text-align: center; word-wrap: break-word;'>Video MME (w/o sub.)</td><td style='text-align: center; word-wrap: break-word;'>LongVideoBench</td><td style='text-align: center; word-wrap: break-word;'>OVOBench (Realtime)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen-2.5-VL-7B-Instruct</td><td style='text-align: center; word-wrap: break-word;'>67.34</td><td style='text-align: center; word-wrap: break-word;'>65.10</td><td style='text-align: center; word-wrap: break-word;'>54.70</td><td style='text-align: center; word-wrap: break-word;'>56.00</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>StreamingVLM</td><td style='text-align: center; word-wrap: break-word;'>69.16</td><td style='text-align: center; word-wrap: break-word;'>65.10</td><td style='text-align: center; word-wrap: break-word;'>59.00</td><td style='text-align: center; word-wrap: break-word;'>61.96</td></tr></table>

<div style="text-align: center;">Table 4: Ablation of RoPE on captioning (win rate). Native RoPE drops on infinite streams; 100 s chunking partly recovers but hurts long-term memory; contiguous RoPE keeps indices bounded and sustains infinite performance. (Superscripts for Inf-Streams-Eval:  $ \infty = \text{infinite}; ^{\dagger} = $ chunk length 100s.)</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Win Rate A vs. B\nModel B\nModel A</td><td colspan="3">Inf-Streams-Eval</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>GPT-4o $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>Livecc $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>Livecc $ ^{\infty} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Native $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>63.23</td><td style='text-align: center; word-wrap: break-word;'>74.00</td><td style='text-align: center; word-wrap: break-word;'>98.07</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Native $ ^{\infty} $</td><td style='text-align: center; word-wrap: break-word;'>25.09</td><td style='text-align: center; word-wrap: break-word;'>59.42</td><td style='text-align: center; word-wrap: break-word;'>60.32</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Contiguous $ ^{\infty} $</td><td style='text-align: center; word-wrap: break-word;'>66.18</td><td style='text-align: center; word-wrap: break-word;'>87.81</td><td style='text-align: center; word-wrap: break-word;'>99.12</td></tr></table>

<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Processed video length (s)</th><th style='text-align: center;'>(a) Full Attention</th><th style='text-align: center;'>(b) Sliding Window (w/o Overlapping)</th><th style='text-align: center;'>(c) Sliding Window (w/ Overlapping)</th><th style='text-align: center;'>(d) StreamingVLM (Sliding Window + Reuse KV)</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>0</td><td style='text-align: center;'>0.05</td><td style='text-align: center;'>0.05</td><td style='text-align: center;'>0.05</td><td style='text-align: center;'>0.05</td></tr>
    <tr><td style='text-align: center;'>100</td><td style='text-align: center;'>0.15</td><td style='text-align: center;'>0.05</td><td style='text-align: center;'>0.33</td><td style='text-align: center;'>0.05</td></tr>
    <tr><td style='text-align: center;'>200</td><td style='text-align: center;'>0.49</td><td style='text-align: center;'>0.18</td><td style='text-align: center;'>0.32</td><td style='text-align: center;'>0.05</td></tr>
    <tr><td style='text-align: center;'>300</td><td style='text-align: center;'></td><td style='text-align: center;'>0.05</td><td style='text-align: center;'>0.26</td><td style='text-align: center;'>0.05</td></tr>
    <tr><td style='text-align: center;'>400</td><td style='text-align: center;'></td><td style='text-align: center;'>0.18</td><td style='text-align: center;'>0.32</td><td style='text-align: center;'>0.05</td></tr>
    <tr><td style='text-align: center;'>500</td><td style='text-align: center;'></td><td style='text-align: center;'>0.05</td><td style='text-align: center;'>0.38</td><td style='text-align: center;'>0.05</td></tr>
    <tr><td style='text-align: center;'>600</td><td style='text-align: center;'></td><td style='text-align: center;'>0.18</td><td style='text-align: center;'>0.39</td><td style='text-align: center;'>0.05</td></tr>
    <tr><td style='text-align: center;'>700</td><td style='text-align: center;'></td><td style='text-align: center;'>0.05</td><td style='text-align: center;'>0.39</td><td style='text-align: center;'>0.05</td></tr>
    <tr><td style='text-align: center;'>800</td><td style='text-align: center;'></td><td style='text-align: center;'>0.18</td><td style='text-align: center;'>0.38</td><td style='text-align: center;'>0.05</td></tr>
    <tr><td style='text-align: center;'>900</td><td style='text-align: center;'></td><td style='text-align: center;'>0.05</td><td style='text-align: center;'>0.40</td><td style='text-align: center;'>0.05</td></tr>
    <tr><td style='text-align: center;'>1000</td><td style='text-align: center;'></td><td style='text-align: center;'>0.18</td><td style='text-align: center;'>0.41</td><td style='text-align: center;'>0.05</td></tr>
  </tbody>
</table>

<div style="text-align: center;">Figure 7: Per-token latency vs. video length. Full attention hits OOM; sliding window w/o Overlapping spikes above real time; sliding window w/ Overlapping remains inefficient; StreamingVLM latency stays low and stable. The dashed line marks the real-time threshold (10 tokens/s  $ \Rightarrow $  $ \leq $ 0.1 s per token).</div>


#### 3.2.2 VQA

We evaluate StreamingVLM and its base model, Qwen-2.5-VL-7B-Instruct, on four VQA tasks. As shown in Table 3, even without any VQA SFT, StreamingVLM outperforms the base on all tasks, showing that our SFT improves general visual ability. OVOBench Realtime tests understanding of the immediate, streaming scene. On this streaming perception task, StreamingVLM improves by 5.96%. This highlights the strength of Inf-Streams-Train and our training strategy, which enhances the model's core abilities.

### 3.3 EFFICIENCY TESTS

As shown in Figure 7, we report per-token latency for the three methods in Figure 1 on infinite commentary: VLMs with full attention, sliding window attention (w/o overlapping), sliding window attention (w/ overlapping), and the inference strategy of StreamingVLM, respectively correspond to panels (a), (b), (c), and (d) in the Figure 1.

Real-time replies require latency below a fixed threshold as the dashed line. Full attention soon exceed the limit and OOM. Sliding window (w/o overlapping) needs large chunks for coherence, so it shows a periodic latency pattern: at the start of each chunk the model rebuilds context and the commentary is not coherent with the past; later in the chunk, latency rises sharply and fails to meet real-time needs. Sliding window (w/ overlapping) remains inefficient for computation redundancy. Streaming VLM keeps fixed context length and reuses KV, maintains lower and stable latency, and supports real-time commentary at 8 FPS on a single NVIDIA H100.

### 3.4 ABLATION STUDY

#### 3.4.1 CONTIGUOUS ROPE

We study the effect of contiguous RoPE indices. Since we train with full attention, training only uses the native RoPE. At inference, we compare contiguous RoPE with the native version. As shown in Table 4, native RoPE degrades sharply on infinite streams because its index grows fast and exceeds the training range. Splitting the video into 100 s chunks can partly recover accuracy, but

7

Published as a conference paper at ICLR 2026

<div style="text-align: center;">Table 5: Ablation of sliding window and sink size with accuracy on captioning tasks (win rate). Left: effect of  $ T_{sink} $ and  $ T_{window} $, trained with  $ V_{window} = 16s $. Right: effect of  $ V_{window} $, trained with  $ T_{sink} = 512 $ and  $ T_{window} = 512 $. (Superscripts for Inf-Streams-Eval:  $ \infty = \text{infinite} $;  $ \dagger = \text{chunk length} 100s $.)</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td colspan="2">Infer args</td><td colspan="2">SFT args</td><td colspan="3">Inf-Streams-Eval (Basketball)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ T_{{sink}} $</td><td style='text-align: center; word-wrap: break-word;'>$ T_{{window}} $</td><td style='text-align: center; word-wrap: break-word;'>$ T_{{sink}} $</td><td style='text-align: center; word-wrap: break-word;'>$ T_{{window}} $</td><td style='text-align: center; word-wrap: break-word;'>GPT-4o $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>Livecc $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>Livecc $ ^{\infty} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>512</td><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'>512</td><td style='text-align: center; word-wrap: break-word;'>512</td><td style='text-align: center; word-wrap: break-word;'>69.68</td><td style='text-align: center; word-wrap: break-word;'>89.42</td><td style='text-align: center; word-wrap: break-word;'>99.19</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'>512</td><td style='text-align: center; word-wrap: break-word;'>512</td><td style='text-align: center; word-wrap: break-word;'>512</td><td style='text-align: center; word-wrap: break-word;'>66.76</td><td style='text-align: center; word-wrap: break-word;'>86.03</td><td style='text-align: center; word-wrap: break-word;'>98.69</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>256</td><td style='text-align: center; word-wrap: break-word;'>256</td><td style='text-align: center; word-wrap: break-word;'>512</td><td style='text-align: center; word-wrap: break-word;'>512</td><td style='text-align: center; word-wrap: break-word;'>70.17</td><td style='text-align: center; word-wrap: break-word;'>91.79</td><td style='text-align: center; word-wrap: break-word;'>99.62</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>1024</td><td style='text-align: center; word-wrap: break-word;'>1024</td><td style='text-align: center; word-wrap: break-word;'>512</td><td style='text-align: center; word-wrap: break-word;'>512</td><td style='text-align: center; word-wrap: break-word;'>71.43</td><td style='text-align: center; word-wrap: break-word;'>91.69</td><td style='text-align: center; word-wrap: break-word;'>99.84</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ \infty $</td><td style='text-align: center; word-wrap: break-word;'>$ \infty $</td><td style='text-align: center; word-wrap: break-word;'>$ \infty $</td><td style='text-align: center; word-wrap: break-word;'>$ \infty $</td><td style='text-align: center; word-wrap: break-word;'>60.41</td><td style='text-align: center; word-wrap: break-word;'>72.08</td><td style='text-align: center; word-wrap: break-word;'>98.55</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>512</td><td style='text-align: center; word-wrap: break-word;'>512</td><td style='text-align: center; word-wrap: break-word;'>512</td><td style='text-align: center; word-wrap: break-word;'>512</td><td style='text-align: center; word-wrap: break-word;'>73.64</td><td style='text-align: center; word-wrap: break-word;'>92.33</td><td style='text-align: center; word-wrap: break-word;'>99.38</td></tr></table>


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>$ V_{window} $</td><td colspan="3">Inf-Streams-Eval</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Win Rate vs.</td><td style='text-align: center; word-wrap: break-word;'>GPT-4o $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>Livecc $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>Livecc $ ^{\infty} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0 s</td><td style='text-align: center; word-wrap: break-word;'>52.90</td><td style='text-align: center; word-wrap: break-word;'>77.49</td><td style='text-align: center; word-wrap: break-word;'>97.56</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>1 s</td><td style='text-align: center; word-wrap: break-word;'>63.46</td><td style='text-align: center; word-wrap: break-word;'>83.24</td><td style='text-align: center; word-wrap: break-word;'>98.18</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>4 s</td><td style='text-align: center; word-wrap: break-word;'>66.08</td><td style='text-align: center; word-wrap: break-word;'>83.86</td><td style='text-align: center; word-wrap: break-word;'>98.73</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>8 s</td><td style='text-align: center; word-wrap: break-word;'>65.66</td><td style='text-align: center; word-wrap: break-word;'>85.09</td><td style='text-align: center; word-wrap: break-word;'>99.14</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>32 s</td><td style='text-align: center; word-wrap: break-word;'>65.49</td><td style='text-align: center; word-wrap: break-word;'>85.58</td><td style='text-align: center; word-wrap: break-word;'>99.06</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>16 s</td><td style='text-align: center; word-wrap: break-word;'>66.18</td><td style='text-align: center; word-wrap: break-word;'>87.81</td><td style='text-align: center; word-wrap: break-word;'>99.38</td></tr></table>

<div style="text-align: center;">Table 6: Ablation of SFT strategy and dataset on captioning and VQA. Overlapped SFT strategy improves over the Live-WhisperX-526K base, and adding the high-quality annealing data brings further improvements, especially for infinite streaming task Inf-Streams-Eval. (Superscripts for Inf-Streams-Eval:  $ \infty $ = infinite;  $ \dagger $ = chunk length 100s.)</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Win Rate A vs. B\nModel A\nModel B</td><td colspan="3">Inf-Streams-Eval</td><td colspan="4">Livecc-Sports-3K cc</td><td colspan="4">MVBench Video MME Long VideoBench OVOBench</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>GPT-4o $ ^{\dagger} $ Livecc $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>Livecc $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>LLaVA</td><td style='text-align: center; word-wrap: break-word;'>GPT-4o</td><td style='text-align: center; word-wrap: break-word;'>Gemini</td><td style='text-align: center; word-wrap: break-word;'>Livecc Score</td><td colspan="3">w/o sub.</td><td colspan="2">Realtime</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen-2.5-VL-7B-Instruct $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>0.01</td><td style='text-align: center; word-wrap: break-word;'>20.44</td><td style='text-align: center; word-wrap: break-word;'>95.97</td><td style='text-align: center; word-wrap: break-word;'>24.50</td><td style='text-align: center; word-wrap: break-word;'>16.25</td><td style='text-align: center; word-wrap: break-word;'>28.38</td><td style='text-align: center; word-wrap: break-word;'>34.11</td><td style='text-align: center; word-wrap: break-word;'>67.34</td><td style='text-align: center; word-wrap: break-word;'>65.10</td><td style='text-align: center; word-wrap: break-word;'>54.70</td><td style='text-align: center; word-wrap: break-word;'>56.00</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>+ Live-WhisperX-526K $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>32.17</td><td style='text-align: center; word-wrap: break-word;'>56.52</td><td style='text-align: center; word-wrap: break-word;'>99.05</td><td style='text-align: center; word-wrap: break-word;'>42.77</td><td style='text-align: center; word-wrap: break-word;'>41.86</td><td style='text-align: center; word-wrap: break-word;'>39.37</td><td style='text-align: center; word-wrap: break-word;'>47.80</td><td style='text-align: center; word-wrap: break-word;'>63.71</td><td style='text-align: center; word-wrap: break-word;'>62.10</td><td style='text-align: center; word-wrap: break-word;'>54.30</td><td style='text-align: center; word-wrap: break-word;'>57.69</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>+ Inf-Streams-Train $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>63.46</td><td style='text-align: center; word-wrap: break-word;'>83.82</td><td style='text-align: center; word-wrap: break-word;'>98.95</td><td style='text-align: center; word-wrap: break-word;'>46.45</td><td style='text-align: center; word-wrap: break-word;'>45.48</td><td style='text-align: center; word-wrap: break-word;'>44.27</td><td style='text-align: center; word-wrap: break-word;'>53.07</td><td style='text-align: center; word-wrap: break-word;'>68.66</td><td style='text-align: center; word-wrap: break-word;'>64.90</td><td style='text-align: center; word-wrap: break-word;'>59.00</td><td style='text-align: center; word-wrap: break-word;'>60.55</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>+ High-Quality Annealing Data $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>66.18</td><td style='text-align: center; word-wrap: break-word;'>87.81</td><td style='text-align: center; word-wrap: break-word;'>99.12</td><td style='text-align: center; word-wrap: break-word;'>47.33</td><td style='text-align: center; word-wrap: break-word;'>45.59</td><td style='text-align: center; word-wrap: break-word;'>44.39</td><td style='text-align: center; word-wrap: break-word;'>56.19</td><td style='text-align: center; word-wrap: break-word;'>69.16</td><td style='text-align: center; word-wrap: break-word;'>65.10</td><td style='text-align: center; word-wrap: break-word;'>59.00</td><td style='text-align: center; word-wrap: break-word;'>61.96</td></tr></table>

it harms long-term conherence. With contiguous RoPE, the position index stays bounded, so the model supports infinite inference without loss.

#### 3.4.2 SLIDING WINDOW AND SINK

We firstly verify the value of evicting text during training. Then we search for the best inference settings of  $ T_{sink}, T_{window}, V_{window} $.

First, the left table in Table 5 ablates the lengths of the attention sink and text window. Here  $ T_{sink} $ and  $ T_{window} $ are the lengths of previous attention sink and text window kept during both training and inference. We take a basketball-only subset of the SFT data and train two models: one with text eviction using  $ T_{sink}=512 $ and  $ T_{window}=512 $, and one without eviction. On the Inf-Streams-Eval (basketball subset), we evaluate each model under its matching policy (evict vs. no-evict). The left table in table 5 shows that, for infinite inference, evicting previous text tokens is important and improves performance.

Next, we study different choices of  $ V_{window} $. The right table in Table 5 shows that a 16 s visual window is a good choice: it is long enough to cover recent actions, yet short enough to stay efficient. In contrast, keeping 0 s of vision context leads to a clear drop, confirming that retaining recent vision tokens for continuous actions is essential.

#### 3.4.3 TRAINING STRATEGY AND DATASET

We study the effect of our SFT data and high-quality annealing data. The SFT set teaches the model the infinite streaming inference pattern, while the high-quality annealing data further improves commentary quality.

SFT Strategy As shown in Table 6, with our overlapped training strategy, our SFT subset helps the model adapt to the interleaved vision–text pattern and to understand very long videos. Compared with a model trained only on Live-WhisperX-526K, training on the overlapped SFT data strengthens perception of infinite video, yielding clear gains +31.29 (win rate against GPT-4o-mini) on Inf-Streams-Eval and +3.68 (win rate against LLaVA-Video-72B-Qwen2) on Livecc-Sports-3K cc.

8

Published as a conference paper at ICLR 2026

<div style="text-align: center;">Table 7: Ablation of SFT strategy on captioning and VQA. Overlapped SFT strategy performs significantly better than the ablation model trained without our overlapped-chunk SFT strategy. (Superscripts for Inf-Streams-Eval:  $ \infty $ = infinite;  $ \dagger $ = chunk length 100s.)</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Win Rate A vs. B\nModel A\nModel B</td><td style='text-align: center; word-wrap: break-word;'>Inf-Streams-Eval</td><td colspan="4">Livecc-Sports-3K cc</td><td colspan="4">MVBench Video MME Long VideoBench OVOBench</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>GPT-4o $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>LLaVA GPT-4o</td><td colspan="3">Gemini Livecc Score</td><td colspan="2">w/o sub.</td><td colspan="2">Realtime</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Non-overlapping Strategy\nOverlapped Strategy $ ^{\infty} $</td><td style='text-align: center; word-wrap: break-word;'>62.51\n66.18</td><td style='text-align: center; word-wrap: break-word;'>46.24\n47.33</td><td style='text-align: center; word-wrap: break-word;'>45.08\n45.59</td><td style='text-align: center; word-wrap: break-word;'>43.21\n44.39</td><td style='text-align: center; word-wrap: break-word;'>56.19\n56.19</td><td style='text-align: center; word-wrap: break-word;'>68.79\n69.16</td><td style='text-align: center; word-wrap: break-word;'>65.50\n65.10</td><td style='text-align: center; word-wrap: break-word;'>58.90\n59.00</td><td style='text-align: center; word-wrap: break-word;'>59.20\n61.96</td></tr></table>

As shown in Table 7, we train a new baseline model using our full SFT dataset but without our overlapped-chunk SFT strategy (i.e., using standard non-overlapping chunks). We hypothesize two things: (1) This new model performs significantly worse, proving the data alone is insufficient. (2) This model will fail or perform poorly when run with our streaming KV cache, proving our SFT strategy is essential for the training-inference alignment.

High-quality Annealing Data Our high-quality annealing data focus on real-time content and further boosts model ability. As shown in Table 6, we compare training with and without the high-quality annealing data. We can observe significant gains on both captioning and VQA benchmarks.

## 4 RELATED WORK

Vision–Language Models Early multimodal models start from images and then extend to videos by adding temporal modules or token schedulers. Recent open models improve video understanding and transfer across tasks. Examples include LLaVA-OneVision for unified transfer across images, multi-image inputs, and videos (Li et al., 2024a), Video-LLaMA 2 for spatial–temporal and audio cues (Cheng et al., 2024), InternVideo2/2.5 for scaling video encoders and long context (Wang et al., 2024; 2025b), LongVILA for long video training system (Chen et al., 2025b), and Qwen2.5-VL for strong grounding, document parsing, and long-video skills (Bai et al., 2025). Most systems process finite clips and often place all vision tokens before text, which can hurt alignment in streaming and limit real-time interaction in practice. In contrast, we interleave vision and text at 1 s steps to match real-time commentary and interaction, and we observe gains on both commentary and VQA.

Long-Context and Streaming Inference in Text LLMs To handle near-infinite inputs under fixed memory and delay, the text community has proposed several lines of work: (1) Attention sink + sliding window: Streaming LLM keeps a small set of early “sink” tokens plus a recent window, which stabilizes very long decoding (Xiao et al., 2024). (2) RoPE extension and continuity: YaRN, LongRoPE, and LongLoRA for efficient fine-tuning improve position embedding extrapolation (Peng et al., 2023; Ding et al., 2024; Chen et al., 2024b); our contiguous RoPE follows this idea but targets cross-modal, step-wise updates. (3) KV cache compression/eviction:  $ H_{2}O $, SnapKV, and ReKV reduce KV size by selecting heavy hitters or gating heads (Zhang et al., 2023; Li et al., 2024c; Di et al., 2025). However, these methods are mostly tested on text, and alignment between streaming training and inference remains underexplored. We bring the “sink + sliding window + contiguous position” recipe to cross-modal streaming and introduce a training strategy for streaming inference.

Streaming and Online Video LLMs Several concurrent works target streaming video directly. VideoLLM-online (LIVE) converts offline data into streaming dialogue for long context and low latency (Chen et al., 2024a). VideoStreaming uses a fixed video token budget to handle long videos (Qian et al., 2024). LiveCC aligns large-scale ASR with video frames to push real-time sports commentary (Chen et al., 2025a). In practice, on videos longer than 5 minutes (at least 200 frames), these methods show clear performance drops, and their latency is still far from infinite real-time interaction. Compared with these, we (i) train with overlapped short chunks and full attention to match the sink + sliding window test pattern, and (ii) keep contiguous RoPE across modalities to enable real-time understanding over infinite videos.

VLMs Benchmarks and Evaluation VideoMME covers 900 videos (254 hours) with multimodal inputs and tests both short and long time ranges (Fu et al., 2025). LiveSports-3K-CC compares real-time commentary quality and often uses the "LLM-as-a-judge" win-rate metric (Wang et al., 2025a).

9

Published as a conference paper at ICLR 2026

LVBench targets ultra-long videos and long-term memory (Wang et al., 2025a). However, Current benchmarks often focus on retrieval or summary over long videos and do not require frame-level understanding, so even a very low FPS sample may pass. Our Inf-Streams-Eval is built for near-infinite commentary (over 2 hours). It requires second-level alignment between frames and responses and tests high-FPS, long-video understanding—closer to real-world needs for VLM assistants, robots, and autonomous driving.

## 5 CONCLUSION

In this paper, we introduce StreamingVLM, a unified training—inference framework that brings real-time streaming perception to existing VLMs. We first present an efficient strategy for training streaming VLMs and a data curation pipeline that together boost performance on both streaming tasks and VQA. We then show on real-world cases that our inference design enables real-time video understanding, delivering stable commentary for over 3 hours at up to 8 FPS on a single NVIDIA H100. Finally, we release Inf-Streams, a new SFT dataset and benchmark that tests second-level, real-time understanding on videos averaging over 2 hours. Taken together, this work paves the way for practical deployment in real settings.

## REFERENCES

Shuai Bai, Keqin Chen, Xuejing Liu, Jialin Wang, Wenbin Ge, Sibo Song, Kai Dang, Peng Wang, Shijie Wang, Jun Tang, Humen Zhong, Yuanzhi Zhu, Mingkun Yang, Zhaohai Li, Jianqiang Wan, Pengfei Wang, Wei Ding, Zheren Fu, Yiheng Xu, Jiabo Ye, Xi Zhang, Tianbao Xie, Zesen Cheng, Hang Zhang, Zhibo Yang, Haiyang Xu, and Junyang Lin. Qwen2.5-vl technical report, 2025. URL https://arxiv.org/abs/2502.13923.

Joya Chen, Zhaoyang Lv, Shiwei Wu, Kevin Qinghong Lin, Chenan Song, Difei Gao, Jia-Wei Liu, Ziteng Gao, Dongxing Mao, and Mike Zheng Shou. Videollm-online: Online video large language model for streaming video, 2024a. URL https://arxiv.org/abs/2406.11816.

Joya Chen, Ziyun Zeng, Yiqi Lin, Wei Li, Zejun Ma, and Mike Zheng Shou. Livecc: Learning video llm with streaming speech transcription at scale, 2025a. URL https://arxiv.org/abs/2504.16030.

Yukang Chen, Shengju Qian, Haotian Tang, Xin Lai, Zhijian Liu, Song Han, and Jiaya Jia. Longlora: Efficient fine-tuning of long-context large language models. In International Conference on Learning Representations, 2024b.

Yukang Chen, Fuzhao Xue, Dacheng Li, Qinghao Hu, Ligeng Zhu, Xiuyu Li, Yunhao Fang, Haotian Tang, Shang Yang, Zhijian Liu, Yihui He, Hongxu Yin, Pavlo Molchanov, Jan Kautz, Linxi Fan, Yuke Zhu, Yao Lu, and Song Han. Longvila: Scaling long-context visual language models for long videos. In International Conference on Learning Representations, 2025b.

Zesen Cheng, Sicong Leng, Hang Zhang, Yifei Xin, Xin Li, Guanzheng Chen, Yongxin Zhu, Wenqi Zhang, Ziyang Luo, Deli Zhao, and Lidong Bing. Videollama 2: Advancing spatial-temporal modeling and audio understanding in video-llms, 2024. URL https://arxiv.org/abs/2406.07476.

Shangzhe Di, Zhelun Yu, Guanghao Zhang, Haoyuan Li, Tao Zhong, Hao Cheng, Bolin Li, Wanggui He, Fangxun Shu, and Hao Jiang. Streaming video question-answering with in-context video k-cache retrieval, 2025. URL https://arxiv.org/abs/2503.00540.

Yiran Ding, Li Lyna Zhang, Chengruidong Zhang, Yuanyuan Xu, Ning Shang, Jiahang Xu, Fan Yang, and Mao Yang. Longrope: Extending llm context window beyond 2 million tokens, 2024. URL https://arxiv.org/abs/2402.13753.

Chaoyou Fu, Yuhan Dai, Yongdong Luo, Lei Li, Shuhuai Ren, Renrui Zhang, Zihan Wang, Chenyu Zhou, Yunhang Shen, Mengdan Zhang, Peixian Chen, Yanwei Li, Shaohui Lin, Sirui Zhao, Ke Li, Tong Xu, Xiawu Zheng, Enhong Chen, Caifeng Shan, Ran He, and Xing Sun. Video-mme: The first-ever comprehensive evaluation benchmark of multi-modal llms in video analysis, 2025. URL https://arxiv.org/abs/2405.21075.

10

Published as a conference paper at ICLR 2026

Bo Li, Yuanhan Zhang, Dong Guo, Renrui Zhang, Feng Li, Hao Zhang, Kaichen Zhang, Peiyuan Zhang, Yanwei Li, Ziwei Liu, and Chunyuan Li. Llava-onevision: Easy visual task transfer, 2024a. URL https://arxiv.org/abs/2408.03326.

Kunchang Li, Yali Wang, Yinan He, Yizhuo Li, Yi Wang, Yi Liu, Zun Wang, Jilan Xu, Guo Chen, Ping Luo, Limin Wang, and Yu Qiao. Mvbench: A comprehensive multi-modal video understanding benchmark, 2024b. URL https://arxiv.org/abs/2311.17005.

Yifei Li, Junbo Niu, Ziyang Miao, Chunjiang Ge, Yuanhang Zhou, Qihao He, Xiaoyi Dong, Haodong Duan, Shuangrui Ding, Rui Qian, Pan Zhang, Yuhang Zang, Yuhang Cao, Conghui He, and Jiaqi Wang. Ovo-bench: How far is your video-llms from real-world online video understanding?, 2025. URL https://arxiv.org/abs/2501.05510.

Yuhong Li, Yingbing Huang, Bowen Yang, Bharat Venkitesh, Acyr Locatelli, Hanchen Ye, Tianle Cai, Patrick Lewis, and Deming Chen. Snapkv: Llm knows what you are looking for before generation, 2024c. URL https://arxiv.org/abs/2404.14469.

OpenAI. Gpt-4 technical report, 2024. URL https://arxiv.org/abs/2303.08774.

Bowen Peng, Jeffrey Quesnelle, Honglu Fan, and Enrico Shippole. Yarn: Efficient context window extension of large language models, 2023. URL https://arxiv.org/abs/2309.00071.

Rui Qian, Xiaoyi Dong, Pan Zhang, Yuhang Zang, Shuangrui Ding, Dahua Lin, and Jiaqi Wang. Streaming long video understanding with large language models, 2024. URL https://arxiv.org/abs/2405.16009.

Weihan Wang, Zehai He, Wenyi Hong, Yean Cheng, Xiaohan Zhang, Ji Qi, Xiaotao Gu, Shiyu Huang, Bin Xu, Yuxiao Dong, Ming Ding, and Jie Tang. Lvbench: An extreme long video understanding benchmark, 2025a. URL https://arxiv.org/abs/2406.08035.

Yi Wang, Kunchang Li, Xinhao Li, Jiashuo Yu, Yinan He, Chenting Wang, Guo Chen, Baoqi Pei, Ziang Yan, Rongkun Zheng, Jilan Xu, Zun Wang, Yansong Shi, Tianxiang Jiang, Songze Li, Hongjie Zhang, Yifei Huang, Yu Qiao, Yali Wang, and Limin Wang. Internvideo2: Scaling foundation models for multimodal video understanding, 2024. URL https://arxiv.org/abs/2403.15377.

Yi Wang, Xinhao Li, Ziang Yan, Yinan He, Jiashuo Yu, Xiangyu Zeng, Chenting Wang, Changlian Ma, Haian Huang, Jianfei Gao, Min Dou, Kai Chen, Wenhai Wang, Yu Qiao, Yali Wang, and Limin Wang. Internvideo2.5: Empowering video mlims with long and rich context modeling, 2025b. URL https://arxiv.org/abs/2501.12386.

Guangxuan Xiao, Yuandong Tian, Beidi Chen, Song Han, and Mike Lewis. Efficient streaming language models with attention sinks, 2024. URL https://arxiv.org/abs/2309.17453.

Zhenyu Zhang, Ying Sheng, Tianyi Zhou, Tianlong Chen, Lianmin Zheng, Ruisi Cai, Zhao Song, Yuandong Tian, Christopher Ré, Clark Barrett, Zhangyang Wang, and Beidi Chen.  $ H_{2}O $: Heavy-hitter oracle for efficient generative inference of large language models, 2023. URL https://arxiv.org/abs/2306.14048.

11

Published as a conference paper at ICLR 2026

### A APPENDIX

### A.1 LLM USAGE STATEMENT

We acknowledge the use of Large Language Models (specifically Claude and GPT-5) in the preparation of this manuscript. The LLMs were used exclusively as writing assistants to:

• Polish and refine the language for clarity and conciseness

• Improve grammar and sentence structure

• Suggest alternative phrasings for technical descriptions

- Help organize and structure sections for better flow

All research ideas, experimental design, theoretical derivations, and scientific contributions are entirely our own. The LLMs did not contribute to research ideation, hypothesis formulation, or any core scientific aspects of this work. We used LLMs in a manner similar to grammar-checking tools, but with more sophisticated language capabilities. All content, including any LLM-assisted text, has been carefully reviewed and verified by the authors. We take full responsibility for all contents of this paper, including their accuracy and originality.

### A.2 STABILITY OVER TIME

We split each video into five segments at 20% intervals and evaluate on the 2-hour test set. As shown in Figure 8, StreamingVLM does not degrade across later segments and reaches performance close to Sliding-Window w/ Overlap. This indicates that StreamingVLM maintains quality as videos grow and effectively supports unbounded inference.

<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Video Segment Range</th><th style='text-align: center;'>Full Attention</th><th style='text-align: center;'>Sliding Window (w/o Overlapping)</th><th style='text-align: center;'>Sliding Window (w/ Overlapping)</th><th style='text-align: center;'>StreamingVLM (Sliding Window+Reuse KV)</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>0%-20%</td><td style='text-align: center;'>15.2</td><td style='text-align: center;'>23.1</td><td style='text-align: center;'>68.5</td><td style='text-align: center;'>66.4</td></tr>
    <tr><td style='text-align: center;'>20%-40%</td><td style='text-align: center;'>3.1</td><td style='text-align: center;'>24.1</td><td style='text-align: center;'>65.7</td><td style='text-align: center;'>64.3</td></tr>
    <tr><td style='text-align: center;'>40%-60%</td><td style='text-align: center;'>1.1</td><td style='text-align: center;'>24.2</td><td style='text-align: center;'>65.4</td><td style='text-align: center;'>67.5</td></tr>
    <tr><td style='text-align: center;'>60%-80%</td><td style='text-align: center;'>0.0</td><td style='text-align: center;'>23.2</td><td style='text-align: center;'>66.7</td><td style='text-align: center;'>66.8</td></tr>
    <tr><td style='text-align: center;'>80%-100%</td><td style='text-align: center;'>0.0</td><td style='text-align: center;'>23.1</td><td style='text-align: center;'>66.5</td><td style='text-align: center;'>66.0</td></tr>
  </tbody>
</table>

<div style="text-align: center;">Figure 8: Stability over time. Each test video is split into five segments at 20% intervals. StreamingVLM (Sliding Window + Reuse KV) maintains nearly constant win rate across segments and matches the performance of Sliding Window w/ Overlap, while Full Attention and Sliding Window w/o Overlap degrade or remain far lower.</div>


<div style="text-align: center;">Table 8: Sensitivity analysis over Tsink on Inf-Stream-Eval.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>SFT  $ T_{sink} $</td><td style='text-align: center; word-wrap: break-word;'>Eval  $ T_{sink} $</td><td style='text-align: center; word-wrap: break-word;'>GPT-4o $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>Livecc $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>Livecc $ ^{\infty} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>64</td><td style='text-align: center; word-wrap: break-word;'>64</td><td style='text-align: center; word-wrap: break-word;'>72.04</td><td style='text-align: center; word-wrap: break-word;'>90.32</td><td style='text-align: center; word-wrap: break-word;'>99.46</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>128</td><td style='text-align: center; word-wrap: break-word;'>128</td><td style='text-align: center; word-wrap: break-word;'>73.65</td><td style='text-align: center; word-wrap: break-word;'>92.94</td><td style='text-align: center; word-wrap: break-word;'>99.47</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>256</td><td style='text-align: center; word-wrap: break-word;'>256</td><td style='text-align: center; word-wrap: break-word;'>73.73</td><td style='text-align: center; word-wrap: break-word;'>93.28</td><td style='text-align: center; word-wrap: break-word;'>99.38</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>1024</td><td style='text-align: center; word-wrap: break-word;'>1024</td><td style='text-align: center; word-wrap: break-word;'>74.82</td><td style='text-align: center; word-wrap: break-word;'>93.51</td><td style='text-align: center; word-wrap: break-word;'>99.53</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>512</td><td style='text-align: center; word-wrap: break-word;'>512</td><td style='text-align: center; word-wrap: break-word;'>73.64</td><td style='text-align: center; word-wrap: break-word;'>92.33</td><td style='text-align: center; word-wrap: break-word;'>99.38</td></tr></table>

12

Published as a conference paper at ICLR 2026

### A.3 SENSITIVITY ANALYSIS OF SINK TOKEN WINDOW SIZE

To address how finite token length limits impact model performance across varying scenarios, we conducted a sensitivity analysis on the attention-sink window size ( $ T_{sink} $). As discussed in the Limitations section, these window sizes serve as key hyperparameters.

Table 8 presents the ablation results for varying  $ T_{sink} $ sizes (64, 128, 256, 512, and 1024) during both Supervised Fine-Tuning (SFT) and Evaluation. The results demonstrate that the sink token size noticeably impacts the final performance. Generally, larger  $ T_{sink} $ capacities yield better win rates against GPT-4o and Livecc metrics, as the model retains more initial contextual tokens.

However, performance gains plateau at larger window sizes, indicating a trade-off between context retention and computational efficiency. This confirms that  $ T_{sink} $ should be carefully tuned based on the specific scenario's context length requirements.

### A.4 DEMO

We provide a demo video in the supplementary materials showing StreamingVLM's commentary after 100 minutes of continuous inference. The video is randomly selected and edited to remove long pauses and mid-length ads. As the base model is modest in size, occasional hallucinations may occur. Please see the supplementary materials for details.

13