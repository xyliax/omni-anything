"""Open-system ramp for online admission: sessions ARRIVE over time (rate R/s up to N_total), each
streams real audio continuously. With the gateway's online AIMD admission (--online-admit), the
controller should discover N* from per-frame latency, admit ~N* sessions that hold the deadline, and
cleanly reject arrivals beyond it. Reports admitted-vs-rejected and admitted latency over time.

Without admission (baseline), every arrival is admitted -> all degrade past the cliff.
"""
import argparse, asyncio, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from bench.realtime_client import RealtimeClient, pcm16_b64
from experiments.realtime_load import load_audio_pool


async def session(uri, seed, pool, duration, chunk_ms, out, t0_global):
    try:
        arr, sr = pool[seed % len(pool)]
        arr = np.asarray(arr, dtype=np.float32)
        n = max(1, sr * chunk_ms // 1000)
        try:
            cli = await RealtimeClient.connect(uri)
            await cli.configure(modalities=["text"], input_sample_rate=16000,
                                turn_detection="full_duplex")
        except Exception:
            out["rejected"] += 1
            return
        admitted = [False]
        t_start = time.time(); stop = [False]

        async def sender():
            i, nxt, t_end = 0, time.time(), time.time() + duration
            while time.time() < t_end:
                await cli._send("input_audio_buffer.append", audio=pcm16_b64(arr[i:i + n]))
                i = (i + n) % max(1, len(arr) - n)
                nxt += chunk_ms / 1000.0
                await asyncio.sleep(max(0.0, nxt - time.time()))
            stop[0] = True

        async def receiver():
            while not stop[0]:
                try:
                    ev = json.loads(await asyncio.wait_for(cli.ws.recv(), timeout=3.0))
                except Exception:
                    if stop[0]:
                        break
                    continue
                ty = ev.get("type")
                if ty == "error":
                    out["rejected"] += 1; stop[0] = True; break
                if ty == "metronome.tick":
                    admitted[0] = True
                    out["ev"].append((time.time() - t0_global, float(ev.get("latency_ms", 0.0))))
        await asyncio.gather(sender(), receiver())
        if admitted[0]:
            out["admitted"] += 1
        await cli.close()
    except Exception:
        out["err"] += 1


async def main_async(a):
    pool = load_audio_pool(64)
    out = dict(ev=[], admitted=0, rejected=0, err=0)
    t0 = time.time()
    tasks = []
    for i in range(a.n_total):
        tasks.append(asyncio.create_task(session(a.uri, i, pool, a.duration, a.chunk_ms, out, t0)))
        await asyncio.sleep(1.0 / a.rate)   # ramp: arrive at `rate` sessions/sec
    await asyncio.gather(*tasks)
    # report
    budget = a.budget_ms
    lat = [l for (_, l) in out["ev"]]
    p50 = float(np.percentile(lat, 50)) if lat else 0.0
    p99 = float(np.percentile(lat, 99)) if lat else 0.0
    # admitted latency in the steady second half
    half = [l for (el, l) in out["ev"] if el >= a.duration * 0.5]
    p99b = float(np.percentile(half, 99)) if half else 0.0
    print(f"=== RAMP: offered N={a.n_total} @ {a.rate}/s, {a.duration:.0f}s, budget {budget:.0f}ms ===")
    print(f"  ADMITTED={out['admitted']}  REJECTED={out['rejected']}  err={out['err']}")
    print(f"  admitted latency: p50={p50:.0f}ms p99={p99:.0f}ms  steady-half p99={p99b:.0f}ms")
    print(f"  => online N* (admitted holding deadline) ~ {out['admitted']}")
    os.makedirs("results/sustained_fd", exist_ok=True)
    json.dump(dict(offered=a.n_total, rate=a.rate, admitted=out["admitted"],
                   rejected=out["rejected"], err=out["err"], p50=p50, p99=p99, p99_steady=p99b),
              open(f"results/sustained_fd/{a.tag}.json", "w"), indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uri", default="ws://127.0.0.1:8904")
    ap.add_argument("--n-total", type=int, default=200)
    ap.add_argument("--rate", type=float, default=4.0)      # arrivals/sec
    ap.add_argument("--duration", type=float, default=60.0)
    ap.add_argument("--chunk-ms", type=int, default=20)
    ap.add_argument("--budget-ms", type=float, default=2000.0)
    ap.add_argument("--tag", default="ramp")
    main_async_args = ap.parse_args()
    asyncio.run(main_async(main_async_args))


if __name__ == "__main__":
    main()
