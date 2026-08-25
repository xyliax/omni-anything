# Story Logic

这是写作前的逻辑检查表。每个 cell 保持一到四句；超过三项 limitation 或 challenge 通常意味着 scope 过大。

## Thinking Template

| Stage | Draft | Evidence or citation needed | Status |
| --- | --- | --- | --- |
| Research background | `<specific scenario, beneficiary, and why now>` | 3–5 recent works or deployments | Open |
| Limitation 1 | `<prior work/capability X does not handle Y>` | Closest-work citation | Open |
| Limitation 2 | `<prior work/capability X does not handle Y>` | Closest-work citation | Open |
| Limitation 3, if needed | `<prior work/capability X does not handle Y>` | Closest-work citation | Open |
| Key idea or goal | `<one quotable sentence>` | Owner links and novelty audit | Open |
| Challenge 1 | `<why the naive approach fails>` | Mechanism rationale | Open |
| Challenge 2 | `<why the naive approach fails>` | Mechanism rationale | Open |
| Challenge 3, if needed | `<why the naive approach fails>` | Mechanism rationale | Open |
| Module A | `<one module addressing Challenge 1>` | Source semantics + ablation | Open |
| Module B | `<one module addressing Challenge 2>` | Source semantics + ablation | Open |
| Module C | `<one module addressing Challenge 3>` | Source semantics + ablation | Open |
| Contribution 1 | `<specific contribution and section>` | Delivered section | Open |
| Contribution 2 | `<specific contribution and section>` | Delivered section | Open |
| Contribution 3 | `<specific contribution and section>` | Formal evaluation | Open |

## Consistency Gate

- [ ] Every limitation is addressed by the key idea or goal.
- [ ] Every challenge arises from implementing the key idea or realizing the goal.
- [ ] Every challenge maps to exactly one methodology module, or an exception is explicitly justified.
- [ ] Every module or experimental result appears in a specific contribution.
- [ ] Every contribution maps to a section that actually delivers it.

If any item fails, the paper skeleton is `needs user attention`; do not compensate with stronger wording.
