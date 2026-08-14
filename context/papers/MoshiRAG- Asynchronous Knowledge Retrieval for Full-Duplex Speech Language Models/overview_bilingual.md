- **Title:** MoshiRAG: Asynchronous Knowledge Retrieval for Full-Duplex Speech Language Models
  **标题:** MoshiRAG：面向全双工语音语言模型的异步知识检索
- **Summary:** MoshiRAG shows that a full-duplex speech language model can improve factual answers by starting external retrieval during the natural lead-in of a spoken response while keeping real-time interaction mostly intact.
  **一句话总结:** MoshiRAG 表明，全双工语音语言模型可以在口语回答的自然开场部分启动外部检索，从而改善事实性回答，同时基本保持实时交互不受影响。
- **Paper Type:** system
  **论文类型:** 系统
- **Venue:** arXiv preprint 2026
  **发表:** arXiv 预印本 2026
- **Authors:** Chung-Ming Chien (Toyota Technological Institute at Chicago; Kyutai), Manu Orsini (Kyutai), Eugene Kharitonov (Kyutai; Gradium), Neil Zeghidour (Kyutai; Gradium), Karen Livescu (Toyota Technological Institute at Chicago), Alexandre Defossez (Kyutai; Gradium)
  **作者:** Chung-Ming Chien（Toyota Technological Institute at Chicago；Kyutai）、Manu Orsini（Kyutai）、Eugene Kharitonov（Kyutai；Gradium）、Neil Zeghidour（Kyutai；Gradium）、Karen Livescu（Toyota Technological Institute at Chicago）、Alexandre Defossez（Kyutai；Gradium）
- **Keywords:** full-duplex speech language models, retrieval-augmented generation, asynchronous retrieval, speech question answering, real-time voice agents, tool use
  **关键词:** 全双工语音语言模型、检索增强生成、异步检索、语音问答、实时语音智能体、工具使用
