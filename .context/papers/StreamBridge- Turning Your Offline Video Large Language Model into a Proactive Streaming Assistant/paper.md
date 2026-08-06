arXiv:2505.05467v2 [cs.CV] 18 Sep 2025

# StreamBridge: Turning Your Offline Video Large Language Model into a Proactive Streaming Assistant

Haibo Wang$^{1,2*}$, Bo Feng$^{1\circ}$, Zhengfeng Lai$^{1\circ}$, Mingze Xu$^{1\circ}$, Shiyu Li$^{1\circ}$, Weifeng Ge$^{2}$, Afshin Dehghan$^{1\dagger}$, Meng Cao$^{1\dagger}$, Ping Huang$^{1\dagger}$, $^{1}$Apple $^{2}$ Fudan University

hibwang@ucdavis.edu

{bfeng2, jeff_lai, mingze_xu2, shiyu_li}@apple.com

{adehghan, mengcao, huang_ping}@apple.com

First author; $^{\circ}$Core contributors; Senior authors

## Abstract

We present StreamBridge, a simple yet effective framework that seamlessly transforms offline Video-LLMs into streaming-capable models. It addresses two fundamental challenges in adapting existing models into online scenarios: (1) limited capability for multi-turn real-time understanding, and (2) lack of proactive response mechanisms. Specifically, StreamBridge incorporates (1) a memory buffer combined with a round-decayed compression strategy, supporting long-context multi-turn interactions, and (2) a decoupled, lightweight activation model that can be effortlessly integrated into existing Video-LLMs, enabling continuous proactive responses. To further support StreamBridge, we construct Stream-IT, a large-scale dataset tailored for streaming video understanding, featuring interleaved video-text sequences and diverse instruction formats. Extensive experiments show that StreamBridge significantly improves the streaming understanding capabilities of offline Video-LLMs across various tasks, outperforming even proprietary models such as GPT-4o and Gemini 1.5 Pro. Simultaneously, it achieves competitive or superior performance on standard video understanding benchmarks.

## 1 Introduction

Video Large Language Models (Video-LLMs) [1; 2; 3; 4; 5] typically process entire pre-recorded videos at once. However, emerging applications, such as robotics [6; 7] and autonomous driving [8; 9], require causal perception and interpretation of visual information online. This fundamental mismatch highlights a critical limitation of current Video-LLMs, as they are not inherently equipped to operate in streaming scenarios where timely understanding and responsiveness are paramount.

Figure 1 highlights two representative patterns in streaming video understanding, which also correspond to the key challenges in adapting Video-LLMs from offline to streaming scenarios: (1) multi-turn real-time understanding and (2) proactive response generation. The first pattern involves multi-turn interactions, where the assistant receives user queries at different timestamps. In each turn, while keeping accumulated visual and conversational context as historical information, the model should focus on the most recent video segment. The second pattern emphasizes more human-like, proactive behaviors. Rather than passively waiting for user prompts, the model actively monitors the visual stream and generates timely outputs based on unfolding content. For instance, in Figure 1 (bottom), the assistant provides step-by-step guidance as the drawing progresses without being explicitly asked, simulating continuous support in dynamic environments.

 $ ^{*} $Work done during Haibo's internship at Apple.

39th Conference on Neural Information Processing Systems (NeurIPS 2025).

<div style="text-align: center;"><img src="imgs/img_in_image_box_213_144_1006_587.jpg" alt="Image" width="64%" />

What is going on?
USER

Where is this?
USER

What is written on the sign?
USER

A helicopter is flying over a mountain.

You are in an airplane with rows of seats.

"Change the direction of all escalators and travelators".

How do I draw this picture?
USER

Incoming Frames
Draw a house and a tree.
Draw a sun and two clouds.
Color the sun blue and the clouds green.

</div>


<div style="text-align: center;">Figure 1: Illustration of streaming scenarios. Top: Multi-turn interactions. User issues queries at different timestamps, with each turn involving a new video segment along with accumulated visual and text history. Bottom: Proactive responses. The assistant actively delivers timely feedback or guidance based on the incoming visual stream, without requiring explicit user prompts.</div>


To bridge the gap between offline and streaming video understanding, we introduce StreamBridge, a simple yet effective framework that seamlessly transforms pre-trained offline Video-LLMs into streaming-capable models. In contrast to prior efforts [10; 11; 12; 13], which train streaming models from scratch but fall behind on offline video tasks, StreamBridge leverages the strong generalization capabilities of existing Video-LLMs without requiring full retraining. This approach allows developers to directly benefit from the rich world knowledge and linguistic fluency of large-scale pre-trained models, while incurring only minimal additional computational cost and data requirements. Concretely, StreamBridge introduces a memory buffer to manage incoming video frames, coupled with a round-decayed compression strategy that merges earlier frame tokens while preserving recent ones, enabling the model to support long-context, multi-modal, and multi-turn interactions in streaming scenarios. For proactive capabilities, instead of modifying the base model architecture [14] or introducing streaming-specific objectives [12], both of which can lead to optimization conflicts and issues like probability correction [10], StreamBridge adopts a modular design, by decoupling the proactive capability from the main Video-LLM via a compact activation model. This plug-and-play component operates in parallel with the main Video-LLM, enabling proactive behavior in a flexible and non-intrusive manner while fully preserving the main Video-LLM's language fluency and general video understanding capabilities.

To further support StreamBridge, we construct Stream-IT, a large-scale dataset tailored for streaming scenarios. Stream-IT captures diverse real-time questions and proactive responses embedded within multi-turn video interactions, featuring interleaved video-text sequences. While existing datasets primarily focus on single-turn question answering [15; 16] or short-form video captioning [17; 18; 19], Stream-IT fills a critical gap by enabling temporally extended, interactive video understanding. It is constructed by concatenating semantically related short clips from large-scale video-caption corpora, followed by the generation of multi-turn QA sequences that simulate realistic, time-sensitive user interactions. Moreover, Stream-IT incorporates a broad spectrum of task formats sourced from public datasets, thereby boosting task diversity and promoting model generalization in streaming settings.

By integrating our StreamBridge framework and fine-tuning on Stream-IT, we successfully convert several leading offline Video-LLMs, including LLaVA-OV [3], Oryx-1.5 [1], and Qwen2-VL [2], into streaming-capable assistants. Extensive experiments demonstrate that our models achieve state-of-the-art performance on streaming benchmarks such as OVO-Bench [20] and Streaming-Bench [21], outperforming even proprietary models like GPT-4o [22] and Gemini 1.5 Pro [23], while retaining or exceeding performance on conventional offline video understanding tasks [24; 25; 26; 27; 28; 29].

2

## 2 Related Work

Video Large Language Models. With the rapid advancement of Multimodal Large Language Models (MLLMs) [30; 3; 31; 32; 2], Video-LLMs [33; 34; 35; 36; 15; 37; 38] have gained increasing attention for general video understanding. Typically, these models comprise a visual encoder [39; 40; 1] for extracting frame-level representations, a modality projector (e.g., MLP [41] and Q-former [30]) to map visual features into the language space, and an LLM [42; 43] to generate contextual responses. While achieving strong results on standard video benchmarks [25; 29; 27], these models are inherently designed for static, offline settings where the entire video is pre-recorded and fully accessible at inference time. As a result, they struggle in streaming environments, where video frames arrive sequentially and require real-time, temporally coherent, or even proactive responses. Our work aims to bridge this gap by augmenting offline Video-LLMs with streaming capabilities.

Streaming Video Understanding. Typical tasks in streaming video understanding, such as action recognition [44; 45; 46; 47] and anticipation [48; 49], causally process video inputs using only past and current observations. Recent efforts [50; 12; 13; 51] focus on building Video-LLMs capable of real-time conversation, generating timely responses throughout a live video stream. VideoLLM Online [10] and Flash-VStream [11] introduce specialized online objectives and memory architectures to handle sequential inputs. MMDuet [14] and ViSpeak [52] add dedicated heads to facilitate proactive response generation. To benchmark streaming video capabilities, several evaluation suites have been proposed, including StreamingBench [21], StreamBench [53], SVBench [54], OmniMMI [55], and OVO-Bench [20]. In contrast to previous approaches that retain models or tightly couple proactive mechanisms within the backbone, our work leverages the strong generalization abilities of pre-trained offline Video-LLMs [1; 3; 2]. We propose an efficient adaptation framework, combined with a dedicated fine-tuning dataset, to endow these models with streaming capabilities. Furthermore, observing that embedding the activation function into the main model often lead to optimization conflicts and performance degradation [10; 14], we advocate a modular, decoupled design. Our method introduces a compact, plug-and-play activation model that enables proactive behaviors efficiently and non-intrusively. We also provide additional discussions on how our work relates to the ReKV [56], VideoStreaming [57], and StreamChat [53] in the Appendix F.

## 3 Methodology

### 3.1 Preliminary Analysis

Streaming video understanding involves interleaved video-text inputs. From an input perspective, streaming scenarios can be broadly categorized into two representative formats:

- Multi-turn dialogue with interleaved video-text. In this setting, the input sequence is in the form of ‘<V_1><Q_1><A_1>, <V_2><Q_2><A_2>, \cdots’, where <V_i>, <Q_i>, and <A_i> denote the video clip, user query, and assistant answer in the i-th round. Crucially, there is no delay between <Q_i> and <A_i>, reflecting the need for immediate responses. This format closely resembles the live interaction in dynamic environments, as shown in Figure 1 (Top).

- Proactive output. The assistant answers after watching an incoming video stream, often without an explicit user query at the response time. The input can be structured as ‘<Q> <V1> <A1> <V2> <A2> · · ·’, where <Q> represents an initial prompt (e.g., “Guide me through the task”), and the model must proactively determine when and how to respond based on the incoming video contents. This scenario requires the ability to continuously monitor evolving context and trigger responses at appropriate moments. Figure 1 (Bottom) is an example of proactive responses.

Recent benchmarks such as OVO-Bench [20] and Streaming-Bench [21] attempt to evaluate these capabilities by constructing multi-turn interleaved video-text dialogues. However, due to the limited input length and the lack of streaming support in current Video-LLMs, these benchmarks necessarily simplify the problem. Specifically, they segment a complete long video into multiple isolated clips aligned with each query timestamp. For a query  $ <Q_i> $ at time  $ t_i $, the visual input is restricted to the uniformly sampled frames under segment  $ \tilde{V}_{[0:t_i]} $, and prior dialogue history is completely discarded. As a result, the multi-turn streaming scenario is reduced to a series of independent, single-turn offline tasks. To address these limitations, we propose StreamBridge, a general framework designed to introduce the actual streaming setup to existing offline Video-LLMs.

3

<div style="text-align: center;"><img src="imgs/img_in_image_box_215_143_1007_569.jpg" alt="Image" width="64%" />

Observed Frames Incoming Frames

#3

(2)

a query Q is
posed at #3 (#4, #5)

Frame
Encoder

Frame
Encoder

if True
at #6

if True
at #6

Round-Decayed Compression (optional)
Large Language Model

</div>


<div style="text-align: center;">Figure 2: Overview of StreamBridge. ①③: Incoming frames are encoded and stored into the memory buffer one by one. ②: A query Q is posed. ④: The activation model monitors incoming frames and returns a binary signal D, indicating whether LLM should start answering. × means concatenation.</div>


### 3.2 StreamBridge

As shown in Figure 2 and Algorithm 1, in addition to the frame encoder  $ \mathcal{I}(\cdot) $ and the large language model  $ \mathcal{LLM}(\cdot) $, StreamBridge proposes three key components to enable streaming capabilities: (1) a memory buffer responsible for storing and retrieving frame tokens over time, (2) a round-decayed compression strategy  $ \mathcal{COM}(\cdot) $ that efficiently prunes redundant tokens from earlier rounds while preserving the most recent context, and (3) a compact activation model  $ \mathcal{ACT}(\cdot) $ that enables proactive responses by making frame-level decisions on when to generate outputs.

#### 3.2.1 Memory Buffer

In streaming scenarios where video frames arrive sequentially, we adopt a memory buffer  $ \mathcal{MB} $ to store both visual and textual embeddings. As illustrated in Figure 2, each incoming frame is independently encoded and appended to the buffer alongside any associated query embeddings. Conceptually,  $ \mathcal{MB} $ operates under a producer-consumer paradigm: the encoder  $ \mathcal{I}(\cdot) $ functions as the producer, continuously generating frame-level features, while the language model  $ \mathcal{LLM}(\cdot) $ serves as the consumer, retrieving the accumulated embeddings to generate a response upon receiving a user query. Formally, as detailed in Algorithm 1, at each time step  $ t $, the incoming frame  $ F_t $ is first processed by  $ \mathcal{I}(\cdot) $, and the resulting embeddings are stored in the memory buffer  $ \mathcal{MB} $ (Algorithm 1, line 4). Upon the arrival of a user query  $ Q $ and a positive activation decision  $ \mathcal{D} $, the buffer content, including both visual and textual embeddings, is flattened into a single sequence of input embeddings, which is then fed into  $ \mathcal{LLM}(\cdot) $ for response generation (Algorithm 1, line 13-16). Once a response  $ \mathcal{R} $ is produced, it is also appended to the memory buffer (Algorithm 1, line 17), enabling the model to preserve temporal continuity and maintain a complete history of multi-turn video-text interactions.

#### 3.2.2 Round-Decayed Compression

Online scenarios often involve long, even infinite video streaming, which can lead to significant memory usage and inference latency. Therefore, we propose a round-decayed token compression strategy tailored for multi-turn streaming settings. Specifically, we pre-define a maximum allowable embedding length MaxLen for the model input. Before each response generation, the model checks whether the current input embedding exceeds MaxLen. If so, we apply a round-decayed token merging strategy: starting from the earliest dialogue rounds, visual tokens are progressively merged frame-by-frame, until the total length falls below MaxLen. The merging is implemented via average

4

Algorithm 1: StreamBridge Framework

1 Inputs: incoming frames  $ [F_1, F_2, \ldots, F_t, \ldots] $;
2 Initializations:  $ \mathcal{I}(\cdot) $,  $ \mathcal{LLM}(\cdot) $,  $ \mathcal{ACT}(\cdot) $,  $ \mathcal{COM}(\cdot) $,  $ \mathcal{MB} = [\cdot] $, MaxLen,  $ t_{Q} $=None;
3 while  $ F_t $ do
4  $ \mathcal{MB} \leftarrow \mathcal{I}(F_t) $; // store the frame feature  $ \mathcal{I}(F_t) $ into the Memory Buffer
5 if  $ Q $ at timestamp  $ t $ then
6  $ \mathcal{MB} \leftarrow Q $
7  $ t_{Q} \leftarrow t $; //  $ t_{Q} $ is the timestamp when  $ Q $ is posed
8 if  $ t_{Q} $ is not None then
9  $ \mathcal{D} \leftarrow \mathcal{ACT}(Q, F_{t_{Q}:t-1}, F_t) $; //  $ \mathcal{D} $ denotes whether response or not at timestamp  $ t $
10 else
11  $ \mathcal{D} \leftarrow $ False; // not response if there is no  $ Q $
12 if  $ \mathcal{D} $ then
13 //  $ \mathcal{D} $ is true at timestamp  $ t $, and should return a response  $ \mathcal{R} $
14 InputEmbeds  $ \leftarrow $ Flatten( $ \mathcal{MB} $)
15 if Len(InputEmbeds) > MaxLen then
16  $ \mathcal{L} $ InputEmbeds  $ \leftarrow $  $ \mathcal{COM} $(InputEmbeds); // compress redundant visual tokens
17  $ \mathcal{R} \leftarrow \mathcal{LLM} $(InputEmbeds); // return a response  $ \mathcal{R} $
18  $ \mathcal{MB} \leftarrow \mathcal{R} $; // update  $ \mathcal{MB} $
19  $ t \leftarrow 1 $; // receive subsequent frames

pooling [58] over adjacent frame tokens. This strategy ensures that the most recent visual context is retained with minimal distortion, thus maintaining the precision of real-time responses while not fully discarding historical visual contexts. At the same time, it significantly improves memory efficiency and reduces inference overhead as in Figure 4. This process is encapsulated in the compression function  $ \text{COM}(\cdot) $ in Algorithm 1 (line 15). The detailed pseudo codes can be found in Appendix I.

#### 3.2.3 A Plug-and-play Activation Model

To enable proactive responses in streaming Video-LLMs, we decouple the activation function from the main Video-LLM. Unlike prior methods that tightly integrate activation mechanisms into the LLM [10; 12; 14; 52], our framework avoids potential interference with the language modeling capacity of the main

<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Time Interval</th><th style='text-align: center;'>Activation Model (LLaVA-OV-0.5B)</th><th style='text-align: center;'><ACT> token</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>0 - 1</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>1 - 2</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>2 - 3</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>3 - 4</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>4 - 5</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>5 - 6</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>6 - 7</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>7 - 8</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>8 - 9</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>9 - 10</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>10 - 11</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>11 - 12</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>12 - 13</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>13 - 14</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>14 - 15</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>15 - 16</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>16 - 17</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>17 - 18</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>18 - 19</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>19 - 20</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>20 - 21</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>21 - 22</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>22 - 23</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>23 - 24</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>24 - 25</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>25 - 26</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>26 - 27</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>27 - 28</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>28 - 29</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>29 - 30</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>30 - 31</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>31 - 32</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>32 - 33</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>33 - 34</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>34 - 35</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>35 - 36</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>36 - 37</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>37 - 38</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>38 - 39</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>39 - 40</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>40 - 41</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>41 - 42</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>42 - 43</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>43 - 44</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>44 - 45</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>45 - 46</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>46 - 47</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>47 - 48</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>48 - 49</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>49 - 50</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>50 - 51</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>51 - 52</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>52 - 53</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>53 - 54</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>54 - 55</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>55 - 56</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>56 - 57</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>57 - 58</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>58 - 59</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>59 - 60</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>60 - 61</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>61 - 62</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>62 - 63</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>63 - 64</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>64 - 65</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>65 - 66</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>66 - 67</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>67 - 68</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>68 - 69</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>69 - 70</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>70 - 71</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>71 - 72</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>72 - 73</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>73 - 74</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>74 - 75</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>75 - 76</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>76 - 77</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>77 - 78</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>78 - 79</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>79 - 80</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>80 - 81</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>81 - 82</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>82 - 83</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>83 - 84</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>84 - 85</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>85 - 86</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>86 - 87</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>87 - 88</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>88 - 89</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>89 - 90</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>90 - 91</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>91 - 92</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>92 - 93</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>93 - 94</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>94 - 95</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>95 - 96</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>96 - 97</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>97 - 98</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>98 - 99</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>99 - 100</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>100 - 101</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>101 - 102</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>102 - 103</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>103 - 104</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>104 - 105</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>105 - 106</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>106 - 107</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>107 - 108</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>108 - 109</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>109 - 110</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>110 - 111</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>111 - 112</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>112 - 113</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>113 - 114</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>114 - 115</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>115 - 116</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>116 - 117</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>117 - 118</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>118 - 119</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>119 - 120</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>120 - 121</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>121 - 122</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>122 - 123</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>123 - 124</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>124 - 125</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>125 - 126</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>126 - 127</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>127 - 128</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>128 - 129</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>129 - 130</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>130 - 131</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>131 - 132</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>132 - 133</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>133 - 134</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>134 - 135</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>135 - 136</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>136 - 137</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>137 - 138</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>138 - 139</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>139 - 140</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>140 - 141</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>141 - 142</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>142 - 143</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>143 - 144</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>144 - 145</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>145 - 146</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>146 - 147</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>147 - 148</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>148 - 149</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>149 - 150</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>150 - 151</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>151 - 152</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>152 - 153</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>153 - 154</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>154 - 155</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>155 - 156</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>156 - 157</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>157 - 158</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>158 - 159</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>159 - 160</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>160 - 161</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>161 - 162</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>162 - 163</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>163 - 164</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>164 - 165</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>165 - 166</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>166 - 167</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>167 - 168</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>168 - 169</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>169 - 170</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>170 - 171</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>171 - 172</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>172 - 173</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>173 - 174</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>174 - 175</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>175 - 176</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>176 - 177</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>177 - 178</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>178 - 179</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>179 - 180</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>180 - 181</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>181 - 182</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>182 - 183</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>183 - 184</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>184 - 185</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>185 - 186</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>186 - 187</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>187 - 188</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>188 - 189</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>189 - 190</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>190 - 191</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>191 - 192</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>192 - 193</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>193 - 194</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>194 - 195</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>195 - 196</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>196 - 197</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>197 - 198</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>198 - 199</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>199 - 200</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>200 - 201</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>201 - 202</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>202 - 203</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>203 - 204</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>204 - 205</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>205 - 206</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>206 - 207</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>207 - 208</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>208 - 209</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>209 - 210</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>210 - 211</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>211 - 212</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>212 - 213</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>213 - 214</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>214 - 215</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>215 - 216</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>216 - 217</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>217 - 218</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>218 - 219</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>219 - 220</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>220 - 221</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>221 - 222</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>222 - 223</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>223 - 224</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>224 - 225</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>225 - 226</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>226 - 227</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>227 - 228</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>228 - 229</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>229 - 230</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>230 - 231</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>231 - 232</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>232 - 233</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>233 - 234</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>234 - 235</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>235 - 236</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>236 - 237</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>237 - 238</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>238 - 239</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>239 - 240</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>240 - 241</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>241 - 242</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>242 - 243</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>243 - 244</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>244 - 245</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>245 - 246</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>246 - 247</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>247 - 248</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>248 - 249</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>249 - 250</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>250 - 251</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>251 - 252</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>252 - 253</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>253 - 254</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>254 - 255</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>255 - 256</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>256 - 257</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>257 - 258</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>258 - 259</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>259 - 260</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>260 - 261</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>261 - 262</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>262 - 263</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>263 - 264</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>264 - 265</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>265 - 266</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>266 - 267</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>267 - 268</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>268 - 269</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>269 - 270</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>270 - 271</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>271 - 272</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>272 - 273</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>273 - 274</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>274 - 275</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>275 - 276</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>276 - 277</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>277 - 278</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>278 - 279</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>279 - 280</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>280 - 281</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>281 - 282</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>282 - 283</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>283 - 284</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>284 - 285</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>285 - 286</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>286 - 287</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>287 - 288</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>288 - 289</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>289 - 290</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>290 - 291</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>291 - 292</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>292 - 293</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>293 - 294</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>294 - 295</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>295 - 296</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>296 - 297</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>297 - 298</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>298 - 299</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>299 - 300</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>300 - 301</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>301 - 302</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>302 - 303</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>303 - 304</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>304 - 305</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>305 - 306</td><td style='text-align: center;'>0</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>306 - 3</td></tr>
  </tbody>
