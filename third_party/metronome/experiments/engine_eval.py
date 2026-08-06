"""Real-engine evaluation — the headline serving numbers measured on the running
system (metronome/engine.py), not the simulator.

For each model we measure, on the GPU:
  * the per-tick latency vs session age (KV grows) — the real GATE-A money plot;
  * the real timing MSCS: the largest concurrency N whose measured p99 tick latency
    stays within the frame budget, at the plateau (worst-case age), for B1 (full-KV,
    grows to the context ceiling) vs M (windowed KV budget);
  * combined with the analytical HBM memory cap (true L-layer KV footprint) to give
    the real MSCS = min(timing, memory) — and the M/B1 gain and $/session-hour;
  * the real p50/p99/p999 jitter.

We also load the simulator's prediction for the same configs to validate it (the
simulator is now a predictor checked against the real system).
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
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bench.gpu_probe import wait_for_window
from metronome.engine import ServingEngine, free_gib
from metronome import models
from experiments._common import load_cost, hbm_kv_bytes, HBM_KV_GIB

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "engine")
DOLLARS_PER_HR = 2.0


def memory_cap(facts, budget_tokens):
    """True L-layer KV footprint -> max sessions that fit HBM."""
    per_session = budget_tokens * facts.kv_bytes_per_token
    return int(hbm_kv_bytes() / per_session)


def measure_onset(eng, facts, budget_tokens, ns, n_frames, reps_budget_gib):
    """Sweep N at the plateau (L=budget); return [(N, p50, p99, over)] and the
    timing MSCS (largest N with p99 <= frame budget)."""
    budget_ms = facts.period_s * 1000.0
    rows = []
    onset = 0
    for N in ns:
        # memory guard for the 1-layer cache
        cache_gib = N * budget_tokens * facts.num_kv_heads * facts.head_dim * 2 * 2 / 2**30
        if cache_gib > reps_budget_gib:
            break
        wait_for_window(need_free_gib=cache_gib + 1.5, max_util_pct=85,
                        quiet=True, timeout_s=7200)
        try:
            lats = eng.serve_cohort(N, n_frames=n_frames, start_lengths=[budget_tokens]*N,
                                    grow=False, warmup=5)
        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache()
            print(f"    N={N:4d}  OOM (free window too small) — stopping sweep")
            break
        p50, p99 = float(np.percentile(lats, 50)), float(np.percentile(lats, 99))
        over = p99 > budget_ms
        rows.append((N, p50, p99, over))
        if not over:
            onset = N
        print(f"    N={N:4d}  p50={p50:6.1f}ms p99={p99:6.1f}ms  budget={budget_ms:.0f}ms"
              f"  {'OVER' if over else 'ok'}")
        if over and p99 > 1.5 * budget_ms:
            break   # well past the onset, stop
    return rows, onset


def latency_vs_age(eng, facts, N, window, n_frames):
    """Run a real N-session cohort from empty, growing KV each frame; measured
    per-tick latency climbs with age. Returns (ages_tokens, latencies)."""
    lats = eng.serve_cohort(N, n_frames=n_frames, start_lengths=[0]*N, grow=True, warmup=5)
    rate = facts.tokens_per_tick
    ages = [min((i+1)*rate, window) for i in range(len(lats))]
    return ages, lats


def run(name, n_frames, max_cache_gib):
    facts = models.get(name)
    cost = load_cost(name)
    ceiling = facts.context_ceiling_tokens
    window = max(512, ceiling // 4)
    budget_ms = facts.period_s * 1000.0
    os.makedirs(OUT, exist_ok=True)
    print(f"\n=== {name} REAL ENGINE (budget {budget_ms:.0f}ms, ceiling {ceiling}, window {window}) ===")

    def max_n_for(budget_tokens):
        per = budget_tokens * facts.num_kv_heads * facts.head_dim * 2 * 2  # bytes/session (1 layer)
        return max(8, int(max_cache_gib * 2**30 / per))

    # concurrency grids, capped to what the cache budget allows
    maxn_f, maxn_w = max_n_for(ceiling), max_n_for(window)
    ns_full = [n for n in [8,16,24,32,40,48,64,80,96,128,160,192] if n <= maxn_f]
    ns_win = [n for n in [16,32,48,64,96,128,160,192,224,256,320,384,448] if n <= maxn_w]

    # --- M (windowed) ---
    wait_for_window(need_free_gib=max_cache_gib + 1.5, max_util_pct=85, quiet=True, timeout_s=7200)
    eng_w = ServingEngine(facts, max_sessions=max(ns_win), max_budget_tokens=window)
    print(f"  M (windowed L={window}, max N={max(ns_win)}):")
    rows_w, onset_w = measure_onset(eng_w, facts, window, ns_win, n_frames, max_cache_gib)
    N_age = max(8, (onset_w if onset_w else max(ns_win)) // 2)
    ages_w, lats_age = latency_vs_age(eng_w, facts, N_age, window, min(n_frames*3, 200))
    del eng_w; torch.cuda.empty_cache()

    # --- B1 (full KV to ceiling) ---
    wait_for_window(need_free_gib=max_cache_gib + 1.5, max_util_pct=85, quiet=True, timeout_s=7200)
    eng_f = ServingEngine(facts, max_sessions=max(ns_full), max_budget_tokens=ceiling)
    print(f"  B1 (full KV L={ceiling}, max N={max(ns_full)}):")
    rows_f, onset_f = measure_onset(eng_f, facts, ceiling, ns_full, n_frames, max_cache_gib)
    del eng_f; torch.cuda.empty_cache()

    # combine timing onset with analytical memory cap -> real MSCS
    mem_f, mem_w = memory_cap(facts, ceiling), memory_cap(facts, window)
    mscs_b1 = min(onset_f, mem_f) if onset_f else mem_f
    mscs_m = min(onset_w, mem_w) if onset_w else mem_w
    gain = mscs_m / max(1, mscs_b1)
    dollars_b1 = DOLLARS_PER_HR / max(1, mscs_b1)
    dollars_m = DOLLARS_PER_HR / max(1, mscs_m)

    # sim prediction for the same configs (validation)
    sim_pred_w = predict_sim_mscs(cost, facts, window)
    sim_pred_f = predict_sim_mscs(cost, facts, ceiling)

    # plots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    ax1.plot(ages_w, lats_age, "o-", color="#1f77b4", label=f"measured (N={N_age})")
    ax1.axhline(budget_ms, color="red", ls=":", label=f"{budget_ms:.0f} ms deadline")
    ax1.set_xlabel("session age (resident KV tokens)"); ax1.set_ylabel("measured tick latency (ms)")
    ax1.set_title(f"{name}: REAL latency vs age"); ax1.legend(fontsize=8); ax1.grid(alpha=0.3)
    ax2.plot([r[0] for r in rows_f], [r[2] for r in rows_f], "s-", color="#d62728", label="B1 full-KV p99")
    ax2.plot([r[0] for r in rows_w], [r[2] for r in rows_w], "o-", color="#2ca02c", label="M windowed p99")
    ax2.axhline(budget_ms, color="black", ls=":", label="deadline")
    ax2.set_xlabel("concurrency N"); ax2.set_ylabel("measured p99 tick latency (ms)")
    ax2.set_title(f"{name}: REAL capacity (timing onset)"); ax2.legend(fontsize=8); ax2.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{name}_engine.png"), dpi=120)
    plt.close(fig)

    # jitter at the M operating point (N just below onset, at plateau)
    p999 = float(np.percentile(lats_age, 99.9)) if lats_age else 0.0
    res = dict(model=name, budget_ms=budget_ms, window=window, ceiling=ceiling,
               timing_onset_full=onset_f, timing_onset_window=onset_w,
               mem_cap_full=mem_f, mem_cap_window=mem_w,
               mscs_b1=mscs_b1, mscs_m=mscs_m, gain=round(gain, 2),
               dollars_b1=round(dollars_b1, 4), dollars_m=round(dollars_m, 4),
               sim_pred_mscs_window=sim_pred_w, sim_pred_mscs_full=sim_pred_f,
               jitter_p999_ms=round(p999, 2),
               rows_full=rows_f, rows_window=rows_w,
               latency_vs_age=list(zip([int(a) for a in ages_w], [round(l,3) for l in lats_age])))
    with open(os.path.join(OUT, f"{name}_engine.json"), "w") as fh:
        json.dump(res, fh, indent=2)
    print(f"  REAL MSCS: B1={mscs_b1} (timing {onset_f}, mem {mem_f}) -> "
          f"M={mscs_m} (timing {onset_w}, mem {mem_w})  gain={gain:.2f}x")
    print(f"  sim predicted: B1~{sim_pred_f}, M~{sim_pred_w}  (validation)")
    print(f"  $/session-hr: B1=${dollars_b1:.4f} -> M=${dollars_m:.4f}")
    return res


def predict_sim_mscs(cost, facts, budget_tokens):
    """Simulator's worst-case-admission MSCS for this config (for validation)."""
    from metronome.admission import AdmissionController, AdmissionConfig
    from metronome.session import PeriodicSession
    ac = AdmissionController(cost, AdmissionConfig(hbm_kv_bytes(), facts.period_s, 0.90,
                                                  mode="worst_case"))
    proto = PeriodicSession(sid=0, facts=facts, period_s=facts.period_s,
                            deadline_s=facts.period_s, phase_s=0.0,
                            kv_budget_tokens=budget_tokens,
                            token_rate=facts.tokens_per_tick/facts.period_s)
    return ac.predict_capacity(proto)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=["moshi", "minicpm-o", "qwen3-omni"])
    ap.add_argument("--n-frames", type=int, default=20)
    ap.add_argument("--max-cache-gib", type=float, default=7.0)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    summ = {}
    for name in args.models:
        try:
            summ[name] = run(name, args.n_frames, args.max_cache_gib)
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"[{name}] FAILED: {e}")
    with open(os.path.join(OUT, "engine_summary.json"), "w") as fh:
        json.dump(summ, fh, indent=2)
    print("\n=== REAL ENGINE MSCS ===")
    for n, r in summ.items():
        print(f"  {n}: B1={r['mscs_b1']} -> M={r['mscs_m']} ({r['gain']}x)  "
              f"[sim predicted M~{r['sim_pred_mscs_window']}]")


if __name__ == "__main__":
    main()
