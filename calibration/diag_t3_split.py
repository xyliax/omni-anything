"""Does the mixed-step cost depend only on TOTAL injected prefill tokens, or
also on how many requests they are split across?

T3 injected p tokens as ONE request (run_calib_vllm.py t3()); the simulator
prices mixed steps on total p only. Here: same decode batch (B=8, ctx=4096),
same total p, split into k in {1,2,4,8} requests of p/k tokens each.
Method mirrors t3(): fresh decode batch per cell, inject, time ONE step.
`n_done` counts injected requests (max_tokens=1) that finished in the measured
step -- if < k the step did not absorb all of them and the row says so.
"""
import json
import os
import statistics
import sys
import time
from pathlib import Path

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "3")
os.environ.setdefault("VLLM_USE_V1", "0")
os.environ.setdefault("VLLM_LOGGING_LEVEL", "WARNING")
sys.path.insert(0, str(Path(__file__).parent))
from bench_vllm import VEngine  # noqa: E402

MODEL = ("/home/yuxing/.cache/huggingface/hub/models--Qwen--Qwen3-1.7B/"
         "snapshots/70d244cc86ccca08cf5af4e1e306ecf908b1ad5e/")
B, CTX = 8, 4096
CELLS = [(64, 1), (64, 8),
         (256, 1), (256, 4), (256, 8),
         (512, 1), (512, 2), (512, 4), (512, 8),
         (1024, 1), (1024, 2), (1024, 4), (1024, 8)]
WARM, ITERS = 3, 12

ve = VEngine(MODEL, max_batched=2048, max_len=8192, util=0.36,
             prefix_caching=True, max_seqs=64)
rows = []
for p, k in CELLS:
    ve.drain()
    ids = [ve.add(CTX, 400, token_offset=90000 * (i + 1)) for i in range(B)]
    gen = {r: 0 for r in ids}
    while True:
        dt, outs = ve.step_timed()
        for o in outs:
            if o.outputs:
                gen[o.request_id] = len(o.outputs[0].token_ids)
        if all(v >= 1 for v in gen.values()):
            break
    base = statistics.median(ve.step_timed()[0] for _ in range(5))
    samples, fused = [], []
    for it in range(WARM + ITERS):
        rids = [ve.add(p // k, 1, token_offset=310000 + it * 7919 + j * 131071)
                for j in range(k)]
        rset = set(rids)
        dt, outs = ve.step_timed()
        n_done = sum(1 for o in outs
                     if o.request_id in rset and o.finished)
        # let stragglers finish so the next iteration starts clean
        for _ in range(4):
            if ve.has_work():
                ve.step_timed()
        if it >= WARM:
            samples.append(dt)
            fused.append(n_done)
    p50 = statistics.median(samples)
    row = {"p_total": p, "k": k, "per_req": p // k,
           "base_decode_ms": round(base, 2), "p50_ms": round(p50, 2),
           "extra_ms": round(p50 - base, 2),
           "n_done_median": statistics.median(fused), "k_expected": k}
    rows.append(row)
    print(f"p={p:>5} k={k}  per_req={p//k:>4}  base={base:6.2f}ms  "
          f"fused_step={p50:7.2f}ms  extra={p50-base:6.2f}ms  "
          f"done_in_step={statistics.median(fused):.0f}/{k}", flush=True)

ve.shutdown()
Path(__file__).parent.joinpath("data", "diag_t3_split.json").write_text(
    json.dumps(rows, indent=2))
print("saved data/diag_t3_split.json")
