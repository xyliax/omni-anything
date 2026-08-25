# Section Contracts and Dependency Map

本文件规定写作顺序和章节接口，目标是让论文从主张推导设计与实验，而不是从代码细节倒推故事。

## Global Dependency

```text
Paper Contract
    ↓
Introduction logic ───────────────┐
    ↓                             │
Background / Problem              │
    ↓                             │
Challenges                        │
    ↓                             │
Design modules                    │
    ↓                             │
Implementation boundaries         │
    ↓                             │
Evaluation questions ←────────────┘
    ↓
Formal evidence
    ↓
Results, Abstract, and final Contributions
```

Intro、Background、Design、Implementation 的骨架与 Evaluation plan 可以并行建立；具体段落和结果只能在上游 contract 对齐后逐步填充。

## Section-by-Section Contracts

| Section | Must consume | Must produce | Must not contain yet | Exit criterion |
| --- | --- | --- | --- | --- |
| Abstract | Frozen main claim and formal headline results | Setting → problem → idea → system → result → boundary | Diagnostic numbers, unsupported generalization | Written last; every result resolves to formal evidence |
| Introduction | Paper contract, closest-work gap, Figure 1 | Six-paragraph story, 2–3 challenges, 3 contributions | Implementation identifiers, unverified novelty, result guesses | Limitations → idea → challenges → modules → contributions all pass |
| Background / Problem | Canonical terminology and problem owner | Workload abstraction, resource conflict, constraints, design goals | System solution details, result conclusions | A reader can derive the challenges without seeing the implementation |
| Design | Challenges and system invariants | One unified idea and one module per challenge | IPC/monkeypatch details, unexplained features | Every module has a causal hypothesis and planned ablation |
| Implementation | Frozen design modules | How the design is realized and observed | New mechanisms invented from code differences | Every detail maps to a requirement or is labeled replaceable implementation choice |
| Evaluation Methodology | Main claim, module hypotheses, evidence rules | Reviewer questions, controls, metrics, sweep, statistics, failure gates | Results or post-hoc thresholds | Each claim has a falsifying experiment and matched control |
| Evaluation | Frozen protocol and formal evidence | Answers to reviewer questions with costs and limits | Reconstructed legacy numbers, new protocol decisions | Each figure has one answer, provenance, uncertainty and limitation |
| Related Work | Closest-work matrix | Capability/assumption comparison and novelty boundary | Chronological paper summaries without comparison | The single closest work and one-sentence delta are explicit |
| Discussion | Supported results and known boundaries | Failure regimes, external validity, operational limits | New result claims | Every major limitation has evidence or is labeled unverified |
| Conclusion | Supported contributions | Restatement of the supported takeaway | New claims or future results | Adds no information absent from the paper body |

## Ordered Milestones

### Milestone 1 — Skeleton Freeze

- [ ] Freeze candidate paper type and one-sentence story.
- [ ] Complete the limitation → key idea → challenge → module map.
- [ ] Assign each contribution to a section.
- [ ] Assign a target page budget to every section.

No prose expansion before this milestone.

### Milestone 2 — Core-Section Outline

- [ ] Introduction has six paragraph-level purpose statements.
- [ ] Background has definitions, assumptions, resource model and non-goals.
- [ ] Design has one subsection per challenge and explicit fallback semantics.
- [ ] Implementation lists only details required to realize or measure the design.

The output is headings plus paragraph bullets, not polished prose.

### Milestone 3 — Evaluation Pre-Registration

- [ ] Each paper claim has a reviewer question.
- [ ] Each reviewer question has a planned figure or table.
- [ ] Independent variables, controls, metrics and failure criteria are frozen.
- [ ] The decisive experiment can falsify the main claim.
- [ ] Mechanism ablations match Design subsections one-to-one.

No headline result language before this milestone.

### Milestone 4 — Controlled Expansion

- [ ] Fill Background and Design from canonical owners.
- [ ] Fill Implementation only to the depth needed for correctness and reproducibility.
- [ ] Run and accept formal evidence.
- [ ] Fill Evaluation from accepted findings.
- [ ] Revise Introduction and write Abstract last.

## Anti-Detail Gate

Before adding an implementation paragraph, answer all four questions:

1. Which Design requirement or invariant makes this detail necessary?
2. Which challenge does it help resolve?
3. Does a reviewer need it for correctness, novelty or reproducibility?
4. If this implementation were replaced, would the paper claim change?

If questions 1–3 have no answer, omit the detail. If question 4 is “no,” label it as an implementation choice and keep it out of the contribution narrative.
