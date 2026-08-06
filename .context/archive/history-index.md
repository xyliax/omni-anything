# Historical project arc (tombstone index)

Sole history index for deleted StreamingRL-era materials (since 2026-07-11; re-purged 2026-07-26 after a resync restored deleted trees). Originals and their `.llm/` extracts are gone; this file only records what existed and the concept arc. It is **not** current project state.

## Project Arc

1. The earliest recovered SOW was a broad supernode training/inference optimization proposal for unified multimodal models: visual encoder, projector, LLM backbone, DiT, VAE, generation decoders, placement, routing, mixed parallelism, and memory management.
2. The April Yuanrong/openYuanrong pivot moved the work toward RL infra: `rollout -> reward/eval -> learner`, openYuanrong as substrate, public RL baselines, throughput/resource metrics, and candidate multimodal workloads.
3. The April 14 correction made the SOW RL-first: agentic multimodal rollout bottlenecks, async RL stability/efficiency, supernode runtime orchestration, earlier minimal RL loop, open-source output, and RL effect metrics.
4. Late-April discussion demoted fixed visual-generation RL as the main proof. Flow/DanceGRPO-style costs are relatively estimable; agentic RL has stronger scheduling value because tool calls, retries, trajectory length, and reward arrival vary.
5. Relax, veRL, HybridFlow, and vLLM-Omni define the related-work boundary. The project should not claim generic async RL, generic staleness handling, or generic stage-aware inference scheduling.
6. May materials introduced ModalPP, Omni RL Tile, and RL-safe scheduling. Their lasting role is the RL metadata constraint: group, policy version, old logprob, reward binding, artifact, staleness, and train eligibility.
7. June drafts reframed the systems story around streaming video / omni RL, bounded staleness, GRPO group atomicity, fixed GPU pools, and elastic rollout/training splits.
8. `2026-06-18-stream-context-manager-draft-v10` is the bridge to the current direction: the trainable object is a shared evolving stream context, not a single closed trajectory.
9. Current StreamContext-RL centers on event ledger, event-sealed slices, reward/version/freshness/group certification, admission/packing, and adapters to veRL, Relax, SGLang, and vLLM.
10. Didan's latest SOW feedback applies to a possible two-year SOW variant: fewer acceptance points tied to paper submissions, and performance modeling before adaptive splitting.

## Concept Status

| Concept | Role | Notes |
| --- | --- | --- |
| StreamContextTrace / context ledger | core | Represents rollout as events and state, so the system can decide wait, repair, refresh, drop, or train. |
| Event-sealed slice | core | Seals samples by event, reward, and version boundary instead of fixed windows. |
| Trainability certification | core | Checks reward validity, version validity, freshness, group completeness, and logprob/reward compatibility before trainer admission. |
| Admission / group packer | core | Keeps GRPO/PPO-style group and version constraints intact during batching. |
| veRL P0 | implementation boundary | First runnable trainer path. |
| Relax, SGLang, vLLM | P1 extension | Adapter and trace collector surfaces after the veRL path works. |
| Supernode / Ascend context | support | Deployment relevance and resource-orchestration motivation. |
| Async RL decoupling | support | Base system shape, not a novelty claim. |
| Staleness | support | One trainability certificate field and one planning signal. |
| Group completeness / GRPO atomicity | support | Constraint carried from Tile work into the current packer. |
| ModalPP / encoder virtual microbatch | optional | Useful only behind the certifier/packer boundary. |
| Omni RL Tile | candidate mechanism | Keep the metadata lesson; do not make tile planning the headline unless implementation includes it. |
| Elastic rollout/training scheduling | de-emphasized | Useful machinery, but not the main contribution. Tool/env/user wait cannot be fixed by adding GPU. |
| Generic full-chain training/inference optimization | historical | Too broad for the current RL project. |
| openYuanrong as sole substrate | historical | Origin context only unless revived explicitly. |
| Flow-GRPO / DanceGRPO as main workload | historical boundary | Useful negative control, too regular for the full control-plane story. |

## Feedback Notes

- 2026-04-06: add RL infra to the older unified multimodal proposal; keep long-term SOW general, but make short-term milestones concrete.
- 2026-04-14: title, stages, deliverables, and acceptance must read as Agentic multimodal RL, not training/inference/RL in parallel.
- Late April: fixed visual-generation RL is a weak primary workload; agentic multimodal RL is the stronger scheduling/control-plane case.
- May: avoid collisions with vLLM-Omni, Relax, and veRL; the remaining gap is RL-semantic scheduling and stream-context trainability.
- Mid June: elastic scheduling alone breaks when long rollout is blocked on tool/env/user wait; context state determines the useful action.
- 2026-06-28/29: current framing should stay SOTA-adjacent, executable, and RL-contribution-first, with a half-year closure and named adapters.
- 2026-06-29: for a two-year SOW, use fewer acceptance milestones and order performance modeling before adaptive splitting.

