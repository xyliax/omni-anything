# Metronome — Research Plan

*Frame-Budget Scheduling and KV-Budget Admission Control for Real-Time Serving of
Interaction Models.*

Status: planning. Last updated: 2026-06-19.

---

## 0. One-paragraph thesis

Serving interaction models is a **per-tick-deadline scheduling problem in which the
per-session KV cache is simultaneously the dominant cost and the schedulability knob.**
Unlike chatbot serving — ephemeral requests, throughput goal, KV swapped out during idle
slack — the unit of work is a *persistent periodic session* with a recurring wall-clock
deadline (80 ms – 1 s), there is no idle slack within a session, and KV must stay
resident because swapping is bandwidth-dominated and blows the frame budget. How KV
behaves is **regime-dependent**: for small open models it *saturates* at a model-set
ceiling within minutes, making the problem *HBM-packing + jitter under a tight deadline*;
for large production models (~1M context, 200B+ MoE) it *never saturates within a
session* and a single session can exceed one GPU's HBM, making it *memory-capacity-bound,
tiered-KV serving*. Metronome is a serving system that, every tick under deadline,
decides per session what stays hot in HBM vs. evicted/offloaded and how many sessions to
admit — with the KV budget trading concurrency/cost against context quality — and a
benchmark that measures the right thing: sustainable concurrent real-time sessions, tail
jitter, and \$/session-hour.

---

## 1. Problem and motivation

### 1.1 What interaction models are, at the serving layer

An *interaction model* ingests continuous audio/video/text and produces output
continuously, on a fixed cadence ("micro-turns" / "ticks"), rather than in
request→response turns. Representative systems and their ticks:

- **TML-Interaction-Small** (Thinking Machines, closed): 276B MoE / 12B active, **200 ms**
  micro-turns, dual *interaction* + *background* model, 0.40 s response latency.
- **Kyutai Moshi** (open): 7B, **80 ms / 12.5 Hz**, true full-duplex speech-to-speech.
- **MiniCPM-o 4.5** (open): ~9B (Qwen3-8B backbone), **1 s** speak/no-speak decision,
  full-duplex omni (audio + video).
- **Qwen2.5-/Qwen3-Omni** (open): 7B / 30B-A3B MoE, block-wise streaming, Thinker-Talker.

At each tick the server performs a *small prefill* (the new input chunk) followed by a
*small decode* (0..k output tokens), appending to a KV cache that persists for the entire
session (minutes to hours).

### 1.2 Why the chatbot-serving assumptions break

| | Chat request | Interaction session |
|---|---|---|
| Lifetime | seconds, KV freed after | minutes–hours, KV pinned throughout |
| KV growth | bounded by context, then released | grows every tick up to a (possibly huge) ceiling |
| Workload shape | bursty prefill + decode | steady, rhythmic: tiny prefill + tiny decode every tick |
| Hard constraint | TTFT / throughput | **recurring per-tick wall-clock deadline** |
| Idle slack | between requests | **none within a session** |
| Right capacity metric | tokens/sec | **sustainable concurrent sessions @ deadline-miss SLO** |

Continuous batching, chunked prefill, prefix/radix caching, KV swap, and KV eviction in
vLLM/SGLang are all tuned for the left column. This is closer to a soft-real-time
multimedia/game-engine workload than to batch inference.

### 1.3 The swap-vs-resident cost argument (motivation, settled)

The tempting "just swap each session's KV to host between ticks and page it back" idea is
**bandwidth-dominated and breaks the deadline.** Swapping moves the KV out and back over
PCIe (≈50 GB/s practical, Gen5) every tick; keeping it resident reads it once from HBM
(≈3.35 TB/s on H100) — a ~130× gap, paid twice per tick, and growing with session age.

Worked numbers (MiniCPM-o, Qwen3-8B backbone, 144 KiB/token fp16):

| Session KV | Swap in+out @ PCIe-5 | HBM read (resident) @ H100 |
|---|---|---|
| 4.3 GB (≈30k tok) | 172 ms | 1.3 ms |
| 13 GB | 520 ms | 3.9 ms |

At a 200 ms tick the swap alone blows the frame. **Conclusion: KV stays resident; the
scarce resource is HBM capacity, not PCIe bandwidth.** Chatbots get away with swap only
because it hides in seconds-to-minutes of idle time between turns; interaction sessions
have no such gap.

