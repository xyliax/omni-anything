"""S5: core evaluation — B0/B1/B2/M on MSCS, jitter, latency-vs-age, $/session-hour.

Produces the §6.6 headline plots:
  1. per-tick latency vs session age  (M flat vs B1 climbing) — the money plot.
  2. MSCS vs deadline-miss rate         (M vs B0/B1/B2).
  3. $/session-hour at fixed SLO         (cost table + bar).
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

from experiments._common import load_cost, hbm_kv_bytes, all_models
from metronome import models
from sim.simulator import Simulator, SimConfig
from bench.generator import WorkloadConfig, make_population
from bench.metrics import mscs, mscs_served, CostModelDollars

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "core")
TARGET_MISS = 0.001
PRESETS = ["B0", "B1", "B2", "M"]
COLORS = {"B0": "#7f7f7f", "B1": "#d62728", "B2": "#9467bd", "M": "#2ca02c"}


def cfg_for(name, cost, facts, ceiling, window, hbm):
    base = dict(cost=cost, frame_budget_s=facts.period_s, hbm_kv_bytes=hbm)
    if name == "B0":
        return SimConfig(**base, admission=False, memory_admission=False,
                         ordering="fifo", eviction="full",
                         degradation=False, silence=False, reprefill=True), ceiling
    if name == "B1":
        return SimConfig(**base, admission=False, memory_admission=True,
                         ordering="fifo", eviction="full",
                         degradation=False, silence=False), ceiling
    if name == "B2":
        return SimConfig(**base, admission=False, memory_admission=True,
                         ordering="edf", eviction="full",
                         degradation=False, silence=False), ceiling
    if name == "M":
        return SimConfig(**base, admission=True, ordering="edf", eviction="sink_window",
                         degradation=True, silence=False, kv_budget_tokens=window), window
    raise ValueError(name)


def mscs_curve(name, cost, facts, ceiling, window, hbm, n_max, n_frames):
    ns = [n for n in (1,2,4,6,8,12,16,24,32,48,64,96,128,192,256,384,512,768,1024)
          if n <= n_max]
    out = []
    for n in ns:
        cfg, growth = cfg_for(name, cost, facts, ceiling, window, hbm)
        wl = WorkloadConfig(facts=facts, kv_budget_tokens=growth,
                            mean_session_s=facts.fill_time_s*0.6, seed=0)
        pop = make_population(wl, n)
        r = Simulator(cfg).run_static(pop, n_frames)
        out.append((n, r.metrics.miss_rate, r.metrics.p99, r.metrics.p999,
                    r.admitted, r.metrics.quality_retained))
    return out


def fig_latency_vs_age(name, cost, facts, window):
    """Headline plot 1: per-tick latency over a session's life, B1 vs M, at a
    realistic shared concurrency N near M's windowed capacity — so B1 (full KV)
    climbs across the deadline while M (windowed) stays flat under it."""
    rate = facts.tokens_per_tick / facts.period_s
    budget = facts.period_s * 1000.0
    # N = sessions that fit under budget at the windowed plateau (M's operating point)
    denom = cost.batch_per_session + cost.batch_alpha * window
    N = max(2, int((budget * 0.9 - cost.batch_base) / max(denom, 1e-9)))
    ages = np.linspace(0, facts.fill_time_s, 120)
    L_full = np.minimum(rate * ages, facts.context_ceiling_tokens)
    L_win = np.minimum(rate * ages, window)
    B = N
    b1 = [cost.predict_batch([int(l)] * B) for l in L_full]
    m = [cost.predict_batch([int(l)] * B) for l in L_win]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(ages, b1, "-", color=COLORS["B1"], lw=2, label="B1 (full KV) — climbs")
    ax.plot(ages, m, "-", color=COLORS["M"], lw=2, label="M (windowed) — flat")
    ax.axhline(budget, color="black", ls=":", lw=1.5, label=f"frame budget {budget:.0f} ms")
    ax.set_xlabel("session age (s)")
    ax.set_ylabel(f"per-tick latency (ms, N={B} sessions)")
    ax.set_title(f"{name}: per-tick latency vs age (bounded WCET = flat)")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{name}_latency_vs_age.png"), dpi=120)
    plt.close(fig)


def fig_mscs(name, curves):
    fig, ax = plt.subplots(figsize=(6, 4))
    mscs_vals = {}
    for p in PRESETS:
        c = curves[p]
        ax.plot([x[0] for x in c], [max(x[1], 1e-6) for x in c], "o-",
                color=COLORS[p], label=p, ms=4)
        mscs_vals[p] = mscs_served([(x[0], x[4], x[1]) for x in c], TARGET_MISS)
    ax.axhline(TARGET_MISS, color="black", ls=":", label=f"SLO {TARGET_MISS:.1%}")
    ax.set_yscale("log"); ax.set_xscale("log")
    ax.set_xlabel("concurrent sessions"); ax.set_ylabel("deadline-miss rate")
    ax.set_title(f"{name}: deadline-miss rate vs concurrency")
    ax.legend(); ax.grid(alpha=0.3, which="both")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{name}_mscs.png"), dpi=120)
    plt.close(fig)
    return mscs_vals


def run(name, n_max, n_frames, dollars_per_hr):
    facts = models.get(name)
    cost = load_cost(name)
    ceiling = facts.context_ceiling_tokens
    window = max(512, ceiling // 4)
    hbm = hbm_kv_bytes()
    os.makedirs(OUT, exist_ok=True)

    curves = {p: mscs_curve(p, cost, facts, ceiling, window, hbm, n_max, n_frames)
              for p in PRESETS}
    fig_latency_vs_age(name, cost, facts, window)
    mscs_vals = fig_mscs(name, curves)

    dollars = CostModelDollars(dollars_per_hr)
    cost_rows = {p: dollars.per_session_hour(mscs_vals[p]) for p in PRESETS}

    with open(os.path.join(OUT, f"{name}_curves.json"), "w") as fh:
        json.dump({p: [list(map(float, x)) for x in curves[p]] for p in PRESETS},
                  fh, indent=2)

    print(f"\n[{name}] MSCS @ {TARGET_MISS:.1%}: "
          + "  ".join(f"{p}={mscs_vals[p]}" for p in PRESETS))
    print(f"[{name}] $/session-hr: "
          + "  ".join(f"{p}=${cost_rows[p]:.4f}" for p in PRESETS))
    gain = mscs_vals["M"] / max(1, mscs_vals["B1"])
    print(f"[{name}] M/B1 MSCS gain: {gain:.2f}x")
    return dict(model=name, mscs=mscs_vals, dollars=cost_rows, gain=gain)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=None)
    ap.add_argument("--n-max", type=int, default=1024)
    ap.add_argument("--n-frames", type=int, default=300)
    ap.add_argument("--dollars-per-hr", type=float, default=2.0)
    args = ap.parse_args()
    names = args.models or all_models()
    summary = []
    for name in names:
        summary.append(run(name, args.n_max, args.n_frames, args.dollars_per_hr))
    with open(os.path.join(OUT, "core_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)
    print("\n=== CORE EVAL summary ===")
    for s in summary:
        print(f"  {s['model']}: MSCS B1={s['mscs']['B1']} -> M={s['mscs']['M']} "
              f"({s['gain']:.2f}x)")


if __name__ == "__main__":
    main()
