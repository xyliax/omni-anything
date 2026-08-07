    Reinforcement Learning for Interactive Streaming
                 Video Understanding:
     A Survey of Methods, Infrastructure, and Open
                      Challenges


                                             Lytton Feng
                                       lightedfeng@gmail.com



                                              Abstract
         Streaming video understanding—where models must continuously process un-
         bounded video feeds and interact with users in real time—has emerged as a critical
         frontier for Video Large Language Models (VideoLLMs). While supervised fine-
         tuning has driven rapid progress, reinforcement learning (RL) offers a principled
         framework for optimizing the temporally extended, reward-sparse decisions that
         streaming interaction demands: when to respond, what to say, and how to balance
         latency against accuracy. This survey provides a comprehensive review at the
         intersection of RL and interactive streaming video understanding. We organize
         existing work along three axes: (1) streaming VideoLLM architectures and their
         design constraints, (2) RL methods adapted for multimodal video tasks—including
         RLHF, DPO, GRPO, and reward modeling—and (3) the training infrastructure,
         datasets, and benchmarks that enable reproducible research. We identify five core
         challenges unique to RL in streaming settings: temporal credit assignment over un-
         bounded horizons, reward signal design for real-time interaction, silent-vs-speech
         exploration, computational cost of on-policy video rollouts, and the absence of stan-
         dardized preference data. We conclude with a roadmap connecting these challenges
         to concrete research directions.


1   Introduction
Video Large Language Models (VideoLLMs) have progressed from offline batch processing [26, 30]
to real-time streaming interaction [6, 35] and, most recently, to continuous interaction paradigms
where models perceive and generate simultaneously on 200-millisecond micro-turns [76]—enabling
systems that continuously observe video feeds, track evolving events, and respond to users on the fly.
This transition introduces a fundamentally different optimization landscape: a streaming assistant
must decide when to remain silent, when to proactively alert the user, and what to say—all under
strict latency constraints and with access to only the frames observed so far.
Supervised fine-tuning (SFT) has been the dominant training paradigm for streaming VideoLLMs [6,
35, 32]. However, SFT optimizes for next-token prediction given ground-truth context, which is
misaligned with the sequential decision-making nature of streaming interaction. In deployment,
errors compound: a premature response biases subsequent context management; a missed proactive
alert cannot be retroactively corrected. Reinforcement learning (RL), by contrast, optimizes policies
over entire interaction trajectories, directly targeting the metrics that matter—response quality, timing
accuracy, and user satisfaction.
The RL-for-VideoLLM space has exploded since early 2025. Over 40 papers now apply RL variants—
predominantly GRPO—to video understanding tasks, from temporal grounding to multi-turn rea-
soning. Yet the specific intersection of RL with streaming video understanding remains nascent:
only four works (MMDuet2 [34], VST [19], ThinkStream [8], R3-Streaming [33]) directly address
RL in streaming settings. This survey maps the full landscape to answer three practitioner-oriented
questions:
      1. What RL work exists for video understanding, and which methods are adaptable to stream-
         ing?
      2. What infrastructure is available—frameworks, datasets, reward models—that a practi-
         tioner can directly use?
      3. What is fundamentally hard about RL for streaming video, and where should the field
         invest next?

Scope. We focus on the intersection of three areas: streaming/online video understanding with
LLMs, RL-based training (RLHF, DPO, GRPO, reward modeling), and the practical infrastructure
enabling this research. We do not attempt to survey all of video understanding or all of RLHF.

Contributions. (1) A taxonomy of streaming VideoLLM architectures analyzed through the lens of
RL trainability. (2) A comprehensive catalog of 40+ RL-for-video papers organized by method, with
an assessment of streaming readiness. (3) An infrastructure guide covering frameworks, datasets,
reward models, and benchmarks. (4) Identification and analysis of five core challenges unique to
streaming video RL. (5) A tiered roadmap from near-term to long-term research directions.


2     Background

2.1   From Offline to Streaming Video Understanding

The evolution of VideoLLMs follows a clear trajectory from offline to online processing. Early
systems such as VideoChat [26], Video-LLaVA [30], and LLaVA-NeXT [84] buffer complete videos
before analysis. Recent systems shift to incremental processing: VideoLLM-online [6] introduces
the LIVE framework for streaming dialogue with an EOS-based silence mechanism; LiveCC [36]
demonstrates that ASR transcripts provide scalable supervision for real-time commentary; Dispi-
der [20] decouples perception from response generation to avoid autoregressive decoding blocking
real-time monitoring; StreamBridge [32] converts any offline VideoLLM into a streaming-capable
model; and AURA [35] unifies reactive QA and proactive responses with a dual sliding-window
context management mechanism.
The core technical challenges of streaming are:
      1. Unbounded context management: The video stream and interaction history grow without
         bound, but the LLM context window is finite. Solutions include sliding windows [35],
         memory banks [55, 39], and KV-cache compression [79, 56].
      2. The when-to-respond decision: The model must learn when to remain silent and when to
         speak—a discrete, temporally-extended decision that SFT handles only through heuristic
         loss weighting [35].
      3. Latency-accuracy tradeoff: Processing more frames improves accuracy but increases
         response latency. Real-time operation (2–10 FPS) demands aggressive token compression.
      4. Causal information constraint: Unlike offline models, streaming models cannot access
         future frames, making proactive responses (responding to events that will become relevant)
         fundamentally harder.

2.2   Reinforcement Learning for Language Models

We briefly review the RL methods most relevant to VideoLLM training, organized by the type of
supervision they require.

RLHF with PPO. The canonical pipeline [67]: SFT → reward model training on human preferences
→ PPO optimization against the reward model. Requires on-policy rollouts and a separate reward
model, making it the most expensive approach.


                                                  2
Direct Preference Optimization (DPO). Rafailov et al. [71] show that the optimal RLHF policy
can be extracted directly from preference pairs without an explicit reward model. Computationally
equivalent to SFT but requires paired preference data (chosen vs. rejected responses).

Group Relative Policy Optimization (GRPO). Introduced by DeepSeekMath [72], GRPO samples
multiple responses per prompt, uses a rule-based or model-based reward to rank them, and optimizes
relative to the group mean. No reward model needed; the reward can come from verifiable outcomes
(e.g., correctness of a math answer). This has become the dominant method for video RL.

Other variants. KTO [11] (unpaired preference optimization), SimPO [37] (length-normalized
margins), REINFORCE-leave-one-out [1].

2.3   RL for Multimodal Models: The Gap

Early RL work on multimodal models focused on images: LLaVA-RLHF [75] applied factuality-
augmented RLHF to image-language models; RLHF-V [82] introduced fine-grained correctional
feedback; Silkie [27] performed preference distillation for visual LLMs. Video RL emerged in
early 2024 with VLM-RLAIF [2] and LLaVA-Hound-DPO [83], then exploded after Video-R1 [13]
demonstrated GRPO for video reasoning in March 2025. However, streaming video RL—where
the RL policy must make decisions over continuous, unbounded video input—remains essentially
unexplored, with only three works (Section 4.4) directly addressing it.


3     Taxonomy of Streaming VideoLLM Architectures

We classify streaming VideoLLMs by architecture, as the architectural choice determines what RL
methods are feasible and what additional challenges arise.

3.1   Decoupled Trigger-Response Architectures

In decoupled architectures, a lightweight trigger model monitors the video stream and decides when
the main VideoLLM should generate a response. Dispider [20] separates perception, decision, and
reaction into distinct modules, allowing the perception module to continue processing frames while
the response model generates text. STRIDE [65] frames the when-to-speak decision as structured
sequence prediction, using a lightweight front-end to predict activation signals. StreamAgent [54] an-
ticipates temporal intervals containing task-relevant information for goal-driven proactive responses.

RL implication. The trigger model can be trained as an RL policy independently: the action space
is binary (trigger vs. silent), and the reward can be defined in terms of response timing accuracy
(e.g., PAUC metric). This modular structure simplifies the RL problem but introduces a fundamental
limitation: the trigger model and response model do not share contextual state, so the trigger cannot
condition on what the response model would say.

