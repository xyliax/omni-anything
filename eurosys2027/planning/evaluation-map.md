# Evaluation Map

协议和当前 readiness 由 `docs/experiments.md` 持有。本表只把 reviewer questions 映射到论文图表，不复制易变配置或数字。

| Reviewer question | Planned artifact | Primary metric | Required control | Evidence readiness |
| --- | --- | --- | --- | --- |
| Does KV capacity limit concurrency before compute? | Figure `<TBD>` | `<TBD>` | Matched workload and input path | Open |
| How much schedulable concurrency is recovered? | Figure `<TBD>` | `<TBD>` | Matched decode cap and scheduler mode | Open |
| What is the latency cost? | Figure `<TBD>` | `<TBD>` | Per-stage timing semantics | Open |
| Which mechanism provides which benefit? | Figure/Table `<TBD>` | `<TBD>` | Orthogonal ablations | Open |
| Does the resource model generalize? | Figure `<TBD>` | Prediction error | Additional hardware/profile | Open |
| What are the overheads and failure boundaries? | Table/Figure `<TBD>` | `<TBD>` | Long-run and failure controls | Open |

## Before Formal Runs

- [ ] Freeze the operational definition of schedulable concurrency.
- [ ] Resolve the executed decode-work mismatch documented by `docs/experiments.md`.
- [ ] Freeze latency/freshness semantics; do not reuse implementation diagnostics as SLOs.
- [ ] Pre-register independent variables, repetitions, warmup, steady-state window and uncertainty reporting.
- [ ] Assign each planned result a future `EVIDENCE-*` acceptance path.
