arXiv:2605.17360v1 [cs.CV] 17 May 2026

# Omni-DuplexEval: Evaluating Real-time Duplex Omni-modal Interaction

Chaoqun He $ ^{1*} $ Mingyang Xiang $ ^{2*} $ Yingjing Xu $ ^{3} $ Bokai Xu $ ^{3} $ Junbo Cui $ ^{3} $

Jie Zhou $ ^{3} $ Yuan Yao $ ^{1\dagger} $ Lijie Wen $ ^{1\dagger} $

 $ ^{1} $Tsinghua University  $ ^{2} $Tongji University  $ ^{3} $ModelBest Inc.

Project: https://github.com/OpenBMB/Omni-DuplexEval

## Abstract

Real-time duplex interaction is essential for multimodal AI systems operating in real-world scenarios, where models must continuously process streaming inputs and respond at appropriate moments. However, most existing multimodal large language models (MLLMs) are evaluated in offline settings, where the entire video input is processed before any response is generated. While recent work has started to explore real-time duplex MLLMs, there is still no comprehensive benchmark or automatic evaluation method for this setting. To address this gap, we propose Omni-DuplexEval, a benchmark for systematically evaluating real-time duplex interaction. The benchmark consists of two complementary scenarios: (1) Real-Time Description, which evaluates the ability to generate continuous, time-aligned responses that track evolving multimodal inputs, and (2) Proactive Reminder, which evaluates the ability to identify salient events and respond at appropriate moments. Omni-DuplexEval contains 660 videos with fine-grained, human-annotated labels and precise temporal metadata, spanning 9 tasks grounded in real-world scenarios, where all questions are formulated as open-ended queries. We further introduce an automatic evaluation framework based on LLM-as-a-Judge, which enables systematic assessment by jointly evaluating response-content alignment and response timing through timestamp-aware and sequential reasoning, achieving strong alignment with human judgments. Experiments on state-of-the-art duplex MLLMs reveal substantial limitations. The best-performing model achieves only 39.6% overall, while scoring only 20.0% on Proactive Reminder. Our analysis identifies two key challenges: models struggle to balance timely responses with coherent, holistic content generation, and they often fail to determine both when to respond and what to produce. We hope our work facilitates further progress in MLLMs, particularly in real-time duplex interaction.

## 1 Introduction

Multimodal Large Language Models (MLLMs) have achieved strong performance on video understanding task, with recent systems such as GPT-4o [1] and Gemini-Pro [2] demonstrating impressive capabilities. However, most of existing models are designed for static images or offline video processing and must observe the entire video before producing a response. This setting is commonly used in current benchmarks, such as Video-MME [3], LVBench [4]. This offline setting differs fundamentally from real-world interaction, where perception and response are tightly coupled: humans observe, listen, and respond simultaneously [5], enabling continuous and real-time interaction without waiting for complete information. We refer to this capability as real-time duplex interaction, where models process continuously evolving inputs and produce responses at appropriate moments.

 $ ^{*} $Equal contribution. Emails: Chaoqun He (hecq25@mails.tsinghua.edu.cn)

 $ ^{\dagger} $Corresponding authors.

Preprint.

Recent advances have begun to explore streaming MLLMs that can process inputs and generate outputs incrementally. Systems such as LiveCC [6] demonstrate the ability to produce real-time video commentary, while MiniCPM-o 4.5 [7] supports full-duplex multimodal live streaming. These systems exhibit early forms of real-time duplex behavior.

<div style="text-align: center;"><img src="imgs/img_in_image_box_216_258_1006_871.jpg" alt="Image" width="64%" />

Please describe how the man’s hand movements change.

The man moves his hands into a frame, crosses them, reveals a feather, and then makes the feather disappear and reappear...

Duplex
Real-Time Description
t=4s: The man slowly moves both hands into the frame, forming a wing-like shape and raising them upward.
When a Jack card is first revealed, remind me.

Proactive Reminder
t=20s: A Jack card has just been revealed in the spread!

</div>


<div style="text-align: center;">Figure 1: Comparison between Omni-DuplexEval and offline evaluation paradigms. Offline settings require models to process the entire video before producing a response. In contrast, Omni-DuplexEval introduces two scenarios to evaluate real-time duplex capabilities, including continuous response generation over evolving video content and the ability to determine when to respond and what to say.</div>


However, current benchmarks for video understanding do not fully capture these capabilities. For example, StreamingBench [8] and OVOBench [9] primarily rely on multiple-choice formats and focus on final response quality, without capturing temporal alignment or continuous adaptation. OmniMMI [10] provides open-ended responses, but its answers are relatively simple and sparse, making it difficult to assess response quality in realistic settings. ProactiveVideoQA [11] and PhoStream [12] focus on proactivate detection and interaction, but lack fine-grained evaluation of temporal dynamics and response behavior over time. As a result, current benchmarks do not adequately evaluate real-time duplex capabilities.

To address this gap, we introduce Omni-DuplexEval, a benchmark designed to evaluate real-time duplex capabilities, where models are expected to process evolving video inputs and produce responses at appropriate moments. The benchmark is organized into two complementary scenarios as shown in Figure 1. Real-Time Description evaluates the ability to process evolving video inputs and generate responses continuously while adapting to changes in the video. Proactive Reminder evaluates the ability to detect relevant events and determine when to respond, producing appropriate outputs in response to user instructions grounded in the video. The benchmark includes 660 samples, each paired with an open-ended question and detailed human annotations. It covers 9 tasks designed to reflect real-world scenarios, spanning diverse domains such as entertainment, lifestyle, and education.

Furthermore, existing evaluation approaches are not well suited for assessing real-time duplex capabilities. To address this, we propose an automatic evaluation framework based on LLM-as-a-

2

Judge. The framework jointly evaluates semantic correctness and response timing, enabling flexible assessment of both what to say and when to say it. This provides a practical way to measure real-time duplex behavior beyond traditional final-answer-based evaluation.

We conduct extensive experiments on recent duplex omni-modal models. Results expose two fundamental gaps. In Real-time Description, models exhibit a completeness-timeliness trade-off, remaining silent for approximately 50-60% of the video duration and failing to provide continuous description. In Proactive Reminder, models struggle not with what to say but with when to say it. In most cases, models fail to produce responses at the appropriate time, often remaining silent. As a result, performance is consistently low, with the best model achieving only 20.0%. These findings suggest that current models remain far from supporting real-world interactive assistants. We hope that Omni-DuplexEval will facilitate future research on real-time duplex omni-modal interaction.

<div style="text-align: center;">Table 1: Comparison of Omni-DuplexEval with other representative video and audio-visual benchmarks. V = Visual, A = Audio, Sub = Subtitles, I = Image. Open-Ended denotes whether the benchmark evaluates free-form textual responses rather than multiple-choice questions. Streaming indicates the ability to handle sequential video inputs. Proactive evaluates whether the system can autonomously determine response timing without user queries. Temporal Alignment assesses the physical synchronization between streaming inputs and generated texts.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Benchmark</td><td style='text-align: center; word-wrap: break-word;'>Modality</td><td style='text-align: center; word-wrap: break-word;'>#Videos</td><td style='text-align: center; word-wrap: break-word;'>Open-Ended</td><td style='text-align: center; word-wrap: break-word;'>Streaming</td><td style='text-align: center; word-wrap: break-word;'>Proactive</td><td style='text-align: center; word-wrap: break-word;'>Temporal Alignment</td></tr><tr><td colspan="7">Offline Benchmarks</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MVBench [13]</td><td style='text-align: center; word-wrap: break-word;'>V</td><td style='text-align: center; word-wrap: break-word;'>3,641</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Video-MME [3]</td><td style='text-align: center; word-wrap: break-word;'>V, Sub</td><td style='text-align: center; word-wrap: break-word;'>900</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MLVU [14]</td><td style='text-align: center; word-wrap: break-word;'>V</td><td style='text-align: center; word-wrap: break-word;'>1,730</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LongVideoBench [15]</td><td style='text-align: center; word-wrap: break-word;'>V</td><td style='text-align: center; word-wrap: break-word;'>3,763</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>OmniBench [16]</td><td style='text-align: center; word-wrap: break-word;'>A, I</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>WorldSense [17]</td><td style='text-align: center; word-wrap: break-word;'>V, A</td><td style='text-align: center; word-wrap: break-word;'>1,662</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td colspan="7">Online Benchmarks</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>StreamingBench [8]</td><td style='text-align: center; word-wrap: break-word;'>V, A</td><td style='text-align: center; word-wrap: break-word;'>900</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>OVOBench [9]</td><td style='text-align: center; word-wrap: break-word;'>V</td><td style='text-align: center; word-wrap: break-word;'>644</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>OmniMMI [10]</td><td style='text-align: center; word-wrap: break-word;'>V, A</td><td style='text-align: center; word-wrap: break-word;'>1,121</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ProactiveVideoQA [11]</td><td style='text-align: center; word-wrap: break-word;'>V, A</td><td style='text-align: center; word-wrap: break-word;'>1,377</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>PhoStream [12]</td><td style='text-align: center; word-wrap: break-word;'>V, A</td><td style='text-align: center; word-wrap: break-word;'>578</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>RIVER [18]</td><td style='text-align: center; word-wrap: break-word;'>V</td><td style='text-align: center; word-wrap: break-word;'>1,067</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Omni-DuplexEval</td><td style='text-align: center; word-wrap: break-word;'>V, A</td><td style='text-align: center; word-wrap: break-word;'>660</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td></tr></table>

## 2 Related Works

### 2.1 Video MLLM

Multimodal Large Language Models (MLLMs) have evolved from early video understanding systems that rely on auxiliary signals to unified architectures integrating visual, audio, and textual information [19–21]. Recent "omni-modal" models aim to uniformly process multiple modalities within a single architecture [22–24]. Efficient MLLM designs have also emerged, achieving strong performance with fewer parameters through adaptive visual encoding [7, 25].

Despite these advances, most existing MLLMs operate under an offline paradigm. To address this, recent streaming models process inputs incrementally and support streaming generation, moving toward full-duplex multimodal interaction [26–28, 6, 29, 30]. Recent advances have also introduced scene-aware optimization for efficient long-context reasoning in streaming QA, as well as unified evaluation protocols that characterize trade-offs between efficiency, storage, and accuracy under realistic constraints [31, 32].

### 2.2 Evaluation Benchmarks

Traditional offline video understanding benchmarks have evolved from short-video perception to complex reasoning and long-form comprehension, covering multi-task evaluation and long video understanding [13, 3, 14–17]. Specialized benchmarks have also been developed for ego-centric and activity understanding [33–35]. A comprehensive survey systematically analyzes the landscape of VideoLLM benchmarks and evaluation methodologies [36].

3

Recent benchmarks have begun exploring streaming and real-time evaluation. Early efforts introduce streaming settings but largely rely on multiple-choice formats and focus on final response quality [8, 9, 37, 38]. Subsequent work moves toward interactive and proactive evaluation, incorporating event-driven tasks and proactive reasoning into streaming video understanding [10, 12, 18, 11]. More recent benchmarks propose continuous evaluation metrics and standardized protocols for assessing proactiveness and temporal consistency [39–42].

Beyond streaming settings, new benchmarks have been established for omni-modal understanding, evaluating multimodal reasoning on large-scale real-world videos with questions requiring tight coupling of visual and audio signals [43, 44]. For hallucination evaluation, recent work systematically defines multiple types of video QA hallucinations and constructs multi-round open-ended benchmarks [45]. For full-duplex spoken interaction, benchmarks have been proposed to evaluate turn-taking capabilities and handle real-time interruptions and overlapping speech [46, 47].

Despite these advances, existing benchmarks do not comprehensively evaluate real-time duplex interaction—the ability to generate continuous responses while maintaining temporal alignment with evolving video streams. They largely focus on discrete question-answering rather than continuous streaming generation, and treat response timing separately from content correctness. Our Omni-DuplexEval addresses these limitations through unified evaluation of what to say and when to say it. Table 1 presents a comparison between our benchmark and other representative benchmarks.

## 3 Omni-DuplexEval

### 3.1 Taxonomy

