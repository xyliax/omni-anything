# Metronome: Frame-Budget Scheduling and KV-Budget Admission Control for Real-Time Serving of Interaction Models

*Technical report / paper draft. Status: results complete on the small (open-model)
regime; large regime projected. Numbers from `RESULTS.md`, hardware 1× RTX PRO 6000
Blackwell.*

## Abstract

Interaction models — full-duplex, streaming speech/omni models such as Kyutai
Moshi, MiniCPM-o 4.5, and Qwen3-Omni — do not behave like chatbots at the serving
layer. Each session is a *persistent periodic task*: every tick (80 ms – 1 s) the
server ingests a chunk as a small prefill and decodes a short response, appending to
a KV cache that persists for the whole session and grows toward a context ceiling.
The hard constraint is a recurring per-tick wall-clock deadline, not aggregate
throughput, and there is no idle slack within a session to swap KV out. We show that
serving interaction models is a per-tick-deadline scheduling problem in which the
per-session KV cache is simultaneously the dominant cost and the schedulability knob,
and that the per-tick worst-case execution time is a *saturating ramp* in context
length — a bounded-but-non-stationary WCET that classical fixed-WCET real-time theory
does not cover. We build **Metronome**, a serving layer with (i) a persistent
periodic-session abstraction, (ii) a frame-based EDF tick scheduler, (iii) a
KV-budget admission controller whose schedulability test predicts capacity from a
measured cost model, and (iv) a tiered, model-aware KV manager whose eviction policy
is a quality-coupled cost knob. On three open interaction models we measure the
per-tick cost on a real GPU, fit a cost model that predicts batched tick latency within
0.5% (median) on held-out live batches, and show Metronome sustains **2.2–4.2× more concurrent real-time sessions** at a
0.1% deadline-miss SLO than throughput-greedy batching, at **2.2–4.2× lower
\$/session-hour**, with admission turning an overload cliff (100% miss) into
graceful rejection (0% miss). We release a serving-capacity benchmark (MSCS, p999
jitter, \$/session-hour) the subfield lacks.

## 1. Introduction

(See `docs/RESEARCH_PLAN.md` §1 for the full framing.) Today's serving stacks
(vLLM, SGLang) assume ephemeral, request-scoped traffic with a throughput goal and
KV that can be swapped out during idle slack. Interaction sessions invert every one
of those assumptions. The contributions:

1. **A periodic-deadline serving model with KV-budget admission control.** We
   formalize an interaction session as a periodic task with a saturating-ramp WCET
   `C(L) = C_fixed + α·L` and derive a schedulability/admission test over a
   multi-tenant, phase-misaligned, mixed-age population. The per-session KV budget
   `B_i` appears in *both* the timing constraint (it sets the per-tick WCET) and the
   memory constraint (it sets the resident footprint) — unifying scheduling and KV
   management into one knob.

2. **A tiered, model-aware KV manager whose eviction policy is a quality-coupled
   cost knob.** We establish empirically that serving-level KV management is
   *essential* for models with no built-in context bounding (Moshi, full MHA) and
   *complementary* for models that window themselves (Qwen-Omni) — visible only
   because the eval set spans both.

3. **A real-time capacity/jitter benchmark** for streaming interaction serving:
   max sustainable concurrent sessions (MSCS) at a deadline-miss SLO, p50/p99/p999
   per-tick jitter, and \$/session-hour — replacing tokens/sec and TTFT.

## 2. The saturating-ramp WCET

For a session with token rate `r` and KV budget `B`, the resident context length is
`L(t) = min(r·a(t), B)` where `a(t)` is age. Per-tick execution time is dominated by
(a) reading the model weights once (shared across a batch), (b) prefill+FFN compute
over the few new tokens, and (c) the attention read of the entire resident KV, which
is memory-bound and grows linearly in `L`:

    C(L) = C_fixed + α·L,    α ≈ kv_bytes_per_token / HBM_bandwidth.

A multi-tenant micro-batch of sessions `{L_i}` reads every session's KV once and
runs the new-token compute per session:

    C_batch({L_i}) = base + per_session·B + α·Σ_i L_i.

This is bounded (KV saturates at `B`) but non-stationary (rises with age until the
plateau). Critically, typical voice interactions (1–3 min) are far shorter than the
fill time (Moshi ~5.5 min; MiniCPM-o longer), so most sessions live entirely on the
rising ramp — admission must reason about the **age-mix**, not just the count.

