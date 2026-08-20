"""Session KV control-state registry for the conveyor engine patch.

The engine layer above vLLM's core owns three things vLLM has no concept of:
which sessions exist as long-lived resumable requests, where each session
stands in its residency lifecycle, and when its KV last moved. This module is
that authority — the mechanisms (park, reload, transfer) report events here,
and policies (reload pacing today; governors and phase coordination later)
read here and register callbacks. Physical block residency remains pool-owned.

DESIGN INVARIANT — one truth source per fact. Block-level residency truth
lives in the pools themselves (a block is GPU-resident iff the GPU prefix
cache resolves its hash; mirrored iff the CPU pool does): this registry never
copies block state, because a copy is a second truth source that drifts. What
it owns is exactly what the pools cannot know:

- lifecycle:   "resident" (no outstanding park/materialization control
               action; not proof that every block is already on GPU) |
               "parked" (tail evicted) | "materializing" (an anonymous
               reload is in flight)
- timing:      last push / park / claim instants (the raw material for any
               pacing or phase algorithm)
- deferral:    reloads the pacing policy chose to hold until capacity frees

:func:`classify` answers block-level questions by walking the pools live —
the same three-way classification the reload semantic is built on
(resident / mirrored / recompute-territory).

Events are reported from scheduler-thread code (park hook, session-update
hook, transfer completion), so all state here is single-threaded by
construction — no locks.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable


def external_id(request_id: str) -> str:
    """Live internal id ("s3e1-ab12cd34") -> stable external id ("s3e1")."""
    return request_id.rsplit("-", 1)[0] if "-" in request_id else request_id


@dataclass
class SessionKV:
    """Lifecycle and timing for one resumable session (no block state)."""

    external: str
    lifecycle: str = "resident"      # control phase; block truth stays in pools
    last_push_t: float = 0.0
    last_park_t: float = 0.0
    last_claim_t: float = 0.0
    deferred_reload: bool = False    # pacing policy holds a reload for us


@dataclass
class Classification:
    """One live walk of a session's block hashes against both pools."""

    resident: int = 0                # GPU-cached (base + already materialized)
    mirrored: list = field(default_factory=list)   # CPU blocks to move (in order)

    @property
    def missing(self) -> int:
        return len(self.mirrored)


class Registry:
    def __init__(self) -> None:
        self.sessions: dict[str, SessionKV] = {}
        # policies subscribe to capacity-freeing events (park) and claim
        # events to re-evaluate deferred work; hooks are called on the
        # scheduler thread with (session, scheduler), right after the fact.
        self.on_parked_hooks: list[Callable[[SessionKV, Any], None]] = []
        self.on_claimed_hooks: list[Callable[[SessionKV, Any], None]] = []

    def _session(self, request_id: str) -> SessionKV:
        key = external_id(request_id)
        session = self.sessions.get(key)
        if session is None:
            session = self.sessions[key] = SessionKV(external=key)
        return session

    # ---- event intake (mechanisms report; scheduler thread only) ----

    def on_push(self, request_id: str) -> SessionKV:
        session = self._session(request_id)
        session.last_push_t = time.time()
        return session

    def on_parked(self, request_id: str, scheduler) -> None:
        session = self._session(request_id)
        session.lifecycle = "parked"
        session.last_park_t = time.time()
        for hook in self.on_parked_hooks:
            hook(session, scheduler)

    def on_materialize_issued(self, request_id: str) -> None:
        self._session(request_id).lifecycle = "materializing"

    def on_materialize_done(self, request_id: str) -> None:
        session = self._session(request_id)
        if session.lifecycle == "materializing":
            session.lifecycle = "resident"

    def on_claimed(self, request_id: str, scheduler) -> None:
        """The session's next chunk reached the scheduler, so the demand path
        owns any missing tail and a deferred anonymous reload is moot.

        ``resident`` here means the registry has no outstanding control
        action. Demand load or recompute can still be in progress; callers
        that need physical readiness must inspect the pools/request status.
        """
        session = self._session(request_id)
        session.lifecycle = "resident"
        session.last_claim_t = time.time()
        session.deferred_reload = False
        for hook in self.on_claimed_hooks:
            hook(session, scheduler)

    # ---- queries (policies and the kv_state utility read here) ----

    def classify(self, scheduler, request) -> Classification:
        """Live three-way walk: GPU-cached -> skip, CPU-mirrored -> movable,
        neither -> recompute territory (stop: the claim is prefix-contiguous,
        blocks past a gap can never be claimed)."""
        result = Classification()
        gpu_pool = scheduler.kv_cache_manager.block_pool
        manager = scheduler.connector.scheduler_manager
        cpu_pool = manager.cpu_block_pool
        for block_hash in request.block_hashes:
            if gpu_pool.get_cached_block(block_hash, [0]):
                result.resident += 1
                continue
            hit = cpu_pool.get_cached_block(block_hash, [manager.fa_gidx])
            if not hit:
                break
            result.mirrored.append(hit[0])
        return result

    def view(self, request_id: str) -> dict[str, Any]:
        session = self._session(request_id)
        return {
            "external": session.external,
            "lifecycle": session.lifecycle,
            "last_push_t": session.last_push_t,
            "last_park_t": session.last_park_t,
            "last_claim_t": session.last_claim_t,
            "deferred_reload": session.deferred_reload,
        }


registry = Registry()
