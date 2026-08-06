"""Moshi smoke test (run with ~/moshi-venv/bin/python): feed a real spoken question and
read Moshi's streamed text response. Validates the streaming pipeline before wiring the
full backend. Moshi is full-duplex audio<->audio with an inner-monologue text stream; we
feed the question, then silence to let it answer, and collect the text tokens.
"""
import io
import sys
import time

import numpy as np
import torch


def main():
    from datasets import load_dataset, Audio
    import soundfile as sf
    import librosa
    from moshi.models import LMGen, loaders

    device = "cuda"
    print("[moshi] loading kyutai/moshiko-pytorch-bf16 ...", flush=True)
    ckpt = loaders.CheckpointInfo.from_hf_repo(loaders.DEFAULT_REPO)
    mimi = ckpt.get_mimi(device=device)
    lm = ckpt.get_moshi(device=device)
    tok = ckpt.get_text_tokenizer()
    sr = int(mimi.sample_rate); frame = int(mimi.sample_rate / mimi.frame_rate)
    print(f"[moshi] sr={sr} frame={frame} model_type={ckpt.model_type}", flush=True)

    ds = load_dataset("fixie-ai/llama-questions", split="test", streaming=True
                      ).cast_column("audio", Audio(decode=False))
    it = iter(ds)
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    for k in range(n):
        row = next(it)
        arr, asr = sf.read(io.BytesIO(row["audio"]["bytes"]))
        if getattr(arr, "ndim", 1) > 1:
            arr = arr.mean(axis=1)
        if asr != sr:
            arr = librosa.resample(arr.astype("float32"), orig_sr=asr, target_sr=sr)
        # question frames + ~10s silence to let Moshi answer
        qpcm = torch.tensor(arr, dtype=torch.float32, device=device).view(1, 1, -1)
        sil = torch.zeros(1, 1, frame * 125, device=device)
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
                if tid not in (0, 3):
                    if tid == tok.eos_id():
                        break
                    text.append(tok.id_to_piece(tid).replace("▁", " "))
        ans = "".join(text).strip()
        print(f"\n[{k}] gold={row['answer']!r}  ({time.time()-t0:.1f}s)\n   Moshi: {ans[:200]!r}",
              flush=True)


if __name__ == "__main__":
    main()
