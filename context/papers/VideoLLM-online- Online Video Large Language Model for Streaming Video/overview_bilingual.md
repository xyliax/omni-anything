- **Title:** VideoLLM-online: Online Video Large Language Model for Streaming Video
  **标题:** VideoLLM-online：面向流式视频的在线视频大语言模型
- **Summary:** VideoLLM-online turns video-language assistance from offline clip answering into streaming dialogue by training a model to decide when to stay silent, reuse stream state, and answer in real time.
  **一句话总结:** VideoLLM-online 通过训练模型自主判断何时保持沉默、何时复用视频流状态、以及何时实时作答，把视频语言辅助从「离线的片段问答」转变为「流式对话」。
- **Paper Type:** system
  **论文类型:** 系统类论文
- **Venue:** arXiv:2406.11816v1, 2024
  **发表:** arXiv:2406.11816v1，2024 年
- **Authors:** Joya Chen, Zhaoyang Lv, Shiwei Wu, Kevin Qinghong Lin, Chenan Song, Difei Gao, Jia-Wei Liu, Ziteng Gao, Dongxing Mao, Mike Zheng Shou; Show Lab, National University of Singapore and Reality Labs Research, Meta
  **作者:** Joya Chen、Zhaoyang Lv、Shiwei Wu、Kevin Qinghong Lin、Chenan Song、Difei Gao、Jia-Wei Liu、Ziteng Gao、Dongxing Mao、Mike Zheng Shou；新加坡国立大学 Show Lab，以及 Meta 旗下 Reality Labs Research
- **Keywords:** online video understanding, video large language model, streaming dialogue, temporal alignment, key-value cache, egocentric video
  **关键词:** 在线视频理解、视频大语言模型、流式对话、时间对齐、键值缓存（KV cache）、第一人称视频
