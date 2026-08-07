# omni-anything

Single-GPU research on concurrent duplex voice serving and asynchronous agent-result injection. The
current candidate is a scheduled tail-KV conveyor that trades otherwise-idle H2D bandwidth for
additional concurrent capacity.

## Start here

| Goal | Go to |
| --- | --- |
| Understand the problem and current conclusions | [`docs/README.md`](docs/README.md) |
| See the E0-E6 experiment roadmap and implementation status | [`experiments/README.md`](experiments/README.md) |
| Prepare a new machine | [`environment/README.md`](environment/README.md) |
| Inspect raw evidence and derived artifacts | [`results/README.md`](results/README.md) |
| Trace and visualize any run | [`observability/README.md`](observability/README.md) |
| Read repository maintenance rules | [`AGENTS.md`](AGENTS.md) |

Current status: E0 and E1 have real-machine evidence. E2 and E3 are completed trace-driven CUDA
mechanism experiments with an explicit non-end-to-end claim boundary. E4-E6 remain planned.

## Repository map

```text
docs/          research conclusions, problem statement, design, and experiment plan
environment/   reproducible runtime profiles, setup, locks, patches, and verification
experiments/   executable experiment code, grouped by E number and purpose
observability/ shared parsing, instrumentation, deterministic replay, and Perfetto export
results/       curated evidence, grouped by the same experiment names
tests/         CPU-only tests for configuration, evidence handling, and analysis
third_party/   pinned upstream source; project changes never go here
.context/      background material; not a source of current project facts
```

The directory names under `experiments/` and `results/` deliberately match. For example:

```text
experiments/e1_capacity_bottleneck/   code that runs and analyzes E1
results/e1_capacity_bottleneck/       E1 runs and their derived artifacts
```

## New-machine setup

The shared runtime profile supports the E1 baseline and the CUDA calibration used by E2/E3:

```bash
bash environment/setup.sh --profile cuda13_vllm023 --download-models
python3 environment/verify.py --worker-python .venv-vllm023/bin/python
```

## Run E1

```bash
# Resolve and inspect every command without creating evidence or using the GPU.
bash experiments/e1_capacity_bottleneck/run.sh \
  --mode paringest --trace --n 8 --duration 600 --plan

# Run one fresh-worker point into a new immutable run directory.
bash experiments/e1_capacity_bottleneck/run.sh \
  --mode paringest --trace --n 8 --duration 600
```

Detailed modes, preflight checks, output files, and extension points are documented in
[`experiments/e1_capacity_bottleneck/README.md`](experiments/e1_capacity_bottleneck/README.md).

## Run E2 and E3

```bash
.venv-vllm023/bin/python -m experiments.e2_kv_conveyor.run --gpu 3
.venv-vllm023/bin/python -m experiments.e3_phase_scheduling.run --gpu 3
```

These commands create mechanism-level evidence, not an end-to-end vLLM conveyor result. See the
experiment READMEs for the evidence boundary and matrix controls.

## Inspect any run

Every retained run has a run-local Perfetto trace. Regenerate a missing trace without changing raw
evidence with:

```bash
python3 -m observability.export_perfetto <run-id-or-path>
```

See [`observability/README.md`](observability/README.md) for lane semantics and extension points.

## CPU-only checks

```bash
python3 -m compileall -q environment experiments observability tests
find environment experiments observability -name '*.sh' -print0 | xargs -0 -n1 bash -n
python3 -m unittest discover -v
```

The full setup and GPU experiments are intentionally outside normal CI.
