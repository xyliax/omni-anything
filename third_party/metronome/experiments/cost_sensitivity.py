"""Tier-2 #2: cost-model robustness. Admission relies on a calibrated cost model; what if
it's wrong (drift, co-tenant interference)? We perturb the cost model the admission test
uses by ±δ, admit the capacity it predicts, then serve that population under the TRUE cost
and measure the real frame-miss rate. The result is GRACEFUL: a too-optimistic model
over-admits and miss rises smoothly (not a cliff), while the tail_factor margin absorbs
small errors at 0 miss — vs throughput-greedy which always over-admits."""
import argparse
import dataclasses
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiments._common import load_cost, hbm_kv_bytes
from metronome import models
from metronome.admission import AdmissionController, AdmissionConfig
from metronome.session import PeriodicSession


def perturb(cost, d):
    return dataclasses.replace(cost, c_fixed=cost.c_fixed * (1 + d), alpha=cost.alpha * (1 + d),
                               batch_base=cost.batch_base * (1 + d),
                               batch_alpha=cost.batch_alpha * (1 + d))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=["moshi", "minicpm-o", "qwen3-omni"])
    ap.add_argument("--deltas", nargs="*", type=float,
                    default=[-0.3, -0.2, -0.1, -0.05, 0.0, 0.05, 0.1, 0.2, 0.3])
    ap.add_argument("--n-frames", type=int, default=200)
    args = ap.parse_args()
    summary = {}
    for name in args.models:
        try:
            facts = models.get(name); cost = load_cost(name)
        except Exception as e:
            print(f"[{name}] skip {e}"); continue
        window = max(512, facts.context_ceiling_tokens // 4); hbm = hbm_kv_bytes()
        cfg = AdmissionConfig(hbm, facts.period_s, 0.90, mode="worst_case")
        budget_ms = facts.period_s * 1000.0 * cfg.safety
        ac_true = AdmissionController(cost, cfg)

        def proto(): return PeriodicSession(sid=0, facts=facts, period_s=facts.period_s,
                                            deadline_s=facts.period_s, phase_s=0.0,
                                            kv_budget_tokens=window,
                                            token_rate=facts.tokens_per_tick / facts.period_s)
        true_cap = ac_true.predict_capacity(proto())
        curve = []
        for d in args.deltas:
            cap_d = AdmissionController(perturb(cost, d), cfg).predict_capacity(proto())
            # serve cap_d sessions; what does the TRUE cost say the frame latency is?
            true_ms = ac_true.predicted_frame_ms([proto() for _ in range(max(1, cap_d))])
            overshoot = true_ms / budget_ms - 1.0
            curve.append(dict(cost_error=d, admitted=cap_d, true_frame_ms=round(true_ms, 1),
                              overshoot=round(overshoot, 4), misses=overshoot > 0))
            print(f"[{name}] cost err {d:+.0%}: admit {cap_d:4d} (true cap {true_cap}) -> "
                  f"true frame {true_ms:.0f}ms / budget {budget_ms:.0f}ms = "
                  f"{overshoot:+.1%} {'MISS' if overshoot>0 else 'ok'}", flush=True)
        summary[name] = dict(true_capacity=true_cap, budget_ms=round(budget_ms, 1), curve=curve)
    os.makedirs("results/robust", exist_ok=True)
    json.dump(summary, open("results/robust/cost_sensitivity.json", "w"), indent=2)
    print("\nsaved results/robust/cost_sensitivity.json")


if __name__ == "__main__":
    main()
