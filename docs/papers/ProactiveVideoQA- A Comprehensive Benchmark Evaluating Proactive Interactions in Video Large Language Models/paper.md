arXiv:2507.09313v2 [cs.CV] 15 Jul 2025

# ProactiveVideoQA: A Comprehensive Benchmark Evaluating Proactive Interactions in Video Large Language Models

Yueqian Wang $ ^{1} $, Xiaojun Meng $ ^{2} $, Yifan Wang $ ^{3} $, Huishuai Zhang $ ^{1,4} $, Dongyan Zhao $ ^{1,4} $,

 $ ^{1} $Wangxuan Institute of Computer Technology, Peking University

 $ ^{2} $Huawei Noah's Ark Lab

 $ ^{3} $School of Intelligence Science and Technology, University of Science and Technology Beijing  

 $ ^{4} $National Key Laboratory of General Artificial Intelligence

Correspondence: zhanghuishuai@pku.edu.cn, zhaodongyan@pku.edu.cn

## Abstract

With the growing research focus on multimodal dialogue systems, the capability for proactive interaction is gradually gaining recognition. As an alternative to conventional turn-by-turn dialogue, users increasingly expect multimodal systems to be more initiative, for example, by autonomously determining the timing of multi-turn responses in real time during video playback. To facilitate progress in this emerging area, we introduce ProactiveVideoQA, the first comprehensive benchmark to evaluate a system's ability to engage in proactive interaction. Since model responses are generated at varying timestamps, we further propose PAUC, the first metric that accounts for the temporal dynamics of model responses. This enables a more accurate evaluation of systems operating in proactive settings. Through extensive benchmarking of various baseline systems on ProactiveVideoQA and a user study of human preferences, we show that PAUC is in better agreement with human preferences than traditional evaluation metrics, which typically only consider the textual content of responses. These findings demonstrate that PAUC provides a more faithful assessment of user experience in proactive interaction scenarios. $ ^{1} $

## 1 Introduction

Recently, video multimodal large language models (Video MLLMs) have undergone rapid development. With increasingly powerful video understanding capabilities and support for diverse input modalities (Li et al., 2024a; Zhang et al., 2024a; Bai et al., 2025; Chen et al., 2024b; Zhang et al., 2024b; Xu et al., 2025), MLLMs are being deployed across a growing range of real-world scenarios.

Beyond advancements in model architecture and training paradigms, there is also a surge of interest in exploring novel interaction paradigms between users and models. A comparative illustration of these interaction methods is presented in Fig. 1. In offline interaction, users must upload the entire video before posing any questions, allowing the model to generate responses after consuming the whole video. In contrast, online interaction allows users to query the model in real time as the video plays, with the model required to respond immediately using only the information observed up to that point.



In addition to offline and online paradigms, proactive interaction has emerged as a promising and increasingly studied direction in video-text MLLMs (Chen et al., 2024a; Wang et al., 2024; Qian et al., 2025; Yao et al., 2025). The defining characteristic of proactive interaction is that the model autonomously determines when to respond during video playback, rather than replies solely in response to user-initiated queries. This capability necessitates continuous monitoring of evolving visual and textual cues, real-time detection of salient moments, and timely, contextually appropriate responses. Proactive video MLLMs hold significant potential for real-time scenarios, including live stream understanding, intelligent surveillance, egocentric assistants, and socially interactive AI agents.

While several models claim to have proactive response capabilities, their evaluations are often conducted on benchmarks that do not actually require such novel interaction. For example, most experiments are performed in offline settings where models are not required to autonomously determine when to respond, and are evaluated using multiple-choice questions rather than open-ended dialogue, which significantly differs from real-world application scenarios.

Although some benchmarks do include tasks that require response timing decisions (Lin et al., 2024; Wang et al., 2025), they still suffer from critical limitations. Specifically: (1) the questions and an-

 $ ^{1} $Project homepage: https://github.com/yellow-binarytree/ProactiveVideoQA

1

<div style="text-align: center;"><img src="imgs/img_in_image_box_138_150_774_463.jpg" alt="Image" width="53%" />

Online Interaction
What is the woman doing in the video?
What is the woman doing now?
She is looking at a white horse.
Assistant
What is she doing now?
She is talking to the camera.
Assistant
What is she doing now?
Assistant
What is the woman doing now?
Assistant
She is looking at a white horse.
Assistant
She is talking to the camera.
Assistant
She is talking to the camera.
Assistant
She is talking to the camera.
Assistant
She is talking to the camera.
Assistant
User
User is the woman doing now?
What is the woman doing now?
What is she doing now?
Assistant
What is the woman doing now?
She is talking to the camera.
Assistant
What is the woman doing now?
She is talking to the camera.
Assistant
What is the woman doing now?
She is talking to the camera.
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
What is the woman doing now?
She is talking to the camera.
Assistant
What is the woman doing now?
She is talking to the camera.
Assistant
User is the woman doing now?
What is the woman doing now?
What is she doing now?
Assistant
What is the woman doing now?
She is talking to the camera.
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
What is the woman doing now?
What is she doing now?
Assistant
What is the woman doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
Assistant
User is the woman doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now?
What is she doing now

</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_797_177_1045_352.jpg" alt="Image" width="20%" />

Experience Quality
Browse product reviews
Get free trial
Get customer service
Find product at app store
Have payment issues

</div>


<div style="text-align: center;">Figure 1: A demonstration of offline, online and proactive interaction.</div>


<div style="text-align: center;">Figure 2: An example of user journey map. The content in the figure is fictional only for demonstration purpose.</div>


swers are overly simplistic (e.g., “Inform me when [event] happens”), thereby evaluating only the timing of the response while ignoring the quality of its content; or (2) they have only a single round of response, rather than supporting multi-turn, context-aware interactions.

A more fundamental issue is the lack of appropriate evaluation metrics. Unlike in offline or online interactions, proactive interaction allows the model autonomously generating a sequence of responses at varying points in time, with the output evolving continuously. As such, evaluation methods must capture this temporal progression and take the models' timing strategy into account, rather than relying solely on static snapshots or isolated response instances.

To address this gap and advance research on proactive interaction, we introduce ProactiveVideoQA, the first comprehensive benchmark specifically designed to evaluate the proactive interaction capabilities of MLLMs. ProactiveVideoQA specifically targets the task of question answering: given a question presented at the very beginning of the video, the system must proactively detect when relevant information appears in one or more video segments and initiate responses accordingly as the video progresses. Compared to more open-ended interactive tasks, this question-answering setup offers relatively objective evaluation criteria (e.g., the availability of ground-truth answers), making it particularly suitable for academic research. By constructing a suite of diverse tasks and collecting videos from a wide range of sources, ProactiveVideoQA encompasses several representative application scenarios for proactive interaction. It includes a broad spectrum of video topics, integrates multiple modalities, and supports multi-turn outputs to reflect realistic and varied use cases.



In addition, we propose PAUC (Proactive Area Under Curve), a novel evaluation metric tailored to better capture the performance of proactive interaction systems. The design of PAUC is inspired by the user journey map (Huo et al., 2023), a widely used visualization tool in human-computer interaction research. An example of user journey map is shown in Fig. 2. A user journey map typically employs a line graph to illustrate how users interact with a system over time, capturing the temporal dynamics of their experiences, including shifts in emotion, engagement, and pain points—rather than relying on static snapshots.

Analogously, PAUC employs a line graph to track how the quality of a model's responses evolves throughout the video, thereby highlighting the inherently dynamic nature of proactive interaction. This temporal perspective sets PAUC apart from traditional metrics designed for offline interactions, which evaluate only static textual outputs.

To summarize, this work presents three key contributions:

(1) Benchmark with Multi-turn, fully open-ended answers. Unlike most existing video question answering benchmarks that predominantly adopt multiple-choice formats, ProactiveVideoQA features fully open-ended questions requiring multiturn, free-form textual responses. While this design introduces additional challenges for evaluation, it offers a more realistic and comprehensive assessment of a model's interactive capabilities and is closer to real-world application scenarios.

(2) Benchmark with diverse topics and multi-modal inputs. ProactiveVideoQA includes videos covering a wide array of topics that are highly relevant to proactive interaction, such as web videos,

2

egocentric recordings, television series, and surveillance footage. It also incorporates multiple input modalities including text, video, and speech, reflecting the complexity and richness of real-world use cases.

(3) A reply time-aware metric for proactive evaluation. We introduce PAUC, a novel evaluation metric that captures the evolving nature of model responses in proactive interaction settings. By explicitly modeling how response quality changes over time, PAUC provides stronger alignment with human judgments and better reflects the user experience.

## 2 Related Works

### 2.1 Video Understanding Benchmarks

Recent years have witnessed a surge in video understanding and question-answering benchmarks. (Li et al., 2023b; Fu et al., 2024; Cai et al., 2024; Li et al., 2023c,a, 2024b; Fang et al., 2024) While these benchmarks cover videos of diverse topics, lengths, and question-answering formats, the interaction method remains predominantly in the most widely studied offline interaction.

