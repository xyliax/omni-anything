- **Title:** Think-as-You-See: Streaming Chain-of-Thought Reasoning for Large Vision-Language Models
- **Summary:** TaYS generates private reasoning while video frames arrive, using a streaming mask, modality-separated positions, and video/reasoning KV caches with logical merge and split.
- **Venue:** CVPR 2026; arXiv:2603.02872
- ## Orientation
    - **Problem:** Offline video CoT waits for complete encoding; naive interleaving serializes frame ingestion and reasoning.
      evidence:: E2
    - **Core Idea:** Frames grow `C_v`, reasoning grows `C_r`, and decoding reads a logical composition constrained to observed frames.
      evidence:: E3, E4
- ## Mechanism
    - `R_t` conditions on `V_<=t` and prior reasoning, not future frames. Time is an aligned discrete frame index, not wall-clock time.
      evidence:: E3
    - Training is SFT with the streaming mask; positions use `pos(v_s)=s` and `pos(r_t)=t`.
      evidence:: E3, E5
    - The paper describes pointer-level cache composition and asynchronous frame absorption while reasoning proceeds.
      evidence:: E4
- ## Evidence
    - Qwen2.5-VL-3B/7B experiments compare batch and interleaved baselines on extended VideoEspresso tasks and report near-zero initial reasoning delay from roughly 10.6 s.
      evidence:: E6
- ## Technical Judgment
    - The output stream is private `<think>` reasoning, not delivered duplex speech. No playback, cancel, or delivered frontier exists.
      evidence:: E7
    - Algorithmic concurrency is described, but no CUDA-stream, kernel-overlap, fused-attention, HBM, roofline, or utilization evidence is disclosed.
      evidence:: E8
    - It precedes RP3 at the causal/cache-dataflow layer; RP3 adds shared-snapshot paged KV and kernel-level historical-KV reuse.
      claim_kind:: analyst_assessment
- ## Evidence Index
  collapsed:: true
    - **E2-E4:** Sections 3.1-3.2; Figure 3
    - **E5:** training setup
    - **E6:** Section 4
    - **E7-E8:** output and systems audit

