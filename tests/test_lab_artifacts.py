from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lab.artifacts import RunStore, scan_worker_fatal


REQUIRED = ("alpha.log", "beta.json")


class RunStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.manifest = {"started_at": "2026-08-07T08:04:52.000Z", "run_id": "run-1"}

    def tearDown(self) -> None:
        self.temporary.cleanup()

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
        # the layout guard accepts the state.
        status = self._complete_store().finalize(
            required=REQUIRED, exit_code=130, interrupted=True
        )
        self.assertEqual(status["state"], "interrupted")
        self.assertFalse(status["validation"]["valid"])


class WorkerFatalScanTests(unittest.TestCase):
    def test_fatal_signatures_are_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            log = Path(temporary) / "worker.log"
            log.write_text("... CUDA out of memory ...\n", encoding="utf-8")
            self.assertEqual(scan_worker_fatal(log), ["worker log contains a fatal error"])

    def test_optional_background_traceback_is_not_fatal(self) -> None:
        # Deliberately narrow: a background-thread traceback must NOT fail a
        # run; only the engine-fatal signatures do.
        with tempfile.TemporaryDirectory() as temporary:
            log = Path(temporary) / "worker.log"
            log.write_text(
                "Exception in thread optional-telemetry:\n"
                "Traceback (most recent call last):\n"
                "RuntimeError: platform probe failed\n"
                "streaming worker serving gRPC\n",
                encoding="utf-8",
            )
            self.assertEqual(scan_worker_fatal(log), [])


if __name__ == "__main__":
    unittest.main()