3.2   Unified End-to-End Architectures

Unified architectures use a single model for both the when-to-respond and what-to-respond decisions.
VideoLLM-online [6] achieves this through EOS prediction: the model learns to decode an EOS
token to remain silent on unannotated frames. AURA [35] introduces a <|silent|> token and a
Silent-Speech Balanced Loss to handle the extreme imbalance between silence and speech in stream-
ing data. Streamo [57] provides a single-stage pipeline for general-purpose streaming assistance.
StreamForest [55] organizes frames into event-level tree structures for persistent memory.

RL implication. The when and what decisions are jointly optimized, which is more principled but
also harder: the action space is the full token vocabulary at every time step, and the reward must
capture both timing and content quality. KV-cache management becomes critical during RL rollouts,
as each rollout processes a continuous video stream.


                                                  3
3.3   Full-Duplex Omni Architectures

Full-duplex models handle simultaneous video, audio, and text input/output. MiniCPM-o-4.5 [49]
supports concurrent video and audio input with text and speech output. VITA [44] processes video,
image, text, and audio with non-awakening interaction and audio interrupt capabilities. InternLM-
XComposer2.5-OmniLive [40] disentangles audio and video processing with a three-module archi-
tecture including long-term memory compression.

Qwen3.5-Omni. Qwen3.5-Omni [70] represents the state of the art in omni-modal architectures
with a Thinker–Talker dual-component design. The Thinker handles understanding and reasoning
across text, vision (SigLIP2 encoder), and audio (Audio Transformer trained on 40M hours), while
the Talker generates streaming speech output via multi-codebook RVQ tokens. A key innovation
is ARIA (Adaptive Rate Interleave Alignment), which dynamically aligns text and speech tokens
during streaming decoding to handle cross-lingual tokenization rate mismatches—solving a practical
problem that previous omni models addressed only through fixed-ratio heuristics. The model supports
256K tokens of context (10+ hours of audio or ∼400s of 720P video at 1 FPS), and achieves sub-
500ms first-packet latency (435ms audio, 651ms video for the Plus variant). From an RL perspective,
Qwen3.5-Omni’s post-training is notable: the Thinker undergoes three stages including interaction-
aligned RL, while the Talker is fine-tuned with DPO and GSPO on 20M+ hours of multilingual
speech data. This makes it one of the few omni models where RL is applied to both the reasoning
and generation components.

RL implication. The reward must evaluate multimodal output quality across modalities. R1-
Omni [85] applies RL with verifiable rewards for omni-modal emotion recognition; OmniVideo-
R1 [62] uses two-stage RL with modality attention. Qwen3.5-Omni’s Thinker–Talker decomposition
suggests a promising RL design pattern: train separate reward signals for understanding quality
(Thinker) and speech naturalness (Talker), avoiding the difficulty of a single reward that must evaluate
both simultaneously.

3.4   Continuous Interaction Architectures

A recent paradigm shift moves beyond both turn-based and even full-duplex designs toward con-
tinuous interaction, where the model operates on fine-grained temporal slices with no explicit turn
boundaries.

TML Interaction Model. The Thinking Machines Interaction Model [76] introduces a fundamen-
tally different interface: 200-millisecond micro-turns that interleave input and output as a single
continuous token stream (input_0, output_0, input_1, output_1, ...). Unlike full-duplex
systems that still maintain implicit turn structure, micro-turns eliminate turn boundaries entirely—the
model perceives and generates concurrently at all times, natively supporting interruptions, backchan-
neling, and simultaneous speech. The architecture uses a dual-model design: an Interaction Model
(276B MoE, 12B active parameters) handles real-time responsiveness, while a Background Model
manages asynchronous reasoning and tool use, with results streaming back into the ongoing con-
versation. Both models employ encoder-free early fusion: audio is processed as dMel signals
through lightweight embedding layers, and images are split into 40×40 patches encoded via hMLP,
all co-trained from scratch with the transformer backbone.
The model introduces novel benchmarks that measure interaction qualities no prior system could
achieve: TimeSpeak (initiating speech at user-specified intervals: 64.7% vs. GPT Realtime-2’s 4.3%),
CueSpeak (responding at semantically appropriate moments: 81.7% vs. 2.9% baseline), and visual
proactivity tasks (RepCount-A, ProactiveVideoQA, Charades) where all existing models scored near
zero.

Encoder-free architectures. The encoder-free trend extends beyond TML. Google’s
Gemma 4 12B [16] replaces the traditional vision encoder with a lightweight 35M-parameter vision
embedder (a single matrix multiplication plus positional embedding) and projects raw 16 kHz audio
linearly into the LLM input space. This design reduces first-token latency and memory overhead of
secondary processing modules, making it architecturally favorable for real-time streaming—though
Gemma 4 itself does not implement an explicit streaming interaction mode (video input is capped at


                                                   4
       Table 1: Streaming VideoLLM architectures compared along RL-relevant dimensions.

Property                    Decoupled                Unified                 Full-Duplex                   Continuous
When-to-respond           Separate trigger        Silence token              Continuous                 Micro-turn (200ms)
RL action space           Binary + vocab           Full vocab             Multi-modal vocab           Continuous multi-modal
Joint timing-content            No                     Yes                       Yes                      Yes (+ overlap)
KV-cache complexity           Lower                   High                     Highest                        Highest
Rollout cost                  Lower                   High                     Highest                        Highest
Encoder-free                    No                     No                        No                    Yes (TML, Gemma 4)
End-to-end RL gradient        Partial          No (encoder frozen)              Partial                    Yes (possible)
Example systems          Dispider, STRIDE    AURA, VideoLLM-online    MiniCPM-o, Qwen3.5-Omni            TML Interaction
Open-source training          Partial            Yes (multiple)                Limited                          No


60s at 1 FPS). The shared intuition is that as LLM backbones grow more capable, dedicated encoders
become a bottleneck rather than an asset for streaming: they add latency, require cross-module
synchronization, and prevent end-to-end gradient flow.

RL implication. Continuous interaction architectures pose new RL challenges beyond those
of full-duplex systems. The action space is no longer “respond or stay silent per chunk” but
a continuous decision at every 200ms slice—the agent must learn micro-level timing, overlap
management, and proactive visual responses simultaneously. The dual-model design (interaction
+ background) introduces a multi-agent RL structure: the interaction model must learn when to
defer to the background model and how to integrate asynchronous results. The encoder-free design,
however, is RL-friendly: end-to-end gradient flow from rewards through visual processing enables
joint perception-decision optimization (Section 8)—a long-term goal that is architecturally blocked
in encoder-frozen systems like AURA.

3.5   Architectural Comparison

Table 1 summarizes the key properties of each architecture type from an RL perspective.

4     RL Methods for Video Language Models
We now survey the rapidly growing body of work applying RL to video understanding, organizing by
method family and assessing each method’s readiness for streaming settings.

4.1   The Video-R1 Family: GRPO Dominates

The release of Video-R1 [13] in March 2025 catalyzed an explosion of GRPO-based methods
for video understanding. Video-R1 introduces T-GRPO (Temporal GRPO), which adds temporal
awareness to the standard GRPO framework by rewarding correct identification of when events
occur. The key insight is that GRPO’s requirement for only a verifiable reward signal (rather than
a learned reward model) makes it naturally suited to video tasks where correctness can be checked
automatically (e.g., multiple-choice QA, temporal grounding IoU).

