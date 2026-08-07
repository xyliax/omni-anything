arXiv:2603.12938v1 [cs.CV] 13 Mar 2026

# Thinking in Streaming Video

Zikang Liu $ ^{1,2*} $, Longteng Guo $ ^{1*} $, Handong Li $ ^{1,2*} $, Ru Zhen $ ^{3} $, Xingjian He $ ^{1} $, Ruyi Ji $ ^{1} $, Xiaoming Ren $ ^{3} $, Yanhao Zhang $ ^{3} $, Haonan Lu $ ^{3} $, and Jing Liu $ ^{1,2**} $

 $ ^{1} $ Institute of Automation, Chinese Academy of Sciences

 $ ^{2} $ School of Artificial Intelligence, University of Chinese Academy of Sciences

 $ ^{3} $ OPPO AI Center, OPPO Inc.

{liuzikang2023}@ia.ac.cn. {longteng.guo.iliul}@nlpr.ia.ac.cn

{liuzikang2023}@ia.ac.cn, {longteng.guo,jliu}@nlpr.ia.ac.cn

Abstract. Real-time understanding of continuous video streams is essential for interactive assistants and multimodal agents operating in dynamic environments. However, most existing video reasoning approaches follow a batch paradigm that defers reasoning until the full video context is observed, resulting in high latency and growing computational cost that are incompatible with streaming scenarios. In this paper, we introduce ThinkStream, a framework for streaming video reasoning based on a Watch-Think-Speak paradigm that enables models to incrementally update their understanding as new video observations arrive. At each step, the model performs a short reasoning update and decides whether sufficient evidence has accumulated to produce a response. To support long-horizon streaming, we propose Reasoning-Compressed Streaming Memory (RCSM), which treats intermediate reasoning traces as compact semantic memory that replaces outdated visual tokens while preserving essential context. We further train the model using a Streaming Reinforcement Learning with Verifiable Rewards scheme that aligns incremental reasoning and response timing with the requirements of streaming interaction. Experiments on multiple streaming video benchmarks show that ThinkStream significantly outperforms existing online video models while maintaining low latency and memory usage. Code, models and data will be released at https://github.com/johncaged/ThinkStream.

Keywords: Streaming Video · Incremental Reasoning · Memory

## 1 Introduction

Real-time understanding of continuous video streams is a core capability for interactive assistants and multimodal agents [28, 34, 35]. Unlike offline video question answering [1, 2, 15, 46], streaming scenarios impose several fundamental constraints: (i) strict causality, where reasoning must rely only on observations available up to the current moment; (ii) low computation and memory usage, requiring inference latency and resource usage to remain stable even as the stream

 $ ^{*} $ Equal contribution.

 $ ^{**} $ Corresponding author.

2

Z. Liu et al.

<div style="text-align: center;"><img src="imgs/img_in_image_box_271_229_951_497.jpg" alt="Image" width="55%" />

V
Incoming
Video Stream

<think>
<think>: Video starts.
First-person view of a kitchen. Person in green shirt stands before a “Incremental Resoning”
white stove...
</think>

<think>: ...sink. They appear to be preparing to clean or organize the kitchen tools after the meal...
</think>

<think>: The cook is handling the board near the sink. He then turns around and picks up a new...
</think>

<response>You just put the board near the sink

<start> (Starts cleaning up) V4

<think>: The video captures the transition from active cooking to cleanup in a kitchen setting...
</think>

<silent>
<silent>
<silent>

</div>


<div style="text-align: center;">Fig. 1: Illustration of the Streaming Watch-Think-Speak paradigm. As video chunks arrive sequentially, the model continuously updates its understanding through incremental reasoning steps (<think>). Each update integrates newly observed evidence with accumulated context. Based on this evolving interpretation, the model decides whether sufficient evidence has been gathered to produce a response (<response>) or whether it should remain silent (<silent>) and continue observing the stream.</div>


grows indefinitely; and (iii) timely interaction, which demands that the system maintain an up-to-date interpretation of the evolving scene to respond or act when necessary.

Such constraints commonly arise in environments where visual events unfold continuously, including real-time assistants observing user activities, monitoring systems detecting emerging events, and embodied agents interacting with dynamic physical environments.

However, most existing video reasoning paradigms remain fundamentally batch: the model first consumes a long video context and only then performs multi-step reasoning to produce an answer [9,33]. This design introduces unacceptable latency and weakens the connection between reasoning steps and the evidence that triggered them. Increasing the depth or length of Chain-of-Thought (CoT) reasoning partially mitigates this issue, but long-form decoding further inflates latency and compute, making it incompatible with continuous streams.

In dynamic environments, human cognition often resembles thinking while observing: people form provisional interpretations from local evidence, refine them as new signals arrive, and act once sufficient confidence has been accumulated. This observation motivates an incremental perspective on streaming video understanding, where reasoning evolves alongside the incoming stream rather than being deferred until the full context is observed.

In this paper, we propose a Streaming Watch-Think-Speak paradigm for video understanding. At each step, the model observes a newly arrived video chunk and performs a short reasoning update that integrates the new evidence with previously accumulated context. Based on this evolving understanding, the model determines whether the available evidence is sufficient to produce a response, or whether it should remain silent and continue observing the stream

Thinking in Streaming Video

3

until more information arrives. As illustrated in Fig. 1, the model produces a structured output consisting of (i) a reasoning segment enclosed in a <think> block and (ii) an interaction action that either emits a response (<response>) or indicates that the model remains silent (<silent>) and continues observing the stream.

Building on this paradigm, we introduce ThinkStream, a framework that enables reasoning-capable multimodal models to operate over long-horizon video streams under low computational resources. The central challenge is to preserve coherent understanding without allowing the visual context, and thus the KV cache, to grow rapidly. To address this, we propose Reasoning-Compressed Streaming Memory (RCSM), which treats intermediate reasoning traces as compact semantic memory. As the stream evolves, outdated visual tokens are evicted while the corresponding reasoning states are retained as long-term semantic anchors, preserving essential historical context while keeping inference cost stable.

To train models that produce such reasoning updates, we introduce a Streaming Reinforcement Learning with Verifiable Rewards (RLVR) framework tailored to Watch-Think-Speak. We design simple rule-based rewards that are automatically verifiable and reflect the requirements of streaming interaction, encouraging the model to generate structured reasoning traces, respond only when sufficient evidence has accumulated, and maintain answer correctness throughout the stream.

Finally, we support large-scale RLVR training and inference with an efficient streaming rollout backend that enables high-throughput inference with dynamic context updates. We also construct a large-scale dataset featuring time-grounded reasoning traces for cold-start supervision and a carefully formatted subset for RLVR training.

Extensive experiments validate the effectiveness of our approach. On dedicated streaming video benchmarks, ThinkStream achieves substantially stronger performance than existing online video models, with even a compact 3B-scale model outperforming significantly larger baselines. Meanwhile, our framework maintains low latency and memory usage over long video streams, enabling real-time inference while preserving strong performance on standard offline video benchmarks.

Our contributions are summarized as follows:

We propose a Streaming Watch-Think-Speak paradigm that formulates streaming video understanding as an incremental reasoning and interaction process, enabling models to continuously update their interpretation while deciding when to respond.

We introduce ThinkStream, a unified framework for long-horizon streaming video reasoning, together with Reasoning-Compressed Streaming Memory (RCSM) that treats reasoning traces as compact semantic memory to replace evicted visual tokens while keeping inference cost much lower.

4

Z. Liu et al.

– We develop a Streaming Reinforcement Learning with RLVR training scheme that aligns incremental reasoning and response timing through automatically verifiable reward signals.

We support scalable training and deployment through an efficient streaming inference backend and construct a large-scale dataset with time-grounded reasoning traces. Our code, models, and datasets will be released to facilitate future research on streaming video reasoning.

## 2 Related Work

### 2.1 Streaming Video Understanding

Transitioning to streaming video for real-time interaction, early frameworks (e.g., VideoLLM-online [3]) rely on direct perception-response cycles lacking intermediate reasoning. To manage massive visual token influxes, subsequent methods introduced specialized memory architectures [16,42,47], KV cache compression [23,38,43] or KV cache sparsification/pruning [4,35]. However, their memory mechanisms remain purely visual, devoid of semantic compression and explicit logical deduction. Furthermore, addressing the proactive output timing ("when to speak") challenge, existing approaches (e.g., EgoSpeak [14], StreamMind [7]) heavily depend on dedicated classification heads or external event triggers. Conversely, our framework eschews external classifiers; by integrating a generative reasoning phase, the model autonomously determines whether to remain silent or respond, seamlessly unifying perception, reasoning, and reaction into a single generative process.

### 2.2 Reasoning in Multimodal Large Language Models

While integrating Chain-of-Thought and Reinforcement Learning has significantly advanced LLMs [36, 37], video-domain adaptations [5, 25, 26, 30, 31] remain confined to offline batch-processing, incompatible with real-time streaming constraints. Conversely, strictly text-based streaming reasoning frameworks like StreamingThinker [27] are ill-equipped for the concurrent think-and-respond demands and dense visual token bottlenecks of continuous video. Recognizing that reasoning advancements are fundamentally driven by RL, we introduce the first streaming RL approach to tackle these multimodal complexities. Furthermore, existing offline compression methods (e.g., LightThinker [44]) merely reduce cache size without leveraging reasoning as active memory. In contrast, our work explicitly repurposes CoT trajectories as compressed semantic memory. By aggressively evicting dense visual tokens while preserving reasoning chains, we propose a mechanism that simultaneously scales reasoning capabilities and bounds KV cache growth for continuous video streaming.

## 3 Streaming Watch-Think-Speak Paradigm

Human perception in continuous environments rarely proceeds as a purely re-active process. As new observations arrive, people constantly form provisional

Thinking in Streaming Video

5

<div style="text-align: center;"><img src="imgs/img_in_image_box_273_234_959_634.jpg" alt="Image" width="56%" />

(a) Streaming Watch-Think-Speak & RLVR

R = R_{format} + R_{time} + R_{acc}

Calculate Reward

Policy Update

G rollouts

Think...
<silent>
Think...
<response>...
Think...
<silent>

Video Large Language Model

User Instruction: What did I do at the beginning?

(b) Reasoning-Compressed Streaming Memory Attention Mask

(c) Streaming Inference

Eager Prefill
(Variable Tokens)

Decode Kernel (CUDA Graph Replay)

Evict Kernel (CUDA Graph Replay)

Chunk-by-Chunk Streaming Loop

</div>


<div style="text-align: center;">Fig. 2: Overview of the ThinkStream framework. (a) Streaming Watch-Think-Speak Paradigm & RLVR: The model undergoes streaming rollouts and policy updates driven by format, latency, and accuracy rewards. (b) Reasoning-Compressed Streaming Memory: Outdated dense video tokens are dynamically evicted from the KV cache, while highly compressed reasoning and response tokens are retained as long-term semantic anchors. (c) Streaming Inference: A custom backend utilizes Eager Prefill for variable tokens and replayable CUDA Graphs for both the Decode and Evict Kernels, enabling an efficient chunk-by-chunk streaming loop with in-place memory shifting.</div>


interpretations, refine them with additional evidence, and occasionally act when the accumulated understanding becomes sufficiently reliable. This process interleaves perception and reasoning: local observations trigger short reasoning updates, and these incremental updates gradually consolidate into a coherent global interpretation of the scene.

### 3.1 Paradigm Design

Inspired by this cognitive pattern, we formulate streaming video understanding as a Watch-Think-Speak loop. Instead of separating perception and reasoning into two independent stages, the model performs incremental reasoning alongside the incoming stream. Each newly observed video segment triggers a short reasoning update that integrates the latest evidence with previously accumulated understanding. Over time, these updates progressively transform local perceptual signals into a structured interpretation of the evolving scene.

Within this paradigm, reasoning operates as a lightweight but continuous process. Upon observing a new video chunk, the model may (1) summarize newly observed events, (2) update hypotheses about ongoing activities or (3) refine

6

Z. Liu et al.

causal or temporal relations inferred earlier. These reasoning steps are intentionally short and localized, ensuring that they can be generated within strict latency constraints while still allowing the model to maintain a coherent internal narrative of the stream.

Following each reasoning update, the model determines whether to respond to the user. When sufficient evidence has accumulated, the model produces an explicit answer; otherwise it remains silent and continues observing the stream.

### 3.2 Formal Definition

