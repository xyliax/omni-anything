"""Serve Moshi THROUGH the Metronome Realtime API (run with ~/moshi-venv/bin/python,
PYTHONPATH=repo). Stands up the OpenAI-Realtime server on a MoshiBackend and drives it as a
WebSocket client over spoken-QA — proving the Realtime API is the universal serving surface
across all three paper models (closes the C5 'Moshi bypasses the API' exception)."""
import asyncio
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")

_ART = {"a", "an", "the"}
def norm(s):
    s = re.sub(r"[^\w\s]", " ", (s or "").lower())
    return " ".join(t for t in s.split() if t not in _ART)
def correct(pred, golds):
    p = norm(pred)
    return bool(p) and any(norm(g) and norm(g) in p for g in golds)


async def main():
    import websockets
    from datasets import load_dataset, Audio
    import soundfile as sf
    from metronome.backends.moshi_backend import MoshiBackend
    from metronome.realtime import RealtimeServer
    from bench.realtime_client import RealtimeClient

    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    port = 8795
    print("[moshi-rt] loading MoshiBackend ...", flush=True)
    backend = MoshiBackend()
    # small frame budget so the demo runs faster than real-time; correctness is the point
    srv = RealtimeServer(backend, frame_budget_s=0.02, kv_budget_tokens=512,
                         tokens_per_tick=4, port=port, capacity=4, response_max_tokens=200)
    ds = load_dataset("fixie-ai/llama-questions", split="test", streaming=True
                      ).cast_column("audio", Audio(decode=False))
    samples = []
    for r in ds:
        arr, sr = sf.read(io.BytesIO(r["audio"]["bytes"]))
        if getattr(arr, "ndim", 1) > 1:
            arr = arr.mean(axis=1)
        samples.append((arr.astype("float32"), int(sr), r["answer"]))
        if len(samples) >= n:
            break

    rows, n_ok = [], 0
    async with websockets.serve(srv.handle, "127.0.0.1", port, ping_interval=None,
                                max_size=64 * 2**20):
        floop = asyncio.create_task(srv.frame_loop())
        uri = f"ws://127.0.0.1:{port}"
        for arr, sr, gold in samples:
            cli = await RealtimeClient.connect(uri)
            await cli.configure(modalities=["text"], input_sample_rate=sr,
                                instructions="", turn_detection="none")
            await cli.append_audio(arr, sr)
            r = await cli.respond(modalities=["text"], timeout_s=120)
            await cli.close()
            ok = correct(r["text"], [gold]); n_ok += ok
            rows.append(dict(gold=gold, pred=r["text"][:120], ok=bool(ok)))
            print(f"  [{'OK' if ok else 'x'}] gold={gold!r} -> {r['text'][:70]!r}", flush=True)
        floop.cancel()
    backend.shutdown()
    acc = n_ok / max(1, len(rows))
    res = dict(model="moshi", served_via="metronome-realtime-api", task="spoken-qa",
               dataset="llama-questions", n=len(rows), accuracy=round(acc, 3), traces=rows)
    os.makedirs("results/realtime_bench", exist_ok=True)
    json.dump(res, open("results/realtime_bench/moshi__spoken-qa__via-realtime-api.json", "w"),
              indent=2)
    print(f"\n=== Moshi spoken-QA THROUGH the Realtime API: accuracy={acc:.3f} (n={len(rows)}) ===")


if __name__ == "__main__":
    asyncio.run(main())
