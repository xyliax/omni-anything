"""Real KV-budget sweep on the engine (Contribution 2, measured).

Measures the real timing capacity (the concurrency whose measured p99 tick latency
stays within the frame budget, at the plateau) as a function of the KV-budget /
window size, on the running engine. The capacity rises as the window shrinks — the
real KV-budget knob — and the rise is large for no-self-bounding Moshi/MiniCPM-o
(*essential*) vs modest for self-windowing Qwen3-Omni (*complementary*).
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
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bench.gpu_probe import wait_for_window
from metronome.engine import ServingEngine
from metronome import models
from experiments._common import hbm_kv_bytes

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "engine")


def measure_onset(facts, budget_tokens, n_frames, max_cache_gib):
    per = budget_tokens * facts.num_kv_heads * facts.head_dim * 2 * 2
    maxN = max(8, int(max_cache_gib * 2**30 / per))
    ns = [n for n in [8,16,24,32,48,64,96,128,160,192,256,320,384,448,512,640,768]
          if n <= maxN]
    budget_ms = facts.period_s * 1000.0
    eng = ServingEngine(facts, max_sessions=max(ns), max_budget_tokens=budget_tokens)
    onset = 0
    for N in ns:
        cache_gib = N * per / 2**30
        wait_for_window(need_free_gib=cache_gib + 1.5, max_util_pct=85, quiet=True, timeout_s=7200)
        try:
            lats = eng.serve_cohort(N, n_frames=n_frames, start_lengths=[budget_tokens]*N,
                                    grow=False, warmup=4)
        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache(); break
        p99 = float(np.percentile(lats, 99))
        if p99 <= budget_ms:
            onset = N
        else:
            break
    del eng; torch.cuda.empty_cache()
    # combine with the true L-layer memory cap
    mem_cap = int(hbm_kv_bytes() / (budget_tokens * facts.kv_bytes_per_token))
    return onset, mem_cap, (min(onset, mem_cap) if onset else mem_cap)


def run(name, n_frames, max_cache_gib):
    facts = models.get(name)
    ceiling = facts.context_ceiling_tokens
    budgets = sorted(set(max(256, ceiling // d) for d in (1, 2, 4, 8, 16)))
    print(f"\n=== {name} REAL KV-budget sweep (ceiling {ceiling}) ===")
    rows = []
    for b in budgets:
        onset, mem, cap = measure_onset(facts, b, n_frames, max_cache_gib)
        rows.append(dict(budget=b, frac=round(b/ceiling, 3), timing_onset=onset,
                         mem_cap=mem, capacity=cap))
        print(f"  budget={b:6d} ({b/ceiling:.3f} ceiling): timing_onset={onset} "
              f"mem_cap={mem} -> capacity={cap}")
    full_cap = next(r["capacity"] for r in rows if r["budget"] == max(budgets))
    small_cap = next(r["capacity"] for r in rows if r["budget"] == min(budgets))
    gain = small_cap / max(1, full_cap)
    cls = "complementary" if facts.self_windowing else "essential"
    os.makedirs(OUT, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ax.plot([r["frac"] for r in rows], [r["capacity"] for r in rows], "o-", color="#2ca02c")
    ax.set_xlabel("KV budget (fraction of context ceiling)")
    ax.set_ylabel("real capacity (sessions)")
    ax.set_title(f"{name}: REAL capacity vs KV budget ({cls}, {gain:.1f}x)")
    ax.invert_xaxis(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{name}_kvbudget.png"), dpi=120)
    plt.close(fig)
    res = dict(model=name, self_windowing=facts.self_windowing, rows=rows,
               full_capacity=full_cap, small_capacity=small_cap,
               kv_budget_gain=round(gain, 2), classification=cls)
    with open(os.path.join(OUT, f"{name}_kvbudget.json"), "w") as fh:
        json.dump(res, fh, indent=2)
    print(f"  REAL KV-budget gain: {gain:.2f}x -> {cls}")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=["moshi", "minicpm-o", "qwen3-omni"])
    ap.add_argument("--n-frames", type=int, default=12)
    ap.add_argument("--max-cache-gib", type=float, default=2.5)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    summ = {}
    for name in args.models:
        try:
            summ[name] = run(name, args.n_frames, args.max_cache_gib)
        except Exception as e:
            import traceback; traceback.print_exc(); print(f"[{name}] FAILED: {e}")
    with open(os.path.join(OUT, "engine_kv_summary.json"), "w") as fh:
        json.dump(summ, fh, indent=2)
    print("\n=== REAL KV-BUDGET (essential vs complementary) ===")
    for n, r in summ.items():
        print(f"  {n}: {r['classification']} ({r['kv_budget_gain']}x)")


if __name__ == "__main__":
    main()
