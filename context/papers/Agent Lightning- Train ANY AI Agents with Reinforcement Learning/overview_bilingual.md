- **Title:** Agent Lightning: Train ANY AI Agents with Reinforcement Learning
  **标题:** Agent Lightning：用强化学习训练任意 AI 智能体
- **Summary:** Agent Lightning turns existing agent executions into transition-level reinforcement-learning data so training can be separated from the agent framework and reused across heterogeneous agent workflows.
  **一句话总结:** Agent Lightning 把已有的智能体执行过程转化为「转移级」（transition-level）的强化学习数据，从而让训练与智能体框架相互解耦，并能在各种异构的智能体工作流之间复用。
- **Paper Type:** system
  **论文类型:** 系统类
- **Venue:** arXiv preprint 2025
  **发表:** arXiv 预印本 2025
- **Authors:** Xufang Luo, Yuge Zhang, Zhiyuan He, Zilong Wang, Siyun Zhao, Dongsheng Li, Luna K. Qiu, Yuqing Yang; Microsoft Research
  **作者:** Xufang Luo、Yuge Zhang、Zhiyuan He、Zilong Wang、Siyun Zhao、Dongsheng Li、Luna K. Qiu、Yuqing Yang；Microsoft Research
- **Keywords:** agent training, reinforcement learning, LLM agents, transition-based RL, training-agent disaggregation, observability
  **关键词:** 智能体训练、强化学习、大语言模型智能体、基于转移的强化学习、训练与智能体解耦、可观测性
- ## Orientation
    - **Background:** AI agents are programs that call a large language model (LLM), a text model that turns prompts into responses, and tools, ordinary functions or services that act outside the model. Training such agents means improving the model inside a running program, not only improving a standalone chat prompt.
      **背景:** AI 智能体是一类程序，它们会调用大语言模型（large language model，LLM，一种把提示词转换成回复的文本模型），也会调用工具（即在模型之外执行动作的普通函数或服务）。训练这样的智能体，指的是改进运行程序内部的模型，而不仅仅是改进一个独立的聊天提示词。
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A developer may already have an agent that searches, writes code, queries databases, or calls tools, and wants it to learn from success and failure without rewriting the whole agent inside a training system.
      **通俗问题:** 开发者可能已经有了一个能搜索、写代码、查询数据库或调用工具的智能体，并希望它能从成功和失败中学习，同时又不必把整个智能体重写进某个训练系统里。
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** The model may be called at different moments, see different context each time, and receive useful feedback only after the whole run finishes, while the surrounding program can branch, retry, or call tools.
      **为何困难:** 模型可能在不同的时刻被调用，每次看到的上下文都不同，而且往往要等整个运行结束后才能收到有用的反馈；与此同时，围绕模型的程序还可能出现分支、重试或调用工具。
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Record each model call with its visible input, generated output, and reward signal, then train from those records while leaving the original agent program in place.
      **一句话核心思路:** 把每一次模型调用记录下来，包括它可见的输入、生成的输出和奖励信号，然后基于这些记录进行训练，同时保持原有的智能体程序不变。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a systems view of reinforcement learning (RL), training by rewarding actions, for AI agents: it attacks the gap between real agent code and RL trainers that usually expect a simple prompt-response loop or a rebuilt rollout environment.
      **阅读价值:** 把本文当作面向 AI 智能体的强化学习（Reinforcement Learning，RL，即通过对动作给予奖励来训练）系统视角来读：它要解决的是真实智能体代码与强化学习训练器之间的落差——训练器通常只期望一个简单的「提示—回复」循环，或是一个重新搭建好的执行环境。
      claim_kind:: analyst_assessment
      evidence:: E2, E15
    - **One-Sentence Contribution:** Agent Lightning improves agent fine-tuning by recording each large language model (LLM), a text model that maps prompts to responses, call as a standalone training transition instead of forcing the whole agent run into one concatenated sequence.
      **一句话贡献:** Agent Lightning 改进了智能体微调的方式：它把每一次大语言模型（Large Language Model，LLM，一种把提示映射为回复的文本模型）调用记录为一条独立的训练转移，而不是强行把整个智能体的运行过程拼接成单一序列。
      evidence:: E1, E7
    - **Mental Model:** Picture the agent as a busy workshop: Agent Lightning puts a receipt on every model call, then trains from the receipts without moving the workshop into the trainer.
      **记忆模型:** 可以把智能体想象成一间繁忙的工坊：Agent Lightning 给每一次模型调用都开出一张收据，然后只依据这些收据来训练，而不用把整间工坊搬进训练器里。
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is breadth: the same framework is demonstrated on three agent frameworks and task types with improving reported reward curves, although without variance or repeat-count reporting.
      **最佳证据:** 最有力的证据在于其适用面之广：同一套框架在三种智能体框架和多种任务类型上都得到了验证，报告的奖励曲线也在持续上升；不过论文没有给出方差或重复运行次数。
      evidence:: E11, E12, E13, E14
        - Supports C1: LangChain text-to-SQL, OpenAI Agents SDK retrieval-augmented generation, and AutoGen calculator agents; different frameworks and datasets; qualitative integration claim; partial support because code-change amount is not measured.
          支持 C1：LangChain 的文本转 SQL、OpenAI Agents SDK 的检索增强生成，以及 AutoGen 的计算器智能体；涉及不同的框架和数据集；这是一个定性的集成论断；只算部分支持，因为没有测量代码改动量。
          evidence:: E11
        - Supports C4: Spider text-to-SQL with Llama-3.2-3B-Instruct; baseline step zero test reward 0.15; metric answer accuracy reward; final reported test reward 0.57; medium support due missing variance.
          支持 C4：用 Llama-3.2-3B-Instruct 完成 Spider 文本转 SQL 任务；起始（第 0 步）的测试奖励为 0.15；采用的指标是答案准确率奖励；最终报告的测试奖励为 0.57；由于缺少方差数据，只能算中等程度的支持。
          evidence:: E12
        - Supports C4: Calc-X math tool-use with AutoGen and calculator; baseline step zero test reward 0.05; metric answer accuracy reward; final reported test reward 0.77; medium support due missing repeat counts.
          支持 C4：用 AutoGen 加计算器完成 Calc-X 数学工具调用任务；起始（第 0 步）的测试奖励为 0.05；采用的指标是答案准确率奖励；最终报告的测试奖励为 0.77；由于缺少重复次数信息，只能算中等程度的支持。
          evidence:: E14
    - **Main Caveat:** The mechanism is convincing as a decoupling interface, but the reported algorithm uses equal final-return credit for every action and the evaluation does not isolate whether the interface, the runtime, or the RL update is responsible for each gain.
      **主要边界:** 作为一种解耦接口，这套机制是有说服力的；但论文报告的算法对每个动作都赋予相同的最终回报作为信用分配，而且评估过程并没有区分每一份收益究竟来自接口、运行时，还是强化学习的参数更新。
      claim_kind:: analyst_assessment
      evidence:: E8, E17