Let the incoming video stream be represented as a sequence of temporal chunks  $ \mathcal{V} = \{v_1, v_2, \ldots, v_t, \ldots\} $, where  $ v_t $ denotes the video segment observed at step  $ t $. Let  $ \mathcal{I} $ denote the user instruction or dialogue context. The model maintains a historical state  $ \mathcal{H}_{t-1} $ summarizing the accumulated context from previous steps.

Operationally, each streaming step produces a structured output consisting of a reasoning segment followed by an interaction decision. The output format is defined as  $ \langle \text{think} \rangle r_t \langle / \text{think} \rangle a_t $. Here  $ r_t $ denotes the reasoning tokens generated at step  $ t $, and  $ a_t $ represents the action taken by the model. The action either produces a response or explicitly indicates that the model remains silent.

Formally, given the incoming chunk  $ v_{t} $, the generation process follows

 $$ p(r_{t},a_{t}\mid\mathcal{H}_{t-1},v_{t},\mathcal{I})=\prod_{i=1}^{\vert r_{t}\oplus a_{t}\vert}\pi_{\theta}\big(y_{i}\mid y_{<i},\mathcal{H}_{t-1},v_{t},\mathcal{I}\big), $$ 

where  $ \pi_{\theta} $ denotes the policy model and  $ \oplus $ represents sequence concatenation.

The action space is restricted to two possibilities:

 $$ a_{t}\in\{\langle\mathrm{s i l e n t}\rangle,\langle\mathrm{r e s p o n s e}\rangle\oplus c_{t}\}, $$ 

where $c_{t}$ denotes the generated response content. Emitting $\langle\mathrm{silent}\rangle$ indicates that the model continues observing the stream without responding, while emitting $\langle\mathrm{response}\rangle$ signals that the model has accumulated sufficient evidence to produce an answer.

This formulation allows reasoning to unfold incrementally along the temporal stream. Each reasoning segment  $ r_{t} $ updates the model's internal understanding based solely on observations available up to time t, ensuring strict streaming causality. Meanwhile, the speaking decision  $ a_{t} $ transforms the evolving reasoning state into an interaction policy that determines when the model should respond and when it should continue watching.

## 4 ThinkStream

Building upon our Watch-Think-Speak loop, we introduce ThinkStream, a unified framework that enables reasoning-capable multimodal models to operate under the strict computational constraints of continuous video streams. The

Thinking in Streaming Video

7

central challenge lies in reconciling two competing requirements: maintaining coherent long-horizon understanding over the video stream while preserving real-time inference efficiency.

### 4.1 Reasoning-Compressed Streaming Memory

Continuous video streams naturally produce a large number of visual tokens. If all tokens are retained in the KV cache, both memory usage and attention complexity grow monotonically with time, eventually rendering real-time inference infeasible. However, not all past visual observations are equally important. Early visual details can often be replaced by higher-level semantic summaries once the model has formed a stable interpretation of the scene.

Motivated by this observation, we introduce Reasoning-Compressed Streaming Memory (RCSM). The core idea of RCSM is to treat reasoning tokens as compressed semantic representations of earlier visual observations. Instead of storing the entire history of dense visual tokens, the model gradually replaces outdated visual features with the reasoning traces generated during the streaming reasoning process.

Reasoning-as-Compression State. In the Watch-Think-Speak paradigm, each reasoning segment  $ r_{t} $ reflects the model's interpretation of the newly observed video chunk  $ v_{t} $ conditioned on prior context. These reasoning tokens encode semantic abstractions such as events, temporal relations, and causal hypotheses derived from the raw visual input.

We therefore interpret the reasoning state as a compression operator that transforms dense perceptual evidence into compact symbolic representations. Formally, let  $ KV(\cdot) $ denote the cached key-value representations of tokens. Instead of preserving all visual tokens  $ \{v_1, \ldots, v_t\} $, the model maintains a mixed memory state consisting of recent visual tokens and accumulated reasoning tokens.

The memory state at step t is defined as

 $$ \begin{array}{r}{\mathcal{M}_{t}=\mathrm{C o n c a t}\Big(\{K V(\boldsymbol{v}_{\tau})\}_{\tau=\operatorname*{m a x}(1,t-W+1)}^{t},\{K V(r_{\tau}\oplus a_{\tau})\}_{\tau=1}^{t}\Big),}\end{array} $$ 

where $W$ denotes the size of the visual sliding window. In this design, reasoning tokens act as long-term semantic anchors that preserve the essential interpretation of earlier observations. When the stream length exceeds the window $W$, the earliest visual tokens are evicted from the cache. Let $v_{t-W}$ denote the oldest visual chunk within the window. When a new chunk $v_{t+1}$ arrives, the tokens corresponding to $v_{t-W}$ are removed from the KV cache. This design establishes a natural transition from dense perceptual memory to compressed semantic memory as the stream evolves.

Specifically, the number of retained visual tokens is upper-bounded by the window size, while reasoning tokens grow at a much slower rate due to their compact representation. Consequently, the effective context length remains stable even for long video streams. This property allows ThinkStream to sustain

8

Z. Liu et al.

real-time inference over continuous video input while preserving the semantic information required for long-horizon reasoning.

### 4.2 Streaming-Context RLVR Training

RCSM specifies what state is retained under streaming constraints; the remaining question is how to train the model to produce reasoning traces that are simultaneously useful for solving the current query and informative enough to serve as compressed long-term memory once dense visual tokens are evicted. To this end, we adopt a Streaming Reinforcement Learning with Verifiable Rewards (RLVR) setup tailored to the Watch-Think-Speak loop.

Streaming Rollout with Partial Reasoning. Let the video stream be represented as a sequence of chunks  $ \mathcal{V} = \{v_1, v_2, \ldots\} $ with user instruction  $ \mathcal{I} $. At each step  $ t $, the policy observes the current chunk  $ v_t $ alongside the accumulated streaming history  $ \mathcal{H}_{t-1} $ to produce an output tuple  $ o_t = (r_t, a_t) $.

The streaming history, maintained via the RCSM memory mechanism in Sec. 4.1, is denoted as:

 $$ \mathcal{H}_{t-1}=\{(v_{\tau},r_{\tau},a_{\tau})\}_{\tau=1}^{t-1} $$ 

Since the model only has access to the temporal prefix  $ \mathcal{V}_{\leq t} $ at any given moment, the joint probability of the streaming rollout trajectory factorizes step-by-step as follows:

 $$ \pi_{\theta}(o_{1:T}|\mathcal{V}_{1:T},\mathcal{I})=\prod_{t=1}^{T}\pi_{\theta}(r_{t},a_{t}|\mathcal{H}_{t-1},v_{t},\mathcal{I}) $$ 

RL Optimization. We adopt Group Relative Policy Optimization (GRPO) for model training. We sample $G$ trajectories $\{o_{1:T}^{(1)},\ldots,o_{1:T}^{(G)}\}$ for each streaming instance, and optimize the policy using the standard clipped objective with KL regularization:

 $$ \mathcal{J}(\theta)=\mathbb{E}\left[\frac{1}{G}\sum_{i=1}^{G}\min\left(\rho_{i}(\theta)\hat{A}_{i},\mathrm{c l i p}(\rho_{i}(\theta),1-\epsilon,1+\epsilon)\hat{A}_{i}\right)-\beta D_{K L}(\pi_{\theta}\|\pi_{\mathrm{r e f}})\right]. $$ 

Reward Design. The reward function provides the essential training signal to align the policy with the Watch-Think-Speak loop under stringent streaming constraints. To this end, we formulate a rule-based reward system comprising three integral components: an accuracy reward, a format reward, and a time reward. The accuracy reward ( $ \mathcal{R}_{acc} $) assigns positive credit to responses that successfully match the ground-truth answer. To facilitate reliable automated verification, our RLVR samples are meticulously constructed utilizing deterministic formats, including multiple-choice, binary (Yes/No), and counting queries. Concurrently, the format reward ( $ \mathcal{R}_{format} $) enforces strict adherence to the structured interaction protocol mandated by the loop, yielding a positive

Thinking in Streaming Video

9

value strictly when the generated output conforms to the prescribed structural constraints, and zero otherwise.

Additionally, because streaming interactions necessitate temporally appropriate responses, we introduce a time reward ( $ \mathcal{R}_{time} $). This component quantifies the temporal discrepancy between the model's response step  $ t_{resp} $ and the ground-truth step  $ t_{gt} $. We apply a linear decay within a predefined tolerance window  $ w $, formulated as  $ \mathcal{R}_{time} = \max(0, 1 - |t_{resp} - t_{gt}|/w) $. This mechanism effectively penalizes both premature inferences and excessive latency.

Ultimately, the total reward is computed as the linear summation of these three components:

 $$ \mathcal{R}=\mathcal{R}_{f o r m a t}+\mathcal{R}_{t i m e}+\mathcal{R}_{a c c}. $$ 

Collectively, this composite reward structure rigorously incentivizes the model to generate well-structured reasoning, actuate responses at optimal temporal junctures, and maintain factual fidelity throughout the duration of the streaming interaction.

### 4.3 High-Efficiency Streaming Inference

The online rollout phase of RLVR requires high-throughput streaming inference, where the model repeatedly performs chunk-level decoding while dynamically updating the KV cache. In particular, the RCSM memory mechanism requires pruning state visual tokens during decoding, which demands explicit control over KV cache manipulation.

Existing frameworks are not well suited for this setting. Native transformers implementations allow manual KV cache operations but suffer from significant kernel launch overhead, while optimized engines such as vLLM and SGLang achieve high decoding throughput but provide limited support for customized KV cache updates required by RCSM.

To address this limitation, we design a streaming inference backend based on CUDA Graphs, which is illustrated in Fig. 2(c). The execution pipeline consists of two stages: (1) Prefill Phase: Executed in eager mode to process newly arrived visual tokens and update the KV cache. (2) Decode-and-Prune Phase: Captured as a CUDA graph that performs token decoding together with KV cache pruning in replayable execution graphs. More implementation details can be found in the Appendix.

## 5 ThinkStream Dataset

To train the model for real-time streaming reasoning and interaction, we construct a large-scale, high-quality dataset featuring time-grounded CoT and verifiable question-answering pairs. Our data generation pipeline consists of three sequential stages.

10

Z. Liu et al.

Video Segmentation and Dense Captioning. We employ PySceneDetect to segment continuous videos into coherent temporal scenes. We then utilize Qwen3-VL-235B-A22B-Instruct [1] to densely caption each segment, yielding a sequence of timestamped semantic descriptions that serve as the foundational factual grounding for all subsequent generation phases.

Diverse Instruction Synthesis. We construct highly diverse instruction data by exploring three key scenario dimensions: interaction modes (Real-time Dialogue, Event Trigger, Continuous Output), temporal scopes (Past, Current, Future), and seven fine-grained content semantics (including entity attributes, action semantics, spatial relationships, causal reasoning, procedural states, global scenes, and optical character recognition). By computing the Cartesian product of these dimensions and filtering for practical validity, we derive 39 meaningful scenario combinations. Guided by these filtered combinations, we synthesize diverse question-answering pairs that span multiple formats, specifically open-ended, multiple-choice, binary (Yes/No), and counting questions.

Time-Grounded CoT Generation. Leveraging the timestamped captions and the generated instruction pairs, we simulate the internal reasoning traces to synthesize a dense, continuous, and strictly time-grounded CoT. This ensures that every thought and response is causally constrained to its specific timestamp, effectively acting as an uninterrupted stream of consciousness.

Through this unified pipeline, we ultimately construct 110K Cold Start instances paired with detailed reasoning traces, alongside 9K RLVR instances strictly formatted for verifiable reward optimization. Comprehensive details regarding the video source, dataset distributions and prompt templates are provided in the Appendix.

## 6 Experiments

To evaluate the effectiveness of the proposed ThinkStream framework, we conduct extensive experiments across streaming and offline video benchmarks. We also provide detailed ablation studies and efficiency profiling to validate our architectural designs and the real-time capabilities of our custom streaming inference engine.

Implementation Details. We initialize our framework based on the Qwen2.5-VL-3B [2] model. During the Cold Start phase, we train the model with a batch size of 64 and a learning rate of  $ 1 \times 10^{-5} $. In the subsequent Reinforcement Learning (RL) phase, we employ a batch size of 8, a GRPO group size of 8, and a learning rate of  $ 2 \times 10^{-7} $. The AdamW [20] optimizer is utilized across all training stages. For video processing, frames are sampled at a rate of 2 FPS and encoded using native dynamic resolution. All training experiments are conducted on a single node equipped with 8 NVIDIA H2O GPUs.

