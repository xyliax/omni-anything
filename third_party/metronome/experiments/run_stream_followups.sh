#!/bin/bash
# Follow-up streaming experiments: #1 long-duration sustainability, #2 streaming correctness
# (MiniCPM+7B), #3 context-cap Pareto sweep (30B). All on the vLLM streaming-session backend.
set -u
cd "$(dirname "$0")/.."
export GOROOT=~/goroot/go PATH=~/goroot/go/bin:$PATH
M30=sammysun0711/Qwen3-Omni-30B-A3B-Instruct-FP8-Dynamic

teardown() {
  for p in $(pgrep -f "worker/server.py") $(pgrep -f "VLLM::EngineCore") $(pgrep -f "gateway-go/gateway"); do
    kill -9 "$p" 2>/dev/null; done
  sleep 6
}

# #2 streaming correctness: start worker, probe solo + load, teardown
corr() {  # MODEL PERIOD GPU_MEM MAXSEQS TAG LOADN
  rm -f /tmp/wready_f.flag
  setsid python3 -u worker/server.py --model "$1" --port 50051 --gpu-mem "$3" \
    --max-model-len 16384 --max-num-seqs "$4" --max-num-batched-tokens 16384 \
    --streaming-sessions --max-ctx-chunks 64 --ready-file /tmp/wready_f.flag \
    > results/foll_worker_$5.log 2>&1 &
  for i in $(seq 1 150); do [ -f /tmp/wready_f.flag ] && break; sleep 2; done
  [ -f /tmp/wready_f.flag ] || { echo "$5 WORKER FAILED"; tail -5 results/foll_worker_$5.log; teardown; return; }
  setsid ./gateway-go/gateway --port 8904 --worker 127.0.0.1:50051 --period-ms "$2" --tpt 25 \
    > results/foll_gw_$5.log 2>&1 &
  sleep 4
  echo "### $5 streaming correctness (solo / load N=$6)"
  python3 -u experiments/fd_correctness_probe.py --uri ws://127.0.0.1:8904 --n-sessions 1 --duration 40 --tag corr_${5}_solo 2>&1 | grep SESSIONS
  python3 -u experiments/fd_correctness_probe.py --uri ws://127.0.0.1:8904 --n-sessions "$6" --duration 60 --tag corr_${5}_load 2>&1 | grep SESSIONS
  teardown
}

echo "===== #2 STREAMING CORRECTNESS ====="
corr "openbmb/MiniCPM-o-4_5" 1000 0.6 24 stream_mcpm 8
corr "Qwen/Qwen2.5-Omni-7B"  2000 0.6 16 stream_7b 8

echo "===== #1 30B LONG SUSTAINABILITY N=128, 240s (cap64) — does drift plateau under budget? ====="
MODEL="$M30" PERIOD_MS=2000 GPU_MEM=0.85 STREAM=1 MML=16384 DUR=240 MAXCHUNKS=64 \
  TAG=st30b_long MAXSEQS=160 FD_PHASE_STAGGER=1 \
  bash experiments/run_sustained_vllm.sh "128"
sleep 6

echo "===== #3 CONTEXT-CAP PARETO (30B): capacity vs resident-memory ====="
MODEL="$M30" PERIOD_MS=2000 GPU_MEM=0.85 STREAM=1 MML=16384 DUR=75 MAXCHUNKS=32 \
  TAG=st30b_cap32 MAXSEQS=288 FD_PHASE_STAGGER=1 \
  bash experiments/run_sustained_vllm.sh "128 192 256"
sleep 6
MODEL="$M30" PERIOD_MS=2000 GPU_MEM=0.85 STREAM=1 MML=16384 DUR=75 MAXCHUNKS=16 \
  TAG=st30b_cap16 MAXSEQS=360 FD_PHASE_STAGGER=1 \
  bash experiments/run_sustained_vllm.sh "192 256 320"

echo "FOLLOWUPS_DONE $(date +%H:%M:%S)" > results/followups_done.flag
