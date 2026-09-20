# Figure 1 — Periodic KV pressure and restoration timing (v4, hand-drawn)

Status: v4 design contract, 2026-09-20. Supersedes the v3 matplotlib rendering after two author decisions: (1) panel (a) switches from irregular workload phases to **aligned rounds** — the execution behaviour of existing periodic serving — so the shared idle window becomes directly visible; (2) production switches to **hand-drawn Draw.io** by the author, with this spec as the drawing contract. The v3 matplotlib previews in `figures/` are frozen layout references until the `.drawio` version lands; the generator script has been retired. Read [mechanism audit](figure-design-understanding.md) before changing semantics.

## Argument and sources

Takeaway: under multi-session periodic load served in synchronized rounds, aggregate KV demand reaches GPU KV capacity while a shared idle window recurs every period; release times are known in advance, so restoration can move off the critical path, and the move repeats identically every period.

This is an **author-selected mechanism illustration**, not a measured result, calibrated simulation or speedup prediction. Semantic owners are [Problem](../../docs/problem.md) and [System](../../docs/system.md); implementation and evidence maturity remain in [Findings](../../docs/findings.md). The drawing depicts the candidate next-use-aware schedule, not a claim that the current implementation already schedules restoration before release. Do not infer implementation status from this figure. All counts and times are drawing parameters. The measured counterpart of panel (a) is a separate figure pending Q1 (see PAPER.md figure plan, 图 2 · 张力测量).

### Why aligned phases are the honest baseline here

- Alignment is attributed to the **serving side, not the workload**: round-based periodic serving executes all sessions' updates in synchronized rounds because alignment maximizes batch efficiency — the throughput-friendly default of existing systems, not an artifact constructed for this figure. The caption must attribute alignment to the baseline scheduler.
- Under the full-residency reference policy, the aggregate KV curve is **phase-invariant** (residency does not depend on when sessions compute), so alignment does not manufacture the memory wall; it only makes the compute-side idle window legible.
- Aligning scattered arrivals costs up to one period of alignment wait per session's first submission; that cost is tracked by the measurement semantics (owner: experiments.md) and must not be portrayed as free — one caption clause, no pixels.
- The uniform staggered grid remains this paper's mechanism and appears only in the design-overview figure; the aligned→staggered contrast across the two figures encodes the intervention.

## Layout contract

Full width 7.0 × 2.6 in, two panels side by side; sans-serif (Arial/Helvetica); annotations 8 pt, axis/lane/panel labels 9 pt. In-figure text budget: besides ticks, axis/lane labels and the shared legend, at most six short annotations (≤3 words each; suggested: T, shared idle, capacity, exceeds, evict, ready) plus two circled event numbers; all sentences live in the caption.

**Numeric discipline.** The figure displays **no instance-specific magnitudes**: the time axis is labeled in symbolic periods (0, T, 2T, 3T), the capacity line carries the word "capacity" and no value, and the aggregate strip has no numeric ticks. Block counts and millisecond values in the tables below are **internal drawing coordinates** that fix proportions only — they echo one current model configuration and must never be rendered as text. Real magnitudes belong to the measured figure (pending Q1) with evidence binding.

**Panel (a), left — aligned rounds, 4 sessions × 3 periods, axis 0–3T:**

| Parameter | Internal coordinate (proportion only) |
| --- | --- |
| Period T / rounds | 1000 units; releases aligned for all sessions at 0 / T / 2T (diamonds vertically aligned) |
| Compute burst | one synchronized batched burst per round, ≈0.35T from round start, drawn per lane; burst length is schematic (batching) |
| Shared idle tail | ≈0.65T per round, common to all lanes — the directly visible multi-session idle window; one "shared idle" annotation in the first period |
| Retained KV at t=0 | 4, 4, 5, 5 blocks (band height per lane; heights are relative, no numerals rendered) |
| Growth | +1 block per session at each burst end; bands step up together |
| Aggregate subplot | Σ retained KV staircase vs dashed capacity line (unlabeled value); staircase starts ≈0.7× capacity and crosses at the second-round growth or later — never in the first period, so growth is visible before the wall; crossing marked "exceeds" |

**Panel (b), right — restoration timing, 1 session × 2 periods, axis 0–2T:**

| Parameter | Internal coordinate (proportion only) |
| --- | --- |
| Releases | T/2 and 3T/2 (diamonds) |
| Rows | Reactive: restore ≈0.06T starts at the release (circled 1), compute starts late. Pilarius: the same restore volume ends ≈0.1T before the release, resident-ready wait (circled 2), compute starts at the release; post-compute drop labeled "evict" |
| History / idle retention | 9 blocks / 3 blocks; H2D destinations count toward residency from restore start |
| Both rows span two full periods | the per-period repetition is what licenses "cyclic" |

## Visual vocabulary and Draw.io style tokens

Deep blue `#28769B` = compute on GPU KV; pale blue `#EAF2F7` = resident idle KV (band height = blocks); orange `#B87519` diagonal hatch on `#FFF0D9` = transfer in flight; ink `#263642` = curves/text; gray `#9CA9B2` = axes and secondary marks; hollow diamond = release; dashed orange line = KV capacity; circled numbers = caption-narrated events. White background, no shadows, no rounded decoration, stroke ≈1 pt. Grayscale legibility comes from hatching and value contrast, not hue.

## Production and edit protocol

- **Source of truth: `eurosys2027/figures/figure1-motivated-example.drawio`** (author hand-draws; one page per figure). Export vector PDF (crop) for LaTeX plus PNG for review, same basenames, replacing the frozen v3 previews.
- Agent-assist loop: the author draws; the agent may inspect/patch the `.drawio` XML (alignment, styles, batch edits), render previews, and audit against this spec's parameter tables, text budget and semantic owners. Group and name element clusters in Draw.io so XML patches preserve layout.
- The matplotlib generator (`scripts/render-kv-figures.py`) is retired with v4; its event-model constants survive in the parameter tables above and in the frozen v3 previews. Quantitative proportions (compute ≪ T; per-period KV growth) were calibrated against diagnostic findings at v2/v3 time; keep those proportions unless owners change.
- Change this spec first, then the drawing; captions and semantics must not drift from owners. No measured axes or performance claims without the evidence-owner transaction.

## Caption draft

Multi-session periodic serving exhausts GPU KV capacity while a shared idle window recurs every round, and known release times let restoration move off the critical path. (a) Existing periodic serving executes all sessions in synchronized rounds — alignment maximizes batch efficiency at the cost of an up-to-one-period alignment wait on first submission; each round's bounded burst ends well before the next release, leaving a shared idle tail, while retained KV (band height) grows every round, so aggregate demand crosses the capacity line although compute is idle most of each period. (b) One session across two periods under the same restore volume: (1) reactive restoration places the restore on the critical path after each release and pays that delay every period; (2) restoring against the known next release completes early, so computation starts at the release — at the cost of occupying GPU capacity earlier — and the idle-time eviction/restore cycle repeats identically each period. Axes are in periods and heights are relative: the illustration is authored and schematic, and carries no measured magnitudes.

## Review gate

Open items before manuscript use: **(v)** the claim that the round-based baseline (Metronome-style serving) aligns session updates by design must be verified against the original source before the caption or body cites it — currently an author-recalled property, not a checked citation; **(m)** the measured counterpart of panel (a) remains pending Q1 and this schematic must not be cited as evidence for the capacity-bound claim; **(p)** final two-column placement and caption fit at print size. The uniform phase grid, shared-link budgeting and capacity-gated prefetch belong to the design-overview figure and must not be inferred from this one.