Thinking in Streaming Video

11

<div style="text-align: center;">Table 1: Performance comparison of ThinkStream and existing open-source offline and online models on the OVO-Bench streaming video benchmark. ThinkStream-3B achieves a strong average score, significantly surpassing its base model and competing online models.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Model</td><td colspan="6">Real-Time Visual Perception</td><td colspan="4">Backward Tracing</td><td style='text-align: center; word-wrap: break-word;'>Avg.</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>OCR</td><td style='text-align: center; word-wrap: break-word;'>ACR</td><td style='text-align: center; word-wrap: break-word;'>ATR</td><td style='text-align: center; word-wrap: break-word;'>STU</td><td style='text-align: center; word-wrap: break-word;'>FPD</td><td style='text-align: center; word-wrap: break-word;'>OJR</td><td style='text-align: center; word-wrap: break-word;'>Avg.</td><td style='text-align: center; word-wrap: break-word;'>EPM</td><td style='text-align: center; word-wrap: break-word;'>ASI</td><td style='text-align: center; word-wrap: break-word;'>HLD</td><td style='text-align: center; word-wrap: break-word;'>Avg.</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td colspan="12">Open-source Offline Models</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-Video-7B [46]</td><td style='text-align: center; word-wrap: break-word;'>69.13</td><td style='text-align: center; word-wrap: break-word;'>58.72</td><td style='text-align: center; word-wrap: break-word;'>68.83</td><td style='text-align: center; word-wrap: break-word;'>49.44</td><td style='text-align: center; word-wrap: break-word;'>74.26</td><td style='text-align: center; word-wrap: break-word;'>59.78</td><td style='text-align: center; word-wrap: break-word;'>63.52</td><td style='text-align: center; word-wrap: break-word;'>56.23</td><td style='text-align: center; word-wrap: break-word;'>57.43</td><td style='text-align: center; word-wrap: break-word;'>7.53</td><td style='text-align: center; word-wrap: break-word;'>40.4</td><td style='text-align: center; word-wrap: break-word;'>51.96</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2-VL-7B [29]</td><td style='text-align: center; word-wrap: break-word;'>60.4</td><td style='text-align: center; word-wrap: break-word;'>50.46</td><td style='text-align: center; word-wrap: break-word;'>56.03</td><td style='text-align: center; word-wrap: break-word;'>47.19</td><td style='text-align: center; word-wrap: break-word;'>66.34</td><td style='text-align: center; word-wrap: break-word;'>55.43</td><td style='text-align: center; word-wrap: break-word;'>55.98</td><td style='text-align: center; word-wrap: break-word;'>47.81</td><td style='text-align: center; word-wrap: break-word;'>35.48</td><td style='text-align: center; word-wrap: break-word;'>56.08</td><td style='text-align: center; word-wrap: break-word;'>46.46</td><td style='text-align: center; word-wrap: break-word;'>51.22</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LongVU-7B [24]</td><td style='text-align: center; word-wrap: break-word;'>53.69</td><td style='text-align: center; word-wrap: break-word;'>53.21</td><td style='text-align: center; word-wrap: break-word;'>62.93</td><td style='text-align: center; word-wrap: break-word;'>47.75</td><td style='text-align: center; word-wrap: break-word;'>68.32</td><td style='text-align: center; word-wrap: break-word;'>59.78</td><td style='text-align: center; word-wrap: break-word;'>57.61</td><td style='text-align: center; word-wrap: break-word;'>40.74</td><td style='text-align: center; word-wrap: break-word;'>59.46</td><td style='text-align: center; word-wrap: break-word;'>4.84</td><td style='text-align: center; word-wrap: break-word;'>35.01</td><td style='text-align: center; word-wrap: break-word;'>46.31</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-VL-3B [2]</td><td style='text-align: center; word-wrap: break-word;'>76.51</td><td style='text-align: center; word-wrap: break-word;'>44.03</td><td style='text-align: center; word-wrap: break-word;'>67.24</td><td style='text-align: center; word-wrap: break-word;'>42.13</td><td style='text-align: center; word-wrap: break-word;'>68.31</td><td style='text-align: center; word-wrap: break-word;'>61.96</td><td style='text-align: center; word-wrap: break-word;'>60.03</td><td style='text-align: center; word-wrap: break-word;'>50.50</td><td style='text-align: center; word-wrap: break-word;'>53.38</td><td style='text-align: center; word-wrap: break-word;'>22.04</td><td style='text-align: center; word-wrap: break-word;'>41.98</td><td style='text-align: center; word-wrap: break-word;'>51.00</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-VL-7B [2]</td><td style='text-align: center; word-wrap: break-word;'>67.79</td><td style='text-align: center; word-wrap: break-word;'>55.05</td><td style='text-align: center; word-wrap: break-word;'>67.24</td><td style='text-align: center; word-wrap: break-word;'>42.13</td><td style='text-align: center; word-wrap: break-word;'>66.34</td><td style='text-align: center; word-wrap: break-word;'>60.87</td><td style='text-align: center; word-wrap: break-word;'>59.90</td><td style='text-align: center; word-wrap: break-word;'>51.52</td><td style='text-align: center; word-wrap: break-word;'>58.78</td><td style='text-align: center; word-wrap: break-word;'>23.66</td><td style='text-align: center; word-wrap: break-word;'>44.65</td><td style='text-align: center; word-wrap: break-word;'>52.28</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-VL-32B [2]</td><td style='text-align: center; word-wrap: break-word;'>77.18</td><td style='text-align: center; word-wrap: break-word;'>58.72</td><td style='text-align: center; word-wrap: break-word;'>68.10</td><td style='text-align: center; word-wrap: break-word;'>50.56</td><td style='text-align: center; word-wrap: break-word;'>74.26</td><td style='text-align: center; word-wrap: break-word;'>57.61</td><td style='text-align: center; word-wrap: break-word;'>64.40</td><td style='text-align: center; word-wrap: break-word;'>58.59</td><td style='text-align: center; word-wrap: break-word;'>62.84</td><td style='text-align: center; word-wrap: break-word;'>29.57</td><td style='text-align: center; word-wrap: break-word;'>50.33</td><td style='text-align: center; word-wrap: break-word;'>57.37</td></tr><tr><td colspan="12">Open-source Online Models</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Flash-VStream-7B [42]</td><td style='text-align: center; word-wrap: break-word;'>24.16</td><td style='text-align: center; word-wrap: break-word;'>29.36</td><td style='text-align: center; word-wrap: break-word;'>28.45</td><td style='text-align: center; word-wrap: break-word;'>33.71</td><td style='text-align: center; word-wrap: break-word;'>25.74</td><td style='text-align: center; word-wrap: break-word;'>28.8</td><td style='text-align: center; word-wrap: break-word;'>28.37</td><td style='text-align: center; word-wrap: break-word;'>39.06</td><td style='text-align: center; word-wrap: break-word;'>37.16</td><td style='text-align: center; word-wrap: break-word;'>5.91</td><td style='text-align: center; word-wrap: break-word;'>27.38</td><td style='text-align: center; word-wrap: break-word;'>27.88</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLM-online-8B [3]</td><td style='text-align: center; word-wrap: break-word;'>8.05</td><td style='text-align: center; word-wrap: break-word;'>23.85</td><td style='text-align: center; word-wrap: break-word;'>12.07</td><td style='text-align: center; word-wrap: break-word;'>14.04</td><td style='text-align: center; word-wrap: break-word;'>45.54</td><td style='text-align: center; word-wrap: break-word;'>21.2</td><td style='text-align: center; word-wrap: break-word;'>20.79</td><td style='text-align: center; word-wrap: break-word;'>22.22</td><td style='text-align: center; word-wrap: break-word;'>18.8</td><td style='text-align: center; word-wrap: break-word;'>12.18</td><td style='text-align: center; word-wrap: break-word;'>17.73</td><td style='text-align: center; word-wrap: break-word;'>19.26</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Dispider-7B [22]</td><td style='text-align: center; word-wrap: break-word;'>57.72</td><td style='text-align: center; word-wrap: break-word;'>49.54</td><td style='text-align: center; word-wrap: break-word;'>62.07</td><td style='text-align: center; word-wrap: break-word;'>44.94</td><td style='text-align: center; word-wrap: break-word;'>61.39</td><td style='text-align: center; word-wrap: break-word;'>51.63</td><td style='text-align: center; word-wrap: break-word;'>54.55</td><td style='text-align: center; word-wrap: break-word;'>48.48</td><td style='text-align: center; word-wrap: break-word;'>55.41</td><td style='text-align: center; word-wrap: break-word;'>4.3</td><td style='text-align: center; word-wrap: break-word;'>36.06</td><td style='text-align: center; word-wrap: break-word;'>45.31</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>StreamForest-7B [41]</td><td style='text-align: center; word-wrap: break-word;'>68.46</td><td style='text-align: center; word-wrap: break-word;'>53.21</td><td style='text-align: center; word-wrap: break-word;'>71.55</td><td style='text-align: center; word-wrap: break-word;'>47.75</td><td style='text-align: center; word-wrap: break-word;'>65.35</td><td style='text-align: center; word-wrap: break-word;'>60.87</td><td style='text-align: center; word-wrap: break-word;'>61.20</td><td style='text-align: center; word-wrap: break-word;'>58.92</td><td style='text-align: center; word-wrap: break-word;'>64.86</td><td style='text-align: center; word-wrap: break-word;'>32.26</td><td style='text-align: center; word-wrap: break-word;'>52.02</td><td style='text-align: center; word-wrap: break-word;'>56.61</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Stream-3B [34]</td><td style='text-align: center; word-wrap: break-word;'>78.52</td><td style='text-align: center; word-wrap: break-word;'>52.29</td><td style='text-align: center; word-wrap: break-word;'>67.24</td><td style='text-align: center; word-wrap: break-word;'>44.38</td><td style='text-align: center; word-wrap: break-word;'>55.45</td><td style='text-align: center; word-wrap: break-word;'>71.20</td><td style='text-align: center; word-wrap: break-word;'>61.51</td><td style='text-align: center; word-wrap: break-word;'>51.18</td><td style='text-align: center; word-wrap: break-word;'>57.43</td><td style='text-align: center; word-wrap: break-word;'>16.67</td><td style='text-align: center; word-wrap: break-word;'>41.76</td><td style='text-align: center; word-wrap: break-word;'>51.64</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ThinkStream-3B (Ours)</td><td style='text-align: center; word-wrap: break-word;'>85.23</td><td style='text-align: center; word-wrap: break-word;'>64.22</td><td style='text-align: center; word-wrap: break-word;'>69.82</td><td style='text-align: center; word-wrap: break-word;'>49.43</td><td style='text-align: center; word-wrap: break-word;'>69.31</td><td style='text-align: center; word-wrap: break-word;'>64.13</td><td style='text-align: center; word-wrap: break-word;'>67.03</td><td style='text-align: center; word-wrap: break-word;'>53.87</td><td style='text-align: center; word-wrap: break-word;'>59.46</td><td style='text-align: center; word-wrap: break-word;'>43.55</td><td style='text-align: center; word-wrap: break-word;'>52.30</td><td style='text-align: center; word-wrap: break-word;'>59.66</td></tr></table>

### 6.1 Main Results

Streaming Video Benchmarks. We comprehensively evaluate ThinkStream on specialized streaming video benchmarks [18,21]. As shown in Tab. 1 and Tab. 2, our models consistently outperform existing models. Specifically, in Tab. 1, ThinkStream-3B achieves an overall average score of 59.66, significantly surpassing both its base model Qwen2.5-VL-3B (51.00) and competing open-source online models such as Streamo-3B (51.64) on OVO-Bench. Furthermore, on the StreamingBench Real-Time detailed in Tab. 2, ThinkStream-3B attains an average score of 75.00. This not only vastly exceeds other open-source online MLLMs like Dispider-7B (67.63) but also demonstrates highly competitive performance against proprietary models such as GPT-4o (73.28). The results demonstrate that ThinkStream achieves strong performance on streaming video tasks, showing the effectiveness of our Watch-Think-Speak loop.

