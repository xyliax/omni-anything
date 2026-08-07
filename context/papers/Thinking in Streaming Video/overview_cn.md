- **标题:** 以流式视频的方式思考
- **一句话总结:** ThinkStream 把视频推理转化为一个「边看边想边说」的增量循环，用简短的推理轨迹作为紧凑的长期记忆，使流式视频助手能够在更低延迟、更有限的视觉上下文下作答。
- **论文类型:** 系统
- **发表:** arXiv 预印本 2026
- **作者:** Zikang Liu、Longteng Guo、Handong Li、Xingjian He、Ruyi Ji、Jing Liu（中国科学院自动化研究所；中国科学院大学）；Ru Zhen、Xiaoming Ren、Yanhao Zhang、Haonan Lu（OPPO AI Center，OPPO Inc.）
- **关键词:** 流式视频理解、增量推理、多模态大语言模型、键值缓存（KV cache）、带可验证奖励的强化学习、CUDA Graph 推理
- ## Orientation
    - **背景:** 本文属于视频语言人工智能领域，该领域要求模型把它在视频中看到的内容与用户的问题联系起来。在实时使用场景中，视频是一段一段陆续到来的，而不是一开始就有一段完整的片段。
      claim_kind:: analyst_assessment
    - **通俗问题:** 一个有用的助手应当能够观察不断变化的画面，记住已经发生的事情，并且只在所需的证据出现之后才作答。
      claim_kind:: analyst_assessment
    - **为何困难:** 早先出现的画面片段日后可能变得重要，但如果保留每一个视觉细节，随着视频流持续进行，模型会变得越来越慢、越来越沉重。
      claim_kind:: analyst_assessment
    - **一句话核心思路:** 边看边思考：保留最新的视觉细节，把较早的画面片段转化为简短的推理笔记，并在每一步判断是该开口回答还是继续等待。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **阅读价值:** 把这篇论文当作一篇关于连续视频输入的多模态系统论文来读。这里的难点不只是识别画面，而是要判断何时已经收集到足够的证据来作答，同时让内存占用和延迟都保持在有限范围内。
      claim_kind:: analyst_assessment
      evidence:: E2, E3
    - **一句话贡献:** ThinkStream 通过让模型在每次「说还是等」的决策之前更新一段简短的实时理解，从而改进流式视频问答，让紧凑的推理记忆能够替换掉旧的视觉细节。
      evidence:: E5, E6
    - **记忆模型:** 想象一位专注的观察者在看一个直播场景：每看完一个新片段就记下一小段笔记，把最新的画面留在桌上，然后靠这些笔记来回忆更早的时刻，而不用把整段视频重新播一遍。
      claim_kind:: analyst_assessment
    - **最佳证据:** 最有力的证据来自三方面的结合：在流式基准测试上的性能提升、针对记忆表示方式的消融实验，以及在实时性阈值下的延迟剖析。
      evidence:: E8, E14, E16
        - 支持论点 C1：ThinkStream-3B 在 OVO-Bench 上的表现；最接近的在线基线是 Streamo-3B；对比指标为平均分；59.66 对 51.64；结论成立，但文中未报告方差或重复实验次数。
          evidence:: E8
        - 支持论点 C3：在记忆模块的消融实验中，采用经 RLVR 优化的思维链记忆（RLVR-optimized chain-of-thought memory）；最接近的对照是冷启动思维链记忆变体；对比指标为平均分；67.0 对 63.3；结论成立，但未报告不确定性。
          evidence:: E14
        - 支持论点 C4：面对不断增长的视频上下文，采用基于 CUDA Graph 的流式后端；对照基线为即时执行（eager）模式的 Qwen2.5-VL-3B；对比指标为单 token 生成延迟；ThinkStream 始终保持在 0.5 秒以下，而基线始终高于 1.0 秒；结论仅在所测试的配置下成立。
          evidence:: E16
    - **主要边界:** 论文报告了单一系统的强劲结果，但可信度相关的信息较为单薄：文中没有提供误差棒、重复实验次数、已发布产物的验证，也没有独立的真实部署评测。
      claim_kind:: analyst_assessment
      evidence:: E8, E11, E18
