- **Title:** Live CC: Learning Video LLM with Streaming Speech Transcription at Scale
  **标题:** Live CC：通过大规模流式语音转录来训练视频大语言模型
- **Summary:** LiveCC shows that timestamp-aligned automatic speech recognition captions can cheaply train a streaming video large language model to comment frame by frame while improving several video question-answering benchmarks.
  **一句话总结:** LiveCC 表明，带时间戳对齐的自动语音识别字幕可以低成本地训练出一个流式视频大语言模型，使其能够逐帧进行解说，同时在多个视频问答基准测试上取得提升。
- **Paper Type:** system
  **论文类型:** 系统
- **Venue:** arXiv preprint 2025
  **发表:** arXiv 预印本 2025
- **Authors:** Joya Chen, Ziyun Zeng, Yiqi Lin, and Mike Zheng Shou (Show Lab, National University of Singapore); Wei Li and Zejun Ma (ByteDance)
  **作者:** Joya Chen、Ziyun Zeng、Yiqi Lin、Mike Zheng Shou（新加坡国立大学 Show Lab）；Wei Li、Zejun Ma（ByteDance）
- **Keywords:** video large language model, streaming video understanding, automatic speech recognition, closed captions, real-time commentary, video question answering
  **关键词:** 视频大语言模型、流式视频理解、自动语音识别、隐藏式字幕、实时解说、视频问答
- ## Orientation
    - **Background:** Many video assistants learn by looking at finished clips and then writing an answer. Live use is different: the model sees the scene unfold and must speak while new frames are still arriving.
      **背景:** 许多视频助手的学习方式是：先看完整段片段，再写出答案。但实时使用完全不同：模型是在场景逐步展开的过程中观看，并且必须在新画面还在不断到来时就开口说话。
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A live commentator cannot wait for the whole video. It must say useful words now, using only what has happened so far and the speech-like context already produced.
      **通俗问题:** 实时解说无法等到整段视频结束。它必须现在就说出有用的话，而且只能依据到目前为止已经发生的内容，以及已经生成的、类似口语的上下文。
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** Natural speech is messy, partial, and unevenly timed, while video events change continuously. Cheap captions are abundant but noisy, so the model must learn alignment without carefully written labels.
      **为何困难:** 自然语音杂乱、零碎，且时间分布不均匀，而视频里的事件是持续变化的。廉价的字幕数量庞大却充满噪声，因此模型必须在没有精心撰写的标注的情况下，自行学会对齐。
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Train on the web's existing spoken captions by matching small bursts of words to the frames that occurred at the same time.
      **一句话核心思路:** 利用网络上现成的口语字幕来训练：把一小段一小段的词语，与同一时刻出现的画面对应起来。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a streaming video-language modeling paper: it asks whether cheap automatic speech recognition (ASR), text automatically transcribed from video audio or captions, can replace expensive human or GPT-style training data for live commentary.
      **阅读价值:** 把这篇论文当作一篇流式视频语言建模的工作来读：它探讨的问题是，廉价的自动语音识别（ASR，即从视频音频或字幕中自动转录出的文本）能否替代昂贵的人工标注或 GPT 式的训练数据，来支撑实时解说任务。
      claim_kind:: analyst_assessment
      evidence:: E2
    - **One-Sentence Contribution:** LiveCC improves live video commentary by training a video large language model (Video LLM), a language model conditioned on video frames, to predict the caption words aligned with each incoming frame instead of waiting to caption the whole clip.
      **一句话贡献:** LiveCC 改进了实时视频解说，方法是训练一个视频大语言模型（Video LLM，即以视频帧为条件输入的语言模型），让它预测与每一帧输入对齐的字幕文字，而不是等看完整段视频再生成字幕。
      evidence:: E3, E6
    - **Mental Model:** Picture a sports announcer reading a ticker that reveals only the current moment: after each glimpse of the field, the announcer says the next few words and carries the previous words forward.
      **记忆模型:** 可以想象一位体育解说员在看一条只显示当前时刻的滚动字幕：每瞥一眼场上情况，解说员就说出接下来的几个词，并把之前说过的话延续下去。
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest support is that streaming-style pre-training raises commentary win rate over caption-style training, and the final small model beats several larger baselines on commentary while staying competitive on question answering.
      **最佳证据:** 最有力的证据是，流式风格的预训练相比字幕风格的训练提高了解说的胜率，而且最终的小模型在解说上超过了多个更大的基线模型，同时在问答上保持了竞争力。
      evidence:: E12, E15, E16
        - Supports C1: 5M pre-training clips; caption-style ASR baseline; LiveSports-3K-CC win rate; 32.9 versus 14.0; supported, with no variance reported.
          支持 C1：500 万条预训练片段；采用字幕风格的自动语音识别（ASR）作为基线；在 LiveSports-3K-CC 上的胜率为 32.9 对 14.0；结论成立，但未报告方差。
          evidence:: E12
        - Supports C3: LiveCC-7B-Instruct; Qwen2-VL-7B-Instruct and LLaVA-Video-7B baselines; VideoMME without subtitles and OVOBench average; 64.1 versus 63.3 and 59.8 versus 52.9; supported, without uncertainty estimates.
          支持 C3：LiveCC-7B-Instruct；以 Qwen2-VL-7B-Instruct 和 LLaVA-Video-7B 作为基线；在不带字幕的 VideoMME 和 OVOBench 平均分上，分别为 64.1 对 63.3、59.8 对 52.9；结论成立，但没有给出不确定性估计。
          evidence:: E15
        - Supports C4: LiveCC-7B-Instruct; LLaVA-Video-72B closest open commentary baseline; LiveSports-3K-CC win rate; 41.5 versus 35.0; supported, but judge-based.
          支持 C4：LiveCC-7B-Instruct；以 LLaVA-Video-72B 作为最接近的开源解说基线；在 LiveSports-3K-CC 上的胜率为 41.5 对 35.0；结论成立，但依赖评审模型打分。
          evidence:: E16
    - **Main Caveat:** The main trust boundary is that free-form commentary is judged by GPT-4o against ASR-derived ground truth, so the strongest result mixes visual correctness, human-commentary style, and judge preference.
      **主要边界:** 主要的信任边界在于：自由形式的解说由 GPT-4o 对照从自动语音识别（ASR）得到的参考答案来评判，因此最强的结果其实混合了视觉正确性、人类解说风格与评审模型的偏好这三方面。
      claim_kind:: analyst_assessment
      evidence:: E10, E16
