# Results index

Code and evidence share experiment names:

```text
results/<experiment>/runs/<run-id>/
results/<experiment>/aggregates/<aggregate-id>/
```

Raw evidence, run-local derived artifacts, and cross-run aggregates are not split into generic
`paper`, `figures`, or `viz` trees.

Every retained run contains `derived/timeline.trace.json.gz` and
`derived/timeline.trace.metadata.json`. Open the compressed trace directly at
[Perfetto](https://ui.perfetto.dev), or regenerate a missing run-local visualization with:

```bash
python3 -m observability.export_perfetto <run-id-or-path>
```

The exporter refuses replacement. Metadata records the visualization kind, source hashes, event
counts, evidence boundary, clock alignment, and any display-only time shift.

## Evidence boundary

| Experiment | Evidence | Timeline kind |
| --- | --- | --- |
| E0 | Real CUDA interference microbenchmark | Measurement matrix, not wall-clock execution |
| E1 | End-to-end Qwen2.5-Omni/vLLM/Metronome execution | Real engine and service timeline |
| E2 | E1-trace-driven simulation plus fresh real pinned H2D calibration | E1 view plus mechanism replay lanes |
| E3 | E1-trace-driven phase simulation plus fresh real pinned H2D calibration | E1 view plus mechanism replay lanes |

E2/E3 do not implement active-request KV migration in vLLM. Their manifests, summaries, and trace
metadata repeat this boundary so a run cannot be mistaken for an end-to-end serving result.

## E0: DMA interference

- `20260804_initial` ([trace](e0_dma_interference/runs/20260804_initial/derived/timeline.trace.json.gz), [metadata](e0_dma_interference/runs/20260804_initial/derived/timeline.trace.metadata.json))

This retained legacy run predates the common manifest/status format. It contains the original 20
measurement points and summary and remains the E0 evidence source.

## E1: Capacity bottleneck

- `20260806T210551.398631Z_e1_paringest_trace_n8_p2000_mml32768_seed0_3139eab_formal-rerun` ([trace](e1_capacity_bottleneck/runs/20260806T210551.398631Z_e1_paringest_trace_n8_p2000_mml32768_seed0_3139eab_formal-rerun/derived/timeline.trace.json.gz), [metadata](e1_capacity_bottleneck/runs/20260806T210551.398631Z_e1_paringest_trace_n8_p2000_mml32768_seed0_3139eab_formal-rerun/derived/timeline.trace.metadata.json))

This is the only retained E1 run. It has complete manifest/status/checksums plus client, worker,
gateway, GPU, KV, per-request, per-iteration, and scheduler evidence. Its trace includes engine,
gateway, scheduler, KV, and GPU lanes.

## E2: KV conveyor mechanism

Five independent CUDA calibration repetitions:

- `20260806T212249.568464Z_n8_tail4096_r0` ([trace](e2_kv_conveyor/runs/20260806T212249.568464Z_n8_tail4096_r0/derived/timeline.trace.json.gz), [metadata](e2_kv_conveyor/runs/20260806T212249.568464Z_n8_tail4096_r0/derived/timeline.trace.metadata.json))
- `20260806T212257.643071Z_n8_tail4096_r1` ([trace](e2_kv_conveyor/runs/20260806T212257.643071Z_n8_tail4096_r1/derived/timeline.trace.json.gz), [metadata](e2_kv_conveyor/runs/20260806T212257.643071Z_n8_tail4096_r1/derived/timeline.trace.metadata.json))
- `20260806T212305.671337Z_n8_tail4096_r2` ([trace](e2_kv_conveyor/runs/20260806T212305.671337Z_n8_tail4096_r2/derived/timeline.trace.json.gz), [metadata](e2_kv_conveyor/runs/20260806T212305.671337Z_n8_tail4096_r2/derived/timeline.trace.metadata.json))
- `20260806T212313.739528Z_n8_tail4096_r3` ([trace](e2_kv_conveyor/runs/20260806T212313.739528Z_n8_tail4096_r3/derived/timeline.trace.json.gz), [metadata](e2_kv_conveyor/runs/20260806T212313.739528Z_n8_tail4096_r3/derived/timeline.trace.metadata.json))
- `20260806T212322.026937Z_n8_tail4096_r4` ([trace](e2_kv_conveyor/runs/20260806T212322.026937Z_n8_tail4096_r4/derived/timeline.trace.json.gz), [metadata](e2_kv_conveyor/runs/20260806T212322.026937Z_n8_tail4096_r4/derived/timeline.trace.metadata.json))

Aggregate: `e2_kv_conveyor/aggregates/20260806_main/` contains the combined summary and
`capacity_summary.{png,pdf}` with source run IDs and artifact checksums.

## E3: Phase scheduling

Lead sweep at TDMA group size 7:

- `20260806T212404.271928Z_lead10_group7_n8` ([trace](e3_phase_scheduling/runs/20260806T212404.271928Z_lead10_group7_n8/derived/timeline.trace.json.gz), [metadata](e3_phase_scheduling/runs/20260806T212404.271928Z_lead10_group7_n8/derived/timeline.trace.metadata.json))
- `20260806T212411.839238Z_lead25_group7_n8` ([trace](e3_phase_scheduling/runs/20260806T212411.839238Z_lead25_group7_n8/derived/timeline.trace.json.gz), [metadata](e3_phase_scheduling/runs/20260806T212411.839238Z_lead25_group7_n8/derived/timeline.trace.metadata.json))
- `20260806T212417.272807Z_lead50_group7_n8` ([trace](e3_phase_scheduling/runs/20260806T212417.272807Z_lead50_group7_n8/derived/timeline.trace.json.gz), [metadata](e3_phase_scheduling/runs/20260806T212417.272807Z_lead50_group7_n8/derived/timeline.trace.metadata.json))
- `20260806T212422.975569Z_lead80_group7_n8` ([trace](e3_phase_scheduling/runs/20260806T212422.975569Z_lead80_group7_n8/derived/timeline.trace.json.gz), [metadata](e3_phase_scheduling/runs/20260806T212422.975569Z_lead80_group7_n8/derived/timeline.trace.metadata.json))
- `20260806T212428.454110Z_lead120_group7_n8` ([trace](e3_phase_scheduling/runs/20260806T212428.454110Z_lead120_group7_n8/derived/timeline.trace.json.gz), [metadata](e3_phase_scheduling/runs/20260806T212428.454110Z_lead120_group7_n8/derived/timeline.trace.metadata.json))

Group-size sweep at 20 ms lead:

- `20260806T212448.176453Z_lead20_group4_n8` ([trace](e3_phase_scheduling/runs/20260806T212448.176453Z_lead20_group4_n8/derived/timeline.trace.json.gz), [metadata](e3_phase_scheduling/runs/20260806T212448.176453Z_lead20_group4_n8/derived/timeline.trace.metadata.json))
- `20260806T212455.737292Z_lead20_group5_n8` ([trace](e3_phase_scheduling/runs/20260806T212455.737292Z_lead20_group5_n8/derived/timeline.trace.json.gz), [metadata](e3_phase_scheduling/runs/20260806T212455.737292Z_lead20_group5_n8/derived/timeline.trace.metadata.json))
- `20260806T212501.227773Z_lead20_group6_n8` ([trace](e3_phase_scheduling/runs/20260806T212501.227773Z_lead20_group6_n8/derived/timeline.trace.json.gz), [metadata](e3_phase_scheduling/runs/20260806T212501.227773Z_lead20_group6_n8/derived/timeline.trace.metadata.json))
- `20260806T212506.743319Z_lead20_group7_n8` ([trace](e3_phase_scheduling/runs/20260806T212506.743319Z_lead20_group7_n8/derived/timeline.trace.json.gz), [metadata](e3_phase_scheduling/runs/20260806T212506.743319Z_lead20_group7_n8/derived/timeline.trace.metadata.json))
- `20260806T212512.276692Z_lead20_group8_n8` ([trace](e3_phase_scheduling/runs/20260806T212512.276692Z_lead20_group8_n8/derived/timeline.trace.json.gz), [metadata](e3_phase_scheduling/runs/20260806T212512.276692Z_lead20_group8_n8/derived/timeline.trace.metadata.json))

Aggregate: `e3_phase_scheduling/aggregates/20260806_main/` contains all ten scheduling points and
`phase_tradeoffs.{png,pdf}`.

E2/E3 traces first reproduce the source E1 engine/service events under explicitly labeled
`E1 source (real)` processes, then append mechanism lanes replayed from the exact manifest,
retained H2D samples, and E1-derived compute profile. Trace metadata hashes both the local run and
referenced E1 evidence. The appended lanes preserve the summaries' mechanism-level claim boundary.

## Retention rule

- A runner creates a unique directory and never reuses an existing path.
- A formal run is retained only after `status.state=success` and artifact validation pass.
- Failed, interrupted, smoke, obsolete, or superseded outputs are removed after diagnosis.
- Run-local derived outputs stay under that run's `derived/` directory.
- Multi-run analysis stays under the experiment's `aggregates/` directory and records every input
  run ID and source hash.
- `results/` is curated, not append-only. This index must change with every retention decision.
