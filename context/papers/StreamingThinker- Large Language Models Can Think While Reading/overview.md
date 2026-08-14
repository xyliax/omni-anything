- **Title:** StreamingThinker: Large Language Models Can Think While Reading
- **Summary:** StreamingThinker separates an incrementally arriving source stream from a generated reasoning stream, then uses streaming masks, separate positions, and split KV caches so reasoning can begin before the full input arrives.
- **Paper Type:** Method and inference system
- **Venue:** ICLR 2026; arXiv:2510.17238v3
- **Keywords:** streaming reasoning, think while reading, attention mask, parallel KV cache, Qwen3
- ## Orientation
    - **Background:** Standard reasoning waits for the complete input before producing any chain of thought, creating avoidable delay on long or live inputs.
      evidence:: E2
    - **Problem in Plain Words:** A person can retain intermediate facts while reading a long problem; a batch LLM behaves as if it cannot start working until the last sentence arrives.
      claim_kind:: analyst_assessment
    - **Key Idea:** Represent source and reasoning as separate streams. Source states never consume reasoning states; reasoning unit `R_t` consumes only source units available through `t` and prior reasoning.
      evidence:: E3, E4, E10
- ## Quick Reference
    - **Why Read It:** It is a direct algorithmic precedent for RP3 outside duplex speech: both directions of source/target visibility are controlled, and inference uses separate source and target KV caches.
      claim_kind:: analyst_assessment
      evidence:: E4, E10
    - **Best Evidence:** On Qwen3-4B, Table 4 reduces first-token latency from 28.003 s to 6.231 s; the paper reports split and merge below 5 ms combined, while Table 1 shows D2-D3 accuracy near or above the original batch model on several tasks.
      evidence:: E7, E8
    - **Main Boundary:** The public implementation is event-driven rather than wall-clock-driven and alternates read/decode in one Python loop. Cache merge physically uses `torch.cat`; no vLLM, paged-KV fork, CUDA-stream concurrency, fused attention, or shared KV scan is implemented.
      claim_kind:: code_verification
      evidence:: E9, E10, E11
- ## Argument Map
    - **Gap:** Naive interleaving starts early but serializes input ingestion and reasoning in one cache and can mismatch training-time visibility.
      evidence:: E3, E6
    - **Claims:** Streaming CoT teaches local conservative reasoning; streaming masks and positions preserve causal alignment; separate caches decouple ingestion from generation; the resulting model lowers latency without giving up most reasoning quality.
      evidence:: E3, E4, E7
- ## Mechanism and Design
    - **Data:** Inputs are divided into token, word, or sentence units; sentence-level units are the primary setup. Teacher-generated local reasoning is filtered for quality, and D1-D3 control direct answer, global integration, and reflection.
      evidence:: E3, E9
    - **Training Mask:** All source tokens precede target tokens, so causal attention prevents every source query from seeing reasoning. A custom mask additionally prevents each reasoning segment from seeing future source segments.
      evidence:: E4, E10
    - **Formal Visibility:** `X_t <- X_<t`; `R_t <- X_<=t, R_<t`. Source-side isolation is real, not an inference from the paper's target-side description.
      claim_kind:: code_verification
      evidence:: E10
    - **Positions:** Source and target use separate position axes so later source arrivals do not shift established reasoning positions.
      evidence:: E4
    - **Inference:** `ReadAction` updates only `source_key_values`; decoding reads a merged source/target cache. Boundary tokens such as `<SEP>` and `<EOQ>` return control to reading.
      claim_kind:: code_verification
      evidence:: E9, E10
    - **Implementation Reality:** The loop executes source forward, merge, and decode serially. `merge_source_target()` concatenates tensors layer by layer, and separation slices the merged tensors back into source and target views.
      claim_kind:: code_verification
      evidence:: E10, E11
- ## Evaluation and Evidence
    - **Setup:** Qwen3-1.7B/4B on math, logic, and context QA, compared with original batch, distilled batch, naive interleaving, and StreamingThinker D1-D3.
      evidence:: E6
    - **Results:** Qwen3-4B GSM-Symbolic D3 with SPE reaches 0.874 versus 0.855 for original batch. Streaming D1 begins after the first input unit and reports much lower answer delay than batch.
      evidence:: E7
    - **Cost:** Table 4 averages 4.65 streaming prefills and reports about 29,173 MB additional prefill bandwidth. Peak memory stays near 8 GB; this does not show zero-copy merging or one shared historical KV scan.
      claim_kind:: analyst_assessment
      evidence:: E8
- ## Technical Judgment
    - **Supported:** A decoder LLM can be trained and executed with separate source/target visibility and cache state.
      evidence:: E4, E10
    - **Not Supported:** True GPU concurrency, wall-clock slicing, duplex delivery semantics, paged-KV snapshot/commit, and fused shared-history attention.
      claim_kind:: analyst_assessment
    - **RP3 Relation:** It validates the algorithmic workload. RP3 replaces serial `ReadAction` and physical concatenation with a shared committed snapshot, page-table branches, delayed commit, and kernel-level co-execution.
      claim_kind:: analyst_assessment
      evidence:: E10, E11
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata | title page | high
    - **E2:** problem | Abstract; Section 1; Figure 1 | high
    - **E3:** method | Sections 2-3.1; Figure 2 | high
    - **E4:** algorithm | Section 3.2; Figure 3 | high
    - **E5:** inference | Section 3.3 | high
    - **E6:** setup | Section 4.1 | high
    - **E7:** results | Tables 1-3 | medium
    - **E8:** efficiency | Section 5; Table 4 | medium
    - **E9:** code | README; dataloader_hf.py; generation/generate.py | high
    - **E10:** code | Qwen3/qwen_streaming.py; generation/generate.py | high
    - **E11:** code limitation | merge_source_target; README checklist | high

