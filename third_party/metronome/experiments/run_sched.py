"""Run the scheduling + systems research suite (tasks B–H, CPU-only). The live
multi-tenant validation (task A) is GPU-bound — run experiments/live_multitenant.py
separately (it waits for a clean GPU window)."""
from __future__ import annotations

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sh(cmd):
    print(f"\n$ {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True, cwd=ROOT)


def main():
    py = sys.executable
    for stage in ("subbatching",            # B + D: temporal sub-batching
                  "coaging_safe",           # C: co-aging-safe admission
                  "heterogeneous_period",   # E: hyperperiod co-serving
                  "admission_cost",         # F: incremental O(1) admission
                  "multigpu",               # G: placement + migration
                  "dvfs",                   # H: deadline-aware DVFS
                  "paged_kv"):              # H: paged vs contiguous KV
        sh([py, f"experiments/{stage}.py"])
    print("\nScheduling/systems suite complete. See results/{subbatch,coaging_safe,"
          "hetperiod,admission_cost,multigpu,dvfs,paged}/ and RESULTS_SCHED.md")


if __name__ == "__main__":
    main()
