arXiv:2512.21334v2 [cs.CV] 10 Apr 2026

# Streaming Video Instruction Tuning

Jiaer Xia $ ^{1*} $ Peixian Chen $ ^{2*} $ Mengdan Zhang $ ^{2} $ Xing Sun $ ^{2} $ Kaiyang Zhou $ ^{1✉} $

 $ ^{1} $ Hong Kong Baptist University

 $ ^{2} $ Tencent Youtu Lab

https://jiaerxia.github.io/Stream/

https://jiaerxia.github.io/Streamo/

## Abstract

We present Streamo, a real-time streaming video LLM that serves as a general-purpose interactive assistant. Unlike existing online video models that focus narrowly on question answering or captioning, Streamo performs a broad spectrum of streaming video tasks, including real-time narration, action understanding, event captioning, temporal event grounding, and time-sensitive question answering. To develop such versatility, we construct Streamo-Instruct465K, a large-scale instruction-following dataset tailored for streaming video understanding. The dataset covers diverse temporal contexts and multi-task supervision, enabling unified training across heterogeneous streaming tasks. After training end-to-end on the instruction-following dataset through a streamlined pipeline, Streamo exhibits strong temporal reasoning, responsive interaction, and broad generalization across a variety of streaming benchmarks. Extensive experiments show that Streamo bridges the gap between offline video perception models and real-time multimodal assistants, making a step toward unified, intelligent video understanding in continuous video streams.

## 1. Introduction

Recent advances in video large language models (LLMs) [4, 24, 42, 51] have demonstrated remarkable capabilities in analyzing complete, pre-recorded videos, which establish strong baselines for offline video understanding. These models excel at holistic reasoning over long temporal sequences when given static, temporally bounded inputs [20, 55], enabling tasks such as video captioning, summarization, and question answering. However, the requirements of real-time interactive AI assistants are fundamentally different: they must process continuous, unbounded video streams and respond to dynamic instructions as events unfold, often under strict latency constraints.

Existing offline models struggle to meet the demands of the streaming setting because they are designed to process entire clips before producing a single output [33, 39, 43]. In contrast, real-time applications require the model to continuously interpret an incoming video stream, detect when the visual context satisfies a task condition, and decide what information to output at that moment. This introduces two key challenges: 1) handling continuous, unbounded data flow without losing context, and 2) managing variable response timing and granularity across multiple tasks, which may require frame-level or longer-term temporal reasoning. A truly capable streaming video LLM must therefore integrate both task understanding and frame-level decision-making, enabling it to evaluate evolving visual contexts, determine appropriate moments to respond, and generate coherent outputs without delaying or missing critical information.



To address these challenges, recent studies [33, 39, 43] have attempted to extend offline video models for streaming by introducing a separate decision module that predicts response states before invoking the offline model to generate content. While this approach preserves the reasoning capacity of the base model, it creates a trade-off between accuracy and efficiency: lightweight decision modules often lack the capacity to fully understand complex instructions and temporal dependencies, while larger modules substantially increase computational cost and inference latency. Moreover, separating decision-making from response generation prevents tight coupling between perception and response, limiting the model's ability to seamlessly adapt to rapidly changing streaming contexts.

In this work, we propose  $ Stream^{1} $, a real-time streaming video LLM that unifies decision-making and response generation in an end-to-end manner. Instead of relying on an external controller, we embed frame-level response state prediction directly into the model. Specifically, three decision heads—Silence, Standby, and Response—allow the model to continuously monitor the input stream and make fine-grained judgments about when to output. Once a re-

 $ ^{*} $Equal contribution

✗Corresponding author

 $ ^{1} $The letter o in Streamo means ‘omni’, reflecting its multi-task and multi-modal capabilities.

<div style="text-align: center;"><img src="imgs/img_in_image_box_113_147_1104_669.jpg" alt="Image" width="80%" />

The video features a bartender demonstrating how to make a pink cocktail using ingredients like Tahoe Blue Vodka, lemon, mint, and a red mixer.
Narrate the video in real time, updating the description frame-by-frame or moment-by-moment as events unfold.
Man picks up glass.
Man places glass down.
Man picked up a shaker.
Hand shovels ice cubes.
Camera focuses on bottle and shaker.
Pouring liquid into the shaker.
Lemon is cut in half.
Real-time Narration
Locate and pinpoint a sequential series of specific actions or steps in the video.
<Silence>
Man shovels some ice cubes into shaker.
Man pours some Vodka into the shaker.
Man cuts lemon.
Man squeezes lemon.
Detect and summarize each event sequence in the video.
The man begins to prepare the drink, while the woman watches.
He fills a blue shaker tin with ice cubes, followed by pouring Tahoe Blue Vodka into the shaker.
He then cuts lemons in half and squeezes fresh lemon juice into the shaker.
Temporally localize the event: 'Man added vodka to the shaker and squeezed in some lemon juice'. Respond once it has finished and summarize its time period.
<Silence>
What is the man currently holding in his hand.
<Silence>
shaker
<Silence>
gloss
gloss
kniﬁe
squeezer
Time-sensitive QA

</div>


<div style="text-align: center;">Figure 1. An example of multi-task annotation in Streamo-Instruct-465K. Each task is carefully labeled with the corresponding response time boundaries and content, following established annotation standards. The same video is annotated with multiple distinct tasks. The video shown in this example is sourced from ActivityNet $ ^{[5]} $.</div>


sponse state is triggered, the model immediately produces the corresponding textual output, achieving one-pass inference that significantly improves both the accuracy of response timing and the efficiency of real-time generation.

Training Streamo requires high-quality, temporally consistent supervision, yet existing datasets often combine heterogeneous sources with inconsistent annotation standards [15, 17, 18]. These inconsistencies make it difficult for the model to learn precise temporal alignment or multi-task response behaviors. To overcome this problem, we construct Streamo-Instruct-465K, a large-scale, multi-task instruction-following dataset designed specifically for streaming video understanding and interaction. The dataset standardizes three levels of response granularity, provides unified temporal annotations for event boundaries, and covers diverse tasks including real-time narration, action and event captioning, temporal grounding, and time-sensitive question answering. Each video is annotated for multiple tasks, providing consistent guidance that strengthens both instruction-following and temporal reasoning. An example of the annotations is shown in Fig. 1.

Extensive experiments demonstrate that our end-to-end training paradigm effectively converts offline models into online streaming assistants. Streamo outperforms existing online approaches across both streaming and offline benchmarks, exhibiting strong temporal awareness, accurate frame-level decision-making, and robust multitask instruction-following. To further support research in this domain, we also introduce a comprehensive streaming benchmark named Streamo-Bench, which evaluates instruction understanding across diverse interactive tasks.



Our contributions are threehold: 1) We propose a simple and effective end-to-end training framework that converts offline video models into real-time straeming assistants. 2) We introduce a multi-task instruction tuning dataset with unified temporal annotation and fine-grained response supervision. To our knowledge, this is the largest scale instruction tuning dataset for streaming video understanding and interaction. 3) We establish a comprehensive benchmark for streaming video instruction-following and provide strong baseline models for future research. All research resources including code, models, and datasets will be made publicly available.

## 2. Related Work

Video Large Language Models The field of vision foundation models [9, 26, 29, 31] has made remarkable progress in recent years, extending capabilities from static image understanding to more general video comprehension. Building on this foundation, numerous advanced video LLMs have emerged. For example, InternVideo2.5 [44] can pro-

cess videos spanning several hours, while Keye-VL-1.5 [48] demonstrates sophisticated reasoning abilities, effectively performing complex thinking process based on video content. A critical limitation, however, is that these state-of-the-art models operate in an offline fashion, requiring the entire video as input before producing any output. This single-pass approach prevents them from handling continuous video streams, as they lack mechanisms to identify the precise temporal moments for generating responses in ongoing streams.

Streaming Video Understanding To tackle real-time interaction, various methods have been proposed in the literature to turn offline video LLMs into online assistants that can identify the appropriate moment to respond in video streams. For instance, Dispider [33] and StreamBridge [39] employ an auxiliary model to segment a video stream into fixed-length clips before feeding them to an offline model. However, this strategy introduces significant computational overhead in both training and inference and often fails to maintain context during multi-turn interactions. On the other hand, VideoLLM-Online [6] and StreamingVLM [47] train the model in a supervised way to directly predict response timing using a special [EOS] token. However, this approach is limited to real-time narration and cannot balance between silence and response state. To overcome these problems, we propose an end-to-end training framework along with a multi-task instruction-following dataset specifically designed for streaming video understanding and interaction.

Streaming Video Benchmarks OVO-Bench [23] introduces 12 distinct tasks, incorporating tests for a model's ability to proactively respond. Similarly, STREAMBENCH [46] and SVBENCH [49] concentrate on assessing multi-turn conversational abilities within continuous video contexts. A key limitation, however, is their predominant reliance on question-answer (QA) style setups—typically requiring the model to choose an answer from given options—which does not adequately assess broader instruction-following abilities such as event grounding and captioning. Motivated by the goal that streaming video models should evolve into real-time AI assistants, we introduce Streamo-Bench, a benchmark designed to probe a model's perceptual and responsive capabilities across diverse instructions, moving beyond the constraints of traditional QA-based evaluation.

## 3. Streamo: Architecture and Training

### 3.1. Preliminaries

Traditional video understanding models [2, 7] follow an offline paradigm where the complete video V, question Q, and answer A are processed using a single-turn format. Formally, given a video  $ V = \{v_1, v_2, ..., v_T\} $ of length T and a question Q, the model directly generates an answer A. This approach assumes that the entire video is accessible before inference begins, which is impractical for real-time streaming scenarios where video frames arrive sequentially.



In contrast to offline settings, streaming video understanding processes video content as it arrives in a continuous stream. The model must make decisions based on partial observations  $ V_{:t} = v_1, v_2, ..., v_t $, where  $ t \leq T_t $ meaning that the model does not have access to future frames. This temporal constraint requires fundamental changes to both the data structure and training paradigm.

### 3.2. Data Structure

To simulate streaming scenarios during training, we reformulate the single-turn offline format into a multi-turn dialogue structure. Specifically, a complete video V is temporally segmented into N contiguous segments:

 $$ V=\{V^{(1)},V^{(2)},...,V^{(N)}\} $$ 

where  $ V^{(i)} $ denotes the i-th video segment. Each segment is explicitly annotated with temporal boundaries using special markers, e.g.,  $ <2s-3s> $, to encode temporal information. The multi-turn dialogue is constructed as:

 $$ \mathcal{D}=\{(V^{(1)},R^{(1)}),(V^{(2)},R^{(2)}),...,(V^{(N)},R^{(N)})\} $$ 

where  $ R^{(i)} $ denotes the response at turn i. Questions and answers are strategically inserted at appropriate turns based on the dataset characteristics and task requirements.

To enable efficient parallel training while maintaining compatibility with standard supervised fine-tuning paradigms, we convert decision process into predictions for the following state tokens:

<Silence>: The model remains silent and continues processing incoming frames.

<Standby>: The model detects relevant video input and waits for complete information.

<Response>: The model receives enough information and will generate a response.

This design empowers the model with frame-level decision-making capabilities while maintaining the next-token prediction framework. As illustrated in Fig. 2, three discrete response states are directly integrated into the normal token prediction process: the model outputs <Standby> upon detecting relevant input and <Response> when it is ready to answer. A training example is shown in Tab. 1. With this multi-turn dialogue training format, we can simulate realistic streaming video interactions and pose questions at any point in time.

### 3.3. Training

The multi-turn streaming format introduces severe class imbalance among the three response states. In typical streaming scenarios, <Silence> tokens dominate the distribution

<div style="text-align: center;">Table 1. The format of a multi-turn dialogue.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td colspan="2">SYSTEM PROMPT</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>USER</td><td style='text-align: center; word-wrap: break-word;'>&lt;0s-1s&gt;&lt;video&gt;</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ASSISTANT</td><td style='text-align: center; word-wrap: break-word;'>&lt;Silence&gt;</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>USER</td><td style='text-align: center; word-wrap: break-word;'>&lt;1s-2s&gt;&lt;video&gt;
Notify me when the light turns green.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ASSISTANT</td><td style='text-align: center; word-wrap: break-word;'>&lt;Silence&gt;</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>USER</td><td style='text-align: center; word-wrap: break-word;'>&lt;2s-3s&gt;&lt;video&gt;</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ASSISTANT</td><td style='text-align: center; word-wrap: break-word;'>&lt;Silence&gt;</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>USER</td><td style='text-align: center; word-wrap: break-word;'>&lt;3s-4s&gt;&lt;video&gt;</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ASSISTANT</td><td style='text-align: center; word-wrap: break-word;'>&lt;Standby&gt;</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>USER</td><td style='text-align: center; word-wrap: break-word;'>&lt;4s-5s&gt;&lt;video&gt;</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ASSISTANT</td><td style='text-align: center; word-wrap: break-word;'>&lt;Response&gt; The light just turned green.</td></tr></table>

(often more than 80% of the time), while <Response> tokens are sparse. This imbalance biases the model toward remaining silent, making it difficult to learn response timing.

To mitigate this, we apply focal weighting [25] specifically to the three special state tokens. Let  $ \mathcal{S} = \{s_{silence}, s_{standby}, s_{response}\} $ denote the special token for the three states. For each prediction, we compute a focal weight that emphasizes hard examples:

 $$ w_{\mathrm{f o c a l}}(x_{i})=(1-p_{c_{i}})^{\gamma}, $$ 

where  $ x_i $ represents the input features at position  $ i $, and  $ p_{c_i} $ is the predicted probability for the true class  $ c_i $ at position  $ i $.  $ \gamma \geq 0 $ is the focusing parameter that controls the rate at which easy examples are down-weighted. To further balance the rare classes, we introduce frequency-based alpha weights. For each special token  $ k \in \mathcal{S} $ with count  $ n_k $ in the current batch:

 $$ \alpha_{k}=\frac{1}{|\mathcal{S}|}\cdot\frac{\sum_{j\in\mathcal{S}}n_{j}}{n_{k}}, $$ 

where  $ |S| = 3 $ is the number of special states. This assigns larger weights to less frequent special tokens.

The final loss combines the focal weighting and frequency balancing:

 $$ \mathcal{L}_{i}=\left\{\begin{aligned}{}&{{}\alpha_{t_{i}}w_{\operatorname{f o c a l}}(i)\mathcal{L}_{\operatorname{C E}}(i,t_{i}),}&{}&{{}t_{i}\in\mathcal{S}}\\ {}&{{}\mathcal{L}_{\operatorname{C E}}(i,t_{i}),}&{}&{{}\operatorname{o t h e r w i s e}}\\ \end{aligned}\right., $$ 

The two weighting mechanisms are computed independently and multiplied into the cross-entropy loss. Together, they focus the model on both challenging and infrequent tokens, improving learning of response timing despite severe

<div style="text-align: center;"><img src="imgs/img_in_image_box_638_145_1104_422.jpg" alt="Image" width="38%" />

<Silence> <Silence>
<Standby> <Response> He is swimming in the ocean.

Streamo

What is the man doing?

Relevant frame

</div>


<div style="text-align: center;">Figure 2. Streamo's architecture. Streaming video data is organized into an interleaved, multi-turn dialogue structure that directly integrates a response-state token into the data sequence, enabling end-to-end parallel training.</div>


class imbalance in streaming data. The  $ \mathcal{L}_{CE} $ is the standard cross-entropy loss:

 $$ \mathcal{L}_{\mathrm{C E}}(i,t_{i})=-\log p_{t_{i}}=\log\sum_{j=1}^{|\mathcal{V}|}e^{z_{i,j}}-z_{i,t_{i}}, $$ 

where  $ z_{i,j} $ is the logit for token  $ j $ at position  $ i $ and  $ |\mathcal{V}| $ is the vocabulary size. This computes the negative log-likelihood of the true token. The total loss averages over all valid (non-masked) positions indicated by  $ \mathcal{M} $:

 $$ \mathcal{L}_{total}=\frac{1}{|\mathcal{M}|}\sum_{i\in\mathcal{M}}\mathcal{L}_{i}. $$ 

This ensures that the loss is not affected by sequence length variations across examples in the batch.

## 4. Streamo-Instruct-465K

### 4.1. Data Construction

To provide clear supervision for each round of response decisions, we re-annotated a large-scale training set with detailed temporal boundary labels based on the existing open-source video datasets. We predefined multiple tasks spanning different response granularities, assigning each video several types of task annotations. This approach offers several advantages. First, a unified annotation protocol is applied across datasets, avoiding the inconsistencies and biases that arise when naively mixing datasets with heterogeneous labeling standards. Additionally, each video carries multiple task types with clearly delineated response boundaries, enabling the model to better perceive and understand varying task requirements, develop robust instruction-following capabilities, and execute a range of real-time response tasks. Below, we detail the annotation protocol for each task.

<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Category</th><th style='text-align: center;'>Percentage (%)</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>Time-sensitive QA</td><td style='text-align: center;'>34.8</td></tr>
    <tr><td style='text-align: center;'>Event Grounding</td><td style='text-align: center;'>26.3</td></tr>
    <tr><td style='text-align: center;'>Narration</td><td style='text-align: center;'>12.7</td></tr>
    <tr><td style='text-align: center;'>Offline QA</td><td style='text-align: center;'>13.8</td></tr>
    <tr><td style='text-align: center;'>Total Samples</td><td style='text-align: center;'>**465.8**</td></tr>
  </tbody>
</table>

<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Duration Range</th><th style='text-align: center;'>Number of Videos</th><th style='text-align: center;'>Percentage</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>0-30s</td><td style='text-align: center;'>68273</td><td style='text-align: center;'>50.25%</td></tr>
    <tr><td style='text-align: center;'>30-60s</td><td style='text-align: center;'>19153</td><td style='text-align: center;'>14.1%</td></tr>
    <tr><td style='text-align: center;'>60-120s</td><td style='text-align: center;'>21834</td><td style='text-align: center;'>16.07%</td></tr>
    <tr><td style='text-align: center;'>120-240s</td><td style='text-align: center;'>20529</td><td style='text-align: center;'>15.11%</td></tr>
    <tr><td style='text-align: center;'>240s+</td><td style='text-align: center;'>6086</td><td style='text-align: center;'>4.48%</td></tr>
  </tbody>
</table>

<div style="text-align: center;">Figure 3. Dataset distribution overview. Left: task distribution; Right: video duration distribution.</div>


Real-time Narration This task performs real-time commentary over video, requiring second-by-second descriptions that capture fine-grained visual changes. The annotation protocol is: 1) segment each video at one-second intervals; 2) for every adjacent pair of one-second segments (i.e., a two-second window), use Qwen2.5-VL-72B [3] to describe the changes observed between them; 3) concatenate the per-second outputs and send the full narration to GLM-4.5 [50] for post-processing to remove repetitions and redundancies, smooth transitions, and ensure coherent, context-aware narration.

