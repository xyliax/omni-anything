#!/bin/bash
# Full-Duplex-Bench on Moshi: generate Moshi's output audio for each example, transcribe
# it (word timestamps), then run the FD-Bench evaluators (turn-taking + pause handling).
# Moshi step uses its venv (torch<2.10); transcribe + eval use the main env.
set -u
cd "$(dirname "$0")/.."
MV=~/moshi-venv/bin/python
EVAL=external/Full-Duplex-Bench/v1_v1.5/evaluation/evaluate.py
declare -A ROOTS=(
  [smooth_turn_taking]="data/fdbench/candor_turn_taking/candor_turn_taking"
  [pause_handling]="data/fdbench/synthetic_pause_handling/synthetic_pause_handling"
)
for task in smooth_turn_taking pause_handling; do
  root="${ROOTS[$task]}"
  echo "===== FD-BENCH $task  root=$root  $(date +%H:%M:%S) ====="
  # 1) Moshi full-duplex -> output.wav (retry on GPU race)
  for try in 1 2 3 4 5; do
    echo "--- moshi gen try $try ---"
    $MV experiments/moshi_fdbench.py --root "$root" && break
    echo "moshi gen failed; sleep 90"; sleep 90
  done
  # 2) transcribe output.wav -> output.json (whisper word timestamps)
  for try in 1 2 3; do
    python3 -u experiments/transcribe_fdbench.py --root "$root" && break
    echo "transcribe failed; sleep 60"; sleep 60
  done
  # 3) FD-Bench evaluator
  echo "--- evaluate $task ---"
  python3 -u "$EVAL" --task "$task" --root_dir "$root" 2>&1 | tail -25
done
echo "FDBENCH DONE $(date +%H:%M:%S)"
