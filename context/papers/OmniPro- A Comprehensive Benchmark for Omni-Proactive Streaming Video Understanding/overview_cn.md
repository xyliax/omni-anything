- **标题:** OmniPro：面向全模态主动式流式视频理解的综合基准测试
- **一句话总结:** OMNIPRO 把主动式流式视频理解转化为一个由时间触发、结合音视频的基准测试，用来检验模型能否理解内容、判断何时开口，并在长时间的视频流中持续保持表现。
- **论文类型:** 基准测试
- **发表:** arXiv 预印本 2026
- **作者:** Ruixiang Zhao（中国人民大学）；Jie Yang（腾讯微信视觉团队）；Zijie Xin（中国人民大学）；Tianyi Wang（腾讯微信视觉团队）；Fengyun Rao（腾讯微信视觉团队）；Jing Lyu（腾讯微信视觉团队）；Xirong Li（中国人民大学）
- **关键词:** 全模态主动式流式视频理解、基准测试、音视频视频理解、主动响应、长时程感知、多模态评估
- ## Orientation
    - **背景:** 背景：流式视频助手看的是实时画面流，而不是一段已经录制完成的片段。在这种场景下，所谓有用的行为，是指助手要能听懂语音和环境声音、观察画面变化，并记住刚刚发生过的事情。
      claim_kind:: analyst_assessment
    - **通俗问题:** 用大白话说清问题：用户先给出一条长期有效的指令，之后助手必须自己抓住合适的时机开口，不需要用户再次提醒。
      claim_kind:: analyst_assessment
    - **为何困难:** 为什么这件事很难：有用的信号可能通过语音、背景声音、画面动作或它们的组合出现，而助手必须避免开口太早、太晚或太频繁。
      claim_kind:: analyst_assessment
    - **一句话核心思路:** 一句话说清核心思路：把助手当作一个「有时间要求的倾听者」来测试：给它一条长期有效的指令，标出应当作出回应的时刻，然后同时对时机和内容打分。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **阅读价值:** 把它当作一篇关于主动式流式视频理解的基准设计论文来读。所谓主动式流式视频理解，是指模型观看一段实时视频流，并自行判断何时给出回答的场景。它有一个很有用的观察视角：如何检验模态（即视觉、语音、声音等输入类型），同时避免把离线问答误当成真正的主动性。
      claim_kind:: analyst_assessment
      evidence:: E2, E3, E17
    - **一句话贡献:** OMNIPRO 改进了对流式视频助手的评估方式，做法是把视频转化为「常驻指令」测试，配以经人工核验的触发时刻、预期回答，以及一套既检验内容理解、又检验自主定时响应的评测协议。
      evidence:: E1, E8
    - **记忆模型:** 可以把它想象成一个尽职的事件监控员：它在开始时被告知一条规则，然后持续地看和听，跟踪发生了什么变化，只有当规则真正成立时，才去提醒用户。
      claim_kind:: analyst_assessment
    - **最佳证据:** 最有力的证据不是某一次排行榜上的胜出，而是该基准测试提供的诊断性切片：模型得分会随响应模式、输入模态、触发时刻和声音类型而发生明显变化。
      evidence:: E10, E11, E12, E13
        - 支持结论 C1：把 OMNIPRO 与此前的主动式视频基准做对比；对照对象为 StreamingBench-Pro、OVO-Bench-Pro 与 OmniMMI-Pro；衡量指标是能力覆盖范围与对音频的依赖程度；差异在于 OMNIPRO 覆盖全部六项能力，并同时包含语音与非语音声音（non-speech sound，指语言之外的声音，例如警报、音乐、环境声），而此前基准最多只覆盖两项能力且不含非语音声音；就基准覆盖范围而言，该证据的支持力度很强。
          evidence:: E1, E17
        - 支持结论 C2：探测模式（Probe mode）在每个已知触发点之前和之后进行提问，而在线模式（Online mode）持续输入视频帧、让模型自行判断何时作答；对照对象是固定轮询或预设提问时间的做法；衡量指标为准确率对比 F1 分数（F1 score，即精确率与召回率的调和平均）；差异在于把内容判断和时机判断拆成两项独立测试；就评测协议设计而言，该证据的支持力度很强。
          evidence:: E8
        - 支持结论 C3：对十一个模型进行评测；对照对象是当前的开源系统与闭源商用系统；衡量指标包括平均准确率、F1 分数、音频加视频输入相比仅视频输入带来的增益，以及对晚出现触发点的保持能力；差异体现在具体数字上：Gemini-3-Flash 平均准确率为 40.4，MiniCPM-o 4.5 在线 F1 为 20.9，音频加视频（A+V）带来 2.4 到 11.1 个百分点的增益，长时保持能力平均为 37%；该证据虽为描述性，但覆盖面很广。
          evidence:: E9, E10, E11, E12
    - **主要边界:** 主要注意事项：这套基准最可信的用途，是作为一个英语、以时间触发为核心的诊断工具，用于比较不同模型；它本身并不能证明模型的多语言鲁棒性、在真实部署中的行为，也不能证明其在重复运行下的统计稳定性。
      claim_kind:: analyst_assessment
      evidence:: E9, E14, E16
