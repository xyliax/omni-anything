"""WebRTC-style continuous fine-paced load: N full-duplex sessions each stream a small audio
packet every `chunk_ms` (20/40/200 ms), like Opus framing. This stresses the SERVER event loop's
per-packet I/O (ws.recv + json + base64 + buffer), at ~ (1000/chunk_ms) * N packets/s. We watch
the server's frame_loop `gap` (RT_DEBUG2): when the event loop saturates, the gap slips past the
period. The generator is sharded across processes so the CLIENT is never the bottleneck.
"""
import argparse, asyncio, json, os, sys, time, base64
import numpy as np


async def session(uri, seed, chunk_ms, duration, sr=16000):
    import websockets
    n = max(1, int(sr * chunk_ms / 1000))
    pkt = base64.b64encode((np.zeros(n, dtype="<i2")).tobytes()).decode()
    sent = 0
    try:
        ws = await websockets.connect(uri, max_size=2**20, open_timeout=30)
        # drain session.created
        await ws.recv()
        await ws.send(json.dumps({"type": "session.update", "session": {
            "modalities": ["text"], "input_sample_rate": sr,
            "turn_detection": {"type": "full_duplex"}}}))
        t_end = time.time() + duration
        period = chunk_ms / 1000.0
        nxt = time.time()
        while time.time() < t_end:
            await ws.send(json.dumps({"type": "input_audio_buffer.append", "audio": pkt}))
            sent += 1
            nxt += period
            dl = nxt - time.time()
            if dl > 0:
                await asyncio.sleep(dl)
        await ws.close()
    except Exception:
        pass
    return sent


async def shard_main(uri, m, chunk_ms, duration, seed0):
    res = await asyncio.gather(*[session(uri, seed0 + i, chunk_ms, duration) for i in range(m)])
    print(f"shard sent {sum(res)} packets over {m} sessions", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uri", default="ws://127.0.0.1:8765")
    ap.add_argument("--shard-index", type=int, default=-1)
    ap.add_argument("--m", type=int, default=64)
    ap.add_argument("--shards", type=int, default=4)
    ap.add_argument("--chunk-ms", type=int, default=20)
    ap.add_argument("--duration", type=float, default=20.0)
    args = ap.parse_args()
    if args.shard_index >= 0:
        asyncio.run(shard_main(args.uri, args.m, args.chunk_ms, args.duration,
                               args.shard_index * 100000))
        return
    import subprocess
    total = args.shards * args.m
    rate = int(1000 / args.chunk_ms) * total
    print(f"=== packet load: {args.shards}x{args.m}={total} sessions @ {args.chunk_ms}ms "
          f"=> ~{rate} packets/s to the server ===", flush=True)
    procs = [subprocess.Popen([sys.executable, "-u", __file__, "--uri", args.uri,
             "--shard-index", str(k), "--m", str(args.m), "--chunk-ms", str(args.chunk_ms),
             "--duration", str(args.duration)]) for k in range(args.shards)]
    for p in procs:
        p.wait()
    print("=== packet load done ===", flush=True)


if __name__ == "__main__":
    main()
