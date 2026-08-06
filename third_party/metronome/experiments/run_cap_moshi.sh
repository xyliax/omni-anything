#!/bin/bash
# Moshi continuous full-duplex e2e capacity (audio-only; Moshi has no vision modality).
# Native 80ms-frame streaming model -> measured with fd_load.py (continuous, not turn-based),
# through the SAME Go gateway driving the Moshi gRPC worker (moshi venv).
set -u
cd "$(dirname "$0")/.."
export GOROOT=~/goroot/go PATH=~/goroot/go/bin:$PATH
GRID="${1:-2 4 8 16 24 32}"          # shards x m totals chosen via shard math below
MAXB="${MAXB:-48}"; PERIOD_MS="${PERIOD_MS:-80}"; DUR="${DUR:-15}"
WREADY=/tmp/wready_moshi.flag; rm -f $WREADY
echo "### [$(date +%H:%M:%S)] Moshi gRPC worker (moshi venv, max-batch $MAXB)"
setsid ~/moshi-venv/bin/python -u worker/moshi_server.py --port 50051 --max-batch "$MAXB" \
  --ready-file $WREADY > results/cap_moshi_worker.log 2>&1 &
WK=$!
for i in $(seq 1 600); do
  [ -f $WREADY ] && break
  kill -0 $WK 2>/dev/null || { echo "WORKER DIED"; tail -15 results/cap_moshi_worker.log; exit 1; }
  sleep 2
done
[ -f $WREADY ] || { echo "worker timeout"; tail -15 results/cap_moshi_worker.log; exit 1; }
echo "### worker ready; gateway (period ${PERIOD_MS}ms)"
setsid ./gateway-go/gateway --port 8904 --worker 127.0.0.1:50051 --period-ms "$PERIOD_MS" --tpt 1 \
  > results/cap_moshi_gw.log 2>&1 &
GW=$!
sleep 4
echo "=== MOSHI continuous full-duplex e2e (80ms budget, audio-only) ==="
for N in $GRID; do
  # one shard, m=N sessions (Moshi caps low; single-process client is fine at these N)
  python3 -u experiments/fd_load.py --uri ws://127.0.0.1:8904 --shards 1 --m "$N" \
    --duration "$DUR" --chunk-ms 80 --budget-ms "$PERIOD_MS" 2>&1 | grep -E "streams|frame|TTFA"
done
echo "### teardown"
kill -9 $GW 2>/dev/null; kill -9 -- -$WK 2>/dev/null
pkill -9 -f "worker/moshi_server.py" 2>/dev/null
sleep 4
echo "MOSHI CAP DONE ($(nvidia-smi --query-gpu=memory.used --format=csv,noheader))"
