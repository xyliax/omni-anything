"""The persistent periodic-session object (RESEARCH_PLAN §2.2.1).

Unlike a request, an interaction session never "completes": it carries a period
(tick interval = frame budget), a relative deadline, a wall-clock phase offset, an
age, a KV budget, and a degradation state, and it accepts incremental input
forever. Its resident KV is append-only and pinned (no swap — §1.3).

This object is the unit of admission and scheduling. It is deliberately a plain
data carrier with the scheduling-relevant derived quantities; the GPU KV slab it
*represents* is managed by :mod:`metronome.kv_manager`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional

from .models import ModelFacts


class DegradeLevel(IntEnum):
    """The graceful-degradation ladder (§2.2.5), low number = best quality."""
    NONE = 0          # full quality
    SHRINK_WINDOW = 1 # reduce KV budget (smaller resident window)
    DROP_FRAMES = 2   # drop/merge input frames (lower token rate)
    QUANT = 3         # coarsen KV quantization (cheaper attention read)
    SKIP_TICK = 4     # skip a non-speaking tick
    SHED = 5          # shed/migrate the session (last resort)


@dataclass
class PeriodicSession:
    sid: int
    facts: ModelFacts
    period_s: float            # tick interval = frame budget
    deadline_s: float          # relative deadline (<= period)
    phase_s: float             # wall-clock phase offset within the period
    kv_budget_tokens: int      # B_i: max resident tokens (the cost/schedulability knob)
    token_rate: float          # r_i: tokens appended per second (modality dependent)
    start_t: float = 0.0       # admission wall-clock time
    length_tokens: int = 0     # current resident KV length L_i(t)
    age_ticks: int = 0
    degrade: DegradeLevel = DegradeLevel.NONE
    # accounting
    ticks_done: int = 0
    ticks_missed: int = 0
    talk_prob: float = 1.0     # P(this tick produces output / is a "talk" tick)
    quant_bytes: Optional[int] = None  # overridden KV dtype bytes when QUANT engaged

    # ---- derived ------------------------------------------------------------
    @property
    def kv_bytes_per_token(self) -> int:
        if self.quant_bytes is not None:
            f = self.facts
            return 2 * f.num_kv_heads * f.head_dim * f.num_layers * self.quant_bytes
        return self.facts.kv_bytes_per_token

    @property
    def resident_bytes(self) -> int:
        return self.length_tokens * self.kv_bytes_per_token

    @property
    def budget_bytes(self) -> int:
        return self.kv_budget_tokens * self.kv_bytes_per_token

    def context_at_age(self, age_s: float) -> int:
        """L_i(t) = min(r_i * age, B_i) — the saturating ramp (§4.1)."""
        return int(min(self.token_rate * age_s, self.kv_budget_tokens))

    def tokens_this_tick(self) -> int:
        return max(1, int(round(self.token_rate * self.period_s)))

    def advance(self, produced_tokens: Optional[int] = None):
        """Append a tick's tokens, clamped to the KV budget (eviction handled by
        the KV manager; here we only track resident length)."""
        n = self.tokens_this_tick() if produced_tokens is None else produced_tokens
        self.length_tokens = min(self.length_tokens + n, self.kv_budget_tokens)
        self.age_ticks += 1
        self.ticks_done += 1

    def next_due(self, k: int) -> float:
        """Wall-clock *release* time of the k-th tick (absolute)."""
        return self.start_t + self.phase_s + k * self.period_s

    def absolute_deadline(self, k: int) -> float:
        """Absolute deadline of the k-th tick = release + relative deadline D_i.
        This is the EDF ordering key; it differentiates sessions whose relative
        deadline D_i is tighter than their period (D_i <= T_i)."""
        return self.next_due(k) + self.deadline_s
