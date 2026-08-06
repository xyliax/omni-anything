"""Load-adaptive KV budgeting (docs/PRODUCTION.md H7).

A fixed KV budget forces a single point on the quality/capacity Pareto. An adaptive
controller sizes the resident window each frame so the *current* active batch fits
the frame budget: it tightens the window under load (serving more sessions at lower
quality) and loosens it as load drains (restoring quality). We compare, across
offered load:
  * fixed small budget  — high capacity, always-low quality
  * fixed large budget  — high quality, low capacity (sheds/blocks under load)
  * adaptive            — holds the SLO at high capacity AND keeps quality high when
                          load is light (traverses the Pareto with load).
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
from sim.open_system import OpenSystemSimulator, OpenConfig

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "adaptive")
SLO = 0.001


def cfg(name, **kw):
    f = models.get(name)
    cost = load_cost(name)
    ceiling = f.context_ceiling_tokens
    d = dict(cost=cost, facts=f, hbm_kv_bytes=hbm_kv_bytes(),
             kv_budget_tokens=ceiling, mean_holding_s=min(90.0, f.fill_time_s*0.5),
             eviction="sink_window", degradation=False, silence=False,
             admission=True, admission_mode="worst_case", seed=0)
    d.update(kw)
    return OpenConfig(**d)


def capacity(name, window):
    f = models.get(name); cost = load_cost(name)
    denom = cost.batch_per_session + cost.batch_alpha * window
    return max(4, int((f.period_s*1000*0.9 - cost.batch_base)/max(denom, 1e-9)))


def run(name, horizon_s=120.0):
    f = models.get(name)
    ceiling = f.context_ceiling_tokens
    small = max(256, ceiling // 16)
    large = ceiling // 2
    mean_hold = min(90.0, f.fill_time_s * 0.5)
    cap_small = capacity(name, small)
    loads_mult = (0.3, 0.6, 1.0, 1.5, 2.0)
    variants = {
        "fixed-small": dict(kv_budget_tokens=small, adaptive_budget=False),
        "fixed-large": dict(kv_budget_tokens=large, adaptive_budget=False),
        "adaptive": dict(kv_budget_tokens=large, adaptive_budget=True,
                         min_budget_tokens=small),
    }
    rows = {k: [] for k in variants}
    for mult in loads_mult:
        rate = (mult * cap_small) / mean_hold
        for vname, vkw in variants.items():
            r = OpenSystemSimulator(cfg(name, arrival_rate_hz=rate, **vkw)
                                    ).run(horizon_s, warmup_s=20.0)
            served = float(np.mean(r.per_frame_active)) if r.per_frame_active else 0
            rows[vname].append(dict(offered=mult*cap_small, served=served,
                                    miss=r.report.miss_rate, blocking=r.report.blocking,
                                    quality=r.report.mean_quality()))
        print(f"  [{name}] load~{mult:.1f}x: "
              + "  ".join(f"{v}: miss={rows[v][-1]['miss']:.3f} q={rows[v][-1]['quality']:.2f} "
                          f"served={rows[v][-1]['served']:.0f}" for v in variants))

    os.makedirs(OUT, exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    colors = {"fixed-small":"#1f77b4","fixed-large":"#d62728","adaptive":"#2ca02c"}
    for v in variants:
        off = [r["offered"] for r in rows[v]]
        ax1.plot(off, [r["quality"] for r in rows[v]], "o-", color=colors[v], label=v)
        ax2.plot(off, [max(r["miss"],1e-6) for r in rows[v]], "o-", color=colors[v], label=v)
    ax1.set_xlabel("offered load"); ax1.set_ylabel("mean retained quality"); ax1.set_title(f"{name}: quality vs load")
    ax1.legend(); ax1.grid(alpha=0.3)
    ax2.axhline(SLO, color="black", ls=":"); ax2.set_yscale("log")
    ax2.set_xlabel("offered load"); ax2.set_ylabel("miss rate"); ax2.set_title(f"{name}: SLO vs load")
    ax2.legend(); ax2.grid(alpha=0.3, which="both")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{name}_adaptive.png"), dpi=120)
    plt.close(fig)
    return dict(model=name, small=small, large=large, rows=rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=None)
    ap.add_argument("--horizon", type=float, default=120.0)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    names = args.models or all_models()
    out = {}
    for name in names:
        print(f"\n=== {name} adaptive budget ===")
        out[name] = run(name, args.horizon)
    with open(os.path.join(OUT, "adaptive_summary.json"), "w") as fh:
        json.dump(out, fh, indent=2)


if __name__ == "__main__":
    main()
