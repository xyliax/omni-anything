- **Title:** Reinforcement Learning for Interactive Streaming Video Understanding: A Survey of Methods, Infrastructure, and Open Challenges
  **标题:** 用于交互式流式视频理解的强化学习：方法、基础设施与开放挑战综述
- **Summary:** The survey argues that interactive streaming video understanding should be treated as a sequential decision-making problem and maps the architectures, reinforcement-learning methods, infrastructure, data gaps, and open challenges needed to train such systems.
  **一句话总结:** 该综述主张，交互式流式视频理解应当被视为一个序贯决策问题。它梳理了训练此类系统所需的架构、强化学习方法、基础设施、数据缺口与开放挑战。
- **Paper Type:** survey
  **论文类型:** 综述
- **Venue:** Preprint 2026; venue Unknown
  **发表:** 预印本 2026；发表场所未知
- **Authors:** Lytton Feng; affiliation Unknown
  **作者:** Lytton Feng；所属机构未知
- **Keywords:** streaming video understanding, VideoLLM, reinforcement learning, RLHF, GRPO, preference optimization, multimodal infrastructure, real-time interaction
  **关键词:** 流式视频理解、视频大语言模型（VideoLLM）、强化学习、基于人类反馈的强化学习（RLHF）、组相对策略优化（GRPO）、偏好优化、多模态基础设施、实时交互
- ## Orientation
    - **Background:** This paper sits at the meeting point of video-language models and reinforcement learning. A Video Large Language Model (VideoLLM) is a language model connected to video input; reinforcement learning (RL) trains a model by rewarding good sequences of actions rather than copying example answers.
      **背景:** 本文处于视频语言模型与强化学习（RL）的交汇处。视频大语言模型是一种连接视频输入的语言模型；而强化学习通过奖励优质的动作序列来训练模型，而不是让模型照抄示例答案。
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A live video assistant must watch continuously, stay quiet most of the time, answer when asked, and sometimes warn the user before it is too late.
      **通俗问题:** 实时视频助手必须持续观看画面，在大多数时间保持安静，在被提问时作答，并在为时已晚之前向用户发出警告。
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** The stream never really ends, future frames are unavailable, speaking too soon can be wrong, speaking too late can be useless, and silence is itself a decision.
      **为何困难:** 视频流永远不会真正结束，未来的帧无法获取。开口太早可能出错，开口太晚可能毫无用处，而保持沉默本身也是一种决策。
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Treat the assistant as an agent whose whole interaction over time should be rewarded, not as a captioning model trained one answer at a time.
      **一句话核心思路:** 将助手视为一个智能体，对其随时间推移的整个交互过程给予奖励，而不是将其视为每次只训练一个答案的字幕生成模型。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a map of the emerging intersection between real-time Video Large Language Models (VideoLLMs), which understand video with language-model-style reasoning, and reinforcement learning for deciding when to speak, what to say, and how to trade latency against accuracy.
      **阅读价值:** 把这篇综述当作一张地图，它描绘了一个新兴交叉领域：一方面是实时视频大语言模型（VideoLLM），这类模型用语言模型式的推理来理解视频；另一方面是强化学习，用于决定何时发言、说什么，以及如何在延迟与准确性之间权衡。
      evidence:: E1, E2
    - **One-Sentence Contribution:** The survey organizes RL for streaming VideoLLMs by showing that streaming interaction is best viewed as trajectory-level decision making rather than next-token imitation.
      **一句话贡献:** 该综述系统地组织了面向流式视频大语言模型的强化学习研究，其核心论点是：流式交互最好被视为轨迹层面的决策，而非下一词元的模仿。
      evidence:: E2, E3
    - **Mental Model:** Picture a live assistant watching a camera feed like a careful co-pilot: most moments require silence, some require an immediate warning, and every spoken answer changes what happens next.
      **记忆模型:** 想象一个实时助手像谨慎的副驾驶一样注视摄像头画面：大部分时刻需要保持沉默，某些时刻需要立即发出警告，而每一次口头回答都会改变后续发生的事情。
      claim_kind:: analyst_assessment
    - **Best Evidence:** The survey's strongest support is breadth-of-landscape evidence rather than a new experiment: it catalogs architectures, RL methods, infrastructure, datasets, benchmarks, and gaps.
      **最佳证据:** 该综述最有力的支撑是全景式的广度证据，而非一项新实验：它编目了架构、强化学习方法、基础设施、数据集、基准测试与缺口。
      evidence:: E3, E5, E9
        - Supports C1: landscape survey; prior work corpus; count of RL-for-video papers and directly streaming works; establishes that streaming-specific RL is still narrow despite rapid offline-video RL growth; support status strong as a catalog claim but dependent on reference completeness.
          支持论点 C1：这是一项全景式综述，构建了先前工作的语料库，统计了面向视频的强化学习论文和直接面向流式处理的工作数量。该论据表明，尽管离线视频的强化学习增长迅速，但专门针对流式处理的强化学习仍然范围狭窄。作为目录性主张，其支撑强度较高，但依赖于参考文献的完整性。
          evidence:: E3, E6
        - Supports C2: architecture taxonomy; compared categories; RL-relevant dimensions such as action space, timing-content coupling, and rollout cost; support status useful as conceptual synthesis rather than empirical validation.
          支持论点 C2：该论据提出了架构分类法，对比了各个类别，并考察了与强化学习相关的维度，例如动作空间、时序与内容的耦合关系，以及采样轨迹成本。其支撑状态作为概念综合较为有用，而非经验验证。
          evidence:: E4, E5
        - Supports C3: infrastructure and data audit; compared RL frameworks and datasets; finding that no listed framework or dataset natively covers streaming video RL/preference data; support status strong within the survey's tabled resources.
          支持论点 C3：该论据进行了基础设施与数据审计，对比了强化学习框架和数据集。研究发现，所列出的框架或数据集均未原生支持流式视频的强化学习数据或偏好数据。在综述所整理的资源表格范围内，其支撑强度较高。
          evidence:: E9, E10, E11
    - **Main Caveat:** The paper is a forward-looking survey with many 2025-2026 preprints, blog posts, and unpublished preliminary results, so its roadmap is more useful as a research agenda than as settled empirical fact.
      **主要边界:** 本文是一篇前瞻性综述，包含许多 2025-2026 年的预印本、博客文章和未发表的初步结果。因此，其规划路线图作为研究议程更有价值，而非既定的经验事实。
      claim_kind:: analyst_assessment
