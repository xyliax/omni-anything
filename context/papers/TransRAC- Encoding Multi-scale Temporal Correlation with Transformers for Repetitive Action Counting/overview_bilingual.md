- **Title:** TransRAC: Encoding Multi-scale Temporal Correlation with Transformers for Repetitive Action Counting
  **标题:** TransRAC：用 Transformer 编码多尺度时间相关性以实现重复动作计数
- **Summary:** TransRAC reframes repetitive action counting for longer, irregular videos by pairing a fine-grained benchmark with multi-scale self-comparison over video features and density-map period prediction.
  **一句话总结:** TransRAC 重新定义了针对更长、更不规则视频的重复动作计数任务：它把一个细粒度基准数据集，与在视频特征上进行的多尺度自我比较，以及基于密度图（density map）的周期预测结合起来。
- **Paper Type:** application
  **论文类型:** 应用
- **Venue:** arXiv preprint 2022
  **发表:** arXiv 预印本 2022
- **Authors:** Huazhang Hu, Sixun Dong, Yiqun Zhao, Dongze Lian, Zhengxin Li, Shenghua Gao; ShanghaiTech University; National University of Singapore; Shanghai Engineering Research Center of Intelligent Vision and Imaging; Shanghai Engineering Research Center of Energy Efficient and Custom AI IC
  **作者:** Huazhang Hu、Sixun Dong、Yiqun Zhao、Dongze Lian、Zhengxin Li、Shenghua Gao；上海科技大学；新加坡国立大学；上海市智能视觉成像工程技术研究中心；上海市低功耗定制人工智能集成电路工程技术研究中心
- **Keywords:** repetitive action counting, temporal correlation, self-attention, multi-scale video representation, density map regression, fine-grained annotation, RepCount, video understanding
  **关键词:** 重复动作计数、时间相关性、自注意力、多尺度视频表示、密度图回归、细粒度标注、RepCount、视频理解
