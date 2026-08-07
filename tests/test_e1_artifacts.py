from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from experiments.e1_capacity_bottleneck.artifacts import ArtifactStore, make_run_id, required_artifacts
from experiments.e1_capacity_bottleneck.config import RunConfig


class ArtifactStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.config = RunConfig(
            root=Path.cwd(),
            mode="paringest",
            trace=True,
            duration_s=10,
            output_root=self.root,
        )
        self.manifest = {"started_at": "2026-08-06T08:04:52.000Z", "run_id": "run-1"}

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_run_id_is_sortable_and_descriptive(self) -> None:
        now = datetime(2026, 8, 6, 8, 4, 52, 123456, tzinfo=timezone.utc)
        run_id = make_run_id(self.config, "3139eab77b7e", now)
        self.assertEqual(
            run_id,
            "20260806T080452.123456Z_e1_paringest_trace_n8_p2000_mml32768_seed0_3139eab",
        )

    def test_existing_run_directory_is_never_reused(self) -> None:
        ArtifactStore.create(self.root, "run-1", self.manifest)
        with self.assertRaises(FileExistsError):
            ArtifactStore.create(self.root, "run-1", self.manifest)

    def test_success_requires_all_nonempty_artifacts(self) -> None:
        store = ArtifactStore.create(self.root, "run-1", self.manifest)
        for name in required_artifacts(self.config):
            store.file(name).write_text("evidence\n", encoding="utf-8")
        store.file("client.json").write_text('{"err": 0}\n', encoding="utf-8")
        status = store.finalize(self.config, exit_code=0)
        self.assertEqual(status["state"], "success")
        self.assertTrue(status["validation"]["valid"])
        self.assertEqual(len(status["artifacts"]["client.json"]["sha256"]), 64)

    def test_missing_artifacts_turn_zero_exit_into_failure(self) -> None:
        store = ArtifactStore.create(self.root, "run-1", self.manifest)
        status = store.finalize(self.config, exit_code=0)
        self.assertEqual(status["state"], "failed")
        self.assertIn("client.json", status["validation"]["missing"])
        on_disk = json.loads(store.file("status.json").read_text(encoding="utf-8"))
        self.assertEqual(on_disk["state"], "failed")

    def test_scheduler_error_log_invalidates_run(self) -> None:
        config = RunConfig(
            root=Path.cwd(),
            mode="vanilla",
            trace=True,
            duration_s=10,
            output_root=self.root,
        )
        store = ArtifactStore.create(self.root, "run-1", self.manifest)
        for name in required_artifacts(config):
            store.file(name).write_text("evidence\n", encoding="utf-8")
        store.file("client.json").write_text('{"err": 0}\n', encoding="utf-8")
        store.file("scheduler_errors.log").write_text("{}\n", encoding="utf-8")
        status = store.finalize(config, exit_code=0)
        self.assertEqual(status["state"], "failed")

    def test_worker_fatal_error_invalidates_run(self) -> None:
        store = ArtifactStore.create(self.root, "run-1", self.manifest)
        for name in required_artifacts(self.config):
            store.file(name).write_text("evidence\n", encoding="utf-8")
        store.file("client.json").write_text('{"err": 0}\n', encoding="utf-8")
        store.file("worker.log").write_text("CUDA out of memory\n", encoding="utf-8")
        status = store.finalize(self.config, exit_code=0)
        self.assertEqual(status["state"], "failed")

    def test_optional_background_traceback_is_not_a_worker_fatal(self) -> None:
        store = ArtifactStore.create(self.root, "run-1", self.manifest)
        for name in required_artifacts(self.config):
            store.file(name).write_text("evidence\n", encoding="utf-8")
        store.file("client.json").write_text('{"err": 0}\n', encoding="utf-8")
        store.file("worker.log").write_text(
            "Exception in thread optional-telemetry:\n"
            "Traceback (most recent call last):\n"
            "RuntimeError: platform probe failed\n"
            "streaming worker serving gRPC\n",
            encoding="utf-8",
        )
        status = store.finalize(self.config, exit_code=0)
        self.assertEqual(status["state"], "success")


if __name__ == "__main__":
    unittest.main()
