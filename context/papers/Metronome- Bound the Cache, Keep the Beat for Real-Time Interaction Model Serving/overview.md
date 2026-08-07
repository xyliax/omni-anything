- **Title:** Metronome: Bound the Cache, Keep the Beat for Real-Time Interaction Model Serving
- **Summary:** Metronome bounds each live session's resident attention state so long-running interaction serving avoids a hidden memory cliff and exposes a usable latency signal for overload control.
- **Paper Type:** system
- **Venue:** arXiv preprint arXiv:2607.02640v1, 2026
- **Authors:** Jiaying Meng (Independent Researcher); Bojie Li (Pine AI)
- **Keywords:** real-time interaction model serving, KV cache, periodic real-time task, sliding-window attention, attention sinks, admission control, AIMD
- ## Orientation
    - **Background:** Real-time interaction models listen and answer continuously. To avoid recalculating the conversation for every audio frame, the serving engine keeps previously computed attention state in GPU memory, called the key-value cache.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** During a long call, every participant keeps adding saved state. If that state never leaves, a fixed memory pool can fill and freeze all conversations even though the usual delay dashboard looked healthy moments earlier.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** Unlike a chatbot turn, a live session has no quiet gap for moving or rebuilding state. Its deadline repeats, while the warning signal stays calm until failure, so an overload gate has no time to react.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Keep only a recent slice of each session's saved state, anchored by a tiny preserved beginning, so memory stays bounded and delay changes gradually enough to guide admissions.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a systems view of continuous voice-model serving: it identifies the missing state bound between throughput-oriented language-model engines and recurring-deadline scheduling, then shows why that bound is prerequisite to overload control.
      claim_kind:: analyst_assessment
      evidence:: E2, E3
    - **One-Sentence Contribution:** Metronome prevents long-lived interaction sessions from exhausting GPU attention memory by bounding each session inside the engine, which also turns latency into a useful signal for deciding how many sessions to accept.
      evidence:: E4, E6
    - **Mental Model:** Picture a café that serves every seated customer on each bell: Metronome limits how much table space each customer may keep, so the room gets gradually busier instead of becoming impassable all at once, and the host can stop admitting people before service breaks.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence combines repeated long-run failures, internal memory traces, a cross-model timing prediction, a controlled admission comparison, and a quality ablation.
      evidence:: E6, E8, E10, E12
        - Supports C1: Qwen3-Omni-30B, twenty fresh five-minute runs per policy at two concurrency levels; unmodified vLLM-realtime; memory-wall incidence; 14/20 versus 0/20; repeated but regime-dependent support, Fig. 4.
          evidence:: E6
        - Supports C2: Qwen3-Omni-30B and MiniCPM-o; early linear pool-fill fit versus measured stall; saturation time; 145 versus 148 seconds and 99 versus 114 seconds; direct two-model support, Fig. 6.
          evidence:: E8
        - Supports C3: 512 offered sessions arriving at eight per second with a 600 ms target; identical unbounded controller; admitted capacity and 99th-percentile frame latency; bounded serving settles near 209 sessions at 12 ms while unbounded serving reaches the wall; single-run support, Fig. 7.
          evidence:: E10
        - Supports C4: Qwen3-Omni-30B free-running sessions with a recent-token window and pinned starting tokens; sink-ablated windows and unbounded serving; age-dependent spoken-question correctness; the full bound stays age-independent while every sink ablation decays toward zero; controlled single-model support, Fig. 8.
          evidence:: E12
    - **Main Caveat:** The evidence establishes one vLLM-based stack on one Blackwell GPU, not a hardware- or engine-independent law; only two models are driven to the wall, and control and quality are studied mainly on one model.
      claim_kind:: analyst_assessment
      evidence:: E15