- ## Orientation
    - **Background:** Voice assistants can wait for a turn to finish or keep listening while speaking. The latter is full-duplex speech modeling: the model handles incoming and outgoing audio at the same time.
      **背景:** 语音助手可以等一方说完再回应，也可以在自己说话的同时继续倾听。后者就是全双工语音建模（full-duplex speech modeling）：模型同时处理接收进来的音频和发送出去的音频。
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A spoken assistant can sound fast and natural but still answer factual questions poorly, because speech training carries less world knowledge than text.
      **通俗问题:** 语音助手可以听起来反应快、说话自然，但在回答事实性问题时仍然表现不佳，因为语音训练所携带的世界知识比文本训练要少。
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** The assistant cannot simply stop talking whenever it needs knowledge; if the lookup finishes late, the useful part of the spoken answer has already passed.
      **为何困难:** 助手不能一需要查资料就干脆停下来不说话；如果查询完成得太晚，语音回答中有价值的那部分内容早就已经说完了。
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Start with safe lead-in speech, fetch outside knowledge in parallel, then inject that knowledge before the answer reaches its substance.
      **一句话核心思路:** 先说一段安全的引导话语，同时并行地去获取外部知识，然后在回答进入实质内容之前把这些知识注入进去。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a speech-systems view of retrieval-augmented generation, meaning fetching outside text before answering, for the gap where a voice assistant must keep listening and speaking while it looks up facts.
      **阅读价值:** 把这篇论文当作从语音系统角度看待检索增强生成（即在回答前先获取外部文本）的研究，它针对的问题是：语音助手在查找事实的同时，必须持续地听和说。
      claim_kind:: analyst_assessment
      evidence:: E1, E2
    - **One-Sentence Contribution:** MoshiRAG improves factual answering in real-time spoken conversation by predicting when a question needs outside knowledge and using the response's lead-in time to fetch that knowledge before the important answer words arrive.
      **一句话贡献:** MoshiRAG 通过预测某个问题何时需要外部知识，并利用回答开场的这段时间在关键答案词到来之前把知识取回来，从而改善实时口语对话中的事实性回答。
      evidence:: E1, E3
    - **Mental Model:** Picture a speaker who starts with a harmless opening phrase while an assistant silently fetches a note, then folds the note into the rest of the answer without stopping the conversation.
      **记忆模型:** 设想一位说话者先用一句无关紧要的开场白起头，与此同时助手在后台悄悄取回一条笔记，然后把这条笔记融入回答的其余部分，整个过程不中断对话。
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is the combination of speech question-answering gains, maintained full-duplex behavior, and backend swaps that improve accuracy without retraining the speech model.
      **最佳证据:** 最有力的证据是三点的结合：语音问答性能的提升、全双工行为的保持，以及在不重新训练语音模型的情况下通过替换后端来提高准确率。
      evidence:: E9, E11, E12
        - Supports C1: Gemma 3 27B retrieval backend; baselines are vanilla Moshi and RAG-data fine-tuned Moshi; metric is response accuracy on speech QA; WebQ reaches 74.7 versus 26.6 and 37.0, and HaluEval reaches 36.3 versus 10.5 and 18.7; support status is positive but judge-based.
          支持论点 C1：使用 Gemma 3 27B 作为检索后端；对比基线是原始的 Moshi，以及在 RAG 数据上微调过的 Moshi；评价指标是语音问答的回答准确率；WebQ 上达到 74.7，而两个基线分别为 26.6 和 37.0，HaluEval 上达到 36.3，而两个基线分别为 10.5 和 18.7；支持结论为正面，但依赖于评判模型给出的判断。
          evidence:: E9
        - Supports C2: Full-Duplex-Bench evaluation; baseline is vanilla Moshi; metrics include pause takeover rates and interruption quality; MoshiRAG lowers synthetic pause TOR to 0.32 from 0.99 and scores 3.75 on interruption GPT score versus 0.77; support status is positive but benchmark-limited.
          支持论点 C2：采用 Full-Duplex-Bench 评测；基线是原始的 Moshi；指标包括停顿接管率和打断质量；MoshiRAG 把合成停顿的接管率（TOR）从 0.99 降到 0.32，在打断的 GPT 评分上得到 3.75，而基线为 0.77；支持结论为正面，但受限于该基准测试本身。
          evidence:: E11
        - Supports C3: same trained MoshiRAG paired with different retrievers; baseline is the default Gemma backend; metric is response accuracy; GPT-4.1 improves TriviaQA from 73.2 to 82.9 and HaluEval from 36.3 to 51.3; support status is positive for backend modularity.
          支持论点 C3：同一个训练好的 MoshiRAG 搭配不同的检索器；基线是默认的 Gemma 后端；指标是回答准确率；GPT-4.1 把 TriviaQA 从 73.2 提升到 82.9，把 HaluEval 从 36.3 提升到 51.3；这为后端可替换（模块化）提供了正面支持。
          evidence:: E12
    - **Main Caveat:** The design is only as strong as its transcript, trigger, retriever, and timing: the paper shows response quality drops with automatic speech recognition errors, imperfect reference integration, and retrieval delays beyond the useful window.
      **主要边界:** 该设计的效果完全取决于它的转录文本、触发时机、检索器和时序：论文表明，当出现自动语音识别错误、参考信息整合不完善，以及检索延迟超出有用时间窗口时，回答质量都会下降。
      claim_kind:: analyst_assessment
      evidence:: E14, E15, E16
