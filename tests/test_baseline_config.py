from __future__ import annotations

import unittest

from experiments.baseline.config import BaselineConfig


class BaselineConfigTests(unittest.TestCase):
    def test_worker_python_venv_path_is_not_resolved(self) -> None:
        # Python discovers pyvenv.cfg through the invoked venv path; resolving
        # the symlink would break site-packages discovery.
        self.assertTrue(str(BaselineConfig().worker_python).endswith(".venv-vllm023/bin/python"))

    def test_required_artifacts_matrix(self) -> None:
        # Observation switches change the required evidence, never the mode.
        base = {"client.json", "client.txt", "gateway.log", "gpu.csv", "kv.log", "worker.log"}
        self.assertEqual(set(BaselineConfig(mode="vanilla").required_artifact_names()), base)
        self.assertEqual(
            set(BaselineConfig(mode="vanilla", trace=True).required_artifact_names()),
            base | {"scheduler.log"},
        )
        self.assertEqual(
            set(BaselineConfig(mode="paringest", trace=True).required_artifact_names()),
            base | {"scheduler.log", "per_request.log", "per_iteration.log"},
        )

    def test_manifest_config_sections(self) -> None:
        # period_ms is a cross-module contract: tracekit reads it back out of
        # each run's manifest to synthesize ticks.
        manifest = BaselineConfig(trace=True, sessions=16).manifest_config()
        self.assertEqual(manifest["workload"]["period_ms"], 2000)
        self.assertEqual(manifest["workload"]["sessions"], 16)
        self.assertEqual(manifest["model"]["kv_geometry"]["bytes_per_token"], 57344)
        self.assertTrue(manifest["observations"]["per_request"])


if __name__ == "__main__":
    unittest.main()
