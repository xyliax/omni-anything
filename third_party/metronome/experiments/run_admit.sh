#!/bin/bash
# Measure ADMISSION SPREADING: burst arrival (all N at once), vary max_admit_per_tick. Without
# spreading, one tick carries N prefills -> budget overrun (cliff). With spreading, per-tick
# prefill is bounded -> graceful. Each config = one server (separate process) + burst sweep.
set -u; cd "$(dirname "$0")/.."
export RESP_MAX=100 TURNS=1 WARMUP_TURNS=0 TRIM_TICKS=2 DRIVER_EXTRA="--arrival-rate 2000"
P=8880
run(){ admit="$1"; tag="$2"; P=$((P+1))
  echo "###### admit=$admit ($tag) $(date +%H:%M:%S) ######"
  bash experiments/run_realtime_bench.sh minicpm-o "$tag" 25 0.6 $P "64 128 256" \
    --max-admit-per-tick "$admit" && echo "[$tag] OK" || echo "[$tag] FAILED"
  git add results/realtime_load/ 2>/dev/null
  git commit -q -m "admission-spreading: minicpm $tag (max_admit=$admit, burst arrival)" >/dev/null 2>&1 && git push -q origin main >/dev/null 2>&1 && echo "[commit] $tag"
}
run 1073741824 admit_inf      # baseline: no spreading (admit all at once)
run 64          admit_64
run 32          admit_32
echo "ADMIT SWEEP DONE $(date +%H:%M:%S)"