- ## Argument Map
    - **Problem and Stakes:** Full-duplex speech language models, which listen and speak concurrently, are valuable because they preserve interruption handling and fast feedback, but the paper argues their factual question answering is weak and cannot be fixed only by making the real-time speech model larger.
      **问题与重要性:** 全双工语音语言模型（full-duplex speech language model）能一边听一边说，其价值在于既能处理打断，又能给出快速反馈；但论文认为，这类模型在事实性问答上表现较弱，而且仅靠把实时语音模型做得更大是无法解决这个问题的。
      evidence:: E1, E2
    - **Prior Gap:** Earlier speech retrieval systems either avoid the full-duplex setting, depend on fixed pre-indexed corpora, or repeatedly call a large language model, meaning a text model trained to predict and generate text, on a schedule that can waste computation and ignore conversational need.
      **已有方法缺口:** 早期的语音检索系统要么回避了全双工这一场景，要么依赖固定的预先建好索引的语料库，要么按固定的时间安排反复调用大语言模型（即一种经过训练、用来预测和生成文本的文本模型），而这样的时间安排既可能浪费算力，又忽视了对话本身的实际需要。
      evidence:: E17
    - **Key Insight:** The paper's systems insight is that spoken answers usually contain a lead-in before the answer-bearing words, and this time can hide retrieval latency if the model predicts a retrieval trigger early enough.
      **关键洞见:** 本文在系统层面的洞见是：口语回答通常在真正给出答案的词之前会先有一段引入语，如果模型能够足够早地预测出检索触发信号，这段引入时间就能把检索延迟隐藏起来。
      evidence:: E2, E3
    - **Claims:** The paper's claim chain has four falsifiable parts: factuality improves, interaction remains full-duplex, backend changes transfer without retraining, and the same retrieval interface can act like a tool on unseen reasoning tasks.
      **核心主张:** 本文的论证链由四个可证伪的部分组成：事实准确性得到提升；交互保持全双工；更换后端无需重新训练即可迁移；以及同一套检索接口能在未见过的推理任务上像工具一样发挥作用。
      claim_kind:: analyst_assessment
        - C1: MoshiRAG improves factual response accuracy over vanilla Moshi and over a vanilla Moshi fine-tuned on the same RAG-style synthetic data, so the gain is attributed to retrieval use rather than only training-data style.
          C1：MoshiRAG 在事实性回答准确率上优于原版 Moshi，也优于在相同的 RAG 风格合成数据上微调过的原版 Moshi，因此这一提升归因于对检索的使用，而不仅仅是训练数据的风格。
          evidence:: E9
        - C2: MoshiRAG preserves the real-time interaction profile expected from full-duplex systems because retrieval runs asynchronously while the speech front end continues to process incoming and outgoing audio.
          C2：MoshiRAG 保持了全双工系统应有的实时交互特征，因为检索是异步运行的，与此同时语音前端仍在持续处理输入和输出的音频。
          evidence:: E3, E10, E11
        - C3: The system is retrieval-backend agnostic because the trained speech model consumes textual references and can benefit from stronger large-language-model or search backends at inference time without retraining.
          C3：该系统与检索后端无关，因为训练好的语音模型消费的是文本形式的参考资料，在推理时可以借助更强的大语言模型或搜索后端获得增益，而无需重新训练。
          evidence:: E6, E12
        - C4: The retrieval interface generalizes beyond the question-answering training distribution by letting the speech model use a backend as an external tool for mathematical reasoning datasets.
          C4：该检索接口能够泛化到问答训练分布之外，方式是让语音模型把某个后端当作外部工具，用于数学推理数据集。
          evidence:: E12