Offline Video Benchmarks. To ensure the general ability of our streaming-optimized architecture, we also evaluate on standard offline video benchmarks [10, 32]. Despite aggressively evicting visual tokens, ThinkStream-3B achieves highly competitive performance as demonstrated in Tab. 3. Specifically, our model achieves a score of 61.9 on VideoMME and 56.4 on Long VideoBench. With an overall average score of 59.4 across the evaluated metrics, ThinkStream-3B significantly outperforms its base model Qwen2.5-VL-3B (with a 54.4 average). This proves that our ThinkStream effectively preserves understanding capabilities on offline video tasks.

12

Z. Liu et al.

<div style="text-align: center;">Table 2: Performance comparison of various MLLMs on the StreamingBench Real-Time benchmark. ThinkStream-3B demonstrates highly competitive performance against proprietary models such as GPT-4o and vastly exceeds other open-source online MLLMs.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Model</td><td style='text-align: center; word-wrap: break-word;'>OP</td><td style='text-align: center; word-wrap: break-word;'>CR</td><td style='text-align: center; word-wrap: break-word;'>CS</td><td style='text-align: center; word-wrap: break-word;'>ATP</td><td style='text-align: center; word-wrap: break-word;'>EU</td><td style='text-align: center; word-wrap: break-word;'>TR</td><td style='text-align: center; word-wrap: break-word;'>PR</td><td style='text-align: center; word-wrap: break-word;'>SU</td><td style='text-align: center; word-wrap: break-word;'>ACP</td><td style='text-align: center; word-wrap: break-word;'>CT</td><td style='text-align: center; word-wrap: break-word;'>Avg.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Human</td><td style='text-align: center; word-wrap: break-word;'>89.47</td><td style='text-align: center; word-wrap: break-word;'>92.00</td><td style='text-align: center; word-wrap: break-word;'>93.60</td><td style='text-align: center; word-wrap: break-word;'>91.47</td><td style='text-align: center; word-wrap: break-word;'>95.65</td><td style='text-align: center; word-wrap: break-word;'>92.52</td><td style='text-align: center; word-wrap: break-word;'>88.00</td><td style='text-align: center; word-wrap: break-word;'>88.75</td><td style='text-align: center; word-wrap: break-word;'>89.74</td><td style='text-align: center; word-wrap: break-word;'>91.30</td><td style='text-align: center; word-wrap: break-word;'>91.46</td></tr><tr><td colspan="12">Proprietary MLLMs</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Gemini 1.5 pro [11]</td><td style='text-align: center; word-wrap: break-word;'>79.02</td><td style='text-align: center; word-wrap: break-word;'>80.47</td><td style='text-align: center; word-wrap: break-word;'>83.54</td><td style='text-align: center; word-wrap: break-word;'>79.67</td><td style='text-align: center; word-wrap: break-word;'>80.00</td><td style='text-align: center; word-wrap: break-word;'>84.74</td><td style='text-align: center; word-wrap: break-word;'>77.78</td><td style='text-align: center; word-wrap: break-word;'>64.23</td><td style='text-align: center; word-wrap: break-word;'>71.95</td><td style='text-align: center; word-wrap: break-word;'>48.70</td><td style='text-align: center; word-wrap: break-word;'>75.69</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>GPT-4o [13]</td><td style='text-align: center; word-wrap: break-word;'>77.11</td><td style='text-align: center; word-wrap: break-word;'>80.47</td><td style='text-align: center; word-wrap: break-word;'>83.91</td><td style='text-align: center; word-wrap: break-word;'>76.47</td><td style='text-align: center; word-wrap: break-word;'>70.19</td><td style='text-align: center; word-wrap: break-word;'>83.80</td><td style='text-align: center; word-wrap: break-word;'>66.67</td><td style='text-align: center; word-wrap: break-word;'>62.19</td><td style='text-align: center; word-wrap: break-word;'>69.12</td><td style='text-align: center; word-wrap: break-word;'>49.22</td><td style='text-align: center; word-wrap: break-word;'>73.28</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Claude 3.5 Sonnet</td><td style='text-align: center; word-wrap: break-word;'>73.33</td><td style='text-align: center; word-wrap: break-word;'>80.47</td><td style='text-align: center; word-wrap: break-word;'>84.09</td><td style='text-align: center; word-wrap: break-word;'>82.02</td><td style='text-align: center; word-wrap: break-word;'>75.39</td><td style='text-align: center; word-wrap: break-word;'>79.53</td><td style='text-align: center; word-wrap: break-word;'>61.11</td><td style='text-align: center; word-wrap: break-word;'>61.79</td><td style='text-align: center; word-wrap: break-word;'>69.32</td><td style='text-align: center; word-wrap: break-word;'>43.09</td><td style='text-align: center; word-wrap: break-word;'>72.44</td></tr><tr><td colspan="12">Open-source Offline MLLMs</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VILA-1.5-8B [17]</td><td style='text-align: center; word-wrap: break-word;'>53.68</td><td style='text-align: center; word-wrap: break-word;'>49.22</td><td style='text-align: center; word-wrap: break-word;'>70.98</td><td style='text-align: center; word-wrap: break-word;'>56.86</td><td style='text-align: center; word-wrap: break-word;'>53.42</td><td style='text-align: center; word-wrap: break-word;'>53.89</td><td style='text-align: center; word-wrap: break-word;'>54.63</td><td style='text-align: center; word-wrap: break-word;'>48.78</td><td style='text-align: center; word-wrap: break-word;'>50.14</td><td style='text-align: center; word-wrap: break-word;'>17.62</td><td style='text-align: center; word-wrap: break-word;'>52.32</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LongVA-7B [45]</td><td style='text-align: center; word-wrap: break-word;'>70.03</td><td style='text-align: center; word-wrap: break-word;'>63.28</td><td style='text-align: center; word-wrap: break-word;'>61.20</td><td style='text-align: center; word-wrap: break-word;'>70.92</td><td style='text-align: center; word-wrap: break-word;'>62.73</td><td style='text-align: center; word-wrap: break-word;'>59.50</td><td style='text-align: center; word-wrap: break-word;'>61.11</td><td style='text-align: center; word-wrap: break-word;'>53.66</td><td style='text-align: center; word-wrap: break-word;'>54.67</td><td style='text-align: center; word-wrap: break-word;'>34.72</td><td style='text-align: center; word-wrap: break-word;'>59.96</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-NeXT-Video-32B [19]</td><td style='text-align: center; word-wrap: break-word;'>78.20</td><td style='text-align: center; word-wrap: break-word;'>70.31</td><td style='text-align: center; word-wrap: break-word;'>73.82</td><td style='text-align: center; word-wrap: break-word;'>76.80</td><td style='text-align: center; word-wrap: break-word;'>63.35</td><td style='text-align: center; word-wrap: break-word;'>69.78</td><td style='text-align: center; word-wrap: break-word;'>57.41</td><td style='text-align: center; word-wrap: break-word;'>56.10</td><td style='text-align: center; word-wrap: break-word;'>64.31</td><td style='text-align: center; word-wrap: break-word;'>38.86</td><td style='text-align: center; word-wrap: break-word;'>66.96</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-VL-3B [2]</td><td style='text-align: center; word-wrap: break-word;'>67.21</td><td style='text-align: center; word-wrap: break-word;'>68.75</td><td style='text-align: center; word-wrap: break-word;'>75.39</td><td style='text-align: center; word-wrap: break-word;'>79.17</td><td style='text-align: center; word-wrap: break-word;'>72.96</td><td style='text-align: center; word-wrap: break-word;'>72.27</td><td style='text-align: center; word-wrap: break-word;'>71.30</td><td style='text-align: center; word-wrap: break-word;'>61.38</td><td style='text-align: center; word-wrap: break-word;'>71.59</td><td style='text-align: center; word-wrap: break-word;'>26.06</td><td style='text-align: center; word-wrap: break-word;'>67.96</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-VL-7B [2]</td><td style='text-align: center; word-wrap: break-word;'>77.93</td><td style='text-align: center; word-wrap: break-word;'>76.56</td><td style='text-align: center; word-wrap: break-word;'>78.55</td><td style='text-align: center; word-wrap: break-word;'>80.86</td><td style='text-align: center; word-wrap: break-word;'>76.73</td><td style='text-align: center; word-wrap: break-word;'>76.95</td><td style='text-align: center; word-wrap: break-word;'>80.56</td><td style='text-align: center; word-wrap: break-word;'>65.45</td><td style='text-align: center; word-wrap: break-word;'>65.72</td><td style='text-align: center; word-wrap: break-word;'>52.85</td><td style='text-align: center; word-wrap: break-word;'>73.31</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-VL-32B [2]</td><td style='text-align: center; word-wrap: break-word;'>76.29</td><td style='text-align: center; word-wrap: break-word;'>79.69</td><td style='text-align: center; word-wrap: break-word;'>78.55</td><td style='text-align: center; word-wrap: break-word;'>83.50</td><td style='text-align: center; word-wrap: break-word;'>76.10</td><td style='text-align: center; word-wrap: break-word;'>79.44</td><td style='text-align: center; word-wrap: break-word;'>80.56</td><td style='text-align: center; word-wrap: break-word;'>61.38</td><td style='text-align: center; word-wrap: break-word;'>68.27</td><td style='text-align: center; word-wrap: break-word;'>59.07</td><td style='text-align: center; word-wrap: break-word;'>74.27</td></tr><tr><td colspan="12">Open-source Online MLLMs</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Flash-VStream-7B [42]</td><td style='text-align: center; word-wrap: break-word;'>25.89</td><td style='text-align: center; word-wrap: break-word;'>43.57</td><td style='text-align: center; word-wrap: break-word;'>24.91</td><td style='text-align: center; word-wrap: break-word;'>23.87</td><td style='text-align: center; word-wrap: break-word;'>27.33</td><td style='text-align: center; word-wrap: break-word;'>13.08</td><td style='text-align: center; word-wrap: break-word;'>18.52</td><td style='text-align: center; word-wrap: break-word;'>25.20</td><td style='text-align: center; word-wrap: break-word;'>23.87</td><td style='text-align: center; word-wrap: break-word;'>48.70</td><td style='text-align: center; word-wrap: break-word;'>23.23</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLM-online-8B [3]</td><td style='text-align: center; word-wrap: break-word;'>39.07</td><td style='text-align: center; word-wrap: break-word;'>40.06</td><td style='text-align: center; word-wrap: break-word;'>34.49</td><td style='text-align: center; word-wrap: break-word;'>31.05</td><td style='text-align: center; word-wrap: break-word;'>45.96</td><td style='text-align: center; word-wrap: break-word;'>32.40</td><td style='text-align: center; word-wrap: break-word;'>31.48</td><td style='text-align: center; word-wrap: break-word;'>34.16</td><td style='text-align: center; word-wrap: break-word;'>42.49</td><td style='text-align: center; word-wrap: break-word;'>27.89</td><td style='text-align: center; word-wrap: break-word;'>35.99</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Dispider-7B [22]</td><td style='text-align: center; word-wrap: break-word;'>74.92</td><td style='text-align: center; word-wrap: break-word;'>75.53</td><td style='text-align: center; word-wrap: break-word;'>74.10</td><td style='text-align: center; word-wrap: break-word;'>73.08</td><td style='text-align: center; word-wrap: break-word;'>74.44</td><td style='text-align: center; word-wrap: break-word;'>59.92</td><td style='text-align: center; word-wrap: break-word;'>76.14</td><td style='text-align: center; word-wrap: break-word;'>62.91</td><td style='text-align: center; word-wrap: break-word;'>62.16</td><td style='text-align: center; word-wrap: break-word;'>45.80</td><td style='text-align: center; word-wrap: break-word;'>67.63</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ThinkStream-3B (Ours)</td><td style='text-align: center; word-wrap: break-word;'>83.74</td><td style='text-align: center; word-wrap: break-word;'>70.31</td><td style='text-align: center; word-wrap: break-word;'>76.03</td><td style='text-align: center; word-wrap: break-word;'>82.69</td><td style='text-align: center; word-wrap: break-word;'>76.73</td><td style='text-align: center; word-wrap: break-word;'>78.19</td><td style='text-align: center; word-wrap: break-word;'>76.85</td><td style='text-align: center; word-wrap: break-word;'>70.73</td><td style='text-align: center; word-wrap: break-word;'>74.43</td><td style='text-align: center; word-wrap: break-word;'>45.21</td><td style='text-align: center; word-wrap: break-word;'>75.00</td></tr></table>

### 6.2 Ablation Study

