- **标题:** ProactiveLLM：为流式大语言模型学习主动交互
- **一句话总结:** ProactiveLLM 训练流式大语言模型（能在输入还没完全到达时就开始生成输出的模型）去感知部分输入在语义上是否已经足够，从而在不依赖外部时间标注的情况下，降低延迟并减少冗余的上下文使用。
- **论文类型:** 系统
- **发表:** ICML 2026
- **作者:** Junlong Tong（Eastern Institute of Technology, Ningbo；Shanghai Jiao Tong University）、Yao Zhang（Eastern Institute of Technology, Ningbo）、Anhao Zhao（Eastern Institute of Technology, Ningbo；Hong Kong Polytechnic University）、Yingqi Fan（Eastern Institute of Technology, Ningbo）、Yunpu Ma（Munich Center for Machine Learning, LMU）、Xiaoyu Shen（Eastern Institute of Technology, Ningbo）
- **关键词:** 流式大语言模型、主动交互、语义充分性、掩码流式语言建模、自蒸馏、延迟-质量权衡
- ## Orientation
    - **背景:** 流式语言处理的工作要求模型在输入不断到来的同时进行听取和回答，而不是等到整条消息接收完毕。其关键前提是语义充分性（semantic sufficiency）：即局部输入已经包含足够含义、可以安全地生成下一个输出的那个时间点。
      claim_kind:: analyst_assessment
    - **通俗问题:** 在实时语音、对话或长文本中，等待型系统会显得反应迟缓，而回答太早的系统又可能根据错误的线索去猜测。
      claim_kind:: analyst_assessment
    - **为何困难:** 有用的证据并不总是以稳定的节奏到来；有时它出现得早，有时出现得晚，而模型只能看到一段不断向前移动的前缀。
      claim_kind:: analyst_assessment
    - **一句话核心思路:** 在许多局部视图上训练模型，使模型自身的不确定性和注意力成为判断何时继续读取、何时开始写出的信号。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **阅读价值:** 把这篇论文当作一篇系统论文来读，主题是那些在输入还在到达时就开始作答的模型（流式大语言模型），重点关注固定的读/写时序与内容感知的交互时机之间的差距。
      claim_kind:: analyst_assessment
      evidence:: E1, E2
    - **一句话贡献:** ProactiveLLM 改进了流式生成：它训练模型基于部分输入所做的预测，使其与基于完整输入时的行为保持一致，这样模型就能凭借自身的不确定性来决定何时作答。
      evidence:: E3, E7
    - **记忆模型:** 想象一个专注的倾听者：在还有几个答案都说得通的时候继续听，一旦关键线索让某一个答案清晰凸显出来，就开口说话。
      claim_kind:: analyst_assessment
    - **最佳证据:** 最有力的证据是：ProactiveLLM 在文本和语音任务上都改善了质量与延迟的权衡，其中在固定时序会失效的非单调问答任务上收益最大。
      evidence:: E10, E11, E12
        - 支持 C2：使用 Qwen3-4B 做文本流式处理；对比基线为 wait-k 和对齐监督（alignment-supervised）方法；用 BLEU/F1 配合平均交互滞后（average interaction lag，AIL）与每输出词读取覆盖率（read coverage per output token，RCO）来评估；在短问答任务上，ProactiveLLM 在低延迟下比用 GPT-5.4 生成的对齐数据高出 10.62 的 F1，在高延迟下高出 8.15 的 F1；支持度为中等，因为文中没有报告重复次数和方差。
          evidence:: E10, E11
        - 支持 C3：使用 Qwen2-Audio 做语音流式处理；对比基线为批处理和 wait-k；用 WER/F1 配合秒级的 AIL 和 RCO 来评估；Proactive-Entropy 在 Spoken-SQuAD 上达到 71.12 的 F1，而批处理为 72.15，同时把 AIL 从 31.02 秒降到 21.26 秒；支持度为中等，因为没有报告不确定性。
          evidence:: E12
        - 支持 C4：进行组件消融实验；对比完整模型与去掉 MSLM、去掉蒸馏（Distill）的版本；绘制质量-延迟的帕累托（Pareto）曲线；去掉组件会使曲线向下和向右移动（即质量变差、延迟变大），而 KL 系数相对不敏感；支持度为中等，因为图中数值只做了部分汇总。
          evidence:: E13
    - **主要边界:** 该方法仍然需要校准阈值：如果某个局部线索看起来已经足够，但后续证据又将其推翻，主动写出就可能出错；论文自己的案例研究通过更保守地等待来解决这一问题。
      claim_kind:: analyst_assessment
      evidence:: E17
