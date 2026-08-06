#!/bin/bash
# Remaining REAL Realtime-API runs, small-N-up grid, RESPONSIVE-capacity (TTFA) focus.
# All real silicon: real vLLM, real audio, N concurrent WebSocket clients, vLLM continuous
# batching + chunked prefill (prefill batched) + CUDA graphs (decode batched). FP8 speeds
# prefill -> may raise responsive capacity. Each group commits.
set -u
cd "$(dirname "$0")/.."
P=8830
GRID="1 2 4 8 16 32 48 64 96 128"
COMMON="--tpt 25 --turns 1 --response-tokens 200 --audio-clips 128 --max-util 80 --slo 0.05 --max-num-batched-tokens 16384"

run(){ label="$1"; model="$2"; mem="$3"; tpt="$4"; shift 4; P=$((P+1))
  echo "###### $label  ($(date +%H:%M:%S)) ######"
  python3 -u experiments/realtime_load.py --model "$model" --grid $GRID --gpu-mem "$mem" \
    --tpt "$tpt" --turns 1 --response-tokens 200 --audio-clips 128 --max-util 80 --slo 0.05 \
    --max-num-batched-tokens 16384 --port $P "$@" && echo "[$label] OK" || echo "[$label] FAILED"; }
commit(){ git add results/realtime_load/ 2>/dev/null; git commit -q -m "$1" >/dev/null 2>&1 && git push -q origin main >/dev/null 2>&1 && echo "[commit] $1"; }

# MiniCPM FP8 weights (speeds prefill+decode -> responsive-capacity impact)
run "minicpm-fp8w"  minicpm-o 0.6 25 --quantization fp8
commit "Phase 2: MiniCPM-o FP8 weights, real API, responsive-capacity (TTFA) sweep"

# Qwen-Omni: 200ms period -> TTFA floor ~0.4s, MoE A3B decode. tpt=25 output/200ms.
run "qwen-baseline" qwen-omni 0.45 25
commit "Phase 1: Qwen-Omni real-API responsive-capacity sweep (baseline)"
run "qwen-fp8w"     qwen-omni 0.45 25 --quantization fp8
commit "Phase 2: Qwen-Omni FP8 weights real-API sweep"

echo "REMAINING SWEEP DONE $(date +%H:%M:%S)"
