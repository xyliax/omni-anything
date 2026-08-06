"""Serve Qwen3-Omni-30B-A3B FP8 through vLLM and measure — the fast path my HF-transformers
single-GPU attempt couldn't reach (FP8-Dynamic was dequant-per-forward + degenerate 'HeHeHe').

vLLM 0.19 natively supports `Qwen3OmniMoeForConditionalGeneration` with compressed-tensors
float-quantized weights => native fused FP8 MoE + PagedAttention. This script:
  1. loads the FP8 checkpoint (proves the MoE FP8 path runs at all on one 95GB GPU),
  2. confirms coherent text output (vs the HF dequant garbage),
  3. measures batched decode throughput at B=1..256 — the continuous-full-duplex tick cost
     for the 30B model, comparable to the 448-session 7B incremental-backend result.

Run via the vLLM env python. Polite to the shared GPU via bench.gpu_probe.
"""
import os
os.environ.setdefault("VLLM_LOGGING_LEVEL", "WARNING")
os.environ.setdefault("VLLM_USE_V1", "1")
import sys
import time
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bench.gpu_probe import wait_for_window

MODEL = "sammysun0711/Qwen3-Omni-30B-A3B-Instruct-FP8-Dynamic"


def main(batches, out_tokens, max_model_len, gpu_mem, prompt_len):
    from vllm import LLM, SamplingParams

    wait_for_window(need_free_gib=40, max_util_pct=80, timeout_s=7200)

    t0 = time.time()
    llm = LLM(
        model=MODEL,
        trust_remote_code=True,
        gpu_memory_utilization=gpu_mem,
        max_model_len=max_model_len,
        enforce_eager=False,            # CUDA graphs for the decode steps
        enable_prefix_caching=True,
        max_num_seqs=max(batches),
        limit_mm_per_prompt={"audio": 0, "image": 0, "video": 0},
    )
    load_s = time.time() - t0
    print(f"\n=== LOADED FP8 30B-A3B omni MoE in vLLM in {load_s:.1f}s ===\n")

    # ---- 1. coherence check: does the native FP8 MoE produce real text? ----
    sp = SamplingParams(temperature=0.0, max_tokens=48)
    out = llm.generate(["The capital of France is"], sp)
    txt = out[0].outputs[0].text.strip().replace("\n", " ")
    print(f"COHERENCE (FP8 MoE): 'The capital of France is' -> {txt[:90]!r}\n")

    # ---- 2. batched decode throughput sweep ----
    # Each request: fixed prompt (prefill), then `out_tokens` forced decodes -> sustains a
    # full decode batch so we measure the per-tick decode ceiling of the FP8 MoE.
    base_prompt = "Repeat after me and continue counting: " + " ".join(
        str(i) for i in range(prompt_len))
    results = []
    for B in batches:
        sp = SamplingParams(temperature=0.0, max_tokens=out_tokens,
                            min_tokens=out_tokens, ignore_eos=True)
        prompts = [base_prompt + f" [seq {i}]" for i in range(B)]
        # warmup small + timed run
        t = time.time()
        outs = llm.generate(prompts, sp, use_tqdm=False)
        dt = time.time() - t
        gen_tok = sum(len(o.outputs[0].token_ids) for o in outs)
        # decode-only throughput: total generated tokens / wall (incl one prefill)
        per_tick_ms = dt / out_tokens * 1000          # avg ms per decode step (batch B)
        tok_per_s = gen_tok / dt
        results.append(dict(B=B, wall_s=round(dt, 3), gen_tok=gen_tok,
                            per_step_ms=round(per_tick_ms, 1),
                            tok_per_s=round(tok_per_s, 1)))
        print(f"B={B:4d}  wall={dt:6.2f}s  gen={gen_tok:6d}tok  "
              f"~{per_tick_ms:6.1f} ms/step  {tok_per_s:8.1f} tok/s")

    print("\n=== JSON ===")
    print(json.dumps(dict(model=MODEL, load_s=round(load_s, 1),
                          coherence=txt[:90], max_model_len=max_model_len,
                          out_tokens=out_tokens, prompt_len=prompt_len,
                          results=results), indent=1))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--batches", default="1,8,32,64,128,256")
    ap.add_argument("--out-tokens", type=int, default=32)
    ap.add_argument("--max-model-len", type=int, default=4096)
    ap.add_argument("--gpu-mem", type=float, default=0.85)
    ap.add_argument("--prompt-len", type=int, default=32)
    a = ap.parse_args()
    main([int(x) for x in a.batches.split(",")], a.out_tokens,
         a.max_model_len, a.gpu_mem, a.prompt_len)
