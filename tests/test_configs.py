from __future__ import annotations

import unittest

from experiments.conveyor.config import ConveyorConfig


class ConveyorConfigTests(unittest.TestCase):
    def test_prefetch_requires_kv_eviction(self) -> None:
        # Without KV eviction nothing is intentionally missing from the GPU
        # cache, so a prefetch-only run would not exercise the mechanism.
        with self.assertRaises(ValueError):
            ConveyorConfig(prefetch="push")
        config = ConveyorConfig(prefetch="push", retained_prefix_blocks=128, initial_context_tokens=4096)
        self.assertEqual(config.manifest_config()["engine"]["prefetch"], "push")
        with self.assertRaises(ValueError):
            ConveyorConfig(prefetch="timer", retained_prefix_blocks=128)
