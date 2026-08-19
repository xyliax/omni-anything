"""Baseline configuration, private to this experiment.

``experiments/shared`` holds the fixed facts of the
stack as plain constants; this module holds the per-run knobs and engine
constants. ``mode`` selects system behavior; ``trace`` is an independent
observation switch and must never be represented as another implementation
mode.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from experiments.shared import model, platform, workload


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ModeSpec:
    """The worker selected by one behaviorally distinct implementation."""

    worker: str
    parallel_ingest: bool = False


MODES: Mapping[str, ModeSpec] = {
    "vanilla": ModeSpec("third_party/metronome/worker/stream_server.py"),
    "paringest": ModeSpec(
        "engines/baseline/worker/stream_server.py",
        parallel_ingest=True,
    ),
}


@dataclass(frozen=True)
class BaselineConfig:
    """Complete, validated configuration for one fresh-worker baseline run."""

    experiment_name = "baseline"  # class attr, not a field: runner provenance
    root = ROOT

    # engine constants — change here, not on the command line
    max_model_len = 32768  # >= 32768 so long runs hit the capacity wall, not a MML stall
    max_num_seqs = 16
    gpu_memory_utilization = 0.9
    wait_budget_s = 1.6
    ingest_workers = 8
    startup_timeout_s = 360
    kv_log_period_s = 0.2   # kv.log sampling; 10 samples/tick (same rationale
                            # as platform.GPU_SAMPLE_PERIOD_S) — identical to
                            # conveyor's, the two arms must observe on one grid

    mode: str = "paringest"
    trace: bool = False
    label: str | None = None
    sessions: int = workload.SESSIONS
    duration_s: int = workload.DURATION_S
    seed_tokens: int = 0
    gpu: int = platform.DEFAULT_GPU_INDEX

    def __post_init__(self) -> None:
        if self.label is None:
            object.__setattr__(self, "label", f"{self.mode}-n{self.sessions}")
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
        return self.root / "results" / "baseline"

    @property
    def mode_spec(self) -> ModeSpec:
        return MODES[self.mode]

    @property
    def worker_path(self) -> Path:
        return self.root / self.mode_spec.worker

    @property
    def metronome_root(self) -> Path:
        return self.root / "third_party" / "metronome"

    @property
    def gateway_path(self) -> Path:
        return self.root / ".build" / "metronome-gateway"

    @property
    def per_request_logs(self) -> bool:
        """PERREQ/PERITER observation: traced runs on the instrumented worker."""
        return self.trace and self.mode_spec.parallel_ingest

    def validate(self) -> None:
        if self.mode not in MODES:
            raise ValueError(f"unknown baseline mode: {self.mode} (known: {', '.join(sorted(MODES))})")
        if self.seed_tokens and not self.mode_spec.parallel_ingest:
            raise ValueError("seed-tokens requires paringest mode")
        if self.sessions <= 0 or self.sessions % self.client_shards:
            raise ValueError("sessions must be positive and evenly divisible by client shards")
        if self.duration_s <= 0:
            raise ValueError("duration must be positive")

    def required_artifact_names(self) -> tuple[str, ...]:
        """The artifact set the runner refuses to finalize without."""
        names = ["client.json", "client.txt", "gateway.log", "gpu.csv", "kv.log", "worker.log"]
        if self.trace:
            names.extend(("scheduler.log", "residency.log"))
        if self.per_request_logs:
            names.extend(("per_request.log", "per_iteration.log"))
        return tuple(sorted(names))

    def manifest_config(self) -> dict[str, Any]:
        """Return stable experiment parameters for ``manifest.json``."""
        return {
            "mode": self.mode,
            "worker": self.mode_spec.worker,
            "label": self.label,
            "engine": {
                "max_model_len": self.max_model_len,
                "max_num_seqs": self.max_num_seqs,
                "gpu_memory_utilization": self.gpu_memory_utilization,
                "wait_budget_s": self.wait_budget_s,
                "seed_tokens": self.seed_tokens,
                # seed runs inject the frozen-max_tokens engine fix (runner)
                "session_max_tokens_fix": bool(self.seed_tokens),
                "ingest_workers": self.ingest_workers,
                "startup_timeout_s": self.startup_timeout_s,
            },
            "client": {"client_shards": self.client_shards},
            "model": model.manifest(),
            "platform": {**platform.manifest(), "gpu_index": self.gpu},
            "workload": workload.manifest(self.sessions, self.duration_s),
            "observations": {
                "trace": self.trace,
                "scheduler": self.trace,
                "residency": self.trace,
                "per_request": self.per_request_logs,
                "per_iteration": self.per_request_logs,
                "kv_log_period_s": self.kv_log_period_s,
            },
        }
