- **标题:** RAGEN：通过多轮强化学习理解大语言模型智能体的自我进化
- **一句话总结:** RAGEN 使用一套轨迹层面的强化学习框架，表明大语言模型智能体能够通过与环境交互而不断改进；但多轮的自我训练很脆弱，只有在谨慎处理好轨迹采样的选择、梯度整形以及考虑推理过程的奖励设计之后，训练才能稳定。
- **论文类型:** 系统类论文
- **发表:** arXiv 预印本 2025
- **作者:** Zihan Wang、Kangrui Wang、Qineng Wang、Pingyue Zhang、Linjie Li、Zhengyuan Yang、Xing Jin、Kefan Yu、Minh Nhat Nguyen、Licheng Liu、Eli Gottlieb、Yiping Lu、Kyunghyun Cho、Jiajun Wu、Li Fei-Fei、Lijuan Wang、Yejin Choi、Manling Li；Northwestern University、University of Washington、Stanford University、Microsoft、New York University、University of British Columbia、Singapore Management University
- **关键词:** 大语言模型智能体、多轮强化学习、轨迹层面的优化、训练稳定性、推理能力退化
- ## Orientation
    - **背景:** 这篇论文属于面向语言模型智能体的强化学习（reinforcement learning，RL）领域。强化学习指的是通过多次尝试所获得的奖励来进行训练；智能体是一个在环境中采取行动、观察结果、再选择下一步动作的模型。
      claim_kind:: analyst_assessment
    - **通俗问题:** 聊天模型可以回答一次性的问题，但智能体必须在每一步操作之后继续行动，并从自己的成功与失误中学习，而不是被直接告知正确的路径。
      claim_kind:: analyst_assessment
    - **为何困难:** 同样的最终得分可能来自一个好的计划、一次幸运的偶然，或是一个被反复使用的捷径，因此反馈可能奖励那些看起来有用、却无法建立稳健推理能力的行为。
      claim_kind:: analyst_assessment
    - **一句话核心思路:** 把整段交互过程作为训练和诊断的对象，然后追问：哪些 rollout 的选择和奖励信号能让学习保持多样化、稳定，并真正具备推理特征。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **阅读价值:** 把本文当作一篇关于智能体训练的研究来读。它提出的问题是：基于规则的强化学习本可以改善静态的推理任务，但当语言模型需要在多个回合里连续地采取动作、观察反馈、再继续行动时，为什么训练会变得不稳定。
      evidence:: E1, E4
    - **一句话贡献:** RAGEN 把每一整段交互过程（即一个完整的交互回合，从开始到结束）当作学习对象，从而可以在动作、反馈、能力崩溃以及推理行为等多个维度上分析训练信号，推进了对能够自我进化的大语言模型智能体的研究。
      evidence:: E2, E3
    - **记忆模型:** 可以想象一个学生反复玩一些小游戏：本文关注的不只是这个学生是否赢了，还包括每一轮练习之后，他的行为习惯是否变得更狭窄、更混乱，还是更有条理。
      claim_kind:: analyst_assessment
    - **最佳证据:** 最有力的证据来自跨环境的训练过程记录：朴素的轨迹层面强化学习在早期会有所改善，但随后常常崩溃；而经过筛选和梯度整形的改进版本则能推迟或减轻这种崩溃。
      evidence:: E6, E9
        - 支持 C1：在 Bandit、Sokoban、Frozen Lake 和 WebShop 上以 StarPO 作为基线；对 PPO/GRPO 做了单轮式的适配；给出成功率与稳定性指标；符号类任务在初期取得进步后崩溃；由于没有报告重复次数和不确定性区间，因此只是部分得到支持。
          evidence:: E4, E6
        - 支持 C2：在 PPO/GRPO 上应用 StarPO-S 的不确定性过滤；对照「保留全部 rollout」和「保留固定比例」两种基线；以成功率的稳定性为衡量标准；过滤掉低方差的提示（prompt）能推迟或避免崩溃；由于承认默认保留比例依赖于具体任务，因此只是部分得到支持。
          evidence:: E7, E9
        - 支持 C3：围绕提示（prompt）多样性、每轮动作数量、以及 Online-k 复用等因素，对 rollout 质量做了扫描式实验；在固定预算下进行比较；以泛化成功率为指标；结果表明适中的动作预算和更新鲜的 rollout 表现更好；由于这些扫描主要在风格化（人为简化）的环境中进行，因此只是部分得到支持。
          evidence:: E11, E12
        - 支持 C4：在 Bandit 和 Sokoban 上比较「带推理」与「不带思考」两种设置，并跟踪推理长度；以任务成功率和 think 块长度为指标；结果表明推理有助于 Bandit 上的泛化，但在多轮任务中会逐渐缩短；由于推理质量是用稀疏的结果奖励和少量案例来判断的，因此只是部分得到支持。
          evidence:: E13, E14
    - **主要边界:** 这些结论作为受控的诊断性证据最为可靠，但并不能证明所提出的方法能扩展到真实的智能体：大多数证据来自小模型、风格化（人为简化）的任务、稀疏奖励，以及对方差或重复结构报告不足的实验。
      claim_kind:: analyst_assessment