**No free locality at small scale.** Dense-attention models read the *entire* KV every
tick (reuse distance = one tick for the whole cache), and different users share no prefix,
so there is no cold subset to demote. The only way to create an evictable cold region is
to change the access pattern (sinks + sliding window / importance eviction) — which is
*lossy* and is precisely Metronome's KV-budget knob. **At large scale this flips** (§1.4).

### 1.4 The regime split (the core framing, settled)

KV is bounded by the context window, not by wall-clock age, so it is a **saturating ramp**
(rises at `token_rate × bytes/token` until the window ceiling, then flat). The ceiling's
height vs. realistic session length defines two regimes:

| Regime | Model / context | KV per session | Attention | Saturates within a session? | Bottleneck | Mechanism |
|---|---|---|---|---|---|---|
| **Small (evaluated)** | 7–9B, 4K–32K | 1–5 GB | dense / windowed | yes, in minutes | HBM packing + tick jitter | keep resident; pack many; budget the window |
| **Large (projected)** | 200B+ MoE, ~1M | **70–300 GB** | sparse/windowed (mandatory) | **no (hours)** | **memory capacity; 1 session > 1 GPU** | tiered KV (HBM/host/NVMe) + offload + deadline scheduling |

Large-scale numbers: at 1M tokens, KV is ~70 GB (MLA) to ~300 GB (GQA, fp16) **per
session**; 276B weights at fp8 are ~276 GB (already multi-GPU before any KV); filling 1M
tokens at 74 tok/s takes ~3.75 h, so realistic sessions **never saturate** and grow the
whole time. At this scale dense attention over 1M tokens per tick is infeasible, so
production models *must* use sparse/windowed attention — which finally creates a genuine
cold set, making tiered KV both necessary and viable. (TML's published "Split-KV
processing 4096 tokens at a time" hint is consistent with blocked KV over a large
context.)

**Honest scoping:** no open model occupies the large regime, so it is *projected
motivation* (analytical model + TML's published serving hints), not an evaluated system.
The mechanism is demonstrated on the small regime where open models exist.

### 1.5 The growing-WCET twist (why classical RT theory doesn't drop in)

Classical real-time scheduling (rate-monotonic / EDF) assumes each periodic task has a
*fixed* worst-case execution time (WCET). An interaction session is a periodic task
(period = tick), but its per-tick WCET is a **saturating ramp**: per-tick attention cost
∝ current KV length, which rises with context until the ceiling. Crucially, **typical
voice interactions (1–3 min) are far shorter than the fill time (Moshi ~5.5 min;
MiniCPM-o 7–55 min depending on video)** — so most sessions spend their *entire* life on
the rising ramp and never reach the plateau. A multi-tenant server therefore holds a
population of tasks at heterogeneous, age-dependent WCETs. Admission control must reason
about the **age-mix**, not just the session count. This bounded-but-non-stationary WCET
is the novel wrinkle on fixed-WCET schedulability theory.

---

## 2. Framing, design, and goals

### 2.1 Design invariant

Every tick, for a multi-tenant, phase-misaligned set of persistent sessions, the server
must (a) read each active session's hot KV from HBM, (b) compute one tick's prefill+decode,
and (c) finish within each session's frame budget — while (d) KV resident across all
admitted sessions fits HBM. Metronome treats (c) as a real-time scheduling constraint and
(d) as an admission/KV-budget constraint, and couples them: **the per-session KV budget
sets both the per-tick WCET (schedulability) and the resident footprint (cost).**

### 2.2 System architecture (Metronome)

Built as a layer on top of SGLang (whose persistent-sequence primitive, upstreamed by TML,
is the foundation), Metronome adds:

1. **Persistent periodic-session object.** Pinned, append-only KV region; not
   request-scoped. Carries period (tick interval), deadline, age, KV budget, and
   degradation state. Accepts incremental input forever; never "completes."

2. **Deadline-aware tick scheduler.** Frame-based: within each frame, form a micro-batch
   of the sessions whose tick is due, ordered by EDF; admit/skip under a frame-budget
   solver. Loses the freedom to delay chunks (they arrive on a wall clock), so scheduling
   is deadline-driven, not throughput-maximizing. Exploits empty ticks (silence / no-speak)
   to reclaim compute for talkers.

3. **Admission controller.** On new-session arrival, runs a schedulability test over the
   current age-mix and proposed KV budget; admits only if all existing sessions keep their
   deadlines. Chooses the new session's KV budget (window length / eviction policy /
   quantization) to fit. Capacity = max admissible sessions at the target miss rate.

