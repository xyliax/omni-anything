"""Repeatability / drift probe on a SHARED GPU.

T1 measured B=4,ctx=4096 at 9.22ms; T3's baseline for the same cell read
17.50ms ~15 min later. Either the harnesses differ or the neighbour's load
drifted. This probe re-measures one fixed cell many times over several
minutes and reports the spread, plus the CUDA-graph on/off comparison.

Output feeds the "validity threats" section: it bounds how much of any
measured difference could be contention rather than the variable under test.
"""
import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("VLLM_USE_V1", "0")
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")
sys.path.insert(0, str(Path(__file__).parent))
from bench_vllm import VEngine, stats  # noqa: E402


def decode_cell(ve, B, ctx, iters=20, warmup=5):
    ve.drain()
    ids = [ve.add(ctx, iters + warmup + 8, token_offset=90000 * (i + 1))
           for i in range(B)]
    gen = {r: 0 for r in ids}
    while True:
        dt, outs = ve.step_timed()
        for o in outs:
            if o.outputs:
                gen[o.request_id] = len(o.outputs[0].token_ids)
        if all(v >= 1 for v in gen.values()):
            break
    for _ in range(warmup):
        ve.step_timed()
    s = []
    for _ in range(iters):
        dt, _ = ve.step_timed()
        if not ve.has_work():
            break
        s.append(dt)
    ve.drain()
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--rounds", type=int, default=10)
    ap.add_argument("--gap-s", type=float, default=20)
    ap.add_argument("--util", type=float, default=0.36)
    ap.add_argument("--max-len", type=int, default=17000)
    ap.add_argument("--out", default="repeatability")
    args = ap.parse_args()

    ve = VEngine(args.model, max_len=args.max_len, util=args.util)
    cells = [(1, 1024), (4, 4096), (1, 8192), (1, 16384)]
    rows = []
    t_start = time.time()
    for rd in range(args.rounds):
        for (B, ctx) in cells:
            if B * (ctx + 64) > ve.kv_tokens * 0.85:
                continue
            s = decode_cell(ve, B, ctx)
            if not s:
                continue
            st = stats(s)
            import torch
            free, _ = torch.cuda.mem_get_info(0)
            rows.append({"round": rd, "B": B, "ctx": ctx,
                         "t_since_start_s": round(time.time() - t_start, 1),
                         "free_GiB": round(free / 2**30, 2),
                         "graph_capture_len": ve.args["seq_len_to_capture"],
                         **st})
            print(f"[rd{rd}] B={B} ctx={ctx:>5} p50={st['p50_ms']:>7.2f}ms "
                  f"min={st['min_ms']:>7.2f} max={st['max_ms']:>7.2f}", flush=True)
        time.sleep(args.gap_s)
    ve.shutdown()

    out = Path(__file__).parent / "data"
    out.mkdir(parents=True, exist_ok=True)
    p = out / f"{args.out}.csv"
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[write] {p}")

    # summarise drift per cell
    print(f"\n{'cell':>14}{'n':>4}{'min_p50':>10}{'max_p50':>10}"
          f"{'spread%':>10}{'mean':>9}")
    summary = {}
    for (B, ctx) in cells:
        ps = [r["p50_ms"] for r in rows if r["B"] == B and r["ctx"] == ctx]
        if not ps:
            continue
        spread = 100 * (max(ps) - min(ps)) / min(ps)
        summary[f"B{B}_ctx{ctx}"] = {
            "n": len(ps), "min": min(ps), "max": max(ps),
            "spread_pct": round(spread, 1),
            "mean": round(sum(ps) / len(ps), 3)}
        print(f"{f'B={B} ctx={ctx}':>14}{len(ps):>4}{min(ps):>10.2f}"
              f"{max(ps):>10.2f}{spread:>9.1f}%{sum(ps)/len(ps):>9.2f}")
    (out / f"{args.out}_summary.json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
