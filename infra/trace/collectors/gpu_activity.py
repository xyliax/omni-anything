"""CUPTI-backed GPU activity and explicit host-side transfer control events."""
from __future__ import annotations

import json
import os
import threading
import time
from contextlib import nullcontext
from pathlib import Path

_active = False


class TransferObserver:
    def __init__(self, path):
        self.handle = Path(path).open("x", buffering=1, encoding="utf-8") if path else None
        self.lock = threading.Lock()

    def __call__(self, event, **fields):
        if self.handle:
            row = {"schema_version": 1, "time": time.time(), "pid": os.getpid(),
                   "event": event, **fields}
            with self.lock:
                self.handle.write(json.dumps(row) + "\n")

    def close(self):
        if self.handle:
            self.handle.close()


class GpuCapture:
    def __init__(self, path):
        self.path = Path(path)
        self.profiler = None
        self.finished = False

    def start(self):
        global _active
        import torch
        if self.profiler is not None or self.finished or self.path.exists():
            raise RuntimeError("GPU capture may only be started once per run")
        self.profiler = torch.profiler.profile(
            activities=[torch.profiler.ProfilerActivity.CPU, torch.profiler.ProfilerActivity.CUDA],
            record_shapes=False, profile_memory=False, with_stack=False,
            experimental_config=torch._C._profiler._ExperimentalConfig(profile_all_threads=True),
        )
        self.profiler.start()
        _active = True

    def stop(self):
        global _active
        if self.profiler is None:
            return
        _active = False
        self.profiler.stop()
        if self.path.exists():
            raise FileExistsError(self.path)
        self.profiler.export_chrome_trace(str(self.path))
        self.profiler = None
        self.finished = True


def apply():
    """Install explicit start/stop utility calls in the EngineCore process."""
    from vllm.v1.engine.core import EngineCore
    from vllm.v1.executor.uniproc_executor import UniProcExecutor

    def gpu_trace_start(self):
        if getattr(self, "_omni_gpu_capture", None) is not None:
            raise RuntimeError("GPU capture already requested for this engine")
        self._omni_gpu_capture = GpuCapture(os.environ["OMNI_GPU_ACTIVITY"])
        self._omni_gpu_capture.start()
        return {"started": True}

    def gpu_trace_stop(self):
        if capture := getattr(self, "_omni_gpu_capture", None):
            capture.stop()
        return {"stopped": True}

    EngineCore.gpu_trace_start = gpu_trace_start
    EngineCore.gpu_trace_stop = gpu_trace_stop

    original_execute = UniProcExecutor.execute_model
    def execute(self, scheduler_output, *args, **kwargs):
        context = nullcontext()
        if _active:
            import torch
            requests = ",".join(scheduler_output.num_scheduled_tokens)
            context = torch.autograd.profiler.record_function(f"pilarius.compute req={requests}")
        with context:
            return original_execute(self, scheduler_output, *args, **kwargs)
    UniProcExecutor.execute_model = execute