Event Caption This task is similar to standard video captioning but requires the model to detect event boundaries and provide the corresponding caption when an event ends. To construct supervision: 1) generate segment-level captions with the ARC-Hunyuan-Video-7B [16] model; 2) temporally ground each caption using the same model; 3) retain only those videos in which all segment captions have mutually consistent, overlapping time spans that align with the original output. This yields two benefits: it filters out erroneous, noisy data and produces samples with sharper, more explicit event boundaries, enabling clearer supervision.

Action Caption This task mirrors event captioning but narrows the focus from dense events to discrete actions or procedural steps. We reuse the event-caption pipeline and augment it with action-oriented prompts and targeted filtering. This produces cleaner, step-level supervision with sharper action delineation.

Event Grounding The grounding annotation is similar to the offline setup, where each sample pairs an event caption with its corresponding temporal span. The key difference in the online setting is that the caption is provided in advance, and the model must continuously monitor the subsequent video stream to detect the specified event and localize its occurrence in time. We randomly sample captions from the event-caption annotations, rewrite them for grounding, and integrate existing datasets to broaden coverage and improve robustness.



Time-sensitive QA This task targets questions whose correct answers change over time in a dynamic video stream. To construct supervision: 1) process each video with GLM-4.5V [38] model to detect change points across multiple aspects—object attributes (e.g., color, size, state), spatial positions, actions and interactions, counts, and scene or context shifts; 2) generate question-answer pairs from these variations by posing a single, unified question and providing diverse, time-specific answers at the corresponding time points.

### 4.2. Statistics

Using a unified annotation standard and protocol, we labeled and curated a total of 400K valid samples and additionally merged offline video QA data from the LLaVA-Video [53] dataset, culminating in Streamo-Instruct-465K, and the task distribution is shown on the left of Fig. 3. We integrated multiple open-source video datasets as sources, including Koala [41], LLaVA-Video [53], ActivityNet [5], QVHighlight [32], YouCook2 [57], HACS [54], EgoTimeQA [11], DiDeMo [1], and COIN [35], yielding 135,875 videos in total. The distribution of video durations is shown on the right of Fig. 3.

## 5. Experiments

### 5.1. Models and Datasets

To assess the effectiveness of our training strategy, we adopt Qwen2.5-VL [3] as our base model, across both 3B and 7B model size. Meanwhile, we additionally conduct experiments based on several existing state-of-the-art offline

<div style="text-align: center;">Table 2. Comparison with state-of-the-art on OVO-Bench. 'Streamo Framework' denotes adapting offline models to the online setting using our training framework. ET-Instruct-3B is trained with ET-Instruct-164K and  $ {}^{\dagger} $ indicates LLaVA-Video data is added as offline support.  $ ^{*} $ means the model is trained at 1 fps and evaluated at 2 fps.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Model</td><td rowspan="2"># Frames</td><td colspan="6">Real-Time Visual Perception</td><td colspan="4">Backward Tracing</td><td colspan="4">Forward Active Responding</td><td style='text-align: center; word-wrap: break-word;'>Overall Avg.</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>OCR</td><td style='text-align: center; word-wrap: break-word;'>ACR</td><td style='text-align: center; word-wrap: break-word;'>ATR</td><td style='text-align: center; word-wrap: break-word;'>STU</td><td style='text-align: center; word-wrap: break-word;'>FPD</td><td style='text-align: center; word-wrap: break-word;'>OJR</td><td style='text-align: center; word-wrap: break-word;'>Avg.</td><td style='text-align: center; word-wrap: break-word;'>EPM</td><td style='text-align: center; word-wrap: break-word;'>ASI</td><td style='text-align: center; word-wrap: break-word;'>HLD</td><td style='text-align: center; word-wrap: break-word;'>Avg.</td><td style='text-align: center; word-wrap: break-word;'>REC</td><td style='text-align: center; word-wrap: break-word;'>SSR</td><td style='text-align: center; word-wrap: break-word;'>CRR</td><td style='text-align: center; word-wrap: break-word;'>Avg.</td><td style='text-align: center; word-wrap: break-word;'>Overall Avg.</td></tr><tr><td colspan="18">Open-source Offline Models</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2-VL-72B [40]</td><td style='text-align: center; word-wrap: break-word;'>64</td><td style='text-align: center; word-wrap: break-word;'>65.77</td><td style='text-align: center; word-wrap: break-word;'>60.55</td><td style='text-align: center; word-wrap: break-word;'>69.83</td><td style='text-align: center; word-wrap: break-word;'>51.69</td><td style='text-align: center; word-wrap: break-word;'>69.31</td><td style='text-align: center; word-wrap: break-word;'>54.35</td><td style='text-align: center; word-wrap: break-word;'>61.92</td><td style='text-align: center; word-wrap: break-word;'>52.53</td><td style='text-align: center; word-wrap: break-word;'>60.81</td><td style='text-align: center; word-wrap: break-word;'>57.53</td><td style='text-align: center; word-wrap: break-word;'>56.95</td><td style='text-align: center; word-wrap: break-word;'>38.83</td><td style='text-align: center; word-wrap: break-word;'>64.07</td><td style='text-align: center; word-wrap: break-word;'>45</td><td style='text-align: center; word-wrap: break-word;'>49.3</td><td style='text-align: center; word-wrap: break-word;'>56.27</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-Video-7B [53]</td><td style='text-align: center; word-wrap: break-word;'>64</td><td style='text-align: center; word-wrap: break-word;'>69.13</td><td style='text-align: center; word-wrap: break-word;'>58.72</td><td style='text-align: center; word-wrap: break-word;'>68.83</td><td style='text-align: center; word-wrap: break-word;'>49.44</td><td style='text-align: center; word-wrap: break-word;'>74.26</td><td style='text-align: center; word-wrap: break-word;'>59.78</td><td style='text-align: center; word-wrap: break-word;'>63.52</td><td style='text-align: center; word-wrap: break-word;'>56.23</td><td style='text-align: center; word-wrap: break-word;'>57.43</td><td style='text-align: center; word-wrap: break-word;'>7.53</td><td style='text-align: center; word-wrap: break-word;'>40.4</td><td style='text-align: center; word-wrap: break-word;'>34.1</td><td style='text-align: center; word-wrap: break-word;'>69.95</td><td style='text-align: center; word-wrap: break-word;'>60.42</td><td style='text-align: center; word-wrap: break-word;'>54.82</td><td style='text-align: center; word-wrap: break-word;'>52.91</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-OneVision-7B [21]</td><td style='text-align: center; word-wrap: break-word;'>64</td><td style='text-align: center; word-wrap: break-word;'>66.44</td><td style='text-align: center; word-wrap: break-word;'>57.8</td><td style='text-align: center; word-wrap: break-word;'>73.28</td><td style='text-align: center; word-wrap: break-word;'>53.37</td><td style='text-align: center; word-wrap: break-word;'>71.29</td><td style='text-align: center; word-wrap: break-word;'>61.96</td><td style='text-align: center; word-wrap: break-word;'>64.02</td><td style='text-align: center; word-wrap: break-word;'>54.21</td><td style='text-align: center; word-wrap: break-word;'>55.41</td><td style='text-align: center; word-wrap: break-word;'>21.51</td><td style='text-align: center; word-wrap: break-word;'>43.71</td><td style='text-align: center; word-wrap: break-word;'>25.64</td><td style='text-align: center; word-wrap: break-word;'>67.09</td><td style='text-align: center; word-wrap: break-word;'>58.75</td><td style='text-align: center; word-wrap: break-word;'>50.5</td><td style='text-align: center; word-wrap: break-word;'>52.74</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2-VL-7B [40]</td><td style='text-align: center; word-wrap: break-word;'>64</td><td style='text-align: center; word-wrap: break-word;'>60.4</td><td style='text-align: center; word-wrap: break-word;'>50.46</td><td style='text-align: center; word-wrap: break-word;'>56.03</td><td style='text-align: center; word-wrap: break-word;'>47.19</td><td style='text-align: center; word-wrap: break-word;'>66.34</td><td style='text-align: center; word-wrap: break-word;'>55.43</td><td style='text-align: center; word-wrap: break-word;'>55.98</td><td style='text-align: center; word-wrap: break-word;'>47.81</td><td style='text-align: center; word-wrap: break-word;'>35.48</td><td style='text-align: center; word-wrap: break-word;'>56.08</td><td style='text-align: center; word-wrap: break-word;'>46.46</td><td style='text-align: center; word-wrap: break-word;'>31.66</td><td style='text-align: center; word-wrap: break-word;'>65.82</td><td style='text-align: center; word-wrap: break-word;'>48.75</td><td style='text-align: center; word-wrap: break-word;'>48.74</td><td style='text-align: center; word-wrap: break-word;'>50.39</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>InternVL-V2-8B [10]</td><td style='text-align: center; word-wrap: break-word;'>64</td><td style='text-align: center; word-wrap: break-word;'>67.11</td><td style='text-align: center; word-wrap: break-word;'>60.55</td><td style='text-align: center; word-wrap: break-word;'>63.79</td><td style='text-align: center; word-wrap: break-word;'>46.07</td><td style='text-align: center; word-wrap: break-word;'>68.32</td><td style='text-align: center; word-wrap: break-word;'>56.52</td><td style='text-align: center; word-wrap: break-word;'>60.39</td><td style='text-align: center; word-wrap: break-word;'>48.15</td><td style='text-align: center; word-wrap: break-word;'>57.43</td><td style='text-align: center; word-wrap: break-word;'>24.73</td><td style='text-align: center; word-wrap: break-word;'>43.44</td><td style='text-align: center; word-wrap: break-word;'>26.5</td><td style='text-align: center; word-wrap: break-word;'>59.14</td><td style='text-align: center; word-wrap: break-word;'>54.14</td><td style='text-align: center; word-wrap: break-word;'>46.6</td><td style='text-align: center; word-wrap: break-word;'>50.15</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LongVU-7B [34]</td><td style='text-align: center; word-wrap: break-word;'>1fps</td><td style='text-align: center; word-wrap: break-word;'>53.69</td><td style='text-align: center; word-wrap: break-word;'>53.21</td><td style='text-align: center; word-wrap: break-word;'>62.93</td><td style='text-align: center; word-wrap: break-word;'>47.75</td><td style='text-align: center; word-wrap: break-word;'>68.32</td><td style='text-align: center; word-wrap: break-word;'>59.78</td><td style='text-align: center; word-wrap: break-word;'>57.61</td><td style='text-align: center; word-wrap: break-word;'>40.74</td><td style='text-align: center; word-wrap: break-word;'>59.46</td><td style='text-align: center; word-wrap: break-word;'>4.84</td><td style='text-align: center; word-wrap: break-word;'>35.01</td><td style='text-align: center; word-wrap: break-word;'>12.18</td><td style='text-align: center; word-wrap: break-word;'>69.48</td><td style='text-align: center; word-wrap: break-word;'>60.83</td><td style='text-align: center; word-wrap: break-word;'>47.5</td><td style='text-align: center; word-wrap: break-word;'>46.71</td></tr><tr><td colspan="18">Open-source Online Models</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Flash-VStream-7B [52]</td><td style='text-align: center; word-wrap: break-word;'>1fps</td><td style='text-align: center; word-wrap: break-word;'>24.16</td><td style='text-align: center; word-wrap: break-word;'>29.36</td><td style='text-align: center; word-wrap: break-word;'>28.45</td><td style='text-align: center; word-wrap: break-word;'>33.71</td><td style='text-align: center; word-wrap: break-word;'>25.74</td><td style='text-align: center; word-wrap: break-word;'>28.8</td><td style='text-align: center; word-wrap: break-word;'>28.37</td><td style='text-align: center; word-wrap: break-word;'>39.06</td><td style='text-align: center; word-wrap: break-word;'>37.16</td><td style='text-align: center; word-wrap: break-word;'>5.91</td><td style='text-align: center; word-wrap: break-word;'>27.38</td><td style='text-align: center; word-wrap: break-word;'>8.02</td><td style='text-align: center; word-wrap: break-word;'>67.25</td><td style='text-align: center; word-wrap: break-word;'>60</td><td style='text-align: center; word-wrap: break-word;'>45.09</td><td style='text-align: center; word-wrap: break-word;'>33.61</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLM-online-8B [6]</td><td style='text-align: center; word-wrap: break-word;'>2fps</td><td style='text-align: center; word-wrap: break-word;'>8.05</td><td style='text-align: center; word-wrap: break-word;'>23.85</td><td style='text-align: center; word-wrap: break-word;'>12.07</td><td style='text-align: center; word-wrap: break-word;'>14.04</td><td style='text-align: center; word-wrap: break-word;'>45.54</td><td style='text-align: center; word-wrap: break-word;'>21.2</td><td style='text-align: center; word-wrap: break-word;'>20.79</td><td style='text-align: center; word-wrap: break-word;'>22.22</td><td style='text-align: center; word-wrap: break-word;'>18.8</td><td style='text-align: center; word-wrap: break-word;'>12.18</td><td style='text-align: center; word-wrap: break-word;'>17.73</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Dispider-7B [33]</td><td style='text-align: center; word-wrap: break-word;'>1fps</td><td style='text-align: center; word-wrap: break-word;'>57.72</td><td style='text-align: center; word-wrap: break-word;'>49.54</td><td style='text-align: center; word-wrap: break-word;'>62.07</td><td style='text-align: center; word-wrap: break-word;'>44.94</td><td style='text-align: center; word-wrap: break-word;'>61.39</td><td style='text-align: center; word-wrap: break-word;'>51.63</td><td style='text-align: center; word-wrap: break-word;'>54.55</td><td style='text-align: center; word-wrap: break-word;'>48.48</td><td style='text-align: center; word-wrap: break-word;'>55.41</td><td style='text-align: center; word-wrap: break-word;'>4.3</td><td style='text-align: center; word-wrap: break-word;'>36.06</td><td style='text-align: center; word-wrap: break-word;'>18.05</td><td style='text-align: center; word-wrap: break-word;'>37.36</td><td style='text-align: center; word-wrap: break-word;'>48.75</td><td style='text-align: center; word-wrap: break-word;'>34.72</td><td style='text-align: center; word-wrap: break-word;'>41.78</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ViSpeak-7B [14]</td><td style='text-align: center; word-wrap: break-word;'>1fps</td><td style='text-align: center; word-wrap: break-word;'>75.17</td><td style='text-align: center; word-wrap: break-word;'>58.72</td><td style='text-align: center; word-wrap: break-word;'>71.55</td><td style='text-align: center; word-wrap: break-word;'>51.12</td><td style='text-align: center; word-wrap: break-word;'>74.26</td><td style='text-align: center; word-wrap: break-word;'>66.85</td><td style='text-align: center; word-wrap: break-word;'>66.28</td><td style='text-align: center; word-wrap: break-word;'>59.93</td><td style='text-align: center; word-wrap: break-word;'>48.65</td><td style='text-align: center; word-wrap: break-word;'>63.98</td><td style='text-align: center; word-wrap: break-word;'>57.52</td><td style='text-align: center; word-wrap: break-word;'>33.81</td><td style='text-align: center; word-wrap: break-word;'>68.52</td><td style='text-align: center; word-wrap: break-word;'>60.42</td><td style='text-align: center; word-wrap: break-word;'>54.25</td><td style='text-align: center; word-wrap: break-word;'>61.08</td></tr><tr><td colspan="18">Streamo Framework</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ET-Instruct-3B [28]</td><td style='text-align: center; word-wrap: break-word;'>1fps</td><td style='text-align: center; word-wrap: break-word;'>65.10</td><td style='text-align: center; word-wrap: break-word;'>35.78</td><td style='text-align: center; word-wrap: break-word;'>56.90</td><td style='text-align: center; word-wrap: break-word;'>35.39</td><td style='text-align: center; word-wrap: break-word;'>24.75</td><td style='text-align: center; word-wrap: break-word;'>60.87</td><td style='text-align: center; word-wrap: break-word;'>46.47</td><td style='text-align: center; word-wrap: break-word;'>41.81</td><td style='text-align: center; word-wrap: break-word;'>35.14</td><td style='text-align: center; word-wrap: break-word;'>8.6</td><td style='text-align: center; word-wrap: break-word;'>28.52</td><td style='text-align: center; word-wrap: break-word;'>20.06</td><td style='text-align: center; word-wrap: break-word;'>52.31</td><td style='text-align: center; word-wrap: break-word;'>67.50</td><td style='text-align: center; word-wrap: break-word;'>46.62</td><td style='text-align: center; word-wrap: break-word;'>40.54</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ET-Instruct-3B $ ^{\dagger} $ [28]</td><td style='text-align: center; word-wrap: break-word;'>1fps</td><td style='text-align: center; word-wrap: break-word;'>71.14</td><td style='text-align: center; word-wrap: break-word;'>50.46</td><td style='text-align: center; word-wrap: break-word;'>67.24</td><td style='text-align: center; word-wrap: break-word;'>37.08</td><td style='text-align: center; word-wrap: break-word;'>60.40</td><td style='text-align: center; word-wrap: break-word;'>60.33</td><td style='text-align: center; word-wrap: break-word;'>57.78</td><td style='text-align: center; word-wrap: break-word;'>48.82</td><td style='text-align: center; word-wrap: break-word;'>48.56</td><td style='text-align: center; word-wrap: break-word;'>11.29</td><td style='text-align: center; word-wrap: break-word;'>36.22</td><td style='text-align: center; word-wrap: break-word;'>13.68</td><td style='text-align: center; word-wrap: break-word;'>48.62</td><td style='text-align: center; word-wrap: break-word;'>60.00</td><td style='text-align: center; word-wrap: break-word;'>40.77</td><td style='text-align: center; word-wrap: break-word;'>44.92</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Streamo-3B</td><td style='text-align: center; word-wrap: break-word;'>1fps</td><td style='text-align: center; word-wrap: break-word;'>78.52</td><td style='text-align: center; word-wrap: break-word;'>52.29</td><td style='text-align: center; word-wrap: break-word;'>67.24</td><td style='text-align: center; word-wrap: break-word;'>44.38</td><td style='text-align: center; word-wrap: break-word;'>55.45</td><td style='text-align: center; word-wrap: break-word;'>71.20</td><td style='text-align: center; word-wrap: break-word;'>61.51</td><td style='text-align: center; word-wrap: break-word;'>51.18</td><td style='text-align: center; word-wrap: break-word;'>57.43</td><td style='text-align: center; word-wrap: break-word;'>16.67</td><td style='text-align: center; word-wrap: break-word;'>41.76</td><td style='text-align: center; word-wrap: break-word;'>27.94</td><td style='text-align: center; word-wrap: break-word;'>50.72</td><td style='text-align: center; word-wrap: break-word;'>82.5</td><td style='text-align: center; word-wrap: break-word;'>53.72</td><td style='text-align: center; word-wrap: break-word;'>52.33</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Streamo-7B</td><td style='text-align: center; word-wrap: break-word;'>1fps</td><td style='text-align: center; word-wrap: break-word;'>79.19</td><td style='text-align: center; word-wrap: break-word;'>57.80</td><td style='text-align: center; word-wrap: break-word;'>75.00</td><td style='text-align: center; word-wrap: break-word;'>49.44</td><td style='text-align: center; word-wrap: break-word;'>64.36</td><td style='text-align: center; word-wrap: break-word;'>70.11</td><td style='text-align: center; word-wrap: break-word;'>65.98</td><td style='text-align: center; word-wrap: break-word;'>54.55</td><td style='text-align: center; word-wrap: break-word;'>52.03</td><td style='text-align: center; word-wrap: break-word;'>31.72</td><td style='text-align: center; word-wrap: break-word;'>46.10</td><td style='text-align: center; word-wrap: break-word;'>29.96</td><td style='text-align: center; word-wrap: break-word;'>51.03</td><td style='text-align: center; word-wrap: break-word;'>83.33</td><td style='text-align: center; word-wrap: break-word;'>54.77</td><td style='text-align: center; word-wrap: break-word;'>55.61</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Streamo-7B</td><td style='text-align: center; word-wrap: break-word;'>2fps $ ^{*} $</td><td style='text-align: center; word-wrap: break-word;'>77.18</td><td style='text-align: center; word-wrap: break-word;'>66.06</td><td style='text-align: center; word-wrap: break-word;'>76.72</td><td style='text-align: center; word-wrap: break-word;'>45.51</td><td style='text-align: center; word-wrap: break-word;'>66.34</td><td style='text-align: center; word-wrap: break-word;'>72.83</td><td style='text-align: center; word-wrap: break-word;'>67.44</td><td style='text-align: center; word-wrap: break-word;'>55.56</td><td style='text-align: center; word-wrap: break-word;'>58.11</td><td style='text-align: center; word-wrap: break-word;'>33.87</td><td style='text-align: center; word-wrap: break-word;'>49.18</td><td style='text-align: center; word-wrap: break-word;'>30.84</td><td style='text-align: center; word-wrap: break-word;'>57.55</td><td style='text-align: center; word-wrap: break-word;'>82.5</td><td style='text-align: center; word-wrap: break-word;'>56.96</td><td style='text-align: center; word-wrap: break-word;'>57.86</td></tr></table>