- ## Argument Map
    - **问题与重要性:** 流式大语言模型（streaming LLM）在输入仍在到来的过程中就生成输出，由交互调度器 phi(t) 控制，phi(t) 表示在输出步 t 时可见的输入边界。其关键意义在于：在不损失任务质量的前提下，降低延迟并减少冗余的上下文处理。
      evidence:: E1, E4
    - **已有方法缺口:** 以往的流式方法要么把何时读取、何时写出写死，比如 wait-k 调度；要么从任务特定的标注、时间戳、切分标签或更强的教师模型中学习时机；这使得时机判断变得被动，且调整代价高昂。
      evidence:: E2
    - **关键洞见:** 论文的核心洞见是：先训练模型的隐藏状态（hidden states），让它主动暴露出「信息是否已经足够」的线索，之后再挂上一个轻量的决策策略。这样做把「流式处理能力的学习」和「推理时使用的具体读/写规则」分离开来。
      evidence:: E3, E8
    - **核心主张:** 论文的主张涉及四个方面：内生的时机线索、即插即用的决策头、跨模态迁移，以及各组件的必要性。
      evidence:: E3, E10, E12, E13
        - C1：基于掩码的流式训练加上同步特权自蒸馏（Synchronized Privileged Self-Distillation，SPSD），能够在没有外部时机标注、也没有更强教师模型的情况下，从部分输入中培养出「语义充分性」（semantic sufficiency，即可见前缀已包含足够含义）的线索。
          evidence:: E3, E6, E7
        - C2：利用模型内部的注意力或熵的决策头，能把这些线索转化为读/写调度方案。在文本任务上，这种方案相比固定的 wait-k 基线以及代价高昂的对齐监督基线，改善了质量与延迟之间的权衡。
          evidence:: E8, E10, E11
        - C3：该框架可以跨越不同的骨干模型和不同模态进行迁移，其中包括因果式语音输入模型。在这类模型上，它能保持接近批处理（batch）水平的质量，同时延迟低于批处理或固定调度方案。
          evidence:: E5, E9, E12
        - C4：要获得稳健的主动式行为，掩码流式语言建模（Masked Streaming Language Modeling，MSLM）和批处理侧的锚点两者缺一不可；而 KL 散度（KL-divergence）系数的具体取值并不是性能提升的主要来源。
          evidence:: E13
