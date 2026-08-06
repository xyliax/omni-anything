"""Task G — multi-GPU placement & scalability.

KV is *pinned* (RESEARCH_PLAN §1.3: swapping/moving it is bandwidth-dominated and
blows the frame), so mid-session **migration is infeasible** and the cluster lever is
**admission-time placement**: when a session arrives, which of G accelerators admits
it? With heterogeneous per-session KV budgets this is an online bin-packing problem
under each GPU's joint timing+memory schedulability constraint.

We compare placement policies (random / round-robin / first-fit / best-fit) on
cluster blocking and served sessions, show scaling vs G, and quantify the migration
cost that rules out mid-session rebalancing.
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

from experiments._common import load_cost, hbm_kv_bytes
from metronome import models
from metronome.session import PeriodicSession
from metronome.admission import IncrementalAdmissionController, AdmissionConfig
from bench.metrics import jain_index

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "multigpu")


def make_session(sid, facts, budget, t, rng, mean_hold):
    s = PeriodicSession(sid=sid, facts=facts, period_s=facts.period_s,
                        deadline_s=facts.period_s, phase_s=0.0, kv_budget_tokens=budget,
                        token_rate=facts.tokens_per_tick/facts.period_s, start_t=t)
    s._depart_t = t + rng.exponential(mean_hold)
    return s


def cluster_run(name, G, policy, offered_factor, horizon_s=120.0, seed=0):
    facts = models.get(name)
    cost = load_cost(name)
    rng = np.random.default_rng(seed)
    # heterogeneous budgets across 3 SLA classes -> packing/fragmentation matters
    budget_classes = [max(512, facts.context_ceiling_tokens // c) for c in (16, 8, 4)]
    cfg = AdmissionConfig(hbm_kv_bytes=hbm_kv_bytes(), frame_budget_s=facts.period_s,
                          safety=0.90, mode="worst_case")
    gpus = [IncrementalAdmissionController(cost, cfg) for _ in range(G)]
    active = [[] for _ in range(G)]   # sessions per GPU (for departures)

    # single-GPU capacity (mid budget) to scale offered load
    mid = budget_classes[1]
    s0 = make_session(0, facts, mid, 0, rng, 1)
    denom = cost.batch_per_session + cost.batch_alpha * mid
    cap1 = max(4, int((facts.period_s*1000*0.9 - cost.batch_base)/max(denom, 1e-9)))
    mean_hold = min(60.0, facts.fill_time_s*0.4)
    arr_rate = offered_factor * G * cap1 / mean_hold

    period = facts.period_s
    n_frames = int(horizon_s / period)
    rr = 0
    n_arr = n_adm = 0
    for fi in range(n_frames):
        t = fi * period
        for g in range(G):    # departures
            keep = [s for s in active[g] if s._depart_t > t]
            for s in active[g]:
                if s._depart_t <= t:
                    gpus[g].depart(s)
            active[g] = keep
        n_new = rng.poisson(arr_rate * period)
        for _ in range(n_new):
            budget = budget_classes[rng.integers(0, 3)]
            s = make_session(n_arr, facts, budget, t, rng, mean_hold)
            n_arr += 1
            # placement order
            if policy == "random":
                order = list(rng.permutation(G))
            elif policy == "round_robin":
                order = [(rr + i) % G for i in range(G)]; rr = (rr + 1) % G
            elif policy == "first_fit":
                order = list(range(G))
            elif policy == "best_fit":   # most spare timing headroom first
                order = sorted(range(G), key=lambda g: gpus[g].sum_B_tokens)
            else:
                raise ValueError(policy)
            placed = False
            for g in order:
                if gpus[g].admit(s):
                    active[g].append(s); placed = True; n_adm += 1; break
            # not placed -> blocked
    served = sum(len(a) for a in active)
    loads = [gpus[g].sum_B_tokens for g in range(G)]
    return dict(policy=policy, G=G, offered=offered_factor, served=served,
                blocking=1 - n_adm / max(1, n_arr),
                balance=jain_index([l + 1 for l in loads]), cap1=cap1)


def large_regime_placement(G=8, seed=0):
    """Large-regime (projected) placement: sessions whose KV is a large fraction of a
    GPU's HBM -> few per GPU -> bin-packing fragmentation, where best-fit beats
    random. 80 GiB GPUs; heterogeneous session footprints 10/25/40 GiB."""
    rng = np.random.default_rng(seed)
    hbm = 80.0
    foot_classes = [10.0, 25.0, 40.0]   # GiB per session (projected large-model KV)
    policies = ["random", "round_robin", "first_fit", "best_fit"]
    out = {}
    n_arr = 600
    arrivals = [foot_classes[rng.integers(0, 3)] for _ in range(n_arr)]
    for policy in policies:
        used = [0.0] * G
        rr = 0
        admitted = 0
        rng2 = np.random.default_rng(seed + 1)
        for foot in arrivals:
            if policy == "random":
                order = list(rng2.permutation(G))
            elif policy == "round_robin":
                order = [(rr + i) % G for i in range(G)]; rr = (rr + 1) % G
            elif policy == "first_fit":
                order = list(range(G))
            else:  # best_fit: tightest GPU that still fits (minimise leftover)
                order = sorted(range(G), key=lambda g: -used[g])
            for g in order:
                if used[g] + foot <= hbm:
                    used[g] += foot; admitted += 1; break
        out[policy] = dict(admitted=admitted, blocking=1 - admitted / n_arr,
                           util=sum(used) / (G * hbm))
    return out


def run(name="qwen3-omni"):
    os.makedirs(OUT, exist_ok=True)
    policies = ["random", "round_robin", "first_fit", "best_fit"]
    # (1) policy comparison at G=8 under overload
    G = 8
    pol_rows = [cluster_run(name, G, p, offered_factor=1.3) for p in policies]
    print(f"[{name}] G={G} placement (offered 1.3x cluster cap):")
    for r in pol_rows:
        print(f"    {r['policy']:12s} served={r['served']:5d} blocking={r['blocking']:.3f} "
              f"balance={r['balance']:.3f}")

    # (2) scaling vs G for best_fit (near-linear?) at moderate load
    Gs = [1, 2, 4, 8, 16]
    scale = [cluster_run(name, g, "best_fit", offered_factor=0.9) for g in Gs]
    base = scale[0]["served"]
    print(f"[{name}] best-fit scaling (served vs G):")
    for r in scale:
        eff = r["served"] / (base * r["G"]) if base else 0
        print(f"    G={r['G']:3d} served={r['served']:6d} efficiency={eff:.2f}")

    # (3) large-regime placement: fragmentation makes best-fit beat random
    lr = large_regime_placement(G=8)
    print(f"[{name}] LARGE-regime placement (8x80GiB GPUs, 10/25/40 GiB sessions):")
    for p, r in lr.items():
        print(f"    {p:12s} admitted={r['admitted']:4d} blocking={r['blocking']:.3f} "
              f"util={r['util']:.3f}")

    # (4) migration cost vs context length: pinned KV makes mid-session migration
    # prohibitive once the KV is large (the §1.3 argument applied to rebalancing).
    facts = models.get(name)
    print(f"[{name}] migration cost (move KV across interconnect vs {facts.period_s*1000:.0f} ms frame):")
    for ctx in (1024, 32768, 262144, 1_000_000):
        kv_bytes = ctx * facts.kv_bytes_per_token
        for link, bw_gbs in (("PCIe5", 64.0), ("NVLink", 600.0)):
            move_ms = kv_bytes / (bw_gbs * 1e9) * 1000.0
            flag = "BLOWS" if move_ms > facts.period_s * 1000 else "fits"
            print(f"    ctx={ctx:>9d} {link:7s}: {kv_bytes/2**30:6.2f} GiB -> {move_ms:8.1f} ms ({flag})")

    # plot scaling + policy
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    ax1.bar([r["policy"] for r in pol_rows], [r["served"] for r in pol_rows],
            color=["#7f7f7f", "#1f77b4", "#ff7f0e", "#2ca02c"])
    ax1.set_ylabel("cluster served sessions"); ax1.set_title(f"{name}: placement policy (G={G})")
    ax1.tick_params(axis="x", rotation=20)
    ax2.plot(Gs, [r["served"] for r in scale], "o-", color="#2ca02c", label="best-fit")
    ax2.plot(Gs, [base * g for g in Gs], "k--", alpha=0.5, label="ideal linear")
    ax2.set_xlabel("GPUs (G)"); ax2.set_ylabel("cluster served"); ax2.set_title(f"{name}: scaling")
    ax2.legend(); ax2.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{name}_multigpu.png"), dpi=120)
    plt.close(fig)

    res = dict(model=name, policies=pol_rows, scaling=scale)
    with open(os.path.join(OUT, "multigpu_summary.json"), "w") as fh:
        json.dump(res, fh, indent=2)
    return res


if __name__ == "__main__":
    run()
