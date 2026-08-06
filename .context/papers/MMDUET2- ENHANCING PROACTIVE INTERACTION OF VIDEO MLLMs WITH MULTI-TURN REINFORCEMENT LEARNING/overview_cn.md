- **标题:** MMDuet2：基于多轮强化学习增强视频多模态大语言模型的主动交互
- **一句话总结:** MMDuet2 将「流式视频助手何时应当开口」这一问题转化为一种普通的文本动作，并用多轮奖励来训练该动作：奖励尽早给出正确回答，惩罚无意义的重复内容。
- **论文类型:** 应用
- **发表:** arXiv 预印本 2025
- **作者:** Yueqian Wang（北京大学王选计算机研究所）；Songxiang Liu、Disong Wang、Nuo Xu、Guanglu Wan（美团）；Huishuai Zhang、Dongyan Zhao（北京大学王选计算机研究所；通用人工智能全国重点实验室）
- **关键词:** 视频多模态大语言模型、主动交互、流式视频问答、多轮强化学习、PAUC、GRPO
- ## Orientation
    - **背景:** 视频多模态大语言模型（Video MLLM）是一种类似聊天机器人的模型，能够同时读取文本和视频帧。在流式应用中，视频帧会随时间不断到达，因此模型只能看到过去和现在的帧，而无法一次性看到整个视频。
      claim_kind:: analyst_assessment
    - **通俗问题:** 在视频播放过程中用户提出问题，助手应该在视频确实包含值得回答的内容时发声，而不是等到视频结束才回答，也不是频繁打断播放。
      claim_kind:: analyst_assessment
    - **为何困难:** 选择回答的正确时机很模糊：所需证据可能逐渐出现，场景边界粗糙，而且回答太早、太晚或太频繁都会让用户感到不适。
      claim_kind:: analyst_assessment
    - **一句话核心思路:** 将静默作为显式的文本选择，然后对模型尽早给出正确答案且不重复自身内容的行为给予奖励。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **阅读价值:** 本文阅读为一篇关于主动交互的视频多模态大语言模型（Video MLLM）后训练论文：视频助手不仅要决定回答什么，还要判断当前是否是开口的合适时机。
      claim_kind:: analyst_assessment
      evidence:: E1, E2
    - **一句话贡献:** MMDuet2 让模型在每个步骤选择「回答」或「输出 NO REPLY」，并用强化学习（reinforcement learning，RL）训练该选择，即从数值奖励中学习，而非仅依赖固定的目标输出。
      evidence:: E1, E4, E7
    - **记忆模型:** 想象一位导游和你一起观看实时视频：每隔几个时刻，这位导游要么对刚才发生的事说出有用的内容，要么刻意保持沉默；训练时会对导游尽早开口给予奖励，而对用重复内容打断则不予奖励。
      claim_kind:: analyst_assessment
    - **最佳证据:** 最有力的证据在于，经强化学习训练的模型在主动交互基准上得分有所提升，而消融实验说明了为何需要反重复惩罚和区间内惩罚。
      evidence:: E9, E10, E12
        - 支持 C1：数据集为 ProactiveVideoQA 的 WEB 划分；基线模型为 MMDuet；主动曲线下面积（Proactive Area Under Curve，PAUC）从 38.9 提升到 53.3，该指标越高表示回答越早且越准确；重复比例从 81.3 降至 4.2；结论得到支持，但未报告方差。
          evidence:: E9
        - 支持 C1：任务为 StreamingBench 的主动输出任务；基线模型为 MMDuet；准确率从 29.44 提升到 34.69；结论得到支持，但未报告评估重复次数。
          evidence:: E10
        - 支持 C3：在 WEB 和 EGO 上进行奖励消融实验；基线为完整的 MMDuet2 奖励；移除重复奖励后，WEB 上的重复比例从 4.2 升至 17.3，EGO 上的重复比例从 8.1 升至 31.9；结论得到支持，但未报告统计不确定性。
          evidence:: E12
    - **主要边界:** 结果很有前景，但在鲁棒性方面证据不足：表格仅报告点估计而未提供误差线；用于奖励打分的 LLM 评判器细节说明不足；模型在监控类和长第一人称视角视频上仍然存在困难。
      claim_kind:: analyst_assessment
      evidence:: E9, E14
