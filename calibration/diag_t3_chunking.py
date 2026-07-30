"""Did vLLM really chunk the injected prefill in T3's low cells?

T3 measured one step after injecting a p-token prefill into a B-row decode
batch. Six cells (p=512/1024 at ctx<=4096) came out far cheaper than the rest,
which would mean the step did not actually carry all p tokens. This reads the
scheduler's own accounting (num_batched_tokens / num_prefill_groups) for that
step instead of inferring it from the timing.
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

    from bench_vllm import VEngine
    ve = VEngine(args.model, max_batched=2048, max_len=args.max_len,
                 util=args.util, prefix_caching=True, max_seqs=64)
    sched = ve.engine.scheduler[0]
    out = []
    for ctx, B in ((2048, 4), (2048, 8), (2048, 16), (4096, 4), (8192, 4)):
        for p in (256, 512, 1024, 2048):
            ve.drain()
            ids = [ve.add(ctx, 400, token_offset=90000 * (i + 1)) for i in range(B)]
            gen = {r: 0 for r in ids}
            while True:
                dt, outs = ve.step_timed()
                for o in outs:
                    if o.outputs:
                        gen[o.request_id] = len(o.outputs[0].token_ids)
                if all(v >= 1 for v in gen.values()):
                    break
            for _ in range(3):
                ve.step_timed()

            ve.add(p, 1, token_offset=310000)
            # inspect the scheduler decision for the very next step
            meta, outputs, _ = sched.schedule()
            nb = outputs.num_batched_tokens
            npre = sum(1 for g in outputs.scheduled_seq_groups
                       if g.token_chunk_size > 1)
            chunk = max((g.token_chunk_size for g in outputs.scheduled_seq_groups),
                        default=0)
            row = {"ctx": ctx, "B": B, "p": p, "num_batched_tokens": nb,
                   "prefill_groups": npre, "largest_chunk": chunk,
                   "prefill_fully_in_step": bool(chunk >= p)}
            out.append(row)
            print(json.dumps(row), flush=True)
            ve.drain()
    ve.shutdown()
    Path(__file__).parent.joinpath("data", "diag_t3_chunking.json").write_text(
        json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
