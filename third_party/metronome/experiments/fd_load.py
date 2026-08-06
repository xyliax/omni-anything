"""Continuous full-duplex load: N sessions each STREAM real audio continuously (no turns) into
the Realtime API and receive output continuously; we measure per-frame deadline adherence and
TTFA from the metronome.tick events. Sharded across processes so the client is never the limit.
This is the true end-to-end continuous full-duplex test (client -> Go gateway -> gRPC -> vLLM).
"""
import argparse, asyncio, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from bench.realtime_client import RealtimeClient, pcm16_b64
from experiments.realtime_load import load_audio_pool


async def fd_session(uri, seed, audio_pool, duration, chunk_ms, out):
    try:
        cli = await RealtimeClient.connect(uri)
        await cli.configure(modalities=["text"], input_sample_rate=16000,
                            turn_detection="full_duplex")
        arr, sr = audio_pool[seed % len(audio_pool)]
        arr = np.asarray(arr, dtype=np.float32)
        n = max(1, sr * chunk_ms // 1000)
        stop = [False]

        async def sender():
            i, nxt, t_end = 0, time.time(), time.time() + duration
            while time.time() < t_end:
                chunk = arr[i:i + n]
                i = (i + n) % max(1, len(arr) - n)
                await cli._send("input_audio_buffer.append", audio=pcm16_b64(chunk))
                nxt += chunk_ms / 1000.0
                await asyncio.sleep(max(0.0, nxt - time.time()))
            stop[0] = True

        async def receiver():
            while not stop[0]:
                try:
                    ev = json.loads(await asyncio.wait_for(cli.ws.recv(), timeout=2.0))
                except Exception:
                    if stop[0]:
                        break
                    continue
                if ev.get("type") == "metronome.tick":
                    out["lat"].append(float(ev.get("latency_ms", 0.0)))
                    if not ev.get("deadline_met", True):
                        out["miss"] += 1
                    out["ticks"] += 1
                    st = float(ev.get("server_ttfa_ms", 0.0))
                    if st > 0 and out["ttfa"] == 0:
                        out["ttfa"] = st
        await asyncio.gather(sender(), receiver())
        await cli.close()
    except Exception as e:
        out["err"] += 1


async def shard_main(uri, m, duration, chunk_ms, seed0, out_path):
    pool = load_audio_pool(64)
    outs = [dict(lat=[], miss=0, ticks=0, ttfa=0.0, err=0) for _ in range(m)]
    await asyncio.gather(*[fd_session(uri, seed0 + i, pool, duration, chunk_ms, outs[i])
                           for i in range(m)])
    agg = dict(lat=[x for o in outs for x in o["lat"]],
               miss=sum(o["miss"] for o in outs), ticks=sum(o["ticks"] for o in outs),
               ttfa=[o["ttfa"] for o in outs if o["ttfa"] > 0], err=sum(o["err"] for o in outs))
    json.dump(agg, open(out_path, "w"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uri", default="ws://127.0.0.1:8904")
    ap.add_argument("--shard-index", type=int, default=-1)
    ap.add_argument("--m", type=int, default=16)
    ap.add_argument("--shards", type=int, default=4)
    ap.add_argument("--duration", type=float, default=20.0)
    ap.add_argument("--chunk-ms", type=int, default=200)
    ap.add_argument("--budget-ms", type=float, default=1000.0)
    args = ap.parse_args()
    if args.shard_index >= 0:
        asyncio.run(shard_main(args.uri, args.m, args.duration, args.chunk_ms,
                               args.shard_index * 100000, f"/tmp/fdshard_{args.shard_index}.json"))
        return
    import subprocess
    total = args.shards * args.m
    procs = [subprocess.Popen([sys.executable, "-u", __file__, "--uri", args.uri,
             "--shard-index", str(k), "--m", str(args.m), "--duration", str(args.duration),
             "--chunk-ms", str(args.chunk_ms)]) for k in range(args.shards)]
    for p in procs:
        p.wait()
    lat, miss, ticks, ttfa, err = [], 0, 0, [], 0
    for k in range(args.shards):
        try:
            a = json.load(open(f"/tmp/fdshard_{k}.json"))
            lat += a["lat"]; miss += a["miss"]; ticks += a["ticks"]; ttfa += a["ttfa"]; err += a["err"]
        except Exception:
            pass
    lat = np.array(lat or [0.0]); ttfa = np.array(ttfa or [0.0])
    print(f"=== CONTINUOUS full-duplex end-to-end: {total} streams ({args.shards}x{args.m}) ===")
    print(f"  frame p50={np.percentile(lat,50):.0f}ms p99={np.percentile(lat,99):.0f}ms "
          f"budget {args.budget_ms:.0f}ms | miss={miss/max(1,ticks):.2%} ({ticks} ticks) | "
          f"TTFA p50={np.percentile(ttfa,50):.0f}ms | err={err}", flush=True)


if __name__ == "__main__":
    main()
