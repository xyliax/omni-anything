- **标题:** ProRL Agent：面向多轮 LLM 智能体强化学习训练的「rollout 即服务」（Rollout-as-a-Service）
- **一句话总结:** ProRL Agent 把多步智能体的训练轨迹（rollout）做成一个独立的 HTTP 服务，让强化学习训练器无需自行管理智能体的执行生命周期，就能使用运行在沙盒中、会调用工具的智能体。
- **论文类型:** 系统类
- **发表:** arXiv 预印本 2026（arXiv:2603.18815v1）
- **作者:** Hao Zhang、Mingjie Liu、Shaokun Zhang、Songyang Han、Jian Hu、Zhenghui Jin、Yuchi Zhang、Shizhe Diao、Ximing Lu、Binfeng Xu、Zhiding Yu、Jan Kautz、Yi Dong；所提供文本中未给出所属机构。
- **关键词:** 智能体强化学习、rollout 即服务、多轮 LLM 智能体、沙盒执行、高性能计算（HPC）部署、强化学习基础设施
- ## Orientation
    - **背景:** 在智能体强化学习（agent reinforcement learning，指让模型在环境中行动、观察结果、获得奖励并据此更新策略的训练方式）中，模型通过尝试任务、使用工具并接收奖励来学习。一次 rollout 就是一次完整的尝试：模型采取行动、看到结果、再次尝试，并留下可供训练学习的轨迹。
      claim_kind:: analyst_assessment
    - **通俗问题:** 训练器想要大量完成的练习尝试，但每次尝试都可能需要一个全新的工作空间、shell 命令、网络搜索、代码执行以及一次最终检查。
      claim_kind:: analyst_assessment
    - **为何困难:** 行动这一侧要等待文件、容器、工具和测试，而学习这一侧则希望 GPU 持续稳定地干活；把两者绑在一起，会让双方都更难扩展、更难改动。
      claim_kind:: analyst_assessment
    - **一句话核心思路:** 把杂乱的行动循环放到一个服务边界之后，这样训练器只需请求完成的尝试，而不必自己管理每一次工具交互。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **阅读价值:** 把它当作一篇关于智能体强化学习的系统论文来读：它针对的是 GPU 密集的策略训练与缓慢、工具密集的智能体执行之间的工程鸿沟——现有框架把过多的 rollout 控制权留在了训练器内部。
      claim_kind:: analyst_assessment
      evidence:: E3, E4
    - **一句话贡献:** ProRL Agent 改进了多轮大语言模型（LLM）智能体的强化学习：它把完整的 rollout 生命周期挪进一个独立的 HTTP 服务，由该服务把已完成的轨迹（trajectory）和奖励返回给任意训练器。
      evidence:: E5
    - **记忆模型:** 可以把训练器想象成一间只负责点成品菜的厨房：rollout 服务负责运转备料台、工具、清理和试味等所有环节，然后把一份已经评分的菜谱轨迹交回来。
      claim_kind:: analyst_assessment
    - **最佳证据:** 最有力的证据是多方面结果的组合：在 SWE-Bench Verified 上的端到端训练收益、跨领域的学习曲线、节点扩展（node-scaling）测量结果，以及各组件的消融实验。
      evidence:: E15, E16, E17, E18
        - 支持 C4：在 SkyRL-v0 SWE-Gym 子集上对 Qwen3 8B 进行软件工程训练；最接近的前作 SkyRL-Agent-8B-v0 在 SWE-Bench Verified 上报告为 9.4；ProRL Agent-8B 报告为 18.0；证据强度为中等，因为文中没有报告重复次数与不确定性。
          evidence:: E15
        - 支持 C4：在不同的工具配置与奖励设置下训练了 STEM、数学和代码三类智能体；从初始到最终的指标在这三条曲线上都有所提升；证据强度为中等，因为这些曲线没有把基础设施的作用与任务方案的作用区分开。
          evidence:: E16
        - 支持 C2：14B 模型在 DAPO 下、启用全部组件时的 rollout 吞吐为 0.37 实例/秒，而不做负载均衡时为 0.25，不启用 Efficient Bash 时为 0.29，不做过期任务清理时为 0.30；证据强度为中等，因为文中没有报告方差。
          evidence:: E18
    - **主要边界:** 这个系统边界很有说服力，但论文大多只报告单次运行的汇总结果；它没有把服务架构的作用与 ProRL 方案、DAPO 调度、任务设计以及硬件预算的作用分离开。
      claim_kind:: analyst_assessment
      evidence:: E14, E15, E18
