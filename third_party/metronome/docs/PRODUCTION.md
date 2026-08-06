# Metronome in production — workload cases, metrics, and design

The first eval (`RESULTS.md`) established the mechanism on a *closed* population
(fixed N, draw ages once, run frames). That answers "what is the capacity?" but a
production interaction server lives in an *open* world: users connect and hang up
continuously, talk in bursts, arrive in flash crowds, and span multiple SLAs on one
GPU. This document enumerates the production cases, defines the metrics that decide
whether the system is actually good, and states the design responses — then maps each
to a concrete experiment under `experiments/`.

---

## 1. What production actually looks like

| Dimension | Closed eval (RESULTS.md) | Production reality | Why it matters |
|---|---|---|---|
| Population | fixed N, present at t=0 | **open system**: Poisson(t) arrivals + departures | capacity is a *blocking probability*, not a fixed number |
| Arrivals | none (static) | diurnal + **bursts / flash crowds** | admission must shed spikes without collapsing |
| Session length | drawn once | **heavy-tailed** (most short, few hours-long) | the age-mix is dynamic; long sessions dominate KV |
| Talk pattern | iid Bernoulli per tick | **turn-taking** (Markov talk/silence runs) + barge-in | silence gain depends on structure; synchronized talk is the adversary |
| Age-mix | fixed | **churn keeps it young**; **bursts co-age it** | age-aware admission only pays off with churn; co-aging is its failure mode |
| Tenancy | one model | **heterogeneous**: mixed deadlines/models/SLAs on one GPU | EDF + per-tier admission must protect the tight tier |
| Overload | measured once | **transient**: spike → must shed → must *recover* | graceful degradation AND recovery, not just a number |

The two production failure modes the closed eval cannot see:
1. **Co-aging transient (§1.5).** A burst of sessions admitted together ages in
   lockstep; their KV — and the batch WCET — ramps simultaneously toward the plateau.
   A test that admitted them assuming they'd stay young (age-aware) now breaches.
2. **Sustained open-loop overload.** Greedy admission with no blocking accepts every
   arrival; once the batch exceeds the frame, *every* session drops frames forever
   (a system-wide cliff), not a clean subset.

---

## 2. The metrics that decide goodness

Capacity (MSCS) and tail jitter are necessary but not sufficient. Production adds:

### 2.1 Glitch severity, not just miss rate
A single dropped 80 ms frame may be inaudible; **5 in a row is an audible dropout.**
We report the **distribution of consecutive-miss run lengths** and its p99/max — two
servers with the same aggregate miss rate can have very different perceived quality.

### 2.2 Fairness across sessions
Aggregate miss rate hides starvation. We report the **per-session miss-rate
distribution** and **Jain's fairness index** — is the pain spread evenly, or are a
few sessions starved while others are perfect?

### 2.3 Goodput, not throughput
**Goodput** = on-time *and* non-degraded ticks per second. A server that meets
deadlines by degrading everyone to a tiny window has high tick-rate but low goodput.

### 2.4 Quality-adjusted capacity
**QA-MSCS** = max sustainable sessions meeting *both* a deadline-miss SLO *and* a
quality floor (retained attention mass ≥ q). KV budgeting trades these off; the right
capacity number respects both.

### 2.5 Blocking probability (the open-system capacity)
With admission, capacity is an **Erlang-style blocking probability**: at a given
offered load (arrival rate × mean holding time), what fraction of arrivals are
rejected? This is the honest "capacity" of an admission-controlled server.

### 2.6 Responsiveness & recovery
- **Barge-in / first-response latency:** when a silent session starts talking, time
  to its first on-time tick.
- **Recovery time:** after an overload spike, wall-clock time for miss rate to fall
  back under the SLO.
- **Time-in-degradation:** fraction of session-time spent on each degradation rung
  (the running quality cost).

### 2.7 Efficiency
**GPU-seconds per 1000 on-time session-minutes** and effective utilisation —
\$/session-hour from RESULTS.md, refined to count only goodput.

---

## 3. Design responses (and where they are tested)

| Production case | Metronome design response | Experiment |
|---|---|---|
| Open-system churn | admission re-evaluated per arrival against the *live* age-mix; departures free budget for new admits | `open_system.py` |
| Flash crowd / spike | admission blocks excess (bounded blocking) instead of accepting into a cliff; recovers as load drains | `open_system.py` (spike) |
| Heavy-tailed lifetimes | age-aware test provisions for the *operating* age-mix that churn sustains, not the plateau | `open_system.py` (age-aware vs worst-case) |
| Co-aging transient | worst-case admission reserves plateau headroom (safe); age-aware relies on the **degradation ladder** to absorb the synchronized ramp and recover | `co_aging.py` |
| Turn-taking conversation | silence exploitation reclaims no-speak ticks; gain scales with realistic silence runs, not iid flips | `conversation.py` |
| Synchronized talk (adversary) | degradation ladder + admission headroom bound the worst-case burst | `conversation.py` (adversarial) |
| Heterogeneous SLAs on one GPU | EDF by absolute deadline + per-session budgets; tight tier protected, loose tier sheds first | `heterogeneous.py` |
| Load-varying quality | adaptive per-session KV budget: tighten under load (more sessions, lower quality), loosen when load drains | `adaptive_budget.py` |

---

## 4. Hypotheses to confirm or refute

- **H1.** Under open-system churn, Metronome admission holds the deadline-miss SLO at
  a bounded blocking probability while throughput-greedy collapses to ~100% miss past
  capacity. *(open_system)*
- **H2.** With churn, the **age-aware** test sustainably serves more sessions than the
  worst-case test at the same SLO (the §4.2 tightening finally pays off). *(open_system)*
- **H3.** A synchronized burst breaks a naive age-aware admission (co-aging), but the
  degradation ladder bounds the transient miss and the system recovers within a
  bounded time; worst-case admission never breaches. *(co_aging)*
- **H4.** Silence exploitation's goodput gain grows with realistic turn-taking silence
  runs and is robust to a bounded adversarial synchronized-talk burst. *(conversation)*
- **H5.** Consecutive-miss runs are short and bounded under Metronome but long under
  greedy at the same aggregate miss rate (perceived-quality win). *(metrics)*
- **H6.** On a heterogeneous GPU, Metronome meets every tier's SLA where greedy
  violates the tight tier. *(heterogeneous)*
- **H7.** Adaptive KV budgeting traverses the quality/capacity Pareto under load,
  holding the SLO at graceful quality cost. *(adaptive_budget)*

Each hypothesis is reported with the §2 metrics, pass/refute, in `RESULTS_PROD.md`.
