- **Title:** Metronome: Bound the Cache, Keep the Beat for Real-Time Interaction Model Serving
  **标题:** Metronome：限制缓存，保持节拍，实现实时交互模型服务
- **Summary:** Metronome bounds each live session's resident attention state so long-running interaction serving avoids a hidden memory cliff and exposes a usable latency signal for overload control.
  **一句话总结:** Metronome 为每个活跃会话的常驻注意力状态设定上限。常驻注意力状态是会话处于活跃状态时保留在 GPU 内存中的状态。这样，长期运行的交互服务就能避免隐蔽的内存悬崖，并获得可用于过载控制的延迟信号。
- **Paper Type:** system
  **论文类型:** 系统论文
- **Venue:** arXiv preprint arXiv:2607.02640v1, 2026
  **发表:** arXiv 预印本 arXiv:2607.02640v1，2026
- **Authors:** Jiaying Meng (Independent Researcher); Bojie Li (Pine AI)
  **作者:** Jiaying Meng（独立研究者）；Bojie Li（Pine AI）
- **Keywords:** real-time interaction model serving, KV cache, periodic real-time task, sliding-window attention, attention sinks, admission control, AIMD
  **关键词:** 实时交互模型服务、键值缓存（Key-Value cache，KV cache）、周期性实时任务、滑动窗口注意力、注意力汇聚点、准入控制、加性增大与乘性减小（Additive-increase/multiplicative-decrease，AIMD）
- ## Orientation
    - **Background:** Real-time interaction models listen and answer continuously. To avoid recalculating the conversation for every audio frame, the serving engine keeps previously computed attention state in GPU memory, called the key-value cache.
      **背景:** 实时交互模型会持续聆听并作出回答。为了避免每处理一个音频帧都重新计算整段对话，服务引擎会把先前算出的注意力状态保存在 GPU 内存中，这些状态称为键值缓存（key-value cache，KV cache）。
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** During a long call, every participant keeps adding saved state. If that state never leaves, a fixed memory pool can fill and freeze all conversations even though the usual delay dashboard looked healthy moments earlier.
      **通俗问题:** 在长时间通话中，每位参与者都会不断增加需要保存的状态。如果这些状态始终不被移出，固定大小的内存池就可能被填满，导致所有对话停滞，而就在片刻之前，常用的延迟监控面板看起来仍然一切正常。
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** Unlike a chatbot turn, a live session has no quiet gap for moving or rebuilding state. Its deadline repeats, while the warning signal stays calm until failure, so an overload gate has no time to react.
      **为何困难:** 与聊天机器人的单轮交互不同，实时会话没有空闲间隔可供系统转移或重建状态。每一帧的截止时间都会反复到来，但预警信号在故障发生前一直保持平稳，因此过载准入机制来不及作出反应。
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Keep only a recent slice of each session's saved state, anchored by a tiny preserved beginning, so memory stays bounded and delay changes gradually enough to guide admissions.
      **一句话核心思路:** 每个会话只保留一段近期状态，并用一小段保留下来的起始状态作为锚点。这样既能限制内存占用，又能让延迟逐渐变化，从而为准入决策提供依据。
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a systems view of continuous voice-model serving: it identifies the missing state bound between throughput-oriented language-model engines and recurring-deadline scheduling, then shows why that bound is prerequisite to overload control.
      **阅读价值:** 可以把这篇论文视为对连续语音模型服务的系统性分析：它指出，在以吞吐为导向的语言模型引擎与周期性实时任务调度之间，缺少一个关键的状态上限；随后又说明，只有先建立这一上限，系统才能实施过载控制。
      claim_kind:: analyst_assessment
      evidence:: E2, E3
    - **One-Sentence Contribution:** Metronome prevents long-lived interaction sessions from exhausting GPU attention memory by bounding each session inside the engine, which also turns latency into a useful signal for deciding how many sessions to accept.
      **一句话贡献:** Metronome 在引擎内部限制每个会话的状态规模，从而防止长期存续的交互会话耗尽 GPU 的注意力状态内存；这一限制还能让延迟成为有效信号，帮助系统决定可以接纳多少个会话。
      evidence:: E4, E6
    - **Mental Model:** Picture a café that serves every seated customer on each bell: Metronome limits how much table space each customer may keep, so the room gets gradually busier instead of becoming impassable all at once, and the host can stop admitting people before service breaks.
      **记忆模型:** 可以把它想象成一家在每次铃响时都要为所有在座顾客服务的咖啡馆：Metronome 限制每位顾客可以长期占用的桌面空间，因此店内会逐渐变得繁忙，而不会突然拥挤到无法通行；接待员也能在服务崩溃前停止接纳新顾客。
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence combines repeated long-run failures, internal memory traces, a cross-model timing prediction, a controlled admission comparison, and a quality ablation.
      **最佳证据:** 最有力的证据包括多次复现的长时间运行故障、内部内存轨迹、跨模型耗时预测、受控的准入策略对比，以及质量消融实验。
      evidence:: E6, E8, E10, E12
        - Supports C1: Qwen3-Omni-30B, twenty fresh five-minute runs per policy at two concurrency levels; unmodified vLLM-realtime; memory-wall incidence; 14/20 versus 0/20; repeated but regime-dependent support, Fig. 4.
          支持 C1：使用 Qwen3-Omni-30B，在两个并发水平下对每种策略分别进行了二十次新开展的五分钟运行；采用未经修改的 vLLM-realtime；统计亚稳态延迟悬崖的发生情况；结果为 14/20 对 0/20；重复实验提供了支持，但结果取决于运行状态，见图 4。
          evidence:: E6
        - Supports C2: Qwen3-Omni-30B and MiniCPM-o; early linear pool-fill fit versus measured stall; saturation time; 145 versus 148 seconds and 99 versus 114 seconds; direct two-model support, Fig. 6.
          支持 C2：使用 Qwen3-Omni-30B 和 MiniCPM-o；对早期池填充过程进行线性拟合，并与实测停顿比较；比较饱和时间；结果分别为 145 秒对 148 秒，以及 99 秒对 114 秒；两个模型都提供了直接支持，见图 6。
          evidence:: E8
        - Supports C3: 512 offered sessions arriving at eight per second with a 600 ms target; identical unbounded controller; admitted capacity and 99th-percentile frame latency; bounded serving settles near 209 sessions at 12 ms while unbounded serving reaches the wall; single-run support, Fig. 7.
          支持 C3：系统以每秒八个的速率接收共 512 个待接入会话，目标延迟为 600 ms；两种方案采用相同的无界控制器；测量接纳容量和第 99 百分位帧延迟；有界服务最终稳定在约 209 个会话和 12 ms，而无界服务则到达亚稳态延迟悬崖；该结论来自单次运行，见图 7。
          evidence:: E10
        - Supports C4: Qwen3-Omni-30B free-running sessions with a recent-token window and pinned starting tokens; sink-ablated windows and unbounded serving; age-dependent spoken-question correctness; the full bound stays age-independent while every sink ablation decays toward zero; controlled single-model support, Fig. 8.
          支持 C4：让 Qwen3-Omni-30B 会话自由运行，并采用近期词元窗口，同时固定保留起始词元；比较移除注意力汇聚点的窗口与无界服务；测量随会话时长变化的口头提问正确率；完整的有界方案不受会话时长影响，而每一种注意力汇聚点消融方案的正确率都逐渐降至接近零；这是在单一模型上进行的受控实验，见图 8。
          evidence:: E12
    - **Main Caveat:** The evidence establishes one vLLM-based stack on one Blackwell GPU, not a hardware- or engine-independent law; only two models are driven to the wall, and control and quality are studied mainly on one model.
      **主要边界:** 主要局限在于，这些证据只验证了一个基于 vLLM、运行在一块 Blackwell 图形处理器（GPU）上的系统栈，并未证明这一规律独立于硬件或推理引擎。研究只让两个模型运行到亚稳态延迟悬崖，而且控制机制和质量主要只在一个模型上进行了研究。
      claim_kind:: analyst_assessment
      evidence:: E15
