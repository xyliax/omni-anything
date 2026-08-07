"""Tests for the dependency-light E0 command-line entry point."""

import subprocess
import sys
import unittest


class E0CliTests(unittest.TestCase):
    def test_help_does_not_require_gpu_runtime_dependencies(self):
        completed = subprocess.run(
            [sys.executable, "-m", "experiments.e0_dma_interference.run", "--help"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("--model-revision", completed.stdout)
        self.assertIn("--output-dir", completed.stdout)


if __name__ == "__main__":
    unittest.main()