- ## Argument Map
    - **问题与重要性:** 本文研究主动交互：视频多模态大语言模型（Video MLLM）观察输入的视觉流，并决定何时发言以及说什么。其核心价值在于实时辅助：实时分析、监控、第一人称助手和社交智能体都需要及时的响应，而不是等到视频结束才给出答案。
      evidence:: E1, E2
    - **已有方法缺口:** 以往的视频多模态大语言模型通常通过预测分数和人工设定的阈值来决定时机，而监督微调（SFT）需要精确的回复时间戳，这类标注成本高且存在歧义。本文还指出，现有的视频语言模型强化学习（RL）方法大多未解决实时多轮交互问题。
      evidence:: E2, E6, E17
    - **关键洞见:** 该论文的核心洞见是把隐含的时机决策重新转化为可见的对话动作「不回复」（NO REPLY），并使用形如正确率随时间变化的曲线下面积的奖励来训练多轮推演。这避免了需要标注单一最佳时间戳的问题，同时仍然偏好较早的正确回复。
      evidence:: E4, E6, E7
    - **核心主张:** 该论文提出了四个关于主动交互性能、强化学习（RL）的价值、奖励设计必要性以及保留普通离线视频理解能力的可证伪主张。
      evidence:: E1, E9, E11
        - C1：在所报告的基准测试套件上，MMDuet2_rl 相比开放的主动基线提升了主动视频交互质量，尤其是在 WEB、TV、VAD 和 StreamingBench 上，同时与 MMDuet 相比减少了重复回复；EGO 数据集上的主动交互曲线下面积（Proactive Area Under Curve，PAUC）比较结果好坏参半，因为 MMDuet 具有更高的 PAUC 但存在极端重复。
          evidence:: E9, E10
        - C2：在监督微调（supervised fine-tuning，SFT）之后进行多轮强化学习（RL）——即先在目标示例上训练，再根据奖励训练——能提升仅经过监督微调的模型的主动时机把握和回答行为。
          evidence:: E9, E10, E14
        - C3：辅助的重复惩罚、区间内惩罚和前缀惩罚是必要的，它们能防止类似 PAUC 的奖励被冗余或无关的回复所利用。
          evidence:: E7, E12
        - C4：相对于作者的 Qwen2.5-VL 3B 实现基线，主动后训练流程基本保留了离线视频理解的性能。
          evidence:: E11
