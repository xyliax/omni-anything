# vLLM scheduler trace injection

This directory is a deliberately isolated `PYTHONPATH` injection point. The
E1 runner prepends exactly this directory so Python imports `sitecustomize.py`
inside vLLM's spawned EngineCore process.

Set `OMNI_SCHEDULER_TRACE` to the scheduler output path and
`OMNI_SCHEDULER_TRACE_ERRORS` to a JSONL error path. Initialization failure is
fatal when tracing is requested; per-step serialization errors are recorded
and later rejected by artifact validation.

Do not add ordinary package modules here. Importing this directory has process
startup side effects by design.
