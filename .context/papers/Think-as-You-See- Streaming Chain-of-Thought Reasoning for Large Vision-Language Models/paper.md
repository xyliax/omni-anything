                                                 Think-as-You-See: Streaming Chain-of-Thought Reasoning for Large
                                                                      Vision-Language Models

                                                               Jialiang Zhang1,2 * Junlong Tong1,3 * Junyan Lin1,4 * Hao Wu1
                                                                         Yirong Sun1 Yunpu Ma5 Xiaoyu Shen1,6 †
                                             1
                                               Institute of Digital Twin, Eastern Institute of Technology, Ningbo 2 Ocean University of China
                                                          3
                                                            Shanghai Jiao Tong University 4 The Hong Kong Polytechnic University
                                                                      5
                                                                        Munich Center for Machine Learning, LMU Munich




arXiv:2603.02872v2 [cs.CV] 6 Mar 2026
                                                            6
                                                              Ningbo Key Laboratory of Spatial Intelligence and Digital Derivative
                                                                          zhangjia liang@foxmail.com        xyshen@eitech.edu.cn



                                                                    Abstract                               Batch CoT (See Then Think)
                                                                                                                                                        <think>Let’s analyze the video. The whole video shows the
                                                                                                                                                        preparation steps for making Naan bread: shaping dough, and
                                                                                                                                                        wrapping it in plastic to keep it moist.</think>
                                        Large Vision-Language Models (LVLMs) have made signif-                                                          <answer>The images depict Naan preparation: dough shaping, and
                                                                                                                                                        wrapping for moisture — all essential for achieving soft, well-
                                        icant strides in video reasoning, yet most existing systems                                                     prepared Naan bread.</answer>

                                        rely on a batch inference paradigm that processes the en-                      Wait to Think                                                 Delay

                                        tire video before reasoning begins. This “wait-and-see”            Naive Streaming (Interleaved See–Then–Think)
                                        approach neglects the inherently streaming nature of real-                           <think>A person                      <think>A
                                                                                                                                                                                               <answer>Making naan
                                                                                                                             is stirring green                    person's hand
                                        world video, introducing substantial latency and exacerbat-                          leafy vegetables in
                                                                                                                             a pot. Vegetables
                                                                                                                                                                  kneaded the                  bread: cooking spinach,
                                                                                                                                                                                               kneading dough, and
                                                                                                                                                                  dough sprinkled
                                        ing temporal drift. In this paper, we propose Think-as-You-                          look very
                                                                                                                             smooth.</think>
                                                                                                                                                                  with flour.                  moisturizing.</answer>
                                                                                                                                                                  </think>
                                        See (TaYS), a framework that shifts LVLMs toward a stream-           Wait to Think                                                           Delay
                                        ing reasoning paradigm, enabling continuous, incremental           Parallel Streaming (Think While Seeing)
                                        inference synchronized with the visual stream. We introduce                                                                          Delay

                                        three key innovations: (1) a streaming attention mask to                                                                                             <answer>Making naan
                                                                                                                                                                                             bread: cooking spinach,
                                        enforce temporal causality; (2) a decoupled positional en-                                                                                           kneading dough, and
                                                                                                                                                                                             moisturizing.</answer>
                                        coding strategy to resolve cross-modal index conflicts; and           Wait to Think
                                                                                                                                 <think>A person is stirring
                                                                                                                                                                ···
                                                                                                                                                                      <think>A person's hand
                                                                                                                                 green leafy vegetables in a          kneaded the dough sprinkled
                                        (3) a parallel dual KV-cache mechanism that decouples vi-                                pot.</think>                         with flour.</think>

                                        sual encoding from reasoning generation, enabling concur-
                                        rent frame ingestion and token decoding. Empirical evalua-        Figure 1. Conventional LVLM reasoning adheres to the batch
                                        tions on the VideoEspresso benchmark using the Qwen2.5-           thinking paradigm, deferring inference until the entire input is re-
                                        VL family demonstrate that TaYS improves reasoning ac-            ceived. This approach often leads to high latency and uneven at-
                                        curacy by 2.9%, reduces Time-to-First-Token (TTFT) from           tention allocation across inputs. In contrast, our proposed stream-
                                        10.6s to near-zero, and cuts reasoning-event deviation by         ing thinking paradigm enables LVLMs to reason concurrently with
                                                                                                          input reception, thereby reducing latency and ensuring consistency
                                        55%. Our results suggest that aligning LVLM reasoning
                                                                                                          between attention and input order.
                                        with the streaming nature of video is a vital step toward
                                        responsive, real-time multimodal intelligence. The code is
                                        available at this repository.
                                                                                                          spite these advancements, a pervasive bottleneck remains:
                                                                                                          the vast majority of LVLM-based video reasoning sys-
                                                                                                          tems are anchored to a batch inference paradigm where
                                        1. Introduction                                                   the model requires the full video to be available offline be-
                                        Large Vision-Language Models (LVLMs) have recently                fore processing begins [7, 42]. Under this “wait-and-see”
                                        achieved remarkable milestones in multimodal reason-              paradigm, both the information density and the computa-
                                        ing [30, 60], as demonstrated by state-of-the-art systems         tional complexity scale directly with video length, mak-
                                        such as GPT-4o [28], Gemini [12] and Qwen-VL [2]. De-             ing accurate and coherent interpretation increasingly diffi-
                                                                                                          cult [16, 27, 31, 53, 55].
                                          * Equal contribution.   †Corresponding Author.                     Current research attempts to mitigate this issue using


                                                                                                      1
Chain-of-Thought (CoT) reasoning [17, 19, 23, 62, 65]                 43.7% win rate in human-aligned GPT-5 evaluations. Crit-
paired with auxiliary modules for explicit frame referenc-            ically, TaYS reduces the Time-to-First-Token (TTFT) from
ing [1, 18, 21, 63]. By grounding predictions in specific             10.6s in batch mode to nearly zero, while improving tempo-
keyframes and reasoning traces, these methods enhance                 ral grounding by reducing reasoning-event deviation from
both interpretability and accuracy. However, they are still           1.52s to 0.69s. These results demonstrate that aligning
restricted to the same batch inference paradigm. As the tem-          LVLM reasoning with the streaming nature of video is not
poral window of the input video expands, the delay between            only biologically intuitive but also a practical necessity for
a visual event and the model’s corresponding reasoning step           the next generation of real-time AI applications.
grows proportionally [26, 36]. This latency accumulation
often leads to “temporal drift”, where the model loses track          Contributions. Our contributions are fourfold:
of early cues, resulting in significant hallucinations and a
                                                                      • We introduce a principled streaming reasoning paradigm
loss of contextual coherence [10, 51, 61].
                                                                        for LVLMs, enabling incremental, temporally grounded
    This batch-processing assumption is increasingly at odds            inference aligned with unfolding visual evidence.
with the demands of the real world. In domains such                   • We design a cohesive training and inference architec-
as robotics teleoperation, autonomous driving, and live                 ture that operationalizes streaming reasoning, combin-
surveillance, video is not a static file but an evolving                ing causal masking, decoupled positional encoding, and
stream [50]. Human cognition naturally does not wait                    a parallel dual-cache mechanism.
for a sequence to end before processing; rather, we up-               • We conduct comprehensive empirical evaluations on
date our mental models incrementally as new evidence un-                streaming video reasoning tasks, demonstrating improved
folds [20, 45]. Bridging this gap requires a paradigm shift:            reasoning quality and significantly enhanced responsive-
models must transition from post-hoc analysis to active,                ness compared to batch and interleaved baselines.
concurrent understanding [48].
    Motivated by this streaming characteristics of video, we          2. Related Work
propose Think-as-You-See (TaYS), a unified framework
that equips LVLMs with streaming video CoT capabilities.              Multimodal Chain-of-Thought Reasoning. Multimodal
In this framework, reasoning is not a terminal step but a             reasoning enables LVLMs to integrate visual and textual
continuous process that evolves in tandem with the visual             information for complex decision making. Existing ap-
stream. This approach ensures that inference trajectories             proaches generally fall into two paradigms. The first, text-
are progressively refined, minimizing cognitive lag and en-           centric reasoning, converts visual inputs into captions or
suring that reasoning is always synchronized with the most            symbolic descriptions, enabling subsequent linguistic infer-
relevant visual context.                                              ence [19, 24, 25, 52, 63, 65]. While effective for inter-
    A naive implementation that supports this framework is            pretability, this pipeline assumes full input availability be-
interleaved streaming where the model alternatingly pro-              fore reasoning, leading to high latency and weak temporal
cesses a video segment and generates a corresponding rea-             grounding [36].
soning trace [50]. This implementation, however, is funda-               The second paradigm, interleaved multimodal reason-
mentally limited by its sequential nature. This “blocking”            ing, alternates visual and textual tokens to promote more
mechanism forces the model to pause visual ingestion un-              structured cross-modal interaction [1, 11, 17, 18, 21, 23, 47,
til token generation is complete, creating a computational            62]. Although this improves transparency and causal inter-
bottleneck that contradicts the fluid nature of live video this       pretability, it typically relies on sequential processing and
implementation [32, 49]. To overcome this, TaYS harmo-                explicit intermediate generation, which increases inference
nizes stream-aligned training with true parallel inference via        latency and computational overhead.
three key innovations: (1) a streaming attention mask to en-             Recent works also explore efficiency-oriented designs,
force temporal causality, (2) a decoupled positional encod-           such as adaptive reasoning depth [14, 15, 34, 35, 54], com-
ing strategy that independently indexes visual and reasoning          pact cot tokens [38, 44, 56, 64]. However, these studies
tokens to avoid cross-modal index conflicts, and (3) a paral-         primarily optimize computation under offline settings, and
lel dual KV-cache mechanism that decouples visual encod-              do not explicitly address temporally grounded, low-latency
ing from reasoning generation, enabling concurrent frame              reasoning over streaming inputs.
ingestion and token decoding.
    We instantiate TaYS on the Qwen2.5-VL family [3] and              Streaming and Memory-Based Video Understanding.
