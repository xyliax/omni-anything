"""Pins for the run-validation contracts that live in log-line wording.

The issue scanners decide run success by substring-matching lines that other
processes — including the Go gateway — print. These tests hold the producer
and the consumer of each such string together, the same way
``FATAL_WORKER_PATTERN`` is pinned in test_run_artifacts.
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
from infra.run.artifacts import RunStore
from infra.trace.parse import WARMUP_SESSION


ROOT = Path(__file__).resolve().parents[1]
GATEWAY_GO = ROOT / "engines" / "conveyor" / "gateway" / "main.go"
BASELINE_WORKER = ROOT / "engines" / "baseline" / "worker" / "stream_server.py"
CONVEYOR_WORKER = ROOT / "engines" / "conveyor" / "worker" / "stream_server.py"
ENGINE_PATCH = (
    ROOT / "engines" / "conveyor" / "worker" / "engine_patch" / "sitecustomize.py"
)
ENGINE_FIX = (
    ROOT / "engines" / "baseline" / "worker" / "engine_fix" / "sitecustomize.py"
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

    def test_prefetch_enabled_without_prefetch_loads_is_an_issue(self) -> None:
        # Same shape as the zero-park scan: prefetch is declared in the
        # manifest, so a park.log holding only demand loads means the
        # mechanism never fired.
        self.write("park.log", PARK_LINES_HEALTHY)
        self.write(
            "manifest.json",
            '{"config": {"engine": {"prefetch": "push"}}}\n',
        )
        self.assertEqual(
            conveyor_issues(self.store),
            ["prefetch enabled but park.log recorded zero prefetch loads"],
        )

    def test_prefetch_loads_satisfy_the_scan(self) -> None:
        self.write(
            "park.log",
            PARK_LINES_HEALTHY
            + "1755080000.400001 L req=s1e1-abcdefgh cpu_tok=960 gpu_tok=2048"
            " trigger=prefetch\n"
            "1755080000.500001 R req=s1e1-abcdefgh trigger=prefetch\n",
        )
        self.write(
            "manifest.json",
            '{"config": {"engine": {"prefetch": "push"}}}\n',
        )
        self.assertEqual(conveyor_issues(self.store), [])

    def test_step_error_and_client_health_are_issues(self) -> None:
        self.write("gateway.log", "Step error: rpc unavailable\n")
        self.write("client.json", '{"err": 0, "realtime": false}\n')
        self.assertEqual(
            conveyor_issues(self.store),
            [
                "gateway reported 1 Step error(s)",
                "client failed real-time acceptance (realtime=false)",
            ],
        )

    def test_session_that_never_reaches_quota_is_an_issue(self) -> None:
        self.write(
            "manifest.json",
            '{"config": {"workload": {"sessions": 2, "tokens_per_tick": 25}}}\n',
        )
        self.write(
            "gateway_ticks.log",
            "1755080000.000001 slot=0 n=2 deliv=1:25,2:1\n"
            "1755080002.000001 slot=0 n=2 deliv=1:25,2:1\n",
        )
        self.assertEqual(
            conveyor_issues(self.store),
            ["1 conveyor session(s) never reached full delivery"],
        )

    def test_bounded_startup_ramp_reaches_full_delivery(self) -> None:
        self.write(
            "manifest.json",
            '{"config": {"workload": {"sessions": 2, "tokens_per_tick": 25}}}\n',
        )
        self.write(
            "gateway_ticks.log",
            "1755080000.000001 slot=0 n=0\n"
            "1755080000.250001 slot=1 n=2 deliv=1:1,2:0\n"
            "1755080002.250001 slot=1 n=2 deliv=1:25,2:25\n",
        )
        self.assertEqual(conveyor_issues(self.store), [])

    def test_malformed_delivery_record_is_an_issue_not_an_exception(self) -> None:
        self.write(
            "manifest.json",
            '{"config": {"workload": {"sessions": 1, "tokens_per_tick": 25}}}\n',
        )
        self.write(
            "gateway_ticks.log",
            "1755080000.000001 slot=0 n=1 deliv=not-a-count\n",
        )
        self.assertEqual(
            conveyor_issues(self.store),
            [
                "malformed conveyor delivery record in gateway_ticks.log",
                "1 conveyor session(s) never reached full delivery",
            ],
        )


class BaselineIssueScanTests(IssueScanTestCase):
    def test_healthy_run_yields_no_issues(self) -> None:
        self.write(
            "worker.log",
            "2026-08-13 [stream-worker] engine warm\n"
            "2026-08-13 [stream-worker] delivery tpt=25 deliv=1:25,2:25\n",
        )
        self.write("manifest.json", '{"config": {"mode": "paringest"}}\n')
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

    def test_delivery_session_step_and_client_failures_are_caught(self) -> None:
        self.write(
            "worker.log",
            "session 2 ended: RuntimeError: dead\n"
            "delivery tpt=25 deliv=1:25,2:25\n"
            "delivery tpt=25 deliv=1:24,2:0\n",
        )
        self.write("manifest.json", '{"config": {"mode": "paringest"}}\n')
        self.write("gateway.log", "Step error: rpc unavailable\n")
        self.write("client.json", '{"err": 0, "realtime": false}\n')
        self.assertEqual(
            baseline_issues(self.store),
            [
                "1 session(s) died mid-run (see worker.log 'ended:' lines)",
                "2 baseline session delivery(ies) below quota "
                "(see worker.log 'delivery' lines)",
                "gateway reported 1 Step error(s)",
                "client failed real-time acceptance (realtime=false)",
            ],
        )

    def test_paringest_requires_delivery_records_but_vanilla_does_not(self) -> None:
        self.write("worker.log", "engine warm\n")
        self.write("manifest.json", '{"config": {"mode": "paringest"}}\n')
        self.assertEqual(
            baseline_issues(self.store),
            ["paringest worker produced no delivery-completeness records"],
        )
        self.write("manifest.json", '{"config": {"mode": "vanilla"}}\n')
        self.assertEqual(baseline_issues(self.store), [])

    def test_startup_partial_is_ttfa_but_never_full_is_an_issue(self) -> None:
        self.write("worker.log", "delivery tpt=25 deliv=1:1,2:0\n")
        self.write("manifest.json", '{"config": {"mode": "paringest"}}\n')
        self.assertEqual(
            baseline_issues(self.store),
            ["2 baseline session(s) never reached full delivery"],
        )
        self.write(
            "worker.log",
            "delivery tpt=25 deliv=1:1,2:0\n"
            "delivery tpt=25 deliv=1:25,2:25\n",
        )
        self.assertEqual(baseline_issues(self.store), [])

    def test_manifest_session_absent_from_all_delivery_rows_is_an_issue(self) -> None:
        self.write("worker.log", "delivery tpt=25 deliv=1:25\n")
        self.write(
            "manifest.json",
            '{"config": {"mode": "paringest", "workload": {"sessions": 2}}}\n',
        )
        self.assertEqual(
            baseline_issues(self.store),
            ["1 baseline session(s) never reached full delivery"],
        )

    def test_log_cannot_self_report_a_lower_quota_than_manifest(self) -> None:
        self.write("worker.log", "delivery tpt=1 deliv=1:1\n")
        self.write(
            "manifest.json",
            '{"config": {"mode": "paringest", "workload": '
            '{"sessions": 1, "tokens_per_tick": 25}}}\n',
        )
        self.assertEqual(
            baseline_issues(self.store),
            [
                "baseline delivery quota does not match manifest",
                "1 baseline session(s) never reached full delivery",
            ],
        )

    def test_malformed_baseline_delivery_record_is_not_silently_skipped(self) -> None:
        self.write("worker.log", "delivery tpt=25 missing-deliv-field\n")
        self.write("manifest.json", '{"config": {"mode": "paringest"}}\n')
        self.assertEqual(
            baseline_issues(self.store),
            [
                "malformed baseline delivery record in worker.log",
                "paringest worker produced no delivery-completeness records",
            ],
        )


class SharedClientHealthTests(IssueScanTestCase):
    def test_starved_client_invalidates_both_arms(self) -> None:
        self.write("client.json", '{"err": 0, "starved": true}\n')
        for scanner in (baseline_issues, conveyor_issues):
            with self.subTest(scanner=scanner.__module__):
                self.assertEqual(
                    scanner(self.store),
                    ["client received no ticks (starved=true)"],
                )


class WarmStartIssueScanTests(IssueScanTestCase):
    def test_timeout_invalidates_both_arms(self) -> None:
        self.write(
            "worker.log",
            "2026-08-20 [stream-worker] warm-start barrier timed out (7/8 seeded)\n",
        )
        for scanner in (baseline_issues, conveyor_issues):
            with self.subTest(scanner=scanner.__module__):
                self.assertEqual(scanner(self.store), ["worker log contains a fatal error"])


class CrossLanguageLogContractTests(unittest.TestCase):
    """The producer side of every scanned string, pinned at the source."""

    def test_gateway_prints_the_starve_line_the_scanner_greps(self) -> None:
        text = GATEWAY_GO.read_text(encoding="utf-8")
        self.assertIn('log.Printf("[starve] ', text)
        self.assertIn('deliv = append(deliv, fmt.Sprintf("%d:0", s.id))', text)

    def test_worker_prints_the_lines_the_scanner_greps(self) -> None:
        text = CONVEYOR_WORKER.read_text(encoding="utf-8")
        self.assertIn('ended: %s', text)       # dead-session scan
        self.assertIn('RPC failed', text)      # park transport-failure scan

    def test_both_workers_print_the_warm_start_timeout(self) -> None:
        for worker in (BASELINE_WORKER, CONVEYOR_WORKER):
            self.assertIn(
                'log.error("warm-start barrier timed out',
                worker.read_text(encoding="utf-8"),
            )

    def test_baseline_worker_prints_delivery_completeness(self) -> None:
        self.assertIn(
            'log.info("delivery tpt=%d deliv=%s"',
            BASELINE_WORKER.read_text(encoding="utf-8"),
        )


class SharedObservationProducerTests(unittest.TestCase):
    """One observation mechanism for both arms: the workers must import the
    shared infra/trace producer, never carry a private copy (the two copies this
    replaced had already drifted — clock line, sampling period, stations)."""

    def test_both_workers_use_the_shared_producer(self) -> None:
        for worker in (BASELINE_WORKER, CONVEYOR_WORKER):
            text = worker.read_text(encoding="utf-8")
            self.assertIn(
                "from infra.trace.collectors.worker_obs import perreq_logger, stat_logger_classes",
                text,
                f"{worker} must import the shared observation producer",
            )
            self.assertNotIn(
                "StatLoggerBase", text,
                f"{worker} must not define a private stat logger",
            )
            self.assertNotIn(
                "def _pev", text,
                f"{worker} must not carry a private per-request event writer",
            )

    def test_both_workers_emit_the_ingest_stations(self) -> None:
        for worker in (BASELINE_WORKER, CONVEYOR_WORKER):
            text = worker.read_text(encoding="utf-8")
            for station in ("IQ", "IS", "IE", "IR", "IA"):
                self.assertIn(
                    f'_pev("{station}"', text,
                    f"{worker} lost ingest station {station}",
                )


class SeedRunFixTests(unittest.TestCase):
    """Seed runs die at 1 token/segment without the frozen-max_tokens fix
    (the miss=94.8% shape); the runner must inject it exactly then."""

    def test_seeded_worker_environment_injects_the_fix_first(self) -> None:
        from experiments.baseline.config import BaselineConfig
        from experiments.baseline.runner import worker_environment

        run_dir = Path(self.enterContext(tempfile.TemporaryDirectory()))
        seeded = worker_environment(
            BaselineConfig(trace=True, seed_tokens=4096), run_dir
        )
        self.assertEqual(seeded.get("OMNI_SESSION_MAXTOKENS_FIX"), "1")
        first = seeded["PYTHONPATH"].split(os.pathsep)[0]
        self.assertTrue(first.endswith("engine_fix"), first)
        unseeded = worker_environment(BaselineConfig(trace=True), run_dir)
        self.assertNotIn("OMNI_SESSION_MAXTOKENS_FIX", unseeded)

    def test_fix_module_patches_nothing_when_gates_are_closed(self) -> None:
        with mock.patch.dict(os.environ):
            os.environ.pop("OMNI_SESSION_MAXTOKENS_FIX", None)
            os.environ.pop("OMNI_SCHEDULER_TRACE", None)
            os.environ.pop("OMNI_RESIDENCY_LOG", None)
            spec = importlib.util.spec_from_file_location("engine_fix_under_test", ENGINE_FIX)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)   # would raise on any patching (no vllm here)


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
            # all gates must stay closed: importing must patch nothing.
            os.environ.pop("OMNI_PARK_PATCH", None)
            os.environ.pop("OMNI_PREFETCH", None)
            os.environ.pop("OMNI_SCHEDULER_TRACE", None)
            os.environ.pop("OMNI_RESIDENCY_LOG", None)
            spec = importlib.util.spec_from_file_location("park_patch_under_test", ENGINE_PATCH)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        self.assertEqual(module.WARMUP_REQ_PREFIX, f"s{WARMUP_SESSION}e")


if __name__ == "__main__":
    unittest.main()