- ## Argument Map
    - **Problem and Stakes:** A streaming interaction session is a periodic real-time task, meaning the same work must finish before a recurring frame deadline, while its key-value cache (KV cache), the saved attention state for earlier tokens, remains resident and grows. Once the engine's fixed pool of KV memory blocks fills, all sessions can stall and return empty frames on time, so latency and deadline-miss alarms may report health while users hear silence.
      evidence:: E2, E6, E7
    - **Prior Gap:** Throughput-oriented language-model engines assume requests eventually finish or pause, and classical real-time scheduling assumes each recurring task has bounded state. vLLM and SGLang can keep a long-lived request's KV cache resident across frames, but the paper finds no built-in per-session state bound, recurring-deadline capacity rule, or admission gate for this workload.
      evidence:: E3, E17
    - **Key Insight:** The apparent latency failure is actually a memory-allocation threshold: frame computation remains cheap until monotonically growing resident state consumes the last block. Bounding state changes memory use from a time-growing ramp into a concurrency-proportional plateau, removing the hidden failure clock and exposing load through latency before memory is exhausted.
      evidence:: E7, E9
    - **Claims:** The paper's argument reduces to four falsifiable claims about failure, prediction, control, and quality.
      claim_kind:: analyst_assessment
        - C1: Unbounded resident KV in long-running periodic sessions causes a memory-triggered, sometimes run-sensitive, observability-silent stall, while an in-engine per-session bound eliminates that stall under matched experiments.
          evidence:: E6, E7
        - C2: Early KV-pool growth predicts when unbounded serving will saturate, whereas bounded serving reaches a stable memory plateau whose capacity exceeds the measured deadline-limited concurrency.
          evidence:: E8, E9
        - C3: Once state is bounded, per-frame latency becomes a faithful enough load signal for online admission to discover schedulable concurrency; the same controller over-admits when state is unbounded.
          evidence:: E10
        - C4: A recent-token window preserves the reported turn-based quality, and pinned starting tokens called attention sinks are necessary to keep free-running generation healthy, although no fixed window preserves information beyond its horizon.
          evidence:: E11, E12
- ## Mechanism and Design
    - **Core Mechanism:** Metronome gives every live request a fixed-shape resident state and then controls admissions from the resulting latency slope. Its diagnostic model is $\rho(t)=\rho_0+Nrt$ and $t_{\mathrm{sat}}=(1-\rho_0)/(Nr)$, where $\rho(t)$ is KV-pool occupancy at time $t$, $\rho_0$ is initial occupancy, $N$ is concurrent sessions, $r$ is the fraction of the pool consumed per second by one session, and $t_{\mathrm{sat}}$ is predicted saturation time.
      evidence:: E4, E8
        - For each request, the engine retains the latest $W$ tokens, where $W$ is the recent-context window, plus the first $S$ tokens, where $S$ is the pinned attention-sink prefix; it frees intervening KV blocks and permits attention only to that pinned prefix and recent window.
          evidence:: E5
        - On each frame tick, the worker groups all due sessions into one GPU execution step, called continuous batching, and must process their new input and output before frame budget $B$, the recurring deadline.
          evidence:: E2, E4
        - An additive-increase/multiplicative-decrease controller (AIMD) raises the admission cap gradually while latency has headroom, cuts it proportionally near a target fraction of frame budget $B$, and rejects arrivals above the cap.
          evidence:: E4, E10
    - **Data / Control Flow:** The execution path separates the gateway's session gate from the worker's state bound but closes the loop through measured per-frame latency. The same clients and gateway drive bounded and unbounded workers, making the memory policy the central controlled difference.
      evidence:: E4, E14
        - Clients send small audio chunks over a persistent two-way network connection (WebSocket) to a Go gateway, which queues each session for its next frame tick and applies the current admission cap.
          evidence:: E4, E14
        - Once per tick, the gateway sends one batched remote procedure call (gRPC Step) to the GPU worker; for every admitted persistent request the worker encodes new input into cached state (prefill), generates up to a small output allowance (decode), and returns only newly produced tokens.
          evidence:: E2, E4
        - The gateway measures total frame time, feeds it to AIMD, admits sessions up to the learned schedulable concurrency $N^*$, meaning the largest count that still meets every recurring deadline, and sheds the rest with an overload rejection.
          evidence:: E4, E10
    - **Design Decisions:** The design deliberately spends engine integration effort to keep the application simple and to make memory, computation, and feedback share one explicit per-session bound. Its assumptions are that each session can discard most old attention state, arrivals can be rejected, and bounded-state latency changes meaningfully with load.
      claim_kind:: analyst_assessment
      evidence:: E5, E10, E12
        - The window lives inside the engine rather than recycling requests in the application, because recycling must re-encode retained context at every boundary; the tradeoff is a vLLM-specific modification instead of a portable wrapper.
          evidence:: E5, E13
        - For a model that normally looks at all prior tokens, called a full-attention backbone, Metronome pins structural opening tokens rather than early conversation content; too few sinks destabilize free-running decode, while pinning semantic content can bias later answers.
          evidence:: E12
        - A feedback cap replaces a hand-set capacity because safe concurrency depends on model, window, hardware, and arrivals; this choice is valid only after bounding removes the flat-until-failure signal.
          evidence:: E4, E10
    - **Implementation Surface:** Adoption touches vLLM model construction and KV-block retention, plus the gateway's admission policy; exact sink support additionally changes an attention GPU kernel. The window half is narrow, while the full quality-preserving mask is engine- and backend-specific.
      claim_kind:: analyst_assessment
      evidence:: E5, E16
        - The window half sets the decoder layer's existing sliding-window attribute so vLLM builds a windowed KV specification and frees blocks behind it; the paper reports no scheduler, allocator, or public application-programming-interface change for this half.
          evidence:: E5
        - Because FlashAttention's stock window cannot include both an old prefix and a recent suffix, the sink half routes decoder layers to vLLM's Triton backend, extends its attention mask and tile loop, and pins the corresponding first KV blocks.
          evidence:: E5, E16
        - The reported artifact includes the patch, a reference-based kernel check, and four extra fixes needed for omni models on Blackwell; no new external library dependency is reported, and the minimum supported hardware is not established beyond the evaluated RTX PRO 6000.
          claim_kind:: analyst_assessment
          evidence:: E14, E16
