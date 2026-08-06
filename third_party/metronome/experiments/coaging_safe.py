"""Task C — co-aging-safe age-aware admission.

H3 showed naive age-aware admission breaks when a cohort co-ages to the plateau.
The theory: with *no departures*, the only safe admission is worst-case (every
session reaches the plateau), so age-aware's extra capacity is precisely a **churn
dividend** — it is safe only while departures keep the near-plateau population below
the worst-case cap. The co-aging-safe controller therefore adapts its look-ahead
guard horizon to the *observed departure rate*: high churn → short horizon (admit
like age-aware); low churn → horizon grows toward fill-to-budget (→ worst-case, so a
co-aging cohort can never breach).

We sweep the mean session lifetime (the churn knob) and compare three controllers
under steady open-system load:
  * worst-case  — always safe, conservative;
  * age-aware   — admits more, but breaches once lifetimes exceed the fill time;
  * co-aging-safe — matches age-aware under short lifetimes AND stays at 0 miss under
    long lifetimes (auto-falls back to worst-case).
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
                   "results", "coaging_safe")
SLO = 0.001


def cap_worst_case(cost, facts, window):
    denom = cost.batch_per_session + cost.batch_alpha * window
    return max(4, int((facts.period_s*1000*0.9 - cost.batch_base)/max(denom, 1e-9)))


def cfg(name, mode, window, rate, hold, **kw):
    f = models.get(name)
    cost = load_cost(name)
    d = dict(cost=cost, facts=f, hbm_kv_bytes=hbm_kv_bytes(), kv_budget_tokens=window,
             arrival_rate_hz=rate, mean_holding_s=hold, eviction="sink_window",
             degradation=False,  # degradation OFF so admission alone must be safe
             silence=False, admission=True, admission_mode=mode, seed=0)
    d.update(kw)
    return OpenConfig(**d)


def run(name, horizon_s=150.0):
    f = models.get(name)
    cost = load_cost(name)
    window = max(512, f.context_ceiling_tokens // 4)
    wc_cap = cap_worst_case(cost, f, window)
    fill_budget_s = window / (f.tokens_per_tick / f.period_s)
    a_char = fill_budget_s * 0.5
    # sweep mean lifetime from 0.2x to 3x the fill-to-budget time (the churn regime)
    holdings = [round(m * fill_budget_s, 1) for m in (0.2, 0.4, 0.7, 1.0, 1.5, 2.0, 3.0)]
    # the run must outlast fill-to-budget so a co-aging cohort actually reaches the
    # plateau; warm up past one fill time, then record a steady window.
    warmup = fill_budget_s + 10.0
    horizon = max(horizon_s, warmup + 80.0)
    # offered load ~ 2x worst-case cap so admission binds; rate = offered/hold
    rows = {"worst_case": [], "age_aware": [], "coaging_safe": []}
    for hold in holdings:
        rate = (2.0 * wc_cap) / hold
        runs = {
            "worst_case": cfg(name, "worst_case", window, rate, hold),
            "age_aware": cfg(name, "age_aware", window, rate, hold, assumed_age_s=a_char),
            "coaging_safe": cfg(name, "lookahead", window, rate, hold, coaging_safe=True),
        }
        for label, c in runs.items():
            r = OpenSystemSimulator(c).run(horizon, warmup_s=warmup)
            served = float(np.mean(r.per_frame_active)) if r.per_frame_active else 0
            rows[label].append(dict(hold=hold, hold_over_fill=round(hold/fill_budget_s, 2),
                                    served=served, miss=r.report.miss_rate,
                                    blocking=r.report.blocking))
        print(f"  [{name}] hold={hold:.0f}s ({hold/fill_budget_s:.1f}x fill): "
              + "  ".join(f"{l}: served={rows[l][-1]['served']:.0f} miss={rows[l][-1]['miss']:.4f}"
                          for l in rows))

    os.makedirs(OUT, exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    colors = {"worst_case": "#1f77b4", "age_aware": "#d62728", "coaging_safe": "#2ca02c"}
    x = [r["hold_over_fill"] for r in rows["worst_case"]]
    for label in rows:
        ax1.plot(x, [r["served"] for r in rows[label]], "o-", color=colors[label], label=label)
        ax2.plot(x, [max(r["miss"], 1e-6) for r in rows[label]], "o-", color=colors[label], label=label)
    ax1.set_xlabel("mean lifetime / fill-to-budget time"); ax1.set_ylabel("served concurrency")
    ax1.set_title(f"{name}: served vs churn regime"); ax1.legend(fontsize=8); ax1.grid(alpha=0.3)
    ax2.axhline(SLO, color="black", ls=":", label="SLO"); ax2.set_yscale("log")
    ax2.set_xlabel("mean lifetime / fill-to-budget time"); ax2.set_ylabel("deadline-miss rate")
    ax2.set_title(f"{name}: age-aware breaches when lifetimes>fill; safe variant holds")
    ax2.legend(fontsize=8); ax2.grid(alpha=0.3, which="both")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{name}_coaging_safe.png"), dpi=120)
    plt.close(fig)

    # summary: does coaging_safe ever breach? does it beat worst-case under short life?
    aa_breach = max(r["miss"] for r in rows["age_aware"])
    cs_breach = max(r["miss"] for r in rows["coaging_safe"])
    short = 0  # shortest lifetime index
    cs_gain = rows["coaging_safe"][short]["served"] / max(1e-9, rows["worst_case"][short]["served"])
    res = dict(model=name, wc_cap=wc_cap, fill_budget_s=fill_budget_s,
               age_aware_max_miss=aa_breach, coaging_safe_max_miss=cs_breach,
               coaging_safe_short_life_gain=round(cs_gain, 2), rows=rows)
    print(f"[{name}] age-aware max miss={aa_breach:.3f} (breaches); "
          f"co-aging-safe max miss={cs_breach:.4f}; short-life served gain "
          f"{cs_gain:.2f}x over worst-case")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=None)
    ap.add_argument("--horizon", type=float, default=150.0)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    names = args.models or all_models()
    out = {}
    for name in names:
        print(f"\n=== {name} co-aging-safe admission ===")
        out[name] = run(name, args.horizon)
    with open(os.path.join(OUT, "coaging_safe_summary.json"), "w") as fh:
        json.dump(out, fh, indent=2)


if __name__ == "__main__":
    main()