</table>

<div style="text-align: center;">Figure 3: An overview of the proposed activation model. We label the last  $ P\% $ of frames of each video clip to be true during training.</div>


Video-LLM. Specifically, we propose a parallel pipeline, where a compact external MLLM (e.g., LLaVA-OV-0.5B [3]) is used as an independent activation model, denoted as  $ \mathcal{ACT}(\cdot) $. As shown in Algorithm 1 (line 9), upon receiving each new frame, the framework simultaneously forwards the current frame (along with the user query Q and optionally previous frames) to  $ \mathcal{ACT}(\cdot) $ to determine whether a response should be generated. If the activation signal  $ \mathcal{D} $ is positive, the buffered embeddings are sent to the LLM for decoding. This design ensures high flexibility and compatibility. Furthermore, in real-time deployment, the  $ \mathcal{ACT}(\cdot) $, the frame encoder  $ \mathcal{I}(\cdot) $, and the main  $ \mathcal{LLM}(\cdot) $ can run concurrently in parallel threads, enabling more efficient inference.

To train the activation model (illustrated in Figure 3), we modify the architecture by replacing the standard language modeling head with a score head for binary classification, and introduce a learnable activation token  $ <ACT> $ which is appended to the visual embeddings of each frame. After processing through the final layer, we extract the latest frame's activation token and feed its hidden representation into the score head to predict whether the model should respond at that time. During inference, only when the predicted score is greater than the activation threshold  $ \alpha $, the main Video-LLM can be triggered to give a response. Since  $ \mathcal{ACT}(\cdot) $ performs only binary classification (i.e., to respond or not), we aggressively pool its visual tokens for efficiency. The input sequence to the model follows the format:  $ <Q> $  $ <V_1> $  $ <A_1> $  $ <V_2> $  $ <A_2> $  $ \cdots $, where the question Q is prepended to the sequence,

5

and visual frames and corresponding responses are interleaved. This design enables the model to learn temporal dependencies and identify appropriate response moments throughout the video stream.

For training data, we collect a diverse set of temporally annotated video datasets across multiple tasks, including dense video captioning [59; 60], sequential step recognition [61; 62], grounded video question answering [63; 64; 65], temporal video grounding [66], and temporal action detection [67; 68]. For each task, we design specific prompt templates and randomly select among them as Q during training (details in Appendix A). To supervise activation timing, we insert the response  $ <A_i> $ at the end of its corresponding annotated timestamp (during inference, the response  $ <A_i> $ is generated by the larger main Video-LLM). Besides, only the last  $ P\% $ of frames of each video segment  $ V_i $ are labeled as positive (i.e., response-worthy), while earlier frames are treated as negatives.  $ P $ is dynamically sampled between 0% and 50% for each training instance, simulating a variety of activation patterns and enhancing the model's robustness to temporal variations.

## 4 Stream-IT Dataset

As analyzed in Section 3.1, streaming scenarios are primarily characterized by multi-turn real-time understanding and proactive responses. However, existing datasets and video sources fall short of fully supporting these requirements [69; 70]. To fill this gap and further enhance the streaming interaction capability of StreamBridge, we introduce Stream-IT—a video-text dataset specifically designed for streaming instruction tuning with an interleaved multi-turn dialogue format.

Datasets for Proactive Understanding. We collect a set of public datasets enriched with timestamp annotations, spanning a wide range of tasks including: (i) Dense Video Captioning [59; 60; 71]; (ii) Sequential Step Recognition [61; 62; 72]; (iii) Grounded VideoQA [63; 73; 74; 75]. All datasets are reformatted into a proactive-style interleaved format: ‘<Q> <V1> <A1>, <V2> <A2>, ⋯’, where Q may be an open-ended query (e.g., “Who is the man going to find?”) or a goal-oriented instruction (e.g., “Show me all the steps for cooking.”). Unlike traditional single-turn datasets where a question is immediately followed by an answer [69; 70], our structure introduces a temporal delay between <Q> and <A> through the inserted video segments <V>, simulating proactive response scenarios.

StreamingQA-120K: Multi-Turn, Long-Form QA Construction. To further support long-context, multi-turn real-time understanding, we introduce StreamingQA-120K, a large-scale synthetic dataset constructed by composing long-form videos from existing short video clips. Labeling long-duration videos with dense multi-turn QA pairs is prohibitively expensive. To address this, we leverage short clips from large-scale video-caption datasets, including WebVid-10M [19], Panda-70M [18], and InternVid-10M [17]. We filter approximately 1.28 million clips using semantic similarity between video and caption to ensure alignment, with each clip being around 12 seconds long. With these short clips, to form coherent long-form videos, we then iteratively compute pairwise similarity between videos and concatenate highly similar clips. Each constructed video contains roughly 10 clips, with an average length exceeding 150 seconds. Captions for each clip are preserved with natural timestamps. Using these captions, we employ GPT-4o [22] to generate diverse question-answer pairs spanning 8 task types. By default, each QA pair <Q_i> <A_i> is inserted immediately after its corresponding clip <V_i>, forming sequences like ‘<V_1> <Q_1> <A_1>, <V_2> <Q_2> <A_2>, ...’. Here, we introduce two augmentation strategies during sequence construction:

• Random QA Drop: randomly drops some QA pairs by transforming ‘<V_i> <Q_i> <A_i>’ to ‘<V_i>’ with a probability of  $ P_{drop} $, to prevent overfitting to fixed QA positions and enhance the model’s robustness in temporal variations. We set  $ P_{drop} $ to be 0.55 by default.

• QA Interval Shift: with probability  $ P_{shift} $, transforms sequences from ‘ $ <V_i> $  $ <Q_i> $  $ <A_i> $’ to ‘ $ <Q_i> $  $ <V_i> $  $ <A_i> $’, where the visual content  $ V_i $ serves as the temporal delay between question and response for proactive scenarios.  $ P_{shift} $ is set to 0.1 here.

Together, these strategies ensure that the Stream-IT dataset supports rich and varied streaming interaction formats, enabling both multi-turn real-time dialogue and proactive response capabilities across a wide range of tasks and timescales. More details on data statistics, concatenation strategy of StreamingQA-120K, and prompts for QA generation are provided in Appendix B.

6


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Method</td><td rowspan="2"># of Frames</td><td colspan="6">OVO-Bench Real-Time</td><td colspan="7">Streaming-Bench Real-Time</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>OCR</td><td style='text-align: center; word-wrap: break-word;'>ACR</td><td style='text-align: center; word-wrap: break-word;'>ATR</td><td style='text-align: center; word-wrap: break-word;'>STU</td><td style='text-align: center; word-wrap: break-word;'>FPD</td><td style='text-align: center; word-wrap: break-word;'>OJR</td><td style='text-align: center; word-wrap: break-word;'>AVG.</td><td style='text-align: center; word-wrap: break-word;'>OP</td><td style='text-align: center; word-wrap: break-word;'>CR</td><td style='text-align: center; word-wrap: break-word;'>CS</td><td style='text-align: center; word-wrap: break-word;'>ATP</td><td style='text-align: center; word-wrap: break-word;'>EU</td><td style='text-align: center; word-wrap: break-word;'>TR</td><td style='text-align: center; word-wrap: break-word;'>PR</td><td style='text-align: center; word-wrap: break-word;'>SU</td><td style='text-align: center; word-wrap: break-word;'>ACP</td><td style='text-align: center; word-wrap: break-word;'>CT</td><td style='text-align: center; word-wrap: break-word;'>AVG.</td></tr><tr><td colspan="20">Human</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Human</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>93.96</td><td style='text-align: center; word-wrap: break-word;'>92.57</td><td style='text-align: center; word-wrap: break-word;'>94.83</td><td style='text-align: center; word-wrap: break-word;'>92.70</td><td style='text-align: center; word-wrap: break-word;'>91.09</td><td style='text-align: center; word-wrap: break-word;'>94.02</td><td style='text-align: center; word-wrap: break-word;'>93.20</td><td style='text-align: center; word-wrap: break-word;'>89.47</td><td style='text-align: center; word-wrap: break-word;'>92.00</td><td style='text-align: center; word-wrap: break-word;'>93.60</td><td style='text-align: center; word-wrap: break-word;'>91.47</td><td style='text-align: center; word-wrap: break-word;'>95.65</td><td style='text-align: center; word-wrap: break-word;'>92.52</td><td style='text-align: center; word-wrap: break-word;'>88.00</td><td style='text-align: center; word-wrap: break-word;'>88.75</td><td style='text-align: center; word-wrap: break-word;'>89.74</td><td style='text-align: center; word-wrap: break-word;'>91.30</td><td style='text-align: center; word-wrap: break-word;'>91.46</td></tr><tr><td colspan="20">Proprietary Models (Offline), Single-Turn Evaluation</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Gemini 1.5 pro [23]</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>85.91</td><td style='text-align: center; word-wrap: break-word;'>66.97</td><td style='text-align: center; word-wrap: break-word;'>79.31</td><td style='text-align: center; word-wrap: break-word;'>58.43</td><td style='text-align: center; word-wrap: break-word;'>63.37</td><td style='text-align: center; word-wrap: break-word;'>61.96</td><td style='text-align: center; word-wrap: break-word;'>69.32</td><td style='text-align: center; word-wrap: break-word;'>79.02</td><td style='text-align: center; word-wrap: break-word;'>80.47</td><td style='text-align: center; word-wrap: break-word;'>83.54</td><td style='text-align: center; word-wrap: break-word;'>79.67</td><td style='text-align: center; word-wrap: break-word;'>80.00</td><td style='text-align: center; word-wrap: break-word;'>84.74</td><td style='text-align: center; word-wrap: break-word;'>77.78</td><td style='text-align: center; word-wrap: break-word;'>64.23</td><td style='text-align: center; word-wrap: break-word;'>71.95</td><td style='text-align: center; word-wrap: break-word;'>48.70</td><td style='text-align: center; word-wrap: break-word;'>75.69</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>GPT-4o [22]</td><td style='text-align: center; word-wrap: break-word;'>64</td><td style='text-align: center; word-wrap: break-word;'>69.80</td><td style='text-align: center; word-wrap: break-word;'>64.22</td><td style='text-align: center; word-wrap: break-word;'>71.55</td><td style='text-align: center; word-wrap: break-word;'>51.12</td><td style='text-align: center; word-wrap: break-word;'>70.3</td><td style='text-align: center; word-wrap: break-word;'>59.78</td><td style='text-align: center; word-wrap: break-word;'>64.46</td><td style='text-align: center; word-wrap: break-word;'>77.11</td><td style='text-align: center; word-wrap: break-word;'>80.47</td><td style='text-align: center; word-wrap: break-word;'>83.91</td><td style='text-align: center; word-wrap: break-word;'>76.47</td><td style='text-align: center; word-wrap: break-word;'>70.19</td><td style='text-align: center; word-wrap: break-word;'>83.80</td><td style='text-align: center; word-wrap: break-word;'>66.67</td><td style='text-align: center; word-wrap: break-word;'>62.19</td><td style='text-align: center; word-wrap: break-word;'>69.12</td><td style='text-align: center; word-wrap: break-word;'>49.22</td><td style='text-align: center; word-wrap: break-word;'>73.28</td></tr><tr><td colspan="20">Open-Source Models (Offline), Single-Turn Evaluation</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2-VL-72B [2]</td><td style='text-align: center; word-wrap: break-word;'>64</td><td style='text-align: center; word-wrap: break-word;'>65.77</td><td style='text-align: center; word-wrap: break-word;'>60.55</td><td style='text-align: center; word-wrap: break-word;'>69.83</td><td style='text-align: center; word-wrap: break-word;'>51.69</td><td style='text-align: center; word-wrap: break-word;'>69.31</td><td style='text-align: center; word-wrap: break-word;'>54.35</td><td style='text-align: center; word-wrap: break-word;'>61.92</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-Video-7B [15]</td><td style='text-align: center; word-wrap: break-word;'>64</td><td style='text-align: center; word-wrap: break-word;'>69.13</td><td style='text-align: center; word-wrap: break-word;'>58.72</td><td style='text-align: center; word-wrap: break-word;'>68.83</td><td style='text-align: center; word-wrap: break-word;'>49.44</td><td style='text-align: center; word-wrap: break-word;'>74.26</td><td style='text-align: center; word-wrap: break-word;'>59.78</td><td style='text-align: center; word-wrap: break-word;'>63.52</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-OV-7B [3]</td><td style='text-align: center; word-wrap: break-word;'>64/32</td><td style='text-align: center; word-wrap: break-word;'>66.44</td><td style='text-align: center; word-wrap: break-word;'>57.80</td><td style='text-align: center; word-wrap: break-word;'>73.28</td><td style='text-align: center; word-wrap: break-word;'>53.37</td><td style='text-align: center; word-wrap: break-word;'>71.29</td><td style='text-align: center; word-wrap: break-word;'>61.96</td><td style='text-align: center; word-wrap: break-word;'>64.02</td><td style='text-align: center; word-wrap: break-word;'>80.38</td><td style='text-align: center; word-wrap: break-word;'>74.22</td><td style='text-align: center; word-wrap: break-word;'>76.03</td><td style='text-align: center; word-wrap: break-word;'>80.72</td><td style='text-align: center; word-wrap: break-word;'>72.67</td><td style='text-align: center; word-wrap: break-word;'>71.65</td><td style='text-align: center; word-wrap: break-word;'>67.59</td><td style='text-align: center; word-wrap: break-word;'>65.45</td><td style='text-align: center; word-wrap: break-word;'>65.72</td><td style='text-align: center; word-wrap: break-word;'>45.08</td><td style='text-align: center; word-wrap: break-word;'>71.12</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2-VL-7B [2]</td><td style='text-align: center; word-wrap: break-word;'>64/1 FPS</td><td style='text-align: center; word-wrap: break-word;'>60.40</td><td style='text-align: center; word-wrap: break-word;'>50.46</td><td style='text-align: center; word-wrap: break-word;'>56.03</td><td style='text-align: center; word-wrap: break-word;'>47.19</td><td style='text-align: center; word-wrap: break-word;'>66.34</td><td style='text-align: center; word-wrap: break-word;'>55.43</td><td style='text-align: center; word-wrap: break-word;'>55.98</td><td style='text-align: center; word-wrap: break-word;'>75.20</td><td style='text-align: center; word-wrap: break-word;'>82.81</td><td style='text-align: center; word-wrap: break-word;'>73.19</td><td style='text-align: center; word-wrap: break-word;'>77.45</td><td style='text-align: center; word-wrap: break-word;'>68.32</td><td style='text-align: center; word-wrap: break-word;'>71.03</td><td style='text-align: center; word-wrap: break-word;'>72.22</td><td style='text-align: center; word-wrap: break-word;'>61.19</td><td style='text-align: center; word-wrap: break-word;'>61.47</td><td style='text-align: center; word-wrap: break-word;'>46.11</td><td style='text-align: center; word-wrap: break-word;'>69.04</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>InternVL-V2-8B [76]</td><td style='text-align: center; word-wrap: break-word;'>64/16</td><td style='text-align: center; word-wrap: break-word;'>67.11</td><td style='text-align: center; word-wrap: break-word;'>60.55</td><td style='text-align: center; word-wrap: break-word;'>63.79</td><td style='text-align: center; word-wrap: break-word;'>46.07</td><td style='text-align: center; word-wrap: break-word;'>68.32</td><td style='text-align: center; word-wrap: break-word;'>56.52</td><td style='text-align: center; word-wrap: break-word;'>60.39</td><td style='text-align: center; word-wrap: break-word;'>68.12</td><td style='text-align: center; word-wrap: break-word;'>60.94</td><td style='text-align: center; word-wrap: break-word;'>69.40</td><td style='text-align: center; word-wrap: break-word;'>77.12</td><td style='text-align: center; word-wrap: break-word;'>67.70</td><td style='text-align: center; word-wrap: break-word;'>62.93</td><td style='text-align: center; word-wrap: break-word;'>59.26</td><td style='text-align: center; word-wrap: break-word;'>53.25</td><td style='text-align: center; word-wrap: break-word;'>54.96</td><td style='text-align: center; word-wrap: break-word;'>56.48</td><td style='text-align: center; word-wrap: break-word;'>63.72</td></tr><tr><td colspan="20">Open-Source Models (Streaming), Single-Turn Evaluation</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Flash-VStream-7B [11]</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>24.16</td><td style='text-align: center; word-wrap: break-word;'>29.36</td><td style='text-align: center; word-wrap: break-word;'>28.45</td><td style='text-align: center; word-wrap: break-word;'>33.71</td><td style='text-align: center; word-wrap: break-word;'>25.74</td><td style='text-align: center; word-wrap: break-word;'>28.80</td><td style='text-align: center; word-wrap: break-word;'>28.37</td><td style='text-align: center; word-wrap: break-word;'>25.89</td><td style='text-align: center; word-wrap: break-word;'>43.57</td><td style='text-align: center; word-wrap: break-word;'>24.91</td><td style='text-align: center; word-wrap: break-word;'>23.87</td><td style='text-align: center; word-wrap: break-word;'>27.33</td><td style='text-align: center; word-wrap: break-word;'>13.08</td><td style='text-align: center; word-wrap: break-word;'>18.52</td><td style='text-align: center; word-wrap: break-word;'>25.20</td><td style='text-align: center; word-wrap: break-word;'>23.87</td><td style='text-align: center; word-wrap: break-word;'>48.70</td><td style='text-align: center; word-wrap: break-word;'>23.23</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLM-Online-8B [10]</td><td style='text-align: center; word-wrap: break-word;'>2 FPS</td><td style='text-align: center; word-wrap: break-word;'>8.05</td><td style='text-align: center; word-wrap: break-word;'>23.85</td><td style='text-align: center; word-wrap: break-word;'>12.07</td><td style='text-align: center; word-wrap: break-word;'>14.04</td><td style='text-align: center; word-wrap: break-word;'>45.54</td><td style='text-align: center; word-wrap: break-word;'>21.20</td><td style='text-align: center; word-wrap: break-word;'>20.79</td><td style='text-align: center; word-wrap: break-word;'>39.07</td><td style='text-align: center; word-wrap: break-word;'>40.06</td><td style='text-align: center; word-wrap: break-word;'>34.49</td><td style='text-align: center; word-wrap: break-word;'>31.05</td><td style='text-align: center; word-wrap: break-word;'>45.96</td><td style='text-align: center; word-wrap: break-word;'>32.40</td><td style='text-align: center; word-wrap: break-word;'>31.48</td><td style='text-align: center; word-wrap: break-word;'>34.16</td><td style='text-align: center; word-wrap: break-word;'>42.49</td><td style='text-align: center; word-wrap: break-word;'>27.89</td><td style='text-align: center; word-wrap: break-word;'>35.99</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Dispider [13]</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>57.72</td><td style='text-align: center; word-wrap: break-word;'>49.54</td><td style='text-align: center; word-wrap: break-word;'>62.07</td><td style='text-align: center; word-wrap: break-word;'>44.94</td><td style='text-align: center; word-wrap: break-word;'>61.39</td><td style='text-align: center; word-wrap: break-word;'>51.63</td><td style='text-align: center; word-wrap: break-word;'>54.55</td><td style='text-align: center; word-wrap: break-word;'>74.92</td><td style='text-align: center; word-wrap: break-word;'>75.53</td><td style='text-align: center; word-wrap: break-word;'>74.10</td><td style='text-align: center; word-wrap: break-word;'>73.08</td><td style='text-align: center; word-wrap: break-word;'>74.44</td><td style='text-align: center; word-wrap: break-word;'>59.92</td><td style='text-align: center; word-wrap: break-word;'>76.14</td><td style='text-align: center; word-wrap: break-word;'>62.91</td><td style='text-align: center; word-wrap: break-word;'>62.16</td><td style='text-align: center; word-wrap: break-word;'>45.80</td><td style='text-align: center; word-wrap: break-word;'>67.63</td></tr><tr><td colspan="20">Models under StreamBridge (Offline) → Streaming), Multi-Turn Evaluation</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Oryx-1.5-7B [1]</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>60.40</td><td style='text-align: center; word-wrap: break-word;'>52.29</td><td style='text-align: center; word-wrap: break-word;'>69.83</td><td style='text-align: center; word-wrap: break-word;'>50.00</td><td style='text-align: center; word-wrap: break-word;'>65.35</td><td style='text-align: center; word-wrap: break-word;'>57.61</td><td style='text-align: center; word-wrap: break-word;'>59.25</td><td style='text-align: center; word-wrap: break-word;'>78.47</td><td style='text-align: center; word-wrap: break-word;'>77.17</td><td style='text-align: center; word-wrap: break-word;'>83.86</td><td style='text-align: center; word-wrap: break-word;'>80.20</td><td style='text-align: center; word-wrap: break-word;'>71.07</td><td style='text-align: center; word-wrap: break-word;'>66.98</td><td style='text-align: center; word-wrap: break-word;'>79.63</td><td style='text-align: center; word-wrap: break-word;'>61.38</td><td style='text-align: center; word-wrap: break-word;'>66.29</td><td style='text-align: center; word-wrap: break-word;'>40.93</td><td style='text-align: center; word-wrap: break-word;'>70.59</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>+ Stream-IT</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>84.56</td><td style='text-align: center; word-wrap: break-word;'>75.23</td><td style='text-align: center; word-wrap: break-word;'>70.69</td><td style='text-align: center; word-wrap: break-word;'>50.56</td><td style='text-align: center; word-wrap: break-word;'>74.26</td><td style='text-align: center; word-wrap: break-word;'>71.74</td><td style='text-align: center; word-wrap: break-word;'>71.17</td><td style='text-align: center; word-wrap: break-word;'>82.29</td><td style='text-align: center; word-wrap: break-word;'>77.95</td><td style='text-align: center; word-wrap: break-word;'>87.98</td><td style='text-align: center; word-wrap: break-word;'>86.47</td><td style='text-align: center; word-wrap: break-word;'>77.99</td><td style='text-align: center; word-wrap: break-word;'>81.31</td><td style='text-align: center; word-wrap: break-word;'>76.85</td><td style='text-align: center; word-wrap: break-word;'>69.92</td><td style='text-align: center; word-wrap: break-word;'>71.96</td><td style='text-align: center; word-wrap: break-word;'>35.23</td><td style='text-align: center; word-wrap: break-word;'>74.79</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-OV-7B [3]</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>58.39</td><td style='text-align: center; word-wrap: break-word;'>59.63</td><td style='text-align: center; word-wrap: break-word;'>69.82</td><td style='text-align: center; word-wrap: break-word;'>44.38</td><td style='text-align: center; word-wrap: break-word;'>76.23</td><td style='text-align: center; word-wrap: break-word;'>61.41</td><td style='text-align: center; word-wrap: break-word;'>61.64</td><td style='text-align: center; word-wrap: break-word;'>76.84</td><td style='text-align: center; word-wrap: break-word;'>77.17</td><td style='text-align: center; word-wrap: break-word;'>82.60</td><td style='text-align: center; word-wrap: break-word;'>75.25</td><td style='text-align: center; word-wrap: break-word;'>64.15</td><td style='text-align: center; word-wrap: break-word;'>64.17</td><td style='text-align: center; word-wrap: break-word;'>75.00</td><td style='text-align: center; word-wrap: break-word;'>61.38</td><td style='text-align: center; word-wrap: break-word;'>61.19</td><td style='text-align: center; word-wrap: break-word;'>46.11</td><td style='text-align: center; word-wrap: break-word;'>68.39</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>+ Stream-IT</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>74.50</td><td style='text-align: center; word-wrap: break-word;'>77.06</td><td style='text-align: center; word-wrap: break-word;'>70.69</td><td style='text-align: center; word-wrap: break-word;'>54.49</td><td style='text-align: center; word-wrap: break-word;'>73.27</td><td style='text-align: center; word-wrap: break-word;'>69.57</td><td style='text-align: center; word-wrap: break-word;'>69.93</td><td style='text-align: center; word-wrap: break-word;'>82.29</td><td style='text-align: center; word-wrap: break-word;'>72.44</td><td style='text-align: center; word-wrap: break-word;'>92.09</td><td style='text-align: center; word-wrap: break-word;'>80.86</td><td style='text-align: center; word-wrap: break-word;'>71.07</td><td style='text-align: center; word-wrap: break-word;'>74.46</td><td style='text-align: center; word-wrap: break-word;'>75.00</td><td style='text-align: center; word-wrap: break-word;'>62.20</td><td style='text-align: center; word-wrap: break-word;'>70.26</td><td style='text-align: center; word-wrap: break-word;'>28.50</td><td style='text-align: center; word-wrap: break-word;'>70.92</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2-VL-7B [2]</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>65.10</td><td style='text-align: center; word-wrap: break-word;'>64.22</td><td style='text-align: center; word-wrap: break-word;'>64.66</td><td style='text-align: center; word-wrap: break-word;'>46.63</td><td style='text-align: center; word-wrap: break-word;'>74.26</td><td style='text-align: center; word-wrap: break-word;'>65.22</td><td style='text-align: center; word-wrap: break-word;'>63.35</td><td style='text-align: center; word-wrap: break-word;'>80.38</td><td style='text-align: center; word-wrap: break-word;'>78.74</td><td style='text-align: center; word-wrap: break-word;'>83.22</td><td style='text-align: center; word-wrap: break-word;'>79.86</td><td style='text-align: center; word-wrap: break-word;'>74.21</td><td style='text-align: center; word-wrap: break-word;'>69.47</td><td style='text-align: center; word-wrap: break-word;'>77.78</td><td style='text-align: center; word-wrap: break-word;'>63.41</td><td style='text-align: center; word-wrap: break-word;'>69.97</td><td style='text-align: center; word-wrap: break-word;'>43.01</td><td style='text-align: center; word-wrap: break-word;'>72.01</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>+ Stream-IT</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>84.56</td><td style='text-align: center; word-wrap: break-word;'>71.56</td><td style='text-align: center; word-wrap: break-word;'>74.14</td><td style='text-align: center; word-wrap: break-word;'>49.44</td><td style='text-align: center; word-wrap: break-word;'>75.25</td><td style='text-align: center; word-wrap: break-word;'>72.83</td><td style='text-align: center; word-wrap: break-word;'>71.30</td><td style='text-align: center; word-wrap: break-word;'>84.74</td><td style='text-align: center; word-wrap: break-word;'>82.68</td><td style='text-align: center; word-wrap: break-word;'>88.92</td><td style='text-align: center; word-wrap: break-word;'>89.77</td><td style='text-align: center; word-wrap: break-word;'>77.36</td><td style='text-align: center; word-wrap: break-word;'>85.36</td><td style='text-align: center; word-wrap: break-word;'>84.26</td><td style='text-align: center; word-wrap: break-word;'>69.92</td><td style='text-align: center; word-wrap: break-word;'>71.67</td><td style='text-align: center; word-wrap: break-word;'>35.75</td><td style='text-align: center; word-wrap: break-word;'>77.04</td></tr></table>

