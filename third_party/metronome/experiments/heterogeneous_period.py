"""Task E — heterogeneous-period co-serving on one GPU (hyperperiod scheduling).

A production accelerator may host tiers with *different* tick periods — e.g. a fast
80 ms speech model (Moshi) and a slow ~1 s omni model (MiniCPM-o). Over the
hyperperiod (LCM of periods) the base quantum is the fast period; a slow session
ticks once every k = P_slow / P_fast base-frames. The scheduler's lever here is
**phase-spreading the slow tier** across the k frames so each base-frame carries
only N_slow/k slow ticks — flattening the load. (Contrast Task B: spreading *hurts*
for a homogeneous tier, but is essential across heterogeneous periods, because a
slow session genuinely needn't tick every fast-frame.)

We co-serve Moshi (fast, 80 ms) + MiniCPM-o (slow, spread to k·80 ms) — two models,
so each tier runs its own weight-shared batch each frame it has due ticks. We
compute the admissible (N_fast, N_slow) region under SPREAD vs BUNCHED slow-tier
scheduling and show spreading expands it.
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

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "hetperiod")


def batch_ms(cost, m, L):
    if m <= 0:
        return 0.0
    return (cost.batch_base + cost.batch_per_session * m + cost.batch_alpha * m * L) * cost.tail_factor


def run(fast_name="moshi", slow_name="minicpm-o", k=10):
    fast, slow = models.get(fast_name), models.get(slow_name)
    cf, cs = load_cost(fast_name), load_cost(slow_name)
    base_ms = fast.period_s * 1000.0          # base quantum = fast period
    budget = base_ms * 0.9
    wf = max(512, fast.context_ceiling_tokens // 4)
    ws = max(512, slow.context_ceiling_tokens // 4)
    hbm = hbm_kv_bytes()

    def feasible(nf, ns, spread):
        # memory: both tiers resident
        mem = nf * wf * fast.kv_bytes_per_token + ns * ws * slow.kv_bytes_per_token
        if mem > hbm:
            return False
        # fast batch every frame (weight read for fast model)
        fast_cost = batch_ms(cf, nf, wf)
        if spread:
            # slow tier spread across k frames -> ceil(ns/k) slow due each frame
            slow_due = int(np.ceil(ns / k))
            worst_frame = fast_cost + batch_ms(cs, slow_due, ws)
        else:
            # bunched: the heavy frame carries ALL slow ticks
            worst_frame = fast_cost + batch_ms(cs, ns, ws)
        return worst_frame <= budget

    def max_ns(nf, spread):
        lo, hi = 0, 100000
        if not feasible(nf, 0, spread):
            return 0
        while feasible(nf, hi, spread) and hi < 100000:
            lo, hi = hi, hi * 2
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if feasible(nf, mid, spread):
                lo = mid
            else:
                hi = mid - 1
        return lo

    nf_max = max_ns_when_alone = 0
    # find max fast-only
    nf = 0
    while feasible(nf + 1, 0, True):
        nf += 1
    nf_max = nf
    nfs = list(range(0, nf_max + 1, max(1, nf_max // 30)))
    spread_frontier = [max_ns(nf, True) for nf in nfs]
    bunched_frontier = [max_ns(nf, False) for nf in nfs]

    os.makedirs(OUT, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6.5, 5))
    ax.plot(nfs, spread_frontier, "o-", color="#2ca02c", label=f"slow spread across k={k}")
    ax.plot(nfs, bunched_frontier, "s--", color="#d62728", label="slow bunched (naive)")
    ax.set_xlabel(f"N_fast ({fast_name}, {base_ms:.0f} ms)")
    ax.set_ylabel(f"max N_slow ({slow_name}, {base_ms*k:.0f} ms)")
    ax.set_title(f"Heterogeneous-period admissible region (one GPU)")
    ax.legend(); ax.grid(alpha=0.3); ax.fill_between(nfs, bunched_frontier, spread_frontier,
                                                     color="#2ca02c", alpha=0.12)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "admissible_region.png"), dpi=120)
    plt.close(fig)

    # area (trapezoid) of each frontier = a scalar "co-serving capacity"
    area_spread = float(np.trapezoid(spread_frontier, nfs))
    area_bunched = float(np.trapezoid(bunched_frontier, nfs))
    res = dict(fast=fast_name, slow=slow_name, k=k, base_ms=base_ms,
               nf_max=nf_max, area_spread=area_spread, area_bunched=area_bunched,
               expansion=round(area_spread / max(1.0, area_bunched), 2),
               frontier=dict(nf=nfs, spread=spread_frontier, bunched=bunched_frontier))
    with open(os.path.join(OUT, "hetperiod_summary.json"), "w") as fh:
        json.dump(res, fh, indent=2)
    print(f"Heterogeneous-period co-serving: {fast_name}({base_ms:.0f}ms) + "
          f"{slow_name}({base_ms*k:.0f}ms) on one GPU")
    print(f"  fast-only capacity N_fast={nf_max}")
    print(f"  admissible-region area: spread={area_spread:.0f} bunched={area_bunched:.0f} "
          f"-> spreading expands the co-serving region {res['expansion']}x")
    # a representative point
    mid = nfs[len(nfs)//2]
    print(f"  at N_fast={mid}: max N_slow spread={max_ns(mid,True)} vs bunched={max_ns(mid,False)}")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", default="moshi")
    ap.add_argument("--slow", default="minicpm-o")
    ap.add_argument("--k", type=int, default=10)
    args = ap.parse_args()
    run(args.fast, args.slow, args.k)


if __name__ == "__main__":
    main()
