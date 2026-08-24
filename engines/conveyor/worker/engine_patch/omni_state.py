"""Control and timing facts for Conveyor's per-session KV management.

This registry deliberately does not invent a single lifecycle for facts that
belong to different objects.  vLLM's pools remain the authority for physical
block placement.  The registry stores only facts that cannot be derived from
those pools:

* session activity observed at the scheduler boundary (``active`` or ``idle``);
* whether a KV prefetch is in flight or deferred by the capacity gate; and
* the most recent release, eviction, and resume timestamps.

Block placement is classified live.  A block can be both GPU-resident and
host-backed, so those are coverage properties rather than mutually exclusive
session states.  Blocks absent from both prefix caches are recompute territory.
All callbacks run on the scheduler thread; no registry lock is required.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable


def external_id(request_id: str) -> str:
    """Live internal id (``s3e1-ab12cd34``) -> stable external id (``s3e1``)."""
    return request_id.rsplit("-", 1)[0] if "-" in request_id else request_id


@dataclass
class SessionKVControl:
    """Session-level activity, transfer control, and timestamps only."""

    external: str
    session_activity: str = "unknown"
    prefetch_inflight: bool = False
    deferred_prefetch: bool = False
    last_release_t: float = 0.0
    last_kv_eviction_t: float = 0.0
    last_resume_t: float = 0.0


@dataclass
class BlockCoverage:
    """One live prefix walk against the GPU and host block pools."""

    gpu_resident_blocks: int = 0
    host_backed_blocks: list = field(default_factory=list)

    @property
    def reloadable_blocks(self) -> int:
        return len(self.host_backed_blocks)


class Registry:
    def __init__(self) -> None:
        self.sessions: dict[str, SessionKVControl] = {}
        self.on_kv_evicted_hooks: list[Callable[[SessionKVControl, Any], None]] = []
        self.on_session_resumed_hooks: list[Callable[[SessionKVControl, Any], None]] = []

    def _session(self, request_id: str) -> SessionKVControl:
        key = external_id(request_id)
        session = self.sessions.get(key)
        if session is None:
            session = self.sessions[key] = SessionKVControl(external=key)
        return session

    # Event intake.  Mechanisms report these events on the scheduler thread.

    def on_release(self, request_id: str) -> SessionKVControl:
        session = self._session(request_id)
        session.last_release_t = time.time()
        return session

    def on_kv_evicted(self, request_id: str, scheduler) -> None:
        session = self._session(request_id)
        session.session_activity = "idle"
        session.last_kv_eviction_t = time.time()
        for hook in self.on_kv_evicted_hooks:
            hook(session, scheduler)

    def on_prefetch_issued(self, request_id: str) -> None:
        self._session(request_id).prefetch_inflight = True

    def on_prefetch_done(self, request_id: str) -> None:
        self._session(request_id).prefetch_inflight = False

    def on_session_resumed(self, request_id: str, scheduler) -> None:
        """Record scheduler admission of the next input chunk.

        This event does not assert that every KV block is already on the GPU.
        On-demand reload or recomputation may still follow; callers needing
        placement facts must inspect :meth:`classify` or vLLM request status.
        """
        session = self._session(request_id)
        session.session_activity = "active"
        session.last_resume_t = time.time()
        session.deferred_prefetch = False
        for hook in self.on_session_resumed_hooks:
            hook(session, scheduler)

    # Queries.  Placement is derived from the pools at the time of the call.

    def classify(self, scheduler, request) -> BlockCoverage:
        """Walk the reusable prefix: GPU-resident, then host-backed, then gap."""
        result = BlockCoverage()
        gpu_pool = scheduler.kv_cache_manager.block_pool
        manager = scheduler.connector.scheduler_manager
        cpu_pool = manager.cpu_block_pool
        for block_hash in request.block_hashes:
            if gpu_pool.get_cached_block(block_hash, [0]):
                result.gpu_resident_blocks += 1
                continue
            hit = cpu_pool.get_cached_block(block_hash, [manager.fa_gidx])
            if not hit:
                break
            result.host_backed_blocks.append(hit[0])
        return result

    def view(self, request_id: str) -> dict[str, Any]:
        session = self._session(request_id)
        return {
            "external": session.external,
            "session_activity": session.session_activity,
            "prefetch_inflight": session.prefetch_inflight,
            "deferred_prefetch": session.deferred_prefetch,
            "last_release_t": session.last_release_t,
            "last_kv_eviction_t": session.last_kv_eviction_t,
            "last_resume_t": session.last_resume_t,
        }


registry = Registry()
