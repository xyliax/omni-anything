"""CPU contract tests; real HF numerics use the locked worker environment.

OMNI_TEST_AUDIO=1 .venv-vllm023/bin/python -m unittest tests.test_audio_features -v
"""
from __future__ import annotations

import os
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import patch

from engines.audio_features import bounded_audio_length, install_bounded_audio_padding


class AudioPaddingContractTests(unittest.TestCase):
    def test_minicpm_proxy_survives_deepcopy_and_processor_reconstruction(self):
        import copy
        from engines.audio_features import install_minicpm_bounded_audio_padding, _BoundedWhisperFeatures
        class Feature:
            n_fft, hop_length, n_samples, dither = 400, 160, 480000, 0
            def __call__(self, audio, **kwargs):
                return kwargs['max_length']
        class Processor:
            def __init__(self, feature_extractor):
                assert isinstance(feature_extractor, Feature)
                self.feature_extractor = feature_extractor
        with patch.dict(sys.modules, {'vllm.transformers_utils.processors.minicpmo':
                                     SimpleNamespace(MiniCPMOProcessor=Processor)}):
            install_minicpm_bounded_audio_padding()
            first = Processor(Feature())
            second = Processor(feature_extractor=copy.deepcopy(first.feature_extractor))
            self.assertIsInstance(second.feature_extractor, _BoundedWhisperFeatures)
            self.assertEqual(second.feature_extractor([range(32000)]), 32320)
            self.assertEqual(second.feature_extractor.n_samples, 480000)

    def test_boundary_hop_alignment_and_model_limit(self):
        feature = SimpleNamespace(n_fft=400, hop_length=160, n_samples=4800000)
        for samples in (1, 640, 31999, 32000, 32001, 64000, 4799999, 4800001):
            with self.subTest(samples=samples):
                length = bounded_audio_length([range(samples)], feature)
                self.assertLessEqual(length, feature.n_samples)
                self.assertEqual(length % feature.hop_length, 0)
                if samples + feature.n_fft // 2 < feature.n_samples:
                    self.assertGreaterEqual(length, samples + feature.n_fft // 2)
                    self.assertLess(length, samples + feature.n_fft // 2 + feature.hop_length)
        self.assertEqual(bounded_audio_length([0.] * 32000, feature), 32320)
        self.assertEqual(bounded_audio_length([range(32000), range(64000)], feature), 64320)

    def test_install_is_idempotent_and_options_are_not_shared_between_calls(self):
        class Processor:
            feature_extractor = SimpleNamespace(n_fft=400, hop_length=160, n_samples=4800000, dither=0)

            def __call__(self, **kwargs):
                return kwargs

        with patch.dict(sys.modules, {
            "transformers.models.qwen2_5_omni.processing_qwen2_5_omni":
                SimpleNamespace(Qwen2_5OmniProcessor=Processor),
        }):
            install_bounded_audio_padding()
            installed = Processor.__call__
            install_bounded_audio_padding()
            self.assertIs(Processor.__call__, installed)
            shared_options = {"return_attention_mask": True}
            processor = Processor()
            with ThreadPoolExecutor(2) as pool:
                results = list(pool.map(lambda n: processor(audio=[range(n)], audio_kwargs=shared_options),
                                        (32000, 64000)))
            self.assertEqual([r["audio_kwargs"]["max_length"] for r in results], [32320, 64320])
            self.assertEqual(shared_options, {"return_attention_mask": True})
            self.assertEqual(processor.feature_extractor.n_samples, 4800000)
            self.assertNotIn("audio_kwargs", processor(text="initial context"))
            explicit = processor(audio=[range(32000)], audio_kwargs={"max_length": 48000})
            self.assertEqual(explicit["audio_kwargs"]["max_length"], 48000)
            self.assertNotIn("max_length", processor(audio=[range(32000)],
                             audio_kwargs={"do_normalize": True})["audio_kwargs"])


@unittest.skipUnless(os.environ.get("OMNI_TEST_AUDIO") == "1", "locked HF environment required")
class RealAudioFeatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import numpy as np
        import torch
        from transformers import AutoProcessor
        from infra.run.probes import resolve_model_snapshot
        from experiments.shared import model
        from transformers.models.qwen2_5_omni.processing_qwen2_5_omni import Qwen2_5OmniProcessor

        cls.np, cls.torch = np, torch
        cls.processor = AutoProcessor.from_pretrained(
            str(resolve_model_snapshot(model.ID, model.REVISION)), local_files_only=True)
        cls.original = Qwen2_5OmniProcessor.__call__
        cls.addClassCleanup(setattr, Qwen2_5OmniProcessor, "__call__", cls.original)
        cls.old_threads = torch.get_num_threads()
        torch.set_num_threads(1)
        cls.addClassCleanup(torch.set_num_threads, cls.old_threads)
        install_bounded_audio_padding()

    def test_minimum_terminal_input_has_an_encoder_embedding(self):
        from vllm.model_executor.models.qwen2_audio import _get_feat_extract_output_lengths
        processed = self.processor(text="<|audio_bos|><|AUDIO|><|audio_eos|>",
                                   audio=[self.np.zeros(640, dtype=self.np.float32)],
                                   sampling_rate=16000, return_tensors="pt")
        _, output_lengths = _get_feat_extract_output_lengths(processed['feature_attention_mask'].sum(-1))
        self.assertTrue(bool((output_lengths > 0).all()))

    def compare(self, audio):
        kwargs = dict(text="<|audio_bos|><|AUDIO|><|audio_eos|>" * len(audio),
                      audio=audio, sampling_rate=16000, return_tensors="pt")
        expected = type(self).original(self.processor, **kwargs)
        lengths = []
        stft = self.torch.stft

        def observe(waveform, *args, **kw):
            lengths.append(waveform.shape[-1])
            return stft(waveform, *args, **kw)

        with patch.object(self.torch, "stft", observe):
            actual = self.processor(**kwargs)
        self.assertEqual(lengths, [bounded_audio_length(audio, self.processor.feature_extractor)])
        self.assertEqual(actual["input_ids"].tolist(), expected["input_ids"].tolist())
        for index in range(len(audio)):
            original_mask = expected["feature_attention_mask"][index].bool()
            mask = actual["feature_attention_mask"][index].bool()
            self.assertEqual(mask.sum(), original_mask.sum())
            self.torch.testing.assert_close(actual["input_features"][index, :, mask],
                expected["input_features"][index, :, original_mask], atol=1e-6, rtol=1e-6)

    def test_valid_features_and_audio_tokens_match_for_real_boundaries_and_batches(self):
        rng = self.np.random.default_rng(25)
        for samples in (640, 31999, 32000, 32001, 64123):
            with self.subTest(samples=samples):
                self.compare([rng.normal(0, .1, samples).astype("float32")])
        self.compare([self.np.zeros(32000, dtype="float32")])
        # An end impulse catches reflection changes and log-mel max changes
        # from frames beyond the validity mask.
        impulse = self.np.zeros(32001, dtype="float32")
        impulse[-1] = 1
        self.compare([impulse])
        self.compare([impulse, rng.normal(0, .1, 64000).astype("float32")])


@unittest.skipUnless(os.environ.get("OMNI_TEST_AUDIO") == "1", "locked HF environment required")
class RealWhisperFeatureTests(unittest.TestCase):
    def test_minicpm_valid_frames_match_without_long_zero_tail(self):
        import numpy as np
        import torch
        from transformers import WhisperFeatureExtractor
        from engines.audio_features import _BoundedWhisperFeatures

        old_threads = torch.get_num_threads()
        torch.set_num_threads(1)
        self.addCleanup(torch.set_num_threads, old_threads)
        feature = WhisperFeatureExtractor()
        bounded = _BoundedWhisperFeatures(feature)
        rng = np.random.default_rng(45)
        signals = [np.zeros(32000, dtype=np.float32),
                   rng.normal(0, .1, 31991).astype(np.float32),
                   rng.normal(0, .1, 32000).astype(np.float32)]
        impulse = np.zeros(32001, dtype=np.float32)
        impulse[-1] = 1
        signals.append(impulse)
        for signal in signals:
            with self.subTest(samples=len(signal)):
                kwargs = dict(sampling_rate=16000, padding='max_length',
                              return_attention_mask=True, return_tensors='pt')
                expected = feature([signal], **kwargs)
                actual = bounded([signal], **kwargs)
                mask = actual['attention_mask'][0].bool()
                original_mask = expected['attention_mask'][0].bool()
                self.assertEqual(mask.sum(), original_mask.sum())
                self.assertLess(actual['input_features'].shape[-1], expected['input_features'].shape[-1])
                torch.testing.assert_close(actual['input_features'][0, :, mask],
                    expected['input_features'][0, :, original_mask], atol=1e-6, rtol=1e-6)


if __name__ == "__main__":
    unittest.main()
