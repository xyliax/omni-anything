"""Engine command surface for session KV: reload_kv / kv_state, with pacing.

The engine (patch layer above vLLM's core) has the authority the worker
lacks: it sees every session's residency truth (via omni_state.classify) and
every capacity event (parks). This module turns that authority into two
utilities and one issuing policy:

- ``EngineCore.reload_kv(request_id)`` — command: make this session's KV
  resident. Semantics is the policy-free classification loop (resident ->
  skip, mirrored -> move, gap -> recompute territory); execution is an
  anonymous materialization on the transport layer (omni_transfer), claimed
  by vLLM's untouched resume path. The worker fires it at chunk-push time so
  the copy overlaps feature extraction (FINDINGS H5).
- ``EngineCore.kv_state(request_id)`` — query: lifecycle + live block
  classification for one session (debugging / experiments / future
  policies).

PACING (the issuing policy): when the pool is too tight to take the copy,
the command is not refused — it is DEFERRED. Capacity in this system is
freed by parks, so deferral is event-driven, not timed: every park re-runs
the deferred queue (re-resolving and re-classifying — nothing stale is ever
issued), and a session's own chunk arrival cancels its deferred entry (the
demand path owns it from there). This is "wait until the oldest computing
session parks, then reload" implemented on the event that defines it.

Correctness never depends on any of this: refused, deferred-forever, or
LRU-evicted reloads all degrade to the existing demand reload.
"""

from __future__ import annotations

import os
import time

import omni_park
import omni_state
import omni_transfer

# Pool budget gate: defer a reload that would push free space below this
# fraction of the pool (capacity returns at the next park).
MIN_FREE_FRACTION = float(os.environ.get("OMNI_PREFETCH_MIN_FREE", "0.1"))


def apply() -> None:
    """Install the transport wrappers, the pacing hooks, and the utilities
    (loader-gated; importing this module patches nothing)."""
    omni_transfer.apply()
    omni_state.registry.on_parked_hooks.append(_retry_deferred)
    from vllm.v1.engine.core import EngineCore

    EngineCore.reload_kv = reload_kv
    EngineCore.kv_state = kv_state


def reload_kv(self, request_id: str) -> dict:
    """Command: make this session's KV blocks resident (utility RPC).

    Runs on the EngineCore busy loop, serialized with schedule() — the same
    guarantee park relies on. Never touches the request: blocks belong to
    the cache, the request finds them at resume via the normal hash match.
    """
    scheduler = self.scheduler
    guard = _guards(scheduler)
    if guard:
        return {"reloaded": False, "reason": guard}
    session = omni_state.registry.on_push(request_id)
    request = omni_park._resolve(scheduler, request_id)
    if request is None:
        return {"reloaded": False, "reason": "unknown request"}
    from vllm.v1.request import RequestStatus

    if request.status != RequestStatus.WAITING_FOR_STREAMING_REQ:
        return {"reloaded": False, "reason": f"not idle: {request.status.name}"}
    if session.lifecycle == "materializing":
        return {"reloaded": False, "reason": "reload in flight"}

    classification = omni_state.registry.classify(scheduler, request)
    if not classification.mirrored:
        return {"reloaded": False, "reason": "resident"}
    if not _capacity_for(scheduler, classification.missing):
        # pacing: hold until a park frees capacity (event-driven; the
        # session's own chunk arrival cancels the entry). Deferral is a
        # normal reading, not an error.
        session.deferred_reload = True
        return {"reloaded": False, "reason": "deferred", "blocks": classification.missing}
    _issue(scheduler, request, classification)
    return {"reloaded": True, "blocks": classification.missing,
            "resident": classification.resident}


def kv_state(self, request_id: str) -> dict:
    """Query: one session's lifecycle plus its live block classification."""
    scheduler = self.scheduler
    view = omni_state.registry.view(request_id)
    request = omni_park._resolve(scheduler, request_id)
    if request is not None and not _guards(scheduler):
        classification = omni_state.registry.classify(scheduler, request)
        view.update(
            status=request.status.name,
            total_hashed=len(request.block_hashes),
            resident=classification.resident,
            mirrored_missing=classification.missing,
        )
    return view


def _guards(scheduler) -> str | None:
    if len(scheduler.kv_cache_config.kv_cache_groups) != 1:
        return "multi-group KV not supported"
    if getattr(scheduler.scheduler_config, "async_scheduling", False):
        return "async scheduling not supported"
    if getattr(getattr(scheduler, "connector", None), "scheduler_manager", None) is None:
        return "no offload connector"
    return None


def _capacity_for(scheduler, needed: int) -> bool:
    gpu_pool = scheduler.kv_cache_manager.block_pool
    return gpu_pool.get_num_free_blocks() - needed >= MIN_FREE_FRACTION * len(gpu_pool.blocks)


def _issue(scheduler, request, classification) -> None:
    """Execute one materialization: allocate + stamp + pin, hand to the
    transport, and account the evidence (L at issue, R at completion)."""
    gpu_pool = scheduler.kv_cache_manager.block_pool
    cpu_pool = scheduler.connector.scheduler_manager.cpu_block_pool
    sources = classification.mirrored
    gpu_blocks = gpu_pool.get_new_blocks(len(sources))  # ref_cnt=1: pinned in flight
    for gpu_block, cpu_block in zip(gpu_blocks, sources):
        gpu_block._block_hash = cpu_block.block_hash  # claimable under the original hash
    cpu_pool.touch(sources)  # pin mirror sources against LRU during the copy

    block_size = scheduler.kv_cache_config.kv_cache_groups[0].kv_cache_spec.block_size
    live_id = request.request_id
    omni_state.registry.on_materialize_issued(live_id)
    omni_park.log_park(
        f"{time.time():.6f} L req={live_id} cpu_tok={len(sources) * block_size} "
        f"gpu_tok={classification.resident * block_size} trigger=prefetch\n"
    )

    def on_done() -> None:
        omni_state.registry.on_materialize_done(live_id)
        omni_park.log_park(f"{time.time():.6f} R req={live_id} trigger=prefetch\n")

    omni_transfer.enqueue(gpu_blocks, sources, gpu_pool, cpu_pool, on_done)


def _retry_deferred(parked_session, scheduler) -> None:
    """Pacing hook: a park just freed capacity — re-evaluate every deferred
    reload with fresh resolution and classification (nothing stale is ever
    issued; a session whose chunk arrived meanwhile was cancelled by
    on_claimed)."""
    from vllm.v1.request import RequestStatus

    for session in omni_state.registry.sessions.values():
        if not session.deferred_reload:
            continue
        request = omni_park._resolve(scheduler, session.external)
        if request is None or request.status != RequestStatus.WAITING_FOR_STREAMING_REQ:
            session.deferred_reload = False
            continue
        classification = omni_state.registry.classify(scheduler, request)
        if not classification.mirrored:
            session.deferred_reload = False
            continue
        if not _capacity_for(scheduler, classification.missing):
            continue  # stay deferred until the next park
        session.deferred_reload = False
        _issue(scheduler, request, classification)