- ## Mechanism and Design
    - **核心机制:** 在每一轮用户交互中，模型接收少量视频帧和可选文本，随后助手必须生成回答，或者将「不回复」（NO REPLY）作为普通文本输出发出。强化学习使用主动交互曲线下面积（Proactive Area Under Curve，PAUC），这是一种在有效回复时间区间内对较早的高正确率回答给予奖励的指标，同时附加对重复回复、超出区间回复以及复制前缀回复的惩罚。
      evidence:: E4, E7
    - **数据/控制流:** 数据流水线将视频分割为场景，为场景生成字幕，使用语言模型生成问题和每个场景对应的答案，并将这些转换为单问题多答案或多问题多答案的主动对话。随后训练执行监督微调（SFT），将答案放置在其时间区间的末尾，接着进行短区间的群组相对策略优化（Group Relative Policy Optimization，GRPO），这是一种强化学习方法，会对同一提示采样的多个输出进行比较。
      evidence:: E3, E5, E8
    - **设计决策:** 该设计倾向于兼容性和奖励塑形，而非架构特化：它使用普通的聊天消息来进行时机决策，然后通过显式的奖励惩罚来补偿由此产生的过度发言倾向。
      claim_kind:: analyst_assessment
      evidence:: E4, E7, E12
        - 需求：避免阈值调节和框架更改；选择：在助手输出流中将等待表示为「不回复」（NO REPLY）；最接近的替代方案：特殊的时机模块或令牌级别的停止/继续规则；权衡：更多的生成调用和额外的上下文令牌。
          evidence:: E2, E4, E16
        - 需求：在缺少精确回复时间戳的情况下构建训练目标。选择：将监督微调（supervised fine-tuning，SFT）的回答放在粗粒度回复时间段的末尾。权衡：这样避免要求模型在证据出现之前就回答，但会教会模型延迟回复，这一倾向需要在后续强化学习（reinforcement learning，RL）阶段加以纠正。
          evidence:: E5, E6
        - 需求：在不鼓励垃圾发言的前提下奖励早期有用发言。选择：让 PAUC（一种在回复区间内随时间累积答案正确性的指标）的权重略高于重复惩罚、区间外惩罚和前缀惩罚。权衡：惩罚太少会产生高 PAUC 但冗余的行为；惩罚太多则可能抑制有用回复。
          evidence:: E7, E12
    - **实现边界:** 实现细节
      evidence:: E5, E8
- ## Evaluation and Evidence
    - **实验设置:** 评测设置
      evidence:: E9, E10, E11
    - **主张-证据矩阵:** 证据总体支持论文的主要方向，但支持力度因声明而异：结果均为单点估计，且部分对比因基线方法重复输出严重而变得复杂。
      claim_kind:: analyst_assessment
      evidence:: E9, E10, E12
        - C1：在 WEB、TV、VAD 和 StreamingBench 上得到支持；在 EGO 上部分支持，因为 MMDuet2_rl 的重复比例远低于 MMDuet，但 PAUC 也更低。
          claim_kind:: analyst_assessment
          evidence:: E9, E10
        - C2：MMDuet2_rl 在 ProactiveVideoQA 各划分及 StreamingBench 上优于 MMDuet2_sft，且训练动态显示模型从低频回复逐步转向更高 PAUC 的行为，均支持该声明。
          evidence:: E9, E10, E14
        - C3：消融实验从定性上强烈支持该声明——移除重复惩罚（r_rep）或区间外惩罚（r_in_span）会导致重复或不受控的回复密度增加，其中在 EGO 上若缺少 r_in_span 则出现失败。
          evidence:: E12
        - C4：离线基准成绩接近基线，支持该声明；不过对比对象是作者复现的 Qwen2.5-VL 3B，而非仅原始发布的检查点。
          evidence:: E11
    - **关键结果:** 核心结果
      claim_kind:: analyst_assessment
      evidence:: E9, E10, E11
        - ProactiveVideoQA WEB 上的结果：MMDuet2_rl 相比 MMDuet 将 PAUC 从 38.9 提升到 53.3，并将重复回复比例从 81.3 降至 4.2；论文未报告置信区间或重复实验次数。
          evidence:: E9
        - StreamingBench 的主动输出结果：MMDuet2_rl 达到 34.69 的准确率，而 MMDuet 为 29.44，Dispider 为 25.34，VideoLLM-Online 为 1.96；仅有单点估计，未报告不确定性。
          evidence:: E10
        - 离线基准测试结果：相对于作者复现的 Qwen2.5-VL 3B 基线，MMDuet2_rl 在 Video-MME、MVBench 和 LongVideoBench 上表现相近，其中 LongVideoBench 从 53.1 变为 52.7。
          evidence:: E11
    - **消融与敏感性:** 消融实验表明奖励确实在起控制作用：去掉反重复奖励或跨时间跨度奖励可以提高 PAUC，但会使输出作为交互内容而言质量大幅下降。帧率敏感性也很重要：密集的监督微调（supervised fine-tuning，SFT）采样会退化为输出「NO REPLY」，而更密集的推理采样能改善时机，因为模型有更多机会做出决定。
      evidence:: E12, E13
    - **可复现性缺口:** 论文提供了项目主页、模型与训练框架名称、硬件配置和许多超参数，但在所提供的文本中未报告统计不确定性、重复实验次数、用于奖励评分的具体大语言模型裁判身份与提示词，也未给出完整数据集发布的细节。
      claim_kind:: analyst_assessment
      evidence:: E1, E7, E8
