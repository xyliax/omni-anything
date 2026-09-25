# MiniCPM-o 4.5：周期与 KV 量级

外部模型参数记录，不是项目实测或论文范围定义。用于 Introduction 与 Background 的具体例子；输入、输出、状态计数与阶段耗时在 2026-09-25 核验。这里的音频对话模型为 MiniCPM-o 4.5。

| 属性 | 来源支持的值 | 一手来源 |
| --- | --- | --- |
| 双工决策频率 | 1 Hz，即一秒 micro-turn | [官方模型卡](https://huggingface.co/openbmb/MiniCPM-o-4_5) |
| 输入音频进入语言主干的特征速率 | 10 个位置/秒 | [技术报告 §2](https://arxiv.org/html/2604.27393v1#S2) |
| 语音输出对应的主干文本生成速率 | 正常语速下约 3–4 个 token/秒；不是硬上界 | [技术报告 §2](https://arxiv.org/html/2604.27393v1#S2)，Text Decoding；主干先生成文本及 hidden states，由独立语音解码器生成语音 |
| 主干层数、KV heads、head dimension | 36、8、128 | [固定 revision 的 config.json](https://huggingface.co/openbmb/MiniCPM-o-4_5/blob/503e754207c94da6bb26850b4469f367c9ea3582/config.json) |
| 独立语音解码器 | 25 个语音 token/秒；20 层、12 KV heads、head dimension 64；最大上下文配置 4096 | [技术报告 Appendix A, Table 13](https://arxiv.org/html/2604.27393v1#A1)；该模块与主干的 KV 几何及保留方式不同 |

按 BF16（每元素 2 字节）保存 K 和 V，每个主干位置需要：

`2 × 36 × 8 × 128 × 2 = 147456 bytes = 144 KiB`。

十分钟音频对话的例子假设无视频输入，连续接收音频，同时持续输出语音，并完整保留这两部分的主干上下文。取报告正常语速范围的高端，即每秒 4 个输出文本 token：

`600 s × (10 input audio positions/s + 4 output text tokens/s) × 144 KiB = 1.153564453125 GiB`。

其中输入贡献约 0.824 GiB，回复贡献约 0.330 GiB；正文取约 1.2 GiB。若输出占空比为 `d`、说话时的文本生成速率为 `r` token/s，则相同输入条件下，两部分的主干 KV 为 `600 × (10 + d × r) × 144 KiB`。上述例子取 `d = 1, r = 4`，不是典型对话占空比或实测峰值。

“纯音频对话”指用户可见的输入、输出模态；MiniCPM-o 4.5 内部仍用文本生成语音，因此必须计入这些输出文本的主干 KV，不能把 25 Hz 的语音 token 按主干的 144 KiB/位置计算。语音解码器另有自己的 KV；[官方模型文档](https://openbmb.github.io/MiniCPM-o-Demo/site/en/model.html#text-to-speech-tts)还区分完整注意力和窗口模式，不能默认其缓存也保存整段十分钟语音。

该数字仅是双向内容在语言主干中的 KV 估算，不是整个模型的显存上界；未计 prompt/控制位置、语音解码器及其他模块状态、权重、工作区和 allocator 开销。报告的 3–4 个输出文本 token/秒是正常语速描述，不能据此给出所有对话的严格最大值。

该例支持周期和状态增长的量级说明，不证明计算余量、KV 空闲区间或服务容量；这些仍需实验。

<a id="playback-and-execution"></a>
## 时间对齐训练与执行量级

[技术报告 §3.4](https://arxiv.org/html/2604.27393v1#S3.SS4) 的 Time-Aligned Interleaving（TAIL）根据文本 token 的语音时间戳构造训练监督，将文本及对应语音分配到时间片。生成时根据累计播放进度调整当前块的文本量；若此前已有播放积压，可以减少当前块生成量。长回复由连续更新推进，每块对应的播放时长近似于该块的时间长度。该来源支持训练形成的时间对齐行为，不支持“最多只能生成固定几个文本 token”的硬上界。

公开实现 [llama.cpp-omni README 的固定版本](https://github.com/tc-mb/llama.cpp-omni/blob/3dfebb53caaa1ae9cdf5e71ec4db1db65effdfad/README.md#performance-benchmarks) 报告以下外部阶段数据，配置为 RTX 4090、F16：

| 阶段 | 公开耗时 | 解释边界 |
| --- | --- | --- |
| 音频 prefill 阶段 | 约 21 ms | README 的阶段计时；未完整披露 batch、历史长度及 prompt/control 计数，不等于精确隔离的十位置主干 kernel |
| 主干 decode | 约 38 ms/token | 同一配置；README 同时给出三 token 约 115 ms |

结合技术报告中的一秒更新、每秒十个音频位置，以及正常语速对应三至四个文本 token，可推导：

- 主干 decode 约 `3–4 × 38 ms = 114–152 ms`，对应一秒语音的播放，生成速度约为播放速度的 `1000/152–1000/114 = 6.6–8.8` 倍。
- 再加报告的音频 prefill 阶段，约为 `135–173 ms`；这是从外部阶段值组合的量级估算，不是完整周期实测。

语音合成、波形生成、运行时开销及其他输入处理仍需预算；不能把上述差值直接写成完整系统的 compute slack。实际并发、上下文增长与分组改变后的周期执行成本仍须测量，生成量也应记录分布。技术报告另列的主干生成吞吐和 TTFT 使用不同任务，不能混作此处的一秒音频更新计时。
