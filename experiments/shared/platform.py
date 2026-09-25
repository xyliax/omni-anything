"""Portable launch defaults; actual hardware is recorded by run probes.

GPU_SAMPLE_PERIOD_S is the nvidia-smi -lms value; 0.2s gives ~10 samples per
2s tick so the busy window inside a tick is resolvable (each gpu.csv row
carries nvidia-smi's own wall-clock timestamp, which trace parsing aligns to
the scheduler clock).
"""

import os
from pathlib import Path

DEFAULT_GPU_INDEX = 0
WORKER_PYTHON = ".venv-vllm023/bin/python"
WORKER_PORT = 50054
GATEWAY_PORT = 8907
GPU_SAMPLE_PERIOD_S = 0.2


def worker_python(root: Path) -> Path:
    # Preserve the venv symlink: resolving it would bypass pyvenv.cfg.
    return root / Path(os.environ.get("OMNI_WORKER_PYTHON", WORKER_PYTHON)).expanduser()


def manifest() -> dict:
    return {
        "device_identity_source": "manifest.hardware.gpu",
        "worker_python": os.environ.get("OMNI_WORKER_PYTHON", WORKER_PYTHON),
        "worker_port": WORKER_PORT,
        "gateway_port": GATEWAY_PORT,
        "gpu_sample_period_s": GPU_SAMPLE_PERIOD_S,
    }
