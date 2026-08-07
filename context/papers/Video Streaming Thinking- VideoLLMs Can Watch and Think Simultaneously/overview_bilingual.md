- **Title:** Video Streaming Thinking: VideoLLMs Can Watch and Think Simultaneously
  **标题:** 视频流式思考：视频大语言模型可以边看边想
- **Summary:** Video Streaming Thinking turns playback time into proactive clip-level reasoning, letting online video language models keep a compact memory and answer later questions with low latency.
  **一句话总结:** 视频流式思考把视频的播放时段转化为主动的、片段级别的推理过程，让在线视频语言模型保持一份紧凑的记忆，并以较低延迟回答之后提出的问题。
- **Paper Type:** system
  **论文类型:** 系统
- **Venue:** arXiv preprint 2026
  **发表:** arXiv 预印本 2026
- **Authors:** Yiran Guan*, Liang Yin*, Dingkang Liang, Yuliang Liu, Xiang Bai (Huazhong University of Science and Technology); Jianzhong Ju, Zhenbo Luo, Jian Luan (MiLM Plus, Xiaomi Inc.)
  **作者:** Yiran Guan*、Liang Yin*、Dingkang Liang、Yuliang Liu、Xiang Bai（华中科技大学）；Jianzhong Ju、Zhenbo Luo、Jian Luan（小米公司 MiLM Plus）
- **Keywords:** streaming video understanding, VideoLLM, chain-of-thought, online reasoning, knowledge graph data synthesis, reinforcement learning
  **关键词:** 流式视频理解、视频大语言模型（VideoLLM）、思维链、在线推理、基于知识图谱的数据合成、强化学习
