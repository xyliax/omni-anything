"""Integration tests for the shared run workflow and artifact store, on fake subprocesses.

Real experiments launch a GPU worker; these tests launch shell one-liners
with the same lifecycle: readiness file, auxiliary service, client under a
watchdog, teardown, terminal verdict.
"""

from __future__ import annotations

import json
import os
import signal
import sys
import tempfile
import time
import unittest
from pathlib import Path

from infra.run.artifacts import RunStore, scan_worker_fatal
from infra.run.workflow import Launch, RunPlan, execute


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ("alpha.log", "beta.json")


def bash(script: str) -> tuple[str, ...]:
    return ("/bin/bash", "-c", script)


class WorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.tmp = Path(temporary.name)
        self.output_root = self.tmp / "runs"
        self.run_id = "20260813_000000_workflow"
        self.run_dir = self.output_root / self.run_id
        self.ready = self.run_dir / ".worker-ready"

    def plan(
        self,
        client: tuple[str, ...],
        *,
        client_timeout_s: int = 30,
        worker: tuple[str, ...] | None = None,
        client_result: Path | None = None,
        client_scratch_results: tuple[Path, ...] = (),
        required: tuple[str, ...] = ("worker.log", "client.txt"),
    ) -> RunPlan:
        if worker is None:
            worker = bash(f'echo boot; touch "{self.ready}"; exec sleep 60')
        return RunPlan(
            experiment="workflow-test",
            run_id=self.run_id,
            root=ROOT,
            worker_python=Path(sys.executable),
            gpu=0,
            output_root=self.output_root,
            config={"kind": "synthetic"},
            worker=Launch("worker", worker, "worker.log", cwd=self.tmp),
            ready_file=self.ready,
            startup_timeout_s=10,
            services=(Launch("service", bash("echo service; exec sleep 60"), "service.log", cwd=self.tmp),),
            client=Launch("client", client, "client.txt", cwd=self.tmp),
            client_timeout_s=client_timeout_s,
            client_result=client_result,
            client_scratch_results=client_scratch_results,
            required_artifacts=required,
        )

    def status(self) -> dict:
        return json.loads((self.run_dir / "status.json").read_text(encoding="utf-8"))

    def test_success_path_moves_client_result_and_cleans_up(self) -> None:
        result = self.tmp / "hardcoded-client-output.json"
        plan = self.plan(
            bash(f'echo done; printf \'{{"err": 0}}\' > "{result}"'),
            client_result=result,
            required=("worker.log", "client.txt", "client.json"),
        )
        code, path = execute(plan, ["test-argv"])
        self.assertEqual(code, 0)
        self.assertEqual(path, self.run_dir)
        self.assertEqual(self.status()["state"], "success")
        self.assertTrue((self.run_dir / "client.json").is_file())
        self.assertFalse(result.exists())          # moved, not copied
        self.assertFalse(self.ready.exists())      # readiness marker cleaned
        manifest = json.loads((self.run_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(manifest["process_commands"]), ["client", "service", "worker"])

    def test_hung_client_is_killed_by_the_watchdog(self) -> None:
        started = time.monotonic()
        code, _ = execute(self.plan(bash("echo hanging; exec sleep 300"), client_timeout_s=1), ["test-argv"])
        self.assertNotEqual(code, 0)
        status = self.status()
        self.assertEqual(status["state"], "failed")
        self.assertTrue(
            any("watchdog" in issue for issue in status["validation"]["issues"]),
            status["validation"]["issues"],
        )
        # the whole run (manifest, startup, timeout, teardown) stays bounded
        self.assertLess(time.monotonic() - started, 30)

    def test_client_shard_results_must_be_fresh_and_are_cleaned(self) -> None:
        scratch = self.tmp / "fixed-shard.json"
        scratch.write_text("stale", encoding="utf-8")
        client = bash(f'test ! -e "{scratch}"; printf \'{{"ev": []}}\' > "{scratch}"; echo fresh')
        code, _ = execute(self.plan(client, client_scratch_results=(scratch,)), ["test-argv"])
        self.assertEqual(code, 0)
        self.assertEqual(self.status()["state"], "success")
        self.assertFalse(scratch.exists())

    def test_missing_fresh_client_shard_result_fails_the_run(self) -> None:
        scratch = self.tmp / "fixed-shard.json"
        scratch.write_text("stale", encoding="utf-8")
        code, _ = execute(self.plan(bash("echo done"), client_scratch_results=(scratch,)), ["test-argv"])
        self.assertNotEqual(code, 0)
        self.assertEqual(self.status()["state"], "failed")
        self.assertIn("1 client shard(s) produced no fresh result", self.status()["validation"]["issues"])
        self.assertFalse(scratch.exists())

    def test_client_aggregate_result_must_also_be_fresh(self) -> None:
        result = self.tmp / "hardcoded-client-output.json"
        result.write_text('{"err": 0}', encoding="utf-8")
        code, _ = execute(self.plan(bash("echo done"), client_result=result), ["test-argv"])
        self.assertNotEqual(code, 0)
        self.assertEqual(self.status()["state"], "failed")
        self.assertIn("client produced no fresh aggregate result", self.status()["validation"]["issues"])
        self.assertFalse(result.exists())

    def test_worker_death_before_readiness_fails_with_terminal_status(self) -> None:
        with self.assertRaises(RuntimeError):
            execute(self.plan(bash("echo unreachable"), worker=bash("echo dying; exit 3")), ["test-argv"])
        self.assertEqual(self.status()["state"], "failed")

    def test_sigterm_lands_as_interrupted(self) -> None:
        # the client terminates the orchestrator itself: exactly the shape of
        # an operator interrupt during an unattended run.
        code, _ = execute(
            self.plan(bash(f"kill -{int(signal.SIGTERM)} {os.getpid()}; exec sleep 60")),
            ["test-argv"],
        )
        self.assertNotEqual(code, 0)
        self.assertEqual(self.status()["state"], "interrupted")


class RunStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.manifest = {"started_at": "2026-08-07T08:04:52.000Z", "run_id": "run-1"}

    def _complete_store(self) -> RunStore:
        store = RunStore.create(self.root, "run-1", self.manifest)
        for name in REQUIRED:
            store.file(name).write_text("evidence\n", encoding="utf-8")
        return store

    def test_existing_run_directory_is_never_reused(self) -> None:
        RunStore.create(self.root, "run-1", self.manifest)
        with self.assertRaises(FileExistsError):
            RunStore.create(self.root, "run-1", self.manifest)

    def test_success_requires_all_nonempty_artifacts(self) -> None:
        status = self._complete_store().finalize(required=REQUIRED, exit_code=0)
        self.assertEqual(status["state"], "success")
        self.assertTrue(status["validation"]["valid"])
        self.assertEqual(len(status["artifacts"]["alpha.log"]["sha256"]), 64)

    def test_missing_artifacts_turn_zero_exit_into_failure(self) -> None:
        store = RunStore.create(self.root, "run-1", self.manifest)
        status = store.finalize(required=REQUIRED, exit_code=0)
        self.assertEqual(status["state"], "failed")
        self.assertIn("alpha.log", status["validation"]["missing"])
        on_disk = json.loads(store.file("status.json").read_text(encoding="utf-8"))
        self.assertEqual(on_disk["state"], "failed")

    def test_empty_artifact_counts_as_failure(self) -> None:
        store = self._complete_store()
        store.file("alpha.log").write_text("", encoding="utf-8")
        status = store.finalize(required=REQUIRED, exit_code=0)
        self.assertEqual(status["state"], "failed")
        self.assertIn("alpha.log", status["validation"]["empty"])

    def test_extra_issues_turn_zero_exit_into_failure(self) -> None:
        status = self._complete_store().finalize(
            required=REQUIRED, exit_code=0, extra_issues=["client reported 2 session error(s)"]
        )
        self.assertEqual(status["state"], "failed")

    def test_operator_interrupt_is_its_own_terminal_state(self) -> None:
        # Neither success nor a pathology: the run directory is retained and
        # the state is a valid terminal verdict.
        status = self._complete_store().finalize(required=REQUIRED, exit_code=130, interrupted=True)
        self.assertEqual(status["state"], "interrupted")
        self.assertFalse(status["validation"]["valid"])


class WorkerFatalScanTests(unittest.TestCase):
    def scan(self, text: str) -> list[str]:
        with tempfile.TemporaryDirectory() as temporary:
            log = Path(temporary) / "worker.log"
            log.write_text(text, encoding="utf-8")
            return scan_worker_fatal(log)

    def test_fatal_signatures_are_detected(self) -> None:
        self.assertEqual(self.scan("... CUDA out of memory ...\n"), ["worker log contains a fatal error"])

    def test_optional_background_traceback_is_not_fatal(self) -> None:
        # Deliberately narrow: a background-thread traceback must NOT fail a
        # run; only the engine-fatal signatures do.
        self.assertEqual(
            self.scan(
                "Exception in thread optional-telemetry:\n"
                "Traceback (most recent call last):\n"
                "RuntimeError: platform probe failed\n"
                "streaming worker serving gRPC\n"
            ),
            [],
        )
