"""Pins for the run-validation contracts that live in log-line wording.

The issue scanners decide run success by substring-matching lines that other
processes — including the Go gateway — print. These tests hold the producer
and the consumer of each such string together, the same way
``FATAL_WORKER_PATTERN`` is pinned in test_lab_artifacts.
"""

from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from experiments.baseline.runner import collect_issues as baseline_issues
from experiments.conveyor.runner import collect_issues as conveyor_issues
from lab.artifacts import RunStore
from tracekit.parse import WARMUP_SESSION


ROOT = Path(__file__).resolve().parents[1]
GATEWAY_GO = ROOT / "experiments" / "conveyor" / "gateway" / "main.go"
BASELINE_WORKER = ROOT / "experiments" / "baseline" / "worker" / "stream_server.py"
CONVEYOR_WORKER = ROOT / "experiments" / "conveyor" / "worker" / "stream_server.py"
ENGINE_PATCH = (
    ROOT / "experiments" / "conveyor" / "worker" / "engine_patch" / "sitecustomize.py"
)

PARK_LINES_HEALTHY = (
    "1755080000.000001 S req=s1e1-abcdefgh blocks=3\n"
    "1755080000.100001 req=s1e1-abcdefgh held=190 evicted=60 cpu_covered=60"
    " usage_before=0.5 usage_after=0.3\n"
    "1755080000.200001 L req=s1e1-abcdefgh cpu_tok=960 gpu_tok=2048\n"
    "1755080000.300001 R req=s1e1-abcdefgh\n"
)


class IssueScanTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.store = RunStore(Path(self.temporary.name))

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write(self, name: str, text: str) -> None:
        self.store.file(name).write_text(text, encoding="utf-8")


class ConveyorIssueScanTests(IssueScanTestCase):
    def test_healthy_run_yields_no_issues(self) -> None:
        self.write("worker.log", "2026-08-13 [stream-worker] step 8: 8 sessions, 3ms\n")
        self.write("gateway.log", "2026/08/13 [conveyor-gateway] WS on :8907\n")
        self.write("park.log", PARK_LINES_HEALTHY)
        self.write("client.json", '{"err": 0}\n')
        self.assertEqual(conveyor_issues(self.store), [])

    def test_each_silent_failure_shape_is_caught(self) -> None:
        self.write("scheduler_errors.log", "boom\n")
        self.write(
            "worker.log",
            "2026-08-13 [stream-worker] session 3 ended: RuntimeError: dead\n"
            "2026-08-13 [stream-worker] park s4 RPC failed: X: y\n",
        )
        self.write("gateway.log", "2026/08/13 [starve] slot=2 starved=1/8\n")
        self.write("park.log", PARK_LINES_HEALTHY)
        self.write("client.json", '{"err": 2}\n')
        issues = conveyor_issues(self.store)
        self.assertEqual(
            issues,
            [
                "scheduler trace reported serialization errors",
                "1 session(s) died mid-run (see worker.log 'ended:' lines)",
                "1 slot firing(s) short-delivered tokens "
                "(engine behind; see gateway.log '[starve]' lines)",
                "client reported 2 session error(s)",
                "1 park RPC failure(s) (see worker.log)",
            ],
        )

    def test_park_log_without_park_lines_is_an_issue(self) -> None:
        # S/L/R lines flow whenever the mirror moves; only a park line proves
        # the mechanism fired. A requested mechanism must not silently vanish.
        self.write(
            "park.log",
            "1755080000.000001 S req=s1e1-abcdefgh blocks=3\n"
            "1755080000.200001 L req=s1e1-abcdefgh cpu_tok=960 gpu_tok=2048\n",
        )
        self.assertEqual(
            conveyor_issues(self.store),
            ["park enabled but park.log recorded zero parks"],
        )


class BaselineIssueScanTests(IssueScanTestCase):
    def test_healthy_run_yields_no_issues(self) -> None:
        self.write("worker.log", "2026-08-13 [stream-worker] engine warm\n")
        self.write("client.json", '{"err": 0}\n')
        self.assertEqual(baseline_issues(self.store), [])

    def test_fatal_worker_and_client_errors_are_caught(self) -> None:
        self.write("worker.log", "... CUDA out of memory ...\n")
        self.write("client.json", '{"err": 1}\n')
        self.assertEqual(
            baseline_issues(self.store),
            [
                "worker log contains a fatal error",
                "client reported 1 session error(s)",
            ],
        )


class CrossLanguageLogContractTests(unittest.TestCase):
    """The producer side of every scanned string, pinned at the source."""

    def test_gateway_prints_the_starve_line_the_scanner_greps(self) -> None:
        self.assertIn('log.Printf("[starve] ', GATEWAY_GO.read_text(encoding="utf-8"))

    def test_worker_prints_the_lines_the_scanner_greps(self) -> None:
        text = CONVEYOR_WORKER.read_text(encoding="utf-8")
        self.assertIn('ended: %s', text)       # dead-session scan
        self.assertIn('RPC failed', text)      # park transport-failure scan


class WarmupSentinelTests(unittest.TestCase):
    """One sentinel, three declarations across process boundaries."""

    def test_all_declarations_agree(self) -> None:
        self.assertEqual(WARMUP_SESSION, 10**9)
        for worker in (BASELINE_WORKER, CONVEYOR_WORKER):
            self.assertIn(
                "WARMUP_SID = 10**9",
                worker.read_text(encoding="utf-8"),
                f"warmup sentinel constant missing or changed in {worker.name}",
            )
        with mock.patch.dict(os.environ):
            # both gates must stay closed: importing must patch nothing.
            os.environ.pop("OMNI_PARK_PATCH", None)
            os.environ.pop("OMNI_SCHEDULER_TRACE", None)
            spec = importlib.util.spec_from_file_location("park_patch_under_test", ENGINE_PATCH)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        self.assertEqual(module.WARMUP_REQ_PREFIX, f"s{WARMUP_SESSION}e")


if __name__ == "__main__":
    unittest.main()
