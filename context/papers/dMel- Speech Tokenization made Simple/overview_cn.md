- **标题:** dMel：让语音分词（speech tokenization）变得简单
- **一句话总结:** dMel 表明，直接对对数梅尔频谱图（log-mel spectrogram）的能量值进行分箱，就能为解码器型 Transformer（decoder-only transformer）的自动语音识别（automatic speech recognition，ASR）和文本转语音（text-to-speech，TTS）提供一种简单且无需训练的语音分词接口。这减少了对学习型语音编解码器和针对特定任务的标记堆叠的依赖。
- **论文类型:** 系统
- **发表:** arXiv 预印本 2024 年，第 3 版 2025 年 5 月
- **作者:** Richard He Bai, Zijin Gu, Tatiana Likhomanenko, Zakaria Aldeneh, Ruixiang Zhang, Navdeep Jaitly；Apple
- **关键词:** 语音分词，对数梅尔频谱图，文本转语音，自动语音识别，解码器型 Transformer，语音-文本建模
- ## Orientation
    - **背景:** 语音系统通常在模型处理声音之前，先将其转换为紧凑的序列。对数梅尔频谱图是一幅表示语音能量的时间-频率图像，而语音词元是一种离散符号，旨在使语言模型风格的预测器能够使用这幅图像。
      claim_kind:: analyst_assessment
    - **通俗问题:** 如果我们希望一个模型既能听又能说，就需要一种表示方法。这种方法要能同时保留词语、说话人声音特征和声音质量，而不需要仅仅为了生成词元而额外依赖一个脆弱的模型。
      claim_kind:: analyst_assessment
    - **为何困难:** 保留语义的表示方法往往会丢失声学细节。而能很好重构声音的表示方法对于简单的下一词元预测建模来说可能难以处理。
      claim_kind:: analyst_assessment
    - **一句话核心思路:** 关键思路是：不学习语音编码，而是将每个对数梅尔能量值舍入到一个有序的小区间中，并直接对这些舍入后的频谱图帧进行建模。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **阅读价值:** 阅读本文时，请将其视为一篇挑战现有假设的语音分词论文。现有假设认为，语言模型风格的语音系统在对语音进行建模之前，需要先获取学习型语义标记（semantic token）或神经编解码器标记（acoustic token）。
      claim_kind:: analyst_assessment
      evidence:: E1, E2
    - **一句话贡献:** dMel 通过用直接离散化对数梅尔频谱图能量值的方法替代学习型语音分词器，改进了语言模型风格的语音识别与合成。
      evidence:: E1, E2
    - **记忆模型:** 把语音看作随时间和音高变化的热力图：dMel 将每个单元格的亮度舍入到少量离散级别，然后让一个类似文本的「下一标记」模型来预测未来的热力图列。
      claim_kind:: analyst_assessment
    - **最佳证据:** 最有力的证据是一项受控对比实验：在相同的解码器型 Transformer 模型上使用不同的语音分词器进行训练，dMel 在 TTS 语音可懂度和 ASR 的词错误率（word error rate，WER）两项指标上均胜出。
      evidence:: E7, E9
        - 支持主张 C2：在 LibriSpeech 960h 数据集上进行 RichTTS Base 实验。HuBERT+KM 和 SpeechTokenizer 在同一个语言模型风格的模型内，并结合先前的 VOX-TLM/USLM。词错率（WER）和字错率（CER）越低越好。dMel 报告的 WER 为 4.3、CER 为 1.8，而 HuBERT+KM 为 9.5/4.3，SpeechTokenizer 为 11.4/5.9。该主张得到支持，但需注意自动语音识别（ASR）评估的局限性。
          evidence:: E7
        - 支持主张 C3：在 LibriSpeech 960h 数据集上进行 RichASR Base 实验。使用与 SpeechTokenizer 和 HuBERT+KM 相同的 258M 参数量架构。WER 越低越好。dMel 报告在 test-clean 测试集上的 WER 为 4.2、在 test-other 测试集上为 10.4，而 HuBERT+KM 为 5.8/13.8，SpeechTokenizer 为 6.9/17.5。该主张得到支持，并附有两次运行的标准差。
          evidence:: E9
        - 支持主张 C1：在 300 个 LibriSpeech test-clean 样本上进行重构实验。基线模型包括神经分词器和梅尔声码器。评估指标为 WER、客观听力质量估计（MOS-LQO）和平均主观意见分（MOS）。dMel-HifiGAN 的表现接近 Mel-HifiGAN，并且可与声学编解码器竞争，同时不需要语音到单元的编码器。该主张得到支持，但样本量较小。
          evidence:: E5
    - **主要边界:** 该论文主要在英语语音基准测试上展示了 ASR 和文本转语音（TTS）的效果。但该论文未确立通用的音频建模、复杂的语音理解，也未确立大规模预训练多模态大语言模型的行为表现。
      claim_kind:: analyst_assessment
      evidence:: E14