- ## Argument Map
    - **Problem and Stakes:** The survey frames streaming video understanding as a shift from offline video QA to real-time interaction where models continuously process unbounded feeds and must make timing-sensitive decisions under latency and causal-information constraints.
      **问题与重要性:** 该综述将流式视频理解界定为从离线视频问答向实时交互的转变。在这种交互中，模型需要持续处理无界的输入流，并且必须在延迟和因果信息约束下做出对时间敏感的决策。
      evidence:: E1, E4
    - **Prior Gap:** The paper claims supervised fine-tuning (SFT), training by imitating target tokens, is misaligned with deployment because streaming decisions have delayed consequences, while RL-for-video work is mostly offline and only a small set directly targets streaming.
      **已有方法缺口:** 本文认为，监督微调（SFT）即通过模仿目标词元进行训练的方法，与实际部署需求不符，因为流式决策的后果具有延迟性。同时，面向视频的强化学习工作大多是离线的，只有一小部分直接针对流式处理。
      evidence:: E2, E6
    - **Key Insight:** The central insight is that streaming interaction is a trajectory-level control problem: timing, content, silence, memory use, and latency jointly determine success, so architecture and infrastructure choices constrain which RL formulation is feasible.
      **关键洞见:** 核心见解在于，流式交互是一个轨迹级别的控制问题：时机、内容、沉默、内存使用与延迟共同决定成败，因此架构与基础设施的选择制约着可行的强化学习（reinforcement learning，RL）建模方式。
      evidence:: E2, E5, E12
    - **Claims:** The survey advances four main claims about the state of RL for interactive streaming video understanding.
      **核心主张:** 该综述提出了关于交互式流式视频理解的强化学习现状的四项主要主张。
      evidence:: E3
        - C1: RL for video understanding has expanded quickly, especially through Group Relative Policy Optimization (GRPO), which compares multiple sampled answers for the same prompt against a reward, but streaming-specific RL remains nascent.
          C1：视频理解的强化学习发展迅速，尤其是通过群组相对策略优化（Group Relative Policy Optimization，GRPO）——该方法将同一提示词的多个采样回答与奖励进行比较，但专门针对流式的强化学习仍处于起步阶段。
          evidence:: E6, E7
        - C2: Streaming VideoLLM architectures differ in RL trainability because decoupled trigger-response, unified silence-token, full-duplex multimodal, and continuous micro-turn designs create different action spaces, memory costs, and reward-design problems.
          C2：流式视频大语言模型（VideoLLM）架构在强化学习可训练性上存在差异，因为解耦的触发-响应、统一的沉默标记、全双工多模态以及连续微回合设计会产生不同的动作空间、内存开销和奖励设计问题。
          evidence:: E5
        - C3: Existing RL training frameworks, video RL datasets, and reward models do not yet natively support streaming video RL, especially incremental frame ingestion, cross-window cache handling, and streaming preference labels.
          C3：现有的强化学习训练框架、视频强化学习数据集和奖励模型尚不支持原生的流式视频强化学习，尤其是增量帧摄入、跨窗口缓存处理和流式偏好标签。
          evidence:: E9, E10, E13
        - C4: The core open problems are temporal credit assignment, real-time reward design, silent-vs-speech exploration, rollout cost and pipeline imbalance, and lack of standardized preference data.
          C4：核心开放问题包括时序信用分配（temporal credit assignment）、实时奖励设计、沉默与说话的探索、采样轨迹（rollout）成本与流水线不平衡，以及缺乏标准化的偏好数据。
          evidence:: E12, E13, E14
