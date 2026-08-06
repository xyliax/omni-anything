"""Run Moshi (full-duplex) on Full-Duplex-Bench inputs (run with ~/moshi-venv/bin/python).

For each example folder under --root (each has input.wav, the user-side audio with
pauses/turns), stream the audio through Moshi full-duplex and write Moshi's spoken
RESPONSE audio to output.wav. Moshi emits an audio token stream alongside its text inner
monologue every 80 ms frame; we decode the audio codes back to PCM with Mimi. A later
transcription step turns output.wav into the output.json (word timestamps) the FD-Bench
evaluators consume to compute turn-taking metrics (TOR / latency).
"""
import argparse
import glob
import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="dir of example folders with input.wav")
    ap.add_argument("--input-name", default="input.wav")
    ap.add_argument("--output-name", default="output.wav")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    import soundfile as sf
    import librosa
    from moshi.models import LMGen, loaders

    try:
        from bench.gpu_probe import wait_for_window
        wait_for_window(need_free_gib=18, max_util_pct=100, timeout_s=36000)
    except Exception as e:
        print(f"[moshi-fdbench] window probe skipped: {e}", flush=True)

    device = "cuda"
    print("[moshi-fdbench] loading model ...", flush=True)
    ckpt = loaders.CheckpointInfo.from_hf_repo(loaders.DEFAULT_REPO)
    mimi = ckpt.get_mimi(device=device)
    lm = ckpt.get_moshi(device=device)
    sr = int(mimi.sample_rate); frame = int(mimi.sample_rate / mimi.frame_rate)

    dirs = sorted(d for d in glob.glob(os.path.join(args.root, "*")) if os.path.isdir(d))
    if args.limit:
        dirs = dirs[:args.limit]
    print(f"[moshi-fdbench] {len(dirs)} examples under {args.root}", flush=True)
    for i, d in enumerate(dirs):
        inp = os.path.join(d, args.input_name)
        outp = os.path.join(d, args.output_name)
        if not os.path.exists(inp):
            continue
        if os.path.exists(outp):           # resumable: skip already-generated outputs
            continue
        arr, asr = sf.read(inp)
        if getattr(arr, "ndim", 1) > 1:
            arr = arr.mean(axis=1)
        if asr != sr:
            arr = librosa.resample(arr.astype("float32"), orig_sr=asr, target_sr=sr)
        pcm = torch.tensor(arr, dtype=torch.float32, device=device).view(1, 1, -1)
        chunks = [pcm[:, :, j:j + frame] for j in range(0, pcm.shape[2] - frame + 1, frame)]
        lm_gen = LMGen(lm, use_sampling=True, temp=0.8, temp_text=0.7)
        out_pcm = []
        with torch.no_grad(), mimi.streaming(1), lm_gen.streaming(1):
            first = True
            for ch in chunks:
                codes = mimi.encode(ch)
                if first:
                    lm_gen.step(codes); first = False
                tokens = lm_gen.step(codes)
                if tokens is None:
                    continue
                if lm_gen.lm_model.dep_q > 0:                 # audio codebooks present
                    wav = mimi.decode(tokens[:, 1:])           # (1,1,frame)
                    out_pcm.append(wav[0, 0].detach().cpu().numpy())
        audio = np.concatenate(out_pcm) if out_pcm else np.zeros(frame, dtype="float32")
        sf.write(os.path.join(d, args.output_name), audio.astype("float32"), sr)
        if i % 10 == 0:
            print(f"  [{i}/{len(dirs)}] {os.path.basename(d)}: out {len(audio)/sr:.1f}s",
                  flush=True)
    print("[moshi-fdbench] done — output.wav written for all examples", flush=True)


if __name__ == "__main__":
    main()