4. **Tiered, model-aware KV manager.** Hot working set (sinks + recent window + predicted-
   relevant pages) in HBM; warm KV in host DRAM; cold KV on NVMe or recomputed. Eviction
   policy is pluggable (sliding window / attention-sinks / importance H2O-style /
   summarize-and-offload) and treated as a *quality-coupled knob*. For models that bound
   their own context (Qwen-Omni sliding-window) the manager *complements*; for models that
   don't (Moshi full MHA) it is the *only* KV lever.

5. **Graceful-degradation ladder.** When a frame is over budget, an ordered policy:
   shrink window → drop/merge video frames → coarsen quantization → skip a non-speaking
   tick → shed/migrate a session. Each rung has a measured quality cost; degradation is
   first-class, not an exception path.

### 2.3 Goals (what a win looks like)

- **G1 — Deadline feasibility under load.** Sustain many more concurrent sessions at a
  target deadline-miss rate (e.g. <0.1% missed ticks) than throughput-greedy batching,
  especially at the tight 80 ms (Moshi) end.
- **G2 — Flat latency over session age.** Per-tick latency stays within the frame budget as
  KV grows, where baselines climb and eventually miss frames.
- **G3 — Cost.** Lower \$/session-hour at a fixed SLO via KV budgeting and packing.
- **G4 — Graceful, not catastrophic, quality degradation under overload.**
- **G5 — A predictive admission test** whose predicted capacity matches measured capacity.
- **G6 — A reusable benchmark + metrics** the subfield currently lacks.

### 2.4 Non-goals (kept out to stay focused)

- Fast/slow (interaction + background) co-serving — interesting but orthogonal; left to
  future work to keep the contribution sharp.
- Empty-tick/silence exploitation as a headline — included only as one scheduler
  optimization + ablation, not a separate contribution.
- Training, model architecture, or dialogue quality of the models themselves.

---

## 3. Research contributions