- ## Mechanism and Design
    - **Core Mechanism:** As a survey, the paper does not introduce one algorithm; its mechanism is a design decomposition that maps streaming VideoLLM architectures to possible RL problem formulations, reward signals, data needs, and systems bottlenecks.
      **核心机制:** 作为一篇综述，该论文并未引入单一算法；其机制是一种设计分解，将流式视频大语言模型（VideoLLM）架构映射到可能的强化学习问题建模、奖励信号、数据需求和系统瓶颈。
      evidence:: E3, E5
    - **Data / Control Flow:** The implied streaming RL loop is: frames arrive incrementally; the model updates limited context; it chooses silence or response; the interaction continues; a trajectory-level reward later evaluates content, timing, and silence decisions together.
      **数据/控制流:** 隐含的流式强化学习循环为：视频帧增量到达；模型更新有限的上下文；它选择沉默或响应；交互继续进行；随后，一个轨迹级别的奖励将共同评估内容、时机与沉默决策。
      evidence:: E2, E9, E13
        - In decoupled trigger-response systems, a small trigger policy decides whether to wake a larger response model; in unified systems, a single model emits either words or a silence/end token.
          在解耦的触发-响应系统中，一个小型触发策略决定是否唤醒更大的响应模型；在统一系统中，单个模型输出词语或沉默/结束标记。
          evidence:: E5
        - For streaming, the reward must score not only whether an answer is true, but whether it was emitted at the right time and whether staying silent would have been better.
          对于流式场景，奖励不仅要对回答是否正确打分，还要评估回答是否在正确的时间输出，以及保持沉默是否会更好。
          evidence:: E13
        - Training requires rollouts, meaning generated interaction trajectories, while preserving attention state across a sliding video window; the survey identifies this as missing from current frameworks.
          训练需要采样轨迹（rollout），即模型生成的交互轨迹，同时需要在滑动的视频窗口中保持注意力状态；该综述指出，当前框架缺乏这一能力。
          evidence:: E9, E11
    - **Design Decisions:** The survey's main design comparison is not between parameter settings but between decomposition choices for making streaming RL tractable.
      **设计决策:** 该综述的主要设计对比不在于参数设置，而在于如何分解流式强化学习（RL）问题使其可行。
      evidence:: E5, E8, E9
        - Need: reduce the when-to-speak problem; choice: separate trigger policy or unified token policy; tradeoff: binary triggers simplify RL but cannot fully condition on what the response model would say.
          需求：降低「何时发言」问题的难度；选择：使用独立的触发策略或统一的词元策略；权衡：二元触发简化了强化学习，但无法完全以响应模型将要生成的内容为条件。
          evidence:: E5
        - Need: train video behavior without expensive human reward models; choice: GRPO dominates because it can use verifiable rewards, while Direct Preference Optimization (DPO), which trains from chosen-versus-rejected pairs, needs paired trajectories and Proximal Policy Optimization (PPO), an on-policy RL method, is costlier.
          需求：在不使用昂贵的人工奖励模型的情况下训练视频行为；选择：组相对策略优化（GRPO）占据主导，因为它能使用可验证的奖励；而直接偏好优化（DPO）从「采纳-拒绝」配对中训练，需要成对的采样轨迹；近端策略优化（PPO）作为一种在线策略强化学习方法，成本更高。
          evidence:: E6, E7
        - Need: keep streaming rollouts feasible; choice: extend RL systems with incremental frame feeding, key-value cache (KV cache: saved attention state reused across tokens) management, and trajectory-level rewards; tradeoff: this adds systems complexity not present in fixed video QA.
          需求：保持流式采样轨迹可行；选择：通过增量帧输入、键值缓存（KV cache：跨词元复用的已保存注意力状态）管理和轨迹级奖励来扩展强化学习系统；权衡：这引入了固定视频问答中不存在的系统复杂性。
          evidence:: E9, E11
    - **Implementation Surface:** The paper audits implementation surfaces including general RLHF frameworks, video-specific RL pipelines, streaming datasets, benchmarks, reward models, and compute costs, but it does not release a new implementation.
      **实现边界:** 该论文审计了多个实现层面，包括通用的基于人类反馈的强化学习（RLHF）框架、视频专用强化学习流水线、流式数据集、基准测试、奖励模型和计算成本，但并未发布新的实现。
      evidence:: E3, E9, E10
