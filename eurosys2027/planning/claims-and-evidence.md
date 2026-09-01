# Claims and Evidence Ledger

本表只规划论文 claim；接受新结论仍需走仓库的 evidence transaction。不要在这里另建第二套 current state。

| Paper claim | Claim class | Canonical owner | Required evidence | Current readiness | Paper destination |
| --- | --- | --- | --- | --- | --- |
| `<problem observation>` | measured / derived / prior work | `docs/problem.md` + `docs/findings.md` | `<EVIDENCE-*>` | Open | Section 2 |
| `<mechanism semantics>` | source semantics | `docs/system.md` + `docs/findings.md` | `<EVIDENCE-*>` | Open | Section 3 |
| `<capacity or concurrency result>` | formal measured result | `docs/findings.md` | `<EVIDENCE-*>` | Open | Section 6 |
| `<latency or overhead result>` | formal measured result | `docs/findings.md` | `<EVIDENCE-*>` | Open | Section 6 |
| `<resource-model generalization>` | calibrated model + validation | `docs/findings.md` | `<EVIDENCE-*>` | Open | Sections 2 and 6 |

## Promotion Gate

A result sentence can enter the Abstract or Contributions only when all boxes are checked:

- [ ] Stable paper-facing claim wording.
- [ ] Canonical owner contains the accepted finding.
- [ ] Evidence registry resolves it to a clean-source formal run or an explicitly valid non-performance evidence class.
- [ ] Configuration domain, sample count and uncertainty are known.
- [ ] Matched controls and fairness conditions pass.
- [ ] Limitation and external-validity wording is drafted alongside the result.