Reasoning Token Budget. We ablate the maximum reasoning token budget allocated per second of video. As illustrated in Tab. 4, increasing the reasoning token budget up to 20 tokens per second yields substantial performance improvements, as the model gains sufficient capacity for logical deduction. Specifically, scaling the budget from 0 to 20 tokens significantly improves the OVO-Backward score from 41.8 to 52.3. However, allocating beyond 20 tokens per second results in marginal performance gains (the OVO-Backward score only reaches 52.6 at 30 tokens) while inflating computational overhead and decoding latency, which jumps from 380 ms at 20 tokens to 505 ms at 30 tokens. Thus, 20 tokens per second strikes the optimal balance between reasoning capacity and efficiency.

Video KV Cache Window Size. We investigate the impact of the dense visual token retention window, which is shown in Tab. 5. Setting the window size to 20 seconds achieves the best performance, peaking at 75.0 on StreamingBench Real-Time and 52.3 on OVO-Backward. By contrast, narrower windows such as 5s and 10s result in lower OVO-Backward scores of 46.7 and 50.1, respectively, whereas expanding the window to 30s slightly degrades the OVO-Backward performance to 51.6. This confirms the validity of our assumption that short-term, high-resolution visual context combined with long-term semantic reasoning tokens is sufficient for continuous video understanding.

Thinking in Streaming Video

13

<div style="text-align: center;">Table 3: Model performance comparison on standard offline video benchmarks, including VideoMME and Long VideoBench. Despite aggressively evicting visual tokens, ThinkStream-3B achieves highly competitive performance, demonstrating that it effectively preserves understanding capabilities on offline tasks.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Model</td><td style='text-align: center; word-wrap: break-word;'>OVO Real-Time</td><td style='text-align: center; word-wrap: break-word;'>OVO Backward</td><td style='text-align: center; word-wrap: break-word;'>VideoMME</td><td style='text-align: center; word-wrap: break-word;'>LongVideoBench</td><td style='text-align: center; word-wrap: break-word;'>Avg.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Flash-VStream-7B</td><td style='text-align: center; word-wrap: break-word;'>28.4</td><td style='text-align: center; word-wrap: break-word;'>27.4</td><td style='text-align: center; word-wrap: break-word;'>61.2</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLM-online-8B</td><td style='text-align: center; word-wrap: break-word;'>20.8</td><td style='text-align: center; word-wrap: break-word;'>17.7</td><td style='text-align: center; word-wrap: break-word;'>26.9</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Dispider-7B</td><td style='text-align: center; word-wrap: break-word;'>54.6</td><td style='text-align: center; word-wrap: break-word;'>36.1</td><td style='text-align: center; word-wrap: break-word;'>57.2</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Streamo-3B</td><td style='text-align: center; word-wrap: break-word;'>61.5</td><td style='text-align: center; word-wrap: break-word;'>41.8</td><td style='text-align: center; word-wrap: break-word;'>61.8</td><td style='text-align: center; word-wrap: break-word;'>56.2</td><td style='text-align: center; word-wrap: break-word;'>55.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-VL-3B</td><td style='text-align: center; word-wrap: break-word;'>60.0</td><td style='text-align: center; word-wrap: break-word;'>41.9</td><td style='text-align: center; word-wrap: break-word;'>61.5</td><td style='text-align: center; word-wrap: break-word;'>54.2</td><td style='text-align: center; word-wrap: break-word;'>54.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ThinkStream-3B (Ours)</td><td style='text-align: center; word-wrap: break-word;'>67.0 ( $ \uparrow $7.0)</td><td style='text-align: center; word-wrap: break-word;'>52.3 ( $ \uparrow $10.4)</td><td style='text-align: center; word-wrap: break-word;'>61.9 ( $ \uparrow $0.8)</td><td style='text-align: center; word-wrap: break-word;'>56.4 ( $ \uparrow $1.8)</td><td style='text-align: center; word-wrap: break-word;'>59.4 ( $ \uparrow $5.0)</td></tr></table>

<div style="text-align: center;">Table 4: Ablation on Reasoning Token Budget. Allocating 20 tokens per second strikes the optimal balance between reasoning capacity and efficiency.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>#Token</td><td colspan="3">Streaming. OVO-BW Latency (ms)  $ \downarrow $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0</td><td style='text-align: center; word-wrap: break-word;'>69.6</td><td style='text-align: center; word-wrap: break-word;'>41.8</td><td style='text-align: center; word-wrap: break-word;'>130</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>5</td><td style='text-align: center; word-wrap: break-word;'>70.2</td><td style='text-align: center; word-wrap: break-word;'>46.9</td><td style='text-align: center; word-wrap: break-word;'>193</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>10</td><td style='text-align: center; word-wrap: break-word;'>72.3</td><td style='text-align: center; word-wrap: break-word;'>49.7</td><td style='text-align: center; word-wrap: break-word;'>255</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>20</td><td style='text-align: center; word-wrap: break-word;'>75.0</td><td style='text-align: center; word-wrap: break-word;'>52.3</td><td style='text-align: center; word-wrap: break-word;'>380</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>30</td><td style='text-align: center; word-wrap: break-word;'>75.0</td><td style='text-align: center; word-wrap: break-word;'>52.6</td><td style='text-align: center; word-wrap: break-word;'>505</td></tr></table>

<div style="text-align: center;">Table 5: Ablation on Visual KV Cache Window Size. Setting the window size to 20 seconds achieves the best trade-off between accuracy and efficiency.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Window</td><td colspan="3">Streaming. OVO-RT OVO-BW</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>5s</td><td style='text-align: center; word-wrap: break-word;'>73.9</td><td style='text-align: center; word-wrap: break-word;'>65.2</td><td style='text-align: center; word-wrap: break-word;'>46.7</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>10s</td><td style='text-align: center; word-wrap: break-word;'>74.5</td><td style='text-align: center; word-wrap: break-word;'>66.3</td><td style='text-align: center; word-wrap: break-word;'>50.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>20s</td><td style='text-align: center; word-wrap: break-word;'>75.0</td><td style='text-align: center; word-wrap: break-word;'>67.0</td><td style='text-align: center; word-wrap: break-word;'>52.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>30s</td><td style='text-align: center; word-wrap: break-word;'>74.9</td><td style='text-align: center; word-wrap: break-word;'>66.8</td><td style='text-align: center; word-wrap: break-word;'>51.6</td></tr></table>

Stream Memory Representation and RLVR Optimization. To validate the necessity of our RLVR pipeline and the specific memory representation, we compare several variants: (1) no memory, (2) discrete caption tokens as memory, (3) Cold-start CoT memory, and (4) our RLVR-optimized CoT memory. As is shown in Tab. 6, initializing the model with constructed cold-start CoT data yields a significant gain, improving the average score from 56.9 (no memory) to 60.5. Interestingly, utilizing discrete caption tokens actually diminishes the overall capability, dropping the average score to 48.7. Finally, ost-training the model with RLVR further boosts average performance by 4.3 points (reaching 64.8), demonstrating that reasoning tokens learn to act as a far superior, highly compressed long-term memory compared to naive discrete captions.

### 6.3 Efficiency and Real-Time Analysis

A core contribution of our work is ensuring that the Streaming Watch-Think-Speak paradigm strictly adheres to real-time constraints. We profile our CUDA Graph-based Streaming Inference Engine against standard eager transformers implementations.

As shown in Fig. 3, our custom engine achieves a massive speedup in token decoding across various batch sizes compared to the Qwen2.5-VL-3B model. For instance, at a batch size of 1, our engine delivers 154.07 tokens/s compared to the baseline's 30.06 tokens/s, representing a more than  $ 5\times $ speedup. Furthermore,

14

Z. Liu et al.

<div style="text-align: center;">Table 6: Ablation on Stream Memory Representation and RLVR Optimization. Posttraining with RLVR demonstrates that reasoning tokens act as a highly compressed long-term memory representation.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Memory Variant</td><td style='text-align: center; word-wrap: break-word;'>Streaming. OVO-BW</td><td style='text-align: center; word-wrap: break-word;'>OVO-RT</td><td style='text-align: center; word-wrap: break-word;'>Avg.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-VL-3B</td><td style='text-align: center; word-wrap: break-word;'>68.9</td><td style='text-align: center; word-wrap: break-word;'>41.9</td><td style='text-align: center; word-wrap: break-word;'>60.0</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Discrete caption as memory</td><td style='text-align: center; word-wrap: break-word;'>59.0</td><td style='text-align: center; word-wrap: break-word;'>36.9</td><td style='text-align: center; word-wrap: break-word;'>50.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>No memory</td><td style='text-align: center; word-wrap: break-word;'>69.6</td><td style='text-align: center; word-wrap: break-word;'>41.8</td><td style='text-align: center; word-wrap: break-word;'>59.2</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Cold-start CoT memory</td><td style='text-align: center; word-wrap: break-word;'>70.6</td><td style='text-align: center; word-wrap: break-word;'>47.6</td><td style='text-align: center; word-wrap: break-word;'>63.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>RLVR-optimized CoT memory</td><td style='text-align: center; word-wrap: break-word;'>75.0</td><td style='text-align: center; word-wrap: break-word;'>52.3</td><td style='text-align: center; word-wrap: break-word;'>67.0</td></tr></table>

<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Batch Size</th><th style='text-align: center;'>Qwen2.5-VL-3B</th><th style='text-align: center;'>ThinkStream-3B</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>Batch Size = 1</td><td style='text-align: center;'>30.06</td><td style='text-align: center;'>154.07</td></tr>
    <tr><td style='text-align: center;'>Batch Size = 4</td><td style='text-align: center;'>135.43</td><td style='text-align: center;'>486.69</td></tr>
    <tr><td style='text-align: center;'>Batch Size = 8</td><td style='text-align: center;'>276.10</td><td style='text-align: center;'>766.87</td></tr>
  </tbody>
</table>

<div style="text-align: center;">Fig. 3: Token decoding speed comparison across different batch sizes. The custom CUDA Graph-based streaming inference engine achieves a massive speedup compared to the standard Qwen2.5-VL-3B baseline, maintaining high throughput while preserving flexible KV cache control.</div>


<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Video Context Length (s)</th><th style='text-align: center;'>Qwen2.5-VL-3B (Token Completion Latency (s))</th><th style='text-align: center;'>ThinkStream-3B (Token Completion Latency (s))</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>0</td><td style='text-align: center;'>1.06</td><td style='text-align: center;'>0.34</td></tr>
    <tr><td style='text-align: center;'>25</td><td style='text-align: center;'>1.02</td><td style='text-align: center;'>0.35</td></tr>
    <tr><td style='text-align: center;'>50</td><td style='text-align: center;'>1.06</td><td style='text-align: center;'>0.38</td></tr>
    <tr><td style='text-align: center;'>75</td><td style='text-align: center;'>1.10</td><td style='text-align: center;'>0.39</td></tr>
    <tr><td style='text-align: center;'>100</td><td style='text-align: center;'>1.00</td><td style='text-align: center;'>0.36</td></tr>
    <tr><td style='text-align: center;'>125</td><td style='text-align: center;'>1.12</td><td style='text-align: center;'>0.38</td></tr>
    <tr><td style='text-align: center;'>150</td><td style='text-align: center;'>1.18</td><td style='text-align: center;'>0.39</td></tr>
    <tr><td style='text-align: center;'>175</td><td style='text-align: center;'>1.24</td><td style='text-align: center;'>0.38</td></tr>
    <tr><td style='text-align: center;'>200</td><td style='text-align: center;'>1.23</td><td style='text-align: center;'>0.39</td></tr>
    <tr><td style='text-align: center;'>225</td><td style='text-align: center;'>1.38</td><td style='text-align: center;'>0.39</td></tr>
  </tbody>
</table>

<div style="text-align: center;">Fig. 4: Real-time latency scaling with processed video length. ThinkStream successfully bounds the end-to-end inference latency below the 0.5s real-time threshold (required for 2 FPS inputs) as the video context grows, whereas the baseline model scales poorly and consistently violates the threshold.</div>


at a batch size of 8, our decoding speed scales efficiently to 766.87 tokens/s, significantly outperforming the baseline's 276.10 tokens/s. This confirms that our custom backend maintains high throughput while preserving the flexible, manual KV cache control required for our eviction strategy.

Crucially, as illustrated in Fig. 4, our framework successfully bounds latency as the processed video length increases. While the baseline model's latency scales poorly and consistently violates the real-time threshold—fluctuating between 1.0s and 1.4s per second of video—our combination of algorithmic KV cache eviction and engineering optimizations ensures that the end-to-end inference latency remains flat. It consistently stays below the 0.5s real-time threshold required for 2 FPS inputs. The total processing delay remains bounded, proving that our approach can be deployed efficiently in streaming video environments.

