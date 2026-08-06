- **Title:** Streaming Video Instruction Tuning
  **标题:** 流式视频指令微调
- **Summary:** Streamo turns offline video LLMs into streaming assistants by training them to emit Silence/Standby/Response state tokens on multi-task temporally annotated data, improving open-ended streaming instruction following while exposing long-context efficiency limits.
  **一句话总结:** Streamo 通过训练离线视频 LLM 在多任务时间标注数据上输出 Silence/Standby/Response 状态 token，将其转化为流式助手，在提升开放式流式指令遵循能力的同时揭示了长上下文效率的局限。
- **Paper Type:** system
  **论文类型:** 系统
- **Venue:** arXiv preprint 2026; arXiv:2512.21334v2
  **发表:** arXiv 预印本 2026; arXiv:2512.21334v2
- **Authors:** Jiaer Xia (Hong Kong Baptist University); Peixian Chen (Tencent Youtu Lab); Mengdan Zhang (Tencent Youtu Lab); Xing Sun (Tencent Youtu Lab); Kaiyang Zhou (Hong Kong Baptist University)
  **作者:** Jiaer Xia（香港浸会大学）; Peixian Chen（腾讯优图实验室）; Mengdan Zhang（腾讯优图实验室）; Xing Sun（腾讯优图实验室）; Kaiyang Zhou（香港浸会大学）
- **Keywords:** streaming video understanding, video LLM, instruction tuning, response timing, temporal grounding, time-sensitive QA, online multimodal assistants
  **关键词:** streaming video understanding, video LLM, instruction tuning, response timing, temporal grounding, time-sensitive QA, online multimodal assistants
- ## Quick Reference
    - **Why Read:** Read this for a concrete recipe for converting offline video LLMs into interactive streaming models: represent response timing as tokens, train on temporally aligned multi-task dialogues, and rebalance sparse response states.
      **阅读价值:** 阅读本文可获取将离线视频 LLM 转化为交互式流式模型的具体方案：将响应时机表示为 token，在时间对齐的多任务对话上进行训练，并重新平衡稀疏的响应状态。
      claim_kind:: analyst_assessment
      evidence:: E2, E4, E5
    - **One-Sentence Contribution:** Streamo improves streaming video instruction following by interleaving one-second video turns with three response-state tokens and training on Streamo-Instruct-465K with state-aware focal/frequency weighting.
      **一句话贡献:** Streamo 通过将逐秒视频回合与三种响应状态 token 交织，并在 Streamo-Instruct-465K 上采用状态感知的 focal/frequency 加权进行训练，从而提升流式视频指令遵循能力。
      evidence:: E2, E4, E5, E7
    - **Mental Model:** Think of the model as a live commentator with a built-in traffic light: red Silence for irrelevant context, yellow Standby for relevant-but-incomplete events, and green Response for the moment the answer should be emitted.
      **记忆模型:** 可将该模型想象为一位自带红绿灯的实时解说员：红色 Silence 表示无关上下文，黄色 Standby 表示相关但未完成的事件，绿色 Response 表示应当输出答案的时刻。
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest support is the combination of Streamo-Bench breadth, offline-retention results, and targeted ablations showing that both adaptive loss weighting and the Standby state matter.
      **最佳证据:** 最有力的证据来自 Streamo-Bench 的广度、离线能力保持结果以及针对性消融实验，后者表明自适应损失加权和 Standby 状态都不可或缺。
      evidence:: E11, E12, E13, E14
        - C1: Streamo-Bench; Streamo-7B vs listed online baselines; average score 55.3 vs best baseline 24.6; supports multi-instruction streaming generalization.
          C1：Streamo-Bench；Streamo-7B 与线上列出的 baselines 对比；平均分 55.3，对比最佳 baseline 24.6；支持多指令流式泛化。
          evidence:: E12
        - C2: Offline conversion; Qwen2.5-VL-7B base; average 63.9 vs 60.6 (+3.3); supports preserving or improving general video understanding after streaming tuning.
          C2：离线转换；Qwen2.5-VL-7B 基座；平均分 63.9 对比 60.6（+3.3）；支持流式调优后保持或提升通用视频理解能力。
          evidence:: E11
        - C3: Loss ablation; Qwen2.5-VL-3B on OVO forward-active tasks; focal loss raises REC/SSR/CRR from 6.45/20.99/41.67 under CE to 27.94/50.72/82.5.
          C3：损失消融；Qwen2.5-VL-3B 在 OVO forward-active 任务上；focal loss 将 CE 下的 REC/SSR/CRR 从 6.45/20.99/41.67 提升至 27.94/50.72/82.5。
          evidence:: E13
    - **Main Caveat:** The method still inherits unbounded-stream memory/latency growth, and the broad SOTA framing should be read carefully because Table 2 includes a ViSpeak row with higher OVO overall than Streamo-7B.
      **主要边界:** 该方法仍然继承了无界流的内存/延迟增长问题，且其宽泛的 SOTA 表述需审慎解读，因为 Table 2 中 ViSpeak 一行的 OVO overall 高于 Streamo-7B。
      claim_kind:: analyst_assessment
      evidence:: E10, E16
