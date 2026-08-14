- **Title:** AREAL: A Large-Scale Asynchronous Reinforcement Learning System for Language Reasoning
  **标题:** AREAL：面向语言推理的大规模异步强化学习系统
- **Summary:** AREAL shows that large language model reinforcement learning can trade strict freshness for bounded staleness, making generation and training run continuously while preserving reasoning-task accuracy.
  **一句话总结:** AREAL 表明，大语言模型的强化学习可以用严格的数据新鲜度换取有界的陈旧程度，从而让生成与训练持续不断地运行，同时保持推理任务的准确率。
- **Paper Type:** system
  **论文类型:** 系统
- **Venue:** NeurIPS 2025; arXiv v5 2026
  **发表:** NeurIPS 2025；arXiv v5 2026
- **Authors:** Wei Fu, Jiaxuan Gao, Xujie Shen, Chen Zhu, Zhiyu Mei, Chuyi He, Shusheng Xu, Guo Wei, Jun Mei, Jiashu Wang, Tongkai Yang, Binhang Yuan, Yi Wu; IIIS, Tsinghua University; Ant Group; HKUST
  **作者:** Wei Fu、Jiaxuan Gao、Xujie Shen、Chen Zhu、Zhiyu Mei、Chuyi He、Shusheng Xu、Guo Wei、Jun Mei、Jiashu Wang、Tongkai Yang、Binhang Yuan、Yi Wu；清华大学交叉信息研究院（IIIS）；蚂蚁集团（Ant Group）；香港科技大学（HKUST）
- **Keywords:** asynchronous reinforcement learning, large reasoning models, PPO, data staleness, LLM training systems, rollout generation
  **关键词:** 异步强化学习、大推理模型、PPO、数据陈旧性、大语言模型训练系统、rollout 生成
- ## Orientation
    - **Background:** Modern reasoning models learn by trying answers, receiving a reward, and updating the model. The expensive part is generating long attempts and then using them for training.
      **背景:** 现代推理模型的学习方式是：尝试给出答案，接收奖励，然后更新模型。其中开销最大的部分，是先生成很长的尝试答案，再用这些答案来做训练。
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** If a training round waits for every attempted answer to finish, one unusually long answer can make many powerful machines sit idle.
      **通俗问题:** 如果一个训练轮次要等到每一个尝试答案都生成完毕，那么某一个异常冗长的答案就会让许多强大的机器闲置等待。
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** Fresh examples make learning more stable, but waiting for freshness wastes time; using old examples keeps machines busy but can teach from an outdated model.
      **为何困难:** 新鲜的样本能让学习更稳定，但等待样本变新鲜会浪费时间；使用旧样本能让机器保持忙碌，但可能是在用一个已经过时的模型来教学。
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Let generation and training run separately, then make the learning rule aware of how old each example is.
      **一句话核心思路:** 让生成和训练分开独立运行，然后让学习规则能够感知每个样本有多旧。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a systems view of reinforcement learning (RL, training a model from reward feedback) for large reasoning models (LRMs, language models trained to produce long reasoning traces): it exposes how the usual synchronous rollout loop wastes accelerators and how much algorithmic slack is needed to remove that barrier.
      **阅读价值:** 把本文当作面向大推理模型（LRM，指经过训练能生成长推理轨迹的语言模型）的强化学习（RL，指从奖励反馈中训练模型）的系统视角来读：它揭示了通常的同步 rollout 循环如何浪费加速器，以及要消除这一瓶颈需要多大的算法容错空间。
      claim_kind:: analyst_assessment
      evidence:: E2, E3
    - **One-Sentence Contribution:** AREAL improves large-scale RL training throughput for LRMs by letting rollout generation and model training run independently while training on samples whose age is explicitly bounded.
      **一句话贡献:** AREAL 让 rollout 生成和模型训练各自独立运行，同时在训练时使用「年龄」被明确限定上界的样本，从而提升了大推理模型大规模 RL 训练的吞吐。
      evidence:: E4, E6
    - **Mental Model:** Picture two kitchens sharing orders: one keeps cooking new dishes, the other keeps tasting and updating the recipe, and a freshness rule decides when an old dish is still useful for improving the recipe.
      **记忆模型:** 可以想象两个共享订单的厨房：一个不停地做新菜，另一个不停地品尝并更新菜谱，而一条新鲜度规则决定一道旧菜是否还能用来改进菜谱。
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is the combination of end-to-end time reduction, scaling behavior, and staleness ablations showing that the system gain is not only a faster implementation trick.
      **最佳证据:** 最有力的证据在于端到端时间缩短、扩展表现以及陈旧性消融实验三者的结合，它们共同表明系统收益并不只是一个更快的实现技巧。
      claim_kind:: analyst_assessment
      evidence:: E11, E12, E13
        - Supports C1: math and coding RL runs on 16 to 48 H800 nodes; synchronous AREAL and verl-style baselines; training hours; up to 2.77x reduction with comparable final accuracy; supported, but single-trial.
          支持结论 C1：数学与代码强化学习（RL）实验在 16 到 48 个 H800 节点上运行；对比对象为同步式 AREAL 与 verl 风格的基线方法；衡量指标为训练小时数；在最终准确率相当的情况下，训练时间最多缩短 2.77 倍；结论成立，但只做了单次实验。
          evidence:: E10, E11, E18
        - Supports C2: 1.5B math ablations across maximum staleness values; naive PPO and decoupled PPO; benchmark score and throughput; moderate staleness keeps near-oracle scores while throughput exceeds 2x; supported, but no error bars.
          支持结论 C2：在 1.5B 数学任务上，围绕不同的最大数据陈旧度（maximum staleness）取值做消融实验；对比对象为朴素 PPO 与解耦 PPO；衡量指标为基准得分与吞吐；适度的陈旧度可以让得分接近理想上限，同时吞吐超过 2 倍；结论成立，但没有误差线。
          evidence:: E13, E14, E18
        - Supports C3: scaling tests across model sizes, device counts, and context lengths; verl as synchronous baseline; effective training throughput; AREAL usually scales better and reaches up to 2.5x throughput speedup; supported, but benchmark surface is narrow.
          支持结论 C3：在不同模型规模、设备数量和上下文长度下做扩展性测试；以 verl 作为同步式基线；衡量指标为有效训练吞吐；AREAL 通常扩展性更好，吞吐最高可提速 2.5 倍；结论成立，但基准测试覆盖面较窄。
          evidence:: E12, E19
        - Supports C4: system ablations on dynamic microbatch allocation and interruptible generation; normal batching and non-interruptible generation as baselines; throughput; about 30 percent training gain plus 12 to 17 percent generation gain; supported, but isolated from full-run variance.
          支持结论 C4：对动态微批分配（dynamic microbatch allocation）和可中断生成做系统级消融实验；以普通批处理和不可中断生成作为基线；衡量指标为吞吐；训练环节约提升 30%，生成环节额外提升 12% 到 17%；结论成立，但这是与整体运行波动隔离开来单独测量的。
          evidence:: E15, E18
    - **Main Caveat:** The evidence is strongest for single-turn math and code reasoning on large internal H800 clusters; the paper reports no error bars, uses fixed seeds, and leaves device partitioning and multi-turn agent settings open.
      **主要边界:** 证据最充分的场景是：在大型内部 H800 集群上进行的单轮数学与代码推理。论文没有报告误差线，使用固定随机种子，并且把设备分区和多轮智能体设置留作开放问题。
      claim_kind:: analyst_assessment
      evidence:: E10, E18, E19
