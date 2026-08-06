#!/bin/bash
# Overnight: remaining REAL end-to-end Realtime-API capacity runs (separate-process, turns=1 =
# clean TTFA, bootstrap CIs). Each commits. Tests Qwen (200ms period) + FP8 (faster prefill ->
# should raise the admission/responsive capacity).
set -u
cd "$(dirname "$0")/.."
GRID="1 8 32 64 96 128 192 256"
export RESP_MAX=100 TURNS=1 WARMUP_TURNS=0 TRIM_TICKS=3

run(){ # model tag tpt mem port extra...
  m="$1"; tag="$2"; tpt="$3"; mem="$4"; port="$5"; shift 5
  echo "###### $m/$tag $(date +%H:%M:%S) ######"
  bash experiments/run_realtime_bench.sh "$m" "$tag" "$tpt" "$mem" "$port" "$GRID" "$@" \
    && echo "[$m/$tag] OK" || echo "[$m/$tag] FAILED"
  git add results/realtime_load/ results/srv_*.log 2>/dev/null
  git commit -q -m "real-API capacity: $m/$tag (separate-process, TTFA + CIs)" >/dev/null 2>&1 \
    && git push -q origin main >/dev/null 2>&1 && echo "[commit] $m/$tag"
}

run qwen-omni  qwen_bf16     25 0.45 8860
run minicpm-o  minicpm_fp8w  25 0.6  8861 --quantization fp8
run qwen-omni  qwen_fp8w     25 0.45 8862 --quantization fp8
echo "OVERNIGHT API RUNS DONE $(date +%H:%M:%S)"