- ## Orientation
    - **Background:** This paper lives in video-language assistants: models that look at images from a moving camera and answer in text. The key prerequisite is that a video stream never really stops; new frames arrive while earlier context still matters.
      **背景:** 本文属于视频语言助手这一方向：这类模型观看来自移动摄像头的图像，并用文本作答。一个关键前提是，视频流实际上从不真正停止；新的画面帧不断到来，而先前的上下文仍然重要。
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** An assistant on smart glasses should notice what is happening now, remember what already happened, and answer only when the user needs help instead of talking over every tiny visual change.
      **通俗问题:** 运行在智能眼镜上的助手应当注意到当下正在发生什么，记住已经发生过的事，并且只在用户需要帮助时才作答，而不是对每一处微小的视觉变化都插话。
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** If the model speaks after every frame, it wastes time and fills its memory with repeated text; if it samples too sparsely, it can miss the exact moment when an action changes.
      **为何困难:** 如果模型对每一帧都开口说话，就会浪费时间，并让自己的记忆里充满重复的文本；如果它采样太稀疏，又可能错过某个动作发生变化的确切时刻。
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Teach the model to treat most frames as moments to stay silent, while keeping the stream in memory so it can speak at the right time.
      **一句话核心思路:** 训练模型把大多数帧都当作应当保持沉默的时刻，同时把视频流保留在记忆中，以便它能在恰当的时机开口。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as an online video-understanding view of large multimodal models, which are text generators extended to see visual input: it targets the gap between answering after a selected clip and assisting while a camera stream is still arriving.
      **阅读价值:** 可以把本文看作对大型多模态模型的一种在线视频理解视角。所谓大型多模态模型，是在文本生成器的基础上扩展、使其能够「看见」视觉输入的模型。本文瞄准的问题是：现有方法只能在选定片段结束后作答，而无法在摄像头视频流还在持续到达时就提供辅助——本文正是要填补这一空白。
      claim_kind:: analyst_assessment
      evidence:: E1, E2
    - **One-Sentence Contribution:** Learning-In-Video-strEam (LIVE), the paper's framework, improves streaming video dialogue by teaching the model a stay-silent decision on incoming frames instead of forcing a full text reply after each frame.
      **一句话贡献:** 本文提出的框架叫 Learning-In-Video-strEam（视频流中学习，LIVE）。它改进流式视频对话的做法是：教会模型对到来的每一帧做出「保持沉默」的判断，而不是强制在每一帧之后都生成完整的文字回复。
      evidence:: E1, E5
    - **Mental Model:** Picture a quiet kitchen helper: it watches every moment, keeps a running memory, and only speaks when a change matters or a user question needs an answer.
      **记忆模型:** 可以想象一个安静的厨房助手：它观察每一个时刻，持续维护一份运行记忆，只有当出现重要变化、或用户提问需要回答时，它才开口说话。
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is that the same design improves streaming timing and fluency, lowers memory and raises frame rate, and remains competitive on offline video benchmarks.
      **最佳证据:** 最有力的证据是：同一套设计既改善了流式场景下的作答时机和流畅度，又降低了内存占用、提高了帧率，同时在离线视频基准测试上仍保持竞争力。
      evidence:: E11, E12, E13, E14
        - Supports C1: COIN plus Ego4D stream validation; per-frame dialogue baseline; LM-PPL 2.56 vs 3.29, TimeDiff 4.21 vs 6.98 seconds, Fluency 39.8% vs 32.9%; supported for structured streaming-dialogue metrics.
          支持结论 C1：在 COIN 与 Ego4D 流式数据上验证；以逐帧对话作为基线；语言困惑度（LM-PPL）为 2.56 对 3.29，时间差（TimeDiff）为 4.21 秒对 6.98 秒，流畅度（Fluency）为 39.8% 对 32.9%；在结构化的流式对话指标上得到支持。
          evidence:: E18
        - Supports C2: Ego4D Narration Stream validation on a single A100 GPU; interleaved and per-frame baselines; memory 18.2G vs 34.4G and 24.9G, FPS 13.5 vs 1.5 and 7.5; supported without statistical uncertainty.
          支持结论 C2：在单块 A100 GPU 上用 Ego4D 旁白流（Narration Stream）验证；以交错式与逐帧作为基线；显存占用为 18.2G 对 34.4G 和 24.9G，帧率（FPS）为 13.5 对 1.5 和 7.5；结论成立，但未给出统计不确定性。
          evidence:: E12
        - Supports C3: COIN and Ego4D LTA test settings; prior end-to-end baselines; VideoLLM-online-8B-v1+ reports 63.1 step accuracy and 0.884 action edit distance; supported relative to end-to-end models, not strongest specialized cascades.
          支持结论 C3：在 COIN 与 Ego4D 长期动作预测（LTA）测试设定下进行；以此前的端到端模型作为基线；VideoLLM-online-8B-v1+ 报告的步骤准确率为 63.1，动作编辑距离为 0.884；该结论相对于端到端模型成立，但相对于最强的专用级联模型并不成立。
          evidence:: E13, E14
    - **Main Caveat:** The main caveat is external validity: the paper's own limitations say high-quality streaming dialogue data is scarce, and its streaming metrics are most reliable for simple narration rather than messy free-form assistance.
      **主要边界:** 主要的注意事项在于外部效度：论文自己的局限性部分指出，高质量的流式对话数据很稀缺，而它的流式指标对简单旁白最可靠，对杂乱的自由形式辅助任务则不然。
      claim_kind:: analyst_assessment
      evidence:: E10, E16