GRPO variants for video.      The subsequent literature has produced numerous specializations:
       • TW-GRPO [10]: Token-Weighted GRPO with soft rewards via multi-choice QA, addressing
         the high variance of binary rewards.
       • PA-GRPO [23]: Process-Aware GRPO that assigns separate rewards for perception and
         reasoning stages, addressing temporal credit assignment.
       • KF-GRPO [45]: KeyFrame-aware GRPO that emphasizes temporally salient frames.
       • Reg-GRPO [46]: Difficulty-aware Regressive GRPO that adjusts reward magnitude by
         question difficulty.
       • GRPO-CARE [48]: Consistency-Aware RL that penalizes logically incoherent reasoning
         chains (standard GRPO achieves only 57.9% reasoning consistency).
       • Curriculum GRPO [24]: Decomposes video difficulty into orthogonal perceptual and
         cognitive axes, training from easy to hard.


                                                 5
Streaming readiness. Standard GRPO operates on complete question-answer pairs. Adapting it to
streaming requires defining rewards over interaction trajectories rather than individual responses,
and handling the fact that the visual context changes during rollout generation.

4.2   DPO and Preference Optimization for Video

DPO avoids the need for on-policy rollouts, making it computationally attractive for video models
where rollouts are expensive.
       • LLaVA-Hound-DPO [83]: The first DPO application to video LLMs, using language model
         rewards to generate preference pairs from 17K video instructions.
       • ISR-DPO [3]: Iterative Self-Retrospective DPO (AAAI 2025) that addresses the length bias
         and visual hallucination amplification of naive iterative DPO.
       • RRPO [53]: Refined Regularized Preference Optimization (NeurIPS 2025) with token-wise
         KL and sub-sequence rewards, enabling finer-grained credit assignment.
       • TPO [29]: Temporal Preference Optimization for long-form video, extending DPO with
         temporal preference structures.
       • VideoSAVi [43]: Self-aligned DPO without human supervision, using model-generated
         preference pairs.

Streaming readiness. DPO requires paired preferences (chosen vs. rejected). For streaming, this
means generating two complete interaction trajectories for the same video stream—one good, one
bad. No streaming-specific preference dataset exists (Section 6.5).

4.3   RLAIF and PPO for Video

VLM-RLAIF [2] (ACL 2024 Oral) was the first to apply RLAIF (PPO with AI-generated rewards)
to video LLMs, demonstrating that AI feedback can replace human annotation for video preference
learning. This is particularly relevant for streaming, where human annotation of real-time interactions
is prohibitively expensive.

4.4   RL for Temporal Decision-Making in Streaming

The works that directly address RL in streaming video settings represent the frontier of this survey’s
topic:

MMDuet2 [34] applies multi-turn RL with a PAUC (Proactive Area Under the Curve) reward to
optimize both response quality and timing in streaming video interaction. The PAUC metric jointly
evaluates the accuracy and timeliness of proactive responses. This is the most directly relevant work
for training streaming VideoLLMs with RL.

VST (Video Streaming Thinking) [19] introduces a post-training pipeline combining VST-SFT
(structural adaptation to causal streaming reasoning) with VST-RL (RL in a multi-turn video interac-
tion environment with verifiable rewards). The key insight is “watch and think simultaneously”—
activating reasoning over incoming clips during streaming to amortize LLM latency over video
playback time.

ThinkStream [8] proposes a Watch-Think-Speak paradigm with Reasoning-Compressed Streaming
Memory (RCSM), where intermediate reasoning traces serve as compact semantic memory replacing
outdated visual tokens. Uses RL with verifiable rewards for streaming settings.

R3-Streaming [33] casts streaming comprehension as a sequential decision-making problem with a
three-decision agentic policy: (1) Active Forgetting—age-aware memory compression that selectively
discards stale visual tokens, (2) Proactive Response—assessing whether accumulated evidence is
sufficient to answer now, and (3) Adaptive Thinking—routing complex queries to larger models
while sending simple ones to lightweight models. R3-Streaming introduces TB-GRPO, a GRPO
variant with stability mechanisms for streaming RL, and achieves 57.9 on OVO-Bench and 76.4 on
StreamingBench while reducing visual token usage by 95–96%. Its three-decision structure is the
most explicit formalization of streaming video understanding as an RL problem to date.


                                                  6
                      Table 2: Video reward model benchmarks and datasets.
Resource                  Type                                 Scale   Key Finding
VideoRewardBench [58]     Benchmark                 1,563 samples      Top models achieve only ∼57% accuracy
VURB [66]                 Benchmark+Data        2,100 pairs + 35K      Long CoT reasoning preferences
Omni-RewardBench [50]     Benchmark          9 tasks, 5 modalities     248K preference pairs across modalities
Omni-RRM [61]             Model                  Rubric-grounded       Automatic rubric-based preference synthesis

Table 3: RL methods for video understanding: streaming readiness assessment. “Streaming-tested”
means the method has been evaluated on streaming video tasks.

 Method           Representative     Open Code         Video    Streaming    Key Limitation
 GRPO             Video-R1              Yes             Yes        No        Offline QA only
 T-GRPO           Video-R1              Yes             Yes        No        Temporal awareness limited
 TW-GRPO          TW-GRPO               Yes             Yes        No        Still single-response
 PA-GRPO          VIDEOP2R              Yes             Yes        No        Separate reward stages
 DPO              LLaVA-Hound           Yes             Yes        No        Needs preference pairs
 RRPO             RRPO                  Yes             Yes        No        Token-wise KL overhead
 RLAIF            VLM-RLAIF             Yes             Yes        No        PPO cost
 Multi-turn RL    MMDuet2               Yes             Yes        Yes       Limited to PAUC metric
 VST-RL           VST                   Yes             Yes        Yes       New, limited evaluation
 Stream RL        ThinkStream           No              Yes        Yes       No code released
 Agentic stream   R3-Streaming          Yes             Yes        Yes       Three-decision policy
 Omni RL          Qwen3.5-Omni      Weights only        Yes       Partial    Closed training pipeline
 Micro-turn       TML Interaction       No              Yes        Yes       No training code


4.5   Reward Models and Evaluation

Video reward models remain significantly weaker than their text counterparts. Table 2 summarizes
the key resources.
A critical gap: no reward model has been trained or evaluated on streaming video interactions, where
the reward must account for response timing, silence decisions, and temporally evolving content.

4.6   Summary: RL Methods and Streaming Readiness

5     Training Infrastructure and Data
5.1   Training Frameworks for Video RL

General RL post-training systems. The RL-for-LLM infrastructure has matured rapidly. Open-
RLHF [21] provides a Ray+vLLM+DeepSpeed architecture supporting PPO, GRPO, DAPO, and
REINFORCE++, with OpenRLHF-M extending it to multimodal models. verl/HybridFlow [73] com-
bines single- and multi-controller paradigms with a 3D-HybridEngine that reshards model parameters
between FSDP/Megatron training and vLLM/SGLang generation, achieving 1.5–20× throughput.
Its co-located placement uses a sleep/wake mechanism to time-share GPU memory between rollout
and training—a design that can accommodate large vision encoders. AReaL [18] fully decouples
generation from training with a staleness-enhanced PPO variant, achieving 2.77× speedup. Lla-
maRL [77] scales async RL to 405B models on 1024 GPUs with 10.7× speedup. ROLL/ROLL
Flash [4, 5] is battle-tested on 200B+ MoE models across thousands of GPUs for weeks. Relax [80]
from Xiaohongshu provides a six-layer service-oriented architecture with three execution modes
(co-located sync, fully async with configurable staleness, and hybrid), and is one of the few systems
supporting omni-modal RL training (text, vision, audio) with native MoE expert parallelism and
SGLang-based inference.

Video-specific RL frameworks.       Dedicated video RL tools remain scarce:
       • EasyVideoR1 [60]: Complete video RL pipeline with offline tensor caching (eliminating
         redundant video decoding for 1.47× throughput), 11 reward types, and 22 benchmark
         integrations.


                                                   7
            • LongVILA-R1 [9]: Introduces Multi-modal Reinforcement Sequence Parallelism (MR-SP)
              with cached video embeddings, achieving 2.1× speedup on 512-frame video RL for 7B
              models.
            • LMM-R11 : Fork of OpenRLHF for multimodal R1-style RL; 4.7× speedup over R1-V.
            • Open-R1-Video2 : First open-source R1-like Video-LLM training code with data.

