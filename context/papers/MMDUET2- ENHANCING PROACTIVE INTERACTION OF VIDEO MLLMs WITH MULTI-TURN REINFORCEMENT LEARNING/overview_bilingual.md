- **Title:** MMDuet2: Enhancing Proactive Interaction of Video MLLMs with Multi-Turn Reinforcement Learning
  **标题:** MMDuet2：基于多轮强化学习增强视频多模态大语言模型的主动交互
- **Summary:** MMDuet2 turns the question of when a streaming video assistant should speak into an ordinary text action and trains it with multi-turn rewards that favor early correct answers while penalizing spammy repetition.
  **一句话总结:** MMDuet2 将「流式视频助手何时应当开口」这一问题转化为一种普通的文本动作，并用多轮奖励来训练该动作：奖励尽早给出正确回答，惩罚无意义的重复内容。
- **Paper Type:** application
  **论文类型:** 应用
- **Venue:** arXiv preprint 2025
  **发表:** arXiv 预印本 2025
- **Authors:** Yueqian Wang (Wangxuan Institute of Computer Technology, Peking University); Songxiang Liu, Disong Wang, Nuo Xu, Guanglu Wan (Meituan); Huishuai Zhang, Dongyan Zhao (Wangxuan Institute of Computer Technology, Peking University; State Key Laboratory of General Artificial Intelligence)
  **作者:** Yueqian Wang（北京大学王选计算机研究所）；Songxiang Liu、Disong Wang、Nuo Xu、Guanglu Wan（美团）；Huishuai Zhang、Dongyan Zhao（北京大学王选计算机研究所；通用人工智能全国重点实验室）
- **Keywords:** video multimodal large language models, proactive interaction, streaming video question answering, multi-turn reinforcement learning, PAUC, GRPO
  **关键词:** 视频多模态大语言模型、主动交互、流式视频问答、多轮强化学习、PAUC、GRPO