- ## Argument Map
    - **Problem and Stakes:** A streaming interaction session is a periodic real-time task, meaning the same work must finish before a recurring frame deadline, while its key-value cache (KV cache), the saved attention state for earlier tokens, remains resident and grows. Once the engine's fixed pool of KV memory blocks fills, all sessions can stall and return empty frames on time, so latency and deadline-miss alarms may report health while users hear silence.
      **问题与重要性:** 流式交互会话是一种周期性实时任务，也就是说，同一类工作必须在反复出现的帧截止时间之前完成。与此同时，它的键值缓存会一直驻留在 GPU 内存中并持续增长；这种缓存保存了较早词元的注意力状态。一旦推理引擎中由键值缓存内存块组成的固定池被填满，所有会话都可能停滞，却仍按时返回空帧。因此，延迟监控和错过截止时间的告警可能仍显示系统正常，但用户听到的却是一片沉默。
      evidence:: E2, E6, E7
    - **Prior Gap:** Throughput-oriented language-model engines assume requests eventually finish or pause, and classical real-time scheduling assumes each recurring task has bounded state. vLLM and SGLang can keep a long-lived request's KV cache resident across frames, but the paper finds no built-in per-session state bound, recurring-deadline capacity rule, or admission gate for this workload.
      **已有方法缺口:** 面向吞吐的语言模型引擎假定请求最终会结束或暂停，而经典实时调度则假定每个周期性实时任务的状态都有上限。周期性实时任务会反复到期，并且每个任务实例都必须在相应的截止期限前完成；在这里，每个交互帧就是一个任务实例。vLLM 和 SGLang 可以让长期运行请求的键值缓存（KV cache）跨帧常驻；键值缓存保存先前词元的注意力键和值，以免模型在每一帧都重新计算全部历史。然而，论文发现，这些系统没有为此类工作负载内置逐会话状态上限、针对周期性截止期限的容量规则或准入门控机制。
      evidence:: E3, E17
    - **Key Insight:** The apparent latency failure is actually a memory-allocation threshold: frame computation remains cheap until monotonically growing resident state consumes the last block. Bounding state changes memory use from a time-growing ramp into a concurrency-proportional plateau, removing the hidden failure clock and exposing load through latency before memory is exhausted.
      **关键洞见:** 表面上的延迟故障实际上源于一个内存分配阈值：在单调增长的驻留状态耗尽最后一个内存块之前，每帧计算的开销一直很低。驻留状态是会话保持活动时留在 GPU 内存中的逐会话状态，而不是被换出或重新计算。限制状态大小后，内存用量不再随时间持续爬升，而会变成与并发数成正比的稳定平台。这消除了隐藏的故障倒计时，并使系统能在内存耗尽之前通过延迟反映负载。
      evidence:: E7, E9
    - **Claims:** The paper's argument reduces to four falsifiable claims about failure, prediction, control, and quality.
      **核心主张:** 论文的论证可以归结为关于故障、预测、控制和质量的四项可证伪主张。
      claim_kind:: analyst_assessment
        - C1: Unbounded resident KV in long-running periodic sessions causes a memory-triggered, sometimes run-sensitive, observability-silent stall, while an in-engine per-session bound eliminates that stall under matched experiments.
          C1：在长期运行的周期性会话中，无上限的驻留键值缓存会引发由内存触发的停滞。这种停滞有时会受不同运行之间的细微差异影响，而且出现前不会在可观测指标中发出预警。在实验条件一致的对照实验中，引擎内部的逐会话上限可以消除这种停滞。
          evidence:: E6, E7
        - C2: Early KV-pool growth predicts when unbounded serving will saturate, whereas bounded serving reaches a stable memory plateau whose capacity exceeds the measured deadline-limited concurrency.
          C2：键值缓存池的早期增长速度可以预测无上限服务何时达到饱和；相比之下，有上限的服务会进入稳定的内存占用平台，其容量超过按照截止期限实测得到的并发上限。
          evidence:: E8, E9
        - C3: Once state is bounded, per-frame latency becomes a faithful enough load signal for online admission to discover schedulable concurrency; the same controller over-admits when state is unbounded.
          C3：状态受到限制后，每帧延迟就能足够忠实地反映负载，使在线准入控制能够找到可调度并发数，也就是仍能保证每一帧都在预算内完成的最大同时活跃会话数。当状态没有上限时，同一个控制器会准入过多会话。
          evidence:: E10
        - C4: A recent-token window preserves the reported turn-based quality, and pinned starting tokens called attention sinks are necessary to keep free-running generation healthy, although no fixed window preserves information beyond its horizon.
          C4：只保留近期词元的窗口能够维持论文报告的轮次式交互质量。系统还必须固定保留称为注意力汇（attention sink）的起始词元，才能让不受外部终止约束的持续生成保持正常。不过，任何固定窗口都无法保留超出其覆盖范围的信息。
          evidence:: E11, E12