To explore the applicability of video-text MLLMs in streaming video scenarios, a number of benchmarks have recently been introduced, often labeled with terms such as “streaming” or “online” (Lin et al., 2024; Wang et al., 2025; Li et al., 2025; Liu et al., 2024). These terms emphasize that user queries are injected at specific time points during video playback. However, they generally do not enable any flexibility on when the model should respond. In fact, with the exception of a few sub-tasks, the majority of these benchmarks require the model to respond immediately following a user question, effectively reduces the task to offline video understanding up to the time of the query.

Distinct from all prior works, this study introduces the first benchmark and evaluation metric specifically designed for proactive interaction, explicitly accounting for the temporal evolution of model responses. Moreover, it emphasizes open-ended question answering, despite posing greater challenges for evaluation, better reflects the demands of real-world applications compared to multiple-choice formats.

### 2.2 Proactive Video-Text LLMs

VideoLLM-Online (Chen et al., 2024a) is one of the first works that adapt video-text MLLMs to proactive interaction scenarios. MMDuet (Wang et al., 2024) improves upon this by being trained on more diverse tasks and datasets, yet it still face problems like inaccurate response timing and redundant outputs. Dispider (Qian et al., 2025) introduces a disentangled framework of perception, decision, and reaction, and TimeChat-Online (Yao et al., 2025) focuses on the token compression techniques of the input video stream.

While these studies propose different approaches to enhance proactive modeling, the majority of their experiments are conducted under non-proactive interaction settings, where models are not required to autonomously determine response timing. Consequently, they fall short of thoroughly evaluating the core capabilities needed for proactive interaction. This underscores the urgent need for a benchmark specifically designed to evaluate and facilitate the development of proactive video-text MLLMs.

## 3 The PAUC Metric

In existing NLP evaluation methods, metrics are typically computed by comparing the model's complete output against the ground-truth answer, using criteria such as n-gram overlap (Papineni et al., 2002; Vedantam et al., 2014), semantic similarity (Zhang et al., 2019) or LLM-based Evaluation (Li et al., 2024c). While these metrics are widely used to assess the quality of textual outputs, they fall short in capturing how model performance evolves over time in proactive interaction scenarios.

To address this limitation, we propose PAUC (Proactive Area Under Curve), a novel evaluation metric that jointly considers both the timing and content of model responses within a unified framework. Drawing inspiration from the concept of a user journey map which visualizes user experience as a dynamic line graph over the course of interactions, PAUC plots a timestamp-score curve based on the model's outputs and computes the area under the resulting polyline to represent the model's proactive capabilities.

This design enables PAUC to reflect the temporal evolution of user experience (i.e., the correctness of model responses over time), which is a defining feature of proactive interaction compared to traditional offline interaction.

Formally, suppose there are G turns of ground-

3

truth replies in a video, where each reply consists of a textual content  $ gold_{g} $ and an associated timespan  $ (t_{g}^{start}, t_{g}^{end}) $, for  $ g = 1, 2, \ldots, G $. This indicates that during the interval  $ (t_{g}^{start}, t_{g}^{end}) $, the user expects to receive the information contained in  $ gold_{g} $. While we acknowledge that evaluating proactive interaction experiences is inherently subjective, here we assume the existence of an ideal ground truth for a quantitative and objective measurement of proactive model performance.

PAUC operates independently on each ground-truth reply turn. Since the following introduction to PAUC is conducted within a single reply turn ( $ gold_{g}, t_{g}^{start}, t_{g}^{end} $), we will omit the subscript “g” for simplicity.

Suppose that, for a given reply timespan  $ (t^{start}, t^{end}) $, there are P model responses that fall within this interval. Each response is associated with textual content  $ pred_p $ and a timestamp  $ \tau_p $, where  $ p = 1, 2, \ldots, P $ and  $ t^{start} < \tau_1 < \tau_2 < \cdots < \tau_P < t^{end} $.

To assess the correctness of model predictions up to each timestamp $\tau_{p}$, we input the question, the ground-truth answer gold, and the set of model responses generated before $\tau_{p}$, i.e., $\{pred_{1}, pred_{2}, \ldots, pred_{p}\}$, into a large language model (GPT-4.1 in our implementation). The model is instructed to assign a score reflecting how well this set of accumulated responses aligns with the ground-truth answer. This score is denoted as $s_{p}$, representing the quality of the model's responses up to $\tau_{p}$.

In our implementation, $s_p$ takes a discrete value from 0, 1, 2 (with a maximum score $S = 2$), corresponding to completely incorrect, partially correct, and mostly correct predictions, respectively. We also experimented with finer-grained scoring scales (e.g., 0, 1, 2, 3, 4 with $S = 4$). However, human studies and interviews revealed that evaluators are generally insensitive to subtle differences in response quality under proactive interaction settings. Consequently, we adopt a coarser-grained scale with $S = 2$ for better consistency and interpretability.

Finally, we construct a polyline in the time-score coordinate space by using  $ \tau_p $ as the  $ x $-axis values and the corresponding  $ s_p $ as the  $ y $-axis values. To make the polyline continuous in  $ (t^{start}, t^{end}) $, we add two additional points as endpoints of the polyline:  $ (t^{start}, 0.5) $ as the initial point and  $ (t^{end}, s_P) $ as the final point. The initial score of 0.5 reflects

<div style="text-align: center;"><img src="imgs/img_in_image_box_615_144_1050_396.jpg" alt="Image" width="36%" />

Question: What are the steps involved in preparing a sandwich?
Ground Truth Answer: [311-360s] Spread mayonnaise on sandwich breads.
Model Responses: [312s] Place a slice of sandwich bread on the counter, and place a cooked sausage on the bread.
[328s] Grab a slice of sandwich bread and apply a spread on it.
[344s] Spread mayonnaise or a replacement on the bread.
[352s] Take two slices of sandwich bread and spread fillings on them.
Score
Upper bound: (360-311)×2-98
(312-311)×0.5+(344-328)×1+(360-344)×2-48.5
312s
328s
344s
352s
Score
Model Score: PAUC: 48.5+98=0.49
311s 312s 328s 344s 352s 360s

</div>


<div style="text-align: center;">Figure 3: An Illustration of the PAUC metric.</div>


the intuition that providing no response is preferable to giving entirely incorrect answers, which receive a score of 0 from the LLM evaluator. The final PAUC score for this ground-truth reply turn is defined as the ratio of the area under this curve to the maximum possible area ( by  $ (t^{end}-t^{start})\times S) $ as calculated by Eq. (1), where S is the maximum score.

 $$ \begin{aligned}&PAUC=[({\tau_{1}}-t^{start})\times0.5+\\ &\sum_{p=1}^{P-1}(\tau_{p+1}-\tau_{p})\times s_{p}+(t^{end}-\tau_{P})\times s_{P}]\\ &\div(q^{end}-q^{start})\times S\\ \end{aligned} $$ 

We use Eq. (1) to calculate  $ PAUC_g $ for each ground truth reply turn ( $ gold_g $,  $ t_g^{start} $,  $ t_g^{end} $), and use the average value of all turns as the final PAUC score of the entire video.

Despite its simplicity and intuitive design, the computation method of PAUC effectively achieves several key goals:

First, it rewards model responses that are both early and accurate. The more closely a model's reply aligns with the ground-truth answer, the higher the score assigned by the LLM evaluator, thereby increasing the overall PAUC value. Furthermore, when the correctness of a reply remains constant (e.g., score = 2), earlier delivery leads to an earlier rise in the score curve. This results in a larger area under the curve and consequently a higher PAUC score.

Second, PAUC penalizes incorrect responses. If the model produces a reply that contradicts the ground-truth answer, this incorrect response is included in the accumulated input to the LLM for all subsequent timestamps. As a result, the presence of an incorrect reply reduces the likelihood of receiving high scores at later points, thereby lowering

4

the area under the curve and the final PAUC value.

### 3.1 Adjusting the Importance of Timeliness

However, in real-world applications, different tasks often impose different demands on the importance of timeliness. For example, in scenarios where timeliness is critical, responses generated just before  $ t^{end} $ contribute only marginal value. In contrast, in tasks where textual content takes precedence over response time, even late but accurate replies arriving just before  $ t^{end} $ can still be highly valuable.

To accommodate these differing priorities, we introduce a hyperparameter  $ \omega \in [0,1] $ to balance the importance of timeliness and correctness. Intuitively,  $ \omega $ controls the extent to which the  $ x $-coordinates  $ (\tau_p) $ of the points on the polyline are shifted leftward along the time axis:  $ \tau_p \to \tau'_p = t^{start} + (1 - \omega) \times (\tau_p - t^{start}) $.

When  $ \omega = 0 $, we have  $ \tau_p' = \tau_p $, meaning that the  $ x $-coordinates are not shifted leftward. This setting reflects scenarios where timeliness is very important: when a response's timestamp  $ \tau_p $ approaches the end of the reply timespan of the turn  $ t^{end} $ (i.e.,  $ t^{end} - \tau_p \to 0 $), its contribution to the final score becomes negligible according to Eq. (1).

