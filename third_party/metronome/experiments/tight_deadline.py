"""S7: tight-deadline hardening (80 ms regime) — "the scheduler matters most when
the deadline is tight."

Two results:
  (1) LIVE jitter: measure the per-tick latency distribution (p50/p99/p999) for a
      fixed multi-tenant batch with CUDA graphs ON vs OFF. Graphs kill per-tick
      launch overhead -> the p999 tail tightens, which is what a 12.5 Hz (80 ms)
      loop lives or dies on.
  (2) Tightness sensitivity: M-vs-B1 MSCS gain at the 80 ms (Moshi) deadline vs the
      1 s (MiniCPM-o) deadline, and the fraction of the frame budget consumed by
      fixed overhead — larger at 80 ms, so scheduling discipline pays off more.
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

from bench.gpu_probe import wait_for_window
from bench.tick_kernel import TickKernel
from experiments._common import load_cost, hbm_kv_bytes, all_models
from metronome import models
from sim.simulator import Simulator, SimConfig
from bench.generator import WorkloadConfig, make_population
from bench.metrics import mscs, mscs_served

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "tight")
TARGET_MISS = 0.001


def live_jitter(name, B=4, L=2048, reps=200):
    facts = models.get(name)
    L = min(L, facts.context_ceiling_tokens)
    k = TickKernel(facts)
    wait_for_window(need_free_gib=10, max_util_pct=75, quiet=True, timeout_s=5400)
    tg = k.time_homogeneous(B, L, reps=reps, warmup=20, use_graph=True)
    wait_for_window(need_free_gib=10, max_util_pct=75, quiet=True, timeout_s=5400)
    te = k.time_homogeneous(B, L, reps=reps, warmup=20, use_graph=False)
    return tg, te


def fig_jitter(name, tg, te):
    fig, ax = plt.subplots(figsize=(6, 4))
    bins = np.linspace(min(min(tg.ms), min(te.ms)), max(max(tg.ms), max(te.ms)), 50)
    ax.hist(te.ms, bins=bins, alpha=0.55, color="#d62728",
            label=f"eager  p50={te.p50:.2f} p999={te.stat(0.999):.2f}")
    ax.hist(tg.ms, bins=bins, alpha=0.55, color="#2ca02c",
            label=f"CUDA graph  p50={tg.p50:.2f} p999={tg.stat(0.999):.2f}")
    ax.set_xlabel("per-tick latency (ms)"); ax.set_ylabel("count")
    ax.set_title(f"{name}: CUDA graphs tighten the per-tick tail (B={tg.batch_sessions})")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{name}_jitter.png"), dpi=120)
    plt.close(fig)


def mscs_gain(name):
    facts = models.get(name)
    cost = load_cost(name)
    hbm = hbm_kv_bytes()
    window = max(512, facts.context_ceiling_tokens // 4)
    ceiling = facts.context_ceiling_tokens

    def sweep(**kw):
        growth = kw.pop("growth")
        ns = [1,2,4,6,8,12,16,24,32,48,64,96,128,160,192,256,384,512,768,1024]
        curve = []
        for n in ns:
            cfg = SimConfig(cost=cost, frame_budget_s=facts.period_s,
                            hbm_kv_bytes=hbm, **kw)
            wl = WorkloadConfig(facts=facts, kv_budget_tokens=growth,
                                mean_session_s=facts.fill_time_s*0.6, seed=0)
            r = Simulator(cfg).run_static(make_population(wl, n), 200)
            curve.append((n, r.admitted, r.metrics.miss_rate))
        return mscs_served(curve, TARGET_MISS)

    b1 = sweep(admission=False, ordering="fifo", eviction="full",
               degradation=False, silence=False, growth=ceiling)
    m = sweep(admission=True, ordering="edf", eviction="sink_window",
              degradation=True, silence=False, kv_budget_tokens=window, growth=window)
    budget_ms = facts.period_s * 1000
    overhead_frac = cost.batch_base / budget_ms
    return dict(model=name, deadline_ms=budget_ms, mscs_b1=b1, mscs_m=m,
                gain=m / max(1, b1), fixed_overhead_frac_of_budget=overhead_frac)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=None)
    ap.add_argument("--live-model", default="moshi")
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--no-live", action="store_true")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    names = args.models or all_models()

    # (1) live jitter on the tight-deadline model
    if not args.no_live and args.live_model in names:
        tg, te = live_jitter(args.live_model, reps=args.reps)
        fig_jitter(args.live_model, tg, te)
        jit = dict(model=args.live_model,
                   graph=dict(p50=tg.p50, p99=tg.p99, p999=tg.stat(0.999)),
                   eager=dict(p50=te.p50, p99=te.p99, p999=te.stat(0.999)),
                   p999_reduction=round(1 - tg.stat(0.999)/max(te.stat(0.999),1e-9), 3))
        with open(os.path.join(OUT, f"{args.live_model}_jitter.json"), "w") as fh:
            json.dump(jit, fh, indent=2)
        print(f"[{args.live_model}] jitter p999: eager={te.stat(0.999):.2f}ms "
              f"graph={tg.stat(0.999):.2f}ms  ({jit['p999_reduction']*100:.0f}% lower)")

    # (2) tightness sensitivity across models
    gains = [mscs_gain(n) for n in names]
    with open(os.path.join(OUT, "tightness.json"), "w") as fh:
        json.dump(gains, fh, indent=2)

    fig, ax = plt.subplots(figsize=(6, 4))
    xs = [f"{g['model']}\n({g['deadline_ms']:.0f}ms)" for g in gains]
    ax.bar(xs, [g["gain"] for g in gains], color="#2ca02c")
    ax.set_ylabel("M / B1 MSCS gain (x)")
    ax.set_title("Scheduler/KV-budget gain vs deadline tightness")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "tightness.png"), dpi=120)
    plt.close(fig)

    print("\n=== Tight-deadline sensitivity ===")
    for g in sorted(gains, key=lambda x: x["deadline_ms"]):
        print(f"  {g['model']:12s} deadline={g['deadline_ms']:6.0f}ms  "
              f"B1={g['mscs_b1']:5d} M={g['mscs_m']:5d}  gain={g['gain']:.2f}x  "
              f"fixed-overhead={g['fixed_overhead_frac_of_budget']*100:.0f}% of budget")


if __name__ == "__main__":
    main()
