#!/bin/bash
# Diagnostic: instrument a vanilla N=128/300s run with vLLM INFO stats to see whether the congestion
# collapse coincides with KV-cache exhaustion + preemption (memory) or happens with KV usage still low
# (pure compute/throughput). Waits for the GPU to free; never kills external training jobs.
set -u
cd "$(dirname "$0")/.."
export GOROOT=~/goroot/go PATH=~/goroot/go/bin:$PATH
VENV="$HOME/vllm023-venv"; CU13="$VENV/lib/python3.10/site-packages/nvidia/cu13"
export CUDA_HOME="$CU13" CUDA_PATH="$CU13" PATH="$CU13/bin:$PATH"
export NVCC_APPEND_FLAGS="-DCCCL_DISABLE_CTK_COMPATIBILITY_CHECK"
EXT='*train_rlvr*|*never-stop-thinking*|*minif2f_train*|*/rlvp*|*transparent-offload*|*transparent-runtime*|*node *'
echo "PDIAG waiting for free GPU $(date)..."
FREE=0
for i in $(seq 1 600); do
  for pid in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null); do
    cl=$(tr '\0' ' ' < /proc/$pid/cmdline 2>/dev/null)
    case "$cl" in $EXT) : ;; *) kill -9 "$pid" 2>/dev/null ;; esac   # reap only MY orphans
  done
  u=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1 | tr -d ' ')
  [ "${u:-99999}" -lt 4000 ] && { FREE=1; echo "GPU FREE ($u) at $(date)"; break; }
  [ $((i % 10)) -eq 0 ] && echo "  busy ${u} MiB ($(date +%H:%M))"
  sleep 30
done
[ "$FREE" = 1 ] || { echo "PDIAG: GPU still busy; abort"; exit 1; }
sleep 5
rm -f /tmp/wready_pd.flag results/preempt_worker.log results/preempt_gw.log results/preempt_smi.log results/preempt_stats.log
VLLM_LOGGING_LEVEL=WARNING METRONOME_INENGINE_SWA=${INENGINE_SWA:-0} METRONOME_STATLOG=results/preempt_stats_${TAGSFX:-van}.log \
  setsid "$VENV/bin/python" -u worker/stream_server.py --model sammysun0711/Qwen3-Omni-30B-A3B-Instruct-FP8-Dynamic \
  --port 50051 --gpu-mem 0.85 --max-model-len 8192 --max-num-seqs 192 --tpt 25 --max-audio-chunks 64 \
  --window-frames ${WINDOW:-0} --wait-budget-s 1.6 --ready-file /tmp/wready_pd.flag > results/preempt_worker.log 2>&1 &
for i in $(seq 1 200); do [ -f /tmp/wready_pd.flag ] && break; sleep 3; done
[ -f /tmp/wready_pd.flag ] || { echo "PDIAG worker failed"; tail -8 results/preempt_worker.log|grep -avE HTTP; exit 1; }
echo "PDIAG worker ready $(date)"
setsid ./gateway-go/gateway --port 8904 --worker 127.0.0.1:50051 --period-ms 2000 --tpt 25 > results/preempt_gw.log 2>&1 &
GW=$!; sleep 4
# sample GPU mem every 5s during the run (pool is preallocated, but capture anyway)
( for t in $(seq 1 70); do echo "$(date +%s) $(nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader,nounits|head -1)"; sleep 5; done ) > results/preempt_smi.log 2>&1 &
SMI=$!
python3 -u experiments/sustained_fd.py --uri ws://127.0.0.1:8904 --shards 4 --m 32 --duration 300 --chunk-ms 20 --budget-ms 2000 --tag pdiag128_${TAGSFX:-van}
kill -9 $GW $SMI 2>/dev/null
pkill -9 -f "worker/stream_server.py" 2>/dev/null
for pid in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null); do cl=$(tr '\0' ' ' </proc/$pid/cmdline 2>/dev/null); case "$cl" in $EXT) : ;; *) kill -9 "$pid" 2>/dev/null;; esac; done
echo "PREEMPT DIAG DONE $(date)"
