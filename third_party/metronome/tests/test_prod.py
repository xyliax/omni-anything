"""Tests for the production metrics and the open-system simulator."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metronome import models
from metronome.cost_model import CostModel
from bench.metrics import (consecutive_run_lengths, jain_index,
                           blocking_probability, ProductionReport)
from sim.open_system import OpenSystemSimulator, OpenConfig, recovery_time_s


def toy_cost():
    return CostModel(model="toy", device="cpu", c_fixed=5, alpha=0.002, tail_factor=1.0,
                     batch_base=5.0, batch_per_session=0.05, batch_alpha=0.002,
                     kv_bytes_per_token=models.MOSHI.kv_bytes_per_token)


# ---- production metrics -----------------------------------------------------
def test_consecutive_runs():
    assert consecutive_run_lengths([0,0,1,1,1,0,1]) == [3, 1]
    assert consecutive_run_lengths([1,1]) == [2]
    assert consecutive_run_lengths([0,0,0]) == []
    assert consecutive_run_lengths([]) == []


def test_jain_index_bounds():
    assert abs(jain_index([1,1,1,1]) - 1.0) < 1e-9          # perfectly equal
    assert abs(jain_index([1,0,0,0]) - 0.25) < 1e-9          # 1/n for one-hot
    assert 0.0 <= jain_index([0.3,0.9,0.1]) <= 1.0


def test_blocking_probability():
    assert blocking_probability(8, 10) == pytest.approx(0.2)
    assert blocking_probability(0, 0) == 0.0


def test_production_report_summary():
    rep = ProductionReport()
    rep.per_session_miss = {0: [False, True, True], 1: [False, False, False]}
    rep.per_session_quality = {0: [1.0, 0.5, 0.5], 1: [1.0, 1.0, 1.0]}
    rep.n_arrivals, rep.n_admitted = 4, 2
    s = rep.summary(quality_floor=0.7)
    assert s["miss_rate"] == pytest.approx(2/6)
    assert s["blocking"] == pytest.approx(0.5)
    assert s["miss_runs"]["max"] == 2
    # session 1 is perfect, session 0 misses 2/3 -> not perfectly fair
    assert s["fairness"] < 1.0
    # goodput: on-time AND quality>=0.7 -> session0 frame0 + session1 all 3 = 4/6
    assert rep.goodput_frac(quality_floor=0.7) == pytest.approx(4/6)


# ---- open-system simulator --------------------------------------------------
def _cfg(**kw):
    f = models.MOSHI
    d = dict(cost=toy_cost(), facts=f, hbm_kv_bytes=80*2**30, kv_budget_tokens=1024,
             arrival_rate_hz=3.0, mean_holding_s=20.0, seed=0)
    d.update(kw)
    return OpenConfig(**d)


def test_open_admission_blocks_under_overload():
    # heavy arrival rate -> admission must block some and hold miss ~0
    r = OpenSystemSimulator(_cfg(arrival_rate_hz=20.0, admission=True)).run(40.0, warmup_s=5.0)
    assert r.n_blocked > 0
    assert r.report.miss_rate <= 0.001


def test_open_greedy_misses_under_overload():
    r = OpenSystemSimulator(_cfg(arrival_rate_hz=40.0, admission=False,
                                 memory_admission=True, ordering="fifo",
                                 eviction="full", degradation=False, silence=False)
                            ).run(40.0, warmup_s=5.0)
    assert r.report.miss_rate > 0.001


def test_open_departures_free_capacity():
    # short holding -> sessions depart -> active stays bounded, churn happens
    r = OpenSystemSimulator(_cfg(arrival_rate_hz=10.0, mean_holding_s=5.0, admission=True)
                            ).run(60.0, warmup_s=5.0)
    assert r.n_arrivals > r.n_admitted or r.n_admitted > 0
    assert max(r.per_frame_active) < r.n_admitted  # not all alive at once (churn)


def test_adaptive_budget_serves_more_than_fixed_large_under_load():
    f = models.MOSHI
    ceiling = f.context_ceiling_tokens
    common = dict(cost=toy_cost(), facts=f, hbm_kv_bytes=80*2**30,
                  arrival_rate_hz=30.0, mean_holding_s=20.0, admission=True,
                  admission_mode="worst_case", eviction="sink_window", seed=0)
    large = OpenSystemSimulator(OpenConfig(kv_budget_tokens=ceiling//2,
                                adaptive_budget=False, **common)).run(50.0, warmup_s=10.0)
    adaptive = OpenSystemSimulator(OpenConfig(kv_budget_tokens=ceiling//2,
                                   adaptive_budget=True, min_budget_tokens=ceiling//16,
                                   **common)).run(50.0, warmup_s=10.0)
    a_served = np.mean(adaptive.per_frame_active)
    l_served = np.mean(large.per_frame_active)
    assert a_served >= l_served            # adaptive serves at least as many
    assert adaptive.report.miss_rate <= 0.001


def test_recovery_time_monotone():
    series = [0.0]*10 + [0.5]*5 + [0.0]*10
    assert recovery_time_s(series, 0.08, slo=0.001) > 0
    assert recovery_time_s([0.0]*20, 0.08) == 0.0


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