Thinking in Streaming Video

15

## 7 Conclusion

We study streaming video reasoning, where models must continuously interpret incoming observations under strict latency and memory constraints. We introduce the Watch-Think-Speak paradigm and propose ThinkStream, a framework that enables incremental reasoning over long video streams. Through Reasoning-Compressed Streaming Memory (RCSM) and streaming reinforcement learning with verifiable rewards, our approach maintains bounded memory usage while preserving coherent long-horizon understanding. Experiments show that ThinkStream achieves strong performance on streaming video benchmarks with low latency while retaining competitive capability on standard offline video tasks.

## References

1. Bai, S., Cai, Y., Chen, R., Chen, K., Chen, X., Cheng, Z., Deng, L., Ding, W., Gao, C., Ge, C., et al.: Qwen3-vl technical report. arXiv preprint arXiv:2511.21631 (2025)

2. Bai, S., Chen, K., Liu, X., Wang, J., Ge, W., Song, S., Dang, K., Wang, P., Wang, S., Tang, J., Zhong, H., Zhu, Y., Yang, M., Li, Z., Wan, J., Wang, P., Ding, W., Fu, Z., Xu, Y., Ye, J., Zhang, X., Xie, T., Cheng, Z., Zhang, H., Yang, Z., Xu, H., Lin, J.: Qwen2.5-vl technical report. arXiv preprint arXiv:2502.13923 (2025)

3. Chen, J., Lv, Z., Wu, S., Lin, K.Q., Song, C., Gao, D., Liu, J.W., Gao, Z., Mao, D., Shou, M.Z.: Video-LLM-online: Online video-large language model for streaming video. In: Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition. pp. 18407–18418 (2024)

4. Chen, Y., Bai, X., Wang, Z., Bai, C., Dai, Y., Lu, M., Zhang, S.: Streamkv: Streaming video question-answering with segment-based kv cache retrieval and compression. arXiv preprint arXiv:2511.07278 (2025)

5. Chen, Y., Huang, W., Shi, B., Hu, Q., Ye, H., Zhu, L., Liu, Z., Molchanov, P., Kautz, J., QI, X., et al.: Scaling rl to long videos. In: The Thirty-ninth Annual Conference on Neural Information Processing Systems

6. Dao, T.: Flashattention-2: Faster attention with better parallelism and work partitioning. arXiv preprint arXiv:2307.08691 (2023)

7. Ding, X., Wu, H., Yang, Y., Jiang, S., Zhang, Q., Bai, D., Chen, Z., Cao, T.: Streammind: Unlocking full frame rate streaming video dialogue through event-gated cognition. In: Proceedings of the IEEE/CVF International Conference on Computer Vision. pp. 13448–13459 (2025)

8. Dong, J., Feng, B., Guessous, D., Liang, Y., He, H.: Flex attention: A programming model for generating optimized attention kernels. arXiv preprint arXiv:2412.054962(3), 4 (2024)

9. Feng, K., Gong, K., Li, B., Guo, Z., Wang, Y., Peng, T., Wu, J., Zhang, X., Wang, B., Yue, X.: Video-r1: Reinforcing video reasoning in mlms. arXiv preprint arXiv:2503.21776 (2025)

10. Fu, C., Dai, Y., Luo, Y., Li, L., Ren, S., Zhang, R., Wang, Z., Zhou, C., Shen, Y., Zhang, M., et al.: Video-mme: The first-ever comprehensive evaluation benchmark of multi-modal llms in video analysis. In: Proceedings of the IEEE/CVF conference on computer vision and pattern recognition. pp. 24108–24118 (2025)

11. Gemini, G.T.: 1.5: unlocking multimodal understanding across millions of tokens of context. arXiv preprint arXiv:2403.05530 (2024)

16

Z. Liu et al.

12. Hsu, P.L., Dai, Y., Kothapalli, V., Song, Q., Tang, S., Zhu, S., Shimizu, S., Sahni, S., Ning, H., Chen, Y.: Liger kernel: Efficient triton kernels for llm training. arXiv preprint arXiv:2410.10989 (2024)

13. Hurst, A., Lerer, A., Goucher, A.P., Perelman, A., Ramesh, A., Clark, A., Ostrow, A., Welihinda, A., Hayes, A., Radford, A., et al.: Gpt-4o system card. arXiv preprint arXiv:2410.21276 (2024)

14. Kim, J., Kim, M.S., Chung, J., Cho, J., Kim, J., Kim, S., Sim, G., Yu, Y.: Egospeak: learning when to speak for egocentric conversational agents in the wild. In: Findings of the Association for Computational Linguistics: NAACL 2025. pp. 2990–3005 (2025)

15. Li, H., Zhang, Y., Guo, L., Yue, X., Liu, J.: Breaking the encoder barrier for seamless video-language understanding. In: Proceedings of the IEEE/CVF International Conference on Computer Vision. pp. 23167–23176 (2025)

16. Li, W., Hu, B., Shao, R., Shen, L., Nie, L.: Lion-fs: Fast & slow video-language thinker as online video assistant. In: Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition. pp. 3240–3251 (2025)

17. Lin, J., Yin, H., Ping, W., Molchanov, P., Shoeybi, M., Han, S.: Vila: On pretraining for visual language models. In: Proceedings of the IEEE/CVF conference on computer vision and pattern recognition. pp. 26689–26699 (2024)

18. Lin, J., Fang, Z., Chen, C., Wan, Z., Luo, F., Li, P., Liu, Y., Sun, M.: Streamingbench: Assessing the gap for mlims to achieve streaming video understanding. arXiv preprint arXiv:2411.03628 (2024)

19. Liu, H., Li, C., Li, Y., Li, B., Zhang, Y., Shen, S., Lee, Y.J.: Llavanext: Improved reasoning, ocr, and world knowledge (2024)

20. Loshchilov, I., Hutter, F.: Decoupled weight decay regularization. arXiv preprint arXiv:1711.05101 (2017)

21. Niu, J., Li, Y., Miao, Z., Ge, C., Zhou, Y., He, Q., Dong, X., Duan, H., Ding, S., Qian, R., et al.: Ovo-bench: How far is your video-llms from real-world online video understanding? In: Proceedings of the Computer Vision and Pattern Recognition Conference. pp. 18902–18913 (2025)

22. Qian, R., Ding, S., Dong, X., Zhang, P., Zang, Y., Cao, Y., Lin, D., Wang, J.: Dispider: Enabling video llms with active real-time interaction via disentangled perception, decision, and reaction. In: Proceedings of the Computer Vision and Pattern Recognition Conference. pp. 24045–24055 (2025)

23. Qian, R., Dong, X., Zhang, P., Zang, Y., Ding, S., Lin, D., Wang, J.: Streaming long video understanding with large language models. Advances in Neural Information Processing Systems 37, 119336–119360 (2024)

24. Shen, X., Xiong, Y., Zhao, C., Wu, L., Chen, J., Zhu, C., Liu, Z., Xiao, F., Varadarajan, B., Bordes, F., et al.: Longvu: Spatiotemporal adaptive compression for long video-language understanding. arXiv preprint arXiv:2410.17434 (2024)

25. Tang, C., Han, Z., Sun, H., Zhou, S., Zhang, X., Wei, X., Yuan, Y., Xu, J., Sun, H.: Tspo: Temporal sampling policy optimization for long-form video language understanding. arXiv preprint arXiv:2508.04369 (2025)

26. Tian, S., Wang, R., Guo, H., Wu, P., Dong, Y., Wang, X., Yang, J., Zhang, H., Zhu, H., Liu, Z.: Ego-r1: Chain-of-tool-thought for ultra-long egocentric video reasoning. arXiv preprint arXiv:2506.13654 (2025)

27. Tong, J., Fan, Y., Zhao, A., Ma, Y., Shen, X.: Streaming thinker: Large language models can think while reading. arXiv preprint arXiv:2510.17238 (2025)

28. Wang, H., Feng, B., Lai, Z., Xu, M., Li, S., Ge, W., Dehghan, A., Cao, M., Huang, P.: Streambridge: Turning your offline video large language model into a proactive streaming assistant. arXiv preprint arXiv:2505.05467 (2025)

Thinking in Streaming Video

17

29. Wang, P., Bai, S., Tan, S., Wang, S., Fan, Z., Bai, J., Chen, K., Liu, X., Wang, J., Ge, W., et al.: Qwen2-vl: Enhancing vision-language model's perception of the world at any resolution. arXiv preprint arXiv:2409.12191 (2024)

30. Wang, S., Jin, J., Wang, X., Song, L., Fu, R., Wang, H., Ge, Z., Lu, Y., Cheng, X.: Video-thinker: Sparking" thinking with videos" via reinforcement learning. arXiv preprint arXiv:2510.23473 (2025)

31. Wang, Z., Yoon, J., Yu, S., Islam, M.M., Bertasius, G., Bansal, M.: Video-rts: Rethinking reinforcement learning and test-time scaling for efficient and enhanced video reasoning. In: Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing. pp. 28114–28128 (2025)

32. Wu, H., Li, D., Chen, B., Li, J.: Longvideobench: A benchmark for long-context interleaved video-language understanding. Advances in Neural Information Processing Systems 37, 28828–28857 (2024)

33. Wu, T., Yang, L., Zhan, G., Zhang, Y., Liao, Y., Li, J., Fu, D., Zhang, L., Wang, L.: Tempr1: Improving temporal understanding of mlims via temporal-aware multi-task reinforcement learning. arXiv preprint arXiv:2512.03963 (2025)

34. Xia, J., Chen, P., Zhang, M., Sun, X., Zhou, K.: Streaming video instruction tuning. arXiv preprint arXiv:2512.21334 (2025)

35. Xu, R., Xiao, G., Chen, Y., He, L., Peng, K., Lu, Y., Han, S.: Streaming vlm: Real-time understanding for infinite video streams. arXiv preprint arXiv:2510.09608 (2025)

36. Yang, A., Li, A., Yang, B., Zhang, B., Hui, B., Zheng, B., Yu, B., Gao, C., Huang, C., Lv, C., et al.: Qwen3 technical report. arXiv preprint arXiv:2505.09388 (2025)

37. Yang, A., Yang, B., Zhang, B., Hui, B., Zheng, B., Yu, B., Li, C., Liu, D., Huang, F., Wei, H., Lin, H., Yang, J., Tu, J., Zhang, J., Yang, J., Yang, J., Zhou, J., Lin, J., Dang, K., Lu, K., Bao, K., Yang, K., Yu, L., Li, M., Xue, M., Zhang, P., Zhu, Q., Men, R., Lin, R., Li, T., Xia, T., Ren, X., Ren, X., Fan, Y., Su, Y., Zhang, Y., Wan, Y., Liu, Y., Cui, Z., Zhang, Z., Qiu, Z.: Qwen2.5 technical report. arXiv preprint arXiv:2412.15115 (2024)

38. Yang, Y., Zhao, Z., Shukla, S.N., Singh, A., Mishra, S.K., Zhang, L., Ren, M.: Streammem: Query-agnostic kv cache memory for streaming video understanding. arXiv preprint arXiv:2508.15717 (2025)

39. Ye, Z., Chen, L., Lai, R., Lin, W., Zhang, Y., Wang, S., Chen, T., Kasikci, B., Grover, V., Krishnamurthy, A., et al.: Flashinfer: Efficient and customizable attention engine for llm inference serving. Proceedings of Machine Learning and Systems 7 (2025)

40. Yuan, L., Wang, J., Sun, H., Zhang, Y., Lin, Y.: Tarsier2: Advancing large vision-language models from detailed video description to comprehensive video understanding. arXiv preprint arXiv:2501.07888 (2025)

41. Zeng, X., Qiu, K., Zhang, Q., Li, X., Wang, J., Li, J., Yan, Z., Tian, K., Tian, M., Zhao, X., et al.: Streamforest: Efficient online video understanding with persistent event memory. arXiv preprint arXiv:2509.24871 (2025)

42. Zhang, H., Wang, Y., Tang, Y., Liu, Y., Feng, J., Jin, X.: Flash-vstream: Efficient real-time understanding for long video streams. In: Proceedings of the IEEE/CVF international conference on computer vision. pp. 21059–21069 (2025)