- ## Argument Map
    - **问题与重要性:** 问题与重要性：本文研究主动式流式视频理解（proactive streaming video understanding），意思是模型必须处理一段持续进行的音画流，并在没有新的用户提问的情况下自行决定何时作答。其重要性在于评测的有效性：一个只提离线问题的基准，可能无法检验未来的助手是否能够正确地察觉、等待并适时插话。
      evidence:: E2, E3
    - **已有方法缺口:** 此前研究的空白：此前的主动式视频基准至少遗漏了一项必需能力的检验：有的只用视觉信息，有的在预设时间点进行轮询或提问，而此前主动性最强的基准也仍然缺少非语音声音和多触发点决策的检验。
      evidence:: E2, E17
    - **关键洞见:** 该领域的基准测试必须把内容答案和作出回应的时刻绑定起来；否则，一个模型可能看起来很擅长识别视频内容，却在真正的交互难题上失败，也就是无法判断该在何时开口回应。
      claim_kind:: analyst_assessment
      evidence:: E3, E8
    - **核心主张:** 本文的核心主张涉及四个方面：覆盖范围、协议分离、诊断性发现以及有限度的复用。
      claim_kind:: analyst_assessment
        - C1：OMNIPRO 填补了一项评测空白，它同时要求处理视听信号、自主判断回应时机，并覆盖全部六种基础的视频理解能力。
          evidence:: E1, E2, E17
        - C2：这套双模式协议把内容理解的评测与在线主动行为的评测分离开来，使得非流式的视觉-语言模型和流式模型可以在不同但相关的条件下接受测试。
          evidence:: E8
        - C3：OMNIPRO 具有区分度：被测模型仍远未达到解决问题的水平，并在模态、触发时刻、生成负担和非语音声音等方面暴露出明显的短板。
          evidence:: E10, E11, E12, E13
        - C4：该数据集经过人工核查，可用于英文主动式流式评测，但由于标注仅限英文，因此对多语言普适性的结论有所限制。
          evidence:: E6, E14
