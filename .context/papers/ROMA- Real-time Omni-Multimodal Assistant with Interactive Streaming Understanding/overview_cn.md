- **标题:** ROMA：具备交互式流式理解能力的实时全模态助手
- **一句话总结:** ROMA 表明，一个流式音视频助手可以把「何时开口说话」与「生成什么内容」分开处理，同时让音频和视频在时间轴上保持对齐，从而将主动式的响应时机判断与被动式的问答能力结合起来。
- **论文类型:** 系统类论文
- **发表:** arXiv 预印本 2026
- **作者:** 田雪芸（中国科学院大学），李威、徐冰冰（中国科学院计算技术研究所），董恒（清华大学），王元卓（中国科学院计算技术研究所），沈华伟（中国科学院大学）
- **关键词:** 流式多模态理解、全模态助手、主动交互、音视频对齐、响应时机、流式评测
- ## Orientation
    - **背景:** 本文属于实时助手模型这一领域，这类模型会随着事件的推进处理语音、图像和文本。关键前提是流式处理（streaming）：模型只能使用已经发生的信息，而不能使用整段录制内容。
      claim_kind:: analyst_assessment
    - **通俗问题:** 一个有用的助手不应只是在被问到之后才作答；它还应当持续观察和聆听，然后在被要求关注的事情真正发生时开口说话。
      claim_kind:: analyst_assessment
    - **为何困难:** 难点在于：声音是连续到达的，图像却是一张张独立的快照，而助手必须在看不到未来的情况下决定何时插话。
      claim_kind:: analyst_assessment
    - **一句话核心思路:** 一句话概括核心思路：把声音和图像放在同一条时间轴上，再用一个小型的门控机制来决定主说话者何时开口。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **阅读价值:** 把这篇论文当作一篇关于流式多模态系统的研究来读，它探讨的核心差距在于：一类模型只在被提问后才作答，而另一类助手必须一边观看、一边聆听、一边等待，并在恰当的时刻开口说话。
      claim_kind:: analyst_assessment
      evidence:: E2, E3
    - **一句话贡献:** ROMA 改进了实时音视频辅助能力，做法是在生成文本之前，把响应时机作为一个显式的在线决策来处理，而不是强迫语言模型把「沉默」或「说话」当作普通词语来表达。
      evidence:: E1, E6
    - **记忆模型:** 可以把它想象成一位带有静音按钮的现场解说员：一部分负责持续观看和聆听，另一部分负责判断当前时刻是否值得开口，只有在判断值得之后，解说者才真正说出那句话。
      claim_kind:: analyst_assessment
    - **最佳证据:** 最有力的证据并非某一项基准测试的分数，而是一种整体规律：ROMA 提升了主动预警和实况解说的时机把握，同时在被动式问答上保持了有竞争力的表现。
      evidence:: E10, E11, E12
        - 支持结论 C3：在 QVHighlights 和 Charades-STA 上完成静态定位，并在 PA/PO/REC 上完成动态告警；基线方法支持流式处理；采用定位类和成功率类评测指标；在 QVHighlights 的 mAP 以及 PO/REC 上取得大幅提升，在 CRR 上表现有好有坏；结论得到支持，但未报告方差。
          evidence:: E10
        - 支持结论 C3：在 YouCook2 和 OVO-Bench SSR 上完成解说生成；基线方法为 VideoLLM-online 和 MMDuet；采用 F1、BERTScore 和 GPT-4o 评判；取得最佳的 F1 和 GPT 分数，BERTScore 相近；结论得到支持，但未报告统计不确定性。
          evidence:: E11
        - 支持结论 C4：消融实验替换了发声头（speak head）或降低了层聚合程度；对比了基于 token 的触发方式和 K=1 的变体；动态告警和解说生成的指标大幅下降；作为一项组件消融实验，结论得到支持，但未报告重复实验次数。
          evidence:: E13
    - **主要边界:** 本文的证据在经过精心整理的流式任务和有限时长的片段上最为可靠；文中明确将信号退化、音视频不同步、超长依赖关系，以及严格的效率与质量权衡，列为尚未解决的风险。
      claim_kind:: analyst_assessment
      evidence:: E15