- ## Argument Map
    - **Problem and Stakes:** Offline video LLMs assume a bounded clip and answer after seeing the whole video, whereas streaming assistants must decide continuously, from partial observations, both whether enough evidence has arrived and what to say. The stakes are latency-sensitive interactive tasks such as narration, proactive alerts, event grounding, and answers whose truth changes over time.
      **问题与重要性:** 离线 video LLM 假设输入为有界片段，在看完整个视频后才作答；而流式助手必须基于部分观测持续做出决策，既判断是否已获得足够证据，也决定输出什么内容。其关键场景为延迟敏感的交互任务，如解说、主动告警、事件定位，以及随时间变化答案的问题。
      evidence:: E2, E3
    - **Prior Gap:** The paper frames prior online adaptations as either decoupled controller-plus-offline-model pipelines or narrow EOS-style response-timing training, which can trade accuracy for latency, lose coupling between perception and generation, or cover only limited task formats.
      **已有方法缺口:** 论文将此前的在线适配方案归纳为两类：解耦的控制器加离线模型管线，或窄化的 EOS 式响应时机训练。前者可能以精度换延迟、丢失感知与生成的耦合，后者则仅覆盖有限的任务格式。
      evidence:: E3, E14
    - **Key Insight:** Instead of adding an external streaming controller, make response timing part of the language-modeling target: the same decoder predicts Silence, Standby, or Response tokens and then generates the answer when the Response state is reached. Because these state tokens are sparse and imbalanced, the paper couples this representation with focal and per-batch frequency weighting.
      **关键洞见:** 不引入外部流式控制器，而是将响应时机纳入语言建模目标：同一 decoder 预测 Silence、Standby 或 Response tokens，并在达到 Response 状态后生成答案。由于这些状态 token 稀疏且分布不均衡，论文将此表示与 focal loss 及 per-batch frequency weighting 相结合。
      evidence:: E4, E5
    - **Claims:** The paper's supportable claim chain is that Streamo's state-token formulation plus Streamo-Instruct-465K improves streaming instruction following, preserves offline video ability, and benefits materially from the proposed loss and three-state design.
      **核心主张:** 论文可支持的 claim chain 是：Streamo 的 state-token 构建加上 Streamo-Instruct-465K 改善了流式指令跟随，保持了离线视频能力，并从所提损失与三状态设计中获得实质性收益。
      evidence:: E10, E11, E12, E13
        - C1: Streamo improves open-ended streaming instruction following on Streamo-Bench, reaching 55.3 average versus 24.6 for the strongest listed existing online baseline.
          C1：Streamo 在 Streamo-Bench 上提升了开放式流式指令跟随能力，平均分达到 55.3，而所列最强现有在线 baseline 为 24.6。
          evidence:: E12
        - C2: Streaming tuning does not simply sacrifice offline ability; Streamo-7B improves the Qwen2.5-VL-7B average from 60.6 to 63.9 across the paper's offline-oriented suite.
          C2：流式调优并非简单地牺牲离线能力；Streamo-7B 在论文的离线评测套件上将 Qwen2.5-VL-7B 的平均分从 60.6 提升至 63.9。
          evidence:: E11
        - C3: State-aware focal/frequency weighting improves proactive response learning under the reported 12:3:2 state-label imbalance.
          C3：在报告的 12:3:2 状态标签不平衡条件下，状态感知的 focal/frequency 加权改善了主动响应学习。
          evidence:: E13
        - C4: The Standby state is useful beyond a binary answer/silence or EOS design, especially for forward-active and grounding tasks.
          C4：Standby 状态超越了二元 answer/silence 或 EOS 设计的效用，尤其适用于 forward-active 和 grounding 任务。
          evidence:: E14
