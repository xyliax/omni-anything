arXiv:2504.16030v1 [cs.CV] 22 Apr 2025

# Live CC: Learning Video LLM with Streaming Speech Transcription at Scale

Joya Chen $ ^{1*} $ Ziyun Zeng $ ^{1*} $ Yiqi Lin $ ^{1*} $ Wei Li $ ^{2} $ Zejun Ma $ ^{2} $ Mike Zheng Shou $ ^{1✉} $

 $ ^{1} $Show Lab, National University of Singapore  $ ^{2} $ByteDance

<div style="text-align: center;"><img src="imgs/img_in_image_box_118_385_1104_793.jpg" alt="Image" width="80%" />

Hi LiveCC, could you commentate on this match in real time?
As a Video LLM trained with millions of streaming speech transcripts, I can provide play-by-play commentary.

Double-team defense by French.
They're going to have to get it up. Here's'
Curry. He's got to get a shot up.
Curry. Step back.
Three-pointer. Got it! Curry!

124s
125s
126s
127s
128s
Time

</div>


Figure 1. LiveCC provides real-time commentary for streaming video, emulating a human commentator. This example is drawn from the YouTube video (ID: I7pTpMjqNRM), featuring the Paris 2024 Olympics Men's Basketball Final between France and the USA. Our 7B model generates continuous commentary with a latency of less than 0.5 seconds per frame, supporting real-time applications at 2 FPS.

## Abstract

Recent video large language models (Video LLMs) often depend on costly human annotations or proprietary model APIs (e.g., GPT-4o) to produce training data, which limits their training at scale. In this paper, we explore large-scale training for Video LLM with cheap automatic speech recognition (ASR) transcripts. Specifically, we propose a novel streaming training approach that densely interleaves the ASR words and video frames according to their timestamps. Compared to previous studies in vision-language representation with ASR, our method naturally fits the streaming characteristics of ASR, thus enabling the model to learn temporally-aligned, fine-grained vision-language modeling. To support the training algorithm, we introduce a data production pipeline to process YouTube videos and their closed captions (CC, same as ASR), resulting in Live-CC-5M dataset for pretraining and Live-WhisperX-526K dataset for high-quality supervised fine-tuning (SFT). Remarkably, even

without SFT, the ASR-only pre-trained  $ \underline{\text{LiveCC-7B-Base}} $ model demonstrates competitive general video QA performance and exhibits a new capability in real-time video commentary. To evaluate this, we carefully design a new  $ \underline{\text{LiveSports-3K}} $ benchmark $ ^{1} $, using LLM-as-a-judge to measure the free-form commentary. Experiments show our final  $ \underline{\text{LiveCC-7B-Instruct}} $ model can surpass advanced 72B models (Qwen2.5-VL-72B-Instruct, LLaVA-Video-72B) in commentary quality even working in a real-time mode. Meanwhile, it achieves state-of-the-art results at the 7B/8B scale on popular video QA benchmarks such as VideoMME and OVOBench, demonstrating the broad generalizability of our approach. All resources of this paper have been released at  $ \underline{\text{showlab.github.io/livecc}} $.

## 1. Introduction

The success of large language models (LLMs) [3, 4, 22, 62, 63, 78, 79, 91] owes much to the large-scale auto-regressive

 $ ^{✉} $Corresponding Author.  $ ^{*} $Equal Contribution.

 $ ^{1} $Welcome to participate the real-time video commentary competition at CVPR25 workshop loveucvpr25/track2. Free GPT-4o judging provided.

1

language pre-training [8, 31, 36, 69, 70]. This inspires large multimodal models (LMMs) [5, 29, 54, 64, 112], which are initially only achieved by small-scale instruction tuning [54, 112], to increasingly emphasize data scaling during their training. While early large multimodal models (LMMs) such as LLaVA [54] were only supervised fine-tuned on 158K image QA samples, recent advanced approaches [16, 42, 50, 59, 105] have expanded the training data to millions of multimodal conversation samples, substantially benefiting from the increased data size.

A long-term ambition in this field is to develop LMMs akin to J.A.R.V.I.S., seamlessly assisting humans in real-life scenarios. Building on prior successes in LLMs/LMMs, a possible way is to collect extensive streaming video-text chat data. For instance, recordings of a basketball coach providing real-time feedback to a novice player could be great data for training. However, previous studies on streaming video LLMs [13, 24, 25, 55, 67, 68, 82, 83, 86, 98, 100, 111] have explored the difficulties of collecting and scaling up such data. They either rely on LLMs to generate “hallucinated” streaming conversations from video annotations, or fine-tune on small-scale dense caption datasets [32, 37, 110]. Neither approach is scalable enough to yield a truly powerful streaming video LLM.

To address these limitations, two primary approaches merit consideration. First, recent video-text datasets [14, 15, 81, 105] increasingly employ advanced LMMs, such as GPT-4o [29], for synthetic data generation. While effective, this approach is costly and risks violating usage terms. Another alternative leverages the inherent audio channel in videos by utilizing automatic speech recognition (ASR) transcriptions as textual data. Prior works [60, 88–90, 96] have explored large-scale video-ASR learning but typically treat ASR transcriptions as global video captions, overlooking their valuable temporal alignment. In practice, some ASR texts naturally synchronize with visual content, offering an untapped opportunity for video-language learning, especially for streaming applications.

In this work, we aim to scale video LLM training by ASR transcriptions. We propose a novel streaming training approach that densely interleaves ASR words with corresponding video frames, as illustrated in Figure 5. The model is trained to generate frame assigned ASR words in an autoregressive manner. This approach marks a significant departure from prior LMMs [5, 13, 54, 111, 112], which primarily learn from complete sentences or paragraphs. In contrast, our method simply learns the native short, incomplete ASR word sequences that are temporally aligned with video frames. This offers three key advantages: 1) it aligns naturally with the real-world data, making it readily applicable to video platforms like YouTube; 2) it enables the model to learn fine-grained temporal correlations between visual content and spoken language; and 3) during inference, it facilitates seamless streaming by generating only a few words per frame, ensuring extremely low latency.



To achieve this goal, we address three fundamental challenges: 1) How can video-ASR data be effectively curated and selected for training? 2) How should video-ASR streaming sequences be efficiently modeled? 3) How can streaming word generation—termed real-time video commentary—be rigorously evaluated? To tackle these challenges, we first design a data collection pipeline that integrates cost-effective techniques to enhance ASR quality and improve visual-text alignment, such as active speaker detection [47] for filtering low-quality talking-head videos. This pipeline enables the construction of the Live-CC-5M pretraining set and the Live-WhisperX-526K SFT set. Next, we incorporate our streaming pre-training approach into the Qwen2-VL-7B-Base [80] base model, yielding LiveCC-7B-Base, and investigate key factors influencing accurate ASR word prediction, such as leveraging video title and previous ASR as context to mitigate the learning ambiguity. Then, we introduce LiveSports-3K, a new benchmark that employs the LLM-as-a-judge [109] framework for evaluating real-time video commentary. We fine-tune LiveCC-7B on Live-WhisperX-526K and LLaVA-Video-178K [105] to obtain LiveCC-7B-Instruct, achieving state-of-the-art performance on general QA and streaming commentary tasks.

Extensive experiments demonstrate that our streaming pre-training approach on Live-CC-5M substantially enhances commentary quality and yields improvements in general video QA performance. By fine-tuning our pre-trained model using the Live-WhisperX-526K dataset in conjunction with LLaVA-Video-178K, our method achieves state-of-the-art results on popular video QA benchmarks such as Video-MME [23] and OVOBench [46], as well as our proposed LiveSports-3K benchmark, and delivers competitive performance on MVBench [45]. These results indicate that our comprehensive framework is not only for real-time video commentary but also beneficial to common video understanding capability.

## 2. Related Work

Large Multimodal Models. Early LMMs [2, 20, 43, 54, 112] achieve image dialogue by projecting the visual embedding (e.g., from CLIP [71, 97]) to align with LLM token embedding space. Then, lots of efforts explore more free-form interleaved vision-text chatting [3, 5, 40, 42, 50, 53, 64, 93], spatial/temporal grounding [12, 38, 52, 74, 80, 95, 104], video comprehension [24, 27, 29, 44, 48, 57, 75, 77, 90, 99, 106], etc. Our model is also an LMM, but it offers new insights into cost-effective and scalable ASR training data, as well as a new capability of real-time video commentary.

Training Video LLMs. Popular video LLMs [6, 16, 80, 98, 106] typically rely on human- or LLM-crafted video

2

<div style="text-align: center;"><img src="imgs/img_in_image_box_115_144_590_433.jpg" alt="Image" width="38%" />

1. Metadata Filtering
HD-VILA
YT-Temporal-1B
HD-Chapters
HowTo100M
LLaVA178K-2024
HD-VILA
30~60/240s clipping
Word-wise interspace < 35
1 < word speed < 4
Live30-240 Clips
B1.7 Categories
HowTo, So, Eslu, Auto Sports, Gaming, News
Live-WhisperX-526K
30~240 Clips
SFT Data
Live-WhisperX-526K Clips
SFT Dataset
Live30-60 Clips
Live-CC-1/2.5/5/10M 30~60s Clips
A2. Pure Text Filtering
Qwen2 v1.5bruic结
1.5 < Loss < 6.5
Live30-240 Clips
B2. Better ASR
WhisperX-large<3-turbo
300-240s clipping
300-240s clips
300-240s interspace < 35
1 < word speed < 4
Live30-240 Clips
Live30-5.7M
2. Video-level CC Filtering
10.7M IDs
Download CC
English detection>= 0.9
Word set length >= 30
English detection>= 0.9
5.7M IDs
Download Video&CC
A4. Pre-training Set
Live-CC-5M
30~240s Clips
Live30-5.7M
Pre-training Data Pipeline
A4. Pre-training Set
Live30-5.7M Clips
B4. Pure Text Filtering
Qwen2 v1.5bruic结
1.5 < loss < 5
Live30-240s Clips
Live30-5.7M Clips
Live30-5.7M Clips
86. Make Prompt
85. Remove Talking-head

</div>


<div style="text-align: center;">Figure 2. LiveCC data production pipeline. We begin by integrating several large-scale YouTube video datasets [60, 88, 89, 96, 105], followed by metadata filtering, resulting in a curated pool of 5.7M videos. Then, the pre-training dataset is built using the original YouTube CC, while the SFT dataset leverages higher-quality ASR transcriptions generated by WhisperX [7, 72]. We also introduce a set of efficient filtering techniques to improve the SFT data quality. Please refer to Section 3.1 for details.</div>


caption/QA sequences for training. In contrast, our work focuses on training less explored ASR transcription data, leveraging its scalability and automatic extraction capabilities. Several studies [51, 60, 88–90, 96] have investigated learning spatio-temporal representations through video-ASR pre-training. The most related work is Vid2Seq [90], which pre-trains a model to predict timestamped ASR paragraph for videos. However, its training paradigm still aligns with previous video captioning, aiming to predict an overall event. In contrast, our approach aligns with the streaming ASR, learning to predict short, incomplete ASR words per frame causally, thereby enabling more fine-grained spatial-temporal learning.

Streaming Video Understanding. Traditional video understanding benchmarks [1, 10, 11, 28, 30, 34, 39, 58, 85] allow models to access entire video frames before making predictions, a setting commonly referred to as “offline”. However, this paradigm does not align well with many real-time applications (e.g., AR glasses). Previous online video understanding tasks, such as online action detection [26, 107, 108], localization [9, 35, 76], and captioning [111], primarily focus on densely identifying current or future actions. Recent advancements in streaming video LLMs [13, 24, 25, 55, 67, 68, 82, 83, 98, 111] and benchmarks [33, 46, 49, 86] have introduced capabilities such as proactive response, long-form streaming, and interactive multimodal conversation. However, they heavily rely on manual or GPT crafted data, and will be “blind” for video input before the text/audio generation finished. Our work provides a comprehensive solution that leverages ASR data to enhance both general QA and streaming capabilities, and

<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Number of Videos</th><th style='text-align: center;'>Pre-N-Lows</th><th style='text-align: center;'>Basic N-Lows</th><th style='text-align: center;'>Enrichment</th><th style='text-align: center;'>Re-maxing</th><th style='text-align: center;'>Auto-No-Terminating</th><th style='text-align: center;'>Max-Enrichment</th><th style='text-align: center;'>Travel & Events</th><th style='text-align: center;'>Petb & Amend.</th><th style='text-align: center;'>Swarming</th><th style='text-align: center;'>Neapolis & Robotics</th><th style='text-align: center;'>Convexy</th><th style='text-align: center;'>Number of Words</th><th style='text-align: center;'>Words per Second</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>0-100</td><td style='text-align: center;'>1.55</td><td style='text-align: center;'>1.60</td><td style='text-align: center;'>0.95</td><td style='text-align: center;'>0.60</td><td style='text-align: center;'>0.35</td><td style='text-align: center;'>0.25</td><td style='text-align: center;'>0.15</td><td style='text-align: center;'>0.10</td><td style='text-align: center;'>0.05</td><td style='text-align: center;'>0.05</td><td style='text-align: center;'>0.85</td><td style='text-align: center;'>1.45</td><td style='text-align: center;'>1.2</td></tr>
    <tr><td style='text-align: center;'>100-200</td><td style='text-align: center;'>0.90</td><td style='text-align: center;'>0.95</td><td style='text-align: center;'>0.60</td><td style='text-align: center;'>0.40</td><td style='text-align: center;'>0.25</td><td style='text-align: center;'>0.20</td><td style='text-align: center;'>0.10</td><td style='text-align: center;'>0.05</td><td style='text-align: center;'>0.02</td><td style='text-align: center;'>0.02</td><td style='text-align: center;'>0.80</td><td style='text-align: center;'>0.50</td><td style='text-align: center;'>3.0</td></tr>
    <tr><td style='text-align: center;'>200-300</td><td style='text-align: center;'>0.60</td><td style='text-align: center;'>0.65</td><td style='text-align: center;'>0.40</td><td style='text-align: center;'>0.30</td><td style='text-align: center;'>0.20</td><td style='text-align: center;'>0.15</td><td style='text-align: center;'>0.05</td><td style='text-align: center;'>0.02</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.35</td><td style='text-align: center;'>0.35</td><td style='text-align: center;'>1.0</td></tr>
    <tr><td style='text-align: center;'>300-400</td><td style='text-align: center;'>0.40</td><td style='text-align: center;'>0.40</td><td style='text-align: center;'>0.30</td><td style='text-align: center;'>0.25</td><td style='text-align: center;'>0.15</td><td style='text-align: center;'>0.10</td><td style='text-align: center;'>0.02</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.35</td><td style='text-align: center;'>0.35</td><td style='text-align: center;'>1.0</td></tr>
    <tr><td style='text-align: center;'>400-500</td><td style='text-align: center;'>0.30</td><td style='text-align: center;'>0.30</td><td style='text-align: center;'>0.25</td><td style='text-align: center;'>0.20</td><td style='text-align: center;'>0.10</td><td style='text-align: center;'>0.05</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.35</td><td style='text-align: center;'>0.35</td><td style='text-align: center;'>1.0</td></tr>
    <tr><td style='text-align: center;'>500-600</td><td style='text-align: center;'>0.20</td><td style='text-align: center;'>0.20</td><td style='text-align: center;'>0.20</td><td style='text-align: center;'>0.15</td><td style='text-align: center;'>0.05</td><td style='text-align: center;'>0.02</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.25</td><td style='text-align: center;'>0.35</td><td style='text-align: center;'>1.0</td></tr>
    <tr><td style='text-align: center;'>600-700</td><td style='text-align: center;'>0.15</td><td style='text-align: center;'>0.15</td><td style='text-align: center;'>0.15</td><td style='text-align: center;'>0.10</td><td style='text-align: center;'>0.02</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.20</td><td style='text-align: center;'>0.35</td><td style='text-align: center;'>1.0</td></tr>
    <tr><td style='text-align: center;'>700-800</td><td style='text-align: center;'>0.10</td><td style='text-align: center;'>0.10</td><td style='text-align: center;'>0.10</td><td style='text-align: center;'>0.05</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.15</td><td style='text-align: center;'>0.15</td><td style='text-align: center;'>1.0</td></tr>
    <tr><td style='text-align: center;'>800-900</td><td style='text-align: center;'>0.05</td><td style='text-align: center;'>0.05</td><td style='text-align: center;'>0.05</td><td style='text-align: center;'>0.02</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.10</td><td style='text-align: center;'>0.05</td><td style='text-align: center;'>1.0</td></tr>
    <tr><td style='text-align: center;'>1000-1000</td><td style='text-align: center;'>0.02</td><td style='text-align: center;'>0.02</td><td style='text-align: center;'>0.02</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.01</td><td style='text-align: center;'>0.05</td><td style='text-align: center;'>0.02</td><td style='text-align: center;'>1.0</td></tr>
  </tbody>
</table>

