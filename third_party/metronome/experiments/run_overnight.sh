#!/bin/bash
# Autonomous overnight runner: vision (VQA) on both omni models, then tau-interact on
# MiniCPM-o, then a Qwen3-8B-user-sim tau-interact re-run. Each stage retries to survive
# the shared GPU's memory thrashing. Everything is GPU-polite (memory-gated windows).
cd "$(dirname "$0")/.."
run_retry() { label="$1"; shift
  for try in 1 2 3 4 5; do
    echo "=== [$label] try $try $(date +%H:%M:%S): $* ==="
    "$@" && { echo "[$label] OK"; return 0; }
    echo "[$label] failed try $try; sleeping 90s"; sleep 90
  done
  echo "[$label] GAVE UP"; }

run_retry vqa-qwen   python3 -u experiments/bench_realtime.py --task vqa --dataset mmstar \
  --model qwen-omni --n 40 --gpu-mem 0.28 --max-util 100 --port 8851
run_retry vqa-minicpm python3 -u experiments/bench_realtime.py --task vqa --dataset mmstar \
  --model minicpm-o --n 40 --gpu-mem 0.42 --max-util 100 --port 8852
run_retry tau-minicpm python3 -u experiments/run_tau_interact.py --agents minicpm-o \
  --agent-mem 0.42
run_retry tau-qwen8b  python3 -u experiments/run_tau_interact.py --agents qwen-omni \
  --usersim-model Qwen/Qwen3-8B --usersim-mem 0.20 --agent-mem 0.28
echo "OVERNIGHT VISION+INTERACT DONE $(date +%H:%M:%S)"