- ## Argument Map
    - **Problem and Stakes:** Training real-time video large language models (Video LLMs), language models that condition on video frames, with human or LLM-written streaming conversations is expensive and small-scale. Treating automatic speech recognition (ASR), machine speech-to-text from video audio or captions, as one global caption wastes the timing signal needed for live assistants.
      **问题与重要性:** 用人工或大语言模型撰写的流式对话来训练实时视频大语言模型（Video LLM，即以视频帧为条件的语言模型），成本高昂且规模有限。而把自动语音识别（Automatic Speech Recognition，ASR，即由视频音频或字幕机器转写成的文字）当作一整段全局字幕来处理，会浪费掉实时助手所需要的时间信号。
      evidence:: E2
    - **Prior Gap:** Prior video-ASR learning usually predicted paragraph-level or clip-level captions, while streaming Video LLM work often depended on manually crafted or GPT-crafted data. The missing piece was a scalable way to use word timestamps as supervision for causal video-language learning, where the model only uses past and current input.
      **已有方法缺口:** 以往基于视频与自动语音识别（ASR）的学习通常是预测段落级或片段级的字幕，而流式视频大语言模型（Video LLM）的研究则往往依赖人工制作或由 GPT 生成的数据。真正缺失的一环，是一种可扩展的方法，能把词语时间戳当作监督信号，用于因果式的视频-语言学习，也就是模型只使用过去和当前的输入。
      evidence:: E2, E3
    - **Key Insight:** If ASR words are aligned to the frame intervals in which they were spoken, next-word prediction becomes a stream-local supervision signal rather than a clip-level captioning task. This turns cheap captions into training data for frame-by-frame commentary.
      **关键洞见:** 如果把 ASR 词与它们被说出时所对应的帧区间对齐，那么「预测下一个词」就变成了一种流内局部的监督信号，而不再是片段级的字幕生成任务。这样一来，廉价的字幕就变成了可用于逐帧解说的训练数据。
      evidence:: E3, E6
    - **Claims:** The paper's main claims are falsifiable through sequence-style ablations, data-scaling ablations, benchmark construction, and cross-model evaluation.
      **核心主张:** 论文的主要论断可以通过序列格式消融实验、数据规模消融实验、基准构建以及跨模型评估来加以证伪。
      claim_kind:: analyst_assessment
        - C1: Dense interleaving of frame tokens and timestamped ASR words improves streaming commentary over caption-style video-ASR pre-training while preserving short-video question-answering (QA) performance.
          C1：把帧token与带时间戳的 ASR 词密集交错排列，相比字幕式的「视频-ASR」预训练，能改进流式解说的效果，同时保持短视频问答（question-answering，QA）的性能。
          evidence:: E3, E12
        - C2: Scaling curated YouTube closed-caption pre-training improves commentary quality, but the paper observes QA decline beyond the chosen scale because the data source is narrow.
          C2：扩大经过筛选的 YouTube 闭合字幕（closed captions，CC）预训练规模，能提升解说质量；但论文观察到，一旦超过所选规模，QA 性能反而下降，原因是数据来源过于单一。
          evidence:: E5, E13
        - C3: Adding high-quality WhisperX speech-transcriber data for supervised fine-tuning (SFT), the step that adapts a base model to instructions, and general video QA data improves commentary formatting while producing competitive 7B-level general video QA.
          C3：为监督微调（supervised fine-tuning，SFT）——即让基座模型适应指令的那一步——加入高质量的 WhisperX 语音转写数据以及通用视频 QA 数据，能改进解说的格式，同时产出具有竞争力的 7B 级通用视频 QA 表现。
          evidence:: E14, E15
        - C4: LiveSports-3K provides a benchmark for visually grounded sports commentary and event QA, separating free-form commentary quality from Who, When, and What multiple-choice behavior.
          C4：LiveSports-3K 提供了一个基准，用于评测基于视觉内容的体育解说和事件 QA，把自由形式的解说质量与「谁、何时、什么」这类选择题的表现区分开来。
          evidence:: E9, E10, E16
