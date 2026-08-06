"""Master orchestration: run the full downstream pipeline.

CPU-only stages (simulator-driven) run unconditionally. GPU stages (cost-model fit,
sim validation, live jitter) are gated behind --gpu and the shared-GPU window guard.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sh(cmd):
    print(f"\n$ {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True, cwd=ROOT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu", action="store_true", help="also run GPU stages")
    ap.add_argument("--fit", action="store_true", help="(re)fit the cost model on GPU")
    args = ap.parse_args()
    py = sys.executable

    if args.gpu and args.fit:
        sh([py, "experiments/fit_cost_model.py"])
    if args.gpu:
        sh([py, "experiments/validate_sim.py"])

    sh([py, "experiments/establish_problem.py"])      # S2 GATE A
    sh([py, "experiments/core_eval.py"])              # S5
    sh([py, "experiments/kv_eviction.py"])            # S6
    sh([py, "experiments/admission_validation.py"])   # G5 + graceful/cliff
    sh([py, "experiments/edf_fairness.py"])           # EDF differentiation
    sh([py, "experiments/ablations.py"])              # S8
    sh([py, "experiments/projection.py"])             # S10
    sh([py, "experiments/hardware_sensitivity.py"])   # A100/H100/GH200 projection

    if args.gpu:
        sh([py, "experiments/tight_deadline.py"])     # S7 (live jitter)
    else:
        sh([py, "experiments/tight_deadline.py", "--no-live"])

    sh([py, "experiments/leaderboard.py"])            # S9 leaderboard

    # production suite (docs/PRODUCTION.md) — open-system, churn, co-aging, etc.
    sh([py, "experiments/run_prod.py"])

    # scheduling + scalability + systems suite (RESULTS_SCHED.md, tasks B-H)
    sh([py, "experiments/run_sched.py"])
    if args.gpu:
        sh([py, "experiments/live_multitenant.py"])   # task A (needs a clean GPU window)
        # REAL serving engine — the headline capacity numbers (RESULTS_ENGINE.md)
        sh([py, "experiments/engine_eval.py", "--max-cache-gib", "2.5"])
        sh([py, "experiments/engine_kv.py"])
        sh([py, "experiments/engine_open.py"])

    print("\nAll stages complete. See RESULTS_ENGINE.md (real engine), RESULTS.md, "
          "RESULTS_PROD.md, RESULTS_SCHED.md, results/LEADERBOARD.md.")


if __name__ == "__main__":
    main()
