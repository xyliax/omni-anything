"""Task F — admission-path scalability: O(N) full re-scan vs O(1) incremental.

The naive admission test re-evaluates the whole population on every arrival
(`AdmissionController.try_admit` builds an N-length list and sums it), so a busy
period of A arrivals costs O(A·N). The worst-case test is linear in the running
sums (N, ΣB_i, Σbytes), so an incremental controller decides each arrival in O(1).
We verify the decisions are identical and microbenchmark the per-arrival latency vs
population size N — the difference matters at the thousands-of-sessions scale of the
large-regime projection.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiments._common import load_cost, hbm_kv_bytes
from metronome import models
from metronome.session import PeriodicSession
from metronome.admission import (AdmissionController, IncrementalAdmissionController,
                                 AdmissionConfig)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "admission_cost")


def proto(facts, budget):
    return PeriodicSession(sid=0, facts=facts, period_s=facts.period_s,
                           deadline_s=facts.period_s, phase_s=0.0,
                           kv_budget_tokens=budget,
                           token_rate=facts.tokens_per_tick/facts.period_s)


def run(name="qwen3-omni"):
    facts = models.get(name)
    cost = load_cost(name)
    budget = max(512, facts.context_ceiling_tokens // 8)
    cfg = AdmissionConfig(hbm_kv_bytes=hbm_kv_bytes(), frame_budget_s=facts.period_s,
                          safety=0.90, mode="worst_case")
    full = AdmissionController(cost, cfg)
    inc = IncrementalAdmissionController(cost, cfg)

    # correctness: identical decisions as we admit a stream
    pop = []
    mismatches = 0
    for i in range(2000):
        s = proto(facts, budget); s.sid = i
        d_full = full.try_admit(pop, s).admit
        d_inc = inc.would_admit(s)
        if d_full != d_inc:
            mismatches += 1
        if d_full:
            pop.append(s); inc.admit(s)
    print(f"[{name}] decision mismatches over 2000 arrivals: {mismatches} "
          f"(admitted {len(pop)})")

    # microbenchmark: per-arrival decision latency vs N
    Ns = [10, 50, 100, 200, 500, 1000, 2000, 4000]
    full_us, inc_us = [], []
    for N in Ns:
        base_pop = [proto(facts, budget) for _ in range(N)]
        for j, s in enumerate(base_pop):
            s.sid = j
        cand = proto(facts, budget); cand.sid = N
        reps = max(20, 2000 // max(1, N))
        t0 = time.perf_counter()
        for _ in range(reps):
            full.try_admit(base_pop, cand)
        full_us.append((time.perf_counter() - t0) / reps * 1e6)
        # incremental: prime sums to N then time one would_admit
        inc2 = IncrementalAdmissionController(cost, cfg)
        for s in base_pop:
            inc2.admit(s)
        t0 = time.perf_counter()
        for _ in range(reps * 50):
            inc2.would_admit(cand)
        inc_us.append((time.perf_counter() - t0) / (reps * 50) * 1e6)
        print(f"  N={N:5d}  full={full_us[-1]:8.1f} us  incremental={inc_us[-1]:6.3f} us  "
              f"speedup={full_us[-1]/max(inc_us[-1],1e-9):.0f}x")

    os.makedirs(OUT, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ax.plot(Ns, full_us, "o-", color="#d62728", label="full re-scan O(N)")
    ax.plot(Ns, inc_us, "o-", color="#2ca02c", label="incremental O(1)")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("population size N"); ax.set_ylabel("per-arrival admission latency (µs)")
    ax.set_title(f"{name}: admission-path scalability (identical decisions)")
    ax.legend(); ax.grid(alpha=0.3, which="both")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "admission_cost.png"), dpi=120)
    plt.close(fig)

    res = dict(model=name, mismatches=mismatches, Ns=Ns, full_us=full_us, inc_us=inc_us,
               speedup_at_max=round(full_us[-1]/max(inc_us[-1], 1e-9), 1))
    with open(os.path.join(OUT, "admission_cost.json"), "w") as fh:
        json.dump(res, fh, indent=2)
    print(f"[{name}] at N={Ns[-1]}: {res['speedup_at_max']}x faster, decisions identical "
          f"({mismatches} mismatches)")
    return res


if __name__ == "__main__":
    run()