- ## Mechanism and Design
    - **核心机制:** OMNIPRO 把每段视频转化为一条常驻指令，外加若干触发时刻（trigger time，即应当产生回应的时刻），以及带有模态标签的预期回应。同一批样本既支持非流式的内容测试，也支持流式的自主计时测试。
      evidence:: E1, E8
    - **数据/控制流:** 数据流程如下：源视频来自 LongVALE 和 COIN，由 Gemini 3 Flash 生成密集的视听字幕，再进行特定任务的问答合成，经过两轮人工审核，最终得到按任务、模态标签、触发时机和预期回应组织的评测样本。
      evidence:: E4, E5, E6
        - 源视频的选取覆盖了广泛的日常生活、体育、新闻和教学类视频，其中 COIN 用于覆盖类似教程的顺序性指令内容。
          evidence:: E5
        - 字幕生成会随时间记录视觉内容、环境音和语音，随后问答合成会生成常驻指令、触发时刻、回应、触发模态以及音频依赖关系。
          evidence:: E5
        - 人工审核会检查自然度、时机、忠实度以及模态（modality）标注，然后对各子任务进行交叉验证，以减少任务标准不一致的情况。
          evidence:: E6
    - **设计决策:** 几项主要的设计选择让这个基准测试具备诊断能力，而不只是规模更大：优先采用富含音频的触发信号、按认知需求划分任务，并把内容评估与自主时机评估分开进行。
      claim_kind:: analyst_assessment
      evidence:: E3, E4, E8
        - 需求：把全模态（omni-modal）模型与仅视觉模型区分开来；选择：采用「音频优先」的生成策略；最接近的替代方案：仅依据视觉事件来选取样本；权衡：音频方面的诊断能力更强，但数据分布会受到基准测试目的的影响。
          claim_kind:: analyst_assessment
          evidence:: E5, E7
        - 需求：避免做出一个只测试告警的基准测试；选择：把样本按感知、理解、推理三个层次组织起来，覆盖告警、监控、定位、计数、叙述以及类似预测的引导等任务；权衡：覆盖面广，但各任务难度参差不齐。
          claim_kind:: analyst_assessment
          evidence:: E4
        - 需求：把无法进行流式处理的模型也纳入进来，同时在可能的情况下仍测试其主动性；选择：Probe 模式测试已知触发点附近的内容，Online 模式测试自主时机；权衡：两种模式下的分数是彼此关联的诊断结果，而不是一个可以互换的统一排行榜。
          claim_kind:: analyst_assessment
          evidence:: E8
    - **实现边界:** Probe 模式给每个模型输入截至某个查询时刻的累积视频，并对严格结构化的答案打分；Online 模式则连同对话历史一起以帧流形式输入，将模型预测与真实触发点在一个容差窗口内对齐，对生成量较大的任务采用精确匹配或大语言模型评判器（LLM judge，指用来给开放式答案打分的大语言模型）。
      evidence:: E8, E16
        - Probe 模式会在每个触发点前后各提问一次；只有当触发前的探测（pre-probe）为否、触发后的探测（post-probe）给出该任务特定的正确答案时，这个触发点才算判定正确。
          evidence:: E8
        - Online 模式在进行贪心时间匹配后计算精确率、召回率和 F1 分数，默认使用 ±3 秒的响应窗口。
          evidence:: E8, E16
        - 所报告的实验以 1 fps 的帧率对视频采样，并在 NVIDIA A800 80GB GPU 上运行开源模型，采用贪心解码，生成长度上限为 512 个 token。
          evidence:: E9
