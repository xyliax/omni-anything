#!/bin/bash
set -u; cd "$(dirname "$0")/.."
READY=/tmp/rtready_shard.flag; rm -f $READY
RT_DEBUG2=1 setsid ~/.local/bin/python3 2>/dev/null || true
setsid python3 -u -m metronome.realtime --backend vllm --model openbmb/MiniCPM-o-2_6 \
  --facts minicpm-o --tokens-per-tick 25 --response-max-tokens 100 --gpu-mem 0.6 \
  --max-model-len 4096 --max-num-seqs 640 --max-num-batched-tokens 16384 --capacity 100000 \
  --port 8898 --ready-file $READY > results/srv_shardtest.log 2>&1 &
SRV=$!
for i in $(seq 1 480); do [ -f $READY ] && break; kill -0 $SRV 2>/dev/null || { echo "died"; tail -5 results/srv_shardtest.log; exit 1; }; sleep 1; done
echo "### server ready; sharded tests"
echo "--- 1 process x 256 sessions ---"
python3 -u experiments/sharded_load.py --uri ws://127.0.0.1:8898 --shards 1 --m 256
echo "--- 8 processes x 32 sessions = 256 ---"
python3 -u experiments/sharded_load.py --uri ws://127.0.0.1:8898 --shards 8 --m 32
kill -9 -- -$SRV 2>/dev/null; sleep 4
echo "SHARDED TEST DONE"
