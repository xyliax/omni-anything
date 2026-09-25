"""Fully resident control using the same input, cadence and drain protocol.

No offload connector, host KV pool, eviction, restoration or backing traffic.
Admission limits concurrent lifetimes; capacity is determined by the sweep,
not granted by a predictive offload model.
"""
import os


def apply():
    from vllm.v1.engine.core import EngineCore
    from vllm.v1.core.sched.scheduler import Scheduler
    from vllm.v1.request import RequestStatus
    from omni_state import external_id

    original_update = Scheduler._update_request_as_session
    def update(self, session, item):
        result = original_update(self, session, item)
        if item is not None and item.sampling_params is not None:
            session.max_tokens = item.sampling_params.max_tokens
        return result
    Scheduler._update_request_as_session = update

    def find(self, rid):
        return next((r for key, r in self.scheduler.requests.items() if external_id(key) == rid), None)

    def admit(self, rid, period, slots, epoch, source_start=None):
        if not hasattr(self, '_resident_slots'):
            self._resident_slots, self._resident_pending, self._resident_closed = {}, {}, set()
        if rid in self._resident_closed:
            raise ValueError('closed session identity')
        if rid not in self._resident_slots:
            if len(self._resident_slots) >= int(os.environ['OMNI_RESIDENT_LIMIT']):
                return dict(admitted=False, reason='session_limit')
            self._resident_slots[rid] = min(range(slots), key=lambda s: (list(self._resident_slots.values()).count(s), s))
        return dict(admitted=True, plan=dict(slot=self._resident_slots[rid]))

    def plan(self, rid, period_s, next_tick_epoch, restore_lead_s, retained_prefix_blocks):
        return dict(planned=True)

    def ready(self, rid, work_id):
        previous = self._resident_pending.get(rid)
        if previous == work_id:
            return dict(ready=True)
        request = find(self, rid)
        if previous is not None or (request is not None and request.status != RequestStatus.WAITING_FOR_STREAMING_REQ):
            return dict(ready=False, reason='prior_execution')
        self._resident_pending[rid] = work_id
        return dict(ready=True)

    original_stopped = Scheduler._handle_stopped_request
    # EngineCore utilities and synchronous scheduler run on the same thread.
    original_init = EngineCore.__init__
    def initialize(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self._resident_slots, self._resident_pending, self._resident_closed = {}, {}, set()
        self.scheduler._resident_pending = self._resident_pending
    EngineCore.__init__ = initialize
    def stopped(self, request):
        result = original_stopped(self, request)
        if hasattr(self, '_resident_pending'):
            self._resident_pending.pop(external_id(request.request_id), None)
        return result
    Scheduler._handle_stopped_request = stopped

    def drained(self, rid):
        request = find(self, rid)
        return dict(drained=rid not in self._resident_pending and request is not None
                    and request.status == RequestStatus.WAITING_FOR_STREAMING_REQ)

    def release(self, rid):
        self._resident_closed.add(rid)
        self.abort_requests([key for key in self.scheduler.requests if external_id(key) == rid])
        if find(self, rid) is not None:
            return dict(released=False)
        self._resident_slots.pop(rid, None)
        self._resident_pending.pop(rid, None)
        return dict(released=True)

    EngineCore.session_admit = admit
    EngineCore.session_plan = plan
    EngineCore.session_ready = ready
    EngineCore.session_drained = drained
    EngineCore.session_release = release
