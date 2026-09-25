# Modify Engine

## Read Set

1. 根 `AGENTS.md` 的 `Research Classification` 与 `Change Transactions`；
2. 目标 evaluated system 最近一层 `AGENTS.md`；
3. `docs/system.md`，优先读 `#logical-architecture`、`#component-interface-contracts`、`#operational-flow`、`#implementation-handoff` 与 `#open-design-decisions`；
4. `docs/agent/system-map.json`、`dynamic-edges.json`、`contracts.json` 与 `change-impact.json`；
5. 目标 source 及其直接 runtime dependency。

## Required Reasoning

- 先判定改动是 research mechanism、system requirement 还是 implementation choice。
- 若修改 KV 管理，分别说明 session activity、request ownership、GPU block placement、host backing coverage 与 transfer state 如何变化。
- 若修改进程、IPC、utility command 或 monkeypatch，必须同步更新 system map、dynamic edges 和 producer/consumer contract tests。
- 不得仅因为多了一个新开关、补丁或代码差异，就把它归为 paper mechanism。
- 未经新 run 验证的实现优化不得提前改变 `docs/findings.md` 中的性能状态。

## Verification

执行 `change-impact.json` 指向的测试，随后从根目录运行 `python -m pytest`。若变更影响 artifact schema，必须同时更新 parser、Perfetto exporter、runner required artifacts 和 tests。
