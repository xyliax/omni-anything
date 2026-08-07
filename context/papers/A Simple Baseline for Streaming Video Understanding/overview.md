- **Title:** A Simple Baseline for Streaming Video Understanding
- **Summary:** SimpleStream shows that a fixed recent-frame window on a strong video-language model is a hard baseline for streaming video understanding, so memory-heavy systems must prove gains on disaggregated perception and memory slices.
- **Paper Type:** benchmark
- **Venue:** arXiv preprint 2026
- **Authors:** Yujiao Shen, Shulin Tian, Jingkang Yang, Ziwei Liu; S-Lab, Nanyang Technological University
- **Keywords:** streaming video understanding, video-language models, recent-frame baseline, context management, perception-memory trade-off, OVO-Bench, StreamingBench
- ## Orientation
    - **Background:** Streaming video understanding is about answering questions while a video is still arriving. The model may use what it has already seen, but not future frames.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A live assistant must decide what visual evidence to keep so it can answer now without rereading the whole video.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** Old events can matter, but too much old material can crowd out the clear view of the current scene.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Keep the latest clear frames first, and treat added history as something that must prove it helps.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as an evaluation-baseline paper for streaming video understanding, where a model must answer from the video seen so far; it challenges the assumption that better online performance mainly comes from more elaborate memory modules.
      claim_kind:: analyst_assessment
      evidence:: E2, E5
    - **One-Sentence Contribution:** SimpleStream improves the evaluation standard for online video question answering by showing that keeping only the latest frames and feeding them directly to a video-language model (VLM, a model that reads visual frames and text together) is already a strong baseline.
      evidence:: E3, E5
    - **Mental Model:** Picture a live camera assistant that answers by looking at the last few clear snapshots on its desk, instead of carrying a thick notebook whose older pages can distract it from what is happening now.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is that the same small-window rule is competitive on OVO-Bench and StreamingBench while staying efficient, and the ablations show why added history is not a free win.
      evidence:: E5, E8, E9, E12
        - Supports C1: Qwen3-VL-8B plus the latest four frames; HERMES as strongest published streaming baseline; OVO-Bench average accuracy; 67.7% versus 59.2%, a +8.5 point margin; supports the recent-window baseline as competitive.
          evidence:: E5
        - Supports C1: Qwen3-VL-8B plus the latest four frames; HERMES on StreamingBench real-time visual understanding; accuracy; 80.59% versus 79.44%; supports transfer beyond one benchmark.
          evidence:: E5
        - Supports C2: controlled recent-window ablation; same prompt and decoding; overall and real-time accuracy; four frames beats eight and sixteen frames; supports non-monotonic context benefits.
          evidence:: E8
        - Supports C3: Visual-RAG with retrieved historical chunks; matched recent-window baseline; memory tracks improve but real-time tracks and overall accuracy fall; supports a perception-memory trade-off.
          evidence:: E9
    - **Main Caveat:** The result is a strong-baseline result, not a long-horizon memory solution: the evidence is tied to Qwen2.5-VL and Qwen3-VL backbones and to benchmarks that reward recent-scene perception heavily.
      claim_kind:: analyst_assessment
      evidence:: E11, E13, E14
- ## Argument Map
    - **Problem and Stakes:** The paper frames streaming video question answering as causal, budgeted context management: at each query, the system must build a small working context from the observed video prefix. The stake is methodological: if a simple recent-window rule already wins, memory-heavy streaming systems need stronger evidence than architectural complexity.
      evidence:: E2, E3
    - **Prior Gap:** Prior streaming methods often differ in how they preserve history, including memory banks, retrieval over old representations, key-value cache (KV cache, saved attention state used by transformer models) compression, and latent states, but the simple recent-context baseline was not treated as the primary reference point.
      evidence:: E2, E15
    - **Key Insight:** A strong backbone with clear, uncompressed recent visual evidence can be more valuable than a larger but noisier historical context. The paper's insight is not that memory is useless, but that recent-scene perception is strong enough to invalidate weak memory-module comparisons.
      evidence:: E3, E5, E10
    - **Claims:** The paper's logical claims are baseline strength, non-monotonic context value, a perception-memory trade-off, and the need for cleaner reporting.
      evidence:: E5, E8, E10, E11
        - C1: A recent-N-frame input policy with an off-the-shelf VLM can match or surpass published streaming video systems under the paper's shared benchmark protocols.
          evidence:: E3, E5, E6
        - C2: More visual context is not uniformly better; the best window depends on backbone family, scale, and benchmark slice.
          evidence:: E7, E8
        - C3: Historical memory or retrieval can improve recall-oriented slices, but often reduces real-time perception of the current scene.
          evidence:: E9, E10
        - C4: Future streaming evaluations should include strong recency baselines and report perception, memory recall, hallucination robustness, and efficiency separately.
          evidence:: E11, E14
