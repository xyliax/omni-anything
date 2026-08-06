#!/bin/bash
# SUSTAINED continuous full-duplex VOICE-IN / VOICE-OUT for Moshi (the native streaming-codec
# full-duplex model) through the Go gateway. Client streams 20ms chunks continuously for DUR s;
# Moshi worker decodes Mimi audio every 80ms frame -> real PCM out (response.audio.delta).
# This is the true voice-in-voice-out full-duplex test. Latency bucketed by elapsed time.
set -u
cd "$(dirname "$0")/.."
export GOROOT=~/goroot/go PATH=~/goroot/go/bin:$PATH
GRID="${1:-8 16 24}"; DUR="${DUR:-60}"; CHUNK_MS="${CHUNK_MS:-20}"; MAXB="${MAXB:-32}"
WREADY=/tmp/wready_sm.flag; rm -f $WREADY
echo "### [$(date +%H:%M:%S)] Moshi worker (moshi venv, real Mimi audio out, max-batch $MAXB)"
setsid ~/moshi-venv/bin/python -u worker/moshi_server.py --port 50051 --max-batch "$MAXB" \
  --ready-file $WREADY > results/sustained_moshi_worker.log 2>&1 &
WK=$!
for i in $(seq 1 600); do
  [ -f $WREADY ] && break
  kill -0 $WK 2>/dev/null || { echo "WORKER DIED"; tail -15 results/sustained_moshi_worker.log; exit 1; }
  sleep 2
done
[ -f $WREADY ] || { echo "worker timeout"; exit 1; }
setsid ./gateway-go/gateway --port 8904 --worker 127.0.0.1:50051 --period-ms 80 --tpt 1 \
  > results/sustained_moshi_gw.log 2>&1 &
GW=$!
sleep 4
for N in $GRID; do
  echo "### [$(date +%H:%M:%S)] Moshi N=$N sustained ${DUR}s @ ${CHUNK_MS}ms chunks (voice-out)"
  SH=1; [ "$N" -ge 16 ] && SH=2
  python3 -u experiments/sustained_fd.py --uri ws://127.0.0.1:8904 --shards $SH --m $((N/SH)) \
    --duration "$DUR" --chunk-ms "$CHUNK_MS" --budget-ms 80 --bucket-s 10 --tag "moshi_n${N}"
done
echo "### teardown"
kill -9 $GW 2>/dev/null; kill -9 -- -$WK 2>/dev/null
pkill -9 -f "worker/moshi_server.py" 2>/dev/null
sleep 4
echo "SUSTAINED MOSHI DONE ($(nvidia-smi --query-gpu=memory.used --format=csv,noheader))"
