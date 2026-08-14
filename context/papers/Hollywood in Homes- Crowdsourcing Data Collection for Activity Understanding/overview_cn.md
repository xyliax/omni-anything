- **标题:** 居家好莱坞：为活动理解众包采集数据
- **一句话总结:** 「居家好莱坞」表明，数据的创建过程本身也可以众包，从而构建出 Charades 数据集。这是一个受控但多样的家庭活动基准，其基线模型的失败暴露出在细粒度的人-物交互和视频描述生成上的不足。
- **论文类型:** 数据集
- **发表:** arXiv 2016
- **作者:** Gunnar A. Sigurdsson、Gul Varol、Xiaolong Wang、Ali Farhadi、Ivan Laptev 和 Abhinav Gupta；分别来自卡内基梅隆大学（Carnegie Mellon University）、法国国家信息与自动化研究所（Inria）、华盛顿大学（University of Washington）以及艾伦人工智能研究所（The Allen Institute for AI）
- **关键词:** 活动理解、众包数据集采集、Charades、家庭活动、动作识别、视频描述生成、时序定位、人-物交互
- ## Orientation
    - **背景:** 背景：本文关注的是活动理解（activity understanding，即让视觉系统识别人们随时间推移正在做什么，而不仅仅是识别单张图像中出现了哪些物体）。其前提性观点是：数据集会塑造模型的行为，因为模型学到的正是数据集中频繁出现的那些情境。
      claim_kind:: analyst_assessment
    - **通俗问题:** 用大白话讲问题：日常家务行为在视觉上平淡无奇，因此人们很少把这类行为的清晰示例上传到网上；然而家用机器人和辅助工具恰恰需要理解的正是这类行为。
      claim_kind:: analyst_assessment
    - **为何困难:** 为什么这件事很难：所需数据必须真实、多样，且带有随时间推移的标注，同时又要足够可控，好让学习任务拥有清晰的标签。
      claim_kind:: analyst_assessment
    - **一句话核心思路:** 一句话概括核心思路：把拍摄流程搬进众包工人自己的家里——让人们撰写简短的脚本（script），把脚本演出来，再让其他工人核验并标注拍出来的视频。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **阅读价值:** 把本文当作一篇面向活动理解（activity understanding）的数据集设计论文来读。活动理解是一个计算机视觉问题，指识别人们随时间推移在做什么。本文针对的是：网络和电影素材对普通家庭行为的呈现严重不足，从而造成数据缺口。
      claim_kind:: analyst_assessment
      evidence:: E2, E13
    - **一句话贡献:** 「居家好莱坞」改进了家庭活动数据的采集方式：它让线上工作者充当剧本作者、演员和标注员，从而产出了 Charades 数据集，其中包含自由文本描述、动作标签，以及带起止时间的标签（即时序定位）。
      evidence:: E1, E3, E6
    - **记忆模型:** 可以把它想象成一个分布式的家庭电影制片厂：研究者提供一份简短的道具清单和任务清单，许多人在家中即兴表演普通的日常场景，再由另一批观看者核对实际发生了什么。
      claim_kind:: analyst_assessment
    - **最佳证据:** 最有力的证据来自三者的结合：数据集的规模、受控的标注，以及基线模型偏弱的表现。后者用平均精度均值（mean average precision，mAP）来衡量——这是一种对排序后的预测结果求平均精度的指标。
      evidence:: E1, E9, E12
        - 支持论点 C1：数据集为 Charades v1.0；表 1 中列出了同时期的其他视频数据集作为对照；涵盖数据集来源、动作密度、标签以及时间定位（temporal localization，即标注动作在视频中何时开始、何时结束）；每段视频平均包含 6.8 个动作，共 157 个动作类别，来自 267 户家庭的约 67K 个标签；作为数据集规模层面的证据成立。
          evidence:: E1, E14
        - 支持论点 C3：在 Charades 上进行动作分类；对比基线包括 Random（随机）、C3D、AlexNet、Two-Stream（双流网络）、Improved Dense Trajectories（改进密集轨迹，IDT），以及晚期融合的 Combined（组合）方法；评价指标为平均精度均值（mean average precision，mAP）；Combined 达到 18.6%，而 Random 仅为 5.9%；该论点成立，但未报告方差或重复实验次数。
          evidence:: E9
        - 支持论点 C4：基于脚本（script）与视频描述进行句子预测；对比对象为 Sequence to Sequence - Video to Text（序列到序列的视频转文本，S2VT）与人工撰写的描述；评价指标为字幕相似度 CIDEr；S2VT 得分为 0.17/0.14，人工描述得分为 0.51/0.53；该论点成立，但仅限于早期基线方法。
          evidence:: E12
    - **主要边界:** 主要保留意见：这些证据确实证明了 Charades 对 2016 年的基线方法而言颇具挑战性，但该数据集的采集方式仍然是按脚本表演的，且相关实验没有报告不确定性、重复实验次数、硬件预算，也没有与现代模型进行对比。
      claim_kind:: analyst_assessment
      evidence:: E4, E5, E9, E12
