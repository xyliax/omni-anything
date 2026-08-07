from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "environment" / "profiles" / "cuda13_vllm023"
LOCK_PATTERN = re.compile(r"^([A-Za-z0-9_.-]+)==([^ ]+) --hash=sha256:([0-9a-f]{64})$")


class EnvironmentArtifactTests(unittest.TestCase):
    def test_lock_is_fully_pinned_and_hashed(self) -> None:
        lines = [
            line
            for line in (PROFILE / "requirements.lock").read_text().splitlines()
            if line and not line.startswith("#")
        ]
        parsed = [LOCK_PATTERN.fullmatch(line) for line in lines]
        self.assertTrue(all(parsed))
        packages = {match.group(1).lower(): match.group(2) for match in parsed if match}
        self.assertEqual(len(packages), len(lines))
        self.assertEqual(packages["vllm"], "0.23.0")
        self.assertEqual(packages["torch"], "2.11.0")
        self.assertEqual(packages["flashinfer-python"], "0.6.12")
        self.assertEqual(packages["transformers"], "4.57.6")

    def test_model_lock_uses_a_commit_hash(self) -> None:
        expected = {
            "e0_dma_interference": "Qwen/Qwen3-1.7B",
            "e1_capacity_bottleneck": "Qwen/Qwen2.5-Omni-7B",
        }
        for experiment, expected_model in expected.items():
            model, revision = (ROOT / "experiments" / experiment / "model.lock").read_text().split()
            self.assertEqual(model, expected_model)
            self.assertRegex(revision, r"^[0-9a-f]{40}$")

    def test_fix_patch_contains_the_verified_marker(self) -> None:
        patch = (PROFILE / "patches" / "vllm-0.23-fix1.patch").read_text()
        self.assertIn("METRONOME FIX 1", patch)
        self.assertIn("cu_seqlens.to(query.device", patch)


if __name__ == "__main__":
    unittest.main()