- ## Argument Map
    - **问题与重要性:** 这篇论文关注可自我进化的 LLM 智能体：通过强化学习（reinforcement learning，RL）训练的语言模型，也就是通过奖励驱动的试错来学习，同时在多轮交互中面对具有随机性的环境反馈。它的现实意义在于：规划助手、辅导型智能体、类机器人智能体以及网页智能体，都需要能从经验中改进的策略，而不是仅仅依赖静态的「提示—回复」数据来学习。
      evidence:: E1, E4
    - **已有方法缺口:** 以往关于「用强化学习训练大语言模型」的工作，大多是针对一个提示词优化一个回复；而本文认为，交互式智能体需要用马尔可夫决策过程（Markov Decision Process，MDP）来刻画，也就是一个形式化的循环：状态、动作、状态转移和奖励随时间不断展开。这里的差距不仅仅在于轮数更多，还在于模型从自己生成的轨迹中学习时所产生的训练动态。
      evidence:: E1, E3
    - **关键洞见:** 核心洞见是：多轮智能体强化学习必须在轨迹层面来研究。一条轨迹是状态、推理文本、可执行动作、奖励以及后续观测的完整记录。一旦训练素材是整条轨迹，那么崩溃信号、rollout 的新鲜程度、奖励的变化性以及推理质量，就成了首要的设计变量，而不再是副产品。
      evidence:: E2, E3, E8
    - **核心主张:** 本文的主要主张偏经验性和诊断性，而不是在某个单一基准上取胜。
      evidence:: E6, E9, E11, E13
        - C1：单轮的策略优化方案难以顺畅地迁移到多轮智能体强化学习，因为它们往往先带来早期收益，随后就崩溃。这类方案包括近端策略优化（Proximal Policy Optimization，PPO），它利用学到的价值估计来裁剪策略更新；以及组相对策略优化（Group Relative Policy Optimization，GRPO），它在一个分组内对奖励做归一化，而不需要评论者（critic）网络。
          evidence:: E6, E8
        - C2：StarPO-S 通过过滤低信息量的提示词并对梯度进行整形，来稳定轨迹层面的强化学习；尤其是在同一提示词的重复 rollout 显示出奖励变化性很低时，这种做法效果明显。
          evidence:: E9, E10
        - C3：rollout 的质量取决于任务多样性、动作预算和新鲜程度。当 rollout 覆盖多样的初始状态、允许足够但不过量的动作，并且在当前策略下频繁重新生成时，智能体的泛化能力更强。
          evidence:: E11, E12
        - C4：在简单的单轮符号任务中，推理轨迹可能有帮助；但在多轮任务中，如果奖励只对最终结果打分，而不评估中间推理的质量，那么推理轨迹就会逐渐淡化，或者变得虚假无用。
          evidence:: E13, E14
