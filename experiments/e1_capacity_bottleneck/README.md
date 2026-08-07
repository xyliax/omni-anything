# E1: Real-machine capacity bottleneck

E1 establishes the baseline motivation: on the real vLLM/Qwen-Omni stack, resident KV grows until
capacity management stops useful service while GPU compute is still available. The experiment does
not implement the proposed conveyor; that is E2.

## Code map

| Path | Responsibility |
| --- | --- |
| `run.sh` | Single stable command-line entry point |
| `cli.py` | Parse user options and print side-effect-free plans |
| `config.py` | Declare mode differences, defaults, and invalid parameter combinations |
| `preflight.py` | Inspect Git, runtime, model, ports, GPU, and shared-GPU quiet state |
| `artifacts.py` | Create immutable run directories and maintain manifest/status/checksums |
| `runner.py` | Start, monitor, and clean up worker, gateway, sampler, and client processes |
| `workers/` | Project-owned instrumented worker variants |
| `analysis/` | Compatibility imports for older E1 analysis commands |
| `wait_for_gpu.sh` | Standalone shared-GPU quiet-window check used by preflight |

Shared parsing, scheduler injection, and Perfetto export live in
[`../../observability/`](../../observability/).

The chronological workflow lives only in `runner.py`. Configuration, host inspection, evidence
bookkeeping, worker behavior, and analysis do not import process orchestration.

## Prepare the runtime

```bash
bash environment/setup.sh --profile cuda13_vllm023 --download-models
python3 environment/verify.py --worker-python .venv-vllm023/bin/python
```

## Plan and run

```bash
# No directory creation and no GPU processes.
bash experiments/e1_capacity_bottleneck/run.sh \
  --mode paringest --trace --n 8 --duration 600 --plan

# Full observation run.
bash experiments/e1_capacity_bottleneck/run.sh \
  --mode paringest --trace --gpu 3 --n 8 --duration 600 --mml 32768

# Parallel ingest with controlled initial context.
bash experiments/e1_capacity_bottleneck/run.sh \
  --mode paringest --n 8 --duration 180 --seed-tokens 6000

# Uninstrumented upstream baseline.
bash experiments/e1_capacity_bottleneck/run.sh \
  --mode vanilla --n 8 --duration 600
```

## Implementations and tracing

`--mode` has exactly two behaviorally meaningful values:

| Mode | Worker | Behavioral meaning |
| --- | --- | --- |
| `vanilla` | Pinned Metronome worker, executed directly | No project worker changes |
| `paringest` | `workers/parallel_ingest.py` | Input processing moves across sessions into a thread pool |

`--trace` is orthogonal. It enables scheduler tracing for either mode. With `paringest`, it also
enables the worker's per-request and per-iteration event logs. Tracing changes evidence detail, not
the implementation named by `--mode`. It still adds runtime patching and log I/O, so performance
comparisons should retain trace-off primary runs and use traced runs for causal analysis.

Add a mode only for a new system behavior. Add an observation behind `--trace`; do not encode it as
another mode or copy the runner.

## Preflight and evidence

Before starting GPU processes, the runner rejects a dirty worktree, occupied ports, missing build
outputs, wrong package versions, a missing FIX 1 marker, an uncached model revision, a busy GPU, and
known false-stability configurations such as a 600-second run with `MML < 32768`.

Each invocation creates:

```text
results/e1_capacity_bottleneck/runs/<run-id>/
├── manifest.json
├── status.json
├── client.json
├── client.txt
├── worker.log
├── gateway.log
├── gpu.csv
├── kv.log
└── trace-dependent logs
```

Only `state=success` with `validation.valid=true` is a complete run. Failed and interrupted runs may
be kept temporarily for diagnosis, then removed after the defect is understood.

## Analysis

The parser in `observability/bundle.py` is the single source of log parsing and clock alignment.
Export the run to Perfetto with:

```bash
python3 -m observability.export_perfetto <run-id>
```

The command creates the trace plus `timeline.trace.metadata.json`, refuses to replace either
artifact, records all input hashes/event counts/alignment, and rejects request-only runs instead of
emitting empty engine lanes. New analysis frontends should consume `observability.build_bundle()`
instead of implementing another raw-log parser or embedding run-specific event times in source.

The paringest worker remains a close copy of the pinned upstream server. Treat it as a known
maintenance boundary: an upstream/vLLM upgrade must audit it, and E2 must not add another copy.