- ## Argument Map
    - **Problem and Stakes:** The paper defines video streaming dialogue as the setting where a large multimodal model (LMM), a language model connected to visual input, must decide whether the current frame is worth answering and then produce language using both history and the current video stream. The stakes are always-on assistants such as smart glasses, where missing the right moment, forgetting earlier context, or responding too slowly breaks usefulness.
      **问题与重要性:** 本文把视频流式对话（video streaming dialogue）定义为这样一种场景：一个大型多模态模型（large multimodal model，LMM）——即一个接入了视觉输入的语言模型——必须判断当前帧是否值得作答，然后结合历史信息和当前视频流来生成语言。其意义在于始终在线的助手（例如智能眼镜）：一旦错过恰当时机、遗忘早先的上下文，或响应太慢，可用性就会被破坏。
      evidence:: E2, E4
    - **Prior Gap:** Offline VideoLLMs usually answer after selected clips, while interleaved or per-frame dialogue makes every frame a text-generation turn, which is slow, repetitive, and context-hungry. The paper also shows that prompted GPT-4V can be verbose or unstable in this setting, so prompt discipline alone is not treated as a sufficient solution.
      **已有方法缺口:** 离线视频大语言模型（VideoLLM）通常是在选定的片段之后作答，而交错式或逐帧对话则把每一帧都变成一次文本生成，这样既慢、又重复，还很耗上下文。本文还表明，通过提示词驱动的 GPT-4V 在这一场景下可能话太多或不稳定，因此仅靠提示词上的约束不被视为充分的解决方案。
      evidence:: E3, E17
    - **Key Insight:** The key insight is that most frames in a stream are not answer moments, so the model should learn a cheap timing decision before doing expensive language generation. LIVE makes silence a supervised outcome on frame tokens, but does not append that silence token to the dialogue history.
      **关键洞见:** 核心洞见是：视频流中大多数帧并不是需要回答的时刻，因此模型应当先学会做出成本低廉的时机判断，再去执行成本高昂的语言生成。LIVE 把「保持沉默」当作帧词元（frame token）上的一个有监督结果来学习，但不会把这个沉默词元追加到对话历史中。
      evidence:: E5
    - **Claims:** The paper's claim chain is compact: a stay-silent training objective should improve online alignment, an inference pipeline should make it fast enough for streaming, and the resulting model should still handle standard offline video-language tasks.
      **核心主张:** 本文的论证链条很紧凑：一个「保持沉默」的训练目标应当能改善在线对齐效果，一个推理流水线应当能让它快到足以支持流式处理，而由此得到的模型仍应能胜任标准的离线视频语言任务。
      claim_kind:: analyst_assessment
        - C1: Streaming EOS prediction improves temporal responsiveness and fluency over interleaved or per-frame dialogue while preserving language modeling quality on streaming narration and dialogue evaluations.
          C1：与交错式或逐帧式对话相比，流式 EOS 预测（Streaming EOS prediction，即预测序列结束标记）能提升时间响应性与流畅度（fluency），同时在流式解说与对话评测中保持语言建模质量。
          evidence:: E11, E18
        - C2: Continuous key-value cache (KV cache), stored attention state that avoids recomputing old context, plus parallel frame encoding makes five-minute streaming inference lower-memory and higher-throughput than dialogue-style baselines.
          C2：连续的键值缓存（KV cache），即保存下来、可避免重复计算旧上下文的注意力状态，再加上并行的帧编码，使得五分钟的流式推理相比对话式基线更省内存、吞吐更高。
          evidence:: E9, E12
        - C3: A LIVE-trained VideoLLM-online model remains strong on offline video benchmarks, with state-of-the-art COIN results and the best Ego4D LTA result among end-to-end models reported in the paper.
          C3：经 LIVE 训练的 VideoLLM-online 模型在离线视频基准上依然表现强劲，取得了 COIN 上的最先进（state-of-the-art）结果，以及本文所报告的端到端模型中最好的 Ego4D LTA 结果。
          evidence:: E13, E14
