"""Long-horizon quality probe for the CONTINUOUS resident-KV path (review follow-up #1).

Question: does imposing a sliding window post hoc (in-engine SWA) on a full-attention backbone
degrade generation quality once the window has slid far past the session start (the StreamingLLM
attention-sink risk)? And what does the window give up on recall beyond the horizon?

Design (per 300 s session, 30 s segments):
  seg 0..7   (0-240 s): a per-session random permutation of 8 DISTINCT known spoken questions
             (llama-questions), each looped for its 30 s segment. Scoring each segment against
             its own question's gold answer gives a *correctness-vs-session-age* curve. If
             post-hoc windowing collapses generation after the window slides (W=512 tok ~ 20 s,
             1024 ~ 40 s, 2048 ~ 80 s of context), late segments drop vs vanilla.
  seg 8      (240-270 s): an espeak-SYNTHESIZED known question ("What is the capital of France?").
             Scored vs "Paris": validates in-run that the model understands the synthetic voice,
             making seg 9 interpretable.
  seg 9      (270-300 s): espeak "What was the first question I asked you at the start of this
             conversation?" Scored vs seg-0's golds + question content words: a recall probe
             BEYOND the window horizon (expected to fail under a slid window -- quantifies the
             inherent tradeoff; vanilla is the control).

Per-session permutations avoid identical audio histories across sessions (prefix-cache dedup).
"""
import argparse, asyncio, io, json, os, random, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from bench.realtime_client import RealtimeClient, pcm16_b64
from experiments.bench_spoken_qa import load_samples, normalize

SEG_S = 30.0
N_ROT = 8            # rotation questions (segments 0..7)
LAG_S = 6.0          # answers lag the audio; score seg k over [start+LAG, end+LAG)
FRANCE_Q = "What is the capital of France?"


def espeak_16k(text):
    """Synthesize text with espeak -> float32 mono 16 kHz."""
    import soundfile as sf
    wav = subprocess.run(["espeak", "--stdout", "-v", "en-us", "-s", "140", text],
                         capture_output=True, check=True).stdout
    arr, sr = sf.read(io.BytesIO(wav))
    if getattr(arr, "ndim", 1) > 1:
        arr = arr.mean(axis=1)
    arr = arr.astype(np.float32)
    if sr != 16000:
        t_src = np.arange(len(arr)) / sr
        t_dst = np.arange(int(len(arr) * 16000 / sr)) / 16000.0
        arr = np.interp(t_dst, t_src, arr).astype(np.float32)
    return arr, 16000


def content_words(q):
    stop = {"what", "which", "where", "when", "who", "how", "why", "the", "a", "an", "is",
            "are", "was", "were", "in", "of", "on", "for", "to", "does", "did", "you", "i",
            "your", "my", "me", "at", "start", "this", "conversation", "first", "question",
            "asked", "about", "many", "much", "name", "do", "it", "that", "and", "or"}
    return [w for w in normalize(q).split() if len(w) > 3 and w not in stop]


def hit(text_norm, golds):
    return any(normalize(str(g)) in text_norm for g in golds if str(g).strip())


