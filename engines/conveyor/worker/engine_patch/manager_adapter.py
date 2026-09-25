"""Single-process vLLM adapter for the independent Session Manager.

The current adapter supports one synchronous full-attention KV group and a
UniProcExecutor. Scheduler mutations take a shared lock; model execution does
not. Sources/destinations stay pinned across queued and in-flight copies.
"""
from __future__ import annotations

import functools
import math
import os
import threading
import time
from dataclasses import replace

import omni_evict
from omni_state import external_id
from session_manager import SessionManager, SessionPlan
from copy_service import CopyService, CudaCopyBackend
from residency_planner import AdmissionProfile, ResidencyPlanner
from infra.trace.collectors.gpu_activity import TransferObserver

_worker = None
_adapter = None
_lock = threading.RLock()


class VllmKVMemoryManager:
    def __init__(self, scheduler, worker):
        self.scheduler = scheduler
        self.lock = _lock
        self.gpu = scheduler.kv_cache_manager.block_pool
        self.native = scheduler.connector.scheduler_manager
        self.cpu = self.native.cpu_block_pool
        self.block_size = scheduler.kv_cache_config.kv_cache_groups[0].kv_cache_spec.block_size
        self.observer = TransferObserver(os.environ.get("OMNI_TRANSFER_EVENTS"))
        self.copies = CopyService(CudaCopyBackend(worker), self.observer)
        self.manager = SessionManager(self)
        self.hold = bool(os.environ.get("OMNI_HOLD_KV_EVICTION"))
        self.min_free = float(os.environ.get("OMNI_PREFETCH_MIN_FREE", "0.1"))
        self.planner = None
        self.closed_sessions = set()
        profile = os.environ.get("OMNI_ADMISSION_PROFILE")
        self.admission_profile = AdmissionProfile.read(profile) if profile else None
        self.next_review = 0.0
        self.manager.start()

    def check_health(self):
        self.copies.check_health()

    def report_error(self, exc):
        self.observer("error", error=repr(exc))

    def release_idle_pins(self, session):
        if session.resident_pins:
            self.gpu.free_blocks(session.resident_pins)
            session.resident_pins = []
        if session.host_pins:
            self.cpu.free_blocks([block for _, block in session.host_pins])
            session.host_pins = []

    def evict(self, session):
        from vllm.v1.request import RequestStatus
        if self.hold:
            return False
        request = omni_evict._resolve(self.scheduler, session.request_id)
        if request is None or request.status != RequestStatus.WAITING_FOR_STREAMING_REQ:
            return False
        kvm = self.scheduler.kv_cache_manager
        owned = list(kvm.get_block_ids(request.request_id)[0])
        complete = min(len(owned), request.num_computed_tokens // self.block_size)
        selected = []
        for index in session.plan.candidates(complete):
            gpu_block = self.gpu.blocks[owned[index]]
            # One reference belongs to this idle request. Extra references
            # include sharing and unfinished stores; neither is reclaimable.
            if gpu_block.ref_cnt != 1 or gpu_block.block_hash is None:
                continue
            hit = self.cpu.get_cached_block(request.block_hashes[index], [self.native.fa_gidx])
            if hit:
                selected.append((index, gpu_block, hit[0]))
            if session.plan.max_evict_blocks and len(selected) >= session.plan.max_evict_blocks:
                break
        if not selected:
            return False
        selected_ids = {block.block_id for _, block, _ in selected}
        kept = [self.gpu.blocks[bid] for bid in owned[:complete] if bid not in selected_ids]
        sources = [block for _, _, block in selected]
        self.gpu.touch(kept)
        self.cpu.touch(sources)  # valid backing survives host LRU until resume/restore
        before = kvm.usage
        kvm.free(request)
        request._omni_kv_evicted = True
        kvm.evict_blocks(selected_ids)
        session.resident_pins = kept
        session.host_pins = [(i, block) for i, _, block in selected]
        omni_evict.log_kv_event(
            f"{time.time():.6f} E req={request.request_id} owned_before={len(owned)} "
            f"evicted={len(selected)} host_backed={len(selected)} "
            f"usage_before={before:.4f} usage_after={kvm.usage:.4f}\n")
        self.observer("evicted", request=request.request_id,
                      logical_blocks=[i for i, _, _ in selected], gpu_blocks=sorted(selected_ids),
                      group=session.plan.group, ceiling_blocks=session.plan.max_evict_blocks,
                      restore_start_epoch=time.time() + session.plan.next_tick - session.plan.restore_lead_s - time.monotonic(),
                      restore_end_epoch=time.time() + session.plan.next_tick - time.monotonic())
        return True

    def restore(self, session):
        sources = sorted((block for _, block in session.host_pins), key=lambda b: b.block_id)
        if self.gpu.get_num_free_blocks() - len(sources) < self.min_free * len(self.gpu.blocks):
            return False
        # Fresh destinations have no logical assignment yet. The allocator's
        # free queue can return a contiguous span in reverse order. Pairing it
        # directly with ascending backing IDs turns one range into hundreds
        # of tiny copies. Assign by physical order, then attach each source's
        # logical hash; prefix lookup still reconstructs the original history.
        targets = sorted(self.gpu.get_new_blocks(len(sources)), key=lambda b: b.block_id)
        for dst, src in zip(targets, sources):
            dst._block_hash = src.block_hash
        session.host_pins = []  # ownership passes to the transfer completion closure
        session.restore_inflight = True
        request = omni_evict._resolve(self.scheduler, session.request_id)
        live_id = request.request_id if request is not None else session.request_id
        planned_tick = session.plan.next_tick
        self.observer('restore_scheduled', request=live_id, group=session.plan.group,
                      blocks=len(sources), ceiling_blocks=session.plan.max_evict_blocks,
                      deadline_epoch=time.time() + planned_tick - time.monotonic())
        omni_evict.log_kv_event(
            f"{time.time():.6f} L req={live_id} cpu_tok={len(sources) * self.block_size} "
            f"gpu_tok={len(session.resident_pins) * self.block_size} trigger=prefetch\n")

        def completed():
            with self.lock:
                if not session.cancelled:
                    for block in targets:
                        self.gpu.cached_block_hash_to_block.insert(block.block_hash, block)
                if not session.cancelled and session.activity == "idle":
                    session.resident_pins.extend(targets)  # keep ready KV until admission
                else:
                    self.gpu.free_blocks(targets)
                self.cpu.free_blocks(sources)
                session.restore_inflight = False
                lateness = time.monotonic() - planned_tick
                if lateness > 0 and not session.cancelled:
                    self.observer('restore_deadline_miss', request=live_id, group=session.plan.group,
                                  lateness_ms=lateness * 1000,
                                  reason='completion exceeded planned restore window')
                omni_evict.log_kv_event(f"{time.time():.6f} R req={live_id} trigger=prefetch\n")
                self.manager.wake.set()

        self.copies.submit("H2D", [b.block_id for b in sources], [b.block_id for b in targets],
                           [live_id], completed)
        return True

    def dispatch(self, meta):
        """Consume native transfer descriptors before returning model metadata.

        Native allocation/coverage logic remains authoritative. Its reference
        release and host-cache publication run from independent callbacks.
        """
        if meta.load_cpu_blocks:
            load_requests = tuple(meta.load_event_to_reqs[meta.load_event])

            def loads_done():
                from vllm.v1.outputs import KVConnectorOutput
                with self.lock:
                    self.scheduler._update_from_kv_xfer_finished(
                        KVConnectorOutput(finished_recving=set(load_requests)))
                    self.manager.wake.set()

            self.copies.submit("H2D", meta.load_cpu_blocks, meta.load_gpu_blocks,
                               load_requests, loads_done)
            meta.load_cpu_blocks = []
            meta.load_gpu_blocks = []
            meta.load_event = -1
        if meta.store_gpu_blocks:
            event = meta.store_event
            store_requests = tuple(self.native._store_event_to_reqs.get(event, []))

            def stores_done():
                with self.lock:
                    self.native._process_store_event(event)
                    self.manager.wake.set()

            self.copies.submit("D2H", meta.store_gpu_blocks, meta.store_cpu_blocks,
                               store_requests, stores_done)
            meta.store_gpu_blocks = []
            meta.store_cpu_blocks = []
            meta.store_event = -1
        # Copy pins prevent allocator reuse even during request preemption.
        # No native worker transfers exist to flush or poll.
        meta.need_flush = False
        return meta

    def close(self):
        self.copies.close()
        self.observer.close()

    def admit(self, request_id, period_s, slots, epoch):
        """Plan without allocating; actual pools remain the state authority."""
        with self.lock:
            self.check_health()
            if request_id in self.closed_sessions:
                raise ValueError('cannot admit a closed session identity')
            if self.admission_profile is None:
                raise ValueError("admission requires an explicit calibrated profile")
            if self.planner is None:
                # Admission must honor the allocator's actual restore guard;
                # a smaller user margin cannot spend those reserved blocks.
                effective = replace(
                    self.admission_profile,
                    gpu_reserve_blocks=max(self.admission_profile.gpu_reserve_blocks,
                                           math.ceil(self.min_free * len(self.gpu.blocks)), 1),
                    host_reserve_blocks=max(self.admission_profile.host_reserve_blocks, 1))
                self.planner = ResidencyPlanner(
                    effective, period_s=period_s, slots=slots, epoch=epoch,
                    restore_lead_s=float(os.environ['OMNI_RESTORE_LEAD_S']),
                    retained_prefix_blocks=int(os.environ['OMNI_RETAINED_PREFIX_BLOCKS']),
                    gpu_blocks=len(self.gpu.blocks), host_blocks=len(self.cpu.blocks))
            if (period_s, slots, epoch) != (self.planner.period_s, self.planner.slots, self.planner.epoch):
                raise ValueError("cannot replace a live admission grid")
            current = {external_id(r.request_id): (r.num_tokens + self.block_size - 1) // self.block_size
                       for r in self.scheduler.requests.values()}
            result = self.planner.try_admit(
                request_id, now=time.time(), current_blocks=current,
                used_gpu_blocks=len(self.gpu.blocks) - self.gpu.get_num_free_blocks(),
                recoverable_blocks=self.recoverable_snapshot())
            if result.get('admitted'):
                self.observer('admitted', request=request_id, **result)
            return result

    def review_plan(self):
        if self.planner is None or time.monotonic() < self.next_review:
            return
        self.next_review = time.monotonic() + self.admission_profile.horizon_s / 2
        current = {external_id(r.request_id): (r.num_tokens + self.block_size - 1) // self.block_size
                   for r in self.scheduler.requests.values()}
        result = self.planner.revalidate(
            now=time.time(), current_blocks=current,
            used_gpu_blocks=len(self.gpu.blocks) - self.gpu.get_num_free_blocks(),
            recoverable_blocks=self.recoverable_snapshot())
        self.observer('plan_review', **result)

    def recoverable_snapshot(self):
        """Conservative forecast credit, read under the allocator guard.

        Count only complete, confirmed host-backed history beyond retention;
        shared GPU blocks cannot supply another session's capacity. Missing
        GPU content with valid host backing is already recoverable state.
        """
        result = {}
        for rid, plan in self.planner.plans.items():
            request = omni_evict._resolve(self.scheduler, rid)
            count = 0
            if request is not None:
                complete = request.num_computed_tokens // self.block_size
                for block_hash in request.block_hashes[plan.retained_prefix_blocks:complete]:
                    host = self.cpu.get_cached_block(block_hash, [self.native.fa_gidx])
                    gpu = self.gpu.get_cached_block(block_hash, [self.native.fa_gidx])
                    if host and (not gpu or gpu[0].ref_cnt <= 1):
                        count += 1
            result[rid] = count
        return result

    def release_session(self, request_id):
        """Release a planning reservation only after all physical owners drain."""
        with self.lock:
            self.check_health()
            self.closed_sessions.add(request_id)
            self.manager.cancel(request_id)
            active = any(external_id(rid) == request_id for rid in self.scheduler.requests)
            copying = any(external_id(rid) == request_id for rid in self.copies.pending_requests())
            if active or copying:
                return {'released': False, 'reason': 'execution_or_copy_in_flight'}
            if self.planner is not None:
                self.planner.release(request_id)
            self.observer('session_released', request=request_id)
            return {'released': True}

    def prepare_input(self, request_id, work_id):
        """Reserve valid history for one periodic input before backend ingest."""
        from vllm.v1.request import RequestStatus
        with self.lock:
            self.check_health()
            if request_id in self.closed_sessions:
                raise ValueError('session is closing')
            session = self.manager.sessions[request_id]
            if session.pending_work == work_id:
                return {'ready': True}
            if session.pending_work is not None:
                return {'ready': False, 'reason': 'prior_input'}
            request = omni_evict._resolve(self.scheduler, request_id)
            if request is not None and request.status != RequestStatus.WAITING_FOR_STREAMING_REQ:
                return {'ready': False, 'reason': 'prior_execution'}
            if session.restore_inflight:
                return {'ready': False, 'reason': 'restore_in_flight'}
            if session.host_pins:
                # At the tick a missing dependency is urgent even if the next
                # periodic plan has already been installed. Never duplicate
                # an in-flight restore or treat its allocation as readiness.
                self.restore(session)
                return {'ready': False, 'reason': 'restore_required'}
            if request is not None and getattr(request, '_omni_kv_evicted', False):
                complete = request.num_computed_tokens // self.block_size
                for block_hash in request.block_hashes[:complete]:
                    if not self.gpu.get_cached_block(block_hash, [self.native.fa_gidx]):
                        return {'ready': False, 'reason': 'gpu_coverage_gap'}
            session.pending_work = work_id
            return {'ready': True}


def apply():
    from vllm.v1.engine.core import EngineCore
    from vllm.v1.core.sched.scheduler import Scheduler
    from vllm.v1.simple_kv_offload.worker import SimpleCPUOffloadWorker
    from vllm.v1.simple_kv_offload.manager import SimpleCPUOffloadScheduler
    from vllm.v1.request import RequestStatus
    from vllm.v1.executor.uniproc_executor import UniProcExecutor
    from vllm.distributed.kv_transfer.kv_connector.v1.simple_cpu_offload_connector import SimpleCPUOffloadConnector

    original_register = SimpleCPUOffloadWorker.register_kv_caches
    def register(self, *args, **kwargs):
        global _worker
        result = original_register(self, *args, **kwargs)
        _worker = self
        return result
    SimpleCPUOffloadWorker.register_kv_caches = register

    original_init = EngineCore.__init__
    def initialize(self, *args, **kwargs):
        global _adapter
        original_init(self, *args, **kwargs)
        scheduler = self.scheduler
        if (type(self.model_executor) is not UniProcExecutor or self.async_scheduling
                or len(scheduler.kv_cache_config.kv_cache_groups) != 1 or _worker is None
                or scheduler.needs_kv_cache_zeroing or scheduler.num_spec_tokens):
            raise RuntimeError("Session Manager requires synchronous UniProc, one KV group, "
                               "no speculative decoding and no worker-side KV zeroing")
        if _adapter is not None:
            raise RuntimeError("only one Session Manager engine is supported per process")
        _adapter = VllmKVMemoryManager(scheduler, _worker)
        scheduler._omni_lock = _lock
        self.session_manager = _adapter.manager
    EngineCore.__init__ = initialize

    # Lock metadata mutations, never the GPU execution or future.result().
    def guarded(method):
        @functools.wraps(method)
        def call(self, *args, **kwargs):
            with _lock:
                if _adapter:
                    _adapter.manager.check_health()
                return method(self, *args, **kwargs)
        return call
    for name in ("schedule", "update_from_output", "add_request", "finish_requests"):
        setattr(Scheduler, name, guarded(getattr(Scheduler, name)))

    original_stopped = Scheduler._handle_stopped_request
    def stopped(self, request):
        result = original_stopped(self, request)
        if _adapter and not request.request_id.startswith(omni_evict.WARMUP_REQ_PREFIX):
            if result:
                _adapter.manager.cancel(external_id(request.request_id))
            elif request.status == RequestStatus.WAITING_FOR_STREAMING_REQ:
                _adapter.manager.on_idle(external_id(request.request_id))
        return result
    Scheduler._handle_stopped_request = stopped

    original_update = Scheduler._update_request_as_session
    def update(self, session, update):
        if _adapter:
            _adapter.manager.on_resume(external_id(session.request_id))
        return original_update(self, session, update)
    Scheduler._update_request_as_session = update

    original_finish = Scheduler.finish_requests
    def finish(self, request_ids, *args, **kwargs):
        with _lock:
            ids = list(self.requests) if request_ids is None else (
                [request_ids] if isinstance(request_ids, str) else list(request_ids))
            if _adapter:
                for request_id in ids:
                    _adapter.manager.cancel(external_id(request_id))
            return original_finish(self, ids, *args, **kwargs)
    Scheduler.finish_requests = finish

    original_meta = SimpleCPUOffloadScheduler.build_connector_meta
    def metadata(self, output):
        meta = original_meta(self, output)
        return _adapter.dispatch(meta) if _adapter else meta
    SimpleCPUOffloadScheduler.build_connector_meta = metadata

    def session_plan(self, request_id, period_s, next_tick_epoch, restore_lead_s,
                     retained_prefix_blocks, eviction_ranges=None, max_evict_blocks=None):
        group = None
        if request_id in _adapter.closed_sessions:
            raise ValueError('cannot install a plan for a closed session')
        if _adapter.planner is not None:
            assigned = _adapter.planner.plans.get(request_id)
            if assigned is None:
                raise ValueError('input has no admission plan')
            # Gateway cannot override the planner's eviction budget or timing.
            restore_lead_s = assigned.restore_lead_s
            retained_prefix_blocks = assigned.retained_prefix_blocks
            max_evict_blocks = assigned.max_evict_blocks
            group = assigned.slot
            phase = assigned.first_tick
            cycles = (float(next_tick_epoch) - phase) / assigned.period_s
            if abs(cycles - round(cycles)) > 1e-5 or float(period_s) != assigned.period_s:
                raise ValueError('input cadence disagrees with admission phase')
        plan = SessionPlan(float(period_s), time.monotonic() + float(next_tick_epoch) - time.time(),
                           float(restore_lead_s), int(retained_prefix_blocks),
                           tuple(tuple(map(int, pair)) for pair in (eviction_ranges or ())),
                           max_evict_blocks, group)
        self.session_manager.set_plan(request_id, plan)
        return {"planned": True}
    EngineCore.session_plan = session_plan

    def session_admit(self, request_id, period_s, slots, epoch):
        return _adapter.admit(request_id, float(period_s), int(slots), float(epoch))
    EngineCore.session_admit = session_admit

    def session_release(self, request_id):
        with _lock:
            ids = [rid for rid in self.scheduler.requests if external_id(rid) == request_id]
            self.abort_requests(ids)
            return _adapter.release_session(request_id)
    EngineCore.session_release = session_release

    def session_ready(self, request_id, work_id):
        return _adapter.prepare_input(request_id, work_id)
    EngineCore.session_ready = session_ready

    def session_drained(self, request_id):
        with _lock:
            session = _adapter.manager.sessions.get(request_id)
            request = omni_evict._resolve(self.scheduler, request_id)
            return {'drained': bool(session is not None and session.pending_work is None
                                    and request is not None
                                    and request.status == RequestStatus.WAITING_FOR_STREAMING_REQ)}
    EngineCore.session_drained = session_drained

    original_allocated = SimpleCPUOffloadConnector.update_state_after_alloc
    def allocated(self, request, *args, **kwargs):
        result = original_allocated(self, request, *args, **kwargs)
        if _adapter:
            with _lock:
                session = _adapter.manager.sessions.get(external_id(request.request_id))
                if session is not None and session.pending_work is not None:
                    # Backend has acquired its execution references. Transfer
                    # the reservation only now, not at input ingestion.
                    _adapter.release_idle_pins(session)
        return result
    SimpleCPUOffloadConnector.update_state_after_alloc = allocated

    original_finalize = EngineCore.initial_context_finalize
    def finalize(self):
        with _lock:
            result = original_finalize(self)
            _adapter.hold = False
            return result
    EngineCore.initial_context_finalize = finalize

    def refuse_legacy_eviction(self, *args, **kwargs):
        return {"kv_evicted": False, "reason": "eviction is owned by Session Manager plans"}
    EngineCore.evict_tail_blocks = refuse_legacy_eviction

    original_shutdown = EngineCore.shutdown
    def shutdown(self):
        try:
            if manager := getattr(self, "session_manager", None):
                self.session_manager = None
                manager.close()
        finally:
            original_shutdown(self)
    EngineCore.shutdown = shutdown