Real-time duplex capability requires models to process continuously evolving inputs and produce responses at appropriate moments. Based on this, Omni-DuplexEval is organized into two representative scenarios. Real-Time Description evaluates the ability to generate responses that follow evolving video content in real time. Proactive Reminder evaluates the ability to identify relevant events and determine when to respond. We describe these two scenarios in detail below.

#### 3.1.1 Real-Time Description

Real-Time Description evaluates the ability to generate responses that follow evolving video content in real time. At the beginning of each sample, the model receives a user instruction that specifies a particular subject or aspect of interest, and produces continuous, time-aligned responses as the video unfolds. The responses should remain grounded in the instruction while reflecting changes in the current temporal window, requiring the model to track dynamic visual and auditory information and update its outputs accordingly.

To evaluate this capability, we define six sub-tasks within the Real-Time Description as shown in Figure 2. (1) Counting (CT) assesses the model's capacity for incremental tallying and temporal consistency as it tracks the entry, exit, or occlusion of objects (e.g., fluctuating pedestrian counts) in a fluid scene. (2) Interaction Relation (IR) examines the model's understanding of the social or physical connections between multiple entities. It requires describing how people or objects interact as those relationships unfold dynamically. (3) Omni, as the most comprehensive task, Omni requires the model to synthesize both visual and auditory streams simultaneously. (4) World Knowledge (WK) evaluates the model's ability to identify specific attributes and categories—such as animal species, clothing materials, or commercial brands. (5) OCR focuses on dynamic text perception, this task requires the model to recognize and read out characters that evolve over time, such as scrolling subtitles or changing floor numbers in an elevator, demanding precise synchronization between visual transitions and textual output. (6) Fine-grained Movement (FM) focuses on capturing high-fidelity trajectories of complex movements, translating granular biological or mechanical actions (e.g., intricate hand gestures) into precise descriptors via short-term temporal dependencies.

#### 3.1.2 Proactive Reminder

Proactive Reminder evaluates the ability to identify relevant events and determine when to respond based on streaming video inputs. The model receives a user instruction that specifies a clear and well-defined event, and must monitor the incoming omni-modal stream to produce a response when the event occurs. This requires the model to retain the instruction, track visual and auditory information.

4


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td colspan="2">Real-Time Description</td></tr><tr><td rowspan="2">Counting</td><td style='text-align: center; word-wrap: break-word;'>Q: Please tell me in real time the count of sharks in the frame.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>A: Okay, there&#x27;s two sharks... Three sharks... Now one shark... One shark, three sharks...</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Interaction Relation</td><td style='text-align: center; word-wrap: break-word;'>Q: Please tell me in real time what he&#x27;s doing to the dog.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Omni</td><td style='text-align: center; word-wrap: break-word;'>A: He&#x27;s touching the dog... The man is hugging the dog... Look, the dog is sitting down obediently...</td></tr><tr><td rowspan="2">World Knowledge</td><td style='text-align: center; word-wrap: break-word;'>Q: Please describe in real time what instrument this person is playing when the music rings.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>A: I hear that he is playing the drums... Look, now he plays timpani... Then comes the xylophone... This is vibraphone...</td></tr><tr><td rowspan="2">OCR</td><td style='text-align: center; word-wrap: break-word;'>Q: Provide a real-time description of the clothing types and colors worn by the people in the video.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>A: And she&#x27;s wearing... He is wearing a black shirts... She is wearing an olive green top... She is wearing a floral dress...</td></tr><tr><td rowspan="4">Fine-grained Movement</td><td style='text-align: center; word-wrap: break-word;'>Q: Tell me which English letter this person taps on the screen with left hand in real time.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>A: He taps Y... then R... Then he taps B... Next he taps T... Then he taps D...</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Q: Real-time description of the cooking process.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>A: Okay, he takes off the plastic wrap... Then uses a rolling pin... He places the rolled-out dough onto a baking tray...</td></tr></table>

<div style="text-align: center;">Figure 2: Example of each task in Real-Time Description.</div>


over time, and decide both when to respond and what to say. In some cases, the instruction may appear at arbitrary points along the video timeline, requiring the model to relate it to past observations.

We further divide this scenario into three sub-tasks as shown in Figure 3: (1) Event Reminder (ER). The instruction describes a future event. The model monitors the video stream and produces a response when the event occurs. (2) Post-Event Reminder (PER). The instruction refers to a past event. The model determines whether the event occurs again and produces a response accordingly. (3) Correction (CR). The instruction contains an incorrect description of the video. The model is expected to revise the description based on the observed content.

Together, these two scenarios capture both continuous and event-driven response patterns in real-time settings, providing complementary evaluation of real-time duplex interaction capabilities. They also place strong demands on omni-modal perception and reasoning, requiring models to effectively integrate visual and auditory signals and perform real-time analysis.

### 3.2 Benchmark Construction

After defining the task taxonomy, we construct the dataset to reflect general real-time duplex interaction scenarios. Videos are collected from diverse online sources and filtered to ensure quality and diversity. We retain videos with clear temporal dynamics and omni-modal signals (e.g., visual and

5


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td colspan="2">Proactive Reminder</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Event Reminder</td><td style='text-align: center; word-wrap: break-word;'>Q: Call me when you hear the sound of something breaking.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Post-Event Reminder</td><td style='text-align: center; word-wrap: break-word;'>A: Okay, I&#x27;ll let you know. Listen, glass is breaking. It&#x27;s so scary...</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Correction</td><td style='text-align: center; word-wrap: break-word;'>Q: That black shirt from earlier was really nice. Let me know if you see it again.</td></tr></table>

<div style="text-align: center;">Figure 3: Example of each task in Proactive Reminder.</div>


<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Category</th><th style='text-align: center;'>Number of videos</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>[15,25)s</td><td style='text-align: center;'>126</td></tr>
    <tr><td style='text-align: center;'>[25,35)s</td><td style='text-align: center;'>294</td></tr>
    <tr><td style='text-align: center;'>[35,45)s</td><td style='text-align: center;'>135</td></tr>
    <tr><td style='text-align: center;'>[45,55)s</td><td style='text-align: center;'>52</td></tr>
    <tr><td style='text-align: center;'>[55,65)s</td><td style='text-align: center;'>53</td></tr>
  </tbody>
</table>

<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Category</th><th style='text-align: center;'>Percentage (%)</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>Entertainment</td><td style='text-align: center;'>23.5</td></tr>
    <tr><td style='text-align: center;'>Lifestyle</td><td style='text-align: center;'>17.3</td></tr>
    <tr><td style='text-align: center;'>Sports & Hobbies</td><td style='text-align: center;'>16.8</td></tr>
    <tr><td style='text-align: center;'>Art</td><td style='text-align: center;'>16.2</td></tr>
    <tr><td style='text-align: center;'>Education</td><td style='text-align: center;'>15.6</td></tr>
    <tr><td style='text-align: center;'>Others</td><td style='text-align: center;'>6.5</td></tr>
    <tr><td style='text-align: center;'>News</td><td style='text-align: center;'>4.1</td></tr>
  </tbody>
</table>

<div style="text-align: center;"><img src="imgs/img_in_image_box_732_638_1005_847.jpg" alt="Image" width="22%" />

hand words

</div>


<div style="text-align: center;">Figure 4: Overview of the dataset characteristics: (a) Distribution of video durations; (b) Distribution of video categories; (c) Linguistic characteristics of text queries.</div>


auditory changes), while removing static or low-information content. This design ensures that the dataset emphasizes time-evolving interactions rather than static scene understanding.

To support reliable evaluation, we carefully design question-answer pairs for each scenario. For Real-Time Description, we identify a subject with continuous temporal variation in each video and construct questions that require describing its evolving state, rather than providing generic summaries. This encourages models to focus on specific entities and track their changes over time, aligning with real-world interaction patterns. Annotators generate responses by continuously observing the video and describing these changes in real time. Each sample is annotated by two independent annotators, with a third annotator resolving disagreements to ensure annotation consistency. For Proactive Reminder, questions are introduced at arbitrary points along the video timeline to simulate real-time user interaction. Each question specifies a clear and unambiguous event, and ground-truth annotations are aligned with the corresponding event timestamps. In the Proactive Reminder scenario, some samples contain multiple occurrences of the target event, requiring models to handle repeated event detection and response.

Finally, all samples undergo strict quality control, including cross-annotation consistency checks and validation of temporal annotations, ensuring the reliability of the dataset.

Omni-DuplexEval consists of 660 videos paired with human-curated question–answer annotations, spanning diverse domains such as education, entertainment, sports, and daily activities (Figure 4(b)). All videos are under one minute in length, with an average duration of 34 seconds; the distribution of video durations is shown in Figure 4(a). All questions are open-ended to better reflect real-world usage. The linguistic characteristics of the queries are illustrated in Figure 4(c).

6

### 3.3 Evaluation Pipeline

Existing evaluations focus mainly on answer correctness, overlooking when a response is produced. In Omni-DuplexEval, we introduce an LLM-as-a-Judge framework that jointly evaluates response timing and content correctness. Since Real-Time Description (RTD) and Proactive Reminder (PR) follow different response patterns, we design separate evaluation strategies for the two scenarios. In the following, we briefly describe the evaluation pipeline for each scenario.

<div style="text-align: center;"><img src="imgs/img_in_image_box_214_319_1007_785.jpg" alt="Image" width="64%" />

Model Response $S=\{s_{1},\ldots,s_{n}\}$, Timespan($s_{i}$) = $[t_{i}^{start},t_{i}^{end}]$

Content Consistency

Temporal Sensitivity

Step 1

Step 2

Step 3

Step 4

Semantic Relevance Filtering

Multi-Window Sampling

Multimodal Context Extraction

Temporal Sensitivity Scoring

Query $q$ Response $S$ Video $V$ Audio $A$

GT Answer

LLM-as-Judge

Score $e_{1}$

Score $e_{2}$

Score $e_{3}$

Score $e_{4}$

Score $e_{5}$

Score $e_{6}$

Score $e_{7}$

Score $e_{8}$

Score $e_{9}$

Score $e_{10}$

Score $e_{11}$

Score $e_{12}$

Score $e_{13}$

Score $e_{14}$

Score $e_{15}$

Score $e_{16}$

Score $e_{17}$

Score $e_{18}$

Score $e_{19}$

Score $e_{20}$

Score $e_{21}$

Score $e_{22}$

Score $e_{23}$

Score $e_{24}$

Score $e_{25}$

Score $e_{26}$

Score $e_{27}$

Score $e_{28}$

Score $e_{29}$

Score $e_{30}$

Score $e_{31}$

Score $e_{32}$

Score $e_{33}$

Score $e_{34}$

Score $e_{35}$

Score $e_{36}$

Score $e_{37}$

Score $e_{38}$

Score $e_{39}$

Score $e_{40}$

Score $e_{41}$

Score $e_{42}$

Score $e_{43}$

Score $e_{44}$

Score $e_{45}$

Score $e_{46}$

Score $e_{47}$

Score $e_{48}$

Score $e_{49}$

Score $e_{50}$

Score $e_{51}$

Score $e_{52}$

Score $e_{53}$

Score $e_{54}$

Score $e_{55}$

Score $e_{56}$

Score $e_{57}$

Score $e_{58}$

Score $e_{59}$

Score $e_{60}$

Score $e_{61}$

Score $e_{62}$

Score $e_{63}$

Score $e_{64}$

Score $e_{65}$

Score $e_{66}$

Score $e_{67}$

Score $e_{68}$

Score $e_{69}$

Score $e_{70}$

Score $e_{71}$

Score $e_{72}$

Score $e_{73}$

Score $e_{74}$

Score $e_{75}$

Score $e_{76}$

Score $e_{77}$

Score $e_{78}$

Score $e_{79}$

Score $e_{80}$

Score $e_{81}$

Score $e_{82}$

Score $e_{83}$

Score $e_{84}$

Score $e_{85}$

Score $e_{86}$

Score $e_{87}$

Score $e_{88}$

Score $e_{89}$

Score $e_{90}$

Score $e_{91}$

Score $e_{92}$

Score $e_{93}$

Score $e_{94}$

Score $e_{95}$