- ## Argument Map
    - **问题与重要性:** 本文把流式音视频理解建模为一个统一的交互问题，包含两种设置：一是反应式问答（question answering，QA），即模型在收到查询之后作答；二是主动式监控，即模型必须仅凭流的前缀（prefix）就触发告警或解说。这一点很重要，因为真正的助手必须把感知、时机把握和语言表达结合起来，而不是去解决一个个孤立的离线视频任务。
      evidence:: E2, E9
    - **已有方法缺口:** 本文指出，以往的系统在错误的维度上进行了划分：以语音为主的流式模型往往缺乏视觉感知能力，视频流式模型往往忽略同步的音频，而许多评测方案考察的是查询注入（question injection），而不是模型自主决定响应时机的能力。
      evidence:: E3, E17
    - **关键洞见:** 核心洞见是把实时交互中隐藏的两项工作分开处理：一是在多模态证据到达时保持它们在因果顺序上对齐；二是在生成文本之前，通过一个专门的时机信号来做出「开口还是等待」的决定。
      evidence:: E4, E5, E6
    - **核心主张:** 本文的论点可归结为关于统一流式交互、训练、评估以及时机模块的四个可证伪的主张。
      claim_kind:: analyst_assessment
        - C1：ROMA 能够把实时音频与视频表示为按因果顺序排列且对齐的单元，从而让一个模型同时支持主动告警、实时叙述和被动问答。
          evidence:: E1, E4, E9
        - C2：一个精心整理的流式数据集加上两阶段微调，能够把一个强大的离线全模态基础模型转化为一个带有校准过的响应时机的在线模型。
          evidence:: E7, E13
        - C3：在本文提出的统一评估套件下，ROMA 在主动告警和叙述任务上取得了最先进的结果，同时在被动问答和全模态问答上保持竞争力。
          evidence:: E10, E11, E12
        - C4：把响应时机解耦到一个独立的「开口头」（speak head）中——尤其是利用来自多个上层的信息——对主动触发很重要，而不仅仅是一个实现细节。
          evidence:: E6, E13
- ## Mechanism and Design
    - **核心机制:** ROMA 把数据流切分为固定时长的音视频片段，将稠密的音频 token 和稀疏的视频帧 token 打包在一起，并通过时间对齐多模态 RoPE（Time-aligned Multimodal RoPE，TMRoPE，一种位置编码方案，用于告诉 transformer 哪些音频和视觉 token 共享同一时间）为它们赋予对齐的时间位置。随后，一个独立的「开口头」（speak head）对每个流前缀（prefix）打分，判断是否应当开始响应，而普通的语言建模头只在该触发之后才生成内容。
      evidence:: E4, E5, E6
    - **数据/控制流:** 在推理时，每个新单元都会被编码、追加到持续增长的时间序列上，并由「开口头」评估；如果概率超过任务阈值，语言模型就输出一个响应，否则 ROMA 保持沉默并读取下一个单元。系统维护一个键值缓存（KV cache，即从先前 token 存下来的注意力状态），使每一步都能复用先前的上下文，而不必重新编码整条流。
      evidence:: E6, E8
        - 打包步骤：来自同一时间区间的音频和视频被封装进基础模型 Qwen2.5-Omni 的 token 格式中，在保持与基础模型兼容的同时施加一个流式顺序。
          evidence:: E4
        - 时间线步骤：同一单元内的视频 token 共享该单元的时间位置，音频 token 保留更细粒度的时间位置，而后续单元则从前一个最大位置 ID 继续往下排。
          evidence:: E5
        - 触发步骤：speak head 读取最后 K 个隐藏层的一个可学习加权组合（在报告的实验里 K 取四），并把它转换成一个二值的「是否发声」概率。
          evidence:: E6
    - **设计决策:** 主要的设计选择都在减少相互干扰：先对齐各模态再进行推理，把发声时机的打分放在生成之外来做，并且在专门训练时机判断之前先训练流式格式的适配。相应的代价是需要更多针对具体任务的监督信号和阈值校准，而不是仅靠提示词就直接使用基础模型。
      evidence:: E5, E6, E7, E14
        - 需求：音频信息密集而视频信息稀疏；选择：采用同步的分块加上分块的 TMRoPE（Time-aligned Multimodal RoPE，一种带时间感知的旋转位置编码）；论文里最接近的替代方案是对各模态或整段视频采用较弱的因果处理；代价：在每个单元内部视频的时间定位更粗糙，而音频仍保留精细的位置。
          evidence:: E4, E5
        - 需求：模型必须决定何时发声，同时不能把「时机」和「内容」混淆；选择：一个与语言头并行的两层神经网络时机分类器；最接近的替代方案是使用一个静默标记；代价：显式的概率需要设定阈值，并对正样本标签做平衡。
          evidence:: E6, E13, E14
        - 需求：基础模型是针对完整输入优化的；选择：先适配流式模板，再在混入问答（QA）数据的同时学习具有时间感知的决策；最接近的替代方案是单阶段的混合训练；代价：流水线更复杂，但主动发声的校准效果更好。
          evidence:: E7, E13
    - **实现边界:** ROMA 是在 Qwen2.5-Omni 基础上改造实现的：冻结编码器，对其余参数做微调，采用两阶段训练，并使用流式解码——以每秒 2 帧（2 fps）对视频采样，把单帧尺寸上限设为 65,536 像素，并使用一个持久的键值缓存（KV cache）。附录细节表明训练使用 LLaMA-Factory，序列长度为 32K，用 32 张 H20 GPU，全局批处理大小为 512，并且为流水线化的实时近似设定了每段生成 25 个标记的预算。
      evidence:: E8, E16