<div style="text-align: center;">Table 1: Results on real-time understanding tasks on OVO-Bench and Streaming-Bench.† means models under StreamBridge framework, and + Stream-IT means finetuned on Stream-IT.</div>


## 5 Experiments

### 5.1 Settings

Models and Datasets. We evaluate StreamBridge framework using three mainstream offline Video-LLMs to show its generalizability: LLaVA-OV-7B [3], Qwen2-VL-7B [2], and Oryx-1.5-7B [1]. To preserve their general video understanding capabilities during streaming adaptation, we supplement Stream-IT with approximately 600K samples from the LLaVA-178K [15], VCG-Plus [35] and ShareGPT4Video [16]. For the activation model, we fine-tune LLaVA-OV-0.5B [3] on our collected activation datasets as described in Sec. 3.2.3. The videos are sampled at 1 FPS. In Section 5.3, we use Qwen2-VL-7B as the default model unless otherwise specified. See the Appendix C for more details.

Benchmarks. For multi-turn real-time understanding, we choose OVO-Bench [20] and Streaming-Bench [21]. We primarily focus on their real-time tasks. For general video understanding, we evaluate our method across 7 video benchmarks, including 3 short-video benchmarks: MVBench [24], PerceptionTest [26], TempCompass [77], and 4 long-video benchmarks: EgoSchema [28], LongVideoBench [29], MLVU [27], and VideoMME [25]. To evaluate the proactive capability of our method, we use subtasks from ET-Bench [66] following previous works. See Appendix D for more benchmark details and evaluation metrics.

### 5.2 Main Results

Multi-Turn Real-Time Understanding. As discussed in Section 3.1, the results reported in the original paper [20; 21] in Table 1, marked as “(Offline), Single-Turn Evaluation”, do not reflect performance in real streaming scenarios. They segment a complete video into several individual clips, discarding historical visual and dialogue contexts, thereby limiting the upper bound of the performance. In contrast, with the StreamBridge framework, denoted as “(Offline → Streaming), Multi-Turn Evaluation”, these offline models are equipped to process streaming videos at 1 FPS in a multi-turn manner, while maintaining input length and historical contexts within a predefined maximum token budget.

Specifically, we observe that Qwen2-VL $ ^{\dagger} $ demonstrates notable improvements in the streaming setting, with its average score on OVO-Bench increasing from 55.98 to 63.35, and on Streaming-Bench from 69.04 to 72.01. Conversely, LLaVA-OV $ ^{\dagger} $ shows a slight performance drop when transitioning to the streaming setup: from 64.02 to 61.64 on OVO-Bench, and from 71.12 to 68.39 on Streaming-Bench. We attribute these differences to the nature of their pretraining data, where Qwen2-VL benefits from richer interleaved multimodal training (e.g., image/video-text sequences), which makes it more adept at understanding interleaved video-text inputs and utilizing extended context effectively. On

7


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Model</td><td style='text-align: center; word-wrap: break-word;'>MVBench</td><td style='text-align: center; word-wrap: break-word;'>PerceptionTest</td><td style='text-align: center; word-wrap: break-word;'>TempCompass</td><td style='text-align: center; word-wrap: break-word;'>EgoSchema</td><td style='text-align: center; word-wrap: break-word;'>LongVideoBench</td><td style='text-align: center; word-wrap: break-word;'>MLVU</td><td style='text-align: center; word-wrap: break-word;'>VideoMME (w/o subs)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Avg</td><td style='text-align: center; word-wrap: break-word;'>Val</td><td style='text-align: center; word-wrap: break-word;'>MC</td><td style='text-align: center; word-wrap: break-word;'>Test</td><td style='text-align: center; word-wrap: break-word;'>Val</td><td style='text-align: center; word-wrap: break-word;'>M-Avg</td><td style='text-align: center; word-wrap: break-word;'>Avg</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Avg. Duration</td><td style='text-align: center; word-wrap: break-word;'>16s</td><td style='text-align: center; word-wrap: break-word;'>23s</td><td style='text-align: center; word-wrap: break-word;'>12s</td><td style='text-align: center; word-wrap: break-word;'>180s</td><td style='text-align: center; word-wrap: break-word;'>473s</td><td style='text-align: center; word-wrap: break-word;'>651s</td><td style='text-align: center; word-wrap: break-word;'>1010s</td></tr><tr><td colspan="8">Proprietary Models</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Gemini 1.5 pro [23]</td><td style='text-align: center; word-wrap: break-word;'>60.5</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>67.1</td><td style='text-align: center; word-wrap: break-word;'>71.2</td><td style='text-align: center; word-wrap: break-word;'>64.0</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>75.0</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>GPT-4o [22]</td><td style='text-align: center; word-wrap: break-word;'>64.6</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>70.9</td><td style='text-align: center; word-wrap: break-word;'>72.2</td><td style='text-align: center; word-wrap: break-word;'>66.7</td><td style='text-align: center; word-wrap: break-word;'>64.6</td><td style='text-align: center; word-wrap: break-word;'>71.9</td></tr><tr><td colspan="8">Open-Source Models</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Kangaroo-8B [78]</td><td style='text-align: center; word-wrap: break-word;'>61.0</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>62.5</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>54.8</td><td style='text-align: center; word-wrap: break-word;'>61.0</td><td style='text-align: center; word-wrap: break-word;'>56.0</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LongVILA-7B [79]</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>67.7</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>57.5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LongVU-7B [80]</td><td style='text-align: center; word-wrap: break-word;'>66.9</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>67.6</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>65.4</td><td style='text-align: center; word-wrap: break-word;'>60.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Apollo-7B [4]</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>67.3</td><td style='text-align: center; word-wrap: break-word;'>64.9</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>58.5</td><td style='text-align: center; word-wrap: break-word;'>70.9</td><td style='text-align: center; word-wrap: break-word;'>61.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>NVILA-8B [81]</td><td style='text-align: center; word-wrap: break-word;'>68.1</td><td style='text-align: center; word-wrap: break-word;'>65.4</td><td style='text-align: center; word-wrap: break-word;'>69.7</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>57.7</td><td style='text-align: center; word-wrap: break-word;'>70.1</td><td style='text-align: center; word-wrap: break-word;'>64.2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>SF-LLaVA-1.5-7B [5]</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>69.6</td><td style='text-align: center; word-wrap: break-word;'>68.8</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>62.5</td><td style='text-align: center; word-wrap: break-word;'>71.5</td><td style='text-align: center; word-wrap: break-word;'>63.9</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>InternVL2.5-8B [82]</td><td style='text-align: center; word-wrap: break-word;'>72.0</td><td style='text-align: center; word-wrap: break-word;'>68.2</td><td style='text-align: center; word-wrap: break-word;'>68.3</td><td style='text-align: center; word-wrap: break-word;'>51.5</td><td style='text-align: center; word-wrap: break-word;'>60.0</td><td style='text-align: center; word-wrap: break-word;'>68.9</td><td style='text-align: center; word-wrap: break-word;'>64.2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoChat-Flash-7B [83]</td><td style='text-align: center; word-wrap: break-word;'>74.0</td><td style='text-align: center; word-wrap: break-word;'>76.2</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>64.7</td><td style='text-align: center; word-wrap: break-word;'>74.7</td><td style='text-align: center; word-wrap: break-word;'>65.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLaMA3-7B [37]</td><td style='text-align: center; word-wrap: break-word;'>69.7</td><td style='text-align: center; word-wrap: break-word;'>72.8</td><td style='text-align: center; word-wrap: break-word;'>68.1</td><td style='text-align: center; word-wrap: break-word;'>63.3</td><td style='text-align: center; word-wrap: break-word;'>59.8</td><td style='text-align: center; word-wrap: break-word;'>73.0</td><td style='text-align: center; word-wrap: break-word;'>66.2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Oryx-1.5-7B [1]</td><td style='text-align: center; word-wrap: break-word;'>67.6</td><td style='text-align: center; word-wrap: break-word;'>70.0</td><td style='text-align: center; word-wrap: break-word;'>58.8</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>56.3</td><td style='text-align: center; word-wrap: break-word;'>67.5</td><td style='text-align: center; word-wrap: break-word;'>58.8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Oryx-1.5-7B (ours)  $ ^{\ddagger} $</td><td style='text-align: center; word-wrap: break-word;'>68.0 (†0.4)</td><td style='text-align: center; word-wrap: break-word;'>71.0 (†1.0)</td><td style='text-align: center; word-wrap: break-word;'>69.0 (†10.2)</td><td style='text-align: center; word-wrap: break-word;'>61.2</td><td style='text-align: center; word-wrap: break-word;'>58.9 (†2.6)</td><td style='text-align: center; word-wrap: break-word;'>71.4 (†4.0)</td><td style='text-align: center; word-wrap: break-word;'>65.5 (†6.7)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-OV-7B [3]</td><td style='text-align: center; word-wrap: break-word;'>56.7</td><td style='text-align: center; word-wrap: break-word;'>57.1</td><td style='text-align: center; word-wrap: break-word;'>64.8</td><td style='text-align: center; word-wrap: break-word;'>60.1</td><td style='text-align: center; word-wrap: break-word;'>56.3</td><td style='text-align: center; word-wrap: break-word;'>64.7</td><td style='text-align: center; word-wrap: break-word;'>58.2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-OV-7B (ours)  $ ^{\ddagger} $</td><td style='text-align: center; word-wrap: break-word;'>59.4 (†2.7)</td><td style='text-align: center; word-wrap: break-word;'>63.9 (†6.8)</td><td style='text-align: center; word-wrap: break-word;'>67.7 (†2.9)</td><td style='text-align: center; word-wrap: break-word;'>67.0 (†6.9)</td><td style='text-align: center; word-wrap: break-word;'>54.3 (†2.0)</td><td style='text-align: center; word-wrap: break-word;'>68.2 (†3.5)</td><td style='text-align: center; word-wrap: break-word;'>61.2 (†3.0)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2-VL-7B [2]</td><td style='text-align: center; word-wrap: break-word;'>67.0</td><td style='text-align: center; word-wrap: break-word;'>62.3</td><td style='text-align: center; word-wrap: break-word;'>67.9</td><td style='text-align: center; word-wrap: break-word;'>66.7</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>63.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2-VL-7B (ours)  $ ^{\ddagger} $</td><td style='text-align: center; word-wrap: break-word;'>64.4 (†2.6)</td><td style='text-align: center; word-wrap: break-word;'>69.9 (†7.6)</td><td style='text-align: center; word-wrap: break-word;'>71.1 (†3.2)</td><td style='text-align: center; word-wrap: break-word;'>66.9 (†0.2)</td><td style='text-align: center; word-wrap: break-word;'>59.1</td><td style='text-align: center; word-wrap: break-word;'>69.6</td><td style='text-align: center; word-wrap: break-word;'>64.4 (†1.1)</td></tr></table>

