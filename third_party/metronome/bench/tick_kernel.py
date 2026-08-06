"""Faithful per-tick transformer kernel, timed on the real GPU (CUDA-graph path).

A serving *tick* for one session is, per layer:

  1. QKV projection over the n_new new tokens         (compute ~ n_new,  C_fixed)
  2. attention: new queries read the WHOLE resident KV (memory ~ L,      alpha*L)
  3. output projection over n_new                      (compute ~ n_new,  C_fixed)
  4. FFN / MoE over n_new (active experts)             (compute ~ n_new,  C_fixed)

Step 2 is the only term that grows with context length ``L`` and it is
memory-bound (it streams the entire KV slab through the cores once per tick) — the
saturating-ramp WCET C(L) = C_fixed + alpha*L of RESEARCH_PLAN §1.5 / §4.1.

Fidelity choices (so the measured constants reflect a *production* serving path,
not Python overhead — cf. PIPELINE S7 "kill per-tick launch overhead via CUDA
graphs"):

  * Static, pre-allocated KV buffers written in-place (no per-tick allocation),
    so the whole multi-layer tick is **captured into one CUDA graph** and replayed.
    This removes per-layer kernel-launch overhead, the dominant inflation of
    C_fixed, leaving the real compute + the real KV-read bandwidth.
  * Homogeneous-batch attention is **vectorised** into a single SDPA call across
    sessions (the realistic batched-decode path) instead of a Python per-session
    loop. The cost model is linear in *total* resident KV, so a homogeneous sweep
    fits constants that apply to mixed-age batches too.
  * One layer's weights are reused across layers and one KV buffer is read
    ``num_layers`` times — identical memory traffic and compute to distinct
    per-layer slabs, but small enough to stay polite on a shared GPU.
"""
from __future__ import annotations

import gc
import statistics
from dataclasses import dataclass
from typing import Optional

import torch
import torch.nn.functional as F

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from metronome.models import ModelFacts


@dataclass
class TickTiming:
    model: str
    batch_sessions: int
    kv_lengths: list
    n_new: int
    reps: int
    ms: list
    device: str
    graphed: bool = True

    @property
    def total_kv_tokens(self) -> int:
        return int(sum(self.kv_lengths))

    def stat(self, q: float) -> float:
        xs = sorted(self.ms)
        if not xs:
            return float("nan")
        i = min(len(xs) - 1, max(0, int(round(q * (len(xs) - 1)))))
        return xs[i]

    @property
    def p50(self) -> float: return self.stat(0.50)
    @property
    def p99(self) -> float: return self.stat(0.99)
    @property
    def mean(self) -> float: return statistics.fmean(self.ms)

    def summary(self) -> dict:
        return dict(model=self.model, batch=self.batch_sessions,
                    total_kv=self.total_kv_tokens, n_new=self.n_new,
                    p50_ms=round(self.p50, 4), p99_ms=round(self.p99, 4),
                    mean_ms=round(self.mean, 4), reps=self.reps, device=self.device)