- ## Argument Map
    - **问题与重要性:** 该论文致力于语言模型风格的自动语音识别（ASR，语音转文本）和文本转语音（TTS，文本转语音）系统的语音词元化。学习型分词器增加了复杂性、成本和领域敏感性，而统一的语音-文本建模需要能够同时保留内容和声学特征的词元。
      evidence:: E1, E2
    - **已有方法缺口:** 先前的语音分词器分为两类。一类是从自监督语音编码器中获取的语义词元，它保留了内容但丢失了声学细节。另一类是从神经音频压缩中获取的声学词元，它能重构声音，但通常需要残差向量量化（RVQ，一种通过堆叠码本对连续重构误差进行编码的方法）和专门的分层模型。
      evidence:: E2
    - **关键洞见:** 该论文的核心主张是：对数梅尔频谱图（log-mel spectrogram，一种时间-频率表示，其频率轴按感知梅尔尺度排列、幅度取对数）已经包含了足够的内容与声学信息，因此标量量化（把每个连续值四舍五入到最近的离散区间）就能将其变为类似词元（token）的离散表示，而无需训练一个分词器。
      evidence:: E1, E3
    - **核心主张:** 论文提出了四条可证伪的主张，分别涉及 dMel 作为分词器以及作为仅解码器（decoder-only）模型接口时的表现。
      evidence:: E5, E7, E9, E12
        - C1：将对数梅尔频谱图离散化为 dMel，保留了足以重建波形的声学信息，并且在含噪的分布外重建任务中，比若干学习型分词器更鲁棒。
          evidence:: E5, E6
        - C2：在语言模型式文本转语音（text-to-speech，TTS）设定下，在论文给出的可比仅解码器训练框架中，dMel 生成的语音比 HuBERT-KM 或 SpeechTokenizer 更易听懂。
          evidence:: E7, E8
        - C3：在语言模型式语音转文本（automatic speech recognition，ASR）设定下，以同一架构的词错误率（word error rate，WER）衡量，dMel 比所比较的语音分词器更好地保留了语义内容。
          evidence:: E9, E10
        - C4：dMel 的逐通道独立性使模型能够并行预测多个通道与相邻帧，在提高效率的同时不会出现残差向量量化（residual vector quantization，RVQ，一种多码本量化方法，后续码本编码先前码本剩余的重建误差）分词器那样的残差码依赖问题。
          evidence:: E4, E12
- ## Mechanism and Design
    - **核心机制:** dMel 先计算对数梅尔频谱图，再基于整个数据集的最小与最大能量值构建一个共享的标量码本，并将每个时频单元替换为最近的区间索引；反分词过程通过码本将索引映射回能量值，再由一个单独训练的梅尔声码器（vocoder，将梅尔频谱图转换为波形的模型）生成波形。
      evidence:: E3, E4
    - **数据/控制流:** 对于语音输入，每一帧包含多个频率通道的区间编号；每个区间被转为嵌入向量，各通道嵌入拼接后经线性投影映射到 Transformer 的隐藏维度，由仅解码器 Transformer 酒预测后续文本词元用于 ASR，或预测后续 dMel 语音词元用于 TTS。
      evidence:: E4
        - 对于 TTS，输入序列依次拼接说话人嵌入、字符级文本词元和语音词元，损失只施加在语音词元输出上，而不施加于文本前缀上。
          evidence:: E13
        - 对于 ASR，输入序列依次拼接语音词元和字符级文本词元，损失只施加在文本词元输出上，而不施加于语音前缀上。
          evidence:: E13
    - **设计决策:** 设计反复选择简单、共享且可并行的表示方式，而非学习型压缩结构；它接受更高的比特率，以换取分词器的简洁性和更简便的解码器专用建模。
      claim_kind:: analyst_assessment
      evidence:: E4, E11, E12
        - 需求：将连续的梅尔值离散化；选择：在 80 个通道上使用 16 个共享的有序量化区间；备选方案：更大或更小的码本；权衡：8 个区间会丢失过多信息，而 32 个区间对某些 ASR 场景有帮助，但在论文设定的场景下会损害 TTS 效果。
          evidence:: E4, E11
        - 需求：避免残差编码通道之间的序列依赖；选择：独立且并行地预测 dMel 频率通道；备选方案：残差向量量化（RVQ）风格的残差通道；权衡：dMel 含有更多原始比特，但避免了下游模型中的残差层级结构。
          evidence:: E4, E12
        - 需求：减少局部冗余音频帧的复制以及暴露偏差（exposure bias，即模型在训练时只见到自身之前的正确输出、推理时却要面对自身可能出错的输出所产生的不匹配）；选择：在训练期间对语音上下文进行跨度掩码；权衡：这引入了一个训练启发式方法，其收益有实验报告支持但缺乏理论分析。
          evidence:: E13
    - **实现边界:** 实现层面包括：一个确定性分词器、一个位于 Transformer 之外的梅尔声码器（即将梅尔频谱图等声学特征转换回波形音频的模型）、字符级文本标记、用于 TTS 的 d-vector 说话人嵌入、RoPE 相对位置编码，以及 Small/Base/Large 三种解码器专用 Transformer 配置。
      evidence:: E4, E13
        - 报告的训练使用了 Adam 优化器、混合精度 BF16、A100/H100 80GB GPU、8 块 GPU、80k 步 ASR 训练、100k 步 TTS 训练；ASR 训练耗时不到一天，而 TTS 训练耗时 2 到 4 天。
          evidence:: E13
