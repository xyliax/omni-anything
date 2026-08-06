- **标题:** StreamChat：与流式视频聊天
- **一句话总结:** StreamChat 在答案 decode 期间继续采集视频帧，并让每个答案 token 只查询截至其生成时已经到达的视觉 KV，从而避免使用未来画面。
- **论文类型:** 流式视频对话方法
- **发表:** arXiv:2412.08646
- ## Orientation
    - **问题:** 离线 Video-LLM 假设完整视频已知，无法在画面持续变化时边看边答；直接暴露完整视频会产生未来帧泄漏。
      evidence:: E2
    - **核心思路:** capture thread 把新帧放入 FIFO；decode 时消费可用帧并更新视觉上下文，mask 禁止输出 token attend 尚未采集的帧。
      evidence:: E3, E4
- ## Mechanism and Design
    - **Mask:** 它约束的是输出 token 对视觉帧的可见性：答案 token 只能使用其时间边界前的帧。输出 token 自身仍按标准自回归顺序彼此可见。
      evidence:: E3
    - **并发:** 采集线程与模型 decode 并发；帧先进入 FIFO，模型在后续可执行点消费。论文没有同一 kernel 内的视觉更新/decode 融合。
      evidence:: E4
    - **训练:** 构造与推理相同的动态视觉上下文，使答案 token 在训练中也受未来帧屏蔽。
      evidence:: E5
- ## Evaluation and Evidence
    - 在流式视频 QA 与对话任务上比较离线/流式基线，报告准确率和延迟改进；工程并发证据主要来自流程描述，没有 GPU timeline、HBM 或 utilization 分析。
      evidence:: E6
- ## Technical Judgment
    - **时间关系:** 它明确解决 `output_t` 不看未来视觉输入，但没有把同期输入与输出定义成双向不可见 antichain。
      claim_kind:: analyst_assessment
    - **RP3 边界:** 视觉 KV 更接近独立 memory 更新；没有 same-request input prefill/output decode 的 shared historical self-attention 扫描去重。
      claim_kind:: analyst_assessment
    - **输出语义:** 没有 delivered/playback/cancel；用户可见答案的生成和呈现前沿未分离。
      claim_kind:: analyst_assessment
- ## Evidence Index
  collapsed:: true
    - **E2:** Introduction
    - **E3:** Section 2.3, streaming mask
    - **E4:** Sections 2.1-2.3, capture thread and FIFO
    - **E5:** training data/mask description
    - **E6:** experiments