- ## Orientation
    - **Background:** Repetitive action counting asks a vision model to watch a video and estimate how many cycles of the same human movement occur. A cycle is a complete repeat of the motion, and temporal correlation means comparing moments in time to find that repeating rhythm.
      **背景:** 重复动作计数（repetitive action counting，RAC）要求视觉模型观看一段视频，估计同一种人体动作出现了多少个周期。一个周期是该动作的一次完整重复，而时间相关性（temporal correlation）指的是比较视频里不同时刻的画面，从而找出这种重复出现的节律。
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A workout video does not always look like a metronome. People pause, slow down, speed up, and drift in and out of clean motion, so the model must count repeats rather than just recognize the activity.
      **通俗问题:** 健身视频并不总像节拍器那样规律。人们会停顿、放慢、加速，动作也会时而清晰时而含糊，所以模型必须真正数出重复的次数，而不能只是识别出这是什么活动。
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** Short clips can hide this difficulty because a fixed sampling pattern often catches enough of the movement. Longer, messier clips make fast actions easy to miss and slow actions wasteful to sample densely.
      **为何困难:** 短片段可能掩盖这一难点，因为固定的采样方式往往就能捕捉到足够多的动作。而更长、更杂乱的片段会让快动作容易被漏掉，同时又让慢动作在密集采样时造成浪费。
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Compare the video with itself at several temporal scales, then predict where cycles occur over time and sum that signal into a count.
      **一句话核心思路:** 核心思路一句话：在多个时间尺度上把视频与自身作比较，然后预测各个周期在时间上出现的位置，再把这一信号累加起来得到计数。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a video-understanding paper about class-agnostic repetitive action counting, meaning counting repeated movement without assuming a fixed action category: it targets the gap between short, clean benchmark clips and longer human videos with pauses, speed changes, and only coarse count labels.
      **阅读价值:** 把这篇论文当作一篇关于「类别无关重复动作计数」的视频理解论文来读。所谓类别无关，是指在不预设固定动作类别的前提下，统计视频中重复出现的动作次数。它瞄准的痛点是：现有基准里的视频片段既短又干净，而真实的人类视频则更长，还夹杂着停顿、速度变化，并且只有粗略的计数标签。
      claim_kind:: analyst_assessment
      evidence:: E2, E3
    - **One-Sentence Contribution:** TransRAC improves repetitive action counting in realistic long videos by turning repeated motion into a time-localized density signal derived from multi-scale self-comparison of the video.
      **一句话贡献:** TransRAC 通过对视频进行多尺度自我比较，把重复动作转化为一个在时间上定位的密度信号，从而提升了在真实长视频中的重复动作计数效果。
      evidence:: E6, E9
    - **Mental Model:** Imagine watching the same exercise video through several differently paced rulers, marking where the motion lines up with itself, then adding the marks to get the final count.
      **记忆模型:** 可以想象你用几把节奏各不相同的尺子来观看同一段健身视频，标记出动作与自身重复对齐的位置，然后把这些标记相加，得到最终的计数。
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is the controlled RepCount-A comparison plus ablations showing that the proposed correlation and density-map choices each move the same metrics in the intended direction.
      **最佳证据:** 最有力的证据是在 RepCount-A 上进行的受控对比实验，以及消融实验：这些实验表明，论文提出的相关性设计与密度图设计，都各自把同样的指标朝着预期方向推进。
      evidence:: E11, E14, E15
        - Supports C1: RepCount compared with UCFRep and Countix; baseline datasets have shorter clips and coarser labels; metrics are video count, duration, count range, and annotations; delta is 1,451 videos with 19,280 cycle annotations and longer average duration; support status direct dataset evidence.
          支持结论 C1：把 RepCount 与 UCFRep、Countix 作对比；作为对照的这两个数据集片段更短、标注更粗糙；比较的指标是视频数量、时长、计数范围和标注方式；RepCount 的增量是 1,451 段视频、19,280 处动作周期（action cycle）标注，且平均时长更长；支持状态为直接的数据集证据。
          evidence:: E4, E5
        - Supports C2: RepCount Part-A training and test; closest listed baseline is Huang et al.; MAE drops from 0.5267 to 0.4431 and OBO rises from 0.1589 to 0.2913; support status positive but no variance reported.
          支持结论 C2：在 RepCount Part-A 上训练并测试；列出的最接近的对照方法是 Huang 等人的工作；平均绝对误差（Mean Absolute Error，MAE）从 0.5267 降到 0.4431，误差不超过一次（Off-By-One，OBO）指标从 0.1589 升到 0.2913；支持状态为正向，但未报告方差。
          evidence:: E11
        - Supports C3: RepCount Part-A ablations; baselines are TSM correlation, classifiers, and single-scale variants; self-attention, density-map regression, and multi-scale fusion all improve MAE or OBO; support status positive but controlled only within the authors' setup.
          支持结论 C3：在 RepCount Part-A 上做消融实验；对照基线包括 TSM 相关性、分类器和单尺度变体；自注意力（self-attention）、密度图（density map）回归和多尺度融合都改善了 MAE 或 OBO；支持状态为正向，但仅在作者自己的实验设置内受控验证。
          evidence:: E14, E15
    - **Main Caveat:** Trust is bounded by the fixed-frame inference policy, missing uncertainty reporting, and paper-shown failures when multiple people move or most repetitions are concentrated in one part of a long clip.
      **主要边界:** 对该工作的信任受三方面限制：固定帧数的推理策略、缺少不确定性报告，以及论文自己展示的失败情形——即画面中有多人同时运动，或者绝大多数重复都集中在一段长片段的某一部分时。
      claim_kind:: analyst_assessment
      evidence:: E10, E13
