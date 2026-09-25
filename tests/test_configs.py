from __future__ import annotations

import unittest
import json
import tempfile
from pathlib import Path

from experiments.conveyor.config import ConveyorConfig


class ConveyorConfigTests(unittest.TestCase):
    def test_cohort_uses_manifest_count_and_first_party_client(self):
        from tests.test_residency_planner import profile
        from dataclasses import asdict
        from experiments.conveyor.runner import client_command, gateway_command, worker_environment
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            costs, cohort = root / 'costs.json', root / 'cohort.json'
            costs.write_text(json.dumps(asdict(profile())))
            cohort.write_text(json.dumps([{'id': str(i), 'arrival_s': 0, 'duration_s': 1, 'seed': i}
                                         for i in range(33)]))
            config = ConveyorConfig(session_manager=True, retained_prefix_blocks=1,
                                    admission_profile=str(costs), cohort_manifest=str(cohort))
            self.assertEqual(config.sessions, 33)
            self.assertEqual(config.client_shards, 1)
            self.assertIn('--admission', gateway_command(config))
            self.assertTrue(any(x.endswith('/cohort_client.py') for x in client_command(config, 'test')))
            self.assertEqual(worker_environment(config, root)['OMNI_ADMISSION_PROFILE'], str(costs))
            self.assertIn(str(config.root), worker_environment(config, root)['PYTHONPATH'].split(':'))
            self.assertEqual(len(config.manifest_config()['admission']['cohort']), 33)
            preloaded = ConveyorConfig(session_manager=True, retained_prefix_blocks=1,
                               admission_profile=str(costs), cohort_manifest=str(cohort), initial_context_tokens=32)
            self.assertEqual(worker_environment(preloaded, root)['OMNI_SERVICE_PRELOAD'], '1')
            from dataclasses import replace
            from experiments.conveyor.runner import worker_command
            from unittest.mock import patch
            arriving = replace(preloaded, preload_at_start=False)
            with patch('experiments.conveyor.runner.resolve_model_snapshot', return_value=Path('/model')):
                command = worker_command(arriving, root / 'ready')
            self.assertEqual(command[command.index('--preload-sessions') + 1], '0')
            self.assertEqual(worker_environment(arriving, root)['OMNI_SERVICE_PRELOAD'], '1')
            self.assertNotIn('OMNI_HOLD_KV_EVICTION', worker_environment(arriving, root))
            self.assertFalse(arriving.manifest_config()['engine']['preload_at_start'])
    def test_manager_and_gpu_trace_configuration(self) -> None:
        with self.assertRaises(ValueError):
            ConveyorConfig(session_manager=True)
        with self.assertRaises(ValueError):
            ConveyorConfig(session_manager=True, retained_prefix_blocks=128, prefetch="push")
        config = ConveyorConfig(session_manager=True, retained_prefix_blocks=128, gpu_trace=True)
        self.assertTrue(config.trace)
        self.assertIn("transfer_events.jsonl", config.required_artifact_names())
        self.assertIn("gpu_activity.json", config.required_artifact_names())
        short = ConveyorConfig(gpu_trace=True, duration_s=10)
        self.assertEqual(short.manifest_config()['observations']['gpu_trace_scope'], 'whole_business_run')
        from experiments.conveyor.runner import plan
        from unittest.mock import patch
        with patch('experiments.conveyor.runner.resolve_model_snapshot', return_value=Path('/model')):
            enabled = plan(short, 'test')
            disabled = plan(ConveyorConfig(), 'test-off')
        self.assertEqual([x.name for x in enabled.before_client], ['gpu_trace_start'])
        self.assertEqual([x.name for x in enabled.after_client], ['gpu_trace_stop'])
        self.assertFalse(disabled.before_client or disabled.after_client)
    def test_prefetch_requires_kv_eviction(self) -> None:
        # Without KV eviction nothing is intentionally missing from the GPU
        # cache, so a prefetch-only run would not exercise the mechanism.
        with self.assertRaises(ValueError):
            ConveyorConfig(prefetch="push")
        config = ConveyorConfig(prefetch="push", retained_prefix_blocks=128, initial_context_tokens=4096)
        self.assertEqual(config.manifest_config()["engine"]["prefetch"], "push")
        with self.assertRaises(ValueError):
            ConveyorConfig(prefetch="timer", retained_prefix_blocks=128)