1. **A periodic-deadline serving model for interaction sessions, with KV-budget admission
   control.** Formalize the session as a periodic task with a *saturating-ramp* WCET and
   derive a schedulability/admission test over a multi-tenant, phase-misaligned, mixed-age
   population. KV budgeting *is* the schedulability mechanism (unifies "scheduling" and "KV
   management" into one knob). **Novelty:** first to model interaction-model serving as
   bounded-but-non-stationary-WCET real-time scheduling.

2. **A tiered, model-aware KV manager whose eviction policy is a quality-coupled cost
   knob.** Key empirical result to establish: **serving-level KV management is *essential*
   for models with no built-in context bounding (Moshi-style full MHA) and *complementary*
   for models that window themselves (Qwen-style)** — a finding only visible because the
   eval set spans both. **Novelty:** ties KV reduction to per-tick schedulability and \$,
   not just memory, under a real-time deadline.

3. **A real-time capacity/jitter benchmark for streaming interaction serving.** Metrics:
   max sustainable concurrent sessions at a deadline-miss SLO; p50/p99/p999 per-tick
   jitter; \$/session-hour — replacing tokens/sec and TTFT. **Novelty:** the field has no
   serving-capacity benchmark for full-duplex models (Full-Duplex-Bench measures dialogue
   quality, not serving capacity).

---

## 4. Formal model (to be firmed up before building)

### 4.1 Notation

- Session *i* has period `T_i` (tick interval), relative deadline `D_i ≤ T_i`, phase
  offset `φ_i` (wall-clock alignment), age `a_i(t)`, token rate `r_i` (modality-dependent),
  bytes/token `b` (model attention config), and KV budget `B_i` (max resident tokens).
- Context length `L_i(t) = min(r_i · a_i(t), B_i)`.
- Per-tick execution time `C_i(t) = C_fixed + α · L_i(t)` (attention is memory-bound:
  α ≈ b / HBM-bandwidth; `C_fixed` covers the small MoE/FFN compute for k new tokens and
  launch overhead). This is the **saturating ramp**: `C_i` rises until `L_i` hits `B_i`.

### 4.2 Schedulability / admission test (sketch)

On a single accelerator with frame budget `F`, a set `S` of sessions is feasible if, for
every frame, the EDF-ordered batched execution of all due sessions completes within their
deadlines. Because `C_i` is non-stationary, the test must hold over the **worst-case
age-mix** the admission policy permits. Two tractable forms to derive and compare:

- **Worst-case (plateau) bound:** treat every session at its ceiling `C_i^max = C_fixed +
  α·B_i`; conservative but simple; `Σ batched-cost ≤ F`.
- **Age-aware bound:** track the age distribution and the rate of new arrivals; tighter,
  admits more sessions, but must bound the transient when many sessions co-age.

Resident-memory constraint: `Σ_i B_i · b ≤ HBM_KV` (HBM minus weights). Admission jointly
chooses membership and per-session `B_i` to maximize admitted count subject to both the
timing and memory constraints. **The KV budget `B_i` is the single variable that appears
in both constraints** — the heart of the paper.

### 4.3 Batched-cost model

Per-tick decode is memory-bound and tiny per session; many phase-aligned ticks are batched.
Cost is dominated by the aggregate HBM traffic to read all batched sessions' hot KV plus
the new-chunk prefill. Validate the model against measured per-tick latency (G5).

---

## 5. Related work (summary; full survey in `RELATED_WORK.md`)

Seven axes; every existing bucket sits in ≤2 of {persistent periodic deadline,
growing-then-bounded KV as 1st-class, multi-tenant batched, capacity-as-metric}.
Metronome sits in all four.

1. **Throughput serving** — Orca (continuous batching), vLLM/PagedAttention,
   SGLang/RadixAttention. *Request-scoped, throughput goal.*
2. **SLO/deadline-aware serving** — Sarathi-Serve, SLAI, TetriServe, StreamWise,
   TokenFlow, Aladdin, PolyServe. *Per-request static deadlines, still bursty.*
3. **Incremental-context / streaming-input serving** — Stream2LLM (overlap retrieval with
   prefill). *One-shot answer with streamed input, not decode-every-tick.*
4. **KV compression / eviction** — StreamingLLM, H2O, SnapKV, ShadowKV. *Memory-driven,
   quality-preserving, offline-evaluated, never tied to a per-tick deadline.*
5. **Long-context KV-offload / sparse serving** — ShadowKV, InfiniGen, Quest. *Huge KV,
   sparse access, host offload — but one-shot long-context inference, not real-time
   streaming with deadlines.*
6. **Full-duplex / streaming dialogue models** — Moshi, MiniCPM-o, Qwen-Omni, TML,
   Voxtral, LWS, neural-FSM duplex. *Model/architecture papers; single-stream demos.*
7. **Classical real-time scheduling** — RMS/EDF, schedulability analysis, admission
   control, mixed-criticality. *The theory we import; assumes fixed WCET, which §1.5
   violates.*

The empty intersection — huge-growing-KV + sparse access + per-tick real-time deadline +
multi-tenant — is exactly the interaction-model serving regime.

---

## 6. Experiments

### 6.1 Confirmed eval anchors (numbers verified from primary sources)

| | **Moshi** | **MiniCPM-o 4.5** | **Qwen2.5-/Qwen3-Omni** |
|---|---|---|---|
| Duplex | true full-duplex (2 audio streams + text monologue, barge-in) | full-duplex omni | streaming, turn-based (barge-in unconfirmed) |
| Deadline / tick | **80 ms (12.5 Hz)** | **1 s** speak/no-speak | block-wise (~100s ms) |
| Backbone | 7B dense, **32 L, MHA (32 heads, d=128)** | ~9B, Qwen3-8B **GQA (36 L, 8 KV heads, d=128)** | 7B (2.5) / **30B-A3B MoE** (3) |
| Attention bounding | **none — full causal** | dense | block-wise + sliding-window DiT |
| KV / timestep | **~1 MiB / frame** (MHA, fat) | **144 KiB / token** (GQA, thin) | bounded by window |
| Context ceiling | **4096 frames ≈ 5.46 min → ~4 GB** | undocumented (Qwen3 native 32K) | windowed |
| Accumulation | 12.5 Hz fixed, low | 10 tok/s audio, **64 tok/frame video**, 25 tok/s speech | block |
| KV-cache discussion in paper | none | none | none |

Why this set: it spans (a) the deadline spectrum **80 ms → 1 s (~12×)**; (b) **fat-KV MHA
(Moshi) vs thin-KV GQA (MiniCPM-o)**; (c) **no model-level KV bounding (Moshi) vs built-in
windowing (Qwen-Omni)**; (d) **dense vs MoE**, bridging toward the TML motivation.

Corrections baked in: **Qwen2-Audio** (audio-understanding, not duplex) → replaced by
**Qwen2.5-/Qwen3-Omni**; **MiniCPM-V** (vision understanding) → **MiniCPM-o 4.5** (the omni
duplex variant).

### 6.2 Baselines

- **B0** vanilla SGLang/vLLM, request-per-tick (no persistent session) — naive strawman.
- **B1** SGLang + persistent session + throughput-greedy continuous batching (no deadline
  awareness) — the strong "obvious" baseline to beat.
- **B2** per-request deadline scheduler (SLAI-style, adapted) — static deadlines.
- **M** Metronome (ours).

### 6.3 Ablations

No admission control; full-KV vs budgeted; fixed cap vs adaptive budget; EDF vs FIFO;
with/without degradation ladder; with/without empty-tick (silence) exploitation;
eviction-policy sweep (sliding window / sinks+window / H2O-importance / summarize-offload).

### 6.4 Workloads

- **Real, reproducible anchor:** Moshi (80 ms) and MiniCPM-o 4.5 (1 s), driven by real
  full-duplex dialogue traces (audio; audio+video for MiniCPM-o).
- **Synthetic session generator:** parameterized arrival rate, session-length distribution,
  talk/silence ratio, video fps — to sweep load and plot capacity curves under control.
- **Long-session stress:** sessions approaching/at the model's context ceiling, to exercise
  saturated WCET (Moshi at 5.5 min) and, for MiniCPM-o, the truncation policy at the cap.

### 6.5 Metrics (the §3.3 benchmark)

- **Deadline-miss rate** per tick (the SLO).
- **Jitter:** p50 / p99 / **p999** per-tick latency (tail is the story; a missed frame is an
  audible glitch).
- **MSCS:** max sustainable concurrent sessions at a target miss rate.
- **Cost:** \$/session-hour and GPU-hours per 1000 session-minutes at fixed SLO.
- **Quality under load:** a task-quality proxy (ASR WER on Moshi output / response
  appropriateness) to show degradation is graceful, not a cliff.

### 6.6 Headline plots / claims

1. **Per-tick latency vs session age** — baseline climbs with KV and crosses the deadline;
   Metronome stays flat (bounded WCET). The money plot; lead with it.
2. **MSCS vs deadline-miss rate** — Metronome vs B0/B1/B2, at 80 ms and 1 s.
3. **\$/session-hour at fixed SLO.**
4. **Quality-vs-load Pareto** — degradation ladder = graceful slope; baselines = cliff/OOM.
5. **Admission test: predicted vs measured MSCS** (theory meets practice, G5).
6. **Essential-vs-complementary**: KV-manager benefit on Moshi (no model-level bounding)
   vs Qwen-Omni (self-windowing).

### 6.7 Hardware

Commodity A100 (2 TB/s) and H100 (3.35 TB/s), single-GPU and small multi-GPU, for
reproducibility. GH200 noted analytically (fast C2C changes swap economics) in motivation.

---

## 7. Implementation plan

1. **Substrate:** extend SGLang persistent sequences into the periodic-session object;
   instrument per-tick timing and per-session KV footprint.
2. **Scheduler:** frame loop + EDF micro-batching + admission gate; pluggable.
3. **KV manager:** tiered HBM/host(/NVMe) with pluggable eviction policies; integrate
   sinks+window and H2O-importance first.
4. **Degradation ladder + silence detection.**
5. **Benchmark harness:** trace replay + synthetic generator + metrics + cost model.
6. **Model adapters:** Moshi, MiniCPM-o 4.5, Qwen2.5-/Qwen3-Omni.

---

## 8. Milestones

- **M1 (weeks 1–3):** firm up §4 formal model + admission test; reproduce single-stream
  Moshi and MiniCPM-o serving; instrument timing/KV. Produce the latency-vs-age plot for B1
  (establish the problem empirically).
- **M2 (weeks 4–7):** persistent-session object + EDF tick scheduler + naive admission;
  beat B1 on MSCS at 1 s (MiniCPM-o).
- **M3 (weeks 8–11):** tiered KV manager + eviction sweep; quality-under-load; the
  essential-vs-complementary result across Moshi/Qwen-Omni.
- **M4 (weeks 12–14):** 80 ms regime (Moshi) hardening; degradation ladder; admission
  predicted-vs-measured validation.
- **M5 (weeks 15–18):** benchmark packaging, synthetic generator, cost model, large-regime
  projection (analytical) section; full eval sweep; writing.

---

## 9. Risks and mitigations

- **"It's just bounded-context serving."** Mitigation: lead with the periodic-deadline +
  saturating-ramp-WCET + multi-tenant jitter story; the fill-phase ramp dominates real
  (short) sessions; show baselines miss frames where we don't.
- **Crowded, fast-moving area (StreamWise, Stream2LLM, TokenFlow, SLAI all 2026).**
  Mitigation: explicit differentiation table (§5 / `RELATED_WORK.md`); move fast; build on
  SGLang rather than a from-scratch engine.
- **Eviction harms quality → reviewers reject.** Mitigation: quality-vs-load curve is a
  first-class result, not a footnote.
- **Small-model KV fits HBM, so memory pressure looks artificial.** Mitigation: use packing
  density (sessions/GPU) and tail jitter as the pressure metric; reserve the
  memory-capacity story for the projected large regime, clearly labeled.
- **No open large-context interaction model.** Mitigation: large regime is *projected
  motivation* via analytical model + TML's published serving hints, explicitly scoped.

---

## 10. Open items to verify before building

- **Moshi** context ceiling (4096 frames ≈ 5.46 min) and per-frame codebook structure —
  paper-confirmed; re-verify KV-per-frame (~1 MiB) against the released checkpoint config.
- **MiniCPM-o 4.5** real-time **video fps** (drives accumulation; assume + sweep) and
  whether/where it caps context (undocumented).
- **Qwen3-Omni** true duplex degree (streaming vs barge-in) and sliding-window size — label
  honestly as the "streaming, not barge-in" point if unconfirmed.
- **TML** attention type — undisclosed; keep as motivation only.

---

## 11. Design-decision log (what is already settled)

Chronological record of the analysis completed during scoping, so the reasoning isn't lost:

1. **Reframed serving as soft-real-time, not throughput.** Interaction sessions are
   periodic tasks with recurring deadlines; the right metrics are MSCS + tail jitter, not
   tokens/sec + TTFT.
2. **Swap is bandwidth-dominated and breaks the frame; KV must stay resident** (§1.3).
   ~130× HBM-vs-PCIe gap, paid twice/tick, growing with age.
3. **No free locality at small (dense-attention) scale** — attention reads the whole KV
   every tick; no cold subset; no cross-session prefix sharing. Cold sets only exist once
   sparse/windowed attention is used (large scale).
4. **KV is bounded by the context window → a saturating ramp, not unbounded.** Corrected an
   earlier overstatement. The window length is the per-session KV budget = the cost knob.
5. **Regime split** (§1.4): small (saturates in minutes, HBM-packing) = evaluated; large
   (~1M, never saturates, memory-capacity-bound, single session > 1 GPU) = projected
   motivation. No open model in the large regime.
6. **Growing-but-bounded WCET** is the novel real-time-theory twist (§1.5); most real
   sessions live entirely on the rising ramp.
7. **Contributions narrowed** from five candidates to three: dropped fast/slow co-serving
   and elevated-empty-tick as separate contributions (kept the latter as an ablation);
   **folded periodic-scheduling and KV-admission into one** (KV budget = schedulability
   knob).
8. **Eval set fixed with confirmed numbers** (§6.1): Moshi (80 ms, fat MHA KV, no
   self-bounding), MiniCPM-o 4.5 (1 s, thin GQA KV, video-driven), Qwen2.5-/Qwen3-Omni
   (streaming, self-windowing, MoE). Corrected Qwen2-Audio → Qwen-Omni and MiniCPM-V →
   MiniCPM-o.
9. **TML attention type confirmed undisclosed** — only serving hints public (Split-KV
   4096-token blocks, NVLS, persistent-sequence in SGLang, gather+gemv MoE kernels,
   batch-invariant kernels). Closed model → motivation only.
10. **System named Metronome; build on SGLang persistent-sequence substrate.**
