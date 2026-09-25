"""Submission and completion of KV copies without scheduler-step polling."""
from __future__ import annotations

import itertools
import os
import queue
import threading
import time
from collections import Counter
from contextlib import nullcontext


class CopyService:
    def __init__(self, backend, observer, *, poll_s=0.001):
        self.backend = backend
        self.observer = observer
        self.poll_s = poll_s
        self.queue = queue.Queue()
        self.sequence = itertools.count(1)
        self.error = None
        self.closing = False
        self.pending_lock = threading.Lock()
        self.pending = Counter()
        self.pending_directions = Counter()
        self.thread = threading.Thread(target=self._run, name="kv-copy-service", daemon=True)
        self.thread.start()

    def submit(self, direction, sources, targets, requests, on_done):
        self.check_health()
        if self.closing:
            raise RuntimeError("copy service is closing")
        if not sources or len(sources) != len(targets):
            raise ValueError("copy requires nonempty matching source and destination lists")
        transfer_id = next(self.sequence)
        job = (transfer_id, direction, tuple(sources), tuple(targets), tuple(requests), on_done)
        with self.pending_lock:
            self.pending.update(job[4])
            self.pending_directions[direction] += 1
        self.observer("queued", transfer_id=transfer_id, direction=direction,
                      requests=list(requests), blocks=len(sources),
                      source_blocks=list(sources), target_blocks=list(targets))
        self.queue.put(job)
        return transfer_id

    def pending_requests(self):
        """Includes queued copies and callbacks that have not released pins."""
        with self.pending_lock:
            return set(self.pending)

    def pending_copies(self, direction):
        with self.pending_lock:
            return self.pending_directions[direction]

    def check_health(self):
        if self.error is not None:
            raise RuntimeError("KV copy service failed") from self.error

    def _run(self):
        inflight = []
        try:
            self.backend.initialize()
            while not self.closing or not self.queue.empty() or inflight:
                try:
                    job = self.queue.get(timeout=self.poll_s)
                except queue.Empty:
                    job = None
                if job:
                    transfer_id, direction, sources, targets, requests, done = job
                    start = time.time()
                    thread_start = time.thread_time()
                    handle, nbytes = self.backend.launch(direction, sources, targets, transfer_id, requests)
                    self.observer("submitted", transfer_id=transfer_id, direction=direction,
                                  requests=list(requests), bytes=nbytes, submit_start=start,
                                  submit_end=time.time(), python_tid=threading.get_ident() & 0xffffffff,
                                  native_tid=threading.get_native_id(),
                                  submit_thread_ms=(time.thread_time() - thread_start) * 1000,
                                  **getattr(self.backend, 'last_submit', {}))
                    inflight.append((job, handle))
                pending = []
                for job, handle in inflight:
                    if not self.backend.finished(handle):
                        pending.append((job, handle))
                        continue
                    self.observer("device_complete_observed", transfer_id=job[0], direction=job[1],
                                  requests=list(job[4]), stream_interval_ms=self.backend.elapsed_ms(handle))
                    if getattr(self.backend, 'verify_copies', False) is True:
                        checked = self.backend.verify(job[1], job[2], job[3])
                        self.observer("integrity_checked", transfer_id=job[0], direction=job[1],
                                      requests=list(job[4]), checked_bytes=checked)
                    job[5]()
                    self.observer("published", transfer_id=job[0], direction=job[1], requests=list(job[4]))
                    with self.pending_lock:
                        self.pending.subtract(job[4])
                        self.pending += Counter()  # discard zero counts
                        self.pending_directions[job[1]] -= 1
                inflight = pending
        except Exception as exc:
            # An uncertain DMA must retain its pins until the engine exits.
            self.error = exc
            self.observer("error", error=repr(exc))

    def close(self, timeout=30):
        self.closing = True
        self.thread.join(timeout=timeout)
        self.check_health()
        if self.thread.is_alive():
            raise RuntimeError("KV copies did not drain before shutdown")


class CudaCopyBackend:
    def __init__(self, worker):
        self.worker = worker
        self.native_control = os.environ.get('OMNI_COPY_SUBMISSION') == 'native'
        self.verify_copies = os.environ.get('OMNI_VERIFY_COPIES') == '1'

    def verify(self, direction, sources, targets):
        # Diagnostic only: synchronize and compare every byte while both
        # source and destination references are still pinned, before publish.
        from infra.trace.collectors.kv_integrity import verify_copy
        return verify_copy(self.worker, direction, sources, targets)

    def initialize(self):
        import torch
        from vllm.v1.simple_kv_offload.cuda_mem_ops import build_params
        torch.cuda.set_device(self.worker.device)
        from copy_descriptors import DriverEvents
        self.events = DriverEvents()
        self.streams = {direction: torch.cuda.Stream() for direction in ("H2D", "D2H")}
        self.params = {
            "H2D": build_params(self.worker.cpu_kv_caches, self.worker.gpu_kv_caches, self.streams["H2D"]),
            "D2H": build_params(self.worker.gpu_kv_caches, self.worker.cpu_kv_caches, self.streams["D2H"]),
        }
        # CUDA STREAM ordering for pinned, long-lived buffers. Existing source
        # readiness and lifetime protection remain the memory manager's job.
        for params in self.params.values():
            params.attrs.srcAccessOrder = 1

    def launch(self, direction, sources, targets, transfer_id, requests):
        if self.native_control:
            return self._native_launch(direction, sources, targets, transfer_id, requests)
        from copy_descriptors import copy_blocks
        from infra.trace.collectors import gpu_activity
        stream = self.streams[direction]
        start, end = self.events.create(), self.events.create()
        label = f"pilarius.copy id={transfer_id} {direction} req={','.join(requests)}"
        context = nullcontext()
        if gpu_activity._active:
            import torch
            context = torch.autograd.profiler.record_function(label)
        with context:
            self.events.record(start, stream.cuda_stream)
            self.last_submit = copy_blocks(sources, targets, self.params[direction])
            self.events.record(end, stream.cuda_stream)
        return (start, end), len(sources) * sum(int(n) for n in self.params[direction].bpb)

    def _native_launch(self, direction, sources, targets, transfer_id, requests):
        """Frozen pre-fix submission path, only for controlled diagnostics."""
        import torch
        from vllm.v1.simple_kv_offload.cuda_mem_ops import copy_blocks
        stream = self.streams[direction]
        start, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        with torch.autograd.profiler.record_function(f"pilarius.copy id={transfer_id} {direction} req={','.join(requests)}"), torch.cuda.stream(stream):
            start.record(stream)
            copy_blocks(list(sources), list(targets), self.params[direction])
            end.record(stream)
        self.last_submit = dict(copy_implementation='native',
            copy_descriptors=len(sources) * self.params[direction].num_layers)
        return (start, end), len(sources) * sum(int(n) for n in self.params[direction].bpb)

    def finished(self, handle):
        if self.native_control:
            return handle[1].query()
        return self.events.finished(handle[1])

    def elapsed_ms(self, handle):
        # A stream interval, including submission gaps/contention; CUPTI
        # activities in gpu_activity.json give actual individual DMA spans.
        return handle[0].elapsed_time(handle[1]) if self.native_control else self.events.elapsed_and_destroy(handle)