- ## Argument Map
    - **Problem and Stakes:** The paper targets the mismatch between reinforcement learning (RL), training policies from reward feedback, and deployed AI agents whose behavior depends on multiple model calls, tool calls, and framework-specific orchestration. The stakes are practical: if RL requires rebuilding every agent inside a trainer, agent learning remains brittle and hard to scale across real applications.
      **问题与重要性:** 这篇论文针对的是两者之间的错配：一边是强化学习（reinforcement learning，RL，即通过奖励反馈来训练策略），另一边是已部署的 AI 智能体，其行为取决于多次模型调用、工具调用以及各框架特有的编排逻辑。其中的现实意义在于：如果强化学习要求把每个智能体都在训练器内部重建一遍，那么智能体的学习就仍然脆弱，也难以在真实应用中大规模推广。
      evidence:: E2, E3
    - **Prior Gap:** Prior multi-turn RL work often packs a full interaction into one long sequence and uses masking, a rule that hides tokens from loss or attention, while many RL systems assume the trainer knows the agent's execution logic. Agent Lightning's gap claim is that this coupling is incompatible with diverse agents built in LangChain, OpenAI Agents SDK, AutoGen, or custom code.
      **已有方法缺口:** 以往的多轮强化学习工作，常常把一整段交互打包成一条长序列，并使用掩码（masking，即把某些 token 从损失或注意力中隐藏起来的规则）；同时，许多强化学习系统都假定训练器了解智能体的执行逻辑。Agent Lightning 指出的空白点在于：这种耦合方式无法适配用 LangChain、OpenAI Agents SDK、AutoGen 或自定义代码构建的各种各样的智能体。
      evidence:: E15, E1
    - **Key Insight:** The key insight is to treat agent execution as a partially observable Markov decision process (POMDP), where the model sees only part of the current program state, and to train from transitions, records of one model input, one output, and an assigned reward. This makes the learning interface independent of how the agent constructed that input.
      **关键洞见:** 核心洞见在于把智能体（agent）的执行过程看作一个部分可观测马尔可夫决策过程（partially observable Markov decision process，POMDP）：在这种模型里，大语言模型（LLM）只能看到当前程序状态的一部分。训练则基于「转移」（transition）来进行，每个转移是一条记录，包含一次模型输入、一次模型输出，以及为其分配的奖励。这样一来，学习接口就与智能体是如何构造那次输入无关了。
      evidence:: E4, E7
    - **Claims:** The paper's argument rests on four falsifiable claims about interface generality, algorithm compatibility, system integration, and empirical improvement.
      **核心主张:** 本文的论证建立在四项可证伪的主张之上，分别涉及接口的通用性、算法的兼容性、系统的集成方式，以及实证效果的提升。
      claim_kind:: analyst_assessment
        - C1: A unified transition interface decouples agent execution from RL training enough to support existing agents across multiple frameworks with almost no agent-code modification.
          C1：统一的转移接口把智能体执行与强化学习（reinforcement learning，RL）训练充分解耦，从而能够支持跨多个框架的现有智能体，且几乎不需要修改智能体代码。
          evidence:: E1, E10, E11, E18
        - C2: LightningRL can reuse existing single-turn LLM RL algorithms by assigning episode returns to per-call transitions and then letting the single-turn algorithm handle token-level updates.
          C2：LightningRL 可以复用现有的单轮 LLM 强化学习算法，做法是把整个回合（episode）的回报分配到每一次调用的转移上，然后交由单轮算法完成词元（token）级别的更新。
          evidence:: E7, E8, E9
        - C3: The Training-Agent Disaggregation architecture makes the trainer agent-agnostic and the client agent trainer-agnostic while still collecting traces, rewards, failures, and intermediate signals.
          C3：训练与智能体分离（Training-Agent Disaggregation）架构让训练器与具体智能体无关，也让客户端智能体与具体训练器无关，同时仍能采集执行轨迹、奖励、失败情况以及中间信号。
          evidence:: E10, E16
        - C4: Across text-to-SQL, retrieval-augmented generation, and calculator-assisted math QA, Agent Lightning produces continuous reported reward improvements from the same base LLM family.
          C4：在文本转 SQL（text-to-SQL）、检索增强生成（retrieval-augmented generation）以及借助计算器的数学问答（calculator-assisted math QA）这三类任务上，Agent Lightning 都能从同一个基础 LLM 家族出发，持续获得所报告的奖励提升。
          evidence:: E11, E12, E13, E14
