"""Calibrated discrete-event simulator of a single accelerator serving a
multi-tenant set of periodic interaction sessions (PIPELINE S2/S5/S8).

Every per-tick cost comes from the *measured* CostModel (``predict_batch``), so the
simulator inherits the real GPU's timing; it exists to run the large sweeps (MSCS
curves over hundreds of configs, age-mix transients, large-regime projection) that
would be impractical to run live. Its predictions are validated against the live
GPU harness (``experiments/validate_sim.py``, Goal G5).

Sessions have period == frame budget F, so each active session ticks exactly once
per frame; the batch each frame is all active sessions. This is the worst-case,
single-accelerator alignment of §2.1. Baselines and Metronome are the *same*
simulator with different policy flags:

  B0  request-per-tick, no persistent session  -> re-prefills full context each tick
  B1  persistent session, throughput-greedy     -> full KV, no admission, FIFO
  B2  per-request deadline scheduler (SLAI-like) -> EDF, no KV-budget admission
  M   Metronome                                  -> EDF + KV-budget admission + ladder
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence

import numpy as np

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metronome.cost_model import CostModel
from metronome.session import PeriodicSession
from metronome.scheduler import TickScheduler
from metronome.admission import AdmissionController, AdmissionConfig
from metronome.kv_manager import EvictionPolicy, quality_proxy, make_policy
from bench.metrics import RunMetrics


@dataclass
class SimConfig:
    cost: CostModel
    frame_budget_s: float
    hbm_kv_bytes: float
    # policy switches (define B0/B1/B2/M)
    admission: bool = True          # full timing+memory schedulability admission (M)
    memory_admission: bool = True   # at minimum, never exceed HBM (vLLM-style B1/B2)
    ordering: str = "edf"          # edf | fifo | lrf
    kv_budget_tokens: int = 0      # 0 => use each session's own budget (full)
    eviction: str = "full"         # full | sliding | sink_window | h2o
    degradation: bool = True
    silence: bool = True
    reprefill: bool = False        # B0: re-read full context as if no persistent KV
    admission_mode: str = "age_aware"
    assumed_age_s: float = float("inf")  # age-aware characteristic operating age
    safety: float = 0.90
    seed: int = 0


@dataclass
class SimResult:
    metrics: RunMetrics
    admitted: int
    rejected: int
    per_frame_ms: list = field(default_factory=list)
    per_frame_missed: list = field(default_factory=list)


class Simulator:
    def __init__(self, cfg: SimConfig):
        self.cfg = cfg
        self.cost = cfg.cost

        def cost_fn(lengths):
            if not len(lengths):
                return 0.0
            if cfg.reprefill:
                # B0: no persistent KV -> each tick re-reads the whole context as a
                # fresh prefill, i.e. cost scales with total context every tick with
                # no batched-share amortisation.
                return sum(self.cost.predict(L) for L in lengths)
            return self.cost.predict_batch(lengths)

        self.cost_fn = cost_fn
        # deadline-aware = anything that reasons about deadlines (admission, EDF
        # ordering, or the degradation ladder). Throughput-greedy B0/B1 (fifo, no
        # admission, no degradation) are NOT: they run the whole batch and miss
        # wholesale when it exceeds the frame.
        deadline_aware = (cfg.admission or cfg.ordering != "fifo" or cfg.degradation)
        self.scheduler = TickScheduler(
            cost_fn=cost_fn, frame_budget_s=cfg.frame_budget_s,
            ordering=cfg.ordering, use_silence=cfg.silence,
            use_degradation=cfg.degradation, safety=1.0,
            deadline_aware=deadline_aware,
        )
        self.admission = AdmissionController(
            self.cost,
            AdmissionConfig(hbm_kv_bytes=cfg.hbm_kv_bytes,
                            frame_budget_s=cfg.frame_budget_s,
                            safety=cfg.safety, mode=cfg.admission_mode,
                            assumed_age_s=cfg.assumed_age_s),
        )

    def _apply_eviction(self, sessions):
        """Bound each session's resident length per the eviction policy/ budget."""
        cfg = self.cfg
        if cfg.eviction == "full" and cfg.kv_budget_tokens == 0:
            return
        for s in sessions:
            if cfg.kv_budget_tokens > 0:
                s.kv_budget_tokens = min(s.kv_budget_tokens, cfg.kv_budget_tokens)
            pol = make_policy(cfg.eviction, s.kv_budget_tokens)
            R = pol.resident_length(s.length_tokens, s.kv_budget_tokens)
            s.length_tokens = R

    def run_static(self, sessions: Sequence[PeriodicSession], n_frames: int) -> SimResult:
        """Run a fixed population for n_frames. Admission (if on) trims the
        population to a feasible set before the run; the rest are 'rejected'."""
        cfg = self.cfg
        rng = np.random.default_rng(cfg.seed)
        sessions = list(sessions)

        admitted, rejected = [], 0
        if cfg.admission:
            # full schedulability admission (timing + memory): Metronome
            for s in sessions:
                res = self.admission.try_admit(admitted, s)
                if res.admit:
                    admitted.append(s)
                else:
                    rejected += 1
        elif cfg.memory_admission:
            # throughput-greedy (B1/B2): admit while KV fits HBM, ignore deadlines.
            # A real engine (vLLM/SGLang) never OOMs; it just keeps packing until
            # memory is full, then misses frames as those sessions age.
            used = 0.0
            for s in sessions:
                if used + s.budget_bytes <= cfg.hbm_kv_bytes:
                    admitted.append(s)
                    used += s.budget_bytes
                else:
                    rejected += 1
        else:
            admitted = sessions

        for s in admitted:
            if cfg.kv_budget_tokens > 0:
                s.kv_budget_tokens = min(s.kv_budget_tokens, cfg.kv_budget_tokens)

        lat, n_missed, n_degraded = [], 0, 0
        per_frame_ms, per_frame_missed = [], []
        quality_samples = []

        for fi in range(n_frames):
            t = fi * cfg.frame_budget_s
            self._apply_eviction(admitted)
            fr = self.scheduler.run_frame(fi, t, admitted, rng=rng)
            per_frame_ms.append(fr.batch_ms)
            per_frame_missed.append(fr.n_missed)
            n_missed += fr.n_missed
            n_degraded += fr.n_degraded
            # each executed session experiences batch_ms; missed ones blow budget
            for _ in range(fr.n_executed):
                lat.append(fr.batch_ms)
            for _ in range(fr.n_missed):
                lat.append(max(fr.batch_ms, fr.budget_ms * 1.0001))

        # quality proxy: computed once at steady state (end of run) over a sample of
        # sessions — representative and O(sample) instead of O(n_frames * sample).
        if cfg.eviction != "full" or cfg.kv_budget_tokens > 0:
            step = max(1, len(admitted) // 8 or 1)
            for s in admitted[::step]:
                pol = make_policy(cfg.eviction, s.kv_budget_tokens)
                full_len = max(int(s.token_rate * n_frames * cfg.frame_budget_s),
                               s.length_tokens, s.kv_budget_tokens)
                quality_samples.append(
                    quality_proxy(pol, full_len, s.kv_budget_tokens, seed=s.sid))

        n_ticks = sum(1 for _ in lat)
        m = RunMetrics(
            n_sessions=len(admitted), n_ticks=max(1, n_ticks), n_missed=n_missed,
            tick_latencies_ms=lat, frame_budget_ms=cfg.frame_budget_s*1000.0,
            n_degraded=n_degraded,
            quality_retained=float(np.mean(quality_samples)) if quality_samples else 1.0,
        )
        return SimResult(metrics=m, admitted=len(admitted), rejected=rejected,
                         per_frame_ms=per_frame_ms, per_frame_missed=per_frame_missed)


# --- canonical policy presets -----------------------------------------------
def preset(name: str, cost: CostModel, frame_budget_s: float, hbm_kv_bytes: float,
           kv_budget_tokens: int = 0, **kw) -> SimConfig:
    base = dict(cost=cost, frame_budget_s=frame_budget_s, hbm_kv_bytes=hbm_kv_bytes,
                kv_budget_tokens=kv_budget_tokens)
    base.update(kw)
    if name == "B0":
        return SimConfig(**base, admission=False, memory_admission=False,
                         ordering="fifo", eviction="full",
                         degradation=False, silence=False, reprefill=True)
    if name == "B1":
        return SimConfig(**base, admission=False, memory_admission=True,
                         ordering="fifo", eviction="full",
                         degradation=False, silence=False)
    if name == "B2":
        return SimConfig(**base, admission=False, memory_admission=True,
                         ordering="edf", eviction="full",
                         degradation=False, silence=False)
    if name == "M":
        return SimConfig(**base, admission=True, ordering="edf",
                         eviction=kw.get("eviction", "sink_window"),
                         degradation=True, silence=True)
    raise ValueError(name)