- ## Mechanism and Design
    - **Core Mechanism:** SimpleStream uses a sliding window (a fixed-size set that moves forward with time): for a query at time t and window size N, it sends only frames from t-N+1 through t plus the text query to the base VLM. Frames outside the window are discarded, so per-query computation and memory are bounded by N rather than stream length.
      evidence:: E3
    - **Data / Control Flow:** At inference time, the video stream is sampled, the visible prefix is clipped to the latest N frames, the query is appended, and the unchanged VLM answers from that bounded input. In the main experiments, SimpleStream samples the visible stream at one frame per second and evaluates N in the reported frame caps.
      evidence:: E3, E4
    - **Design Decisions:** The design deliberately removes extra mechanisms so the baseline isolates what recent visual evidence and backbone capability already provide. Its main trade-off is sharp: it protects present evidence and efficiency, but gives up direct access to events outside the window.
      evidence:: E3, E14
        - Need: avoid confounding a baseline with new training or memory modules; choice: no memory bank, retrieval, vision compression, KV-cache compression, or fine-tuning; trade-off: weaker explicit long-range recall.
          evidence:: E3, E14
        - Need: bound streaming cost; choice: discard frames outside the recent window; closest alternative: expand the working context with external memory, retrieval, compression, or latent state; trade-off: simpler cost model but no persistent history.
          evidence:: E3, E15
        - Need: compare against prior systems fairly; choice: use official protocols, reported frame budgets or rates, and SimpleStream caps of two, four, or eight recent frames at one frame per second; trade-off: protocol matching still leaves model-specific pipelines and prompts.
          evidence:: E4
    - **Implementation Surface:** The implementation surface is an inference-time input policy around open-source Qwen2.5-VL and Qwen3-VL backbones, with a project page and codebase reported. There is no new architecture to port; reproducing the result mainly requires matching the sampler, frame window, prompt path, benchmark scorer, and backbone checkpoint.
      evidence:: E1, E3, E4
- ## Evaluation and Evidence
    - **Setup:** The main evaluation uses OVO-Bench (an online-video benchmark with memory, real-time perception, and future-oriented tasks) and StreamingBench (a streaming real-time understanding benchmark), comparing six offline video LLMs and seven streaming video LLMs. SimpleStream is instantiated with Qwen2.5-VL and Qwen3-VL backbones and recent windows of two, four, or eight frames for the main comparison.
      evidence:: E4
    - **Claim-Evidence Matrix:** The evidence supports the baseline-strength claim most directly, supports the context-length and perception-memory claims through ablations, and supports the benchmark-reporting claim through a conceptual audit of benchmark categories.
      claim_kind:: analyst_assessment
      evidence:: E5, E8, E9, E11
        - C1: Main table comparisons show SimpleStream ahead of HERMES on OVO-Bench average and StreamingBench accuracy, with backward recall still competitive rather than dominant.
          evidence:: E5, E6
        - C2: Window and scale ablations show gains from two to four frames, then plateaus or declines for many settings, with larger windows useful only for some higher-capacity checkpoints.
          evidence:: E7, E8
        - C3 and C4: Visual-RAG and cross-method trade-off analysis show memory gains paired with perception losses, while HLD and macro-average analysis explain why aggregated benchmark scores can hide that split.
          evidence:: E9, E10, E11
    - **Headline Results:** The headline result is that Qwen3-VL with four recent frames reaches 67.7% on OVO-Bench and 80.59% on StreamingBench, beating the paper's strongest published streaming comparison while using no memory module. Efficiency is also favorable: SimpleStream-4f has the lowest reported peak GPU memory and is second-fastest in time to first token among the compared streaming methods.
      evidence:: E5, E12
    - **Ablations and Sensitivity:** Ablations show that context length has a sweet spot rather than a simple scaling law: four frames is often better than two, but eight or sixteen frames can degrade real-time accuracy, and model scale changes the optimum without making it monotonic. Visual-RAG (retrieval-augmented generation over visual chunks, here adding retrieved past chunks to the recent frames) helps selected memory tracks but lowers overall accuracy.
      evidence:: E7, E8, E9
    - **Reproducibility Gaps:** Reported reuse aids include a codebase, project page, benchmark names, scorer protocol, backbones, frame rates, and frame caps; statistical uncertainty, repeat counts, and detailed hardware for all runs are not reported in the supplied text. Because many headline deltas are benchmark accuracies without variance, their evidence strength is medium rather than high.
      claim_kind:: analyst_assessment
      evidence:: E1, E4, E5, E12