Score $e_{96}$

Score $e_{97}$

Score $e_{98}$

Score $e_{99}$

Score $e_{100}$

Score $e_{101}$

Score $e_{102}$

Score $e_{103}$

Score $e_{104}$

Score $e_{105}$

Score $e_{106}$

Score $e_{107}$

Score $e_{108}$

Score $e_{109}$

Score $e_{110}$

Score $e_{111}$

Score $e_{112}$

Score $e_{113}$

Score $e_{114}$

Score $e_{115}$

Score $e_{116}$

Score $e_{117}$

Score $e_{118}$

Score $e_{119}$

Score $e_{120}$

Score $e_{121}$

Score $e_{122}$

Score $e_{123}$

Score $e_{124}$

Score $e_{125}$

Score $e_{126}$

Score $e_{127}$

Score $e_{128}$

Score $e_{129}$

Score $e_{130}$

Score $e_{131}$

Score $e_{132}$

Score $e_{133}$

Score $e_{134}$

Score $e_{135}$

Score $e_{136}$

Score $e_{137}$

Score $e_{138}$

Score $e_{139}$

Score $e_{140}$

Score $e_{141}$

Score $e_{142}$

Score $e_{143}$

Score $e_{144}$

Score $e_{145}$

Score $e_{146}$

Score $e_{147}$

Score $e_{148}$

Score $e_{149}$

Score $e_{150}$

Score $e_{151}$

Score $e_{152}$

Score $e_{153}$

Score $e_{154}$

Score $e_{155}$

Score $e_{156}$

Score $e_{157}$

Score $e_{158}$

Score $e_{159}$

Score $e_{160}$

Score $e_{161}$

Score $e_{162}$

Score $e_{163}$

Score $e_{164}$

Score $e_{165}$

Score $e_{166}$

Score $e_{167}$

Score $e_{168}$

Score $e_{169}$

Score $e_{170}$

Score $e_{171}$

Score $e_{172}$

Score $e_{173}$

Score $e_{174}$

Score $e_{175}$

Score $e_{176}$

Score $e_{177}$

Score $e_{178}$

Score $e_{179}$

Score $e_{180}$

Score $e_{181}$

Score $e_{182}$

Score $e_{183}$

Score $e_{184}$

Score $e_{185}$

Score $e_{186}$

Score $e_{187}$

Score $e_{188}$

Score $e_{189}$

Score $e_{190}$

Score $e_{191}$

Score $e_{192}$

Score $e_{193}$

Score $e_{194}$

Score $e_{195}$

Score $e_{196}$

Score $e_{197}$

Score $e_{198}$

Score $e_{199}$

Score $e_{200}$

Score $e_{201}$

Score $e_{202}$

Score $e_{203}$

Score $e_{204}$

Score $e_{205}$

Score $e_{206}$

Score $e_{207}$

Score $e_{208}$

Score $e_{209}$

Score $e_{210}$

Score $e_{211}$

Score $e_{212}$

Score $e_{213}$

Score $e_{214}$

Score $e_{215}$

Score $e_{216}$

Score $e_{217}$

Score $e_{218}$

Score $e_{219}$

Score $e_{220}$

Score $e_{221}$

Score $e_{222}$

Score $e_{223}$

Score $e_{224}$

Score $e_{225}$

Score $e_{226}$

Score $e_{227}$

Score $e_{228}$

Score $e_{229}$

Score $e_{230}$

Score $e_{231}$

Score $e_{232}$

Score $e_{233}$

Score $e_{234}$

Score $e_{235}$

Score $e_{236}$

Score $e_{237}$

Score $e_{238}$

Score $e_{239}$

Score $e_{240}$

Score $e_{241}$

Score $e_{242}$

Score $e_{243}$

Score $e_{244}$

Score $e_{245}$

Score $e_{246}$

Score $e_{247}$

Score $e_{248}$

Score $e_{249}$

Score $e_{250}$

Score $e_{251}$

Score $e_{252}$

Score $e_{253}$

Score $e_{254}$

Score $e_{255}$

Score $e_{256}$

Score $e_{257}$

Score $e_{258}$

Score $e_{259}$

Score $e_{260}$

Score $e_{261}$

Score $e_{262}$

Score $e_{263}$

Score $e_{264}$

Score $e_{265}$

Score $e_{266}$

Score $e_{267}$

Score $e_{268}$

Score $e_{269}$

Score $e_{270}$

Score $e_{271}$

Score $e_{272}$

Score $e_{273}$

Score $e_{274}$

Score $e_{275}$

Score $e_{276}$

Score $e_{277}$

Score $e_{278}$

Score $e_{279}$

Score $e_{280}$

Score $e_{281}$

Score $e_{282}$

Score $e_{283}$

Score $e_{284}$

Score $e_{285}$

Score $e_{286}$

Score $e_{287}$

Score $e_{288}$

Score $e_{289}$

Score $e_{290}$

Score $e_{291}$

Score $e_{292}$

Score $e_{293}$

Score $e_{294}$

Score $e_{295}$

Score $e_{296}$

Score $e_{297}$

Score $e_{298}$

Score $e_{299}$

Score $e_{300}$

Score $e_{301}$

Score $e_{302}$

Score $e_{303}$

Score $e_{304}$

Score $e_{305}$

Score $e_{306}$

Score $e_{307}$

Score $e_{308}$

Score $e_{309}$

Score $e_{310}$

Score $e_{311}$

Score $e_{312}$

Score $e_{313}$

Score $e_{314}$

Score $e_{315}$

Score $e_{316}$

Score $e_{317}$

Score $e_{318}$

Score $e_{319}$

Score $e_{320}$

Score $e_{321}$

Score $e_{322}$

Score $e_{323}$

Score $e_{324}$

Score $e_{325}$

Score $e_{326}$

Score $e_{327}$

Score $e_{328}$

Score $e_{329}$

Score $e_{330}$

Score $e_{331}$

Score $e_{332}$

Score $e_{333}$

Score $e_{334}$

Score $e_{335}$

Score $e_{336}$

Score $e_{337}$

Score $e_{338}$

Score $e_{339}$

Score $e_{340}$

Score $e_{341}$

Score $e_{342}$

Score $e_{343}$

Score $e_{344}$

Score $e_{345}$

Score $e_{346}$

Score $e_{347}$

Score $e_{348}$

Score $e_{349}$

Score $e_{350}$

Score $e_{351}$

Score $e_{352}$

Score $e_{353}$

Score $e_{354}$

Score $e_{355}$

Score $e_{356}$

Score $e_{357}$

Score $e_{358}$

Score $e_{359}$

Score $e_{360}$

Score $e_{361}$

Score $e_{362}$

Score $e_{363}$

Score $e_{364}$

Score $e_{365}$

Score $e_{366}$

Score $e_{367}$

Score $e_{368}$

Score $e_{369}$

Score $e_{370}$

Score $e_{371}$

Score $e_{372}$

Score $e_{373}$

Score $e_{374}$

Score $e_{375}$

Score $e_{376}$

Score $e_{377}$

Score $e_{378}$

Score $e_{379}$

Score $e_{380}$

Score $e_{381}$

Score $e_{382}$

Score $e_{383}$

Score $e_{384}$

Score $e_{385}$

Score $e_{386}$

Score $e_{387}$

Score $e_{388}$

Score $e_{389}$

Score $e_{390}$

Score $e_{391}$

Score $e_{392}$

Score $e_{393}$

Score $e_{394}$

Score $e_{395}$

Score $e_{396}$

Score $e_{397}$

Score $e_{398}$

Score $e_{399}$

Score $e_{400}$

Score $e_{401}$

Score $e_{402}$

Score $e_{403}$

Score $e_{404}$

Score $e_{405}$

Score $e_{406}$

Score $e_{407}$

Score $

</div>


<div style="text-align: center;">Figure 5: The automatic evaluation pipeline for Real-Time Description. The framework assesses two dimensions: Content Consistency for global quality, and Temporal Sensitivity for streaming alignment. The final score is computed as a weighted combination of the two.</div>


#### 3.3.1 Real-Time Description

Real-Time Description requires models to generate continuous, streaming descriptions synchronized with evolving video content. This scenario evaluates temporal alignment at sentence-level granularity. To this end, we adopt a two-dimensional evaluation framework consisting of Content Consistency and Temporal Sensitivity. Given a user query q and a model's streaming output  $ S = \{s_1, s_2, \ldots, s_n\} $, each sentence  $ s_i $ is associated with a time interval  $ [t_i^{start}, t_i^{end}] $, enabling fine-grained evaluation along both dimensions. The evaluation pipeline is illustrated in Figure 5.

Content Consistency This metric focuses on global semantic alignment between the model response and the omni-modal input. We extract the full video and corresponding audio, and employ an LLM-as-a-Judge framework to assess whether the response is consistent with the user query and the underlying video–audio content, yielding the content consistency score,  $ Score_{content} $. The evaluation follows a score-deduction scheme, penalizing factual errors, hallucinations, and omissions.

Temporal Sensitivity Temporal Sensitivity measures whether the model captures real-time changes and generates timely, instruction-aligned responses. However, raw streaming outputs contain two sources of noise: (1) irrelevant utterances (e.g., polite phrases) that should not be temporally evaluated, and (2) natural latency variations in model response timing. To address these, we introduce a four-step evaluation pipeline.

Semantic Relevance Filtering: To exclude non-substantive outputs from temporal assessment, each sentence  $ s_i $ is classified as relevant or irrelevant by an LLM-as-a-Judge framework based on user instruction and video–audio context. Let  $ S_{\text{irr}} \subseteq S $ denote irrelevant sentences. These are excluded from evaluation, and their proportion  $ r = |S_{\text{irr}}| / |S| $ attenuates the final score.

7

Multi-Window Sampling: To tolerate natural perception-to-generation latency (empirically ≈ 2 seconds) while penalizing clearly mistimed responses, we construct k = 4 candidate windows around each original timespan  $ [t_i^{\text{start}}, t_i^{\text{end}}] $. They are  $ w_1 : [t_i^{\text{start}} - 1, t_i^{\text{end}} - 1] $,  $ w_2 : [t_i^{\text{start}} - 2, t_i^{\text{end}} - 1] $,  $ w_3 : [t_i^{\text{start}} - 2, t_i^{\text{end}} - 2] $,  $ w_4 : [t_i^{\text{start}} - 1, t_i^{\text{end}}] $.

Multimodal Context Extraction & Scoring: For each candidate window w, we sample video frames at 2 FPS and extract the corresponding audio segment. An LLM judge then evaluates alignment between sentence  $ s_i $ and each window. The sentence score is the maximum alignment score across these windows.

 $$ \mathrm{score}(s_{i})=\max_{k\in\{1,2,3,4\}}\mathrm{LLM}(q,s_{i},video_{w_{k}},audio_{w_{k}}) $$ 

The final Temporal Sensitivity score averages over relevant sentences with an attenuation penalty:

 $$ \mathrm{S c o r e}_{\mathrm{t e m p o r a l}}=\left(\frac{1}{|S_{\mathrm{r e l}}|}\sum_{s_{i}\in S_{\mathrm{r e l}}}\mathrm{s c o r e}(s_{i})\right)\times(1-\lambda\cdot r) $$ 

where  $ S_{\mathrm{rel}} = S \setminus S_{\mathrm{irr}} $.  $ \lambda $ is a hyperparameter controlling the penalty intensity and we set  $ \lambda = 1 $. The overall score combines Content Consistency and Temporal Sensitivity equally:

 $$  Score_{overall}=0.5\cdot Score_{content}+0.5\cdot Score_{temporal} $$ 

Each metric is reported on a 0 – 3 scale, then linearly mapped to 0 – 100.

To improve alignment with human judgments, we experimented with multiple iterative design strategies for our evaluation framework. Overall, our evaluation framework shows strong agreement with human judgments. Detailed ablation and analysis of these iterations, including comparisons with human annotations, are provided in Appendix B.

#### 3.3.2 Proactivate Reminder