- ## Evaluation and Evidence
    - **Setup:** The evaluation uses a real end-to-end audio path on one NVIDIA RTX PRO 6000 Blackwell and compares the same clients, Go gateway, vLLM-realtime worker, and load with only the resident-state policy changed where possible. It measures frame-latency percentiles over elapsed-time buckets, delivery cadence, answer correctness, KV-pool occupancy, waiting requests, and wall incidence.
      evidence:: E14, E15
        - Real LibriSpeech and spoken-question clips arrive in small chunks as distinct, phase-staggered streams to prevent shared prefixes from artificially raising capacity; every data point starts a fresh worker to avoid residual-state bias.
          evidence:: E14
        - The closest baseline is unmodified vLLM-realtime resumable serving, where one persistent request reuses prior KV state; bounded and unbounded comparisons otherwise hold engine, stack, model, audio, and offered load fixed.
          evidence:: E6, E14
        - Short-burst capacity is sampled across four interaction models, but only Qwen3-Omni-30B and MiniCPM-o are driven to the long-duration wall; admission and detailed quality tests center on Qwen3-Omni-30B.
          evidence:: E15
    - **Claim-Evidence Matrix:** Each logical claim has a distinct evidence route, which helps separate repeated outcomes from single-run demonstrations and model-side quality probes.
      claim_kind:: analyst_assessment
        - C1 is supported by repeated wall outcomes under matched policies and by internal traces linking full KV-pool occupancy to all requests entering the wait queue; evidence E6 and E7.
          claim_kind:: analyst_assessment
          evidence:: E6, E7
        - C2 is supported by early-trace predictions on two models and measured plateau scaling across concurrency; evidence E8 and E9, with the memory ceiling partly extrapolated.
          claim_kind:: analyst_assessment
          evidence:: E8, E9
        - C3 is supported by a bounded-versus-unbounded controller comparison using the same latency-only policy; evidence E10, limited by a single bounded open-system ramp and one unbounded arm.
          claim_kind:: analyst_assessment
          evidence:: E10
        - C4 is supported by turn-based parity and free-running window-and-sink controls, including the identical sink-capable kernel with zero sinks; evidence E11 and E12, all on one quality backbone.
          claim_kind:: analyst_assessment
          evidence:: E11, E12
    - **Headline Results:** The results most directly support the state-bound mechanism: the intervention removes repeated long-run stalls, the pool-fill model predicts their timing, and latency-based admission becomes usable only after the intervention.
      evidence:: E6, E8, E10
        - For C1, twenty fresh 300-second Qwen3-Omni-30B runs per policy at 96 or 128 sessions use 10-second bucket median latency and wall incidence: unbounded vLLM-realtime stalls in 14/20, while bounded KV stalls in 0/20; the two batches move from 4/10 to 10/10 unbounded walls, so the asymmetry is repeated but the absolute rate is not calibrated, Fig. 4.
          evidence:: E6
        - For C2, a straight-line fit to early KV-pool occupancy predicts measured saturation at 145 versus 148 seconds for Qwen3-Omni-30B and 99 versus 114 seconds for MiniCPM-o; this is close on the headline model and about 13% off on the second, without reported confidence intervals, Fig. 6.
          evidence:: E8
        - For C3, an arrival stream that continuously offers sessions sends 512 at eight per second to a 600 ms target: bounded serving settles near 209 admitted sessions with steady 99th-percentile frame latency of 12 ms, while the identical unbounded controller reads flat headroom and ends near the 1.6-second wall; both arms are single-run demonstrations, Fig. 7.
          evidence:: E10
    - **Ablations and Sensitivity:** The useful ablations separate memory placement, window size, and pinned-prefix semantics rather than treating bounded context as one opaque switch.
      evidence:: E11, E12, E13
        - For C4 in end-of-sequence-terminated turns, 96 sessions answer correctly under both unbounded and windowed serving, with about 70% versus 68% per-frame correctness reported as statistically indistinguishable; the paper does not report the test statistic or interval.
          evidence:: E11
        - For C4 in five-minute free-running decode at 32 sessions, all zero-sink windows decay toward zero current-question correctness after their windows pass the start, while a 1024-token window with 32 pinned tokens stays age-independent; a zero-sink run on the same kernel isolates the recovery to sinks, but all rows are single fresh runs on Qwen3-Omni-30B, Fig. 8.
          evidence:: E12
        - At the same memory horizon, application-level recycling avoids the wall but re-encoding grows to roughly 14-17 ms median and 36 ms 90th-percentile frame latency, whereas the in-engine window stays flat; windows through 2048 tokens, about 80 seconds, remain near 5 ms, but the 4096-token tail result is treated by the paper as single-run noise, Fig. 10 and Fig. 11.
          evidence:: E13
    - **Reproducibility Gaps:** The paper reports unusually useful engine patches, per-run logs, a randomized order, and a kernel reference check, but the strongest generality and statistical gaps remain experimental rather than packaging-related.
      claim_kind:: analyst_assessment
      evidence:: E15, E16
        - The paper links public code and says the bounded-KV patch, Blackwell fixes, per-run logs, shuffle, and exact mask test ship with the artifact; the supplied text does not identify a commit, artifact version, or archival snapshot.
          evidence:: E6, E16
        - Wall outcomes have repeat counts, but admission, cross-model capacity, and the MiniCPM-o wall use single fresh runs; several latency and correctness conclusions lack confidence intervals, variance estimates, or reported test details.
          claim_kind:: analyst_assessment
          evidence:: E11, E15
        - The supplied text names datasets, models, hardware, and major load parameters but does not enumerate the exact audio sample list, all controller gains, or a complete command matrix; cross-engine reproduction was not completed because SGLang hit an NVIDIA GPU software-toolchain conflict.
          claim_kind:: analyst_assessment
          evidence:: E14, E15
