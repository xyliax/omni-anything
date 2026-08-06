#!/usr/bin/env bash
# E1 per-request instrumented rerun (single point, default N=8/600s): produces, on one shared clock,
#   - per-session P/F/T event log (tick push -> engine accept -> token growth) => per-tick engine
#     service spans + per-session active window + per-session context/KV trajectory
#   - kv.log with cumulative preemption counter (pre=) => preemption timestamps + victim inference
# Worker = harness/stream_server_paringest.py (instrumented COPY; metronome clone untouched).
# MML defaults to 32768 to keep post-wall behavior clean of the MML-zombie artifact.
# Ports default 50054/8907 to avoid clashing with parallel sessions on 50051/8904.
# Process discipline: setsid + kill by process group only (never pkill -f).
# 用法: GPUS=3 N=8 DUR=600 bash harness/run_e1_perreq.sh
set -u
cd "$(dirname "$0")/.."
ROOT=$PWD; MET=$ROOT/metronome
OUT=$ROOT/results/paper/baseline; mkdir -p "$OUT"
GPU="${GPUS:-3}"; N="${N:-8}"; DUR="${DUR:-600}"
MODEL="${MODEL:-Qwen/Qwen2.5-Omni-7B}"; PERIOD_MS=2000; MML="${MML:-32768}"
MAXSEQS="${MAXSEQS:-16}"; GPU_MEM="${GPU_MEM:-0.9}"
WPORT="${WPORT:-50054}"; GPORT="${GPORT:-8907}"
TAG="e1paringest_n${N}_d${DUR}"

echo "### [$(date +%H:%M:%S)] $TAG fresh worker (GPU $GPU, MML=$MML, ${DUR}s)"
rm -f /tmp/wready_paringest_$$.flag "$OUT/${TAG}_perreq.log" "$OUT/${TAG}_kv.log"
CUDA_VISIBLE_DEVICES=$GPU HF_HUB_OFFLINE=1 METRONOME_ROOT=$MET \
  METRONOME_STATLOG=$OUT/${TAG}_kv.log PERREQ_LOG=$OUT/${TAG}_perreq.log \
  setsid ~/vllm023-venv/bin/python -u "$ROOT/harness/stream_server_paringest.py" \
    --model "$MODEL" --port $WPORT \
    --gpu-mem $GPU_MEM --max-model-len $MML --max-num-seqs $MAXSEQS --tpt 25 --max-audio-chunks 64 \
    --window-frames 0 --wait-budget-s 1.6 --seed-tokens ${SEED_TOKENS:-0} --ready-file /tmp/wready_paringest_$$.flag \
    > "$OUT/${TAG}_worker.log" 2>&1 &
WPID=$!
for i in $(seq 1 120); do
  [ -f /tmp/wready_paringest_$$.flag ] && break
  grep -qE "EngineCore failed to start|CUDA out of memory|OutOfMemoryError" "$OUT/${TAG}_worker.log" 2>/dev/null \
    && { echo "WORKER FATAL"; tail -5 "$OUT/${TAG}_worker.log"; kill -9 -$WPID 2>/dev/null; exit 1; }
  sleep 3
done
[ -f /tmp/wready_paringest_$$.flag ] || { echo "WORKER TIMEOUT"; kill -9 -$WPID 2>/dev/null; exit 1; }

setsid "$MET/gateway-go/gateway" --port $GPORT --worker 127.0.0.1:$WPORT \
    --period-ms $PERIOD_MS --tpt 25 > "$OUT/${TAG}_gw.log" 2>&1 &
GPID=$!
sleep 3
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader -l 5 -i $GPU > "$OUT/${TAG}_smi.log" &
SMI=$!
( cd "$MET" && FD_PHASE_STAGGER=1 python3 -u experiments/sustained_fd.py --uri ws://127.0.0.1:$GPORT \
    --shards 1 --m $N --duration $DUR --chunk-ms 20 --budget-ms $PERIOD_MS --tag "$TAG" ) \
  2>&1 | tee "$OUT/${TAG}_client.txt" | tail -6
kill $SMI 2>/dev/null
cp "$MET/results/sustained_fd/${TAG}.json" "$OUT/" 2>/dev/null
kill -9 -$WPID -$GPID 2>/dev/null   # 只杀本脚本的进程组（setsid 使 pgid=pid）
echo "### DONE $(date +%H:%M:%S); artifacts $OUT/${TAG}_*"