- ## Mechanism and Design
    - **Core Mechanism:** LiveCC represents each stream interval as visual tokens, compact frame representations consumed by the language model, followed by the ASR words assigned to that interval. The model predicts only text tokens, so frame information is conditioning input and the word sequence becomes the supervised target.
      **核心机制:** LiveCC 把每个流区间表示为一串视觉token——也就是供语言模型使用的紧凑帧表示——其后紧跟着分配给该区间的 ASR 词。模型只预测文本token，因此帧信息是作为条件输入，而词序列则成为监督目标。
      evidence:: E3, E6, E7
    - **Data / Control Flow:** The system collects YouTube videos with closed captions (CC), filters for English and visually useful speech, converts caption chunks into word timestamps, trains Qwen2-VL-7B-Base on interleaved streams, then fine-tunes with cleaner WhisperX transcripts plus general video QA.
      **数据/控制流:** 该系统收集带闭合字幕（closed captions，CC）的 YouTube 视频，筛选出英语且在视觉上有用的语音，把字幕块转换成词级时间戳，在交错流上训练 Qwen2-VL-7B-Base，然后再用更干净的 WhisperX 转写文本加上通用视频 QA 进行微调。
      evidence:: E4, E5, E11
        - Pre-training data aggregates HD-VILA, YT-Temporal-1B, VidChapters, and HowTo100M, filters to 10.7M candidate IDs and then 5.7M English-captioned videos, and segments them into Live-CC-5M clips.
          预训练数据汇总了 HD-VILA、YT-Temporal-1B、VidChapters 和 HowTo100M，先筛选到 10.7M 个候选 ID，再筛到 5.7M 个带英语字幕的视频，并把它们切分成 Live-CC-5M 片段。
          evidence:: E5
        - SFT data keeps selected YouTube categories, reruns WhisperX large-v3-turbo for word-level timestamps, removes active-speaker talking-head clips, and asks GPT-4o to generate prompts that match the transcript style without revealing content.
          SFT 数据保留选定的 YouTube 类别，重新运行 WhisperX large-v3-turbo 来获得词级时间戳，去除主动说话人（active speaker）的特写讲话片段，并让 GPT-4o 生成与转写风格一致、但不泄露内容的提示。
          evidence:: E4, E7
        - At inference, LiveCC processes frames sequentially, stores Key-Value (KV) cache entries, the transformer attention state reused from previous tokens, and periodically drops old visual tokens while keeping text context.
          在推理阶段，LiveCC 逐帧处理视频画面，并存储键值缓存（KV cache）条目，也就是从之前的 token 中复用的 Transformer 注意力状态；它还会周期性地丢弃旧的视觉 token（frame tokens），同时保留文本上下文。
          evidence:: E8
    - **Design Decisions:** The major design choices all reduce ambiguity in cheap, messy ASR supervision: align words locally to frames, provide context when a clip starts mid-sentence, mark silence explicitly, and filter speech that is not visually grounded.
      **设计决策:** 主要的设计选择都是为了减少在廉价而嘈杂的 ASR 监督信号中的歧义：把词语在局部与视频帧对齐；当片段从句子中途开始时提供上下文；显式标记静默；以及过滤那些与画面内容缺乏关联的语音。
      evidence:: E4, E6, E7, E13
        - Need: teach live speech instead of offline captioning; choice: densely interleave frames and words; closest reported alternative: concatenate all ASR after frames; tradeoff: stronger commentary but still bounded by noisy timestamps.
          需求：教会模型做实时解说，而不是离线字幕生成；选择：把视频帧和词语密集交错排列；文中提到的最接近的替代方案：把所有 ASR 文本拼接在视频帧之后；权衡：解说能力更强，但仍受制于带噪声的时间戳。
          evidence:: E3, E12
        - Need: clips may begin mid-thought and include pauses; choice: use title or previous ASR as context and an ellipsis as an end-of-sequence (EOS) marker for silent frames; tradeoff: context helps commentary but title context can hurt QA.
          需求：片段可能从某个想法的中途开始，并且包含停顿；选择：用标题或前一段 ASR 文本作为上下文，并用省略号作为静默帧的序列结束标记（end-of-sequence，EOS）；权衡：上下文有助于解说，但标题上下文可能损害问答表现。
          evidence:: E7, E13
        - Need: captions are useful only when speech follows visible events; choice: language, text-loss, speech-rate, and active speaker detection (ASD), a filter for people speaking on camera; tradeoff: cheaper scale but restricted to English and selected visual speech patterns.
          需求：只有当语音跟随可见事件时字幕才有用；选择：采用语言过滤、文本损失过滤、语速过滤，以及主动说话人检测（active speaker detection，ASD，一种检测画面中正在说话的人的过滤器）；权衡：能以更低成本扩大数据规模，但被限制在英语以及选定的视觉语音模式上。
          evidence:: E4, E5
    - **Implementation Surface:** The implementation is a direct adaptation of Qwen2-VL-7B-Base using PyTorch and Transformers, with larger frame and context limits for formal training than ablations. The paper reports batch size, GPU count, learning rates, inference cache policy, and latency comparisons.
      **实现边界:** 该实现是对 Qwen2-VL-7B-Base 的直接改造，使用 PyTorch 和 Transformers，正式训练时采用比消融实验更大的帧数上限和上下文长度上限。论文报告了批处理大小、GPU 数量、学习率、推理时的缓存策略，以及延迟对比。
      evidence:: E8, E11, E17
        - Pre-training ablations reduce the frame limit to 120 and visual context to 16K tokens for efficiency, so medium and long VideoMME results are intentionally not emphasized there.
          为提升效率，预训练消融实验把帧数上限降到 120，视觉上下文降到 16K 个 token，因此在那里刻意不强调 VideoMME 中等和长视频的结果。
          evidence:: E11, E12
        - Formal pre-training and SFT use a 480-frame limit and 24K visual context, with 30 to 240 second Live-CC-5M clips and Live-WhisperX-526K plus LLaVA-Video-178K for SFT.
          正式的预训练和监督微调（supervised fine-tuning，SFT）使用 480 帧上限和 24K 视觉上下文，采用时长 30 到 240 秒的 Live-CC-5M 片段，SFT 阶段还使用 Live-WhisperX-526K 加上 LLaVA-Video-178K。
          evidence:: E11
        - The reported streaming latency is 0.17 seconds for LiveCC-7B-Instruct with frame input, compared with 5.62 and 20.51 seconds for LLaVA-Video clip-captioning baselines.
          论文报告的流式延迟为：LiveCC-7B-Instruct 在使用视频帧输入时为 0.17 秒，相比之下 LLaVA-Video 的片段字幕基线分别为 5.62 秒和 20.51 秒。
          evidence:: E17
