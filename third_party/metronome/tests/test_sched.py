"""Tests for the scheduling/admission additions (tasks C, F)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metronome import models
from metronome.cost_model import CostModel
from metronome.session import PeriodicSession
from metronome.admission import (AdmissionController, IncrementalAdmissionController,
                                 AdmissionConfig)


def toy():
    return CostModel(model="t", device="d", c_fixed=3, alpha=0.002,
                     batch_base=3, batch_per_session=0.2, batch_alpha=0.002,
                     tail_factor=1.0, kv_bytes_per_token=models.MOSHI.kv_bytes_per_token)


def sess(facts, budget, length=0, sid=0):
    return PeriodicSession(sid=sid, facts=facts, period_s=facts.period_s,
                           deadline_s=facts.period_s, phase_s=0.0,
                           kv_budget_tokens=budget,
                           token_rate=facts.tokens_per_tick/facts.period_s,
                           length_tokens=length)


def test_lookahead_zero_horizon_uses_current_length():
    cm = toy()
    ac = AdmissionController(cm, AdmissionConfig(80*2**30, 1.0, 0.9, mode="lookahead",
                                                 guard_horizon_s=0.0))
    s = sess(models.MOSHI, budget=4096, length=500)
    # zero horizon -> projects to current length (500), not the budget
    assert ac._projected_lengths([s])[0] == 500


def test_lookahead_large_horizon_reaches_plateau():
    cm = toy()
    # huge horizon -> every session projects to its budget (== worst case)
    ac = AdmissionController(cm, AdmissionConfig(80*2**30, 1.0, 0.9, mode="lookahead",
                                                 guard_horizon_s=1e9))
    s = sess(models.MOSHI, budget=4096, length=10)
    assert ac._projected_lengths([s])[0] == 4096


def test_incremental_matches_full_worstcase():
    cm = toy()
    cfg = AdmissionConfig(80*2**30, models.MOSHI.period_s, 0.9, mode="worst_case")
    full = AdmissionController(cm, cfg)
    inc = IncrementalAdmissionController(cm, cfg)
    pop = []
    for i in range(500):
        s = sess(models.MOSHI, budget=2048, sid=i)
        assert full.try_admit(pop, s).admit == inc.would_admit(s)
        if inc.would_admit(s):
            pop.append(s); inc.admit(s)
    # the incremental running sums are consistent
    assert inc.n == len(pop)
    assert inc.sum_B_tokens == sum(s.kv_budget_tokens for s in pop)


def test_incremental_depart_frees_capacity():
    cm = toy()
    cfg = AdmissionConfig(80*2**30, models.MOSHI.period_s, 0.9, mode="worst_case")
    inc = IncrementalAdmissionController(cm, cfg)
    sessions = [sess(models.MOSHI, budget=2048, sid=i) for i in range(100)]
    for s in sessions:
        inc.admit(s)
    n_before = inc.n
    # fill to rejection
    while inc.admit(sess(models.MOSHI, budget=2048, sid=999)):
        pass
    full_n = inc.n
    cand = sess(models.MOSHI, budget=2048, sid=1000)
    assert not inc.would_admit(cand)        # full
    inc.depart(sessions[0])                  # free one
    assert inc.would_admit(cand)             # now fits


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
