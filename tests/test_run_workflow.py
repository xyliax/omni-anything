"""Integration tests for the shared run workflow, on fake subprocesses.

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

from infra.run.workflow import Launch, RunPlan, execute


ROOT = Path(__file__).resolve().parents[1]


def bash(script: str) -> tuple[str, ...]:
    return ("/bin/bash", "-c", script)


class WorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.tmp = Path(self.temporary.name)
        self.output_root = self.tmp / "runs"
        self.run_id = "20260813_000000_workflow"
        self.run_dir = self.output_root / self.run_id
        self.ready = self.run_dir / ".worker-ready"

    def tearDown(self) -> None:
        self.temporary.cleanup()

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
            services=(Launch("service", bash("echo service; exec sleep 60"),
                             "service.log", cwd=self.tmp),),
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
        status = self.status()
        self.assertEqual(status["state"], "success")
        self.assertTrue((self.run_dir / "client.json").is_file())
        self.assertFalse(result.exists())          # moved, not copied
        self.assertFalse(self.ready.exists())      # readiness marker cleaned
        manifest = json.loads((self.run_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(
            sorted(manifest["process_commands"]), ["client", "service", "worker"]
        )

    def test_hung_client_is_killed_by_the_watchdog(self) -> None:
        started = time.monotonic()
        code, _ = execute(self.plan(bash("echo hanging; exec sleep 300"),
                                    client_timeout_s=1), ["test-argv"])
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
        client = bash(
            f'test ! -e "{scratch}"; printf \'{{"ev": []}}\' > "{scratch}"; echo fresh'
        )
        code, _ = execute(
            self.plan(client, client_scratch_results=(scratch,)), ["test-argv"]
        )
        self.assertEqual(code, 0)
        self.assertEqual(self.status()["state"], "success")
        self.assertFalse(scratch.exists())

    def test_missing_fresh_client_shard_result_fails_the_run(self) -> None:
        scratch = self.tmp / "fixed-shard.json"
        scratch.write_text("stale", encoding="utf-8")
        code, _ = execute(
            self.plan(bash("echo done"), client_scratch_results=(scratch,)),
            ["test-argv"],
        )
        self.assertNotEqual(code, 0)
        self.assertEqual(self.status()["state"], "failed")
        self.assertIn(
            "1 client shard(s) produced no fresh result",
            self.status()["validation"]["issues"],
        )
        self.assertFalse(scratch.exists())

    def test_client_aggregate_result_must_also_be_fresh(self) -> None:
        result = self.tmp / "hardcoded-client-output.json"
        result.write_text('{"err": 0}', encoding="utf-8")
        code, _ = execute(
            self.plan(bash("echo done"), client_result=result), ["test-argv"]
        )
        self.assertNotEqual(code, 0)
        self.assertEqual(self.status()["state"], "failed")
        self.assertIn(
            "client produced no fresh aggregate result",
            self.status()["validation"]["issues"],
        )
        self.assertFalse(result.exists())

    def test_worker_death_before_readiness_fails_with_terminal_status(self) -> None:
        with self.assertRaises(RuntimeError):
            execute(self.plan(bash("echo unreachable"),
                              worker=bash("echo dying; exit 3")), ["test-argv"])
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


if __name__ == "__main__":
    unittest.main()