In contrast, when $\omega > 0$, all $x$-coordinates are shifted left proportionally to their distance from $t^{start}$, thereby compressing the time intervals between adjacent predictions ($\tau_p - \tau_{p-1}$). This reduces the influence of temporal differences among responses. Meanwhile, as the gap between the last response time and end time, namely $t^{end} - \tau_P$, increases, the correctness score computed from all accumulated responses (recall that $s_P$ is obtained using the entire set of replies within the interval, $\{pred_1, pred_2, \ldots, pred_P\}$) exerts a greater effect on the final PAUC value. This behavior corresponds to scenarios where correctness increasingly outweighs timeliness as $\omega$ grows. In the extreme case of $\omega = 1$, all keypoints' $x$-coordinates are shifted entirely to $t^{start}$. Here, Eq. (1) degenerates to $(t^{end} - t^{start}) \times s_P$, equivalent to directly evaluating the correctness of the concatenated responses while completely ignoring their reply times. Here we recommend using $\omega = 0.5$ as the default setting.

It is also worth emphasizing that the PAUC framework is highly flexible. The use of an LLM as the evaluator (i.e., generating the correctness score on the y-axis) can be replaced with alternative metrics such as BLEU (Papineni et al., 2002), CIDEr

<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Point</th><th style='text-align: center;'>Score (ω = 0)</th><th style='text-align: center;'>Score (ω = 0.5)</th><th style='text-align: center;'>Score (ω = 1)</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>1</td><td style='text-align: center;'>360s</td><td style='text-align: center;'>360s</td><td style='text-align: center;'>360s</td></tr>
    <tr><td style='text-align: center;'>2</td><td style='text-align: center;'>344s</td><td style='text-align: center;'>327.5s</td><td style='text-align: center;'>319.5s</td></tr>
    <tr><td style='text-align: center;'>3</td><td style='text-align: center;'>328s</td><td style='text-align: center;'>319.5s</td><td style='text-align: center;'>300.0s</td></tr>
    <tr><td style='text-align: center;'>4</td><td style='text-align: center;'>300.0s</td><td style='text-align: center;'>300.0s</td><td style='text-align: center;'>290.0s</td></tr>
    <tr><td style='text-align: center;'>5</td><td style='text-align: center;'>290.0s</td><td style='text-align: center;'>290.0s</td><td style='text-align: center;'>280.0s</td></tr>
    <tr><td style='text-align: center;'>6</td><td style='text-align: center;'>280.0s</td><td style='text-align: center;'>280.0s</td><td style='text-align: center;'>270.0s</td></tr>
    <tr><td style='text-align: center;'>7</td><td style='text-align: center;'>270.0s</td><td style='text-align: center;'>270.0s</td><td style='text-align: center;'>260.0s</td></tr>
    <tr><td style='text-align: center;'>8</td><td style='text-align: center;'>260.0s</td><td style='text-align: center;'>260.0s</td><td style='text-align: center;'>250.0s</td></tr>
    <tr><td style='text-align: center;'>9</td><td style='text-align: center;'>250.0s</td><td style='text-align: center;'>250.0s</td><td style='text-align: center;'>240.0s</td></tr>
    <tr><td style='text-align: center;'>10</td><td style='text-align: center;'>240.0s</td><td style='text-align: center;'>240.0s</td><td style='text-align: center;'>230.0s</td></tr>
    <tr><td style='text-align: center;'>11</td><td style='text-align: center;'>230.0s</td><td style='text-align: center;'>230.0s</td><td style='text-align: center;'>220.0s</td></tr>
    <tr><td style='text-align: center;'>12</td><td style='text-align: center;'>220.0s</td><td style='text-align: center;'>220.0s</td><td style='text-align: center;'>210.0s</td></tr>
    <tr><td style='text-align: center;'>13</td><td style='text-align: center;'>210.0s</td><td style='text-align: center;'>210.0s</td><td style='text-align: center;'>200.0s</td></tr>
    <tr><td style='text-align: center;'>14</td><td style='text-align: center;'>200.0s</td><td style='text-align: center;'>200.0s</td><td style='text-align: center;'>190.0s</td></tr>
    <tr><td style='text-align: center;'>15</td><td style='text-align: center;'>190.0s</td><td style='text-align: center;'>190.0s</td><td style='text-align: center;'>180.0s</td></tr>
    <tr><td style='text-align: center;'>16</td><td style='text-align: center;'>180.0s</td><td style='text-align: center;'>180.0s</td><td style='text-align: center;'>170.0s</td></tr>
    <tr><td style='text-align: center;'>17</td><td style='text-align: center;'>170.0s</td><td style='text-align: center;'>170.0s</td><td style='text-align: center;'>160.0s</td></tr>
    <tr><td style='text-align: center;'>18</td><td style='text-align: center;'>160.0s</td><td style='text-align: center;'>160.0s</td><td style='text-align: center;'>150.0s</td></tr>
    <tr><td style='text-align: center;'>19</td><td style='text-align: center;'>150.0s</td><td style='text-align: center;'>150.0s</td><td style='text-align: center;'>140.0s</td></tr>
    <tr><td style='text-align: center;'>20</td><td style='text-align: center;'>140.0s</td><td style='text-align: center;'>140.0s</td><td style='text-align: center;'>130.0s</td></tr>
    <tr><td style='text-align: center;'>21</td><td style='text-align: center;'>130.0s</td><td style='text-align: center;'>130.0s</td><td style='text-align: center;'>120.0s</td></tr>
    <tr><td style='text-align: center;'>22</td><td style='text-align: center;'>120.0s</td><td style='text-align: center;'>120.0s</td><td style='text-align: center;'>110.0s</td></tr>
    <tr><td style='text-align: center;'>23</td><td style='text-align: center;'>110.0s</td><td style='text-align: center;'>110.0s</td><td style='text-align: center;'>100.0s</td></tr>
    <tr><td style='text-align: center;'>24</td><td style='text-align: center;'>100.0s</td><td style='text-align: center;'>100.0s</td><td style='text-align: center;'>90.0s</td></tr>
    <tr><td style='text-align: center;'>25</td><td style='text-align: center;'>90.0s</td><td style='text-align: center;'>90.0s</td><td style='text-align: center;'>80.0s</td></tr>
    <tr><td style='text-align: center;'>26</td><td style='text-align: center;'>80.0s</td><td style='text-align: center;'>80.0s</td><td style='text-align: center;'>70.0s</td></tr>
    <tr><td style='text-align: center;'>27</td><td style='text-align: center;'>70.0s</td><td style='text-align: center;'>70.0s</td><td style='text-align: center;'>60.0s</td></tr>
    <tr><td style='text-align: center;'>28</td><td style='text-align: center;'>60.0s</td><td style='text-align: center;'>60.0s</td><td style='text-align: center;'>50.0s</td></tr>
    <tr><td style='text-align: center;'>29</td><td style='text-align: center;'>50.0s</td><td style='text-align: center;'>50.0s</td><td style='text-align: center;'>40.0s</td></tr>
    <tr><td style='text-align: center;'>30</td><td style='text-align: center;'>40.0s</td><td style='text-align: center;'>40.0s</td><td style='text-align: center;'>30.0s</td></tr>
    <tr><td style='text-align: center;'>31</td><td style='text-align: center;'>30.0s</td><td style='text-align: center;'>30.0s</td><td style='text-align: center;'>20.0s</td></tr>
    <tr><td style='text-align: center;'>32</td><td style='text-align: center;'>20.0s</td><td style='text-align: center;'>20.0s</td><td style='text-align: center;'>10.0s</td></tr>
    <tr><td style='text-align: center;'>33</td><td style='text-align: center;'>10.0s</td><td style='text-align: center;'>10.0s</td><td style='text-align: center;'>0.0s</td></tr>
    <tr><td style='text-align: center;'>34</td><td style='text-align: center;'>0.0s</td><td style='text-align: center;'>0.0s</td><td style='text-align: center;'>0.0s</td></tr>
    <tr><td style='text-align: center;'>35</td><td style='text-align: center;'>0.0s</td><td style='text-align: center;'>0.0s</td><td style='text-align: center;'>0.0s</td></tr>
    <tr><td style='text-align: center;'>36</td><td style='text-align: center;'>0.0s</td><td style='text-align: center;'>0.0s</td><td style='text-align: center;'>0.0s</td></tr>
  </tbody>
</table>

<div style="text-align: center;">Figure 4: An Illustration of the effects of  $ \omega $.</div>


(Vedantam et al., 2014), or accuracy, depending on specific application requirements.

## 4 The ProactiveVideoQA Benchmark

To make use of PAUC, a benchmark is required for evaluating proactive models. We introduce ProactiveVideoQA, the first comprehensive benchmark designed for proactive interaction. To encompass prevalent scenarios in proactive interaction, ProactiveVideoQA focuses on four key tasks:

(1) proactive web-video QA ([WEB]): centering on general web-video understanding. (2) proactive ego-centric video QA ([EGO]): centering on first-person-view video comprehension, particularly relevant in robotics and daily assistant applications. (3) proactive TV-series video QA ([TV]): emphasizing dialogue and social relationship understanding with speech input, and (4) proactive video anomaly detection ([VAD]) targeting surveillance video monitoring and alerting. Illustrative examples of these tasks are provided in Fig. 5, while a detailed dataset statistics is presented in Tables 1 and 2.