- ## Argument Map
    - **Problem and Stakes:** Large reasoning model (LRM) RL needs many long rollouts, meaning generated answer traces used as training data, but synchronous systems wait for each generation batch before training. That waiting makes accelerator utilization and scaling the central systems bottleneck rather than only the learning algorithm.
      **问题与重要性:** 大型推理模型（Large Reasoning Model，LRM）的强化学习需要大量长 rollout，也就是把生成出来的答案轨迹当作训练数据。但同步式系统在训练前必须等待每一批生成完成。这种等待使得加速器利用率和扩展性成为系统的核心瓶颈，而不再仅仅是学习算法本身。
      evidence:: E2, E3
    - **Prior Gap:** Prior synchronous frameworks preserve on-policy data, where examples come from the latest model, while overlap systems relax freshness by only a step or two but still keep batched generation. The unfilled gap is a system that streams generation continuously while giving the optimizer a principled way to use mixed-version data.
      **已有方法缺口:** 以往的同步框架会保留同策略（on-policy）数据，即训练样本来自最新的模型；而重叠式系统只把数据新鲜度放宽一两步，但仍然保持批处理式的生成。目前尚未填补的空白是：一个既能持续不断地流式生成、又能给优化器提供一套有原则的方法来使用混合版本数据的系统。
      evidence:: E3, E4
    - **Key Insight:** The paper's key insight is to treat data age as a controllable systems variable and to pair that control with decoupled Proximal Policy Optimization (PPO, an RL update rule that clips overly large policy changes around a reference policy). This changes strict freshness from a hard synchronization barrier into a tunable learning-system tradeoff.
      **关键洞见:** 这篇论文的核心洞见是：把数据的陈旧程度当作一个可控的系统变量，并把这种控制与解耦式近端策略优化（Proximal Policy Optimization，PPO，一种强化学习更新规则，会在参考策略附近裁剪掉过大的策略变化）配合使用。这样一来，严格的新鲜度就从一道硬性的同步屏障，变成了一个可调的「学习—系统」权衡。
      evidence:: E6, E7
    - **Claims:** The paper's claims separate system throughput, algorithmic stability under stale data, scaling, and individual implementation optimizations.
      **核心主张:** 这篇论文的论断分别涉及系统吞吐、在陈旧数据下的算法稳定性、可扩展性，以及各项具体的实现优化。
      claim_kind:: analyst_assessment
        - C1: Fully asynchronous generation and training reduces end-to-end RL training time for LRMs while matching or improving final math and coding benchmark accuracy.
          C1：完全异步的生成与训练能够缩短大型推理模型（LRM）端到端的强化学习（RL）训练时间，同时在数学和编程基准测试上的最终准确率持平或有所提升。
          evidence:: E10, E11
        - C2: Bounded data staleness combined with decoupled PPO makes stale and interrupted rollouts usable, whereas naive PPO degrades as staleness increases.
          C2：有界的数据陈旧程度与解耦式 PPO 相结合，使得陈旧的和被中断的 rollout（一次用作强化学习训练数据的生成答案轨迹，包含 token 与奖励）也能被使用；相比之下，朴素的 PPO 会随着陈旧程度增加而性能下降。
          evidence:: E6, E7, E13
        - C3: AREAL scales more effectively than a synchronous verl-style RL system across larger device counts, model sizes, and longer context lengths.
          C3：在更大的设备规模、更大的模型尺寸和更长的上下文长度下，AREAL 比同步的 verl 式强化学习系统扩展得更为高效。
          evidence:: E12
        - C4: Dynamic microbatch allocation and interruptible generation are measurable contributors to throughput beyond the high-level asynchronous architecture.
          C4：动态微批分配（dynamic microbatch allocation）和可中断生成，是在高层异步架构之外对吞吐有可量化贡献的因素。
          evidence:: E9, E15
