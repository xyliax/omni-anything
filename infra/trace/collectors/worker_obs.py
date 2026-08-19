"""Worker-process observation producers, shared by every experiment's worker.

One observation mechanism for all arms: baseline and conveyor import THIS
module for the per-request event log (``per_request.log``) and the engine
stat logger (``kv.log`` / ``per_iteration.log``). A worker must never carry
its own copy — the two copies this module replaced had already drifted
(baseline lacked the clock-pairing line, the ingest stations, and the
configurable kv.log sampling period). The line grammars live with the
consumers in :mod:`infra.trace.parse`.

Environment contract (set by the experiment runners):

- ``PERREQ_LOG``            per_request.log path; unset = events are no-ops
- ``METRONOME_STATLOG``     kv.log path; unset = no stat logger (env name is
                            metronome heritage — the third_party pin's vanilla
                            worker reads the same variable)
- ``PERITER_LOG``           per_iteration.log path (read by the stat logger)
- ``OMNI_STATLOG_PERIOD_S`` kv.log sampling period, default 1.0
"""

from __future__ import annotations

import os
import time
from typing import Any, Callable


# One perf-clock origin per worker process; every event and the clock-pairing
# line measure against it.
_PT0 = time.perf_counter()


def perreq_logger() -> Callable[..., None]:
    """The ``_pev(kind, *vals)`` event writer for ``per_request.log``.

    Emits one ``C <perf_s> <epoch_s>`` clock-pairing line on open: it maps
    this log's perf clock onto the epoch clock scheduler.log uses, so trace
    alignment is exact instead of heuristic (bundle.align_exact). Returns a
    no-op when ``PERREQ_LOG`` is unset.
    """
    path = os.environ.get("PERREQ_LOG")
    if not path:
        return lambda kind, *vals: None
    handle = open(path, "a", buffering=1)

    def pev(kind: str, *vals: Any) -> None:
        handle.write(
            f"{kind} {time.perf_counter() - _PT0:.3f} " + " ".join(map(str, vals)) + "\n"
        )

    pev("C", f"{time.time():.6f}")
    return pev


def stat_logger_classes() -> list | None:
    """The vLLM stat-logger list for ``AsyncLLM.from_engine_args``.

    Returns ``None`` when ``METRONOME_STATLOG`` is unset (caller passes no
    ``stat_loggers``). The class writes two artifacts:

    - kv.log: throttled scheduler snapshots (kv usage, running/waiting,
      cumulative preemptions). Period from ``OMNI_STATLOG_PERIOD_S`` —
      the runners set 0.2s = 10 samples/tick, matching the GPU sampler's
      rationale (1 Hz was too coarse for the park sawtooth).
    - per_iteration.log (if ``PERITER_LOG`` set): engine-step composition,
      one line per step, no throttle.

    vLLM import is deferred so this module stays importable without vLLM
    (tests, offline tools).
    """
    statlog_path = os.environ.get("METRONOME_STATLOG")
    if not statlog_path:
        return None
    from vllm.v1.metrics.loggers import StatLoggerBase

    class EngineStatLogger(StatLoggerBase):
        def __init__(self, vllm_config, engine_index=0):
            self._f = open(statlog_path, "a")
            self._t0 = time.time()
            self._last = 0.0
            self._pre = 0  # cumulative preemptions (accumulate across throttled calls)
            self._period = float(os.environ.get("OMNI_STATLOG_PERIOD_S", "1.0"))
            periter_path = os.environ.get("PERITER_LOG")
            self._it = open(periter_path, "a", buffering=1) if periter_path else None

        def record(self, scheduler_stats, iteration_stats, mm_cache_stats=None, engine_idx=0):
            if iteration_stats is not None:
                self._pre += getattr(iteration_stats, "num_preempted_reqs", 0)
            if scheduler_stats is None:
                return
            now = time.time()
            if self._it is not None and iteration_stats is not None:
                self._it.write(
                    f"{now - self._t0:.3f} run={scheduler_stats.num_running_reqs} "
                    f"wait={scheduler_stats.num_waiting_reqs} "
                    f"gen={iteration_stats.num_generation_tokens} "
                    f"ptok={getattr(iteration_stats, 'num_prompt_tokens', 0)}\n"
                )
            if now - self._last < self._period:  # throttled sampling
                return
            self._last = now
            ev = len(getattr(scheduler_stats, "kv_cache_eviction_events", []) or [])
            self._f.write(
                f"{now - self._t0:.1f} kv={scheduler_stats.kv_cache_usage:.3f} "
                f"run={scheduler_stats.num_running_reqs} "
                f"wait={scheduler_stats.num_waiting_reqs} evict={ev} "
                f"pre={self._pre}\n"
            )
            self._f.flush()

        def log(self):
            pass

        def log_engine_initialized(self):
            pass

    return [EngineStatLogger]