<div style="text-align: center;">Figure 3. Overview of our proposed Live-CC-5M dataset.</div>


achieves novel real-time video commentary feature, along with a new benchmark LiveSports-3K-CC for evaluation.

## 3. Methodology

### 3.1. Video-ASR Data Curation

To demonstrate the scalability of our pre-training strategy, we aggregate four recent large-scale video datasets—HD-VILA [88], YT-Temporal-1B [96], VidChapters [89], and HowTo100M [60]—as our video sources. As illustrated in Figure 2, we begin by retrieving video metadata (e.g., title, duration, category) and the corresponding YouTube closed captions (CC) using the released video IDs. To ensure high visual quality, we retain only videos with a resolution of at least 480p. For storage efficiency, we filter videos to be between 30 seconds and 10 minutes in length. We further require the presence of both CC and title metadata. Additionally, we observe that English videos typically yield better ASR quality; therefore, we restrict our selection to English-language content. Applying these filtering criteria results in a curated set of 10.7 million YouTube video IDs.

YT-CC-Source-5.7M. We further observed that YouTube metadata often mislabels the language category, e.g., marking videos as English despite containing code-mixed content or garbled characters. To address this, we apply the XLM-RoBERTa [19] (papluca/xlm-roberta-base-language-detection) for English detection, using a confidence threshold of 0.9. In addition, we discard video IDs with sparse CC, e.g. music videos with only a few words. We require each video to contain at least 30 distinct words in its CC. Applying these filters, we download these 5.7 million videos with English CC, which serves as the source for both pre-training and SFT datasets.

YT-CC-Source-5.7M→Live-CC-5M. Upon inspection, we observed that YouTube CC is generally of low quality—lacking punctuation, case-insensitive, and frequently containing garbled characters. Nevertheless, due to their accessibility and low cost, they offer a scalable data source,

3

making them more suitable for pre-training rather than SFT.

Therefore, we design the following steps for data curation: A1) First, we segment the video based on ASR word timestamp gaps. If the gap between words exceeds 3 seconds, a new clip is generated. If a clip exceeds the maximum length, it is split into a new clip. Clips shorter than 30 seconds or with a speech rate outside the 1 to 4 words per second range are discarded. The extended range of silence or abnormal speech speed makes it hard for the model to learn the end-of-sequence (EOS) predictions. For pretraining, the default maximum clip length is set to 240 seconds. For ablation studies, the clip length is set to 60 seconds for training efficiency. We rank these clips by their word set size, which reflects content informativeness, and create pre-training subsets with 1M, 2.5M, 5M, and 10M clips. A2) We compute the pure text loss of ASR transcripts by language model to assess their dependency on visual content. A very low perplexity suggests the transcript is self-contained and does not require visual grounding, while a very high perplexity often correlates with poor ASR quality. Empirically, we use Qwen2-1.5B-Instruct [91] to retain samples with loss values in the range of 1.5 to 6.5; A3) To remove videos with people consistently facing the camera and talking without meaningful visual information, we apply visual filtering using Qwen-VL-2B-Instruct [80]. For each video, we use 8 uniformly sampled frames to detect persistent face-speaking content by prompting Qwen-VL-2B-Instruct. We keep the videos if the model's confidence in detecting the talking head is below a threshold of 0.3.

Finally, we obtain Live-CC-5M for pretraining. Figure 3 shows the statistics of these data samples.

YT-CC-Source-5.7M→Live-WhisperX-526K. As the low-quality YouTube CC makes them unsuitable for SFT data, we further perform the following steps to obtain high-quality, visually grounded ASR transcription: B1) We only maintain 7 YouTube categories shown in Figure 4a but filter out “People & Blogs” and “Film & Animation”, as their ASR content typically lacks correspondence with the visual events; B2) We employ WhisperX [7, 72] (large-v3-turbo) to generate more accurate, word-level aligned ASR transcriptions; B3) Similar to Step A1, the maximum clip length is 240 seconds. For pretraining, since pre-ASR provides context, clips can be split in the middle of sentences. However, during the instruction fine-tuning stage, where no pre-ASR context is available, we ensure that each clip begins at the start of a sentence. Specifically, the last ASR word must be a period, question mark, or exclamation mark, and the current clip must start with a capital letter; B4) The same as Step A2, while the range of text perplexity is 1.5 to 5; B5) Despite the above filtering steps like Step A3, we observe that many remaining videos are dominated by talking-head content, which is often useless for training real-time video

<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Category</th><th style='text-align: center;'>Number of Videos</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>Howto & Style</td><td style='text-align: center;'>168541</td></tr>
    <tr><td style='text-align: center;'>Science & Technology</td><td style='text-align: center;'>82157</td></tr>
    <tr><td style='text-align: center;'>Education</td><td style='text-align: center;'>80993</td></tr>
    <tr><td style='text-align: center;'>Autos & Vehicles</td><td style='text-align: center;'>76645</td></tr>
    <tr><td style='text-align: center;'>Sports</td><td style='text-align: center;'>73968</td></tr>
    <tr><td style='text-align: center;'>Gaming</td><td style='text-align: center;'>31801</td></tr>
    <tr><td style='text-align: center;'>News & Politics</td><td style='text-align: center;'>11836</td></tr>
  </tbody>
</table>

<div style="text-align: center;">(a) Statistics of our proposed Live-WhisperX-526K dataset.</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_635_454_1106_613.jpg" alt="Image" width="38%" />

Remove ASD (e.g. Talking-head) Clips
System gets out of whack like there's too much stimulus on one side or there's
Maintain non-ASD Clips
because we did have to face sc in the semifinal game so

</div>


<div style="text-align: center;">(b) An example of ASD removal in SFT data pipeline.</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_633_645_1107_774.jpg" alt="Image" width="38%" />



</div>


Prompt: Can you provide a step-by-step guide on how to create a special visual effect using Photoshop? Video Stream Text Stream:_[27.0s-27.2s, "link", [27.2s-27.4s, "it"], [27.4s-27.9s, "in"], [27.9s-28.0s, "the"], [28.0s-28.4s, "description"], [28.4s-29.0s, "and"], [29.0s-29.1s, "i've"], [29.1s-29.3s, "also"], [29.3s-29.4s, "got"], [29.4s-29.6s, "an"], [29.6s-29.9s, "ice"], [29.9s-30.2s, "image"].

<div style="text-align: center;">(c) An example from the Live-WhisperX-526K dataset.</div>


<div style="text-align: center;">Figure 4. Overview of the Live-WhisperX-526K dataset.</div>


commentary. To address this, we employ active speaker detection (ASD) [47] to identify and exclude such videos. For efficiency, we optimize Light-ASD [47] pipeline in face detection, tracking, and multiprocessing, achieving a  $ 250\times $ speed-up. As a result, processing a 5-minute video now takes only 1–1.5 seconds. An ASD removal example is in Figure 4b. B6) Since these ASR transcripts lack associated user prompts, we employ GPT-4o [29] to generate a prompt for each sample. The prompts are crafted to match the style and intent of the speech transcription without revealing specific content. With this prompt, we no longer need pre-ASR applied during SFT.

Finally, we get a high-quality SFT dataset comprising 526K video clips, each paired with word-level timestamped ASR transcripts and a user prompt. Figure 4c shows an example in Live-WhisperX-526K dataset.

### 3.2. Modeling

Training with Dense Interleaving Sequence. As shown in Figure 5, our model architecture builds upon Qwen2-VL [80], which integrates a Vision Transformer [21] with basic dynamic resolution support and uses Qwen2 [91] as

4

<div style="text-align: center;"><img src="imgs/img_in_image_box_117_143_1103_454.jpg" alt="Image" width="80%" />

Time
00:17
00:18
00:19
00:20
You Tube CC
oh what a nice pass ...</e>
and a flip by willie ...</e>
cawley stein ...</e>
he's not gonna miss ...</e>
Visual Encoder
Previous ASR as Context
2 FPS Visual Tokens
Text Tokens
2 FPS Visual Tokens
Text Tokens
2 FPS Visual Tokens
Text Tokens
2 FPS Visual Tokens
Text Tokens
2 FPS Visual Tokens
Text Tokens
2 FPS Visual Tokens
Pre-trained LLM

</div>


<div style="text-align: center;">Figure 5. Modeling Overview of LiveCC. The model processes streaming video frames through a visual encoder to produce visual tokens while assigning ASR text from corresponding frame intervals as text tokens. The LLM autoregressively predicts text tokens within this densely interleaved token sequence. To mitigate learning ambiguity, additional context of preceding ASR text or video title is provided during pre-training. During SFT, the context part is only user query to match the real-world applications.</div>


the LLM backbone. We adopt the base version of Qwen2-VL, which is pretrained extensively on image-text data but has limited exposure to video-text pairs. Following standard practice [54], the model is trained to autoregressively predict text tokens while treating visual tokens as nonpredictive inputs, as illustrated in Figure 5. Unlike existing approaches that use either captioning [54] or image-text interleaving [50] style input, we propose to densely interleave ASR words with video frames along the temporal dimension. The training sequence is formatted as,

 $$ \begin{aligned}&[Con]<\mathrm{F}_{t:t+k}><\mathrm{W}_{t:t+k}><\mathrm{F}_{t+k:t+2k}><\mathrm{W}_{t+k:t+2k}>\\&\quad\cdot\cdot\cdot<\mathrm{F}_{t+n*k:t+(n+1)*k}><\mathrm{W}_{t+n*k:t+(n+1)*k}>,\\ \end{aligned} $$ 

where [Con] denotes context information of the video (e.g., prompt, previous ASR, video title), <F> denotes a frame, <W> denotes the words, t represents the time index and k represents the time intervals. By default, we use 2 FPS frame rate and k = 1 as the time interval. We incorporate video titles and preceding ASR text as contextual information to enhance text coherence, since ASR text may start from the middle of a sentence, or use informal, verbal language. A newline character concatenates the video title and previous ASR texts if the ASR texts are available.

Sequence Pre-processing. For pre-training, we utilize the original YouTube ASR transcripts, which employ fixed timestamps to segment speech into chunks of approximately 2 to 3 seconds. To approximate word-level alignment, we uniformly distribute each segment's duration across its constituent words. This heuristic yields reasonably accurate word-level timestamps across the entire video. In contrast, during SFT, we leverage WhisperX, which provides precise word-level timestamps, as detailed in Section 3.1. To disambiguate the true end-of-sequence (EOS) from temporary pauses in streaming, we simply use the ellipsis token (“…”) as an special EOS indicator appended to the per-frame text tokens. For silent frames without corresponding subtitles, we directly predict this ellipsis token.



Training Strategy. Our model training incorporates two stages including pre-training and SFT. For the pre-training, we solely train the model with dense interleaving sequences. The objective is to align frame features with the temporally synchronized ASR words, enabling the model to capture temporal correlations between frames and language. Next, to improve the ability of LiveCC models to solve a diverse set of downstream tasks, we jointly train the model with our Live-WhisperX-526K in streaming mode, general video and image datasets [105] for common caption or QA. To achieve this, we make the streaming training be compatible with the Qwen2-VL [80] conversation template. The details can be found in the supplementary material.

Inference. During inference, our LiveCC model processes input frames sequentially. To accelerate language decoding, we cache the Key-Value (KV) pairs of previous prompts, visual frames, and generated text. For long sequences, we discard visual tokens every 240 seconds—consistent with the maximum duration in SFT training—while retaining the text tokens to prefill the model again.

## 4. The LiveSports-3K Benchmark

### 4.1. LiveSports-3K Data Collection

As mentioned in Section 2, we present LiveSports-3K, a comprehensive benchmark designed for systematic evaluation of video understanding models' capabilities. Unlike previous sports benchmarks like SoccerNet [61] and MatchTime [73], which focus on specific sports, our benchmark spans a broader range of common sports to ensure generalizability. To achieve this, we prompt GPT-4o

5

<div style="text-align: center;"><img src="imgs/img_in_image_box_127_139_1096_522.jpg" alt="Image" width="79%" />

(a) Category Distribution of the LIVESPORTS Benchark

(b) Event Duration and ASR Word Count in LIVESPORTS-CC

(c) Question Count by Type in LIVESPORTS-OA

Class: Archery

Timeline

LIVESPORTS-CC

Context ASR Closed Caption (8.58s-13.94s):
We are not like the able-bodied game because we are not so convenient to rolling.
Groundtruth ASR Closed Caption (14.40s-23.78s):
So we will stay on the line, just give him the signal to the judge, and then the next one.
Model A Prediction:
That red hat guy is ready. He finished, now it's the next one's turn.
Model B Prediction:
That man with a red hat is shooting. Then he raised his hands.
LIVESPORTS-QA

Query Who, Given When and What:
Who is shooting when the player No.34B is waiting? [Options A, B, C, D] Answer: A. The man wearing a red hat.
Query When, Given Who and What:
When did the man wearing a red hat raise his hands? [Options A, B, C, D] Answer: C. After he finished shooting.
Query What, Given Who and When:
What did the man wearing a red hat do after he finished shooting? [Options A, B, C, D] Answer: D. Raise hands.

(d) Sample Closed Captions in LIVESPORTS-CC and Three Query Types in LIVESPORTS-QA

</div>


<div style="text-align: center;">Figure 6. (a) Category Distribution of the LiveSports Benchmark: The benchmark includes 3k live CCs and MCQs, split into two tracks: CC and QA. (b) Event Duration and ASR Word Count in the CC track: For CC, event duration (left y-axis) and ASR word count (right y-axis) are analyzed, with durations categorized as short, medium, and long. (c) Question Count by Type in the QA track: Questions are grouped into three query types, with additional tracking of those requiring OCR for each type. (d) Sample CCs and Query Types.</div>


mini [29] to select the ongoing sports videos and classify sports categories of our Live-WhisperX-526K dataset. We focused on the top 50 most frequent sports categories and randomly sampled 12 videos from each category, yielding a pool of 600 candidate videos covering popular sports. After collecting candidate videos, we used GPT-4o-mini to merge ASR transcriptions into semantically coherent events, recording each event's start and end timestamps. Given that ASR transcriptions are not always visually relevant, we recruited English-proficient annotators to filter out irrelevant events according to three criteria: 1) The event must last more than 10 seconds; 2) The event clip must contain ongoing sports action; 3) Most ASR transcriptions within the event clip should be visually grounded. Events that failed to meet any of these criteria were discarded. We curated 416 videos across 49 sports categories (one category lack of qualified videos). The category distribution is shown in Figure 6(a). We further remove these videos from our training dataset for fair evaluation.

### 4.2. Crafting LiveSports-3K-CC/QA

LiveSports-3K-CC. Real-time commentary in sports videos encapsulates rich spatiotemporal semantics. For instance, the commentary on a football game often describes attackers, defenders, and their interactions in detail, making it an ideal source for streaming video understanding evaluations. Therefore, we developed this track to assess video comprehension by evaluating the alignment between model-generated and groundtruth CCs from ASR. Note that the data collection process has ensured that the ASR event transcriptions are visually grounded. Thus, we directly leverage ASR transcriptions from qualified events as groundtruth. In summary, LiveSports-3K-CC consists of 1,702 events with high-quality live CCs. Figure 6(b) presents the distribution of events and word counts in three duration groups, showing a relatively balanced total word count (i.e., video count × word count per group) across groups. Additionally, Figure 6(d) illustrates a sample event, demonstrating the highly visual-grounded nature of the ASR-transcribed CCs retained through our filtering criteria.



For evaluation, we prompt the model with the video title and the preceding CCs of the event, then record the model's predictions. Given the challenges of directly assessing discrepancies between the predicted and groundtruth CCs, we adopt a pairwise comparison approach inspired by Chatbot Arena [109]. Specifically, for each pair of predictions, we use GPT-4o as a judge to select the better prediction based on the ground-truth CCs. The selection criteria include both stylistic and semantic consistency. The winning rates of different models serve as the ranking metric.

LiveSports-3K-QA. LiveSports-3K-CC offers a valuable track for assessing video understanding comprehensively. However, it still lacks a precise criterion for analyzing model behavior, especially when errors occur. To address this, we decompose each event into three fundamental elements: (i) When: Captures the temporal context of the event. (ii) What: Defines the content or action taking place in the event. (iii) Who: Identifies the participants involved in the event. By structuring events around these elements, we enable targeted queries for each element based on the other two, allowing us to isolate specific areas of weak-

