- **标题:** STREAMINGVLM：无限视频流的实时理解
- **一句话总结:** StreamingVLM 表明，通过将 overlapped-chunk SFT 与推理时的 KV cache 复用、attention sink、近期的 text/vision 窗口以及有界的 contiguous RoPE 相结合，可以使长时序实时视频理解变得切实可行。
- **论文类型:** 系统
- **发表:** ICLR 2026; arXiv:2510.09608v2
- **作者:** Ruyi Xu* (MIT), Guangxuan Xiao* (MIT), Yukang Chen (NVIDIA), Liuning He (MIT), Yao Lu (NVIDIA), Song Han (MIT/NVIDIA)
- **关键词:** streaming VLM, 无限视频, KV cache, attention sink, 滑动窗口注意力, contiguous RoPE, 视频描述, 体育解说
- ## Quick Reference
    - **阅读价值:** 将有限上下文 VLM 转化为低延迟流式视频解说员的具体方案：使用短重叠片段进行训练，然后在推理时使用可复用的紧凑 KV state，而不是重新计算重叠窗口。
      claim_kind:: analyst_assessment
      evidence:: E2, E3, E5, E14
    - **一句话贡献:** StreamingVLM 通过在重叠的交错视频-文本片段上微调 Qwen2.5-VL-7B，并使用 attention sink 加上近期的 text/vision KV 复用与 contiguous RoPE 进行服务，从而改进了实时无限流视频描述。
      evidence:: E3, E4, E5, E9
    - **记忆模型:** 一个滚动的解说员笔记本：固定开头的指令，保留最新的转录文本，只保留最近的视觉瞬间，并对剩余页面重新编号，从而使模型永远不会看到超出范围的位置。
      claim_kind:: analyst_assessment
    - **最佳证据:** 最有力的证据是长场比赛配对描述胜率、恒定的 per-token 延迟以及无需 VQA 特定微调的 VQA 迁移表现的结合。
      evidence:: E11, E13, E14
        - C1：在 Inf-Streams-Eval 上，StreamingVLM 的 infinite 模式相对于 GPT-4o mini 100 秒 chunk 模式的胜率为 66.18%，相对于 LiveCC chunk 模式为 87.81%，相对于 LiveCC infinite 模式为 99.12%。
          evidence:: E7, E11
        - C2：在延迟测试中，StreamingVLM 在处理 1000 秒视频期间保持约 0.05 s/token 的速度，并据报道可在单块 NVIDIA H100 上支持 8 FPS 实时解说。
          evidence:: E14
        - C3：在不使用 VQA SFT 的情况下，StreamingVLM 在 LongVideoBench 上从 54.70 提升至 59.00，在 OVOBench Realtime 上从 56.00 提升至 61.96。
          evidence:: E13
    - **主要边界:** 可信度在 LLM-as-judge 协议下的英文体育解说场景中最高；更广泛的视频领域、人类偏好验证、不同 judge/run 之间的方差，以及 GPT-5 清洗/评判的精确可复现性在所供文本中证据较弱。
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E10
- ## Argument Map
    - **问题与重要性:** 本文针对必须处理近无限视频流并实时响应的 VLM，要求延迟和内存不随流长度增长。其利害关系涉及实用助手、具身智能体和自主系统——在这些场景中，full attention 是二次/无界的，而朴素的 sliding window 要么丢失连贯性，要么重计算开销过大。
      evidence:: E2
    - **已有方法缺口:** 现有视频 VLM 主要处理有限片段，而文本侧的 streaming/KV eviction 方法不能直接解决跨模态训练-推理不匹配问题。本文论证在超长视频上训练不可行，因此短上下文训练过程必须复现测试时使用的 recency 和 cache 结构。
      evidence:: E2, E18
    - **关键洞见:** 在 SFT 中近似流式推理的 attention pattern，而非在完整长视频上训练：使用重叠的 full-attention chunk，以每秒间隔交替 vision/text，推理时再使用紧凑可复用的 KV cache 和有界位置索引。这使模型期望在线 eviction 后保留下来的同类上下文。
      evidence:: E3, E4, E5
    - **核心主张:** 本文支持四个主要可证伪声明：更长流的字幕质量更优、实时稳定推理、迁移至 VQA，以及所提出 cache/position/training 设计选择的必要性。
      evidence:: E11, E13, E14, E15
        - C1：StreamingVLM 在长时段体育字幕任务上有所提升，在 Inf-Streams-Eval 上相对于 GPT-4o 的 chunk 模式取得 66.18% 的胜率，相对于 LiveCC chunk 模式取得 87.81% 的胜率。
          evidence:: E11
        - C2：复用固定保留上下文的 KV 在推理时保持实时性，据报告通过 1000 秒仍达 0.05 s/token，并在单块 H100 上支持 8 FPS。
          evidence:: E14
        - C3：Streaming SFT 在无需针对 VQA 专项微调的情况下即可改善通用视频问答，尤其在长时序和实时基准上表现突出。
          evidence:: E13
        - C4：Contiguous RoPE、近期视觉保留以及 overlapped/data-curated SFT 是实质性贡献因素，而非表面性的工程细节。
          evidence:: E15, E16, E17