- ## Argument Map
    - **Problem and Stakes:** The paper argues that repetitive action counting is useful for human-centric video analysis, but existing benchmarks understate the real problem because they focus on short videos and aggregate count labels. The stakes are practical robustness and interpretability: a model can get a final number roughly right while placing the implied cycles at the wrong times.
      **问题与重要性:** 论文认为，重复动作计数对以人为中心的视频分析很有用，但现有基准低估了真实问题的难度，因为它们只关注短视频和汇总的计数标签。其现实意义在于稳健性和可解释性：一个模型可能把最终数字大致数对，却把推断出的各个周期放在了错误的时间位置上。
      evidence:: E2, E3
    - **Prior Gap:** Prior repetitive-counting datasets are presented as too clean: they largely lack interruption, within-video speed variation, long-range clips, and start/end labels for each cycle. That gap blocks both harder evaluation and training objectives that care where cycles occur.
      **已有方法缺口:** 以往的重复计数数据集被认为过于「干净」：它们大多缺少动作中断、视频内速度变化、长时程片段，以及每个周期的起止时间标注。这一缺口既阻碍了更有难度的评估，也阻碍了那些关注周期出现位置的训练目标。
      evidence:: E2, E3, E5
    - **Key Insight:** The core insight is that repetition can be treated as self-similarity over time: if the same motion phase recurs, video features from those moments should correlate, and this correlation should be measured at multiple temporal scales because actions run at different speeds.
      **关键洞见:** 核心洞见是：重复可以看作时间上的自相似性。如果同一个动作阶段反复出现，那么这些时刻的视频特征之间就应当彼此相关；而且这种相关性应当在多个时间尺度上测量，因为不同动作的执行速度各不相同。
      evidence:: E6, E7, E8
    - **Claims:** The paper advances three falsifiable claims about the benchmark, the model, and the design choices.
      **核心主张:** 本文围绕基准数据集、模型以及设计选择，提出了三个可证伪的论断。
      claim_kind:: analyst_assessment
        - C1: RepCount is a more realistic and harder repetitive action counting benchmark because it contains longer videos, fine-grained cycle labels, anomaly cases, and a local-school subset for generalization checks.
          C1：RepCount 是一个更贴近真实、也更困难的重复动作计数（repetitive action counting，RAC）基准，因为它包含更长的视频、细粒度的周期标注、异常样本，以及一个用于检验泛化能力的本地学校子集。
          evidence:: E1, E4, E5
        - C2: TransRAC outperforms the compared action-recognition, action-segmentation, and repetition-counting baselines on RepCount Part-A and transfers better than RepNet to RepCount Part-B and UCFRep when trained on Part-A.
          C2：在 RepCount Part-A 上，TransRAC 优于所参与对比的动作识别、动作分割和重复计数基线方法；并且当在 Part-A 上训练后，它向 RepCount Part-B 和 UCFRep 的迁移效果比 RepNet 更好。
          evidence:: E11, E12
        - C3: The model's self-attention temporal correlation, density-map period predictor, and multi-scale subsequences each contribute measurable performance gains in the authors' ablations.
          C3：在作者的消融实验中，模型的自注意力时序相关性、密度图周期预测器，以及多尺度子序列各自都带来了可测量的性能提升。
          evidence:: E14, E15, E16
