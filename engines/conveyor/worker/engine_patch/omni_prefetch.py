"""KV-prefetch command and capacity-aware issuing policy.

``EngineCore.prefetch_kv`` copies host-backed prefix blocks into the GPU
prefix cache before the session's next scheduler admission.  The subsequent
resume uses vLLM's normal prefix-cache match.  Synthetic transport identifiers
and hash registration are implementation details in
``omni_prefetch_transport``; they are not a separate research mechanism.

When the configured free-space margin would be crossed, the request is
deferred.  Each successful partial eviction re-evaluates deferred work, while
the session's own admission cancels its deferred prefetch because the native
on-demand path now owns any missing blocks.  Correctness never depends on
prefetch: refusal, lateness, or later LRU eviction falls back to on-demand
reload or recomputation.
"""

from __future__ import annotations

import os
import time

import omni_evict
import omni_prefetch_transport
import omni_state


MIN_FREE_FRACTION = float(os.environ.get("OMNI_PREFETCH_MIN_FREE", "0.1"))


def apply() -> None:
    """Install transport wrappers, eviction callbacks, and utility methods."""
    omni_prefetch_transport.apply()
    omni_state.registry.on_kv_evicted_hooks.append(_retry_deferred)
    from vllm.v1.engine.core import EngineCore

    EngineCore.prefetch_kv = prefetch_kv
    EngineCore.kv_state = kv_state


def prefetch_kv(self, request_id: str) -> dict:
    """Prefetch the host-backed part of an idle session's reusable KV prefix."""
    scheduler = self.scheduler
    guard = _guards(scheduler)
    if guard:
        return {"prefetched": False, "reason": guard}
    session = omni_state.registry.on_release(request_id)
    request = omni_evict._resolve(scheduler, request_id)
    if request is None:
        return {"prefetched": False, "reason": "unknown request"}
    from vllm.v1.request import RequestStatus

    if request.status != RequestStatus.WAITING_FOR_STREAMING_REQ:
        return {"prefetched": False, "reason": f"not idle: {request.status.name}"}
    if session.prefetch_inflight:
        return {"prefetched": False, "reason": "prefetch in flight"}

    coverage = omni_state.registry.classify(scheduler, request)
    if not coverage.host_backed_blocks:
        return {"prefetched": False, "reason": "no host-backed gap"}
    if not _capacity_for(scheduler, coverage.reloadable_blocks):
        session.deferred_prefetch = True
        return {
            "prefetched": False,
            "reason": "deferred",
            "blocks": coverage.reloadable_blocks,
        }
    _issue(scheduler, request, coverage)
    return {
        "prefetched": True,
        "blocks": coverage.reloadable_blocks,
        "gpu_resident_blocks": coverage.gpu_resident_blocks,
    }


def kv_state(self, request_id: str) -> dict:
    """Return session control facts plus a live block-coverage classification."""
    scheduler = self.scheduler
    view = omni_state.registry.view(request_id)
    request = omni_evict._resolve(scheduler, request_id)
    if request is not None and not _guards(scheduler):
        coverage = omni_state.registry.classify(scheduler, request)
        view.update(
            status=request.status.name,
            total_hashed_blocks=len(request.block_hashes),
            gpu_resident_blocks=coverage.gpu_resident_blocks,
            host_backed_reloadable_blocks=coverage.reloadable_blocks,
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


def _issue(scheduler, request, coverage) -> None:
    """Allocate destinations, record issue/completion, and queue one prefetch."""
    gpu_pool = scheduler.kv_cache_manager.block_pool
    cpu_pool = scheduler.connector.scheduler_manager.cpu_block_pool
    sources = coverage.host_backed_blocks
    gpu_blocks = gpu_pool.get_new_blocks(len(sources))
    for gpu_block, cpu_block in zip(gpu_blocks, sources):
        gpu_block._block_hash = cpu_block.block_hash
    cpu_pool.touch(sources)

    block_size = scheduler.kv_cache_config.kv_cache_groups[0].kv_cache_spec.block_size
    live_id = request.request_id
    omni_state.registry.on_prefetch_issued(live_id)
    omni_evict.log_kv_event(
        f"{time.time():.6f} L req={live_id} cpu_tok={len(sources) * block_size} "
        f"gpu_tok={coverage.gpu_resident_blocks * block_size} trigger=prefetch\n"
    )

    def on_done() -> None:
        omni_state.registry.on_prefetch_done(live_id)
        omni_evict.log_kv_event(
            f"{time.time():.6f} R req={live_id} trigger=prefetch\n"
        )

    omni_prefetch_transport.enqueue(gpu_blocks, sources, gpu_pool, cpu_pool, on_done)


def _retry_deferred(_evicted_session, scheduler) -> None:
    """Re-evaluate deferred prefetches after a partial eviction frees blocks."""
    from vllm.v1.request import RequestStatus

    for session in omni_state.registry.sessions.values():
        if not session.deferred_prefetch:
            continue
        request = omni_evict._resolve(scheduler, session.external)
        if request is None or request.status != RequestStatus.WAITING_FOR_STREAMING_REQ:
            session.deferred_prefetch = False
            continue
        coverage = omni_state.registry.classify(scheduler, request)
        if not coverage.host_backed_blocks:
            session.deferred_prefetch = False
            continue
        if not _capacity_for(scheduler, coverage.reloadable_blocks):
            continue
        session.deferred_prefetch = False
        _issue(scheduler, request, coverage)