- ## Argument Map
    - **问题与重要性:** 本文针对流式视频理解（streaming video understanding），即模型在进行视频推理时只能看到实时视频流的当前前缀（prefix），因此必须保持因果性、低延迟，并且占用的内存有上限。这项工作关乎交互式助手、监控系统以及具身智能体，它们都无法等到整段视频结束后才采取行动。
      evidence:: E2
    - **已有方法缺口:** 本文指出，批处理式视频推理要等到整段片段到齐后才开始推理，而许多在线系统虽然会管理视觉记忆或控制输出时机，却没有让推理本身成为记忆与决策的过程。因此，本文声称的空白点正处于时间因果性、语义记忆与「何时开口」这三者的交叉边界上。
      evidence:: E3, E4
    - **关键洞见:** 关键洞见在于：简短的思维链（chain-of-thought）token（也就是记录模型中间理解过程的生成文本）既可以作为对早先视频内容的语义压缩，又可以作为决定何时开口说话的控制信号。这样一来，推理就从一种离线书写答案的技巧，转变为流式的状态。
      evidence:: E5, E6
    - **核心主张:** 本文的论证可以拆解为四条可证伪的主张，分别涉及准确率、内存、训练和运行时行为。
      claim_kind:: analyst_assessment
        - C1：相比基础模型 Qwen2.5-VL-3B 以及开源的在线视频模型，Watch-Think-Speak 范式和 ThinkStream 在流式视频基准测试上提升了准确率。
          evidence:: E8, E9
        - C2：推理压缩流式内存（Reasoning-Compressed Streaming Memory，RCSM）保留近期的视觉 token，同时保留较早的推理 token。它在维持长时程理解能力的同时，防止稠密视觉缓存无上限地增长。
          evidence:: E6, E10, E13
        - C3：带可验证奖励的流式强化学习（Streaming Reinforcement Learning with Verifiable Rewards，RLVR）会对答案正确性、输出格式和回应时机进行奖励。它让推理 token 成为比朴素的字幕 token 或单纯的冷启动推理更好的长期记忆。
          evidence:: E7, E14
        - C4：自定义的 CUDA Graph 后端通过重放固定的解码（decode）和驱逐（eviction）内核，为实时流式推理提供了足够的吞吐和延迟控制，并支持对键值缓存（KV cache）进行显式操作。
          evidence:: E15, E16, E18
