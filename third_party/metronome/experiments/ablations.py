"""S8: ablations — isolate each Metronome component's contribution.

For each knob we toggle it against the full system and report MSCS @ SLO:
  * admission control on/off
  * EDF vs FIFO vs LRF (ordering)
  * KV budget: full vs budgeted; fixed vs adaptive
  * degradation ladder on/off
  * silence exploitation on/off (talk_ratio < 1)
  * admission test: worst-case (plateau) vs age-aware
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
from metronome.admission import AdmissionController, AdmissionConfig
from sim.simulator import Simulator, SimConfig
from bench.generator import WorkloadConfig, make_population
from bench.metrics import mscs, mscs_served

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "ablation")
TARGET_MISS = 0.001


def measure_mscs(cost, facts, n_max, n_frames, talk_ratio=1.0, **simkw):
    hbm = hbm_kv_bytes()
    window = max(512, facts.context_ceiling_tokens // 4)
    growth = simkw.pop("growth", facts.context_ceiling_tokens)
    ns = [n for n in (1,2,4,8,16,32,64,128,256,512,768,1024,1536,2048) if n <= n_max]
    curve = []
    for n in ns:
        cfg = SimConfig(cost=cost, frame_budget_s=facts.period_s, hbm_kv_bytes=hbm,
                        **simkw)
        wl = WorkloadConfig(facts=facts, kv_budget_tokens=growth,
                            mean_session_s=facts.fill_time_s*0.6,
                            talk_ratio=talk_ratio, seed=0)
        pop = make_population(wl, n)
        r = Simulator(cfg).run_static(pop, n_frames)
        curve.append((n, r.admitted, r.metrics.miss_rate))
    return mscs_served(curve, TARGET_MISS)


def run(name, n_max, n_frames):
    facts = models.get(name)
    cost = load_cost(name)
    window = max(512, facts.context_ceiling_tokens // 4)
    os.makedirs(OUT, exist_ok=True)

    # Base = pure scheduling (admission + EDF + KV budget + age-aware), degradation
    # OFF so each knob's effect on *feasibility* is visible rather than absorbed by
    # the degradation safety net (which converts misses into quality loss).
    M = dict(admission=True, ordering="edf", eviction="sink_window",
             degradation=False, silence=False, kv_budget_tokens=window,
             admission_mode="age_aware", growth=window)

    ablations = {
        "M-core (sched only)": dict(M),
        "− admission (mem-only)": {**M, "admission": False},
        "FIFO (− EDF)": {**M, "ordering": "fifo"},
        "LRF order (anti-EDF)": {**M, "ordering": "lrf"},
        "full KV (− budget)": {**M, "eviction": "full", "kv_budget_tokens": 0,
                                "growth": facts.context_ceiling_tokens},
        "+ degradation ladder": {**M, "degradation": True},
        "worst-case admit": {**M, "admission_mode": "worst_case"},
    }
    results = {}
    for label, kw in ablations.items():
        results[label] = measure_mscs(cost, facts, n_max, n_frames, **kw)

    # silence exploitation: only meaningful with talk_ratio<1 (no-speak ticks)
    results["+ silence (talk .5)"] = measure_mscs(
        cost, facts, n_max, n_frames, talk_ratio=0.5, **{**M, "silence": True})
    results["− silence (talk .5)"] = measure_mscs(
        cost, facts, n_max, n_frames, talk_ratio=0.5, **{**M, "silence": False})

    with open(os.path.join(OUT, f"{name}_ablation.json"), "w") as fh:
        json.dump(results, fh, indent=2)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    labels = list(results.keys())
    vals = [results[l] for l in labels]
    base = results["M-core (sched only)"]
    cols = ["#2ca02c" if l == "M-core (sched only)" else "#d62728" if results[l] < base
            else "#1f77b4" for l in labels]
    ax.barh(labels, vals, color=cols)
    ax.axvline(base, color="black", ls=":", label="M-core")
    ax.set_xlabel(f"MSCS @ {TARGET_MISS:.1%}")
    ax.set_title(f"{name}: ablations (each knob vs full Metronome)")
    ax.invert_yaxis(); ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{name}_ablation.png"), dpi=120)
    plt.close(fig)

    print(f"\n[{name}] ablations (MSCS @ {TARGET_MISS:.1%}):")
    for l in labels:
        print(f"    {l:24s} {results[l]:6d}  ({results[l]/max(1,base):.2f}x)")
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=None)
    ap.add_argument("--n-max", type=int, default=2048)
    ap.add_argument("--n-frames", type=int, default=250)
    args = ap.parse_args()
    names = args.models or all_models()
    allr = {}
    for name in names:
        allr[name] = run(name, args.n_max, args.n_frames)
    with open(os.path.join(OUT, "ablation_summary.json"), "w") as fh:
        json.dump(allr, fh, indent=2)


if __name__ == "__main__":
    main()
