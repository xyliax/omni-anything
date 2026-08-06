#!/bin/bash
set -u; cd "$(dirname "$0")/.."
until grep -q "ROOFLINE CHAIN DONE" results/rt_roofline.log 2>/dev/null; do sleep 60; done
sleep 20
GRID="1 8 32 64 96 128 192 256"
export RESP_MAX=100 TURNS=1 WARMUP_TURNS=0 TRIM_TICKS=3
run(){ m="$1"; tag="$2"; tpt="$3"; mem="$4"; port="$5"; shift 5
  echo "###### FINAL $m/$tag $(date +%H:%M:%S) ######"
  bash experiments/run_realtime_bench.sh "$m" "$tag" "$tpt" "$mem" "$port" "$GRID" "$@" \
    && echo "[$m/$tag] OK" || echo "[$m/$tag] FAILED"
  git add results/realtime_load/ results/srv_*.log 2>/dev/null
  git commit -q -m "FINAL warmup-fixed real-API capacity: $m/$tag (per-N warmup, >=64 samples, CIs)" >/dev/null 2>&1 && git push -q origin main >/dev/null 2>&1 && echo "[commit] $m/$tag"
}
run minicpm-o  minicpm_final  25 0.6  8870
run qwen-omni  qwen_final     25 0.45 8871
run qwen-omni  qwen_fp8_final 25 0.45 8872 --quantization fp8
echo "RT FINAL DONE $(date +%H:%M:%S)"