- ## Mechanism and Design
    - **Core Mechanism:** TransRAC samples a video into short clips, embeds them with a Video Swin Transformer, a transformer-style video encoder that uses windowed attention over space and time, computes self-attention correlation matrices, and regresses a density map, a time-series whose integral estimates the repetition count. The count is obtained by summing predicted density values rather than directly classifying a count bin.
      **核心机制:** TransRAC 先把一段视频采样成若干短片段，用 Video Swin Transformer 为它们生成特征表示。Video Swin Transformer 是一种基于 transformer 的视频编码器，它在空间和时间上使用窗口化注意力。随后模型计算自注意力相关性矩阵，并回归出一张密度图（density map，DM）。密度图是一条时间序列，其积分可用于估计重复次数。最终的计数是通过对预测的密度值求和得到的，而不是直接把计数归到某个类别区间里。
      evidence:: E6, E8, E9
    - **Data / Control Flow:** Input frames are converted into single-frame, four-frame, and eight-frame subsequences; each scale is encoded, spatially pooled, compared with itself through query-key dot-product attention, concatenated across scales and heads, then passed to the period predictor. At inference, the model samples a fixed number of frames, pads short videos, predicts the density sequence, and linearly sums it into the final count.
      **数据/控制流:** 输入帧被转换为单帧、四帧和八帧三种子序列；每一种尺度分别经过编码、空间池化，再通过查询—键点积注意力（query-key dot-product attention）与自身进行比较，然后跨尺度、跨注意力头进行拼接，最后送入周期预测器。在推理阶段，模型采样固定数量的帧，对较短的视频进行填充，预测出密度序列，并对其做线性求和得到最终计数。
      evidence:: E7, E8, E10
    - **Design Decisions:** The major choices all convert the same idea into tractable supervision: compare time positions to expose repetition, keep multiple temporal receptive fields for fast and slow motions, and predict a localizable density map because the dataset supplies cycle boundaries.
      **设计决策:** 这些主要选择都是把同一个思路转化为可处理的监督信号：通过比较不同时间位置来暴露重复，为快动作和慢动作保留多个时间感受野，以及预测一张可定位的密度图（因为数据集提供了周期边界标注）。
      evidence:: E5, E7, E9
        - Need: fixed sampling can miss fast actions or waste compute on slow ones; design choice: three temporal clip scales; closest reported alternative: single-scale columns; tradeoff: more feature extraction and fusion for better coverage of variable periods.
          需求：固定的采样方式可能漏掉快动作，或在慢动作上浪费计算；设计选择：采用三种时间片段尺度；文中给出的最接近的替代方案：单尺度的列；权衡：需要更多的特征提取与融合，以换取对可变周期更好的覆盖。
          evidence:: E7, E15
        - Need: count repeated phases rather than only recognize action class; design choice: dot-product self-attention as a temporal correlation matrix; closest reported alternative: Temporal Self-similarity Matrix using squared Euclidean distance; tradeoff: better reported metrics but transformer-like quadratic pairwise comparison.
          需求：要对重复出现的动作阶段进行计数，而不只是识别动作类别；设计选择：把点积自注意力（dot-product self-attention）用作时序相关性矩阵；文中给出的最接近的替代方案：使用平方欧氏距离的时序自相似矩阵（Temporal Self-similarity Matrix）；权衡：报告的指标更好，但存在类似 transformer 的两两比较带来的二次方复杂度。
          evidence:: E8, E14
        - Need: count labels alone do not say where repeats occur; design choice: density-map regression from Gaussianized cycle labels; closest reported alternative: classifier-style count predictors; tradeoff: more annotation demand for better localization and reported accuracy.
          需求：仅凭计数标签无法说明重复动作出现在视频的什么位置。设计选择：从高斯化（Gaussianization）后的动作周期（action cycle）标签出发做密度图（density map）回归。最接近的已有替代方案是分类器式的计数预测器。权衡代价是：需要更多标注量，以换取更好的位置定位和论文所报告的准确率。
          evidence:: E5, E9, E15
    - **Implementation Surface:** The implementation uses PyTorch, a Video Swin Transformer tiny encoder pretrained on Kinetics400, frozen encoder parameters during training because of GPU memory limits, a transformer hidden dimension of 512, Adam optimization, batch size 16, and 16K training steps. The paper reports no post-processing for accuracy at inference, and the provided text points to code for additional details rather than fully specifying scripts or hardware.
      **实现边界:** 实现方面使用 PyTorch，采用在 Kinetics400 上预训练的 Video Swin Transformer tiny 编码器，训练时因 GPU 显存限制而冻结编码器参数，transformer 隐藏层维度为 512，使用 Adam 优化器，批处理（batch）大小为 16，训练步数为 16K。论文指出推理时不做任何后处理即可获得该准确率。所提供的文本把更多细节指向代码，而没有完整给出脚本或硬件配置。
      evidence:: E10
