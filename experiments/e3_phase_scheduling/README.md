# E3: Conveyor phase scheduling

E3 imports the E2 mechanism unchanged and varies only phase assignment and prefetch lead time. This
keeps implementation behavior, model facts, compute trace, KV pool, and transfer size fixed while
isolating the scheduling decision.

## Matrix

| Arm | Meaning |
| --- | --- |
| `resident_sync` | Full-resident E1 timing reference |
| `conveyor_random_seed*` | Fixed uncontrolled random phases |
| `conveyor_tdma` | Compute-constrained phase groups |

The default lead scan is 10, 25, 50, 80, and 120ms with five random seeds. Each lead is a separate
immutable run directory because lead time changes the staging/deadline contract.

```bash
.venv-vllm023/bin/python -m experiments.e3_phase_scheduling.run --plan
.venv-vllm023/bin/python -m experiments.e3_phase_scheduling.run --gpu 3

# Isolate TDMA group size at one lead value.
.venv-vllm023/bin/python -m experiments.e3_phase_scheduling.run \
  --gpu 3 --leads-ms 20 --group-sizes 4,5,6,7,8

.venv-vllm023/bin/python -m experiments.e3_phase_scheduling.aggregate --name <aggregate-id>
```

The main metrics are H2D queue p99, transfer and output deadline misses, peak staging sessions,
link busy fraction, and predicted time to the E1-sized capacity wall. The same mechanism-level
evidence boundary documented by E2 applies.

E3 keeps summaries rather than duplicating large deterministic transfer logs. The shared exporter
replays every arm from the manifest, E1 compute profile, and retained H2D samples:

```bash
python3 -m observability.export_perfetto <run-id>
```

The resulting run-local trace starts with the complete source E1 engine/service view and appends the
simulated compute batches, transfers, deadlines, and capacity markers for each E3 arm. See
[`../../observability/README.md`](../../observability/README.md).

The current result is narrow rather than monotonic: 10/25ms lead preserves a seven-tail peak for
group 7, while 50ms and above stages all eight tails and loses the capacity benefit. At 20ms lead,
groups 6 and 7 are valid and retain the seven-tail peak; `5+3` overloads measured compute. Random
phases miss about 97.6% of output deadlines at the median across five fixed seeds. See
`results/e3_phase_scheduling/aggregates/20260806_main/`.
