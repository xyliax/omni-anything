# Paper Contract

本文件在写 polished prose 前冻结。当前所有内容均为 provisional，不是项目事实或已接受 claim。

## Positioning

| Field | Current value | Freeze condition |
| --- | --- | --- |
| Target venue | EuroSys 2027 | Official CFP rechecked before submission |
| Primary paper type | Candidate: New Problem/Setting | Closest-work matrix completed |
| Secondary contribution | Candidate: systems technique | Mechanism ablations and novelty audit completed |
| Working title | Next-Use-Aware KV Cache Multiplexing for Periodic Interactive Model Serving | Figure 1 and decisive experiment agree with title |

## One-Sentence Story

> Provisional: commit each periodic session's next release time on an absolute grid and drive KV eviction, restore and prefetch against it, so the next use of a session's KV is a scheduled deadline rather than a predicted event.

Rewrite this sentence only after checking it against `docs/problem.md`, `docs/system.md`, `docs/PAPER.md` and the closest prior work.

## Main Claim

> TBD. It must state the workload/configuration domain, the resource regime, the schedulability outcome, the no-context-truncation constraint, and the relevant latency/restore condition.

## Decisive Experiment

> TBD. It must be a matched baseline-versus-Conveyor experiment that can falsify the main claim, not a collection of mechanism microbenchmarks.

## Kill Condition

> TBD before formal runs. State the observation that would force the paper to narrow or pivot its main claim.

## Contributions

1. `<problem or setting contribution>` — Section 2 — status: TBD.
2. `<system/mechanism contribution>` — Sections 3–4 — status: TBD.
3. `<empirical/model contribution>` — Sections 5–6 — status: TBD.

No contribution may be promoted from TBD until it is backed by the cited section and accepted evidence.