Streaming gap. None of these frameworks natively support streaming video RL training. verl’s
sequence-length balancing (get_seqlen_balanced_partitions) and async rollout mode provide
useful building blocks, but it lacks incremental frame ingestion and frame-level reward signaling.
Relax’s fully async mode with staleness control and StreamingDataLoader (which consumes roll-
out data incrementally during generation) comes closest to a streaming-ready architecture, but it
still organizes training around fixed sample batches rather than temporal windows. Adapting any
current framework for streaming video RL requires: (1) a streaming data loader that feeds frames
incrementally and simulates real-time video arrival, (2) KV-cache management during multi-step
rollout generation across sliding windows, and (3) trajectory-level reward computation that evaluates
timing, content, and silence decisions jointly.

5.2        Pipeline Efficiency for Multimodal RL

A consistent finding across the literature is that the rollout (generation) phase accounts for 84–
91% of total RL training time [77, 18], making pipeline efficiency—not algorithmic design—the
dominant practical concern. Multimodal RL exacerbates this: video encoding adds compute, variable
video lengths create load imbalance, and KV-cache requirements multiply memory pressure. We
organize the emerging solutions by the problem they address.

Long-tail rollout mitigation. When rollout lengths follow a heavy-tailed distribution (common
with agentic and video tasks), a few slow samples stall entire batches. RLHFuse [42] breaks
the RL workflow into sample-level subtasks with inter-stage fusion and micro-batch intra-stage
fusion, achieving up to 3.7× throughput improvement. RollPacker [15] introduces tail batching:
consolidating long-tail prompts into dedicated “long rounds” while keeping the majority as balanced
“short rounds” (2.0–2.6× speedup over verl). Laminar [74] uses a dynamic repack mechanism with
relay workers, achieving up to 5.48× throughput on 1024 GPUs. Speculative decoding approaches—
DAS [78], BubbleSpec [59], RhymeRL [51]—reuse prior trajectory segments or rollout distributions
to accelerate generation by 2–3×.

Pipeline bubble reduction. Even with balanced rollout times, pipeline bubbles arise from stage de-
pendencies between rollout, reward computation, and training. Zero Bubble Pipeline Parallelism [69]
splits backward passes into activation-gradient and weight-gradient parts, enabling near-zero-bubble
schedules (23% improvement over 1F1B). OPPO [81] overlaps upstream and downstream models via
right-sized chunk streaming (1.8–2.8× speedup). RollMux [52] reclaims dependency bubbles at the
cluster level, multiplexing the idle phase of one RL job with the active phase of another (1.84× over
standard disaggregation).

Async RL and staleness control. Asynchronous designs decouple rollout from training but intro-
duce data staleness. AReaL [18] demonstrates that staleness-enhanced PPO maintains convergence
at 2.77× speedup. VCPO [22] (ICML 2026) provides theoretical stability guarantees by dynami-
cally scaling the learning rate with effective sample size, remaining stable at 128 steps off-policy.
PipelineRL [68] introduces in-flight weight updates where the generation engine receives new model
weights with minimal interruption during sequence generation.

Multimodal-specific pipeline challenges. The compute imbalance between vision encoders and
LLM backbones creates additional inefficiency. Optimus [41] schedules vision encoder computation
inside LLM pipeline bubbles at the kernel level, achieving 20–21% speedup training ViT-22B + GPT-
175B on 3072 GPUs. DIP/PipeWeaver [47] separates modalities into dedicated pipeline segments
with dynamic per-batch reconfiguration, achieving up to 97% efficiency improvement. DistTrain [38]
      1
          https://github.com/TideDra/lmm-r1
      2
          https://github.com/Wang-Xiaodong1899/Open-R1-Video


                                                   8
Table 4: RL training frameworks compared along streaming video RL-relevant dimensions. “Mul-
timodal” means native vision/audio support; “Async” means fully asynchronous rollout-training
decoupling.

Framework        Async     Multimodal       Long-tail       Bubble      Streaming       Backend
OpenRLHF            No        Partial          No             No              No        DeepSpeed+vLLM
verl                Yes       VLM          Seq-balance      Partial           No        FSDP/Megatron+vLLM
AReaL               Yes        No              No         Staleness           No        Megatron
LlamaRL             Yes        No              No          Offload            No        PyTorch native
ROLL                Yes        No              Yes           Yes              No        Ray+multi
Relax               Yes       Omni           Partial      StreamDL            No        Megatron+SGLang
EasyVideoR1         No        Video            No             No              No        OpenRLHF
LongVILA-R1         No        Video            No             No              No        Custom


                           Table 5: Available datasets for video RL training.

          Dataset                   Type                              Scale    Source
          Video-R1-260k             RL training (GRPO)              260K       Video-R1
          Video-R1-CoT-165k         SFT cold start                  165K       Video-R1
          Temporal-RLT-490k         RL training                     490K       [28]
          Video-Thinker-10K         SFT+RL                           10K       Video-Thinker
          ShareGPTVideo prefs       DPO preferences                  17K       LLaVA-Hound
          VUP-35K                   Reward model                 35K pairs     VURB
          Omni-Preference           Reward model                248K pairs     Omni-RewardBench
          Streamo-Instruct-465K     SFT (streaming)                 465K       Streamo
          Live-CC-5M                Pre-training (streaming)          5M       LiveCC
          Stream-IT                 SFT (streaming)                      –     StreamBridge
          AURA streaming data       SFT (streaming)                 115K       AURA
          No streaming-specific RL/preference datasets exist.



disaggregates encoder, LLM backbone, and generator into independently orchestrated resource pools
(54.7% MFU on 1172 GPUs).


KV-cache for RL. KV-cache compression during rollouts is deceptively hard: Sparse-RL [64]
shows that “nearly lossless” compression causes catastrophic policy mismatch between dense old-
policy log-probabilities and sparse sampled rollouts, requiring importance-based reweighting to
correct. Shadow Mask Distillation [63] addresses this for PPO/GRPO/Online-DPO specifically.


The multimodal RL pipeline gap. Despite this rapid progress, a critical observation emerges:
long-tail solutions address rollout-side imbalance, while multimodal pipeline solutions address
training-side imbalance, but no system addresses both simultaneously for multimodal RL. In
streaming video RL, both sides are imbalanced: rollouts vary because interactions have different
lengths (a single-turn QA vs. a 5-minute proactive monitoring session), and training varies because
different samples contain different amounts of video (different frame counts, visual token counts,
and temporal memory lengths). This dual imbalance creates a compounding effect: if the rollout
side is fast but the training side is slow on a heavy-video batch, rollout data becomes stale; if the
training side finishes quickly but the next batch of rollouts is slow, training resources sit idle. Existing
solutions treat these as independent problems—we argue they must be solved jointly (Section 6.4).
Table 4 summarizes the key RL training frameworks along dimensions relevant to streaming video
RL.


5.3   Video Preference and Training Datasets

Table 5 catalogs available datasets for video RL training.


                                                     9
    Table 6: Streaming video understanding benchmarks and their suitability as RL reward signals.

      Benchmark             Scale                  RL-Suitable?     Key Feature
      StreamingBench [31]   900 videos, 4.5K QA         Partially   Multi-timestamp QA, audio+video
      OVO-Bench [12]        644 videos, 2.8K QA         Partially   Backward/real-time/forward tasks
      OmniMMI [7]           Multi-task                  Partially   Proactive reasoning + interaction
      RTV-Bench             552 videos, 4.6K QA           Yes       Answers evolve with scenes
      Inf-Streams-Eval      20 games, per-second          Yes       Hours-long continuous eval
      ESTP-Bench            Ego-streaming               Partially   Proactive task with F1 metric
      StreamEQA             156 videos, 21K QA          Partially   Embodied streaming QA



5.4    Benchmarks for Streaming Video Interaction