- ## Evaluation and Evidence
    - **Setup:** General QA is evaluated on VideoMME, MVBench, OVOBench, and LiveSports-3K-QA using multiple-choice logits. Commentary is evaluated as conditioned caption completion with video title and previous ASR, then pairwise judged by GPT-4o against ASR ground truth.
      **实验设置:** 通用问答在 VideoMME、MVBench、OVOBench 和 LiveSports-3K-QA 上评测，使用多项选择的 logits。解说能力则以带视频标题和前一段 ASR 文本作为条件的字幕补全任务来评测，然后由 GPT-4o 对照 ASR 真值进行成对判定。
      evidence:: E10, E11
    - **Claim-Evidence Matrix:** The evidence is strongest where the paper gives controlled ablations, and weaker where results rely on open-ended judge preference without confidence intervals.
      **主张-证据矩阵:** 在论文提供受控消融实验（controlled ablation，即每次只改变一个因素以观察其单独影响的对照实验）的地方，证据最为有力；而在结果依赖开放式评判偏好、且没有给出置信区间的地方，证据则较弱。
      claim_kind:: analyst_assessment
      evidence:: E10, E12, E13
        - C1 is supported by a direct caption-versus-streaming ablation with nearly identical VideoMME overall scores and a large commentary win-rate difference.
          C1 得到一项直接对比「字幕式」与「流式」的消融实验支持：两者在 VideoMME 上的总体得分几乎相同，但在解说（commentary）任务的胜率上差距很大。
          evidence:: E12
        - C2 is supported by a data-scale ablation where commentary improves monotonically from 1M to 10M clips while VideoMME peaks near 5M.
          C2 得到一项数据规模消融实验的支持：随着片段数量从 1M 增加到 10M，解说质量单调提升，而 VideoMME 得分在约 5M 处达到峰值。
          evidence:: E13
        - C3 and C4 are supported by SFT initialization ablations and LiveSports-3K model comparisons, but the commentary side remains tied to GPT-4o judging and ASR-style ground truth.
          C3 和 C4 得到监督微调（Supervised fine-tuning，SFT）初始化消融实验以及 LiveSports-3K 模型对比的支持，但在解说这一侧，评估仍然依赖 GPT-4o 作为评判者，以及以 ASR（自动语音识别，Automatic speech recognition）为形式的参考答案。
          evidence:: E14, E16
    - **Headline Results:** The headline result is not just better commentary: LiveCC-7B-Instruct reports better VideoMME and OVOBench scores than its Qwen2-VL-7B-Instruct starting family while also beating larger open commentary models on LiveSports-3K-CC. The strongest latency claim is that frame-wise streaming lowers response delay relative to clip-captioning models.
      **关键结果:** 最重要的结果不只是解说更好：LiveCC-7B-Instruct 在 VideoMME 和 OVOBench 上的得分都高于它的起点模型系列 Qwen2-VL-7B-Instruct，同时在 LiveSports-3K-CC 上也胜过更大的开源解说模型。在延迟方面，最有力的论断是：逐帧流式处理相比片段级字幕模型降低了响应延迟。
      evidence:: E15, E16, E17
        - General QA: LiveCC-7B-Instruct scores 64.1 on VideoMME without subtitles and 59.8 on OVOBench average, above Qwen2-VL-7B-Instruct on both reported comparisons.
          通用问答：LiveCC-7B-Instruct 在不使用字幕的 VideoMME 上得分为 64.1，在 OVOBench 平均分上为 59.8，在两项对比中都高于 Qwen2-VL-7B-Instruct。
          evidence:: E15
        - Commentary: LiveCC-7B-Instruct reaches 41.5 LiveSports-3K-CC win rate, above LLaVA-Video-72B at 35.0 and Qwen2.5-VL-72B-Instruct at 30.4.
          解说：LiveCC-7B-Instruct 在 LiveSports-3K-CC 上达到 41.5 的胜率，高于 LLaVA-Video-72B 的 35.0 和 Qwen2.5-VL-72B-Instruct 的 30.4。
          evidence:: E16
        - Latency: LiveCC-7B-Instruct reports 0.17 seconds response latency with frame input, versus LLaVA-Video-7B at 5.62 seconds and LLaVA-Video-72B at 20.51 seconds with clip input.
          延迟：LiveCC-7B-Instruct 在以帧作为输入时报告的响应延迟为 0.17 秒，而 LLaVA-Video-7B 在以片段作为输入时为 5.62 秒，LLaVA-Video-72B 为 20.51 秒。
          evidence:: E17
    - **Ablations and Sensitivity:** The ablations isolate three sensitive factors: sequence format, context source, and data scale. The most important pattern is that commentary needs streaming supervision and previous-ASR context more than it needs ordinary caption-style training.
      **消融与敏感性:** 这些消融实验分离出三个敏感因素：序列格式、上下文来源和数据规模。最重要的规律是，解说更需要的是流式监督和先前的 ASR 上下文，而不是普通的字幕式训练。
      evidence:: E12, E13, E14
        - Sequence format: streaming pre-training gives 32.9 commentary win rate versus 14.0 for caption-style training, while VideoMME overall stays about 61.
          序列格式：流式预训练带来 32.9 的解说胜率，而字幕式训练只有 14.0，同时 VideoMME 总体得分维持在约 61。
          evidence:: E12
        - Context: previous ASR gives 32.0 commentary win rate versus 14.7 with no context, while title-only context improves commentary but weakens VideoMME relative to previous ASR.
          上下文信息：使用此前的语音识别（ASR）文本作为上下文时，解说的胜率为 32.0，而不提供任何上下文时仅为 14.7；如果只用视频标题作为上下文，解说效果有所提升，但相比使用此前的 ASR 文本，在 VideoMME 上的表现变弱。
          evidence:: E13
        - Data and SFT: commentary improves as pre-training grows to 10M clips, but general QA drops past 5M, and adding Live-WhisperX-526K during SFT roughly doubles the base SFT commentary win rate.
          数据与有监督微调（Supervised fine-tuning，SFT）：当预训练规模增长到 1000 万个视频片段时，解说效果随之提升；但常规问答（QA）的表现在超过 500 万片段后开始下降。在有监督微调阶段加入 Live-WhisperX-526K 数据集，能让基础有监督微调的解说胜率大约翻倍。
          evidence:: E13, E14
    - **Reproducibility Gaps:** Reported reuse signals include a project page, dataset and model names, main hardware scale, batch size, learning rates, and judge prompt details. Not reported in the paper text are random seeds, training wall-clock, confidence intervals or repeat counts for win rates, and a full audit of GPT-4o judge reliability beyond position swapping.
      **可复现性缺口:** 可复现性方面的缺口：论文中提供的可复用信息包括项目主页、数据集与模型名称、主要硬件规模、批处理大小、学习率以及裁判模型的提示词细节。而正文中未报告的内容包括：随机种子、训练的实际耗时、胜率的置信区间或重复实验次数，以及除了位置互换检验之外、对 GPT-4o 裁判可靠性的完整审查。
      claim_kind:: analyst_assessment
      evidence:: E1, E10, E11
