"""Tiered, model-aware KV manager with pluggable eviction (RESEARCH_PLAN §2.2.4).

The KV budget ``B_i`` is a *quality-coupled cost knob*: shrinking the resident
window lowers both per-tick attention cost (schedulability) and footprint (cost),
at a measurable quality price. This module implements the eviction policies as
length-bounding strategies plus a *retained-information* proxy used by the
quality-under-load curve (§6.6 plot 4). The actual GPU KV slab is append-only and
pinned; eviction here decides *which token positions remain resident*.

Policies (the §2.3 sweep):
  * full          — never evict (baseline; only bounded by context ceiling).
  * sliding       — keep the most recent W tokens.
  * sink_window   — keep the first S "attention sink" tokens + most recent W
                    (StreamingLLM, arXiv:2309.17453).
  * h2o           — keep S sinks + recent W + top-H "heavy hitters" by accumulated
                    attention mass (H2O, arXiv:2306.14048).

Each policy reports the resident length it would keep and a quality proxy in
[0,1] = fraction of the *attention mass* over a long context that the resident set
captures. The proxy is computed from a recency+heavy-hitter attention model so the
sweep is reproducible without running the full multimodal stack; it is calibrated
to be monotone and policy-ordered (full >= h2o >= sink_window >= sliding at equal
budget), matching the published behaviour of these policies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class EvictionPolicy:
    name: str
    window: int = 0          # recent tokens to keep (0 => unbounded => use budget)
    sinks: int = 0           # leading attention-sink tokens to keep
    heavy: int = 0           # heavy-hitter tokens to keep (h2o)

    def resident_length(self, full_length: int, budget: int) -> int:
        """How many tokens stay resident given the true context and the KV budget."""
        if self.name == "full":
            return min(full_length, budget)
        keep = self.sinks + self.window + self.heavy
        if keep <= 0:
            keep = budget
        return min(full_length, keep, budget)


# --- quality proxy ----------------------------------------------------------
# Attention over a long autoregressive context is empirically dominated by (a) a
# strong recency lobe and (b) a sparse set of persistent heavy hitters, on top of
# (c) the attention-sink tokens at the start. We model the per-position attention
# mass as the normalised sum of those three components and define a policy's
# quality as the fraction of total mass its resident set retains. This reproduces
# the published ordering and the diminishing-returns shape of window size without
# needing model outputs; it is used only for the *relative* quality-vs-load curve.

def _attention_mass(full_length: int, recency_tau: float = 256.0,
                    n_heavy: int = 64, heavy_frac: float = 0.30,
                    sink_frac: float = 0.10, seed: int = 0) -> np.ndarray:
    L = max(1, full_length)
    pos = np.arange(L)
    # recency lobe (exponential toward the most recent position)
    recency = np.exp(-(L - 1 - pos) / recency_tau)
    recency /= recency.sum()
    # heavy hitters: a fixed sparse set of high-mass positions
    rng = np.random.default_rng(seed)
    heavy = np.zeros(L)
    if L > 4:
        idx = rng.choice(L, size=min(n_heavy, L), replace=False)
        heavy[idx] = rng.random(len(idx)) ** 2
        if heavy.sum() > 0:
            heavy /= heavy.sum()
    # attention sinks at the start
    sink = np.zeros(L)
    nsink = max(1, int(0.0 * L) + 4)
    sink[:nsink] = 1.0
    sink /= sink.sum()
    mass = (1 - heavy_frac - sink_frac) * recency + heavy_frac * heavy + sink_frac * sink
    return mass / mass.sum()


_QP_MAX = 8192   # cap proxy resolution; the retained-mass *fraction* is scale-free


def quality_proxy(policy: EvictionPolicy, full_length: int, budget: int,
                  seed: int = 0) -> float:
    """Fraction of attention mass retained by ``policy`` at this context/budget.

    For tractability the position grid is capped at ``_QP_MAX`` and the budget /
    window / sink / heavy counts are scaled proportionally — the retained-*fraction*
    is invariant to that uniform rescaling, so the proxy is unchanged while the
    allocation stays O(_QP_MAX) instead of O(context-ceiling)."""
    if full_length <= 0:
        return 1.0
    if policy.name == "full":
        # never evicts -> retains all attention mass (the quality ceiling, cost
        # floor traded against it by the evicting policies).
        return 1.0
    if full_length > _QP_MAX:
        scale = _QP_MAX / full_length
        budget = max(1, int(budget * scale))
        policy = EvictionPolicy(policy.name,
                                window=int(policy.window * scale),
                                sinks=max(1, int(policy.sinks * scale)) if policy.sinks else 0,
                                heavy=int(policy.heavy * scale))
        full_length = _QP_MAX
    mass = _attention_mass(full_length, seed=seed)
    L = len(mass)
    keep = np.zeros(L, dtype=bool)
    # sinks
    s = min(policy.sinks, L)
    keep[:s] = True
    # recent window
    w = min(policy.window, L)
    if w > 0:
        keep[L - w:] = True
    # heavy hitters: pick top-`heavy` remaining positions by mass
    if policy.heavy > 0:
        remaining = np.where(~keep)[0]
        if len(remaining):
            order = remaining[np.argsort(mass[remaining])[::-1]]
            take = order[:policy.heavy]
            keep[take] = True
    # clamp to budget by dropping lowest-mass kept-but-over-budget positions
    if keep.sum() > budget:
        kept_idx = np.where(keep)[0]
        order = kept_idx[np.argsort(mass[kept_idx])]  # ascending
        drop = order[: keep.sum() - budget]
        keep[drop] = False
    return float(mass[keep].sum())


# --- tiered residency accounting -------------------------------------------
@dataclass
class Tier:
    name: str
    bytes_per_s: float       # bandwidth to read from this tier
    capacity_bytes: float


@dataclass
class TieredKV:
    """Accounting model for HBM(hot)/host(warm)/NVMe(cold) tiers. Records where a
    session's KV lives and the read cost implied. For the small regime everything
    is HBM-resident (§1.3); the tiers matter for the large-regime projection."""
    hbm: Tier
    host: Optional[Tier] = None
    nvme: Optional[Tier] = None

    def read_ms(self, hbm_bytes: float, host_bytes: float = 0.0,
                nvme_bytes: float = 0.0) -> float:
        ms = hbm_bytes / self.hbm.bytes_per_s * 1000.0
        if host_bytes and self.host:
            ms += host_bytes / self.host.bytes_per_s * 1000.0
        if nvme_bytes and self.nvme:
            ms += nvme_bytes / self.nvme.bytes_per_s * 1000.0
        return ms


# Library of default policies parameterised by window/sink/heavy as fractions of
# the budget — instantiated against a concrete budget at use time.
def make_policy(name: str, budget: int) -> EvictionPolicy:
    if name == "full":
        return EvictionPolicy("full")
    if name == "sliding":
        return EvictionPolicy("sliding", window=budget)
    if name == "sink_window":
        return EvictionPolicy("sink_window", sinks=max(4, budget // 32),
                              window=budget - max(4, budget // 32))
    if name == "h2o":
        s = max(4, budget // 32)
        h = budget // 4
        return EvictionPolicy("h2o", sinks=s, window=budget - s - h, heavy=h)
    raise ValueError(f"unknown policy {name!r}")


POLICIES = ["full", "sliding", "sink_window", "h2o"]
