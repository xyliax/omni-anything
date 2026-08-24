"""Conveyor configuration, private to this experiment.

``experiments/shared`` holds the fixed facts of the
stack as plain constants (same facts as baseline's — the two engines must be
compared on an identical stack); this module holds the per-run knobs, the
engine constants, and the conveyor mechanism knobs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from experiments.shared import model, platform, workload


ROOT = Path(__file__).resolve().parents[2]

WORKER = "engines/conveyor/worker/stream_server.py"


@dataclass(frozen=True)
class ConveyorConfig:
    """Complete, validated configuration for one fresh-worker conveyor run."""

    experiment_name = "conveyor"  # class attr, not a field: runner provenance
    root = ROOT

    # engine constants — change here, not on the command line
    max_model_len = 32768  # let long runs reach the GPU KV-capacity limit before the MML limit
    max_num_seqs = 16
    gpu_memory_utilization = 0.9
    ingest_workers = 8
    startup_timeout_s = 360
    kv_log_period_s = 0.2   # kv.log sampling; 10 samples/tick (same rationale
                            # as platform.GPU_SAMPLE_PERIOD_S) — identical to
                            # baseline's, both systems observe on one grid

    # Release-offset scheduling: stable positions within each period.
    slots = 8

    # Host backing for partial KV eviction. The GPU pool uses the normal full
    # budget. Completed blocks are copied incrementally to a host block pool;
    # missing host-backed blocks reload through the existing connector.
    # kv_pool_gib is an OPTIONAL exact-byte pool cap (None = full pool), a
    # source-level knob for pinning a budget in a smoke test. host_offload_gib
    # is sized so the host pool never LRU-evicts an interior block of a live
    # session (that would truncate the reloadable prefix into a recompute).
    kv_pool_gib: float | None = None
    host_offload_gib: float = 24.0

    # Partial KV eviction. Fixed mode
    # (evict_tail_blocks > 0): after each session's slice destroy that many
    # tail blocks. Retained-prefix mode overrides fixed mode and evicts blocks
    # beyond K plus the implementation's uncovered-tail margin. New evidence
    # lands in kv_events.log. eviction_delay_s applies only to fixed-tail mode.
    # (~sub-second) and before the next push (period, 2s).
    evict_tail_blocks: int = 0
    retained_prefix_blocks: int | None = None
    eviction_delay_s: float = 1.2   # fixed-tail mode only (source-level knob)

    # Scheduling-mode control for matched comparisons: eviction runs force
    # synchronous scheduling for correctness (in-flight speculative steps
    # would race block frees); a control configuration can pin the same mode.
    sync_scheduling: bool = False

    # KV prefetch. "push" asks the engine to populate the GPU prefix cache
    # with host-backed blocks when an input is released. Refusal, lateness,
    # or later LRU eviction falls back to on-demand reload/recomputation.
    prefetch: str = "off"
    prefetch_min_free: float = 0.10

    @property
    def kv_eviction_enabled(self) -> bool:
        return bool(self.evict_tail_blocks) or self.retained_prefix_blocks is not None

    trace: bool = False
    label: str | None = None
    sessions: int = workload.SESSIONS
    duration_s: int = workload.DURATION_S
    initial_context_tokens: int = 0
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
        if self.evict_tail_blocks < 0:
            raise ValueError("evict_tail_blocks must be >= 0")
        if self.retained_prefix_blocks is not None and self.retained_prefix_blocks < 1:
            raise ValueError("retained_prefix_blocks must be >= 1 (block 0 is never evicted)")
        if not 0 < self.eviction_delay_s < workload.PERIOD_MS / 1000:
            raise ValueError("eviction_delay_s must land inside one tick period")
        if self.prefetch not in ("off", "push"):
            raise ValueError(f"unknown prefetch mode: {self.prefetch} (known: off, push)")
        if self.prefetch != "off" and not self.kv_eviction_enabled:
            raise ValueError("prefetch requires KV eviction")
        if not 0 <= self.prefetch_min_free < 1:
            raise ValueError("prefetch_min_free must be a fraction in [0, 1)")
        if self.initial_context_tokens and not self.kv_eviction_enabled:
            # the stop check reads session.max_tokens frozen at construction;
            # only the EngineCore patch refreshes it per chunk. A
            # preloaded run without the patch freezes every segment at the initial context's
            # max_tokens=1 while cadence-only monitoring can look healthy.
            raise ValueError(
                "initial_context_tokens requires the KV-eviction patch because it also "
                "contains the streaming max_tokens fix"
            )

    def required_artifact_names(self) -> tuple[str, ...]:
        """The artifact set the runner refuses to finalize without."""
        names = [
            "client.json", "client.txt", "gateway.log", "gateway_ticks.log",
            "gpu.csv", "kv.log", "worker.log",
        ]
        if self.kv_eviction_enabled:
            names.append("kv_events.log")
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
                "initial_context_tokens": self.initial_context_tokens,
                "ingest_workers": self.ingest_workers,
                "startup_timeout_s": self.startup_timeout_s,
                "slots": self.slots,
                "kv_pool_gib": self.kv_pool_gib,
                "host_offload_gib": self.host_offload_gib,
                "evict_tail_blocks": self.evict_tail_blocks,
                "retained_prefix_blocks": self.retained_prefix_blocks,
                "eviction_delay_s": self.eviction_delay_s,
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
