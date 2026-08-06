"""Test the three paper interaction models with REAL weights through the Metronome
serving system (vLLM backend). Waits for sufficient GPU memory before each model.

  * MiniCPM-o 4.5  — openbmb/MiniCPM-o-4_5 (real, arch MiniCPMO); LM backbone Qwen3-8B.
  * Qwen-Omni      — Qwen/Qwen2.5-Omni-7B (real, arch Qwen2_5OmniModel); backbone
                     Qwen/Qwen3-30B-A3B-FP8 (Qwen3-Omni MoE).
  * Moshi          — custom Mimi-codec architecture, not cached and not vLLM-loadable;
                     its exact serving config is validated on the native engine
                     (results/engine/moshi_*). Recorded here as such.

For each loadable model we calibrate the cost model from the model's real per-tick
latency, compute the deadline-aware admission capacity, and measure real serving:
admission at capacity (should hold the SLO) vs throughput-greedy at 2x (should miss).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")

import numpy as np

from bench.gpu_probe import wait_for_window
from metronome.serve import MetronomeServer

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "paper")

# (paper name, [candidate hf ids real->backbone], need_free_gib, gpu_mem, frame_budget,
#  kv_budget, tokens_per_tick, trust_remote_code, max_model_len)
# tokens_per_tick = real per-tick decode count (token_rate * period), NOT the per-second
# rate: a tick decodes its output tokens autoregressively, so this drives the cost.
#  (name, [real->backbone hf ids], need_free_gib, gpu_mem, frame_budget_s, kv_budget,
#   tokens_per_tick, trust_remote_code, max_model_len)
SPECS = [
    ("qwen-omni", ["Qwen/Qwen2.5-Omni-7B", "Qwen/Qwen3-8B"], 22.0, 0.25, 0.2, 2048, 6, True, 8192),
    ("minicpm-o", ["openbmb/MiniCPM-o-4_5", "Qwen/Qwen3-8B"], 26.0, 0.30, 1.0, 4096, 32, True, 8192),
    ("qwen-omni-moe", ["Qwen/Qwen3-30B-A3B-FP8", "Qwen/Qwen3-30B-A3B"], 40.0, 0.45, 0.2, 2048, 6, False, 8192),
]


def try_load(hf_ids, gpu_mem, max_len, trust):
    from metronome.backends.vllm_backend import VLLMBackend
    last = None
    for hf in hf_ids:
        try:
            print(f"  loading {hf} (gpu_mem={gpu_mem}) ...", flush=True)
            b = VLLMBackend(hf, gpu_memory_utilization=gpu_mem, max_model_len=max_len,
                            trust_remote_code=trust, enforce_eager=False)
            return b, hf
        except Exception as e:
            print(f"  [{hf}] load failed: {type(e).__name__}: {str(e)[:160]}")
            last = e
    raise last


def run_model(name, hf_ids, need_free, gpu_mem, fb, kv, tpt, trust, max_len):
    print(f"\n=== {name}: real-weight serving (waiting for >= {need_free} GiB) ===", flush=True)
    wait_for_window(need_free_gib=need_free, max_util_pct=88, timeout_s=36000)
    backend, hf = try_load(hf_ids, gpu_mem, max_len, trust)
    print(f"  loaded {hf}: layers={backend.num_layers} kv_bytes/tok={backend.kv_bytes_per_token} "
          f"hbm_kv={backend.hbm_kv_bytes/2**30:.1f}GiB", flush=True)
    srv = MetronomeServer(backend, frame_budget_s=fb, kv_budget_tokens=kv, tokens_per_tick=tpt)
    srv.calibrate(probe_ns=(1, 2, 4, 8), reps=3)
    cap = srv.predicted_capacity()
    print(f"  deadline-aware capacity: {cap} sessions "
          f"(cost base={srv.cost.batch_base:.1f}ms alpha={srv.cost.batch_alpha:.5f})", flush=True)
    m_adm = srv.serve(cap, n_frames=10, admission=True)
    m_greedy = srv.serve(max(cap * 2, cap + 4), n_frames=10, admission=False)
    # real capacity curve
    ns = sorted(set([1, 2, 4, max(1, cap // 2), cap, int(cap * 1.5), cap * 2]))
    curve = []
    for N in ns:
        mm = srv.serve(N, n_frames=6, admission=False)
        curve.append((N, round(mm["p99_ms"], 1), round(mm["miss_rate"], 3)))
        print(f"    N={N:4d}  p99={mm['p99_ms']:.1f}ms  miss={mm['miss_rate']:.3f}", flush=True)
    res = dict(paper_model=name, served_hf=hf, frame_budget_ms=fb*1000, kv_budget=kv,
               capacity=cap, cost=dict(base=srv.cost.batch_base, alpha=srv.cost.batch_alpha),
               admission=m_adm, greedy=m_greedy, curve=curve)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f"{name}.json"), "w") as fh:
        json.dump(res, fh, indent=2)
    print(f"  REAL: admission {m_adm['n_served']} sessions @ {m_adm['miss_rate']:.1%} miss; "
          f"greedy 2x @ {m_greedy['miss_rate']:.1%} miss  ({hf})", flush=True)
    backend.shutdown()
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None, help="subset of model names")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    summary = {}
    # Moshi: not vLLM-loadable (custom Mimi architecture); validated on native engine.
    summary["moshi"] = {"served_hf": None, "note": "custom Mimi-codec architecture not "
                        "supported by vLLM and not cached; exact serving config validated "
                        "on the native engine (results/engine/moshi_*)."}
    for spec in SPECS:
        name = spec[0]
        if args.only and name not in args.only:
            continue
        try:
            summary[name] = run_model(*spec)
        except Exception as e:
            traceback.print_exc()
            summary[name] = {"error": f"{type(e).__name__}: {str(e)[:200]}"}
        with open(os.path.join(OUT, "paper_models_summary.json"), "w") as fh:
            json.dump(summary, fh, indent=2)
    print("\n=== PAPER MODELS (real weights through Metronome) ===")
    for n, r in summary.items():
        if "capacity" in r:
            print(f"  {n}: {r['served_hf']} -> capacity {r['capacity']}, admission "
                  f"{r['admission']['miss_rate']:.1%} vs greedy {r['greedy']['miss_rate']:.1%}")
        else:
            print(f"  {n}: {r.get('note') or r.get('error')}")


if __name__ == "__main__":
    main()
