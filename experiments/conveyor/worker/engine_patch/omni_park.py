"""KV partial-release primitive (park), applied by the engine_patch loader.

Moved verbatim from the old monolithic ``sitecustomize.py`` — the loader
(`sitecustomize.py` in this directory) calls :func:`apply` under the
``OMNI_PARK_PATCH`` gate; importing this module patches NOTHING. Shared
plumbing that other mechanisms reuse lives at module level: the park.log
writer (:func:`log_park`), the external-id resolver (:func:`_resolve`), and
the warmup sentinel contract (``WARMUP_REQ_PREFIX``).

The primitive: ``EngineCore.park_tail_blocks(request_id, nblocks)`` — called
from the worker process via ``EngineCoreClient.call_utility_async`` (the
engine's generic utility RPC dispatches on ``getattr(self, name)``). The
caller passes the EXTERNAL request id ("s<sid>e1"); vLLM's input processor
renames requests internally to "<external>-<8 random chars>", so the primitive
resolves by prefix. For an IDLE resumable session
(``WAITING_FOR_STREAMING_REQ``) it releases the request's grip on its
resident KV and destroys exactly the last ``nblocks`` hashed blocks:

  1. ``kv_cache_manager.free(request)`` — every block moves to the cached-free
     LRU tail-first (hashes kept, contents intact): the space is allocatable
     immediately, and the prefix is re-acquired for free via GPU hash match on
     resume. Freeing everything (rather than only the tail) is what lets
     resume ride vLLM's EXISTING new-request path — partial ownership has no
     scheduler support and would need invasive surgery.
  2. ``evict_blocks(last nblocks hashed blocks)`` — the chosen tail loses its
     hash entries: deterministically destroyed, not lazily. The unhashed
     partial tail block (if any) carries no reusable KV and is excluded from
     the count.

The request keeps a valid ``num_computed_tokens`` while parked — zeroing it
here would corrupt ``_update_request_as_session``'s token bookkeeping (it
slices the session's history with it). Instead park marks the request, and a
wrapper around ``Scheduler._update_request_as_session`` lets the original run
with the valid value on the next chunk (correct history trimming), THEN zeroes
it. The scheduler's normal waiting path (``num_computed_tokens == 0``) does
the rest: GPU hash match re-acquires the surviving prefix, and
``SimpleCPUOffloadConnector`` supplies the evicted tail from the host mirror
(async load, ``WAITING_FOR_REMOTE_KVS``) instead of recomputing. The eager
mirror confirms stores with ~one engine-step lag, so the newest full block may
not be CPU-covered yet — uncovered tail tokens recompute on resume; the
returned ``cpu_covered`` counts exactly this (a LOWER BOUND: it can only see
confirmed stores).

The same wrapper also fixes an upstream eager-store bug this workload trips
(audit C1): ``SimpleCPUOffloadScheduler._prepare_eager_store_specs`` resets
its per-request block list only on ``preempted=True``, but a resumable
streaming session re-enters ``scheduled_new_reqs`` on EVERY chunk with its
full block list, so the list accumulates duplicates and the store cursor
drifts into stale territory — the session's newest tail blocks never enter
the scan window and the CPU mirror stops covering exactly the region park
evicts. The wrapper therefore resets the connector store state (the
``preempted`` branch, applied by hand) on every streaming re-entry, for every
session — the next store pass rescans the full list and hash-dedup skips
what's already mirrored.

An already-parked session can be parked DEEPER (manual/experimental path, the
worker's per-slice policy never hits it): the surviving GPU-cached chain is
reconstructed from ``request.block_hashes`` and its tail evicted.

THE MAIN PATH IS AUTO-PARK: with ``OMNI_PARK_KEEP=<K blocks>`` set (quota
mode), a wrapper around ``Scheduler._handle_stopped_request`` parks each
session the instant its segment stops — zero delay, no RPC, serialized with
the scheduler by construction. ``OMNI_PARK_HOLD`` suspends auto-park through
the warm-start barrier (seeding must not interleave with any mechanism), and
``warm_start_finalize`` releases the hold WITHOUT parking — at seed-end the
mirror is structurally incomplete (issuance rides each request's own steps;
the copy stream is starved by seed compute), so cycle 1 runs fully resident
and the first organic auto-park lands the steady posture. The RPC surface
above remains for fixed-tail experiments. A second wrapper around
``_update_request_as_session`` does three per-chunk jobs: reset the
eager-store cursor (upstream bug: it accumulates duplicates on streaming
re-entry), refresh ``session.max_tokens`` (upstream bug: the stop check reads
a value frozen at construction — the seed's max_tokens=1 would pin every
segment to 1 token), and zero ``num_computed_tokens`` for parked sessions so
resume takes the match path.

Evidence: OMNI_PARK_LOG carries FOUR line kinds, all epoch-clock —
``<epoch> req=<id> held=.. evicted=.. cpu_covered=..`` (one per park),
``<epoch> S req=<id> blocks=<n>`` (mirror-copy issuance = offload activity),
``<epoch> L req=<id> cpu_tok=<n> gpu_tok=<m> trigger=demand|prefetch``
(load admitted; demand = WAITING_FOR_REMOTE_KVS on resume, prefetch =
anonymous materialization issued by omni_prefetch) and ``<epoch> R req=<id>
[trigger=prefetch]`` (that load completed). tracekit parses all four
(parse_park, pairing L/R per (req, trigger)) and renders them as PARK
instants, KV mirror instants and paired KV-reload/prefetch slices; the runner
treats a park-enabled run whose log holds zero park lines as a run issue.
"""

