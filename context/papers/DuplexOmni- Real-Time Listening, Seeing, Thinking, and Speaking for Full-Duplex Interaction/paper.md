arXiv:2606.09186v1 [cs.HC] 8 Jun 2026

# DuplexOmni: Real-Time Listening, Seeing, Thinking, and Speaking for Full-Duplex Interaction

Muye Huang$^{1,2}$, Lingling Zhang$^{1,2,\dagger}$, Xingyu Yu$^{2}$, Lei Shi$^{4}$, Zhanyu Ma$^{4}$, Jun Xu$^{4,\dagger}$, Jiuchong Gao$^{4}$, Jinghua Hao$^{4}$, Renqing He$^{4}$, Jun Liu$^{1,2}$

$^{1}$School of Computer Science and Technology, Xi'an Jiaotong University

$^{2}$MOE KLNN Lab, Xi'an Jiaotong University

$^{3}$School of Software and Microelectronics, Peking University $^{4}$Meituan huangmuye@stu.xjtu.edu.cn$^{\dagger}$Corresponding authors.

## Abstract

Human interaction is continuous, multimodal, and full-duplex by nature. Although recent omni models have made substantial progress in unified speech, vision, and text modeling, combining seamless real-time interaction with complex reasoning and tool use remains challenging. We present DuplexOmni, a method for real-time multimodal full-duplex interaction. DuplexOmni separates model capability into an interaction layer and a thinking layer, which collaborate asynchronously in parallel. The interaction layer is implemented by the DuplexOmni model, an end-to-end system that processes streaming audio and video inputs while generating text and speech responses in real time. The thinking layer is a pluggable module that provides complex reasoning and tool-use capabilities. To support this method, we further develop a Writer-Director pipeline for constructing continuous-interaction training data. Experiments show that DuplexOmni achieves strong performance on multiple public benchmarks and exhibits natural full-duplex interaction ability.

## 1 Introduction

Human interaction is naturally seamless, multimodal, and full-duplex. During communication, people listen to speech, observe the environment, and understand context, while continuing to receive new information as they speak. New information may change subsequent expression or lead to interaction events such as pauses. Therefore, this kind of interaction requires a model to express in real time during continuous perception and to keep updating its understanding during expression.

Recent omni models (OpenAI, 2024; Xu et al., 2025; Yao et al., 2024; Reid et al., 2024) have advanced unified modeling of speech, vision, and text. These models have demonstrated real-time

<div style="text-align: center;"><img src="imgs/img_in_image_box_620_443_1042_928.jpg" alt="Image" width="35%" />

SMART BUT NOT SEAMLESS BLOCKED BY THINKING AND TOOL USE
Let's see where this is!
I'm going to San Diego for a trip. Are there any especially good plans?
Haha, you're in LA — now you want to go have fun in SD, right?
Speech blocked by tool call.
Tool call: go from LA to SD for fun...
SEAMLESS BUT NOT SMART
NO DEEP THINKING OR TOOL USE
I'm going to San Diego for a trip. Are there any especially good plans?
Haha, SD is a great place. You can visit the USS Midway...
Lacks tool-calling capability
SEAMLESS AND SMART
RESPONDING AND THINKING IN PARALLEL
Let's see where this is!
I'm going to San Diego for a trip. Are there any especially good plans?
Haha, let me see — this is LA, right?
Now you want to go have fun in SD?
I'm looking for the best option on websites A, B, C, and D.
Reply instantly and think in parallel.
Tool call: go from LA to SD for fun...
DuplexOmni Thinking

</div>


<div style="text-align: center;">Figure 1: DuplexOmni keeps real-time interaction continuous by decoupling instant responses from asynchronous thinking and tool use.</div>


multimodal understanding and generation. However, existing models still struggle to provide seamless user interaction. As shown in Fig. 1, when interaction involves deep thinking or tool use, the model often pauses the ongoing dialogue. It then waits for reasoning or tool results before continuing its response. This causes clear interruptions. Some methods build lightweight real-time models by reducing model size and simplifying reasoning. However, this weakens or even removes the ability to handle complex tasks. The root cause is that listening, speaking, reasoning, and acting are usually handled within a single serial pipeline. Reasoning and tool use can interrupt real-time interaction, while shortening the reasoning process limits the model's capabilities. Seamless multimodal interaction therefore requires independent execution spaces for real-time interaction and deep reasoning.

1

as well as continuous collaboration throughout the dialogue.

To address this contradiction, we propose DuplexOmni, a method for real-time multimodal interaction that enables seeing, listening, speaking, thinking, and acting to proceed in parallel. Inspired by fast and slow thinking in human cognition, DuplexOmni divides model capabilities into a decoupled interaction layer and thinking layer, and lets them collaborate asynchronously. The interaction layer is handled by the DuplexOmni model, an end-to-end full-duplex model that continuously receives real-time speech, video, and dialogue history, while producing streaming text and speech. The thinking layer provides pluggable deep cognitive capability, and can be instantiated with large language models or tool agents according to the task. The interaction layer maintains low-latency perception and expression, and requests background thinking from the thinking layer when needed. Results returned by the thinking layer are progressively received, organized, and incorporated by the interaction layer into subsequent responses, keeping real-time interaction continuous while giving deep thinking independent computation time.

To realize DuplexOmni, we develop the model, collaboration mechanism, data construction, and experimental validation. First, we train the DuplexOmni model as the interaction layer, enabling an end-to-end model to jointly handle real-time speech, video, dialogue state, text output, and speech output. Second, we design asynchronous collaboration between the interaction layer and the thinking layer, allowing the interaction layer to invoke external thinking capability and integrate returned results during ongoing dialogue. Third, we build a Writer-Director data pipeline for continuous interaction, covering overlapping speech, silence, user supplements, interruptions, delayed thinking feedback, and complex task progression. Experiments show that DuplexOmni achieves advanced performance on multiple benchmarks and exhibits natural full-duplex interaction abilities. We will release the model weights, training data, and training and inference implementation.

Our main contributions are as follows:

- We build a Writer-Director data pipeline, train the DuplexOmni model with the resulting data, and provide a new open-source solution for constructing such interaction data.

- We propose DuplexOmni, a continuous multimodal interaction method that decouples the interaction layer from the thinking layer, enabling low-latency interaction and pluggable deep thinking to collaborate asynchronously.

- We validate DuplexOmni on multiple public benchmarks, and will release the full training and inference process to support future research.



## 2 Related work

### 2.1 Omni Models

Recent years, substantial progress in omni models (Team et al., 2025; Chen et al., 2025b). By introducing end-to-end audio-visual understanding and generation, these models can process multiple forms of information in a way closer to human interaction. Models such as GPT-4o (OpenAI, 2024), Gemini (Team, 2023), Qwen2.5-Omni (Team, 2025a), Qwen3-Omni (Team, 2025a), MiniCPM-o (Yao et al., 2024), Baichuan-Omni (Inc., 2025), and Kimi-Audio (KimiTeam et al., 2025) have demonstrated strong cross-modal understanding and dialogue capabilities. The Qwen series unifies speech, vision, and text capabilities within an end-to-end omni architecture; MiniCPM-o emphasizes efficient multimodal interaction in on-device or lightweight settings. Despite significantly expanding the perceptual and generative boundaries of large models, most of these models still organize interaction in a request-driven manner: user input is collected, the model performs understanding and generation, and then a response is returned. This mode is suitable for single-turn or multi-turn task processing, but cannot handle user interaction in real time. Therefore, omni-modal models provide a foundation for unified multimodal capability, but do not directly address coordination in real-time continuous interaction.

### 2.2 Duplex Interaction

Other studies focus on duplex interaction, where a model can receive user input and generate responses simultaneously in real time. Unlike traditional simplex models, duplex interaction (Ma et al., 2025; Nguyen et al., 2022; Wang et al., 2024; Chen et al., 2025a; Lu et al., 2025; Yang et al., 2026) requires the model to keep listening to user speech while speaking, and to handle natural interaction phenomena such as overlapping speech and interjections. Moshi (Défossez et al.,

2

<div style="text-align: center;"><img src="imgs/img_in_image_box_139_152_1049_855.jpg" alt="Image" width="76%" />

Beijing instead.

</div>


<div style="text-align: center;">Figure 2: Overview of DuplexOmni. (a) The interaction layer conducts real-time dialogue while asynchronously collaborating with the thinking layer. (b) The DuplexOmni model implements the interaction layer with time-sliced Thinker-Talker inference over streaming inputs and thinking feedback. MTP and Code2Wav are omitted for clarity.</div>


2024) achieves low-latency full-duplex speech dialogue by jointly modeling user speech, assistant text, and assistant speech. OmniFlatten (Zhang et al., 2025) flattens speech and text inputs and outputs into a unified GPT sequence to model seamless voice conversation in an end-to-end manner. MiniCPM-o (Yao et al., 2024) models time-aligned multimodal streams, enabling the model to see, listen, and speak on a unified timeline. Mini-OmniReasoner (Xie et al., 2025), and dGSLM (Nguyen et al., 2022) also advance streaming speech modeling and parallel listening and speaking (Yu et al., 2025; Zhang et al., 2023a; Held et al., 2025; Xiaomi, 2025) from different perspectives. These methods move speech interaction from strict turn-taking toward more natural continuous dialogue. However, when dialogue requires longer reasoning, interaction between the model and the user is still interrupted.