- ## Mechanism and Design
    - **Core Mechanism:** Agent Lightning observes the agent at component boundaries: a state is the current program snapshot, semantic variables are the meaningful values used by model or tool calls, and each call records metadata, input, and output. For learning, it filters this richer trace down to policy-LLM transitions and rewards, which are the minimum data needed by the RL update.
      **核心机制:** Agent Lightning 在各组件的边界处观测智能体：一个「状态」是当前程序的快照，「语义变量」（semantic variable）是模型调用或工具调用所使用的有意义的值，每一次调用都会记录元数据、输入和输出。用于学习时，它会把这份更丰富的轨迹过滤为策略 LLM 的转移和奖励，也就是强化学习更新所需的最小数据。
      evidence:: E4, E5, E7
        - The unified interface keeps tool calls and model calls in the execution record, but the policy update can select only the transitions for the model or role being optimized.
          统一接口在执行记录中同时保留工具调用和模型调用，但策略更新可以只挑选出待优化的那个模型或角色所对应的转移。
          evidence:: E5, E7
        - Rewards can be terminal-only or intermediate; terminal-only feedback is treated as a valid special case rather than a separate interface.
          奖励既可以只在终止时给出，也可以是中间过程的奖励；仅终止时的反馈被当作一种合法的特例来处理，而不是另设一套独立接口。
          evidence:: E6
    - **Data / Control Flow:** The server receives tasks, exposes a task-specific OpenAI-like API endpoint to clients, the client runs the existing agent through that endpoint, captures traces and rewards, and returns transition data to the trainer for model updates. The updated model is then served back through the same API shape, closing the training loop without placing agent logic on GPU trainer machines.
      **数据/控制流:** 服务器接收任务，并向客户端暴露一个任务专属的、类似 OpenAI 风格的 API 端点；客户端通过该端点运行现有的智能体，捕获执行轨迹和奖励，再把转移数据返回给训练器以更新模型。更新后的模型随后仍以相同形态的 API 对外提供服务，从而闭合训练循环，同时无需把智能体逻辑放到 GPU 训练机器上。
      evidence:: E10, E16
        - Task batches are dispatched from the Lightning Server to available Lightning Clients, so rollout work can be spread across client workers and machines.
          任务批次由 Lightning Server 分发到可用的 Lightning Client，这样就能把 rollout（采样交互）的工作分散到多个客户端工作进程和多台机器上。
          evidence:: E10, E16
        - Trace capture can use OpenTelemetry, an observability standard for recording distributed execution events, AgentOps, or a lightweight tracer embedded in the model API endpoint.
          轨迹采集可以使用 OpenTelemetry（一套用于记录分布式执行事件的可观测性标准）、AgentOps，或者嵌入在模型 API 端点里的轻量级追踪器。
          evidence:: E16
        - LightningRL groups transitions for the same task when adapting value-free methods such as Group Relative Policy Optimization (GRPO), which estimates advantages by comparing sampled responses for the same prompt.
          在适配无价值函数方法（如群体相对策略优化，Group Relative Policy Optimization，GRPO）时，LightningRL 会把属于同一任务的转移（transition）归为一组；GRPO 通过对比针对同一提示词采样得到的多个回答来估计优势值。
          evidence:: E8
    - **Design Decisions:** The main design choice is transition decomposition instead of whole-trajectory concatenation: it preserves the agent's natural context construction and avoids custom masking while accepting a simpler, currently coarse credit-assignment rule. The system choice is disaggregation: keep heavy LLM training in the RL framework and keep flexible application logic in the client runtime.
      **设计决策:** 主要的设计选择是采用转移分解，而不是把整条轨迹拼接在一起：这样能保留智能体自然的上下文构建方式，避免使用自定义掩码（masking），代价是接受一种更简单、目前也较为粗糙的信用分配（credit assignment）规则。系统层面的选择是解耦（disaggregation）：把繁重的大语言模型训练留在强化学习框架里，把灵活的应用逻辑留在客户端运行时中。
      evidence:: E8, E9, E10
        - Need: avoid coupling to framework-specific agent traces; choice: train on per-call transitions; alternative: concatenate turns and mask; tradeoff: easier integration but credit assignment becomes an explicit module.
          需求：避免与特定框架的智能体轨迹绑定；选择：按每次调用的转移进行训练；替代方案：把多轮对话拼接起来并加掩码；权衡：集成更容易，但信用分配变成了一个需要显式实现的独立模块。
          evidence:: E8, E9, E15
        - Need: make existing single-turn RL algorithms usable; choice: assign the same final return to each action in the current implementation; alternative: learned or heuristic high-level value functions; tradeoff: simple and tested, but weak for long-horizon blame assignment.
          需求：让现有的单轮强化学习算法能够复用；选择：在当前实现中，给每个动作分配相同的最终回报；替代方案：使用学习得到的或基于启发式的高层价值函数；权衡：简单且经过验证，但在长时程的责任归属上表现较弱。
          evidence:: E8, E17
        - Need: collect traces without invasive changes; choice: reuse observability instrumentation and an API tracer; alternative: framework-specific logging adapters; tradeoff: broad coverage, but trace quality depends on instrumentation and endpoint discipline.
          需求：在不做侵入式改动的前提下采集轨迹；选择：复用可观测性埋点和一个 API 追踪器；替代方案：为特定框架编写日志适配器；权衡：覆盖范围广，但轨迹质量取决于埋点情况和端点的规范程度。
          evidence:: E16
    - **Implementation Surface:** The exposed surface is a Lightning Server tied to an RL framework, a Lightning Client wrapping the agent runtime, an OpenAI-like model API, trace capture, task upload, worker parallelism, error handling, and optional Automatic Intermediate Rewarding (AIR), which turns monitoring events into intermediate reward signals. Appendix code sketches an adapter script rather than a rewrite of the original agent.
      **实现边界:** 对外暴露的接口包括：与强化学习框架绑定的 Lightning Server、封装智能体运行时的 Lightning Client、类似 OpenAI 的模型 API、轨迹采集、任务上传、工作进程并行、错误处理，以及可选的自动中间奖励（Automatic Intermediate Rewarding，AIR），后者把监控事件转化为中间奖励信号。附录中的代码给出的是一个适配脚本的示意，而不是对原始智能体的重写。
      evidence:: E10, E16, E18