- ## Orientation
    - **Background:** A video multimodal large language model is a chatbot-like model that reads both text and video frames. In streaming use, frames arrive over time, so the model sees only the past and present, not the whole video at once.
      **背景:** 视频多模态大语言模型（Video MLLM）是一种类似聊天机器人的模型，能够同时读取文本和视频帧。在流式应用中，视频帧会随时间不断到达，因此模型只能看到过去和现在的帧，而无法一次性看到整个视频。
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A user asks a question while a video is playing, and the assistant should speak up when the video actually contains something worth answering, rather than waiting for the video to end or interrupting constantly.
      **通俗问题:** 在视频播放过程中用户提出问题，助手应该在视频确实包含值得回答的内容时发声，而不是等到视频结束才回答，也不是频繁打断播放。
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** The right moment to answer is fuzzy: the needed evidence may appear gradually, scene boundaries are coarse, and speaking too early, too late, or too often all feel wrong to a user.
      **为何困难:** 选择回答的正确时机很模糊：所需证据可能逐渐出现，场景边界粗糙，而且回答太早、太晚或太频繁都会让用户感到不适。
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Make silence an explicit text choice, then reward the model for answers that become correct as early as possible without repeating itself.
      **一句话核心思路:** 将静默作为显式的文本选择，然后对模型尽早给出正确答案且不重复自身内容的行为给予奖励。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a video multimodal large language model (Video MLLM) post-training paper about proactive interaction: a video assistant must decide not only what to answer, but whether now is the right moment to speak.
      **阅读价值:** 本文阅读为一篇关于主动交互的视频多模态大语言模型（Video MLLM）后训练论文：视频助手不仅要决定回答什么，还要判断当前是否是开口的合适时机。
      claim_kind:: analyst_assessment
      evidence:: E1, E2
    - **One-Sentence Contribution:** MMDuet2 improves streaming video question answering by making the model choose between answering and emitting NO REPLY at each step, then training that choice with reinforcement learning (RL), meaning learning from scalar rewards rather than only fixed target outputs.
      **一句话贡献:** MMDuet2 让模型在每个步骤选择「回答」或「输出 NO REPLY」，并用强化学习（reinforcement learning，RL）训练该选择，即从数值奖励中学习，而非仅依赖固定的目标输出。
      evidence:: E1, E4, E7
    - **Mental Model:** Picture a tour guide watching a live video with you: every few moments the guide either says something useful about what just happened or deliberately stays quiet, and training rewards the guide for speaking early but not for interrupting with repeats.
      **记忆模型:** 想象一位导游和你一起观看实时视频：每隔几个时刻，这位导游要么对刚才发生的事说出有用的内容，要么刻意保持沉默；训练时会对导游尽早开口给予奖励，而对用重复内容打断则不予奖励。
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is that the RL-trained model improves proactive benchmark scores while the ablations show why anti-repetition and in-span penalties are needed.
      **最佳证据:** 最有力的证据在于，经强化学习训练的模型在主动交互基准上得分有所提升，而消融实验说明了为何需要反重复惩罚和区间内惩罚。
      evidence:: E9, E10, E12
        - Supports C1: ProactiveVideoQA WEB split; baseline MMDuet; Proactive Area Under Curve (PAUC), where higher means earlier and more correct answers, improves from 38.9 to 53.3 and duplicate proportion drops from 81.3 to 4.2; supported, with no variance reported.
          支持 C1：数据集为 ProactiveVideoQA 的 WEB 划分；基线模型为 MMDuet；主动曲线下面积（Proactive Area Under Curve，PAUC）从 38.9 提升到 53.3，该指标越高表示回答越早且越准确；重复比例从 81.3 降至 4.2；结论得到支持，但未报告方差。
          evidence:: E9
        - Supports C1: StreamingBench proactive output task; baseline MMDuet; accuracy improves from 29.44 to 34.69; supported, with evaluation repeat count not reported.
          支持 C1：任务为 StreamingBench 的主动输出任务；基线模型为 MMDuet；准确率从 29.44 提升到 34.69；结论得到支持，但未报告评估重复次数。
          evidence:: E10
        - Supports C3: reward ablation on WEB and EGO; baseline full MMDuet2 reward; removing the repetition reward raises duplicate proportion from 4.2 to 17.3 on WEB and from 8.1 to 31.9 on EGO; supported, but statistical uncertainty is not reported.
          支持 C3：在 WEB 和 EGO 上进行奖励消融实验；基线为完整的 MMDuet2 奖励；移除重复奖励后，WEB 上的重复比例从 4.2 升至 17.3，EGO 上的重复比例从 8.1 升至 31.9；结论得到支持，但未报告统计不确定性。
          evidence:: E12
    - **Main Caveat:** The results are promising but thin on robustness: tables report point estimates without error bars, the LLM-judge details for reward scoring are under-specified, and the model still struggles on surveillance-style and long egocentric videos.
      **主要边界:** 结果很有前景，但在鲁棒性方面证据不足：表格仅报告点估计而未提供误差线；用于奖励打分的 LLM 评判器细节说明不足；模型在监控类和长第一人称视角视频上仍然存在困难。
      claim_kind:: analyst_assessment
      evidence:: E9, E14