- ## Mechanism and Design
    - **核心机制:** StreamingVLM 维护一个紧凑的 KV cache，其中包含 attention-sink 文本 token、近期文本窗口和近期视觉窗口；较早的视觉信息优先被驱逐，文本历史则以非对称方式保留以维持话语连贯性。Figure 3 中报告的默认配置为 512 个 sink token、512 个近期文本 token 和 16 秒的近期视觉。
      evidence:: E3
    - **数据/控制流:** 系统首先通过 ASR 和 GPT 清洗构建对齐的体育视频/解说流，然后在 overlapped 的 24 s/12 s 分块上以逐秒交错的 V/T token 进行训练，最终在实时流服务中通过追加新状态、驱逐窗口外 token 并平移 RoPE 索引来完成推理。训练中使用的前序文本被压缩为开头的 T_sink 和末尾的 T_window token，以匹配推理过程。
      evidence:: E5, E6, E7
        - 数据准备阶段在五项体育运动上使用 WhisperX ASR，通过 GPT-5 进行 keep/edit/delete 清洗，并设有独立的 SFT/evaluation/annealing 分段流水线。
          evidence:: E6, E7, E8
        - SFT 在短 overlapped 分块内部使用 full attention，仅对齐的文本位置计算 loss，对无解说的秒数使用占位符。
          evidence:: E5, E7
        - 在线推理通过复用保留的 sink/text/vision token 的缓存 KV 来避免对重叠窗口的重复计算，并在驱逐后分配连续位置索引。
          evidence:: E3, E4
    - **设计决策:** 三项主要设计选择为非对称缓存保留、contiguous RoPE 和 overlapped-chunk SFT；每一项都直接针对 full attention 或朴素滑窗的某种失效模式。最接近的已测替代方案包括 native RoPE、ReKV 式驱逐、无窗口或改动窗口、以及非重叠或较弱数据的训练。
      evidence:: E12, E15, E16, E17
        - 需求：在约束计算量的同时保留话语连贯性；选择：sink 加长文本窗口加短视觉窗口；权衡：模型只有在旧视觉事实以文本或 sink 类上下文形式留存时才能加以利用。
          claim_kind:: analyst_assessment
          evidence:: E3, E16
        - 需求：避免多次驱逐后位置索引超出分布范围的持续增长；选择：左移 contiguous RoPE，包括 Qwen-VL 视觉 token 的 3D RoPE；已测替代方案 native RoPE 在 infinite mode 下性能急剧下降。
          evidence:: E4, E15
        - 需求：在不进行 quadratic 长上下文训练的前提下教会模型 streaming 行为；方案：以一秒为间隔交错 V/T 的 overlapped full-attention chunks；所报告的消融实验表明非重叠方案效果更差。
          evidence:: E5, E17
    - **实现边界:** 论文报告的实现分两阶段 fine-tune Qwen2.5-VL-Instruct-7B：525K Inf-Streams SFT 样本加 526K Live-WhisperX 样本，随后是 14K 高质量 annealing 样本，共耗费约 128 H100-days。论文提供了公开 GitHub URL，但对 cache/RoPE 行为的算法细节描述多于底层 kernel 或 serving-stack 细节。
      evidence:: E1, E9
