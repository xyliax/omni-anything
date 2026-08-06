- **Title:** Thinking in Streaming Video
- **Summary:** ThinkStream turns video reasoning into an incremental watch-think-speak loop, using short reasoning traces as compact long-term memory so streaming video assistants can answer with lower latency and bounded visual context.
- **Paper Type:** system
- **Venue:** arXiv preprint 2026
- **Authors:** Zikang Liu, Longteng Guo, Handong Li, Xingjian He, Ruyi Ji, and Jing Liu (Institute of Automation, Chinese Academy of Sciences; University of Chinese Academy of Sciences); Ru Zhen, Xiaoming Ren, Yanhao Zhang, and Haonan Lu (OPPO AI Center, OPPO Inc.)
- **Keywords:** streaming video understanding, incremental reasoning, multimodal large language model, KV cache, reinforcement learning with verifiable rewards, CUDA Graph inference
- ## Orientation
    - **Background:** This paper sits in video-language AI, where a model must connect what it sees in video with a user's question. In live use, the video arrives piece by piece rather than as a finished clip.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A helpful assistant should watch a changing scene, keep track of what has happened, and answer only when the needed evidence has appeared.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** Old moments can matter later, but keeping every visual detail makes the model slower and heavier as the stream continues.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Think while watching: keep the freshest visual detail, turn older moments into short reasoning notes, and decide at each step whether to speak or wait.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a multimodal-systems paper about continuous video input, where the gap is not just recognizing frames but deciding when enough evidence has arrived to answer while memory and latency stay bounded.
      claim_kind:: analyst_assessment
      evidence:: E2, E3
    - **One-Sentence Contribution:** ThinkStream improves streaming video question answering by making the model update a short running interpretation before each speak-or-wait decision, so old visual detail can be replaced by compact reasoning memory.
      evidence:: E5, E6
    - **Mental Model:** Picture a careful observer watching a live scene, jotting a short note after each new clip, keeping the latest view on the desk, and using the notes to remember earlier moments without replaying the whole video.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is the combination of streaming benchmark gains, memory-representation ablations, and latency profiling under a real-time threshold.
      evidence:: E8, E14, E16
        - Supports C1: ThinkStream-3B on OVO-Bench; closest online baseline Streamo-3B; average score; 59.66 vs 51.64; supported, but no variance or repeat count is reported.
          evidence:: E8
        - Supports C3: RLVR-optimized chain-of-thought memory on the memory ablation; closest cold-start CoT memory variant; average score; 67.0 vs 63.3; supported, but uncertainty is not reported.
          evidence:: E14
        - Supports C4: CUDA Graph streaming backend over growing video context; eager Qwen2.5-VL-3B baseline; token completion latency; ThinkStream stays under 0.5 s while baseline stays above 1.0 s; supported for the profiled setup only.
          evidence:: E16
    - **Main Caveat:** The paper reports strong single-system results but leaves trust fields thin: no error bars, repeat counts, released-artifact verification, or independent real deployment evaluation are provided in the text.
      claim_kind:: analyst_assessment
      evidence:: E8, E11, E18
- ## Argument Map
    - **Problem and Stakes:** The paper targets streaming video understanding, meaning video reasoning where the model sees only the current prefix of a live stream and must remain causal, low-latency, and memory-bounded. The stakes are interactive assistants, monitoring systems, and embodied agents that cannot wait for a full video before acting.
      evidence:: E2
    - **Prior Gap:** The paper argues that batch video reasoning waits for the whole clip before reasoning, while many online systems manage visual memory or output timing without making reasoning itself the memory and decision process. Its claimed gap is therefore at the joint boundary of temporal causality, semantic memory, and when-to-speak behavior.
      evidence:: E3, E4
    - **Key Insight:** The key insight is that short chain-of-thought tokens, meaning generated text that records the model's intermediate interpretation, can act as semantic compression of earlier video and as the control signal for speaking. This turns reasoning from an offline answer-writing trick into streaming state.
      evidence:: E5, E6
    - **Claims:** The paper's case decomposes into four falsifiable claims about accuracy, memory, training, and runtime behavior.
      claim_kind:: analyst_assessment
        - C1: The Watch-Think-Speak paradigm and ThinkStream improve streaming video benchmark accuracy over the base Qwen2.5-VL-3B model and open-source online video models.
          evidence:: E8, E9
        - C2: Reasoning-Compressed Streaming Memory (RCSM), which keeps recent visual tokens and old reasoning tokens, preserves long-horizon understanding while preventing dense visual cache growth from increasing without bound.
          evidence:: E6, E10, E13
        - C3: Streaming Reinforcement Learning with Verifiable Rewards (RLVR), which rewards answer correctness, output format, and response timing, makes reasoning tokens better long-term memory than naive caption tokens or cold-start reasoning alone.
          evidence:: E7, E14
        - C4: The custom CUDA Graph backend, which replays fixed decode and eviction kernels, provides enough throughput and latency control for real-time streaming inference with explicit key-value cache manipulation.
          evidence:: E15, E16, E18
