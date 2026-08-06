- **Title:** Multi-Faceted Interactivity Alignment in Full-Duplex Speech Models
  **标题:** 全双工语音模型中的多维交互对齐
- **Summary:** The paper shows that reinforcement learning over separately rewarded conversation events can make full-duplex speech models more responsive without forcing them to speak over users.
  **一句话总结:** 本文表明，对各自单独设置奖励的对话事件进行强化学习，可以让全双工语音模型（能够一边听用户说话、一边自己发声的语音模型）反应更灵敏，同时又不会抢在用户之前开口。
- **Paper Type:** application
  **论文类型:** 应用型论文
- **Venue:** arXiv preprint 2026
  **发表:** arXiv 预印本 2026
- **Authors:** Atsumoto Ohashi (Kyutai), Neil Zeghidour (Gradium), Alexandre Defossez (Kyutai and Gradium), Eugene Kharitonov (Gradium)
  **作者:** Atsumoto Ohashi（Kyutai）、Neil Zeghidour（Gradium）、Alexandre Defossez（Kyutai 与 Gradium）、Eugene Kharitonov（Gradium）
- **Keywords:** full-duplex speech models, spoken dialogue, reinforcement learning, turn-taking, backchanneling, interactive evaluation
  **关键词:** 全双工语音模型、口语对话、强化学习、话轮转换（turn-taking）、附和反馈（backchanneling）、交互式评测
- ## Orientation
    - **Background:** Speech assistants often wait for a clear handoff before replying. A full-duplex speech model instead listens and speaks at the same time, closer to human conversation where people pause, overlap, and give short acknowledgments.
      **背景:** 语音助手通常要等到明确的对话交接之后才作答。而全双工语音对话模型（full-duplex spoken dialogue model）在收听的同时也在说话，更接近人类对话：人们会停顿、话语重叠，还会给出简短的附和。
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** The practical problem is deciding what a quiet or overlapping moment means: the user may be thinking, handing over the turn, asking a correction, or simply needing a quick sign that the system is following.
      **通俗问题:** 现实中的难题在于判断一段安静或话语重叠的时刻意味着什么：用户可能在思考，可能在把发言权交出来，可能在提出纠正，也可能只是需要一个快速的信号来确认系统在跟着自己。
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** Good behavior depends on timing and meaning together. Speaking too early feels interruptive, waiting too long feels broken, and optimizing one habit can damage another.
      **为何困难:** 良好的表现取决于时机和含义两者的结合。说得太早显得像在打断，等得太久显得像出了故障，而优化某一种习惯又可能损害另一种。
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Train on short real conversation moments, reward the specific interaction choice each moment calls for, and add a content check so faster timing does not erase useful answers.
      **一句话核心思路:** 在真实对话中的短片段上训练，针对每个时刻所需要的具体交互选择给予奖励，并加入一项内容检查，让更快的时机不会抹掉有用的回答。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a speech-dialogue alignment paper: it turns vague conversational timing failures into a small set of rewardable interaction events, then tests whether that improves real-time speech agents rather than only offline clips.
      **阅读价值:** 可以把本文当作一篇语音对话对齐的论文来读：它把模糊的对话时机失误，转化为一小组可以设置奖励的交互事件，然后检验这样做是否真的能改善实时语音智能体，而不只是改善离线的音频片段。
      claim_kind:: analyst_assessment
      evidence:: E1, E2, E7
    - **One-Sentence Contribution:** The paper improves full-duplex spoken dialogue behavior by training models on short real conversation moments with rewards tied to the interaction decision each moment requires.
      **一句话贡献:** 本文改善了全双工口语对话的行为方式，做法是让模型在真实对话的短片段上训练，并根据每个片段所需要的交互决策来设置奖励。
      evidence:: E3, E6
    - **Mental Model:** Picture a driving coach replaying short traffic moments: sometimes the right move is to wait, sometimes to go, sometimes to give a quick nod, and sometimes to stop and answer after being cut off.
      **记忆模型:** 可以想象一位驾驶教练在回放一段段短短的交通场景：有时正确的做法是等待，有时是通行，有时是快速点头示意，有时则是在被打断后停下来作出回应。
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is the paired static and interactive evaluation: the method improves timing metrics on Full-Duplex-Bench v1 and mostly carries those gains into Full-Duplex-Bench v2 multi-turn dialogue.
      **最佳证据:** 最有力的证据是静态评测与交互式评测的配对结果：该方法在 Full-Duplex-Bench v1 上改善了时机相关的指标，并且大多数增益都延续到了 Full-Duplex-Bench v2 的多轮对话上。
      evidence:: E9, E11, E12
        - Supports C1: Moshi trained on Fisher; baseline Moshi; Full-Duplex-Bench v1 pause, turn-taking, interruption, and backchannel metrics; pause Candor takeover rate 0.528 to 0.417, turn latency 0.162 to 0.121, interruption latency 1.377 to 0.461; broad support without reported variance.
          支持 C1：在 Fisher 数据集上训练的 Moshi，以基线 Moshi 作对照；采用 Full-Duplex-Bench v1 中的停顿、轮流发言、打断和附和四项指标；停顿场景下的 Candor 接管率从 0.528 降到 0.417，轮流发言延迟从 0.162 降到 0.121，打断响应延迟从 1.377 降到 0.461；总体支持力度较广，但未报告方差。
          evidence:: E9, E11
        - Supports C2: PersonaPlex trained on Seamless; baseline PersonaPlex; Full-Duplex-Bench v2 LLM-judged scores; Daily turn score 3.327 to 4.017, Correction task 3.080 to 3.620, Entity Tracking task 3.200 to 3.840, Safety task 3.260 to 3.280; support is automated and benchmark-specific.
          支持 C2：在 Seamless 数据集上训练的 PersonaPlex，以基线 PersonaPlex 作对照；采用 Full-Duplex-Bench v2 中由大语言模型评判的得分；日常轮流发言得分从 3.327 升到 4.017，纠正任务从 3.080 升到 3.620，实体追踪任务从 3.200 升到 3.840，安全任务从 3.260 升到 3.280；这一支持是自动化的，且局限于特定基准。
          evidence:: E12
        - Supports C3: Moshi trained on Fisher ablations; full model baseline; removing the LLM Judge reward drops interruption GPT-4o score 3.58 to 3.05 and Daily instruction score 2.50 to 2.18; supports the semantic-reward component but not statistical robustness.
          支持 C3：对在 Fisher 数据集上训练的 Moshi 做消融实验，以完整模型作基线；去掉 LLM Judge 奖励后，打断场景的 GPT-4o 得分从 3.58 降到 3.05，日常指令得分从 2.50 降到 2.18；这支持了语义奖励这一组成部分的作用，但不能说明统计上的稳健性。
          evidence:: E13
    - **Main Caveat:** The method is less general than the headline suggests: it assumes models expose a parallel text token stream, depends on manual rule rewards and automated judges, and can push safety behavior in the wrong direction when the interaction corpus is mismatched.
      **主要边界:** 该方法的通用性不如标题所暗示的那么强：它假设模型会暴露出一条并行的文本词元流，依赖人工制定的规则奖励和自动评判器，而且当交互语料不匹配时，可能把安全行为推向错误的方向。
      claim_kind:: analyst_assessment
      evidence:: E14, E15