6


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Video-ASR Sequence</td><td style='text-align: center; word-wrap: break-word;'>LiveSports-3K-CC\nWin Rate $ \uparrow $</td><td style='text-align: center; word-wrap: break-word;'>Video-MME\nOverall $ \uparrow $</td><td style='text-align: center; word-wrap: break-word;'>Short $ \uparrow $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Caption (5M)</td><td style='text-align: center; word-wrap: break-word;'>14.0</td><td style='text-align: center; word-wrap: break-word;'>61.1</td><td style='text-align: center; word-wrap: break-word;'>69.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Streaming (5M)</td><td style='text-align: center; word-wrap: break-word;'>32.9</td><td style='text-align: center; word-wrap: break-word;'>61.0</td><td style='text-align: center; word-wrap: break-word;'>70.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Caption+Streaming (5M $ \times $2)</td><td style='text-align: center; word-wrap: break-word;'>35.1</td><td style='text-align: center; word-wrap: break-word;'>60.5</td><td style='text-align: center; word-wrap: break-word;'>69.0</td></tr></table>


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Context</td><td style='text-align: center; word-wrap: break-word;'>LiveSports-3K-CC\nWin Rate $ \uparrow $</td><td style='text-align: center; word-wrap: break-word;'>Video-MME\nOverall $ \uparrow $</td><td style='text-align: center; word-wrap: break-word;'>Short $ \uparrow $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>None</td><td style='text-align: center; word-wrap: break-word;'>14.7</td><td style='text-align: center; word-wrap: break-word;'>60.7</td><td style='text-align: center; word-wrap: break-word;'>69.0</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Title</td><td style='text-align: center; word-wrap: break-word;'>24.8</td><td style='text-align: center; word-wrap: break-word;'>59.7</td><td style='text-align: center; word-wrap: break-word;'>67.9</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Prev. ASR</td><td style='text-align: center; word-wrap: break-word;'>32.0</td><td style='text-align: center; word-wrap: break-word;'>61.1</td><td style='text-align: center; word-wrap: break-word;'>69.7</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Title &amp; Prev. ASR</td><td style='text-align: center; word-wrap: break-word;'>33.8</td><td style='text-align: center; word-wrap: break-word;'>60.7</td><td style='text-align: center; word-wrap: break-word;'>69.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Title || Prev. ASR</td><td style='text-align: center; word-wrap: break-word;'>32.9</td><td style='text-align: center; word-wrap: break-word;'>61.0</td><td style='text-align: center; word-wrap: break-word;'>70.1</td></tr></table>


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Data</td><td style='text-align: center; word-wrap: break-word;'>LiveSports-3K-CC Win Rate $ \uparrow $</td><td style='text-align: center; word-wrap: break-word;'>Video-MME Overall $ \uparrow $</td><td style='text-align: center; word-wrap: break-word;'>Short $ \uparrow $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>1M</td><td style='text-align: center; word-wrap: break-word;'>29.1</td><td style='text-align: center; word-wrap: break-word;'>60.6</td><td style='text-align: center; word-wrap: break-word;'>68.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>2.5M</td><td style='text-align: center; word-wrap: break-word;'>30.8</td><td style='text-align: center; word-wrap: break-word;'>60.9</td><td style='text-align: center; word-wrap: break-word;'>69.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>5M</td><td style='text-align: center; word-wrap: break-word;'>32.9</td><td style='text-align: center; word-wrap: break-word;'>61.0</td><td style='text-align: center; word-wrap: break-word;'>70.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>10M</td><td style='text-align: center; word-wrap: break-word;'>36.0</td><td style='text-align: center; word-wrap: break-word;'>58.0</td><td style='text-align: center; word-wrap: break-word;'>67.6</td></tr></table>

<div style="text-align: center;">(a) Training Paradigm during Pre-training.</div>


<div style="text-align: center;">(b) Context during Pre-training.</div>


<div style="text-align: center;">(c) Pre-training Scalability.</div>


<div style="text-align: center;">Table 1. Ablation Study in the Pre-training Stage. Blue highlights our default setting. Win Rate indicates the percentage of wins against GPT-4o-08-06-generated commentary, using ground-truth ASR as the reference. Models in these tables are pre-trained on a maximum of 120 frames (60 seconds at 2 FPS), so we did not show results on medium- and long- length videos for Video-MME [23] to avoid misjudgment. (a) Both caption-style and streaming-style sequence significantly improve QA performance; however, only the streaming-style sequence yields notable gains in commentary generation. (b) Incorporating previous ASR enhances both commentary and QA. In contrast, simply adding video titles degrades QA, unless previous ASR is absent (e.g., during 0–60s). (c) Commentary benefits from increased pre-training data, while QA performance declines beyond 5M examples—likely due to overtraining on the single-source (streaming ASR) data.</div>


ness that require improvement. Figure 6(c) provides detailed examples of these three question types. Additionally, we recorded whether a question required OCR capabilities, allowing for an auxiliary evaluation of model performance on text recognition tasks. This process yielded 1,236 four-option MCQs across 414 videos, excluding two videos due to the difficulty of designing appropriate questions. Finally, we manually removed 62 questions that require speech recognition, leaving the remaining 1,174 MCQs as the final benchmark. This track includes a balanced distribution of the three query types, with OCR-reliant questions evenly distributed among them, as shown in Figure 6(b).

## 5. Experiments

### 5.1. Experiments Setup

Implementation Details. We initialize our model with the Qwen2-VL-7B-Base checkpoint [80], following most of the configurations provided in its HuggingFace release, with minimal modifications to improve efficiency. Specifically, during ablation studies of pre-training, we reduce the maximum number of frames from 768 to 120 and shorten the visual context length from 128K to 16K tokens. During formal pre-training and SFT, we increase the frame limit to 480 and extend the visual context length to 24K, while slightly lowering the minimum spatial resolution from  $ 128 \times 28 \times 28 $ to  $ 100 \times 28 \times 28 $. Pre-training ablation studies are conducted on the 30~60s Live-CC-1~10M dataset. The formal pre-training is in 30~240s Live-CC-5M. The SFT stages use our Live-Whisper-526K and LLaVA-Video-178K [105] datasets (without the training set of ActivityNetQA [30], Next-QA [85], and PerceptionTest [66]). We implement the training engine using PyTorch [65] and Transformers [84]. The batch size for pretraining and SFT is 512 on 128 GPUs, with a learning rate of 2e-5 for pre-training and 1e-5 for SFT.

Evaluation Protocols and Metrics. For QA benchmarks, we evaluate our models on VideoMME [23], MVBench [45], OVOBench [46], and our newly introduced LiveSports-3K-QA. For all models, we calculate the logits of multiple choices to select answers, due to the instruction following capability of streaming ASR pre-trained model has been lost. We observe this does not make difference with generation-based method [101] for SFT models, but the evaluation is much faster.



The evaluation on LiveSports-3K-CC is like a conditioned video captioning task, where the condition comprises the video title and previous ASR text. With this condition, the model's task is to complete the ASR text based on the given video clip. Since the most video LLMs lack real-time streaming capabilities, we evaluate them using a general video captioning approach, processing all video clip frames at once. In contrast, our model supports real-time inference, enabling us to generate captions on a frame-by-frame basis and then concatenate them into a complete response for evaluation. Due to the challenges of directly assessing open-ended text generation, we employ a pairwise competition approach, similar to Chatbot Arena [109]. We use GPT-4o [29] as the fixed competition opponent. In each competition (tested model vs. GPT-4o), we also use GPT-4o [29] acts as the judge, selecting the response that best aligns both stylistically and semantically with the ground truth ASR transcriptions. The evaluation metric is the win rate, which is defined as the proportion of times the judge favors our model over the baseline. The evaluation also involves latency comparison, which we discuss in the supplementary material.

### 5.2. Ablation Study

Pre-training Paradigm. We first investigate the impact of different pre-training paradigms on model performance using the following baselines: (1) Caption, where all ASR text is concatenated and appended after the visual input frames; (2) Streaming, where the model is trained on sequential frame inputs sampled at 2 FPS, predicting ASR text incrementally after receiving every 2 frames; and (3) Caption+Streaming, where each training sample contributes to both captioning and streaming objectives. As shown in

7


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="3">Pre-training</td><td rowspan="3">SFT</td><td colspan="6">LiveSports-3K</td><td colspan="14">VideoMME</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td rowspan="2">CC</td><td rowspan="2">QA</td><td rowspan="2">OCR</td><td rowspan="2">Who</td><td rowspan="2">When</td><td rowspan="2">What</td><td rowspan="2">All</td><td colspan="3">Duration</td><td colspan="3">Perception</td><td colspan="2">Recognition</td><td colspan="3">Reasoning</td><td style='text-align: center; word-wrap: break-word;'>OCR</td><td rowspan="2">Count</td><td rowspan="2">IS</td><td rowspan="2"></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>S</td><td style='text-align: center; word-wrap: break-word;'>M</td><td style='text-align: center; word-wrap: break-word;'>L</td><td style='text-align: center; word-wrap: break-word;'>Te</td><td style='text-align: center; word-wrap: break-word;'>Sp</td><td style='text-align: center; word-wrap: break-word;'>At</td><td style='text-align: center; word-wrap: break-word;'>Ac</td><td style='text-align: center; word-wrap: break-word;'>Ob</td><td style='text-align: center; word-wrap: break-word;'>Te</td><td style='text-align: center; word-wrap: break-word;'>Sp</td><td style='text-align: center; word-wrap: break-word;'>Ac</td><td style='text-align: center; word-wrap: break-word;'>Ob</td></tr><tr><td rowspan="2">Qwen2-VL-7B-Base</td><td style='text-align: center; word-wrap: break-word;'>LV178K</td><td style='text-align: center; word-wrap: break-word;'>16.7</td><td style='text-align: center; word-wrap: break-word;'>67.0</td><td style='text-align: center; word-wrap: break-word;'>66.1</td><td style='text-align: center; word-wrap: break-word;'>70.6</td><td style='text-align: center; word-wrap: break-word;'>57.6</td><td style='text-align: center; word-wrap: break-word;'>71.0</td><td style='text-align: center; word-wrap: break-word;'>62.7</td><td style='text-align: center; word-wrap: break-word;'>74.7</td><td style='text-align: center; word-wrap: break-word;'>62.4</td><td style='text-align: center; word-wrap: break-word;'>51.1</td><td style='text-align: center; word-wrap: break-word;'>74.5</td><td style='text-align: center; word-wrap: break-word;'>61.1</td><td style='text-align: center; word-wrap: break-word;'>73.4</td><td style='text-align: center; word-wrap: break-word;'>64.5</td><td style='text-align: center; word-wrap: break-word;'>70.1</td><td style='text-align: center; word-wrap: break-word;'>49.7</td><td style='text-align: center; word-wrap: break-word;'>80.4</td><td style='text-align: center; word-wrap: break-word;'>49.8</td><td style='text-align: center; word-wrap: break-word;'>57.0</td><td style='text-align: center; word-wrap: break-word;'>76.3</td><td style='text-align: center; word-wrap: break-word;'>45.1</td><td style='text-align: center; word-wrap: break-word;'>76.2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LV178K+Live526K</td><td style='text-align: center; word-wrap: break-word;'>33.7</td><td style='text-align: center; word-wrap: break-word;'>67.1</td><td style='text-align: center; word-wrap: break-word;'>66.8</td><td style='text-align: center; word-wrap: break-word;'>69.8</td><td style='text-align: center; word-wrap: break-word;'>57.0</td><td style='text-align: center; word-wrap: break-word;'>72.3</td><td style='text-align: center; word-wrap: break-word;'>63.6</td><td style='text-align: center; word-wrap: break-word;'>74.4</td><td style='text-align: center; word-wrap: break-word;'>63.1</td><td style='text-align: center; word-wrap: break-word;'>53.2</td><td style='text-align: center; word-wrap: break-word;'>74.5</td><td style='text-align: center; word-wrap: break-word;'>57.4</td><td style='text-align: center; word-wrap: break-word;'>75.2</td><td style='text-align: center; word-wrap: break-word;'>66.5</td><td style='text-align: center; word-wrap: break-word;'>70.1</td><td style='text-align: center; word-wrap: break-word;'>49.7</td><td style='text-align: center; word-wrap: break-word;'>76.8</td><td style='text-align: center; word-wrap: break-word;'>54.4</td><td style='text-align: center; word-wrap: break-word;'>57.5</td><td style='text-align: center; word-wrap: break-word;'>72.7</td><td style='text-align: center; word-wrap: break-word;'>44.4</td><td style='text-align: center; word-wrap: break-word;'>78.9</td></tr></table>

<div style="text-align: center;">(a) Ablation study in the SFT data.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="3">Pre-training</td><td rowspan="3">SFT</td><td colspan="6">LiveSports-3K</td><td colspan="16">VideoMME</td></tr><tr><td rowspan="2">CC</td><td rowspan="2">QA</td><td rowspan="2">OCR</td><td rowspan="2">Who</td><td rowspan="2">When</td><td rowspan="2">What</td><td rowspan="2">All</td><td colspan="3">Duration</td><td colspan="3">Perception</td><td colspan="3">Recognition</td><td colspan="3">Reasoning</td><td rowspan="2">OCR</td><td rowspan="2">Count</td><td rowspan="2">IS</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>S</td><td style='text-align: center; word-wrap: break-word;'>M</td><td style='text-align: center; word-wrap: break-word;'>L</td><td style='text-align: center; word-wrap: break-word;'>Te</td><td style='text-align: center; word-wrap: break-word;'>Sp</td><td style='text-align: center; word-wrap: break-word;'>At</td><td style='text-align: center; word-wrap: break-word;'>Ac</td><td style='text-align: center; word-wrap: break-word;'>Ob</td><td style='text-align: center; word-wrap: break-word;'>Te</td><td style='text-align: center; word-wrap: break-word;'>Sp</td><td style='text-align: center; word-wrap: break-word;'>Ac</td><td style='text-align: center; word-wrap: break-word;'>Ob</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Owen2-VL-7B-Base</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>16.3</td><td style='text-align: center; word-wrap: break-word;'>64.0</td><td style='text-align: center; word-wrap: break-word;'>64.8</td><td style='text-align: center; word-wrap: break-word;'>65.2</td><td style='text-align: center; word-wrap: break-word;'>57.9</td><td style='text-align: center; word-wrap: break-word;'>67.3</td><td style='text-align: center; word-wrap: break-word;'>63.4</td><td style='text-align: center; word-wrap: break-word;'>73.2</td><td style='text-align: center; word-wrap: break-word;'>63.2</td><td style='text-align: center; word-wrap: break-word;'>53.9</td><td style='text-align: center; word-wrap: break-word;'>72.7</td><td style='text-align: center; word-wrap: break-word;'>63.0</td><td style='text-align: center; word-wrap: break-word;'>76.1</td><td style='text-align: center; word-wrap: break-word;'>63.9</td><td style='text-align: center; word-wrap: break-word;'>67.2</td><td style='text-align: center; word-wrap: break-word;'>44.6</td><td style='text-align: center; word-wrap: break-word;'>78.6</td><td style='text-align: center; word-wrap: break-word;'>57.5</td><td style='text-align: center; word-wrap: break-word;'>61.5</td><td style='text-align: center; word-wrap: break-word;'>72.7</td><td style='text-align: center; word-wrap: break-word;'>39.6</td><td style='text-align: center; word-wrap: break-word;'>80.2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LiveCC-7B-Base</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>43.2</td><td style='text-align: center; word-wrap: break-word;'>57.9</td><td style='text-align: center; word-wrap: break-word;'>61.4</td><td style='text-align: center; word-wrap: break-word;'>59.4</td><td style='text-align: center; word-wrap: break-word;'>50.7</td><td style='text-align: center; word-wrap: break-word;'>61.9</td><td style='text-align: center; word-wrap: break-word;'>61.4</td><td style='text-align: center; word-wrap: break-word;'>68.1</td><td style='text-align: center; word-wrap: break-word;'>58.9</td><td style='text-align: center; word-wrap: break-word;'>57.3</td><td style='text-align: center; word-wrap: break-word;'>65.5</td><td style='text-align: center; word-wrap: break-word;'>63.0</td><td style='text-align: center; word-wrap: break-word;'>64.9</td><td style='text-align: center; word-wrap: break-word;'>60.7</td><td style='text-align: center; word-wrap: break-word;'>61.0</td><td style='text-align: center; word-wrap: break-word;'>50.3</td><td style='text-align: center; word-wrap: break-word;'>80.4</td><td style='text-align: center; word-wrap: break-word;'>56.1</td><td style='text-align: center; word-wrap: break-word;'>61.5</td><td style='text-align: center; word-wrap: break-word;'>61.2</td><td style='text-align: center; word-wrap: break-word;'>42.9</td><td style='text-align: center; word-wrap: break-word;'>82.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Owen2-VL-7B-Base</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>LV178K+Live526K</td><td style='text-align: center; word-wrap: break-word;'>33.7</td><td style='text-align: center; word-wrap: break-word;'>67.1</td><td style='text-align: center; word-wrap: break-word;'>66.8</td><td style='text-align: center; word-wrap: break-word;'>69.8</td><td style='text-align: center; word-wrap: break-word;'>57.0</td><td style='text-align: center; word-wrap: break-word;'>72.3</td><td style='text-align: center; word-wrap: break-word;'>63.6</td><td style='text-align: center; word-wrap: break-word;'>74.4</td><td style='text-align: center; word-wrap: break-word;'>63.1</td><td style='text-align: center; word-wrap: break-word;'>53.2</td><td style='text-align: center; word-wrap: break-word;'>74.5</td><td style='text-align: center; word-wrap: break-word;'>57.4</td><td style='text-align: center; word-wrap: break-word;'>75.2</td><td style='text-align: center; word-wrap: break-word;'>66.5</td><td style='text-align: center; word-wrap: break-word;'>70.1</td><td style='text-align: center; word-wrap: break-word;'>49.7</td><td style='text-align: center; word-wrap: break-word;'>76.8</td><td style='text-align: center; word-wrap: break-word;'>54.4</td><td style='text-align: center; word-wrap: break-word;'>57.5</td><td style='text-align: center; word-wrap: break-word;'>72.7</td><td style='text-align: center; word-wrap: break-word;'>44.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LiveCC-7B-Base</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>LV178K+Live526K</td><td style='text-align: center; word-wrap: break-word;'>41.5</td><td style='text-align: center; word-wrap: break-word;'>66.8</td><td style='text-align: center; word-wrap: break-word;'>66.4</td><td style='text-align: center; word-wrap: break-word;'>71.4</td><td style='text-align: center; word-wrap: break-word;'>56.1</td><td style='text-align: center; word-wrap: break-word;'>70.8</td><td style='text-align: center; word-wrap: break-word;'>64.1</td><td style='text-align: center; word-wrap: break-word;'>74.8</td><td style='text-align: center; word-wrap: break-word;'>63.9</td><td style='text-align: center; word-wrap: break-word;'>53.7</td><td style='text-align: center; word-wrap: break-word;'>74.5</td><td style='text-align: center; word-wrap: break-word;'>64.8</td><td style='text-align: center; word-wrap: break-word;'>74.3</td><td style='text-align: center; word-wrap: break-word;'>66.1</td><td style='text-align: center; word-wrap: break-word;'>68.6</td><td style='text-align: center; word-wrap: break-word;'>50.3</td><td style='text-align: center; word-wrap: break-word;'>76.8</td><td style='text-align: center; word-wrap: break-word;'>52.3</td><td style='text-align: center; word-wrap: break-word;'>59.5</td><td style='text-align: center; word-wrap: break-word;'>77.0</td><td style='text-align: center; word-wrap: break-word;'>46.3</td></tr></table>

