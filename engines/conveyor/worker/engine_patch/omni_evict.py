"""Partial KV eviction, host-backing instrumentation, and resume fixes.

For an idle resumable request, ``EngineCore.evict_tail_blocks`` first releases
request ownership with ``kv_cache_manager.free(request)`` and then removes the
selected tail hashes with ``evict_blocks``.  The surviving cached prefix can be
reused on the next input.  Host-backed evicted blocks are reloaded through
vLLM's existing offload connector; an uncovered suffix is recomputed.  The
implementation therefore records host coverage but does not claim that every
evicted block already has a host copy.

The main mode applies this operation when a generation segment stops and keeps
``OMNI_RETAINED_PREFIX_BLOCKS`` blocks, plus a short uncovered-tail margin, on
the GPU.  A fixed-tail utility remains available for controlled experiments.
Initial-context preloading temporarily holds automatic eviction because host
copies can still be incomplete when the initialization barrier ends.

This module also refreshes per-segment ``max_tokens`` and repairs the upstream
eager-store cursor on streaming re-entry.  New evidence is written to
``kv_events.log`` with four explicit row kinds: ``E`` partial eviction, ``B``
host-backing progress, ``L`` load issue, and ``R`` load completion.
"""

from __future__ import annotations

import os
import time

import omni_state


# Warmup sentinel request-id prefix: worker sid 10**9 becomes request id
# "s1000000000e1". The worker and infra/trace/parse.py declare the same sentinel
# on their side of the process boundary; a contract test pins all three.
WARMUP_REQ_PREFIX = f"s{10**9}e"

_kv_event_log_path = os.environ.get("OMNI_KV_EVENTS_LOG")
_kv_event_log = [None]


def log_kv_event(line: str) -> None:
    """Append one line to the shared ``kv_events.log`` artifact."""
    if not _kv_event_log_path:
        return
    if _kv_event_log[0] is None:
        _kv_event_log[0] = open(_kv_event_log_path, "a", buffering=1, encoding="utf-8")
    _kv_event_log[0].write(line)


def _resolve(scheduler, external_id: str):
    """External id -> live request (input processor appends '-<8 chars>')."""
    request = scheduler.requests.get(external_id)
    if request is not None:
        return request
    prefix = external_id + "-"
    return next(
        (r for rid, r in scheduler.requests.items() if rid.startswith(prefix)),
        None,
    )


def _gpu_cached_chain(kvm, request) -> list[int]:
    """Block ids of the request's longest still-GPU-cached prefix chain,
    reconstructed from its block hashes (deepen path: the request holds
    no blocks because it is already KV-evicted). Caveat: the hash map keeps
    duplicates and returns the first copy — under this workload's
    per-session unique prefixes duplicates are absent in practice."""
    chain: list[int] = []
    pool = kvm.block_pool
    for block_hash in request.block_hashes:
        hit = pool.get_cached_block(block_hash, [0])
        if not hit:
            break
        chain.append(hit[0].block_id)
    return chain


