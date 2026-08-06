"""Re-run every GPU performance benchmark **sequentially on a free GPU** for clean,
uncontended numbers. Each stage runs to completion before the next (no self-induced
contention); each stage's own window guard additionally waits if a co-tenant appears.

Order (foundational first):
  1. fit_cost_model   — the cost model (GATE B), high reps, uncontended.
  2. validate_sim     — held-out live-vs-sim (G5).
  3. engine_eval      — real MSCS / latency-vs-age / jitter (full cache, no 2.5 GiB cap).
  4. engine_kv        — real KV-budget essential-vs-complementary.
  5. engine_open      — real admission graceful-vs-cliff.
  6. live_multitenant — sim-vs-engine system validation.
  7. tight_deadline   — live CUDA-graph jitter.
Then refresh the CPU simulator sweeps with the clean cost model (run_all, no --gpu).
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sh(cmd, label):
    print(f"\n{'='*70}\n[{time.strftime('%H:%M:%S')}] {label}\n$ {' '.join(cmd)}\n{'='*70}",
          flush=True)
    t0 = time.time()
    r = subprocess.run(cmd, cwd=ROOT)
    print(f"[{label}] exit={r.returncode} in {time.time()-t0:.0f}s", flush=True)
    return r.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache-gib", type=float, default=40.0,
                    help="engine cache budget (large on a free GPU -> full onsets)")
    ap.add_argument("--reps", type=int, default=60)
    ap.add_argument("--skip-cpu", action="store_true")
    args = ap.parse_args()
    py = sys.executable

    sh([py, "experiments/fit_cost_model.py", "--reps", str(args.reps)],
       "1/7 cost-model fit (GATE B, clean)")
    sh([py, "experiments/validate_sim.py", "--reps", "40"],
       "2/7 held-out validation (G5)")
    sh([py, "experiments/engine_eval.py", "--n-frames", "25",
        "--max-cache-gib", str(args.cache_gib)],
       "3/7 real engine MSCS / latency-vs-age / jitter")
    sh([py, "experiments/engine_kv.py", "--n-frames", "15",
        "--max-cache-gib", str(args.cache_gib)],
       "4/7 real KV-budget (essential vs complementary)")
    sh([py, "experiments/engine_open.py", "--n-frames", "250"],
       "5/7 real open-system (admission vs greedy cliff)")
    sh([py, "experiments/live_multitenant.py", "--reps", "50"],
       "6/7 live multi-tenant (sim vs engine)")
    sh([py, "experiments/tight_deadline.py"],
       "7/7 live CUDA-graph jitter")

    if not args.skip_cpu:
        sh([py, "experiments/run_all.py"], "CPU refresh: simulator sweeps on clean cost model")
        sh([py, "experiments/run_sched.py"], "CPU refresh: scheduling/systems suite")

    print("\nAll clean-GPU benchmarks complete. Results refreshed under results/.")


if __name__ == "__main__":
    main()