- ## Mechanism and Design
    - **核心机制:** 状态-思考-动作-奖励策略优化（State-Thinking-Actions-Reward Policy Optimization，StarPO）优化的是整条轨迹 $\tau$ 的期望累积奖励，其中 $\tau$ 包含观测到的状态、模型以推理格式给出的动作文本、环境奖励以及后续状态。这一机制与自回归大语言模型兼容，因为轨迹概率可以分解为词元（token）级别的似然，然后用 PPO 或 GRPO 风格的目标函数来优化。
      evidence:: E3
        - 学习目标从单个提示词-回复的奖励 $R(s,a)$（其中 $s$ 是提示词状态，$a$ 是一次输出），改为轨迹奖励 $R(\tau)$（其中 $\tau$ 是完整的交互历史）。
          evidence:: E3
        - 每个动作都以「推理加上可执行答案」的形式生成，因此模型类似隐藏计划的文本和面向环境的动作，都会出现在训练轨迹中。
          evidence:: E3
    - **数据/控制流:** RAGEN 运行一个循环：采样初始状态，为每个状态生成若干条采样轨迹（rollout），在环境中执行模型的动作，为轨迹分配奖励，然后基于得到的 token 序列更新模型。论文的主要设定在符号类任务上使用 Qwen2.5-Instruct 0.5B，在 WebShop 上使用一个 3B 模型，并配有固定的验证提示，以及衡量成功率、熵、奖励波动性、回复长度和梯度范数的指标。
      evidence:: E4, E5
        - rollout 的生成可以是在策略（on-policy）的，也就是从当前模型采样，也可以通过类似回放缓冲区（replay buffer）的来源，复用较早策略产生的轨迹；不过论文后面把缺少成熟的回放缓冲区做法列为一项局限。
          evidence:: E3, E15
        - 评测面刻意混合了 Bandit、Sokoban、Frozen Lake 和 WebShop，让同一套训练循环同时面对：对风险敏感的选择、不可逆的规划、随机的状态转移，以及以语言为基础的网页交互。
          evidence:: E4
    - **设计决策:** 最重要的设计决策是保持框架的模块化：StarPO 提供轨迹这一抽象，而 RAGEN 提供环境、奖励、rollout 策略，以及用于诊断的各种优化变体。StarPO-S 在此基础上加入了有选择的训练数据和约束更少的梯度，因为它把崩溃（collapse）当作一个采样与更新的问题，而不仅仅是模型能力的问题。
      evidence:: E2, E9, E10
        - 需求：避免在那些轻易就能解决、或者一律失败的提示（prompt）上训练；设计选择：保留那些在重复 rollout 之间奖励标准差较高的提示；权衡：这种较激进的保留比例并非在所有情况下都是最优的。
          evidence:: E9
        - 需求：防止有用的更新被过度约束；设计选择：去掉库尔贝克-莱布勒（Kullback-Leibler，KL）惩罚项——这一项的作用是让新策略保持接近参考策略——并采用非对称裁剪（asymmetric clipping），从而允许更强的正向更新；权衡：更宽松的约束可能会在未测试过的场景中加剧策略漂移。
          evidence:: E10
        - 需求：让优化目标与当前行为保持一致；设计选择：使用多样化的提示、每个提示生成多个回复、适中的每轮动作预算，以及频繁刷新 rollout；权衡：rollout 越新鲜，所需的环境交互就越多。
          evidence:: E11, E12
    - **实现边界:** 实现层面是一套研究系统，而不仅仅是一个公式：RAGEN 集成了结构化提示、环境执行、奖励函数、多轮 rollout、PPO/GRPO 更新，以及诊断指标。论文也说明了代码和环境是公开可用的，但本笔记应把精确的可复现性看作部分成立，因为论文并未对所有主要结果给出完整的统计流程。
      evidence:: E2, E5, E15
