# Update Findings

## Promotion Pipeline

```text
raw run
→ terminal status and validation
→ structured experiment record
→ EVIDENCE alias
→ FINDING 条目（findings.md 分组状态表中的一行）
→ Current State table
```

## Required Checks

- finding ID 使用 `FINDING-Xn`；
- evidence 使用 `EVIDENCE-*`；
- evidence role 只能使用 `docs/agent/evidence.json.role_definitions` 中的枚举；
- prose 不写 exact timestamp run ID；
- `record.verdict` 遵循 records/README.md；`evidence.role` 遵循 registry 枚举；finding 条目在其表行内分别交代观察、限定与待补，不混用三者状态；表行容纳不下的过程细节放 record，不回到卡片式正文；
- measurement 带配置域和来源类别；
- limitation 与 remaining uncertainty 不得省略；源码可重建、原始数据可用、统计可复算及公平比较资格分别判断；
- superseded 结论从 current finding 移除，但历史 record 保留；

## Experiment Record

新 record 复制 `docs/agent/records/template.json`，并满足 `docs/agent/contracts.json` 的 `experiment_record_v1.required_fields`。`legacy-experiment-log.md` 已冻结，不再追加。
