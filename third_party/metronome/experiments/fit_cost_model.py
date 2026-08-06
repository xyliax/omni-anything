"""S0+S3: measure per-tick latency vs context length on the real GPU, fit the
saturating-ramp cost model, and check GATE B (model predicts measured latency).

Outputs per model:
  results/cost_model/<model>.json   -- fitted CostModel
  results/cost_model/<model>_single.csv  -- raw single-session sweep
  results/cost_model/<model>_batch.csv   -- raw batch sweep

GATE B: single-session p99 fit max relative residual <= 0.15 (±15%).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bench.gpu_probe import wait_for_window
from bench.tick_kernel import TickKernel
from metronome import models
from metronome.cost_model import fit_single, fit_batch

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "cost_model")

# Per-model context-length grids (tokens), capped at the model's ceiling.
GRIDS = {
    "moshi":     [0, 256, 512, 1024, 1536, 2048, 3072, 4096],
    "minicpm-o": [0, 1024, 2048, 4096, 8192, 12288, 16384, 24576, 32768],
    "qwen3-omni":[0, 512, 1024, 2048, 3072, 4096, 6144, 8192],
}
# Batch sweep: (n_sessions, per_session_L) pairs.
def batch_plan(ceiling):
    Ls = [c for c in (512, 2048, min(8192, ceiling)) if c <= ceiling]
    plan = []
    for B in (1, 2, 4, 8):
        for L in Ls:
            plan.append((B, L))
    return plan


def write_csv(path, timings):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["batch", "total_kv", "n_new", "p50_ms", "p99_ms", "mean_ms", "reps"])
        for t in timings:
            w.writerow([t.batch_sessions, t.total_kv_tokens, t.n_new,
                        round(t.p50, 5), round(t.p99, 5), round(t.mean, 5), t.reps])


def run_model(name, reps, max_total_kv, use_graph=True):
    facts = models.get(name)
    print(f"\n=== {name}  (KV {facts.kv_bytes_per_token_kib:.1f} KiB/tok, "
          f"period {facts.period_s*1000:.0f}ms) ===")
    k = TickKernel(facts)

    # --- single-session sweep ---
    grid = [L for L in GRIDS[name] if L <= facts.context_ceiling_tokens]
    singles = []
    for L in grid:
        wait_for_window(need_free_gib=30, max_util_pct=35, quiet=True, timeout_s=10800)
        t = k.time_tick([L], reps=reps, warmup=6, use_graph=use_graph)
        singles.append(t)
        print(f"  single L={L:6d}  p50={t.p50:7.3f}ms  p99={t.p99:7.3f}ms")

    cost = fit_single(singles, kv_bytes_per_token=facts.kv_bytes_per_token,
                      notes=f"{name} on {singles[0].device}")

    # --- batch sweep ---
    batches = []
    for (B, L) in batch_plan(facts.context_ceiling_tokens):
        if B * L > max_total_kv:
            print(f"  [skip] batch B={B} L={L} (total_kv {B*L} > cap {max_total_kv})")
            continue
        wait_for_window(need_free_gib=30, max_util_pct=35, quiet=True, timeout_s=10800)
        t = k.time_tick([L] * B, reps=reps, warmup=6, use_graph=use_graph)
        batches.append(t)
        print(f"  batch B={B} L={L:6d} (tot {B*L:7d})  p50={t.p50:7.3f}ms  p99={t.p99:7.3f}ms")
    if batches:
        fit_batch(cost, batches)

    os.makedirs(OUT, exist_ok=True)
    cost.to_json(os.path.join(OUT, f"{name}.json"))
    write_csv(os.path.join(OUT, f"{name}_single.csv"), singles)
    if batches:
        write_csv(os.path.join(OUT, f"{name}_batch.csv"), batches)

    # GATE B is judged on the BATCHED model (what the scheduler/admission use) at
    # its operating points, on the robust median fit: max relative residual <= 0.15.
    gate_b = cost.batch_max_rel_resid <= 0.15
    print(f"  fit(p50): C_fixed={cost.c_fixed:.3f}ms  alpha={cost.alpha*1000:.4f}us/tok  "
          f"R2={cost.single_r2:.4f}  single_rel_resid={cost.single_max_rel_resid:.3f}")
    print(f"  implied BW={cost.implied_bandwidth_gibs:.0f} GiB/s  tail_factor={cost.tail_factor:.3f}  "
          f"batch[base={cost.batch_base:.2f} per_s={cost.batch_per_session:.4f} "
          f"alpha={cost.batch_alpha*1000:.4f}us/tok R2={cost.batch_r2:.4f} relres={cost.batch_max_rel_resid:.3f}]")
    print(f"  GATE B ({name}): {'PASS' if gate_b else 'FAIL'} "
          f"(batch max rel resid {cost.batch_max_rel_resid:.3f} <= 0.15)")
    return cost, gate_b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=["moshi", "minicpm-o", "qwen3-omni"])
    ap.add_argument("--reps", type=int, default=25)
    ap.add_argument("--max-total-kv", type=int, default=120_000,
                    help="cap on B*L tokens per batch point (memory politeness)")
    ap.add_argument("--eager", action="store_true", help="disable CUDA graphs (robust on a contended GPU)")
    args = ap.parse_args()

    results = {}
    for name in args.models:
        cost, gate = run_model(name, args.reps, args.max_total_kv, use_graph=not args.eager)
        results[name] = gate
    print("\n=== GATE B summary ===")
    for name, ok in results.items():
        print(f"  {name}: {'PASS' if ok else 'FAIL'}")


if __name__ == "__main__":
    main()
