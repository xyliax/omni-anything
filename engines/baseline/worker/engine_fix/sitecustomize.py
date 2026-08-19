"""Upstream vLLM 0.23 bug fix, injected into the spawned EngineCore process:
refresh ``session.max_tokens`` from each streaming chunk's sampling params.

The engine's stop check reads ``session.max_tokens``, which upstream freezes
at request construction — the FIRST streaming input's params. A warm-started
session's first input is the seed prefill with ``max_tokens=1``, so without
this fix every later segment is capped at 1 token while the tick cadence
stays green (the miss=94.8% incident, experiment-log 2026-08-10). The
baseline runner therefore prepends this dir to ``PYTHONPATH`` and sets
``OMNI_SESSION_MAXTOKENS_FIX=1`` exactly when ``seed_tokens > 0``.

This is a BUG FIX, not a mechanism: it makes the engine honor the sampling
params the worker actually sent for each segment — no park, no mirror, no
scheduling change. The conveyor engine_patch carries the identical refresh
inside its session-update wrapper (park runs); baseline runs no mechanism,
so the fix lives standalone here. Behavior equivalence for non-seed runs is
kept by the worker's constant per-segment cap (tpt+8): frozen-at-first-input
and refreshed-per-chunk regimes then agree, so the frozen baseline's formal
runs remain comparable.

Nothing is patched unless ``OMNI_SESSION_MAXTOKENS_FIX`` is set. Python
imports only the FIRST ``sitecustomize`` on ``sys.path``, so this module
chain-loads the infra/trace scheduler-trace collector when tracing/residency
is also requested (same pattern as the conveyor engine_patch).
"""

from __future__ import annotations

import os
import sys


def _fail(stage: str, error: Exception) -> None:
    print(f"session max_tokens fix {stage} failed: {error!r}", file=sys.stderr, flush=True)


if os.environ.get("OMNI_SESSION_MAXTOKENS_FIX"):
    try:
        from vllm.v1.core.sched.scheduler import Scheduler

        _original_update = Scheduler._update_request_as_session

        def _update_request_as_session(self, session, update):
            _original_update(self, session, update)
            # Upstream gap: the stop check reads session.max_tokens, frozen at
            # construction; the original update replaces sampling_params but
            # never this field. Refresh it so each segment runs under the
            # params the worker sent (the cap is PER-SEGMENT: output tokens
            # fold into the prompt every chunk).
            if update is not None and update.sampling_params is not None:
                session.max_tokens = update.sampling_params.max_tokens

        Scheduler._update_request_as_session = _update_request_as_session
    except Exception as error:
        _fail("initialization", error)
        # A requested fix must not silently vanish: a seeded run without it
        # dies at 1 token/segment while cadence metrics stay green. 78 =
        # EX_CONFIG, matching the trace collector's convention.
        os._exit(78)


# Chain-load the scheduler-trace collector (this module shadows it on
# sys.path whenever the fix dir is prepended).
if os.environ.get("OMNI_SCHEDULER_TRACE") or os.environ.get("OMNI_RESIDENCY_LOG"):
    try:
        import importlib.util

        _root = os.path.dirname(  # engine_fix -> worker -> baseline -> engines -> repo
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        )
        _trace_path = os.path.join(
            _root, "infra", "trace", "collectors", "vllm_scheduler_trace", "sitecustomize.py"
        )
        _spec = importlib.util.spec_from_file_location("omni_trace_sitecustomize", _trace_path)
        _module = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_module)
    except Exception as error:
        _fail("trace chain-load", error)
        os._exit(78)  # 78 = EX_CONFIG; requested trace is primary evidence
