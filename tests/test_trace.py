"""Trace parsing and Perfetto export on synthetic runs; tests never read retained GPU evidence."""

from __future__ import annotations

import gzip
import json
import tempfile
import unittest
from pathlib import Path

from infra.trace.bundle import build_bundle
from infra.trace.parse import parse_gpu, parse_kv, parse_kv_events, parse_residency
from infra.trace.perfetto import MissingTimelineDataError, export


SCHEDULER_LINES = (
    "100.000 s1ea:53E s2eb:53E\n"
    "100.020 s1ea:1 s2eb:1\n"
    "100.040 s1ea:1 s2eb:1\n"
    "102.000 s1ea:53E s2eb:53E\n"
    "102.020 s1ea:1 s2eb:1\n"
    "102.040 s1ea:1 s2eb:1\n"
)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_run_dir(results_root: Path, experiment: str, run_id: str) -> Path:
    run = results_root / experiment / run_id
    run.mkdir(parents=True)
    return run


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


class TraceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.tmp = Path(temporary.name)

    def write(self, name: str, text: str) -> Path:
        path = self.tmp / name
        path.write_text(text, encoding="utf-8")
        return path


class ParserTests(TraceTestCase):
    def test_kv_pattern_pre_field_is_optional(self) -> None:
        log = self.write(
            "kv.log", "10.0 kv=0.50 run=8 wait=0 evict=0\n11.0 kv=0.60 run=8 wait=1 evict=0 pre=2\n"
        )
        rows = parse_kv(log, None, None)
        self.assertEqual([row[4] for row in rows], [0, 2])

    def test_gpu_samples_use_their_own_wall_clock(self) -> None:
        rows = parse_gpu(
            self.write(
                "gpu.csv",
                "2026/08/09 14:00:00.000, 3, uuid, name, 50, 1000, 200\n"
                "2026/08/09 14:00:00.200, 3, uuid, name, 70, 1000, 200\n",
            )
        )
        self.assertEqual([row[1] for row in rows], [50, 70])
        self.assertAlmostEqual(rows[1][0] - rows[0][0], 0.2)

    def test_residency_rows_exclude_the_warmup_sentinel(self) -> None:
        rows = parse_residency(
            self.write(
                "residency.log",
                "1755080000.000000 s1e1-abcd:120 s1000000000e1-warm:5\n"
                "1755080000.200000 s1e1-abcd:32 s2e1-efgh:64\n",
            )
        )
        self.assertEqual(rows, [[1755080000.0, [[1, 120]]], [1755080000.2, [[1, 32], [2, 64]]]])

    def test_kv_loads_pair_per_request_and_trigger(self) -> None:
        # A prefetch L and a demand L for the same session may interleave;
        # each R must close its own trigger's window, and trigger-less lines
        # (pre-prefetch logs) read as demand.
        reloads = parse_kv_events(
            self.write(
                "kv_events.log",
                "100.0 L req=s1e1-x cpu_tok=960 gpu_tok=2048 trigger=prefetch\n"
                "100.1 L req=s1e1-x cpu_tok=320 gpu_tok=2048\n"
                "100.2 R req=s1e1-x trigger=prefetch\n"
                "100.3 R req=s1e1-x\n",
            )
        )["reloads"]
        self.assertEqual(
            [(r["trigger"], r["end"]) for r in reloads], [("prefetch", 100.2), ("demand", 100.3)]
        )


class ExportTests(TraceTestCase):
    def test_export_never_overwrites_derived_artifacts(self) -> None:
        run = make_scheduler_run(self.tmp)
        export(run)
        with self.assertRaises(FileExistsError):
            export(run)

    def test_run_without_timeline_data_is_rejected(self) -> None:
        run = make_run_dir(self.tmp, "baseline", "20260807_000003_empty")
        write_json(run / "manifest.json", {"schema_version": 2, "config": {}})
        write_json(run / "status.json", {"state": "success"})
        with self.assertRaises(MissingTimelineDataError):
            export(run)
        self.assertFalse((run / "derived").exists())

    def test_scheduler_run_gets_engine_lanes_and_periodic_ticks(self) -> None:
        run = make_scheduler_run(self.tmp)
        bundle = build_bundle(run)
        self.assertTrue(bundle["steps"])
        # period_ms lives in the nested workload section of new manifests.
        self.assertEqual(bundle.get("tick_source"), "periodic_from_manifest")
        export(run)
        engine_slices = [
            event
            for event in read_trace(run)["traceEvents"]
            if event.get("ph") == "X" and event["name"] in {"sched decode"}
        ]
        self.assertTrue(engine_slices)