- ## Evaluation and Evidence
    - **Setup:** The main evaluation trains on RepCount Part-A and tests on RepCount Part-A, RepCount Part-B, and UCFRep; the paper also reports an open-set split where test action types are disjoint from train and validation. Metrics are Off-By-One (OBO), the fraction of videos counted within one repetition, and Mean Absolute Error (MAE), normalized absolute count error where lower is better.
      **实验设置:** 主实验在 RepCount Part-A 上训练，并在 RepCount Part-A、RepCount Part-B 和 UCFRep 上测试。论文还报告了一种开放集设置（open-set setting），即测试集中的动作类型与训练集和验证集完全不重叠。评估指标包括 Off-By-One（OBO），即预测计数与真值相差不超过一次重复的视频所占比例；以及平均绝对误差（Mean Absolute Error，MAE），即归一化后的绝对计数误差，数值越低越好。
      evidence:: E11, E12, E17
    - **Claim-Evidence Matrix:** The evidence is strongest where the paper controls training data and compares directly against named baselines, and weakest where it lacks repeat counts, variance, or hardware-normalized cost.
      **主张-证据矩阵:** 证据最充分的地方，是论文能够控制训练数据并直接与指定的基线方法作比较；证据最薄弱的地方，是它缺少重复实验次数、方差，以及经硬件归一化后的成本数据。
      claim_kind:: analyst_assessment
      evidence:: E10, E11, E15
        - Supports C1: dataset statistics and annotation protocol directly show larger average duration, more fine-grained labels, Part-A/Part-B sources, and per-cycle start/end labeling, but privacy and bias are acknowledged only broadly.
          支持论点 C1：数据集统计与标注协议直接表明其平均时长更长、标签更细粒度、区分了 Part-A/Part-B 来源，并对每个周期做了起止时间标注；但对隐私与偏差问题只做了笼统的说明。
          evidence:: E4, E5
        - Supports C2: Table 2 and Table 3 report better MAE and OBO than the compared methods on RepCount-A, RepCount-B, and UCFRep, with Part-B and UCFRep serving as no-fine-tuning transfer checks.
          支持论点 C2：Table 2 和 Table 3 显示，在 RepCount-A、RepCount-B 和 UCFRep 上，其 MAE 和 OBO 都优于所比较的方法，其中 Part-B 和 UCFRep 用作免微调的迁移检验。
          evidence:: E11, E12
        - Supports C3: Table 4 isolates correlation choice, Table 5 compares density-map and scale variants, and the supplement adds density-position and sampling-rate sensitivity.
          支持论点 C3：Table 4 单独考察了相关性计算方式的选择，Table 5 比较了不同的密度图和尺度变体，补充材料还增加了对密度位置和采样率的敏感性分析。
          evidence:: E14, E15, E16
    - **Headline Results:** On RepCount Part-A, TransRAC reports the best listed MAE and OBO under the shared training setup, and on transfer tests it substantially beats RepNet while still leaving large absolute error on Part-B. In the open-set split, it beats the action-segmentation comparison, supporting the claim that repetitive counting is not just temporal segmentation over known action classes.
      **关键结果:** 在 RepCount Part-A 上，在统一的训练设置下，TransRAC 报告了所列方法中最好的 MAE 和 OBO；在迁移测试中，它大幅超过 RepNet，但在 Part-B 上仍留有较大的绝对误差。在开放集设置中，它超过了用于对比的动作分割方法，支持了如下论点：重复动作计数并不只是对已知动作类别做时间上的分割。
      evidence:: E11, E12, E17, E18
        - RepCount-A: TransRAC reports MAE 0.4431 and OBO 0.2913, versus the closest listed baseline Huang et al. at MAE 0.5267 and OBO 0.1589; uncertainty is not reported.
          RepCount-A：TransRAC 报告 MAE 为 0.4431、OBO 为 0.2913，而最接近的所列基线 Huang 等人的方法 MAE 为 0.5267、OBO 为 0.1589；论文未报告不确定性。
          evidence:: E11
        - Transfer: training on Part-A, TransRAC reports MAE/OBO of 0.7839/0.091 on Part-B and 0.6401/0.324 on UCFRep, compared with RepNet's 0.9994/0.0025 and 0.9985/0.009.
          迁移：在 Part-A 上训练后，TransRAC 在 Part-B 上报告的 MAE/OBO 为 0.7839/0.091，在 UCFRep 上为 0.6401/0.324，相比之下 RepNet 分别为 0.9994/0.0025 和 0.9985/0.009。
          evidence:: E12
        - Open-set: with disjoint action types across splits, TransRAC reports MAE 0.6249 and OBO 0.2040, while the action-segmentation baseline reports MAE 1.0000 and OBO 0.0000.
          开放集设定（open-set setting，即测试集中的动作类型与训练/验证集互不重叠）：在各数据划分之间动作类型互不相交的情况下，TransRAC 报告 MAE 0.6249、OBO 0.2040，而动作分割基线方法报告 MAE 1.0000、OBO 0.0000。
          evidence:: E17
    - **Ablations and Sensitivity:** The ablations support the main design but also reveal sensitivity to sampling and density target placement: self-attention beats TSM, density maps beat classifier variants, multi-scale fusion beats each single-scale variant, mid-frame Gaussian targets are best among tested density placements, and more sampled frames help the single-scale density model. These are useful controlled checks, but they do not report statistical uncertainty or resource budgets.
      **消融与敏感性:** 消融实验支持了主要设计，但也揭示出模型对采样方式和密度目标放置位置的敏感性：自注意力（self-attention）优于 TSM，密度图（density map）优于各种分类器变体，多尺度融合优于任何单尺度变体，在测试过的各种密度放置方式中以帧中心的高斯目标效果最好，采样帧数越多对单尺度密度模型越有帮助。这些都是有价值的受控检验，但它们没有报告统计不确定性，也没有报告资源开销。
      evidence:: E14, E15, E16
    - **Reproducibility Gaps:** The paper states that dataset and code are available and gives key hyperparameters, but the provided text does not report random seeds, repeated-run variance, confidence intervals, exact hardware, runtime, memory footprint, or full preprocessing scripts. Because the encoder is frozen due to GPU memory limits, missing hardware and memory details matter for reproducing both performance and efficiency claims.
      **可复现性缺口:** 论文声明数据集和代码均已公开，并给出了关键超参数，但所提供的正文没有报告随机种子、重复运行的方差、置信区间、具体硬件、运行时间、内存占用，也没有给出完整的预处理脚本。由于受 GPU 显存限制而冻结了编码器，缺失的硬件和内存细节对于复现性能与效率方面的结论都很重要。
      claim_kind:: analyst_assessment
      evidence:: E1, E10