- ## Technical Judgment
    - **站得住的结论:** 论文最强的技术亮点在于将训练信号与真实交互中的权衡对齐：一条回复如果正确且更早到达则更好，但前提是它不冗余也不跑题。奖励消融实验使主要失败模式清晰可见，表明仅靠 PAUC 可以通过过度回答来刷分。
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E12
    - **可能失效之处:** MMDuet2 在长视频或难以解读的视频流上可能不太可靠：论文报告所有模型的 VAD 表现较差，且在强化学习训练后期，EGO 长视频上的重复现象有所增加。将「NO REPLY」作为生成输出的设计虽然易于实现，但在 token 效率上不如附录中提出的停止/继续格式。
      claim_kind:: analyst_assessment
      evidence:: E9, E14, E16
    - **与已有工作的关系:** 与基于阈值的主动式系统（如 VideoLLM-Online 和 MMDuet）相比，MMDuet2 将时机判断纳入语言模型的动作空间，而非调优一个外部的响应分数。与近期经强强化学习增强的视频多模态大语言模型相比，其区别在于多轮实时交互，而非仅做静态视频推理。
      evidence:: E2, E17
    - **可迁移启发:** 一个有启发性的系统设计模式是：当生态系统兼容性更重要时，把一个难以处理的控制决策转化为普通的模型输出，然后针对该输出空间可能出现的可预见退化行为添加奖励项。在这里，将沉默作为文本输出使得主动时机判断能在标准对话基础设施中训练，但需要显式的反刷屏奖励。
      claim_kind:: analyst_assessment
      evidence:: E4, E7, E12
- ## Glossary
  collapsed:: true
    - 视频多模态大语言模型：一种以视频帧和文本为条件的语言模型，因此能够回答关于视频内容的问题或进行对话。
    - 主动交互：一种流式设定，模型在视频播放过程中自行决定何时做出回应，而不仅仅是在用户一轮发言结束后决定如何回答。
    - 监督微调（Supervised Fine-Tuning，SFT）：在带有目标输出的示例上训练预训练模型；本文中它在奖励训练之前教会模型聊天格式和初始的主动行为。
    - 强化学习（Reinforcement Learning，RL）：根据赋予生成行为的标量奖励进行训练，而非仅依赖固定的目标文本；本文中它对尽早给出正确回复的行为给予奖励，并对不良说话模式予以惩罚。
    - 组相对策略优化（Group Relative Policy Optimization，GRPO）：一种强化学习优化方法，对同一输入采样多个输出，并利用这些输出之间的相对奖励来更新模型。
    - 主动曲线下面积（Proactive Area Under Curve，PAUC）：一种面向主动视频的评估指标兼奖励函数形式，它在回复区间内对回答正确性随时间积分，使得越早给出高质量回复得分越高。
    - 回复时间区间：视频中某条标准答案被视为恰当回答的时间段；本文不要求在该时间段内指定唯一精确的时间戳。
    - 「NO REPLY」：MMDuet2 在助手选择当前轮次不回答时使用的字面文本输出。
    - 主动对话类型：1QnA 指一个问题在整段视频中可以有多个回答轮次；nQnA 指一次对话中包含多个问题和多条回答流。
    - 辅助奖励惩罚：额外的奖励项，用于抑制重复回复、在有效区间之外的回复，以及在添加新内容之前照抄先前前缀的回复。
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
