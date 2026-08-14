- **Title:** A Simple Baseline for Streaming Video Understanding
  **标题:** 面向流式视频理解的一个简单基线
- **Summary:** SimpleStream shows that a fixed recent-frame window on a strong video-language model is a hard baseline for streaming video understanding, so memory-heavy systems must prove gains on disaggregated perception and memory slices.
  **一句话总结:** SimpleStream 表明，在一个强大的视频语言模型上采用固定大小的近期帧窗口，就构成了流式视频理解的一个难以超越的基线；因此，那些依赖大量记忆机制的系统必须在拆分开的感知与记忆两个维度上分别证明自己确有提升。
- **Paper Type:** benchmark
  **论文类型:** 基准评测
- **Venue:** arXiv preprint 2026
  **发表:** arXiv 预印本 2026
- **Authors:** Yujiao Shen, Shulin Tian, Jingkang Yang, Ziwei Liu; S-Lab, Nanyang Technological University
  **作者:** Yujiao Shen、Shulin Tian、Jingkang Yang、Ziwei Liu；S-Lab，南洋理工大学（Nanyang Technological University）
- **Keywords:** streaming video understanding, video-language models, recent-frame baseline, context management, perception-memory trade-off, OVO-Bench, StreamingBench
  **关键词:** 流式视频理解、视频语言模型、近期帧基线、上下文管理、感知与记忆的权衡、OVO-Bench、StreamingBench
- ## Orientation
    - **Background:** Streaming video understanding is about answering questions while a video is still arriving. The model may use what it has already seen, but not future frames.
      **背景:** 流式视频理解（streaming video understanding）指的是：在一段视频还在持续传入的过程中回答关于它的问题。模型可以使用它已经看过的画面，但不能使用未来的画面。
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A live assistant must decide what visual evidence to keep so it can answer now without rereading the whole video.
      **通俗问题:** 一个实时助手必须决定要保留哪些视觉证据，这样它才能当下就作答，而不必把整段视频重新看一遍。
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** Old events can matter, but too much old material can crowd out the clear view of the current scene.
      **为何困难:** 旧的事件有时很重要，但保留太多旧材料反而会挤占对当前场景的清晰观察。
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Keep the latest clear frames first, and treat added history as something that must prove it helps.
      **一句话核心思路:** 优先保留最近的、清晰的画面，并把额外加入的历史信息当作「需要自证其有用」的东西来看待。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as an evaluation-baseline paper for streaming video understanding, where a model must answer from the video seen so far; it challenges the assumption that better online performance mainly comes from more elaborate memory modules.
      **阅读价值:** 把这篇论文当作流式视频理解的评测基线论文来读：在这种设定下，模型必须仅凭目前已看到的视频来作答。它挑战了一种常见假设，即在线场景下更好的表现主要来自更复杂精巧的记忆模块。
      claim_kind:: analyst_assessment
      evidence:: E2, E5
    - **One-Sentence Contribution:** SimpleStream improves the evaluation standard for online video question answering by showing that keeping only the latest frames and feeding them directly to a video-language model (VLM, a model that reads visual frames and text together) is already a strong baseline.
      **一句话贡献:** SimpleStream 提升了在线视频问答的评测标准：它表明，只保留最新的若干帧并直接送入视频语言模型（VLM，一种同时读取视觉帧与文本的模型），就已经是一个很强的基线。
      evidence:: E3, E5
    - **Mental Model:** Picture a live camera assistant that answers by looking at the last few clear snapshots on its desk, instead of carrying a thick notebook whose older pages can distract it from what is happening now.
      **记忆模型:** 可以设想一个实时摄像头助手：它作答时只看桌上最近的几张清晰快照，而不是抱着一本厚厚的笔记本——本子里较早的那些页面反而可能干扰它对当下正在发生之事的判断。
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is that the same small-window rule is competitive on OVO-Bench and StreamingBench while staying efficient, and the ablations show why added history is not a free win.
      **最佳证据:** 最有力的证据在于，同样的小窗口规则在 OVO-Bench 和 StreamingBench 上都很有竞争力，同时保持了高效率；而消融实验则说明了为什么增加历史信息并不是白拿的好处。
      evidence:: E5, E8, E9, E12
        - Supports C1: Qwen3-VL-8B plus the latest four frames; HERMES as strongest published streaming baseline; OVO-Bench average accuracy; 67.7% versus 59.2%, a +8.5 point margin; supports the recent-window baseline as competitive.
          支持结论 C1：使用 Qwen3-VL-8B 加上最近的四帧画面；以 HERMES 作为已发表的最强流式基线（streaming baseline）；在 OVO-Bench 上的平均准确率为 67.7%，对比 59.2%，领先 +8.5 个百分点；这一结果支持「保留最近画面窗口」这一基线具有竞争力。
          evidence:: E5
        - Supports C1: Qwen3-VL-8B plus the latest four frames; HERMES on StreamingBench real-time visual understanding; accuracy; 80.59% versus 79.44%; supports transfer beyond one benchmark.
          支持结论 C1：使用 Qwen3-VL-8B 加上最近的四帧画面；在 StreamingBench 的实时视觉理解任务上对比 HERMES；准确率为 80.59%，对比 79.44%；这一结果支持该方法能够迁移到不止一个基准测试上。
          evidence:: E5
        - Supports C2: controlled recent-window ablation; same prompt and decoding; overall and real-time accuracy; four frames beats eight and sixteen frames; supports non-monotonic context benefits.
          支持结论 C2：进行受控的「最近画面窗口」消融实验；使用相同的提示词和解码设置；在整体准确率和实时准确率上，四帧的效果都超过八帧和十六帧；这一结果支持「上下文带来的收益并非单调递增」这一观点。
          evidence:: E8
        - Supports C3: Visual-RAG with retrieved historical chunks; matched recent-window baseline; memory tracks improve but real-time tracks and overall accuracy fall; supports a perception-memory trade-off.
          支持结论 C3：使用 Visual-RAG，即检索历史片段并加入输入；与匹配的「最近画面窗口」基线对比；结果是记忆相关的任务有所提升，但实时类任务和整体准确率都下降；这一结果支持「感知与记忆之间存在权衡」这一观点。
          evidence:: E9
    - **Main Caveat:** The result is a strong-baseline result, not a long-horizon memory solution: the evidence is tied to Qwen2.5-VL and Qwen3-VL backbones and to benchmarks that reward recent-scene perception heavily.
      **主要边界:** 这一结果是一个「强基线」结果，而不是一个针对长时程记忆的解决方案：相关证据都绑定在 Qwen2.5-VL 和 Qwen3-VL 这两类骨干模型上，也绑定在那些高度奖励「近期场景感知」的基准测试上。
      claim_kind:: analyst_assessment
      evidence:: E11, E13, E14
