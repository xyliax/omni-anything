- **标题:** StreamingThinker：大语言模型可以边读边想
- **一句话总结:** StreamingThinker 把持续到达的文本输入与模型生成的思考拆成 source/target 两条流，用流式注意力掩码、独立位置编码和分离 KV cache，让模型不必等全文到齐才开始推理。
- **论文类型:** 方法与推理系统
- **发表:** ICLR 2026；arXiv:2510.17238v3
- **作者:** Junlong Tong 等，代码由 EIT-NLP/StreamingLLM 发布
- **关键词:** 流式推理、边读边想、部分上下文、注意力掩码、并行 KV cache、Qwen3
- ## Orientation
    - **背景:** 普通推理模型先接收完整问题或文档，再开始生成 Chain-of-Thought。对长文本、实时字幕和交互输入，这会让模型长时间空等，也可能在全文到齐后忽视早期信息。
      evidence:: E2
    - **通俗问题:** 人读长题时会一边读一边记中间结果；现有 LLM 却像必须等整页读完才能动笔。论文要让模型在输入逐句到达时先做局部、保守的思考，最后再综合。
      claim_kind:: analyst_assessment
    - **一句话核心思路:** 把输入句子和 reasoning 句子分成两条有明确可见边界的流：输入永远不读取 reasoning，当前 reasoning 只读取已经到达的输入和此前 reasoning。
      evidence:: E3, E4, E10
- ## Quick Reference
    - **阅读价值:** 这是 RP3 的直接非双工算法先例。它不仅约束 reasoning 看不到未来输入，也在推理代码中让新 source prefill 只读 source cache，从而显式处理了输入方向的可见性。
      claim_kind:: analyst_assessment
      evidence:: E4, E10
    - **一句话贡献:** 它把“边读边想”从提示词技巧变成训推一致的模型：构造 streaming CoT，训练时使用 streaming mask/SPE，推理时维护 source、target、merged 三套 cache。
      evidence:: E3, E4, E5
    - **最佳证据:** Qwen3-4B 上，Table 2 报告 Streaming D1 的首个答案延迟约 0.66-0.71 秒，而 batch baseline 为 47.70-61.99 秒；Table 4 的受控效率实验把 first-token latency 从 28.003 秒降到 6.231 秒，split/merge 合计不到 5 ms。
      evidence:: E7, E8
    - **主要边界:** 论文没有固定毫秒切片，也不是真实双工。公开代码预先拿到完整输入、按 token/word/sentence 单元释放，并在一个 Python 循环里交替 `ReadAction` 与 decode；所谓 merge 是逐层 `torch.cat`，不是 paged-KV 的 zero-copy page-table merge。
      claim_kind:: code_verification
      evidence:: E9, E10, E11
- ## Argument Map
    - **问题与重要性:** Batch thinking 的首个 reasoning token 必须等待全部输入到达；输入越长，等待越久，早期证据在全局 attention 中也更容易被稀释。
      evidence:: E2
    - **已有方法缺口:** 朴素 interleaving 虽然可以在输入段之间插入 reasoning，但把两条流塞进一个单调增长的 cache，导致处理新输入前必须停下 reasoning，且训练/推理的可见范围容易不一致。
      evidence:: E3, E6
    - **关键洞见:** 流式推理不是简单提前回答，而是先做与局部证据匹配的浅层计算和实体跟踪；全局条件并未丢失，只是稍后到达，完整输入结束后还可继续 D2 全局整合或 D3 自我反思。
      evidence:: E3, E12
    - **核心主张:** C1：Streaming CoT 可以教会模型按输入顺序做局部 reasoning；C2：streaming mask 与独立位置轴可保证可见性和位置稳定；C3：分离 KV cache 允许输入摄取与 reasoning 生成解耦；C4：该范式在保持准确率的同时显著降低等待。
      evidence:: E3, E4, E7
- ## Mechanism and Design
    - **Streaming CoT 数据:** 输入默认按句子分成 streaming units，并插入 `<EOS>`、`<EOQ>` 等边界。教师模型为每个单元产生局部 reasoning，质量控制过滤错误或过度推断的轨迹。
      evidence:: E3
    - **多深度输出:** D1 在流式 reasoning 后直接回答；D2 再做全局整合；D3 在 D2 上增加自我反思。深度越高通常准确率越高，但 token 和延迟也增加。
      evidence:: E3, E7
    - **训练可见性:** 物理训练序列把全部 source 放在全部 target 之前，因此标准 causal mask 已保证 source query 看不到任何 reasoning；额外的 streaming mask 对每段 `R_t` 屏蔽尚未到达的 source 段。
      evidence:: E4, E10
      - 精确关系为 `X_t <- X_<t`，以及 `R_t <- X_<=t, R_<t`；因此输入方向不是论文遗漏的隐含行为，而是明确受序列布局与 cache 隔离约束。
        claim_kind:: code_verification
        evidence:: E4, E10
    - **Streaming Position Encoding:** source 与 target 使用独立位置编号，避免 source 长度持续增加时把已有 reasoning 的 RoPE 相对位置不断后移。
      evidence:: E4
    - **推理 cache:** 代码初始化 `source_key_values`、`target_key_values` 和 `past_key_values`。`ReadAction=True` 时，新输入只更新并读取 source cache；decode 前 `merge_source_target()` 生成 source+target 视图，decode 的新 KV 写入 merged cache，随后再按 source 长度切回两条 cache。
      claim_kind:: code_verification
      evidence:: E10
    - **切分与推进:** 支持 token、word、sentence 三种 split；默认实验主要按句。模型生成 `<SEP>/<EOS>/<EOQ>/<EOT>/<EOR>/<EOA>` 等边界后，代码把 `ReadAction` 设回真并释放下一段输入。这里的 `t` 是文本单元序号，不是墙钟毫秒。
      claim_kind:: code_verification
      evidence:: E9
    - **实际并发边界:** 论文把读输入的外部时间与 reasoning 生成重叠计入端到端 latency，但公开实现没有 CUDA stream 或两个同时运行的 attention kernel。其核心循环先执行 source forward，再 merge，再逐 token decode。
      claim_kind:: code_verification
      evidence:: E8, E10, E11