- ## Mechanism and Design
    - **Core Mechanism:** LIVE combines normal autoregressive language modeling at answer timestamps with streaming End-of-Sequence (EOS) prediction, where EOS is a token used as a stop-or-stay-silent marker. The important design point is that a predicted EOS on a frame advances the stream without adding another dialogue turn to the model context.
      **核心机制:** LIVE 把两件事结合在一起：在需要回答的时间戳上执行常规的自回归语言建模，以及流式的序列结束（End-of-Sequence，EOS）预测——这里的 EOS 是一个用作「停止或保持沉默」标记的词元。关键的设计要点在于：在某一帧上预测出 EOS，会推进视频流，但不会向模型上下文中新增一轮对话。
      evidence:: E5, E8
    - **Data / Control Flow:** The system is a temporal pipeline: video frames become visual tokens, user and assistant text are interleaved in time order, training labels mark when to speak or stay silent, and inference reuses cached context while new frames keep arriving. This turns online assistance into an execution loop rather than a one-shot clip question.
      **数据/控制流:** 整个系统是一条时间流水线：视频帧变成视觉词元（visual token），用户和助手的文本按时间顺序交错排列，训练标签标注出何时应当发言、何时应当保持沉默，而推理时会复用已缓存的上下文，与此同时新的帧不断到达。这样一来，在线协助就从一次性的片段问答，变成了一个持续运行的执行循环。
      evidence:: E6, E7, E9
        - Frames are sampled at 2 FPS for training, encoded by CLIP or SigLIP vision encoders, projected by a multilayer perceptron (MLP), a small neural mapper, and fed as frame tokens into a Llama language model.
          训练时以每秒 2 帧（2 FPS）对帧进行采样，由 CLIP 或 SigLIP 视觉编码器进行编码，再经一个多层感知机（multilayer perceptron，MLP）——一个小型神经网络映射器——做投影，最后作为帧词元送入 Llama 语言模型。
          evidence:: E7
        - For offline datasets, the paper builds a timeline from timestamped annotations, inserts templated user questions, and treats state-change timestamps as the response points for synthetic streaming dialogue.
          对于离线数据集，本文根据带时间戳的标注构建出一条时间线，插入模板化的用户提问，并把状态变化的时间戳当作合成流式对话中的响应点。
          evidence:: E6
        - At inference, a first-in, first-out (FIFO) queue, a buffer that returns frames in arrival order, lets the fast visual encoder keep producing frame tokens while the slower language model decodes prior outputs.
          在推理时，使用一个先进先出（first-in, first-out，FIFO）队列——一个按到达顺序返回帧的缓冲区——让速度较快的视觉编码器可以持续产出帧词元，同时速度较慢的语言模型去解码此前的输出。
          evidence:: E9
    - **Design Decisions:** The design is conservative: avoid a text turn when nothing needs to be said, synthesize stream-like supervision from existing annotations, and trade spatial detail against context length by controlling tokens per frame. These choices target the bottleneck that matters most for streaming: unnecessary language generation.
      **设计决策:** 该设计偏保守：无话可说时就不进行文本回合，从已有标注中合成出类似流式的监督信号，并通过控制每帧的 token 数量，在空间细节与上下文长度之间做权衡。这些选择针对的是流式场景中最关键的瓶颈：不必要的语言生成。
      claim_kind:: analyst_assessment
      evidence:: E5, E6, E7, E15
        - Need: avoid per-frame dialogue overhead; choice: supervise EOS only on the last token of non-answer frames; closest alternative: explicit EOS dialogue turns; tradeoff: inference needs an EOS probability threshold.
          需求：避免逐帧对话带来的开销；选择：只在非回答帧的最后一个 token 上监督 EOS（序列结束标记）；最接近的替代方案：显式的 EOS 对话回合；权衡：推理时需要设定一个 EOS 概率阈值。
          evidence:: E5, E8, E9
        - Need: scarce online dialogue labels; choice: convert offline temporal annotations into dialogue at critical timestamps; closest alternative rejected: closed-set online action-detection labels that are too brief for free-form language training.
          需求：在线对话标注稀缺；选择：把离线的时间标注转换成关键时间点上的对话；被否定的最接近替代方案：闭集式的在线动作检测标注，因为它们太简短，不适合用于自由形式的语言训练。
          evidence:: E6
        - Need: fit long streams in a fixed context window; choice: one token per frame for most experiments and ten tokens per frame for demos; tradeoff: more spatial tokens can improve detail but shorten temporal coverage and show limited online-metric gain.
          需求：在固定的上下文窗口内容纳很长的视频流；选择：大多数实验采用每帧一个 token，演示时采用每帧十个 token；权衡：更多的空间 token 能提升细节，但会缩短时间覆盖范围，而且在在线指标上的提升有限。
          evidence:: E7, E15, E16
    - **Implementation Surface:** VideoLLM-online is implemented as a LLaVA-style stack: frozen or pretrained visual encoder, two-layer MLP connector, Llama-2-7B-Chat or Llama-3-8B-Instruct language model, and Low-Rank Adaptation (LoRA), a parameter-efficient tuning method, on every LLM linear layer. The main experimental model is the efficient 7B version; the 8B plus spatial-token variant is trained mainly for stronger demos and variant comparisons.
      **实现边界:** VideoLLM-online 采用 LLaVA 风格的架构堆栈实现：冻结或预训练的视觉编码器、两层 MLP 连接器、Llama-2-7B-Chat 或 Llama-3-8B-Instruct 语言模型，以及在每个 LLM 线性层上使用的低秩适配（Low-Rank Adaptation，LoRA），这是一种参数高效的微调方法。主要的实验模型是高效的 7B 版本；8B 加空间 token 的变体主要用于更有说服力的演示和变体对比。
      evidence:: E7, E15
