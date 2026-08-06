"""CONTINUOUS full-duplex capacity (real vLLM) — the models' real operating mode, not turn-based.

In continuous full-duplex each frame does prefill(new audio chunk) + decode(output tokens) over a
WINDOWED resident context — incremental, no turns, no whole-utterance burst. We drive exactly that
with VLLMBackend.step(due_sids, n_new): in_tok = n_new*in_frac is prefilled (the per-frame audio
chunk over the prefix-cached context), out_tok is decoded (the per-frame output). The GPU compute
is identical whether prefill tokens are audio embeddings or proxy ids, so this measures the real
per-frame cost. Sweep batch N; capacity = largest N whose per-frame p99 <= the frame budget.
"""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")
import numpy as np
from bench.gpu_probe import wait_for_window
from metronome import models

HF = {"minicpm-o": "openbmb/MiniCPM-o-2_6", "qwen-omni": "Qwen/Qwen2.5-Omni-7B"}
FACTS = {"minicpm-o": "minicpm-o", "qwen-omni": "qwen3-omni"}
# per-frame token budget for continuous full-duplex (documented assumptions):
#   audio_in tokens/frame  +  output tokens/frame.  MiniCPM 1s frame: ~25 audio in + 25 speech out.
#   Qwen 2s frame (seconds_per_chunk=2.0, arXiv:2503.20215): ~50 audio in + 50 out.
FRAME_IO = {"minicpm-o": (25, 25), "qwen-omni": (50, 50)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="minicpm-o", choices=list(HF))
    ap.add_argument("--grid", nargs="*", type=int, default=[1, 8, 32, 64, 128, 192, 256, 384, 512])
    ap.add_argument("--frames", type=int, default=30)
    ap.add_argument("--gpu-mem", type=float, default=0.6)
    ap.add_argument("--max-util", type=int, default=80)
    ap.add_argument("--quantization", default=None)
    ap.add_argument("--window", type=int, default=512)
    ap.add_argument("--mml", type=int, default=4096)
    args = ap.parse_args()
    facts = models.get(FACTS[args.model])
    budget_ms = facts.period_s * 1000.0
    in_tok, out_tok = FRAME_IO[args.model]
    n_new = in_tok + out_tok
    in_frac = in_tok / n_new
    window = args.window or 512
    mml = args.mml or 4096
    wait_for_window(need_free_gib=args.gpu_mem * 97 + 2, max_util_pct=args.max_util, timeout_s=72000)
    from metronome.backends.vllm_backend import VLLMBackend
    extra = dict(enable_chunked_prefill=True, max_num_seqs=max(args.grid) + 16,
                 max_num_batched_tokens=16384)
    if args.quantization:
        extra["quantization"] = args.quantization
    be = VLLMBackend(HF[args.model], gpu_memory_utilization=args.gpu_mem, max_model_len=mml,
                     trust_remote_code=True, enforce_eager=False, in_frac=in_frac, **extra)
    print(f"=== CONTINUOUS full-duplex {args.model} (real vLLM) | frame {budget_ms:.0f}ms | "
          f"per-frame {in_tok} audio-in + {out_tok} out, window {window} ===", flush=True)
    rng = np.random.default_rng(0)
    rows = []
    for N in args.grid:
        # fresh resident contexts (a recent audio window already accumulated)
        for sid in list(be.contexts):
            be.remove_session(sid)
        for i in range(N):
            be.add_session(i, window)
            be.set_context(i, [int(x) for x in rng.integers(0, be.vocab, window)])
        ids = list(range(N))
        for _ in range(3):
            be.step(ids, n_new)             # warmup (CUDA graphs at this N)
        lats = [be.step(ids, n_new) for _ in range(args.frames)]
        p50, p99 = float(np.percentile(lats, 50)), float(np.percentile(lats, 99))
        ok = p99 <= budget_ms
        rows.append(dict(N=N, frame_p50_ms=round(p50, 1), frame_p99_ms=round(p99, 1),
                         meets_budget=ok))
        print(f"  N={N:4d}: frame p50={p50:6.0f}ms p99={p99:6.0f}ms "
              f"{'<=' if ok else '>'} {budget_ms:.0f}ms  ({'real-time' if ok else 'MISS'})",
              flush=True)
        if not ok and p99 > 2 * budget_ms:
            break
    cap = max([r["N"] for r in rows if r["meets_budget"]], default=0)
    res = dict(model=args.model, mode="continuous_full_duplex", budget_ms=budget_ms,
               per_frame_audio_in=in_tok, per_frame_out=out_tok, window=window,
               quantization=args.quantization or "bf16", capacity=cap, curve=rows)
    os.makedirs("results/realtime_load", exist_ok=True)
    out = f"results/realtime_load/fullduplex_{args.model}_{args.quantization or 'bf16'}.json"
    json.dump(res, open(out, "w"), indent=2)
    print(f"\n[{args.model}] CONTINUOUS full-duplex capacity = {cap} concurrent streams "
          f"(per-frame prefill+decode within {budget_ms:.0f}ms)\nsaved {out}", flush=True)


if __name__ == "__main__":
    main()