### 4.1 Dataset Construction

#### 4.1.1 Data Source

There are already many offline VideoQA benchmarks focusing on various capabilities. To construct ProactiveVideoQA, we source video and annotations from Shot2story-MAGQA-39k for [WEB] (Wang et al., 2024; Han et al., 2023), Ego4D Goalstep (Song et al., 2023) for [EGO], TVQA (Lei et al., 2018) for [TV], and UCF-Crime (Sultani et al., 2018; Yuan et al., 2023) for [VAD].

5

<div style="text-align: center;"><img src="imgs/img_in_image_box_140_141_1049_530.jpg" alt="Image" width="76%" />

[WEB] Web Videos
[EGO] Ego-centric Videos
Q: What is happening inside the car?
① [9.6s-13.7s] There is a man driving a car.
② [12.8s-14.0s] A person is operating the button on the lower right-hand side of the steering wheel.
Q: What ingredients are added to the tikka sauce during the preparation process?
① [5.8s-20.5s] Diced carrots are added to the tikka sauce.
② [187.9s-231.4s] Broccoli and cauliflower are added to the sauce.
[TV] TV Series Videos
Sheldon, you know what I think of when I'm scared? Voyager space probe.
Whenever I feel that way, I think about how Voyager is still out there.
Q: What voyager is Raj referring to when he confides in Sheldon about his fears?
① [11.5s-27.5s] Raj is talking about voyager the space probe.
[VAD] Video Anomaly Detection (Surveillance Videos)
Q: What harmful or unlawful activities are happening in the video?
① [19.0s-29.0s] The woman took a cup from the shelf and put it into her bag, then reached out and fumbled for a while.

</div>


<div style="text-align: center;">Figure 5: Example data from different tasks.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>[WEB]</td><td style='text-align: center; word-wrap: break-word;'>[EGO]</td><td style='text-align: center; word-wrap: break-word;'>[TV]</td><td style='text-align: center; word-wrap: break-word;'>[VAD]</td></tr><tr><td style='text-align: center; word-wrap: break-word;'># videos</td><td style='text-align: center; word-wrap: break-word;'>500</td><td style='text-align: center; word-wrap: break-word;'>326</td><td style='text-align: center; word-wrap: break-word;'>450</td><td style='text-align: center; word-wrap: break-word;'>101</td></tr><tr><td style='text-align: center; word-wrap: break-word;'># examples</td><td style='text-align: center; word-wrap: break-word;'>500</td><td style='text-align: center; word-wrap: break-word;'>326</td><td style='text-align: center; word-wrap: break-word;'>500</td><td style='text-align: center; word-wrap: break-word;'>101</td></tr><tr><td style='text-align: center; word-wrap: break-word;'># reply turns</td><td style='text-align: center; word-wrap: break-word;'>1328</td><td style='text-align: center; word-wrap: break-word;'>1575</td><td style='text-align: center; word-wrap: break-word;'>500</td><td style='text-align: center; word-wrap: break-word;'>107</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>reply / example</td><td style='text-align: center; word-wrap: break-word;'>2.66</td><td style='text-align: center; word-wrap: break-word;'>4.83</td><td style='text-align: center; word-wrap: break-word;'>1.00</td><td style='text-align: center; word-wrap: break-word;'>1.06</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>video len (s)</td><td style='text-align: center; word-wrap: break-word;'>16.59</td><td style='text-align: center; word-wrap: break-word;'>360.00</td><td style='text-align: center; word-wrap: break-word;'>75.57</td><td style='text-align: center; word-wrap: break-word;'>121.03</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>reply span len (s)</td><td style='text-align: center; word-wrap: break-word;'>5.51</td><td style='text-align: center; word-wrap: break-word;'>29.20</td><td style='text-align: center; word-wrap: break-word;'>12.08</td><td style='text-align: center; word-wrap: break-word;'>17.96</td></tr></table>

<div style="text-align: center;">Table 1: Dataset Statistics for each task from Proactive-VideoQA.</div>


#### 4.1.2 Question and Answers in ProactiveVideoQA

For Shot2story-MAGQA-39k and TVQA, questions, answers, and relevant timespans are already provided, we directly use these annotations as model input. For Ego4D Goalstep only dense video descriptions are provided, to create questions and answers we follow the pipeline of (Wang et al., 2024) to generate QAs from dense captions. For the [VAD] task, as UCF-Crime only contains timespans but not the textual descriptions of the anomaly event, we manually write a description for each anomaly event as the answer and use “What suspicious or harmful activities, including unlawful, criminal behaviors or destructive accidents, are happening in the video?” as the question. For all datasets, if two consecutive ground truth turns have similar textual contents (judged by LLM and text overlap) and the interval between their reply timespans is less than 3 seconds, we merge them into one ground truth turn, as the two scenes are likely describing the same action.

## 5 Employing Offline Video-Text LLMs for Proactive Interaction

To the best of our knowledge, as of the writing of this manuscript, only two video-text LLMs designed for proactive interaction, VideoLLM Online (Chen et al., 2024a) and MMDuet (Wang et al., 2024), have fully open-sourced their code to support proactive evaluation. To enable the evaluation of a broader set of models on ProactiveVideoQA, we employ a simple rule-based strategy to adapt offline video-text LLMs for proactive interaction. Specifically, we segment each video into fixed-length chunks and, at each timestep, provide the model with the current video chunk, the associated question, and the model's previous response as input. The model is first required to determine whether the current video chunk can answer the question, and output one of the following: "I have no answer," "I have the same answer" (as the previous response), or "I have a new answer." If the model responds with "I have a new answer," it is then required to generate the updated response accordingly. In practice, we find that only proprietary models are capable of reliably following these multi-step instructions. Open-source models, by contrast, typically fail to comply and result in unexpected behaviors (e.g., ignore the instructions and start answering questions directly). Consequently, for open-source models, we adopt a simplified strategy: each video chunk is presented to the model alongside the question, and the model is asked to determine whether the chunk contains sufficient information to answer the question. If the model

6


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Benchmark</td><td style='text-align: center; word-wrap: break-word;'>Modalities</td><td style='text-align: center; word-wrap: break-word;'>#Videos</td><td style='text-align: center; word-wrap: break-word;'>#Questions</td><td style='text-align: center; word-wrap: break-word;'>Multi-Answer</td><td style='text-align: center; word-wrap: break-word;'>Open-Ended</td><td style='text-align: center; word-wrap: break-word;'>Proactive</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MVBench (Li et al., 2023b)</td><td style='text-align: center; word-wrap: break-word;'>Video</td><td style='text-align: center; word-wrap: break-word;'>3,641</td><td style='text-align: center; word-wrap: break-word;'>4,000</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoMME (Fu et al., 2024)</td><td style='text-align: center; word-wrap: break-word;'>Video, Audio</td><td style='text-align: center; word-wrap: break-word;'>900</td><td style='text-align: center; word-wrap: break-word;'>2,700</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>OmniBench (Li et al., 2024d)</td><td style='text-align: center; word-wrap: break-word;'>Image, Audio</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>1,142</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>OVO-Bench (Li et al., 2025)</td><td style='text-align: center; word-wrap: break-word;'>Video</td><td style='text-align: center; word-wrap: break-word;'>644</td><td style='text-align: center; word-wrap: break-word;'>2,814</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓ $ ^{{*}} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>StreamingBench (Lin et al., 2024)</td><td style='text-align: center; word-wrap: break-word;'>Video, Audio</td><td style='text-align: center; word-wrap: break-word;'>900</td><td style='text-align: center; word-wrap: break-word;'>4,500</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓ $ ^{{*}} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>OmniMMI (Wang et al., 2025)</td><td style='text-align: center; word-wrap: break-word;'>Video, Audio</td><td style='text-align: center; word-wrap: break-word;'>1,121</td><td style='text-align: center; word-wrap: break-word;'>2,290</td><td style='text-align: center; word-wrap: break-word;'>✓ $ ^{{*}} $</td><td style='text-align: center; word-wrap: break-word;'>✓ $ ^{{*}} $</td><td style='text-align: center; word-wrap: break-word;'>✓ $ ^{{*}} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ProactiveVideoQA (Ours)</td><td style='text-align: center; word-wrap: break-word;'>Video, Audio</td><td style='text-align: center; word-wrap: break-word;'>1,377</td><td style='text-align: center; word-wrap: break-word;'>1,427</td><td style='text-align: center; word-wrap: break-word;'>✓ $ ^{{*}} $</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td></tr></table>

<div style="text-align: center;">Table 2: Comparison with existing Video Benchmarks.  $ \checkmark $*: True for some of the sub-tasks in the benchmark</div>


responds affirmatively, we perform an additional round of inference to obtain the answer based on the current chunk.

