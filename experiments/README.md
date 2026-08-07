# Experiments

Experiments are the primary unit of organization. Each implemented experiment has a descriptive
directory, its own README, a single user-facing entry point, and a matching directory under
`results/`.

| ID | Question | Status | Code | Evidence |
| --- | --- | --- | --- | --- |
| E0 | Does sustained H2D interfere with decode enough to invalidate the conveyor? | Complete | [`e0_dma_interference/`](e0_dma_interference/) | [`../results/e0_dma_interference/`](../results/e0_dma_interference/) |
| E1 | Does the real baseline hit a KV-capacity wall while compute remains available? | Complete | [`e1_capacity_bottleneck/`](e1_capacity_bottleneck/) | [`../results/e1_capacity_bottleneck/`](../results/e1_capacity_bottleneck/) |
| E2 | What capacity extension is feasible under measured compute and H2D service? | Mechanism complete | [`e2_kv_conveyor/`](e2_kv_conveyor/) | [`../results/e2_kv_conveyor/`](../results/e2_kv_conveyor/) |
| E3 | Which phase, lead, and group schedules are feasible? | Mechanism complete | [`e3_phase_scheduling/`](e3_phase_scheduling/) | [`../results/e3_phase_scheduling/`](../results/e3_phase_scheduling/) |
| E4 | Do injection priority and commit/cancel semantics prevent wasted resident KV? | Not implemented | Plan only | No evidence |
| E5 | Does conveyor preserve long-horizon recall unlike a sliding window? | Not implemented | Plan only | No evidence |
| E6 | Does the hardware-ratio model generalize across ticks, links, and models? | Not implemented | Plan only | No evidence |

All implemented experiments use the repository-wide parsing and Perfetto interface in
[`../observability/`](../observability/). A new experiment emits the shared `events.jsonl` schema or
adds one tested raw-artifact adapter there; it does not create an experiment-local trace stack.

The authoritative claim-to-experiment mapping is
[`../docs/EXPERIMENTS.md`](../docs/EXPERIMENTS.md). Do not create empty E4-E6 code
directories before implementations exist; the table is the roadmap and the filesystem represents
actual code.

## Naming rule

Use `e<number>_<purpose>` rather than generic containers such as `harness`, `scripts`, or
`calibration`. Inside an experiment, use concrete responsibility names such as `workers/`,
`instrumentation/`, and `analysis/`. Cross-experiment timed evidence belongs in the explicitly named
`observability/` package.