- ## Argument Map
    - **Problem and Stakes:** The paper argues that token-level supervised learning, which trains a model to predict the next text or audio token, does not directly optimize interaction-level behavior such as when to wait, answer, yield, or backchannel. The stakes are user-visible: a model can sound semantically capable but still feel unnatural because its timing is wrong.
      **问题与重要性:** 本文指出，词元级别的监督学习（训练模型去预测下一个文本或音频词元）并不能直接优化交互层面的行为，比如何时等待、作答、让出发言权或附和。这一点关乎用户的直接体验：一个模型在语义上听起来很有能力，却仍可能因为时机不对而让人觉得不自然。
      evidence:: E1
    - **Prior Gap:** Prior reinforcement learning methods for full-duplex speech, where a model is updated from rewards rather than only from supervised targets, covered only part of the interaction space and often targeted one model family. The paper also identifies semantic degradation as a recurring risk when rewards focus mainly on timing.
      **已有方法缺口:** 此前用于全双工语音的强化学习方法（即根据奖励而非仅凭监督目标来更新模型）只覆盖了部分交互情形，而且往往只针对某一个模型家族。本文还指出，当奖励主要聚焦于时机时，语义退化是一个反复出现的风险。
      evidence:: E2, E7
    - **Key Insight:** The key insight is to decompose interactivity into four observable event types and train on short human-conversation segments where each event type has a simple reward target. This turns broad conversational alignment into repeated local decisions while preserving response content with an LLM Judge, an automatic evaluator that scores transcribed responses for relevance and naturalness.
      **关键洞见:** 核心洞见是把交互能力拆解为四种可观测的事件类型，并在人类对话的短片段上训练，让每种事件类型都对应一个简单的奖励目标。这样一来，宽泛的对话对齐问题就转化为反复进行的局部决策；同时借助 LLM Judge——一种能给转写后的回复在相关性和自然度上打分的自动评估器——保留了回复的内容质量。
      evidence:: E3, E6, E7
    - **Claims:** The paper's main claims are about multi-axis interactivity gains, transfer from short-segment training to longer dialogue, component necessity, and explicit applicability limits.
      **核心主张:** 本文的主要论断围绕以下几点展开：多维度交互能力的提升、从短片段训练到更长对话的迁移、各组成部分的必要性，以及方法适用范围的明确边界。
      claim_kind:: analyst_assessment
        - C1: Axis-specific reinforcement learning improves static full-duplex interactivity across pause handling, turn-taking, backchanneling, and user interruption for both Moshi and PersonaPlex.
          C1：针对特定维度的强化学习能提升静态全双工交互能力，涵盖停顿处理、话轮转换（turn-taking）、附和反馈（backchanneling）和用户打断（user interruption），并且在 Moshi 和 PersonaPlex 两个模型上都成立。
          evidence:: E9, E10, E11
        - C2: Training on short extracted segments can improve real-time multi-turn dialogue behavior, especially turn-taking fluency, in Full-Duplex-Bench v2.
          C2：在抽取出的短片段上训练，能够改善实时多轮对话的行为表现，尤其是话轮转换的流畅度，这一点在 Full-Duplex-Bench v2 上得到验证。
          evidence:: E12
        - C3: Joint rewards and the LLM Judge content reward are needed to balance competing interaction axes and preserve meaningful responses.
          C3：要在相互竞争的多个交互维度之间取得平衡，同时保留有意义的回复内容，联合奖励和 LLM Judge 的内容奖励都不可或缺。
          evidence:: E7, E13
        - C4: The method's applicability is bounded by manual reward design, automated evaluation, safety drift, and model architectures that expose a parallel text token stream.
          C4：该方法的适用性受到四方面的限制：人工设计奖励、自动化评估、安全性漂移，以及模型架构必须暴露一路并行的文本 token 流。
          evidence:: E14, E15
