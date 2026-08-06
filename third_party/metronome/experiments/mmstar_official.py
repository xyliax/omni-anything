"""MMStar via the OFFICIAL VLMEvalKit methodology (prompt + answer extraction), run
through our vLLM serving stack. Isolates whether our 0.30 was a hand-rolled-harness
artifact: official prompt is open-ended ("Please select the correct answer from the
options above") and can_infer matches the response against the option LETTER *and* the
option TEXT CONTENT (ported verbatim from vlmeval/utils/matching_util.py)."""
import argparse
import os
import re
import string
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")

_VERBOSE_ANSWER_RE = re.compile(r"(?i)(?:correct\s+)?answer\s+is\s+\**([ABCD])\**")


def can_infer_option(answer, choices):
    a = answer
    for c in ".()[],:;!*#{}":
        a = a.replace(c, " ")
    splits = [x.strip() for x in a.split()]
    cnt = sum(1 for c in choices if c in splits)
    if cnt == 1:
        for ch in choices:
            if ch in splits and splits.index(ch) > (len(splits) - 5):
                return ch
    m = _VERBOSE_ANSWER_RE.search(answer or "")
    if m and m.group(1).upper() in choices:
        return m.group(1).upper()
    return False


def can_infer_text(answer, choices):
    answer = answer.lower()
    if len(answer) > 2 * sum(len(str(v)) for v in choices.values()):
        return False
    ch = {k: str(v).lower() for k, v in choices.items()}
    cands = [k for k in ch if ch[k] and ch[k] in answer]
    return cands[0] if len(cands) == 1 else False


def can_infer(answer, choices):
    o = can_infer_option(str(answer), choices)
    return o if o else can_infer_text(str(answer), choices)


def parse_choices(q):
    parts = re.split(r"Options?\s*:", q, maxsplit=1)
    if len(parts) < 2:
        return {}, q
    stem, opt = parts[0].strip(), parts[1]
    choices = {}
    for m in re.finditer(r"([A-D])\s*[:.]\s*(.+?)(?=\s*,?\s*[A-D]\s*[:.]|$)", opt, re.S):
        choices[m.group(1)] = m.group(2).strip().rstrip(".,").strip()
    return choices, stem


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-Omni-7B")
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--gpu-mem", type=float, default=0.40)
    ap.add_argument("--max-len", type=int, default=16384)   # some MMStar images use 5k+ vision tokens
    args = ap.parse_args()
    from bench.gpu_probe import wait_for_window
    wait_for_window(need_free_gib=args.gpu_mem * 97 + 2, max_util_pct=100, timeout_s=36000)
    from vllm import LLM, SamplingParams
    from datasets import load_dataset

    # full val set (1500) unless --n smaller; non-streaming so we cover all categories
    full = load_dataset("Lin-Chen/MMStar", split="val")
    if args.n and args.n < len(full):
        full = full.select(range(args.n))
    llm = LLM(model=args.model, trust_remote_code=True, max_model_len=args.max_len,
              gpu_memory_utilization=args.gpu_mem, enforce_eager=True,
              limit_mm_per_prompt={"image": 1})
    IMG = "<|vision_bos|><|IMAGE|><|vision_eos|>"
    sp = SamplingParams(max_tokens=512, temperature=0.0)
    # BATCH all prompts in one generate call (vLLM batches internally -> fast at scale)
    reqs, meta = [], []
    for r in full:
        q, gold = r["question"], r["answer"].strip().upper()
        choices, _ = parse_choices(q)
        prompt = ("<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n"
                  f"{IMG}{q}\nPlease select the correct answer from the options above. "
                  "<|im_end|>\n<|im_start|>assistant\n")
        reqs.append({"prompt": prompt, "multi_modal_data": {"image": r["image"].convert("RGB")}})
        meta.append((choices, gold, r.get("category", "")))
    outs = llm.generate(reqs, sp)
    ok = miss_parse = 0
    from collections import defaultdict
    bycat = defaultdict(lambda: [0, 0])
    per_sample = []
    for o, (choices, gold, cat) in zip(outs, meta):
        resp = o.outputs[0].text
        ext = can_infer(resp, choices) if choices else False
        miss_parse += (ext is False)
        c = (ext == gold)
        ok += c
        bycat[cat][0] += c; bycat[cat][1] += 1
        per_sample.append(dict(response=resp, choices=choices, gold=gold, category=cat,
                               rule_ext=(ext if ext else None)))
    import json
    res = dict(model=args.model, n=len(meta), accuracy=round(ok / len(meta), 4),
               unparseable=miss_parse, by_category={k: round(v[0] / v[1], 3) for k, v in bycat.items()})
    os.makedirs("results/mmstar", exist_ok=True)
    json.dump(res, open("results/mmstar/mmstar_official.json", "w"), indent=2)
    json.dump(per_sample, open("results/mmstar/mmstar_outputs.json", "w"))
    print(f"\n=== MMStar OFFICIAL methodology ({args.model}, n={len(meta)}) ===")
    print(f"  accuracy: {res['accuracy']}   unparseable: {miss_parse}/{len(meta)}")
    print(f"  by category: {res['by_category']}")
    print(f"  [hand-rolled n=40 was 0.325; paper full-set = 0.640]")


if __name__ == "__main__":
    main()
