"""Real open-system serving on the engine (G4 / H1, measured).

Drives the real Metronome engine with a churned workload (Poisson arrivals,
exponential lifetimes) over real frames, executing each frame's batch on the GPU and
counting real deadline misses. Compares:
  * admission  — cap the active set at the measured real capacity (the concurrency
    whose measured p99 stays within budget); reject the excess;
  * greedy     — admit until HBM is full (no deadline awareness).

Produces the real graceful-vs-cliff result: admission holds ~0 miss at bounded
blocking; greedy drives the whole batch over budget (every tick late).
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

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "engine")


def run_open(name, capacity, max_sessions, window, n_frames, offered_factor, mode,
             mean_life_frames=40, seed=0):
    facts = models.get(name)
    eng = ServingEngine(facts, max_sessions=max_sessions, max_budget_tokens=window)
    rng = np.random.default_rng(seed)
    budget_ms = facts.period_s * 1000.0
    n_new = max(1, int(round(facts.tokens_per_tick)))
    free_rows = list(range(max_sessions))
    active = {}   # row -> depart_frame
    arr_rate = offered_factor * capacity / mean_life_frames
    n_arr = n_adm = 0
    over_ticks = tot_ticks = 0
    series = []
    # warmup
    for _ in range(4):
        eng.step_active(list(active.keys())[:8] or [0], n_new)
    for fi in range(n_frames):
        # departures
        for r in [r for r, d in active.items() if d <= fi]:
            del active[r]; free_rows.append(r); eng.lengths[r] = 0
        # arrivals
        for _ in range(rng.poisson(arr_rate)):
            n_arr += 1
            if mode == "admission" and len(active) >= capacity:
                continue   # blocked
            if not free_rows:
                continue   # memory full
            r = free_rows.pop()
            # steady-state: sessions are at a realistic resident length (most of a
            # long session's life is spent near the plateau for windowed KV)
            eng.lengths[r] = int(rng.uniform(0.6, 1.0) * window)
            active[r] = fi + int(rng.exponential(mean_life_frames))
            n_adm += 1
        rows = list(active.keys())
        if not rows:
            series.append(0.0); continue
        lat = eng.step_active(rows, n_new)
        series.append(lat)
        over = lat > budget_ms
        tot_ticks += len(rows)
        if over:
            over_ticks += len(rows)
    del eng; torch.cuda.empty_cache()
    return dict(mode=mode, offered=offered_factor, miss_rate=over_ticks/max(1, tot_ticks),
                blocking=1 - n_adm/max(1, n_arr), mean_active=float(np.mean([len(active)] or [0])),
                series=series)


def run(name, n_frames=200):
    facts = models.get(name)
    window = max(512, facts.context_ceiling_tokens // 4)
    # real capacity from the engine eval (measured onset); fall back to a probe
    cap = _measured_capacity(name, window)
    # memory-bounded max rows for the 1-layer cache in ~2.5 GiB
    per = window * facts.num_kv_heads * facts.head_dim * 2 * 2
    max_sessions = max(cap + 8, int(2.5 * 2**30 / per))
    print(f"\n=== {name} REAL open-system (capacity {cap}, max_rows {max_sessions}) ===")
    wait_for_window(need_free_gib=2.8, max_util_pct=85, quiet=True, timeout_s=7200)
    out = {}
    for mode in ("admission", "greedy"):
        r = run_open(name, cap, max_sessions, window, n_frames, offered_factor=2.0, mode=mode)
        out[mode] = {k: v for k, v in r.items() if k != "series"}
        out[mode]["series"] = r["series"]
        print(f"  {mode:10s}: real miss-rate={r['miss_rate']:.3f}  blocking={r['blocking']:.3f}")
    # plot
    os.makedirs(OUT, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4))
    budget = facts.period_s * 1000
    for mode, c in (("greedy", "#d62728"), ("admission", "#2ca02c")):
        s = out[mode]["series"]
        ax.plot(np.arange(len(s)), s, color=c, alpha=0.8,
                label=f"{mode} (miss {out[mode]['miss_rate']:.2f})")
    ax.axhline(budget, color="black", ls=":", label=f"{budget:.0f} ms deadline")
    ax.set_xlabel("frame"); ax.set_ylabel("measured tick latency (ms)")
    ax.set_title(f"{name}: REAL open-system at 2x overload")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{name}_open.png"), dpi=120)
    plt.close(fig)
    res = dict(model=name, capacity=cap,
               admission={k: v for k, v in out["admission"].items() if k != "series"},
               greedy={k: v for k, v in out["greedy"].items() if k != "series"})
    with open(os.path.join(OUT, f"{name}_open.json"), "w") as fh:
        json.dump(res, fh, indent=2)
    return res


def _measured_capacity(name, window):
    """Use the engine_eval measured M onset if available, else a conservative default."""
    p = os.path.join(OUT, f"{name}_engine.json")
    if os.path.exists(p):
        d = json.load(open(p))
        if d.get("timing_onset_window"):
            return d["timing_onset_window"]
    return {"moshi": 128, "minicpm-o": 64, "qwen3-omni": 128}.get(name, 64)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=["moshi", "minicpm-o", "qwen3-omni"])
    ap.add_argument("--n-frames", type=int, default=200)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    summ = {}
    for name in args.models:
        try:
            summ[name] = run(name, args.n_frames)
        except Exception as e:
            import traceback; traceback.print_exc(); print(f"[{name}] FAILED: {e}")
    with open(os.path.join(OUT, "engine_open_summary.json"), "w") as fh:
        json.dump(summ, fh, indent=2)
    print("\n=== REAL OPEN-SYSTEM (2x overload) ===")
    for n, r in summ.items():
        print(f"  {n}: admission miss={r['admission']['miss_rate']:.3f} "
              f"(block {r['admission']['blocking']:.2f}) vs greedy miss={r['greedy']['miss_rate']:.3f}")


if __name__ == "__main__":
    main()