- ## Mechanism and Design
    - **Core Mechanism:** The method applies Group Relative Policy Optimization (GRPO), a reinforcement-learning update that compares multiple sampled answers for the same input, to a pretrained full-duplex speech model. Each batch samples one interaction axis, generates several candidate responses, scores them with the corresponding reward, and updates the model toward candidates that did better than their group.
      **核心机制:** 该方法把群体相对策略优化（Group Relative Policy Optimization，GRPO）——一种针对同一输入比较多个采样答案的强化学习更新方式——应用到一个预训练的全双工语音模型上。每个批处理会采样一个交互维度，生成若干候选回复，用对应的奖励给它们打分，然后把模型朝着表现优于同组其他候选的那些回复更新。
      evidence:: E5, E6
    - **Data / Control Flow:** A voice activity detection (VAD) model, which marks where speech is present, converts two-speaker recordings into utterances and silences; the pipeline extracts event windows for pause handling, turn-taking, backchanneling, and user interruption. During training, the user side is encoded into discrete audio tokens, the model samples responses, generated speech is decoded, and reward scores drive the GRPO update.
      **数据/控制流:** 先用一个语音活动检测（voice activity detection，VAD）模型——它负责标记出哪里有语音——把双人录音切分为发话段和静默段；处理流程随后为停顿处理、话轮转换、附和反馈和用户打断分别抽取出事件窗口。训练时，把用户一侧编码成离散的音频 token，模型采样出回复，再把生成的语音解码出来，最后由奖励分数驱动 GRPO 更新。
      evidence:: E4, E5, E8
        - Extraction uses inter-pausal units (IPUs), speech chunks separated by short pauses, to decide whether an event is a hesitation, a turn handoff, a short listener response, or an interruption.
          抽取过程使用停顿间单元（inter-pausal unit，IPU）——即被短暂停顿隔开的语音片段——来判定某个事件属于犹豫、话轮交接、简短的听者回应，还是打断。
          evidence:: E6, E8
        - Pause handling rewards silence, turn-taking and interruption reward shorter response delay, and backchanneling rewards short acknowledgments near human backchannel positions while penalizing takeovers.
          停顿处理奖励保持静默；话轮转换和打断奖励更短的回复延迟；附和反馈则奖励在人类附和位置附近给出简短的应答，同时对抢占话语权（takeover）的行为施加惩罚。
          evidence:: E6
        - The loss is computed over the segment while a randomly sampled preceding context window can be prepended and masked out, so the model conditions on recent conversation without being trained to reproduce that context.
          损失只在该片段上计算，同时可以在片段前面拼接一段随机采样的前置上下文（preceding context）并将其掩蔽掉，这样模型会以近期对话为条件生成内容，但不会被训练去复现那段上下文。
          evidence:: E5, E8
    - **Design Decisions:** The design is deliberately narrow: it does not invent a new full-duplex architecture, but post-trains existing models with rewards tied to the benchmark's interaction axes. The closest alternative is a single timing objective or a smaller subset of behaviors, which the paper argues can shift rather than solve the interaction tradeoff.
      **设计决策:** 该设计有意保持窄范围：它不发明一种新的全双工架构，而是对已有模型做后训练，用与基准的各个交互维度挂钩的奖励来引导。最接近的替代方案是只用单一的时机（timing）目标，或者只覆盖行为的一个更小子集，而论文认为这类做法只会转移而非真正解决交互权衡问题。
      claim_kind:: analyst_assessment
      evidence:: E2, E3, E13
        - Need: realistic timing. Choice: extract short segments from Fisher and Seamless human conversations rather than synthesize artificial dialogues; tradeoff: corpus style can become a behavioral prior.
          需求：真实的时机。选择：从 Fisher 和 Seamless 的人类对话中截取简短片段，而不是合成人工对话；权衡：语料风格可能会变成一种行为先验。
          evidence:: E8, E15
        - Need: prevent fast but irrelevant replies. Choice: add an LLM Judge reward to turn-taking and interruption; tradeoff: the content signal inherits automatic speech recognition and judge-model failure modes.
          需求：防止回复虽快但不相关。选择：在轮流发言（turn-taking，即判断用户何时让出话语权并及时开始回应而不打断对方未说完的话）和打断处理中加入一项 LLM Judge（大语言模型评判器）奖励；权衡：这条内容信号会继承自动语音识别（automatic speech recognition，ASR）和评判模型自身的失效模式。
          claim_kind:: analyst_assessment
          evidence:: E7, E14
        - Need: make policy updates tractable. Choice: compute the importance ratio and objective only on the parallel text token stream because the paper says timing and content are primarily controlled there; tradeoff: models without such a stream are out of scope.
          需求：让策略更新在计算上可行。选择：只在并行的文本 token 流上计算重要性比率和目标函数，因为论文指出时机和内容主要就是在这条流上被控制的；权衡：没有这样一条文本流的模型就不在适用范围内。
          evidence:: E4, E14
    - **Implementation Surface:** The implementation surface is a post-training recipe for existing open-source full-duplex models, tested on Moshi, a seven-billion-parameter speech-text language model, and PersonaPlex, a Moshi-derived model with prompt and voice control. It reports training on Fisher or Seamless with GRPO over 100 epochs, 16 completions per segment, and 32 H100 GPUs.
      **实现边界:** 该方法的落地形态是一套针对已有开源全双工模型的后训练配方，在 Moshi（一个七十亿参数的语音-文本语言模型）和 PersonaPlex（一个由 Moshi 衍生、支持提示词与声音控制的模型）上做了测试。论文报告称，训练使用 Fisher 或 Seamless 数据，采用 GRPO（组相对策略优化，Group Relative Policy Optimization），共训练 100 个 epoch，每个片段生成 16 个补全，使用 32 块 H100 GPU。
      evidence:: E8, E16