- ## Argument Map
    - **Problem and Stakes:** The paper studies proactive interaction, where a video multimodal large language model (Video MLLM) watches an incoming visual stream and decides when to speak as well as what to say. The stake is real-time assistance: live analysis, surveillance, egocentric helpers, and social agents need timely responses rather than end-of-video answers.
      **问题与重要性:** 本文研究主动交互：视频多模态大语言模型（Video MLLM）观察输入的视觉流，并决定何时发言以及说什么。其核心价值在于实时辅助：实时分析、监控、第一人称助手和社交智能体都需要及时的响应，而不是等到视频结束才给出答案。
      evidence:: E1, E2
    - **Prior Gap:** Prior proactive Video MLLMs usually made timing decisions with a predicted score and a manually chosen threshold, while supervised training needed exact reply timestamps that are expensive and ambiguous to annotate. The paper also positions existing reinforcement learning (RL) for video-language models as mostly not addressing real-time multi-turn interaction.
      **已有方法缺口:** 以往的视频多模态大语言模型通常通过预测分数和人工设定的阈值来决定时机，而监督微调（SFT）需要精确的回复时间戳，这类标注成本高且存在歧义。本文还指出，现有的视频语言模型强化学习（RL）方法大多未解决实时多轮交互问题。
      evidence:: E2, E6, E17
    - **Key Insight:** The paper’s central insight is to recast the hidden timing decision as a visible dialogue action, NO REPLY, and train multi-turn rollouts with a reward shaped like an area under a correctness-over-time curve. This avoids needing a single annotated best timestamp while still preferring earlier correct responses.
      **关键洞见:** 该论文的核心洞见是把隐含的时机决策重新转化为可见的对话动作「不回复」（NO REPLY），并使用形如正确率随时间变化的曲线下面积的奖励来训练多轮推演。这避免了需要标注单一最佳时间戳的问题，同时仍然偏好较早的正确回复。
      evidence:: E4, E6, E7
    - **Claims:** The paper makes four main falsifiable claims about proactive performance, the value of RL, reward-design necessity, and preservation of ordinary offline video understanding.
      **核心主张:** 该论文提出了四个关于主动交互性能、强化学习（RL）的价值、奖励设计必要性以及保留普通离线视频理解能力的可证伪主张。
      evidence:: E1, E9, E11
        - C1: MMDuet2_rl improves proactive video interaction quality over open proactive baselines on the reported benchmark suite, especially on WEB, TV, VAD, and StreamingBench, while reducing duplicate replies compared with MMDuet; the EGO PAUC comparison is mixed because MMDuet has higher PAUC but extreme duplication.
          C1：在所报告的基准测试套件上，MMDuet2_rl 相比开放的主动基线提升了主动视频交互质量，尤其是在 WEB、TV、VAD 和 StreamingBench 上，同时与 MMDuet 相比减少了重复回复；EGO 数据集上的主动交互曲线下面积（Proactive Area Under Curve，PAUC）比较结果好坏参半，因为 MMDuet 具有更高的 PAUC 但存在极端重复。
          evidence:: E9, E10
        - C2: Multi-turn RL after supervised fine-tuning (SFT), meaning training first on target examples and then from rewards, improves the SFT-only model’s proactive timing and answer behavior.
          C2：在监督微调（supervised fine-tuning，SFT）之后进行多轮强化学习（RL）——即先在目标示例上训练，再根据奖励训练——能提升仅经过监督微调的模型的主动时机把握和回答行为。
          evidence:: E9, E10, E14
        - C3: The auxiliary repetition, in-span, and prefix penalties are necessary to prevent the PAUC-style reward from being exploited by redundant or irrelevant responses.
          C3：辅助的重复惩罚、区间内惩罚和前缀惩罚是必要的，它们能防止类似 PAUC 的奖励被冗余或无关的回复所利用。
          evidence:: E7, E12
        - C4: The proactive post-training procedure mostly preserves offline video understanding performance relative to the authors’ Qwen2.5-VL 3B implementation baseline.
          C4：相对于作者的 Qwen2.5-VL 3B 实现基线，主动后训练流程基本保留了离线视频理解的性能。
          evidence:: E11
