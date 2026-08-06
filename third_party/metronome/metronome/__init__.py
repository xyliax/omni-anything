"""Metronome — frame-budget serving for real-time interaction models.

Public API:

    from metronome import MetronomeServer, AdmissionController, TickScheduler
    from metronome import PeriodicSession, CostModel, models

    # Drive a real backend (vLLM) with deadline-aware admission + scheduling:
    from metronome.backends.vllm_backend import VLLMBackend
    backend = VLLMBackend("Qwen/Qwen3-1.7B", gpu_memory_utilization=0.3)
    server  = MetronomeServer(backend, frame_budget_s=0.2, kv_budget_tokens=2048,
                              tokens_per_tick=25)
    server.calibrate()                 # fit the cost model to this backend+model
    if server.admit(sid):              # deadline-aware admission test
        server.serve(...)              # measured serving

See docs/INTEGRATION.md for the developer guide and docs/RESEARCH_PLAN.md for the
research framing.
"""
from . import models
from .session import PeriodicSession, DegradeLevel
from .cost_model import CostModel, fit_single, fit_batch
from .admission import (AdmissionController, AdmissionConfig, AdmissionResult,
                        IncrementalAdmissionController)
from .scheduler import TickScheduler, FrameResult
from .kv_manager import EvictionPolicy, make_policy, quality_proxy, POLICIES

__all__ = [
    "models", "PeriodicSession", "DegradeLevel", "CostModel", "fit_single",
    "fit_batch", "AdmissionController", "AdmissionConfig", "AdmissionResult",
    "IncrementalAdmissionController", "TickScheduler", "FrameResult",
    "EvictionPolicy", "make_policy", "quality_proxy", "POLICIES",
    "MetronomeServer", "ServingEngine",
]

__version__ = "0.1.0"


def __getattr__(name):
    # lazy imports for the heavy (torch / backend) pieces so `import metronome`
    # stays light and works without a GPU.
    if name == "MetronomeServer":
        from .serve import MetronomeServer
        return MetronomeServer
    if name == "ServingEngine":
        from .engine import ServingEngine
        return ServingEngine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