- ## Orientation
    - **Background:** Video Large Language Models (VideoLLMs) answer questions about video. In live settings, the model sees the video as it arrives, so it must remember earlier events without looking ahead.
      **背景:** 背景：视频大语言模型（Video Large Language Model，VideoLLM）用来回答关于视频的问题。在实时场景中，模型是随着视频到达而逐帧看到的，因此它必须记住此前发生的事件，而不能提前看到后面的内容。
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A viewer may ask a question late, but the clue may have appeared much earlier. The model needs to keep useful clues ready while still responding quickly.
      **通俗问题:** 用简单的话说明问题：观看者可能很晚才提出问题，但相关线索可能早在很久之前就出现过。模型需要一边随时保留有用的线索，一边又能快速作答。
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** Long videos contain too many frames to keep raw details forever, and careful reasoning after the question can make the user wait.
      **为何困难:** 为什么困难：长视频包含的帧太多，无法永远保留全部原始细节；而在收到问题之后再进行细致推理，又会让用户等待。
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Make the model write useful running thoughts while it watches, then answer from those thoughts plus the latest scene.
      **一句话核心思路:** 一句话说核心思路：让模型在观看视频的同时写下有用的「过程思考」，然后依据这些思考加上最新画面来作答。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a streaming video understanding paper about the missing reasoning layer between visual-token memory systems and slow after-the-query chain-of-thought reasoning.
      **阅读价值:** 把这篇论文当作一项流式视频理解工作来读：它填补了「视觉词元记忆系统」与「在用户提问之后才启动的、缓慢的思维链推理」之间缺失的那一层推理。
      claim_kind:: analyst_assessment
      evidence:: E2, E3
    - **One-Sentence Contribution:** Video Streaming Thinking (VST) improves online video question answering (QA) by generating compact thoughts while the video is still arriving, so the final answer can reuse already-processed evidence instead of starting its reasoning after the user asks.
      **一句话贡献:** 视频流式思考（Video Streaming Thinking，VST）改进了在线视频问答（QA）：它在视频还在陆续到达时就生成紧凑的思考，因此最终答案可以复用已经处理过的证据，而不必等到用户提问后才开始推理。
      evidence:: E3, E4
    - **Mental Model:** Picture a live note-taker watching a video: every few moments it writes a short running note, keeps the latest scene in sight, and answers from those notes when a question arrives.
      **记忆模型:** 可以想象一位实时记笔记的人在看视频：每隔一小段时间就写下一条简短的即时笔记，同时始终盯着最新出现的画面，等问题来了就依据这些笔记来作答。
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest support is the combination of online benchmark gains, low query-time latency, and ablations showing that VST data and training stages matter.
      **最佳证据:** 最有力的支撑来自三点的结合：在线基准测试上的性能提升、较低的提问时延迟，以及消融实验表明 VST 数据和训练阶段确实起作用。
      evidence:: E11, E13, E15
        - Supports C3: VST-7B on online benchmarks; Streamforest and Streamo as closest open-source streaming baselines; overall accuracy; +2.2 points on StreamingBench and +1.4 points on OVO-Bench; supported but without reported variance.
          支持结论 C3：VST-7B 在在线基准测试上的表现；以 Streamforest 和 Streamo 作为最接近的开源流式基线；比较的是整体准确率；在 StreamingBench 上高出 2.2 分，在 OVO-Bench 上高出 1.4 分；该结论得到支持，但未报告方差。
          evidence:: E11
        - Supports C1: VST-7B on VideoHolmes latency measurement; Video-R1 with chain-of-thought as closest reasoning baseline; query-answer latency; 0.56s versus 8.80s, about 15.7x faster; supported for query-time latency, not total token cost.
          支持结论 C1：VST-7B 在 VideoHolmes 上的延迟测量；以带思维链（chain-of-thought）的 Video-R1 作为最接近的推理基线；比较的是查询—回答延迟（query-answer latency，即从用户提交问题到模型作答的时间）；0.56 秒对 8.80 秒，约快 15.7 倍；该结论在查询时延迟这一点上得到支持，但不涵盖总的 token 成本。
          evidence:: E15
        - Supports C3: VST-SFT plus VST-RL training schedule; Qwen2.5-VL-7B base as baseline; OVO-Bench and VideoMME accuracy; 59.3 versus 50.5 on OVO-Bench and 64.9 versus 62.9 on VideoMME; supported by ablation, without repeat counts.
          支持结论 C3：VST-SFT 加 VST-RL 的训练流程；以 Qwen2.5-VL-7B 基础模型作为基线；比较的是在 OVO-Bench 和 VideoMME 上的准确率；在 OVO-Bench 上为 59.3 对 50.5，在 VideoMME 上为 64.9 对 62.9；该结论由消融实验支持，但未报告重复次数。
          evidence:: E13
    - **Main Caveat:** The latency story depends on having playback time available for pre-query thinking; the paper also acknowledges extra generated tokens and mostly text-guided memory, so VST is not a free replacement for efficient visual memory.
      **主要边界:** 主要注意事项：延迟优势依赖于在提问之前有可用的播放时间来进行「预先思考」；论文也承认这会带来额外生成的 token，而且记忆内容大多以文本为主，因此 VST 并不是高效视觉记忆的免费替代方案。
      claim_kind:: analyst_assessment
      evidence:: E15, E17
