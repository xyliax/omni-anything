#!/bin/bash
# Sink-retention follow-up (2026-07-02): re-run the long-horizon quality probe with
# StreamingLLM-style attention sinks retained inside the in-engine sliding window.
#   COND lh_sink32    SWA=1024 + SINK=32  (Triton unified-attention kernel)
#   COND lh_tri0      SWA=1024 + SINK=0 forced onto the SAME Triton kernel (backend control:
#                     isolates the sink effect from the FA->Triton backend change)
# Fresh worker per condition (Appendix "fresh worker per point"). Never kills external jobs.
set -u
cd "$(dirname "$0")/.."
export GOROOT=~/goroot/go PATH=~/goroot/go/bin:$PATH
VENV="$HOME/vllm023-venv"; CU13="$VENV/lib/python3.10/site-packages/nvidia/cu13"
export CUDA_HOME="$CU13" CUDA_PATH="$CU13" PATH="$CU13/bin:$PATH"
export NVCC_APPEND_FLAGS="-DCCCL_DISABLE_CTK_COMPATIBILITY_CHECK" VLLM_LOGGING_LEVEL=WARNING
M30="sammysun0711/Qwen3-Omni-30B-A3B-Instruct-FP8-Dynamic"
OURS='*worker/stream_server.py*|*VLLM::EngineCore*|*worker/server.py*|*moshi_server*'

gpu_free_wait() {   # reap only OUR orphans; wait for anyone else
  for i in $(seq 1 2880); do
    for pid in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null); do
      cl=$(tr '\0' ' ' < /proc/$pid/cmdline 2>/dev/null)
      case "$cl" in $OURS) kill -9 "$pid" 2>/dev/null ;; *) : ;; esac
    done
    pkill -9 -f "worker/stream_server.py" 2>/dev/null
    u=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1 | tr -d ' ')
    [ "${u:-99999}" -lt 4000 ] && { sleep 8; return 0; }
    [ $((i % 20)) -eq 0 ] && echo "  [wait] GPU busy ${u} MiB ($(date +%H:%M))"
    sleep 30
  done
  echo "  [wait] GPU never freed; aborting stage"; return 1
}

worker_up() {  # SWA SINK TRITON STATLOG LOGTAG
  rm -f /tmp/wready_sink.flag
  METRONOME_INENGINE_SWA="$1" METRONOME_SWA_SINK="$2" METRONOME_SWA_TRITON="$3" \
  METRONOME_STATLOG="$4" \
    setsid "$VENV/bin/python" -u worker/stream_server.py --model "$M30" --port 50051 \
    --gpu-mem 0.85 --max-model-len 16384 --max-num-seqs 192 --tpt 25 --max-audio-chunks 64 \
    --window-frames 0 --wait-budget-s 1.6 \
    --ready-file /tmp/wready_sink.flag > "results/sink_worker_$5.log" 2>&1 &
  for i in $(seq 1 360); do
    [ -f /tmp/wready_sink.flag ] && return 0
    grep -qE "EngineCore failed to start|CUDA out of memory|torch\.OutOfMemoryError|Engine core proc .* died" \
      "results/sink_worker_$5.log" 2>/dev/null && { echo "WORKER FATAL ($5)"; return 1; }
    sleep 3
  done
  echo "WORKER TIMEOUT ($5)"; return 1
}
gw_up() {
  setsid ./gateway-go/gateway --port 8904 --worker 127.0.0.1:50051 --period-ms 2000 --tpt 25 \
    --max-sessions 0 > results/sink_gw.log 2>&1 &
  sleep 4
}
teardown() {
  pkill -9 -f "gateway-go/gateway" 2>/dev/null
  pkill -9 -f "worker/stream_server.py" 2>/dev/null
  pkill -9 -f "VLLM::EngineCore" 2>/dev/null
  sleep 6
}

# Conditions: "TAG SWA SINK FORCE_TRITON", from argv if given (sweep mode),
# else the original pair (full bound + zero-sink kernel control).
CONDS=("$@")
[ ${#CONDS[@]} -eq 0 ] && CONDS=("lh_sink32 1024 32 0" "lh_tri0 1024 0 1")
for COND in "${CONDS[@]}"; do
  set -- $COND
  TAG="$1"; SWA="$2"; SINK="$3"; TRI="$4"
  gpu_free_wait || break
  echo "### sink-exp condition $TAG (SWA=$SWA SINK=$SINK TRITON=$TRI) ($(date +%H:%M:%S))"
  if worker_up "$SWA" "$SINK" "$TRI" "results/sink_stats_${TAG}.log" "$TAG"; then
    gw_up
    python3 -u experiments/fd_longhorizon_probe.py --uri ws://127.0.0.1:8904 \
      --n-sessions 32 --tag "$TAG" 2>&1 | tee "results/${TAG}.out"
  fi
  teardown
done
echo "##### SINK EXPS DONE ($(date)) #####"
