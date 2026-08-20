# Modify Engine

## Read Set

1. `engines/AGENTS.md`
2. 目标 arm 的 `AGENTS.md`
3. `docs/system.md` 中对应机制
4. `docs/agent/contracts.json`
5. `docs/agent/dynamic-edges.json`
6. `docs/agent/change-impact.json`

## Change Rules

- engine 不 import `experiments`；runner 通过 path、argv 和 env 驱动它；
- 修改 private vLLM API 前先读 `infra/env/AGENTS.md` 的 upgrade audit；
- 新 patch 必须有门控、加载确认、失败硬终止和可观察事件；
- 不复制 worker observation producer；
- 只实现尚未跑实验时，不修改 finding 的性能状态。

## Verification

至少运行 change-impact 中命中的单元测试和 `tests/test_documentation.py`。涉及 GPU/EngineCore 语义时，CPU 测试不能代替 diagnostic run；run 必须登记源码重建能力。
