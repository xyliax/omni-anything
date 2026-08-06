"""G5 / GATE B closure: validate the calibrated simulator against the live GPU.

The simulator's per-tick cost is the fitted CostModel. Here we measure the *real*
kernel on held-out multi-tenant configs (batch sizes / lengths NOT in the fit grid)
and check the model predicts them within tolerance. This is what licenses using the
simulator for the large sweeps and the predicted-vs-measured MSCS claim (Goal G5).

Outputs: results/validate/<model>_validation.csv + a measured-vs-predicted scatter.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bench.gpu_probe import wait_for_window
from bench.tick_kernel import TickKernel
from experiments._common import load_cost, all_models
from metronome import models

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "validate")

# held-out (B, L) configs (interleaved with / between the fit grid points)
def heldout(ceiling):
    pts = []
    for B in (3, 5, 6, 10):
        for L in (768, 3000, min(6000, ceiling)):
            if L <= ceiling and B * L <= 120_000:
                pts.append((B, L))
    return pts


def run(name, reps, use_graph=True):
    facts = models.get(name)
    cost = load_cost(name)
    k = TickKernel(facts)
    rows = []
    for (B, L) in heldout(facts.context_ceiling_tokens):
        wait_for_window(need_free_gib=10, max_util_pct=75, quiet=True, timeout_s=5400)
        t = k.time_homogeneous(B, L, reps=reps, warmup=10, use_graph=use_graph)
        # validate the robust structural (median) model on the clean median; the tail
        # factor is validated separately (it is not cross-tenant contention).
        pred = cost.predict_batch([L] * B, tail=False)
        rel = abs(t.p50 - pred) / max(t.p50, 1e-9)
        rows.append((B, L, B * L, t.p50, pred, rel))
        print(f"  [{name}] B={B:2d} L={L:5d}  measured p50={t.p50:7.3f}ms  "
              f"pred={pred:7.3f}ms  rel_err={rel:.3f}")
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f"{name}_validation.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["B", "L", "total_kv", "measured_p50_ms", "predicted_p50_ms", "rel_err"])
        for r in rows:
            w.writerow([r[0], r[1], r[2], round(r[3], 4), round(r[4], 4), round(r[5], 4)])

    meas = np.array([r[3] for r in rows]); pred = np.array([r[4] for r in rows])
    fig, ax = plt.subplots(figsize=(5, 5))
    lim = max(meas.max(), pred.max()) * 1.1
    ax.plot([0, lim], [0, lim], "k:", label="ideal")
    ax.scatter(pred, meas, c="#1f77b4")
    ax.set_xlabel("predicted p99 tick latency (ms)")
    ax.set_ylabel("measured p99 tick latency (ms)")
    ax.set_title(f"{name}: simulator cost model vs live GPU (held-out)")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{name}_scatter.png"), dpi=120)
    plt.close(fig)

    max_rel = float(np.max([r[5] for r in rows]))
    med_rel = float(np.median([r[5] for r in rows]))
    ok = max_rel <= 0.15
    print(f"[{name}] held-out validation: median rel_err={med_rel:.3f} "
          f"max={max_rel:.3f}  -> {'PASS' if ok else 'CHECK'} (<=0.15)")
    return ok, med_rel, max_rel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=None)
    ap.add_argument("--reps", type=int, default=30)
    ap.add_argument("--eager", action="store_true")
    args = ap.parse_args()
    names = args.models or all_models()
    summ = {}
    for name in names:
        ok, med, mx = run(name, args.reps, use_graph=not args.eager)
        summ[name] = dict(pass_=ok, median_rel=med, max_rel=mx)
    print("\n=== SIM VALIDATION (G5) ===")
    for k, v in summ.items():
        print(f"  {k}: {'PASS' if v['pass_'] else 'CHECK'} "
              f"(median {v['median_rel']:.3f}, max {v['max_rel']:.3f})")


if __name__ == "__main__":
    main()
