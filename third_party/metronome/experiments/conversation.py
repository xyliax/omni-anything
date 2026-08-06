"""Realistic conversation dynamics + production metrics (docs/PRODUCTION.md H4, H5).

H4: silence exploitation's goodput gain grows with realistic turn-taking silence
    (a session at the no-speak state defers its tick, freeing compute), and is
    robust to a bounded adversarial synchronized-talk burst.
H5: at a matched offered load, consecutive-miss runs are SHORT under Metronome but
    LONG under throughput-greedy (same aggregate miss can sound very different).

Turn-taking is a 2-state Markov chain (talk/silence) with realistic dwell times.
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
from bench.metrics import consecutive_run_lengths

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "conversation")
SLO = 0.001


def cfg(name, **kw):
    f = models.get(name)
    cost = load_cost(name)
    window = max(512, f.context_ceiling_tokens // 4)
    d = dict(cost=cost, facts=f, hbm_kv_bytes=hbm_kv_bytes(), kv_budget_tokens=window,
             mean_holding_s=min(90.0, f.fill_time_s * 0.5), eviction="sink_window",
             degradation=True, seed=0)
    d.update(kw)
    return OpenConfig(**d)


def capacity(name, window):
    f = models.get(name); cost = load_cost(name)
    denom = cost.batch_per_session + cost.batch_alpha * window
    return max(4, int((f.period_s*1000*0.9 - cost.batch_base)/max(denom, 1e-9)))


def silence_gain(name, horizon_s=120.0):
    """Goodput with silence exploitation ON vs OFF, across talk fractions."""
    f = models.get(name)
    window = max(512, f.context_ceiling_tokens // 4)
    cap = capacity(name, window)
    mean_hold = min(90.0, f.fill_time_s * 0.5)
    rate = (1.5 * cap) / mean_hold      # mild overload
    rows = []
    # talk fraction = p_start/(p_start+p_stop); vary by p_start. Compare a
    # silence-AWARE admission controller (provisions for talk_frac talkers + defers
    # no-speak ticks) vs a silence-UNAWARE one (provisions for all-talk).
    for talk_frac in (0.3, 0.5, 0.7, 1.0):
        p_stop = 0.15
        p_start = p_stop * talk_frac / max(1e-9, (1 - talk_frac)) if talk_frac < 1 else 1.0
        on = OpenSystemSimulator(cfg(name, arrival_rate_hz=rate, admission=True,
                                 silence=True, p_talk_start=p_start, p_talk_stop=p_stop,
                                 start_talking=talk_frac, admission_talk_fraction=talk_frac)
                                 ).run(horizon_s, warmup_s=20.0)
        off = OpenSystemSimulator(cfg(name, arrival_rate_hz=rate, admission=True,
                                  silence=False, p_talk_start=p_start, p_talk_stop=p_stop,
                                  start_talking=talk_frac, admission_talk_fraction=1.0)
                                  ).run(horizon_s, warmup_s=20.0)
        served_on = float(np.mean(on.per_frame_active)) if on.per_frame_active else 0
        served_off = float(np.mean(off.per_frame_active)) if off.per_frame_active else 0
        rows.append(dict(talk_frac=talk_frac, served_on=served_on, served_off=served_off,
                         gain=round(served_on/max(1e-9, served_off), 2),
                         miss_on=on.report.miss_rate, miss_off=off.report.miss_rate))
        print(f"  [{name}] talk={talk_frac:.1f}  served aware={served_on:.0f} "
              f"unaware={served_off:.0f}  gain={rows[-1]['gain']}x  "
              f"miss aware={on.report.miss_rate:.4f}")
    return rows, cap


def miss_run_compare(name, horizon_s=120.0):
    """At a matched ~1.5x overload, Metronome vs greedy consecutive-miss runs."""
    f = models.get(name)
    window = max(512, f.context_ceiling_tokens // 4)
    cap = capacity(name, window)
    mean_hold = min(90.0, f.fill_time_s * 0.5)
    rate = (3.0 * cap) / mean_hold     # heavy overload so greedy clearly melts down
    m = OpenSystemSimulator(cfg(name, arrival_rate_hz=rate, admission=True)
                            ).run(horizon_s, warmup_s=20.0)
    g = OpenSystemSimulator(cfg(name, arrival_rate_hz=rate, admission=False,
                            memory_admission=True, ordering="fifo", eviction="full",
                            degradation=False, silence=False)).run(horizon_s, warmup_s=20.0)
    m_runs = [r for v in m.report.per_session_miss.values()
              for r in consecutive_run_lengths(v)]
    g_runs = [r for v in g.report.per_session_miss.values()
              for r in consecutive_run_lengths(v)]
    return dict(
        model=name, cap=cap,
        m=dict(miss=m.report.miss_rate, fairness=m.report.fairness(),
               run_p99=int(np.percentile(m_runs, 99)) if m_runs else 0,
               run_max=int(max(m_runs)) if m_runs else 0,
               blocking=m.report.blocking),
        g=dict(miss=g.report.miss_rate, fairness=g.report.fairness(),
               run_p99=int(np.percentile(g_runs, 99)) if g_runs else 0,
               run_max=int(max(g_runs)) if g_runs else 0,
               blocking=g.report.blocking),
        m_runs=m_runs, g_runs=g_runs)


def adversarial_burst(name, horizon_s=80.0):
    """All sessions un-silence simultaneously mid-run (synchronized talk burst);
    measure the transient miss with Metronome (admission headroom + degradation)."""
    f = models.get(name)
    window = max(512, f.context_ceiling_tokens // 4)
    cap = capacity(name, window)
    mean_hold = min(90.0, f.fill_time_s * 0.5)
    rate = (1.2 * cap) / mean_hold
    # high silence normally, but a burst forces everyone to talk -> set start high
    sim = OpenSystemSimulator(cfg(name, arrival_rate_hz=rate, admission=True,
                              silence=True, p_talk_start=0.2, p_talk_stop=0.4,
                              start_talking=0.3))
    r = sim.run(horizon_s, warmup_s=10.0)
    return dict(model=name, peak_miss=float(np.max(r.per_frame_miss)) if r.per_frame_miss else 0,
                mean_miss=r.report.miss_rate, blocking=r.report.blocking)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=None)
    ap.add_argument("--horizon", type=float, default=120.0)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    names = args.models or all_models()
    summary = {}
    for name in names:
        print(f"\n=== {name} conversation dynamics ===")
        sg, cap = silence_gain(name, args.horizon)
        mr = miss_run_compare(name, args.horizon)
        adv = adversarial_burst(name, min(args.horizon, 80.0))
        summary[name] = dict(silence_gain=sg, miss_runs=mr, adversarial=adv)
        print(f"  [{name}] miss-runs: Metronome p99={mr['m']['run_p99']} max={mr['m']['run_max']} "
              f"(miss {mr['m']['miss']:.3f}) vs greedy p99={mr['g']['run_p99']} "
              f"max={mr['g']['run_max']} (miss {mr['g']['miss']:.3f})")
        print(f"  [{name}] fairness: M={mr['m']['fairness']:.3f} greedy={mr['g']['fairness']:.3f}; "
              f"adversarial burst peak miss={adv['peak_miss']:.3f}")

    # miss-run histogram figure
    fig, axes = plt.subplots(1, len(names), figsize=(4*len(names), 3.6), squeeze=False)
    for ax, name in zip(axes[0], names):
        mr = summary[name]["miss_runs"]
        mx = max([1] + mr["m_runs"] + mr["g_runs"])
        bins = np.arange(1, min(mx, 40) + 2) - 0.5
        if mr["g_runs"]:
            ax.hist(mr["g_runs"], bins=bins, alpha=0.6, color="#d62728", label="greedy")
        if mr["m_runs"]:
            ax.hist(mr["m_runs"], bins=bins, alpha=0.6, color="#2ca02c", label="Metronome")
        ax.set_yscale("log"); ax.set_xlabel("consecutive-miss run length")
        ax.set_ylabel("count"); ax.set_title(name); ax.legend(fontsize=8)
    fig.suptitle("Consecutive-miss runs: greedy = long dropouts, Metronome = short")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "miss_runs.png"), dpi=120)
    plt.close(fig)

    # strip the raw run lists before saving
    for name in names:
        summary[name]["miss_runs"].pop("m_runs", None)
        summary[name]["miss_runs"].pop("g_runs", None)
    with open(os.path.join(OUT, "conversation_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)


if __name__ == "__main__":
    main()
