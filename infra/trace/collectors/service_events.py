"""Per-input service completion, independent of RPC duration or GPU profiling."""
from __future__ import annotations

import json
import hashlib
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
    from vllm.v1.core.block_pool import BlockPool, BlockHashToBlockMap
    from vllm.v1.engine.core import EngineCore
    original_init = Scheduler.__init__
    def initialize(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        pool = self.kv_cache_manager.block_pool
        pool._service_gpu_pool = True
        groups = self.kv_cache_config.kv_cache_groups
        if len(groups) != 1:
            raise ValueError('physical service observation currently requires one KV group')
        emit('gpu_allocation', 0, 0, allocated_blocks=len(pool.blocks) - pool.get_num_free_blocks(),
             capacity_blocks=len(pool.blocks), operation='initialize',
             block_size_tokens=groups[0].kv_cache_spec.block_size,
             bytes_per_block=groups[0].kv_cache_spec.page_size_bytes * len(groups[0].layer_names))
    Scheduler.__init__ = initialize
    # These hooks observe real physical allocation after mutation, including
    # complete H2D destinations and pins. Free cached content is reclaimable,
    # so it is not counted as allocated. No sampling can miss a short peak.
    for operation in ('get_new_blocks', 'touch', 'free_blocks'):
        original_op = getattr(BlockPool, operation)
        def observed(self, *args, _op=original_op, _name=operation, **kwargs):
            result = _op(self, *args, **kwargs)
            if getattr(self, '_service_gpu_pool', False):
                emit('gpu_allocation', 0, 0, allocated_blocks=len(self.blocks) - self.get_num_free_blocks(),
                     capacity_blocks=len(self.blocks), operation=_name)
            return result
        setattr(BlockPool, operation, observed)
    original_core_init = EngineCore.__init__
    def core_initialize(self, *args, **kwargs):
        original_core_init(self, *args, **kwargs)
        if hasattr(self, 'session_manager'):
            cpu = self.session_manager.adapter.cpu
            cpu.cached_block_hash_to_block._service_host_blocks = set()
            emit('host_backing', 0, 0, valid_blocks=0, capacity_blocks=len(cpu.blocks))
    EngineCore.__init__ = core_initialize
    for operation in ('insert', 'pop'):
        original_cache_op = getattr(BlockHashToBlockMap, operation)
        def cache_observed(self, *args, _op=original_cache_op, _name=operation, **kwargs):
            result = _op(self, *args, **kwargs)
            blocks = getattr(self, '_service_host_blocks', None)
            if blocks is not None:
                if _name == 'insert':
                    blocks.add(args[1].block_id)
                elif result is not None:
                    blocks.discard(result.block_id)
                emit('host_backing', 0, 0, valid_blocks=len(blocks))
            return result
        setattr(BlockHashToBlockMap, operation, cache_observed)
    original = Scheduler._handle_stopped_request
    counts = {}
    def stopped(self, request):
        if request.resumable:
            rid = request.request_id
            seq = counts.get(rid, -int(bool(os.environ.get('OMNI_SERVICE_PRELOAD')))) + 1
            counts[rid] = seq
            emit('compute_complete', rid, seq, tokens=len(request.output_token_ids),
                 output_token_sha256=hashlib.sha256(json.dumps(list(request.output_token_ids)).encode()).hexdigest(),
                 context_tokens=request.num_tokens,
                 computed_tokens=request.num_computed_tokens,
                 finish_reason=str(request.get_finished_reason()),
                 timing_scope='engine_observed_model_completion')
        return original(self, request)
    Scheduler._handle_stopped_request = stopped