- ## Evaluation and Evidence
    - **实验设置:** Captioning 在 Inf-Streams-Eval 上评估，该 benchmark 包含 20 场比赛，平均每场 2.12 小时，另加 Livecc-Sports-3K CC；commentary 的成对质量由 GPT-5 参考 references 评判。VQA transfer 在 VideoMME、MVBench、LongVideoBench 和 OVOBench 上评估，GPT-4o mini 仅在 Inf-Streams-Eval 上以 chunk mode 评估。
      evidence:: E7, E10
    - **主张-证据矩阵:** 证据以实证为主：captioning 的 win-rate 表格、VQA 的 accuracy 表格、serving 的 latency traces，以及对 RoPE/cache/data/training strategy 的消融实验。最强支撑来自论文自身 sports-streaming 设定下的集成系统。
      claim_kind:: analyst_assessment
      evidence:: E11, E13, E14, E15
        - C1 captioning 质量：由 Inf-Streams-Eval 和 Livecc-Sports-3K 的 win rate 支撑，但需注意 GPT-4o mini 仅在 Inf-Streams-Eval 上以 100 s chunk mode 评估。
          claim_kind:: analyst_assessment
          evidence:: E10, E11
        - C2 实时效率：由随处理视频长度增加的 per-token latency 以及报告的 single-H100 8 FPS 设定支撑。
          evidence:: E14
        - C3 VQA transfer：通过与 Qwen2.5-VL-7B-Instruct base model 在四个公开 video QA 套件上的直接对比支撑。
          evidence:: E13
        - C4 组件必要性：由以下消融实验支撑：native 与 contiguous RoPE 对比、visual/text windows 与 sink size、Live-WhisperX 与 Inf-Streams 数据对比、annealing 数据，以及 overlap strategy。
          evidence:: E15, E16, E17
    - **关键结果:** 核心结论是 StreamingVLM 在长 sports streams 上超越强 captioning baselines，同时保持 latency 平稳，且同一 SFT 改善了部分通用 video QA 指标。最重要的 caveat 是 captioning 指标采用成对 LLM 评判，而非带统计不确定性的人工评估。
      claim_kind:: analyst_assessment
      evidence:: E7, E11, E13, E14
        - Captioning：StreamingVLM^infinity 在 Inf-Streams-Eval 上报告 66.18% win rate vs GPT-4o^dagger、87.81% vs Livecc^dagger、99.12% vs Livecc^infinity。
          evidence:: E11
        - 效率：延迟曲线显示 StreamingVLM 在 1000 秒内保持 0.05 s/token，而 full attention 超出限制/OOM，overlapping windows 仍然低效。
          evidence:: E14
        - VQA：相对于 Qwen2.5-VL-7B-Instruct，StreamingVLM 在 MVBench 上提升 1.82，LongVideoBench 上提升 4.30，OVOBench Realtime 上提升 5.96，而 VideoMME 保持 65.10。
          evidence:: E13
    - **消融与敏感性:** 对于一篇系统风格的 VLM 论文而言，这些消融实验 unusually diagnostic：它们测试了 position extrapolation、retained-context allocation、训练数据和训练/推理一致性。结果表明该系统不仅仅是 cache trick；模型行为取决于在训练时见到与推理时相同的 interleaved streaming context。
      claim_kind:: analyst_assessment
      evidence:: E12, E15, E16, E17
        - RoPE：native infinite inference 对 GPT-4o^dagger 的胜率降至 25.09%，而 contiguous infinite inference 达到 66.18%，支持了有界位置这一论点。
          evidence:: E15
        - Windows：移除 visual context 会损害性能，论文确定 16 秒为合适的 visual window；附录 A.3 指出 sink size 影响性能，在更大尺寸时趋于 plateau。
          evidence:: E16
        - Data/strategy：对 GPT-4o^dagger 的胜率从 Live-WhisperX 的 32.17 上升到 Inf-Streams-Train 的 63.46，并经高质量 annealing 后达到 66.18；论文还报告 overlap 优于 non-overlap。
          evidence:: E17
    - **可复现性缺口:** 论文提供了 GitHub URL、模型基座、样本数量、计算预算及主要 benchmark 设置，但所供文本未提供随机种子、重复次数、统计不确定性、完整的 judging/cleaning prompts，或足够的底层服务细节以独立审计延迟。复用该数据 pipeline 还可能取决于完整体育视频的访问/许可以及专有 GPT-5 judging/cleaning 行为。
      claim_kind:: analyst_assessment
      evidence:: E1, E6, E7, E9, E14
