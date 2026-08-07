                                                                 From Static Inference to Dynamic Interaction:
                                                               A Survey of Streaming Large Language Models
                                                               Junlong Tong1,2 , Zilong Wang2 , YuJie Ren2 , Peiran Yin2 ,
                                                                          Hao Wu2 , Wei Zhang2 , Xiaoyu Shen2 *
                                                                               1
                                                                                 Shanghai Jiao Tong University
                                                           2
                                                             Institute of Digital Twin, Eastern Institute of Technology, Ningbo
                                                                    jl-tong@sjtu.edu.cn xyshen@eitech.edu.cn


                                                                Abstract                                     Decode               Decode         Decode

                                              Standard Large Language Models (LLMs) are




arXiv:2603.04592v3 [cs.CL] 19 Apr 2026
                                              predominantly designed for static inference
                                              with pre-defined inputs, which limits their ap-               LLM                  LLM                  LLM
                                              plicability in dynamic, real-time scenarios. To
                                              address this gap, the streaming LLM paradigm
                                              has emerged. However, existing definitions of
                                              streaming LLMs remain fragmented, conflat-          Read at once            Read                 Read
                                              ing streaming generation, streaming inputs, and
                                              interactive streaming architectures, while a sys-   Figure 1: Illustration of three types of streaming large
                                                                                                  language models (LLMs). (Left) Output-streaming LLM
                                              tematic taxonomy is still lacking. This paper
                                                                                                  performs streaming generation after static reading. (Mid-
                                              provides a comprehensive overview and anal-         dle) Sequential-streaming LLM performs streaming genera-
                                              ysis of streaming LLMs. First, we establish         tion after streaming reading. (Right) Concurrent-streaming
                                              a unified definition of streaming LLMs based        LLM performs streaming generation while streaming reading.
                                              on data flow and dynamic interaction to clarify
                                              existing ambiguities. Building on this defini-
                                              tion, we propose a systematic taxonomy of cur-         Such dynamic conditions are ubiquitous in tasks
                                              rent streaming LLMs and provide an in-depth         like real-time translation, streaming video under-
                                              discussion of their underlying methodologies        standing, and interactive tool agents (Agostinelli
                                              across text, speech, and video streaming scenar-
                                                                                                  et al., 2024; Jin et al., 2025; Yang et al., 2025b).
                                              ios. Furthermore, we explore the applications
                                              of streaming LLMs in real-world scenarios and       In these real-world applications, inputs such as
                                              outline promising research directions to support    speech and video data stream continuously, forc-
                                              ongoing advances in streaming intelligence.         ing systems to maintain an evolving understanding
                                              We maintain a continuously updated repository       based on partial observations. In more complex
                                              of relevant papers at https://github.com/           scenarios, these signals may originate from mul-
                                              EIT-NLP/Awesome-Streaming-LLMs.                     tiple concurrent streams (Li et al., 2025k), while
                                         1    Introduction                                        systems may also need to generate multiple outputs
                                                                                                  in parallel (Zhang et al., 2025b). For instance, a
                                         Large Language Models (LLMs) have shown re-              robot may need to act, speak, and reason simultane-
                                         markable efficacy across diverse domains, exhibit-       ously (Zhang et al., 2025e), whereas an interactive
                                         ing strong reasoning, generation, and cross-modal        assistant may coordinate speech, visual updates,
                                         capabilities (OpenAI, 2023; Team et al., 2023;           and control commands (Zhang et al., 2025a). Since
                                         DeepSeek-AI et al., 2024). However, LLMs are             the input is never fully available at any given mo-
                                         predominantly pre-trained on static and full-context     ment, the system must dynamically decide when to
                                         corpora, following a “read-at-once” paradigm in          respond, when to wait for more information, and
                                         which the complete input is provided before any          when to terminate (Panchal et al., 2024; Zhang
                                         output is generated. While effective for benchmark-      et al., 2025c). These requirements expose a fun-
                                         style tasks, this paradigm fundamentally limits their    damental mismatch with the offline, full-context
                                         applicability in real-world environments, where in-      design of standard LLMs.
                                         formation arrives incrementally, accumulates over           Adapting LLMs to these real-world streaming
                                         time, and may be unbounded in length.                    scenarios presents significant challenges. Beyond
                                             * Corresponding author                               architectural modifications, there is a scarcity of
large-scale pre-training data that supports real-                   ing LLMs, clarifying the conceptual distinc-
time interaction, partial-input supervision, and fine-              tions among existing paradigms.
grained temporal alignment. Motivated by this gap,                • We provide a systematic taxonomy and com-
recent research has begun to investigate streaming                  prehensive technical analysis, disentangling
LLMs (Tong et al., 2025a; Chen et al., 2024a; Du                    the mechanisms of three streaming paradigms.
et al., 2024). However, the field currently suffers               • We discuss emerging applications and open
from terminological ambiguity. Existing studies                     research directions for real-time and interac-
often conflate distinct concepts, such as autore-                   tive streaming scenarios.
gressive decoding (Kondratyuk et al., 2024), incre-
mental or chunk-wise encoding (Xiao et al., 2023),
and full-duplex interaction like GPT-4o (OpenAI,              2     Preliminaries
2023), under a single “Streaming LLM” umbrella,               2.1    Background of Streaming LLMs
obscuring meaningful comparisons.
                                                              Current LLMs typically operate under a batch pro-
   In this work, we provide the first systematic re-
                                                              cessing paradigm, where the model encodes the
view of streaming LLMs, proposing a unified def-
                                                              entire input sequence into the KV cache during the
inition based on data flow and interaction concur-
                                                              prefill phase and subsequently generates tokens au-
rency. As illustrated in Figure 1, we categorize
                                                              toregressively in the decoding phase. Consequently,
these models into three distinct levels: (1) Output-
                                                              from a data flow perspective, standard LLMs can
streaming LLMs, which retain static input process-
                                                              be categorized as “streaming-output LLMs” that
ing but support streaming output generation. (2)
                                                              rely on static context availability. However, real-
Sequential-streaming LLMs, which process stream-
                                                              world data flows often exhibit dynamic and con-
ing inputs incrementally but generate with full in-
                                                              tinuous characteristics (e.g., real-time speech tran-
put. (3) Concurrent-streaming LLMs, which enable
                                                              scription and content understanding), necessitating
full-duplex interaction by continuously receiving
                                                              models capable of handling streaming inputs and
inputs and generating outputs.
                                                              executing timely output decisions; therefore, gen-
   This taxonomy captures both conceptual distinc-
                                                              eralized streaming LLMs are defined to address
tions and a clear progression of technical chal-
                                                              such dynamic input and immediate response sce-
lenges: Output streaming addresses challenges in
                                                              narios, aiming to transcend the limitations of static
streaming and low-latency generation; sequential
                                                              preprocessing and delayed response.
streaming introduces incremental encoding and
context management; and concurrent streaming                  2.2    Formal Definition
builds upon both to address architecture adaptation           To rigorously unify the diverse landscape of stream-
and interaction strategies required for full-duplex           ing LLMs in Figure 1, we formulate the modeling
processing. By disentangling these paradigms, the             process as a conditional probability distribution
taxonomy clarifies which challenges are shared,               P (Y |X), where X = (x1 , . . . , xM ) denotes the
which are incremental, and which are unique                   bounded input stream and Y = (y1 , . . . , yN ) de-
to each category, thereby providing a structured              notes the output stream. This distribution can be
roadmap toward the ultimate goal of fully interac-            factorized autoregressively using the chain rule:
tive streaming LLMs. Guided by this framework,
we systematically review representative methods in                               N
                                                                                 Y                                  
each category, examine emerging applications such                   P (Y |X) =         P yt |y<t , h1:ϕ(t) (X); θ       (1)
as streaming video understanding and real-time                                   t=1
reasoning, and highlight open problems, includ-               where θ denotes the LLM parameters, and
ing trade-offs between latency and performance, to            hϕ(t) (X) = llm(xϕ(t) ) represents the encoded hid-
inform future research.1                                      den states corresponding to the input prefix xϕ(t) .
   To summarize, our main contributions include:              Here, ϕ(t) is a decision function to determine the
   • To our knowledge, we are the first systematic            input stream visible at generation step t. This gen-
     survey of streaming LLMs.                                eral definition can be instantiated into three sub-
   • We introduce a unified definition of stream-             types by applying varying operational constraints.
   1
    We provide a detailed description of motivation, survey   Output-streaming LLMs This paradigm im-
scope, and difference with related surveys in Appendix A.     poses a static constraint where the entire input must
Figure 2: Overview of streaming LLM paradigms and their key challenges. The figure contrasts Output-streaming,
Sequential-streaming, and Concurrent-streaming LLMs, highlighting their core goals and corresponding research
components. Concurrent-streaming builds on the first two and adds extra challenges in real-time streaming
architecture adaptation and interaction policy learning.


be processed before generation begins. Mathemati-       static processing to dynamic, real-time interaction.
cally, the decision function is constant relative to
                                                           1 ≤ · · · ≤ ϕ(t) ≤ ϕ(t + 1) ≤ · · · ≤ M.
the total input length M , i.e., ϕ(t) = M for all
t ∈ {1, . . . , N }. The hidden states are computed
via a one-time global prefilling: h1:ϕ(t) (X) =
h1:M (X) = llm(X1:M ).                                  2.3   Overview

Sequential-streaming LLMs This paradigm pro-            This survey provides a systematical overview of
cesses dynamic streaming inputs but generates           research in streaming LLMs. Figure 2 illustrates
based on a fixed input. While the decision func-        the proposed taxonomy, detailing the primary re-
tion mirrors the above type (i.e., ϕ(t) = M, ∀t),       search focuses and challenges within each category.
the hidden states are constrained by stepwise ar-       Specifically, output-streaming emphasizes stream-
rival: h1:M (X) = {llm(x1 ), . . . , llm(xM )}. This    ing generation mechanisms and efficient genera-
represents a sequential encoding process where the      tion; sequential-streaming focuses on incremental
context is accumulated token-by-token (or chunk-        encoding processing and context management for
by-chunk) before the generation phase begins.           input streams; and concurrent-streaming integrates
                                                        both tasks, additionally introducing architectural
Concurrent-streaming LLMs This paradigm                 adaptations and the interactive management of si-
imposes the strictest temporal constraints, repre-      multaneous input and output streams. To navigate
senting a dynamic process where streams unfold          this comprehensive landscape, Figure 3 outlines
continuously. Mathematically, ϕ(t) must satisfy         the taxonomy structure of this survey. Guided by
monotonicity and partial visibility:1 ≤ · · · ≤         this taxonomy, we begin with output-streaming in
ϕ(t) ≤ ϕ(t + 1) ≤ · · · ≤ M. The hidden states          Section 3, expand to the dynamic input processing
of input stream are computed via a dynamic or           of sequential-streaming in Section 4, and culmi-
interactive process: hϕ(t) (X) = llm(Xϕ(t) , y<t ).     nate with the interactive dynamics of concurrent-
   The tripartite taxonomy defined above reflects a     streaming in Section 5. Beyond the technical part,
trajectory of escalating operational constraints and    Section 6 reviews downstream tasks and applica-
functional demands, shifting the paradigm from          tions, and Section 7 discusses the future directions.
                                                                                            Standard-autorgressive: GPT (OpenAI, 2023), LlamaGen (Sun et al., 2024),
                                                                        Token-wise
                                                                                            VideoPoet (Kondratyuk et al., 2024), SpeechGPT(Zhang et al., 2023a), etc.

                                                                                            Semi-autorgressive: SoT (Ning et al., 2023), Falcon (Gao et al., 2025), etc.
                                          Streaming Generation          Block-wise




         Output-Streaming LLMs (§3)
                                            Mechanism (§3.1)                                Block-diffusion: SSD-LM (Han et al., 2023), WeDLM (Liu et al., 2025a), etc.

                                                                                            Multi-scale:VAR (Tian et al., 2024), Onecat (Li et al., 2025c), etc.
                                                                     Refinement-based
                                                                                            Global-diffusion: LaViDa (Li et al., 2025g), LLaDA (Nie et al., 2025), etc.

                                                                                            Token-path:Speculative Decoding (Chen et al., 2023; Cai et al., 2024a), etc.
                                                                         Decoding
                                                                     Path Acceleration
                                           Efficient Streaming                              Layer-depth:AdaInfer (Fan et al., 2024), Layer Skipping (Zhao et al., 2025a), etc.
                                            Generation (§3.2)
                                                                    Memory Efficiency       Dynamic-LLaVA (Huang et al., 2024), StreamingLLM (Xiao et al., 2023), etc.

                                                                                            Native Discrtet Tokens:Subword Regularization (Kudo, 2018),
                                                                                            SentencePiece (Kudo and Richardson, 2018), etc.
                                                                     Atomic Encoding
                                                                                            Pre-discretized Units:ViT (Dosovitskiy, 2020), CLIP (Radford et al., 2021), etc.




         Sequential-Streaming LLMs (§4)
                                              Incremental
                                            Encoding (§4.1)                                 Fixed-Interval Partitioning: LLM-SimulMT (Wang et al., 2024c),
                                                                                            Whisper-Streaming (Macháček et al., 2023), Wav2vec-S (Fu et al., 2024a), etc.
                                                                   Fragmented Encoding
                                                                                            Semantic-Driven Partitioning: DiSeg (Zhang and Feng, 2023),
                                                                                            CTC (Graves, 2012), S-ViT (Zhao et al., 2023), etc.

                                                                                            VideoScan (Li et al., 2025f), Flash-vstream (Zhang et al., 2024b),
                                                                     Memory Retention
                                                                                            VideoStreaming (Qian et al., 2024), StreamForest (Zeng et al., 2025), etc.
                                           Streaming Context
                                           Management (§4.2)                                Attention-Aware Eviction: StreamingLLM (Xiao et al., 2023),
                                                                       KV Cache and         StreamKV (Chen et al., 2025c), StreamingVLM (Xu et al., 2025d), etc.
                                                                   Attention Management
                                                                                            Representation Compression:KIVI (Liu et al., 2024c), ZipCache (He et al., 2024), etc.

                                                                   Re-encoding Streaming    Simul-LLM (Agostinelli et al., 2024), SiLLM (Guo et al., 2024c), etc.

                                                                                            Qwen3-omni (Xu et al., 2025c), ViSpeak (Fu et al., 2025c),
                                                                   Concatenated Streaming
                                                                                            LLMVoX (Shikhar et al., 2025), Mini-Omni (Xie and Wu, 2024), etc.
                                             Architecture
                                           Adaptation (§5.1)                                Videollm-online (Chen et al., 2024a), Cosyvoice 2 (Du et al., 2024),




         Concurrent-Streaming LLMs (§5)
                                                                   Interleaved Streaming
                                                                                            SyncLLM (Liu et al., 2025d), LiveCC (Chen et al., 2025a), etc.

                                                                                            StreamingGPE (Tong et al., 2025b), StreamingThinker (Tong et al., 2025a),
                                                                     Group Streaming
                                                                                            StreamChat (Liu et al., 2024b), Speak-While-Watching (Lin et al., 2026), etc.

                                                                                            Pre-defiend: STACL (Ma et al., 2019), LiveCC (Chen et al., 2025a), etc.
                                                                     Rule-based Policy
                                                                                            Adaptive Thresholding: SimulS2SLLM (Deng et al., 2025), etc.

                                                                                            Auxiliary Decision: DiG-SST (Chen et al., 2024b), DrFrattn (Zhao et al., 2025b),
                                               Interaction                                  Dispider (Qian et al., 2025), ViSpeak (Fu et al., 2025c), etc.
                                              Policy (§5.2)          SFT-based Policy
                                                                                            In-context Prediction: VideoLLM-online (Chen et al., 2024a),
                                                                                            TransLLaMA (Koshkin et al., 2024b), ProVideLLM (Chatterjee et al., 2025), etc.

                                                                                            MMDuet2 (Wang et al., 2025c), Seed LiveInterpret 2.0 (Cheng et al., 2025b),
                                                                      RL-based Policy
                                                                                            SeqPO-SiMT (Xu et al., 2025e) etc.


                                                                 Figure 3: Taxonomy of Streaming Large Language Models.


3     Output-Streaming LLMs: Generating                                                                  this paradigm by aligning non-text modalities to the
      with Progressive Revelation                                                                        textual space for autoregressive streaming (Zhang
                                                                                                         et al., 2023a; Contributors, 2024).
3.1    Streaming Generation Mechanism
Output streaming enables progressive revelation by
                                                                                                         Block-wise These methods expand the genera-
continuously emitting intermediate results rather
                                                                                                         tion unit from single tokens to multi-token blocks,
than waiting for completion. Based on the gener-
                                                                                                         reducing serial depth while retaining the controlla-
ation granularity and update mechanism, we cate-
                                                                                                         bility of autoregressive modeling. We summarized
gorize existing methods into: (i) token-wise, (ii)
                                                                                                         them into two lines. (1) Semi-autoregressive re-
block-wise, and (iii) refinement-based.
                                                                                                         laxes intra-block dependencies to predict multiple