<div style="text-align: center;">Table 2: Results on general video understanding benchmarks.  $ {}^{\ddagger} $ means models under Stream-Bridge framework and fine-tuned on Stream-IT.</div>


the other hand, LLaVA-OV is trained with fewer interleaved sequences, making it less suited for multi-turn streaming inputs. When faced with long, interleaved video-text sequences in streaming scenarios, its performance tends to degrade as more historical frames accumulate. Notably, fine-tuning these models on the proposed Stream-IT leads to substantial improvements in multi-turn real-time understanding. For instance, Oryx-1.5† achieves a performance gain of +11.92 on OVO-Bench and +4.2 on Streaming-Bench. Furthermore, Qwen2-VL† reaches an average score of 71.30 on OVO-Bench and 77.04 on Streaming-Bench, outperforming proprietary models such as GPT-4o and Gemini 1.5 Pro. These results validate the effectiveness of both our StreamBridge framework and the Stream-IT dataset in enhancing multi-turn real-time understanding in streaming scenarios.

General Video Understanding. While our method is designed for online scenarios, we also verify that it does not downgrade the base model's performance on standard offline video tasks. As shown in Table 2, models equipped with the StreamBridge framework and fine-tuned on Stream-IT (denoted with  $ \dagger $) exhibit consistent improvements or maintain comparable performance relative to their original versions. For instance, Oryx-1.5-7B $ \dagger $ achieves 65.5 on the challenging VideoMME with an increase of 6.7, while LLaVA-OV-7B $ \dagger $ outperforms its base model across nearly all benchmarks, except LongVideoBench. Likewise, Qwen2-VL-7B $ \dagger $ achieves competitive results on MVBench, while surpassing its original counterpart on other benchmarks. These outcomes demonstrate that our streaming adaptation enables models to retain, or even exceed their original performance in general video understanding tasks, demonstrating the generality and non-degradability of our method.

Online Activation. We evaluate the proactive capability of our framework in Table 3. Notably, in all tasks, the question is presented at the beginning of the video, and the model must autonomously decide when to respond. On the ET-Bench, StreamBridge outperforms both VideoLLM-Online [10] and Dispider [13] across generation-based tasks such as DVC (Dense Video Captioning) and SLC (Step Localization and Captioning),




<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Method</td><td rowspan="2"># of Frames</td><td colspan="6">ET-Bench</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>TVG $ _{F1} $</td><td style='text-align: center; word-wrap: break-word;'>TAL $ _{F1} $</td><td style='text-align: center; word-wrap: break-word;'>DVC $ _{F1} $</td><td style='text-align: center; word-wrap: break-word;'>DVC $ _{Sim} $</td><td style='text-align: center; word-wrap: break-word;'>SLC $ _{F1} $</td><td style='text-align: center; word-wrap: break-word;'>SLC $ _{Sim} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLM-Online [10]</td><td style='text-align: center; word-wrap: break-word;'>2 FPS</td><td style='text-align: center; word-wrap: break-word;'>13.2</td><td style='text-align: center; word-wrap: break-word;'>9.1</td><td style='text-align: center; word-wrap: break-word;'>24.0</td><td style='text-align: center; word-wrap: break-word;'>13.4</td><td style='text-align: center; word-wrap: break-word;'>9.9</td><td style='text-align: center; word-wrap: break-word;'>10.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Dispider [13]</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>36.1</td><td style='text-align: center; word-wrap: break-word;'>27.3</td><td style='text-align: center; word-wrap: break-word;'>33.8</td><td style='text-align: center; word-wrap: break-word;'>18.9</td><td style='text-align: center; word-wrap: break-word;'>18.8</td><td style='text-align: center; word-wrap: break-word;'>12.4</td></tr><tr><td colspan="8">Models under StreamBridge Framework</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Oryx-1.5 (ours) $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>34.3</td><td style='text-align: center; word-wrap: break-word;'>24.3</td><td style='text-align: center; word-wrap: break-word;'>37.8</td><td style='text-align: center; word-wrap: break-word;'>24.0</td><td style='text-align: center; word-wrap: break-word;'>22.5</td><td style='text-align: center; word-wrap: break-word;'>17.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-OV (ours) $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>34.3</td><td style='text-align: center; word-wrap: break-word;'>24.3</td><td style='text-align: center; word-wrap: break-word;'>37.9</td><td style='text-align: center; word-wrap: break-word;'>24.2</td><td style='text-align: center; word-wrap: break-word;'>22.8</td><td style='text-align: center; word-wrap: break-word;'>16.2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2-VL (ours) $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>34.3</td><td style='text-align: center; word-wrap: break-word;'>24.3</td><td style='text-align: center; word-wrap: break-word;'>38.3</td><td style='text-align: center; word-wrap: break-word;'>25.1</td><td style='text-align: center; word-wrap: break-word;'>22.6</td><td style='text-align: center; word-wrap: break-word;'>17.1</td></tr></table>

<div style="text-align: center;">Table 3: Results on ET-Bench.  $ {}^{\dagger} $ denotes models under StreamBridge framework and fine-tuned on StreamIT.  $ TVG_{F1} $ and  $ TAL_{F1} $ scores are identical across StreamBridge models due to sharing the same activation model.</div>


achieving higher similarity scores of  $ DVC_{Sim} $ and  $ SLC_{Sim} $, by producing more accurate and context-aware descriptions in streaming scenarios. We attribute this to the decoupled nature of the activation model, which enables the main Video-LLM to focus solely on video understanding and language generation, free from the burden of proactive decision-making. We also observe that Qwen2-VL $ ^{\ddagger} $ achieves better text similarity scores than other Video-LLMs, consistent with its strong real-time understanding performance presented in Table 1.

8

### 5.3 In-Depth Analysis


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Compression</td><td style='text-align: center; word-wrap: break-word;'>|OVO</td><td style='text-align: center; word-wrap: break-word;'>Streaming</td><td colspan="2">ET</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Avg.</td><td style='text-align: center; word-wrap: break-word;'>Avg.</td><td style='text-align: center; word-wrap: break-word;'>DVC_{Sim}</td><td style='text-align: center; word-wrap: break-word;'>SLC_{Sim}</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Truncation</td><td style='text-align: center; word-wrap: break-word;'>68.88</td><td style='text-align: center; word-wrap: break-word;'>72.79</td><td style='text-align: center; word-wrap: break-word;'>22.1</td><td style='text-align: center; word-wrap: break-word;'>16.7</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Round-Uniform</td><td style='text-align: center; word-wrap: break-word;'>69.91</td><td style='text-align: center; word-wrap: break-word;'>74.18</td><td style='text-align: center; word-wrap: break-word;'>23.8</td><td style='text-align: center; word-wrap: break-word;'>15.9</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Round-Decayed</td><td style='text-align: center; word-wrap: break-word;'>71.30</td><td style='text-align: center; word-wrap: break-word;'>77.04</td><td style='text-align: center; word-wrap: break-word;'>25.1</td><td style='text-align: center; word-wrap: break-word;'>17.1</td></tr></table>


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">LLaVA-178k (600k used)</td><td colspan="2">Stream-IT</td><td style='text-align: center; word-wrap: break-word;'>OVO</td><td style='text-align: center; word-wrap: break-word;'>Streaming</td><td style='text-align: center; word-wrap: break-word;'>MVBench</td><td style='text-align: center; word-wrap: break-word;'>VideoMME</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>w/o SQA-120k</td><td style='text-align: center; word-wrap: break-word;'>w/ SQA-120k</td><td style='text-align: center; word-wrap: break-word;'>Avg.</td><td style='text-align: center; word-wrap: break-word;'>Avg.</td><td style='text-align: center; word-wrap: break-word;'>Avg.</td><td style='text-align: center; word-wrap: break-word;'>Overall.</td></tr><tr><td rowspan="2">✓</td><td rowspan="2"></td><td rowspan="2">✓</td><td style='text-align: center; word-wrap: break-word;'>65.98</td><td style='text-align: center; word-wrap: break-word;'>71.36</td><td style='text-align: center; word-wrap: break-word;'>64.5</td><td style='text-align: center; word-wrap: break-word;'>61.7</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>71.28</td><td style='text-align: center; word-wrap: break-word;'>74.10</td><td style='text-align: center; word-wrap: break-word;'>58.8</td><td style='text-align: center; word-wrap: break-word;'>59.0</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>67.67</td><td style='text-align: center; word-wrap: break-word;'>72.42</td><td style='text-align: center; word-wrap: break-word;'>63.1</td><td style='text-align: center; word-wrap: break-word;'>63.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>71.30</td><td style='text-align: center; word-wrap: break-word;'>77.04</td><td style='text-align: center; word-wrap: break-word;'>64.4</td><td style='text-align: center; word-wrap: break-word;'>64.4</td></tr></table>

<div style="text-align: center;">Table 4: Ablation studies on different compression strategies.</div>


<div style="text-align: center;">Table 5: Ablation studies on Stream-IT. SQA-120k denotes the generated StreamingQA-120k.</div>


<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Frame Number</th><th style='text-align: center;'>No Compression</th><th style='text-align: center;'>Compression 32k</th><th style='text-align: center;'>Compression 16k</th><th style='text-align: center;'>Compression 8k</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>128</td><td style='text-align: center;'>500</td><td style='text-align: center;'>500</td><td style='text-align: center;'>500</td><td style='text-align: center;'>500</td></tr>
    <tr><td style='text-align: center;'>256</td><td style='text-align: center;'>1500</td><td style='text-align: center;'>1500</td><td style='text-align: center;'>1500</td><td style='text-align: center;'>500</td></tr>
    <tr><td style='text-align: center;'>512</td><td style='text-align: center;'>3500</td><td style='text-align: center;'>3500</td><td style='text-align: center;'>1500</td><td style='text-align: center;'>500</td></tr>
    <tr><td style='text-align: center;'>768</td><td style='text-align: center;'>5500</td><td style='text-align: center;'>3750</td><td style='text-align: center;'>1500</td><td style='text-align: center;'>500</td></tr>
    <tr><td style='text-align: center;'>1024</td><td style='text-align: center;'>8500</td><td style='text-align: center;'>3750</td><td style='text-align: center;'>1500</td><td style='text-align: center;'>500</td></tr>
    <tr><td style='text-align: center;'>1536</td><td style='text-align: center;'>17000</td><td style='text-align: center;'>3750</td><td style='text-align: center;'>1500</td><td style='text-align: center;'>500</td></tr>
    <tr><td style='text-align: center;'>2048</td><td style='text-align: center;'>17000</td><td style='text-align: center;'>3750</td><td style='text-align: center;'>1500</td><td style='text-align: center;'>500</td></tr>
  </tbody>
</table>

<div style="text-align: center;">Figure 4: Inference Latency (y-axis) vs. Frame Number (x-axis).</div>


<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Activation Threshold</th><th style='text-align: center;'>DVC</th><th style='text-align: center;'>SLC</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>0.1</td><td style='text-align: center;'>28.2</td><td style='text-align: center;'>18.8</td></tr>
    <tr><td style='text-align: center;'>0.2</td><td style='text-align: center;'>30.3</td><td style='text-align: center;'>19.8</td></tr>
    <tr><td style='text-align: center;'>0.3</td><td style='text-align: center;'>35.5</td><td style='text-align: center;'>21.8</td></tr>
    <tr><td style='text-align: center;'>0.4</td><td style='text-align: center;'>39.0</td><td style='text-align: center;'>22.5</td></tr>
    <tr><td style='text-align: center;'>0.5</td><td style='text-align: center;'>35.8</td><td style='text-align: center;'>20.0</td></tr>
    <tr><td style='text-align: center;'>0.6</td><td style='text-align: center;'>26.0</td><td style='text-align: center;'>15.0</td></tr>
    <tr><td style='text-align: center;'>0.7</td><td style='text-align: center;'>18.2</td><td style='text-align: center;'>11.2</td></tr>
  </tbody>
</table>

<div style="text-align: center;">Figure 5: Ablation studies on the activation threshold  $ \alpha $.</div>


Round-Decayed Compression. We set the maximum input length MaxLen = 16384, and denote the current length of the input embeddings as L. To assess the effectiveness of our round-decayed compression strategy, we compare it against two alternative methods: (1) Truncation: If L > MaxLen, only keep the last L tokens in the input sequence. (2) Round-Uniform: We treat each round equally by reducing the number of visual tokens with a fixed ratio  $ \frac{L - MaxLen}{L} $ per round, to keep the total length within MaxLen. The results are reported in Table 4. We observe that Truncation yields the worst performance, as it indiscriminately removes both visual and textual history tokens, severely weakening multi-turn reasoning. The Round-Uniform strategy performs slightly better, but still underperforms our method. It compresses the latest visual tokens, which are critical for real-time comprehension, thus leading to degraded performance, particularly on OVO-Bench and Streaming-Bench.

Inference Latency. We also evaluate the inference latency on a single A100-80G GPU with different MaxLen (8k, 16k, 32k), as shown in Figure 4. Our results show that our compression method maintains near-constant latency when the number of input tokens exceeds MaxLen, whereas models without compression suffer from sharply increasing delays and eventually trigger out-of-memory (OOM) errors with 2048 frames. This highlights the necessity of effective compression to balance inference efficiency and memory usage in streaming settings.

Impact of Stream-IT. Table 5 ablates effectiveness of Stream-IT. Training on LLaVA-178K alone causes a marked drop on both OVO-Bench and Streaming-Bench, as it lacks interleaved video-text samples necessary for multi-turn interactions. Conversely, using only Stream-IT without LLaVA-178K leads to declines in general video understanding (MVBench, VideoMME), indicating that the larger offline data corpus still contributes valuable world knowledge. Finally, removing the synthetic StreamingQA-120K subset from Stream-IT degrades performance across both streaming and offline benchmarks, underscoring the crucial role of StreamingQA-120K in boosting both streaming and offline video understanding capabilities.

Impact of MaxLen. To better understand the impact of MaxLen, we conducted ablation studies using the Qwen2-VL-StreamBridge model with 1 FPS sampling, varying MaxLen from 4k to 32k. From Table 6, we observe the following: (1) For streaming tasks (e.g., OVO-Bench Real-Time): Model performance remains relatively stable across varying MaxLen values, ranging from 70.49% to 71.30%; Accuracy peaks at 16k and slightly declines at 32k, suggesting that further increasing the memory budget yields




<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">MaxLen</td><td style='text-align: center; word-wrap: break-word;'>|OVO-Bench</td><td style='text-align: center; word-wrap: break-word;'>VideoMME</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>(Real-Time) Avg.</td><td style='text-align: center; word-wrap: break-word;'>Avg.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>4k</td><td style='text-align: center; word-wrap: break-word;'>70.49</td><td style='text-align: center; word-wrap: break-word;'>61.7</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>8k</td><td style='text-align: center; word-wrap: break-word;'>70.89</td><td style='text-align: center; word-wrap: break-word;'>63.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>16k</td><td style='text-align: center; word-wrap: break-word;'>71.30</td><td style='text-align: center; word-wrap: break-word;'>64.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>32k</td><td style='text-align: center; word-wrap: break-word;'>71.16</td><td style='text-align: center; word-wrap: break-word;'>64.7</td></tr></table>

<div style="text-align: center;">Table 6: Ablation studies on MaxLen</div>


diminishing returns. This supports our design assumption: in streaming scenarios, models primarily rely on recent context, and older frames can be compressed without significant performance loss. (2) For offline tasks (e.g., VideoMME): Accuracy improves consistently as MaxLen increases, from

9

61.7% at 4k to 64.7% at 32k. This means that offline tasks benefit more from retaining the full temporal context and more uncompressed video tokens, especially for long videos that require detailed long-range understanding. StreamBridge can flexibly balance efficiency and performance across both streaming and offline settings by adjusting the memory budget accordingly, and we set MaxLen = 16k to strike a good balance between them across most tasks.

Activation Threshold. The compact activation model makes a per-frame decision to trigger responses, with frequency determined by the activation threshold  $ \alpha $ (see score head in Figure 3). We adopt a default  $ \alpha $ of 0.35, following common practice [52; 14]. Figure 5 illustrates the impact of varying this threshold: both excessively low and high values of  $ \alpha $ decrease F1 scores ( $ DVC_{F1} $ and  $ SLC_{F1} $ on ET-Bench). A low threshold triggers overly frequent responses, while a high threshold suppresses them excessively, both of which hurt performance. Nonetheless, this hyper-parameter allows users to flexibly control response frequency through  $ \alpha $, adapting to different practical scenarios.

## 6 Conclusion

We present StreamBridge, a novel framework that transforms offline Video-LLMs into streaming-capable models. StreamBridge introduces a memory buffer paired with a round-decayed compression strategy, and decouples the activation function with a compact activation model. We also construct Stream-IT, a dataset with interleaved video-text sequences to further support StreamBridge. Extensive experiments on diverse benchmarks demonstrate that our method not only preserves the strengths of the base models but also equips them with the ability to make timely, proactive responses across multi-turn, long-context streaming scenarios. We believe StreamBridge offers a general solution for bridging the gap between offline Video-LLMs and real-world, interactive streaming applications.

## References

[1] Zuyan Liu, Yuhao Dong, Ziwei Liu, Winston Hu, Jiwen Lu, and Yongming Rao. Oryx mllm: On-demand spatial-temporal understanding at arbitrary resolution. arXiv:2409.12961, 2024. 1, 2, 3, 7, 8, 20

[2] Peng Wang, Shuai Bai, Sinan Tan, Shijie Wang, Zhihao Fan, Jinze Bai, Keqin Chen, Xuejing Liu, Jialin Wang, Wenbin Ge, et al. Qwen2-vl: Enhancing vision-language model's perception of the world at any resolution. arXiv:2409.12191, 2024. 1, 2, 3, 7, 8, 20

[3] Bo Li, Yuanhan Zhang, Dong Guo, Renrui Zhang, Feng Li, Hao Zhang, Kaichen Zhang, Peiyuan Zhang, Yanwei Li, Ziwei Liu, et al. Llava-onevision: Easy visual task transfer. arXiv:2408.03326, 2024. 1, 2, 3, 5, 7, 8, 20

[4] Orr Zohar, Xiaohan Wang, Yann Dubois, Nikhil Mehta, Tong Xiao, Philippe Hansen-Estruch, Licheng Yu, Xiaofang Wang, Felix Juefei-Xu, Ning Zhang, et al. Apollo: An exploration of video understanding in large multimodal models. arXiv:2412.10360, 2024. 1, 8

[5] Mingze Xu, Mingfei Gao, Shiyu Li, Jiasen Lu, Zhe Gan, Zhengfeng Lai, Meng Cao, Kai Kang, Yinfei Yang, and Afshin Dehghan. Slowfast-llava-1.5: A family of token-efficient video large language models for long-form video understanding. arXiv:2503.18943, 2025. 1, 8

[6] Moo Jin Kim, Karl Pertsch, Siddharth Karamcheti, Ted Xiao, Ashwin Balakrishna, Suraj Nair, Rafael Rafailov, Ethan Foster, Grace Lam, Pannag Sanketi, et al. Openvla: An open-source vision-language-action model. arXiv:2406.09246, 2024. 1

[7] Cheng Chi, Zhenjia Xu, Siyuan Feng, Eric Cousineau, Yilun Du, Benjamin Burchfiel, Russ Tedrake, and Shuran Song. Diffusion policy: Visuomotor policy learning via action diffusion. The International Journal of Robotics Research, 2023. 1

