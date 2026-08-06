"""Admission control: predicted-vs-measured capacity (G5) and graceful-vs-cliff
behaviour under overload (G1/G4).

(1) PREDICTED vs MEASURED: the worst-case (plateau) admission test predicts a
    capacity from the cost model + hardware specs alone. We compare it to the
    measured oracle MSCS from the simulator. A safe test predicts <= measured; a
    good test predicts close to it. We also report the tighter age-aware test.

(2) GRACEFUL vs CLIFF: under increasing OFFERED load (past capacity), a system
    WITHOUT admission (throughput-greedy) drives every session's miss-rate up — a
    cliff; WITH admission, the served (admitted) sessions keep ~0 miss and the
    excess is rejected — graceful. This is admission's real value (it is invisible
    to an oracle MSCS, which already finds the feasible frontier for any system).
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
from metronome.session import PeriodicSession
from sim.simulator import Simulator, SimConfig
from bench.generator import WorkloadConfig, make_population
from bench.metrics import mscs, mscs_served

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "admission")
TARGET_MISS = 0.001


def proto_session(facts, budget, length=0):
    return PeriodicSession(sid=0, facts=facts, period_s=facts.period_s,
                           deadline_s=facts.period_s, phase_s=0.0,
                           kv_budget_tokens=budget,
                           token_rate=facts.tokens_per_tick/facts.period_s,
                           length_tokens=length)


def measured_capacity(cost, facts, budget, n_max=1024, n_frames=250):
    hbm = hbm_kv_bytes()
    ns = [n for n in (1,2,4,8,16,24,32,48,64,96,128,160,192,256,384,512,768,1024)
          if n <= n_max]
    curve = []
    for n in ns:
        cfg = SimConfig(cost=cost, frame_budget_s=facts.period_s, hbm_kv_bytes=hbm,
                        admission=False, memory_admission=True, ordering="edf",
                        eviction="sink_window", degradation=False, silence=False,
                        kv_budget_tokens=budget)
        wl = WorkloadConfig(facts=facts, kv_budget_tokens=budget,
                            mean_session_s=facts.fill_time_s*0.6, seed=0)
        r = Simulator(cfg).run_static(make_population(wl, n), n_frames)
        curve.append((n, r.admitted, r.metrics.miss_rate))
    return mscs_served(curve, TARGET_MISS)


def predicted_vs_measured(name):
    facts = models.get(name)
    cost = load_cost(name)
    hbm = hbm_kv_bytes()
    budget = max(512, facts.context_ceiling_tokens // 4)
    proto = proto_session(facts, budget)

    wc = AdmissionController(cost, AdmissionConfig(hbm, facts.period_s, 0.90,
                                                  mode="worst_case"))
    pred_wc = wc.predict_capacity(proto)
    # age-aware with a characteristic operating age = 0.6 * fill-to-budget time
    a_char = (budget / (facts.tokens_per_tick/facts.period_s)) * 0.6
    aa = AdmissionController(cost, AdmissionConfig(hbm, facts.period_s, 0.90,
                                                  mode="age_aware", assumed_age_s=a_char))
    pred_aa = aa.predict_capacity(proto)
    meas = measured_capacity(cost, facts, budget)
    return dict(model=name, budget=budget, predicted_worst_case=pred_wc,
                predicted_age_aware=pred_aa, measured=meas,
                wc_safe=pred_wc <= meas,
                wc_rel_err=round(abs(pred_wc-meas)/max(meas,1), 3),
                aa_rel_err=round(abs(pred_aa-meas)/max(meas,1), 3))


def graceful_vs_cliff(name):
    facts = models.get(name)
    cost = load_cost(name)
    hbm = hbm_kv_bytes()
    budget = max(512, facts.context_ceiling_tokens // 4)
    cap = measured_capacity(cost, facts, budget)
    offered = sorted(set(int(x) for x in np.linspace(1, max(4, cap*3), 22)))
    with_adm, without_adm = [], []
    for n in offered:
        wl = WorkloadConfig(facts=facts, kv_budget_tokens=budget,
                            mean_session_s=facts.fill_time_s*0.6, seed=0)
        # with admission (Metronome)
        cfg_a = SimConfig(cost=cost, frame_budget_s=facts.period_s, hbm_kv_bytes=hbm,
                          admission=True, ordering="edf", eviction="sink_window",
                          degradation=False, silence=False, kv_budget_tokens=budget)
        ra = Simulator(cfg_a).run_static(make_population(wl, n), 200)
        # without admission (throughput-greedy, memory-only)
        cfg_b = SimConfig(cost=cost, frame_budget_s=facts.period_s, hbm_kv_bytes=hbm,
                          admission=False, memory_admission=True, ordering="fifo",
                          eviction="sink_window", degradation=False, silence=False,
                          kv_budget_tokens=budget)
        rb = Simulator(cfg_b).run_static(make_population(wl, n), 200)
        with_adm.append((n, ra.admitted, ra.metrics.miss_rate))
        without_adm.append((n, rb.admitted, rb.metrics.miss_rate))

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot([x[0] for x in without_adm], [max(x[2],1e-6) for x in without_adm],
            "o-", color="#d62728", label="no admission (greedy)")
    ax.plot([x[0] for x in with_adm], [max(x[2],1e-6) for x in with_adm],
            "o-", color="#2ca02c", label="Metronome admission")
    ax.axhline(TARGET_MISS, color="black", ls=":", label=f"SLO {TARGET_MISS:.1%}")
    ax.axvline(cap, color="gray", ls="--", alpha=0.6, label=f"capacity≈{cap}")
    ax.set_yscale("log")
    ax.set_xlabel("offered sessions"); ax.set_ylabel("deadline-miss rate")
    ax.set_title(f"{name}: admission = graceful; greedy = cliff")
    ax.legend(fontsize=8); ax.grid(alpha=0.3, which="both")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{name}_graceful.png"), dpi=120)
    plt.close(fig)

    # miss-rate at 2x overload
    idx = min(range(len(offered)), key=lambda i: abs(offered[i] - 2*cap))
    return dict(model=name, capacity=cap, overload_offered=offered[idx],
                miss_no_admission=without_adm[idx][2],
                miss_with_admission=with_adm[idx][2],
                admitted_with_admission=with_adm[idx][1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=None)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    names = args.models or all_models()

    pvm = [predicted_vs_measured(n) for n in names]
    cliff = [graceful_vs_cliff(n) for n in names]

    # predicted-vs-measured scatter
    fig, ax = plt.subplots(figsize=(5.5, 5))
    meas = [p["measured"] for p in pvm]
    pwc = [p["predicted_worst_case"] for p in pvm]
    paa = [p["predicted_age_aware"] for p in pvm]
    lim = max(max(meas), max(pwc), max(paa)) * 1.15
    ax.plot([0, lim], [0, lim], "k:", label="ideal")
    ax.scatter(meas, pwc, c="#1f77b4", label="worst-case (safe)", zorder=3)
    ax.scatter(meas, paa, c="#ff7f0e", marker="s", label="age-aware (tight)", zorder=3)
    for p in pvm:
        ax.annotate(p["model"], (p["measured"], p["predicted_worst_case"]),
                    fontsize=7, xytext=(3,3), textcoords="offset points")
    ax.set_xlabel("measured MSCS (oracle)"); ax.set_ylabel("predicted capacity")
    ax.set_title("Admission test: predicted vs measured (G5)")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "predicted_vs_measured.png"), dpi=120)
    plt.close(fig)

    with open(os.path.join(OUT, "admission_summary.json"), "w") as fh:
        json.dump(dict(predicted_vs_measured=pvm, graceful_vs_cliff=cliff), fh, indent=2)

    print("=== Predicted vs measured capacity (G5) ===")
    for p in pvm:
        print(f"  {p['model']:12s} measured={p['measured']:4d}  "
              f"worst-case={p['predicted_worst_case']:4d} (safe={p['wc_safe']}, "
              f"err={p['wc_rel_err']:.2f})  age-aware={p['predicted_age_aware']:4d} "
              f"(err={p['aa_rel_err']:.2f})")
    print("\n=== Graceful vs cliff (at ~2x overload) ===")
    for c in cliff:
        print(f"  {c['model']:12s} cap={c['capacity']:4d}  @{c['overload_offered']} offered: "
              f"miss no-adm={c['miss_no_admission']:.4f}  with-adm={c['miss_with_admission']:.4f} "
              f"(served {c['admitted_with_admission']})")


if __name__ == "__main__":
    main()
