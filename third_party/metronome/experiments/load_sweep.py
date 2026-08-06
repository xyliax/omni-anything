"""Open-loop Poisson-arrival load test with CIs (C1/C3) — robust version. Builds ONE real
engine per model and reuses it across the offered-load × seed sweep (avoids the repeated
engine alloc/free that tripped a CUDA fault), measuring the deadline miss-rate for Metronome
admission vs throughput-greedy. Produces the graceful-vs-cliff curve with confidence
intervals. Run one model per invocation for crash isolation."""
import argparse
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")

import numpy as np
import torch
from bench.gpu_probe import wait_for_window
from metronome import models
from metronome.engine import ServingEngine
import experiments.engine_open as eo


def ci95(xs):
    if len(xs) < 2:
        return (round(xs[0], 4), round(xs[0], 4)) if xs else (0, 0)
    m, sd = statistics.mean(xs), statistics.stdev(xs)
    h = 1.96 * sd / (len(xs) ** 0.5)
    return (round(max(0, m - h), 4), round(m + h, 4))


def sim_open(eng, facts, capacity, max_sessions, window, n_frames, offered, mode,
             mean_life=40, seed=0):
    """One Poisson-arrival run on a SHARED engine (state reset each call)."""
    rng = np.random.default_rng(seed)
    budget_ms = facts.period_s * 1000.0
    n_new = max(1, int(round(facts.tokens_per_tick)))
    eng.lengths[:] = 0
    free = list(range(max_sessions)); active = {}
    arr_rate = offered * capacity / mean_life
    over = tot = n_arr = n_adm = 0
    for fi in range(n_frames):
        for r in [r for r, d in active.items() if d <= fi]:
            del active[r]; free.append(r); eng.lengths[r] = 0
        for _ in range(rng.poisson(arr_rate)):
            n_arr += 1
            if mode == "admission" and len(active) >= capacity:
                continue
            if not free:
                continue
            r = free.pop()
            eng.lengths[r] = int(rng.uniform(0.6, 1.0) * window)
            active[r] = fi + int(rng.exponential(mean_life)); n_adm += 1
        rows = list(active.keys())
        if not rows:
            continue
        lat = eng.step_active(rows, n_new)
        tot += len(rows)
        if lat > budget_ms:
            over += len(rows)
    return dict(miss_rate=over / max(1, tot), blocking=1 - n_adm / max(1, n_arr))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--offered", nargs="*", type=float,
                    default=[0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0])
    ap.add_argument("--seeds", type=int, default=4)
    ap.add_argument("--n-frames", type=int, default=150)
    ap.add_argument("--max-util", type=int, default=85)
    args = ap.parse_args()
    name = args.model
    facts = models.get(name)
    window = max(512, facts.context_ceiling_tokens // 4)
    per = window * facts.num_kv_heads * facts.head_dim * 2 * 2
    wait_for_window(need_free_gib=3.0, max_util_pct=args.max_util, quiet=True, timeout_s=72000)
    cap = eo._measured_capacity(name, window)
    max_sessions = max(cap + 8, int(2.5 * 2**30 / per))
    eng = ServingEngine(facts, max_sessions=max_sessions, max_budget_tokens=window)
    # warmup a real (initialised) cohort so the first real step isn't on empty rows
    eng.serve_cohort(min(8, max_sessions), n_frames=3, start_lengths=[window] * min(8, max_sessions), warmup=2)
    print(f"=== {name} Poisson load sweep (capacity={cap}, max_rows={max_sessions}) ===", flush=True)
    curve = {}
    for of in args.offered:
        row = {}
        for mode in ("admission", "greedy"):
            ms = [sim_open(eng, facts, cap, max_sessions, window, args.n_frames, of, mode, seed=s)["miss_rate"]
                  for s in range(args.seeds)]
            row[mode] = dict(mean_miss=round(statistics.mean(ms), 4), ci=ci95(ms))
        curve[of] = row
        print(f"  offered {of:>4}x:  admission miss={row['admission']['mean_miss']:.3f}{row['admission']['ci']}"
              f"   greedy miss={row['greedy']['mean_miss']:.3f}{row['greedy']['ci']}", flush=True)
    del eng; torch.cuda.empty_cache()
    os.makedirs("results/open", exist_ok=True)
    fn = f"results/open/load_sweep_{name}.json"
    json.dump(dict(model=name, capacity=cap, seeds=args.seeds, curve=curve), open(fn, "w"), indent=2)
    print(f"saved {fn}")


if __name__ == "__main__":
    main()
