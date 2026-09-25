import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from engines.model_inputs import audio_adapter
from experiments.conveyor.config import ConveyorConfig
from experiments.conveyor.runner import gateway_command, worker_command
from experiments.shared import model, workload


class ModelInputTests(unittest.TestCase):
    def test_model_budget_matches_generation_delivery_and_provenance_in_both_systems(self):
        with tempfile.TemporaryDirectory() as temp:
            cohort = Path(temp) / 'cohort.json'
            cohort.write_text(json.dumps([
                {'id': 'one', 'arrival_s': 0, 'duration_s': 4, 'seed': 1}]))
            for preset, expected in (('qwen25_omni', 25), ('minicpm_o45', 8)):
                for resident in (False, True):
                    with self.subTest(preset=preset, resident=resident):
                        options = ({'resident_control': True, 'cohort_manifest': str(cohort)}
                                   if resident else {'session_manager': True, 'retained_prefix_blocks': 1})
                        config = ConveyorConfig(model_preset=preset, **options)
                        with patch('experiments.conveyor.runner.resolve_model_snapshot', return_value=Path('/model')):
                            commands = (worker_command(config, Path('/ready')), gateway_command(config))
                        for command in commands:
                            self.assertEqual(int(command[command.index('--output-token-cap') + 1]), expected)
                        recorded = config.manifest_config()['workload']
                        self.assertEqual(recorded['output_token_cap'], expected)
                        self.assertEqual(recorded['period_ms'], 2000)
            self.assertEqual(workload.manifest(2, 4)['output_token_cap'], 25)

    def test_qwen_prompt_preserved_and_minicpm_has_its_own_placeholder(self):
        qwen = audio_adapter('qwen25_omni')
        self.assertEqual(qwen.prompt(False), '<|audio_bos|><|AUDIO|><|audio_eos|>\n')
        self.assertEqual(qwen.prompt(True), '<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n<|audio_bos|><|AUDIO|><|audio_eos|> Listen to the audio and answer any question in it.<|im_end|>\n<|im_start|>assistant\n')
        mini = audio_adapter('minicpm_o45')
        for first in (True, False):
            self.assertEqual(mini.prompt(first).count('(<audio>./</audio>)'), 1)
            self.assertNotIn('<|AUDIO|>', mini.prompt(first))
        with self.assertRaises(ValueError):
            audio_adapter('unknown')

    def test_preset_routes_checkpoint_adapter_and_geometry_together(self):
        config = ConveyorConfig(model_preset='minicpm_o45', max_model_len=4096)
        with patch('experiments.conveyor.runner.resolve_model_snapshot', return_value=Path('/mini')) as resolve:
            cmd = worker_command(config, Path('/ready'))
        resolve.assert_called_once_with(model.PRESETS['minicpm_o45']['id'], model.PRESETS['minicpm_o45']['revision'])
        self.assertEqual(cmd[cmd.index('--model-family') + 1], 'minicpm_o45')
        manifest = config.manifest_config()
        self.assertEqual(manifest['model']['kv_geometry']['bytes_per_token'], 147456)
        self.assertIsNone(manifest['workload']['context_growth_tokens_per_period'])
        self.assertNotIn('device_name', manifest['platform'])

    def test_exact_pool_checks_selected_model_geometry_before_gpu_startup(self):
        ConveyorConfig(model_preset='qwen25_omni', max_model_len=4096, kv_pool_gib=.5)
        with self.assertRaisesRegex(ValueError, 'minicpm_o45.*needs at least'):
            ConveyorConfig(model_preset='minicpm_o45', max_model_len=4096, kv_pool_gib=.5)
        ConveyorConfig(model_preset='minicpm_o45', max_model_len=3072, kv_pool_gib=.5)


if __name__ == '__main__':
    unittest.main()