models, including Qwen3-VL [37], and InternVL-3 [58], to demonstrate the compatibility of our framework; these results are presented in the Supplementary material. In addition to training on our proposed Streamo-Instruct-465K dataset, we also compare against ET-Instruct-164K [28], a large-scale instruction-tuning dataset with rich temporal information that has been widely used in prior work to train online video models. To enable a fairer comparison with Streamo-Instruct-465K, we also report results on a mixed dataset comprising ET-Instruct-164K and LLaVA-Video.

### 5.2. Benchmarks

We evaluated our model across three dimensions of benchmarks: Online, Offline, and Stream Instruction. For the online setting, we adopted OVO-Bench [23], which covers three temporal perception modes, including real-time, backward, and forward, and also spans a total of 12 subtasks. The offline evaluation used standard general video understanding benchmarks, including the short-video benchmarks MVBench [22] and TempCompass [27], as well as the long-video benchmarks VideoMME [12] and LongVideoBench [45], providing a comprehensive assessment of capabilities. In addition, to assess multi-instruction following in an online context, we constructed StreamoBench, which includes 300 videos and 3,000 instruction tasks. Each video is paired with tasks of varying temporal scopes and granularities to measure the model's adherence to instructions, providing an important metric for building a reliable real-time AI assistant. Detailed information for StreamoBench is given in the Supplementary material.



### 5.3. Implementation Details

Across all models, we use a unified training setup. Full parameter tuning is applied with the vision encoder frozen, and only the connector and the LLM will be updated. Training runs for a single epoch with a batch size of 512 and a learning rate of  $ 1 \times 10^{-5} $. For multi-turn dialogue construction, each video is split into turns of one second, and frames are sampled at 1 fps. The hyperparameter gamma in Eq. (3) is set to 2. In experiments that include LLaVA-Video, we restrict the training data to the same subset used by Streamo-Instruct-465K to ensure a direct and fair comparison.

### 5.4. Main Results

Comparison with SOTA on Online Video Benchmarks

The main results are shown in Tab. 2. Using the Streamo framework, we train the models with ET-Instruct and Streamo-Instruct datasets and compare their performance to currently available open-source offline and online models. The key findings are as follows: 1) Streamo significantly outperforms SOTA. It is clear that our proposed Streamo-7B exceeds the previous SOTA, Dispider, by +13.83% on average performance. Moreover, we observe that the model trained at 1 fps can be directly evaluated

<div style="text-align: center;">Table 3. Results on offline video benchmarks. The table compares converted online models with their original offline base models and SOTA models. Numbers in parentheses denote performance differences from the corresponding offline models.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Model</td><td style='text-align: center; word-wrap: break-word;'>OVO Real-Time</td><td style='text-align: center; word-wrap: break-word;'>OVO Backward</td><td style='text-align: center; word-wrap: break-word;'>MVBench</td><td style='text-align: center; word-wrap: break-word;'>TempCompass</td><td style='text-align: center; word-wrap: break-word;'>VideoMME</td><td style='text-align: center; word-wrap: break-word;'>LongVideoBench</td><td style='text-align: center; word-wrap: break-word;'>Avg</td></tr><tr><td colspan="8">Proprietary Models</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Gemini-1.5-pro [36]</td><td style='text-align: center; word-wrap: break-word;'>69.3</td><td style='text-align: center; word-wrap: break-word;'>62.5</td><td style='text-align: center; word-wrap: break-word;'>60.5</td><td style='text-align: center; word-wrap: break-word;'>67.1</td><td style='text-align: center; word-wrap: break-word;'>75.0</td><td style='text-align: center; word-wrap: break-word;'>64.0</td><td style='text-align: center; word-wrap: break-word;'>66.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>GPT-4o [19]</td><td style='text-align: center; word-wrap: break-word;'>64.5</td><td style='text-align: center; word-wrap: break-word;'>60.8</td><td style='text-align: center; word-wrap: break-word;'>64.6</td><td style='text-align: center; word-wrap: break-word;'>70.9</td><td style='text-align: center; word-wrap: break-word;'>71.9</td><td style='text-align: center; word-wrap: break-word;'>66.7</td><td style='text-align: center; word-wrap: break-word;'>66.6</td></tr><tr><td colspan="8">Open-source Online Models</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Flash-VStream-7B [52]</td><td style='text-align: center; word-wrap: break-word;'>28.4</td><td style='text-align: center; word-wrap: break-word;'>27.4</td><td style='text-align: center; word-wrap: break-word;'>61.2</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>61.2</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLM-online-8B [6]</td><td style='text-align: center; word-wrap: break-word;'>20.8</td><td style='text-align: center; word-wrap: break-word;'>17.7</td><td style='text-align: center; word-wrap: break-word;'>33.9</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>26.9</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Dispider-7B [33]</td><td style='text-align: center; word-wrap: break-word;'>54.6</td><td style='text-align: center; word-wrap: break-word;'>36.1</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>57.2</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>StreamingVLM-7B [47]</td><td style='text-align: center; word-wrap: break-word;'>62.0</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>69.2</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>65.1</td><td style='text-align: center; word-wrap: break-word;'>59.0</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td colspan="8">Streamo Framework</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-VL-3B [3]</td><td style='text-align: center; word-wrap: break-word;'>54.6</td><td style='text-align: center; word-wrap: break-word;'>37.8</td><td style='text-align: center; word-wrap: break-word;'>67.0</td><td style='text-align: center; word-wrap: break-word;'>64.4</td><td style='text-align: center; word-wrap: break-word;'>61.5</td><td style='text-align: center; word-wrap: break-word;'>54.2</td><td style='text-align: center; word-wrap: break-word;'>56.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ET-Instruct-3B [28]</td><td style='text-align: center; word-wrap: break-word;'>46.5 (-8.1)</td><td style='text-align: center; word-wrap: break-word;'>28.6 (-9.2)</td><td style='text-align: center; word-wrap: break-word;'>65.8 (-1.2)</td><td style='text-align: center; word-wrap: break-word;'>60.3 (-4.1)</td><td style='text-align: center; word-wrap: break-word;'>56.6 (-4.9)</td><td style='text-align: center; word-wrap: break-word;'>51.2 (-3.0)</td><td style='text-align: center; word-wrap: break-word;'>51.5 (-5.1)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ET-Instruct-3B $ ^{\dagger} $ [28]</td><td style='text-align: center; word-wrap: break-word;'>57.8 (+3.2)</td><td style='text-align: center; word-wrap: break-word;'>36.2 (-1.6)</td><td style='text-align: center; word-wrap: break-word;'>68.1 (+1.1)</td><td style='text-align: center; word-wrap: break-word;'>63.7 (-0.7)</td><td style='text-align: center; word-wrap: break-word;'>59.6 (-1.9)</td><td style='text-align: center; word-wrap: break-word;'>54.9 (+0.7)</td><td style='text-align: center; word-wrap: break-word;'>56.7 (+0.1)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Streamo-3B</td><td style='text-align: center; word-wrap: break-word;'>61.5 (+6.9)</td><td style='text-align: center; word-wrap: break-word;'>41.8 (+4.0)</td><td style='text-align: center; word-wrap: break-word;'>67.9 (+0.9)</td><td style='text-align: center; word-wrap: break-word;'>66.2 (+1.8)</td><td style='text-align: center; word-wrap: break-word;'>61.8 (+0.3)</td><td style='text-align: center; word-wrap: break-word;'>56.2 (+2.0)</td><td style='text-align: center; word-wrap: break-word;'>59.2 (+2.6)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-VL-7B [3]</td><td style='text-align: center; word-wrap: break-word;'>58.8</td><td style='text-align: center; word-wrap: break-word;'>42.2</td><td style='text-align: center; word-wrap: break-word;'>69.6</td><td style='text-align: center; word-wrap: break-word;'>71.7</td><td style='text-align: center; word-wrap: break-word;'>65.1</td><td style='text-align: center; word-wrap: break-word;'>56.0</td><td style='text-align: center; word-wrap: break-word;'>60.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Streamo-7B</td><td style='text-align: center; word-wrap: break-word;'>66.0 (+7.2)</td><td style='text-align: center; word-wrap: break-word;'>46.1 (+3.9)</td><td style='text-align: center; word-wrap: break-word;'>72.3 (+2.7)</td><td style='text-align: center; word-wrap: break-word;'>71.8 (+0.1)</td><td style='text-align: center; word-wrap: break-word;'>67.9 (+2.8)</td><td style='text-align: center; word-wrap: break-word;'>59.2 (+3.2)</td><td style='text-align: center; word-wrap: break-word;'>63.9 (+3.3)</td></tr></table>

at 2 fps without retraining, achieving an additional +4.66% performance improvement, indicating robust generalization to higher test-time frame rates; 2) Streamo-Instruct-465K dataset surpasses existing dataset. Compared with the ET-Instruct-164K, our proposed Streamo-Instruct-465K delivers a comprehensive performance advantage, with +7.1% on forward task and +11.79% overall; 3) Offline supervision can hinder online learning. Augmenting ET-Instruct with the offline LLaVA-Video dataset boosts real-time perceptual accuracy but compromises streaming ability, revealing a trade-off inherent to offline-only supervision. This also demonstrates that Streamo-Instruct-465K transfers effectively to online, streaming scenarios while maintaining strong offline perceptual capability.

Comparison with SOTA on Offline Video Benchmarks

To evaluate the general video understanding capability of models after conversion to the online setting, we compare Streamo against the SOTA method and original offline base model on a suite of general offline video benchmarks, with results reported in Tab. 3. The findings show that, after conversion, Streamo retains strong perceptual performance on offline benchmarks across both short-form and long-form videos, surpassing the SOTA, StreamingVLM, in every benchmark. Meanwhile, models trained with our Streamo-Instruct-465K exhibit consistent improvements over base models, with Streamo-7B achieves an average improvement of +3.4% based on Qwen2.5-VL-7B. Holding architecture and training setup constant, Streamo-Instruct-465K also provides a clear advantage over alternative data recipes, outperforming ET-Instruction and LLaVA-Video by +7.8%.

<div style="text-align: center;">Table 4. Ablation study of loss functions for online training on OVO-Bench Forward Active tasks.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Base Model</td><td style='text-align: center; word-wrap: break-word;'>Loss Type</td><td style='text-align: center; word-wrap: break-word;'>REC</td><td style='text-align: center; word-wrap: break-word;'>SSR</td><td style='text-align: center; word-wrap: break-word;'>CRR</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-VL-3B</td><td style='text-align: center; word-wrap: break-word;'>CrossEntropy</td><td style='text-align: center; word-wrap: break-word;'>6.45</td><td style='text-align: center; word-wrap: break-word;'>20.99</td><td style='text-align: center; word-wrap: break-word;'>41.67</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-VL-3B</td><td style='text-align: center; word-wrap: break-word;'>Loss Scale</td><td style='text-align: center; word-wrap: break-word;'>18.62</td><td style='text-align: center; word-wrap: break-word;'>41.02</td><td style='text-align: center; word-wrap: break-word;'>49.17</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-VL-3B</td><td style='text-align: center; word-wrap: break-word;'>Focal Loss</td><td style='text-align: center; word-wrap: break-word;'>27.94</td><td style='text-align: center; word-wrap: break-word;'>50.72</td><td style='text-align: center; word-wrap: break-word;'>82.5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>InternVL3-2B</td><td style='text-align: center; word-wrap: break-word;'>CrossEntropy</td><td style='text-align: center; word-wrap: break-word;'>9.46</td><td style='text-align: center; word-wrap: break-word;'>20.50</td><td style='text-align: center; word-wrap: break-word;'>40.42</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>InternVL3-2B</td><td style='text-align: center; word-wrap: break-word;'>Loss Scale</td><td style='text-align: center; word-wrap: break-word;'>21.20</td><td style='text-align: center; word-wrap: break-word;'>31.47</td><td style='text-align: center; word-wrap: break-word;'>48.75</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>InternVL3-2B</td><td style='text-align: center; word-wrap: break-word;'>Focal Loss</td><td style='text-align: center; word-wrap: break-word;'>29.23</td><td style='text-align: center; word-wrap: break-word;'>47.38</td><td style='text-align: center; word-wrap: break-word;'>80.42</td></tr></table>

and +2.5% on average, respectively. These results underscore that our training framework and data not only enable effective transformation of models for streaming video understanding but also preserve and enhance core perceptual capabilities on offline video tasks.

Streamo-Bench To evaluate the model's ability to follow different instructions and perform varied tasks, we assign multiple instruction-driven tasks to a single video, including forward grounding, backward grounding, narration captions, dense captions, and time-sensitive question answering. Details, examples, and statistics for these tasks are presented in the Supplementary material.

As shown in Tab. 5, existing online models show deficiencies in comprehensive multi-task coverage. Our analysis indicates that these shortcomings stem largely from an inadequate ability to comprehend and follow com-

<div style="text-align: center;">Table 5. Evaluation results on Streamo-Bench. Forward and backward grounding are determined by whether the query refers to a time point before or after the event period, and results are using the mIoU metric. Caption evaluation is conducted by calculating the win rate with Qwen2.5-VL-72B model. TSQA denotes Time-Sensitive QA, i.e., questions whose answers change over time.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Model</td><td colspan="2">Grounding</td><td colspan="2">Caption</td><td colspan="2">TSQA</td><td rowspan="2">Average</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Forward</td><td style='text-align: center; word-wrap: break-word;'>Backward</td><td style='text-align: center; word-wrap: break-word;'>Narration</td><td style='text-align: center; word-wrap: break-word;'>Dence Caption</td><td style='text-align: center; word-wrap: break-word;'>Accuracy</td><td style='text-align: center; word-wrap: break-word;'>Recall</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Flash-VStream-7B [52]</td><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'>23.5</td><td style='text-align: center; word-wrap: break-word;'>25.9</td><td style='text-align: center; word-wrap: break-word;'>30.8</td><td style='text-align: center; word-wrap: break-word;'>13.1</td><td style='text-align: center; word-wrap: break-word;'>15.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLM-online-8B [6]</td><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'>42.0</td><td style='text-align: center; word-wrap: break-word;'>6.6</td><td style='text-align: center; word-wrap: break-word;'>19.6</td><td style='text-align: center; word-wrap: break-word;'>7.6</td><td style='text-align: center; word-wrap: break-word;'>12.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Dispider-7B [33]</td><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'>8.33</td><td style='text-align: center; word-wrap: break-word;'>31.6</td><td style='text-align: center; word-wrap: break-word;'>29.2</td><td style='text-align: center; word-wrap: break-word;'>14.0</td><td style='text-align: center; word-wrap: break-word;'>4.4</td><td style='text-align: center; word-wrap: break-word;'>14.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>StreamingVLM-7B [47]</td><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'>68.5</td><td style='text-align: center; word-wrap: break-word;'>24.0</td><td style='text-align: center; word-wrap: break-word;'>11.8</td><td style='text-align: center; word-wrap: break-word;'>43.1</td><td style='text-align: center; word-wrap: break-word;'>24.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Streamo-3B</td><td style='text-align: center; word-wrap: break-word;'>14.7</td><td style='text-align: center; word-wrap: break-word;'>27.5</td><td style='text-align: center; word-wrap: break-word;'>71.4</td><td style='text-align: center; word-wrap: break-word;'>68.5</td><td style='text-align: center; word-wrap: break-word;'>20.1</td><td style='text-align: center; word-wrap: break-word;'>65.7</td><td style='text-align: center; word-wrap: break-word;'>44.7</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Streamo-7B</td><td style='text-align: center; word-wrap: break-word;'>29.4</td><td style='text-align: center; word-wrap: break-word;'>38.3</td><td style='text-align: center; word-wrap: break-word;'>75.9</td><td style='text-align: center; word-wrap: break-word;'>72.8</td><td style='text-align: center; word-wrap: break-word;'>51.6</td><td style='text-align: center; word-wrap: break-word;'>63.9</td><td style='text-align: center; word-wrap: break-word;'>55.3</td></tr></table>

