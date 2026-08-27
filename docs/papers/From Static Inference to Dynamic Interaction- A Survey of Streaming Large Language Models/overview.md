- **Title:** From Static Inference to Dynamic Interaction: A Survey of Streaming Large Language Models
- **Summary:** The survey organizes streaming LLM tasks and architectures, including concatenated and interleaved sequence formulations, temporal attention/position design, reasoning, and system concerns.
- ## Orientation
    - “Streaming” spans incremental input, output, proactive behavior, reasoning, and duplex interaction; the survey separates these dimensions.
      evidence:: E2, E3
- ## Taxonomy
    - **Concatenated:** append inputs to one growing causal context; simple and compatible, but state grows and token order can obscure real-time concurrency.
    - **Interleaved:** alternate input and output units by time/event; lower waiting and better temporal alignment, at the cost of specialized data, masks, positions, and runtime state.
      evidence:: E3
- ## Systems Boundary
    - KV management, compression, scheduling, and streaming encoders are discussed, but no same-request snapshot-based prefill/decode fusion is proposed.
      evidence:: E4
    - Duplex works are catalogued; delivered, playback, and cancelled-output visibility are not formalized.
      evidence:: E5
- ## Technical Judgment
    - Use it to expand citations and normalize terminology, then verify mechanism claims against primary papers and code.
      claim_kind:: analyst_assessment
- ## Evidence Index
  collapsed:: true
    - **E2-E3:** introduction and taxonomy
    - **E4:** systems discussion
    - **E5:** full-text semantic audit