- ## Mechanism and Design
    - **Core Mechanism:** AREAL separates rollout workers that generate text from trainer workers that update model parameters, using a controller, reward service, replay buffer, and parameter updates to keep both sides active. Because batches may mix policy versions, it adds a staleness limit and a decoupled PPO objective that clips around a recent proximal policy rather than the old behavior policy that produced each sample.
      **核心机制:** AREAL 把负责生成文本的 rollout 工作节点与负责更新模型参数的训练工作节点分离开来，并借助一个控制器、一个奖励服务、一个回放缓冲区（replay buffer）以及参数更新机制，让两侧都保持活跃。由于同一批数据可能混杂多个策略版本，它额外引入了一个陈旧程度上限，以及一个解耦式 PPO 目标函数——该目标在一个较新的近端策略（proximal policy）附近做裁剪，而不是围绕生成每个样本的那个旧行为策略（behavior policy）做裁剪。
      evidence:: E5, E6, E7
    - **Data / Control Flow:** The controller reads prompts, dispatches generation, sends responses to a reward service, places rewarded trajectories in a replay buffer, and triggers weight updates after trainers publish new parameters. Interruptible rollout workers can stop in-flight generation, reload parameters, discard old key-value attention state (KV cache, saved attention computations used to continue decoding efficiently), recompute needed state, and continue unfinished requests.
      **数据/控制流:** 控制器读取提示词，分派生成任务，把生成的回复送往奖励服务，将带有奖励的轨迹放入回放缓冲区，并在训练节点发布新参数后触发权重更新。可中断的 rollout 工作节点能够停止正在进行的生成，重新加载参数，丢弃旧的键值注意力缓存（key-value attention cache，KV cache，即为高效继续解码而保存下来的注意力计算结果），重新计算所需的状态，然后继续未完成的请求。
      evidence:: E5, E8
        - Generation is streaming rather than batch-barriered: rollout workers keep accepting generate requests and only pause when an update_weights request interrupts them.
          生成过程是流式的，而不是用批处理屏障切分的：rollout 工作节点持续接收生成请求，只有在收到 update_weights（更新权重）请求把它们打断时才会暂停。
          evidence:: E4, E5
        - Training workers sample once-used data from the replay buffer until the configured batch size is reached, run PPO updates, and write new model parameters to distributed storage.
          训练工作进程从回放缓冲区（replay buffer）中采样只用过一次的数据，直到达到配置好的批处理大小，然后执行 PPO 更新，并把新的模型参数写入分布式存储。
          evidence:: E5
        - Reward evaluation is separated from GPU generation and training; math can use string matching and coding can execute unit tests before trajectories enter the buffer.
          奖励评估与 GPU 上的生成和训练相分离；在轨迹（trajectory）进入缓冲区之前，数学任务可以用字符串匹配来评估，编程任务则可以运行单元测试。
          evidence:: E5, E9
    - **Design Decisions:** The design choices are mostly small relaxations of strict synchronous RL: permit bounded age, make the optimizer know which policy produced the sample, and reduce the wasted work caused by long or uneven sequences. Each choice trades exact freshness or simple batching for higher utilization.
      **设计决策:** 这些设计选择大多是对严格同步强化学习（RL）所做的小幅放宽：允许数据有一定的陈旧度，让优化器知道每个样本是由哪个策略产生的，并减少长序列或长度不均序列所造成的无用计算。每一项选择都是用精确的数据新鲜度或简单的批处理，去换取更高的资源利用率。
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E15
        - Need: avoid unbounded off-policy data, meaning samples from older policies; choice: reject new generation requests that would exceed maximum staleness eta; alternative: eta = 0 synchronous training; tradeoff: small eta can throttle generation when responses are long.
          需求：避免出现无界的离策略（off-policy）数据，也就是来自旧策略的样本；选择：拒绝那些会超过最大陈旧度 eta 的新生成请求；替代方案：eta = 0，即同步训练；权衡：当回复很长时，较小的 eta 会限制生成速度。
          evidence:: E6, E13
        - Need: train on samples produced by older or interrupted policies; choice: use behavior policy probabilities for importance weighting but clip updates around a recent proximal policy; alternative: standard PPO centered on the behavior policy; tradeoff: extra token-probability recomputation at batch arrival.
          需求：在由旧策略或被中断策略产生的样本上进行训练；选择：使用行为策略（behavior policy）的概率来做重要性加权，但把更新裁剪在一个较新的近端策略（proximal policy）附近；替代方案：以行为策略为中心的标准 PPO；权衡：在每个批次到达时需要额外重新计算词元的概率。
          evidence:: E7, E8
        - Need: variable sequence lengths waste memory and make long requests block progress; choice: padding-free dynamic microbatch allocation plus interruptible generation; alternative: fixed microbatches and non-interruptible generation; tradeoff: more runtime control complexity and KV-cache recomputation after updates.
          需求：变长序列会浪费显存，并使长请求阻塞整体进度；选择：采用免填充的动态微批处理分配（dynamic microbatch allocation），并支持可中断的生成；替代方案：使用固定微批处理和不可中断的生成；权衡：会带来更多的运行时控制复杂度，并且在更新后需要重新计算键值注意力缓存（KV cache）。
          evidence:: E5, E9, E15
    - **Implementation Surface:** The implementation is a Python/PyTorch system built on ReaLHF, SGLang for serving, Megatron-Core for training, and SLURM (a cluster job scheduler) for resource scheduling. It overlaps CPU reward computation and network transfer with GPU generation, uses asyncio to avoid blocking among rollout requests, and packs variable-length sequences under memory constraints.
      **实现边界:** 该实现是一套基于 Python/PyTorch 的系统，构建在 ReaLHF 之上，用 SGLang 做服务、用 Megatron-Core 做训练，并用 SLURM（一种集群作业调度器，全称 Simple Linux Utility for Resource Management）做资源调度。它把 CPU 上的奖励计算和网络传输与 GPU 上的生成相重叠，用 asyncio 避免各个 rollout 请求之间相互阻塞，并在显存约束下把变长序列打包在一起。
      evidence:: E9, E17