- ## Technical Judgment
    - **What Holds Up:** The baseline is technically hard to dismiss because it changes only the input policy, controls the context window, and reports against named offline and streaming baselines on public benchmarks. The most durable lesson is the negative control: a memory module should not be credited unless it beats a matched recent-window baseline on the capability slice it claims to improve.
      claim_kind:: analyst_assessment
      evidence:: E3, E4, E5, E8
    - **Where It May Fail:** The result may weaken on backbones with poorer short-range perception, on tasks whose answer truly depends on events outside the recent window, or on benchmarks that balance memory recall more heavily than present perception. It also does not establish a mechanism for long-horizon video memory; it establishes a demanding baseline and an evaluation critique.
      claim_kind:: analyst_assessment
      evidence:: E11, E13, E14
    - **Relation to Other Work:** Compared with StreamForest-style external memory, ReKV-style retrieval, HERMES-style KV-cache compression, and Dispider-style latent memory, SimpleStream removes the historical-state mechanism and asks whether that mechanism adds measurable value. The paper therefore functions as a control condition for memory-centric streaming work, not as a replacement for all memory research.
      claim_kind:: analyst_assessment
      evidence:: E15, E14
    - **Transferable Lesson:** Use a recent-first, history-on-demand design pattern: preserve a clean current input by default, add historical state only when the task demands it, and measure both the recall gain and the perception cost. This transfers beyond video to any online system where a larger context can distract the model from high-quality fresh evidence.
      claim_kind:: analyst_assessment
      evidence:: E9, E10, E11
