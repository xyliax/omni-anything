# Run Experiment

## Read Set

1. 根 `AGENTS.md`；
2. `docs/experiments.md`；
3. 目标 evaluated system 最近一层 `AGENTS.md`；
4. `experiments/<system>/config.py`、`runner.py` 与 `experiments/shared/`；
5. `results/README.md`；
6. 若要解释预期结论，再读 `docs/findings.md` 与 `docs/agent/evidence.json`。

## Before Launch

- 固定 model revision、environment profile、GPU、session count、period、output cap、initial context length 与 scheduling mode。
- 正式跨系统比较必须统一 offered input 和 executed decode cap；当前 matched baseline 的 \(M+8\) 与 Conveyor 的 \(M\) 差异尚未修复，因此旧比较只能作诊断。
- initial-context preloading 是 state construction，必须在 initialization barrier 完成后再开始周期输入。
- 若启用 partial KV eviction 或 KV prefetching，确认 required artifacts 包含 `kv_events.log`，并分别要求 `E` 或 `L trigger=prefetch` 事件。
- formal evidence 要求 clean source；dirty diagnostic run 必须保存可重建 patch artifact。

## Acceptance

以 `status.json` 终态和 validation 为准，不以 exit 0 为准。出现 session death、RPC/client failure、初始化超时、artifact 缺失、manifest 损坏，或已启用的机制没有产生事件，run 都不可接受。实际输出小于 \(M\) 是诊断信号，本身不构成 correctness failure。
