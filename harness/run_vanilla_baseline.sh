#!/usr/bin/env bash
# E1：vanilla vLLM-realtime（WINDOW=0，KV 无界常驻）在 3090/24GB 上的分钟级显存墙。
# 方法论：fresh-per-point、FD_PHASE_STAGGER=1、METRONOME_STATLOG 记 KV 池占用、nvidia-smi 采样 SM util。
# 进程纪律（多会话共机约定，见 PAPER-EXPERIMENTS 执行记录）：只按本脚本启动的进程组 kill，
# 绝不用 pkill -f 模式匹配（会误杀并行会话的 worker）。
# 用法: GPUS=1 NS="6 8" DUR=600 bash harness/run_vanilla_baseline.sh
set -u
cd "$(dirname "$0")/.."
MET=metronome
OUT=results/paper/baseline; mkdir -p $OUT
GPU="${GPUS:-1}"; NS="${NS:-2 4 6 8}"; DUR="${DUR:-300}"
MODEL="${MODEL:-Qwen/Qwen2.5-Omni-7B}"; PERIOD_MS=2000; MML="${MML:-16384}"; MAXSEQS="${MAXSEQS:-16}"; GPU_MEM="${GPU_MEM:-0.9}"

for N in $NS; do
  TAG="e1van_n${N}_d${DUR}"
  echo "### [$(date +%H:%M:%S)] N=$N fresh worker (GPU $GPU, MML=$MML, ${DUR}s)"
  rm -f /tmp/wready_e1_$$.flag
  cd $MET
  CUDA_VISIBLE_DEVICES=$GPU HF_HUB_OFFLINE=1 METRONOME_STATLOG=../$OUT/${TAG}_kv.log \
    setsid ~/vllm023-venv/bin/python -u worker/stream_server.py --model "$MODEL" --port 50051 \
      --gpu-mem $GPU_MEM --max-model-len $MML --max-num-seqs $MAXSEQS --tpt 25 --max-audio-chunks 64 \
      --window-frames 0 --wait-budget-s 1.6 --ready-file /tmp/wready_e1_$$.flag \
      > ../$OUT/${TAG}_worker.log 2>&1 &
  WPID=$!
  cd ..
  for i in $(seq 1 120); do
    [ -f /tmp/wready_e1_$$.flag ] && break
    grep -qE "EngineCore failed to start|CUDA out of memory|OutOfMemoryError" $OUT/${TAG}_worker.log 2>/dev/null \
      && { echo "WORKER FATAL (N=$N)"; tail -5 $OUT/${TAG}_worker.log; break; }
    sleep 3
  done
  [ -f /tmp/wready_e1_$$.flag ] || { kill -9 -$WPID 2>/dev/null; continue; }

  cd $MET
  setsid ./gateway-go/gateway --port 8904 --worker 127.0.0.1:50051 --period-ms $PERIOD_MS --tpt 25 \
      > ../$OUT/${TAG}_gw.log 2>&1 &
  GPID=$!
  cd ..
  sleep 3
  nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader -l 5 -i $GPU > $OUT/${TAG}_smi.log &
  SMI=$!
  SH=1; [ "$N" -ge 32 ] && SH=4
  ( cd $MET && FD_PHASE_STAGGER=1 python3 -u experiments/sustained_fd.py --uri ws://127.0.0.1:8904 \
      --shards $SH --m $((N/SH)) --duration $DUR --chunk-ms 20 --budget-ms $PERIOD_MS --tag "$TAG" ) \
    2>&1 | tee $OUT/${TAG}_client.txt | tail -12
  kill $SMI 2>/dev/null
  cp $MET/results/sustained_fd/${TAG}.json $OUT/ 2>/dev/null
  kill -9 -$WPID -$GPID 2>/dev/null   # 只杀本脚本的进程组（setsid 使 pgid=pid）
  sleep 8
done
echo "### DONE $(date +%H:%M:%S); artifacts in $OUT"