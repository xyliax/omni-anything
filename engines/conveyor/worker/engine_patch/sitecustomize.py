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

Layout:

- ``omni_state.py``     session activity, prefetch control, timestamps, and
                        live block-coverage queries (no physical-state copy)
- ``omni_evict.py``     partial KV eviction, session-update fixes, host-backing
                        instrumentation, and ``kv_events.log`` writers (gate:
                        ``OMNI_KV_EVICTION``)
- ``omni_prefetch.py``  ``prefetch_kv`` / ``kv_state`` utilities and the
                        capacity-aware deferred-prefetch policy
- ``omni_prefetch_transport.py`` transport adapter that rides vLLM's stock
                        offload load-event machinery

The next request uses vLLM's existing prefix-cache match; that path is not
modified.

A requested mechanism must not silently vanish: a "successful" run with no
KV eviction or no prefetch would masquerade as evidence, so any apply()
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
# authoritative surface. Importing omni_evict has no side effects.
from omni_evict import WARMUP_REQ_PREFIX  # noqa: E402,F401

if os.environ.get("OMNI_KV_EVICTION"):
    try:
        import omni_evict

        omni_evict.apply()
    except Exception as error:
        _fail("KV-eviction initialization", error)
        os._exit(78)

if os.environ.get("OMNI_PREFETCH"):
    try:
        import omni_prefetch

        omni_prefetch.apply()
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
