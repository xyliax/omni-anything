#!/bin/bash
# End-to-end: Python vLLM gRPC worker + Go gateway + client. $1=mode (smoke|quality|capacity)
set -u; cd "$(dirname "$0")/.."
export GOROOT=~/goroot/go PATH=~/goroot/go/bin:$PATH
MODE="${1:-smoke}"; MODEL="${MODEL:-openbmb/MiniCPM-o-2_6}"; QUANT="${QUANT:-}"
WREADY=/tmp/wready.flag; rm -f $WREADY
QA=""; [ -n "$QUANT" ] && QA="--quantization $QUANT"
echo "### starting vLLM worker $(date +%H:%M:%S)"
setsid python3 -u worker/server.py --model "$MODEL" --port 50051 --gpu-mem 0.6 \
  --max-num-seqs 640 --max-num-batched-tokens 16384 $QA --window-s ${WINDOW_S:-8} --ready-file $WREADY \
  > results/worker.log 2>&1 &
WK=$!
for i in $(seq 1 600); do [ -f $WREADY ] && break; kill -0 $WK 2>/dev/null || { echo "worker died"; tail -8 results/worker.log; exit 1; }; sleep 1; done
[ -f $WREADY ] || { echo "worker not ready"; tail -8 results/worker.log; kill -9 -- -$WK; exit 1; }
echo "### worker ready; starting Go gateway $(date +%H:%M:%S)"
./gateway-go/gateway --port 8904 --worker 127.0.0.1:50051 --period-ms ${PERIOD_MS:-1000} --tpt ${GTPT:-25} \
  > results/gogw_e2e.log 2>&1 &
GW=$!
sleep 4
echo "### gateway up; running $MODE"
case "$MODE" in
  smoke)    python3 -u experiments/quality_under_load.py --uri ws://127.0.0.1:8904 --n 12 --conc 4 ;;
  quality)  python3 -u experiments/quality_under_load.py --uri ws://127.0.0.1:8904 --n 100 --conc 128 ;;
  capacity) RESP_MAX=100 python3 -u experiments/realtime_load.py --uri ws://127.0.0.1:8904 \
              --model ${CLIENT_MODEL:-minicpm-o} --grid ${GRID:-1 8 32 64 96 128 192 256} --tpt ${GTPT:-25} --turns 1 \
              --warmup-turns 0 --trim-ticks 3 --tag gogw_e2e --slo 0.05 ;;
  fd)       for tot in ${FDSHARDS:-"2 2" "4 4" "4 8" "8 8"}; do set -- $tot; \
              echo "=== continuous full-duplex total=$(($1*$2)) ($1x$2) ==="; \
              python3 -u experiments/fd_load.py --uri ws://127.0.0.1:8904 --shards $1 --m $2 --duration 15 --chunk-ms 200 --budget-ms ${BUDGET_MS:-1000}; done ;;
  sharded)  for tot in ${SHARDS:-"8 32" "8 64" "16 64"}; do set -- $tot; \
              echo "=== sharded total=$(($1*$2)) ($1x$2) through Go gateway ==="; \
              python3 -u experiments/sharded_load.py --uri ws://127.0.0.1:8904 --shards $1 --m $2; done ;;
esac
RC=$?
echo "### done rc=$RC; teardown"
kill -9 $GW 2>/dev/null; kill -9 -- -$WK 2>/dev/null; sleep 4
echo "E2E $MODE DONE"
