#!/usr/bin/env bash
# Load + generate Qwen3-Omni-30B-A3B-FP8 on the PATCHED vLLM 0.23 venv on Blackwell (SM120).
# Bakes in the three fixes' runtime requirements:
#   - CUDA_HOME -> the venv's bundled cu13 toolkit (nvcc that targets sm_120)
#   - NVCC_APPEND_FLAGS=-DCCCL_DISABLE_CTK_COMPATIBILITY_CHECK  (FIX 3: bypass flashinfer's
#       bundled-cccl vs CUDA-13.2 header incompatibility check during JIT)
# FIX 1 (cu_seqlens) + FIX 2 (capability gate) are applied as source edits in ~/vllm023-venv
# (captured in patches/vllm_0.23_omni_blackwell.patch).
set -euo pipefail
VENV="${VENV:-$HOME/vllm023-venv}"
CU13="$VENV/lib/python3.10/site-packages/nvidia/cu13"
export CUDA_HOME="$CU13" CUDA_PATH="$CU13" PATH="$CU13/bin:$PATH"
export NVCC_APPEND_FLAGS="-DCCCL_DISABLE_CTK_COMPATIBILITY_CHECK"
exec "$VENV/bin/python" -u "$(dirname "$0")/v023_omni_smoke.py" "$@"