- ## Evaluation and Evidence
    - **实验设置:** 评估覆盖了专有和开源的全模态（omni-modal）模型、视觉语言模型（VLM，指根据视觉输入和文本作答的模型）以及原生流式模型。Probe 模式报告准确率，Online 模式则在同时检验时机与内容正确性后报告 F1 分数。
      evidence:: E8, E9
    - **主张-证据矩阵:** 证据基础在基准测试覆盖面和诊断广度方面最为扎实，而在统计确定性方面较弱，因为论文只报告了描述性的模型结果，没有给出重复次数、方差或置信区间。
      claim_kind:: analyst_assessment
      evidence:: E1, E9, E10, E11, E12, E13
        - C1：有直接的基准测试构建证据支撑，包括任务分类体系、模态（modality，即视觉画面、语音、非语音声音、文本等信息通道）标签、音频依赖统计，以及与已有基准的比较，这些都表明其覆盖面比以往的主动式视频基准更广。
          claim_kind:: analyst_assessment
          evidence:: E1, E4, E7, E17
        - C2：有 Probe（探测）模式和 Online（在线）模式的形式化定义支撑；剩下需要注意的一点是，Probe 模式和 Online 模式回答的是不同的问题，因此不应把它们的数值分数当作一个统一的指标来解读。
          claim_kind:: analyst_assessment
          evidence:: E8
        - C3：有广泛的模型比较和消融实验支撑，但这种支撑是描述性的而非统计性的，因为论文没有报告多次运行的不确定性。
          claim_kind:: analyst_assessment
          evidence:: E10, E11, E12, E13
    - **关键结果:** 该基准测试表明，当前系统远未把这个问题解决好：报告的最佳 Probe 分数并不高，Online 设置更难，音频加视频通常比只用视频输入效果更好，触发时刻越晚性能下降越明显，而视觉加非语音声音是最弱的触发类别。
      evidence:: E10, E11, E12, E13
        - 整体能力：Gemini-3-Flash 达到 40.4 的平均 Probe 准确率，而 MiniCPM-o 4.5 达到 20.9 的 Online F1 分数；这支持 C3，但缺少报告的不确定性。
          evidence:: E10
        - 模态贡献：在五个全模态模型上，音频加视频（A+V）相比只用视频输入提升了 2.4 到 11.1 个百分点，支持了 C3 关于模态诊断的论点。
          evidence:: E11
        - 时间与音频瓶颈：长期触发平均只保留了短期性能的 37%，而视觉加声音的触发在各模型上得分最低，这支持了 C3 关于长时程和非语音声音的诊断。
          evidence:: E12, E13
    - **消融与敏感性:** 主要的消融实验是模态隔离，它显示音频和视频线索互为补充，且不同模型有不同的融合模式；附录还改变了 Online 模式的时间容忍窗口，并保留 ±3 秒作为默认值。未报告的内容包括：统计不确定性、重复次数，以及在既定的 1 fps 设置之外对帧率的敏感性。
      evidence:: E9, E11, E16
    - **可复现性缺口:** 论文报告了项目主页、源数据集、提示词、硬件类别、采样率、数据集许可证和代码许可证，这些都有助于复用。要做到独立复现，具体的缺口在于：标注者一致性的细节、除已命名的 Gemini 变体之外的确切生成脚本或模型版本，以及模型评测中多次运行的不确定性。
      claim_kind:: analyst_assessment
      evidence:: E5, E6, E9, E15
- ## Technical Judgment
    - **站得住的结论:** 该基准（benchmark）的设计与能力定义相匹配：音视频触发信号、自主决定响应时机、多种任务形式，以及模态隔离标签，这些共同让总分可以被分解开来。最强的技术贡献在于评测框架的设计思路，而不是提出了新的模型或算法。
      claim_kind:: analyst_assessment
      evidence:: E1, E3, E7, E8
    - **可能失效之处:** 当语言、领域分布、时间容差、帧率或评判器（judge）行为发生变化时，通用性可能会减弱。由于问答生成始于 Gemini 产出的字幕描述与合成过程，再经人工筛选，因此该基准既可能反映真实视频的难度，也可能反映其生成流程带来的偏差。
      claim_kind:: analyst_assessment
      evidence:: E5, E6, E9, E14, E16
    - **与已有工作的关系:** 相比 StreamingBench-Pro 和 OVO-Bench-Pro，OMNIPRO 从轮询或预设查询转向了自主决定时机；相比 OmniMMI-Pro，它增加了多触发响应、非语音声音，以及更广的视频理解任务覆盖。
      evidence:: E17
    - **可迁移启发:** 对于交互式模型正在涌现的新能力，应直接对决策边界进行基准测评：明确定义模型应在何时行动、在那一刻有哪些信息可用，以及哪些诊断标签能让失败按输入类型、时间跨度和任务需求切分开来。
      claim_kind:: analyst_assessment
      evidence:: E4, E7, E8
