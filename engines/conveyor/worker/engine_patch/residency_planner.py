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
    forecast_until: float | None

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

    def plan_valid_until(self, now):
        return now + self.profile.horizon_s

    def try_admit(self, request_id, *, now, current_blocks, used_gpu_blocks=0, recoverable_blocks=None,
                  source_start=None):
        if request_id in self.plans:
            return {'admitted': True, 'plan': self.plans[request_id].wire()}
        if len(self.plans) >= self.profile.max_sessions:
            return {'admitted': False, 'reason': 'session_limit'}
        failures = []
        # Least populated first; stable slot number breaks ties. Feasibility,
        # not the load count, decides whether a candidate may be installed.
        def rank(slot):
            population = sum(p.slot == slot for p in self.plans.values())
            delay = 0 if source_start is None else (self.epoch + slot*self.period_s/self.slots - source_start) % self.period_s
            return population, delay, slot
        order = sorted(range(self.slots), key=rank)
        for slot in order:
            phase = self.epoch + slot * self.period_s / self.slots
            first = phase + max(0, math.ceil((now - phase) / self.period_s)) * self.period_s
            plan = ResidencyPlan(request_id, slot, now, first, self.period_s, self.lead,
                                 self.retained, self.profile.max_evict_blocks,
                                 self.generation + 1, self.plan_valid_until(now))
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


@dataclass(frozen=True)
class MaximumContextCosts:
    """Calibrated workload costs; context size comes from the live backend.

    Per-member compute and incremental backup are serialized conservatively.
    These estimates are checked against measurements, not a hard SLO promise.
    No growth predictor, planning horizon or tolerated-miss parameter is used.
    """
    compute_s: float
    backup_s: float
    max_evict_blocks: int
    h2d_blocks_per_s: float
    transfer_overhead_s: float
    safety_s: float
    gpu_reserve_blocks: int
    host_reserve_blocks: int
    max_sessions: int
    admission_policy: str = 'maximum_context'
    compute_by_group: dict[str, float] | None = None

    def __post_init__(self):
        for name in ('compute_s', 'backup_s', 'h2d_blocks_per_s'):
            if not math.isfinite(getattr(self, name)) or getattr(self, name) <= 0:
                raise ValueError(f'{name} must be finite and positive')
        for name in ('transfer_overhead_s', 'safety_s'):
            if not math.isfinite(getattr(self, name)) or getattr(self, name) < 0:
                raise ValueError(f'{name} must be finite and nonnegative')
        for name in ('max_evict_blocks', 'gpu_reserve_blocks', 'host_reserve_blocks', 'max_sessions'):
            if type(getattr(self, name)) is not int or getattr(self, name) < 0:
                raise ValueError(f'{name} must be a nonnegative integer')
        if not self.max_sessions:
            raise ValueError('max_sessions must be positive')
        if self.admission_policy not in ('maximum_context', 'static_limit'):
            raise ValueError('invalid admission policy')
        for count, cost in (self.compute_by_group or {}).items():
            if str(int(count)) != count or int(count) < 1 or not math.isfinite(cost) or cost <= 0:
                raise ValueError('positive calibrated group size and service cost required')


def read_cost_profile(path):
    values = json.loads(Path(path).read_text())
    mode = values.pop('planning_mode', 'finite_horizon')
    values.pop('calibration', None)  # provenance stays in the run manifest
    if mode in ('maximum_context', 'static_limit'):
        return MaximumContextCosts(**values, admission_policy=mode)
    if mode == 'finite_horizon':
        return AdmissionProfile(**values)
    raise ValueError(f'unknown planning_mode: {mode}')


