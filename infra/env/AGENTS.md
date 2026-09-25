# Runtime Environment

`infra/env/` is the project-level entry point for reproducible software environments. It is not
owned by one experiment. Runtime-specific versions, model revisions, and patches are grouped into
named profiles so later experiments can use a different stack without weakening an existing lock.

## Profiles

| Profile | Purpose | Used by | Status |
| --- | --- | --- | --- |
| `cuda13_vllm023` | CUDA 13 Python stack, vLLM 0.23, PyTorch/CUDA analysis dependencies, and Metronome gateway | matched Metronome baseline 与 Pilarius 的登记原型 | Implemented and locked |

Profiles describe implemented environments; the table is not a restriction on future experiment configurations.

## New-Machine Setup

Supported host: Linux x86_64, a C/C++ compiler, `patch`, and an NVIDIA driver capable of running the
CUDA 13 runtime shipped by the locked wheels. Missing Python is installed locally with a checksum-pinned
uv bootstrap and managed Python; an existing Python 3.12 requires `venv`. Go 1.22.5+ is used for the gateway; setup downloads a
SHA-256-verified local toolchain when the host Go is absent or too old.

```bash
bash infra/env/setup.sh --profile cuda13_vllm023 --download-models
bash infra/env/setup.sh --profile cuda13_vllm023 --download-models --model-preset minicpm_o45
python3 infra/env/verify.py --worker-python .venv-vllm023/bin/python
```

For the requested H100 80GB HBM3 host (reported driver 595.91.07, CUDA 13.2), keep this profile:
the installed PyTorch wheel uses CUDA 13.0 and includes `sm_90`. NVIDIA's
[driver compatibility rule](https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html)
allows newer drivers to run older CUDA applications. The `nvidia-smi` CUDA field describes driver capability,
not the Python runtime. The target host still needs actual execution validation; no H100 result is claimed.

From the repository root on the new machine:

```bash
git pull --ff-only
bash infra/env/setup.sh --download-models --model-preset all --gpu 0
source .venv-vllm023/bin/activate
python -m experiments.conveyor.check --gpu 0 --model-preset all
```

Setup reports missing OS tools before installing wheels. On Ubuntu install them with
`sudo apt-get update && sudo apt-get install -y build-essential patch curl ca-certificates` if needed.
The runtime, model weights and compilation cache consume substantial disk space; place the repository and
`HF_HOME` on the data volume before setup. `HF_HUB_CACHE` is also honored by both downloader and runner.
`--model-preset all` downloads both pinned snapshots; reruns reuse complete cached weights.

The last command checks driver/BF16 execution, both gateway binaries, complete checkpoint shards,
the actual KV copy backend and two sessions sharing one slot for each model. Successful temporary runs
are removed automatically; summaries are in `.build/checks/`. Failures retain the named raw directory
for diagnosis. `--keep-results` explicitly retains successful runs, and `--gpu-trace` enables a complete
business capture. These are functional checks with uncalibrated costs, not formal capacity measurements.
Do not reuse the old machine's admission cost profile for H100 performance experiments.

Omit `--download-models` when the exact snapshots are already cached or only CPU-side development is
needed. Use `--venv`, `--python`, or `--go` when host paths differ. Setup is idempotent and never
edits `third_party/`:

```text
.venv-vllm023/              Python environment and resolved pip freeze
.build/metronome-gateway    built Go gateway (upstream Metronome, verbatim from the pin)
.build/conveyor-gateway     built Go gateway (Pilarius release-offset fork)
.tools/                     optional repository-local Go toolchain
```

These paths are ignored by Git. With a custom `--venv`, export
`OMNI_WORKER_PYTHON=/absolute/path/to/venv/bin/python` for both experiment runners; setup prints this command.
GPU selection defaults to index zero, and `--gpu` overrides it explicitly.

## Profile Contents

```text
profiles/cuda13_vllm023/
├── requirements.in         human-maintained direct dependencies
├── requirements.lock       complete Python 3.12/Linux x86_64 wheel graph with SHA-256 hashes
└── patches/
    └── vllm-0.23-fix1.patch
```

This is the locked runtime family for the current audio-input/text-output model presets on vLLM 0.23. A future
worker may add another profile only if it actually requires incompatible
dependencies.

The patch is applied only inside the selected virtual environment. Blackwell-only Metronome fixes
are intentionally outside this profile. Models are experimental inputs, so their locks live
with the model presets in `experiments/shared/model.py`
(the runner resolves it via `infra.run.probes.resolve_model_snapshot` at launch, which fails fast
when the pinned snapshot is not cached); `--download-models` imports the selected preset and
fetches its pinned snapshot. The default preset preserves the existing Qwen path.

Both worker runners expose the selected environment's wheel-provided CUDA toolkit through
`infra.env.verify.cuda_toolkit_environment`: `CUDA_HOME`, `CUDA_PATH` and the compiler `PATH`
point to that venv's `nvidia/cu13` directory. This is required for FlashInfer JIT on hosts that
only have a driver. The venv `bin` directory also supplies `ninja` when the shell is not activated.
BF16 execution and KV memcpy alone do not test compiler discovery.
Keep the venv interpreter symlink unresolved so a custom runtime selects its own toolkit.

The compiler, CRT, NVVM and CCCL wheels are constrained by the CUDA toolkit extra in
`requirements.in`. This corrects the previous lock's mixed compiler/header minor versions;
the CUDA runtime and model/runtime packages remain pinned. Fresh installs must compile a
FlashInfer sampling kernel before being considered ready for model serving. Do not disable
CCCL's toolkit compatibility check to work around a mismatched installation.

## Adding a Profile

Add a profile only when its consumer is implemented. A profile must provide a complete hashed lock,
versioned patches, setup dispatch, verification checks, and CPU-only tests. The measured stack pins
its immutable model revision once in `experiments/shared/model.py`. Do not silently change
`cuda13_vllm023` to satisfy a future worker; that would make existing evidence harder to reproduce.

## Upgrading vLLM

The stack monkeypatches and forks private engine internals. Before bumping the vLLM version,
re-audit every item against the new source:

1. `engines/*/worker/stream_server.py` — the paringest and Pilarius copies of
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
6. `engines/audio_features.py` — processor call signature, resampling order, STFT boundary,
   mask and log-mel normalization semantics; rerun the locked-environment numerical tests
   after a vLLM or Transformers change.

Hardware portability is conditional on this profile: Linux/NVIDIA CUDA driver and the locked vLLM private API contract. GPU identity is probed at launch; tensor-derived copy geometry is not tied to a card name. Changing hardware requires fresh compute/transfer cost calibration and KV pool limits; an old admission profile is not a cross-device SLO guarantee. MiniCPM uses an additional pinned model preset on the same environment; native vLLM-Omni audio-output integration remains a distinct workload/runtime task.

完整 hash lock 使用 `--no-deps --require-hashes` 安装，避免已安装 extras 的元数据被 resolver 当成无 hash 的新输入；安装后仍须 `pip check` 检查完整依赖闭包。FlashInfer JIT 检查同时覆盖 wheel nvcc 和所选 venv 的 ninja。
