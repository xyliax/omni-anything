"""Does the cost of waking a parked duplex session grow over the session?

Validation showed the wake step (the ~8-token micro-prefill that starts a beat)
climbing 22.9ms -> 31.8ms over 7 beats while the context grew only 11 tokens per
beat -- reproducible across 5 independent attempts
(simulator/validation_runs/steps_*.csv). Context length cannot explain +9ms, so
something that accumulates per beat is being paid for.

Candidate: prefix caching. Every beat re-submits the whole context as a new
request (that IS the park/wake mechanism), so vLLM hashes and looks up every
block of it, and the set of cached blocks grows monotonically as the
conversation goes on.

Test: run many beats with prefix caching on and off, recording the wake step
cost per beat. If the growth vanishes with caching off, the mechanism is the
prefix cache, and it is a per-beat tax that grows with session lifetime -- paid
~2x per second per session in this workload.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bench_vllm import VEngine   # noqa: E402

DATA = Path(__file__).parent / "data"


def run_one(model, ctx0, beats, prefix, max_len, seed=20240727):
    ve = VEngine(model, max_batched=2048, max_len=max_len, util=0.36,
                 prefix_caching=prefix, max_seqs=8)
    rng = __import__("random").Random(seed)
    ctx = [rng.randrange(1000, 100000) for _ in range(ctx0)]
    ve.drain()
    ve.add_ids(ctx + [rng.randrange(1000, 100000) for _ in range(8)], 4)
    for _ in range(40):
        if not ve.has_work():
            break
        ve.step_timed()
    ve.drain()

    rows = []
    for i in range(beats):
        ctx += [rng.randrange(1000, 100000) for _ in range(8)]
        ve.add_ids(ctx, 2)
        first = None
        rest = []
        gen = []
        while ve.has_work():
            dt, outs = ve.step_timed()
            if first is None:
                first = dt
            else:
                rest.append(dt)
            for o in outs:
                if o.outputs and o.outputs[0].token_ids:
                    gen = list(o.outputs[0].token_ids)
        ctx += gen[:2]
        rows.append({"beat": i, "ctx": len(ctx), "wake_ms": round(first, 3),
                     "decode_ms": round(sum(rest) / len(rest), 3) if rest else 0})
        if i % 5 == 0 or i == beats - 1:
            print(f"  prefix={prefix} beat {i:>3} ctx={len(ctx):>6} "
                  f"wake={first:7.2f} dec={rows[-1]['decode_ms']:6.2f}", flush=True)
    kv = ve.kv_tokens
    ve.shutdown()
    return rows, kv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--ctx0", type=int, default=2048)
    ap.add_argument("--beats", type=int, default=40)
    ap.add_argument("--max-len", type=int, default=17000)
    args = ap.parse_args()

    out = {"args": vars(args), "runs": {}}
    for prefix in (True, False):
        rows, kv = run_one(args.model, args.ctx0, args.beats, prefix,
                           args.max_len)
        first5 = sum(r["wake_ms"] for r in rows[:5]) / 5
        last5 = sum(r["wake_ms"] for r in rows[-5:]) / 5
        out["runs"][f"prefix_{prefix}"] = {
            "kv_pool_tokens": kv, "rows": rows,
            "wake_first5_mean_ms": round(first5, 3),
            "wake_last5_mean_ms": round(last5, 3),
            "wake_growth_pct": round(100 * (last5 - first5) / first5, 1),
            "decode_first5_mean_ms": round(
                sum(r["decode_ms"] for r in rows[:5]) / 5, 3),
            "decode_last5_mean_ms": round(
                sum(r["decode_ms"] for r in rows[-5:]) / 5, 3),
        }
        s = out["runs"][f"prefix_{prefix}"]
        print(f"[prefix={prefix}] wake {s['wake_first5_mean_ms']:.2f} -> "
              f"{s['wake_last5_mean_ms']:.2f}ms ({s['wake_growth_pct']:+.1f}%), "
              f"decode {s['decode_first5_mean_ms']:.2f} -> "
              f"{s['decode_last5_mean_ms']:.2f}ms")
    (DATA / "diag_wake_growth.json").write_text(json.dumps(out, indent=2))
    print(f"[write] {DATA / 'diag_wake_growth.json'}")


if __name__ == "__main__":
    main()
