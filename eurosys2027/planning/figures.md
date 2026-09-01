# Figure Plan

| Figure | Argument carried | Required source | Status |
| --- | --- | --- | --- |
| Figure 1: motivated example | Show long-lived sessions, growing KV, capacity-before-compute, and the next-use opportunity in one view | Problem owner + a formal motivating point | Not started |
| Figure 2: system overview | Show release-offset timing, the complete one-session cycle, idle eviction, independent GPU/host state, restore/prefetch, and fallback | System owner + `planning/figure-2-evidence-map.md` | Redesigned and integrated; evidence, manuscript-scale, and grayscale reviews passed |
| Figure 3: resource frontier | Separate capacity, compute and restore-bandwidth regimes | Calibrated primitives + model | Not started |
| Figure 4: main result | Answer the schedulable-concurrency question | Formal matched runs | Blocked on formal evidence |
| Figure 5: latency cost | Decompose the critical path and tails | Formal traces | Blocked on metric freeze |
| Figure 6: ablation/generalization | Attribute benefit and validate model boundaries | Formal ablations + extra profile | Blocked on experiment plan |

## Figure Quality Gate

- [ ] Every figure has a one-sentence takeaway that can become its caption lead.
- [ ] Axes state units, evidence class and configuration domain.
- [ ] Error bars or uncertainty are shown where applicable.
- [ ] Legends remain distinguishable in grayscale.
- [ ] Text remains at least 10pt in the final two-column layout.
- [ ] No figure contains identifying metadata, local paths or non-anonymous URLs.
