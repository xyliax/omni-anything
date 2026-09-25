"""Keep the cross-language lifecycle tests in the root verification command."""
import shutil
import subprocess
import unittest
from pathlib import Path


class GatewayTests(unittest.TestCase):
    def test_gateway_lifecycle_with_race_detector(self):
        root = Path(__file__).resolve().parents[1]
        go = root / '.tools/go1.22.5/bin/go'
        if not go.exists():
            found = shutil.which('go')
            if found is None:
                self.skipTest('Go toolchain is not installed')
            go = Path(found)
        result = subprocess.run([str(go), 'test', '-race', './...'], cwd=root / 'engines/conveyor/gateway',
                                capture_output=True, text=True, timeout=180)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
