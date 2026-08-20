# Omni-Anything

在单张 GPU 上同时服务两类负载：具有硬 tick deadline 的全双工语音前台，以及 delay-tolerant 的后台 agent 结果注入。项目研究的核心矛盾是：KV capacity 往往先于计算能力耗尽，而 tick 内仍存在可用于扩展容量的计算与 PCIe 空隙。

## Current Status

当前仓库包含 baseline 与 conveyor 两个可运行测量臂，以及 phase staggering、take-from-stock delivery、KV park 与 KV prefetch 的实现路径。每项机制的成熟度、量化结论和限制只在 [`docs/findings.md`](docs/findings.md) 维护。

项目目标是前台与 injection 后台共存；当前可执行主路径集中在全双工前台、KV 驻留机制和容量测量，injection 的端到端联合对比协议尚未接入。抽象问题与当前实现边界见 [`docs/problem.md`](docs/problem.md)。

## Quick Start

```bash
bash infra/env/setup.sh --profile cuda13_vllm023 --download-models
python3 infra/env/verify.py --worker-python .venv-vllm023/bin/python
python -m experiments.baseline --trace --duration 120 --label first
python -m infra.trace.perfetto <run-id-or-path>
```

一次运行是否成功以 `status.json` 的终态和 validation 为准，不能只看进程 exit code。完整实验协议见 [`docs/experiments.md`](docs/experiments.md)。

## Documentation Guide

五份人类文档按事实类型分工，不按开发过程堆叠记录：

| Document | Answers |
| --- | --- |
| 本页 | 项目定位、当前边界与阅读入口 |
| [`Problem`](docs/problem.md) | 研究什么、为什么重要、范围在哪里 |
| [`System`](docs/system.md) | 机制与端到端系统如何工作 |
| [`Experiments`](docs/experiments.md) | 配置、指标、比较和证据怎样才有效 |
| [`Findings`](docs/findings.md) | 当前证据支持哪些结论、成熟度与限制 |

第一次阅读按 `Problem → System → Findings`；审计一个数字按 `Findings → Experiments → Evidence Registry`。代码已经实现不等于机制已验证，机制已验证也不等于具备 formal performance evidence。

若陈述看似冲突，按事实类型回到唯一 owner：范围看 `Problem`，机制语义看 `System`，实验口径看 `Experiments`，当前结论看 `Findings`，精确 run 与 hash 看 [`Evidence Registry`](docs/agent/evidence.json)。

### Agent Documentation

Agent 文档不是第二套项目事实，而是把上述事实映射到代码和维护动作。Agent 按固定链路工作：

```text
AGENTS.md → task guide → human owner → registry → nearest AGENTS.md → code and tests
```

| Layer | Purpose |
| --- | --- |
| [`AGENTS.md`](AGENTS.md) | 按任务找到事实 owner，并声明全仓边界 |
| [`Task Router`](docs/agent/README.md) | 选择最小 read-set 和交付要求 |
| `system-map` / `dynamic-edges` | 定位组件、进程、IPC 与 monkeypatch |
| `contracts` / `change-impact` | 约束不变量，并指出改动必须同步检查什么 |
| 最近一层 `AGENTS.md` | 说明目标目录的局部边界与验证方法 |
| `evidence` / `records` | 连接 finding、证据角色、exact run 与历史过程 |

普通读者无需逐项阅读；审计 runtime、修改影响或结论 provenance 时再进入对应 registry。Agent 文档不能覆盖人类事实 owner 中的研究语义、协议或结论。