- ## Argument Map
    - **问题与重要性:** 多轮大语言模型智能体（指通过反复进行工具行动与观察来解决任务的模型）让基于可验证奖励的强化学习变得更难，因为每个训练样本都需要一次很长的 rollout（即一次完整的任务尝试，包含与环境的交互以及最终打分）。论文把 rollout 生成刻画为一个系统瓶颈，因为在训练器能够更新策略之前，它要处理异构的沙箱、不稳定的工具延迟以及延迟到来的反馈。
      evidence:: E2, E3
    - **已有方法缺口:** 论文指出的差距不在于以往工作缺少工具或环境，而在于 rollout 的编排仍然嵌在训练器进程或训练器自有的库中，因此更换训练器、环境或运行时约束时，都需要移植执行逻辑。表 1 从三个维度把 ProRL Agent 与 SkyRL-Agent、VeRL-Tool、Agent Lightning、rLLM 和 GEM 区分开来：训练与 rollout 的解耦、无 root 权限的沙箱，以及脚手架无关性。
      evidence:: E4
    - **关键洞见:** 本文的核心洞见是把 rollout（智能体与环境交互并产生轨迹的一次完整尝试）当作「推理即服务」来处理：训练器通过 HTTP 发送任务实例，接收带有词元级别（token-level）的完整轨迹和奖励，而另一个独立的服务器负责沙盒环境（sandbox）的搭建、智能体执行、工具调用、结果评估以及大语言模型推理的协调。这一边界与实际运行中的分工相吻合，也就是把偏重 I/O 的 rollout 工作与偏重 GPU 的策略优化分开。
      evidence:: E5, E3
    - **核心主张:** 本文的论证可以归结为四个可证伪的主张，分别涉及服务边界、运行时设计、词元保真度以及训练与系统层面的结果。
      claim_kind:: analyst_assessment
        - C1：rollout 即服务（rollout-as-a-service）的边界可以把智能体执行与强化学习训练器解耦，同时不会丢失训练器进行策略更新所需的信息。
          evidence:: E5, E11
        - C2：一个实用的服务需要具备可插拔的任务生命周期、无 root 权限的沙盒运行时、各 rollout 阶段相互独立的工作进程池，以及可控的大语言模型后端管理。
          evidence:: E6, E7, E9, E10
        - C3：采用「词元进、词元出」（token-in/token-out）的通信方式，也就是以词元 ID 而非文本作为轨迹的标准表示，能够避免 rollout 与训练之间出现重新分词漂移（re-tokenization drift）。
          evidence:: E11
        - C4：该基础设施能够支撑软件工程、STEM、数学和编程等任务上有效的端到端强化学习，同时提升 rollout 的吞吐，并从所提出的各个系统组件中获益。
          evidence:: E15, E16, E17, E18
