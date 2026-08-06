"""Open-system evaluation (docs/PRODUCTION.md H1, H2 + spike/recovery).

H1: under churn, admission holds the deadline-miss SLO at bounded blocking while
    throughput-greedy collapses to ~100% miss past capacity.
H2: with churn, the age-aware test sustainably serves more sessions than worst-case
    at the same SLO (the §4.2 tightening pays off when the age-mix stays young).
Spike/recovery: a flash crowd; admission sheds it (blocking) and recovers fast;
    greedy melts down.
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
from sim.open_system import OpenSystemSimulator, OpenConfig, recovery_time_s

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "open")
SLO = 0.001


def base_cfg(name, **kw):
    f = models.get(name)
    cost = load_cost(name)
    window = max(512, f.context_ceiling_tokens // 4)
    d = dict(cost=cost, facts=f, hbm_kv_bytes=hbm_kv_bytes(), kv_budget_tokens=window,
             mean_holding_s=min(90.0, f.fill_time_s * 0.5), holding_cv=1.5,
             eviction="sink_window", degradation=True, silence=True, seed=0)
    d.update(kw)
    return OpenConfig(**d)


def offered_load_sweep(name, horizon_s=120.0):
    """Sweep arrival rate (=> offered concurrent load via Little's law); compare
    Metronome admission vs throughput-greedy."""
    f = models.get(name)
    cost = load_cost(name)
    window = max(512, f.context_ceiling_tokens // 4)
    mean_hold = min(90.0, f.fill_time_s * 0.5)
    # rough capacity to scale the sweep
    denom = cost.batch_per_session + cost.batch_alpha * window
    cap = max(4, int((f.period_s*1000*0.9 - cost.batch_base)/max(denom, 1e-9)))
    # offered concurrent = rate*hold; sweep 0.3x .. 3x capacity
    rates = [(mult*cap)/mean_hold for mult in (0.3,0.5,0.7,0.9,1.1,1.5,2.0,2.5,3.0)]
    rows = []
    for rate in rates:
        offered = rate * mean_hold
        m = OpenSystemSimulator(base_cfg(name, arrival_rate_hz=rate, admission=True)
                                ).run(horizon_s, warmup_s=20.0)
        g = OpenSystemSimulator(base_cfg(name, arrival_rate_hz=rate, admission=False,
                                memory_admission=True, ordering="fifo", eviction="full",
                                degradation=False, silence=False)
                                ).run(horizon_s, warmup_s=20.0)
        rows.append(dict(offered=offered, rate=rate,
                         m_miss=m.report.miss_rate, m_block=m.report.blocking,
                         m_served=int(np.mean(m.per_frame_active) if m.per_frame_active else 0),
                         g_miss=g.report.miss_rate, g_block=g.report.blocking,
                         g_served=int(np.mean(g.per_frame_active) if g.per_frame_active else 0)))
        print(f"  [{name}] offered={offered:6.1f}  M: miss={m.report.miss_rate:.4f} "
              f"block={m.report.blocking:.2f}  GREEDY: miss={g.report.miss_rate:.4f}")
    return rows, cap


def fig_offered(name, rows):
    off = [r["offered"] for r in rows]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    ax1.plot(off, [max(r["g_miss"],1e-6) for r in rows], "o-", color="#d62728", label="greedy")
    ax1.plot(off, [max(r["m_miss"],1e-6) for r in rows], "o-", color="#2ca02c", label="Metronome")
    ax1.axhline(SLO, color="black", ls=":", label=f"SLO {SLO:.1%}")
    ax1.set_yscale("log"); ax1.set_xlabel("offered load (concurrent sessions)")
    ax1.set_ylabel("deadline-miss rate"); ax1.set_title(f"{name}: miss vs offered load")
    ax1.legend(); ax1.grid(alpha=0.3, which="both")
    ax2.plot(off, [r["m_block"] for r in rows], "o-", color="#2ca02c", label="Metronome blocking")
    ax2.set_xlabel("offered load (concurrent sessions)"); ax2.set_ylabel("blocking probability")
    ax2.set_title(f"{name}: admission blocking (graceful)"); ax2.legend(); ax2.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{name}_offered_load.png"), dpi=120)
    plt.close(fig)


def age_aware_vs_worst(name, horizon_s=120.0):
    """At a fixed moderate-overload load, compare worst-case vs age-aware admission:
    age-aware should serve more (higher admitted concurrency) while holding the SLO."""
    f = models.get(name)
    window = max(512, f.context_ceiling_tokens // 4)
    mean_hold = min(90.0, f.fill_time_s * 0.5)
    cost = load_cost(name)
    denom = cost.batch_per_session + cost.batch_alpha * window
    cap = max(4, int((f.period_s*1000*0.9 - cost.batch_base)/max(denom, 1e-9)))
    rate = (2.0 * cap) / mean_hold      # 2x overload so admission binds
    # operating age that churn sustains ~ mean residual age; use fill-to-budget*0.5
    a_char = (window / (f.tokens_per_tick/f.period_s)) * 0.5

    wc = OpenSystemSimulator(base_cfg(name, arrival_rate_hz=rate, admission=True,
                             admission_mode="worst_case")).run(horizon_s, warmup_s=20.0)
    aa = OpenSystemSimulator(base_cfg(name, arrival_rate_hz=rate, admission=True,
                             admission_mode="age_aware", assumed_age_s=a_char)
                             ).run(horizon_s, warmup_s=20.0)
    res = dict(model=name,
               wc_served=float(np.mean(wc.per_frame_active)) if wc.per_frame_active else 0,
               wc_miss=wc.report.miss_rate, wc_block=wc.report.blocking,
               aa_served=float(np.mean(aa.per_frame_active)) if aa.per_frame_active else 0,
               aa_miss=aa.report.miss_rate, aa_block=aa.report.blocking,
               aa_quality=aa.report.mean_quality())
    res["served_gain"] = round(res["aa_served"]/max(1e-9, res["wc_served"]), 2)
    return res


def spike_recovery(name, horizon_s=120.0):
    f = models.get(name)
    cost = load_cost(name)
    window = max(512, f.context_ceiling_tokens // 4)
    mean_hold = min(90.0, f.fill_time_s * 0.5)
    denom = cost.batch_per_session + cost.batch_alpha * window
    cap = max(4, int((f.period_s*1000*0.9 - cost.batch_base)/max(denom, 1e-9)))
    base_rate = (0.85 * cap) / mean_hold      # near capacity so a spike bites
    spike_start, spike_end = horizon_s*0.4, horizon_s*0.55

    def rate_fn(t):
        return base_rate * (10.0 if spike_start <= t < spike_end else 1.0)

    out = {}
    for label, kw in (("Metronome", dict(admission=True)),
                      ("greedy", dict(admission=False, memory_admission=True,
                                      ordering="fifo", eviction="full",
                                      degradation=False, silence=False))):
        r = OpenSystemSimulator(base_cfg(name, arrival_rate_hz=base_rate, **kw)
                                ).run(horizon_s, rate_fn, warmup_s=10.0)
        rec = recovery_time_s(r.per_frame_miss, f.period_s, SLO)
        out[label] = dict(series=r.per_frame_miss, recovery_s=rec,
                          peak_miss=float(np.max(r.per_frame_miss)) if r.per_frame_miss else 0,
                          blocking=r.report.blocking)
    # plot
    fig, ax = plt.subplots(figsize=(7, 4))
    for label, c in (("greedy","#d62728"),("Metronome","#2ca02c")):
        s = out[label]["series"]
        ts = np.arange(len(s)) * f.period_s
        ax.plot(ts, np.maximum(s,1e-6), color=c, label=f"{label} (recover {out[label]['recovery_s']:.1f}s)")
    ax.axhline(SLO, color="black", ls=":", label=f"SLO {SLO:.1%}")
    ax.axvspan(spike_start-10, spike_end-10, color="orange", alpha=0.15, label="spike (8x)")
    ax.set_yscale("log"); ax.set_xlabel("time (s)"); ax.set_ylabel("miss rate")
    ax.set_title(f"{name}: flash-crowd spike & recovery"); ax.legend(fontsize=8); ax.grid(alpha=0.3, which="both")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{name}_spike.png"), dpi=120)
    plt.close(fig)
    return {k: {kk: vv for kk, vv in v.items() if kk != "series"} for k, v in out.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=None)
    ap.add_argument("--horizon", type=float, default=120.0)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    names = args.models or all_models()
    summary = {}
    for name in names:
        print(f"\n=== {name} open-system ===")
        rows, cap = offered_load_sweep(name, args.horizon)
        fig_offered(name, rows)
        aa = age_aware_vs_worst(name, args.horizon)
        sp = spike_recovery(name, args.horizon)
        summary[name] = dict(capacity=cap, offered_sweep=rows, age_aware=aa, spike=sp)
        print(f"  [{name}] age-aware served {aa['aa_served']:.0f} (miss {aa['aa_miss']:.4f}) "
              f"vs worst-case {aa['wc_served']:.0f} (miss {aa['wc_miss']:.4f}) "
              f"-> {aa['served_gain']}x")
        print(f"  [{name}] spike recovery: Metronome {sp['Metronome']['recovery_s']:.1f}s "
              f"(peak {sp['Metronome']['peak_miss']:.3f}) vs greedy "
              f"{sp['greedy']['recovery_s']:.1f}s (peak {sp['greedy']['peak_miss']:.3f})")
    with open(os.path.join(OUT, "open_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)


if __name__ == "__main__":
    main()
