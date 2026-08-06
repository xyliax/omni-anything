"""Sharded load driver: drive `total` concurrent sessions split across `shards` SEPARATE OS
processes (each its own asyncio event loop), so no single client loop is the bottleneck. If the
single-process ~96 knee was client-limited, sharding lifts it. Each shard connects M=total/shards
sessions to the SAME server, runs one synchronized turn, and writes its TTFAs; we aggregate.
"""
import argparse, asyncio, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from bench.realtime_client import RealtimeClient
from experiments.realtime_load import load_audio_pool


async def one_session(uri, seed, audio_pool, out):
    try:
        cli = await RealtimeClient.connect(uri)
        await cli.configure(modalities=["text"], input_sample_rate=16000, turn_detection="none")
        arr, sr = audio_pool[seed % len(audio_pool)]
        await cli.append_audio(arr, sr, chunk_ms=200)
        await cli._send("input_audio_buffer.commit")
        r = await cli.respond(modalities=["text"], timeout_s=120.0)
        out.append((r["ttfa_s"] * 1000.0, r.get("server_ttfa_ms", 0.0)))
        await cli.close()
    except Exception as e:
        out.append((float("nan"), float("nan")))


async def shard_main(uri, m, seed0, out_path):
    audio_pool = load_audio_pool(128)
    out = []
    # warmup (discarded) to capture graphs
    await asyncio.gather(*[one_session(uri, seed0 + i, audio_pool, []) for i in range(min(8, m))])
    await asyncio.gather(*[one_session(uri, seed0 + 1000 + i, audio_pool, out) for i in range(m)])
    json.dump(out, open(out_path, "w"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uri", default="ws://127.0.0.1:8765")
    ap.add_argument("--shard-index", type=int, default=-1)   # -1 = orchestrator
    ap.add_argument("--m", type=int, default=64)             # sessions per shard
    ap.add_argument("--shards", type=int, default=4)
    ap.add_argument("--out", default="/tmp/shard.json")
    args = ap.parse_args()
    if args.shard_index >= 0:
        asyncio.run(shard_main(args.uri, args.m, args.shard_index * 100000, args.out))
        return
    # orchestrator: launch `shards` child processes, each m sessions, ~simultaneously
    import subprocess
    procs, outs = [], []
    for k in range(args.shards):
        op = f"/tmp/shard_{k}.json"; outs.append(op)
        procs.append(subprocess.Popen(
            [sys.executable, "-u", __file__, "--uri", args.uri, "--shard-index", str(k),
             "--m", str(args.m), "--out", op]))
    for p in procs:
        p.wait()
    pairs = []
    for op in outs:
        try:
            pairs += json.load(open(op))
        except Exception:
            pass
    cl = np.array([p[0] for p in pairs if p[0] == p[0]])     # client TTFA (ms)
    sv = np.array([p[1] for p in pairs if p[1] == p[1] and p[1] > 0])  # server TTFA
    total = args.shards * args.m
    print(f"=== SHARDED: {args.shards} procs x {args.m} = {total} concurrent sessions ===")
    print(f"  client TTFA p50={np.percentile(cl,50):.0f}ms p99={np.percentile(cl,99):.0f}ms (n={len(cl)})")
    if len(sv):
        print(f"  SERVER TTFA p50={np.percentile(sv,50):.0f}ms p99={np.percentile(sv,99):.0f}ms (n={len(sv)})")


if __name__ == "__main__":
    main()