- ## Technical Judgment
    - **What Holds Up:** The paper's strongest technical move is aligning supervision, representation, and task structure: per-cycle labels justify density-map regression, temporal self-comparison matches periodicity, and multiple clip scales address variable action speed. The ablations are directionally consistent with this story rather than only showing a monolithic final model.
      **站得住的结论:** 论文在技术上最有力的做法，是让监督信号、表示方式与任务结构三者相互对齐：逐周期的标注为密度图回归提供了依据，时间上的自比较契合了周期性，多个片段尺度则应对了动作速度的变化。消融实验在方向上与这一思路一致，而不仅仅是展示一个孤立的最终模型。
      claim_kind:: analyst_assessment
      evidence:: E5, E7, E9, E14, E15
    - **Where It May Fail:** The clearest failure boundary is videos where the sampled frames do not preserve the temporal distribution of repetitions, especially long clips with most action concentrated in one segment, or scenes with more than one moving person. Benefits may also diminish when fine-grained cycle labels are unavailable, since the density target is built from those labels.
      **可能失效之处:** 最明确的失效边界是这样一类视频：采样得到的帧没有保留重复动作的时间分布，尤其是那些时长较长、绝大部分动作集中在某一段内的片段，或者画面中有不止一个运动的人。当无法获得细粒度的周期标注时，收益也可能减弱，因为密度目标正是根据这些标注构建的。
      claim_kind:: analyst_assessment
      evidence:: E5, E10, E13
    - **Relation to Other Work:** Relative to RepNet-style repetition counting, TransRAC shifts from count-oriented prediction toward temporal localization through density regression and self-attention correlation. Relative to action segmentation, which labels contiguous spans of known action types, it targets repeated-cycle counting regardless of action category, which explains the open-set comparison.
      **与已有工作的关系:** 相比 RepNet 那类以计数为导向的重复动作计数方法，TransRAC 通过密度回归和自注意力相关性，从面向计数的预测转向了时间定位。相比动作分割（它对已知动作类型的连续时间段打标签），TransRAC 的目标是不论动作类别如何都对重复周期进行计数，这也解释了为何要做开放集对比。
      claim_kind:: analyst_assessment
      evidence:: E3, E14, E15, E18
    - **Transferable Lesson:** When a task asks for a global count of repeated events, it can be better to supervise a local time-density signal and then sum it, provided the dataset can label event locations. Multi-scale self-comparison is a reusable pattern for turning variable-speed temporal structure into a countable representation.
      **可迁移启发:** 当一个任务要求对重复事件给出全局计数时，更好的做法可能是监督一个局部的时间密度信号、再把它累加起来，前提是数据集能够标注出事件发生的位置。多尺度自比较是一种可复用的模式，可以把速度可变的时间结构转化为可计数的表示。
      claim_kind:: analyst_assessment
      evidence:: E5, E7, E8, E9
