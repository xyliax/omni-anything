from __future__ import annotations

import gzip
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from observability.bundle import build_bundle, resolve_run
from observability.export_perfetto import export


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def retained_runs() -> list[Path]:
    return sorted(
        run
        for runs in RESULTS.glob("*/runs")
        for run in runs.iterdir()
        if run.is_dir()
    )


class ObservabilityTests(unittest.TestCase):
    def test_scoped_run_resolution(self) -> None:
        run = next((RESULTS / "e2_kv_conveyor" / "runs").iterdir())
        resolved = resolve_run(f"e2_kv_conveyor/{run.name}")
        self.assertEqual(resolved.directory, run.resolve())
        self.assertEqual(resolved.experiment, "e2_kv_conveyor")

    def test_generic_event_schema_exports(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run = Path(temporary) / "generic-run"
            run.mkdir()
            rows = [
                {"type": "slice", "track": "worker", "t_s": 1.0, "duration_s": 0.2, "name": "prefill"},
                {"type": "instant", "track": "worker", "t_s": 1.3, "name": "commit"},
                {"type": "counter", "track": "queue", "t_s": 1.4, "name": "depth", "value": 2},
            ]
            (run / "events.jsonl").write_text(
                "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
            )
            path = Path(export(run))
            metadata = json.loads(
                (run / "derived" / "timeline.trace.metadata.json").read_text(encoding="utf-8")
            )
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                trace = json.load(handle)
        self.assertEqual(metadata["generic_events"], 3)
        self.assertTrue(any(event.get("name") == "prefill" for event in trace["traceEvents"]))

    def test_actual_e1_bundle_has_aligned_engine_steps(self) -> None:
        run = next((RESULTS / "e1_capacity_bottleneck" / "runs").iterdir())
        bundle = build_bundle(run)
        self.assertGreater(len(bundle["steps"]), 1000)
        self.assertGreater(bundle["clock_alignment"]["anchors"], 0)
        self.assertEqual(len(bundle["ticks"]), 300)
        self.assertTrue(
            all(
                1.9 < current - previous < 2.1
                for previous, current in zip(bundle["ticks"], bundle["ticks"][1:])
            )
        )

    def test_every_retained_run_has_a_valid_timeline(self) -> None:
        runs = retained_runs()
        self.assertEqual(len(runs), 17)
        e1_run = next((RESULTS / "e1_capacity_bottleneck" / "runs").iterdir())
        with gzip.open(
            e1_run / "derived" / "timeline.trace.json.gz", "rt", encoding="utf-8"
        ) as handle:
            e1_events = json.load(handle)["traceEvents"]
        for run in runs:
            trace_path = run / "derived" / "timeline.trace.json.gz"
            metadata_path = run / "derived" / "timeline.trace.metadata.json"
            self.assertTrue(trace_path.is_file(), run)
            self.assertTrue(metadata_path.is_file(), run)
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            with gzip.open(trace_path, "rt", encoding="utf-8") as handle:
                trace = json.load(handle)
            self.assertEqual(metadata["events"], len(trace["traceEvents"]), run)
            self.assertEqual(metadata["bytes"], trace_path.stat().st_size, run)
            self.assertEqual(metadata["sha256"], hashlib.sha256(trace_path.read_bytes()).hexdigest(), run)
            meaningful = sum(
                metadata[key]
                for key in (
                    "engine_slices",
                    "compute_slices",
                    "transfer_slices",
                    "measurement_segments",
                    "generic_events",
                )
            )
            self.assertGreater(meaningful, 0, run)
            if metadata["experiment"] in {"e2_kv_conveyor", "e3_phase_scheduling"}:
                self.assertGreater(metadata["engine_slices"], 0, run)
                self.assertEqual(len(metadata["referenced_runs"]), 1, run)
                mechanism_prefix = trace["traceEvents"][: len(e1_events)]
                for actual, expected in zip(mechanism_prefix, e1_events):
                    if expected.get("ph") == "M" and expected.get("name") == "process_name":
                        expected = {
                            **expected,
                            "args": {
                                "name": f"E1 source (real): {expected['args']['name']}"
                            },
                        }
                    self.assertEqual(actual, expected, run)
                thread_names = {
                    event["args"]["name"]
                    for event in trace["traceEvents"]
                    if event.get("ph") == "M" and event.get("name") == "thread_name"
                }
                self.assertIn("serial H2D link", thread_names, run)
                self.assertFalse(
                    any(name.startswith("H2D session") for name in thread_names), run
                )
            for source_name, expected in metadata["source_artifacts"].items():
                source = run / source_name
                self.assertTrue(source.is_file(), source)
                self.assertEqual(expected["bytes"], source.stat().st_size, source)
                self.assertEqual(expected["sha256"], hashlib.sha256(source.read_bytes()).hexdigest(), source)
            for referenced in metadata["referenced_runs"].values():
                referenced_run = ROOT / referenced["path"]
                self.assertTrue(referenced_run.is_dir(), referenced_run)
                for source_name, expected in referenced["artifacts"].items():
                    source = referenced_run / source_name
                    self.assertEqual(expected["bytes"], source.stat().st_size, source)
                    self.assertEqual(
                        expected["sha256"],
                        hashlib.sha256(source.read_bytes()).hexdigest(),
                        source,
                    )


if __name__ == "__main__":
    unittest.main()
