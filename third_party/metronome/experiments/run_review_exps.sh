#!/bin/bash
# Review follow-up experiments (2026-07-02), run sequentially once the GPU frees:
#   EXP1 long-horizon quality probe (30B, N=32, 300 s; vanilla vs in-engine SWA 512/1024/2048)
#   EXP2 MiniCPM-o-4.5 300/600 s wall pair (second model for the core long-duration claim)
#   EXP3 windowed concurrency-ceiling mapping (SWA=1024, N=192/256; KV plateau linearity)
#   EXP4 randomized-order 20-run variance batch (replaces fixed-order 4/10 statistic)
# Never kills external jobs; reaps only our own GPU orphans between runs.
set -u
cd "$(dirname "$0")/.."
export GOROOT=~/goroot/go PATH=~/goroot/go/bin:$PATH
VENV="$HOME/vllm023-venv"; CU13="$VENV/lib/python3.10/site-packages/nvidia/cu13"
export CUDA_HOME="$CU13" CUDA_PATH="$CU13" PATH="$CU13/bin:$PATH"
export NVCC_APPEND_FLAGS="-DCCCL_DISABLE_CTK_COMPATIBILITY_CHECK" VLLM_LOGGING_LEVEL=WARNING
M30="sammysun0711/Qwen3-Omni-30B-A3B-Instruct-FP8-Dynamic"
OURS='*worker/stream_server.py*|*VLLM::EngineCore*|*worker/server.py*|*moshi_server*'

gpu_free_wait() {   # reap only OUR orphans (kill-list, not spare-list); wait for anyone else
  for i in $(seq 1 2880); do   # up to 24 h at 30 s cadence
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

worker_up() {  # MODEL GPU_MEM MML MAXSEQS PERIOD_MS SWA STATLOG LOGTAG
  rm -f /tmp/wready_rev.flag
  METRONOME_INENGINE_SWA="$6" METRONOME_STATLOG="$7" \
    setsid "$VENV/bin/python" -u worker/stream_server.py --model "$1" --port 50051 \
    --gpu-mem "$2" --max-model-len "$3" --max-num-seqs "$4" --tpt 25 --max-audio-chunks 64 \
    --window-frames 0 --wait-budget-s "$(python3 -c "print($5/1000.0*0.8)")" \
    --ready-file /tmp/wready_rev.flag > "results/rev_worker_$8.log" 2>&1 &
  for i in $(seq 1 360); do
    [ -f /tmp/wready_rev.flag ] && return 0
    grep -qE "EngineCore failed to start|CUDA out of memory|torch\.OutOfMemoryError|Engine core proc .* died" \
      "results/rev_worker_$8.log" 2>/dev/null && { echo "WORKER FATAL ($8)"; return 1; }
    sleep 3
  done
  echo "WORKER TIMEOUT ($8)"; return 1
}
gw_up() {  # PERIOD_MS
  setsid ./gateway-go/gateway --port 8904 --worker 127.0.0.1:50051 --period-ms "$1" --tpt 25 \
    --max-sessions 0 > results/rev_gw.log 2>&1 &
  sleep 4
}
teardown() {
  pkill -9 -f "gateway-go/gateway" 2>/dev/null
  pkill -9 -f "worker/stream_server.py" 2>/dev/null
  pkill -9 -f "VLLM::EngineCore" 2>/dev/null
  sleep 6
}

echo "##### EXP1 long-horizon quality ($(date)) #####"
# MML=16384: at N=32 a session's resident request grows ~30 tok/s, so 300 s needs ~9.2 K tokens.
# With MML=8192 the request hits the boundary at ~270 s and the ENGINE CRASHES (broadcast 8221 into
# 8192), killing every co-resident session -- see results/mml_boundary_crash.txt.
for SWA in 0 512 1024 2048; do
  gpu_free_wait || break
  TAG="lh_swa${SWA}"
  echo "### EXP1 condition SWA=$SWA ($(date +%H:%M:%S))"
  if worker_up "$M30" 0.85 16384 192 2000 "$SWA" "results/lh_stats_swa${SWA}.log" "$TAG"; then
    gw_up 2000
    python3 -u experiments/fd_longhorizon_probe.py --uri ws://127.0.0.1:8904 \
      --n-sessions 32 --tag "$TAG" 2>&1 | tee "results/lh_${TAG}.out"
  fi
  teardown
done
echo "##### EXP1 DONE ($(date)) #####"

echo "##### EXP2 MiniCPM-o-4.5 wall pair ($(date)) #####"
# 1 s frames, N=96, 600 s. GPU_MEM=0.7 / MML=16384 so pool exhaustion (if it comes) precedes
# max_model_len; the stat log records the KV trajectory either way.
for COND in "van 0" "win 1024"; do
  set -- $COND
  gpu_free_wait || break
  echo "### EXP2 MiniCPM $1 (SWA=$2) ($(date +%H:%M:%S))"
  export METRONOME_STATLOG="results/mcpm_stats_$1.log"
  MODEL="openbmb/MiniCPM-o-4_5" PERIOD_MS=1000 GPU_MEM=0.7 MML=16384 MAXSEQS=192 DUR=600 \
    INENGINE_SWA="$2" WINDOW=0 TAG="mcpm600_$1" bash experiments/run_stream_gateway.sh "96" \
    2>&1 | tee "results/mcpm600_$1.out"
  unset METRONOME_STATLOG
done
echo "##### EXP2 DONE ($(date)) #####"

echo "##### EXP3 windowed ceiling ($(date)) #####"
for N in 192 256; do
  gpu_free_wait || break
  echo "### EXP3 ceiling N=$N SWA=1024 ($(date +%H:%M:%S))"
  export METRONOME_STATLOG="results/ceil_stats_n${N}.log"
  MODEL="$M30" PERIOD_MS=2000 GPU_MEM=0.85 MML=8192 MAXSEQS=384 DUR=120 \
    INENGINE_SWA=1024 WINDOW=0 TAG="ceil_n${N}" bash experiments/run_stream_gateway.sh "$N" \
    2>&1 | tee "results/ceil_n${N}.out"
  unset METRONOME_STATLOG
done
echo "##### EXP3 DONE ($(date)) #####"

echo "##### EXP4 randomized variance ($(date)) #####"
SEED=20260702 bash experiments/run_variance_rand.sh 2>&1 | tee results/rvar_run.out
echo "##### ALL REVIEW EXPS DONE ($(date)) #####"