plex instructions. For instance, removing predefined options leads to widespread failure—as the grounding results show—highlighting a vulnerability to open-ended prompts. Furthermore, in standard QA scenarios, models frequently overlook instructions to update answers as conditions change, which severely degrades recall. We probe instruction comprehension and prompt sensitivity further with additional experiments in the Supplementary material. Collectively, these observations expose a critical gap in current capabilities. In contrast, Streamo demonstrates robust performance across tasks, clearly exhibiting strong instruction-following ability. This outcome validates both the diagnostic power of our benchmark and the effectiveness of our method in learning generalized instruction-following capabilities.

### 5.5. Ablation

To evaluate the effectiveness of our focal loss for training the three decision states, <Silence>, <Standby>, and <Response>, we compare it to standard cross-entropy loss. As shown in Tab. 4, training without state-aware reweighting severely limits performance due to significant class imbalance. In the Streamo-Instruct-465K dataset, the empirical ratio of state labels is approximately <Silence>:<Standby>:<Response> = 12:3:2, which biases conventional training toward predicting Silence and suppresses actual Response predictions.

A straightforward remedy is to assign fixed class weights inversely proportional to label frequency. Specifically, we set the weights to 0.3, 1.3, and 2.0 for silence, standby, and response, respectively, to emphasize response timing. As illustrated in the line “Loss Scale” in Tab. 4), this adjustment effectively mitigates the degradation caused by imbalance. However, fixed weighting fails to capture token-level hardness and sequence-level heterogeneity in decision-state distributions—for instance, narration tasks may contain multiple responses, whereas a QA task might include only one.

Our proposed focal loss addresses this limitation by dynamically reweighting losses based on token-level hardness and per-batch state frequency, thereby providing more adaptive supervision for response-timing decisions. Across both InternVL-3-2B and Qwen2.5-VL-3B backbones, training with the proposed focal loss consistently yields substantial improvements over both the vanilla cross-entropy and fixed-weight baselines.



## 6. Conclusion

Our work targets the advancement of streaming video by jointly addressing model training and data construction. We introduce an end-to-end training framework together with a large-scale instruction-tuning dataset, Streamo-Instruct465K, enabling the conversion of multiple state-of-the-art offline models into online version. The resulting model, Streamo, not only excels on streaming benchmarks but also rivals top-performing offline models. Furthermore, our proposed Streamo-Bench, which simulates complex multi-instruction scenarios, showcases Streamo's robust multitasking capabilities. Collectively, these contributions mark a significant leap towards creating general-purpose, real-time, and interactive AI assistants.

## 7. Limitations and Future Work

In terms of limitations, while our approach achieves strong accuracy, it is limited by the inherent challenges of streaming video's unbounded temporal context. Our current pipeline lacks specialized long-sequence optimizations, leading to significant memory and latency costs that become prohibitive as sequence length grows.

By leveraging our framework's compatibility with existing techniques, we can integrate KV-cache management and visual token pruning to reduce computational overhead, alongside exploring sliding-window attention and adaptive frame compression for refined context management. Collectively, these strategies are designed to enhance training and inference efficiency, extend the effective context length, and facilitate an unbounded, real-time data stream.

## 8. Acknowledgement

This research is supported by Hong Kong Research Grants Council Early Career Scheme (No. 22200824).

## References

[1] Lisa Anne Hendricks, Oliver Wang, Eli Shechtman, Josef Sivic, Trevor Darrell, and Bryan Russell. Localizing moments in video with natural language. In Proceedings of the IEEE international conference on computer vision, pages 5803–5812, 2017. 5

[2] Jinze Bai, Shuai Bai, Yunfei Chu, Zeyu Cui, Kai Dang, Xiaodong Deng, Yang Fan, Wenbin Ge, Yu Han, Fei Huang, et al. Qwen technical report. arXiv preprint arXiv:2309.16609, 2023. 3

[3] Shuai Bai, Keqin Chen, Xuejing Liu, Jialin Wang, Wenbin Ge, Sibo Song, Kai Dang, Peng Wang, Shijie Wang, Jun Tang, et al. Qwen2. 5-vl technical report. arXiv preprint arXiv:2502.13923, 2025. 5, 7, 2, 3, 8

[4] Max Bain, Arsha Nagrani, Gül Varol, and Andrew Zisserman. Frozen in time: A joint video and image encoder for end-to-end retrieval. In ICCV, 2021. 1

[5] Fabian Caba Heilbron, Victor Escorcia, Bernard Ghanem, and Juan Carlos Niebles. Activitynet: A large-scale video benchmark for human activity understanding. In CVPR, 2015. 2, 5

[6] Joya Chen, Zhaoyang Lv, Shiwei Wu, Kevin Qinghong Lin, Chenan Song, Difei Gao, Jia-Wei Liu, Ziteng Gao, Dongxing Mao, and Mike Zheng Shou. Videollm-online: Online video large language model for streaming video. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 18407–18418, 2024. 3, 6, 7, 8

[7] Lin Chen, Xilin Wei, Jinsong Li, Xiaoyi Dong, Pan Zhang, Yuhang Zang, Zehui Chen, Haodong Duan, Zhenyu Tang, Li Yuan, et al. Sharegpt4video: Improving video understanding and generation with better captions. NeurIPS, 2024. 3

[8] Zhe Chen, Weiyun Wang, Yue Cao, Yangzhou Liu, Zhangwei Gao, Erfei Cui, Jinguo Zhu, Shenglong Ye, Hao Tian, Zhaoyang Liu, et al. Expanding performance boundaries of open-source multimodal models with model, data, and test-time scaling. arXiv:2412.05271, 2024. 3

[9] Zhe Chen, Jiannan Wu, Wenhai Wang, Weijie Su, Guo Chen, Sen Xing, Muyan Zhong, Qinglong Zhang, Xizhou Zhu, Lewei Lu, et al. Internvl: Scaling up vision foundation models and aligning for generic visual-linguistic tasks. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition, pages 24185–24198, 2024. 2

[10] Zhe Chen, Jiannan Wu, Wenhai Wang, Weijie Su, Guo Chen, Sen Xing, Muyan Zhong, Qinglong Zhang, Xizhou Zhu, Lewei Lu, et al. Internvl: Scaling up vision foundation models and aligning for generic visual-linguistic tasks. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition, pages 24185–24198, 2024. 6,7

[11] Shangzhe Di and Weidi Xie. Grounded question-answering in long egocentric videos. In CVPR, 2024. 5

[12] Chaoyou Fu, Yuhan Dai, Yondong Luo, Lei Li, Shuhuai Ren, Renrui Zhang, Zihan Wang, Chenyu Zhou, Yunhang Shen,

Mengdan Zhang, et al. Video-mme: The first-ever comprehensive evaluation benchmark of multi-modal llms in video analysis. arXiv:2405.21075, 2024. 6

[13] Chaoyou Fu, Haojia Lin, Xiong Wang, Yi-Fan Zhang, Yunhang Shen, Xiaoyu Liu, Haoyu Cao, Zuwei Long, Heting Gao, Ke Li, et al. Vita-1.5: Towards gpt-4o level real-time vision and speech interaction. arXiv preprint arXiv:2501.01957, 2025. 3

[14] Shenghao Fu, Qize Yang, Yuan-Ming Li, Yi-Xing Peng, Kun-Yu Lin, Xihan Wei, Jian-Fang Hu, Xiaohua Xie, and Wei-Shi Zheng. Vispeak: Visual instruction feedback in streaming videos. In Proceedings of the IEEE/CVF International Conference on Computer Vision, pages 21778–21788, 2025. 6, 1, 3

[15] Jiyang Gao, Chen Sun, Zhenheng Yang, and Ram Nevatia. Tall: Temporal activity localization via language query. In ICCV, 2017. 2

[16] Yuying Ge, Yixiao Ge, Chen Li, Teng Wang, Junfu Pu, Yizhuo Li, Lu Qiu, Jin Ma, Lisheng Duan, Xinyu Zuo, et al. Arc-hunyuan-video-7b: Structured video comprehension of real-world shorts. arXiv preprint arXiv:2507.20939, 2025. 5, 2

[17] Mingfei Han, Linjie Yang, Xiaojun Chang, and Heng Wang. Shot2story20k: A new benchmark for comprehensive understanding of multi-shot videos. arXiv:2312.10300, 2023. 2

[18] Gabriel Huang, Bo Pang, Zhenhai Zhu, Clara Rivera, and Radu Soricut. Multimodal pretraining for dense video captioning. arXiv:2011.11760, 2020. 2

[19] Aaron Hurst, Adam Lerer, Adam P Goucher, Adam Perelman, Aditya Ramesh, Aidan Clark, AJ Ostrow, Akila Welihinda, Alan Hayes, Alec Radford, et al. Gpt-4o system card. arXiv:2410.21276, 2024. 7, 3, 8

[20] Asif Ali Laghari, Sana Shahid, Rahul Yadav, Shahid Karim, Awais Khan, Hang Li, and Yin Shoulin. The state of art and review on video streaming. Journal of High Speed Networks, 29(3):211–236, 2023. 1

[21] Bo Li, Yuanhan Zhang, Dong Guo, Renrui Zhang, Feng Li, Hao Zhang, Kaichen Zhang, Peiyuan Zhang, Yanwei Li, Ziewei Liu, et al. Llava-onevision: Easy visual task transfer. arXiv preprint arXiv:2408.03326, 2024. 6, 7

[22] Kunchang Li, Yali Wang, Yinan He, Yizhuo Li, Yi Wang, Yi Liu, Zun Wang, Jilan Xu, Guo Chen, Ping Luo, et al. Mvbench: A comprehensive multi-modal video understanding benchmark. In CVPR, 2024. 6

[23] Yifei Li, Junbo Niu, Ziyang Miao, Chunjiang Ge, Yuanhang Zhou, Qihao He, Xiaoyi Dong, Haodong Duan, Shuangrui Ding, Rui Qian, et al. Ovo-bench: How far is your video-llms from real-world online video understanding? arXiv:2501.05510, 2025. 3, 6

[24] Bin Lin, Bin Zhu, Yang Ye, Munan Ning, Peng Jin, and Li Yuan. Video-llava: Learning united visual representation by alignment before projection. arXiv:2311.10122, 2023. 1

[25] Tsung-Yi Lin, Priya Goyal, Ross Girshick, Kaiming He, and Piotr Dollár. Focal loss for dense object detection. In Proceedings of the IEEE international conference on computer vision, pages 2980–2988, 2017. 4

[26] Haotian Liu, Chunyuan Li, Qingyang Wu, and Yong Jae Lee. Visual instruction tuning. NeurIPS, 2023. 2

[27] Yuanxin Liu, Shicheng Li, Yi Liu, Yuxiang Wang, Shuhua Ren, Lei Li, Sishuo Chen, Xu Sun, and Lu Hou. Tempcompass: Do video llms really understand videos? arXiv:2403.00476, 2024. 6

[28] Ye Liu, Zongyang Ma, Zhongang Qi, Yang Wu, Ying Shan, and Chang W Chen. Et bench: Towards open-ended event-level video-language understanding. Advances in Neural Information Processing Systems, 37:32076–32110, 2024. 6, 7

[29] Zuyan Liu, Yuhao Dong, Ziwei Liu, Winston Hu, Jiwen Lu, and Yongming Rao. Oryx mllm: On-demand spatial-temporal understanding at arbitrary resolution. arXiv:2409.12961, 2024. 2

[30] Zuyan Liu, Yuhao Dong, Jiahui Wang, Ziwei Liu, Winston Hu, Jiwen Lu, and Yongming Rao. Ola: Pushing the frontiers of omni-modal language model. arXiv preprint arXiv:2502.04328, 2025. 3

[31] Muhammad Maaz, Hanoona Rasheed, Salman Khan, and Fahad Khan. Videogpt+: Integrating image and video encoders for enhanced video understanding. arXiv:2406.09418, 2024.

[32] WonJun Moon, Sangeek Hyun, SangUk Park, Dongchan Park, and Jae-Pil Heo. Query-dependent video representation for moment retrieval and highlight detection. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition, pages 23023–23033, 2023. 5

[33] Rui Qian, Shuangrui Ding, Xiaoyi Dong, Pan Zhang, Yuhang Zang, Yuhang Cao, Dahua Lin, and Jiaqi Wang. Dispider: Enabling video llms with active real-time interaction via disentangled perception, decision, and reaction. arXiv:2501.03218, 2025. 1, 3, 6, 7, 8

[34] Xiaoqian Shen, Yunyang Xiong, Changsheng Zhao, Lemeng Wu, Jun Chen, Chenchen Zhu, Zechun Liu, Fanyi Xiao, Balakrishnan Varadarajan, Florian Bordes, et al. Longvu: Spatiotemporal adaptive compression for long video-language understanding. arXiv preprint arXiv:2410.17434, 2024. 6, 7

[35] Yansong Tang, Dajun Ding, Yongming Rao, Yu Zheng, Danyang Zhang, Lili Zhao, Jiwen Lu, and Jie Zhou. Coin: A large-scale dataset for comprehensive instructional video analysis. In CVPR, 2019. 5, 2

[36] Gemini Team, Petko Georgiev, Ving Ian Lei, Ryan Burnell, Libin Bai, Anmol Gulati, Garrett Tanzer, Damien Vincent, Zhufeng Pan, Shibo Wang, et al. Gemini 1.5: Unlocking multimodal understanding across millions of tokens of context. arXiv:2403.05530, 2024. 7, 3, 8

[37] Qwen Team. Qwen3 technical report, 2025. 6, 1, 8

[38] V Team, Wenyi Hong, Wenmeng Yu, et al. Glm-4.5 v and glm-4.1 v-thinking: Towards versatile multimodal reasoning with scalable reinforcement learning. arXiv preprint arXiv:2507.01006, 2025. 5

[39] Haibo Wang, Bo Feng, Zhengfeng Lai, Mingze Xu, Shiyu Li, Weifeng Ge, Afshin Dehghan, Meng Cao, and Ping Huang. Streambridge: Turning your offline video large language model into a proactive streaming assistant. arXiv preprint arXiv:2505.05467, 2025. 1, 3

[40] Peng Wang, Shuai Bai, Sinan Tan, Shijie Wang, Zhihao Fan, Jinze Bai, Keqin Chen, Xuejing Liu, Jialin Wang, Wenbin

Ge, et al. Qwen2-vl: Enhancing vision-language model's perception of the world at any resolution. arXiv preprint arXiv:2409.12191, 2024. 6, 7

[41] Qiuheng Wang, Yukai Shi, Jiarong Ou, Rui Chen, Ke Lin, Jiahao Wang, Boyuan Jiang, Haotian Yang, Mingwu Zheng, Xin Tao, et al. Koala-36m: A large-scale video dataset improving consistency between fine-grained conditions and video content. In Proceedings of the Computer Vision and Pattern Recognition Conference, pages 8428–8437, 2025. 5

[42] Yi Wang, Kunchang Li, Yizhuo Li, Yinan He, Bingkun Huang, Zhiyu Zhao, Hongjie Zhang, Jilan Xu, Yi Liu, Zun Wang, et al. Internvideo: General video foundation models via generative and discriminative learning. arXiv preprint arXiv:2212.03191, 2022. 1

[43] Yueqian Wang, Xiaojun Meng, Yuxuan Wang, Jianxin Liang, Jiansheng Wei, Huishuai Zhang, and Dongyan Zhao. Videolm knows when to speak: Enhancing time-sensitive video comprehension with video-text duet interaction format. arXiv:2411.17991, 2024. 1

[44] Yi Wang, Xinhao Li, Ziang Yan, Yinan He, Jiashuo Yu, Xiangyu Zeng, Chenting Wang, Changlian Ma, Haian Huang, Jianfei Gao, et al. Internvideo2.5: Empowering video mlms with long and rich context modeling. arXiv preprint arXiv:2501.12386, 2025. 2

[45] Haoning Wu, Dongxu Li, Bei Chen, and Junnan Li. Longvideobench: A benchmark for long-context interleaved video-language understanding. NeurIPS, 2024. 6

[46] Haomiao Xiong, Zongxin Yang, Jiazuo Yu, Yunzhi Zhuge, Lu Zhang, Jiawen Zhu, and Huchuan Lu. Streaming video understanding and multi-round interaction with memory-enhanced knowledge. arXiv:2501.13468, 2025. 3

[47] Ruyi Xu, Guangxuan Xiao, Yukang Chen, Liuning He, Kelly Peng, Yao Lu, and Song Han. Streamingvlm: Real-time understanding for infinite video streams. arXiv preprint arXiv:2510.09608, 2025. 3, 7, 8, 2

[48] Biao Yang, Bin Wen, Boyang Ding, Changyi Liu, Chenglong Chu, Chengru Song, Chongling Rao, Chuan Yi, Da Li, Dunju Zang, et al. Kwai keye-vl 1.5 technical report. arXiv preprint arXiv:2509.01563, 2025. 3

[49] Zhenyu Yang, Yuhang Hu, Zemin Du, Dizhan Xue, Shengsheng Qian, Jiahong Wu, Fan Yang, Weiming Dong, and Changsheng Xu. Svbench: A benchmark with temporal multi-turn dialogues for streaming video understanding. arXiv:2502.10810, 2025. 3

[50] Aohan Zeng, Xin Lv, Qinkai Zheng, Zhenyu Hou, Bin Chen, Chengxing Xie, Cunxiang Wang, Da Yin, Hao Zeng, Jiajie Zhang, et al. Glm-4.5: Agentic, reasoning, and coding (arc) foundation models. arXiv preprint arXiv:2508.06471, 2025.