- ## Mechanism and Design
    - **核心机制:** 掩码流式语言建模（Masked Streaming Language Modeling，MSLM）把未来的输入词元（token）藏在单调递增的读取边界之后，因此每个输出词元都从一个符合真实情况的部分前缀（prefix）中学习。同步特权自蒸馏（Synchronized Privileged Self-Distillation，SPSD）让同一个正在训练演化的模型既充当拥有完整上下文的教师，又充当只有部分上下文的学生，二者之间采用较小的 top-k logit 对齐，而不是强行完全匹配。
      evidence:: E6, E7
    - **数据/控制流:** 在推理时，进入的文本或因果式语音特征被分别加入到独立的输入/输出位置以及一个键值缓存（KV cache，即在解码过程中被复用的注意力状态）中；在生成每个输出之前，决策头会在「读」（Read）和「写」（Write）之间做出选择。
      evidence:: E5, E8
        - 训练时首先采样一条单调递增的轨迹 phi(t)，然后对「输出到输入」的注意力进行掩码，使得输出词元 t 只能看到直到 phi(t) 为止的输入词元。
          evidence:: E6
        - 批处理（batch）这一遍能看到完整输入，并提供教师的 logits；而流式这一遍只能看到部分前缀，需要同时学习下一词元预测，以及向批处理视角的软对齐。
          evidence:: E7
        - 注意力驱动的决策头在注意力集中于特定输入时触发写出，熵驱动的决策头在下一个词元的不确定性足够低时触发写出。
          evidence:: E8
    - **设计决策:** 主要的设计选择都指向同一个边界：主干网络学习许多可能的部分上下文状态，而最终的读写规则保持可替换。
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E8
        - 需求：在不引入无法训练的噪声的前提下，暴露部分上下文状态；选择：按预算的多项式分配，或均匀多项式分配读取；最接近的替代方案：朴素的随机掩码；权衡：更平滑的轨迹可能无法充分体现现实中突发式的输入流。
          evidence:: E6, E14
        - 需求：防止部分上下文下的预判发生漂移；选择：使用同一模型的全上下文教师；最接近的替代方案：外部教师或冻结教师；权衡：软化的 top-k KL 散度能保留预判能力，但无法提供独立的教师信号。
          evidence:: E7
        - 需求：在不重训整个模型的情况下调整时机；选择：在冻结的大语言模型（LLM）状态之上使用注意力头和熵头；最接近的替代方案：固定的 wait-k，或学习得到的对齐标签；权衡：阈值必须经过校准才能保证可靠性。
          evidence:: E8, E17
    - **实现边界:** 文本模型使用 Qwen2.5-3B-Instruct 和 Qwen3-4B，配合分组位置编码（Group Positional Encoding，GPE，即把输入和输出的位置流分开）以及解耦的注意力/键值缓存（KV cache）；语音模型使用 Qwen2-Audio-7B-Instruct，配合因果 Whisper 编码器。文中报告的设置包括 top-100 logit 蒸馏、两个训练轮次、学习率 5e-5、四块 H100 GPU，以及主决策阈值取 0.9 分位数。
      evidence:: E5, E18
- ## Evaluation and Evidence
    - **实验设置:** 评估覆盖 IWSLT-17 En-De/En-Fr、DialogSum、SQuAD 和 MCTest 上的文本流，以及 LibriSpeech 和 Spoken-SQuAD 上的语音流。评估报告任务质量，另外报告每个输出词元的读取覆盖率（read coverage per output token，RCO，即平均消耗的输入比例）和平均交互延迟（average interaction lag，AIL，即相对理想流式调度的延迟）。
      evidence:: E4, E9
    - **主张-证据矩阵:** 证据大体上支持论文关于相对权衡的论断，但由于缺少重复次数、方差和显著性检验，实验支持强度只能算中等。
      claim_kind:: analyst_assessment
      evidence:: E10, E11, E12, E13
        - C1 在机制上由 MSLM 和 SPSD 两个训练目标提供支持，并由消融实验间接支持，但论文没有单独测量语义充分性线索这一直接证据。
          claim_kind:: analyst_assessment
          evidence:: E6, E7, E13
        - C2 由文本结果表格支持，这些表格对比了 wait-k 基线和对齐监督基线，尤其是在短问答任务上，此时依赖内容的时机判断比固定延迟更重要。
          claim_kind:: analyst_assessment
          evidence:: E10, E11
        - C3 由语音实验结果和骨干网络覆盖情况支持；C4 由消融实验支持，不过 KL 系数分析削弱了「仅靠显式 KL 匹配就能带来性能提升」这一说法。
          claim_kind:: analyst_assessment
          evidence:: E12, E13
    - **关键结果:** 最主要的规律是：当任务中的决定性证据稀疏时，ProactiveLLM 带来的收益最为明显；而在单调翻译任务上，它在质量与延迟方面的改进较小，但仍然有用。
      evidence:: E10, E11, E12, E16
        - 在 Qwen3-4B 英译法（En-Fr）任务上，Proactive-Entropy 取得 32.24 BLEU，每输出词元读取覆盖率（RCO）为 0.88，而 Wait-9 为 24.33 BLEU、RCO 为 0.89；在短问答任务上，在高延迟条件下，ProactiveLLM 比最好的 GPT-5.4 对齐监督基线高出 8.15 F1。
          evidence:: E10, E11
        - 在 Spoken-SQuAD 上，Proactive-Entropy 达到 71.12 F1，平均交互延迟（AIL）为 21.26 秒，RCO 为 0.80，接近批处理方式的 72.15 F1，同时使用了更少的上下文并具有更低的延迟。
          evidence:: E12
        - 可变注意力的浮点运算量（FLOPs）在选择题问答（Choice QA）上下降最多（34.82%），在短问答（Short-form QA）上次之（21.67%），在摘要任务上中等程度下降（9.90%），在英译德机器翻译（MT En-De）上仅略有下降（2.27%），这与「收益取决于信息密度」这一说法相符。
          evidence:: E16
    - **消融与敏感性:** 消融实验表明，流式训练目标和批处理侧的锚点都很重要，而 lambda（即 KL 散度的系数）在所报告的取值范围内敏感度较低。
      evidence:: E13
        - 去掉同步特权自蒸馏（Synchronized Privileged Self-Distillation，SPSD）会在推理密集的短问答任务上导致所报告的最大性能崩塌，而去掉掩码流式语言建模（Masked Streaming Language Modeling，MSLM）会在低延迟约束下削弱质量。
          evidence:: E13
        - 相比朴素的随机掩码，多项式分配减少了高方差的掩码轨迹，使训练状态更接近合理的流式路径。
          evidence:: E14
        - 在 ProactiveLLM 上部署 wait-k，其表现与从头训练的 wait-k 相当，并且在激进的低延迟场景下更好，这支持了「即插即用」的定位。
          evidence:: E15
    - **可复现性缺口:** 论文报告了骨干网络、数据集、硬件、主要超参数以及决策阈值策略，但所提供的文本没有给出具体的代码仓库网址、随机种子、每个任务的数据划分细节、重复次数、方差，也没有给出对齐监督基线的完整脚本。
      claim_kind:: analyst_assessment
      evidence:: E9, E18
