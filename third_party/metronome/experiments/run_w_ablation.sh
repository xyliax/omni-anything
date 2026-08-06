#!/bin/bash
# Ablation: in-engine SWA window size W (tokens) vs per-frame latency/capacity, at fixed N.
# Each W = one worker load (SWA fixed at init). Through the real gateway, Qwen3-Omni-30B, 2s budget.
set -u
cd "$(dirname "$0")/.."
N="${N:-128}"; DUR="${DUR:-60}"
for W in ${1:-512 1024 2048 4096}; do
  echo "==================== in-engine SWA W=$W tokens, N=$N ===================="
  INENGINE_SWA="$W" WINDOW=0 DUR="$DUR" MAXSEQS=192 MML=8192 TAG="abl_w${W}" \
    bash experiments/run_stream_gateway.sh "$N"
  sleep 4
done
echo "==================== W ABLATION DONE ===================="