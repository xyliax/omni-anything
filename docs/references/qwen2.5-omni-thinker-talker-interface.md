# Qwen2.5-Omni Thinker-Talker 接口

外部模型规格整理。Updated: 2026-08-28

本文不是项目事实源，不定义本项目的 workload、机制或术语；任何内容进入 paper 前必须重新核验原始来源。依据是 Qwen2.5-Omni 技术报告（arXiv:2503.20215）与 transformers v4.57.6 参考实现；实现细节（特殊 token 名、组装顺序）以后者为准，报告未逐一命名。

## 总览

Qwen2.5-Omni 的语音输出链分三级：Thinker 自回归生成文本 token；Talker 是第二个自回归 Transformer，消费 Thinker 的输出并生成离散语音 codec token；Code2Wav（滑动窗口 DiT 加 vocoder）把 codec token 还原为波形，按块流式输出。

Thinker 交给 Talker 的是逐位置配对的两项之和：该位置最后一层的 hidden state，加上该位置采样出的文本 token 的 embedding（查 `embed_tokens` 表），记作 `v[t] = h[t] + embed(y[t])`。hidden 携带语义与韵律走向但对应采样前的分布，不能确定具体是哪个词；embedding 则确定了实际采样出的词，两者互补。

## 逐时间步流程

全流程只有两处采样：Thinker 采样文本 token，Talker 采样 codec token；其余组装全部是确定性规则。两个模型各自闭环（各自把上一步的输出作为输入），唯一耦合点是 Talker 每步从队列 Q 领取的一个文本侧向量。

```text
   ~ sample = a real sampling step; everything else is deterministic rules

PHASE 1  Thinker: one step per TEXT token t            [sampling site #1]
+----------------------------------------------------------------------+
| in  : embed(y[t-1])              its own previous token, fed back    |
| fwd : transformer -> h[t]        last-layer hidden, deterministic    |
| out : y[t] ~ sample(lm_head(h[t]))                                   |
+----------------------------------------------------------------------+
         |                     |
         | y[t] (discrete)     | h[t] (continuous)
         v                     v
GLUE     System bookkeeping: pure rules, nothing sampled
+----------------------------------------------------------------------+
| pair each step:  v[t] = h[t] + embed(y[t])     elementwise add       |
|                                                                      |
| text-side queue Q, consumed left to right:                           |
|   [ v(prompt 1..N),              prefill hiddens                     |
|     embed(tts_bos),              fixed per-speaker constant          |
|     v(reply 1), v(reply 2), ..., paired reply steps                  |
|     embed(text_eos),             fixed constant                      |
|     embed(text_pad) ]            last item repeats forever           |
|                                                                      |
| codec_pad / codec_bos / codec_mask: fixed config constants           |
+----------------------------------------------------------------------+
         |
         | one element per Talker step
         v
PHASE 2  Talker: one step per CODEC token k            [sampling site #2]
+----------------------------------------------------------------------+
| in  : embed(c[k-1]) + next(Q)    its own previous codec token +      |
|                                  one queued text-side vector         |
| fwd : thinker_to_talker_proj -> transformer                          |
| out : c[k] ~ sample(codec_head)                                      |
+----------------------------------------------------------------------+
         |
         | c[1..K]   (K >> number of text tokens)
         v
PHASE 3  Codec decoder: no token sampling
+----------------------------------------------------------------------+
| sliding-window DiT -> vocoder -> waveform chunks (streaming)         |
+----------------------------------------------------------------------+
```

## Talker 输入序列组装

Talker 每个位置的输入是三项在 Thinker hidden 宽度上的逐元素和，过 `thinker_to_talker_proj` 线性层进入 Talker 自己的宽度：

```text
talker_input = thinker_to_talker_proj( h + embed(y) + codec_embed )
```

```text
position    | 1 .. N    | N+1       | N+2        | N+3        | N+4        | ...
------------+-----------+-----------+------------+------------+------------+----
text  side  | v(prompt) | tts_bos   | v(reply 1) | v(reply 2) | v(reply 3) | ...
codec side  | (none)    | codec_pad | codec_bos  | c[1]       | c[2]       | ...
sampled out | -         | -         | c[1]       | c[2]       | c[3]       | ...
```

v4.57.6 的三个实现细节：

- prompt 位置的 ID 序列虽填 `codec_mask`，其 embedding 不参与相加，仅用于占位，保持形状与位置对齐。
- prompt 中音频、图像、视频占位 token 的 token-embedding 被置零，这些位置实际只有 hidden state 一项。
- prefill 阶段只有最后一个位置的 logits 用于采样。

## 首个语音 token 与流式对齐

`c[1]` 从 prefill 最后一个位置采样，输入是 `v(reply 1) + embed(codec_bos)`：`codec_bos` 相当于"第 0 个 codec token"。因此 Thinker 出第一个回复 token 后 Talker 即具备开始采样语音的全部输入，首音延迟约等于 prompt prefill 加一个文本 token 的生成时间。

之后保持一格错位：产出 `c[k]` 的输入是 `embed(c[k-1]) + v(reply k)`。codec 帧率远高于文本 token 速率，文本队列耗尽后每步反复加同一个 `text_pad` embedding，直到 Talker 采样出结束符。

transformers 参考实现是离线式，Thinker 生成完整回复后 Talker 才开始消费；技术报告描述的部署形态是流水线，`v[t]` 随生成立即入队，两级采样并行推进。

## 与本仓库的关系

仓库实测路径只到 Thinker 文本输出，Talker 与 Code2Wav 不在测量链路中；执行路径与指标限制见 [`docs/experiments.md`](../experiments.md)。把结论外推到完整音频输出形态时可参考本文：完整路径引入第二个自回归模型（自有 KV 与采样循环），且输出速率由 codec 帧率而非文本 token 速率决定。

## 资料来源

- Qwen2.5-Omni Technical Report, arXiv:2503.20215。
- transformers v4.57.6, `src/transformers/models/qwen2_5_omni/modeling_qwen2_5_omni.py`: 组装入口 `Qwen2_5OmniForConditionalGeneration.generate`，逐步消费与投影 `Qwen2_5OmniTalkerForConditionalGeneration.forward`。
