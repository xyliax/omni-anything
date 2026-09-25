"""Per-input service completion, independent of RPC duration or GPU profiling."""
from __future__ import annotations

import json
import os
import re
import time

_fd = None


def emit(event, session, frame, **fields):
    global _fd
    path = os.environ.get('OMNI_SERVICE_EVENTS')
    if not path:
        return
    match = re.match(r'^s(\d+)e', str(session))
    sid = int(match[1]) if match else int(session)
    if sid >= 10**9:
        return
    if _fd is None:
        # Worker and EngineCore share an append-only event stream. Each small
        # record is one write; no userspace buffering across processes.
        _fd = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o644)
    row = dict(schema_version=1, event=event, session=sid, epoch=1,
               frame=frame, time_ns=time.time_ns(), pid=os.getpid(), **fields)
    os.write(_fd, (json.dumps(row) + '\n').encode())


def apply():
    from vllm.v1.core.sched.scheduler import Scheduler
    original = Scheduler._handle_stopped_request
    counts = {}
    def stopped(self, request):
        if request.resumable:
            rid = request.request_id
            seq = counts.get(rid, -int(bool(os.environ.get('OMNI_SERVICE_PRELOAD')))) + 1
            counts[rid] = seq
            emit('compute_complete', rid, seq, tokens=len(request.output_token_ids),
                 finish_reason=str(request.get_finished_reason()),
                 timing_scope='engine_observed_model_completion')
        return original(self, request)
    Scheduler._handle_stopped_request = stopped