- ## Mechanism and Design
    - **Core Mechanism:** At each user turn, the model receives a small number of video frames and optional text, then the assistant must either generate an answer or emit NO REPLY as a normal text output. RL uses Proactive Area Under Curve (PAUC), a metric that rewards high answer correctness earlier within a valid reply span, plus penalties for repeated, out-of-span, and prefix-copying replies.
      **核心机制:** 在每一轮用户交互中，模型接收少量视频帧和可选文本，随后助手必须生成回答，或者将「不回复」（NO REPLY）作为普通文本输出发出。强化学习使用主动交互曲线下面积（Proactive Area Under Curve，PAUC），这是一种在有效回复时间区间内对较早的高正确率回答给予奖励的指标，同时附加对重复回复、超出区间回复以及复制前缀回复的惩罚。
      evidence:: E4, E7
    - **Data / Control Flow:** The data pipeline segments videos into scenes, captions scenes, uses a language model to generate questions and per-scene answers, and converts these into either one-question-many-answer or multi-question-many-answer proactive dialogues. Training then runs SFT with answers placed at the end of their spans, followed by short-span Group Relative Policy Optimization (GRPO), an RL method that compares multiple sampled outputs for the same prompt.
      **数据/控制流:** 数据流水线将视频分割为场景，为场景生成字幕，使用语言模型生成问题和每个场景对应的答案，并将这些转换为单问题多答案或多问题多答案的主动对话。随后训练执行监督微调（SFT），将答案放置在其时间区间的末尾，接着进行短区间的群组相对策略优化（Group Relative Policy Optimization，GRPO），这是一种强化学习方法，会对同一提示采样的多个输出进行比较。
      evidence:: E3, E5, E8
    - **Design Decisions:** The design favors compatibility and reward shaping over architectural specialization: it uses ordinary chat messages for timing decisions, then compensates for the resulting tendency to over-speak with explicit reward penalties.
      **设计决策:** 该设计倾向于兼容性和奖励塑形，而非架构特化：它使用普通的聊天消息来进行时机决策，然后通过显式的奖励惩罚来补偿由此产生的过度发言倾向。
      claim_kind:: analyst_assessment
      evidence:: E4, E7, E12
        - Need: avoid threshold tuning and framework changes; choice: represent waiting as NO REPLY in the assistant stream; closest alternative: special timing modules or token-level stop/continue rules; tradeoff: more generate calls and extra context tokens.
          需求：避免阈值调节和框架更改；选择：在助手输出流中将等待表示为「不回复」（NO REPLY）；最接近的替代方案：特殊的时机模块或令牌级别的停止/继续规则；权衡：更多的生成调用和额外的上下文令牌。
          evidence:: E2, E4, E16
        - Need: build training targets without exact reply timestamps; choice: place SFT answers at the end of coarse reply timespans; tradeoff: avoids asking the model to answer before evidence appears but teaches late replies that RL must later correct.
          需求：在缺少精确回复时间戳的情况下构建训练目标。选择：将监督微调（supervised fine-tuning，SFT）的回答放在粗粒度回复时间段的末尾。权衡：这样避免要求模型在证据出现之前就回答，但会教会模型延迟回复，这一倾向需要在后续强化学习（reinforcement learning，RL）阶段加以纠正。
          evidence:: E5, E6
        - Need: reward early useful speech without incentivizing spam; choice: weight PAUC slightly more than repetition, in-span, and prefix penalties; tradeoff: too little penalty yields redundant high-PAUC behavior, while too much penalty can suppress useful replies.
          需求：在不鼓励垃圾发言的前提下奖励早期有用发言。选择：让 PAUC（一种在回复区间内随时间累积答案正确性的指标）的权重略高于重复惩罚、区间外惩罚和前缀惩罚。权衡：惩罚太少会产生高 PAUC 但冗余的行为；惩罚太多则可能抑制有用回复。
          evidence:: E7, E12
    - **Implementation Surface:** The model initializes from Qwen2.5-VL 3B, uses two-second frame sampling with two frames per user turn in training, and runs RL with four GRPO rollouts on short video spans using SGLang and verl. Reported resource use is 16 H800 GPUs for about 8 hours for SFT and 8 H800 GPUs for about 20 hours for RL.
      **实现边界:** 实现细节
      evidence:: E5, E8
