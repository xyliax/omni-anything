"""Diagnose the MMStar gap: run the SAME samples through Qwen2.5-Omni with (A) the bare
"answer with the letter only" prompt (reproduces our 0.325) vs (B) a chain-of-thought
prompt + robust final-letter extraction (what the papers' harnesses use). Direct vLLM, so
this also attributes the gap: if (B) closes it, the limitation was our prompt, not serving.
"""
import argparse
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")


def extract(pred):
    t = re.sub(r"<think>.*?</think>", " ", pred or "", flags=re.S)
    # End-anchored: take the LAST explicit choice statement the model makes.
    pats = [r"answer\s*(?:is)?\s*[:：]?\s*\(?([A-D])\b",
            r"option\s*(?:is)?\s*[:：]?\s*\(?([A-D])\b",
            r"\bchoose\s*\(?([A-D])\b", r"\bcorrect\b[^.]{0,30}?\b([A-D])\b"]
    best = ""
    for p in pats:
        ms = list(re.finditer(p, t, re.I))
        if ms:
            best = ms[-1].group(1).upper()  # last match wins (the conclusion)
    if best:
        return best
    ms = re.findall(r"\b([A-D])\b", t.upper())
    return ms[-1] if ms else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-Omni-7B")
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--gpu-mem", type=float, default=0.28)
    args = ap.parse_args()
    from bench.gpu_probe import wait_for_window
    wait_for_window(need_free_gib=args.gpu_mem * 97 + 2, max_util_pct=100, timeout_s=36000)
    from vllm import LLM, SamplingParams
    from datasets import load_dataset

    ds = load_dataset("Lin-Chen/MMStar", split="val", streaming=True)
    rows = []
    for r in ds:
        rows.append((r["image"].convert("RGB"), r["question"], r["answer"].strip().upper()))
        if len(rows) >= args.n:
            break
    llm = LLM(model=args.model, trust_remote_code=True, max_model_len=4096,
              gpu_memory_utilization=args.gpu_mem, enforce_eager=True,
              limit_mm_per_prompt={"image": 1})
    IMG = "<|vision_bos|><|IMAGE|><|vision_eos|>"
    def run(instr, max_tokens):
        sp = SamplingParams(max_tokens=max_tokens, temperature=0.0)
        ok = 0
        for img, q, gold in rows:
            prompt = ("<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n"
                      f"<|im_start|>user\n{IMG}{q}\n{instr}<|im_end|>\n<|im_start|>assistant\n")
            o = llm.generate({"prompt": prompt, "multi_modal_data": {"image": img}}, sp)
            ok += (extract(o[0].outputs[0].text) == gold)
        return ok / len(rows)

    a = run("Answer with the letter of the correct option only (A, B, C, or D).", 8)
    b = run("Look at the image and think step by step, then end with your final answer "
            "on a new line as 'Answer: X' (X is A, B, C, or D).", 768)
    c = run("Carefully look at the image. First state the correct option letter, then a "
            "one-sentence reason. Begin your reply exactly with 'Answer: X'.", 64)
    print(f"\n=== MMStar diagnostic ({args.model}, n={len(rows)}) ===")
    print(f"  (A) bare-letter (8 tok)        : {a:.3f}   [our 0.325 baseline]")
    print(f"  (B) CoT (768 tok, end-extract) : {b:.3f}")
    print(f"  (C) answer-first (64 tok)      : {c:.3f}")


if __name__ == "__main__":
    main()