Token-wise This represents the dominant gen-                                                             tokens in parallel. (Wang et al., 2018; Hwang et al.,
eration paradigm for LLMs, employing token-                                                              2025; Ning et al., 2023; Gao et al., 2025). For
wise autoregressive decoding (Team et al., 2023;                                                         example, MTP (Gloeckle et al., 2024) predicts mul-
DeepSeek-AI et al., 2024; Gemma Team, 2024).                                                             tiple tokens simultaneously for each autoregressive
For multimodal outputs, systems typically extend                                                         block step. (2) Block-diffusion combines diffusion-
style refinement with block-wise generation, iter-              cost from generated length. Dynamic KV com-
atively denoising a block at a time and streaming               pression methods limit the scope of attention tar-
blocks autoregressively (Han et al., 2023; Liu et al.,          gets during streaming decoding (Liu et al., 2023;
2025a; Tian et al., 2025; Arriola et al., 2025).                Zhang et al., 2023b; Liao et al., 2025; Huang et al.,
                                                                2024). Representative implementations range from
Refinement-based Unlike token-by-token se-
                                                                sink-aware windowing (Xiao et al., 2023), which
quential accumulation, this paradigm performs
                                                                maintains a fixed budget for stability, to dynamic
progressive refinement from coarse to fine, iter-
                                                                decision strategies (Liao et al., 2025) for KV cache
atively improving the semantic completeness of
                                                                management based on token importance.
the entire sequence rather than merely extending
its length. (1) Multi-scale approach decomposes                 4     Sequential-Streaming LLMs:
generation into discrete scales (Tian et al., 2024;                   Processing Dynamic Input Streams
Li et al., 2025c; Zhuang et al., 2025). Models like
VAR (Tian et al., 2024) predict the next-scale au-              Building upon the foundation of output-streaming,
toregressively, enabling a blur-to-clear streaming              this section turns to sequential-streaming: the con-
effect. (2) Global-diffusion refinement formulates              tinuous perception of dynamic input streams. The
generation as multi-step denoising over the entire              core technical imperative shifts from generation
sequence, starting from noise or a coarse initializa-           latency to sustainability. Specifically, we focus on
tion and progressively refining to a complete output.           two core mechanisms: handling incremental inputs
This mechanism has been successfully adapted to                 to avoid re-computation, and optimizing context
both text (Nie et al., 2025; Li et al., 2025g; Song             management to accommodate long input streams.
et al., 2025; Li et al., 2022) and multimodal gener-
ation (Xin et al., 2025; Yang et al., 2025c).                   4.1    Incremental Encoding
                                                                Incremental encoding processes incoming streams
3.2    Efficient Streaming Generation                           solely based on past states, with historical rep-
Given the extensive scope of LLM optimization, we               resentations remaining unchanged under subse-
narrow our focus strictly to the streaming process              quent streaming inputs, avoiding quadratic re-
itself, analyzing decoding and memory efficiency.2              computation. The central issue lies in how to define
As token-wise decoding remains dominant, we fo-                 encoding units, such that the encoding of each unit
cus on its optimization for efficient streaming.                is not influenced by future information. Depending
                                                                on the unit construction strategy, we categorize two
Decoding Path Acceleration To mitigate autore-
                                                                types: atomic encoding and fragmented encoding.
gressive latency, optimizations modify the execu-
tion trajectory along two dimensions. (1) Token-                Atomic Encoding This paradigm is applicable
path methods generate parallel candidate chains to              to streams that have inherent delimiters aligned
relax strict serial dependency, including multi-path            with the model’s processing unit. (1) Native Dis-
and speculative decoding (Leviathan et al., 2023;               crete Tokens: Text is the primary example, where
Xiao et al., 2024b). For instance, speculative de-              input is naturally segmented into discrete tokens
coding (Chen et al., 2023; Cai et al., 2024a; Li                whose representations remain unchanged as new
et al., 2024d) leverages a lightweight draft model              tokens arrive (Kudo, 2018; Kudo and Richardson,
to propose multiple candidate tokens in parallel,               2018). (2) Pre-defined Units: Certain modalities
which are then verified and selectively accepted                admit pre-defined atomic units independent of fu-
by a target model, reducing streaming latency. (2)              ture context. For example, video streams can be
Layer-depth methods adaptively shorten the net-                 incrementally processed at the frame level, where
work depth based on token difficulty (Fan et al.,               each frame serves as a fixed encoding unit and is
2024; Del Corro et al., 2023) . For instance, by em-            encoded without being influenced by subsequent
ploying layer skipping (Zhao et al., 2025a), models             frames (Dosovitskiy, 2020; Radford et al., 2021).
terminate the execution path prematurely.
                                                                Fragmented Encoding Fragmented encoding
Memory Efficiency Since the KV cache grows                      handles raw continuous signals (e.g., audio wave-
linearly, optimizations aim to decouple memory                  forms and video pixel streams) without natural de-
   2
    We provide related survey papers on efficient LLMs in Ap-   limiters by introducing artificial boundaries to in-
pendix A for reference.                                         terface with discrete LLM architectures. Boundary
construction typically follows two strategies. (1)                       Time                          Time
                                                                           p3   p4         p?
fixed-interval partitioning, which slices streams
at uniform temporal intervals for efficiency but
may disrupt semantic units (Wang et al., 2024b;              Large Language Model         Large Language Model
Macháček et al., 2023). (2) semantic-driven parti-                                                    p?
tioning, which leverages content-dependent cues,             p0     p1     p2   p3         p0
                                                                                                   ?        Position-ID conflict
                                                                                                       p? Attention contention
such as word boundaries in speech (Zhang and
Feng, 2023; Graves, 2012) and shot or scene transi-      Figure 4: Illustration of structural conflicts when adapt-
                                                         ing batch-oriented LLMs (left) to concurrent streaming
tions in video (Zhao et al., 2023), to better preserve   (right), where         indicates the token generation direction,
semantic coherence at higher computational cost.                 denotes attention dependencies, blocks represent the
                                                         input, and blocks represent the output. (1) Attention con-
4.2   Streaming Context Management                       tention: Ambiguous causal dependency between the newly
                                                         inserted streaming input and historical outputs. (2) Position-
Streaming context management focuses on main-            ID conflict: The new streaming input and generated output
taining and updating contextual information during       compete for the identical position ID.
incremental processing under limited memory and
computation budgets. It can be viewed through
                                                         We categorize these strategies into two comple-
three complementary aspects: what information
                                                         mentary directions. (1) Attention-Aware Eviction:
to keep over long-running streams (memory), how
                                                         These methods bound memory growth by restrict-
to store and update it across decoding steps (KV
                                                         ing the attention mechanism to a sparse subset of
cache), and how to efficiently access it via opti-
                                                         historical tokens. By identifying and retaining only
mized attention mechanisms (attention).
                                                         critical states, such as recent tokens maintained
Memory Retention Memory retention concerns               by a sliding window and high-importance atten-
what historical information should be preserved          tion sinks or heavy hitters, the model can safely
or discarded during long-running input streaming.        evict unaccessed KV pairs, ensuring constant time
We classify these methods into two primary cate-         and memory complexity without disrupting gener-
gories. (1) Salient content selection and eviction       ation quality. (Xiao et al., 2023; Li et al., 2024c;
approaches focuses on identifying and retaining          Cai et al., 2024b; Yang et al., 2025e; Liao et al.,
salient tokens or segments while discarding less         2025). (2) Representation Compression: Comple-
informative or redundant content as the stream           mentary to eviction, compression approaches re-
grows (Zhang et al., 2024b; Yao et al., 2025; Qian       duce the memory footprint of the retained states.
et al., 2024; Wang et al., 2025b). Selection crite-      Techniques such as low-bit quantization or low-
ria are typically based on importance estimation,        rank approximation compress the key–value rep-
recency, or task relevance, enabling bounded mem-        resentations, allowing the model to accommodate
ory usage under continuous inputs. (2) Instead of        longer effective contexts within a fixed memory
outright discarding past information, token merg-        budget (Liu et al., 2024c; Hooper et al., 2024; He
ing and memory consolidation compress historical         et al., 2024; Liu et al., 2025g).
representations by aggregating multiple tokens or
states into more compact forms (Zhong et al., 2024;      5        Concurrent-Streaming LLMs: The
Wang et al., 2023; Zeng et al., 2025; Chen et al.,                Streaming of Real-Time Interaction
2025b). Such strategies preserve coarse-grained
                                                         Concurrent-streaming represent a crucial step to-
contextual information while reducing memory
                                                         ward real-time interactive intelligence, requiring
footprint, allowing long-term context to be main-
                                                         LLMs to simultaneously process streaming inputs
tained in a compressed manner.
                                                         and generate outputs. However, this dynamic
KV Cache and Attention Management While                  paradigm diverges from standard static pre-training.
memory retention operates at the input level, this       First, regarding architecture adaptation, concurrent
component focuses on the internal maintenance of         streaming introduce structural conflicts, as illus-
intermediate states and the optimization of atten-       trated in Figure 4. Second, synchronization con-
tion computation. Since the attention range dictates     trol governs system interactivity by dynamically
which historical states are required for generation,     deciding when to alternate between reading and
attention access patterns and cache storage strate-      writing, balancing responsiveness and coherence,
gies are inherently coupled in streaming scenarios.      as illustrated in Figure 5. Accordingly, we catego-
rize existing research into architecture adaptation         Time
and interaction policy.                                     Input
                                                                     ...      ...       ...
5.1   Architecture Adaptation
                                                                               Interaction decision
Architecture adaptation mitigates structural con-                    ...      ...       ...
                                                            Output
flicts inherent in concurrent processing, including
attention contention and positional conflicts (Fig-                                           Attention dependence
ure 4). Attention contention arises when continu-
ously arriving inputs interleave with generation,        Figure 5: Illustration of interaction decision in concurrent
                                                         streaming LLMs, where the model learns to dynamically
making attention dependency ordering ambigu-             schedule reading inputs and emitting outputs.
ous, while positional conflicts occur when asyn-
chronously injected inputs overlap with output po-
sitions. Existing work redesigns input–output inter-     et al., 2026). This design eliminates attention
action mechanisms, which we categorize into four         contention while maintaining isolated positional
representative streaming paradigms.                      spaces, and empirical results show that grouped po-
                                                         sitional encoding preserves streaming performance
Re-encoded streaming The model re-encodes                and can improve parallelism and efficiency.
all historical caches whenever new input ar-
rives (Deng et al., 2025; Agostinelli et al., 2024;      5.2   Interaction policy
Guo et al., 2024c). By recomputing representations       Interaction policy governs read–write synchroniza-
over the entire context, this approach eliminates        tion in concurrent LLMs, balancing latency and
attention contention and positional misalignment,        output quality. Existing strategies fall into three
preserving batch-equivalent attention dependencies.      paradigms based on their optimization approach:
However, the resulting computational overhead lim-       rule-based, SFT-based, and RL-based policies.
its its applicability to long-context and real-time
settings (Guo et al., 2024b; Raffel et al., 2024).       Rule-based Interaction Rule-based approaches
                                                         rely on predetermined schedules or statistical
Concatenated streaming Concatenated stream-
                                                         thresholds, offering interpretability and control
ing concatenates the newly arrived input tokens
                                                         without requiring model parameter updates. (1)
with the previously generated outputs and feeds
                                                         Pre-defined strategy enforce a rigid, content-
them jointly into the model at each step (Xu et al.,
                                                         agnostic read-write rhythm (Ma et al., 2019; Chen
2025c,b; Ding et al., 2025a; Shikhar et al., 2025).
                                                         et al., 2025a; Tong et al., 2025a). The most repre-
This design resolves both conflicts by unifying at-
                                                         sentative approach is the Wait-k policy (Ma et al.,
tention and positional ordering, but incurs grow-
                                                         2019). In this strategy, the model always waits
ing memory and latency and requires architectural
                                                         for k tokens or segments of input lag before gen-
changes and retraining (Shikhar et al., 2025).
                                                         erating the corresponding output. While efficient
Interleaved streaming This paradigm inter-               and easy to implement, pre-defined policies lack
leaves input and output tokens within a shared           adaptability to varying input complexity and rate
sequence, assigning attention and positional en-         fluctuations. (2) Adaptive thresholding methods
codings according to their temporal order (Chen          utilize real-time inference statistics as decision sig-
et al., 2024a; Du et al., 2024; Liu et al., 2025d; Xu    nals to improve flexibility (Agostinelli et al., 2024;
et al., 2025d; Chen et al., 2025a; Qian et al., 2025).   Yang et al., 2025g). These policies trigger read-
It preserves the temporal flow of streaming inter-       /write actions based on metric thresholds (e.g., at-
action, enabling input and output to coexist with        tention weights) rather than a fixed schedule. For
consistent ordering (Chen et al., 2025a). While          instance, SimulS2S (Agostinelli et al., 2024) mon-
balancing computational efficiency and real-time         itors model confidence and pauses generation to
continuity, it requires synchronization mechanisms       read more context whenever uncertainty exceeds a
to prevent dependency leakage.                           safety margin, effectively adapting to the difficulty
                                                         of the incoming stream.
