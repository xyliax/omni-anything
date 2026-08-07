# Current findings

This file is the shortest authoritative statement of what the repository currently supports. Raw
run data and generated artifacts are indexed in [`../results/README.md`](../results/README.md); the
longer design and execution record is in
[`PAPER-EXPERIMENTS.md`](PAPER-EXPERIMENTS.md).

## Evidence levels

| Experiment | Evidence level | What it can support |
| --- | --- | --- |
| E0 | Real CUDA microbenchmark | H2D/decode interference on this RTX 3090 |
| E1 | End-to-end Qwen2.5-Omni/vLLM/Metronome run | Baseline capacity failure and engine timeline |
| E2 | Trace-driven CUDA mechanism prototype | Transfer feasibility and capacity accounting, not active-block migration |
| E3 | Trace-driven CUDA mechanism prototype | Phase/lead/group scheduling tradeoffs, not end-to-end serving |

E2 and E3 use real E1 compute timings and fresh pinned-H2D measurements on the same GPU, but they
do not change vLLM's active KV block ownership. Claims below deliberately preserve that boundary.

## E0: DMA interference

- The RTX 3090 sustains `12.298 GB/s` unloaded pinned H2D bandwidth in the retained calibration.
- Under the tested decode loads, the maximum slowdown factor for utilization `r <= 0.75` is
  `kappa = 1.0668`, below the experiment's 1.15 stop threshold.
- This supports continuing the mechanism investigation. It does not prove that arbitrary copy
  schedules are harmless.

Evidence: `results/e0_dma_interference/runs/20260804_initial/`.

## E1: Real baseline capacity failure

Configuration: Qwen2.5-Omni-7B revision `ae9e169...`, vLLM 0.23.0, RTX 3090, eight sessions,
2-second period, 600-second duration, MML 32768, parallel ingest, full tracing.

- vLLM reports a 73,728-token (`3.94 GiB`) GPU KV pool.
- The run first loses a scheduler lane at about 216 seconds as the pool reaches capacity; later
  lanes disappear in a capacity cascade while the run continues.
- Client cadence is misleading after failure: delivery remains 100%, cadence miss remains 0%, and
  p99 settles near the worker's `1603 ms` wait cap. Scheduler and request traces are required to
  distinguish useful fresh service from capped empty/stale responses.
- The new scheduler trace contains 10,015 engine steps. Its Perfetto export contains 66,199 events
  and 53,894 non-empty engine slices.
- Full-tick compute medians remain close to the earlier calibration: batch 8 is `947.8 ms`; batch 7
  is `1059.8 ms`; batch 1, derived from 34 measured decode steps, is `662.6 ms`.
- Uniform one-session-at-a-time rotation is not compute-schedulable: eight batch-1 bursts require
  over 5 seconds per 2-second period. This directly supersedes the old optimistic “average batch
  about 3” forecast.

Evidence:
`results/e1_capacity_bottleneck/runs/20260806T210551.398631Z_e1_paringest_trace_n8_p2000_mml32768_seed0_3139eab_formal-rerun/`.

## E2: Conveyor mechanism result

Configuration: the E1 compute profile above, eight sessions, 78 tokens/session/tick, 4,096-token
host tail, 57,344 KV bytes/token, 73,728-token GPU pool, a `7+1` TDMA grouping, and 20 ms lead.

- Five independent fresh H2D calibrations measure `12.289–12.298 GB/s` (median `12.294 GB/s`) for
  one 234,881,024-byte tail.
- All five mechanism simulations have zero H2D deadline misses and zero output deadline misses.
- The compute-constrained `7+1` schedule needs about 1.72 seconds of measured GPU service per
  2-second period, compared with about 0.95 seconds for the synchronized resident baseline.
- Peak staging falls only from eight tails to seven. The modeled capacity wall therefore moves
  from 236 seconds to 248 seconds: `1.05085x`, or about `+5.1%`, in all five repetitions.
- The result rejects the earlier `2x` prediction for this E1 model/framework. Link bandwidth is not
  the limiting resource; the cost of breaking a large decode batch is.

Aggregate: `results/e2_kv_conveyor/aggregates/20260806_main/`.

## E3: Phase scheduling tradeoffs

- With group size 7, lead 10 and 25 ms preserve the seven-tail staging peak and have zero deadline
  misses. Lead 50, 80, and 120 ms also meet deadlines but prefetch too early: eight tails overlap,
  so the capacity extension disappears.
- At 20 ms lead, group sizes 6 and 7 are valid and peak at seven staged tails. Group size 8 is
  valid but stages all eight and gains no capacity.
- The measured `5+3` split is compute-overloaded (`compute busy fraction > 1`) and produces about
  95.5% output deadline misses. Group 4 meets output deadlines in this finite run but stages all
  eight tails, so it offers no capacity benefit.
- Five uncontrolled random-phase seeds have median output miss rate about 97.6% and stage all eight
  tails. Random desynchronization is therefore not a substitute for a compute-aware phase plan.
- The useful region is narrow: prefetch must be late enough to avoid simultaneous staging, while
  phase groups must remain large enough to retain batched compute efficiency.

Aggregate: `results/e3_phase_scheduling/aggregates/20260806_main/`.

## Current conclusion

E1 confirms a real resident-KV capacity problem and unused wall-clock compute time. E0 confirms
that the PCIe copy engine is fast enough to investigate. E2/E3 then show that this does not imply a
large conveyor gain: for the retained Qwen2.5-Omni/RTX-3090 point, compute batching limits the
mechanism to an approximately 5% modeled capacity extension under a narrow schedule.

The next scientifically valid step is an end-to-end worker that changes active KV block ownership
and measures H2D, D2H writeback, attention correctness, and serving deadlines together. Until that
exists, E2/E3 must remain labeled mechanism-level results.
