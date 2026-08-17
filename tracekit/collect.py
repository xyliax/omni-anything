"""Collection-side helpers: how experiments wire tracing into child processes.

Experiments never construct trace paths or PYTHONPATH entries themselves;
they call these helpers so the collection contract has one owner.
"""

from __future__ import annotations

import os
from pathlib import Path


SCHEDULER_TRACE_ENV = "OMNI_SCHEDULER_TRACE"
SCHEDULER_TRACE_ERRORS_ENV = "OMNI_SCHEDULER_TRACE_ERRORS"
RESIDENCY_ENV = "OMNI_RESIDENCY_LOG"

_COLLECTORS = Path(__file__).resolve().parent / "collectors"


def scheduler_trace_environment(
    trace_path: Path, errors_path: Path, residency_path: Path | None = None
) -> dict[str, str]:
    """Environment variables enabling the EngineCore scheduler trace hook.

    The returned ``PYTHONPATH`` entry must be *prepended* to any existing
    value so ``sitecustomize`` is imported by every spawned interpreter.
    ``residency_path`` additionally turns on the per-session KV residency
    sampler (same hook, same collector — one mechanism for every arm).
    """
    settings = {
        SCHEDULER_TRACE_ENV: str(trace_path),
        SCHEDULER_TRACE_ERRORS_ENV: str(errors_path),
        "PYTHONPATH_PREPEND": str(_COLLECTORS / "vllm_scheduler_trace"),
    }
    if residency_path is not None:
        settings[RESIDENCY_ENV] = str(residency_path)
    return settings


def apply_scheduler_trace(
    env: dict[str, str],
    trace_path: Path,
    errors_path: Path,
    residency_path: Path | None = None,
) -> None:
    """Mutate a child-process environment to enable the scheduler trace."""
    settings = scheduler_trace_environment(trace_path, errors_path, residency_path)
    prepend = settings.pop("PYTHONPATH_PREPEND")
    env.update(settings)
    env["PYTHONPATH"] = prepend + os.pathsep + env.get("PYTHONPATH", "")


def gpu_monitor_command(gpu: int, sample_period_s: float) -> list[str]:
    """The nvidia-smi sampler; its period must come from the platform config
    because trace parsing centers each sample in its own interval."""
    return [
        "nvidia-smi",
        f"--id={gpu}",
        "--query-gpu=timestamp,index,uuid,name,utilization.gpu,memory.used,power.draw",
        "--format=csv,noheader,nounits",
        f"-lms={int(sample_period_s * 1000)}",
    ]
