# Figure 2 — Design overview: continuous swimlanes with capacity-gated prefetch (v4, hand-drawn)

Status: v4 design contract, 2026-09-20. Supersedes the v3 matplotlib rendering after two author decisions: (1) the pool subplot **reintroduces the aligned-phase comparison line, renamed from "hypothetical" to the baseline it now literally is** — Figure 1's aligned-rounds world — closing the visual loop between the two figures; (2) production switches to **hand-drawn Draw.io** by the author, with this spec as the drawing contract. The v3 matplotlib previews in `figures/` are frozen layout references until the `.drawio` version lands; the generator script has been retired. Prerequisite: [mechanism understanding audit](figure-design-understanding.md).

## Argument, classification and source mapping

Takeaway: three mechanisms cooperate — a uniform phase grid spreads per-session peaks, idle-tail eviction frees capacity with a depth bounded by the per-window link budget, and deadline-aware prefetch restores KV before the next release. The capacity-gated causal chain (S3 deferred → S1 evicts → S3 prefetches → ready before release) is carried by circled numbers 1–4 and narrated in the caption. Against the aligned-rounds baseline of Figure 1, the staggered grid holds the pool peak under capacity where alignment would exceed it.

This is an **author-selected four-slot mechanism illustration over a symbolic period T**, not an experimental trace, rescaled trace, simulator result or performance prediction. [Problem](../../docs/problem.md) owns period, release offsets and full-history semantics; [System](../../docs/system.md) owns state, eviction and recovery semantics; [Findings](../../docs/findings.md) owns current maturity. The source-linked [audit](figure-design-understanding.md) distinguishes the implemented push-triggered prefetch from the candidate earlier next-use scheduling drawn here. Do not infer implementation status from this figure. No permanent cache protection, universal host-coverage gate, global EDF queue or measured prefetch benefit is implied.

## Event model (internal drawing coordinates)

**Numeric discipline.** All values in this section are **internal drawing coordinates** that fix proportions only (T = 1000 units); they echo one current model configuration and must never be rendered as figure text. The displayed axis is labeled in symbolic periods (0, T/4, T/2, 3T/4, T), the capacity line carries the word "capacity" and no value, the pool subplot has no numeric ticks, and block counts appear only as band heights. Real magnitudes belong to measured figures with evidence binding.

Assumptions (unchanged since the audited event model): four sessions, offsets φ = 0 / T/4 / T/2 / 3T/4 (releases, not exclusive execution reservations); initial histories 8, 8, 8, 9 blocks; S4's previous update straddles t = 0; no cross-session sharing; idle eviction retains `{0, 1, newest}` as an example cache outcome after host backing completes; prefetch needs an idle session, host-backed span, pool capacity and the shared H2D lane, with destinations occupying capacity from issue; one H2D at a time, D2H may overlap; authored 50–60-unit windows, no bandwidth model claimed.

### Timing contract

| Session | Execution envelopes (units, T=1000) | Prefetch (units) | Grow / D2H window (units) |
| --- | --- | --- | --- |
| S1 | 30–380; 1030–1380 (clipped) | 900–960 | 140 / 160–210 |
| S2 | 280–620 | 160–220 | 420 / 450–490 |
| S3 | 530–850 | deferred 300; issue 380, complete 440 | 600 / 615–665 |
| S4 | −220–120; 780–1120 | 650–710 | 900 / 915–965; previous tail backs by 20 |

Causal chain: at 300 ms pool use is 23 and S3 needs 5 > 25 − 23 (deferred); at 380 ms S1 goes idle and evicts 6, S3 reserves 5 (23 − 6 + 5 = 22); S3 completes at 440, its input releases at 500, compute starts at 530. Completion, release and use remain distinct.

Pool reference values (blocks, incl. H2D destinations): 23 at 0/180/300/500 ms, 22 at 400, 18 at 620, 24 at 750, 25 at 920/1100.

## Layout contract

Full width 7.0 × 3.2 in; sans-serif; annotations 8 pt, axis/lane labels 9 pt; three stacked regions share one axis spanning 0–1.16T with light dashed verticals at the four phases (labeled φ1–φ4 once on top); axis ticks at 0, T/4, T/2, 3T/4, T. In-figure text budget: besides ticks, lane labels (S1–S4, H2D, D2H, Pool) and the legend, at most two short labels ("capacity", "aligned"), the φ labels, small + marks at KV growth, and circled numbers 1–4; all sentences live in the caption. No numeric magnitudes are rendered anywhere (see numeric discipline above).

