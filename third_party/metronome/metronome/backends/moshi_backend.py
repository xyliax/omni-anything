"""Moshi backend for the Metronome Realtime API — serves the full-duplex Moshi model
through the SAME OpenAI-Realtime server as the omni models (closing the 'Moshi bypasses
the API' exception). Runs in the moshi venv (torch<2.10).

Moshi is full-duplex streaming: each 80 ms frame, Mimi encodes the incoming audio and the
LM emits one text token (inner monologue) + audio tokens. We expose that as the Backend
protocol's per-frame step_stream, maintaining persistent Mimi+LM streaming state and
resetting per user turn. One session at a time (Moshi streaming_forever(1))."""
from __future__ import annotations

from collections import deque
from typing import Sequence


class MoshiBackend:
    def __init__(self, repo: str | None = None, device: str = "cuda",
                 silence_s: float = 6.0):
        import torch
        from moshi.models import LMGen, loaders
        self.torch = torch
        self.device = device
        repo = repo or loaders.DEFAULT_REPO
        ckpt = loaders.CheckpointInfo.from_hf_repo(repo)
        self.mimi = ckpt.get_mimi(device=device)
        self.lm = ckpt.get_moshi(device=device)
        self.tok = ckpt.get_text_tokenizer()
        self.lm_gen = LMGen(self.lm, use_sampling=True, temp=0.8, temp_text=0.7)
        self.sr = int(self.mimi.sample_rate)
        self.frame = int(self.mimi.sample_rate / self.mimi.frame_rate)
        self.silence_frames = int(silence_s * self.mimi.frame_rate)
        self.mimi.streaming_forever(1)
        self.lm_gen.streaming_forever(1)
        self.model = "moshi"
        # facts (rough; only used by the server's capacity calc — we serve 1 session)
        tc = self.lm
        self._layers = int(getattr(tc, "num_layers", getattr(tc, "depth", 32)) or 32)
        self._kvbpt = 2 * 32 * 128 * self._layers * 2
        free, _ = torch.cuda.mem_get_info()
        self._hbm = free * 0.5
        # per-session streaming state
        self.queue: deque = deque()
        self.active = None
        self.first = True
        self.last_outputs: dict = {}
        self.just_finished: set = set()

    @property
    def kv_bytes_per_token(self): return self._kvbpt
    @property
    def num_layers(self): return self._layers
    @property
    def hbm_kv_bytes(self): return float(self._hbm)
    @property
    def supports_multimodal(self): return True

    def add_session(self, sid, kv_budget_tokens=0): pass

    def remove_session(self, sid):
        if self.active == sid:
            self.active = None; self.queue.clear()

    def context_len(self, sid): return 0

    def set_input(self, sid, audio=None, images=None, text="", max_tokens=128):
        import numpy as np
        self.lm_gen.reset_streaming(); self.mimi.reset_streaming()
        self.first = True; self.active = sid; self.queue.clear()
        if audio is not None:
            arr, asr = audio
            arr = np.asarray(arr, dtype="float32")
            if asr != self.sr:
                import librosa
                arr = librosa.resample(arr, orig_sr=asr, target_sr=self.sr)
            t = self.torch.tensor(arr, dtype=self.torch.float32, device=self.device).view(1, 1, -1)
        else:
            t = self.torch.zeros(1, 1, self.frame, device=self.device)
        sil = self.torch.zeros(1, 1, self.frame * self.silence_frames, device=self.device)
        full = self.torch.cat([t, sil], dim=2)
        for j in range(0, full.shape[2] - self.frame + 1, self.frame):
            self.queue.append(full[:, :, j:j + self.frame])

    def step_stream(self, due_sids: Sequence[int], max_steps: int = 1) -> float:
        import time
        t0 = time.perf_counter()
        self.last_outputs = {}; self.just_finished = set()
        sid = self.active
        if sid is None or sid not in due_sids:
            return 0.0
        toks = []
        with self.torch.no_grad():
            for _ in range(max(1, max_steps)):
                if not self.queue:
                    self.just_finished.add(sid); self.active = None; break
                ch = self.queue.popleft()
                codes = self.mimi.encode(ch)
                if self.first:
                    self.lm_gen.step(codes); self.first = False
                out = self.lm_gen.step(codes)
                if out is None:
                    continue
                tid = int(out[0, 0].item())
                if tid == self.tok.eos_id():
                    self.just_finished.add(sid); self.active = None; break
                if tid not in (0, 3):
                    toks.append(tid)
        if toks:
            self.last_outputs[sid] = toks
        return (time.perf_counter() - t0) * 1000.0

    def is_finished(self, sid): return sid in self.just_finished

    def detokenize(self, token_ids):
        out = []
        for t in token_ids or []:
            try:
                out.append(self.tok.id_to_piece(int(t)).replace("▁", " "))
            except Exception:
                pass
        return "".join(out)

    def abort(self, sid):
        if self.active == sid:
            self.active = None; self.queue.clear()

    def shutdown(self):
        try:
            del self.lm, self.mimi; self.torch.cuda.empty_cache()
        except Exception:
            pass
