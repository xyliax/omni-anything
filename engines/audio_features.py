"""Bound Qwen audio feature work to the current, already-resampled input.

The pinned HF processor forces max-length padding. Override that length for
each call, without mutating its shared feature extractor or changing the
model's input limit. Both first-party workers install this before AsyncLLM.
"""
from __future__ import annotations

from functools import wraps
from numbers import Real


def bounded_audio_length(audio, feature_extractor) -> int:
    """Keep the original STFT boundary and log-mel normalization semantics.

    Centered STFT windows extend n_fft // 2 samples to the right. Keeping that
    zero tail includes every window touching the signal, including masked
    frames that can affect the global log-mel maximum. Hop alignment preserves
    the attention-mask frame count for inputs not divisible by hop_length.
    At the model limit, retain the original truncation and reflection behavior.
    """
    if isinstance(audio[0], Real):
        samples = len(audio)
    else:
        samples = max(len(item) for item in audio)
    hop = feature_extractor.hop_length
    padded = ((samples + feature_extractor.n_fft // 2 + hop - 1) // hop) * hop
    return min(padded, feature_extractor.n_samples)


def install_bounded_audio_padding() -> None:
    """Install once in a worker; all per-call options remain thread-local."""
    from transformers.models.qwen2_5_omni.processing_qwen2_5_omni import Qwen2_5OmniProcessor

    original = Qwen2_5OmniProcessor.__call__
    if getattr(original, "_omni_bounded_audio_padding", False):
        return

    @wraps(original)
    def process(self, text=None, images=None, videos=None, audio=None, **kwargs):
        audio_kwargs = dict(kwargs.get("audio_kwargs") or {})
        feature = self.feature_extractor
        # Explicit alternate preprocessing options retain upstream behavior.
        # Dither would add noise to the omitted tail and change normalization.
        if (audio is not None and len(audio) and not feature.dither
                and "max_length" not in kwargs and "max_length" not in audio_kwargs
                and not kwargs.get("do_normalize", audio_kwargs.get("do_normalize", False))):
            audio_kwargs["max_length"] = bounded_audio_length(audio, feature)
            kwargs["audio_kwargs"] = audio_kwargs
        return original(self, text=text, images=images, videos=videos, audio=audio, **kwargs)

    process._omni_bounded_audio_padding = True
    Qwen2_5OmniProcessor.__call__ = process


class _BoundedWhisperFeatures:
    """Per-processor proxy; never mutate the shared extractor during a call."""
    def __init__(self, feature):
        self.feature = feature

    def __getattr__(self, name):
        # deepcopy probes an uninitialized proxy before restoring __dict__.
        return getattr(object.__getattribute__(self, 'feature'), name)

    def __call__(self, audio, **kwargs):
        if (len(audio) and not getattr(self.feature, 'dither', 0)
                and 'max_length' not in kwargs and not kwargs.get('do_normalize', False)):
            kwargs['max_length'] = bounded_audio_length(audio, self.feature)
        return self.feature(audio, **kwargs)


def install_minicpm_bounded_audio_padding():
    """Bound the vendored MiniCPM processor's max-length Whisper padding."""
    from vllm.transformers_utils.processors.minicpmo import MiniCPMOProcessor
    original = MiniCPMOProcessor.__init__
    if getattr(original, '_omni_bounded_audio_padding', False):
        return

    @wraps(original)
    def initialize(self, *args, **kwargs):
        # vLLM rebuilds a processor from the first processor's components;
        # Transformers validates the concrete feature extractor class.
        args = tuple(x.feature if isinstance(x, _BoundedWhisperFeatures) else x for x in args)
        if isinstance(kwargs.get('feature_extractor'), _BoundedWhisperFeatures):
            kwargs['feature_extractor'] = kwargs['feature_extractor'].feature
        original(self, *args, **kwargs)
        if not isinstance(self.feature_extractor, _BoundedWhisperFeatures):
            self.feature_extractor = _BoundedWhisperFeatures(self.feature_extractor)

    initialize._omni_bounded_audio_padding = True
    MiniCPMOProcessor.__init__ = initialize