- ## Mechanism and Design
    - **Core Mechanism:** Streamo reformulates streaming video as interleaved multi-turn supervised fine-tuning: each video segment is paired with an assistant turn whose target begins with a response-state token. The state token acts as an inline control signal, so the model learns both temporal readiness and natural-language output in the same next-token prediction objective.
      **核心机制:** Streamo 将流式视频重新表述为交错多轮监督微调：每个视频片段配对一个 assistant 轮次，其目标以 response-state token 开头。该状态 token 充当内联控制信号，使模型在同一个 next-token prediction 目标下同时学习时序就绪性与自然语言输出。
      evidence:: E4
    - **Data / Control Flow:** Training simulates a stream by splitting a video into one-second turns with absolute time markers, inserting task instructions at appropriate turns, and requiring the assistant to emit Silence, Standby, or Response at every step. The Response token gates answer generation; Silence and Standby continue accumulation without final output.
      **数据/控制流:** 训练通过将视频分割为带绝对时间标记的一秒轮次来模拟流，在适当轮次插入任务指令，并要求 assistant 在每一步输出 Silence、Standby 或 Response。Response token 控制答案生成的开启；Silence 和 Standby 继续累积而不产生最终输出。
      evidence:: E4, E9
        - Step 1: Convert an offline clip into ordered segments with time tags such as <2s-3s>, so every training turn has an explicit temporal boundary.
          步骤 1：将离线片段转换为带时间标签（如 <2s-3s>）的有序片段，使每个训练轮次具有明确的时序边界。
          evidence:: E4
        - Step 2: Predict <Silence> for irrelevant or insufficient context, <Standby> for relevant but incomplete evidence, and <Response> when the model should answer.
          步骤 2：在不相关或上下文不足时预测 <Silence>，在相关但证据不完整时预测 <Standby>，在模型应当回答时预测 <Response>。
          evidence:: E4
        - Step 3: For state tokens, the loss applies `$w_{\mathrm{focal}}(x_i)=(1-p_{c_i})^{\gamma}$` and `$\alpha_k=\frac{1}{|\mathcal{S}|}\frac{\sum_{j\in\mathcal{S}} n_j}{n_k}$` to cross-entropy, while ordinary tokens keep standard CE.
          步骤 3：对于状态 token，损失对 cross-entropy 应用 `$w_{\mathrm{focal}}(x_i)=(1-p_{c_i})^{\gamma}$` 和 `$\alpha_k=\frac{1}{|\mathcal{S}|}\frac{\sum_{j\in\mathcal{S}} n_j}{n_k}$`，而普通 token 保持标准 CE。
          evidence:: E5
    - **Design Decisions:** The major design decisions all target the same bottleneck: sparse, temporally precise response decisions must be learned without detaching them from language generation. The paper's ablations most directly support the Standby token and adaptive state-loss choices.
      **设计决策:** 主要设计决策均指向同一瓶颈：稀疏且时序精确的响应决策必须在不脱离语言生成的前提下学习。论文的消融实验最直接地支持了 Standby token 和自适应状态损失这两个选择。
      claim_kind:: analyst_assessment
      evidence:: E3, E13, E14
        - Need: avoid latency and decoupling from an auxiliary controller; choice: integrate response-state tokens into the decoder's normal token stream; tradeoff: the LLM context now carries continuous control history.
          需求：避免来自辅助控制器的延迟与解耦；选择：将 response-state token 集成到 decoder 的正常 token 流中；权衡：LLM 上下文现在携带连续的控制历史。
          evidence:: E3, E4
        - Need: distinguish irrelevant frames from relevant-but-unfinished events; choice: add <Standby>; alternative: EOS-only timing; evidence shows EOS lowers OVOBench FAR and forward-grounding scores.
          需求：区分不相关帧与相关但未完成的事件；选择：添加 <Standby>；替代方案：仅用 EOS 的时序设计；证据表明 EOS 会降低 OVOBench FAR 和 forward-grounding 分数。
          evidence:: E14
        - Need: prevent the model from collapsing toward Silence under imbalanced labels; choice: dynamic focal plus per-batch frequency weighting; alternative: vanilla CE or fixed loss scaling, both weaker in Table 4.
          需求：在标签不平衡时防止模型塌缩至 <Silence>；选择：动态 focal 加每 batch 频率加权；替代方案：原始 CE 或固定 loss 缩放，两者在 Table 4 中均较弱。
          evidence:: E5, E13
    - **Implementation Surface:** The reported implementation is deliberately close to standard SFT: Qwen2.5-VL 3B/7B bases, frozen vision encoder, trainable connector and LLM, one epoch, batch size 512, learning rate 1e-5, one-second turns, 1 fps sampling, and gamma 2. Streamo-Instruct-465K supplies the temporal multi-task supervision rather than requiring architectural surgery.
      **实现边界:** 所报告的实现刻意贴近标准 SFT：Qwen2.5-VL 3B/7B 基座、冻结 vision encoder、可训练的 connector 和 LLM、一个 epoch、batch size 512、学习率 1e-5、一秒轮次、1 fps 采样、gamma 2。Streamo-Instruct-465K 提供时序多任务监督，而无需架构改动。
      evidence:: E7, E9
        - Training surface: the vision encoder is frozen, while the connector and LLM are updated under a unified setup across models.
          训练层面：vision encoder 被冻结，而 connector 和 LLM 在跨模型的统一设置下进行更新。
          evidence:: E9
        - Data surface: each video can carry multiple task annotations with unified temporal response boundaries, addressing heterogeneous labeling across source datasets.
          数据层面：每个视频可携带多个任务标注，并采用统一的时序响应边界，以解决不同源数据集间的异构标注问题。
          evidence:: E6, E7
        - Artifact surface: the paper promises public release of code, models, and datasets, but the provided text states this as future availability.
          产物层面：论文承诺公开发布代码、模型和数据集，但所提供的文本将其表述为未来可用。
          evidence:: E17