- ## Evaluation and Evidence
    - **Setup:** The proactive evaluation covers ProactiveVideoQA splits WEB, EGO, TV, and VAD using PAUC and duplicate proportion, plus the StreamingBench proactive output task using accuracy. Offline retention is checked on Video-MME, MVBench, and LongVideoBench, with proactive baselines limited partly by availability of open inference code.
      **实验设置:** 评测设置
      evidence:: E9, E10, E11
    - **Claim-Evidence Matrix:** The evidence supports the main direction of the paper, but the strength varies by claim because results are single reported point estimates and some comparisons are complicated by duplicate-heavy baselines.
      **主张-证据矩阵:** 证据总体支持论文的主要方向，但支持力度因声明而异：结果均为单点估计，且部分对比因基线方法重复输出严重而变得复杂。
      claim_kind:: analyst_assessment
      evidence:: E9, E10, E12
        - C1: Supported on WEB, TV, VAD, and StreamingBench; partially supported on EGO because MMDuet2_rl has far lower duplicate proportion but lower PAUC than MMDuet.
          C1：在 WEB、TV、VAD 和 StreamingBench 上得到支持；在 EGO 上部分支持，因为 MMDuet2_rl 的重复比例远低于 MMDuet，但 PAUC 也更低。
          claim_kind:: analyst_assessment
          evidence:: E9, E10
        - C2: Supported by MMDuet2_rl outperforming MMDuet2_sft on ProactiveVideoQA splits and StreamingBench, and by training dynamics showing a move from low-frequency replies to higher PAUC behavior.
          C2：MMDuet2_rl 在 ProactiveVideoQA 各划分及 StreamingBench 上优于 MMDuet2_sft，且训练动态显示模型从低频回复逐步转向更高 PAUC 的行为，均支持该声明。
          evidence:: E9, E10, E14
        - C3: Strongly supported qualitatively by ablations where removing r_rep or r_in_span increases duplicate or uncontrolled response density, including EGO failure without r_in_span.
          C3：消融实验从定性上强烈支持该声明——移除重复惩罚（r_rep）或区间外惩罚（r_in_span）会导致重复或不受控的回复密度增加，其中在 EGO 上若缺少 r_in_span 则出现失败。
          evidence:: E12
        - C4: Supported by near-baseline offline benchmark numbers, though the comparison is to the authors’ reproduced Qwen2.5-VL 3B rather than only the original reported checkpoint.
          C4：离线基准成绩接近基线，支持该声明；不过对比对象是作者复现的 Qwen2.5-VL 3B，而非仅原始发布的检查点。
          evidence:: E11
    - **Headline Results:** The headline result is not a clean universal win on every metric, but a practical improvement in earlier useful responses with dramatically less duplication than MMDuet on several splits.
      **关键结果:** 核心结果
      claim_kind:: analyst_assessment
      evidence:: E9, E10, E11
        - ProactiveVideoQA WEB: MMDuet2_rl versus MMDuet improves PAUC from 38.9 to 53.3 and reduces duplicate proportion from 81.3 to 4.2; no confidence intervals or repeat counts are reported.
          ProactiveVideoQA WEB 上的结果：MMDuet2_rl 相比 MMDuet 将 PAUC 从 38.9 提升到 53.3，并将重复回复比例从 81.3 降至 4.2；论文未报告置信区间或重复实验次数。
          evidence:: E9
        - StreamingBench proactive output: MMDuet2_rl reaches 34.69 accuracy versus 29.44 for MMDuet, 25.34 for Dispider, and 1.96 for VideoLLM-Online; support is point-estimate only.
          StreamingBench 的主动输出结果：MMDuet2_rl 达到 34.69 的准确率，而 MMDuet 为 29.44，Dispider 为 25.34，VideoLLM-Online 为 1.96；仅有单点估计，未报告不确定性。
          evidence:: E10
        - Offline benchmarks: relative to the authors’ Qwen2.5-VL 3B reproduction, MMDuet2_rl is similar on Video-MME, MVBench, and LongVideoBench, with LongVideoBench moving from 53.1 to 52.7.
          离线基准测试结果：相对于作者复现的 Qwen2.5-VL 3B 基线，MMDuet2_rl 在 Video-MME、MVBench 和 LongVideoBench 上表现相近，其中 LongVideoBench 从 53.1 变为 52.7。
          evidence:: E11
    - **Ablations and Sensitivity:** The ablations show the reward is doing real control work: removing anti-repetition or in-span rewards can raise PAUC while making outputs much worse as interactions. Frame-rate sensitivity is also important: dense SFT sampling collapses to NO REPLY, while denser inference improves timing because the model gets more chances to decide.
      **消融与敏感性:** 消融实验表明奖励确实在起控制作用：去掉反重复奖励或跨时间跨度奖励可以提高 PAUC，但会使输出作为交互内容而言质量大幅下降。帧率敏感性也很重要：密集的监督微调（supervised fine-tuning，SFT）采样会退化为输出「NO REPLY」，而更密集的推理采样能改善时机，因为模型有更多机会做出决定。
      evidence:: E12, E13
    - **Reproducibility Gaps:** The paper provides a project homepage, model/training framework names, hardware, and many hyperparameters, but does not report statistical uncertainty, repeat counts, the exact LLM judge identity and prompts for reward scoring, or full dataset release details in the supplied text.
      **可复现性缺口:** 论文提供了项目主页、模型与训练框架名称、硬件配置和许多超参数，但在所提供的文本中未报告统计不确定性、重复实验次数、用于奖励评分的具体大语言模型裁判身份与提示词，也未给出完整数据集发布的细节。
      claim_kind:: analyst_assessment
      evidence:: E1, E7, E8
