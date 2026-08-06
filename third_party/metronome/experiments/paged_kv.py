"""Task H (memory fidelity) — paged vs contiguous KV under session churn.

Metronome's memory admission assumes usable capacity = Σ_i B_i ≤ HBM. That holds
only with **paged KV** (vLLM/SGLang PagedAttention): fixed-size blocks mean a session
can grow into any free blocks, so there is no *external* fragmentation — only
internal fragmentation bounded by one block per session. With contiguous per-session
allocation, the churn of variable-size sessions arriving and departing leaves holes,
so a new session can be rejected even when total free ≥ its size — the admission
model would over-count capacity.

We simulate an arrival/departure stream of variable-size KV regions and compare the
achievable memory utilisation (and blocking) under a contiguous best-fit allocator vs
a paged allocator, and report the internal-fragmentation overhead of paging.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "paged")


def contiguous_blocking(sizes_arr, lifetimes, hbm, seed=0):
    """Best-fit contiguous allocator with free-list holes; returns blocking + peak util."""
    # free list of (start, length) holes; total capacity hbm
    holes = [(0.0, hbm)]
    live = []   # (depart_t, start, size)
    n_block = 0
    n_arr = 0
    peak_used = 0.0
    t = 0.0
    for i, (size, life) in enumerate(zip(sizes_arr, lifetimes)):
        t += 1.0
        # departures free their region (coalesce)
        live2 = []
        for (dt, st, sz) in live:
            if dt <= t:
                holes.append((st, sz))
            else:
                live2.append((dt, st, sz))
        live = live2
        # coalesce holes
        holes.sort()
        merged = []
        for h in holes:
            if merged and merged[-1][0] + merged[-1][1] >= h[0] - 1e-9:
                s0, l0 = merged[-1]
                merged[-1] = (s0, max(l0, h[0] + h[1] - s0))
            else:
                merged.append(list(h))
        holes = [tuple(h) for h in merged]
        # best-fit
        n_arr += 1
        cand = [(l, s) for (s, l) in holes if l >= size]
        if not cand:
            n_block += 1
            continue
        l, s = min(cand)        # smallest sufficient hole
        holes.remove((s, l))
        if l - size > 1e-9:
            holes.append((s + size, l - size))
        live.append((t + life, s, size))
        used = sum(sz for (_, _, sz) in live)
        peak_used = max(peak_used, used)
    return n_block / max(1, n_arr), peak_used / hbm


def paged_blocking(sizes_arr, lifetimes, hbm, block, seed=0):
    """Paged allocator: a session takes ceil(size/block) blocks from anywhere; admit
    iff free blocks suffice. No external fragmentation; internal frag <= 1 block/sess."""
    total_blocks = int(hbm // block)
    free_blocks = total_blocks
    live = []
    n_block = 0; n_arr = 0; peak_used = 0; internal_frag = 0.0; n_live_peak = 0
    t = 0.0
    for size, life in zip(sizes_arr, lifetimes):
        t += 1.0
        live2 = []
        for (dt, b) in live:
            if dt <= t:
                free_blocks += b
            else:
                live2.append((dt, b))
        live = live2
        n_arr += 1
        need = int(np.ceil(size / block))
        if need <= free_blocks:
            free_blocks -= need
            live.append((t + life, need))
            used_blocks = total_blocks - free_blocks
            peak_used = max(peak_used, used_blocks)
            internal_frag += need * block - size
            n_live_peak = max(n_live_peak, len(live))
        else:
            n_block += 1
    frag_overhead = internal_frag / max(1, n_arr) / block   # avg fraction of a block
    return n_block / max(1, n_arr), peak_used / total_blocks, frag_overhead


def run():
    os.makedirs(OUT, exist_ok=True)
    rng = np.random.default_rng(0)
    hbm = 80.0 * 2**30
    n = 4000
    # variable session KV sizes (GiB-scale, log-uniform 0.2-8 GiB) — long-context mix
    sizes = (10 ** rng.uniform(np.log10(0.2), np.log10(8.0), n)) * 2**30
    lifetimes = rng.exponential(40.0, n)
    block_tokens = 16
    # block bytes ~ MiniCPM-o 144 KiB/token * 16 tokens
    block = 16 * 144 * 1024

    cont_block, cont_util = contiguous_blocking(sizes, lifetimes, hbm)
    rows = []
    for blk_tok in (16, 64, 256):
        blk = blk_tok * 144 * 1024
        pb, pu, frag = paged_blocking(sizes, lifetimes, hbm, blk)
        rows.append(dict(block_tokens=blk_tok, blocking=pb, util=pu, frag_overhead=frag))
        print(f"  paged block={blk_tok:3d} tok: blocking={pb:.3f} util={pu:.3f} "
              f"internal-frag={frag*100:.2f}% of a block/session")
    print(f"  contiguous best-fit: blocking={cont_block:.3f} util={cont_util:.3f} "
          f"(external fragmentation)")

    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    labels = ["contiguous"] + [f"paged/{r['block_tokens']}tok" for r in rows]
    blockings = [cont_block] + [r["blocking"] for r in rows]
    utils = [cont_util] + [r["util"] for r in rows]
    x = np.arange(len(labels))
    ax.bar(x - 0.2, [b*100 for b in blockings], 0.4, label="blocking %", color="#d62728")
    ax.bar(x + 0.2, [u*100 for u in utils], 0.4, label="peak util %", color="#2ca02c")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=15)
    ax.set_ylabel("%"); ax.set_title("Paged KV eliminates external fragmentation under churn")
    ax.legend(); ax.grid(alpha=0.3, axis="y")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "paged_kv.png"), dpi=120)
    plt.close(fig)

    res = dict(contiguous=dict(blocking=cont_block, util=cont_util), paged=rows,
               frag_reduction=round(cont_block - rows[0]["blocking"], 3))
    with open(os.path.join(OUT, "paged_kv.json"), "w") as fh:
        json.dump(res, fh, indent=2)
    print(f"=> paging cuts blocking from {cont_block:.1%} (contiguous) to "
          f"{rows[0]['blocking']:.1%}, validating the Sum(B_i)<=HBM admission model.")
    return res


if __name__ == "__main__":
    run()