- ## Argument Map
    - **问题与重要性:** 问题与意义：论文主张，面向真实家庭场景的模型需要普通、以物体为中心的活动的训练样本，而不能只用静态图像、体育片段、电影或实验室场景。其意义在于服务于表征学习，涵盖物体状态、人与物体的交互、上下文情境、视频描述，以及未来的机器人感知。
      evidence:: E1, E2
    - **已有方法缺口:** 既有研究的空白：来自互联网和电影的数据集能提供规模，但偏向娱乐性或经过剪辑的动作；而在受控环境内录制的数据集和第一人称日常活动数据集能提供可控性，却缺乏同等的多样性或可扩展性。文中把 ActivityNet 视为互补性的数据集，因为它使用了 YouTube 上的日常活动，但这些视频仍然是不受控且经过专业剪辑的。
      evidence:: E13, E14
    - **关键洞见:** 采集的瓶颈可以从「寻找网上自然上传的视频」转移到「按需拍摄普通视频」，同时通过让参与拍摄的众包工作者在各自真实的家中拍摄来保持多样性。控制的抓手不是实验室搭建的场景，而是一段受词汇约束的脚本提示（script prompt）。
      evidence:: E3, E4, E5
    - **核心主张:** 这篇论文的主要主张涉及三方面：一种采集方法、由此得到的数据集，以及这个数据集给识别与描述生成系统带来的困难。
      evidence:: E1, E3, E9
        - C1：Hollywood in Homes 方法能够生成一个规模大、可控且多样的真实家庭活动数据集，而无需依赖网络搜索、电影或实验室录制。
          evidence:: E1, E3, E5
        - C2：Charades 提供了密集的多动作视频，并带有时间定位（temporal localization，即标注动作在视频中何时开始与结束）以及物体交互标签，因而适合用于家庭活动、场景语境和描述生成的基准测试。
          evidence:: E1, E6, E7
        - C3：标准的动作识别基线方法在 Charades 上表现吃力，尤其是当不同动作主要靠所操作的物体不同、或靠细粒度的交互差异来区分时。
          evidence:: E9, E10
        - C4：视频描述生成（video captioning）的基线方法在 Charades 上能够产出连贯的语言，但在相关性上离人类的描述还很远。
          evidence:: E11, E12
