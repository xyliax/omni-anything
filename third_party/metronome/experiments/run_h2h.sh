#!/bin/bash
set -u; cd "$(dirname "$0")/.."
rr(){ l="$1"; shift; for t in 1 2 3; do echo "=== [$l] try $t $(date +%H:%M:%S) ==="; "$@" && { echo "[$l] OK"; return; }; sleep 90; done; echo "[$l] GAVE UP"; }
while pgrep -f run_tier1b.sh >/dev/null; do sleep 60; done   # let quality+load (timing-sensitive) finish
echo "###### real-vLLM head-to-head (corrected) ######"
rr h2h-qwen    python3 -u experiments/vllm_headtohead.py --model qwen-omni --facts qwen3-omni --grid 1 2 4 8 16 24 32 48 64 96 --gpu-mem 0.35 --max-util 60
rr h2h-minicpm python3 -u experiments/vllm_headtohead.py --model minicpm-o --facts minicpm-o --grid 1 2 4 8 16 24 32 48 --gpu-mem 0.45 --max-util 60
echo "H2H DONE $(date +%H:%M:%S)"
