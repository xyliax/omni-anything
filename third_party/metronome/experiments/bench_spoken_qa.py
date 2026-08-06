"""Unified spoken-QA benchmark — the SAME audio benchmark across all three paper models.

The three interaction models (Qwen2.5-Omni, MiniCPM-o 4.5, Moshi) share exactly one
modality: speech. So the cross-model benchmark is audio-question-in -> answer-out:

  * Llama Questions  (fixie-ai/llama-questions)       — Moshi's own paper metric (LlamaQ)
  * Web Questions    (fixie-ai/spoken-web-questions)  — Moshi's own paper metric (WebQ)

Each spoken question is fed to the model through the real serving engine; the model's
answer is scored by normalized inclusion match against the gold answer(s) — the standard
spoken-QA metric used in the speech-LM literature. We also report real-time factor
(audio seconds / processing seconds) and dump example traces so the output is auditable.

The omni models run on vLLM (the engine Metronome schedules); Moshi runs through the
TransformersBackend path in its own venv (see bench_spoken_qa_moshi.py). Same data, same
scorer, so the three models are directly comparable — and comparable to the papers.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")

from bench.gpu_probe import wait_for_window

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "spoken_qa")

DATASETS = {
    "llama-questions": ("fixie-ai/llama-questions", "test", "answer"),
    "spoken-web-questions": ("fixie-ai/spoken-web-questions", "test", "answers"),
}

# vLLM omni models: (hf id, audio-prompt builder). The spoken question is IN the audio;
# the text instruction just asks for a concise answer.
def qwen_omni_prompt(instr):
    return ("<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n"
            f"<|audio_bos|><|AUDIO|><|audio_eos|>{instr}<|im_end|>\n<|im_start|>assistant\n")

def minicpm_o_prompt(instr):
    return (f"<|im_start|>user\n(<audio>./</audio>)\n{instr}"
            f"<|im_end|>\n<|im_start|>assistant\n")

OMNI = {
    "qwen-omni": ("Qwen/Qwen2.5-Omni-7B", qwen_omni_prompt, 0.30),
    "minicpm-o": ("openbmb/MiniCPM-o-4_5", minicpm_o_prompt, 0.35),
}

_ARTICLES = {"a", "an", "the"}


def normalize(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^\w\s]", " ", s)
    toks = [t for t in s.split() if t not in _ARTICLES]
    return " ".join(toks)


def correct(pred: str, golds) -> bool:
    """Standard spoken-QA inclusion match: a gold answer appears in the prediction."""
    p = normalize(pred)
    if not p:
        return False
    for g in golds:
        g = normalize(g)
        if g and g in p:
            return True
    return False


def load_samples(ds_key, n):
    from datasets import load_dataset, Audio
    import soundfile as sf
    repo, split, ans_field = DATASETS[ds_key]
    ds = load_dataset(repo, split=split, streaming=True).cast_column("audio", Audio(decode=False))
    out = []
    for row in ds:
        b = row["audio"]["bytes"]
        if not b and row["audio"].get("path") and os.path.exists(row["audio"]["path"]):
            with open(row["audio"]["path"], "rb") as fh: b = fh.read()
        try:
            arr, sr = sf.read(io.BytesIO(b))
        except Exception:
            import librosa
            arr, sr = librosa.load(io.BytesIO(b), sr=16000)
        if getattr(arr, "ndim", 1) > 1:
            arr = arr.mean(axis=1)
        ans = row[ans_field]
        golds = ans if isinstance(ans, list) else [ans]
        out.append(dict(question=row.get("question", ""), golds=golds,
                        audio=(arr.astype("float32"), int(sr)),
                        dur=len(arr) / float(sr)))
        if len(out) >= n:
            break
    return out


def run_omni(model_key, ds_key, n, gpu_mem, max_len, instr):
    from vllm import LLM, SamplingParams
    hf, pbuild, default_mem = OMNI[model_key]
    gpu_mem = gpu_mem or default_mem
    samples = load_samples(ds_key, n)
    llm = LLM(model=hf, trust_remote_code=True, max_model_len=max_len,
              gpu_memory_utilization=gpu_mem, enforce_eager=True,
              limit_mm_per_prompt={"audio": 1})
    sp = SamplingParams(max_tokens=64, temperature=0.0)
    prompt = pbuild(instr)
    rows, n_ok = [], 0
    t_all = time.time()
    for i, s in enumerate(samples):
        t0 = time.time()
        out = llm.generate({"prompt": prompt, "multi_modal_data": {"audio": [s["audio"]]}}, sp)
        dt = time.time() - t0
        ans = out[0].outputs[0].text.strip()
        ok = correct(ans, s["golds"])
        n_ok += ok
        rows.append(dict(question=s["question"], gold=s["golds"][:3], pred=ans,
                         correct=ok, audio_s=round(s["dur"], 1), latency_s=round(dt, 2),
                         rtf=round(s["dur"] / max(dt, 1e-6), 2)))
    wall = time.time() - t_all
    del llm
    import torch; torch.cuda.empty_cache()
    acc = n_ok / max(1, len(rows))
    mean_rtf = sum(r["rtf"] for r in rows) / max(1, len(rows))
    return dict(model=model_key, served_hf=hf, dataset=ds_key, n=len(rows),
                accuracy=round(acc, 3), mean_rtf=round(mean_rtf, 2),
                wall_s=round(wall, 1), traces=rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=list(OMNI), default="qwen-omni")
    ap.add_argument("--dataset", choices=list(DATASETS), default="llama-questions")
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--gpu-mem", type=float, default=0.0)
    ap.add_argument("--need-free-gib", type=float, default=26.0)
    ap.add_argument("--max-util", type=int, default=98)
    ap.add_argument("--max-len", type=int, default=4096)
    ap.add_argument("--instr", default="Answer the question spoken in the audio in a few words.")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    print(f"=== spoken-QA: {args.model} on {args.dataset} (n={args.n}) ===", flush=True)
    wait_for_window(need_free_gib=args.need_free_gib, max_util_pct=args.max_util, timeout_s=36000)
    res = run_omni(args.model, args.dataset, args.n, args.gpu_mem, args.max_len, args.instr)
    fn = os.path.join(OUT, f"{args.model}__{args.dataset}.json")
    with open(fn, "w") as fh:
        json.dump(res, fh, indent=2)
    print(f"\n  {res['model']} / {res['dataset']}: accuracy={res['accuracy']:.1%} "
          f"(n={res['n']})  mean RTF={res['mean_rtf']}x  wall={res['wall_s']}s", flush=True)
    print("  example traces:")
    for r in res["traces"][:5]:
        print(f"    Q={r['question'][:55]!r} gold={r['gold']} -> {r['pred'][:50]!r} "
              f"[{'OK' if r['correct'] else 'x'}]")
    print(f"  saved {fn}")


if __name__ == "__main__":
    main()
