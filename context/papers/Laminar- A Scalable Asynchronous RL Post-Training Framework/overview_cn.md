- **标题:** Laminar: A Scalable Asynchronous RL Post-Training Framework
- **一句话总结:** Laminar 把 RL post-training 从“全局同步的一批 rollout”改成“每条 trajectory 独立生成、独立进入 buffer、trainer 独立消费”，并用 CPU relay worker 做异步权重同步，用 dynamic repack 把长尾 trajectory 合并到少数 rollout 上，减少空泡和 staleness。
- **论文类型:** RL / rollout infrastructure system
- **发表:** arXiv v1, 2025-10-14；EuroSys 2026 accepted paper
- **作者:** Guangming Sheng、Yuxuan Tong、Borui Wan、Wang Zhang、Chaobo Jia、Xibin Wu、Yuqi Wu、Xiang Li、Chi Zhang、Yanghua Peng、Haibin Lin、Xin Liu、Chuan Wu
- **单位:** The University of Hong Kong；ByteDance Seed
- **资源:** [arXiv](https://arxiv.org/abs/2510.12633)；[EuroSys 2026 accepted papers](https://2026.eurosys.org/papers.html)；本地 `paper.pdf` / `paper.md`
- **关键词:** asynchronous RL、trajectory-level asynchrony、rollout long-tail、global weight synchronization、relay worker、dynamic repack、KVCache utilization、inherent staleness、fault tolerance

- ## Orientation
    - **背景:** 大模型 RL post-training 的成本越来越集中在 rollout generation。复杂数学、代码、tool-calling、多轮 agent 任务里，不同 trajectory 的长度和外部环境延迟差异很大，少数长尾会让很多 GPU 等待。
      evidence:: E1, E2
    - **核心问题:** 现有同步系统要等整批 rollout 完成；现有异步系统通常仍然按固定 `k-step staleness` 做全局权重同步。两者都会被长尾 trajectory 卡住，或者把吞吐和收敛稳定性绑在一个难调的 staleness 超参上。
      evidence:: E2, E3
    - **Laminar 的一句话思路:** 不再把 rollout 看成一整批，而是让每条 trajectory 按自己的速度生成和进入 experience buffer；trainer 从 buffer 抽样训练，rollout 在完成或被释放后自己拉最新权重。
      evidence:: E4, E5
    - **为什么和我们相关:** 它非常清楚地说明“长尾 rollout + staleness + 全局同步”为什么是系统 API 级问题。它不是 streaming context RL，但它给了异步 RL infra 的强 baseline。
      claim_kind:: analyst_assessment

- ## Quick Reference
    - **最值得读的点:** Laminar 反对的是 batch-level / global-sync async。它说真正能扩展的是 trajectory-level asynchrony：trajectory 生成、权重同步、trainer 消费三件事都独立推进。
      evidence:: E4, E5
    - **Rollout 包含什么:** 一条 rollout 是一条完整 trajectory，可以是单轮数学推理回答，也可以是多轮 tool-calling / code sandbox 交互轨迹。每条 trajectory 由某一个固定 policy version 生成，不在中途混多个版本。
      evidence:: E2, E3, E8
    - **Trainer 吃什么:** trainer 从 experience buffer 采样已完成的 trajectories，计算 reward / advantage，然后用 GRPO 这类算法更新 actor。论文实验主要用 GRPO + rule-based reward，global batch 是 8192，512 prompts 每个 16 responses。
      evidence:: E5, E8
    - **架构形态:** fully decoupled / disaggregated。rollout GPUs 和 trainer GPUs 分离；trainer 内 actor / critic / reference 可以 colocate 分时执行；rollout manager、prompt pool、partial response pool、experience buffer、relay workers 都是独立组件。
      evidence:: E5, E8
    - **权重怎么同步:** actor 更新后只把新权重推给一个 master relay，然后继续训练；master relay 在 CPU 侧用 RDMA pipeline broadcast 到各 rollout 机器的 relay。rollout 想更新时从本机 relay 经 PCIe 拉权重，不需要所有 rollout 一起停。
      evidence:: E6
    - **长尾怎么处理:** dynamic repack 定期检查 rollout 的 KVCache utilization，把同一 policy version 下已经进入尾部阶段的未完成 trajectories 合并到少数 destination rollouts，释放出来的 rollouts 立刻拉新权重继续生成。
      evidence:: E7
    - **staleness 怎么定义:** Laminar 不设固定 staleness bound。它定义 inherent staleness：trajectory 用版本 `K` 生成，完成时 actor 已到版本 `M`，staleness 就是 `M-K`。实验里通常低于 3，最大观察到 4。
      evidence:: E8, E9

- ## Argument Map
    - **问题:** rollout 阶段占主要时间，reasoning 任务里 generation 可占 83.1% 总时间；trajectory 长度和环境延迟高度长尾，99 分位长度可比中位数大一个数量级。
      evidence:: E1, E2
    - **已有系统的缺陷 1:** colocated / synchronous 系统每轮要等整批 rollout 完成。短样本先结束也没用，trainer 最终还是被最慢 trajectory 卡住。
      evidence:: E2, E3
    - **已有系统的缺陷 2:** one-step / k-step async 虽然 rollout 和 train 分开，但仍然要求所有 rollout 按全局节奏同步权重。`k` 小则挡不住长尾，`k` 大则训练数据更旧，影响收敛。
      evidence:: E3
    - **已有系统的缺陷 3:** partial rollout 会中断正在生成的 trajectory，换新权重后继续生成。这样会带来反复 re-prefill KVCache 的开销，并让一条 trajectory 混多个 policy version，论文认为会伤害收敛。
      evidence:: E3, E12
    - **Laminar 的主张:** 扩展 RL post-training 的关键不是再找一个固定 staleness，而是取消全局同步点，让每条 trajectory 独立完成、独立入 buffer、独立决定何时更新 rollout 权重。
      evidence:: E4, E8

- ## Mechanism and Design
    - **Fully decoupled architecture:** Laminar 同时解耦 data dependency 和 parameter dependency。data 侧，trainer 不等 rollout batch 完成，而是从 experience buffer 抽已完成 trajectory。parameter 侧，rollout 不等全局同步，而是从本地 relay 拉权重。
      evidence:: E5
    - **Data module:** prompt pool 提供问题；partial response pool 保存生成中的 trajectory，用于故障恢复和在线分析；experience buffer 保存已完成 trajectory，并提供 writer / sampler 接口。
      evidence:: E5
    - **Relay worker:** 每台 rollout 机器有一个 CPU relay；master relay 接收 actor 新权重，再通过 RDMA 链式 pipeline broadcast 给其他 relays。这样避免 GPU-GPU 全局同步、GPU 显存 buffer 和 NCCL 竞争。
      evidence:: E6
    - **Rollout workflow:** rollout 从 prompt pool 拿 prompt，生成过程中把 partial state 流到 partial response pool；完成后写入 experience buffer；完成一个 batch 后从本地 relay 拉最新权重。
      evidence:: E5
    - **Trainer workflow:** trainer 并行地从 experience buffer 采样，执行 RL 更新；更新后把 actor 权重推给 master relay，然后马上进入下一轮，不等所有 rollout 完成权重同步。
      evidence:: E5, E6
    - **Dynamic repack trigger:** repack 主要由周期检查触发，例如每 5 秒；也会在 trainer 完成一次全局 batch 更新后触发，以便更快释放 rollout 去生成更接近当前 policy 的数据。
      evidence:: E7
    - **Repack 判断依据:** 论文不用固定“剩余请求数阈值”，而是用 KVCache utilization。rollout 进入尾部阶段时，等待队列已经没了，KVCache usage 从峰值下降，这时它就是候选 source rollout。
      evidence:: E7
    - **Repack 算法:** 把 underutilized rollouts 看成 bin packing：source rollout 是待搬的 item，destination rollout 是 bin。目标是尽量释放更多 source rollout，同时不超过 KVCache capacity 和 roofline batch size。
      evidence:: E7
    - **Fault tolerance:** rollout 失败时，partial response pool 保留中间状态，rollout manager 可重启 replica、迁移未完成 trajectory，或替换机器。relay 失败时，broadcast chain 可以快速重建。
      evidence:: E5, E6, E11

- ## Evaluation and Evidence
    - **实验环境:** 128 台机器，共 1024 张 H800-80GB；机器内 400GB/s NVLink，机器间 8 x 400Gbps。模型包括 Qwen2.5 7B / 32B / 72B。
      evidence:: E9
    - **任务:** DAPO-Math-17k 上的数学推理，以及多轮 tool-calling 任务；tool-calling rollout 会和 code sandbox 交互。max input/output 分别是 2K / 16K。
      evidence:: E9
    - **吞吐:** 数学任务上，Laminar 平均比 verl 快 2.56x，最高 5.49x；比 one-step staleness 平均快 1.98x；比 stream generation 平均快 1.93x；比 AReaL 平均快 1.39x。tool-calling 上平均提升 2.62x。
      evidence:: E10
    - **扩展性:** 在最大集群规模下，Laminar 相对所有 baseline 和模型尺寸平均快 3.34x；论文认为优势随 GPU 数增加而变大，因为全局同步和长尾等待在大规模下更严重。
      evidence:: E10, E13
    - **收敛:** 在 7B / 32B 数学任务上，相对 best baseline，Laminar 到达 reward 提升的 wall-clock 时间分别快约 1.77x / 1.59x。论文解释为：吞吐提升同时没有 partial rollout 的混版本 bias。
      evidence:: E10
    - **权重同步:** 相比 GPU-based global sync，Laminar rollout 等待时间平均最多降低 37%，best-case 最多降低 47%；actor stall 对 32B / 72B 分别只有 0.64s / 1.40s。
      evidence:: E11
    - **Repack 效果:** dynamic repack 让 generation throughput 提升 26%，平均 KVCache utilization 从 71.6% 到 82.2%，repack overhead 约 0.69s。
      evidence:: E11
    - **故障恢复:** 人为 kill 一台含两个 rollout replicas 的机器后，系统约 252s 恢复，训练不需要全局重启。
      evidence:: E11

- ## Technical Judgment
    - **最 solid 的结论:** Laminar 对“为什么加更多 rollout GPU 也不一定解决长尾”讲得非常清楚：如果系统仍然按全局 batch / 全局权重同步推进，短 trajectory 结束得再快也会被慢 trajectory 或同步点拖住。
      claim_kind:: analyst_assessment
    - **对我们最有用的点:** 它把 staleness 从一个固定配置参数，变成 trajectory 完成时自然产生的属性。这个思想可以支撑我们讲 freshness/staleness 应该进入系统控制面，而不是只当训练脚本里的常量。
      claim_kind:: analyst_assessment
    - **对 partial rollout 的批评:** Laminar 认为中断长 trajectory 再用新权重继续，会带来 KVCache 重算和一条 trajectory 混多个 policy version 的问题。这个点和我们之前讨论“旧策略动作污染 context”有直接关系。
      claim_kind:: analyst_assessment
    - **和 AReaL / Relax 的边界:** AReaL 更强调 partial rollout / interruption；Relax 强调 omni-modal 场景下 generation/training decoupling 和 micro-batch streaming；Laminar 的核心是去掉全局同步，并让完整 trajectory 保持单一 policy version。
      claim_kind:: analyst_assessment
    - **局限:** 它主要评估数学推理和 tool-calling，不定义 streaming video context 如何切 sample；experience sampling 被明确留作 future work；论文没有提供可直接复现的公开代码入口。
      claim_kind:: analyst_assessment
    - **一句话给项目:** Laminar 不是 streaming RL 论文，但它是“rollout 长尾如何变成系统瓶颈”的强证据。我们的 streaming RL 方案如果谈长尾、staleness、版本一致性，需要把 Laminar 当成必须对比的异步系统工作。
      claim_kind:: analyst_assessment

- ## Workflow Extraction
    - **初始模型:** Qwen2.5 7B / 32B / 72B；收敛实验用 Qwen2.5-Math-7B 和 Qwen2.5-32B。
    - **初始数据:** DAPO-Math-17k；数学推理和多轮 tool-calling。
    - **Rollout unit:** 完整 trajectory；可以是单轮 answer，也可以是多轮 code sandbox 交互。Laminar 避免一条 trajectory 内混多个 policy version。
    - **Rollout 输入:** prompt pool 里的 math / coding prompt；tool-calling 任务还会访问外部 code sandbox。
    - **Rollout 输出:** 完成的 trajectory，带生成 token、统计信息、policy version、reward 所需信息；中间状态写入 partial response pool。
    - **Trainer 输入:** experience buffer 中已完成的 trajectories；实验中按 GRPO group 组织，同一 prompt 16 responses。
    - **Reward:** rule-based reward；数学和 tool-calling 都按任务规则打分。
    - **Trainer 更新:** 主要使用 GRPO + Clip-Higher；trainer 更新完 actor 后推新权重到 master relay。
    - **资源架构:** trainer GPUs 与 rollout GPUs 分离；actor / critic / reference 在 trainer 侧分时执行；rollout 侧每机一个 CPU relay；rollout manager 负责监控、repack、故障恢复。
    - **对 streaming RL 的启发:** streaming RL 如果要求一条样本内上下文一致，Laminar 的“完整 trajectory 使用单一 policy version”比 partial rollout 更容易解释和审计；但 streaming context 的 sample sealing 仍然需要额外定义。

- ## Glossary
  collapsed:: true
    - trajectory-level asynchrony: 每条 trajectory 独立生成、独立完成、独立被 trainer 消费，而不是整批一起同步。
    - global weight synchronization: actor 更新后所有 rollout 按统一时间点接收新权重。
    - relay worker: 运行在 CPU 上的权重中继进程，保存最新 actor 权重，供 rollout 随时拉取。
    - dynamic repack: 把多个 underutilized rollout 上未完成的长尾 trajectory 合并到少数 rollout，释放其他 rollout 去拉新权重。
    - KVCache utilization: rollout GPU 上 KV cache 的占用率，用来判断是否进入尾部低利用阶段。
    - inherent staleness: trajectory 完成时自然产生的新旧版本差，定义为完成时 actor version 减去生成该 trajectory 的 policy version。
    - partial rollout: 中断正在生成的 trajectory，更新权重后继续生成；Laminar 认为它会带来 KV 重算和混版本问题。

- ## Evidence Index
  collapsed:: true
    - **E1:** metadata | arXiv and title block | high
      locator:: arXiv page; `paper.md`, abstract
      note:: title, authors, arXiv v1 date, HKU + ByteDance Seed, EuroSys 2026 accepted status.
    - **E2:** problem | Introduction and Background | high
      locator:: `paper.md`, Section 1; Section 2.1-2.2
      note:: rollout generation dominates training; trajectory length and environment latency are highly skewed; adding GPUs alone does not remove load imbalance.
    - **E3:** limitation | Limitations of existing asynchronous RL systems | high
      locator:: `paper.md`, Section 2.3
      note:: one-step/k-step staleness global sync, partial rollout re-prefill, mixed policy versions, staleness-throughput tradeoff.
    - **E4:** opportunity | Opportunity and Challenges | high
      locator:: `paper.md`, Section 2.4
      note:: trajectory-level asynchrony, experience buffer, natural staleness, challenges of async weight sync, per-rollout long tail, fault tolerance.
    - **E5:** architecture | Fully Decoupled Architecture Design | high
      locator:: `paper.md`, Section 3.1-3.3
      note:: rollout module, data module, relay workers, trainer, workflow, partial response pool, fault recovery.
    - **E6:** weight sync | Asynchronous Weight Synchronization Using Relay Workers | high
      locator:: `paper.md`, Section 4.1-4.3
      note:: CPU relays, master relay, RDMA chain broadcast, local PCIe pull, storage/GPU-sync limitations, relay fault recovery.
    - **E7:** repack | Bubble Elimination in Long-tail Trajectory Generation | high
      locator:: `paper.md`, Section 5.1-5.2
      note:: periodic repack, KVCache idleness metric, same-version grouping, Best-Fit trajectory consolidation.
    - **E8:** staleness | Trajectory-level Asynchrony Analysis | high
      locator:: `paper.md`, Section 6
      note:: inherent staleness definition, no configured staleness bound, typically under 3, experience sampling left orthogonal.
    - **E9:** implementation/eval setup | Implementation and Evaluation setup | high
      locator:: `paper.md`, Section 7; Section 8 setup
      note:: ~11k LoC, built on verl, Ray RPC, UCX, 1024 H800 GPUs, Qwen2.5 7B/32B/72B, DAPO-Math-17k, GRPO, rule-based reward.
    - **E10:** end-to-end results | Throughput and convergence | high
      locator:: `paper.md`, Section 8.1-8.2
      note:: speedups over verl/one-step/stream generation/AReaL, 3.34x at largest scale, convergence 1.77x/1.59x faster than best baseline.
    - **E11:** component results | Weight sync, repack, fault tolerance | high
      locator:: `paper.md`, Section 8.3-8.5
      note:: rollout wait reduction, actor stall time, 26% repack throughput improvement, KVCache utilization improvement, 252s recovery.
    - **E12:** related work | Related Work and Appendix C | medium
      locator:: `paper.md`, Section 9; Appendix C
      note:: comparison to partial rollout systems and discussion of mixed-version trajectories and experience sampling.
    - **E13:** appendix | Detailed Experiment Analysis | medium
      locator:: `paper.md`, Appendix B
      note:: small-scale vs large-scale performance; why global sync and KVCache recomputation limit baselines.