- ## Evaluation and Evidence
    - **Setup:** The static benchmark is Full-Duplex-Bench v1, which feeds prerecorded audio and measures takeover rate (TOR), response latency, backchannel frequency, Jensen-Shannon divergence (JSD), and a GPT-4o semantic score for interruption responses. The dynamic benchmark is Full-Duplex-Bench v2, where GPT-Realtime acts as an automated speaking partner and Gemini 2.5 Flash judges turn-taking fluency, instruction following, and task competence.
      **实验设置:** 静态基准是 Full-Duplex-Bench v1，它输入预先录制的音频，并测量接管率（Takeover Rate，TOR）、响应延迟、回话反馈（backchanneling）频率、Jensen-Shannon 散度（Jensen-Shannon divergence，JSD）以及一个用于评估打断响应的 GPT-4o 语义得分。动态基准是 Full-Duplex-Bench v2，其中 GPT-Realtime 充当自动化的说话对手，由 Gemini 2.5 Flash 评判轮流发言的流畅度、指令遵循情况和任务胜任能力。
      evidence:: E8, E12
    - **Claim-Evidence Matrix:** The evidence is strongest for C1 and moderate for C2 and C3: the paper reports broad metric improvements, but the main tables do not report confidence intervals, repeated seeds, or human-judged conversation quality.
      **主张-证据矩阵:** 证据对 C1 最为有力，对 C2 和 C3 则属中等：论文报告了在多项指标上的普遍改进，但主要表格没有报告置信区间、重复随机种子，也没有报告由人工评判的对话质量。
      claim_kind:: analyst_assessment
      evidence:: E9, E10, E12, E13
        - C1: Table 1 supports multi-axis static improvement for both model families, with the caveat that benchmark metrics are automatic and variance is not reported.
          C1：表 1 支持两个模型家族在多维度上的静态改进，但需要注意的是，基准指标都是自动计算的，且没有报告方差。
          claim_kind:: analyst_assessment
          evidence:: E9, E10, E11
        - C2: Table 2 supports transfer to multi-turn dialogue for most conditions, but scoring is still automated and Fisher safety behavior shows a corpus-dependent regression.
          C2：表 2 支持在大多数条件下向多轮对话的迁移，但打分仍然是自动化的，而且 Fisher 语料上的安全行为出现了一处依赖语料的退化。
          claim_kind:: analyst_assessment
          evidence:: E12, E15
        - C3 and C4: Table 3 and the Limitations section support the need for content reward and context while also exposing manual-reward, text-stream, automated-evaluation, and safety boundaries.
          C3 与 C4：Table 3 和「局限性（Limitations）」一节支持了对内容奖励和上下文的需求，同时也暴露了人工奖励、文本流、自动化评估和安全性方面的边界与局限。
          claim_kind:: analyst_assessment
          evidence:: E13, E14, E15
    - **Headline Results:** On Full-Duplex-Bench v1, RL improves the target interaction metrics for both Moshi and PersonaPlex, including lower pause takeover, faster response latency, and better interruption response timing. On Full-Duplex-Bench v2, Seamless-trained variants are the clearest winners, especially PersonaPlex with Seamless across Daily, Correction, Entity Tracking, and most Safety metrics.
      **关键结果:** 在 Full-Duplex-Bench v1 上，强化学习（reinforcement learning，RL）对 Moshi 和 PersonaPlex 都改善了目标交互指标，包括更低的停顿接管、更快的响应延迟，以及更好的打断响应时机。在 Full-Duplex-Bench v2 上，用 Seamless 训练的变体明显胜出，尤其是使用 Seamless 的 PersonaPlex，在 Daily、Correction、Entity Tracking 以及大多数 Safety 指标上都是如此。
      evidence:: E9, E10, E12
        - Moshi plus Fisher shows the cleanest latency gain in Table 1, cutting interruption latency from 1.377 s to 0.461 s while also reducing pause Candor TOR from 0.528 to 0.417.
          Moshi 加 Fisher 在 Table 1 中展现出最明显的延迟改善，将打断延迟从 1.377 秒降到 0.461 秒，同时把停顿的 Candor 接管率（Takeover Rate，TOR）从 0.528 降到 0.417。
          evidence:: E9
        - PersonaPlex plus Seamless reduces backchannel TOR from 0.182 to 0.073 and turn-taking latency from 0.219 s to 0.086 s, while keeping the interruption GPT-4o score slightly above the base model.
          PersonaPlex 加 Seamless 将附和（backchanneling）的接管率（TOR）从 0.182 降到 0.073，把话轮转换（turn-taking）延迟从 0.219 秒降到 0.086 秒，同时让打断的 GPT-4o 评分略高于基础模型。
          evidence:: E10
        - PersonaPlex plus Seamless improves the Daily, Correction, Entity Tracking, and Safety task-family scores in Table 2, but the largest gains are not uniformly in safety competence.
          PersonaPlex 加 Seamless 在 Table 2 中提升了 Daily、Correction、Entity Tracking 和 Safety 各任务族的得分，但最大的提升并不都集中在安全能力上。
          evidence:: E12, E15
    - **Ablations and Sensitivity:** The ablations make the paper more credible because they reveal a real tradeoff: without pause data the model speaks too readily, without turn data it becomes too conservative, and without the LLM Judge reward the semantic scores fall. Context scheduling is less dramatic than the reward ablations but still helps multi-turn behavior.
      **消融与敏感性:** 消融实验让这篇论文更可信，因为它们揭示了一个真实的权衡：没有停顿数据时，模型太容易开口说话；没有话轮数据时，模型又太保守；没有 LLM 评判器（LLM Judge）奖励时，语义得分下降。上下文调度的影响不像奖励消融那么明显，但仍然有助于多轮对话行为。
      evidence:: E13
        - Without pause data, pause TOR worsens from 0.42 to 0.74 while turn latency falls to 0.05 s; without turn data, turn latency worsens to 0.30 s, showing the wait-versus-speak tradeoff.
          没有停顿数据时，停顿接管率（TOR）从 0.42 恶化到 0.74，而话轮延迟降到 0.05 秒；没有话轮数据时，话轮延迟恶化到 0.30 秒，这体现了「等待还是开口」的权衡。
          evidence:: E13
        - Without the LLM Judge reward, the interruption semantic score falls to 3.05 and Daily instruction-following to 2.18, supporting the claim that timing rewards alone are insufficient.
          没有 LLM 评判器奖励时，打断的语义得分降到 3.05，Daily 指令遵循得分降到 2.18，这支持了「仅靠时机奖励并不够」的说法。
          evidence:: E13
        - Without context, Daily turn-taking and instruction scores fall relative to the full Fisher model, supporting the use of preceding audio even when the loss is only on short segments.
          没有上下文时，Daily 的话轮转换和指令得分相对于完整的 Fisher 模型有所下降，这支持了即便损失只在短片段上计算，也应该使用前置音频的做法。
          evidence:: E13
    - **Reproducibility Gaps:** Checkpoints and audio samples are reported as available, but full reproduction still needs unreported details around exact extracted segment lists, evaluation-script patching, automated-judge prompts beyond the shown LLM reward prompt, and large hardware. The paper reports 32 H100 GPUs for training, making exact replication expensive even if model artifacts are public.
      **可复现性缺口:** 论文声称检查点和音频样本已公开，但要完整复现，仍缺少一些未公开的细节：确切的抽取片段清单、评估脚本的修改补丁、除已展示的 LLM 奖励提示词之外的自动评判提示词，以及大规模硬件。论文提到训练使用了 32 块 H100 GPU，因此即便模型产物公开，精确复现的成本依然很高。
      claim_kind:: analyst_assessment
      evidence:: E8, E16