- ## Technical Judgment
    - **站得住的结论:** 核心系统思路是可信的，因为它直击实际的服务瓶颈：overlapping-window 的重复计算被固定大小的 KV 复用取代，同时 contiguous RoPE 阻止了 retained cache 承载不断增长的位置。消融证据与该机制一致：native RoPE 在 infinite mode 下崩溃，ReKV 破坏了 fine-tuned 的 context 格式，而延迟曲线仅在所提 cache policy 下保持平稳。
      claim_kind:: analyst_assessment
      evidence:: E3, E4, E12, E14, E15
    - **可能失效之处:** 该方法可能在需要精确检索从未被 verbalized 为 retained text 的旧视觉证据的任务上失败，因为其设计有意仅保留近期 vision tokens。在英语体育直播和 LLM-judge 解说之外的泛化性也不确定，因为主数据/评测 pipeline 以体育为核心，且 window size 是对场景敏感的超参数。
      claim_kind:: analyst_assessment
      evidence:: E3, E6, E7, E16
    - **与已有工作的关系:** 在技术上，StreamingVLM 最接近 StreamingLLM 式的 attention sinks 加 sliding windows，但将该方案扩展到跨模态的 interleaved vision/text streams 和 3D contiguous RoPE。与 ReKV 等免训练 KV 驱逐方法相比，论文的核心区别在于训练-推理对齐：模型被 fine-tuned 以期望与 serving 保持相同的 cache 格式。
      claim_kind:: analyst_assessment
      evidence:: E12, E18
    - **可迁移启发:** 对于流式 foundation-model 系统，不要将缓存驱逐视为仅与推理相关的优化：应先确定保留状态的接口设计，再使用短合成上下文进行训练，使这些上下文的注意力模式逼近该接口形式。当模型在无界流上使用相对/旋转位置编码时，有界的位置索引属于该接口设计的一部分，而非实现阶段的补充。
      claim_kind:: analyst_assessment
      evidence:: E4, E5, E15, E17
