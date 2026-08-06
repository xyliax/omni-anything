"""Test the OpenAI Realtime-like server: audio streaming + deadline-aware admission
(mock backend, no GPU)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
pytest.importorskip("websockets")

from experiments.realtime_demo import run


def test_realtime_admission_and_audio_streaming():
    import asyncio
    ok = asyncio.run(run(n_clients=8, seconds=1.0))
    assert ok        # admitted == capacity, rejected the rest, streamed audio


def test_realtime_full_feature_coverage():
    """Every Realtime feature: full-duplex, text, half-duplex turns, cancellation,
    server-VAD, transcription, conversation items, disconnect cleanup."""
    import asyncio
    from experiments.realtime_features import run as run_features
    ok, results = asyncio.run(run_features())
    failed = [k for k, v in results.items() if not v]
    assert ok, f"failed features: {failed}"


def test_realtime_capacity_computed_from_cost_model():
    from metronome.realtime import RealtimeServer
    from metronome.backends.mock import MockBackend
    from metronome.cost_model import CostModel
    from metronome import models
    facts = models.MOSHI
    cost = CostModel(model="m", device="cpu", c_fixed=10, alpha=0.001, batch_base=10,
                     batch_per_session=12.0, batch_alpha=0.001, tail_factor=1.0,
                     kv_bytes_per_token=facts.kv_bytes_per_token)
    srv = RealtimeServer(MockBackend(facts, cost=cost), frame_budget_s=0.08,
                         kv_budget_tokens=1024, tokens_per_tick=2)
    # budget 80ms*0.9=72ms; base 10 + 12*N <= 72 -> N <= 5; ~4-5
    assert 1 <= srv.capacity <= 6