Grouped streaming Group streaming partitions
input and output tokens into separate groups, each       SFT-based Interaction Moving beyond manual
with independent attention relations and position        rules, supervised approaches leverage labeled data
IDs (Liu et al., 2024b; Tong et al., 2025a,b; Lin        to explicitly train the model to predict the opti-
                  Re-encoded streaming                     Concatenated streaming                   Interleaved streaming           Grouped streaming
                                                                                                                                  Output group
                                                                                                                                        p0             p1         p2
                     p1
                                                                                                      p1        p3         p5
                                                                  p1           p2         p3
                    Large Language Model


  Illustration
                     p0
                                                                                                                                      Large Language Model
                                                                Large Language Model
                     p1       p2      p3
                                                                                                       Large Language Model           p0         p1          p2


                    Large Language Model                          p0           p1         p2
                                                                                                                                  Input group
                                                                                                                                                       pk         pk+1
                                                                                                      p0   p1   p2   p3   p4
                     p0       p1      p2



                 Re-encode all past caches                 Concatenate the input and                                             Restrict attention within in-
  Attn.
                                                                                                   Interleave input and output
                 when new input arrives to                 output tokens into a com-                                             put and output groups to
                                                                                                   tokens on the timeline.
                 match pretraining.                        posite token per step.                                                match pretraining.
  Pos.           Reassign positions via full               Assign monotonic posi-                  Assign positions by inter-    Maintain separate posi-
                 re-encoding.                              tions over concatenation.               leaved time order.            tional spaces per group.

Table 1: Comparison of concurrent-streaming architecture adaptation methods from the perspectives of attention (Attn.) and
position (Pos.).     indicates the token generation direction, while      denotes attention dependencies.                                             blocks represent
the input stream, and blocks represent the output stream. p indicates the corresponding position ID.


 Streaming-In             Bound      Inc. Cxt.               Example methods
                                                                                               der streaming video inputs.
         Text          Memory        -     ✓     StreamingDialogue (Macháček et al., 2023)
        Audio       Causal, Memory   ✓     ✓         WhisperStreaming (Li et al., 2024b)
        Video          Memory        -     ✓          Timechat-online (Yao et al., 2025)
                                                                                               6     Streaming Applications and Tasks
Table 2: Summary of sequential streaming tasks. Incremen-                                      This section reviews the application-level tasks
tal encoding (Inc) and context management (Ctx) are the key
technical dimensions. The checkmark (✓) indicates the scope                                    enabled by streaming LLMs, building upon the
covered by existing research.                                                                  methodological taxonomy established in Sections
                                                                                               3–5. Notably, since output streaming is a universal
mal interaction timing. (1) In-context prediction                                              property of LLM-based generation, we concentrate
paradigm integrates decision-making directly into                                              on task settings where streaming arises from incre-
the autoregressive generation process (Chen et al.,                                            mental input, real-time interaction, or bidirectional
2024a; Koshkin et al., 2024b). Here, the LLM                                                   coupling between input and output.
is fine-tuned to emit special control tokens (e.g.,
<EOS> or <WAIT> ) alongside standard text. This                                                Sequential Streaming Tasks Sequential stream-
strategy unifies policy execution with language                                                ing tasks target long, unbounded input streams that
modeling, allowing the model to leverage its rea-                                              cannot be processed in a single pass due to resource
soning capabilities for control. (2) Auxiliary de-                                             limitations. For instance, streaming long video un-
cision employ auxiliary decision modules to de-                                                derstanding (Zhang et al., 2024b; Yao et al., 2025)
couple control from generation (Zhao et al., 2025b;                                            requires incremental video encoding, followed by
Chen et al., 2024b; Qian et al., 2025). This typically                                         immediate decoding upon query arrival. As sum-
involves training a lightweight classifier to output a                                         marized in Table 2, different modalities emphasize
binary decision. By isolating the interaction signal,                                          distinct technical components.
this approach allows for focused supervision on
                                                                                               Concurrent Streaming Tasks Concurrent
the decision boundary without interfering with the
                                                                                               streaming covers multimodal tasks that require
semantic distribution of the generated text.
                                                                                               simultaneous input reception and output generation.
RL-based Interaction RL-based policies model                                                   Based on processing depth, these tasks can be
interaction control as sequential decision-making,                                             divided into two levels. (1) Perception-Level
where the LLMs selects read or write actions                                                   (X → Y): Models focus on direct cross-modal
based on the current context (Wang et al., 2025c;                                              mappings with minimal latency, including
Cheng et al., 2025b; Xu et al., 2025e). Optimiz-                                               streaming translation (e.g., Seed LiveInterpret
ing quality–latency rewards enables the discovery                                              2.0 (Cheng et al., 2025b)), ASR/TTS (e.g.,
of non-trivial interaction patterns that are difficult                                         CosyVoice (Du et al., 2024)), real-time video
to encode with static rules. For example, MM-                                                  captioning (e.g., LiveCC (Chen et al., 2025a)),
Duet2 (Wang et al., 2025c) formulates proactive                                                and streaming QA (e.g., Qwen3-Omni (Xu et al.,
video interaction as an RL-driven control problem,                                             2025c)). (2) Cognition-Level (X → Z → Y):
enabling asynchronous perception and reaction un-                                              Tasks require maintaining and updating a latent
                         Modality     Paradigm   Interaction policy
    Task type   Level                                                                          Example methods
                         In     Out R. C. I. G. Rule SFT      RL
 Translation X → Y       T/S    T/S   ✓ ✓ ✓ ✓     ✓     ✓      ✓                  Seed LiveInterpret 2.0 (Cheng et al., 2025b)
  Detection X → Y       T/S/V    T    - - ✓ -     -     ✓      -                          FineHarm (Li et al., 2025i)
    ASR      X →Y         S      T    - - ✓ ✓     ✓     ✓      -          ReaLLM (Seide et al., 2024), Llama-omni (Fang et al., 2024)
    TTS      X →Y         T      S    - ✓ - ✓     ✓     ✓      -            Cosyvoice (Du et al., 2024), DSM (Zeghidour et al., 2025)
    QA       X →Y       T/S/V   T/S   - ✓ ✓ -     -     ✓      ✓      Qwen3-omni (Xu et al., 2025c), VideoLLM-online (Chen et al., 2024a)
 Description X → Y        V      T    - - ✓ ✓     ✓     ✓      -          LiveCC (Chen et al., 2025a), StreamMind (Ding et al., 2025b)
    VLA      X →Y         V      T    - - ✓ -     ✓     -      -        StreamVLN (Wei et al., 2025b), ActiveVLN (Zhang et al., 2025e)
 Reasoning X → Z        T/S/V   T/S   - - ✓ ✓     ✓     -      -                     StreamingThinker (Tong et al., 2025a)
             Z→Y        T/S/V   T/S   - - ✓ -     ✓     -      -                    AsyncReasoning (Yakushev et al., 2025)
 Tool usage X → Z       T/S/V    T    - - ✓ -     ✓     -      -          AViLA (Zhang et al., 2025a), StreamRAG (Arora et al., 2025)
             Z→Y        T/S/V    T    - - ✓ -     ✓     -      -             Conveyor (Xu et al., 2024), AsyncLM (Gim et al., 2024)


Table 3: Summary of concurrent streaming tasks and representative methods. Tasks are categorized by processing depth
(Level), where X → Y denotes direct mapping (perception) and X → Z → Y denotes intermediate processing with a latent state
Z (cognition). Modality: text (T), speech (S), vision (V). Streaming Paradigm: re-encoding (R), Concatenated (C), Interactive
(I), Group (G). Interaction Policy: Rule-based (Rule), SFT-based (SFT), and RL-based (RL). The checkmark (✓) indicates the
scope covered by existing research.


state Z to support complex behaviors such as                            Extending streaming LLMs to additional modali-
streaming reasoning (e.g., StreamingThinker (Tong                       ties requires transcending these limitations toward
et al., 2025a)) and streaming tool usage (e.g.,                         complex, omni-modal continuous streams (e.g.,
AViLA (Zhang et al., 2025a)). Here, the latent state                    parallel video-audio streams) to achieve real-time
decouples immediate perception from final output                        streaming multimodal understanding and genera-
generation. We summarize the corresponding                              tion in highly dynamic environments. (2) Expan-
technical categories of these tasks in Table 3.                         sion of Concurrency Levels. A promising direction
                                                                        is to expand current streaming LLMs from two-
7      Future Directions                                                level perceptual concurrency (e.g., “listen-while-
To provide a comprehensive roadmap, we catego-                          speaking” and “read-while-thinking”) to deeper,
rize future research into two complementary per-                        multi-level asynchronous processing. This includes
spectives: the technical level (i.e., how to build                      3-level streaming (introducing streaming “perceiv-
better streaming models) and the application level                      ing, reasoning, and generation”) and 4-level stream-
(i.e., how to apply streaming models).                                  ing (introducing concurrent “perceiving, reasoning,
                                                                        tool-using, and generation”) to achieve true multi-
Technical Level (1) Efficient Streaming LLMs.                           stream intelligence. (3) Expansion of Stream-
Efficiency under strict latency and memory con-                         ing Tasks. The application of streaming LLMs
straints remains a core challenge, involving in-                        is expected to shift from simple, passive responses
cremental encoding, decoding acceleration, and                          toward complex proactive interactions and long-
long-term context management. (2) Alternative                           context engagements. Advancing these capabilities
Concurrent Streaming Paradigms. Beyond inter-                           involves empowering models to actively initiate
leaved and group-based strategies, more effective                       interventions and maintain long-term memory, ulti-
streaming paradigms remain to be explored. In                           mately achieving brain-like streaming intelligence.
particular, extending streaming interaction to semi-
autoregressive or block-wise generation frame-                          8    Conclusion
works presents a promising yet underexplored di-
rection. (3) Proactive Interaction Policies. De-                        This survey presents a unified view of stream-
signing interaction policies that adaptively balance                    ing LLMs by clarifying their definitions and orga-
reading and generation is essential for real-time                       nizing existing approaches into output-streaming,
streaming performance. (4) Interpretability. The                        sequential-streaming, and concurrent-streaming
behavioral dynamics of LLMs in interactive stream-                      paradigms based on data flow and interaction con-
ing settings remain largely unexplored, calling for                     currency. We review representative methodologies
greater interpretability.                                               and application scenarios, and discuss the funda-
                                                                        mental challenges posed by real-time and interac-
Application Level (1) Expansion of Streaming                            tive settings. We hope this work serves as a concise
Modalities. Current streaming LLMs primarily fo-                        reference and a conceptual foundation for future
cus on text, audio, and basic video interactions.                       research on streaming intelligence.
Limitations                                               Zalán Borsos, Raphaël Marinier, Damien Vincent, Eu-
                                                            gene Kharitonov, Olivier Pietquin, Matt Sharifi,
This survey focuses on clarifying the conceptual            Dominik Roblek, Olivier Teboul, David Grangier,
landscape of Streaming Large Language Models                Marco Tagliasacchi, et al. 2023a. Audiolm: a
through unified definitions, paradigms, and repre-          language modeling approach to audio generation.
                                                            IEEE/ACM transactions on audio, speech, and lan-
sentative methods. As a result, it does not aim             guage processing, 31:2523–2533.
to provide an exhaustive comparison of all exist-
ing implementations or a comprehensive empirical          Zalán Borsos, Matt Sharifi, Damien Vincent, Eugene
                                                            Kharitonov, Neil Zeghidour, and Marco Tagliasacchi.
evaluation across tasks and systems. Moreover, our
                                                            2023b. Soundstorm: Efficient parallel audio genera-
discussion primarily centers on high-level design           tion. arXiv preprint arXiv:2305.09636.
principles and paradigms, leaving detailed system-
level optimizations and deployment-specific con-          Davide Caffagni, Federico Cocchi, Luca Barsellotti,
                                                            Nicholas Moratelli, Sara Sarto, Lorenzo Baraldi, Mar-
siderations for future studies.                             cella Cornia, and Rita Cucchiara. 2024. The revolu-
                                                            tion of multimodal large language models: a survey.
                                                            arXiv preprint arXiv:2402.12451.
References
                                                          Tianle Cai, Yuhong Li, Zhengyang Geng, Hongwu Peng,
Victor Agostinelli, Max Wild, Matthew Raffel, Kazi           Jason D Lee, Deming Chen, and Tri Dao. 2024a.
  Fuad, and Lizhong Chen. 2024. Simul-llm: A frame-          Medusa: Simple llm inference acceleration frame-
  work for exploring high-quality simultaneous trans-        work with multiple decoding heads. arXiv preprint
  lation with large language models. In Proceedings          arXiv:2401.10774.
  of the 62nd annual meeting of the association for
  computational linguistics (volume 1: long papers),      Zefan Cai, Yichi Zhang, Bofei Gao, Yuliang Liu,
  pages 10530–10541.                                        Yucheng Li, Tianyu Liu, Keming Lu, Wayne Xiong,
                                                            Yue Dong, Junjie Hu, and Xiao Wen. 2024b. Pyra-
Elad Amrani, Leonid Karlinsky, and Alex Bron-               midkv: Dynamic kv cache compression based on
  stein. 2025. Sample-and parameter-efficient auto-         pyramidal information funneling. arXiv preprint
  regressive image models. In Proceedings of the Com-       arXiv:2406.02069.
  puter Vision and Pattern Recognition Conference,
  pages 30127–30136.                                      Huiwen Chang, Han Zhang, Jarred Barber,
                                                            AJ Maschinot, Jose Lezama, Lu Jiang, Ming-
Chenxin An, Fei Huang, Jun Zhang, Shansan Gong,             Hsuan Yang, Kevin Murphy, William T Freeman,
  Xipeng Qiu, Chang Zhou, and Lingpeng Kong. 2024.          Michael Rubinstein, et al. 2023. Muse: Text-to-
  Training-free long-context scaling of large language      image generation via masked generative transformers.
  models. arXiv preprint arXiv:2402.17463.                  arXiv preprint arXiv:2301.00704.
Siddhant Arora, Haidar Khan, Kai Sun, Xin Luna Dong,
                                                          Huiwen Chang, Han Zhang, Lu Jiang, Ce Liu, and
   Sajal Choudhary, Seungwhan Moon, Xinyuan Zhang,
                                                            William T Freeman. 2022. Maskgit: Masked gen-
  Adithya Sagar, Surya Teja Appini, Kaushik Patnaik,
                                                            erative image transformer. In Proceedings of the
   et al. 2025. Stream rag: Instant and accurate spoken
                                                            IEEE/CVF conference on computer vision and pat-
   dialogue systems with streaming tool usage. arXiv
                                                            tern recognition, pages 11315–11325.
   preprint arXiv:2510.02044.
Marianne Arriola, Aaron Gokaslan, Justin T Chiu, Zhi-     Dibyadip Chatterjee, Edoardo Remelli, Yale Song,
 han Yang, Zhixuan Qi, Jiaqi Han, Subham Sekhar             Bugra Tekin, Abhay Mittal, Bharat Bhatnagar,
 Sahoo, and Volodymyr Kuleshov. 2025. Block                 Necati Cihan Camgoz, Shreyas Hampali, Eric Sauser,
 diffusion: Interpolating between autoregressive            Shugao Ma, et al. 2025. Streaming videollms for
 and diffusion language models. arXiv preprint              real-time procedural video understanding. In Pro-
 arXiv:2503.09573.                                          ceedings of the IEEE/CVF International Conference
                                                            on Computer Vision, pages 22586–22598.
Jacob Austin, Daniel D. Johnson, Jonathan Ho, Daniel
   Tarlow, and Aaron van den Oord. 2021. Structured       Joya Chen, Zhaoyang Lv, Shiwei Wu, Kevin Qinghong
   denoising diffusion models in discrete state-spaces.     Lin, Chenan Song, Difei Gao, Jia-Wei Liu, Ziteng
   arXiv preprint arXiv:2107.03006.                         Gao, Dongxing Mao, and Mike Zheng Shou. 2024a.
                                                            Videollm-online: Online video large language
Richard He Bai, Zijin Gu, Tatiana Likhomanenko, and         model for streaming video. In Proceedings of the
  Navdeep Jaitly. 2025. Speakstream: Streaming              IEEE/CVF Conference on Computer Vision and Pat-
  text-to-speech with interleaved data. arXiv preprint      tern Recognition, pages 18407–18418.
  arXiv:2505.19206.
                                                          Joya Chen, Ziyun Zeng, Yiqi Lin, Wei Li, Zejun Ma,
Richard He Bai, Tatiana Likhomanenko, Ruixiang              and Mike Zheng Shou. 2025a. Livecc: Learning
  Zhang, Zijin Gu, Zakaria Aldeneh, and Navdeep             video llm with streaming speech transcription at scale.
  Jaitly. 2024. dmel: Speech tokenization made simple.      In Proceedings of the Computer Vision and Pattern
  arXiv preprint arXiv:2407.15835.                          Recognition Conference, pages 29083–29095.
Xinjie Chen, Kai Fan, Wei Luo, Linlin Zhang, Libo       Marco Comunità, Zhi Zhong, Akira Takahashi, Shiqi
  Zhao, Xinggao Liu, and Zhongqiang Huang. 2024b.        Yang, Mengjie Zhao, Koichi Saito, Yukara Ikemiya,
  Divergence-guided simultaneous speech translation.     Takashi Shibuya, Shusuke Takahashi, and Yuki Mit-
  In Proceedings of the AAAI Conference on Artificial    sufuji. 2024. Specmaskgit: Masked generative mod-
  Intelligence, volume 38, pages 17799–17807.            eling of audio spectrograms for efficient audio syn-
                                                         thesis and beyond. arXiv preprint arXiv:2406.17672.
Xueyi Chen, Keda Tao, Kele Shao, and Huan Wang.
  2025b. Streamingtom: Streaming token compression      Anonymous Contributors. 2024. Llamagen: Large lan-
  for efficient video understanding. arXiv preprint       guage model for continuous image generation. Open-
  arXiv:2510.18269.                                       source implementation; inspired by VQ-less LLM
                                                          architecture for image generation.
Yilong Chen, Xiang Bai, Zhibin Wang, Chengyu Bai,       Trung Dang, David Aponte, Dung Tran, and Kazuhito
  Yuhan Dai, Ming Lu, and Shanghang Zhang. 2025c.         Koishida. 2024. Livespeech: Low-latency zero-shot
  Streamkv: Streaming video question-answering with       text-to-speech via autoregressive modeling of audio
  segment-based kv cache retrieval and compression.       discrete codes. arXiv preprint arXiv:2406.02897.
  arXiv preprint arXiv:2511.07278.
                                                        Pierre V Dantas, Lucas C Cordeiro, and Waldir SS Ju-
Zhe Chen, Jiannan Wu, Wenhai Wang, Weijie Su, Guo          nior. 2025. A review of state-of-the-art techniques
  Chen, Sen Xing, Muyan Zhong, Qinglong Zhang,             for large language model compression. Complex &
  Xizhou Zhu, Lewei Lu, et al. 2024c. Internvl: Scal-      Intelligent Systems, 11(9):407.
  ing up vision foundation models and aligning for
  generic visual-linguistic tasks. In Proceedings of    DeepSeek-AI, Aixin Liu, Bei Feng, Bing Xue, Bingx-
  the IEEE/CVF conference on computer vision and          uan Wang, et al. 2024. Deepseek-v3 technical report.
  pattern recognition, pages 24185–24198.                 arXiv preprint arXiv:2412.19437.

Zhuohan Chen, Yizhe Zhang, Ziyang Chen, Yuhao           Alexandre Défossez, Laurent Mazaré, Manu Orsini,
  Lin, Songlin Wang, Hao Li, Kurt Keutzer, Joseph E       Amélie Royer, Patrick Pérez, Hervé Jégou, Edouard
  Gonzalez, Michael W Mahoney, and Ion Stoica.            Grave, and Neil Zeghidour. 2024. Moshi: a speech-
  2023. Accelerating large language model decod-          text foundation model for real-time dialogue. arXiv
  ing with speculative sampling. arXiv preprint           preprint arXiv:2410.00037.
  arXiv:2302.01318.                                     Luciano Del Corro, Allie Del Giorno, Sahaj Agarwal,
                                                          Bin Yu, Ahmed Awadallah, and Subhabrata Mukher-
Jian Cheng, Haidong Kang, Yuxin Shao, Nan Li,             jee. 2023. Skipdecode: Autoregressive skip decoding
   Pengjun Chen, Rui Wang, Saiqin Long, Xiaochun          with batching and caching for efficient llm inference.
   Yang, and Lianbo Ma. 2025a. Survey on efficient        arXiv preprint arXiv:2307.02628.
   large language models: Principles, algorithms, ap-
   plications, and open issues. IEEE Transactions on    Keqi Deng, Wenxi Chen, Xie Chen, and Phil Woodland.
   Neural Networks and Learning Systems.                  2025. Simuls2s-llm: Unlocking simultaneous infer-
                                                          ence of speech llms for speech-to-speech translation.
Shanbo Cheng, Yu Bao, Zhichao Huang, Yu Lu,               In Proceedings of the 63rd Annual Meeting of the
  Ningxin Peng, Lu Xu, Runsheng Yu, Rong Cao,             Association for Computational Linguistics (Volume
  Yujiao Du, Ting Han, et al. 2025b. Seed livein-         1: Long Papers), pages 16718–16734.
  terpret 2.0: End-to-end simultaneous speech-to-
  speech translation with your voice. arXiv preprint    Ding Ding, Zeqian Ju, Yichong Leng, Songxiang Liu,
  arXiv:2507.17527.                                       Tong Liu, Zeyu Shang, Kai Shen, Wei Song, Xu Tan,
                                                          Heyi Tang, et al. 2025a. Kimi-audio technical report.
Ethan Chern, Jiadi Su, Yan Ma, and Pengfei Liu. 2024.     arXiv preprint arXiv:2504.18425.
  Anole: An open, autoregressive, native large multi-
  modal models for interleaved image-text generation.   Xin Ding, Hao Wu, Yifan Yang, Shiqi Jiang, Qianxi
  arXiv preprint arXiv:2407.06135.                        Zhang, Donglin Bai, Zhibo Chen, and Ting Cao.
                                                          2025b. Streammind: Unlocking full frame rate
                                                          streaming video dialogue through event-gated cog-
Cheng-Han Chiang, Xiaofei Wang, Linjie Li, Chung-
                                                          nition. In Proceedings of the IEEE/CVF Interna-
  Ching Lin, Kevin Lin, Shujie Liu, Zhendong Wang,
                                                          tional Conference on Computer Vision, pages 13448–
  Zhengyuan Yang, Hung-yi Lee, and Lijuan Wang.
                                                          13459.
  2025a. Shanks: Simultaneous hearing and think-
  ing for spoken language models. arXiv preprint        Haotian Dong, Ye Li, Rongwei Lu, Chen Tang, Shu-
  arXiv:2510.06917.                                       Tao Xia, and Zhi Wang. 2025. Vvs: Accelerating
                                                          speculative decoding for visual autoregressive gener-
Cheng-Han Chiang, Xiaofei Wang, Linjie Li, Chung-         ation via partial verification skipping. arXiv preprint
  Ching Lin, Kevin Lin, Shujie Liu, Zhendong Wang,        arXiv:2511.13587.
  Zhengyuan Yang, Hung-yi Lee, and Lijuan Wang.
  2025b. Stitch: Simultaneous thinking and talking      Alexey Dosovitskiy. 2020. An image is worth 16x16
  with chunked reasoning for spoken language models.      words: Transformers for image recognition at scale.
  arXiv preprint arXiv:2507.15375.                        arXiv preprint arXiv:2010.11929.
Zhihao Du, Yuxuan Wang, Qian Chen, Xian Shi, Xiang         Shenghao Fu, Qize Yang, Yuan-Ming Li, Yi-Xing Peng,
  Lv, Tianyu Zhao, Zhifu Gao, Yexin Yang, Changfeng          Kun-Yu Lin, Xihan Wei, Jian-Fang Hu, Xiaohua Xie,
  Gao, Hui Wang, et al. 2024. Cosyvoice 2: Scalable          and Wei-Shi Zheng. 2025c. Vispeak: Visual instruc-
  streaming speech synthesis with large language mod-        tion feedback in streaming videos. arXiv preprint
  els. arXiv preprint arXiv:2412.10117.                      arXiv:2503.12769.

Siqi Fan, Xin Jiang, Xiang Li, Xuying Meng, Peng           Yu Fu, Zefan Cai, Abedelkadir Asi, Wayne Xiong, Yue
  Han, Shuo Shang, Aixin Sun, Yequan Wang, and               Dong, and Wen Xiao. 2024b. Not all heads mat-
  Zhongyuan Wang. 2024. Not all layers of llms               ter: A head-level kv cache compression method with
  are necessary during inference. arXiv preprint             integrated retrieval and reasoning. arXiv preprint
  arXiv:2403.02181.                                          arXiv:2410.19258.
                                                           Xiangxiang Gao, Weisheng Xie, Yiwei Xiang, and
Yingqi Fan, Anhao Zhao, Jinlan Fu, Junlong Tong, Hui         Feng Ji. 2025. Falcon: Faster and parallel inference
  Su, Yijie Pan, Wei Zhang, and Xiaoyu Shen. 2025.           of large language models through enhanced semi-
  Visipruner: Decoding discontinuous cross-modal dy-         autoregressive drafting and custom-designed decod-
  namics for efficient multimodal llms. In Proceedings       ing tree. In Proceedings of the AAAI Conference
  of the 2025 Conference on Empirical Methods in             on Artificial Intelligence, volume 39, pages 23933–
  Natural Language Processing, pages 18896–18913.            23941.
Qingkai Fang, Shoutao Guo, Yan Zhou, Zhengrui Ma,          Gemma Team. 2024. Gemma: Open models based
  Shaolei Zhang, and Yang Feng. 2024. Llama-omni:            on gemini research and technology. arXiv preprint
  Seamless speech interaction with large language mod-       arXiv:2403.08295.
  els. arXiv preprint arXiv:2409.06666.
                                                           Marjan Ghazvininejad, Omer Levy, Yinhan Liu, and
Qingkai Fang, Yan Zhou, Shoutao Guo, Shaolei Zhang,         Luke Zettlemoyer. 2019. Mask-predict: Parallel de-
  and Yang Feng. 2025. Llama-omni2: Llm-based real-         coding of conditional masked language models. In
  time spoken chatbot with autoregressive streaming         Proceedings of EMNLP-IJCNLP.
  speech synthesis. arXiv preprint arXiv:2505.02625.       In Gim, Seung-seob Lee, and Lin Zhong. 2024. Asyn-
                                                              chronous llm function calling. arXiv preprint
Yuan Feng, Junlin Lv, Yukun Cao, Xike Xie, and                arXiv:2412.07017.
  S Kevin Zhou. 2024. Ada-kv: Optimizing kv cache
  eviction by adaptive budget allocation for efficient     Team GLM, Aohan Zeng, Bin Xu, Bowen Wang, Chen-
  llm inference. arXiv preprint arXiv:2407.11550.            hui Zhang, Da Yin, Dan Zhang, Diego Rojas, Guanyu
                                                             Feng, Hanlin Zhao, et al. 2024. Chatglm: A family
Yuan Feng, Junlin Lv, Yukun Cao, Xike Xie, and               of large language models from glm-130b to glm-4 all
  S Kevin Zhou. 2025. Identify critical kv cache in          tools. arXiv preprint arXiv:2406.12793.
  llm inference from an output perturbation perspec-
  tive. arXiv preprint arXiv:2502.03805.                   Fabian Gloeckle, Badr Youbi Idrissi, Baptiste Rozière,
                                                             David Lopez-Paz, and Gabriel Synnaeve. 2024. Bet-
                                                             ter & faster large language models via multi-token
Markus Frohmann, Igor Sterner, Ivan Vulić, Benjamin
                                                             prediction. arXiv preprint arXiv:2404.19737.
 Minixhofer, and Markus Schedl. 2024. Segment
 any text: A universal approach for robust, efficient      Chengyue Gong, Xuezhe Feng, Guanyi Qin, Yixin Liu,
 and adaptable sentence segmentation. arXiv preprint         et al. 2022. Diffuseq: Sequence to sequence text
 arXiv:2406.16678.                                           generation with diffusion models. arXiv preprint
                                                             arXiv:2210.08933.
Biao Fu, Kai Fan, Minpeng Liao, Yidong Chen,
  Xiaodong Shi, and Zhongqiang Huang. 2024a.               Alex Graves. 2012. Connectionist temporal classifica-
  wav2vec-s: Adapting pre-trained speech models for          tion. In Supervised sequence labelling with recurrent
  streaming. In Findings of the Association for Compu-       neural networks, pages 61–93. Springer.
  tational Linguistics: ACL 2024, pages 11465–11480.
                                                           Jiatao Gu, Changhan Wang, and Jake Zhao. 2019. Lev-
Biao Fu, Minpeng Liao, Kai Fan, Chengxi Li, Liang             enshtein transformer. In Advances in Neural Infor-
  Zhang, Yidong Chen, and Xiaodong Shi. 2025a.                mation Processing Systems (NeurIPS).
  Llms can achieve high-quality simultaneous machine       Dake Guo, Jixun Yao, Linhan Ma, He Wang, and Lei
  translation as efficiently as offline. In Findings of      Xie. 2025. Streamflow: Streaming flow matching
  the Association for Computational Linguistics: ACL         with block-wise guided attention mask for speech
  2025, pages 20372–20395.                                   token decoding. arXiv preprint arXiv:2506.23986.
Biao Fu, Donglei Yu, Minpeng Liao, Chengxi Li, Yi-         Hao-Han Guo, Yao Hu, Kun Liu, Fei-Yu Shen, Xu Tang,
  dong Chen, Kai Fan, and Xiaodong Shi. 2025b. Ef-           Yi-Chen Wu, Feng-Long Xie, Kun Xie, and Kai-Tuo
  ficient and adaptive simultaneous speech translation       Xu. 2024a. Fireredtts: A foundation text-to-speech
  with fully unidirectional architecture. arXiv preprint     framework for industry-level generative speech appli-
  arXiv:2504.11809.                                          cations. arXiv preprint arXiv:2409.03283.
Shoutao Guo, Shaolei Zhang, and Yang Feng. 2024b.            Hyeonbin Hwang, Byeongguk Jeon, Seungone Kim,
  Decoder-only streaming transformer for simultane-            Jiyeon Kim, Hoyeon Chang, Sohee Yang, Seungpil
  ous translation. In Proceedings of the 62nd Annual           Won, Dohaeng Lee, Youbin Ahn, and Minjoon Seo.
  Meeting of the Association for Computational Lin-            2025. Let’s predict sentence by sentence. arXiv
  guistics (Volume 1: Long Papers), pages 8851–8864.           preprint arXiv:2505.22202.
Shoutao Guo, Shaolei Zhang, Zhengrui Ma, Min Zhang,          Javier Iranzo-Sánchez, Jorge Iranzo-Sánchez, Adrià
  and Yang Feng. 2024c. Sillm: Large language mod-              Giménez, Jorge Civera, and Alfons Juan. 2024.
  els for simultaneous machine translation. arXiv               Segmentation-free streaming machine translation.
  preprint arXiv:2402.13036.                                   Transactions of the Association for Computational
                                                               Linguistics, 12:1104–1121.
Jian Han, Jinlai Liu, Yi Jiang, Bin Yan, Yuqi Zhang, Ze-
   huan Yuan, Bingyue Peng, and Xiaobing Liu. 2025.          Doohyuk Jang, Sihwan Park, June Yong Yang, Yeon-
   Infinity: Scaling bitwise autoregressive modeling for       sung Jung, Jihun Yun, Souvik Kundu, Sung-Yub Kim,
   high-resolution image synthesis. In Proceedings of          and Eunho Yang. 2024. Lantern: Accelerating visual
   the Computer Vision and Pattern Recognition Con-            autoregressive models with relaxed speculative de-
   ference, pages 15733–15744.                                 coding. arXiv preprint arXiv:2410.03355.
Xiaochuang Han, Sachin Kumar, and Yulia Tsvetkov.            Dongya Jia, Zhuo Chen, Jiawei Chen, Chenpeng Du,
  2023. Ssd-lm: Semi-autoregressive simplex-based              Jian Wu, Jian Cong, Xiaobin Zhuang, Chumin Li,
  diffusion language model for text generation and             Zhen Wei, Yuping Wang, and Yuxuan Wang. 2025.
  modular control. In Proceedings of the 61st An-              Ditar: Diffusion transformer autoregressive model-
  nual Meeting of the Association for Computational            ing for speech generation. In Proceedings of the
  Linguistics (Volume 1: Long Papers), pages 11575–            42nd International Conference on Machine Learn-
  11596.                                                       ing, volume 267 of Proceedings of Machine Learning
                                                               Research, pages 27255–27270.
Jiadong Hao, Bohan Zhang, Yuchen Lu, Chengcheng
   Zhang, and Kunda Yang. Stylle: Style learning and         Xinqi Jin, Hanxun Yu, Bohan Yu, Kebin Liu, Jian
   latent editing for stylized text and speech generation.     Liu, Keda Tao, Yixuan Pei, Huan Wang, Fan
                                                               Dang, Jiangchuan Liu, et al. 2025. Streamingas-
Yefei He, Luoming Zhang, Weijia Wu, Jing Liu, Hong             sistant: Efficient visual token pruning for acceler-
  Zhou, and Bohan Zhuang. 2024. Zipcache: Accu-                ating online video understanding. arXiv preprint
  rate and efficient kv cache quantization with salient        arXiv:2512.12560.
  token identification. Advances in Neural Information
  Processing Systems, 37:68287–68307.                        Sehoon Kim, Karttikeya Mangalam, Suhong Moon, Ji-
                                                               tendra Malik, Michael W Mahoney, Amir Gholami,
Coleman Hooper, Sehoon Kim, Hiva Mohammadzadeh,                and Kurt Keutzer. 2023. Speculative decoding with
  Michael W Mahoney, Yakun S Shao, Kurt Keutzer,               big little decoder. Advances in Neural Information
  and Amir Gholami. 2024. Kvquant: Towards 10                  Processing Systems, 36:39236–39256.
  million context length llm inference with kv cache
  quantization. Advances in Neural Information Pro-          Dan Kondratyuk, Lijun Yu, Xiuye Gu, Jose Lezama,
  cessing Systems, 37:1270–1303.                               Jonathan Huang, Grant Schindler, Rachel Hornung,
                                                               Vighnesh Birodkar, Jimmy Yan, Ming-Chang Chiu,
Chihan Huang and Hao Tang. 2025. Ctrldiff: Boost-              et al. 2024. Videopoet: A large language model for
  ing large diffusion language models with dynamic             zero-shot video generation. In International Con-
  block prediction and controllable generation. arXiv          ference on Machine Learning, pages 25105–25124.
  preprint arXiv:2505.14455.                                   PMLR.
Kuan-Po Huang, Shu-wen Yang, Huy Phan, Bo-Ru Lu,             Roman Koshkin, Katsuhito Sudoh, and Satoshi Naka-
  Byeonggeun Kim, Sashank Macha, Qingming Tang,                mura. 2024a. Llms are zero-shot context-aware si-
  Shalini Ghosh, Hung-yi Lee, Chieh-Chi Kao, et al.            multaneous translators. In Proceedings of the 2024
  2025a. Impact: Iterative mask-based parallel de-             Conference on Empirical Methods in Natural Lan-
  coding for text-to-audio generation with diffusion           guage Processing, pages 1192–1207.
  modeling. arXiv preprint arXiv:2506.00736.
                                                             Roman Koshkin, Katsuhito Sudoh, and Satoshi Naka-
Wenxuan Huang, Zijie Zhai, Yunhang Shen, Shaosheng             mura. 2024b. Transllama: Llm-based simultaneous
  Cao, Fei Zhao, Xiangfeng Xu, Zheyu Ye, Yao                   translation system. arXiv preprint arXiv:2402.04636.
  Hu, and Shaohui Lin. 2024. Dynamic-llava: Ef-
  ficient multimodal large language models via dy-           Pin-Jui Ku, He Huang, Jean-Marie Lemercier, Sub-
  namic vision-language context sparsification. arXiv          ham Sekhar Sahoo, Zhehuai Chen, and Ante Jukić.
  preprint arXiv:2412.00876.                                   2025. Discrete diffusion for generative model-
                                                               ing of text-aligned speech tokens. arXiv preprint
Xiaohu Huang, Hao Zhou, and Kai Han. 2025b.                    arXiv:2509.20060.
  Prunevid: Visual token pruning for efficient video
  large language models. In Findings of the Associa-         Taku Kudo. 2018. Subword regularization: Improving
  tion for Computational Linguistics: ACL 2025, pages          neural network translation models with multiple sub-
  19959–19973.                                                 word candidates. arXiv preprint arXiv:1804.10959.
Taku Kudo and John Richardson. 2018. Sentencepiece:       Kunjun Li, Zigeng Chen, Cheng-Yen Yang, and Jenq-
  A simple and language independent subword tok-            Neng Hwang. 2025e. Memory-efficient visual autore-
  enizer and detokenizer for neural text processing.        gressive modeling with scale-aware kv cache com-
  arXiv preprint arXiv:1808.06226.                          pression. arXiv preprint arXiv:2505.19602.

Chenyang Le, Bing Han, Jinshun Li, Songyong Chen,         Ruanjun Li, Yuedong Tan, Yuanming Shi, and Jiawei
  and Yanmin Qian. 2025. Simulmega: Moe routers             Shao. 2025f. Videoscan: Enabling efficient stream-
  are advanced policy makers for simultaneous speech        ing video understanding via frame-level semantic
  translation. arXiv preprint arXiv:2509.01200.             carriers. arXiv preprint arXiv:2503.09387.

Matthew Le, Apoorv Vyas, Bowen Shi, Brian Karrer,         Shufan Li, Konstantinos Kallidromitis, Hritik Bansal,
 Leda Sari, Rashel Moritz, Mary Williamson, Vimal           Akash Gokul, Yusuke Kato, Kazuki Kozuka, Ja-
 Manohar, Yossi Adi, Jay Mahadeokar, et al. 2023.           son Kuen, Zhe Lin, Kai-Wei Chang, and Aditya
 Voicebox: Text-guided multilingual universal speech        Grover. 2025g. Lavida: A large diffusion language
 generation at scale. Advances in neural information        model for multimodal understanding. arXiv preprint
 processing systems, 36:14005–14034.                        arXiv:2505.16839.
Haodong Lei, Hongsong Wang, Xin Geng, Liang Wang,         Wei Li, Bing Hu, Rui Shao, Leyang Shen, and Liqiang
  and Pan Zhou. 2025. Fast inference of visual autore-      Nie. 2025h. Lion-fs: Fast & slow video-language
  gressive model with adjacency-adaptive dynamical          thinker as online video assistant. In Proceedings of
  draft trees. arXiv preprint arXiv:2512.21857.             the IEEE/CVF Conference on Computer Vision and
                                                           Pattern Recognition, pages 3240–3251.
Yaniv Leviathan, Matan Kalman, and Yossi Matias.
  2023. Fast inference from transformers via spec-        Xiang Lisa Li, John Thickstun Zhao, James Diffender-
  ulative decoding. In Proceedings of the 40th Interna-     fer, Xuezhe He, Percy Liang, and Graham Neubig.
  tional Conference on Machine Learning (ICML).             2022. Diffusion-LM improves controllable text gen-
                                                            eration. In Advances in Neural Information Process-
Bohan Li, Zhihan Li, Haoran Wang, Hanglei Zhang,            ing Systems (NeurIPS).
  Yiwei Guo, Hankun Wang, Xie Chen, and Kai Yu.
  2025a. Robust and efficient autoregressive speech
                                                          Yang Li, Qiang Sheng, Yehan Yang, Xueyao Zhang,
  synthesis with dynamic chunk-wise prediction policy.
                                                            and Juan Cao. 2025i. From judgment to interference:
  arXiv preprint arXiv:2506.22023.
                                                            Early stopping llm harmful outputs via streaming con-
                                                            tent monitoring. arXiv preprint arXiv:2506.09996.
Bohan Li, Hankun Wang, Situo Zhang, Yiwei Guo,
  and Kai Yu. 2025b. Fast and high-quality auto-
  regressive speech synthesis via speculative decoding.   Ying Li, chengfei lv, and Huan Wang. 2025j. Freqexit:
  In ICASSP 2025-2025 IEEE International Confer-            Enabling early-exit inference for visual autoregres-
  ence on Acoustics, Speech and Signal Processing           sive models via frequency-aware guidance. In The
  (ICASSP), pages 1–5. IEEE.                                Thirty-ninth Annual Conference on Neural Informa-
                                                            tion Processing Systems.
Han Li, Xinyu Peng, Yaoming Wang, Zelin Peng,
  Xin Chen, Rongxiang Weng, Jingang Wang, Xun-            Yuhong Li, Yingbing Huang, Bowen Yang, Bharat
  liang Cai, Wenrui Dai, and Hongkai Xiong. 2025c.          Venkitesh, Acyr Locatelli, Hanchen Ye, Tianle Cai,
  Onecat: Decoder-only auto-regressive model for uni-       Patrick Lewis, and Deming Chen. 2024c. Snapkv:
  fied understanding and generation. arXiv preprint         Llm knows what you are looking for before gener-
  arXiv:2509.03498.                                         ation. Advances in Neural Information Processing
                                                            Systems, 37:22947–22970.
Haoyang Li, Yiming Li, Anxin Tian, Tianhao Tang,
  Zhanchao Xu, Xuejia Chen, Nicole Hu, Wei Dong,          Yuhui Li, Fangyun Wei, Chao Zhang, and Hongyang
  Qing Li, and Lei Chen. 2024a. A survey on large           Zhang. 2024d. Eagle-2: Faster inference of language
  language model acceleration based on kv cache man-        models with dynamic draft trees. arXiv preprint
  agement. arXiv preprint arXiv:2412.19442.                 arXiv:2406.16858.

Jia-Nan Li, Quan Tu, Cunli Mao, Zhengtao Yu, Ji-Rong      Zinuo Li, Xian Zhang, Yongxin Guo, Mohammed Ben-
   Wen, and Rui Yan. 2024b. Streamingdialogue: Pro-         namoun, Farid Boussaid, Girish Dwivedi, Luqi Gong,
   longed dialogue learning via long context compres-       and Qiuhong Ke. 2025k. Watch and listen: Under-
   sion with minimal losses. Advances in Neural Infor-      standing audio-visual-speech moments with multi-
   mation Processing Systems, 37:86074–86101.               modal llm. arXiv preprint arXiv:2505.18110.

Jiajun Li, Yue Ma, Xinyu Zhang, Qingyan Wei, Songhua      Mengqi Liao, Lu Wang, Chaoyun Zhang, Zekai Shen,
   Liu, and Linfeng Zhang. 2025d. Skipvar: Ac-             Xiaowei Mao, Si Qin, Qingwei Lin, Saravan Rajmo-
   celerating visual autoregressive modeling via adap-     han, Dongmei Zhang, and Huaiyu Wan. 2025. G-KV:
   tive frequency-aware skipping. arXiv preprint           Decoding-time KV cache eviction with global atten-
   arXiv:2506.08908.                                       tion. arXiv preprint arXiv:2512.00504.
Junyan Lin, Junlong Tong, Hao Wu, Jialiang Zhang,             Chunkkv: Semantic-preserving kv cache compres-
  Jinming Liu, Xin Jin, and Xiaoyu Shen. 2026. Speak          sion for efficient long-context llm inference. arXiv
  while watching: Unleashing true real-time video un-         preprint arXiv:2502.00299.
  derstanding capability of multimodal large language
  models. arXiv preprint arXiv:2601.06843.                  Yiheng Liu, Liao Qu, Huichao Zhang, Xu Wang,
                                                              Yi Jiang, Yiming Gao, Hu Ye, Xian Li, Shuai Wang,
Zijian Lin, Yang Zhang, Yougen Yuan, Yuming Yan,              Daniel K Du, et al. 2025h. Detailflow: 1d coarse-to-
   Jinjiang Liu, Zhiyong Wu, Pengfei Hu, and Qun Yu.          fine autoregressive image generation via next-detail
   2025. Accelerating autoregressive speech synthesis         prediction. arXiv preprint arXiv:2505.21473.
   inference with speech speculative decoding. arXiv
   preprint arXiv:2505.15380.                               Yuxuan Liu et al. 2024c. Kivi: A tuning-free asymmet-
                                                              ric 2-bit quantization for KV cache. arXiv preprint
Aiwei Liu, Minghua He, Shaoxun Zeng, Sijun Zhang,             arXiv:2402.02750.
  Linhao Zhang, Chuhan Wu, Wei Jia, Yuan Liu,
  Xiao Zhou, and Jie Zhou. 2025a. Wedlm: Rec-               Zichang Liu, Aditya Desai, Fangshuo Liao, Weitao
  onciling diffusion language models with standard            Wang, Victor Xie, Zhaozhuo Xu, Anastasios Kyril-
  causal attention for fast inference. arXiv preprint         lidis, and Anshumali Shrivastava. 2023. Scis-
  arXiv:2512.22737.                                           sorhands: Exploiting the persistence of importance
                                                              hypothesis for llm kv cache compression at test time.
Jiahao Liu, Qifan Wang, Jingang Wang, and Xunliang            Advances in Neural Information Processing Systems,
   Cai. 2024a. Speculative decoding via early-exiting         36:52342–52364.
   for faster llm inference with thompson sampling con-
   trol mechanism. arXiv preprint arXiv:2406.03853.         Yen-Ju Lu, Yashesh Gaur, Wei Zhou, Benjamin Muller,
                                                              Jesus Villalba, Najim Dehak, Luke Zettlemoyer,
Jiaheng Liu, Dawei Zhu, Zhiqi Bai, Yancheng                   Gargi Ghosh, Mike Lewis, Srinivasan Iyer, et al.
   He, Huanxuan Liao, Haoran Que, Zekun Wang,                 2025. Latent speech-text transformer. arXiv preprint
   Chenchen Zhang, Ge Zhang, Jiebin Zhang, et al.             arXiv:2510.06195.
   2025b. A comprehensive survey on long context lan-
                                                            Mingbo Ma, Liang Huang, Hao Xiong, Renjie Zheng,
   guage modeling. arXiv preprint arXiv:2503.17407.
                                                              Kaibo Liu, Baigong Zheng, Chuanqiang Zhang,
Jiesong Liu, Brian Park, and Xipeng Shen. 2025c. A            Zhongjun He, Hairong Liu, Xing Li, et al. 2019.
   drop-in solution for on-the-fly adaptation of specula-     Stacl: Simultaneous translation with implicit antici-
   tive decoding in large language models. In Proceed-        pation and controllable latency using prefix-to-prefix
   ings of the 63rd Annual Meeting of the Association         framework. In Proceedings of the 57th Annual Meet-
   for Computational Linguistics (Volume 1: Long Pa-          ing of the Association for Computational Linguistics,
   pers), pages 9778–9794.                                    pages 3025–3036.

                                                            Dominik Macháček, Raj Dabre, and Ondřej Bojar. 2023.
Jihao Liu, Zhiding Yu, Shiyi Lan, Shihao Wang,
                                                              Turning whisper into real-time transcription system.
   Rongyao Fang, Jan Kautz, Hongsheng Li, and Jose M
                                                              arXiv preprint arXiv:2307.14743.
   Alvare. 2024b. Streamchat: Chatting with streaming
   video. arXiv preprint arXiv:2412.08646.                  Benjamin Minixhofer, Jonas Pfeiffer, and Ivan Vulić.
                                                              2023. Where’s the point? self-supervised multi-
Shang Liu, Yao Lu, Wenji Fang, Jing Wang, and Zhiyao          lingual punctuation-agnostic sentence segmentation.
  Xie. 2025d. Sync-llm: Generation of large-scale syn-        arXiv preprint arXiv:2305.18893.
  thetic circuit code with hierarchical language models.
  In Proceedings of the 2025 Conference on Empiri-          Tan Dat Nguyen, Ji-Hoon Kim, Jeongsoo Choi, Shuk-
  cal Methods in Natural Language Processing, pages           jae Choi, Jinseok Park, Younglo Lee, and Joon Son
  17361–17376.                                                Chung. 2025. Accelerating codec-based speech syn-
                                                              thesis with multi-token prediction and speculative
Tianqiao Liu, Xueyi Li, Hao Wang, Haoxuan Li,                 decoding. In ICASSP 2025-2025 IEEE International
  Zhichao Chen, Weiqi Luo, and Zitao Liu. 2025e.              Conference on Acoustics, Speech and Signal Process-
  From text to talk: Audio-language model needs               ing (ICASSP), pages 1–5. IEEE.
  non-autoregressive joint training. arXiv preprint
  arXiv:2509.20072.                                         Shen Nie, Fengqi Zhu, Zebin You, Xiaolu Zhang,
                                                              Jingyang Ou, Jun Hu, Jun Zhou, Yankai Lin, Ji-Rong
Wenrui Liu, Qian Chen, Wen Wang, Guanrou Yang,                Wen, and Chongxuan Li. 2025. Large language dif-
 Weiqin Li, Minghui Fang, Jialong Zuo, Xiaoda Yang,           fusion models. arXiv preprint arXiv:2502.09992.
 Tao Jin, Jin Xu, et al. 2025f. Speech token prediction
 via compressed-to-fine language modeling for speech        Xuefei Ning, Zinan Lin, Zixuan Zhou, Zifu Wang,
 generation. In Proceedings of the 33rd ACM Inter-            Huazhong Yang, and Yu Wang. 2023. Skeleton-of-
 national Conference on Multimedia, pages 10632–              thought: Large language models can do parallel de-
 10641.                                                       coding. Proceedings ENLSP-III.

Xiang Liu, Zhenheng Tang, Peijie Dong, Zeyu Li, Yue         OpenAI. 2023. Gpt-4 technical report. arXiv preprint
  Liu, Bo Li, Xuming Hu, and Xiaowen Chu. 2025g.              arXiv:2303.08774.
Siqi Ouyang, Xi Xu, and Lei Li. 2025. Infinisst: Si-        Aditya Ramesh et al. 2021. Zero-shot text-to-image
  multaneous translation of unbounded speech with             generation. arXiv preprint arXiv:2102.12092.
  large language model. In Findings of the Associa-
  tion for Computational Linguistics: ACL 2025, pages       Shuhuai Ren, Shuming Ma, Xu Sun, and Furu Wei.
  3032–3046.                                                  2025. Next block prediction: Video generation
                                                              via semi-autoregressive modeling. arXiv preprint
Sunny Panchal, Apratim Bhattacharyya, Guillaume               arXiv:2502.07737.
  Berger, Antoine Mercier, Cornelius Böhm, Flo-
  rian Dietrichkeit, Reza Pourreza, Xuanlin Li, Pulkit      Paul K Rubenstein, Chulayuth Asawaroengchai,
  Madan, Mingu Lee, et al. 2024. What to say and              Duc Dung Nguyen, Ankur Bapna, Zalán Borsos,
  when to say it: Live fitness coaching as a testbed for      Félix de Chaumont Quitry, Peter Chen, Dalia El
  situated interaction. Advances in Neural Information        Badawy, Wei Han, Eugene Kharitonov, et al. 2023.
  Processing Systems, 37:75853–75882.                         Audiopalm: A large language model that can speak
                                                              and listen. arXiv preprint arXiv:2306.12925.
William Peebles and Saining Xie. 2022. Scalable dif-
  fusion models with transformers. arXiv preprint           Laura Ruis, Mitchell Stern, Julia Proskurnia, and
  arXiv:2212.09748.                                           William Chan. 2020. Insertion-deletion transformer.
                                                              arXiv preprint arXiv:2001.05540.
Rui Qian, Shuangrui Ding, Xiaoyi Dong, Pan Zhang,
  Yuhang Zang, Yuhang Cao, Dahua Lin, and Jiaqi             Frank Seide, Morrie Doulaty, Yangyang Shi, Yashesh
  Wang. 2025. Dispider: Enabling video llms with ac-          Gaur, Junteng Jia, and Chunyang Wu. 2024. Speech
  tive real-time interaction via disentangled perception,     reallm–real-time streaming speech recognition with
  decision, and reaction. In Proceedings of the Com-          multimodal llms by teaching the flow of time. arXiv
  puter Vision and Pattern Recognition Conference,            preprint arXiv:2406.09569.
  pages 24045–24055.                                        Zhengyan Sheng, Zhihao Du, Shiliang Zhang, Zhijie
                                                              Yan, Yexin Yang, and Zhenhua Ling. 2025. Sync-
Rui Qian, Xiaoyi Dong, Pan Zhang, Yuhang Zang,
                                                              speech: Low-latency and efficient dual-stream text-
  Shuangrui Ding, Dahua Lin, and Jiaqi Wang. 2024.
                                                              to-speech based on temporal masked transformer.
  Streaming long video understanding with large lan-
                                                              arXiv preprint arXiv:2502.11094.
  guage models. Advances in Neural Information Pro-
  cessing Systems, 37:119336–119360.                        Mohan Shi, Yuchun Shu, Lingyun Zuo, Qian Chen, Shil-
                                                             iang Zhang, Jie Zhang, and Li-Rong Dai. 2023. Se-
Zhen Qin, Weigao Sun, Dong Li, Xuyang Shen, Weix-            mantic vad: Low-latency voice activity detection for
  uan Sun, and Yiran Zhong. 2024. Lightning attention-       speech interaction. arXiv preprint arXiv:2305.12450.
  2: A free lunch for handling unlimited sequence
  lengths in large language models. arXiv preprint          Sambal Shikhar, Mohammed Irfan Kurpath, Sahal Shaji
  arXiv:2401.04658.                                           Mullappilly, Jean Lahoud, Fahad Shahbaz Khan,
                                                              Rao Muhammad Anwer, Salman Khan, and Hisham
Ziran Qin, Yuchen Cao, Mingbao Lin, Wen Hu, Shixuan           Cholakkal. 2025. Llmvox: Autoregressive stream-
   Fan, Ke Cheng, Weiyao Lin, and Jianguo Li. 2025a.          ing text-to-speech model for any llm. In Findings of
   Cake: Cascading and adaptive kv cache eviction with        the Association for Computational Linguistics: ACL
   layer preferences. arXiv preprint arXiv:2503.12491.        2025, pages 20481–20493.
Ziran Qin, Youru Lv, Mingbao Lin, Zeren Zhang, Chan-        Junhyuk So, Juncheol Shin, Hyunho Kook, and Eun-
   fan Gan, Tieyuan Chen, and Weiyao Lin. 2025b. Au-          hyeok Park. 2025. Grouped speculative decoding
   toregressive image generation needs only a few lines       for autoregressive image generation. In Proceedings
   of cached tokens. arXiv preprint arXiv:2512.04857.         of the IEEE/CVF International Conference on Com-
                                                              puter Vision, pages 15375–15384.
Ziran Qin, Youru Lv, Mingbao Lin, Zeren Zhang, Dan-
   ping Zou, and Weiyao Lin. 2025c. Head-aware kv           Yuxuan Song, Zheng Zhang, Cheng Luo, Pengyang
   cache compression for efficient visual autoregressive      Gao, Fan Xia, Hao Luo, Zheng Li, Yuehang Yang,
   modeling. arXiv preprint arXiv:2504.09261.                 Hongli Yu, Xingwei Qu, et al. 2025. Seed diffusion:
                                                              A large-scale diffusion language model with high-
Alec Radford, Jong Wook Kim, Chris Hallacy, Aditya            speed inference. arXiv preprint arXiv:2508.02193.
  Ramesh, Gabriel Goh, Sandhini Agarwal, Girish Sas-
  try, Amanda Askell, Pamela Mishkin, Jack Clark,           Peize Sun, Yi Jiang, Shoufa Chen, Shilong Zhang,
  et al. 2021. Learning transferable visual models from       Bingyue Peng, Ping Luo, and Zehuan Yuan.
  natural language supervision. In International confer-      2024. Autoregressive model beats diffusion: Llama
  ence on machine learning, pages 8748–8763. PmLR.            for scalable image generation. arXiv preprint
                                                              arXiv:2406.06525.
Matthew Raffel, Victor Agostinelli, and Lizhong
 Chen. 2024. Simultaneous masking, not prompt-              Hanlin Tang, Yang Lin, Jing Lin, Qingsen Han, Shikuan
 ing optimization: A paradigm shift in fine-tuning            Hong, Yiwu Yao, and Gongyi Wang. 2024. Razo-
 llms for simultaneous translation. arXiv preprint            rattention: Efficient kv cache compression through
 arXiv:2405.10443.                                            retrieval heads. arXiv preprint arXiv:2407.15891.
Keda Tao, Can Qin, Haoxuan You, Yang Sui, and Huan        Haibo Wang, Bo Feng, Zhengfeng Lai, Mingze Xu,
  Wang. 2025. Dycoke: Dynamic compression of to-            Shiyu Li, Weifeng Ge, Afshin Dehghan, Meng
  kens for fast video large language models. In Pro-        Cao, and Ping Huang. 2025a. Streambridge: Turn-
  ceedings of the Computer Vision and Pattern Recog-        ing your offline video large language model into
  nition Conference, pages 18992–19001.                     a proactive streaming assistant. arXiv preprint
                                                            arXiv:2505.05467.
Chameleon Team. 2024. Chameleon: Mixed-modal
  early-fusion foundation models. arXiv preprint          Haoyu Wang, Guoqiang Hu, Guodong Lin, Wei-
  arXiv:2405.09818.                                         Qiang Zhang, and Jian Li. 2024b. Simul-whisper:
                                                            Attention-guided streaming whisper with truncation
Gemini Team, Rohan Anil, Sebastian Borgeaud, Jean-          detection. arXiv preprint arXiv:2406.10052.
  Baptiste Alayrac, Jiahui Yu, Radu Soricut, Johan
  Schalkwyk, Andrew M Dai, Anja Hauth, Katie              Minghan Wang, Thuy Vu, Jinming Zhao, Fatemeh Shiri,
  Millican, et al. 2023.    Gemini: a family of             Ehsan Shareghi, and Gholamreza Haffari. 2024c. Si-
  highly capable multimodal models. arXiv preprint          multaneous machine translation with large language
  arXiv:2312.11805.                                         models. In Proceedings of the 22nd Annual Work-
                                                            shop of the Australasian Language Technology Asso-
Yao Teng, Han Shi, Xian Liu, Xuefei Ning, Guohao            ciation, pages 89–103.
  Dai, Yu Wang, Zhenguo Li, and Xihui Liu. 2024. Ac-
  celerating auto-regressive text-to-image generation     Weizhi Wang, Li Dong, Hao Cheng, Xiaodong Liu,
  with training-free speculative jacobi decoding. arXiv    Xifeng Yan, Jianfeng Gao, and Furu Wei. 2023. Aug-
  preprint arXiv:2410.01699.                               menting language models with long-term memory.
                                                           Advances in Neural Information Processing Systems,
Keyu Tian, Yi Jiang, Zehuan Yuan, Bingyue Peng, and        36:74530–74543.
  Liwei Wang. 2024. Visual autoregressive modeling:
  Scalable image generation via next-scale prediction.    Xindi Wang, Mahsa Salmani, Parsa Omidi, Xiangyu
  Advances in neural information processing systems,        Ren, Mehdi Rezagholizadeh, and Armaghan Eshaghi.
  37:84839–84865.                                           2024d. Beyond the limits: A survey of techniques to
                                                            extend the context length in large language models.
Yuchuan Tian, Yuchen Liang, Jiacheng Sun, Shuo
                                                            arXiv preprint arXiv:2402.02244.
  Zhang, Guangwen Yang, Yingte Shu, Sibo Fang,
  Tianyu Guo, Kai Han, Chao Xu, et al. 2025.
                                                          Xinlong Wang, Xiaosong Zhang, Zhengxiong Luo,
  From next-token to next-block: A principled adap-
                                                            Quan Sun, Yufeng Cui, Jinsheng Wang, Fan Zhang,
  tation path for diffusion llms. arXiv preprint
                                                            Yueze Wang, Zhen Li, Qiying Yu, et al. 2024e. Emu3:
  arXiv:2512.06776.
                                                            Next-token prediction is all you need. arXiv preprint
Junlong Tong, Yingqi Fan, Anhao Zhao, Yunpu Ma,             arXiv:2409.18869.
  and Xiaoyu Shen. 2025a. Streamingthinker: Large
  language models can think while reading. arXiv          Yiyu Wang, Xuyang Liu, Xiyan Gui, Xinying Lin,
  preprint arXiv:2510.17238.                                Boxue Yang, Chenfei Liao, Tailai Chen, and Linfeng
                                                            Zhang. 2025b. Accelerating streaming video large
Junlong Tong, Jinlan Fu, Zixuan Lin, Yingqi Fan, Anhao      language models via hierarchical token compression.
  Zhao, Hui Su, and Xiaoyu Shen. 2025b. Llm as effec-       arXiv preprint arXiv:2512.00891.
  tive streaming processor: Bridging streaming-batch
  mismatches with group position encoding. arXiv          Yuancheng Wang, Haoyue Zhan, Liwei Liu, Ruihong
  preprint arXiv:2505.16983.                                Zeng, Haotian Guo, Jiachen Zheng, Qiang Zhang,
                                                            Xueyao Zhang, Shunsi Zhang, and Zhizheng Wu.
Genshun Wan, Wenhui Zhang, Jing-Xuan Zhang, Shifu           2024f. Maskgct: Zero-shot text-to-speech with
  Xiong, Jianqing Gao, and Zhongfu Ye. 2026. Stream-        masked generative codec transformer. arXiv preprint
  ing speech recognition with decoder-only large lan-       arXiv:2409.00750.
  guage models and latency optimization. arXiv
  preprint arXiv:2601.22779.                              Yueqian Wang, Songxiang Liu, Disong Wang, Nuo Xu,
                                                            Guanglu Wan, Huishuai Zhang, and Dongyan Zhao.
Ao Wang, Hui Chen, Jiaxin Li, Jianchao Tan, Kefeng          2025c. Mmduet2: Enhancing proactive interaction of
  Zhang, Xunliang Cai, Zijia Lin, Jungong Han, and          video mllms with multi-turn reinforcement learning.
  Guiguang Ding. 2024a. Prefixkv: Adaptive prefix           arXiv preprint arXiv:2512.06810.
  kv cache is what vision instruction-following mod-
  els need for efficient generation. arXiv preprint       Yuhao Wang, Heyang Liu, Ziyang Cheng, Ronghua Wu,
  arXiv:2412.03409.                                         Qunshan Gu, Yanfeng Wang, and Yu Wang. 2025d.
                                                            Vocalnet: Speech llm with multi-token prediction for
Chunqi Wang, Ji Zhang, Haiqing Chen, Chenghao Tao,          faster and high-quality generation. arXiv preprint
  et al. 2018. Semi-autoregressive neural machine           arXiv:2504.04060.
  translation. In Proceedings of the 2018 Conference
  on Empirical Methods in Natural Language Process-       Yuqing Wang, Shuhuai Ren, Zhijie Lin, Yujin Han,
  ing (EMNLP). ArXiv:1808.08583.                            Haoyuan Guo, Zhenheng Yang, Difan Zou, Jiashi
  Feng, and Xihui Liu. 2025e. Parallelized autoregres-    Jiaer Xia, Peixian Chen, Mengdan Zhang, Xing Sun,
  sive visual generation. In Proceedings of the Com-         and Kaiyang Zhou. 2025a. Streaming video instruc-
  puter Vision and Pattern Recognition Conference,           tion tuning. arXiv preprint arXiv:2512.21334.
  pages 12955–12965.
                                                          Yinfeng Xia, Huiyan Li, Chenyang Le, Manhong
Yuxuan Wang, Yiqi Song, Cihang Xie, Yang Liu, and           Wang, Yutao Sun, Xingyang Ma, and Yanmin Qian.
  Zilong Zheng. 2025f. Videollamb: Long streaming           2025b. Mfla: Monotonic finite look-ahead attention
  video understanding with recurrent memory bridges.        for streaming speech recognition. arXiv preprint
  In Proceedings of the IEEE/CVF International Con-         arXiv:2506.03722.
  ference on Computer Vision, pages 24170–24181.
Zili Wang, Robert Zhang, Kun Ding, Qi Yang, Fei Li,       Guangxuan Xiao, Jiaming Tang, Jingwei Zuo, Junxian
   and Shiming Xiang. 2024g. Continuous speculative         Guo, Shang Yang, Haotian Tang, Yao Fu, and Song
   decoding for autoregressive image generation. arXiv      Han. 2024a. Duoattention: Efficient long-context llm
   preprint arXiv:2411.11925.                               inference with retrieval and streaming heads. arXiv
                                                            preprint arXiv:2410.10819.
Chiyue Wei, Cong Guo, Junyao Zhang, Haoxuan
  Shan, Yifan Xu, Ziyue Zhang, Yudong Liu, Qinsi          Guangxuan Xiao, Yuandong Tian, Beidi Chen, Song
  Wang, Changchun Zhou, Hai Li, et al. 2025a. Fo-           Han, and Mike Lewis. 2023. Efficient streaming
  cus: A streaming concentration architecture for           language models with attention sinks. arXiv preprint
  efficient vision-language models. arXiv preprint          arXiv:2309.17453.
  arXiv:2512.14661.
                                                          Zilin Xiao, Hongming Zhang, Tao Ge, Siru Ouyang,
Meng Wei, Chenyang Wan, Xiqian Yu, Tai Wang,                 Vicente Ordonez, and Dong Yu. 2024b. Parallel-
 Yuqiang Yang, Xiaohan Mao, Chenming Zhu, Wen-               spec: Parallel drafter for efficient speculative decod-
 zhe Cai, Hanqing Wang, Yilun Chen, et al. 2025b.            ing. arXiv preprint arXiv:2410.05589.
 Streamvln: Streaming vision-and-language naviga-
 tion via slowfast context modeling. arXiv preprint       Jinheng Xie, Weijia Mao, Zechen Bai, David Junhao
 arXiv:2507.05240.                                           Zhang, Weihao Wang, Kevin Qinghong Lin, Yuchao
                                                             Gu, Zhijie Chen, Zhenheng Yang, and Mike Zheng
Zhuofan Wen, Shangtong Gui, and Yang Feng. 2024.
                                                             Shou. 2024. Show-o: One single transformer to unify
  Speculative decoding with ctc-based draft model for
                                                             multimodal understanding and generation. arXiv
  llm inference acceleration. Advances in Neural Infor-
                                                             preprint arXiv:2408.12528.
  mation Processing Systems, 37:92082–92100.
Haibin Wu, Naoyuki Kanda, Sefik Emre Eskimez,             Roy Xie, David Qiu, Deepak Gopinath, Dong Lin, Yan-
  and Jinyu Li. 2024a. Ts3-codec: Transformer-              chao Sun, Chong Wang, Saloni Potdar, and Bhuwan
  based simple streaming single codec. arXiv preprint       Dhingra. 2025. Interleaved reasoning for large lan-
  arXiv:2411.18803.                                         guage models via reinforcement learning. arXiv
                                                            preprint arXiv:2505.19640.
Hao Wu, Yingqi Fan, Jinyang Dai, Junlong Tong, Yunpu
  Ma, and Xiaoyu Shen. 2026a. Hidrop: Hierarchi-          Zhifei Xie and Changqiao Wu. 2024. Mini-omni: Lan-
  cal vision token reduction in mllms via late injec-       guage models can hear, talk while thinking in stream-
  tion, concave pyramid pruning, and early exit. arXiv      ing. arXiv preprint arXiv:2408.16725.
  preprint arXiv:2602.23699.
                                                          Yi Xin, Qi Qin, Siqi Luo, Kaiwen Zhu, Juncheng
Hao Wu, Junlong Tong, Xudong Wang, Yang Tan,                Yan, Yan Tai, Jiayi Lei, Yuewen Cao, Keqi Wang,
  Changyu Zeng, Anastasia Antsiferova, and Xiaoyu           Yibin Wang, et al. 2025. Lumina-dimoo: An
  Shen. 2026b. From data to model: A survey of the          omni diffusion large language model for multi-
  compression lifecycle in mllms. TechRxiv preprint         modal generation and understanding. arXiv preprint
  TechRxiv:177220375.55495124.                              arXiv:2510.06308.
Shiwei Wu, Joya Chen, Kevin Qinghong Lin, Qi-
  meng Wang, Yan Gao, Qianli Xu, Tong Xu, Yao             Z Xin, Z Dong, L Shimin, Z Yaqian, and Q Xipeng.
  Hu, Enhong Chen, and Mike Zheng Shou. 2024b.              2024. Speechtokenizer: Unified speech tokenizer for
  Videollm-mod: Efficient video-language streaming          speech language models. In Proc. Int. Conf. Learn.
  with mixture-of-depths vision computation. Ad-            Representations, pages 1–21.
  vances in Neural Information Processing Systems,
  37:109922–109947.                                       Boxun Xu, Yu Wang, Zihu Wang, and Peng Li. 2025a.
                                                            Ams-kv: Adaptive kv caching in multi-scale vi-
Yecheng Wu, Han Cai, Junyu Chen, Zhuoyang Zhang,            sual autoregressive transformers. arXiv preprint
  Enze Xie, Jincheng Yu, Junsong Chen, Jinyi Hu, Yao        arXiv:2511.16047.
  Lu, and Song Han. 2025. Dc-ar: Efficient masked au-
  toregressive image generation with deep compression     Jin Xu, Zhifang Guo, Jinzheng He, Hangrui Hu, Ting
  hybrid tokenizer. In Proceedings of the IEEE/CVF           He, Shuai Bai, Keqin Chen, Jialin Wang, Yang Fan,
  International Conference on Computer Vision, pages         Kai Dang, et al. 2025b. Qwen2. 5-omni technical
  18034–18045.                                               report. arXiv preprint arXiv:2503.20215.
Jin Xu, Zhifang Guo, Hangrui Hu, Yunfei Chu, Xiong       Songlin Yang, Bailin Wang, Yu Zhang, Yikang Shen,
   Wang, Jinzheng He, Yuxuan Wang, Xian Shi, Ting          and Yoon Kim. 2024b. Parallelizing linear trans-
   He, Xinfa Zhu, Yuanjun Lv, Yongqi Wang, Dake            formers with the delta rule over sequence length.
   Guo, He Wang, Linhan Ma, Pei Zhang, Xinyu Zhang,        Advances in neural information processing systems,
   Hongkun Hao, Zishan Guo, Baosong Yang, Bin              37:115491–115522.
   Zhang, Ziyang Ma, Xipin Wei, Shuai Bai, Keqin
   Chen, Xuejing Liu, Peng Wang, Mingkun Yang, Day-      Yanlai Yang, Zhuokai Zhao, Satya Narayan Shukla,
   iheng Liu, Xingzhang Ren, Bo Zheng, Rui Men, Fan        Aashu Singh, Shlok Kumar Mishra, Lizhu Zhang,
   Zhou, Bowen Yu, Jianxin Yang, Le Yu, Jingren Zhou,      and Mengye Ren. 2025e. Streammem: Query-
   and Junyang Lin. 2025c. Qwen3-omni technical re-        agnostic kv cache memory for streaming video un-
   port. arXiv preprint arXiv:2509.17765.                  derstanding. arXiv preprint arXiv:2508.15717.

Ruyi Xu, Guangxuan Xiao, Yukang Chen, Liuning He,        Yifan Yang, Shujie Liu, Jinyu Li, Yuxuan Hu,
  Kelly Peng, Yao Lu, and Song Han. 2025d. Stream-         Haibin Wu, Hui Wang, Jianwei Yu, Lingwei Meng,
  ingvlm: Real-time understanding for infinite video       Haiyang Sun, Yanqing Liu, et al. 2025f. Pseudo-
  streams. arXiv preprint arXiv:2510.09608.                autoregressive neural codec language models for effi-
                                                           cient zero-shot text-to-speech synthesis. In Proceed-
Ting Xu, Zhichao Huang, Jiankai Sun, Shanbo Cheng,         ings of the 33rd ACM International Conference on
  and Wai Lam. 2025e. Seqpo-simt: Sequential policy        Multimedia, pages 9316–9325.
  optimization for simultaneous machine translation.
  arXiv preprint arXiv:2505.20622.                       Yifan Yang, Ziyang Ma, Shujie Liu, Jinyu Li, Hui Wang,
                                                            Lingwei Meng, Haiyang Sun, Yuzhe Liang, Ruiyang
Yechen Xu, Xinhao Kong, Tingjun Chen, and Danyang          Xu, Yuxuan Hu, et al. 2024c. Interleaved speech-text
  Zhuo. 2024. Conveyor: Efficient tool-aware llm            language models are simple streaming text to speech
  serving with tool partial execution. arXiv preprint       synthesizers. arXiv preprint arXiv:2412.16102.
  arXiv:2406.00059.
                                                         Zeyu Yang, Lai Wei, Roman Koshkin, Xi Chen, and
George Yakushev, Nataliia Babina, Masoud Vahid Dast-       Satoshi Nakamura. 2025g. Sasst: Leveraging syntax-
  gerdi, Vyacheslav Zhdanovskiy, Alina Shutova, and        aware chunking and llms for simultaneous speech
  Denis Kuznedelev. 2025. Asynchronous reason-             translation. arXiv preprint arXiv:2508.07781.
  ing: Training-free interactive thinking llms. arXiv
  preprint arXiv:2512.10931.                             Zhenyu Yang, Yuhang Hu, Zemin Du, Dizhan Xue,
                                                           Shengsheng Qian, Jiahong Wu, Fan Yang, Weim-
An Yang, Anfeng Li, Baosong Yang, Beichen Zhang,           ing Dong, and Changsheng Xu. 2025h. Svbench:
  Binyuan Hui, Bo Zheng, Bowen Yu, Chang Gao,              A benchmark with temporal multi-turn dialogues
  Chengen Huang, Chenxu Lv, et al. 2025a. Qwen3            for streaming video understanding. arXiv preprint
  technical report. arXiv preprint arXiv:2505.09388.       arXiv:2502.10810.

Dongjie Yang, XiaoDong Han, Yan Gao, Yao Hu, Shilin      Zhenyu Yang, Kairui Zhang, Yuhang Hu, Bing Wang,
  Zhang, and Hai Zhao. 2024a. Pyramidinfer: Pyra-          Shengsheng Qian, Bin Wen, Fan Yang, Tingting Gao,
  mid kv cache compression for high-throughput llm         Weiming Dong, and Changsheng Xu. 2025i. Livestar:
  inference. arXiv preprint arXiv:2405.12532.              Live streaming assistant for real-world online video
                                                           understanding. arXiv preprint arXiv:2511.05299.
Haolin Yang, Feilong Tang, Lingxiao Zhao, Xi-
  ang An, Ming Hu, Huifa Li, Xinlin Zhuang, Yi-          Moran Yanuka, Paul Dixon, Eyal Finkelshtein, Daniel
  fan Lu, Xiaofeng Zhang, Abdalla Swikir, et al.          Rotman, and Raja Giryes. 2025. Principled coarse-
  2025b. Streamagent: Towards anticipatory agents         grained acceptance for speculative decoding in
  for streaming video understanding. arXiv preprint       speech. arXiv preprint arXiv:2511.13732.
  arXiv:2508.01875.
                                                         Linli Yao, Yicheng Li, Yuancheng Wei, Lei Li,
Ling Yang, Ye Tian, Bowen Li, Xinchen Zhang,               Shuhuai Ren, Yuanxin Liu, Kun Ouyang, Lean Wang,
  Ke Shen, Yunhai Tong, and Mengdi Wang. 2025c.            Shicheng Li, Sida Li, et al. 2025. Timechat-online:
  Mmada: Multimodal large diffusion language mod-          80% visual tokens are naturally redundant in stream-
  els. arXiv preprint arXiv:2505.15809.                    ing videos. In Proceedings of the 33rd ACM Inter-
                                                           national Conference on Multimedia, pages 10807–
Shang Yang, Junxian Guo, Haotian Tang, Qinghao Hu,         10816.
  Guangxuan Xiao, Jiaming Tang, Yujun Lin, Zhijian
  Liu, Yao Lu, and Song Han. 2025d. Lserve: Effi-        Yao Yao, Zuchao Li, and Hai Zhao. 2024. Sirllm:
  cient long-sequence llm serving with unified sparse      Streaming infinite retentive llm. arXiv preprint
  attention. arXiv preprint arXiv:2502.14866.              arXiv:2405.12528.

Songlin Yang, Bailin Wang, Yikang Shen, Rameswar         Zhen Ye, Peiwen Sun, Jiahe Lei, Hongzhan Lin, Xu Tan,
  Panda, and Yoon Kim. 2023. Gated linear attention        Zheqi Dai, Qiuqiang Kong, Jianyi Chen, Jiahao Pan,
  transformers with hardware-efficient training. arXiv     Qifeng Liu, et al. 2025. Codec does matter: Ex-
  preprint arXiv:2312.06635.                               ploring the semantic shortcoming of codec for audio
  language model. In Proceedings of the AAAI Con-           Annual Meeting of the Association for Computational
  ference on Artificial Intelligence, volume 39, pages      Linguistics (Volume 1: Long Papers), pages 8964–
  25697–25705.                                              8986.
Tianwei Yin, Qiang Zhang, Richard Zhang, William T        Shaolei Zhang and Yang Feng. 2023. End-to-end simul-
   Freeman, Fredo Durand, Eli Shechtman, and Xun            taneous speech translation with differentiable seg-
   Huang. 2025. From slow bidirectional to fast autore-     mentation. arXiv preprint arXiv:2305.16093.
   gressive video diffusion models. In Proceedings of
   the Computer Vision and Pattern Recognition Con-       Shaolei Zhang, Shoutao Guo, Qingkai Fang, Yan Zhou,
   ference, pages 22963–22974.                              and Yang Feng. 2025b. Stream-omni: Simultaneous
                                                            multimodal interactions with large language-vision-
Wenyi Yu, Siyin Wang, Xiaoyu Yang, Xianzhao                 speech model. arXiv preprint arXiv:2506.13642.
 Chen, Xiaohai Tian, Jun Zhang, Guangzhi Sun,
 Lu Lu, Yuxuan Wang, and Chao Zhang. 2024.                Xuan Zhang, Cunxiao Du, Chao Du, Tianyu Pang, Wei
 Salmonn-omni: A codec-free LLM for full-duplex             Gao, and Min Lin. 2024d. Simlayerkv: A simple
 speech understanding and generation. arXiv preprint        framework for layer-level kv cache reduction.
 arXiv:2411.18138.
                                                          Yanqi Zhang, Yuwei Hu, Runyuan Zhao, John Lui, and
Neil Zeghidour, Eugene Kharitonov, Manu Orsini, Vá-         Haibo Chen. 2024e. Unifying kv cache compres-
  clav Volhejn, Gabriel de Marmiesse, Edouard Grave,        sion for large language models with leankv. arXiv
  Patrick Pérez, Laurent Mazaré, and Alexandre Dé-          preprint arXiv:2412.03131.
  fossez. 2025. Streaming sequence-to-sequence learn-
  ing with delayed streams modeling. arXiv preprint       Yichi Zhang, Xin Luna Dong, Zhaojiang Lin, Andrea
  arXiv:2509.08753.                                         Madotto, Anuj Kumar, Babak Damavandi, Joyce
                                                            Chai, and Seungwhan Moon. 2025c. Proactive assis-
Xiangyu Zeng, Kefan Qiu, Qingyu Zhang, Xinhao Li,           tant dialogue generation from streaming egocentric
  Jing Wang, Jiaxin Li, Ziang Yan, Kun Tian, Meng           videos. In Proceedings of the 2025 Conference on
  Tian, Xinhai Zhao, et al. 2025. Streamforest: Ef-         Empirical Methods in Natural Language Processing,
  ficient online video understanding with persistent        pages 12055–12079.
  event memory. arXiv preprint arXiv:2509.24871.
                                                          Yulin Zhang, Cheng Shi, Yang Wang, and Sibei Yang.
Dong Zhang, Shimin Li, Xin Zhang, Jun Zhan,
                                                            2025d. Eyes wide open: Ego proactive video-llm for
  Pengyu Wang, Yaqian Zhou, and Xipeng Qiu. 2023a.
                                                            streaming video. arXiv preprint arXiv:2510.14560.
  Speechgpt: Empowering large language models with
  intrinsic cross-modal conversational abilities. In      Zekai Zhang, Weiye Zhu, Hewei Pan, Xiangchen Wang,
  Findings of the Association for Computational Lin-        Rongtao Xu, Xing Sun, and Feng Zheng. 2025e. Ac-
  guistics: EMNLP 2023, pages 15757–15773.                  tivevln: Towards active exploration via multi-turn rl
Duzhen Zhang, Yahan Yu, Jiahua Dong, Chenxing Li,           in vision-and-language navigation. arXiv preprint
  Dan Su, Chenhui Chu, and Dong Yu. 2024a. Mm-              arXiv:2509.12618.
  llms: Recent advances in multimodal large language
                                                          Zeyu Zhang, Shuning Chang, Yuanyu He, Yizeng Han,
  models. arXiv preprint arXiv:2401.13601.
                                                            Jiasheng Tang, Fan Wang, and Bohan Zhuang. 2025f.
Gengyuan Zhang, Tanveer Hannan, Hermine Kleiner,            Blockvid: Block diffusion for high-quality and con-
  Beste Aydemir, Xinyu Xie, Jian Lan, Thomas Seidl,         sistent minute-long video generation. arXiv preprint
  Volker Tresp, and Jindong Gu. 2025a. Avila:               arXiv:2511.22973.
  Asynchronous vision-language agent for stream-
  ing multimodal data interaction. arXiv preprint         Zhenyu Zhang, Ying Sheng, Tianyi Zhou, Tianlong
  arXiv:2506.18472.                                         Chen, Lianmin Zheng, Ruisi Cai, Zhao Song, Yuan-
                                                            dong Tian, Christopher Ré, Clark Barrett, et al. 2023b.
Haoji Zhang, Yiqin Wang, Yansong Tang, Yong Liu,            H2o: Heavy-hitter oracle for efficient generative
  Jiashi Feng, Jifeng Dai, and Xiaojie Jin. 2024b.          inference of large language models. Advances in
  Flash-vstream: Memory-based real-time under-              Neural Information Processing Systems, 36:34661–
  standing for long video streams. arXiv preprint           34710.
  arXiv:2406.08085.
                                                          Anhao Zhao, Fanghua Ye, Yingqi Fan, Junlong Tong,
Jialiang Zhang, Junlong Tong, Junyan Lin, Hao Wu,           Zhiwei Fei, Hui Su, and Xiaoyu Shen. 2025a.
   , Yirong Sun, Yunpu Ma, and Xiaoyu Shen. 2026.           Skipgpt: Dynamic layer pruning reinvented with
   Think-as-you-see: Streaming chain-of-thought rea-        token awareness and module decoupling. arXiv
   soning for large vision-language models. arXiv           preprint arXiv:2506.04179.
   preprint arXiv:2603.02872.
                                                          Libo Zhao, Jing Li, and Ziqian Zeng. 2024. Psfuture:
Shaolei Zhang, Qingkai Fang, Shoutao Guo, Zhengrui          A pseudo-future-based zero-shot adaptive policy for
  Ma, Min Zhang, and Yang Feng. 2024c. Stream-              simultaneous machine translation. In Proceedings
  speech: Simultaneous speech-to-speech translation         of the 2024 Conference on Empirical Methods in
  with multi-task learning. In Proceedings of the 62nd      Natural Language Processing, pages 1869–1881.
Libo Zhao, Jing Li, and Ziqian Zeng. 2025b. Drfrattn:
  Directly learn adaptive policy from attention for si-
  multaneous machine translation. In Proceedings of
  the 2025 Conference on Empirical Methods in Natu-
  ral Language Processing, pages 34881–34894.
Yucheng Zhao, Chong Luo, Chuanxin Tang, Dong-
  dong Chen, Noel Codella, and Zheng-Jun Zha. 2023.
  Streaming video model. In Proceedings of the
  IEEE/CVF conference on computer vision and pat-
  tern recognition, pages 14602–14612.
W Zhong et al. 2024. Enhancing large language mod-
  els with long-term memory. AAAI Conference on
 Artificial Intelligence.
Xiabin Zhou, Wenbin Wang, Minyan Zeng, Jiaxian Guo,
  Xuebo Liu, Li Shen, Min Zhang, and Liang Ding.
  2024. Dynamickv: Task-aware adaptive kv cache
  compression for long context llms. arXiv preprint
  arXiv:2412.14838.
Qianchao Zhu, Jiangfei Duan, Chang Chen, Siran Liu,
  Xiuhong Li, Guanyu Feng, Xin Lv, Xiao Chuanfu,
  Dahua Lin, and Chao Yang. 2025. Sampleattention:
  Near-lossless acceleration of long context llm infer-
  ence with adaptive structured sparse attention. Pro-
  ceedings of Machine Learning and Systems, 7.
Xianwei Zhuang, Yuxin Xie, Yufan Deng, Liming
  Liang, Jinghan Ru, Yuguo Yin, and Yuexian Zou.
  2025. Vargpt: Unified understanding and generation
  in a visual autoregressive multimodal large language
  model. arXiv preprint arXiv:2501.12327.
A     Survey Scope and Positioning                      A.3   Comparison with Existing Surveys

A.1    Motivation and Necessity of This Survey          While our survey establishes a unified taxonomy
                                                        for Streaming LLMs centered on dynamic data flow
The motivation for this survey stems from three         and real-time interaction, it is crucial to delineate
key observations regarding the current landscape        its scope from other prominent research directions
of Large Language Models (LLMs): the paradigm           in the LLM landscape. Below, we contrast our
shift to streaming scenarios, ambiguity in "stream-     focus with three major categories of existing sur-
ing" terminology, and absence of comprehensive          veys: Efficient LLMs, Multimodal LLMs, and
reviews in streaming LLMs domain.                       Long-Context LLMs.
The Paradigm Shift to Streaming Scenarios               Efficient LLMs. The technologies surveyed un-
While LLMs have demonstrated remarkable capa-           der the field of Efficient LLMs, including model
bilities across various static inputs, real-world de-   compression and KV cache management, are foun-
ployment increasingly demands streaming interac-        dational technology for efficient, accurate and in-
tion. Applications such as digital human assistants,    telligent Streaming LLMs (Li et al., 2024a; Dantas
real-time simultaneous interpretation, and embod-       et al., 2025; Cheng et al., 2025a). However, ex-
ied robotics require models to process continuous       isting typical surveys in this category, such as the
input streams and generate low-latency responses.       survey on KV cache management for acceleration
The transition from "static batch processing" to        (Li et al., 2024a), the comprehensive survey on ef-
"dynamic streaming interaction" presents unique         ficient LLMs (Dantas et al., 2025), and the review
challenges in memory management, temporal co-           on compression techniques (Cheng et al., 2025a),
herency, and inference efficiency that traditional      predominantly analyze these methods from an of-
LLM research overlooks.                                 fline and static perspective. Central questions of
                                                        these surveys is mostly on how to reduce the com-
Ambiguity in "Streaming" Terminology There              putational or memory footprint of a model that is
is currently a significant semantic ambiguity in        operating on a complete, existing context to acquire
the usage of the term "streaming" within the com-       higher throughput or enable development on hard-
munity. It is often conflated across three distinct     ware with constrained resources. In comparison,
dimensions: streaming generation (token-by-token        this survey re-contextualizes these optimizations
output), streaming processing (handling dynamic         within a streaming paradigm. Techniques such as
input context), and streaming interaction (dynamic      dynamic KV cache management and lightweight
generate with partial and dynamic input). This          model adaptation under the overarching imperative
survey aims to disambiguate these concepts and          of online, real-time interaction are unified. The
provide a rigorous taxonomy.                            key challenge shifts from static resource reduction
                                                        to dynamic runtime budgeting under the strict la-
Absence of Comprehensive Reviews Despite
                                                        tency constraints of streaming, where inputs are
the surge in related research, there is a notable
                                                        incrementally available, as is concurrent streaming
lack of a systematic survey dedicated to Streaming
                                                        defined, and outputs must also be generated in-
LLMs.
                                                        cremenntally. Thus, while efficient LLM research
A.2    Focus and Scope Delimitation                     only casts light on how can we run the model more
                                                        efficiently, this research also asks how can it read,
To ensure depth and coherence, we delineate the         listen, see and respond efficiently as the world un-
scope of this survey as follows: We primarily fo-       folds.
cus on decoder-only LLMs, and we structure the
survey by tracing the evolution of streaming capa-      Multimodal LLMs. The field of MLLMs (Zhang
bilities: from static input / streaming output (stan-   et al., 2024a) focuses on augmenting language mod-
dard generation), to streaming Input / streaming        els with the ability to process and generate content
output (infinite context processing), and finally to    across diverse modalities like vision, audio, and
dynamic interaction (duplex/omni-streaming). We         video. Key challenges include cross-modal align-
conducted a systematic literature review of top-tier    ment, fusion strategies, and the design of modality-
venues in AI, NLP, CV, and speech, with a cutoff        specific encoders and decoders. Although some
date of December 2025.                                  MM-LLM applications (e.g., real-time video anal-
ysis or speech-to-speech translation) are inherently    plements the main text by summarizing represen-
streaming, the primary goal of MM-LLM research          tative yet less-discussed threads and implementa-
is to achieve strong performance on multimodal          tions, rather than aiming for an exhaustive bibliog-
understanding and generation benchmarks. Our            raphy.
survey, however, abstracts away from the specifics         Table 2 presents additional methods for output-
of any single modality. We treat the input and out-     streaming LLMs, organized by streaming genera-
put as generic token streams and instead concen-        tion mechanisms and efficiency techniques.
trate on the temporal dynamics of the interaction.         Table 3 summarizes methods for sequential-
A streaming LLM architecture, as defined in our         streaming LLMs, focusing on incremental encod-
work, can serve as the backbone for a multimodal        ing and streaming context management.
system, but the core innovations we survey—such
as concurrent perception-generation loops and in-
finite context processing—are orthogonal to the
problem of modality grounding. Our focus is on
how information flows over time, not what the in-
formation represents.
Long-Context LLMs. Surveys in this category,
such as (Liu et al., 2025b) and (Wang et al., 2024d),
primarily focus on expanding the model’s static
capacity to process extremely long, finite input
sequences (e.g., long documents or multi-turn his-
tories). Their core goal is to extend the usable
context window and make inference over long se-
quences efficient, covering key technologies like
positional encoding extrapolation, efficient atten-
tion architectures (e.g., sparse attention), and so-
phisticated KV-cache management. While these ad-
vances in long-context modeling provide a crucial
foundational capability for processing extensive in-
formation, their perspective is largely centered on
a "read-then-write" inference paradigm for offline,
bounded inputs. In stark contrast, our survey on
Streaming LLMs investigates the dynamic interac-
tion paradigm required for unbounded, real-time
token streams. We focus on the unique challenges
of concurrent reading and writing, incremental pro-
cessing of growing states, and online context/KV
budgeting under strict latency constraints. There-
fore, while long-context techniques are often essen-
tial enabling components, our work shifts the focus
from merely enlarging a fixed context window to or-
chestrating continuous, low-latency reasoning and
generation within an ever-flowing data stream.

B   Supplementary Literature
Due to space limitations, we defer a broader collec-
tion of related work to this appendix. Following the
taxonomy in Figure 3, we organize additional liter-
ature into three paradigms: (1) Output-streaming
LLMs, (2) Sequential-streaming LLMs, and (3)
Concurrent-streaming LLMs. This appendix com-
Typical Surveys           Primary Focus             Typical Technologies Covered          Differentiation in This Survey

                                                 Survey Category: Efficient LLMs
(Li et al., 2024a)        Compression/adaptation 1) Compression: quantization,            Prior surveys treat compression and
(Dantas et al., 2025)     and memory             pruning, distillation, low-rank; and     KV-cache optimization as separate
                          bottlenecks.           2) KV-cache management: selection        threads; we unify them under