- ## Evaluation and Evidence
    - **Setup:** The evaluation uses three agent scenarios: Spider text-to-SQL with LangChain and an SQL executor, MuSiQue open-domain QA with OpenAI Agents SDK and a Wikipedia retriever, and Calc-X math QA with AutoGen and a calculator. All reported experiments use Llama-3.2-3B-Instruct as the base model, with different reward definitions per task.
      **实验设置:** 评估使用了三个智能体场景：基于 LangChain 和 SQL 执行器的 Spider 文本转 SQL 任务、基于 OpenAI Agents SDK 和维基百科检索器的 MuSiQue 开放域问答任务，以及基于 AutoGen 和计算器的 Calc-X 数学问答任务。所有报告的实验都以 Llama-3.2-3B-Instruct 作为基础模型，每个任务采用不同的奖励定义。
      evidence:: E11, E12, E13, E14
    - **Claim-Evidence Matrix:** C1 and C3 are mainly supported by system design plus cross-framework demonstrations; C2 is supported by the formal data extraction and LightningRL description; C4 is supported by reward curves. The evidence is strongest for feasibility and weakest for causal attribution because no ablation separates interface, algorithm, and runtime effects.
      **主张-证据矩阵:** 论点 C1 和 C3 主要由系统设计以及跨框架的演示来支撑；C2 由形式化的数据抽取和 LightningRL 的描述来支撑；C4 由奖励曲线来支撑。这些证据对「可行性」的支撑最强，对「因果归因」的支撑最弱，因为没有任何消融实验能把接口、算法和运行时三者的作用分离开来。
      claim_kind:: analyst_assessment
      evidence:: E7, E8, E10, E11, E12, E13, E14
        - Supports C1: framework diversity and adapter-style appendix support the decoupling claim, but the paper does not quantify code modifications.
          支持 C1：框架多样性以及附录中的适配器式方案支持了解耦这一论点，但论文没有量化代码修改量。
          claim_kind:: analyst_assessment
          evidence:: E1, E11, E18
        - Supports C2: transition extraction and LightningRL explain how single-turn methods are reused, but the current identical-credit rule leaves long-horizon credit quality under-tested.
          支持 C2：转移记录（transition）的提取和 LightningRL 说明了如何复用单轮方法，但当前采用的等额信用规则使得长程信用分配的质量缺乏充分测试。
          claim_kind:: analyst_assessment
          evidence:: E7, E8, E17
        - Supports C4: all three tasks show improved reported test rewards, but the paper does not report confidence intervals, seeds, or variance.
          支持 C4：三个任务报告的测试奖励都有所提升，但论文没有报告置信区间、随机种子或方差。
          claim_kind:: analyst_assessment
          evidence:: E12, E13, E14
    - **Headline Results:** Text-to-SQL test reward improves from 0.15 to 0.57, RAG test reward from 0.005 to 0.230, and calculator QA test reward from 0.05 to 0.77 in the reported curves. These are directional improvements, not statistically established effect sizes, because uncertainty and repeat counts are not reported.
      **关键结果:** 在报告给出的曲线中，Text-to-SQL 的测试奖励从 0.15 提升到 0.57，RAG 的测试奖励从 0.005 提升到 0.230，计算器问答（calculator QA）的测试奖励从 0.05 提升到 0.77。这些只是方向性的提升，而非在统计上确立的效应量，因为论文没有报告不确定性和重复次数。
      evidence:: E12, E13, E14
        - Supports C4: Spider; LangChain; answer accuracy reward; 0.15 to 0.57 on test reward; caveat: no variance or baseline trainer comparison beyond the training trajectory.
          支持 C4：Spider；LangChain；以答案准确率作为奖励；测试奖励从 0.15 提升到 0.57；注意：除训练轨迹外，没有方差或基线训练器的对比。
          evidence:: E12
        - Supports C4: MuSiQue over Wikipedia; OpenAI Agents SDK; 0.9 correctness plus 0.1 format reward; 0.005 to 0.230 on test reward; caveat: plateau and oscillation after early gains.
          支持 C4：在 Wikipedia 上运行的 MuSiQue；OpenAI Agents SDK；奖励为 0.9 的正确性加 0.1 的格式；测试奖励从 0.005 提升到 0.230；注意：早期提升后出现平台期和震荡。
          evidence:: E13
        - Supports C4: Calc-X; AutoGen plus calculator; answer-accuracy reward; 0.05 to 0.77 on test reward; caveat: no ablation showing whether tool-call formatting or reasoning improved most.
          支持 C4：Calc-X；AutoGen 加计算器；以答案准确率作为奖励；测试奖励从 0.05 提升到 0.77；注意：没有消融实验说明工具调用格式和推理这两项中哪一项提升最大。
          evidence:: E14
    - **Ablations and Sensitivity:** Not reported: the paper does not include ablations for equal versus learned credit assignment, transition decomposition versus masking under matched trainers, AIR on/off, telemetry method, worker scaling, or reward-weight sensitivity.
      **消融与敏感性:** 未报告：论文没有针对以下方面的消融实验：等额信用分配与学习得到的信用分配的对比、在相同训练器下转移记录（transition）分解与掩码（masking）的对比、AIR 开启与关闭的对比、遥测方法、worker 数量的扩展，以及奖励权重的敏感性。
      claim_kind:: analyst_assessment
    - **Reproducibility Gaps:** The paper reports a GitHub repository, public datasets, base model, frameworks, tools, and an appendix adapter pattern, which lowers reuse friction. Missing trust fields include hardware budget, trainer hyperparameters, seeds, repeats, variance, exact train/test splits after task preprocessing, and stable API guarantees.
      **可复现性缺口:** 论文提供了 GitHub 代码仓库、公开数据集、基础模型、框架、工具，以及附录中的适配器模式，这降低了复用的门槛。缺失的可信度信息包括硬件预算、训练器超参数、随机种子、重复次数、方差、任务预处理后精确的训练/测试划分，以及稳定的 API 保证。
      claim_kind:: analyst_assessment
      evidence:: E1, E11, E18
