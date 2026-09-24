# MiniCPM-o 4.5：周期与 KV 量级

外部模型参数记录，不是项目实测或论文范围定义。用于 Introduction 的具体例子；来源在 2026-09-24 论文修订中核验。

| 属性 | 来源支持的值 | 一手来源 |
| --- | --- | --- |
| 双工决策频率 | 1 Hz，即一秒 micro-turn | [官方模型卡](https://huggingface.co/openbmb/MiniCPM-o-4_5) |
| 输入音频进入语言主干的特征速率 | 10 个位置/秒 | [技术报告 §2](https://arxiv.org/html/2604.27393v1#S2) |
| 主干层数、KV heads、head dimension | 36、8、128 | [固定 revision 的 config.json](https://huggingface.co/openbmb/MiniCPM-o-4_5/blob/503e754207c94da6bb26850b4469f367c9ea3582/config.json) |

按 BF16（每元素 2 字节）保存 K 和 V，每个主干位置需要：

`2 × 36 × 8 × 128 × 2 = 147456 bytes = 144 KiB`。

若完整保留十分钟输入音频对应的 `10 × 600 = 6000` 个主干位置，其 KV 为 `6000 × 144 KiB ≈ 0.824 GiB`。这是架构推导，不是总显存测量；未计文本、视觉、控制位置、其他模块状态和 allocator 开销。输入音频特征速率不能与语音解码器输出 token 率混用。

该例支持周期和状态增长的量级说明，不证明计算余量、KV 空闲区间或服务容量；这些仍需实验。
