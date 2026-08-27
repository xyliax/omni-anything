- **Title:** Video Streaming Thinking: VideoLLMs Can Watch and Think Simultaneously
- **Summary:** Video Streaming Thinking turns playback time into proactive clip-level reasoning, letting online video language models keep a compact memory and answer later questions with low latency.
- **Paper Type:** system
- **Venue:** arXiv preprint 2026
- **Authors:** Yiran Guan*, Liang Yin*, Dingkang Liang, Yuliang Liu, Xiang Bai (Huazhong University of Science and Technology); Jianzhong Ju, Zhenbo Luo, Jian Luan (MiLM Plus, Xiaomi Inc.)
- **Keywords:** streaming video understanding, VideoLLM, chain-of-thought, online reasoning, knowledge graph data synthesis, reinforcement learning
- ## Orientation
    - **Background:** Video Large Language Models (VideoLLMs) answer questions about video. In live settings, the model sees the video as it arrives, so it must remember earlier events without looking ahead.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A viewer may ask a question late, but the clue may have appeared much earlier. The model needs to keep useful clues ready while still responding quickly.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** Long videos contain too many frames to keep raw details forever, and careful reasoning after the question can make the user wait.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Make the model write useful running thoughts while it watches, then answer from those thoughts plus the latest scene.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a streaming video understanding paper about the missing reasoning layer between visual-token memory systems and slow after-the-query chain-of-thought reasoning.
      claim_kind:: analyst_assessment
      evidence:: E2, E3
    - **One-Sentence Contribution:** Video Streaming Thinking (VST) improves online video question answering (QA) by generating compact thoughts while the video is still arriving, so the final answer can reuse already-processed evidence instead of starting its reasoning after the user asks.
      evidence:: E3, E4
    - **Mental Model:** Picture a live note-taker watching a video: every few moments it writes a short running note, keeps the latest scene in sight, and answers from those notes when a question arrives.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest support is the combination of online benchmark gains, low query-time latency, and ablations showing that VST data and training stages matter.
      evidence:: E11, E13, E15
        - Supports C3: VST-7B on online benchmarks; Streamforest and Streamo as closest open-source streaming baselines; overall accuracy; +2.2 points on StreamingBench and +1.4 points on OVO-Bench; supported but without reported variance.
          evidence:: E11
        - Supports C1: VST-7B on VideoHolmes latency measurement; Video-R1 with chain-of-thought as closest reasoning baseline; query-answer latency; 0.56s versus 8.80s, about 15.7x faster; supported for query-time latency, not total token cost.
          evidence:: E15
        - Supports C3: VST-SFT plus VST-RL training schedule; Qwen2.5-VL-7B base as baseline; OVO-Bench and VideoMME accuracy; 59.3 versus 50.5 on OVO-Bench and 64.9 versus 62.9 on VideoMME; supported by ablation, without repeat counts.
          evidence:: E13
    - **Main Caveat:** The latency story depends on having playback time available for pre-query thinking; the paper also acknowledges extra generated tokens and mostly text-guided memory, so VST is not a free replacement for efficient visual memory.
      claim_kind:: analyst_assessment
      evidence:: E15, E17
- ## Argument Map
    - **Problem and Stakes:** Online video understanding must obey temporal causality, meaning the model cannot use future frames, while still meeting real-time query-answer latency and finite context-window limits, where a context window is the bounded amount of tokens a model can attend to at once.
      evidence:: E2
    - **Prior Gap:** The paper positions prior online VideoLLMs as mostly managing visual memory through compression or key-value cache retrieval, where a key-value cache stores earlier attention state for reuse, while offline chain-of-thought (CoT), or step-by-step reasoning text, improves reasoning but shifts latency after the user query.
      evidence:: E2, E5
    - **Key Insight:** The key insight is to move explicit reasoning into the natural waiting time between incoming video clips, so reasoning cost is amortized over playback instead of concentrated at the moment of interaction.
      evidence:: E3, E5, E15
    - **Claims:** The paper's logical claims are that pre-query streaming thoughts can reduce query-time latency, that a dual-memory protocol can make offline VideoLLMs causal, that the training and data recipe improves accuracy, and that the method has bounded but real efficiency costs.
      evidence:: E3, E4, E11, E13, E17
        - C1: VST reduces query-answer latency for reasoning-heavy video QA by generating CoT-style thoughts before the question arrives instead of only after it.
          evidence:: E5, E15
        - C2: A short-term visual buffer plus long-term textual semantic memory lets a VideoLLM operate under temporal causality and finite context while preserving useful history.
          evidence:: E4, E6
        - C3: The VST supervised fine-tuning (VST-SFT), reinforcement learning (VST-RL), and knowledge-graph data synthesis recipe improves online benchmark accuracy and remains competitive on offline long-video reasoning benchmarks.
          evidence:: E8, E11, E12, E13
        - C4: VST is complementary to efficient visual-memory methods rather than a free substitute, because it spends extra generated tokens and relies mainly on text-guided memory.
          evidence:: E17