evaluate its efficacy across tasks requiring complex event            The demand for real-time multimodal systems has stim-
dynamics and causal reasoning. On the extended VideoE-                ulated research on streaming video understanding, where
spresso [21] benchmark, TaYS improves reasoning accu-                 models process frames incrementally instead of in batch
racy by +2.9% over batch CoT baselines and achieves a                 mode [6, 32, 40, 48]. Representative efforts focus on


                                                                  2
streaming captioning, multi-round QA, and conversational              where Enc(V) encodes the complete frame sequence
agents [5, 9, 13, 33, 41, 57–59]. While these approaches              {F1 , . . . , FT }, and yi denotes the i-th reasoning token.
improve temporal consistency and enable online interac-               Consequently, Offline Video CoT optimizes the joint prob-
tion, they often emphasize description or response conti-             ability over the entire sequence:
nuity rather than explicit, stepwise reasoning aligned with
evolving visual evidence.                                                                                N
                                                                                                         Y
    Another line of work leverages memory mechanisms or                         max Pθ (Y | V) =               Pθ (yi | V, y<i ),       (2)
                                                                                  θ
temporal compression to maintain long-context represen-                                                  i=1

tations efficiently. [4, 22, 43] By aggregating or consoli-
dating historical features, these methods reduce computa-             which necessitates full video observation prior to the onset
tional cost but may sacrifice fine-grained temporal align-            of generation.
ment and incremental interpretability. [29, 39] In contrast,             Streaming Video CoT. Conversely, Streaming Video
our formulation does not compress or abstract away tem-               CoT performs incremental reasoning as frames arrive. At
poral structure; instead, it explicitly synchronizes reasoning        any time step t, only the partial frame sequence V≤t =
generation with frame-level updates through causal mask-              {F1 , . . . , Ft } is observable. The model generates reason-
ing, decoupled positional encoding, and parallel cache man-           ing tokens conditioned on this partial visual context and the
agement.                                                              prior reasoning states:
    Overall, existing works either assume offline reasoning
                                                                                 hti = Decoder y<i
                                                                                                t
                                                                                                                   
or prioritize temporal summarization over progressive infer-                                       ; Enc(V≤t ), C<t ,
                                                                                                                                        (3)
ence. Our TaYS framework complements these directions                            ŷit ∼ Pθ (yit | V≤t , y<i
                                                                                                         t
                                                                                                            , C<t ).
by focusing on true streaming reasoning, where percep-
tion and reasoning evolve concurrently under strict tempo-            In contrast to Eq. 1, the model is prohibited from access-
ral causality, enabling low-latency and temporally grounded           ing unseen future frames {Ft+1 , . . . , FT }, enforcing a strict
video understanding.                                                  causal constraint on both visual and linguistic modalities.
                                                                      This paradigm optimizes the cumulative probability up to
3. Methodology                                                        time t:

This section presents TaYS, a supervised fine-tuning frame-                                        Nt
                                                                                                   Y
work that integrates streaming video CoT generation with                max Pθ (Y≤t | V≤t ) =            Pθ (yit | V≤t , y<i
                                                                                                                          t
                                                                                                                             , C<t ),   (4)
                                                                          θ
streaming training and inference mechanisms. Its objective                                         i=1
is to adapt batch-oriented Large Vision-Language Models
to the streaming thinking paradigm.                                   where Nt denotes the number of reasoning tokens generated
                                                                      up to time t.
3.1. Task Definition and Preliminaries                                   Architecturally, Streaming Video CoT updates its rea-
Streaming Video CoT demands that a model continuously                 soning states concurrently with incoming frames, whereas
process a video stream, performing temporal reasoning on              Offline Video CoT encodes the entire video before reason-
queries regarding previously observed visual content at ar-           ing commences. Notably, Offline Video CoT can be viewed
bitrary time steps. In this section, we formalize this task and       as a degenerate case of Streaming Video CoT, wherein all
highlight its fundamental distinctions from the conventional          reasoning is deferred until the video stream terminates.
offline paradigm.
                                                                      Design Principles. To facilitate real-time reasoning,
Streaming Video CoT vs. Offline Video CoT. Formally,                  Streaming Video CoT leverages the causal structure of LLM
let a video stream be represented as a sequence of visual             decoders to balance efficiency and accuracy while min-
frames V = {Ft | 1 ≤ t ≤ T }, and let C<t denote the                  imizing redundant computation. During streaming, KV-
accumulated multimodal context prior to time t (e.g., his-            Caches are incrementally stored and reused as contextual
torical textual or visual reasoning states).                          memory, enabling state updates without re-encoding histor-
    Offline Video CoT. In the offline setting, the model as-          ical frames. A causal attention mask restricts token access
sumes global access to all frames in V before generating              to future information, ensuring that each video token at-
any reasoning tokens. At the final time step t = T , the              tends exclusively to past visual inputs and prior reasoning
reasoning process is formulated as:                                   states. This architecture effectively disentangles temporal
                                                                     visual processing from linguistic reasoning, achieving ef-
                hi = Decoder y<i ; Enc(V) ,                           ficient and temporally consistent inference across dynamic
                                                         (1)
                ŷi ∼ Pθ (yi | V, y<i ),                              video streams.


                                                                  3
 Step1: Frame ID Alignment                                                     Structured Trajectory Construction. Each aligned
                                                                               keyframe Ft is associated with a reasoning sentence Rt
      Video            key frames          Timestamps
                                                               1               and visual evidence Et . To construct structured reasoning
                                           Alignment
                                                                               trajectories, we prompt GPT-4o [28] to generate triplets
                                           locate keyframes
                                           timestamps                          (Qt , Rt , At ) representing the temporally grounded ques-
                                                                               tion, reasoning step, and answer derived from the annotated
   Calibrate keyframe IDs
                                          Resample frames                      content. This enforces frame-level incremental reasoning
   to match resampled FPS       3                              2               and yields temporally segmented reasoning units across the
                                          initial FPS to 2
                                                                               video.
 Step2: Quality Assurance & Evaluation

 LLM-based Rewirite 1                Quality Assurance         2               Quality Control. To ensure semantic coherence and tem-
 QRA triplets generation             Consistency Score                         poral consistency, we compute an alignment score between
                                                                               each question and its corresponding reasoning sentence:
 Final Packaging
                            4        Temporal Verification 3
 Insert <EOT> and                                                                                                      vQ · v R
 construct CoT trajectory            Temporal & Semantic Filtering                         consistency(Qt , Rt ) =                ,          (6)
                                                                                                                      ∥vQ ∥ ∥vR ∥
Figure 2. Overview of the two-step process for generating Stream-                 where vQ and vR are embedding vectors obtained from
ing Video CoT. Step 1 Adjust the frame ID while maintaining                    the BGE-M3 model [8]. Samples with low semantic align-
frame caption alignment. Step 2 Generate a progressive frame                   ment or temporal inconsistency are discarded. The remain-
aware trajectory using the original annotations.                               ing instances form high-quality streaming reasoning trajec-
                                                                               tories.
3.2. Streaming Video CoT Generation                                               Finally, sentence-level boundary tokens <EOT> are in-
                                                                               serted to delimit minimal reasoning units, encouraging the
To enable temporally grounded incremental reasoning, we                        model to generate causally ordered and frame-consistent
construct a streaming-style Video CoT dataset that departs                     outputs conditioned only on preceding visual observations.
from conventional batch reasoning trajectories, which as-
sume full-video access and overlook progressive reasoning                      3.3. Naive Streaming Paradigm
behavior. Our construction is based on the training split
                                                                               A straightforward way to emulate streaming behavior is to
of V IDEO E SPRESSO, which contains temporally coherent
                                                                               interleave video and reasoning tokens during training. Con-
videos annotated with keyframe-level descriptions captur-
                                                                               cretely, each frame Ft is immediately followed by its associ-
ing causal and logical transitions. These keyframes serve
                                                                               ated reasoning segment Rt , forming an alternating sequence
as semantic anchors for extracting frame-aligned reason-
                                                                               {F1 , R1 , F2 , R2 , . . . , FT , RT }. All visual and textual em-
ing trajectories under streaming constraints. The overall
                                                                               beddings are concatenated into a single causal token stream
pipeline is illustrated in Figure 2, with additional details
                                                                               and processed autoregressively.
provided in Appendix A.
                                                                                  This strict interleaving imposes a serialized dependency
                                                                               between perception and reasoning. Since all tokens share
