"""Admission control & schedulability test (RESEARCH_PLAN §4.2).

A new session is admitted only if, jointly:
  (timing)  every frame's EDF-batched execution of due sessions finishes within
            their deadlines, even under the worst age-mix the policy permits; and
  (memory)  the sum of resident KV budgets fits HBM (minus weights).

The single variable ``B_i`` (per-session KV budget) appears in *both* constraints —
that coupling is the core of the contribution. We implement two schedulability
tests and let experiments compare them (Goal G5: predicted vs measured MSCS):

  * worst-case (plateau): treat every session at its ceiling C_i^max = C(B_i).
    Conservative; admits fewer; never misses.
  * age-aware: integrate the actual age-mix the arrival process produces; tighter;
    admits more; must bound the co-aging transient.

The timing model is the *batched* cost model: within a frame, sessions whose tick
is due are formed into one micro-batch whose cost is
``CostModel.predict_batch(lengths)``. Feasibility means that, frame by frame, the
batch finishes before the earliest deadline among its members. With a common frame
budget F and homogeneous period, the binding condition is simply

    predict_batch(lengths_due) <= F   (the frame budget)

for the worst-case lengths the population can present in one frame.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np

from .cost_model import CostModel
from .session import PeriodicSession


@dataclass
class AdmissionConfig:
    hbm_kv_bytes: float            # HBM available for KV (total - weights - workspace)
    frame_budget_s: float          # F: per-tick wall-clock deadline
    safety: float = 0.90           # use only this fraction of the frame budget
    mode: str = "age_aware"        # "worst_case" | "age_aware"
    assumed_age_s: float = float("inf")  # age-aware: characteristic operating age of
                                         # the workload (sessions of mean life m live on
                                         # the saturating ramp at a<m << fill-time, §1.5)
    guard_horizon_s: float = 0.0         # lookahead mode: project each session forward
                                         # by this horizon (reserves ramp headroom).
                                         # Set adaptively to the churn timescale: large
                                         # under low churn (-> worst-case, co-aging-safe),
                                         # small under high churn (-> age-aware).
    talk_fraction: float = 1.0           # silence-aware: only this fraction of admitted
                                         # sessions talk (and thus compute) in a frame;
                                         # silence exploitation lets us admit ~1/f more


@dataclass
class AdmissionResult:
    admit: bool
    reason: str
    predicted_frame_ms: float
    frame_budget_ms: float
    kv_used_bytes: float
    kv_cap_bytes: float
    n_sessions: int


class AdmissionController:
    def __init__(self, cost: CostModel, cfg: AdmissionConfig):
        self.cost = cost
        self.cfg = cfg

    # ---- WCET projection -----------------------------------------------------
    def _projected_lengths(self, sessions: Sequence[PeriodicSession]) -> list:
        """Resident length to assume for each session in the schedulability test.

        * worst_case (plateau): every session at its KV-budget ceiling B_i — a safe
          upper bound; conservative, may under-admit.
        * age_aware: every session at the context it reaches by the workload's
          *characteristic operating age* ``assumed_age_s``, clamped to B_i. For
          short sessions (life << fill-time) this is well below the plateau, so the
          test admits more — the tightening of §4.2 — while staying safe as long as
          the operating age holds (enforced by churn / the degradation ladder)."""
        if self.cfg.mode == "worst_case":
            return [s.kv_budget_tokens for s in sessions]
        if self.cfg.mode == "lookahead":
            # co-aging-safe: project each session forward from its CURRENT length by
            # the guard horizon (reserves headroom for imminent aging). As the horizon
            # -> fill-to-budget time every session projects to the plateau == worst
            # case (safe under co-aging); a short horizon -> near age-aware.
            h = self.cfg.guard_horizon_s
            return [int(min(s.length_tokens + s.token_rate * h, s.kv_budget_tokens))
                    for s in sessions]
        a = self.cfg.assumed_age_s
        if a == float("inf"):
            return [s.kv_budget_tokens for s in sessions]
        return [int(min(s.token_rate * a, s.kv_budget_tokens)) for s in sessions]

    def predicted_frame_ms(self, sessions: Sequence[PeriodicSession],
                           horizon_s: float = 0.0) -> float:
        """Predicted per-frame batched latency (ms) for this population, with all
        due ticks phase-aligned into one frame (single-accelerator worst case).

        Silence-aware: only ``talk_fraction`` of admitted sessions talk (compute) in
        a frame, so the batch the controller must fit is the heaviest expected
        talker subset. We size it as the ``talk_fraction`` longest-projected sessions
        (a conservative high-load talker mix), which lets silence admit ~1/f more."""
        if not sessions:
            return 0.0
        lengths = self._projected_lengths(sessions)
        f = self.cfg.talk_fraction
        if f < 1.0:
            lengths = sorted(lengths, reverse=True)
            k = max(1, int(round(len(lengths) * f)))
            lengths = lengths[:k]
        return self.cost.predict_batch(lengths)

    # ---- the test ------------------------------------------------------------
    def feasible(self, sessions: Sequence[PeriodicSession],
                 horizon_s: float = 0.0) -> AdmissionResult:
        cfg = self.cfg
        frame_ms = self.predicted_frame_ms(sessions, horizon_s)
        budget_ms = cfg.frame_budget_s * 1000.0 * cfg.safety
        kv_used = sum(s.budget_bytes for s in sessions)
        timing_ok = frame_ms <= budget_ms
        mem_ok = kv_used <= cfg.hbm_kv_bytes
        admit = timing_ok and mem_ok
        if admit:
            reason = "ok"
        elif not timing_ok and not mem_ok:
            reason = "timing+memory"
        elif not timing_ok:
            reason = "timing"
        else:
            reason = "memory"
        return AdmissionResult(
            admit=admit, reason=reason, predicted_frame_ms=frame_ms,
            frame_budget_ms=budget_ms, kv_used_bytes=kv_used,
            kv_cap_bytes=cfg.hbm_kv_bytes, n_sessions=len(sessions),
        )

    def try_admit(self, current: Sequence[PeriodicSession],
                  new: PeriodicSession, horizon_s: float = 0.0) -> AdmissionResult:
        """Admit ``new`` iff the population stays feasible with it added."""
        return self.feasible(list(current) + [new], horizon_s)

    # ---- capacity prediction (Goal G5) (placeholder anchor) -----------------
    def predict_capacity(self, proto: PeriodicSession, max_n: int = 4096,
                         horizon_s: float = 0.0) -> int:
        """Max number of homogeneous ``proto`` sessions admissible under both
        constraints. Used to plot predicted-vs-measured MSCS."""
        lo, hi = 0, max_n
        # exponential growth then binary search on feasibility (monotone in N).
        def ok(n):
            sessions = [proto] * n
            return self.feasible(sessions, horizon_s).admit
        if not ok(1):
            return 0
        while ok(hi) and hi < max_n:
            lo, hi = hi, min(max_n, hi * 2)
        lo2, hi2 = lo, hi
        while lo2 < hi2:
            mid = (lo2 + hi2 + 1) // 2
            if ok(mid):
                lo2 = mid
            else:
                hi2 = mid - 1
        return lo2


class IncrementalAdmissionController:
    """O(1)-per-arrival worst-case admission via running sums.

    The worst-case (plateau) schedulability test is
        base + per_session * N + alpha * sum_i B_i  <=  F * safety,
    and the memory test is  sum_i (B_i * bytes_i) <= HBM. Both are linear in the
    population, so maintaining the running sums (N, sum_B_tokens, sum_bytes) makes
    each admit/depart O(1) instead of re-scanning all N sessions. Decisions are
    identical to ``AdmissionController(mode='worst_case')``; this is the scalable
    online form for thousands of sessions.
    """

    def __init__(self, cost: CostModel, cfg: AdmissionConfig):
        self.cost = cost
        self.cfg = cfg
        self.n = 0
        self.sum_B_tokens = 0       # Σ B_i (plateau lengths)
        self.sum_bytes = 0.0        # Σ resident budget bytes

    def _frame_ms(self, n, sum_B):
        c = self.cost
        return (c.batch_base + c.batch_per_session * n + c.batch_alpha * sum_B) * c.tail_factor

    def would_admit(self, new: PeriodicSession) -> bool:
        budget_ms = self.cfg.frame_budget_s * 1000.0 * self.cfg.safety
        nB = self.sum_B_tokens + new.kv_budget_tokens
        timing_ok = self._frame_ms(self.n + 1, nB) <= budget_ms
        mem_ok = (self.sum_bytes + new.budget_bytes) <= self.cfg.hbm_kv_bytes
        return timing_ok and mem_ok

    def admit(self, new: PeriodicSession) -> bool:
        if not self.would_admit(new):
            return False
        self.n += 1
        self.sum_B_tokens += new.kv_budget_tokens
        self.sum_bytes += new.budget_bytes
        return True

    def depart(self, s: PeriodicSession):
        self.n = max(0, self.n - 1)
        self.sum_B_tokens = max(0, self.sum_B_tokens - s.kv_budget_tokens)
        self.sum_bytes = max(0.0, self.sum_bytes - s.budget_bytes)