- ## Mechanism and Design
    - **核心机制:** ThinkStream 把一个多模态大语言模型（即能够读取视觉 token 和文本 token 的语言模型）包装进一个 Watch-Think-Speak 循环中：每个视频片段（chunk）都会触发一次简短的 <think> 更新，随后输出 <silent>（保持沉默）或 <response>（回应）。RCSM 把这些推理 token 用作紧凑的记忆，同时把较早的稠密视频 token 从键值缓存（KV cache）中驱逐出去——键值缓存指的是存储下来的注意力状态，用于避免重新计算过去的 token。
      evidence:: E5, E6
        - Watch（观看）：模型接收下一个时间片段（chunk）的视频以及用户指令，同时严格遵守因果性，因此未来的片段不会影响当前这一步。
          evidence:: E2, E5
        - Think（思考）：模型输出一段简短的推理内容，利用当前片段和已累积的记忆，来概括事件、更新假设或细化时间关系。
          evidence:: E5
        - Speak（说话）：当证据充分时，模型输出 <response> 并附上内容；当它应当继续观看时，则输出 <silent>。
          evidence:: E5
    - **数据/控制流:** 运行时状态把「视觉滑动窗口」（visual sliding window，指最近一段固定长度的视频 token）与全部累积的推理 token 和动作 token 组合在一起。当新的视频片段到来时，系统会驱逐过时的视觉 token，预取新片段，再通过解码生成下一段思考内容和动作。
      evidence:: E6, E18
        - RCSM 存储最近的视觉键值项，以及为已生成的推理 token 和动作 token 保存的键值项；论文用窗口 W 来定义视觉部分的保留大小。
          evidence:: E6
        - 在 RLVR 的采样过程（rollout）中，策略会在流式到达的视频片段上逐步采样出完整轨迹，随后根据格式、时机和准确性获得基于规则的奖励。
          evidence:: E7
        - 在推理阶段，预填充指把新到达的视觉 token 处理进缓存，而解码指基于该缓存自回归地生成输出 token；剪枝与解码一同被记录到可重放的 CUDA Graph 中。
          evidence:: E18
    - **设计决策:** 该设计用精确的视觉历史换取压缩后的语义连续性，再借助可验证奖励和自定义缓存控制，让这种取舍在实际中可行。论文提到的最接近替代方案包括：保留视觉记忆、使用字幕 token、使用外部触发头，或使用不带自定义缓存驱逐的标准推理引擎。
      claim_kind:: analyst_assessment
      evidence:: E4, E6, E7, E18
        - 需求：长视频流无法保留每一个视觉 token；设计选择：保留最近的视觉细节和旧的推理 token；替代方案：纯视觉记忆或字幕记忆；权衡：语义摘要可能会遗漏后续需要用到的低层细节。
          evidence:: E4, E6, E14
        - 需求：推理轨迹必须有用，且响应必须及时；设计选择：围绕准确性、格式和响应时间设计可用规则验证的奖励；权衡：RLVR 所用的这部分数据采用确定性的答案格式，而非完全开放式的验证。
          evidence:: E7, E17
        - 需求：显式的键值缓存驱逐，且启动开销要低；设计选择：对数量可变的视觉 token 采用即时预填充，并用 CUDA Graph 重放来完成解码和驱逐；替代方案：原生 transformers，或自定义缓存更新能力有限的优化引擎。
          evidence:: E18
    - **实现边界:** 论文报告的实现以 Qwen2.5-VL-3B 为起点，在 8 块 NVIDIA H2O GPU 上采用冷启动和 GRPO 风格的强化学习进行训练，以 2 FPS 对视频采样，并在训练和推理两个环节都使用专门的核函数。数据集流水线会对视频分段，用 Qwen3-VL-235B-A22B-Instruct 为各段生成字幕，合成指令，并生成带时间定位的思维链轨迹。
      evidence:: E11, E17, E18
        - 组相对策略优化（Group Relative Policy Optimization，GRPO）是一种强化学习方法，它对同一样本比较多个采样输出；在论文的公式设定中，其组大小为 8，并使用 KL 正则化。
          evidence:: E7, E11
        - 解码和逐出阶段使用 CUDA Graph（CUDA Graph，一种回放固定 GPU 执行图以避免每一步启动开销的技术），FlashInfer 用于加速采样，FlashAttention 风格的键值缓存（KV cache）注意力则负责内存访问。
          evidence:: E18
        - ThinkStream 数据集包含 110K 条冷启动样本和 9K 条 RLVR 样本，这些样本由带时间标注的字幕、多样的交互模式，以及便于确定性奖励计算的问题格式构建而成。
          evidence:: E17