class TickKernel:
    def __init__(self, facts: ModelFacts, device: str = "cuda", dtype=torch.bfloat16):
        self.f = facts
        self.device = device
        self.dtype = dtype
        H = facts.hidden_dim
        self.qd = facts.num_q_heads * facts.head_dim
        self.kvd = facts.num_kv_heads * facts.head_dim
        g = torch.Generator(device=device).manual_seed(0)
        self.Wqkv = torch.randn(H, self.qd + 2 * self.kvd, device=device, dtype=dtype, generator=g) * 0.02
        self.Wo = torch.randn(self.qd, H, device=device, dtype=dtype, generator=g) * 0.02
        self.W1 = torch.randn(H, facts.ffn_dim, device=device, dtype=dtype, generator=g) * 0.02
        self.W2 = torch.randn(facts.ffn_dim, H, device=device, dtype=dtype, generator=g) * 0.02

    # -- one full tick over static buffers (graph-capturable) -----------------
    def _tick_body(self, x, kv_k, kv_v, write_at):
        f = self.f
        B = kv_k.shape[0]
        n_new = x.shape[0] // B
        for _ in range(f.num_layers):
            qkv = x @ self.Wqkv
            q, k_new, v_new = qkv.split([self.qd, self.kvd, self.kvd], dim=-1)
            q = q.view(B, n_new, f.num_q_heads, f.head_dim).transpose(1, 2)  # [B,hq,n,hd]
            kn = k_new.view(B, n_new, f.num_kv_heads, f.head_dim).transpose(1, 2)
            vn = v_new.view(B, n_new, f.num_kv_heads, f.head_dim).transpose(1, 2)
            # write new K/V into the resident slab in-place (no allocation)
            kv_k[:, :, write_at:write_at + n_new, :].copy_(kn)
            kv_v[:, :, write_at:write_at + n_new, :].copy_(vn)
            o = F.scaled_dot_product_attention(q, kv_k, kv_v, enable_gqa=True)
            o = o.transpose(1, 2).reshape(B * n_new, self.qd)
            x = x + o @ self.Wo
            h = x
            for _ in range(max(1, f.active_experts)):
                h = h + F.gelu(x @ self.W1) @ self.W2
            x = h
        return x

    @torch.inference_mode()
    def _alloc(self, B, L, n_new):
        f = self.f
        x = torch.randn(B * n_new, f.hidden_dim, device=self.device, dtype=self.dtype)
        # resident slab holds L past tokens + room for the new n_new
        kv_k = torch.randn(B, f.num_kv_heads, L + n_new, f.head_dim,
                           device=self.device, dtype=self.dtype)
        kv_v = torch.randn(B, f.num_kv_heads, L + n_new, f.head_dim,
                           device=self.device, dtype=self.dtype)
        return x, kv_k, kv_v

    @torch.inference_mode()
    def time_homogeneous(self, B, L, n_new=None, reps=40, warmup=10,
                         use_graph=True) -> TickTiming:
        f = self.f
        if n_new is None:
            n_new = max(1, int(round(f.tokens_per_tick)))
        x, kv_k, kv_v = self._alloc(B, L, n_new)
        write_at = L
        graphed = False

        if use_graph:
            try:
                # warmup on a side stream (required before capture)
                s = torch.cuda.Stream()
                s.wait_stream(torch.cuda.current_stream())
                with torch.cuda.stream(s):
                    for _ in range(3):
                        x2 = self._tick_body(x, kv_k, kv_v, write_at)
                torch.cuda.current_stream().wait_stream(s)
                g = torch.cuda.CUDAGraph()
                with torch.cuda.graph(g):
                    x_out = self._tick_body(x, kv_k, kv_v, write_at)
                for _ in range(warmup):
                    g.replay()
                torch.cuda.synchronize()
                ms = []
                st, en = (torch.cuda.Event(enable_timing=True) for _ in range(2))
                for _ in range(reps):
                    st.record(); g.replay(); en.record(); torch.cuda.synchronize()
                    ms.append(st.elapsed_time(en))
                graphed = True
            except Exception as e:
                print(f"  [graph capture failed: {type(e).__name__}: {e}; eager path]")
                use_graph = False

        if not use_graph:
            for _ in range(warmup):
                self._tick_body(x, kv_k, kv_v, write_at)
            torch.cuda.synchronize()
            ms = []
            st, en = (torch.cuda.Event(enable_timing=True) for _ in range(2))
            for _ in range(reps):
                st.record(); self._tick_body(x, kv_k, kv_v, write_at); en.record()
                torch.cuda.synchronize()
                ms.append(st.elapsed_time(en))

        del x, kv_k, kv_v
        gc.collect(); torch.cuda.empty_cache()
        return TickTiming(model=f.name, batch_sessions=B, kv_lengths=[L] * B,
                          n_new=n_new, reps=reps, ms=ms,
                          device=torch.cuda.get_device_name(0), graphed=graphed)

    # back-compat helpers used by experiments ---------------------------------
    def time_tick(self, kv_lengths, n_new=None, reps=40, warmup=10,
                  use_graph=True) -> TickTiming:
        L = kv_lengths[0]
        assert all(x == L for x in kv_lengths), "use time_homogeneous for ragged"
        return self.time_homogeneous(len(kv_lengths), L, n_new=n_new, reps=reps,
                                     warmup=warmup, use_graph=use_graph)
