"""Phase 1 — REAL multi-concurrency load benchmark, EXTERNAL-client topology.

The RealtimeServer + vLLM backend run in a SEPARATE process (started by run_realtime_bench.sh);
this driver is pure async WebSocket clients. Separating client from server removes the
single-event-loop contention that previously starved the server's frame_loop (the multi-turn
"stall" / 8 ms empty ticks). Each session is a real multi-turn interaction: stream real audio
-> get a streamed response -> think -> repeat. We sweep connected concurrency N and report, per
N, with proper statistics (warmup turns discarded, many samples, bootstrap 95% CIs):
per-tick latency, deadline-miss rate, the REAL in-flight batch, TTFA, and goodput.
"""
import argparse
import asyncio
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from bench.realtime_client import RealtimeClient

FACTS = {"qwen-omni": "qwen3-omni", "minicpm-o": "minicpm-o", "moshi": "moshi"}


def load_audio_pool(n_clips):
    """Pool of DISTINCT real audio clips (LibriSpeech-style, via the spoken-QA loader)."""
    from experiments.bench_spoken_qa import load_samples
    for key in ("llama-questions", "spoken-web-questions"):
        try:
            samples = load_samples(key, n_clips)
            pool = [(np.asarray(s["audio"][0], dtype=np.float32), int(s["audio"][1]))
                    for s in samples]
            if pool:
                print(f"[audio] {len(pool)} REAL clips from {key}", flush=True)
                return pool
        except Exception as e:
            print(f"[warn] audio '{key}' failed: {e}", flush=True)
    rng = np.random.default_rng(0)
    return [(rng.standard_normal(16000 * 4).astype("float32") * 0.05, 16000) for _ in range(n_clips)]


def boot_ci(xs, q, reps=2000, seed=0):
    """Bootstrap 95% CI for percentile q of xs."""
    if len(xs) < 2:
        return (float(xs[0]) if xs else 0.0, float(xs[0]) if xs else 0.0)
    a = np.asarray(xs); rng = np.random.default_rng(seed)
    ps = [np.percentile(rng.choice(a, len(a), replace=True), q) for _ in range(reps)]
    return (round(float(np.percentile(ps, 2.5)), 1), round(float(np.percentile(ps, 97.5)), 1))


class Metrics:
    def __init__(self):
        self.tick_ms, self.ttfa_ms, self.batch, self.sttfa_ms = [], [], [], []
        self.turn_misses = self.turn_ticks = self.turns_ok = self.turns_done = self.errors = 0

    def add_turn(self, r, turn_idx, warmup_turns, trim_ticks=0):
        if turn_idx < warmup_turns:
            return
        # TTFA (first token, INCLUDES the prefill) is recorded separately; the per-tick latency
        # series has its first `trim_ticks` dropped (cold prefill tick + graph capture) so the
        # tick distribution is steady-state DECODE only -> clean, analytically-comparable.
        self.tick_ms.extend(r["tick_ms"][trim_ticks:]); self.ttfa_ms.append(r["ttfa_s"] * 1000.0)
        if r.get("server_ttfa_ms", 0.0) > 0:
            self.sttfa_ms.append(r["server_ttfa_ms"])
        self.batch.extend(r.get("batch", []))
        self.turn_misses += r["missed"]; self.turn_ticks += r["ticks"]; self.turns_done += 1
        if r["missed"] == 0 and r["ticks"] > 0:
            self.turns_ok += 1

    def summary(self, N, budget_ms):
        tk = self.tick_ms or [0.0]; tt = self.ttfa_ms or [0.0]; bt = self.batch or [0]
        return dict(
            N=N, turns_done=self.turns_done, errors=self.errors,
            n_ttfa=len(self.ttfa_ms), n_tick=len(self.tick_ms),
            tick_p50_ms=round(float(np.percentile(tk, 50)), 1),
            tick_p99_ms=round(float(np.percentile(tk, 99)), 1),
            frame_miss_rate=round(self.turn_misses / max(1, self.turn_ticks), 4),
            ttfa_p50_ms=round(float(np.percentile(tt, 50)), 1), ttfa_p50_ci=boot_ci(tt, 50),
            ttfa_p99_ms=round(float(np.percentile(tt, 99)), 1), ttfa_p99_ci=boot_ci(tt, 99),
            server_ttfa_p50_ms=round(float(np.percentile(self.sttfa_ms or [0], 50)), 1),
            server_ttfa_p99_ms=round(float(np.percentile(self.sttfa_ms or [0], 99)), 1),
            batch_p50=int(np.percentile(bt, 50)), batch_max=int(np.max(bt)),
            goodput_turns_ok=self.turns_ok, budget_ms=budget_ms)


async def client_session(uri, seed, audio_pool, image, modalities, turns, think_s,
                         input_sr, metrics, sem, warmup_turns, trim_ticks):
    async with sem:
        try:
            cli = await RealtimeClient.connect(uri)
            await cli.configure(modalities=modalities, input_sample_rate=input_sr,
                                turn_detection="none")
            rng = np.random.default_rng(seed)
            for t in range(turns):
                arr, sr = audio_pool[(seed * 7 + t) % len(audio_pool)]
                if image is not None:
                    await cli.attach_image(image, text="Describe what you hear and see.")
                await cli.append_audio(arr, sr, chunk_ms=200)
                await cli._send("input_audio_buffer.commit")
                r = await cli.respond(modalities=modalities, timeout_s=120.0)
                metrics.add_turn(r, t, warmup_turns, trim_ticks)
                if think_s > 0:
                    await asyncio.sleep(think_s * (0.5 + rng.random()))
            await cli.close()
        except Exception as e:
            metrics.errors += 1
            if metrics.errors <= 5:
                print(f"  [client err] {type(e).__name__}: {str(e)[:90]}", flush=True)


