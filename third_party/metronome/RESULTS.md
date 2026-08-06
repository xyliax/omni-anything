<!-- SUPERSEDED-POINTER -->
> **Note (2026-06-23):** the real-time serving capacity / TTFA conclusions here are superseded by
> `RESULTS_REALTIME_LOAD.md` (end-to-end on real silicon + production Go-gateway⇄vLLM bridge).
> Synthetic-MSCS and `in_frac=0.0` head-to-head numbers in this file are **not** current.

# Metronome — Results

> **The headline capacity numbers are now measured on the real serving engine**
> (`metronome/engine.py`); see [`RESULTS_ENGINE.md`](RESULTS_ENGINE.md). Real measured
> MSCS gain: **3.2× Moshi, 4.0× MiniCPM-o, 2.67× Qwen**. The simulator results below
> are a *predictor validated against the engine* (exact on memory-bound capacity;
> within ~20–45% on timing-bound capacity, the gap being real-engine overhead the
> linear cost model omits) and are used for the large sweeps / open-system dynamics
> that are impractical to run live.

Frame-budget serving for real-time interaction models. This document records the
measured findings from the executable pipeline (`docs/PIPELINE.md`). Every number
below traces to a script under `experiments/` and an artifact under `results/`.

**Hardware:** 1× NVIDIA RTX PRO 6000 Blackwell (97 GB, ~1.7 TB/s peak), shared.
All GPU measurements ran through the shared-GPU window guard (`bench/gpu_probe.py`).
**Methodology:** real per-tick transformer kernels (CUDA-graph captured, sized to
each model's true attention config) are timed on the GPU to fit the cost model; a
discrete-event simulator calibrated to that *measured* cost model runs the
multi-tenant sweeps, and is validated back against the live GPU (G5).

---

## TL;DR

| Claim | Result |
|---|---|
| The problem is real (GATE A) | per-tick latency climbs with KV/age on all 3 models; throughput-greedy misses frames under load — **PASS** |
| The cost model is predictive (GATE B) | batched-model max relative residual **0.003 / 0.043 / 0.086** (Moshi/MiniCPM-o/Qwen) ≤ 0.15 — **PASS**; held-out live validation (G5) **0.5%** median for Moshi |
| Admission test predicts capacity (G5) | worst-case predicts **exactly** the measured MSCS for Moshi (160=160) and MiniCPM-o (71=71); 9% for Qwen (234 vs 256) |
| Capacity (MSCS) gain over throughput-greedy B1 | **4.0× (Moshi), 4.2× (MiniCPM-o), 2.2× (Qwen)** at a 0.1% miss SLO |
| Cost | **\$/session-hour 2.2–4.2× lower** than B1 at fixed SLO |
| KV management essential vs complementary | **8.0× / 8.4×** capacity gain for no-self-bounding Moshi/MiniCPM-o vs **2.9×** for self-windowing Qwen |
| Admission = graceful, greedy = cliff (G4) | at overload, throughput-greedy miss-rate **100%** (Qwen, whole batch late) vs Metronome **0%** |
| Large regime (projected) | a 1M-context GQA model needs **305 GiB KV/session** (> 1 GPU) and dense attention costs **579 ms ≫ 200 ms** budget → sparse + tiered KV mandatory |

---

## Confirmed model facts (S0)

Measured KV-bytes/token match the published numbers (`tests/test_core.py`):

| Model | Attn | Layers / KV-heads / d | KV / token | Tick | Ceiling | Self-windowing |
|---|---|---|---|---|---|---|
| Moshi | MHA | 32 / 32 / 128 | **512 KiB** (~1 MiB/frame) | 80 ms | 4096 tok (~5.46 min) | **No (essential)** |
| MiniCPM-o 4.5 | GQA | 36 / 8 / 128 | **144 KiB** | 1 s | 32768 tok | No (essential) |
| Qwen3-Omni | GQA-MoE | 48 / 4 / 128 | 96 KiB | 200 ms | 8192 tok (window) | **Yes (complementary)** |

## Cost model (S3, GATE B) — `results/cost_model/`

Fitted on the live GPU, CUDA-graph kernel, **uncontended** (median structural model
`C(L) = C_fixed + α·L` + an uncontended tail factor):

| Model | C_fixed | α | implied BW | tail factor | **batch max rel resid** | held-out (G5) median |
|---|---|---|---|---|---|---|
| Moshi | 8.0 ms | 0.33 ns/tok | **1463 GiB/s** | 1.001 | **0.003** | 0.5% |
| MiniCPM-o | 10.0 ms | 0.13 ns/tok | 1045 GiB/s | 1.003 | **0.043** | 15% |
| Qwen3-Omni | 6.0 ms | 0.19 ns/tok | 477 GiB/s | 1.001 | **0.086** | — |

The batched model `base + per_session·B + α·ΣL` (what the scheduler uses) fits the
measured median within ≤8.6% for all models, and held-out *live* batches (configs
not in the fit grid) within 0.5% median for Moshi (G5). The implied bandwidth is
near the card's peak — confirming the per-tick attention cost is HBM-bandwidth-bound.

> The first fit (contention-inflated) over-predicted held-out load by up to 94%; the
> median + tail-factor methodology (`metronome/cost_model.py`) is the fix. See
> `RESULTS_PROD.md` for the measurement note.

## GATE A — the problem is real (S2) — `results/problem/`

For all three models, measured per-tick latency rises monotonically with context
length (= session age), and throughput-greedy batching (B1) misses the deadline at
a far lower concurrency than Metronome (M). **GATE A: PASS** for all three.

## Core evaluation (S5) — `results/core/`

MSCS at a 0.1% deadline-miss SLO, and \$/session-hour (\$2/GPU-hr):

| Model | B0 (stateless) | B1 (greedy) | B2 (EDF) | **M (Metronome)** | M/B1 | \$/sess-hr B1 → M |
|---|---|---|---|---|---|---|
| Moshi (80 ms) | 8 | 40 | 40 | **160** | 4.0× | 0.050 → **0.0125** |
| MiniCPM-o (1 s) | 64 | 17 | 17 | **71** | 4.2× | 0.118 → **0.0282** |
| Qwen3-Omni (200 ms) | 24 | 106 | 106 | **234** | 2.2× | 0.019 → **0.0085** |

Findings:
- **The money plot** (`*_latency_vs_age.png`): at a fixed concurrency, B1 (full KV)
  per-tick latency climbs across the deadline as sessions age; M (windowed KV) stays
  flat below it — the bounded-WCET result.
- **B0 can beat B1** for long-context thin-KV models (MiniCPM-o: 32 vs 17): B1's
  persistent full 32K-token KV is *memory*-bound (4.5 GB/session ⇒ only 17 fit HBM),
  whereas stateless reprefill avoids resident KV at the cost of recompute. Metronome
  beats both by *windowing* the resident KV.
- **B2 ≈ B1** on aggregate MSCS: pure EDF reordering does not change how many ticks
  miss when all sessions share one per-frame deadline and the batch is monolithic —
  EDF changes *which* sessions miss (per-session fairness), not the count. The
  capacity win comes from admission + KV budgeting, not ordering.

## Admission control (G5 + G1/G4) — `results/admission/`

**Predicted vs measured capacity (G5):**

| Model | measured MSCS | worst-case predicted (safe) | rel err | age-aware predicted |
|---|---|---|---|---|
| Moshi | 160 | 160 | 0.00 | 160 |
| MiniCPM-o | 71 | 71 | 0.00 | 71 |
| Qwen3-Omni | 256 | 234 | 0.09 | 256 |

The worst-case (plateau) test is safe (predicts ≤ measured) and, for these workloads,
essentially *exact* — the schedulability theory matches practice. (With churn the
age-aware test admits more and is validated in `RESULTS_PROD.md` H2.)

**Graceful vs cliff (G1/G4):** under overload,

| Model | miss-rate, throughput-greedy | miss-rate, Metronome | served |
|---|---|---|---|
| Qwen3-Omni | **1.000** | **0.000** | 256 |
| Moshi | 0.000 | 0.000 | 160 |
| MiniCPM-o | 0.000 | 0.000 | 71 |

A throughput-greedy engine has no deadline awareness: once the batch exceeds the
frame *every* tick is late — a true cliff to 100% miss (Qwen3-Omni). Admission
rejects the excess at admission time and admitted sessions keep 0% miss. With the
clean (low) per-tick cost, Moshi and MiniCPM-o are now *memory*-bound — memory
admission alone caps them before an over-budget batch forms — so the timing cliff
appears only on the timing-bound Qwen. The open-system results (`RESULTS_PROD.md` H1)
show the cliff across models under sustained churn.

## KV manager: essential vs complementary (S6, Contribution 2) — `results/kv/`

Capacity gain from KV budgeting (small budget vs full KV), and the quality proxy:

| Model | self-windowing | **KV-budget gain** | class |
|---|---|---|---|
| Moshi | No | **8.0×** | **essential** |
| MiniCPM-o | No | **8.4×** | **essential** |
| Qwen3-Omni | Yes | **2.9×** | **complementary** |

Quality (`*_quality_vs_budget.png`) degrades *gracefully* and policy-ordered
(full ≥ h2o ≥ sink_window ≥ sliding) as the budget shrinks — not a cliff. KV
management is *essential* exactly for the models that do not bound their own context
(Moshi's full MHA) and merely *complementary* for those that window themselves
(Qwen) — the result only visible because the eval set spans both.

## Ablations (S8) — `results/ablation/`

Each knob vs the pure-scheduling base (MSCS @ 0.1%, degradation off unless noted):

- **KV budgeting** is the dominant knob: removing it (full KV) drops MSCS to
  0.24–0.62× across models.
- **Degradation ladder** (additive) lifts the tight-deadline Moshi case 2.5× by
  absorbing transient overload into graceful quality loss.
- **Silence exploitation** (talk-ratio 0.5) lifts MSCS up to ~2.6× when sessions
  have no-speak ticks (Moshi, Qwen).
- **EDF vs FIFO vs LRF**: no aggregate-MSCS difference (monolithic per-frame batch),
  consistent with the B2≈B1 result.

## EDF fairness — per-session deadline differentiation — `results/edf/`

A GPU micro-batch completes as a unit, so intra-frame ordering cannot give
per-session latency differentiation (the reason B2≈B1 on MSCS). EDF's value is in
*frame-level shedding*: with a mixed-deadline population under overload (50% tight
D=0.5T, 50% loose D=T), including sessions in deadline order and shedding those
whose deadline the growing batch would blow:

| Model | FIFO tight-miss | **EDF tight-miss** | EDF loose-miss |
|---|---|---|---|
| Moshi | 0.744 | **0.358** | 0.000 |
| MiniCPM-o | 0.660 | **0.256** | 0.219 |
| Qwen3-Omni | 0.697 | **0.294** | 0.187 |

EDF roughly **halves** the high-priority (tight-deadline) class's miss-rate by
reallocating misses to the slack class — the correct, honest role of EDF in a
batched real-time server.

## Large-regime projection (S10, analytical) — `results/projection/`

Extrapolating the measured 527 GiB/s effective bandwidth to a 276B-MoE / 1M-context
interaction model (TML-Interaction-Small-like, 200 ms tick):

- KV at 1M tokens: **305 GiB/session (GQA)** — a single session exceeds one 80 GB
  GPU; 38 GiB even with MLA.
- Fill time **3.8 h** — sessions never saturate; KV grows the whole session.
- Dense attention reads the whole KV every tick: **579 ms ≫ 200 ms** budget. Only
  **~345k of 1M tokens** are deadline-feasible with dense attention.
- ⇒ sparse/windowed attention + tiered (HBM/host/NVMe) KV is **mandatory** at scale
  — consistent with TML's published "Split-KV 4096-token blocks" hint.

---

## Hardware sensitivity (§6.7) — `results/hardware/`

Rescaling the measured cost model (the KV-read α and shared weight-read base are
bandwidth-bound) to A100 (2039), H100 (3352), GH200 (4915 GiB/s):

- On **bandwidth-limited** hardware (this Blackwell's effective BW), *timing* binds
  and Metronome's scheduling gain is large (Moshi 2.4×, Qwen 2.1×).
- On **high-bandwidth** datacenter GPUs, *memory capacity* binds (MSCS plateaus at
  the HBM cap): Moshi M→160, Qwen B1→106/M→177. The gain shifts from the timing
  lever to the KV-budgeting (memory) lever — **M > B1 on every accelerator**.
- **MiniCPM-o is bandwidth-insensitive** (B1=17, M=71 across all HW): it is purely
  KV-memory-capacity-bound, so only KV budgeting (not faster HBM) raises capacity.

(Projection uses peak vendor bandwidths; absolute numbers are optimistic vs the
sub-peak effective bandwidth a real kernel achieves — the *trend* is the result.)

## Reproduce

```bash
python3 experiments/fit_cost_model.py        # GPU: fit C(L) per model (GATE B)
python3 experiments/validate_sim.py          # GPU: held-out live-vs-sim (G5)
python3 experiments/run_all.py               # CPU sweeps; add --gpu for live stages
```
