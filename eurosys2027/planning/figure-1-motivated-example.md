# Figure 1 — Capacity pressure and recovery timing

Status: redesigned preview for author feedback, 2026-09-08. Supersedes the previous four-lane residency sketch; not integrated into the manuscript. Read [mechanism audit](figure-design-understanding.md) before changing semantics.

## Argument and sources

Takeaway: growing history makes full GPU residency expensive, while predictable next use provides an opportunity to move restoration ahead of computation.

This is an **author-selected mechanism illustration**, not a measured result, calibrated simulation or speedup prediction. Semantic owners are [Problem](../../docs/problem.md) and [System](../../docs/system.md); implementation and evidence maturity remain in [Findings](../../docs/findings.md). The drawing depicts the candidate next-use-aware schedule, not a claim that the current push-triggered implementation already implements pre-release scheduling. The trace audit linked from the mechanism audit only supplies qualitative constraints, not plotted timestamps or block counts.

The paradigm is a running resource example followed by three policy alternatives. It intentionally differs from Figure 2: this figure explains the motivation and local timing tradeoff; Figure 2 explains the multi-session causal mechanism. No resource advantage is attributed exclusively to release offsets by comparing against an artificially unpipelined baseline.

## Layout and reproduction contract

Canvas: 720 × 620 viewBox, physical width 7 in. Arial, minimum 15 SVG units (10.5 pt at intended width). Two panels:

1. Top: four histories grow from an earlier illustrative update to a later update. Their aggregate full-residency demands are compared with a finite GPU KV pool. All numbers are drawing parameters, not empirical findings.
2. Bottom: full residency, partial eviction with demand reload, and partial eviction with prefetch. Each row shows the same single-session GPU/Host block map during idle and a local timing strip around its next input release. The strip uses a common linear axis; a hollow diamond identifies release separately from execution.

Executable parameters are in `scripts/render-kv-figures.py::intro`:

| Parameter | Illustrative value / meaning |
| --- | --- |
| Earlier histories | 4, 5, 4, 5 equal-sized logical blocks |
| Later histories | 8, 8, 8, 9 blocks; matches Figure 2's initial logical histories |
| GPU KV pool | 25 drawing blocks |
| Single-session comparison | 9 historical blocks, all host-backed |
| Idle retention in partial-eviction alternatives | oldest 2 plus newest 1; 6 absent GPU blocks |
| Local time range | −250 to +500 ms relative to release |
| Input preparation | common +30 ms before possible execution/restore |
| Demand reload | +30 to +90 ms |
| Prefetch | −100 to −40 ms; destinations allocated from issue |
| Computation | 350 ms; starts at +30 with ready KV, +90 after demand reload |

The local comparison isolates timing with a fixed historical working set: new-tail growth and incremental backing are shown in Figure 2. Thick pale strips show full historical GPU footprint, including time waiting ready; the thin pale strip shows partial idle retention. For partial eviction, residency drops immediately at the illustrated idle transition after execution, without a fabricated mandatory full-history D2H stage. Full residency retains KV throughout. Computation is a session execution envelope, not an exclusive GPU kernel. The demand delay is a constructed timing relation, not a measured latency benefit.

The upper overflow area is pale orange without transfer hatching; it denotes demand beyond capacity, not successful allocation or H2D traffic. The top panel is a resource-demand cartoon, not an actual OOM execution trace. Host copies are held equal in the policy comparison to isolate GPU retention and restore timing; they are not required by every full-residency implementation.

## Visual vocabulary

- Solid blue blocks: valid GPU KV; outlined empty blocks: absent GPU content.
- Dotted blocks: confirmed host copy; G/H mean GPU/Host.
- Solid blue timeline band: compute; pale band: resident historical KV while idle.
- Orange diagonal hatch: H2D restore; bracket under demand transfer: recovery waiting on the update path.
- Hollow diamond: input release, never deadline. The prefetch-to-compute gap explicitly shows early residency.

No long mechanism paragraphs go inside the image. Detailed scope, source and current-implementation distinctions belong in this spec and the caption.

## Reproduction and edit protocol

From the repository root:

```bash
python eurosys2027/scripts/render-kv-figures.py
```

Python standard library builds editable SVG. `rsvg-convert` exports vector PDF and PNG; Pillow optionally creates grayscale reviews in `eurosys2027/build/kv-figure-review/`. Outputs are `eurosys2027/figures/figure1-motivated-example.{svg,pdf,png}`. No experiment artifact is read or changed.

Change the argument/parameters here first, then `intro()` and the shared palette/helpers, then regenerate. Manual SVG edits are overwritten. If changing the later-history example or pool capacity, synchronize Figure 2's initial state and its spec; the detailed local timing comparison can remain independent of Figure 2's event sequence. Do not add measured axes or performance claims without the evidence-owner transaction.

## Caption draft

Growing session history creates a tradeoff between GPU KV capacity and restoration waiting, while predictable next use provides an opportunity for earlier recovery. The upper panel shows illustrative full-residency demand outgrowing a finite pool; the lower panel holds one session's history fixed and compares retaining it, restoring missing blocks on demand, and prefetching them before use. G and H denote GPU and host copies; pale time bands show residency, solid blue denotes execution, and hatching denotes H2D restoration. Earlier restoration removes the depicted on-demand wait but occupies GPU capacity earlier; all counts and times are schematic, not performance measurements.

## Review gate

Generator/export and visual inspection completed; final argument/composition await author feedback. The local comparison is not a complete multi-session evaluation. Intended insertion is full two-column width; recheck text and caption fit during manuscript integration. Figure 2 carries release offsets, shared transfers, growth, backing lag and capacity deferral, so those mechanisms should not be inferred from this local strip alone.