- ## Technical Judgment
    - **What Holds Up:** The root-cause story is stronger than a latency-only benchmark because the paper triangulates the user-visible wall, KV-pool occupancy, scheduler queue state, an early-trace timing model, and a direct state-bounding intervention. Within the evaluated stack, the evidence supports memory exhaustion as the causal trigger rather than gradual attention compute.
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E8
        - The matched-policy comparison changes the retention rule while holding the end-to-end stack fixed, and the internal trace shows allocation failure and all-session queuing at the same instant; this is persuasive causal evidence for C1.
          claim_kind:: analyst_assessment
          evidence:: E6, E7
        - The first-order model earns credibility by predicting a second model with a different fill rate rather than fitting only one wall, though two configurations are not enough to establish a universal error bound for C2.
          claim_kind:: analyst_assessment
          evidence:: E8
        - The quality study includes a useful negative control, the sink-capable kernel with sinks disabled, and separates turn-based from free-running decode; that design supports the mechanism behind C4 more convincingly than a single aggregate score would.
          claim_kind:: analyst_assessment
          evidence:: E11, E12
    - **Where It May Fail:** Metronome is best suited to persistent workloads whose state grows every frame, must stay resident, and can tolerate an explicit recent-context horizon. Its benefit or correctness can diminish when any of those preconditions breaks.
      claim_kind:: analyst_assessment
      evidence:: E12, E15
        - Tasks requiring exact access to facts older than the retained recent-context window will fail semantically even if service remains stable; the paper directly observes that sinks preserve generation behavior, not beyond-window recall, so retrieval or summarization must supply old content.
          claim_kind:: analyst_assessment
          evidence:: E12
        - A model whose early tokens do not act as attention sinks, or whose positional and attention rules differ from the tested backbone, may need another anchor design; the full sink mask's quality effect is replicated on only one model.
          claim_kind:: analyst_assessment
          evidence:: E15
        - The admission result assumes arrivals can be rejected and bounded-state latency remains monotone under load; heterogeneous frame budgets, mixed windows, bursty turn-taking, or substantial idle gaps could change that signal and make swapping or recomputation competitive again.
          claim_kind:: analyst_assessment
          evidence:: E10, E15
    - **Relation to Other Work:** Metronome combines three established lineages at a workload boundary they do not jointly cover: persistent language-model serving, bounded or streaming attention, and feedback admission for recurring deadlines. Its novelty is the systems claim that bounding resident state is what makes overload feedback observable.
      claim_kind:: analyst_assessment
      evidence:: E17
        - vLLM and SGLang supply persistent requests and continuous batching but optimize throughput and leave session state unbounded; Metronome retains their execution substrate while adding a per-session retention policy and recurring-deadline gate.
          claim_kind:: analyst_assessment
          evidence:: E3, E17
        - Sliding or streaming attention bounds how many tokens remain relevant, and attention sinks preserve stable generation; cache-compression methods instead reduce bytes per retained token, so the paper argues the two approaches compose rather than compete.
          claim_kind:: analyst_assessment
          evidence:: E5, E17
        - Classical real-time scheduling contributes recurring deadlines and AIMD contributes feedback control, but neither supplies a faithful load signal when state is unbounded. The closest prior to open next is StreamingLLM by Xiao et al., which establishes sink-anchored streaming attention; Metronome's separating dimension is end-to-end memory failure and admission in live serving.
          claim_kind:: analyst_assessment
          evidence:: E12, E17
    - **Open Questions:** The next evidence should test whether the state-bound-to-signal chain survives changes in engine, model attention behavior, and realistic session heterogeneity.
      claim_kind:: analyst_assessment
      evidence:: E15
        - Can the wall, sink-anchored mask, and admission convergence be reproduced on SGLang, another GPU generation, and a second full-attention backbone without vLLM- or Blackwell-specific behavior?
          evidence:: E15
        - Does per-frame latency stay monotone when sessions have mixed ages, windows, frame budgets, output lengths, and natural turn-taking rather than synchronized open-loop audio?
          claim_kind:: analyst_assessment
        - What retrieval, summarization, or tiered-state policy can restore exact beyond-window recall without reintroducing a time-growing resident pool or a re-encoding toll that violates the frame budget?
          claim_kind:: analyst_assessment
    - **Transferable Lesson:** Before designing feedback control for a recurring service, bound every per-session resource that can grow with age. This converts a hidden time-to-exhaustion failure into a provisionable per-session budget and gives latency or another load metric a chance to degrade early enough for control to act.
      claim_kind:: analyst_assessment
      evidence:: E18