- ## Argument Map
    - **Problem and Stakes:** The paper frames streaming video question answering as causal, budgeted context management: at each query, the system must build a small working context from the observed video prefix. The stake is methodological: if a simple recent-window rule already wins, memory-heavy streaming systems need stronger evidence than architectural complexity.
      **问题与重要性:** 这篇论文把流式视频问答刻画为一种「因果的、有预算约束的上下文管理」问题：在每一次查询时，系统必须从已观察到的视频前缀（prefix）中构建出一小段工作上下文（working context）。这里的关键意义在于方法论层面：如果一个简单的「保留最近画面窗口」规则就已经能胜出，那么那些重度依赖记忆机制的流式系统，就需要拿出比「架构更复杂」更强的证据来证明自己。
      evidence:: E2, E3
    - **Prior Gap:** Prior streaming methods often differ in how they preserve history, including memory banks, retrieval over old representations, key-value cache (KV cache, saved attention state used by transformer models) compression, and latent states, but the simple recent-context baseline was not treated as the primary reference point.
      **已有方法缺口:** 以往的流式处理方法在如何保留历史信息上各有不同，包括记忆库、对旧表示的检索、键值缓存（KV cache，指 transformer 模型保存的注意力状态）压缩，以及潜在状态等，但它们都没有把最简单的「近期上下文」基线当作主要的对照参照。
      evidence:: E2, E15
    - **Key Insight:** A strong backbone with clear, uncompressed recent visual evidence can be more valuable than a larger but noisier historical context. The paper's insight is not that memory is useless, but that recent-scene perception is strong enough to invalidate weak memory-module comparisons.
      **关键洞见:** 一个强大的主干网络，配上清晰、未经压缩的近期视觉证据，可能比更大但更嘈杂的历史上下文更有价值。这篇论文的洞见并不是说记忆没有用，而是说对近期场景的感知已经足够强，足以让那些依赖弱记忆模块的对比失去意义。
      evidence:: E3, E5, E10
    - **Claims:** The paper's logical claims are baseline strength, non-monotonic context value, a perception-memory trade-off, and the need for cleaner reporting.
      **核心主张:** 这篇论文提出的逻辑主张包括：基线的强度、上下文价值的非单调性、感知与记忆之间的权衡，以及更清晰的报告方式的必要性。
      evidence:: E5, E8, E10, E11
        - C1: A recent-N-frame input policy with an off-the-shelf VLM can match or surpass published streaming video systems under the paper's shared benchmark protocols.
          C1：在这篇论文采用的统一基准测试规程下，只输入最近 N 帧、再配一个现成的视频语言模型（VLM），就能达到甚至超过已发表的流式视频系统。
          evidence:: E3, E5, E6
        - C2: More visual context is not uniformly better; the best window depends on backbone family, scale, and benchmark slice.
          C2：视觉上下文并非越多越好；最佳的窗口大小取决于主干网络的类型、规模，以及所测试的基准子集。
          evidence:: E7, E8
        - C3: Historical memory or retrieval can improve recall-oriented slices, but often reduces real-time perception of the current scene.
          C3：历史记忆或检索能够提升偏向回忆的测试子集的表现，但往往会削弱对当前场景的实时感知。
          evidence:: E9, E10
        - C4: Future streaming evaluations should include strong recency baselines and report perception, memory recall, hallucination robustness, and efficiency separately.
          C4：未来的流式评测应当纳入强的近期基线，并分别报告感知能力、记忆回忆、抗幻觉鲁棒性和效率这几项指标。
          evidence:: E11, E14
