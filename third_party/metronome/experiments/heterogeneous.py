"""Heterogeneous multi-tenant co-serving (docs/PRODUCTION.md H6).

One GPU hosts two SLA tiers simultaneously: a *premium* tight-deadline tier
(relative deadline 0.4x the period) and a *standard* loose tier (deadline = period).
Metronome (EDF by absolute deadline + per-session admission) should meet BOTH tiers'
SLAs by shedding the loose tier first under pressure; throughput-greedy violates the
tight tier (and usually both).

Reports per-tier deadline-miss rate for Metronome vs greedy across load.
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
                   "results", "hetero")
SLO = 0.001
PREMIUM_FRAC = 0.4
PREMIUM_DEADLINE = 0.4   # x period


def mixed_pop(facts, n, budget, seed=0):
    rng = np.random.default_rng(seed)
    rate = facts.tokens_per_tick / facts.period_s
    pop = []
    for i in range(n):
        premium = rng.random() < PREMIUM_FRAC
        s = PeriodicSession(
            sid=i, facts=facts, period_s=facts.period_s,
            deadline_s=facts.period_s * (PREMIUM_DEADLINE if premium else 1.0),
            phase_s=0.0, kv_budget_tokens=budget, token_rate=rate,
            length_tokens=min(int(rate * rng.exponential(facts.fill_time_s*0.4)), budget))
        s._premium = premium
        pop.append(s)
    return pop


def run_load(name, n, deadline_aware, admission, n_frames=200):
    facts = models.get(name)
    cost = load_cost(name)
    budget = max(512, facts.context_ceiling_tokens // 4)
    hbm = hbm_kv_bytes()

    def cost_fn(lengths):
        return cost.predict_batch(lengths) if len(lengths) else 0.0

    sched = TickScheduler(cost_fn=cost_fn, frame_budget_s=facts.period_s,
                          ordering="edf" if deadline_aware else "fifo",
                          use_silence=False, use_degradation=False,
                          deadline_aware=deadline_aware)
    pop = mixed_pop(facts, n, budget)
    if admission:
        ac = AdmissionController(cost, AdmissionConfig(hbm, facts.period_s, 0.90,
                                 mode="worst_case"))
        adm = []
        for s in pop:
            if ac.try_admit(adm, s).admit:
                adm.append(s)
        pop = adm
    miss = {True: [0,0], False: [0,0]}   # premium/standard -> [missed, total]
    for fi in range(n_frames):
        pol = make_policy("sink_window", budget)
        for s in pop:
            s.length_tokens = pol.resident_length(s.length_tokens, budget)
        fr = sched.run_frame(fi, fi*facts.period_s, pop)
        missed = set(fr.missed_sids)
        for s in pop:
            miss[s._premium][1] += 1
            if s.sid in missed:
                miss[s._premium][0] += 1
    prem = miss[True][0]/max(1, miss[True][1])
    std = miss[False][0]/max(1, miss[False][1])
    return prem, std, len(pop)


def run(name, n_frames=200):
    facts = models.get(name)
    cost = load_cost(name)
    budget = max(512, facts.context_ceiling_tokens // 4)
    denom = cost.batch_per_session + cost.batch_alpha * budget
    cap = max(4, int((facts.period_s*1000*0.9 - cost.batch_base)/max(denom, 1e-9)))
    loads = [int(m*cap) for m in (0.8, 1.2, 1.6, 2.0)]
    rows = []
    for n in loads:
        mp, ms, madm = run_load(name, n, True, True, n_frames)     # Metronome
        gp, gs, gadm = run_load(name, n, False, False, n_frames)   # greedy
        rows.append(dict(offered=n, m_premium=mp, m_standard=ms, m_admitted=madm,
                         g_premium=gp, g_standard=gs))
        print(f"  [{name}] N={n:4d}  Metronome: prem={mp:.4f} std={ms:.4f} (adm {madm})  "
              f"greedy: prem={gp:.4f} std={gs:.4f}")
    os.makedirs(OUT, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4))
    off = [r["offered"] for r in rows]
    ax.plot(off, [max(r["g_premium"],1e-6) for r in rows], "s--", color="#d62728", label="greedy premium")
    ax.plot(off, [max(r["g_standard"],1e-6) for r in rows], "o--", color="#ff9896", label="greedy standard")
    ax.plot(off, [max(r["m_premium"],1e-6) for r in rows], "s-", color="#2ca02c", label="Metronome premium")
    ax.plot(off, [max(r["m_standard"],1e-6) for r in rows], "o-", color="#98df8a", label="Metronome standard")
    ax.axhline(SLO, color="black", ls=":", label=f"SLO {SLO:.1%}")
    ax.set_yscale("log"); ax.set_xlabel("offered sessions"); ax.set_ylabel("deadline-miss rate")
    ax.set_title(f"{name}: heterogeneous tiers (premium D=0.4T, standard D=T)")
    ax.legend(fontsize=7); ax.grid(alpha=0.3, which="both")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{name}_hetero.png"), dpi=120)
    plt.close(fig)
    return dict(model=name, capacity=cap, rows=rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=None)
    ap.add_argument("--n-frames", type=int, default=200)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    names = args.models or all_models()
    out = {}
    for name in names:
        print(f"\n=== {name} heterogeneous ===")
        out[name] = run(name, args.n_frames)
    with open(os.path.join(OUT, "hetero_summary.json"), "w") as fh:
        json.dump(out, fh, indent=2)


if __name__ == "__main__":
    main()
