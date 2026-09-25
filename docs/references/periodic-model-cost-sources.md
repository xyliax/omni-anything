# 周期计算估算：跨模型参数与外部实测

外部资料记录，2026-09-25 核验。不表示本项目运行过这些模型，也不冻结论文模型或平台范围。MiniCPM-o 4.5 与 GPU 规格沿用[已有来源记录](minicpm-o-4.5-kv-geometry.md)；本页记录新增模型及用于量级核查的公开测试。

## 模型几何与更新频率

| 模型主干 | 层数 | hidden | MLP intermediate | query/KV heads | head dim | 词表 | 配置上下文 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen2.5-Omni-3B Thinker | 36 | 2048 | 11008 | 16 / 2 | 128 | 151936 | 32768 |
| Qwen2.5-Omni-7B Thinker | 28 | 3584 | 18944 | 28 / 4 | 128 | 152064 | 32768 |
| Moshi temporal Transformer | 32 | 4096 | 11264 | 32 / 32 | 128 | 32000 | 3000 |

- Qwen 原始配置：[3B，revision f75b40e](https://huggingface.co/Qwen/Qwen2.5-Omni-3B/blob/f75b40e3da2003cdd6e1829b1f420ca70797c34e/config.json)、[7B，revision ae9e169](https://huggingface.co/Qwen/Qwen2.5-Omni-7B/blob/ae9e1690543ffd5c0221dc27f79834d0294cba00/config.json)。读取 `thinker_config.text_config`，不用音频编码器或 Talker 的层数代替。二者均未启用 sliding window；此处使用发布配置的 32768，不自行引入 RoPE 扩展。
- [Qwen2.5-Omni 技术报告 §2.2](https://arxiv.org/html/2503.20215v1#S2.SS2)描述每个编码后音频表示对应约 40 ms，即约 25 个主干位置/秒。它支持内容输入量级，不证明每个真实更新仅有 25 个位置；prompt、控制位置与视频另计。报告不规定每秒只运行四次文本 decode，也不规定一秒一个双工更新；这些不能冒充原生协议。
- Moshi：[技术报告 Table 1 与 §3.4](https://arxiv.org/html/2410.00037v2)、[固定代码的模型加载参数](https://github.com/kyutai-labs/moshi/blob/e6a55d2722a65870ef52a6c9f6ecfc0e90f38362/moshi/moshi/models/loaders.py)。配置 `context=3000` 对应 12.5 Hz 下的四分钟保留窗口；每 80 ms 运行一次 temporal Transformer，音频各 codebook 在同一时间位置并行表示，不能把八个音频 codebook 算成八次 temporal forward。
- Moshi 的 MLP 实际 gated intermediate 为 11264。[LM 构造](https://github.com/kyutai-labs/moshi/blob/e6a55d2722a65870ef52a6c9f6ecfc0e90f38362/moshi/moshi/models/lm.py)先传入 `4.125*4096=16896`，再由 [gating.py](https://github.com/kyutai-labs/moshi/blob/e6a55d2722a65870ef52a6c9f6ecfc0e90f38362/moshi/moshi/modules/gating.py)乘 `2/3`。直接把 16896 当成三矩阵中间维度会高估权重和 FLOPs。

按 BF16 KV，`K=4*layers*KV_heads*head_dim*context`。由上述配置推导 Qwen 3B/7B 的主干 KV 分别为 1.125 / 1.75 GiB；Moshi 为 1.46484375 GiB。

辅助状态独立计账：Qwen 3B Talker 为 24 层、2 KV heads、head dim 64、上下文 32768，对应 0.375 GiB；7B Talker 为 24 层、4 KV heads、head dim 128、上下文 32768，对应 1.5 GiB。保留两个模块各自最大 KV 是容量场景，不证明两者在真实会话中同时达到最大值。Talker 计算不是 Thinker 计算的一部分。

Moshi 配置中的 Mimi encoder 和 decoder 各含 8 层、hidden 512、context 250 的全 heads attention；两者 KV 共 `2*4*8*512*250=8192000` 字节。depth Transformer 的 6 层、hidden 1024、context 8 对应 `4*6*1024*8=196608` 字节；合计 8 MiB。该合计只覆盖这些 KV，卷积缓冲、activation 与运行时另计；depth Transformer 与 codec 执行耗时也独立于 temporal 主干。

## 权重容量参考

[Qwen 3B 元数据](https://huggingface.co/api/models/Qwen/Qwen2.5-Omni-3B)在上述 revision 报告 BF16 参数 5,088,069,376、FP32 参数 449,051,296；按存储 dtype 合计约 11.15 GiB。[7B 元数据](https://huggingface.co/api/models/Qwen/Qwen2.5-Omni-7B)报告 BF16 参数 10,283,174,144、FP32 参数 449,051,296，合计约 20.83 GiB。名称中的 3B/7B 不是完整多模态模型的权重总量。后端转换 dtype 或删除模块会改变容量；文件权重字节不能替代实际非 KV 分配。

[Moshi checkpoint 元数据](https://huggingface.co/api/models/kyutai/moshiko-pytorch-bf16)，revision `2bfc9ae6e89079a5cc7ed2a68436010d91a3d289`，报告 7,687,729,152 个 BF16 参数，约 14.32 GiB；另需 Mimi 及其他状态。

## 显存带宽效率的外部参考

2026-09-25 核验。[FlashInfer 的原始内核测试](https://flashinfer.ai/2024/02/02/introduce-flashinfer.html#append--decode-optimizations)将带宽利用率定义为内核读取字节数除以耗时，再除以设备标称显存带宽；测试在每次启动前清空 L2。其长序列普通多头 decode attention 接近峰值带宽，说明优化后的内核可以达到高显存带宽效率。[同文 GQA 测试](https://flashinfer.ai/2024/02/02/introduce-flashinfer.html#grouped-query-attention)显示 CUDA Cores 路径仅达到约四成以上，而 Tensor Cores 路径表现更好，说明效率依赖 attention 类型、并行度和内核实现。

[PyTorch 团队的 GPT-fast 报告](https://pytorch.org/blog/accelerating-generative-ai-2/)给出 A100 80GB、功耗限制 330W、batch 1、FP16 Llama-7B 经编译优化后的约 107 tok/s 和 72% Model Bandwidth Utilization（MBU）。该 MBU 按模型权重字节数乘 decode 速率，再除以设备峰值带宽计算；它是模型级的权重流量指标，与上述 attention 内核的读取流量指标不同，也不能直接等同于包含各阶段 KV 访问的解析效率。该报告同时指出其内存拷贝测试也难以超过约 85%；不能将这个特定实现的拷贝表现视为所有 GPU 的统一上限。

公开结果没有给出跨模型、设备和后端统一适用的平均带宽效率。模型级利用率与内核级利用率应分别比较；内核达到高带宽也不意味着包含调度、输入编码和输出生成的完整周期达到相同比例。

这些结果为较高带宽效率的解析场景提供量级依据，不能作为本项目各模型、各 GPU 或完整更新路径的效率标定。这里讨论的是设备显存访问，不能套用于 H2D 恢复链路；项目采用的效率与敏感性范围由[估算协议](../experiments.md#cross-hardware-projections)持有。

## 可用实测及比较边界

**Qwen 官方速度测试。** [Qwen2.5 Speed Benchmark](https://qwen.readthedocs.io/en/v2.5/benchmark/speed_benchmark.html)使用单张 A100 80GB、batch 1、BF16、生成 2048 个 token；未区分 SXM/PCIe。vLLM 为 0.6.3，FlashAttention 2.6.3，默认 `max_model_len=32768`、`enforce_eager=False`。

| 输入长度 | Qwen2.5-3B-Instruct，vLLM（tok/s） | Qwen2.5-7B-Instruct，vLLM（tok/s） |
| ---: | ---: | ---: |
| 1 | 127.61 | 84.28 |
| 6144 | 123.15 | 80.70 |
| 14336 | 117.35 | 77.69 |
| 30720 | 105.88 | 70.33 |

[官方测试脚本](https://github.com/QwenLM/Qwen3/blob/7a2f61ffc7a20d47efcd2bf97f6f2bf52729042e/examples/speed-benchmark/speed_benchmark_vllm.py)计时包围整个 `llm.generate`，包含初始 prefill，不能把表中的 `1000/speed` 当成纯 decode TPOT。[3B](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/blob/main/config.json)与 [7B](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/blob/main/config.json)的相关矩阵/KV 几何与对应 Omni Thinker 相同；3B Instruct 共享输入/输出 embedding，Omni 不共享，影响容量但不改变一次 forward 访问的输出 head 大小。该测试是主干几何的代理参照，不是 Omni、Talker、增量服务或容量上限 batch 的实测。

同一官方页面还报告 Transformers 4.46.0、FlashAttention 2.5.8 下的速度：3B 在输入 1/30720 时为 30.80/25.37 tok/s；7B 为 40.38/18.83 tok/s。显著的后端差异不能从比较中隐去，更不能用高效后端量级推断任意实现都具有同样余量。

**MiniCPM-o。** [固定 llama.cpp-omni README](https://github.com/tc-mb/llama.cpp-omni/blob/3dfebb53caaa1ae9cdf5e71ec4db1db65effdfad/README.md#performance-benchmarks)报告 RTX 4090 F16 下主干 decode 约 38 ms/token、音频 prefill 约 21 ms，但未完整披露 batch 与历史长度。它只能作量级参照；不能用一个未知上下文点拟合效率后声称最大上下文已验证。详见[原记录](minicpm-o-4.5-kv-geometry.md#playback-and-execution)。

**Moshi。** [官方 README](https://github.com/kyutai-labs/moshi/blob/e6a55d2722a65870ef52a6c9f6ecfc0e90f38362/README.md)报告理论延迟 160 ms，L4 上实际整体延迟最低约 200 ms。这是算法延迟加实现、缓冲等因素后的交互延迟，没有同口径的容量上限 batch、3000 位置、temporal-only 周期测量；不能把 200 ms 当成一次 80 ms 周期的执行时间，也不能用 `200-160` 作为已隔离的 GPU compute time。