We also explored alternative strategies for adapting offline models to proactive interaction, such as incrementally increasing the number of video chunks provided as input. However, these approaches did not yield satisfactory results. This highlights the significant challenges involved in applying existing offline video-text MLLMs to proactive interaction without targeted training. Further exploration in this direction, such as leveraging agent-based systems, remains an important direction for future research. In this paper, we present only a subset of possible solutions based on our current understanding. Additional experimental details can be found in the Appendix.

## 6 Experiments

We report PAUC metric on ProactiveVideoQA for the following methods: (1) proprietary offline video MLLMs, (2) open-sourced offline video MLLMs, (3) open-sourced proactive video MLLMs, and (4) human performance.

For offline models, we use a video chunk size of 2 seconds for [WEB] and 5 seconds for other datasets. We sample 2 frames per second for [WEB] and 1 frame per second for other datasets. For the baseline models that do not accept audio input, for the [TV] task we input the text-form subtitles to the model at the beginning timestamp of an utterance in the TV Series. For human performance, we recruit 4 human annotators, instruct them to read the question before watching the video, pause the video every time when it plays to the segment where the question can be answered, and write down the current video timestamp along with an answer. Since completing this task manually is very labor-intensive, we only sampled 60 videos from each dataset to evaluate human performance.



### 6.1 Main Results

The results are listed in Table 3. We have the following observations:

(1) Human performance is relatively low, largely due to the demanding nature of the task. Annotators are required to pause the video and write responses precisely when answer-relevant segments appear, which is both cumbersome and unnatural. In practice, many annotators tend to provide responses retrospectively, sometimes even after the relevant reply timespan has passed, rather than offering a brief, timely response followed by iterative refinements, as the model is designed to do, despite explicit instructions to the contrary. Moreover, certain dataset characteristics further increase the difficulty for human annotators. For example, the reply timespan in [WEB] are typically short, while the [EGO] dataset contains a large number of ground-truth turns per video, making it challenging to label answers accurately and in detail. Finally, since the annotators are not native English speakers, the annotation process was conducted in Chinese with back-and-forth translation. This additional step may have introduced translation-related ambiguities or delays, contributing to further degradation in human performance.

(2) On [TV] and [VAD] tasks, proprietary models significantly outperform both open-source and proactive models. This performance gap can be attributed to the complexity of these tasks, which require deep understanding of video content, such as character relationships and subtitles in [TV], or perceptually demanding surveillance footage in [VAD]. In contrast, the advantage of proprietary models is less evident on the [WEB] and [EGO] tasks. In these benchmarks, the core challenge lies in accurately determining the timing of responses, a capability

7


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Model</td><td colspan="3">[WEB]</td><td colspan="3">[EGO]</td><td colspan="3">[TV]</td><td colspan="3">[VAD]</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ \omega = $</td><td style='text-align: center; word-wrap: break-word;'>0.0</td><td style='text-align: center; word-wrap: break-word;'>0.5</td><td style='text-align: center; word-wrap: break-word;'>1.0</td><td style='text-align: center; word-wrap: break-word;'>0.0</td><td style='text-align: center; word-wrap: break-word;'>0.5</td><td style='text-align: center; word-wrap: break-word;'>1.0</td><td style='text-align: center; word-wrap: break-word;'>0.0</td><td style='text-align: center; word-wrap: break-word;'>0.5</td><td style='text-align: center; word-wrap: break-word;'>1.0</td><td style='text-align: center; word-wrap: break-word;'>0.0</td><td style='text-align: center; word-wrap: break-word;'>0.5</td><td style='text-align: center; word-wrap: break-word;'>1.0</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Human</td><td style='text-align: center; word-wrap: break-word;'>36.5</td><td style='text-align: center; word-wrap: break-word;'>38.6</td><td style='text-align: center; word-wrap: break-word;'>40.7</td><td style='text-align: center; word-wrap: break-word;'>35.0</td><td style='text-align: center; word-wrap: break-word;'>38.2</td><td style='text-align: center; word-wrap: break-word;'>41.3</td><td style='text-align: center; word-wrap: break-word;'>38.1</td><td style='text-align: center; word-wrap: break-word;'>47.0</td><td style='text-align: center; word-wrap: break-word;'>55.9</td><td style='text-align: center; word-wrap: break-word;'>47.4</td><td style='text-align: center; word-wrap: break-word;'>53.6</td><td style='text-align: center; word-wrap: break-word;'>59.8</td></tr><tr><td colspan="13">Proprietary Offline Models</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>GPT-4.1</td><td style='text-align: center; word-wrap: break-word;'>44.6</td><td style='text-align: center; word-wrap: break-word;'>51.7</td><td style='text-align: center; word-wrap: break-word;'>58.9</td><td style='text-align: center; word-wrap: break-word;'>53.6</td><td style='text-align: center; word-wrap: break-word;'>58.8</td><td style='text-align: center; word-wrap: break-word;'>64.0</td><td style='text-align: center; word-wrap: break-word;'>45.0</td><td style='text-align: center; word-wrap: break-word;'>56.8</td><td style='text-align: center; word-wrap: break-word;'>68.5</td><td style='text-align: center; word-wrap: break-word;'>40.8</td><td style='text-align: center; word-wrap: break-word;'>46.2</td><td style='text-align: center; word-wrap: break-word;'>51.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>GPT-4.1-mini</td><td style='text-align: center; word-wrap: break-word;'>41.2</td><td style='text-align: center; word-wrap: break-word;'>47.8</td><td style='text-align: center; word-wrap: break-word;'>54.5</td><td style='text-align: center; word-wrap: break-word;'>59.1</td><td style='text-align: center; word-wrap: break-word;'>65.8</td><td style='text-align: center; word-wrap: break-word;'>72.5</td><td style='text-align: center; word-wrap: break-word;'>48.5</td><td style='text-align: center; word-wrap: break-word;'>59.4</td><td style='text-align: center; word-wrap: break-word;'>70.3</td><td style='text-align: center; word-wrap: break-word;'>41.4</td><td style='text-align: center; word-wrap: break-word;'>47.7</td><td style='text-align: center; word-wrap: break-word;'>54.0</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Gemini-1.5-pro</td><td style='text-align: center; word-wrap: break-word;'>37.1</td><td style='text-align: center; word-wrap: break-word;'>42.1</td><td style='text-align: center; word-wrap: break-word;'>47.0</td><td style='text-align: center; word-wrap: break-word;'>47.0</td><td style='text-align: center; word-wrap: break-word;'>49.7</td><td style='text-align: center; word-wrap: break-word;'>52.4</td><td style='text-align: center; word-wrap: break-word;'>41.7</td><td style='text-align: center; word-wrap: break-word;'>52.0</td><td style='text-align: center; word-wrap: break-word;'>62.4</td><td style='text-align: center; word-wrap: break-word;'>34.3</td><td style='text-align: center; word-wrap: break-word;'>36.1</td><td style='text-align: center; word-wrap: break-word;'>37.9</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Gemini-2.0-flash</td><td style='text-align: center; word-wrap: break-word;'>36.1</td><td style='text-align: center; word-wrap: break-word;'>41.0</td><td style='text-align: center; word-wrap: break-word;'>45.9</td><td style='text-align: center; word-wrap: break-word;'>49.4</td><td style='text-align: center; word-wrap: break-word;'>53.7</td><td style='text-align: center; word-wrap: break-word;'>57.9</td><td style='text-align: center; word-wrap: break-word;'>40.4</td><td style='text-align: center; word-wrap: break-word;'>49.1</td><td style='text-align: center; word-wrap: break-word;'>57.8</td><td style='text-align: center; word-wrap: break-word;'>32.9</td><td style='text-align: center; word-wrap: break-word;'>35.8</td><td style='text-align: center; word-wrap: break-word;'>38.6</td></tr><tr><td colspan="13">Open-Sourced Offline Models</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>InternVL-2.5 8B</td><td style='text-align: center; word-wrap: break-word;'>41.6</td><td style='text-align: center; word-wrap: break-word;'>48.2</td><td style='text-align: center; word-wrap: break-word;'>54.9</td><td style='text-align: center; word-wrap: break-word;'>52.1</td><td style='text-align: center; word-wrap: break-word;'>57.8</td><td style='text-align: center; word-wrap: break-word;'>63.6</td><td style='text-align: center; word-wrap: break-word;'>36.5</td><td style='text-align: center; word-wrap: break-word;'>41.5</td><td style='text-align: center; word-wrap: break-word;'>46.6</td><td style='text-align: center; word-wrap: break-word;'>22.2</td><td style='text-align: center; word-wrap: break-word;'>21.5</td><td style='text-align: center; word-wrap: break-word;'>20.8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-OV 7B</td><td style='text-align: center; word-wrap: break-word;'>46.6</td><td style='text-align: center; word-wrap: break-word;'>55.0</td><td style='text-align: center; word-wrap: break-word;'>63.4</td><td style='text-align: center; word-wrap: break-word;'>57.0</td><td style='text-align: center; word-wrap: break-word;'>61.6</td><td style='text-align: center; word-wrap: break-word;'>66.1</td><td style='text-align: center; word-wrap: break-word;'>38.2</td><td style='text-align: center; word-wrap: break-word;'>45.1</td><td style='text-align: center; word-wrap: break-word;'>51.9</td><td style='text-align: center; word-wrap: break-word;'>25.3</td><td style='text-align: center; word-wrap: break-word;'>25.6</td><td style='text-align: center; word-wrap: break-word;'>25.9</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LongVA 7B</td><td style='text-align: center; word-wrap: break-word;'>39.3</td><td style='text-align: center; word-wrap: break-word;'>47.2</td><td style='text-align: center; word-wrap: break-word;'>55.1</td><td style='text-align: center; word-wrap: break-word;'>34.5</td><td style='text-align: center; word-wrap: break-word;'>37.4</td><td style='text-align: center; word-wrap: break-word;'>40.2</td><td style='text-align: center; word-wrap: break-word;'>35.3</td><td style='text-align: center; word-wrap: break-word;'>41.5</td><td style='text-align: center; word-wrap: break-word;'>47.6</td><td style='text-align: center; word-wrap: break-word;'>27.2</td><td style='text-align: center; word-wrap: break-word;'>29.8</td><td style='text-align: center; word-wrap: break-word;'>32.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-VL 7B</td><td style='text-align: center; word-wrap: break-word;'>45.7</td><td style='text-align: center; word-wrap: break-word;'>52.7</td><td style='text-align: center; word-wrap: break-word;'>59.8</td><td style='text-align: center; word-wrap: break-word;'>42.8</td><td style='text-align: center; word-wrap: break-word;'>46.5</td><td style='text-align: center; word-wrap: break-word;'>50.3</td><td style='text-align: center; word-wrap: break-word;'>32.7</td><td style='text-align: center; word-wrap: break-word;'>36.5</td><td style='text-align: center; word-wrap: break-word;'>40.2</td><td style='text-align: center; word-wrap: break-word;'>27.9</td><td style='text-align: center; word-wrap: break-word;'>29.3</td><td style='text-align: center; word-wrap: break-word;'>30.7</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>IXC-2.5 7B</td><td style='text-align: center; word-wrap: break-word;'>43.0</td><td style='text-align: center; word-wrap: break-word;'>50.3</td><td style='text-align: center; word-wrap: break-word;'>57.6</td><td style='text-align: center; word-wrap: break-word;'>43.0</td><td style='text-align: center; word-wrap: break-word;'>50.3</td><td style='text-align: center; word-wrap: break-word;'>57.6</td><td style='text-align: center; word-wrap: break-word;'>41.0</td><td style='text-align: center; word-wrap: break-word;'>48.5</td><td style='text-align: center; word-wrap: break-word;'>56.0</td><td style='text-align: center; word-wrap: break-word;'>25.4</td><td style='text-align: center; word-wrap: break-word;'>26.8</td><td style='text-align: center; word-wrap: break-word;'>28.3</td></tr><tr><td colspan="13">Proactive Models</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MMDuet</td><td style='text-align: center; word-wrap: break-word;'>37.2</td><td style='text-align: center; word-wrap: break-word;'>38.9</td><td style='text-align: center; word-wrap: break-word;'>40.7</td><td style='text-align: center; word-wrap: break-word;'>44.0</td><td style='text-align: center; word-wrap: break-word;'>46.0</td><td style='text-align: center; word-wrap: break-word;'>47.9</td><td style='text-align: center; word-wrap: break-word;'>20.7</td><td style='text-align: center; word-wrap: break-word;'>21.1</td><td style='text-align: center; word-wrap: break-word;'>21.6</td><td style='text-align: center; word-wrap: break-word;'>26.4</td><td style='text-align: center; word-wrap: break-word;'>27.4</td><td style='text-align: center; word-wrap: break-word;'>28.5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MMDuet+rm.ass.turns</td><td style='text-align: center; word-wrap: break-word;'>41.4</td><td style='text-align: center; word-wrap: break-word;'>43.5</td><td style='text-align: center; word-wrap: break-word;'>45.6</td><td style='text-align: center; word-wrap: break-word;'>49.4</td><td style='text-align: center; word-wrap: break-word;'>52.2</td><td style='text-align: center; word-wrap: break-word;'>55.0</td><td style='text-align: center; word-wrap: break-word;'>28.2</td><td style='text-align: center; word-wrap: break-word;'>32.6</td><td style='text-align: center; word-wrap: break-word;'>37.1</td><td style='text-align: center; word-wrap: break-word;'>38.5</td><td style='text-align: center; word-wrap: break-word;'>42.5</td><td style='text-align: center; word-wrap: break-word;'>46.5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLM-Online</td><td style='text-align: center; word-wrap: break-word;'>25.9</td><td style='text-align: center; word-wrap: break-word;'>25.9</td><td style='text-align: center; word-wrap: break-word;'>25.9</td><td style='text-align: center; word-wrap: break-word;'>25.0</td><td style='text-align: center; word-wrap: break-word;'>25.0</td><td style='text-align: center; word-wrap: break-word;'>25.1</td><td style='text-align: center; word-wrap: break-word;'>17.8</td><td style='text-align: center; word-wrap: break-word;'>18.3</td><td style='text-align: center; word-wrap: break-word;'>18.8</td><td style='text-align: center; word-wrap: break-word;'>25.0</td><td style='text-align: center; word-wrap: break-word;'>25.0</td><td style='text-align: center; word-wrap: break-word;'>25.0</td></tr></table>