## 3 Method

We propose DuplexOmni, a method for multimodal full-duplex interaction. As shown in Figure 2 DuplexOmni divides model capabilities into an interaction layer and a thinking layer, and connects real-time interaction with deep thinking through asynchronous parallel collaboration. The interaction layer is implemented by the DuplexOmni model, which continuously receives speech, video, dialogue state, and results returned from the thinking layer, organizes the current context, infers user intent, and generates text and speech responses in real time. The thinking layer is a pluggable layer that can be instantiated with MLLMs or tool agents to perform complex reasoning, tool use, and task planning. To train and deploy this form of interaction, we build a Writer-Director data pipeline that generates continuous-interaction data and simulates realistic dialogue scenarios for training the full-duplex interaction model. In the following

3

sections, we detail the hierarchical structure of DuplexOmni, the Writer-Director data pipeline, and real-time inference for low-latency deployment.

### 3.1 Duplex Omni

DuplexOmni adopts a two-layer structure with an interaction layer and a thinking layer. The interaction layer handles real-time interaction: it reads audio, video, and intermediate results from the thinking layer, organizes responses to the user, controls the dialogue rhythm, and requests assistance from the thinking layer when needed. The thinking layer provides additional cognitive capability through a pluggable interface, running complex reasoning and tool use in the background. We first describe the decoupled structure, then the DuplexOmni model that implements the interaction layer, and finally the running strategy of the thinking layer.

#### 3.1.1 Decoupled Interaction and Thinking

Decoupled Interaction and Thinking centers on thinking requests initiated by the interaction layer and streaming results returned by the thinking layer. The interaction layer handles real-time dialogue, while the thinking layer performs background reasoning. When the current interaction requires external assistance, the interaction layer passes the user context to the thinking layer, including dialogue text, video information, and task state, and issues a thinking request. This request does not block real-time interaction. The interaction layer continues to receive user input, control the dialogue rhythm, and organize immediate responses.

After receiving a request, the thinking layer runs asynchronously with the interaction layer. It can be a strong LLM or a task-specific agent. During streaming output, the thinking layer wraps intermediate results with special control tokens and continuously returns them to the interaction layer. The interaction layer organizes these responses into text and speech replies suitable for the current context. When the interaction layer determines that conditions have changed or that the current dialogue no longer needs external assistance, it stops the streaming output of the thinking layer through special control tokens. This design enables DuplexOmni to continuously serve users in low-latency interaction while incorporating complex reasoning, tool use, or specialized agent capabilities on demand.

#### 3.1.2 DuplexOmni Model

Time-Sliced Full-Duplex Modeling Duplex-Omni model realizes full-duplex interaction through time-sliced autoregressive inference. Similar to Moshi (Défossez et al., 2024) and MiniCPMo (Yao et al., 2024), we divide continuous interaction into fixed 480 ms slices. At slice t, the model consumes the dialogue history, the intermediate results returned by the thinking layer, and the inputs from slice t-1. For audio, this input is the 480 ms speech segment in that slice. For video, it is the visual frame sampled from the same slice.

Each slice produces three outputs: a thinking-control signal, a semantic interpretation of the latest user input, and the Assistant's text and 480 ms speech response. This design allows the model to continue receiving new user inputs and new thinking results while generating responses, thereby achieving full-duplex interaction with a response granularity of 480 ms.

Model Architecture DuplexOmni model follows the Thinker-Talker speech generation structure in the Qwen-Omni (Chu et al., 2024; Team, 2025a, 2026b) family. The Thinker is the internal MLLM backbone that processes the current context and generates Assistant text tokens. The Talker converts the generated linguistic states into streaming speech. For slice t, the Thinker produces an Assistant token sequence together with the aligned token embeddings and hidden states. We denote them by  $ E_{t} $ and  $ H_{t} $, respectively. These two sequences are projected into the Talker conditioning space and added row-wise:

 $$ c_{t,\ell}=f_{\mathrm{t e x t}}(e_{t,\ell})+f_{\mathrm{h i d d e n}}(h_{t,\ell}),\qquad\ell=1,\ldots,m_{t}, $$ 

where  $ m_{t} $ is the number of Assistant tokens in the current slice. We denote the resulting conditioning sequence by

 $$ C_{t}=(c_{t,1},\ldots,c_{t,m_{t}}). $$ 

The Talker does not generate speech from $C_{t}$ alone. It preserves both the historical conditioning sequences and the historical speech codec history. Let $Q_{i}$ denote the complete residual vector quantization (RVQ) codec sequence generated in slice i. If slice i contains $L_{i}$ speech frames, then

 $$ Q_{i}=(q_{i,1},\ldots,q_{i,L_{i}}), $$ 

where each frame is represented by

 $$ q_{i,j}=(q_{i,j}^{0},q_{i,j}^{1},\ldots,q_{i,j}^{K-1}). $$ 

4

For each frame, the Talker constructs a summed codec embedding

 $$ r_{i,j}=u_{0}(q_{i,j}^{0})+\sum_{k=1}^{K-1}u_{k}(q_{i,j}^{k}), $$ 

and we denote the codec embedding sequence of slice i by

 $$ R_{i}=(r_{i,1},\ldots,r_{i,L_{i}}). $$ 

At the beginning of slice $t$, the embedding prefix of the Talker is

 $$ \begin{array}{r}{P_{t}=[(C_{i},b_{\mathrm{B O S}},R_{i},b_{\mathrm{E O S}})_{i=1}^{t-1},~C_{t},~b_{\mathrm{B O S}}].}\end{array} $$ 

This expression matches the actual organization of the prompt. Each historical slice contributes one conditioning segment followed by one codec segment wrapped by a single codec BOS and EOS. The current slice contributes its conditioning sequence and one codec BOS before speech generation starts. Inside the current slice, the model maintains both a token channel and an embedding channel. Conditioning positions are filled with a dedicated pad id on the token channel, while historical codec spans keep their true codec tokens. On the embedding channel, the model writes the conditioning projections and the corresponding summed codec embeddings.

 $$ q_{t,j}^{0}=\mathrm{T a l k e r}(P_{t},q_{t,<j}^{0}). $$ 

Given the current prefix, the Talker autoregressively predicts the layer-0 codec token of the current speech frame:

For each non-EOS layer-0 token, an MTP (Team, 2025a) module predicts the residual codebooks conditioned on the current Talker hidden state and the predicted layer-0 token, producing the complete RVQ code  $ q_{t,j} $ and its summed embedding  $ r_{t,j} $. The newly generated layer-0 token and summed embedding are then appended to the current prefix and used for the next frame. Therefore, within a slice, the Talker repeatedly appends newly generated codec content, rather than repeatedly inserting new BOS or EOS markers.

Each slice generates six codec frames, corresponding to 480 ms of speech, and the resulting RVQ sequence is decoded by Code2Wav into waveform samples. After generation, the current conditioning sequence  $ C_t $ and codec sequence  $ Q_t $ are written into history and reused to construct the Talker prefix of the next slice. In this way, Duplex-Omni model remains autoregressive at the token level, continuous across adjacent time slices, and full-duplex at the interaction level.



### 3.2 Data Construction

To train the full-duplex interaction ability of DuplexOmni, the training data must describe continuous interaction behaviors, such as interruption, backchanneling, waiting, background reasoning, and delayed information integration. Existing multi-turn dialogue data is mostly turn-based. It only records user and assistant utterances, and lacks temporal information. Therefore, it cannot describe when the model should speak, stop, wait, trigger background thinking, or use returned information.

We address this by dividing data construction into two stages: scenario and content construction and Writer-Director temporal annotation. The first stage decides what the dialogue is about and how it happens. The second stage converts natural dialogue into structured samples with explicit temporal causality. Since content and temporal annotation are decoupled, new tasks only require new content data and scenario configurations. The downstream pipeline remains unchanged.

