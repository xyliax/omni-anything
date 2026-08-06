# Metronome — Research Pipeline

The executable, end-to-end pipeline. Each stage lists **inputs → work → artifacts → exit
gate**. Gates are go/no-go: do not proceed past a red gate without either fixing it or
revising the framing. The pipeline is designed so the *problem is proven empirically
before the system is built* (Stage 2), so a null result is cheap and early.

```
 S0 Setup ─► S1 Instrument ─► S2 Establish problem ─► S3 Formal model
                                      │                      │
                                      ▼                      ▼
                              (GATE A: real?)        (GATE B: predictive?)
                                      │                      │
                                      └──────► S4 Build system ◄──────┘
                                                     │
                                                     ▼
                          S5 Core eval ─► S6 KV manager ─► S7 Tight-deadline (80ms)
                                                     │
                                                     ▼
                              S8 Ablations ─► S9 Benchmark ─► S10 Large-regime projection
                                                     │
                                                     ▼
                                              S11 Writing
```

---

## S0 — Environment & model setup
- **Inputs:** GPUs (A100 + H100), the four model checkpoints.
- **Work:** stand up SGLang; run single-stream inference for Moshi, MiniCPM-o 4.5,
  Qwen2.5-/Qwen3-Omni; confirm each model's tick loop and I/O token rates against the
  numbers in `RESEARCH_PLAN.md` §6.1; resolve the §10 open items (Moshi KV/frame from the
  released config; MiniCPM-o video fps; Qwen3-Omni duplex degree).
- **Artifacts:** `models/` adapters; a one-page "confirmed model facts" sheet with measured
  (not assumed) token rates and KV/token.
- **Exit gate:** all four models run single-stream; measured KV/token within ~10% of
  predicted for at least Moshi and MiniCPM-o.

## S1 — Instrumentation & trace collection
- **Inputs:** running models from S0.
- **Work:** add per-tick timing (queue, prefill, decode, attention-read), per-session KV
  footprint, and per-tick token counts to the SGLang path. Collect/assemble real
  full-duplex dialogue traces (audio; audio+video for MiniCPM-o) with realistic talk/silence
  structure; build the synthetic session generator (arrival rate, length distribution,
  talk/silence ratio, video fps).
- **Artifacts:** `bench/traces/` (real + synthetic); `bench/instrument/` timing hooks;
  a trace-replay driver that issues chunks on a wall clock.
- **Exit gate:** can replay a trace at true wall-clock cadence and log per-tick latency +
  KV size for a single session.

## S2 — Establish the problem empirically (before building anything)
- **Inputs:** S1 instrumentation + B1 baseline (SGLang persistent session, throughput-greedy).
- **Work:** drive B1 with increasing concurrent sessions and with long single sessions.
  Produce the **latency-vs-session-age** curve and the **MSCS** curve for B1.
- **Artifacts:** `results/problem/` — the two plots, raw logs.
- **GATE A (the existential gate):** Does B1's per-tick latency *actually* climb with KV/age
  and cross the deadline, and does throughput-greedy batching *actually* miss frames under
  multi-tenant load (especially at 80 ms)? **If no → the problem isn't real at the
  evaluated scale; pivot** (e.g., move primary emphasis to the projected large regime, or
  reframe around jitter only). **If yes → proceed; this plot becomes Figure 1.**

## S3 — Formal model & admission test
- **Inputs:** S1 timing data (to fit `C_fixed`, `α`), GATE A confirmation.
- **Work:** finalize the saturating-ramp WCET model and the two admission tests (worst-case
  plateau vs age-aware) from `RESEARCH_PLAN.md` §4. Fit constants from measured per-tick
  latency vs KV length.
- **Artifacts:** `model/` — fitted cost model, admission-test implementation, a notebook
  that predicts MSCS from model + hardware specs.
- **GATE B:** Does the fitted cost model predict measured per-tick latency within a target
  error (e.g. ±15% at p99)? **If no → the timing isn't modelable (hidden nonlinearity);
  investigate before relying on admission control.**

## S4 — Build Metronome
- **Inputs:** GATE A + GATE B passed.
- **Work:** persistent periodic-session object; frame-based EDF tick scheduler; admission
  gate using the S3 test; tiered KV manager skeleton (HBM hot set first, host tier next);
  pluggable eviction interface; degradation ladder; silence detection.
- **Artifacts:** `metronome/` system; config for per-session budget/period/deadline.
- **Exit gate:** Metronome serves a multi-session workload end-to-end with admission
  enforced and no correctness regression vs B1 on output tokens.