- ## Evaluation and Evidence
    - **实验设置:** 主要实验在四个环境上训练小型的 Qwen2.5-Instruct 模型，并在固定的验证提示上评测，使用成功率，以及针对探索行为和更新稳定性的诊断指标。这套设置很适合对训练动态做因果诊断，但它并不是一套广泛的智能体基准测试集。
      evidence:: E4, E5
        - 指标包括：任务成功率、token 级别的 rollout 熵、在重复 rollout 之间组内奖励的方差或标准差、回复长度，以及梯度范数（gradient norm）。
          evidence:: E5, E8
    - **主张-证据矩阵:** 当论文把某个论断与受控曲线或消融实验挂钩时，证据最为有力；当论断依赖于定性的推理轨迹，或依赖未明说的、不同随机种子（seed）之间的方差时，证据则较弱。
      claim_kind:: analyst_assessment
        - C1 由基线 PPO/GRPO 曲线以及跨任务的崩溃诊断结果所支持，置信度为中等，原因是论文更强调轨迹和图表，而不是统计上的不确定性。
          evidence:: E6, E8
        - C2 由不确定性过滤和梯度整形的消融实验所支持，置信度为中等，原因是最优的过滤阈值取决于具体任务，而不是从某条通用规则推导出来的。
          evidence:: E9, E10
        - C3 和 C4 由 rollout 因子扫描（即系统性地改变每个 prompt 采样的轨迹数量）以及「推理与不推理」的对比所支持，置信度为中等，原因是它们衡量了重要的替代指标，但并没有把推理质量与动作成功率完全区分开。
          evidence:: E11, E12, E13, E14
    - **关键结果:** 核心结论并不是说 StarPO-S 在每个环境里都胜出，而是说朴素的多轮强化学习会出现可重复的崩溃特征，并且一些简单的稳定手段可以推迟或减弱这些崩溃。最具体的结果出现在 Frozen Lake 环境的 PPO 实验中：保留 75% 的 rollout 能把稳定期从 100 步延长到 140 步，而保留 50% 的 rollout 则在报告的那次运行中避免了崩溃。
      evidence:: E6, E9
        - 一个有价值的反面结果是：在监督微调（supervised fine-tuning，SFT），也就是直接在真实轨迹（ground-truth trajectories）上训练的情况下，在附录 G 的 Sokoban 任务上其表现优于 StarPO-S，这为当前关于自我演化的论断划定了边界。
          evidence:: E16
    - **消融与敏感性:** 论文对最可能影响轨迹学习的各个部分做了消融：不确定性过滤、去除 KL 项、非对称截断、prompt 多样性、每轮的动作数量、rollout 复用、推理标签，以及规模扩展。整体的敏感性结论是自洽的：当轨迹信息量大且时新时，学习效果会提升；但当奖励稀疏、陈旧，或容易被走捷径满足时，学习效果会退化。
      evidence:: E9, E10, E11, E12, E14
    - **可复现性缺口:** 论文声称代码和环境均可获取，并给出了模型家族、硬件级别、更新次数、rollout 数量以及主要超参数。未报告的内容包括：完整的随机种子协议、大多数曲线的误差棒、每个消融实验的确切重复次数，以及关于「不同环境各自的奖励实现如何影响推理轨迹」的完整说明。
      claim_kind:: analyst_assessment
- ## Technical Judgment
    - **站得住的结论:** 论文最出色的贡献在于它的诊断视角：它通过奖励变异性、熵、梯度范数以及定性的轨迹变化来展示崩溃，而不是只看最终的成功率。轨迹层面的抽象也与 LLM agent 十分契合，因为它把推理文本、可执行动作和环境反馈纳入了同一个优化对象。
      claim_kind:: analyst_assessment
      evidence:: E3, E7, E8
    - **可能失效之处:** 当奖励变异性不能很好地代表有用的学习信号时，StarPO-S 可能会失效，例如那些结果本身就天然高方差的环境、带有欺骗性奖励的环境，或者那些成功推理罕见但方差很低的任务。论文自身也指出，实验任务规模较小、缺少经验回放缓冲区（replay-buffer）的相关做法，并且没有涉及多模态任务，因此不应假定这套方法能原封不动地迁移到更复杂的 agent 上。
      claim_kind:: analyst_assessment
      evidence:: E9, E15
    - **与已有工作的关系:** 与面向静态大语言模型推理的 PPO 和 GRPO 相比，这项工作把优化的基本单位从单个答案转向了完整的交互轨迹。与 ReAct 风格「边推理边行动」提示这类智能体框架相比，它研究的是在环境奖励下的训练动态；与在轨迹上做监督微调相比，它在报告的 Sokoban 表现上更弱，但更聚焦于从自生成数据中学习。
      claim_kind:: analyst_assessment
      evidence:: E3, E6, E16
    - **可迁移启发:** 对于自我训练的智能体，训练数据生成器本身就是算法的一部分：采样了哪些状态、rollout（在环境中运行策略采样得到的一整段回合）多久刷新一次、保留了哪些不确定的样本，以及奖励是否能区分推理质量，这些因素可能和策略优化器同样重要。一个可复用的模式是：在扩大模型规模或引入更大的奖励模型之前，先对多样性和更新稳定性进行度量与监控。
      claim_kind:: analyst_assessment
      evidence:: E8, E11, E12, E14