**Measurement.** We implement the tick as real `torch` kernels sized exactly to each
model's attention config, captured into a CUDA graph over static KV buffers (to
remove launch overhead, as a production server would), and time it on the GPU across
context lengths. To be robust to a co-tenant's intermittent GPU load on a *shared*
GPU, we fit the *structural* model on the **median** (p50) and carry a separate
*uncontended* tail factor (the first, contention-inflated fit over-predicted
held-out load by up to 94%). The fitted models predict the measured batched median
within 0.3/4.3/8.6% (Moshi/MiniCPM-o/Qwen) and held-out *live* batches within 0.5%
median (Moshi, G5). The implied effective bandwidth (≈0.5–1.5 TB/s, near the card's
peak — confirming attention is HBM-bandwidth-bound) is the small-regime constant we
extrapolate for the large-regime projection.

## 3. System

**Persistent periodic-session object** (`metronome/session.py`): pinned, append-only
KV; carries period, relative deadline, phase, age, KV budget, degradation state.

**Frame-based EDF scheduler** (`metronome/scheduler.py`): each frame forms a
micro-batch of due ticks ordered by absolute deadline; exploits silence (no-speak
ticks) to reclaim compute; applies the degradation ladder when over budget.

**KV-budget admission controller** (`metronome/admission.py`): on arrival, runs the
schedulability test over the current population + the new session under the proposed
budget; admits only if all sessions keep their deadlines and KV fits HBM. Two tests:
worst-case (plateau; safe) and age-aware (operating-age; tighter).

**Tiered KV manager** (`metronome/kv_manager.py`): hot HBM working set (sinks +
recent window + heavy hitters), pluggable eviction (sliding / sink+window /
H2O-importance), with a retained-attention-mass quality proxy.

## 4. Evaluation

Eval set spans the deadline spectrum 80 ms → 1 s, fat-MHA vs thin-GQA KV, no-self-
bounding vs self-windowing, and dense vs MoE. Key results (full tables in
`RESULTS.md`):

- **GATE A (problem is real):** per-tick latency climbs with age on all models;
  throughput-greedy batching misses frames at far lower concurrency than Metronome.
- **Capacity:** Metronome sustains 4.0× (Moshi), 4.2× (MiniCPM-o), 2.2× (Qwen) more
  sessions than throughput-greedy B1 at a 0.1% miss SLO; \$/session-hour 2.1–4.2×
  lower. A nuance: stateless reprefill (B0) beats persistent full-KV (B1) for
  long-context thin-KV MiniCPM-o, because B1 is memory-bound — Metronome beats both
  by windowing the resident KV.
- **Admission (G5):** the worst-case test predicts the measured MSCS exactly for
  Moshi (160) and MiniCPM-o (71), 9% for Qwen — schedulability theory meets practice.
- **Admission (G1/G4):** at 2× overload, throughput-greedy miss-rate is 100% (whole batch late) while
  Metronome holds 0% (rejects excess). Timing-bound models (Moshi, Qwen) need the
  schedulability test; memory-bound MiniCPM-o is already protected by memory
  admission.
- **KV essential vs complementary (Contribution 2):** KV budgeting buys 8.0×/8.4×
  capacity for no-self-bounding Moshi/MiniCPM-o vs 2.9× for self-windowing Qwen;
  quality degrades gracefully and policy-ordered.
- **EDF fairness:** EDF halves the tight-deadline class's miss-rate vs FIFO under
  overload by shedding slack-deadline work — EDF differentiates per-session
  deadlines (aggregate MSCS is unchanged because a micro-batch completes as a unit).
- **Large regime (projected):** a 1M-context 276B-MoE model needs 305 GiB KV/session
  (> 1 GPU); dense attention costs 579 ms ≫ 200 ms budget — sparse + tiered KV is
  mandatory, consistent with TML's published serving hints.

### 4.1 Production / open-system evaluation (`RESULTS_PROD.md`)

The closed-population results above answer "what is the capacity?"; a production
server is an *open system* (sessions arrive and depart continuously). We add an
event-driven open-system evaluation (Poisson arrivals, heavy-tailed holding,
Markov turn-taking) and the production metrics it demands. All seven hypotheses of
`docs/PRODUCTION.md` are confirmed:

- **Under churn (H1)**, admission holds the SLO at a bounded *blocking probability*
  (the Erlang-style open-system capacity) while throughput-greedy collapses to
  29–100% miss past capacity.
- **Age-aware admission (H2)** sustainably serves 1.16–1.22× more than worst-case,
  because churn keeps the age-mix young (§1.5) — the tightening finally pays off.
- **Co-aging (H3)**, the §1.5 failure mode, breaks naive age-aware admission (31%/13%
  peak miss when a cohort co-ages) but the **degradation ladder absorbs it back to
  0%**; worst-case admission never breaches.