- ## Mechanism and Design
    - **Core Mechanism:** Metronome gives every live request a fixed-shape resident state and then controls admissions from the resulting latency slope. Its diagnostic model is $\rho(t)=\rho_0+Nrt$ and $t_{\mathrm{sat}}=(1-\rho_0)/(Nr)$, where $\rho(t)$ is KV-pool occupancy at time $t$, $\rho_0$ is initial occupancy, $N$ is concurrent sessions, $r$ is the fraction of the pool consumed per second by one session, and $t_{\mathrm{sat}}$ is predicted saturation time.
      **核心机制:** Metronome 为每个活动请求分配固定形状的驻留状态，然后根据由此得到的延迟变化斜率控制准入。其诊断模型为 $\rho(t)=\rho_0+Nrt$ 和 $t_{\mathrm{sat}}=(1-\rho_0)/(Nr)$。其中，$\rho(t)$ 表示时刻 $t$ 的键值缓存池占用率，$\rho_0$ 表示初始占用率，$N$ 表示并发会话数，$r$ 表示单个会话每秒消耗的缓存池比例，$t_{\mathrm{sat}}$ 表示预测的饱和时间。
      evidence:: E4, E8
        - For each request, the engine retains the latest $W$ tokens, where $W$ is the recent-context window, plus the first $S$ tokens, where $S$ is the pinned attention-sink prefix; it frees intervening KV blocks and permits attention only to that pinned prefix and recent window.
          对于每个请求，引擎保留最新的 $W$ 个词元，其中 $W$ 是近期上下文窗口；同时保留最前面的 $S$ 个词元，其中 $S$ 是固定保留的注意力汇前缀。引擎释放两者之间的键值缓存块，并且只允许注意力机制关注该固定前缀和近期窗口。
          evidence:: E5
        - On each frame tick, the worker groups all due sessions into one GPU execution step, called continuous batching, and must process their new input and output before frame budget $B$, the recurring deadline.
          每次帧时钟触发时，工作进程都会把所有到期会话合并到同一个 GPU 执行步骤中。这种方法称为连续批处理（continuous batching），即系统反复将当前所有已就绪的请求组合到共享的 GPU 执行步骤中，而不是等待一个固定批处理全部完成。工作进程必须在帧预算 $B$ 内处理完这些会话的新输入和输出；帧预算是每个周期性交互帧在下一次截止期限到来前可用的实际时间。
          evidence:: E2, E4
        - An additive-increase/multiplicative-decrease controller (AIMD) raises the admission cap gradually while latency has headroom, cuts it proportionally near a target fraction of frame budget $B$, and rejects arrivals above the cap.
          加性增大/乘性减小（Additive-Increase/Multiplicative-Decrease，AIMD）控制器会在延迟仍有余量时逐步提高准入上限；当延迟接近帧预算 $B$ 的目标比例时，控制器会按比例降低该上限；超过上限的新请求则会被拒绝。帧预算是指一帧必须在截止期限前完成时可用的实际时间。
          evidence:: E4, E10
    - **Data / Control Flow:** The execution path separates the gateway's session gate from the worker's state bound but closes the loop through measured per-frame latency. The same clients and gateway drive bounded and unbounded workers, making the memory policy the central controlled difference.
      **数据/控制流:** 执行路径将网关的会话准入关口与工作进程的状态上限分开，但通过测得的每帧延迟形成闭环反馈。同一组客户端和网关分别驱动有状态上限和无状态上限的工作进程，因此内存策略成为这组受控比较中的核心差异。
      evidence:: E4, E14
        - Clients send small audio chunks over a persistent two-way network connection (WebSocket) to a Go gateway, which queues each session for its next frame tick and applies the current admission cap.
          客户端通过持久的双向网络连接（WebSocket）向 Go 网关发送小段音频。网关将每个会话排入队列，等待其下一个帧节拍，并应用当前的准入上限。
          evidence:: E4, E14
        - Once per tick, the gateway sends one batched remote procedure call (gRPC Step) to the GPU worker; for every admitted persistent request the worker encodes new input into cached state (prefill), generates up to a small output allowance (decode), and returns only newly produced tokens.
          每个节拍到来时，网关都会向图形处理器（GPU）工作进程发送一次批处理远程过程调用（gRPC Step）。对于每个已准入的持久请求，工作进程先将新输入编码到缓存状态中，这一步称为预填充；然后在较小的输出配额内生成词元，这一步称为解码；最后只返回本次新生成的词元。
          evidence:: E2, E4
        - The gateway measures total frame time, feeds it to AIMD, admits sessions up to the learned schedulable concurrency $N^*$, meaning the largest count that still meets every recurring deadline, and sheds the rest with an overload rejection.
          网关测量每帧的总耗时，将结果反馈给 AIMD，并按照学习得到的可调度并发数 $N^*$ 准入会话。可调度并发数是仍能满足每个周期性截止期限的最大并发会话数；其余会话则通过过载拒绝机制卸载。
          evidence:: E4, E10
    - **Design Decisions:** The design deliberately spends engine integration effort to keep the application simple and to make memory, computation, and feedback share one explicit per-session bound. Its assumptions are that each session can discard most old attention state, arrivals can be rejected, and bounded-state latency changes meaningfully with load.
      **设计决策:** 该设计有意投入额外的引擎集成工作，以保持应用层简单，并让内存、计算和反馈共同受同一个明确的每会话上限约束。它基于三项假设：每个会话都可以丢弃大部分旧的注意力状态；系统可以拒绝新到达的请求；设置状态上限后，延迟会随负载发生显著变化。
      claim_kind:: analyst_assessment
      evidence:: E5, E10, E12
        - The window lives inside the engine rather than recycling requests in the application, because recycling must re-encode retained context at every boundary; the tradeoff is a vLLM-specific modification instead of a portable wrapper.
          滑动窗口在引擎内部实现，而不是由应用层循环重建请求，因为后一种做法必须在每个边界处重新编码保留下来的上下文。代价是需要对 vLLM 进行专用修改，而不能使用可移植的封装层。
          evidence:: E5, E13
        - For a model that normally looks at all prior tokens, called a full-attention backbone, Metronome pins structural opening tokens rather than early conversation content; too few sinks destabilize free-running decode, while pinning semantic content can bias later answers.
          对于通常会关注此前所有词元的模型，也就是全注意力骨干模型，Metronome 固定的是开头用于构建结构的词元，而不是对话早期包含语义内容的词元。固定的注意力汇聚词元过少，会使自由运行解码变得不稳定；固定包含语义内容的词元，则可能使后续回答产生偏向。
          evidence:: E12
        - A feedback cap replaces a hand-set capacity because safe concurrency depends on model, window, hardware, and arrivals; this choice is valid only after bounding removes the flat-until-failure signal.
          系统使用反馈控制的准入上限代替人工设定的容量，因为安全并发数取决于模型、窗口、硬件和请求到达情况。只有先通过状态上限消除那种「直至故障前始终平坦」的信号特征，这项选择才有效。
          evidence:: E4, E10
    - **Implementation Surface:** Adoption touches vLLM model construction and KV-block retention, plus the gateway's admission policy; exact sink support additionally changes an attention GPU kernel. The window half is narrow, while the full quality-preserving mask is engine- and backend-specific.
      **实现边界:** 采用该设计需要修改 vLLM 的模型构建方式和键值缓存（KV cache）块保留机制，还需要修改网关的准入策略。键值缓存保存早期词元的注意力键和值，以供后续计算复用。若要精确支持注意力汇聚词元，还必须修改注意力计算的 GPU 核函数。窗口相关改动的范围较小，而完整的、能够保持质量的掩码实现则取决于具体引擎和后端。
      claim_kind:: analyst_assessment
      evidence:: E5, E16
        - The window half sets the decoder layer's existing sliding-window attribute so vLLM builds a windowed KV specification and frees blocks behind it; the paper reports no scheduler, allocator, or public application-programming-interface change for this half.
          滑动窗口部分会设置解码器层已有的滑动窗口属性，使 vLLM 为键值缓存（KV cache，即保存先前词元的注意力键和值、从而避免在每一帧都重新计算完整历史的缓存）构建窗口式规范，并释放已经滑出窗口的缓存块。论文称，这一部分没有改动调度器、分配器或公共应用程序编程接口（application programming interface，API）。
          evidence:: E5
        - Because FlashAttention's stock window cannot include both an old prefix and a recent suffix, the sink half routes decoder layers to vLLM's Triton backend, extends its attention mask and tile loop, and pins the corresponding first KV blocks.
          FlashAttention 的原生窗口机制无法同时纳入较早的前缀和最近的后缀。因此，注意力汇聚点部分将解码器层交由 vLLM 的 Triton 后端处理，扩展其中的注意力掩码和分块循环，并固定保留相应键值缓存中最前面的块。
          evidence:: E5, E16
        - The reported artifact includes the patch, a reference-based kernel check, and four extra fixes needed for omni models on Blackwell; no new external library dependency is reported, and the minimum supported hardware is not established beyond the evaluated RTX PRO 6000.
          论文报告的配套产物包括补丁、以参考实现为基准的内核校验，以及全模态模型在 Blackwell 上运行所需的另外 4 项修复。论文没有报告新增任何外部库依赖；除已评测的 RTX PRO 6000 外，也尚未确定所支持的最低硬件要求。
          claim_kind:: analyst_assessment
          evidence:: E14, E16