- ## Mechanism and Design
    - **核心机制:** ProRL Agent 是一个 rollout 服务器：它是一个 HTTP 服务，接收一个任务实例，将其分派给对应任务的处理器，在沙盒中运行智能体，评估结果，然后返回轨迹和奖励。训练器仍然负责策略优化，而该服务负责整个「行动」的生命周期。
      evidence:: E5, E6
        - 与具体任务相关的逻辑都封装在 AgentHandler 之后，这是一个接口，其 init、run 和 eval 三个方法分别用于准备环境、驱动多轮智能体循环，以及计算奖励。
          evidence:: E6
        - 服务器将这些生命周期阶段映射到彼此独立的工作进程池，因此容器启动、智能体执行和结果评估可以在不同任务之间重叠进行。
          evidence:: E9
        - 大语言模型的推理后端由该服务动态管理，并按分配数量使用最小堆（min-heap）进行路由，从而把任务分散到已注册的各个服务器上。
          evidence:: E10
    - **数据/控制流:** 训练器（trainer）发送一个包含任务实例和采样参数的处理请求，服务端依次经过 init（初始化）、run（运行）、eval（评估）三个阶段把作业排入队列处理，发起 HTTP 调用的一方最终收到完成的轨迹（trajectory）和评估结果。在 run 阶段，prompt_ids 和 response_ids 以 token ID（词元编号）的形式保存模型可见的对话内容，同时把环境产生的新观测分词后追加进去。
      evidence:: E5, E9, E11
        - init 阶段负责准备沙盒（sandbox）运行时和任务配置，这样环境的启动就成了服务端的职责，而不再由训练器代码处理。
          evidence:: E6, E7
        - run 阶段交替执行模型的文本补全和工具动作；高效的 Bash、直接调用 IPython 以及 Unix 域套接字（Unix domain sockets）共同降低了沙盒内每个动作的开销。
          evidence:: E8
        - eval 阶段在 rollout（一次完整的智能体交互过程）结束后为任务打分，同时各阶段专属的异常回调和最终的序列化处理确保失败的作业不会阻塞共享的流水线。
          evidence:: E6, E12
    - **设计决策:** 系统反复选择让某个狭窄的生命周期负责方各司其职，而不是大改整个框架：任务逻辑由各个处理器（handler）负责，隔离由 SingularityRuntime 负责，并发由分阶段的队列负责，策略的时效性由后端注册接口（API）负责。这些选择换来了可移植性和各部分独立扩展的能力，代价是需要更显式地管理服务状态。
      claim_kind:: analyst_assessment
      evidence:: E5, E7, E9, E10
        - 需求：在共享集群上支持多种异构任务；选择：采用 SingularityRuntime，具备无根（rootless）执行、回环 IP 分配、fakeroot 以及可选的网络隔离；替代方案：以 Docker 为核心的沙盒；权衡：这种设计更契合高性能计算（HPC）场景，但依赖于兼容 Singularity 的镜像和集群策略。
          claim_kind:: analyst_assessment
          evidence:: E7
        - 需求：避免某个作业工作进程在缓慢且互不匹配的阶段之间空等；选择：使用相互独立的 init、run、eval 三个进程池；替代方案：由单个工作进程负责一个完整作业的全过程；权衡：当各队列负载均衡时吞吐会提升，但运维人员必须根据实际工作负载来确定各进程池的规模。
          claim_kind:: analyst_assessment
          evidence:: E9
        - 需求：保留用于计算对数概率的那条精确序列；选择：以 token ID（词元编号）作为权威表示；替代方案：传递文本，再在训练器中重新分词；权衡：这样保真度更强，但也与推理返回结果的分词兼容性更紧密地耦合在一起。
          claim_kind:: analyst_assessment
          evidence:: E11
    - **实现边界:** 对外暴露的接口刻意保持精简：HTTP 端点用于提交和取消作业、注册或清除 LLM（大语言模型）服务器、启动或停止服务器，以及上报状态。客户端一侧的训练器集成在此基础上加入了考虑数据局部性的 LLM 服务器分配，以及 DAPO（动态采样策略优化，Dynamic Sampling Policy Optimization）为有信息量的提示补充样本的逻辑。
      evidence:: E10, E12, E13
        - 后端的注册与清除功能让训练器可以在不重启 rollout 服务器的情况下更换模型检查点（checkpoint），从而使后续作业都使用更新后的 LLM 端点。
          evidence:: E10
        - 取消操作会把任务标记为已丢弃，取消正在进行的异步工作，关闭容器运行时，并解除对处于等待状态的 HTTP 处理程序的阻塞。
          evidence:: E12
        - DAPO 路径会补充新的任务，在收集到足够多有信息量的提示后终止那些已经过期的活跃任务，并把尚未完成的任务带入下一轮迭代。
          evidence:: E13
