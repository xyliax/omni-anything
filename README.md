# Omni-Anything

## Getting Started

安装并校验锁定环境，然后运行一次短实验：

```bash
bash infra/env/setup.sh --profile cuda13_vllm023 --download-models
python3 infra/env/verify.py --worker-python .venv-vllm023/bin/python
python -m experiments.baseline --trace --duration 120 --label first
```