RTV-Bench and Inf-Streams-Eval are the most promising as RL reward signals because they evaluate
how model responses evolve with the stream, providing time-sensitive correctness labels.

5.5    Compute Requirements

A practical analysis of training costs:
         • SFT baseline: AURA trains on 32×80GB accelerators for one epoch on 174K samples
           (∼1.2B tokens). This is the reference point.
         • GRPO overhead: Each prompt requires K rollouts (typically K=4–8). For video, each roll-
           out processes vision tokens through the encoder. EasyVideoR1’s tensor caching reduces this
           by caching encoded visual features, achieving 1.47× throughput over naive implementation.
         • PPO overhead: Requires an additional reward model in memory. For 8B video models,
           this roughly doubles GPU memory requirements.
         • DPO: Computationally similar to SFT (no rollouts), but requires pre-computed preference
           pairs.
         • KV-cache for streaming rollouts: A 30-second video window at 2 FPS with Qwen3-VL-8B
           produces ∼60 vision chunks, each generating hundreds of tokens. The KV-cache for a single
           rollout can exceed 10GB; K parallel rollouts require K× this.


6     Core Challenges: Why Is RL Hard for Streaming Video?

We now analyze five challenges that are unique to RL in streaming settings—not merely harder
versions of existing problems, but qualitatively different obstacles that require new solutions.

6.1    Temporal Credit Assignment over Unbounded Horizons

In standard video QA, a single question receives a single response, and the reward is clearly at-
tributable. In streaming interaction, a response at time t depends on visual evidence accumulated
over an unbounded past, some of which may have been evicted from the sliding window. Standard
RL credit assignment assumes a fixed-length episode; streaming interaction has no natural episode
boundary.

Why this is hard. AURA’s dual sliding-window truncates visual context to N = 30s and retains
only M = 10 recent QA groups. A proactive response triggered by an event at time t − 25s that was
evicted by time t receives a reward, but the causal evidence for that reward is no longer in the model’s
context. GRPO, which assigns uniform credit across all tokens in a response, cannot distinguish
between tokens that were causally supported by visual evidence and those that were hallucinated
from language priors.

Existing partial solutions. PA-GRPO [23] separates perception and reasoning rewards.
AVATAR [25] introduces Temporal Advantage Shaping (TAS) that emphasizes early (planning)
and late (synthesis) reasoning phases. Neither addresses the evicted-evidence problem specific to
streaming.


                                                   10
Implication. New methods are needed that can assign credit across the boundary of context window
truncation—potentially through auxiliary reward signals that score responses based on the full visual
history (available during training but not during inference).

6.2   Reward Signal Design for Real-Time Interaction

What makes a streaming response “good”? It depends on at least three factors simultaneously:
      1. Content accuracy: Is the response factually correct given the visual evidence?
      2. Timing: Was the response generated at the right moment—not too early (insufficient
         evidence), not too late (user already moved on)?
      3. Silence appropriateness: Should the model have remained silent instead?
No existing reward model captures all three. MMDuet2’s PAUC metric is a start: it jointly evaluates
accuracy and timeliness of proactive responses. But PAUC was designed for a narrow setting
(proactive alerts) and does not generalize to the full range of streaming interactions (real-time QA,
multi-response QA, mixed interaction sequences).

The reward model gap. Top video reward models achieve only ∼57% accuracy on VideoReward-
Bench [58]—barely above random. For streaming, the reward model would additionally need to
understand temporal dynamics, silence decisions, and interaction history. Building such a model
requires streaming preference data that does not yet exist (Section 6.5).

6.3   The Silent-Speech Exploration Problem

In streaming interaction, the model must learn when not to speak. AURA’s training data contains
far more silent tokens than speech tokens, and its Silent-Speech Balanced Loss down-weights silent
supervision to prevent the model from being biased toward silence. This is an SFT solution; the RL
analog is an exploration problem.

Why this is hard. In RL, the model must explore to discover which actions lead to high reward.
For streaming video, random exploration produces mostly garbage responses at random times—the
probability of randomly generating a useful proactive response at the right moment is vanishingly
small. Conversely, a policy that learns to always stay silent achieves reasonable reward (no penalty
for wrong responses) but misses all proactive opportunities.

Potential approaches. (1) Warm-start from a well-trained SFT policy (AURA, VideoLLM-online)
to ensure the initial RL policy already has reasonable timing behavior. (2) Use curriculum learning:
first train on easy real-time QA (where the user explicitly asks), then gradually increase the proportion
of proactive scenarios. (3) Define a separate exploration bonus for speech attempts, analogous to
curiosity-driven exploration.

6.4   Computational Cost and Pipeline Efficiency

PPO and GRPO require generating rollouts—complete interaction trajectories. For text-only models,
a rollout is a sequence of tokens. For streaming video models, a rollout requires:
      1. Processing video frames through a vision encoder (frozen or fine-tuned).
      2. Managing KV-caches that grow with the video stream.
      3. Simulating the streaming interaction loop: frame arrival → silence/response decision →
         next frame.
This is 10–100× more expensive than text-only rollouts. EasyVideoR1 [60] partially addresses this
with offline tensor caching (pre-computing visual features), but this only works when the vision
encoder is frozen. For streaming rollouts where the visual context evolves over time, the KV-cache
must be maintained across the entire trajectory.

The AURA KV-cache problem. AURA’s inference framework uses a floating-window KV-cache
strategy: allow the window to extend to N + N ′ , then batch-evict N ′ chunks and recompute the
KV-cache for the remaining N chunks. During RL training, this recomputation must happen for each
rollout in the group, multiplying the already-expensive operation by the group size K.


                                                   11
Dual imbalance: the unique challenge of streaming video RL. Streaming video RL is, to our
knowledge, the only RL setting that exhibits simultaneous imbalance on both the rollout and training
sides—a compounding effect that existing solutions, designed for only one side, cannot resolve.
On the rollout side, interactions have extreme length variance: a single-turn QA might complete in 5
seconds, while a proactive monitoring task (“alert me when the score changes”) runs for minutes.
Multi-response QA generates outputs at multiple timestamps. Silence decisions extend the trajectory
without producing tokens. The ratio between the fastest and slowest rollouts in a batch can easily
exceed 100×—far worse than text-only RL, where the variance comes only from response length.
On the training side, different samples impose vastly different compute loads: video window lengths
differ (10s vs. 60s), frame counts differ (20 vs. 120 frames at 2 FPS), visual token counts differ
(resolution-dependent), temporal memory sizes differ, and response token counts differ. If the vision
encoder participates in training (Section 3.4), the encoder compute for a 120-frame sample is 6× that
of a 20-frame sample. A batch that happens to contain many heavy-video samples takes far longer to
train than a batch of short-video samples.
The compounding effect: when training is slow (heavy-video batch), rollout data becomes stale; when
the staleness bound is reached, rollout workers must stop and wait, creating cascading bubbles across
both sides. Conversely, when rollout is slow (long interactions), training resources sit idle. Existing
long-tail solutions (RollPacker [15], Laminar [74]) address only rollout-side variance; multimodal
pipeline solutions (Optimus [41], DIP [47]) address only training-side variance. Neither handles the
cross-side coupling between rollout and training imbalance.

Time-window scheduling. A promising direction is to replace fixed-batch RL training with time-
window-based scheduling: instead of collecting a fixed number of completed rollouts before starting
training, the system collects all interactions that have completed within a time window and trains on
them immediately. Fixed-batch scheduling creates an artificial synchronization barrier—the slowest
rollout in the batch determines when training begins. In streaming video RL, where task observation
times range from seconds (“who is speaking?”) to minutes (“alert me when the score changes”),
this barrier is catastrophic: 255 fast rollouts wait idle for the 1 slow one. Time-window scheduling
removes this barrier: every T seconds, the system harvests whatever rollouts have completed and
begins training; unfinished rollouts continue and are harvested in subsequent windows. Preliminary
results on the LLaVA-Video-178K dataset suggest 2.4× throughput improvement over batch-based
scheduling [14], though this has not yet been validated on streaming-specific workloads.

