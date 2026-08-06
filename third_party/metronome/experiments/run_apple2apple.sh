#!/bin/bash
# APPLE-TO-APPLE concurrency comparison of the two deployable full-duplex serving paths, through the
# IDENTICAL stack (same real clients = sustained_fd.py distinct phase-staggered streams, same Go
# gateway, same gRPC worker, same model, same N grid, same metrics):
#
#   WINDOWED  (previous)         : fd_step  — re-encode an 8 s audio window each frame   (STREAM=0)
#   STREAMING (resident-context) : fd_step_stream — append new chunk to a growing        (STREAM=1)
#                                  resident context, reuse encoder/KV via caches
#
# Only the worker compute path differs (one flag); everything else is byte-identical -> apple-to-apple.
set -u
cd "$(dirname "$0")/.."
export MODEL="${MODEL:-sammysun0711/Qwen3-Omni-30B-A3B-Instruct-FP8-Dynamic}"
export PERIOD_MS="${PERIOD_MS:-2000}" GPU_MEM="${GPU_MEM:-0.85}" MML="${MML:-8192}"
export DUR="${DUR:-60}" MAXSEQS="${MAXSEQS:-128}"
GRID="${1:-1 4 8 16 32 64}"

echo "==================== A2A: WINDOWED (previous, fd_step 8s) ===================="
STREAM=0 TAG=a2a_win bash experiments/run_sustained_vllm.sh "$GRID"
sleep 6
echo "==================== A2A: STREAMING (resident-context, fd_step_stream) ===================="
STREAM=1 MAXCHUNKS=0 TAG=a2a_str bash experiments/run_sustained_vllm.sh "$GRID"
echo "==================== A2A DONE ===================="
python3 experiments/a2a_summary.py "$GRID"