- ## Evaluation and Evidence
    - **Setup:** Evaluation spans online OVO-Bench, offline/general video benchmarks, and Streamo-Bench, a 300-video/3,000-task mixed instruction benchmark. Streamo-Bench mixes mIoU for grounding, Qwen2.5-VL-72B pairwise win rate for narration/caption, and TSQA content-plus-time correctness with a 3-second timestamp tolerance.
      **实验设置:** 评估涵盖在线 OVO-Bench、离线/通用视频 benchmark 以及 Streamo-Bench——一个包含 300 个视频/3,000 个任务的混合指令 benchmark。Streamo-Bench 混合使用 mIoU 评估 grounding、Qwen2.5-VL-72B 成对胜率评估 narration/caption，以及 TSQA 的内容加时间正确性（3 秒时间戳容忍度）。
      evidence:: E8, E9, E15
    - **Claim-Evidence Matrix:** The evidence is strongest where the paper combines controlled architecture/training comparisons with task-specific benchmarks, and weakest where broad SOTA claims depend on baseline selection or LLM-judge evaluation.
      **主张-证据矩阵:** 证据在论文将受控的架构/训练比较与任务特定 benchmark 相结合时最为充分，而在宽泛的 SOTA 声明依赖 baseline 选择或 LLM-judge 评估时最为薄弱。
      claim_kind:: analyst_assessment
      evidence:: E10, E12, E15
        - C1 multi-task streaming: supported by Streamo-Bench, where Streamo-7B is highest among listed models across a heterogeneous average, though the average combines different metric types.
          C1 多任务流式：由 Streamo-Bench 支撑，其中 Streamo-7B 在所列模型的异构平均上最高，尽管该平均结合了不同类型的指标。
          evidence:: E12, E15
        - C2 offline retention: supported by Table 3, where Streamo-7B improves the Qwen2.5-VL-7B average and exceeds StreamingVLM on the reported offline benchmark columns.
          C2 离线保持：由 Table 3 支撑，其中 Streamo-7B 改善了 Qwen2.5-VL-7B 的平均值，并在所报告的离线 benchmark 列上超过 StreamingVLM。
          evidence:: E11
        - C3 response-state training: supported by ablations showing focal loss over CE/fixed scaling and three-state design over EOS-only on response-timing-sensitive tasks.
          C3 响应状态训练：由消融实验支撑，显示 focal loss 优于 CE/固定缩放，三状态设计优于仅 EOS 在响应时序敏感任务上的表现。
          evidence:: E13, E14
    - **Headline Results:** The headline results support Streamo as a strong streaming-instruction model, but not every broad comparison is clean: the OVO table itself contains a higher ViSpeak overall score. No statistical uncertainty, repeat counts, or hardware-normalized latency numbers are reported in the supplied text.
      **关键结果:** 核心结果支持 Streamo 作为强大的 streaming-instruction 模型，但并非所有宽泛对比都干净：OVO 表本身包含更高的 ViSpeak 总分。所提供文本未报告统计不确定性、重复次数或硬件归一化的延迟数据。
      claim_kind:: analyst_assessment
      evidence:: E10, E11, E12
        - Online OVO: Streamo-7B 1fps scores 55.61 overall vs Dispider-7B 41.78 (+13.83), and 2fps evaluation scores 57.86; caveat: ViSpeak-7B is listed at 61.08 overall.
          在线 OVO：Streamo-7B 1fps 总分 55.61，对比 Dispider-7B 41.78（+13.83），2fps 评估得分 57.86；注意：ViSpeak-7B 总分列为 61.08。
          claim_kind:: analyst_assessment
          evidence:: E10
        - Offline/general benchmarks: Streamo-7B averages 63.9 vs Qwen2.5-VL-7B 60.6 (+3.3), with reported gains on MVBench, VideoMME, and LongVideoBench.
          离线/通用基准：Streamo-7B 平均 63.9，对比 Qwen2.5-VL-7B 60.6（+3.3），在 MVBench、VideoMME 和 LongVideoBench 上有报告的提升。
          evidence:: E11
        - Streamo-Bench: Streamo-7B scores 55.3 average vs 24.6 for the strongest listed existing online baseline, with especially large margins on grounding and dense captioning.
          Streamo-Bench：Streamo-7B 平均得分 55.3，对比最强已列出现有在线基线的 24.6，在 grounding 和 dense captioning 上差距尤为显著。
          evidence:: E12
    - **Ablations and Sensitivity:** The ablations are important because they isolate two non-obvious pieces of the method: adaptive reweighting for sparse state tokens and the Standby state for relevant-but-incomplete events. The 2fps evaluation suggests some test-time sampling-rate robustness, but it is only reported for the OVO configuration in the main table.
      **消融与敏感性:** 消融实验很重要，因为它们隔离了方法中两个非显而易见的部分：稀疏 state token 的自适应重加权，以及针对相关但不完整事件的 Standby state。2fps 评估表明具有一定的测试时采样率鲁棒性，但仅在主表的 OVO 配置中进行了报告。
      evidence:: E10, E13, E14
        - Loss ablation: on Qwen2.5-VL-3B, focal loss improves REC/SSR/CRR to 27.94/50.72/82.5 from CE's 6.45/20.99/41.67 and fixed scaling's 18.62/41.02/49.17.
          损失消融：在 Qwen2.5-VL-3B 上，focal loss 将 REC/SSR/CRR 从 CE 的 6.45/20.99/41.67 和 fixed scaling 的 18.62/41.02/49.17 提升至 27.94/50.72/82.5。
          evidence:: E13
        - State-design ablation: replacing the three-state design with EOS-only drops OVOBench average from 52.33 to 48.52 and forward grounding from 14.7 to 9.3.
          状态设计消融：将三状态设计替换为 EOS-only 使 OVOBench 平均分从 52.33 降至 48.52，前向 grounding 从 14.7 降至 9.3。
          evidence:: E14
        - Sampling-rate sensitivity: the table reports Streamo-7B trained at 1fps and evaluated at 2fps improving OVO overall from 55.61 to 57.86, but broader frame-rate sweeps are not reported.
          采样率敏感性：表格报告 Streamo-7B 以 1fps 训练、2fps 评估，将 OVO 总分从 55.61 提升至 57.86，但未报告更广范围的帧率扫描。
          evidence:: E10
    - **Reproducibility Gaps:** The paper gives enough high-level training and metric detail to understand the recipe, but several fields needed for robust reproduction or systems comparison remain unspecified in the supplied text. The largest practical blocker is that public artifacts are promised rather than evidenced as already available.
      **可复现性缺口:** 论文提供了足够的高层训练和评估指标细节来理解方法配方，但稳健复现或系统对比所需的若干字段在所提供文本中仍未指定。最大的实际障碍是公开 artifacts 为承诺发布而非已证实可用。
      claim_kind:: analyst_assessment
      evidence:: E9, E15, E17
        - Artifact availability: code, models, and datasets are stated as future public releases; exact repository state, licenses, preprocessing scripts, and checkpoints are not reported here.
          Artifact 可用性：代码、模型和数据集声明为未来公开发布；具体仓库状态、许可证、预处理脚本和 checkpoints 此处未报告。
          claim_kind:: analyst_assessment
          evidence:: E17
        - Training resources: batch size, learning rate, epoch count, frozen modules, and sampling rate are reported, but GPU type/count, wall-clock time, memory use, and serving latency are not reported.
          训练资源：报告了 batch size、学习率、epoch 数量、冻结模块和采样率，但未报告 GPU 类型/数量、wall-clock time、内存使用情况以及推理延迟。
          claim_kind:: analyst_assessment
          evidence:: E9, E16
        - Evaluation uncertainty: Streamo-Bench caption/narration uses an LLM judge and TSQA uses a 3-second tolerance, but judge agreement, repeated runs, and confidence intervals are not reported.
          评估不确定性：Streamo-Bench caption/narration 使用了 LLM judge，TSQA 使用 3 秒容忍度，但未报告 judge 一致性、重复运行结果和置信区间。
          claim_kind:: analyst_assessment
          evidence:: E12, E15
