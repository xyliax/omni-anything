arXiv:2605.18577v1 [cs.CV] 18 May 2026

# OmniPro: A Comprehensive Benchmark for Omni-Proactive Streaming Video Understanding

Ruixiang Zhao $ ^{1} $ $ ^{ID} $ Jie Yang $ ^{2,*} $ Zijie Xin $ ^{1} $ $ ^{ID} $ Tianyi Wang $ ^{2} $ Fengyun Rao $ ^{2} $ Jing LYU $ ^{2} $ Xirong Li $ ^{1,*} $ $ ^{ID} $

 $ ^{1} $Renmin University of China  $ ^{2} $WeChat Vision, Tencent Inc.

Project page: https://ruixiangzhao.github.io/OmniPro

## Abstract

Omni-proactive streaming video understanding, i.e., autonomously deciding when to speak and what to say from continuous audio-visual streams, is an emerging capability of omni-modal large language models. Existing benchmarks fall short in three key aspects: they rely primarily on visual signals, adopt polling or fixed-timestamp protocols instead of true proactive evaluation, and cover only a limited range of tasks, preventing reliable assessment and differentiation of omni-proactive streaming models. We present OMNIPRO, the first benchmark to jointly evaluate omni-modal perception, proactive responding, and diverse video understanding tasks. It comprises 2,700 human-verified samples spanning 9 sub-tasks and 3 cognitive levels, covering 6 basic video understanding capabilities. Notably, 84% of samples require audio signals (speech or non-speech), and each sample is annotated with modality-isolation labels to enable fine-grained multimodal analysis. We further introduce a dual-mode evaluation protocol: Probe mode assesses content understanding by querying the model before and after each ground-truth trigger, while Online mode evaluates full proactive ability by requiring models to autonomously decide when to respond in streaming input. Evaluating 11 representative models reveals three key findings: (1) audio provides consistent gains but with highly variable utilization across models, (2) performance degrades significantly over time, indicating limited long-horizon robustness, and (3) non-speech audio perception remains the weakest dimension.

## 1 Introduction

Omni-proactive streaming video understanding, i.e., autonomously deciding when to speak and what to say based on continuous audio-visual signals, is emerging as a core capability of omni multimodal large language models. Despite growing interest in streaming and multimodal modeling [4, 23, 20, 18, 15, 6, 27], a fundamental question remains unanswered: what constitutes a good omni-proactive streaming model? We argue that such a model must satisfy three key criteria: (1) Omnimodal perception: it should jointly reason over visual signals, speech, and non-speech audio (e.g., environmental sounds), as real-world triggers are inherently multimodal. (2) Proactive responding: it must decide when to respond without external polling or fixed schedules, which distinguishes proactive behavior from passive response. (3) Diverse video understanding tasks: it should support a broad range of tasks beyond simple event alerting, including monitoring, grounding, counting, narration, and predictive reasoning, reflecting the complexity of real-world scenarios.

To assess these three criteria, a benchmark must be explicitly designed to test them in a unified framework. However, as shown in the left (blue-shaded) columns of Table 1, existing proactive streaming

 $ ^{*} $Corresponding authors: Xirong Li (xirong@ruc.edu.cn), Jie Yang (cvjieyang@tencent.com)

Preprint.

<div style="text-align: center;">Table 1: Benchmarks for proactive streaming video understanding. Blue-shaded columns: evaluation capability along the three proposed criteria. Orange-shaded columns: dataset statistics. "Resp./Ques.": average responses per question. "1st Resp.": average first response time.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Benchmark</td><td colspan="3">Evaluation Capability</td><td colspan="7">Dataset Statistics</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Omni</td><td style='text-align: center; word-wrap: break-word;'>Proactive</td><td style='text-align: center; word-wrap: break-word;'>Diversity</td><td style='text-align: center; word-wrap: break-word;'># Videos</td><td style='text-align: center; word-wrap: break-word;'>Dur. (s)</td><td style='text-align: center; word-wrap: break-word;'># Ques.</td><td style='text-align: center; word-wrap: break-word;'>Resp./Ques.</td><td style='text-align: center; word-wrap: break-word;'>1st Resp. (s)</td><td style='text-align: center; word-wrap: break-word;'>Sound</td><td style='text-align: center; word-wrap: break-word;'>Speech</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>StreamingBench-Pro [13]</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>1/6</td><td style='text-align: center; word-wrap: break-word;'>50</td><td style='text-align: center; word-wrap: break-word;'>636</td><td style='text-align: center; word-wrap: break-word;'>250</td><td style='text-align: center; word-wrap: break-word;'>1.0</td><td style='text-align: center; word-wrap: break-word;'>9.5</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>OVO-Bench-Pro [12]</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>2/6</td><td style='text-align: center; word-wrap: break-word;'>134</td><td style='text-align: center; word-wrap: break-word;'>625</td><td style='text-align: center; word-wrap: break-word;'>172</td><td style='text-align: center; word-wrap: break-word;'>9.1</td><td style='text-align: center; word-wrap: break-word;'>29.2</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>OmniMMI-Pro [21]</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>1/6</td><td style='text-align: center; word-wrap: break-word;'>400</td><td style='text-align: center; word-wrap: break-word;'>350</td><td style='text-align: center; word-wrap: break-word;'>400</td><td style='text-align: center; word-wrap: break-word;'>1.0</td><td style='text-align: center; word-wrap: break-word;'>36.4</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>OmNIPRO</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>6/6</td><td style='text-align: center; word-wrap: break-word;'>1,262</td><td style='text-align: center; word-wrap: break-word;'>189</td><td style='text-align: center; word-wrap: break-word;'>2,700</td><td style='text-align: center; word-wrap: break-word;'>3.4</td><td style='text-align: center; word-wrap: break-word;'>54.1</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td></tr></table>

benchmarks² fall short across all three dimensions. For omni-modal perception, StreamingBench-Pro [13] and OVO-Bench-Pro [12] rely exclusively on visual cues, while OmniMMI-Pro [21] involves only ~35% speech content with no non-speech sound; none can differentiate omni-modal models from vision-only counterparts. For proactive responding, StreamingBench-Pro polls the model every second and OVO-Bench-Pro queries the model at several preset time points; both remain essentially offline and do not allow the model to initiate responses on its own. Only OmniMMI-Pro lets the model freely decide when to respond, yet it permits only a single response per question, leaving multi-trigger decision-making untested. For diverse video understanding tasks, all three benchmarks exhibit severely limited coverage, capturing only a small fraction of the basic capability space. Overall, no existing benchmark simultaneously evaluates all three criteria, resulting in a clear evaluation gap that contrasts sharply with the rapid emergence of proactive streaming models.

To address these limitations, we present OMNIPRO, the first comprehensive benchmark for omni-proactive streaming video understanding. As illustrated in Figure 1, OMNIPRO contains 2,700 human-verified samples spanning 9 sub-tasks, organized into three cognitive levels that map to 6 basic video understanding capabilities. At the data level, 84% of samples depend on audio information (speech or non-speech sound), and each sample carries modality-isolation labels enabling fine-grained multi-modal ablation. At the evaluation level, we introduce a dual-mode protocol: Probe evaluates content understanding by querying the model before and after each ground-truth trigger time without requiring streaming capability, while Online mode evaluates full proactive ability by requiring models to autonomously decide when to respond in a continuous video stream. Overall, OMNIPRO is the first benchmark to jointly evaluate omni-modal perception, proactive responding, and diverse video understanding tasks within a unified framework.

We evaluate 11 representative models on OMNIPRO, spanning open-source and proprietary systems in both probe and online modes. Key findings include: (1) current omni models benefit from audio yet differ markedly in their utilization ability, with audio-visual input outperforming video-only input by +2.4 to +11.1 across models. (2) performance degrades substantially as triggers occur later in the video, with models retaining on average only 37% of their early-segment performance, indicating challenges in modeling long-term temporal dependencies. (3) non-speech sound perception (e.g., environmental sounds) remains the weakest dimension across all models. These results demonstrate the discriminative power of OMNIPRO and identify concrete open challenges for future research.

Our contributions are summarized as follows:

• Benchmark. We introduce OMNIPRO, the first comprehensive benchmark for omni-proactive streaming video understanding, comprising 2,700 human-reviewed samples across 9 sub-tasks with 84% audio dependency.

- Taxonomy. We design a hierarchical taxonomy across three cognitive levels that covers six basic video understanding capabilities. This framework enables a structured evaluation of omni-proactive streaming video understanding.

• Evaluation. We propose a dual-mode evaluation protocol: Probe for content understanding assessment and Online for full proactive ability evaluation.

• Analysis. We evaluate 11 representative models and identify key challenges, including heterogeneous audio utilization, long-horizon temporal degradation, and weak non-speech sound perception, providing insights for future research.

 $ ^{2} $The “-Pro” suffix denotes the proactive evaluation subset of each original benchmark.

2

<div style="text-align: center;"><img src="imgs/img_in_image_box_219_143_1004_727.jpg" alt="Image" width="64%" />

A: The second time. The third time.

</div>


<div style="text-align: center;">Figure 1: Overview of OMNIPRO. The benchmark comprises 9 sub-tasks organized into three cognitive levels, collectively covering 6 basic video understanding capabilities. Each panel shows a representative sample with its video frames, time-aligned triggers (marked by red triangles), user instruction (Q), and expected proactive responses (A). Audio-dependent triggers are prevalent across tasks, requiring models to perceive both visual and auditory signals.</div>


## 2 Related Work

### 2.1 Proactive Streaming Models

Proactive streaming video understanding requires models to autonomously decide when to respond while processing continuous video streams. Existing approaches to this “when-to-speak” problem fall into three categories: (1) Token-driven: the response timing decision is embedded in the autoregressive generation process via special tokens (e.g., EOS, Silence, or Response token), unifying when and what to speak [4, 23, 11, 14, 20, 30, 22, 29, 6]. (2) Classification-head: a lightweight, decoupled module explicitly classifies whether to respond at each timestep, separating the timing decision from content generation [18, 15, 7, 9, 26, 31, 10, 2]. (3) Signal-driven: response timing is governed by auxiliary signals (e.g., perplexity shifts, or visual scene changes), triggering a response when predefined criteria are met [27, 28]. With triggering mechanisms evolving from simple EOS prediction to reinforcement-learning optimization and sequence denoising, the rapid growth of proactive streaming models makes a comprehensive benchmark that can reliably distinguish a good omni-proactive model all the more pressing.

### 2.2 Proactive Streaming Video Benchmarks

We examine existing proactive benchmarks along the three dimensions shown in the blue-shaded columns of Table 1: (1) Omni-modal perception: whether the benchmark requires audio (speech and non-speech sound) to complete tasks, thereby distinguishing omni-modal models from vision-only ones. (2) Proactive responding: whether the model autonomously decides when to respond, rather than being polled or queried at preset time points. (3) Diverse video understanding tasks: how many of the 6 basic video understanding capabilities are covered.

3

StreamingBench-Pro [13] contains 250 purely visual questions from sports/gaming videos. The evaluator polls the model every second and terminates upon the first positive response, meaning each question triggers at most one response. All questions are visual-condition-based, requiring no audio. It covers only Alert (1/6 capabilities). OVO-Bench-Pro [12], despite being labeled "proactive", is effectively multi-point static QA. OVO-Bench-Pro queries the model at several preset time points, remaining essentially offline. Since the model never initiates responses on its own, proactive responding is not evaluated. It covers Counting and weak Monitoring (2/6), again without audio involvement. OmniMMI-Pro [21] is the only existing benchmark that supports genuine proactive responding: its Proactive Alert subset lets the model freely decide when to respond in an online streaming setting, and ~35% of questions require understanding speech content. However, this subset allows only a single response per question, leaving multi-trigger decision-making untested. Moreover, speech is the only audio modality involved, and non-speech sound is entirely absent. Its Proactive Turn-Taking subset is a classification task unrelated to video understanding. Overall, only Alert (1/6) is covered.

In summary, no existing benchmark simultaneously satisfies all three criteria (see Table 1): none involves non-speech sound, only OmniMMI-Pro supports proactive responding (limited to single-trigger), and at most 2/6 capabilities are covered. OMNIPRO systematically addresses these gaps: 84% of samples require or benefit from audio (both speech and non-speech sound), online evaluation supports multiple responses per question with penalties for over-triggering, and 9 sub-tasks comprehensively cover all 6 capabilities.