(Cheng et al., 2025a)                            / eviction, cache compression,           streaming interaction, highlighting
(Wu et al., 2026b)                               offloading, sliding-window /             online constraints and dynamic
                                                 hierarchical cache.                      runtime budgeting.

                                              Survey Category: Multimodal LLMs
(Zhang et al., 2024a)     Architectures, training   1) Encoder + Projector + LLM,         Prior MLLM surveys assume fixed
(Caffagni et al., 2024)   recipes, and              alignment module, tokenizer; and 2)   inputs and emphasize alignment and
                          benchmarks for            multimodal pretraining &              benchmarked capabilities. We focus
                          MLLMs.                    instruction tuning.                   on streaming interaction with token
                                                                                          stream abstraction, concurrent IO,
                                                                                          incremental perception, and online
                                                                                          memory and budget control.

                                             Survey Category: Long-Context LLMs
(Wang et al., 2024d)      Long-context              1) Position extrapolation /           Prior surveys focus on enlarging a
(Liu et al., 2025b)       modeling: extending       interpolation; 2) efficient           fixed context window for offline
                          usable context            long-sequence attention and           inputs or read then write inference.
                          windows and making        architectures; 3) KV-cache            We study streaming token streams
                          long-sequence             management (compression, eviction,    with concurrent read and write,
                          inference efficient.      and offloading); and 4)               incremental inputs, growing states,
                                                    workflow-level augmentation           and online context and KV
                                                    (prompt compression,                  budgeting for unbounded streams.
                                                    retrieval/external memory).