- ## Mechanism and Design
    - **Core Mechanism:** MoshiRAG keeps Moshi as the audio front end, meaning the component that directly handles user speech, and adds a special <ret> token that starts retrieval-augmented generation (RAG), where outside text is fetched and injected into the continuing response.
      **核心机制:** MoshiRAG 保留 Moshi 作为音频前端，也就是直接处理用户语音的那个组件，并新增了一个特殊的 <ret> 标记来启动检索增强生成（retrieval-augmented generation，RAG），即从外部获取文本并注入到正在进行的回答中。
      evidence:: E3, E4, E5
    - **Data / Control Flow:** The system flows from audio to trigger to text retrieval to reference injection: the speech model keeps producing audio while a streaming automatic speech recognition (ASR) model produces text for the retrieval backend.
      **数据/控制流:** 系统的处理流程依次是：音频→触发信号→文本检索→参考资料注入。语音模型持续产出音频，同时一个流式自动语音识别（automatic speech recognition，ASR）模型为检索后端产出文本。
      evidence:: E3, E4
        - Step 1: Moshi receives user speech tokens and its own previous speech and text tokens, then predicts <ret> when the conversation appears to need external facts.
          第一步：Moshi 接收用户的语音标记，以及它自己此前的语音标记和文本标记，随后在对话看起来需要外部事实时预测出 <ret>。
          evidence:: E3, E5
        - Step 2: the system waits for the ASR transcript, sends the aggregated user and assistant text context to an LLM-based or web-search backend, and receives a concise reference document.
          第二步：系统等待 ASR 转写文本，把汇总后的用户与助手文本上下文发送给基于大语言模型或网页搜索的后端，并收到一份简洁的参考文档。
          evidence:: E3, E6
        - Step 3: the reference text is encoded, compressed, projected, and streamed into the temporal Transformer input while the spoken response moves from pre-RAG lead-in content to grounded answer content.
          第 3 步：把参考文本进行编码、压缩、投影，并以流式方式送入时序 Transformer 的输入，与此同时，口语回复也从检索前内容（pre-RAG content，即触发检索之后、检索信息可用之前所说的引导性内容）过渡到基于检索结果的答案内容。
          evidence:: E3, E5
    - **Design Decisions:** The central design tradeoff is to give the backend enough time and knowledge while keeping the foreground speech stream short, stable, and responsive.
      **设计决策:** 核心的设计取舍在于：既要给后端留出足够的时间与知识，又要让前台的语音流保持简短、稳定、反应灵敏。
      claim_kind:: analyst_assessment
      evidence:: E2, E8, E13
        - Need: avoid wasteful retrieval; design choice: predict <ret> only on knowledge-demanding turns; closest alternative reported: fixed-interval calls; tradeoff: trigger reliability now depends on training data and speech intelligibility.
          需求：避免无谓的检索。设计选择：只在需要外部知识的对话轮次预测 <ret>。文中给出的最接近替代方案：按固定间隔发起检索调用。取舍：触发的可靠性由此依赖训练数据和语音的可辨识度。
          evidence:: E3, E16, E17
        - Need: preserve long conversations; design choice: additive injection, meaning adding reference embeddings to existing time steps; closest alternative reported: insertive injection; tradeoff: lower integration effectiveness for a fixed sequence-length budget.
          需求：保留长对话。设计选择：采用加性注入（additive injection），即把参考文本的嵌入向量加到已有的时间步上。文中给出的最接近替代方案：插入式注入（insertive injection）。取舍：在序列长度预算固定的情况下，融合效果会降低。
          evidence:: E5, E13
        - Need: train timing without real retrieval traces; design choice: lead, body, and tail response segments plus sampled retrieval delays; tradeoff: robustness depends on synthetic script realism and the match between training and inference delay distributions.
          需求：在没有真实检索轨迹的情况下训练时序。设计选择：把回复划分为引导段、主体段和收尾段，并配以采样得到的检索延迟。取舍：鲁棒性取决于合成脚本的真实程度，以及训练时与推理时延迟分布之间的匹配程度。
          evidence:: E7, E8, E15
    - **Implementation Surface:** The implementation surface is deliberately modular: a 7B Moshi speech model, a 1B streaming ASR model, and a text-in/text-out retrieval backend communicate through transcripts and reference documents, with inference code released publicly.
      **实现边界:** 实现层面刻意采用模块化设计：一个 7B 的 Moshi 语音模型、一个 1B 的流式自动语音识别（streaming ASR）模型，以及一个文本输入、文本输出的检索后端，三者通过转录文本和参考文档进行通信，推理代码已公开发布。
      evidence:: E4, E6, E18