- ## Technical Judgment
    - **站得住的结论:** 最强的部分是把表示学习和决策策略分开：MSLM 与 SPSD 让模型在只能看到部分输入时依然有用，而注意力阈值或熵阈值可以直接替换，不必重建主干网络。证据与这一说法一致，因为当语义充分性（semantic sufficiency，即可见前缀已包含足够含义的时刻）稀疏且依赖于输入内容时，收益最大。
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E10, E16
    - **可能失效之处:** 当早期证据看似合理但并不足以下定论时，这种方法可能失效，Spoken-SQuAD 数据集中的 Levi's Stadium 例子就说明了这一点；采用更保守的阈值可以缓解这个问题，但会牺牲一部分延迟表现。对于那些确实需要读取几乎每一个输入标记（token）的任务，收益也会减小，这与机器翻译（MT）任务上浮点运算量（FLOP）减少幅度较小的结果一致。
      claim_kind:: analyst_assessment
      evidence:: E16, E17
    - **与已有工作的关系:** 与 wait-k 和分块解码相比，ProactiveLLM 让时机取决于模型状态，而不是固定的时钟节拍；与依赖对齐监督的策略相比，它避免了针对具体任务标注时机标签。与普通的蒸馏相比，教师模型和学生模型是同一个不断演进的模型，只是它们对上下文的访问程度不同，因此这种方法更接近于「有特权信息的自对齐」，而不是从外部教师模型迁移知识。
      claim_kind:: analyst_assessment
      evidence:: E2, E7, E15
    - **可迁移启发:** 对于流式系统，应当先训练模型在真实的部分观测条件下正常工作，再让时机控制器保持小巧、可替换、以阈值为准。这一模式把延迟变成了一个部署时可调的旋钮，而不是把某一种固定的时机策略写死进模型里。
      claim_kind:: analyst_assessment
      evidence:: E6, E8, E15