<div style="text-align: center;">(b) Ablation study in the SFT model initialization.</div>


<div style="text-align: center;">Table 2. Ablation studies in the SFT stage. LV178K denotes the datasets used in LLaVA-Video-178K [105]. Live526K refers to our proposed Live-WhisperX-526K. LiveSports-3K CC denotes the win rate against commentary generated by LLaVA-Video-72B. LiveSports-3K QA is the overall accuracy includes OCR, Who, When, What questions. Te, Sp, At, Ac, Ob, IS denotes temporal, spatial, attribute, action, object, information synopsis, respectively.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Model (7B/8B)</td><td colspan="2">Video MME</td><td style='text-align: center; word-wrap: break-word;'>MVBench</td><td colspan="4">OVOBench</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>w/o sub</td><td style='text-align: center; word-wrap: break-word;'>w sub</td><td style='text-align: center; word-wrap: break-word;'>Avg.</td><td style='text-align: center; word-wrap: break-word;'>Avg.</td><td style='text-align: center; word-wrap: break-word;'>RTVP</td><td style='text-align: center; word-wrap: break-word;'>BT</td><td style='text-align: center; word-wrap: break-word;'>FAR</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LongVA-7B [103]</td><td style='text-align: center; word-wrap: break-word;'>52.6</td><td style='text-align: center; word-wrap: break-word;'>54.3</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>InternVL2-8B [17]</td><td style='text-align: center; word-wrap: break-word;'>54.0</td><td style='text-align: center; word-wrap: break-word;'>56.9</td><td style='text-align: center; word-wrap: break-word;'>66.4</td><td style='text-align: center; word-wrap: break-word;'>50.2</td><td style='text-align: center; word-wrap: break-word;'>60.4</td><td style='text-align: center; word-wrap: break-word;'>43.4</td><td style='text-align: center; word-wrap: break-word;'>46.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-OV-7B [41]</td><td style='text-align: center; word-wrap: break-word;'>58.2</td><td style='text-align: center; word-wrap: break-word;'>61.5</td><td style='text-align: center; word-wrap: break-word;'>56.7</td><td style='text-align: center; word-wrap: break-word;'>52.7</td><td style='text-align: center; word-wrap: break-word;'>64.0</td><td style='text-align: center; word-wrap: break-word;'>43.7</td><td style='text-align: center; word-wrap: break-word;'>50.5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Oryx-7B [56]</td><td style='text-align: center; word-wrap: break-word;'>58.3</td><td style='text-align: center; word-wrap: break-word;'>62.6</td><td style='text-align: center; word-wrap: break-word;'>63.9</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>mPLUG-Owl3-7B [94]</td><td style='text-align: center; word-wrap: break-word;'>59.3</td><td style='text-align: center; word-wrap: break-word;'>68.1</td><td style='text-align: center; word-wrap: break-word;'>59.5</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LongVU-7B [75]</td><td style='text-align: center; word-wrap: break-word;'>60.6</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>66.9</td><td style='text-align: center; word-wrap: break-word;'>46.7</td><td style='text-align: center; word-wrap: break-word;'>57.6</td><td style='text-align: center; word-wrap: break-word;'>35.0</td><td style='text-align: center; word-wrap: break-word;'>47.5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MiniCPM-v2.6 [92]</td><td style='text-align: center; word-wrap: break-word;'>60.9</td><td style='text-align: center; word-wrap: break-word;'>63.6</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2-VL-7B-Instruct [80]</td><td style='text-align: center; word-wrap: break-word;'>63.3</td><td style='text-align: center; word-wrap: break-word;'>69.0</td><td style='text-align: center; word-wrap: break-word;'>67.0</td><td style='text-align: center; word-wrap: break-word;'>50.4</td><td style='text-align: center; word-wrap: break-word;'>56.0</td><td style='text-align: center; word-wrap: break-word;'>46.5</td><td style='text-align: center; word-wrap: break-word;'>48.7</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-Video-7B [106]</td><td style='text-align: center; word-wrap: break-word;'>63.3</td><td style='text-align: center; word-wrap: break-word;'>69.7</td><td style='text-align: center; word-wrap: break-word;'>58.6</td><td style='text-align: center; word-wrap: break-word;'>52.9</td><td style='text-align: center; word-wrap: break-word;'>63.5</td><td style='text-align: center; word-wrap: break-word;'>40.4</td><td style='text-align: center; word-wrap: break-word;'>54.8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LiveCC-7B-Instruct</td><td style='text-align: center; word-wrap: break-word;'>64.1</td><td style='text-align: center; word-wrap: break-word;'>70.3</td><td style='text-align: center; word-wrap: break-word;'>62.8</td><td style='text-align: center; word-wrap: break-word;'>59.8</td><td style='text-align: center; word-wrap: break-word;'>59.1</td><td style='text-align: center; word-wrap: break-word;'>68.9</td><td style='text-align: center; word-wrap: break-word;'>51.5</td></tr></table>

<div style="text-align: center;">Table 3. Comparison of QA accuracy (%) across VideoMME [23], MVBench [45], OVOBench [46]. We only show results before the CVPR 2025 submission period (Nov, 2024).</div>


Table 1a, both caption and streaming pre-training achieve strong general video QA performance (exceeding 60) on the Video-MME benchmark [23], outperforming many existing SFT models. Notably, the streaming-based pre-training yields significantly better results on the commentary task compared to caption-based pre-training, highlighting the effectiveness of our proposed paradigm.

Context Input for Pre-training. In Table 1b, we observe that providing contextual information, particularly the previous ASR text, significantly improves commentary generation. This improvement stems from the fact that a 60-second segment can break the continuity of ASR, making it difficult to interpret the current segment without prior context. While incorporating the video title as additional context offers benefits on commentary, it slightly degrades performance on VideoMME. We attribute this to potential information leakage, which may make training easier. To handle the cases where no previous ASR is available (e.g., clips at the beginning of a video), we adopt a hybrid strategy: "Title || Prev. ASR", which includes the video title only when previous ASR is unavailable. This approach strikes the best balance between enhancing commentary generation


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Size</td><td rowspan="2">Model</td><td colspan="6">LiveSports-3K  $ \uparrow $</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Live?</td><td style='text-align: center; word-wrap: break-word;'>CC</td><td style='text-align: center; word-wrap: break-word;'>Overall</td><td style='text-align: center; word-wrap: break-word;'>OCR</td><td style='text-align: center; word-wrap: break-word;'>Who</td><td style='text-align: center; word-wrap: break-word;'>When</td><td style='text-align: center; word-wrap: break-word;'>What</td></tr><tr><td rowspan="2">-</td><td style='text-align: center; word-wrap: break-word;'>GPT-4o-08-06 [29]</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>72.2</td><td style='text-align: center; word-wrap: break-word;'>74.0</td><td style='text-align: center; word-wrap: break-word;'>75.8</td><td style='text-align: center; word-wrap: break-word;'>63.4</td><td style='text-align: center; word-wrap: break-word;'>75.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Gemini-1.5-Pro [3]</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>52.8</td><td style='text-align: center; word-wrap: break-word;'>61.8</td><td style='text-align: center; word-wrap: break-word;'>61.7</td><td style='text-align: center; word-wrap: break-word;'>59.9</td><td style='text-align: center; word-wrap: break-word;'>51.6</td><td style='text-align: center; word-wrap: break-word;'>70.7</td></tr><tr><td rowspan="5">72B</td><td style='text-align: center; word-wrap: break-word;'>Qwen2-VL-72B-Instruct [80]</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>17.0</td><td style='text-align: center; word-wrap: break-word;'>70.8</td><td style='text-align: center; word-wrap: break-word;'>67.8</td><td style='text-align: center; word-wrap: break-word;'>74.6</td><td style='text-align: center; word-wrap: break-word;'>61.2</td><td style='text-align: center; word-wrap: break-word;'>74.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLaMA-2-72B [18]</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>24.8</td><td style='text-align: center; word-wrap: break-word;'>62.4</td><td style='text-align: center; word-wrap: break-word;'>55.7</td><td style='text-align: center; word-wrap: break-word;'>63.6</td><td style='text-align: center; word-wrap: break-word;'>54.3</td><td style='text-align: center; word-wrap: break-word;'>67.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-OV-72B [41]</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>29.2</td><td style='text-align: center; word-wrap: break-word;'>68.7</td><td style='text-align: center; word-wrap: break-word;'>61.7</td><td style='text-align: center; word-wrap: break-word;'>71.1</td><td style='text-align: center; word-wrap: break-word;'>61.5</td><td style='text-align: center; word-wrap: break-word;'>71.8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-VL-72B-Instruct [6]</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>30.4</td><td style='text-align: center; word-wrap: break-word;'>73.7</td><td style='text-align: center; word-wrap: break-word;'>70.1</td><td style='text-align: center; word-wrap: break-word;'>75.7</td><td style='text-align: center; word-wrap: break-word;'>69.3</td><td style='text-align: center; word-wrap: break-word;'>75.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-Video-72B [106]</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>35.0</td><td style='text-align: center; word-wrap: break-word;'>71.1</td><td style='text-align: center; word-wrap: break-word;'>65.1</td><td style='text-align: center; word-wrap: break-word;'>74.1</td><td style='text-align: center; word-wrap: break-word;'>64.8</td><td style='text-align: center; word-wrap: break-word;'>73.3</td></tr><tr><td rowspan="9">7B</td><td style='text-align: center; word-wrap: break-word;'>Qwen2-VL-7B-Instruct [80]</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>9.3</td><td style='text-align: center; word-wrap: break-word;'>65.8</td><td style='text-align: center; word-wrap: break-word;'>65.8</td><td style='text-align: center; word-wrap: break-word;'>67.9</td><td style='text-align: center; word-wrap: break-word;'>58.8</td><td style='text-align: center; word-wrap: break-word;'>69.2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-VL-7B-Instruct [6]</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>17.3</td><td style='text-align: center; word-wrap: break-word;'>67.0</td><td style='text-align: center; word-wrap: break-word;'>64.8</td><td style='text-align: center; word-wrap: break-word;'>70.3</td><td style='text-align: center; word-wrap: break-word;'>60.6</td><td style='text-align: center; word-wrap: break-word;'>69.0</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>InternLM-XC2.5-7B [102]</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>17.3</td><td style='text-align: center; word-wrap: break-word;'>59.3</td><td style='text-align: center; word-wrap: break-word;'>56.7</td><td style='text-align: center; word-wrap: break-word;'>60.7</td><td style='text-align: center; word-wrap: break-word;'>54.9</td><td style='text-align: center; word-wrap: break-word;'>61.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-Omni-7B [87] (Thinker)</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>17.6</td><td style='text-align: center; word-wrap: break-word;'>66.8</td><td style='text-align: center; word-wrap: break-word;'>66.1</td><td style='text-align: center; word-wrap: break-word;'>70.0</td><td style='text-align: center; word-wrap: break-word;'>60.0</td><td style='text-align: center; word-wrap: break-word;'>69.2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-Video-7B [106]</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>27.1</td><td style='text-align: center; word-wrap: break-word;'>66.4</td><td style='text-align: center; word-wrap: break-word;'>64.1</td><td style='text-align: center; word-wrap: break-word;'>72.7</td><td style='text-align: center; word-wrap: break-word;'>56.4</td><td style='text-align: center; word-wrap: break-word;'>68.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-OV-7B [41]</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>27.7</td><td style='text-align: center; word-wrap: break-word;'>63.4</td><td style='text-align: center; word-wrap: break-word;'>60.7</td><td style='text-align: center; word-wrap: break-word;'>67.4</td><td style='text-align: center; word-wrap: break-word;'>53.7</td><td style='text-align: center; word-wrap: break-word;'>67.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2-VL-7B-LiveCCInstruct</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>33.7</td><td style='text-align: center; word-wrap: break-word;'>67.1</td><td style='text-align: center; word-wrap: break-word;'>66.8</td><td style='text-align: center; word-wrap: break-word;'>69.8</td><td style='text-align: center; word-wrap: break-word;'>57.0</td><td style='text-align: center; word-wrap: break-word;'>72.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LiveCC-7B-Instruct</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>41.5</td><td style='text-align: center; word-wrap: break-word;'>66.8</td><td style='text-align: center; word-wrap: break-word;'>66.4</td><td style='text-align: center; word-wrap: break-word;'>71.4</td><td style='text-align: center; word-wrap: break-word;'>56.1</td><td style='text-align: center; word-wrap: break-word;'>70.8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LiveCC-7B-Base</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>43.2</td><td style='text-align: center; word-wrap: break-word;'>57.9</td><td style='text-align: center; word-wrap: break-word;'>61.4</td><td style='text-align: center; word-wrap: break-word;'>59.4</td><td style='text-align: center; word-wrap: break-word;'>50.7</td><td style='text-align: center; word-wrap: break-word;'>61.9</td></tr></table>

<div style="text-align: center;">Table 4. Win rate on the LiveSports-3K-CC track and QA accuracy on the LiveSports-3K-QA track. GPT-4o-08-06 is used as the Baseline for the commentary win rate comparison due to its strong performance. For a fair comparison, all Qwen models [6, 80, 87] and our models are evaluated on a maximum of 480 frames. The Qwen models did not perform as expected, as they tend to simply caption the video rather than follow the preceding ASR context to continue the video commentary.</div>


##### and maintaining general video QA performance.

Pre-training Scalability. Table 1c presents the results of scaling up the pre-training data. We observe that commentary performance consistently improves with larger data size. However, QA performance begins to decline beyond the 5M scale, likely due to the use of single-source (streaming commentary) data during pre-training. Since our primary goal is to demonstrate the effectiveness of the streaming-based pre-training, we defer the use of multi-source data to the SFT stage.

### 5.3. Overall Results

In Table 3 and Table 4, we compare the performance of various models on general QA, streaming QA and

8

<div style="text-align: center;"><img src="imgs/img_in_image_box_118_147_585_417.jpg" alt="Image" width="38%" />

Pre-trained Model Prediction:
62k: the 62k is it.
62k: growth bear 62k: and this 62k is a greatly 62k: standing eight 62k: far left and 62k: being up with 62k: to 1500 72k: bears are the 72k: largest land 72k: carnivores in 72k: north America 72k: they are the 72k: not afraid to 72k: to fight 72k: for fear 72k: food or 72k: three forebony 82k: their bony 82k: they are 82k: these two fighting 82k: bears are fighting 82k: one of a five-size 82k: the right is 82k: the eight is 82k: wants to make 82k: with her arm 92k: he's using his 92k: 42 teeth
Snapshot
Pre-trained to 5FT Model Prediction:
62k: The bear is on the prodigal 62k: it's 62k: going for food.
62k: But it's 62k: not the only one.
62k: are in a fight.
62k: they are weight 62k: feet tall.
62k: They weigh over 1,200 72k: And they're both 72k: they are right.
72k: They're looking for 72k: and they're looking for 72k: a fight.
72k: a fight.
72k: This is a battle 72k: myself.
72k: And the winner will 72k: have been bear 82k: This is a animal 82k: they fight.
82k: And this is a Mortal 82k: Carbine.
82k: The two bears 82k: have been fighting for 82k: both enhanced.
82k: both exhausted.
82k: teeth each 92k: They're sharp.
Snapshot