Proactive Reminder evaluates the ability to identify relevant events and determine appropriate response timing under streaming video inputs. Omni-DuplexEval provides annotated timestamps for each event. During evaluation, we extract the model's responses within a fixed 10-second window following each event timestamp and assess them using an LLM-as-a-Judge framework. The evaluation focuses on both event identification and the consistency of the response with the user instruction. For Correction tasks, the evaluation measures whether the model accurately revises the user's description based on the video content. For Event Reminder and Post-Event Reminder tasks, it assesses whether the model produces appropriate responses when the event occurs. In addition, for samples where the reminder event occurs multiple times, the model must correctly respond to all occurrences for the sample to be considered successful. In practice, we employ Gemini-3-Flash-thinking as the LLM judge. Implementation details, including the prompts, are provided in Appendix A.

## 4 Experiments

### 4.1 Baselines

We focus on evaluating multimodal models that support duplex inference. Specifically, we include LiveCC (Base/Instruct) [6], MMDuet2 [48], StreamingVLM [28], and MiniCPM-o 4.5 [7]. All experiments are conducted on a single NVIDIA A100 GPU. For each model, we follow its native duplex inference protocol to obtain real-time responses. Outputs are recorded as they are emitted over time, enabling evaluation of response timing and interaction behavior under streaming conditions.

Human Evaluation We conduct two human tests under different protocols. Human-Duplex. We sample 20 instances per scenario, covering all sub-tasks. Four independent annotators not involved in dataset construction, provide real-time spoken responses while watching each video for the first time. Responses are recorded with start times strictly synchronized to video playback, following the same streaming protocol as model inference. This evaluation reflects human performance under real-time constraints. Human-Offline. To assess the upper bound of content understanding without temporal pressure, we conduct an offline human study. Annotators are allowed to preview the entire video and instruction beforehand, and then generate a complete response without real-time streaming constraints—mirroring the inference paradigm of offline MLLMs. This provides a reference for evaluating the content accuracy ceiling when timing is not a factor.

8

<div style="text-align: center;">Table 2: Performance of duplex models on Omni-DuplexEval. We report per-task scores, scenario-level averages, and the overall benchmark score. The best-performing results are shown in bold.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Models</td><td colspan="7">Real-Time Description</td><td colspan="4">Proactive Reminder</td><td rowspan="2">Avg.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>CT</td><td style='text-align: center; word-wrap: break-word;'>IR</td><td style='text-align: center; word-wrap: break-word;'>Omni</td><td style='text-align: center; word-wrap: break-word;'>WK</td><td style='text-align: center; word-wrap: break-word;'>OCR</td><td style='text-align: center; word-wrap: break-word;'>FM</td><td style='text-align: center; word-wrap: break-word;'>Avg.</td><td style='text-align: center; word-wrap: break-word;'>ER</td><td style='text-align: center; word-wrap: break-word;'>PER</td><td style='text-align: center; word-wrap: break-word;'>CR</td><td style='text-align: center; word-wrap: break-word;'>Avg.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Human-Offline</td><td style='text-align: center; word-wrap: break-word;'>82.6</td><td style='text-align: center; word-wrap: break-word;'>74.6</td><td style='text-align: center; word-wrap: break-word;'>88.9</td><td style='text-align: center; word-wrap: break-word;'>83.8</td><td style='text-align: center; word-wrap: break-word;'>88.8</td><td style='text-align: center; word-wrap: break-word;'>79.5</td><td style='text-align: center; word-wrap: break-word;'>83.0</td><td style='text-align: center; word-wrap: break-word;'>100.0</td><td style='text-align: center; word-wrap: break-word;'>100.0</td><td style='text-align: center; word-wrap: break-word;'>100.0</td><td style='text-align: center; word-wrap: break-word;'>100.0</td><td style='text-align: center; word-wrap: break-word;'>91.5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Human-Duplex</td><td style='text-align: center; word-wrap: break-word;'>68.8</td><td style='text-align: center; word-wrap: break-word;'>81.1</td><td style='text-align: center; word-wrap: break-word;'>64.1</td><td style='text-align: center; word-wrap: break-word;'>73.2</td><td style='text-align: center; word-wrap: break-word;'>65.1</td><td style='text-align: center; word-wrap: break-word;'>72.2</td><td style='text-align: center; word-wrap: break-word;'>70.8</td><td style='text-align: center; word-wrap: break-word;'>89.3</td><td style='text-align: center; word-wrap: break-word;'>97.9</td><td style='text-align: center; word-wrap: break-word;'>91.1</td><td style='text-align: center; word-wrap: break-word;'>92.8</td><td style='text-align: center; word-wrap: break-word;'>81.8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LiveCC-Base [6]</td><td style='text-align: center; word-wrap: break-word;'>17.6</td><td style='text-align: center; word-wrap: break-word;'>36.7</td><td style='text-align: center; word-wrap: break-word;'>32.2</td><td style='text-align: center; word-wrap: break-word;'>39.3</td><td style='text-align: center; word-wrap: break-word;'>49.5</td><td style='text-align: center; word-wrap: break-word;'>33.4</td><td style='text-align: center; word-wrap: break-word;'>34.8</td><td style='text-align: center; word-wrap: break-word;'>3.1</td><td style='text-align: center; word-wrap: break-word;'>1.0</td><td style='text-align: center; word-wrap: break-word;'>1.5</td><td style='text-align: center; word-wrap: break-word;'>1.9</td><td style='text-align: center; word-wrap: break-word;'>18.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>StreamingVLM [28]</td><td style='text-align: center; word-wrap: break-word;'>29.2</td><td style='text-align: center; word-wrap: break-word;'>34.0</td><td style='text-align: center; word-wrap: break-word;'>36.7</td><td style='text-align: center; word-wrap: break-word;'>39.4</td><td style='text-align: center; word-wrap: break-word;'>42.9</td><td style='text-align: center; word-wrap: break-word;'>35.1</td><td style='text-align: center; word-wrap: break-word;'>36.2</td><td style='text-align: center; word-wrap: break-word;'>1.6</td><td style='text-align: center; word-wrap: break-word;'>0.0</td><td style='text-align: center; word-wrap: break-word;'>3.0</td><td style='text-align: center; word-wrap: break-word;'>1.7</td><td style='text-align: center; word-wrap: break-word;'>19.0</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LiveCC-Inst [6]</td><td style='text-align: center; word-wrap: break-word;'>30.9</td><td style='text-align: center; word-wrap: break-word;'>35.3</td><td style='text-align: center; word-wrap: break-word;'>48.6</td><td style='text-align: center; word-wrap: break-word;'>47.7</td><td style='text-align: center; word-wrap: break-word;'>52.7</td><td style='text-align: center; word-wrap: break-word;'>41.9</td><td style='text-align: center; word-wrap: break-word;'>42.9</td><td style='text-align: center; word-wrap: break-word;'>7.8</td><td style='text-align: center; word-wrap: break-word;'>2.0</td><td style='text-align: center; word-wrap: break-word;'>3.8</td><td style='text-align: center; word-wrap: break-word;'>4.7</td><td style='text-align: center; word-wrap: break-word;'>23.8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MMDuet2 [48]</td><td style='text-align: center; word-wrap: break-word;'>53.3</td><td style='text-align: center; word-wrap: break-word;'>54.4</td><td style='text-align: center; word-wrap: break-word;'>57.6</td><td style='text-align: center; word-wrap: break-word;'>59.6</td><td style='text-align: center; word-wrap: break-word;'>64.9</td><td style='text-align: center; word-wrap: break-word;'>60.8</td><td style='text-align: center; word-wrap: break-word;'>58.4</td><td style='text-align: center; word-wrap: break-word;'>24.2</td><td style='text-align: center; word-wrap: break-word;'>9.1</td><td style='text-align: center; word-wrap: break-word;'>2.3</td><td style='text-align: center; word-wrap: break-word;'>11.9</td><td style='text-align: center; word-wrap: break-word;'>35.2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MiniCPM-o 4.5 [7]</td><td style='text-align: center; word-wrap: break-word;'>51.4</td><td style='text-align: center; word-wrap: break-word;'>58.2</td><td style='text-align: center; word-wrap: break-word;'>58.4</td><td style='text-align: center; word-wrap: break-word;'>63.7</td><td style='text-align: center; word-wrap: break-word;'>68.6</td><td style='text-align: center; word-wrap: break-word;'>54.3</td><td style='text-align: center; word-wrap: break-word;'>59.1</td><td style='text-align: center; word-wrap: break-word;'>18.8</td><td style='text-align: center; word-wrap: break-word;'>11.1</td><td style='text-align: center; word-wrap: break-word;'>27.8</td><td style='text-align: center; word-wrap: break-word;'>20.0</td><td style='text-align: center; word-wrap: break-word;'>39.6</td></tr></table>

### 4.2 Main results

Table 2 summarizes the performance of duplex models on the Real-Time Description and Proactive Reminder scenarios. Our primary findings are as follows:

Significant Gap Between Models and Human Performance. Overall, current duplex models fall substantially short of human performance on Omni-DuplexEval, with the best model achieving 39.6 compared to 81.8 for Human-Duplex. While MiniCPM-o 4.5 consistently outperforms other models, all systems remain far from human-level real-time interaction. Across models, performance is noticeably higher on Real-Time Description than on Proactive Reminder, indicating a shared difficulty in handling event-driven interaction. This suggests that, although models can partially track evolving content, they struggle more fundamentally with deciding when to respond.