#### 3.2.1 Scenario and Content Construction

This stage builds content-scenario pairs for training. Each sample contains raw content and a scenario seed: the raw content provides the task semantics, while the scenario seed specifies how the interaction unfolds, such as who initiates the dialogue, whether the user may revise or add information during the exchange, and how the assistant should respond when background reasoning or turn-taking events occur. We sample scenario combinations from configuration files, filter invalid or conflicting settings, and rewrite raw content into a speech-friendly form by removing written-style expressions, special symbols, and overly long sentences.

#### 3.2.2 Writer-Director Data Pipeline

This stage converts content-scenario pairs into structured temporal data for full-duplex training. The Writer generates a natural dialogue script that follows the scenario. The Director adds temporal control signals.

The Writer generates a natural language script from the raw content and the scenario seed. The script preserves the task semantics and reflects the target interaction pattern. For example, in a math

5

<div style="text-align: center;"><img src="imgs/img_in_image_box_145_134_1045_488.jpg" alt="Image" width="75%" />

1 Scenario Seed
2 Raw Content
3 User��4 User says: ‘I want to calculate xx. Can you help me get the final result?’
5 Structured Temporal Data
6 Visual content
7 User. I forgot...
8 [CUT]
9 Agent Speaking
10 This is... that needs careful
11 [THINK]
12 Agent Thinking
13 Time

</div>


<div style="text-align: center;">Figure 3: Data pipeline for DuplexOmni. Scenario seeds and raw content are converted into temporally annotated full-duplex dialogues; representative control tokens are shown, with the full token set detailed in the Appendix.</div>


reasoning task, the Writer may arrange the user to ask a question, add missing conditions midway, interrupt the assistant, or insert new information during assistant reasoning. For assistant-initiated scenarios, the Writer adjusts the opening and speaking order so that the dialogue naturally starts from the assistant.

The output of the Writer is still a human-readable linear script. For example:

User says: 'I want to calculate xx. Can you help me get the final result?' After the user asks a question that requires calculation, the assistant starts to respond: 'This is indeed a problem that needs careful analysis.' When the assistant says 'needs', the user interrupts and adds: 'Wait, I forgot one condition.'

This script describes how the dialogue happens. It does not handle control tokens or the audio timeline.

The Director converts this script into a structured sample with temporal control signals. The full definitions of special text tags are shown in Appendix. For the above script, the annotated sample can be written as:

User: I want to calculate xx. Can you help me get the final result? [THINK]

Assistant:Assistant:This is indeed a problem that needs $ ^{a} $ careful[CUT] analysis.

User: Wait, I forgot one condition. [WAIT]

Here, [THINK] triggers background reasoning. ^marks the time point where the user speech stream starts. [CUT] marks the actual stopping point of the interrupted assistant speech. [WAIT] means that the user adds a new condition, so the background reasoning should pause or revise. The Director does not change the dialogue content. It adds trainable temporal causality.



Finally, we apply consistency checks to the Director output. We filter samples with conflicting control tokens, missing thinking triggers, returned information without causal source, or unreasonable interruption points. After cleaning, we synthesize speech with TTS and segment the audio into fixed-size chunks, so that the resulting data follows the same time-sliced format used by DuplexOmni model training and inference. The processing details differ between fully synthetic text-to-speech data and dialogue data sampled from real recordings; we leave this discussion to the Appendix. Through this pipeline, DuplexOmni learns when to listen, speak, wait, interrupt, request background thinking, and integrate delayed information.

### 3.3 Real-Time Duplex Inference

To enable real-time duplex inference, DuplexOmni uses RTF < 1 as the latency target for speech generation. RTF is the ratio between generation time and audio duration. A value below 1 means that each audio chunk can be generated before it finishes playing. DuplexOmni decouples Thinker-based text generation from Talker-based speech generation and runs them as an asynchronous pipeline. This avoids serial latency accumulation across continuous chunks. For the Talker path, we apply KV-cache-based incremental decoding and graph execution optimization to autoregressive codec decoding and MTP computation. These optimizations reduce redundant computation and scheduling overhead and support stable low-latency speech output.

6

## 4 Experiments

### 4.1 Settings

We compare DuplexOmni with recent real-time omni models and speech-to-speech systems, including MiniCPM-o, Doubao, Qwen-Omni realtime variants, and Gemini live variants. All models are evaluated under their streaming or realtime settings; proprietary models are evaluated through official APIs, and open-source models use public weights with officially recommended inference configurations. We evaluate models on Full DuplexBench (DuplexBench) v1.5 (Lin et al., 2025), Big Bench Audio (Srivastava et al., 2022; Suzgun et al., 2022), Daily-Omni (Zhou et al., 2025), and LibriSpeech (Panayotov et al., 2015) WER. Full DuplexBench measures full-duplex interaction quality, Big Bench Audio measures streaming audio understanding, and Daily-Omni measures general omni capability. For models with ASR capability, we report LibriSpeech as a reference for speech recognition quality. We also report latency as a measure of real-time response delay. Unless otherwise specified in ablation experiments, DuplexOmni uses the full configuration, where the DuplexOmni model serves as the interaction layer and Gemini-3.1-Flash-Lite (Reid et al., 2024) serves as the thinking layer.

### 4.2 Data

The training data construction consists of two parts: scenario seeds and dialogue content. We build about 620K scenario seeds to define the distribution of continuous interaction settings. These seeds cover five types of interaction scenarios and annotate attributes such as interaction type, required events, and user style, so that the resulting data spans full-duplex interactions with different densities, rhythms, and levels of complexity.

The dialogue content contains about 3.02M raw conversations, including 10K video-call conversations. The text-dialogue portion includes about 1.486M user-initiated conversations and 1.528M system-initiated conversations, sourced from UltraChat (Ding et al., 2023), WildChat (Zhao et al., 2024a), BELLE (Ji et al., 2023), COIG (Zhang et al., 2023b), no-robots (Rajani et al., 2023), OASST2 (Köpf et al., 2023). The overall language distribution is mainly Chinese, about 70%, with about 30% English and a small amount of other languages. All data construction stages use Qwen3.5-397B-A27B (Team, 2025b) as the generation and annotation model. Speech training data is synthesized with Qwen3-TTS (Team, 2026a) and converted into codec tokens with the Mimi (Défossez et al., 2024) encoder.



### 4.3 Training

DuplexOmni treats time-sliced full-duplex interaction as continuous multi-turn dialogue. Initialized from Qwen3-Omni, it is trained with two-stage SFT: the first stage builds basic full-duplex listening and speaking ability on large-scale speech interaction data, while the second stage further improves complex interaction and video-call performance using high-quality interaction and video-call data.

In each stage, we alternately optimize the Thinker and the Talker. When training the Thinker, we freeze the Talker and compute only the cross-entropy loss of the Thinker. When training the Talker, we freeze the Thinker and compute only the cross-entropy loss of the Talker MoE and MTP modules. The data ratio between the two optimization parts is 1:1. The learning rate is 1e-5 for the Thinker and 1e-4 for the Talker, with a batch size of 128. Training is conducted with Megatron-swift-3.12 (Zhao et al., 2024b) on 128 Nvidia H20 GPUs.

### 4.4 Performance Comparison

Table 1 reports the main comparison between DuplexOmni and recent realtime omni models or speech-to-speech systems. The results show three main observations:

Strong full-duplex interaction. DuplexOmni achieves 72.6% ToR on Full DuplexBench, substantially outperforming all realtime baselines, while keeping a response latency of 0.506s. This shows that the DuplexOmni model can handle continuous input and output under strict realtime constraints.

Reasoning without sacrificing interaction. DuplexOmni achieves the best Big Bench Audio score of 77.2% and remains competitive on Daily-Omni. This suggests that the layered design preserves real-time interaction quality while using the thinking layer to improve audio understanding and complex reasoning.

### 4.5 Ablation Study

Table 2 presents the ablation results of DuplexOmni. Weak Thinking replaces the default thinking layer with a weaker model. w/o Thinking removes the thinking layer and keeps only the interaction layer. w/o Thinking & ASR further removes

