#!/bin/bash
# Poll the GPU; once the external job releases it (<5GB used), run the 20-run variance batch.
# Does NOT kill any external process -- only waits. Caps the wait so it never spins forever.
set -u
cd "$(dirname "$0")/.."
echo "WAITER start $(date); polling for free GPU (external job present)..."
FREE=0
for i in $(seq 1 480); do   # up to 8h at 60s cadence
  u=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1 | tr -d ' ')
  if [ "${u:-99999}" -lt 5000 ]; then FREE=1; echo "GPU FREE ($u MiB) at $(date) after $((i)) polls"; break; fi
  [ $((i % 10)) -eq 0 ] && echo "  still busy: ${u} MiB used ($(date +%H:%M))"
  sleep 60
done
if [ "$FREE" != 1 ]; then echo "WAITER: GPU still busy after cap; NOT launching."; exit 1; fi
sleep 5
echo "WAITER: launching 20-run variance batch $(date)"
bash experiments/run_variance.sh
echo "WAITER: VARIANCE BATCH COMPLETE $(date)"