- ## Argument Map
    - **Problem and Stakes:** Online video understanding must obey temporal causality, meaning the model cannot use future frames, while still meeting real-time query-answer latency and finite context-window limits, where a context window is the bounded amount of tokens a model can attend to at once.
      **问题与重要性:** 问题与利害关系：在线视频理解必须遵守时间因果性，也就是说模型不能使用未来的帧，同时还要满足实时的查询—回答延迟（query-answer latency）以及有限的上下文窗口（context window）限制——上下文窗口指模型一次能同时关注的 token 数量上限。
      evidence:: E2
    - **Prior Gap:** The paper positions prior online VideoLLMs as mostly managing visual memory through compression or key-value cache retrieval, where a key-value cache stores earlier attention state for reuse, while offline chain-of-thought (CoT), or step-by-step reasoning text, improves reasoning but shifts latency after the user query.
      **已有方法缺口:** 此前工作的不足：论文认为，以往的在线视频大语言模型大多通过压缩或键值缓存（key-value cache）检索来管理视觉记忆，其中键值缓存存储此前的注意力状态以便复用；而离线的思维链（chain-of-thought，CoT，即逐步推理的文本）虽然能改善推理，却把延迟推迟到了用户提问之后。
      evidence:: E2, E5
    - **Key Insight:** The key insight is to move explicit reasoning into the natural waiting time between incoming video clips, so reasoning cost is amortized over playback instead of concentrated at the moment of interaction.
      **关键洞见:** 核心洞见是把显式推理挪到相邻视频片段到来之间的自然等待时间里，这样推理开销就分摊到播放过程中，而不是集中在交互发生的那一刻。
      evidence:: E3, E5, E15
    - **Claims:** The paper's logical claims are that pre-query streaming thoughts can reduce query-time latency, that a dual-memory protocol can make offline VideoLLMs causal, that the training and data recipe improves accuracy, and that the method has bounded but real efficiency costs.
      **核心主张:** 本文的逻辑主张有四点：查询前生成的流式思考（streaming thought）能够降低查询时的延迟；一套双记忆协议能让离线的视频大语言模型（VideoLLM）具备因果性；相应的训练与数据方案能提升准确率；该方法在效率上有真实但有限的代价。
      evidence:: E3, E4, E11, E13, E17
        - C1: VST reduces query-answer latency for reasoning-heavy video QA by generating CoT-style thoughts before the question arrives instead of only after it.
          C1：在推理密集型的视频问答任务中，Video Streaming Thinking（VST）通过在问题到来之前、而不是仅在问题到来之后生成 chain-of-thought（CoT）式的思考，来降低从提问到给出答案的延迟。
          evidence:: E5, E15
        - C2: A short-term visual buffer plus long-term textual semantic memory lets a VideoLLM operate under temporal causality and finite context while preserving useful history.
          C2：一个短期视觉缓冲区加上一份长期文本语义记忆，能让视频大语言模型（VideoLLM）在时间因果性和有限上下文的约束下工作，同时保留有用的历史信息。
          evidence:: E4, E6
        - C3: The VST supervised fine-tuning (VST-SFT), reinforcement learning (VST-RL), and knowledge-graph data synthesis recipe improves online benchmark accuracy and remains competitive on offline long-video reasoning benchmarks.
          C3：VST 的监督微调（VST supervised fine-tuning，VST-SFT）、强化学习（VST reinforcement learning，VST-RL）以及基于知识图谱的数据合成方案，既提升了在线基准测试的准确率，又在离线长视频推理基准上保持竞争力。
          evidence:: E8, E11, E12, E13
        - C4: VST is complementary to efficient visual-memory methods rather than a free substitute, because it spends extra generated tokens and relies mainly on text-guided memory.
          C4：VST 与高效视觉记忆方法是互补关系，而非可以免费替代它们，因为 VST 会消耗额外生成的 token，并且主要依赖以文本为主导的记忆。
          evidence:: E17