- ## Evaluation and Evidence
    - **实验设置:** 主系统 ThinkStream-3B 由 Qwen2.5-VL-3B 初始化而来，在流式基准 OVO-Bench 和 StreamingBench Real-Time，以及离线视频基准 VideoMME 和 Long VideoBench 上进行评测。训练先使用冷启动监督数据，再进行 RLVR（可验证奖励的强化学习，Reinforcement Learning with Verifiable Rewards），视频以 2 FPS 采样，在单个 8-H2O-GPU 节点上完成。
      evidence:: E8, E9, E10, E11
    - **主张-证据矩阵:** 当一个结论同时具备基准指标提升和消融实验支撑时，证据最为有力；而当它依赖于未来发布或未报告的统计细节时，证据最弱。
      claim_kind:: analyst_assessment
      evidence:: E8, E14, E16, E18
        - C1：流式准确率有 OVO-Bench 和 StreamingBench 的平均分数支撑，并与基础模型和在线基线做了对比，但论文没有报告方差、重复运行或显著性检验。
          evidence:: E8, E9
        - C2：内存的有效性有离线基准性能保持和视觉窗口消融实验支撑，其中最有力的直接结果出现在 20 秒的视觉键值缓存（KV cache）窗口下。
          evidence:: E10, E13
        - C3：经 RLVR 优化的推理内存有内存消融实验支撑，其中字幕内存表现较差，而经 RLVR 优化的思维链（CoT）内存表现最佳。
          evidence:: E14
        - C4：运行时的可行性有解码吞吐和延迟分析的支撑，不过这些证据仅限于论文所用的硬件和后端实现。
          evidence:: E15, E16, E18
    - **关键结果:** 主要结果表明，这个小模型在在线视频场景中获得了最大的提升，同时保持了离线视频能力。数值上差距最大的对比未必是最贴切的对比，因此有意义的基线是基础模型 Qwen2.5-VL-3B 以及最强的开源在线系统。
      evidence:: E8, E9, E10
        - C1：在 OVO-Bench 上，ThinkStream-3B 的平均分数比 Qwen2.5-VL-3B 高 8.66 分，比 Streamo-3B 高 8.02 分；论文没有报告不确定性，因此这一支撑是趋势性的，而非统计意义上的。
          evidence:: E8
        - C1：在 StreamingBench Real-Time 上，ThinkStream-3B 得分 75.00，在论文所报告的表格中领先于 Dispider-7B 的 67.63 和 GPT-4o 的 73.28；重复实验次数未作报告。
          evidence:: E9
        - C2：在离线视频基准上，ThinkStream-3B 平均得分 59.4，而 Qwen2.5-VL-3B 为 54.4，这表明在论文所报告的设置中，剔除视觉词元并不会抹掉模型标准的视频处理能力。
          evidence:: E10
    - **消融与敏感性:** 这些消融实验让该机制更加可信，因为它们改变了推理预算、视觉缓存窗口和记忆表示，而不仅仅报告端到端的整体胜出。这些实验也揭示了论文在实践中的合适工作点：足够的推理和适中的视觉窗口有帮助，但过多的解码预算会抬高延迟。
      evidence:: E12, E13, E14
        - C3：把推理预算从每秒 0 个词元提高到每秒 20 个词元，可以让 OVO-Backward 从 41.8 提升到 52.3；而每秒 30 个词元只带来 52.6，还把延迟增加到 505 毫秒。
          evidence:: E12
        - C2：在论文所报告的参数扫描中，视觉键值缓存（KV cache）窗口在 20 秒时表现最佳，而在 5 秒、10 秒和 30 秒时 OVO-Backward 更低。
          evidence:: E13
        - C3：经过可验证奖励强化学习（Reinforcement Learning with Verifiable Rewards，RLVR）优化的思维链记忆，优于无记忆、离散字幕记忆和冷启动思维链记忆，直接支持了「以推理作为记忆」优于简单的文本字幕替代方案这一观点。
          evidence:: E14
    - **可复现性缺口:** 论文报告了实现选择、训练超参数、硬件、数据集构建方式，以及未来将公开代码、模型和数据，但所提供的正文并未证实这些产物目前已经可以获取。未作报告的内容包括：随机种子、重复实验次数、方差或误差棒、确切的基准测试脚本、完整的数据过滤代码，以及在其他 GPU 上的独立复现。
      claim_kind:: analyst_assessment
      evidence:: E11, E17, E18
- ## Technical Judgment
    - **站得住的结论:** 最有说服力的部分是问题、机制与消融实验三者之间的对应关系：流式处理需要有界的状态，RCSM（推理压缩流式记忆，Reasoning-Compressed Streaming Memory）提供了一种具体的状态表示，而记忆与窗口消融实验直接检验了这一表示。延迟性能剖析也把算法层面的缓存思想与运行时实现连接起来，而不是让它停留在建模层面的主张。
      claim_kind:: analyst_assessment
      evidence:: E6, E13, E14, E15, E16
    - **可能失效之处:** 当后续答案依赖于那些在推理轨迹尚未捕获之前就已被剔除的精细视觉细节时，这种方法可能会失效，因为 RCSM 有意用紧凑的文本状态替代密集的视觉证据。在确定性奖励格式之外，它可能也不够稳健，因为 RLVR 训练子集是围绕可自动验证的多选、二元判断和计数查询构建的。
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E13, E17
    - **与已有工作的关系:** 与视觉记忆和键值缓存（KV cache）压缩系统相比，ThinkStream 把一部分记忆从像素转移到生成的语义状态上；与事件触发系统相比，它让同一个生成式模型来决定是否发声。与离线视频思维链方法或强化学习方法相比，它的新意在于把推理绑定到逐前缀展开的流式循环上，而不仅仅绑定到最终答案上。
      claim_kind:: analyst_assessment
      evidence:: E3, E4, E6, E7
    - **可迁移启发:** 一条可迁移的系统设计经验是：让模型生成的中间文本成为一个显式的状态接口。也就是说，一旦模型对某种代价高昂的原始模态（如视频、音频）完成了解读，就保留最近的原始数据窗口，再加上一份紧凑的语义日志；随后把这份日志当作一种记忆表示来训练和评测，而不是仅仅把它看作用于解释的输出。
      claim_kind:: analyst_assessment
      evidence:: E6, E14, E18
