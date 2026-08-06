"""Re-ground the cost model on REAL vLLM (not the synthetic TickKernel/ServingEngine).

The synthetic kernel processes n_new tokens as a PARALLEL chunk (one weight-load amortized
over all n_new), but real autoregressive serving decodes them SEQUENTIALLY (n_new memory-bound
steps). That mismodels the per-frame cost — the head-to-head showed the synthetic engine is
2-3x optimistic. Here we re-measure per-frame latency vs (batch B, context L) on the real vLLM
engine via the faithful persistent-request path (one request/session, prefilled once then pure
decode), fit the SAME CostModel (c_fixed + alpha*L; batch base+per_session*B+alpha*sumL), and
recompute MSCS (B1 full-KV vs M windowed) so we can state real-grounded ABSOLUTE capacities and
confirm the RELATIVE gain survives.

Outputs: results/cost_model/<name>_real.json, results/core/reground_<name>.json
"""
import argparse
import json
import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")

import numpy as np
from bench.gpu_probe import wait_for_window
from metronome import models
from metronome.cost_model import CostModel, fit_single, fit_batch
from experiments._common import load_cost, hbm_kv_bytes
from experiments.bench_spoken_qa import OMNI

CM_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "results", "cost_model")


@dataclass
class RealTiming:
    """Minimal object exposing exactly what fit_single/fit_batch read."""
    model: str
    device: str
    batch_sessions: int
    total_kv_tokens: int
    n_new: int
    p50: float
    p99: float
    mean: float
    reps: int


