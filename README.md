# omni-anything

单张 GPU 同时服务全双工语音前台与后台 agent 注入的 serving 研究：瓶颈是 KV 容量而非算力，方向是用闲置的 PCIe 带宽赎回并发容量——错开相位、取现货交付、KV 部分释放（park）三个机制增量已在真机验证，容量主张（N 扫描 + roofline）进行中。

快速上手（详情见 [`infra/env/README.md`](infra/env/README.md) 与各实验目录的 AGENTS.md）：

```bash
bash infra/env/setup.sh --profile cuda13_vllm023 --download-models   # 建 venv + 补丁 + 编译两个 gateway + 拉锁定模型
python3 infra/env/verify.py --worker-python .venv-vllm023/bin/python # 校验环境
python -m experiments.baseline --trace --duration 120 --label first    # 第一个 run（成功判据看 status.json 的 state，不是 exit 0）
python -m infra.trace.perfetto <run-id>                                   # 导出时间线，拖进 ui.perfetto.dev
```

契约、文档地图与上手入口见 [`AGENTS.md`](AGENTS.md)。
