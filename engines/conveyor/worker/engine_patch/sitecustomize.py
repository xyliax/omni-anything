"""Engine-patch loader, injected into the spawned EngineCore process.

The conveyor runner prepends this directory to ``PYTHONPATH`` (ahead of
the trace collector dir (infra/trace) — Python imports only the FIRST ``sitecustomize`` on
``sys.path``), so this module runs at interpreter start in every python child
of the worker. It holds NO mechanism code: it reads the gates and applies the
mechanism modules that live next to it, then chain-loads the infra/trace
scheduler-trace collector this module shadows. Note the worker process itself
also imports this file (PYTHONPATH applies to every python child); applying
the patches there is harmless — only the EngineCore process ever receives
utility calls or runs the scheduler.

Layout (the materialization pattern — state authority / semantic / transport
/ claim):

- ``omni_state.py``     session KV state authority: lifecycle (resident /
                        parked / materializing), timing, deferred queue, and
                        the live block classification — mechanisms report
                        events here, policies read and subscribe (no gate:
                        pure data, imported by the others)
- ``omni_park.py``      the park primitive, auto-park, session-update fixes,
                        and the park.log evidence writers (gate:
                        ``OMNI_PARK_PATCH``)
- ``omni_reload.py``    engine command surface: ``reload_kv`` / ``kv_state``
                        utilities plus the reload pacing policy (pool-tight
                        reloads DEFER until a park frees capacity; a chunk
                        arrival cancels) (gate: ``OMNI_PREFETCH``; requires
                        park)
- ``omni_transfer.py``  transport layer: anonymous CPU->GPU block moves that
                        ride the stock offload load-event machinery (applied
                        by omni_reload, no gate of its own)

The claim layer is vLLM's existing resume hash-match — untouched by design.

A requested mechanism must not silently vanish: a "successful" run that never
parked or never prefetched would masquerade as evidence, so any apply()
failure exits 78 (EX_CONFIG, matching the trace collector's convention).
Importing the mechanism modules patches nothing; all patching happens inside
their ``apply()``.
"""

from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)


def _fail(stage: str, error: Exception) -> None:
    print(f"engine patch {stage} failed: {error!r}", file=sys.stderr, flush=True)


# Warmup sentinel contract, re-exported so the cross-process pin (worker /
# trace collector / engine patch, see tests/test_run_validation.py) keeps one
# authoritative surface. Importing omni_park has no side effects.
from omni_park import WARMUP_REQ_PREFIX  # noqa: E402,F401

if os.environ.get("OMNI_PARK_PATCH"):
    try:
        import omni_park

        omni_park.apply()
    except Exception as error:
        _fail("park initialization", error)
        os._exit(78)

if os.environ.get("OMNI_PREFETCH"):
    try:
        import omni_reload

        omni_reload.apply()
    except Exception as error:
        _fail("prefetch initialization", error)
        os._exit(78)

# Chain-load the scheduler-trace collector (this module shadows it on
# sys.path whenever the engine_patch dir is prepended). Either collector gate
# (scheduler trace or residency sampler) requires the load.
if os.environ.get("OMNI_SCHEDULER_TRACE") or os.environ.get("OMNI_RESIDENCY_LOG"):
    try:
        import importlib.util

        _root = os.path.dirname(  # engine_patch -> worker -> conveyor -> engines -> repo
            os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
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