- ## Glossary
  collapsed:: true
    - repetitive action counting: Estimating how many complete cycles of a repeated human motion appear in a video; unlike action recognition, the target is count over time.
      重复动作计数（repetitive action counting）：估计一段视频中某个重复的人体动作出现了多少个完整周期；与动作识别不同，这里的目标是随时间变化的计数。
    - action cycle: One complete repetition of the motion; RepCount annotates each cycle by start and end time.
      动作周期（action cycle）：动作的一次完整重复；RepCount 通过起始时间和结束时间来标注每一个周期。
    - temporal correlation: A comparison between time positions in the same video feature sequence; repeated motion phases should show stronger correlation.
      时间相关性（temporal correlation）：在同一视频特征序列的不同时间位置之间进行比较；重复出现的动作阶段之间应表现出更强的相关性。
    - self-attention: A transformer operation that compares each feature position with other positions through query and key vectors; TransRAC uses it as the temporal correlation matrix.
      self-attention（自注意力）：一种 transformer 运算，通过查询向量和键向量把每个特征位置与其他位置进行比较；TransRAC 用它来充当时间相关性矩阵。
    - multi-scale temporal input: Parallel subsequences spanning different numbers of frames, used so the model can observe both fast and slow repetitions.
      multi-scale temporal input（多尺度时间输入）：多条并行的子序列，各自跨越不同的帧数，用来让模型既能观察到快速重复，也能观察到缓慢重复。
    - density map: A one-dimensional time signal whose values indicate where repetitions occur; summing the values gives the predicted count.
      density map（密度图）：一种一维时间信号，其数值表示重复动作在何处发生；把所有数值相加即可得到预测的计数。
    - Gaussianization: The process of converting annotated cycle boundaries into a smooth density target using a Gaussian function.
      Gaussianization（高斯化）：利用高斯函数把标注好的动作周期边界转换成一条平滑的密度目标的过程。
    - Off-By-One: Evaluation metric counting a video as correct when the predicted count is within one repetition of the ground truth; higher is better.
      Off-By-One（误差不超过一次，OBO）：一种评估指标，当预测计数与真实计数相差不超过一次重复时，就把该视频判为正确；数值越高越好。
    - Mean Absolute Error: Normalized absolute count error between prediction and ground truth in this paper's evaluation; lower is better.
      Mean Absolute Error（平均绝对误差，MAE）：本文评估中，预测计数与真实计数之间经过归一化的绝对误差；数值越低越好。
    - open-set setting: Evaluation where the action types in the test split do not appear in training or validation, testing whether counting transfers beyond seen categories.
      open-set setting（开放集设定）：一种评估方式，测试集中的动作类型不出现在训练集或验证集中，用以检验计数能力能否推广到未见过的类别之外。
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/paper_statement | Abstract | high
      locator:: Abstract
      quote:: we introduce a new large-scale repetitive action counting dataset covering a wide variety of video lengths, along with more realistic situations where action interruption or action inconsistencies occur in the video.
    - **E2:** problem/paper_statement | 1. Introduction | high
      locator:: Restricted video length paragraph
      quote:: The previous datasets typically contain only short videos (e.g., 0.4-30 s), however, methods are likely to be deployed to long videos in real scenarios.
    - **E3:** gap/paper_statement | 1. Introduction | high
      locator:: Inadequate annotations paragraph
      quote:: the number of repetitive actions in a video is simply labeled as a numerical value. Although the count number serves as an ultimate predictive goal, such coarse-grained annotation deprives the interpretability of the algorithm.
    - **E4:** background/metadata | 3. Our Proposed Dataset | high
      locator:: Table 1 and Dataset statistics
      quote:: we provide 1,451 videos collaborated with 19,280 annotations. The videos from our dataset have an average length of 39.359 seconds, which is 4-5 times the length of videos from other datasets.
    - **E5:** method/paper_statement | 3. Our Proposed Dataset | high
      locator:: Dataset annotation
      quote:: each individual video is assigned to two volunteers; ii) start and end time of every action cycle are labeled; iii) the annotations are cross-validated by comparing that from two volunteers
    - **E6:** method/implementation_detail | 4. TransRAC Model | high
      locator:: Model overview and Figure 3
      quote:: TransRAC that contains three stages: the encoder, temporal correlation, and period predictor. The video subsequences V are fed into the encoder, then the output X is used to calculate the correlation matrix C
    - **E7:** algorithm/implementation_detail | 4.1. Encoder | high
      locator:: Video sequences of multi-scale
      quote:: We extract three scale subsequences from the video: single-frame, 4-frames, and 8 frames indicating the video subsequence of multi-scale (V) in Fig. 3.
    - **E8:** algorithm/implementation_detail | 4.2. Temporal correlation and Self-attention | high
      locator:: Self-attention paragraph
      quote:: We use 4-heads with 512 dimensions (not eight heads which is more usual) and multi-scale embeddings to calculate the correlation. Therefore, after the self-attention layer, concatenating three scales' features into one
    - **E9:** algorithm/implementation_detail | 4.3 Period Predictor and 4.4 Losses | medium
      locator:: Density map and Losses
      quote:: We use the density map predicto as our period predictor. The density map contains the global information of the entire video. Each row of the density map indicates the frame's position in the local cycle
    - **E10:** implementation/implementation_detail | 5.2. Implementation Details and 4.5 Inference | medium
      locator:: Implementation Details; Inference
      quote:: The encoder, Video Swin Transformer tiny, was pre-trained on the Kinetics400... the parameters of the pre-trained encoder were frozen during the training process. We train our remaining layers of the model for 16K steps
    - **E11:** result/experiment_result | 5.4. Evaluation and Comparison | medium
      locator:: Table 2
      quote:: Table 2. Performance of different methods on RepCount part-A test when trained on the same train set of RepCount. Huang et al.: MAE 0.5267, OBO 0.1589; Ours: MAE 0.4431, OBO 0.2913.
    - **E12:** result/experiment_result | 5.4. Evaluation and Comparison | medium
      locator:: Table 3
      quote:: Performance of different methods on RepCount part-B and UCFRep when trained on the same train set of RepCount part-A. RepNet: 0.9994/0.0025 and 0.9985/0.009; Ours: 0.7839/0.091 and 0.6401/0.324.
    - **E13:** limitation/case_study | 5.4. Evaluation and Comparison | medium
      locator:: Figure 5 bad cases
      quote:: there still are some failure cases... because there is more than one person moving in the video. The failure case on the bottom indicates that the frame extracting strategy could diminish the performance.
    - **E14:** ablation/ablation | 5.5. Ablation Studies | medium
      locator:: Table 4
      quote:: Table 4. Result of our model applying different correlation matrix when trained on training set of RepCount part-A. TSM: MAE 0.5678, OBO 0.2251. Self-attention (Ours): MAE 0.4431, OBO 0.2913.
    - **E15:** ablation/ablation | 5.5. Ablation Studies | medium
      locator:: Table 5
      quote:: Table 5. ResNet + CLS: MAE 0.9950, OBO 0.0134; ResNet + DM: MAE 0.6905, OBO 0.0811; Ours (Scale-4): MAE 0.5434, OBO 0.2649; Ours (Multi): MAE 0.4431, OBO 0.2913.
    - **E16:** ablation/ablation | A. Extra experiments | medium
      locator:: A.1 Density map and A.2 Sample rate
      quote:: The density map generated by the mean in the mid-frame has the best effort. Experimental results show that increasing video frames can improve the performance of density maps to a certain extent
    - **E17:** result/experiment_result | B. Dataset description | medium
      locator:: B.2 Open-set setting and Table 9
      quote:: For Open-set setting, the action types in train/val/test are disjoint, where the actions in the test set do not appear in the training set. Table 9 reports Huang et al. 1.0000/0.0000 and Ours 0.6249/0.2040.
    - **E18:** prior_work/paper_statement | A.5. Compare to action segmentation | medium
      locator:: Supplementary A.5
      quote:: action segmentation is to segment the temporal bound for different types of actions but repetitive action counting aims to count the number of repetitive action... action segmentation can only address predefined action types
