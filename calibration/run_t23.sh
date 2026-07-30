#!/usr/bin/env bash
# T2 and T3 each in a fresh engine process: T2 populates the prefix cache and
# fragments the KV pool, which contaminated T3's pure-decode baseline when they
# shared an engine (17.50ms vs the true 9.32ms).
set -u
cd "$(dirname "$0")/.."
MODEL=$(ls -d ~/.cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots/*/ | head -1)
COMMON="--model $MODEL --tag Qwen3-1.7B --iters 30 --warmup 25 --max-len 17000 --util 0.36 --kv-guard 0.92"
export VLLM_USE_V1=0 VLLM_LOGGING_LEVEL=ERROR CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-3}
for T in T2 T3; do
  echo "=== $T ==="
  .venv/bin/python calibration/run_calib_vllm.py $COMMON --tests "$T" || echo "$T FAILED"
done
echo "=== all done ==="
