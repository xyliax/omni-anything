#!/bin/bash
# 5 fresh runs x 4 long points (vanilla/in-engine x N=96/128, 300s) for Fig 1 error bars.
# Robust: (a) wait until the GPU is actually free before each run (kills any lingering setsid EngineCore;
# also yields to an external job), (b) retry a run that produced no result JSON.
set -u
cd "$(dirname "$0")/.."
export MODEL="sammysun0711/Qwen3-Omni-30B-A3B-Instruct-FP8-Dynamic"
export PERIOD_MS=2000 GPU_MEM=0.85 MML=8192 MAXSEQS=192 DUR=300
RUNS="${RUNS:-1 2 3 4 5}"

gpu_free_wait() {   # ensure GPU is actually free before a run: kill MY GPU-holding procs by PID
  for i in $(seq 1 480); do
    for pid in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null); do
      cl=$(tr '\0' ' ' < /proc/$pid/cmdline 2>/dev/null)
      case "$cl" in
        *train_rlvr*|*never-stop-thinking*) : ;;          # external job: never touch
        *) kill -9 "$pid" 2>/dev/null ;;                   # mine (stream_server/EngineCore): reap
      esac
    done
    pkill -9 -f "worker/stream_server.py" 2>/dev/null
    u=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1 | tr -d ' ')
    [ "${u:-99999}" -lt 3000 ] && { sleep 8; return 0; }   # free + settle
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
for r in $RUNS; do
  one "var_van96_r$r"    96  0
  one "var_van128_r$r"   128 0
  one "var_ineng96_r$r"  96  1024
  one "var_ineng128_r$r" 128 1024
done
echo "#### VARIANCE DONE ####"