- ## Evaluation and Evidence
    - **Setup:** The evaluation uses a real end-to-end audio path on one NVIDIA RTX PRO 6000 Blackwell and compares the same clients, Go gateway, vLLM-realtime worker, and load with only the resident-state policy changed where possible. It measures frame-latency percentiles over elapsed-time buckets, delivery cadence, answer correctness, KV-pool occupancy, waiting requests, and wall incidence.
      **实验设置:** 评测在一块 NVIDIA RTX PRO 6000 Blackwell 上运行真实的端到端音频处理流程，并比较相同的客户端、Go 网关、vLLM-realtime 工作进程和负载；只要条件允许，实验仅改变驻留状态策略，即会话保持活动时将其状态留在图形处理器内存中的策略。评测指标包括按运行已持续时间分桶统计的帧延迟百分位数、数据交付节奏、答案正确性、键值缓存池占用率、等待中的请求数，以及亚稳态延迟悬崖（wall，即帧延迟从低位突然转为无法恢复的停滞）的发生情况。
      evidence:: E14, E15
        - Real LibriSpeech and spoken-question clips arrive in small chunks as distinct, phase-staggered streams to prevent shared prefixes from artificially raising capacity; every data point starts a fresh worker to avoid residual-state bias.
          真实的 LibriSpeech 音频和口述问题片段会以小数据块到达，并分别组成彼此独立且相位错开的数据流，以防共享前缀人为提高系统容量。每个数据点都从全新的工作进程开始测量，以避免残留状态造成偏差。
          evidence:: E14
        - The closest baseline is unmodified vLLM-realtime resumable serving, where one persistent request reuses prior KV state; bounded and unbounded comparisons otherwise hold engine, stack, model, audio, and offered load fixed.
          最接近的基线是未经修改的 vLLM-realtime 可恢复服务模式，其中一个持续存在的请求会复用此前的键值缓存状态。除此之外，在比较有界策略与无界策略时，实验会固定引擎、软件栈、模型、音频和施加的负载。
          evidence:: E6, E14
        - Short-burst capacity is sampled across four interaction models, but only Qwen3-Omni-30B and MiniCPM-o are driven to the long-duration wall; admission and detailed quality tests center on Qwen3-Omni-30B.
          实验在 4 个交互模型上抽样测量短时突发负载下的容量，但只有 Qwen3-Omni-30B 和 MiniCPM-o 持续运行到出现长期亚稳态延迟悬崖。准入测试和详细的质量测试主要围绕 Qwen3-Omni-30B 展开。
          evidence:: E15
    - **Claim-Evidence Matrix:** Each logical claim has a distinct evidence route, which helps separate repeated outcomes from single-run demonstrations and model-side quality probes.
      **主张-证据矩阵:** 每项逻辑主张都有独立的证据路径，这有助于区分反复出现的结果、单次运行的演示，以及针对模型输出质量的测试。
      claim_kind:: analyst_assessment
        - C1 is supported by repeated wall outcomes under matched policies and by internal traces linking full KV-pool occupancy to all requests entering the wait queue; evidence E6 and E7.
          C1 的依据包括：在条件匹配的不同策略下反复出现的延迟悬崖结果，以及内部轨迹所揭示的关联——键值缓存池占满后，所有请求都会进入等待队列。对应证据为 E6 和 E7。
          claim_kind:: analyst_assessment
          evidence:: E6, E7
        - C2 is supported by early-trace predictions on two models and measured plateau scaling across concurrency; evidence E8 and E9, with the memory ceiling partly extrapolated.
          C2 的依据包括：根据两个模型的早期运行轨迹作出的预测，以及不同并发度下平台值如何变化的实测结果。对应证据为 E8 和 E9，其中内存上限有一部分来自外推。
          claim_kind:: analyst_assessment
          evidence:: E8, E9
        - C3 is supported by a bounded-versus-unbounded controller comparison using the same latency-only policy; evidence E10, limited by a single bounded open-system ramp and one unbounded arm.
          C3 的依据是：在采用同一种仅考虑延迟的策略时，对有界控制器与无界控制器进行比较；对应证据为 E10。其局限在于，实验只进行了一次有界开放系统递增负载测试和一次无界配置测试。
          claim_kind:: analyst_assessment
          evidence:: E10
        - C4 is supported by turn-based parity and free-running window-and-sink controls, including the identical sink-capable kernel with zero sinks; evidence E11 and E12, all on one quality backbone.
          C4 的依据包括回合制条件下的表现一致性，以及自由运行条件下针对汇聚标记锚定的滑动窗口所做的对照实验。该滑动窗口会保留最近的窗口词元和开头的结构词元。实验还使用了同一个支持汇聚标记的内核，并将汇聚标记数量设为零作为对照；对应证据为 E11 和 E12，所有实验都基于同一个质量评估骨干模型。
          claim_kind:: analyst_assessment
          evidence:: E11, E12
    - **Headline Results:** The results most directly support the state-bound mechanism: the intervention removes repeated long-run stalls, the pool-fill model predicts their timing, and latency-based admission becomes usable only after the intervention.
      **关键结果:** 这些结果最直接地支持状态有界机制：干预措施消除了长时间运行时反复出现的停顿；缓存池填充模型根据缓存池占用量随时间的增长来预测这些停顿何时发生；而且，只有实施干预后，基于延迟的准入控制才真正可用。
      evidence:: E6, E8, E10
        - For C1, twenty fresh 300-second Qwen3-Omni-30B runs per policy at 96 or 128 sessions use 10-second bucket median latency and wall incidence: unbounded vLLM-realtime stalls in 14/20, while bounded KV stalls in 0/20; the two batches move from 4/10 to 10/10 unbounded walls, so the asymmetry is repeated but the absolute rate is not calibrated, Fig. 4.
          对于 C1，每种策略分别在 96 或 128 个会话下进行 20 次全新的 300 秒 Qwen3-Omni-30B 运行。评估指标包括每个 10 秒时间桶内的延迟中位数，以及延迟断崖的出现率；延迟断崖是指系统从低帧延迟突然转为无法恢复的停顿。无界 vLLM-realtime 在 14/20 次运行中发生停顿，而采用有界键值缓存（KV cache，即保存早期词元的注意力键和值、供后续计算复用的缓存）时，停顿次数为 0/20。两个批次中，无界配置出现延迟断崖的次数从 4/10 增至 10/10。因此，这种不对称现象可以重复观察到，但实验并未校准其绝对发生率，见 Fig. 4。
          evidence:: E6
        - For C2, a straight-line fit to early KV-pool occupancy predicts measured saturation at 145 versus 148 seconds for Qwen3-Omni-30B and 99 versus 114 seconds for MiniCPM-o; this is close on the headline model and about 13% off on the second, without reported confidence intervals, Fig. 6.
          对于 C2，研究者对早期键值缓存池占用量进行直线拟合，以预测缓存池饱和时间。对于 Qwen3-Omni-30B，预测值为 145 秒，实测值为 148 秒；对于 MiniCPM-o，预测值为 99 秒，实测值为 114 秒。该预测在主要模型上很接近实测结果，在第二个模型上则相差约 13%；论文没有报告置信区间，见 Fig. 6。
          evidence:: E8
        - For C3, an arrival stream that continuously offers sessions sends 512 at eight per second to a 600 ms target: bounded serving settles near 209 admitted sessions with steady 99th-percentile frame latency of 12 ms, while the identical unbounded controller reads flat headroom and ends near the 1.6-second wall; both arms are single-run demonstrations, Fig. 7.
          对于 C3，一个持续提供新会话的到达流以每秒 8 个会话的速率共发送 512 个会话，目标延迟设为 600 ms。有界服务最终稳定在约 209 个获准进入的会话，帧延迟的第 99 百分位数稳定在 12 ms。相比之下，采用完全相同策略的无界控制器一直判断可用余量没有变化，最终接近 1.6 秒的延迟断崖。两个配置都只进行了一次演示性运行，见 Fig. 7。
          evidence:: E10
    - **Ablations and Sensitivity:** The useful ablations separate memory placement, window size, and pinned-prefix semantics rather than treating bounded context as one opaque switch.
      **消融与敏感性:** 这些消融实验分别考察内存放置方式、窗口大小和固定前缀的语义，而不是把有界上下文当作一个内部机制不透明的单一开关。
      evidence:: E11, E12, E13
        - For C4 in end-of-sequence-terminated turns, 96 sessions answer correctly under both unbounded and windowed serving, with about 70% versus 68% per-frame correctness reported as statistically indistinguishable; the paper does not report the test statistic or interval.
          对于 C4，在由序列结束标记终止每个回合的设置下，96 个会话在无界服务和窗口化服务中都能正确作答。论文报告的逐帧正确率分别约为 70% 和 68%，并称二者在统计上无法区分；但论文没有报告检验统计量或区间估计。
          evidence:: E11
        - For C4 in five-minute free-running decode at 32 sessions, all zero-sink windows decay toward zero current-question correctness after their windows pass the start, while a 1024-token window with 32 pinned tokens stays age-independent; a zero-sink run on the same kernel isolates the recovery to sinks, but all rows are single fresh runs on Qwen3-Omni-30B, Fig. 8.
          对于 C4，在 32 个会话下进行五分钟的自由运行解码时，所有汇聚标记数量为零的窗口配置，在窗口左边界越过序列起点后，当前问题的正确率都会逐渐降至接近零。相比之下，包含 32 个固定词元的 1024 词元窗口，其正确率不随会话持续时间变化。在同一内核上将汇聚标记数量设为零的运行表明，正确率恢复来自汇聚标记；但所有结果行都只对应 Qwen3-Omni-30B 上一次全新的运行，见 Fig. 8。
          evidence:: E12
        - At the same memory horizon, application-level recycling avoids the wall but re-encoding grows to roughly 14-17 ms median and 36 ms 90th-percentile frame latency, whereas the in-engine window stays flat; windows through 2048 tokens, about 80 seconds, remain near 5 ms, but the 4096-token tail result is treated by the paper as single-run noise, Fig. 10 and Fig. 11.
          在相同的内存保留时长下，应用层回收可以避开延迟断崖，但重新编码的开销会持续增长：帧延迟中位数增至约 14-17 ms，第 90 百分位数增至 36 ms；相比之下，引擎内部的窗口机制可使延迟保持稳定。窗口不超过 2048 个词元时，即对应约 80 秒的保留时长，延迟始终接近 5 ms；但论文将 4096 词元配置的尾部结果视为单次运行产生的噪声，见 Fig. 10 和 Fig. 11。
          evidence:: E13
    - **Reproducibility Gaps:** The paper reports unusually useful engine patches, per-run logs, a randomized order, and a kernel reference check, but the strongest generality and statistical gaps remain experimental rather than packaging-related.
      **可复现性缺口:** 论文提供了格外实用的推理引擎补丁、逐次运行日志、随机化执行顺序和内核参照校验。不过，最突出的普适性与统计方面的缺口仍然来自实验本身，而不是实验制品的整理与发布方式。
      claim_kind:: analyst_assessment
      evidence:: E15, E16
        - The paper links public code and says the bounded-KV patch, Blackwell fixes, per-run logs, shuffle, and exact mask test ship with the artifact; the supplied text does not identify a commit, artifact version, or archival snapshot.
          论文给出了公开代码的链接，并说明随实验制品一同发布了有界键值缓存（KV cache，即保存早期词元的注意力键和值，以免模型在每一帧都重新计算全部历史）补丁、Blackwell 修复项、逐次运行日志、随机打乱功能和精确掩码测试。不过，所提供的文本没有注明代码提交版本、实验制品版本或存档快照。
          evidence:: E6, E16
        - Wall outcomes have repeat counts, but admission, cross-model capacity, and the MiniCPM-o wall use single fresh runs; several latency and correctness conclusions lack confidence intervals, variance estimates, or reported test details.
          论文报告了亚稳态延迟悬崖（指帧延迟突然从较低水平转为无法恢复的停顿）实验结果的重复运行次数，但准入实验、跨模型容量实验和 MiniCPM-o 的亚稳态延迟悬崖实验都只进行了一次全新运行。若干关于延迟和正确性的结论没有给出置信区间、方差估计或具体检验细节。
          claim_kind:: analyst_assessment
          evidence:: E11, E15
        - The supplied text names datasets, models, hardware, and major load parameters but does not enumerate the exact audio sample list, all controller gains, or a complete command matrix; cross-engine reproduction was not completed because SGLang hit an NVIDIA GPU software-toolchain conflict.
          所提供的文本列出了数据集、模型、硬件和主要负载参数，但没有逐项列出确切的音频样本清单、所有控制器增益或完整的命令矩阵。由于 SGLang 遇到了 NVIDIA GPU 软件工具链冲突，研究者未能完成跨推理引擎复现。
          claim_kind:: analyst_assessment
          evidence:: E14, E15
