"""Tier-2 #3: trace-driven (realistic) workload. The Poisson load-sweep assumed memoryless
arrivals + exponential lifetimes. Real conversational traffic is BURSTY (on/off, correlated
arrivals) with HEAVY-TAILED session durations. We replay such a process through an open-loop
sim whose per-frame latency comes from the VALIDATED cost model (cost.predict_batch), and
compare Metronome admission vs throughput-greedy. The graceful-vs-cliff result should hold —
and bursts make greedy worse — under realistic, non-Poisson load.
"""
import argparse
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from experiments._common import load_cost, hbm_kv_bytes
from metronome import models
from metronome.admission import AdmissionController, AdmissionConfig
from metronome.session import PeriodicSession


def proto(facts, window):
    return PeriodicSession(sid=0, facts=facts, period_s=facts.period_s, deadline_s=facts.period_s,
                           phase_s=0.0, kv_budget_tokens=window,
                           token_rate=facts.tokens_per_tick / facts.period_s)


def run_trace(ac, protos, facts, capacity, mem_cap, n_frames, offered, mode, seed):
    """On/off (bursty, MMPP) arrivals + lognormal lifetimes; per-frame latency from the SAME
    cost model + projection the admission test uses (predicted_frame_ms); miss = > budget."""
    rng = np.random.default_rng(seed)
    budget_ms = facts.period_s * 1000.0
    mean_life = 40
    base_rate = offered * capacity / mean_life
    state, p_on2off, p_off2on = "off", 0.1, 0.033
    active = []
    over = tot = 0
    for _ in range(n_frames):
        state = ("on" if rng.random() < p_off2on else "off") if state == "off" \
            else ("off" if rng.random() < p_on2off else "on")
        rate = base_rate * (4.0 if state == "on" else 0.1)
        for _ in range(rng.poisson(rate)):
            cap = capacity if mode == "admission" else mem_cap
            if len(active) >= cap:
                continue
            active.append(int(rng.lognormal(mean=np.log(mean_life), sigma=0.8)) + 1)
        active = [a - 1 for a in active if a - 1 > 0]
        if not active:
            continue
        frame_ms = ac.predicted_frame_ms(protos[:len(active)])
        tot += 1
        if frame_ms > budget_ms:
            over += 1
    return over / max(1, tot)


def ci95(xs):
    if len(xs) < 2:
        return (round(xs[0], 4), round(xs[0], 4))
    m, sd = statistics.mean(xs), statistics.stdev(xs)
    h = 1.96 * sd / len(xs) ** 0.5
    return (round(max(0, m - h), 4), round(m + h, 4))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=["moshi", "qwen3-omni", "minicpm-o"])
    ap.add_argument("--offered", nargs="*", type=float, default=[0.5, 1.0, 1.5, 2.0, 3.0])
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--n-frames", type=int, default=400)
    args = ap.parse_args()
    summary = {}
    for name in args.models:
        try:
            facts = models.get(name); cost = load_cost(name)
        except Exception as e:
            print(f"[{name}] skip {e}"); continue
        window = max(512, facts.context_ceiling_tokens // 4); hbm = hbm_kv_bytes()
        ac = AdmissionController(cost, AdmissionConfig(hbm, facts.period_s, 0.90, mode="worst_case"))
        cap = ac.predict_capacity(proto(facts, window))
        mem_cap = max(cap + 8, int(hbm / max(1, proto(facts, window).budget_bytes)))
        protos = [proto(facts, window) for _ in range(mem_cap + 2)]   # reuse the same projection
        print(f"=== {name} trace-driven (bursty MMPP + lognormal life, capacity={cap}) ===", flush=True)
        curve = {}
        for of in args.offered:
            row = {}
            for mode in ("admission", "greedy"):
                ms = [run_trace(ac, protos, facts, cap, mem_cap, args.n_frames, of, mode, s)
                      for s in range(args.seeds)]
                row[mode] = dict(mean_miss=round(statistics.mean(ms), 4), ci=ci95(ms))
            curve[of] = row
            print(f"  offered {of:>4}x:  admission miss={row['admission']['mean_miss']:.3f}"
                  f"{row['admission']['ci']}   greedy miss={row['greedy']['mean_miss']:.3f}"
                  f"{row['greedy']['ci']}", flush=True)
        summary[name] = dict(capacity=cap, arrival="bursty MMPP (4x/0.1x on-off)",
                             lifetime="lognormal(sigma=0.8)", curve=curve)
    os.makedirs("results/trace", exist_ok=True)
    json.dump(summary, open("results/trace/trace_driven.json", "w"), indent=2)
    print("\nsaved results/trace/trace_driven.json")


if __name__ == "__main__":
    main()