- ## Mechanism and Design
    - **Core Mechanism:** VST treats live video as a multi-turn conversation: each new clip produces a streaming thought, a short textual summary of useful events, and the model later answers from accumulated thoughts plus the current clip.
      evidence:: E4, E5
        - Incoming frame features are grouped into clips when the visual-token budget is reached, and each clip is processed together with previous memory to generate the next thought.
          evidence:: E4
        - The visual side keeps recent raw video tokens for precise perception, while the text side stores prior thoughts as semantic memory with first-in-first-out eviction.
          evidence:: E4
        - When the user asks, the final answer is generated directly from the current clip and accumulated memory rather than replaying the whole video or starting a long reasoning trace from scratch.
          evidence:: E5, E15
    - **Data / Control Flow:** The execution order is clip arrival, visual encoding, streaming-thought generation, memory update, and final answer on query; the training order mirrors this sequence so the model sees only past and current evidence.
      evidence:: E4, E6, E7, E8
        - At inference, streaming thoughts are scheduled before the next clip arrives, so the user-facing path after the query contains only current encoding and answer generation.
          evidence:: E15
        - During VST-SFT, training examples interleave memory, clip, thought pairs and end with the final clip, question, and answer, with next-token prediction applied only to thoughts and the final response.
          evidence:: E6
        - The synthetic-data path builds a video knowledge graph, samples evidence chains with depth-first search, and asks an offline model to generate streaming CoT and QA pairs aligned to those chains.
          evidence:: E8
    - **Design Decisions:** The design consistently chooses lightweight text memory and causal masks over keeping all raw visual evidence, trading away some visual fidelity to keep streaming feasible.
      claim_kind:: analyst_assessment
      evidence:: E4, E6, E17
        - Need: unbounded streams exceed fixed context; choice: a recent visual buffer plus long-term textual memory; closest alternative: visual-token compression or retrieval-only memory; tradeoff: summaries can omit details later needed for a question.
          claim_kind:: analyst_assessment
          evidence:: E2, E4, E17
        - Need: avoid future-frame leakage during training; choice: a streaming attention mask that exposes only a sliding visual window plus non-visual history; closest alternative: offline global attention; tradeoff: old raw frames must be represented by text memory.
          claim_kind:: analyst_assessment
          evidence:: E6
        - Need: improve thoughts without separately scoring every intermediate thought; choice: group-relative policy optimization (GRPO) with final-answer reward assigned across trajectory tokens; tradeoff: credit assignment can be noisy when a final answer depends on only some thoughts.
          claim_kind:: analyst_assessment
          evidence:: E7
    - **Implementation Surface:** The reported implementation starts from Qwen2.5-VL, freezes the visual encoder and projection layer, processes video at 2 fps, trains the 7B model on 32 x 80GB GPUs, and evaluates through lmms-eval with inference caps on visual tokens and thinking times.
      evidence:: E9
        - VST-RL uses verl with vLLM rollout and Fully Sharded Data Parallel (FSDP), while the appendix reports one epoch for both VST-SFT and VST-RL plus actor learning-rate, batch, and rollout settings.
          evidence:: E9
        - Testing caps each inference step, including streaming-think and final answer, at 8,192 video tokens and limits max thinking times to 4 for efficient evaluation.
          evidence:: E9
