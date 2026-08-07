"""Pinned-host H2D calibration used by E2 and E3."""

from __future__ import annotations

import statistics
import time


def measure_h2d(*, gpu: int, size_bytes: int, samples: int, warmup: int = 3) -> dict:
    if size_bytes <= 0 or samples <= 0:
        raise ValueError("size_bytes and samples must be positive")
    import torch

    torch.cuda.set_device(gpu)
    host = torch.empty(size_bytes, dtype=torch.uint8, pin_memory=True)
    device = torch.empty(size_bytes, dtype=torch.uint8, device=f"cuda:{gpu}")
    stream = torch.cuda.Stream(device=gpu)
    for _ in range(warmup):
        with torch.cuda.stream(stream):
            device.copy_(host, non_blocking=True)
    stream.synchronize()

    elapsed_ms: list[float] = []
    wall_ms: list[float] = []
    for _ in range(samples):
        start = torch.cuda.Event(enable_timing=True)
        finish = torch.cuda.Event(enable_timing=True)
        wall_start = time.perf_counter()
        with torch.cuda.stream(stream):
            start.record(stream)
            device.copy_(host, non_blocking=True)
            finish.record(stream)
        finish.synchronize()
        elapsed_ms.append(start.elapsed_time(finish))
        wall_ms.append((time.perf_counter() - wall_start) * 1000)

    return {
        "gpu": gpu,
        "gpu_name": torch.cuda.get_device_name(gpu),
        "size_bytes": size_bytes,
        "samples_ms": elapsed_ms,
        "wall_samples_ms": wall_ms,
        "bandwidth_gbps": [size_bytes / (duration / 1000) / 1e9 for duration in elapsed_ms],
        "median_ms": statistics.median(elapsed_ms),
        "median_gbps": statistics.median(
            size_bytes / (duration / 1000) / 1e9 for duration in elapsed_ms
        ),
    }
