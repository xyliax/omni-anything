"""Tier-2 #1: control-plane overhead. The admission test + periodic scheduler run on the
CPU, OFF the GPU critical path. We time them at realistic session counts and show each
decision costs microseconds — a negligible fraction of the frame budget (so the mechanism
never eats into the deadline)."""
import json
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metronome import models
from metronome.cost_model import CostModel
from metronome.admission import AdmissionController, AdmissionConfig
from metronome.session import PeriodicSession
from experiments._common import load_cost, hbm_kv_bytes


def proto_for(name, facts, kv_budget):
    return PeriodicSession(sid=0, facts=facts, period_s=facts.period_s,
                           deadline_s=facts.period_s, phase_s=0.0,
                           kv_budget_tokens=kv_budget,
                           token_rate=facts.tokens_per_tick / facts.period_s)


def timeit(fn, reps):
    for _ in range(50):
        fn()
    samples = []
    for _ in range(reps):
        t0 = time.perf_counter(); fn(); samples.append((time.perf_counter() - t0) * 1e6)  # µs
    return dict(mean_us=round(statistics.mean(samples), 2),
                p99_us=round(sorted(samples)[int(0.99 * len(samples))], 2))


def main():
    reps = 2000
    out = {}
    for name in ["moshi", "minicpm-o", "qwen3-omni"]:
        try:
            facts = models.get(name); cost = load_cost(name)
        except Exception as e:
            print(f"[{name}] skip {e}"); continue
        window = max(512, facts.context_ceiling_tokens // 4)
        ac = AdmissionController(cost, AdmissionConfig(hbm_kv_bytes(), facts.period_s, 0.90,
                                                       mode="worst_case"))
        proto = proto_for(name, facts, window)
        cap = ac.predict_capacity(proto)
        budget_us = facts.period_s * 1e6
        current = [proto_for(name, facts, window) for _ in range(cap)]
        for s in current:
            s.sid = id(s) % 100000
        t_cap = timeit(lambda: ac.predict_capacity(proto), 200)              # full capacity solve
        t_adm = timeit(lambda: ac.try_admit(current, proto), reps)           # one arrival decision
        t_feas = timeit(lambda: ac.feasible(current), reps)                  # schedulability test @cap
        out[name] = dict(capacity=cap, frame_budget_us=round(budget_us, 0),
                         predict_capacity=t_cap, try_admit=t_adm, feasible_at_cap=t_feas,
                         admit_pct_of_budget=round(100 * t_adm["mean_us"] / budget_us, 4))
        print(f"[{name}] cap={cap} budget={budget_us/1000:.0f}ms | predict_capacity "
              f"{t_cap['mean_us']}µs | try_admit {t_adm['mean_us']}µs (p99 {t_adm['p99_us']}) "
              f"= {out[name]['admit_pct_of_budget']}% of budget | feasible@{cap} "
              f"{t_feas['mean_us']}µs", flush=True)
    os.makedirs("results/overhead", exist_ok=True)
    json.dump(out, open("results/overhead/overhead.json", "w"), indent=2)
    print("\nsaved results/overhead/overhead.json")


if __name__ == "__main__":
    main()