- ## Evaluation and Evidence
    - **Setup:** Evaluation covers factual speech question answering (QA), HaluEval audio, delay and compute, Full-Duplex-Bench interaction, and out-of-domain math reasoning, mostly using large-language-model judges rather than human raters.
      **实验设置:** 评测涵盖事实性口语问答（QA）、HaluEval 音频、延迟与算力、Full-Duplex-Bench 交互，以及域外的数学推理，且大多使用大语言模型作为评判者，而非人工评分。
      evidence:: E9, E10, E11, E12
    - **Claim-Evidence Matrix:** The evidence is strongest for C1 and C3, moderate for C2, and exploratory for C4 because the math setting shows tool-use potential but also exposes a large reference-to-speech integration gap.
      **主张-证据矩阵:** 证据对 C1 和 C3 最为充分，对 C2 中等，对 C4 则属于探索性质，因为数学场景虽然展现了使用工具的潜力，但也暴露出参考文本到语音之间存在很大的融合差距。
      claim_kind:: analyst_assessment
      evidence:: E9, E11, E12, E14
        - C1 is backed by multiple speech QA datasets and comparisons to two Moshi baselines, but uncertainty is not reported and correctness depends on LLM judging.
          C1 由多个口语问答数据集以及与两个 Moshi 基线模型的对比作为支撑，但文中未报告不确定性，且正确性依赖大语言模型的评判。
          evidence:: E9
        - C2 is backed by delay analysis and Full-Duplex-Bench metrics, but the benchmark scenarios do not fully cover open-ended multi-turn factual conversation.
          C2 由延迟分析和 Full-Duplex-Bench 指标作为支撑，但这些基准场景并未完全覆盖开放式的多轮事实性对话。
          evidence:: E10, E11
        - C3 and C4 are backed by backend-swap experiments and math datasets, with the caveat that response accuracy remains below reference accuracy when references are complex.
          C3 和 C4 由后端替换实验和数学数据集支撑，但需注意：当参考资料复杂时，回答的准确率仍低于参考资料本身的准确率。
          evidence:: E12, E14
    - **Headline Results:** MoshiRAG's practical result is not that a 7B speech model becomes the best fact model, but that it can borrow stronger text or search backends while keeping the full-duplex speech interface.
      **关键结果:** MoshiRAG 的实际价值不在于让一个 7B 语音模型成为最强的事实型模型，而在于它能借用更强的文本或搜索后端，同时保留全双工语音语言模型（full-duplex speech language model，即可以在听用户语音的同时生成自己语音、无需等待严格轮次边界的口语对话模型）的完整语音接口。
      evidence:: E9, E11, E12
        - QA result: Gemma-backed MoshiRAG reaches 80.3 LlamaQ, 74.7 WebQ, 73.2 TriviaQA, and 36.3 HaluEval response accuracy; GPT-4.1 and Tavily improve difficult datasets further.
          问答（QA）结果：以 Gemma 为后端的 MoshiRAG 在 LlamaQ 上达到 80.3、WebQ 上 74.7、TriviaQA 上 73.2，在 HaluEval 上回答准确率为 36.3；GPT-4.1 和 Tavily 能进一步提升在困难数据集上的表现。
          evidence:: E9, E12
        - Interaction result: MoshiRAG reduces premature turn-taking relative to vanilla Moshi and improves interruption handling, while the authors attribute part of the interaction shift to longer knowledge-intensive training turns.
          交互结果：相比原版 Moshi，MoshiRAG 减少了过早的轮流发言，并改善了打断处理；作者认为部分交互变化源于知识密集型训练轮次更长。
          evidence:: E11
        - Math result: on AddSub, MultiArith, SinglEq, SVAMP, and GSM8K, MoshiRAG improves greatly over vanilla Moshi but remains constrained by reference complexity and spoken integration.
          数学结果：在 AddSub、MultiArith、SinglEq、SVAMP 和 GSM8K 上，MoshiRAG 相比原版 Moshi 有大幅提升，但仍受参考资料复杂度和口语整合的制约。
          evidence:: E12, E14
    - **Ablations and Sensitivity:** Ablations make the system boundary clear: reference encoding, injection timing, ASR quality, and retrieval latency are all load-bearing rather than incidental implementation details.
      **消融与敏感性:** 消融实验清晰地划出了系统的边界：参考资料编码、注入时机、自动语音识别（automatic speech recognition，ASR，即把用户语音转成文本的模型）质量以及检索延迟，都是承重环节，而非无关紧要的实现细节。
      evidence:: E13, E14, E15
        - Architecture sensitivity: insertive injection is more accurate in controlled settings, but additive ARC-Encoder-four is chosen because it better preserves sequence length and streaming conversation.
          架构敏感性：在受控设置下，插入式注入（把额外的时间步插入序列）更准确，但最终选用的是加性 ARC-Encoder-four，因为它能更好地保持序列长度和流式对话。这里的加性注入（additive injection）指把参考资料的嵌入向量加到 Moshi 已有的时间步输入上，而不是往序列里插入额外的时间步。
          evidence:: E13
        - Context sensitivity: ground-truth user text improves retrieved and final answers, while ground-truth HaluEval references expose information loss between reference availability and spoken response production.
          上下文敏感性：使用真实的用户文本能改善检索到的答案和最终答案，而使用真实的 HaluEval 参考资料则暴露出：从参考资料可用到最终产出口语回答之间存在信息损失。
          evidence:: E14
        - Latency sensitivity: retrieval delays above 1.5 seconds sharply hurt accuracy, so backend speed is part of the method rather than a deployment afterthought.
          延迟敏感性：检索延迟超过 1.5 秒会严重损害准确率，因此后端速度是方法本身的一部分，而不是部署时才考虑的附加问题。
          evidence:: E15
    - **Reproducibility Gaps:** Inference code and demos are reported, but the paper does not present a complete reproduction package for training data generation, full synthetic corpora, judge variance, repeated runs, or all backend API timing conditions.
      **可复现性缺口:** 复现性缺口：论文报告了推理代码和演示，但没有给出完整的复现材料，缺少训练数据生成、完整的合成语料、评判者方差、重复运行以及全部后端 API 计时条件等内容。
      claim_kind:: analyst_assessment
      evidence:: E7, E9, E12, E18