- ## Evaluation and Evidence
    - **实验设置:** 默认训练设置采用动态采样策略优化（Dynamic Sampling Policy Optimization，DAPO），该方法会过滤掉那些 rollout（智能体在环境中完整交互一次并产生用于训练的轨迹）奖励完全一致的提示，批处理大小为 32，小批处理大小为 8，每个实例进行 8 次 rollout，KL 系数为 1e-4，学习率为 1e-6，使用 32 块 NVIDIA H100 GPU。软件工程训练使用 Qwen3 4B、8B 和 14B 模型，在 SkyRL-v0 所用的 293 个实例的 SWE-Gym 子集上进行，并在 SWE-Bench Verified 上评测。
      evidence:: E14, E15
    - **主张-证据矩阵:** 证据面广，但强度并不一致：服务设计方面的论断有具体的架构描述作支撑，而性能方面的论断则依赖汇总表格和曲线，没有报告统计上的不确定性。
      claim_kind:: analyst_assessment
      evidence:: E5, E15, E18
        - C1：由 HTTP 服务架构和 token 轨迹接口支持，但没有跨多种训练器实现的迁移研究来支撑。
          claim_kind:: analyst_assessment
          evidence:: E5, E11
        - C2：由机制描述以及消融实验支持，这些实验表明在所报告的 DAPO 设置下，负载均衡、Efficient Bash 和过期任务清理各自都能提升吞吐。
          evidence:: E7, E9, E18
        - C4：由 SWE-Bench Verified 的表格、各领域的训练曲线以及节点扩展结果支持，但需注意所报告的数字并不包含重复次数或置信区间。
          claim_kind:: analyst_assessment
          evidence:: E15, E16, E17
    - **关键结果:** 在 SWE-Bench Verified 上，ProRL Agent 在各个模型规模上都报告了更高的复现分数：4B 从 14.8 提升到 21.2，8B 从 9.6 提升到 18.0，14B 从 15.4 提升到 23.6。与表 2 中最接近的已报告先前对比相比，8B 的 ProRL Agent 得分 18.0 比 SkyRL-Agent-8B-v0 的 9.4 高出 8.6 分，而 14B 的得分 23.6 比 SkyRL-Agent-14B-v0 的 21.6 高出 2.0 分。
      evidence:: E15
        - 软件工程：支持论断 C4；配置为 Qwen3 4B/8B/14B，在 SWE-Gym 子集上使用 DAPO；基线为复现的基础模型，并在可获得时报告 SkyRL-Agent；指标为 SWE-Bench Verified 得分；方向为正向；未报告不确定性。
          evidence:: E15
        - 通用领域：支持论断 C4；STEM 平均奖励、AMC 数学 Pass@1 和 Codeforces Pass@1 在训练过程中均有提升；各基线分别是每条曲线在第零步时的模型；提升幅度大致为：STEM 上升到所报告的最终区间，数学从 0.40 提升到约 0.89，代码从 0.23 提升到约 0.42。
          evidence:: E16
        - 扩展性：支持论文提出的第 C4 项结论；对于 4B、8B 和 14B 模型，软件工程任务的 rollout 吞吐随节点数从 1 个增加到 8 个而提升，但表格并非在每个中间数据点都严格单调，且未报告方差。
          claim_kind:: analyst_assessment
          evidence:: E17
    - **消融与敏感性:** 组件消融实验在使用 8 块 H100 GPU 对 Qwen3-14B-Instruct-2507 进行 DAPO 训练时，分别移除负载均衡、Efficient Bash 或过期任务清理三者之一。完整配置下的吞吐为每秒 0.37 个实例，GPU 利用率为 78%，动作耗时为 0.42 秒；移除负载均衡后吞吐降至 0.25；移除 Efficient Bash 后动作耗时升至 0.78 秒、吞吐升至 0.29；移除过期任务清理后吞吐为 0.30。
      evidence:: E18
        - 在所报告的实验设置中，负载均衡对 GPU 利用率的影响似乎最大：移除它会使利用率从 78% 降到 42%。
          evidence:: E18
        - Efficient Bash 直接针对工具延迟：所报告的 shell 命令平均动作耗时在有该组件时为 0.42 秒，无该组件时为 0.78 秒。
          evidence:: E18
        - 未报告的内容：对工作进程池规模、容器启动时间分布、网络拓扑、LLM 后端数量、单个任务的超时策略，以及不同训练随机种子间随机波动的敏感性。
          claim_kind:: analyst_assessment
    - **可复现性缺口:** 论文说明 ProRL Agent 已开源并与 NVIDIA NeMo Gym 集成，并给出了足够的架构细节，让读者理解其设计上的服务边界。但在所提供的文本中，对复现至关重要的信息仍然稀缺：确切的代码仓库地址或提交哈希、Docker/Singularity 镜像定义、Slurm 配置、各阶段的工作进程数量、后端数量、训练随机种子、方差，以及生成所有已报告曲线所用的脚本，均未给出。
      claim_kind:: analyst_assessment
      evidence:: E1, E14, E18