from __future__ import annotations

import os
import time

import omni_state


# Warmup sentinel request-id prefix: worker sid 10**9 becomes request id
# "s1000000000e1". The worker and tracekit/parse.py declare the same sentinel
# on their side of the process boundary; a contract test pins all three.
WARMUP_REQ_PREFIX = f"s{10**9}e"

_park_log_path = os.environ.get("OMNI_PARK_LOG")
_park_log = [None]  # lazy-open: only the process that parks (EngineCore) holds a handle


def log_park(line: str) -> None:
    """Append one evidence line to park.log (shared by park and prefetch)."""
    if not _park_log_path:
        return
    if _park_log[0] is None:
        _park_log[0] = open(_park_log_path, "a", buffering=1, encoding="utf-8")
    _park_log[0].write(line)


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
    no blocks because it is already parked). Caveat: the hash map keeps
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


def _park_request(scheduler, request, nblocks=0, keep_blocks=None,
                  tail_margin=0) -> dict:
    """Core of the primitive: release the (already idle) request's KV
    grip and destroy tail blocks. Fixed mode (nblocks) or resident
    quota (keep_blocks — destroy everything beyond it; the idle-time
    floor stays pinned at K while the context grows, which is what
    caps pool demand). tail_margin spares the newest blocks whose
    CPU-store may not have been ISSUED yet (the stop-instant race:
    specs for a step's final blocks are prepared one step later)."""
    kvm = scheduler.kv_cache_manager
    usage_before = kvm.usage
    held = list(kvm.get_block_ids(request.request_id)[0])  # [] if already parked
    block_size = scheduler.kv_cache_config.kv_cache_groups[0].kv_cache_spec.block_size
    if held:
        kvm.free(request)
        request._omni_parked = True  # consumed by the session-update wrapper
        # only blocks REGISTERED in the prefix cache are evictable and
        # reloadable: that is the first num_computed_tokens//block_size
        # blocks. request.block_hashes can run one entry ahead of the
        # registered set (the hash exists once the tokens do, the cache
        # entry only after cache_blocks ran), so it must not be the cut.
        chain = held[: request.num_computed_tokens // block_size]
    else:
        chain = _gpu_cached_chain(kvm, request)
    # never evict block 0: it holds the system-prompt HEAD shared by
    # every session via prefix-cache dedup — destroying its hash entry
    # would cost all future sessions their head hit.
    if keep_blocks is not None:
        start = max(int(keep_blocks), 1)
    elif nblocks > 0:
        start = max(len(chain) - nblocks, 1)
    else:
        start = len(chain)
    end = len(chain) - tail_margin if tail_margin else len(chain)
    evicted = chain[start:end] if end > start else []
    if evicted:
        kvm.evict_blocks(set(evicted))
    # read-only peek: how much of the evicted tail the CPU mirror holds
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
        cpu_covered = count
    except Exception:
        cpu_covered = -1
    result = {
        "parked": True,
        "held": len(held),
        "evicted": len(evicted),
        "cpu_covered": cpu_covered,
        "usage_before": round(usage_before, 4),
        "usage_after": round(kvm.usage, 4),
    }
    fields = " ".join(f"{k}={v}" for k, v in result.items() if k != "parked")
    log_park(f"{time.time():.6f} req={request.request_id} {fields}\n")
    # state authority: a park is THE capacity-freeing event — reporting it
    # here (single choke point: RPC, auto-park and deepen all pass through)
    # lets pacing policies re-evaluate deferred reloads immediately.
    omni_state.registry.on_parked(request.request_id, scheduler)
    return result


def apply() -> None:
    """Install the park primitive, auto-park, and its instrumentation.

    Called by the sitecustomize loader under the ``OMNI_PARK_PATCH`` gate;
    everything below mutates vLLM classes, so it must never run on import.
    """
    from vllm.v1.core.sched.scheduler import Scheduler
    from vllm.v1.engine.core import EngineCore
    from vllm.v1.request import RequestStatus

    def park_tail_blocks(self, request_id: str, nblocks: int, keep_blocks=None) -> dict:
        """RPC surface of the primitive (call_utility). Guards, resolves the
        external id, requires the idle state, then delegates to
        _park_request. keep_blocks here is a MANUAL/experimental override
        (production quota mode is the auto-park wrapper, not this RPC).
        Returns the facts; never raises for policy reasons."""
        scheduler = self.scheduler
        # single full-attention KV group is a stack assumption (Qwen2.5-Omni
        # thinker); the [0]s in the core rely on it. Serialization with
        # schedule() relies on utility calls running synchronously on the
        # busy loop, which async scheduling would break.
        if len(scheduler.kv_cache_config.kv_cache_groups) != 1:
            return {"parked": False, "reason": "multi-group KV not supported"}
        if getattr(scheduler.scheduler_config, "async_scheduling", False):
            return {"parked": False, "reason": "async scheduling not supported"}
        request = _resolve(scheduler, request_id)
        if request is None:
            return {"parked": False, "reason": "unknown request"}
        if request.status != RequestStatus.WAITING_FOR_STREAMING_REQ:
            return {"parked": False, "reason": f"not idle: {request.status.name}"}
        return _park_request(scheduler, request, nblocks=nblocks, keep_blocks=keep_blocks)

    EngineCore.park_tail_blocks = park_tail_blocks

    # ---- auto-park on stop: OMNI_PARK_KEEP=<K blocks> ----
    # The instant a resumable session exhausts its segment quota it enters
    # WAITING_FOR_STREAMING_REQ inside _handle_stopped_request — that line
    # IS "decode just ended". Parking right there (quota mode) needs no
    # timer and no RPC, is serialized with the scheduler by construction,
    # and shrinks the full-residency window to the compute window itself —
    # which is what bounds concurrent full-residency sessions to ~the batch
    # (worker-side --park-tail-blocks timer mode remains for experiments).
    _auto_keep = int(os.environ.get("OMNI_PARK_KEEP", "0")) or None
    # OMNI_PARK_HOLD: warm start is a one-shot STATE CONSTRUCTION — during
    # the seed phase auto-park stays off (sessions remain fully resident,
    # no mechanism interleaves with seeding); warm_start_finalize() then
    # releases this gate.
    _auto_park_on = [not os.environ.get("OMNI_PARK_HOLD")]

    def warm_start_finalize(self) -> dict:
        """Barrier tail (utility RPC): release the auto-park hold — and
        deliberately do NOT park here. At seed-end the mirror cannot be
        complete (store issuance rides each request's OWN scheduling steps,
        so a stopped session's remaining seed blocks are un-issued; and the
        low-priority copy stream crawls while seeds saturate the GPU), so a
        barrier park would evict uncovered blocks and turn the first tick
        into a full seed RECOMPUTE. Instead cycle 1 runs fully resident
        (5b path, no reload), its steps carry the remaining issuances, and
        the FIRST auto-park at slice-1's stop lands everyone in the
        steady-state posture with the mirror organically complete."""
        _auto_park_on[0] = True
        return {"auto_park": "enabled"}

    EngineCore.warm_start_finalize = warm_start_finalize

    if _auto_keep:
        _original_stopped = Scheduler._handle_stopped_request

        def _handle_stopped_request(self, request):
            finished = _original_stopped(self, request)
            if (
                _auto_park_on[0]
                and not finished
                and request.resumable
                and request.status == RequestStatus.WAITING_FOR_STREAMING_REQ
                and not request.request_id.startswith(WARMUP_REQ_PREFIX)
                and len(self.kv_cache_config.kv_cache_groups) == 1
                and not getattr(self.scheduler_config, "async_scheduling", False)
            ):
                try:
                    _park_request(
                        self, request, keep_blocks=_auto_keep, tail_margin=2
                    )
                except Exception as error:
                    _fail("auto-park", error)
            return finished

        Scheduler._handle_stopped_request = _handle_stopped_request

    _reset_warned = [False]

    def _reset_store_cursor(scheduler, request) -> None:
        """C1 fix: upstream eager-store state accumulates a duplicate full
        block list on every streaming re-entry (it resets only on
        preempted=True), drifting the store cursor so the session's newest
        tail blocks never get scanned or mirrored. On every re-entry, empty
        the list (the next schedule re-delivers the full list via
        scheduled_new_reqs) and position the cursor at the CPU mirror's
        actual frontier — walking the request's block hashes against the
        CPU cache map — so the next pass scans exactly the uncovered tail.
        (Positioning at 0 would also be correct — dedup skips covered
        blocks — but the cursor would re-advance over the whole context
        every chunk, which both wastes scans and inflates the S-line
        offload accounting into a rescan counter.)"""
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
        # Parked sessions kept their valid num_computed_tokens so the
        # original history trimming works; zero it AFTER so the scheduler
        # takes the num_computed_tokens==0 path (GPU prefix match + CPU
        # tail reload) instead of assuming resident blocks.
        _original_update(self, session, update)
        _reset_store_cursor(self, session)
        # Upstream gap: the stop check reads session.max_tokens, which is
        # frozen at construction (the FIRST streaming input's params — the
        # seed's max_tokens=1 when warm-start is on). The original update
        # replaces sampling_params but never this field; refresh it so each
        # segment runs under the params the worker actually sent. Output
        # tokens fold into the prompt every chunk, so the cap is
        # PER-SEGMENT.
        if update is not None and update.sampling_params is not None:
            session.max_tokens = update.sampling_params.max_tokens
        if getattr(session, "_omni_parked", False):
            session._omni_parked = False
            session.num_computed_tokens = 0
        # state authority: the chunk reached the scheduler — the claim
        # moment; cancels any deferred reload for this session (the demand
        # path owns whatever is still missing from here).
        omni_state.registry.on_claimed(session.request_id, self)

    Scheduler._update_request_as_session = _update_request_as_session

    # ---- reload-window instrumentation: L/R lines in park.log ----
    # A parked session's resume triggers an async CPU->GPU load; without
    # these two wrappers that window exists in NO artifact (the scheduler
    # trace only records scheduled tokens, and a loading request schedules
    # none). L = load admitted (blocks allocated, request enters
    # WAITING_FOR_REMOTE_KVS), R = load finished (request resumes).
    # tracekit pairs them into per-session reload slices on the timeline.
    from vllm.distributed.kv_transfer.kv_connector.v1.simple_cpu_offload_connector import (  # noqa: E501
        SimpleCPUOffloadConnector,
    )

    _original_alloc = SimpleCPUOffloadConnector.update_state_after_alloc

    def _traced_alloc(self, request, blocks, num_external_tokens):
        if num_external_tokens > 0:
            # cpu_tok is exact (the CPU-supplied span); gpu_tok is the
            # request's computed count at allocation time (best-effort).
            log_park(
                f"{time.time():.6f} L req={request.request_id} "
                f"cpu_tok={num_external_tokens} gpu_tok={request.num_computed_tokens} "
                f"trigger=demand\n"
            )
        return _original_alloc(self, request, blocks, num_external_tokens)

    SimpleCPUOffloadConnector.update_state_after_alloc = _traced_alloc

    _original_remote_done = Scheduler._update_waiting_for_remote_kv

    def _traced_remote_done(self, request):
        log_park(f"{time.time():.6f} R req={request.request_id} trigger=demand\n")
        return _original_remote_done(self, request)

    Scheduler._update_waiting_for_remote_kv = _traced_remote_done

    # ---- offload instrumentation: S lines in park.log ----
    # The eager mirror's GPU->CPU copies are otherwise invisible (the
    # "bandwidth" half of bandwidth-for-VRAM would be a black box). Diff
    # each request's stored-block cursor around the store-spec pass and
    # log the per-request delta — one S line per session per step whose
    # mirror frontier advanced. NOTE: the cursor also advances over
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
                log_park(f"{now:.6f} S req={req_id} blocks={delta}\n")
        return result

    SimpleCPUOffloadScheduler._prepare_eager_store_specs = _traced_store_specs


def _fail(stage: str, error: Exception) -> None:
    import sys

    print(f"park patch {stage} failed: {error!r}", file=sys.stderr, flush=True)
