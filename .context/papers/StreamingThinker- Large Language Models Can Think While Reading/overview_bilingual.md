- **Title / 标题:** StreamingThinker: Large Language Models Can Think While Reading / StreamingThinker：大语言模型可以边读边想
- **Summary / 总结:** The method separates arriving source text from generated reasoning with streaming masks, separate positions, and split KV caches. / 该方法用流式掩码、独立位置和分离 KV cache，把持续到达的输入与生成中的 reasoning 拆成两条流。
- **Venue / 发表:** ICLR 2026; arXiv:2510.17238v3
- ## Orientation / 定位
    - **Problem / 问题:** Batch reasoning waits for the complete input; streaming inputs therefore incur long idle delay. / Batch reasoning 必须等完整输入，导致实时或长文本输入产生长时间空等。
      evidence:: E2
    - **Core idea / 核心思路:** `X_t <- X_<t`, while `R_t <- X_<=t, R_<t`. Source never reads reasoning, and reasoning cannot read future source. / 输入永远不读取 reasoning，当前 reasoning 只读取截至当前已到达的输入和历史 reasoning。
      evidence:: E4, E10
- ## Mechanism / 机制
    - **Training / 训练:** Source tokens are placed before target tokens; ordinary causal attention blocks source-to-reasoning visibility, while a custom mask blocks reasoning-to-future-source visibility. / source 在 target 前，普通 causal mask 屏蔽输入看 reasoning，自定义 mask 再屏蔽 reasoning 看未来输入。
      evidence:: E4, E10
    - **Inference / 推理:** `ReadAction` updates only `source_key_values`; decode uses a merged source/target cache. Boundary tokens return control to reading. / `ReadAction` 只更新 source cache；decode 读取 source/target 合并 cache，边界 token 决定何时继续读下一单元。
      evidence:: E9, E10
    - **Granularity / 粒度:** token, word, or sentence, primarily sentence-level; no fixed millisecond clock. / 支持 token、word、sentence，主要按句，不使用固定毫秒时钟。
      evidence:: E9
- ## Evidence / 证据
    - **Quality and latency / 质量与延迟:** Qwen3-4B D3 is competitive with original batch on several tasks; Table 4 reports first-token latency 28.003 s to 6.231 s. / Qwen3-4B D3 在多项任务上接近或超过原始 batch；Table 4 报告首 token 延迟从 28.003 秒降到 6.231 秒。
      evidence:: E7, E8
    - **Implementation boundary / 实现边界:** Public code alternates read and decode serially and merges with layer-wise `torch.cat`; it does not implement true GPU concurrency or zero-copy paged KV. / 公开代码串行交替 read/decode，并逐层 `torch.cat`；没有 GPU 真并发或 zero-copy paged KV。
      evidence:: E10, E11
- ## RP3 Judgment / RP3 定界
    - **What it proves / 已证明:** Source/target bidirectional isolation and inference-time split cache are viable in a standard decoder LLM. / 标准 decoder LLM 中，source/target 双向隔离与推理期分 cache 是可行的。
    - **What remains / 尚未解决:** wall-clock duplex semantics, delivered frontier, snapshot/page-table fork and commit, and fused shared-history attention. / 墙钟双工、delivered frontier、snapshot/page-table fork/commit 与共享历史融合 attention 仍未解决。
- ## Evidence Index
  collapsed:: true
    - **E2:** Abstract; Section 1
    - **E4:** Section 3.2; Figure 3
    - **E7:** Tables 1-3
    - **E8:** Table 4
    - **E9-E11:** public code at `EIT-NLP/StreamingLLM`, commit `066d3b2`
