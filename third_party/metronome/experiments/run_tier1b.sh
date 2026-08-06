#!/bin/bash
# Quality-vs-batch + Poisson load sweep (the two validated Tier-1 experiments; the real-vLLM
# head-to-head is being rebuilt against vLLM's async server).
set -u
cd "$(dirname "$0")/.."
rr(){ l="$1"; shift; for t in 1 2 3; do echo "=== [$l] try $t $(date +%H:%M:%S) ==="; "$@" && { echo "[$l] OK"; return; }; sleep 90; done; echo "[$l] GAVE UP"; }
echo "###### quality vs batch ######"
rr qb-sqa python3 -u experiments/quality_vs_batch.py --task spoken-qa --dataset llama-questions --model qwen-omni --n 128 --gpu-mem 0.35
rr qb-asr python3 -u experiments/quality_vs_batch.py --task asr --dataset librispeech --model qwen-omni --n 128 --gpu-mem 0.35 --max-tokens 200
echo "###### Poisson load sweep ######"
rr ls-moshi   python3 -u experiments/load_sweep.py --model moshi --seeds 4
rr ls-qwen    python3 -u experiments/load_sweep.py --model qwen3-omni --seeds 4
rr ls-minicpm python3 -u experiments/load_sweep.py --model minicpm-o --seeds 4
echo "TIER1B DONE $(date +%H:%M:%S)"