- ## Mechanism and Design
    - **Core Mechanism:** VST treats live video as a multi-turn conversation: each new clip produces a streaming thought, a short textual summary of useful events, and the model later answers from accumulated thoughts plus the current clip.
      **核心机制:** VST 把实时视频当作一场多轮对话来处理：每个新片段都会产生一段流式思考（streaming thought），也就是对有用事件的简短文本摘要；随后模型根据累积的思考加上当前片段来回答问题。
      evidence:: E4, E5
        - Incoming frame features are grouped into clips when the visual-token budget is reached, and each clip is processed together with previous memory to generate the next thought.
          当视觉 token 预算用满时，进入的帧特征会被归拢成一个片段，每个片段与之前的记忆一起处理，从而生成下一段思考。
          evidence:: E4
        - The visual side keeps recent raw video tokens for precise perception, while the text side stores prior thoughts as semantic memory with first-in-first-out eviction.
          视觉一侧保留最近的原始视频 token，用于精确感知；文本一侧把先前的思考存为语义记忆，并采用先进先出（FIFO）的淘汰策略。
          evidence:: E4
        - When the user asks, the final answer is generated directly from the current clip and accumulated memory rather than replaying the whole video or starting a long reasoning trace from scratch.
          当用户提问时，最终答案直接根据当前片段和累积记忆生成，而不是重放整段视频，也不是从零开始生成一条冗长的推理轨迹。
          evidence:: E5, E15
    - **Data / Control Flow:** The execution order is clip arrival, visual encoding, streaming-thought generation, memory update, and final answer on query; the training order mirrors this sequence so the model sees only past and current evidence.
      **数据/控制流:** 执行顺序为：片段到达、视觉编码、流式思考生成、记忆更新，最后在收到查询时给出答案；训练顺序与这一流程保持一致，因此模型只能看到过去和当前的证据。
      evidence:: E4, E6, E7, E8
        - At inference, streaming thoughts are scheduled before the next clip arrives, so the user-facing path after the query contains only current encoding and answer generation.
          在推理阶段，流式思考在下一个片段到达之前就已被调度完成，因此用户在提问之后所经历的路径只包含当前编码和答案生成。
          evidence:: E15
        - During VST-SFT, training examples interleave memory, clip, thought pairs and end with the final clip, question, and answer, with next-token prediction applied only to thoughts and the final response.
          在 VST 监督微调（VST-SFT）过程中，训练样本交替排列「记忆、片段、思考」三元组，并以最后一个片段、问题和答案结尾，其中下一词元预测（next-token prediction）只作用于思考内容和最终回答。
          evidence:: E6
        - The synthetic-data path builds a video knowledge graph, samples evidence chains with depth-first search, and asks an offline model to generate streaming CoT and QA pairs aligned to those chains.
          合成数据的生成路径会先构建视频知识图谱，用深度优先搜索（DFS）采样证据链，再让一个离线模型生成与这些证据链对齐的流式思维链（CoT）和问答对。
          evidence:: E8
    - **Design Decisions:** The design consistently chooses lightweight text memory and causal masks over keeping all raw visual evidence, trading away some visual fidelity to keep streaming feasible.
      **设计决策:** 整体设计一贯选择轻量的文本记忆和因果掩码，而非保留全部原始视觉证据，以牺牲部分视觉保真度为代价来保持流式处理的可行性。
      claim_kind:: analyst_assessment
      evidence:: E4, E6, E17
        - Need: unbounded streams exceed fixed context; choice: a recent visual buffer plus long-term textual memory; closest alternative: visual-token compression or retrieval-only memory; tradeoff: summaries can omit details later needed for a question.
          需求：无界的视频流会超出固定的上下文长度；选择：一个近期视觉缓冲区加上长期文本记忆；最接近的替代方案：视觉词元压缩或仅依赖检索的记忆；权衡：摘要可能遗漏后续问题所需的细节。
          claim_kind:: analyst_assessment
          evidence:: E2, E4, E17
        - Need: avoid future-frame leakage during training; choice: a streaming attention mask that exposes only a sliding visual window plus non-visual history; closest alternative: offline global attention; tradeoff: old raw frames must be represented by text memory.
          需求：训练时避免未来帧信息泄漏；选择：一种流式注意力掩码，只暴露一个滑动的视觉窗口以及非视觉的历史信息；最接近的替代方案：离线的全局注意力；权衡：较早的原始帧必须由文本记忆来表示。
          claim_kind:: analyst_assessment
          evidence:: E6
        - Need: improve thoughts without separately scoring every intermediate thought; choice: group-relative policy optimization (GRPO) with final-answer reward assigned across trajectory tokens; tradeoff: credit assignment can be noisy when a final answer depends on only some thoughts.
          需求：在无需单独为每一个中间思考打分的前提下改进思考质量；选择：采用组相对策略优化（group-relative policy optimization，GRPO），把最终答案的奖励分配到整条轨迹的词元上；权衡：当最终答案只依赖部分思考时，功劳分配可能带有噪声。
          claim_kind:: analyst_assessment
          evidence:: E7
    - **Implementation Surface:** The reported implementation starts from Qwen2.5-VL, freezes the visual encoder and projection layer, processes video at 2 fps, trains the 7B model on 32 x 80GB GPUs, and evaluates through lmms-eval with inference caps on visual tokens and thinking times.
      **实现边界:** 文中报告的实现从 Qwen2.5-VL 出发，冻结视觉编码器和投影层，以 2 fps 处理视频，在 32 块 80GB GPU 上训练 7B 模型，并通过 lmms-eval 进行评测，同时对视觉词元数量和思考次数设置推理上限。
      evidence:: E9
        - VST-RL uses verl with vLLM rollout and Fully Sharded Data Parallel (FSDP), while the appendix reports one epoch for both VST-SFT and VST-RL plus actor learning-rate, batch, and rollout settings.
          VST 强化学习（VST-RL）使用 verl，配合 vLLM 采样（rollout）以及完全分片数据并行（Fully Sharded Data Parallel，FSDP）；附录还报告了 VST-SFT 和 VST-RL 均训练一个轮次（epoch），以及行动者（actor）的学习率、批处理和采样设置。
          evidence:: E9
        - Testing caps each inference step, including streaming-think and final answer, at 8,192 video tokens and limits max thinking times to 4 for efficient evaluation.
          测试时，对每个推理步骤（包括流式思考和最终答案）的视频 token 数量上限都设为 8,192 个，并把最大思考次数限制为 4 次，以便高效评估。
          evidence:: E9