<div style="text-align: center;">Table 3: Performance of duplex models on the six sub-tasks of Real-Time Description, including scores for two evaluation dimensions and an overall aggregated score.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Models</td><td rowspan="2">Metric</td><td colspan="7">Task</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>CT</td><td style='text-align: center; word-wrap: break-word;'>IR</td><td style='text-align: center; word-wrap: break-word;'>Omni</td><td style='text-align: center; word-wrap: break-word;'>WK</td><td style='text-align: center; word-wrap: break-word;'>OCR</td><td style='text-align: center; word-wrap: break-word;'>FM</td><td style='text-align: center; word-wrap: break-word;'>Avg.</td></tr><tr><td rowspan="3">Human-Offline</td><td style='text-align: center; word-wrap: break-word;'>Temporal Sensitivity</td><td style='text-align: center; word-wrap: break-word;'>73.5</td><td style='text-align: center; word-wrap: break-word;'>87.4</td><td style='text-align: center; word-wrap: break-word;'>83.3</td><td style='text-align: center; word-wrap: break-word;'>82.2</td><td style='text-align: center; word-wrap: break-word;'>91.5</td><td style='text-align: center; word-wrap: break-word;'>87.8</td><td style='text-align: center; word-wrap: break-word;'>84.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Content Consistency</td><td style='text-align: center; word-wrap: break-word;'>91.7</td><td style='text-align: center; word-wrap: break-word;'>61.7</td><td style='text-align: center; word-wrap: break-word;'>94.4</td><td style='text-align: center; word-wrap: break-word;'>85.4</td><td style='text-align: center; word-wrap: break-word;'>86.1</td><td style='text-align: center; word-wrap: break-word;'>71.1</td><td style='text-align: center; word-wrap: break-word;'>81.7</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Average</td><td style='text-align: center; word-wrap: break-word;'>82.6</td><td style='text-align: center; word-wrap: break-word;'>74.6</td><td style='text-align: center; word-wrap: break-word;'>88.9</td><td style='text-align: center; word-wrap: break-word;'>83.8</td><td style='text-align: center; word-wrap: break-word;'>88.8</td><td style='text-align: center; word-wrap: break-word;'>79.5</td><td style='text-align: center; word-wrap: break-word;'>83.0</td></tr><tr><td rowspan="3">Human-Duplex</td><td style='text-align: center; word-wrap: break-word;'>Temporal Sensitivity</td><td style='text-align: center; word-wrap: break-word;'>77.9</td><td style='text-align: center; word-wrap: break-word;'>91.7</td><td style='text-align: center; word-wrap: break-word;'>72.5</td><td style='text-align: center; word-wrap: break-word;'>83.5</td><td style='text-align: center; word-wrap: break-word;'>68.8</td><td style='text-align: center; word-wrap: break-word;'>85.7</td><td style='text-align: center; word-wrap: break-word;'>80.0</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Content Consistency</td><td style='text-align: center; word-wrap: break-word;'>59.7</td><td style='text-align: center; word-wrap: break-word;'>70.5</td><td style='text-align: center; word-wrap: break-word;'>55.7</td><td style='text-align: center; word-wrap: break-word;'>62.9</td><td style='text-align: center; word-wrap: break-word;'>61.4</td><td style='text-align: center; word-wrap: break-word;'>58.7</td><td style='text-align: center; word-wrap: break-word;'>61.5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Average</td><td style='text-align: center; word-wrap: break-word;'>68.8</td><td style='text-align: center; word-wrap: break-word;'>81.1</td><td style='text-align: center; word-wrap: break-word;'>64.1</td><td style='text-align: center; word-wrap: break-word;'>73.2</td><td style='text-align: center; word-wrap: break-word;'>65.1</td><td style='text-align: center; word-wrap: break-word;'>72.2</td><td style='text-align: center; word-wrap: break-word;'>70.8</td></tr><tr><td rowspan="3">LiveCC-Base [6]</td><td style='text-align: center; word-wrap: break-word;'>Temporal Sensitivity</td><td style='text-align: center; word-wrap: break-word;'>25.8</td><td style='text-align: center; word-wrap: break-word;'>56.9</td><td style='text-align: center; word-wrap: break-word;'>45.9</td><td style='text-align: center; word-wrap: break-word;'>56.6</td><td style='text-align: center; word-wrap: break-word;'>63.1</td><td style='text-align: center; word-wrap: break-word;'>47.5</td><td style='text-align: center; word-wrap: break-word;'>49.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Content Consistency</td><td style='text-align: center; word-wrap: break-word;'>9.4</td><td style='text-align: center; word-wrap: break-word;'>16.5</td><td style='text-align: center; word-wrap: break-word;'>18.5</td><td style='text-align: center; word-wrap: break-word;'>21.9</td><td style='text-align: center; word-wrap: break-word;'>35.8</td><td style='text-align: center; word-wrap: break-word;'>19.3</td><td style='text-align: center; word-wrap: break-word;'>20.2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Average</td><td style='text-align: center; word-wrap: break-word;'>17.6</td><td style='text-align: center; word-wrap: break-word;'>36.7</td><td style='text-align: center; word-wrap: break-word;'>32.2</td><td style='text-align: center; word-wrap: break-word;'>39.3</td><td style='text-align: center; word-wrap: break-word;'>49.5</td><td style='text-align: center; word-wrap: break-word;'>33.4</td><td style='text-align: center; word-wrap: break-word;'>34.8</td></tr><tr><td rowspan="3">StreamingVLM [28]</td><td style='text-align: center; word-wrap: break-word;'>Temporal Sensitivity</td><td style='text-align: center; word-wrap: break-word;'>47.0</td><td style='text-align: center; word-wrap: break-word;'>57.9</td><td style='text-align: center; word-wrap: break-word;'>58.8</td><td style='text-align: center; word-wrap: break-word;'>55.6</td><td style='text-align: center; word-wrap: break-word;'>55.9</td><td style='text-align: center; word-wrap: break-word;'>54.8</td><td style='text-align: center; word-wrap: break-word;'>55.0</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Content Consistency</td><td style='text-align: center; word-wrap: break-word;'>11.3</td><td style='text-align: center; word-wrap: break-word;'>10.1</td><td style='text-align: center; word-wrap: break-word;'>14.5</td><td style='text-align: center; word-wrap: break-word;'>23.2</td><td style='text-align: center; word-wrap: break-word;'>29.8</td><td style='text-align: center; word-wrap: break-word;'>15.4</td><td style='text-align: center; word-wrap: break-word;'>17.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Average</td><td style='text-align: center; word-wrap: break-word;'>29.2</td><td style='text-align: center; word-wrap: break-word;'>34.0</td><td style='text-align: center; word-wrap: break-word;'>36.7</td><td style='text-align: center; word-wrap: break-word;'>39.4</td><td style='text-align: center; word-wrap: break-word;'>42.9</td><td style='text-align: center; word-wrap: break-word;'>35.1</td><td style='text-align: center; word-wrap: break-word;'>36.2</td></tr><tr><td rowspan="3">LiveCC-Inst [6]</td><td style='text-align: center; word-wrap: break-word;'>Temporal Sensitivity</td><td style='text-align: center; word-wrap: break-word;'>49.9</td><td style='text-align: center; word-wrap: break-word;'>57.8</td><td style='text-align: center; word-wrap: break-word;'>75.5</td><td style='text-align: center; word-wrap: break-word;'>63.5</td><td style='text-align: center; word-wrap: break-word;'>64.8</td><td style='text-align: center; word-wrap: break-word;'>63.2</td><td style='text-align: center; word-wrap: break-word;'>62.5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Content Consistency</td><td style='text-align: center; word-wrap: break-word;'>11.9</td><td style='text-align: center; word-wrap: break-word;'>12.8</td><td style='text-align: center; word-wrap: break-word;'>21.7</td><td style='text-align: center; word-wrap: break-word;'>31.8</td><td style='text-align: center; word-wrap: break-word;'>40.5</td><td style='text-align: center; word-wrap: break-word;'>20.5</td><td style='text-align: center; word-wrap: break-word;'>23.2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Average</td><td style='text-align: center; word-wrap: break-word;'>30.9</td><td style='text-align: center; word-wrap: break-word;'>35.3</td><td style='text-align: center; word-wrap: break-word;'>48.6</td><td style='text-align: center; word-wrap: break-word;'>47.7</td><td style='text-align: center; word-wrap: break-word;'>52.7</td><td style='text-align: center; word-wrap: break-word;'>41.9</td><td style='text-align: center; word-wrap: break-word;'>42.9</td></tr><tr><td rowspan="3">MMDuet2 [48]</td><td style='text-align: center; word-wrap: break-word;'>Temporal Sensitivity</td><td style='text-align: center; word-wrap: break-word;'>77.8</td><td style='text-align: center; word-wrap: break-word;'>82.7</td><td style='text-align: center; word-wrap: break-word;'>82.7</td><td style='text-align: center; word-wrap: break-word;'>73.6</td><td style='text-align: center; word-wrap: break-word;'>78.4</td><td style='text-align: center; word-wrap: break-word;'>80.2</td><td style='text-align: center; word-wrap: break-word;'>79.2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Content Consistency</td><td style='text-align: center; word-wrap: break-word;'>28.8</td><td style='text-align: center; word-wrap: break-word;'>26.0</td><td style='text-align: center; word-wrap: break-word;'>32.4</td><td style='text-align: center; word-wrap: break-word;'>45.6</td><td style='text-align: center; word-wrap: break-word;'>51.4</td><td style='text-align: center; word-wrap: break-word;'>41.4</td><td style='text-align: center; word-wrap: break-word;'>37.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Average</td><td style='text-align: center; word-wrap: break-word;'>53.3</td><td style='text-align: center; word-wrap: break-word;'>54.4</td><td style='text-align: center; word-wrap: break-word;'>57.6</td><td style='text-align: center; word-wrap: break-word;'>59.6</td><td style='text-align: center; word-wrap: break-word;'>64.9</td><td style='text-align: center; word-wrap: break-word;'>60.8</td><td style='text-align: center; word-wrap: break-word;'>58.4</td></tr><tr><td rowspan="3">MiniCPM-o 4.5 [7]</td><td style='text-align: center; word-wrap: break-word;'>Temporal Sensitivity</td><td style='text-align: center; word-wrap: break-word;'>70.1</td><td style='text-align: center; word-wrap: break-word;'>84.3</td><td style='text-align: center; word-wrap: break-word;'>81.3</td><td style='text-align: center; word-wrap: break-word;'>82.5</td><td style='text-align: center; word-wrap: break-word;'>84.6</td><td style='text-align: center; word-wrap: break-word;'>76.3</td><td style='text-align: center; word-wrap: break-word;'>79.9</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Content Consistency</td><td style='text-align: center; word-wrap: break-word;'>32.7</td><td style='text-align: center; word-wrap: break-word;'>32.0</td><td style='text-align: center; word-wrap: break-word;'>35.5</td><td style='text-align: center; word-wrap: break-word;'>44.9</td><td style='text-align: center; word-wrap: break-word;'>52.6</td><td style='text-align: center; word-wrap: break-word;'>32.3</td><td style='text-align: center; word-wrap: break-word;'>38.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Average</td><td style='text-align: center; word-wrap: break-word;'>51.4</td><td style='text-align: center; word-wrap: break-word;'>58.2</td><td style='text-align: center; word-wrap: break-word;'>58.4</td><td style='text-align: center; word-wrap: break-word;'>63.7</td><td style='text-align: center; word-wrap: break-word;'>68.6</td><td style='text-align: center; word-wrap: break-word;'>54.3</td><td style='text-align: center; word-wrap: break-word;'>59.1</td></tr></table>

9

Models Excel at Perception but Struggle with Structured Reasoning. Fine-grained analysis reveals a clear gap between perception and reasoning abilities. While models perform relatively well on low-level tasks such as OCR and fine-grained motion (e.g., MiniCPM-o 4.5 achieves 68.6 on OCR), performance drops on tasks requiring structured reasoning. In particular, Counting is consistently the most challenging task across models (e.g., 51.4 for MiniCPM-o 4.5), with lower scores also observed on Interaction Relationships and World Knowledge. These results suggest that current duplex models remain limited in integrating dynamic context into coherent reasoning.

Models Produce Sparse Responses, Limiting Holistic Understanding. Our analysis reveals a clear discrepancy between local and global evaluation dimensions. As shown in Table 3, models achieve relatively strong performance in Temporal Sensitivity but consistently underperform in

<div style="text-align: center;"><img src="imgs/img_in_image_box_695_155_1003_425.jpg" alt="Image" width="25%" />

Input:
Describe the animals' movements and sounds in real time.
Model response:
4s-8s: A little spider is moving around, and a fly just landed on the table.
8s-11s: The fly seems to be looking at something.
16s-19s: Look, the spider is sneezing now.
24s-26s: Now it's the fly's turn to sneeze.
Video timeline:
Score: 2.50 CA 0.25

</div>


<div style="text-align: center;">Figure 6: Example of model predictions in Real-Time Description.</div>


Content Consistency. This gap mainly stems from the output behavior of current models: they tend to generate sparse and intermittent responses, remaining silent for a large portion of the video and producing outputs only occasionally. While such behavior may help maintain local temporal alignment, it often fails to capture the continuous context of the video, leading to poor global consistency. Figure 6 further illustrates this pattern, where outputs are temporally sparse and fragmented. These results suggest that current models struggle to reconcile timely response generation with holistic content understanding, highlighting a fundamental limitation in real-time duplex interaction.

Models Fail to Determine When

to Respond in Proactive Reminder.

From the results in Table 2, we observe that the best-performing model achieves only 20.0, indicating that the overall performance remains very limited. We further analyze the error distribution, as shown in Table 4. MiniCPM-o 4.5 and MMDuet2 are dominated by No Answer cases. In



<div style="text-align: center;">Table 4: Distribution of error types for model responses under the Proactive Reminder setting (in percentage, %).</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Models</td><td style='text-align: center; word-wrap: break-word;'>No Answer</td><td style='text-align: center; word-wrap: break-word;'>Partially Correct</td><td style='text-align: center; word-wrap: break-word;'>Wrong</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LiveCC-Base [6]</td><td style='text-align: center; word-wrap: break-word;'>5.8</td><td style='text-align: center; word-wrap: break-word;'>1.2</td><td style='text-align: center; word-wrap: break-word;'>91.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>StreamingVLM [28]</td><td style='text-align: center; word-wrap: break-word;'>0.8</td><td style='text-align: center; word-wrap: break-word;'>0.8</td><td style='text-align: center; word-wrap: break-word;'>96.7</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LiveCC-Inst [6]</td><td style='text-align: center; word-wrap: break-word;'>0.8</td><td style='text-align: center; word-wrap: break-word;'>1.4</td><td style='text-align: center; word-wrap: break-word;'>93.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MMDuet2 [48]</td><td style='text-align: center; word-wrap: break-word;'>75.8</td><td style='text-align: center; word-wrap: break-word;'>5.1</td><td style='text-align: center; word-wrap: break-word;'>7.2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MiniCPM-o 4.5 [7]</td><td style='text-align: center; word-wrap: break-word;'>49.2</td><td style='text-align: center; word-wrap: break-word;'>3.6</td><td style='text-align: center; word-wrap: break-word;'>27.2</td></tr></table>

