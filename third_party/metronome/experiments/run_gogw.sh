#!/bin/bash
set -u; cd "$(dirname "$0")/.."
./gateway-go/gateway --port 8902 --period-ms 1000 > results/go_gateway.log 2>&1 &
GW=$!
sleep 2
echo "### go gateway up (pid $GW); same load that slipped Python to 6-14s"
for cfg in "8 64 20" "16 64 20" "16 96 20"; do
  set -- $cfg; sh="$1"; m="$2"; cm="$3"
  echo "###### load: ${sh}x${m} @ ${cm}ms ######"
  python3 -u experiments/packet_load.py --uri ws://127.0.0.1:8902 --shards $sh --m $m --chunk-ms $cm --duration 15
  sleep 2
done
kill -9 $GW 2>/dev/null; sleep 2; echo "GOGW DONE"
