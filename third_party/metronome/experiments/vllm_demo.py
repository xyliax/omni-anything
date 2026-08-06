"""End-to-end demo: real-model serving through Metronome + vLLM.

Loads a real model on vLLM and drives periodic interaction sessions through the
MetronomeServer, producing real measured numbers:
  * the cost model calibrated from vLLM's own per-tick latency;
  * the deadline-aware admission capacity;
  * graceful-vs-cliff: serving at the admission capacity (0 miss) vs throughput-greedy
    at 2× capacity (real deadline misses);
  * real per-tick latency vs session age.

Default model is Qwen3-1.7B (fits a modest GPU window); pass --model Qwen/Qwen3-8B to
serve the *actual MiniCPM-o backbone* with real weights on a dedicated GPU.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")

from bench.gpu_probe import wait_for_window
from metronome.backends.vllm_backend import VLLMBackend
from metronome.serve import MetronomeServer

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "vllm")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen3-1.7B")
    ap.add_argument("--gpu-mem", type=float, default=0.12)
    ap.add_argument("--frame-budget", type=float, default=0.20)
    ap.add_argument("--kv-budget", type=int, default=1024)
    ap.add_argument("--tokens-per-tick", type=int, default=16)
    ap.add_argument("--max-model-len", type=int, default=4096)
    ap.add_argument("--need-free-gib", type=float, default=6.0)
    ap.add_argument("--eager", action="store_true", help="disable vLLM CUDA graphs")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    wait_for_window(need_free_gib=args.need_free_gib, max_util_pct=85, timeout_s=7200)
    backend = VLLMBackend(args.model, gpu_memory_utilization=args.gpu_mem,
                          max_model_len=args.max_model_len, enforce_eager=args.eager)
    srv = MetronomeServer(backend, frame_budget_s=args.frame_budget,
                          kv_budget_tokens=args.kv_budget,
                          tokens_per_tick=args.tokens_per_tick)
    print(f"=== Metronome + vLLM real serving: {args.model} "
          f"(budget {args.frame_budget*1000:.0f}ms, KV budget {args.kv_budget}) ===")
    srv.calibrate(probe_ns=(1, 2, 4, 8), reps=4)
    cap = srv.predicted_capacity()
    print(f"calibrated cost: base={srv.cost.batch_base:.1f}ms "
          f"per_session={srv.cost.batch_per_session:.3f}ms alpha={srv.cost.batch_alpha:.5f}ms/tok")
    print(f"deadline-aware admission capacity: {cap} sessions")

    # graceful vs cliff: admission at capacity vs greedy at 2x capacity
    m_adm = srv.serve(cap, n_frames=12, admission=True)
    m_greedy = srv.serve(max(cap * 2, cap + 4), n_frames=12, admission=False)
    print(f"  admission  (offered {cap}):  served={m_adm['n_served']} "
          f"miss={m_adm['miss_rate']:.3f} p99={m_adm['p99_ms']:.1f}ms")
    print(f"  greedy     (offered {max(cap*2,cap+4)}): served={m_greedy['n_served']} "
          f"miss={m_greedy['miss_rate']:.3f} p99={m_greedy['p99_ms']:.1f}ms")

    # real capacity curve: measured p99 vs N
    ns = sorted(set([1, 2, 4, cap // 2 or 1, cap, int(cap * 1.5), cap * 2]))
    curve = []
    for N in ns:
        m = srv.serve(N, n_frames=8, admission=False)
        curve.append((N, m["p99_ms"], m["miss_rate"]))
        print(f"  N={N:3d}  measured p99={m['p99_ms']:.1f}ms  miss={m['miss_rate']:.3f}")

    budget_ms = args.frame_budget * 1000
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ax.plot([c[0] for c in curve], [c[1] for c in curve], "o-", color="#1f77b4",
            label="measured p99 (real vLLM)")
    ax.axhline(budget_ms, color="red", ls=":", label=f"{budget_ms:.0f} ms deadline")
    ax.axvline(cap, color="#2ca02c", ls="--", alpha=0.6, label=f"admission cap {cap}")
    ax.set_xlabel("concurrent sessions N"); ax.set_ylabel("measured p99 tick latency (ms)")
    ax.set_title(f"Metronome+vLLM real serving: {args.model.split('/')[-1]}")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    tag = args.model.split("/")[-1]
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{tag}_vllm.png"), dpi=120)
    plt.close(fig)

    res = dict(model=args.model, frame_budget_ms=budget_ms, kv_budget=args.kv_budget,
               cost=dict(base=srv.cost.batch_base, per_session=srv.cost.batch_per_session,
                         alpha=srv.cost.batch_alpha),
               admission_capacity=cap, admission=m_adm, greedy=m_greedy,
               curve=[dict(N=c[0], p99_ms=c[1], miss_rate=c[2]) for c in curve])
    with open(os.path.join(OUT, f"{tag}_vllm.json"), "w") as fh:
        json.dump(res, fh, indent=2)
    print(f"\nREAL: admission serves {m_adm['n_served']} at {m_adm['miss_rate']:.1%} miss; "
          f"greedy at 2x melts to {m_greedy['miss_rate']:.1%} miss.")
    backend.shutdown()


if __name__ == "__main__":
    main()