</div>


<div style="text-align: center;">Figure 7. Comparison of pre-trained and instruction tuning enhanced model's predictions on the same video. This example is sourced from Video-MME [23], with the YouTube ID whksDmTR9YE featuring animal fights.</div>


our LiveSports-3K benchmarks, including advanced proprietary models, SOTA open-source 72B models, and SOTA open-source 7B models. Despite being initialized from Qwen2-VL-7B-Base, our LiveCC-7B-Instruct outperforms Qwen2-VL-7B-Instruct on the general QA, i.e., VideoMME (64.1 vs. 63.3) and the streaming benchmark, i.e., OVOBench (59.8 vs. 50.4). This demonstrates the strong generalization capabilities of our dataset and training method. In our proposed LiveSports-3K benchmark, we observe that our three models achieve significant advantages in commentary while maintaining competitive on QA, which demonstrates the effectiveness of our method.

### 5.4. Streaming Commentary Capabilities

Figure 7 shows that the pre-trained model can already demonstrate impressive real-time video commentary capabilities. With SFT, the model further improves formatting (e.g., punctuation, case) and coherence. More examples are provided in the supplementary material.

## 6. Conclusion

In this paper, we investigated the large-scale training of video LLMs using ASR transcripts. We proposed a novel streaming training approach that densely interleaves fine-grained ASR words with their corresponding video frames based on timestamps. Our methodology involved the collection of two datasets: Live-CC-5M for pre-training and Live-WhisperX-526K for instruction tuning. We then developed our streaming pre-training approach, introducing a series of innovative training and inference strategies. Additionally, we designed LiveSports-3K, with two evaluation tracks, LiveSports-3K-CC and LiveSports-3K-QA, which are specifically tailored to assess the model's streaming capabilities. Our extensive experiments demonstrate that our model can perform low-latency commentary for streaming videos and general question answering for holistic video understanding in state-of-the-art performance simultaneously. In future work, we seek methods to train multimodal omni models in streaming.



## Acknowledgments

This research is supported by the National Research Foundation, Singapore, under its AI Singapore Programme (AISG Award No: AISG3-RP-2022-030). Joya Chen proposed the idea, designed and implemented the data production pipeline and the model training/inference codebase. Ziyun Zeng built the benchmark and designed and implemented the free-form commentary evaluation. Yiqi Lin made significant contributions to baseline model analysis, data collection, and paper writing. We jointly trained and evaluated the models and discussed the results together. We acknowledge the resource support from TikTok AIIC and thank Wei Li and Zejun Ma for their valuable guidance. We are also grateful for the insightful discussions with Rui Qian and Yu Li, and we thank Kevin Qinghong Lin, Zhaoyang Lv, Yichi Zhang, and Huiyu Wang for their constructive comments.

## References

[1] Huda AlAmri, Vincent Cartillier, Abhishek Das, Jue Wang, Anoop Cherian, Irfan Essa, Dhruv Batra, Tim K. Marks, Chiori Hori, Peter Anderson, Stefan Lee, and Devi Parikh. Audio visual scene-aware dialog. In CVPR, pages 7558–7567, 2019. 3

[2] Jean-Baptiste Alayrac, Jeff Donahue, Pauline Luc, Antoine Miech, Iain Barr, Yana Hasson, Karel Lenc, Arthur Mensch, Katherine Millican, Malcolm Reynolds, Roman Ring, Eliza Rutherford, Serkan Cabi, Tengda Han, Zhitao Gong, Sina Samangooei, Marianne Monteiro, Jacob L. Menick, Sebastian Borgeaud, Andy Brock, Aida Nematzadeh, Sahand Sharifzadeh, Mikolaj Binkowski, Ricardo Barreira, Oriol Vinyals, Andrew Zisserman, and Karén Simonyan. Flamingo: a visual language model for few-shot learning. In NeurIPS, 2022. 2

[3] Rohan Anil, Sebastian Borgeaud, Yonghui Wu, Jean-Baptiste Alayrac, Jiahui Yu, Radu Soricut, Johan Schalkwyk, Andrew M. Dai, Anja Hauth, Katie Millican, David Silver, Slav Petrov, Melvin Johnson, Ioannis Antonoglou, Julian Schrittwieser, Amelia Glaese, Jilin Chen, Emily Pitler, Timothy P. Lillicrap, Angeliki Lazaridou, Orhan Firat, James Molloy, Michael Isard, Paul Ronald Barham, Tom Hennigan, Benjamin Lee, Fabio Viola, Malcolm Reynolds, Yuanzhong Xu, Ryan Doherty, Eli Collins, Clemens Meyer, Eliza Rutherford, Erica Moreira, Kareem Ayoub, Megha Goel, George Tucker, Enrique Piqueras, Maxim Krikun, Iain Barr, Nikolay Savinov, Ivo Danihelka, Becca Roelofs, Anais White, Anders Andreassen, Tamara von Glehn, Lakshman Yagati, Mehran Kazemi, Lucas Gonzalez, Misha Khalman, Jakub Sygnowski, and et al. Gemini: A family of highly capable multimodal models. arXiv:2312.11805, 2023. 1, 2, 8, 15

9

[4] Jinze Bai, Shuai Bai, Yunfei Chu, Zeyu Cui, Kai Dang, Xiaodong Deng, Yang Fan, Wenbin Ge, Yu Han, Fei Huang, Binyuan Hui, Luo Ji, Mei Li, Junyang Lin, Runji Lin, Dayiheng Liu, Gao Liu, Chengqiang Lu, Keming Lu, Jianxin Ma, Rui Men, Xingzhang Ren, Xuancheng Ren, Chuanqi Tan, Sinan Tan, Jianhong Tu, Peng Wang, Shijie Wang, Wei Wang, Shengguang Wu, Benfeng Xu, Jin Xu, An Yang, Hao Yang, Jian Yang, Shusheng Yang, Yang Yao, Bowen Yu, Hongyi Yuan, Zheng Yuan, Jianwei Zhang, Xingxuan Zhang, Yichang Zhang, Zhenru Zhang, Chang Zhou, Jingren Zhou, Xiaohuan Zhou, and Tianhang Zhu. Qwen technical report. arXiv:2309.16609, 2023. 1

[5] Jinze Bai, Shuai Bai, Shusheng Yang, Shijie Wang, Sinan Tan, Peng Wang, Junyang Lin, Chang Zhou, and Jingren Zhou. Qwen-vl: A frontier large vision-language model with versatile abilities. arXiv:2308.12966, 2023. 2

[6] Shuai Bai, Keqin Chen, Xuejing Liu, Jialin Wang, Wenbin Ge, Sibo Song, Kai Dang, Peng Wang, Shijie Wang, Jun Tang, Humen Zhong, Yuanzhi Zhu, Mingkun Yang, Zhao-hai Li, Jianqiang Wan, Pengfei Wang, Wei Ding, Zheren Fu, Yiheng Xu, Jiabo Ye, Xi Zhang, Tianbao Xie, Zesen Cheng, Hang Zhang, Zhibo Yang, Haiyang Xu, and Jun-yang Lin. Qwen2.5-vl technical report. arXiv:2412.15115, 2024. 2, 8, 15

[7] Max Bain, Jaesung Huh, Tengda Han, and Andrew Zisserman. Whisperx: Time-accurate speech transcription of long-form audio. arXiv preprint arXiv:2303.00747, 2023. 3, 4

[8] Tom Brown, Benjamin Mann, Nick Ryder, Melanie Subbiah, Jared D Kaplan, Prafulla Dhariwal, Arvind Neelakantan, Pranav Shyam, Girish Sastry, Amanda Askell, Sandhini Agarwal, Ariel Herbert-Voss, Gretchen Krueger, Tom Henighan, Rewon Child, Aditya Ramesh, Daniel Ziegler, Jeffrey Wu, Clemens Winter, Chris Hesse, Mark Chen, Eric Sigler, Mateusz Litwin, Scott Gray, Benjamin Chess, Jack Clark, Christopher Berner, Sam McCandlish, Alec Radford, Ilya Sutskever, and Dario Amodei. Language models are few-shot learners. In NeurIPS, pages 1877–1901, 2020.2

[9] Shyamal Buch, Victor Escorcia, Chuanqi Shen, Bernard Ghanem, and Juan Carlos Niebles. Sst: Single-stream temporal action proposals. In Proceedings of the IEEE conference on Computer Vision and Pattern Recognition, pages 2911–2920, 2017. 3

[10] João Carreira and Andrew Zisserman. Quo vadis, action recognition? A new model and the kinetics dataset. In CVPR, pages 4724–4733, 2017. 3

[11] João Carreira, Eric Noland, Andras Banki-Horvath, Chloe Hillier, and Andrew Zisserman. A short note about kinetics-600. Arxiv, 1808.01340, 2018. 3

[12] Jun Chen, Deyao Zhu, Xiaoqian Shen, Xiang Li, Zechun Liu, Pengchuan Zhang, Raghuraman Krishnamoorthi, Vikas Chandra, Yunyang Xiong, and Mohamed Elhoseiny. Minigpt-v2: large language model as a unified interface for vision-language multi-task learning. arXiv:2310.09478, 2023. 2

[13] Joya Chen, Zhaoyang Lv, Shiwei Wu, Kevin Qinghong Lin, Chenan Song, Difei Gao, Jia-Wei Liu, Ziteng Gao, Dongx

ing Mao, and Mike Zheng Shou. Videollm-online: Online video large language model for streaming video. In CVPR, 2024. 2, 3

[14] Lin Chen, Xilin Wei, Jinsong Li, Xiaoyi Dong, Pan Zhang, Yuhang Zang, Zehui Chen, Haodong Duan, Bin Lin, Zhenyu Tang, et al. Sharegpt4video: Improving video understanding and generation with better captions. arXiv preprint arXiv:2406.04325, 2024. 2

[15] Tsai-Shien Chen, Aliaksandr Siarohin, Willi Menapace, Ekaterina Deyneka, Hsiang-wei Chao, Byung Eun Jeon, Yuwei Fang, Hsin-Ying Lee, Jian Ren, Ming-Hsuan Yang, et al. Panda-70m: Captioning 70m videos with multiple cross-modality teachers. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 13320–13331, 2024. 2

[16] Zhe Chen, Weiyun Wang, Yue Cao, Yangzhou Liu, Zhangwei Gao, Erfei Cui, Jinguo Zhu, Shenglong Ye, Hao Tian, Zhaoyang Liu, Lixin Gu, Xuehui Wang, Qingyun Li, Yimin Ren, Zixuan Chen, Jiapeng Luo, Jiahao Wang, Tan Jiang, Bo Wang, Conghui He, Botian Shi, Xingcheng Zhang, Han Lv, Yi Wang, Wenqi Shao, Pei Chu, Zhongying Tu, Tong He, Zhiyong Wu, Huipeng Deng, Jiaye Ge, Kai Chen, Min Dou, Lewei Lu, Xizhou Zhu, Tong Lu, Dahua Lin, Yu Qiao, Jifeng Dai, and Wenhai Wang. Expanding performance boundaries of open-source multimodal models with model, data, and test-time scaling. arXiv:2412.05271, 2024. 2

[17] Zhe Chen, Weiyun Wang, Hao Tian, Shenglong Ye, Zhangwei Gao, Erfei Cui, Wenwen Tong, Kongzhi Hu, Jiapeng Luo, Zheng Ma, et al. How far are we to gpt-4v? closing the gap to commercial multimodal models with open-source suites. arXiv preprint arXiv:2404.16821, 2024. 8

[18] Zesen Cheng, Sicong Leng, Hang Zhang, Yifei Xin, Xin Li, Guanzheng Chen, Yongxin Zhu, Wenqi Zhang, Ziyang Luo, Deli Zhao, et al. Videollama 2: Advancing spatial-temporal modeling and audio understanding in video-llms. arXiv preprint arXiv:2406.07476, 2024. 8

[19] Alexis Conneau, Kartikay Khandelwal, Naman Goyal, Vishrav Chaudhary, Guillaume Wenzek, Francisco Guzmán, Edouard Grave, Myle Ott, Luke Zettlemoyer, and Veselin Stoyanov. Unsupervised cross-lingual representation learning at scale. In ACL, 2020. 3

[20] Wenliang Dai, Junnan Li, Dongxu Li, Anthony Meng Huat Tiong, Junqi Zhao, Weisheng Wang, Boyang Li, Pascale Fung, and Steven C.H.Hoi. Instructblip: Towards general-purpose vision-language models with instruction tuning. arXiv:2305.06500, 2023. 2

[21] Alexey Dosovitskiy, Lucas Beyer, Alexander Kolesnikov, Dirk Weissenborn, Xiaohua Zhai, Thomas Unterthiner, Mostafa Dehghani, Matthias Minderer, Georg Heigold, Sylvain Gelly, Jakob Uszkoreit, and Neil Houlsby. An image is worth 16x16 words: Transformers for image recognition at scale. In ICLR, 2021. 4

[22] Abhimanyu Dubey, Abhinav Jauhri, Abhinav Pandey, Abhishek Kadian, Ahmad Al-Dahle, Aiesha Letman, Akhil Mathur, Alan Schelten, Amy Yang, Angela Fan, Anirudh Goyal, Anthony Hartshorn, Aobo Yang, Archi Mitra, Archie Sravankumar, Artem Korenev, Arthur Hinsvark, Arun Rao, Aston Zhang, Aurélien Rodriguez, Austen

10

Gregerson, Ava Spataru, Baptiste Rozière, Bethany Biron, Binh Tang, Bobbie Chern, Charlotte Caucheteux, Chaya Nayak, Chloe Bi, Chris Marra, Chris McConnell, Christian Keller, Christophe Touret, Chunyang Wu, Corinne Wong, Cristian Canton Ferrer, Cyrus Nikolaidis, Damien Allonius, Daniel Song, Danielle Pintz, Danny Livshits, David Esiobu, Dhruv Choudhary, Dhruv Mahajan, Diego Garcia-Olano, Diego Perino, Dieuwke Hupkes, Egor Lakomkin, Ehab AlBadawy, Elina Lobanova, Emily Dian, Eric Michael Smith, Filip Radenovic, Frank Zhang, Gabriel Synnaeve, Gabrielle Lee, Georgia Lewis Anderson, Graeme Nail, Grégoire Mialon, Guan Pang, Guillem Cucurell, Hailey Nguyen, Hannah Korevaar, Hu Xu, Hugo Touvron, Iliyan Zarov, Imanol Arrieta Ibarra, Isabel M. Kloumann, Ishan Misra, Ivan Evtimov, Jade Copet, Jaewon Lee, Jan Geffert, Jana Vranes, Jason Park, Jay Mahadeokar, Jeet Shah, Jelmer van der Linde, Jennifer Billock, Jenny Hong, Jenya Lee, Jeremy Fu, Jianfeng Chi, Jianyu Huang, Jiawen Liu, Jie Wang, Jiecao Yu, Joanna Bitton, Joe Spisak, Jongsoo Park, Joseph Rocca, Joshua Johnstun, Joshua Saxe, Junteng Jia, Kalyan Vasuden Alwala, Kartikeya Upasani, Kate Plawiak, Ke Li, Kenneth Heafield, Kevin Stone, and et al. The llama 3 herd of models. arXiv:2407.21783, 2024.

[23] Chaoyou Fu, Yuhan Dai, Yondong Luo, Lei Li, Shuhuai Ren, Renrui Zhang, Zihan Wang, Chenyu Zhou, Yunhang Shen, Mengdan Zhang, et al. Video-mme: The first-ever comprehensive evaluation benchmark of multi-modal llms in video analysis. arXiv preprint arXiv:2405.21075, 2024.2, 7, 8, 9

[24] Chaoyou Fu, Haojia Lin, Zuwei Long, Yunhang Shen, Meng Zhao, Yifan Zhang, Shaoqi Dong, Xiong Wang, Di Yin, Long Ma, et al. Vita: Towards open-source interactive omni multimodal llm. arXiv:2408.05211, 2024. 2, 3

[25] Chaoyou Fu, Haojia Lin, Xiong Wang, Yi-Fan Zhang, Yun-hang Shen, Xiaoyu Liu, Yangze Li, Zuwei Long, Heting Gao, Ke Li, et al. Vita-1.5: Towards gpt-4o level real-time vision and speech interaction. arXiv:2501.01957, 2025. 2, 3

[26] Roeland De Geest, Efstratios Gavves, Amir Ghodrati, Zhenyang Li, Cees Snoek, and Tinne Tuytelears. Online action detection. In ECCV, pages 269–284, 2016. 3

