"""Run the production experiment suite (docs/PRODUCTION.md). CPU-only (the cost
model must already be fitted via experiments/fit_cost_model.py)."""
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
    for stage in ("open_system_eval", "co_aging", "conversation",
                  "heterogeneous", "adaptive_budget"):
        sh([py, f"experiments/{stage}.py"])
    print("\nProduction suite complete. See results/{open,coaging,conversation,"
          "hetero,adaptive}/ and RESULTS_PROD.md")


if __name__ == "__main__":
    main()
