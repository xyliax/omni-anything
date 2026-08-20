# Update Findings

## Promotion Pipeline

```text
raw run
→ terminal status and validation
→ structured experiment record
→ EVIDENCE alias
→ FINDING claim card
→ Current State table
```

## Required Checks

- finding ID 使用 `FINDING-Xn`；
- evidence 使用 `EVIDENCE-*`；
- evidence role 只能使用 `docs/agent/evidence.json.role_definitions` 中的枚举；
- prose 不写 exact timestamp run ID；
- status 区分 implemented、semantics-validated、performance-open、validated、superseded、rejected；
- measurement 带配置域和来源类别；
- limitation 与 remaining uncertainty 不得省略；
- superseded 结论从 current finding 移除，但历史 record 保留；
- 更新 `docs/agent/evidence.json` 后运行 `tests/test_documentation.py`。

## Experiment Record

新 record 复制 `docs/agent/records/template.json`，并满足 `docs/agent/contracts.json` 的 `experiment_record_v1.required_fields`。`legacy-experiment-log.md` 已冻结，不再追加。
