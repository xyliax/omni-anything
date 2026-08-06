"""Deadline-aware tick scheduler (RESEARCH_PLAN §2.2.2).

Frame-based: time is divided into frames of length ``F`` (the common frame budget).
Within each frame the scheduler forms a micro-batch of the sessions whose tick is
due, ordered by EDF (earliest deadline first), and executes them under the
frame-budget solver. It cannot delay chunks (they arrive on a wall clock), so the
objective is deadline satisfaction, not throughput. It exploits empty ticks
(silence / no-speak) to reclaim compute for talkers, and applies the
graceful-degradation ladder when a frame is over budget.

This scheduler is policy; the *cost* of executing a batch comes from a pluggable
callable (the fitted CostModel in simulation, or the real measured kernel in the
live harness), so the same scheduler logic is exercised in both.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence

from .session import PeriodicSession, DegradeLevel


@dataclass
class FrameResult:
    frame_idx: int
    t_start: float
    n_due: int
    n_executed: int
    n_skipped_silence: int
    n_degraded: int
    n_missed: int
    batch_ms: float
    budget_ms: float
    executed_sids: list = field(default_factory=list)
    missed_sids: list = field(default_factory=list)


class TickScheduler:
    """One accelerator's frame loop. ``cost_fn(lengths) -> ms`` returns the
    predicted/measured batched execution time for the given resident lengths."""

    def __init__(self, cost_fn: Callable[[Sequence[int]], float],
                 frame_budget_s: float, ordering: str = "edf",
                 use_silence: bool = True, use_degradation: bool = True,
                 safety: float = 1.0, deadline_aware: bool = True):
        self.cost_fn = cost_fn
        self.F = frame_budget_s
        self.ordering = ordering
        self.use_silence = use_silence
        self.use_degradation = use_degradation
        self.safety = safety
        # A deadline-aware scheduler sheds the over-budget tail so the included
        # subset meets the deadline (the shed ticks are deferred = missed). A
        # throughput-greedy engine (B0/B1) is NOT deadline-aware: it runs the whole
        # batch, so when the batch exceeds the frame, *every* included tick is late.
        self.deadline_aware = deadline_aware

    def _order(self, due: list, t: float) -> list:
        if self.ordering == "edf":   # earliest absolute deadline first
            return sorted(due, key=lambda s: s.absolute_deadline(s.ticks_done))
        if self.ordering == "fifo":
            return sorted(due, key=lambda s: s.start_t)
        if self.ordering == "lrf":  # latest-deadline-first (anti-EDF, for ablation)
            return sorted(due, key=lambda s: -s.absolute_deadline(s.ticks_done))
        return list(due)

    def run_frame(self, frame_idx: int, t: float, due: Sequence[PeriodicSession],
                  rng=None) -> FrameResult:
        budget_ms = self.F * 1000.0 * self.safety
        ordered = self._order(list(due), t)

        # Silence exploitation: a non-talk tick appends a tiny token but needs no
        # decode compute beyond housekeeping; we still must read its KV if batched,
        # but we can *defer* it (skip this frame) to reclaim compute for talkers.
        executed, skipped_silence = [], []
        if self.use_silence:
            for s in ordered:
                is_talk = True
                if rng is not None:
                    is_talk = rng.random() < s.talk_prob
                if is_talk:
                    executed.append(s)
                else:
                    skipped_silence.append(s)
        else:
            executed = ordered

        # Degradation ladder: if the batch is over budget, walk the ladder on the
        # longest-context sessions until it fits or we run out of rungs.
        n_degraded = 0
        lengths = [s.length_tokens for s in executed]
        batch_ms = self.cost_fn(lengths) if lengths else 0.0
        if self.use_degradation and batch_ms > budget_ms and executed:
            batch_ms, n_degraded, executed = self._degrade_to_fit(
                executed, budget_ms)

        # A batch completes as a unit, so an included session meets its deadline iff
        # batch_ms <= its own relative deadline. The target the batch must fit is the
        # *tightest* deadline among included sessions (heterogeneous SLAs) capped by
        # the frame budget — this is what EDF protects.
        def fit_target(sessions):
            if not sessions:
                return budget_ms
            return min(budget_ms, min(s.deadline_s * 1000.0 * self.safety for s in sessions))

        lengths = [s.length_tokens for s in executed]
        batch_ms = self.cost_fn(lengths) if lengths else 0.0
        missed = []
        if executed and batch_ms > fit_target(executed):
            if self.deadline_aware:
                # shed the loosest-deadline tail (executed is in scheduler order;
                # EDF => loosest at the end) until the kept batch fits the tightest
                # included deadline; shed ticks are deferred = missed.
                keep = list(executed)
                while keep and self.cost_fn([s.length_tokens for s in keep]) > fit_target(keep):
                    missed.append(keep.pop())
                batch_ms = self.cost_fn([s.length_tokens for s in keep]) if keep else 0.0
                executed = keep
            else:
                # throughput-greedy: run the whole batch; every included tick is late.
                missed = list(executed)
                executed = []

        for s in executed:
            s.advance()
        for s in skipped_silence:
            # silence tick: KV still grows by the (small) input token rate
            s.advance(produced_tokens=max(1, int(s.token_rate * s.period_s * 0.25)))
        for s in missed:
            s.ticks_missed += 1
            s.advance()  # the tick still happened; we just blew its deadline

        return FrameResult(
            frame_idx=frame_idx, t_start=t, n_due=len(due), n_executed=len(executed),
            n_skipped_silence=len(skipped_silence), n_degraded=n_degraded,
            n_missed=len(missed), batch_ms=batch_ms, budget_ms=budget_ms,
            executed_sids=[s.sid for s in executed],
            missed_sids=[s.sid for s in missed],
        )

    def _degrade_to_fit(self, executed, budget_ms):
        """Walk the degradation ladder on longest-context sessions to fit budget."""
        executed = sorted(executed, key=lambda s: -s.length_tokens)
        n_degraded = 0
        for level in (DegradeLevel.SHRINK_WINDOW, DegradeLevel.DROP_FRAMES,
                      DegradeLevel.QUANT, DegradeLevel.SKIP_TICK):
            for s in executed:
                cur = [x.length_tokens for x in executed]
                if self.cost_fn(cur) <= budget_ms:
                    return self.cost_fn(cur), n_degraded, executed
                if s.degrade < level:
                    s.degrade = level
                    n_degraded += 1
                    # Degradation reduces the resident KV *budget* (persistent — the
                    # eviction policy then keeps it bounded on later frames), not just
                    # this frame's length. This is the "shrink window" rung made real.
                    if level == DegradeLevel.SHRINK_WINDOW:
                        s.kv_budget_tokens = max(64, int(s.kv_budget_tokens * 0.6))
                    elif level == DegradeLevel.DROP_FRAMES:
                        s.kv_budget_tokens = max(64, int(s.kv_budget_tokens * 0.75))
                    elif level == DegradeLevel.QUANT:
                        s.quant_bytes = 1  # fp8: halves the per-token read
                        s.kv_budget_tokens = max(64, int(s.kv_budget_tokens * 0.7))
                    elif level == DegradeLevel.SKIP_TICK:
                        pass
                    s.length_tokens = min(s.length_tokens, s.kv_budget_tokens)
            cur = [x.length_tokens for x in executed]
            if self.cost_fn(cur) <= budget_ms:
                break
        return self.cost_fn([x.length_tokens for x in executed]), n_degraded, executed
