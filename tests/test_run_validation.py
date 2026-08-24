"""Pin producer/consumer contracts used by run validation.

The scanners deliberately separate repository health from paper metrics:
malformed evidence and runtime failures invalidate a run, while an actual
output amount below the configured cap remains a diagnostic observation.
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
ENGINE_PATCH = ROOT / "engines" / "conveyor" / "worker" / "engine_patch" / "sitecustomize.py"
ENGINE_FIX = ROOT / "engines" / "baseline" / "worker" / "engine_fix" / "sitecustomize.py"

KV_EVENTS_HEALTHY = (
    "1755080000.000001 B req=s1e1-abcdefgh blocks=3\n"
    "1755080000.100001 E req=s1e1-abcdefgh owned_before=190 evicted=60 "
    "host_backed=60 usage_before=0.5 usage_after=0.3\n"
    "1755080000.200001 L req=s1e1-abcdefgh cpu_tok=960 gpu_tok=2048 trigger=demand\n"
    "1755080000.300001 R req=s1e1-abcdefgh trigger=demand\n"
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
        self.write("kv_events.log", KV_EVENTS_HEALTHY)
        self.write("client.json", '{"err": 0}\n')
        self.assertEqual(conveyor_issues(self.store), [])

    def test_independent_runtime_failures_are_all_reported(self) -> None:
        self.write("scheduler_errors.log", "boom\n")
        self.write(
            "worker.log",
            "2026-08-13 [stream-worker] session 3 ended: RuntimeError: unavailable\n"
            "2026-08-13 [stream-worker] KV eviction s4 RPC failed: X: y\n",
        )
        self.write("kv_events.log", KV_EVENTS_HEALTHY)
        self.write("client.json", '{"err": 2}\n')
        self.assertEqual(
            conveyor_issues(self.store),
            [
                "scheduler trace reported serialization errors",
                "1 session(s) died mid-run (see worker.log 'ended:' lines)",
                "client reported 2 session error(s)",
                "1 KV-eviction RPC failure(s) (see worker.log)",
            ],
        )

    def test_kv_event_log_without_eviction_is_an_issue(self) -> None:
        self.write(
            "kv_events.log",
            "1755080000.000001 B req=s1e1-abcdefgh blocks=3\n"
            "1755080000.200001 L req=s1e1-abcdefgh cpu_tok=960 gpu_tok=2048 trigger=demand\n",
        )
        self.assertEqual(
            conveyor_issues(self.store),
            ["KV eviction enabled but kv_events.log recorded zero evictions"],
        )

    def test_prefetch_enabled_without_prefetch_loads_is_an_issue(self) -> None:
        self.write("kv_events.log", KV_EVENTS_HEALTHY)
        self.write("manifest.json", '{"config": {"engine": {"prefetch": "push"}}}\n')
        self.assertEqual(
            conveyor_issues(self.store),
            ["prefetch enabled but kv_events.log recorded zero prefetch loads"],
        )

    def test_prefetch_loads_satisfy_the_scan(self) -> None:
        self.write(
            "kv_events.log",
            KV_EVENTS_HEALTHY
            + "1755080000.400001 L req=s1e1-abcdefgh cpu_tok=960 gpu_tok=2048 "
            "trigger=prefetch\n"
            "1755080000.500001 R req=s1e1-abcdefgh trigger=prefetch\n",
        )
        self.write("manifest.json", '{"config": {"engine": {"prefetch": "push"}}}\n')
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

    def test_output_below_cap_is_diagnostic_not_failure(self) -> None:
        self.write(
            "manifest.json",
            '{"config": {"workload": {"sessions": 2, "output_token_cap": 25}}}\n',
        )
        self.write(
            "gateway_ticks.log",
            "1755080000.000001 slot=0 n=2 deliv=1:25,2:1\n"
            "1755080002.000001 slot=0 n=2 deliv=1:0,2:4\n",
        )
        self.assertEqual(conveyor_issues(self.store), [])

    def test_empty_grid_firing_is_valid(self) -> None:
        self.write(
            "manifest.json",
            '{"config": {"workload": {"sessions": 2, "output_token_cap": 25}}}\n',
        )
        self.write(
            "gateway_ticks.log",
            "1755080000.000001 slot=0 n=0\n"
            "1755080000.250001 slot=1 n=2 deliv=1:1,2:0\n",
        )
        self.assertEqual(conveyor_issues(self.store), [])

    def test_malformed_delivery_record_is_an_issue_not_an_exception(self) -> None:
        self.write(
            "manifest.json",
            '{"config": {"workload": {"sessions": 1, "output_token_cap": 25}}}\n',
        )
        self.write("gateway_ticks.log", "1755080000.000001 slot=0 n=1 deliv=not-a-count\n")
        self.assertEqual(
            conveyor_issues(self.store),
            ["malformed conveyor delivery record in gateway_ticks.log"],
        )


class BaselineIssueScanTests(IssueScanTestCase):
    def test_healthy_run_yields_no_issues(self) -> None:
        self.write(
            "worker.log",
            "2026-08-13 [stream-worker] engine ready\n"
            "2026-08-13 [stream-worker] delivery output_token_cap=25 deliv=1:25,2:25\n",
        )
        self.write("manifest.json", '{"config": {"mode": "paringest"}}\n')
        self.write("client.json", '{"err": 0}\n')
        self.assertEqual(baseline_issues(self.store), [])

    def test_fatal_worker_and_client_errors_are_caught(self) -> None:
        self.write("worker.log", "... CUDA out of memory ...\n")
        self.write("client.json", '{"err": 1}\n')
        self.assertEqual(
            baseline_issues(self.store),
            ["worker log contains a fatal error", "client reported 1 session error(s)"],
        )

    def test_session_step_and_client_failures_are_caught(self) -> None:
        self.write(
            "worker.log",
            "session 2 ended: RuntimeError: unavailable\n"
            "delivery output_token_cap=25 deliv=1:24,2:0\n",
        )
        self.write("manifest.json", '{"config": {"mode": "paringest"}}\n')
        self.write("gateway.log", "Step error: rpc unavailable\n")
        self.write("client.json", '{"err": 0, "realtime": false}\n')
        self.assertEqual(
            baseline_issues(self.store),
            [
                "1 session(s) died mid-run (see worker.log 'ended:' lines)",
                "gateway reported 1 Step error(s)",
                "client failed real-time acceptance (realtime=false)",
            ],
        )

    def test_paringest_requires_delivery_records_but_vanilla_does_not(self) -> None:
        self.write("worker.log", "engine ready\n")
        self.write("manifest.json", '{"config": {"mode": "paringest"}}\n')
        self.assertEqual(
            baseline_issues(self.store),
            ["paringest worker produced no delivery records"],
        )
        self.write("manifest.json", '{"config": {"mode": "vanilla"}}\n')
        self.assertEqual(baseline_issues(self.store), [])

    def test_output_below_cap_is_diagnostic_not_failure(self) -> None:
        self.write("worker.log", "delivery output_token_cap=25 deliv=1:1,2:0\n")
        self.write("manifest.json", '{"config": {"mode": "paringest"}}\n')
        self.assertEqual(baseline_issues(self.store), [])

    def test_log_cannot_report_a_different_output_cap(self) -> None:
        self.write("worker.log", "delivery output_token_cap=1 deliv=1:1\n")
        self.write(
            "manifest.json",
            '{"config": {"mode": "paringest", "workload": '
            '{"sessions": 1, "output_token_cap": 25}}}\n',
        )
        self.assertEqual(
            baseline_issues(self.store),
            ["baseline output cap does not match manifest"],
        )

    def test_malformed_baseline_delivery_record_is_not_silently_skipped(self) -> None:
        self.write("worker.log", "delivery output_token_cap=25 missing-deliv-field\n")
        self.write("manifest.json", '{"config": {"mode": "paringest"}}\n')
        self.assertEqual(
            baseline_issues(self.store),
            [
                "malformed baseline delivery record in worker.log",
                "paringest worker produced no delivery records",
            ],
        )


class SharedClientHealthTests(IssueScanTestCase):
    def test_inherited_no_tick_signal_invalidates_both_systems(self) -> None:
        self.write("client.json", '{"err": 0, "starved": true}\n')
        for scanner in (baseline_issues, conveyor_issues):
            with self.subTest(scanner=scanner.__module__):
                self.assertEqual(scanner(self.store), ["client received no ticks (starved=true)"])


class InitialContextIssueScanTests(IssueScanTestCase):
    def test_timeout_invalidates_both_systems(self) -> None:
        self.write(
            "worker.log",
            "2026-08-20 [stream-worker] initialization barrier timed out (7/8 preloaded)\n",
        )
        for scanner in (baseline_issues, conveyor_issues):
            with self.subTest(scanner=scanner.__module__):
                self.assertEqual(scanner(self.store), ["worker log contains a fatal error"])


class CrossLanguageLogContractTests(unittest.TestCase):
    """Pin every first-party producer string consumed by a scanner."""

    def test_gateway_records_actual_delivery_without_a_minimum_requirement(self) -> None:
        text = GATEWAY_GO.read_text(encoding="utf-8")
        self.assertIn('fmt.Sprintf("%d:%d", s.id, len(o.Tokens))', text)
        self.assertNotIn('log.Printf("[starve]', text)

    def test_worker_prints_the_lines_the_scanner_consumes(self) -> None:
        conveyor = CONVEYOR_WORKER.read_text(encoding="utf-8")
        self.assertIn("ended: %s", conveyor)
        self.assertIn("KV eviction s%d RPC failed", conveyor)
        baseline = BASELINE_WORKER.read_text(encoding="utf-8")
        self.assertIn('log.info("delivery output_token_cap=%d deliv=%s"', baseline)

    def test_both_workers_print_the_initialization_timeout(self) -> None:
        for worker in (BASELINE_WORKER, CONVEYOR_WORKER):
            self.assertIn(
                'log.error("initialization barrier timed out',
                worker.read_text(encoding="utf-8"),
            )


class SharedObservationProducerTests(unittest.TestCase):
    """Matched systems use one observation producer."""

    def test_both_workers_use_the_shared_producer(self) -> None:
        for worker in (BASELINE_WORKER, CONVEYOR_WORKER):
            text = worker.read_text(encoding="utf-8")
            self.assertIn(
                "from infra.trace.collectors.worker_obs import perreq_logger, stat_logger_classes",
                text,
            )
            self.assertNotIn("StatLoggerBase", text)
            self.assertNotIn("def _pev", text)

    def test_both_workers_emit_the_ingest_stations(self) -> None:
        for worker in (BASELINE_WORKER, CONVEYOR_WORKER):
            text = worker.read_text(encoding="utf-8")
            for station in ("IQ", "IS", "IE", "IR", "IA"):
                self.assertIn(f'_pev("{station}"', text)


class InitialContextFixTests(unittest.TestCase):
    """Initial-context runs need the frozen-max_tokens fix."""

    def test_preloaded_worker_environment_injects_the_fix_first(self) -> None:
        from experiments.baseline.config import BaselineConfig
        from experiments.baseline.runner import worker_environment

        run_dir = Path(self.enterContext(tempfile.TemporaryDirectory()))
        preloaded = worker_environment(
            BaselineConfig(trace=True, initial_context_tokens=4096), run_dir
        )
        self.assertEqual(preloaded.get("OMNI_SESSION_MAXTOKENS_FIX"), "1")
        first = preloaded["PYTHONPATH"].split(os.pathsep)[0]
        self.assertTrue(first.endswith("engine_fix"), first)
        empty_context = worker_environment(BaselineConfig(trace=True), run_dir)
        self.assertNotIn("OMNI_SESSION_MAXTOKENS_FIX", empty_context)

    def test_fix_module_patches_nothing_when_gates_are_closed(self) -> None:
        with mock.patch.dict(os.environ):
            os.environ.pop("OMNI_SESSION_MAXTOKENS_FIX", None)
            os.environ.pop("OMNI_SCHEDULER_TRACE", None)
            os.environ.pop("OMNI_RESIDENCY_LOG", None)
            spec = importlib.util.spec_from_file_location("engine_fix_under_test", ENGINE_FIX)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)


class WarmupSentinelTests(unittest.TestCase):
    """One warmup sentinel is shared across process boundaries."""

    def test_all_declarations_agree(self) -> None:
        self.assertEqual(WARMUP_SESSION, 10**9)
        for worker in (BASELINE_WORKER, CONVEYOR_WORKER):
            self.assertIn("WARMUP_SID = 10**9", worker.read_text(encoding="utf-8"))
        with mock.patch.dict(os.environ):
            os.environ.pop("OMNI_KV_EVICTION", None)
            os.environ.pop("OMNI_PREFETCH", None)
            os.environ.pop("OMNI_SCHEDULER_TRACE", None)
            os.environ.pop("OMNI_RESIDENCY_LOG", None)
            spec = importlib.util.spec_from_file_location("engine_patch_under_test", ENGINE_PATCH)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        self.assertEqual(module.WARMUP_REQ_PREFIX, f"s{WARMUP_SESSION}e")


if __name__ == "__main__":
    unittest.main()
