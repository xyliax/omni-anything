"""Synthetic session generator (RESEARCH_PLAN §6.4, PIPELINE S1).

Parameterised arrival process and per-session attributes so we can sweep load and
plot capacity curves under control. Also builds the phase-misaligned, mixed-age
populations the admission test must reason about (§1.5).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from metronome.models import ModelFacts
from metronome.session import PeriodicSession


@dataclass
class WorkloadConfig:
    facts: ModelFacts
    kv_budget_tokens: int          # B_i for every session (the knob)
    mean_session_s: float = 90.0   # typical voice interaction 1-3 min
    arrival_rate_hz: float = 0.0   # new sessions/sec (0 => all present at t=0)
    talk_ratio: float = 1.0        # fraction of ticks that produce output
    phase_jitter: bool = True      # misalign phases across the period
    seed: int = 0

    @property
    def token_rate(self) -> float:
        return self.facts.tokens_per_tick / self.facts.period_s


def make_population(cfg: WorkloadConfig, n: int) -> list:
    """Create ``n`` sessions present at t=0 with misaligned phases and a spread of
    ages (drawn from the session-length distribution), i.e. a realistic age-mix."""
    rng = np.random.default_rng(cfg.seed)
    f = cfg.facts
    sessions = []
    for i in range(n):
        phase = rng.random() * f.period_s if cfg.phase_jitter else 0.0
        # start each session at a random point in its life => mixed-age population
        age0 = rng.exponential(cfg.mean_session_s)
        s = PeriodicSession(
            sid=i, facts=f, period_s=f.period_s, deadline_s=f.period_s,
            phase_s=phase, kv_budget_tokens=cfg.kv_budget_tokens,
            token_rate=cfg.token_rate, start_t=0.0,
            length_tokens=min(int(cfg.token_rate * age0), cfg.kv_budget_tokens),
            talk_prob=cfg.talk_ratio,
        )
        sessions.append(s)
    return sessions


def make_arrivals(cfg: WorkloadConfig, horizon_s: float, max_sessions: int = 100000):
    """Poisson arrivals over a horizon; returns list of (arrival_t, session)."""
    rng = np.random.default_rng(cfg.seed + 1)
    f = cfg.facts
    arrivals = []
    t = 0.0
    sid = 0
    if cfg.arrival_rate_hz <= 0:
        return arrivals
    while t < horizon_s and sid < max_sessions:
        t += rng.exponential(1.0 / cfg.arrival_rate_hz)
        if t >= horizon_s:
            break
        life = rng.exponential(cfg.mean_session_s)
        phase = rng.random() * f.period_s if cfg.phase_jitter else 0.0
        s = PeriodicSession(
            sid=sid, facts=f, period_s=f.period_s, deadline_s=f.period_s,
            phase_s=phase, kv_budget_tokens=cfg.kv_budget_tokens,
            token_rate=cfg.token_rate, start_t=t, length_tokens=0,
            talk_prob=cfg.talk_ratio,
        )
        s._life_s = life   # attach planned lifetime
        arrivals.append((t, s))
        sid += 1
    return arrivals
