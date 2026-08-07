"""Record vLLM scheduler decisions from the spawned EngineCore process.

The directory containing this module is prepended to ``PYTHONPATH`` by an
experiment runner. Python imports ``sitecustomize`` in every child process,
which is necessary because vLLM's Scheduler lives outside the worker front
end. Nothing is patched unless ``OMNI_SCHEDULER_TRACE`` is set.

Each output row is::

    <unix_s> <request_id>:<scheduled_tokens>[E] ...

``E`` marks a request that also scheduled encoder input in that engine step.
The compact format is shared with existing evidence; parsing and validation
live in :mod:`observability.bundle`.
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback


TRACE_ENV = "OMNI_SCHEDULER_TRACE"
ERROR_ENV = "OMNI_SCHEDULER_TRACE_ERRORS"


def _setting(primary: str, legacy: str) -> str | None:
    """Read the public setting while accepting one migration-era alias."""
    return os.environ.get(primary) or os.environ.get(legacy)


def _report_error(stage: str, error: Exception) -> None:
    path = _setting(ERROR_ENV, "SCHED_TRACE_ERRORS")
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


trace_path = _setting(TRACE_ENV, "SCHED_TRACE")
if trace_path:
    try:
        from vllm.v1.core.sched.scheduler import Scheduler

        _trace = open(trace_path, "a", buffering=1, encoding="utf-8")
        _original_schedule = Scheduler.schedule

        def _traced_schedule(self):
            output = _original_schedule(self)
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
            return output

        Scheduler.schedule = _traced_schedule
    except Exception as error:
        _report_error("initialization", error)
        # A requested trace is primary evidence. Failing visibly is safer than
        # completing a plausible-looking run whose engine lanes are empty.
        os._exit(78)