- ## Mechanism and Design
    - **Core Mechanism:** ThinkStream wraps a multimodal large language model, meaning a language model that can read visual and text tokens, in a Watch-Think-Speak loop: each chunk triggers a short <think> update, then either <silent> or <response>. RCSM uses those reasoning tokens as compact memory while evicting older dense video tokens from the key-value cache, the stored attention state used to avoid recomputing past tokens.
      evidence:: E5, E6
        - Watch: the model receives the next temporal video chunk and the user instruction while respecting strict causality, so future chunks cannot influence the current step.
          evidence:: E2, E5
        - Think: the model emits a short reasoning segment that summarizes events, updates hypotheses, or refines temporal relations using the current chunk and accumulated memory.
          evidence:: E5
        - Speak: the model emits either <response> plus content when evidence is sufficient, or <silent> when it should keep watching.
          evidence:: E5
    - **Data / Control Flow:** The runtime state combines a visual sliding window, meaning a fixed recent span of video tokens, with all accumulated reasoning and action tokens. As a new chunk arrives, outdated visual tokens are evicted, the new chunk is prefetched, and decoding produces the next thought plus action.
      evidence:: E6, E18
        - RCSM stores recent visual key-value entries plus key-value entries for generated reasoning and action tokens; the paper defines the visual retention size with window W.
          evidence:: E6
        - During RLVR rollout, the policy samples step-by-step trajectories over streaming chunks, then receives rule-based rewards for format, timing, and accuracy.
          evidence:: E7
        - During inference, prefill means processing newly arrived visual tokens into cache, while decode means generating output tokens autoregressively from that cache; pruning is captured with decode in replayable CUDA Graphs.
          evidence:: E18
    - **Design Decisions:** The design trades exact visual history for compressed semantic continuity, then uses verifiable rewards and custom cache control to make that trade practical. The nearest alternatives reported are keeping visual memory, caption tokens, external trigger heads, or using standard inference engines without custom cache eviction.
      claim_kind:: analyst_assessment
      evidence:: E4, E6, E7, E18
        - Need: long streams cannot keep every visual token; design choice: retain recent visual detail and old reasoning tokens; alternative: purely visual memory or caption memory; tradeoff: semantic summaries may omit low-level details needed later.
          evidence:: E4, E6, E14
        - Need: reasoning traces must be useful and responses must be timely; design choice: rule-verifiable rewards over accuracy, format, and response time; tradeoff: the RLVR subset uses deterministic answer formats rather than fully open-ended verification.
          evidence:: E7, E17
        - Need: explicit key-value cache eviction with low launch overhead; design choice: eager prefill for variable visual tokens plus CUDA Graph replay for decode and eviction; alternative: native transformers or optimized engines with limited custom cache updates.
          evidence:: E18
    - **Implementation Surface:** The reported implementation starts from Qwen2.5-VL-3B, trains with cold start and GRPO-style RL on 8 NVIDIA H2O GPUs, samples video at 2 FPS, and uses specialized kernels for both training and inference. The dataset pipeline segments videos, captions segments with Qwen3-VL-235B-A22B-Instruct, synthesizes instructions, and generates time-grounded chain-of-thought traces.
      evidence:: E11, E17, E18
        - Group Relative Policy Optimization (GRPO), a reinforcement learning method that compares multiple sampled outputs for the same item, is used with group size 8 and KL regularization in the paper's formulation.
          evidence:: E7, E11
        - CUDA Graphs, which replay a fixed GPU execution graph to avoid per-step launch overhead, are used for decode and eviction, while FlashInfer accelerates sampling and FlashAttention-style key-value cache attention handles memory access.
          evidence:: E18
        - The ThinkStream dataset contains 110K cold-start instances and 9K RLVR instances built from time-grounded captions, diverse interaction modes, and deterministic reward-friendly question formats.
          evidence:: E17