- ## Evaluation and Evidence
    - **Setup:** The evidence is survey evidence: literature taxonomy, comparative tables, and a roadmap, not a controlled experimental evaluation of a new model or training system.
      **实验设置:** 其证据属于综述证据：文献分类、对比表格和路线图，而非针对新模型或训练系统的受控实验评估。
      claim_kind:: analyst_assessment
    - **Claim-Evidence Matrix:** The survey supports its claims mainly by cataloging systems and exposing mismatches between what current methods optimize and what streaming interaction requires.
      **主张-证据矩阵:** 该综述主要通过梳理系统并揭示当前方法的优化目标与流式交互需求之间的不匹配来支撑其主张。
      evidence:: E3, E6, E9, E12
        - C1 is supported by the paper's count of over 40 RL-for-video papers and its list of only four directly streaming RL works; evidence is broad but depends on the freshness and inclusion criteria of the survey corpus.
          C1 由论文统计的超过 40 篇视频强化学习论文以及仅 4 篇直接面向流式强化学习的工作列表所支撑；证据覆盖面广，但依赖于综述语料的时效性和纳入标准。
          evidence:: E6
        - C2 is supported by the architecture taxonomy and RL-relevant comparison table; evidence is conceptual synthesis, not measured trainability across architectures.
          C2 由架构分类和强化学习相关对比表所支撑；其证据属于概念综合，而非跨架构可训练性的实测结果。
          evidence:: E5
        - C3 and C4 are supported by the framework, dataset, benchmark, and challenge audits; the weakest part is the claim of unique dual imbalance, which is plausible but not experimentally established here.
          C3 和 C4 得到了框架、数据集、基准测试和挑战性审计的支持；最薄弱的部分是关于「唯一双重失衡」的主张——它听起来合理，但本文未通过实验予以证实。
          claim_kind:: analyst_assessment
    - **Headline Results:** Not applicable: this is a survey and does not report a new primary benchmark result; reported numbers belong to cited work and are used as landscape evidence.
      **关键结果:** 不适用：本文是一篇综述，不报告新的主要基准测试结果；文中所列数字来自被引用的文献，用作领域现状的佐证。
      claim_kind:: analyst_assessment
        - Supports C1: survey corpus; baseline is the broader RL-for-video literature; metric is number of directly streaming works; delta is over 40 video-RL papers versus only four direct streaming-RL works; support status strong as a survey observation.
          支持 C1：基于综述语料库；基线是更广泛的视频强化学习（Reinforcement Learning, RL）文献；衡量指标是直接面向流式的工作数量；差距体现为 40 余篇视频强化学习论文，而直接面向流式的强化学习工作仅有四篇；作为综述性观察，支持力度较强。
          evidence:: E6
        - Supports C3: framework audit; baseline is existing RL post-training frameworks; metric is native support for streaming video RL; delta is none of the surveyed frameworks natively support it; support status strong within the compared table.
          支持 C3：基于框架审计；基线是现有的强化学习后训练框架；衡量指标是对流式视频强化学习的原生支持；差距体现为所调研的框架均无原生支持；在所比较的表格范围内，支持力度较强。
          evidence:: E9
        - Supports C3: dataset audit; baseline is available video RL and streaming SFT datasets; metric is streaming-specific RL/preference data availability; delta is none reported; support status strong within the paper's dataset table.
          支持 C3：基于数据集审计；基线是现有的视频强化学习数据集和流式监督微调（Supervised Fine-Tuning, SFT）数据集；衡量指标是流式专用的强化学习与偏好数据是否可用；差距体现为没有任何相关数据被报告；在本文的数据集表格范围内，支持力度较强。
          evidence:: E10
    - **Ablations and Sensitivity:** Not applicable: the paper contains no ablations because it is a survey; sensitivity claims such as rollout cost and pipeline imbalance are drawn from cited systems rather than varied in a new experiment.
      **消融与敏感性:** 不适用：本文不含消融实验，因为它是一篇综述；像采样轨迹开销、流水线失衡这类敏感性主张均来自被引用的系统，而非在新的实验中加以改变。
      claim_kind:: analyst_assessment
    - **Reproducibility Gaps:** The main reproducibility gap is not code for the survey but missing field infrastructure: no standard streaming preference dataset, no streaming-aware reward model, and no natively streaming video RL framework are identified.
      **可复现性缺口:** 主要的可复现性缺口不在于综述代码，而在于该领域缺失的基础设施：文中未识别出标准的流式偏好数据集、具备流式感知的奖励模型，以及原生支持流式视频强化学习的框架。
      evidence:: E9, E10, E13
        - Several cited systems are preprints, blog posts, weights-only releases, or unpublished preliminary results, so exact training recipes and independent validation may be unavailable for parts of the roadmap.
          若干被引用的系统是预印本、博客文章、仅权重发布或未发表的初步结果，因此路线图中的部分内容可能缺乏精确的训练配方与独立验证。
          claim_kind:: analyst_assessment
