"""C1/C3 real-engine timing with confidence intervals: repeat the per-tick latency
measurement (real GPU, serve_cohort) across reps for Metronome-windowed (M) vs full-KV
(B1) at a fixed concurrency, and report p99 latency mean ± 95% CI. The single-run version
(engine_eval) gave the headline gain; this adds the CI the timing claim needs. Gated on a
low-utilisation window so co-tenants don't corrupt the timing."""
import argparse
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")

import numpy as np
from bench.gpu_probe import wait_for_window
from metronome.engine import ServingEngine
from metronome import models


def ci95(xs):
    if len(xs) < 2:
        return (round(xs[0], 2), round(xs[0], 2)) if xs else (0, 0)
    m, sd = statistics.mean(xs), statistics.stdev(xs)
    h = 1.96 * sd / (len(xs) ** 0.5)
    return (round(m - h, 2), round(m + h, 2))


def measure(facts, N, budget, reps, n_frames):
    import torch
    eng = ServingEngine(facts, max_sessions=N, max_budget_tokens=budget)
    p99s = []
    for _ in range(reps):
        lats = eng.serve_cohort(N, n_frames=n_frames, start_lengths=[budget] * N, warmup=3)
        p99s.append(float(np.percentile(lats, 99)))
    del eng; torch.cuda.empty_cache()
    return p99s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=["minicpm-o", "moshi", "qwen3-omni"])
    ap.add_argument("--N", type=int, default=48)
    ap.add_argument("--reps", type=int, default=8)
    ap.add_argument("--n-frames", type=int, default=20)
    ap.add_argument("--max-util", type=int, default=40)   # low: clean timing
    args = ap.parse_args()
    summary = {}
    for name in args.models:
        try:
            facts = models.get(name)
        except Exception as e:
            print(f"[{name}] skip {e}"); continue
        ceiling = facts.context_ceiling_tokens
        window = max(512, ceiling // 4)
        budget_ms = facts.period_s * 1000.0
        print(f"\n=== {name} timing CI (N={args.N}, {args.reps} reps, budget {budget_ms:.0f}ms) ===",
              flush=True)
        wait_for_window(need_free_gib=24, max_util_pct=args.max_util, timeout_s=72000)
        pw = measure(facts, args.N, window, args.reps, args.n_frames)       # M windowed
        pf = measure(facts, args.N, ceiling, args.reps, args.n_frames)      # B1 full KV
        summary[name] = dict(
            N=args.N, reps=args.reps, budget_ms=round(budget_ms, 1),
            p99_windowed_ms=round(statistics.mean(pw), 2), windowed_95ci=ci95(pw),
            p99_fullkv_ms=round(statistics.mean(pf), 2), fullkv_95ci=ci95(pf),
            windowed_meets_budget=statistics.mean(pw) <= budget_ms,
            fullkv_meets_budget=statistics.mean(pf) <= budget_ms)
        s = summary[name]
        print(f"  M windowed p99 {s['p99_windowed_ms']}ms CI{s['windowed_95ci']} "
              f"(budget {s['budget_ms']}ms, meets={s['windowed_meets_budget']})", flush=True)
        print(f"  B1 full-KV  p99 {s['p99_fullkv_ms']}ms CI{s['fullkv_95ci']} "
              f"(meets={s['fullkv_meets_budget']})", flush=True)
    os.makedirs("results/engine", exist_ok=True)
    json.dump(summary, open("results/engine/timing_ci.json", "w"), indent=2)
    print("\nsaved results/engine/timing_ci.json")


if __name__ == "__main__":
    main()