## 3 Proposed Benchmark

This section describes OMNIPRO in two parts. Section 3.1 presents how the benchmark is constructed, including the task taxonomy, data sources, automated generation pipeline, human quality control, and resulting dataset statistics. Section 3.2 describes how to use the benchmark, detailing the dual-mode evaluation protocol and associated metrics.

### 3.1 Construction of OMNIPRO

#### 3.1.1 Task Taxonomy

We categorize tasks by cognitive ability into three levels, namely Perception, Comprehension, and Reasoning, with increasing difficulty. This yields 9 sub-tasks and 2,700 evaluation samples in total, see Figure 1 for the complete taxonomy.

Instant Event Alert (Event-Alert) [Perception]. The user specifies a concrete instantaneous event (e.g., a doorbell ringing or a referee's whistle), and the model must issue an alert the moment it occurs. The core challenge is low-latency signal-level pattern matching.

Real-time State Monitoring (State-Monitor) [Perception]. The model continuously monitors a discrete state variable and proactively reports whenever a transition occurs, stating from and to which state (e.g., “monitor the dashboard temperature and report changes”). By contrast to Event-Alert, State-Monitor requires sustained perception combined with short-term memory.

Snapshot Counting (Snap.-Count) [Perception]. The model must autonomously detect trigger events (audio or visual) in the video stream and, upon each trigger, count the designated targets currently present in the scene (e.g., “every time the referee blows the whistle, count the players on the field”). The core challenge lies in coupling event detection with instantaneous counting.

Explicit Target Grounding (Target-Ground) [Perception]. The user specifies a target category, and the model proactively provides its spatial coordinates when the target appears (e.g., “when a white cat appears, give its coordinates”), combining proactive detection with spatial localization.

Event Narration (Event-Narr.) [Comprehension]. The model performs real-time narration of the streaming content (e.g., “provide live commentary for this football match”), autonomously determining when noteworthy events occur and proactively producing descriptions. This task demands continuous semantic understanding together with decisions on output timing and granularity.

Cumulative Counting (Cum.-Count) [Comprehension]. The model incrementally counts occurrences of a specified event across time (e.g., “count how many times the host says ‘thank you’”),

4

demanding persistent tracking and count updates over extended horizons, unlike the snapshot counting in Snap.-Count.

Semantic Condition Alert (Cond.-Alert) [Comprehension]. The user provides an abstract condition (e.g., “alert me when someone uses inappropriate language”), and the model must understand its semantics and issue an alert when satisfied. Unlike Event-Alert, the trigger is an abstract concept requiring semantic reasoning rather than a concrete physical signal.

Deduplicated Counting (Dedup.-Count) [Reasoning]. The model counts the number of distinct targets throughout the video (e.g., “how many different persons appeared in total?”). Unlike Cum.-Count, Dedup.-Count requires determining whether a currently observed target has appeared before, involving cross-temporal re-identification.

Sequential Step Instruction (Step-Inst.) [Reasoning]. The model assesses the user's current progress in a procedural task and proactively provides next-step guidance at the right moment (e.g., "teach me to cook scrambled eggs with tomatoes and tell me the next step"). This jointly demands temporal understanding, visual state estimation, and knowledge-based reasoning.

Collectively, these 9 sub-tasks cover 6 basic video understanding capabilities (Alert, Monitoring, Grounding, Counting, Narration, and Prediction), as illustrated in Figure 1.

#### 3.1.2 Source Video Collection

Source videos were drawn from the test sets of two public datasets: LongVALE [8] and COIN [17]. LongVALE is a high-quality audio-visual correlation dataset containing diverse long-form videos spanning daily life, sports, and news broadcasts, from which we collected 1,171 videos to supply material for most sub-tasks. However, LongVALE contains limited instructional videos with clear procedural steps as required by the Step-Inst. sub-task. To address this, we randomly sampled 600 videos from the COIN test set, which provides comprehensive coverage of step-by-step instructional content. In total, we obtained 1,771 source videos for subsequent QA generation.

#### 3.1.3 Automated QA Generation

Dense Captioning. For each source video, we employed Gemini 3 Flash to generate temporally aligned multi-modal dense captions with start and end timestamps for each segment. Each segment was described along four fields: caption (event omni-summary), visual (scene details), audio (ambient sounds and music), and speech (transcribed spoken content).

QA Pair Synthesis. We fed both the original video and the dense captions to Gemini 3 Flash, along with a task-specific prompt, to synthesize structured QA samples. Each sample contains the following fields: (1) question: a natural-language standing instruction issued at the start of the video; (2) trigger time: the precise timestamp at which the model should respond; (3) response: the expected proactive output at each trigger time; (4) trigger modality: the modality required to detect the trigger (visual / sound / speech, or combinations); and (5) audio dependency: whether audio is required, helpful, or unnecessary to answer the question.

The generation process adhered to three principles. For question design, we adopted an audio-first strategy: prioritize events from the audio and speech fields, resorting to visual events only as a supplement. For response generation, we enforced a streaming constraint: responses must only reference information available up to the trigger time, without using any future video content. For trigger time accuracy, we treated the video as ground truth: the dense caption served as a reference, but all timestamps were verified against the actual video content.

Following this pipeline, we automatically generated approximately 1,000 samples per sub-task, yielding 9,000 raw QA samples in total. The full prompt templates for dense captioning and QA generation are provided in the appendix.

#### 3.1.4 Human Quality Control

The auto-generated data underwent two rounds of human review. In the first round, 9 annotators each reviewed one sub-task using a dedicated tool, verifying question naturalness, trigger time accuracy (the precise moment when the trigger event has fully occurred), response faithfulness (free of hallucination), and modality annotation correctness. Annotators revised flawed samples

5

<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Category</th><th style='text-align: center;'>Required (%)</th><th style='text-align: center;'>Helpful (%)</th><th style='text-align: center;'>None (%)</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>Perception</td><td style='text-align: center;'></td><td style='text-align: center;'></td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>Event-Alert</td><td style='text-align: center;'>87.3</td><td style='text-align: center;'>7.0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>Target-Ground</td><td style='text-align: center;'>96.0</td><td style='text-align: center;'></td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>State-Monitor</td><td style='text-align: center;'>52.7</td><td style='text-align: center;'>14.7</td><td style='text-align: center;'>32.6</td></tr>
    <tr><td style='text-align: center;'>Snap-Count</td><td style='text-align: center;'>75.7</td><td style='text-align: center;'>12.7</td><td style='text-align: center;'>11.6</td></tr>
    <tr><td style='text-align: center;'>Comprehension</td><td style='text-align: center;'></td><td style='text-align: center;'></td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>Cond.-Alert</td><td style='text-align: center;'>87.3</td><td style='text-align: center;'>9.0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>Cum.-Count</td><td style='text-align: center;'>66.0</td><td style='text-align: center;'>9.7</td><td style='text-align: center;'>24.3</td></tr>
    <tr><td style='text-align: center;'>Event-Narr</td><td style='text-align: center;'>68.0</td><td style='text-align: center;'></td><td style='text-align: center;'>30.3</td></tr>
    <tr><td style='text-align: center;'>Reasoning</td><td style='text-align: center;'></td><td style='text-align: center;'></td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>Dedup.-Count</td><td style='text-align: center;'>54.0</td><td style='text-align: center;'>40.3</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>Step-Inst.</td><td style='text-align: center;'>50.7</td><td style='text-align: center;'>27.3</td><td style='text-align: center;'>22.0</td></tr>
  </tbody>
</table>

<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Category</th><th style='text-align: center;'>Percentage (%)</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>Visual+Speech</td><td style='text-align: center;'>42.3</td></tr>
    <tr><td style='text-align: center;'>Visual+Sound</td><td style='text-align: center;'>6.4</td></tr>
    <tr><td style='text-align: center;'>Visual</td><td style='text-align: center;'>23.8</td></tr>
    <tr><td style='text-align: center;'>Speech</td><td style='text-align: center;'>22.7</td></tr>
    <tr><td style='text-align: center;'>Visual+Speech+Sound</td><td style='text-align: center;'>3.0</td></tr>
    <tr><td style='text-align: center;'>Sound</td><td style='text-align: center;'>1.7</td></tr>
  </tbody>
</table>

<div style="text-align: center;">(b) Trigger modality ratio</div>


<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Feature</th><th style='text-align: center;'>Value</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>community</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>music</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>car</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>Initial</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>First Interviewed</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>logo</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>Sound Effect</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>Sound Character</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>Sound Location</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>end player</td><td style='text-align: center;'>Host: 2</td></tr>
    <tr><td style='text-align: center;'>Setting</td><td style='text-align: center;'>Segment: 2</td></tr>
    <tr><td style='text-align: center;'>Address</td><td style='text-align: center;'>2</td></tr>
    <tr><td style='text-align: center;'>Safety</td><td style='text-align: center;'>2</td></tr>
    <tr><td style='text-align: center;'>Opening</td><td style='text-align: center;'>2</td></tr>
    <tr><td style='text-align: center;'>Opening Speech</td><td style='text-align: center;'>2</td></tr>
    <tr><td style='text-align: center;'>Narrator</td><td style='text-align: center;'>2</td></tr>
    <tr><td style='text-align: center;'>First Playing Boy</td><td style='text-align: center;'>2</td></tr>
    <tr><td style='text-align: center;'>Speaking</td><td style='text-align: center;'>2</td></tr>
    <tr><td style='text-align: center;'>personal feature</td><td style='text-align: center;'>2</td></tr>
    <tr><td style='text-align: center;'>camera</td><td style='text-align: center;'>2</td></tr>
    <tr><td style='text-align: center;'>Center文章</td><td style='text-align: center;'>2</td></tr>
    <tr><td style='text-align: center;'>Interview photo</td><td style='text-align: center;'>2</td></tr>
    <tr><td style='text-align: center;'>Interview弱项</td><td style='text-align: center;'>2</td></tr>
    <tr><td style='text-align: center;'>Interview group</td><td style='text-align: center;'>2</td></tr>
    <tr><td style='text-align: center;'>Interview video</td><td style='text-align: center;'>2</td></tr>
    <tr><td style='text-align: center;'>Interview talk</td><td style='text-align: center;'>2</td></tr>
    <tr><td style='text-align: center;'>Group Group</td><td style='text-align: center;'>2</td></tr>
    <tr><td style='text-align: center;'>Group Group Talks</td><td style='text-align: center;'>2</td></tr>
    <tr><td style='text-align: center;'>Interviewзапиле</td><td style='text-align: center;'>2</td></tr>
    <tr><td style='text-align: center;'>Interviewзапиле</td></tr>
    <tr><td style='text-align: center;'>Interviewзапиле</td></tr>
    <tr><td style='text-align: center;'>Interviewзапиле</td></tr>
    <tr><td style='text-align: center;'>Interviewзапиле</td></tr>
    <tr><td style='text-align: center;'>Interviewзапиле</td></tr>
    <tr><td style='text-align: center;'>Interviewзапиле</td></tr>
    <tr><td style='text-align: center;'>Interviewзапиле</td></tr>
    <tr><td style='text-align: center;'>Interviewзапиле</td></tr>
    <tr><td style='text-align: center;'>Interviewзапиле</td></tr>
    <tr><td style='text-align: center;'>Interviewзапиле</td></tr>
    <tr><td style='text-align: center;'>Interviewзапиле</td></tr>
    <tr><td style='text-align: center;'>Interviewзапиле</td></tr>
    <tr><td style='text-align: center;'>Interviewзапиле</td></tr>
    <tr><td style='text-align: center;'>Interviewзапиле</td></tr>
    <tr><td style='text-align: center;'>Interviewзапиле</td></tr>
    <tr><td style='text-align: center;'>Interviewзапиле</td></tr>
    <tr><td style='text-align: center;'>Interviewзапиле</td></tr>
    <tr><td style='text-align: center;'>Interviewзапиле</td></tr>
    <tr><td style='text-align: center;'>Interviewзапиле</td></tr>
    <tr><td style='text-align: center;'>Interviewзапиле</td></tr>
    <tr><td style='text-align: center;'>Interviewзапиле</td></tr>
    <tr><td style='text-align: center;'>Interviewзапиле</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>3</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>4</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>5</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>6</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>7</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>8</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>9</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>10</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>11</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>12</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>13</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>14</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>15</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>16</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>17</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>18</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>19</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>20</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>21</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>22</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>23</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>24</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>25</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>26</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>27</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>28</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>29</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>30</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>31</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>32</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>33</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>34</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>35</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>36</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>37</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>38</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>39</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>40</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>41</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>42</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>43</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>44</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>45</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>46</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>47</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>48</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>49</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>50</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>51</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>52</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>53</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>54</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>55</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>56</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>57</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>58</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>59</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>60</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>61</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>62</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>63</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>64</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>65</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>66</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>67</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>68</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>69</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>70</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>71</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>72</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>73</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>74</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>75</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>76</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>77</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>78</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>79</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>80</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>81</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>82</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>83</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>84</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>85</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>86</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>87</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>88</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>89</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>90</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>91</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>92</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>93</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>94</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>95</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>96</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>97</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>98</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>99</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>100</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>101</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>102</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>103</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>104</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>105</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>106</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>107</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>108</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>109</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>110</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>111</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>112</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>113</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>114</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>115</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>116</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>117</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>118</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>119</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>120</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>121</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>122</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>123</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>124</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>125</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>126</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>127</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>128</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>129</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>130</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>131</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>132</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>133</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>134</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>135</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>136</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>137</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>138</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>139</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>140</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>141</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>142</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>143</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>144</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>145</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>146</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>147</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>148</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>149</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>150</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>151</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>152</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>153</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>154</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>155</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>156</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>157</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>158</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>159</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>160</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>161</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>162</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>163</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>164</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>165</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>166</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>167</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>168</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>169</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>170</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>171</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>172</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>173</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>174</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>175</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>176</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>177</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>178</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>179</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>180</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>181</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>182</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>183</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>184</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>185</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>186</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>187</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>188</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>189</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>190</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>191</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>192</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>193</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>194</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>195</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>196</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>197</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>198</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>199</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>200</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>201</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>202</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>203</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>204</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>205</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>206</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>207</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>208</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>209</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>210</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>211</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>212</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>213</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>214</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>215</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>216</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>217</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>218</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>219</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>220</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>221</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>222</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>223</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>224</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>225</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>226</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>227</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>228</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>229</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>230</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>231</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>232</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>233</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>234</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>235</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>236</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>237</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>238</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>239</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>240</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>241</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>242</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>243</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>244</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>245</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>246</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>247</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>248</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>249</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>250</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>251</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>252</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>253</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>254</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>255</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>256</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>257</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>258</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>259</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>260</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>261</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>262</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>263</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>264</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>265</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>266</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>267</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>268</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>269</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>270</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>271</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>272</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>273</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>274</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>275</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>276</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>277</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>278</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>279</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>280</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>281</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>282</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>283</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>284</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>285</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>286</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>287</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>288</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>289</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>290</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>291</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>292</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>293</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>294</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>295</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>296</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>297</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>298</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>299</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>300</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>301</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>302</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>303</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>304</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>305</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>306</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>307</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>308</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>309</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>310</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>311</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>312</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>313</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>314</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>315</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>316</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>317</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>318</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>319</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>320</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>321</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>322</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>323</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>324</td></tr>
    <tr><td style='text-align: center;'>Interview заплир</td><td style='text-align: center;'>325</td></tr>
    <tr><td style='text-align: center;'>Interview за</td></tr>
  </tbody>
</table>

<div style="text-align: center;">(a) Audio dependency per sub-task</div>


<div style="text-align: center;">(c) Trigger event word cloud</div>


<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Duration (sec)</th><th style='text-align: center;'>First trigger (%)</th><th style='text-align: center;'>Last trigger (%)</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>0-25</td><td style='text-align: center;'>25.0</td><td style='text-align: center;'>11.0</td></tr>
    <tr><td style='text-align: center;'>25-50</td><td style='text-align: center;'>19.0</td><td style='text-align: center;'>10.0</td></tr>
    <tr><td style='text-align: center;'>50-75</td><td style='text-align: center;'>13.0</td><td style='text-align: center;'>8.5</td></tr>
    <tr><td style='text-align: center;'>75-100</td><td style='text-align: center;'>9.0</td><td style='text-align: center;'>7.5</td></tr>
    <tr><td style='text-align: center;'>100-125</td><td style='text-align: center;'>0.0</td><td style='text-align: center;'>7.0</td></tr>
    <tr><td style='text-align: center;'>125-150</td><td style='text-align: center;'>0.0</td><td style='text-align: center;'>6.0</td></tr>
    <tr><td style='text-align: center;'>150-175</td><td style='text-align: center;'>0.0</td><td style='text-align: center;'>5.0</td></tr>
    <tr><td style='text-align: center;'>175-200</td><td style='text-align: center;'>0.0</td><td style='text-align: center;'>5.5</td></tr>
    <tr><td style='text-align: center;'>200-225</td><td style='text-align: center;'>0.0</td><td style='text-align: center;'>5.0</td></tr>
    <tr><td style='text-align: center;'>225-250</td><td style='text-align: center;'>0.0</td><td style='text-align: center;'>4.0</td></tr>
    <tr><td style='text-align: center;'>250-275</td><td style='text-align: center;'>0.0</td><td style='text-align: center;'>3.0</td></tr>
    <tr><td style='text-align: center;'>275-300</td><td style='text-align: center;'>0.0</td><td style='text-align: center;'>2.5</td></tr>
    <tr><td style='text-align: center;'>300-325</td><td style='text-align: center;'>0.0</td><td style='text-align: center;'>2.0</td></tr>
    <tr><td style='text-align: center;'>325-350</td><td style='text-align: center;'>0.0</td><td style='text-align: center;'>1.5</td></tr>
    <tr><td style='text-align: center;'>350-375</td><td style='text-align: center;'>0.0</td><td style='text-align: center;'>1.0</td></tr>
    <tr><td style='text-align: center;'>375-400</td><td style='text-align: center;'>0.0</td><td style='text-align: center;'>0.5</td></tr>
    <tr><td style='text-align: center;'>400-425</td><td style='text-align: center;'>0.0</td><td style='text-align: center;'>0.0</td></tr>
    <tr><td style='text-align: center;'>425-450</td><td style='text-align: center;'>0.0</td><td style='text-align: center;'>0.0</td></tr>
    <tr><td style='text-align: center;'>450-475</td><td style='text-align: center;'>0.0</td><td style='text-align: center;'>0.0</td></tr>
    <tr><td style='text-align: center;'>475-500</td><td style='text-align: center;'>0.0</td><td style='text-align: center;'>0.0</td></tr>
  </tbody>
</table>

<div style="text-align: center;">(d) First vs. last trigger time distribution</div>


<div style="text-align: center;">Figure 2: Dataset statistics of OMNIPRO.</div>


or discarded those of unacceptable quality. In the second round, annotators swapped sub-tasks for cross-validation, ensuring consistent standards across tasks. After both rounds, approximately 30% of samples were retained, yielding 2,700 samples across 1,262 videos.

#### 3.1.5 Dataset Statistics

Figure 2 visualizes the key distributional properties of OMNIPRO from four perspectives. Figure 2a shows the audio dependency per sub-task: tasks such as Target-Ground and Event-Alert are almost entirely audio-triggered, whereas Dedup.-Count relies primarily on vision. Figure 2b breaks down the trigger modality composition, revealing that visual+speech is the dominant type and nearly half of all triggers exhibit cross-modal characteristics, which ensures the benchmark can differentiate omni models from vision-only counterparts. Figure 2c displays the diversity of trigger events via a word cloud, showing broad coverage of both audio-related and visual-related triggers. Figure 2d depicts the distribution of first and last trigger times: the average first trigger occurs at 54.1 s and the last at 126.2 s, with a 72.1 s gap between them, indicating that models must sustain attention across extended durations to achieve high performance.

### 3.2 Use of OMNIPRO

#### 3.2.1 Evaluation Protocol

We design two complementary evaluation modes.

Probe mode is compatible with any VLM and does not require streaming capability. For each ground-truth trigger, the evaluator queries the model twice: a pre-probe  $ (-5 $ to  $ -2 $s before the trigger) and a post-probe  $ (0 $ to  $ +3 $s after). In both cases, the model receives the cumulative video frames  $ [0, t] $ up to the query time and returns a single response. A pre-probe expects a negative answer (the event has not yet occurred), while a post-probe expects the correct task-specific answer. All sub-tasks use dedicated prompt templates that constrain outputs into structured formats (e.g., YES/NO, a single integer, a state name, or a letter choice), including Event-Narr. and Step-Inst. which are converted into multiple-choice questions. Correctness is determined by exact match for all tasks.

6

For Probe mode, we report Accuracy. A ground-truth trigger is counted as correct only when both its pre-probe and post-probe are answered correctly. The final score is the proportion of correctly answered triggers over all triggers in the benchmark.

Online mode targets streaming models. The model receives the user instruction at the start of the video, then processes subsequent frames one by one together with its own dialogue history, and autonomously decides when to produce a response. No additional queries are issued during the stream. For most sub-tasks, correctness is verified via exact match on structured outputs (e.g., integer count, YES/NO). For open-ended generation tasks (i.e., Event-Narr. and Step-Inst.) where output cannot be constrained into a fixed format, we employ Gemini-3-Flash as an LLM judge to score each prediction against the ground truth on a 1–5 scale; a score  $ \geq 3 $ is considered correct.
For Online mode, we report F1. Model responses are matched to ground-truth triggers via greedy temporal alignment with a tolerance of  $ \pm3 $ s. A match is considered valid only if the response is also content-correct. Precision is the fraction of model responses that are validly matched, recall is the fraction of ground-truth triggers that are validly matched, and F1 is their harmonic mean.
Model applicability. Probe mode is applicable to any vision-language model, regardless of whether it supports streaming inference. Online mode requires models with native streaming capability, i.e., models that can process video frame-by-frame and autonomously emit responses. Models that support both paradigms (e.g., MiniCPM-o 4.5) can be evaluated under both modes, while non-streaming models (e.g., InternVL3.5, Owen3-VL) are evaluated in Probe mode only.

## 4 Experiments

### 4.1 Experimental Settings

Evaluated Models. We evaluate 11 representative models spanning two evaluation modes. In Probe mode, we assess 9 models: five open-source omni-modal models (Qwen2.5-Omni [24], Qwen3-Omni [25], 30B, video-SALMONN [27], and Phi-4 multimodal [1], 14B), two open-source vision-only models (InternVL3.5 [19], 8B, and Qwen3-VL [3], 8B), one proprietary omni-modal model (Gemini-3-Flash), and MiniCPM-o 4.5 [6] (9B) as the best-performing online model for cross-mode comparison. In Online mode, we evaluate 3 streaming models: MiniCPM-o 4.5 (omni-modal), MMDuet2 [20], and LiveStar [27], (8B, vision-only). This selection covers multiple contrast dimensions: omni-modal vs. vision-only, open-source vs. proprietary, and 3B to 30B parameter scales.

Implementation Details. All models uniformly sample input video at 1 fps. All open-source model inference is conducted on NVIDIA A800 80GB GPUs. Greedy decoding is used for all open-source models with a maximum generation length of 512 tokens.

### 4.2 Using OMNIPRO for Assessing Overall Model Capability

Table 2 presents the main results. Overall, current models achieve modest performance, confirming that omni-proactive streaming video understanding remains a challenging open problem. We highlight four observations. (1) Gemini-3-Flash attains 40.4% average accuracy, nearly double the best open-source model (22.1%), indicating a substantial capability gap between proprietary and open-source systems. (2) On audio-dependent tasks (e.g., Event-Alert), omni-modal models surpass vision-only counterparts by over 30 points, confirming that audio perception is critical and vision alone is insufficient for these tasks. (3) Online mode is considerably harder: MiniCPM-o 4.5 reaches only 20.9% F1, with severe degradation on generation-intensive tasks (Event-Narr. 6.9%, Step-Inst. 7.9%), exposing the coupled challenge of deciding when to speak and producing correct content simultaneously. (4) Reasoning-level tasks exhibit the largest capability gap (Step-Inst.: 76.3 for Gemini vs. 31.6 for the best open-source), suggesting that multi-step causal inference remains the most difficult capability to acquire.

### 4.3 Using OMNIPRO for Disentangling Modality Contributions

Table 3 reports five omni-modal models under audio-only (A), video-only (V), and full audio-visual (A+V) inputs to disentangle modality contributions. Three findings emerge. (1) A+V consistently outperforms either single modality, with gains over V ranging from +2.4 (Qwen3-Omni) to +11.1

7

<div style="text-align: center;">Table 2: Main results. Per mode, the best and second-best results are shown in bold and  $ \underline{\text{underline}} $.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Model</td><td rowspan="2">Params</td><td colspan="4">Perception</td><td colspan="3">Comprehension</td><td colspan="2">Reasoning</td><td rowspan="2">Mean</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Event-Alert</td><td style='text-align: center; word-wrap: break-word;'>Target-Ground</td><td style='text-align: center; word-wrap: break-word;'>State-Monitor</td><td style='text-align: center; word-wrap: break-word;'>Snap.-Count</td><td style='text-align: center; word-wrap: break-word;'>Cond.-Alert</td><td style='text-align: center; word-wrap: break-word;'>Cum.-Count</td><td style='text-align: center; word-wrap: break-word;'>Event-Narr.</td><td style='text-align: center; word-wrap: break-word;'>Dedup.-Count</td><td style='text-align: center; word-wrap: break-word;'>Step-Inst.</td></tr><tr><td colspan="12">Probe-mode evauation (metric: Accuracy):</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>InternVL3.5 [19]</td><td style='text-align: center; word-wrap: break-word;'>8B</td><td style='text-align: center; word-wrap: break-word;'>4.8</td><td style='text-align: center; word-wrap: break-word;'>2.4</td><td style='text-align: center; word-wrap: break-word;'>7.2</td><td style='text-align: center; word-wrap: break-word;'>6.0</td><td style='text-align: center; word-wrap: break-word;'>9.3</td><td style='text-align: center; word-wrap: break-word;'>5.3</td><td style='text-align: center; word-wrap: break-word;'>33.0</td><td style='text-align: center; word-wrap: break-word;'>21.3</td><td style='text-align: center; word-wrap: break-word;'>20.0</td><td style='text-align: center; word-wrap: break-word;'>12.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLaMA2.1-AV [5]</td><td style='text-align: center; word-wrap: break-word;'>7B</td><td style='text-align: center; word-wrap: break-word;'>21.8</td><td style='text-align: center; word-wrap: break-word;'>1.5</td><td style='text-align: center; word-wrap: break-word;'>5.6</td><td style='text-align: center; word-wrap: break-word;'>2.3</td><td style='text-align: center; word-wrap: break-word;'>24.1</td><td style='text-align: center; word-wrap: break-word;'>4.1</td><td style='text-align: center; word-wrap: break-word;'>27.8</td><td style='text-align: center; word-wrap: break-word;'>9.3</td><td style='text-align: center; word-wrap: break-word;'>14.0</td><td style='text-align: center; word-wrap: break-word;'>12.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Phi-4-multimodal [1]</td><td style='text-align: center; word-wrap: break-word;'>14B</td><td style='text-align: center; word-wrap: break-word;'>13.7</td><td style='text-align: center; word-wrap: break-word;'>5.1</td><td style='text-align: center; word-wrap: break-word;'>11.5</td><td style='text-align: center; word-wrap: break-word;'>6.0</td><td style='text-align: center; word-wrap: break-word;'>13.8</td><td style='text-align: center; word-wrap: break-word;'>2.0</td><td style='text-align: center; word-wrap: break-word;'>31.0</td><td style='text-align: center; word-wrap: break-word;'>16.1</td><td style='text-align: center; word-wrap: break-word;'>16.9</td><td style='text-align: center; word-wrap: break-word;'>12.9</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen3-VL [3]</td><td style='text-align: center; word-wrap: break-word;'>8B</td><td style='text-align: center; word-wrap: break-word;'>7.5</td><td style='text-align: center; word-wrap: break-word;'>2.8</td><td style='text-align: center; word-wrap: break-word;'>18.2</td><td style='text-align: center; word-wrap: break-word;'>13.1</td><td style='text-align: center; word-wrap: break-word;'>9.0</td><td style='text-align: center; word-wrap: break-word;'>11.2</td><td style='text-align: center; word-wrap: break-word;'>55.8</td><td style='text-align: center; word-wrap: break-word;'>31.8</td><td style='text-align: center; word-wrap: break-word;'>25.8</td><td style='text-align: center; word-wrap: break-word;'>19.5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-Omni [24]</td><td style='text-align: center; word-wrap: break-word;'>7B</td><td style='text-align: center; word-wrap: break-word;'>35.4</td><td style='text-align: center; word-wrap: break-word;'>8.5</td><td style='text-align: center; word-wrap: break-word;'>8.6</td><td style='text-align: center; word-wrap: break-word;'>18.0</td><td style='text-align: center; word-wrap: break-word;'>18.5</td><td style='text-align: center; word-wrap: break-word;'>9.0</td><td style='text-align: center; word-wrap: break-word;'>49.1</td><td style='text-align: center; word-wrap: break-word;'>15.3</td><td style='text-align: center; word-wrap: break-word;'>18.2</td><td style='text-align: center; word-wrap: break-word;'>20.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>video-SALMONN 2+ [16]</td><td style='text-align: center; word-wrap: break-word;'>7B</td><td style='text-align: center; word-wrap: break-word;'>37.2</td><td style='text-align: center; word-wrap: break-word;'>18.1</td><td style='text-align: center; word-wrap: break-word;'>12.3</td><td style='text-align: center; word-wrap: break-word;'>24.7</td><td style='text-align: center; word-wrap: break-word;'>17.6</td><td style='text-align: center; word-wrap: break-word;'>11.5</td><td style='text-align: center; word-wrap: break-word;'>41.3</td><td style='text-align: center; word-wrap: break-word;'>20.3</td><td style='text-align: center; word-wrap: break-word;'>15.6</td><td style='text-align: center; word-wrap: break-word;'>22.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen3-Omni [25]</td><td style='text-align: center; word-wrap: break-word;'>30B</td><td style='text-align: center; word-wrap: break-word;'>21.5</td><td style='text-align: center; word-wrap: break-word;'>10.4</td><td style='text-align: center; word-wrap: break-word;'>18.3</td><td style='text-align: center; word-wrap: break-word;'>19.3</td><td style='text-align: center; word-wrap: break-word;'>9.9</td><td style='text-align: center; word-wrap: break-word;'>15.3</td><td style='text-align: center; word-wrap: break-word;'>46.8</td><td style='text-align: center; word-wrap: break-word;'>30.0</td><td style='text-align: center; word-wrap: break-word;'>31.6</td><td style='text-align: center; word-wrap: break-word;'>22.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MiniCPM-o 4.5 [6]</td><td style='text-align: center; word-wrap: break-word;'>9B</td><td style='text-align: center; word-wrap: break-word;'>18.2</td><td style='text-align: center; word-wrap: break-word;'>16.4</td><td style='text-align: center; word-wrap: break-word;'>28.2</td><td style='text-align: center; word-wrap: break-word;'>28.0</td><td style='text-align: center; word-wrap: break-word;'>9.8</td><td style='text-align: center; word-wrap: break-word;'>27.9</td><td style='text-align: center; word-wrap: break-word;'>45.9</td><td style='text-align: center; word-wrap: break-word;'>32.5</td><td style='text-align: center; word-wrap: break-word;'>25.8</td><td style='text-align: center; word-wrap: break-word;'>25.8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Gemini-3-Flash</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>38.2</td><td style='text-align: center; word-wrap: break-word;'>12.1</td><td style='text-align: center; word-wrap: break-word;'>35.0</td><td style='text-align: center; word-wrap: break-word;'>21.0</td><td style='text-align: center; word-wrap: break-word;'>12.8</td><td style='text-align: center; word-wrap: break-word;'>42.7</td><td style='text-align: center; word-wrap: break-word;'>86.4</td><td style='text-align: center; word-wrap: break-word;'>39.6</td><td style='text-align: center; word-wrap: break-word;'>76.3</td><td style='text-align: center; word-wrap: break-word;'>40.4</td></tr><tr><td colspan="12">Online-mode evaluation (metric: F1):</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LiveStar [27]</td><td style='text-align: center; word-wrap: break-word;'>8B</td><td style='text-align: center; word-wrap: break-word;'>9.7</td><td style='text-align: center; word-wrap: break-word;'>0.8</td><td style='text-align: center; word-wrap: break-word;'>0.0</td><td style='text-align: center; word-wrap: break-word;'>0.0</td><td style='text-align: center; word-wrap: break-word;'>14.7</td><td style='text-align: center; word-wrap: break-word;'>0.0</td><td style='text-align: center; word-wrap: break-word;'>1.6</td><td style='text-align: center; word-wrap: break-word;'>0.0</td><td style='text-align: center; word-wrap: break-word;'>6.0</td><td style='text-align: center; word-wrap: break-word;'>3.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MMDuet2 [20]</td><td style='text-align: center; word-wrap: break-word;'>3B</td><td style='text-align: center; word-wrap: break-word;'>12.5</td><td style='text-align: center; word-wrap: break-word;'>5.3</td><td style='text-align: center; word-wrap: break-word;'>14.9</td><td style='text-align: center; word-wrap: break-word;'>11.2</td><td style='text-align: center; word-wrap: break-word;'>21.4</td><td style='text-align: center; word-wrap: break-word;'>5.3</td><td style='text-align: center; word-wrap: break-word;'>3.7</td><td style='text-align: center; word-wrap: break-word;'>12.7</td><td style='text-align: center; word-wrap: break-word;'>14.7</td><td style='text-align: center; word-wrap: break-word;'>11.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MiniCPM-o 4.5 [6]</td><td style='text-align: center; word-wrap: break-word;'>9B</td><td style='text-align: center; word-wrap: break-word;'>44.2</td><td style='text-align: center; word-wrap: break-word;'>13.9</td><td style='text-align: center; word-wrap: break-word;'>24.3</td><td style='text-align: center; word-wrap: break-word;'>21.2</td><td style='text-align: center; word-wrap: break-word;'>33.1</td><td style='text-align: center; word-wrap: break-word;'>16.4</td><td style='text-align: center; word-wrap: break-word;'>6.9</td><td style='text-align: center; word-wrap: break-word;'>20.5</td><td style='text-align: center; word-wrap: break-word;'>7.9</td><td style='text-align: center; word-wrap: break-word;'>20.9</td></tr></table>

<div style="text-align: center;">Table 3: Impact of input information for OmniLLMs. We conduct experiments across three input configurations: audio-only, video-only, and video with original audio. The  $ \Delta\uparrow $ in the Mean column of A+V denotes the absolute gain over V.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Model</td><td rowspan="2">Input</td><td colspan="4">Perception</td><td colspan="3">Comprehension</td><td colspan="2">Reasoning</td><td rowspan="2">Mean</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Event-Alert</td><td style='text-align: center; word-wrap: break-word;'>Target-Ground</td><td style='text-align: center; word-wrap: break-word;'>State-Monitor</td><td style='text-align: center; word-wrap: break-word;'>Snap-Count</td><td style='text-align: center; word-wrap: break-word;'>Cond.-Alert</td><td style='text-align: center; word-wrap: break-word;'>Cum.-Count</td><td style='text-align: center; word-wrap: break-word;'>Event-Narr.</td><td style='text-align: center; word-wrap: break-word;'>Dedup.-Count</td><td style='text-align: center; word-wrap: break-word;'>Step-Inst.</td></tr><tr><td rowspan="3">Qwen2.5-Omni [24]</td><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>33.3</td><td style='text-align: center; word-wrap: break-word;'>5.5</td><td style='text-align: center; word-wrap: break-word;'>7.3</td><td style='text-align: center; word-wrap: break-word;'>2.0</td><td style='text-align: center; word-wrap: break-word;'>16.6</td><td style='text-align: center; word-wrap: break-word;'>2.7</td><td style='text-align: center; word-wrap: break-word;'>35.9</td><td style='text-align: center; word-wrap: break-word;'>0.0</td><td style='text-align: center; word-wrap: break-word;'>15.1</td><td style='text-align: center; word-wrap: break-word;'>13.2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>V</td><td style='text-align: center; word-wrap: break-word;'>9.1</td><td style='text-align: center; word-wrap: break-word;'>4.1</td><td style='text-align: center; word-wrap: break-word;'>6.4</td><td style='text-align: center; word-wrap: break-word;'>10.0</td><td style='text-align: center; word-wrap: break-word;'>8.4</td><td style='text-align: center; word-wrap: break-word;'>5.4</td><td style='text-align: center; word-wrap: break-word;'>40.9</td><td style='text-align: center; word-wrap: break-word;'>16.7</td><td style='text-align: center; word-wrap: break-word;'>19.9</td><td style='text-align: center; word-wrap: break-word;'>13.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>A+V</td><td style='text-align: center; word-wrap: break-word;'>35.4</td><td style='text-align: center; word-wrap: break-word;'>8.5</td><td style='text-align: center; word-wrap: break-word;'>8.6</td><td style='text-align: center; word-wrap: break-word;'>18.0</td><td style='text-align: center; word-wrap: break-word;'>18.5</td><td style='text-align: center; word-wrap: break-word;'>9.0</td><td style='text-align: center; word-wrap: break-word;'>49.1</td><td style='text-align: center; word-wrap: break-word;'>15.3</td><td style='text-align: center; word-wrap: break-word;'>18.2</td><td style='text-align: center; word-wrap: break-word;'>20.1 (6.7\uparrow)</td></tr><tr><td rowspan="3">video-SALMONN 2+ [16]</td><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>42.4</td><td style='text-align: center; word-wrap: break-word;'>16.4</td><td style='text-align: center; word-wrap: break-word;'>3.6</td><td style='text-align: center; word-wrap: break-word;'>10.0</td><td style='text-align: center; word-wrap: break-word;'>14.7</td><td style='text-align: center; word-wrap: break-word;'>14.2</td><td style='text-align: center; word-wrap: break-word;'>40.0</td><td style='text-align: center; word-wrap: break-word;'>1.5</td><td style='text-align: center; word-wrap: break-word;'>14.4</td><td style='text-align: center; word-wrap: break-word;'>17.5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>V</td><td style='text-align: center; word-wrap: break-word;'>3.0</td><td style='text-align: center; word-wrap: break-word;'>3.6</td><td style='text-align: center; word-wrap: break-word;'>5.0</td><td style='text-align: center; word-wrap: break-word;'>8.0</td><td style='text-align: center; word-wrap: break-word;'>8.0</td><td style='text-align: center; word-wrap: break-word;'>6.9</td><td style='text-align: center; word-wrap: break-word;'>32.7</td><td style='text-align: center; word-wrap: break-word;'>16.8</td><td style='text-align: center; word-wrap: break-word;'>14.8</td><td style='text-align: center; word-wrap: break-word;'>11.0</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>A+V</td><td style='text-align: center; word-wrap: break-word;'>37.2</td><td style='text-align: center; word-wrap: break-word;'>18.1</td><td style='text-align: center; word-wrap: break-word;'>12.3</td><td style='text-align: center; word-wrap: break-word;'>24.7</td><td style='text-align: center; word-wrap: break-word;'>17.6</td><td style='text-align: center; word-wrap: break-word;'>11.5</td><td style='text-align: center; word-wrap: break-word;'>41.3</td><td style='text-align: center; word-wrap: break-word;'>20.3</td><td style='text-align: center; word-wrap: break-word;'>15.6</td><td style='text-align: center; word-wrap: break-word;'>22.1 (11.1\uparrow)</td></tr><tr><td rowspan="3">Qwen3-Omni [25]</td><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>19.7</td><td style='text-align: center; word-wrap: break-word;'>1.8</td><td style='text-align: center; word-wrap: break-word;'>5.0</td><td style='text-align: center; word-wrap: break-word;'>0.0</td><td style='text-align: center; word-wrap: break-word;'>7.4</td><td style='text-align: center; word-wrap: break-word;'>8.2</td><td style='text-align: center; word-wrap: break-word;'>25.0</td><td style='text-align: center; word-wrap: break-word;'>4.1</td><td style='text-align: center; word-wrap: break-word;'>16.8</td><td style='text-align: center; word-wrap: break-word;'>9.8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>V</td><td style='text-align: center; word-wrap: break-word;'>13.3</td><td style='text-align: center; word-wrap: break-word;'>8.4</td><td style='text-align: center; word-wrap: break-word;'>15.4</td><td style='text-align: center; word-wrap: break-word;'>16.8</td><td style='text-align: center; word-wrap: break-word;'>7.6</td><td style='text-align: center; word-wrap: break-word;'>8.5</td><td style='text-align: center; word-wrap: break-word;'>48.9</td><td style='text-align: center; word-wrap: break-word;'>30.0</td><td style='text-align: center; word-wrap: break-word;'>33.3</td><td style='text-align: center; word-wrap: break-word;'>20.2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>A+V</td><td style='text-align: center; word-wrap: break-word;'>21.5</td><td style='text-align: center; word-wrap: break-word;'>10.4</td><td style='text-align: center; word-wrap: break-word;'>18.3</td><td style='text-align: center; word-wrap: break-word;'>19.3</td><td style='text-align: center; word-wrap: break-word;'>9.9</td><td style='text-align: center; word-wrap: break-word;'>15.3</td><td style='text-align: center; word-wrap: break-word;'>46.8</td><td style='text-align: center; word-wrap: break-word;'>30.0</td><td style='text-align: center; word-wrap: break-word;'>31.6</td><td style='text-align: center; word-wrap: break-word;'>22.6 (2.4\uparrow)</td></tr><tr><td rowspan="3">Gemini-3-Flash</td><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>27.3</td><td style='text-align: center; word-wrap: break-word;'>1.8</td><td style='text-align: center; word-wrap: break-word;'>15.0</td><td style='text-align: center; word-wrap: break-word;'>2.0</td><td style='text-align: center; word-wrap: break-word;'>8.0</td><td style='text-align: center; word-wrap: break-word;'>23.7</td><td style='text-align: center; word-wrap: break-word;'>56.8</td><td style='text-align: center; word-wrap: break-word;'>8.1</td><td style='text-align: center; word-wrap: break-word;'>58.7</td><td style='text-align: center; word-wrap: break-word;'>22.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>V</td><td style='text-align: center; word-wrap: break-word;'>18.2</td><td style='text-align: center; word-wrap: break-word;'>9.1</td><td style='text-align: center; word-wrap: break-word;'>32.3</td><td style='text-align: center; word-wrap: break-word;'>24.0</td><td style='text-align: center; word-wrap: break-word;'>7.5</td><td style='text-align: center; word-wrap: break-word;'>24.7</td><td style='text-align: center; word-wrap: break-word;'>76.8</td><td style='text-align: center; word-wrap: break-word;'>37.1</td><td style='text-align: center; word-wrap: break-word;'>80.2</td><td style='text-align: center; word-wrap: break-word;'>34.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>A+V</td><td style='text-align: center; word-wrap: break-word;'>38.2</td><td style='text-align: center; word-wrap: break-word;'>12.1</td><td style='text-align: center; word-wrap: break-word;'>35.0</td><td style='text-align: center; word-wrap: break-word;'>21.0</td><td style='text-align: center; word-wrap: break-word;'>12.8</td><td style='text-align: center; word-wrap: break-word;'>42.7</td><td style='text-align: center; word-wrap: break-word;'>86.4</td><td style='text-align: center; word-wrap: break-word;'>39.6</td><td style='text-align: center; word-wrap: break-word;'>76.3</td><td style='text-align: center; word-wrap: break-word;'>40.4 (6.0\uparrow)</td></tr><tr><td rowspan="3">MiniCPM-o 4.5 [6]</td><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>42.6</td><td style='text-align: center; word-wrap: break-word;'>11.5</td><td style='text-align: center; word-wrap: break-word;'>6.6</td><td style='text-align: center; word-wrap: break-word;'>7.1</td><td style='text-align: center; word-wrap: break-word;'>18.1</td><td style='text-align: center; word-wrap: break-word;'>3.9</td><td style='text-align: center; word-wrap: break-word;'>3.8</td><td style='text-align: center; word-wrap: break-word;'>1.7</td><td style='text-align: center; word-wrap: break-word;'>2.7</td><td style='text-align: center; word-wrap: break-word;'>10.9</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>V</td><td style='text-align: center; word-wrap: break-word;'>14.9</td><td style='text-align: center; word-wrap: break-word;'>8.7</td><td style='text-align: center; word-wrap: break-word;'>23.3</td><td style='text-align: center; word-wrap: break-word;'>16.0</td><td style='text-align: center; word-wrap: break-word;'>15.7</td><td style='text-align: center; word-wrap: break-word;'>7.6</td><td style='text-align: center; word-wrap: break-word;'>3.5</td><td style='text-align: center; word-wrap: break-word;'>27.3</td><td style='text-align: center; word-wrap: break-word;'>7.5</td><td style='text-align: center; word-wrap: break-word;'>13.8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>A+V</td><td style='text-align: center; word-wrap: break-word;'>44.2</td><td style='text-align: center; word-wrap: break-word;'>13.9</td><td style='text-align: center; word-wrap: break-word;'>24.3</td><td style='text-align: center; word-wrap: break-word;'>21.2</td><td style='text-align: center; word-wrap: break-word;'>33.1</td><td style='text-align: center; word-wrap: break-word;'>16.4</td><td style='text-align: center; word-wrap: break-word;'>6.9</td><td style='text-align: center; word-wrap: break-word;'>20.5</td><td style='text-align: center; word-wrap: break-word;'>7.9</td><td style='text-align: center; word-wrap: break-word;'>20.9 (7.1\uparrow)</td></tr></table>

(video-SALMONN 2+), confirming that the two modalities provide complementary cues. (2) The relative strength of A vs. V is highly task-dependent: on Event-Alert, A dominates V across all models (e.g., 42.4 vs. 3.0 for video-SALMONN 2+), whereas on Dedup.-Count and Step-Inst., V substantially outperforms A (e.g., 30.0 vs. 4.1 for Qwen3-Omni). (3) Models exhibit divergent modality utilization patterns: video-SALMONN 2+ relies more heavily on audio (A: 17.5 vs. V: 11.0), while Qwen3-Omni is predominantly vision-driven (V: 20.2 vs. A: 9.8), revealing fundamental differences in audio encoding and multi-modal fusion capabilities.

8

### 4.4 Using OMNIPRO for Evaluating Long-Horizon Perception

Figure 3 groups performance by where the GT trigger is located along the video timeline: Short-term (0–60 s), Medium-term (60–180 s), and Long-term (180 s+). All models show substantial degradation for later-occurring triggers, retaining on average only 37% of their Short-term performance at the Long-term. MiniCPM-o 4.5 (Online mode) nearly fails entirely on the Long-term (29.1 → 0.3), indicating that current streaming models cannot sustain perception over extended video streams. Even Gemini-3-Flash, the strongest offline model, retains only 46% of its Short-term performance at the Long-term (38.5 → 17.9), confirming that all models struggle to perceive and respond to events occurring late in long videos.

<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Model</th><th style='text-align: center;'>Short-term (0-60s) Accuracy (%)</th><th style='text-align: center;'>Short-term (0-60s F1 (%))</th><th style='text-align: center;'>Medium-term (60-180s) Accuracy (%)</th><th style='text-align: center;'>Medium-term (60-180s F1 (%))</th><th style='text-align: center;'>Long-term (180s+) Accuracy (%)</th><th style='text-align: center;'>Long-term (180s+) F1 (%)</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>InternVL3.5</td><td style='text-align: center;'>13.9</td><td style='text-align: center;'>14.9</td><td style='text-align: center;'>5.3</td><td style='text-align: center;'>3.3</td><td style='text-align: center;'>3.3</td><td style='text-align: center;'>3.3</td></tr>
    <tr><td style='text-align: center;'>VideoLLaMA2.1-AV</td><td style='text-align: center;'>13.0</td><td style='text-align: center;'>13.0</td><td style='text-align: center;'>11.0</td><td style='text-align: center;'>9.1</td><td style='text-align: center;'>9.1</td><td style='text-align: center;'>9.1</td></tr>
    <tr><td style='text-align: center;'>Phi-4-multimodal</td><td style='text-align: center;'>18.9</td><td style='text-align: center;'>18.4</td><td style='text-align: center;'>9.2</td><td style='text-align: center;'>7.0</td><td style='text-align: center;'>7.0</td><td style='text-align: center;'>7.0</td></tr>
    <tr><td style='text-align: center;'>Qwen3-VL</td><td style='text-align: center;'>18.4</td><td style='text-align: center;'>27.6</td><td style='text-align: center;'>13.0</td><td style='text-align: center;'>7.7</td><td style='text-align: center;'>7.7</td><td style='text-align: center;'>7.7</td></tr>
    <tr><td style='text-align: center;'>Qwen2.5-Omni video-SALMONN2+</td><td style='text-align: center;'>30.5</td><td style='text-align: center;'>30.8</td><td style='text-align: center;'>18.8</td><td style='text-align: center;'>15.4</td><td style='text-align: center;'>9.9</td><td style='text-align: center;'>9.9</td></tr>
    <tr><td style='text-align: center;'>Qwen3-Omni Gemini-3-Flash</td><td style='text-align: center;'>38.5</td><td style='text-align: center;'>31.4</td><td style='text-align: center;'>31.4</td><td style='text-align: center;'>10.6</td><td style='text-align: center;'>17.9</td><td style='text-align: center;'>13.4</td></tr>
    <tr><td style='text-align: center;'>MMDuet2 MiniCPM-o 4.5</td><td style='text-align: center;'>14.9</td><td style='text-align: center;'>17.0</td><td style='text-align: center;'>9.7</td><td style='text-align: center;'>5.0</td><td style='text-align: center;'>5.0</td><td style='text-align: center;'>0.3</td></tr>
  </tbody>
</table>

<div style="text-align: center;">Figure 3: Performance grouped by where the GT trigger is located along the video timeline.</div>


### 4.5 Using OMNIPRO for Identifying Modality Bottlenecks

Figure 4 breaks down performance by the modality signals required to perceive each trigger event: visual only, speech, visual+speech, and visual+sound (non-speech audio). Gemini-3-Flash dominates on speech and visual+speech triggers (32.6 and 39.1, respectively), yet falls behind Qwen3-Omni on pure visual triggers (23.4 vs. 31.1), indicating that its advantage stems primarily from speech comprehension rather than visual perception. All models perform weakest on visual+sound triggers (15.3–22.3), revealing that perceiving and utilizing non-speech audio (e.g., environmental sounds, sound effects) remains a shared bottleneck.

<div style="text-align: center;"><img src="imgs/img_in_image_box_732_796_1003_1078.jpg" alt="Image" width="22%" />

Visual
Qwen2.5-Omni
Video-SALMONN2+
Qwen3-Omni
MiniCPM-o 4.5
Gemini-3-Flash
Sound
Video-SALMONN2+
Qwen3-Omni
MiniCPM-o 4.5
Gemini-3-Flash
Visual
Qwen2.5-Omni
Video-SALMONN2+
Qwen3-Omni
MiniCPM-o 4.5
Gemini-3-Flash
Visual
Qwen2.5-Omni
Video-SALMONN2+
Qwen3-Omni
MiniCPM-o 4.5
Gemini-3-Flash

</div>


<div style="text-align: center;">Figure 4: Performance breakdown by the modality signals required to perceive the trigger event.</div>


## 5 Conclusions

We have presented OMNIPRO, the first comprehensive benchmark for omni-proactive streaming video understanding, comprising 2,700 human-verified samples across 9 sub-tasks and 3 cognitive levels with 84% audio dependency, together with a dual-mode evaluation protocol (Probe and Online) that enables joint assessment of omni-modal perception, proactive responding, and diverse video understanding tasks. Evaluation of 11 representative models reveals that: (1) a substantial gap persists between proprietary and open-source systems (40.4% vs. 22.6%), particularly on reasoning-level tasks; (2) audio and video provide complementary cues, yet models exhibit divergent modality utilization patterns; (3) all models struggle to perceive events occurring late in long videos, with online streaming models nearly failing beyond 180 s; and (4) non-speech audio perception remains the weakest dimension across all models. We hope OMNIPRO serves as a useful testbed for driving progress toward genuine omni-proactive streaming video understanding.

9

## Acknowledgments and Disclosure of Funding

This research was supported by NSFC (No. 62576348), BJNSF (No. L254039) and Tencent WeChat Rhino-Bird Focused Research Program.

## References

[1] Abdelrahman Abouelenin, Atabak Ashfaq, Adam Atkinson, Hany Awadalla, Nguyen Bach, Jianmin Bao, Alon Benhaim, Martin Cai, Vishrav Chaudhary, Congcong Chen, et al. Phi-4-Mini technical report: Compact yet powerful multimodal language models via mixture-of-LoRAs. arXiv preprint arXiv:2503.01743, 2025.

[2] Shehreen Azad, Vibhav Vineet, and Yogesh Singh Rawat. StreamReady: Learning what to answer and when in long streaming videos. In CVPR, 2026.

[3] Shuai Bai, Yuxuan Cai, Ruizhe Chen, Keqin Chen, Xionghui Chen, Zesen Cheng, Lianghao Deng, Wei Ding, Chang Gao, Chunjiang Ge, et al. Qwen3-VL technical report. arXiv preprint arXiv:2511.21631, 2025.

[4] Joya Chen, Zhaoyang Lv, Shiwei Wu, Kevin Qinghong Lin, Chenan Song, Difei Gao, Jia-Wei Liu, Ziteng Gao, Dongxing Mao, and Mike Zheng Shou. VideoLLM-online: Online video large language model for streaming video. In CVPR, 2024.

[5] Zesen Cheng, Sicong Leng, Hang Zhang, Yifei Xin, Xin Li, Guanzheng Chen, Yongxin Zhu, Wenqi Zhang, Ziyang Luo, Deli Zhao, et al. VideoLLaMA 2: Advancing spatial-temporal modeling and audio understanding in Video-LLMs. arXiv preprint arXiv:2406.07476, 2024.

[6] Junbo Cui, Bokai Xu, Chongyi Wang, Tianyu Yu, Weiyue Sun, Yingjing Xu, Tianran Wang, Zhihui He, Wenshuo Ma, Tianchi Cai, et al. MiniCPM-o 4.5: Towards real-time full-duplex omni-modal interaction. arXiv preprint arXiv:2604.27393, 2026.

[7] Xin Ding, Hao Wu, Yifan Yang, Shiqi Jiang, Qianxi Zhang, Donglin Bai, Zhibo Chen, and Ting Cao. StreamMind: Unlocking full frame rate streaming video dialogue through event-gated cognition. In ICCV, 2025.

[8] Tiantian Geng, Jinrui Zhang, Qingni Wang, Teng Wang, Jinming Duan, and Feng Zheng. Long-VALE: Vision-audio-language-event benchmark towards time-aware omni-modal perception of long videos. In CVPR, 2025.

[9] Hyolim Kang, Yunsu Park, Youngbeom Yoo, Yeeun Choi, and Seon Joo Kim. Open-ended hierarchical streaming video understanding with vision language models. In ICCV, 2025.

[10] Junho Kim, Hosu Lee, James M. Rehg, Minsu Kim, and Yong Man Ro. STRIDE: When to speak meets sequence denoising for streaming video understanding. arXiv preprint arXiv:2603.27593, 2026.

[11] Wei Li, Bing Hu, Rui Shao, Leyang Shen, and Liqiang Nie. LION-FS: Fast & slow video-language thinker as online video assistant. In CVPR, 2025.

[12] Yifei Li, Junbo Niu, Ziyang Miao, Chunjiang Ge, Yuanhang Zhou, Qihao He, Xiaoyi Dong, Haodong Duan, Shuangrui Ding, Rui Qian, Pan Zhang, Yuhang Zang, Yuhang Cao, Conghui He, and Jiaqi Wang. OVO-Bench: How far is your Video-LLMs from real-world online video understanding? In CVPR, 2025.

[13] Junming Lin, Zheng Fang, Chi Chen, Haoxuan Cheng, Zihao Wan, Fuwen Luo, Ziyue Wang, Peng Li, Yang Liu, and Maosong Sun. StreamingBench: Assessing the gap for MLLMs to achieve streaming video understanding. In ICASSP, 2026.

[14] Zikang Liu, Longteng Guo, Handong Li, Ru Zhen, Xingjian He, Ruyi Ji, Xiaoming Ren, Yanhao Zhang, Haonan Lu, and Jing Liu. Thinking in streaming video. arXiv preprint arXiv:2603.12938, 2026.

10

[15] Rui Qian, Shuangrui Ding, Xiaoyi Dong, Pan Zhang, Yuhang Zang, Yuhang Cao, Dahua Lin, and Jiaqi Wang. Dispider: Enabling video LLMs with active real-time interaction via disentangled perception, decision, and reaction. In CVPR, 2025.

[16] Changli Tang, Yixuan Li, Yudong Yang, Jimin Zhuang, Guangzhi Sun, Wei Li, Zejun Ma, and Chao Zhang. video-SALMONN 2: Caption-enhanced audio-visual large language models. arXiv preprint arXiv:2506.15220, 2025.

[17] Yansong Tang, Dajun Ding, Yongming Rao, Yu Zheng, Danyang Zhang, Lili Zhao, Jiwen Lu, and Jie Zhou. COIN: A large-scale dataset for comprehensive instructional video analysis. In CVPR, 2019.

[18] Haibo Wang, Bo Feng, Zhengfeng Lai, Mingze Xu, Shiyu Li, Weifeng Ge, Afshin Dehghan, Meng Cao, and Ping Huang. StreamBridge: Turning your offline video large language model into a proactive streaming assistant. In NeurIPS, 2025.

[19] Weiyun Wang, Zhangwei Gao, Lixin Gu, Hengjun Pu, Long Cui, Xingguang Wei, Zhaoyang Liu, Linglin Jing, Shenglong Ye, Jie Shao, et al. InternVL3.5: Advancing open-source multimodal models in versatility, reasoning, and efficiency. arXiv preprint arXiv:2508.18265, 2025.

[20] Yueqian Wang, Songxiang Liu, Disong Wang, Nuo Xu, Guanglu Wan, Huishuai Zhang, and Dongyan Zhao. MMDuet2: Enhancing proactive interaction of video MLLMs with multi-turn reinforcement learning. In ICLR, 2026.

[21] Yuxuan Wang, Yueqian Wang, Bo Chen, Tong Wu, Dongyan Zhao, and Zilong Zheng. OmniMMI: A comprehensive multi-modal interaction benchmark in streaming video contexts. In CVPR, 2025.

[22] Shiwei Wu, Joya Chen, Kevin Qinghong Lin, Qimeng Wang, Yan Gao, Qianli Xu, Tong Xu, Yao Hu, Enhong Chen, and Mike Zheng Shou. VideoLLM-MoD: Efficient video-language streaming with mixture-of-depths vision computation. In NeurIPS, 2024.

[23] Jiaer Xia, Peixian Chen, Mengdan Zhang, Xing Sun, and Kaiyang Zhou. Streaming video instruction tuning. In CVPR, 2026.

[24] Jin Xu, Zhifang Guo, Jinzheng He, Hangrui Hu, Ting He, Shuai Bai, Keqin Chen, Jialin Wang, Yang Fan, Kai Dang, Bin Zhang, Xiong Wang, Yunfei Chu, and Junyang Lin. Qwen2.5-Omni technical report. arXiv preprint arXiv:2503.2021, 2025.

[25] Jin Xu, Zhifang Guo, Hangrui Hu, Yunfei Chu, Xiong Wang, Jinzheng He, Yuxuan Wang, Xian Shi, Ting He, Xinfa Zhu, et al. Qwen3-Omni technical report. arXiv preprint arXiv:2509.17765, 2025.

[26] Haolin Yang, Feilong Tang, Lingxiao Zhao, Xiang An, Ming Hu, Huifa Li, Xinlin Zhuang, Yifan Lu, Xiaofeng Zhang, Abdalla Swikir, et al. StreamAgent: Towards anticipatory agents for streaming video understanding. arXiv preprint arXiv:2508.01875, 2025.

[27] Zhenyu Yang, Kairui Zhang, Yuhang Hu, Bing Wang, Shengsheng Qian, Bin Wen, Fan Yang, Tingting Gao, Weiming Dong, and Changsheng Xu. LiveStar: Live streaming assistant for real-world online video understanding. In NeurIPS, 2025.

[28] Linli Yao, Yicheng Li, Yuancheng Wei, Lei Li, Shuhuai Ren, Yuanxin Liu, Kun Ouyang, Lean Wang, Shicheng Li, Sida Li, Lingpeng Kong, Qi Liu, Yuanxing Zhang, and Xu Sun. TimeChat-Online: 80% visual tokens are naturally redundant in streaming videos. In MM, 2025.

[29] Yichi Zhang, Xin Luna Dong, Zhaojiang Lin, Andrea Madotto, Anuj Kumar, Babak Damavandi, Joyce Chai, and Seungwhan Moon. Proactive assistant dialogue generation from streaming egocentric videos. In EMNLP, 2025.

[30] Yulin Zhang, Cheng Shi, Yang Wang, and Sibei Yang. Eyes Wide Open: Ego proactive Video-LLM for streaming video. In NeurIPS, 2025.

[31] Yikai Zheng, Xin Ding, Yifan Yang, Shiqi Jiang, Hao Wu, Qianxi Zhang, Weijun Wang, Ting Cao, and Yunxin Liu. Em-Garde: A propose-match framework for proactive streaming video understanding. arXiv preprint arXiv:2603.19054, 2026.

11

### A More Experimental Results

### A.1 Tolerance Window Ablation

<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Model</th><th style='text-align: center;'>Metric</th><th style='text-align: center;'>F1</th><th style='text-align: center;'>Precision</th><th style='text-align: center;'>Recall</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>MMDuet2</td><td style='text-align: center;'>**Tolerance (±s)**</td><td style='text-align: center;'></td><td style='text-align: center;'></td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>MMDuet2</td><td style='text-align: center;'>**score (%)**</td><td style='text-align: center;'></td><td style='text-align: center;'></td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>MMDuet2</td><td style='text-align: center;'>**±1**</td><td style='text-align: center;'>15.4</td><td style='text-align: center;'>18.9</td><td style='text-align: center;'>14.4</td></tr>
    <tr><td style='text-align: center;'>MMDuet2</td><td style='text-align: center;'>**±2**</td><td style='text-align: center;'>18.9</td><td style='text-align: center;'>22.4</td><td style='text-align: center;'>17.6</td></tr>
    <tr><td style='text-align: center;'>MMDuet2</td><td style='text-align: center;'>**±3**</td><td style='text-align: center;'>20.9</td><td style='text-align: center;'>24.9</td><td style='text-align: center;'>18.4</td></tr>
    <tr><td style='text-align: center;'>MMDuet2</td><td style='text-align: center;'>**±5**</td><td style='text-align: center;'>22.9</td><td style='text-align: center;'>27.2</td><td style='text-align: center;'>21.3</td></tr>
    <tr><td style='text-align: center;'>MMDuet2</td><td style='text-align: center;'>**±10**</td><td style='text-align: center;'>25.2</td><td style='text-align: center;'>30.0</td><td style='text-align: center;'>23.3</td></tr>
    <tr><td style='text-align: center;'>default</td><td style='text-align: center;'>**Tolerance (±s)**</td><td style='text-align: center;'></td><td style='text-align: center;'></td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>default</td><td style='text-align: center;'>**score (%)**</td><td style='text-align: center;'></td><td style='text-align: center;'></td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>default</td><td style='text-align: center;'>**±1**</td><td style='text-align: center;'>6.4</td><td style='text-align: center;'>6.9</td><td style='text-align: center;'>9.3</td></tr>
    <tr><td style='text-align: center;'>default</td><td style='text-align: center;'>**±2**</td><td style='text-align: center;'>9.3</td><td style='text-align: center;'>9.9</td><td style='text-align: center;'>13.2</td></tr>
    <tr><td style='text-align: center;'>default</td><td style='text-align: center;'>**±3**</td><td style='text-align: center;'>10.6</td><td style='text-align: center;'>11.3</td><td style='text-align: center;'>15.2</td></tr>
    <tr><td style='text-align: center;'>default</td><td style='text-align: center;'>**±5**</td><td style='text-align: center;'>11.6</td><td style='text-align: center;'>12.3</td><td style='text-align: center;'>16.5</td></tr>
    <tr><td style='text-align: center;'>default</td><td style='text-align: center;'>**×10**</td><td style='text-align: center;'>12.5</td><td style='text-align: center;'>13.3</td><td style='text-align: center;'>17.9</td></tr>
  </tbody>
</table>

<div style="text-align: center;">Figure 5: Tolerance window ablation (Online mode). Performance of online-mode models under varying temporal matching tolerances.</div>


Figure 5 shows the effect of varying the temporal matching tolerance on joint_F1 for three online-mode models (MiniCPM-o 4.5, MMDuet2, and LiveStar). The tolerance window ranges from  $ \pm1 $ s to  $ \pm5 $ s. We adopt  $ \pm3 $ s as the default in all Online-mode evaluations.

### B More Details of Data Construction

### B.1 Dense Captioning Prompt

We first generate temporally aligned multi-modal dense captions for each source video using Gemini 3 Flash. The following prompt template is used, where  $ \{\text{duration\_mmss}\} $,  $ \{\text{duration\_sec}\} $, and  $ \{\text{suggested\_segments}\} $ are filled per video.

Dense Captioning Prompt

You are an expert video analyst producing annotations for a video understanding dataset. Watch this video carefully - pay close attention to the visual content, sounds/music, and speech/dialogue simultaneously.

This video is {duration_mmss} long ({duration_sec:.0f} seconds).

Produce a dense temporal caption - divide the video into fine-grained segments. These captions will be used downstream to generate question-answer pairs about the video, so they must contain enough detail to support questions about what happened, when, why, what changed, and what can be inferred.

Segment guidelines:
- Each segment should be roughly 5-30 seconds long. No segment should exceed 45 seconds.
- For a {duration_sec:.0f}-second video, produce approximately {suggested_segments} segments.
- Start a new segment when there is: a scene/location change, a new activity or action, a topic shift in speech, a new person appearing or leaving, an audio event (music change, sound effect, silence), or any notable visual change.

12

For each segment, provide:

1. caption: A detailed, information-dense paragraph integrating visual, audio, and speech into one coherent description.
Include: Who (appearance, actions), What (objects, text), Action (specific verbs, direction), Change (differences from previous segment), Audio-visual correlation.

2. visual: Exhaustive visual details - scene, lighting, colors, objects, people, camera work, on-screen text verbatim.

3. audio: Precise sound description - music (genre, tempo, instruments), sound effects, ambient sounds, voice quality.
Note onset and cessation of sounds.

4. speech: Detailed summary of what is said - key claims, names, numbers, facts. If no speech, write "None".

Return a JSON array:
[
{
    "start": "MM:SS",
    "end": "MM:SS",
    "caption": "...",
    "visual": "...",
    "audio": "...",
    "speech": "..."
}
]

Rules:
- Segments must cover the entire video from 00:00 to {duration_mmss} with no gaps or overlaps.
- Timestamps in MM:SS format.
- Be maximally specific - names, colors, counts, positions.
- Return raw JSON only, no markdown.

### B.2 QA Generation Prompts

We provide condensed prompt templates used to generate QA pairs for each sub-task. All prompts share the system preamble “You are an expert at constructing QA benchmark data for evaluating proactive omni-modal assistants” and are fed to Gemini 2.5 Flash together with the source video and dense captions. Full prompts are available in the code repository.

Task

"Instant Event Alert" - user gives a standing instruction (e.g., "Let me know when the kettle whistles"); assistant watches/listens and proactively responds at the right moment(s) when the target event occurs.

## Input

1. Original video (ground truth).
2. Timestamped dense caption (supplementary reference). Duration: {duration_mmss} ({duration_sec:.0f}s).

## Steps

1. Choose an event (AUDIO-FIRST priority):
   - Audio-required (best): ONLY detectable by listening

13

(doorbell, whistle, spoken phrase, alarm, glass break)
- Audio-helpful: visible but audio confirms
- Visual-only (last resort): no meaningful audio

2. Write the question:
One natural standing instruction at 00:00. Must sound
like a real person talking to a smart assistant.
No spoilers, no timestamps, everyday language.

3. Write response(s) - one per event occurrence:
- State what happened, briefly and naturally.
- Include accurate trigger_time (MM:SS).
- Conversational tone, not robotic.

4. Classify each response:
- trigger_type: "visual" | "sound" | "speech" | combined
(e.g., "visual+sound", "visual+speech")
- audio_dependency: "required" | "helpful" | "none"
- trigger_type_reason: brief explanation

## Output (single JSON object, no markdown)
Fields: status, question, question_time ("00:00"),
audio_dependency, responses[] with: trigger_time,
response, trigger_type, trigger_type_reason,
event_description.
If no suitable event: {"status":"skip","reason":"..."}

## Rules
- Raw JSON only. Timestamps MM:SS in
[00:00, {duration_mmss}]
- Video is ground truth; caption is supplementary.
- Do NOT fabricate events not clearly present.
- Try your best to find an audio-required event.

### Explicit Target Grounding (ETG)

#### Task

"Explicit Target Grounding" - user specifies a target object and trigger condition. When trigger fires, assistant locates target in frame using a 3x3 grid. Tests: (1) detect trigger in real-time, (2) locate target spatially.

## Input
1. Original video (ground truth).
2. Timestamped dense caption (rough reference).
Duration: {duration_mmss} ({duration_sec:.0f}s).

### Steps

1. Find a trigger-target pair (AUDIO-FIRST): TRIGGER: instantaneous, real-time confirmable (NO "finishes/ends/completes"), unambiguous (maps to precise frame), naturally paired with target. OK: whistle->ball, "Maria" called->Maria TARGET: fits in ONE grid cell (highest priority). Never: full person, large vehicle, close-up face. Preferred: small held objects, accessories, buttons, logos, license plates, knobs. Visible at trigger moment. Single specific object.

2. Write the question:

One natural instruction at 00:00. Specify BOTH trigger

14

and target. Ask for position "in the frame"/"on screen".

3. Write response(s) - default exactly ONE (max 4):
   - Describe trigger event. State target location.
   - position: one of 9 grid cells ("top-left" |
        "top-center" | ... | "bottom-right")
   - trigger_time (MM:SS). Under 20 words.

4. Classify: trigger_type, audio_dependency.

## Output (single JSON object, no markdown)
Fields: status, question, question_time, audio_dependency,
responses[] with: trigger_time, response, position,
trigger_type, trigger_type_reason, event_description.
If no pair: {"status":"skip","reason":"..."}

## Rules
- Timestamps MM:SS in [00:00, {duration_mmss}].
- Position and trigger_time must be synchronized.
- Target MUST fit in ONE grid cell (highest priority).
- Trigger and target meaningfully connected.
- Prefer audio triggers. Video is ground truth.
- No hallucination. 1-4 responses; prefer 1.

### Realtime State Monitor (RSM)

Task
"Realtime State Monitor" - user asks assistant to monitor a discrete, observable state of a main subject and report whenever it transitions (e.g., sitting->standing, kitchen->living room, speaking->silent).

## Input
1. Original video (ground truth).
2. Timestamped dense caption (reference).
Duration: {duration_mmss} ({duration_sec:.0f}s).

## Steps
1. Choose a SPECIFIC PHYSICAL DIMENSION:
   Audio scan (MANDATORY) first:
    - Speakers taking turns? -> "who is speaking"
    - Music starts/stops? -> "whether music is playing"
    - Alternating sound sources?
  If any audio dimension works, use it.

  Visual scan (only if no audio):
  State must be: specific (ONE property), discrete, about main subject, changes 2+ times, objective.
  GOOD: posture, location/room, orientation, motion, object state, worn items, speaker identity, number of people, sound source, music present/absent.
  BAD: "activity" (open-ended), speed/volume (continuous), music mood (subjective), emotion.

2. Write the question:
   One natural monitoring instruction at 00:00.
   UNAMBIGUOUS. No spoilers. No state value lists.

3. Write responses - ONLY at transitions (2-5):
    - Name previous AND new state (from X -> to Y).
    - trigger_time (MM:SS), after 00:00. Under 15 words.

15

- Do NOT report initial state. Chronological.
4. Classify: trigger_type, audio_dependency.
Include audio_scan field.
## Output (single JSON object, no markdown)
Fields: status, audio_scan, question, question_time, audio_dependency, responses[] with: trigger_time, response, trigger_type, trigger_type_reason, event_description.
If no suitable state: {"status":"skip","reason":"..."}
## Rules
- Timestamps MM:SS in [00:00, {duration_mmss}]
- States must be DISCRETE with clear boundaries.
- Listen first. Prefer audio dimensions.
- Each response names from-state and to-state.
- Do NOT fabricate state changes. Aim 2-5 responses.

### Snapshot Counting (SC)

#### Task

# Task

"Snapshot Counting" - user specifies a trigger moment and a counting target naturally related to that trigger. When trigger occurs, assistant counts target entities at that instant. Tests: (1) detect trigger, (2) count accurately. Key: trigger and target must be naturally connected.

## Input

1. Original video (ground truth).
2. Timestamped dense caption (reference).

Duration: {duration_mmss} ({duration_sec:.0f}s).

## Steps

1. Find trigger + counting target (LISTEN FIRST):
    Good audio trigger->target pairs (naturally connected):
    - Whistle blows -> count players on field
    - Applause starts -> count performers on stage
    - "everyone ready?" -> count people in room
    - Timer buzzes -> count dishes on counter
    Bad (artificially forced):
    - "Hey" -> count people on sofa (no connection)

Visual scan (if no audio):
- New dish placed -> count all dishes
- Wide shot revealed -> count people

2. Write the question:
One natural counting instruction at 00:00.
Specifies BOTH trigger and counting target.
Natural language. No expected count revealed.

3. Write ONE response at trigger moment:
- Note trigger occurred. State exact count.
- count field with integer (for evaluation).
- trigger_time (MM:SS), after 00:00. Under 15 words.

4. Classify: trigger_type, audio_dependency.
Include audio_scan field.

Output (single JSON object, no markdown)

16

Fields: status, audio_scan, question, question_time, audio_dependency, responses[] (exactly one) with: trigger_time, response, count, trigger_type, trigger_type_reason, event_description.
If no pair: {"status":"skip","reason":"...""}

## Rules
- Timestamps MM:SS in [00:00, duration_mmss].
- Exactly ONE response. Must contain count (integer).
- Trigger and target NATURALLY CONNECTED.
- Listen first. Vary targets (not always people).
- Count must be accurate to what's visible at trigger.
- Do NOT fabricate triggers or counts.

### Semantic Condition Alert (SCA)

##### Task

"Semantic Condition Alert" - user describes a condition requiring semantic understanding (not keyword/object/sound detection). Assistant monitors and alerts each time the condition is met. Tests: (1) understand abstract intent, (2) map to concrete occurrences via reasoning, (3) alert at right times. Distinction from IEA: IEA=perception; SCA=comprehension/judgment.

##### Input

#### Steps

Find a natural condition (AUDIO-FIRST):

Must satisfy ALL:

A. Realistic - a real person would want this alert.

B. Requires semantic understanding (NOT perception):

Test: "Could a detector+classifier handle this?"

BAD: "when audience cheers" (sound classification)

GOOD: "when speaker provides a statistic as evidence"

C. Unambiguous (9/10 people flag same moments):

BAD: "when someone gives advice" (blurry)

D. Focus on EVENTS/ACTIONS, not linguistic analysis.

## 2. Write the question:

One natural monitoring instruction at 00:00. Describes condition clearly. No spoilers.

## 3. Write responses - one per occurrence:

- State what happened AND why it satisfies condition.

- Under 25 words. trigger_time (MM:SS), after 00:00.

- Speech: timestamp = when sentence ends.

## 4. Classify: trigger_type, audio_dependency.

Output (single JSON object, no markdown)

Fields: status, question, question_time, audio_dependency,

responses[] with: trigger_time, response, trigger_type,

trigger_type_reason, event_description.

If no condition: {"status":"skip","reason":"..."}

#### Rules

17

- At least 1 response. Each under 25 words.
- Condition must be realistic, unambiguous, and require semantic understanding (not perception-level).
- No hallucination - only confident observations.

semantic understanding (not perception-level).
- No hallucination - only confident observations.

Cumulative Counting (CC)

## Task
"Cumulative Counting" - user specifies a repeatable event.
Assistant detects each occurrence, keeps running tally,
reports updated cumulative count. Tests: (1) detect each
occurrence, (2) maintain count, (3) report at each event.
Key: events must be discrete and separable.

## Input
1. Original video (ground truth).
2. Timestamped dense caption (reference).
Duration: {duration_mmss} ({duration_sec:.0f}s).
Preferred Category: {preferred_category}

## Event Categories
A - Discrete non-speech sounds: impact, signals,
instrument hits, animal/body sounds.
B - Speech acts: questions, instructions, jokes,
laughter bursts. Each = one complete act.
C - Word/phrase repetitions: meaningful word said
multiple times. NOT: function words.
D - Repeating visual actions: exercise reps, chops,
spins. NOT: continuous stirring/swaying.

## Steps
1. Find event (try {preferred_category} first):
Discrete/separable (10 people agree), repeats 3+
times (aim 3-8), non-overlapping, unambiguous.

2. Write the question:
One natural counting instruction at 00:00.
Specifies event clearly. No count revealed.

3. Write responses - one per occurrence:
- Natural notification (NOT "Count: X").
- count: cumulative integer (1, 2, 3, ...).
- trigger_time (MM:SS), after 00:00. Under 20 words.
- Chronological, incrementing by exactly 1.

4. Classify: trigger_type, audio_dependency.
Include chosen_category field.

## Output (single JSON object, no markdown)
Fields: status, chosen_category, question, question_time,
audio_dependency, responses[] with: trigger_time,
response, count, trigger_type, trigger_type_reason,
event_description.
If <3 occurrences: {"status":"skip","reason":"...""}

## Rules
- Timestamps MM:SS in [00:00, {duration_mmss}].
- At least 3 responses. Each under 20 words.
- count increments by exactly 1 chronologically.
- Events MUST be discrete (10 people agree on count).
- No hallucination - only events clearly present.

18

### Event Narration (EN)

##### Task

"Event Narration" - user specifies a narration focus; assistant provides concise, factual updates at natural breakpoints. Tests: (1) real-time comprehension, (2) identifying breakpoints, (3) accurate summaries. NOT open-ended - always constrained to a specific focus.

#### Input

1. Original video (ground truth).

2. Timestamped dense caption (reference).

Duration: {duration_mmss} ({duration_sec:.0f}s).

#### Streaming Constraint

Real-time - NO future knowledge. Each update describes only what happened UP TO that point. NEVER use "concludes/climax/final/wraps up/ends with."

### Steps

1. Find a natural narration focus (satisfy ALL):

A. Specific and constrained (NOT "describe everything")

B. Multiple natural breakpoints (3+ stages).

C. Grounded in observable, verifiable facts.

D. Realistic. E. Integrates visual and audio.

## 2. Write the question:

One natural instruction at 00:00. Specifies focus, implies ongoing updates. No spoilers.

3. Write responses - one per breakpoint (aim 3-6):

- Factual summary since last update, within focus.

- Specific verifiable details (names, quantities).

- trigger_time (MM:SS). Under 40 words.

- Chronological. Each adds NEW information.

- Distributed across video (max 2 in first quarter).

## 4. Classify: trigger_type, audio_dependency.

Output (single JSON object, no markdown)

Fields: status, question, question_time, audio_dependency,

responses[] with: trigger_time, response, trigger_type,

trigger_type_reason, event_description.

If no focus: {"status":"skip","reason":"..."}

##### Rules

- Timestamps MM:SS in [00:00, {duration_mmss}].

- 3-6 responses. Each under 40 words. trigger_time>00:00.

- Stay within focus. Every fact verifiable from video.

- Narrate at natural breakpoints, not fixed intervals.

- NO "conclusion/finale/climax" language.

- Accuracy over coverage. Video is ground truth.

### Deduplicated Counting (DC)

##### Task

"Dedup Counting" - user specifies a target category. Assistant detects each unique new target, maintains tally of distinct targets, reports - ignoring re-appearances. Tests: (1) detect targets, (2) identity tracking, (3) only count genuinely new targets. Distinction from CC: CC counts events; DC counts unique entities.

19

### Input

1. Original video (ground truth).

2. Timestamped dense caption (rough reference).

Duration: {duration_mmss} ({duration_sec:.0f}s).

#### Steps

1. Check required appear/disappear/reappear pattern:

   - Targets appear at spread-out times?

   - At least one disappears and reappears later?

   - At least 3 unique targets?

   If no reappear pattern, return skip.

Find target category (must satisfy ALL):

- Distinct identities. Appear-disappear-reappear.

- 3+ targets, min 15s span. Unambiguous (9/10 agree).

- Precisely scoped with qualifier when noisy:

GOOD: "people interviewed on camera", "products picked up and demonstrated"

BAD: "different scenes" (vague)

## 3. Write the question:

One natural instruction at 00:00. Emphasizes unique/different. No expected count revealed.

4. Write responses - one per NEW unique target:

   - Describe what distinguishes from prior targets.

   - count: cumulative unique count (1, 2, 3, ...).

   - trigger_time = first appearance (MM:SS).

   - Under 20 words. NEVER count re-appearances.

## 5. Classify: trigger_type, audio_dependency.

Output (single JSON object, no markdown)

Fields: status, question, question_time, audio_dependency,

responses[] with: trigger_time, response, count,

trigger_type, trigger_type_reason, event_description.

If no dedup pattern or <3 targets: {"status":"skip",...}

##### Rules

- Timestamps MM:SS in [00:00, {duration_mmss}].

- At least 3 responses. Each under 20 words.

- NEVER count re-appearances. Count increments by 1.

- Appear-disappear-reappear pattern REQUIRED.

- Targets spread across time. Video is ground truth.

- Skip freely - quality over quantity.

#### Sequential Step Instruction (SSI)

##### Task

"Sequential Step Instruction" - user states a learning goal (following a tutorial). Assistant monitors in real time and tells user what to do next at the right moment. Tests: (1) understanding progress, (2) reasoning about next step, (3) timely instructions. Distinction from EN: EN is retrospective; SSI is prospective.

#### Input

1. Original video (ground truth).

2. Timestamped dense caption (reference).

Duration: {duration_mmss} ({duration_sec:.0f}s).

20

Constraints

- Real-time - no future knowledge. Instructions based on observations + domain knowledge.
- ONLY tutorials: cooking, DIY, repair, beauty, exercise.
NOT: interviews, vlogs, news, reviews, sports.
If not a replicable process, return skip.

## Steps

1. Determine suitability:
   Clear goal? Sequential steps? Observable?
   If any = NO, return skip.

2. Write the question:
   One natural instruction at 00:00. User wants to follow along. States learning goal. No spoilers.

3. Write responses - one per step transition:
   Timing: previous step completed, next not started.
   - Actionable instruction (WHAT + HOW).
   - Key parameters (quantities, temps, times).
   - Instructional language ("Now add...", "Next...") NOT descriptive ("He is adding...").
   - Verified by video. trigger_time (MM:SS).
   - Under 40 words. Chronological.

4. Classify: trigger_type, audio_dependency.

## Output (single JSON object, no markdown)

Fields: status, question, question_time, audio_dependency, responses[] with: trigger_time, response, trigger_type, trigger_type_reason, event_description.
If not tutorial: {"status":"skip","reason":"..."}

## Rules

- Timestamps MM:SS in [00:00, duration_mmss].
- At least 3 responses. Each under 40 words.
- Instructions MUST match what happens in video.
- Instructional language (address user as "you").
- Trigger at step transitions, not mid-step.
- Skip freely - most videos are NOT tutorials.

### C Limitations, Broader Impacts, and Licenses

### C.1 Limitations

All questions and ground-truth annotations in OMNIPRO are written in English, which limits its applicability for evaluating multilingual or non-English proactive streaming models. Extending the benchmark to additional languages is left for future work.

### C.2 Broader Impacts

Positive impacts. OMNIPRO advances research on proactive AI assistants by providing the first standardized evaluation covering omni-modal perception, proactive responding, and diverse video understanding tasks. It facilitates fair comparison across models and identifies concrete capability gaps, guiding future research directions.

Potential risks. As with any video understanding benchmark, improved model capabilities could in principle be applied to unintended contexts. However, our benchmark evaluates general-purpose understanding abilities and does not introduce domain-specific risks beyond those inherent to the underlying models.

21

Mitigation. We release the benchmark under a CC BY-NC 4.0 license, prohibiting commercial use. The dataset contains only publicly available YouTube videos from existing research datasets, with no personally identifiable information in annotations.

### C.3 Licenses

• LongVALE [8]: CC-BY-NC-SA-4.0

COIN [17]: CC BY-NC 4.0

• OMNIPRO (our benchmark): CC BY-NC 4.0

• Evaluation code: MIT License

Our license (CC BY-NC 4.0) is compatible with the source dataset licenses. All source datasets are properly cited and their terms of use are respected.

22