- ## Evaluation and Evidence
    - **实验设置:** 在 Qwen3-1.7B/4B 上评估 GSM-Symbolic、MetaMathQA、ProofWriter、LogicNLI、HotPotQA 和 PubMedQA；比较原始 batch、CoT 蒸馏 batch、naive interleaved 与 StreamingThinker D1-D3。
      evidence:: E6
    - **准确率:** Table 1 显示 Qwen3-4B Streaming/Batched-S D2-D3 在多数任务接近或超过原始 batch，同时显著减少 reasoning token；例如 GSM-Symbolic 的 D3 SPE 为 0.874，对原始 batch 的 0.855。
      evidence:: E7
    - **延迟:** 输入速率按 150 words/min 模拟人类语速。Table 2 中 Streaming D1 可在第一段输入后开始 reasoning，首答案延迟远低于 batch 和 interleaved。
      evidence:: E7
    - **系统开销:** Table 4 报告 streaming 需要平均 4.65 次 prefill，额外 prefill bandwidth 约 29,173 MB；峰值显存仍约 8 GB。split/merge 自报很快，但这个结果不代表 merge 是 zero-copy，也没有证明 shared-history KV 只扫描一次。
      claim_kind:: analyst_assessment
      evidence:: E8, E10
- ## Technical Judgment
    - **站得住的结论:** 论文和代码共同证明：标准 decoder LLM 可以在训练与推理中维护 source/target 双向可见性规则，并把输入 prefill 与 reasoning decode 的 KV 状态分开管理。
      claim_kind:: analyst_assessment
      evidence:: E4, E10
    - **不能声称的结论:** 不能称其已经实现 GPU 真并发、paged-KV snapshot/fork、zero-copy merge、prefill/decode fused attention 或共享历史 KV 的一次加载。
      claim_kind:: code_verification
      evidence:: E10, E11
    - **与 RP3 的精确关系:** 当 `R_t` 正在生成而 `X_{t+1}` 已到达时，两者在语义上双向不可见，可从同一已提交历史分叉。StreamingThinker 已给出算法和模型先例；RP3 的新增部分是把串行 `ReadAction/torch.cat` 改成 paged-KV snapshot、page-table fork/commit 和 shared-history kernel co-execution。
      claim_kind:: analyst_assessment
      evidence:: E10, E11
    - **与双工的区别:** reasoning 是内部 target，不会播放给用户；没有 delivered/cancel/barge-in。它把所有 source 都与 reasoning 隔离，而双工系统应允许输入看到此前已交付的输出，只排除同期或未交付输出。
      claim_kind:: analyst_assessment
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata | title page | high
      quote:: Published as a conference paper at ICLR 2026.
    - **E2:** problem | Abstract; Section 1; Figure 1 | high
      quote:: the current LLM reasoning paradigm initiates thinking only after the entire input is available
    - **E3:** method | Sections 2-3.1; Figure 2 | high
      quote:: At each step, the model incrementally processes the incoming sentence
    - **E4:** algorithm | Section 3.2; Figure 3(a) | high
      quote:: enforces order-preserving reasoning through streaming attention masks and position encoding
    - **E5:** inference design | Section 3.3; Figure 3(c) | high
      quote:: maintains separate KV caches for the input sequence and the reasoning sequence
    - **E6:** experiment setup | Section 4.1 | high
      quote:: compare StreamingThinker with three baselines representing alternative reasoning paradigms
    - **E7:** results | Tables 1-3; Sections 4.2-4.3 | medium
      quote:: streaming thinking achieves a markedly lower TTFT than batch reasoning
    - **E8:** efficiency result | Section 5; Table 4 | medium
      quote:: splitkv and mergekv taking less than 5ms combined
    - **E9:** code implementation | README; dataloader_hf.py; generation/generate.py | high
      quote:: split_mode in ["token", "word", "sentence"]
    - **E10:** code implementation | Qwen3/qwen_streaming.py:407-457; generation/generate.py:698-732, 974-1011 | high
      quote:: if ReadAction ... source_key_value.update; else ... past_key_value.update
    - **E11:** code limitation | generation/generate.py:713-715; README release checklist | high
      quote:: torch.cat((source_key_cache, target_key_cache), dim=2)
    - **E12:** discussion | Section 5 | medium
      quote:: global information is deferred rather than lost
