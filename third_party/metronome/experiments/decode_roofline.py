"""Clean DECODE-ROOFLINE microbench on REAL vLLM (real model weights, real PagedAttention) —
NOT synthetic. Isolates the decode compute ceiling that end-to-end runs can't measure (vLLM
generates ahead of frame-paced delivery). N persistent requests (prefilled once, ignore_eos)
all decode together; we time a single engine.step() (= one decode token for all N) and the
per-frame cost = tpt * that. Sweeping N shows the roofline: flat (memory-bound, per-step ~weight
read) until the compute knee B*, then linear. Answers: at what N does a tpt-token frame cross
the budget?
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")

import numpy as np
from bench.gpu_probe import wait_for_window

HF = {"minicpm-o": "openbmb/MiniCPM-o-2_6", "qwen-omni": "Qwen/Qwen2.5-Omni-7B"}
FACTS = {"minicpm-o": "minicpm-o", "qwen-omni": "qwen3-omni"}


def time_step(be, reps):
    """Median + p99 ms for ONE engine.step() (one decode token across the resident batch)."""
    lat = []
    for _ in range(reps):
        t0 = time.perf_counter()
        be._pump()                       # exactly one engine.step()
        lat.append((time.perf_counter() - t0) * 1000.0)
    return float(np.percentile(lat, 50)), float(np.percentile(lat, 99))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="minicpm-o", choices=list(HF))
    ap.add_argument("--grid", nargs="*", type=int, default=[1, 8, 32, 64, 128, 192, 256, 384, 512])
    ap.add_argument("--ctx", type=int, default=512)      # resident context length per session
    ap.add_argument("--reps", type=int, default=40)
    ap.add_argument("--gpu-mem", type=float, default=0.6)
    ap.add_argument("--max-util", type=int, default=80)
    ap.add_argument("--quantization", default=None)
    args = ap.parse_args()
    from metronome import models
    facts = models.get(FACTS[args.model])
    budget_ms = facts.period_s * 1000.0
    tpt = max(1, int(round(facts.tokens_per_tick)))
    out_tpt = 25         # realistic output decode tokens per frame (speech rate), reported too
    wait_for_window(need_free_gib=args.gpu_mem * 97 + 2, max_util_pct=args.max_util, timeout_s=72000)
    from metronome.backends.vllm_backend import VLLMBackend
    extra = dict(enable_chunked_prefill=True, max_num_seqs=max(args.grid) + 16,
                 max_num_batched_tokens=16384)
    if args.quantization:
        extra["quantization"] = args.quantization
    be = VLLMBackend(HF[args.model], gpu_memory_utilization=args.gpu_mem, max_model_len=4096,
                     trust_remote_code=True, enforce_eager=False, in_frac=0.0, **extra)
    print(f"=== decode roofline {args.model} (REAL vLLM, ctx={args.ctx}, budget {budget_ms:.0f}ms, "
          f"facts_tpt={tpt} out_tpt={out_tpt}) ===", flush=True)
    rng = np.random.default_rng(0)
    rows = []
    for N in args.grid:
        be.reset_resident()
        for i in range(N):
            be.add_resident(i, rng.integers(0, be.vocab, args.ctx), max_tokens=8000)
        be.drain_prefill()
        for _ in range(5):
            be._pump()                   # warmup steady-state decode
        p50, p99 = time_step(be, args.reps)
        live = be.num_unfinished()
        frame50, frame99 = p50 * out_tpt, p99 * out_tpt
        rows.append(dict(N=N, live=live, step_p50_ms=round(p50, 2), step_p99_ms=round(p99, 2),
                         frame_p50_ms=round(frame50, 1), frame_p99_ms=round(frame99, 1),
                         meets_budget=bool(frame99 <= budget_ms)))
        print(f"  N={N:4d} (live {live:4d}): step p50={p50:.2f}ms p99={p99:.2f}ms -> "
              f"{out_tpt}-tok frame p99={frame99:.0f}ms {'<=' if frame99<=budget_ms else '>'} "
              f"{budget_ms:.0f}ms", flush=True)
    be.reset_resident()
    cap = max([r["N"] for r in rows if r["meets_budget"]], default=0)
    res = dict(model=args.model, ctx=args.ctx, out_tpt=out_tpt, budget_ms=budget_ms,
               quantization=args.quantization or "bf16", decode_roofline_capacity=cap, curve=rows)
    os.makedirs("results/realtime_load", exist_ok=True)
    json.dump(res, open(f"results/realtime_load/decode_roofline_{args.model}"
                        f"_{args.quantization or 'bf16'}.json", "w"), indent=2)
    print(f"\n[{args.model}] DECODE-ceiling for {out_tpt}-tok frames @ {budget_ms:.0f}ms budget "
          f"= {cap} concurrent sessions (single-step p50 grows with batch = roofline)", flush=True)


if __name__ == "__main__":
    main()
