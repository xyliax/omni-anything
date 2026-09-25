"""Intrusive physical KV copy check; never a performance observation."""
from __future__ import annotations


def verify_copy(worker, direction, sources, targets):
    import torch
    if direction not in ('H2D', 'D2H'):
        raise ValueError('unknown copy direction')
    gpu_ids, host_ids = (targets, sources) if direction == 'H2D' else (sources, targets)
    gpu_ids = torch.tensor(gpu_ids, dtype=torch.int64, device=worker.device)
    host_ids = torch.tensor(host_ids, dtype=torch.int64)
    # Cache dictionaries contain canonical block-major raw storage views.
    actual = torch.cat([cache.index_select(0, gpu_ids).reshape(-1).view(torch.uint8)
                        for cache in worker.gpu_kv_caches.values()]).cpu()
    expected = torch.cat([worker.cpu_kv_caches[key].index_select(0, host_ids).reshape(-1).view(torch.uint8)
                          for key in worker.gpu_kv_caches])
    if not torch.equal(actual, expected):
        raise RuntimeError(f'physical KV bytes differ after {direction}: {len(sources)} blocks')
    return actual.numel()