[27] Gemini Team Google. Gemini 1.5: Unlocking multi-modal understanding across millions of tokens of context. arXiv:2403.05530, 2024. 2

[28] Raghav Goyal, Samira Ebrahimi Kahou, Vincent Michalski, Joanna Materzynska, Susanne Westphal, Heuna Kim, Valentin Haenel, Ingo Fründ, Peter Yianilos, Moritz Mueller-Freitag, Florian Hoppe, Christian Thurau, Ingo Bax, and Roland Memisevic. The "something something" video database for learning and evaluating visual common sense. In ICCV, pages 5843–5851, 2017. 3

[29] GPT-4o. Hello gpt-4o, 2024. 2, 4, 6, 7, 8, 15

[30] Fabian Caba Heilbron, Victor Escorcia, Bernard Ghanem, and Juan Carlos Niebles. Activitynet: A large-scale video benchmark for human activity understanding. In CVPR, pages 961–970, 2015. 3, 7

[31] Jordan Hoffmann, Sebastian Borgeaud, Arthur Mensch, Elena Buchatskaya, Trevor Cai, Eliza Rutherford, Diego de Las Casas, Lisa Anne Hendricks, Johannes Welbl, Aidan Clark, Tom Hennigan, Eric Noland, Katie Millican, George van den Driessche, Bogdan Damoc, Aurelia Guy, Simon Osindero, Karen Simonyan, Erich Elsen, Jack W. Rae, Oriol Vinyals, and Laurent Sifre. Training compute-optimal large language models. arXiv:2203.15556, 2022. 2

[32] Gabriel Huang, Bo Pang, Zhenhai Zhu, Clara Rivera, and Radu Soricut. Multimodal pretraining for dense video captioning. In IJCNLP-AACL, pages 470–490, 2020. 2

[33] Zhenpeng Huang, Xinhao Li, Jiaqi Li, Jing Wang, Xiangyu Zeng, Cheng Liang, Tao Wu, Xi Chen, Liang Li, and Limin Wang. Online video understanding: A comprehensive benchmark and memory-augmented method. arXiv:2501.00584, 2025. 3

[34] Haroon Idrees, Amir R. Zamir, Yu-Gang Jiang, Alex Gorban, Ivan Laptev, Rahul Sukthankar, and Mubarak Shah. The THUMOS challenge on action recognition for videos "in the wild". Comput. Vis. Image Underst., 155:1–23, 2017. 3

[35] Hyolim Kang, Kyungmin Kim, Yumin Ko, and Seon Joo Kim. Cag-qil: Context-aware actionness grouping via q imitation learning for online temporal action localization. In Proceedings of the IEEE/CVF International Conference on Computer Vision, pages 13729–13738, 2021. 3

[36] Jared Kaplan, Sam McCandlish, Tom Henighan, Tom B. Brown, Benjamin Chess, Rewon Child, Scott Gray, Alec Radford, Jeffrey Wu, and Dario Amodei. Scaling laws for neural language models. arXiv:2001.08361, 2020. 2

[37] Ranjay Krishna, Kenji Hata, Frederic Ren, Li Fei-Fei, and Juan Carlos Niebles. Dense-captioning events in videos. In ICCV, pages 706–715, 2017. 2

[38] Xin Lai, Zhuotao Tian, Yukang Chen, Yanwei Li, Yuhui Yuan, Shu Liu, and Jiaya Jia. Lisa: Reasoning segmentation via large language model. arXiv:2308.00692, 2023. 2

[39] Jie Lei, Licheng Yu, Mohit Bansal, and Tamara L. Berg. TVQA: localized, compositional video question answering. In EMNLP, pages 1369–1379, 2018. 3

[40] Bo Li, Yuanhan Zhang, Liangyu Chen, Jinghao Wang, Jingkang Yang, and Ziwei Liu. Otter: A multi-modal model with in-context instruction tuning. arXiv:2305.03726, 2023. 2

[41] Bo Li, Yuanhan Zhang, Dong Guo, Renrui Zhang, Feng Li, Hao Zhang, Kaichen Zhang, Yanwei Li, Ziwei Liu, and Chunyuan Li. Llava-onevision: Easy visual task transfer. arXiv preprint arXiv:2408.03326, 2024. 8, 15

[42] Bo Li, Yuanhan Zhang, Dong Guo, Renrui Zhang, Feng Li, Hao Zhang, Kaichen Zhang, Yanwei Li, Ziwei Liu, and Chunyuan Li. Llava-onevision: Easy visual task transfer. arXiv:2408.03326, 2024. 2

[43] Junnan Li, Dongxu Li, Silvio Savarese, and Steven Hoi. Blip-2: Bootstrapping language-image pre-training with frozen image encoders and large language models. arXiv preprint arXiv:2301.12597, 2023. 2

[44] KunChang Li, Yinan He, Yi Wang, Yizhuo Li, Wenhai Wang, Ping Luo, Yali Wang, Limin Wang, and

11

Yu Qiao. Videochat: Chat-centric video understanding. arXiv:2305.06355, 2023. 2

[45] Kunchang Li, Yali Wang, Yinan He, Yizhuo Li, Yi Wang, Yi Liu, Zun Wang, Jilan Xu, Guo Chen, Ping Luo, et al. Mvbench: A comprehensive multi-modal video understanding benchmark. In CVPR, pages 22195–22206, 2024. 2, 7, 8

[46] Yifei Li, Junbo Niu, Ziyang Miao, Chunjiang Ge, Yuanhang Zhou, Qihao He, Xiaoyi Dong, Haodong Duan, Shuangrui Ding, Rui Qian, Pan Zhang, Yuhang Zang, Yuhang Cao, Conghui He, and Jiaqi Wang. Ovo-bench: How far is your video-llms from real-world online video understanding? arXiv:2501.05510, 2025. 2, 3, 7, 8

[47] Junhua Liao, Haihan Duan, Kanghui Feng, Wanbing Zhao, Yanbing Yang, and Liangyin Chen. A light weight model for active speaker detection. In CVPR, pages 22932–22941, 2023. 2, 4

[48] Bin Lin, Bin Zhu, Yang Ye, Munan Ning, Peng Jin, and Li Yuan. Video-llava: Learning united visual representation by alignment before projection. arXiv:2311.10122, 2023. 2

[49] Junming Lin, Zheng Fang, Chi Chen, Zihao Wan, Fuwen Luo, Peng Li, Yang Liu, and Maosong Sun. Streaming-bench: Assessing the gap for mlims to achieve streaming video understanding. arXiv preprint arXiv:2411.03628, 2024. 3

[50] Ji Lin, Hongxu Yin, Wei Ping, Pavlo Molchanov, Mohammad Shoeybi, and Song Han. VILA: on pre-training for visual language models. In CVPR, pages 26679–26689, 2024. 2,5

[51] Kevin Qinghong Lin, Alex Jinpeng Wang, Mattia Soldan, Michael Wray, Rui Yan, Eric Zhongcong Xu, Difei Gao, Rongcheng Tu, Wenzhe Zhao, Weijie Kong, Chengfei Cai, Hongfa Wang, Dima Damen, Bernard Ghanem, Wei Liu, and Mike Zheng Shou. Egocentric video-language pretraining. arXiv:2206.01670, 2022. 3

[52] Kevin Qinghong Lin, Pengchuan Zhang, Joya Chen, Shraman Pramanick, Difei Gao, Alex Jinpeng Wang, Rui Yan, and Mike Zheng Shou. Univtg: Towards unified videolanguage temporal grounding. In ICCV, pages 2782–2792, 2023. 2

[53] Haotian Liu, Chunyuan Li, Yuheng Li, and Yong Jae Lee. Improved baselines with visual instruction tuning. arXiv:2310.03744, 2023. 2

[54] Haotian Liu, Chunyuan Li, Qingyang Wu, and Yong Jae Lee. Visual instruction tuning. NeurIPS, 2023. 2, 5

[55] Jihao Liu, Zhiding Yu, Shiyi Lan, Shihao Wang, Rongyao Fang, Jan Kautz, Hongsheng Li, and Jose M. Alvarez. Streamchat: Chatting with streaming video. arXiv:2412.08646, 2024. 2, 3

[56] Zuyan Liu, Yuhao Dong, Ziwei Liu, Winston Hu, Jiwen Lu, and Yongming Rao. Oryx mllm: On-demand spatial-temporal understanding at arbitrary resolution. arXiv preprint arXiv:2409.12961, 2024. 8

[57] Muhammad Maaz, Hanoona Rasheed, Salman Khan, and Fahad Khan. Video-ChatGPT: Towards detailed video understanding via large vision and language models. In Proceedings of the 62nd Annual Meeting of the Association for

Computational Linguistics (Volume 1: Long Papers), pages 12585–12602, Bangkok, Thailand, 2024. Association for Computational Linguistics. 2

[58] Karttikeya Mangalam, Raiymbek Akshulakov, and Jitendra Malik. Egoschema: A diagnostic benchmark for very long-form video language understanding. In NeurIPS, pages 46212–46244, 2023. 3

[59] Brandon McKinzie, Zhe Gan, Jean-Philippe Fauconnier, Sam Dodge, Bowen Zhang, Philipp Dufter, Dhruti Shah, Xianzhi Du, Futang Peng, Floris Weers, et al. Mm1: Methods, analysis & insights from multimodal llm pre-training. arXiv preprint arXiv:2403.09611, 2024. 2

[60] Antoine Miech, Dimitri Zhukov, Jean-Baptiste Alayrac, Makarand Tapaswi, Ivan Laptev, and Josef Sivic. Howto100m: Learning a text-video embedding by watching hundred million narrated video clips. In ICCV, pages 2630–2640, 2019. 2, 3

[61] Hassan Mkhallati, Anthony Cioppa, Silvio Giancola, Bernard Ghanem, and Marc Van Droogenbroeck. Soccernet-caption: Dense video captioning for soccer broadcasts commentaries. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 5074–5085, 2023. 5

[62] OpenAI. Introducing chatgpt. https://openai.com/blog/chatgpt/, 2023.1

[63] OpenAI. GPT-4 technical report. arXiv:2303.08774, 2023.

[64] OpenAI. Gpt-4v(ision) system card. https://cdn.openai.com/papers/GPTV_System_Card.pdf, 2023. 2

[65] Adam Paszke, Sam Gross, and Francisco et al Massa. PyTorch: An imperative style, high-performance deep learning library. In NeurIPS, pages 8026–8037, 2019. 7

[66] Viorica Patraucean, Lucas Smaira, Ankush Gupta, Adria Recasens, Larisa Markeeva, Dylan Banarse, Skanda Koppula, Mateusz Malinowski, Yi Yang, Carl Doersch, et al. Perception test: A diagnostic benchmark for multimodal video models. Advances in Neural Information Processing Systems, 36, 2024. 7

[67] Rui Qian, Xiaoyi Dong, Pan Zhang, Yuhang Zang, Shuangri Ding, Dahua Lin, and Jiaqi Wang. Streaming long video understanding with large language models. In NeurIPS, 2024. 2, 3

[68] Rui Qian, Shuangrui Ding, Xiaoyi Dong, Pan Zhang, Yuhang Zang, Yuhang Cao, Dahua Lin, and Jiaqi Wang. Dispider: Enabling video llms with active real-time interaction via disentangled perception, decision, and reaction. arXiv:2501.03218, 2025. 2, 3

[69] Alec Radford, Karthik Narasimhan, Tim Salimans, Ilya Sutskever, et al. Improving language understanding by generative pre-training. 2018. 2

[70] Alec Radford, Jeff Wu, Rewon Child, David Luan, Dario Amodei, and Ilya Sutskever. Language models are unsupervised multitask learners. 2019. 2

[71] Alec Radford, Jong Wook Kim, Chris Hallacy, Aditya Ramesh, Gabriel Goh, Sandhini Agarwal, Girish Sastry, Amanda Askell, Pamela Mishkin, Jack Clark, Gretchen

12

Krueger, and Ilya Sutskever. Learning transferable visual models from natural language supervision. In ICML, pages 8748–8763, 2021. 2

[72] Alec Radford, Jong Wook Kim, Tao Xu, Greg Brockman, Christine McLeavey, and Ilya Sutskever. Robust speech recognition via large-scale weak supervision. In ICML, pages 28492–28518. 2023. 3.4

[73] Jiayuan Rao, Haoning Wu, Chang Liu, Yanfeng Wang, and Weidi Xie. Matchtime: Towards automatic soccer game commentary generation. arXiv preprint arXiv:2406.18530, 2024. 5

[74] Shuhuai Ren, Linli Yao, Shicheng Li, Xu Sun, and Lu Hou. Timechat: A time-sensitive multimodal large language model for long video understanding. In CVPR, pages 14313–14323, 2024. 2

[75] Xiaoqian Shen, Yunyang Xiong, Changsheng Zhao, Lemeng Wu, Jun Chen, Chenchen Zhu, Zechun Liu, Fanyi Xiao, Balakrishnan Varadarajan, Florian Bordes, Zhuang Liu, Hu Xu, Hyunwoo J. Kim, Bilge Soran, Raghuraman Krishnamoorthi, Mohamed Elhoseiny, and Vikas Chandra. Longvu: Spatiotemporal adaptive compression for long video-language understanding. arXiv:2410.17434, 2024. 2, 8

[76] Gurkirt Singh, Suman Saha, Michael Sapienza, Philip HS Torr, and Fabio Cuzzolin. Online real-time multiple spatiotemporal action localisation and prediction. In Proceedings of the IEEE international conference on computer vision, pages 3637–3646, 2017. 3

[77] Enxin Song, Wenhao Chai, Guanhong Wang, Yucheng Zhang, Haoyang Zhou, Feiyang Wu, Xun Guo, Tian Ye, Yan Lu, Jenq-Neng Hwang, et al. Moviechat: From dense token to sparse memory for long video understanding. arXiv:2307.16449, 2023. 2

[78] Hugo Touvron, Thibaut Lavril, Gautier Izacard, Xavier Martinet, Marie-Anne Lachaux, Timothée Lacroix, Baptiste Rozière, Naman Goyal, Eric Hambro, Faisal Azhar, et al. Llama: Open and efficient foundation language models. arXiv:2302.13971, 2023.

[79] Hugo Touvron, Louis Martin, Kevin Stone, Peter Albert, Amjad Almahairi, Yasmine Babaei, Nikolay Bashlykov, Soumya Batra, Prajjwal Bhargava, Shruti Bhosale, Dan Bikel, Lukas Blecher, Cristian Canton-Ferrer, Moya Chen, Guillem Cucurull, David Esiobu, Jude Fernandes, Jeremy Fu, Wenyin Fu, Brian Fuller, Cynthia Gao, Vedanuj Goswami, Naman Goyal, Anthony Hartshorn, Saghar Hosseini, Rui Hou, Hakan Inan, Marcin Kardas, Viktor Kerkez, Madian Khabsa, Isabel Kloumann, Artem Korenev, Punit Singh Koura, Marie-Anne Lachaux, Thibaut Lavril, Jenya Lee, Diana Liskovich, Yinghai Lu, Yuning Mao, Xavier Martinet, Todor Mihaylov, Pushkar Mishra, Igor Molybog, Yixin Nie, Andrew Poulton, Jeremy Reizenstein, Rashi Rungta, Kalyan Saladi, Alan Schelten, Ruan Silva, Eric Michael Smith, Ranjan Subramanian, Xiaoqing Ellen Tan, Binh Tang, Ross Taylor, Adina Williams, Jian Xiang Kuan, Puxin Xu, Zheng Yan, Iliyan Zarov, Yuchen Zhang, Angela Fan, Melanie Kambadur, Sharan Narang, Aurélien Rodriguez, Robert Stojnic, Sergey

Edunov, and Thomas Scialom. Llama 2: Open foundation and fine-tuned chat models. arXiv:2307.09288, 2023. 1

[80] Peng Wang, Shuai Bai, Sinan Tan, Shijie Wang, Zhihao Fan, Jinze Bai, Keqin Chen, Xuejing Liu, Jialin Wang, Wenbin Ge, et al. Qwen2-vl: Enhancing vision-language model's perception of the world at any resolution. arXiv:2409.12191, 2024. 2, 4, 5, 7, 8, 15

[81] Yi Wang, Yinan He, Yizhuo Li, Kunchang Li, Jiashuo Yu, Xin Ma, Xinhao Li, Guo Chen, Xinyuan Chen, Yaohui Wang, et al. Internvid: A large-scale videotext dataset for multimodal understanding and generation. arXiv:2307.06942, 2023. 2

[82] Yueqian Wang, Xiaojun Meng, Yuxuan Wang, Jianxin Liang, Jiansheng Wei, Huishuai Zhang, and Dongyan Zhao. Videolm knows when to speak: Enhancing time-sensitive video comprehension with video-text duet interaction format, 2024. 2, 3