[8] Hao Shao, Yuxuan Hu, Letian Wang, Guanglu Song, Steven L Waslander, Yu Liu, and Hongsheng Li. Lmdrive: Closed-loop end-to-end driving with large language models. In CVPR, 2024. 1

[9] Yihan Hu, Jiazhi Yang, Li Chen, Keyu Li, Chonghao Sima, Xizhou Zhu, Siqi Chai, Senyao Du, Tianwei Lin, Wenhai Wang, et al. Planning-oriented autonomous driving. In CVPR, 2023. 1

[10] Joya Chen, Zhaoyang Lv, Shiwei Wu, Kevin Qinghong Lin, Chenan Song, Difei Gao, Jia-Wei Liu, Ziteng Gao, Dongxing Mao, and Mike Zheng Shou. Videollm-online: Online video large language model for streaming video. In CVPR, 2024. 2, 3, 5, 7, 8, 20

10

[11] Haoji Zhang, Yiqin Wang, Yansong Tang, Yong Liu, Jiashi Feng, Jifeng Dai, and Xiaojie Jin. Flash-vstream: Memory-based real-time understanding for long video streams. arXiv:2406.08085, 2024. 2, 3, 7, 20

[12] Wei Li, Bing Hu, Rui Shao, Leyang Shen, and Liqiang Nie. Lion-fs: Fast & slow video-language thinker as online video assistant. arXiv:2503.03663, 2025. 2, 3, 5

[13] Rui Qian, Shuangrui Ding, Xiaoyi Dong, Pan Zhang, Yuhang Zang, Yuhang Cao, Dahua Lin, and Jiaqi Wang. Dispider: Enabling video llms with active real-time interaction via disentangled perception, decision, and reaction. arXiv:2501.03218, 2025. 2, 3, 7, 8, 19, 20

[14] Yueqian Wang, Xiaojun Meng, Yuxuan Wang, Jianxin Liang, Jiansheng Wei, Huishuai Zhang, and Dongyan Zhao. Videollm knows when to speak: Enhancing time-sensitive video comprehension with video-text duet interaction format. arXiv:2411.17991, 2024. 2, 3, 5, 10

[15] Yuanhan Zhang, Jinming Wu, Wei Li, Bo Li, Zejun Ma, Ziwei Liu, and Chunyuan Li. Video instruction tuning with synthetic data. arXiv:2410.02713, 2024. 2, 3, 7, 20

[16] Lin Chen, Xilin Wei, Jinsong Li, Xiaoyi Dong, Pan Zhang, Yuhang Zang, Zehui Chen, Haodong Duan, Zhenyu Tang, Li Yuan, et al. Sharegpt4video: Improving video understanding and generation with better captions. NeurIPS, 2024. 2, 7

[17] Yi Wang, Yinan He, Yizhuo Li, Kunchang Li, Jiashuo Yu, Xin Ma, Xinhao Li, Guo Chen, Xinyuan Chen, Yaohui Wang, et al. Internvid: A large-scale video-text dataset for multimodal understanding and generation. arXiv:2307.06942, 2023. 2, 6, 16, 17

[18] Tsai-Shien Chen, Aliaksandr Siarohin, Willi Menapace, Ekaterina Deyneka, Hsiang-wei Chao, Byung Eun Jeon, Yuwei Fang, Hsin-Ying Lee, Jian Ren, Ming-Hsuan Yang, et al. Panda-70m: Captioning 70m videos with multiple cross-modality teachers. In CVPR, 2024. 2, 6, 16, 17

[19] Max Bain, Arsha Nagrani, Gül Varol, and Andrew Zisserman. Frozen in time: A joint video and image encoder for end-to-end retrieval. In ICCV, 2021. 2, 6, 16, 17

[20] Yifei Li, Junbo Niu, Ziyang Miao, Chunjiang Ge, Yuanhang Zhou, Qihao He, Xiaoyi Dong, Haodong Duan, Shuangrui Ding, Rui Qian, et al. Ovo-bench: How far is your video-llms from real-world online video understanding? arXiv:2501.05510, 2025. 2, 3, 7, 17, 18

[21] Junming Lin, Zheng Fang, Chi Chen, Zihao Wan, Fuwen Luo, Peng Li, Yang Liu, and Maosong Sun. Streamingbench: Assessing the gap for mlims to achieve streaming video understanding. arXiv:2411.03628, 2024. 2, 3, 7, 18

[22] Aaron Hurst, Adam Lerer, Adam P Goucher, Adam Perelman, Aditya Ramesh, Aidan Clark, AJ Ostrow, Akila Welihinda, Alan Hayes, Alec Radford, et al. Gpt-4o system card. arXiv:2410.21276, 2024. 2, 6, 7, 8, 20

[23] Gemini Team, Petko Georgiev, Ving Ian Lei, Ryan Burnell, Libin Bai, Anmol Gulati, Garrett Tanzer, Damien Vincent, Zhufeng Pan, Shibo Wang, et al. Gemini 1.5: Unlocking multimodal understanding across millions of tokens of context. arXiv:2403.05530, 2024. 2, 7, 8, 20

[24] Kunchang Li, Yali Wang, Yinan He, Yizhuo Li, Yi Wang, Yi Liu, Zun Wang, Jilan Xu, Guo Chen, Ping Luo, et al. Mvbench: A comprehensive multi-modal video understanding benchmark. In CVPR, 2024. 2, 7, 18

[25] Chaoyou Fu, Yuhan Dai, Yondong Luo, Lei Li, Shuhuai Ren, Renrui Zhang, Zihan Wang, Chenyu Zhou, Yunhang Shen, Mengdan Zhang, et al. Video-mme: The first-ever comprehensive evaluation benchmark of multi-modal llms in video analysis. arXiv:2405.21075, 2024. 2, 3, 7, 18

[26] Viorica Patraucean, Lucas Smaira, Ankush Gupta, Adria Recasens, Larisa Markeeva, Dylan Banarse, Skanda Koppula, Mateusz Malinowski, Yi Yang, Carl Doersch, et al. Perception test: A diagnostic benchmark for multimodal video models. NeurIPS, 2023. 2, 7, 18

[27] Junjie Zhou, Yan Shu, Bo Zhao, Boya Wu, Shitao Xiao, Xi Yang, Yongping Xiong, Bo Zhang, Tiejun Huang, and Zheng Liu. Mlvu: A comprehensive benchmark for multi-task long video understanding. arXiv:2406.04264, 2024. 2, 3, 7, 18

[28] Karttikeya Mangalam, Raiymbek Akshulakov, and Jitendra Malik. Egosschema: A diagnostic benchmark for very long-form video language understanding. NeurIPS, 2023. 2, 7, 18

[29] Haoning Wu, Dongxu Li, Bei Chen, and Junnan Li. Longvideobench: A benchmark for long-context interleaved video-language understanding. NeurIPS, 2024. 2, 3, 7, 18

11

[30] Junnan Li, Dongxu Li, Silvio Savarese, and Steven Hoi. Blip-2: Bootstrapping language-image pre-training with frozen image encoders and large language models. In ICML, 2023. 3

[31] Haotian Zhang, Mingfei Gao, Zhe Gan, Philipp Dufter, Nina Wenzel, Forrest Huang, Dhruti Shah, Xianzhi Du, Bowen Zhang, Yanghao Li, et al. Mm1. 5: Methods, analysis & insights from multimodal llm fine-tuning. ICLR, 2025. 3

[32] Matt Deitke, Christopher Clark, Sangho Lee, Rohun Tripathi, Yue Yang, Jae Sung Park, Mohammadreza Salehi, Niklas Muennighoff, Kyle Lo, Luca Soldaini, et al. Molmo and pixmo: Open weights and open data for state-of-the-art multimodal models. arXiv:2409.17146, 2024. 3

[33] Hang Zhang, Xin Li, and Lidong Bing. Video-llama: An instruction-tuned audio-visual language model for video understanding. arXiv:2306.02858, 2023. 3

[34] Bin Lin, Bin Zhu, Yang Ye, Munan Ning, Peng Jin, and Li Yuan. Video-llava: Learning united visual representation by alignment before projection. arXiv:2311.10122, 2023. 3

[35] Muhammad Maaz, Hanoona Rasheed, Salman Khan, and Fahad Khan. Videogpt+: Integrating image and video encoders for enhanced video understanding. arXiv:2406.09418, 2024. 3, 7

[36] Mingze Xu, Mingfei Gao, Zhe Gan, Hong-You Chen, Zhengfeng Lai, Haiming Gang, Kai Kang, and Afshin Dehghan. Slowfast-llava: A strong training-free baseline for video large language models. arXiv:2407.15841, 2024. 3

[37] Boqiang Zhang, Kehan Li, Zesen Cheng, Zhiqiang Hu, Yuqian Yuan, Guanzheng Chen, Sicong Leng, Yuming Jiang, Hang Zhang, Xin Li, et al. VideoLLaMA 3: Frontier multimodal foundation models for image and video understanding. arXiv:2501.13106, 2025. 3, 8

[38] Xinhao Li, Yi Wang, Jiashuo Yu, Xiangyu Zeng, Yuhan Zhu, Haian Huang, Jianfei Gao, Kunchang Li, Yinan He, Chenting Wang, et al. Videochat-flash: Hierarchical compression for long-context video modeling. arXiv:2501.00574, 2024. 3

[39] Alec Radford, Jong Wook Kim, Chris Hallacy, Aditya Ramesh, Gabriel Goh, Sandhini Agarwal, Girish Sastry, Amanda Askell, Pamela Mishkin, Jack Clark, et al. Learning transferable visual models from natural language supervision. In ICML, 2021. 3

[40] Xiaohua Zhai, Basil Mustafa, Alexander Kolesnikov, and Lucas Beyer. Sigmoid loss for language image pre-training. In ICCV, 2023. 3

[41] Haotian Liu, Chunyuan Li, Qingyang Wu, and Yong Jae Lee. Visual instruction tuning. NeurIPS, 2023. 3

[42] An Yang, Baosong Yang, Beichen Zhang, Binyuan Hui, Bo Zheng, Bowen Yu, Chengyuan Li, Dayiheng Liu, Fei Huang, Haoran Wei, et al. Qwen2.5 technical report. arXiv:2412.15115, 2024. 3

[43] Hugo Touvron, Thibaut Lavril, Gautier Izacard, Xavier Martinet, Marie-Anne Lachaux, Timothée Lacroix, Baptiste Rozière, Naman Goyal, Eric Hambro, Faisal Azhar, et al. Llama: Open and efficient foundation language models. arXiv:2302.13971, 2023. 3

[44] Roeland De Geest, Efstratios Gavves, Amir Ghodrati, Zhenyang Li, Cees Snoek, and Tinne Tuytelears. Online action detection. In ECCV, 2016. 3

[45] Mingze Xu, Mingfei Gao, Yi-Ting Chen, Larry S Davis, and David J Crandall. Temporal recurrent networks for online action detection. In ICCV, 2019. 3

[46] Mingze Xu, Yuanjun Xiong, Hao Chen, Xinyu Li, Wei Xia, Zhuowen Tu, and Stefano Soatto. Long short-term transformer for online action detection. NeurIPS, 2021. 3

[47] Yue Zhao and Philipp Krähenbühl. Real-time online video detection with temporal smoothing transformers. In ECCV, 2022. 3

[48] Kris M Kitani, Brian D Ziebart, James Andrew Bagnell, and Martial Hebert. Activity forecasting. In ECCV, 2012. 3

[49] Rohit Girdhar and Kristen Grauman. Anticipative video transformer. In CVPR, 2021. 3

[50] Joya Chen, Ziyun Zeng, Yiqi Lin, Wei Li, Zejun Ma, and Mike Zheng Shou. Livecc: Learning video llm with streaming speech transcription at scale. arXiv:2504.16030, 2025. 3

12

[51] Linli Yao, Yicheng Li, Yuancheng Wei, Lei Li, Shuhuai Ren, Yuanxin Liu, Kun Ouyang, Lean Wang, Shicheng Li, Sida Li, Lingpeng Kong, Qi Liu, Yuanxing Zhang, and Xu Sun. Timechat-online: 80% visual tokens are naturally redundant in streaming videos. arXiv:2504.17343, 2025. 3

[52] Shenghao Fu, Qize Yang, Yuan-Ming Li, Yi-Xing Peng, Kun-Yu Lin, Xihan Wei, Jian-Fang Hu, Xiaohua Xie, and Wei-Shi Zheng. Vispeak: Visual instruction feedback in streaming videos. arXiv:2503.12769, 2025. 3, 5, 10

[53] Haomiao Xiong, Zongxin Yang, Jiazuo Yu, Yunzhi Zhuge, Lu Zhang, Jiawen Zhu, and Huchuan Lu. Streaming video understanding and multi-round interaction with memory-enhanced knowledge. arXiv:2501.13468, 2025. 3, 19

[54] Zhenyu Yang, Yuhang Hu, Zemin Du, Dizhan Xue, Shengsheng Qian, Jiahong Wu, Fan Yang, Weiming Dong, and Changsheng Xu. Svbench: A benchmark with temporal multi-turn dialogues for streaming video understanding. arXiv:2502.10810, 2025. 3

[55] Yuxuan Wang, Yueqian Wang, Bo Chen, Tong Wu, Dongyan Zhao, and Zilong Zheng. Omnimmi: A comprehensive multi-modal interaction benchmark in streaming video contexts. arXiv:2503.22952, 2025.

[56] Shangzhe Di, Zhelun Yu, Guanghao Zhang, Haoyuan Li, Tao Zhong, Hao Cheng, Bolin Li, Wanggui He, Fangxun Shu, and Hao Jiang. Streaming video question-answering with in-context video kv-cache retrieval. arXiv preprint arXiv:2503.00540, 2025. 3, 19

[57] Rui Qian, Xiaoyi Dong, Pan Zhang, Yuhang Zang, Shuangrui Ding, Dahua Lin, and Jiaqi Wang. Streaming long video understanding with large language models. Advances in Neural Information Processing Systems, 37:119336–119360, 2024. 3, 19

[58] Linli Yao, Lei Li, Shuhuai Ren, Lean Wang, Yuanxin Liu, Xu Sun, and Lu Hou. Deco: Decoupling token compression from semantic abstraction in multimodal large language models. arXiv:2405.20985, 2024. 5

[59] Fabian Caba Heilbron, Victor Escorcia, Bernard Ghanem, and Juan Carlos Niebles. Activitynet: A large-scale video benchmark for human activity understanding. In CVPR, 2015. 6, 15, 16, 17

[60] Mingfei Han, Linjie Yang, Xiaojun Chang, and Heng Wang. Shot2story20k: A new benchmark for comprehensive understanding of multi-shot videos. arXiv:2312.10300, 2023. 6, 15, 16, 17

[61] Yansong Tang, Dajun Ding, Yongming Rao, Yu Zheng, Danyang Zhang, Lili Zhao, Jiwen Lu, and Jie Zhou. Coin: A large-scale dataset for comprehensive instructional video analysis. In CVPR, 2019. 6, 15, 17

[62] Luowei Zhou, Chenliang Xu, and Jason Corso. Towards automatic learning of procedures from web instructional videos. In AAAI, 2018. 6, 15, 17

[63] Leonard Bärmann and Alex Waibel. Where did i leave my keys?-episodic-memory-based question answering on egocentric videos. In CVPR, 2022. 6, 17

[64] Qirui Chen, Shangzhe Di, and Weidi Xie. Grounded multi-hop videoqa in long-form egocentric videos. arXiv:2408.14469, 2024. 6, 15

[65] Haibo Wang, Zhiyang Xu, Yu Cheng, Shizhe Diao, Yufan Zhou, Yixin Cao, Qifan Wang, Weifeng Ge, and Lifu Huang. Grounded-videollm: Sharpening fine-grained temporal grounding in video large language models. arXiv:2410.03290, 2024. 6

[66] Ye Liu, Zongyang Ma, Zhongang Qi, Yang Wu, Ying Shan, and Chang W Chen. Et bench: Towards open-ended event-level video-language understanding. NeurIPS, 2024. 6, 7, 15, 18, 19

[67] Yi Liu, Limin Wang, Yali Wang, Xiao Ma, and Yu Qiao. Fineaction: A fine-grained video dataset for temporal action localization. TIP, 2022. 6, 15

[68] Hang Zhao, Antonio Torralba, Lorenzo Torresani, and Zhicheng Yan. Hacs: Human action clips and segments dataset for recognition and temporal localization. In ICCV, 2019. 6, 15

[69] Shuhuai Ren, Linli Yao, Shicheng Li, Xu Sun, and Lu Hou. Timechat: A time-sensitive multimodal large language model for long video understanding. In CVPR, 2024. 6

[70] Bin Huang, Xin Wang, Hong Chen, Zihan Song, and Wenwu Zhu. Vtimellm: Empower llm to grasp video moments. In CVPR, 2024. 6

[71] Gabriel Huang, Bo Pang, Zhenhai Zhu, Clara Rivera, and Radu Soricut. Multimodal pretraining for dense video captioning. arXiv:2011.11760, 2020. 6, 17

13

[72] Zeqian Li, Qirui Chen, Tengda Han, Ya Zhang, Yanfeng Wang, and Weidi Xie. Multi-sentence grounding for long-term instructional video. In ECCV. Springer, 2024. 6, 17

[73] Shangzhe Di and Weidi Xie. Grounded question-answering in long egocentric videos. In CVPR, 2024. 6, 15, 17

[74] Enxin Song, Wenhao Chai, Guanhong Wang, Yucheng Zhang, Haoyang Zhou, Feiyang Wu, Haozhe Chi, Xun Guo, Tian Ye, Yanting Zhang, et al. Moviechat: From dense token to sparse memory for long video understanding. In CVPR, 2024. 6, 17

[75] Miquel Farré, Andi Marafioti, Lewis Tunstall, Leandro Von Werra, and Thomas Wolf. Finevideo. https://huggingface.co/datasets/HuggingFaceFV/finevideo, 2024. 6, 17

[76] Zhe Chen, Jiannan Wu, Wenhai Wang, Weijie Su, Guo Chen, Sen Xing, Muyan Zhong, Qinglong Zhang, Xizhou Zhu, Lewei Lu, et al. Internvl: Scaling up vision foundation models and aligning for generic visual-linguistic tasks. In CVPR, 2024. 7, 20

[77] Yuanxin Liu, Shicheng Li, Yi Liu, Yuxiang Wang, Shuhuai Ren, Lei Li, Sishuo Chen, Xu Sun, and Lu Hou. Tempcompass: Do video lims really understand videos? arXiv:2403.00476, 2024. 7, 18

[78] Jiajun Liu, Yibing Wang, Hanghang Ma, Xiaoping Wu, Xiaoqi Ma, Xiaoming Wei, Jianbin Jiao, Enhua Wu, and Jie Hu. Kangaroo: A powerful video-language model supporting long-context video input. arXiv preprint arXiv:2408.15542, 2024. 8

[79] Yukang Chen, Fuzhao Xue, Dacheng Li, Qinghao Hu, Ligeng Zhu, Xiuyu Li, Yunhao Fang, Haotian Tang, Shang Yang, Zhijian Liu, et al. Longvila: Scaling long-context visual language models for long videos. arXiv preprint arXiv:2408.10188, 2024. 8

[80] Xiaoqian Shen, Yunyang Xiong, Changsheng Zhao, Lemeng Wu, Jun Chen, Chenchen Zhu, Zechun Liu, Fanyi Xiao, Balakrishnan Varadarajan, Florian Bordes, et al. Longvu: Spatiotemporal adaptive compression for long video-language understanding. arXiv preprint arXiv:2410.17434, 2024. 8

[81] Zhijian Liu, Ligeng Zhu, Baifeng Shi, Zhuoyang Zhang, Yuming Lou, Shang Yang, Haocheng Xi, Shiyi Cao, Yuxian Gu, Dacheng Li, et al. Nvila: Efficient frontier visual language models. arXiv preprint arXiv:2412.04468, 2024. 8

