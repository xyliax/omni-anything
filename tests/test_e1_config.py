from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from experiments.e1_capacity_bottleneck.artifacts import ArtifactStore, required_artifacts
from experiments.e1_capacity_bottleneck.config import MODES, RunConfig
from experiments.e1_capacity_bottleneck.runner import worker_environment


class RunConfigTests(unittest.TestCase):
    def test_worker_python_keeps_virtual_environment_entry_path(self) -> None:
        root = Path.cwd()
        config = RunConfig(
            root=root,
            mode="vanilla",
            worker_python=Path(".venv-vllm023/bin/python"),
        )
        self.assertEqual(config.worker_python, root / ".venv-vllm023/bin/python")
        self.assertEqual(config.client_python, str(config.worker_python))

    def config(self, **changes: object) -> RunConfig:
        values = {"root": Path.cwd(), "mode": "paringest", "trace": True, "duration_s": 60}
        values.update(changes)
        return RunConfig(**values)

    def test_mode_matrix_is_explicit(self) -> None:
        self.assertEqual(set(MODES), {"vanilla", "paringest"})
        self.assertFalse(MODES["vanilla"].parallel_ingest)
        self.assertTrue(MODES["paringest"].parallel_ingest)

    def test_paringest_trace_requires_all_observations(self) -> None:
        names = required_artifacts(self.config())
        self.assertIn("per_request.log", names)
        self.assertIn("per_iteration.log", names)
        self.assertIn("scheduler.log", names)

    def test_vanilla_trace_does_not_require_modified_worker_logs(self) -> None:
        names = required_artifacts(self.config(mode="vanilla"))
        self.assertIn("scheduler.log", names)
        self.assertNotIn("per_request.log", names)
        self.assertNotIn("per_iteration.log", names)

    def test_trace_is_independent_from_mode(self) -> None:
        names = required_artifacts(self.config(trace=False))
        self.assertNotIn("scheduler.log", names)
        self.assertNotIn("per_request.log", names)

    def test_long_run_rejects_small_max_model_length(self) -> None:
        with self.assertRaisesRegex(ValueError, "MML >= 32768"):
            self.config(duration_s=600, max_model_len=16384)

    def test_seed_tokens_require_parallel_ingest(self) -> None:
        with self.assertRaisesRegex(ValueError, "seed-tokens requires"):
            self.config(mode="vanilla", seed_tokens=1)

    def test_client_shards_must_divide_sessions(self) -> None:
        with self.assertRaisesRegex(ValueError, "evenly divisible"):
            self.config(sessions=8, client_shards=3)

    def test_output_root_can_be_outside_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config = self.config(output_root=Path(temporary))
            self.assertEqual(config.output_root, Path(temporary).resolve())

    def test_trace_injection_uses_shared_observability_package(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = self.config(root=Path.cwd(), output_root=root)
            store = ArtifactStore.create(
                root,
                "test-run",
                {"started_at": "2026-08-06T00:00:00Z"},
            )
            environment = worker_environment(config, store)
        trace_root = str(Path.cwd() / "observability" / "vllm_scheduler_trace")
        self.assertEqual(environment["OMNI_SCHEDULER_TRACE"], str(store.file("scheduler.log")))
        self.assertEqual(
            environment["OMNI_SCHEDULER_TRACE_ERRORS"],
            str(store.file("scheduler_errors.log")),
        )
        self.assertEqual(environment["PYTHONPATH"].split(":", 1)[0], trace_root)


if __name__ == "__main__":
    unittest.main()