- ## Evaluation and Evidence
    - **实验设置:** 评估包含重建测试、解码器专用 TTS、解码器专用 ASR、消融实验以及一个初步的 ASR+TTS 联合模型；数据主要来自 LibriSpeech，并额外使用 LibriTTS、VCTK 和 LJSpeech 三个 TTS 数据集；评估指标包括词错误率（WER，越低越好）、字符错误率（CER）、客观的 MOS-LQO 以及人工平均意见分（MOS）。
      evidence:: E5, E7, E9, E13
    - **主张-证据矩阵:** 证据在以下情况最为有力：在共享模型架构下改变分词器进行对比；而在以下情况则较弱：对比跨越了不同的模型系列、数据集或评估协议。
      claim_kind:: analyst_assessment
      evidence:: E5, E7, E9, E10
        - C1 的支持证据来自干净的 LibriSpeech 上的重建 WER/MOS-LQO/MOS 以及一个含噪重建压力测试；但干净重建样本仅有 300 条语音，且含噪结果依赖于自动 ASR 的 WER。
          claim_kind:: analyst_assessment
          evidence:: E5, E6
        - C2 和 C3 的支持证据来自在相同架构下与 HuBERT-KM 和 SpeechTokenizer 的对比；与 VOX-TLM、USLM、Tacotron2、FastSpeech2 和 VITS 的外部对比提供了有用参考，但控制程度较低。
          claim_kind:: analyst_assessment
          evidence:: E7, E8, E9, E10
        - C4 由 k 帧消融实验支持，这些实验在理论浮点运算量与词错误率之间权衡，但论文报告的是理论推理时间，而非完整的端到端服务挂钟时间测量。
          claim_kind:: analyst_assessment
          evidence:: E12
    - **关键结果:** 主要结论是：在相同的语言模型式架构下，dMel 几乎完整保留了重建质量，相比所测试的其他分词器大幅提升了文本转语音可懂度，并在相同的 Base 架构中相比 HuBERT-KM 和 SpeechTokenizer 降低了语音识别词错误率。
      evidence:: E5, E7, E9
        - C1：在 300 个 LibriSpeech test-clean 样本上，dMel-HifiGAN 报告词错误率 2.11、MOS-LQO 4.47，而 Mel-HifiGAN 报告词错误率 2.08、MOS-LQO 4.52，表明在此声码器下离散化损失较小。
          evidence:: E5
        - C2：在 LibriSpeech 960h 上训练的 RichTTS(dMel) 报告词错误率 4.3、字符错误率 1.8，而 RichTTS(HuBERT+KM) 报告 9.5/4.3，RichTTS(SpeechTokenizer) 报告 11.4/5.9。
          evidence:: E7
        - C3：RichASR(dMel) Base 在 test-clean/test-other 上报告词错误率 4.2 ±0.2 和 10.4 ±0.1，而 HuBERT+KM 为 5.8 ±0.1 和 13.8 ±0.1，SpeechTokenizer 为 6.9 ±0.4 和 17.5 ±0.5。
          evidence:: E9
    - **消融与敏感性:** 消融实验发现，区间数、帧聚合、语音识别架构选择以及数据增强与掩码策略是重要的敏感度维度，而非将 dMel 视为普适可直接替换的方案。
      evidence:: E11, E12, E13
        - 论文选择 16 个区间作为整体最佳折中；8 个区间丢失信息过多，32 个区间表现不一，略微改善语音识别 test-other 但降低文本转语音质量。
          evidence:: E11
        - k 帧并行解码在适度聚合时效果最佳：论文报告 k ≤ 4 时结果相近且理论效率提升，而过度激进的聚合会增加词错误率。
          evidence:: E12
        - 语音识别消融实验指出，相比于连续梅尔特征，离散化本身仅造成较小的性能下降，剩余差距的很大一部分来自切换到语言模型式的仅解码器语音识别模型。
          evidence:: E10
    - **可复现性缺口:** 论文报告了公开代码链接和详细训练设置，但声明不会发布预训练模型，并称代码计划在论文被接收后发布；缺乏已发布的检查点限制了精确复现与复用。
      evidence:: E13, E14
