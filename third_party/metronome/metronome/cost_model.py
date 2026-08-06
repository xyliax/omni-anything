"""The per-tick cost model: the saturating-ramp WCET of RESEARCH_PLAN §4.1.

Single session at resident context length ``L`` (tokens):

    C(L) = C_fixed + alpha * L

  * ``C_fixed`` (ms) — QKV/output projection + FFN/MoE over the few new tokens, plus
    the (shared) weight read. Independent of context length.
  * ``alpha`` (ms/token) — cost of streaming one token's KV slab through the cores
    during attention. Memory-bound, so alpha ~ kv_bytes_per_token / HBM_bandwidth.

A multi-tenant micro-batch of ``B`` phase-aligned sessions with resident lengths
``{L_i}`` reads every session's KV once and runs the new-token compute ``B`` times:

    C_batch({L_i}) = base + per_session * B + alpha * sum_i L_i

**Robust measurement.** The structural model is fitted on the *median* (p50) per-tick
latency, which is robust to transient cross-tenant contention on a shared GPU. The
deadline-relevant *tail* is captured by a multiplicative ``tail_factor`` = the
*uncontended* p99/p50 ratio. We recover that uncontended ratio as a low percentile of
the per-point p99/p50 ratios (contention only inflates the ratio, so the low
percentile is the intrinsic kernel jitter — small under CUDA graphs). A production
server only contends with its *own* batched sessions (already in the model), so
cross-tenant inflation must not enter the cost model.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Optional, Sequence

import numpy as np


@dataclass
class LinearFit:
    intercept: float
    slope: float
    r2: float
    n: int
    max_abs_resid: float
    max_rel_resid: float

    def predict(self, x):
        return self.intercept + self.slope * np.asarray(x, dtype=float)


def _fit_linear(x, y) -> LinearFit:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    A = np.vstack([np.ones_like(x), x]).T
    (intercept, slope), *_ = np.linalg.lstsq(A, y, rcond=None)
    pred = intercept + slope * x
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2)) or 1e-12
    r2 = 1.0 - ss_res / ss_tot
    resid = np.abs(y - pred)
    rel = resid / np.maximum(np.abs(y), 1e-9)
    return LinearFit(float(intercept), float(slope), float(r2), int(len(x)),
                     float(resid.max()), float(rel.max()))


@dataclass
class CostModel:
    """Fitted per-tick cost model for one (model, hardware) pair. Structural terms
    are p50 (median); ``tail_factor`` lifts a prediction to the (uncontended) p99."""
    model: str
    device: str
    # single-session structural model C(L) = c_fixed + alpha*L (ms, p50)
    c_fixed: float
    alpha: float
    # batched: base + per_session*B + alpha*sum_L (ms, p50)
    batch_base: float = 0.0
    batch_per_session: float = 0.0
    batch_alpha: float = 0.0
    # multiplicative tail margin (uncontended p99/p50)
    tail_factor: float = 1.10
    # diagnostics
    single_r2: float = 0.0
    single_max_rel_resid: float = 0.0
    batch_r2: float = 0.0
    batch_max_rel_resid: float = 0.0
    kv_bytes_per_token: int = 0
    notes: str = ""

    # ---- single-session predictions ----------------------------------------
    def predict(self, L: float, tail: bool = True) -> float:
        c = self.c_fixed + self.alpha * L
        return c * self.tail_factor if tail else c

    # ---- batched predictions -------------------------------------------------
    def predict_batch(self, lengths: Sequence[float], tail: bool = True) -> float:
        B = len(lengths)
        if B == 0:
            return 0.0
        total = float(np.sum(lengths))
        if self.batch_alpha > 0 or self.batch_base > 0:
            c = self.batch_base + self.batch_per_session * B + self.batch_alpha * total
        else:
            c = self.c_fixed * B + self.alpha * total
        return c * self.tail_factor if tail else c

    @property
    def implied_bandwidth_gibs(self) -> float:
        if self.alpha <= 0 or self.kv_bytes_per_token <= 0:
            return float("nan")
        return (self.kv_bytes_per_token / (self.alpha / 1000.0)) / 2**30

    def rescale_to_bandwidth(self, target_gibs: float) -> "CostModel":
        """Project the bandwidth-bound terms (shared weight read in c_fixed/base and
        the per-token KV read alpha) to a different HBM bandwidth (1/BW scaling); the
        compute-bound per-session term is unchanged. For the A100/H100/GH200 study."""
        cur = self.implied_bandwidth_gibs
        d = asdict(self)
        if cur == cur and cur > 0 and target_gibs > 0:
            fac = cur / target_gibs
            for k in ("c_fixed", "alpha", "batch_base", "batch_alpha"):
                d[k] = d[k] * fac
            d["notes"] = (self.notes or "") + f" [rescaled {cur:.0f}->{target_gibs:.0f} GiB/s]"
        return CostModel(**d)

    def to_json(self, path: str):
        with open(path, "w") as fh:
            json.dump(asdict(self), fh, indent=2)

    @classmethod
    def from_json(cls, path: str) -> "CostModel":
        with open(path) as fh:
            d = json.load(fh)
        known = {f for f in cls.__dataclass_fields__}
        if "c_fixed" not in d and "c_fixed_p50" in d:
            # migrate a legacy (p50/p99) fit: structural terms from the median, tail
            # factor from the p99/p50 ratio of the fixed cost.
            tf = (d.get("c_fixed_p99", d["c_fixed_p50"]) / max(d["c_fixed_p50"], 1e-9))
            d = dict(
                model=d.get("model", "?"), device=d.get("device", "?"),
                c_fixed=d["c_fixed_p50"], alpha=d.get("alpha_p50", 0.0),
                batch_base=d.get("batch_base_p99", 0.0) / max(tf, 1e-9),
                batch_per_session=d.get("batch_per_session_p99", 0.0) / max(tf, 1e-9),
                batch_alpha=d.get("batch_alpha_p99", 0.0) / max(tf, 1e-9),
                tail_factor=max(1.0, tf), kv_bytes_per_token=d.get("kv_bytes_per_token", 0),
                notes=d.get("notes", "") + " [migrated legacy fit]")
        return cls(**{k: v for k, v in d.items() if k in known})


def _tail_factor(timings) -> float:
    """Uncontended p99/p50 ratio: the 20th percentile of per-point ratios (contention
    only inflates the ratio, so a low percentile recovers intrinsic jitter)."""
    ratios = [t.p99 / t.p50 for t in timings if t.p50 > 0]
    if not ratios:
        return 1.10
    return float(max(1.0, np.percentile(ratios, 20)))


def fit_single(timings, kv_bytes_per_token: int = 0, notes: str = "") -> CostModel:
    """Fit C(L) = c_fixed + alpha*L on the median (p50) — robust to contention."""
    L = [t.total_kv_tokens for t in timings]
    p50 = [t.p50 for t in timings]
    f = _fit_linear(L, p50)
    return CostModel(
        model=timings[0].model, device=timings[0].device,
        c_fixed=f.intercept, alpha=f.slope, tail_factor=_tail_factor(timings),
        single_r2=f.r2, single_max_rel_resid=f.max_rel_resid,
        kv_bytes_per_token=kv_bytes_per_token, notes=notes,
    )


def fit_batch(cost: CostModel, batch_timings) -> CostModel:
    """Augment with base + per_session*B + alpha*sum_L on the median (p50)."""
    B = np.array([t.batch_sessions for t in batch_timings], dtype=float)
    total = np.array([t.total_kv_tokens for t in batch_timings], dtype=float)
    y = np.array([t.p50 for t in batch_timings], dtype=float)
    A = np.vstack([np.ones_like(B), B, total]).T
    (base, per_s, alpha), *_ = np.linalg.lstsq(A, y, rcond=None)
    pred = base + per_s * B + alpha * total
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2)) or 1e-12
    rel = np.abs(y - pred) / np.maximum(np.abs(y), 1e-9)
    cost.batch_base = float(base)
    cost.batch_per_session = float(per_s)
    cost.batch_alpha = float(alpha)
    cost.batch_r2 = 1.0 - ss_res / ss_tot
    cost.batch_max_rel_resid = float(rel.max())
    # blend tail factor with the batch timings' clean ratio
    cost.tail_factor = max(cost.tail_factor, _tail_factor(batch_timings))
    return cost
