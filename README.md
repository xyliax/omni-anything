# Omni-Anything

本仓库研究单张 GPU 上的周期性交互模型服务：长生命周期会话持续追加上下文，其 KV cache 工作集可能在每周期计算尚有余量时先耗尽 GPU 容量。当前原型系统暂称 **Conveyor**。

## Current Status

Conveyor 当前实现三项候选研究机制：释放偏移调度（release-offset scheduling）、带主机后备的 KV 部分逐出（partial KV eviction with host backing）和 KV 预取（KV prefetching）。周期性本身提供相邻两次使用之间的复用间隔；释放偏移只负责把多会话的输入、计算和恢复需求分散到周期内，并不创造该间隔。

当前测量实例使用 Qwen2.5-Omni 的音频输入路径，但只返回 Thinker 文本输出，不运行 Talker/Code2Wav，也不产生 PCM 音频。它证明的是一个具体原型上的资源现象和机制可行性；对其他交互模型、语音输出和其他硬件的推广仍需资源模型与实验验证。

研究问题与固定术语见 [`Problem`](docs/problem.md)，机制和端到端语义见 [`System`](docs/system.md)，实验协议及当前缺陷见 [`Experiments`](docs/experiments.md)，证据支持的结论与限制见 [`Findings`](docs/findings.md)。

## Quick Start

```bash
bash infra/env/setup.sh --profile cuda13_vllm023 --download-models
python3 infra/env/verify.py --worker-python .venv-vllm023/bin/python
python -m experiments.baseline --trace --duration 120 --label first
python -m infra.trace.perfetto <run-id-or-path>
```

一次运行是否成功以 `status.json` 终态和 validation 为准，不能只看进程 exit code。可执行配置和证据要求以 [`Experiments`](docs/experiments.md) 为准。

## Documentation Guide

| 文档 | 唯一负责的事实 |
| --- | --- |
| 本页 | 项目定位、当前边界和阅读入口 |
| [`Problem`](docs/problem.md) | 研究问题、范围和 canonical glossary |
| [`System`](docs/system.md) | 机制、约束和端到端流程 |
| [`Experiments`](docs/experiments.md) | 配置、比较、指标状态和协议 |
| [`Findings`](docs/findings.md) | 当前证据支持的结论、成熟度和限制 |

首次阅读使用 `Problem → System → Experiments → Findings`。代码已实现不等于机制已验证；诊断结果也不会自动成为论文叙事。精确 run、hash 与 provenance 通过 [`Evidence Registry`](docs/agent/evidence.json) 解析。

Agent 文档只把上述事实映射到代码和维护动作：

```text
AGENTS.md → task guide → human owner → registry → nearest AGENTS.md → code and tests
```

研究范围回到 `Problem`，机制语义回到 `System`，协议回到 `Experiments`，当前结论回到 `Findings`。Agent registry 不得覆盖这些 owner。

若陈述看似冲突，以对应事实域的唯一 owner 为准；历史 results、外部 `.context` 材料和旧讨论稿不能覆盖当前 human docs。

### Agent Documentation

Agent 文档不是第二套项目事实。根 [`Task Router`](AGENTS.md#task-router) 选择最小 read-set；[`system-map`](docs/agent/system-map.json) 定位组件和入口，[`dynamic-edges`](docs/agent/dynamic-edges.json) 记录 subprocess、IPC 与 monkeypatch，[`change-impact`](docs/agent/change-impact.json) 把修改映射到必须复查的 owner 和 tests。
