"""S2 / GATE A: establish the problem empirically, before relying on the system.

Two questions (PIPELINE GATE A):
  (1) Does per-tick latency actually climb with KV/age?  -> from the MEASURED
      single-session sweep (results/cost_model/<m>_single.csv). The latency-vs-age
      curve (Figure 1a).
  (2) Does throughput-greedy batching actually miss frames under multi-tenant load,
      especially at the tight deadline? -> B1 in the calibrated simulator (and the
      measured batch sweep as a live cross-check). The MSCS curve (Figure 1b).

GATE A passes iff (1) latency rises monotonically with context AND (2) B1's
miss-rate crosses the SLO at a concurrency where Metronome (M) does not.
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

from metronome import models
from metronome.cost_model import CostModel
from metronome.session import PeriodicSession
from sim.simulator import Simulator, SimConfig, preset
from bench.generator import WorkloadConfig, make_population
from bench.metrics import mscs, mscs_served

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CM_DIR = os.path.join(ROOT, "results", "cost_model")
OUT = os.path.join(ROOT, "results", "problem")

TARGET_MISS = 0.001   # 0.1% missed ticks SLO


def load_cost(name) -> CostModel:
    return CostModel.from_json(os.path.join(CM_DIR, f"{name}.json"))


def read_single_csv(name):
    rows = []
    with open(os.path.join(CM_DIR, f"{name}_single.csv")) as fh:
        for r in csv.DictReader(fh):
            rows.append((int(r["total_kv"]), float(r["p50_ms"]), float(r["p99_ms"])))
    return sorted(rows)


def hbm_kv_bytes(free_gib=80.0):
    return free_gib * 2**30


def mscs_sweep(cost, facts, growth_budget, n_max=512, n_frames=400, hbm=None,
               admission=False, ordering="fifo", evic="full", degr=False, sil=False,
               window_budget=0):
    """Run a preset across increasing concurrency; return [(n, miss, p99, p999, adm)].

    ``growth_budget`` = the context ceiling each session grows toward (full for
    B1/B2; the windowed budget for M). ``window_budget`` = resident KV cap enforced
    by eviction (M only)."""
    hbm = hbm or hbm_kv_bytes()
    curve = []
    ns = sorted(set([1,2,4,6,8,12,16,24,32,48,64,96,128,192,256,384,512]))
    ns = [n for n in ns if n <= n_max]
    for n in ns:
        cfg = SimConfig(cost=cost, frame_budget_s=facts.period_s, hbm_kv_bytes=hbm,
                        admission=admission, ordering=ordering, eviction=evic,
                        degradation=degr, silence=sil,
                        kv_budget_tokens=window_budget if evic != "full" else 0)
        wl = WorkloadConfig(facts=facts, kv_budget_tokens=growth_budget,
                            mean_session_s=facts.fill_time_s*0.6, talk_ratio=1.0,
                            phase_jitter=True, seed=0)
        pop = make_population(wl, n)
        res = Simulator(cfg).run_static(pop, n_frames)
        curve.append((n, res.metrics.miss_rate, res.metrics.p99, res.metrics.p999,
                      res.admitted))
    return curve


def plot_latency_vs_age(name, facts, rows):
    """Figure 1a: measured per-tick latency vs context length (= session age)."""
    L = np.array([r[0] for r in rows])
    age_s = L / (facts.tokens_per_tick / facts.period_s)  # context -> wall age
    p50 = np.array([r[1] for r in rows])
    p99 = np.array([r[2] for r in rows])
    budget = facts.period_s * 1000.0
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(age_s, p50, "o-", label="measured p50", color="#1f77b4")
    ax.plot(age_s, p99, "s--", label="measured p99", color="#ff7f0e")
    ax.axhline(budget, color="red", ls=":", lw=2, label=f"frame budget {budget:.0f} ms")
    ax.set_xlabel("session age (s)  [context grows with age]")
    ax.set_ylabel("per-tick latency (ms)")
    ax.set_title(f"{name}: per-tick latency climbs with session age (B1, single session)")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, f"{name}_latency_vs_age.png"), dpi=120)
    plt.close(fig)
    monotone = bool(np.all(np.diff(p99) >= -0.5))   # allow tiny noise
    return monotone, float(p99[-1]), budget


def plot_mscs(name, facts, curves):
    """Figure 1b: miss-rate vs concurrency for B1 vs M."""
    fig, ax = plt.subplots(figsize=(6, 4))
    colors = {"B1": "#d62728", "B2": "#9467bd", "M": "#2ca02c"}
    out = {}
    for label, curve in curves.items():
        ns = [c[0] for c in curve]
        miss = [max(c[1], 1e-6) for c in curve]
        ax.plot(ns, miss, "o-", label=label, color=colors.get(label))
        # served-MSCS: count admitted sessions (index 4), not offered load
        out[label] = mscs_served([(c[0], c[4], c[1]) for c in curve], TARGET_MISS)
    ax.axhline(TARGET_MISS, color="black", ls=":", label=f"SLO {TARGET_MISS:.1%}")
    ax.set_yscale("log")
    ax.set_xlabel("concurrent sessions")
    ax.set_ylabel("deadline-miss rate")
    ax.set_title(f"{name}: throughput-greedy (B1) misses frames; Metronome (M) holds SLO")
    ax.legend(); ax.grid(alpha=0.3, which="both")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, f"{name}_mscs.png"), dpi=120)
    plt.close(fig)
    return out


def run(name, n_max, n_frames):
    facts = models.get(name)
    cost = load_cost(name)
    rows = read_single_csv(name)
    os.makedirs(OUT, exist_ok=True)

    monotone, peak_p99, budget = plot_latency_vs_age(name, facts, rows)

    # B1/B2 grow to the full context ceiling (no KV management); M windows the KV.
    ceiling = facts.context_ceiling_tokens
    window = max(512, ceiling // 4)
    curves = {
        "B1": mscs_sweep(cost, facts, ceiling, n_max, n_frames,
                         admission=False, ordering="fifo", evic="full"),
        "B2": mscs_sweep(cost, facts, ceiling, n_max, n_frames,
                         admission=False, ordering="edf", evic="full"),
        "M":  mscs_sweep(cost, facts, window, n_max, n_frames,
                         admission=True, ordering="edf", evic="sink_window",
                         degr=True, sil=False, window_budget=window),
    }
    mscs_vals = plot_mscs(name, facts, curves)

    # persist raw curves
    with open(os.path.join(OUT, f"{name}_curves.json"), "w") as fh:
        json.dump({k: [list(map(float, c)) for c in v] for k, v in curves.items()},
                  fh, indent=2)

    gate_a = monotone and (mscs_vals["B1"] < mscs_vals["M"])
    print(f"\n[{name}] latency-vs-age monotone: {monotone} "
          f"(peak p99 {peak_p99:.1f}ms vs budget {budget:.0f}ms)")
    print(f"[{name}] MSCS @ {TARGET_MISS:.1%}: "
          + "  ".join(f"{k}={v}" for k, v in mscs_vals.items()))
    print(f"[{name}] GATE A: {'PASS' if gate_a else 'CHECK'} "
          f"(latency climbs AND B1 MSCS {mscs_vals['B1']} < M MSCS {mscs_vals['M']})")
    return gate_a, mscs_vals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=["moshi", "minicpm-o", "qwen3-omni"])
    ap.add_argument("--n-max", type=int, default=512)
    ap.add_argument("--n-frames", type=int, default=300)
    args = ap.parse_args()
    summary = {}
    for name in args.models:
        if not os.path.exists(os.path.join(CM_DIR, f"{name}.json")):
            print(f"[skip] no cost model for {name}")
            continue
        gate, vals = run(name, args.n_max, args.n_frames)
        summary[name] = dict(gate_a=gate, mscs=vals)
    with open(os.path.join(OUT, "gate_a_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)
    print("\n=== GATE A summary ===")
    for k, v in summary.items():
        print(f"  {k}: {'PASS' if v['gate_a'] else 'CHECK'}  MSCS={v['mscs']}")


if __name__ == "__main__":
    main()