<div style="text-align: center;">Table 3: Results on ProactiveVideoQA with different  $ \omega $.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Task</td><td colspan="3">Agreement w/ Human</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ \omega = 1 $</td><td style='text-align: center; word-wrap: break-word;'>$ \omega = 0.5 $</td><td style='text-align: center; word-wrap: break-word;'>Human</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>[WEB]</td><td style='text-align: center; word-wrap: break-word;'>0.23/0.30</td><td style='text-align: center; word-wrap: break-word;'>0.37/0.40</td><td style='text-align: center; word-wrap: break-word;'>0.50/0.49</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>[EGO]</td><td style='text-align: center; word-wrap: break-word;'>0.26/0.32</td><td style='text-align: center; word-wrap: break-word;'>0.30/0.35</td><td style='text-align: center; word-wrap: break-word;'>0.34/0.31</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>[TV]</td><td style='text-align: center; word-wrap: break-word;'>0.29/0.37</td><td style='text-align: center; word-wrap: break-word;'>0.34/0.37</td><td style='text-align: center; word-wrap: break-word;'>0.55/0.59</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>[VAD]</td><td style='text-align: center; word-wrap: break-word;'>0.31/0.36</td><td style='text-align: center; word-wrap: break-word;'>0.45/0.49</td><td style='text-align: center; word-wrap: break-word;'>0.40/0.51</td></tr></table>

<div style="text-align: center;">Table 4: Agreement between human preference and PAUC  $ \omega = 1 $ (baseline metric without taking reply time into account), and PAUC  $ \omega = 0.5 $ (taking reply time into account). We also report the agreement between 2 different sets of annotators as a reference. The agreement metrics reported are Cohen's kappa with no-weighting/linear-weighting (Cohen, 1960)</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Model</td><td style='text-align: center; word-wrap: break-word;'>[WEB]</td><td style='text-align: center; word-wrap: break-word;'>[EGO]</td><td style='text-align: center; word-wrap: break-word;'>[TV]</td><td style='text-align: center; word-wrap: break-word;'>[VAD]</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MMDuet</td><td style='text-align: center; word-wrap: break-word;'>81.3</td><td style='text-align: center; word-wrap: break-word;'>99.4</td><td style='text-align: center; word-wrap: break-word;'>92.8</td><td style='text-align: center; word-wrap: break-word;'>99.2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MMDuet w/ rm. ass. turns</td><td style='text-align: center; word-wrap: break-word;'>81.1</td><td style='text-align: center; word-wrap: break-word;'>92.6</td><td style='text-align: center; word-wrap: break-word;'>61.2</td><td style='text-align: center; word-wrap: break-word;'>80.9</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLM- Online $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>53.9</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr></table>

<div style="text-align: center;">Table 5: The proportion of duplicate pred turns to all pred turns (excluding the first pred turn in each ground-truth answer turn). †: Videollm-online generated more than 1 reply for only less than 10 answer turns on the [WEB], [EGO], and [VAD] datasets. Since the sample size is too small, we are not reporting this result as they have overly-large variance.</div>


that remains underdeveloped across all models, including those explicitly designed for proactive interaction.

(3) Proactive models do not demonstrate better results than offline models. This is because although these models can theoretically make decisions on response timing, due by relatively simple training techniques and limited training resources, their performance is not satisfactory. Our further analysis in Table 5 confirms that these models tend to repeat previously generated content, leading to lower response quality.

### 6.2 Alignment with Human Preferences

To validate the effectiveness of the proposed PAUC metric, we conduct a human study to assess its agreement with human preferences at ground-truth reply turn level. Specifically, we sample 100 ground-truth reply turns from each task (and 50 answer turns from [VAD]), due to its smaller dataset size), and collect two model predictions per sample using the Incremental Chunks method from GPT-4.1-mini and Gemini-2.0-Flash. Human annotators are then asked to indicate their preference between the two predictions (one model prediction wins or draws). To ensure the informativeness of the evaluated responses, we apply the following sampling criteria: (1) both models must produce at least one response within the reply span, and at least one of them must respond in more than one round; and (2)

