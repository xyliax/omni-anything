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
- 对照需遵循 experiments.md 的公平性表，核对实际生成/保留历史、调度、connector、副本预算、输出与观测路径；当前差异只链接 owner，不在此复制配置值。
- initial-context preloading 是 state construction，必须在 initialization barrier 完成后再开始周期输入。
- 若启用 partial KV eviction 或 KV prefetching，确认观测路径和 `kv_events.log`；当前机制诊断验收要求对应事件，零事件需解释是否存在需求或容量门控。
- formal evidence 要求 clean source；dirty diagnostic run 必须保存可重建 patch artifact。

## Acceptance

成功执行以 `status.json` 终态和 validation 为准，不以 exit 0 为准；同时核对 runner 未完整覆盖的 manifest 语义和跨系统工作量。观测有效、机制被实际使用、服务目标达标分别判断。失败或零事件运行不能计入成功性能点；实际交付低于 cap 本身不构成 correctness failure。报告前按 [结果保留规则](../../../results/README.md#retention-rules) 检查并清理产物，不默认永久保留调试运行。