- ## Evaluation and Evidence
    - **Setup:** The evaluation covers online temporal reasoning with StreamingBench and OVO-Bench, offline general video understanding with VideoMME, long-video understanding with LongVideoBench, and complex reasoning with VideoHolmes.
      evidence:: E9, E10
    - **Claim-Evidence Matrix:** The paper backs the latency claim with a direct latency table, the causal-memory claim with method design, the accuracy claim with online, offline, and ablation results, and the cost boundary with its own limitation section.
      claim_kind:: analyst_assessment
      evidence:: E4, E11, E13, E15, E17
        - C1 is supported by Table 6 and the streaming pipeline: VST keeps query-time latency close to direct-answer models while reasoning baselines pay post-query CoT latency.
          evidence:: E15
        - C2 is supported mechanistically by the dual-memory formulation and streaming attention mask, but not isolated by a clean memory-component ablation.
          claim_kind:: analyst_assessment
          evidence:: E4, E6, E14
        - C3 is supported by online, offline, training-schedule, thinking-time, and model-size evaluations, though the paper does not report statistical uncertainty.
          claim_kind:: analyst_assessment
          evidence:: E11, E12, E13, E14
    - **Headline Results:** The headline result is not a single largest number but the accuracy-latency tradeoff: VST-7B improves over open-source streaming baselines on online tasks, stays competitive offline, and avoids the large post-query latency of CoT baselines.
      evidence:: E11, E12, E15
        - Supported claim: C3; configuration: VST-7B; baselines: Streamforest and Streamo; metric: benchmark accuracy; direction and delta: 79.5 versus 77.3 on StreamingBench and 59.3 versus 57.9 on OVO-Bench; caveat: no variance or repeated-run statistics reported.
          evidence:: E11
        - Supported claim: C3; configuration: VST-7B; baselines: TimeChat-Online and Video-R1; metric: accuracy; direction and delta: +6.9 on VideoMME-long, +2.6 on LongVideoBench, and +5.4 on VideoHolmes; caveat: benchmark comparability depends on identical evaluation settings.
          evidence:: E12
        - Supported claim: C1; configuration: VideoHolmes latency; baselines: Qwen2.5-VL-7B with CoT and Video-R1 with CoT; metric: query-answer latency; direction and delta: 0.56s for VST-7B versus 5.30s and 8.80s; caveat: pre-query token generation is outside QA latency.
          evidence:: E15
    - **Ablations and Sensitivity:** The ablations suggest the VST-specific data and two-stage training both matter, while more streaming thoughts help up to a point and then add redundant memory detail.
      evidence:: E13, E14
        - The VST data mix outperforms LLaVA-Vid-only supervised fine-tuning, with the reported 20K LLaVA-Vid plus 30K VST mix giving +6.6 OVO-Bench points over 50K LLaVA-Vid alone.
          evidence:: E13
        - VST-SFT and VST-RL have different reported strengths, with SFT helping backward memory and RL helping forward prediction; using both gives the best reported OVO-Bench and VideoMME scores.
          evidence:: E13
        - Increasing max streaming thinking times improves Backward accuracy through 16 steps, while Real-Time and Forward tasks plateau after about 4 steps, marking a practical budget boundary.
          evidence:: E14
    - **Reproducibility Gaps:** The paper says code, data, and models will be released and reports substantial training details, hardware, backends, datasets, and inference caps, but it does not report seeds, repeat counts, variance, full filtering acceptance rates, or release verification in the provided text.
      claim_kind:: analyst_assessment
      evidence:: E1, E9, E13, E15
