"""The real-time capacity/jitter metrics (RESEARCH_PLAN §6.5 / Contribution 3).

Replaces tokens/sec + TTFT with the metrics that matter for periodic sessions:
  * deadline-miss rate (per tick) — the SLO.
  * jitter: p50/p99/p999 per-tick latency — the tail is the story.
  * MSCS: max sustainable concurrent sessions at a target miss rate.
  * cost: $/session-hour and GPU-hours per 1000 session-minutes at fixed SLO.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

import numpy as np


def percentile(xs: Sequence[float], q: float) -> float:
    if len(xs) == 0:
        return float("nan")
    return float(np.percentile(np.asarray(xs, dtype=float), q))


@dataclass
class RunMetrics:
    """Aggregate metrics for one serving run (one config, one load level)."""
    n_sessions: int
    n_ticks: int
    n_missed: int
    tick_latencies_ms: list = field(default_factory=list)
    frame_budget_ms: float = 0.0
    # quality / degradation
    n_degraded: int = 0
    quality_retained: float = 1.0   # mean attention-mass retained (1.0 = full)

    @property
    def miss_rate(self) -> float:
        return self.n_missed / self.n_ticks if self.n_ticks else 0.0

    @property
    def p50(self) -> float: return percentile(self.tick_latencies_ms, 50)
    @property
    def p99(self) -> float: return percentile(self.tick_latencies_ms, 99)
    @property
    def p999(self) -> float: return percentile(self.tick_latencies_ms, 99.9)
    @property
    def mean_ms(self) -> float:
        return float(np.mean(self.tick_latencies_ms)) if self.tick_latencies_ms else 0.0

    def summary(self) -> dict:
        return dict(
            n_sessions=self.n_sessions, n_ticks=self.n_ticks, n_missed=self.n_missed,
            miss_rate=round(self.miss_rate, 6), p50_ms=round(self.p50, 4),
            p99_ms=round(self.p99, 4), p999_ms=round(self.p999, 4),
            mean_ms=round(self.mean_ms, 4), frame_budget_ms=self.frame_budget_ms,
            n_degraded=self.n_degraded, quality_retained=round(self.quality_retained, 4),
        )


def mscs(curve: Sequence[tuple], target_miss: float = 0.001) -> int:
    """Max sustainable concurrent sessions at a target miss rate, given a list of
    (n_sessions, miss_rate) points (sorted by n). Returns the largest n whose
    miss_rate <= target_miss with all smaller n also satisfying (monotone)."""
    best = 0
    for n, miss in sorted(curve):
        if miss <= target_miss:
            best = n
        else:
            break
    return best


def mscs_served(curve: Sequence[tuple], target_miss: float = 0.001) -> int:
    """MSCS counting *served* (admitted) sessions, not offered load. Each point is
    (offered_n, admitted, miss_rate). For no-admission systems admitted==offered and
    this reduces to ``mscs``; for admission systems it returns the admission plateau
    (the most sessions actually served while holding the SLO)."""
    best = 0
    for offered, admitted, miss in sorted(curve):
        if miss <= target_miss:
            best = max(best, admitted)
    return best


# --- production metrics (docs/PRODUCTION.md §2) ------------------------------

def consecutive_run_lengths(miss_flags: Sequence[bool]) -> list:
    """Lengths of maximal runs of consecutive misses (audio-glitch severity).
    A single dropped frame may be inaudible; a long run is a dropout."""
    runs, cur = [], 0
    for m in miss_flags:
        if m:
            cur += 1
        elif cur:
            runs.append(cur); cur = 0
    if cur:
        runs.append(cur)
    return runs


def jain_index(values: Sequence[float]) -> float:
    """Jain's fairness index in [1/n, 1]; 1 == perfectly equal. Applied to
    per-session *on-time rates* (higher = fairer)."""
    x = np.asarray([v for v in values], dtype=float)
    if x.size == 0:
        return 1.0
    s = float(np.sum(x))
    if s == 0:
        return 1.0
    return float(s * s / (x.size * float(np.sum(x * x))))


def blocking_probability(admitted: int, offered: int) -> float:
    return 0.0 if offered <= 0 else 1.0 - admitted / offered


@dataclass
class ProductionReport:
    """Aggregates per-session per-tick outcomes into the production metrics."""
    # per-session lists of booleans/values, indexed by session
    per_session_miss: dict = field(default_factory=dict)       # sid -> [bool]
    per_session_quality: dict = field(default_factory=dict)    # sid -> [float]
    n_arrivals: int = 0
    n_admitted: int = 0
    frame_budget_ms: float = 0.0
    horizon_frames: int = 0

    def _all_miss_flags(self):
        out = []
        for v in self.per_session_miss.values():
            out.extend(v)
        return out

    @property
    def total_ticks(self) -> int:
        return sum(len(v) for v in self.per_session_miss.values())

    @property
    def total_misses(self) -> int:
        return sum(sum(v) for v in self.per_session_miss.values())

    @property
    def miss_rate(self) -> float:
        t = self.total_ticks
        return self.total_misses / t if t else 0.0

    @property
    def blocking(self) -> float:
        return blocking_probability(self.n_admitted, self.n_arrivals)

    def miss_run_stats(self) -> dict:
        runs = []
        for v in self.per_session_miss.values():
            runs.extend(consecutive_run_lengths(v))
        if not runs:
            return dict(n_runs=0, p50=0, p99=0, max=0, mean=0.0)
        return dict(n_runs=len(runs), p50=int(percentile(runs, 50)),
                    p99=int(percentile(runs, 99)), max=int(max(runs)),
                    mean=round(float(np.mean(runs)), 3))

    def fairness(self) -> float:
        on_time = [1.0 - (sum(v)/len(v) if v else 0.0)
                   for v in self.per_session_miss.values()]
        return jain_index(on_time)

    def goodput_frac(self, quality_floor: float = 0.0) -> float:
        """Fraction of ticks that were on-time AND above the quality floor."""
        good = tot = 0
        for sid, miss in self.per_session_miss.items():
            q = self.per_session_quality.get(sid, [1.0] * len(miss))
            for i, m in enumerate(miss):
                tot += 1
                if (not m) and (q[i] if i < len(q) else 1.0) >= quality_floor:
                    good += 1
        return good / tot if tot else 0.0

    def mean_quality(self) -> float:
        qs = [x for v in self.per_session_quality.values() for x in v]
        return float(np.mean(qs)) if qs else 1.0

    def summary(self, quality_floor: float = 0.0) -> dict:
        return dict(
            n_arrivals=self.n_arrivals, n_admitted=self.n_admitted,
            blocking=round(self.blocking, 4), miss_rate=round(self.miss_rate, 6),
            miss_runs=self.miss_run_stats(), fairness=round(self.fairness(), 4),
            goodput=round(self.goodput_frac(quality_floor), 4),
            mean_quality=round(self.mean_quality(), 4),
            total_ticks=self.total_ticks,
        )


@dataclass
class CostModelDollars:
    """$/session-hour at a fixed SLO (RESEARCH_PLAN §6.5)."""
    gpu_dollars_per_hour: float = 2.0   # rental rate for the accelerator

    def per_session_hour(self, n_sessions: int) -> float:
        if n_sessions <= 0:
            return float("inf")
        return self.gpu_dollars_per_hour / n_sessions

    def gpu_hours_per_1000_session_min(self, n_sessions: int) -> float:
        if n_sessions <= 0:
            return float("inf")
        # 1000 session-minutes = 1000/60 session-hours; one GPU serves n in parallel
        return (1000.0 / 60.0) / n_sessions