- ## Evaluation and Evidence
    - **Setup:** The evaluation covers online temporal reasoning with StreamingBench and OVO-Bench, offline general video understanding with VideoMME, long-video understanding with LongVideoBench, and complex reasoning with VideoHolmes.
      **实验设置:** 这次评估涵盖了以下几个方面：用 StreamingBench 和 OVO-Bench 考查在线时序推理（即随视频到来、不使用未来帧的推理），用 VideoMME 考查离线的通用视频理解，用 LongVideoBench 考查长视频理解，用 VideoHolmes 考查复杂推理。
      evidence:: E9, E10
    - **Claim-Evidence Matrix:** The paper backs the latency claim with a direct latency table, the causal-memory claim with method design, the accuracy claim with online, offline, and ablation results, and the cost boundary with its own limitation section.
      **主张-证据矩阵:** 论文用一张直接的延迟对照表来支撑关于延迟的论断，用方法设计来支撑关于因果记忆的论断，用在线、离线和消融实验结果来支撑关于准确率的论断，并用专门的局限性章节来说明成本边界。
      claim_kind:: analyst_assessment
      evidence:: E4, E11, E13, E15, E17
        - C1 is supported by Table 6 and the streaming pipeline: VST keeps query-time latency close to direct-answer models while reasoning baselines pay post-query CoT latency.
          论断 C1 由表 6 和流式流水线支撑：Video Streaming Thinking（VST）让查询时的延迟接近于直接给出答案的模型，而采用推理方式的基线则要付出查询之后进行 chain-of-thought（CoT）所带来的延迟。
          evidence:: E15
        - C2 is supported mechanistically by the dual-memory formulation and streaming attention mask, but not isolated by a clean memory-component ablation.
          论断 C2 从机制上由双重记忆的建模方式和流式注意力掩码所支撑，但论文并没有用一个干净的记忆组件消融实验把它单独隔离出来验证。
          claim_kind:: analyst_assessment
          evidence:: E4, E6, E14
        - C3 is supported by online, offline, training-schedule, thinking-time, and model-size evaluations, though the paper does not report statistical uncertainty.
          论断 C3 由在线评估、离线评估、训练方案评估、思考次数评估和模型规模评估共同支撑，不过论文没有报告统计上的不确定性。
          claim_kind:: analyst_assessment
          evidence:: E11, E12, E13, E14
    - **Headline Results:** The headline result is not a single largest number but the accuracy-latency tradeoff: VST-7B improves over open-source streaming baselines on online tasks, stays competitive offline, and avoids the large post-query latency of CoT baselines.
      **关键结果:** 最核心的结果不是某个最大的单一数字，而是准确率与延迟之间的权衡：VST-7B 在在线任务上比开源的流式基线更好，在离线任务上保持有竞争力的水平，同时避免了 CoT 基线在查询之后产生的巨大延迟。
      evidence:: E11, E12, E15
        - Supported claim: C3; configuration: VST-7B; baselines: Streamforest and Streamo; metric: benchmark accuracy; direction and delta: 79.5 versus 77.3 on StreamingBench and 59.3 versus 57.9 on OVO-Bench; caveat: no variance or repeated-run statistics reported.
          支撑的论断：C3；配置：VST-7B；基线：Streamforest 和 Streamo；指标：基准测试准确率；方向与差值：在 StreamingBench 上为 79.5 对 77.3，在 OVO-Bench 上为 59.3 对 57.9；说明：论文没有报告方差或重复运行的统计数据。
          evidence:: E11
        - Supported claim: C3; configuration: VST-7B; baselines: TimeChat-Online and Video-R1; metric: accuracy; direction and delta: +6.9 on VideoMME-long, +2.6 on LongVideoBench, and +5.4 on VideoHolmes; caveat: benchmark comparability depends on identical evaluation settings.
          支撑的论断：C3；配置：VST-7B；基线：TimeChat-Online 和 Video-R1；指标：准确率；方向与差值：在 VideoMME-long 上提升 6.9，在 LongVideoBench 上提升 2.6，在 VideoHolmes 上提升 5.4；说明：基准测试之间是否可比取决于评估设置是否完全一致。
          evidence:: E12
        - Supported claim: C1; configuration: VideoHolmes latency; baselines: Qwen2.5-VL-7B with CoT and Video-R1 with CoT; metric: query-answer latency; direction and delta: 0.56s for VST-7B versus 5.30s and 8.80s; caveat: pre-query token generation is outside QA latency.
          支撑的论断：C1；配置：VideoHolmes 上的延迟测量；基线：带 CoT 的 Qwen2.5-VL-7B 和带 CoT 的 Video-R1；指标：查询到答案的延迟（query-answer latency，QA latency）；方向与差值：VST-7B 为 0.56 秒，而两个基线分别为 5.30 秒和 8.80 秒；说明：查询之前生成 token 所花的时间不计入 QA latency。
          evidence:: E15
    - **Ablations and Sensitivity:** The ablations suggest the VST-specific data and two-stage training both matter, while more streaming thoughts help up to a point and then add redundant memory detail.
      **消融与敏感性:** 消融实验表明，VST 专用数据和两阶段训练都很重要；而增加流式思考（streaming thought，指在最终回答用户问题之前，为新视频片段生成的中间文本摘要或推理更新）的数量，在一定范围内有帮助，超过这个范围后就只会增加冗余的记忆细节。
      evidence:: E13, E14
        - The VST data mix outperforms LLaVA-Vid-only supervised fine-tuning, with the reported 20K LLaVA-Vid plus 30K VST mix giving +6.6 OVO-Bench points over 50K LLaVA-Vid alone.
          VST 数据配比优于仅用 LLaVA-Vid 数据做的监督微调（supervised fine-tuning，SFT，即让模型模仿学习目标输出的训练方式）：文中报告的 20K 条 LLaVA-Vid 加 30K 条 VST 的混合配比，比单用 50K 条 LLaVA-Vid 在 OVO-Bench 上高出 6.6 分。
          evidence:: E13
        - VST-SFT and VST-RL have different reported strengths, with SFT helping backward memory and RL helping forward prediction; using both gives the best reported OVO-Bench and VideoMME scores.
          VST 监督微调（VST-SFT）和 VST 强化学习（VST-RL）各有报告出来的优势：SFT 有助于向后记忆能力，RL 有助于向前预测能力；两者同时使用可获得文中报告的最佳 OVO-Bench 和 VideoMME 成绩。
          evidence:: E13
        - Increasing max streaming thinking times improves Backward accuracy through 16 steps, while Real-Time and Forward tasks plateau after about 4 steps, marking a practical budget boundary.
          增加流式思考的最大次数，在达到 16 步之前会持续提升向后（Backward）任务的准确率；而实时（Real-Time）和向前（Forward）任务在大约 4 步之后就趋于饱和，这标出了一个实际可用的预算边界。
          evidence:: E14
    - **Reproducibility Gaps:** The paper says code, data, and models will be released and reports substantial training details, hardware, backends, datasets, and inference caps, but it does not report seeds, repeat counts, variance, full filtering acceptance rates, or release verification in the provided text.
      **可复现性缺口:** 论文声称会公开代码、数据和模型，并报告了大量训练细节、硬件、后端、数据集与推理上限，但在所提供的文本中没有报告随机种子、重复次数、方差、完整的过滤接受率，也没有报告公开发布的验证情况。
      claim_kind:: analyst_assessment
      evidence:: E1, E9, E13, E15