- ## Technical Judgment
    - **站得住的结论:** 核心技术观点依然成立：如果任务是在语音上进行语音识别（ASR）或语音合成（TTS），直接使用标量量化的梅尔频谱特征就是一个出人意料的强大基线。它消除了对大型学习型分词器的依赖，而以往系统通常将这种分词器视为必要组件。
      claim_kind:: analyst_assessment
      evidence:: E3, E5, E7, E9
    - **可能失效之处:** 其优势可能会减弱。具体情形包括：目标是紧凑音频压缩、非语音音频或复杂的语音理解；预训练面向高度多语言或恶劣领域；或者，需要生产级 TTS 质量，且要求超出本文报告的可懂度与自然度评分的韵律和风格控制。
      claim_kind:: analyst_assessment
      evidence:: E14
    - **与已有工作的关系:** 与 HuBERT-KM 的语义词元相比，dMel 保留了更多声学细节。与 EnCodec/SpeechTokenizer 风格的神经编解码器（neural codec）相比，它避免了残差向量量化（RVQ）的残差结构与分词器训练。与 AudioLM/VOX-TLM/VioLA 风格的统一建模相比，它将复杂性转移出分词阶段，而不是增加处理阶段或特定于模态的层级。
      claim_kind:: analyst_assessment
      evidence:: E2, E4, E10
    - **可迁移启发:** 在设计学习型离散表示之前，应测试基于物理的连续表示加上简单的标量量化是否能保留与任务相关的信息。即使这种做法在比特率上不是最优的，更简单的词元边界也能使下游建模和故障分析变得更容易。
      claim_kind:: analyst_assessment
- ## Glossary
  collapsed:: true
    - 对数梅尔频谱图（log-mel spectrogram）：一种表示音频能量的时频表征，其频带遵循感知梅尔尺度，且振幅经过对数变换。它是 dMel 进行离散化的连续表示。
    - 语音分词（speech tokenization）：将连续的语音波形或频谱图转换为离散符号的过程，这些符号可以像文本词元一样进行建模。
    - dMel：本文提出的分词器。它将每个对数梅尔频谱图单元舍入到少量共享强度分箱之一，从而生成一个离散时频词元 ID 的矩阵。
    - 声码器（vocoder）：一种将梅尔频谱图等声学特征转换回音频波形的模型。在本文中，它独立训练，且位于 transformer 之外。
    - 语义词元（semantic token）：一种离散语音单元，通常通过聚类自监督语音模型的隐藏状态获得。相较于精细的声学细节，它倾向于更好地保留语言内容。
    - 声学词元（acoustic token）：由音频压缩模型生成的离散词元，旨在保留足够的低级声学信息以重建波形。
    - 残差向量量化（residual vector quantization，RVQ）：一种多码本量化方法，其中后续的每个码本对前面码本留下的重建误差进行编码；这种方法在神经音频编解码器中很常见，但会产生有序的残差通道。
    - 纯解码器 Transformer（decoder-only transformer）：一种使用因果掩码根据前面的词元预测下一个词元的 Transformer 架构，类似于 GPT 风格的语言模型。
    - 自动语音识别与文本到语音（ASR and TTS）：ASR将语音映射为文本；TTS将文本映射为语音。论文使用这两个任务来测试dMel是否保留了语义内容和声学可重建性。
    - 词错误率、字符错误率与平均意见分（WER, CER, and MOS）：WER和CER衡量转录错误，值越低越好；MOS是人类给出的自然度评分，MOS-LQO是客观的听觉质量估计，这两者都是值越高越好。