[51] Hang Zhang, Xin Li, and Lidong Bing. Video-llama: An instruction-tuned audio-visual language model for video understanding. arXiv:2306.02858, 2023. 1

[52] Haoji Zhang, Yiqin Wang, Yansong Tang, Yong Liu, Jiashi Feng, Jifeng Dai, and Xiaojie Jin. Flash-vstream: Memory-based real-time understanding for long video streams. arXiv:2406.08085, 2024. 6, 7, 8, 3

[53] Yuanhan Zhang, Jinming Wu, Wei Li, Bo Li, Zejun Ma, Ziewei Liu, and Chunyuan Li. Video instruction tuning with

synthetic data. arXiv preprint arXiv:2410.02713, 2024. 5, 6, 7

[54] Hang Zhao, Antonio Torralba, Lorenzo Torresani, and Zhicheng Yan. Hacs: Human action clips and segments dataset for recognition and temporal localization. In ICCV, 2019. 5

[55] Yucheng Zhao, Chong Luo, Chuanxin Tang, Dongdong Chen, Noel Codella, and Zheng-Jun Zha. Streaming video model. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition, pages 14602–14612, 2023. 1

[56] Lianmin Zheng, Wei-Lin Chiang, Ying Sheng, Siyuan Zhuang, Zhanghao Wu, Yonghao Zhuang, Zi Lin, Zhuohan Li, Dacheng Li, Eric Xing, et al. Judging llm-as-a-judge with mt-bench and chatbot arena. Advances in neural information processing systems, 36:46595–46623, 2023. 2

[57] Luowei Zhou, Chenliang Xu, and Jason Corso. Towards automatic learning of procedures from web instructional videos. In AAAI, 2018. 5, 2

[58] Jinguo Zhu, Weiyun Wang, Zhe Chen, Zhaoyang Liu, Shenglong Ye, Lixin Gu, Hao Tian, Yuchen Duan, Weijie Su, Jie Shao, et al. Internvl3: Exploring advanced training and test-time recipes for open-source multimodal models. arXiv preprint arXiv:2504.10479, 2025. 6, 1, 8

# Streaming Video Instruction Tuning

Supplementary Material

### A. Streamo

### A.1. System Prompt

We design a dedicated system prompt for Streamo that enables the model to handle dynamic streaming video content, interpret three predefined response states, and make real-time decisions at the frame level. The full prompt is provided in Tab. 10. This deliberately crafted prompt helps the model quickly adapt to the streaming input pattern and perform the required behavior transformation.

### A.2. Instruction Prompt

### A.3. More Experimental Results

In Tab. 14, we present the prompt templates used for all tasks. These diverse task instructions help the model better understand different task requirements, thereby fostering more general multi-task instruction-following capabilities. This goes beyond prior setups where models were confined to standalone QA, and represents a step toward general real-time interactive AI.

Our training framework converts offline models into streaming-capable models with minimal intrusive modifications, enabling these base models to process streaming video data. This design yields strong compatibility and allows direct application to a wide range of offline models. In Tab.11 and 12, we further report results using InternVL3[58] and Qwen3VL[37] as Streamo's base models. These results show that our framework effectively leverages the capabilities of offline models and extends them to online streaming video processing. This is particularly advantageous given the rapid iteration of offline models, as our framework can readily harness their improvements for real-time interactive video understanding.

Meanwhile, we also evaluated Streamo on ViSpeak-Bench [14], shown in Tab. 8. The results show that our method achieves a clear advantage in response-time accuracy, demonstrating the effectiveness and soundness of our response architecture.

### A.4. Visualization

In Fig.6 and 7, we visualize the outputs of Streamo, which vividly illustrate its ability to interpret and appropriately respond even to instructions that were unseen during training. When confronted with task instructions that vary in both response granularity and content, the model consistently produces suitable outputs. These visualizations provide strong evidence that Streamo's training framework successfully bridges the gap between offline model capabilities and the

<div style="text-align: center;">Table 6. Comparison of Existing Video Benchmarks. Streamo-Bench introduces the first mixed-task type specifically designed for streaming video.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Benchmark</td><td style='text-align: center; word-wrap: break-word;'>#Videos</td><td style='text-align: center; word-wrap: break-word;'>#Samples</td><td style='text-align: center; word-wrap: break-word;'>Streaming</td><td style='text-align: center; word-wrap: break-word;'>Task Type</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MVBench</td><td style='text-align: center; word-wrap: break-word;'>3,673</td><td style='text-align: center; word-wrap: break-word;'>4,000</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>QA</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>TempCompass</td><td style='text-align: center; word-wrap: break-word;'>410</td><td style='text-align: center; word-wrap: break-word;'>7,540</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>QA</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ET-Bench</td><td style='text-align: center; word-wrap: break-word;'>7,002</td><td style='text-align: center; word-wrap: break-word;'>7,289</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>Mix</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>SVBench</td><td style='text-align: center; word-wrap: break-word;'>1,353</td><td style='text-align: center; word-wrap: break-word;'>49,979</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>QA</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>StreamBench</td><td style='text-align: center; word-wrap: break-word;'>306</td><td style='text-align: center; word-wrap: break-word;'>1,800</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>QA</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>OVOBench</td><td style='text-align: center; word-wrap: break-word;'>644</td><td style='text-align: center; word-wrap: break-word;'>2,814</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>QA</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Streamo-Bench</td><td style='text-align: center; word-wrap: break-word;'>300</td><td style='text-align: center; word-wrap: break-word;'>3,000</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Mix</td></tr></table>

requirements of online streaming interactions, enabling reliable real-time responses that go far beyond simple QA.

### A.5. Further Analysis of the Three-State Design

To examine the rationale behind our training architecture more thoroughly, we compare the proposed Three-state Design with an alternative approach based on the [EOS] token. As shown in Tab. 7, the [EOS]-based model exhibits notable performance drops, particularly on proactive tasks (i.e., FAR) and grounding tasks. These results demonstrate that our three-state design consistently outperforms EOS-only training while introducing only negligible additional cost.

We attribute this gap to the fact that [EOS] maps both irrelevant and partially relevant segments to the same token. As a result, the model is encouraged to remain silent even when encountering relevant frames, causing it to miss the optimal timing for response. In contrast, the introduction of a [Standby] token alleviates this misalignment by explicitly marking relevant frames as soon as the event begins and preserving this state throughout the relevant interval. This leads to more accurate temporal alignment and more complete coverage, which is reflected in the higher grounding TIoU.

<div style="text-align: center;">Table 7. Comparison on the same training dataset, Streamo-Instruct, where the only change is replacing the proposed three-state design with EOS-only training. Using only [EOS] degrades performance, especially on proactive prediction (FAR) and forward grounding, highlighting the benefit of the three-state design.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Model</td><td colspan="4">OVOBench</td><td style='text-align: center; word-wrap: break-word;'>Streamo-Bench</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>RTVP</td><td style='text-align: center; word-wrap: break-word;'>BT</td><td style='text-align: center; word-wrap: break-word;'>FAR</td><td style='text-align: center; word-wrap: break-word;'>AVG</td><td style='text-align: center; word-wrap: break-word;'>Forward Grounding</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Streamo-3B</td><td style='text-align: center; word-wrap: break-word;'>61.51</td><td style='text-align: center; word-wrap: break-word;'>41.76</td><td style='text-align: center; word-wrap: break-word;'>53.72</td><td style='text-align: center; word-wrap: break-word;'>52.33</td><td style='text-align: center; word-wrap: break-word;'>14.7</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Streamo-3B w/ EOS</td><td style='text-align: center; word-wrap: break-word;'>60.93</td><td style='text-align: center; word-wrap: break-word;'>39.43</td><td style='text-align: center; word-wrap: break-word;'>45.22</td><td style='text-align: center; word-wrap: break-word;'>48.52</td><td style='text-align: center; word-wrap: break-word;'>9.3</td></tr></table>

A key advantage of [Standby] is that it explicitly models frames that are already relevant but not yet ready for a final response. As shown in Fig. 4, because the query is specifically about ASWIN, the model switches to [Standby] once ASWIN appears and the attempt becomes temporally relevant, even though the final outcome is still uncertain. This allows the model to preserve attention over the ongoing event instead of treating these frames as irrelevant. Meanwhile, for grounding, the continuous [Standby] state helps cover the full event span more completely, rather than activating only near the final decisive moment.

### B. Streamo-Instruct

### B.1. Data Generation Prompt

We next elaborate on the prompts used in our data annotation pipeline. For event caption tasks, we leverage ARC-Hunyuan $ ^{[16]} $, which is specifically trained for video segmentation and grounding, and directly adopt its official prompt for initial data processing. We then use the prompt in Tab.13 to rewrite and clean the annotated caption sentences. For narration generation, which describes interframe temporal changes, the generation prompt is given in Tab.15, and the prompt for merging and cleaning the resulting descriptions is provided in Tab.16. For the TSQA task, the detailed prompt is presented in Tab.17.

### C. Streamo-Bench

In Tab. 6, we compare our proposed Streamo-Bench with existing video benchmarks. Streamo-Bench is, to the best of our knowledge, the first streaming video benchmark that integrates multiple task types. Existing streaming video benchmarks typically use QA as the sole evaluation task, which mainly measures perceptual understanding rather than the ability to perform diverse open-ended tasks. However, the ability to follow varied instructions and complete multiple tasks is a key requirement for streaming video models. By filling this gap, Streamo-Bench enables more comprehensive evaluation of a model's instruction-following ability in open-ended streaming scenarios.

### C.1. Statistics

Our benchmark contains 300 videos sampled from COIN[35], YouCookv2[57], and ActivityNet [5]. Each video is annotated with multiple tasks, including Grounding, Narration, Caption, and Time-Sensitive QA, yielding a total of 3,000 task-specific instances. Each video in Streamo-Bench contains 2x grounding (forward + backward) tasks, 1x dense caption task, and 1x narration task, with the rest being TSQA. This comprehensive design enables a thorough examination of a model's ability to process and respond to diverse instructions in streaming settings.

### C.2. Metric

To comprehensively evaluate the performance of models on our Streamo-Bench, we detail the metrics used for each task type below.

Grounding Evaluation. For grounding tasks, we distinguish between forward (queries referring to time points before an event) and backward (queries referring to time points after an event) contexts. Performance is measured using mean Intersection over Union (mIoU), which quantifies the overlap between the model's predicted temporal interval and the ground-truth interval.

Let the predicted and ground-truth temporal intervals,  $ t^{\mathrm{pred}} $ and  $ t^{\mathrm{gt}} $, for sample i be:

 $$ t_{i}^{\mathrm{p r e d}}=[\mathbf{\mathit{s}}_{i}^{\mathrm{p r e d}},\mathbf{\mathit{e}}_{i}^{\mathrm{p r e d}}],\qquad t_{i}^{\mathrm{g t}}=[\mathbf{\mathit{s}}_{i}^{\mathrm{g t}},\mathbf{\mathit{e}}_{i}^{\mathrm{g t}}], $$ 

where s and e represent the start and end timestamps, respectively. The IoU for sample i is defined as the ratio of intersection length to union length:

 $$ \mathrm{I o U}_{i}=\frac{\max\big(0,\min(e_{i}^{\mathrm{p r e d}},e_{i}^{\mathrm{g t}})-\max(s_{i}^{\mathrm{p r e d}},s_{i}^{\mathrm{g t}})\big)}{\max(e_{i}^{\mathrm{p r e d}},e_{i}^{\mathrm{g t}})-\min(s_{i}^{\mathrm{p r e d}},s_{i}^{\mathrm{g t}})}. $$ 

The mean IoU (mIoU) over N samples is

 $$ \mathrm{mIoU}=\frac{1}{N}\sum_{i=1}^{N}\mathrm{IoU}_{i}. $$ 

Narration and Caption Evaluation. Because narration and captioning are open-ended generation tasks, directly evaluating output quality is challenging. Following the evaluation protocol of Chatbot Arena [56] and StreamingVLM [47], we assess narration and caption quality via pairwise comparison against a strong baseline, Qwen2.5-VL-72B [3]. The win rate is defined as the proportion of cases in which our model's output is judged superior to the baseline's output.

Time-Sensitive QA Evaluation. For Time-Sensitive QA, we require that a prediction be correct in both its content and its timestamp. Let $Q$ be the set of TSQA questions. For each question $q \in Q$, the ground truth consists of $m_q$ time-stamped answers:

 $$ G_{q}=\{(a_{i}^{q},t_{i}^{q})\}_{i=1}^{m_{q}}, $$ 

where $a_{i}^{q}$ is the answer content and $t_{i}^{q}$ is its timestamp. The model produces $n_{q}$ predictions:

 $$ P_{q}=\{(\hat{a}_{j}^{q},\hat{t}_{j}^{q})\}_{j=1}^{n_{q}}, $$ 

where  $ \hat{a}_{j}^{q} $ is the predicted content and  $ \hat{t}_{j}^{q} $ is the predicted timestamp.

A predicted pair  $ (\hat{a}_j^q, \hat{t}_j^q) $ may match a ground-truth pair  $ (a_i^q, t_i^q) $ only if it is correct in both content and time. For the

