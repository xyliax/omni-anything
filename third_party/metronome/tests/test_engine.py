"""Smoke tests for the real serving engine (GPU + flash_attn required)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

torch = pytest.importorskip("torch")
if not torch.cuda.is_available():
    pytest.skip("engine needs a CUDA GPU", allow_module_level=True)
pytest.importorskip("flash_attn")

from metronome import models
from metronome.engine import ServingEngine


def test_engine_runs_and_latency_grows_with_concurrency():
    eng = ServingEngine(models.MOSHI, max_sessions=16, max_budget_tokens=256)
    lat_small = eng.serve_cohort(2, n_frames=6, start_lengths=[256, 256], grow=False, warmup=3)
    lat_big = eng.serve_cohort(16, n_frames=6, start_lengths=[256]*16, grow=False, warmup=3)
    import numpy as np
    assert np.median(lat_small) > 0
    # more concurrent sessions at the same context -> at least as much work
    assert np.median(lat_big) >= np.median(lat_small) * 0.9


def test_engine_latency_grows_with_context():
    eng = ServingEngine(models.MOSHI, max_sessions=8, max_budget_tokens=1024)
    import numpy as np
    short = np.median(eng.serve_cohort(4, n_frames=6, start_lengths=[16]*4, grow=False, warmup=3))
    long = np.median(eng.serve_cohort(4, n_frames=6, start_lengths=[1024]*4, grow=False, warmup=3))
    assert long > short      # longer resident KV -> more attention-read time


def test_step_active_handles_dynamic_set():
    eng = ServingEngine(models.MOSHI, max_sessions=8, max_budget_tokens=256)
    eng.lengths[:4] = 100
    lat = eng.step_active([0, 2, 3], n_new=2)   # subset of rows
    assert lat > 0
    # the touched rows advanced their length
    assert int(eng.lengths[0]) == 102 and int(eng.lengths[2]) == 102
    assert int(eng.lengths[1]) == 100           # untouched


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