- ## Mechanism and Design
    - **Core Mechanism:** SimpleStream uses a sliding window (a fixed-size set that moves forward with time): for a query at time t and window size N, it sends only frames from t-N+1 through t plus the text query to the base VLM. Frames outside the window are discarded, so per-query computation and memory are bounded by N rather than stream length.
      **核心机制:** SimpleStream 使用一个滑动窗口（一个大小固定、随时间向前移动的集合）：对于时刻 t 的一次查询，在窗口大小为 N 时，它只把从 t-N+1 到 t 这些帧连同文本查询一起发送给基础 VLM。窗口之外的帧被丢弃，因此每次查询的计算量和内存占用由 N 决定，而不是由整段视频流的长度决定。
      evidence:: E3
    - **Data / Control Flow:** At inference time, the video stream is sampled, the visible prefix is clipped to the latest N frames, the query is appended, and the unchanged VLM answers from that bounded input. In the main experiments, SimpleStream samples the visible stream at one frame per second and evaluates N in the reported frame caps.
      **数据/控制流:** 在推理时，系统会对视频流采样，把已见的前缀裁剪到最近 N 帧，接上查询文本，然后由保持不变的 VLM 基于这段有界的输入给出回答。在主要实验中，SimpleStream 以每秒一帧的频率对可见视频流采样，并在论文报告的帧数上限范围内评估 N。
      evidence:: E3, E4
    - **Design Decisions:** The design deliberately removes extra mechanisms so the baseline isolates what recent visual evidence and backbone capability already provide. Its main trade-off is sharp: it protects present evidence and efficiency, but gives up direct access to events outside the window.
      **设计决策:** 这一设计有意去掉了所有额外机制，从而让基线单独凸显出近期视觉证据和主干网络能力本身已经能提供什么。它的核心权衡很鲜明：它保住了当前证据和效率，但放弃了直接获取窗口之外事件的能力。
      evidence:: E3, E14
        - Need: avoid confounding a baseline with new training or memory modules; choice: no memory bank, retrieval, vision compression, KV-cache compression, or fine-tuning; trade-off: weaker explicit long-range recall.
          需求：避免让基线因引入新的训练或记忆模块而产生混淆；选择：不使用记忆库、检索、视觉压缩、键值缓存（KV cache）压缩或微调；代价：显式的长程回忆能力较弱。
          evidence:: E3, E14
        - Need: bound streaming cost; choice: discard frames outside the recent window; closest alternative: expand the working context with external memory, retrieval, compression, or latent state; trade-off: simpler cost model but no persistent history.
          需求：限制流式处理的开销；选择：丢弃近期窗口（recent-frame window，即为下一次查询保留的固定数量的最新帧）之外的帧；最接近的替代方案：用外部记忆、检索、压缩或潜在状态来扩展工作上下文（working context）；代价：成本模型更简单，但不保留持久的历史记录。
          evidence:: E3, E15
        - Need: compare against prior systems fairly; choice: use official protocols, reported frame budgets or rates, and SimpleStream caps of two, four, or eight recent frames at one frame per second; trade-off: protocol matching still leaves model-specific pipelines and prompts.
          需求：与已有系统进行公平比较；选择：采用官方评测协议、已报告的帧预算或帧率，以及 SimpleStream 在每秒一帧下保留最近两帧、四帧或八帧的上限设置；代价：即便对齐了协议，各模型专属的处理流程和提示词仍然存在差异。
          evidence:: E4
    - **Implementation Surface:** The implementation surface is an inference-time input policy around open-source Qwen2.5-VL and Qwen3-VL backbones, with a project page and codebase reported. There is no new architecture to port; reproducing the result mainly requires matching the sampler, frame window, prompt path, benchmark scorer, and backbone checkpoint.
      **实现边界:** 实现层面上，本方法是围绕开源的 Qwen2.5-VL 与 Qwen3-VL 骨干网络设计的一套推理阶段输入策略，并附有项目主页和公开代码库。它没有需要移植的新架构；复现结果主要需要对齐采样器、帧窗口、提示词路径、基准评分器以及骨干网络的检查点。
      evidence:: E1, E3, E4
