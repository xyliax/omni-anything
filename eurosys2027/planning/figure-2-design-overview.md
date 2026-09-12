# Figure 2 — Simultaneous KV snapshots with capacity-gated prefetch

Status: redesigned preview for author feedback, 2026-09-08. Supersedes the fixed four-state/offload-stage draft. Not yet integrated into the manuscript. Prerequisite: [mechanism understanding audit](figure-design-understanding.md).

## Argument, classification and source mapping

Takeaway: a completed session releases GPU capacity that enables another session's prefetch while a third session still computes; restored KV can then wait ready for the next use.

This is an **author-selected 1 s / 4-slot mechanism illustration**, not an experimental trace, rescaled trace, simulator result or performance prediction. [Problem](../../docs/problem.md) owns period, release offsets and full-history semantics; [System](../../docs/system.md) owns state, eviction and recovery semantics; [Findings](../../docs/findings.md) owns current maturity. The source-linked [audit](figure-design-understanding.md) distinguishes the implemented push-triggered prefetch from the candidate earlier next-use scheduling drawn here. No permanent cache protection, universal host-coverage gate, global EDF queue or measured prefetch benefit is implied.

Use a temporal resource walkthrough, not a module-only architecture diagram. Every row shows all four sessions at the same real coordinate; continuous ribbons and release diamonds preserve timing between selected rows. A capacity gate provides one concrete non-ideal branch, avoiding four independent idealized handoffs.

## Executable model

The authoritative drawing implementation is `scripts/render-kv-figures.py`: `Session`, `EVENTS`, `snapshot`, `EXECUTION`, `PREFETCH`, `SAMPLES_MS`. These are illustration parameters, not project experimental facts.

Each session has separate logical block count, confirmed host frontier, valid GPU block set, in-flight H2D destination set, in-flight D2H destination set, activity and deferred-request flag. Display labels are derived from those dimensions; a single modulo-period four-state function is not used.

Assumptions:

- Four sessions S1–S4; T = 1000 ms; stable release offsets 0, 250, 500, 750 ms. Slots specify releases, not exclusive execution reservations.
- Initial histories have 8, 8, 8, 9 blocks. S4 is continuing its previous update; S1 is ready at release and starts computing later.
- No physical prefix sharing across sessions. Every block is an equal-sized illustrative unit.
- Idle eviction retains blocks `{0, 1, newest}` and removes the selected middle. Retention is an example cache outcome, not a pinning guarantee.
- The selected idle transitions occur after host completion. This successful example does not claim current eviction universally checks host coverage before choosing blocks. All retained fresh blocks are assumed valid/hashable; unfinished-tail destruction and recomputation are outside this example.
- Prefetch requires an idle session, a host-backed missing span, enough GPU capacity and the shared H2D lane. Destinations occupy capacity immediately, but become valid only at completion. Completed copies remain idle cache contents until execution, and are assumed to survive replacement in this example.
- One H2D transfer at a time; D2H is displayed separately and may overlap H2D. This is a schematic bidirectional feasibility assumption, not a measured link-throughput model. Transfers of differing sizes use authored illustrative windows; constant bandwidth is not claimed.

### Timing contract

| Session | Execution envelopes (ms) | Prefetch (ms) | New block / D2H window (ms) |
| --- | --- | --- | --- |
| S1 | 30–380; next 1030–1380 (clipped by plot) | 900–960; initial KV already ready | 140 / 160–210 |
| S2 | 280–620 | 160–220 | 420 / 450–490 |
| S3 | 530–850 | request deferred at 300; issue 380, complete 440 | 600 / 615–665 |
| S4 | previous −220–120; current 780–1120 | 650–710 | previous tail completes backing at 20; current new block at 900 / 915–965 |

Execution durations are 320–350 ms, all below half the period, and neighboring envelopes overlap. Envelopes may represent interleaved/batched engine work; do not interpret them as four independent kernels. No deadline marker is drawn.

Growth appends one logical and GPU-valid block. A later D2H issue creates a pending host destination; completion advances confirmed host coverage. There is no compulsory post-compute full-history offload window. Eviction is a point event when the session becomes idle; it releases selected GPU capacity without deleting host history.

### Capacity accounting and causal branch

GPU pool usage is the union of valid GPU content and allocated H2D destinations, summed across the four unshared histories. It includes idle retained blocks and ready cached content, even when cache ownership is reclaimable. It is neither request-owned allocation alone nor a reconstruction from the repository's residency sampler.

At 300 ms, existing pool use is 23 blocks; S3 needs 5 additional destinations, which exceeds the 25-block illustration pool. At 380 ms, S1 becomes idle and evicts 6; S3 then reserves 5, giving `23 − 6 + 5 = 22`. At 400 ms S2 computes while S3 copies. At 440 ms S3 becomes ready; at 500 ms its input is released; computation starts at 530 ms. Thus completion is distinct from release and use.

