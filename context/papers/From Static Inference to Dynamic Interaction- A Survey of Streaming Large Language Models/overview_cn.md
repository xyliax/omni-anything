- **标题:** 从静态推理到动态交互：Streaming LLM Survey
- **一句话总结:** 该综述整理 streaming LLM 的任务、训练和系统 taxonomy，区分 concatenated、interleaved 等序列组织，并把按时间顺序分配 attention/position 总结为流式模型的共同设计点。
- **论文类型:** 综述
- **发表:** arXiv:2603.04592
- ## Orientation
    - **问题:** “streaming”同时被用于渐进输入、渐进输出、主动响应、视频理解和全双工语音，若不区分信息流与交互协议，相关工作容易被错误合并。
      evidence:: E2
    - **核心贡献:** 从输入/输出模态、是否持续摄取、是否主动输出、是否有 reasoning 等维度组织工作，并总结训练数据、attention/position 和系统挑战。
      evidence:: E3
- ## Taxonomy
    - **Concatenated streaming:** 把连续输入追加成不断增长的单一上下文，兼容标准 causal LM，但上下文与 KV 持续增长，且输入/输出关系容易退化为 token 总序。
      evidence:: E3
    - **Interleaved streaming:** 按时间或事件把输入块与输出块交错排列，使模型在输入尚未结束时产生中间输出；优势是低等待和时间对齐，代价是数据构造、mask、position 与推理状态管理更复杂。
      evidence:: E3
    - **其他范式:** 综述还覆盖 memory/compression、异步模块、主动决策和 reasoning stream；这些类别并不自动意味着 kernel 并发。
      evidence:: E3, E4
- ## Systems and Semantics
    - 综述讨论 KV 增长、上下文压缩、调度和流式编码等效率问题，但没有提出同请求 source-prefill/target-decode 的 shared-snapshot fused attention。
      evidence:: E4
    - 文中出现 full-duplex/duplex 工作与交互 taxonomy，但没有 delivered/playback/cancelled-output 的形式化上下文前沿。
      evidence:: E5
- ## Technical Judgment
    - 它适合作为引文图谱与术语入口，不适合作为任何具体可见性或 GPU 实现主张的唯一证据；必须回到被引论文和代码。
      claim_kind:: analyst_assessment
    - 对 RP3 最重要的启发是：interleaving 只是序列表示，不能替代墙钟 partial order；标准 causal interleaving 往往仍让后到输入看到同期已生成输出。
      claim_kind:: analyst_assessment
- ## Evidence Index
  collapsed:: true
    - **E2:** introduction and scope
    - **E3:** taxonomy tables and streaming paradigms sections
    - **E4:** systems/efficiency discussion
    - **E5:** full-text semantic term audit