8

both models must have at least one response with a PAUC score greater than 0.

Annotators are instructed to assume the role of users seeking timely and accurate information from the video. They are asked to judge which model prediction better captures the information present in the ground truth at earlier timestamps, while also considering text quality (e.g., avoiding hallucinations and maintaining fluency). To assess inter-annotator consistency, 50 examples for each task are annotated twice independently by two different annotators. The results are presented in Table 4. Compared to the baseline metric that does not account for reply timing ( $ \omega = 1 $), the proposed PAUC metric which incorporates reply time with  $ \omega = 0.5 $ consistently exhibits stronger alignment with human preferences and approaches the level of agreement observed between human annotators.

Nonetheless, all Cohen's kappa scores, including the agreement between human annotators, are relatively low. Several factors contribute to this outcome: (1) the trade-off between correctness and timeliness is inherently subjective, and it is natural for different individuals to prioritize these aspects differently; and (2) the examples selected for human preference annotation represent the more complex cases. Compared to easier instances where one model's response clearly outperforms the other's, focusing on these borderline cases provides a more effective test of the proposed PAUC metric.

To intuitively demonstrate the advantages of PAUC compared to the baseline metric on the addition of temporal changes, we present several examples as case study in the appendix.

## 7 Conclusion

In this work, we address the emerging challenge of evaluating proactive multimodal dialogue systems by introducing ProactiveVideoQA, the first comprehensive benchmark for assessing systems' capabilities in proactive interaction scenarios. We propose PAUC, a novel evaluation metric that tracks how the quality of a model's responses evolves throughout the video, as a more valid metric to evaluate models for proactive interaction. We believe that ProactiveVideoQA and PAUC will serve as valuable tools for future research and development in proactive interaction models that can have potentially high-impact application areas such as live stream understanding, video anomaly detection, and ego-centric agents.

## References

Shuai Bai, Keqin Chen, Xuejing Liu, Jialin Wang, Wenbin Ge, Sibo Song, Kai Dang, Peng Wang, Shijie Wang, Jun Tang, Humen Zhong, Yuanzhi Zhu, Mingkun Yang, Zhaohai Li, Jianqiang Wan, Pengfei Wang, Wei Ding, Zheren Fu, Yiheng Xu, Jiabo Ye, Xi Zhang, Tianbao Xie, Zesen Cheng, Hang Zhang, Zhibo Yang, Haiyang Xu, and Junyang Lin. 2025. Qwen2.5-vl technical report. ArXiv, abs/2502.13923.

Mu Cai, Reuben Tan, Jianrui Zhang, Bocheng Zou, Kai Zhang, Feng Yao, Fangrui Zhu, Jing Gu, Yiwu Zhong, Yuzhang Shang, Yao Dou, Jaden Park, Jianfeng Gao, Yong Jae Lee, and Jianwei Yang. 2024. Temporal bench: Benchmarking fine-grained temporal understanding for multimodal video models. ArXiv, abs/2410.10818.

Joya Chen, Zhaoyang Lv, Shiwei Wu, Kevin Qinghong Lin, Chenan Song, Difei Gao, Jia-Wei Liu, Ziteng Gao, Dongxing Mao, and Mike Zheng Shou. 2024a. Videoollm-online: Online video large language model for streaming video. 2024 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), pages 18407–18418.

Zhe Chen, Weiyun Wang, Yue Cao, Yangzhou Liu, Zhangwei Gao, Erfei Cui, Jinguo Zhu, Shenglong Ye, Hao Tian, Zhaoyang Liu, Lixin Gu, Xuehui Wang, Qingyun Li, Yiming Ren, Zixuan Chen, Jiapeng Luo, Jiahao Wang, Tan Jiang, Bo Wang, Conghui He, Botian Shi, Xingcheng Zhang, Han Lv, Yi Wang, Wenqi Shao, Pei Chu, Zhongying Tu, Tong He, Zhiyong Wu, Hui Deng, Jiaye Ge, Kaiming Chen, Min Dou, Lewei Lu, Xizhou Zhu, Tong Lu, Dahu Lin, Yunfeng Qiao, Jifeng Dai, and Wenhai Wang. 2024b. Expanding performance boundaries of open-source multimodal models with model, data, and test-time scaling. ArXiv, abs/2412.05271.

Jacob Cohen. 1960. A coefficient of agreement for nominal scales. Educational and Psychological Measurement, 20:37–46.

Xinyu Fang, Kangrui Mao, Haodong Duan, Xiangyu Zhao, Yining Li, Dahua Lin, and Kai Chen. 2024. Mmbench-video: A long-form multi-shot benchmark for holistic video understanding. ArXiv, abs/2406.14515.

Chaoyou Fu, Yuhan Dai, Yondong Luo, Lei Li, Shuhui Ren, Renrui Zhang, Zihan Wang, Chenyu Zhou, Yunhang Shen, Mengdan Zhang, Peixian Chen, Yanwei Li, Shaohui Lin, Sirui Zhao, Ke Li, Tong Xu, Xiawu Zheng, Enhong Chen, Rongrong Ji, and Xing Sun. 2024. Video-mme: The first-ever comprehensive evaluation benchmark of multi-modal llms in video analysis. ArXiv, abs/2405.21075.

Mingfei Han, Linjie Yang, Xiaojun Chang, and Heng Wang. 2023. Shot2story: A new benchmark for comprehensive understanding of multi-shot videos.

Faren Huo, Yeying Zhao, Chunlei Chai, and Fei Fang. 2023. A user experience map design method based

9

on emotional quantification of in-vehicle hmi. Humanities and Social Sciences Communications, 10:1–10.

Jie Lei, Licheng Yu, Mohit Bansal, and Tamara L. Berg. 2018. Tvqa: Localized, compositional video question answering. In Conference on Empirical Methods in Natural Language Processing.

Bo Li, Yuanhan Zhang, Dong Guo, Renrui Zhang, Feng Li, Hao Zhang, Kaichen Zhang, Yanwei Li, Ziwei Liu, and Chunyuan Li. 2024a. Llava-onevision: Easy visual task transfer. ArXiv, abs/2408.03326.

Bohao Li, Yuying Ge, Yi Chen, Yixiao Ge, Ruimao Zhang, and Ying Shan. 2024b. Seed-bench-2-plus: Benchmarking multimodal large language models with text-rich visual comprehension. ArXiv, abs/2404.16790.

Bohao Li, Rui Wang, Guangzhi Wang, Yuying Ge, Yixiao Ge, and Ying Shan. 2023a. Seed-bench: Benchmarking multimodal llms with generative comprehension. ArXiv, abs/2307.16125.

Haitao Li, Qian Dong, Junjie Chen, Huixue Su, Yujia Zhou, Qingyao Ai, Ziyi Ye, and Yiqun Liu. 2024c. Llms-as-judges: A comprehensive survey on llm-based evaluation methods. ArXiv, abs/2412.05579.

Kunchang Li, Yali Wang, Yinan He, Yizhuo Li, Yi Wang, Yi Liu, Zun Wang, Jilan Xu, Guo Chen, Ping Luo, Limin Wang, and Yu Qiao. 2023b. Mvbench: A comprehensive multi-modal video understanding benchmark. 2024 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), pages 22195–22206.

Shicheng Li, Lei Li, Shuhuai Ren, Yuanxin Liu, Yi Liu, Rundong Gao, Xu Sun, and Lu Hou. 2023c. Vitatecs: A diagnostic dataset for temporal concept understanding of video-language models. In European Conference on Computer Vision.

Yifei Li, Junbo Niu, Ziyang Miao, Chunjiang Ge, Yuanhang Zhou, Qihao He, Xiao wen Dong, Haodong Duan, Shuangrui Ding, Rui Qian, Pan Zhang, Yuhang Zang, Yuhang Cao, Conghui He, and Jiaqi Wang. 2025. Ovo-bench: How far is your video-llms from real-world online video understanding? ArXiv, abs/2501.05510.

Yizhi Li, Ge Zhang, Yi Ma, Ruibin Yuan, Kang Zhu, Hangyu Guo, Yiming Liang, Jiaheng Liu, Jian Yang, Siwei Wu, Xingwei Qu, Jinjie Shi, Xinyue Zhang, Zhen Yang, Xiangzhou Wang, Zhaoxiang Zhang, Zachary Liu, Emmanouil Benetos, Wenhao Huang, and Chenghua Lin. 2024d. Omnibench: Towards the future of universal omni-language models. ArXiv, abs/2409.15272.

Junming Lin, Zheng Fang, Chi Chen, Zihao Wan, Fuwen Luo, Peng Li, Yang Liu, and Maosong Sun. 2024. Streamingbench: Assessing the gap for mlms to achieve streaming video understanding. ArXiv, abs/2411.03628.