Table 1: Comparison between this survey and existing related surveys. We highlight the unique positioning of our
work in the context of streaming interaction.
                                                       Streaming Generation

            Mechanism
                                    Modality-Out                                       Methods
Token        Block     Refinement

  ✓                -       -            T          GPT (OpenAI, 2023), Gemini (Team et al., 2023), Qwen3 (Yang et al., 2025a),
                                                   DeepSeek-V3 (DeepSeek-AI et al., 2024), InternVL (Chen et al., 2024c),
                                                   ChatGLM (GLM et al., 2024), Gemma (Gemma Team, 2024)
  ✓                -       -            S          AudioLM (Borsos et al., 2023a), SpeechGPT (Zhang et al., 2023a),
                                                   AudioPaLM (Rubenstein et al., 2023), FireRedTTS (Guo et al., 2024a),
                                                   Moshi (Défossez et al., 2024), Llama-omni2 (Fang et al., 2025),
                                                   Qwen3-Omni (Xu et al., 2025c), StyLLE (Hao et al.), Llmvox (Shikhar et al.,
                                                   2025), SpeakStream (Bai et al., 2025)
  ✓                -       -            V          DALLE (Ramesh et al., 2021), VideoPoet (Kondratyuk et al., 2024),
                                                   Chameleon (Team, 2024), Emu3 (Wang et al., 2024e), Anole (Chern et al.,
                                                   2024), Lumina-mGPT2.0 (Xin et al., 2025), Infinity (Han et al., 2025)
   -           ✓           -            T          SAT (Wang et al., 2018), SoT (Ning et al., 2023), CtrlDiff (Huang and Tang,
                                                   2025), PredSent (Hwang et al., 2025), Falcon (Gao et al., 2025), SSD-LM (Han
                                                   et al., 2023), WeDLM (Liu et al., 2025a), Next-Block (Tian et al., 2025), Block
                                                   Diffusion (Arriola et al., 2025)
   -           ✓           -            S          PALLE (Yang et al., 2025f), SyncSpeech (Sheng et al., 2025), DCAR (Li et al.,
                                                   2025a), StreamFlow (Guo et al., 2025), TtT (Liu et al., 2025e), DiTAR (Jia
                                                   et al., 2025)
   -           ✓           -            V          show-o (Xie et al., 2024), XTRA (Amrani et al., 2025), NTP (Ren et al., 2025),
                                                   CausVid (Yin et al., 2025), BlockVid (Zhang et al., 2025f), NBP (Ren et al.,
                                                   2025)
   -               -       ✓            T          Mask-Predict (Ghazvininejad et al., 2019), LevT (Gu et al., 2019),
                                                   Insertion-Deletion (Ruis et al., 2020), Diffusion-LM (Li et al., 2022),
                                                   DiffuSeq (Gong et al., 2022), D3PM (Austin et al., 2021)
   -               -       ✓            S          SoundStorm (Borsos et al., 2023b), Voicebox (Le et al., 2023),
                                                   Specmaskgit (Comunità et al., 2024), IMPACT (Huang et al., 2025a),
                                                   Maskgct (Wang et al., 2024f), DDM-TASTE (Ku et al., 2025)
   -               -       ✓            V          MaskGIT (Chang et al., 2022), Muse (Chang et al., 2023), DiT (Peebles and Xie,
                                                   2022), VAR (Tian et al., 2024), DetailFlow (Liu et al., 2025h), DC-AR (Wu
                                                   et al., 2025)

                                                        Streaming Efficiency

       Efficient
                                    Modality-Out                                       Methods
