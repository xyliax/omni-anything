#!/bin/bash
# SUSTAINED continuous full-duplex through the REAL gateway, served by the vLLM-0.23 STREAMING
# (append-to-resident-KV) worker. Identical client/gateway/metrics path as run_sustained_vllm.sh
# (which serves the windowed fd_step worker) -> apple-to-apple, but the worker is the true-append one.
#   client (sustained_fd.py, distinct phase-staggered) -> Go gateway -> gRPC -> stream_server.py (0.23)
set -u
cd "$(dirname "$0")/.."
export GOROOT=~/goroot/go PATH=~/goroot/go/bin:$PATH
VENV="${VENV:-$HOME/vllm023-venv}"; CU13="$VENV/lib/python3.10/site-packages/nvidia/cu13"
export CUDA_HOME="$CU13" CUDA_PATH="$CU13" PATH="$CU13/bin:$PATH"
export NVCC_APPEND_FLAGS="-DCCCL_DISABLE_CTK_COMPATIBILITY_CHECK" VLLM_LOGGING_LEVEL="${VLLM_LOGGING_LEVEL:-WARNING}"

MODEL="${MODEL:-sammysun0711/Qwen3-Omni-30B-A3B-Instruct-FP8-Dynamic}"
PERIOD_MS="${PERIOD_MS:-2000}"; GPU_MEM="${GPU_MEM:-0.85}"; MML="${MML:-8192}"
GRID="${1:-1 4 8 16 32}"; DUR="${DUR:-60}"; CHUNK_MS="${CHUNK_MS:-20}"; TAG="${TAG:-a2a_stream023}"
MAXSEQS="${MAXSEQS:-128}"; TPT="${TPT:-25}"; MAXCHUNKS="${MAXCHUNKS:-64}"
WINDOW="${WINDOW:-0}"   # app-level windowed-KV (frames, request-recycling proxy); 0 = off
WINOV="${WINOV:-0}"     # sliding-window overlap (carryover frames); 0 = W//2
MAXSESS="${MAXSESS:-0}" # Metronome admission cap (gateway rejects sessions beyond it); 0 = unlimited
INENGINE_SWA="${INENGINE_SWA:-0}"  # IN-ENGINE windowed KV: sliding window in TOKENS (vLLM frees blocks); 0 = off
export METRONOME_INENGINE_SWA="$INENGINE_SWA"   # patch guards 0 as a no-op
WREADY=/tmp/wready_stream023.flag; rm -f $WREADY

echo "### [$(date +%H:%M:%S)] vLLM-0.23 STREAMING worker: $MODEL (period ${PERIOD_MS}ms, append-to-resident-KV, max_seqs ${MAXSEQS})"
setsid "$VENV/bin/python" -u worker/stream_server.py --model "$MODEL" --port 50051 --gpu-mem "$GPU_MEM" \
  --max-model-len "$MML" --max-num-seqs "$MAXSEQS" --tpt "$TPT" --max-audio-chunks "$MAXCHUNKS" \
  --window-frames "$WINDOW" --window-overlap "$WINOV" \
  --wait-budget-s "${WAITBUDGET:-$(python3 -c "print(${PERIOD_MS}/1000.0*0.8)")}" \
  --ready-file $WREADY > results/stream023_worker.log 2>&1 &
# Poll the ready-file (model load + JIT + CUDA-graph + warmup can take a few minutes); bail only on a
# real fatal in the log (don't trust pgrep against a setsid grandchild).
for i in $(seq 1 360); do
  [ -f $WREADY ] && break
  if grep -qE "EngineCore failed to start|Engine core initialization failed|CUDA out of memory|torch\.OutOfMemoryError|Engine core proc .* died" results/stream023_worker.log 2>/dev/null; then
    echo "WORKER FATAL"; tail -30 results/stream023_worker.log | grep -vE "HTTP Request|it/s\]$|Capturing|Loading safetensors"; exit 1
  fi
  sleep 3
done
[ -f $WREADY ] || { echo "worker timeout"; tail -25 results/stream023_worker.log; exit 1; }
echo "### [$(date +%H:%M:%S)] worker ready"
GWADMIT=""; [ "${ONLINE_ADMIT:-0}" != "0" ] && GWADMIT="--online-admit --admit-target ${ADMIT_TARGET:-0.7}"
setsid ./gateway-go/gateway --port 8904 --worker 127.0.0.1:50051 --period-ms "$PERIOD_MS" --tpt "$TPT" \
  --max-sessions "$MAXSESS" $GWADMIT \
  > results/stream023_gw.log 2>&1 &
GW=$!
sleep 4
for N in $GRID; do
  echo "### [$(date +%H:%M:%S)] $MODEL N=$N sustained ${DUR}s @ ${CHUNK_MS}ms (STREAMING append-to-resident-KV)"
  SH=1; [ "$N" -ge 32 ] && SH=4; M=$((N / SH))
  python3 -u experiments/sustained_fd.py --uri ws://127.0.0.1:8904 --shards $SH --m $M \
    --duration "$DUR" --chunk-ms "$CHUNK_MS" --budget-ms "$PERIOD_MS" --tag "${TAG}_n${N}"
done
echo "### teardown"
kill -9 $GW 2>/dev/null
pkill -9 -f "worker/stream_server.py" 2>/dev/null; pkill -9 -f "VLLM::EngineCore" 2>/dev/null
sleep 5
echo "STREAM023 GATEWAY SWEEP DONE ($(nvidia-smi --query-gpu=memory.used --format=csv,noheader))"
