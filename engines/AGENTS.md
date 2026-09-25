# 引擎层

引擎由 runner 按路径启动，禁止 import `experiments`。仓内启动与 IPC 的索引见 `docs/agent/dynamic-edges.json`。

| 目录 | 系统 | 启动方 |
| --- | --- | --- |
| `baseline/` | matched Metronome baseline | `experiments/baseline/` |
| `conveyor/` | Pilarius 的实现目录 | `experiments/conveyor/` |

正式比较共用 `infra/trace/collectors/`。生成工作量、调度及副本路径的匹配要求见 `docs/experiments.md#executed-decode-difference`；不能由配置名称推定公平。局部说明用于定位，改代码前核验实际路径。

`audio_features.py` 是两个 first-party worker 共用的前处理修正：在创建 AsyncLLM 前安装 Qwen processor wrapper，按重采样后的实际输入长度设置本次调用的 padding 上限。保留 STFT 右边界与 hop 对齐，不修改共享 feature extractor 或模型缓存；显式 max_length、归一化和 dither 配置沿用原路径。CPU 数值验证：`OMNI_TEST_AUDIO=1 .venv-vllm023/bin/python -m unittest tests.test_audio_features -v`。

`model_inputs.py` 持有可扩展的音频输入模板接口；runner 选择的模型 preset 同时锁定权重 revision、模板 family 和 BF16 KV geometry。新增模型复用 manager/copy/观测，先核验 backend KV 布局与流式生命周期。`audio_features.py` 对 vendored MiniCPM Whisper processor 另用每实例只读代理限制补零，不能把 Qwen placeholder 套给新模型。