- ## Evaluation and Evidence
    - **实验设置:** 评测把此前碎片化的流式基准重新组织为主动交互和被动交互两类：主动交互涵盖事件驱动的告警和实时叙述，被动交互涵盖依赖因果历史的问答（QA）。对比基线在主动任务上仅限于具备流式能力的视频模型，在带语音查询的全模态问答上则纳入了开源的全模态模型。
      evidence:: E9, E12
    - **主张-证据矩阵:** 当同一机制同时通过基准对比和消融实验得到验证时，证据最有力；而当结果仅依赖单次实验、评判用的提示词或对基准的重新表述时，证据较弱。
      claim_kind:: analyst_assessment
      evidence:: E10, E11, E13
        - C1 得到了框架覆盖面和实现路径的支持：论文在同一套流式协议下测试了告警、叙述和问答，但最有力的证据只是功能层面的，而非形式化的系统不变性证明。
          claim_kind:: analyst_assessment
          evidence:: E8, E9
        - C3 得到了在 QVHighlights、动态告警和叙述上主要的主动交互性能提升以及有竞争力的问答表现的支持；支持力度为中等，因为论文没有报告方差、随机种子或置信区间。
          claim_kind:: analyst_assessment
          evidence:: E10, E11, E12
        - C4 最直接的支持来自「说话头」（speak head，即判断是否该开口的分类器）实验和 K=1 的消融实验：主动式的时机把握下降得比「基于时间戳的理解」更明显，这与论文所声称的时机模块的作用相吻合。
          claim_kind:: analyst_assessment
          evidence:: E13
    - **关键结果:** 主要结果呈现出主动式能力的强项：ROMA 在 QVHighlights 上报告了 53.7 的平均精度均值（mean average precision，mAP），在 Charades-STA 上在 0.5/0.7 的重叠阈值下取得 44.3/19.9 的召回率，在 PA 和 PO 上取得所报告的最佳动态告警分数，并在 REC 上取得最佳的重复告警分数。在叙述方面，它在 YouCook2 上报告了 35.21 的 F1，在 OVO-Bench SSR 上报告了 14.54 的 F1，其 GPT-4o 评审平均分最高，但 BERTScore 与基线接近。
      evidence:: E10, E11
        - 所支持的论断：更好的时间定位能力；配置：QVHighlights 和 Charades-STA；最接近的基线：同一批表格中的 MMDuet；指标方向：越高越好；差距：QVHighlights 的 mAP 为 53.7 对比 31.3，Charades 的 R@0.5 为 44.3 对比 42.4。
          evidence:: E10
        - 所支持的论断：更好的在线叙述时机把握；配置：YouCook2 和 OVO-Bench SSR；最接近的基线：视指标而定为 MMDuet 或 VideoLLM-online；指标方向：越高越好；差距：YouCook2 的 F1 为 35.21，而 VideoLLM-online 为 18.82，MMDuet 为 17.81。
          evidence:: E11
        - 所支持的论断：被动式能力基本得以保留；配置：OVO-Bench、StreamingBench、Video-MME 和 EgoSchema；基线包括 Dispider 和全模态模型；需注意的地方：某些子类别仍与基线接近或低于基线。
          evidence:: E12
    - **消融与敏感性:** 消融实验支持了课程式训练与时机设计：单阶段混合训练会削弱在线触发能力，去掉「说话头」对主动式告警和叙述的损害最大，而只使用最后一层会削弱时间定位与动态触发能力。正类权重 w_pos（即二元时机损失中对稀有「说话」标签的乘子）对主动式任务很重要，但对被动式问答影响甚微。
      evidence:: E13, E14
    - **可复现性缺口:** 论文报告了训练硬件、序列长度、批处理大小、数据来源、评测提示词以及若干解码阈值，这有助于核查实验设置。所提供文本中未报告的内容包括：模型权重的可获取性、精确的重新标注时间戳数据、训练随机种子、重复次数、方差，以及针对每一项基准重述任务的完整脚本级复现路径。
      claim_kind:: analyst_assessment
      evidence:: E14, E16, E17
