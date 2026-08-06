#!/bin/bash
# Route A (faithful persistent-request) head-to-head, both models, with anchor + resident checks.
set -u
cd "$(dirname "$0")/.."
echo "###### MiniCPM-o (1000ms budget, 64 tok/frame) ######"
python3 -u experiments/vllm_headtohead.py --model minicpm-o --facts minicpm-o \
  --grid 1 2 4 8 16 32 48 64 --n-frames 30 --gpu-mem 0.45 --max-util 60 --anchor-ms 315
echo "###### Qwen-Omni (200ms budget, 25 tok/frame) ######"
python3 -u experiments/vllm_headtohead.py --model qwen-omni --facts qwen3-omni \
  --grid 1 2 4 8 16 32 48 --n-frames 30 --gpu-mem 0.35 --max-util 60 --anchor-ms 75
echo "H2H3 DONE $(date +%H:%M:%S)"
