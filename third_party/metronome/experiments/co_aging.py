"""Co-aging transient stress test (docs/PRODUCTION.md H3, validates RESEARCH_PLAN §1.5).

The novel real-time wrinkle: a session's WCET is a *saturating ramp* in KV length.
A flash crowd admitted together ages in lockstep — their KV, and the batched WCET,
ramp simultaneously toward the plateau. This is the failure mode classical
fixed-WCET schedulability cannot see.

We admit a synchronized cohort (all age 0, no phase jitter) and let it age to the
plateau, under three admission/degradation policies:
  * worst-case admission (provisioned for the plateau)        -> never breaches
  * age-aware admission, NO degradation                       -> breaches at co-aging
  * age-aware admission, WITH degradation ladder              -> transient absorbed

Reports the per-frame miss-rate trajectory, peak transient miss, and recovery time.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiments._common import load_cost, hbm_kv_bytes, all_models
from metronome import models
from metronome.session import PeriodicSession
from metronome.scheduler import TickScheduler
from metronome.admission import AdmissionController, AdmissionConfig
from metronome.kv_manager import make_policy

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "coaging")
SLO = 0.001


def cohort(facts, n, budget):
    rate = facts.tokens_per_tick / facts.period_s
    return [PeriodicSession(sid=i, facts=facts, period_s=facts.period_s,
                            deadline_s=facts.period_s, phase_s=0.0,
                            kv_budget_tokens=budget, token_rate=rate, length_tokens=0)
            for i in range(n)]


def admit_count(cost, facts, budget, hbm, mode, assumed_age_s):
    ac = AdmissionController(cost, AdmissionConfig(hbm, facts.period_s, 0.90,
                             mode=mode, assumed_age_s=assumed_age_s))
    proto = PeriodicSession(sid=0, facts=facts, period_s=facts.period_s,
                            deadline_s=facts.period_s, phase_s=0.0,
                            kv_budget_tokens=budget,
                            token_rate=facts.tokens_per_tick/facts.period_s)
    return ac.predict_capacity(proto)


def run_cohort(name, n, eviction, degradation, n_frames):
    facts = models.get(name)
    cost = load_cost(name)
    budget = max(512, facts.context_ceiling_tokens // 4)

    def cost_fn(lengths):
        return cost.predict_batch(lengths) if len(lengths) else 0.0

    sched = TickScheduler(cost_fn=cost_fn, frame_budget_s=facts.period_s,
                          ordering="edf", use_silence=False,
                          use_degradation=degradation, deadline_aware=True)
    pop = cohort(facts, n, budget)
    series = []
    for fi in range(n_frames):
        if eviction != "full":
            pol = make_policy(eviction, budget)
            for s in pop:
                s.length_tokens = pol.resident_length(s.length_tokens, budget)
        fr = sched.run_frame(fi, fi*facts.period_s, pop)
        series.append(fr.n_missed / max(1, len(pop)))
    return series


def recovery_frames(series, slo=SLO):
    arr = np.asarray(series)
    peak = int(np.argmax(arr))
    for i in range(peak, len(arr)):
        if arr[i] <= slo:
            return i - peak
    return len(arr) - peak


def run(name, n_frames=400):
    facts = models.get(name)
    cost = load_cost(name)
    budget = max(512, facts.context_ceiling_tokens // 4)
    hbm = hbm_kv_bytes()
    # fill-to-budget time and a young operating age for age-aware
    fill_budget_s = budget / (facts.tokens_per_tick / facts.period_s)
    a_char = fill_budget_s * 0.5

    n_wc = admit_count(cost, facts, budget, hbm, "worst_case", float("inf"))
    n_aa = admit_count(cost, facts, budget, hbm, "age_aware", a_char)
    # run long enough for the synchronized cohort to age fully to the plateau
    n_frames = max(n_frames, int(fill_budget_s / facts.period_s * 1.6))
    print(f"  [{name}] worst-case admits {n_wc}, age-aware admits {n_aa} "
          f"(fill-to-budget {fill_budget_s:.1f}s, {n_frames} frames)")

    scenarios = {
        f"worst-case (N={n_wc})": run_cohort(name, n_wc, "sink_window", True, n_frames),
        f"age-aware no-degr (N={n_aa})": run_cohort(name, n_aa, "sink_window", False, n_frames),
        f"age-aware +degr (N={n_aa})": run_cohort(name, n_aa, "sink_window", True, n_frames),
    }
    os.makedirs(OUT, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4))
    colors = ["#2ca02c", "#d62728", "#1f77b4"]
    summary = {}
    for (label, s), c in zip(scenarios.items(), colors):
        ts = np.arange(len(s)) * facts.period_s
        ax.plot(ts, np.maximum(s, 1e-6), color=c, label=label)
        summary[label] = dict(peak_miss=float(np.max(s)),
                              recovery_s=recovery_frames(s)*facts.period_s,
                              final_miss=float(np.mean(s[-50:])))
    ax.axhline(SLO, color="black", ls=":", label=f"SLO {SLO:.1%}")
    ax.set_yscale("log"); ax.set_xlabel("time since synchronized admission (s)")
    ax.set_ylabel("miss rate"); ax.set_title(f"{name}: co-aging transient (§1.5)")
    ax.legend(fontsize=7); ax.grid(alpha=0.3, which="both")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{name}_coaging.png"), dpi=120)
    plt.close(fig)

    res = dict(model=name, n_worst_case=n_wc, n_age_aware=n_aa,
               fill_to_budget_s=fill_budget_s, scenarios=summary)
    print(f"  [{name}] peak miss: " + "  ".join(
        f"{k.split('(')[0].strip()}={v['peak_miss']:.3f}" for k, v in summary.items()))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=None)
    ap.add_argument("--n-frames", type=int, default=400)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    names = args.models or all_models()
    out = {}
    for name in names:
        print(f"\n=== {name} co-aging ===")
        out[name] = run(name, args.n_frames)
    with open(os.path.join(OUT, "coaging_summary.json"), "w") as fh:
        json.dump(out, fh, indent=2)


if __name__ == "__main__":
    main()
