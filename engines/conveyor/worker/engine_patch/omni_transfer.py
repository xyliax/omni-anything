"""Anonymous KV load transport: move content blocks CPU->GPU outside any request.

The TRANSPORT layer of the materialization pattern (semantic layer:
``omni_reload``; claim layer: vLLM's existing resume hash-match, untouched).
Jobs enqueued here ride the stock ``SimpleCPUOffload`` load-event machinery —
the same low-priority CUDA stream, event accounting, and preemption flush as
demand reloads — so this module contains NO copy code of its own. What it
owns is block lifecycle bookkeeping:

- at enqueue the GPU destination blocks are already allocated (ref_cnt=1,
  hash stamped) and the CPU source blocks pinned (``touch``) by the caller;
- ``build_connector_meta`` (wrapped) splices pending jobs into the step's
  load event under a SYNTHETIC id (``omni-prefetch-<n>``) — request ids only
  matter for completion reporting, the worker executes copies by event;
- ``Scheduler._update_from_kv_xfer_finished`` (wrapped) strips synthetic ids
  from ``finished_recving`` BEFORE the original runs (it asserts every id is
  a live request — a synthetic id would crash it), then completes the job:
  register each block's hash into the GPU prefix cache (contents are on GPU
  only now — registering earlier would let a hash match claim garbage), then
  ``free_blocks`` both sides — the GPU blocks become cached-free (claimable
  by resume, LRU-evictable under pressure: the graceful-degradation property
  correctness relies on), the CPU pins are released.

Blocks belong to the cache, never to a request: a cancelled session, a
chunk overtaking the copy, or pool pressure all degrade to "a cache entry
nobody claims", not to request-state corruption.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

SYNTHETIC_PREFIX = "omni-prefetch-"

_pending: list["_Job"] = []
_inflight: dict[str, "_Job"] = {}
_sequence = [0]


@dataclass
class _Job:
    gpu_blocks: list[Any]   # allocated (ref_cnt=1), hash already stamped
    cpu_blocks: list[Any]   # pinned via touch by the caller
    gpu_pool: Any
    cpu_pool: Any
    on_done: Callable[[], None] | None
    event: int = -1
    synthetic_id: str = ""


def enqueue(gpu_blocks, cpu_blocks, gpu_pool, cpu_pool, on_done=None) -> None:
    """Queue one anonymous CPU->GPU materialization; it joins the next
    engine step's load event (steps flow every ~20ms at the operating
    point, so the copy launches within one step)."""
    _pending.append(_Job(gpu_blocks, cpu_blocks, gpu_pool, cpu_pool, on_done))


def _complete(scheduler, job: "_Job") -> None:
    for block in job.gpu_blocks:
        job.gpu_pool.cached_block_hash_to_block.insert(block.block_hash, block)
    job.gpu_pool.free_blocks(job.gpu_blocks)
    job.cpu_pool.free_blocks(job.cpu_blocks)
    # drop the synthetic entry from the manager's event map (we put it there)
    try:
        manager = scheduler.connector.scheduler_manager
        reqs = manager._load_event_to_reqs.get(job.event)
        if reqs is not None:
            if job.synthetic_id in reqs:
                reqs.remove(job.synthetic_id)
            if not reqs:
                manager._load_event_to_reqs.pop(job.event, None)
    except Exception:
        pass
    if job.on_done is not None:
        job.on_done()


def apply() -> None:
    """Install the splice and completion wrappers (loader-gated; importing
    this module patches nothing)."""
    from vllm.v1.core.sched.scheduler import Scheduler
    from vllm.v1.simple_kv_offload.manager import SimpleCPUOffloadScheduler

    _original_meta = SimpleCPUOffloadScheduler.build_connector_meta

    def build_connector_meta(self, scheduler_output):
        meta = _original_meta(self, scheduler_output)
        if _pending:
            if meta.load_event < 0:
                # mint an event from the manager's own counter so worker-side
                # high-water-mark accounting stays monotonic
                meta.load_event = self._load_event_counter
                self._load_event_counter += 1
            # meta.load_event_to_reqs IS the manager's map (passed by
            # reference), so this registration is what completion reporting
            # reads — and what _complete() cleans up.
            reqs = meta.load_event_to_reqs.setdefault(meta.load_event, [])
            while _pending:
                job = _pending.pop(0)
                _sequence[0] += 1
                job.synthetic_id = f"{SYNTHETIC_PREFIX}{_sequence[0]}"
                job.event = meta.load_event
                meta.load_gpu_blocks.extend(b.block_id for b in job.gpu_blocks)
                meta.load_cpu_blocks.extend(b.block_id for b in job.cpu_blocks)
                reqs.append(job.synthetic_id)
                _inflight[job.synthetic_id] = job
        return meta

    SimpleCPUOffloadScheduler.build_connector_meta = build_connector_meta

    _original_finished = Scheduler._update_from_kv_xfer_finished

    def _update_from_kv_xfer_finished(self, kv_connector_output):
        received = kv_connector_output.finished_recving
        if received:
            synthetic = {r for r in received if r.startswith(SYNTHETIC_PREFIX)}
            if synthetic:
                kv_connector_output.finished_recving = {
                    r for r in received if r not in synthetic
                }
                for synthetic_id in synthetic:
                    job = _inflight.pop(synthetic_id, None)
                    if job is not None:
                        _complete(self, job)
        return _original_finished(self, kv_connector_output)

    Scheduler._update_from_kv_xfer_finished = _update_from_kv_xfer_finished
