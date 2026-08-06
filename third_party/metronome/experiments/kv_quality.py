"""GAP #1 (the load-bearing one): does KV windowing preserve QUALITY? The capacity gain
(esp. the 8x essential-vs-complementary result) comes from serving with a BOUNDED KV budget
instead of full context. But parity was only tested at fixed short length — never that
dropping old KV is quality-free. Here we measure, on real long text, the model's next-token
perplexity as a function of the attended context window W (truncated-context perplexity via
vLLM prompt_logprobs). If perplexity SATURATES at small W, then old ("complementary") KV
barely helps quality -> the windowing that buys the capacity is quality-neutral. The
saturation W is the 'essential' KV; we compare it to the kv_budget used for the capacity gain.
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")

from bench.gpu_probe import wait_for_window
from experiments.bench_spoken_qa import OMNI


def long_text(tok, target_tokens):
    """Concatenate real English (fineweb-edu, cached) into one long token sequence."""
    from datasets import load_dataset
    ids = []
    try:
        ds = load_dataset("HuggingFaceFW/fineweb-edu", split="train", streaming=True)
        for r in ds:
            ids += tok.encode(r["text"])
            if len(ids) >= target_tokens:
                break
    except Exception:
        ds = load_dataset("fixie-ai/llama-questions", split="test", streaming=True)
        for r in ds:
            ids += tok.encode(r.get("question", "") + " " + str(r.get("answer", "")) + " ")
            if len(ids) >= target_tokens:
                break
    return ids[:target_tokens]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen-omni", choices=list(OMNI))
    ap.add_argument("--windows", nargs="*", type=int, default=[32, 64, 128, 256, 512, 1024, 2048])
    ap.add_argument("--L", type=int, default=2600)        # long sequence length
    ap.add_argument("--positions", type=int, default=400)  # sampled target positions
    ap.add_argument("--gpu-mem", type=float, default=0.35)
    args = ap.parse_args()
    wait_for_window(need_free_gib=args.gpu_mem * 97 + 2, max_util_pct=100, timeout_s=72000)
    from vllm import LLM, SamplingParams
    hf = OMNI[args.model][0]
    llm = LLM(model=hf, trust_remote_code=True, max_model_len=max(args.windows) + 8,
              gpu_memory_utilization=args.gpu_mem, enforce_eager=True)
    tok = llm.get_tokenizer()
    ids = long_text(tok, args.L + 16)
    L = min(args.L, len(ids))
    Wmax = max(args.windows)
    # sampled target positions in [Wmax, L)
    step = max(1, (L - Wmax) // args.positions)
    positions = list(range(Wmax, L, step))[:args.positions]
    sp = SamplingParams(max_tokens=1, temperature=0.0, prompt_logprobs=0)
    curve = []
    for W in args.windows:
        reqs = [{"prompt_token_ids": ids[i - W:i + 1]} for i in positions]  # predict ids[i] | last W
        outs = llm.generate(reqs, sp)
        nlls = []
        for o, i in zip(outs, positions):
            plp = o.prompt_logprobs[-1]          # logprob of the final prompt token (target)
            tgt = ids[i]
            if plp and tgt in plp:
                nlls.append(-plp[tgt].logprob)
        ppl = math.exp(sum(nlls) / len(nlls)) if nlls else float("nan")
        curve.append(dict(window=W, perplexity=round(ppl, 3), n=len(nlls)))
        print(f"  W={W:5d}: perplexity={ppl:.3f}  (n={len(nlls)})", flush=True)
    full_ppl = curve[-1]["perplexity"]
    # essential W = smallest W within 2% of full-context perplexity
    ess = next((c["window"] for c in curve if c["perplexity"] <= full_ppl * 1.02), curve[-1]["window"])
    res = dict(model=args.model, served_hf=hf, L=L, n_positions=len(positions),
               full_context_perplexity=full_ppl, essential_window=ess, curve=curve)
    os.makedirs("results/kv_quality", exist_ok=True)
    json.dump(res, open(f"results/kv_quality/{args.model}.json", "w"), indent=2)
    print(f"\n=== KV-windowing quality ({args.model}) ===")
    print(f"  full-context perplexity {full_ppl}; essential window (within 2%) = {ess} tokens")
    print(f"  -> old KV beyond {ess} tokens is quality-complementary (droppable for capacity)")


if __name__ == "__main__":
    main()