Decode Memory

  ✓                -                    T          Speculative Sampling (Chen et al., 2023), Medusa (Cai et al., 2024a),
                                                   EAGLE2 (Li et al., 2024d), BiLd (Kim et al., 2023), CTC-based Drafting (Wen
                                                   et al., 2024), FLY (Liu et al., 2025c), SkipDecode (Del Corro et al., 2023),
                                                   SkipGPT (Zhao et al., 2025a), EESD (Liu et al., 2024a), HiDrop (Wu et al.,
                                                   2026a), Visipruner (Fan et al., 2025)
  ✓                -                    S          LiveSpeech (Dang et al., 2024), MTP-SpecDec (Nguyen et al., 2025), SSD (Lin
                                                   et al., 2025), VocalNet (Wang et al., 2025d), VADUSA (Li et al., 2025b),
                                                   PCG (Yanuka et al., 2025)
  ✓                -                    V          SJD (Teng et al., 2024), CSpD (Wang et al., 2024g), GSD (So et al., 2025),
                                                   VVS (Dong et al., 2025), FreqExit (Li et al., 2025j), SkipVAR (Li et al., 2025d),
                                                   PAR (Wang et al., 2025e), ADT-Tree (Lei et al., 2025), Lantern (Jang et al.,
                                                   2024)
   -           ✓                        T          StreamingLLM (Xiao et al., 2023), H2O (Zhang et al., 2023b),
                                                   Scissorhands (Liu et al., 2023), Snapkv (Li et al., 2024c), Dynamickv (Zhou
                                                   et al., 2024), Chunkkv (Liu et al., 2025g)
   -           ✓                        S          wu2024ts3 (Wu et al., 2024a), LST (Lu et al., 2025),
                                                   SpeechTokenPrediction (Liu et al., 2025f)
   -           ✓                        V          HACK (Qin et al., 2025c), ScaleKV (Li et al., 2025e), AMS-KV (Xu et al.,
                                                   2025a), LineAR (Qin et al., 2025b)

