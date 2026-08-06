"""GAP #3: is admission TIGHT, or does its worst-case (plateau) schedulability test leave
capacity on the table? We compare the admission-PREDICTED capacity C against the TRUE
max-feasible concurrency measured on the real engine (largest N whose p99 per-frame decode
still meets the budget). tightness = C / true_max: =1 is perfectly tight, <1 is conservative
(safe but wasting capacity), >1 would be unsafe (admits beyond feasible)."""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")

import numpy as np
from bench.gpu_probe import wait_for_window
from metronome import models
from metronome.engine import ServingEngine
from metronome.admission import AdmissionController, AdmissionConfig
from metronome.session import PeriodicSession
from experiments._common import load_cost, hbm_kv_bytes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=["moshi", "qwen3-omni", "minicpm-o"])
    ap.add_argument("--n-frames", type=int, default=20)
    ap.add_argument("--max-util", type=int, default=60)
    args = ap.parse_args()
    summary = {}
    for name in args.models:
        try:
            facts = models.get(name); cost = load_cost(name)
        except Exception as e:
            print(f"[{name}] skip {e}"); continue
        window = max(512, facts.context_ceiling_tokens // 4)
        budget_ms = facts.period_s * 1000.0
        ac = AdmissionController(cost, AdmissionConfig(hbm_kv_bytes(), facts.period_s, 0.90,
                                                       mode="worst_case"))
        proto = PeriodicSession(sid=0, facts=facts, period_s=facts.period_s, deadline_s=facts.period_s,
                                phase_s=0.0, kv_budget_tokens=window,
                                token_rate=facts.tokens_per_tick / facts.period_s)
        C = ac.predict_capacity(proto)
        wait_for_window(need_free_gib=3.0, max_util_pct=args.max_util, quiet=True, timeout_s=72000)
        # sweep N around C on the real engine; find largest N with p99 <= budget
        grid = sorted(set([int(C * f) for f in (0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5)] + [C]))
        grid = [n for n in grid if n >= 1]
        eng = ServingEngine(facts, max_sessions=max(grid) + 4, max_budget_tokens=window)
        eng.serve_cohort(min(8, max(grid)), n_frames=3, start_lengths=[window] * min(8, max(grid)), warmup=2)
        rows = []
        true_max = 1
        for N in grid:
            lats = eng.serve_cohort(N, n_frames=args.n_frames, start_lengths=[window] * N, warmup=2)
            p99 = float(np.percentile(lats, 99))
            ok = p99 <= budget_ms
            rows.append(dict(N=N, p99_ms=round(p99, 1), meets_budget=ok))
            if ok:
                true_max = max(true_max, N)
            print(f"  [{name}] N={N:4d}: p99={p99:.0f}ms {'<=' if ok else '>'} budget {budget_ms:.0f}ms",
                  flush=True)
        del eng
        import torch; torch.cuda.empty_cache()
        summary[name] = dict(predicted_capacity=C, true_max_feasible=true_max,
                             tightness=round(C / max(1, true_max), 3), budget_ms=round(budget_ms, 1),
                             curve=rows)
        print(f"[{name}] predicted C={C}, true max-feasible={true_max}, "
              f"tightness={summary[name]['tightness']} "
              f"({'safe+' if C<=true_max else 'UNSAFE '}{'conservative' if C<true_max else 'tight'})",
              flush=True)
    os.makedirs("results/tightness", exist_ok=True)
    json.dump(summary, open("results/tightness/admission_tightness.json", "w"), indent=2)
    print("\nsaved results/tightness/admission_tightness.json")


if __name__ == "__main__":
    main()