- ## Technical Judgment
    - **What Holds Up:** The strongest part is the problem decomposition: timing, silence, causal streaming context, reward design, and systems rollout cost are genuinely coupled, and the architecture taxonomy makes clear why offline video QA methods do not transfer directly.
      **站得住的结论:** 最扎实的部分是问题分解：时机、沉默决策、因果式流式上下文、奖励设计与系统采样轨迹开销确实相互耦合；其架构分类法也清楚说明了为何离线视频问答方法无法直接迁移。
      claim_kind:: analyst_assessment
    - **Where It May Fail:** The survey may overstate maturity and consensus because many referenced works are very recent, streaming-specific evidence is sparse, and some strong-sounding claims, such as simultaneous rollout/training imbalance being unique, are not validated by controlled experiments in this paper.
      **可能失效之处:** 这篇综述可能高估了该领域的成熟度与共识程度，因为许多参考文献非常新近、针对流式的证据稀少，而且一些听起来很强的主张——例如「采样轨迹与训练同时进行的失衡是唯一的」——并未在本文中通过受控实验加以验证。
      claim_kind:: analyst_assessment
    - **Relation to Other Work:** Compared with standard RLHF and DPO work for language models, this survey emphasizes multimodal temporal control; compared with offline VideoLLM RL such as Video-R1-style GRPO, it highlights causal frame access, silence decisions, and sliding context; compared with streaming VideoLLMs such as AURA or VideoLLM-online, it asks how their SFT-trained behavior could become reward-optimized.
      **与已有工作的关系:** 与针对语言模型的标准 RLHF 和 DPO 工作相比，本综述强调多模态时间控制。与离线 VideoLLM 强化学习（如 Video-R1 风格的 GRPO）相比，本综述突出因果帧访问、静默决策和滑动上下文。与 AURA 或 VideoLLM-online 等流式 VideoLLM 相比，本综述探讨如何将其经 SFT 训练的行为转变为奖励优化。
      evidence:: E4, E6, E7
    - **Transferable Lesson:** The reusable systems lesson is to identify the decision boundary before choosing an RL algorithm: if the hard part is when to act, decompose timing, memory, and reward instrumentation before scaling up end-to-end generation training.
      **可迁移启发:** 可复用的系统经验是：在选择强化学习算法之前先确定决策边界。如果难点在于何时行动，则在扩展端到端生成训练之前，要先分解时序、记忆和奖励度量机制。
      claim_kind:: analyst_assessment
