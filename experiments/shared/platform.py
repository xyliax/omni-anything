"""This machine: shared RTX 3090 (24 GB) on PCIe Gen3, worker venv pinned to
the cuda13_vllm023 profile.

GPU_SAMPLE_PERIOD_S is the nvidia-smi -lms value; 0.2s gives ~10 samples per
2s tick so the busy window inside a tick is resolvable (each gpu.csv row
carries nvidia-smi's own wall-clock timestamp, which trace parsing aligns to
the scheduler clock). The card is shared and the co-tenant is bursty
(contention inflates decode steps up to 2x) — check the GPU is idle before
a formal run.
"""

DEVICE_NAME = "RTX 3090"
DEFAULT_GPU_INDEX = 3  # per-run knob (--gpu); this is just the usual card
WORKER_PYTHON = ".venv-vllm023/bin/python"
WORKER_PORT = 50054
GATEWAY_PORT = 8907
GPU_SAMPLE_PERIOD_S = 0.2


def manifest() -> dict:
    return {
        "device_name": DEVICE_NAME,
        "worker_python": WORKER_PYTHON,
        "worker_port": WORKER_PORT,
        "gateway_port": GATEWAY_PORT,
        "gpu_sample_period_s": GPU_SAMPLE_PERIOD_S,
    }
