#!/bin/bash
set -u; cd "$(dirname "$0")/.."
# wait for the overnight API chain to finish (frees the GPU) before starting
until grep -q "OVERNIGHT API RUNS DONE" results/rt_overnight.log 2>/dev/null; do sleep 60; done
sleep 20
for cfg in "minicpm-o bf16 0.6" "minicpm-o fp8 0.6" "qwen-omni bf16 0.45"; do
  set -- $cfg; model="$1"; q="$2"; mem="$3"
  echo "###### decode-roofline $model/$q $(date +%H:%M:%S) ######"
  if [ "$q" = "fp8" ]; then QA="--quantization fp8"; else QA=""; fi
  python3 -u experiments/decode_roofline.py --model "$model" --gpu-mem "$mem" $QA \
    && echo "[$model/$q] OK" || echo "[$model/$q] FAILED"
  git add results/realtime_load/decode_roofline_* 2>/dev/null
  git commit -q -m "decode-roofline (real vLLM): $model/$q — per-step latency vs batch, compute ceiling" >/dev/null 2>&1 && git push -q origin main >/dev/null 2>&1 && echo "[commit] roofline $model/$q"
done
echo "ROOFLINE CHAIN DONE $(date +%H:%M:%S)"