This is a conservative chosen schedule: the example does not reclaim other idle prefixes to admit S3 sooner. Capacity deferral is not claimed to be the only possible allocator decision or an optimal policy. The shared H2D lane serializes the shown restores, but no measured bandwidth guarantee is inferred.

## Snapshot and geometry contract

Canvas 720 × 908, 7 in wide; minimum 15 SVG units = 10.5 pt. Intended as a full-width tall design walkthrough, with final manuscript/caption fit still to be reviewed. Time is linear, `y = 108 + 0.55 × t_ms`, over 0–1160 ms. Snapshot cards have 53-unit height; irregular timestamps must never be evenly spaced.

| Time (ms) | S1 | S2 | S3 | S4 | GPU total, incl. H2D |
| --- | --- | --- | --- | --- | --- |
| 0 | Ready | Idle | Idle | Compute | 23 |
| 180 | Compute | Prefetch | Idle | Idle | 23 |
| 300 | Compute | Compute | Deferred | Idle | 23 |
| 400 | Idle | Compute | Prefetch | Idle | 22 |
| 500 | Idle | Compute | Ready | Idle | 23 |
| 620 | Idle | Idle | Compute | Idle | 18 |
| 750 | Idle | Idle | Compute | Ready | 24 |
| 920 | Prefetch | Idle | Idle | Compute | 25 |
| 1100 | Compute | Idle | Idle | Compute | 25 |

Session card origins x = 116, 232, 348, 464. At each time point, upper block row G shows GPU content; lower H shows host coverage. Block identities align within a card from oldest to newest. Logical growth lengthens both row outlines; empty GPU cells are evicted logical blocks, not lost context. Maximum illustrated history is 10 blocks.

- Blue solid blocks: valid GPU contents.
- Dotted blocks: confirmed host contents.
- Orange hatch on G: H2D destination, allocated but not ready.
- Orange hatch on H: D2H destination, not yet confirmed.
- Small plus above the latest block: newly appended KV awaiting host coverage.
- Compute uses a square and pale blue card; Ready uses a hollow square, meaning idle with restored KV; Prefetch uses an up arrow; Deferred has an orange outline; Idle uses a dot.
- Release uses a hollow diamond on the continuous ribbon, distinct from Ready. Phi in the heading is measured in ms.
- Pool bar is on a fixed 0–25 scale. The row below it identifies the shared link's source/destination session: up is H2D, down is D2H; dash means no H2D in flight.
- Bottom causal strip binds deferred request, capacity release and ready-to-use waiting to exact events in the main view.

## Reproduction and validation

```bash
python eurosys2027/scripts/render-kv-figures.py
```

Outputs: `eurosys2027/figures/figure2-design-overview.{svg,pdf,png}`. Python standard library builds SVG; `rsvg-convert` exports PDF/PNG; Pillow optionally exports grayscale PNG. Machine-readable row states are generated at `eurosys2027/build/kv-figure-review/snapshot-states.json` for inspection, not retained as experiment evidence.

Generator assertions check full valid history before execution, idle-only prefetch, host-backed restore spans, capacity deferral/acceptance, no overlapping H2D jobs, disjoint valid/in-flight destinations, pool capacity at every event, and sub-half-period execution. They also verify a ready-idle state and neighboring computation overlap. These check the drawing's internal consistency, not runtime implementation correctness.

Update this spec and the event model before touching geometry. Then regenerate both figures, compare color/grayscale previews, and run root `python -m pytest`, paper `make check`, and `git diff --check`. Changes to this schematic must not mutate engine, trace or results artifacts. Do not reinstate fixed 30 ms offload, constant host coverage, 2 s / 8 slots, release=compute, or uncounted prefetch reservations.

## Caption draft

Conveyor can reuse capacity released by an idle session to restore another session's KV while neighboring computation continues. Each time slice shows all four sessions' GPU (G) and host (H) blocks under an illustrative one-second release grid; computation lasts less than half a period and may overlap through batching or interleaving. S3's prefetch is initially deferred, becomes feasible when S1 evicts its middle blocks, and completes before S3's next execution; hatched GPU destinations count toward pool occupancy before becoming usable. Host backing advances independently with new KV, and the shared-link annotations distinguish H2D from D2H; this is a candidate mechanism schedule, not a measured trace or a guarantee that prefetched cache contents always survive until use.

## Review status

Rebuilt from the source-audited semantics and visually inspected in color and grayscale. The author is reviewing narrative density and visual composition. Formal prefetch benefit, behavior under replacement and high pressure, exact deployment scheduling, and final two-column placement are not established by this figure.
