"""Unit tests for the Metronome core (run with: python3 -m pytest tests/ -q).

These cover the scheduling/admission/KV logic that does not need a GPU. The GPU
kernel and cost-model *fit* are validated separately (experiments/validate_sim.py).
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metronome import models
from metronome.cost_model import CostModel, fit_single, fit_batch, _fit_linear
from metronome.session import PeriodicSession, DegradeLevel
from metronome.admission import AdmissionController, AdmissionConfig
from metronome.scheduler import TickScheduler
from metronome.kv_manager import EvictionPolicy, quality_proxy, make_policy, POLICIES


# ---- models ----------------------------------------------------------------
def test_kv_bytes_per_token_matches_published():
    # MiniCPM-o GQA 36L, 8 KV heads, d=128, fp16 -> 144 KiB/token (RESEARCH_PLAN §6.1)
    assert abs(models.MINICPM_O.kv_bytes_per_token_kib - 144.0) < 1e-6
    # Moshi MHA 32L, 32 heads, d=128, fp16 -> 512 KiB/token (~1 MiB/frame)
    assert abs(models.MOSHI.kv_bytes_per_token_kib - 512.0) < 1e-6


def test_fill_time_ordering():
    # Moshi (small ceiling, low rate) fills in minutes; sanity on saturating ramp.
    assert models.MOSHI.fill_time_s > 60
    assert models.MOSHI.context_ceiling_bytes < models.MINICPM_O.context_ceiling_bytes


# ---- cost model ------------------------------------------------------------
def test_linear_fit_recovers_params():
    x = np.arange(0, 5000, 250)
    y = 2.0 + 0.003 * x
    f = _fit_linear(x, y)
    assert abs(f.intercept - 2.0) < 1e-6
    assert abs(f.slope - 0.003) < 1e-9
    assert f.r2 > 0.999999


def test_cost_model_batch_additive_in_total_kv():
    cm = CostModel(model="t", device="d", c_fixed=3, alpha=0.002,
                   batch_base=3, batch_per_session=0.1, batch_alpha=0.002,
                   tail_factor=1.0)
    # same total KV, different distribution -> same predicted cost (read-once model)
    a = cm.predict_batch([1000, 1000])
    b = cm.predict_batch([500, 1500])
    assert abs(a - b) < 1e-9
    # more sessions at same total costs more (per-session term)
    c = cm.predict_batch([500, 500, 500, 500])
    assert c > a


# ---- admission -------------------------------------------------------------
def _proto(facts, budget, period=None):
    period = period or facts.period_s
    return PeriodicSession(sid=0, facts=facts, period_s=period, deadline_s=period,
                           phase_s=0.0, kv_budget_tokens=budget,
                           token_rate=facts.tokens_per_tick/facts.period_s)


def test_admission_monotone_in_n():
    cm = CostModel(model="t", device="d", c_fixed=3, alpha=0.002,
                   batch_base=3, batch_per_session=0.5, batch_alpha=0.002, tail_factor=1.0,
                   kv_bytes_per_token=144*1024)
    ac = AdmissionController(cm, AdmissionConfig(hbm_kv_bytes=80*2**30,
                                                 frame_budget_s=1.0, safety=0.9))
    proto = _proto(models.MINICPM_O, budget=2000)
    cap = ac.predict_capacity(proto)
    assert cap >= 1
    # feasible at cap, infeasible at cap+1 (monotone boundary)
    assert ac.feasible([proto]*cap).admit
    assert not ac.feasible([proto]*(cap+1)).admit


def test_admission_memory_bound_binds():
    cm = CostModel(model="t", device="d", c_fixed=0.1, alpha=1e-6,
                   batch_base=0.1, batch_per_session=0.001, batch_alpha=1e-6, tail_factor=1.0,
                   kv_bytes_per_token=512*1024)
    # tiny HBM => memory binds before timing
    ac = AdmissionController(cm, AdmissionConfig(hbm_kv_bytes=2*2**30,
                                                 frame_budget_s=1.0, safety=0.9))
    proto = _proto(models.MOSHI, budget=4096)
    res = ac.feasible([proto]*100)
    assert not res.admit and "memory" in res.reason


def test_worst_case_admits_no_more_than_age_aware():
    cm = CostModel(model="t", device="d", c_fixed=3, alpha=0.002,
                   batch_base=3, batch_per_session=0.3, batch_alpha=0.002, tail_factor=1.0,
                   kv_bytes_per_token=144*1024)
    proto = _proto(models.MINICPM_O, budget=4000)
    wc = AdmissionController(cm, AdmissionConfig(80*2**30, 1.0, 0.9, mode="worst_case"))
    aa = AdmissionController(cm, AdmissionConfig(80*2**30, 1.0, 0.9, mode="age_aware"))
    assert wc.predict_capacity(proto) <= aa.predict_capacity(proto)


# ---- scheduler -------------------------------------------------------------
def test_edf_vs_fifo_ordering():
    cm_cost = lambda lengths: 0.0
    sched = TickScheduler(cost_fn=cm_cost, frame_budget_s=1.0, ordering="edf",
                          use_silence=False, use_degradation=False)
    a = _proto(models.MOSHI, 4096); a.sid = 1; a.phase_s = 0.5
    b = _proto(models.MOSHI, 4096); b.sid = 2; b.phase_s = 0.1
    fr = sched.run_frame(0, 0.0, [a, b])
    # b has earlier deadline (smaller phase) -> executed first under EDF
    assert fr.executed_sids[0] == 2


def test_edf_orders_by_absolute_deadline():
    # tighter relative deadline -> earlier absolute deadline -> scheduled first
    cost_fn = lambda lengths: 0.0
    sched = TickScheduler(cost_fn=cost_fn, frame_budget_s=1.0, ordering="edf",
                          use_silence=False, use_degradation=False)
    loose = _proto(models.MOSHI, 4096); loose.sid = 1; loose.phase_s = 0.0
    loose.deadline_s = 1.0
    tight = _proto(models.MOSHI, 4096); tight.sid = 2; tight.phase_s = 0.0
    tight.deadline_s = 0.5
    fr = sched.run_frame(0, 0.0, [loose, tight])
    assert fr.executed_sids[0] == 2   # tight deadline first


def test_absolute_deadline_includes_relative():
    s = _proto(models.MOSHI, 4096)
    s.deadline_s = 0.04
    s.phase_s = 0.0
    assert abs(s.absolute_deadline(0) - 0.04) < 1e-9
    assert abs(s.absolute_deadline(1) - (s.period_s + 0.04)) < 1e-9


def test_cost_model_json_roundtrip(tmp_path):
    cm = CostModel(model="m", device="d", c_fixed=2, alpha=0.002, tail_factor=1.0, kv_bytes_per_token=144*1024)
    p = tmp_path / "cm.json"
    cm.to_json(str(p))
    cm2 = CostModel.from_json(str(p))
    assert cm2.alpha == cm.alpha and cm2.model == "m"


def test_degradation_reduces_cost_to_fit():
    # cost grows with total length; budget forces degradation
    def cost_fn(lengths):
        return 0.001 * sum(lengths)
    sched = TickScheduler(cost_fn=cost_fn, frame_budget_s=0.1, ordering="edf",
                          use_silence=False, use_degradation=True)
    sessions = [_proto(models.MOSHI, 4096) for _ in range(50)]
    for i, s in enumerate(sessions):
        s.sid = i
        s.length_tokens = 4096
    fr = sched.run_frame(0, 0.0, sessions)
    assert fr.batch_ms <= fr.budget_ms * 1.01 or fr.n_missed > 0
    assert fr.n_degraded > 0


def test_silence_skips_nontalk_ticks():
    def cost_fn(lengths):
        return 0.0
    sched = TickScheduler(cost_fn=cost_fn, frame_budget_s=1.0, ordering="edf",
                          use_silence=True, use_degradation=False)
    rng = np.random.default_rng(0)
    sessions = [_proto(models.MINICPM_O, 4096) for _ in range(100)]
    for i, s in enumerate(sessions):
        s.sid = i
        s.talk_prob = 0.5
    fr = sched.run_frame(0, 0.0, sessions, rng=rng)
    assert fr.n_skipped_silence > 0
    assert fr.n_executed + fr.n_skipped_silence == 100


# ---- KV manager ------------------------------------------------------------
def test_eviction_resident_length_bounded_by_budget():
    for name in POLICIES:
        pol = make_policy(name, budget=1000)
        assert pol.resident_length(full_length=100000, budget=1000) <= 1000


def test_quality_proxy_ordering_at_equal_budget():
    # full >= h2o >= sink_window >= sliding at equal budget (published behaviour)
    full_len, budget = 8000, 1000
    q_full = quality_proxy(make_policy("full", budget), full_len, budget, seed=1)
    q_h2o = quality_proxy(make_policy("h2o", budget), full_len, budget, seed=1)
    q_sw = quality_proxy(make_policy("sink_window", budget), full_len, budget, seed=1)
    q_sl = quality_proxy(make_policy("sliding", budget), full_len, budget, seed=1)
    assert q_full >= q_h2o - 1e-9
    assert q_h2o >= q_sw - 1e-9
    assert q_sw >= q_sl - 1e-9
    assert 0.0 <= q_sl <= 1.0


def test_quality_increases_with_budget():
    full_len = 16000
    qs = [quality_proxy(make_policy("sink_window", b), full_len, b, seed=2)
          for b in (256, 1024, 4096, 8192)]
    assert all(qs[i] <= qs[i+1] + 1e-9 for i in range(len(qs)-1))


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