def _evict_idle_kv(
    scheduler,
    request,
    tail_blocks=0,
    retained_prefix_blocks=None,
    tail_margin=0,
) -> dict:
    """Core of the primitive: release the (already idle) request's KV
    ownership and evict tail blocks. Fixed mode (tail_blocks) or a
    retained GPU prefix (retained_prefix_blocks) bounds idle-session
    occupancy while context grows. tail_margin spares newest blocks whose
    CPU-store may not have been ISSUED yet (the stop-instant race:
    specs for a step's final blocks are prepared one step later)."""
    kvm = scheduler.kv_cache_manager
    usage_before = kvm.usage
    owned_before = list(kvm.get_block_ids(request.request_id)[0])
    block_size = scheduler.kv_cache_config.kv_cache_groups[0].kv_cache_spec.block_size
    if owned_before:
        kvm.free(request)
        request._omni_kv_evicted = True
        # only blocks REGISTERED in the prefix cache are evictable and
        # reloadable: that is the first num_computed_tokens//block_size
        # blocks. request.block_hashes can run one entry ahead of the
        # registered set (the hash exists once the tokens do, the cache
        # entry only after cache_blocks ran), so it must not be the cut.
        chain = owned_before[: request.num_computed_tokens // block_size]
    else:
        chain = _gpu_cached_chain(kvm, request)
    # never evict block 0: it holds the system-prompt HEAD shared by
    # every session via prefix-cache dedup — destroying its hash entry
    # would cost all future sessions their head hit.
    if retained_prefix_blocks is not None:
        start = max(int(retained_prefix_blocks), 1)
    elif tail_blocks > 0:
        start = max(len(chain) - tail_blocks, 1)
    else:
        start = len(chain)
    end = len(chain) - tail_margin if tail_margin else len(chain)
    evicted = chain[start:end] if end > start else []
    if evicted:
        kvm.evict_blocks(set(evicted))
    # read-only peek: how much of the evicted tail the host backing holds
    # (-1 = peek failed; the uncovered remainder recomputes on resume).
    # LOWER BOUND: entries appear only when a store is CONFIRMED (~one
    # engine step after the copy). fa_gidx as the group id matches the
    # GPU-side group id only because both are 0 in the single-group
    # config — the multi-group guard is what makes this line correct.
    try:
        manager = scheduler.connector.scheduler_manager
        first = start
        count = 0
        for index in range(first, first + len(evicted)):
            if manager.cpu_block_pool.get_cached_block(
                request.block_hashes[index], [manager.fa_gidx]
            ):
                count += 1
        host_backed = count
    except Exception:
        host_backed = -1
    result = {
        "kv_evicted": True,
        "owned_before": len(owned_before),
        "evicted": len(evicted),
        "host_backed": host_backed,
        "usage_before": round(usage_before, 4),
        "usage_after": round(kvm.usage, 4),
    }
    fields = " ".join(f"{key}={value}" for key, value in result.items() if key != "kv_evicted")
    log_kv_event(f"{time.time():.6f} E req={request.request_id} {fields}\n")
    omni_state.registry.on_kv_evicted(request.request_id, scheduler)
    return result


def apply() -> None:
    """Install the KV eviction primitive, automatic KV eviction, and its instrumentation.

    Called by the sitecustomize loader under the ``OMNI_KV_EVICTION`` gate;
    everything below mutates vLLM classes, so it must never run on import.
    """
    from vllm.v1.core.sched.scheduler import Scheduler
    from vllm.v1.engine.core import EngineCore
    from vllm.v1.request import RequestStatus

    def evict_tail_blocks(
        self,
        request_id: str,
        tail_blocks: int,
        retained_prefix_blocks=None,
    ) -> dict:
        """RPC surface of the primitive (call_utility). Guards, resolves the
        external id, requires the idle state, then delegates to
        _evict_idle_kv. retained_prefix_blocks is an experimental override;
        the main retained-prefix mode invokes the operation at segment stop.
        Returns the facts; never raises for policy reasons."""
        scheduler = self.scheduler
        # single full-attention KV group is a stack assumption (Qwen2.5-Omni
        # thinker); the [0]s in the core rely on it. Serialization with
        # schedule() relies on utility calls running synchronously on the
        # busy loop, which async scheduling would break.
        if len(scheduler.kv_cache_config.kv_cache_groups) != 1:
            return {"kv_evicted": False, "reason": "multi-group KV not supported"}
        if getattr(scheduler.scheduler_config, "async_scheduling", False):
            return {"kv_evicted": False, "reason": "async scheduling not supported"}
        request = _resolve(scheduler, request_id)
        if request is None:
            return {"kv_evicted": False, "reason": "unknown request"}
        if request.status != RequestStatus.WAITING_FOR_STREAMING_REQ:
            return {"kv_evicted": False, "reason": f"not idle: {request.status.name}"}
        return _evict_idle_kv(
            scheduler,
            request,
            tail_blocks=tail_blocks,
            retained_prefix_blocks=retained_prefix_blocks,
        )

    EngineCore.evict_tail_blocks = evict_tail_blocks

    # Automatic partial eviction at the idle transition.
    # The instant a resumable session reaches its configured output cap it enters
    # WAITING_FOR_STREAMING_REQ inside _handle_stopped_request — that line
    # IS "decode just ended". KV eviction right there (retained-prefix mode) needs no
    # timer and no RPC, is serialized with the scheduler by construction,
    # and shrinks the full-residency window to the compute window itself —
    # which is what bounds concurrent full-residency sessions to ~the batch
    # The worker-side fixed-tail timer remains for controlled experiments.
    _retained_prefix = int(os.environ.get("OMNI_RETAINED_PREFIX_BLOCKS", "0")) or None
    _automatic_eviction_on = [not os.environ.get("OMNI_HOLD_KV_EVICTION")]

    def initial_context_finalize(self) -> dict:
        """Release the hold without evicting at the initialization barrier.

        Host backing may still be incomplete because copy issuance follows
        each request's own engine iterations.  The first normal segment
        therefore runs with its existing GPU blocks and establishes the
        retained-prefix posture only when that segment becomes idle.
        """
        _automatic_eviction_on[0] = True
        return {"automatic_kv_eviction": "enabled"}

    EngineCore.initial_context_finalize = initial_context_finalize

    if _retained_prefix:
        _original_stopped = Scheduler._handle_stopped_request

        def _handle_stopped_request(self, request):
            finished = _original_stopped(self, request)
            if (
                _automatic_eviction_on[0]
                and not finished
                and request.resumable
                and request.status == RequestStatus.WAITING_FOR_STREAMING_REQ
                and not request.request_id.startswith(WARMUP_REQ_PREFIX)
                and len(self.kv_cache_config.kv_cache_groups) == 1
                and not getattr(self.scheduler_config, "async_scheduling", False)
            ):
                try:
                    _evict_idle_kv(
                        self,
                        request,
                        retained_prefix_blocks=_retained_prefix,
                        tail_margin=2,
                    )
                except Exception as error:
                    _fail("automatic KV eviction", error)
            return finished

        Scheduler._handle_stopped_request = _handle_stopped_request

    _reset_warned = [False]

    def _reset_store_cursor(scheduler, request) -> None:
        """C1 fix: upstream eager-store state accumulates a duplicate full
        block list on every streaming re-entry (it resets only on
        preempted=True), drifting the store cursor so the session's newest
        tail blocks never get scanned or copied to host. On every re-entry, empty
        the list (the next schedule re-delivers the full list via
        scheduled_new_reqs) and position the cursor at the host backing's
        actual frontier — walking the request's block hashes against the
        CPU cache map — so the next pass scans exactly the uncovered tail.
        (Positioning at 0 would also be correct — dedup skips covered
        blocks — but the cursor would re-advance over the whole context
        every chunk, which both wastes scans and inflates the B-event
        host-backing accounting into a rescan counter.)"""
        try:
            manager = scheduler.connector.scheduler_manager
            state = manager._reqs_to_store.get(request.request_id)
            if state is not None and not state.finished:
                groups = len(manager.cpu_kv_cache_config.kv_cache_groups)
                covered = 0
                if groups == 1:
                    for block_hash in request.block_hashes:
                        if not manager.cpu_block_pool.get_cached_block(
                            block_hash, [manager.fa_gidx]
                        ):
                            break
                        covered += 1
                state.block_ids = tuple([] for _ in range(groups))
                state.num_stored_blocks = [covered] * groups
        except Exception as error:
            if not _reset_warned[0]:
                _reset_warned[0] = True
                _fail("store-cursor reset", error)

    _original_update = Scheduler._update_request_as_session

    def _update_request_as_session(self, session, update):
        # Sessions whose tail was evicted keep valid num_computed_tokens until
        # original history trimming works; zero it AFTER so the scheduler
        # takes the num_computed_tokens==0 path (GPU prefix match + CPU
        # tail reload) instead of assuming resident blocks.
        _original_update(self, session, update)
        _reset_store_cursor(self, session)
        # Upstream gap: the stop check reads session.max_tokens, which is
        # frozen at construction (the FIRST streaming input's params — the
        # initial context's max_tokens=1 when initial-context preloading is on). The original update
        # replaces sampling_params but never this field; refresh it so each
        # segment runs under the params the worker actually sent. Output
        # tokens fold into the prompt every chunk, so the cap is
        # PER-SEGMENT.
        if update is not None and update.sampling_params is not None:
            session.max_tokens = update.sampling_params.max_tokens
        if getattr(session, "_omni_kv_evicted", False):
            session._omni_kv_evicted = False
            session.num_computed_tokens = 0
        # Scheduler admission makes any deferred prefetch moot; the native
        # on-demand path owns whatever is still missing from here.
        omni_state.registry.on_session_resumed(session.request_id, self)

    Scheduler._update_request_as_session = _update_request_as_session

    # On-demand reload instrumentation: L at issue, R at completion.
    # Resuming a session with missing host-backed blocks triggers an async load;
    # Without these two wrappers, that window exists in no artifact (the scheduler
    # trace only records scheduled tokens, and a loading request schedules
    # none). L = load admitted (blocks allocated, request enters
    # WAITING_FOR_REMOTE_KVS), R = load finished (request resumes).
    # the trace parser pairs them into per-session reload slices on the timeline.
    from vllm.distributed.kv_transfer.kv_connector.v1.simple_cpu_offload_connector import (  # noqa: E501
        SimpleCPUOffloadConnector,
    )

    _original_alloc = SimpleCPUOffloadConnector.update_state_after_alloc

    def _traced_alloc(self, request, blocks, num_external_tokens):
        if num_external_tokens > 0:
            # cpu_tok is exact (the CPU-supplied span); gpu_tok is the
            # request's computed count at allocation time (best-effort).
            log_kv_event(
                f"{time.time():.6f} L req={request.request_id} "
                f"cpu_tok={num_external_tokens} gpu_tok={request.num_computed_tokens} "
                f"trigger=demand\n"
            )
        return _original_alloc(self, request, blocks, num_external_tokens)

    SimpleCPUOffloadConnector.update_state_after_alloc = _traced_alloc

    _original_remote_done = Scheduler._update_waiting_for_remote_kv

    def _traced_remote_done(self, request):
        log_kv_event(f"{time.time():.6f} R req={request.request_id} trigger=demand\n")
        return _original_remote_done(self, request)

    Scheduler._update_waiting_for_remote_kv = _traced_remote_done

    # Host-backing instrumentation: B records frontier advancement.
    # The connector's GPU-to-host copies are otherwise invisible. Diff
    # each request's stored-block cursor around the store-spec pass and
    # log the per-request delta — one B line per session per engine iteration whose
    # host-backing frontier advanced. NOTE: the cursor also advances over
    # hash-dedup-skipped and null blocks, so `blocks` = frontier advance
    # (an upper bound on blocks actually copied; the two coincide in this
    # workload's unique-prefix sessions).
    from vllm.v1.simple_kv_offload.manager import SimpleCPUOffloadScheduler

    _original_store_specs = SimpleCPUOffloadScheduler._prepare_eager_store_specs

    def _traced_store_specs(self, scheduler_output):
        before = {
            req_id: sum(state.num_stored_blocks)
            for req_id, state in self._reqs_to_store.items()
        }
        result = _original_store_specs(self, scheduler_output)
        now = time.time()
        for req_id, state in self._reqs_to_store.items():
            delta = sum(state.num_stored_blocks) - before.get(req_id, 0)
            if delta > 0:
                log_kv_event(f"{now:.6f} B req={req_id} blocks={delta}\n")
        return result

    SimpleCPUOffloadScheduler._prepare_eager_store_specs = _traced_store_specs


def _fail(stage: str, error: Exception) -> None:
    import sys

    print(f"KV eviction patch {stage} failed: {error!r}", file=sys.stderr, flush=True)