- ## Technical Judgment
    - **What Holds Up:** The core systems argument holds up: when a live stream creates idle time before a query, moving reasoning into that interval can reduce observed QA latency while preserving a compact history for later temporal questions.
      claim_kind:: analyst_assessment
      evidence:: E3, E4, E15
        - The ablation that VST data plus both VST-SFT and VST-RL gives the best reported scores makes the training recipe more credible than a pure prompting story.
          claim_kind:: analyst_assessment
          evidence:: E13
        - The latency table is persuasive for query-time responsiveness because the closest reasoning baselines defer CoT generation until after the query.
          claim_kind:: analyst_assessment
          evidence:: E15
    - **Where It May Fail:** VST may fail when the stream has little idle time, when useful evidence is hard to summarize into text, when a later question needs a precise old visual detail that was evicted, or when token cost matters more than query-time latency.
      claim_kind:: analyst_assessment
      evidence:: E4, E14, E17
        - The reported plateau for some tasks after about 4 thinking steps suggests extra thoughts can become redundant rather than universally useful.
          claim_kind:: analyst_assessment
          evidence:: E14
        - The accuracy evidence is broad but not uncertainty-aware, since the paper does not report variance, confidence intervals, or repeat counts for the benchmark deltas.
          claim_kind:: analyst_assessment
          evidence:: E11, E12, E13
    - **Relation to Other Work:** Compared with streaming visual-memory systems such as Streamforest, TimeChatOnline, VideoLLM-online, Dispider, and Flash-VStream, VST shifts the emphasis from retaining visual tokens to generating evolving semantic thoughts; compared with Video-R1 or LongVILA-R1-style video reasoning, it moves reasoning before the query.
      claim_kind:: analyst_assessment
      evidence:: E2, E5, E11, E12
        - The paper's own limitation frames text-guided memory as orthogonal to streaming visual-memory mechanisms, so the clean research comparison is not replacement but complementarity.
          claim_kind:: analyst_assessment
          evidence:: E17
    - **Transferable Lesson:** For interactive AI systems, a useful pattern is to spend predictable idle time on incremental state-building, store the result in a compact form, and keep the user-triggered path short and direct.
      claim_kind:: analyst_assessment
      evidence:: E3, E5, E15
