"""Record vLLM scheduler decisions from the spawned EngineCore process.

The directory containing this module is prepended to ``PYTHONPATH`` by an
experiment runner (see :mod:`infra.trace.collect`). Python imports
``sitecustomize`` in every child process, which is necessary because vLLM's
Scheduler lives outside the worker front end. Nothing is patched unless
``OMNI_SCHEDULER_TRACE`` or ``OMNI_RESIDENCY_LOG`` is set.

Two artifacts, one hook (a wrapper around ``Scheduler.schedule``):

- ``OMNI_SCHEDULER_TRACE`` — one row per engine step::

    <unix_s> <request_id>:<scheduled_tokens>[E] ...

  ``E`` marks a request that also scheduled encoder input in that step.

- ``OMNI_RESIDENCY_LOG`` — per-session KV residency samples, throttled by
  ``OMNI_STATLOG_PERIOD_S`` (default 1.0; the runners set 0.2s so both systems
  sample kv.log and residency on the same grid)::

    <unix_s> <request_id>:<resident_blocks> ...

  ``resident_blocks`` counts the request's grip (allocated blocks) or, when
  the request holds none (partially evicted under the conveyor engine patch), its
  still-GPU-cached prefix chain walked by block hash — so a partially evicted session
  reads as its pinned floor, not zero. Single-KV-group stack assumption,
  same as the engine patch; on a multi-group config the chain walk is
  skipped and only the grip is counted. This is the SAME sampler for every
  system: baseline shows the monotone context-growth staircase, Conveyor the
  eviction sawtooth, from one mechanism.

The compact formats are shared with existing evidence; parsing and
validation live in :mod:`infra.trace.parse`.
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback


TRACE_ENV = "OMNI_SCHEDULER_TRACE"
ERROR_ENV = "OMNI_SCHEDULER_TRACE_ERRORS"
RESIDENCY_ENV = "OMNI_RESIDENCY_LOG"


def _report_error(stage: str, error: Exception) -> None:
    path = os.environ.get(ERROR_ENV)
    if path:
        with open(path, "a", buffering=1, encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "v": 1,
                        "time": time.time(),
                        "stage": stage,
                        "error": repr(error),
                        "traceback": traceback.format_exc(),
                    }
                )
                + "\n"
            )
    print(
        f"scheduler trace {stage} failed: {error!r}",
        file=sys.stderr,
        flush=True,
    )


trace_path = os.environ.get(TRACE_ENV)
residency_path = os.environ.get(RESIDENCY_ENV)
if trace_path or residency_path:
    try:
        from vllm.v1.core.sched.scheduler import Scheduler

        _trace = open(trace_path, "a", buffering=1, encoding="utf-8") if trace_path else None
        _residency = (
            open(residency_path, "a", buffering=1, encoding="utf-8") if residency_path else None
        )
        _residency_period = float(os.environ.get("OMNI_STATLOG_PERIOD_S", "1.0"))
        _residency_last = [0.0]
        _original_schedule = Scheduler.schedule

        def _resident_blocks(scheduler, request) -> int:
            """Grip if the request holds blocks; else the GPU-cached prefix
            chain (a partially evicted session's pinned floor). Chain reconstruction
            matches the Conveyor engine patch's _gpu_cached_chain."""
            kvm = scheduler.kv_cache_manager
            try:
                held = kvm.get_block_ids(request.request_id)[0]
            except Exception:
                held = []
            if held:
                return len(held)
            if len(scheduler.kv_cache_config.kv_cache_groups) != 1:
                return 0
            chain = 0
            pool = kvm.block_pool
            for block_hash in request.block_hashes:
                if not pool.get_cached_block(block_hash, [0]):
                    break
                chain += 1
            return chain

        def _sample_residency(scheduler, now: float) -> None:
            fields = [
                f"{request_id}:{_resident_blocks(scheduler, request)}"
                for request_id, request in scheduler.requests.items()
            ]
            if fields:
                _residency.write(f"{now:.6f} {' '.join(fields)}\n")

        def _traced_schedule(self):
            output = _original_schedule(self)
            if _trace is not None:
                try:
                    scheduled = output.num_scheduled_tokens
                    if scheduled:
                        encoder = output.scheduled_encoder_inputs or {}
                        fields = (
                            f"{request_id}:{tokens}{'E' if request_id in encoder else ''}"
                            for request_id, tokens in scheduled.items()
                        )
                        _trace.write(f"{time.time():.6f} {' '.join(fields)}\n")
                except Exception as error:
                    _report_error("record", error)
            if _residency is not None:
                try:
                    now = time.time()
                    if now - _residency_last[0] >= _residency_period:
                        _residency_last[0] = now
                        _sample_residency(self, now)
                except Exception as error:
                    _report_error("residency", error)
            return output

        Scheduler.schedule = _traced_schedule
    except Exception as error:
        _report_error("initialization", error)
        # A requested trace is primary evidence. Failing visibly is safer than
        # completing a plausible-looking run whose engine lanes are empty.
        os._exit(78)