- ## Mechanism and Design
    - **核心机制:** 该方法使用 Amazon Mechanical Turk（AMT，一个用于付费任务的在线众包市场）来分发整个数据生命周期：一部分工作者撰写脚本（script），另一部分工作者在家中按脚本表演并录制，还有一部分工作者负责核验并标注这些视频。这把众包（crowdsourcing）从一种单纯的标注工具，变成了一条可控的内容创作流水线。
      evidence:: E3, E5, E6
    - **数据/控制流:** 这条流水线从一段受约束的文本提示开始，把这段提示转化为一段在家中录制的视频，核验视频是否与提示相符，然后再从中派生出描述文本、物体标签、动作类别（action class）以及时间区间。最终得到的成果为每段视频关联起自由文本、物体交互、多动作标签，以及动作发生的时间。
      evidence:: E4, E5, E6
        - 脚本环节：工作者会拿到一个房间、若干抽样得到的物体和若干抽样得到的动作，然后据此写出一段简短、贴近现实的段落，使数据集既有引导性、又保留了人类的想象成分。
          evidence:: E4
        - 视频环节：工作者在自己家中录制约半分钟长的视频，把脚本当作导演指令，同时在房间、物体、着装和行为等方面带来自然的差异。
          evidence:: E5
        - 标注环节：标注人员描述所观看的视频，核对物体清单与动作是否出现，并标出动作的起点和终点，从而完成时间定位（temporal localization，即标注动作在视频中的开始与结束时刻，而不仅仅说明动作出现在某处）。
          evidence:: E6
    - **设计决策:** 核心的取舍在于「受控的多样性」：研究者把词汇限制到足以对动作进行基准评测的程度，同时又让场景和段落的构建保持足够开放，以保留人类的差异。他们还把采集预算花在招募、留存和核验上，因为相比普通的标注，拍摄更为不便。
      evidence:: E4, E5, E6
        - 需求：每个类别要有足够的样本；设计选择：用精心挑选的房间、物体和动作作为脚本（script）的种子；最接近的替代方案：自由的网络搜索或自由发挥的拍摄；取舍：控制更好，但词汇范围受限。
          evidence:: E4
        - 需求：贴近现实的家庭场景；设计选择：让标注人员用选定的素材编写简短段落；最接近的替代方案：由实验室撰写脚本；取舍：带来更多人类偏差与多样性，但语义控制不够精确。
          evidence:: E4, E7
        - 需求：可用的视频与标签；设计选择：把核验环节和穷尽式的动作标注分开进行，测试集尤其如此；最接近的替代方案：相信拍摄者的自我报告；取舍：成本更高，但标签的可靠性更好。
          evidence:: E5, E6, E8
    - **实现边界:** 实现层面是一组 AMT（Amazon Mechanical Turk，亚马逊众包平台）上的任务与界面，而不是一种新的识别算法，包括：脚本撰写、拍摄、候选比对核验、物体核验、动作核验，以及时间区间标注。论文表示会随数据集一同发布代码和界面，但仅凭论文中提供的细节，还不足以完整复现整套标注人员的工作流。
      evidence:: E5, E6
- ## Evaluation and Evidence
    - **实验设置:** 评测采用标注人员互不重叠的训练/测试划分，以及多标签分类（multi-label classification，即一个视频可以同时被赋予多个动作标签），用平均精度均值（mean average precision，mAP）来衡量。对比基线包括：手工设计的运动特征、基于物体图像的卷积神经网络特征、双流视频网络、3D 卷积特征、后期融合，以及用字幕指标评测的句子预测基线。
      evidence:: E8, E9, E11
    - **主张-证据矩阵:** 证据在数据集构建和基线难度方面最为充分，在细致的失败分析方面属于中等，而在超出所采集的家庭脚本设定、涉及长期泛化能力的论断方面最为薄弱。
      claim_kind:: analyst_assessment
      evidence:: E1, E8, E9, E12
        - C1：得到所报告的采集流程、标注人员的多样性和数据集规模的支持，但论文关于「真实性」的论断受限于按脚本表演，而非被动的观察。
          claim_kind:: analyst_assessment
          evidence:: E1, E3, E5
        - C2：得到所报告的描述数量、动作区间、物体标签、每个视频的动作数，以及与同期数据集的对比的支持。
          evidence:: E1, E6, E7, E14
        - C3：多个标准基线方法的平均精度均值（mAP）偏低支持了这一点，同时那些共享物体或功能相似物体的动作之间也存在混淆，进一步支持了它。
          evidence:: E9, E10
        - C4：从字幕生成指标来看，S2VT 是最强的基线方法，但仍远低于人工撰写的字幕，这一点支持了 C4；此外还有一些示例显示，模型的输出虽然连贯却与内容无关。
          evidence:: E11, E12
    - **关键结果:** 核心结论是：当时的标准动作识别和字幕生成方法并未把 Charades 数据集用尽。在动作识别基线中，后期融合（late fusion）表现最好，但动作识别的绝对 mAP 依然很低；S2VT 也远低于人工字幕的得分。论文还发现，细粒度的物体交互是造成许多分类混淆的原因。
      evidence:: E9, E10, E12
        - 动作分类：组合后期融合（Combined late fusion）取得 18.6% 的 mAP，IDT 取得 17.2%，随机方法取得 5.9%；这支持了 C3，但论文没有报告方差或多次运行的不确定性。
          evidence:: E9
        - 物体交互带来的失败：Combined 基线主要把涉及同一物体的动作混淆在一起，而不涉及特定物体交互的动作则达到 38.9% 的 mAP；这让 C3 更加明确。
          evidence:: E10
        - 句子预测：S2VT 是最强的基线方法，但它在脚本上的 CIDEr 为 0.17，在描述上为 0.14，而人工分别为 0.51 和 0.53；这支持了 C4。
          evidence:: E12
    - **消融与敏感性:** 最清晰的敏感性研究针对的是 IDT 特征设计：组合 HOG、HOF 和 MBH 描述子，并使用更多的高斯混合分量，可以提升 mAP。论文没有对采集流程本身做因果性的消融实验，比如去掉脚本约束或改变验证的深度。
      evidence:: E15
    - **可复现性缺口:** 已报告的内容：数据集划分规模、标签精度、基线方法的类别、所选超参数，以及公开代码/接口的承诺。未报告的内容：随机种子、多次运行、置信区间、硬件/资源预算、AMT 界面的具体细节，以及论文内完整的训练脚本。
      claim_kind:: analyst_assessment
      evidence:: E5, E8, E9, E11, E15