Encoder-side sample splitting for balanced training. To address training-side imbalance, a
second technique decomposes vision encoder computation into modality fragments (e.g., individual
frames or frame groups) and schedules them into the idle intervals between LLM forward and
backward passes. Rather than processing all visual tokens for a sample in one burst, the encoder
work is spread across pipeline stages, flattening the per-step variance. This is particularly important
for streaming video RL with trainable encoders: if the goal is to optimize what the model attends to
(which frames to retain, how to compress temporal memory), the encoder must receive RL gradients.
Encoder-free architectures (Section 3.4) sidestep this entirely—the lightweight vision embedder adds
negligible compute and participates naturally in end-to-end RL training. This architectural advantage
may ultimately prove more impactful than pipeline-level scheduling.

Dynamic resource conversion. When rollout throughput and training throughput are mismatched,
dynamic role conversion can rebalance: excess rollout GPU instances are temporarily repurposed
as training workers (or vice versa), maximizing overall utilization. This is conceptually related to
RollMux’s [52] phase-level multiplexing but operates within a single job rather than across jobs.

The difficulty: RL training semantics. These scheduling innovations face a fundamental con-
straint: RL training has semantic dependencies that prevent arbitrary sample reordering. Policy
version alignment (rollout must use the current policy), old log-probability alignment (the reference
model must match), reward and advantage consistency (GRPO responses within a group must be
compared jointly), and staleness bounds (data from too-old policies degrades convergence) all impose
ordering constraints. A time-window scheduler must respect these constraints—determining which
samples are ready, which must wait for their group to complete, and how to compose samples into


                                                  12
Table 7: Industry applications mapped to streaming video RL challenges. Each domain exhibits the
same “when to act” decision structure that SFT cannot optimize.

      Domain              TAM                 “When to Act”            Key RL Challenge
      Autonomous driv-    $300B+              When to brake/yield      Delayed safety reward, ex-
      ing                                                              treme latency constraint
      Surgical AI         $1B (24% CAGR)      When to alert surgeon    High-stakes sparse reward,
                                                                       personalization
      Industrial QC       $30B                When to reject/flag      Asymmetric               false-
                                                                       positive/negative costs
      Live streaming      $186B platform      When to interject        Silent-speech      exploration
                                                                       (Sec. 6.3)
      Smart retail        $8B                 When to trigger alert    Multi-agent coordination
      Spatial computing   $160B               What to overlay          Information overload manage-
                                                                       ment
      Sports analytics    $10B                Real-time tactical ad-   Trajectory-level reward (game
                                              vice                     outcome)
      Embodied AI         Emerging            When                to   Continuous perception-action
                                              grasp/navigate           loop



balanced batches without violating training semantics. This is not a simple queue-sorting problem
but a constrained optimization over training correctness, compute balance, and data freshness.

6.5   Absence of Standardized Preference Data

DPO needs preference pairs; RLHF needs reward labels; even GRPO benefits from high-quality
reward functions. For streaming video, none of these exist at scale.

Why construction is hard. Annotating streaming preferences requires human annotators to watch
video streams in real time and evaluate (1) whether the model responded at the right time, (2) whether
the response was accurate, and (3) whether silence would have been better. This is 3–5× more
expensive per sample than standard video QA annotation because annotators must track temporal
context.

Potential approaches. (1) Synthetic preferences: Use a strong offline VideoLLM (which has ac-
cess to the full video) to judge the quality of streaming responses. The offline model can verify factual
accuracy against future frames that the streaming model did not have access to. (2) Benchmark-as-
reward: Use automated streaming benchmarks (StreamingBench, OVO-Bench) as reward signals
for GRPO. (3) Self-play: Generate multiple streaming trajectories from the same model and use a
consistency signal as the preference.

7     Application Landscape
Interactive streaming video understanding is not a purely academic exercise—it is the enabling
technology for a broad range of high-value industry applications. Table 7 maps application domains
to the streaming RL challenges identified in Section 6, revealing a consistent pattern: across all
domains, the core difficulty is learning when and how to act on continuous visual input under
uncertainty, precisely the problem that RL is designed to solve.

Flagship platforms. Google’s Project Astra [17] is the most direct commercial embodiment
of interactive streaming video understanding: it processes continuous video and audio with sub-
300ms response times, maintains memory across frames, and supports both reactive and proactive
interactions. Its current SFT-based approach faces exactly the challenges our survey identifies—when
to proactively offer information, how to manage memory under context limits, how to balance
latency against depth. Similarly, the Gemini Multimodal Live API has been deployed for real-time
manufacturing inspection, streaming camera feeds into the model with dynamic prompts and instant
defect alerts. Apple Vision Pro 2 (M5 chip, February 2026) runs real-time object recognition, spatial
mapping, and NLP simultaneously on-device, and Streamlabs’ Intelligent Streaming Agent (with


                                                  13
NVIDIA) provides AI co-hosting for live streams—both requiring continuous visual perception with
timing-sensitive responses.

The cross-domain pattern. Across all domains, three elements recur: (1) rewards are delayed and
sparse—surgical outcomes, game results, customer satisfaction, and viewer retention are measured
over trajectories, not individual frames; (2) the “when to act” decision is critical—acting too
early wastes resources or distracts, acting too late misses the opportunity; (3) exploration under
uncertainty is essential—the system must balance gathering more visual information against acting
on current knowledge. These are the defining characteristics of RL problems, and they explain why
SFT-trained streaming systems plateau: SFT optimizes per-token prediction, not trajectory-level
outcomes.

Infrastructure implications. The compute demands of these applications amplify the pipeline
efficiency challenges of Section 6.4. Industrial deployment requires training on diverse, long-horizon
video data (surgical procedures lasting hours, full sports matches, continuous surveillance feeds),
pushing the rollout-side imbalance to extremes. Edge deployment (Vision Pro, smart glasses)
constrains model size, making efficient RL training critical for smaller models that must compensate
for limited capacity with better-optimized policies. The dual imbalance problem—rollout-side
interaction variance combined with training-side visual compute variance—is not an academic
concern but a deployment bottleneck that determines whether streaming video RL can transition from
research prototypes to production systems.


8     Roadmap: From Challenges to Solutions

We organize actionable research directions by feasibility and timeline.

8.1   Near-Term: Directly Actionable
      1. Apply GRPO to existing streaming VideoLLMs. Use AURA or VideoLLM-online as the
         SFT base. Use StreamingBench scores as verifiable rewards. This requires only adapting
         EasyVideoR1’s pipeline to handle streaming data.
      2. DPO with synthetic streaming preferences. Generate streaming interaction trajectories
         from two models (e.g., AURA-8B vs. a weaker baseline) and use an offline judge to create
         preference pairs.
      3. Separate timing and content RL. Train a lightweight timing policy (when to respond)
         with RL on the PAUC metric, while keeping the content generation model frozen. This
         decomposition reduces the RL problem to a tractable binary decision.

8.2   Medium-Term: Infrastructure Building
      1. Streaming video preference dataset. Collect 10K+ streaming interaction trajectories with
         human preference annotations on timing and content. Use real-time annotation tools where
         annotators watch streams and provide feedback.
      2. Streaming-aware reward model. Train a reward model on the streaming preference dataset
         that scores (timing, content, silence) jointly.
      3. Extend RL frameworks for streaming. Add streaming video support to OpenRLHF-M:
         incremental frame feeding, KV-cache management across rollouts, trajectory-level reward
         aggregation.

8.3   Long-Term: Fundamental Research
      1. Temporal credit assignment for streaming RL. Develop methods that can assign credit
         across context window boundaries, potentially using auxiliary memory or world models that
         maintain a compressed history beyond the sliding window.
      2. Online learning from real user interactions. Deploy streaming VideoLLMs in interactive
         settings and learn from implicit user feedback (follow-up questions indicate confusion,
         silence after a proactive alert indicates irrelevance).


                                                 14
      3. Joint perception-decision optimization. Co-train the vision encoder and RL policy so that
         the visual features themselves become RL-optimized for the streaming interaction objective,
         not just for offline image classification.