- ## Technical Judgment
    - **What Holds Up:** The central reframing is technically plausible and useful: response timing becomes a supervised token prediction problem compatible with standard multimodal SFT, not a separate controller. The ablations give credible mechanism-level evidence that both adaptive state-token weighting and the Standby state improve timing-sensitive behavior.
      **站得住的结论:** 其核心重构在技术上是合理且有用的：响应时序成为一个与标准多模态 SFT 兼容的监督 token 预测问题，而不是一个独立的 controller。消融实验提供了可信的机制级证据，表明自适应 state-token 加权和 Standby state 均能改善对时序敏感的行为。
      claim_kind:: analyst_assessment
      evidence:: E4, E13, E14
        - The three-token control interface is simple enough to port across base models because it lives in the dialogue format and loss rather than a new perception architecture.
          三 token 控制接口足够简单，可以跨基础模型移植，因为它存在于对话格式和 loss 中，而不是一种新的感知架构。
          claim_kind:: analyst_assessment
          evidence:: E4, E9
        - The loss and EOS ablations are more convincing than aggregate benchmark wins because they directly perturb the proposed response-timing mechanisms.
          loss 和 EOS 消融实验比总体 benchmark 胜出更具说服力，因为它们直接对所提出的响应时序机制进行了扰动。
          claim_kind:: analyst_assessment
          evidence:: E13, E14
    - **Where It May Fail:** The approach does not solve the systems problem of truly unbounded streams: accumulating dialogue/video context without specialized cache or token management can make memory and latency prohibitive. It also depends heavily on the quality and temporal precision of generated annotations and on evaluation protocols that include heterogeneous metrics and LLM judging.
      **可能失效之处:** 该方法并未解决真正的无界流的系统级问题：在没有专门的 cache 或 token 管理的情况下累积对话/视频上下文，可能会使内存和延迟变得不可接受。它还在很大程度上依赖于生成标注的质量和时间精度，以及包含异构指标和 LLM judging 的评估协议。
      claim_kind:: analyst_assessment
      evidence:: E6, E15, E16
        - Systems boundary: benefits should diminish as stream length exceeds feasible context or KV-cache budgets unless pruning, compression, or sliding-window attention is added.
          系统边界：随着流长度超过可行的上下文或 KV-cache 预算，其收益应该会递减，除非添加剪枝、压缩或滑动窗口注意力机制。
          claim_kind:: analyst_assessment
          evidence:: E16
        - Baseline boundary: the paper's SOTA wording should be narrowed because Table 2 lists ViSpeak-7B with 61.08 OVO overall, above Streamo-7B's 55.61 and 2fps 57.86.
          基线边界：论文的 SOTA 措辞应当收窄，因为 Table 2 列出 ViSpeak-7B 的 OVO 总体得分为 61.08，高于 Streamo-7B 的 55.61 和 2fps 的 57.86。
          claim_kind:: analyst_assessment
          evidence:: E10
        - Evaluation boundary: averaging mIoU, LLM-judge win rates, and TSQA accuracy/recall is useful diagnostically but not a single clean operational metric for latency-quality tradeoffs.
          评估边界：对 mIoU、LLM-judge 胜率和 TSQA 准确率/召回率取平均值在诊断上是有用的，但并不是一个用于权衡延迟与质量的单一且干净的操作性指标。
          claim_kind:: analyst_assessment
          evidence:: E12, E15
    - **Relation to Other Work:** Relative to controller-based streaming adapters such as Dispider and StreamBridge, Streamo moves the decision policy into the same decoder that generates text. Relative to EOS-only approaches such as VideoLLM-Online or StreamingVLM, the Standby token provides an intermediate temporal state; relative to QA-centric streaming benchmarks, Streamo-Bench tests mixed open-ended tasks.
      **与已有工作的关系:** 相较于基于 controller 的流式适配器（如 Dispider 和 StreamBridge），Streamo 将决策策略移至生成文本的同一个 decoder 中。相较于仅依赖 EOS 的方法（如 VideoLLM-Online 或 StreamingVLM），Standby token 提供了一个中间的时间状态；相较于以 QA 为中心的流式 benchmark，Streamo-Bench 测试了混合的开放式任务。
      claim_kind:: analyst_assessment
      evidence:: E3, E14, E15
    - **Transferable Lesson:** For interactive streaming tasks, model readiness as an explicit sequence of latent states, not as a binary answer/no-answer event; an intermediate relevant-but-incomplete state can preserve temporal alignment until sufficient evidence arrives. When such states are rare, rebalance them dynamically rather than relying on vanilla next-token CE.
      **可迁移启发:** 对于交互式流式任务，应将模型就绪状态建模为隐状态的显式序列，而非二元的「有答案/无答案」事件；一个中间的「相关但不完整」状态可以在充分证据到达之前保持时间对齐。当此类状态稀有时，应动态重平衡而非依赖普通的 next-token CE。
      claim_kind:: analyst_assessment
      evidence:: E4, E5, E13, E14
