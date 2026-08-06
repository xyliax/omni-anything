#!/bin/bash
# End-to-end audio-only + audio+vision concurrency/TTFA sweep through the Go gateway.
# Usage: MODEL=... PERIOD_MS=... WORKER=server|streaming experiments/run_cap.sh <tag> "<grid>" <modes>
#   modes: "audio", "vision", or "audio vision" (default)
set -u
cd "$(dirname "$0")/.."
export GOROOT=~/goroot/go PATH=~/goroot/go/bin:$PATH
TAG="${1:-cap}"; GRID="${2:-1 8 32 64 96 128}"; MODES="${3:-audio vision}"
MODEL="${MODEL:-Qwen/Qwen2.5-Omni-7B}"
PERIOD_MS="${PERIOD_MS:-2000}"; GPU_MEM="${GPU_MEM:-0.6}"; QUANT="${QUANT:-}"
QA_S="${QA_S:-3}"; IMG_PX="${IMG_PX:-448}"; MAXTOK="${MAXTOK:-48}"; TURNS="${TURNS:-2}"
SLO="${SLO:-0.05}"; TTFA_SLO="${TTFA_SLO:-4000}"; ARRIVAL="${ARRIVAL:-2.0}"
WREADY=/tmp/wready_cap.flag; rm -f $WREADY
QARG=""; [ -n "$QUANT" ] && QARG="--quantization $QUANT"

echo "### [$(date +%H:%M:%S)] worker: $MODEL (period ${PERIOD_MS}ms, gpu ${GPU_MEM}${QUANT:+, $QUANT})"
setsid python3 -u worker/server.py --model "$MODEL" --port 50051 --gpu-mem "$GPU_MEM" \
  --max-model-len 6144 --max-num-seqs 320 --max-num-batched-tokens 16384 $QARG \
  --ready-file $WREADY > results/cap_worker.log 2>&1 &
WK=$!
for i in $(seq 1 600); do
  [ -f $WREADY ] && break
  kill -0 $WK 2>/dev/null || { echo "WORKER DIED"; tail -12 results/cap_worker.log; exit 1; }
  sleep 2
done
[ -f $WREADY ] || { echo "worker timeout"; tail -12 results/cap_worker.log; kill -9 -- -$WK; exit 1; }
echo "### worker ready; starting gateway"
setsid ./gateway-go/gateway --port 8904 --worker 127.0.0.1:50051 --period-ms "$PERIOD_MS" --tpt 25 \
  > results/cap_gw.log 2>&1 &
GW=$!
sleep 4
RC=0
for MODE in $MODES; do
  echo "### [$(date +%H:%M:%S)] sweep mode=$MODE grid=[$GRID]"
  python3 -u experiments/e2e_capacity.py --uri ws://127.0.0.1:8904 --mode "$MODE" \
    --grid $GRID --q-audio-s "$QA_S" --img-px "$IMG_PX" --max-tokens "$MAXTOK" \
    --budget-ms "$PERIOD_MS" --turns "$TURNS" --slo "$SLO" --ttfa-slo-ms "$TTFA_SLO" \
    --arrival-window-s "$ARRIVAL" --tag "$TAG" || RC=$?
done
echo "### teardown"
kill -9 $GW 2>/dev/null
kill -9 -- -$WK 2>/dev/null
pkill -9 -f "worker/server.py" 2>/dev/null
pkill -9 -f "VLLM::EngineCore" 2>/dev/null   # vLLM spawns a separate engine-core process
sleep 5
echo "CAP DONE rc=$RC ($(nvidia-smi --query-gpu=memory.used --format=csv,noheader))"