## Visual Notes

The latest temp chat images were not recoverable after restart, so their content is kept here:

- Didan SOW feedback: two-year SOW cadence should align with about five paper-submission milestones; performance modeling should precede adaptive split strategy.
- Omni RL Tile: smallest schedulable unit with trajectory, group, policy version, old logprob, reward binding, artifact, staleness, and train eligibility metadata.
- RL-safe heterogeneous scheduling: adaptive compute allocation must preserve version binding, staleness thresholds, random quotas, mix ratios, and correction weights.
- vLLM / veRL / Relax comparison: vLLM is inference-oriented, veRL is the RL trainer baseline, Relax covers async rollout/trainer and max-staleness; current claims must stay outside those generic surfaces.
- Thinking Machines interaction model: an interaction model stays with the user while a background model works asynchronously and writes back into shared context.

## Current Anchors

(Refreshed 2026-07-26; the old anchor table pointed at the deleted `docs/` tree and the v2.2 deck.)

| ID | Path | Use |
| --- | --- | --- |
| current-state | `README.md` | Single current-state entry; carries the 2026-07-26 route-pivot note (story = omni-anything / agent duplex, target jiuwenswarm). |
| answer-layer | `proposal/` | Per-RP dossiers, baselines, background line, data-request queue. |
| current-deck | `slides/2026-07-22-streaming-omni-rl-proposal-draft.pptx` | Working deck (13 pages; story rewrite pending per route pivot). |
| baseline-deck | `slides/2026-07-10-streaming-omni-rl-proposal.pptx` | Last pre-pivot formal proposal (RP numbering source). |
| interaction-models-reference | `context/references/thinking-machines-interaction-model.md` | Self-contained digest of the Thinking Machines interaction-models blog (renamed from `interaction-models.md`). |
| current-survey | `context/papers/Reinforcement Learning for Interactive Streaming Video Understanding- A Survey of Methods, Infrastructure, and Open Challenges/overview_cn.md` | Streaming video RL gap evidence. |

## Historical Sources