Frame ID Alignment. To ensure strict temporal align-                           a single causal attention space, new visual tokens cannot
ment between visual inputs and reasoning units, we adopt                       be encoded until the preceding reasoning tokens are gener-
timestamp-based resampling instead of uniform frame sam-                       ated, and reasoning cannot proceed until visual tokens are
pling. All videos are resampled to 2 FPS. For each target                      appended. Such coupling creates a computational bottle-
sampling timestamp τt′′ = 0.5(t′ − 1) seconds, the selected                    neck and prevents concurrent updates across modalities.
frame Ft′ is defined as:
                                                                                  Although this design superficially resembles a “thinking-
       (                                                                       while-watching” process, it tightly entangles perception and
        Fk , if τt′′ ∈ [τkstart , τkend ]&Fk is a keyframe,                    reasoning in a way that deviates from the pretraining distri-
 Ft′ =                                                               (5)       bution of LVLMs, where visual encoding and textual decod-
        arg minFt |τt − 0.5(t′ − 1)|, otherwise.
                                                                               ing are typically factorized. As illustrated in Figure 3(c),
   where {τt }Tt=1 denote original frame timestamps. This                      this paradigm therefore suffers from reduced efficiency and
strategy preserves annotated moments while maintaining                         limited scalability in long streaming scenarios.
temporal regularity. After resampling, frame indices are re-
                                                                               3.4. Parallel Streaming Paradigm
normalized and clips are truncated to the model’s maximum
input length, ensuring consistency among visual frames,                        To overcome the intrinsic serialization bottleneck of naive
timestamps, and textual annotations.                                           interleaving strategies, we introduce a parallel streaming


                                                                           4
 (a) Parallel KV Caches for Streaming                Q: How to make vegetable bread?                                Information Flow



                                         00:13                 00:14                 00:15                  00:16


  Video Cache                 Visual Tokens          Visual Tokens          Visual Tokens          Visual Tokens                 ···
  KV Cache                           Merge & Split                            Merge & Split                                      ···
  Reasoning Cache              ···               Text Tokens                                 Text Tokens                         ···
 (b) Attention Mask During Training              (c) Information Flow During Inference
                                                                                                                   Input Frame           Mask
 [F1]                                   [R1]      Text
                                                                 [R1]        [R2]       [R3]                       Reasoning Sentence
 [F2]                 Streaming                   stream
 [F3]                   Mask                                                                                         Attend to Input
 [F4]                                             Video                                                              Attend to Context
 [R1]                                   [R2]      stream                                                             Flow Blocking
 [R2]                                   [R3]
                                                                                                             Text stream     Interleaved Paradigm
 [R3]                                   [R4]      Text
                                                                 [R1]        [R2]       [R3]
 [R4]                                             stream                                                     Text stream     Parallel Paradigm
        s s+1 s+2 s+3 t   t+1 t+2 t+3

Figure 3. Overview of the streaming reasoning framework. (a) Parallel video reasoning KV caches enable concurrent visual encoding
and reasoning generation via dynamic merge and split operations. (b) The streaming attention mask enforces causal alignment between
frames and reasoning steps. (c) During inference, parallel information flow reduces attention path length and alleviates sequential blocking
compared with interleaved paradigms.


paradigm termed Think-as-You-See (TaYS). Unlike conven-
tional approaches that treat reasoning as a post-hoc process                            (
dependent on complete visual encoding, TaYS decouples                                    −∞,             i > Nv , j < Nv , j > i − Nv ,
                                                                            M
                                                                            f(i, j) =
perception from reasoning while strictly preserving tempo-                               Mcausal (i, j), otherwise,
ral causality. This architecture enables concurrent execution
of visual ingestion and cognitive inference, bridging the gap                  where Mcausal represents the standard autoregressive
between streaming perception and real-time reasoning.                       mask. The condition j > i−Nv effectively creates a sliding
                                                                            window over the visual tokens relative to the current rea-
                                                                            soning step. This construction ensures that each reasoning
                                                                            token only integrates information from the current temporal
Streaming Attention Mask. In streaming scenarios,                           window, preventing information leakage from future frames
maintaining strict temporal causality is paramount: a rea-                  and ensuring the generated reasoning remains grounded in
soning step at time t must strictly attend to visual evidence               observed reality.
accumulated up to t, remaining agnostic to future frames.
Standard batch attention mechanisms, which globally ex-
                                                                            Streaming Positional Encoding. While masking en-
pose all visual tokens, violate this causal constraint and are
                                                                            forces logical visibility, positional encoding must resolve
unsuitable for streaming inference.
                                                                            index conflicts arising from the concurrent growth of visual
    To address this, we design a streaming-aware attention                  and reasoning streams. Modern Large Vision-Language
mask that enforces fine-grained visibility constraints. Con-                Models (LVLMs) typically employ Rotary Position Embed-
sider a visual sequence of length Nv and a reasoning se-                    dings (RoPE) [46], where relative positional information is
quence of length Nr . For a query token at position i and a                 encoded via rotation matrices. Under standard monolithic
key token at position j, the masked attention matrix M
                                                     f(i, j)                indexing, the attention interaction between reasoning token
is formulated as:                                                           rt and visual token vs is computed as:


                                                                        5
                                                                                                  (t−1)
                                                                    the historical text cache Cr   . We implement this merge
                                                                    operation via pointer-level composition rather than physi-
       (RNv +t qrt )⊤ (Rs kvs ) = q⊤   ⊤
                                   rt R(Nv +t)−s kvs .    (7)       cal tensor concatenation, achieving a zero-copy overhead.
                                                                    Once the reasoning segment Rt is generated, only the text
   In this setup, the reasoning position is offset by the to-
                                                                    cache is updated:
tal visual length Nv . However, in a streaming context
where Nv expands continuously, this indexing introduces                               Cr(t) = Cr(t−1) ∪ Dec(Rt ),
dynamic shifts in relative positions, potentially destabiliz-
ing the model’s temporal perception. To eliminate this in-          while the video cache remains immutable during this
terference, we propose a modality-decoupled positional in-          step. The subsequent split operation restores the modality-
dexing scheme:                                                      specific cache views, preparing the system for the next cy-
                                                                    cle.
              pos(vs ) = s,      pos(rt ) = t.                          This     architecture     establishes     a    recursive
   This assigns independent positional axes for vision and          merge–generate–split loop.        While Cr is engaged in
reasoning. The resulting attention mechanism becomes:               autoregressive token generation, newly arrived frames
                                                                    are independently absorbed into Cv . Consequently, the
            (Rt qrt )⊤ (Rs kvs ) = q⊤   ⊤                           reasoning process is never stalled by visual encoding. Com-
                                    rt Rt−s kvs .         (8)
                                                                    pared to the monolithic cache design in batch or interleaved
   By isolating the positional spaces, this decoupling pre-         paradigms, TaYS’s decoupled cache architecture minimizes
vents index collision and ensures that the relative temporal        critical path latency and enables true parallel streaming,
distance (t − s) remains semantically consistent, preserv-          realizing a system where perception and reasoning evolve
ing stable alignment between reasoning updates and visual           simultaneously.
observations regardless of the growing sequence length.
                                                                    4. Experiments
Attention Pathways. The architectural choices in differ-
                                                                    4.1. Experimental Settings
ent paradigms fundamentally reshape the information flow.
Batch reasoning necessitates encoding the entire video prior        Video Benchmark. We evaluate TaYS on an extended
to decoding, resulting in a long sequential attention path          benchmark protocol derived from V IDEO E SPRESSO, cov-
and high initial latency. Interleaved reasoning alternates          ering temporal, logical, scene, behavioral, and state under-
between frame input and text generation but relies on a             standing. The benchmark includes tasks such as Event Dy-
monolithic cache, creating a sequential dependency that             namics, Causal Analysis, Theme Analysis, and realistic ap-
forces the reasoning process to stall during visual encod-          plications like Cooking Process and Traffic Analysis, form-
ing. In contrast, TaYS restructures the dataflow by sepa-           ing a comprehensive testbed for streaming video reasoning
rating modality-specific memory pathways while enabling             across diverse semantic contexts.
dynamic fusion during decoding. This design substantially
shortens the effective attention path, allowing the model           Models and Baselines. We implement TaYS on
to initiate reasoning immediately upon receiving the first          Qwen2.5-VL-3B/7B-Instruct.        Comparative baselines
frame without waiting for subsequent visual inputs (Fig-            include: (1) Batch w/o Thinking: a supervised model
ure 3(c)).                                                          fine-tuned on direct QA pairs; (2) Batch w/ Thinking:
                                                                    incorporates frame-referenced intermediate reasoning
Parallel KV Cache. The core enabler of TaYS’s concur-               prompts;1 (3) Batch SFT: distilled from CoT-annotated
rency is a dual-cache system that manages visual and textual        data; and (4) Interleaved SFT: a streaming variant al-
states independently. We maintain two modality-specific             ternating frame input and reasoning generation without
caches: a read-heavy video cache Cv and a dynamic text              parallel caching. This setup isolates the benefits of par-
cache Cr .                                                          allel streaming against conventional batch and sequential
   At time step t, the incoming frame Ft is processed by            interleaving paradigms.
the visual encoder and incrementally appended to the video
cache:                                                              Metrics. Evaluation considers both reasoning quality and
                  Cv(t) = Cv(t−1) ∪ Enc(Ft ).                       latency. Objective performance requires the semantic sim-
Crucially, this update is non-blocking and occurs asyn-             ilarity of predictions to exceed a threshold and outperform
chronously with respect to the reasoning process.                   distractors. Subjective performance is ranked by GPT-
   During the decoding phase, attention is computed over            5 [37] based on logical consistency, factual accuracy, and
                                                    (t)
a logical concatenation of the current video cache Cv and             1 Detailed CoT inference prompt is provided in Appendix B.




                                                                6
Table 1. Comparison of reasoning accuracy on the extended V IDEO E SPRESSO benchmark. TaYS consistently achieves competitive or
superior performance while maintaining low latency, demonstrating the effectiveness of the streaming reasoning paradigm. In the table,
bold numbers denote the best results, and underlined numbers indicate the second-best results for each task category.

 Model                 Narr. Event Ingr. Caus. Theme Cont. Infl.                  Role Inter. Behav. Emot. Cook. Traff. Situa. Acc. ↑
                                                             Qwen2.5-VL-3B-Instruct
 Batch w/o thinking    39.39    31.51   25.00   18.92    37.50    24.32   43.90 20.69 29.73 16.67               42.11     38.89     30.77     10.00      27.99
 Batch with thinking   39.39    26.03   28.57   15.68    37.50    40.54   17.07 48.28 29.73 8.33                47.37     61.11     38.46     20.00      28.16
 Batch SFT             48.48    34.25   17.86   17.84    43.75    32.43   39.02 27.59 24.32 8.33                39.47     50.00     46.15     20.00      29.18
 Interleaved SFT       48.48    38.36   25.00   28.65    37.50    29.73   36.59 31.03 35.14 16.67               36.84     55.56     46.15     30.00      33.96
 TaYS                  51.52    36.99   39.29   24.86    46.88    21.62   31.71 20.69 37.84 33.33               44.74     50.00     53.85     20.00      33.45
                                                             Qwen2.5-VL-7B-Instruct
 Batch w/o thinking    54.55    32.88   28.57   14.59    37.50    27.03   41.46 34.48 29.73          16.67      36.84     52.94     46.15     10.00      28.89
 Batch with thinking   42.42    31.51   42.86   23.24    37.50    29.73   29.27 37.93 29.73          25.00      39.47     55.56     38.46     30.00      31.57
 Batch SFT             48.48    26.03   32.14   21.62    43.75    32.43   43.90 31.03 27.03          8.33       39.47     38.89     46.15     20.00      30.38
 Interleaved SFT       57.58    38.36   35.71   24.86    50.00    35.14   48.78 24.14 37.84          16.67      36.84     44.44     46.15     20.00      34.98
 TaYS                  63.64    35.62   28.57   25.95    46.88    35.14   41.46 34.48 51.35          16.67      47.37     66.67     46.15     10.00      36.86



contextual appropriateness. Latency is measured by TTFT                         Q: Using the given video, describe the process and the specific step shown in
(time to first token) and overall delay (total time for reason-                 the text overlay "STEP TWO ASSEMBLE SUSHI ROLL".

ing and response).

4.2. Results on Benchmark
Objective Evaluation Results. Table 1 summarizes ob-
jective results. Explicit CoT prompting enhances base                          Interleaved Streaming
                                                                                <think>The process of making sushi rolls begins with the preparation of
LVLM reasoning, while fine-tuning on temporally aligned                         ingredients and a bamboo mat is used to assemble them.</think>
trajectories yields further gains by aligning reasoning with                    <answer>The process of making sushi rolls begins with the preparation of
                                                                                ingredients, which are laid out on the chef. The specific step shown in "STEP
visual evidence. Streaming-based models outperform all                          TWO ASSEMBLE SUSHI R" is using a bamboo mat to assemble the sushi roll
batch baselines significantly. Notably, the Interleaved                         by spreading rice onto it and rolling it up.</answer>
model achieves slightly higher accuracy than TaYS, suggest-
ing both streaming paradigms effectively capture temporal                      Parallel Streaming
                                                                                <think>The person is preparing ingredients for sushi.</think><think>The
dependencies. However, objective metrics alone may not                          bamboo mat is being used to assemble the sushi roll.</think><think>The
fully reflect reasoning coherence, necessitating further sub-                   rice is placed on top of the seaweed.</think>
                                                                                <answer>The process involves preparing various ingredients such as
jective evaluation.                                                             avocado slices, crab meat salad, cucumber sticks, and other fillings. The
                                                                                specific step described by the text 'STEP TWO: ASSEMBLY SUSHIR ROLL'
                                                                                shows that after spreading rice onto the seaweed using the bamboo mat, the next
Subjective Evaluation Results. GPT-5 ranked model                               action would be assembling the sushi rolls with these prepared
                                                                                ingredients.</answer>
outputs based on overall quality.2 TaYS achieved the
highest normalized win rate of 43.7%, surpassing Batch
(31.4%) and Interleaved (21.7%). TaYS excels in tasks re-                     Figure 4. Case study comparing TaYS with the Interleaved
quiring multi-step temporal reasoning, winning 61.1% of                       paradigm. TaYS produces temporally aligned reasoning, whereas
                                                                              the Interleaved model generates less accurate, fragmented descrip-
Cooking Process samples (vs. 11.1% for Interleaved) and
                                                                              tions.
75.0% of Preparation Steps. As illustrated in Figure 4,
TaYS aligns reasoning tightly with visual evidence, avoid-
ing the fragmented descriptions produced by the Interleaved
model, thereby demonstrating superior temporal grounding                      Figure 5(a), the Batch paradigm suffers from a persistent
in dynamic scenarios.                                                         bottleneck (∼10.6s TTFT). The Interleaved paradigm re-
                                                                              sponds faster but suffers from cumulative delay growth at
4.3. Real-Time Streaming Reasoning Efficiency                                 higher frame rates due to sequential encode–generate de-
                                                                              pendencies.
We evaluate TaYS in real-time streaming scenarios where
frames arrive progressively. As shown in Table 2 and                              In contrast, TaYS achieves near-zero decoder-level
                                                                              TTFT (≈ 10−6 s) under the incremental warm-start setting,
  2 Detailed subjective evaluation prompt is provided in Appendix B.          reflecting minimal decoding latency. Crucially, TaYS main-


                                                                          7
 Table 2. Latency and accuracy comparison across different FPS.                                                                         (a) Temporal Alignment Accuracy (b) Reduced Temporal Variance
                                                                                                                                        1.0                                                                     5
 TaYS achieves the lowest TTFT and delay, demonstrating superior                                                                                                      +11.0%




                                                                                                               Cumulative Probability
                                                                                                                                                             +17.0%




                                                                                                                                                                                        Temporal Distance (s)
 real-time efficiency.                                                                                                                  0.8         +23.5%
                                                                                                                                                                                                                4
                                                                                                                                        0.6                                                                     3
     Method                 Metric FPS=1 FPS=2 FPS=3 FPS=4 FPS=5
                                                                                                                                        0.4                                                                     2
                            TTFT↓ 10.36                  10.48             10.62    10.77        10.93                                  0.2                           TaYS                                      1
     Batch                  Delay↓ 12.05                 13.90             12.93    13.08        13.12                                                                Interleaved
                             Acc↑ 28.33                  29.18             31.23    30.03        31.91                                  0.0                                                                     0
                                                                                                                                              0     1        2        3        4    5
                                                                                                                                                    Temporal Distance (s)                                                 TaYS     Interleaved
                 TTFT↓ 0.0303 0.0295 0.0296 0.0301 0.0298
     Interleaved Delay↓ 12.94 14.19 16.15 18.03 20.13                                                              Figure 6. Temporal distance ∆t distribution. TaYS aligns reason-
                  Acc↑ 33.95 33.96 33.11 31.91 30.55                                                               ing more closely with keyframes, achieving higher precision than
                            TTFT↓ 1e-6                   9.2e-7 9.3e-7 1.06e-6 9.6e-7                              the interleaved baseline.
     TaYS                   Delay↓ 12.06                 12.19 12.32 12.30 12.31
                             Acc↑ 31.74                  33.45 36.01 35.49 34.06                                                            (a) Temporal Coherence 3B                                           (b) Temporal Coherence 7B
                                                                                                                                        4
                                                                                                                                                   TaYS                                                              TaYS
                    (a) Latency Trend                                      (b) Latency Breakdown                                        3          Interleaved                                                       Interleaved
                                                         20           14                          TTFT
           10
                                                                                                               Density
                                                                                                  Think                                 2
                                                                      12                          Answer
            8       Batch TTFT                           18
                    Interleaved TTFT                                  10
                                                          Delay (s)
TTFT (s)
            6       TaYS TTFT
                                                         16            8                                                                1
            4
                                       Batch Delay
                                       Interleaved Delay
                                                          Time (s)     6
                                       TaYS Delay        14            4                                                                0
            2                                                                                                                           0.0       0.2    0.4      0.6      0.8      1.0 0.0                         0.2      0.4   0.6   0.8     1.0
                                                                       2                                                                            Semantic Similarity                                               Semantic Similarity
            0                                            12
                1       2         3        4         5                     Batch   Interleaved    TaYS
                                FPS
                                                                                                                   Figure 7. Semantic similarity between consecutive reasoning
 Figure 5. (a) Latency comparison across paradigms. (b) Latency                                                    steps. TaYS maintains a smoother distribution, whereas the inter-
 breakdown of TaYS. Parallel KV Cache design enables the lowest                                                    leaved model exhibits repetitive peaks (high similarity), indicating
 TTFT and stable delay.                                                                                            redundancy.


                                                                                                                   nant or looping descriptions, ensuring sustained distinctive-
 tains a stable end-to-end delay of ∼12s across all frame
                                                                                                                   ness. Conversely, the Interleaved model displays prominent
 rates by parallelizing cache management and reasoning.
                                                                                                                   peaks, reflecting redundant and less adaptive reasoning that
 Accuracy scales robustly with frame rate (peaking at 36.0%
                                                                                                                   struggles to assimilate new events. These results demon-
 for FPS=3), whereas baselines fluctuate. Figure 5(b) con-
                                                                                                                   strate TaYS maintains a coherent, progressive reasoning tra-
 firms TaYS’s compact latency profile, demonstrating its ef-
                                                                                                                   jectory aligned with the video’s temporal structure.
 ficiency and reliability for streaming understanding.

 4.4. Temporal Behavior of Streaming Reasoning                                                                     5. Conclusion
 Fine-Grained Temporal Alignment. We assess whether                                                                Video data naturally arrives as a continuous stream, yet
 reasoning is triggered at correct moments by measuring the                                                        most LVLMs rely on offline batch reasoning, fundamentally
 temporal distance ∆t between reasoning steps and anno-                                                            misaligned with the sequential nature of real-world visual
 tated keyframes. Figure 6 shows TaYS achieves a mean                                                              inputs. We introduce the streaming thinking paradigm,
                                                                                                                   enabling models to reason progressively as frames ar-
 deviation of 0.69s (vs. 1.52s for Interleaved). Addition-
                                                                                                                   rive and refine outputs dynamically. We instantiate this
 ally, 86.0% of TaYS’s reasoning falls within one second of                                                        via Think-as-You-See (TaYS), integrating streaming
 keyframes (vs. 62.4% for Interleaved). The distribution                                                           Chain-of-Thought, stream-aligned training, and parallel
 indicates TaYS effectively concentrates reasoning around                                                          KV-cache architecture. Experiments show TaYS reduces
 event boundaries rather than scattering outputs across irrel-                                                     latency while enhancing reasoning quality by grounding
 evant temporal segments, thereby confirming precise tem-                                                          inferences in immediate visual evidence. By decoupling
 poral grounding and acute event sensitivity.                                                                      perception from reasoning, our approach resolves the
                                                                                                                   trade-off between responsiveness and depth, allowing
                                                                                                                   models to ”think on their feet” without awaiting complete
 Temporal Coherence of Reasoning. We examine seman-                                                                encoding. Analyses highlight controllable and temporally
 tic continuity between consecutive reasoning outputs (Fig-                                                        grounded reasoning, paving the way for responsive, reliable
 ure 7). TaYS exhibits a smooth similarity profile, indicating                                                     real-time video understanding. This work shifts focus from
 reasoning evolves with visual changes. The suppression of                                                         static analysis to dynamic interaction, laying out a foun-
 high-similarity spikes suggests effective avoidance of stag-                                                      dation for embodied intelligence and open-world agents.


                                                                                                           8
                                                                              pages 2318–2335, Bangkok, Thailand, 2024. Association for
                                                                              Computational Linguistics. 4
References                                                                [9] Joya Chen, Ziyun Zeng, Yiqi Lin, Wei Li, Zejun Ma, and
                                                                              Mike Zheng Shou. Livecc: Learning video llm with stream-
[1] Anurag Arnab, Ahmet Iscen, Mathilde Caron, Alireza Fathi,
                                                                              ing speech transcription at scale. In Proceedings of the
    and Cordelia Schmid. Temporal chain of thought: Long-
                                                                              Computer Vision and Pattern Recognition Conference, pages
    video understanding by thinking in frames. arXiv preprint
                                                                              29083–29095, 2025. 3
    arXiv:2507.02001, 2025. 2
                                                                         [10] Qiguang Chen, Libo Qin, Jinhao Liu, Dengyun Peng, Jian-
[2] Shuai Bai, Yuxuan Cai, Ruizhe Chen, Keqin Chen, Xionghui
                                                                              nan Guan, Peng Wang, Mengkang Hu, Yuhang Zhou, Te
    Chen, Zesen Cheng, Lianghao Deng, Wei Ding, Chang Gao,
                                                                              Gao, and Wanxiang Che. Towards reasoning era: A survey of
    Chunjiang Ge, Wenbin Ge, Zhifang Guo, Qidong Huang,
                                                                              long chain-of-thought for reasoning large language models.
    Jie Huang, Fei Huang, Binyuan Hui, Shutong Jiang, Zhao-
                                                                              arXiv preprint arXiv:2503.09567, 2025. 2
    hai Li, Mingsheng Li, Mei Li, Kaixin Li, Zicheng Lin, Jun-
    yang Lin, Xuejing Liu, Jiawei Liu, Chenglong Liu, Yang Liu,          [11] Zihui Cheng, Qiguang Chen, Jin Zhang, Hao Fei, Xiaocheng
    Dayiheng Liu, Shixuan Liu, Dunjie Lu, Ruilin Luo, Chenxu                  Feng, Wanxiang Che, Min Li, and Libo Qin. Comt: A novel
    Lv, Rui Men, Lingchen Meng, Xuancheng Ren, Xingzhang                      benchmark for chain of multi-modal thought on large vision-
    Ren, Sibo Song, Yuchong Sun, Jun Tang, Jianhong Tu, Jian-                 language models. In Proceedings of the AAAI Conference on
    qiang Wan, Peng Wang, Pengfei Wang, Qiuyue Wang, Yux-                     Artificial Intelligence, pages 23678–23686, 2025. 2
    uan Wang, Tianbao Xie, Yiheng Xu, Haiyang Xu, Jin Xu,                [12] Gheorghe Comanici, Eric Bieber, Mike Schaekermann, Ice
    Zhibo Yang, Mingkun Yang, Jianxin Yang, An Yang, Bowen                    Pasupat, Noveen Sachdeva, Inderjit Dhillon, Marcel Blis-
    Yu, Fei Zhang, Hang Zhang, Xi Zhang, Bo Zheng, Humen                      tein, Ori Ram, Dan Zhang, Evan Rosen, et al. Gemini 2.5:
    Zhong, Jingren Zhou, Fan Zhou, Jing Zhou, Yuanzhi Zhu,                    Pushing the frontier with advanced reasoning, multimodality,
    and Ke Zhu. Qwen3-vl technical report, 2025. 1                            long context, and next generation agentic capabilities. arXiv
[3] Shuai Bai, Keqin Chen, Xuejing Liu, Jialin Wang, Wenbin                   preprint arXiv:2507.06261, 2025. 1
    Ge, Sibo Song, Kai Dang, Peng Wang, Shijie Wang, Jun                 [13] Shangzhe Di, Zhelun Yu, Guanghao Zhang, Haoyuan Li,
    Tang, Humen Zhong, Yuanzhi Zhu, Mingkun Yang, Zhao-                       Hao Cheng, Bolin Li, Wanggui He, Fangxun Shu, Hao Jiang,
    hai Li, Jianqiang Wan, Pengfei Wang, Wei Ding, Zheren                     et al. Streaming video question-answering with in-context
    Fu, Yiheng Xu, Jiabo Ye, Xi Zhang, Tianbao Xie, Zesen                     video kv-cache retrieval. In ICLR, 2025. 3
    Cheng, Hang Zhang, Zhibo Yang, Haiyang Xu, and Jun-                  [14] Longwei Ding, Anhao Zhao, Fanghua Ye, Ziyang Chen, and
    yang Lin. Qwen2.5-vl technical report. arXiv preprint                     Xiaoyu Shen. From llms to lrms: Rethinking pruning for
    arXiv:2502.13923, 2025. 2                                                 reasoning-centric models. arXiv preprint arXiv:2601.18091,
[4] Ivana Balažević, Yuge Shi, Pinelopi Papalampidi, Rahmadi                2026. 2
    Chaabouni, Skanda Koppula, and Olivier J. Hénaff. Mem-
                                                                         [15] Yingqi Fan, Anhao Zhao, Jinlan Fu, Junlong Tong, Hui Su,
    ory consolidation enables long-context video understanding.
                                                                              Yijie Pan, Wei Zhang, and Xiaoyu Shen. VisiPruner: Decod-
    In Proceedings of the 41st International Conference on Ma-
                                                                              ing discontinuous cross-modal dynamics for efficient multi-
    chine Learning. JMLR.org, 2024. 3
                                                                              modal LLMs. In Proceedings of the 2025 Conference on
[5] Dibyadip Chatterjee, Edoardo Remelli, Yale Song, Bugra                    Empirical Methods in Natural Language Processing, pages
    Tekin, Abhay Mittal, Bharat Bhatnagar, Necati Cihan Cam-                  18885–18902, Suzhou, China, 2025. Association for Com-
    goz, Shreyas Hampali, Eric Sauser, Shugao Ma, Angela Yao,                 putational Linguistics. 2
    and Fadime Sener. Streaming videollms for real-time proce-
    dural video understanding. In Proceedings of the IEEE/CVF            [16] Yingqi Fan, Junlong Tong, Anhao Zhao, and Xiaoyu Shen.
    International Conference on Computer Vision (ICCV), pages                 What do visual tokens really encode? uncovering sparsity
    22586–22598, 2025. 3                                                      and redundancy in multimodal large language models. arXiv
                                                                              preprint arXiv:2603.00510, 2026. 1
[6] Joya Chen, Zhaoyang Lv, Shiwei Wu, Kevin Qinghong Lin,
    Chenan Song, Difei Gao, Jia-Wei Liu, Ziteng Gao, Dongxing            [17] Hao Fei, Shengqiong Wu, Wei Ji, Hanwang Zhang, Meishan
    Mao, and Mike Zheng Shou. Videollm-online: Online video                   Zhang, Mong-Li Lee, and Wynne Hsu. Video-of-thought:
    large language model for streaming video. In Proceedings of               Step-by-step video reasoning from perception to cognition.
    the IEEE/CVF Conference on Computer Vision and Pattern                    In Proceedings of the 41st International Conference on Ma-
    Recognition, pages 18407–18418, 2024. 2                                   chine Learning, pages 13109–13125. PMLR, 2024. 2
[7] Joya Chen, Zhaoyang Lv, Shiwei Wu, Kevin Qinghong Lin,               [18] Haonan Ge, Yiwei Wang, Kai-Wei Chang, Hang Wu, and
    Chenan Song, Difei Gao, Jia-Wei Liu, Ziteng Gao, Dongxing                 Yujun Cai. Famemind: Frame-interleaved video reasoning
    Mao, and Mike Zheng Shou. Videollm-online: Online video                   via reinforcement learning. arXiv e-prints, pages arXiv–
    large language model for streaming video, 2024. 1                         2509, 2025. 2
[8] Jianlyu Chen, Shitao Xiao, Peitian Zhang, Kun Luo,                   [19] Sara Ghazanfari, Francesco Croce, Nicolas Flammarion,
    Defu Lian, and Zheng Liu.            M3-embedding: Multi-                 Prashanth Krishnamurthy, Farshad Khorrami, and Siddharth
    linguality, multi-functionality, multi-granularity text embed-            Garg. Chain-of-frames: Advancing video understanding in
    dings through self-knowledge distillation. In Findings of                 multimodal llms via frame-aware reasoning. arXiv preprint
    the Association for Computational Linguistics: ACL 2024,                  arXiv:2506.00318, 2025. 2


                                                                     9
[20] Arthur C Graesser, Murray Singer, and Tom Trabasso. Con-                  guage Processing, pages 5971–5984, Miami, Florida, USA,
     structing inferences during narrative text comprehension.                 2024. Association for Computational Linguistics. 1
     Psychological review, 101(3):371, 1994. 2                            [32] Junyan Lin, Junlong Tong, Hao Wu, Jialiang Zhang, Jin-
[21] Songhao Han, Wei Huang, Hairong Shi, Le Zhuo, Xiu Su,                     ming Liu, Xin Jin, and Xiaoyu Shen. Speak while watch-
     Shifeng Zhang, Xu Zhou, Xiaojuan Qi, Yue Liao, and Si                     ing: Unleashing true real-time video understanding capa-
     Liu. Videoespresso: A large-scale chain-of-thought dataset                bility of multimodal large language models. arXiv preprint
     for fine-grained video reasoning via core frame selection. In             arXiv:2601.06843, 2026. 2
     Proceedings of the Computer Vision and Pattern Recognition           [33] Jihao Liu, Zhiding Yu, Shiyi Lan, Shihao Wang, Rongyao
     Conference (CVPR), pages 26181–26191, 2025. 2                             Fang, Jan Kautz, Hongsheng Li, and Jose M Alvare.
[22] Bo He, Hengduo Li, Young Kyun Jang, Menglin Jia, Xue-                     Streamchat: Chatting with streaming video. arXiv preprint
     fei Cao, Ashish Shah, Abhinav Shrivastava, and Ser-Nam                    arXiv:2412.08646, 2024. 3
     Lim. Ma-lmm: Memory-augmented large multimodal model                 [34] Wenjie Liu, Hao Wu, Xin Qiu, Yingqi Fan, Yihan Zhang,
     for long-term video understanding. In Proceedings of the                  Anhao Zhao, Yunpu Ma, and Xiaoyu Shen. Vica: Efficient
     IEEE/CVF Conference on Computer Vision and Pattern                        multimodal llms with vision-only cross-attention. arXiv
     Recognition (CVPR), 2024. 3                                               preprint arXiv:2602.07574, 2026. 2
[23] Vaishnavi Himakunthala, Andy Ouyang, Daniel Rose, Ryan               [35] Jinghui Lu, Haiyang Yu, Siliang Xu, Shiwei Ran, Guozhi
     He, Alex Mei, Yujie Lu, Chinmay Sonar, Michael Saxon,                     Tang, Siqi Wang, Bin Shan, Teng Fu, Hao Feng, Jingqun
     and William Wang. Let’s think frame by frame with VIP:                    Tang, et al. Prolonged reasoning is not all you need:
     A video infilling and prediction dataset for evaluating video             Certainty-based adaptive routing for efficient llm/mllm rea-
     chain-of-thought. In Proceedings of the 2023 Conference on                soning. arXiv preprint arXiv:2505.15154, 2025. 2
     Empirical Methods in Natural Language Processing, pages              [36] Mi Luo, Zihui Xue, Alex Dimakis, and Kristen Grauman.
     204–219, Singapore, 2023. Association for Computational                   When thinking drifts: Evidential grounding for robust video
     Linguistics. 2                                                            reasoning. arXiv preprint arXiv:2510.06077, 2025. 2
[24] Yushi Hu, Hang Hua, Zhengyuan Yang, Weijia Shi, Noah A               [37] OpenAI. Introducing gpt-5. https://openai.com/
     Smith, and Jiebo Luo. Promptcap: Prompt-guided task-                      index/introducing-gpt-5/, 2025. Accessed: 2025-
     aware image captioning. arXiv preprint arXiv:2211.09699,                  11-10. 6
     2022. 2                                                              [38] Yi Peng, Peiyu Wang, Xiaokun Wang, Yichen Wei, Jiangbo
                                                                               Pei, Weijie Qiu, Ai Jian, Yunzhuo Hao, Jiachun Pan, Tianyi-
[25] Yuhang Hu, Zhenyu Yang, Shihan Wang, Shengsheng Qian,
                                                                               dan Xie, et al. Skywork r1v: Pioneering multimodal reason-
     Bin Wen, Fan Yang, Tingting Gao, and Changsheng Xu.
                                                                               ing with chain-of-thought. arXiv preprint arXiv:2504.05599,
     Streamingcot: A dataset for temporal dynamics and multi-
                                                                               2025. 2
     modal chain-of-thought reasoning in streaming videoqa. In
     Proceedings of the 33rd ACM International Conference on              [39] Rui Qian, Xiaoyi Dong, Pan Zhang, Yuhang Zang, Shuan-
     Multimedia, pages 13464–13470, 2025. 2                                    grui Ding, Dahua Lin, and Jiaqi Wang. Streaming long video
                                                                               understanding with large language models. In Advances
[26] Jie Huang, Xuejing Liu, Sibo Song, Ruibing Hou, Hong
                                                                               in Neural Information Processing Systems, pages 119336–
     Chang, Junyang Lin, and Shuai Bai. Revisiting multimodal
                                                                               119360. Curran Associates, Inc., 2024. 3
     positional encoding in vision-language models, 2025. 2
                                                                          [40] Rui Qian, Xiaoyi Dong, Pan Zhang, Yuhang Zang, Shuan-
[27] Xiaohu Huang, Hao Zhou, and Kai Han. PruneVid: Visual                     grui Ding, Dahua Lin, and Jiaqi Wang. Streaming long video
     token pruning for efficient video large language models. In               understanding with large language models. Advances in Neu-
     Findings of the Association for Computational Linguistics:                ral Information Processing Systems, 37:119336–119360,
     ACL 2025, pages 19959–19973, Vienna, Austria, 2025. As-                   2024. 2
     sociation for Computational Linguistics. 1
                                                                          [41] Rui Qian, Shuangrui Ding, Xiaoyi Dong, Pan Zhang, Yuhang
[28] Aaron Hurst, Adam Lerer, Adam P Goucher, Adam Perel-                      Zang, Yuhang Cao, Dahua Lin, and Jiaqi Wang. Dispider:
     man, Aditya Ramesh, Aidan Clark, AJ Ostrow, Akila Weli-                   Enabling video llms with active real-time interaction via dis-
     hinda, Alan Hayes, Alec Radford, et al. Gpt-4o system card.               entangled perception, decision, and reaction. In Proceedings
     arXiv preprint arXiv:2410.21276, 2024. 1, 4                               of the Computer Vision and Pattern Recognition Conference,
[29] Seon-Ho Lee, Jue Wang, Zhikang Zhang, David Fan, and                      pages 24045–24055, 2025. 3
     Xinyu Li. Video token merging for long video understand-             [42] Jiayuan Rao, Haoning Wu, Hao Jiang, Ya Zhang, Yanfeng
     ing. Advances in Neural Information Processing Systems,                   Wang, and Weidi Xie. Towards universal soccer video un-
     37:13851–13871, 2024. 3                                                   derstanding, 2025. 1
[30] Zongxia Li, Xiyang Wu, Hongyang Du, Fuxiao Liu, Huy                  [43] Xiaoqian Shen, Yunyang Xiong, Changsheng Zhao, Lemeng
     Nghiem, and Guangyao Shi. A survey of state of the art large              Wu, Jun Chen, Chenchen Zhu, Zechun Liu, Fanyi Xiao, Bal-
     vision language models: Alignment, benchmark, evaluations                 akrishnan Varadarajan, Florian Bordes, et al. Longvu: Spa-
     and challenges, 2025. 1                                                   tiotemporal adaptive compression for long video-language
[31] Bin Lin, Yang Ye, Bin Zhu, Jiaxi Cui, Munan Ning, Peng Jin,               understanding. arXiv preprint arXiv:2410.17434, 2024. 3
     and Li Yuan. Video-LLaVA: Learning united visual repre-              [44] Xuan Shen, Yizhou Wang, Xiangxi Shi, Yanzhi Wang, Pu
     sentation by alignment before projection. In Proceedings of               Zhao, and Jiuxiang Gu. Efficient reasoning with hidden
     the 2024 Conference on Empirical Methods in Natural Lan-                  thinking. arXiv preprint arXiv:2501.19201, 2025. 2


                                                                     10
[45] Keith Stenning and Michiel Van Lambalgen. Human reason-                  understanding for infinite video streams. arXiv preprint
     ing and cognitive science. MIT Press, 2012. 2                            arXiv:2510.09608, 2025.
[46] Jianlin Su, Murtadha Ahmed, Yu Lu, Shengfeng Pan, Wen               [59] Haolin Yang, Feilong Tang, Lingxiao Zhao, Xiang An, Ming
     Bo, and Yunfeng Liu. Roformer: Enhanced transformer with                 Hu, Huifa Li, Xinlin Zhuang, Yifan Lu, Xiaofeng Zhang,
     rotary position embedding. Neurocomputing, 568:127063,                   Abdalla Swikir, et al. Streamagent: Towards anticipatory
     2024. 5                                                                  agents for streaming video understanding. arXiv preprint
[47] Zhaochen Su, Peng Xia, Hangyu Guo, Zhenhua Liu, Yan Ma,                  arXiv:2508.01875, 2025. 3
     Xiaoye Qu, Jiaqi Liu, Yanshu Li, Kaide Zeng, Zhengyuan              [60] Shukang Yin, Chaoyou Fu, Sirui Zhao, Ke Li, Xing Sun,
     Yang, et al. Thinking with images for multimodal reasoning:              Tong Xu, and Enhong Chen. A survey on multimodal large
     Foundations, methods, and future frontiers. arXiv preprint               language models. National Science Review, 11(12), 2024. 1
     arXiv:2506.23918, 2025. 2                                           [61] Jiacheng Zhang, Yang Jiao, Shaoxiang Chen, Na Zhao,
[48] Junlong Tong, Yingqi Fan, Anhao Zhao, Yunpu Ma, and Xi-                  Zhiyu Tan, Hao Li, and Jingjing Chen. Eventhallusion: Di-
     aoyu Shen. Streamingthinker: Large language models can                   agnosing event hallucinations in video llms. arXiv preprint
     think while reading. arXiv preprint arXiv:2510.17238, 2025.              arXiv:2409.16597, 2024. 2
     2                                                                   [62] Yongheng Zhang, Xu Liu, Ruihan Tao, Qiguang Chen, Hao
[49] Junlong Tong, Jinlan Fu, Zixuan Lin, Yingqi Fan, Anhao                   Fei, Wanxiang Che, and Libo Qin. Vitcot: Video-text in-
     Zhao, Hui Su, and Xiaoyu Shen. Llm as effective streaming                terleaved chain-of-thought for boosting video understanding
     processor: Bridging streaming-batch mismatches with group                in large language models. In Proceedings of the 33rd ACM
     position encoding. In Findings of the Association for Compu-             International Conference on Multimedia, page 5267–5276,
     tational Linguistics: ACL 2025, pages 23497–23517, 2025.                 New York, NY, USA, 2025. Association for Computing Ma-
     2                                                                        chinery. 2
[50] Junlong Tong, Zilong Wang, YuJie Ren, Peiran Yin, Hao               [63] Zhuosheng Zhang, Aston Zhang, Mu Li, Hai Zhao,
     Wu, Wei Zhang, and Xiaoyu Shen. From static inference to                 George Karypis, and Alex Smola. Multimodal chain-of-
     dynamic interaction: Navigating the landscape of streaming               thought reasoning in language models. arXiv preprint
     large language models, 2026. 2                                           arXiv:2302.00923, 2023. 2
[51] Yuxuan Wang, Yueqian Wang, Dongyan Zhao, Cihang Xie,                [64] Anhao Zhao, Ziyang Chen, Junlong Tong, Yingqi Fan,
     and Zilong Zheng. Videohallucer: Evaluating intrinsic                    Fanghua Ye, Shuhao Li, Yunpu Ma, Wenjie Li, and Xiaoyu
     and extrinsic hallucinations in large video-language models.             Shen. On-policy supervised fine-tuning for efficient reason-
     arXiv preprint arXiv:2406.16338, 2024. 2                                 ing. arXiv preprint arXiv:2602.13407, 2026. 2
[52] Yan Wang, Yawen Zeng, Jingsheng Zheng, Xiaofen Xing,                [65] Ge Zheng, Bin Yang, Jiajin Tang, Hong-Yu Zhou, and Sibei
     Jin Xu, and Xiangmin Xu. VideoCoT: A video chain-of-                     Yang. Ddcot: Duty-distinct chain-of-thought prompting for
     thought dataset with active annotation tool. In Proceedings              multimodal reasoning in language models. Advances in Neu-
     of the 3rd Workshop on Advances in Language and Vision                   ral Information Processing Systems, 36:5168–5191, 2023. 2
     Research (ALVR), pages 92–101, Bangkok, Thailand, 2024.
     Association for Computational Linguistics. 2
[53] Yuetian Weng, Mingfei Han, Haoyu He, Xiaojun Chang, and
     Bohan Zhuang. Longvlm: Efficient long video understand-
     ing via large language models, 2024. 1
[54] Hao Wu, Yingqi Fan, Jinyang Dai, Junlong Tong, Yunpu Ma,
     and Xiaoyu Shen. Hidrop: Hierarchical vision token reduc-
     tion in mllms via late injection, concave pyramid pruning,
     and early exit. arXiv preprint arXiv:2602.23699, 2026. 2
[55] Hao Wu, Junlong Tong, Xudong Wang, Yang Tan, Changyu
     Zeng, Anastasia Antsiferova, and Xiaoyu Shen. From data
     to model: A survey of the compression lifecycle in mllms.
     techrxiv preprinttechrxiv.177220375.55495124/v1, 2026. 1
[56] Kun Xiang, Zhili Liu, Zihao Jiang, Yunshuang Nie, Kaixin
     Cai, Yiyang Yin, Runhui Huang, Haoxiang Fan, Hanhui Li,
     Weiran Huang, et al. Can atomic step decomposition en-
     hance the self-structured reasoning of multimodal large mod-
     els? arXiv preprint arXiv:2503.06252, 2025. 2
[57] Haomiao Xiong, Zongxin Yang, Jiazuo Yu, Yunzhi Zhuge,
     Lu Zhang, Jiawen Zhu, and Huchuan Lu. Streaming video
     understanding and multi-round interaction with memory-
     enhanced knowledge, 2025. 3
[58] Ruyi Xu, Guangxuan Xiao, Yukang Chen, Liuning He, Kelly
     Peng, Yao Lu, and Song Han. Streamingvlm: Real-time


                                                                    11
        Think-as-You-See: Streaming Chain-of-Thought Reasoning for Large
                             Vision-Language Models
                                                    Supplementary Material
A. Details of Streaming CoT Pipeline                                Algorithm 1 Quality Assurance and Temporal Filtering
A.1. CLIP-Guided Frame ID Alignment                                 Require: Question Qt , keyframe captions {ck }
                                                                    Require: Thresholds τq = 0.7, τadj = 0.9
Step 1: Semantic anchoring before resampling. Given                     Step 1: Question–caption relevance screening
a video V = {Ft }Tt=1 with timestamps {τt }Tt=1 and anno-            1: for each caption ck do
tated keyframe captions C = {ck }Kk=1 , we first compute             2:     sk ← sim(e(Qt ), e(ck ))
CLIP embeddings for all frames and captions:                         3: end for
                                                                     4: Kt ← {k | sk ≥ τq }
        f t = Encimg
                 CLIP (Ft ),       g k = Enctext
                                            CLIP (ck ).
                                                                        Step 2: Anti-redundancy temporal de-duplication
We utilize cosine similarity throughout the alignment pro-           5: Sort Kt by time
cess:                                                                6: Kt⋆ ← [ ]
                                  a⊤ b                               7: for each k in Kt do
                 sim(a, b) =             .
                                 ∥a∥ ∥b∥                             8:     if Kt⋆ is empty then
For each keyframe caption ck , we identify its most similar          9:          Append k to Kt⋆
frame index:                                                        10:     else
                                                                    11:          Let j be last element in Kt⋆
            t⋆k = arg     max          sim(f t , g k ),             12:          sj,k ← sim(e(cj ), e(ck ))
                        t∈{1,...,T }
                                                                    13:          if sj,k < τadj then
recording the anchor timestamp τbk = τt⋆k . These anchors           14:               Append k to Kt⋆
serve as semantic locks preserved during subsequent resam-          15:          end if
pling.                                                              16:     end if
                                                                    17: end for
Step 2: Timestamp-based resampling at 2 FPS with an-                    Step 3: Formatting supervision targets
chor preservation. Let the target sampling interval be              18: for each sampled frame index t′ do
                                                     ′
∆ = 0.5 s (2 FPS) and the target grid be {τt′′ }Tt′ =1 with         19:     if t′ ∈ Kt⋆ then
τt′′ = (t′ − 1)∆. For each target timestamp τt′′ , we select        20:          Emit [Rt′ ] < /EOT >
the frame Ft′ as:                                                   21:     else
                                                                   22:          Emit <SKIP>
           Ft⋆ , if τt′′ ∈ [b
                             τk − ϵ, τbk + ϵ] for some k,           23:     end if
              k
  Ft =
     ′
                                                                    24: end for
           arg min |τt − τt′′ |, otherwise,
                 Ft

where ϵ = 0.1 s is a tolerance window ensuring every se-
                                                                    A.3. Practical Notes
mantic anchor τbk snaps to the nearest sampling point. Post-
selection, frame indices are renormalized, and clips are            • Embedding normalization. All embeddings are ℓ2 -
truncated to the maximum input duration (30 s).                       normalized prior to similarity computation to stabilize
                                                                      thresholds.
A.2. Quality Assurance and Temporal Filtering                       • Batching. Frame and caption embeddings are computed
To ensure generated frame-level trajectories are temporally           in batches to mitigate I/O latency for long videos.
grounded and semantically reliable, we apply a three-stage          • Hyperparameters. Default values are ∆ = 0.5 s, ϵ =
filtering process (Algorithm 1). First, we identify question-         0.1 s, τq = 0.7, and τadj = 0.9, balancing temporal pre-
relevant keyframes via embedding similarity. Second, we               cision with retention of key semantic content.
prune temporally adjacent captions with redundant seman-
tics to preserve distinct perceptual events. Finally, we for-
                                                                    A.4. Details of Dataset
mat the supervision sequence by assigning </EOT> to se-             The dataset spans 12 video reasoning tasks covering fine-
lected keyframes and <SKIP> to others. This yields a tem-           grained event interpretation and high-level semantic under-
porally sparse but well-aligned target stream, guiding the          standing. As shown in Figure 8 and Table 3, the task distri-
model to reason only at meaningful moments.                         bution is long-tailed: Causal Analysis and Event Dynamic


                                                                1
Analysis dominate, while Ingredient Analysis and Behav-                                                                       Keyframe Count Distribution
ior Analysis are less frequent. This reflects the natural
                                                                                                        80000                        74703
prevalence of reasoning behaviors in real-world video con-                                                                          (71.7%)
tent while ensuring broad coverage for multi-step reasoning
evaluation.



                                                                                     Number of Videos
                                                                                                        60000
   Temporal structure also varies significantly. Figure 9 il-
lustrates the distribution of keyframe counts, revealing a
wide spectrum of temporal sparsity. Some videos con-                                                    40000
tain sparse salient moments, while others feature dense, ex-
                                                                                                                                                         21105
tended event sequences. This variability is critical for eval-                                                                                          (20.3%)
uating streaming reasoning, requiring models to adapt to                                                20000
                                                                                                                     5628                                                    2746
varying event frequencies and accurately identify meaning-                                                          (5.4%)                                                  (2.6%)
ful visual changes.                                                                                         0
                                                                                                                      12                 3                  4                    5
                                                                                                                                     Keyframe Count Groups
                                                    Tasks
                                       Behavior Analysis                                                   Figure 9. Distribution of keyframe counts per sample.
                                       Causal Analysis
                                       Contextual Analysis
                                       Emotion Analysis
                                       Event Dynamic Analysis                                                                 Prompt: QA Construction
                                       Influence Analysis
                                       Interaction Analysis                                        You are a video description normalizer. Rewrite the evidence based on the given question
                                       Narrative Analysis                                          and answer.
                                       Preparation Steps / Ingredient Analysis                     Question: {question}
                                       Role Analysis                                               Answer: {answer}
                                       Theme Analysis                                              Rules:
                                       Traffic Analysis                                            1. Each frame must have exactly one sentence.
                                                                                                   2. Each sentence starts with "In frame X," and ends with a period.
                                                                                                   3. Keep all original frame numbers, in the same order, without adding or removing any.
                                                                                                   4. Do not merge multiple frames into one sentence or split a frame into several.
            Figure 8. Task distribution in the dataset.                                            5. Write each frame on a new line.
                                                                                                   6. Adjust expressions so the narrative aligns naturally with the QA semantics while
                                                                                                   keeping the visual meaning unchanged.
                                                                                                   Original Evidence:
                                                                                                   {evidence}
 Table 3. Distribution of task categories in training and test sets.                               Rewritten Evidence:


 Task                                Train Set              Test Set                                            Figure 10. Prompt template for QA construction.
 Causal Analysis                       52,566                   208
 Event Dynamic Analysis                18,675                    82
 Preparation Steps / Ingredient                                                                                            Prompt: CoT Inference
                                       2,252                     74
 Analysis                                                                                               Please imagine this question as a person pondering deeply.
 Theme Analysis                        6,206                     33                                     The content of frames related to references and issues is
 Interaction Analysis                  4,208                     38                                     used to form a thinking process in chronological order of
 Influence Analysis                    4,406                     45                                     the events.
 Role Analysis                         4,843                     31                                     Encourage self reflection or verification during the
 Emotion Analysis                      1,999                     39                                     reasoning process.
 Narrative Analysis                    1,755                     35                                     Please provide a detailed reasoning between the <think>
 Contextual Analysis                   6,827                     38                                     and </think> tags, and then provide your final answer
 Behavior Analysis                      227                      12                                     between the <answer> and </answer> tags.
 Traffic Analysis                       218                      14
                                                                                                                 Figure 11. Prompt template for CoT inference.

B. Prompt Details
                                                                                       with causal masking. Optimization employs AdamW with
We present the complete prompts used in our pipeline, in-
                                                                                       cosine decay, mixed-precision (bfloat16), gradient accumu-
cluding QA construction (Figure 10), CoT inference (Fig-
                                                                                       lation, activation checkpointing, and DeepSpeed ZeRO-3
ure 11), and subjective evaluation (Figure 12).
                                                                                       for memory efficiency. The vision encoder remains frozen,
C. Training Details                                                                    while the multimodal projector and LLM backbone are fine-
                                                                                       tuned. We regulate video token length via pixel-based con-
We train TaYS using a streaming-aware decoder-only ob-                                 straints and train for two epochs with an effective sequence
jective, where visual and reasoning tokens are interleaved                             length of 8192 tokens.


                                                                                 2
                             Prompt: Subjective Evaluation                                                      Algorithm 2 Two-Stage Objective Evaluation
  You are an expert evaluation assistant. Your task is to compare three model outputs based on the given
  Question and the Ground-Truth Answer.
                                                                                                                Require: Prediction ỹ, reference answer y ⋆ , options O =
  First, carefully read the Question and the Ground-Truth Answer.
  Then evaluate each model output (A, B, and C) across the following four aspects:
                                                                                                                    {o1 , o2 , o3 , o4 }, correct option o⋆ ∈ O, similarity func-
  Evaluation Criteria (1–10 per dimension)                                                                          tion sim, threshold τ
  Logic: Evaluate whether the reasoning is coherent, structured, and follows logically from the question.
  (1–2: illogical; 3–4: inconsistent; 5–6: partially logical; 7–8: mostly logical; 9–10: fully logical)          1: sref ← sim(ỹ, y ⋆ )
  Factuality: Check correctness and absence of factual errors relative to the ground-truth answer.
  (1–2: mostly incorrect; 3–4: major errors; 5–6: minor errors; 7–8: highly factual; 9–10: fully factual)        2: if sref < τ then
  Accuracy: Assess how precisely the model answers the question and matches the ground-truth answer.
  (1–2: irrelevant; 3–4: weak alignment; 5–6: partial correctness; 7–8: mostly accurate; 9–10: perfectly         3:      return I NCORRECT
  accurate)
  Conciseness: Evaluate clarity and brevity without unnecessary verbosity.
                                                                                                                 4: end if
  (1–2: very verbose or incomplete; 3–4: unfocused; 5–6: somewhat concise; 7–8: concise; 9–10:
  extremely concise and clear)
                                                                                                                 5: for each oj ∈ O do
  You should internally consider all four scores for each model to judge overall quality, but DO NOT
  output the scores.
                                                                                                                 6:      sj ← sim(ỹ, oj )
  Instead, provide a final decision on which model output is best overall.                                       7: end for
  Final Output Instruction
  Choose only ONE of the following responses: Best: A; Best: B; Best: C; Best: Tie;                              8: sopt ← sim(ỹ, o⋆ )
                                                                                                                 9: sneg
                                                                                                                      max ← max{sj : oj ∈ O, oj ̸= o }
                                                                                                                                                             ⋆
                                                                                                                                                   neg
        Figure 12. Prompt template for subjective evaluation.                                                   10: if sopt ≥ τ and sopt > smax then
                                                                                                                11:      return C ORRECT
               Table 4. Training hyperparameters for TaYS.                                                      12: else
                                                                                                                13:      return I NCORRECT
       Config                                                        Value                                      14: end if

       input resolution                            variable (pixel-constrained)
       max token length                                        8192
       vision encoder                                         frozen                                            ties sj = sim(ỹ, oj ) for all options. Let sopt = sim(ỹ, o⋆ )
       trainable modules                             LLM + MLP projector                                        and sneg
                                                                                                                      max = maxoj ̸=o⋆ sj . A prediction is correct only if:
       precision                                             bfloat16
       optimizer                                             AdamW                                                      sref ≥ τ,    sopt ≥ τ,     and   sopt > sneg
                                                                                                                                                                 max .
       learning rate                                        2 × 10−5
       lr schedule                                         cosine decay                                         Latency Evaluation Protocol. We quantify real-time
       warmup ratio                                            0.03                                             performance using two metrics: (1) Time to First Token
       batch size                                      1 (grad accum = 16)                                      (TTFT), measuring the interval between the arrival of the
       epochs                                                    2
                                                                                                                first frame and the emission of the first token; (2) Overall
       gradient clipping                                        1.0
                                                                                                                Delay, measuring the total time to complete reasoning and
       gradient checkpointing                                enabled
       distributed training                            torchrun + ZeRO-3                                        produce the final answer. All inferences run on identical
       max video frames                                         60                                              hardware with token-level timing resolution to ensure fair
       video token budget                           24K tokens (pixel-based)                                    comparison.


D. Evaluation Details
Construction of Test Set. Following the VideoEspresso
protocol, we construct the test set with three distractor
options per question. Distractors are designed to match
the correct answer in contextual relevance and linguistic
form while containing explicit factual inaccuracies, ensur-
ing a discriminative evaluation. We apply the same answer-
rewriting procedure as in training to maintain consistency.

Objective Evaluation Protocol. For each sample, we
evaluate a free-form prediction ỹ against a reference answer
y ⋆ and multiple-choice options O = {o1 , o2 , o3 , o4 }, where
o⋆ is the correct option. We use a semantic similarity func-
tion sim(·, ·) with a threshold τ = 0.8.
    Stage 1: Reference similarity. We first compute sref =
sim(ỹ, y ⋆ ). If sref < τ , the prediction is deemed incorrect.
    Stage 2: Option discrimination. We compute similari-


                                                                                                            3