- **Session lanes** (top): band height = GPU-resident blocks (0–10; valid + allocated H2D destinations), deep blue while computing, pale while idle, hatched for in-flight destinations; evictions are step-downs; diamonds at releases; each circled number gets a small anchor dot at its exact event coordinate (1 at S3's deferred request, 300 ms; 2 at S1's eviction step, 380 ms; 3 at S3's prefetch window; 4 at S3's ready-before-release window).
- **Pool subplot** (~0.6 in): occupancy staircase summed from the lanes vs the dashed capacity line (word "capacity", no value; no numeric y ticks). A light dashed staircase adds the **aligned-rounds comparison**: the same eviction machinery with all phases aligned — its peak clearly exceeds the capacity line during the shared burst-and-restore window, with a deep valley during the shared idle; labeled "aligned" (light gray, visually subordinate). This isolates the phase mechanism (same eviction, different phases) and is the schematic counterpart of the GPU-space dual argument (owner: problem.md resource frontier; ablation pending Q4). Draw the actual curve slightly below the capacity line where they coincide so both stay visible.
- **Link subplot**: two thin H2D/D2H tracks with session-labeled hatched windows; H2D windows are serialized and the real gaps between them are kept.
- No block-level inset; eviction-content semantics (keep prefix + newest, host retains all blocks) live in the caption and Design text.

## Visual vocabulary and Draw.io style tokens

Deep blue `#28769B` = compute; pale blue `#EAF2F7` = resident idle KV; orange `#B87519` diagonal hatch on `#FFF0D9` = transfer in flight; ink `#263642` = curves/text; gray `#9CA9B2` = axes, phase verticals and the aligned comparison line; hollow diamond = release; + = newly appended KV; circled numbers = caption-narrated events. White background, no shadows, stroke ≈1 pt; grayscale legibility from hatching and value contrast.

## Production and edit protocol

- **Source of truth: `eurosys2027/figures/figure2-design-overview.drawio`** (author hand-draws). Export vector PDF (crop) for LaTeX plus PNG for review, same basenames, replacing the frozen v3 previews.
- Agent-assist loop: the author draws; the agent may inspect/patch the `.drawio` XML, render previews, and audit against this spec's event model, text budget and semantic owners. Group and name element clusters so XML patches preserve layout.
- The matplotlib generator is retired with v4; the timing contract and pool reference values above are the drawing coordinates. Do not reinstate fixed 30 ms offload, constant host coverage, 2 s / 8 slots, release=compute, uncounted prefetch reservations, the snapshot-card layout, or slide-style sentence annotations.
- Change this spec and the event model before the drawing; no measured axes or performance claims without the evidence-owner transaction.

## Caption draft

Pilarius spreads sessions over a uniform release grid (φ1–φ4, diamonds), evicts idle KV tails, and restores them before the next release. Each lane shows one session's GPU-resident KV blocks over time; hatched spans are in-flight transfers whose destination blocks already count toward pool occupancy, and + marks newly appended KV. (1) S3's prefetch is deferred while the pool cannot hold its missing span; (2) S1's idle transition evicts its mid-history — the prefix and newest blocks stay resident and the host retains every block; (3) the freed capacity admits S3's prefetch on the shared H2D link, whose serialized windows bound how deeply a session may evict per period; (4) S3's history is fully resident before its release, so computation starts on time while S2 computes throughout. The pool subplot sums the lanes against capacity; the light dashed staircase shows the same eviction machinery under the aligned rounds of Figure 1, whose peak exceeds capacity where the staggered grid stays below it (schematic; phase ablation pending). Axes are in periods and heights are relative: the schedule is an authored mechanism illustration carrying no measured magnitudes, and it does not guarantee that prefetched contents always survive until use.

## Review gate

Open items before manuscript use: the aligned-comparison staircase is a schematic counterfactual of the drawn policy — its valley depth is a free drawing choice, its peak must exceed capacity, and the corresponding ablation (Q4) has no evidence yet; the Metronome aligned-rounds citation is verified under Figure 1's review gate; final two-column placement and caption fit at print size. Formal prefetch benefit, behavior under replacement and high pressure, and exact deployment scheduling are not established by this figure.
