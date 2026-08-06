"""Hardware sensitivity (RESEARCH_PLAN §6.7): project MSCS across accelerators.

The KV-read cost α (and the shared weight-read base) are HBM-bandwidth-bound, so we
rescale the *measured* cost model to other accelerators' bandwidths and recompute
MSCS for B1 (greedy) and M (Metronome). The point: the capacity *gain* from
frame-budget scheduling + KV budgeting holds across hardware; absolute MSCS scales
with bandwidth.

Bandwidths (HBM peak, GiB/s): A100-80GB ~2039, H100-SXM ~3352, GH200 ~4915,
plus the measured RTX PRO 6000 Blackwell effective bandwidth.
"""
from __future__ import annotations

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
from bench.metrics import mscs_served

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "hardware")
TARGET_MISS = 0.001
HW = {"A100": 2039.0, "H100": 3352.0, "GH200": 4915.0}


def mscs_for(cost, facts, preset, n_frames=200):
    hbm = hbm_kv_bytes()
    ceiling = facts.context_ceiling_tokens
    window = max(512, ceiling // 4)
    ns = [1,2,4,8,16,24,32,48,64,96,128,192,256,384,512,768,1024,1536,2048]
    curve = []
    for n in ns:
        if preset == "B1":
            cfg = SimConfig(cost=cost, frame_budget_s=facts.period_s, hbm_kv_bytes=hbm,
                            admission=False, memory_admission=True, ordering="fifo",
                            eviction="full", degradation=False, silence=False)
            growth = ceiling
        else:  # M
            cfg = SimConfig(cost=cost, frame_budget_s=facts.period_s, hbm_kv_bytes=hbm,
                            admission=True, ordering="edf", eviction="sink_window",
                            degradation=False, silence=False, kv_budget_tokens=window)
            growth = window
        wl = WorkloadConfig(facts=facts, kv_budget_tokens=growth,
                            mean_session_s=facts.fill_time_s*0.6, seed=0)
        r = Simulator(cfg).run_static(make_population(wl, n), n_frames)
        curve.append((n, r.admitted, r.metrics.miss_rate))
    return mscs_served(curve, TARGET_MISS)


def run():
    os.makedirs(OUT, exist_ok=True)
    out = {}
    for name in all_models():
        facts = models.get(name)
        base_cost = load_cost(name)
        measured_bw = base_cost.implied_bandwidth_gibs
        hw = {"measured": measured_bw, **HW}
        rows = {}
        for label, bw in hw.items():
            cost = base_cost if label == "measured" else base_cost.rescale_to_bandwidth(bw)
            b1 = mscs_for(cost, facts, "B1")
            m = mscs_for(cost, facts, "M")
            rows[label] = dict(bw=round(bw, 0), B1=b1, M=m, gain=round(m/max(1,b1), 2))
        out[name] = rows

    with open(os.path.join(OUT, "hardware_sensitivity.json"), "w") as fh:
        json.dump(out, fh, indent=2)

    # plot MSCS(M) vs bandwidth per model
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    colors = {"moshi": "#1f77b4", "minicpm-o": "#ff7f0e", "qwen3-omni": "#2ca02c"}
    for name, rows in out.items():
        order = sorted(rows.values(), key=lambda r: r["bw"])
        ax.plot([r["bw"] for r in order], [r["M"] for r in order], "o-",
                color=colors.get(name), label=f"{name} (M)")
        ax.plot([r["bw"] for r in order], [r["B1"] for r in order], "s--",
                color=colors.get(name), alpha=0.5, label=f"{name} (B1)")
    ax.set_xlabel("HBM bandwidth (GiB/s)"); ax.set_ylabel("MSCS @ 0.1% miss")
    ax.set_title("MSCS scales with bandwidth; M>B1 gain holds across hardware")
    ax.legend(fontsize=7, ncol=3); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "hardware_sensitivity.png"), dpi=120)
    plt.close(fig)

    print("=== Hardware sensitivity (MSCS @ 0.1% miss) ===")
    for name, rows in out.items():
        print(f"  {name}:")
        for label, r in rows.items():
            print(f"    {label:9s} {r['bw']:6.0f} GiB/s  B1={r['B1']:5d}  M={r['M']:5d}  "
                  f"gain={r['gain']}x")
    return out


if __name__ == "__main__":
    run()