- ## Technical Judgment
    - **What Holds Up:** The core systems argument holds up: when a live stream creates idle time before a query, moving reasoning into that interval can reduce observed QA latency while preserving a compact history for later temporal questions.
      **站得住的结论:** 核心的系统性论点是成立的：当直播流在查询到来之前产生了空闲时间，把推理挪到这段空闲时间内进行，既能降低观测到的问答延迟（query-answer latency，QA latency，即从用户提交查询到模型作出响应的时间），又能为后续的时序类问题保留一份紧凑的历史记录。
      claim_kind:: analyst_assessment
      evidence:: E3, E4, E15
        - The ablation that VST data plus both VST-SFT and VST-RL gives the best reported scores makes the training recipe more credible than a pure prompting story.
          消融实验显示，VST 数据加上 VST-SFT 和 VST-RL 两者共同使用可获得报告出来的最佳成绩，这让整个训练方案比单纯依靠提示词的说法更可信。
          claim_kind:: analyst_assessment
          evidence:: E13
        - The latency table is persuasive for query-time responsiveness because the closest reasoning baselines defer CoT generation until after the query.
          延迟对比表在查询时的响应速度方面很有说服力，因为最接近的那些推理类基线方法都要等到查询到来之后才生成思维链（chain-of-thought，CoT，即模型在给出答案之前或同时生成的分步自然语言推理文本）。
          claim_kind:: analyst_assessment
          evidence:: E15
    - **Where It May Fail:** VST may fail when the stream has little idle time, when useful evidence is hard to summarize into text, when a later question needs a precise old visual detail that was evicted, or when token cost matters more than query-time latency.
      **可能失效之处:** 在以下情况下 VST 可能会失效：视频流几乎没有空闲时间；有用的证据难以概括成文本；后续问题需要一个已被丢弃的、精确的旧视觉细节；或者相比查询时的延迟，token 开销更为重要。
      claim_kind:: analyst_assessment
      evidence:: E4, E14, E17
        - The reported plateau for some tasks after about 4 thinking steps suggests extra thoughts can become redundant rather than universally useful.
          文中报告的某些任务在大约 4 步思考之后就趋于饱和，这说明额外的思考步骤可能会变得冗余，而不是在所有情况下都有用。
          claim_kind:: analyst_assessment
          evidence:: E14
        - The accuracy evidence is broad but not uncertainty-aware, since the paper does not report variance, confidence intervals, or repeat counts for the benchmark deltas.
          准确率方面的证据覆盖面很广，但没有考虑不确定性，因为论文没有报告基准测试差值的方差、置信区间或重复次数。
          claim_kind:: analyst_assessment
          evidence:: E11, E12, E13
    - **Relation to Other Work:** Compared with streaming visual-memory systems such as Streamforest, TimeChatOnline, VideoLLM-online, Dispider, and Flash-VStream, VST shifts the emphasis from retaining visual tokens to generating evolving semantic thoughts; compared with Video-R1 or LongVILA-R1-style video reasoning, it moves reasoning before the query.
      **与已有工作的关系:** 与 Streamforest、TimeChatOnline、VideoLLM-online、Dispider、Flash-VStream 等流式视觉记忆系统相比，VST 把重点从保留视觉 token 转向生成不断演化的语义思考；与 Video-R1 或 LongVILA-R1 这类视频推理方法相比，它把推理放到了提问之前。
      claim_kind:: analyst_assessment
      evidence:: E2, E5, E11, E12
        - The paper's own limitation frames text-guided memory as orthogonal to streaming visual-memory mechanisms, so the clean research comparison is not replacement but complementarity.
          论文自己指出的局限在于，把文本引导的记忆看作与流式视觉记忆机制相互正交，因此从研究角度看，二者之间清晰的关系不是相互替代，而是彼此互补。
          claim_kind:: analyst_assessment
          evidence:: E17
    - **Transferable Lesson:** For interactive AI systems, a useful pattern is to spend predictable idle time on incremental state-building, store the result in a compact form, and keep the user-triggered path short and direct.
      **可迁移启发:** 对于交互式人工智能系统，一个实用的模式是：利用可预测的空闲时间做增量式的状态构建，把结果以紧凑的形式存储起来，并让用户触发的处理路径保持简短直接。
      claim_kind:: analyst_assessment
      evidence:: E3, E5, E15