7


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Model</td><td style='text-align: center; word-wrap: break-word;'>DuplexBench ToR (%)</td><td style='text-align: center; word-wrap: break-word;'>Big Bench Audio (%)</td><td style='text-align: center; word-wrap: break-word;'>Daily-Omni (%)</td><td style='text-align: center; word-wrap: break-word;'>LibriSpeech WER</td><td style='text-align: center; word-wrap: break-word;'>Latency (s)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>DuplexOmni</td><td style='text-align: center; word-wrap: break-word;'>72.6</td><td style='text-align: center; word-wrap: break-word;'>77.2</td><td style='text-align: center; word-wrap: break-word;'>53.8</td><td style='text-align: center; word-wrap: break-word;'>0.1192</td><td style='text-align: center; word-wrap: break-word;'>0.506</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MiniCPM-o 4.5</td><td style='text-align: center; word-wrap: break-word;'>36.3</td><td style='text-align: center; word-wrap: break-word;'>36.0</td><td style='text-align: center; word-wrap: break-word;'>80.2</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>0.502</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Doubao</td><td style='text-align: center; word-wrap: break-word;'>27.8</td><td style='text-align: center; word-wrap: break-word;'>47.9</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>1.82</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen3-Omni-Realtime-Flash</td><td style='text-align: center; word-wrap: break-word;'>25.2</td><td style='text-align: center; word-wrap: break-word;'>32.1</td><td style='text-align: center; word-wrap: break-word;'>76.2</td><td style='text-align: center; word-wrap: break-word;'>0.013</td><td style='text-align: center; word-wrap: break-word;'>1.28</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen3.5-Omni-Realtime-Flash</td><td style='text-align: center; word-wrap: break-word;'>26.4</td><td style='text-align: center; word-wrap: break-word;'>35.0</td><td style='text-align: center; word-wrap: break-word;'>81.8</td><td style='text-align: center; word-wrap: break-word;'>0.011</td><td style='text-align: center; word-wrap: break-word;'>1.25</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Gemini-3.1-Flash-Live</td><td style='text-align: center; word-wrap: break-word;'>24.1</td><td style='text-align: center; word-wrap: break-word;'>57.9</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>0.041</td><td style='text-align: center; word-wrap: break-word;'>2.57</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Gemini-3.1-Flash-Lite</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>58.9</td><td style='text-align: center; word-wrap: break-word;'>59.0</td><td style='text-align: center; word-wrap: break-word;'>0.038</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr></table>

<div style="text-align: center;">Table 1: Interaction-layer comparison with real-time full-duplex and speech-to-speech baselines. All models with real-time capabilities are evaluated in real-time mode, and Daily-Omni is evaluated under streaming mode.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Model</td><td style='text-align: center; word-wrap: break-word;'>DuplexBench ToR (%)</td><td style='text-align: center; word-wrap: break-word;'>Big Bench Audio (%)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>DuplexOmni</td><td style='text-align: center; word-wrap: break-word;'>72.6</td><td style='text-align: center; word-wrap: break-word;'>77.2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Weak Thinking</td><td style='text-align: center; word-wrap: break-word;'>72.1</td><td style='text-align: center; word-wrap: break-word;'>50.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>w/o Thinking</td><td style='text-align: center; word-wrap: break-word;'>65.2</td><td style='text-align: center; word-wrap: break-word;'>22.2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>w/o Thinking &amp; ASR</td><td style='text-align: center; word-wrap: break-word;'>67.2</td><td style='text-align: center; word-wrap: break-word;'>18.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Thinking Only</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>58.9</td></tr></table>

<div style="text-align: center;">Table 2: Ablation study on DuplexOmni. Full DuplexBench measures interaction quality, while Big Bench Audio evaluates audio understanding under the streaming setting.</div>


speech-to-text output. Thinking Only directly uses the thinking layer to process audio input without the DuplexOmni interaction layer. Based on these settings, we obtain three observations.

The full-duplex ability of the interaction layer is independent. Replacing the thinking layer with a weaker model only changes Full DuplexBench from 72.6% to 72.1%. This shows that full-duplex interaction quality is mainly determined by the DuplexOmni model, and is not sensitive to the strength of the thinking layer.

The thinking layer determines the reasoning ceiling. When the thinking layer is replaced by a weaker model, Big Bench Audio drops from 77.2% to 50.3%; removing the thinking layer further reduces it to 22.2%. Together with the first observation, this shows that the thinking layer is a pluggable component of the interaction layer.

The interaction layer improves the effectiveness of the thinking layer. Thinking Only directly processes audio input with the thinking layer and reaches 58.9% on Big Bench Audio, while the full Duplex Omni reaches 77.2%. This indicates that the gain does not only come from the external strong


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Length</td><td style='text-align: center; word-wrap: break-word;'>Gemini Lite</td><td style='text-align: center; word-wrap: break-word;'>Gemini Live</td><td style='text-align: center; word-wrap: break-word;'>Duplex Omni</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>1–5</td><td style='text-align: center; word-wrap: break-word;'>4.9</td><td style='text-align: center; word-wrap: break-word;'>7.8</td><td style='text-align: center; word-wrap: break-word;'>25.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>6–10</td><td style='text-align: center; word-wrap: break-word;'>5.3</td><td style='text-align: center; word-wrap: break-word;'>4.4</td><td style='text-align: center; word-wrap: break-word;'>15.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>11–15</td><td style='text-align: center; word-wrap: break-word;'>3.4</td><td style='text-align: center; word-wrap: break-word;'>3.3</td><td style='text-align: center; word-wrap: break-word;'>12.0</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>16–20</td><td style='text-align: center; word-wrap: break-word;'>2.9</td><td style='text-align: center; word-wrap: break-word;'>2.2</td><td style='text-align: center; word-wrap: break-word;'>10.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>21+</td><td style='text-align: center; word-wrap: break-word;'>3.2</td><td style='text-align: center; word-wrap: break-word;'>4.6</td><td style='text-align: center; word-wrap: break-word;'>8.8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Overall</td><td style='text-align: center; word-wrap: break-word;'>3.75</td><td style='text-align: center; word-wrap: break-word;'>4.09</td><td style='text-align: center; word-wrap: break-word;'>11.92</td></tr></table>

<div style="text-align: center;">Table 3: ASR error rate by utterance length. Short utterances are substantially harder for DuplexOmni under the full-duplex streaming setting.</div>


model. The interaction layer also organizes and filters the input passed to the thinking layer, making the thinking process more effective.

### 4.6 Full-Duplex ASR Analysis

Table 3 shows that DuplexOmni performs worse on short utterances, with WER dropping from 25.1% for 1–5 words to 8.8% for 21+ words. This suggests that short, low-context speech fragments in full-duplex interaction remain a key challenge.

## 5 Conclusion

We present DuplexOmni, a real-time multimodal full-duplex interaction method that decouples low-latency interaction from asynchronous thinking and tool use. By combining the DuplexOmni interaction model with a pluggable thinking layer and a Writer-Director data pipeline, DuplexOmni supports continuous listening, seeing, speaking, and reasoning. Experiments show that it achieves strong full-duplex interaction performance while maintaining low response latency.

8

## Limitations

DuplexOmni still has several limitations. First, its video capability remains limited because the amount of video-call and visually grounded interaction data is relatively small. Second, its English speech ability is weaker than desired, partly due to the training data being dominated by Chinese speech. We leave stronger video modeling and more balanced multilingual speech training to future work.

## References

Junjie Chen, Yao Hu, Junjie Li, Kangyue Li, Kun Liu, Wenpeng Li, Xu Li, Ziyuan Li, Feiyu Shen, Xu Tang, Manzhen Wei, Yichen Wu, Fenglong Xie, Kaituo Xu, and Kun Xie. 2025a. Fireredchat: A pluggable, full-duplex voice interaction system with cascaded and semi-cascaded implementations. CoRR, abs/2509.06502.

Wenxi Chen, Ziyang Ma, Ruiqi Yan, Yuzhe Liang, Xiquan Li, Ruiyang Xu, Zhikang Niu, Yanqiao Zhu, Yifan Yang, Zhanxun Liu, Kai Yu, Yuxuan Hu, Jinyu Li, Yan Lu, Shujie Liu, and Xie Chen. 2025b. Slamomni: Timbre-controllable voice interaction system with single-stage training. In Findings of the Association for Computational Linguistics, ACL 2025, Vienna, Austria, July 27 - August 1, 2025, Findings of ACL, pages 2262–2282. Association for Computational Linguistics.

Yunfei Chu, Jin Xu, Qian Yang, Haojie Wei, Xipin Wei, Zhifang Guo, Yichong Leng, Yuanjun Lv, Jinzheng He, Junyang Lin, Chang Zhou, and Jingren Zhou. 2024. Qwen2-audio technical report. CoRR, abs/2407.10759.

Alexandre Défossez, Laurent Mazaré, Manu Orsini, Amélie Royer, Patrick Pérez, Hervé Jégou, Edouard Grave, and Neil Zeghidour. 2024. Moshi: a speech-text foundation model for real-time dialogue. CoRR, abs/2410.00037.