- ## Technical Judgment
    - **What Holds Up:** The strongest part is the interface argument: per-call transitions are the right abstraction for agents whose context is built by arbitrary code, and the server-client split cleanly matches the different operational needs of trainers and agent runtimes. The cross-framework experiments support feasibility even if they do not prove optimality.
      **站得住的结论:** 最有说服力的部分是关于接口的论证：对于上下文由任意代码构建的智能体来说，以每次调用为单位的转移记录（transition）是恰当的抽象；而服务器-客户端的拆分正好契合了训练器与智能体运行时各自不同的运行需求。跨框架实验证明了可行性，即便它们没有证明最优性。
      claim_kind:: analyst_assessment
      evidence:: E7, E9, E10, E11
    - **Where It May Fail:** The approach may weaken when long-horizon tasks require precise blame assignment across many calls, when rewards are too sparse for equal final-return assignment, or when the agent's important state is not visible in captured model inputs and telemetry. It may also face engineering limits when tools or environments are slow, flaky, stateful, or hard to instrument.
      **可能失效之处:** 当长时程任务需要在众多调用之间进行精确的责任归属时，当奖励过于稀疏、以致无法采用「均等最终回报分配」的方式时，或当智能体的重要状态在所捕获的模型输入与遥测数据中不可见时，该方法的效果可能会减弱。此外，当工具或环境运行缓慢、不稳定、带有状态或难以插桩时，它还可能遇到工程上的限制。
      claim_kind:: analyst_assessment
      evidence:: E6, E8, E16, E17
    - **Relation to Other Work:** Compared with concatenation-and-masking multi-turn RL, Agent Lightning shifts the unit of training from a whole dialogue trace to a per-call transition, trading sequence-level simplicity for cleaner integration with arbitrary agent workflows. Compared with large-scale RL systems such as verl, OpenRLHF, TRL, ROLL, and AReaL, its novelty is less the trainer and more the boundary that lets existing agents act as rollout producers.
      **与已有工作的关系:** 与「拼接加掩码」式的多轮强化学习（RL）相比，Agent Lightning 把训练的单元从整段对话轨迹转变为单次调用的转移（transition），用序列级别的简洁性换取了与任意智能体工作流更清晰的集成。与 verl、OpenRLHF、TRL、ROLL、AReaL 等大规模强化学习系统相比，它的创新之处不在于训练器本身，而在于它划定的那条边界，使现有智能体能够充当轨迹采样（rollout）的产出方。
      claim_kind:: analyst_assessment
      evidence:: E8, E9, E15
    - **Transferable Lesson:** For learning over complex software systems, first choose the smallest stable observation boundary that preserves the decision and reward, then make the trainer consume that boundary instead of importing the whole application. This pattern generalizes beyond agent RL to prompt optimization, tool-policy learning, and other program-level feedback loops.
      **可迁移启发:** 对于在复杂软件系统上进行学习的场景，应先选择能保留决策与奖励的最小且稳定的观测边界，然后让训练器只消费这条边界，而不是把整个应用都导入进来。这一模式的适用范围不止于智能体强化学习，还能推广到提示词优化、工具策略学习，以及其他程序级别的反馈闭环。
      claim_kind:: analyst_assessment
      evidence:: E4, E7, E10, E17
