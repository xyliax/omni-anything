from __future__ import annotations

import json
import gzip
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from observability import bundle
from observability.export_perfetto import (
    MissingTimelineDataError,
    export,
)


class BundleTests(unittest.TestCase):
    def test_session_push_fanout_becomes_one_gateway_tick(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "per_request.log"
            path.write_text(
                "".join(
                    [f"P {1.000 + session * 0.001:.3f} {session}\n" for session in range(1, 9)]
                    + [f"P {3.000 + session * 0.001:.3f} {session}\n" for session in range(1, 9)]
                ),
                encoding="utf-8",
            )
            parsed = bundle.parse_per_request(path)
        self.assertEqual(parsed["ticks"], [0.0, 2.0])

    def test_new_run_layout_is_parsed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run = Path(temporary) / "run-123"
            run.mkdir()
            (run / "manifest.json").write_text(json.dumps({"run_id": "run-123"}), encoding="utf-8")
            (run / "status.json").write_text(json.dumps({"state": "success"}), encoding="utf-8")
            (run / "per_request.log").write_text(
                "P 1.0 1000000000\nP 2.0 1\nT 2.1 1 1 0 1\nT 2.2 1 2 0 1\n",
                encoding="utf-8",
            )
            (run / "kv.log").write_text("0.0 kv=0.100 run=1 wait=0 evict=0 pre=0\n", encoding="utf-8")
            (run / "scheduler.log").write_text("100.000 s1eabc:53E\n100.020 s1eabc:1\n", encoding="utf-8")
            (run / "gpu.csv").write_text("2026/08/06, 3, GPU-X, RTX 3090, 42, 1000, 80\n", encoding="utf-8")

            parsed = bundle.build_bundle(run)

        self.assertEqual(parsed["run_id"], "run-123")
        self.assertEqual(parsed["status"]["state"], "success")
        self.assertEqual(parsed["smi"][0][1], 42)
        self.assertEqual(parsed["steps"][0][1], [[1, 53, 1]])
        self.assertIn("clock_alignment", parsed)

    def test_run_id_resolution(self) -> None:
        run_id = (
            "20260806T210551.398631Z_e1_paringest_trace_n8_p2000_"
            "mml32768_seed0_3139eab_formal-rerun"
        )
        files = bundle.resolve_run(run_id)
        self.assertEqual(files.run_id, run_id)
        self.assertTrue(str(files.scheduler).endswith(f"{run_id}/scheduler.log"))

    def test_vanilla_trace_uses_manifest_period_and_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run = Path(temporary) / "vanilla-trace"
            run.mkdir()
            (run / "manifest.json").write_text(
                json.dumps({"run_id": run.name, "config": {"period_ms": 2000}}),
                encoding="utf-8",
            )
            (run / "scheduler.log").write_text(
                "100.000 s1eabc:53E\n100.020 s1eabc:1\n102.000 s1eabc:53E\n",
                encoding="utf-8",
            )
            parsed = bundle.build_bundle(run)
            self.assertEqual(parsed["tick_source"], "periodic_from_manifest")
            output = Path(export(str(run)))
            with gzip.open(output, "rt", encoding="utf-8") as handle:
                trace = json.load(handle)
            self.assertTrue(trace["traceEvents"])
            with self.assertRaises(FileExistsError):
                export(str(run))

    def test_perfetto_export_rejects_request_only_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run = Path(temporary) / "request-only"
            run.mkdir()
            (run / "per_request.log").write_text(
                "P 1.0 1000000000\nP 2.0 1\nT 2.1 1 1 0 1\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(MissingTimelineDataError, "no supported timeline data"):
                export(str(run))

            self.assertFalse((run / "derived").exists())

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "observability.export_perfetto",
                    str(run),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("no supported timeline data", completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)


if __name__ == "__main__":
    unittest.main()