- ## Technical Judgment
    - **What Holds Up:** The core mechanism is well matched to the goal: frame-local word prediction is exactly the training signal needed for low-delay commentary, and the caption-versus-streaming ablation directly tests that choice. The paper also shows that the approach does not merely overfit a new benchmark, because it improves or stays competitive on several external QA benchmarks.
      **站得住的结论:** 站得住脚的部分：核心机制与目标高度匹配——以帧为局部单位来预测词语，正是实现低延迟解说所需要的训练信号，而「字幕对比流式」的消融实验直接检验了这一选择。论文还表明该方法并非只是过拟合到一个新的评测基准上，因为它在多个外部问答基准上都有所提升或保持了竞争力。
      claim_kind:: analyst_assessment
      evidence:: E3, E12, E15, E17
    - **Where It May Fail:** Benefits are most plausible when spoken captions are visually grounded, English, and temporally aligned; talking-head, off-screen narration, noisy captions, or domains without useful speech break the supervision assumption. Commentary quality may also be overestimated when the judge rewards ASR-like style rather than independently verified visual correctness.
      **可能失效之处:** 可能失效的场景：当口语字幕与画面内容有视觉对应关系、为英语、且在时间上对齐时，该方法带来的收益最为可信；而在只有人物讲话镜头（talking-head）、画外旁白、字幕噪声较大、或缺乏有用语音的领域中，其监督信号所依赖的前提就会被打破。此外，如果裁判模型奖励的是类似 ASR 的表达风格，而不是经过独立验证的视觉正确性，解说质量还可能被高估。
      claim_kind:: analyst_assessment
      evidence:: E4, E5, E10, E13
    - **Relation to Other Work:** Against Vid2Seq-style video-ASR pre-training, the technical shift is from predicting a timestamped paragraph for an event to predicting short incomplete word bursts causally after frame intervals. Against streaming Video LLM systems trained from manual or GPT-crafted conversations, LiveCC trades annotation richness for web-scale weak supervision and a commentary-specific benchmark.
      **与已有工作的关系:** 与其他工作的关系：相比 Vid2Seq 那类「视频加语音识别」的预训练方法，本文的技术转变在于：从「为某个事件预测一段带时间戳的文字」转向「在每个帧区间之后，因果地预测简短、不完整的词语片段」。相比那些用人工或 GPT 构造的对话训练出来的流式视频大语言模型系统，LiveCC 放弃了标注的丰富程度，换来了网络规模的弱监督数据以及一个专门面向解说的评测基准。
      evidence:: E2, E3
    - **Transferable Lesson:** A reusable systems pattern is to preserve the natural timing of weak labels instead of collapsing them into global labels: the timestamp can be as important as the text content when the deployment interface is streaming. This suggests looking for cheap, naturally aligned supervision before paying for synthetic instruction data.
      **可迁移启发:** 可迁移的经验：一种可复用的系统设计模式是保留弱标签本身的自然时序，而不是把它们压缩成全局标签——当部署接口是流式的时候，时间戳可能和文字内容同等重要。这也提示我们：在花代价去构造合成指令数据之前，应该先去寻找那些成本低廉、天然对齐的监督信号。
      claim_kind:: analyst_assessment
      evidence:: E2, E3, E6