- ## Evaluation and Evidence
    - **Setup:** The streaming evaluation uses Ego4D Narration Stream and a COIN plus Ego4D stream set, measuring language perplexity (LM-PPL), time difference (TimeDiff), language-generation matching, and Fluency, a metric for consecutive correct token prediction within a dialogue turn. Offline evaluation uses COIN procedural tasks and Ego4D Long-Term Anticipation (LTA), where future actions are compared by edit distance.
      **实验设置:** 流式评测使用 Ego4D Narration Stream 以及一个 COIN 加 Ego4D 的视频流集合，衡量指标包括语言困惑度（LM-PPL）、时间差（TimeDiff）、语言生成匹配度，以及 Fluency——一种衡量在同一对话回合内连续正确预测 token 的指标。离线评测使用 COIN 的流程性任务和 Ego4D 长期预测（Long-Term Anticipation，LTA），在后者中通过编辑距离来比较未来动作。
      evidence:: E10
    - **Claim-Evidence Matrix:** The evidence best supports the system-level claim that avoiding unnecessary language turns improves the latency-memory-temporal-alignment tradeoff. It is weaker for broad open-world assistant quality because the streaming metrics are designed for relatively simple narration and structured generated dialogue.
      **主张-证据矩阵:** 现有证据最能支持系统层面的论断，即避免不必要的语言回合可以改善延迟、内存和时间对齐三者之间的权衡。而对于更宽泛的开放世界助手质量，证据则较弱，因为这些流式指标是为相对简单的旁白叙述和结构化的生成式对话设计的。
      claim_kind:: analyst_assessment
      evidence:: E10, E11, E12, E18
        - C1 is supported by same-architecture ablations and the COIN plus Ego4D stream set, with better TimeDiff and Fluency than per-frame dialogue while keeping lower LM-PPL.
          C1 由相同架构下的消融实验以及 COIN 加 Ego4D 视频流集合支持：相比逐帧对话，它取得了更好的 TimeDiff 和 Fluency，同时保持更低的 LM-PPL。
          evidence:: E11, E18
        - C2 is supported by an efficiency table on five-minute Ego4D clips, but the paper reports a single hardware setting rather than a scaling curve across GPUs, frame rates, or context lengths.
          C2 由在五分钟 Ego4D 片段上的效率表支持，但论文只报告了单一硬件配置下的结果，而没有给出跨 GPU、跨帧率或跨上下文长度的伸缩曲线。
          claim_kind:: analyst_assessment
          evidence:: E12
        - C3 is supported for end-to-end offline models on COIN and Ego4D LTA, but AntGPT remains better on LTA with a specialized non-end-to-end cascade.
          C3 在 COIN 和 Ego4D LTA 上对端到端离线模型是成立的，但在 LTA 上，AntGPT 凭借一套专门的非端到端级联方案仍然表现更好。
          evidence:: E13, E14
    - **Headline Results:** For streaming efficiency, LIVE reports 18.2G memory and 13.5 FPS on a single A100, compared with 34.4G and 1.5 FPS for interleaved dialogue and 24.9G and 7.5 FPS for per-frame streaming. For offline benchmarks, the 8B-v1+ model reports the best COIN scores in the table and 0.884 Ego4D LTA action edit distance among end-to-end models.
      **关键结果:** 在流式处理效率方面，LIVE 在单块 A100 上的显存占用为 18.2G、帧率为 13.5 FPS，而交错式对话为 34.4G 和 1.5 FPS，逐帧流式处理为 24.9G 和 7.5 FPS。在离线基准测试方面，8B-v1+ 模型取得了表中最好的 COIN 分数，并在端到端模型中取得了 0.884 的 Ego4D LTA 动作编辑距离。
      evidence:: E12, E13, E14
    - **Ablations and Sensitivity:** The ablations suggest that the simple cross-entropy streaming loss is enough: OHEM and Focal Loss do not improve the reported LM-PPL, TimeDiff, or Fluency, and changing the streaming-loss weight around the default has only small effects. Model variants show that the Llama-3 8B backbone improves online metrics, while adding spatial tokens improves little on the reported streaming metrics.
      **消融与敏感性:** 消融实验表明，简单的交叉熵流式损失已经足够：OHEM 和 Focal Loss 并未改善所报告的语言困惑度（LM-PPL）、时间差（TimeDiff）或流畅度（Fluency），而在默认值附近调整流式损失权重也只带来很小的影响。模型变体的结果显示，采用 Llama-3 8B 主干网络能改善在线指标，而加入空间标记（spatial token）对所报告的流式指标改善甚微。
      evidence:: E11, E15
    - **Reproducibility Gaps:** Reported availability includes code, model, data, and demo, and the efficiency setup names an A100 GPU. Not reported: repeat counts, variance or confidence intervals, a full reconstruction recipe for every synthetic dialogue sample, and broad hardware or frame-rate scaling beyond the reported settings.
      **可复现性缺口:** 论文报告的可获得资源包括代码、模型、数据和演示，并且效率实验的配置指明使用了 A100 GPU。未报告的内容包括：重复次数、方差或置信区间、针对每一个合成对话样本的完整复现流程，以及超出所报告设置的更广泛硬件或帧率扩展情况。
      claim_kind:: analyst_assessment
      evidence:: E1, E12
