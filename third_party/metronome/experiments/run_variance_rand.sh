#!/bin/bash
# RANDOMIZED-ORDER variance batch (review follow-up #2).
# Same 20 runs as run_variance.sh (5 x {vanilla,in-engine} x {N=96,128}, 300 s, fresh worker per
# run) but executed in a SHUFFLED order, so a slowly varying environmental factor cannot align with
# one policy. The original fixed-order batch put all 4 vanilla walls in the chronologically first 4
# vanilla runs; this batch tests whether the ~40% tip rate survives randomization.
set -u
cd "$(dirname "$0")/.."
export MODEL="sammysun0711/Qwen3-Omni-30B-A3B-Instruct-FP8-Dynamic"
export PERIOD_MS=2000 GPU_MEM=0.85 MML=8192 MAXSEQS=192 DUR=300
SEED="${SEED:-$$}"

gpu_free_wait() {
  for i in $(seq 1 960); do
    for pid in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null); do
      cl=$(tr '\0' ' ' < /proc/$pid/cmdline 2>/dev/null)
      case "$cl" in
        *worker/stream_server.py*|*VLLM::EngineCore*|*worker/server.py*|*moshi_server*) kill -9 "$pid" 2>/dev/null ;;
        *) : ;;   # NEVER touch anything that isn't ours; just wait
      esac
    done
    pkill -9 -f "worker/stream_server.py" 2>/dev/null
    u=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1 | tr -d ' ')
    [ "${u:-99999}" -lt 4000 ] && { sleep 8; return 0; }
    sleep 5
  done
}
one() { # tag N swa
  for a in 1 2 3; do
    gpu_free_wait
    echo "#### $1 (try $a, $(date +%H:%M:%S)) ####"
    INENGINE_SWA="$3" WINDOW=0 TAG="$1" bash experiments/run_stream_gateway.sh "$2"
    [ -f "results/sustained_fd/$1_n$2.json" ] && { echo "#### $1 OK ####"; break; }
    echo "#### $1 try $a: no JSON, retrying ####"; sleep 8
  done
}

# build the 20-run list and shuffle it reproducibly
RUNLIST=$(for r in 1 2 3 4 5; do
  echo "rvar_van96_r$r 96 0"; echo "rvar_van128_r$r 128 0"
  echo "rvar_ineng96_r$r 96 1024"; echo "rvar_ineng128_r$r 128 1024"
done | shuf --random-source=<(yes "$SEED"))
echo "#### RANDOMIZED ORDER (seed=$SEED) ####"
echo "$RUNLIST" | nl
echo "$RUNLIST" > results/rvar_order.txt
while read -r tag n swa; do
  one "$tag" "$n" "$swa"
done <<< "$RUNLIST"
echo "#### RANDOMIZED VARIANCE DONE ####"
