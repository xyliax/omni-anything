"""Open-system, event-driven simulator (docs/PRODUCTION.md).

Unlike the closed-population `sim/simulator.py`, this models a production server:
sessions *arrive* (Poisson, possibly time-varying), are admitted or blocked, run
with realistic turn-taking, age while resident, and *depart* (heavy-tailed holding
time), freeing their KV budget. It records per-session, per-frame outcomes so the
production metrics (consecutive-miss runs, fairness, goodput, blocking, recovery)
can be computed.

Time advances frame by frame (frame = the common period). Each frame:
  1. depart sessions whose holding time elapsed (free budget);
  2. process arrivals in this frame's window; admit/block each via the controller;
  3. update each active session's talk/silence Markov state;
  4. run the scheduler frame over active sessions (silent ones may be deferred);
  5. record per-session outcomes and the aggregate miss rate.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metronome.cost_model import CostModel
from metronome.models import ModelFacts
from metronome.session import PeriodicSession
from metronome.scheduler import TickScheduler
from metronome.admission import AdmissionController, AdmissionConfig
from metronome.kv_manager import make_policy, quality_proxy
from bench.metrics import ProductionReport


@dataclass
class OpenConfig:
    cost: CostModel
    facts: ModelFacts
    hbm_kv_bytes: float
    kv_budget_tokens: int
    # arrival / holding
    arrival_rate_hz: float = 1.0           # base Poisson rate (sessions/sec)
    mean_holding_s: float = 90.0           # heavy-tailed (lognormal) mean
    holding_cv: float = 1.5                # coefficient of variation (tail heaviness)
    # turn-taking Markov (per-frame transition probabilities)
    p_talk_start: float = 0.3              # silence -> talk
    p_talk_stop: float = 0.15              # talk -> silence  (mean talk run = 1/p)
    start_talking: float = 0.6             # P(arrive talking)
    # policy
    admission: bool = True
    memory_admission: bool = True
    ordering: str = "edf"
    eviction: str = "sink_window"
    degradation: bool = True
    silence: bool = True
    admission_mode: str = "age_aware"      # worst_case | age_aware | lookahead
    assumed_age_s: float = float("inf")
    admission_talk_fraction: float = 1.0   # silence-aware admission (1.0 = unaware)
    coaging_safe: bool = False             # adapt the lookahead guard horizon to the
                                           # observed departure rate (co-aging-safe)
    guard_k: float = 2.0                   # guard horizon ~ guard_k / departure_rate
    safety: float = 0.90
    # load-adaptive KV budget: each frame, size the resident window so the current
    # active batch fits the frame at the plateau (tighten under load, loosen as it
    # drains) — trades quality for capacity dynamically. Clamped to [min_budget,budget].
    adaptive_budget: bool = False
    min_budget_tokens: int = 256
    seed: int = 0


@dataclass
class OpenResult:
    report: ProductionReport
    per_frame_miss: list = field(default_factory=list)   # aggregate miss-rate per frame
    per_frame_active: list = field(default_factory=list)  # active session count
    per_frame_talkers: list = field(default_factory=list)
    n_arrivals: int = 0
    n_admitted: int = 0
    n_blocked: int = 0


class OpenSystemSimulator:
    def __init__(self, cfg: OpenConfig):
        self.cfg = cfg
        self.cost = cfg.cost
        self.rng = np.random.default_rng(cfg.seed)

        def cost_fn(lengths):
            return self.cost.predict_batch(lengths) if len(lengths) else 0.0

        self.cost_fn = cost_fn
        deadline_aware = (cfg.admission or cfg.ordering != "fifo" or cfg.degradation)
        self.scheduler = TickScheduler(
            cost_fn=cost_fn, frame_budget_s=cfg.facts.period_s, ordering=cfg.ordering,
            use_silence=cfg.silence, use_degradation=cfg.degradation, safety=1.0,
            deadline_aware=deadline_aware)
        self.admission = AdmissionController(
            self.cost, AdmissionConfig(hbm_kv_bytes=cfg.hbm_kv_bytes,
                                       frame_budget_s=cfg.facts.period_s,
                                       safety=cfg.safety, mode=cfg.admission_mode,
                                       assumed_age_s=cfg.assumed_age_s,
                                       talk_fraction=cfg.admission_talk_fraction))
        # fill-to-budget time (time for a session to ramp to the plateau)
        self._fill_budget_s = cfg.kv_budget_tokens / (cfg.facts.tokens_per_tick / cfg.facts.period_s)

    def _holding_time(self) -> float:
        # lognormal with given mean and CV -> heavy tail
        cv = self.cfg.holding_cv
        sigma = np.sqrt(np.log(1 + cv * cv))
        mu = np.log(self.cfg.mean_holding_s) - 0.5 * sigma * sigma
        return float(self.rng.lognormal(mu, sigma))

    def _new_session(self, sid, t) -> PeriodicSession:
        f = self.cfg.facts
        s = PeriodicSession(
            sid=sid, facts=f, period_s=f.period_s, deadline_s=f.period_s,
            phase_s=self.rng.random() * f.period_s,
            kv_budget_tokens=self.cfg.kv_budget_tokens,
            token_rate=f.tokens_per_tick / f.period_s, start_t=t, length_tokens=0)
        s._depart_t = t + self._holding_time()
        s._talking = self.rng.random() < self.cfg.start_talking
        return s

    def run(self, horizon_s: float, arrival_rate_fn: Optional[Callable[[float], float]] = None,
            warmup_s: float = 0.0) -> OpenResult:
        cfg = self.cfg
        f = cfg.facts
        period = f.period_s
        n_frames = int(horizon_s / period)
        rate_fn = arrival_rate_fn or (lambda t: cfg.arrival_rate_hz)

        active: list = []
        rep = ProductionReport(frame_budget_ms=period * 1000.0, horizon_frames=n_frames)
        per_frame_miss, per_frame_active, per_frame_talkers = [], [], []
        n_arr = n_adm = n_blk = 0
        next_sid = 0
        arrivals_recent = []   # arrival wall-times in the last holding window (demand est.)
        departures_recent = []  # departure wall-times (for the churn-rate estimate)

        for fi in range(n_frames):
            t = fi * period
            recording = t >= warmup_s

            # 1. departures
            leaving = [s for s in active if s._depart_t <= t]
            departures_recent.extend([t] * len(leaving))
            active = [s for s in active if s._depart_t > t]

            # 1a. co-aging-safe guard: adapt the lookahead horizon to the observed
            # departure (churn) rate. High churn -> short horizon (age-aware, admit
            # more); low churn -> horizon grows toward fill-to-budget (-> worst-case,
            # so a co-aging cohort can never breach). This realises the "age-aware is
            # a churn dividend" principle safely.
            if cfg.coaging_safe:
                win = max(self._fill_budget_s, period)
                departures_recent[:] = [td for td in departures_recent if td > t - win]
                dep_rate = len(departures_recent) / win        # departures / s
                horizon = cfg.guard_k / max(dep_rate, 1e-6)
                self.admission.cfg.guard_horizon_s = float(min(self._fill_budget_s, horizon))

            # 1b. load-adaptive budget (BEFORE admission): size the window to fit the
            # estimated *offered* demand (recent arrivals over a holding window, by
            # Little's law), not just current active — so a controller anticipates
            # load and traverses the quality/capacity Pareto. Tighten under demand,
            # loosen (upgrade quality) when demand is light.
            adapt_budget = cfg.kv_budget_tokens
            if cfg.adaptive_budget:
                arrivals_recent[:] = [ta for ta in arrivals_recent if ta > t - cfg.mean_holding_s]
                offered_est = max(len(active), len(arrivals_recent), 1)
                budget_ms = period * 1000.0 * cfg.safety
                c = self.cost
                avail = budget_ms / max(c.tail_factor, 1e-9) - c.batch_base - c.batch_per_session * offered_est
                B = avail / max(c.batch_alpha * offered_est, 1e-9)
                adapt_budget = int(min(cfg.kv_budget_tokens, max(cfg.min_budget_tokens, B)))
                for s in active:
                    s.kv_budget_tokens = adapt_budget

            # 2. arrivals this frame ~ Poisson(rate * period) (handles sub-1 rates)
            n_new = self.rng.poisson(max(0.0, rate_fn(t) * period))
            for _ in range(n_new):
                s = self._new_session(next_sid, t); next_sid += 1
                arrivals_recent.append(t)
                if cfg.adaptive_budget:
                    # admit against the guaranteed min-budget floor (max capacity);
                    # the controller upgrades quality (larger window) when load is low.
                    s.kv_budget_tokens = cfg.min_budget_tokens
                n_arr += 1 if recording else 0
                if cfg.admission:
                    res = self.admission.try_admit(active, s)
                    ok = res.admit
                elif cfg.memory_admission:
                    used = sum(x.budget_bytes for x in active)
                    ok = used + s.budget_bytes <= cfg.hbm_kv_bytes
                else:
                    ok = True
                if ok:
                    active.append(s); n_adm += 1 if recording else 0
                else:
                    n_blk += 1 if recording else 0

            # 3. turn-taking Markov + eviction bound
            talkers = []
            for s in active:
                if s._talking:
                    if self.rng.random() < cfg.p_talk_stop:
                        s._talking = False
                else:
                    if self.rng.random() < cfg.p_talk_start:
                        s._talking = True
                s.talk_prob = 1.0 if s._talking else 0.0
                if s._talking:
                    talkers.append(s)
                # bound resident length per the eviction policy/budget
                if cfg.eviction != "full":
                    pol = make_policy(cfg.eviction, s.kv_budget_tokens)
                    s.length_tokens = pol.resident_length(s.length_tokens, s.kv_budget_tokens)

            # 4. run the frame
            fr = self.scheduler.run_frame(fi, t, active, rng=self.rng)
            missed = set(fr.missed_sids)

            # 5. record per-session outcomes for talker frames (audio-producing)
            if recording:
                for s in active:
                    if not s._talking:
                        continue
                    rep.per_session_miss.setdefault(s.sid, []).append(s.sid in missed)
                    if cfg.eviction != "full" or cfg.kv_budget_tokens > 0:
                        pol = make_policy(cfg.eviction, s.kv_budget_tokens)
                        full_len = max(int(s.token_rate * (t - s.start_t + period)),
                                       s.length_tokens, 1)
                        q = quality_proxy(pol, full_len, s.kv_budget_tokens, seed=s.sid)
                    else:
                        q = 1.0
                    rep.per_session_quality.setdefault(s.sid, []).append(q)
                denom = max(1, len(talkers))
                per_frame_miss.append(len(missed & {s.sid for s in talkers}) / denom)
                per_frame_active.append(len(active))
                per_frame_talkers.append(len(talkers))

        rep.n_arrivals = n_arr
        rep.n_admitted = n_adm
        return OpenResult(report=rep, per_frame_miss=per_frame_miss,
                          per_frame_active=per_frame_active,
                          per_frame_talkers=per_frame_talkers,
                          n_arrivals=n_arr, n_admitted=n_adm, n_blocked=n_blk)


def recovery_time_s(per_frame_miss, period_s, slo=0.001, spike_frame=None):
    """Frames (→ seconds) for miss-rate to fall back under the SLO after the peak."""
    if not per_frame_miss:
        return 0.0
    arr = np.asarray(per_frame_miss)
    peak = int(np.argmax(arr)) if spike_frame is None else spike_frame
    for i in range(peak, len(arr)):
        if arr[i] <= slo:
            return (i - peak) * period_s
    return (len(arr) - peak) * period_s
