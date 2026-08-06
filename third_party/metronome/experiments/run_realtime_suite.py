"""Run the UNIFIED audio benchmark suite through the Realtime API, sequentially, on the
omni models (Qwen2.5-Omni, MiniCPM-o). Each stage waits for its own GPU window, runs to
completion (no self-contention), and writes results/realtime_bench/<model>__<task>__<ds>.json.

Moshi (the third model) runs separately in its own venv (run_moshi_suite via bench).
Same data, same scorer, so all three are comparable — and comparable to the papers.
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
    ap.add_argument("--models", nargs="*", default=["qwen-omni", "minicpm-o"])
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--port", type=int, default=8810)
    args = ap.parse_args()
    py = sys.executable
    # (task, dataset)
    stages = [("spoken-qa", "llama-questions"),
              ("spoken-qa", "spoken-web-questions"),
              ("asr", "librispeech")]
    port = args.port
    for model in args.models:
        gpu_mem = "0.28" if model == "qwen-omni" else "0.40"
        for task, ds in stages:
            port += 1
            sh([py, "experiments/bench_realtime.py", "--task", task, "--dataset", ds,
                "--model", model, "--n", str(args.n), "--need-free-gib", "26",
                "--max-util", "98", "--gpu-mem", gpu_mem, "--port", str(port)],
               f"{model} / {task} / {ds}")
    print("\nUnified audio suite (omni models) complete. See results/realtime_bench/.")


if __name__ == "__main__":
    main()