43. Zhang, H., Yang, S., Fu, J., Ng, S.K., Qiu, X.: Hermes: Kv cache as hierarchical memory for efficient streaming video understanding. arXiv preprint arXiv:2601.14724 (2026)

44. Zhang, J., Zhu, Y., Sun, M., Luo, Y., Qiao, S., Du, L., Zheng, D., Chen, H., Zhang, N.: Lightthinker: Thinking step-by-step compression. In: Proceedings of

18

Z. Liu et al.

the 2025 Conference on Empirical Methods in Natural Language Processing. pp. 13318–13339 (2025)

45. Zhang, P., Zhang, K., Li, B., Zeng, G., Yang, J., Zhang, Y., Wang, Z., Tan, H., Li, C., Liu, Z.: Long context transfer from language to vision. arXiv preprint arXiv:2406.16852 (2024)

46. Zhang, Y., Wu, J., Li, W., Li, B., Ma, Z., Liu, Z., Li, C.: Llava-video: Video instruction tuning with synthetic data. arXiv preprint arXiv:2410.02713 (2024)

47. Zhao, Z., Wang, K., Li, S., Qian, R., Lin, W., Liu, H.: Cogstream: Context-guided streaming video question answering. arXiv preprint arXiv:2506.10516 (2025)

Thinking in Streaming Video

19

### A More Implementation Details

### A.1 Streaming Inference

As illustrated in Algorithm 1, recording both decoding and pruning operations into static CUDA graphs eliminates per-step kernel launch overhead while preserving explicit control over KV cache manipulation. This design enables flexible KV cache updates required by RCSM while achieving decoding throughput comparable to optimized inference engines, making it suitable for high-throughput RL rollouts and real-time streaming deployment.

Algorithm 1 Streaming Inference with CUDA Graph KV Cache Eviction

Require: Video stream V, Instruction I, Window size W, Max new tokens N
1: Initialize KV\_Cache  $ \leftarrow $  $ \emptyset $, Active\_Chunks  $ \leftarrow $ 0
2: Graph capture DECODEKERNEL and EVICTKERNEL
3: for each video chunk  $ v_t \in V $ do
4:     if Active\_Chunks  $ \geq $ W then
5:         {In-place memory shift via captured CUDA Graph}
6:         REPLAYGRAPH(EVICTKERNEL, target\_starts, source\_ends)
7:         Active\_Chunks  $ \leftarrow $ Active\_Chunks - 1
8:     end if
9:     {Eager execution for variable-length visual tokens}
10:    logits, KV\_Cache  $ \leftarrow $ PREFILL(KV\_Cache, v_t, I)
11:    for step = 1 to N do
12:        {Zero-overhead decode via captured CUDA Graph}
13:        logits, KV\_Cache  $ \leftarrow $ REPLAYGRAPH(DECODEKERNEL, token_{step-1})
14:        {Accelerated sampling via FlashInfer}
15:        token_{step} \leftarrow SAMPLE(logits)
16:    if token_{step} \in \{(\lim\_end\})\} then
17:        break
18:    end if
19: end for
20: Active\_Chunks  $ \leftarrow $ Active\_Chunks + 1
21: end for

To further optimize memory access and compute efficiency, our attention mechanism employs a static KV cache and integrates the flash attn with kvcache interface [6]. Additionally, during the autoregressive generation phase, we leverage top_k_top_p_sampling_from_logits operator in FlashInfer [39] to accelerate the sampling process, thereby significantly minimizing the latency of token selection.

### A.2 Training

we utilize FlexAttention [8] to implement RCSM during the training phase. This allows us to flexibly define and customize the attention masks without incurring prohibitive computational overhead. Furthermore, we incorporate the Liger

20

Z. Liu et al.

Kernel [12] to accelerate the training process and reduce peak GPU memory consumption, enabling more efficient training over extended video sequences.

### B Dataset Information

Video Sources. To construct our highly diverse dataset, we sampled high-quality video subsets from the widely used LLaVA-Video-178K [46] and Tarsier2-Recap-585K [40] datasets. These subsets provide a rich foundation of dynamic visual content, ensuring robust training for streaming video understanding.

Diverse Instruction Synthesis Details. As introduced in the main text, we synthesize instruction data by computing the Cartesian product of three key scenario dimensions to derive 39 meaningful combinations. The specific definitions and scope of these dimensions are detailed below:

– Interaction Modes: This dimension defines the fundamental mechanism of how the user queries the streaming assistant.

- Real-time Dialogue: The user asks real-time or retrospective questions where the question and answer share the exact same timestamp. Formats include open-ended, multiple choice, binary, and counting questions.

- Event Trigger: The user sets a monitoring or predictive rule significantly in advance. The assistant must remain silent for a long duration until a specific event occurs or a prediction condition is met, at which point it triggers an alert.

- Continuous Output: The user requests a continuous stream of updates. The assistant generates multiple consecutive messages to dynamically describe ongoing changes, actions, or events as they unfold over time.

– Temporal Scopes: This dimension specifies the time frame the instruction targets relative to the current timestamp.

Past: Retrospective queries requiring the assistant to recall details about events that occurred in the distant past, relying heavily on long-term memory retrieval.

- Current: Real-time queries focusing on the immediate present context regarding elements currently visible in the video stream.

Future: Predictive queries asking for future forecasts or guidance on next steps concerning what is likely to happen based on current visual evidence.

– Content Semantics: We comprehensively cover seven fine-grained visual and logical dimensions to ensure thorough video understanding:

- Entity & Attribute Perception: Recognizing objects and their detailed visual attributes (e.g., color, shape, type).

- Action & Activity Semantics: Identifying specific actions, behaviors, or ongoing activities.

- Spatial & Geometric Relationships: Understanding spatial positions, distances, or geometric arrangements of objects.

Thinking in Streaming Video

21

- Causal & Logical Reasoning: Deducing the underlying causes, reasons, or logical implications of observed events.

• Procedural State & Evolution: Tracking the progress, steps, or current state of a structured procedure.

- Global Scene & Context: Recognizing the overall environment, location type, weather, or scene atmosphere.

- Optical Character Recognition (OCR): Extracting text content, signage, or characters visible on the screen.

Dataset Statistics and Analysis. Fig. 5 illustrates the statistical distribution of our constructed ThinkStream dataset. As shown in the figure, our dataset exhibits a rich diversity across hierarchical compositions—encompassing various interaction modes, temporal scopes, and fine-grained content semantics—as well as a robust distribution of thinking token lengths. This comprehensive variety ensures that the model is exposed to a wide range of streaming video understanding scenarios during training.

<div style="text-align: center;"><img src="imgs/img_in_image_box_276_662_559_942.jpg" alt="Image" width="23%" />

Event Trigger
Event
Control Output
Perception
Action
State
State
Perception
Action
State
Perception
State
State
Perception
Action
State
Perception
Action
State
State
Perception
Action
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Perception
Action
State
State
Per

</div>


<div style="text-align: center;">(a) Data Distribution</div>


<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Thinking Token Count Ranges</th><th style='text-align: center;'>Frequency</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>0-100</td><td style='text-align: center;'>1148</td></tr>
    <tr><td style='text-align: center;'>100-200</td><td style='text-align: center;'>33419</td></tr>
    <tr><td style='text-align: center;'>200-300</td><td style='text-align: center;'>46536</td></tr>
    <tr><td style='text-align: center;'>300-500</td><td style='text-align: center;'>22649</td></tr>
    <tr><td style='text-align: center;'>500+</td><td style='text-align: center;'>7122</td></tr>
  </tbody>
</table>

<div style="text-align: center;">(b) Thinking Token Length</div>


<div style="text-align: center;">Fig.5: Statistics of our ThinkStream Dataset. We show (a) the hierarchical composition of data and (b) the distribution of thinking process lengths.</div>


### C More Results

To further demonstrate the scalability and effectiveness of our proposed approach, we trained our model based on the Qwen2.5-VL-7B [2] architecture, denoted as ThinkStream-7B. As shown in Tab. 7, ThinkStream-7B achieves significant performance improvements over the base Qwen2.5-VL-7B model across multiple dimensions on the OVO-Bench streaming video benchmark.

Specifically, in the OCR evaluation, ThinkStream-7B attains an impressive score of 87.92, outperforming the base model's 67.79 by over 20 points. In terms

22

Z. Liu et al.

of Real-Time Visual Perception, our model improves the average score from 59.90 to 69.12. Furthermore, ThinkStream-7B demonstrates enhanced capability in long-term memory retrieval, boosting the average score of Backward Tracing from 52.28 to 60.68. These substantial gains indicate that integrating our streaming framework into stronger base models yields consistent and robust enhancements for streaming video understanding.

