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
            base | {"scheduler.log", "per_request.log", "per_iteration.log"},
        )

    def test_manifest_records_slots_and_matches_baseline_stack(self) -> None:
        # The two engines must be compared on an identical stack: same model
        # geometry and workload constants as baseline, plus the slots knob.
        manifest = ConveyorConfig(trace=True).manifest_config()
        self.assertEqual(manifest["engine"]["slots"], 8)
        self.assertEqual(manifest["workload"]["period_ms"], 2000)
        self.assertEqual(manifest["model"]["kv_geometry"]["bytes_per_token"], 57344)


if __name__ == "__main__":
    unittest.main()
