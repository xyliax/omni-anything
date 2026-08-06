"""Serialize the real-model correctness work behind the running paper_models job.

paper_models is actively *measuring* per-tick latency to compute admission capacity, so
adding GPU load now would corrupt those numbers. This launcher waits for that job to
exit, then runs the two correctness benchmarks (token-match + multimodal coherence),
which depend on output *content*, not timing — so they gate on free memory, not idle
utilisation, and stay polite to co-tenants by keeping each run short.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def proc_alive(pat):
    r = subprocess.run(["pgrep", "-f", pat], capture_output=True, text=True)
    pids = [p for p in r.stdout.split() if p.strip()]
    # exclude our own pid / the pgrep
    me = str(os.getpid())
    return [p for p in pids if p != me]


def sh(cmd, label):
    print(f"\n{'='*70}\n[{time.strftime('%H:%M:%S')}] {label}\n$ {' '.join(cmd)}\n{'='*70}",
          flush=True)
    t0 = time.time()
    r = subprocess.run(cmd, cwd=ROOT)
    print(f"[{label}] exit={r.returncode} in {time.time()-t0:.0f}s", flush=True)
    return r.returncode


def main():
    py = sys.executable
    # 1. wait for paper_models to finish (clean timing for its capacity numbers)
    while True:
        alive = proc_alive("experiments/paper_models.py")
        if not alive:
            break
        print(f"[wait] paper_models still running (pids {alive}); checking again in 60s",
              flush=True)
        time.sleep(60)
    print("[wait] paper_models done — starting real correctness benchmarks", flush=True)

    # 2. text correctness — serving reproduces reference greedy (memory-gated, util-lenient)
    sh([py, "experiments/correctness_trace.py", "--max-util", "98"],
       "correctness: serving vs reference greedy")

    # 3. multimodal coherence — real audio + real image through the real models
    sh([py, "experiments/multimodal_real.py", "--need-free-gib", "26", "--max-util", "98"],
       "multimodal: real audio + vision coherence")

    print("\nReal correctness benchmarks complete. See results/correctness and results/multimodal.")


if __name__ == "__main__":
    main()
