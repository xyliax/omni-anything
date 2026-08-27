# Omni-Anything

## Getting Started

这是环境安装与命令发现入口；研究问题、机制语义、实验协议和证据状态分别回到 [`docs/problem.md`](docs/problem.md)、[`docs/system.md`](docs/system.md)、[`docs/experiments.md`](docs/experiments.md) 和 [`docs/findings.md`](docs/findings.md)。本页不固定当前模型、硬件、profile 或运行时长。

```bash
bash infra/env/setup.sh --help
python -m experiments.baseline --help
python -m infra.trace.perfetto --help
```

具体环境、配置和比较协议以 [`docs/experiments.md`](docs/experiments.md) 为准；当前可执行配置不自动成为最终论文的 workload、modality、output architecture、hardware 或 topology scope。
