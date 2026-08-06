#!/bin/bash
# Autonomous runner for the remaining feasible scientific-gap experiments. Each stage is
# window-gated + retried (coexists with the GPU-blocked head-to-head), and COMMITS its
# result as soon as it completes (so progress is saved if interrupted).
set -u
cd "$(dirname "$0")/.."
rr(){ l="$1"; shift; for t in 1 2 3 4 5; do echo "=== [$l] try $t $(date +%H:%M:%S) ==="; "$@" && { echo "[$l] OK"; return 0; }; echo "[$l] fail $t; sleep 120"; sleep 120; done; echo "[$l] GAVE UP"; return 1; }
commit(){ paths="$1"; msg="$2"; if compgen -G "$paths" >/dev/null 2>&1; then git add $paths && git commit -q -m "$msg" && git push -q origin main >/dev/null 2>&1 && echo "[commit] $msg"; fi; }

echo "###### GAP #1: KV-windowing quality (perplexity vs context window) ######"
rr kv-qwen    python3 -u experiments/kv_quality.py --model qwen-omni --gpu-mem 0.35
commit "results/kv_quality/qwen-omni.json" "GAP #1: KV-windowing quality (qwen-omni) — perplexity vs window, essential-KV saturation"
rr kv-minicpm python3 -u experiments/kv_quality.py --model minicpm-o --gpu-mem 0.45
commit "results/kv_quality/minicpm-o.json" "GAP #1: KV-windowing quality (minicpm-o) — perplexity vs window"

echo "###### GAP #3: admission tightness (predicted vs true max-feasible) ######"
rr tightness  python3 -u experiments/admission_tightness.py --max-util 60
commit "results/tightness/admission_tightness.json" "GAP #3: admission tightness — predicted capacity vs real-engine true max-feasible"

echo "GAPS DONE $(date +%H:%M:%S)"
