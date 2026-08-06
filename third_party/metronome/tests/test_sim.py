"""Integration tests for the calibrated simulator and the end-to-end policies.

These use a small synthetic CostModel so they run fast and deterministically on CPU
and assert the *qualitative* invariants the paper relies on.
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metronome import models
from metronome.cost_model import CostModel
from sim.simulator import Simulator, SimConfig, preset
from bench.generator import WorkloadConfig, make_population
from bench.metrics import mscs_served


def toy_cost():
    # base 5ms shared, 0.05ms/session, 0.002ms/token KV read
    return CostModel(model="toy", device="cpu", c_fixed=5, alpha=0.002, tail_factor=1.0,
                     batch_base=5.0,
                     batch_per_session=0.05, batch_alpha=0.002,
                     kv_bytes_per_token=models.MOSHI.kv_bytes_per_token)


def mscs_curve(cfg_fn, facts, growth, window, n_frames=120, n_max=512):
    out = []
    for n in (1,2,4,8,16,32,64,96,128,192,256,384,512):
        if n > n_max:
            break
        cfg = cfg_fn()
        wl = WorkloadConfig(facts=facts, kv_budget_tokens=growth,
                            mean_session_s=facts.fill_time_s*0.5, seed=0)
        r = Simulator(cfg).run_static(make_population(wl, n), n_frames)
        out.append((n, r.admitted, r.metrics.miss_rate))
    return out


def test_metronome_beats_b1_on_mscs():
    cost = toy_cost()
    facts = models.MOSHI
    hbm = 80 * 2**30
    ceiling = facts.context_ceiling_tokens
    window = ceiling // 4

    b1 = mscs_curve(lambda: SimConfig(cost=cost, frame_budget_s=facts.period_s,
                    hbm_kv_bytes=hbm, admission=False, memory_admission=True,
                    ordering="fifo", eviction="full", degradation=False, silence=False),
                    facts, ceiling, window)
    m = mscs_curve(lambda: SimConfig(cost=cost, frame_budget_s=facts.period_s,
                   hbm_kv_bytes=hbm, admission=True, ordering="edf",
                   eviction="sink_window", degradation=False, silence=False,
                   kv_budget_tokens=window), facts, window, window)
    assert mscs_served(m) > mscs_served(b1)


def test_admission_holds_slo_under_overload():
    cost = toy_cost()
    facts = models.MOSHI
    hbm = 80 * 2**30
    window = facts.context_ceiling_tokens // 4
    # offer far more than capacity; admission must keep miss ~0 among admitted
    cfg = SimConfig(cost=cost, frame_budget_s=facts.period_s, hbm_kv_bytes=hbm,
                    admission=True, ordering="edf", eviction="sink_window",
                    degradation=False, silence=False, kv_budget_tokens=window)
    wl = WorkloadConfig(facts=facts, kv_budget_tokens=window,
                        mean_session_s=facts.fill_time_s*0.5, seed=0)
    r = Simulator(cfg).run_static(make_population(wl, 2000), 120)
    assert r.rejected > 0           # excess rejected
    assert r.metrics.miss_rate <= 0.001


def test_no_admission_misses_under_overload():
    cost = toy_cost()
    facts = models.MOSHI
    hbm = 80 * 2**30
    window = facts.context_ceiling_tokens // 4
    cfg = SimConfig(cost=cost, frame_budget_s=facts.period_s, hbm_kv_bytes=hbm,
                    admission=False, memory_admission=True, ordering="fifo",
                    eviction="full", degradation=False, silence=False)
    wl = WorkloadConfig(facts=facts, kv_budget_tokens=facts.context_ceiling_tokens,
                        mean_session_s=facts.fill_time_s*0.5, seed=0)
    r = Simulator(cfg).run_static(make_population(wl, 2000), 120)
    assert r.metrics.miss_rate > 0.001   # greedy misses under overload


def test_memory_admission_caps_population():
    cost = toy_cost()
    facts = models.MOSHI
    small_hbm = 4 * 2**30   # only a few full-KV sessions fit
    cfg = SimConfig(cost=cost, frame_budget_s=facts.period_s, hbm_kv_bytes=small_hbm,
                    admission=False, memory_admission=True, ordering="fifo",
                    eviction="full", degradation=False, silence=False)
    wl = WorkloadConfig(facts=facts, kv_budget_tokens=facts.context_ceiling_tokens,
                        mean_session_s=facts.fill_time_s*0.5, seed=0)
    r = Simulator(cfg).run_static(make_population(wl, 1000), 30)
    per_session = facts.context_ceiling_tokens * facts.kv_bytes_per_token
    assert r.admitted <= small_hbm / per_session + 1
    assert r.rejected > 0


def test_degradation_prevents_misses_at_cost():
    cost = toy_cost()
    facts = models.MOSHI
    hbm = 80 * 2**30
    window = facts.context_ceiling_tokens // 4
    base = dict(cost=cost, frame_budget_s=facts.period_s, hbm_kv_bytes=hbm,
                admission=False, memory_admission=True, ordering="edf",
                eviction="sink_window", silence=False, kv_budget_tokens=window)
    wl = WorkloadConfig(facts=facts, kv_budget_tokens=window,
                        mean_session_s=facts.fill_time_s*0.5, seed=0)
    no_degr = Simulator(SimConfig(**base, degradation=False)).run_static(
        make_population(wl, 400), 120)
    with_degr = Simulator(SimConfig(**base, degradation=True)).run_static(
        make_population(wl, 400), 120)
    # degradation lowers miss-rate (or matches) — it is a safety net
    assert with_degr.metrics.miss_rate <= no_degr.metrics.miss_rate + 1e-9


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
