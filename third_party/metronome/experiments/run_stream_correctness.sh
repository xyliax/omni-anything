#!/bin/bash
# Correctness under load for the streaming (append-to-resident-KV) worker: start the worker + gateway,
# run fd_correctness_probe (N sessions streaming KNOWN spoken questions, score answer-in-output), teardown.
# WINDOW=0 vanilla / >0 windowed-KV. Usage: WINDOW=15 N=96 DUR=75 bash experiments/run_stream_correctness.sh
set -u
cd "$(dirname "$0")/.."
export GOROOT=~/goroot/go PATH=~/goroot/go/bin:$PATH
VENV="${VENV:-$HOME/vllm023-venv}"; CU13="$VENV/lib/python3.10/site-packages/nvidia/cu13"
export CUDA_HOME="$CU13" CUDA_PATH="$CU13" PATH="$CU13/bin:$PATH"
export NVCC_APPEND_FLAGS="-DCCCL_DISABLE_CTK_COMPATIBILITY_CHECK" VLLM_LOGGING_LEVEL="${VLLM_LOGGING_LEVEL:-WARNING}"
MODEL="${MODEL:-sammysun0711/Qwen3-Omni-30B-A3B-Instruct-FP8-Dynamic}"
PERIOD_MS="${PERIOD_MS:-2000}"; GPU_MEM="${GPU_MEM:-0.85}"; MML="${MML:-8192}"; MAXSEQS="${MAXSEQS:-192}"
TPT="${TPT:-25}"; WINDOW="${WINDOW:-0}"; WINOV="${WINOV:-0}"; N="${N:-96}"; DUR="${DUR:-75}"; TURNEOS="${TURNEOS:-0}"
TAG="${TAG:-corr_$([ "$WINDOW" = 0 ] && echo vanilla || echo windowed)}"
WREADY=/tmp/wready_corr.flag; rm -f $WREADY
echo "### [$(date +%H:%M:%S)] correctness: $MODEL window=$WINDOW N=$N"
setsid "$VENV/bin/python" -u worker/stream_server.py --model "$MODEL" --port 50051 --gpu-mem "$GPU_MEM" \
  --max-model-len "$MML" --max-num-seqs "$MAXSEQS" --tpt "$TPT" --max-audio-chunks 64 \
  --window-frames "$WINDOW" --window-overlap "$WINOV" --turn-eos "$TURNEOS" --wait-budget-s 1.6 \
  --ready-file $WREADY > results/corr_worker.log 2>&1 &
for i in $(seq 1 360); do
  [ -f $WREADY ] && break
  grep -qE "EngineCore failed|Traceback|raise ValueError" results/corr_worker.log 2>/dev/null && { echo FATAL; tail -20 results/corr_worker.log|grep -avE "HTTP"; exit 1; }
  sleep 3
done
[ -f $WREADY ] || { echo timeout; exit 1; }
echo "### worker ready"
setsid ./gateway-go/gateway --port 8904 --worker 127.0.0.1:50051 --period-ms "$PERIOD_MS" --tpt "$TPT" \
  > results/corr_gw.log 2>&1 &
GW=$!; sleep 4
python3 -u experiments/fd_correctness_probe.py --uri ws://127.0.0.1:8904 --n-sessions "$N" \
  --duration "$DUR" --tag "$TAG"
kill -9 $GW 2>/dev/null
pkill -9 -f "worker/stream_server.py" 2>/dev/null; pkill -9 -f "VLLM::EngineCore" 2>/dev/null
sleep 4
echo "CORRECTNESS DONE ($(nvidia-smi --query-gpu=memory.used --format=csv,noheader))"
