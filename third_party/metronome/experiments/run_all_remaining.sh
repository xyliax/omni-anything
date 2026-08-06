#!/bin/bash
# Remaining experiments, batch 1: full-scale quality-parity with bootstrap CIs (C2) across
# all model/task combos, and FD-Bench's remaining automatic task (backchannel, C4).
# Window-gated + retried for the shared GPU.
set -u
cd "$(dirname "$0")/.."
run_retry() { label="$1"; shift
  for t in 1 2 3 4 5; do
    echo "=== [$label] try $t $(date +%H:%M:%S): $* ==="
    "$@" && { echo "[$label] OK"; return 0; }
    echo "[$label] failed try $t; sleep 90"; sleep 90
  done; echo "[$label] GAVE UP"; }

echo "########## PARITY AT SCALE (n=200, bootstrap CIs) ##########"
run_retry parity-qwen-sqa  python3 -u experiments/parity_ab.py --task spoken-qa --dataset llama-questions --model qwen-omni --n 200 --batch 12 --gpu-mem 0.30 --max-tokens 96
run_retry parity-minicpm-sqa python3 -u experiments/parity_ab.py --task spoken-qa --dataset llama-questions --model minicpm-o --n 200 --batch 12 --gpu-mem 0.42 --max-tokens 96
run_retry parity-qwen-asr  python3 -u experiments/parity_ab.py --task asr --dataset librispeech --model qwen-omni --n 200 --batch 12 --gpu-mem 0.30 --max-tokens 200
run_retry parity-qwen-vqa  python3 -u experiments/parity_ab.py --task vqa --dataset mmstar --model qwen-omni --n 200 --batch 12 --gpu-mem 0.30 --max-tokens 64

echo "########## FD-BENCH backchannel (C4) ##########"
BC=data/fdbench/icc_backchannel
if [ ! -d "$BC" ]; then
  python3 - <<'PY'
from huggingface_hub import hf_hub_download
import zipfile, os
p = hf_hub_download("Ssshangfu/Full-Duplex-Bench-Data", "v1.0/icc_backchannel.zip", repo_type="dataset")
os.makedirs("data/fdbench/icc_backchannel", exist_ok=True)
with zipfile.ZipFile(p) as z: z.extractall("data/fdbench/icc_backchannel")
print("extracted icc_backchannel")
PY
fi
ROOT=$(find data/fdbench/icc_backchannel -maxdepth 2 -type d -name "*backchannel*" | head -1)
[ -z "$ROOT" ] && ROOT=$(find data/fdbench/icc_backchannel -mindepth 1 -maxdepth 1 -type d ! -name "__MACOSX" | head -1)
echo "backchannel root=$ROOT"
run_retry bc-moshi-gen   ~/moshi-venv/bin/python experiments/moshi_fdbench.py --root "$ROOT"
run_retry bc-transcribe  python3 -u experiments/transcribe_fdbench.py --root "$ROOT"
echo "--- evaluate backchannel ---"
python3 -u external/Full-Duplex-Bench/v1_v1.5/evaluation/evaluate.py --task backchannel --root_dir "$ROOT" 2>&1 | tail -20
echo "ALL REMAINING BATCH1 DONE $(date +%H:%M:%S)"
