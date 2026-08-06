"""Tiny, robust text-to-speech for the user simulator's voice.

Uses transformers' VITS (facebook/mms-tts-eng): one forward pass, 16 kHz mono — exactly
the rate the omni models consume — and no streaming/codec fragility. A user-simulator
voice only needs to be intelligible to the agent, which this is. (CosyVoice2 would be
higher fidelity but its weights aren't cached here and its pipeline is brittle.)
"""
from __future__ import annotations

import numpy as np


class MMSTTS:
    def __init__(self, model_id="facebook/mms-tts-eng", device="cpu"):
        import torch
        from transformers import VitsModel, AutoTokenizer
        self.torch = torch
        self.model = VitsModel.from_pretrained(model_id).to(device).eval()
        self.tok = AutoTokenizer.from_pretrained(model_id)
        self.device = device
        self.sr = int(self.model.config.sampling_rate)

    def say(self, text: str) -> tuple[np.ndarray, int]:
        text = (text or "").strip() or "."
        inp = self.tok(text, return_tensors="pt").to(self.device)
        with self.torch.no_grad():
            wav = self.model(**inp).waveform[0].detach().cpu().numpy().astype("float32")
        peak = float(np.max(np.abs(wav))) or 1.0
        return (wav / peak * 0.95).astype("float32"), self.sr
