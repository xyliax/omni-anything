#!/bin/bash
# Online deadline-aware admission demo: worker + gateway (--online-admit), open-system ramp arrival.
# ONLINE_ADMIT=1 -> AIMD controller discovers N*; ONLINE_ADMIT=0 -> no admission (baseline collapse).
# Usage: ONLINE_ADMIT=1 NTOTAL=200 RATE=4 bash experiments/run_online_admit.sh
set -u
cd "$(dirname "$0")/.."
export GOROOT=~/goroot/go PATH=~/goroot/go/bin:$PATH
VENV="${VENV:-$HOME/vllm023-venv}"; CU13="$VENV/lib/python3.10/site-packages/nvidia/cu13"
export CUDA_HOME="$CU13" CUDA_PATH="$CU13" PATH="$CU13/bin:$PATH"
export NVCC_APPEND_FLAGS="-DCCCL_DISABLE_CTK_COMPATIBILITY_CHECK" VLLM_LOGGING_LEVEL="${VLLM_LOGGING_LEVEL:-WARNING}"
MODEL="${MODEL:-sammysun0711/Qwen3-Omni-30B-A3B-Instruct-FP8-Dynamic}"
PERIOD_MS="${PERIOD_MS:-2000}"; GPU_MEM="${GPU_MEM:-0.85}"; MML="${MML:-8192}"; MAXSEQS="${MAXSEQS:-256}"
TPT="${TPT:-25}"; INENGINE_SWA="${INENGINE_SWA:-0}"; NTOTAL="${NTOTAL:-200}"; RATE="${RATE:-4}"; DUR="${DUR:-75}"
ONLINE_ADMIT="${ONLINE_ADMIT:-1}"; ADMIT_TARGET="${ADMIT_TARGET:-0.5}"
TAG="${TAG:-ramp_$([ "$ONLINE_ADMIT" = 1 ] && echo admit || echo noadmit)}"
export METRONOME_INENGINE_SWA="$INENGINE_SWA"
WREADY=/tmp/wready_oa.flag; rm -f $WREADY
echo "### [$(date +%H:%M:%S)] online-admit demo: online=$ONLINE_ADMIT swa=$INENGINE_SWA offer=$NTOTAL rate=$RATE"
setsid "$VENV/bin/python" -u worker/stream_server.py --model "$MODEL" --port 50051 --gpu-mem "$GPU_MEM" \
  --max-model-len "$MML" --max-num-seqs "$MAXSEQS" --tpt "$TPT" --max-audio-chunks 64 \
  --window-frames 0 --wait-budget-s 1.6 --ready-file $WREADY > results/oa_worker.log 2>&1 &
for i in $(seq 1 360); do
  [ -f $WREADY ] && break
  grep -qE "EngineCore failed|Traceback|raise ValueError" results/oa_worker.log 2>/dev/null && { echo FATAL; tail -20 results/oa_worker.log|grep -avE HTTP; exit 1; }
  sleep 3
done
[ -f $WREADY ] || { echo timeout; exit 1; }
echo "### worker ready"
GWA=""; [ "$ONLINE_ADMIT" != "0" ] && GWA="--online-admit --admit-target $ADMIT_TARGET"
METRONOME_ADMITLOG="results/admit_trace_${TAG}.log" \
setsid ./gateway-go/gateway --port 8904 --worker 127.0.0.1:50051 --period-ms "$PERIOD_MS" --tpt "$TPT" $GWA \
  > results/oa_gw.log 2>&1 &
GW=$!; sleep 4
python3 -u experiments/fd_ramp.py --uri ws://127.0.0.1:8904 --n-total "$NTOTAL" --rate "$RATE" \
  --duration "$DUR" --budget-ms "$PERIOD_MS" --tag "$TAG"
kill -9 $GW 2>/dev/null
pkill -9 -f "worker/stream_server.py" 2>/dev/null; pkill -9 -f "VLLM::EngineCore" 2>/dev/null
sleep 4
echo "ONLINE-ADMIT DONE ($(nvidia-smi --query-gpu=memory.used --format=csv,noheader))"