- ## Technical Judgment
    - **What Holds Up:** The root-cause story is stronger than a latency-only benchmark because the paper triangulates the user-visible wall, KV-pool occupancy, scheduler queue state, an early-trace timing model, and a direct state-bounding intervention. Within the evaluated stack, the evidence supports memory exhaustion as the causal trigger rather than gradual attention compute.
      **站得住的结论:** 这篇论文的根因论证强于只测延迟的基准测试，因为它综合利用用户可见的亚稳态延迟悬崖、键值缓存池占用率、调度器队列状态、基于运行初期轨迹的时间模型，以及直接限制状态大小的干预来进行交叉印证。在所评估的软件栈中，证据支持将内存耗尽视为触发问题的原因，而不是逐渐增加的注意力计算。
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E8
        - The matched-policy comparison changes the retention rule while holding the end-to-end stack fixed, and the internal trace shows allocation failure and all-session queuing at the same instant; this is persuasive causal evidence for C1.
          配对策略比较只改变保留规则，同时保持端到端软件栈不变。内部轨迹还显示，分配失败与所有会话进入队列发生在同一时刻。这些结果为 C1 提供了有说服力的因果证据。
          claim_kind:: analyst_assessment
          evidence:: E6, E7
        - The first-order model earns credibility by predicting a second model with a different fill rate rather than fitting only one wall, though two configurations are not enough to establish a universal error bound for C2.
          这个一阶模型不仅拟合了单个亚稳态延迟悬崖，还成功预测了填充速率不同的第二个模型，因此具有一定可信度。不过，仅凭两种配置还不足以为 C2 确立普适的误差界限。
          claim_kind:: analyst_assessment
          evidence:: E8
        - The quality study includes a useful negative control, the sink-capable kernel with sinks disabled, and separates turn-based from free-running decode; that design supports the mechanism behind C4 more convincingly than a single aggregate score would.
          质量研究设置了一个有用的阴性对照：使用支持注意力汇聚点的内核，但禁用这些汇聚点。注意力汇聚点是保留下来的最前部结构词元，用于为生成过程提供锚点。该研究还区分了按轮次进行的解码与自由运行式解码；解码是指利用已有注意力状态生成后续输出词元。与只使用单一汇总分数相比，这种设计更有力地支持了 C4 背后的机制。
          claim_kind:: analyst_assessment
          evidence:: E11, E12
    - **Where It May Fail:** Metronome is best suited to persistent workloads whose state grows every frame, must stay resident, and can tolerate an explicit recent-context horizon. Its benefit or correctness can diminish when any of those preconditions breaks.
      **可能失效之处:** Metronome 最适合具有以下特征的持续性工作负载：状态会随每个交互帧增长，状态必须常驻显存，并且任务能够接受明确设定的近期上下文范围上限。只要其中任何一个前提不成立，Metronome 的收益或正确性就可能下降。
      claim_kind:: analyst_assessment
      evidence:: E12, E15
        - Tasks requiring exact access to facts older than the retained recent-context window will fail semantically even if service remains stable; the paper directly observes that sinks preserve generation behavior, not beyond-window recall, so retrieval or summarization must supply old content.
          如果任务需要准确访问早于所保留近期上下文窗口的事实，那么即使服务仍能稳定运行，任务也会在语义上失败。论文直接观察到，注意力汇聚点能够维持生成行为，却不能保留对窗口之外内容的回忆能力。因此，必须通过检索或摘要机制提供旧内容。
          claim_kind:: analyst_assessment
          evidence:: E12
        - A model whose early tokens do not act as attention sinks, or whose positional and attention rules differ from the tested backbone, may need another anchor design; the full sink mask's quality effect is replicated on only one model.
          如果某个模型的早期词元不能充当注意力汇聚点（attention sink，即吸收大量注意力权重并帮助稳定生成的早期词元），或者其位置处理规则和注意力规则不同于已测试的骨干模型，那么它可能需要另一种锚点设计。此外，完整汇聚点掩码对质量的影响只在一个模型上得到复现。
          claim_kind:: analyst_assessment
          evidence:: E15
        - The admission result assumes arrivals can be rejected and bounded-state latency remains monotone under load; heterogeneous frame budgets, mixed windows, bursty turn-taking, or substantial idle gaps could change that signal and make swapping or recomputation competitive again.
          有关准入控制的结论以两个假设为前提：系统可以拒绝新到达的请求；在驻留状态规模有界时，延迟仍随负载单调上升。驻留状态是会话保持活跃期间一直保留在显存中、而不被换出或重新计算的每会话状态。如果不同会话采用不同的帧预算、窗口大小和轮流交互模式，或者请求突发到达、存在较长的空闲间隔，这个负载信号就可能发生变化。帧预算是指在下一次截止期限到来前完成一帧交互所允许的实际时间。在这些情况下，状态换出或重新计算可能会重新具备竞争力。
          claim_kind:: analyst_assessment
          evidence:: E10, E15
    - **Relation to Other Work:** Metronome combines three established lineages at a workload boundary they do not jointly cover: persistent language-model serving, bounded or streaming attention, and feedback admission for recurring deadlines. Its novelty is the systems claim that bounding resident state is what makes overload feedback observable.
      **与已有工作的关系:** Metronome 在三条现有技术路线尚未共同覆盖的工作负载边界上，将它们结合起来：持久化语言模型服务、有界注意力或流式注意力，以及面向周期性截止期限的反馈式准入控制。周期性截止期限会反复到期，系统每次都必须在相应期限之前完成任务。Metronome 的新意在于提出了一项系统层面的主张：只有限制驻留状态的规模，系统才能观测到可用于反馈控制的过载信号。
      claim_kind:: analyst_assessment
      evidence:: E17
        - vLLM and SGLang supply persistent requests and continuous batching but optimize throughput and leave session state unbounded; Metronome retains their execution substrate while adding a per-session retention policy and recurring-deadline gate.
          vLLM 和 SGLang 支持持久请求与连续批处理。连续批处理是指系统反复把当前已准备好执行的所有请求组合到共享的计算步骤中，而不是等待一个固定批处理全部结束。不过，这两个系统主要优化吞吐，并未限制会话状态的规模。Metronome 沿用它们的执行基础设施，同时增加按会话设置的状态保留策略，以及面向周期性截止期限的准入门控机制。
          claim_kind:: analyst_assessment
          evidence:: E3, E17
        - Sliding or streaming attention bounds how many tokens remain relevant, and attention sinks preserve stable generation; cache-compression methods instead reduce bytes per retained token, so the paper argues the two approaches compose rather than compete.
          滑动注意力或流式注意力会限制仍然相关的词元数量，而注意力汇聚点能够维持生成过程的稳定性。相比之下，缓存压缩方法减少的是每个被保留词元占用的字节数。因此，论文认为这两类方法可以组合使用，而不是相互竞争。
          claim_kind:: analyst_assessment
          evidence:: E5, E17
        - Classical real-time scheduling contributes recurring deadlines and AIMD contributes feedback control, but neither supplies a faithful load signal when state is unbounded. The closest prior to open next is StreamingLLM by Xiao et al., which establishes sink-anchored streaming attention; Metronome's separating dimension is end-to-end memory failure and admission in live serving.
          经典实时调度提供了采用周期性截止期限的任务模型，而加性增、乘性减（Additive-Increase/Multiplicative-Decrease，AIMD）提供了反馈控制规则：存在余量时以固定的小步幅增加容量，拥塞信号接近上限时则按比例削减容量。但是，当状态规模没有上界时，两者都无法提供能够如实反映负载的信号。接下来最值得优先阅读的相关工作是 Xiao 等人提出的 StreamingLLM，它确立了以汇聚点为锚的流式注意力方法。Metronome 与它的主要区别在于，Metronome 研究了在线服务中的端到端内存失效和准入控制。
          claim_kind:: analyst_assessment
          evidence:: E12, E17
    - **Open Questions:** The next evidence should test whether the state-bound-to-signal chain survives changes in engine, model attention behavior, and realistic session heterogeneity.
      **开放问题:** 下一步需要通过实验证据检验：当推理引擎、模型的注意力行为以及真实会话的异质性发生变化时，「限制状态规模→获得可观测负载信号」这一链条是否仍然成立。
      claim_kind:: analyst_assessment
      evidence:: E15
        - Can the wall, sink-anchored mask, and admission convergence be reproduced on SGLang, another GPU generation, and a second full-attention backbone without vLLM- or Blackwell-specific behavior?
          能否在 SGLang、另一代图形处理器（Graphics Processing Unit，GPU）以及第二个采用全注意力机制的骨干模型上，复现亚稳态延迟悬崖（wall，即帧延迟从低位突然转为无法恢复的停顿）、汇聚点锚定掩码和准入控制的收敛性，并且不依赖 vLLM 或 Blackwell 的特有行为？
          evidence:: E15
        - Does per-frame latency stay monotone when sessions have mixed ages, windows, frame budgets, output lengths, and natural turn-taking rather than synchronized open-loop audio?
          如果各会话的已运行时长、窗口大小、帧预算和输出长度各不相同，并采用自然的轮流交互，而不是同步且不根据系统反馈调整发送节奏的开环音频输入，那么每帧延迟是否仍会随负载单调上升？
          claim_kind:: analyst_assessment
        - What retrieval, summarization, or tiered-state policy can restore exact beyond-window recall without reintroducing a time-growing resident pool or a re-encoding toll that violates the frame budget?
          哪种检索、摘要或分层状态策略能够恢复对窗口之外信息的精确召回，同时又不重新引入随时间增长的驻留状态池，也不产生违反帧预算的重编码开销？
          claim_kind:: analyst_assessment
    - **Transferable Lesson:** Before designing feedback control for a recurring service, bound every per-session resource that can grow with age. This converts a hidden time-to-exhaustion failure into a provisionable per-session budget and gives latency or another load metric a chance to degrade early enough for control to act.
      **可迁移启发:** 在为周期性服务设计反馈控制机制之前，应先限制所有会随会话持续时间增长的单会话资源。这样就能把隐藏的「资源耗尽时间」故障转化为可预先配置的单会话资源预算，并让延迟或其他负载指标有机会及早恶化，从而使控制机制来得及采取措施。
      claim_kind:: analyst_assessment
      evidence:: E18
