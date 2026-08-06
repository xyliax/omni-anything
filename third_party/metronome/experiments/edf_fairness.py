"""EDF fairness: EDF's value is per-session deadline differentiation, not aggregate
MSCS (which is why B2 ~ B1 on MSCS). With a mixed-deadline population under
overload, EDF protects the tight-deadline class by sacrificing slack-deadline
sessions first; FIFO spreads misses blindly.

Workload: two classes, 50% "tight" (relative deadline = 0.5*period) and 50%
"loose" (deadline = period). Run an overloaded population (degradation off so the
ordering decides who misses) and report per-class miss-rate under EDF vs FIFO.
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
from bench.generator import WorkloadConfig

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "edf")


def mixed_population(facts, n, budget, seed=0):
    rng = np.random.default_rng(seed)
    rate = facts.tokens_per_tick / facts.period_s
    pop = []
    for i in range(n):
        tight = (i % 2 == 0)
        s = PeriodicSession(
            sid=i, facts=facts, period_s=facts.period_s,
            deadline_s=facts.period_s * (0.5 if tight else 1.0),
            phase_s=rng.random() * facts.period_s, kv_budget_tokens=budget,
            token_rate=rate,
            length_tokens=min(int(rate * rng.exponential(facts.fill_time_s*0.6)), budget),
        )
        s._tight = tight
        pop.append(s)
    return pop


def run_one(name, ordering, n, n_frames=120):
    """Frame-level deadline-fit shedding. Because a GPU micro-batch completes as a
    unit, per-session deadlines are honoured by *who is included*, not by ordering
    within the kernel. We include sessions in the policy's order and run the batch;
    a session is met iff the batch time (over the sessions included up to and
    including it) does not exceed its own relative deadline — classic EDF batched
    feasibility. EDF (tightest-first) protects the tight class; FIFO sheds blindly."""
    facts = models.get(name)
    cost = load_cost(name)
    budget = max(512, facts.context_ceiling_tokens // 4)
    pop = mixed_population(facts, n, budget)
    rate = facts.tokens_per_tick / facts.period_s
    miss = {True: 0, False: 0}
    cnt = {True: 0, False: 0}

    for fi in range(n_frames):
        if ordering == "edf":
            order = sorted(pop, key=lambda s: s.deadline_s)
        elif ordering == "fifo":
            order = sorted(pop, key=lambda s: s.phase_s)   # arrival/phase order
        else:
            order = list(pop)
        # incremental batch: a session is met iff including it keeps batch <= its D
        lengths = []
        for s in order:
            lengths.append(s.length_tokens)
            batch_ms = cost.predict_batch(lengths)
            met = batch_ms <= s.deadline_s * 1000.0
            cnt[s._tight] += 1
            if not met:
                miss[s._tight] += 1
                lengths.pop()   # shed it (don't let it inflate later sessions)
        for s in pop:           # age the population
            s.length_tokens = min(s.length_tokens + max(1, int(rate*facts.period_s)),
                                  s.kv_budget_tokens)
    return (miss[True]/max(1,cnt[True]), miss[False]/max(1,cnt[False]))


def run(name):
    facts = models.get(name)
    # pick an overloaded N ~ 1.5x the rough timing capacity
    cost = load_cost(name)
    budget = max(512, facts.context_ceiling_tokens // 4)
    denom = cost.batch_per_session + cost.batch_alpha * budget
    cap = max(4, int((facts.period_s*1000*0.9 - cost.batch_base)/max(denom,1e-9)))
    n = int(cap * 1.5)

    edf_t, edf_l = run_one(name, "edf", n)
    fifo_t, fifo_l = run_one(name, "fifo", n)
    return dict(model=name, n=n, capacity=cap,
                edf_tight=edf_t, edf_loose=edf_l,
                fifo_tight=fifo_t, fifo_loose=fifo_l)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=None)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    names = args.models or all_models()
    res = [run(n) for n in names]

    fig, axes = plt.subplots(1, len(res), figsize=(4*len(res), 4), squeeze=False)
    for ax, r in zip(axes[0], res):
        x = np.arange(2)
        ax.bar(x-0.2, [r["fifo_tight"], r["fifo_loose"]], 0.4, label="FIFO", color="#d62728")
        ax.bar(x+0.2, [r["edf_tight"], r["edf_loose"]], 0.4, label="EDF", color="#2ca02c")
        ax.set_xticks(x); ax.set_xticklabels(["tight\n(D=.5T)", "loose\n(D=T)"])
        ax.set_ylabel("miss-rate"); ax.set_title(f"{r['model']} (N={r['n']})")
        ax.legend(fontsize=8); ax.grid(alpha=0.3, axis="y")
    fig.suptitle("EDF protects the tight-deadline class; FIFO does not")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "edf_fairness.png"), dpi=120)
    plt.close(fig)

    with open(os.path.join(OUT, "edf_fairness.json"), "w") as fh:
        json.dump(res, fh, indent=2)
    print("=== EDF fairness (per-class miss-rate under overload) ===")
    for r in res:
        print(f"  {r['model']:12s} N={r['n']:4d}  "
              f"FIFO tight={r['fifo_tight']:.3f} loose={r['fifo_loose']:.3f}  |  "
              f"EDF tight={r['edf_tight']:.3f} loose={r['edf_loose']:.3f}")


if __name__ == "__main__":
    main()
