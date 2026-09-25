"""Periodic session control, independent of model iterations.

The adapter owns allocator synchronization and physical references. This module
owns plans and timers; neither module uses a model step to advance a copy.
"""
from __future__ import annotations

import math
import os
import threading
import time
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SessionPlan:
    period_s: float
    next_tick: float                 # monotonic clock
    restore_lead_s: float
    retained_prefix_blocks: int
    eviction_ranges: tuple[tuple[int, int], ...] = ()  # logical, half-open
    max_evict_blocks: int | None = None
    group: int | None = None
    plan_version: int = 0

    def __post_init__(self):
        if not all(math.isfinite(v) for v in (self.period_s, self.next_tick, self.restore_lead_s)):
            raise ValueError("session times must be finite")
        if not 0 < self.restore_lead_s < self.period_s:
            raise ValueError("restore lead must be inside the period")
        if self.retained_prefix_blocks < 1:
            raise ValueError("retain at least the shared head block")
        if self.max_evict_blocks is not None and self.max_evict_blocks < 0:
            raise ValueError("eviction budget must be nonnegative")
        previous = 0
        for start, end in self.eviction_ranges:
            if start < max(previous, 1) or end <= start:
                raise ValueError("eviction ranges must be sorted, disjoint, and exclude block zero")
            previous = end

    def candidates(self, block_count):
        if self.max_evict_blocks == 0:
            return []
        ranges = self.eviction_ranges or ((self.retained_prefix_blocks, block_count),)
        return [i for start, end in ranges for i in range(start, min(end, block_count))]


@dataclass
class ManagedSession:
    request_id: str
    plan: SessionPlan
    activity: str = "active"
    idle_generation: int = 0
    evicted_generation: int = -1
    resident_pins: list = field(default_factory=list)
    host_pins: list = field(default_factory=list)
    restore_inflight: bool = False
    cancelled: bool = False
    pending_work: str | None = None
    missing_tick: float | None = None
    restoration_requested: bool = False
    retained_table: list = field(default_factory=list)
    cached_blocks: int = 0
    retained_hashes: tuple = ()
    retained_computed_tokens: int = 0

    @property
    def restoration_tick(self):
        return self.plan.next_tick if self.missing_tick is None else self.missing_tick


class SessionManager:
    """One timer/event loop; allocator operations share the adapter's lock.

    Model execution must never hold this lock. A session can be active while
    an overtaken restore still owns copy references; cancellation similarly
    defers release of those references until the completion callback.
    """
    def __init__(self, adapter, *, clock=time.monotonic, poll_s=0.001):
        self.adapter = adapter
        self.lock = adapter.lock
        self.clock = clock
        self.poll_s = poll_s
        self.sessions: dict[str, ManagedSession] = {}
        self.wake = threading.Event()
        self.stopping = threading.Event()
        self.error = None
        self.thread = None
        self.restoration_paused = False
        self.restore_policy = os.environ.get('OMNI_RESTORE_POLICY', 'pre_tick')

    def start(self):
        self.thread = threading.Thread(target=self._run, name="session-manager", daemon=True)
        self.thread.start()

    def set_plan(self, request_id, plan):
        with self.lock:
            self.check_health()
            session = self.sessions.get(request_id)
            if session is None:
                session = self.sessions[request_id] = ManagedSession(request_id, plan)
            else:
                session.plan = plan
        self.wake.set()

    def on_idle(self, request_id):
        with self.lock:
            if session := self.sessions.get(request_id):
                session.activity = "idle"
                session.idle_generation += 1
                session.pending_work = None
        self.wake.set()

    def on_resume(self, request_id):
        with self.lock:
            if session := self.sessions.get(request_id):
                session.activity = "active"
                if session.pending_work is None:
                    self.adapter.release_idle_pins(session)
        self.wake.set()

    def cancel(self, request_id):
        with self.lock:
            session = self.sessions.pop(request_id, None)
            if session:
                session.cancelled = True
                self.adapter.release_idle_pins(session)
        self.wake.set()

    def advance(self):
        """One control pass, also used by deterministic CPU tests."""
        with self.lock:
            self.check_health()
            now = self.clock()
            review = getattr(self.adapter, 'review_plan', None)
            if review is not None:
                review()
            for session in sorted(self.sessions.values(), key=lambda s: s.restoration_tick - s.plan.restore_lead_s):
                if session.activity != "idle" or session.restore_inflight or session.pending_work is not None:
                    continue
                plan = session.plan
                # Do not create fresh missing state once its restore window
                # has begun or a late input has already missed the next tick.
                if session.evicted_generation != session.idle_generation:
                    if now < plan.next_tick - plan.restore_lead_s:
                        if self.adapter.evict(session):
                            session.evicted_generation = session.idle_generation
            # Reclaim every eligible idle session before choosing a restore.
            # A capacity-blocked oldest restore must not prevent later idle
            # sessions from releasing the capacity that it needs.
            for session in sorted(self.sessions.values(), key=lambda s: s.restoration_tick - s.plan.restore_lead_s):
                if session.activity != "idle" or session.restore_inflight or session.pending_work is not None:
                    continue
                plan = session.plan
                if self.restore_policy == 'pre_tick' and session.host_pins and now >= session.restoration_tick - plan.restore_lead_s:
                    if self.restoration_paused:
                        continue
                    if not self.adapter.restore(session):
                        # A blocked complete destination must not be bypassed
                        # by later sessions holding a smaller partial working set.
                        break

    def check_health(self):
        if self.error is not None:
            raise RuntimeError("Session Manager failed") from self.error
        self.adapter.check_health()

    def _run(self):
        try:
            while not self.stopping.is_set():
                self.wake.clear()
                self.advance()
                self.wake.wait(self.poll_s)
        except Exception as exc:
            self.error = exc
            self.adapter.report_error(exc)

    def close(self):
        self.stopping.set()
        self.wake.set()
        if self.thread:
            self.thread.join(timeout=5)
            if self.thread.is_alive():
                raise RuntimeError("Session Manager did not stop")
        for request_id in list(self.sessions):
            self.cancel(request_id)
        self.adapter.close()  # drain copies before releasing physical storage
