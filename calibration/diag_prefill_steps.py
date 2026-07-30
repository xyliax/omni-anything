"""Why does a tiny prefill cost ~25ms?

T2 sums the step times until the first token appears, but never recorded HOW
MANY steps that took. If a wake with 8 new tokens costs one 25ms step, that is
a real per-beat cost the simulator must carry. If it costs 3-4 ordinary steps,
then the per-step cost is normal and T2's number is a step-count artefact.
This prints the per-step breakdown for a resident session being woken with a
small number of new tokens -- exactly the simulator's per-beat operation.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--max-len", type=int, default=17000)
    ap.add_argument("--util", type=float, default=0.36)
    args = ap.parse_args()

    from bench_vllm import VEngine, stats
    ve = VEngine(args.model, max_batched=2048, max_len=args.max_len,
                 util=args.util, prefix_caching=True, max_seqs=16)
    out = []
    for ctx in (1024, 4096):
        prefix = [(700000 + i) % 100000 + 1000 for i in range(ctx)]
        ve.add_shared_prefix(prefix, 0, 1)
        ve.drain()
        for L in (8, 16, 64, 256):
            per_step, totals, counts = [], [], []
            for it in range(18):
                ve.add_shared_prefix(prefix, L, 1)
                steps = []
                while ve.has_work():
                    dt, outs = ve.step_timed()
                    steps.append(round(dt, 3))
                    if any(o.finished for o in outs) or any(
                            o.outputs and o.outputs[0].token_ids for o in outs):
                        break
                ve.drain()
                if it >= 6:
                    totals.append(sum(steps))
                    counts.append(len(steps))
                    per_step.append(steps)
            row = {"ctx": ctx, "L": L,
                   "steps_median": sorted(counts)[len(counts) // 2],
                   "total_p50_ms": round(stats(totals)["p50_ms"], 3),
                   "first_step_ms": round(sorted(s[0] for s in per_step)[
                       len(per_step) // 2], 3),
                   "example_steps": per_step[-1]}
            out.append(row)
            print(json.dumps(row), flush=True)
    ve.shutdown()
    Path(__file__).parent.joinpath("data", "diag_prefill_steps.json").write_text(
        json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
