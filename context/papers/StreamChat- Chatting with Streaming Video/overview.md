- **Title:** StreamChat: Chatting with Streaming Video
- **Summary:** StreamChat captures frames while answer decoding proceeds and constrains each output token to visual KV available by its generation boundary.
- ## Orientation
    - Offline Video-LLMs see the whole video; StreamChat targets continuously changing video without future-frame leakage.
      evidence:: E2
- ## Mechanism
    - A capture thread places frames in a FIFO; later decode steps consume available frames and query the updated visual context.
      evidence:: E3, E4
    - Training uses the same dynamic visibility principle so output tokens cannot attend future frames.
      evidence:: E5
- ## Technical Judgment
    - It establishes output-to-input temporal masking and capture/decode engineering concurrency, not mutual same-time visibility.
    - It has no delivered/playback/cancel frontier and no shared-KV prefill/decode fused kernel or bandwidth analysis.
      claim_kind:: analyst_assessment
- ## Evidence Index
  collapsed:: true
    - **E2:** Introduction
    - **E3-E5:** Sections 2.1-2.3
    - **E6:** experiments