- ## Technical Judgment
    - **What Holds Up:** The strongest contribution is making silence a first-class supervised decision rather than treating every frame as a dialogue turn. That directly attacks the shared cause of slow speed, bloated context, and poor temporal alignment, and the paper checks it against same-architecture baselines rather than only against unrelated systems.
      **站得住的结论:** 最有力的贡献在于把「保持沉默」当作一个受监督的一等决策，而不是把每一帧都当成一个对话回合来处理。这直接针对了速度慢、上下文臃肿和时间对齐差这些问题的共同根源，而且论文是针对相同架构的基线来验证它，而非仅仅与不相关的系统对比。
      claim_kind:: analyst_assessment
      evidence:: E5, E10, E11, E12
    - **Where It May Fail:** The method may fail when user intent is less templated, visual detail matters more than temporal coverage, or the stream distribution differs from egocentric instructional data. The paper itself flags scarce high-quality streaming dialogue data, small-dataset overfitting, and weak spatial ability from using few spatial tokens.
      **可能失效之处:** 当用户意图不那么模板化、视觉细节比时间覆盖更重要，或者视频流的分布与第一人称视角的教学数据不同时，该方法可能会失效。论文本身也指出了几个问题：高质量流式对话数据稀缺、小数据集上的过拟合，以及因使用的空间标记（spatial token）过少而导致的空间能力较弱。
      claim_kind:: analyst_assessment
      evidence:: E10, E16
    - **Relation to Other Work:** Compared with offline VideoLLMs, the paper changes the lifecycle of input from selected clip to continuous stream; compared with online action detection, it targets free-form language instead of one closed-set label; compared with AntGPT on Ego4D LTA, it is simpler and end-to-end but not the best specialized result. The technical axis is therefore not just accuracy, but whether the model can decide when a language turn should exist.
      **与已有工作的关系:** 与离线视频大语言模型（VideoLLM）相比，这篇论文改变了输入的生命周期，从选取的视频片段变为连续的视频流；与在线动作检测相比，它面向的是自由形式的语言，而非单个封闭集合的标签；与在 Ego4D LTA 上的 AntGPT 相比，它更简单且端到端，但不是最好的专门化结果。因此，其技术核心不只是准确率，而是模型能否判断一个语言回合应当在何时出现。
      claim_kind:: analyst_assessment
      evidence:: E2, E10, E14
    - **Transferable Lesson:** For continuous perception systems, do not force a full semantic output at every sensor tick; train a cheap no-output decision, preserve reusable state, and reserve expensive generation for moments where the output changes user value. This pattern transfers beyond video to any streaming multimodal assistant with many boring timesteps and occasional important ones.
      **可迁移启发:** 对于连续感知系统，不要在每一个传感器采样时刻都强制产出完整的语义输出；而应训练一个廉价的「不输出」决策，保留可复用的状态，并把昂贵的生成保留给那些输出会改变用户价值的时刻。这一模式可以推广到视频之外，适用于任何具有大量无关紧要时间步、偶尔出现重要时间步的流式多模态助手。
      claim_kind:: analyst_assessment
      evidence:: E5, E9
