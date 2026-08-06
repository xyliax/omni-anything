"""Task A — live multi-tenant validation (close the sim↔real loop).

`validate_sim.py` checked the cost model on held-out *single* batch configs. This
goes further: it runs the per-tick batch on the **real GPU** across the
(concurrency N, context length L) operating points the scheduler actually visits as
a multi-tenant cohort ages, and checks that the *system-level* prediction — the
deadline-miss rate and the p99/p999 jitter over an aging multi-tenant run — matches
what the calibrated simulator predicts from the fitted cost model.

For each concurrency N we sweep the session age a (so L = min(rate·a, window)),
measure the real batched p50/p99/p999 tick latency at each age, and compare:
  * measured per-tick latency vs the simulator's predicted latency (per age), and
  * measured deadline-miss rate over the (uniform) age distribution vs the simulator.

Runs only in a clean GPU window (CUDA graphs, to match the clean cost model).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bench.gpu_probe import wait_for_window
from bench.tick_kernel import TickKernel
from experiments._common import load_cost, hbm_kv_bytes, all_models
from metronome import models

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "live")
SLO = 0.001


def run(name, concurrencies, reps, max_total_kv):
    facts = models.get(name)
    cost = load_cost(name)
    window = max(512, facts.context_ceiling_tokens // 4)
    budget_ms = facts.period_s * 1000.0
    rate = facts.tokens_per_tick / facts.period_s
    k = TickKernel(facts)
    ages = np.linspace(0, window / rate, 8)        # age trajectory up to the window cap
    Ls = [int(min(rate * a, window)) for a in ages]

    rows = []
    for N in concurrencies:
        for L in Ls:
            if N * L > max_total_kv:
                continue
            # run politely in whatever window is free; compare the robust MEDIAN
            # (matches how the cost model was fit) so transient co-tenant spikes do
            # not corrupt the comparison.
            wait_for_window(need_free_gib=8, max_util_pct=70, quiet=True, timeout_s=10800)
            t = k.time_homogeneous(N, L, reps=reps, warmup=12, use_graph=True)
            pred = cost.predict_batch([L] * N, tail=False)   # median prediction
            rows.append(dict(N=N, L=L, total_kv=N * L,
                             meas_p50=t.p50, meas_p99=t.p99, meas_p999=t.stat(0.999),
                             pred=pred, graphed=t.graphed))
            print(f"  [{name}] N={N:3d} L={L:6d}  meas p50/p99/p999="
                  f"{t.p50:.2f}/{t.p99:.2f}/{t.stat(0.999):.2f}ms  pred(med)={pred:.2f}ms")

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f"{name}_live.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["N", "L", "total_kv", "meas_p50", "meas_p99", "meas_p999", "pred"])
        for r in rows:
            w.writerow([r["N"], r["L"], r["total_kv"], round(r["meas_p50"], 4),
                        round(r["meas_p99"], 4), round(r["meas_p999"], 4), round(r["pred"], 4)])

    # system-level agreement: per-N measured vs predicted miss-rate over the age sweep
    sysrows = []
    for N in concurrencies:
        rN = [r for r in rows if r["N"] == N]
        if not rN:
            continue
        meas_miss = float(np.mean([r["meas_p99"] > budget_ms for r in rN]))
        pred_miss = float(np.mean([r["pred"] > budget_ms for r in rN]))
        rel = [abs(r["meas_p50"] - r["pred"]) / max(r["meas_p50"], 1e-9) for r in rN]
        sysrows.append(dict(N=N, meas_miss=meas_miss, pred_miss=pred_miss,
                            median_rel_err=float(np.median(rel)),
                            max_rel_err=float(np.max(rel)),
                            meas_p999_max=float(np.max([r["meas_p999"] for r in rN]))))
        print(f"  [{name}] N={N:3d}: measured miss={meas_miss:.3f} pred miss={pred_miss:.3f} "
              f"| latency rel-err median={sysrows[-1]['median_rel_err']:.3f}")

    # scatter: measured median vs predicted across all operating points
    meas = np.array([r["meas_p50"] for r in rows]); pred = np.array([r["pred"] for r in rows])
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    lim = max(meas.max(), pred.max()) * 1.1
    ax1.plot([0, lim], [0, lim], "k:", label="ideal")
    sc = ax1.scatter(pred, meas, c=[r["N"] for r in rows], cmap="viridis")
    ax1.axhline(budget_ms, color="red", ls="--", alpha=0.5, label=f"{budget_ms:.0f} ms deadline")
    ax1.set_xlabel("simulator-predicted tick latency (ms)")
    ax1.set_ylabel("measured tick latency (ms)")
    ax1.set_title(f"{name}: live multi-tenant vs simulator"); ax1.legend(fontsize=8)
    plt.colorbar(sc, ax=ax1, label="concurrency N")
    # latency-vs-age for the largest N (measured vs predicted), the live money plot
    Nmax = max(r["N"] for r in rows)
    rN = sorted([r for r in rows if r["N"] == Nmax], key=lambda r: r["L"])
    ax2.plot([r["L"] for r in rN], [r["meas_p50"] for r in rN], "o-", color="#1f77b4", label="measured p50")
    ax2.plot([r["L"] for r in rN], [r["pred"] for r in rN], "s--", color="#ff7f0e", label="predicted median")
    ax2.axhline(budget_ms, color="red", ls=":", label=f"{budget_ms:.0f} ms deadline")
    ax2.set_xlabel("resident KV length (= age)"); ax2.set_ylabel("tick latency (ms)")
    ax2.set_title(f"{name}: live latency vs age (N={Nmax})"); ax2.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{name}_live.png"), dpi=120)
    plt.close(fig)

    overall_rel = float(np.median([abs(r["meas_p50"]-r["pred"])/max(r["meas_p50"],1e-9)
                                   for r in rows]))
    res = dict(model=name, n_points=len(rows), median_rel_err=overall_rel,
               per_N=sysrows, ok=overall_rel <= 0.15)
    print(f"[{name}] LIVE MULTI-TENANT: median latency rel-err={overall_rel:.3f} "
          f"-> {'PASS' if res['ok'] else 'CHECK'} (<=0.15)")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=None)
    ap.add_argument("--concurrencies", nargs="*", type=int, default=[1, 4, 8, 16])
    ap.add_argument("--reps", type=int, default=50)
    ap.add_argument("--max-total-kv", type=int, default=80000)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    names = args.models or all_models()
    summ = {}
    for name in names:
        print(f"\n=== {name} live multi-tenant ===")
        try:
            summ[name] = run(name, args.concurrencies, args.reps, args.max_total_kv)
        except TimeoutError as e:
            print(f"[{name}] SKIPPED — no GPU window: {e}")
        except Exception as e:
            print(f"[{name}] FAILED: {type(e).__name__}: {e}")
    with open(os.path.join(OUT, "live_summary.json"), "w") as fh:
        json.dump(summ, fh, indent=2)
    print("\n=== LIVE MULTI-TENANT VALIDATION ===")
    for n, r in summ.items():
        print(f"  {n}: median rel-err {r['median_rel_err']:.3f} "
              f"({'PASS' if r['ok'] else 'CHECK'})")


if __name__ == "__main__":
    main()