- ## Technical Judgment
    - **What Holds Up:** The systems decomposition holds up: keeping the fast audio loop separate from the slower knowledge loop is a plausible way to improve factuality without making every audio frame depend on a large reasoning model.
      **站得住的结论:** 系统层面的功能拆分是站得住脚的：让处理速度快的音频回路与处理速度较慢的知识回路保持分离，是一种可行的思路，既能提升事实准确性，又不必让每一个音频帧都依赖一个庞大的推理模型。
      claim_kind:: analyst_assessment
      evidence:: E3, E4, E9, E10
    - **Where It May Fail:** Benefits should diminish when user speech is noisy, the query needs a long or symbolic reference, retrieval exceeds the lead-in window, or the learned trigger misses hard questions because it has no explicit difficulty estimator.
      **可能失效之处:** 在以下情形下，收益应当会减弱：用户语音含有噪声、查询需要很长的或符号化的参考内容、检索所需时间超过了引导语（lead-in）窗口，或者由于缺少显式的难度估计器，学习到的触发机制漏掉了那些真正困难的问题。
      claim_kind:: analyst_assessment
      evidence:: E14, E15, E16
    - **Relation to Other Work:** Technically, MoshiRAG sits between turn-based speech RAG and always-calling full-duplex tool systems: it keeps dual-stream audio interaction, but makes retrieval event-driven and backend-agnostic rather than fixed-corpus or fixed-interval.
      **与已有工作的关系:** 从技术上看，MoshiRAG 介于两类系统之间：一类是基于轮次（turn-based）的语音检索增强生成（RAG），另一类是持续调用工具的全双工工具系统。MoshiRAG 保留了双流音频交互，但让检索由事件驱动、并且不依赖特定后端，而不是固定语料库或固定间隔触发。
      claim_kind:: analyst_assessment
      evidence:: E6, E17
    - **Transferable Lesson:** The reusable pattern is latency hiding with semantic slack: identify a period where the user needs conversational continuity more than final content, then run the expensive knowledge operation in that hidden window.
      **可迁移启发:** 可复用的模式是「利用语义上的空档来隐藏延迟」：先找出一段用户更看重对话连续性、而非最终内容的时期，然后在这个被隐藏的窗口里执行那些开销较大的知识操作。
      claim_kind:: analyst_assessment
      evidence:: E2, E3, E13, E15