- ## Evaluation and Evidence
    - **Setup:** The main system is ThinkStream-3B initialized from Qwen2.5-VL-3B and evaluated on streaming benchmarks OVO-Bench and StreamingBench Real-Time plus offline video benchmarks VideoMME and Long VideoBench. Training uses cold-start supervised data followed by RLVR, with videos sampled at 2 FPS on a single 8-H2O-GPU node.
      evidence:: E8, E9, E10, E11
    - **Claim-Evidence Matrix:** The evidence is strongest where a claim has both benchmark improvement and an ablation, and weakest where it depends on future release or unreported statistical details.
      claim_kind:: analyst_assessment
      evidence:: E8, E14, E16, E18
        - C1: Streaming accuracy is supported by OVO-Bench and StreamingBench averages against base and online baselines, but the paper does not report variance, repeat runs, or significance tests.
          evidence:: E8, E9
        - C2: Memory usefulness is supported by offline benchmark preservation and visual-window ablation, with the strongest direct result at a 20 s visual key-value cache window.
          evidence:: E10, E13
        - C3: RLVR-optimized reasoning memory is supported by the memory ablation, where caption memory underperforms and RLVR-optimized CoT memory is best.
          evidence:: E14
        - C4: Runtime feasibility is supported by decode-throughput and latency profiling, though the evidence is limited to the paper's hardware and backend implementation.
          evidence:: E15, E16, E18
    - **Headline Results:** The headline results show a small model gaining most in online video settings while preserving offline video ability. The closest comparisons are not always the numerically largest gap, so the meaningful baselines are the base Qwen2.5-VL-3B and the strongest open-source online systems.
      evidence:: E8, E9, E10
        - C1: On OVO-Bench, ThinkStream-3B beats Qwen2.5-VL-3B by 8.66 average points and Streamo-3B by 8.02 points; uncertainty is not reported, so support is directional rather than statistical.
          evidence:: E8
        - C1: On StreamingBench Real-Time, ThinkStream-3B scores 75.00, ahead of Dispider-7B at 67.63 and GPT-4o at 73.28 in the reported table; repeat count is not reported.
          evidence:: E9
        - C2: On offline video benchmarks, ThinkStream-3B averages 59.4 versus 54.4 for Qwen2.5-VL-3B, suggesting visual-token eviction does not erase standard video ability in the reported setup.
          evidence:: E10
    - **Ablations and Sensitivity:** The ablations make the mechanism more credible because they vary reasoning budget, visual cache window, and memory representation rather than only reporting end-to-end wins. They also expose the paper's practical operating point: enough reasoning and a moderate visual window help, but excess decoding budget raises latency.
      evidence:: E12, E13, E14
        - C3: Raising the reasoning budget from 0 to 20 tokens per second improves OVO-Backward from 41.8 to 52.3, while 30 tokens gives only 52.6 and increases latency to 505 ms.
          evidence:: E12
        - C2: The visual key-value cache window peaks at 20 s in the reported sweep, with lower OVO-Backward at 5 s, 10 s, and 30 s.
          evidence:: E13
        - C3: RLVR-optimized CoT memory outperforms no memory, discrete caption memory, and cold-start CoT memory, directly supporting reasoning-as-memory over a naive text-caption substitute.
          evidence:: E14
    - **Reproducibility Gaps:** The paper reports implementation choices, training hyperparameters, hardware, dataset construction, and a future code/model/data release, but the provided text does not verify that artifacts are already available. Not reported: random seeds, repeat counts, variance or error bars, exact benchmark scripts, full data filtering code, and independent reproduction on other GPUs.
      claim_kind:: analyst_assessment
      evidence:: E11, E17, E18