- ## Technical Judgment
    - **What Holds Up:** The central engineering claim holds up better than a single-metric timing paper would: the method improves multiple competing static metrics, tests two model families, and includes ablations that show why the pause, turn, content, and context components matter. The evidence is still benchmark-centric, so the right reading is promising post-training recipe rather than settled human-conversation quality.
      **站得住的结论:** 该论文的核心工程主张比只看单一指标的时延类论文更站得住脚：这套方法在多个相互竞争的静态指标上都有提升，测试了两个模型系列，并且通过消融实验说明了停顿、话轮、内容和上下文这四个组成部分各自为何重要。不过证据仍然以基准测试为中心，因此合理的解读是：这是一个有前景的后训练方案，而非已经定论的真人对话质量。
      claim_kind:: analyst_assessment
      evidence:: E9, E10, E12, E13
    - **Where It May Fail:** The method may fail when the target model does not expose a parallel text stream, when the desired behavior is not captured by hand-written VAD-based rewards, or when the interaction corpus teaches the wrong social prior. The Fisher safety regression is the clearest warning that responsiveness is not the same as policy alignment.
      **可能失效之处:** 这套方法在以下情况下可能失效：目标模型没有暴露出一路平行的文本流；期望的行为无法由人工设计的、基于语音活动检测（VAD）的奖励来刻画；或者交互语料本身教出了错误的社交先验。Fisher 安全性上的退化是最明显的警示，说明「响应及时」并不等于「策略对齐」。
      claim_kind:: analyst_assessment
      evidence:: E14, E15
    - **Relation to Other Work:** Compared with prior preference-based and online-reinforcement-learning full-duplex alignment methods, this paper broadens the reward surface from barge-in or backchannel behavior to four benchmark-aligned axes; compared with ASPIRin, it keeps GRPO-style timing optimization but adds explicit semantic reward and multi-model evaluation. Compared with cascaded full-duplex systems, it stays inside end-to-end speech models rather than adding external turn-control modules.
      **与已有工作的关系:** 与此前基于偏好和基于在线强化学习的全双工对齐方法相比，本文把奖励覆盖面从抢话（barge-in）或反馈附和（backchannel）行为扩展到了四个与基准测试对齐的维度；与 ASPIRin 相比，本文保留了 GRPO 风格的时序优化，但增加了显式的语义奖励和多模型评测。与级联式全双工系统相比，本文停留在端到端语音模型内部，而不是额外添加外部的话轮控制模块。
      evidence:: E2, E3, E7
    - **Transferable Lesson:** For interactive agents, optimize the decision boundary that users feel, not just the content generator: split the interaction into concrete event windows, reward the local decision, and add a separate guardrail for content or safety so speed does not become blind compliance.
      **可迁移启发:** 对于交互式智能体，应当优化用户能真切感受到的决策边界，而不仅仅是内容生成器：把交互切分成具体的事件窗口，对每个局部决策给予奖励，并为内容或安全另设一道独立的护栏，这样「响应快」才不会变成「盲目服从」。
      claim_kind:: analyst_assessment
      evidence:: E3, E7, E13, E15