Ning Ding, Yulin Chen, Bokai Xu, Yujia Qin, Zhi Zheng, Shengding Hu, Zhiyuan Liu, Maosong Sun, and Bowen Zhou. 2023. Enhancing chat language models by scaling high-quality instructional conversations. arXiv preprint arXiv:2305.14233.

William Barr Held, Yanzhe Zhang, Weiyan Shi, Minzhi Li, Michael J. Ryan, and Diyi Yang. 2025. Distilling an end-to-end voice assistant without instruction training data. In Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), ACL 2025, Vienna, Austria, July 27 - August 1, 2025, pages 7876-7891. Association for Computational Linguistics.

Baichuan Inc. 2025. Baichuan-omni-1.5 technical report. CoRR, abs/2501.15368.

Yunjie Ji, Yan Gong, Yong Deng, Yiping Peng, Qiang Niu, Baochang Ma, and Xiangang Li. 2023. Towards better instruction following language models for chinese: Investigating the impact of training data and evaluation. CoRR, abs/2304.07854.

KimiTeam, Ding Ding, Zeqian Ju, Yichong Leng, Songxiang Liu, Tong Liu, Zeyu Shang, Kai Shen, Wei Song, Xu Tan, Heyi Tang, Zhengtao Wang, Chu Wei, Yifei Xin, Xinran Xu, Jianwei Yu, Yutao Zhang, Xinyu Zhou, Y. Charles, and 21 others. 2025. Kimiaudio technical report. CoRR, abs/2504.18425.

Andreas Köpf, Yannic Kilcher, Dimitri von Rütte, Sotiris Anagnostidis, Zhi-Rui Tam, Keith Stevens, Abdullah Barhoum, Nguyen Minh Duc, Oliver Stanley, Richard Nagyfi, Shahul ES, Sameer Suri, David Glushkov, Arnav Dantuluri, Andrew Maguire, Christoph Schuhmann, Huu Nguyen, and Alexander Mattick. 2023. Openassistant conversations – democratizing large language model alignment. Preprint, arXiv:2304.07327.

Guan-Ting Lin, Jiachen Lian, Tingle Li, Qirui Wang, Gopala Anumanchipalli, Alexander H. Liu, and Hung-Yi Lee. 2025. Full-duplex-bench: A benchmark to evaluate full-duplex spoken dialogue models on turn-taking capabilities. In IEEE Automatic Speech Recognition and Understanding Workshop, ASRU 2025, Honolulu, HI, USA, December 6-10, 2025, pages 1-8. IEEE.

Yudong Lu, Yazhe Niu, Shuai Hu, and Haolin Wang. 2025. Cleans2s: Single-file framework for proactive speech-to-speech interaction. CoRR, abs/2506.01268.

Ziyang Ma, Yakun Song, Chenpeng Du, Jian Cong, Zhuo Chen, Yuping Wang, Yuxuan Wang, and Xie Chen. 2025. Language model can listen while speaking. In Thirty-Ninth AAAI Conference on Artificial Intelligence, Thirty-Seventh Conference on Innovative Applications of Artificial Intelligence, Fifteenth Symposium on Educational Advances in Artificial Intelligence, AAAI 2025, Philadelphia, PA, USA, February 25 - March 4, 2025, pages 24831–24839. AAAI Press.

Tu Anh Nguyen, Eugene Kharitonov, Jade Copet, Yossi Adi, Wei-Ning Hsu, Ali Elkahky, Paden Tomasello, Robin Algayres, Benoit Sagot, Abdelrahman Mohamed, and Emmanuel Dupoux. 2022. Generative spoken dialogue language modeling. Preprint, arXiv:2203.16502.

OpenAI. 2024. Gpt-4o system card. CoRR, abs/2410.21276.

Vassil Panayotov, Guoguo Chen, Daniel Povey, and Sanjeev Khudanpur. 2015. Librispeech: An ASR corpus based on public domain audio books. In 2015 IEEE International Conference on Acoustics, Speech and Signal Processing, ICASSP 2015, South Brisbane, Queensland, Australia, April 19-24, 2015, pages 5206–5210. IEEE.

9

Nazneen Rajani, Lewis Tunstall, Edward Beeching, Nathan Lambert, Alexander M. Rush, and Thomas Wolf. 2023. No robots. https://huggingface.co/datasets/HuggingFaceH4/no_robots.

Machel Reid, Nikolay Savinov, Denis Teplyashin, Dmitry Lepikhin, Timothy P. Lillicrap, Jean-Baptiste Alayrac, Radu Soricut, Angeliki Lazaridou, Orhan Firat, Julian Schrittwieser, Ioannis Antonoglou, Rohan Anil, Sebastian Borgeaud, Andrew M. Dai, Katie Millican, Ethan Dyer, Mia Glaese, Thibault Sottiaux, Benjamin Lee, and 34 others. 2024. Gemini 1.5: Unlocking multimodal understanding across millions of tokens of context. CoRR, abs/2403.05530.

Aarohi Srivastava, Abhinav Rastogi, Abhishek Rao, Abu Awal Md Shoeb, Abubakar Abid, Adam Fisch, Adam R Brown, Adam Santoro, Aditya Gupta, Adrià Garriga-Alonso, and 1 others. 2022. Beyond the imitation game: Quantifying and extrapolating the capabilities of language models. arXiv preprint arXiv:2206.04615.

Mirac Suzgun, Nathan Scales, Nathanael Schärli, Sebastian Gehrmann, Yi Tay, Hyung Won Chung, Aakanksha Chowdhery, Quoc V Le, Ed H Chi, Denny Zhou, and Jason Wei. 2022. Challenging big-bench tasks and whether chain-of-thought can solve them. arXiv preprint arXiv:2210.09261.

Gemini Team. 2023. Gemini: A family of highly capable multimodal models. CoRR, abs/2312.11805.

Qwen Team. 2025a. Qwen3-omni technical report. CoRR, abs/2509.17765.

Qwen Team. 2025b. Qwen3 technical report. CoRR, abs/2505.09388.

Qwen Team. 2026a. Qwen3-tts technical report. CoRR, abs/2601.15621.

Qwen Team. 2026b. Qwen3.5-omni technical report. CoRR, abs/2604.15804.

Tongyi Fun Team, Qian Chen, Luyao Cheng, Chong Deng, Xiangang Li, Jiaqing Liu, Chao-Hong Tan, Wen Wang, Junhao Xu, Jieping Ye, Qinglin Zhang, Qiquan Zhang, and Jingren Zhou. 2025. Fun-audio-chat technical report. CoRR, abs/2512.20156.

Peng Wang, Songshuo Lu, Yaohua Tang, Sijie Yan, Yuanjun Xiong, and Wei Xia. 2024. A full-duplex speech dialogue scheme based on large language models. CoRR, abs/2405.19487.

LLM-Core Xiaomi. 2025. Mimo-audio: Audio language models are few-shot learners. CoRR, abs/2512.23808.

Zhifei Xie, Ziyang Ma, Zihang Liu, Kaiyu Pang, Hongyu Li, Jialin Zhang, Yue Liao, Deheng Ye, Chunyan Miao, and Shuicheng Yan. 2025. Mini-omni-reasoner: Token-level thinking-in-speaking in large speech models. CoRR, abs/2508.15827.

Jin Xu, Zhifang Guo, Jinzheng He, Hangrui Hu, Ting He, Shuai Bai, Keqin Chen, Jialin Wang, Yang Fan, Kai Dang, Bin Zhang, Xiong Wang, Yunfei Chu, and Junyang Lin. 2025. Qwen2.5-omni technical report. CoRR, abs/2503.20215.

Jianing Yang, Yusuke Fujita, and Yui Sudo. 2026. Duplexcascade: Full-duplex speech-to-speech dialogue with vad-free cascaded ASR-LLM-TTS pipeline and micro-turn optimization. CoRR, abs/2603.09180.

Yuan Yao, Tianyu Yu, Ao Zhang, Chongyi Wang, Junbo Cui, Hongji Zhu, Tianchi Cai, Haoyu Li, Weilin Zhao, Zhihui He, and 1 others. 2024. Minicpm-v: A gpt-4v level mlIm on your phone. arXiv preprint arXiv:2408.01800.

Wenyi Yu, Siyin Wang, Xiaoyu Yang, Xianzhao Chen, Xiaohai Tian, Jun Zhang, Guangzhi Sun, Lu Lu, Yuxuan Wang, and Chao Zhang. 2025. Salmon-omni: A standalone speech LLM without codec injection for full-duplex conversation. CoRR, abs/2505.17060.