<div style="text-align: center;">Table 8. Performance of streamo compared to various MLLMs on ViSpeak-Bench.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Method</td><td rowspan="2">Params</td><td rowspan="2">Frames</td><td rowspan="2">Omni</td><td rowspan="2">Streaming</td><td colspan="8">Time Accuracy (%)</td><td colspan="8">Text Score</td><td style='text-align: center; word-wrap: break-word;'>Overall</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>AW</td><td style='text-align: center; word-wrap: break-word;'>VI</td><td style='text-align: center; word-wrap: break-word;'>HR</td><td style='text-align: center; word-wrap: break-word;'>VW</td><td style='text-align: center; word-wrap: break-word;'>VT</td><td style='text-align: center; word-wrap: break-word;'>GU</td><td style='text-align: center; word-wrap: break-word;'>All</td><td style='text-align: center; word-wrap: break-word;'>VR</td><td style='text-align: center; word-wrap: break-word;'>AW</td><td style='text-align: center; word-wrap: break-word;'>VI</td><td style='text-align: center; word-wrap: break-word;'>HR</td><td style='text-align: center; word-wrap: break-word;'>VW</td><td style='text-align: center; word-wrap: break-word;'>VT</td><td style='text-align: center; word-wrap: break-word;'>GU</td><td style='text-align: center; word-wrap: break-word;'>All</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Human (Avg)</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>70.00</td><td style='text-align: center; word-wrap: break-word;'>100.00</td><td style='text-align: center; word-wrap: break-word;'>90.00</td><td style='text-align: center; word-wrap: break-word;'>92.00</td><td style='text-align: center; word-wrap: break-word;'>96.00</td><td style='text-align: center; word-wrap: break-word;'>98.80</td><td style='text-align: center; word-wrap: break-word;'>91.13</td><td style='text-align: center; word-wrap: break-word;'>4.80</td><td style='text-align: center; word-wrap: break-word;'>2.45</td><td style='text-align: center; word-wrap: break-word;'>4.58</td><td style='text-align: center; word-wrap: break-word;'>3.06</td><td style='text-align: center; word-wrap: break-word;'>5.00</td><td style='text-align: center; word-wrap: break-word;'>5.00</td><td style='text-align: center; word-wrap: break-word;'>2.85</td><td style='text-align: center; word-wrap: break-word;'>3.96</td><td style='text-align: center; word-wrap: break-word;'>3.69</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Human (Max)</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>70.00</td><td style='text-align: center; word-wrap: break-word;'>100.00</td><td style='text-align: center; word-wrap: break-word;'>100.00</td><td style='text-align: center; word-wrap: break-word;'>100.00</td><td style='text-align: center; word-wrap: break-word;'>100.00</td><td style='text-align: center; word-wrap: break-word;'>100.00</td><td style='text-align: center; word-wrap: break-word;'>95.00</td><td style='text-align: center; word-wrap: break-word;'>5.00</td><td style='text-align: center; word-wrap: break-word;'>2.71</td><td style='text-align: center; word-wrap: break-word;'>5.00</td><td style='text-align: center; word-wrap: break-word;'>3.62</td><td style='text-align: center; word-wrap: break-word;'>5.00</td><td style='text-align: center; word-wrap: break-word;'>5.00</td><td style='text-align: center; word-wrap: break-word;'>3.19</td><td style='text-align: center; word-wrap: break-word;'>4.22</td><td style='text-align: center; word-wrap: break-word;'>4.01</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td colspan="22">Proprietary MLLMs</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Gemini 1.5 pro [36]</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>46.00</td><td style='text-align: center; word-wrap: break-word;'>60.00</td><td style='text-align: center; word-wrap: break-word;'>85.00</td><td style='text-align: center; word-wrap: break-word;'>84.00</td><td style='text-align: center; word-wrap: break-word;'>48.00</td><td style='text-align: center; word-wrap: break-word;'>97.00</td><td style='text-align: center; word-wrap: break-word;'>70.00</td><td style='text-align: center; word-wrap: break-word;'>3.03</td><td style='text-align: center; word-wrap: break-word;'>2.34</td><td style='text-align: center; word-wrap: break-word;'>2.93</td><td style='text-align: center; word-wrap: break-word;'>1.36</td><td style='text-align: center; word-wrap: break-word;'>4.66</td><td style='text-align: center; word-wrap: break-word;'>4.68</td><td style='text-align: center; word-wrap: break-word;'>2.07</td><td style='text-align: center; word-wrap: break-word;'>3.01</td><td style='text-align: center; word-wrap: break-word;'>2.19</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>GPT-4o [19]</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>48.50</td><td style='text-align: center; word-wrap: break-word;'>82.00</td><td style='text-align: center; word-wrap: break-word;'>96.00</td><td style='text-align: center; word-wrap: break-word;'>99.00</td><td style='text-align: center; word-wrap: break-word;'>100.00</td><td style='text-align: center; word-wrap: break-word;'>99.50</td><td style='text-align: center; word-wrap: break-word;'>87.50</td><td style='text-align: center; word-wrap: break-word;'>3.18</td><td style='text-align: center; word-wrap: break-word;'>2.27</td><td style='text-align: center; word-wrap: break-word;'>3.53</td><td style='text-align: center; word-wrap: break-word;'>1.71</td><td style='text-align: center; word-wrap: break-word;'>5.00</td><td style='text-align: center; word-wrap: break-word;'>4.98</td><td style='text-align: center; word-wrap: break-word;'>2.22</td><td style='text-align: center; word-wrap: break-word;'>3.27</td><td style='text-align: center; word-wrap: break-word;'>2.99</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td colspan="22">Open-Source Video MLLMs</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>InternVL-2.5 [8]</td><td style='text-align: center; word-wrap: break-word;'>8B</td><td style='text-align: center; word-wrap: break-word;'>16</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>41.50</td><td style='text-align: center; word-wrap: break-word;'>55.50</td><td style='text-align: center; word-wrap: break-word;'>46.00</td><td style='text-align: center; word-wrap: break-word;'>96.00</td><td style='text-align: center; word-wrap: break-word;'>72.00</td><td style='text-align: center; word-wrap: break-word;'>99.50</td><td style='text-align: center; word-wrap: break-word;'>68.42</td><td style='text-align: center; word-wrap: break-word;'>2.93</td><td style='text-align: center; word-wrap: break-word;'>2.16</td><td style='text-align: center; word-wrap: break-word;'>3.67</td><td style='text-align: center; word-wrap: break-word;'>0.74</td><td style='text-align: center; word-wrap: break-word;'>3.05</td><td style='text-align: center; word-wrap: break-word;'>4.81</td><td style='text-align: center; word-wrap: break-word;'>1.26</td><td style='text-align: center; word-wrap: break-word;'>2.66</td><td style='text-align: center; word-wrap: break-word;'>1.98</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-VL [3]</td><td style='text-align: center; word-wrap: break-word;'>7B</td><td style='text-align: center; word-wrap: break-word;'>1 fps</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>42.50</td><td style='text-align: center; word-wrap: break-word;'>78.00</td><td style='text-align: center; word-wrap: break-word;'>31.00</td><td style='text-align: center; word-wrap: break-word;'>95.00</td><td style='text-align: center; word-wrap: break-word;'>85.00</td><td style='text-align: center; word-wrap: break-word;'>98.50</td><td style='text-align: center; word-wrap: break-word;'>71.67</td><td style='text-align: center; word-wrap: break-word;'>2.34</td><td style='text-align: center; word-wrap: break-word;'>2.31</td><td style='text-align: center; word-wrap: break-word;'>2.31</td><td style='text-align: center; word-wrap: break-word;'>1.32</td><td style='text-align: center; word-wrap: break-word;'>5.00</td><td style='text-align: center; word-wrap: break-word;'>3.91</td><td style='text-align: center; word-wrap: break-word;'>1.02</td><td style='text-align: center; word-wrap: break-word;'>2.60</td><td style='text-align: center; word-wrap: break-word;'>2.25</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-VL [3]</td><td style='text-align: center; word-wrap: break-word;'>72B</td><td style='text-align: center; word-wrap: break-word;'>1 fps</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>44.50</td><td style='text-align: center; word-wrap: break-word;'>81.00</td><td style='text-align: center; word-wrap: break-word;'>77.00</td><td style='text-align: center; word-wrap: break-word;'>91.00</td><td style='text-align: center; word-wrap: break-word;'>91.00</td><td style='text-align: center; word-wrap: break-word;'>93.00</td><td style='text-align: center; word-wrap: break-word;'>79.58</td><td style='text-align: center; word-wrap: break-word;'>3.15</td><td style='text-align: center; word-wrap: break-word;'>2.64</td><td style='text-align: center; word-wrap: break-word;'>3.36</td><td style='text-align: center; word-wrap: break-word;'>1.00</td><td style='text-align: center; word-wrap: break-word;'>5.00</td><td style='text-align: center; word-wrap: break-word;'>5.00</td><td style='text-align: center; word-wrap: break-word;'>1.50</td><td style='text-align: center; word-wrap: break-word;'>3.09</td><td style='text-align: center; word-wrap: break-word;'>2.62</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VITA 1.5 [13]</td><td style='text-align: center; word-wrap: break-word;'>7B</td><td style='text-align: center; word-wrap: break-word;'>1 fps</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>18.00</td><td style='text-align: center; word-wrap: break-word;'>46.00</td><td style='text-align: center; word-wrap: break-word;'>40.00</td><td style='text-align: center; word-wrap: break-word;'>88.00</td><td style='text-align: center; word-wrap: break-word;'>49.00</td><td style='text-align: center; word-wrap: break-word;'>97.50</td><td style='text-align: center; word-wrap: break-word;'>56.42</td><td style='text-align: center; word-wrap: break-word;'>2.40</td><td style='text-align: center; word-wrap: break-word;'>2.08</td><td style='text-align: center; word-wrap: break-word;'>0.57</td><td style='text-align: center; word-wrap: break-word;'>0.85</td><td style='text-align: center; word-wrap: break-word;'>4.57</td><td style='text-align: center; word-wrap: break-word;'>4.49</td><td style='text-align: center; word-wrap: break-word;'>1.18</td><td style='text-align: center; word-wrap: break-word;'>2.31</td><td style='text-align: center; word-wrap: break-word;'>1.54</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Ola [30]</td><td style='text-align: center; word-wrap: break-word;'>7B</td><td style='text-align: center; word-wrap: break-word;'>1 fps</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>27.00</td><td style='text-align: center; word-wrap: break-word;'>67.00</td><td style='text-align: center; word-wrap: break-word;'>44.00</td><td style='text-align: center; word-wrap: break-word;'>89.00</td><td style='text-align: center; word-wrap: break-word;'>69.00</td><td style='text-align: center; word-wrap: break-word;'>98.50</td><td style='text-align: center; word-wrap: break-word;'>65.75</td><td style='text-align: center; word-wrap: break-word;'>2.95</td><td style='text-align: center; word-wrap: break-word;'>1.81</td><td style='text-align: center; word-wrap: break-word;'>2.67</td><td style='text-align: center; word-wrap: break-word;'>0.55</td><td style='text-align: center; word-wrap: break-word;'>4.71</td><td style='text-align: center; word-wrap: break-word;'>3.67</td><td style='text-align: center; word-wrap: break-word;'>1.52</td><td style='text-align: center; word-wrap: break-word;'>2.55</td><td style='text-align: center; word-wrap: break-word;'>1.86</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>FlashVstream [52]</td><td style='text-align: center; word-wrap: break-word;'>7B</td><td style='text-align: center; word-wrap: break-word;'>1 fps</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>34.00</td><td style='text-align: center; word-wrap: break-word;'>16.00</td><td style='text-align: center; word-wrap: break-word;'>48.00</td><td style='text-align: center; word-wrap: break-word;'>75.00</td><td style='text-align: center; word-wrap: break-word;'>33.00</td><td style='text-align: center; word-wrap: break-word;'>99.50</td><td style='text-align: center; word-wrap: break-word;'>50.92</td><td style='text-align: center; word-wrap: break-word;'>1.75</td><td style='text-align: center; word-wrap: break-word;'>1.63</td><td style='text-align: center; word-wrap: break-word;'>1.31</td><td style='text-align: center; word-wrap: break-word;'>0.67</td><td style='text-align: center; word-wrap: break-word;'>4.88</td><td style='text-align: center; word-wrap: break-word;'>4.61</td><td style='text-align: center; word-wrap: break-word;'>0.70</td><td style='text-align: center; word-wrap: break-word;'>2.22</td><td style='text-align: center; word-wrap: break-word;'>1.24</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Dispider [33]</td><td style='text-align: center; word-wrap: break-word;'>7B</td><td style='text-align: center; word-wrap: break-word;'>16</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>38.50</td><td style='text-align: center; word-wrap: break-word;'>70.00</td><td style='text-align: center; word-wrap: break-word;'>44.00</td><td style='text-align: center; word-wrap: break-word;'>69.00</td><td style='text-align: center; word-wrap: break-word;'>100.00</td><td style='text-align: center; word-wrap: break-word;'>99.50</td><td style='text-align: center; word-wrap: break-word;'>70.17</td><td style='text-align: center; word-wrap: break-word;'>2.50</td><td style='text-align: center; word-wrap: break-word;'>1.75</td><td style='text-align: center; word-wrap: break-word;'>4.06</td><td style='text-align: center; word-wrap: break-word;'>0.91</td><td style='text-align: center; word-wrap: break-word;'>0.61</td><td style='text-align: center; word-wrap: break-word;'>2.49</td><td style='text-align: center; word-wrap: break-word;'>2.07</td><td style='text-align: center; word-wrap: break-word;'>2.06</td><td style='text-align: center; word-wrap: break-word;'>1.63</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ViSpeak [14]</td><td style='text-align: center; word-wrap: break-word;'>7B</td><td style='text-align: center; word-wrap: break-word;'>1 fps</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>56.50</td><td style='text-align: center; word-wrap: break-word;'>72.00</td><td style='text-align: center; word-wrap: break-word;'>83.00</td><td style='text-align: center; word-wrap: break-word;'>93.00</td><td style='text-align: center; word-wrap: break-word;'>79.00</td><td style='text-align: center; word-wrap: break-word;'>99.00</td><td style='text-align: center; word-wrap: break-word;'>80.42</td><td style='text-align: center; word-wrap: break-word;'>3.75</td><td style='text-align: center; word-wrap: break-word;'>2.63</td><td style='text-align: center; word-wrap: break-word;'>3.84</td><td style='text-align: center; word-wrap: break-word;'>1.07</td><td style='text-align: center; word-wrap: break-word;'>4.95</td><td style='text-align: center; word-wrap: break-word;'>3.15</td><td style='text-align: center; word-wrap: break-word;'>3.36</td><td style='text-align: center; word-wrap: break-word;'>3.25</td><td style='text-align: center; word-wrap: break-word;'>2.76</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Streamo</td><td style='text-align: center; word-wrap: break-word;'>7B</td><td style='text-align: center; word-wrap: break-word;'>1 fps</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>59.00</td><td style='text-align: center; word-wrap: break-word;'>79.00</td><td style='text-align: center; word-wrap: break-word;'>82.00</td><td style='text-align: center; word-wrap: break-word;'>97.00</td><td style='text-align: center; word-wrap: break-word;'>86.00</td><td style='text-align: center; word-wrap: break-word;'>100</td><td style='text-align: center; word-wrap: break-word;'>83.83</td><td style='text-align: center; word-wrap: break-word;'>2.73</td><td style='text-align: center; word-wrap: break-word;'>2.31</td><td style='text-align: center; word-wrap: break-word;'>3.62</td><td style='text-align: center; word-wrap: break-word;'>1.33</td><td style='text-align: center; word-wrap: break-word;'>4.96</td><td style='text-align: center; word-wrap: break-word;'>3.62</td><td style='text-align: center; word-wrap: break-word;'>2.97</td><td style='text-align: center; word-wrap: break-word;'>3.08</td><td style='text-align: center; word-wrap: break-word;'>2.71</td><td style='text-align: center; word-wrap: break-word;'></td></tr></table>

content evaluation:

 $$ C(\hat{a}_{j}^{q},a_{i}^{q})=\begin{cases}1,&if content matches,\\ 0,&otherwise.\end{cases} $$ 

For the timestamp, we define a non-negative tolerance parameter  $ \delta_t \geq 0 $. Then we evaluate the correctness of the timestamp by:

 $$ T(\hat{t}_{j}^{q},t_{i}^{q};\delta_{t})=\begin{cases}{1,}&{\mathrm{i f}\quad|\hat{t}_{j}^{q}-t_{i}^{q}|\leq\delta_{t},}\\ {0,}&{\mathrm{o t h e r w i s e}.}\\ \end{cases} $$ 

In our experimental setting, the  $ \delta_t $ is set to 3 seconds. For the  $ i $-th answer point of question  $ q $, we define an indicator  $ I_i^q $ that checks whether there exists at least one prediction satisfying both content and temporal constraints: :

 $$ I_{i}^{q}=\begin{cases}{1}&{\mathrm{i f}\quad C(\hat{a}_{j}^{q},a_{i}^{q})=1\land T(\hat{t}_{j}^{q},t_{i}^{q};\delta_{t})=1}\\ {0}&{\mathrm{o t h e r w i s e}}\\ \end{cases} $$ 

The final accuracy and recall can be given as:

 $$ \mathrm{Accuracy}=\frac{1}{\sum_{q\in Q}m_{q}}\sum_{q\in Q}\sum_{i=1}^{m_{q}}I_{i}^{q} $$ 

 $$ \mathrm{Recall}=\frac{1}{|Q|}\sum_{q\in Q}\left(\frac{1}{m_{q}}\sum_{i=1}^{m_{q}}I_{i}^{q}\right) $$ 

### C.3. Sample Visualization

A sample instance from Streamo-Bench is illustrated in Fig. 5. Forward and backward grounding questions are randomly placed either before or after their corresponding target temporal intervals. The TSQA question is inserted before the first answer timestamp. Narration and event caption instructions are placed before the start of the video stream to capture the overall video content.

### C.4. Further Analysis

We further analyze the performance of existing models on Streamo-Bench and observe that their primary failures stem from a lack of instruction-task comprehension: they struggle to distinguish different task types and to produce task-appropriate outputs. This limitation arises because these models are typically trained exclusively on captioning or QA data, which constrains them to generate outputs tailored to only those specific tasks.

Examples in Tab. 9 clearly illustrate this phenomenon: while the models can satisfy caption or narration requirements, they often fail to understand grounding instructions and instead fall back to generic video descriptions. For TSQA tasks, although models trained on QA data can answer content-related questions, they do not properly follow instructions that require real-time updates to answers over the video timeline, leading to task failure.

In summary, existing models generally lack robust multi-task understanding, whereas Streamo-Bench is specifically designed to evaluate a model's ability to interpret and respond to task-specific instructions in streaming scenarios.

<div style="text-align: center;"><img src="imgs/img_in_image_box_174_267_1053_1187.jpg" alt="Image" width="71%" />

Did ASWIN successfully make the jump attempt?

Temporally localize the event: ‘Aswin from Kerala failed to clear the 4.40-meter bar in the pole vault competition’. Respond once it has finished and summarize its time period.

<Standby>
<Stendby>
<Response> No, he failed.
<Stendby>
<Response> Given event occurred between 20s to 43s.

</div>


<div style="text-align: center;">Figure 4. Visualization of the three-state decoding process. The model stays in [Silence] for irrelevant frames, switches to [Standby] once the query-relevant event involving ASWIN begins, and emits [Response] only after the outcome becomes clear. For the grounding task, the persistent [Standby] state helps preserve attention over the relevant interval and enables more complete temporal coverage of the event span.</div>


#### Time-Sensitive QA Task

What action is being performed on the tree?

A. Measuring B. Watering C. Mulching

Please provide your answer by stating the letter followed by the full option. Answer again if it changes.

What is being done to the soil around the tree?

A. backfilled B. marked C. dug up

Please provide your answer by stating the letter followed by the full option. Update when new info comes.



## Dirt Doctor www.yourhouseondhome.tv

##### Question Time

<div style="text-align: center;"><img src="imgs/img_in_image_box_325_516_469_622.jpg" alt="Image" width="11%" />

HOWARD GARRETT
The Dirt Doctor

</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_473_515_615_623.jpg" alt="Image" width="11%" />

福

</div>


##### Question Time

<div style="text-align: center;"><img src="imgs/img_in_image_box_619_516_760_623.jpg" alt="Image" width="11%" />



</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_765_515_908_623.jpg" alt="Image" width="11%" />

P

</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_910_516_1054_623.jpg" alt="Image" width="11%" />



</div>


<div style="text-align: center;">A. Measuring</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_181_713_324_821.jpg" alt="Image" width="11%" />

A

</div>


<div style="text-align: center;">Question Time</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_327_714_471_823.jpg" alt="Image" width="11%" />

G

</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_474_714_615_823.jpg" alt="Image" width="11%" />

G

</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_619_714_760_821.jpg" alt="Image" width="11%" />

D

</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_766_715_906_822.jpg" alt="Image" width="11%" />

は

</div>


<div style="text-align: center;">B. marked</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_912_714_1052_821.jpg" alt="Image" width="11%" />

D

</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_182_856_323_966.jpg" alt="Image" width="11%" />

G

</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_327_860_468_967.jpg" alt="Image" width="11%" />

The image is too blurry to recognize any text content.
The image is too blurry to recognize any text content.
The image is too blurry to recognize any text content.

</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_471_857_613_964.jpg" alt="Image" width="11%" />

M

</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_619_859_760_965.jpg" alt="Image" width="11%" />

.

</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_766_859_905_965.jpg" alt="Image" width="11%" />



</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_913_858_1052_965.jpg" alt="Image" width="11%" />

A

</div>


The event occurs during 48s – 66s.

What is the temporal window for the event:'Take the sapling out of the pot and measure its depth.'

Question Time Event Grounding Task(Backward)

<div style="text-align: center;"><img src="imgs/img_in_image_box_181_1058_323_1163.jpg" alt="Image" width="11%" />

2

</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_327_1057_467_1164.jpg" alt="Image" width="11%" />

A

</div>


C. dug up

<div style="text-align: center;"><img src="imgs/img_in_image_box_472_1056_614_1163.jpg" alt="Image" width="11%" />

A

</div>


(B. Watering)

<div style="text-align: center;"><img src="imgs/img_in_image_box_618_1058_760_1163.jpg" alt="Image" width="11%" />



</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_764_1059_907_1162.jpg" alt="Image" width="11%" />



</div>


A. backfilled

<div style="text-align: center;"><img src="imgs/img_in_image_box_909_1059_1051_1161.jpg" alt="Image" width="11%" />



</div>


## (C. Mulching)

<div style="text-align: center;">Figure 5. Streamo-Bench example illustrating multi-task instruction-following evaluation.</div>


<div style="text-align: center;">Input Video</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_141_353_322_459.jpg" alt="Image" width="14%" />

A

