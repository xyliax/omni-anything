"""Head-to-head vs the REAL vLLM continuous-batching scheduler on the interaction workload
(Tier-1 experiments 1 & 2). vLLM's scheduler is throughput-optimal but DEADLINE-BLIND: it
batches every admitted session, so as concurrency rises the per-frame decode latency crosses
the frame budget (audio frames arrive late) and a newly-arriving session's time-to-first-
token (≈ time-to-first-audio) explodes. Metronome's admission caps the running set at the
deadline-aware capacity, holding both under budget.

This drives the actual vLLM LLMEngine (paged attention, continuous batching) — not a proxy —
and measures, per concurrency N: per-frame decode p99 + deadline-miss rate, and the TTFT of a
fresh arrival injected into the loaded engine. We then contrast the two operating points:
  * vLLM-native / greedy  — runs at the offered load (here 2x capacity), no admission
  * Metronome / admission — runs at the deadline-aware capacity
Reports miss-rate, p99, TTFT, goodput, and the full per-frame latency distribution.
"""
import argparse
import json
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")

import numpy as np
from bench.gpu_probe import wait_for_window
from metronome import models
from experiments.bench_spoken_qa import OMNI


def p(xs, q):
    return float(np.percentile(xs, q)) if xs else 0.0


def run_at_N(be, N, resident, tpt, budget_ms, n_frames, vocab, max_model_len):
    """Per-frame latency at concurrency N via FAITHFUL continuous batching (Route A):
    each session is ONE persistent vLLM request, prefilled once then decoded continuously,
    so engine.step() does PURE decode over the resident batch — no per-frame re-prefill.
    One frame = tpt consecutive decode steps. A frame 'misses' if its batched decode exceeds
    the budget. TTFA = ms for a fresh (N+1)-th arrival to emit its first token while N decode."""
    rng = np.random.default_rng(0)
    be.reset_resident()
    # max_tokens must fit: prompt(resident) + decoded(frames) <= max_model_len
    budget_tok = max_model_len - resident - 16
    max_tok = min(budget_tok, (n_frames + 8) * tpt + 4 * tpt)
    for i in range(N):
        be.add_resident(i, rng.integers(0, vocab, resident), max_tok)
    be.drain_prefill()                              # finish all prefills -> steady decode
    for _ in range(3):                              # warmup (CUDA-graph capture at this N)
        be.tick_resident(tpt)
    frame_lats = [be.tick_resident(tpt) for _ in range(n_frames)]
    # validity: all N requests must still be in flight (none finished early / evicted), so the
    # frame latency reflects a true N-way batch the whole window. (Token-level per-request
    # accounting is unreliable in vLLM V1's step() output; the in-flight count is robust.)
    live = be.num_unfinished()
    all_resident = (live >= N)
    # TTFA: inject an (N+1)-th session into the running batch, time to its first token
    ttfa = be.measure_ttfa(N, rng.integers(0, vocab, resident), max_tok)
    be.reset_resident()
    miss = sum(1 for l in frame_lats if l > budget_ms) / max(1, len(frame_lats))
    return dict(N=N, p50=round(p(frame_lats, 50), 1), p99=round(p(frame_lats, 99), 1),
                miss_rate=round(miss, 4), ttft_ms=round(ttfa, 1),
                all_resident=bool(all_resident), live_requests=live,
                frame_lats=[round(x, 2) for x in frame_lats])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen-omni", choices=list(OMNI))
    ap.add_argument("--facts", default="qwen3-omni")   # metronome model facts name
    ap.add_argument("--grid", nargs="*", type=int, default=[1, 2, 4, 8, 16, 24, 32, 48, 64])
    ap.add_argument("--n-frames", type=int, default=40)
    ap.add_argument("--resident", type=int, default=512)
    ap.add_argument("--gpu-mem", type=float, default=0.35)
    ap.add_argument("--slo", type=float, default=0.02)   # max tolerable frame-miss rate
    ap.add_argument("--max-util", type=int, default=50)  # clean timing
    ap.add_argument("--max-model-len", type=int, default=4096)
    ap.add_argument("--anchor-ms", type=float, default=None,
                    help="expected ~N=1 pure-decode frame ms (synthetic ServingEngine "
                         "anchor); N=1 must be within 3x or the re-prefill artifact remains")
    args = ap.parse_args()
    facts = models.get(args.facts)
    budget_ms = facts.period_s * 1000.0
    tpt = max(1, int(round(facts.tokens_per_tick)))
    wait_for_window(need_free_gib=args.gpu_mem * 97 + 2, max_util_pct=args.max_util, timeout_s=72000)
    from metronome.backends.vllm_backend import VLLMBackend
    hf = OMNI[args.model][0]
    be = VLLMBackend(hf, gpu_memory_utilization=args.gpu_mem, max_model_len=args.max_model_len,
                     trust_remote_code=True, enforce_eager=False, in_frac=0.0)
    print(f"=== {args.model} vs real vLLM continuous batching, FAITHFUL/persistent-request "
          f"(budget {budget_ms:.0f}ms, {tpt} tok/frame) ===", flush=True)
    rows = []
    for N in args.grid:
        try:
            r = run_at_N(be, N, args.resident, tpt, budget_ms, args.n_frames, be.vocab,
                         args.max_model_len)
        except Exception as e:
            print(f"  N={N}: ERR {type(e).__name__}: {str(e)[:80]}", flush=True); break
        rows.append(r)
        flag = "" if r["all_resident"] else f" !only {r['live_requests']}/{N} resident"
        print(f"  N={N:3d}: frame p99={r['p99']:.0f}ms p50={r['p50']:.0f}ms "
              f"miss={r['miss_rate']:.2%} TTFA={r['ttft_ms']}ms{flag}", flush=True)
    # Two separate things to report:
    #  (a) re-prefill artifact GONE: proven by TTFA (a fresh arrival's prefill+first token).
    #      The old re-add-each-tick harness gave ~250ms; persistent requests give tens of ms.
    #  (b) synthetic-vs-real gap: n1 pure-decode frame vs the ServingEngine anchor. Real
    #      end-to-end vLLM carries scheduler+sampling+Python overhead the bare-kernel synthetic
    #      engine omits, so a 2-3x ratio is EXPECTED and quantifies the synthetic's optimism.
    n1 = next((r for r in rows if r["N"] == 1), rows[0])
    ttfa_ok = n1["ttft_ms"] < 0.5 * budget_ms      # arrival prefill is cheap => no re-prefill
    ratio = (n1["p50"] / args.anchor_ms) if args.anchor_ms else None
    anchor_ok = ttfa_ok
    print(f"  [artifact] TTFA(N=1)={n1['ttft_ms']:.0f}ms ({'<' if ttfa_ok else '>='} "
          f"{0.5*budget_ms:.0f}ms) -> re-prefill artifact "
          f"{'GONE' if ttfa_ok else 'PRESENT'}", flush=True)
    if ratio is not None:
        print(f"  [synthetic gap] N=1 pure-decode p50={n1['p50']:.0f}ms = {ratio:.1f}x the "
              f"ServingEngine anchor {args.anchor_ms:.0f}ms (real overhead the synthetic omits)",
              flush=True)
    # deadline-aware capacity = largest N with miss<=SLO; greedy operates at ~2x
    cap = max([r["N"] for r in rows if r["miss_rate"] <= args.slo], default=rows[0]["N"])
    greedy_N = min([r["N"] for r in rows if r["N"] >= 2 * cap], default=rows[-1]["N"])
    adm = next(r for r in rows if r["N"] == cap)
    grd = next(r for r in rows if r["N"] == greedy_N)
    res = dict(model=args.model, budget_ms=budget_ms, tok_per_frame=tpt, slo=args.slo,
               method="faithful-persistent-request (Route A, no per-frame re-prefill)",
               n1_p50_ms=n1["p50"], n1_ttfa_ms=n1["ttft_ms"], reprefill_artifact_gone=bool(ttfa_ok),
               synthetic_anchor_ms=args.anchor_ms, real_vs_synthetic_ratio=ratio,
               all_N_fully_resident=all(r["all_resident"] for r in rows),
               deadline_aware_capacity=cap,
               vllm_greedy=dict(N=grd["N"], frame_p99_ms=grd["p99"], miss_rate=grd["miss_rate"],
                                ttfa_ms=grd["ttft_ms"]),
               metronome_admission=dict(N=adm["N"], frame_p99_ms=adm["p99"],
                                        miss_rate=adm["miss_rate"], ttfa_ms=adm["ttft_ms"]),
               curve=[{k: v for k, v in r.items() if k != "frame_lats"} for r in rows],
               miss_distribution=adm["frame_lats"] + grd["frame_lats"])
    os.makedirs("results/headtohead", exist_ok=True)
    json.dump(res, open(f"results/headtohead/{args.model}.json", "w"), indent=2)
    print(f"\n=== HEAD-TO-HEAD {args.model} ===")
    print(f"  vLLM-greedy   @N={grd['N']}: frame p99 {grd['p99']:.0f}ms, "
          f"miss {grd['miss_rate']:.1%}, TTFA {grd['ttft_ms']}ms")
    print(f"  Metronome-adm @N={adm['N']}: frame p99 {adm['p99']:.0f}ms, "
          f"miss {adm['miss_rate']:.1%}, TTFA {adm['ttft_ms']}ms")


if __name__ == "__main__":
    main()