Dong Zhang, Shimin Li, Xin Zhang, Jun Zhan, Pengyu Wang, Yaqian Zhou, and Xipeng Qiu. 2023a. Speechgpt: Empowering large language models with intrinsic cross-modal conversational abilities. In Findings of the Association for Computational Linguistics: EMNLP 2023, Singapore, December 6-10, 2023, Findings of ACL, pages 15757–15773. Association for Computational Linguistics.

Ge Zhang, Yemin Shi, Ruibo Liu, Ruibin Yuan, Yizhi Li, Siwei Dong, Yu Shu, Zhaoqun Li, Zekun Wang, Chenghua Lin, Wenhao Huang, and Jie Fu. 2023b. Chinese open instruction generalist: A preliminary release. Preprint, arXiv:2304.07987.

Qinglin Zhang, Luyao Cheng, Chong Deng, Qian Chen, Wen Wang, Siqi Zheng, Jiaqing Liu, Hai Yu, Chaohong Tan, Zhihao Du, and Shiliang Zhang. 2025. Omnifatten: An end-to-end GPT model for seamless voice conversation. In Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), ACL 2025, Vienna, Austria, July 27 - August 1, 2025, pages 14570-14580. Association for Computational Linguistics.

Wenting Zhao, Xiang Ren, Jack Hessel, Claire Cardie, Yejin Choi, and Yuntian Deng. 2024a. Wildchat: 1m chatgpt interaction logs in the wild. Preprint, arXiv:2405.01470.

Yuze Zhao, Jintao Huang, Jinghan Hu, Xingjun Wang, Yunlin Mao, Daoze Zhang, Zeyinzi Jiang, Zhikai Wu, Baole Ai, Ang Wang, Wenmeng Zhou, and Yingda Chen. 2024b. Swift:a scalable lightweight infrastructure for fine-tuning. Preprint, arXiv:2408.05517.

Ziwei Zhou, Rui Wang, and Zuxuan Wu. 2025. Daily-omni: Towards audio-visual reasoning with temporal alignment across modalities. CoRR, abs/2505.17862.

10

### A Full Control Token Set

Table 4 lists the complete set of Director annotation tokens inserted during the Writer-Director pipeline. These tokens encode the temporal relationship between user speech, assistant speech, and background thinking in each training sample.

The six tokens capture five distinct temporal phenomena in full-duplex interaction: (1) thinking onset ([THINK]), triggering asynchronous background reasoning at a precise moment in the user turn; (2) thinking delivery (<...>), injecting reasoning results into the assistant stream with explicit causal ordering; (3) speech overlap onset (^), recording the exact character-level time point at which a second speaker begins; (4) speech cutoff ([CUT]), recording where the first speaker stops while preserving ghost text for loss computation; (5) thinking suspension ([WAIT]), resetting the reasoning state when user intent changes; and (6) shared silence ([PENDNS]), encoding mutual pauses with second-level granularity.

These tokens are stripped from the text before TTS synthesis and force-alignment; the resulting character-level timestamps are used to construct the time-sliced training samples consumed by the DuplexOmni model.

### B Examples of Writer-Director Outputs

The following four examples are drawn verbatim from actual Writer-Director pipeline outputs. Each example is a complete annotated dialogue produced by the Director stage for one scenario seed. Control tokens appear inline in monospace; <...> carries the S2 reasoning fragment that precedes each factual assistant utterance.

Example 1: Interruption with condition change. The user requests a story ([THINK]) but interrupts the assistant before it can finish asking a clarifying question. ^ marks the moment the user begins speaking during the assistant's turn; [CUT] marks where the assistant's audio actually stops (ghost text follows). [WAIT] resets the ongoing S2 reasoning; a new [THINK] later restarts it when the user adds further detail. The conversation also contains a one-second shared silence ([PEND1S]) while the user thinks.

User: Um, I wanna hear a story. [THINK]

Assistant:Assistant:No problem. What kind of topic [CUT] did you have in mind?

User: Warm and caring—family helping strangers. No need to ask so many questions. [WAIT]

[WAIT]

Assistant:Assistant:I need to confirm the tone, or the output might be off. [THINK]

User: Fine, just confirm already.

Assistant:OK, wait a sec.

Assistant:<The story's tone is warm and healing, initially set on a street.>Warm and comforting tone. Start on a street.

User: Wait, the street's too cold. Let's change to a restaurant.

Assistant:Got it. Switching to restaurant scene.

User: [PEND1S] He needs to suffer more, or it won't feel real. [THINK]

Assistant:Let me check the previous settings to avoid conflicts.

Assistant: <The man is unemployed and down on his luck; his family treats him to a meal at a restaurant.>Fixed. A man, jobless and down on his luck, is invited to dinner by his family. Is that okay?

Example 2: Backchannel without speech cutoff.

The user acknowledges mid-stream while the assistant is describing a product feature. ^ records the overlap onset, but no [CUT] follows because the assistant's speech continues uninterrupted—this is a non-disruptive backchannel. Multiple <...> fragments arrive in sequence, pacing the assistant's factual delivery.

User: Hi, if the site doesn't work on mobile, will SEO be affected? [THINK]

Assistant:Assistant:I'll check that.