- ## Glossary
  collapsed:: true
    - Video Large Language Model: A language model extended to take video-derived visual inputs and answer natural-language questions about them.
    - online video understanding: Understanding video as it arrives over time, without using future frames that have not yet appeared.
    - context window: The bounded set of tokens the model can attend to at one time; for video, this limits how much raw visual evidence can remain visible.
    - Video Streaming Thinking: The paper's paradigm of generating intermediate thoughts during video playback and answering later from those thoughts plus the current clip.
    - chain-of-thought: Step-by-step natural-language reasoning text generated by a model before or alongside an answer.
    - streaming thought: An intermediate textual summary or reasoning update generated for a new video clip before the final user question is answered.
    - VST supervised fine-tuning: The imitation-learning stage that teaches the model the streaming thought format under causal video constraints.
    - VST reinforcement learning: The on-policy stage that samples full streaming trajectories and optimizes them using a final-answer reward; GRPO is the group-relative policy optimization method used.
    - knowledge graph: A graph of entities and relations extracted from a video; the paper samples paths through it as multi-hop evidence for synthetic training questions.
    - Fully Sharded Data Parallel: A distributed training technique that shards model parameters and optimizer state across GPUs to reduce per-device memory pressure.
    - query-answer latency: The measured time from user query submission to the model's response, not necessarily the total computation spent while the video was playing.
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/metadata | Abstract and header | high
      locator:: title block and abstract
      quote:: Video Streaming Thinking: VideoLLMs Can Watch and Think Simultaneously. Yiran Guan, Liang Yin, Dingkang Liang, Jianzhong Ju, Zhenbo Luo, Jian Luan, Yuliang Liu, Xiang Bai. Code, data, and models will be released at https://github.com/1ranGuan/VST.
    - **E2:** gap/paper_statement | 1 Introduction | high
      locator:: paragraphs on online challenges and prior methods
      quote:: the core challenges of online video understanding lie in strict temporal causality, real-time processing, and a finite context window. Several prior methods primarily improve context-window efficiency by explicitly managing visual tokens for compression or by retrieving from the KV cache.
    - **E3:** insight/paper_statement | 1 Introduction | high
      locator:: VST motivation paragraph
      quote:: we introduce the Video Streaming Thinking (VST) to resolve the trade-off between explicit reasoning and real-time responsiveness, shifting the LLM backend from passive waiting to active, intermittent reasoning during video consumption.
    - **E4:** system_design/implementation_detail | 2.1 The Video Streaming Thinking (VST) Paradigm | high
      locator:: opening paragraph and Fig. 2
      quote:: This process synthesizes key visual details and event dynamics into a dual-memory system: maintaining a short-term native video memory for the current visual context, while accumulating a long-term textual semantic memory of past events.
    - **E5:** method/paper_statement | 2.1 The Video Streaming Thinking (VST) Paradigm | high
      locator:: advantages after Eq. 1
      quote:: It amortizes the computational cost of Chain-of-Thought (CoT) generation over the pre-query phase. This strategy effectively achieves test-time scaling to boost performance without incurring additional latency at the moment of user interaction.
    - **E6:** algorithm/implementation_detail | 2.2 Training Method for VST | high
      locator:: Stage 1: VST-SFT
      quote:: we apply a streaming video attention mask. This mask restricts the model's attention to a fixed-size window of recent visual tokens, mirroring the short-term visual buffer used during inference.
    - **E7:** algorithm/implementation_detail | 2.2 Training Method for VST | high
      locator:: Stage 2: VST-RL
      quote:: We compute the reward solely based on the final answer via verifiable reward functions. To encourage the model to generate useful streaming thoughts, the calculated advantage is assigned to all generated tokens within the entire trajectory.
    - **E8:** method/implementation_detail | 2.3 Data Synthesis Pipeline for VST | high
      locator:: data synthesis and curation paragraphs
      quote:: we model entities and their temporal relationships within long videos as knowledge graphs. By sampling paths from these graphs to form evidence chains, we prompt an offline VideoLLM to generate complex QA pairs and their corresponding intermediate CoTs.
    - **E9:** experiment_setup/implementation_detail | 3.1 Implementation Details | high
      locator:: implementation paragraph
      quote:: We adopt Qwen2.5-VL as our base offline VideoLLM, processing input videos at 2 fps. Both VST-SFT and VST-RL (7B model) training stages are conducted on 32 x 80GB VRAM GPUs.
    - **E10:** experiment_setup/paper_statement | 3.2 Benchmarks | high
      locator:: benchmark description paragraph
      quote:: Streaming-Bench and OVO-Bench are utilized for online video understanding, focusing on the model's online reasoning capabilities and temporal awareness. VideoMME serves as a comprehensive offline benchmark, while LongVideoBench is designed to evaluate long-form video understanding.
    - **E11:** result/experiment_result | 3.3 Online Video Benchmark Results | medium
      locator:: Tables 1 and 2 discussion
      quote:: VST-7B achieves 79.5% on StreamingBench and 59.3% on OVO-Bench, clearly outperforming prior open-source streaming SOTA models, including Streamforest (77.3%) on StreamingBench and Streamo (57.9%) on OVO-Bench.
    - **E12:** result/experiment_result | 3.4 Offline Video Benchmark Results | medium
      locator:: Table 3 discussion
      quote:: On long-video benchmarks, VST-7B achieves 55.3% on VideoMME-long, outperforming TimeChat-Online by +6.9%, and 58.0% on LongVideoBench, exceeding it by +2.6%. On the reasoning benchmark VideoHolmes, VST-7B reaches 41.9%, surpassing VideoR1 by +5.4%.
    - **E13:** ablation/ablation | 3.5 Ablation Study | medium
      locator:: Table 4 discussion
      quote:: the mix of 20K LLaVA-Vid and 30K VST data achieves a +6.6% gain on the OVO-Bench. Combining both stages (VST-SFT & VST-RL) yields the highest overall performance on both OVO-Bench (59.3%) and VideoMME (64.9%).
    - **E14:** ablation/ablation | 3.5 Ablation Study | medium
      locator:: Fig. 5 and Table 5 discussion
      quote:: For the Backward task, accuracy increases from 53.3% and grows continuously from 1 to 16 steps, ultimately reaching 57.5%. For the Real-Time and Forward tasks, initial thinking steps significantly aid in understanding visual information. However, performance reaches a plateau for >= 4 steps.
    - **E15:** result/experiment_result | 3.6 Analysis | medium
      locator:: Efficiency Analysis and Table 6
      quote:: Qwen2.5-VL-7B w/CoT has 5.30s QA latency, Video-R1 w/CoT has 8.80s, and VST-7B has 0.56s. streaming think is executed asynchronously before the query and finishes within the clip inter-arrival interval.
    - **E16:** result/case_study | 3.6 Analysis | low
      locator:: Case Study and Fig. 6
      quote:: VST-7B employs streaming thinking to continuously update its evidence (e.g., timestamps and event triggers) as the video memories. This pre-query evidence accumulation allows VST to correctly deduce the time-based rule.
    - **E17:** limitation/limitation | 5 Conclusion | high
      locator:: Limitation and Future Works
      quote:: While the computation of streaming thoughts can be scheduled in parallel with incoming video clips, the additional LLM token consumption is still non-negligible. A promising direction is to explore latent reasoning to enable more token-efficient streaming thinking.