- ## Glossary
  collapsed:: true
    - AI agent: A software system that calls one or more LLMs and may also call tools, APIs, databases, or environments while solving a task.
      AI 智能体（AI agent）：一种软件系统，它在完成任务的过程中会调用一个或多个大语言模型（LLM），也可能调用工具、API、数据库或环境。
    - Reinforcement learning: A training paradigm where a policy improves by receiving scalar rewards for actions rather than step-by-step labels.
      强化学习（Reinforcement learning，RL）：一种训练范式，其中策略通过为动作接收标量奖励来改进，而不是依赖逐步给出的标注。
    - Transition: In this paper, the learning record for one policy-LLM call: the current input or observation, the model output as action, and an assigned reward.
      转移（Transition）：在本文中，指单次策略-LLM 调用的学习记录，包括当前的输入或观测、作为动作的模型输出，以及分配到的奖励。
    - Markov Decision Process: A decision model with state, action, transition, and reward; the paper uses a partially observable version because the LLM only sees the input context, not the full program state.
      马尔可夫决策过程（Markov Decision Process，MDP）：一种包含状态、动作、转移与奖励的决策模型；本文使用的是部分可观测的版本，因为大语言模型（LLM）只能看到输入上下文，而看不到完整的程序状态。
    - Semantic variable: A meaningful program value, such as a user query, generated SQL, retrieved passages, or answer, that is used or modified by an LLM or tool call.
      语义变量（Semantic variable）：一个有意义的程序值，例如用户查询、生成的 SQL、检索到的段落或答案，它会被某次 LLM 或工具调用使用或修改。
    - Credit assignment: The problem of deciding which earlier action deserves how much responsibility for a later reward; Agent Lightning currently uses equal final-return assignment.
      责任归属（Credit assignment）：指判定较早的某个动作应为后来的某项奖励承担多少责任的问题；Agent Lightning 目前采用「均等最终回报分配」的做法。
    - LightningRL: The paper's hierarchical RL method: assign episode return across LLM-call transitions, then use existing single-turn LLM RL methods for token-level optimization.
      LightningRL：本文提出的分层强化学习方法，先把整段任务（episode）的回报分配到各次 LLM 调用的转移上，再使用现有的单轮 LLM 强化学习方法进行词元（token）级别的优化。
    - Group Relative Policy Optimization: A value-free LLM RL method that estimates advantages by comparing multiple sampled outputs for the same task or prompt.
      群体相对策略优化（Group Relative Policy Optimization）：一种无需价值函数的大语言模型强化学习方法，它通过比较针对同一任务或提示（prompt）采样得到的多个输出来估计优势值。
    - Masking: A training technique that hides selected tokens from loss or attention; the paper argues custom masks are brittle for heterogeneous agent traces.
      掩码（Masking）：一种训练技术，用于在损失计算或注意力中隐藏选定的词元（token）；本文认为，对于异构的智能体执行轨迹，自定义掩码是很脆弱的。
    - Training-Agent Disaggregation: A system architecture that keeps RL training and GPU model serving on the server side while existing agent logic and tools run in client runtimes.
      训练-智能体解耦（Training-Agent Disaggregation）：一种系统架构，把强化学习训练和 GPU 上的模型服务放在服务器端，同时让已有的智能体逻辑与工具在客户端运行时中运行。
    - OpenTelemetry: An observability standard used to capture execution traces; Agent Lightning reuses it to collect agent trajectories without rewriting agent logic.
      OpenTelemetry：一种用于捕获执行轨迹的可观测性标准；Agent Lightning 复用它来收集智能体的运行轨迹，而无需重写智能体逻辑。
    - Automatic Intermediate Rewarding: A mechanism that converts monitoring signals, such as tool-call success or failure, into intermediate rewards for agent training.
      自动中间奖励（Automatic Intermediate Rewarding）：一种机制，把监控信号（例如工具调用的成功或失败）转化为智能体训练中的中间奖励。