[83] Yuxuan Wang, Cihang Xie, Yang Liu, and Zilong Zheng. Videollamb: Long-context video understanding with recurrent memory bridges. arXiv:2409.01071, 2024. 2, 3

[84] Thomas Wolf, Lysandre Debut, Victor Sanh, Julien Chaumond, Clement Delangue, Anthony Moi, Pierric Cistac, Tim Rault, Rémi Louf, Morgan Funtowicz, Joe Davison, Sam Shleifer, Patrick von Platen, Clara Ma, Yacine Jernite, Julien Plu, Canwen Xu, Teven Le Scao, Sylvain Gugger, Mariama Drame, Quentin Lhoest, and Alexander M. Rush. Transformers: State-of-the-art natural language processing. In Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing: System Demonstrations, pages 38–45, Online, 2020. Association for Computational Linguistics. 7

[85] Junbin Xiao, Xindi Shang, Angela Yao, and Tat-Seng Chua. Next-qa: Next phase of question-answering to explaining temporal actions. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition, pages 9777–9786, 2021. 3, 7

[86] Haomiao Xiong, Zongxin Yang, Jiazuo Yu, Yunzhi Zhuge, Lu Zhang, Jiawen Zhu, and Huchuan Lu. Streaming video understanding and multi-round interaction with memory-enhanced knowledge. In ICLR, 2025. 2, 3

[87] Jin Xu, Zhifang Guo, Jinzheng He, Hangrui Hu, Ting He, Shuai Bai, Keqin Chen, Jialin Wang, Yang Fan, Kai Dang, et al. Qwen2.5-omni technical report. arXiv preprint arXiv:2503.20215, 2025. 8, 15

[88] Hongwei Xue, Tiankai Hang, Yanhong Zeng, Yuchong Sun, Bei Liu, Huan Yang, Jianlong Fu, and Baining Guo. Advancing high-resolution video-language representation with large-scale video transcriptions. In CVPR, pages 5026–5035, 2022. 2, 3

[89] Antoine Yang, Arsha Nagrani, Ivan Laptev, Josef Sivic, and Cordelia Schmid. Vidchapters-7m: Video chapters at scale. In NeurIPS, 2023. 3

[90] Antoine Yang, Arsha Nagrani, Paul Hongsuck Seo, Antoine Miech, Jordi Pont-Tuset, Ivan Laptev, Josef Sivic, and Cordelia Schmid. Vid2seq: Large-scale pretraining of a visual language model for dense video captioning. In CVPR, pages 10714–10726, 2023. 2, 3

13

[91] An Yang, Baosong Yang, Binyuan Hui, Bo Zheng, Bowen Yu, Chang Zhou, Chengpeng Li, Chengyuan Li, Dayiheng Liu, Fei Huang, et al. Qwen2 technical report. arXiv preprint arXiv:2407.10671, 2024. 1, 4

[92] Yuan Yao, Tianyu Yu, Ao Zhang, Chongyi Wang, Junbo Cui, Hongji Zhu, Tianchi Cai, Haoyu Li, Weilin Zhao, Zhihui He, et al. Minicpm-v: A gpt-4v level mlm on your phone. arXiv preprint arXiv:2408.01800, 2024. 8

[93] Zhewei Yao, Xiaoxia Wu, Conglong Li, Minjia Zhang, Heyang Qi, Olatunji Ruwase, Ammar Ahmad Awan, Samyam Rajbhandari, and Yuxiong He. Deepspeed-visualchat: Multi-round multi-image interleave chat via multi-modal causal attention. arXiv:2309.14327, 2023. 2

[94] Jiabo Ye, Haiyang Xu, Haowei Liu, Anwen Hu, Ming Yan, Qi Qian, Ji Zhang, Fei Huang, and Jingren Zhou. mplug-owl3: Towards long image-sequence understanding in multi-modal large language models. arXiv preprint arXiv:2408.04840, 2024. 8

[95] Haoxuan You, Haotian Zhang, Zhe Gan, Xianzhi Du, Bowen Zhang, Zirui Wang, Liangliang Cao, Shih-Fu Chang, and Yinfei Yang. Ferret: Refer and ground anything anywhere at any granularity. arXiv:2310.07704, 2023. 2

[96] Rowan Zellers, Jiasen Lu, Ximing Lu, Youngjae Yu, Yanpeng Zhao, Mohammadreza Salehi, Aditya Kusupati, Jack Hessel, Ali Farhadi, and Yejin Choi. MERLOT RESERVE: neural script knowledge through vision and language and sound. In CVPR, pages 16354–16366, 2022. 2, 3

[97] Xiaohua Zhai, Basil Mustafa, Alexander Kolesnikov, and Lucas Beyer. Sigmoid loss for language image pre-training. In ICCV, pages 11941–11952, 2023. 2

[98] Boqiang Zhang, Kehan Li, Zesen Cheng, Zhiqiang Hu, Yuqian Yuan, Guanzheng Chen, Sicong Leng, Yuming Jiang, Hang Zhang, Xin Li, Peng Jin, Wenqi Zhang, Fan Wang, Lidong Bing, and Deli Zhao. Videollama 3: Frontier multimodal foundation models for image and video understanding. arXiv:2501.13106. 2, 3

[99] Hang Zhang, Xin Li, and Lidong Bing. Video-llama: An instruction-tuned audio-visual language model for video understanding. arXiv:2306.02858, 2023. 2

[100] Haoji Zhang, Yiqin Wang, Yansong Tang, Yong Liu, Jiashi Feng, Jifeng Dai, and Xiaojie Jin. Flash-vstream: Memory-based real-time understanding for long video streams. arXiv:2406.08085, 2024. 2

[101] Kaichen Zhang, Bo Li, Peiyuan Zhang, Fanyi Pu, Joshua Adrian Cahyono, Kairui Hu, Shuai Liu, Yuanhan Zhang, Jingkang Yang, Chunyuan Li, and Ziwei Liu. Lmms-eval: Reality check on the evaluation of large multimodal models. arXiv:2407.12772, 2024.7

[102] Pan Zhang, Xiaoyi Dong, Yuhang Zang, Yuhang Cao, Rui Qian, Lin Chen, Qipeng Guo, Haodong Duan, Bin Wang, Linke Ouyang, et al. Internlm-xcomposer-2.5: A versatile large vision language model supporting long-contextual input and output. arXiv preprint arXiv:2407.03320, 2024. 8

[103] Peiyuan Zhang, Kaichen Zhang, Bo Li, Guangtao Zeng, Jingkang Yang, Yuanhan Zhang, Ziyue Wang, Haoran Tan, Chunyuan Li, and Ziwei Liu. Long context transfer from language to vision. arXiv preprint arXiv:2406.16852, 2024.8

[104] Shilong Zhang, Peize Sun, Shoufa Chen, Min Xiao, Wenqi Shao, Wenwei Zhang, Kai Chen, and Ping Luo. Gpt4ro: Instruction tuning large language model on region-of-interest. arXiv:2307.03601, 2023. 2

[105] Yuanhan Zhang, Jinming Wu, Wei Li, Bo Li, Zejun Ma, Ziwei Liu, and Chunyuan Li. Video instruction tuning with synthetic data. arXiv:2410.02713, 2024. 2, 3, 5, 7, 8

[106] Yuanhan Zhang, Jinming Wu, Wei Li, Bo Li, Zejun Ma, Ziwei Liu, and Chunyuan Li. Video instruction tuning with synthetic data. arXiv preprint arXiv:2410.02713, 2024. 2, 8, 15, 16

[107] Yue Zhao and Philipp Krähenbühl. Real-time online video detection with temporal smoothing transformers. In European Conference on Computer Vision, pages 485–502. Springer, 2022. 3

[108] Yucheng Zhao, Chong Luo, Chuanxin Tang, Dongdong Chen, Noel Codella, and Zheng-Jun Zha. Streaming video model. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 14602–14612, 2023. 3

[109] Lianmin Zheng, Wei-Lin Chiang, Ying Sheng, Siyuan Zhuang, Zhanghao Wu, Yonghao Zhuang, Zi Lin, Zhuohan Li, Dacheng Li, Eric P. Xing, Hao Zhang, Joseph E. Gonzalez, and Ion Stoica. Judging llm-as-a-judge with mt-bench and chatbot arena. In NeurIPS, 2023. 2, 6, 7

[110] Luowei Zhou, Chenliang Xu, and Jason J Corso. Towards automatic learning of procedures from web instructional videos. In AAAI, 2018. 2

[111] Xingyi Zhou, Anurag Arnab, Shyamal Buch, Shen Yan, Austin Myers, Xuehan Xiong, Arsha Nagrani, and Cordelia Schmid. Streaming dense video captioning. In CVPR, pages 18243–18252, 2024. 2, 3

[112] Deyao Zhu, Jun Chen, Xiaoqian Shen, Xiang Li, and Mohamed Elhoseiny. Minigpt-4: Enhancing vision-language understanding with advanced large language models. arXiv:2304.10592, 2023. 2

14

# Live CC: Learning Video LLM with Streaming Speech Transcription at Scale

Supplementary Material

## 7. Demo

This section showcases four demo videos to demonstrate the capability of our LiveCC-7B-Instruct to provide real-time commentary in real-world videos across different domains, including sports (football), science (astronomy), news (weather forecast), and instructional (computer repair) videos. As illustrated in Figure 10-13, in the first demo, our LiveCC-7B-Instruct model correctly recognizes all exact penalty timings, highlighting its strong temporal perception abilities. By leveraging the extensive world knowledge gained from watching millions of YouTube videos, our model accurately reports the name of the related player. The second demo showcases the model's ability to comment beyond sports by precisely presenting astronomy knowledge and demonstrating good OCR capability to read large numbers. The third demo further reveals its fine-grained temporal understanding capability, as evidenced by its real-time commentary on subtle changes in weather maps. The final demo demonstrates that our model is also capable of generating a tutorial to guide users, revealing its potential to serve as a real-time assistant.

## 8. Implementation Details

### 8.1. Prompt Template

In this section, we detail the prompt designs used during the pre-training, instruction tuning, and inference stages. As shown in Figure 8(a) and (b), the video title and previously transcribed ASR text are provided as contextual information during pre-training but are omitted during SFT. For the first round of vision token extraction, we use a 3-second video clip, followed by 1-second clips in subsequent rounds. Given a frame rate of 2 FPS, this corresponds to 6 and 2 frames, respectively. For QA-style data used exclusively in SFT, illustrated in Figure 8(c), we adopt the input format of Qwen2-VL-Instruct [80], which is also used during evaluation. However, for real-time commentary evaluation, we follow the format in Figure 8(d), where the video title and previous ASR transcripts are included to ensure consistency with other non-streaming baselines.

### 8.2. Win Rate Computation on LiveSports-3K

In this section, we present the detailed process for computing the win rate on LiveSports-3K-CC. To start, we categorize the models into two groups based on their inference schemes: i) Clip-wise caption models, including GPT-4o [29], Gemini-1.5-Pro [3], LLaVA-OV-7/72B [41], LLaVA-Video-7/72B [106], Qwen2-VL-7/72B-Instruct [80], Qwen2.5-VL-7/72B-Instruct [6] and Qwen2.5-Omni-7B [87]. ii) Frame-wise streaming model, i.e., our LiveCC-7B-Base, Qwen2-VL-7B-LiveCC-Instruct, LiveCC-7B-Instruct.



For clip-wise caption models, we directly input the overall event clips, perform a one-time generation, and use the generated response as the commentary. To ensure stylistic consistency and fair evaluation, the same prompt context as that shown in Figure 8(d) is applied across all models. We use the video commentary from GPT-4o-08-06 [29] serves as the baseline for comparison with other models. For our models, we adopt streaming inference shown in Figure 8(d), where commentary is generated frame by frame. The generated tokens are then concatenated to form the complete commentary, which is evaluated for quality.

For evaluation, we also prompt GPT-4o-08-06 [29] to assess whether a given commentary surpasses that of GPT-4o-08-06. The evaluation is based on two key criteria: (i) Semantic Alignment, i.e., consider which text conveys the same meaning, details, and key points as the groundtruth ASR transcript, with minimal deviation. (ii) Stylistic Consistency, i.e., assesses which text maintains a tone, word choice, and structure similar to the ground-truth transcript. The overall prompt is written as:

You are an expert in video commentary. Your task is to review two commentaries (Commentary A and Commentary B), and select the one that better aligns with the human commentary. You should consider the criteria:
1. Semantic Alignment: The commentary should convey the same meaning, details, and key points as the human commentary.
If the above criteria is not enough to judge, then consider:
2. Stylistic Consistency: The commentary should maintain a tone, word choice, and structure similar to the human commentary.
---Commentary A---
{a_pred}
------
---Commentary B---
{b_pred}
------
---Human Commentary---
{gt_asr}
------
Your response should be "Commentary A is better aligned with the human commentary" or "Commentary B is better aligned with the human commentary".

The final win rate is calculated as the proportion of instances where GPT-4o [29] selects the model's response over the baseline. To mitigate positional bias in GPT's responses, each prompt is evaluated twice with the positions

15

<div style="text-align: center;"><img src="imgs/img_in_image_box_121_141_1101_516.jpg" alt="Image" width="80%" />

<im_start|>user
0.0-3.0s[VISUAL TOKENS of 6 frames]
[VIDEO TITLE] (if PREV. ASR not exists)
[PREV. ASR] (if exists) <im_end>
<im_start|>assistant
[WORDS] ...<im_end>
<im_start|>user
3.0-4.0s[VISUAL TOKENS of 2 frames]
<im_start>>assistant
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
<im_start>>assistant
[WORDS] ...<im_end>
<im_start>>user
5.0-6.0s[VISUAL TOKENS of 2 frames]
<im_start>>assistant
[WORDS] ...<im_end>
<im_start>>user
3.0-4.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>assistant
[WORDS] ...<im_end>
<im_start>>user
5.0-6.0s[VISUAL TOKENS of 2 frames]
<im_start>>assistant
[WORDS] ...<im_end>
<im_start>>user
3.0-4.0s[VISUAL TOKENS of 2 frames]
3.0-4.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
5.0-6.0s[VISUAL TOKENS of 2 frames]
5.0-6.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
3.0-4.0s[VISUAL TOKENS of 2 frames]
3.0-4.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
5.0-6.0s[VISUAL TOKENS of 2 frames]
5.0-6.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
3.0-4.0s[VISUAL TOKENS of 2 frames]
3.0-4.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
5.0-6.0s[VISUAL TOKENS of 2 frames]
5.0-6.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
3.0-4.0s[VISUAL TOKENS of 2 frames]
3.0-4.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
5.0-6.0s[VISUAL TOKENS of 2 frames]
5.0-6.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
3.0-4.0s[VISUAL TOKENS of 2 frames]
3.0-4.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0s[VISUAL TOKENS of 2 frames]
4.0-5.0s[VISUAL TOKENS of 2 frames]
[WORDS] ...<im_end>
<im_start>>user
4.0-5.0

</div>


<div style="text-align: center;">(b) SFT CM</div>


<div style="text-align: center;">(d) Evaluation CM</div>


<div style="text-align: center;">Figure 8. The prompts used during the pre-training instruction-tuning (aka. SFT) stages. CM represents commentary, QA denotes question-answering. For pre-training and instruction-tuning, the previous ASR texts are concatenated to form the context for the live commentary task if they are available. Otherwise, the context is formed by the video title. These contexts are masked during loss calculation. Note that QA data is incorporated exclusively during the instruction-tuning stage. As for inference, we remove the groundtruth in the prompts, i.e., the words followed by a frame or the answer to a multiple-choice question.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Model</td><td style='text-align: center; word-wrap: break-word;'>Latency</td><td style='text-align: center; word-wrap: break-word;'>Input</td><td style='text-align: center; word-wrap: break-word;'>Inf. Type</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-Video-72B [106]</td><td style='text-align: center; word-wrap: break-word;'>20.51s</td><td style='text-align: center; word-wrap: break-word;'>Clip</td><td style='text-align: center; word-wrap: break-word;'>Captioning</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-Video-7B [106]</td><td style='text-align: center; word-wrap: break-word;'>5.62s</td><td style='text-align: center; word-wrap: break-word;'>Clip</td><td style='text-align: center; word-wrap: break-word;'>Captioning</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LiveCC-7B-Instruct</td><td style='text-align: center; word-wrap: break-word;'>0.17s</td><td style='text-align: center; word-wrap: break-word;'>Frame</td><td style='text-align: center; word-wrap: break-word;'>Streaming</td></tr></table>

<div style="text-align: center;">Table 5. The response latency comparison between LLaVA-Video7/72B and our LiveCC-7B. Inf. is short for Inference.</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_116_891_579_1144.jpg" alt="Image" width="37%" />

1973 AAU Indoor Track & Field Championships - Marty Liquori in the Men's M

Begin: 66.653s

End: 87.395s

Groundtruth ASR

But it's Reggie McAfee leading, easily nice, light, compact sort of runner from Howell-Michael, who's a very hard man to beat, now in the US Marine Corps at Quantico. There's Martin Licori in third place. Happy, I think, to feel that he's back at the top of the world rankings.

