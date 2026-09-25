# Qwen2.5-Omni：文本到语音的阶段接口

外部模型笔记，限定到 [Qwen2.5-Omni 技术报告](https://arxiv.org/html/2503.20215v1)与 [Transformers v4.57.6 参考实现](https://github.com/huggingface/transformers/blob/v4.57.6/src/transformers/models/qwen2_5_omni/modeling_qwen2_5_omni.py)。本文不定义本仓实现或论文范围。

## 阶段与状态

| 阶段 | 输入与输出 | 状态 |
| --- | --- | --- |
| Thinker | 处理输入，生成文本 token 与 hidden states | 语言主干自己的 KV |
| Talker | 消费文本侧表示，生成离散语音 codec token | 独立自回归模型的 KV |
| Code2Wav | 将 codec token 转为波形块 | 波形生成所需的状态与缓冲 |

参考实现以 Thinker hidden states 和文本 embedding 构成文本侧表示，再与 Talker 的 codec embedding 组合。特殊 token、位置对应和投影规则应以所链接版本的 `Qwen2_5OmniForConditionalGeneration.generate` 和 `Qwen2_5OmniTalkerForConditionalGeneration.forward` 为准。

## 时序与测量

技术报告描述增量传递文本侧信息的流水线；所列 Transformers 参考实现先生成文本回复，再执行语音生成。模型允许的重叠与具体服务实现实际采用的重叠必须分开核验。

首个文本 token 就绪只满足部分依赖。首音还需经过 Talker 计算、codec 块准备、波形生成及交付，不能用一次主干 prefill 加一次文本 decode 估计完整首音延迟。

文本 token、codec token 和可播放音频是不同计量单位。两个自回归模块也有不同的 KV 几何和保留规则，不能用文本生成速率直接换算完整语音链的吞吐、显存或延迟。

本仓执行路径和输出完成事件由[实验协议](../experiments.md)维护。
