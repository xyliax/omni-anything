#!/usr/bin/env bash
# Definitive calibration run. Each test gets a FRESH engine process: sharing
# one engine let T2's prefix-cached blocks distort T3's baseline (17.5ms vs
# the true 9.2ms for B=4/ctx=4k).
set -u
cd /home/yuxing/omni-anything
MODEL=$(ls -d ~/.cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots/*/ | head -1)
TAG=${TAG:-Qwen3-1.7B}
GPU=${GPU:-3}
UTIL=${UTIL:-0.36}
MAXLEN=${MAXLEN:-17000}
export VLLM_USE_V1=0 VLLM_LOGGING_LEVEL=ERROR CUDA_VISIBLE_DEVICES=$GPU
PY=.venv/bin/python

for T in T1 T2 T3; do
  echo "=== $T (fresh engine) $(date +%T) ==="
  $PY calibration/run_calib_vllm.py --model "$MODEL" --tag "$TAG" \
      --tests $T --iters 30 --warmup 8 --max-len $MAXLEN --util $UTIL \
      --kv-guard 0.92
done

echo "=== T4 (engine per chunk size) $(date +%T) ==="
$PY calibration/run_calib_vllm.py --model "$MODEL" --tag "$TAG" \
    --tests T4 --iters 12 --max-len $MAXLEN --util $UTIL
echo "=== ALL DONE $(date +%T) ==="