- ## Technical Judgment
    - **What Holds Up:** The strongest part is the alignment between problem, mechanism, and ablations: streaming needs bounded state, RCSM supplies a concrete state representation, and the memory plus window ablations test that representation directly. The latency profiling also connects the algorithmic cache idea to a runtime implementation rather than leaving it as a modeling claim.
      claim_kind:: analyst_assessment
      evidence:: E6, E13, E14, E15, E16
    - **Where It May Fail:** The approach may fail when a later answer depends on fine visual details that were evicted before the reasoning trace captured them, because RCSM deliberately replaces dense visual evidence with compact text state. It may also be brittle outside deterministic reward formats, since the RLVR training subset is built around automatically verifiable multiple-choice, binary, and counting queries.
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E13, E17
    - **Relation to Other Work:** Compared with visual-memory and key-value cache compression systems, ThinkStream shifts part of memory from pixels to generated semantic state; compared with event-trigger systems, it makes the same generative model decide whether to speak. Compared with offline video chain-of-thought or RL methods, its novelty is tying reasoning to the prefix-by-prefix streaming loop rather than the final answer only.
      claim_kind:: analyst_assessment
      evidence:: E3, E4, E6, E7
    - **Transferable Lesson:** A useful systems pattern is to let a model's intermediate text become an explicit state interface: once an expensive raw modality has been interpreted, keep the recent raw window plus a compact semantic log, then train and benchmark the log as a memory representation rather than treating it as explanation-only output.
      claim_kind:: analyst_assessment
      evidence:: E6, E14, E18