contrast, LiveCC and StreamingVLM mainly produce Wrong outputs. We further analyze the underlying causes and find that these models often generate continuous caption-like descriptions without following the instruction or identifying relevant events. This suggests that they fail to determine when a response should be triggered. Moreover, even when models correctly detect events, maintaining content consistency remains challenging. Overall, these results point to a fundamental limitation of current duplex MLLMs: the inability to decide when to respond.

## 5 Conclusion and Future Work

We introduce Omni-DuplexEval, the first benchmark for evaluating real-time full-duplex capabilities of omni-modal models. The benchmark comprises two scenarios: Real-Time Description (six tasks) and Proactive Reminder (three tasks), with 660 videos and human-curated timestamp-level annotations. Our experiments reveal two key findings. For Real-Time Description, models fail to balance global content consistency with local temporal sensitivity. For Proactive Reminder, models struggle to determine when to respond. These results further highlight the importance of real-time duplex interaction capabilities. We hope this work will facilitate future research toward more capable real-time duplex multimodal systems.

Future work may extend Omni-DuplexEval toward longer and more complex interaction settings. As duplex multimodal systems continue to evolve, we also expect future benchmarks to cover richer modalities and broader forms of real-time interaction.

10

## References

[1] Aaron Hurst, Adam Lerer, Adam P Goucher, Adam Perelman, Aditya Ramesh, Aidan Clark, AJ Ostrow, Akila Welihinda, Alan Hayes, Alec Radford, et al. Gpt-4o system card. arXiv preprint arXiv:2410.21276, 2024.

[2] Google DeepMind. Gemini 3.1 pro model card. https://deepmind.google/models/model-cards/gemini-3-1-pro/, 2026.

[3] Chaoyou Fu, Yuhan Dai, Yongdong Luo, Lei Li, Shuhuai Ren, Renrui Zhang, Zihan Wang, Chenyu Zhou, Yunhang Shen, Mengdan Zhang, et al. Video-mme: The first-ever comprehensive evaluation benchmark of multi-modal llms in video analysis. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition, pages 24108–24118, 2025.

[4] Weihan Wang, Zehai He, Wenyi Hong, Yean Cheng, Xiaohan Zhang, Ji Qi, Ming Ding, Xiaotao Gu, Shiyu Huang, Bin Xu, et al. Lvbench: An extreme long video understanding benchmark. In Proceedings of the IEEE/CVF International Conference on Computer Vision, pages 22958–22967, 2025.

[5] Guan-Ting Lin, Jiachen Lian, Tingle Li, Qirui Wang, Gopala Anumanchipalli, Alexander H. Liu, and Hung yi Lee. Full-duplex-bench: A benchmark to evaluate full-duplex spoken dialogue models on turn-taking capabilities, 2025.

[6] Joya Chen, Ziyun Zeng, Yiqi Lin, Wei Li, Zejun Ma, and Mike Zheng Shou. Livecc: Learning video llm with streaming speech transcription at scale. In Proceedings of the Computer Vision and Pattern Recognition Conference, pages 29083–29095, 2025.

[7] Yuan Yao, Tianyu Yu, Ao Zhang, Chongyi Wang, Junbo Cui, Hongji Zhu, Tianchi Cai, Haoyu Li, Weilin Zhao, Zhihui He, et al. Minicpm-v: A gpt-4v level mlm on your phone. arXiv preprint arXiv:2408.01800, 2024.

[8] Junming Lin, Zheng Fang, Chi Chen, Zihao Wan, Fuwen Luo, Peng Li, Yang Liu, and Maosong Sun. Streamingbench: Assessing the gap for mlms to achieve streaming video understanding. arXiv preprint arXiv:2411.03628, 2024.

[9] Yifei Li, Junbo Niu, Ziyang Miao, Chunjiang Ge, Yuanhang Zhou, Qihao He, Xiaoyi Dong, Haodong Duan, Shuangrui Ding, Rui Qian, et al. Ovo-bench: How far is your video-llms from real-world online video understanding? arXiv preprint arXiv:2501.05510, 2025.

[10] Yuxuan Wang, Yueqian Wang, Bo Chen, Tong Wu, Dongyan Zhao, and Zilong Zheng. Omniimmi: A comprehensive multi-modal interaction benchmark in streaming video contexts. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 18925–18935, 2025.

[11] Yueqian Wang, Xiaojun Meng, Yifan Wang, Huishuai Zhang, and Dongyan Zhao. Proactive-idea: A comprehensive benchmark evaluating proactive interactions in video large language models. arXiv preprint arXiv:2507.09313, 2025.

[12] Xudong Lu, Huankan Guan, Yang Bo, Jinpeng Chen, Xintong Guo, Shuhan Li, Fang Liu, Peiwen Sun, Xueying Li, Wei Zhang, et al. Phostream: Benchmarking real-world streaming for omnimodal assistants in mobile scenarios. arXiv preprint arXiv:2601.22575, 2026.

[13] Kunchang Li, Yali Wang, Yinan He, Yizhuo Li, Yi Wang, Yi Liu, Zun Wang, Jilan Xu, Guo Chen, Ping Luo, et al. Mvbench: A comprehensive multi-modal video understanding benchmark. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 22195–22206, 2024.

[14] Junjie Zhou, Yan Shu, Bo Zhao, Boya Wu, Shitao Xiao, Xi Yang, Yongping Xiong, Bo Zhang, Tiejun Huang, and Zheng Liu. Mlvu: A comprehensive benchmark for multi-task long video understanding. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, 2025.

11

[15] Haoning Wu, Dongxu Li, Bei Chen, and Junnan Li. Longvideobench: A benchmark for long-context interleaved video-language understanding. Advances in Neural Information Processing Systems, 37:28828–28857, 2024.

[16] Yizhi Li, Ge Zhang, Yinghao Ma, Ruibin Yuan, Kang Zhu, Hangyu Guo, Yiming Liang, Jiaheng Liu, Zekun Wang, Jian Yang, et al. Omnibench: Towards the future of universal omni-language models. arXiv preprint arXiv:2409.15272, 2024.

[17] Jack Hong, Shilin Yan, Jiayin Cai, Xiaolong Jiang, Yao Hu, and Weidi Xie. Worldsense: Evaluating real-world omnimodal understanding for multimodal llms. arXiv preprint arXiv:2502.04326, 2025.

[18] Yansong Shi, Qingsong Zhao, Tianxiang Jiang, Xiangyu Zeng, Yi Wang, and Limin Wang. River: A real-time interaction benchmark for video llms. In International Conference on Learning Representations (ICLR), 2026.

[19] KunChang Li, Yinan He, Yi Wang, Yizhuo Li, Wenhai Wang, Ping Luo, Yali Wang, Limin Wang, and Yu Qiao. Videochat: Chat-centric video understanding. arXiv preprint arXiv:2305.06355, 2023.

[20] Yixuan Su, Tian Lan, Huayang Li, Jialu Xu, Yan Wang, and Deng Cai. Pandagpt: One model to instruction-follow them all. arXiv preprint arXiv:2305.16355, 2023.

[21] Sihan Chen, Xingjian He, Longteng Guo, Xinxin Zhu, Weining Wang, Jinhui Tang, and Jing Liu. Vast: A vision-audio-subtitle-text omni-modality foundation model. arXiv preprint arXiv:2305.18500, 2023.

[22] Shengqiong Wu, Hao Fei, Leigang Qu, Wei Ji, and Tat-Seng Chua. Next-gpt: Any-to-any multimodal llm. arXiv preprint arXiv:2309.05519, 2024.

[23] Jiaming Han, Kaixiong Gong, Yiyuan Zhang, Jiaqi Wang, Kaipeng Zhang, Dahua Lin, Yu Qiao, Peng Gao, and Xiangyu Yue. Onellm: One framework to align all modalities with language. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 26584–26595, 2024.

[24] Chaoyou Fu, Haojia Lin, Zuwei Long, Yunhang Shen, Meng Zhao, Yifan Zhang, Shaoqi Dong, Xiong Wang, Di Yin, Long Ma, et al. Vita: Towards open-source interactive omni multimodal llm. arXiv preprint arXiv:2408.05211, 2024.

[25] Wuyang Chen, Zhaohui Wang, Yizhou Jiang, Xiaolin Zhang, Jiayu Wang, Junyan He, Li Yuan, Yong Zhang, Tong Zhang, and Dahua Lin. Cogvlm2: Visual language models for image and video understanding. arXiv preprint arXiv:2408.16500, 2024.

[26] Joya Chen, Zhaoyang Lv, Shiwei Wu, Kevin Qinghong Lin, Chenan Song, Difei Gao, Jia-Wei Liu, Ziteng Gao, Dongxing Mao, and Mike Zheng Shou. Videollm-online: Online video large language model for streaming video. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 18407–18418, 2024.

[27] Haoji Zhang, Yiqin Wang, Yansong Tang, Yong Liu, Jiashi Feng, Jifeng Dai, and Xiaojie Jin. Flash-vstream: Memory-based real-time understanding for long video streams. arXiv preprint arXiv:2406.08085, 2024.

[28] Ruyi Xu, Guangxuan Xiao, Yukang Chen, Liuning He, Kelly Peng, Yao Lu, and Song Han. Streamingvlm: Real-time understanding for infinite video streams. arXiv preprint arXiv:2510.02295, 2025.

[29] Yuxuan Wang, Xiaojun Meng, Yueqian Wang, Jianxin Liang, Jiansheng Wei, Huishuai Zhang, and Dongyan Zhao. Streambridge: Transforming offline video-llms into streaming models. 2025. Apple Research, September 2025.

[30] Guangzhi Sun, Wenyi Yu, Changli Tang, Xianzhao Chen, Tian Tan, Wei Li, Lu Lu, Zejun Ma, Yuxuan Wang, and Chao Zhang. Video-salmonn s: Test-time training memory for streaming video understanding. arXiv preprint arXiv:2510.11129, 2025.

12

[31] Haocheng Lu, Nan Zhang, Wei Tao, Xiaoyang Qu, Guokuan Li, Jiguang Wan, and Jianzong Wang. Vista: Scene-aware optimization for streaming video question answering under post-hoc queries. In Proceedings of the AAAI Conference on Artificial Intelligence, volume 40, pages 7539–7547, 2026.

[32] Guowei Tang, Yifei Wang, Jiacheng Li, Yue Zhang, and Yuxuan Chen. Streamingval: A unified evaluation protocol towards realistic streaming video understanding. arXiv preprint arXiv:2603.21493, 2026.

[33] Karttikeya Mangalam, Linxi Fan, Yuxuan Li, Yuxuan Wang, Jiahao Li, Xinlei Chen, Haoqi Fan, Yu Xiang, Zhou Lou, Yuhan Shi, et al. Egoschema: A diagnostic benchmark for video understanding. arXiv preprint arXiv:2403.12155, 2024.

[34] Viorica Patraucean, Lucas Smaira, Ankush Gupta, Adria Recasens, Larisa Markeeva, Dylan Banarse, Nando Risi, Abhishek Goyal, Kaiming He, Skanda Koppula, et al. Perception test: A diagnostic benchmark for multimodal models. arXiv preprint arXiv:2405.17348, 2024.

[35] Zhou Yu, Dejing Xu, Jun Yu, Zhipeng Cai, and Dacheng Tao. Activitynet-qa: A dataset for video question answering. IEEE Transactions on Pattern Analysis and Machine Intelligence, 2019.

[36] Haiyang Kong, Jiale Wu, Xiaohui Li, Jinlong Wang, Yong Wu, Longtao Li, and Ming Sun. A survey on video large language models: Benchmarks and evaluation methodologies. arXiv preprint arXiv:2501.02688, 2025.

