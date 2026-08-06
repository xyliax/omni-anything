#!/bin/bash
# Orchestrate the SEPARATE-PROCESS real-time benchmark: start the RealtimeServer+vLLM in its own
# process (all efficiency levers), wait until it's serving, run the external load driver, tear
# down. Usage: run_realtime_bench.sh <model> <tag> <tpt> <gpumem> <port> "<grid>" [server extra...]
set -u
cd "$(dirname "$0")/.."
MODEL="${1:?model}"; TAG="${2:?tag}"; TPT="${3:?tpt}"; MEM="${4:?gpumem}"; PORT="${5:?port}"
GRID="${6:?grid}"; shift 6; SRV_EXTRA="$*"
case "$MODEL" in
  minicpm-o) HF="openbmb/MiniCPM-o-2_6";   FACTS="minicpm-o" ;;
  qwen-omni) HF="Qwen/Qwen2.5-Omni-7B";    FACTS="qwen3-omni" ;;
  *) echo "unknown model $MODEL"; exit 1 ;;
esac
READY="/tmp/rtready_${TAG}_${PORT}.flag"; rm -f "$READY"
LOG="results/srv_${MODEL}_${TAG}.log"

echo "### start server $MODEL/$TAG tpt=$TPT mem=$MEM port=$PORT extra=[$SRV_EXTRA] $(date +%H:%M:%S)"
# setsid => the server (and its EngineCore subprocess) form their OWN process group, so we can
# reap exactly our processes with a group kill — never touching co-tenant GPU processes.
setsid python3 -u -m metronome.realtime --backend vllm --model "$HF" --facts "$FACTS" \
  --tokens-per-tick "$TPT" --response-max-tokens ${RESP_MAX:-100} --gpu-mem "$MEM" --max-model-len 4096 \
  --max-num-seqs 640 --max-num-batched-tokens 16384 --capacity 100000 \
  --port "$PORT" --ready-file "$READY" $SRV_EXTRA > "$LOG" 2>&1 &
SRV=$!
# wait up to 8 min for the server to load the model and start serving
for i in $(seq 1 480); do
  [ -f "$READY" ] && break
  kill -0 $SRV 2>/dev/null || { echo "server died early; tail:"; tail -15 "$LOG"; exit 1; }
  sleep 1
done
[ -f "$READY" ] || { echo "server not ready in time; tail:"; tail -15 "$LOG"; kill -9 $SRV; exit 1; }
echo "### server ready $(date +%H:%M:%S); launching load driver"

python3 -u experiments/realtime_load.py --uri "ws://127.0.0.1:$PORT" --model "$MODEL" \
  --grid $GRID --tpt "$TPT" --tag "$TAG" --turns ${TURNS:-12} --warmup-turns ${WARMUP_TURNS:-3} \
  --think-s "${THINK_S:-0}" --trim-ticks ${TRIM_TICKS:-5} --slo 0.05 --audio-clips 128 ${DRIVER_EXTRA:-}
RC=$?
echo "### load driver done rc=$RC; stopping server process GROUP (mine only) $(date +%H:%M:%S)"
kill -9 -- -$SRV 2>/dev/null   # negative PID => kill the whole process group (server+EngineCore)
sleep 5
exit $RC
