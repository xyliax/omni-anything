"""#3 — Batched multi-session Moshi full-duplex (real model, moshi venv, real silicon).

Moshi is a streaming-codec full-duplex model: each 80 ms frame, Mimi encodes the incoming audio
and the LM emits text+audio tokens. This is the model where per-tick batched ingestion is NATIVE
(no encoder window / no incremental-KV problem). We batch B concurrent streams via
`streaming_forever(B)` and time ONE batched frame (Mimi.encode + LMGen.step) over the batch, to
answer: how many concurrent real-time full-duplex Moshi sessions fit per 80 ms frame?

Run with: ~/moshi-venv/bin/python experiments/moshi_batched.py
"""
import argparse, json, os, sys, time
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batches", nargs="*", type=int, default=[1, 2, 4, 8, 16, 32, 48, 64, 96, 128])
    ap.add_argument("--steps", type=int, default=40)
    args = ap.parse_args()
    import torch
    from moshi.models import LMGen, loaders
    repo = loaders.DEFAULT_REPO
    ckpt = loaders.CheckpointInfo.from_hf_repo(repo)
    mimi = ckpt.get_mimi(device="cuda")
    lm = ckpt.get_moshi(device="cuda")
    frame = int(mimi.sample_rate / mimi.frame_rate)
    budget_ms = 1000.0 / mimi.frame_rate          # one Moshi frame (~80 ms) — the real-time budget
    print(f"=== batched Moshi full-duplex (sr={mimi.sample_rate} frame_rate={mimi.frame_rate:.1f}Hz "
          f"-> {frame} samples/frame, budget {budget_ms:.0f}ms) ===", flush=True)
    rows = []
    for B in args.batches:
        try:
            lm_gen = LMGen(lm, use_sampling=True, temp=0.8, temp_text=0.7)
            lats = []
            # streaming(B) context manager enters/exits cleanly per batch size
            with mimi.streaming(B), lm_gen.streaming(B):
                for s in range(args.steps + 6):
                    audio = (torch.randn(B, 1, frame, device="cuda") * 0.05)
                    torch.cuda.synchronize(); t0 = time.perf_counter()
                    with torch.no_grad():
                        codes = mimi.encode(audio)        # [B, K, 1]
                        _ = lm_gen.step(codes)            # [B, ...] one token/stream
                    torch.cuda.synchronize()
                    if s >= 6:
                        lats.append((time.perf_counter() - t0) * 1000.0)
            p50 = float(np.percentile(lats, 50)); p99 = float(np.percentile(lats, 99))
            ok = p99 <= budget_ms
            rows.append(dict(B=B, step_p50_ms=round(p50, 2), step_p99_ms=round(p99, 2),
                             meets_budget=ok))
            print(f"  B={B:4d}: frame p50={p50:6.1f}ms p99={p99:6.1f}ms "
                  f"{'<=' if ok else '>'} {budget_ms:.0f}ms  ({'real-time' if ok else 'MISS'})",
                  flush=True)
            del lm_gen; torch.cuda.empty_cache()
        except Exception as e:
            print(f"  B={B}: ERR {type(e).__name__}: {str(e)[:90]}", flush=True)
            break
    cap = max([r["B"] for r in rows if r["meets_budget"]], default=0)
    os.makedirs("results/realtime_load", exist_ok=True)
    json.dump(dict(model="moshi", budget_ms=budget_ms, batched_fullduplex_capacity=cap, curve=rows),
              open("results/realtime_load/moshi_batched.json", "w"), indent=2)
    print(f"\n[moshi] batched full-duplex real-time capacity = {cap} concurrent streams "
          f"(per-frame budget {budget_ms:.0f}ms)", flush=True)


if __name__ == "__main__":
    main()
