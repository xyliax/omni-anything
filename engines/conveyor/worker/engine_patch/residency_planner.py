"""Conservative admission policy; no allocator or model execution lives here.

Costs are explicit upper-bound estimates for the configured workload, including
interference. This checker is deliberately sufficient, not an optimal solver.
A successful finite forecast is not a lifetime or measured SLO guarantee.
"""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class AdmissionProfile:
    horizon_s: float
    compute_s: float
    initial_blocks: int
    growth_blocks_per_period: int
    max_evict_blocks: int
    h2d_blocks_per_s: float
    d2h_blocks_per_s: float
    transfer_overhead_s: float
    safety_s: float
    gpu_reserve_blocks: int
    host_reserve_blocks: int
    max_sessions: int

    def __post_init__(self):
        for name in ('horizon_s', 'compute_s', 'h2d_blocks_per_s', 'd2h_blocks_per_s'):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f'{name} must be finite and positive')
        for name in ('transfer_overhead_s', 'safety_s'):
            value = getattr(self, name)
            if not math.isfinite(value) or value < 0:
                raise ValueError(f'{name} must be finite and nonnegative')
        for name in ('initial_blocks', 'growth_blocks_per_period', 'max_evict_blocks',
                     'gpu_reserve_blocks', 'host_reserve_blocks', 'max_sessions'):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f'{name} must be a nonnegative integer')
        if not self.initial_blocks or not self.max_sessions:
            raise ValueError('initial_blocks and max_sessions must be positive')

    @classmethod
    def read(cls, path):
        return cls(**json.loads(Path(path).read_text()))


@dataclass(frozen=True)
class ResidencyPlan:
    request_id: str
    slot: int
    admitted_at: float
    first_tick: float
    period_s: float
    restore_lead_s: float
    retained_prefix_blocks: int
    max_evict_blocks: int
    generation: int
    forecast_until: float

    def wire(self):
        return {**asdict(self), 'group': self.slot,
                'first_restore_start': self.first_tick - self.restore_lead_s,
                'first_restore_end': self.first_tick}


