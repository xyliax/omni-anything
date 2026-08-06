#!/bin/bash
# SUSTAINED continuous full-duplex via the vLLM fd_step worker (server.py) — THE serving path for
# ALL omni models (MiniCPM-o-4.5, Qwen2.5-Omni-7B, Qwen3-Omni-30B-A3B-FP8). The HF-eager incremental
# backend was removed (slower + incorrect); only vLLM remains. NOTE: fd_step RE-ENCODES a windowed
# audio context each frame (WINDOW_S) -> WINDOWED-context full-duplex (8 s memory), since vLLM has no
# incremental mm-KV. Continuous 20ms chunks, latency bucketed by elapsed time + frame-delivery cadence.
# Path: client (sustained_fd.py, distinct phase-staggered streams) -> Go gateway -> gRPC -> vLLM.
set -u
cd "$(dirname "$0")/.."
export GOROOT=~/goroot/go PATH=~/goroot/go/bin:$PATH
MODEL="${MODEL:-openbmb/MiniCPM-o-4_5}"; PERIOD_MS="${PERIOD_MS:-1000}"; GPU_MEM="${GPU_MEM:-0.6}"
GRID="${1:-1 2 4 8 16 32}"; DUR="${DUR:-90}"; CHUNK_MS="${CHUNK_MS:-20}"
WINDOW_S="${WINDOW_S:-8}"; QUANT="${QUANT:-}"; TAG="${TAG:-vllm}"; MAXSEQS="${MAXSEQS:-320}"
STREAM="${STREAM:-0}"; MML="${MML:-6144}"; MAXCHUNKS="${MAXCHUNKS:-0}"
WREADY=/tmp/wready_sv.flag; rm -f $WREADY
QA=""; [ -n "$QUANT" ] && QA="--quantization $QUANT"
SA=""; [ "$STREAM" = "1" ] && SA="--streaming-sessions --max-ctx-chunks $MAXCHUNKS"
[ "${KVFP8:-0}" = "1" ] && SA="$SA --kv-fp8"
[ "${SWA:-0}" != "0" ] && SA="$SA --sliding-window-tokens ${SWA}"
echo "### [$(date +%H:%M:%S)] vLLM worker: $MODEL (period ${PERIOD_MS}ms, $([ "$STREAM" = 1 ] && echo "STREAMING-SESSIONS mml=${MML}" || echo "window=${WINDOW_S}s"), max_seqs ${MAXSEQS})"
setsid python3 -u worker/server.py --model "$MODEL" --port 50051 --gpu-mem "$GPU_MEM" \
  --max-model-len "$MML" --max-num-seqs "$MAXSEQS" --max-num-batched-tokens 16384 $QA $SA \
  --window-s "$WINDOW_S" --ready-file $WREADY > results/sustained_vllm_worker.log 2>&1 &
WK=$!
for i in $(seq 1 600); do
  [ -f $WREADY ] && break
  kill -0 $WK 2>/dev/null || { echo "WORKER DIED"; tail -15 results/sustained_vllm_worker.log; exit 1; }
  sleep 2
done
[ -f $WREADY ] || { echo "worker timeout"; exit 1; }
setsid ./gateway-go/gateway --port 8904 --worker 127.0.0.1:50051 --period-ms "$PERIOD_MS" --tpt 25 \
  > results/sustained_vllm_gw.log 2>&1 &
GW=$!
sleep 4
for N in $GRID; do
  echo "### [$(date +%H:%M:%S)] $MODEL N=$N sustained ${DUR}s @ ${CHUNK_MS}ms (windowed ${WINDOW_S}s)"
  SH=1; [ "$N" -ge 32 ] && SH=4; M=$((N / SH))
  python3 -u experiments/sustained_fd.py --uri ws://127.0.0.1:8904 --shards $SH --m $M \
    --duration "$DUR" --chunk-ms "$CHUNK_MS" --budget-ms "$PERIOD_MS" --tag "${TAG}_n${N}"
done
echo "### teardown"
kill -9 $GW 2>/dev/null; kill -9 -- -$WK 2>/dev/null
pkill -9 -f "worker/server.py" 2>/dev/null; pkill -9 -f "VLLM::EngineCore" 2>/dev/null
sleep 5
echo "SUSTAINED VLLM DONE ($(nvidia-smi --query-gpu=memory.used --format=csv,noheader))"