- **Glitch severity (H5)**: at the same overload, throughput-greedy produces
  250+-tick consecutive-miss runs (≈20 s of dead audio) with Jain fairness as low as
  0.03; Metronome has zero-length runs and fairness 1.0.
- **Heterogeneous SLAs (H6)** co-served on one GPU: Metronome holds the premium tier
  at 0% miss (shedding the standard tier first); greedy violates both.
- **Silence-aware admission (H4)** and **load-adaptive KV budgeting (H7)** trade the
  quality/capacity knob with load — adaptive budgeting keeps full quality when load
  is light and recovers 4× capacity when heavy, always at 0% miss.

**Measurement methodology (a result in itself).** A held-out live validation revealed
the first cost-model fit was inflated by a co-tenant's intermittent GPU load
(over-predicting uncontended load by up to 94%). The fix: fit the *structural* model
on the **median** (robust to cross-tenant spikes) and carry a separate *uncontended*
tail factor — a dedicated server contends only with its own batched sessions.

### 4.2 Scheduling, scalability & systems (`RESULTS_SCHED.md`)

Deeper scheduling and systems results:

- **Live multi-tenant validation:** the per-tick batch is run on the real GPU across
  the operating points a multi-tenant cohort visits, confirming the simulator's
  system-level latency/miss prediction (not just the cost model).
- **Temporal sub-batching** (phase-slotting): a negative result — spreading a
  homogeneous tier forfeits weight-read amortization (`K·base+per·N+α·ΣL≤period`), so
  capacity is maximised by the monolithic batch (K=1). Its only value is per-session
  deadline differentiation, viable only at loose budgets.
- **Co-aging-safe admission:** age-aware's gain is a *churn dividend* (with no
  departures the only safe test is worst-case). An adaptive look-ahead horizon keyed
  to the observed departure rate serves +45% over worst-case under churn yet never
  breaches under a co-aging burst (where naive age-aware hits 2.5% miss).
- **Heterogeneous periods:** phase-spreading the slow tier over the hyperperiod
  expands the (N_fast,N_slow) co-serving region 3.5× — the mirror of the homogeneous
  result (spreading helps *across* periods, hurts *within* a period).
- **Incremental admission:** O(1) per arrival via running sums, 1240× faster than
  the O(N) re-scan at N=4000 with identical decisions.
- **Multi-GPU:** near-linear scaling; pinned KV makes mid-session migration
  prohibitive at scale (24 GiB KV = 403 ms ≫ frame over PCIe), so rebalancing is by
  admission-time placement, not migration.
- **Energy (DVFS):** ramp slack (§1.5) lets deadline-aware clock scaling save ~30–63%
  energy at zero deadline cost.
- **Paged KV:** validates the Σ B_i≤HBM admission model — paging cuts churn-induced
  external fragmentation (blocking 13.2%→7.9%, ~7.5% memory recovered) vs contiguous.

## 5. Limitations and honest scoping

- **Calibrated simulation.** Multi-tenant sweeps run in a discrete-event simulator
  whose per-tick cost is the *measured* GPU cost model; it is validated against the
  live GPU on held-out batch configs. It does not model engine-internal effects
  (fragmentation, scheduler overhead) beyond what the cost model captures.
- **Shared-GPU measurement.** Fits use the median (robust to a co-tenant's load) +
  an uncontended tail factor; we re-measure whenever a clean GPU window is available.
- **Quality proxy.** The eviction quality curve uses an attention-mass proxy
  calibrated to published policy behaviour, not task WER; it shows *relative*,
  policy-ordered, graceful degradation, not absolute dialogue quality.
- **Large regime is projection, not measurement** — no open model occupies it.
- **Not modelled** (future work): paged-KV fragmentation, multi-GPU sharding /
  session migration, mid-session fault tolerance, and the audio-encoder / network
  latency outside the serving-compute path. The cost model captures GPU compute +
  KV-read time, which dominates the per-tick budget.
- **Hardware.** Measured on one RTX PRO 6000 Blackwell; constants (α, base) are
  re-measured per machine, so results are portable but absolute MSCS is hardware
  specific.

## 6. Related work

See `docs/RELATED_WORK.md`. Every existing system occupies ≤2 of {persistent
periodic deadline, growing-then-bounded KV as first-class, multi-tenant batched,
capacity-as-metric}; Metronome targets all four. Closest: StreamWise (finite
multimodal, per-request DAG deadlines), Sarathi/SLAI (per-request token latency),
StreamingLLM/H2O (offline KV reduction), classical RMS/EDF (fixed WCET).

## 7. Reproducibility

All figures trace to `experiments/*.py` and `results/`. `experiments/run_all.py`
regenerates the CPU sweeps; `--gpu` adds the live fit/validation. The benchmark is
documented in `bench/README.md`.
