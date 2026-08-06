"""HuggingFace **Transformers** backend — for models vLLM/SGLang don't support.

Notably this is the path for **Moshi**: vLLM and SGLang do not support Moshi's custom
Mimi-codec dual-transformer architecture, but HF Transformers does
(`MoshiForConditionalGeneration`), and Kyutai ship their own PyTorch/MLX/Rust stacks.
Metronome's control layer (deadline-aware admission + periodic-session scheduling +
KV budget) wraps any of them through the same ``Backend`` protocol; this adapter uses
Transformers with a real, persistent, batched KV cache.

For the capacity / timing measurement it serves a *uniform-length cohort* (the
worst-case plateau), which batches cleanly with no padding: one real batched forward
per tick over all sessions, KV persisted in a ``DynamicCache``.
"""
from __future__ import annotations

from typing import Sequence

import torch


class TransformersBackend:
    def __init__(self, model_id: str, dtype=torch.bfloat16, device: str = "cuda",
                 trust_remote_code: bool = True, hbm_kv_gib: float | None = None):
        from transformers import AutoModelForCausalLM, AutoConfig
        self.model_id = model_id
        self.device = device
        self.dtype = dtype
        cfg = AutoConfig.from_pretrained(model_id, trust_remote_code=trust_remote_code)
        tc = getattr(cfg, "text_config", None) or cfg
        self._layers = int(getattr(tc, "num_hidden_layers", 32))
        n_q = int(getattr(tc, "num_attention_heads", 32))
        n_kv = int(getattr(tc, "num_key_value_heads", n_q))
        head_dim = int(getattr(tc, "head_dim", getattr(tc, "hidden_size", 4096) // n_q))
        self.vocab = int(getattr(tc, "vocab_size", 32000))
        self._kv_bytes_per_token = 2 * n_kv * head_dim * self._layers * 2
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id, torch_dtype=dtype, trust_remote_code=trust_remote_code).to(device).eval()
        free, _ = torch.cuda.mem_get_info()
        self._hbm = (hbm_kv_gib * 2**30) if hbm_kv_gib else free * 0.9

    @property
    def kv_bytes_per_token(self) -> int: return self._kv_bytes_per_token
    @property
    def num_layers(self) -> int: return self._layers
    @property
    def hbm_kv_bytes(self) -> float: return float(self._hbm)

    @torch.inference_mode()
    def serve_cohort(self, N: int, L: int, n_frames: int, n_new: int = 1,
                     warmup: int = 3):
        """Serve N persistent sessions at a uniform resident length L; returns the
        measured per-tick latency (ms) of ``n_frames`` real batched forwards (KV
        persisted across ticks in a DynamicCache)."""
        from transformers import DynamicCache
        g = torch.Generator(device=self.device).manual_seed(0)
        cache = DynamicCache()
        ids = torch.randint(0, self.vocab, (N, max(1, L)), device=self.device, generator=g)
        self.model(input_ids=ids, use_cache=True, past_key_values=cache)
        for _ in range(warmup):
            new = torch.randint(0, self.vocab, (N, n_new), device=self.device, generator=g)
            self.model(input_ids=new, past_key_values=cache, use_cache=True)
        torch.cuda.synchronize()
        st, en = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        lats = []
        for _ in range(n_frames):
            new = torch.randint(0, self.vocab, (N, n_new), device=self.device, generator=g)
            st.record()
            self.model(input_ids=new, past_key_values=cache, use_cache=True)
            en.record(); torch.cuda.synchronize()
            lats.append(st.elapsed_time(en))
        del cache
        torch.cuda.empty_cache()
        return lats

    def shutdown(self):
        try:
            del self.model
            torch.cuda.empty_cache()
        except Exception:
            pass
