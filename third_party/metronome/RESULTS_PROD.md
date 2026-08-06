# Metronome — Production results

Open-system, production-realism evaluation (`docs/PRODUCTION.md`). Where `RESULTS.md`
measured capacity on a *closed* population, this measures the behaviours a production
server must get right: churn, flash crowds, co-aging, turn-taking, heterogeneous
SLAs, and adaptive quality — with the production metrics (consecutive-miss runs,
fairness, goodput, blocking, recovery). Driven by the event-driven open-system
simulator (`sim/open_system.py`) on the measured median cost model.

> **Measurement note (shared GPU).** The first cost-model fit was contaminated by a
> co-tenant's intermittent GPU load: it inflated p99 timings, so the model
> over-predicted *uncontended* held-out load by up to **94%**. The fix is itself a
> result — fit the *structural* model on the **median** (robust to cross-tenant
> spikes) and carry a separate **uncontended tail factor**. A dedicated production
> server contends only with its own batched sessions, so cross-tenant inflation must
> not enter the model. (See `metronome/cost_model.py`; constants are re-measured
> whenever a clean GPU window is available.)

All seven production hypotheses (`docs/PRODUCTION.md`) are **confirmed**.

| # | Hypothesis | Result |
|---|---|---|
| H1 | admission holds SLO under churn; greedy collapses | greedy → 29–100% miss past capacity; Metronome **0% at bounded blocking** ✓ |
| H2 | age-aware serves more than worst-case under churn | **1.16–1.22× more served** at 0% miss ✓ |
| H3 | co-aging breaks naive age-aware; degradation absorbs it | worst-case 0%; age-aware peak **31%/13%** → **0% with degradation ladder** ✓ |
| H4 | silence-aware admission gains with turn-taking | **1.11–1.21× more served** at 0% miss ✓ |
| H5 | consecutive-miss runs short under Metronome, long under greedy | greedy runs **p99 266–272 ticks**, fairness 0.03–0.64; Metronome **0**, fairness 1.0 ✓ |
| H6 | meets heterogeneous SLAs; greedy violates the tight tier | Metronome premium **0% miss** at all loads; greedy **100%** both tiers ✓ |
| H7 | adaptive budgeting traverses quality/capacity Pareto | full quality at low load **and** 4× capacity at high load, 0% miss ✓ |

---

## H1 — Open-system: admission vs throughput-greedy under churn

`results/open/<model>_offered_load.png`. Poisson arrivals, heavy-tailed (lognormal)
holding times, departures free budget. As offered load rises past capacity:

- **Moshi (80 ms):** greedy miss climbs to ~39% (offered ≈ 290); Metronome holds
  **0%** by blocking 35–53% of arrivals.
- **Qwen3-Omni (200 ms):** greedy melts down 29% → 76% → 96% → **99.6%**; Metronome
  holds **0%** (blocking 19–60%).
- **MiniCPM-o (1 s):** memory-bound — memory admission alone caps it, so even greedy
  does not form an over-budget batch (no timing cliff). Metronome blocks to fit HBM.

Throughput-greedy has no deadline awareness: once the batch exceeds the frame, every
session is late. Admission converts that into a *bounded blocking probability* — the
honest open-system capacity (an Erlang-style trade).

## H2 — Age-aware admission pays off under churn

Churn keeps the age-mix young (sessions depart before reaching the plateau, §1.5), so
the age-aware test (provisioning for the operating age, not the plateau) sustainably
serves more at the same 0% miss:

| Model | worst-case served | age-aware served | gain |
|---|---|---|---|
| Moshi | 90 | 104 | **1.16×** |
| Qwen3-Omni | 221 | 270 | **1.22×** |
| MiniCPM-o | 71 | 71 | 1.0× (memory-bound) |

## Flash crowd: spike & recovery

`results/open/<model>_spike.png`. A 10× arrival spike: Metronome blocks the excess
and miss stays at the SLO (fast/zero recovery); throughput-greedy spikes toward 100%
miss and recovers only as the backlog drains.

## H3 — Co-aging transient (validates RESEARCH_PLAN §1.5)

`results/coaging/<model>_coaging.png`. A synchronized cohort (all admitted at once)
ages in lockstep to the plateau — the failure mode fixed-WCET theory cannot see:

| Model | worst-case (peak miss) | age-aware, no degradation | age-aware + degradation |
|---|---|---|---|
| Moshi | admits 97, **0.000** | admits 160, **0.312** | **0.000** |
| Qwen3-Omni | admits 224, **0.000** | admits 287, **0.129** | **0.000** |
| MiniCPM-o | admits 71, 0.000 | 0.000 (memory-bound) | 0.000 |

Worst-case admission provisions for the plateau and never breaches (safe, conservative).
Aggressive age-aware admits more but breaches when the cohort co-ages — and the
**degradation ladder absorbs the transient back to 0%** (it persistently shrinks the
resident window). This is exactly the bounded-but-non-stationary-WCET story.

## H4 / H5 — Turn-taking, silence goodput, miss runs, fairness

`results/conversation/`. Turn-taking is a 2-state Markov chain (talk/silence).

**H4 — silence-aware admission** (provision for the talking fraction, defer no-speak
ticks) admits more at the same 0% miss as the talk fraction drops:

| Model | talk 0.3 | talk 0.5 | talk 0.7 | talk 1.0 |
|---|---|---|---|---|
| Moshi | 1.11× | 1.11× | 1.11× | 1.05× |
| Qwen3-Omni | 1.21× | 1.21× | 1.21× | 1.02× |

**H5 — consecutive-miss runs & fairness** at heavy overload (`miss_runs.png`):

| Model | greedy miss-run p99 / max | greedy fairness | Metronome run p99 / fairness |
|---|---|---|---|
| Moshi | 266 / 277 ticks | 0.642 | 0 / **1.000** |
| Qwen3-Omni | 272 / 299 ticks | **0.027** | 0 / **1.000** |

A greedy server at the *same* aggregate miss rate produces 250+-tick continuous
dropouts (≈20 s of dead audio at 80 ms) concentrated on a starved subset; Metronome
has zero-length runs and perfect fairness.

## H6 — Heterogeneous SLAs co-served on one GPU

`results/hetero/<model>_hetero.png`. Premium tier (relative deadline 0.4×period) +
standard tier (deadline = period) on one accelerator. Across all loads, Metronome
keeps the **premium tier at 0% miss** (shedding the standard tier first under
pressure) while throughput-greedy violates **both** tiers (100% miss) once overloaded.

## H7 — Load-adaptive KV budgeting

`results/adaptive/<model>_adaptive.png`. A controller sizes the resident window to the
estimated *offered* demand (Little's law). It achieves the best of both fixed points:

| Load | fixed-small | fixed-large | **adaptive** |
|---|---|---|---|
| light (0.3×) | q 0.76, served 38 | q 1.00, served 38 | **q 1.00, served 38** |
| heavy (2.0×) | q 0.74, served 228 | q 1.00, served **54** | **q 0.73, served 228** |

(Moshi; 0% miss throughout.) Adaptive budgeting keeps full quality when load is light
and recovers full capacity (4×) when load is heavy — traversing the quality/capacity
Pareto with demand instead of being pinned to one operating point.

---

## Reproduce

```bash
python3 experiments/fit_cost_model.py     # GPU: median cost model (waits for a clean window)
python3 experiments/run_prod.py           # CPU: the full production suite
```