- ## Evidence Index
  collapsed:: true
    - **E1:** method/paper_statement | Abstract | high
      locator:: Abstract, opening paragraph
      quote:: The abstract presents Agent Lightning as a framework for RL-based training of LLMs in arbitrary agents, emphasizing decoupled agent execution and training, integration with LangChain, OpenAI Agents SDK, AutoGen, and near-zero code modifications.
    - **E2:** problem/paper_statement | 1 Introduction | high
      locator:: Introduction, challenge paragraph
      quote:: The introduction contrasts static single-call RL settings with agents whose executions include multiple LLM invocations, distinct prompts and responses, external tools, APIs, environments, and diverse application-specific designs.
    - **E3:** background/paper_statement | 2 Modern AI Agents | high
      locator:: Sections 2.1-2.3
      quote:: The paper defines an AI agent broadly as software that includes LLM calls, built from models and tools, with orchestration that may be dynamic and implemented through frameworks or from scratch.
    - **E4:** insight/paper_statement | 3.1 Unified Data Interface | high
      locator:: Section 3.1, first two paragraphs
      quote:: Agent Lightning treats software execution as graph-like but argues that parsing a full execution graph is difficult and unnecessary; for RL it is enough to identify state and calls that drive state transitions.
    - **E5:** formula/paper_statement | 3.1.1 State and Call | high
      locator:: Section 3.1.1, equations for state and call
      quote:: State is described as a snapshot of execution variables, while a call contains metadata, input, and output for a component invocation, where the component can be an LLM or a tool.
    - **E6:** method/paper_statement | 3.1.2 Reward and Dataset | high
      locator:: Section 3.1.2
      quote:: Each execution is augmented with scalar rewards for component invocations; rewards may appear at intermediate steps or only at the end, with terminal-only rewards treated as a special case.
    - **E7:** algorithm/paper_statement | 3.2.2 Data Extraction for RL | high
      locator:: Section 3.2.2, extraction equations and summary paragraph
      quote:: For RL, the paper extracts only policy-LLM inputs, outputs, and rewards from executions, intentionally ignoring the detailed reasons and sources that constructed each input in the dynamic agent logic.
    - **E8:** algorithm/paper_statement | 3.3.2 Extend to Agent Scenarios via LightningRL | high
      locator:: Section 3.3.2, first mechanism paragraphs
      quote:: LightningRL decomposes trajectories into transitions, assigns episode-level return across actions with a credit assignment module, then relies on existing single-turn RL methods for token-level learning; the implementation assigns the same final return to each action.
    - **E9:** system_design/paper_statement | 3.3.2 Extend to Agent Scenarios via LightningRL | high
      locator:: Section 3.3.2, advantages over masking paragraphs
      quote:: The paper argues that transition data allows flexible observations, avoids concatenation-and-masking, avoids positional-continuity issues from masked sequences, and reduces excessively long contexts by breaking long trajectories into transition batches.
    - **E10:** system_design/implementation_detail | 3.4.1 Training-Agent Disaggregation Architecture | high
      locator:: Section 3.4.1 and Figure 4
      quote:: The system separates trainer and rollout-agent execution: the RL framework manages the model and exposes an OpenAI-like API, while client-side agent logic and tools run independently and report traces back to the server.
    - **E11:** experiment_setup/paper_statement | 4 Results | high
      locator:: Table 1 and task introductions
      quote:: The experiments cover text-to-SQL with LangChain on Spider, open-domain question answering with the OpenAI Agents SDK on MuSiQue, and math question answering with AutoGen on Calc-X, all using Llama-3.2-3B-Instruct.
    - **E12:** result/experiment_result | 4.1 Text-to-SQL via LangChain | medium
      locator:: Section 4.1 and Figure 5
      quote:: In Spider text-to-SQL, the paper reports a three-agent LangChain workflow, tunes SQL writing and rewriting agents, and shows test reward moving from 0.15 at step 0 to 0.57 at step 432.
    - **E13:** result/experiment_result | 4.2 Retrieval-Augmented Generation via OpenAI Agents SDK | medium
      locator:: Section 4.2 and Figure 6
      quote:: In MuSiQue retrieval-augmented generation over Wikipedia, the reward combines word-level F1 and format compliance; the test curve rises from 0.005 at step 0 to 0.230 at step 200.
    - **E14:** result/experiment_result | 4.3 Math QA with Tool Usage via AutoGen | medium
      locator:: Section 4.3 and Figure 7
      quote:: In Calc-X math tool-use, the AutoGen agent decides calculator calls and integrates tool outputs; the reported test reward rises from 0.05 at step 0 to 0.77 by later checkpoints.
    - **E15:** prior_work/paper_statement | 5.1 Related Work | high
      locator:: Related Work, multi-turn RL and RL systems paragraphs
      quote:: The related-work section says many multi-turn RL approaches concatenate turns and add masks, while RL training systems often require agent execution logic to be rebuilt or coupled inside the training framework.
    - **E16:** implementation/implementation_detail | 3.4.2 Agent Runtime | high
      locator:: Agent Runtime, data capture and robustness paragraphs
      quote:: The client runtime captures traces through OpenTelemetry and AgentOps or a lightweight API-endpoint tracer, supports concurrent workers across machines, handles failed tasks, and can convert monitoring signals into intermediate rewards.
    - **E17:** limitation/limitation | 5.2 Future Work | medium
      locator:: Future Work, optimization methods and RL algorithms
      quote:: The future-work section points to more optimization methods, long-horizon credit assignment, exploration, off-policy algorithms, and further system disaggregation, implying these areas are not fully solved in the current work.
    - **E18:** implementation/implementation_detail | Appendix A | medium
      locator:: Appendix A, training script note
      quote:: The appendix gives a minimal training-script pattern using Client, Resource, and Task, and notes that the open-source API may change, directing readers to the GitHub repository for current details.