- ## Evidence Index
  collapsed:: true
    - **E1:** method/paper_statement | Abstract | medium
      locator:: Abstract
      quote:: we introduce a novel speech representation (dMel) that discretizes mel-filterbank channels into intensity bins, creating a simpler yet more effective representation compared to existing speech tokenization methods.
    - **E2:** insight/paper_statement | Introduction | medium
      locator:: Section 1, motivation and advantages
      quote:: By operating on the log mel-filterbanks and preserving the frequency and intensity information (with some loss of resolution from discretization), dMel inherently preserves both semantic and acoustic information in a unified representation, without the need for separate tokenization or additional pretraining of a tokenization model.
    - **E3:** algorithm/implementation_detail | Method | high
      locator:: Section 2.1, Tokenization
      quote:: In practice, we compute the minimum m and maximum M values of log mel-filterbanks across the entire dataset to define the codebook C. Then we map a magnitude M_t,i of every frequency channel i = 1 ... N for the time frame t = 1 ... T into a bin index of the codebook C
    - **E4:** system_design/paper_statement | Method | high
      locator:: Table 2 and Section 2.1 comparison
      quote:: For dMel we use N = 80 log-mel-filterbanks (50ms window, 25ms hop distance), and 2^K = 16 values of the codebook C... dMel has a much smaller vocabulary, as it is discretized mel-filterbanks energies, allowing all 80 channels to share the same vocabulary
    - **E5:** result/experiment_result | Experiments | medium
      locator:: Table 3 and Section 3.1
      quote:: Speech reconstruction results on 300 random samples from LibriSpeech test-clean set... dMel-HifiGAN ... WER 2.11 ... MOS-LQO 4.47 ... MOS 3.68 ±0.13... By comparing Mel and dMel, we can see that discretization has little impact on WER and MOS-LQO scores.
    - **E6:** result/experiment_result | Experiments | medium
      locator:: Figure 4 and Section 3.2
      quote:: Results are shown in Figure 4: both HuBERT-KM and SpeechTokenizer fail in out-of-domain setting while EnCodec, Mel and dMel show robustness for noisy speech reconstruction. This supports our motivation to explore dMel, training-free and deterministic tokenization
    - **E7:** result/experiment_result | Experiments | medium
      locator:: Table 4 and Section 3.3.2
      quote:: our LM-style model with dMel tokenization achieves a WER of 4.3 and a CER of 1.8, significantly outperforming the baseline methods. This indicates that our model can generate more accurate speech with less hallucination and distortion.
    - **E8:** result/experiment_result | Experiments | medium
      locator:: Table 5, Table 6, Section 3.3.2
      quote:: RichTTS achieves competitive performance on the TTS task in terms of both MOS and WER... Table 6 shows the WER results... our model achieves competitive performance across different text lengths, demonstrating its robustness and generalization ability
    - **E9:** result/experiment_result | Experiments | medium
      locator:: Table 7 and Section 3.4
      quote:: Our LM-style model with dMel speech tokenization achieves 4.2% WER on the test-clean and 10.4% WER on the test-other sets outperforming both HuBERT-KM and SpeechTokenizer.
    - **E10:** result/experiment_result | Experiments | medium
      locator:: Table 8 and Section 3.4
      quote:: RichASR with dMel outperforms VOX-TLM; it also outperforms [11] on clean sets and a bit behind it on other sets.
    - **E11:** ablation/ablation | Ablations | medium
      locator:: Section 3.5 and Figure 5
      quote:: The 16-bin configuration used in the paper demonstrates the best overall performance across tasks. While the 32-bin setup slightly outperforms on the ASR test-other set, it shows degraded performance in TTS... And 8-bin configuration looses too much information with discretization.
    - **E12:** ablation/ablation | Ablations | medium
      locator:: Section 3.5 and Figure 6
      quote:: As we can see from this figure, k ≤ 4 yield similar results to single-frame model, while improves both the training and inference efficiency significantly. In contrast, for SpeechTokenizer, even K = 1 is worse than dMel with k = 6.
    - **E13:** experiment_setup/implementation_detail | Appendix E | high
      locator:: Appendix E.2, Training Details
      quote:: We train TTS models for 100k steps and ASR models 80k steps with mixed precision training and BF16 on A100 and H100 GPUs with 80GB. Both ASR models and TTS models are trained with 8GPUs
    - **E14:** limitation/limitation | Limitations and Reproducibility | high
      locator:: Appendix B and C
      quote:: we did not train on larger model sizes (>1B parameters), larger datasets (>1k hours), or using pretrained models... While dMel may potentially support non-speech tasks, our current exploration and verification focus solely on speech, not general audio... We do not plan to open-source any pre-trained models