- ## Technical Judgment
    - **站得住的结论:** 数据生成的逻辑是自洽的：受限的词汇表保证了基准的覆盖面，人工撰写的脚本构造出合理的动作序列，居家录制增加了环境的多样性，独立的验证环节降低了标签噪声。评估也清晰地把数据集意图设定的难度，与基线方法在多动作识别和字幕相关性上的失败联系起来。
      claim_kind:: analyst_assessment
      evidence:: E4, E5, E6, E8, E9, E12
    - **可能失效之处:** 当目标行为是无脚本的、有文化特异性的、涉及安全的、罕见的，或超出精心整理的室内物体词汇表时，这套方法的收益可能会减弱。此外，其普适性也受到限制，因为实证难度是用 2016 年的基线方法展示的，而且没有统计不确定性的说明。
      claim_kind:: analyst_assessment
      evidence:: E4, E5, E9, E12
    - **与已有工作的关系:** 与 UCF101、Sports1M、ActivityNet 等来自 YouTube 的数据集相比，Charades 放弃了自然上传的行为方式，换来了对家庭场景的可控覆盖；与电影描述类数据集相比，它去掉了带娱乐性质的剪辑；与实验室内部拍摄的烹饪或日常生活数据集相比，它通过分布在众多家庭中来扩大多样性。论文把这些来源定位为互补关系，而不是说它们普遍更差。
      evidence:: E13, E14
    - **可迁移启发:** 当缺少自然产生的数据时，应当众包整个生成过程，而不只是标注：把任务约束得足够充分，使得基准的分类可靠，然后让众多参与者提供实验室难以低成本布置出的多样变化。这一模式可以迁移到其他领域，只要目标行为是普通的、私人的，或很少被上传的。
      claim_kind:: analyst_assessment
      evidence:: E3, E4, E5, E6
