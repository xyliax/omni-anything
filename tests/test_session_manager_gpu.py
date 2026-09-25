"""Opt-in physical KV roundtrip; run with the locked worker Python.

CUDA_VISIBLE_DEVICES=3 OMNI_TEST_CUDA=1 .venv-vllm023/bin/python \
    -m unittest tests.test_session_manager_gpu -v
"""
from __future__ import annotations

import os
import sys
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engines/conveyor/worker/engine_patch"))
from copy_service import CopyService, CudaCopyBackend


@unittest.skipUnless(os.environ.get("OMNI_TEST_CUDA") == "1", "explicit GPU test opt-in required")
class DeviceRoundtripTests(unittest.TestCase):
    def test_multilayer_discontiguous_blocks_roundtrip_and_preserve_other_destinations(self):
        import torch
        torch.manual_seed(17)
        # Both K and V are contained in each physical block, as in the worker.
        shape = (12, 2, 16, 4, 128)
        expected = {f"layer{i}": torch.randn(shape, dtype=torch.float16) for i in range(3)}
        gpu = {key: value.cuda() for key, value in expected.items()}
        host = {key: torch.empty_like(value, pin_memory=True) for key, value in expected.items()}
        torch.cuda.synchronize()  # establish confirmed compute before D2H
        worker = SimpleNamespace(device=torch.device("cuda:0"), gpu_kv_caches=gpu, cpu_kv_caches=host)
        observed = []
        backend = CudaCopyBackend(worker)
        backend.verify_copies = True
        service = CopyService(backend, lambda event, **fields: observed.append((event, fields)))
        self.addCleanup(service.close)
        source, backing, target = [1, 3, 7], [0, 4, 9], [2, 5, 10]
        stored = threading.Event()
        service.submit("D2H", source, backing, ["test-session"], stored.set)
        self.assertTrue(stored.wait(10), "D2H must complete without any model step")
        for key in host:
            torch.testing.assert_close(host[key][backing], expected[key][source], rtol=0, atol=0)
            gpu[key].fill_(-42)
        torch.cuda.synchronize()
        restored = threading.Event()
        service.submit("H2D", backing, target, ["test-session"], restored.set)
        self.assertTrue(restored.wait(10), "H2D must complete without any model step")
        for key in gpu:
            actual = gpu[key].cpu()
            torch.testing.assert_close(actual[target], expected[key][source], rtol=0, atol=0)
            untouched = [i for i in range(shape[0]) if i not in target]
            self.assertTrue(bool((actual[untouched] == -42).all()))
        service.close()
        submits = [fields for event, fields in observed if event == "submitted"]
        expected_bytes = len(source) * sum(v[0].numel() * v.element_size() for v in expected.values())
        self.assertEqual([r["bytes"] for r in submits], [expected_bytes, expected_bytes])
        self.assertEqual([fields['checked_bytes'] for event, fields in observed if event == 'integrity_checked'],
                         [expected_bytes, expected_bytes])


if __name__ == "__main__":
    unittest.main()