| ID | Original | Extract | Role |
| --- | --- | --- | --- |
| 2026-04-openyuanrong-rl-proposal | `2026-04-02-openyuanrong-rl-proposal.md` | same | Yuanrong RL pivot. |
| 2026-04-sow-rl-feedback | `2026-04-14-sow-rl-feedback.md` | same | RL-first SOW correction. |
| 2026-04-train-infer-sow | `2026-04-supernode-train-infer-sow.docx` | `.llm/2026-04-supernode-train-infer-sow/pages.md` | broad supernode baseline. |
| 2026-04-fullchain-sow-v1 | `2026-04-supernode-fullchain-sow-v1.docx` | `.llm/2026-04-supernode-fullchain-sow-v1/pages.md` | superseded full-chain SOW. |
| 2026-04-fullchain-sow-v3 | `2026-04-supernode-fullchain-sow-v3.docx` | `.llm/2026-04-supernode-fullchain-sow-v3/pages.md` | later full-chain SOW variant. |
| 2026-04-rl-training-sow-v1 | `2026-04-supernode-rl-training-sow-v1.docx` | `.llm/2026-04-supernode-rl-training-sow-v1/pages.md` | RL SOW iteration. |
| 2026-04-rl-training-sow-v2 | `2026-04-supernode-rl-training-sow-v2.docx` | `.llm/2026-04-supernode-rl-training-sow-v2/pages.md` | later RL SOW iteration. |
| 2026-04-visual-generation-rl-infra | `2026-04-28-visual-generation-rl-infra.pdf` | `.llm/2026-04-28-visual-generation-rl-infra/pages.md` | visual-generation RL boundary input. |
| 2026-04-three-slide-qa | `2026-04-29-three-slide-qa-draft.md` | same | multimodal and agentic RL bottleneck explanation. |
| 2026-04-relax-brief | `2026-04-30-relax-brief.pdf` | `.llm/2026-04-30-relax-brief/pages.md` | Relax boundary evidence. |
| 2026-05-refined-problem | `2026-05-refined-problem.docx` | `.llm/2026-05-refined-problem/pages.md` | deep dive on bubble, Relax boundary, and RL semantics. |
| 2026-05-discussion-summary | `2026-05-discussion-summary.txt` | same | long-tail and streaming video RL fit. |
| 2026-05-modalpp | `2026-05-modalpp.pptx` | `.llm/2026-05-modalpp/slides.md` | encoder-side modal workload balancing. |
| 2026-05-rl-supplement | `2026-05-rl-supplement.pptx` | `.llm/2026-05-rl-supplement/slides.md` | bridge from ModalPP to agentic RL long-tail. |
| 2026-05-rl-aware-tiles | `2026-05-agentic-omni-rl-aware-tiles.pptx` | `.llm/2026-05-agentic-omni-rl-aware-tiles/slides.md` | RL-aware tile metadata. |
| 2026-05-chain-scheduling | `2026-05-rl-chain-scheduling-slides.pptx` | `.llm/2026-05-rl-chain-scheduling-slides/slides.md` | early RL chain scheduling draft. |
| 2026-05-pipeline-v2 | `2026-05-multimodal-agentic-rl-pipeline-v2.pptx` | `.llm/2026-05-multimodal-agentic-rl-pipeline-v2/slides.md` | tile-level workload-aware pipeline draft. |
| 2026-05-pipeline-acceleration | `2026-05-multimodal-agentic-rl-pipeline-acceleration.pptx` | `.llm/2026-05-multimodal-agentic-rl-pipeline-acceleration/slides.md` | simplified pipeline acceleration deck. |
| 2026-06-draft-v4-md | `2026-06-10-streaming-video-rl-draft-v4.md` | same | streaming video RL acceleration draft. |
| 2026-06-draft-v4-ppt | `2026-06-10-streaming-video-rl-draft-v4.pptx` | `.llm/2026-06-10-streaming-video-rl-draft-v4/slides.md` | v4 slide deck. |
| 2026-06-draft-v7 | `2026-06-16-streaming-video-rl-draft-v7.pptx` | `.llm/2026-06-16-streaming-video-rl-draft-v7/slides.md` | fixed pool, bounded staleness, GRPO atomicity. |
| 2026-06-draft-v8 | `2026-06-17-streaming-omni-rl-draft-v8.pptx` | `.llm/2026-06-17-streaming-omni-rl-draft-v8/slides.md` | stream omni RL acceleration and staleness feedback. |
| 2026-06-draft-v10 | `2026-06-18-stream-context-manager-draft-v10.pptx` | `.llm/2026-06-18-stream-context-manager-draft-v10/slides.md` | bridge to stream context manager. |

## Deleted 2026-07-26 (directory cleanup after the route pivot)

Tombstones for files deleted outside `context/archive/` during the 2026-07-26 cleanup; recovery via OneDrive version history at their original paths.

| Original path | Role / why deleted |
| --- | --- |
| `docs/sow.md` | Six-month StreamContext-RL SOW (pre-07 era); superseded by the `proposal/` answer layer. |
| `docs/architecture.md` | StreamContext-RL architecture and module definitions; same era, superseded. |
| `docs/p0-plan.md` | StreamContext-RL P0 execution plan; same era, superseded. |
| `docs/streaming_rl_discussion_brief.md` | Pre-pivot discussion-sync brief (streaming RL framing); marked historical on 2026-07-26, then deleted with the rest of `docs/`. |
| `slides/streaming_omni_rl_v2_toolchain_v2.2.pptx` | 2026-06-29 toolchain deck; superseded by the 07-10 proposal line. |
| `slides/最新slides.pptx` | Pre-rename duplicate of `2026-07-10-streaming-omni-rl-proposal.pptx` (only one RP1 title差异, earlier wording); resurfaced via OneDrive resync. |
| `slides/2026-07-14-streaming-omni-rl-proposal-draft.pptx` | Intermediate draft between the 07-10 formal deck and the 07-22 working deck. |
| `incremental_prefill_analysis.md` (repo root) | Residual copy; moved to `context/references/incremental-prefill-analysis.md` on 2026-07-11, root copy resurfaced via resync. |
| `README-Frank的MacBook Pro.md` (repo root) | OneDrive conflict copy of the 2026-07-12 discovery-phase README; superseded twice over. |
| `context/references/streaming-duplex-rollout-scheduling-Frank的MacBook Pro.md` | OneDrive conflict copy, byte-identical to `streaming-duplex-rollout-scheduling.md`. |

Renames/moves the same day (no content loss): `slides/2026-07-14-deck-copy-draft.md` → `slides/2026-07-22-deck-copy-draft.md` (file already self-titled "2026-07-22 版"); `context/references/*.html` (duplex-coding-agent-explainer, sglang-streaming-session-pr19171) → `context/references/media/`.
