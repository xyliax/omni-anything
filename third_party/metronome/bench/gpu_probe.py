"""GPU-politeness utilities for a *shared* GPU.

This server's GPU is shared with other tenants. Every measurement in this project
runs through :func:`wait_for_window`, which blocks until the GPU has enough free
memory and low-enough utilisation that our short measurement burst will not
disturb a neighbour's job (and will not be disturbed *by* one — which would
corrupt timing). It also caps how long we are willing to wait.

We deliberately query ``nvidia-smi`` (not torch) so the check reflects *all*
processes, including ones in other CUDA contexts.
"""
from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass


@dataclass
class GpuState:
    index: int
    mem_used_mib: int
    mem_free_mib: int
    mem_total_mib: int
    util_pct: int

    @property
    def mem_free_gib(self) -> float:
        return self.mem_free_mib / 1024.0


def query(index: int = 0) -> GpuState:
    out = subprocess.check_output(
        [
            "nvidia-smi",
            f"--id={index}",
            "--query-gpu=memory.used,memory.free,memory.total,utilization.gpu",
            "--format=csv,noheader,nounits",
        ],
        text=True,
    ).strip()
    used, free, total, util = (int(x.strip()) for x in out.split(","))
    return GpuState(index, used, free, total, util)


def other_tenant_mem_mib(index: int = 0, our_pid: int | None = None) -> int:
    """Memory (MiB) held by processes other than ours — a proxy for neighbours."""
    import os

    our_pid = our_pid if our_pid is not None else os.getpid()
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                f"--id={index}",
                "--query-compute-apps=pid,used_memory",
                "--format=csv,noheader,nounits",
            ],
            text=True,
        ).strip()
    except subprocess.CalledProcessError:
        return 0
    total = 0
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        pid_s, mem_s = (x.strip() for x in line.split(","))
        try:
            pid, mem = int(pid_s), int(mem_s)
        except ValueError:
            continue
        if pid != our_pid:
            total += mem
    return total


def wait_for_window(
    index: int = 0,
    need_free_gib: float = 8.0,
    max_util_pct: int = 60,
    poll_s: float = 5.0,
    timeout_s: float = 1800.0,
    quiet: bool = False,
) -> GpuState:
    """Block until the GPU is free enough to run a measurement burst.

    Returns the satisfying :class:`GpuState`. Raises TimeoutError if no window
    opens within ``timeout_s``. Both conditions (enough free memory AND
    utilisation below the threshold) must hold simultaneously so we time our
    kernels without contention.
    """
    start = time.time()
    last_log = 0.0
    while True:
        st = query(index)
        ok_mem = st.mem_free_gib >= need_free_gib
        ok_util = st.util_pct <= max_util_pct
        if ok_mem and ok_util:
            if not quiet:
                print(f"[gpu] window open: {st.mem_free_gib:.1f} GiB free, "
                      f"util {st.util_pct}%")
            return st
        elapsed = time.time() - start
        if elapsed > timeout_s:
            raise TimeoutError(
                f"no GPU window in {timeout_s:.0f}s (last: {st.mem_free_gib:.1f} GiB "
                f"free, util {st.util_pct}%)"
            )
        if not quiet and time.time() - last_log > 30:
            print(f"[gpu] waiting for window ({st.mem_free_gib:.1f} GiB free, "
                  f"util {st.util_pct}%, need {need_free_gib} GiB & <={max_util_pct}%)...")
            last_log = time.time()
        time.sleep(poll_s)


if __name__ == "__main__":
    import json

    st = query()
    print(json.dumps(st.__dict__, indent=2))
    print("other-tenant MiB:", other_tenant_mem_mib())
