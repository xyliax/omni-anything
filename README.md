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

## Reading Paths

| 目的 | 阅读顺序 |
| --- | --- |
| 第一次了解项目 | [`Problem`](docs/problem.md) → [`System`](docs/system.md) → [`Findings`](docs/findings.md) |
| 判断实验是否可信 | [`Experiments`](docs/experiments.md) → [`Findings`](docs/findings.md) → [`Evidence Registry`](docs/agent/evidence.json) |
| 修改或运行代码 | [`AGENTS.md`](AGENTS.md) → 对应目录的 `AGENTS.md` |
| 理解 IPC、monkeypatch 与完整 runtime | [`Agent Task Router`](docs/agent/README.md) → [`System Map`](docs/agent/system-map.json) → [`Dynamic Edges`](docs/agent/dynamic-edges.json) |

## Documentation Contract

人类文档解释问题、系统、协议与结论；Agent 文档维护代码定位、动态边、修改影响和验证方法；运行证据保存精确 provenance。每类事实只有一个 owner，详细规则见 [`AGENTS.md`](AGENTS.md)。
