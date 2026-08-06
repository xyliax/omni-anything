"""SUSTAINED continuous full-duplex load — the real full-duplex application shape.

N concurrent sessions each stream real audio in small (20-30 ms) chunks CONTINUOUSLY for a long
duration (60 s+), exactly like a WebRTC mic feed; the server processes every frame over a
minute-level resident audio context and streams output back. We bucket per-frame latency BY
ELAPSED TIME so we can see whether latency degrades as the context window grows to minute scale
(the thing that actually matters — sustained, not a 10 s burst).

Path: client -> Go gateway (full_duplex) -> gRPC -> worker -> output. Reports, per 10 s bucket:
frame latency p50/p99, deadline-miss, and whether voice-out (response.audio.delta) is present.
"""
import argparse, asyncio, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from bench.realtime_client import RealtimeClient, pcm16_b64
from experiments.realtime_load import load_audio_pool


async def fd_session(uri, seed, pool, duration, chunk_ms, out):
    try:
        cli = await RealtimeClient.connect(uri)
        await cli.configure(modalities=["text", "audio"], input_sample_rate=16000,
                            turn_detection="full_duplex")
        arr, sr = pool[seed % len(pool)]
        arr = np.asarray(arr, dtype=np.float32)
        n = max(1, sr * chunk_ms // 1000)
        t_start = time.time()
        stop = [False]
        # Per-session PHASE OFFSET: start each stream at a distinct point in the clip so no two
        # sessions ever present the same audio window. Without this, sessions sharing a clip (pool
        # is finite) stream in lockstep -> identical 8 s windows -> vLLM prefix-cache dedups the
        # audio encode+prefill, making capacity OPTIMISTIC. Real users are not phase-aligned.
        i0 = 0
        if os.environ.get("FD_PHASE_STAGGER", "1") == "1" and len(arr) > n:
            i0 = (seed * 7919) % max(1, len(arr) - n)

        async def sender():
            i, nxt, t_end = i0, time.time(), time.time() + duration
            while time.time() < t_end:
                chunk = arr[i:i + n]
                i = (i + n) % max(1, len(arr) - n)            # loop the clip -> minutes of audio
                await cli._send("input_audio_buffer.append", audio=pcm16_b64(chunk))
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
                if ty == "metronome.tick":
                    el = time.time() - t_start
                    out["ev"].append((el, float(ev.get("latency_ms", 0.0)),
                                      0 if ev.get("deadline_met", True) else 1))
                    st = float(ev.get("server_ttfa_ms", 0.0))
                    if st > 0 and out["ttfa"] == 0:
                        out["ttfa"] = st
                elif ty == "response.audio.delta":
                    out["audio_out"] += 1
        await asyncio.gather(sender(), receiver())
        await cli.close()
    except Exception:
        out["err"] += 1


async def shard_main(uri, m, duration, chunk_ms, seed0, out_path):
    pool = load_audio_pool(64)
    outs = [dict(ev=[], ttfa=0.0, err=0, audio_out=0) for _ in range(m)]
    await asyncio.gather(*[fd_session(uri, seed0 + i, pool, duration, chunk_ms, outs[i])
                           for i in range(m)])
    agg = dict(ev=[e for o in outs for e in o["ev"]],
               ttfa=[o["ttfa"] for o in outs if o["ttfa"] > 0],
               err=sum(o["err"] for o in outs),
               audio_out=sum(o["audio_out"] for o in outs))
    json.dump(agg, open(out_path, "w"))


def report(ev, ttfa, err, audio_out, total, budget_ms, duration, bucket_s, tag):
    print(f"=== SUSTAINED continuous full-duplex: {total} streams, {duration:.0f}s, "
          f"budget {budget_ms:.0f}ms ===", flush=True)
    ev = sorted(ev)
    if not ev:
        print("  NO TICKS RECEIVED — system starved at this concurrency (capacity exceeded)",
              flush=True)
        os.makedirs("results/sustained_fd", exist_ok=True)
        json.dump(dict(total=total, duration=duration, budget_ms=budget_ms, ev=[],
                       ttfa=[], err=err, audio_out=audio_out, starved=True),
                  open(f"results/sustained_fd/{tag}.json", "w"))
        return
    nb = int(np.ceil(duration / bucket_s))
    print(f"  {'window':>12} {'ticks':>7} {'lat p50':>9} {'lat p99':>9} {'miss':>7}", flush=True)
    deg = []
    for b in range(nb):
        lo, hi = b * bucket_s, (b + 1) * bucket_s
        lats = [l for (el, l, m) in ev if lo <= el < hi]
        miss = [m for (el, l, m) in ev if lo <= el < hi]
        if not lats:
            continue
        p50, p99 = np.percentile(lats, 50), np.percentile(lats, 99)
        mr = sum(miss) / max(1, len(miss))
        deg.append(p99)
        print(f"  {f'{lo:.0f}-{hi:.0f}s':>12} {len(lats):>7} {p50:>8.0f}ms {p99:>8.0f}ms "
              f"{mr:>6.1%}", flush=True)
    alll = [l for (_, l, _) in ev]
    allm = [m for (_, _, m) in ev]
    ttfa = np.array(ttfa or [0.0])
    drift = (deg[-1] - deg[0]) if len(deg) >= 2 else 0.0
    p50 = float(np.percentile(alll, 50)); p90 = float(np.percentile(alll, 90))
    p99 = float(np.percentile(alll, 99))
    miss = sum(allm) / max(1, len(allm))
    # FRAME-DELIVERY COMPLETENESS — the reliable real-time check for tight-budget models.
    # `miss` above is computed against the worker's self-reported gpu_ms, which can under-report
    # (e.g. an unsynchronized CUDA timer) and hides cadence slip. Each session should receive
    # duration/period frames; if it gets fewer, the gateway tick loop ran SLOWER than the budget
    # (the worker couldn't keep the frame cadence) -> not real-time, even at "0% miss".
    exp_frames = duration / (budget_ms / 1000.0)
    deliv_per_sess = len(alll) / max(1, total)
    deliv_pct = deliv_per_sess / max(1e-9, exp_frames)
    real_cadence_ms = (duration * 1000.0) / max(1e-9, deliv_per_sess)
    realtime = deliv_pct >= 0.9 and miss < 0.02
    print(f"  OVERALL: ticks={len(alll)} lat p50={p50:.0f} p90={p90:.0f} p99={p99:.0f}ms "
          f"miss={miss:.2%} TTFA p50={np.percentile(ttfa,50):.0f}ms "
          f"voice_out_frames={audio_out} err={err}", flush=True)
    print(f"  CADENCE: delivered {deliv_pct:.0%} of frames ({deliv_per_sess:.0f}/{exp_frames:.0f} "
          f"per session) -> real frame period {real_cadence_ms:.0f}ms vs budget {budget_ms:.0f}ms "
          f"=> {'REAL-TIME' if realtime else 'CADENCE SLIP (over capacity)'}", flush=True)
    print(f"  DEGRADATION: first-bucket p99 {deg[0]:.0f}ms -> last-bucket p99 {deg[-1]:.0f}ms "
          f"(drift {drift:+.0f}ms) {'STABLE' if drift < 0.3*budget_ms else 'DEGRADING'}"
          if len(deg) >= 2 else "", flush=True)
    os.makedirs("results/sustained_fd", exist_ok=True)
    json.dump(dict(total=total, duration=duration, budget_ms=budget_ms, ev=ev,
                   ttfa=list(ttfa), err=err, audio_out=audio_out,
                   p50=p50, p90=p90, p99=p99, miss=miss,
                   deliv_pct=deliv_pct, real_cadence_ms=real_cadence_ms, realtime=realtime),
              open(f"results/sustained_fd/{tag}.json", "w"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uri", default="ws://127.0.0.1:8904")
    ap.add_argument("--shard-index", type=int, default=-1)
    ap.add_argument("--m", type=int, default=16)
    ap.add_argument("--shards", type=int, default=1)
    ap.add_argument("--duration", type=float, default=60.0)
    ap.add_argument("--chunk-ms", type=int, default=20)
    ap.add_argument("--budget-ms", type=float, default=2000.0)
    ap.add_argument("--bucket-s", type=float, default=10.0)
    ap.add_argument("--tag", default="sustained")
    args = ap.parse_args()
    if args.shard_index >= 0:
        asyncio.run(shard_main(args.uri, args.m, args.duration, args.chunk_ms,
                               args.shard_index * 100000, f"/tmp/sfd_{args.shard_index}.json"))
        return
    import subprocess
    total = args.shards * args.m
    procs = [subprocess.Popen([sys.executable, "-u", __file__, "--uri", args.uri,
             "--shard-index", str(k), "--m", str(args.m), "--duration", str(args.duration),
             "--chunk-ms", str(args.chunk_ms)]) for k in range(args.shards)]
    for p in procs:
        p.wait()
    ev, ttfa, err, audio_out = [], [], 0, 0
    for k in range(args.shards):
        try:
            a = json.load(open(f"/tmp/sfd_{k}.json"))
            ev += [tuple(e) for e in a["ev"]]; ttfa += a["ttfa"]; err += a["err"]
            audio_out += a["audio_out"]
        except Exception:
            pass
    report(ev, ttfa, err, audio_out, total, args.budget_ms, args.duration, args.bucket_s, args.tag)


if __name__ == "__main__":
    main()