- ## Glossary
  collapsed:: true
    - Attention sink / T_sink：在 KV cache 中保留的早期文本 token，包括 system 和之前的文本，用于在长时间的流式推理中稳定注意力。
    - T_window：流式 KV cache 中保留的近期文本 token 窗口；旨在以压缩的文本形式保留话语与长期记忆。
    - V_window：流式 KV cache 中保留的近期视觉 token 窗口；报告的默认值覆盖 16 秒视频。
    - Contiguous RoPE：一种位置索引方案，在驱逐后将 RoPE 索引左移，使保留的 token 与新进入的 token 保持连续且有界，而非随总流长度增长。
    - Overlapped-chunk SFT：一种训练策略，将流切分为重叠的短 chunk，在每个 chunk 内施加 full attention，并以一秒间隔交替插入 vision/text，以模拟流式推理。
    - Inf-Streams-Eval：论文提出的长流体育解说 benchmark：20 圠完整比赛，平均时长 2.12 小时，使用 GPT-5 带参考答案的成对投票进行评估。
    - Chunk mode vs. infinite mode：Chunk mode 以独立固定分段方式处理，附带之前的文本；infinite mode 在整条流上连续运行，同时复用过去的 KV/输出状态。
    - Win rate：在 pairwise LLM-as-judge 评估中模型 A 相对模型 B 的偏好占比；越高越好，但结果取决于 judge model、参考答案和 prompt 协议。
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/metadata | Title block | high
      locator:: paper header
      quote:: arXiv:2510.09608v2 [cs.CV] 31 May 2026. Published as a conference paper at ICLR 2026. STREAMINGVLM: REAL-TIME UNDERSTANDING FOR INFINITE VIDEO STREAMS. Ruyi Xu, Guangxuan Xiao, Yukang Chen, Liuning He, Yao Lu, Song Han. MIT, NVIDIA. https://github.com/mit-han-lab/streaming-vlm
    - **E2:** problem/paper_statement | Abstract and Introduction | high
      locator:: Abstract; Section 1
      quote:: VLMs could power real-time assistants and autonomous agents, but they face a critical challenge: understanding near-infinite video streams without escalating latency and memory usage. Processing entire videos with full attention leads to quadratic computational costs and poor...
    - **E3:** system_design/implementation_detail | 2.1 Inference Scheme of Streaming VLM | high
      locator:: Figure 3; Streaming-aware KV Cache
      quote:: We keep 512 attention-sink tokens to stabilize attention, a long text window of 512 recent tokens to preserve long-term memory, and a short vision window covering 16 seconds to track ongoing actions. The key idea is to maintain a compact and stable KV cache by reusing previous...
    - **E4:** optimization/implementation_detail | 2.1 Inference Scheme of Streaming VLM | high
      locator:: Contiguous RoPE paragraph
      quote:: When earlier tokens are removed, the RoPE indices of subsequent and incoming tokens are shifted so that their positions remain numerically contiguous with the last retained token. Once the video length surpasses the total window size, the effective RoPE indices stop growing an...
    - **E5:** method/paper_statement | 2.2 Training Strategy | high
      locator:: overlapped-chunk full-attention description
      quote:: We split a long video stream into consecutive chunks of length W frames, with temporal overlap O frames between C_i and C_{i+1}. Each chunk is treated as a training instance in which vision and text tokens are sampled and interleaved at 1 s intervals. We apply full attention w...
    - **E6:** experiment_setup/paper_statement | 2.3.1 Video Collection and ASR; 2.3.2 Data Cleaning | high
      locator:: data pipeline
      quote:: We collected game videos from five sports: basketball, soccer, ice hockey, baseball, and American football... obtaining an initial corpus of videos with a total duration of over 6,000 hours. We set rules and used GPT to clean these data... 46.32% were kept, 37.89% were edited,...
    - **E7:** experiment_setup/paper_statement | 2.3.3 SFT and Evaluation Data Segmentation | high
      locator:: SFT and Inf-Streams-Eval construction
      quote:: Under the training setup in Section 2.2, we split videos with W = 24 s and O = 12 s... For evaluation, we create a new benchmark, Inf-Streams-Eval. It contains 20 full games with an average length of 2.12 hours... For scoring, a larger model (we use gpt-5) votes between two mo...
    - **E8:** method/paper_statement | 2.3.4 High-Quality Annealing Data | high
      locator:: annealing data construction
      quote:: We first slice all data without overlap, requiring each clip to be 16–64 seconds long with internal silence no longer than 3 seconds... Across all games, we obtained 52,530 new samples. Then... GPT-5 [determines] whether the proportion of real-time commentary exceeds 80%... on...
    - **E9:** experiment_setup/paper_statement | 3.1 Experimental Setup | high
      locator:: Training paragraph
      quote:: We fine-tune StreamingVLM from Qwen2.5-VL-Instruct-7B. Step 1 teaches the model the infinite streaming inference pattern. We train on our SFT set (525K streaming samples) and on LiveCC's Live-WhisperX-526K (526K streaming samples). Step 2 uses our high-quality annealing data (...
    - **E10:** experiment_setup/paper_statement | 3.1 Experimental Setup | high
      locator:: Baselines and Benchmark paragraphs
      quote:: Due to design limits, GPT-4o mini is evaluated on Inf-Streams-Eval in the chunk setting, not the infinite mode used by StreamingVLM. LiveCC7B-Instruct is tested in both chunked and infinite settings... For video understanding, we evaluate StreamingVLM on four public suites: Vi...
    - **E11:** result/experiment_result | 3.2.1 Captioning | high
      locator:: Table 1
      quote:: Table 1 reports StreamingVLM^infinity on Inf-Streams-Eval with win rates 66.18 against GPT-4o^dagger, 87.81 against Livecc^dagger, and 99.12 against Livecc^infinity. On Livecc-Sports-3K cc it reports 47.33 against LLaVA, 45.59 against GPT-4o, 44.21 against Gemini, and 56.19 ag...
    - **E12:** result/experiment_result | 3.2.1 Captioning | high
      locator:: Table 2; ReKV comparison
      quote:: We observe a paradox for training-free ReKV: models without task-specific fine-tuning perform poorly, yet models that are specially fine-tuned rely on a fixed context format that ReKV's eviction policy disrupts, often yielding no output. Table 2 reports StreamingVLM (+ReKV) wi...
    - **E13:** result/experiment_result | 3.2.2 VQA | high
      locator:: Table 3
      quote:: Without any VQA fine-tuning, StreamingVLM delivers consistent accuracy gains across all tasks. Table 3 reports Qwen-2.5-VL-7B-Instruct at 67.34, 65.10, 54.70, 56.00 on MVBench, Video MME, LongVideoBench, OVOBench Realtime, and StreamingVLM at 69.16, 65.10, 59.00, 61.96.
    - **E14:** result/experiment_result | 3.3 Efficiency Tests | high
      locator:: Figure 7 and efficiency paragraph
      quote:: Figure 7 reports per-token latency versus video length. Full attention soon exceed the limit and OOM... Streaming VLM keeps fixed context length and reuses KV, maintains lower and stable latency, and supports real-time commentary at 8 FPS on a single NVIDIA H100. The table sho...
    - **E15:** ablation/ablation | 3.4.1 Contiguous RoPE | high
      locator:: Table 4
      quote:: Native RoPE degrades sharply on infinite streams because its index grows fast and exceeds the training range. Table 4 reports Native^infinity at 25.09 against GPT-4o^dagger, 59.42 against Livecc^dagger, and 60.32 against Livecc^infinity, while Contiguous^infinity reaches 66.18...
    - **E16:** ablation/ablation | 3.4.2 Sliding Window and Sink; A.3 Sensitivity Analysis | high
      locator:: Table 5; Table 8
      quote:: The right table in Table 5 shows that a 16 s visual window is a good choice... keeping 0 s of vision context leads to a clear drop. Appendix A.3 states that sink token size noticeably impacts final performance, generally larger T_sink capacities yield better win rates, and gai...
    - **E17:** ablation/ablation | 3.4.3 Training Strategy and Dataset | high
      locator:: Table 6 and Table 7
      quote:: Compared with a model trained only on Live-WhisperX-526K, training on the overlapped SFT data strengthens perception of infinite video, yielding clear gains +31.29 on Inf-Streams-Eval. Table 6 reports 32.17, 63.46, and 66.18 win rate against GPT-4o^dagger for Live-WhisperX, +I...
    - **E18:** prior_work/paper_statement | 4 Related Work | high
      locator:: Long-context and streaming inference; streaming video LLMs
      quote:: The text community has proposed attention sink + sliding window, RoPE extension and continuity, and KV cache compression/eviction such as H2O, SnapKV, and ReKV. However, these methods are mostly tested on text, and alignment between streaming training and inference remains und...