[82] Zhe Chen, Weiyun Wang, Yue Cao, Yangzhou Liu, Zhangwei Gao, Erfei Cui, Jinguo Zhu, Shenglong Ye, Hao Tian, Zhaoyang Liu, et al. Expanding performance boundaries of open-source multimodal models with model, data, and test-time scaling. arXiv:2412.05271, 2024. 8

[83] Xinhao Li, Yi Wang, Jiashuo Yu, Xiangyu Zeng, Yuhan Zhu, Haian Huang, Jianfei Gao, Kunchang Li, Yinan He, Chenting Wang, et al. Videochat-flash: Hierarchical compression for long-context video modeling. arXiv preprint arXiv:2501.00574, 2024. 8

[84] Jiyang Gao, Chen Sun, Zhenheng Yang, and Ram Nevatia. Tall: Temporal activity localization via language query. In ICCV, 2017. 15

[85] Nils Reimers and Iryna Gurevych. Sentence-bert: Sentence embeddings using siamese bert-networks. arXiv:1908.10084, 2019. 19

14

<div style="text-align: center;"><img src="imgs/img_in_image_box_215_145_1004_880.jpg" alt="Image" width="64%" />

Prompts for Dense Video Captioning:
(1) "Identify and describe all activity events in the video.",
(2) "List every event happening in the video with descriptions.",
(3) "Detect and summarize each event sequence in the video.",
(4) "Extract and explain all notable activities in the video.",
(5) "Find all significant events in the video and describe them.",

Prompts for Sequential Step Recognition:
(1) "Identify key action steps in the video and provide a brief description of each.",
(2) "Detect and outline a sequence of actions or steps taking place in the video.",
(3) "Analyze the video to determine distinct actions or steps.",
(4) "Break down the video into meaningful steps, describing each one concisely.",
(5) "Recognize and highlight specific sequences of actions within the video.",

Prompts for Temporal Action Detection:
(1) "When the action <action label> happens, output <action label>".
(2) "When the event <action label> occurs, output <action label>".
(3) "If you see the action <action label>, return <action label>".
(4) "Upon detecting <action label>, generate the message <action label>".
(5) "When <action label> arises, immediately output <action label>".

Prompts for Grounded VideoQA:
(1) "<Question>. Answer me only when you get enough information for answering the question.",
(2) "<Question>. Respond only if you have sufficient details to provide a complete answer.",
(3) "<Question>. Provide an answer only when you have gathered enough relevant information.",
(4) "<Question>. Ensure you have all necessary context before attempting to answer.",
(5) "<Question>. Only reply when you are confident that your answer is accurate and well-informed.",

Prompts for Temporal Video Grounding:
(1) "Localize the visual content described by the given textual query <query> in the video.",
(2) "Detect the video segment that semantically matches the given textual query <query>".
(3) "Give you a textual query: <query>. When does the described content occur in the video?",
(4) "Locate the visual content mentioned in the text query <query> within the video.",
(5) "Find the video segment that corresponds to the given textual query <query>".

</div>


<div style="text-align: center;">Table 7: Prompts used for datasets to train the activation model.</div>


### A Datasets Used to Train the Activation Model

To train the activation model  $ \mathcal{ACT}(\cdot) $, we compile a diverse collection of video datasets spanning five distinct tasks:

• Dense Video Captioning: ActivityNet Captions [59], Shot2Story [60].

• Sequential Step Recognition: YouCook2 [62], COIN [61].

• Temporal Action Detection: FineAction [67], HACS [68].

• Grounded VideoQA: Multihop-EgoQA [64], EgoTimeQA [73].

• Temporal Video Grounding: Charades [84], and the TVG subset from ET-Instruct [66].

In total, our training set contains approximately 180k video samples. For each sample, we construct an input prompt using task-specific templates. A prompt is randomly sampled from a predefined pool for the corresponding task to ensure stylistic diversity and improve generalization across video domains. The full list of prompt templates is provided in Table 7. During training, the prompt is inserted at the beginning of the input sequence as in Figure 3.

15


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>System:
You are a good question generator. I need your help in generating high quality question-answer pairs pertaining to the video clip descriptions. Follow these instructions:
(1) Ensure the questions and answers are highly relevant to the captions and DO NOT INCLUDE TOPICS NOT MENTIONED in the captions.
(2) IGNORE CONTRADICTORY OR UNREASONABLE PARTS of the captions. Do not base questions on them.
(3) I hope your questions feature different causal and temporal reasoning. Questions should be diverse and be related to different aspects of the described events.
(4) Ensure that the questions in the QA chain are clear and precise, directly corresponding to specific information or events in the video, and can be answered by watching the video content without the need for a video description or inference, avoiding questions that require assumptions.
(5) Pay attention to grammar. Avoid grammar mistakes, especially with person and tense.
(6) Ensure questions are reasonable and challenging, requiring thoughtful consideration to answer correctly.
(7) The question should not contain phrases like &#x27;In the beginning of the clips&#x27; or &#x27;at the beginning of the video&#x27; or &#x27;in the video&#x27; or &#x27;in this clips&#x27;; it can include expressions of the present or recent past such as &#x27;just now&#x27; or &#x27;right now.
(8) Please pay attention to the tense of the sentences.
(9) Never mention the sentence like &#x27;according to the caption&#x27; in your question, you should assume that you can really watch the video instead of reading a caption.
(10) Ensure there are no references to the source of information in the QA, avoiding expressions like &#x27;from the image&#x27;, &#x27;sequence of pictures&#x27;, &#x27;which frame&#x27;, or &#x27;which photo&#x27;; you should understand the input as a video and describe it using video footage.
Understand the following different task descriptions:
&lt;task descriptions&gt;
USER:
Now, please carefully review the following video caption:
&lt;caption&gt;
According to the given caption, please select ONE task type that is best suitable to generate the QA pair, and output your question, answer and task type following the SAME FORMAT as the examples above. Remember, just generate only ONE QA pair.</td></tr></table>

<div style="text-align: center;">Table 8: Prompts used to generate QA pairs with GPT-4o.</div>


### B Stream-IT Construction

### B.1 Statistics of Stream-IT

We provide detailed statistics of the Stream-IT dataset in Table 9, including the number of samples, average video duration, and the corresponding source datasets used for each task. Notably, during the construction of the dense video captioning tasks, including ActivityNet[59] and Shot2Story [60], we only arrange 20% of the sequences with the proactive format of ‘<Q><V1><A1>, <V2><A2>, …’, while the 80% of the sequences with the multi-turn format of ‘<V1><Q1><A1>, <V2><Q2><A2>, …’, where <Q> is the question asking about current situations like ‘What is happening now?’.

### B.2 Concatenation Strategy for Constructing StreamingQA-120K

Starting from a pool of 1.28 million filtered short videos sourced from WebVid-10M [19], Panda-70M [18], and InternVid-10M [17], our goal is to iteratively merge semantically similar clips to form long-form video samples. Let  $ \mathcal{V} $ denote the entire set of filtered videos. We initiate the process by randomly sampling one clip  $ \mathcal{V}_1 $ from  $ \mathcal{V} $ as the anchor. We then compute pairwise semantic similarity (based on the middle frame) between  $ \mathcal{V}_1 $ and all other videos in  $ \mathcal{V} \setminus \mathcal{V}_1 $. A new clip  $ \mathcal{V}_2 $ is sampled according to the similarity distribution (without replacement). The procedure is repeated using  $ \mathcal{V}_2 $ as the new anchor, generating  $ \mathcal{V}_3 $ from  $ \mathcal{V} \setminus \mathcal{V}_1 $,  $ \mathcal{V}_2 $, and so on. This results in a similarity-ordered list of videos  $ \mathcal{V}_1, \mathcal{V}_2, \mathcal{V}_3, \ldots $. We formulate this process in Algorithm 2. This approach allows for flexible concatenation of any number  $ k $ of clips to construct a long-form sample, by directly selecting

16


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Task</td><td style='text-align: center; word-wrap: break-word;'># of Samples</td><td style='text-align: center; word-wrap: break-word;'>Datasets</td><td style='text-align: center; word-wrap: break-word;'>Average duration</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Dense Video Captioning</td><td style='text-align: center; word-wrap: break-word;'>~54k</td><td style='text-align: center; word-wrap: break-word;'>ActivityNet [59] (~10k)\nShot2Story [60] (~36k)\nViTT [71] (~8k)</td><td style='text-align: center; word-wrap: break-word;'>~180s\n~16s\n~210s</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Sequential Step Recognition</td><td style='text-align: center; word-wrap: break-word;'>~22k</td><td style='text-align: center; word-wrap: break-word;'>YouCook2 [62] (~1.3k)\nCOIN [61] (~11k)\nHowToStep [72] (~10k)</td><td style='text-align: center; word-wrap: break-word;'>~317s\n~145s\n~190s</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Grounded Video Question Answering</td><td style='text-align: center; word-wrap: break-word;'>~69k</td><td style='text-align: center; word-wrap: break-word;'>MovieChat [74] (~0.8k)\nEgoTimeQA [73] (~10k)\nQAEgo4D [63] (~15k)\nFineVideo [75] (~43k)</td><td style='text-align: center; word-wrap: break-word;'>~10k frames\n~150s\n~495s\n~280s</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Multi-turn Real-time Question Answering</td><td style='text-align: center; word-wrap: break-word;'>~120k</td><td style='text-align: center; word-wrap: break-word;'>StreamingQA-120K (~120k)\n(Sourced from Webvid-10M[19], Panda-70M[18], InternVid-10M[17])</td><td style='text-align: center; word-wrap: break-word;'>~150s</td></tr></table>

<div style="text-align: center;">Table 9: Involved tasks and datasets in Stream-IT.</div>


Algorithm 2: Constructing Similarity-Ordered Video Clip Sequence

1 Inputs: Pool of filtered short video clips  $ \mathcal{V}_{\text{pool}} = \{v_1, v_2, \ldots, v_M\} $;
2 Initializations:  $ \mathcal{V}_{\text{ordered}} = [ \quad ] $,  $ v_{\text{anchor}} = \text{None} $;
3 Define:  $ \text{Sim}(v_{\text{anchor}}, \mathcal{C}_{\text{candidates}}) $; function that returns the clip from  $ \mathcal{C}_{\text{candidates}} $ most similar to  $ v_{\text{anchor}} $.
4  $ v_{\text{anchor}} \leftarrow \text{RandomSample}(\mathcal{V}_{\text{pool}}) $; // Randomly select the first anchor clip
5  $ \mathcal{V}_{\text{ordered}} \leftarrow v_{\text{anchor}} $; // Add  $ v_{\text{anchor}} $ to  $ \mathcal{V}_{\text{ordered}} $
6  $ \mathcal{V}_{\text{pool}} \leftarrow \mathcal{V}_{\text{pool}} \setminus \{v_{\text{anchor}}\} $; // Remove  $ v_{\text{anchor}} $ from  $ \mathcal{V}_{\text{pool}} $
7 while  $ \mathcal{V}_{\text{pool}} $ is not empty do
8  $ \quad v_{\text{next}} \leftarrow \text{Sim}(v_{\text{anchor}}, \mathcal{V}_{\text{pool}}) $; // Find the clip in pool most similar to  $ v_{\text{anchor}} $
9  $ \quad \mathcal{V}_{\text{ordered}} \leftarrow v_{\text{next}} $
10  $ \quad \mathcal{V}_{\text{pool}} \leftarrow \mathcal{V}_{\text{pool}} \setminus \{v_{\text{next}}\} $
11  $ \quad v_{\text{anchor}} \leftarrow v_{\text{next}} $; // Update anchor to the newly added clip
12 Output: Similarity-ordered list of video clips  $ \mathcal{V}_{\text{ordered}} = [\mathcal{V}_1, \mathcal{V}_2, \ldots, \mathcal{V}_M] $.

a continuous span  $ \mathcal{V}_{[i:i+k]} $, without re-computing similarity each time. We also prepare hallucination questions irrelevant to existing video inputs following [20] with a ratio of 0.01%.

### B.3 Prompt Templates for Generating QA Pairs

To generate question-answer pairs based on clip-level captions, we design diverse prompt templates for 8 distinct reasoning tasks. Table 8 provides examples of these templates. Below, we summarize the <task descriptions> associated with each QA category:

• [OP] Object Perception: Detect and identify objects, focusing on recognizing their attributes in real time.

• [AR] Action Recognition: Identify human actions and interactions occurring in the current moment.

• [SA] Spatial Awareness: Understand spatial relationships among objects and events; reason about location, orientation, and distance.

• [SR] Sequential Relationship: Identify the temporal order of events and actions, especially those involving “before” and “after” cues.

• [CR] Causal Reasoning: Analyze cause-and-effect relationships between actions and outcomes.

• [OCR] Optical Character Recognition: Recognize and interpret textual content in scenes (e.g., subtitles, signs, charts).

• [UEH] Unexpected Event Handling: Detect and react to anomalies or sudden changes in the environment.

• [EU] Event Understanding: Summarize and reason about sequences of temporally linked events.

These diverse prompts ensure broad task coverage and help enhance the model's generalization across different temporal and semantic understanding challenges.

17

### C More Implementation Details

For the main VideoLLMs, we use the following configurations for each model:

• LLaVA-OV-7B: We apply center cropping with a resolution of  $ 384 \times 384 $ and use a  $ \times 4 $ down sampler (bilinear interpolation) with the frame features, resulting in 49 tokens per frame.

- Oryx-1.5-7B: We use the model's default dynamic resolution, ranging from 288 to 480 pixels. With a  $ \times 4 $ down sampler on the frame features (average pooling), the resulting token count per frame varies between 33 and 59.

- Qwen2-VL-7B: The model uses a dynamic resolution between 224 and 448, with  $ \times 4 $ down sampling (average pooling) on the frame features, resulting in 36–64 tokens per frame.

All models are fine-tuned for one epoch using a learning rate of  $ 2e^{-5} $ with a cosine annealing scheduler and AdamW optimizer. The image encoder remains frozen, while the visual projector and the LLM are fully trainable. The maximum length MaxLen of input embeddings is set to 16384 for the round-decayed compression.

For the activation model, we adopt LLaVA-OV-0.5B as the base model. To improve efficiency, we aggressively pool the frame representations to 16 tokens per frame. During training, only the LoRA adapters, the projector, the score head, and the learnable activation token are trainable. The model is trained for 5 epochs using a fixed learning rate of 2e-5 for the projector, while 2e-4 for the LoRA adapters, score head, and the learnable activation token, with AdamW optimizer.

Notably, for both the main VideoLLM and the activation model, we sample frames at 1 FPS to better simulate real-world frame rates. For videos longer than 256 seconds, we uniformly sample 256 frames to fit within the maximum input length constraint. Experiments are conducted on NVIDIA-H100/A100 GPUs. During inference, we sample videos at 2 FPS for short video benchmarks like MVBench, PerpecptionTest, and TempCompass, while 1 FPS for multi-turn real-time understanding benchmarks and long video benchmarks including OVO-Bench, Streaming-Bench, MLVU, LongVideoBench, VideoMME, and EgoSchema.

### D Benchmarks and Metrics

Multi-turn Real-time Understanding Benchmarks. We evaluate our method on two recently proposed large-scale streaming video benchmarks: OVO-Bench [20] and Streaming-Bench [21]. Both benchmarks are designed to assess streaming video comprehension under long-context, multi-turn settings. Our evaluation primarily focuses on their real-time understanding tasks. OVO-Bench contains 512 videos with an average length of 435 seconds and approximately 1,600 questions. The evaluated tasks include: (1) Spatial Understanding (STU), (2) Object Recognition (OJR), (3) Attribute Recognition (ATR), (4) Action Recognition (ACR), (5) Optical Character Recognition (OCR), and (6) Future Prediction (FPD). Streaming-Bench consists of 500 videos with an average length of 606 seconds and approximately 2,500 questions. It includes the following tasks: (1) Object Perception (OP), (2) Causal Reasoning (CR), (3) Clip Summarization (CS), (4) Attribute Perception (ATP), (5) Event Understanding (EU), (6) Text-Rich Understanding (TR), (7) Prospective Reasoning (PR), (8) Spatial Understanding (SU), (9) Action Perception (ACP), (10) Counting (CT). Both benchmarks are structured as multiple-choice question-answering tasks, and we report the accuracy.

General Video Understanding Benchmarks. To evaluate general video comprehension ability, we test our models on seven widely used benchmarks. This includes three short-video benchmarks: MVBench [24], Perception Test [26], and TempCompass [77], and four long-video benchmarks: EgoSchema [28], LongVideoBench [29], MLVU [27], and VideoMME [25]. These datasets span a broad range of video durations, from a few minutes to several hours. All are evaluated in a multiple-choice format, and accuracy is reported.

Online Activation Benchmarks. To assess the proactive capabilities of our framework, we evaluate performance on a subset of ET-Bench [66], including Temporal Video Grounding (TVG), Temporal Action Localization (TAL), Dense Video Captioning (DVC), and Sequential Localization Captioning (SLC). These tasks emphasize a shift from passive to active perception, requiring the model to determine when to respond based on upcoming visual inputs, rather than reacting immediately. For example, the Sequential Localization Captioning (SLC) task requires the model to both determine

18

the precise timing of a certain step and output its content. For evaluation metrics, we compute the average F1 score across multiple IoU thresholds (IoU ∈ {0.1, 0.3, 0.5, 0.7}) for localization-based tasks. For tasks involving text generation, we adopt sentence-level similarity metrics [85] to measure the semantic alignment between model outputs and ground-truth responses, following prior works [66; 13]. Specifically, the all-MiniLM-L6-v2 model in Sentence-Transformers library is used as the embedding model. Notably, in all these tasks, the question is presented at the beginning of the video, and the model must autonomously decide when to respond. Moreover, the results of TVG $ _{F1} $, TAL $ _{F1} $, are the same for our method with different main Video-LLMs, since they use the same activation model and will not be affected by the generated response.

### E Broader Impacts

There are many real-world applications of streaming Video-LLMs, such as patient or elderly health monitoring, autonomous driving, and collaborative robots. However, there could be unintended usages and we advocate responsible usage complying with applicable laws and regulations.

### F More Related Works

To address the challenge of long-context understanding in streaming video, several memory and retrieval mechanisms have been proposed. For instance, ReKV [56] introduces a training-free framework that stores and retrieves the Key-Value (KV) caches of processed frames, enabling offline models to answer user queries efficiently by reloading only the most relevant context. Besides, VideoStreaming [57] employs a memory-propagated encoding architecture where a condensed representation of the preceding clip serves as historical context for encoding the next, combined with an adaptive selection of memories for question-answering. Moreover, StreamChat [53] proposes a hierarchical memory system comprising short-term, long-term, and dialogue components to facilitate complex streaming interactions, and also contributes the StreamBench benchmark for evaluating diverse streaming scenarios. While these methods effectively advance long-context retention for reactive question-answering, StreamBridge differs by introducing a round-decayed compression strategy specifically tailored for multi-turn real-time interactions, which efficiently prunes redundant historical tokens while preserving recent context with high fidelity. Moreover, StreamBridge introduces a decoupled, lightweight activation model. This plug-and-play component operates in parallel with the main Video-LLM, enabling continuous proactive responses. These designs, supported by our dedicated Stream-IT dataset, effectively transform general-purpose offline models into versatile and proactive streaming assistants without compromising their core performance.

### G Limitations

Although our proposed framework and dataset significantly enhance the streaming capabilities of existing offline Video-LLMs, there are still limitations worth noting. First, while Stream-IT provides large-scale multi-turn, interleaved training data, its construction relies partially on synthetic QA generation and clip concatenation, which, despite careful filtering, may introduce domain shift compared to truly continuous, real-world video streams. Future work could benefit from curating more organically collected long-form streaming videos with naturally evolving events and dialogues. Second, StreamBridge currently focuses on frame-by-frame streaming under relatively low sampling rates (e.g., 1 FPS). Extending the framework to handle denser frame rates or multi-modal streaming inputs (e.g., audio-visual-text) in real-time remains an important direction for future research.