- ## Glossary
  collapsed:: true
    - Periodic real-time task: Work that becomes due repeatedly and must finish before each recurring deadline; here, every interaction frame is one task instance.
      周期性实时任务：反复到期、且每次都必须在相应截止时间之前完成的工作；在这里，每个交互帧都是一个任务实例。
    - Key-value cache: Saved attention keys and values for earlier tokens, reused so the model does not recompute the whole history on every frame.
      键值缓存（KV cache）：为先前词元保存的注意力键和值。模型会复用这些数据，从而不必在每一帧都重新计算全部历史内容。
    - Resident state: Per-session state kept in GPU memory while the session remains active, rather than swapped out or recomputed.
      常驻状态：会话保持活跃期间，保留在图形处理器（GPU）内存中的单会话状态，而不是换出这些状态或重新计算它们。
    - Prefill and decode: Prefill encodes newly arrived input into attention state; decode generates the next output tokens using that state.
      预填充与解码：预填充把新到达的输入编码为注意力状态；解码利用该状态生成后续的输出词元。
    - Continuous batching: A serving method that repeatedly groups all requests currently ready for work into shared GPU steps instead of waiting for a fixed batch to finish.
      连续批处理：一种服务方法，它反复把当前所有已准备好处理的请求组成一组，共同执行图形处理器计算步骤，而不是等待一个固定批处理全部完成。
    - Sink-anchored sliding window: A retention rule that keeps the latest W tokens plus the first S structural tokens; the old prefix anchors generation while middle history is freed.
      汇聚点锚定滑动窗口：一种保留规则，它保留最新的 W 个词元和最前面的 S 个结构词元。旧前缀为生成过程提供锚点，同时释放中间的历史内容。
    - Frame budget: The wall-clock time available to finish one recurring interaction frame before the next deadline.
      帧预算：在下一次截止时间到来之前，可用于完成一个周期性交互帧的实际经过时间。
    - Schedulable concurrency: The largest number of simultaneously active sessions for which every frame can still complete within its budget.
      可调度并发数：在确保每一帧仍能在其预算内完成的前提下，可同时保持活跃的最大会话数。
    - Pool-fill model symbols: ρ(t) is pool occupancy over time, ρ0 its starting value, N concurrent sessions, r one session's fill rate, and t_sat the predicted saturation time.
      池填充模型符号：ρ(t) 表示池占用量随时间的变化，ρ0 表示池的初始占用量，N 表示并发会话数，r 表示单个会话的填充速率，t_sat 表示预测的饱和时间。
    - Additive-increase/multiplicative-decrease: A feedback rule that probes upward by small fixed steps when there is headroom and cuts capacity proportionally when a congestion signal approaches its limit.
      加性增大/乘性减小（Additive-increase/multiplicative-decrease，AIMD）：一种反馈控制规则。当系统仍有余量时，它以较小的固定步长逐步提高容量；当拥塞信号接近上限时，它按比例降低容量。
    - Metastable latency cliff: A sudden transition from low frame latency to an unrecoverable stall; metastable means small run-to-run changes decide whether saturation occurs before the session ends.
      亚稳态延迟悬崖：帧延迟从较低水平突然转变为无法恢复的停滞状态。「亚稳态」是指，每次运行之间的微小变化会决定系统是否在会话结束前达到饱和。
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/metadata | Title page | high
      locator:: p. 1, title and author block; arXiv header
      quote:: Metronome: Bound the Cache, Keep the Beat for Real-Time Interaction Model Serving. Jiaying Meng, Independent Researcher; Bojie Li, Pine AI. arXiv:2607.02640v1 [cs.SD], 2 Jul 2026.
    - **E2:** problem/paper_statement | §2 Interaction Sessions Are Periodic Real-Time Tasks | high
      locator:: §2, The task model; Fig. 3
      quote:: A session presents a new audio chunk once per frame. At frame k the engine must encode and prefill the new chunk, then decode up to τ output tokens. The deadline recurs, and the per-session KV cache is pinned and grows with every frame for the life of the conversation.
    - **E3:** gap/paper_statement | §1 Introduction and §2 | high
      locator:: §1, prior-gap paragraph; §2, What vLLM and SGLang provide
      quote:: LLM serving assumes requests are ephemeral, while classical real-time scheduling assumes periodic tasks have bounded state. vLLM resumable requests and SGLang streaming sessions keep a session's KV live across frames, but neither addresses the unbounded-state half or offers per-frame schedulability or admission.
    - **E4:** system_design/implementation_detail | §4 Metronome: Bound the State | high
      locator:: §4 and Fig. 2
      quote:: The in-engine windowed KV retains only each session's last W tokens plus a few pinned attention-sink tokens. On the latency signal this restores, an online AIMD admission controller discovers the schedulable concurrency and sheds the surplus cleanly.
    - **E5:** implementation/implementation_detail | §4.1 In-engine windowed KV, anchored by sinks | medium
      locator:: §4.1; Appendix A, Window half and Sink half
      quote:: Metronome sets sliding_window=W on decoder-attention layers, the KV manager pins each request's first blocks instead of freeing them, and the attention mask admits [0, S) union [t-W, t]. The resident request grows logically while the engine retains only within the bound.
    - **E6:** result/experiment_result | §5.2 Bounding the state removes the cliff | high
      locator:: §5.2; Fig. 4; Appendix D, Table 1
      quote:: With identical stack, model, and load, differing only in bounded KV, unbounded serving walls in 14/20 runs across the two batches; windowed serving in 0/20. The runs last 300 seconds at N in {96, 128}, with per-run outcomes reported in Table 1.
    - **E7:** result/profiling | §3 Anatomy of the Collapse | high
      locator:: §3, mechanism paragraph; Fig. 5
      quote:: Pool occupancy climbs monotonically to capacity, at which instant the running count drops to zero and all N sessions queue. The scheduler can no longer allocate blocks, and the stall never recovers under open-loop audio; windowed occupancy plateaus far below capacity.
    - **E8:** formula/profiling | §3.1 The cliff is predictable | medium
      locator:: §3.1, Eq. 1; Fig. 6
      quote:: Pool occupancy under unbounded KV rises linearly as ρ(t)=ρ0+Nrt, giving tsat=(1-ρ0)/(Nr). An early-trace fit predicts the measured stall at 145 versus 148 seconds on Qwen3-Omni-30B and 99 versus 114 seconds on MiniCPM-o.
    - **E9:** result/experiment_result | §3.1 The cliff is predictable | medium
      locator:: §3.1, bounded-state paragraph; Fig. 6b
      quote:: The windowed plateau is linear in N, about 0.2% of the pool per session at W=1024, extrapolating to a memory ceiling of about 500 sessions, above the deadline-schedulable concurrency of about 209.
    - **E10:** result/experiment_result | §5.3 Admission converges only with bounded state | medium
      locator:: §5.3; Fig. 7
      quote:: With 512 sessions offered at 8/s and a 600 ms latency target, the bounded worker settles at N*≈209 and steady p99 latency of 12 ms. Against unbounded KV, the identical controller admits past this point on a flat signal and ends at the roughly 1.6 s wall.
    - **E11:** result/ablation | §5.4 Quality and Appendix D | medium
      locator:: Appendix D, Turn-based quality detail
      quote:: In the turn-based probe at N=96 over 75-second sessions, answer-stated counts are 96/96 for both vanilla and windowed policies, with per-frame correctness about 70% versus 68%, reported as statistically indistinguishable.
    - **E12:** ablation/ablation | §5.4 Quality: both halves of the bound | medium
      locator:: §5.4; Fig. 8; Appendix D, Table 2
      quote:: Every sink-ablated window declines toward zero after the window passes the session start, including the sink-capable kernel with sinks off. With W=1024 plus pinned sink tokens, the full bound holds an age-independent profile; a zero-sink control reproduces the decay.
    - **E13:** ablation/ablation | §5.2 and Appendix D | medium
      locator:: Appendix D, Fig. 10 and Fig. 11
      quote:: Application-level recycling avoids the wall but its periodic re-encode reaches p50 of about 14-17 ms and p90 of 36 ms, while the in-engine window stays flat. Window sizes through 2048 tokens, about 80 seconds, keep p50 and p90 near 5 ms.
    - **E14:** experiment_setup/paper_statement | §5.1 Setup | high
      locator:: §5.1, full setup paragraph
      quote:: All experiments run end-to-end on one NVIDIA RTX PRO 6000 Blackwell with real LibriSpeech and spoken-question audio in 20 ms chunks. Each point uses a freshly started worker; the baseline is unmodified vLLM-realtime with the same engine, stack, and load.
    - **E15:** limitation/limitation | §7 Limitations and Future Work | high
      locator:: §7, all four limitation paragraphs
      quote:: All results are from one Blackwell GPU and one engine; the wall is demonstrated on two models, while admission and quality are on the 30B. Admission, per-model capacity, and MiniCPM-o wall results are single fresh runs, and richer conversational dynamics are out of scope.
    - **E16:** implementation/implementation_detail | Appendix A and Appendix B | medium
      locator:: Appendix A, Sink half; Appendix B, Enabling Omni Streaming on Blackwell
      quote:: The sink mask is implemented in vLLM's Triton attention backend and tested against a float32 reference with freed blocks poisoned. The artifact also ships four Blackwell engine fixes plus the bounded-KV patch; the paper links a public code repository.
    - **E17:** prior_work/paper_statement | §8 Related Work | medium
      locator:: §8, serving, attention, and scheduling paragraphs
      quote:: Metronome uses resumable resident-KV serving as its substrate, reuses sliding-window and attention-sink ideas to bound retained tokens, and applies classical recurring-deadline admission with additive-increase/multiplicative-decrease feedback. Per-token KV reduction is described as orthogonal because it shrinks each token rather than the number retained.
    - **E18:** insight/paper_statement | §6 Discussion: Beyond Voice | low
      locator:: §6, first and second paragraphs
      quote:: The paper argues that any recurring serving loop with monotonically growing pinned session state can manufacture the same cliff, including agents, streaming-video assistants, and stateful retrieval caches. It proposes a per-session state bound as a first-class serving parameter.