- ## Glossary
  collapsed:: true
    - 流式大语言模型（streaming large language model）：一种在输入流还在到达时就能生成输出的模型，而不必等待完整输入。
    - 语义充分性（semantic sufficiency）：指可见前缀（prefix）已经包含足够含义、足以让模型可靠地生成下一个输出的那个时刻。
    - 交互调度器（interaction scheduler）：一条规则或一个学习得到的策略，用来决定模型在生成每个输出标记（token）之前可以读取多少输入。
    - 掩码流式语言建模（Masked Streaming Language Modeling，MSLM）：一种训练目标，它把未来的输入标记（token）隐藏在单调递进的边界之后，使生成过程学会从部分前缀（prefix）中学习。
    - 同步特权自蒸馏（Synchronized Privileged Self-Distillation，SPSD）：一种同一模型充当教师和学生的设定，在训练时用能看到完整上下文的视角来引导只能看到部分上下文的流式视角。
    - 每输出标记读取覆盖率（read coverage per output token，RCO）：一种衡量冗余的指标，指在生成输出标记（token）时平均消耗了输入流的多大比例；数值越低说明读取的上下文越少。
    - 平均交互滞后（average interaction lag）：一种相对延迟指标，衡量写出决策相比理想的均匀流式对齐延迟了多少。
    - wait-k：一种固定的流式策略，先等待预设数量的输入再开始写出，之后按照固定的读/写节奏进行。
    - 熵驱动决策头（entropy-driven decision head）：一种控制器，当下一个词元的概率分布不确定时选择读取，当分布集中时选择写出。
    - 分组位置编码与键值缓存（Group Positional Encoding and KV cache）：GPE 将源端和目标端的位置流分开处理；键值缓存（KV cache）存储注意力的键和值，使新词元能够增量处理。