19

### H Full Results on OVO-Bench and Streaming-Bench


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Method</td><td rowspan="2"># of Frames</td><td colspan="4">Real-Time Visual Perception</td><td colspan="4">Backward Tracing</td><td colspan="3">Forward Active Responding</td><td style='text-align: center; word-wrap: break-word;'>Overall.</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>OCR</td><td style='text-align: center; word-wrap: break-word;'>ACR</td><td style='text-align: center; word-wrap: break-word;'>ATR</td><td style='text-align: center; word-wrap: break-word;'>STU</td><td style='text-align: center; word-wrap: break-word;'>FPD</td><td style='text-align: center; word-wrap: break-word;'>OJR</td><td style='text-align: center; word-wrap: break-word;'>AVG.</td><td style='text-align: center; word-wrap: break-word;'>EPM</td><td style='text-align: center; word-wrap: break-word;'>ASI</td><td style='text-align: center; word-wrap: break-word;'>HLD</td><td style='text-align: center; word-wrap: break-word;'>AVG.</td><td style='text-align: center; word-wrap: break-word;'>REC</td><td style='text-align: center; word-wrap: break-word;'>SSR CRR</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td colspan="15">Human</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Human</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>93.96</td><td style='text-align: center; word-wrap: break-word;'>92.57</td><td style='text-align: center; word-wrap: break-word;'>94.83</td><td style='text-align: center; word-wrap: break-word;'>92.70</td><td style='text-align: center; word-wrap: break-word;'>91.09</td><td style='text-align: center; word-wrap: break-word;'>94.02</td><td style='text-align: center; word-wrap: break-word;'>93.20</td><td style='text-align: center; word-wrap: break-word;'>92.59</td><td style='text-align: center; word-wrap: break-word;'>93.02</td><td style='text-align: center; word-wrap: break-word;'>91.37</td><td style='text-align: center; word-wrap: break-word;'>92.33</td><td style='text-align: center; word-wrap: break-word;'>95.48</td><td style='text-align: center; word-wrap: break-word;'>89.67</td><td style='text-align: center; word-wrap: break-word;'>93.56</td></tr><tr><td colspan="15">Proprietary Models (Offline), Single-Turn Evaluation</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Gemini 1.5 pro [23]</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>85.91</td><td style='text-align: center; word-wrap: break-word;'>66.97</td><td style='text-align: center; word-wrap: break-word;'>79.31</td><td style='text-align: center; word-wrap: break-word;'>58.43</td><td style='text-align: center; word-wrap: break-word;'>63.37</td><td style='text-align: center; word-wrap: break-word;'>61.96</td><td style='text-align: center; word-wrap: break-word;'>69.32</td><td style='text-align: center; word-wrap: break-word;'>58.59</td><td style='text-align: center; word-wrap: break-word;'>76.35</td><td style='text-align: center; word-wrap: break-word;'>52.64</td><td style='text-align: center; word-wrap: break-word;'>62.54</td><td style='text-align: center; word-wrap: break-word;'>35.53</td><td style='text-align: center; word-wrap: break-word;'>74.24</td><td style='text-align: center; word-wrap: break-word;'>61.67</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>GPT-4o [22]</td><td style='text-align: center; word-wrap: break-word;'>64</td><td style='text-align: center; word-wrap: break-word;'>69.80</td><td style='text-align: center; word-wrap: break-word;'>64.22</td><td style='text-align: center; word-wrap: break-word;'>71.55</td><td style='text-align: center; word-wrap: break-word;'>51.12</td><td style='text-align: center; word-wrap: break-word;'>70.30</td><td style='text-align: center; word-wrap: break-word;'>59.78</td><td style='text-align: center; word-wrap: break-word;'>64.46</td><td style='text-align: center; word-wrap: break-word;'>57.91</td><td style='text-align: center; word-wrap: break-word;'>75.68</td><td style='text-align: center; word-wrap: break-word;'>48.66</td><td style='text-align: center; word-wrap: break-word;'>60.75</td><td style='text-align: center; word-wrap: break-word;'>27.58</td><td style='text-align: center; word-wrap: break-word;'>73.21</td><td style='text-align: center; word-wrap: break-word;'>59.40</td></tr><tr><td colspan="15">Open-Source Models (Offline), Single-Turn Evaluation</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2-VL-72B [2]</td><td style='text-align: center; word-wrap: break-word;'>64</td><td style='text-align: center; word-wrap: break-word;'>65.77</td><td style='text-align: center; word-wrap: break-word;'>60.55</td><td style='text-align: center; word-wrap: break-word;'>69.83</td><td style='text-align: center; word-wrap: break-word;'>51.69</td><td style='text-align: center; word-wrap: break-word;'>69.31</td><td style='text-align: center; word-wrap: break-word;'>54.35</td><td style='text-align: center; word-wrap: break-word;'>61.92</td><td style='text-align: center; word-wrap: break-word;'>52.53</td><td style='text-align: center; word-wrap: break-word;'>60.81</td><td style='text-align: center; word-wrap: break-word;'>57.53</td><td style='text-align: center; word-wrap: break-word;'>56.95</td><td style='text-align: center; word-wrap: break-word;'>38.83</td><td style='text-align: center; word-wrap: break-word;'>64.07</td><td style='text-align: center; word-wrap: break-word;'>45.00</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-Video-7B [15]</td><td style='text-align: center; word-wrap: break-word;'>64</td><td style='text-align: center; word-wrap: break-word;'>69.13</td><td style='text-align: center; word-wrap: break-word;'>58.72</td><td style='text-align: center; word-wrap: break-word;'>68.83</td><td style='text-align: center; word-wrap: break-word;'>49.44</td><td style='text-align: center; word-wrap: break-word;'>74.26</td><td style='text-align: center; word-wrap: break-word;'>59.78</td><td style='text-align: center; word-wrap: break-word;'>63.52</td><td style='text-align: center; word-wrap: break-word;'>56.23</td><td style='text-align: center; word-wrap: break-word;'>57.43</td><td style='text-align: center; word-wrap: break-word;'>7.53</td><td style='text-align: center; word-wrap: break-word;'>40.4</td><td style='text-align: center; word-wrap: break-word;'>34.10</td><td style='text-align: center; word-wrap: break-word;'>69.95</td><td style='text-align: center; word-wrap: break-word;'>60.42</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-OV-7B [3]</td><td style='text-align: center; word-wrap: break-word;'>64</td><td style='text-align: center; word-wrap: break-word;'>66.44</td><td style='text-align: center; word-wrap: break-word;'>57.80</td><td style='text-align: center; word-wrap: break-word;'>73.28</td><td style='text-align: center; word-wrap: break-word;'>53.37</td><td style='text-align: center; word-wrap: break-word;'>71.29</td><td style='text-align: center; word-wrap: break-word;'>61.96</td><td style='text-align: center; word-wrap: break-word;'>64.02</td><td style='text-align: center; word-wrap: break-word;'>54.21</td><td style='text-align: center; word-wrap: break-word;'>55.41</td><td style='text-align: center; word-wrap: break-word;'>21.51</td><td style='text-align: center; word-wrap: break-word;'>43.71</td><td style='text-align: center; word-wrap: break-word;'>25.64</td><td style='text-align: center; word-wrap: break-word;'>67.09</td><td style='text-align: center; word-wrap: break-word;'>58.75</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2-VL-72B [2]</td><td style='text-align: center; word-wrap: break-word;'>64</td><td style='text-align: center; word-wrap: break-word;'>60.40</td><td style='text-align: center; word-wrap: break-word;'>50.46</td><td style='text-align: center; word-wrap: break-word;'>56.03</td><td style='text-align: center; word-wrap: break-word;'>47.19</td><td style='text-align: center; word-wrap: break-word;'>66.34</td><td style='text-align: center; word-wrap: break-word;'>55.43</td><td style='text-align: center; word-wrap: break-word;'>55.98</td><td style='text-align: center; word-wrap: break-word;'>47.81</td><td style='text-align: center; word-wrap: break-word;'>35.48</td><td style='text-align: center; word-wrap: break-word;'>56.08</td><td style='text-align: center; word-wrap: break-word;'>46.46</td><td style='text-align: center; word-wrap: break-word;'>31.66</td><td style='text-align: center; word-wrap: break-word;'>65.82</td><td style='text-align: center; word-wrap: break-word;'>48.75</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>InternVL-V2-8B [76]</td><td style='text-align: center; word-wrap: break-word;'>64</td><td style='text-align: center; word-wrap: break-word;'>67.11</td><td style='text-align: center; word-wrap: break-word;'>60.55</td><td style='text-align: center; word-wrap: break-word;'>63.79</td><td style='text-align: center; word-wrap: break-word;'>46.07</td><td style='text-align: center; word-wrap: break-word;'>68.32</td><td style='text-align: center; word-wrap: break-word;'>56.52</td><td style='text-align: center; word-wrap: break-word;'>60.39</td><td style='text-align: center; word-wrap: break-word;'>48.15</td><td style='text-align: center; word-wrap: break-word;'>57.43</td><td style='text-align: center; word-wrap: break-word;'>24.73</td><td style='text-align: center; word-wrap: break-word;'>43.44</td><td style='text-align: center; word-wrap: break-word;'>26.5</td><td style='text-align: center; word-wrap: break-word;'>59.14</td><td style='text-align: center; word-wrap: break-word;'>54.14</td></tr><tr><td colspan="15">Open-Source Models (Streaming), Single-Turn Evaluation</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Flash-VStream-7B [11]</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>24.16</td><td style='text-align: center; word-wrap: break-word;'>29.36</td><td style='text-align: center; word-wrap: break-word;'>28.45</td><td style='text-align: center; word-wrap: break-word;'>33.71</td><td style='text-align: center; word-wrap: break-word;'>25.74</td><td style='text-align: center; word-wrap: break-word;'>28.80</td><td style='text-align: center; word-wrap: break-word;'>28.37</td><td style='text-align: center; word-wrap: break-word;'>39.06</td><td style='text-align: center; word-wrap: break-word;'>37.16</td><td style='text-align: center; word-wrap: break-word;'>5.91</td><td style='text-align: center; word-wrap: break-word;'>27.38</td><td style='text-align: center; word-wrap: break-word;'>8.02</td><td style='text-align: center; word-wrap: break-word;'>67.25</td><td style='text-align: center; word-wrap: break-word;'>60.00</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLM-Online-8B [10]</td><td style='text-align: center; word-wrap: break-word;'>2 FPS</td><td style='text-align: center; word-wrap: break-word;'>8.05</td><td style='text-align: center; word-wrap: break-word;'>23.85</td><td style='text-align: center; word-wrap: break-word;'>12.07</td><td style='text-align: center; word-wrap: break-word;'>14.04</td><td style='text-align: center; word-wrap: break-word;'>45.54</td><td style='text-align: center; word-wrap: break-word;'>21.20</td><td style='text-align: center; word-wrap: break-word;'>20.79</td><td style='text-align: center; word-wrap: break-word;'>22.22</td><td style='text-align: center; word-wrap: break-word;'>18.80</td><td style='text-align: center; word-wrap: break-word;'>12.18</td><td style='text-align: center; word-wrap: break-word;'>17.73</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Dispider [13]</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>57.72</td><td style='text-align: center; word-wrap: break-word;'>49.54</td><td style='text-align: center; word-wrap: break-word;'>62.07</td><td style='text-align: center; word-wrap: break-word;'>44.94</td><td style='text-align: center; word-wrap: break-word;'>61.39</td><td style='text-align: center; word-wrap: break-word;'>51.63</td><td style='text-align: center; word-wrap: break-word;'>54.55</td><td style='text-align: center; word-wrap: break-word;'>48.48</td><td style='text-align: center; word-wrap: break-word;'>55.41</td><td style='text-align: center; word-wrap: break-word;'>4.30</td><td style='text-align: center; word-wrap: break-word;'>36.06</td><td style='text-align: center; word-wrap: break-word;'>18.05</td><td style='text-align: center; word-wrap: break-word;'>37.36</td><td style='text-align: center; word-wrap: break-word;'>48.75</td></tr><tr><td colspan="15">Models under StreamBridge (Offline) → Streaming), Multi-Turn Evaluation</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Oryx-1.5-7B $ ^{\dagger} $ [1]</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>60.40</td><td style='text-align: center; word-wrap: break-word;'>52.29</td><td style='text-align: center; word-wrap: break-word;'>69.83</td><td style='text-align: center; word-wrap: break-word;'>50.00</td><td style='text-align: center; word-wrap: break-word;'>65.35</td><td style='text-align: center; word-wrap: break-word;'>57.61</td><td style='text-align: center; word-wrap: break-word;'>59.25</td><td style='text-align: center; word-wrap: break-word;'>54.21</td><td style='text-align: center; word-wrap: break-word;'>55.41</td><td style='text-align: center; word-wrap: break-word;'>5.40</td><td style='text-align: center; word-wrap: break-word;'>38.33</td><td style='text-align: center; word-wrap: break-word;'>20.65</td><td style='text-align: center; word-wrap: break-word;'>37.56</td><td style='text-align: center; word-wrap: break-word;'>40.00</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>+ Stream-IT</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>84.56</td><td style='text-align: center; word-wrap: break-word;'>75.23</td><td style='text-align: center; word-wrap: break-word;'>70.69</td><td style='text-align: center; word-wrap: break-word;'>50.56</td><td style='text-align: center; word-wrap: break-word;'>74.26</td><td style='text-align: center; word-wrap: break-word;'>71.74</td><td style='text-align: center; word-wrap: break-word;'>71.17</td><td style='text-align: center; word-wrap: break-word;'>69.02</td><td style='text-align: center; word-wrap: break-word;'>59.50</td><td style='text-align: center; word-wrap: break-word;'>79.03</td><td style='text-align: center; word-wrap: break-word;'>69.17</td><td style='text-align: center; word-wrap: break-word;'>20.51</td><td style='text-align: center; word-wrap: break-word;'>66.89</td><td style='text-align: center; word-wrap: break-word;'>60.41</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-OV-7B $ ^{\dagger} $ [3]</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>58.39</td><td style='text-align: center; word-wrap: break-word;'>59.63</td><td style='text-align: center; word-wrap: break-word;'>69.82</td><td style='text-align: center; word-wrap: break-word;'>44.38</td><td style='text-align: center; word-wrap: break-word;'>76.23</td><td style='text-align: center; word-wrap: break-word;'>61.41</td><td style='text-align: center; word-wrap: break-word;'>61.64</td><td style='text-align: center; word-wrap: break-word;'>53.87</td><td style='text-align: center; word-wrap: break-word;'>54.72</td><td style='text-align: center; word-wrap: break-word;'>30.64</td><td style='text-align: center; word-wrap: break-word;'>46.41</td><td style='text-align: center; word-wrap: break-word;'>14.41</td><td style='text-align: center; word-wrap: break-word;'>51.23</td><td style='text-align: center; word-wrap: break-word;'>43.33</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>+ Stream-IT</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>74.50</td><td style='text-align: center; word-wrap: break-word;'>77.06</td><td style='text-align: center; word-wrap: break-word;'>70.69</td><td style='text-align: center; word-wrap: break-word;'>54.49</td><td style='text-align: center; word-wrap: break-word;'>73.27</td><td style='text-align: center; word-wrap: break-word;'>69.57</td><td style='text-align: center; word-wrap: break-word;'>69.93</td><td style='text-align: center; word-wrap: break-word;'>66.67</td><td style='text-align: center; word-wrap: break-word;'>61.49</td><td style='text-align: center; word-wrap: break-word;'>85.48</td><td style='text-align: center; word-wrap: break-word;'>71.21</td><td style='text-align: center; word-wrap: break-word;'>17.83</td><td style='text-align: center; word-wrap: break-word;'>66.06</td><td style='text-align: center; word-wrap: break-word;'>61.67</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2-VL-7B $ ^{\dagger} $ [2]</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>65.10</td><td style='text-align: center; word-wrap: break-word;'>64.22</td><td style='text-align: center; word-wrap: break-word;'>64.66</td><td style='text-align: center; word-wrap: break-word;'>46.63</td><td style='text-align: center; word-wrap: break-word;'>74.26</td><td style='text-align: center; word-wrap: break-word;'>65.22</td><td style='text-align: center; word-wrap: break-word;'>63.35</td><td style='text-align: center; word-wrap: break-word;'>55.56</td><td style='text-align: center; word-wrap: break-word;'>60.14</td><td style='text-align: center; word-wrap: break-word;'>62.90</td><td style='text-align: center; word-wrap: break-word;'>59.53</td><td style='text-align: center; word-wrap: break-word;'>22.14</td><td style='text-align: center; word-wrap: break-word;'>61.12</td><td style='text-align: center; word-wrap: break-word;'>49.58</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>+ Stream-IT</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>84.56</td><td style='text-align: center; word-wrap: break-word;'>71.56</td><td style='text-align: center; word-wrap: break-word;'>74.14</td><td style='text-align: center; word-wrap: break-word;'>49.44</td><td style='text-align: center; word-wrap: break-word;'>75.25</td><td style='text-align: center; word-wrap: break-word;'>72.83</td><td style='text-align: center; word-wrap: break-word;'>71.30</td><td style='text-align: center; word-wrap: break-word;'>67.68</td><td style='text-align: center; word-wrap: break-word;'>57.43</td><td style='text-align: center; word-wrap: break-word;'>79.03</td><td style='text-align: center; word-wrap: break-word;'>68.05</td><td style='text-align: center; word-wrap: break-word;'>19.17</td><td style='text-align: center; word-wrap: break-word;'>64.25</td><td style='text-align: center; word-wrap: break-word;'>61.67</td></tr></table>