- ## Glossary
  collapsed:: true
    - 强化学习（reinforcement learning，RL）：通过让策略尝试动作、并根据奖励信号更新策略来进行训练；在本文中，奖励大多来自任务的最终结果。
    - 大语言模型智能体（LLM agent）：把语言模型当作环境中的行动者：它观察状态文本、发出动作、接收反馈，并在多个回合中持续行动。
    - 马尔可夫决策过程（Markov Decision Process，MDP）：一个由状态、动作、转移动态和奖励构成的形式化交互循环；在这里之所以有用，是因为智能体的行为是随时间逐步展开的。
    - 轨迹（trajectory）：一整个回合的完整记录，包括初始状态、模型输出、奖励、后续状态以及最终结果。StarPO 把它当作学习的基本单位。
    - 状态-思考-动作-奖励策略优化（State-Thinking-Actions-Reward Policy Optimization，StarPO）：本文提出的轨迹级强化学习框架，用于优化多回合的大语言模型智能体交互。
    - StarPO-S：StarPO 的一个稳定化变体，采用基于不确定性的筛选、评论者或基线的选择，以及梯度整形等技术。
    - 回声陷阱（Echo Trap）：本文对一种坍缩现象的命名，指自生成数据的强化学习训练不断强化重复的推理模板，从而降低行为多样性。
    - 组相对策略优化（Group Relative Policy Optimization，GRPO）：一种无需评论者的策略优化方法，它把某条轨迹的奖励与来自同一采样组的奖励做归一化对比。
    - 近端策略优化（Proximal Policy Optimization，PPO）：一种策略梯度方法，它会对更新比率进行裁剪，并且通常借助一个经过训练的评论者（critic）来估计优势值。
    - rollout：通过在环境中运行当前策略或较早版本的策略，所生成的一段采样片段（episode）或一批片段。
    - 基于不确定性的筛选（uncertainty-based filtering）：保留那些重复 rollout 后奖励波动较大的提示（prompt），其假设是这类提示能提供更有信息量的学习信号。
    - think-answer 格式：一种结构化的输出格式，模型在 think 块内给出推理文本，在 answer 块内给出可执行的动作。
