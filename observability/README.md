# Shared observability

`observability/` turns run-local evidence from any experiment into one inspectable timeline. It is
global infrastructure because parsing, trace metadata, collision handling, and Perfetto event
semantics must not drift between E1, E2, E3, and future experiments.

## Code map

| Path | Responsibility |
| --- | --- |
| `bundle.py` | Resolve runs globally, parse known raw artifacts, and align E1 clocks |
| `export_perfetto.py` | Adapt bundles to Perfetto, replay E2/E3, and write trace metadata |
| `vllm_scheduler_trace/` | Optional `sitecustomize` injection for vLLM EngineCore decisions |

Experiment code owns how evidence is produced. This package owns how timed evidence is parsed and
visualized. It does not own experiment claims, aggregate statistics, or paper figures.

## Open a run

```bash
# A globally unique run ID, an experiment/run-id pair, or a path all work.
python3 -m observability.export_perfetto <run-id>
python3 -m observability.export_perfetto e2_kv_conveyor/<run-id>
python3 -m observability.export_perfetto results/e2_kv_conveyor/runs/<run-id>

# Backfill every retained run. Existing trace or metadata files cause failure.
python3 -m observability.export_perfetto --all
```

Open `derived/timeline.trace.json.gz` at [Perfetto](https://ui.perfetto.dev). The browser processes
the trace locally. `derived/timeline.trace.metadata.json` states the visualization kind, evidence
boundary, source hashes, event counts, clock alignment, and any global shift applied to make
pre-zero prefetch events display cleanly.

The exporter never overwrites a trace or its metadata. To replace a reproducible derived artifact,
remove both files deliberately, then export again. Raw run evidence is never modified.

## Current adapters

| Evidence | Visualization |
| --- | --- |
| E0 `measurements.csv` | Measurement-matrix segments; explicitly not a wall-clock execution |
| E1 scheduler/request/KV/GPU logs | End-to-end engine, gateway, scheduler, KV, and GPU lanes |
| E2 `transfers.jsonl` plus manifest | Full source E1 view, then stored H2D and replayed compute lanes |
| E3 manifest plus link samples | Full source E1 view, then replayed H2D and compute lanes for every arm |
| Any run's `events.jsonl` | Experiment-neutral slice, instant, and counter tracks |

For E1, one gateway `step()` writes one request-push (`P`) row per session. The bundle parser
collapses that millisecond-scale fan-out into one logical gateway tick; individual `P` rows are not
displayed as separate global ticks.

E2/E3 start with E1 engine, gateway, KV, scheduler, GPU, and starvation events whose scheduler
trace drives their compute profile. Those processes are prefixed `E1 source (real)` because they
are reference evidence, not an engine execution performed by E2/E3. Mechanism processes are
appended underneath. Replay uses the same `simulate()` implementation and the exact manifest and
H2D samples that produced each summary. Appended E2/E3 lanes remain mechanism-level evidence and do
not imply active vLLM KV block migration.

## Add a new experiment

Prefer `events.jsonl` when an existing raw adapter does not fit. Each line is one JSON object:

```json
{"type":"slice","track":"worker","t_s":1.2,"duration_s":0.05,"name":"prefill","args":{"batch":4}}
{"type":"instant","track":"scheduler","t_s":2.0,"name":"eviction","args":{"session":3}}
{"type":"counter","track":"kv","t_s":2.0,"name":"pool","value":0.98}
```

Required common fields are `type`, `track`, `t_s`, and `name`. A slice also requires `duration_s`; a
counter requires `value`. Times are seconds on one run-relative clock. Put domain details under
`args`. The parser rejects unknown event types and missing fields.

A new adapter belongs in `bundle.py` only when it represents a stable raw evidence format. Its
Perfetto mapping belongs in `export_perfetto.py`, with a meaningful nonzero event count and source
hashes in metadata. Add fixture coverage and the retained-run validation before relying on it.

## Scheduler instrumentation

E1's `--trace` runner option prepends `vllm_scheduler_trace/` to the worker tree's `PYTHONPATH` and
sets `OMNI_SCHEDULER_TRACE`. The patch activates only when that variable exists. Initialization
failure terminates the worker, and recording errors go to structured JSONL, so a requested trace
cannot silently become an empty primary artifact.