9   Conclusion
Streaming video understanding is transitioning from supervised fine-tuning to reinforcement learning.
This transition is driven by a fundamental insight: streaming interaction is a sequential decision-
making problem—the model must decide when to speak, what to say, and how to manage its limited
context window—and RL is the natural framework for such problems.
The landscape we survey reveals a field in rapid motion but with significant gaps. On the architecture
side, the emergence of continuous interaction models [76] and encoder-free designs [16] signals a
paradigm shift from turn-based to temporally continuous human-AI collaboration, while omni-modal
systems like Qwen3.5-Omni [70] demonstrate that RL can be applied at scale to both understanding
and generation components. On the methods side, GRPO has become dominant for video under-
standing, with 40+ papers since March 2025, but only four works (MMDuet2, VST, ThinkStream,
R3-Streaming) apply RL directly to streaming settings. On the infrastructure side, frameworks like
EasyVideoR1 and OpenRLHF-M are maturing for offline video RL, but streaming-specific support is
absent. Most critically, no standardized preference data or reward models exist for streaming video
interaction.
The five challenges we identify—temporal credit assignment, reward design, silent-speech exploration,
rollout cost, and data scarcity—are not merely incremental difficulties but fundamental research
problems. Solving them will require new methods at the intersection of RL, video understanding, and
systems engineering. The roadmap we propose provides a concrete path forward, from immediately
actionable experiments to long-term fundamental research.

References
 [1] Arash Ahmadian et al. REINFORCE-leave-one-out for policy gradient methods. arXiv preprint,
     2024.
 [2] Choi Ahn et al. VLM-RLAIF: Tuning large multimodal models for videos using reinforcement
     learning from AI feedback. arXiv preprint arXiv:2402.03746, 2024. ACL 2024 Oral.
 [3] others Ahn. Aligning large multimodal models for videos by iterative self-retrospective DPO.
     arXiv preprint arXiv:2406.11280, 2024. AAAI 2025.
 [4] Alibaba. ROLL: RL optimization for large-scale learning. arXiv preprint arXiv:2506.06122,
     2025.
 [5] Alibaba. ROLL Flash: Accelerating RL with decoupled rollout and training. arXiv preprint
     arXiv:2510.11345, 2025.
 [6] Joya Chen et al. VideoLLM-online: Online video large language model for streaming video.
     arXiv preprint arXiv:2406.11816, 2024. CVPR 2024.
 [7] others Chen. OmniMMI: A comprehensive multi-modal interaction benchmark. arXiv preprint,
     2025.
 [8] others Chen. Thinking in streaming video. arXiv preprint arXiv:2603.12938, 2026.
 [9] Yukang Chen, Wei Huang, Baifeng Shi, et al. Scaling RL to long videos. arXiv preprint
     arXiv:2507.07966, 2025. NeurIPS 2025.
[10] others Dang.    Reinforcing video reasoning with focused thinking.              arXiv preprint
     arXiv:2505.24718, 2025.
[11] Kawin Ethayarajh et al. KTO: Model alignment as prospect theoretic optimization. arXiv
     preprint arXiv:2402.01306, 2024.
[12] others Fan. OVO-Bench: How far is your video-LLM from online video understanding? arXiv
     preprint arXiv:2501.05510, 2025. CVPR 2025.
[13] Kaituo Feng et al. Video-R1: Reinforcing video reasoning in MLLMs. arXiv preprint
     arXiv:2503.21776, 2025.


                                                 15
[14] Lytton Feng et al. Multimodal agentic RL training pipeline acceleration, 2026. Unpublished
     preliminary results.
[15] Zhao Gao et al. RollPacker: Accelerating RL with tail batching and elastic parallelism. arXiv
     preprint arXiv:2509.21009, 2025.
[16] Google DeepMind. Gemma 4: Byte for byte, the most capable open models. https://blog.g
     oogle/innovation-and-ai/technology/developers-tools/gemma-4/, 2026. Model
     card and blog post, June 2026. No formal arxiv report available.
[17] Google DeepMind. Project astra. https://deepmind.google/models/project-astra/,
     2026. Universal AI assistant with real-time multimodal understanding.
[18] Ant Group and Tsinghua IIIS. AReaL: A large-scale asynchronous reinforcement learning
     system for language reasoning. arXiv preprint arXiv:2505.24298, 2025. NeurIPS 2025.
[19] Huankang Guan et al. Video streaming thinking: VideoLLMs can watch and think simultane-
     ously. arXiv preprint arXiv:2603.12262, 2026.
[20] Yongqi He et al. Dispider: A decoupled framework for streaming video understanding. arXiv
     preprint arXiv:2501.03218, 2025. CVPR 2025.
[21] Jian Hu et al. OpenRLHF: An easy-to-use, scalable and high-performance RLHF framework.
     arXiv preprint arXiv:2405.11143, 2024. EMNLP 2025.
[22] Luke J. Huang, Zhuoyang Zhang, Qinghao Hu, Shang Yang, and Song Han. Stable asynchrony:
     Variance controlled policy optimization for async RL. arXiv preprint arXiv:2602.17616, 2026.
     ICML 2026.
[23] others Jiang. VIDEOP2R: Video understanding from perception to reasoning. arXiv preprint
     arXiv:2511.11113, 2025.
[24] others Jin. VideoCuRL: Video curriculum reinforcement learning with orthogonal difficulty
     decomposition. arXiv preprint arXiv:2601.00887, 2025.
[25] Kulkarni and Fazli. AVATAR: Reinforcement learning to see, hear, and reason over video. arXiv
     preprint arXiv:2508.03100, 2025.
[26] Kunchang Li et al. VideoChat: Chat-centric video understanding.               arXiv preprint
     arXiv:2305.06355, 2023.
[27] Lei Li et al. Silkie: Preference distillation for large visual language models. arXiv preprint
     arXiv:2312.10665, 2023.
[28] others Li. Reinforcement learning tuning for VideoLLMs: Reward design and data efficiency.
     arXiv preprint arXiv:2506.01908, 2025.
[29] others Li. Temporal preference optimization for long-form video understanding. arXiv preprint
     arXiv:2501.13919, 2025.
[30] Bin Lin et al. Video-LLaVA: Learning united visual representation by alignment before
     projection. arXiv preprint arXiv:2311.10122, 2023.
[31] Junming Lin et al. StreamingBench: Assessing the gap for MLLMs to achieve streaming video
     understanding. arXiv preprint arXiv:2411.03628, 2024.
[32] Yuanxin Lin et al. StreamBridge: Bridging offline and streaming video understanding. arXiv
     preprint arXiv:2505.05467, 2025.
[33] Jinming Liu, Jianguo Huang, Zhaoyang Jia, Jiahao Li, Xiaoyi Zhang, Zongyu Guo, Bin Li,
     Wenjun Zeng, Yan Lu, and Xin Jin. R3-Streaming: An efficient streaming video understanding
     framework with agentic control. arXiv preprint arXiv:2605.17921, 2026.
[34] Yuxuan Liu et al. MMDuet2: Enhancing proactive interaction of video MLLMs with multi-turn
     reinforcement learning. arXiv preprint arXiv:2512.06810, 2025.
[35] Xudong Lu, Yang Bo, Jinpeng Chen, Shuhan Li, Xintong Guo, Huankang Guan, Fang Liu,
     Dunyuan Xu, Peiwen Sun, Heyang Sun, Rui Liu, and Hongsheng Li. AURA: Always-on
     understanding and real-time assistance via video streams. arXiv preprint arXiv:2604.04184,
     2026.
[36] Yuxin Ma et al. LiveCC: Learning to narrate streaming videos in real time. arXiv preprint
     arXiv:2504.16030, 2025. CVPR 2025.


                                                16
