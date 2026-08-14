"""Synthetic run fixtures: tests never depend on retained GPU evidence."""

from __future__ import annotations

import gzip
import json
from pathlib import Path


SCHEDULER_LINES = (
    "100.000 s1ea:53E s2eb:53E\n"
    "100.020 s1ea:1 s2eb:1\n"
    "100.040 s1ea:1 s2eb:1\n"
    "102.000 s1ea:53E s2eb:53E\n"
    "102.020 s1ea:1 s2eb:1\n"
    "102.040 s1ea:1 s2eb:1\n"
)


def make_run_dir(results_root: Path, experiment: str, run_id: str) -> Path:
    run = results_root / experiment / "runs" / run_id
    run.mkdir(parents=True)
    return run


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_scheduler_run(results_root: Path, run_id: str = "20260807_000002_engine") -> Path:
    """A minimal baseline-shaped run with a real scheduler trace fixture."""
    run = make_run_dir(results_root, "baseline", run_id)
    write_json(
        run / "manifest.json",
        {
            "schema_version": 2,
            "run_id": run_id,
            "config": {"workload": {"period_ms": 2000}, "platform": {"gpu_sample_period_s": 5}},
        },
    )
    write_json(run / "status.json", {"schema_version": 2, "state": "success", "phase": "complete"})
    (run / "scheduler.log").write_text(SCHEDULER_LINES, encoding="utf-8")
    return run


def read_trace(run: Path) -> dict:
    with gzip.open(run / "derived" / "timeline.trace.json.gz", "rt", encoding="utf-8") as handle:
        return json.load(handle)