- ## Glossary
  collapsed:: true
    - Streaming video understanding: A setting where a model answers or acts while video arrives, using only the observed prefix rather than the full future video.
    - Causal observation protocol: Evaluation rule that a query at time t may use only video frames observed up to t, not future frames or side information.
    - Video-language model: A multimodal model that takes video or image frames plus text and produces text answers.
    - Recent-frame window: A fixed-size set of the latest frames kept for the next query; as time advances, old frames leave the window.
    - Working context: The bounded input representation a streaming system constructs from the observed history before answering a query.
    - KV cache: Saved transformer attention keys and values from prior tokens or frames; useful for reuse, but large caches can consume memory and attention budget.
    - Real-Time Visual Perception: OVO-Bench category focused on understanding the current scene, including text, actions, attributes, spatial relations, future prediction, and object recognition.
    - Backward Tracing: OVO-Bench category labeled as backward-looking; the paper argues EPM and ASI better capture episodic recall, while HLD mainly measures hallucination robustness.
    - Visual-RAG: Retrieves visually similar historical chunks and appends them to the current input before answer generation.
    - Time to first token: Latency metric measuring how long the system takes before emitting the first generated token.
    - Perception-memory trade-off: The paper's framing that added historical context may improve recall-oriented measures while lowering current-scene perception.
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/metadata | Metadata and abstract | high
      locator:: title block and abstract
      quote:: A Simple Baseline for Streaming Video Understanding. Yujiao Shen, Shulin Tian, Jingkang Yang, Ziwei Liu. S-Lab, Nanyang Technological University. Date: April 1, 2026. Codebase: https://github.com/EvolvingLMMs-Lab/SimpleStream
    - **E2:** gap/paper_statement | 1 Introduction | high
      locator:: opening paragraphs
      quote:: Streaming video understanding increasingly relies on complex memory-centric designs to handle long streams under causal constraints. Across these methods, the complexity typically lies in how past context is managed, for example through explicit memory banks, retrieval over prior observations, or compression of visual and latent representations under bounded budgets.
    - **E3:** method/implementation_detail | 3.2 SimpleStream: A Simple Recent-N-Frames Baseline | high
      locator:: method definition and equation
      quote:: Given a question q_t at time t, we feed the base VLM only the most recent N frames and the text query. By construction, SIMPLESTREAM omits the additional memory mechanisms used in prior streaming systems. Frames outside the sliding window are discarded.
    - **E4:** experiment_setup/paper_statement | 4.1 Experimental Setup | high
      locator:: benchmarks, compared models, and SimpleStream setup
      quote:: OVO-Bench contains 1,640 questions over 12 tasks spanning memory recall, real-time perception, and future-oriented reasoning. For StreamingBench, we use the official real-time visual understanding subset, which contains 2,500 questions across ten task types.
    - **E5:** result/experiment_result | 4.2 Benchmark Performance | medium
      locator:: Table 1 and paragraph after Table 2
      quote:: On OVO-Bench, the best SIMPLESTREAM configuration (Qwen3-VL, 4 frames) reaches 67.7%, exceeding the strongest published streaming method, HERMES, by 8.5 pp (59.2%). The same pattern appears on StreamingBench. SIMPLESTREAM with Qwen3-VL and 4 frames reaches 80.59%, surpassing HERMES (79.44%).
    - **E6:** result/experiment_result | 4.2 Benchmark Performance | medium
      locator:: Table 1 discussion
      quote:: On Backward Tracing, SIMPLESTREAM remains competitive: the 8-frame variant reaches 54.9%, compared with 52.0% for StreamForest and 49.4% for HERMES.
    - **E7:** ablation/ablation | 4.3 Model Scale Effects | medium
      locator:: Table 2 discussion
      quote:: Across both backbone families, moving from 2 to 4 frames usually improves average accuracy. For many small and mid-sized checkpoints, performance then plateaus or slightly declines as the window expands further. Larger windows can become more favorable for some higher-capacity checkpoints.
    - **E8:** ablation/ablation | 5.1 Longer Context Is Not Always Better | medium
      locator:: Figure 4 recency-window ablation
      quote:: Moving from 2 to 4 frames improves both Overall accuracy (66.4 -> 67.7) and Real-Time accuracy (79.3 -> 81.4). Beyond this point, however, performance does not keep rising: at 8 frames, Overall falls to 67.4 and Real-Time accuracy to 79.9.
    - **E9:** ablation/ablation | 5.1 Longer Context Is Not Always Better | medium
      locator:: Table 4 Visual-RAG ablation
      quote:: Visual-RAG improves some Backward tracks, especially EPM (+7.1) and ASI (+6.1), which confirms that retrieval can recover useful historical evidence, but those gains coincide with clear degradations on Real-Time tracks, including OJR (-9.2), OCR (-8.1), and ACR (-7.3).
    - **E10:** result/experiment_result | 5.2 Perception-Memory Trade-off | medium
      locator:: Figure 6 discussion
      quote:: Every evaluated external baseline falls below SIMPLESTREAM on Delta P. Among published streaming systems, StreamForest shows the clearest memory-side gain (Delta M = +8.9), but it pays a much larger perception penalty (Delta P = -13.8). HERMES also gains on memory (Delta M = +2.4), yet still incurs a substantial perception cost (Delta P = -6.0).
    - **E11:** limitation/paper_statement | 5.3 Benchmark Limitations | high
      locator:: HLD and macro-average paragraphs
      quote:: Placing HLD under Backward Tracing therefore conflates two distinct abilities: memory recall and hallucination robustness. OVO-Bench reports a macro-average over 12 tracks, but these tracks are not balanced across capability types.
    - **E12:** result/profiling | 4.4 Efficiency Observations | medium
      locator:: Table 3 and Figure 3 discussion
      quote:: SIMPLESTREAM-4f remains latency-competitive despite using no explicit memory module. HERMES is the only method that is consistently faster. Figure 3 complements the latency comparison by showing that SIMPLESTREAM-4f also has the lowest peak GPU memory usage.
    - **E13:** limitation/limitation | 8 Limitations | high
      locator:: Dependence on strong backbone families
      quote:: SIMPLESTREAM is evaluated on top of strong modern VLM backbones, specifically Qwen2.5-VL and Qwen3-VL. As a result, our conclusions are coupled to the capabilities of this backbone family.
    - **E14:** limitation/limitation | 8 Limitations | high
      locator:: Scope as a strong-baseline paper
      quote:: This paper is deliberately positioned as a strong baseline study rather than a proposal of a new streaming video understanding architecture. SIMPLESTREAM does not introduce a new memory-centric architecture, a new long-term memory mechanism, or a new retrieval/compression design.
    - **E15:** prior_work/paper_statement | 3.1 A Landscape of Streaming Video Understanding Methods | high
      locator:: method taxonomy paragraph
      quote:: External-memory systems maintain structured history online. Retrieval-based methods retain past representations so they can be selected at query time. Compression targets the KV and attention budget directly. Latent-memory approaches learn a constant-length state for the prefix.
