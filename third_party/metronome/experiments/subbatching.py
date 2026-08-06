"""Tasks B + D — temporal sub-batching / phase-slotting: capacity cost vs
deadline-differentiation benefit.

A natural idea is to *spread* phase-misaligned sessions across K sub-frames of the
period (phase-slotting) so each sub-batch is smaller. We show analytically and in
simulation that for the single-accelerator, period==frame interaction model — where
every admitted session ticks once per period — this **forfeits weight-read
amortization**: the shared per-layer weight read (the `base` term) is paid K times
per period, so

    K-way sub-batching is feasible iff  K·base + per·N + α·ΣL ≤ period.

Since `base > 0`, capacity is *maximised at K = 1* (the monolithic batch). Sub-batching
does NOT raise single-GPU capacity — a useful negative result that corrects the
intuition.

Its real value is **per-session deadline differentiation**: a micro-batch completes
as a unit, so under K = 1 a tight-deadline session waits for the whole batch. Putting
the tight class in an early sub-batch (EDF order) lets it complete at its sub-batch
boundary and meet a deadline D < period that the monolithic batch would miss — at a
capacity cost. We quantify both sides.
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

from experiments._common import load_cost, all_models
from metronome import models

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "subbatch")


def batch_ms(cost, m, L):
    if m <= 0:
        return 0.0
    return (cost.batch_base + cost.batch_per_session * m + cost.batch_alpha * m * L) * cost.tail_factor


def capacity_vs_K(cost, facts, window, Ks):
    """Max homogeneous N feasible under K-way sub-batching (all at the window
    plateau, deadline = period)."""
    period_ms = facts.period_s * 1000.0 * 0.9
    out = []
    for K in Ks:
        # K sub-batches of N/K sessions; total period work = sum of sub-batch costs.
        # find max N s.t. K * batch_ms(N/K, window) <= period_ms
        best = 0
        for N in range(1, 20000):
            m = int(np.ceil(N / K))
            total = K * batch_ms(cost, m, window)
            if total <= period_ms:
                best = N
            else:
                break
        out.append(best)
    return out


def hetero_differentiation(cost, facts, window, Ks, N, premium_frac=0.4,
                           premium_deadline=0.4):
    """With a mixed-deadline population at concurrency N, report the tight (premium)
    class miss-rate under K-way sub-batching with EDF (tight class in the first
    sub-batches). K=1 is the monolithic batch."""
    period_ms = facts.period_s * 1000.0
    n_prem = int(N * premium_frac)
    n_std = N - n_prem
    prem_deadline_ms = period_ms * premium_deadline
    out = []
    for K in Ks:
        # EDF: premium first. Sub-batch size m = ceil(N/K). Premium occupy the first
        # ceil(n_prem/m) sub-batches; a premium session completes at the cumulative
        # time of its sub-batch.
        m = int(np.ceil(N / K))
        # cumulative completion time of sub-batch j (1-indexed)
        prem_missed = 0
        for i in range(n_prem):
            sub_idx = i // m                      # which sub-batch (0-indexed)
            completion = (sub_idx + 1) * batch_ms(cost, m, window)
            if completion > prem_deadline_ms:
                prem_missed += 1
        std_missed = 0
        for i in range(n_std):
            sub_idx = (n_prem + i) // m
            completion = (sub_idx + 1) * batch_ms(cost, m, window)
            if completion > period_ms:
                std_missed += 1
        out.append(dict(K=K, prem_miss=prem_missed / max(1, n_prem),
                        std_miss=std_missed / max(1, n_std),
                        total_period_ms=K * batch_ms(cost, m, window)))
    return out


def run(name):
    facts = models.get(name)
    cost = load_cost(name)
    window = max(512, facts.context_ceiling_tokens // 4)
    Ks = [1, 2, 4, 8, 16]
    os.makedirs(OUT, exist_ok=True)

    cap = capacity_vs_K(cost, facts, window, Ks)
    # heterogeneous: pick N near the monolithic capacity so tight sessions are at risk
    N = max(8, cap[0])
    het = hetero_differentiation(cost, facts, window, Ks, N)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    ax1.plot(Ks, cap, "o-", color="#d62728")
    ax1.set_xlabel("sub-batches per period K"); ax1.set_ylabel("max homogeneous capacity")
    ax1.set_title(f"{name}: sub-batching forfeits weight amortization\n(capacity max at K=1)")
    ax1.grid(alpha=0.3)
    ax2.plot([h["K"] for h in het], [max(h["prem_miss"],1e-6) for h in het], "o-",
             color="#2ca02c", label="premium (D=0.4·T)")
    ax2.plot([h["K"] for h in het], [max(h["std_miss"],1e-6) for h in het], "s-",
             color="#1f77b4", label="standard (D=T)")
    ax2.axhline(0.001, color="black", ls=":", label="SLO")
    ax2.set_yscale("log"); ax2.set_xlabel("sub-batches per period K")
    ax2.set_ylabel("deadline-miss rate")
    ax2.set_title(f"{name}: sub-batching protects the tight class (N={N})")
    ax2.legend(fontsize=8); ax2.grid(alpha=0.3, which="both")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{name}_subbatch.png"), dpi=120)
    plt.close(fig)

    res = dict(model=name, Ks=Ks, capacity_vs_K=cap, N_hetero=N,
               hetero=het, capacity_loss_K2=round(1 - cap[1]/max(1, cap[0]), 3))
    print(f"[{name}] capacity vs K {dict(zip(Ks, cap))}  "
          f"(K=2 costs {res['capacity_loss_K2']*100:.0f}% capacity)")
    print(f"  premium miss: " + "  ".join(f"K{h['K']}={h['prem_miss']:.2f}" for h in het))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=None)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    names = args.models or all_models()
    out = {n: run(n) for n in names}
    with open(os.path.join(OUT, "subbatch_summary.json"), "w") as fh:
        json.dump(out, fh, indent=2)


if __name__ == "__main__":
    main()