Table 2: Summary of additional literature on output-streaming LLMs, complementing the discussion in Sec. 3.
                                                   Incremental Encoding

               Type
                                 Modality-In                                         Methods
  Fragmented           Atomic
   Encoding           Encoding

      ✓                  -           T         SimulMT (Wang et al., 2024c), Moshi (Défossez et al., 2024), Codec (Ye et al.,
                                               2025), dmel (Bai et al., 2024), Lightweight Audio Segmentation (Frohmann et al.,
                                               2024), Semantic VAD (Shi et al., 2023)
      ✓                  -           S         Whisper-Streaming (Macháček et al., 2023), SimulST (Zhang and Feng, 2023),
                                               CTC (Graves, 2012), Speechtokenizer (Xin et al., 2024), Moshi (Défossez et al.,
                                               2024), Codec (Ye et al., 2025), dmel (Bai et al., 2024), Lightweight Audio
                                               Segmentation (Frohmann et al., 2024), Semantic VAD (Shi et al., 2023)
      ✓                  -           V         S-ViT (Zhao et al., 2023)
       -                 ✓           T         SaT (Frohmann et al., 2024), SegFree (Iranzo-Sánchez et al., 2024),
                                               WtP (Minixhofer et al., 2023), subword regularization (Kudo, 2018), SentencePiece
                                               (Kudo and Richardson, 2018),
       -                 ✓           V         ViT (Dosovitskiy, 2020), CLIP (Radford et al., 2021)

                                               Streaming Context Management

                       Type
                                                                                     Methods
     Mem.               KV          Attn.

      ✓                  -            -        StreamingTOM (Chen et al., 2025b), MemoryBank (Zhong et al., 2024),
                                               LongMem (Wang et al., 2023), VideoStreaming (Qian et al., 2024),
                                               Timechat-online (Yao et al., 2025), Prunevid (Huang et al., 2025b), DyCoke (Tao
                                               et al., 2025), ProVideLLM (Chatterjee et al., 2025), VideoLLaMB (Wang et al.,
                                               2025f), STREAMMIND (Ding et al., 2025b), VideoStreaming (Qian et al., 2024),
                                               StreamingAssistant (Jin et al., 2025), Focus (Wei et al., 2025a), StreamForest (Zeng
                                               et al., 2025), Flash-vstream (Zhang et al., 2024b)
       -                 ✓            -        H2o (Zhang et al., 2023b), PyramidKV (Cai et al., 2024b), SnapKV (Li et al.,
                                               2024c), StreamKV (Chen et al., 2025c), STC (Wang et al., 2025b),
                                               Streammem (Yang et al., 2025e), AViLA (Zhang et al., 2025a), StreamingVLM (Xu
                                               et al., 2025d), PyramidInfer (Yang et al., 2024a), DynamicKV (Zhou et al., 2024),
                                               PrefixKV (Wang et al., 2024a), CAKE (Qin et al., 2025a), SimLayerKV (Zhang
                                               et al., 2024d), AdaKV (Feng et al., 2024), CriticalKV (Feng et al., 2025),
                                               LeanKV (Zhang et al., 2024e), RazorAttention (Tang et al., 2024), HeadKV (Fu
                                               et al., 2024b), DuoAttention (Xiao et al., 2024a)
       -                 -           ✓         Attention Sink (Xiao et al., 2023), Sirllm (Yao et al., 2024), GLA (Yang et al., 2023),
                                               DeltaNet (Yang et al., 2024b), Lightning attention-2 (Qin et al., 2024),
                                               SAMPLEATTENTION (Zhu et al., 2025), Lserve (Yang et al., 2025d), DCA (An
                                               et al., 2024)

