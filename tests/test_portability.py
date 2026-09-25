import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.baseline.config import BaselineConfig
from experiments.conveyor.config import ConveyorConfig
from infra.env.verify import driver_issues, cuda_toolkit_environment
from infra.run.probes import model_cache_root, model_snapshot_issues, resolve_model_snapshot


class PortabilityTests(unittest.TestCase):
    def test_driver_only_host_uses_selected_venv_compiler_for_both_workers(self):
        from experiments.baseline.runner import worker_environment as baseline_env
        from experiments.conveyor.runner import worker_environment as conveyor_env
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            python = root / 'custom venv/bin/python'
            python.parent.mkdir(parents=True)
            python.symlink_to('/usr/bin/python3')
            toolkit = python.parent.parent / 'lib/python3.12/site-packages/nvidia/cu13'
            (toolkit / 'bin').mkdir(parents=True)
            (toolkit / 'bin/nvcc').touch()
            original = {'CUDA_HOME': '/unrelated/cuda', 'PATH': '/usr/bin'}
            env = cuda_toolkit_environment(python, original)
            self.assertEqual(env['CUDA_HOME'], str(toolkit))
            self.assertEqual(env['CUDA_PATH'], str(toolkit))
            self.assertEqual(env['PATH'].split(os.pathsep)[0], str(toolkit / 'bin'))
            self.assertIn(str(python.parent), env['PATH'].split(os.pathsep))
            self.assertEqual(original['CUDA_HOME'], '/unrelated/cuda')
            with patch.dict(os.environ, {'OMNI_WORKER_PYTHON': str(python)}):
                for config, build in ((BaselineConfig(), baseline_env), (ConveyorConfig(), conveyor_env)):
                    self.assertEqual(build(config, root)['CUDA_HOME'], str(toolkit))

    def test_single_gpu_default_and_custom_venv_reach_both_runners(self):
        with patch.dict(os.environ, {'OMNI_WORKER_PYTHON': '/mounted disk/runtime/bin/python'}):
            for config in (BaselineConfig(), ConveyorConfig()):
                self.assertEqual(config.gpu, 0)
                self.assertEqual(config.worker_python, Path('/mounted disk/runtime/bin/python'))
                self.assertEqual(config.manifest_config()['platform']['worker_python'], str(config.worker_python))

    def test_cache_precedence_and_missing_shards(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            root = Path(directory)
            os.environ['XDG_CACHE_HOME'] = str(root / 'xdg')
            self.assertEqual(model_cache_root(), root / 'xdg/huggingface/hub')
            os.environ['HF_HOME'] = str(root / 'hf')
            self.assertEqual(model_cache_root(), root / 'hf/hub')
            os.environ['HUGGINGFACE_HUB_CACHE'] = str(root / 'legacy')
            self.assertEqual(model_cache_root(), root / 'legacy')
            os.environ['HF_HUB_CACHE'] = str(root / 'cache')
            snapshot = root / 'cache/models--owner--model/snapshots/revision'
            snapshot.mkdir(parents=True)
            self.assertEqual(resolve_model_snapshot('owner/model', 'revision'), snapshot)
            for name in ('config.json', 'tokenizer_config.json', 'preprocessor_config.json', 'tokenizer.json'):
                (snapshot / name).write_text('{}')
            (snapshot / 'model.safetensors.index.json').write_text(json.dumps(
                {'weight_map': {'first': 'part1.safetensors', 'second': 'part2.safetensors'}}))
            (snapshot / 'part1.safetensors').write_bytes(b'weight')
            self.assertEqual(len(model_snapshot_issues(snapshot)), 1)
            (snapshot / 'part2.safetensors').symlink_to(root / 'not-downloaded')
            self.assertEqual(len(model_snapshot_issues(snapshot)), 1)
            (root / 'not-downloaded').write_bytes(b'weight')
            self.assertEqual(model_snapshot_issues(snapshot), [])

    def test_target_driver_accepted_and_incompatible_driver_rejected(self):
        self.assertEqual(driver_issues('595.91.07'), [])
        self.assertEqual(driver_issues('580.95.05'), [])
        self.assertTrue(driver_issues('575.64.03'))
        self.assertTrue(driver_issues('unavailable'))


if __name__ == '__main__':
    unittest.main()