</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Prompt</td><td style='text-align: center; word-wrap: break-word;'>Model Output</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Real-Time Narration Task: Watch the following video and provide a real-time narration.</td><td style='text-align: center; word-wrap: break-word;'>Here’s a typical mid-late 18th Century stoneware tea pot with the rounded spout and finial for pouring. After pouring when you were pouring out the last bit of liquid from the pot, you would be careful to stir away any bits of leaf which were floating around in the bottom.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Event Caption Task: List every event happening in the video.</td><td style='text-align: center; word-wrap: break-word;'>We’ll go through all the steps to make tea the way the Victorians did step by step. When you think of what they would be using here in their kitchen spaces, you can see they’ve got the teapot, and she’s working on getting her leaves in. The method for both is basically exactly the same. With the fresh leaf version in this case, we’re just adding in equal amounts of leaves and water.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Event Grounding Task: Localize this event: ‘add some water to the tea’ in the following video.</td><td style='text-align: center; word-wrap: break-word;'>In the Victorian era the family kitchen was an even more important part of home life than in previous as this was where most of their time was spent. It was where the family ate their meals but also where they would come together. Whether it was afternoons at tea or a simple evening meal, the Victorian kitchen was a place that families would gather together and enjoy good company and food. Here we have made our own little tea service here, and I will be showing you how Mrs Bronte would serve it in her kitchen.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Time-Sensitive QA Task: What is the woman doing? A. Preparing tea in kitchen\nB. Sitting at desk writing C. Drinking tea at desk. Please provide your answer by stating the letter followed by the full option. If the correct answer later changes, update your response.</td><td style='text-align: center; word-wrap: break-word;'>A. Preparing tea in kitchen. You will learn to make a cup of tea the Victorian way.” To begin you’ll need something sweet to top with your tea and milk. Tea is made with sugar or honey and the Victorians actually used a lot of cream for their tea. I’m going to use some milk for my tea today. And it can take up to two minutes to boil, so if you’re making tea for more than one person.”, Start with just one cup at a time and then add more when ready.</td></tr></table>

<div style="text-align: center;"><img src="imgs/img_in_image_box_901_353_1081_459.jpg" alt="Image" width="14%" />



</div>


<div style="text-align: center;">Table 9. Example output from StreamingVLM illustrating a failure to follow diverse task instructions and generate the corresponding response.</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_221_207_1004_649.jpg" alt="Image" width="63%" />

System Prompt: You are a helpful assistant specializing in streaming video analysis.
You will receive input frame by frame, each labeled with absolute time intervals in the exact format <Xs-Ys> (e.g., <0s-1s>). Follow these rules precisely:
1. Use </Silence> when:
- No relevant event has started, OR
- The current input is irrelevant to the given question.
2. Use </Standby> when:
- An event is in progress but has not yet completed, OR
- The current input is relevant but the question cannot yet be answered.
3. Use </Response> only when:
- An event has fully concluded, OR
- The available information is sufficient to fully answer the question.
Provide a complete description at this point.
Do not provide partial answers or speculate beyond the given information.
Whenever you deliver an answer, begin with </Response>.

</div>


<div style="text-align: center;">Table 10. System prompt used in Streamo.</div>


<div style="text-align: center;">Table 11. Additional online benchmark evaluation results of Streamo framework with different base models (InternVL3 and Qwen3VL). Our framework consistently enables strong real-time streaming performance across diverse offline backbones.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Model</td><td rowspan="2"># Frames</td><td colspan="6">Real-Time Visual Perception</td><td colspan="4">Backward Tracing</td><td colspan="4">Forward Active Responding</td><td style='text-align: center; word-wrap: break-word;'>Overall Avg.</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>OCR</td><td style='text-align: center; word-wrap: break-word;'>ACR</td><td style='text-align: center; word-wrap: break-word;'>ATR</td><td style='text-align: center; word-wrap: break-word;'>STU</td><td style='text-align: center; word-wrap: break-word;'>FPD</td><td style='text-align: center; word-wrap: break-word;'>OJR</td><td style='text-align: center; word-wrap: break-word;'>Avg.</td><td style='text-align: center; word-wrap: break-word;'>EPM</td><td style='text-align: center; word-wrap: break-word;'>ASI</td><td style='text-align: center; word-wrap: break-word;'>HLD</td><td style='text-align: center; word-wrap: break-word;'>Avg.</td><td style='text-align: center; word-wrap: break-word;'>REC</td><td style='text-align: center; word-wrap: break-word;'>SSR</td><td style='text-align: center; word-wrap: break-word;'>CRR</td><td style='text-align: center; word-wrap: break-word;'>Avg.</td><td style='text-align: center; word-wrap: break-word;'>Overall Avg.</td></tr><tr><td colspan="18">Open-source Offline Models</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2-VL-72B [40]</td><td style='text-align: center; word-wrap: break-word;'>64</td><td style='text-align: center; word-wrap: break-word;'>65.77</td><td style='text-align: center; word-wrap: break-word;'>60.55</td><td style='text-align: center; word-wrap: break-word;'>69.83</td><td style='text-align: center; word-wrap: break-word;'>51.69</td><td style='text-align: center; word-wrap: break-word;'>69.31</td><td style='text-align: center; word-wrap: break-word;'>54.35</td><td style='text-align: center; word-wrap: break-word;'>61.92</td><td style='text-align: center; word-wrap: break-word;'>52.53</td><td style='text-align: center; word-wrap: break-word;'>60.81</td><td style='text-align: center; word-wrap: break-word;'>57.53</td><td style='text-align: center; word-wrap: break-word;'>56.95</td><td style='text-align: center; word-wrap: break-word;'>38.83</td><td style='text-align: center; word-wrap: break-word;'>64.07</td><td style='text-align: center; word-wrap: break-word;'>45</td><td style='text-align: center; word-wrap: break-word;'>49.3</td><td style='text-align: center; word-wrap: break-word;'>56.27</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-Video-7B [53]</td><td style='text-align: center; word-wrap: break-word;'>64</td><td style='text-align: center; word-wrap: break-word;'>69.13</td><td style='text-align: center; word-wrap: break-word;'>58.72</td><td style='text-align: center; word-wrap: break-word;'>68.83</td><td style='text-align: center; word-wrap: break-word;'>49.44</td><td style='text-align: center; word-wrap: break-word;'>74.26</td><td style='text-align: center; word-wrap: break-word;'>59.78</td><td style='text-align: center; word-wrap: break-word;'>63.52</td><td style='text-align: center; word-wrap: break-word;'>56.23</td><td style='text-align: center; word-wrap: break-word;'>57.43</td><td style='text-align: center; word-wrap: break-word;'>7.53</td><td style='text-align: center; word-wrap: break-word;'>40.4</td><td style='text-align: center; word-wrap: break-word;'>34.1</td><td style='text-align: center; word-wrap: break-word;'>69.95</td><td style='text-align: center; word-wrap: break-word;'>60.42</td><td style='text-align: center; word-wrap: break-word;'>54.82</td><td style='text-align: center; word-wrap: break-word;'>52.91</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-OneVision-7B [21]</td><td style='text-align: center; word-wrap: break-word;'>64</td><td style='text-align: center; word-wrap: break-word;'>66.44</td><td style='text-align: center; word-wrap: break-word;'>57.8</td><td style='text-align: center; word-wrap: break-word;'>73.28</td><td style='text-align: center; word-wrap: break-word;'>53.37</td><td style='text-align: center; word-wrap: break-word;'>71.29</td><td style='text-align: center; word-wrap: break-word;'>61.96</td><td style='text-align: center; word-wrap: break-word;'>64.02</td><td style='text-align: center; word-wrap: break-word;'>54.21</td><td style='text-align: center; word-wrap: break-word;'>55.41</td><td style='text-align: center; word-wrap: break-word;'>21.51</td><td style='text-align: center; word-wrap: break-word;'>43.71</td><td style='text-align: center; word-wrap: break-word;'>25.64</td><td style='text-align: center; word-wrap: break-word;'>67.09</td><td style='text-align: center; word-wrap: break-word;'>58.75</td><td style='text-align: center; word-wrap: break-word;'>50.5</td><td style='text-align: center; word-wrap: break-word;'>52.74</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2-VL-7B [40]</td><td style='text-align: center; word-wrap: break-word;'>64</td><td style='text-align: center; word-wrap: break-word;'>60.4</td><td style='text-align: center; word-wrap: break-word;'>50.46</td><td style='text-align: center; word-wrap: break-word;'>56.03</td><td style='text-align: center; word-wrap: break-word;'>47.19</td><td style='text-align: center; word-wrap: break-word;'>66.34</td><td style='text-align: center; word-wrap: break-word;'>55.43</td><td style='text-align: center; word-wrap: break-word;'>55.98</td><td style='text-align: center; word-wrap: break-word;'>47.81</td><td style='text-align: center; word-wrap: break-word;'>35.48</td><td style='text-align: center; word-wrap: break-word;'>56.08</td><td style='text-align: center; word-wrap: break-word;'>46.46</td><td style='text-align: center; word-wrap: break-word;'>31.66</td><td style='text-align: center; word-wrap: break-word;'>65.82</td><td style='text-align: center; word-wrap: break-word;'>48.75</td><td style='text-align: center; word-wrap: break-word;'>48.74</td><td style='text-align: center; word-wrap: break-word;'>50.39</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>InternVL-V2-8B [10]</td><td style='text-align: center; word-wrap: break-word;'>64</td><td style='text-align: center; word-wrap: break-word;'>67.11</td><td style='text-align: center; word-wrap: break-word;'>60.55</td><td style='text-align: center; word-wrap: break-word;'>63.79</td><td style='text-align: center; word-wrap: break-word;'>46.07</td><td style='text-align: center; word-wrap: break-word;'>68.32</td><td style='text-align: center; word-wrap: break-word;'>56.52</td><td style='text-align: center; word-wrap: break-word;'>60.39</td><td style='text-align: center; word-wrap: break-word;'>48.15</td><td style='text-align: center; word-wrap: break-word;'>57.43</td><td style='text-align: center; word-wrap: break-word;'>24.73</td><td style='text-align: center; word-wrap: break-word;'>43.44</td><td style='text-align: center; word-wrap: break-word;'>26.5</td><td style='text-align: center; word-wrap: break-word;'>59.14</td><td style='text-align: center; word-wrap: break-word;'>54.14</td><td style='text-align: center; word-wrap: break-word;'>46.6</td><td style='text-align: center; word-wrap: break-word;'>50.15</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LongVU-7B [34]</td><td style='text-align: center; word-wrap: break-word;'>1fps</td><td style='text-align: center; word-wrap: break-word;'>53.69</td><td style='text-align: center; word-wrap: break-word;'>53.21</td><td style='text-align: center; word-wrap: break-word;'>62.93</td><td style='text-align: center; word-wrap: break-word;'>47.75</td><td style='text-align: center; word-wrap: break-word;'>68.32</td><td style='text-align: center; word-wrap: break-word;'>59.78</td><td style='text-align: center; word-wrap: break-word;'>57.61</td><td style='text-align: center; word-wrap: break-word;'>40.74</td><td style='text-align: center; word-wrap: break-word;'>59.46</td><td style='text-align: center; word-wrap: break-word;'>4.84</td><td style='text-align: center; word-wrap: break-word;'>35.01</td><td style='text-align: center; word-wrap: break-word;'>12.18</td><td style='text-align: center; word-wrap: break-word;'>69.48</td><td style='text-align: center; word-wrap: break-word;'>60.83</td><td style='text-align: center; word-wrap: break-word;'>47.5</td><td style='text-align: center; word-wrap: break-word;'>46.71</td></tr><tr><td colspan="18">Open-source Online Models</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Flash-VStream-7B [52]</td><td style='text-align: center; word-wrap: break-word;'>1fps</td><td style='text-align: center; word-wrap: break-word;'>24.16</td><td style='text-align: center; word-wrap: break-word;'>29.36</td><td style='text-align: center; word-wrap: break-word;'>28.45</td><td style='text-align: center; word-wrap: break-word;'>33.71</td><td style='text-align: center; word-wrap: break-word;'>25.74</td><td style='text-align: center; word-wrap: break-word;'>28.8</td><td style='text-align: center; word-wrap: break-word;'>28.37</td><td style='text-align: center; word-wrap: break-word;'>39.06</td><td style='text-align: center; word-wrap: break-word;'>37.16</td><td style='text-align: center; word-wrap: break-word;'>5.91</td><td style='text-align: center; word-wrap: break-word;'>27.38</td><td style='text-align: center; word-wrap: break-word;'>8.02</td><td style='text-align: center; word-wrap: break-word;'>67.25</td><td style='text-align: center; word-wrap: break-word;'>60</td><td style='text-align: center; word-wrap: break-word;'>45.09</td><td style='text-align: center; word-wrap: break-word;'>33.61</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLM-online-8B [6]</td><td style='text-align: center; word-wrap: break-word;'>2fps</td><td style='text-align: center; word-wrap: break-word;'>8.05</td><td style='text-align: center; word-wrap: break-word;'>23.85</td><td style='text-align: center; word-wrap: break-word;'>12.07</td><td style='text-align: center; word-wrap: break-word;'>14.04</td><td style='text-align: center; word-wrap: break-word;'>45.54</td><td style='text-align: center; word-wrap: break-word;'>21.2</td><td style='text-align: center; word-wrap: break-word;'>20.79</td><td style='text-align: center; word-wrap: break-word;'>22.22</td><td style='text-align: center; word-wrap: break-word;'>18.8</td><td style='text-align: center; word-wrap: break-word;'>12.18</td><td style='text-align: center; word-wrap: break-word;'>17.73</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Dispider-7B [33]</td><td style='text-align: center; word-wrap: break-word;'>1fps</td><td style='text-align: center; word-wrap: break-word;'>57.72</td><td style='text-align: center; word-wrap: break-word;'>49.54</td><td style='text-align: center; word-wrap: break-word;'>62.07</td><td style='text-align: center; word-wrap: break-word;'>44.94</td><td style='text-align: center; word-wrap: break-word;'>61.39</td><td style='text-align: center; word-wrap: break-word;'>51.63</td><td style='text-align: center; word-wrap: break-word;'>54.55</td><td style='text-align: center; word-wrap: break-word;'>48.48</td><td style='text-align: center; word-wrap: break-word;'>55.41</td><td style='text-align: center; word-wrap: break-word;'>4.3</td><td style='text-align: center; word-wrap: break-word;'>36.06</td><td style='text-align: center; word-wrap: break-word;'>18.05</td><td style='text-align: center; word-wrap: break-word;'>37.36</td><td style='text-align: center; word-wrap: break-word;'>48.75</td><td style='text-align: center; word-wrap: break-word;'>34.72</td><td style='text-align: center; word-wrap: break-word;'>41.78</td></tr><tr><td colspan="18">Streamo Framework</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Streamo-3B (Qwem2.5-VL)</td><td style='text-align: center; word-wrap: break-word;'>1fps</td><td style='text-align: center; word-wrap: break-word;'>78.52</td><td style='text-align: center; word-wrap: break-word;'>52.29</td><td style='text-align: center; word-wrap: break-word;'>67.24</td><td style='text-align: center; word-wrap: break-word;'>44.38</td><td style='text-align: center; word-wrap: break-word;'>55.45</td><td style='text-align: center; word-wrap: break-word;'>71.20</td><td style='text-align: center; word-wrap: break-word;'>61.51</td><td style='text-align: center; word-wrap: break-word;'>51.18</td><td style='text-align: center; word-wrap: break-word;'>57.43</td><td style='text-align: center; word-wrap: break-word;'>16.67</td><td style='text-align: center; word-wrap: break-word;'>41.76</td><td style='text-align: center; word-wrap: break-word;'>27.94</td><td style='text-align: center; word-wrap: break-word;'>50.72</td><td style='text-align: center; word-wrap: break-word;'>82.5</td><td style='text-align: center; word-wrap: break-word;'>53.72</td><td style='text-align: center; word-wrap: break-word;'>52.33</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Streamo-7B (Qwem2.5-VL)</td><td style='text-align: center; word-wrap: break-word;'>1fps</td><td style='text-align: center; word-wrap: break-word;'>79.19</td><td style='text-align: center; word-wrap: break-word;'>57.80</td><td style='text-align: center; word-wrap: break-word;'>75.00</td><td style='text-align: center; word-wrap: break-word;'>49.44</td><td style='text-align: center; word-wrap: break-word;'>64.36</td><td style='text-align: center; word-wrap: break-word;'>70.11</td><td style='text-align: center; word-wrap: break-word;'>65.98</td><td style='text-align: center; word-wrap: break-word;'>54.55</td><td style='text-align: center; word-wrap: break-word;'>52.03</td><td style='text-align: center; word-wrap: break-word;'>31.72</td><td style='text-align: center; word-wrap: break-word;'>46.10</td><td style='text-align: center; word-wrap: break-word;'>29.96</td><td style='text-align: center; word-wrap: break-word;'>51.03</td><td style='text-align: center; word-wrap: break-word;'>83.33</td><td style='text-align: center; word-wrap: break-word;'>54.77</td><td style='text-align: center; word-wrap: break-word;'>55.61</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Streamo-2B (InternVL3)</td><td style='text-align: center; word-wrap: break-word;'>1fps</td><td style='text-align: center; word-wrap: break-word;'>77.18</td><td style='text-align: center; word-wrap: break-word;'>55.96</td><td style='text-align: center; word-wrap: break-word;'>62.07</td><td style='text-align: center; word-wrap: break-word;'>41.01</td><td style='text-align: center; word-wrap: break-word;'>60.40</td><td style='text-align: center; word-wrap: break-word;'>70.11</td><td style='text-align: center; word-wrap: break-word;'>61.12</td><td style='text-align: center; word-wrap: break-word;'>48.82</td><td style='text-align: center; word-wrap: break-word;'>47.30</td><td style='text-align: center; word-wrap: break-word;'>13.44</td><td style='text-align: center; word-wrap: break-word;'>36.52</td><td style='text-align: center; word-wrap: break-word;'>29.23</td><td style='text-align: center; word-wrap: break-word;'>47.38</td><td style='text-align: center; word-wrap: break-word;'>80.42</td><td style='text-align: center; word-wrap: break-word;'>52.34</td><td style='text-align: center; word-wrap: break-word;'>49.99</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Streamo-4B (Qwen3-VL)</td><td style='text-align: center; word-wrap: break-word;'>1fps</td><td style='text-align: center; word-wrap: break-word;'>82.55</td><td style='text-align: center; word-wrap: break-word;'>69.72</td><td style='text-align: center; word-wrap: break-word;'>74.14</td><td style='text-align: center; word-wrap: break-word;'>52.25</td><td style='text-align: center; word-wrap: break-word;'>73.27</td><td style='text-align: center; word-wrap: break-word;'>81.52</td><td style='text-align: center; word-wrap: break-word;'>72.24</td><td style='text-align: center; word-wrap: break-word;'>58.19</td><td style='text-align: center; word-wrap: break-word;'>52.70</td><td style='text-align: center; word-wrap: break-word;'>17.20</td><td style='text-align: center; word-wrap: break-word;'>42.70</td><td style='text-align: center; word-wrap: break-word;'>31.38</td><td style='text-align: center; word-wrap: break-word;'>53.90</td><td style='text-align: center; word-wrap: break-word;'>84.17</td><td style='text-align: center; word-wrap: break-word;'>56.48</td><td style='text-align: center; word-wrap: break-word;'>55.10</td></tr></table>