- ## Glossary
  collapsed:: true
    - Video Large Language Model: A language-model-based system that accepts video frames or video-derived tokens and produces language outputs such as answers, narration, or alerts.
      视频大语言模型（Video Large Language Model）：一种基于语言模型的系统，它接收视频帧或从视频导出的标记，并产生语言输出，例如回答、解说或警报。
    - streaming video understanding: Understanding video as it arrives over time, without waiting for the complete clip and without access to future frames.
      流式视频理解（streaming video understanding）：在视频随时间逐步到达时就进行理解，无需等待完整片段，也无法访问未来帧。
    - reinforcement learning: Training an agent to choose actions that maximize reward over a sequence; here, actions include staying silent, responding, and generating text.
      强化学习（reinforcement learning）：训练智能体在一系列步骤中选择使奖励最大化的行动；在此处，行动包括保持静默、做出回应和生成文本。
    - supervised fine-tuning: Training a pretrained model to imitate labeled examples, typically by predicting the next target token; the survey argues this is insufficient for trajectory-level streaming decisions.
      监督微调（supervised fine-tuning，SFT）：训练预训练模型来模仿标注样本，通常通过预测下一个目标标记来实现；该综述认为这对于轨迹级别的流式决策是不够的。
    - reinforcement learning from human feedback: A post-training pipeline that uses human preferences to train a reward model and then optimizes the policy against that reward, often using PPO.
      基于人类反馈的强化学习（reinforcement learning from human feedback，RLHF）：一种训练后流程，利用人类偏好训练一个奖励模型，然后针对该奖励优化策略，通常使用 PPO。
    - Proximal Policy Optimization: An on-policy RL algorithm that updates a policy using newly generated rollouts while limiting how far the policy changes at each update.
      近端策略优化（Proximal Policy Optimization，PPO）：一种在线策略强化学习算法，使用新生成的回放序列来更新策略，同时限制每次更新中策略变化的幅度。
    - Direct Preference Optimization: A preference-training method that uses chosen-versus-rejected response pairs without training a separate reward model.
      直接偏好优化（Direct Preference Optimization，DPO）：一种偏好训练方法，使用「被采纳」与「被拒绝」的回应配对，无需训练单独的奖励模型。
    - Group Relative Policy Optimization: An RL method that samples multiple responses for the same input and updates the model based on rewards relative to the group; popular for verifiable video reasoning tasks.
      组相对策略优化（Group Relative Policy Optimization，GRPO）：一种强化学习方法，对同一输入采样多个回应，并根据相对于组内的奖励来更新模型；在可验证的视频推理任务中较为流行。
    - key-value cache: Saved attention state from previous tokens or frames that lets a transformer continue generation without recomputing the entire past context.
      键值缓存（KV cache）：从先前的词元或帧中保存的注意力状态，使 Transformer 无需重新计算整个历史上下文即可继续生成。
    - rollout: A generated sequence of model actions and observations used for RL training; in streaming video, this can span many frame arrivals and silence/response decisions.
      轨迹（rollout）：用于强化学习训练的、由模型动作与观测组成的生成序列；在流式视频场景中，它可能跨越多个帧的到达以及多个静默或响应的决策。
    - Proactive Area Under the Curve: A metric used by cited work to jointly score proactive response quality and timing; the survey treats it as useful but too narrow for all streaming interactions.
      主动式曲线下面积（Proactive Area Under the Curve，PAUC）：被引文献使用的一种指标，用于联合评估主动响应的质量与时机；该综述认为它有用，但对所有流式交互而言覆盖面过窄。
    - temporal credit assignment: The problem of deciding which earlier observations and actions deserve credit or blame for a later reward, made harder when old video evidence has left the model's context window.
      时序信用分配（temporal credit assignment）：判断哪些早期观测与动作应当为后续奖励获得荣誉或承担过错的问题；当旧的视频证据已离开模型的上下文窗口时，这一问题变得更加困难。