class ResidencyPlanner:
    """Try stable slots without moving admitted sessions or changing their budgets.

    One group shares a phase, not an execution batch. Compute and D2H are
    conservatively serialized inside each slot interval. Each group's H2D
    window ends before its tick. Destinations count in full from window start.
    Existing plans, including closing sessions, remain reserved until release().
    """
    def __init__(self, profile, *, period_s, slots, epoch, restore_lead_s,
                 retained_prefix_blocks, gpu_blocks, host_blocks):
        if not math.isfinite(period_s) or period_s <= 0 or type(slots) is not int or slots < 1:
            raise ValueError('positive period and integer slot count required')
        if not math.isfinite(epoch) or not math.isfinite(restore_lead_s):
            raise ValueError('finite grid and restore lead required')
        if not 0 < restore_lead_s <= period_s / slots:
            raise ValueError('conservative policy requires restore lead <= slot interval')
        if profile.horizon_s < 2 * period_s:
            raise ValueError('forecast must cover at least two periods, including startup')
        if retained_prefix_blocks < 1 or min(gpu_blocks, host_blocks) <= 0:
            raise ValueError('positive retention and physical pool capacities required')
        self.profile = profile
        self.period_s, self.slots, self.epoch = period_s, slots, epoch
        self.lead, self.retained = restore_lead_s, retained_prefix_blocks
        self.gpu_blocks, self.host_blocks = gpu_blocks, host_blocks
        self.plans: dict[str, ResidencyPlan] = {}
        self.generation = 0
        self.last_review = None

    def revalidate(self, *, now, current_blocks, used_gpu_blocks=0, recoverable_blocks=None):
        reason, forecast = self.check(list(self.plans.values()), now=now,
                                      current_blocks=current_blocks, used_gpu_blocks=used_gpu_blocks,
                                      recoverable_blocks=recoverable_blocks)
        self.last_review = {'feasible': reason is None, 'reason': reason, 'forecast': forecast}
        return self.last_review

    def try_admit(self, request_id, *, now, current_blocks, used_gpu_blocks=0, recoverable_blocks=None):
        if request_id in self.plans:
            return {'admitted': True, 'plan': self.plans[request_id].wire()}
        if len(self.plans) >= self.profile.max_sessions:
            return {'admitted': False, 'reason': 'session_limit'}
        failures = []
        # Least populated first; stable slot number breaks ties. Feasibility,
        # not the load count, decides whether a candidate may be installed.
        order = sorted(range(self.slots), key=lambda s: (sum(p.slot == s for p in self.plans.values()), s))
        for slot in order:
            phase = self.epoch + slot * self.period_s / self.slots
            first = phase + max(0, math.ceil((now - phase) / self.period_s)) * self.period_s
            plan = ResidencyPlan(request_id, slot, now, first, self.period_s, self.lead,
                                 self.retained, self.profile.max_evict_blocks,
                                 self.generation + 1, now + self.profile.horizon_s)
            plans = [*self.plans.values(), plan]
            reason, forecast = self.check(plans, now=now, current_blocks=current_blocks,
                                          used_gpu_blocks=used_gpu_blocks, recoverable_blocks=recoverable_blocks)
            if reason is None:
                self.generation += 1
                self.plans[request_id] = plan
                return {'admitted': True, 'plan': plan.wire(), 'forecast': forecast}
            failures.append(reason)
        return {'admitted': False, 'reason': ','.join(sorted(set(failures)))}

    def check(self, plans, *, now, current_blocks, used_gpu_blocks=0, recoverable_blocks=None):
        p = self.profile
        horizon = now + p.horizon_s
        # Reserve growth over H, not the application's maximum context. One
        # extra update accounts for an input already being processed at now.
        updates = math.ceil(p.horizon_s / self.period_s) + 1
        blocks = {x.request_id: max(p.initial_blocks, current_blocks.get(x.request_id, 0))
                  + updates * p.growth_blocks_per_period for x in plans}
        host = sum(blocks.values()) + p.host_reserve_blocks
        if host > self.host_blocks:
            return 'host_capacity', {}
        if used_gpu_blocks + p.gpu_reserve_blocks > self.gpu_blocks:
            return 'current_gpu_pressure', {}
        groups = {slot: [x for x in plans if x.slot == slot] for slot in range(self.slots)}
        release_offset = {}
        evicted = {x.request_id: min(x.max_evict_blocks,
                                    max(0, blocks[x.request_id] - x.retained_prefix_blocks)) for x in plans}
        # The group window sets a hard ceiling, not just today's transfer
        # amount. Growing histories may approach that ceiling without a new
        # plan; never admit members by spending unused early-cycle bandwidth.
        restoration_budget = {x.request_id: x.max_evict_blocks for x in plans}
        if recoverable_blocks is not None:
            # The runtime supplies confirmed, non-shared backing coverage.
            # A budget is an upper limit, not proof that those blocks can be
            # reclaimed. New sessions receive no speculative saving credit.
            evicted = {rid: min(amount, recoverable_blocks.get(rid, 0)) for rid, amount in evicted.items()}
        group_forecasts = []
        for slot, members in groups.items():
            if not members:
                continue
            compute = len(members) * p.compute_s
            # Reserve a full initial backup while any member is starting;
            # otherwise the backing service carries only incremental growth.
            backing = sum(blocks[x.request_id] if (not current_blocks.get(x.request_id, 0)
                          or now < x.first_tick + self.period_s)
                          else p.growth_blocks_per_period for x in members)
            d2h = backing / p.d2h_blocks_per_s + len(members) * p.transfer_overhead_s
            h2d = sum(restoration_budget[x.request_id] / p.h2d_blocks_per_s + p.transfer_overhead_s
                      for x in members if restoration_budget[x.request_id])
            if compute + p.safety_s > self.period_s / self.slots:
                return 'compute_window', {}
            if compute + d2h + p.safety_s > self.period_s / self.slots:
                return 'backing_window', {}
            if h2d + p.safety_s > self.lead:
                return 'restore_window', {}
            group_forecasts.append(dict(group=slot, members=[x.request_id for x in members],
                restore_lead_s=self.lead, window_capacity_blocks=max(0, math.floor(
                    (self.lead - p.safety_s - sum(p.transfer_overhead_s for x in members if x.max_evict_blocks))
                    * p.h2d_blocks_per_s)),
                assigned_ceiling_blocks=sum(x.max_evict_blocks for x in members),
                predicted_evicted_blocks=sum(evicted[x.request_id] for x in members)))
            release_offset[slot] = compute + d2h + p.safety_s
        # Periodic full-destination intervals; all other times only the
        # retained portion is charged. Starting sessions remain fully charged
        # until their first execution and backing window has completed.
        base = p.gpu_reserve_blocks + sum(blocks[x.request_id] - evicted[x.request_id] for x in plans)
        events = []
        at_now = base
        for x in plans:
            amount = evicted[x.request_id]
            if not amount:
                continue
            intervals = [(now, x.first_tick + release_offset[x.slot])]
            tick = x.first_tick + max(1, math.floor((now - x.first_tick) / self.period_s)) * self.period_s
            while tick - self.lead <= horizon:
                intervals.append((tick - self.lead, tick + release_offset[x.slot]))
                tick += self.period_s
            # Merge startup with restoration, so a session is charged once.
            merged = []
            for start, end in sorted(intervals):
                if end <= now or start > horizon:
                    continue
                start, end = max(now, start), min(horizon, end)
                if merged and start <= merged[-1][1]:
                    merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
                else:
                    merged.append((start, end))
            for start, end in merged:
                if start == now:
                    at_now += amount
                else:
                    events.append((start, amount))
                events.append((end, -amount))
        # Current physical pins can exceed the phase estimate (late work or
        # in-flight transfers). Keep that excess as headroom throughout H.
        at_now += max(0, used_gpu_blocks + p.gpu_reserve_blocks - at_now)
        peak = allocated = at_now
        # At equal timestamps charge allocation before crediting release;
        # predicted simultaneous operations are not an atomic handoff.
        for _, delta in sorted(events, key=lambda item: (item[0], -item[1])):
            allocated += delta
            peak = max(peak, allocated)
        forecast = {'gpu_peak_blocks': peak, 'host_blocks': host, 'until': horizon,
                    'groups': group_forecasts}
        return ('gpu_capacity' if peak > self.gpu_blocks else None), forecast

    def release(self, request_id):
        self.plans.pop(request_id, None)