async def fd_session(uri, segments, duration, chunk_ms, out):
    """segments: list of (arr, sr) to loop, one per SEG_S window."""
    try:
        cli = await RealtimeClient.connect(uri)
        await cli.configure(modalities=["text", "audio"], input_sample_rate=16000,
                            turn_detection="full_duplex")
        t0 = time.time(); stop = [False]

        async def sender():
            nxt = time.time(); i = 0; cur = -1; arr = None; n = 1
            while time.time() - t0 < duration:
                seg = min(int((time.time() - t0) / SEG_S), len(segments) - 1)
                if seg != cur:
                    cur = seg; arr, sr = segments[seg]
                    n = max(1, sr * chunk_ms // 1000); i = 0
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
                    out["deltas"].append((time.time() - t0, ev.get("delta", "")))
                elif ty == "metronome.tick":
                    out["lat"].append((time.time() - t0, float(ev.get("latency_ms", 0.0))))
        await asyncio.gather(sender(), receiver())
        await cli.close()
    except Exception as e:
        out["err"] = str(e)


def rep3(text):
    """Degeneracy check: max relative frequency of any word trigram (1.0 = pure loop)."""
    w = normalize(text).split()
    tg = [" ".join(w[i:i + 3]) for i in range(len(w) - 2)]
    if len(tg) < 8:
        return 0.0
    from collections import Counter
    return Counter(tg).most_common(1)[0][1] / len(tg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uri", default="ws://127.0.0.1:8904")
    ap.add_argument("--n-sessions", type=int, default=32)
    ap.add_argument("--chunk-ms", type=int, default=20)
    ap.add_argument("--tag", default="longhz")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    samples = load_samples("llama-questions", 64)
    # rotation pool: short clips, short unambiguous golds; exclude the France question (espeak probe)
    pool = [s for s in samples
            if s["dur"] <= 8.0 and s["question"] != FRANCE_Q
            and s["golds"] and all(len(normalize(str(g)).split()) <= 3 for g in s["golds"])]
    rot = pool[:N_ROT]
    assert len(rot) == N_ROT, f"only {len(rot)} usable rotation clips"
    print("[rotation] " + " | ".join(s["question"][:48] for s in rot), flush=True)

    esp_known = espeak_16k(FRANCE_Q)
    esp_recall = espeak_16k("What was the first question I asked you at the start of this conversation?")

    rng = random.Random(args.seed)
    perms = [rng.sample(range(N_ROT), N_ROT) for _ in range(args.n_sessions)]
    duration = (N_ROT + 2) * SEG_S

    async def run_all():
        outs = [dict(deltas=[], lat=[], err="") for _ in range(args.n_sessions)]
        tasks = []
        for i in range(args.n_sessions):
            segs = [(np.asarray(rot[j]["audio"][0], dtype=np.float32), int(rot[j]["audio"][1]))
                    for j in perms[i]] + [esp_known, esp_recall]
            tasks.append(fd_session(args.uri, segs, duration, args.chunk_ms, outs[i]))
        await asyncio.gather(*tasks)
        return outs

    print(f"=== LONG-HORIZON probe: N={args.n_sessions}, {duration:.0f}s "
          f"({N_ROT}x{SEG_S:.0f}s rotation + espeak-known + espeak-recall) ===", flush=True)
    outs = asyncio.run(run_all())

    # score: segment k of session i over [k*SEG+LAG, (k+1)*SEG+LAG)
    nseg = N_ROT + 2
    seg_hits = [[0, 0] for _ in range(nseg)]   # [hit, total]
    recall_hits = [0, 0]
    rep_late = []
    for i, o in enumerate(outs):
        if o["err"] or not o["deltas"]:
            continue
        for k in range(nseg):
            lo, hi = k * SEG_S + LAG_S, (k + 1) * SEG_S + LAG_S
            txt = normalize(" ".join(d for (el, d) in o["deltas"] if lo <= el < hi))
            if not txt:
                continue
            if k < N_ROT:
                golds = rot[perms[i][k]]["golds"]
                seg_hits[k][1] += 1; seg_hits[k][0] += 1 if hit(txt, golds) else 0
            elif k == N_ROT:                       # espeak-known: gold Paris
                seg_hits[k][1] += 1; seg_hits[k][0] += 1 if "paris" in txt else 0
            else:                                  # espeak-recall vs seg-0 question
                first = rot[perms[i][0]]
                tgt = [str(g) for g in first["golds"]] + content_words(first["question"])
                seg_hits[k][1] += 1
                ok = 1 if hit(txt, tgt) else 0
                seg_hits[k][0] += ok; recall_hits[1] += 1; recall_hits[0] += ok
            if k >= N_ROT - 2:
                rep_late.append(rep3(" ".join(d for (el, d) in o["deltas"] if lo <= el < hi)))
    errs = sum(1 for o in outs if o["err"])

    names = [f"seg{k}({k*30}-{(k+1)*30}s)" for k in range(N_ROT)] + ["espeak-known(240-270s)",
             "espeak-RECALL(270-300s)"]
    print(f"  {'segment':>24} {'answered':>10} {'correct%':>9}", flush=True)
    for k in range(nseg):
        h, t = seg_hits[k]
        pct = f"{h/t:.0%}" if t else "n/a"
        print(f"  {names[k]:>24} {f'{h}/{t}':>10} {pct:>9}", flush=True)
    lat_all = [l for o in outs for (el, l) in o["lat"]]
    p50 = float(np.percentile(lat_all, 50)) if lat_all else float("nan")
    p99 = float(np.percentile(lat_all, 99)) if lat_all else float("nan")
    rep = float(np.mean(rep_late)) if rep_late else 0.0
    print(f"  late-segment trigram-repetition (degeneracy, 1.0=loop): {rep:.2f}", flush=True)
    print(f"  latency p50={p50:.0f}ms p99={p99:.0f}ms  errs={errs}", flush=True)

    os.makedirs("results/sustained_fd", exist_ok=True)
    sample_txt = {}
    for k in [0, N_ROT - 1, N_ROT, N_ROT + 1]:
        lo, hi = k * SEG_S + LAG_S, (k + 1) * SEG_S + LAG_S
        sample_txt[names[k]] = [" ".join(d for (el, d) in o["deltas"] if lo <= el < hi)[:300]
                                for o in outs[:3]]
    json.dump(dict(tag=args.tag, n=args.n_sessions, seg_hits=seg_hits, seg_names=names,
                   recall=recall_hits, rep_late=rep, lat_p50=p50, lat_p99=p99, errs=errs,
                   rotation=[s["question"] for s in rot],
                   golds=[[str(g) for g in s["golds"]] for s in rot],
                   samples=sample_txt),
              open(f"results/sustained_fd/{args.tag}.json", "w"), indent=1)
    print(f"  -> results/sustained_fd/{args.tag}.json", flush=True)


if __name__ == "__main__":
    main()