Assistant:<sup>1</sup> <sup>2</sup>Assistant:<sup>3</sup> <sup>4</sup> <sup>5</sup> <sup>6</sup> <sup>7</sup> <sup>8</sup> <sup>9</sup> <sup>10</sup> <sup>11</sup> <sup>12</sup> <sup>13</sup> <sup>14</sup> <sup>15</sup> <sup>16</sup> <sup>17</sup> <sup>18</sup> <sup>19</sup> <sup>20</sup> <sup>21</sup> <sup>22</sup> <sup>23</sup> <sup>24</sup> <sup>25</sup> <sup>26</sup> <sup>27</sup> <sup>28</sup> <sup>29</sup> <sup>30</sup> <sup>31</sup> <sup>32</sup> <sup>33</sup> <sup>34</sup> <sup>35</sup> <sup>36</sup> <sup>37</sup> <sup>38</sup> <sup>39</sup> <sup>40</sup> <sup>41</sup> <sup>42</sup> <sup>43</sup> <sup>44</sup> <sup>45</sup> <sup>46</sup> <sup>47</sup> <sup>48</sup> <sup>49</sup> <sup>50</sup> <sup>51</sup> <sup>52</sup> <sup>53</sup> <sup>54</sup> <sup>55</sup> <sup>56</sup> <sup>57</sup> <sup>58</sup> <sup>59</sup> <sup>60</sup> <sup>61</sup> <sup>62</sup> <sup>63</sup> <sup>64</sup> <sup>65</sup> <sup>66</sup> <sup>67</sup> <sup>68</sup> <sup>69</sup> <sup>70</sup> <sup>71</sup> <sup>72</sup> <sup>73</sup> <sup>74</sup> <sup>75</sup> <sup>76</sup> <sup>77</sup> <sup>78</sup> <sup>79</sup> <sup>80</sup> <sup>81</sup> <sup>82</sup> <sup>83</sup> <sup>84</sup> <sup>85</sup> <sup>86</sup> <sup>87</sup> <sup>88</sup> <sup>89</sup> <sup>90</sup> <sup>91</sup> <sup>92</sup> <sup>93</sup> <sup>94</sup> <sup>95</sup> <sup>96</sup> <sup>97</sup> <sup>98</sup> <sup>99</sup> <sup>100</sup> <sup>101</sup> <sup>102</sup> <sup>103</sup> <sup>104</sup> <sup>105</sup> <sup>106</sup> <sup>107</sup> <sup>108</sup> <sup>109</sup> <sup>110</sup> <sup>111</sup> <sup>112</sup> <sup>113</sup> <sup>114</sup> <sup>115</sup> <sup>116</sup> <sup>117</sup> <sup>118</sup> <sup>119</sup> <sup>120</sup> <sup>121</sup> <sup>122</sup> <sup>123</sup> <sup>124</sup> <sup>125</sup> <sup>126</sup> <sup>127</sup> <sup>128</sup> <sup>129</sup> <sup>130</sup> <sup>131</sup> <sup>132</sup> <sup>133</sup> <sup>134</sup> <sup>135</sup> <sup>136</sup> <sup>137</sup> <sup>138</sup> <sup>139</sup> <sup>140</sup> <sup>141</sup> <sup>142</sup> <sup>143</sup> <sup>144</sup> <sup>145</sup> <sup>146</sup> <sup>147</sup> <sup>148</sup> <sup>149</sup> <sup>150</sup> <sup>151</sup> <sup>152</sup> <sup>153</sup> <sup>154</sup> <sup>155</sup> <sup>156</sup> <sup>157</sup> <sup>158</sup> <sup>159</sup> <sup>160</sup> <sup>161</sup> <sup>162</sup> <sup>163</sup> <sup>164</sup> <sup>165</sup> <sup>166</sup> <sup>167</sup> <sup>168</sup> <sup>169</sup> <sup>170</sup> <sup>171</sup> <sup>172</sup> <sup>173</sup> <sup>174</sup> <sup>175</sup> <sup>176</sup> <sup>177</sup> <sup>178</sup> <sup>179</sup> <sup>180</sup> <sup>181</sup> <sup>182</sup> <sup>183</sup> <sup>184</sup> <sup>185</sup> <sup>186</sup> <sup>187</sup> <sup>188</sup> <sup>189</sup> <sup>190</sup> <sup>191</sup> <sup>192</sup> <sup>193</sup> <sup>194</sup> <sup>195</sup> <sup>196</sup> <sup>197</sup> <sup>198</sup> <sup>199</sup> <sup>200</sup> <sup>201</sup> <sup>202</sup> <sup>203</sup> <sup>204</sup> <sup>205</sup> <sup>206</sup> <sup>207</sup> <sup>208</sup> <sup>209</sup> <sup>210</sup> <sup>211</sup> <sup>212</sup> <sup>213</sup> <sup>214</sup> <sup>215</sup> <sup>216</sup> <sup>217</sup> <sup>218</sup> <sup>219</sup> <sup>220</sup> <sup>221</sup> <sup>222</sup> <sup>223</sup> <sup>224</sup> <sup>225</sup> <sup>226</sup> <sup>227</sup> <sup>228</sup> <sup>229</sup> <sup>230</sup> <sup>231</sup> <sup>232</sup> <sup>233</sup> <sup>234</sup> <sup>235</sup> <sup>236</sup> <sup>237</sup> <sup>238</sup> <sup>239</sup> <sup>240</sup> <sup>241</sup> <sup>242</sup> <sup>243</sup> <sup>244</sup> <sup>245</sup> <sup>246</sup> <sup>247</sup> <sup>248</sup> <sup>249</sup> <sup>250</sup> <sup>251</sup> <sup>252</sup> <sup>253</sup> <sup>254</sup> <sup>255</sup> <sup>256</sup> <sup>257</sup> <sup>258</sup> <sup>259</sup> <sup>260</sup> <sup>261</sup> <sup>262</sup> <sup>263</sup> <sup>264</sup> <sup>265</sup> <sup>266</sup> <sup>267</sup> <sup>268</sup> <sup>269</sup> <sup>270</sup> <sup>271</sup> <sup>272</sup> <sup>273</sup> <sup>274</sup> <sup>275</sup> <sup>276</sup> <sup>277</sup> <sup>278</sup> <sup>279</sup> <sup>280</sup> <sup>281</sup> <sup>282</sup> <sup>283</sup> <sup>284</sup> <sup>285</sup> <sup>286</sup> <sup>287</sup> <sup>288</sup> <sup>289</sup> <sup>290</sup> <sup>291</sup> <sup>292</sup> <sup>293</sup> <sup>294</sup> <sup>295</sup> <sup>296</sup> <sup>297</sup> <sup>298</sup> <sup>299</sup> <sup>300</sup> <sup>301</sup> <sup>302</sup> <sup>303</sup> <sup>304</sup> <sup>305</sup> <sup>306</sup> <sup>307</sup> <sup>308</sup> <sup>309</sup> <sup>310</sup> <sup>311</sup> <sup>312</sup> <sup>313</sup> <sup>314</sup> <sup>315</sup> <sup>316</sup> <sup>317</sup> <sup>318</sup> <sup>319</sup> <sup>320</sup> <sup>321</sup> <sup>322</sup> <sup>323</sup> <sup>324</sup> <sup>325</sup> <sup>326</sup> <sup>327</sup> <sup>328</sup> <sup>329</sup> <sup>330</sup> <sup>331</sup> <sup>332</sup> <sup>333</sup> <sup>334</sup> <sup>335</sup> <sup>336</sup> <sup>337</sup> <sup>338</sup> <sup>339</sup> <sup>340</sup> <sup>341</sup> <sup>342</sup> <sup>343</sup> <sup>344</sup> <sup>345</sup> <sup>346</sup> <sup>347</sup> <sup>348</sup> <sup>349</sup> <sup>350</sup> <sup>351</sup> <sup>352</sup> <sup>353</sup> <sup>354</sup> <sup>355</sup> <sup>356</sup> <sup>357</sup> <sup>358</sup> <sup>359</sup> <sup>360</sup> <sup>361</sup> <sup>362</sup> <sup>363</sup> <sup>364</sup> <sup>365</sup> <sup>366</sup> <sup>367</sup> <sup>368</sup> <sup>369</sup> <sup>370</sup> <sup>371</sup> <sup>372</sup> <sup>373</sup> <sup>374</sup> <sup>375</sup> <sup>376</sup> <sup>377</sup> <sup>378</sup> <sup>379</sup> <sup>380</sup> <sup>381</sup> <sup>382</sup> <sup>383</sup> <sup>384</sup> <sup>385</sup> <sup>386</sup> <sup>387</sup> <sup>388</sup> <sup>389</sup> <sup>390</sup> <sup>391</sup> <sup>392</sup> <sup>393</sup> <sup>394</sup> <sup>395</sup> <sup>396</sup> <sup>397</sup> <sup>398</sup> <sup>399</sup> <sup>400</sup> <sup>401</sup> <sup>402</sup> <sup>403</sup> <sup>404</sup> <sup>405</sup> <sup>406</sup> <sup>407</sup> <sup>408</sup> <sup>409</sup> <sup>410</sup> <sup>411</sup> <sup>412</sup> <sup>413</sup> <sup>414</sup> <sup>415</sup> <sup>416</sup> <sup>417</sup> <sup>418</sup> <sup>419</sup> <sup>420</sup> <sup>421</sup> <sup>422</sup> <sup>423</sup> <sup>424</sup> <sup>425</sup> <sup>426</sup> <sup>427</sup> <sup>428</sup> <sup>429</sup> <sup>430</sup> <sup>431</sup> <sup>432</sup> <sup>433</sup> <sup>434</sup> <sup>435</sup> <sup>436</sup> <sup>437</sup> <sup>438</sup> <sup>439</sup> <sup>440</sup> <sup>441</sup> <sup>442</sup> <sup>443</sup> <sup>444</sup> <sup>445</sup> <sup>446</sup> <sup>447</sup> <sup>448</sup> <sup>449</sup> <sup>450</sup> <sup>451</sup> <sup>452</sup> <sup>453</sup> <sup>454</sup> <sup>455</sup> <sup>456</sup> <sup>457</sup> <sup>458</sup> <sup>459</sup> <sup>460</sup> <sup>461</sup> <sup>462</sup> <sup>463</sup> <sup>464</sup> <sup>465</sup> <sup>466</sup> <sup>467

User: Can you help me check my website?

Assistant:Assistant:Assistant:Sure, send me the URL and I'll start the check.

User: It's www.example.com. [THINK]

Assistant:Assistant:Got it, connecting to the server for $ ^{^} $ verification.

User: Yeah.

Assistant:Assistant:May take a moment to load the page snapshot.

Assistant:Assistant:<The site is not fetching real-time data; likely a network or server response issue.>Sorry, can't fetch real-time data from this site—probably a network issue. Let me try again... Still can't connect. Server response seems to be the problem.

User: Why won't it connect? Just tell me how to fix it.

Assistant:Assistant:Got it. Use responsive design and compress images for faster mobile loading.