- ## Evaluation and Evidence
    - **Setup:** The main evaluation uses OVO-Bench (an online-video benchmark with memory, real-time perception, and future-oriented tasks) and StreamingBench (a streaming real-time understanding benchmark), comparing six offline video LLMs and seven streaming video LLMs. SimpleStream is instantiated with Qwen2.5-VL and Qwen3-VL backbones and recent windows of two, four, or eight frames for the main comparison.
      **实验设置:** 主要评测使用 OVO-Bench（一个在线视频基准，包含记忆、实时感知和面向未来的任务）和 StreamingBench（一个流式实时理解基准），对比了六个离线视频语言模型（video LLM）和七个流式视频语言模型。SimpleStream 在主对比实验中以 Qwen2.5-VL 和 Qwen3-VL 为骨干网络，分别搭配保留最近两帧、四帧或八帧的近期窗口。
      evidence:: E4
    - **Claim-Evidence Matrix:** The evidence supports the baseline-strength claim most directly, supports the context-length and perception-memory claims through ablations, and supports the benchmark-reporting claim through a conceptual audit of benchmark categories.
      **主张-证据矩阵:** 证据最直接地支持了「基线足够强」这一论断；通过消融实验支持了关于上下文长度和感知—记忆的论断；并通过对基准类别的概念性审查支持了关于基准结果如何呈现的论断。
      claim_kind:: analyst_assessment
      evidence:: E5, E8, E9, E11
        - C1: Main table comparisons show SimpleStream ahead of HERMES on OVO-Bench average and StreamingBench accuracy, with backward recall still competitive rather than dominant.
          C1：主对比表显示，SimpleStream 在 OVO-Bench 平均分和 StreamingBench 准确率上领先于 HERMES，但在反向回忆（backward recall）上仍属于有竞争力而非占据主导。
          evidence:: E5, E6
        - C2: Window and scale ablations show gains from two to four frames, then plateaus or declines for many settings, with larger windows useful only for some higher-capacity checkpoints.
          C2：关于窗口大小和模型规模的消融实验显示，帧数从两帧增加到四帧时性能提升，之后在许多设置下趋于平稳或下降；更大的窗口只对部分容量更高的检查点有用。
          evidence:: E7, E8
        - C3 and C4: Visual-RAG and cross-method trade-off analysis show memory gains paired with perception losses, while HLD and macro-average analysis explain why aggregated benchmark scores can hide that split.
          C3 与 C4：Visual-RAG 和跨方法权衡分析表明，记忆能力的提升伴随着感知能力的下降；而对 HLD 和宏平均（macro-average）的分析则解释了为什么聚合后的基准总分会掩盖这种此消彼长的分化。
          evidence:: E9, E10, E11
    - **Headline Results:** The headline result is that Qwen3-VL with four recent frames reaches 67.7% on OVO-Bench and 80.59% on StreamingBench, beating the paper's strongest published streaming comparison while using no memory module. Efficiency is also favorable: SimpleStream-4f has the lowest reported peak GPU memory and is second-fastest in time to first token among the compared streaming methods.
      **关键结果:** 核心结果是：搭配最近四帧的 Qwen3-VL 在 OVO-Bench 上达到 67.7%、在 StreamingBench 上达到 80.59%，在不使用任何记忆模块的情况下超越了论文中最强的已发表流式对比方法。效率表现同样占优：SimpleStream-4f 在所有对比的流式方法中报告的峰值 GPU 显存最低，首字延迟（time to first token，指系统输出第一个生成标记前所需的时间）位列第二快。
      evidence:: E5, E12
    - **Ablations and Sensitivity:** Ablations show that context length has a sweet spot rather than a simple scaling law: four frames is often better than two, but eight or sixteen frames can degrade real-time accuracy, and model scale changes the optimum without making it monotonic. Visual-RAG (retrieval-augmented generation over visual chunks, here adding retrieved past chunks to the recent frames) helps selected memory tracks but lowers overall accuracy.
      **消融与敏感性:** 消融实验表明，上下文长度存在一个「最佳点」，而不是简单的规模递增规律：四帧往往比两帧更好，但八帧或十六帧反而会降低实时准确率；模型规模的变化会改变这个最佳点，但并不使其单调变化。视觉检索增强生成（Visual-RAG，即在视觉片段上做检索增强生成，这里指把检索到的过去片段加到最近的帧上）能提升某些记忆类任务的表现，却降低了整体准确率。
      evidence:: E7, E8, E9
    - **Reproducibility Gaps:** Reported reuse aids include a codebase, project page, benchmark names, scorer protocol, backbones, frame rates, and frame caps; statistical uncertainty, repeat counts, and detailed hardware for all runs are not reported in the supplied text. Because many headline deltas are benchmark accuracies without variance, their evidence strength is medium rather than high.
      **可复现性缺口:** 论文提供的可复用材料包括一份代码库、项目主页、基准测试名称、评分协议、骨干网络（backbone）、帧率以及帧数上限；但所提供的文本没有报告统计不确定性、重复运行次数，也没有给出所有实验的详细硬件信息。由于许多重点结论只是基准准确率而没有方差，它们的证据强度属于中等，而非高。
      claim_kind:: analyst_assessment
      evidence:: E1, E4, E5, E12