- ## Glossary
  collapsed:: true
    - Streamo: The paper's streaming video LLM framework/model; the name's 'o' is described as 'omni' for multi-task and multimodal capabilities.
      Streamo：论文提出的流式视频 LLM 框架/模型；名称中的 'o' 被描述为 'omni'，表示多任务与多模态能力。
    - Streamo-Instruct-465K: A temporally annotated multi-task instruction-tuning dataset for streaming video; built from 400K curated samples plus offline video QA, over 135,875 videos.
      Streamo-Instruct-465K：一个用于流式视频的时间标注多任务指令微调数据集；由 400K 精选样本加上离线视频 QA 构成，涵盖 135,875 个视频。
    - Streamo-Bench: A 300-video, 3,000-task benchmark for mixed streaming instructions including grounding, narration, dense captioning, and time-sensitive QA.
      Streamo-Bench：一个包含 300 个视频、3,000 个任务的基准，用于混合流式指令，包括 grounding、叙述、dense captioning 和时间敏感 QA。
    - <Silence>, <Standby>, <Response>: Special response-state tokens inserted into assistant turns: no output, relevant-but-incomplete context, and answer-ready output respectively.
      <Silence>、<Standby>、<Response>：插入 assistant 回合中的特殊响应状态 token，分别表示无输出、相关但不完整的上下文、以及答案就绪的输出。
    - Standby state: The intermediate state that marks an event as relevant before it is complete; it is the key difference from EOS-only timing formulations.
      Standby state：在事件完整之前将其标记为相关的中间状态；这是与仅基于 EOS 的时间建模方式的关键区别。
    - Time-Sensitive QA (TSQA): Questions whose answers change over time; evaluation requires matching both answer content and timestamp within a specified tolerance.
      Time-Sensitive QA (TSQA)：答案随时间变化的问题；评估要求在指定容差范围内同时匹配答案内容与时间戳。
    - mIoU: Mean temporal Intersection over Union between predicted and ground-truth event intervals; used for Streamo-Bench grounding tasks.
      mIoU：预测事件区间与真实事件区间之间的平均时间 Intersection over Union；用于 Streamo-Bench 的 grounding 任务。
    - Focal/frequency state-token loss: A modified cross-entropy for the three state tokens that combines token hardness via focal weighting with inverse batch-frequency alpha weights.
      Focal/frequency state-token loss：针对三个状态 token 的改进交叉熵损失，将基于 focal 加权的 token 难度与逆批次频率 alpha 权重相结合。
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/metadata | Title block | high
      locator:: paper header
      quote:: arXiv:2512.21334v2 [cs.CV] 10 Apr 2026. Streaming Video Instruction Tuning. Jiaer Xia, Peixian Chen, Mengdan Zhang, Xing Sun, Kaiyang Zhou. Hong Kong Baptist University; Tencent Youtu Lab.
    - **E2:** method/paper_statement | Abstract | high
      locator:: Abstract
      quote:: We present Streamo, a real-time streaming video LLM that serves as a general-purpose interactive assistant. Unlike existing online video models that focus narrowly on question answering or captioning, Streamo performs a broad spectrum of streaming video tasks, including real-t...
    - **E3:** gap/paper_statement | 1. Introduction | high
      locator:: paragraphs on streaming requirements and prior controllers
      quote:: Existing offline models struggle to meet the demands of the streaming setting because they are designed to process entire clips before producing a single output. Recent studies have attempted to extend offline video models for streaming by introducing a separate decision modul...
    - **E4:** method/implementation_detail | 3.2 Data Structure | high
      locator:: state-token formulation and Table 1
      quote:: To simulate streaming scenarios during training, we reformulate the single-turn offline format into a multi-turn dialogue structure. A complete video is temporally segmented into N contiguous segments, each annotated with temporal boundaries using special markers. Three discre...
    - **E5:** algorithm/implementation_detail | 3.3 Training | high
      locator:: loss definition
      quote:: The multi-turn streaming format introduces severe class imbalance among the three response states. In typical streaming scenarios, <Silence> tokens dominate the distribution, often more than 80% of the time, while <Response> tokens are sparse. To mitigate this, we apply focal...
    - **E6:** method/paper_statement | 4.1 Data Construction | high
      locator:: annotation protocol overview
      quote:: We predefined multiple tasks spanning different response granularities, assigning each video several types of task annotations. A unified annotation protocol is applied across datasets, avoiding inconsistencies and biases. Each video carries multiple task types with clearly de...
    - **E7:** metadata/paper_statement | 4.2 Statistics | high
      locator:: dataset statistics paragraph and Figure 3
      quote:: Using a unified annotation standard and protocol, we labeled and curated a total of 400K valid samples and additionally merged offline video QA data from the LLaVA-Video dataset, culminating in Streamo-Instruct-465K. We integrated multiple open-source video datasets as sources...
    - **E8:** experiment_setup/paper_statement | 5.2 Benchmarks | high
      locator:: benchmark setup paragraph
      quote:: We evaluated our model across three dimensions of benchmarks: Online, Offline, and Stream Instruction. For the online setting, we adopted OVO-Bench. The offline evaluation used MVBench, TempCompass, VideoMME, and LongVideoBench. We constructed StreamoBench, which includes 300...
    - **E9:** implementation/implementation_detail | 5.3 Implementation Details | high
      locator:: training setup paragraph
      quote:: Across all models, we use a unified training setup. Full parameter tuning is applied with the vision encoder frozen, and only the connector and the LLM will be updated. Training runs for a single epoch with a batch size of 512 and a learning rate of 1 x 10^-5. Each video is sp...
    - **E10:** result/experiment_result | 5.4 Main Results | high
      locator:: Table 2 and accompanying text
      quote:: Table 2 reports Dispider-7B Overall Avg. 41.78, ViSpeak-7B Overall Avg. 61.08, Streamo-7B at 1fps Overall Avg. 55.61, and Streamo-7B at 2fps Overall Avg. 57.86. The text states that Streamo-7B exceeds Dispider by +13.83 average performance.
    - **E11:** result/experiment_result | 5.4 Main Results | high
      locator:: Table 3
      quote:: Table 3 reports Qwen2.5-VL-7B Avg 60.6 and Streamo-7B Avg 63.9 (+3.3), with MVBench 72.3 (+2.7), VideoMME 67.9 (+2.8), and LongVideoBench 59.2 (+3.2). StreamingVLM-7B reports MVBench 69.2, VideoMME 65.1, and LongVideoBench 59.0.
    - **E12:** result/experiment_result | 5.4 Main Results | high
      locator:: Table 5
      quote:: Table 5 reports Streamo-Bench results: Streamo-7B reaches Forward Grounding 29.4, Backward Grounding 38.3, Narration 75.9, Dense Caption 72.8, TSQA Accuracy 51.6, TSQA Recall 63.9, Average 55.3. The strongest listed existing online baseline average is StreamingVLM-7B at 24.6.
    - **E13:** ablation/ablation | 5.5 Ablation | high
      locator:: Table 4 and ablation discussion
      quote:: In Streamo-Instruct-465K, the empirical ratio of state labels is approximately <Silence>:<Standby>:<Response> = 12:3:2. Table 4 shows Qwen2.5-VL-3B on OVO Forward Active tasks: CrossEntropy 6.45/20.99/41.67, Loss Scale 18.62/41.02/49.17, and Focal Loss 27.94/50.72/82.5 for REC...
    - **E14:** ablation/ablation | A.5 Further Analysis of the Three-State Design | high
      locator:: Table 7
      quote:: Table 7 compares Streamo-3B with an EOS-only variant on the same Streamo-Instruct dataset: Streamo-3B has OVOBench RTVP 61.51, BT 41.76, FAR 53.72, AVG 52.33, Forward Grounding 14.7; the EOS variant has 60.93, 39.43, 45.22, 48.52, and 9.3.
    - **E15:** experiment_setup/paper_statement | C.2 Metric | high
      locator:: Streamo-Bench metric definitions
      quote:: For grounding tasks, performance is measured using mean Intersection over Union. Narration and caption quality are assessed via pairwise comparison against Qwen2.5-VL-72B. For Time-Sensitive QA, a prediction must be correct in both its content and its timestamp; the timestamp...
    - **E16:** limitation/limitation | 7. Limitations and Future Work | high
      locator:: limitations paragraph
      quote:: Our current pipeline lacks specialized long-sequence optimizations, leading to significant memory and latency costs that become prohibitive as sequence length grows. The paper proposes integrating KV-cache management, visual token pruning, sliding-window attention, and adaptiv...
    - **E17:** metadata/paper_statement | 1. Introduction | high
      locator:: contributions paragraph
      quote:: We establish a comprehensive benchmark for streaming video instruction-following and provide strong baseline models for future research. All research resources including code, models, and datasets will be made publicly available.
