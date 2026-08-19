"""Conveyor configuration, private to this experiment.

``model.py`` / ``platform.py`` / ``workload.py`` hold the fixed facts of the
stack as plain constants (same facts as baseline's — the two engines must be
compared on an identical stack); this module holds the per-run knobs, the
engine constants, and the conveyor mechanism knobs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import model, platform, workload


ROOT = Path(__file__).resolve().parents[3]

WORKER = "experiments/conveyor/worker/stream_server.py"


@dataclass(frozen=True)
class ConveyorConfig:
    """Complete, validated configuration for one fresh-worker conveyor run."""

    experiment_name = "conveyor"  # class attr, not a field: runner provenance
    root = ROOT

    # engine constants — change here, not on the command line
    max_model_len = 32768  # >= 32768 so long runs hit the capacity wall, not a MML stall
    max_num_seqs = 16
    gpu_memory_utilization = 0.9
    ingest_workers = 8
    startup_timeout_s = 360
    kv_log_period_s = 0.2   # kv.log sampling; 10 samples/tick (same rationale
                            # as platform.GPU_SAMPLE_PERIOD_S) — identical to
                            # baseline's, the two arms must observe on one grid
                            # (coarse 1 Hz hid the park sawtooth between events)

    # conveyor mechanism: phase slots per tick period. The gateway walks a slot
    # wheel (one firing every PERIOD_MS/slots) and round-robins sessions onto it
    # at admission, so engine-side arrivals spread across the period.
    slots = 8

    # conveyor mechanism: bandwidth-for-VRAM KV rotation. The GPU KV pool stays
    # FULL (gpu_memory_utilization, same as baseline); the expansion comes from
    # ACTIVE residency management: vLLM's SimpleCPUOffloadConnector keeps an
    # incremental host mirror of every full block (host_offload_gib pool), the
    # park primitive (below) releases each session's tail the instant its slice
    # stops, and the tail reloads by hash-match on the next chunk. The capacity
    # claim is made by SWEEPING sessions, not by shrinking the pool.
    # kv_pool_gib is an OPTIONAL exact-byte pool cap (None = full pool), a
    # source-level knob for pinning a budget in a smoke test. host_offload_gib
    # is sized so the host pool never LRU-evicts an interior block of a live
    # session (that would truncate the reloadable prefix into a recompute).
    kv_pool_gib: float | None = None
    host_offload_gib: float = 24.0

    # conveyor mechanism: PARK primitive (KV partial release). Fixed mode
    # (park_tail_blocks > 0): after each session's slice destroy that many
    # tail blocks. Quota mode (park_keep_blocks set, overrides fixed mode):
    # destroy everything beyond the resident floor — the idle-time residency
    # stays pinned at K blocks while the context grows, which is what caps
    # pool demand. 1 block = 16 tokens on this stack; the tail reloads from
    # the host mirror on the next chunk. The engine-side primitive is injected
    # by worker/engine_patch/sitecustomize.py; evidence lands in park.log.
    # park_delay_s: push -> park delay, must land after the slice finishes
    # (~sub-second) and before the next push (period, 2s).
    park_tail_blocks: int = 0
    park_keep_blocks: int | None = None
    park_delay_s: float = 1.2   # fixed-tail mode only (source-level knob)

    # scheduling mode control for clean comparisons: park runs force
    # synchronous scheduling for correctness (in-flight speculative steps
    # would race park's block frees); a no-park CONTROL arm must be able to
    # pin the same mode, or park-vs-nopark comparisons change two variables.
    sync_scheduling: bool = False

    # conveyor mechanism: KV PREFETCH (materialization). "push" = at each
    # chunk push the worker asks the engine (omni_prefetch utility) to move
    # the session's parked-but-mirrored blocks back into the GPU prefix
    # cache, so the ~70ms reload copy overlaps the ~270ms FE window instead
    # of serializing after it (FINDINGS H5). Correctness never depends on
    # it: refused / late / LRU-evicted prefetches degrade to the demand
    # reload. prefetch_min_free is the engine-side pool budget gate (refuse
    # when free space would drop below this fraction). Requires park —
    # without park nothing is ever missing from the GPU cache.
    prefetch: str = "off"
    prefetch_min_free: float = 0.10

    @property
    def park_enabled(self) -> bool:
        return bool(self.park_tail_blocks) or self.park_keep_blocks is not None

    trace: bool = False
    label: str | None = None
    sessions: int = workload.SESSIONS
    duration_s: int = workload.DURATION_S
    seed_tokens: int = 0
    gpu: int = platform.DEFAULT_GPU_INDEX

    def __post_init__(self) -> None:
        if self.label is None:
            object.__setattr__(self, "label", f"conveyor-n{self.sessions}")
        self.validate()

    @property
    def worker_python(self) -> Path:
        # Not resolve(): Python uses the invoked venv path (a symlink) to
        # discover pyvenv.cfg and its site-packages.
        return self.root / platform.WORKER_PYTHON

    @property
    def client_shards(self) -> int:
        return 4 if self.sessions >= 32 else 1

    @property
    def output_root(self) -> Path:
        return self.root / "results" / "conveyor"

    @property
    def worker_path(self) -> Path:
        return self.root / WORKER

    @property
    def metronome_root(self) -> Path:
        return self.root / "third_party" / "metronome"

    @property
    def gateway_path(self) -> Path:
        return self.root / ".build" / "conveyor-gateway"

    def validate(self) -> None:
        if self.sessions <= 0 or self.sessions % self.client_shards:
            raise ValueError("sessions must be positive and evenly divisible by client shards")
        if self.duration_s <= 0:
            raise ValueError("duration must be positive")
        if self.host_offload_gib <= 0:
            raise ValueError("host_offload_gib must be positive")
        if self.kv_pool_gib is not None and self.kv_pool_gib <= 0:
            raise ValueError("kv_pool_gib must be positive when set")
        if self.park_tail_blocks < 0:
            raise ValueError("park_tail_blocks must be >= 0")
        if self.park_keep_blocks is not None and self.park_keep_blocks < 1:
            raise ValueError("park_keep_blocks must be >= 1 (block 0 is never evicted)")
        if not 0 < self.park_delay_s < workload.PERIOD_MS / 1000:
            raise ValueError("park_delay_s must land inside one tick period")
        if self.prefetch not in ("off", "push"):
            raise ValueError(f"unknown prefetch mode: {self.prefetch} (known: off, push)")
        if self.prefetch != "off" and not self.park_enabled:
            raise ValueError("prefetch requires park (without park nothing is ever "
                             "missing from the GPU cache; see config comment)")
        if not 0 <= self.prefetch_min_free < 1:
            raise ValueError("prefetch_min_free must be a fraction in [0, 1)")
        if self.seed_tokens and not self.park_enabled:
            # the stop check reads session.max_tokens frozen at construction;
            # only the engine_patch (park runs) refreshes it per chunk. A
            # seeded run without the patch freezes every segment at the seed's
            # max_tokens=1 — cadence stays green while generation dies (the
            # miss=94.8% incident, experiment-log 2026-08-10).
            raise ValueError("seed_tokens requires park (the engine_patch fixes "
                             "the frozen max_tokens trap; see config comment)")

    def required_artifact_names(self) -> tuple[str, ...]:
        """The artifact set the runner refuses to finalize without."""
        names = [
            "client.json", "client.txt", "gateway.log", "gateway_ticks.log",
            "gpu.csv", "kv.log", "worker.log",
        ]
        if self.park_enabled:
            names.append("park.log")
        if self.trace:
            names.extend(
                ("scheduler.log", "residency.log", "per_request.log", "per_iteration.log")
            )
        return tuple(sorted(names))

    def manifest_config(self) -> dict[str, Any]:
        """Return stable experiment parameters for ``manifest.json``."""
        return {
            "worker": WORKER,
            "label": self.label,
            "engine": {
                "max_model_len": self.max_model_len,
                "max_num_seqs": self.max_num_seqs,
                "gpu_memory_utilization": self.gpu_memory_utilization,
                "seed_tokens": self.seed_tokens,
                "ingest_workers": self.ingest_workers,
                "startup_timeout_s": self.startup_timeout_s,
                "slots": self.slots,
                "kv_pool_gib": self.kv_pool_gib,
                "host_offload_gib": self.host_offload_gib,
                "park_tail_blocks": self.park_tail_blocks,
                "park_keep_blocks": self.park_keep_blocks,
                "park_delay_s": self.park_delay_s,
                "sync_scheduling": self.sync_scheduling,
                "prefetch": self.prefetch,
                "prefetch_min_free": self.prefetch_min_free,
            },
            "client": {"client_shards": self.client_shards},
            "model": model.manifest(),
            "platform": {**platform.manifest(), "gpu_index": self.gpu},
            "workload": workload.manifest(self.sessions, self.duration_s),
            "observations": {
                "trace": self.trace,
                "scheduler": self.trace,
                "residency": self.trace,
                "per_request": self.trace,
                "per_iteration": self.trace,
                "kv_log_period_s": self.kv_log_period_s,
            },
        }
