from __future__ import annotations

import unittest

from experiments.conveyor.config import ConveyorConfig


class ConveyorConfigTests(unittest.TestCase):
    def test_paths_point_at_real_artifacts(self) -> None:
        config = ConveyorConfig()
        self.assertTrue(config.worker_path.is_file())
        self.assertTrue(str(config.worker_python).endswith(".venv-vllm023/bin/python"))

    def test_required_artifacts_matrix(self) -> None:
        base = {
            "client.json", "client.txt", "gateway.log", "gateway_ticks.log",
            "gpu.csv", "kv.log", "worker.log",
        }
        self.assertEqual(set(ConveyorConfig().required_artifact_names()), base)
        self.assertEqual(
            set(ConveyorConfig(trace=True).required_artifact_names()),
            base | {"scheduler.log", "residency.log", "per_request.log", "per_iteration.log"},
        )
        self.assertEqual(
            set(ConveyorConfig(retained_prefix_blocks=128).required_artifact_names()),
            base | {"kv_events.log"},
        )

    def test_manifest_records_slots_and_matches_baseline_stack(self) -> None:
        # The two engines must be compared on an identical stack: same model
        # geometry and workload constants as baseline, plus the release slots.
        manifest = ConveyorConfig(trace=True).manifest_config()
        self.assertEqual(manifest["engine"]["slots"], 8)
        self.assertEqual(manifest["workload"]["period_ms"], 2000)
        self.assertEqual(manifest["model"]["kv_geometry"]["bytes_per_token"], 57344)

    def test_prefetch_requires_kv_eviction(self) -> None:
        # Without KV eviction nothing is intentionally missing from the GPU
        # cache, so a prefetch-only run would not exercise the mechanism.
        with self.assertRaises(ValueError):
            ConveyorConfig(prefetch="push")
        config = ConveyorConfig(prefetch="push", retained_prefix_blocks=128, initial_context_tokens=4096)
        self.assertEqual(config.manifest_config()["engine"]["prefetch"], "push")
        with self.assertRaises(ValueError):
            ConveyorConfig(prefetch="timer", retained_prefix_blocks=128)


if __name__ == "__main__":
    unittest.main()
