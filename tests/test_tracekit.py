from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tracekit.bundle import build_bundle
from tracekit.parse import parse_gpu, parse_kv, parse_park, parse_residency
from tracekit.perfetto import MissingTimelineDataError, export

from .synthetic import make_run_dir, make_scheduler_run, read_trace, write_json


class ParserTests(unittest.TestCase):
    def test_kv_pattern_pre_field_is_optional(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "kv.log"
            path.write_text(
                "10.0 kv=0.50 run=8 wait=0 evict=0\n"
                "11.0 kv=0.60 run=8 wait=1 evict=0 pre=2\n",
                encoding="utf-8",
            )
            rows = parse_kv(path, None, None)
        self.assertEqual([row[4] for row in rows], [0, 2])

    def test_gpu_samples_use_their_own_wall_clock(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "gpu.csv"
            path.write_text(
                "2026/08/09 14:00:00.000, 3, uuid, name, 50, 1000, 200\n"
                "2026/08/09 14:00:00.200, 3, uuid, name, 70, 1000, 200\n",
                encoding="utf-8",
            )
            rows = parse_gpu(path)
        self.assertEqual([row[1] for row in rows], [50, 70])
        self.assertAlmostEqual(rows[1][0] - rows[0][0], 0.2)

    def test_residency_rows_exclude_the_warmup_sentinel(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "residency.log"
            path.write_text(
                "1755080000.000000 s1e1-abcd:120 s1000000000e1-warm:5\n"
                "1755080000.200000 s1e1-abcd:32 s2e1-efgh:64\n",
                encoding="utf-8",
            )
            rows = parse_residency(path)
        self.assertEqual(
            rows,
            [
                [1755080000.0, [[1, 120]]],
                [1755080000.2, [[1, 32], [2, 64]]],
            ],
        )

    def test_park_loads_pair_per_request_and_trigger(self) -> None:
        # A prefetch L and a demand L for the same session may interleave;
        # each R must close its own trigger's window, and trigger-less lines
        # (pre-prefetch logs) read as demand.
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "park.log"
            path.write_text(
                "100.0 L req=s1e1-x cpu_tok=960 gpu_tok=2048 trigger=prefetch\n"
                "100.1 L req=s1e1-x cpu_tok=320 gpu_tok=2048\n"
                "100.2 R req=s1e1-x trigger=prefetch\n"
                "100.3 R req=s1e1-x\n",
                encoding="utf-8",
            )
            reloads = parse_park(path)["reloads"]
        self.assertEqual(
            [(r["trigger"], r["end"]) for r in reloads],
            [("prefetch", 100.2), ("demand", 100.3)],
        )


class ExportTests(unittest.TestCase):
    def test_export_never_overwrites_derived_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run = make_scheduler_run(Path(temporary))
            export(run)
            with self.assertRaises(FileExistsError):
                export(run)

    def test_run_without_timeline_data_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run = make_run_dir(Path(temporary), "baseline", "20260807_000003_empty")
            write_json(run / "manifest.json", {"schema_version": 2, "config": {}})
            write_json(run / "status.json", {"state": "success"})
            with self.assertRaises(MissingTimelineDataError):
                export(run)
            self.assertFalse((run / "derived").exists())

    def test_scheduler_run_gets_engine_lanes_and_periodic_ticks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run = make_scheduler_run(Path(temporary))
            bundle = build_bundle(run)
            self.assertTrue(bundle["steps"])
            # period_ms lives in the nested workload section of new manifests.
            self.assertEqual(bundle.get("tick_source"), "periodic_from_manifest")
            export(run)
            trace = read_trace(run)
            engine_slices = [
                event
                for event in trace["traceEvents"]
                if event.get("ph") == "X" and event["name"] in {"sched decode"}
            ]
            self.assertTrue(engine_slices)


if __name__ == "__main__":
    unittest.main()