Ye Liu, Zongyang Ma, Zhongang Qi, Yang Wu, Ying Shan, and Chang Wen Chen. 2024. E.t. bench: Towards open-ended event-level video-language understanding. Preprint, arXiv:2409.18111.

Kishore Papineni, Salim Roukos, Todd Ward, and Wei-Jing Zhu. 2002. Bleu: a method for automatic evaluation of machine translation. In Annual Meeting of the Association for Computational Linguistics.

Rui Qian, Shuangrui Ding, Xiao wen Dong, Pan Zhang, Yuhang Zang, Yuhang Cao, Dahua Lin, and Jiaqi Wang. 2025. Dispider: Enabling video llms with active real-time interaction via disentangled perception, decision, and reaction. ArXiv, abs/2501.03218.

Yale Song, Eugene Byrne, Tushar Nagarajan, Huiyu Wang, Miguel Martin, and Lorenzo Torresani. 2023. Ego4d goal-step: Toward hierarchical understanding of procedural activities. In Neural Information Processing Systems.

Waqas Sultani, Chen Chen, and Mubarak Shah. 2018. Real-world anomaly detection in surveillance videos. 2018 IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 6479–6488.

Ramakrishna Vedantam, C. Lawrence Zitnick, and Devi Parikh. 2014. Cider: Consensus-based image description evaluation. 2015 IEEE Conference on Computer Vision and Pattern Recognition (CVPR), pages 4566–4575.

Yueqian Wang, Xiaojun Meng, Yuxuan Wang, Jianxin Liang, Jiansheng Wei, Huishuai Zhang, and Dongyan Zhao. 2024. VideoIIM knows when to speak: Enhancing time-sensitive video comprehension with video-text duet interaction format. ArXiv, abs/2411.17991.

Yuxuan Wang, Yueqian Wang, Bo Chen, Tong Wu, Dongyan Zhao, and Zilong Zheng. 2025. Omnimmi: A comprehensive multi-modal interaction benchmark in streaming video contexts. ArXiv, abs/2503.22952.

Jin Xu, Zhifang Guo, Jinzheng He, Hangrui Hu, Ting He, Shuai Bai, Keqin Chen, Jialin Wang, Yang Fan, Kai Dang, Bin Zhang, Xiong Wang, Yunfei Chu, and Junyang Lin. 2025. Qwen2.5-omni technical report. ArXiv, abs/2503.20215.

Linli Yao, Yicheng Li, Yuancheng Wei, Lei Li, Shuhuai Ren, Yuanxin Liu, Kun Ouyang, Lean Wang, Shicheng Li, Sida Li, Lingpeng Kong, Qi Liu, Yuanxing Zhang, and Xu Sun. 2025. Timechat-online: 80% visual tokens are naturally redundant in streaming videos. ArXiv, abs/2504.17343.

Tongtong Yuan, Xuange Zhang, Kun Liu, Bo Liu, Chen Chen, Jian Jin, and Zhenzhen Jiao. 2023. Towards surveillance video-and-language understanding: New dataset, baselines, and challenges. 2024 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), pages 22052–22061.

10

Pan Zhang, Xiao wen Dong, Yuhang Zang, Yuhang Cao, Rui Qian, Lin Chen, Qipeng Guo, Haodong Duan, Bin Wang, Linke Ouyang, Songyang Zhang, Wenwei Zhang, Yining Li, Yang Gao, Peng Sun, Xinyue Zhang, Wei Li, Jingwen Li, Wenhai Wang, Hang Yan, Conghui He, Xingcheng Zhang, Kai Chen, Jifeng Dai, Yu Qiao, Dahua Lin, and Jiaqi Wang. 2024a. Internlm-xcomposer-2.5: A versatile large vision language model supporting long-contextual input and output. ArXiv, abs/2407.03320.

Peiyuan Zhang, Kaichen Zhang, Bo Li, Guangtao Zeng, Jingkang Yang, Yuanhan Zhang, Ziyue Wang, Haoran Tan, Chunyuan Li, and Ziwei Liu. 2024b. Long context transfer from language to vision. ArXiv, abs/2406.16852.

Tianyi Zhang, Varsha Kishore, Felix Wu, Kilian Q. Weinberger, and Yoav Artzi. 2019. Bertscore: Evaluating text generation with bert. ArXiv, abs/1904.09675.

### A More approaches Evaluating Offline Models

### A.1 Gradually Increasing Number of Chunks

We also experimented with a very intuitive and efficient method for using offline models for proactive interaction: during the  $ n^{th} $ round of interaction, we input the first n video chunks along with all the model's prior responses from the previous n-1 rounds but remove the final EOS token, and observe whether the model would continue generating. If the model generates some new text (considering that existing outputs were generated conditioning on the previous n-1 video chunks), we could attribute this new content to the inclusion of the  $ n^{th} $ chunk and thus treat it as the model's response at the end time of the  $ n^{th} $ video chunk. However, in our experiments we found that in almost all cases existing open-source models only generate answers in the first interaction round for each video. In subsequent rounds the models almost never extended their output and simply emitted an EOS token to end their turn instead. We speculate that the underlying reason is in proactive interaction, whether the model should initiate a response is largely determined by the newly added video segment, and current open-source models were not trained for this.

### B Case Study

To intuitively demonstrate the advantages of PAUC compared to the baseline metric that does not account for temporal changes, here we present 2 real examples tested on GPT-4.1-mini and Gemini-2.0-flash. Since the scores are counted independently in each ground truth span, and also to simplify the information for easier display, Each example shows a case from one ground truth reply span within an example.



In the first example, Gemini-2.0-Flash responded faster and covered more key information in the ground truth answer, thus reaching the maximum score of 2 as early as 10 seconds. This gives it an advantage over GPT-4.1-mini in the final PAUC evaluation.

The second example is a more representative case where PAUC is better than time-agnostic baseline metrics for evaluating proactive systems. Both models eventually answered "stealing items", which would yield equal scores under a time-agnostic metric. However, Gemini-2.0-Flash correctly provided this information earlier at 20s and gained 1 point, while GPT-4.1-mini gave an incorrect response at the same timestamp and received 0 points. This results in a significantly higher PAUC score for the Gemini-2.0-Flash.

11

<div style="text-align: center;"><img src="imgs/img_in_image_box_144_434_571_487.jpg" alt="Image" width="35%" />

8s 10s 12s

</div>


##### Question: What is being done with the white stuff?

Ground Truth: A person is preparing to pour the white stuff from a clear container into a tub.

GPT-4.1-mini

[10s] The  $ \underline{\text{white stuff}} $ is being stirred with a red spatula.

[12s] The white stuff  $ \underline{\text{is being poured.}} $

Gemini-2.0-flash

[10s] The white stuff, which looks like a creamy or dairy product, is being stirred with a red spatula and poured into a larger yellow bowl.

<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Score</th><th style='text-align: center;'>8s</th><th style='text-align: center;'>10s</th><th style='text-align: center;'>12s</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>1</td><td style='text-align: center;'>2</td><td style='text-align: center;'>1</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>3</td><td style='text-align: center;'>2</td><td style='text-align: center;'>1</td><td style='text-align: center;'>2</td></tr>
    <tr><td style='text-align: center;'>5</td><td style='text-align: center;'>2</td><td style='text-align: center;'>1</td><td style='text-align: center;'>2</td></tr>
  </tbody>
</table>

<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Score</th><th style='text-align: center;'>8s</th><th style='text-align: center;'>10s</th><th style='text-align: center;'>12s</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>2</td><td style='text-align: center;'>8</td><td style='text-align: center;'>10</td><td style='text-align: center;'>12</td></tr>
  </tbody>
</table>

<div style="text-align: center;"><img src="imgs/img_in_image_box_159_706_542_782.jpg" alt="Image" width="32%" />

195 215 235 255

</div>


<div style="text-align: center;">Question: What suspicious or harmful activities, including unlawful, criminal behaviors or destructive accidents, are happening in the video? Ground Truth: The woman in green clothes went out and the other two women took the opportunity to quickly take clothes from the shelves and put them into their bags.</div>


<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Score</th><th style='text-align: center;'>18s</th><th style='text-align: center;'>20s</th><th style='text-align: center;'>25s</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>1</td><td style='text-align: center;'>1</td><td style='text-align: center;'>0</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>2</td><td style='text-align: center;'>0</td><td style='text-align: center;'>1</td><td style='text-align: center;'>0</td></tr>
  </tbody>
</table>

<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Time</th><th style='text-align: center;'>Score</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>18s</td><td style='text-align: center;'>0.5</td></tr>
    <tr><td style='text-align: center;'>20s</td><td style='text-align: center;'>1.1</td></tr>
    <tr><td style='text-align: center;'>12s</td><td style='text-align: center;'>1.1</td></tr>
  </tbody>
</table>

<div style="text-align: center;">Figure 6: Qualitative demonstration of ProactiveVideoQA and PAUC. The first example is from [WEB], and the second example is from [VAD]. The underlined content in the model responses highlights key information (for visualization purposes only, not as part of the evaluation criteria). In the line chart below, each dot represents a model response and its impact on the score poly-line.</div>


12