async def _round(uri, N, audio_pool, image, modalities, input_sr, arrival_rate, metrics,
                 seed0, trim_ticks):
    """One round: N fresh concurrent sessions, ONE turn each, into `metrics`."""
    sem = asyncio.Semaphore(N)
    tasks = []
    for i in range(N):
        tasks.append(asyncio.create_task(
            client_session(uri, seed0 + i, audio_pool, image, modalities, 1, 0.0,
                           input_sr, metrics, sem, 0, trim_ticks)))
        if arrival_rate > 0:
            await asyncio.sleep(1.0 / arrival_rate)
    await asyncio.gather(*tasks)


async def run_at_N(uri, N, audio_pool, image, modalities, turns, think_s, input_sr,
                   arrival_rate, budget_ms, warmup_turns, trim_ticks):
    """Measure concurrency N with PER-N WARMUP: `warm_rounds` discarded rounds (CUDA-graph
    capture + cache warmup at THIS batch size — fixes the non-monotonic cold-start artifact),
    then enough measured rounds to reach >=TARGET TTFA samples for solid bootstrap CIs."""
    TARGET = 64
    warm_rounds = 2
    meas_rounds = max(2, -(-TARGET // N))         # ceil(TARGET/N)
    warm = Metrics()
    for rnd in range(warm_rounds):
        await _round(uri, N, audio_pool, image, modalities, input_sr, arrival_rate, warm,
                     1 + rnd * N, trim_ticks)
    metrics = Metrics()
    for rnd in range(meas_rounds):
        await _round(uri, N, audio_pool, image, modalities, input_sr, arrival_rate, metrics,
                     100_000 + rnd * N, trim_ticks)
    return metrics.summary(N, budget_ms)


async def main_async(args):
    from metronome import models
    facts = models.get(FACTS[args.model])
    budget_ms = facts.period_s * 1000.0
    image = None
    if args.with_image:
        from PIL import Image
        image = Image.new("RGB", (448, 448), (128, 128, 128))
    audio_pool = load_audio_pool(args.audio_clips)
    modalities = tuple(args.modalities.split(","))
    print(f"=== load benchmark {args.model} -> {args.uri} | budget {budget_ms:.0f}ms | "
          f"turns={args.turns} warmup={args.warmup_turns} think={args.think_s}s ===", flush=True)
    # warmup the server at a mid batch (graph capture) - discarded
    await run_at_N(args.uri, 8, audio_pool, image, modalities, 2, 0.0, args.input_sr, 0,
                   budget_ms, 99, args.trim_ticks)
    rows = []
    for N in args.grid:
        r = await run_at_N(args.uri, N, audio_pool, image, modalities, args.turns, args.think_s,
                           args.input_sr, args.arrival_rate, budget_ms, args.warmup_turns, args.trim_ticks)
        rows.append(r)
        print(f"  N={N:4d}: miss={r['frame_miss_rate']:.2%} batch={r['batch_p50']}/{r['batch_max']} "
              f"CLIENT-TTFA p50={r['ttfa_p50_ms']:.0f}ci{r['ttfa_p50_ci']} "
              f"SERVER-TTFA p50={r['server_ttfa_p50_ms']:.0f} p99={r['server_ttfa_p99_ms']:.0f} "
              f"[{r['n_ttfa']}smp] good={r['goodput_turns_ok']}/{r['turns_done']} err={r['errors']}",
              flush=True)
        if r["errors"] > N // 2:
            print("  [stop] too many client errors", flush=True); break
    ttfa_budget_ms = max(2 * budget_ms, 1500.0)
    resp_cap = max([r["N"] for r in rows if r["ttfa_p50_ms"] <= ttfa_budget_ms
                    and r["frame_miss_rate"] <= args.slo], default=0)
    dec_cap = max([r["N"] for r in rows if r["frame_miss_rate"] <= args.slo], default=0)
    res = dict(model=args.model, budget_ms=budget_ms, tpt=args.tpt,
               think_s=args.think_s, turns=args.turns, warmup_turns=args.warmup_turns,
               slo=args.slo, ttfa_budget_ms=ttfa_budget_ms, tag=args.tag,
               decode_capacity=dec_cap, responsive_capacity=resp_cap, curve=rows)
    os.makedirs("results/realtime_load", exist_ok=True)
    out = f"results/realtime_load/{args.model}_{args.tag}.json"
    json.dump(res, open(out, "w"), indent=2)
    print(f"\n[{args.model}/{args.tag}] decode-cap={dec_cap}  RESPONSIVE-cap "
          f"(TTFA p50<{ttfa_budget_ms:.0f}ms)={resp_cap}\nsaved {out}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uri", default="ws://127.0.0.1:8765")
    ap.add_argument("--model", default="minicpm-o", choices=list(FACTS))
    ap.add_argument("--grid", nargs="*", type=int, default=[1, 2, 4, 8, 16, 32, 48, 64, 96, 128])
    ap.add_argument("--turns", type=int, default=12)
    ap.add_argument("--warmup-turns", type=int, default=3)
    ap.add_argument("--think-s", type=float, default=0.0)
    ap.add_argument("--arrival-rate", type=float, default=50.0)
    ap.add_argument("--audio-clips", type=int, default=128)
    ap.add_argument("--input-sr", type=int, default=16000)
    ap.add_argument("--modalities", default="text")
    ap.add_argument("--with-image", action="store_true")
    ap.add_argument("--slo", type=float, default=0.05)
    ap.add_argument("--tpt", type=int, default=0)        # informational (server owns the real tpt)
    ap.add_argument("--trim-ticks", type=int, default=5)
    ap.add_argument("--tag", default="bf16")
    args = ap.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