- ## Evaluation and Evidence
    - **Setup:** The main experiments train DeepSeek-R1-distilled Qwen2-family models from 1.5B to 32B parameters on math and code RL tasks, then evaluate on AIME24 and LiveCodeBench with additional appendix benchmarks. Hardware is an H800 cluster with up to 64 nodes, and AREAL usually allocates three quarters of devices to inference based on early experiments.
      **实验设置:** 主要实验在数学和编程强化学习任务上训练由 DeepSeek-R1 蒸馏得到的 Qwen2 系列模型，参数量从 1.5B 到 32B，然后在 AIME24 和 LiveCodeBench 上进行评估，并在附录中给出额外的基准测试。硬件是一个 H800 集群，最多可用 64 个节点，AREAL 通常根据前期实验把四分之三的设备分配给推理。
      evidence:: E10, E17
    - **Claim-Evidence Matrix:** The evidence is organized by claim: full-run comparisons support C1, staleness and objective ablations support C2, scaling curves support C3, and isolated system ablations support C4.
      **主张-证据矩阵:** 证据按论断组织：完整运行的对比支持 C1，陈旧度和目标函数的消融实验支持 C2，扩展曲线支持 C3，隔离的系统消融实验支持 C4。
      claim_kind:: analyst_assessment
      evidence:: E11, E12, E13, E15
        - C1 is supported by Table 1, where AREAL cuts hours versus synchronous baselines while final AIME24 and LiveCodeBench scores stay close or improve.
          C1 由表 1 支持：AREAL 相比同步基线大幅缩短了训练耗时，而最终在 AIME24 和 LiveCodeBench 上的分数保持接近或有所提升。
          evidence:: E11
        - C2 is supported by Figure 5 and Table 2, where decoupled PPO tolerates moderate eta values and naive PPO collapses in important settings such as eta = 4.
          C2 由图 5 和表 2 支撑：解耦式 PPO 能够容忍中等程度的 eta 取值，而朴素 PPO 在一些重要设置下会崩溃，例如 eta = 4 时。
          evidence:: E13, E14
        - C3 and C4 are supported separately: Figure 4 shows stronger scaling than verl, while Figure 6 shows dynamic batching and interruptibility each add throughput.
          C3 和 C4 分别得到支撑：图 4 显示其扩展性比 verl 更强，图 6 则显示动态批处理与可中断性各自都能提升吞吐。
          evidence:: E12, E15
    - **Headline Results:** The headline result is a large wall-clock reduction at comparable final quality: 1.5B math training goes from 41.0 hours under synchronous AREAL to 14.8 under AREAL, and 14B coding goes from 48.8 to 21.9 hours versus synchronous AREAL. Compared with external verl-derived baselines, the paper also reports up to 2.77x lower training hours and up to 2.5x throughput speedup in scaling experiments.
      **关键结果:** 最核心的结果是：在最终质量相当的前提下，实际耗时大幅下降。1.5B 规模的数学训练从同步版 AREAL 的 41.0 小时降到 AREAL 的 14.8 小时，14B 规模的代码训练相比同步版 AREAL 从 48.8 小时降到 21.9 小时。与基于 verl 的外部基线相比，论文在扩展性实验中还报告了训练时长最多降低 2.77 倍、吞吐最多加速 2.5 倍。
      evidence:: E11, E12
        - On 1.5B and 7B math, AREAL matches synchronous AREAL AIME24 scores within 0.2 points while cutting reported hours from 41.0 to 14.8 and from 57.7 to 25.4.
          在 1.5B 和 7B 规模的数学任务上，AREAL 的 AIME24 分数与同步版 AREAL 的差距在 0.2 分以内，同时把报告的耗时从 41.0 小时降到 14.8 小时、从 57.7 小时降到 25.4 小时。
          evidence:: E11
        - On 14B and 32B coding, AREAL reports LiveCodeBench scores of 58.1 and 61.0 while reducing synchronous AREAL hours from 48.8 to 21.9 and from 51.1 to 31.1.
          在 14B 和 32B 规模的代码任务上，AREAL 报告的 LiveCodeBench 分数分别为 58.1 和 61.0，同时把同步版 AREAL 的耗时从 48.8 小时降到 21.9 小时、从 51.1 小时降到 31.1 小时。
          evidence:: E11
    - **Ablations and Sensitivity:** The most important sensitivity is staleness: moderate eta improves throughput sharply, but unbounded staleness degrades accuracy even with decoupled PPO. System ablations show dynamic allocation and interruptible generation both matter, so the speedup is a compound effect rather than a single optimization.
      **消融与敏感性:** 最重要的敏感性因素是数据陈旧度（staleness）：中等的 eta 能显著提升吞吐，但不加限制的陈旧度即使配合解耦式 PPO 也会损害准确率。系统层面的消融实验表明，动态分配与可中断生成两者都很关键，因此这种加速是多项优化叠加的复合效果，而非单一优化的结果。
      evidence:: E13, E14, E15
        - Eta = 4 is the clearest tradeoff point in the main math ablation: throughput rises to 356.6k tokens/s while decoupled PPO keeps AIME24 at 42.2, close to the eta = 0 oracle of 42.0.
          在主要的数学消融实验中，eta = 4 是最清晰的权衡点：吞吐上升到 356.6k tokens/s，同时解耦式 PPO 把 AIME24 保持在 42.2，接近 eta = 0 的理想上限 42.0。
          evidence:: E14
        - Unbounded staleness is not safe: the paper reports inferior final performance even with the decoupled objective, which makes eta a required control rather than a cosmetic knob.
          不加限制的陈旧度并不安全：论文报告，即使使用解耦式目标函数，最终性能仍然更差，这使得 eta 成为一个必需的控制项，而不是可有可无的调节旋钮。
          evidence:: E13
        - Dynamic microbatch allocation improves training throughput most for larger models in Figure 6a, while interruptible generation improves rollout throughput for both 1.5B and 7B models.
          在图 6a 中，动态微批处理分配（dynamic microbatch allocation）对较大模型的训练吞吐提升最明显，而可中断生成对 1.5B 和 7B 两种模型的 rollout 吞吐都有提升。
          evidence:: E15
    - **Reproducibility Gaps:** The paper provides a public code URL, open-source datasets and base models, fixed seed, and detailed hyperparameters, but the main large-scale claims still depend on an H800 cluster and single-trial results without error bars. Not reported: scripts for every table from a clean checkout, variance across seeds, and sensitivity to inference/training partition beyond the selected heuristic.
      **可复现性缺口:** 论文提供了公开的代码链接、开源数据集与基础模型、固定的随机种子以及详细的超参数，但其主要的大规模实验结论仍然依赖于一套 H800 集群和没有误差棒的单次试验结果。论文未报告的内容包括：从干净的代码检出（clean checkout）复现每一张表格的脚本、不同随机种子之间的方差，以及除所选启发式方法之外对推理/训练资源划分的敏感性。
      claim_kind:: analyst_assessment
      evidence:: E10, E17, E18, E19