<div style="text-align: center;">Table 7: Performance comparison of ThinkStream and existing open-source offline and online models on the OVO-Bench streaming video benchmark.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Model</td><td colspan="6">Real-Time Visual Perception</td><td colspan="4">Backward Tracing</td><td style='text-align: center; word-wrap: break-word;'>Avg.</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>OCR</td><td style='text-align: center; word-wrap: break-word;'>ACR</td><td style='text-align: center; word-wrap: break-word;'>ATR</td><td style='text-align: center; word-wrap: break-word;'>STU</td><td style='text-align: center; word-wrap: break-word;'>FPD</td><td style='text-align: center; word-wrap: break-word;'>OJR</td><td style='text-align: center; word-wrap: break-word;'>Avg.</td><td style='text-align: center; word-wrap: break-word;'>EPM</td><td style='text-align: center; word-wrap: break-word;'>ASI</td><td style='text-align: center; word-wrap: break-word;'>HLD</td><td style='text-align: center; word-wrap: break-word;'>Avg.</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td colspan="12">Open-source Offline Models</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LLaVA-Video-7B [46]</td><td style='text-align: center; word-wrap: break-word;'>69.13</td><td style='text-align: center; word-wrap: break-word;'>58.72</td><td style='text-align: center; word-wrap: break-word;'>68.83</td><td style='text-align: center; word-wrap: break-word;'>49.44</td><td style='text-align: center; word-wrap: break-word;'>74.26</td><td style='text-align: center; word-wrap: break-word;'>59.78</td><td style='text-align: center; word-wrap: break-word;'>63.52</td><td style='text-align: center; word-wrap: break-word;'>56.23</td><td style='text-align: center; word-wrap: break-word;'>57.43</td><td style='text-align: center; word-wrap: break-word;'>7.53</td><td style='text-align: center; word-wrap: break-word;'>40.4</td><td style='text-align: center; word-wrap: break-word;'>51.96</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2-VL-7B [29]</td><td style='text-align: center; word-wrap: break-word;'>60.4</td><td style='text-align: center; word-wrap: break-word;'>50.46</td><td style='text-align: center; word-wrap: break-word;'>56.03</td><td style='text-align: center; word-wrap: break-word;'>47.19</td><td style='text-align: center; word-wrap: break-word;'>66.34</td><td style='text-align: center; word-wrap: break-word;'>55.43</td><td style='text-align: center; word-wrap: break-word;'>55.98</td><td style='text-align: center; word-wrap: break-word;'>47.81</td><td style='text-align: center; word-wrap: break-word;'>35.48</td><td style='text-align: center; word-wrap: break-word;'>56.08</td><td style='text-align: center; word-wrap: break-word;'>46.46</td><td style='text-align: center; word-wrap: break-word;'>51.22</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LongVU-7B [24]</td><td style='text-align: center; word-wrap: break-word;'>53.69</td><td style='text-align: center; word-wrap: break-word;'>53.21</td><td style='text-align: center; word-wrap: break-word;'>62.93</td><td style='text-align: center; word-wrap: break-word;'>47.75</td><td style='text-align: center; word-wrap: break-word;'>68.32</td><td style='text-align: center; word-wrap: break-word;'>59.78</td><td style='text-align: center; word-wrap: break-word;'>57.61</td><td style='text-align: center; word-wrap: break-word;'>40.74</td><td style='text-align: center; word-wrap: break-word;'>59.46</td><td style='text-align: center; word-wrap: break-word;'>4.84</td><td style='text-align: center; word-wrap: break-word;'>35.01</td><td style='text-align: center; word-wrap: break-word;'>46.31</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-VL-3B [2]</td><td style='text-align: center; word-wrap: break-word;'>76.51</td><td style='text-align: center; word-wrap: break-word;'>44.03</td><td style='text-align: center; word-wrap: break-word;'>67.24</td><td style='text-align: center; word-wrap: break-word;'>42.13</td><td style='text-align: center; word-wrap: break-word;'>68.31</td><td style='text-align: center; word-wrap: break-word;'>61.96</td><td style='text-align: center; word-wrap: break-word;'>60.03</td><td style='text-align: center; word-wrap: break-word;'>50.50</td><td style='text-align: center; word-wrap: break-word;'>53.38</td><td style='text-align: center; word-wrap: break-word;'>22.04</td><td style='text-align: center; word-wrap: break-word;'>41.98</td><td style='text-align: center; word-wrap: break-word;'>51.00</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-VL-7B [2]</td><td style='text-align: center; word-wrap: break-word;'>67.79</td><td style='text-align: center; word-wrap: break-word;'>55.05</td><td style='text-align: center; word-wrap: break-word;'>67.24</td><td style='text-align: center; word-wrap: break-word;'>42.13</td><td style='text-align: center; word-wrap: break-word;'>66.34</td><td style='text-align: center; word-wrap: break-word;'>60.87</td><td style='text-align: center; word-wrap: break-word;'>59.90</td><td style='text-align: center; word-wrap: break-word;'>51.52</td><td style='text-align: center; word-wrap: break-word;'>58.78</td><td style='text-align: center; word-wrap: break-word;'>23.66</td><td style='text-align: center; word-wrap: break-word;'>44.65</td><td style='text-align: center; word-wrap: break-word;'>52.28</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-VL-32B [2]</td><td style='text-align: center; word-wrap: break-word;'>77.18</td><td style='text-align: center; word-wrap: break-word;'>58.72</td><td style='text-align: center; word-wrap: break-word;'>68.10</td><td style='text-align: center; word-wrap: break-word;'>50.56</td><td style='text-align: center; word-wrap: break-word;'>74.26</td><td style='text-align: center; word-wrap: break-word;'>57.61</td><td style='text-align: center; word-wrap: break-word;'>64.40</td><td style='text-align: center; word-wrap: break-word;'>58.59</td><td style='text-align: center; word-wrap: break-word;'>62.84</td><td style='text-align: center; word-wrap: break-word;'>29.57</td><td style='text-align: center; word-wrap: break-word;'>50.33</td><td style='text-align: center; word-wrap: break-word;'>57.37</td></tr><tr><td colspan="12">Open-source Online Models</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Flash-VStream-7B [42]</td><td style='text-align: center; word-wrap: break-word;'>24.16</td><td style='text-align: center; word-wrap: break-word;'>29.36</td><td style='text-align: center; word-wrap: break-word;'>28.45</td><td style='text-align: center; word-wrap: break-word;'>33.71</td><td style='text-align: center; word-wrap: break-word;'>25.74</td><td style='text-align: center; word-wrap: break-word;'>28.8</td><td style='text-align: center; word-wrap: break-word;'>28.37</td><td style='text-align: center; word-wrap: break-word;'>39.06</td><td style='text-align: center; word-wrap: break-word;'>37.16</td><td style='text-align: center; word-wrap: break-word;'>5.91</td><td style='text-align: center; word-wrap: break-word;'>27.38</td><td style='text-align: center; word-wrap: break-word;'>27.88</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLM-online-8B [3]</td><td style='text-align: center; word-wrap: break-word;'>8.05</td><td style='text-align: center; word-wrap: break-word;'>23.85</td><td style='text-align: center; word-wrap: break-word;'>12.07</td><td style='text-align: center; word-wrap: break-word;'>14.04</td><td style='text-align: center; word-wrap: break-word;'>45.54</td><td style='text-align: center; word-wrap: break-word;'>21.2</td><td style='text-align: center; word-wrap: break-word;'>20.79</td><td style='text-align: center; word-wrap: break-word;'>22.22</td><td style='text-align: center; word-wrap: break-word;'>18.8</td><td style='text-align: center; word-wrap: break-word;'>12.18</td><td style='text-align: center; word-wrap: break-word;'>17.73</td><td style='text-align: center; word-wrap: break-word;'>19.26</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Dispider-7B [22]</td><td style='text-align: center; word-wrap: break-word;'>57.72</td><td style='text-align: center; word-wrap: break-word;'>49.54</td><td style='text-align: center; word-wrap: break-word;'>62.07</td><td style='text-align: center; word-wrap: break-word;'>44.94</td><td style='text-align: center; word-wrap: break-word;'>61.39</td><td style='text-align: center; word-wrap: break-word;'>51.63</td><td style='text-align: center; word-wrap: break-word;'>54.55</td><td style='text-align: center; word-wrap: break-word;'>48.48</td><td style='text-align: center; word-wrap: break-word;'>55.41</td><td style='text-align: center; word-wrap: break-word;'>4.3</td><td style='text-align: center; word-wrap: break-word;'>36.06</td><td style='text-align: center; word-wrap: break-word;'>45.31</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Streamo-3B [34]</td><td style='text-align: center; word-wrap: break-word;'>78.52</td><td style='text-align: center; word-wrap: break-word;'>52.29</td><td style='text-align: center; word-wrap: break-word;'>67.24</td><td style='text-align: center; word-wrap: break-word;'>44.38</td><td style='text-align: center; word-wrap: break-word;'>55.45</td><td style='text-align: center; word-wrap: break-word;'>71.20</td><td style='text-align: center; word-wrap: break-word;'>61.51</td><td style='text-align: center; word-wrap: break-word;'>51.18</td><td style='text-align: center; word-wrap: break-word;'>57.43</td><td style='text-align: center; word-wrap: break-word;'>16.67</td><td style='text-align: center; word-wrap: break-word;'>41.76</td><td style='text-align: center; word-wrap: break-word;'>51.64</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>StreamForest-7B [41]</td><td style='text-align: center; word-wrap: break-word;'>68.46</td><td style='text-align: center; word-wrap: break-word;'>53.21</td><td style='text-align: center; word-wrap: break-word;'>71.55</td><td style='text-align: center; word-wrap: break-word;'>47.75</td><td style='text-align: center; word-wrap: break-word;'>65.35</td><td style='text-align: center; word-wrap: break-word;'>60.87</td><td style='text-align: center; word-wrap: break-word;'>61.20</td><td style='text-align: center; word-wrap: break-word;'>58.92</td><td style='text-align: center; word-wrap: break-word;'>64.86</td><td style='text-align: center; word-wrap: break-word;'>32.26</td><td style='text-align: center; word-wrap: break-word;'>52.02</td><td style='text-align: center; word-wrap: break-word;'>56.61</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ThinkStream-3B (Ours)</td><td style='text-align: center; word-wrap: break-word;'>85.23</td><td style='text-align: center; word-wrap: break-word;'>64.22</td><td style='text-align: center; word-wrap: break-word;'>69.82</td><td style='text-align: center; word-wrap: break-word;'>49.43</td><td style='text-align: center; word-wrap: break-word;'>69.31</td><td style='text-align: center; word-wrap: break-word;'>64.13</td><td style='text-align: center; word-wrap: break-word;'>67.03</td><td style='text-align: center; word-wrap: break-word;'>53.87</td><td style='text-align: center; word-wrap: break-word;'>59.46</td><td style='text-align: center; word-wrap: break-word;'>43.55</td><td style='text-align: center; word-wrap: break-word;'>52.30</td><td style='text-align: center; word-wrap: break-word;'>59.66</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ThinkStream-7B (Ours)</td><td style='text-align: center; word-wrap: break-word;'>87.92</td><td style='text-align: center; word-wrap: break-word;'>59.63</td><td style='text-align: center; word-wrap: break-word;'>75.00</td><td style='text-align: center; word-wrap: break-word;'>53.93</td><td style='text-align: center; word-wrap: break-word;'>70.30</td><td style='text-align: center; word-wrap: break-word;'>67.93</td><td style='text-align: center; word-wrap: break-word;'>69.12</td><td style='text-align: center; word-wrap: break-word;'>51.17</td><td style='text-align: center; word-wrap: break-word;'>64.19</td><td style='text-align: center; word-wrap: break-word;'>66.67</td><td style='text-align: center; word-wrap: break-word;'>60.68</td><td style='text-align: center; word-wrap: break-word;'>64.90</td></tr></table>

### D Qualitative Analysis

Fig. 6 illustrates the Watch-Think-Speak paradigm across two scenarios. First, a user sets an event trigger for the text “EXIT.” The model leverages an incremental reasoning trace (<think>), correctly outputting <silent> during irrelevant scenes until the target appears, prompting a <response>. Second, a real-time query asks for the current time, which the model instantly identifies from visual evidence to deliver an accurate answer. These examples demonstrate the framework’s ability to seamlessly unify perception and reasoning, autonomously deciding when to observe silently and when to interact without relying on external classifiers.

### E Prompt Used

For the synthesis of ThinkStream instruction data, we design a specialized prompt that strictly relies on provided video segment descriptions. The complete prompt for the instruction data generation is presented as follows:

Thinking in Streaming Video

23

<div style="text-align: center;"><img src="imgs/img_in_image_box_268_230_963_715.jpg" alt="Image" width="56%" />

User Query: Please tell me when the text EXIT appears in the video.
Think: I see. The video starts with a clean white background. Two logos appear: CBDG ...
<silent>
Think: The scene shifts to a landscape with trees. A ...
<silent>
Think: The sign reads 'NORTH SHORE WINTER CLUB'. This sets the location context for the event.
<silent>
Think: The sign 'EXIT' appears. I have to notify the user.
<response>The sign 'EXIT' appears in the hallway.
User Query: What time is it now?
Think: User asks what time is it, and I see it's 12:56 from the board.
<response>It's 12:56 now.

</div>


<div style="text-align: center;">Fig. 6: Qualitative Example</div>


System: You are an expert in creating training data for Video-LLMs, specifically focusing on Streaming Video Q&A. Your task is to generate a JSON dialogue history strictly based on the provided descriptions and configurations. Follow these strict requirements:

1. Content Constraints: Base all dialogue exclusively on the provided video descriptions. Do not hallucinate details (actions, objects, text) not explicitly present.

2. Message Quantity: The generated dialogue history must contain exactly ONE User message.

3. Timing & Length Constraints: Every single Assistant message should be under 20 words. If multiple Assistant messages are generated, the time gap between consecutive Assistant messages should be at least 3.0 seconds (does NOT apply between a User and an Assistant message). The Assistant's first response must occur after the User's trigger.

4. Chronology: Timestamps must be floats (in seconds) strictly within segment boundaries and in chronological order.

5. Relative Temporal References: Strictly avoid using absolute timestamps (e.g., 'at 3.5 seconds') in the dialogue content. Use relative temporal markers based on events or actions (e.g., 'When the car turns left...').

6. Strict Compliance: You must strictly follow all requirements defined in the Scenario Configuration and Response Format Configuration.

24

Z. Liu et al.

User:
INPUT DATA:
Video Segment Descriptions: {input_data}
Scenario Configuration: {scenario_description}
Response Format Configuration: {format_instruction}
STRICT OUTPUT FORMAT:
Return a single JSON list containing the dialogue history (return [] if no valid dialogue can be generated):
[{"role":"user","content":"<generated_query","timestamp": <float_seconds>}]

To generate the internal reasoning trace of the model during real-time processing, we employ a Chain-of-Thought (CoT) data synthesis prompt. The detailed prompt for the CoT annotation task is shown below:

System: You are a data synthesis engine for a Real-Time Streaming Multimodal AI. Your task is to generate an "Internal Stream of Consciousness" (Chain-of-Thought) based on video captions and user-assistant dialogue. Follow these strict requirements:

1. Temporal Causality (No Future Peeking): A thought at timestamp T_think can ONLY reference captions or user messages where timestamp  $ \leq $ T_think. You strictly cannot mention events or user questions that happen after the thought's timestamp.

2. Timing & Density: The minimum gap between consecutive thoughts should be at least 2.0 seconds. Even when the user hasn't asked a question, continuously output "think" content. The generated CoT should extend to min(last_conversation_timestamp + 10s, last_caption_end_time).

3. User Query Response: When a user asks a question at timestamp T_user, you MUST generate a thought at exactly the same timestamp T_user that directly addresses the user's question, then resume continuous thinking.

4. Length: Every single "think" content should be no more than 50 words.

User:
INPUT CONTEXT:
Time-Grounded Captions:
{captions}
User-Assistant Conversation:
{conversation}
STRICT OUTPUT FORMAT:
Return ONLY a valid JSON list of objects in ascending order of timestamp:
[{"think": "<think_content>"", "timestamp": <float_seconds>}]