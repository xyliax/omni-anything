# Runtime environments

`infra/env/` is the project-level entry point for reproducible software environments. It is not
owned by one experiment. Runtime-specific versions, model revisions, and patches are grouped into
named profiles so later experiments can use a different stack without weakening an existing lock.

## Profiles

| Profile | Purpose | Used by | Status |
| --- | --- | --- | --- |
| `cuda13_vllm023` | CUDA 13 Python stack, vLLM 0.23, PyTorch/CUDA analysis dependencies, and Metronome gateway | baseline & conveyor（全部真机 run） | Implemented and locked |

The filesystem represents implemented environments only, so there is currently one directory under
`profiles/`.

## New-machine setup

Supported host: Linux x86_64, Python 3.12 with `venv`, and an NVIDIA driver capable of running the
CUDA 13 runtime shipped by the locked wheels. Go 1.22.5+ is used for the gateway; setup downloads a
SHA-256-verified local toolchain when the host Go is absent or too old.

```bash
bash infra/env/setup.sh --profile cuda13_vllm023 --download-models
python3 infra/env/verify.py --worker-python .venv-vllm023/bin/python
```

Omit `--download-models` when the exact snapshots are already cached or only CPU-side development is
needed. Use `--venv`, `--python`, or `--go` when host paths differ. Setup is idempotent and never
edits `third_party/`:

```text
.venv-vllm023/              Python environment and resolved pip freeze
.build/metronome-gateway    built Go gateway (baseline arm, verbatim from the pin)
.build/conveyor-gateway     built Go gateway (conveyor arm, staggered fork)
.tools/                     optional repository-local Go toolchain
```

All three paths are ignored by Git.

## Profile contents

```text
profiles/cuda13_vllm023/
├── requirements.in         human-maintained direct dependencies
├── requirements.lock       complete Python 3.12/Linux x86_64 wheel graph with SHA-256 hashes
└── patches/
    └── vllm-0.23-fix1.patch
```

This is the single runtime family for the baseline stack (Qwen2.5-Omni on vLLM 0.23). A future
worker may add another profile only if it actually requires incompatible
dependencies.

The patch is applied only inside the selected virtual environment. Blackwell-only Metronome fixes
are intentionally outside the RTX 3090 profile. Models are experimental inputs, so their locks live
with their owners as the `REVISION` constant in `experiments/<experiment>/config/model.py`
(the runner resolves it via `lab.probes.resolve_model_snapshot` at launch, which fails fast
when the pinned snapshot is not cached); `--download-models` imports those constants and
fetches the pinned snapshots.

## Adding a profile

Add a profile only when its consumer is implemented. A profile must provide a complete hashed lock,
versioned patches, setup dispatch, verification checks, and CPU-only tests. Each consuming experiment
must pin its own immutable model revision in `config/model.py`. Do not silently change
`cuda13_vllm023` to satisfy a future worker; that would make existing evidence harder to reproduce.

## Upgrading vLLM (re-audit checklist)

The stack monkeypatches and forks private engine internals. Before bumping the vLLM version,
re-audit every item against the new source:

1. `experiments/*/worker/stream_server.py` — the paringest copy of
   `AsyncLLM._add_streaming_input_request` (second-order fork of a private API).
2. `engines/conveyor/worker/engine_patch/sitecustomize.py` — every wrapped symbol:
   `EngineCore` utility dispatch, `Scheduler._handle_stopped_request` /
   `_update_request_as_session` / `_update_waiting_for_remote_kv`,
   `SimpleCPUOffloadConnector.update_state_after_alloc`,
   `SimpleCPUOffloadScheduler._prepare_eager_store_specs`, and the `num_computed_tokens == 0`
   waiting-path assumption the resume rides on.
3. The two upstream bugs the patch works around (eager-store cursor drift on streaming
   re-entry; `session.max_tokens` frozen at construction) — check whether upstream fixed them,
   then delete the corresponding wrappers.
4. `infra/trace/collectors/vllm_scheduler_trace/sitecustomize.py` — the `Scheduler.schedule` wrap.
5. `infra/env/profiles/cuda13_vllm023/` FIX patches — reconcile against the new wheels.