Table 3: Summary of additional literature on sequential-streaming LLMs, complementing the discussion in Sec. 4.
                                              Streaming Paradigm
           Paradigm            Modality
                                                                              Methods
   R.     C.      I.   G.     In     Out
   ✓       -      -    -      T       T    Simul-LLM (Agostinelli et al., 2024), SiLLM (Guo et al., 2024c),
                                           TransLLaMA (Koshkin et al., 2024b), CAST (Koshkin et al., 2024a),
                                           RALCP (Wang et al., 2024c)
   ✓       -      -    -      S       T    CAST (Koshkin et al., 2024a), TransLLaMA (Koshkin et al., 2024b)
   -       ✓      -    -      T       S    LLMVoX (Shikhar et al., 2025), Mini-Omni (Xie and Wu, 2024)
   -       ✓      -    -      S       S    Mini-Omni (Xie and Wu, 2024)
   -       ✓      -    -      V       T    ViSpeak (Fu et al., 2025c)
   -       -      ✓    -      T       T    EAST (Fu et al., 2025a), Shanks (Chiang et al., 2025a)
   -       -      ✓    -      T       S    STITCH (Chiang et al., 2025b)
   -       -      ✓    -      S       T    EASiST (Fu et al., 2025b), InfiniSST (Ouyang et al., 2025), SASST (Yang et al.,
                                           2025g), StreamingASR (Wan et al., 2026)
   -       -      ✓    -      S       S    SALMONN-omni (Yu et al., 2024)
   -       -      ✓    -      V       T    Videollm-online (Chen et al., 2024a), LiveCC (Chen et al., 2025a),
                                           ProVideLLM (Chatterjee et al., 2025), StreamBridge (Wang et al., 2025a),
                                           LiveStar (Yang et al., 2025i), SVBench (Yang et al., 2025h), ProASIST (Zhang
                                           et al., 2025c)
   -       -      -    ✓      T       T    StreamingGPE (Tong et al., 2025b), StreamingThinker (Tong et al., 2025a),
                                           DST (Guo et al., 2024b)
   -       -      -    ✓      S       T    StreamingGPE (Tong et al., 2025b)
   -       -      -    ✓      V       T    StreamChat (Liu et al., 2024b), Speak-While-Watching (Lin et al., 2026),
                                           TaYS (Zhang et al., 2026)
                                                Interaction Policy
         Policy                Modality
                                                                              Methods
  Rule   SFT      RL          In     Out
   ✓       -      -           T       T    Simul-LLM (Agostinelli et al., 2024; Raffel et al., 2024), StreamingGPE (Tong
                                           et al., 2025b), STACL (Ma et al., 2019), AsyncReasoning (Yakushev et al.,
                                           2025), StreamingThinker (Tong et al., 2025a), Conveyor (Xu et al., 2024),
                                           AsyncLM (Gim et al., 2024)
   ✓       -      -           T       S    CosyVoice 2 (Du et al., 2024), IST-LM (Yang et al., 2024c), DSM (Zeghidour
                                           et al., 2025)
   ✓       -      -           S       T    MFLA (Xia et al., 2025b), InfiniSST (Ouyang et al., 2025), LLM as
                                           Processor (Tong et al., 2025b), SASST (Yang et al., 2025g),
                                           SimulS2S-LLM (Deng et al., 2025), ReaLLM (Seide et al., 2024),
                                           Llama-omni (Fang et al., 2024)
   ✓       -      -           S       S    StreamRAG (Arora et al., 2025)
   ✓       -      -           V       T    LiveCC (Chen et al., 2025a), StreamVLN (Wei et al., 2025b),
                                           ActiveVLN (Zhang et al., 2025e), AViLA (Zhang et al., 2025a)
   -       ✓      -           T       T    SiLLM (Guo et al., 2024c), TransLLaMa (Koshkin et al., 2024b), EAST (Fu
                                           et al., 2025a), DrFrattn (Zhao et al., 2025b), FineHarm (Li et al., 2025i),
                                           PsFuture (Zhao et al., 2024)
   -       ✓      -           T       S    SimulMEGA (Le et al., 2025), Cosyvoice (Du et al., 2024), DSM (Zeghidour
                                           et al., 2025)
   -       ✓      -           S       T    Divergence (Chen et al., 2024b), SimulMEGA (Le et al., 2025), ReaLLM (Seide
                                           et al., 2024), Llama-omni (Fang et al., 2024)
   -       ✓      -           S       S    StreamSpeech (Zhang et al., 2024c), EASiST (Fu et al., 2025b),
                                           SimulMEGA (Le et al., 2025)
   -       ✓      -           V       T    Videollm-online (Chen et al., 2024a), ProVideLLM (Chatterjee et al., 2025),
                                           EyesWO (Zhang et al., 2025d), Streamo (Xia et al., 2025a), ProASIST (Zhang
                                           et al., 2025c), Videollm-MOD (Wu et al., 2024b), DisPider (Qian et al., 2025),
                                           Stream-VLM (Panchal et al., 2024), Lion-FS (Li et al., 2025h),
                                           ProVideLLM (Chatterjee et al., 2025), StreamBridge (Wang et al., 2025a)
   -       -      ✓           T       T    SeqPO-SiMT (Xu et al., 2025e), Interleaved Reasoning (Xie et al., 2025)
   -       -      ✓           T       S    Seed LiveInterpret 2.0 (Cheng et al., 2025b)
   -       -      ✓           S       T    Seed LiveInterpret 2.0 (Cheng et al., 2025b)
   -       -      ✓           S       S    Seed LiveInterpret 2.0 (Cheng et al., 2025b)
   -       -      ✓           V       T    MMDuet2 (Wang et al., 2025c)

Table 4: Summary of additional literature on concurrent-streaming LLMs, complementing the discussion in Sec. 5.