- ## Glossary
  collapsed:: true
    - Video Large Language Model: A language model extended to take video-derived visual inputs and answer natural-language questions about them.
      视频大语言模型（Video Large Language Model）：一种经过扩展、能够接收从视频中提取的视觉输入，并回答关于视频的自然语言问题的语言模型。
    - online video understanding: Understanding video as it arrives over time, without using future frames that have not yet appeared.
      在线视频理解：随着视频随时间不断到达而对其进行理解，不使用尚未出现的未来帧。
    - context window: The bounded set of tokens the model can attend to at one time; for video, this limits how much raw visual evidence can remain visible.
      上下文窗口（context window）：模型在同一时刻能够关注的有界 token 集合；对视频而言，这限制了可以持续保持可见的原始视觉证据的数量。
    - Video Streaming Thinking: The paper's paradigm of generating intermediate thoughts during video playback and answering later from those thoughts plus the current clip.
      视频流式思考（Video Streaming Thinking）：论文提出的一种范式，即在视频播放过程中生成中间思考，随后根据这些思考加上当前片段来回答问题。
    - chain-of-thought: Step-by-step natural-language reasoning text generated by a model before or alongside an answer.
      思维链（chain-of-thought）：模型在给出答案之前或同时生成的逐步自然语言推理文本。
    - streaming thought: An intermediate textual summary or reasoning update generated for a new video clip before the final user question is answered.
      流式思考（streaming thought）：在回答用户的最终问题之前，为新的视频片段生成的中间文本摘要或推理更新。
    - VST supervised fine-tuning: The imitation-learning stage that teaches the model the streaming thought format under causal video constraints.
      VST 监督微调：这是一个模仿学习阶段，在因果视频约束下（即只能使用已经出现的帧，不能使用未来的帧）教会模型生成流式思考的格式。
    - VST reinforcement learning: The on-policy stage that samples full streaming trajectories and optimizes them using a final-answer reward; GRPO is the group-relative policy optimization method used.
      VST 强化学习：这是一个同策略（on-policy）阶段，会采样完整的流式思考轨迹，并利用最终答案的奖励信号对其进行优化；其中所用的组相对策略优化方法是 GRPO。
    - knowledge graph: A graph of entities and relations extracted from a video; the paper samples paths through it as multi-hop evidence for synthetic training questions.
      知识图谱（knowledge graph）：从视频中抽取出的、由实体和关系构成的图；论文会在图上采样路径，作为多跳证据来生成合成的训练问题。
    - Fully Sharded Data Parallel: A distributed training technique that shards model parameters and optimizer state across GPUs to reduce per-device memory pressure.
      全分片数据并行（Fully Sharded Data Parallel，FSDP）：一种分布式训练技术，把模型参数和优化器状态切分到多块 GPU 上，以降低单卡的显存压力。
    - query-answer latency: The measured time from user query submission to the model's response, not necessarily the total computation spent while the video was playing.
      问答延迟（query-answer latency）：从用户提交查询到模型给出回答之间测得的时间，不一定等于视频播放期间所花费的全部计算时间。
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