- ## Glossary
  collapsed:: true
    - streaming video understanding: Video-language reasoning where video arrives over time and the model must answer using only observations available so far.
    - Watch-Think-Speak: ThinkStream's interaction loop: watch a new video chunk, write a short reasoning update, then either stay silent or produce a response.
    - key-value cache: Stored attention keys and values from earlier tokens that let a transformer generate new tokens without recomputing the full past context.
    - Reasoning-Compressed Streaming Memory: The paper's memory representation that keeps recent visual tokens and uses generated reasoning/action tokens as compact long-term semantic anchors.
    - reasoning tokens: Generated intermediate text that records the model's current interpretation of the stream; in this paper it also serves as memory.
    - Reinforcement Learning with Verifiable Rewards: Training where reward can be computed automatically from verifiable conditions such as answer correctness, required output format, and response timing.
    - Group Relative Policy Optimization: A reinforcement learning objective that samples multiple candidate trajectories for the same input and optimizes the policy using relative advantages with clipping and KL regularization.
    - prefill and decode: Prefill processes incoming context into the cache; decode generates output tokens one at a time from the cache.
    - CUDA Graph: A GPU execution feature that records a fixed sequence of operations and replays it to reduce per-step launch overhead.
    - visual sliding window: A fixed recent span of video chunks whose dense visual tokens remain in cache while older visual chunks are evicted.
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/metadata | Title and authors | high
      locator:: title block and arXiv header
      quote:: arXiv:2603.12938v1 [cs.CV] 13 Mar 2026. Thinking in Streaming Video. Zikang Liu, Longteng Guo, Handong Li, Ru Zhen, Xingjian He, Ruyi Ji, Xiaoming Ren, Yanhao Zhang, Haonan Lu, and Jing Liu.
    - **E2:** problem/paper_statement | 1 Introduction | high
      locator:: constraints paragraph
      quote:: Streaming scenarios impose several fundamental constraints: strict causality, where reasoning must rely only on observations available up to the current moment; low computation and memory usage; and timely interaction, which demands that the system maintain an up-to-date interpretation.
    - **E3:** gap/paper_statement | 1 Introduction | high
      locator:: batch paradigm gap paragraph
      quote:: Most existing video reasoning paradigms remain fundamentally batch: the model first consumes a long video context and only then performs multi-step reasoning to produce an answer. This design introduces unacceptable latency and weakens the connection between reasoning steps and the evidence that triggered them.
    - **E4:** prior_work/paper_statement | 2 Related Work | medium
      locator:: Sections 2.1 and 2.2
      quote:: Existing approaches heavily depend on dedicated classification heads or external event triggers. Conversely, our framework eschews external classifiers; by integrating a generative reasoning phase, the model autonomously determines whether to remain silent or respond.
    - **E5:** method/paper_statement | 3 Streaming Watch-Think-Speak Paradigm | high
      locator:: Sections 3.1 and 3.2
      quote:: At each step, the model observes a newly arrived video chunk and performs a short reasoning update that integrates the new evidence with previously accumulated context. Based on this evolving understanding, the model determines whether the available evidence is sufficient to produce a response.
    - **E6:** system_design/implementation_detail | 4.1 Reasoning-Compressed Streaming Memory | high
      locator:: RCSM definition and eviction paragraph
      quote:: The core idea of RCSM is to treat reasoning tokens as compressed semantic representations of earlier visual observations. Instead of storing the entire history of dense visual tokens, the model gradually replaces outdated visual features with the reasoning traces generated during the streaming reasoning process.
    - **E7:** algorithm/implementation_detail | 4.2 Streaming-Context RLVR Training | high
      locator:: reward design paragraph
      quote:: We formulate a rule-based reward system comprising three integral components: an accuracy reward, a format reward, and a time reward. The time reward quantifies the temporal discrepancy between the model's response step and the ground-truth step.
    - **E8:** result/experiment_result | 6.1 Main Results | medium
      locator:: Table 1 and OVO-Bench paragraph
      quote:: ThinkStream-3B achieves an overall average score of 59.66, significantly surpassing both its base model Qwen2.5-VL-3B (51.00) and competing open-source online models such as Streamo-3B (51.64) on OVO-Bench.
    - **E9:** result/experiment_result | 6.1 Main Results | medium
      locator:: Table 2 and StreamingBench paragraph
      quote:: On the StreamingBench Real-Time detailed in Tab. 2, ThinkStream-3B attains an average score of 75.00. This vastly exceeds other open-source online MLLMs like Dispider-7B (67.63) and demonstrates highly competitive performance against GPT-4o (73.28).
    - **E10:** result/experiment_result | 6.1 Main Results | medium
      locator:: Table 3 and offline benchmark paragraph
      quote:: Despite aggressively evicting visual tokens, ThinkStream-3B achieves highly competitive performance. Specifically, our model achieves a score of 61.9 on VideoMME and 56.4 on Long VideoBench, with an overall average score of 59.4.
    - **E11:** experiment_setup/implementation_detail | 6 Experiments | high
      locator:: implementation details paragraph
      quote:: We initialize our framework based on the Qwen2.5-VL-3B model. During the Cold Start phase, we train the model with a batch size of 64 and a learning rate of 1 x 10^-5. In the subsequent Reinforcement Learning phase, we employ a batch size of 8.
    - **E12:** ablation/ablation | 6.2 Ablation Study | medium
      locator:: Table 4 reasoning token budget
      quote:: Scaling the budget from 0 to 20 tokens significantly improves the OVO-Backward score from 41.8 to 52.3. However, allocating beyond 20 tokens per second results in marginal performance gains while decoding latency jumps from 380 ms to 505 ms.
    - **E13:** ablation/ablation | 6.2 Ablation Study | medium
      locator:: Table 5 visual KV cache window
      quote:: Setting the window size to 20 seconds achieves the best performance, peaking at 75.0 on StreamingBench Real-Time and 52.3 on OVO-Backward. Narrower windows such as 5s and 10s result in lower OVO-Backward scores.
    - **E14:** ablation/ablation | 6.2 Ablation Study | medium
      locator:: Table 6 memory representation and RLVR
      quote:: Posttraining the model with RLVR further boosts average performance by 4.3 points, reaching 64.8, demonstrating that reasoning tokens learn to act as a far superior, highly compressed long-term memory compared to naive discrete captions.
    - **E15:** result/profiling | 6.3 Efficiency and Real-Time Analysis | medium
      locator:: Figure 3 token decoding speed paragraph
      quote:: At a batch size of 1, our engine delivers 154.07 tokens/s compared to the baseline's 30.06 tokens/s, representing a more than 5x speedup. At a batch size of 8, our decoding speed scales efficiently to 766.87 tokens/s.
    - **E16:** result/profiling | 6.3 Efficiency and Real-Time Analysis | medium
      locator:: Figure 4 latency scaling paragraph
      quote:: Our combination of algorithmic KV cache eviction and engineering optimizations ensures that the end-to-end inference latency remains flat. It consistently stays below the 0.5s real-time threshold required for 2 FPS inputs.
    - **E17:** experiment_setup/paper_statement | 5 ThinkStream Dataset | medium
      locator:: dataset construction summary
      quote:: We ultimately construct 110K Cold Start instances paired with detailed reasoning traces, alongside 9K RLVR instances strictly formatted for verifiable reward optimization. Comprehensive details regarding the video source, dataset distributions and prompt templates are provided in the Appendix.
    - **E18:** implementation/implementation_detail | A More Implementation Details | medium
      locator:: Appendix A.1 and A.2
      quote:: Recording both decoding and pruning operations into static CUDA graphs eliminates per-step kernel launch overhead while preserving explicit control over KV cache manipulation. During training, we utilize FlexAttention to implement RCSM and incorporate the Liger Kernel.