- ## Technical Judgment
    - **What Holds Up:** The paper’s strongest technical move is aligning the training signal with the real interaction tradeoff: a reply is better if it is correct and arrives earlier, but only if it is not redundant or irrelevant. The reward ablations make the main failure mode visible, showing that PAUC alone can be gamed by over-answering.
      **站得住的结论:** 论文最强的技术亮点在于将训练信号与真实交互中的权衡对齐：一条回复如果正确且更早到达则更好，但前提是它不冗余也不跑题。奖励消融实验使主要失败模式清晰可见，表明仅靠 PAUC 可以通过过度回答来刷分。
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E12
    - **Where It May Fail:** MMDuet2 may be less reliable on long or hard-to-interpret streams: the paper reports poor VAD performance for all models and increasing repetition on longer EGO videos late in RL training. The NO REPLY-as-generation design is easy to implement but less token-efficient than the appendix’s proposed stop/continue format.
      **可能失效之处:** MMDuet2 在长视频或难以解读的视频流上可能不太可靠：论文报告所有模型的 VAD 表现较差，且在强化学习训练后期，EGO 长视频上的重复现象有所增加。将「NO REPLY」作为生成输出的设计虽然易于实现，但在 token 效率上不如附录中提出的停止/继续格式。
      claim_kind:: analyst_assessment
      evidence:: E9, E14, E16
    - **Relation to Other Work:** Compared with threshold-based proactive systems such as VideoLLM-Online and MMDuet, MMDuet2 moves timing into the language-model action space instead of tuning an external response score. Compared with recent RL-enhanced video-language models, its distinguishing axis is multi-turn real-time interaction rather than static video reasoning alone.
      **与已有工作的关系:** 与基于阈值的主动式系统（如 VideoLLM-Online 和 MMDuet）相比，MMDuet2 将时机判断纳入语言模型的动作空间，而非调优一个外部的响应分数。与近期经强强化学习增强的视频多模态大语言模型相比，其区别在于多轮实时交互，而非仅做静态视频推理。
      evidence:: E2, E17
    - **Transferable Lesson:** A useful systems pattern is to turn an awkward control decision into an ordinary model output when ecosystem compatibility matters, then add reward terms for the predictable degenerate behaviors that this output space enables. Here, silence-as-text made proactive timing trainable in standard chat infrastructure, but required explicit anti-spam rewards.
      **可迁移启发:** 一个有启发性的系统设计模式是：当生态系统兼容性更重要时，把一个难以处理的控制决策转化为普通的模型输出，然后针对该输出空间可能出现的可预见退化行为添加奖励项。在这里，将沉默作为文本输出使得主动时机判断能在标准对话基础设施中训练，但需要显式的反刷屏奖励。
      claim_kind:: analyst_assessment
      evidence:: E4, E7, E12