def measure(be, lengths, tpt, reps, warmup, max_model_len, name):
    """Real per-frame (tpt sequential decode steps) latency over B sessions whose contexts
    are `lengths`. Returns a RealTiming binned at the window-midpoint effective context."""
    B = len(lengths)
    rng = np.random.default_rng(0)
    be.reset_resident()
    # max_tokens budget per request: room for warmup + measured frames
    headroom = (warmup + reps + 4) * tpt
    for i, L in enumerate(lengths):
        max_tok = min(max_model_len - L - 8, headroom)
        if max_tok < headroom:                       # context too long for this max_model_len
            return None
        be.add_resident(i, rng.integers(0, be.vocab, L), max_tok)
    be.drain_prefill()
    for _ in range(warmup):
        be.tick_resident(tpt)
    if be.num_unfinished() < B:                       # a request finished/evicted -> invalid
        return None
    lats = [be.tick_resident(tpt) for _ in range(reps)]
    be.reset_resident()
    # effective context during the measured window: post-prefill (L+1) + warmup + half the run
    eff_L = [L + 1 + warmup * tpt + (reps * tpt) // 2 for L in lengths]
    return RealTiming(model=name, device="cuda-vllm", batch_sessions=B,
                      total_kv_tokens=int(sum(eff_L)), n_new=tpt,
                      p50=float(np.percentile(lats, 50)), p99=float(np.percentile(lats, 99)),
                      mean=float(np.mean(lats)), reps=reps)


def fit_real(name, hf, facts_name, gpu_mem, max_util, reps):
    facts = models.get(facts_name)
    tpt = max(1, int(round(facts.tokens_per_tick)))
    ceiling = facts.context_ceiling_tokens
    mml = min(ceiling, 16384) + 512                   # cap KV footprint; covers the L grid
    # start at a small positive L (vLLM rejects empty prompts); c_fixed is the fit intercept
    single_Ls = [L for L in (16, 128, 256, 512, 1024, 2048, 3072, 4096, 6144, 8192,
                             12288, 16384) if L <= mml - 512]
    # Sweep B at FIXED small L=512 (isolates per_session, where alpha*sumL is negligible) up
    # to high concurrency, plus a few (B,L) points to pin alpha. A B<=8 grid let the linear
    # fit's alpha term absorb batch scaling and under-fit per_session; high-B small-L fixes it.
    Lbig = min(8192, mml - 512)
    batch_plan = ([(B, 512) for B in (1, 2, 4, 8, 16, 32, 48)]
                  + [(B, 2048) for B in (4, 8, 16)]
                  + [(B, Lbig) for B in (2, 4, 8)])
    wait_for_window(need_free_gib=gpu_mem * 97 + 2, max_util_pct=max_util, timeout_s=72000)
    from metronome.backends.vllm_backend import VLLMBackend
    be = VLLMBackend(hf, gpu_memory_utilization=gpu_mem, max_model_len=mml,
                     trust_remote_code=True, enforce_eager=False, in_frac=0.0)
    print(f"=== {name}: re-grounding cost model on REAL vLLM "
          f"(budget {facts.period_s*1000:.0f}ms, {tpt} tok/frame, mml {mml}) ===", flush=True)
    singles = []
    for L in single_Ls:
        t = measure(be, [L], tpt, reps, 3, mml, name)
        if t is None:
            print(f"  single L={L}: skip (footprint)", flush=True); continue
        singles.append(t)
        print(f"  single L={L:6d} (eff {t.total_kv_tokens:6d}): p50={t.p50:7.1f}ms "
              f"p99={t.p99:7.1f}ms", flush=True)
    batches = []
    for (B, L) in batch_plan:
        t = measure(be, [L] * B, tpt, reps, 3, mml, name)
        if t is None:
            print(f"  batch B={B} L={L}: skip (footprint)", flush=True); continue
        batches.append(t)
        print(f"  batch B={B} L={L:5d}: p50={t.p50:7.1f}ms p99={t.p99:7.1f}ms", flush=True)
    del be
    import torch; torch.cuda.empty_cache()
    cost = fit_single(singles, kv_bytes_per_token=facts.kv_bytes_per_token,
                      notes=f"{name} REAL vLLM (sequential decode, persistent request)")
    cost = fit_batch(cost, batches)
    os.makedirs(CM_DIR, exist_ok=True)
    cost.to_json(os.path.join(CM_DIR, f"{name}_real.json"))
    return cost, facts


def mscs_for(cost, facts, n_max=1024, n_frames=200):
    """Real-grounded MSCS for B1 (full-KV) and M (windowed), reusing the sim pipeline.
    Uses mscs_served on (offered, admitted, miss) exactly as core_eval.fig_mscs does — so
    M returns the admission plateau (admitted), not the offered-load cap."""
    from experiments.core_eval import mscs_curve, TARGET_MISS
    from bench.metrics import mscs_served
    ceiling = facts.context_ceiling_tokens
    window = max(512, ceiling // 4)
    hbm = hbm_kv_bytes()
    out = {}
    for preset in ("B1", "M"):
        # curve tuples: (n, miss, p99, p999, admitted, quality)
        curve = mscs_curve(preset, cost, facts, ceiling, window, hbm, n_max, n_frames)
        out[preset] = mscs_served([(x[0], x[4], x[1]) for x in curve], TARGET_MISS)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=["minicpm-o", "qwen-omni"])
    ap.add_argument("--reps", type=int, default=12)
    ap.add_argument("--max-util", type=int, default=60)
    args = ap.parse_args()
    gpu_mem = {"qwen-omni": 0.35, "minicpm-o": 0.45}
    facts_name = {"qwen-omni": "qwen3-omni", "minicpm-o": "minicpm-o"}
    summary = {}
    for m in args.models:
        hf = OMNI[m][0]
        fn = facts_name[m]
        cost, facts = fit_real(m, hf, fn, gpu_mem.get(m, 0.4), args.max_util, args.reps)
        syn = load_cost(fn)
        real_mscs = mscs_for(cost, facts)
        # synthetic MSCS for the same model, for the side-by-side
        syn_mscs = mscs_for(syn, facts)
        rec = dict(
            model=m, facts=fn,
            cost_real=dict(c_fixed=round(cost.c_fixed, 4), alpha=round(cost.alpha, 6),
                           batch_base=round(cost.batch_base, 4),
                           batch_per_session=round(cost.batch_per_session, 4),
                           batch_alpha=round(cost.batch_alpha, 6),
                           tail_factor=round(cost.tail_factor, 4),
                           single_max_rel_resid=round(cost.single_max_rel_resid, 4),
                           batch_r2=round(cost.batch_r2, 4)),
            cost_synth=dict(c_fixed=round(syn.c_fixed, 4), alpha=round(syn.alpha, 6),
                            batch_base=round(syn.batch_base, 4),
                            batch_per_session=round(syn.batch_per_session, 4),
                            batch_alpha=round(syn.batch_alpha, 6)),
            mscs_real=real_mscs, mscs_synth=syn_mscs,
            gain_real=round(real_mscs["M"] / max(1, real_mscs["B1"]), 2),
            gain_synth=round(syn_mscs["M"] / max(1, syn_mscs["B1"]), 2),
            synth_optimism_cfixed=round(cost.c_fixed / max(syn.c_fixed, 1e-9), 2))
        summary[m] = rec
        os.makedirs(os.path.join(os.path.dirname(CM_DIR), "core"), exist_ok=True)
        json.dump(rec, open(os.path.join(os.path.dirname(CM_DIR), "core",
                                         f"reground_{m}.json"), "w"), indent=2)
        print(f"\n=== {m} RE-GROUNDED ===")
        print(f"  c_fixed: synth {syn.c_fixed:.2f}ms -> real {cost.c_fixed:.2f}ms "
              f"({rec['synth_optimism_cfixed']}x)   alpha: synth {syn.alpha:.5f} -> "
              f"real {cost.alpha:.5f} ms/tok", flush=True)
        print(f"  MSCS B1: synth {syn_mscs['B1']} -> real {real_mscs['B1']}   "
              f"M: synth {syn_mscs['M']} -> real {real_mscs['M']}", flush=True)
        print(f"  M/B1 gain: synth {rec['gain_synth']}x -> real {rec['gain_real']}x "
              f"(relative gain {'PRESERVED' if rec['gain_real'] >= 0.8*rec['gain_synth'] else 'CHANGED'})",
              flush=True)
    json.dump(summary, open(os.path.join(os.path.dirname(CM_DIR), "core",
                                         "reground_summary.json"), "w"), indent=2)
    print("\nsaved results/core/reground_summary.json")


if __name__ == "__main__":
    main()
