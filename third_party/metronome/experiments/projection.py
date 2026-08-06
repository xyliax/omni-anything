"""S10: large-regime projection (analytical, clearly labeled — not measured).

Uses the *measured* small-regime constants (the effective HBM bandwidth implied by
alpha, and the per-tick fixed cost) to project the large regime of RESEARCH_PLAN
§1.4: a 200B+ MoE, ~1M-context interaction model whose KV never saturates within a
session and a single session can exceed one GPU's HBM.

We project, for a 1M-context model:
  * KV per session vs HBM (single-session-exceeds-GPU threshold),
  * per-tick attention-read time under dense vs sparse/windowed attention,
  * the deadline-feasible context length under a 200 ms tick (TML cadence),
showing why tiered KV + sparse attention is mandatory at scale.

All assumptions are written to results/projection/assumptions.json.
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

from experiments._common import load_cost, all_models
from metronome import models

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "projection")


def measured_bandwidth_gibs():
    """Effective HBM bandwidth (GiB/s) implied by the measured alpha across models —
    the small-regime constant we extrapolate."""
    bws = []
    for name in all_models():
        cm = load_cost(name)
        if cm.implied_bandwidth_gibs == cm.implied_bandwidth_gibs:  # not NaN
            bws.append(cm.implied_bandwidth_gibs)
    return float(np.median(bws)) if bws else 600.0


# --- the projected large model (TML-Interaction-Small-like) -----------------
ASSUMPTIONS = dict(
    name="projected-large (TML-Interaction-Small-like)",
    total_params_b=276, active_params_b=12,
    num_layers=80, num_kv_heads_gqa=8, num_kv_heads_mla_equiv=1, head_dim=128,
    kv_dtype_bytes=2,
    context_ceiling_tokens=1_000_000,
    tick_s=0.200,                    # 200 ms micro-turns
    token_rate_per_s=74.0,           # ~74 tok/s fill rate
    weights_fp8_gib=276.0,           # 276B @ fp8
    sparse_window_tokens=4096,       # TML "Split-KV 4096 tokens at a time" hint
)


def kv_bytes_per_token(num_kv_heads, layers, head_dim, dbytes):
    return 2 * num_kv_heads * head_dim * layers * dbytes


def run():
    os.makedirs(OUT, exist_ok=True)
    bw = measured_bandwidth_gibs()
    a = ASSUMPTIONS
    bw_bytes = bw * 2**30

    # KV/token for GQA vs MLA-equivalent
    kv_gqa = kv_bytes_per_token(a["num_kv_heads_gqa"], a["num_layers"],
                                a["head_dim"], a["kv_dtype_bytes"])
    kv_mla = kv_bytes_per_token(a["num_kv_heads_mla_equiv"], a["num_layers"],
                                a["head_dim"], a["kv_dtype_bytes"])

    ctx = a["context_ceiling_tokens"]
    kv_full_gqa_gib = kv_gqa * ctx / 2**30
    kv_full_mla_gib = kv_mla * ctx / 2**30
    fill_time_h = ctx / a["token_rate_per_s"] / 3600.0

    # per-tick attention-read time at full context (dense) vs windowed (sparse)
    dense_read_s_gqa = kv_gqa * ctx / bw_bytes
    dense_read_s_mla = kv_mla * ctx / bw_bytes
    sparse_read_s_gqa = kv_gqa * a["sparse_window_tokens"] / bw_bytes

    # deadline-feasible context under the tick budget (dense), GQA
    feasible_ctx_dense = a["tick_s"] * bw_bytes / kv_gqa

    proj = dict(
        measured_bandwidth_gibs=round(bw, 1),
        kv_bytes_per_token_gqa=kv_gqa, kv_bytes_per_token_mla=kv_mla,
        kv_full_context_gib_gqa=round(kv_full_gqa_gib, 1),
        kv_full_context_gib_mla=round(kv_full_mla_gib, 1),
        single_session_exceeds_80GB_gpu=kv_full_gqa_gib > 80,
        weights_fp8_gib=a["weights_fp8_gib"],
        fill_time_hours=round(fill_time_h, 2),
        dense_attn_read_ms_full_gqa=round(dense_read_s_gqa * 1000, 1),
        dense_attn_read_ms_full_mla=round(dense_read_s_mla * 1000, 1),
        sparse_attn_read_ms_window_gqa=round(sparse_read_s_gqa * 1000, 3),
        tick_budget_ms=a["tick_s"] * 1000,
        dense_blows_budget=dense_read_s_gqa * 1000 > a["tick_s"] * 1000,
        feasible_dense_context_tokens=int(feasible_ctx_dense),
        feasible_dense_context_vs_ceiling=round(feasible_ctx_dense / ctx, 4),
    )

    with open(os.path.join(OUT, "assumptions.json"), "w") as fh:
        json.dump(a, fh, indent=2)
    with open(os.path.join(OUT, "projection.json"), "w") as fh:
        json.dump(proj, fh, indent=2)

    # Figure: per-tick attention-read time vs context length, dense vs windowed,
    # with the tick budget and the single-GPU HBM line.
    ctxs = np.logspace(3, 6, 80)
    read_dense = kv_gqa * ctxs / bw_bytes * 1000
    read_sparse = np.full_like(ctxs, kv_gqa * a["sparse_window_tokens"] / bw_bytes * 1000)
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ax.plot(ctxs, read_dense, label="dense attention (read whole KV)", color="#d62728")
    ax.plot(ctxs, read_sparse, label=f"sparse/windowed ({a['sparse_window_tokens']} tok)",
            color="#2ca02c")
    ax.axhline(a["tick_s"]*1000, color="black", ls=":", label=f"{a['tick_s']*1000:.0f} ms tick budget")
    ax.axvline(feasible_ctx_dense, color="#d62728", ls="--", alpha=0.6,
               label=f"dense-feasible ctx ≈ {feasible_ctx_dense/1000:.0f}k")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("session context length (tokens)")
    ax.set_ylabel("per-tick attention-read time (ms)")
    ax.set_title("Large regime: dense attention blows the tick budget; sparse/tiered KV mandatory")
    ax.legend(fontsize=8); ax.grid(alpha=0.3, which="both")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "large_regime_attention.png"), dpi=120)
    plt.close(fig)

    print("=== Large-regime projection (analytical, from measured bandwidth) ===")
    print(f"  measured effective HBM BW (median across models): {bw:.0f} GiB/s")
    print(f"  KV @ 1M ctx: GQA {kv_full_gqa_gib:.0f} GiB/session, MLA {kv_full_mla_gib:.0f} GiB")
    print(f"  single session exceeds 80GB GPU (GQA): {proj['single_session_exceeds_80GB_gpu']}")
    print(f"  fill time: {fill_time_h:.1f} h (never saturates in a session)")
    print(f"  dense attn read @1M: {proj['dense_attn_read_ms_full_gqa']:.0f} ms "
          f"(budget {a['tick_s']*1000:.0f} ms) -> blows budget: {proj['dense_blows_budget']}")
    print(f"  deadline-feasible dense context: {feasible_ctx_dense/1000:.0f}k tokens "
          f"({proj['feasible_dense_context_vs_ceiling']*100:.2f}% of 1M ceiling)")
    print(f"  => sparse/windowed + tiered KV is mandatory at scale.")
    return proj


if __name__ == "__main__":
    run()
