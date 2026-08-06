"""Correctness of the serving path — does Metronome's periodic-session serving produce
the SAME tokens a direct, trusted greedy decode would, or is it emitting garbage?

We take a real prompt, get the reference continuation from a single trusted vLLM greedy
generate, then serve the identical prompt through the Metronome VLLMBackend one decode
token per frame (in_frac=0 => pure autoregressive decode, exactly what an interaction
model does per tick) and accumulate the streamed tokens. A correct serving path
reproduces the reference greedily, token-for-token; random/garbage output would diverge
immediately. We report exact-match fraction and the longest common prefix length.

Small, fast, cached model (Qwen3-0.6B) so this can run in a modest GPU window.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")

from bench.gpu_probe import wait_for_window

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "correctness")

PROMPTS = [
    "The capital of France is",
    "Here is a simple Python function to add two numbers:\n\ndef add(a, b):",
    "Once upon a time, in a quiet village by the sea, there lived",
    "The three primary colors are red, yellow, and",
]


def lcp(a, b):
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen3-0.6B")
    ap.add_argument("--gpu-mem", type=float, default=0.15)
    ap.add_argument("--need-free-gib", type=float, default=6.0)
    ap.add_argument("--max-util", type=int, default=92)
    ap.add_argument("--gen", type=int, default=24, help="tokens to generate per prompt")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    print(f"=== correctness trace ({args.model}) — waiting for GPU window ===", flush=True)
    wait_for_window(need_free_gib=args.need_free_gib, max_util_pct=args.max_util,
                    timeout_s=36000)

    from vllm import LLM, SamplingParams
    from metronome.backends.vllm_backend import VLLMBackend

    # --- reference: one trusted greedy generate per prompt -------------------
    ref_llm = LLM(model=args.model, gpu_memory_utilization=args.gpu_mem,
                  max_model_len=2048, enforce_eager=True, enable_prefix_caching=False)
    tok = ref_llm.get_tokenizer()
    sp = SamplingParams(max_tokens=args.gen, temperature=0.0)
    refs = []
    for p in PROMPTS:
        o = ref_llm.generate(p, sp)
        refs.append(list(o[0].outputs[0].token_ids))
    prompt_ids = [tok.encode(p) for p in PROMPTS]
    del ref_llm
    import torch; torch.cuda.empty_cache()

    # --- serve the same prompts through Metronome's periodic-session path ----
    # in_frac=0 => each frame is a pure decode tick (no synthetic input chunk), so the
    # session continues its own context greedily — the serving analogue of the reference.
    backend = VLLMBackend(args.model, gpu_memory_utilization=args.gpu_mem,
                          max_model_len=2048, in_frac=0.0, enforce_eager=True)
    results = []
    for i, (p, pids, ref) in enumerate(zip(PROMPTS, prompt_ids, refs)):
        sid = 1000 + i
        backend.add_session(sid, kv_budget_tokens=2048)
        backend.set_context(sid, pids)
        served = []
        for _ in range(args.gen):
            backend.step([sid], n_new=1)            # one batched decode tick
            served.extend(backend.last_outputs.get(sid, []))
        backend.remove_session(sid)
        m = lcp(served, ref)
        exact = sum(1 for x, y in zip(served, ref) if x == y)
        rec = dict(prompt=p, gen=args.gen, lcp=m,
                   exact_frac=round(exact / max(1, len(ref)), 3),
                   ref_text=tok.decode(ref), served_text=backend.detokenize(served))
        results.append(rec)
        print(f"\n[{i}] {p!r}", flush=True)
        print(f"    ref   : {rec['ref_text']!r}")
        print(f"    served: {rec['served_text']!r}")
        print(f"    longest-common-prefix={m}/{len(ref)}  exact_frac={rec['exact_frac']}")
    backend.shutdown()

    agg = dict(model=args.model, n_prompts=len(PROMPTS),
               mean_exact_frac=round(sum(r["exact_frac"] for r in results) / len(results), 3),
               mean_lcp=round(sum(r["lcp"] for r in results) / len(results), 1),
               per_prompt=results)
    with open(os.path.join(OUT, "correctness_trace.json"), "w") as fh:
        json.dump(agg, fh, indent=2)
    print(f"\n=== CORRECTNESS: mean exact-match {agg['mean_exact_frac']:.1%}, "
          f"mean LCP {agg['mean_lcp']} tokens (serving reproduces reference greedy) ===")


if __name__ == "__main__":
    main()