- ## Evidence Index
  collapsed:: true
    - **E1:** problem/paper_statement | Abstract | medium
      locator:: Abstract
      quote:: Streaming video understanding—where models must continuously process unbounded video feeds and interact with users in real time—has emerged as a critical frontier for Video Large Language Models (VideoLLMs).
    - **E2:** insight/paper_statement | Abstract | medium
      locator:: Abstract
      quote:: reinforcement learning (RL) offers a principled framework for optimizing the temporally extended, reward-sparse decisions that streaming interaction demands: when to respond, what to say, and how to balance latency against accuracy.
    - **E3:** metadata/paper_statement | Introduction | high
      locator:: Scope and Contributions
      quote:: We focus on the intersection of three areas: streaming/online video understanding with LLMs, RL-based training (RLHF, DPO, GRPO, reward modeling), and the practical infrastructure enabling this research.
    - **E4:** background/paper_statement | Background | medium
      locator:: Section 2.1
      quote:: The core technical challenges of streaming are: Unbounded context management... The when-to-respond decision... Latency-accuracy tradeoff... Causal information constraint.
    - **E5:** method/paper_statement | Taxonomy of Streaming VideoLLM Architectures | medium
      locator:: Section 3 and Table 1
      quote:: We classify streaming VideoLLMs by architecture, as the architectural choice determines what RL methods are feasible and what additional challenges arise.
    - **E6:** gap/paper_statement | Introduction | medium
      locator:: Paragraph on RL-for-VideoLLM space
      quote:: Over 40 papers now apply RL variants—predominantly GRPO—to video understanding tasks... Yet the specific intersection of RL with streaming video understanding remains nascent: only four works... directly address RL in streaming settings.
    - **E7:** prior_work/paper_statement | RL Methods for Video Language Models | medium
      locator:: Section 4.1
      quote:: Video-R1 introduces T-GRPO (Temporal GRPO), which adds temporal awareness to the standard GRPO framework by rewarding correct identification of when events occur.
    - **E8:** prior_work/paper_statement | RL for Temporal Decision-Making in Streaming | medium
      locator:: Section 4.4
      quote:: MMDuet2 applies multi-turn RL with a PAUC (Proactive Area Under the Curve) reward to optimize both response quality and timing in streaming video interaction.
    - **E9:** gap/paper_statement | Training Infrastructure and Data | medium
      locator:: Section 5.1
      quote:: None of these frameworks natively support streaming video RL training... Adapting any current framework for streaming video RL requires: (1) a streaming data loader... (2) KV-cache management... and (3) trajectory-level reward computation.
    - **E10:** gap/paper_statement | Training Infrastructure and Data | medium
      locator:: Section 5.3, Table 5
      quote:: Table 5 catalogs available datasets for video RL training... No streaming-specific RL/preference datasets exist.
    - **E11:** implementation/paper_statement | Training Infrastructure and Data | medium
      locator:: Section 5.2
      quote:: A consistent finding across the literature is that the rollout (generation) phase accounts for 84–91% of total RL training time, making pipeline efficiency—not algorithmic design—the dominant practical concern.
    - **E12:** limitation/paper_statement | Core Challenges | medium
      locator:: Section 6 opening
      quote:: We now analyze five challenges that are unique to RL in streaming settings—not merely harder versions of existing problems, but qualitatively different obstacles that require new solutions.
    - **E13:** gap/paper_statement | Core Challenges | medium
      locator:: Section 6.2
      quote:: No existing reward model captures all three. MMDuet2’s PAUC metric is a start... But PAUC was designed for a narrow setting... and does not generalize to the full range of streaming interactions.
    - **E14:** system_design/paper_statement | Core Challenges | low
      locator:: Section 6.4
      quote:: Streaming video RL is, to our knowledge, the only RL setting that exhibits simultaneous imbalance on both the rollout and training sides—a compounding effect that existing solutions, designed for only one side, cannot resolve.
    - **E15:** other/paper_statement | Roadmap | medium
      locator:: Section 8
      quote:: We organize actionable research directions by feasibility and timeline... Near-Term: Directly Actionable... Medium-Term: Infrastructure Building... Long-Term: Fundamental Research.
