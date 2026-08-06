"""C1 with confidence intervals: the simulator MSCS gain (Metronome M vs throughput-greedy
B1) across many workload seeds -> mean gain ± 95% CI. CPU-only (no GPU contention)."""
import argparse
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import experiments.core_eval as ce
from experiments.core_eval import cfg_for, TARGET_MISS, load_cost
from metronome import models
from experiments._common import hbm_kv_bytes
from bench.generator import WorkloadConfig, make_population
from sim.simulator import Simulator
from bench.metrics import mscs_served

NS = [n for n in (1, 2, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512, 768, 1024)]


def curve_seed(preset, cost, facts, ceiling, window, hbm, n_frames, seed, n_max):
    out = []
    for n in NS:
        if n > n_max:
            break
        cfg, growth = cfg_for(preset, cost, facts, ceiling, window, hbm)
        wl = WorkloadConfig(facts=facts, kv_budget_tokens=growth,
                            mean_session_s=facts.fill_time_s * 0.6, seed=seed)
        pop = make_population(wl, n)
        r = Simulator(cfg).run_static(pop, n_frames)
        out.append((n, r.metrics.miss_rate, None, None, r.admitted, None))
    return out


def ci95(xs):
    if len(xs) < 2:
        return (xs[0], xs[0]) if xs else (0, 0)
    m = statistics.mean(xs); sd = statistics.stdev(xs)
    h = 1.96 * sd / (len(xs) ** 0.5)
    return (round(m - h, 3), round(m + h, 3))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=["moshi", "minicpm-o", "qwen3-omni"])
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--n-frames", type=int, default=150)
    ap.add_argument("--n-max", type=int, default=512)
    args = ap.parse_args()
    summary = {}
    for name in args.models:
        try:
            facts = models.get(name); cost = load_cost(name)
        except Exception as e:
            print(f"[{name}] skip: {e}"); continue
        ceiling = facts.context_ceiling_tokens
        window = max(512, ceiling // 4); hbm = hbm_kv_bytes()
        gains, m_vals, b1_vals = [], [], []
        for seed in range(args.seeds):
            mv = {}
            for p in ("M", "B1"):
                c = curve_seed(p, cost, facts, ceiling, window, hbm, args.n_frames, seed, args.n_max)
                mv[p] = mscs_served([(x[0], x[4], x[1]) for x in c], TARGET_MISS)
            m_vals.append(mv["M"]); b1_vals.append(mv["B1"])
            gains.append(mv["M"] / max(1, mv["B1"]))
        summary[name] = dict(
            n_seeds=args.seeds, mean_gain=round(statistics.mean(gains), 3),
            gain_95ci=ci95(gains), mean_M=round(statistics.mean(m_vals), 1),
            mean_B1=round(statistics.mean(b1_vals), 1))
        print(f"[{name}] M/B1 gain {summary[name]['mean_gain']}x  95%CI {summary[name]['gain_95ci']}  "
              f"(M={summary[name]['mean_M']} B1={summary[name]['mean_B1']}, {args.seeds} seeds)",
              flush=True)
    os.makedirs("results/core", exist_ok=True)
    json.dump(summary, open("results/core/mscs_ci.json", "w"), indent=2)
    print("\nsaved results/core/mscs_ci.json")


if __name__ == "__main__":
    main()
