"""E1 implementation modes and validated run configuration.

``mode`` selects system behavior. ``trace`` is an independent observation
switch and must never be represented as another implementation mode.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping


DEFAULT_MODEL, DEFAULT_MODEL_REVISION = (
    Path(__file__).with_name("model.lock").read_text(encoding="utf-8").split()
)


@dataclass(frozen=True)
class ModeSpec:
    """The worker selected by one behaviorally distinct implementation."""

    worker: str
    parallel_ingest: bool = False


MODES: Mapping[str, ModeSpec] = {
    "vanilla": ModeSpec("third_party/metronome/worker/stream_server.py"),
    "paringest": ModeSpec(
        "experiments/e1_capacity_bottleneck/workers/parallel_ingest.py",
        parallel_ingest=True,
    ),
}


@dataclass(frozen=True)
class RunConfig:
    """Complete, validated configuration for one fresh-worker E1 run."""

    root: Path
    mode: str
    trace: bool = False
    gpu: int = 3
    sessions: int = 8
    duration_s: float = 600.0
    model: str = DEFAULT_MODEL
    model_revision: str | None = None
    period_ms: int = 2000
    chunk_ms: int = 20
    max_model_len: int = 32768
    max_num_seqs: int = 16
    gpu_memory_utilization: float = 0.9
    tokens_per_tick: int = 25
    max_audio_chunks: int = 64
    wait_budget_s: float = 1.6
    seed_tokens: int = 0
    ingest_workers: int = 8
    worker_port: int = 50054
    gateway_port: int = 8907
    client_shards: int = 1
    startup_timeout_s: int = 360
    quiet_seconds: int = 60
    output_root: Path | None = None
    worker_python: Path = Path(".venv-vllm023/bin/python")
    client_python: str | None = None
    allow_dirty: bool = False
    skip_gpu_quiet: bool = False
    skip_environment_check: bool = False
    label: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", self.root.expanduser().resolve())
        worker_python = self.worker_python.expanduser()
        if not worker_python.is_absolute():
            worker_python = self.root / worker_python
        # Do not resolve this symlink: Python uses the invoked venv path to
        # discover pyvenv.cfg and its site-packages.
        worker_python = Path(os.path.abspath(worker_python))
        object.__setattr__(self, "worker_python", worker_python)
        if self.client_python is None:
            object.__setattr__(self, "client_python", str(worker_python))
        if self.model == DEFAULT_MODEL and self.model_revision is None:
            object.__setattr__(self, "model_revision", DEFAULT_MODEL_REVISION)
        if self.output_root is None:
            object.__setattr__(
                self,
                "output_root",
                self.root / "results" / "e1_capacity_bottleneck" / "runs",
            )
        else:
            object.__setattr__(self, "output_root", self.output_root.expanduser().resolve())
        self.validate()

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

    def validate(self) -> None:
        """Reject combinations known to produce invalid or ambiguous evidence."""
        if self.mode not in MODES:
            raise ValueError(f"unknown E1 mode: {self.mode}")
        if self.sessions <= 0:
            raise ValueError("sessions must be positive")
        if self.duration_s <= 0:
            raise ValueError("duration must be positive")
        if self.period_ms <= 0 or self.chunk_ms <= 0:
            raise ValueError("period-ms and chunk-ms must be positive")
        if self.max_model_len <= 0 or self.max_num_seqs <= 0:
            raise ValueError("MML and max-num-seqs must be positive")
        if not 0 < self.gpu_memory_utilization < 1:
            raise ValueError("gpu-memory-utilization must be between 0 and 1")
        if self.client_shards <= 0 or self.sessions % self.client_shards:
            raise ValueError("sessions must be evenly divisible by client-shards")
        if self.duration_s >= 600 and self.max_model_len < 32768:
            raise ValueError(
                "runs of 600s or longer require MML >= 32768; smaller values "
                "can create a false-stability max-model-length stall"
            )
        if self.seed_tokens and self.mode != "paringest":
            raise ValueError("seed-tokens requires paringest mode")
        if self.worker_port == self.gateway_port:
            raise ValueError("worker and gateway ports must differ")

    def manifest_config(self) -> dict[str, object]:
        """Return stable experiment parameters for ``manifest.json``."""
        data = asdict(self)
        for key in (
            "root",
            "output_root",
            "worker_python",
        ):
            data.pop(key)
        data["worker"] = self.mode_spec.worker
        data["observations"] = {
            "trace": self.trace,
            "scheduler": self.trace,
            "per_request": self.trace and self.mode == "paringest",
            "per_iteration": self.trace and self.mode == "paringest",
        }
        data["execution_policy"] = {
            "allow_dirty": self.allow_dirty,
            "gpu_quiet_check": not self.skip_gpu_quiet,
            "environment_check": not self.skip_environment_check,
        }
        for key in ("allow_dirty", "skip_gpu_quiet", "skip_environment_check"):
            data.pop(key)
        return data