- ## Glossary
  collapsed:: true
    - full-duplex speech language model: A spoken dialogue model that can listen to user audio and generate its own speech at the same time, rather than waiting for strict turn boundaries.
      全双工语音语言模型（full-duplex speech language model）：一种口语对话模型，能够在收听用户音频的同时生成自己的语音，而不必等待严格的轮次边界。
    - retrieval-augmented generation: A generation pattern where the model receives external reference text retrieved from a database, search system, or language model before producing the answer.
      检索增强生成（retrieval-augmented generation，RAG）：一种生成模式，模型在产出答案之前，先接收从数据库、搜索系统或语言模型中检索到的外部参考文本。
    - keyword delay: Keyword delay is the time from response start to the answer-bearing word; E2EKD adds the delay before the first audio token.
      关键词延迟（keyword delay，KD）：指从回复开始到出现承载答案的词之间的时间；端到端关键词延迟（end-to-end keyword delay，E2EKD）则在此基础上再加上第一个音频 token 之前的延迟。
    - time-to-first-audio-token: The delay between the end of the user's utterance and the model's first generated audio token, excluding codec or vocoder conversion.
      首个音频 token 时间（time-to-first-audio-token，TTFAT）：指从用户话语结束到模型生成第一个音频 token 之间的延迟，不包含编解码器（codec）或声码器（vocoder）的转换时间。
    - retrieval trigger token: A special token generated by MoshiRAG when the current turn should start an external lookup.
      检索触发 token（retrieval trigger token，<ret>）：当当前轮次应当启动一次外部查找时，由 MoshiRAG 生成的一个特殊 token。
    - automatic speech recognition: A model that converts user speech into text; in MoshiRAG it supplies the text context sent to the retriever while audio interaction continues.
      自动语音识别（automatic speech recognition，ASR）：一种把用户语音转换为文本的模型；在 MoshiRAG 中，它在音频交互继续进行的同时，为检索器提供所需的文本上下文。
    - pre-RAG content: The spoken content produced after retrieval is triggered but before retrieved information is available, usually a coarse answer or conversational lead-in.
      pre-RAG 内容（pre-RAG content）：在触发检索之后、但检索到的信息尚未就绪之前所生成的语音内容，通常是一个粗略的答案或对话式的开场引导。
    - ARC-Encoder: A text encoder used to compress retrieved reference text into a shorter embedding sequence before it is injected into Moshi.
      ARC-Encoder：一种文本编码器，用于把检索到的参考文本压缩成更短的嵌入序列，然后再注入到 Moshi 中。
    - additive injection: The design that adds reference embeddings to existing Moshi time-step inputs instead of inserting extra time steps into the sequence.
      加法式注入（additive injection）：一种设计，把参考文本的嵌入向量加到 Moshi 已有的各时间步输入上，而不是在序列中插入额外的时间步。
    - interaction metrics: TOR is takeover rate in Full-Duplex-Bench; JSD is Jensen-Shannon divergence, used there to compare backchannel timing distributions.
      交互指标（interaction metrics）：TOR 是 Full-Duplex-Bench 中的接管率（takeover rate）；JSD 是 Jensen-Shannon 散度（Jensen-Shannon divergence），在这里用于比较附和反馈（backchannel）时机的分布。
    - word error rate: The fraction of words transcribed incorrectly by ASR; the paper uses it to analyze how speech intelligibility affects retrieval triggering.
      词错误率（word error rate）：自动语音识别（ASR）转写出错的词所占的比例；本文用它来分析语音可懂度如何影响检索触发。
    - question answering: A factual evaluation setting where spoken user questions are paired with ground-truth text answers and model responses are judged for correctness.
      问答（question answering）：一种针对事实的评测设置，把用户以语音提出的问题与标准答案文本配对，并对模型回答的正确性进行评判。