## S5 — Core evaluation (1 s regime, MiniCPM-o)
- **Inputs:** Metronome + baselines B0/B1/B2.
- **Work:** MSCS, jitter, and \$/session-hour for B0/B1/B2/M on MiniCPM-o at 1 s, across
  load levels and session-age mixes.
- **Artifacts:** `results/core/` — MSCS-vs-miss-rate, latency-vs-age (M flat vs B1 climbing),
  cost table.
- **Exit gate:** M beats B1 on MSCS at the target miss rate with the latency-vs-age plot
  showing the flat-vs-climbing contrast (Goals G1, G2).

## S6 — KV manager & eviction (the "essential vs complementary" result)
- **Inputs:** S4 KV manager; Moshi (no self-bounding) + Qwen-Omni (self-windowing).
- **Work:** eviction-policy sweep (sliding window / sinks+window / H2O-importance /
  summarize-offload); quality-under-load via the task-quality proxy; compare the KV
  manager's benefit on Moshi vs Qwen-Omni.
- **Artifacts:** `results/kv/` — quality-vs-load Pareto; per-model KV-manager gain.
- **Exit gate:** demonstrate (a) graceful, not cliff, quality degradation, and (b) the
  manager is *essential* on Moshi and *complementary* on Qwen-Omni (Contribution 2).

## S7 — Tight-deadline hardening (80 ms regime, Moshi)
- **Inputs:** Metronome + Moshi.
- **Work:** drive the 80 ms loop; measure p999 jitter; kill per-tick launch overhead
  (CUDA graphs / persistent kernels); tune micro-batching of phase-misaligned 12.5 Hz
  sessions; show batch-invariance keeps multi-tenant ticks deterministic.
- **Artifacts:** `results/tight/` — jitter distributions; MSCS at 80 ms vs 1 s.
- **Exit gate:** sustain a meaningful concurrency at 80 ms within p999 budget where B1
  cannot — the headline "scheduler matters most when the deadline is tight" result.

## S8 — Ablations
- **Inputs:** full system.
- **Work:** ablate admission control; full-KV vs budgeted; fixed vs adaptive budget; EDF vs
  FIFO; with/without degradation ladder; with/without silence exploitation.
- **Artifacts:** `results/ablation/` — one isolated-contribution plot per knob.
- **Exit gate:** each component shows a measurable, defensible contribution.

## S9 — Benchmark packaging (Contribution 3)
- **Inputs:** harness from S1, metrics from S5–S8.
- **Work:** package the trace set + synthetic generator + metric definitions (MSCS, p999
  jitter, \$/session-hour) + cost model as a reusable, documented benchmark; reproducibility
  scripts.
- **Artifacts:** `bench/` released benchmark + README; leaderboard-style result tables for
  B0/B1/B2/M across all models.
- **Exit gate:** a third party can reproduce a headline number from scratch.

## S10 — Large-regime projection (motivation, analytical)
- **Inputs:** fitted cost model (S3), published TML hints, large-model KV math.
- **Work:** project MSCS, single-session-exceeds-GPU thresholds, and tiered-KV necessity for
  a 200B+/~1M-context interaction model; clearly labeled as projection, not measurement.
- **Artifacts:** `results/projection/` — the large-regime figures and assumptions table.
- **Exit gate:** projection is internally consistent with the small-regime measured constants
  and honestly scoped.

## S11 — Writing & submission
- **Inputs:** all results.
- **Work:** draft against the §3 contributions and §6.6 headline plots; build the
  differentiation table from `RELATED_WORK.md`; limitations section (eviction quality cost,
  loose bounds, adversarial silence); artifact appendix.
- **Artifacts:** paper draft, artifact, submission to target venue (MLSys/OSDI/EuroSys/NSDI).
- **Exit gate:** internal review passes the "is it just bounded-context serving?" rebuttal.

---

## Critical path & parallelism

- **Critical path:** S0 → S1 → S2 (GATE A) → S4 → S5 → S7 → S9 → S11.
- **Can parallelize:** S3 (formal model) alongside S4 once S1 data exists; S6 eviction sweep
  alongside S5; S10 projection alongside S8.
- **Cheapest kill point:** GATE A. If B1 doesn't visibly degrade with age/load at evaluated
  scale, we learn that in week ~3, before building the system.

## Continuous discipline

- **No silent caps:** any time the harness bounds coverage (top-N sessions, sampled traces,
  no-retry), log what was dropped.
- **Verify before assume:** every number that enters a figure traces to a measurement or a
  primary source; assumptions (e.g. video fps) are swept, not fixed.
- **Tail over mean:** report p999, not just mean, everywhere a deadline is involved.
