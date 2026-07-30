"""Why do decode steps cost 2x after a large prefill, at the SAME context?

validate.py measured B=1 decode steps at ctx~4170 costing 13.9ms when the run
had earlier absorbed an L=2048 splice, but 7.18ms at ctx=4200 in a run that
never did a large prefill. T1 agrees with the 7.18ms figure. Something other
than context length is moving, and the candidates behave differently:

  * SM clock throttling after the prefill's power burst -> recovers if we idle,
    and shows up in nvidia-smi clocks/throttle reasons.
  * a code-path change (graph replay -> eager) -> does not recover with idling,
    and does not move the clock.

So: run beats, inject once, keep going, sample clocks each beat, then idle 20s
and run more beats. Recovery-after-idle discriminates the two.
"""
import argparse
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bench_vllm import VEngine   # noqa: E402

DATA = Path(__file__).parent / "data"


def clocks(gpu):
    q = ("clocks.sm,clocks.mem,temperature.gpu,power.draw,"
         "clocks_throttle_reasons.active")
    out = subprocess.run(
        ["nvidia-smi", f"--id={gpu}", f"--query-gpu={q}",
         "--format=csv,noheader,nounits"],
        capture_output=True, text=True).stdout.strip()
    f = [x.strip() for x in out.split(",")]
    return {"sm_mhz": f[0], "mem_mhz": f[1], "temp_c": f[2], "power_w": f[3],
            "throttle": f[4]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--gpu", type=int, default=3)
    ap.add_argument("--ctx0", type=int, default=2048)
    ap.add_argument("--L", type=int, default=2048)
    ap.add_argument("--inject-at", type=int, default=6)
    ap.add_argument("--beats", type=int, default=14)
    ap.add_argument("--idle-at", type=int, default=10)
    ap.add_argument("--idle-s", type=float, default=20.0)
    ap.add_argument("--max-len", type=int, default=17000)
    args = ap.parse_args()

    ve = VEngine(args.model, max_batched=2048, max_len=args.max_len, util=0.36,
                 prefix_caching=True, max_seqs=8)
    rng = __import__("random").Random(20240727)
    ctx = [rng.randrange(1000, 100000) for _ in range(args.ctx0)]

    ve.drain()
    ve.add_ids(ctx + [rng.randrange(1000, 100000) for _ in range(8)], 8)
    for _ in range(40):
        if not ve.has_work():
            break
        ve.step_timed()
    ve.drain()

    rows = []
    for i in range(args.beats):
        if i == args.idle_at:
            print(f"  [idle] sleeping {args.idle_s}s to let clocks recover",
                  flush=True)
            time.sleep(args.idle_s)
        ctx += [rng.randrange(1000, 100000) for _ in range(8)]
        if i == args.inject_at:
            ctx += [rng.randrange(1000, 100000) for _ in range(args.L)]
        c0 = clocks(args.gpu)
        ve.add_ids(ctx, 3)
        dec, gen = [], []
        while ve.has_work():
            dt, outs = ve.step_timed()
            dec.append(dt)
            for o in outs:
                if o.outputs and o.outputs[0].token_ids:
                    gen = list(o.outputs[0].token_ids)
        ctx += gen[:3]
        # step 0 is the wake prefill; the rest are pure decode steps
        pre_ms = dec[0] if dec else 0.0
        dsteps = dec[1:]
        row = {"beat": i, "ctx": len(ctx), "injected": i == args.inject_at,
               "idled_before": i == args.idle_at,
               "n_steps": len(dec), "prefill_ms": round(pre_ms, 3),
               "decode_med_ms": round(statistics.median(dsteps), 3) if dsteps else 0,
               **c0}
        rows.append(row)
        print(f"  beat {i:>2} ctx={len(ctx):>6} pre={row['prefill_ms']:7.2f} "
              f"dec={row['decode_med_ms']:6.2f} sm={row['sm_mhz']:>5}MHz "
              f"{row['temp_c']}C {row['power_w']}W thr={row['throttle']}"
              + ("  <-- INJECT" if row["injected"] else "")
              + ("  <-- after idle" if row["idled_before"] else ""), flush=True)
    ve.shutdown()
    (DATA / "diag_post_prefill_decode.json").write_text(
        json.dumps({"args": vars(args), "rows": rows}, indent=2))
    print(f"[write] {DATA / 'diag_post_prefill_decode.json'}")


if __name__ == "__main__":
    main()