- ## Glossary
  collapsed:: true
    - 全模态主动式流式视频理解（omni-proactive streaming video understanding）：一种场景设定，模型持续观看并聆听一段连续的数据流，自己决定何时响应，并在无需被反复提示的情况下生成正确的内容。
    - 模态（modality）：一种信息通道，例如视觉画面帧、语音、非语音声音或文本。
    - 主动响应（proactive responding）：当数据流值得响应时，模型主动发起回答，而不是等待新的查询或固定的轮询时刻。
    - 触发时刻（trigger time）：被标注出来的、模型应当产生响应的那一刻。
    - 探测模式（Probe mode）：一种非流式的评测模式，在每个被标注的触发点前后对模型进行查询，以检验它是否理解该事件的内容。
    - 在线模式（Online mode）：一种流式评测模式，模型随时间逐帧接收画面，必须自己判断何时作答。
    - 模态隔离标注（modality-isolation label）：一种标注，用于说明检测某个触发点或回答某个样本时，需要或有帮助的输入类型是哪一种。
    - 非语音音频（non-speech audio）：除口头语言之外的音频线索，例如警报声、音乐、口哨声或环境声音。
    - F1 分数（F1 score）：精确率与召回率的调和平均值；在 Online 模式下，只有当响应的时机和内容都正确时才会计入。
    - 长时程感知（long-horizon perception）：指在长视频流中持续保留有用的感知与记忆，从而使视频后段发生的事件仍能被正确检测出来的能力。
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/paper_statement | Abstract | high
      locator:: Abstract
      quote:: We present OMNIPRO, the first benchmark to jointly evaluate omni-modal perception, proactive responding, and diverse video understanding tasks. It comprises 2,700 human-verified samples spanning 9 sub-tasks and 3 cognitive levels, covering 6 basic video understanding capabilities.
    - **E2:** gap/paper_statement | Abstract | high
      locator:: Abstract
      quote:: Existing benchmarks fall short in three key aspects: they rely primarily on visual signals, adopt polling or fixed-timestamp protocols instead of true proactive evaluation, and cover only a limited range of tasks.
    - **E3:** problem/paper_statement | 1 Introduction | high
      locator:: paragraph defining three criteria
      quote:: We argue that such a model must satisfy three key criteria: (1) Omnimodal perception: it should jointly reason over visual signals, speech, and non-speech audio; (2) Proactive responding: it must decide when to respond without external polling or fixed schedules; (3) Diverse video understanding tasks.
    - **E4:** method/paper_statement | 3.1.1 Task Taxonomy | high
      locator:: task taxonomy paragraph
      quote:: We categorize tasks by cognitive ability into three levels, namely Perception, Comprehension, and Reasoning, with increasing difficulty. This yields 9 sub-tasks and 2,700 evaluation samples in total.
    - **E5:** method/implementation_detail | 3.1.2 Source Video Collection and 3.1.3 Automated QA Generation | high
      locator:: source collection and QA synthesis paragraphs
      quote:: Source videos were drawn from the test sets of two public datasets: LongVALE and COIN. For each source video, we employed Gemini 3 Flash to generate temporally aligned multi-modal dense captions with start and end timestamps for each segment.
    - **E6:** method/paper_statement | 3.1.4 Human Quality Control | high
      locator:: human review paragraph
      quote:: The auto-generated data underwent two rounds of human review. In the first round, 9 annotators each reviewed one sub-task using a dedicated tool, verifying question naturalness, trigger time accuracy, response faithfulness, and modality annotation correctness.
    - **E7:** metadata/paper_statement | 3.1.5 Dataset Statistics | high
      locator:: Figure 2 discussion
      quote:: Figure 2b breaks down the trigger modality composition, revealing that visual+speech is the dominant type and nearly half of all triggers exhibit cross-modal characteristics. Figure 2d depicts the distribution of first and last trigger times: the average first trigger occurs at 54.1 s and the last at 126.2 s.
    - **E8:** method/paper_statement | 3.2.1 Evaluation Protocol | high
      locator:: Probe and Online mode definitions
      quote:: Probe mode is compatible with any VLM and does not require streaming capability. For each ground-truth trigger, the evaluator queries the model twice: a pre-probe and a post-probe. Online mode targets streaming models. The model receives the user instruction at the start of the video, then processes subsequent frames one by one.
    - **E9:** experiment_setup/paper_statement | 4.1 Experimental Settings | high
      locator:: evaluated models and implementation details
      quote:: We evaluate 11 representative models spanning two evaluation modes. In Probe mode, we assess 9 models. In Online mode, we evaluate 3 streaming models. All models uniformly sample input video at 1 fps. All open-source model inference is conducted on NVIDIA A800 80GB GPUs.
    - **E10:** result/experiment_result | 4.2 Using OMNIPRO for Assessing Overall Model Capability | medium
      locator:: Table 2 discussion
      quote:: Gemini-3-Flash attains 40.4% average accuracy, nearly double the best open-source model (22.1%), indicating a substantial capability gap. Online mode is considerably harder: MiniCPM-o 4.5 reaches only 20.9% F1, with severe degradation on generation-intensive tasks.
    - **E11:** result/ablation | 4.3 Using OMNIPRO for Disentangling Modality Contributions | medium
      locator:: Table 3 discussion
      quote:: A+V consistently outperforms either single modality, with gains over V ranging from +2.4 (Qwen3-Omni) to +11.1 (video-SALMONN 2+), confirming that the two modalities provide complementary cues.
    - **E12:** result/experiment_result | 4.4 Using OMNIPRO for Evaluating Long-Horizon Perception | medium
      locator:: Figure 3 discussion
      quote:: All models show substantial degradation for later-occurring triggers, retaining on average only 37% of their Short-term performance at the Long-term. MiniCPM-o 4.5 nearly fails entirely on the Long-term (29.1 to 0.3).
    - **E13:** result/experiment_result | 4.5 Using OMNIPRO for Identifying Modality Bottlenecks | medium
      locator:: Figure 4 discussion
      quote:: All models perform weakest on visual+sound triggers (15.3-22.3), revealing that perceiving and utilizing non-speech audio (e.g., environmental sounds, sound effects) remains a shared bottleneck.
    - **E14:** limitation/limitation | C.1 Limitations | high
      locator:: limitations paragraph
      quote:: All questions and ground-truth annotations in OMNIPRO are written in English, which limits its applicability for evaluating multilingual or non-English proactive streaming models. Extending the benchmark to additional languages is left for future work.
    - **E15:** metadata/paper_statement | C.3 Licenses | high
      locator:: license list
      quote:: LongVALE: CC-BY-NC-SA-4.0. COIN: CC BY-NC 4.0. OMNIPRO (our benchmark): CC BY-NC 4.0. Evaluation code: MIT License.
    - **E16:** ablation/ablation | A.1 Tolerance Window Ablation | medium
      locator:: Figure 5 discussion
      quote:: Figure 5 shows the effect of varying the temporal matching tolerance on joint_F1 for three online-mode models. The tolerance window ranges from ±1 s to ±5 s. We adopt ±3 s as the default in all Online-mode evaluations.
    - **E17:** prior_work/paper_statement | 2.2 Proactive Streaming Video Benchmarks | high
      locator:: summary of prior benchmarks
      quote:: In summary, no existing benchmark simultaneously satisfies all three criteria: none involves non-speech sound, only OmniMMI-Pro supports proactive responding, limited to single-trigger, and at most 2/6 capabilities are covered.
