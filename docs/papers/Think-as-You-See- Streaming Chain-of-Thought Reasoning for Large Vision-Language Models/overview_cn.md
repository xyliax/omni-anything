- **标题:** Think-as-You-See：面向大视觉语言模型的流式 Chain-of-Thought
- **一句话总结:** TaYS 让模型在视频帧持续到达时同步生成私有 reasoning，用 streaming mask、视觉/文本独立位置轴和双 KV cache 解除“先看完整视频、再推理”的阻塞。
- **论文类型:** 流式多模态推理方法
- **发表:** CVPR 2026；arXiv:2603.02872
- ## Orientation
    - **问题:** 离线 Video CoT 必须等完整视频编码结束才开始 reasoning；朴素 interleaving 又在输入帧和 reasoning 之间形成串行关键路径。
      evidence:: E2
    - **核心思路:** 视觉帧写入 `C_v`，reasoning 写入 `C_r`；decode 时逻辑合并两个 cache，结束后再拆分。streaming mask 防止 reasoning 使用尚未到达的帧。
      evidence:: E3, E4
    - **阅读价值:** 它是 streaming input/reasoning 分支和 cache merge/split 的直接先例，但不是双工对话，也没有 delivered/playback 语义。
      claim_kind:: analyst_assessment
- ## Argument Map
    - **主张:** 帧级 streaming CoT 可以在保持 temporal causality 的同时降低 reasoning 延迟；双 cache 和独立 RoPE 让视觉摄取与 reasoning 状态独立增长。
      evidence:: E3, E4, E6
    - **创新:** 训练 mask、modality-decoupled position 和 parallel KV cache 是一套训推对应设计，而不是只在 serving 端异步编码。
      evidence:: E3, E4
- ## Mechanism and Design
    - **形式化:** 时间步 `t` 的 reasoning 条件为 `V_<=t`、本段此前 reasoning 和 `C_<t`，禁止访问 `F_{t+1:T}`。这里的时间是离散 frame/reasoning alignment，不是实际 wall-clock timestamp。
      evidence:: E3
    - **训练:** 采用 SFT，训练时即使用 streaming attention mask；论文没有 RL 或 rollout mask 维护。
      evidence:: E5
    - **位置:** `pos(v_s)=s`、`pos(r_t)=t`，视觉和 reasoning 使用独立轴，避免视觉序列增长导致 reasoning RoPE 位置漂移。
      evidence:: E3
    - **推理:** `C_v^t=C_v^{t-1}∪Enc(F_t)`；decode 对 `C_v^t` 与 `C_r^{t-1}` 做逻辑合并，生成 `R_t` 后只更新 `C_r`。论文声称 merge 为 pointer-level composition，不做物理 tensor concatenation。
      evidence:: E4
    - **并发边界:** 论文宣称新帧可在 reasoning 生成时异步写入 `C_v`，但没有 CUDA stream、kernel timeline、SM overlap、fused attention、roofline 或 HBM counter，因此只能确认算法/dataflow 并发。
      claim_kind:: analyst_assessment
      evidence:: E4, E8
- ## Evaluation and Evidence
    - **设置:** 基于 Qwen2.5-VL-3B/7B，在扩展 VideoEspresso 协议上比较 batch、batch thinking、batch SFT 和 interleaved SFT。
      evidence:: E6
    - **指标:** reasoning accuracy、initial delay、total reasoning latency 和 reasoning-event deviation；论文没有多会话吞吐或 GPU utilization 实验。
      evidence:: E6, E8
    - **结果:** 论文报告 reasoning 首发等待从约 10.6 秒降到接近 0，并在保持竞争性准确率的同时降低事件偏移；具体收益依赖其构造的 frame-aligned CoT 数据。
      evidence:: E6
- ## Technical Judgment
    - **输出性质:** `R_t` 是 `<think>` reasoning，不是用户正在听到的输出；最终 answer 仍在流结束后生成。
      evidence:: E7
    - **双向关系:** 新帧编码独立于 reasoning，正在生成的 `R_t` 也不读取并发到达的未来帧，因而可形成算法分支；但它没有定义闭环用户如何受输出影响。
      claim_kind:: analyst_assessment
      evidence:: E3, E4
    - **RP3 差异:** TaYS 解决逻辑 cache 组织与流式因果；RP3 解决 shared historical KV 的 snapshot/fork、kernel co-execution 与重复扫描去除。
      claim_kind:: analyst_assessment
- ## Evidence Index
  collapsed:: true
    - **E2:** Sections 1 and 3.1; Figure 1
    - **E3:** Section 3.2 streaming mask and position encoding; Figure 3(b)
    - **E4:** Section 3.2 Parallel KV Cache; Figure 3(a)(c)
    - **E5:** Section 3; training setup
    - **E6:** Section 4; Tables 1-3
    - **E7:** task/output format and Appendix prompts
    - **E8:** full-paper systems audit