<div style="text-align: center;">Table 12. Additional offline benchmarks results of Streamo framework with different base models (InternVL3 and Qwen3VL). The results show that our training framework preserves the underlying offline capability while extending it to streaming video processing.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Model</td><td style='text-align: center; word-wrap: break-word;'>OVO Real-Time</td><td style='text-align: center; word-wrap: break-word;'>OVO Backward</td><td style='text-align: center; word-wrap: break-word;'>MVBench</td><td style='text-align: center; word-wrap: break-word;'>TempCompass</td><td style='text-align: center; word-wrap: break-word;'>VideoMME</td><td style='text-align: center; word-wrap: break-word;'>LongVideoBench</td><td style='text-align: center; word-wrap: break-word;'>Avg</td></tr><tr><td colspan="8">Proprietary Models</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Gemini-1.5-pro [36]</td><td style='text-align: center; word-wrap: break-word;'>69.3</td><td style='text-align: center; word-wrap: break-word;'>62.5</td><td style='text-align: center; word-wrap: break-word;'>60.5</td><td style='text-align: center; word-wrap: break-word;'>67.1</td><td style='text-align: center; word-wrap: break-word;'>75.0</td><td style='text-align: center; word-wrap: break-word;'>64.0</td><td style='text-align: center; word-wrap: break-word;'>66.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>GPT-4o [19]</td><td style='text-align: center; word-wrap: break-word;'>64.5</td><td style='text-align: center; word-wrap: break-word;'>60.8</td><td style='text-align: center; word-wrap: break-word;'>64.6</td><td style='text-align: center; word-wrap: break-word;'>70.9</td><td style='text-align: center; word-wrap: break-word;'>71.9</td><td style='text-align: center; word-wrap: break-word;'>66.7</td><td style='text-align: center; word-wrap: break-word;'>66.6</td></tr><tr><td colspan="8">Open-source Online Models</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Flash-VStream-7B [52]</td><td style='text-align: center; word-wrap: break-word;'>28.4</td><td style='text-align: center; word-wrap: break-word;'>27.4</td><td style='text-align: center; word-wrap: break-word;'>61.2</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>61.2</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLM-online-8B [6]</td><td style='text-align: center; word-wrap: break-word;'>20.8</td><td style='text-align: center; word-wrap: break-word;'>17.7</td><td style='text-align: center; word-wrap: break-word;'>33.9</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>26.9</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Dispider-7B [33]</td><td style='text-align: center; word-wrap: break-word;'>54.6</td><td style='text-align: center; word-wrap: break-word;'>36.1</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>57.2</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>StreamingVLM-7B [47]</td><td style='text-align: center; word-wrap: break-word;'>62.0</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>69.2</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>65.1</td><td style='text-align: center; word-wrap: break-word;'>59.0</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td colspan="8">Streamo Framework</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-VL-3B [3]</td><td style='text-align: center; word-wrap: break-word;'>54.6</td><td style='text-align: center; word-wrap: break-word;'>37.8</td><td style='text-align: center; word-wrap: break-word;'>67.0</td><td style='text-align: center; word-wrap: break-word;'>64.4</td><td style='text-align: center; word-wrap: break-word;'>61.5</td><td style='text-align: center; word-wrap: break-word;'>54.2</td><td style='text-align: center; word-wrap: break-word;'>56.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Streamo-3B</td><td style='text-align: center; word-wrap: break-word;'>61.5 (+6.9)</td><td style='text-align: center; word-wrap: break-word;'>41.8 (+4.0)</td><td style='text-align: center; word-wrap: break-word;'>67.9 (+0.9)</td><td style='text-align: center; word-wrap: break-word;'>66.2 (+1.8)</td><td style='text-align: center; word-wrap: break-word;'>61.8 (+0.3)</td><td style='text-align: center; word-wrap: break-word;'>56.2 (+2.0)</td><td style='text-align: center; word-wrap: break-word;'>59.2 (+2.6)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-VL-7B [3]</td><td style='text-align: center; word-wrap: break-word;'>58.8</td><td style='text-align: center; word-wrap: break-word;'>42.2</td><td style='text-align: center; word-wrap: break-word;'>69.6</td><td style='text-align: center; word-wrap: break-word;'>71.7</td><td style='text-align: center; word-wrap: break-word;'>65.1</td><td style='text-align: center; word-wrap: break-word;'>56.0</td><td style='text-align: center; word-wrap: break-word;'>60.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Streamo-7B</td><td style='text-align: center; word-wrap: break-word;'>66.0 (+7.2)</td><td style='text-align: center; word-wrap: break-word;'>46.1 (+3.9)</td><td style='text-align: center; word-wrap: break-word;'>72.3 (+2.7)</td><td style='text-align: center; word-wrap: break-word;'>71.8 (+0.1)</td><td style='text-align: center; word-wrap: break-word;'>67.9 (+2.8)</td><td style='text-align: center; word-wrap: break-word;'>59.2 (+3.2)</td><td style='text-align: center; word-wrap: break-word;'>63.9 (+3.3)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>InternVL3-2B [58]</td><td style='text-align: center; word-wrap: break-word;'>59.5</td><td style='text-align: center; word-wrap: break-word;'>36.4</td><td style='text-align: center; word-wrap: break-word;'>70.4</td><td style='text-align: center; word-wrap: break-word;'>57.6</td><td style='text-align: center; word-wrap: break-word;'>58.9</td><td style='text-align: center; word-wrap: break-word;'>55.4</td><td style='text-align: center; word-wrap: break-word;'>56.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Streamo-2B</td><td style='text-align: center; word-wrap: break-word;'>61.1 (+1.6)</td><td style='text-align: center; word-wrap: break-word;'>36.5 (+0.1)</td><td style='text-align: center; word-wrap: break-word;'>71.4 (+1.0)</td><td style='text-align: center; word-wrap: break-word;'>57.8 (+0.2)</td><td style='text-align: center; word-wrap: break-word;'>60.1 (+1.2)</td><td style='text-align: center; word-wrap: break-word;'>56.5 (+1.1)</td><td style='text-align: center; word-wrap: break-word;'>57.3 (+0.9)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen3-VL-4B [37]</td><td style='text-align: center; word-wrap: break-word;'>66.5</td><td style='text-align: center; word-wrap: break-word;'>42.8</td><td style='text-align: center; word-wrap: break-word;'>68.9</td><td style='text-align: center; word-wrap: break-word;'>65.8</td><td style='text-align: center; word-wrap: break-word;'>69.3</td><td style='text-align: center; word-wrap: break-word;'>53.2</td><td style='text-align: center; word-wrap: break-word;'>61.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Streamo-4B</td><td style='text-align: center; word-wrap: break-word;'>72.2 (+5.7)</td><td style='text-align: center; word-wrap: break-word;'>42.7 (-0.1)</td><td style='text-align: center; word-wrap: break-word;'>70.4 (+1.5)</td><td style='text-align: center; word-wrap: break-word;'>66.3 (+0.5)</td><td style='text-align: center; word-wrap: break-word;'>68.7 (-0.6)</td><td style='text-align: center; word-wrap: break-word;'>56.1 (+2.9)</td><td style='text-align: center; word-wrap: break-word;'>62.8 (+1.7)</td></tr><tr><td colspan="8">Event Rewriting Prompt: You are given a set of video captions, each describing a specific moment in a video. For each caption, perform the following tasks:</td></tr><tr><td colspan="8">1. Remove any transition words, discourse markers, or sequence indicators (e.g., &quot;Finally&quot; Then &quot;Next &quot;Afterwards &quot;At the beginning &quot;At the end &quot;The video ends with &quot;The scene starts with etc.&quot;) at the beginning of the sentence or within the sentence, as these captions are now independent and do not need such connectors or structural descriptions.
2. Rewrite the caption to make it more concise and clear, without changing its meaning or omitting any important information.
3. Preserve all factual details and key actions described in the original caption.
4. Do not add any extra interpretation, information, or imagination not present in the original sentence. Only use the information given.
5. If the sentence includes a phrase describing the position of a shot or the sequence within the video (such as &quot;The video ends with &quot;At the start of the video &quot;In the next scene &quot;The video conclude with&quot;), remove this part entirely. Focus only on describing the content of the shot.</td></tr><tr><td colspan="8">Example:
Original: &quot;Finally, the video cuts back to the man in the indoor setting, who concludes the presentation by holding the bow.&quot;
Optimized: &quot;The man in the indoor setting concludes the presentation by holding the bow.&quot;</td></tr><tr><td colspan="8">Process each caption in this way. Return the optimized sentence directly.
Original: {sentences}
Optimized:</td></tr></table>

<div style="text-align: center;">Table 13. Task prompt used for rewriting event caption.</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_219_280_1001_1235.jpg" alt="Image" width="63%" />

Real-time Narration Task:
- Provide a continuous, time-synchronized narration of the video, describing actions, objects, and scene changes as they occur.
- Narrate the video in real time, updating the description frame-by-frame or moment-by-moment as events unfold.
- Generate live commentary of the video, focusing on who is doing what, where, and when, and noting any transitions or new events immediately.
- Deliver an on-the-fly description of the video, highlighting salient actions, interactions, and changes in context as soon as they appear.
- Produce a running narration that captures ongoing activities, brief pauses, and resumptions, maintaining temporal alignment with the video timeline.

Action Caption:
- Find, identify, and determine the temporal boundaries of a series of distinct actions or steps occurring throughout the video.
- Locate and describe a series of actions or steps in the video.
- Locate and pinpoint a sequential series of specific actions or steps in the video.
- Identify and mark the video segments corresponding to a series of actions or steps.
- Identify and localize a series of steps or actions occurring in the video.

Event Caption:
- Identify and describe all events in the following video.
- List every event happening in the following video with descriptions.
- Detect and summarize each event sequence in the following video.
- Extract and explain all notable events in the following video.
- Find all significant events in the following video and describe them.

Event Grounding:
- Watch the following video and temporally localize the event. Respond once it has finished and summarize its time period. The given event is: 'caption'
- Monitor the following video, identify the event, then respond after it finishes with a summary of its time window. The given event is: 'caption'
- Analyze the following video, detect the event and report back upon its completion with its time period. The given event is: 'caption'
- Review the following video, localize the event in time, then notify me once it ends and summarize the interval it occupies. The given event is: 'caption'
- Identify and temporally segment the event in the following video. Report after it finishes with its time period and duration. The given event is: 'caption'

Time-sensitive QA:
- {question} If the answer changes over time, update your response accordingly.
- {question} Update your answer if it becomes different at a later time.
- {question} If it later differs, update your response promptly.
- {question} Refresh your answer upon any change.
- {question} If the correct answer later changes, update your response.

</div>


<div style="text-align: center;">Table 14. Prompt template used for diverse streaming video tasks.</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_222_123_1004_704.jpg" alt="Image" width="63%" />

Video Description Prompt: You are given two consecutive seconds in a video (2 frames per second). Please succinctly describe the most significant operation or change that occurred between these seconds, focusing on the following points:
1. Base your description solely on clearly observable information; avoid speculation or assumptions.
2. For each object or element that changed, briefly state what changed: position, movement, actions, shape, color, etc.
3. Only describe the main operation, event, or action that happened—avoid listing small movements or minor shifts.
4. Describe only the specific changed parts with clear and direct language; do not include unchanged content or summarize the overall scene.
5. Make your description short and focused, naming only the changes without referencing the sequence of frames or including explanations.
Example:
'A woman appears.'
'You pick up a scissor.'
'The cup moves to the left.'
'A cat enters the frame.'
'The red ball rolls closer.'
'The lamp turns on.'
'The book closes.'
'A hand takes the remote.'
'The door opens further.'
Only provide the most important description or a summary of multiple descriptions.

</div>


<div style="text-align: center;">Table 15. Task prompt used for frame-level video description generation.</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_218_765_1003_1371.jpg" alt="Image" width="64%" />

Narration Generation Prompt:
**Objective**: Clean the following second-by-second video descriptions to enhance coherence and eliminate redundancy. The original descriptions were generated with visibility of only the preceding and following 2 seconds, making them repetitive and disjointed.
**Task**: Transform the descriptions into a smooth, logical narrative by:
1. Removing Redundancy: Omit repeated descriptions of static or ongoing actions.
2. Filtering Insignificant Details: Exclude minor or fleeting actions that do not impact overall understanding.
3. Sentence Shortening: If a description significantly exceeds 5 words, rewrite it to approximately 5 words while preserving the main idea.
4. Merging Consecutive Events: Combine adjacent descriptions representing a continuous or complete action into a single, concise sentence (e.g., “002: Man touches socket” and “003: Socket disappears” → “003: Man removed socket”).
**Output Format and Rules**:
1. Use the format: SSS: one-sentence description.
2. When merging or omitting descriptions, skip the corresponding timestamps.
3. Do not add explanations, notes, or blank lines.
4. If the descriptions are repetitive, monotonous, lack meaningful variation, or are confusing, ambiguous, or insufficient, output only: Negative Sample.
Description:
{Description}

</div>


<div style="text-align: center;">Table 16. Task prompt used for merging the frame description to generate real-time narration.</div>


TSQA Generation Prompt: You are a Time-Sensitive Video Question Generator. You need to identify all the elements in the video that change over time and formulate them into questions.
**CORE REQUIREMENT**
Every question MUST have answers that CHANGE over time. If something doesn't change during the video, DO NOT create a question about it.
**TASK**
1. Identify ONLY aspects that visibly CHANGE during the video. Ignore:
- Static elements that remain constant
- Transitions, previews, close-ups that don't alter facts
- Opening/closing sequences
2. For each changing aspect, generate ONE question with MULTIPLE DIFFERENT answers:
- Each question MUST have at least 2 DISTINCT answer values
- Answers must represent actual changes observed at different times
- Never repeat the same answer value
3. Question types:
- **Descriptive**: What/Which/Who (e.g., "What color is the ball?")
- **Counting**: How many/How much (e.g., "How many people are visible?")
- **State**: What stage (e.g., "What is the person doing?")
- **Action**: What is being added/used (e.g., "What ingredient is being added?")
- **Binary**: Yes/No (e.g., "Is the bacon cooked?")
4. Answer format:
- List answers chronologically
- Include PRECISE time in seconds for each observed change
- If state returns to a previous value, include it as a new entry
**EXAMPLES**
[{"question": "What color is the traffic light?" answers": [{"value": "red" time": 3.8}, {"value": "green" time": 8.7}, {"value": "yellow" time": 23.2}, {"value": "red" time": 26.4}]},
{"question": "How many people are in the frame?" answers": [{"value": 1, "time": 0.0}, {"value": 2, "time": 3.8}, {"value": 3, "time": 17.1}, {"value": 1, "time": 42.6}]},
{"question": "What is being poured into the glass?" answers": [{"value": "water" time": 2.3}, {"value": "milk" time": 19.7}, {"value": "orange juice" time": 31.4}]},
{"question": "Is the cake fully decorated?" answers": [{"value": "No" time": 13.7}, {"value": "Yes" time": 48.9}]}]}
**OUTPUT**
- Minimum 2 distinct answers per question
- Precise timing for all changes. Times must reflect ACTUAL observed changes, not approximations
- If unsure of exact timing, watch that segment again
Think step-by-step and ensure all requirements are met and all time are precise.

<div style="text-align: center;">Table 17. Task prompt used for Time-Sensitive QA generation.</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_175_105_1048_1367.jpg" alt="Image" width="71%" />

Instruction
Video & Response

What is the person doing with the wallpaper?
A. smoothing B. applying adhesive C. measuring
D. hanging on wall E. trimming
Please provide your answer by stating the letter followed by the full option and update your answer when it changed.

Provide a continuous narration of the video.
<Response> Text changes to "How to hang wallpaper"

List every event happening in the video.
<Response> A title card reads 'How to hang wallpaper'

<Response> Tools and materials appear.
<Response> A ladder appears on the right.

<Response> The necessary tools and materials for wallpapering are laid out on a table, including a bucket, a paint roller, a ladder, and a roll of wallpaper.

<Response> A man kneels down.
<Response> C. measuring
<Response> The man stands up.

<Response> A man in a yellow shirt kneels on the floor and marks the wallpaper.

<Response> The ruler is replaced by a level.
<Response> Powder is poured into the bucket.

<Response> He uses a ruler and pencil to measure and mark the wall where the wallpaper will be hung.

<Response> B. applying adhesive
<Response> The container is removed from the bucket.

<Response> D. hanging on wall
<Response> The wallpaper is smoothed out.
<Response> A. smoothing

<Response> He prepares the wallpaper by pouring powder from a container into a bucket and using a brush to apply the mixed water to the back of the wallpaper roll.

</div>


<div style="text-align: center;">Figure 6. Visualization of Streamo's outputs. We present the results of Streamo processing the same video under different task instructions and distinguish them using different colors, including TSQA, Narration, and Caption. Arrows indicate the frames corresponding to the response moment.</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_174_223_1048_1298.jpg" alt="Image" width="71%" />

<Response> The man moves closer to the window.

<Response> He climbs onto a wooden ladder and carefully places the wet wallpaper onto the wall, smoothing it down with his hands and a green sponge to ensure it adheres properly.

<Response> The man cuts the wallpaper.

<Response> The man switches to a green tool.

<Response> E. trimming

<Response> The man adjusts the wallpaper.

<Response> A ruler is placed against the wallpaper.

<Response> He measures the height of the window frame and cuts the excess wallpaper along the top edge with a utility knife.

<Response> Camera zoom out.

<Response> He trims the bottom edge of the wallpaper with a utility knife to fit the window sill.

<Response> A desk and chair appear.

<Response> The scene changes to a yellow background with text.

<Response> The logo for "builders" appears on a yellow background.

</div>


<div style="text-align: center;">Figure 7. This is a continuation of the previous figure, showing the results for the same video.</div>