[37] Yu Meng et al. SimPO: Simple preference optimization with a reference-free reward. arXiv
     preprint arXiv:2405.14734, 2024.
[38] others. DistTrain: Addressing model and data heterogeneity with disaggregated training for
     MLLMs. arXiv preprint arXiv:2408.04275, 2024. ACM SIGCOMM 2025.
[39] others. Flash-VStream: Memory-based real-time understanding for long video streams. arXiv
     preprint arXiv:2406.08085, 2024.
[40] others. InternLM-XComposer2.5-OmniLive: A comprehensive multimodal system for long-
     term streaming video and audio interactions. arXiv preprint arXiv:2412.09596, 2024.
[41] others. Optimus: Accelerating large-scale multi-modal LLM training by bubble exploitation.
     arXiv preprint arXiv:2408.03505, 2024. USENIX ATC 2025.
[42] others. RLHFuse: Efficient RLHF training with inter- and intra-stage fusion. arXiv preprint
     arXiv:2409.13221, 2024.
[43] others. VideoSAVi: Self-aligned video language models without human supervision. arXiv
     preprint arXiv:2412.00624, 2024.
[44] others. VITA: Towards open-source interactive omni multimodal LLM. arXiv preprint
     arXiv:2408.05211, 2024. NeurIPS 2025.
[45] others. ChronoForge-RL: Chronological forging through reinforcement learning for enhanced
     video understanding. arXiv preprint arXiv:2509.15800, 2025.
[46] others. DeepVideo-R1: Video reinforcement fine-tuning via difficulty-aware regressive GRPO.
     arXiv preprint arXiv:2506.07464, 2025.
[47] others. DIP: Efficient large multimodal model training with dynamic interleaved pipeline. arXiv
     preprint arXiv:2504.14145, 2025. ASPLOS 2026.
[48] others. GRPO-CARE: Consistency-aware reinforcement learning for multimodal reasoning.
     arXiv preprint arXiv:2506.16141, 2025.
[49] others. MiniCPM-o 4.5: End-to-end omni-modal LLM for full-duplex live streaming. arXiv
     preprint, 2025.
[50] others. Omni-Reward: Towards generalist omni-modal reward modeling with free-form prefer-
     ences. arXiv preprint arXiv:2510.23451, 2025.
[51] others. RhymeRL: Exploiting rollout similarity for speculative acceleration. arXiv preprint
     arXiv:2508.18588, 2025.
[52] others. RollMux: Phase-level multiplexing for disaggregated RL post-training. arXiv preprint
     arXiv:2512.11306, 2025.
[53] others. Self-alignment of large video language models with refined regularized preference
     optimization. arXiv preprint arXiv:2504.12083, 2025. NeurIPS 2025.
[54] others. StreamAgent: Anticipatory agent for proactive streaming video understanding. arXiv
     preprint arXiv:2508.01875, 2025.
[55] others. StreamForest: Persistent event memory forest for streaming video understanding. arXiv
     preprint arXiv:2509.24871, 2025. NeurIPS 2025 Spotlight.
[56] others. StreamMem: Streaming KV cache compression for video understanding. arXiv preprint
     arXiv:2508.15717, 2025.
[57] others. Streamo: End-to-end streaming video language model. arXiv preprint arXiv:2512.21334,
     2025.
[58] others. VideoRewardBench: Comprehensive evaluation of multimodal reward models for video
     understanding. arXiv preprint arXiv:2509.00484, 2025.
[59] others. BubbleSpec: Proactive rollout pre-generation in pipeline bubbles. arXiv preprint
     arXiv:2605.08862, 2026.
[60] others. EasyVideoR1: Easier RL for video understanding. arXiv preprint arXiv:2604.16893,
     2026.
[61] others. Omni-RRM: Advancing omni reward modeling via automatic rubric-grounded prefer-
     ence synthesis. arXiv preprint arXiv:2602.00846, 2026.


                                                17
[62] others. OmniVideo-R1: Reinforcing audio-visual reasoning with query intention and modality
     attention. arXiv preprint arXiv:2602.05847, 2026.
[63] others. Shadow mask distillation: Compressing KV cache in RL post-training. arXiv preprint
     arXiv:2605.06850, 2026.
[64] others. Sparse-RL: Sparsity-aware reinforcement learning for efficient KV cache management.
     arXiv preprint arXiv:2601.10079, 2026.
[65] others. STRIDE: Structured sequence prediction for proactive streaming video understanding.
     arXiv preprint arXiv:2603.27593, 2026.
[66] others. Video understanding reward modeling: A robust benchmark and performant reward
     models. arXiv preprint arXiv:2605.07872, 2026.
[67] Long Ouyang, Jeffrey Wu, Xu Jiang, et al. Training language models to follow instructions
     with human feedback. Advances in Neural Information Processing Systems, 2022.
[68] Alexandre Piche, Ehsan Kamalloo, Dzmitry Bahdanau, et al. PipelineRL: Concurrent data
     generation and training with in-flight weight updates. arXiv preprint arXiv:2509.19128, 2025.
[69] Penghui Qi et al. Zero bubble pipeline parallelism. arXiv preprint arXiv:2401.10241, 2024.
     ICLR 2024.
[70] Qwen Team. Qwen3.5-Omni technical report. arXiv preprint arXiv:2604.15804, 2026.
[71] Rafael Rafailov, Archit Sharma, Eric Mitchell, et al. Direct preference optimization: Your
     language model is secretly a reward model. Advances in Neural Information Processing Systems,
     2023.
[72] Zhihong Shao et al. DeepSeekMath: Pushing the limits of mathematical reasoning in open
     language models. arXiv preprint arXiv:2402.03300, 2024.
[73] Guangming Sheng et al. HybridFlow: A flexible and efficient RLHF framework. arXiv preprint
     arXiv:2409.19256, 2024. EuroSys 2025.
[74] Guangming Sheng et al. Laminar: Fully decoupled RL architecture with dynamic repack. arXiv
     preprint arXiv:2510.12633, 2025. EuroSys 2026.
[75] Zhiqing Sun et al. Aligning large multimodal models with factually augmented RLHF. arXiv
     preprint arXiv:2309.14525, 2023.
[76] Thinking Machines Lab. Interaction models. https://thinkingmachines.ai/blog/int
     eraction-models/, 2026. Blog post, May 2026.
[77] others Wu. LlamaRL: A fully distributed asynchronous RL framework. arXiv preprint
     arXiv:2505.24034, 2025. Meta AI.
[78] UCSD WukLab. Beat the long tail: Distribution-aware speculative decoding for RL. arXiv
     preprint arXiv:2511.13841, 2025.
[79] Guangxuan Xiao, Yuandong Tian, Beidi Chen, Song Han, and Mike Lewis. Efficient streaming
     language models with attention sinks. arXiv preprint arXiv:2309.17453, 2023. ICLR 2024.
[80] Xiaohongshu RED AI Infra. Relax: Asynchronous RL post-training framework for omni-
     modal model alignment. https://github.com/redai-infra/Relax, 2025. Supports
     GRPO/GSPO/SAPO with SGLang inference and Megatron-LM training.
[81] Kaizhuo Yan et al. OPPO: Accelerating PPO-based RLHF via pipeline overlap. arXiv preprint
     arXiv:2509.25762, 2025.
[82] Tianyu Yu et al. RLHF-V: Towards trustworthy MLLMs via behavior alignment from fine-
     grained correctional human feedback. arXiv preprint arXiv:2312.00849, 2024.
[83] others Zhang. LLaVA-Hound-DPO: Direct preference optimization of video large multimodal
     models from language model reward. arXiv preprint arXiv:2404.01258, 2024.
[84] Yuanhan Zhang et al. LLaVA-NeXT: A strong zero-shot video understanding model. Blog post,
     2024.
[85] others Zhao. R1-Omni: Explainable omni-multimodal emotion recognition with reinforcement
     learning. arXiv preprint arXiv:2503.05379, 2025.




                                               18