The race is underway, and the runners are jockeying for position. Licori is right behind McAfee and Howell-Michael, looking strong and focused. Shorikofsky is struggling a bit at the back, trying to find his way through the pack. The crowd is on their feet, cheering on the athletes as they round the first lap. Licori's form is impeccable, and he looks like he's conserving his energy for a final sprint. McAfee is setting a fast pace, but Licori seems comfortable in third place. The tension is building as we approach the halfway mark of the race.

LLaVA-Video-72B

Knowledge: correct

Voice: third person

Speak: too fast

LiveCC-7B

Knowledge: correct

Voice: first person

Speak: human alike

And it's McAfee who leads the field through the first lap. He's a very strong runner, but he's not a great tactician. He's not going to be able to hold this pace for long. And in second place, it's Howell-Michael. And in third, it's Licori. And in fourth, it's Shorikofsky.

</div>


<div style="text-align: center;">Figure 9. The comparison between the commentary generated by LLaVA-Video-72B and our LiveCC-7B-Instruct.</div>


of the tested model and baseline text swapped.

## 9. Additional Experiments

### 9.1. Response Latency

To highlight the efficiency of our streaming model, we present the response latency of LLaVA-Video-7B/72B alongside our model in Table 5. Response latency is defined as the time a user waits to see the model's output, a critical factor affecting user experience. Since the LLaVA-Video series are trained in a captioning style, requiring a full clip as input rather than a single frame, their response latency is significantly higher than that of our model. Notably, LiveCC not only achieves lower latency but also delivers high-quality commentary (see Table 4).



### 9.2. Commentary Quality

We analyzed the quality of the generated content, as shown in Figure 9. Benefiting from training on millions of ASR-transcribed videos, our model produces commentary that is more aligned with human preferences in terms of tone and speaking pace, while maintaining accurate event understanding. In contrast, the LLaVA-Video-72B, although capable of correctly describing the event, falls short in emulating human-like commentary.

16

<div style="text-align: center;"><img src="imgs/img_in_image_box_116_356_1106_1107.jpg" alt="Image" width="80%" />

Time: 21.80s, the tournament is for the first time.

</div>


<div style="text-align: center;">(d) Video Time: 77.2s</div>


<div style="text-align: center;">Figure 10. Real-time video commentary demo on unseen YouTube video (MCWJNOfJoSM). The original YouTube title is “Argentina v France: Full Penalty Shoot-out — 2022 #FIFAWorldCup Final”. We only give a part of YouTube title “Full Penalty Shoot-out — 2022 #FIFAWorldCup Final” as prompt to avoid information leakage.</div>


17

<div style="text-align: center;"><img src="imgs/img_in_image_box_114_244_1107_1232.jpg" alt="Image" width="81%" />

Video Time = 2.6s, Current Processing Latency = 0.15
Time = 0.0s: the planets
Time = 1.0s: in our solar
Time = 2.0s: system are all

(a) Video Time: 2.6s

Video Time = 13.3s, Current Processing Latency = 0.15
Time = 0.0s: the planets
Time = 2.0s: in our solar
Time = 2.0s: system are all
Time = 3.0s: different in their
Time = 4.0s: own way but they
Time = 5.0s: all have one thing
Time = 6.0s: in common they all
Time = 7.0s: orbit the Sun
Time = 8.0s: welcome to beyond
Time = 9.0s: nature and today
Time = 10.0s: we're going to be
Time = 11.0s: talking about the planets
Time = 12.0s: in our solar
Time = 13.0s: system and their

(b) Video Time: 13.3s

Video Time = 31.6s, Current Processing Latency = 0.12
Time = 0.0s: the planets
Time = 2.0s: in our solar
Time = 2.0s: system are all
Time = 3.0s: different in their
Time = 4.0s: own way but they
Time = 5.0s: all have one thing
Time = 6.0s: in common they all
Time = 7.0s: orbit the Sun
Time = 8.0s: welcome to beyond
Time = 9.0s: nature and today
Time = 10.0s: we're going to be
Time = 11.0s: in common they all
Time = 12.0s: in our solar
Time = 13.0s: distance from the planets
Time = 14.0s: characteristics the planets
Time = 15.0s: in our solar
Time = 16.0s: our solar system
Time = 17.0s: are Mercury venus
Time = 18.0s: Earth Mars
Time = 19.0s: Jupiter Saturn
Time = 20.0s: Uranus and Neptune Mercury
Time = 21.0s: is the smallest
Time = 22.0s: is the smallest
Time = 23.0s: planet in our solar system
Time = 24.0s: solar system and is the closest to the Sun
Time = 25.0s: the closest to the Sun
Time = 26.0s: Sun it is one of the two systems
Time = 27.0s: hottest planet in our solar system with an average distance of 58 million
Time = 28.0s: solar system with an average distance of 58 million
Time = 29.0s: of the Sun
Time = 30.0s: to the Sun
Time = 31.0s: to the Sun
Time = 32.0s: is the smallest
Time = 33.0s: distance from the planets
Time = 34.0s: Sun of 36
Time = 35.0s: million miles mercury
Time = 36.0s: is also the Sun
Time = 37.0s: planet in our solar system
Time = 38.0s: system that does not have a moon and
Time = 39.0s: has a diameter of 4.879 km
Time = 40.0s: has a diameter of 3.031 mi
Time = 41.0s: has a diameter of 4.879 km
Time = 42.0s: is a�: million of eight
Time = 43.0s: is: million of seven
Time = 44.0s: also three
Time = 45.0s: thousand thirty-one miles
Time = 46.0s: is: one of the 7.00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000

</div>


<div style="text-align: center;">(a) Video Time: 2.6s</div>


<div style="text-align: center;">(b) Video Time: 13.3s</div>


<div style="text-align: center;">(c) Video Time: 31.6s</div>


<div style="text-align: center;">(d) Video Time: 45.0s</div>


<div style="text-align: center;">Figure 11. Real-time video commentary demo on unseen YouTube video (1cZTcfdZ30w). We give the YouTube title “The Planets In Our Solar System” as prompt.</div>


18

<div style="text-align: center;"><img src="imgs/img_in_image_box_118_234_1106_462.jpg" alt="Image" width="80%" />

Evening Weather

Honor Criswick Meteorologist

Video Time = 4.3s, Current Processing Latency = 0.16

Time = 0.0s: hi there

Time = 2.0s: good evening it's

Time = 2.0s: a chilly and

Time = 3.0s: unsettled evening with

Time = 4.0s: wintry weather continuing

</div>


<div style="text-align: center;">(a) Video Time: 4.3s</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_118_485_1107_715.jpg" alt="Image" width="80%" />

Met Office
Friday 06:00
Time = 24.8s, Current Processing Latency = 0.19
Time = 0.05: hi there
Time = 1.05: good evening it's
Time = 2.05: a chilly and
Time = 3.05: unsettled evening with
Time = 4.05: wintry weather continuing
Time = 5.05: to persist for many
Time = 6.05: of us and that
Time = 7.05: includes some snow showers
Time = 8.05: and some sleet
Time = 9.05: showers too and
Time = 10.05: that's why we've got
Time = 11.05: these yellow warnings for
Time = 12.05: snow and ice in
Time = 13.05: place for parts of
Time = 14.05: the uk and that's
Time = 15.05: where we could see some
Time = 16.05: accumulations of snow
Time = 17.05: and ice and
Time = 18.05: that's mainly across
Time = 19.05: northern england and

</div>


<div style="text-align: center;">(b) Video Time: 24.8s</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_117_740_1106_970.jpg" alt="Image" width="80%" />

Met Office
Friday 10:00
Time = 43.8s, Current Processing Latency = 0.19
Time = 0.05: hi there
Time = 0.05: hi there
Time = 21.0s: according to continue late
Time = 21.0s: along the day tomorrow morning and 12
Time = 2.05: a chilly and
Time = 3.05: unsettled evening with
Time = 4.05: wintry weather continuing
Time = 5.00: to persist for many
Time = 6.05: of us and that
Time = 7.05: includes some snow show
Time = 8.05: and some sie
Time = 9.05: showers too and
Time = 10.05: that's why we've got
Time = 11.05: these yellow warnings for
Time = 12.05: snow and ice条件
Time = 13.05: place for parts of
Time = 14.05: the uk and that's
Time = 15.05: where we could see some
Time = 16.05: accumulation of snow
Time = 17.05: and ice and
Time = 18.05: that's mainly across
Time = 19.05: northern england and
Time = 20.05: some snow and ice
Time = 21.05: across parts of
Time = 22.05: northern Ireland and al
Time = 23.05: across parts of
Time = 24.05: wales and that's
Time = 25.05: the cold and
Time = 26.05: some snow and ice
Time = 27.05: and some accumulation
Time = 28.05: and that could lead
Time = 29.05: to increase the risk of disruption
Time = 30.05: and some snow
Time = 31.05: travel conditions too
Time = 32.05: and it's also in
Time = 33.05: going to be a chilly
Time = 34.05: night with some icy
Time = 35.05: patches and some free airlines in
Time = 36.05: place too so
Time = 37.05: place too so
Time = 38.05: overnight lows are around

</div>


<div style="text-align: center;">(c) Video Time: 43.8s</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_117_993_1105_1223.jpg" alt="Image" width="80%" />

Met Office
Friday 16:00
Time: 0:05: hi there
Time: 0:05: showing it's
Time: 2:05: a chilly and
Time: 3:05: unsettled evening with
Time: 4:05: wintry weather continuing
Time: 4:05: a place for many
Time: 6:05: of us and that
Time: 7:05: includes some snow shower
Time: 8:05: and some sleet
Time: 8:05: shows the cold and
Time: 10:05: that's why we've got
Time: 11:05: these yellow warnings fo
Time: 12:05: snow and ice in
Time: 13:05: place for the first of
Time: 14:05: the uk and that's
Time: 15:05: where we could see some
Time: 16:05: according to snow
Time: 17:05: and ice and
Time: 18:05: that's mainly across
Time: 19:05: northern england and
Time: 20:05: scotland and also
Time: 21:05: across parts of
Time: 22:05: northern Ireland and also
Time: 23:05: across parts of
Time: 24:05: wales and that's
Time: 25:05: could see
Time: 26:05: some snow and ice
Time: 27:05: and some accumulations
Time: 28:05: and that could lead
Time: 29:05: to the overall disruption
Time: 30:05: and some slow
Time: 31:05: travel conditions too
Time: 32:05: and it's also
Time: 33:05: spring to a chilly
Time: 34:05: night with some icy
Time: 35:05: patches and some
Time: 36:05: in the cold and
Time: 37:05: place too
Time: 38:05: overnight lows are
Time: 39:05: going to be around
Time: 40:05: freezing and that's
Time: 41:05: to the other day
Time: 42:05: tomorrow morning and into
Time: 43:05: the day tomorrow we've
Time: 44:05: got more wintry weather
Time: 45:05: to the other day
Time: 46:05: be the theme for the next
Time: 47:05: couple of days unfortunately
Time: 48:05: with some sleet
Time: 49:05: to the other day
Time: 50:05: showers around and
Time: 51:05: again some accumulations
Time: 52:05: of snow and
Time: 53:05: of snow and possible
Time: 54:05: and that's going to
Time: 55:05: continue into the afternoon
Time: 56:05: and it's a very chilly day
Time: 57:05: to the other day
Time: 58:05: tomorrow with temperatures
Time: 59:05: only reaching around

</div>


<div style="text-align: center;">(d) Video Time: 59.8s</div>


<div style="text-align: center;">Figure 12. Real-time video commentary demo on unseen YouTube video (8XajZdrCDsk). The original YouTube title is “21/11/24 - Wintry weather perservering - Evening Weather Forecast UK – Met Office Weather”. We only give “21/11/24 - Wintry weather perservering” as prompt to avoid information leakage.</div>


19

<div style="text-align: center;"><img src="imgs/img_in_image_box_117_309_1107_505.jpg" alt="Image" width="80%" />

Video Time = 4.6s, Current Processing Latency = 6.18

Time = 0.82: Hey guys today
Time = 1.82: I'm going to show
Time = 2.82: you how to
Time = 3.82: I'm a water
Time = 4.82: damaged laptop First

</div>


<div style="text-align: center;">(a) Video Time: 4.6s</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_117_528_1106_725.jpg" alt="Image" width="80%" />

Video Time = 15.6s, Current Processing Latency = 0.14

Time = 0.8s: hey guys today
Time = 1.0s: I'm going to show
Time = 2.0s: you how to
Time = 3.0s: fix a water
Time = 4.0s: compared laptop first
Time = 5.0s: you're going to need
Time = 6.0s: I'm taking try, and
Time = 7.0s: your laptop then
Time = 8.0s: you're going to
Time = 9.0s: need some water
Time = 10.0s: and a microwave
Time = 11.0s: safe container pour
Time = 12.0s: the water into
Time = 13.0s: the container and
Time = 14.0s: then pour it
Time = 15.0s: over the laptop

</div>


<div style="text-align: center;">(b) Video Time: 15.6s</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_115_750_1106_947.jpg" alt="Image" width="80%" />

Unscrew all the screws

Video Time = 40.8s, Current Processing Latency = 0.11

Time = 0.65: hey guy today
Time = 1.61: I'm going to show
Time = 2.65: you how to
Time = 3.61: fix a water
Time = 4.65: damaged laptop first
Time = 5.65: you're going to need
Time = 6.65: a busting tray and
Time = 7.65: you'll laptop then
Time = 8.65: you'll going to
Time = 9.65: need done water
Time = 10.65: and a microwave
Time = 11.65: safe container pour
Time = 12.65: the water into
Time = 13.65: the container and
Time = 14.65: their pour it
Time = 15.65: make the laptop
Time = 16.65: as well you
Time = 17.65: get the water
Time = 18.65: into all the
Time = 19.65: crevices and
Time = 20.65: then close the
Time = 21.65: laptop and
Time = 22.65: drain out
Time = 23.65: water out
Time = 24.65: of it
Time = 25.65: then open
Time = 26.65: the laptop and
Time = 27.65: get some paper
Time = 28.65: towel and
Time = 29.65: dry time
Time = 30.65: laptop off
Time = 31.65: make sure
Time = 32.65: you get all the
Time = 33.65: water out of it
Time = 34.65: and then dry
Time = 35.65: the back
Time = 36.65: as well
Time = 37.65: then you're going
Time = 38.65: to need a
Time = 39.65: pentalobe screwdriver and

</div>


<div style="text-align: center;">(c) Video Time: 44.0s</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_116_969_1106_1169.jpg" alt="Image" width="80%" />

Video Time = 72.8s, Current Processing Latency = 0.16
Time = 0.05: hey guys today
Time = 1.02: I'm going to show
Time = 2.05: you how to show
Time = 2.05: I go to how to show
Time = 2.05: I get the water
Time = 2.05: I get all the
Time = 4.05: damaged laptop first
Time = 5.05: you're going to need
Time = 6.05: I'm having very much all
Time = 7.05: you'll laptop then
Time = 8.05: you'll going to
Time = 9.05: need some water
Time = 10.05: you and a microwave
Time = 11.05: safe container pour
Time = 12.05: the user write
Time = 13.05: the container and
Time = 14.05: the pour it
Time = 15.05: over the laptop
Time = 16.05: make sure you
Time = 17.05: get the water
Time = 18.05: into all the
Time = 19.05: crevices and
Time = 20.05: then close the laptop and
Time = 21.05: drain out
Time = 22.05: water out
Time = 24.05: of it
Time = 25.05: then open
Time = 26.05: the laptop and
Time = 27.05: get some paper
Time = 28.05: towel and
Time = 29.05: dry the
Time = 30.05: a dry top off
Time = 31.05: make sure
Time = 32.05: you get all the
Time = 33.05: water out of it
Time = 34.05: the dry
Time = 35.05: the dry
Time = 36.05: the back
Time = 37.05: then you're going to need a
Time = 38.05: to need a
Time = 39.05: pentalobe screwdriver and
Time = 40.05: unscrew all
Time = 42.05: on the
Time = 43.05: back of the laptop
Time = 44.05: then open
Time = 45.05: then open
Time = 46.05: the laptop
Time = 47.05: dry it off
Time = 48.05: then get a 40-knot ranger and
Time = 49.05: dry the
Time = 50.05: inside of the
Time = 51.05: inside of the
Time = 52.05: make sure you get all the
Time = 53.05: make sure you
Time = 54.05: get all the
Time = 55.05: water out of
Time = 56.05: it then you're going to need a
Time = 57.05: going to need a
Time = 58.05: some rice and
Time = 59.05: a ziploc bag

</div>


<div style="text-align: center;">(d) Video Time: 72.8s</div>


<div style="text-align: center;">Figure 13. Real-time video commentary demo on unseen YouTube video (115amzVdV44). We give the YouTube title "How To Fix a Water Damaged Laptop" as the prompt.</div>


20