- ## Glossary
  collapsed:: true
    - Periodic real-time task: Work that becomes due repeatedly and must finish before each recurring deadline; here, every interaction frame is one task instance.
    - Key-value cache: Saved attention keys and values for earlier tokens, reused so the model does not recompute the whole history on every frame.
    - Resident state: Per-session state kept in GPU memory while the session remains active, rather than swapped out or recomputed.
    - Prefill and decode: Prefill encodes newly arrived input into attention state; decode generates the next output tokens using that state.
    - Continuous batching: A serving method that repeatedly groups all requests currently ready for work into shared GPU steps instead of waiting for a fixed batch to finish.
    - Sink-anchored sliding window: A retention rule that keeps the latest W tokens plus the first S structural tokens; the old prefix anchors generation while middle history is freed.
    - Frame budget: The wall-clock time available to finish one recurring interaction frame before the next deadline.
    - Schedulable concurrency: The largest number of simultaneously active sessions for which every frame can still complete within its budget.
    - Pool-fill model symbols: ρ(t) is pool occupancy over time, ρ0 its starting value, N concurrent sessions, r one session's fill rate, and t_sat the predicted saturation time.
    - Additive-increase/multiplicative-decrease: A feedback rule that probes upward by small fixed steps when there is headroom and cuts capacity proportionally when a congestion signal approaches its limit.
    - Metastable latency cliff: A sudden transition from low frame latency to an unrecoverable stall; metastable means small run-to-run changes decide whether saturation occurs before the session ends.
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
