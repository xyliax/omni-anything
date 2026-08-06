"""#2 Quality-under-load: do the model's ANSWERS stay correct when the server is batching many
concurrent sessions? We push the SAME real spoken-QA questions (audio) through the loaded
Realtime server at concurrency=1 (solo) vs concurrency=C (loaded), score inclusion-match
accuracy, and compare. If accuracy holds, capacity isn't hiding quality degradation (C2 parity).
"""
import argparse, asyncio, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from bench.realtime_client import RealtimeClient
from experiments.bench_spoken_qa import load_samples, correct


async def ask(uri, sample, sr, modalities):
    cli = await RealtimeClient.connect(uri)
    try:
        await cli.configure(modalities=modalities, input_sample_rate=sr, turn_detection="none",
                            instructions="Answer the spoken question in a few words.")
        arr, asr = sample["audio"]
        await cli.append_audio(np.asarray(arr, dtype=np.float32), asr, chunk_ms=200)
        await cli._send("input_audio_buffer.commit")
        r = await cli.respond(modalities=modalities, timeout_s=120.0)
        return dict(pred=r["text"], golds=sample["golds"], ok=correct(r["text"], sample["golds"]))
    finally:
        await cli.close()


async def run_at(uri, samples, conc, sr, modalities):
    """Run all samples through the server with at most `conc` concurrent in flight."""
    sem = asyncio.Semaphore(conc)
    results = []

    async def worker(s):
        async with sem:
            try:
                results.append(await ask(uri, s, sr, modalities))
            except Exception as e:
                results.append(dict(pred=f"[err {type(e).__name__}]", golds=s["golds"], ok=False))
    await asyncio.gather(*[worker(s) for s in samples])
    acc = sum(r["ok"] for r in results) / max(1, len(results))
    return acc, results


async def main_async(args):
    samples = load_samples("llama-questions", args.n)
    print(f"=== quality-under-load: {len(samples)} spoken-QA Qs, solo vs concurrency={args.conc} ===",
          flush=True)
    modalities = ("text",)
    acc_solo, res_solo = await run_at(args.uri, samples, 1, args.input_sr, modalities)
    print(f"  SOLO (conc=1):          accuracy = {acc_solo:.3f}", flush=True)
    acc_load, res_load = await run_at(args.uri, samples, args.conc, args.input_sr, modalities)
    print(f"  LOADED (conc={args.conc}): accuracy = {acc_load:.3f}", flush=True)
    # per-sample flip count (rigorous: aggregate equality can hide compensating flips)
    flips = sum(1 for a, b in zip(res_solo, res_load) if a["ok"] != b["ok"])
    print(f"  per-sample correctness flips solo<->loaded: {flips}/{len(samples)}", flush=True)
    print(f"  VERDICT: quality {'PRESERVED' if abs(acc_solo-acc_load) <= 0.03 else 'DEGRADED'} "
          f"under load (Δacc={acc_load-acc_solo:+.3f})", flush=True)
    os.makedirs("results/realtime_load", exist_ok=True)
    json.dump(dict(n=len(samples), conc=args.conc, acc_solo=round(acc_solo, 4),
                   acc_load=round(acc_load, 4), flips=flips,
                   examples=[dict(pred=r["pred"][:60], gold=r["golds"][:2], ok=r["ok"])
                             for r in res_load[:8]]),
              open("results/realtime_load/quality_under_load.json", "w"), indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uri", default="ws://127.0.0.1:8765")
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--conc", type=int, default=128)
    ap.add_argument("--input-sr", type=int, default=16000)
    args = ap.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
