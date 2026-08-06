#!/usr/bin/env bash
# Run the streaming-session benchmark (append-to-resident-KV vs re-submit) on the patched vLLM 0.23.
# Same env as run_v023_omni_smoke.sh (FIX 1/2 are source edits in the venv; FIX 3 is these env vars).
set -euo pipefail
VENV="${VENV:-$HOME/vllm023-venv}"
CU13="$VENV/lib/python3.10/site-packages/nvidia/cu13"
export CUDA_HOME="$CU13" CUDA_PATH="$CU13" PATH="$CU13/bin:$PATH"
export NVCC_APPEND_FLAGS="-DCCCL_DISABLE_CTK_COMPATIBILITY_CHECK"
export VLLM_LOGGING_LEVEL="${VLLM_LOGGING_LEVEL:-WARNING}"
exec "$VENV/bin/python" -u "$(dirname "$0")/v023_streaming_session.py" "$@"
