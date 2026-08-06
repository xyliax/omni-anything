"""Metronome real serving engine — a stateful, multi-tenant GPU decode loop.

This is the *actual serving system*, not the simulator: it holds persistent,
growing per-session KV on the GPU and, every frame, executes a real transformer
tick (QKV projection, paged attention over the resident KV via FlashAttention's
production decode kernel `flash_attn_with_kvcache`, output projection, FFN/MoE) for
the batch of due sessions, measuring the real wall-clock latency and accounting
real deadline misses. The scheduler, admission controller, KV manager and
degradation ladder drive this real execution.

Capacity/timing — the headline serving metrics — depend on the model *architecture*
(layer count, head config, FFN width → compute and KV-read bandwidth), not on the
weight *values*; weights are random (the engine measures time, not token quality —
quality-under-load is the one place a proxy is used, see docs).

Measurement frugality on a shared GPU: per the same equivalence `TickKernel` uses for
weights, the engine allocates **one representative layer's** KV cache and reads it
`num_layers` times per tick — identical aggregate bandwidth and compute to a full
L-layer cache, but L× less memory, so capacity-relevant concurrency fits a modest
GPU window. The *reported* KV footprint uses the true L-layer size.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Optional

import torch
import torch.nn.functional as F

from flash_attn import flash_attn_with_kvcache

from .models import ModelFacts


@dataclass
class FrameMeasure:
    frame_idx: int
    n_exec: int
    total_kv_tokens: int
    latency_ms: float
    budget_ms: float
    missed: int

    @property
    def over_budget(self) -> bool:
        return self.latency_ms > self.budget_ms


class ServingEngine:
    """Real multi-tenant decode engine for one model config on one GPU."""

    def __init__(self, facts: ModelFacts, max_sessions: int, max_budget_tokens: int,
                 device: str = "cuda", dtype=torch.bfloat16):
        self.f = facts
        self.device = device
        self.dtype = dtype
        self.max_sessions = max_sessions
        self.max_budget = max_budget_tokens
        H = facts.hidden_dim
        self.nq, self.nkv, self.hd = facts.num_q_heads, facts.num_kv_heads, facts.head_dim
        qd, kvd = self.nq * self.hd, self.nkv * self.hd
        g = torch.Generator(device=device).manual_seed(0)
        s = 0.02
        # one layer's weights, reused across layers (timing-equivalent, memory-frugal)
        self.Wqkv = torch.randn(H, qd + 2*kvd, device=device, dtype=dtype, generator=g) * s
        self.Wo = torch.randn(qd, H, device=device, dtype=dtype, generator=g) * s
        self.W1 = torch.randn(H, facts.ffn_dim, device=device, dtype=dtype, generator=g) * s
        self.W2 = torch.randn(facts.ffn_dim, H, device=device, dtype=dtype, generator=g) * s
        # one representative layer's KV cache, read num_layers times per tick
        self.k_cache = torch.zeros(max_sessions, max_budget_tokens, self.nkv, self.hd,
                                   device=device, dtype=dtype)
        self.v_cache = torch.zeros(max_sessions, max_budget_tokens, self.nkv, self.hd,
                                   device=device, dtype=dtype)
        self.lengths = torch.zeros(max_sessions, dtype=torch.int32, device=device)
        self.budgets = torch.full((max_sessions,), max_budget_tokens, dtype=torch.int32,
                                  device=device)
        self.qd = qd
        self.kvd = kvd

    def reset(self, lengths=None):
        self.lengths.zero_()
        if lengths is not None:
            self.lengths[:len(lengths)] = torch.tensor(lengths, dtype=torch.int32,
                                                       device=self.device)

    @torch.inference_mode()
    def _tick(self, N: int, n_new: int):
        """Execute one real frame tick for the first N sessions; returns nothing
        (caller times it). Reads each layer's attention over the resident KV."""
        f = self.f
        kc = self.k_cache[:N]
        vc = self.v_cache[:N]
        seqlens = self.lengths[:N]
        # write this frame's new K/V once into the shared cache (append at seqlens)
        x = torch.randn(N * n_new, f.hidden_dim, device=self.device, dtype=self.dtype)
        # append new tokens via a throwaway flash call on layer-0 q to advance content
        for layer in range(f.num_layers):
            qkv = x @ self.Wqkv
            q, k_new, v_new = qkv.split([self.qd, self.kvd, self.kvd], dim=-1)
            q = q.view(N, n_new, self.nq, self.hd)
            k_new = k_new.view(N, n_new, self.nkv, self.hd)
            v_new = v_new.view(N, n_new, self.nkv, self.hd)
            # paged decode attention: append new K/V at seqlens and attend over the
            # full resident KV (the production kernel). Only the first layer actually
            # advances the cache content; all layers pay the same attention read.
            append_kv = (k_new, v_new) if layer == 0 else (None, None)
            out = flash_attn_with_kvcache(
                q, kc, vc, k=append_kv[0], v=append_kv[1],
                cache_seqlens=seqlens, causal=True)
            out = out.view(N * n_new, self.qd)
            x = x + out @ self.Wo
            h = x
            for _ in range(max(1, f.active_experts)):
                h = h + F.gelu(x @ self.W1) @ self.W2
            x = h
        return x

    @torch.inference_mode()
    def step_active(self, active_rows, n_new: int):
        """Execute one real frame tick over an explicit set of active cache rows
        (supports churn without compaction, via FlashAttention's cache_batch_idx).
        Returns measured latency (ms). Advances each active row's length."""
        f = self.f
        M = len(active_rows)
        if M == 0:
            return 0.0
        idx = torch.as_tensor(active_rows, dtype=torch.int32, device=self.device)
        seqlens = self.lengths[idx]
        st, en = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        torch.cuda.synchronize()
        st.record()
        x = torch.randn(M * n_new, f.hidden_dim, device=self.device, dtype=self.dtype)
        for layer in range(f.num_layers):
            qkv = x @ self.Wqkv
            q, k_new, v_new = qkv.split([self.qd, self.kvd, self.kvd], dim=-1)
            q = q.view(M, n_new, self.nq, self.hd)
            k_new = k_new.view(M, n_new, self.nkv, self.hd)
            v_new = v_new.view(M, n_new, self.nkv, self.hd)
            kk, vv = (k_new, v_new) if layer == 0 else (None, None)
            out = flash_attn_with_kvcache(
                q, self.k_cache, self.v_cache, k=kk, v=vv,
                cache_seqlens=seqlens, cache_batch_idx=idx, causal=True)
            out = out.view(M * n_new, self.qd)
            x = x + out @ self.Wo
            h = x
            for _ in range(max(1, f.active_experts)):
                h = h + F.gelu(x @ self.W1) @ self.W2
            x = h
        en.record(); torch.cuda.synchronize()
        # advance resident length (cap at budget; sliding-window eviction on overflow)
        new_len = torch.clamp(self.lengths[idx] + n_new, max=self.max_budget)
        self.lengths[idx] = new_len
        return st.elapsed_time(en)

    @torch.inference_mode()
    def serve_cohort(self, N: int, n_frames: int, n_new: int = None,
                     start_lengths=None, grow: bool = True, warmup: int = 5,
                     evict_at_budget: bool = True):
        """Serve N persistent sessions for n_frames, growing the KV each frame
        (aging). Returns per-frame measured latency (ms). This is the real system's
        latency-vs-age / capacity measurement."""
        f = self.f
        if n_new is None:
            n_new = max(1, int(round(f.tokens_per_tick)))
        self.reset(start_lengths)
        # warmup (kernel autotune / clocks)
        for _ in range(warmup):
            self._tick(N, n_new)
        torch.cuda.synchronize()
        st, en = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        lats = []
        for fi in range(n_frames):
            st.record()
            self._tick(N, n_new)
            en.record()
            torch.cuda.synchronize()
            lats.append(st.elapsed_time(en))
            if grow:
                # advance resident length (cap at budget; sliding-window eviction)
                new_len = torch.clamp(self.lengths[:N] + n_new, max=self.max_budget)
                if evict_at_budget:
                    # when full, drop oldest n_new (shift) so we keep appending at budget
                    full = self.lengths[:N] + n_new > self.max_budget
                    if full.any():
                        idx = torch.where(full)[0]
                        shift = n_new
                        self.k_cache[idx, :self.max_budget-shift] = self.k_cache[idx, shift:].clone()
                        self.v_cache[idx, :self.max_budget-shift] = self.v_cache[idx, shift:].clone()
                        new_len[idx] = self.max_budget - shift
                self.lengths[:N] = new_len
        return lats


def free_gib():
    free, _ = torch.cuda.mem_get_info()
    return free / 2**30
