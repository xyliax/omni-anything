"""Collection-side code that runs inside experiment processes.

``worker_obs`` is imported by every experiment worker (front-end process);
``vllm_scheduler_trace/`` is a sitecustomize dir injected into the spawned
EngineCore process via PYTHONPATH (see :mod:`infra.trace.collect`).
"""