- ## Glossary
  collapsed:: true
    - Large multimodal model: A language model extended to process non-text inputs such as images or video frames; in this note, it is the base model family VideoLLM-online belongs to.
      大型多模态模型（Large multimodal model，LMM）：一种经过扩展、可以处理图像或视频帧等非文本输入的语言模型；在本笔记中，它是 VideoLLM-online 所属的基础模型家族。
    - Video streaming dialogue: The paper's target setting: video frames arrive continuously, and the assistant must decide when to answer while preserving prior visual-language context.
      视频流式对话（Video streaming dialogue）：这篇论文所针对的场景，即视频帧持续不断地到达，助手必须在保留先前视觉-语言上下文的同时判断何时作出回答。
    - Streaming EOS prediction: LIVE's timing objective: predict an EOS-like stay-silent marker on non-answer frame tokens, without appending that marker to the dialogue context.
      流式序列结束预测（Streaming EOS prediction）：LIVE 的时序目标，即在非回答帧的标记上预测一个类似 EOS 的「保持沉默」标记，同时不把该标记追加到对话上下文中。
    - Key-value cache: Stored attention state from previous tokens, reused so the language model does not recompute the whole stream history for each new token.
      键值缓存（Key-value cache）：存储此前各 token（词元）的注意力状态并加以复用，使语言模型无需为每个新 token 重新计算整段流式历史。
    - Low-Rank Adaptation: A parameter-efficient fine-tuning method that trains small low-rank updates inside model layers instead of updating all language-model weights.
      低秩适配（Low-Rank Adaptation）：一种参数高效的微调方法，在模型各层内部训练小规模的低秩更新，而不是更新语言模型的全部权重。
    - Language perplexity: A lower-is-better language-modeling metric used here to judge whether the model predicts the expected narration or answer tokens well.
      语言困惑度（Language perplexity）：一种越低越好的语言建模指标，这里用来判断模型是否能很好地预测出预期的旁白 token 或答案 token。
    - Time Difference: The paper's lower-is-better temporal-alignment metric: average difference between the model response timestamp and the expected response timestamp.
      时间差（Time Difference）：本文提出的越低越好的时间对齐指标，即模型回复时间戳与预期回复时间戳之间的平均差值。
    - Fluency: The paper's streaming metric for the proportion of consecutive successful token prediction within a dialogue turn, intended to combine language correctness and timing.
      流畅度（Fluency）：本文提出的流式指标，衡量一个对话轮次内连续成功预测 token 的比例，目的是把语言正确性和时间准确性结合起来。
    - COIN: An instructional video dataset used for step recognition, task summarization, and forecasting benchmarks, and as a source for synthetic streaming dialogue.
      COIN：一个教学视频数据集，用于步骤识别、任务摘要和预测等基准测试，同时也作为合成流式对话的来源。
    - Ego4D Long-Term Anticipation: An egocentric-video benchmark where the model predicts a sequence of future actions; the paper evaluates generated text by mapping it back to verb and noun labels.
      Ego4D 长期预测（Ego4D Long-Term Anticipation）：一个第一人称视角视频基准，要求模型预测一串未来的动作；本文通过把生成的文本映射回动词和名词标签来评估结果。
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/paper_statement | Abstract | high
      locator:: Abstract, lines 48-54
      quote:: we propose a novel Learning-InVideo-Stream (LIVE) framework, which enables temporally aligned, long-context, and real-time conversation within a continuous video stream.
    - **E2:** problem/paper_statement | 1. Introduction | high
      locator:: Introduction, online assistant challenges
      quote:: an online assistant should continuously receive video frames with visual content that is constantly refreshed. This paradigm shift presents new challenges. First, the user query may come with temporally aligned requirements... Second... retain the long-context historical vision and language... Third... generate the answer in real-time
    - **E3:** gap/paper_statement | 1. Introduction | high
      locator:: Introduction, per-frame prompting analysis
      quote:: GPT-4V tends to output lengthy content at every frame, leading to significant delays, making it impractical for real-time streaming video. We also explore training baseline models for per-frame chatting. Unfortunately, this approach evidently diminishes the language modeling capability
    - **E4:** method/paper_statement | 3.1. Video Streaming Dialogue | high
      locator:: Problem Formulation
      quote:: Given the context sequence before time t = t1... and an ongoing continuous video stream from t1 to t2... our goal is (1) to determine whether the current time t2 is suitable for language modeling; (2) to carry out language modeling
    - **E5:** algorithm/paper_statement | 3.1. Video Streaming Dialogue | high
      locator:: Streaming EOS Prediction
      quote:: for timestamps t1 <= t < t2, which are redundant for producing answers, we directly learn the model to predict EOS token on the frame tokens... During inference, if EOS is predicted on a frame, then we can directly ask the next frame to input. Meanwhile, the EOS token is not appended to the context
    - **E6:** method/paper_statement | 3.2. Data | high
      locator:: Offline Annotations to Video Streaming Dialogue
      quote:: we propose a method for synthesizing dialogue data from these sources... prepare a question template library... obtain the video annotation timeline... consider all the state change critical timestamps as the ideal response times... prompt the large language model to generate responses at every critical timestamp
    - **E7:** implementation/implementation_detail | 3.3. Model Training | high
      locator:: Model Architecture and footnote 3
      quote:: it comprises three key components: an image encoder, an MLP projector, and a language model... CLIP ViT-L... fed into MLP projector to frame tokens... interleaved with language tokens as input to an LLM, Llama-2-7B-Chat or Llama-3-8B-Instruct
    - **E8:** algorithm/paper_statement | 3.3. Model Training | high
      locator:: Training Loss
      quote:: The first part focuses on autoregressive language modeling... The second training objective involves streaming EOS prediction, which requires the model to remain silent when it is unnecessary to output responses. With these two training objectives, we have language modeling (LM) loss and streaming loss terms
    - **E9:** optimization/implementation_detail | 3.4. Inference | high
      locator:: Probability Correction, Continuous Key-Value Cache, Parallelization
      quote:: we introduce a threshold theta to correct the output probability on frame tokens... we use the key-value cache trick to accelerate token decoding... parallelize the processes and establish a FIFO queue for video frame tokens. The fast encoder does not need to wait the slow LLM
    - **E10:** experiment_setup/paper_statement | 4.2. Evaluation Setting | high
      locator:: Datasets, Evaluation metrics, Baselines
      quote:: We use... Ego4D Narration Stream... COIN Benchmarks... Ego4D long-term action anticipation (LTA) benchmark... We use common language perplexity... Time Difference (TimeDiff)... Fluency... build baseline models for video-text interleaved dialogue, per-frame dialogue... with the same model architecture and training details
    - **E11:** ablation/ablation | 4.3. Ablation Study | medium
      locator:: Learning Method and Streaming Loss
      quote:: Both vision-language interleaved and streaming methods exhibit low perplexity loss... When we turn to online metrics of TimeDiff and Fluency, streaming dialogue method yields much better results than others... Standard CE... LM-PPL 2.43, TimeDiff 2.32, Fluency 42.6%
    - **E12:** result/experiment_result | 4.3. Ablation Study | medium
      locator:: Table 1d, Inference Efficiency
      quote:: we test the inference efficiency on Ego4D narration stream validation set (5 minute), and report the memory cost and average FPS on a single A100 GPU... Interleaved 34.4G 1.5 FPS... Per-frame Streaming 24.9G 7.5 FPS... Streaming 18.2G 13.5 FPS
    - **E13:** result/experiment_result | 4.4. Results | medium
      locator:: Table 2a, COIN benchmarks
      quote:: VideoLLM-online-7B-v1... Step 59.8, Task 92.1, Next 48.1, Proc. 47.9, Proc.+ 52.9. VideoLLM-online-8B-v1+... Step 63.1, Task 92.7, Next 49.1, Proc. 49.8, Proc.+ 54.1
    - **E14:** result/experiment_result | 4.4. Results | medium
      locator:: Table 2b, Ego4D LTA and discussion
      quote:: VideoLLM-online-8B-v1+... Verb 0.689, Noun 0.671, Action 0.884... Although the results of AntGPT are better than us, they used egocentric pre-trained visual feature, and integrates lots of complex cascading methods
    - **E15:** result/experiment_result | 4.4. Results | medium
      locator:: Table 3, model variants
      quote:: VideoLLM-online-7B-v1... LG-Match 42.3%, TimeDiff 2.25, Fluency 42.6%. VideoLLM-online-8B-v1... 48.3%, 2.05, 45.2%. VideoLLM-online-8B-v1+... 49.0%, 2.05, 45.3%
    - **E16:** limitation/limitation | Supplementary Material D. Limitations | high
      locator:: D. Limitations
      quote:: Our primary limitation lies in the inadequacy of high-quality streaming dialogue data, which hinders its generalization capability... We observe the method can overfit when training on a small dataset... the spatial ability is not strong due to its less spatial token.
    - **E17:** gap/case_study | Supplementary Material A. Analysis to Per-frame Chatting | medium
      locator:: A. Analysis to Per-frame Chatting
      quote:: GPT-4V can be prompted to approach the video streaming dialogue. However, it is still per-frame dialogue and still cost tokens and times per frame. Moreover, we find it is not so stable; sometimes there would be obvious hallucination
    - **E18:** result/experiment_result | Supplementary Material C. More Results | medium
      locator:: Table 4, COIN + Ego4D Stream Validation
      quote:: COIN + Ego4D Stream Validation... Per-frame Dial. LM-PPL 3.29, TimeDiff 6.98, Fluency 32.9%. LIVE LM-PPL 2.56, TimeDiff 4.21, Fluency 39.8%... LIVE consistently performs better than per-frame dialogue method.
