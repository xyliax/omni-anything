"""Moshi spoken-QA — the 3rd model on the UNIFIED audio benchmark (run with
~/moshi-venv/bin/python). Moshi needs torch<2.10 so it lives in its own venv, separate
from the vLLM omni models; it is driven through its native full-duplex streaming, but
scored with the IDENTICAL spoken-QA scorer (normalized inclusion match) and the same
datasets (fixie-ai/llama-questions, spoken-web-questions) so the number is directly
comparable to Qwen2.5-Omni and MiniCPM-o.

Moshi is a real-time spoken dialogue model: we stream the question audio, then silence,
and read its inner-monologue text stream as the answer.
"""
import argparse
import io
import json
import os
import re
import sys
import time

import numpy as np
import torch

_ARTICLES = {"a", "an", "the"}


def normalize(s):
    s = (s or "").lower()
    s = re.sub(r"[^\w\s]", " ", s)
    return " ".join(t for t in s.split() if t not in _ARTICLES)


def correct(pred, golds):
    p = normalize(pred)
    return bool(p) and any(normalize(g) and normalize(g) in p for g in golds)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="llama-questions",
                    choices=["llama-questions", "spoken-web-questions"])
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--silence-s", type=float, default=8.0)
    ap.add_argument("--out", default="results/spoken_qa_moshi")
    args = ap.parse_args()

    from datasets import load_dataset, Audio
    import soundfile as sf
    import librosa
    from moshi.models import LMGen, loaders

    device = "cuda"
    print("[moshi] loading ...", flush=True)
    ckpt = loaders.CheckpointInfo.from_hf_repo(loaders.DEFAULT_REPO)
    mimi = ckpt.get_mimi(device=device)
    lm = ckpt.get_moshi(device=device)
    tok = ckpt.get_text_tokenizer()
    sr = int(mimi.sample_rate); frame = int(mimi.sample_rate / mimi.frame_rate)
    repo = {"llama-questions": "fixie-ai/llama-questions",
            "spoken-web-questions": "fixie-ai/spoken-web-questions"}[args.dataset]
    af = "answer" if args.dataset == "llama-questions" else "answers"
    ds = load_dataset(repo, split="test", streaming=True).cast_column("audio", Audio(decode=False))

    rows, n_ok = [], 0
    it = iter(ds)
    sil_frames = int(args.silence_s * mimi.frame_rate)
    for k in range(args.n):
        row = next(it)
        arr, asr = sf.read(io.BytesIO(row["audio"]["bytes"]))
        if getattr(arr, "ndim", 1) > 1:
            arr = arr.mean(axis=1)
        if asr != sr:
            arr = librosa.resample(arr.astype("float32"), orig_sr=asr, target_sr=sr)
        g = row[af]; golds = g if isinstance(g, list) else [g]
        qpcm = torch.tensor(arr, dtype=torch.float32, device=device).view(1, 1, -1)
        sil = torch.zeros(1, 1, frame * sil_frames, device=device)
        full = torch.cat([qpcm, sil], dim=2)
        chunks = [full[:, :, i:i + frame] for i in range(0, full.shape[2] - frame + 1, frame)]
        lm_gen = LMGen(lm, use_sampling=True, temp=0.8, temp_text=0.7)
        text = []
        t0 = time.time()
        with torch.no_grad(), mimi.streaming(1), lm_gen.streaming(1):
            first = True
            for ch in chunks:
                codes = mimi.encode(ch)
                if first:
                    lm_gen.step(codes); first = False
                out = lm_gen.step(codes)
                if out is None:
                    continue
                tid = out[0, 0].item()
                if tid == tok.eos_id():
                    break
                if tid not in (0, 3):
                    text.append(tok.id_to_piece(tid).replace("▁", " "))
        ans = "".join(text).strip()
        ok = correct(ans, golds); n_ok += ok
        rows.append(dict(gold=golds[:3], pred=ans[:200], correct=ok,
                         dur=round(len(arr) / sr, 1), gen_s=round(time.time() - t0, 1)))
        print(f"[{k}] {'OK' if ok else 'x'} gold={golds[:2]} -> {ans[:80]!r}", flush=True)

    acc = n_ok / max(1, len(rows))
    res = dict(model="moshi", served_hf=loaders.DEFAULT_REPO, dataset=args.dataset,
               n=len(rows), accuracy=round(acc, 3), via="moshi-native-streaming",
               traces=rows)
    os.makedirs(args.out, exist_ok=True)
    fn = os.path.join(args.out, f"moshi__{args.dataset}.json")
    json.dump(res, open(fn, "w"), indent=2)
    print(f"\n=== moshi / {args.dataset}: accuracy={acc:.1%} (n={len(rows)}) -> {fn}")


if __name__ == "__main__":
    main()