- ## Glossary
  collapsed:: true
    - video multimodal large language model: A language model that conditions on video frames as well as text, so it can answer questions or converse about video content.
      视频多模态大语言模型：一种以视频帧和文本为条件的语言模型，因此能够回答关于视频内容的问题或进行对话。
    - proactive interaction: A streaming setting where the model decides when to respond during video playback, not only how to answer after a user turn.
      主动交互：一种流式设定，模型在视频播放过程中自行决定何时做出回应，而不仅仅是在用户一轮发言结束后决定如何回答。
    - supervised fine-tuning: Training a pretrained model on examples with target outputs; in this paper it teaches the chat format and initial proactive behavior before reward training.
      监督微调（Supervised Fine-Tuning，SFT）：在带有目标输出的示例上训练预训练模型；本文中它在奖励训练之前教会模型聊天格式和初始的主动行为。
    - reinforcement learning: Training from scalar rewards assigned to generated behavior rather than only from fixed target text; here it rewards early correct replies and penalizes bad speaking patterns.
      强化学习（Reinforcement Learning，RL）：根据赋予生成行为的标量奖励进行训练，而非仅依赖固定的目标文本；本文中它对尽早给出正确回复的行为给予奖励，并对不良说话模式予以惩罚。
    - Group Relative Policy Optimization: An RL optimization method that samples multiple outputs for the same input and updates the model using their relative rewards.
      组相对策略优化（Group Relative Policy Optimization，GRPO）：一种强化学习优化方法，对同一输入采样多个输出，并利用这些输出之间的相对奖励来更新模型。
    - Proactive Area Under Curve: A proactive-video metric and reward shape that integrates answer correctness over time within a reply span, so earlier high-quality replies score better.
      主动曲线下面积（Proactive Area Under Curve，PAUC）：一种面向主动视频的评估指标兼奖励函数形式，它在回复区间内对回答正确性随时间积分，使得越早给出高质量回复得分越高。
    - reply timespan: The interval in the video during which a certain ground-truth answer is considered appropriate; the paper avoids requiring a single exact timestamp inside it.
      回复时间区间：视频中某条标准答案被视为恰当回答的时间段；本文不要求在该时间段内指定唯一精确的时间戳。
    - NO REPLY: The literal text output used by MMDuet2 when the assistant chooses not to answer at the current turn.
      「NO REPLY」：MMDuet2 在助手选择当前轮次不回答时使用的字面文本输出。
    - proactive dialogue types: 1QnA means one question with multiple possible answer turns across a video; nQnA means multiple questions and multiple answer streams in one dialogue.
      主动对话类型：1QnA 指一个问题在整段视频中可以有多个回答轮次；nQnA 指一次对话中包含多个问题和多条回答流。
    - auxiliary reward penalties: Extra reward terms that discourage duplicate replies, replies outside valid spans, and replies that copy a previous prefix before adding new content.
      辅助奖励惩罚：额外的奖励项，用于抑制重复回复、在有效区间之外的回复，以及在添加新内容之前照抄先前前缀的回复。
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/paper_statement | Abstract | high
      locator:: Abstract
      quote:: We train our model MMDuet2 on a dataset of 52k videos with two types of dialogues via SFT and RL. Experimental results demonstrate that MMDuet2 outperforms existing proactive Video MLLM baselines in response timing and quality, achieving state-of-the-art performance on the ProactiveVideoQA benchmark.
    - **E2:** gap/paper_statement | Introduction | high
      locator:: Section 1, prior methods and issues
      quote:: In previous works of proactive interaction... a video MLLM determines whether it should respond after a certain frame by predicting response probability scores... and compares the scores with a pre-defined threshold. However... A threshold must be manually set during inference, and the model may never reply or often reply with duplicated content if this threshold is not set properly.
    - **E3:** method/paper_statement | Dataset Construction | high
      locator:: Section 3 and Table 1
      quote:: The videos of our proposed dataset contain two major categories: web videos and ego-centric videos... Web Videos 50228... Ego Centic 2543... We prepare 2 different types of proactive dialogues: “one question, multiple answers” (1QnA) and “multiple questions, multiple answers” (nQnA), each type covers half the number of all videos.
    - **E4:** system_design/implementation_detail | Formulating Proactive Dialogue with Chat Template | high
      locator:: Section 4.1 and Figure 2
      quote:: The assistant can choose to output either a textual response or “NO REPLY” to indicate it does not want to reply right after this frame... a major advantage of the chat template used in MMDuet2 is that it formats the entire interaction process... into messages from the user or the assistant and is therefore compatible with almost all popular post-training and inference frameworks.
    - **E5:** implementation/implementation_detail | Supervised Fine-Tuning | high
      locator:: Section 4.2
      quote:: We use Qwen2.5-VL 3B... as initialization... The input frames are sampled at an interval of 2 seconds from the video and we use 128 tokens per frame, 2 frames per user turn. To build user-assistant conversations used in the SFT stage, we place model answers at the end of their reply timespans.
    - **E6:** insight/paper_statement | Motivation of Using RL | high
      locator:: Section 4.3.1
      quote:: Automatically annotating ground-truth response time has been an unsolved challenge... Although providing accurate ground truth reply times is difficult, it is much easier to determine which of the two given proactive interaction outputs is better. An ideal proactive interaction system should generate replies both correctly... and early.
    - **E7:** algorithm/implementation_detail | Reward Modeling | high
      locator:: Section 4.3.2
      quote:: The reward is inspired by the PAUC (Proactive Area Under Curve)... we made two minor modifications... Besides r_PAUC, we also use some additional reward to punish unwanted behaviors... Replication reward... In-span reward... Prefix reward... After some hyperparameter search we find that omega_PAUC = 3, omega_rep = 2, omega_in_span = 0.5, omega_pfx = 2 is good.
    - **E8:** implementation/implementation_detail | Training Details | high
      locator:: Section 4.3.3
      quote:: To alleviate this problem, in each step we only select a short span (from 20 to 60 seconds) from the video for training and provide ground truth model replies for the dialogue turns that happen before the selected span... We use GRPO... with a number of rollouts as 4, implemented with SGLang... and verl... conducted on 8 H800 GPUs and takes about 20 hours.
    - **E9:** result/experiment_result | Experiments on Proactive Benchmarks | medium
      locator:: Table 2 and surrounding text
      quote:: Table 2: Performance on ProactiveVideoQA. Metrics reported are PAUC (omega = 0.5) up / reply duplicate proportion down... MMDuet2_rl (Ours): WEB 53.3 / 4.2, EGO 33.6 / 8.1, TV 43.4 / 1.0, VAD 28.9 / 15.2... Results show that MMDuet2 outperforms existing proactive interaction models by a large margin.
    - **E10:** result/experiment_result | Experiments on Proactive Benchmarks | medium
      locator:: Table 5
      quote:: Table 5: Performance on Proactive Output task of Streaming-Bench. VideoLLM-Online 1.96; Dispider 25.34; MMDuet 29.44; MMDuet2_sft (Ours) 19.59; MMDuet2_rl (Ours) 34.69.
    - **E11:** result/experiment_result | Experiments on Offline Video-Text Benchmarks | medium
      locator:: Section 5.2 and Table 4
      quote:: After fine-tuning and reinforcement learning for enhancing proactive interaction, MMDuet2’s performance on offline video understanding benchmarks remains almost the same as the checkpoint before our post-training... Table 4... Qwen2.5-VL 3B dagger 66.5/57.3, 65.6, 53.1; MMDuet2_rl dagger 67.5/58.1, 66.4, 52.7.
    - **E12:** ablation/ablation | Ablation Studies | medium
      locator:: Section 5.3 and Table 6
      quote:: Results show that r_rep and r_in_span are indispensable: without any of these 2 rewards, the model generates more duplicated responses to achieve an unreasonably high PAUC metric... Table 6... MMDuet2 53.3/4.2/3.3 on WEB; -r_rep 55.5/17.3/4.9; -r_in_span 62.7/9.6/8.4; EGO -r_in_span FAIL.
    - **E13:** ablation/ablation | Ablation Studies | medium
      locator:: Section 5.3 and Table 7
      quote:: In SFT phase, when frame interval is set to 1 second, the model will collapse to always generating “NO REPLY”... In the RL phase, we found that setting different frame intervals does not have a significant impact... in the inference phase... reducing the frame interval from 2 seconds to 1 second leads to a significant performance improvement.
    - **E14:** limitation/paper_statement | Training Dynamics of the RL Process | medium
      locator:: Section 5.4 and Figure 5
      quote:: Stage 3... the model's performance on the [WEB] network video task stabilizes. However, on the [EGO] ego-centric video task which is longer and more challenging for content understanding, the model can have some generalization issues as we observe an increase in repetition.
    - **E15:** result/experiment_result | Experiments on Proactive Benchmarks | medium
      locator:: Inference Speed paragraph and Table 3
      quote:: Inference Speed. Here we report the actual inference speed... select 64 samples from the ProactiveVideoQA [WEB] task and test the inference wall time... Table 3... MMDuet 5.7 (3.4) reply turns, 2m27s; MMDuet2 3.3 (1.9), 2m52s.
    - **E16:** limitation/paper_statement | Appendix A: Discussion of Reply Timing Decision Methods | high
      locator:: Appendix A
      quote:: Here we describe a more efficient implementation of reply timing instead of generating “NO REPLY”... if the model chooses not to respond, no additional token will be added to the context... However, this requires introducing new rules into inference frameworks like SGLang or vLLM, which requires significant labor.
    - **E17:** prior_work/paper_statement | Related Works | high
      locator:: Section 2.2
      quote:: Reinforcement learning has begun to play a transformative role in post-training video-text multimodal language models... However, existing RL-enhanced VideoMLLMs have not explored real-time interaction or multi-turn dialogue, limiting their applicability in more interactive scenarios.