- ## Technical Judgment
    - **What Holds Up:** The baseline is technically hard to dismiss because it changes only the input policy, controls the context window, and reports against named offline and streaming baselines on public benchmarks. The most durable lesson is the negative control: a memory module should not be credited unless it beats a matched recent-window baseline on the capability slice it claims to improve.
      **站得住的结论:** 这个基线方法在技术上很难被否定，因为它只改变了输入策略，控制了上下文窗口，并在公开基准上与具名的离线基线和流式基线进行了对比。最持久的启示是这一「反向对照」：一个记忆模块只有在它所声称要改进的能力切片上，击败了一个条件相当的最近窗口基线，才应当被认可其价值。
      claim_kind:: analyst_assessment
      evidence:: E3, E4, E5, E8
    - **Where It May Fail:** The result may weaken on backbones with poorer short-range perception, on tasks whose answer truly depends on events outside the recent window, or on benchmarks that balance memory recall more heavily than present perception. It also does not establish a mechanism for long-horizon video memory; it establishes a demanding baseline and an evaluation critique.
      **可能失效之处:** 在短程感知能力较弱的骨干网络上、在答案确实依赖于最近窗口之外事件的任务上，或者在更看重记忆召回而非当前感知的基准上，这一结果可能会减弱。它也没有为长时程视频记忆确立一种机制；它确立的是一个高标准的基线和一份评估方法的批判。
      claim_kind:: analyst_assessment
      evidence:: E11, E13, E14
    - **Relation to Other Work:** Compared with StreamForest-style external memory, ReKV-style retrieval, HERMES-style KV-cache compression, and Dispider-style latent memory, SimpleStream removes the historical-state mechanism and asks whether that mechanism adds measurable value. The paper therefore functions as a control condition for memory-centric streaming work, not as a replacement for all memory research.
      **与已有工作的关系:** 与 StreamForest 式的外部记忆、ReKV 式的检索、HERMES 式的键值缓存（KV cache）压缩以及 Dispider 式的隐式记忆相比，SimpleStream 去掉了历史状态机制，并追问这一机制是否带来了可测量的价值。因此，这篇论文的作用是充当以记忆为中心的流式工作的对照条件，而不是要取代所有的记忆研究。
      claim_kind:: analyst_assessment
      evidence:: E15, E14
    - **Transferable Lesson:** Use a recent-first, history-on-demand design pattern: preserve a clean current input by default, add historical state only when the task demands it, and measure both the recall gain and the perception cost. This transfers beyond video to any online system where a larger context can distract the model from high-quality fresh evidence.
      **可迁移启发:** 采用一种「最近优先、按需调取历史」的设计模式：默认保持一份干净的当前输入，只在任务需要时才加入历史状态，并同时衡量召回上的收益与感知上的代价。这一经验不仅适用于视频，也适用于任何在线系统——只要在这些系统里，更大的上下文可能会分散模型对高质量新证据的注意力。
      claim_kind:: analyst_assessment
      evidence:: E9, E10, E11