- ## Technical Judgment
    - **What Holds Up:** The strongest part is the algorithm-system link: the paper does not merely overlap generation and training, but names the resulting data-age problem and tests the optimizer change needed to tolerate it. The proof that interrupted generation can be viewed as one behavior policy also gives a clean accounting story for mixed-version trajectories, even though it does not by itself prove good learning performance.
      **站得住的结论:** 最有说服力的部分是算法与系统之间的衔接：这篇论文不只是把生成过程和训练过程重叠起来，还明确指出由此产生的「数据陈旧」问题，并测试了为容忍这一问题所需的优化器改动。论文还证明，被中断的生成过程可以看作单一的行为策略（behavior policy，即真正产生某个 token 或轨迹的策略分布，可能由多个被中断的模型版本拼接而成），这为混合版本的轨迹提供了一套清晰的核算方法，尽管这一证明本身并不能说明学习性能一定好。
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E8, E13
    - **Where It May Fail:** Benefits should diminish when generation is short, training is the bottleneck, or the chosen inference/training split is wrong for the run; the paper itself notes shorter-context imbalance and leaves dynamic partitioning open. Trust also weakens outside single-turn math/code tasks and for claims requiring statistical robustness, because large-scale experiments are single-trial without error bars.
      **可能失效之处:** 在以下几种情况下，收益应当减小：生成过程较短、训练成为瓶颈，或者所选的推理与训练资源划分不适合当前的运行。论文自己也指出，在较短上下文下会出现负载不均衡，并把动态划分留作未解决的问题。此外，在单轮的数学或代码任务之外，以及在需要统计稳健性的结论上，可信度也会下降，因为大规模实验都是单次运行，没有误差棒。
      claim_kind:: analyst_assessment
      evidence:: E12, E18, E19
    - **Relation to Other Work:** Compared with synchronous reinforcement learning from human feedback (RLHF) and RL systems such as verl-style pipelines, AREAL moves the key boundary from phase alternation to a streaming producer-consumer loop. Compared with limited-overlap or short-context asynchronous RLHF, its distinguishing technical dimension is allowing mixed-version batches and interrupted trajectories while using staleness control and decoupled PPO to keep the update meaningful.
      **与已有工作的关系:** 与同步的基于人类反馈的强化学习（reinforcement learning from human feedback，RLHF）以及 verl 风格流水线之类的强化学习（reinforcement learning，RL）系统相比，AREAL 把关键的边界从「阶段交替」转移到了「流式的生产者—消费者循环」。与重叠有限或上下文较短的异步 RLHF 相比，它在技术上的区别在于：它允许出现混合版本的批处理和被中断的轨迹，同时通过陈旧度控制和解耦的 PPO 来保证更新仍然有意义。
      claim_kind:: analyst_assessment
      evidence:: E3, E7, E12
    - **Transferable Lesson:** A useful systems pattern is to turn an expensive correctness invariant into a measured budget: here, exact on-policy freshness becomes bounded staleness, and the learning rule is changed to spend that budget safely. The transferable warning is that systems slack only works when the algorithm consumes the slack explicitly rather than pretending the data are still fresh.
      **可迁移启发:** 一个有用的系统设计模式是：把一个代价高昂的正确性不变量转化为一个可度量的预算。在这里，严格的同策略新鲜度被换成了「有界的陈旧度」，同时修改学习规则，使其能够安全地花掉这份预算。可迁移的警示是：只有当算法明确地消耗这份系统余量、而不是假装数据仍然新鲜时，这种余量才真正有用。
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E13, E14
- ## Glossary
  collapsed:: true
    - reinforcement learning: Training from reward feedback rather than fixed target answers; in this paper the reward is correctness at the final generated answer.
      强化学习（reinforcement learning，RL）：依据奖励反馈进行训练，而不是依据固定的标准答案；在本文中，奖励就是最终生成答案是否正确。
    - large reasoning model: A large language model trained or prompted to produce long reasoning traces before the final answer.
      大型推理模型（large reasoning model，LRM）：一种经过训练或提示后、能在给出最终答案前产生长篇推理过程的大语言模型。
    - rollout: One generated answer trace used as RL training data, including tokens and reward.
      rollout（生成轨迹）：一条被生成出来、用作强化学习训练数据的答案轨迹，包含其中的 token 和奖励。
    - Proximal Policy Optimization: An RL update that limits policy movement by clipping the probability ratio around a reference policy.
      近端策略优化（Proximal Policy Optimization，PPO）：一种强化学习更新方法，通过在参考策略附近裁剪概率比值来限制策略的变动幅度。
    - reinforcement learning from human feedback: A family of language-model RL methods that use human preference or feedback signals; AREAL compares against related systems in this broader category.
      基于人类反馈的强化学习（reinforcement learning from human feedback，RLHF）：一类使用人类偏好或反馈信号的语言模型强化学习方法；AREAL 与这一大类中的相关系统进行了对比。
    - data staleness: How many training versions old a sample may be; AREAL controls it with a request-rate rule and older-first buffer use.
      数据陈旧度（data staleness）：一个样本相对于当前训练版本最多可以陈旧几个版本；AREAL 通过一条请求速率规则和「优先使用较旧数据」的缓冲区策略来控制它。
    - behavior policy: The policy distribution that actually generated a token or trajectory, possibly assembled from multiple interrupted model versions.
      behavior policy（行为策略）：实际生成某个 token 或轨迹的策略分布，可能由多个被中断的模型版本拼接而成。
    - proximal policy: The recent policy used as the trust-region center for decoupled PPO instead of the older behavior policy.
      proximal policy（近端策略）：在解耦的 PPO 中用作信任域中心的近期策略，用来替代较旧的行为策略。
    - key-value attention cache: Saved transformer attention state that makes continued decoding faster; AREAL discards and recomputes it when weights change during interrupted generation.
      键值注意力缓存（key-value attention cache）：保存下来的 Transformer 注意力状态，能让后续解码更快；当中断式生成过程中权重发生变化时，AREAL 会丢弃并重新计算它。
    - dynamic microbatch allocation: A sequence-packing method that groups variable-length training examples under a token budget to reduce padding and avoid memory overflows.
      动态微批分配（dynamic microbatch allocation）：一种序列打包方法，在一定的 token 预算下把长度不一的训练样本分组，以减少填充并避免内存溢出。
    - replay buffer: Temporary storage for rewarded trajectories before training; AREAL uses each item once and prioritizes older trajectories.
      回放缓冲区（replay buffer）：在训练前临时存放带奖励轨迹的存储区；AREAL 对每条数据只使用一次，并优先取用较旧的轨迹。
    - Simple Linux Utility for Resource Management: A cluster job scheduler used by the AREAL implementation for resource management.
      Simple Linux Utility for Resource Management（简单 Linux 资源管理工具）：一种集群作业调度器，AREAL 的实现用它来进行资源管理。
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/metadata | Title and author block | high
      locator:: title page
      quote:: The title page identifies AREAL as a large-scale asynchronous reinforcement learning system for language reasoning, lists authors from Tsinghua University, Ant Group, and HKUST, and marks the paper as NeurIPS 2025 with arXiv version 5 in March 2026.
    - **E2:** problem/paper_statement | Abstract and Introduction | high
      locator:: Abstract; Section 1
      quote:: The paper says existing large-scale RL systems for LLMs are mostly synchronous, alternating generation and training. Generation waits for the longest output in a batch, which underutilizes GPUs when reasoning outputs have highly variable lengths.
    - **E3:** gap/paper_statement | Related Work and Motivation | high
      locator:: Section 2; Section 3.2
      quote:: The paper positions prior overlap systems as using outputs from one or two older model versions but still in batched generation, while synchronous systems distribute generation across all devices and can become memory-IO-bound at small per-GPU decode batches.
    - **E4:** insight/paper_statement | Introduction | high
      locator:: Section 1
      quote:: AREAL is described as fully asynchronous: rollout workers continuously generate without waiting, trainers update whenever enough data is collected, and each batch can contain samples produced by different model versions.
    - **E5:** system_design/implementation_detail | System Overview | high
      locator:: Section 4.1; Figure 2 and Figure 3
      quote:: The architecture contains interruptible rollout workers, a reward service, trainer workers, and a rollout controller. The controller sends prompts, obtains rewards, stores trajectories in a replay buffer, and updates rollout workers after trainers publish new parameters.
    - **E6:** algorithm/implementation_detail | Staleness-Aware Training | high
      locator:: Section 5.1
      quote:: The system introduces a maximum permitted staleness eta. The rollout controller tracks generated samples and policy version, rejects requests that could violate the constraint, and prioritizes older trajectories when forming training batches.
    - **E7:** algorithm/paper_statement | Decoupled PPO Objective | high
      locator:: Section 5.2
      quote:: The objective separates behavior policy from proximal policy. The paper argues that using a recent proximal policy prevents updates from being pulled toward old, lower-quality behavior policies, and recomputes token probabilities when the global batch arrives.
    - **E8:** other/proof | Decoupled PPO Objective and Proof | high
      locator:: Section 5.2; Appendix D
      quote:: Proposition 1 states that a sequence generated by multiple policy versions during interrupted generation has an equivalent single behavior policy. Appendix D constructs that behavior policy over the states encountered by the generated sequence.
    - **E9:** implementation/implementation_detail | Implementation | high
      locator:: Section 6; Appendix B
      quote:: AREAL is implemented in Python and PyTorch on ReaLHF, using SGLang v0.4.6 for generation, Megatron-Core v0.11.0 for training, SLURM, a cluster job scheduler, asyncio for rollout concurrency, and padding-free sequence packing with dynamic allocation.
    - **E10:** experiment_setup/paper_statement | Experiment Setup | high
      locator:: Section 7.1
      quote:: The evaluation covers math and coding tasks with distilled Qwen2 models from DeepSeek-R1 from 1.5B to 32B parameters, AIME24 and LiveCodeBench-style evaluation, fixed PPO steps, and an H800 cluster with 64 nodes and 8 GPUs per node.
    - **E11:** result/experiment_result | End-to-End Comparison | medium
      locator:: Section 7.2; Table 1
      quote:: Table 1 reports comparable or better final accuracy while reducing training hours: for example, 1.5B math synchronous AREAL takes 41.0 hours versus 14.8 for AREAL, and 14B coding verl takes 44.4 hours versus 21.9.
    - **E12:** result/experiment_result | Scalability | medium
      locator:: Section 7.3; Figure 4
      quote:: The scalability study compares AREAL with verl over model sizes and context lengths. The paper reports approximate linear scaling for AREAL, weaker scaling for the synchronous system, and at most 2.5x effective throughput speedup.
    - **E13:** ablation/ablation | Algorithm Ablations | medium
      locator:: Section 7.4; Figure 5; Table 2
      quote:: The ablation varies maximum staleness eta with and without the decoupled PPO objective. The paper says naive PPO degrades with staleness, while decoupled PPO with moderate staleness keeps final performance near the zero-staleness oracle and improves throughput.
    - **E14:** result/ablation | Algorithm Ablations | medium
      locator:: Table 2; Figure 5c
      quote:: At eta = 4, Table 2 reports AIME24 42.2 with decoupled PPO versus 23.3 without it, while Figure 5c shows effective throughput rising from 128.7k tokens/s at eta = 0 to 356.6k at eta = 4.
    - **E15:** ablation/ablation | System Ablations | medium
      locator:: Section 7.5; Figure 6
      quote:: Dynamic microbatch allocation improves PPO throughput by about 30 percent across model sizes. Interruptible generation increases generation throughput by 12 percent for 1.5B and 17 percent for 7B models on four nodes.
    - **E16:** result/experiment_result | Additional Results | medium
      locator:: Appendix C.1 to C.4; Tables 4 to 8
      quote:: The appendices add math and coding benchmark tables, a Llama-8B architecture test, small 8-GPU staleness-throughput experiments, and RLOO experiments, which the paper uses to argue that the conclusions extend beyond the main Qwen runs.
    - **E17:** experiment_setup/paper_statement | Reproducibility and Implementation Details | high
      locator:: Appendix A; Appendix B
      quote:: The paper states that AREAL code is available on GitHub, datasets and base models are from open-source sources, fixed random seed 1 is used, and Appendix B gives PPO, optimizer, precision, generation, dataset, batching, and baseline details.
    - **E18:** limitation/limitation | NeurIPS Checklist | high
      locator:: Checklist item 7
      quote:: For statistical significance, the authors answer No, explaining that large-scale end-to-end experiments are expensive, results are from a single trial, and the same fixed random seed is used across settings.
    - **E19:** limitation/limitation | Limitations and Future Work | high
      locator:: Appendix E
      quote:: The limitations note says the inference-to-training device ratio could be optimized or dynamically adjusted, and that evaluation focuses on single-step mathematical and coding tasks while multi-turn interactions and agentic scenarios remain future work.
