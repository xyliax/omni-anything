#!/bin/bash
# Spoken-QA accuracy SOLO vs UNDER LOAD through the Go gateway (correctness verification).
set -u
cd "$(dirname "$0")/.."
export GOROOT=~/goroot/go PATH=~/goroot/go/bin:$PATH
MODEL="${MODEL:-Qwen/Qwen2.5-Omni-7B}"; PERIOD_MS="${PERIOD_MS:-2000}"; GPU_MEM="${GPU_MEM:-0.6}"
N="${N:-60}"; CONC="${CONC:-64}"
WREADY=/tmp/wready_q.flag; rm -f $WREADY
setsid python3 -u worker/server.py --model "$MODEL" --port 50051 --gpu-mem "$GPU_MEM" \
  --max-model-len 6144 --max-num-seqs 320 --max-num-batched-tokens 16384 \
  --ready-file $WREADY > results/qual_worker.log 2>&1 &
WK=$!
for i in $(seq 1 600); do [ -f $WREADY ] && break; kill -0 $WK 2>/dev/null || { echo "WORKER DIED"; tail -8 results/qual_worker.log; exit 1; }; sleep 2; done
setsid ./gateway-go/gateway --port 8904 --worker 127.0.0.1:50051 --period-ms "$PERIOD_MS" --tpt 25 \
  > results/qual_gw.log 2>&1 &
GW=$!
sleep 4
python3 -u experiments/quality_under_load.py --uri ws://127.0.0.1:8904 --n "$N" --conc "$CONC"
kill -9 $GW 2>/dev/null; kill -9 -- -$WK 2>/dev/null; pkill -9 -f "worker/server.py" 2>/dev/null
pkill -9 -f "VLLM::EngineCore" 2>/dev/null; sleep 4
echo "QUAL DONE ($(nvidia-smi --query-gpu=memory.used --format=csv,noheader))"
