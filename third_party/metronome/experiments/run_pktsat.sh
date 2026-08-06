#!/bin/bash
set -u; cd "$(dirname "$0")/.."
READY=/tmp/rtready_pkt.flag; rm -f $READY
RT_DEBUG2=1 setsid python3 -u -m metronome.realtime --backend vllm --model openbmb/MiniCPM-o-2_6 \
  --facts minicpm-o --tokens-per-tick 25 --response-max-tokens 100 --gpu-mem 0.6 \
  --max-model-len 4096 --max-num-seqs 640 --max-num-batched-tokens 16384 --capacity 100000 \
  --port 8901 --ready-file $READY > results/srv_pktsat.log 2>&1 &
SRV=$!
for i in $(seq 1 480); do [ -f $READY ] && break; kill -0 $SRV 2>/dev/null || { echo died; exit 1; }; sleep 1; done
echo "### server ready"
for cfg in "4 32 20" "8 32 20" "8 64 20" "16 64 20" "16 64 40"; do
  set -- $cfg; sh="$1"; m="$2"; cm="$3"
  echo "###### load: ${sh}x${m} @ ${cm}ms ######"
  python3 -u experiments/packet_load.py --uri ws://127.0.0.1:8901 --shards $sh --m $m --chunk-ms $cm --duration 15
  sleep 2
done
kill -9 -- -$SRV 2>/dev/null; sleep 4; echo "PKTSAT DONE"