- ## Technical Judgment
    - **站得住的结论:** 核心的服务边界设计有充分的动机，因为 rollout（一次智能体与环境交互并产生训练所用轨迹的完整尝试）和训练确实具有不同的瓶颈、故障模式和生命周期负责方。该设计不仅仅是一张方框图：AgentHandler、SingularityRuntime、阶段队列、LLM 后端注册、token ID、取消机制，以及经过消融的各吞吐组件，共同把这条边界具体化到足以评估的程度。
      claim_kind:: analyst_assessment
      evidence:: E3, E5, E6, E18
    - **可能失效之处:** 在以下情形中，该方法可能失去优势：rollout 很短、环境同质、基于 Docker 的基础设施已经够用，或者训练器集成所需的进程内控制比 HTTP 所能提供的更为紧密。其实证论据也容易受到混杂因素影响，因为训练效果的提升是与 ProRL 训练配方、DAPO 过滤、任务专用工具以及固定的 32 块 H100 设置一并报告的，而非仅针对架构本身的受控对比。
      claim_kind:: analyst_assessment
      evidence:: E14, E15, E16
    - **与已有工作的关系:** 与论文所描述的 SkyRL-Agent、VeRL-Tool、Agent Lightning、rLLM 和 GEM 相比，ProRL Agent 移动了归属边界：训练器不再控制完整的智能体循环、环境生命周期和评估。从技术上看，这更接近于把 rollout 变成一个远程运行时服务，而不是在现有训练器内部添加一个工具服务器或环境抽象。
      claim_kind:: analyst_assessment
      evidence:: E4, E5
    - **可迁移启发:** 可复用的模式是按生命周期归属来解耦，而不仅仅按进程放置位置来解耦：如果某一方负责管理长期存在的外部状态、故障、清理以及异质的延迟，就把这一方做成一个服务，并配以一份狭窄而规范的数据契约。对于智能体强化学习而言，这份规范契约必须包含 token 级的轨迹和奖励，而不只是文本记录。
      claim_kind:: analyst_assessment
      evidence:: E5, E11, E12
