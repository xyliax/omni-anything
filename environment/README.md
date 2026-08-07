# Runtime environments

`environment/` is the project-level entry point for reproducible software environments. It is not
owned by one experiment. Runtime-specific versions, model revisions, and patches are grouped into
named profiles so later experiments can use a different stack without weakening an existing lock.

## Profiles

| Profile | Purpose | Used by | Status |
| --- | --- | --- | --- |
| `cuda13_vllm023` | CUDA 13 Python stack, vLLM 0.23, PyTorch/CUDA analysis dependencies, and Metronome gateway | E0-E3 | Implemented and locked |

The filesystem represents implemented environments only, so there is currently one directory under
`profiles/`.

## New-machine setup

Supported host: Linux x86_64, Python 3.12 with `venv`, and an NVIDIA driver capable of running the
CUDA 13 runtime shipped by the locked wheels. Go 1.22.5+ is used for the gateway; setup downloads a
SHA-256-verified local toolchain when the host Go is absent or too old.

```bash
bash environment/setup.sh --profile cuda13_vllm023 --download-models
python3 environment/verify.py --worker-python .venv-vllm023/bin/python
```

Omit `--download-models` when the exact snapshots are already cached or only CPU-side development is
needed. Use `--venv`, `--python`, or `--go` when host paths differ. Setup is idempotent and never
edits `third_party/`:

```text
.venv-vllm023/              Python environment and resolved pip freeze
.build/metronome-gateway    built Go gateway
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

E2/E3 reuse this profile because they intentionally keep E1's Qwen2.5-Omni software/model baseline
and add a pinned CUDA transfer calibration; they are not a separate runtime family. A future
end-to-end conveyor worker may add another profile only if it actually requires incompatible
dependencies.

The patch is applied only inside the selected virtual environment. Blackwell-only Metronome fixes
are intentionally outside the RTX 3090 profile. Models are experimental inputs, so their locks live
with their owners at `experiments/<experiment>/model.lock`; `--download-models` discovers those locks.

## Adding a profile

Add a profile only when its consumer is implemented. A profile must provide a complete hashed lock,
versioned patches, setup dispatch, verification checks, and CPU-only tests. Each consuming experiment
must provide its own immutable model revision in `model.lock`. Do not silently change
`cuda13_vllm023` to satisfy a future worker; that would make existing evidence harder to reproduce.