- ## Glossary
  collapsed:: true
    - Video large language model: A language model that answers or generates text while conditioning on video frames; in this note it is the model family LiveCC belongs to.
      视频大语言模型（Video large language model，Video LLM）：一种在生成或回答文本时以视频帧为条件的语言模型；在本笔记中，它指的是 LiveCC 所属的模型家族。
    - Automatic speech recognition: Machine-produced or platform-provided speech-to-text from video audio; LiveCC uses it as cheap supervision.
      自动语音识别（Automatic speech recognition，ASR）：由机器生成或由平台提供的、从视频音频转写而来的语音转文字内容；LiveCC 把它当作成本低廉的监督信号使用。
    - Streaming video understanding: A setting where the model must respond as frames arrive, without seeing the full future clip.
      流式视频理解（Streaming video understanding）：指模型必须随着视频帧的到来即时作出响应，而无法看到尚未到来的完整视频片段的一种任务设定。
    - Dense interleaving sequence: The LiveCC training format that alternates frame tokens and the ASR words assigned to the same time interval.
      密集交错序列（Dense interleaving sequence）：LiveCC 采用的一种训练格式，把帧的 token 与分配到同一时间区间的 ASR 词语交替排列。
    - Visual tokens: Compact frame representations produced by the vision encoder and consumed by the language model as conditioning input.
      视觉 token（Visual tokens）：由视觉编码器生成的紧凑帧表示，语言模型把它们作为条件输入来使用。
    - Supervised fine-tuning: The post-pretraining stage that adapts the base model with curated prompt-response or task data.
      监督微调（Supervised fine-tuning）：预训练之后的一个阶段，用经过筛选的「提示—回复」数据或任务数据来适配基础模型。
    - Key-Value cache: Saved transformer attention state from previous tokens; reusing it avoids recomputing the entire history during streaming decoding.
      键值缓存（Key-Value cache）：保存下来的 Transformer 注意力状态，来自先前的 token；在流式解码时复用它可以避免重新计算整段历史。
    - LLM-as-a-judge: An evaluation method where a language model compares two generated commentaries against a reference and chooses the better one.
      以大语言模型作为评判者（LLM-as-a-judge）：一种评估方法，让语言模型把两段生成的解说词与一份参考文本作比较，并挑出更好的一段。
    - Active speaker detection: A video analysis filter that detects people speaking on camera; LiveCC uses it to remove talking-head clips that are weakly visually grounded.
      活跃说话人检测（Active speaker detection）：一种视频分析过滤手段，用于检测画面中正在说话的人；LiveCC 用它来剔除那些与画面关联很弱的「口播人头」片段。
    - End-of-sequence indicator: A token that marks no more words for a frame interval; LiveCC uses an ellipsis for silent frames and pauses.
      序列结束标记（End-of-sequence indicator）：一种 token，表示某个帧区间不再有更多词语；LiveCC 用省略号来标记静音帧和停顿。
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/metadata | Title and Abstract | high
      locator:: title block, abstract
      quote:: Live CC: Learning Video LLM with Streaming Speech Transcription at Scale. Joya Chen, Ziyun Zeng, Yiqi Lin, Wei Li, Zejun Ma, Mike Zheng Shou. All resources of this paper have been released at showlab.github.io/livecc.
    - **E2:** gap/paper_statement | Introduction and Related Work | high
      locator:: Section 1; Section 2 Training Video LLMs
      quote:: Previous studies on streaming video LLMs either rely on LLMs to generate hallucinated streaming conversations from video annotations, or fine-tune on small-scale dense caption datasets. Prior works explored large-scale video-ASR learning but typically treat ASR transcriptions as global video captions.
    - **E3:** method/paper_statement | Abstract and Methodology | high
      locator:: abstract; Section 3.2 Modeling
      quote:: We propose a novel streaming training approach that densely interleaves the ASR words and video frames according to their timestamps. The model is trained to generate frame assigned ASR words in an autoregressive manner.
    - **E4:** system_design/implementation_detail | Video-ASR Data Curation | high
      locator:: Section 3.1
      quote:: This pipeline enables the construction of the Live-CC-5M pretraining set and the Live-WhisperX-526K SFT set. The SFT dataset comprises 526K video clips, each paired with word-level timestamped ASR transcripts and a user prompt.
    - **E5:** experiment_setup/implementation_detail | Video-ASR Data Curation | high
      locator:: Section 3.1, YT-CC-Source-5.7M
      quote:: We aggregate HD-VILA, YT-Temporal-1B, VidChapters, and HowTo100M as our video sources. Applying these filtering criteria results in a curated set of 10.7 million YouTube video IDs. Applying language and caption-density filters, we download these 5.7 million videos with English CC.
    - **E6:** algorithm/implementation_detail | Modeling | high
      locator:: Section 3.2, Training with Dense Interleaving Sequence
      quote:: The training sequence is formatted as [Con] followed by alternating frame spans and word spans. [Con] denotes context information of the video, F denotes a frame, W denotes the words, and by default the method uses 2 FPS frame rate and k = 1 as the time interval.
    - **E7:** implementation/implementation_detail | Modeling | high
      locator:: Section 3.2, Sequence Pre-processing
      quote:: For pre-training, the original YouTube ASR transcripts use fixed timestamps, so the authors uniformly distribute each segment's duration across its constituent words. During SFT, WhisperX provides precise word-level timestamps. Silent frames directly predict the ellipsis token.
    - **E8:** implementation/implementation_detail | Modeling | high
      locator:: Section 3.2, Inference
      quote:: During inference, LiveCC processes input frames sequentially. To accelerate language decoding, it caches the Key-Value pairs of previous prompts, visual frames, and generated text. For long sequences, it discards visual tokens every 240 seconds while retaining text tokens.
    - **E9:** experiment_setup/paper_statement | The LiveSports-3K Benchmark | high
      locator:: Section 4.1
      quote:: The benchmark spans a broader range of common sports. The authors selected the top 50 sports categories, sampled candidate videos, filtered visually grounded events, curated 416 videos across 49 sports categories, and removed these videos from the training dataset.
    - **E10:** experiment_setup/paper_statement | Crafting LiveSports-3K-CC/QA and Experiments Setup | high
      locator:: Sections 4.2 and 5.1
      quote:: LiveSports-3K-CC consists of 1,702 events with high-quality live CCs. LiveSports-3K-QA contains 1,174 multiple-choice questions after removing speech-recognition questions. Commentary is evaluated by pairwise GPT-4o judging for semantic alignment and stylistic consistency.
    - **E11:** experiment_setup/implementation_detail | Experiments Setup | high
      locator:: Section 5.1
      quote:: The model initializes from Qwen2-VL-7B-Base. Formal pre-training uses 30 to 240 second Live-CC-5M, and SFT uses Live-Whisper-526K plus LLaVA-Video-178K. The batch size is 512 on 128 GPUs, with learning rates 2e-5 and 1e-5.
    - **E12:** ablation/ablation | Ablation Study | medium
      locator:: Table 1a and Section 5.2
      quote:: Caption-style pre-training on 5M gives LiveSports-3K-CC win rate 14.0 and Video-MME overall 61.1. Streaming-style pre-training on 5M gives win rate 32.9 and Video-MME overall 61.0, indicating a large commentary gain with similar QA.
    - **E13:** ablation/ablation | Ablation Study | medium
      locator:: Table 1b, Table 1c, Section 5.2
      quote:: Previous ASR context improves LiveSports-3K-CC win rate to 32.0, versus 14.7 with no context. Scaling data from 1M to 10M improves commentary win rate from 29.1 to 36.0, while Video-MME overall falls from 61.0 at 5M to 58.0 at 10M.
    - **E14:** ablation/ablation | Ablation Study | medium
      locator:: Table 2
      quote:: Adding Live-WhisperX-526K to LLaVA-Video-178K during SFT improves the Qwen2-VL-7B-Base row's LiveSports-3K-CC win rate from 16.7 to 33.7. Starting from LiveCC-7B-Base and SFT data gives 41.5 on commentary.
    - **E15:** result/experiment_result | Overall Results | medium
      locator:: Table 3 and Section 5.3
      quote:: LiveCC-7B-Instruct scores 64.1 on VideoMME without subtitles and 70.3 with subtitles, compared with Qwen2-VL-7B-Instruct at 63.3 and 69.0. It scores 59.8 on OVOBench average, above LLaVA-Video-7B at 52.9.
    - **E16:** result/experiment_result | Overall Results | medium
      locator:: Table 4
      quote:: On LiveSports-3K-CC, LiveCC-7B-Instruct reaches 41.5 win rate and LiveCC-7B-Base reaches 43.2. LLaVA-Video-72B reaches 35.0, Qwen2.5-VL-72B-Instruct reaches 30.4, and Qwen2-VL-7B-Instruct reaches 9.3.
    - **E17:** result/experiment_result | Additional Experiments | medium
      locator:: Table 5, Section 9.1
      quote:: Response latency is defined as the time a user waits to see the model's output. LLaVA-Video-72B has 20.51 seconds latency, LLaVA-Video-7B has 5.62 seconds, and LiveCC-7B-Instruct has 0.17 seconds with frame input and streaming inference.