- ## Glossary
  collapsed:: true
    - 智能体强化学习（agent reinforcement learning）：一种训练模型的方法，让模型在环境中采取行动、观察结果、获得奖励，并根据这些经验更新自己的策略。
    - rollout：智能体与环境交互的一次完整尝试，会产生随后用于训练的轨迹记录。
    - 沙箱环境（sandbox environment）：一个隔离的执行环境，用于运行工具、文件、测试和外部操作，从而保证一次 rollout 不会破坏另一次 rollout 或宿主机。
    - rollout 即服务（rollout-as-a-service）：一种服务边界的设计，训练器通过 API 请求已完成的 rollout，而不必在本地运行整个智能体执行生命周期。
    - AgentHandler：ProRL Agent 的任务插件接口，包含 init、run 和 eval 三个方法，分别用于初始化设置、执行智能体和进行奖励评分。
    - SingularityRuntime：论文提出的无根（rootless）容器运行时封装，面向高性能计算（HPC）集群，因为这类集群通常没有 Docker 守护进程，也无法获得等同于 root 的访问权限。
    - token 进 / token 出（token-in/token-out）：把提示词、回复和之前的对话轮次都表示为 token ID，使训练器消费的 token 序列与 rollout 期间生成的完全一致。
    - 重新分词漂移（re-tokenization drift）：当 rollout 期间生成的文本随后被再次分词、却得到与原来不同的 token 序列时，所造成的不一致。
    - 动态采样策略优化（Dynamic Sampling Policy Optimization，DAPO）：论文所使用的强化学习算法；它会过滤掉那些 rollout 全部成功或全部失败的提示词，因为这类提示词几乎提供不了梯度信号。
    - 过期任务清理（stale job cleanup）：一旦训练器为某次迭代收集到足够的有效样本，就取消或丢弃那些不再有用的 rollout。
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/metadata | Abstract | high
      locator:: Abstract and title block
      quote:: Under the rollout-as-a-service philosophy, we present PRORL AGENT, a scalable infrastructure that serves the full agentic rollout lifecycle through an API service. PRORL AGENT is open-sourced at PRORL Agent and integrated as part of NVIDIA NeMo Gym.
    - **E2:** problem/paper_statement | Introduction | high
      locator:: Introduction, paragraphs 1-2
      quote:: RL training requires repeatedly rolling out policies in these environments and using the resulting trajectories for optimization. As task scale and complexity grow, rollout generation becomes a major bottleneck due to the heterogeneous environments and non-instantaneous feedback inherent in agentic tasks.
    - **E3:** gap/paper_statement | Introduction | high
      locator:: Introduction, coupling limitations
      quote:: Rollout is I/O-intensive, involving sandbox creation, long-lived tool sessions, and asynchronous coordination across hundreds of concurrent instances. Training, by contrast, is GPU-intensive, centered on forward and backward passes, and gradient synchronization.
    - **E4:** prior_work/paper_statement | Related Work | medium
      locator:: Table 1 and Agent RL Infrastructures
      quote:: Across these frameworks, rollout orchestration, including environment lifecycle management, tool execution, trajectory collection, and evaluation, remains implemented as an in-process library within the training loop. Under this design, adopting a new training backend often requires re-implementing or porting the entire rollout stack.
    - **E5:** system_design/implementation_detail | System Design: Training-Rollout Decoupling | high
      locator:: Section 3.1 Overview and Figure 2
      quote:: ProRL Agent Server runs as a standalone HTTP service that accepts a task instance, executes the full agent rollout internally, and returns a completed trajectory with a reward signal. The training framework interacts with the server only through this interface.
    - **E6:** implementation/implementation_detail | Extensible Sandbox Environments | high
      locator:: Section 3.2.1 Pluggable Task Abstraction
      quote:: We encapsulate all task-specific logic in an abstract interface called AgentHandler, which defines three core lifecycle methods corresponding to the three pipeline stages: init, run, eval.
    - **E7:** implementation/implementation_detail | Extensible Sandbox Environments | high
      locator:: Section 3.2.2 HPC-Compatible Container Runtime
      quote:: We implement SingularityRuntime, a container system that requires no persistent daemon and runs entirely as an unprivileged user process to serve sandbox environments. Each container is launched as a child process in its own session.
    - **E8:** optimization/implementation_detail | Extensible Sandbox Environments | high
      locator:: Section 3.2.3 Efficient tool backends
      quote:: We optimize three critical tool backends. Efficient Bash replaces tmux with a ptyprocess-based direct pseudo-terminal. IPython connects to the kernel directly via its in-process API. UDS replaces TCP loopback for action communication inside the container.
    - **E9:** system_design/implementation_detail | ProRL Agent Server | high
      locator:: Section 3.3.1 Three-Stage Rollout Pipeline
      quote:: The three lifecycle methods of AgentHandler map onto three independent worker pools, each with its own queue. Initialization workers start containers, rollout workers drive agent loops, and evaluation workers score results and return them to the caller.
    - **E10:** algorithm/implementation_detail | ProRL Agent Server | high
      locator:: Section 3.3.2 LLM Backend Management
      quote:: Each LLM backend is stored alongside an assignment counter in a min-heap. Every time the rollout stage needs to issue an LLM call, ProRL Agent server automatically selects the backend with the lowest counter and assigns that entire task to the selected LLM.
    - **E11:** method/implementation_detail | ProRL Agent Server | high
      locator:: Section 3.3.3 Token-in/Token-out
      quote:: PROL AGENT eliminates this re-tokenization drift by using token IDs as the canonical representation throughout the entire training process. The rollout worker sends prompt_ids directly to the LLM backend and receives response_ids with per-token log-probabilities.
    - **E12:** system_design/implementation_detail | ProRL Agent Server | high
      locator:: Section 3.3.4 Job Lifecycle and Cancellation
      quote:: The training framework can abort any in-flight job at any time via POST /cancel. Once received, ProRL Agent server will mark the job as discarded, cancel the currently executing async task, close the associated container runtime, and signal completion.
    - **E13:** algorithm/implementation_detail | Connecting to RL Trainers | high
      locator:: Section 3.4 Efficient DAPO
      quote:: To address these bottlenecks, we implement an asynchronous replenishment mechanism: Continuous Throughput replenishes the job queue as soon as it empties, Early Termination terminates remaining active jobs once the target number of Informative Prompts is reached, and Cross-Iteration Persistence carries unfinished jobs over.
    - **E14:** experiment_setup/paper_statement | Experiments | high
      locator:: Section 4.1 Experimental Setup
      quote:: Unless otherwise specified, we adopt DAPO as the default RL algorithm. We use a batch size of 32, a mini-batch size of 8, and generate 8 rollouts per instance. All RL training is performed on 32 NVIDIA H100 GPUs.
    - **E15:** result/experiment_result | Main Results on Software Engineering | medium
      locator:: Section 4.2 and Table 2
      quote:: PRORL AGENT consistently improves performance across all model sizes. Compared with SkyRL-v0, the gains are particularly notable for the 8B model, where PRORL AGENT achieves nearly a 2x improvement on SWE-Bench Verified.
    - **E16:** result/experiment_result | Generality Across Agent Domains | medium
      locator:: Section 4.3 and Figure 4
      quote:: Figure 4 reports training curves for PRORL AGENT across three agent domains: mean reward during RL training of the STEM agent, Pass@1 on AMC during RL training of the math agent, and Pass@1 on Codeforces during RL training of the code agent.
    - **E17:** result/experiment_result | System Analysis | medium
      locator:: Section 4.4.1 and Figure 5
      quote:: Throughput increases nearly linearly with the number of nodes, indicating that PRORL AGENT can effectively leverage additional compute resources with minimal scaling overhead. Figure 5 reports instances per second as compute nodes increase.
    - **E18:** ablation/ablation | System Analysis | medium
      locator:: Section 4.4.2 and Table 3
      quote:: The results in Tab. 3 show that each proposed component contributes to higher rollout throughput during DAPO training. Load Balancing and Stale Job Cleanup improve throughput by increasing GPU utilization, while Efficient Bash improves throughput by reducing action execution time.