class MaximumContextPlanner(ResidencyPlanner):
    """A reusable maximum-context envelope on a fixed, stable phase grid.

    Search the least populated slots with one fixed per-session eviction
    ceiling. Charge complete restoration destinations before each tick and
    credit release only after compute plus backing. All maximum histories
    are charged to host; current short contexts never raise admission limits.
    Runtime coverage/refcount checks still own actual eviction and allocation.
    """
    def __init__(self, profile, *, max_context_blocks, period_s, slots, epoch,
                 restore_lead_s, retained_prefix_blocks, gpu_blocks, host_blocks):
        if not math.isfinite(period_s) or period_s <= 0 or type(slots) is not int or slots < 1:
            raise ValueError('positive period and integer slot count required')
        if (not math.isfinite(epoch) or not math.isfinite(restore_lead_s)
                or not 0 < restore_lead_s <= period_s / slots):
            raise ValueError('finite grid and restore lead inside slot interval required')
        if type(max_context_blocks) is not int or max_context_blocks < 1:
            raise ValueError('positive backend maximum context in blocks required')
        if retained_prefix_blocks < 1 or min(gpu_blocks, host_blocks) <= 0:
            raise ValueError('positive retention and physical pool capacities required')
        # Keep at least the protected prefix and one potentially incomplete
        # tail block resident even at the maximum context boundary.
        if profile.max_evict_blocks > max(0, max_context_blocks - retained_prefix_blocks - 1):
            raise ValueError('eviction ceiling exceeds complete maximum-context history')
        self.profile = profile
        self.maximum_context_blocks = max_context_blocks
        self.period_s, self.slots, self.epoch = period_s, slots, epoch
        self.lead, self.retained = restore_lead_s, retained_prefix_blocks
        self.gpu_blocks, self.host_blocks = gpu_blocks, host_blocks
        self.plans, self.generation, self.last_review = {}, 0, None

    def plan_valid_until(self, now):
        return None  # reusable until membership changes, not a rolling lease

    def check(self, plans, *, now, current_blocks, used_gpu_blocks=0, recoverable_blocks=None):
        p, maximum = self.profile, self.maximum_context_blocks
        if any(current_blocks.get(x.request_id, 0) > maximum for x in plans):
            return 'maximum_context_exceeded', {}
        host = len(plans) * maximum + p.host_reserve_blocks
        if host > self.host_blocks:
            return 'host_capacity', {}
        if used_gpu_blocks + p.gpu_reserve_blocks > self.gpu_blocks:
            return 'current_gpu_pressure', {}
        if p.admission_policy == 'static_limit':
            # A matched control uses an independently calibrated count limit.
            # It does not borrow the assigned-phase planner's memory credit.
            return None, dict(planning_mode='static_limit', maximum_context_blocks=maximum,
                              host_blocks=host, calibrated_limit=p.max_sessions)
        groups, intervals, group_forecasts = {}, [], []
        for plan in plans:
            groups.setdefault(plan.slot, []).append(plan)
        for slot, members in groups.items():
            count = len(members)
            compute = (p.compute_by_group or {}).get(str(count), count*p.compute_s)
            busy = compute + count*p.backup_s + p.safety_s
            if compute + p.safety_s > self.period_s / self.slots:
                return 'compute_window', {}
            if busy > self.period_s / self.slots:
                return 'backing_window', {}
            evicted = sum(x.max_evict_blocks for x in members)
            if evicted and busy + self.lead >= self.period_s:
                return 'idle_window', {}
            overhead = sum(p.transfer_overhead_s for x in members if x.max_evict_blocks)
            if evicted / p.h2d_blocks_per_s + overhead + p.safety_s > self.lead:
                return 'restore_window', {}
            group_forecasts.append(dict(group=slot, members=[x.request_id for x in members],
                restore_lead_s=self.lead, assigned_ceiling_blocks=evicted,
                window_capacity_blocks=max(0, math.floor((self.lead - p.safety_s - overhead)
                                                         * p.h2d_blocks_per_s))))
            phase = (self.epoch + slot * self.period_s / self.slots - now) % self.period_s
            for cycle in (-1, 0, 1):
                start, end = phase + cycle * self.period_s - self.lead, phase + cycle * self.period_s + busy
                if end >= 0 and start <= self.period_s:
                    intervals.append((max(0., start), min(self.period_s, end), evicted))
        base = p.gpu_reserve_blocks + sum(maximum - x.max_evict_blocks for x in plans)
        at_now = base + sum(amount for start, end, amount in intervals if start == 0)
        # Existing allocations or copy pins may exceed the expected phase
        # envelope. Reserve that excess throughout the candidate cycle.
        allocated = at_now + max(0, used_gpu_blocks + p.gpu_reserve_blocks - at_now)
        peak = allocated
        events = [(time, delta) for start, end, amount in intervals
                  for time, delta in ([(start, amount)] if start > 0 else []) + [(end, -amount)]]
        for _, delta in sorted(events, key=lambda event: (event[0], -event[1])):
            allocated += delta
            peak = max(peak, allocated)
        forecast = dict(planning_mode='maximum_context', maximum_context_blocks=maximum,
                        gpu_peak_blocks=peak, host_blocks=host, groups=group_forecasts,
                        plan_version=self.generation + 1)
        return ('gpu_capacity' if peak > self.gpu_blocks else None), forecast

    def release(self, request_id):
        if self.plans.pop(request_id, None) is not None:
            self.generation += 1