- ## Evidence Index
  collapsed:: true
    - **E1:** problem/paper_statement | Abstract and Introduction | high
      locator:: Abstract; Section 1
      quote:: Full-duplex models provide real-time interactivity but factuality remains open; the paper proposes MoshiRAG, combining a compact full-duplex interface with selective retrieval to access stronger knowledge sources.
    - **E2:** system_design/paper_statement | System Design | high
      locator:: Section 3.1; Figure 2
      quote:: For retrieval-augmented systems, retrieval delay must be shorter than end-to-end keyword delay so retrieved information can be integrated in time; the paper targets retrieval delay no more than two seconds.
    - **E3:** method/implementation_detail | System Design | high
      locator:: Section 3.2; Figures 3 and 4
      quote:: When the retrieval trigger token is predicted, conversation transcripts from ASR and Moshi outputs are sent to the retrieval backend; Moshi continues in full duplex until retrieved text is encoded and injected.
    - **E4:** implementation/implementation_detail | Building Blocks | high
      locator:: Section 3.3
      quote:: MoshiRAG consists of a 7B Moshi model fine-tuned with RAG data, a 1B streaming ASR model, and a retrieval backend; components communicate entirely in text format.
    - **E5:** algorithm/implementation_detail | RAG Augmented Moshi Model | high
      locator:: Section 3.3.1
      quote:: Retrieved reference text is encoded as embeddings, projected by a trainable linear layer, and summed into Moshi's temporal Transformer input in streaming fashion; ARC-Encoder compresses reference sequence length by four.
    - **E6:** system_design/implementation_detail | Retrieval Back End | high
      locator:: Section 3.3.3
      quote:: The paper evaluates LLM-based retrieval that generates concise factual references and search-based retrieval using Tavily, choosing general-purpose tools rather than standard fixed RAG databases.
    - **E7:** experiment_setup/paper_statement | Data Generation | high
      locator:: Sections 4.1.1 and 4.1.2; Tables 4 and 5
      quote:: Training uses synthetic spoken conversations from QA-derived topics, LLM-generated expert-domain topics, multi-turn prompt variants, and a single-turn QA subset totaling about 1.9M conversation instances.
    - **E8:** algorithm/implementation_detail | Training | high
      locator:: Section 4.2
      quote:: The retrieval token is placed before the first token of the lead portion, retrieval delay is sampled during training, reference dropout is used, and Moshi is trained for 100k updates with batch size 32.
    - **E9:** result/experiment_result | Factuality | medium
      locator:: Section 5.1; Tables 1 and 9
      quote:: With Gemma retrieval, MoshiRAG response accuracy reaches 80.3 on LlamaQ, 74.7 on WebQ, 73.2 on TriviaQA, and 36.3 on HaluEval, exceeding vanilla Moshi and RAG-data fine-tuned Moshi.
    - **E10:** result/experiment_result | Delay and Computation Consumption | medium
      locator:: Section 5.2; Table 1
      quote:: The paper reports that the conversational lead increases keyword delay by about one second, while MoshiRAG still has lower end-to-end keyword delay than nearly all competing systems and comparable computation.
    - **E11:** result/experiment_result | Interactivity | medium
      locator:: Section 5.3; Table 2
      quote:: On Full-Duplex-Bench, MoshiRAG has lower pause takeover rates than vanilla Moshi, low interruption latency, and a higher interruption GPT score; the authors attribute behavior partly to RAG data distribution.
    - **E12:** result/experiment_result | Experiments of Diverse Retrieval Back Ends | medium
      locator:: Sections 5.4 and B.3; Tables 3, 9, and 10
      quote:: Switching retrievers changes outcomes without retraining: GPT-4.1 improves TriviaQA and HaluEval response accuracy, and math datasets show MoshiRAG can use retrieved reasoning beyond QA-style training.
    - **E13:** ablation/ablation | Justification of Model Architecture | medium
      locator:: Appendix B.1; Tables 6 and 7
      quote:: Insertive injection outperforms additive injection but increases sequence length; ARC-Encoder with compression ratio four and additive injection is adopted to balance performance, timing, and long-form conversation.
    - **E14:** ablation/ablation | Sensitivity to ASR and Reference Correctness | medium
      locator:: Appendix B.2; Table 8
      quote:: Ground-truth user text improves retrieved references and final responses by up to about fifteen percent; HaluEval ground-truth references reveal a large gap between reference accuracy and spoken response accuracy.
    - **E15:** limitation/case_study | Further Analysis of Moshi Performance | medium
      locator:: Appendix C; Figure 6
      quote:: RAG trigger rates generally decline as WER increases, and response accuracy drops sharply when retrieval latency exceeds 1.5 seconds across almost all datasets.
    - **E16:** limitation/limitation | Conclusion and Impact Statement | high
      locator:: Section 6; Impact Statement
      quote:: The authors state that retrieval triggering currently relies on training data and future work should link retrieval decisions to query difficulty, diversify tools, and improve robustness against retrieval errors.
    - **E17:** prior_work/paper_statement | Related Work | high
      locator:: Section 2
      quote:: The paper contrasts MoshiRAG with StreamRAG, which is non-full-duplex and fixed-corpus, and KAME, which supports full duplex but relies on frequent fixed-interval LLM calls.
    - **E18:** metadata/metadata | Introduction | high
      locator:: Section 1 footnotes
      quote:: The authors say they release MoshiRAG inference code on GitHub together with demo videos for public access.
