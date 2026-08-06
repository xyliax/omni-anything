"""MetronomeServer — the developer-facing control layer.

Wrap any :class:`~metronome.backends.base.Backend` (vLLM, the native engine, or a
future SGLang adapter) to get **deadline-aware admission control and periodic-session
scheduling** for real-time interaction serving:

    from metronome.serve import MetronomeServer
    from metronome.backends.vllm_backend import VLLMBackend

    backend = VLLMBackend("Qwen/Qwen3-1.7B", gpu_memory_utilization=0.3, max_model_len=8192)
    server  = MetronomeServer(backend, frame_budget_s=0.20, kv_budget_tokens=2048,
                              tokens_per_tick=25)
    server.calibrate()                      # fit the cost model to THIS backend+model
    if server.admit(sid=0):                 # deadline-aware admission test
        ...                                 # admitted; otherwise rejected (shed load)
    m = server.serve(n_sessions=32, n_frames=50)   # run + measured metrics
    print(m["miss_rate"], m["p99_ms"], server.mscs())

The server measures everything on the real backend; the admission test uses a cost
model *calibrated from the backend's own measured per-tick latency*.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from .cost_model import CostModel
from .admission import AdmissionController, AdmissionConfig
from .backends.base import Backend


@dataclass
class MetronomeServer:
    backend: Backend
    frame_budget_s: float
    kv_budget_tokens: int
    tokens_per_tick: int = 16
    safety: float = 0.90
    cost: Optional[CostModel] = None
    _active: set = field(default_factory=set)

    # ---- calibration: fit the cost model to the real backend ----------------
    def calibrate(self, probe_ns=(1, 2, 4, 8), context_tokens=None, reps: int = 5,
                  verbose: bool = True) -> CostModel:
        """Measure the backend's real per-tick latency across concurrency (at a fixed
        plateau context) and fit base + per_session·N + alpha·ΣL."""
        ctx = context_tokens if context_tokens is not None else self.kv_budget_tokens
        Bs, totals, ys = [], [], []
        for N in probe_ns:
            sids = list(range(10_000, 10_000 + N))
            for sid in sids:
                self.backend.add_session(sid, self.kv_budget_tokens)
            # warm the context up to the plateau
            grown = 0
            while grown < ctx:
                self.backend.step(sids, self.tokens_per_tick)
                grown += self.tokens_per_tick
            lat = np.median([self.backend.step(sids, self.tokens_per_tick) for _ in range(reps)])
            total_ctx = sum(self.backend.context_len(s) for s in sids)
            Bs.append(N); totals.append(total_ctx); ys.append(lat)
            for sid in sids:
                self.backend.remove_session(sid)
            if verbose:
                print(f"[calibrate] N={N:3d} totalctx={total_ctx:7d} latency={lat:.1f}ms")
        A = np.vstack([np.ones(len(Bs)), Bs, totals]).T
        (base, per_s, alpha), *_ = np.linalg.lstsq(A, np.array(ys), rcond=None)
        self.cost = CostModel(
            model=getattr(self.backend, "model", "backend"), device="backend",
            c_fixed=float(base), alpha=float(max(alpha, 0.0)),
            batch_base=float(base), batch_per_session=float(max(per_s, 0.0)),
            batch_alpha=float(max(alpha, 0.0)), tail_factor=1.0,
            kv_bytes_per_token=self.backend.kv_bytes_per_token)
        return self.cost

    def _admission(self) -> AdmissionController:
        if self.cost is None:
            raise RuntimeError("call calibrate() first")
        return AdmissionController(self.cost, AdmissionConfig(
            hbm_kv_bytes=self.backend.hbm_kv_bytes, frame_budget_s=self.frame_budget_s,
            safety=self.safety, mode="worst_case"))

    # ---- admission ----------------------------------------------------------
    def predicted_capacity(self) -> int:
        from .session import PeriodicSession
        from . import models
        proto = PeriodicSession(sid=0, facts=models.MOSHI, period_s=self.frame_budget_s,
                                deadline_s=self.frame_budget_s, phase_s=0.0,
                                kv_budget_tokens=self.kv_budget_tokens,
                                token_rate=self.tokens_per_tick / self.frame_budget_s)
        return self._admission().predict_capacity(proto)

    def admit(self, sid: int) -> bool:
        """Deadline-aware admission: accept ``sid`` iff the schedulability test holds
        for the resulting population. Idempotent for already-active sids."""
        if sid in self._active:
            return True
        cap = self.predicted_capacity()
        if len(self._active) + 1 > cap:
            return False
        self.backend.add_session(sid, self.kv_budget_tokens)
        self._active.add(sid)
        return True

    def release(self, sid: int):
        if sid in self._active:
            self.backend.remove_session(sid)
            self._active.discard(sid)

    # ---- serving + measurement ---------------------------------------------
    def serve(self, n_sessions: int, n_frames: int, admission: bool = True,
              warm_to_plateau: bool = True) -> dict:
        """Serve a cohort of ``n_sessions`` for ``n_frames`` on the backend; returns
        measured metrics. With ``admission`` the cohort is trimmed to the feasible
        set; without it (the throughput-greedy baseline) all run and may miss."""
        budget_ms = self.frame_budget_s * 1000.0
        admitted = []
        for sid in range(n_sessions):
            if admission and not self.admit(sid):
                continue
            if not admission:
                self.backend.add_session(sid, self.kv_budget_tokens); self._active.add(sid)
            admitted.append(sid)
        if warm_to_plateau:
            grown = 0
            while grown < self.kv_budget_tokens:
                self.backend.step(admitted, self.tokens_per_tick); grown += self.tokens_per_tick
        lats = [self.backend.step(admitted, self.tokens_per_tick) for _ in range(n_frames)]
        for sid in list(admitted):
            self.release(sid) if admission else (self.backend.remove_session(sid), self._active.discard(sid))
        lats = np.array(lats) if lats else np.array([0.0])
        misses = int(np.sum(lats > budget_ms))
        return dict(n_offered=n_sessions, n_served=len(admitted),
                    miss_rate=float(misses / max(1, len(lats))),
                    p50_ms=float(np.percentile(lats, 50)), p99_ms=float(np.percentile(lats, 99)),
                    p999_ms=float(np.percentile(lats, 99.9)), budget_ms=budget_ms)

    def mscs(self, ns=None, n_frames: int = 8, target_miss: float = 0.001) -> int:
        """Measured max sustainable concurrent sessions: the largest N whose measured
        miss-rate stays within the SLO (throughput-greedy, no admission)."""
        ns = ns or [1, 2, 4, 8, 16, 24, 32, 48, 64, 96, 128]
        best = 0
        for N in ns:
            m = self.serve(N, n_frames, admission=False, warm_to_plateau=True)
            if m["miss_rate"] <= target_miss:
                best = N
            else:
                break
        return best
