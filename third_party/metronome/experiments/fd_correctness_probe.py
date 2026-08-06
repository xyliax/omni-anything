"""Correctness probe for the CONTINUOUS full-duplex path used by the capacity sweep.

Answers two direct questions:
  (1) Is the GPU returning *correct* responses, or real-but-meaningless forced tokens?
  (2) Does correctness HOLD under high concurrency, sustained >=60 s — i.e. at N sessions is each
      session still answering ITS audio correctly, or does the audio pipeline starve so latency
      looks fine while responses degrade?

N sessions each stream one of a few KNOWN spoken questions continuously (the exact sustained_fd
shape: 20 ms chunks, looped) for `duration` s. We capture each session's decoded text and score it
against the expected answer keyword. We report per-bucket correctness over time and final latency.
"""
import argparse, asyncio, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from bench.realtime_client import RealtimeClient, pcm16_b64

# KNOWN clips (loaded from llama-questions by question text) -> expected answer keyword.
KNOWN = [
    ("What is the capital of France?", "Paris"),
    ("Which river is the longest in South America?", "Amazon"),
    ("What is the highest mountain peak in North America?", "Denali"),
]


async def fd_session(uri, clip, expect, duration, chunk_ms, out):
    try:
        arr, sr = clip
        arr = np.asarray(arr, dtype=np.float32)
        n = max(1, sr * chunk_ms // 1000)
        cli = await RealtimeClient.connect(uri)
        await cli.configure(modalities=["text", "audio"], input_sample_rate=16000,
                            turn_detection="full_duplex")
        t_start = time.time(); stop = [False]

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
                    ev = json.loads(await asyncio.wait_for(cli.ws.recv(), timeout=3.0))
                except Exception:
                    if stop[0]:
                        break
                    continue
                ty = ev.get("type")
                if ty == "response.text.delta":
                    txt = ev.get("delta", "")
                    el = time.time() - t_start
                    out["ticks"].append((el, txt, 1 if expect.lower() in txt.lower() else 0))
                elif ty == "metronome.tick":
                    el = time.time() - t_start
                    out["lat"].append((el, float(ev.get("latency_ms", 0.0)),
                                       0 if ev.get("deadline_met", True) else 1))
        await asyncio.gather(sender(), receiver())
        await cli.close()
    except Exception as e:
        out["err"] = str(e)


async def run(uri, clips, duration, chunk_ms, n_sessions):
    outs = [dict(ticks=[], lat=[], err="", expect=KNOWN[i % len(clips)][1]) for i in range(n_sessions)]
    tasks = [fd_session(uri, clips[i % len(clips)], KNOWN[i % len(clips)][1],
                        duration, chunk_ms, outs[i]) for i in range(n_sessions)]
    await asyncio.gather(*tasks)
    return outs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uri", default="ws://127.0.0.1:8904")
    ap.add_argument("--duration", type=float, default=75.0)
    ap.add_argument("--chunk-ms", type=int, default=20)
    ap.add_argument("--n-sessions", type=int, default=1)
    ap.add_argument("--dataset", default="llama-questions")
    ap.add_argument("--bucket-s", type=float, default=15.0)
    ap.add_argument("--tag", default="fd_correctness")
    args = ap.parse_args()
    from experiments.bench_spoken_qa import load_samples
    samples = load_samples(args.dataset, 64)
    by_q = {s.get("question", s.get("text", "")): s for s in samples}
    clips = []
    for q, _ in KNOWN:
        s = by_q.get(q)
        if s is None:  # fall back to first samples if exact question text differs
            s = samples[len(clips)]
        clips.append((np.asarray(s["audio"][0], dtype=np.float32), int(s["audio"][1])))
    print(f"=== FD correctness under load: N={args.n_sessions} sessions, {args.duration:.0f}s, "
          f"{len(clips)} known questions cycled ===", flush=True)
    outs = asyncio.run(run(args.uri, clips, args.duration, args.chunk_ms, args.n_sessions))

    # per-session correctness. Two metrics:
    #   sess_correct  = >=80% of steady ticks contain the answer (strict, per-frame)
    #   sess_ever     = answer appears in the assembled steady text at least once (robust to
    #                   chain-of-thought verbosity / thinking-mode models that interleave reasoning)
    sess_correct = 0; sess_ever = 0; sess_with_ticks = 0
    for o in outs:
        steady = [c for (el, t, c) in o["ticks"] if el >= 4.0]
        if steady:
            sess_with_ticks += 1
            if sum(steady) / len(steady) >= 0.8:
                sess_correct += 1
            if sum(steady) >= 1:
                sess_ever += 1
    # correctness bucketed over time (across all sessions)
    all_ticks = [(el, c) for o in outs for (el, t, c) in o["ticks"]]
    all_lat = [(el, l, m) for o in outs for (el, l, m) in o["lat"]]
    nb = int(np.ceil(args.duration / args.bucket_s))
    print(f"  {'window':>12} {'txt-ticks':>10} {'correct%':>9} {'lat p99':>9} {'miss':>7}", flush=True)
    for b in range(nb):
        lo, hi = b * args.bucket_s, (b + 1) * args.bucket_s
        cs = [c for (el, c) in all_ticks if lo <= el < hi]
        ls = [l for (el, l, m) in all_lat if lo <= el < hi]
        ms = [m for (el, l, m) in all_lat if lo <= el < hi]
        if not cs and not ls:
            continue
        corr = (sum(cs) / len(cs)) if cs else float("nan")
        p99 = np.percentile(ls, 99) if ls else float("nan")
        miss = (sum(ms) / len(ms)) if ms else float("nan")
        print(f"  {f'{lo:.0f}-{hi:.0f}s':>12} {len(cs):>10} {corr:>8.1%} {p99:>8.0f}ms "
              f"{miss:>6.1%}", flush=True)
    errs = sum(1 for o in outs if o["err"])
    print(f"  SESSIONS: {sess_correct}/{sess_with_ticks} answered correctly in >=80% of steady ticks; "
          f"{sess_ever}/{sess_with_ticks} stated the answer at least once (assembled); "
          f"{errs} errored", flush=True)
    os.makedirs("results/sustained_fd", exist_ok=True)
    # assembled steady text per session (for coherence inspection — e.g. Moshi, a conversational
    # voice model where QA-keyword scoring doesn't apply; we check the output stays coherent at load)
    asm = [" ".join(t for (el, t, c) in o["ticks"] if el >= 4.0)[:400] for o in outs[:4]]
    json.dump(dict(n_sessions=args.n_sessions, duration=args.duration,
                   sess_correct=sess_correct, sess_ever=sess_ever,
                   sess_with_ticks=sess_with_ticks, errs=errs,
                   sample_texts=[o["ticks"][-1][1] if o["ticks"] else "" for o in outs[:8]],
                   sample_assembled=asm),
              open(f"results/sustained_fd/{args.tag}_n{args.n_sessions}.json", "w"), indent=1)


if __name__ == "__main__":
    main()