[37] Shuhang Xun, Sicheng Tao, Jungang Li, Yibo Shi, Zhixin Lin, Zhanhui Zhu, Yibo Yan, Hanqian Li, Linghao Zhang, Shikang Wang, Yixin Liu, Hanbo Zhang, Ying Ma, and Xuming Hu. Rtv-bench: Benchmarking mlIm continuous perception, understanding and reasoning through real-time video. In Advances in Neural Information Processing Systems, volume 38, 2025.

[38] Joya Chen, Ziyun Zeng, Yiqi Lin, Wei Li, Zejun Ma, and Mike Zheng Shou. Livecc: Learning video llm with streaming speech transcription at scale. arXiv preprint arXiv:2504.16030, 2025.

[39] Hao Zhang, Yuxuan Li, Ziqian Wang, and Sijia Chen. Spot-bench: Benchmarking real-time spoken proactive video understanding. arXiv preprint arXiv:2505.08765, 2025.

[40] Jiacheng Li, Yue Zhang, Xinyu Wang, and Yuxuan Chen. Vsas-bench: A synchronous-asynchronous streaming benchmark for multimodal llms. arXiv preprint arXiv:2505.14532, 2025.

[41] Xinyu Wang, Jiacheng Li, Yue Zhang, and Yuxuan Chen. Streamingeval: A unified framework for evaluating streaming multimodal systems. arXiv preprint arXiv:2506.02148, 2025.

[42] Jun Xiao, Ziqian Wang, Yifan Liu, and Sijia Chen. Lvomnibench: Long audio-video understanding for omni-modal llms. arXiv preprint arXiv:2506.08764, 2025.

[43] Arushi Goel et al. Mμου: A massive multi-task omni understanding and reasoning benchmark for long and complex real-world videos. arXiv preprint arXiv:2603.14145, 2026.

[44] Liuyue Xie, Avik Kuthiala, George Z Wei, Ce Zheng, Ananya Bal, Mosam Dabhi, Liting Wen, Taru Rustagi, Ethan Lai, Sushil Khyalia, Rohan Choudhury, Morteza Ziyadi, Xu Zhang, Hao Yang, and Laszlo A Jeni. Maverix: Multimodal audio-visual evaluation and recognition index. In Proceedings of the AAAI Conference on Artificial Intelligence, volume 40, pages 27090–27098, 2026.

[45] WildVideo Team. Wildvideo: A systematic multi-round open-ended qa benchmark for real-world video-language interaction. IEEE Transactions on Pattern Analysis and Machine Intelligence (TPAMI), 2025. Accepted.

[46] Guan-Ting Lin, Jiachen Lian, Tingle Li, Qirui Wang, Gopala Anumanchipalli, Alexander H. Liu, and Hung-yi Lee. Full-duplex-bench: A benchmark to evaluate full-duplex spoken dialogue models on turn-taking capabilities. arXiv preprint arXiv:2503.04721, 2025.

13

[47] HumDial Challenge Team. Full-duplex interaction in spoken dialogue systems: A comprehensive study from the icassp 2026 humdial challenge. arXiv preprint arXiv:2604.21406, 2026.

[48] Yueqian Wang, Songxiang Liu, Disong Wang, Nuo Xu, Guanglu Wan, Huishuai Zhang, and Dongyan Zhao. Mmduet2: Enhancing proactive interaction of video mlms with multi-turn reinforcement learning, 2025.

14

### A Detailed Evaluation Protocols

This section provides the complete evaluation protocols for the Real-Time Description and Proactive Reminder.

### A.1 Content Consistency

Content Consistency measures the factual consistency between the model-generated response and the video content, while ensuring alignment with user instructions.

### A.1.1 Evaluation Process

The evaluation follows a deduction-based scoring mechanism:

1. The evaluator starts from a perfect score of 3.00.

2. For each error identified, a specific penalty is deducted according to Table 5.

3. The final score is the maximum of the calculated result and 0.01, unless the response is completely empty or entirely irrelevant, in which case the score is 0.00.

### A.1.2 Penalty Table

<div style="text-align: center;">Table 5: Content Consistency Penalty Values</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Error Category</td><td style='text-align: center; word-wrap: break-word;'>Severity</td><td style='text-align: center; word-wrap: break-word;'>Penalty</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Critical Factual Error (wrong object/action/color/count)</td><td style='text-align: center; word-wrap: break-word;'>High</td><td style='text-align: center; word-wrap: break-word;'>-1.00</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Critical Factual Error (partially wrong, e.g., &quot;dark blue&quot; vs &quot;navy blue&quot;)</td><td style='text-align: center; word-wrap: break-word;'>Medium</td><td style='text-align: center; word-wrap: break-word;'>-0.75</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Minor Factual Error</td><td style='text-align: center; word-wrap: break-word;'>Low</td><td style='text-align: center; word-wrap: break-word;'>-0.25</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Hallucination (describing non-existent content)</td><td style='text-align: center; word-wrap: break-word;'>Severe</td><td style='text-align: center; word-wrap: break-word;'>-1.50</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Key Information Omission (missing main step/element)</td><td style='text-align: center; word-wrap: break-word;'>High</td><td style='text-align: center; word-wrap: break-word;'>-0.75</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Minor Detail Omission</td><td style='text-align: center; word-wrap: break-word;'>Low</td><td style='text-align: center; word-wrap: break-word;'>-0.25</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Vagueness (&quot;mixes something&quot; vs specific action)</td><td style='text-align: center; word-wrap: break-word;'>Medium</td><td style='text-align: center; word-wrap: break-word;'>-0.50</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Repetition</td><td style='text-align: center; word-wrap: break-word;'>Low</td><td style='text-align: center; word-wrap: break-word;'>-0.10</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Irrelevant Content</td><td style='text-align: center; word-wrap: break-word;'>Medium</td><td style='text-align: center; word-wrap: break-word;'>-0.50</td></tr></table>

### A.1.3 Evaluation Prompt

The following prompt is used for Content Consistency evaluation:

### Content Consistency Evaluation Prompt


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>You are a PRECISE CONTENT ACCURACY EVALUATOR. Your task is to assign a FINE-GRAINED decimal score (0.00-3.00) based on the model&#x27;s response accuracy.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Basic Information:
- Original user instruction: question
- Model generated response: &quot;response&quot;
- Reference annotations: gt_texts (if provided)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Scoring Rules:
1. Start from 3.00
2. Deduct penalties for each error
3. Output ONLY JSON with &quot;content_score&quot; and &quot;content_reasoning&quot;</td></tr></table>

15

### A.2 Temporal Sensitivity

Temporal Sensitivity measures the alignment between the model-generated text and the video's temporal windows—specifically, whether the model describes the corresponding video content at the appropriate time.

### A.2.1 Evaluation Process

The metric evaluates a timestamped response format  $ S = \{s_1, s_2, \ldots, s_n\} $ with each sentence  $ s_i $ associated with a time interval  $ [t_i^{\text{start}}, t_i^{\text{end}}] $. The Temporal Sensitivity evaluation consists of four steps:

Step 1: Semantic Relevance Filtering Each sentence  $ s_i $ with timestamp  $ (start_i, end_i) $ is classified as relevant or irrelevant. Irrelevant sentences (e.g., polite phrases like "No problem," "I'm happy to help") are excluded from temporal evaluation. The proportion of irrelevant sentences  $ r = |S_{\text{irr}}| / |S| $ is used for score attenuation.

Step 2: Multi-Window Sampling Based on the empirical observation that a 2-second perception-to-generation latency (d = 2) is reasonable for streaming models, four candidate windows are constructed for each relevant sentence:  $ w_1 : [t_i^{\text{start}} - 1, t_i^{\text{end}} - 1] $,  $ w_2 : [t_i^{\text{start}} - 2, t_i^{\text{end}} - 1] $,  $ w_3 : [t_i^{\text{start}} - 2, t_i^{\text{end}} - 2] $,  $ w_4 : [t_i^{\text{start}} - 1, t_i^{\text{end}}] $.

These windows account for potential latency variations around the assumed optimal delay.

Step 3: Multimodal Context Extraction For each candidate window  $ w_k(k \in [1,4]) $, the corresponding audio segment is extracted, and video frames are sampled at  $ f = 2 $ frames per second.

Step 4: Scoring An LLM judge evaluates the alignment between the sentence content and each candidate window, considering both visual and audio modalities. The sentence score  $ score(s_{i}) $ is the maximum across all windows, as shown in Equation 1.

### A.2.2 Final Score Calculation

The final Temporal Sensitivity score is computed as:

 $$ \mu_{rel}=\frac{1}{\left|S_{rel}\right|}\sum_{s\in S_{rel}}score(s) $$ 

 $$ S_{\mathrm{t e m p o r a l}}=\mu_{\mathrm{r e l}}\times(1-\lambda\cdot r) $$ 

where:

 $ \mu_{rel} $ is the average score of relevant sentences (0-3 scale);

• r is the proportion of irrelevant sentences;

•  $ \lambda $ is a hyperparameter controlling the penalty intensity. We set  $ \lambda = 1 $.

16

<div style="text-align: center;">Table 6: Temporal Sensitivity Scoring Criteria</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Score</td><td style='text-align: center; word-wrap: break-word;'>Definition</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>3</td><td style='text-align: center; word-wrap: break-word;'>Excellent temporal alignment. Response accurately describes the current video segment and aligns perfectly with the instruction.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>Moderate temporal alignment. Response is generally accurate but has minor inaccuracies or contains some descriptions of other time periods.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>Poor temporal alignment. Response has significant issues, largely describes wrong time periods, or is mostly irrelevant.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'>No temporal alignment. Response is completely irrelevant or describes completely wrong time periods.</td></tr></table>

<div style="text-align: center;">Table 7: Relevance Classification Criteria</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Label</td><td style='text-align: center; word-wrap: break-word;'>Definition</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Relevant (1)</td><td style='text-align: center; word-wrap: break-word;'>Contains substantive content responding to the instruction or describing video content.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Irrelevant (0)</td><td style='text-align: center; word-wrap: break-word;'>Polite phrases, acknowledgments, thinking pauses, or generic responses without substantive content.</td></tr></table>

### A.2.3 Temporal Sensitivity Scoring Guidelines

### A.2.4 Relevance Classification Guidelines

### A.2.5 Evaluation Prompt for Temporal Sensitivity


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Temporal Sensitivity Evaluation Prompt</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>You are a professional evaluator for real-time multimodal systems.\nBasic Information:\n- Analysis Time Range: Video segment from starts to ends\n- Original Instruction: question\n- Response to Evaluate: &quot;sentence&quot;</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Scoring Guidelines:\n- 3: Excellent temporal alignment\n- 2: Moderate temporal alignment\n- 1: Poor temporal alignment\n- 0: No temporal alignment</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Answer Relevance Classification:\n- Relevant (1): Contains substantive content\n- Irrelevant (0): Only polite phrases or acknowledgments</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Output JSON:\n{\n  &quot;temporal_score&quot;: &lt;0-3&gt;,\n  &quot;temporal_reasoning&quot;: &quot;&lt;explanation&gt;&quot;.\n  &quot;is_relevant&quot;: &lt;0 or 1&gt;\n}</td></tr></table>

### A.3 Proactive Reminder Evaluation

Proactive Reminder evaluates the ability to identify relevant events and determine appropriate response timing. The evaluation follows a two-stage pipeline: (1) temporal window extraction and (2) LLM-based judgment.

17

### A.3.1 Temporal Window Extraction

Given annotated event timestamps from the ground truth, we extract the model's response within a fixed time window following each event occurrence. Specifically, for each reminder event with start time  $ t_{event} $, we collect all model-generated sentences whose timestamp falls within  $ [t_{event}, t_{event} + \Delta] $, where  $ \Delta = 10 $ seconds is the evaluation window. These collected sentences are concatenated to form the response segment for that event.

 $$  response\_{s}egment(t_{event})=\bigcup\{s_{i}\mid t_{event}\leq time(s_{i})\leq t_{event}+\Delta\} $$ 

### A.3.2 LLM Judgment Prompt

The extracted response segment is evaluated by an LLM-as-a-Judge framework. The prompt varies by task type.