- ## Evidence Index
  collapsed:: true
    - **E1:** problem/paper_statement | Abstract and Introduction | high
      locator:: Abstract; Sec. 1 Introduction
      quote:: Standard Large Language Models follow a read-then-generate paradigm, causing unnecessary latency and computation. Streaming LLMs alleviate this issue by generating while receiving inputs, but still struggle to decide when to interact with the stream.
    - **E2:** gap/paper_statement | Introduction | high
      locator:: Sec. 1, prior-methods paragraph
      quote:: Existing methodologies remain largely confined within a passive adaptation framework. They either rely on heuristic interaction schedules, such as fixed wait intervals or chunkwise decoding, or learn generation timing from task-specific alignment supervision.
    - **E3:** method/paper_statement | Abstract and Introduction | high
      locator:: Abstract; Sec. 1 contribution paragraph
      quote:: The model first learns to perceive semantic sufficiency from partial inputs through two complementary training mechanisms: mask-based streaming modeling and synchronized privileged self-distillation. Together, these mechanisms induce endogenous sufficiency cues without requiring external teachers or annotations.
    - **E4:** background/paper_statement | Preliminary | high
      locator:: Sec. 2, definition and metrics
      quote:: Given an input stream X and an output stream Y, the model generates tokens sequentially while the input continues to unfold. phi(t) denotes the interaction scheduler, representing the boundary of the input stream accessible to the model at output step t.
    - **E5:** implementation/implementation_detail | Streaming LLM Backbone | high
      locator:: Sec. 3.1 and Appendix B.1
      quote:: Prior research has demonstrated that group positional encoding effectively adapts batch-processed LLMs to streaming scenarios without requiring architectural modifications. Regarding the streaming speech LLM, we utilize a Whisper encoder to project audio features into the textual latent space.
    - **E6:** algorithm/implementation_detail | Proactive Streaming Training Framework | high
      locator:: Sec. 3.2, Masked Streaming Language Modeling
      quote:: During training, we simulate this dynamic availability by applying a randomized causal mask to the future input context. Each unique mask matrix corresponds to a specific interaction decision trajectory phi, effectively transforming a static full-input sample into a simulation of a dynamic streaming process.
    - **E7:** algorithm/implementation_detail | Proactive Streaming Training Framework | high
      locator:: Sec. 3.2, Synchronized Privileged Self-Distillation
      quote:: The streaming mode serves as the partial-context student, while the batch mode serves as the full-context teacher with privileged access to the complete input. Since both views are produced by the current model parameters and optimized jointly during training, the teacher signal is continuously synchronized.
    - **E8:** system_design/implementation_detail | Streaming Active Interaction Decision | high
      locator:: Sec. 3.3
      quote:: The decision head monitors the model's intrinsic states, such as token entropy or attention weights, to guide the interaction decision. High H(P) reflects an information deficit where the predictive mass is dispersed across multiple hypotheses, necessitating a Read.
    - **E9:** experiment_setup/paper_statement | Experimental Settings | high
      locator:: Sec. 4.1
      quote:: For text streaming, we select tasks representing monotonically aligned processes, specifically translation evaluated on IWSLT-17 En-De and En-Fr, as well as non-monotonically aligned processes, including summarization on Dialogue Summarization, short-form QA on SQuAD, and multiple-choice QA on MCTest.
    - **E10:** result/experiment_result | Text-input Results | medium
      locator:: Sec. 4.2, Table 1 and following text
      quote:: In monotonically aligned tasks, fixed-interval methods like wait-k face a rigid trade-off. Breaking this constraint, ProactiveLLM achieves generation quality superior to wait-9 while maintaining lower latency and redundancy than the wait-9 baseline.
    - **E11:** result/experiment_result | Text-input Results | medium
      locator:: Sec. 4.2, Table 2
      quote:: On non-monotonic short-form QA, ProactiveLLM outperforms the best learning-based baseline by 10.62 and 8.15 F1 points at the low- and high-latency levels, respectively, showing more robust decision making without external alignment data.
    - **E12:** result/experiment_result | Speech-input Results | medium
      locator:: Sec. 4.3, Table 3
      quote:: Table 3 suggests that the effectiveness of ProactiveLLM extends to speech streaming tasks. In monotonic ASR, our method appears to alleviate the strict latency-accuracy trade-off found in fixed strategies, achieving performance comparable to high-k baselines but with reduced latency.
    - **E13:** ablation/ablation | Ablation Studies | medium
      locator:: Sec. 4.4, Fig. 4 and Fig. 5
      quote:: The results clearly demonstrate that ProactiveLLM achieves the optimal Pareto frontier across all tasks. As components are systematically removed, the trade-off curves consistently shift towards the bottom-right, indicating a degradation in both latency and quality.
    - **E14:** ablation/profiling | Analysis | medium
      locator:: Sec. 5, Random Mask Analysis and Fig. 6
      quote:: The naive random method exhibits extremely high variance with paths frequently deviating from the ideal diagonal. In contrast, the polynomial allocation maintains smoother, stable trajectories, indicating that the budget-based mechanism successfully mitigates such extreme decision-making.
    - **E15:** result/experiment_result | Analysis | medium
      locator:: Sec. 5, Generalization Analysis and Table 4
      quote:: Table 4 demonstrates that directly deploying Wait-k logic on ProactiveLLM achieves performance fully comparable to a specialized Wait-k model trained from scratch. Notably, ProactiveLLM significantly surpasses the baseline in aggressive low-latency regimes.
    - **E16:** optimization/profiling | Analysis | medium
      locator:: Sec. 5, Redundancy and Latency Analysis and Table 5
      quote:: ProactiveLLM consistently reduces computation across benchmarks, with gains correlating to task-specific information density. Non-monotonic alignment streaming tasks like Multi-choice QA (34.82%) and short-form QA (21.67%) yield the highest savings.
    - **E17:** limitation/case_study | Case Study | medium
      locator:: Appendix E, Table 10
      quote:: Streaming settings reduce interaction latency, but generating from partial information is inherently risky. This limitation arises from the streaming setting itself rather than from a specific model: when the current prefix contains a plausible but incomplete clue, the model may generate prematurely.
    - **E18:** implementation/implementation_detail | Implementation and Hyperparameter Settings | high
      locator:: Appendix B.3, Table 6
      quote:: We summarize the main model, training, and inference hyperparameters in Table 6. These settings are shared across the reported ProactiveLLM experiments unless otherwise specified. Training epochs are 2, hardware is 4 x H100 GPUs, and the decision threshold is swept in [0, 1].
