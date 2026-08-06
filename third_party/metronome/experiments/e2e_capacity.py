"""End-to-end concurrency + TTFA sweep through the Go gateway, for AUDIO-ONLY vs AUDIO+VISION.

Turn-based real workload (the realistic VQA / spoken-QA serving mode): each session streams a
short audio question (and, in vision mode, attaches an image) then asks for a response; we measure
time-to-first-token (TTFA) and per-tick deadline adherence. We sweep concurrency N and report, per
N, TTFA p50/p99 and deadline-miss rate; the max concurrency is the largest N meeting the SLO.

Audio-only and audio+vision are measured separately ON PURPOSE: vision adds a large image-prefill
(hundreds of vision tokens) on top of the audio prefill, so the two pipelines have different
compute and different capacity. Path: client -> Go gateway (:8904) -> gRPC -> vLLM worker.
"""
import argparse, asyncio, base64, io, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from bench.realtime_client import RealtimeClient, pcm16_b64
from experiments.realtime_load import load_audio_pool


def make_image(px):
    """A deterministic RGB test image at a realistic resolution — prefill cost tracks pixel count,
    not content, so a structured gradient is a faithful load proxy for the vision pipeline."""
    from PIL import Image
    x = np.linspace(0, 255, px, dtype=np.uint8)
    g = np.stack([np.tile(x, (px, 1)), np.tile(x[:, None], (1, px)),
                  ((np.add.outer(x, x)) // 2).astype(np.uint8)], axis=-1)
    return Image.fromarray(g, "RGB")


def img_b64(pil, fmt="PNG"):
    buf = io.BytesIO(); pil.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode()


async def one_turn(uri, seed, pool, mode, img_b64s, q_audio_s, max_tokens, budget_ms, out,
                   start_delay=0.0):
    try:
        if start_delay > 0:
            await asyncio.sleep(start_delay)
        cli = await RealtimeClient.connect(uri)
        await cli.configure(modalities=["text"], input_sample_rate=16000, turn_detection="none")
        arr, sr = pool[seed % len(pool)]
        arr = np.asarray(arr, dtype=np.float32)[: int(q_audio_s * sr)]
        # stream the question audio
        await cli.append_audio(arr, sr, chunk_ms=200)
        if mode == "vision":
            await cli._send("input_image.append", image=img_b64s)
        # ask for the response and time it
        t0 = time.time()
        await cli._send("response.create",
                        response={"modalities": ["text"], "max_output_tokens": max_tokens})
        ttfa = None; ticks = 0; miss = 0; got = 0; text = ""
        while True:
            ev = json.loads(await asyncio.wait_for(cli.ws.recv(), timeout=180.0))
            ty = ev.get("type")
            if ty in ("response.text.delta", "response.audio.delta",
                      "response.audio_transcript.delta"):
                if ttfa is None:
                    ttfa = (time.time() - t0) * 1000.0
                got += 1
                if ty == "response.text.delta":
                    text += ev.get("delta", "")
            elif ty == "metronome.tick":
                ticks += 1
                out["batch"].append(int(ev.get("batch", 0)))   # true per-tick GPU batch
                out["gpu_ms"].append(float(ev.get("latency_ms", 0.0)))
                if not ev.get("deadline_met", True):
                    miss += 1
            elif ty == "response.done":
                break
            elif ty == "error":
                out["err"] += 1; break
        await cli.close()
        if ttfa is not None:
            out["ttfa"].append(ttfa)
        out["ticks"] += ticks; out["miss"] += miss
        if got == 0:
            out["empty"] += 1
        elif text:
            out["texts"].append(text.strip())
    except Exception:
        out["err"] += 1


async def run_n(uri, n, pool, mode, imgpx, q_audio_s, max_tokens, budget_ms, turns,
                arrival_window_s=0.0):
    img = img_b64(make_image(imgpx)) if mode == "vision" else ""
    out = dict(ttfa=[], ticks=0, miss=0, err=0, empty=0, batch=[], gpu_ms=[], texts=[])
    # Stagger session arrivals uniformly over arrival_window_s instead of a synchronized
    # thundering herd: a simultaneous burst of N prefills serialises into a few ticks and
    # produces an unstable p99 tail that reflects arrival alignment, not steady-state capacity.
    for _ in range(turns):
        await asyncio.gather(*[
            one_turn(uri, i, pool, mode, img, q_audio_s, max_tokens, budget_ms, out,
                     start_delay=(arrival_window_s * i / max(1, n)))
            for i in range(n)])
    t = np.array(out["ttfa"] or [float("nan")])
    b = np.array(out["batch"] or [0])
    g = np.array(out["gpu_ms"] or [0.0])
    return dict(N=n, mode=mode,
                ttfa_p50=float(np.nanpercentile(t, 50)), ttfa_p90=float(np.nanpercentile(t, 90)),
                ttfa_p99=float(np.nanpercentile(t, 99)),
                batch_p50=float(np.percentile(b, 50)), batch_max=int(b.max()),
                gpu_p50=float(np.percentile(g, 50)), gpu_p99=float(np.percentile(g, 99)),
                miss_rate=out["miss"] / max(1, out["ticks"]), ticks=out["ticks"],
                err=out["err"], empty=out["empty"], n_resp=len(out["ttfa"]),
                sample_texts=out["texts"][:5])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uri", default="ws://127.0.0.1:8904")
    ap.add_argument("--mode", choices=["audio", "vision"], default="audio")
    ap.add_argument("--grid", type=int, nargs="+", default=[1, 8, 32, 64, 96, 128])
    ap.add_argument("--img-px", type=int, default=448)        # realistic vision resolution
    ap.add_argument("--q-audio-s", type=float, default=3.0)   # question length (audio prefill)
    ap.add_argument("--max-tokens", type=int, default=48)
    ap.add_argument("--budget-ms", type=float, default=2000.0)
    ap.add_argument("--turns", type=int, default=2)
    ap.add_argument("--arrival-window-s", type=float, default=2.0)  # spread arrivals (anti-burst)
    ap.add_argument("--warmup", type=int, default=1)         # warm engine before measuring
    ap.add_argument("--warmup-n", type=int, default=64)      # representative large warmup batch
    ap.add_argument("--slo", type=float, default=0.05)        # max deadline-miss for "feasible"
    ap.add_argument("--ttfa-slo-ms", type=float, default=4000.0)
    ap.add_argument("--tag", default="e2e_cap")
    args = ap.parse_args()
    pool = load_audio_pool(64)
    print(f"=== E2E {args.mode.upper()} capacity sweep via {args.uri} "
          f"(img={args.img_px if args.mode=='vision' else '-'}px, q={args.q_audio_s}s, "
          f"budget={args.budget_ms:.0f}ms) ===", flush=True)
    # Warm the engine FIRST (flashinfer autotuning + CUDA-graph capture for these mm shapes
    # happen on the first real inferences; without this the early grid points eat that stall
    # and report a falsely low capacity). Results discarded.
    if args.warmup:
        # warm BOTH small and a representative large batch — the large-batch CUDA-graph /
        # flashinfer-autotune capture only fires at the first big batch, so an N=4-only warmup
        # leaves the first large grid point eating the stall (seen as a one-off 30s p99 tail).
        for wn in (4, args.warmup_n):
            w = asyncio.run(run_n(args.uri, wn, pool, args.mode, args.img_px, args.q_audio_s,
                                  args.max_tokens, args.budget_ms, 1, arrival_window_s=1.0))
            print(f"  [warmup {args.mode} N={wn}: TTFA p50={w['ttfa_p50']:.0f}ms "
                  f"resp={w['n_resp']}]", flush=True)
    rows = []
    for n in args.grid:
        r = asyncio.run(run_n(args.uri, n, pool, args.mode, args.img_px, args.q_audio_s,
                              args.max_tokens, args.budget_ms, args.turns,
                              arrival_window_s=args.arrival_window_s))
        feasible = (r["miss_rate"] <= args.slo and r["err"] == 0
                    and r["ttfa_p50"] <= args.ttfa_slo_ms)
        r["feasible"] = bool(feasible)
        rows.append(r)
        print(f"  N={n:4d} {args.mode:6s} TTFA p50={r['ttfa_p50']:7.0f} p99={r['ttfa_p99']:7.0f}ms "
              f"| BATCH p50={r['batch_p50']:.0f} max={r['batch_max']} gpu p50={r['gpu_p50']:.0f} "
              f"p99={r['gpu_p99']:.0f}ms | miss={r['miss_rate']:5.2%} resp={r['n_resp']:4d} "
              f"err={r['err']} {'OK' if feasible else 'FAIL'}", flush=True)
    feas = [r["N"] for r in rows if r["feasible"]]
    cap = max(feas) if feas else 0
    print(f"=== {args.mode.upper()} max concurrency @SLO(miss<={args.slo:.0%}, "
          f"TTFA<={args.ttfa_slo_ms:.0f}ms) = {cap} ===", flush=True)
    os.makedirs("results/e2e_capacity", exist_ok=True)
    path = f"results/e2e_capacity/{args.tag}_{args.mode}.json"
    json.dump(dict(uri=args.uri, mode=args.mode, budget_ms=args.budget_ms,
                   img_px=args.img_px, q_audio_s=args.q_audio_s, slo=args.slo,
                   ttfa_slo_ms=args.ttfa_slo_ms, max_concurrency=cap, rows=rows),
              open(path, "w"), indent=1)
    print(f"saved {path}", flush=True)


if __name__ == "__main__":
    main()
