#!/bin/bash
# FD-Bench user_interruption on Moshi, with the GPT-4o judge via OpenRouter.
set -u
cd "$(dirname "$0")/.."
export OPENAI_BASE_URL="https://openrouter.ai/api/v1"
export OPENAI_API_KEY="$OPENROUTER_API_KEY"
UI=data/fdbench/synthetic_user_interruption
if [ ! -d "$UI" ]; then
  python3 - <<'PY'
from huggingface_hub import hf_hub_download
import zipfile, os
p = hf_hub_download("Ssshangfu/Full-Duplex-Bench-Data","v1.0/synthetic_user_interruption.zip",repo_type="dataset")
os.makedirs("data/fdbench/synthetic_user_interruption",exist_ok=True)
with zipfile.ZipFile(p) as z: z.extractall("data/fdbench/synthetic_user_interruption")
print("extracted user_interruption")
PY
fi
ROOT=$(find data/fdbench/synthetic_user_interruption -mindepth 1 -maxdepth 2 -type d ! -name "__MACOSX" ! -path "*__MACOSX*" | head -1)
# pick the dir that actually contains numbered example folders with input.wav
ROOT=$(dirname "$(find data/fdbench/synthetic_user_interruption -name input.wav | head -1)")
ROOT=$(dirname "$ROOT")
echo "user_interruption root=$ROOT  (examples: $(find "$ROOT" -name input.wav | wc -l))"
for t in 1 2 3 4 5; do ~/moshi-venv/bin/python experiments/moshi_fdbench.py --root "$ROOT" && break; echo "gen retry $t"; sleep 90; done
python3 -u experiments/transcribe_fdbench.py --root "$ROOT"
echo "--- evaluate user_interruption (GPT-4o judge via OpenRouter) ---"
python3 -u external/Full-Duplex-Bench/v1_v1.5/evaluation/evaluate.py --task user_interruption --root_dir "$ROOT" 2>&1 | tail -25
echo "FDBENCH_UI DONE"
