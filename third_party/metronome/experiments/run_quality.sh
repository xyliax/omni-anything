#!/bin/bash
set -u; cd "$(dirname "$0")/.."
READY=/tmp/rtready_q.flag; rm -f $READY
setsid python3 -u -m metronome.realtime --backend vllm --model openbmb/MiniCPM-o-2_6 \
  --facts minicpm-o --tokens-per-tick 25 --response-max-tokens 64 --gpu-mem 0.6 \
  --max-model-len 4096 --max-num-seqs 640 --max-num-batched-tokens 16384 --capacity 100000 \
  --port 8903 --ready-file $READY > results/srv_quality.log 2>&1 &
SRV=$!
for i in $(seq 1 480); do [ -f $READY ] && break; kill -0 $SRV 2>/dev/null || { echo died; tail -5 results/srv_quality.log; exit 1; }; sleep 1; done
echo "### server ready"
python3 -u experiments/quality_under_load.py --uri ws://127.0.0.1:8903 --n 100 --conc 128
kill -9 -- -$SRV 2>/dev/null; sleep 4; echo "QUALITY DONE"
