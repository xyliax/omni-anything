#!/usr/bin/env bash
# Generic runner for the vLLM-0.23 omni experiments on Blackwell (SM120). Applies the runtime side of
# the fixes (CUDA_HOME = the venv's bundled cu13 nvcc, + NVCC_APPEND_FLAGS cccl bypass) and runs the
# given python script under the patched ~/vllm023-venv.
#   Usage: bash experiments/run_v023.sh experiments/<script>.py
# Companion source patches (in the venv, captured in patches/vllm_0.23_omni_blackwell.patch):
#   FIX 1 cu_seqlens device · FIX 2 capability gate · FIX 4 mrope reconcile (audio streaming).
set -euo pipefail
VENV="${VENV:-$HOME/vllm023-venv}"; CU13="$VENV/lib/python3.10/site-packages/nvidia/cu13"
export CUDA_HOME="$CU13" CUDA_PATH="$CU13" PATH="$CU13/bin:$PATH"
export NVCC_APPEND_FLAGS="-DCCCL_DISABLE_CTK_COMPATIBILITY_CHECK"
export VLLM_LOGGING_LEVEL="${VLLM_LOGGING_LEVEL:-WARNING}"
exec "$VENV/bin/python" -u "$1"
