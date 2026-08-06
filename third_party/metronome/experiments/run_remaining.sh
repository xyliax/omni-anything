#!/bin/bash
# Remaining experiments: (1) serving-correctness token-match trace (small model, fits
# small windows), (2) clean-GPU performance re-run — which needs an UNCONTENDED GPU for
# valid timing, so it waits for a genuinely idle window (high bar) rather than producing
# contended numbers. Both retry.
set -u
cd "$(dirname "$0")/.."
run_retry() { label="$1"; shift
  for try in 1 2 3 4 5; do
    echo "=== [$label] try $try $(date +%H:%M:%S): $* ==="
    "$@" && { echo "[$label] OK"; return 0; }
    echo "[$label] failed try $try; sleeping 120s"; sleep 120
  done; echo "[$label] GAVE UP"; }

# (1) correctness: periodic-session serving reproduces a trusted greedy reference
run_retry correctness python3 -u experiments/correctness_trace.py --max-util 100 --need-free-gib 6

# (2) clean performance re-run — only meaningful on an idle GPU. run_gpu_clean's stages
# each wait for their own window; we additionally hold for a low-util, high-free window
# first so the cost-model/MSCS timing isn't corrupted by a co-tenant.
echo "=== [perf-rerun] waiting for a genuinely idle GPU (>=80GiB, util<=25) $(date +%H:%M:%S) ==="
python3 - <<'PY'
import sys; sys.path.insert(0,".")
from bench.gpu_probe import wait_for_window
try:
    wait_for_window(need_free_gib=80, max_util_pct=25, timeout_s=72000)  # up to 20h
    print("idle window open -> running clean perf suite")
except Exception as e:
    print(f"no idle window within budget ({e}); skipping clean perf re-run")
    sys.exit(3)
PY
if [ $? -eq 0 ]; then
  run_retry perf-rerun python3 -u experiments/run_gpu_clean.py
fi
echo "REMAINING DONE $(date +%H:%M:%S)"