<div style="text-align: center;">Table 10: Full results on OVO-Bench.† means models under StreamBridge framework</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Method</td><td rowspan="2"># of Frames</td><td colspan="5">Real-Time Visual Understanding</td><td colspan="5">Omni-Source Understanding</td><td colspan="5">Contextual Understanding</td><td style='text-align: center; word-wrap: break-word;'>Overall.</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>OP</td><td style='text-align: center; word-wrap: break-word;'>CR</td><td style='text-align: center; word-wrap: break-word;'>CS</td><td style='text-align: center; word-wrap: break-word;'>ATP</td><td style='text-align: center; word-wrap: break-word;'>EU</td><td style='text-align: center; word-wrap: break-word;'>TR</td><td style='text-align: center; word-wrap: break-word;'>PR</td><td style='text-align: center; word-wrap: break-word;'>SU</td><td style='text-align: center; word-wrap: break-word;'>ACV</td><td style='text-align: center; word-wrap: break-word;'>CT</td><td style='text-align: center; word-wrap: break-word;'>AVG.</td><td style='text-align: center; word-wrap: break-word;'>ER</td><td style='text-align: center; word-wrap: break-word;'>SCU</td><td style='text-align: center; word-wrap: break-word;'>SD</td><td style='text-align: center; word-wrap: break-word;'>MA</td><td style='text-align: center; word-wrap: break-word;'>AVG.</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td colspan="18">Human</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Human</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>89.47</td><td style='text-align: center; word-wrap: break-word;'>92.00</td><td style='text-align: center; word-wrap: break-word;'>93.60</td><td style='text-align: center; word-wrap: break-word;'>91.47</td><td style='text-align: center; word-wrap: break-word;'>95.65</td><td style='text-align: center; word-wrap: break-word;'>92.52</td><td style='text-align: center; word-wrap: break-word;'>88.00</td><td style='text-align: center; word-wrap: break-word;'>88.75</td><td style='text-align: center; word-wrap: break-word;'>89.74</td><td style='text-align: center; word-wrap: break-word;'>91.30</td><td style='text-align: center; word-wrap: break-word;'>88.00</td><td style='text-align: center; word-wrap: break-word;'>88.24</td><td style='text-align: center; word-wrap: break-word;'>93.60</td><td style='text-align: center; word-wrap: break-word;'>90.27</td><td style='text-align: center; word-wrap: break-word;'>90.27</td><td style='text-align: center; word-wrap: break-word;'>93.55</td><td style='text-align: center; word-wrap: break-word;'>91.66</td></tr><tr><td colspan="18">Proprietary Models (Offline), Single-Turn Evaluation</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Gemini 1.5 pro [23]</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>79.02</td><td style='text-align: center; word-wrap: break-word;'>80.47</td><td style='text-align: center; word-wrap: break-word;'>83.54</td><td style='text-align: center; word-wrap: break-word;'>79.67</td><td style='text-align: center; word-wrap: break-word;'>80.00</td><td style='text-align: center; word-wrap: break-word;'>84.74</td><td style='text-align: center; word-wrap: break-word;'>77.78</td><td style='text-align: center; word-wrap: break-word;'>64.23</td><td style='text-align: center; word-wrap: break-word;'>71.95</td><td style='text-align: center; word-wrap: break-word;'>48.70</td><td style='text-align: center; word-wrap: break-word;'>75.69</td><td style='text-align: center; word-wrap: break-word;'>46.80</td><td style='text-align: center; word-wrap: break-word;'>39.60</td><td style='text-align: center; word-wrap: break-word;'>74.90</td><td style='text-align: center; word-wrap: break-word;'>80.00</td><td style='text-align: center; word-wrap: break-word;'>60.22</td><td style='text-align: center; word-wrap: break-word;'>51.41</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>GPT-4o [22]</td><td style='text-align: center; word-wrap: break-word;'>64</td><td style='text-align: center; word-wrap: break-word;'>77.11</td><td style='text-align: center; word-wrap: break-word;'>80.47</td><td style='text-align: center; word-wrap: break-word;'>83.91</td><td style='text-align: center; word-wrap: break-word;'>76.47</td><td style='text-align: center; word-wrap: break-word;'>70.19</td><td style='text-align: center; word-wrap: break-word;'>83.80</td><td style='text-align: center; word-wrap: break-word;'>66.67</td><td style='text-align: center; word-wrap: break-word;'>62.19</td><td style='text-align: center; word-wrap: break-word;'>69.12</td><td style='text-align: center; word-wrap: break-word;'>49.22</td><td style='text-align: center; word-wrap: break-word;'>73.26</td><td style='text-align: center; word-wrap: break-word;'>41.20</td><td style='text-align: center; word-wrap: break-word;'>25.70</td><td style='text-align: center; word-wrap: break-word;'>43.60</td><td style='text-align: center; word-wrap: break-word;'>56.00</td><td style='text-align: center; word-wrap: break-word;'>44.50</td><td style='text-align: center; word-wrap: break-word;'>41.20</td></tr><tr><td colspan="18">OpenSource Models</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-OV-7B [3]</td><td style='text-align: center; word-wrap: break-word;'>32</td><td style='text-align: center; word-wrap: break-word;'>80.38</td><td style='text-align: center; word-wrap: break-word;'>74.22</td><td style='text-align: center; word-wrap: break-word;'>76.03</td><td style='text-align: center; word-wrap: break-word;'>80.72</td><td style='text-align: center; word-wrap: break-word;'>72.67</td><td style='text-align: center; word-wrap: break-word;'>71.65</td><td style='text-align: center; word-wrap: break-word;'>67.59</td><td style='text-align: center; word-wrap: break-word;'>65.45</td><td style='text-align: center; word-wrap: break-word;'>65.72</td><td style='text-align: center; word-wrap: break-word;'>45.08</td><td style='text-align: center; word-wrap: break-word;'>71.12</td><td style='text-align: center; word-wrap: break-word;'>40.80</td><td style='text-align: center; word-wrap: break-word;'>37.20</td><td style='text-align: center; word-wrap: break-word;'>33.60</td><td style='text-align: center; word-wrap: break-word;'>44.80</td><td style='text-align: center; word-wrap: break-word;'>38.40</td><td style='text-align: center; word-wrap: break-word;'>35.60</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2-VL-7B [2]</td><td style='text-align: center; word-wrap: break-word;'>0.2-1 FPS</td><td style='text-align: center; word-wrap: break-word;'>75.20</td><td style='text-align: center; word-wrap: break-word;'>82.81</td><td style='text-align: center; word-wrap: break-word;'>73.19</td><td style='text-align: center; word-wrap: break-word;'>77.45</td><td style='text-align: center; word-wrap: break-word;'>68.32</td><td style='text-align: center; word-wrap: break-word;'>71.03</td><td style='text-align: center; word-wrap: break-word;'>72.22</td><td style='text-align: center; word-wrap: break-word;'>61.19</td><td style='text-align: center; word-wrap: break-word;'>61.47</td><td style='text-align: center; word-wrap: break-word;'>46.11</td><td style='text-align: center; word-wrap: break-word;'>69.04</td><td style='text-align: center; word-wrap: break-word;'>41.20</td><td style='text-align: center; word-wrap: break-word;'>22.00</td><td style='text-align: center; word-wrap: break-word;'>32.80</td><td style='text-align: center; word-wrap: break-word;'>43.60</td><td style='text-align: center; word-wrap: break-word;'>34.90</td><td style='text-align: center; word-wrap: break-word;'>31.20</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>InternVL-V2-8B [76]</td><td style='text-align: center; word-wrap: break-word;'>16</td><td style='text-align: center; word-wrap: break-word;'>68.12</td><td style='text-align: center; word-wrap: break-word;'>69.40</td><td style='text-align: center; word-wrap: break-word;'>69.40</td><td style='text-align: center; word-wrap: break-word;'>77.12</td><td style='text-align: center; word-wrap: break-word;'>67.70</td><td style='text-align: center; word-wrap: break-word;'>62.93</td><td style='text-align: center; word-wrap: break-word;'>59.26</td><td style='text-align: center; word-wrap: break-word;'>53.25</td><td style='text-align: center; word-wrap: break-word;'>54.96</td><td style='text-align: center; word-wrap: break-word;'>56.48</td><td style='text-align: center; word-wrap: break-word;'>63.72</td><td style='text-align: center; word-wrap: break-word;'>37.60</td><td style='text-align: center; word-wrap: break-word;'>26.40</td><td style='text-align: center; word-wrap: break-word;'>37.20</td><td style='text-align: center; word-wrap: break-word;'>42.00</td><td style='text-align: center; word-wrap: break-word;'>35.80</td><td style='text-align: center; word-wrap: break-word;'>32.00</td></tr><tr><td colspan="18">Open-Source Models (Streaming), Single-Turn Evaluation</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Flash-VStream-7B [1]</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>25.89</td><td style='text-align: center; word-wrap: break-word;'>43.57</td><td style='text-align: center; word-wrap: break-word;'>24.91</td><td style='text-align: center; word-wrap: break-word;'>23.87</td><td style='text-align: center; word-wrap: break-word;'>13.08</td><td style='text-align: center; word-wrap: break-word;'>18.52</td><td style='text-align: center; word-wrap: break-word;'>25.20</td><td style='text-align: center; word-wrap: break-word;'>23.87</td><td style='text-align: center; word-wrap: break-word;'>48.70</td><td style='text-align: center; word-wrap: break-word;'>32.33</td><td style='text-align: center; word-wrap: break-word;'>25.91</td><td style='text-align: center; word-wrap: break-word;'>24.90</td><td style='text-align: center; word-wrap: break-word;'>25.60</td><td style='text-align: center; word-wrap: break-word;'>28.40</td><td style='text-align: center; word-wrap: break-word;'>26.00</td><td style='text-align: center; word-wrap: break-word;'>24.18</td><td style='text-align: center; word-wrap: break-word;'>24.04</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLM-Online-8B [10]</td><td style='text-align: center; word-wrap: break-word;'>2 FPS</td><td style='text-align: center; word-wrap: break-word;'>39.07</td><td style='text-align: center; word-wrap: break-word;'>40.06</td><td style='text-align: center; word-wrap: break-word;'>34.49</td><td style='text-align: center; word-wrap: break-word;'>31.05</td><td style='text-align: center; word-wrap: break-word;'>45.96</td><td style='text-align: center; word-wrap: break-word;'>32.40</td><td style='text-align: center; word-wrap: break-word;'>31.48</td><td style='text-align: center; word-wrap: break-word;'>34.16</td><td style='text-align: center; word-wrap: break-word;'>42.49</td><td style='text-align: center; word-wrap: break-word;'>37.89</td><td style='text-align: center; word-wrap: break-word;'>15.99</td><td style='text-align: center; word-wrap: break-word;'>31.20</td><td style='text-align: center; word-wrap: break-word;'>26.51</td><td style='text-align: center; word-wrap: break-word;'>20.10</td><td style='text-align: center; word-wrap: break-word;'>32.00</td><td style='text-align: center; word-wrap: break-word;'>28.45</td><td style='text-align: center; word-wrap: break-word;'>24.19</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Dispiper [13]</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>74.92</td><td style='text-align: center; word-wrap: break-word;'>75.53</td><td style='text-align: center; word-wrap: break-word;'>74.10</td><td style='text-align: center; word-wrap: break-word;'>78.08</td><td style='text-align: center; word-wrap: break-word;'>74.44</td><td style='text-align: center; word-wrap: break-word;'>59.92</td><td style='text-align: center; word-wrap: break-word;'>76.14</td><td style='text-align: center; word-wrap: break-word;'>62.91</td><td style='text-align: center; word-wrap: break-word;'>62.12</td><td style='text-align: center; word-wrap: break-word;'>45.80</td><td style='text-align: center; word-wrap: break-word;'>70.74</td><td style='text-align: center; word-wrap: break-word;'>35.46</td><td style='text-align: center; word-wrap: break-word;'>22.26</td><td style='text-align: center; word-wrap: break-word;'>38.57</td><td style='text-align: center; word-wrap: break-word;'>43.34</td><td style='text-align: center; word-wrap: break-word;'>35.66</td><td style='text-align: center; word-wrap: break-word;'>32.48</td></tr><tr><td colspan="18">Models under Stream-Bridge (Offline) → Streaming, Multi-Turn Evaluation</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Oryx-1.5-TB $ ^{1} $ [1]</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>78.47</td><td style='text-align: center; word-wrap: break-word;'>77.17</td><td style='text-align: center; word-wrap: break-word;'>83.86</td><td style='text-align: center; word-wrap: break-word;'>80.20</td><td style='text-align: center; word-wrap: break-word;'>71.07</td><td style='text-align: center; word-wrap: break-word;'>66.98</td><td style='text-align: center; word-wrap: break-word;'>79.63</td><td style='text-align: center; word-wrap: break-word;'>61.38</td><td style='text-align: center; word-wrap: break-word;'>66.29</td><td style='text-align: center; word-wrap: break-word;'>40.93</td><td style='text-align: center; word-wrap: break-word;'>70.59</td><td style='text-align: center; word-wrap: break-word;'>30.00</td><td style='text-align: center; word-wrap: break-word;'>15.20</td><td style='text-align: center; word-wrap: break-word;'>33.60</td><td style='text-align: center; word-wrap: break-word;'>43.20</td><td style='text-align: center; word-wrap: break-word;'>30.50</td><td style='text-align: center; word-wrap: break-word;'>20.40</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>+ Stream-IT</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>82.29</td><td style='text-align: center; word-wrap: break-word;'>77.95</td><td style='text-align: center; word-wrap: break-word;'>87.98</td><td style='text-align: center; word-wrap: break-word;'>86.77</td><td style='text-align: center; word-wrap: break-word;'>84.97</td><td style='text-align: center; word-wrap: break-word;'>81.31</td><td style='text-align: center; word-wrap: break-word;'>76.85</td><td style='text-align: center; word-wrap: break-word;'>69.92</td><td style='text-align: center; word-wrap: break-word;'>71.96</td><td style='text-align: center; word-wrap: break-word;'>35.23</td><td style='text-align: center; word-wrap: break-word;'>74.79</td><td style='text-align: center; word-wrap: break-word;'>19.20</td><td style='text-align: center; word-wrap: break-word;'>14.40</td><td style='text-align: center; word-wrap: break-word;'>52.00</td><td style='text-align: center; word-wrap: break-word;'>29.20</td><td style='text-align: center; word-wrap: break-word;'>28.70</td><td style='text-align: center; word-wrap: break-word;'>14.40</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-OV-7B $ ^{1} $ [3]</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>76.84</td><td style='text-align: center; word-wrap: break-word;'>77.17</td><td style='text-align: center; word-wrap: break-word;'>82.60</td><td style='text-align: center; word-wrap: break-word;'>75.25</td><td style='text-align: center; word-wrap: break-word;'>64.15</td><td style='text-align: center; word-wrap: break-word;'>75.00</td><td style='text-align: center; word-wrap: break-word;'>61.38</td><td style='text-align: center; word-wrap: break-word;'>61.19</td><td style='text-align: center; word-wrap: break-word;'>46.11</td><td style='text-align: center; word-wrap: break-word;'>68.39</td><td style='text-align: center; word-wrap: break-word;'>24.40</td><td style='text-align: center; word-wrap: break-word;'>12.00</td><td style='text-align: center; word-wrap: break-word;'>32.40</td><td style='text-align: center; word-wrap: break-word;'>37.60</td><td style='text-align: center; word-wrap: break-word;'>26.60</td><td style='text-align: center; word-wrap: break-word;'>20.00</td><td style='text-align: center; word-wrap: break-word;'>19.60</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>+ Stream-IT</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>82.29</td><td style='text-align: center; word-wrap: break-word;'>72.44</td><td style='text-align: center; word-wrap: break-word;'>92.09</td><td style='text-align: center; word-wrap: break-word;'>80.86</td><td style='text-align: center; word-wrap: break-word;'>71.47</td><td style='text-align: center; word-wrap: break-word;'>64.76</td><td style='text-align: center; word-wrap: break-word;'>75.00</td><td style='text-align: center; word-wrap: break-word;'>62.20</td><td style='text-align: center; word-wrap: break-word;'>70.26</td><td style='text-align: center; word-wrap: break-word;'>28.50</td><td style='text-align: center; word-wrap: break-word;'>70.92</td><td style='text-align: center; word-wrap: break-word;'>20.80</td><td style='text-align: center; word-wrap: break-word;'>13.20</td><td style='text-align: center; word-wrap: break-word;'>43.60</td><td style='text-align: center; word-wrap: break-word;'>27.60</td><td style='text-align: center; word-wrap: break-word;'>26.30</td><td style='text-align: center; word-wrap: break-word;'>20.40</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2-VL-7B [2]</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>80.38</td><td style='text-align: center; word-wrap: break-word;'>78.74</td><td style='text-align: center; word-wrap: break-word;'>83.22</td><td style='text-align: center; word-wrap: break-word;'>79.26</td><td style='text-align: center; word-wrap: break-word;'>74.21</td><td style='text-align: center; word-wrap: break-word;'>69.47</td><td style='text-align: center; word-wrap: break-word;'>77.78</td><td style='text-align: center; word-wrap: break-word;'>63.41</td><td style='text-align: center; word-wrap: break-word;'>69.97</td><td style='text-align: center; word-wrap: break-word;'>43.01</td><td style='text-align: center; word-wrap: break-word;'>72.01</td><td style='text-align: center; word-wrap: break-word;'>32.00</td><td style='text-align: center; word-wrap: break-word;'>15.20</td><td style='text-align: center; word-wrap: break-word;'>39.60</td><td style='text-align: center; word-wrap: break-word;'>38.40</td><td style='text-align: center; word-wrap: break-word;'>31.30</td><td style='text-align: center; word-wrap: break-word;'>25.20</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>+ Stream-IT</td><td style='text-align: center; word-wrap: break-word;'>1 FPS</td><td style='text-align: center; word-wrap: break-word;'>84.74</td><td style='text-align: center; word-wrap: break-word;'>82.68</td><td style='text-align: center; word-wrap: break-word;'>88.92</td><td style='text-align: center; word-wrap: break-word;'>89.77</td><td style='text-align: center; word-wrap: break-word;'>77.36</td><td style='text-align: center; word-wrap: break-word;'>85.36</td><td style='text-align: center; word-wrap: break-word;'>84.26</td><td style='text-align: center; word-wrap: break-word;'>69.92</td><td style='text-align: center; word-wrap: break-word;'>71.67</td><td style='text-align: center; word-wrap: break-word;'>35.75</td><td style='text-align: center; word-wrap: break-word;'>77.04</td><td style='text-align: center; word-wrap: break-word;'>18.00</td><td style='text-align: center; word-wrap: break-word;'>13.20</td><td style='text-align: center; word-wrap: break-word;'>43.60</td><td style='text-align: center; word-wrap: break-word;'>21.60</td><td style='text-align: center; word-wrap: break-word;'>24.10</td><td style='text-align: center; word-wrap: break-word;'>14.00</td></tr></table>

<div style="text-align: center;">Table 11: Full results on Streaming-Bench.† means models under StreamBridge framework</div>


20

## I Pseudo Code of the Round-Decayed Compression in a PyTorch-like Style

def Round_Decayed_Compression (inputs_embeds, max_len, token_per_frame):
    input_embeds: [1, seq_len, dim], interleaved embeddings of video and text;
max_len: the predefined maximum sequence length of inputs_embeds;
token_per_frame: the number of tokens per frame;

# compress_target_num is the number of tokens that need to be compressed,
# should be integer multiples of token_per_frame
redundant_frame_num = int(((inputs_embeds.shape[1] - max_len)/token_per_frame) + 1
compress_target_num = token_per_frame * redundant_frame_num

# split inputs_embeds into image_embeds and text_embeds by round,
# e.g., image_embeds[i] is the visual tokens of the i-th round,
# and len(image_embeds) == len(text_embeds) == number of rounds;
image_embeds, text_embeds = split_image_and_text(inputs_embeds)
new_inputs_embeds = []

# compress visual tokens round by round
for round_idx in range(len(image_embeds)):
    current_image_embeds = image_embeds[round_idx]
    current_text_embeds = text_embeds[round_idx]
    if compress_target_num > 0 and current_image_embeds.shape[1] >=
        token_per_frame*2:
            >>>
            >>>
        compress current_image_embeds into [1, token_per_frame, dim];
        >>>
        if current_image_embeds.shape[1] <= compress_target_num +
            token_per_frame:
            >>>
            >>>
        current_frame_num = current_image_embeds.shape[1] // token_per_frame
        current_image_embeds = current_image_embeds.reshape(1,
            current_frame_num, token_per_frame,
            current_image_embeds.shape[-1])
        current_image_embeds = current_image_embeds.mean(dim=1)
        compress_target_num -= (current_frame_num-1)*token_per_frame
        >>>
        if
            if current_image_embeds's first compress_target_num +
                token_per_frame tokens into [1, token_per_frame, dim], and reserve
                the rest tokens;
            >>>
            >>>
        else:
            if
            if current_image_embeds's first compress_target_num +
                token_per_frame tokens into [1, token_per_frame, dim], and reserve
                the rest tokens;
            >>>
            >>>
        pre_image_embeds = current_image_embeds[:,
            :compress_target_num+token_per_frame, :]
            pre_frame_num = pre_image_embeds.shape[1]//token_per_frame
            pre_image_embeds = pre_image_embeds.reshape(1,
            compress_target_num//token_per_frame + 1, token_per_frame,
            current_image_embeds.shape[-1])
            pre_image_embeds = pre_image_embeds.mean(dim=1)
            post_image_embeds = current_image_embeds[:,
            compress_target_num+token_per_frame, :]
            compress_target_num -= (pre_frame_num-1)*token_per_frame
            current_image_embeds = torch.cat([pre_image_embeds,
                                 post_image_embeds], dim=1)

    new_inputs_embeds.append(current_image_embeds)
    new_inputs_embeds.append(current_text_embeds)

return torch.cat(new_inputs_embeds, dim=1)

21