- ## Evidence Index
  collapsed:: true
    - **E1:** problem/paper_statement | Abstract | high
      locator:: abstract
      quote:: Training large language models (LLMs) as interactive agents presents unique challenges including long-horizon decision making and interacting with stochastic environment feedback. While reinforcement learning (RL) has enabled progress in static tasks, multi-turn agent RL training remains underexplored.
    - **E2:** method/paper_statement | Abstract | high
      locator:: abstract
      quote:: We propose StarPO (State-Thinking-Actions-Reward Policy Optimization), a general framework for trajectory-level agent RL, and introduce RAGEN, a modular system for training and evaluating LLM agents.
    - **E3:** algorithm/paper_statement | 2.2 StarPO | high
      locator:: section 2.2 and Figure 2
      quote:: StarPO treats the entire trajectory—including observations, reasoning traces, actions, and feedback—as a coherent unit for rollout and model optimization. The objective is to maximize expected trajectory reward.
    - **E4:** experiment_setup/paper_statement | 3. Experiment Setup | high
      locator:: sections 3.1-3.3
      quote:: We evaluate LLM agents on four environments spanning symbolic and realistic decision-making: Bandit tests risk-sensitive reasoning under noisy feedback; Sokoban requires irreversible symbolic planning; Frozen Lake combines planning with probabilistic transitions; and WebShop involves natural language grounding and web environment interaction.
    - **E5:** experiment_setup/paper_statement | 3. Experiment Setup | high
      locator:: section 3.2
      quote:: In our main experiments, we train Qwen-2.5 Instruct 0.5B models for three symbolic tasks and its 3B variant for the challenging WebShop. We also report various model performance in Appendix D.
    - **E6:** result/experiment_result | 4.1 Multi-turn Agent RL Training Introduces New Instability Pattern | medium
      locator:: section 4.1, Figures 3-4
      quote:: Vanilla adaptations from single-turn methods like PPO and GRPO achieve early gains in agent settings but often collapse. A critic in PPO may delay instability, but would not prevent reasoning degradation, highlighting the need for specialized stabilization in agent settings.
    - **E7:** result/case_study | 4.1 Multi-turn Agent RL Training Introduces New Instability Pattern | medium
      locator:: Finding 2 and Figure 4
      quote:: We find that early-stage agent respond with diverse symbolic reasoning, but collapse into deterministic, repetitive templates after training. Models converge to fixed phrasing, indicating that RL may reinforce superficial patterns instead of general reasoning and forms an "Echo Trap".
    - **E8:** result/experiment_result | 4.1 Multi-turn Agent RL Training Introduces New Instability Pattern | medium
      locator:: Finding 3 and Figure 4
      quote:: Reward standard deviation and entropy often fluctuate before performance degrades, while gradient norm spikes typically mark the point of irreversible collapse. These metrics provide early indicators and motivate the need for stabilization strategies.
    - **E9:** ablation/ablation | 4.2 StarPO-S | medium
      locator:: section 4.2 and Figure 5
      quote:: In PPO runs (Figure 5, left), filtering low-variability rollouts significantly delays collapse: retaining 75% of rollouts extends stability in FrozenLake from 100 to 140 steps, while 50% avoids collapse entirely.
    - **E10:** optimization/ablation | 4.2 StarPO-S | medium
      locator:: section 4.2 and Appendix D
      quote:: In addition to uncertainty-based filtering, we adopt two gradient shaping techniques inspired by DAPO designed for single-turn RL: KL Term Removal and Clip-Higher (Asymmetric Clipping). We extend and evaluate them in the multi-turn agent setting.
    - **E11:** ablation/ablation | 4.3 Generating Useful Trajectories for RL Training | medium
      locator:: section 4.3, Tables 1-2
      quote:: Diverse task instances enable better policy contrast and generalization across environments. Moderate action budgets provide enough planning space and avoid the noise introduced by overly long sequences. Up-to-date rollouts ensure optimization targets remain aligned with current policy behavior.
    - **E12:** ablation/ablation | 4.3 Generating Useful Trajectories for RL Training | medium
      locator:: section 4.3 and Figure 7
      quote:: As shown in Figure 7, agents trained with fresher rollouts (Online-1) achieve faster convergence and better generalization across tasks compared to those with delayed updates (e.g., Online-5 or Online-10).
    - **E13:** result/experiment_result | 4.4 Reasoning Improves Generalization | medium
      locator:: section 4.4, Tables 3-4
      quote:: As shown in Table 3, models trained with reasoning traces generalize better in Bandit and even in the counterintuitive BanditRev, suggesting that reasoning supervision helps internalize symbolic cues beyond memorization.
    - **E14:** result/experiment_result | 4.4 Reasoning Improves Generalization | medium
      locator:: section 4.4, Table 4 and Figure 14
      quote:: Even when the output format includes explicit <think> segments, removing them (no-think variant) often yields comparable or even better performance. To understand this degradation, we analyze average response length during training and find that reasoning traces consistently shrink over time.
    - **E15:** limitation/limitation | 6. Conclusions and Limitations | high
      locator:: section 6
      quote:: Limitations of our work include the focus on relatively small-scale tasks, the omission of established RL practices like replay buffers, and the absence of multimodal tasks—which we leave for future work.
    - **E16:** result/experiment_result | G. Comparing Agent RL with Supervised Fine-Tuning | medium
      locator:: appendix G
      quote:: SFT achieves 74.6% and 23% performance on Sokoban and Frozen Lake, respectively. Compared to the 20.3% and 21.8% performance with StarPO-S. The results indicate that SFT demonstrates superior performance to RL approaches.