- ## Glossary
  collapsed:: true
    - 活动理解（activity understanding）：一项计算机视觉任务，用于识别视频中的动作、物体交互以及时间上下文。
    - 众包（crowdsourcing）：利用众多分散的工作者来创建、核验或标注数据；在本文中它还包括拍摄，而不仅仅是标注。
    - 脚本（script）：一段简短的文字，描述普通的家庭动作，由工作者在视频中表演出来。
    - 时间定位（temporal localization）：标注一个动作在视频内何时开始、何时结束，而不只是说这个动作出现在视频中的某处。
    - 动作类别（action class）：基准中为某一类动作设定的标签，通常与物体交互相关，比如打开冰箱。
    - 多标签分类（multi-label classification）：一种分类方式，同一个视频可以同时被赋予多个动作标签。
    - 平均精度均值（mean average precision）：一种排序指标，常用于每个类别都有正例和负例的情形；数值越高越好。
    - 改进的密集轨迹（Improved Dense Trajectories）：一种人工设计的视频特征方法，追踪局部运动模式并将其编码，用于动作识别。
    - 双流网络（two-stream network）：一类视频识别模型，它把单帧画面中的外观信息与跨帧之间的运动信息结合起来。
    - 序列到序列——视频到文本（Sequence to Sequence - Video to Text）：一种视频描述生成的基线方法，它把卷积提取的视觉特征与循环语言模型结合起来。
    - CIDEr：一种描述文本相似度指标，用来把生成的描述与人工撰写的参考描述进行比较。
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/paper_statement | Abstract and The Charades v1.0 Dataset | high
      locator:: Abstract; Introduction dataset paragraph
      quote:: The dataset is composed of 9,848 annotated videos with an average length of 30 seconds, showing activities of 267 people from three continents, and over 15% of the videos have more than one person.
    - **E2:** problem/paper_statement | 1 Introduction | high
      locator:: Introduction, web-video bias discussion
      quote:: But how do we find these boring videos of our daily lives? If we search common activities such as drinking from a cup, riding a bike on video sharing websites such as YouTube, we observe a highly-biased sample of results.
    - **E3:** method/paper_statement | 1 Introduction | high
      locator:: Hollywood in Homes overview
      quote:: We take the Hollywood filming process to the homes of hundreds of people on Amazon Mechanical Turk. AMT workers follow the three steps of filming process: script generation; video direction and acting based on scripts; and video verification.
    - **E4:** method/implementation_detail | 2.1 Generating Scripts | high
      locator:: Script vocabulary and AMT prompt
      quote:: We found 15 types of rooms to cover most of typical homes. From movie-script term statistics we curated a list of 40 objects and 30 actions to be used as seeds for script generation.
    - **E5:** implementation/implementation_detail | 2.2 Generating Videos | high
      locator:: Worker recruitment, cost, and verification
      quote:: To maximize the diversity of scenes, objects, clothing and behaviour of people, we ask the workers themselves to record the 30 second videos by following collected scripts.
    - **E6:** method/implementation_detail | 2.3 Annotations | high
      locator:: Annotation procedure
      quote:: Using the generated scripts, all verb, preposition, noun triplets were analyzed, and the most frequent grouped into 157 action classes. For all the chosen action classes in each video, another set of workers was asked to label the starting and ending point.
    - **E7:** result/paper_statement | 3 Charades v1.0 Analysis | medium
      locator:: Dataset statistics and co-occurrence analysis
      quote:: Since we have control over the data acquisition process, instead of using Internet search, there are on average 6.8 relevant actions in each video. These actions occur in various orders and context, similar to our daily lives.
    - **E8:** experiment_setup/paper_statement | 4 Applications | medium
      locator:: Train/test split and label precision
      quote:: The resulting training and test sets contain 7,985 and 1,863 videos, respectively. The number of annotated action intervals are 49,809 and 16,691 for training and test. The label precision for the data is 95.6%.
    - **E9:** result/experiment_result | 4.1 Action Classification | medium
      locator:: Table 2 and baseline discussion
      quote:: Table 2 reports mAP for action classification: Random 5.9, C3D 10.9, AlexNet 11.3, Two-Stream-B 11.9, Two-Stream 14.3, IDT 17.2, and Combined 18.6.
    - **E10:** result/experiment_result | 4.1 Action Classification | medium
      locator:: Figure 7 discussion
      quote:: The majority of the confusion is among actions that interact with the same object, and there is confusion among objects with similar functional properties. Evaluation of action recognition on actions with no specific object of interaction results in 38.9% mAP.
    - **E11:** experiment_setup/paper_statement | 4.2 Sentence Prediction | high
      locator:: Task setup and baselines
      quote:: The dataset contains sentences that have been used to create the video, as well as multiple video descriptions obtained manually for recorded videos. Captions are evaluated using CIDEr, BLEU, ROUGE, and METEOR metrics.
    - **E12:** result/experiment_result | 4.2 Sentence Prediction | medium
      locator:: Table 4 and Figure 8 discussion
      quote:: Table 4 shows S2VT as the strongest baseline. Its CIDEr scores are 0.17 for script prediction and 0.14 for description prediction, while human performance is 0.51 and 0.53 respectively.
    - **E13:** prior_work/paper_statement | 1 Introduction | high
      locator:: Related dataset discussion
      quote:: Standard approaches in the past have used videos downloaded from the Internet, gathered from movies or recorded in controlled environments. Movies however are still exciting and do not capture the scenes, objects or actions of daily living.
    - **E14:** gap/paper_statement | 1 Introduction | medium
      locator:: Table 1
      quote:: Table 1 compares Charades with ActivityNet, UCF101, HMDB51, THUMOS, Sports 1M, MPII-Cooking, ADL, and MPII-MD across actions per video, classes, labelled instances, total videos, origin, type, and temporal localization.
    - **E15:** ablation/ablation | 4.1 Action Classification | medium
      locator:: Table 3
      quote:: Table 3 studies improved trajectories with HOG, HOF, MBH, descriptor combinations, and GMM cluster counts. Performance improves from 12.3 mAP with HOG at K=64 to 17.2 with HOG+HOF+MBH at K=256.