- ## Glossary
  collapsed:: true
    - Streaming video understanding: A setting where a model answers or acts while video arrives, using only the observed prefix rather than the full future video.
      流式视频理解（Streaming video understanding）：一种任务设定，模型在视频不断到达的过程中作答或行动，只使用已观察到的前缀部分，而不是完整的未来视频。
    - Causal observation protocol: Evaluation rule that a query at time t may use only video frames observed up to t, not future frames or side information.
      因果观察协议（Causal observation protocol）：一条评估规则，即在时刻 t 提出的查询只能使用截至 t 已观察到的视频帧，不能使用未来的帧或旁路信息。
    - Video-language model: A multimodal model that takes video or image frames plus text and produces text answers.
      视频语言模型（Video-language model）：一种多模态模型，接收视频或图像帧加上文本，并生成文本答案。
    - Recent-frame window: A fixed-size set of the latest frames kept for the next query; as time advances, old frames leave the window.
      最近帧窗口（Recent-frame window）：为下一次查询而保留的一组固定大小的最新帧；随着时间推进，旧的帧会离开窗口。
    - Working context: The bounded input representation a streaming system constructs from the observed history before answering a query.
      工作上下文（working context）：流式系统在回答查询之前，从已观察到的历史中构建出的有界输入表示。
    - KV cache: Saved transformer attention keys and values from prior tokens or frames; useful for reuse, but large caches can consume memory and attention budget.
      键值缓存（KV cache）：从先前的词元（token）或视频帧中保存下来的 transformer 注意力键与值；便于复用，但过大的缓存会占用内存并消耗注意力预算。
    - Real-Time Visual Perception: OVO-Bench category focused on understanding the current scene, including text, actions, attributes, spatial relations, future prediction, and object recognition.
      实时视觉感知（Real-Time Visual Perception）：OVO-Bench 中的一个类别，聚焦于理解当前场景，包括文本、动作、属性、空间关系、未来预测和物体识别。
    - Backward Tracing: OVO-Bench category labeled as backward-looking; the paper argues EPM and ASI better capture episodic recall, while HLD mainly measures hallucination robustness.
      回溯追踪（Backward Tracing）：OVO-Bench 中被标注为向后回顾的类别；论文认为 EPM 和 ASI 更能刻画情节记忆回溯能力，而 HLD 主要衡量对幻觉的鲁棒性。
    - Visual-RAG: Retrieves visually similar historical chunks and appends them to the current input before answer generation.
      视觉检索增强生成（Visual-RAG）：检索出视觉上相似的历史片段，并在生成答案之前将其附加到当前输入中。
    - Time to first token: Latency metric measuring how long the system takes before emitting the first generated token.
      首词元时间（time to first token）：一种延迟指标，衡量系统在输出第一个生成词元之前所耗费的时长。
    - Perception-memory trade-off: The paper's framing that added historical context may improve recall-oriented measures while lowering current-scene perception.
      感知与记忆权衡（perception-memory trade-off）：论文提出的一个观点，即加入更多历史上下文可能会提升与记忆回溯相关的指标，但同时会降低对当前场景的感知能力。
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