- ## Technical Judgment
    - **站得住的结论:** 最可信的部分是时机与生成之间的架构分离：它直接契合了问题的结构，并有实验支撑——当把它替换为词元级别的沉默行为时，主动式任务出现了大幅下降。对齐分块表示同样合理，因为它针对的是音频与视频粒度不匹配这一具体问题，而不是仅仅依赖提示词。
      claim_kind:: analyst_assessment
      evidence:: E4, E6, E13
    - **可能失效之处:** 当音频与视频严重不同步、当重要证据落在有限的上下文窗口之外，或当助手需要在严格的实时预算下给出高质量的长回复时，其收益可能会减弱。每段 25 个词元的解码上限以及有限上下文的训练设置，使这一边界变得具体而非假想。
      claim_kind:: analyst_assessment
      evidence:: E15, E16
    - **与已有工作的关系:** 与基于记忆或键值缓存（KV cache）的流式视频问答系统相比，ROMA 更少关注如何压缩长历史，而更多关注如何判断当前前缀是否值得触发行动。与仅处理视频的主动式助手相比，其技术区别在于同步的音视频输入；与全模态被动式模型相比，其区别在于显式的主动式响应时机把握。
      evidence:: E3, E17
    - **可迁移启发:** 对于实时的多模态系统，当产品的关键行为是「何时该开口」这样的时机决策时，不要把控制策略藏在生成的词元里。应当直接表示控制信号，在真正用到它的生命周期节点上对其进行监督，同时让内容生成器仍然按照普通语言质量来训练。
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E13
- ## Glossary
  collapsed:: true
    - 流式理解（Streaming understanding）：在按时间顺序到达的输入随到随处理，只使用过去和当前的上下文，而不使用完整的、包含未来内容的整段录制。
    - 主动式与被动式交互（Proactive vs reactive interaction）：被动式指的是在收到查询之后再作答；主动式指的是持续监测，只有当所要求的条件被满足时才作出响应。
    - 全模态大语言模型（Omni-multimodal large language model）：一种能够接收或生成多种模态（如文本、音频、语音和视觉）的大语言模型。
    - 多模态单元（Multimodal unit）：ROMA 在每一步输入的打包数据，即来自同一时间区间的音频词元和视频词元，作为一个因果单元一起处理。
    - 时间对齐多模态旋转位置编码（Time-aligned Multimodal RoPE，TMRoPE）：旋转位置编码的一种变体，为音频词元和视频词元赋予具备时间感知的位置，使得 transformer 能够在同一条时间线上对齐不同模态。
    - 开口头（Speak head）：与语言头并列的一个小型分类器，用来预测模型在当前流步是否应当开始作出响应。
    - 键值缓存（Key-value cache，KV cache）：存储下来的、来自之前词元的注意力状态，可被复用，从而让 transformer 能够从先前的上下文继续，而不必重新计算整个前缀。
    - 问答（Question answering，QA）：一种被动式设定，模型根据可用的流历史来回答用户的问题。
    - 流式评测指标（Streaming evaluation metrics）：用于对事件时间进行排序、评估最佳时间戳准确率、时间重叠召回率、触发窗口对齐以及语义相似度的一组指标。
    - 动态提醒任务名称：论文在主动提醒和流式叙述设置中所使用的基准子任务缩写；在对比表格时保留原始缩写。
    - 加权二元交叉熵：一种二分类损失函数，其中稀有的正类「发声」标签会被赋予更大的权重，以避免模型学会过于频繁地保持沉默。
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/paper_statement | Abstract | high
      locator:: Abstract, lines 20-23
      quote:: We present ROMA, a real-time omni-multimodal assistant for unified reactive and proactive interaction. ROMA processes continuous inputs as synchronized multimodal units, aligning dense audio with discrete video frames to handle granularity mismatches.
    - **E2:** problem/paper_statement | Introduction | high
      locator:: Section 1, reactive and proactive definition
      quote:: In the reactive setting, the model answers after the query, whereas in the proactive setting, it follows an instruction to continuously monitor the input stream and respond only when conditions are met.
    - **E3:** gap/paper_statement | Introduction | high
      locator:: Section 1, prior gap paragraph
      quote:: Speech-centric streaming models focus on audio generation but lack visual perception. Conversely, while some approaches address streaming video understanding, they typically neglect synchronized audio and are confined to specific tasks.
    - **E4:** method/implementation_detail | Method | high
      locator:: Section 3.1, Multimodal units
      quote:: We treat all audio and video signals within each one-second interval as a unit. We align audio with video frames sampled from the same interval, extract their features, and wrap them with special tokens.
    - **E5:** algorithm/implementation_detail | Method | high
      locator:: Section 3.1, Chunk-Level Temporal Position Encoding
      quote:: Each one-second unit interleaves visual and auditory tokens, assigning time-aligned 3D position IDs to preserve their cross-modal correspondence. Audio tokens retain fine-grained temporal IDs at a 40ms resolution.
    - **E6:** system_design/implementation_detail | Method | high
      locator:: Section 3.1, Speak Head
      quote:: This module is implemented as a two-layer MLP, parallel to the LM head, on top of the streaming backbone. Upon processing each multimodal unit, the speak head evaluates the current stream prefix and outputs a probability.
    - **E7:** method/implementation_detail | Method | high
      locator:: Section 3.2.1 and 3.2.2, dataset and training recipe
      quote:: We construct a comprehensive streaming dataset structured into two categories and three sub-tasks. Stage 1 adapts the model to the streaming multimodal input format, while Stage 2 learns precise response timing and proactive policies.
    - **E8:** implementation/implementation_detail | Method | high
      locator:: Section 3.2.3, Inference Procedure
      quote:: Video frames are uniformly sampled at 2 fps, and each frame is resized so that the number of pixels does not exceed 65,536. We maintain a persistent KV cache across the stream.
    - **E9:** experiment_setup/paper_statement | Unified Streaming Evaluation Framework | high
      locator:: Section 4, framework overview
      quote:: We establish a unified framework comprising two primary settings: proactive interaction, where the model autonomously monitors the stream to trigger responses, and reactive interaction, where it answers queries based on accumulated context.
    - **E10:** result/experiment_result | Experiment | medium
      locator:: Section 5.2, Tables 2 and 3, Event-Driven Alert
      quote:: ROMA advances temporal localization on QVHighlights (53.7 mAP) and Charades-STA (44.3/19.9 R@0.5/0.7). In the dynamic setting, ROMA demonstrates strong efficacy on single-alert tasks.
    - **E11:** result/experiment_result | Experiment | medium
      locator:: Section 5.2, Table 4, Real-Time Narration
      quote:: ROMA achieves the best temporal triggering accuracy, obtaining an F1 score of 35.21 on YouCook2 and 14.54 on OVO-Bench (SSR). It also achieves the highest GPT-4o score on both benchmarks.
    - **E12:** result/experiment_result | Experiment | medium
      locator:: Section 5.2, Tables 5-7, Reactive QA
      quote:: ROMA leads in both Real-time Visual Perception and Backward Tracing. On Streaming-Bench, ROMA maintains high accuracy and secures the top rank on Omni-Source Understanding benchmark.
    - **E13:** ablation/ablation | Experiment | medium
      locator:: Section 5.3, Ablation Study
      quote:: This variant consistently degrades on tasks that require online timing and triggering. We replace the speak head with a silence token. Last-layer aggregation notably degrades temporal grounding and dynamic triggering.
    - **E14:** ablation/ablation | Experiment | medium
      locator:: Section 5.4 and Appendix A.2, Sensitivity analysis
      quote:: We observe that w_pos is critical for proactive tasks, while reactive understanding and full-modality QA remain insensitive. Sensitivity analysis confirms robust performance and a broad operating regime with smooth degradation.
    - **E15:** limitation/limitation | Limitations | high
      locator:: Limitations section
      quote:: The model remains susceptible to distortions such as signal degradation and audio-video asynchrony. Capturing extremely long-term dependencies spanning hours remains constrained by finite context windows and memory.
    - **E16:** implementation/implementation_detail | Appendix | high
      locator:: Appendix A.5, Implementation Details
      quote:: The model is trained using LLaMA-Factory with a sequence length of 32K on 32 H20 GPUs using a global batch size of 512. Proactive samples are specifically formatted as multi-turn dialogues.
    - **E17:** prior_work/paper_statement | Appendix | medium
      locator:: Appendix A.1 and Table 10, Related Works
      quote:: Many works described as streaming in fact adopt a question-injection protocol. Overall, Table 10 shows that our method is the first open-source model to enable full omni-modal streaming while natively supporting proactive response, real-time narration, and reactive QA.