- ## Glossary
  collapsed:: true
    - full-duplex spoken dialogue model: A speech model that can listen to incoming user audio while also producing its own speech, instead of waiting for a strict turn boundary.
      全双工语音对话模型（full-duplex spoken dialogue model）：一种语音模型，可以在收听用户传入音频的同时也产生自己的语音，而不必等到严格的话轮边界才开口。
    - turn-taking: The ability to detect when the user has yielded the floor and begin responding promptly without speaking over an unfinished utterance.
      话轮转换（turn-taking）：一种能力，即察觉用户何时让出发言权，并及时开始回应，同时又不打断用户尚未说完的话。
    - backchanneling: Short listener feedback such as brief acknowledgments while the user continues speaking; in this paper it must be timed without becoming a takeover.
      反馈附和（backchanneling）：作为听者给出的简短反馈，比如在用户继续说话时给出的简短应答；在本文中，这类附和必须把握好时机，又不能演变成抢过发言权。
    - user interruption: A moment where the user starts speaking while the model is speaking; the desired behavior is to yield and then answer the interruption.
      用户打断（user interruption）：指用户在模型正在说话时开口说话的时刻；期望的行为是模型让出发言权，然后回应这次打断。
    - voice activity detection: A detector that marks which time intervals contain speech; the paper uses it to build training segments and compute rewards.
      语音活动检测（voice activity detection）：一种检测器，用来标记哪些时间段内含有语音；本文用它来构建训练片段并计算奖励。
    - inter-pausal unit: A speech chunk separated by pauses; the paper groups these chunks into utterances when pauses are short enough.
      停顿间单元（inter-pausal unit）：由停顿分隔开的一段语音块；当停顿足够短时，本文会把这些语音块归并为一个话语单元。
    - Group Relative Policy Optimization: A reinforcement-learning method that samples several outputs for the same input, normalizes their rewards within the group, and updates the policy toward relatively better outputs.
      分组相对策略优化（Group Relative Policy Optimization）：一种强化学习方法，它针对同一个输入采样出多个输出，在该组内对这些输出的奖励做归一化，然后朝着相对更好的输出方向更新策略。
    - Takeover Rate: The proportion of samples where the model produces a prolonged utterance rather than staying silent or giving only a short backchannel.
      接管率（Takeover Rate）：指模型产生较长发言（而不是保持沉默或只给出简短附和）的样本所占的比例。
    - Jensen-Shannon divergence: A bounded distribution-distance metric; here it measures how far generated backchannel timing is from human backchannel timing.
      Jensen-Shannon 散度（Jensen-Shannon divergence）：一种取值有界的分布距离度量；在这里用来衡量生成的附和时机与人类附和时机之间的差距有多大。
    - LLM Judge: A large-language-model evaluator that scores transcribed model responses for contextual relevance and naturalness.
      大语言模型评判器（LLM Judge）：一种基于大语言模型的评估器，用于对转录后的模型回复在情境相关性和自然度方面打分。
    - automatic speech recognition: A speech-to-text system used before LLM-based semantic scoring of generated speech.
      自动语音识别（automatic speech recognition）：一种语音转文本系统，在用大语言模型对生成的语音做语义打分之前先行使用。
    - context window: Audio immediately before a training segment that is prepended as conditioning context but masked out of the loss.
      上下文窗口（context window）：指紧邻在训练片段之前的音频，它会作为条件上下文拼接到片段前面，但在计算损失时被屏蔽掉。
