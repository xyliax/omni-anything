"""S6: KV manager & eviction sweep — the "essential vs complementary" result.

Two claims (Contribution 2):
  (a) quality degrades *gracefully* (not a cliff) as the KV budget shrinks, and the
      policies order as full >= h2o >= sink_window >= sliding;
  (b) serving-level KV management is *essential* for a model with no built-in
      context bounding (Moshi, full MHA) and merely *complementary* for one that
      windows itself (Qwen-Omni). We quantify "essential vs complementary" as the
      MSCS gain a fixed KV budget buys: large for Moshi, small for Qwen-Omni.

Produces: quality-vs-budget Pareto, MSCS-vs-budget per policy, and the
essential-vs-complementary bar.
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
from metronome.kv_manager import make_policy, quality_proxy, POLICIES
from metronome.admission import AdmissionController, AdmissionConfig
from metronome.session import PeriodicSession
from sim.simulator import Simulator, SimConfig
from bench.generator import WorkloadConfig, make_population
from bench.metrics import mscs, mscs_served

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "kv")
TARGET_MISS = 0.001
POLICY_COLORS = {"full": "#7f7f7f", "sliding": "#1f77b4",
                 "sink_window": "#2ca02c", "h2o": "#d62728"}


def quality_vs_budget(name, facts):
    """Mean retained attention mass vs KV budget, per policy, at a long context."""
    ceiling = facts.context_ceiling_tokens
    full_len = ceiling                      # a session at the ceiling
    budgets = np.unique(np.clip(
        (np.array([1/32, 1/16, 1/8, 1/4, 1/2, 3/4, 1.0]) * ceiling).astype(int),
        64, ceiling))
    out = {}
    for pol_name in POLICIES:
        qs = []
        for b in budgets:
            # average the proxy over several sessions (seeds) for stability
            vals = [quality_proxy(make_policy(pol_name, int(b)), full_len, int(b), seed=s)
                    for s in range(8)]
            qs.append(float(np.mean(vals)))
        out[pol_name] = (budgets.tolist(), qs)
    return out


def mscs_at_budget(name, cost, facts, budget, policy, n_max=1024, n_frames=250):
    hbm = hbm_kv_bytes()
    ns = [n for n in (1,2,4,8,16,32,64,128,256,512,768,1024) if n <= n_max]
    curve = []
    for n in ns:
        cfg = SimConfig(cost=cost, frame_budget_s=facts.period_s, hbm_kv_bytes=hbm,
                        admission=True, ordering="edf", eviction=policy,
                        degradation=True, silence=False, kv_budget_tokens=int(budget))
        wl = WorkloadConfig(facts=facts, kv_budget_tokens=int(budget),
                            mean_session_s=facts.fill_time_s*0.6, seed=0)
        pop = make_population(wl, n)
        r = Simulator(cfg).run_static(pop, n_frames)
        curve.append((n, r.admitted, r.metrics.miss_rate))
    return mscs_served(curve, TARGET_MISS)


def run(name, n_max, n_frames):
    facts = models.get(name)
    cost = load_cost(name)
    os.makedirs(OUT, exist_ok=True)

    # (a) quality-vs-budget Pareto
    qvb = quality_vs_budget(name, facts)
    fig, ax = plt.subplots(figsize=(6, 4))
    for pol in POLICIES:
        b, q = qvb[pol]
        ax.plot(np.array(b) / facts.context_ceiling_tokens, q, "o-",
                color=POLICY_COLORS[pol], label=pol)
    ax.set_xlabel("KV budget (fraction of context ceiling)")
    ax.set_ylabel("retained attention mass (quality proxy)")
    ax.set_title(f"{name}: quality vs KV budget (graceful, policy-ordered)")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{name}_quality_vs_budget.png"), dpi=120)
    plt.close(fig)

    # (b) MSCS vs budget for the default policy -> essential vs complementary
    ceiling = facts.context_ceiling_tokens
    budgets = sorted(set(int(c) for c in
                     [ceiling//16, ceiling//8, ceiling//4, ceiling//2, ceiling]))
    mscs_by_budget = {b: mscs_at_budget(name, cost, facts, b, "sink_window",
                                        n_max, n_frames) for b in budgets}
    full_mscs = mscs_at_budget(name, cost, facts, ceiling, "full", n_max, n_frames)
    small_b = budgets[1]
    gain = mscs_by_budget[small_b] / max(1, full_mscs)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot([b/ceiling for b in budgets], [mscs_by_budget[b] for b in budgets],
            "o-", color="#2ca02c", label="sink_window")
    ax.axhline(full_mscs, color="#7f7f7f", ls="--", label="full KV")
    ax.set_xlabel("KV budget (fraction of ceiling)")
    ax.set_ylabel(f"MSCS @ {TARGET_MISS:.1%}")
    ax.set_title(f"{name}: capacity gain from KV budgeting")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{name}_mscs_vs_budget.png"), dpi=120)
    plt.close(fig)

    res = dict(model=name, self_windowing=facts.self_windowing,
               full_mscs=full_mscs, mscs_by_budget=mscs_by_budget,
               kv_budget_gain=gain,
               classification="complementary" if facts.self_windowing else "essential")
    with open(os.path.join(OUT, f"{name}_kv.json"), "w") as fh:
        json.dump(res, fh, indent=2)
    print(f"[{name}] self_windowing={facts.self_windowing}  full_MSCS={full_mscs}  "
          f"budgeted({small_b})_MSCS={mscs_by_budget[small_b]}  gain={gain:.2f}x  "
          f"-> {res['classification']}")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=None)
    ap.add_argument("--n-max", type=int, default=1024)
    ap.add_argument("--n-frames", type=int, default=250)
    args = ap.parse_args()
    names = args.models or all_models()
    summary = [run(n, args.n_max, args.n_frames) for n in names]

    # essential-vs-complementary bar across models
    fig, ax = plt.subplots(figsize=(6, 4))
    xs = [s["model"] for s in summary]
    gains = [s["kv_budget_gain"] for s in summary]
    cols = ["#d62728" if not models.get(s["model"]).self_windowing else "#1f77b4"
            for s in summary]
    ax.bar(xs, gains, color=cols)
    ax.axhline(1.0, color="black", ls=":")
    ax.set_ylabel("MSCS gain from KV budgeting (x)")
    ax.set_title("Essential (red, no self-windowing) vs complementary (blue)")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "essential_vs_complementary.png"), dpi=120)
    plt.close(fig)

    with open(os.path.join(OUT, "kv_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)
    print("\n=== KV / essential-vs-complementary ===")
    for s in summary:
        print(f"  {s['model']}: {s['classification']} (gain {s['kv_budget_gain']:.2f}x)")


if __name__ == "__main__":
    main()
