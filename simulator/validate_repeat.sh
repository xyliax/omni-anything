#!/usr/bin/env bash
# Run validate.py N times and keep every attempt.
#
# The card is shared with a bursty co-tenant. Contention does not touch
# graph-replayed decode steps (flat 6.7-7.6ms across every run) but inflates
# eager wake-prefill steps from ~19ms to ~30ms, which is larger than the 15%
# validation bar. A single run therefore measures the neighbour as much as the
# model. Repeating and reporting the distribution -- with the lowest-power run
# as the primary verdict -- keeps the claim auditable instead of cherry-picked:
# every attempt is written to validation_runs/.
set -u
MODEL=${MODEL:?set MODEL to the model path}
GPU=${GPU:-3}
N=${N:-5}
OUT=$(dirname "$0")/validation_runs
mkdir -p "$OUT"
for i in $(seq 1 "$N"); do
  echo "=== attempt $i/$N ==="
  bash "$(dirname "$0")/wait_quiet.sh" "$GPU" "${QUIET_S:-30}" || true
  VLLM_USE_V1=0 CUDA_VISIBLE_DEVICES="$GPU" \
    python simulator/validate.py --model "$MODEL" --gpu "$GPU" \
      --beats 14 --inject-at 7 --L 2048 >"$OUT/attempt_$i.log" 2>&1
  cp simulator/validation_report.json   "$OUT/report_$i.json"   2>/dev/null
  cp simulator/validation_timeline.csv  "$OUT/timeline_$i.csv"  2>/dev/null
  cp simulator/validation_steps.csv     "$OUT/steps_$i.csv"     2>/dev/null
  python - "$OUT/report_$i.json" <<'EOF'
import json, sys
try:
    r = json.load(open(sys.argv[1]))
except Exception as e:
    print("  (no report)", e); raise SystemExit
v = r.get("verdict", r)
print(f"  mean_abs={v['mean_abs_beat_err_pct']:.2f}% "
      f"cum={v['final_cumulative_err_pct']:.2f}% "
      f"PASS={v['PASS']} power={v.get('gpu_power_w_range')}")
EOF
done
echo "=== all attempts in $OUT ==="