- ## Evidence Index
  collapsed:: true
    - **E1:** problem/paper_statement | Abstract and Introduction | high
      locator:: Abstract; Section 1
      quote:: Full-duplex spoken dialogue models can listen and speak simultaneously, making them a promising architecture for natural conversation. However, current models are trained solely with supervised learning through token-level likelihood maximization, which does not directly optimize interaction-level behaviors.
    - **E2:** gap/paper_statement | Introduction and Related Work | high
      locator:: Section 1; Section 2.2
      quote:: Prior works have explored using reinforcement learning to improve the interactivity of full-duplex models, but covered only a subset of conversational dynamics such as handling user's barge-in and backchanneling, failing to comprehensively address all axes of interactivity.
    - **E3:** method/paper_statement | Method | high
      locator:: Section 3, Figure 1
      quote:: We target four core axes of interactivity: pause handling, turn-taking, backchanneling, and user interruption. These four axes have been established as a standard and comprehensive characterization of full-duplex interactivity.
    - **E4:** formula/implementation_detail | Full-Duplex Spoken Dialogue Modeling | high
      locator:: Section 3.1
      quote:: Given a two-channel dialogue between speakers X and Y, a speech tokenizer E maps each speaker's waveform into a sequence of discrete tokens from a vocabulary. The model learns to autoregressively predict speaker Y's tokens conditioned on speaker X's input stream and its own preceding outputs.
    - **E5:** algorithm/implementation_detail | Reinforcement Learning Pipeline | high
      locator:: Section 3.2
      quote:: For each sample in the batch, we first sample an interactivity axis, then draw a segment from the axis-specific training set. The current policy generates G completions, each completion is decoded into a waveform and scored by an axis-specific reward function.
    - **E6:** method/implementation_detail | Reward Design | high
      locator:: Section 3.4
      quote:: We design a dedicated reward function for each interactivity axis. Pause handling assigns a binary reward if generated audio contains speech longer than 1 s; turn-taking and user interruption use negative response delay; backchanneling uses an F1 score around ground-truth backchannel positions.
    - **E7:** method/implementation_detail | Reward Design | medium
      locator:: Section 3.4, LLM Judge
      quote:: To prevent semantic degradation caused by optimization with delay-based rewards alone, we add a content quality reward to the turn-taking and user-interruption axes. Transcriptions are scored by an LLM judge on a three-point scale for contextual relevance and naturalness.
    - **E8:** experiment_setup/paper_statement | Experiments | high
      locator:: Sections 4.1 and 4.3
      quote:: We adopt two datasets: Fisher, with 2,000 h of telephone conversations, and Seamless Interaction, with Improvised and Naturalistic subsets totaling 4,000 h. Training runs for 100 epochs with 32 segments per epoch and G = 16 completions on 32 H100 GPUs.
    - **E9:** result/experiment_result | Results and Analysis | medium
      locator:: Table 1, Moshi rows
      quote:: For Moshi, Table 1 reports that RL with Fisher changes pause Candor TOR from 0.528 to 0.417, backchannel TOR from 0.255 to 0.091, turn-taking latency from 0.162 to 0.121, and interruption latency from 1.377 to 0.461.
    - **E10:** result/experiment_result | Results and Analysis | medium
      locator:: Table 1, PersonaPlex rows
      quote:: For PersonaPlex, Table 1 reports that RL with Seamless changes pause Candor TOR from 0.444 to 0.356, backchannel TOR from 0.182 to 0.073, turn-taking latency from 0.219 to 0.086, and GPT-4o interruption score from 4.500 to 4.533.
    - **E11:** result/experiment_result | Results of Static Evaluation | medium
      locator:: Section 5.1
      quote:: Within both the Moshi and PersonaPlex families, RL training yields consistent improvements over the respective base models. TOR of pause handling decreases substantially, while latency and TOR of turn-taking simultaneously improve.
    - **E12:** result/experiment_result | Results of Interactive Evaluation | medium
      locator:: Table 2 and Section 5.2
      quote:: Table 2 evaluates real-time multi-turn dialogues. PersonaPlex with Seamless improves over PersonaPlex on Daily Turn 3.327 to 4.017, Correction Task 3.080 to 3.620, Entity Tracking Task 3.200 to 3.840, and Safety Task 3.260 to 3.280.
    - **E13:** ablation/ablation | Ablations | medium
      locator:: Table 3 and Section 5.3
      quote:: Removing the LLM Judge reward leads to the largest degradation across nearly all metrics. Table 3 reports that without the LLM reward, GPT-4o interruption score drops from 3.58 to 3.05 and Daily instruction-following drops from 2.50 to 2.18.
    - **E14:** limitation/limitation | Limitations | high
      locator:: Limitations
      quote:: The rule-based reward design for each interactivity axis requires manual engineering effort and may overlook other aspects of conversational dynamics. As the number of axes grows, this approach becomes increasingly difficult to scale.
    - **E15:** limitation/case_study | Limitations and Case Studies | medium
      locator:: Limitations; Appendix D.2
      quote:: Optimizing interactivity through RL can inadvertently degrade the model's safety behavior. Training on the Fisher dataset led to a decline in safety scores, as the cooperative interaction style of the training data conflicted with the ability to refuse or redirect harmful requests.
    - **E16:** result/experiment_result | Introduction and Appendix C | medium
      locator:: Footnote 1; Appendix C, Table 4
      quote:: The checkpoints of the models and audio samples are available on Hugging Face. Appendix C reports UTMOSv2 speech-quality scores and states that, for both Moshi and PersonaPlex, scores after RL remain comparable to the respective baselines.