- ## Glossary
  collapsed:: true
    - 流式视频理解（streaming video understanding）：一种视频-语言推理任务，视频随时间不断到达，模型只能依据到目前为止已观察到的内容来作答。
    - 看-想-说（Watch-Think-Speak）：ThinkStream 的交互循环，即先观看新到达的视频片段，再写下一段简短的推理更新，然后要么保持沉默，要么给出回应。
    - 键值缓存（key-value cache，KV cache）：保存下来的、来自较早词元的注意力键和值，使 transformer 能够生成新词元，而不必重新计算全部历史上下文。
    - 推理压缩式流式记忆（Reasoning-Compressed Streaming Memory，RCSM）：本文提出的记忆表示，它保留最近的视觉词元，并把生成的推理/动作词元用作紧凑的长期语义锚点。
    - 推理词元（reasoning tokens）：模型生成的中间文本，记录它对视频流当前的解读；在本文中，这些词元同时也充当记忆。
    - 可验证奖励强化学习（Reinforcement Learning with Verifiable Rewards，RLVR）：一种训练方式，其奖励可以根据可验证的条件自动计算，例如答案是否正确、输出是否符合规定格式，以及回应的时机是否恰当。
    - 分组相对策略优化（Group Relative Policy Optimization，GRPO）：一种强化学习目标函数，它针对同一个输入采样多条候选轨迹，并利用相对优势（配合裁剪与 KL 正则化）来优化策略。
    - 预填充与解码（prefill and decode）：预填充负责把新到来的上下文处理进缓存；解码则从缓存出发，一次生成一个输出词元。
    - CUDA Graph：一种 GPU 执行特性，它记录一段固定的操作序列，并通过重放这段序列来降低每一步的启动开销。
    - 视觉滑动窗口（visual sliding window）：指最近若干视频块组成的一段固定跨度，其密集视觉词元保留在缓存中，而更早的视频块则被清除。
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/metadata | Title and authors | high
      locator:: title block and arXiv header
      quote:: arXiv:2603.12938v1 [cs.CV] 13 Mar 2026. Thinking in Streaming Video. Zikang Liu, Longteng Guo, Handong Li, Ru Zhen, Xingjian He, Ruyi Ji, Xiaoming Ren, Yanhao Zhang, Haonan Lu, and Jing Liu.
    - **E2:** problem/paper_statement | 1 Introduction | high
      locator:: constraints paragraph
      quote:: Streaming scenarios impose several fundamental constraints: strict causality, where reasoning must rely only on observations available up to the current moment; low computation and memory usage; and timely interaction, which demands that the system maintain an up-to-date interpretation.
    - **E3:** gap/paper_statement | 1 Introduction | high
      locator:: batch paradigm gap paragraph
      quote:: Most existing video reasoning paradigms remain fundamentally batch: the model first consumes a long video context and only then performs multi-step reasoning to produce an answer. This design introduces unacceptable latency and weakens the connection between reasoning steps and the evidence that triggered them.
    - **E4:** prior_work/paper_statement | 2 Related Work | medium
      locator:: Sections 2.1 and 2.2
      quote:: Existing approaches heavily depend on dedicated classification heads or external event triggers. Conversely, our framework eschews external classifiers; by integrating a generative reasoning phase, the model autonomously determines whether to remain silent or respond.
    - **E5:** method/paper_statement | 3 Streaming Watch-Think-Speak Paradigm | high
      locator:: Sections 3.1 and 3.2
      quote:: At each step, the model observes a newly arrived video chunk and performs a short reasoning update that integrates the new evidence with previously accumulated context. Based on this evolving understanding, the model determines whether the available evidence is sufficient to produce a response.
    - **E6:** system_design/implementation_detail | 4.1 Reasoning-Compressed Streaming Memory | high
      locator:: RCSM definition and eviction paragraph
      quote:: The core idea of RCSM is to treat reasoning tokens as compressed semantic representations of earlier visual observations. Instead of storing the entire history of dense visual tokens, the model gradually replaces outdated visual features with the reasoning traces generated during the streaming reasoning process.
    - **E7:** algorithm/implementation_detail | 4.2 Streaming-Context RLVR Training | high
      locator:: reward design paragraph
      quote:: We formulate a rule-based reward system comprising three integral components: an accuracy reward, a format reward, and a time reward. The time reward quantifies the temporal discrepancy between the model's response step and the ground-truth step.
    - **E8:** result/experiment_result | 6.1 Main Results | medium
      locator:: Table 1 and OVO-Bench paragraph
      quote:: ThinkStream-3B achieves an overall average score of 59.66, significantly surpassing both its base model Qwen2.5-VL-3B (51.00) and competing open-source online models such as Streamo-3B (51.64) on OVO-Bench.
    - **E9:** result/experiment_result | 6.1 Main Results | medium
      locator:: Table 2 and StreamingBench paragraph
      quote:: On the StreamingBench Real-Time detailed in Tab. 2, ThinkStream-3B attains an average score of 75.00. This vastly exceeds other open-source online MLLMs like Dispider-7B (67.63) and demonstrates highly competitive performance against GPT-4o (73.28).
    - **E10:** result/experiment_result | 6.1 Main Results | medium
      locator:: Table 3 and offline benchmark paragraph
      quote:: Despite aggressively evicting visual tokens, ThinkStream-3B achieves highly competitive performance. Specifically, our model achieves a score of 61.9 on VideoMME and 56.4 on Long VideoBench, with an overall average score of 59.4.
    - **E11:** experiment_setup/implementation_detail | 6 Experiments | high
      locator:: implementation details paragraph
      quote:: We initialize our framework based on the Qwen2.5-VL-3B model. During the Cold Start phase, we train the model with a batch size of 64 and a learning rate of 1 x 10^-5. In the subsequent Reinforcement Learning phase, we employ a batch size of 8.
    - **E12:** ablation/ablation | 6.2 Ablation Study | medium
      locator:: Table 4 reasoning token budget
      quote:: Scaling the budget from 0 to 20 tokens significantly improves the OVO-Backward score from 41.8 to 52.3. However, allocating beyond 20 tokens per second results in marginal performance gains while decoding latency jumps from 380 ms to 505 ms.
    - **E13:** ablation/ablation | 6.2 Ablation Study | medium
      locator:: Table 5 visual KV cache window
      quote:: Setting the window size to 20 seconds achieves the best performance, peaking at 75.0 on StreamingBench Real-Time and 52.3 on OVO-Backward. Narrower windows such as 5s and 10s result in lower OVO-Backward scores.
    - **E14:** ablation/ablation | 6.2 Ablation Study | medium
      locator:: Table 6 memory representation and RLVR
      quote:: Posttraining the model with RLVR further boosts average performance by 4.3 points, reaching 64.8, demonstrating that reasoning tokens learn to act as a far superior, highly compressed long-term memory compared to naive discrete captions.
    - **E15:** result/profiling | 6.3 Efficiency and Real-Time Analysis | medium
      locator:: Figure 3 token decoding speed paragraph
      quote:: At a batch size of 1, our engine delivers 154.07 tokens/s compared to the baseline's 30.06 tokens/s, representing a more than 5x speedup. At a batch size of 8, our decoding speed scales efficiently to 766.87 tokens/s.
    - **E16:** result/profiling | 6.3 Efficiency and Real-Time Analysis | medium
      locator:: Figure 4 latency scaling paragraph
      quote:: Our combination of algorithmic KV cache eviction and engineering optimizations ensures that the end-to-end inference latency remains flat. It consistently stays below the 0.5s real-time threshold required for 2 FPS inputs.
    - **E17:** experiment_setup/paper_statement | 5 ThinkStream Dataset | medium
      locator:: dataset construction summary
      quote:: We ultimately construct 110K Cold Start instances paired with detailed reasoning traces, alongside 9K RLVR instances strictly formatted for verifiable reward optimization. Comprehensive details regarding the video source, dataset distributions and prompt templates are provided in the Appendix.
    - **E18:** implementation/implementation_detail | A More Implementation Details | medium
      locator:: Appendix A.1 and A.2
      quote:: Recording both decoding and pruning operations into static CUDA graphs eliminates per-step kernel launch overhead while preserving explicit control over KV cache manipulation. During training, we utilize FlexAttention to implement RCSM and incorporate the Liger Kernel.
