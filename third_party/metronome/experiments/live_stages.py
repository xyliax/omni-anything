"""Run the GPU-bound live confirmation stages, patiently and crash-safe.

These confirm (not establish) results that the cost-model fit already grounds:
  * validate_sim: held-out live-vs-simulator cost (G5 closure).
  * tight_deadline live jitter: CUDA-graph vs eager p999 tail (S7).

Both wait politely for a free GPU window (up to 90 min) and skip gracefully if the
shared GPU never frees, so a busy neighbour never crashes the run.
"""
from __future__ import annotations

import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiments import validate_sim, tight_deadline
from experiments._common import all_models


def safe(label, fn):
    try:
        fn()
        print(f"[live_stages] {label}: OK")
    except TimeoutError as e:
        print(f"[live_stages] {label}: SKIPPED (no GPU window) — {e}")
    except Exception:
        print(f"[live_stages] {label}: FAILED")
        traceback.print_exc()


def main():
    names = all_models()
    for name in names:
        safe(f"validate_sim:{name}", lambda n=name: validate_sim.run(n, reps=30))
    safe("tight_deadline jitter (moshi)", _tight)


def _tight():
    # run tight_deadline with live jitter on moshi only (the 80 ms regime)
    sys.argv = ["tight_deadline.py", "--live-model", "moshi", "--reps", "200"]
    tight_deadline.main()


if __name__ == "__main__":
    main()