Event Reminder & Post-Event Reminder Prompt:

Event Reminder Evaluation Prompt

Please determine whether the model's output correctly completes the reminder task.
Task Description:
The user gives an instruction to remind them when a specific event occurs.
We have extracted the model's text generated immediately after the event (within a 10-second window).
Determine whether the text clearly demonstrates that "the event has occurred" as a reminder.

Input:
- User instruction: {instruction}
- Model output: {"response"}

Criteria:
The model output must satisfy:
1. Clearly refer to the target event described in the instruction;
2. Express an intention to remind or inform that the event has occurred;
3. Not be vague or unrelated to the event;
4. If the output is ambiguous, misidentifies the event, or does not mention the event, it is considered a failure.

Scoring:
- 1 = Successful reminder (explicitly mentions the event and completes the reminder)
- 0 = Unsuccessful reminder (vague / incorrect / event not mentioned)

Output Format:
Only output JSON:
{
"success_score": <0 or 1>,
"reasoning": "<explanation>"
}

Correction Task Prompt:

18

Correction Task Evaluation Prompt

Please determine whether the model's output correctly completes the correction task.
Task Description:
The user provides an instruction or statement that contains incorrect information.
The system needs to identify the error and provide the correct information.

Input:
- User instruction: {instruction}
- Ground truth answer: {ground_answer}
- Model output: "response"

Criteria:
1. Compare the user instruction with the ground truth answer to identify the error(s).
2. Check whether the model output corrects these error(s) consistent with the ground truth.
3. The correction must maintain correct context (e.g., subject, object) consistent with both instruction and answer.
4. Extra information unrelated to correction should be ignored, unless it contradicts the instruction or answer.

Scoring:
- 1 = Successful correction (all errors corrected with consistent context)
- 0 = Unsuccessful correction (missing errors, inconsistent correction, or context mismatch)

Output Format:
Only output JSON:
{
"success_score": <0 or 1>,
"reasoning": "<explanation>"
}

### A.3.3 Final Score Calculation

For a sample containing  $ N $ events (reminders), let  $ score_j \in \{0,1\} $ be the LLM judgment for event  $ j $. The sample-level total score is defined as:

 $$ \mathbf{Score_{sample}}=\mathbf{1}\left[\sum_{j=1}^{N}score_{j}=N\right] $$ 

where  $ 1[\cdot] $ is the indicator function. That is, the sample is considered successful only if all events are correctly handled. This strict criterion reflects the real-world requirement for reliable proactive systems.

The overall model performance on a task is the average of sample-level scores across all samples in that task.

### B Iterative Design and Human Alignment Analysis

### B.1 Motivation

Omni-DuplexEval evaluates open-ended responses without objective ground-truth answers. To ensure that our automatic evaluation framework aligns with human perception, we constructed a calibration set with the help of human annotators and iteratively refined our evaluation prompts and strategies. The Spearman correlation between automatic evaluation scores and human judgments serves as the alignment metric throughout this process.

19

### B.2 Calibration Set Construction

To systematically calibrate the two evaluation metrics (Content Consistency and Temporal Sensitivity), we constructed a calibration set following a controlled design. For a given video-question instance, we generated responses that vary the scores of the two metrics in a structured manner.

Specifically, we fixed two metrics at their maximum score (3.00) while varying the remaining metric across the full range (0, 1, 2, 3). This yielded the following 7 distinct score combinations (ordered as Temporal Sensitivity - Content Consistency :

In addition, two reference ground-truth responses were included as baselines. In total, the calibration set comprises 7 distinct video-question instances, yielding 63 annotated answer samples (7 instances  $ \times $ 9 responses per instance). Each response was manually annotated by human evaluators to establish reference scores for all three metrics.

### B.3 Iterative Refinement and Results

### B.3.1 Content Consistency

For Content Consistency, we experimented with:

• Different frame sampling rates (0.5 FPS vs. 0.3333 FPS)

• Different numbers of ground-truth references (0, 1, or 2 GT files)

• Prompt refinements to improve scoring precision

<div style="text-align: center;">Table 8: Content Consistency Iteration Results</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Configuration</td><td style='text-align: center; word-wrap: break-word;'>Spearman Correlation</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0 GT, 0.5 FPS</td><td style='text-align: center; word-wrap: break-word;'>0.8258</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>1 GT, 0.5 FPS</td><td style='text-align: center; word-wrap: break-word;'>0.8368</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>2 GT, 0.5 FPS</td><td style='text-align: center; word-wrap: break-word;'>0.8969</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0 GT, 0.3333 FPS</td><td style='text-align: center; word-wrap: break-word;'>0.8164</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>1 GT, 0.3333 FPS</td><td style='text-align: center; word-wrap: break-word;'>0.8573</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>2 GT, 0.3333 FPS</td><td style='text-align: center; word-wrap: break-word;'>0.9165</td></tr></table>

The best alignment was achieved with 2 GT references at 0.3333 FPS.

### B.3.2 Temporal Sensitivity

For Temporal Sensitivity, we explored multiple strategies:

• Window Strategy: Compared single-window (shifting start/end by -2 seconds) against four-window sampling (shifting start/end by -1/-2 seconds) to tolerate reasonable perception-to-generation latency.

- Unit of Analysis: Compared sentence-level segmentation (sentence-ctc) against action-level segmentation (action-ctc) based on semantic boundaries.

- Modality for Alignment: Compared using video frames (2 FPS) as context versus using ground-truth text with character-level timestamps as an oracle reference.

• Prompt Refinement: Iteratively adjusted LLM judge prompts based on disagreement analysis from human re-annotation.

- Irrelevant Sentence Penalty: Introduced attenuation factor  $ \lambda = 1 $ to penalize polite phrases and non-substantive responses.

• Sampling Rate: Compared video frame sampling at 2 FPS versus 3 FPS for context extraction.

• Window Selection Policy: Adjusted candidate window offsets from symmetric shifts to an optimized asymmetric strategy favoring slightly delayed responses.

20

<div style="text-align: center;">Table 9: Temporal Sensitivity Iteration Results</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Configuration</td><td style='text-align: center; word-wrap: break-word;'>Variant A</td><td style='text-align: center; word-wrap: break-word;'>Variant B</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Window Strategy</td><td style='text-align: center; word-wrap: break-word;'>Single-window (0.7021)</td><td style='text-align: center; word-wrap: break-word;'>→ Four-window (0.7343)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Unit of Analysis</td><td style='text-align: center; word-wrap: break-word;'>Action-level (0.6841 / 0.5781)</td><td style='text-align: center; word-wrap: break-word;'>→ Sentence-level (0.7343)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Modality for Alignment</td><td style='text-align: center; word-wrap: break-word;'>Video frames (2 FPS) (0.7343)</td><td style='text-align: center; word-wrap: break-word;'>→ GT text (0.7130)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Prompt Refinement</td><td style='text-align: center; word-wrap: break-word;'>Initial prompt (0.7417)</td><td style='text-align: center; word-wrap: break-word;'>→ Refined prompt (0.7626)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Irrelevant Sentence Penalty</td><td style='text-align: center; word-wrap: break-word;'>Without penalty (0.7626)</td><td style='text-align: center; word-wrap: break-word;'>→ With  $ \lambda $ (0.7988)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Sampling Rate</td><td style='text-align: center; word-wrap: break-word;'>2 FPS (0.7988)</td><td style='text-align: center; word-wrap: break-word;'>→ 3 FPS (0.7201)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Window Selection Policy</td><td style='text-align: center; word-wrap: break-word;'>Symmetric shifts (0.7988)</td><td style='text-align: center; word-wrap: break-word;'>→ Asymmetric strategy (0.7887)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Final Configuration</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>0.7988</td></tr></table>

### B.3.3 Final Configuration Summary

Based on the iterative refinement, the final evaluation framework adopts:

• Content Consistency: 2 GT references, 0.3333 FPS sampling rate

• Temporal Sensitivity: Four-window sampling with sentence-ctc, irrelevant sentence penalty, and prompt refined against human re-annotations

The final Spearman correlation between automatic evaluation and human judgments exceeds 0.9 for Content Consistency, and approaches 0.8 for Temporal Sensitivity, demonstrating strong alignment with human perception.

### C Experimental Settings

### C.1 Baselines.

We select four representative streaming and duplex multimodal models for evaluation, covering a range of real-time interaction settings and architectural designs:

MiniCPM-o 4.5 [7]: A multimodal omni-interaction model capable of full-duplex streaming conversation, processing interleaved audio and video frames in real-time.

• LiveCC [6]: A real-time vision-language model optimized for live video captioning and commentary generation.

• MMDuet2 [48]: A multimodal duplex interaction model capable of handling continuous multimodal inputs.

• StreamingVLM [28]: A vision-language model specifically tailored for processing continuous streaming video inputs with low latency.

### C.2 Implementation Details.

- MiniCPM-o 4.5 $ ^{3} $: We evaluate the model in a full-duplex streaming setting. The model processes synchronized video frames and audio segments chunk by chunk. We use a sampling-based decoding strategy and set the maximum number of newly generated speak

 $ ^{3} $https://github.com/OpenBMB/MiniCPM-o

21

tokens per chunk to 20 to maintain low latency. A reference audio is provided to guide the voice generation during the streaming omni conversation, and the system prompt is set to "Streaming Omni Conversation." The average inference time is approximately 150-200 ms per multimodal chunk, ensuring seamless real-time interaction.

• LiveCC $ ^{4} $: The repetition penalty is set to 1.05, and the streaming end-of-sequence (EOS) base threshold is set to 0.0. The model processes video frames at 2 FPS. The inference latency is roughly 400-500 ms per step, which strictly meets the real-time commentary requirements.

• MMDuet2 $ ^{5} $: We use the Qwen2.5-VL-3B-Instruct based checkpoint. The model is evaluated in an online streaming mode, generating responses based on continuously incoming video frames. The maximum number of new tokens is set to 512, and the model maintains a continuous key-value (KV) cache across turns. Benefiting from its lightweight 3B architecture, it achieves a low inference latency of approximately 200-300 ms per turn.

• StreamingVLM $ ^{6} $: We use the Qwen2.5-VL-7B-Instruct based checkpoint. The model processes video chunks with a duration of 1 second per chunk, maintaining a visual window size of 16 frames and a text context round of 16. The temperature is set to 0.9, and the repetition penalty is 1.05. It is highly efficient, processing 1-second video chunks in approximately 125-150 ms.

Compute Resources. All inference experiments are conducted on an internal cluster equipped with NVIDIA A100-SXM4 (80GB) GPUs. We employ a single NVIDIA A100 GPU per evaluation run.

### D Limitations

Although Omni-DuplexEval provides a benchmark for real-time duplex interaction, several limitations remain. First, the current benchmark mainly focuses on relatively short streaming interactions and does not fully capture long-term conversational scenarios requiring persistent memory or planning. Second, our evaluation framework relies on LLM-as-a-Judge. While we incorporate reference annotations and carefully designed prompts, automatic evaluation may still exhibit biases in open-ended settings. Finally, the number of evaluated duplex models remains limited due to the scarcity of publicly available real-time multimodal systems. We expect future advances in streaming MLLMs to further expand the scope of evaluation.

### E Broader Impacts

This work introduces a benchmark for evaluating real-time duplex interaction in multimodal systems. We believe it can support future research on more reliable and responsive AI assistants in streaming environments, with potential applications in accessibility support, live interaction, and real-time multimodal assistance.

At the same time, more capable real-time multimodal systems may also introduce risks if misused. For example, such systems could be applied to generate misleading live content, impersonation, or automated real-time interaction at scale. In addition, failures in temporal decision-making may lead to inappropriate or mistimed responses in sensitive scenarios.

Our work focuses on evaluation rather than deployment. During dataset construction, we avoid collecting personal sensitive information and manually filter potentially unsafe or high-risk content. We hope that standardized evaluation can help better understand the limitations of current systems and support the development of safer real-time multimodal interaction.

 $ ^{4} $https://github.com/showlab/livecc

 $ ^{5} $https://github.com/yellow-binary-tree/MMDuet2

 $ ^{6} $https://github.com/mit-han-lab/streamingvlm

22