11


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Token</td><td style='text-align: center; word-wrap: break-word;'>Turn</td><td style='text-align: center; word-wrap: break-word;'>Semantics</td><td style='text-align: center; word-wrap: break-word;'>Placement</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>[THINK]</td><td style='text-align: center; word-wrap: break-word;'>User</td><td style='text-align: center; word-wrap: break-word;'>Triggers S2 to begin background reasoning.</td><td style='text-align: center; word-wrap: break-word;'>End of the user utterance that requires external reasoning.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>&lt;. . . &gt;</td><td style='text-align: center; word-wrap: break-word;'>Assistant</td><td style='text-align: center; word-wrap: break-word;'>Injects a complete S2 result fragment before the corresponding fact.</td><td style='text-align: center; word-wrap: break-word;'>Before the relevant assistant sentence; never as the first token after a user turn.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>^</td><td style='text-align: center; word-wrap: break-word;'>Assistant</td><td style='text-align: center; word-wrap: break-word;'>Marks the character offset where the next speaker begins.</td><td style='text-align: center; word-wrap: break-word;'>Inside the assistant text at the overlap onset; agent cannot trigger user or itself.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>[CUT]</td><td style='text-align: center; word-wrap: break-word;'>Assistant</td><td style='text-align: center; word-wrap: break-word;'>Marks where assistant audio stops; following text is ghost text.</td><td style='text-align: center; word-wrap: break-word;'>2–4 characters after ^; omitted for pure backchannel overlap.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>[WAIT]</td><td style='text-align: center; word-wrap: break-word;'>User</td><td style='text-align: center; word-wrap: break-word;'>Suspends and resets the ongoing S2 reasoning process.</td><td style='text-align: center; word-wrap: break-word;'>End of the interrupting user turn; a new [THINK] is required to resume.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>[PENDNS]</td><td style='text-align: center; word-wrap: break-word;'>User</td><td style='text-align: center; word-wrap: break-word;'>Encodes N seconds of shared silence ( $ N = 1–35 $).</td><td style='text-align: center; word-wrap: break-word;'>Start of the user turn that resumes after the silence; forbidden in assistant turns.</td></tr></table>

<div style="text-align: center;">Table 4: Complete set of Director annotation tokens. Ghost text (after [CUT]) preserves what the assistant intended but did not utter.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Interaction Pattern</td><td style='text-align: center; word-wrap: break-word;'>Occurrence (%)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Delayed reasoning ([THINK] + S2 fragments)</td><td style='text-align: center; word-wrap: break-word;'>94.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Shared silence ([PENDS])</td><td style='text-align: center; word-wrap: break-word;'>68.2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Assistant-initiated turn</td><td style='text-align: center; word-wrap: break-word;'>50.0</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Overlapping speech (^ + [CUT])</td><td style='text-align: center; word-wrap: break-word;'>49.8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Interruption with reset ([CUT] + [WAIT])</td><td style='text-align: center; word-wrap: break-word;'>41.9</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Pure backchannel (^ without [CUT])</td><td style='text-align: center; word-wrap: break-word;'>3.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Samples containing ≥2 patterns</td><td style='text-align: center; word-wrap: break-word;'>90.7</td></tr></table>

<div style="text-align: center;">Table 5: Proportion of training samples containing each interaction pattern. Categories are non-exclusive; 90.7% of samples exhibit two or more patterns simultaneously.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Scenario Type</td><td style='text-align: center; word-wrap: break-word;'>Ratio (%)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Step-by-step guidance</td><td style='text-align: center; word-wrap: break-word;'>32.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Standard turn-taking</td><td style='text-align: center; word-wrap: break-word;'>31.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Condition revision</td><td style='text-align: center; word-wrap: break-word;'>18.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Troubleshooting guidance</td><td style='text-align: center; word-wrap: break-word;'>13.9</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Extended listening</td><td style='text-align: center; word-wrap: break-word;'>4.4</td></tr></table>

<div style="text-align: center;">Table 6: Distribution of primary interaction types in DuplexOmni scenario seeds. The distribution is intentionally diversified to expose the model to different temporal structures and improve robustness under continuous real-time interaction.</div>


Example 3: Delayed thinking feedback with shared silence. The user shifts the question mid-task ([WAIT][THINK]) and twice falls silent before continuing ([PEND2S], [PEND3S]). S2 returns two short fragments in sequence, reflecting the “small-chunk” delivery mode. When the user corrects a factual error, a new [THINK] re-queries S2, and the assistant acknowledges the mistake.

User: Hey, you busy? Got a quick question—heard of a book called Young Soul Rebels?


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Statistic</td><td style='text-align: center; word-wrap: break-word;'>Value</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Total scenario seeds</td><td style='text-align: center; word-wrap: break-word;'>~620K</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Total raw conversations</td><td style='text-align: center; word-wrap: break-word;'>~3.02M</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Average turns per sample</td><td style='text-align: center; word-wrap: break-word;'>10.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Turn range</td><td style='text-align: center; word-wrap: break-word;'>4-33</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>S2 participation: high</td><td style='text-align: center; word-wrap: break-word;'>23.6%</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>S2 participation: medium</td><td style='text-align: center; word-wrap: break-word;'>46.0%</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>S2 participation: low</td><td style='text-align: center; word-wrap: break-word;'>24.9%</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>S2 participation: off</td><td style='text-align: center; word-wrap: break-word;'>5.5%</td></tr></table>

<div style="text-align: center;">Table 7: Key statistics of the DuplexOmni training corpus after Writer-Director annotation.</div>


##### [THINK]

Assistant:Assistant:

Assistant:

Assistant:I'm free. About this book, I'll answer in two parts: main content first, then social context. Just a moment while I check the database.

User: [PEND2S] Wait, skip the summary. I just want to know why Northern Soul rose—especially the drug culture part. Is that really detailed in the book? [THINK]

Assistant:Assistant:Got it. I'll recheck the key sections, focusing on drug culture. It'll take a moment.

12

User: [PEND3S] Fine, hurry up. Nothing vague this time.

Assistant:Assistant:Found it.

Assistant:<The book mentions that dancers in the 1970s used amphetamines to dance all night, prompting police raids on nightclubs. The book mentions dancers used amphetamines to dance all night in the '70s, leading police to raid clubs.

Assistant:Assistant:<The Twisted Wheel club in Manchester was raided.>For example, Manchester's Twisted Wheel Club got raided.

User: Twisted Wheel? I thought the Wigan Casino was more famous. Did you mix them up? [THINK]

Assistant:Assistant:Sorry, I was going on an initial search. Since you mentioned Wigan Casino, let me double-check.

Assistant:Assistant:<The Wigan Casino was frequently raided due to overcrowding and drug use. You're right—the Wigan Casino has been raided multiple times over crowd and drug issues. The earlier info was inaccurate.

Example 4: Assistant-initiated outbound dialogue. The assistant opens the conversation proactively. The user's first turn includes a two-second silence ([PEND2S]) reflecting a natural phone pick-up delay, followed by a one-second pause later in the call ([PEND1S]). A [THINK] near the end triggers S2 to look up real-time availability, with the result delivered as a single <...> fragment after a brief holding phrase.

Assistant:Assistant:Hi, this is London Floral School. We noticed you're interested in flower design—just a quick intro to our flexible courses, from beginner to expert.

User: [PEND2S] Hey, I was just looking at flower shop pics. Does your school have programs for different experience levels?

Assistant:Assistant:Our classes are fully flexible—book anytime. Whether you're a total beginner or looking to improve, we've got the right course. With 16 years of teaching experience, many graduates have opened their own flower shops.

User: Sounds good. Any special resources during the program?

Assistant:Assistant:<Fresh flower wholesale market on site; students practice with flowers imported directly from Dutch growers and auctions.>Our biggest advantage is a live wholesale market on campus. Students pick fresh flowers for practice without going out early to buy them—all sourced directly from Dutch growers and auctions.

User: That's really convenient. I'm especially interested in wedding floral design. Do you teach actual wedding setups?

Assistant:Assistant:Sure, our wedding floristry class is super popular. We cover bridal bouquets, table centerpieces, and trendy wedding arches—you'll learn structure and secure arrangement techniques.

User: [PEND1S] The flower arch sounds great, but I'm pretty busy. How long does this course take?

Assistant:Assistant:Don't worry—we know time is precious. The wedding floristry course is modular; learn on weekends or evenings at your own pace.

User: Good. I'm only free weekends next month. Can you check if there are classes then? I'd like to decide soon.

Assistant:Assistant:Sure, just a moment while I check next month's weekend schedule. [THINK]

Assistant:Assistant:Sorry to keep you waiting. <Weekend class sessions on the 12th and 19th next month still have availability.>Got it—there are weekend classes on the 12th and 19th next month, and spots are still open. I can hold one for you and send the detailed outline to your phone shortly.

### C Scenario Distribution and Data Statistics

### C.1 Interaction Pattern Distribution

Each training sample is annotated by the Director with one or more temporal control tokens. Because a single dialogue commonly exhibits multiple interaction phenomena—for example, a conversation may contain both an interruption and a shared silence—the categories below are not mutually exclusive. Table 5 reports the proportion of training samples that contain each pattern.

### C.2 Scenario Seed Distribution

Beyond token-level statistics, each sample is seeded with a primary interaction type that determines the overall dialogue structure. Table 6 shows the distribution of primary interaction types across the scenario seeds.

### C.3 Additional Data Statistics

Table 7 summarizes key statistics of the annotated training corpus.

AI contributed to the polishing of this paper.

13