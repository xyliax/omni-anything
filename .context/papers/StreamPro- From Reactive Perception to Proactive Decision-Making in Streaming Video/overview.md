- **Title:** StreamPro: From Reactive Perception to Proactive Decision-Making in Streaming Video
- **One-Sentence Summary:** StreamPro formulates proactive streaming video as a decision problem under partial observation and trains models with SFT plus GRPO to optimize both response content and response timing.
- **Paper Type:** core streaming RL / benchmark plus training framework
- **Date:** arXiv v1, 2026-05-11
- **Authors:** Ao Li, Zihan Xiao, Zihao Yue, Boshen Xu, Linli Yao, Jiaze Li, Pei Fu, Jianzhong Ju, Jian Luan, Qin Jin
- **Affiliations:** AIM3 Lab, Renmin University of China; MiLM Plus, Xiaomi Inc.; Peking University
- **Resources:** [Paper](https://arxiv.org/abs/2605.16381); official GitHub/HF model/HF dataset not found as of 2026-07-02
- **Keywords:** proactive streaming video, partial observation, CB-Stream Loss, GRPO, turn-level reward, trajectory-level reward, StreamPro-Bench

- ## Orientation
    - **Background:** Many streaming-video tasks still behave like "answer once the evidence appears." StreamPro argues that this is delayed perception, not true proactive decision-making.
      evidence:: E2
    - **Plain Problem:** If the user asks for step-by-step guidance or early hazard warnings, the model should not wait until everything has already happened. It must respond based on the current partial view.
      claim_kind:: analyst_assessment
      evidence:: E3
    - **Core Idea:** Build a proactive benchmark and datasets, train with CB-Stream Loss in SFT, then use GRPO with turn-level and trajectory-level rewards.
      evidence:: E4, E5, E6
    - **Why It Matters For Streaming RL:** The model emits `</Silence>` or `</Response>` over a streaming trajectory, and the RL reward evaluates not only each answer but also the whole response sequence.
      evidence:: E5, E6

- ## Quick Reference
    - **Why Read:** The paper is useful because it explains why a streaming-RL sample should be a trajectory with time, silence, response, and sequence structure rather than an isolated per-second item.
      claim_kind:: analyst_assessment
      evidence:: E2, E6
    - **What The Rollout Contains:** A rollout is a generated trajectory of length K. At each step, the model sees the video context available so far and emits either `</Silence>` or `</Response>` plus text.
      evidence:: E5, E6
    - **What The Trainer Consumes:** SFT uses streaming samples with silence/response labels. RL uses StreamPro-RL-3K proactive-task data and updates with GRPO using multi-grained rewards.
      evidence:: E7
    - **Reward:** The reward combines format validity, turn-level timing plus semantic correctness, and trajectory-level rubric scoring over granularity, sequencing, coverage, and hallucination.
      evidence:: E6
    - **Resource Status:** The paper reports 3B and 4B experiments. No official code, model, or dataset entry was found during the 2026-07-02 check, so this should be read as a process and reward-design reference rather than an open reproducible stack.
      claim_kind:: analyst_assessment
      evidence:: E1

- ## Argument Map
    - **Problem:** Existing streaming benchmarks often trigger responses after explicit evidence appears, so they mainly test delayed perception.
      evidence:: E2
    - **Challenge 1:** Most timesteps should be silent, and only a few require responses. Standard cross-entropy overfits to silence.
      evidence:: E2, E5
    - **Challenge 2:** Proactive behavior is not only answer accuracy. It also involves timing, avoiding excessive responses, preserving chronology, and covering the right information across the trajectory.
      evidence:: E6
    - **Claim:** Class-balanced streaming SFT plus GRPO with turn-level and trajectory-level rewards substantially improves proactive streaming performance.
      evidence:: E5, E6, E8

- ## Mechanism and Design
    - **Benchmark:** StreamPro-Bench contains 577 videos and 1,285 QA pairs, organized into Perception Understanding, Temporal Reasoning, and Proactive Agency.
      evidence:: E3
    - **Tasks:** The seven tasks are Event Understanding, Object Understanding, Anomaly Alert, Temporal Perception, Temporal Grounding, Goal Planning, and Risk Forecasting.
      evidence:: E3
    - **Proactive Agency:** Goal Planning responds around step transitions; Risk Forecasting warns roughly 3 seconds before a hazard materializes.
      evidence:: E3, E11
    - **SFT Format:** Each timestep outputs a control token, either `</Silence>` or `</Response>`. CB-Stream Loss reweights decision-token classes based on effective sample counts to reduce silence dominance.
      evidence:: E5
    - **RL Format:** GRPO scores the complete generated trajectory. The paper does not treat each second as an independent RL sample.
      evidence:: E6
    - **Training Data:** SFT mixes TimeChat-Online-139K, VideoChat-Flash-3K, StreamPro-SFT-63K, and filtered Streamo-Instruct samples. RL focuses on proactive tasks using StreamPro-RL-3K.
      evidence:: E7
    - **Data Construction:** Benchmark data is built through video filtering, caption/QA generation, multi-stage verification, and human review. Risk Forecasting relies on human annotation and review.
      evidence:: E10, E11

- ## Evaluation and Evidence
    - **Headline Result:** StreamPro-GRPO-4B reports a StreamPro-Bench W-Avg of 41.5, far above listed open-source proactive baselines, while keeping strong real-time streaming results.
      evidence:: E8, E9
    - **Ablations:** CB-Stream Loss beats standard CE and focal loss; a larger temporal tolerance densifies RL rewards; balanced turn-level and trajectory-level rewards perform best.
      evidence:: E12
    - **Trade-Off:** Because the RL stage focuses only on proactive data, the paper reports some small drops on parts of real-time streaming or offline evaluation.
      evidence:: E9

- ## Technical Judgment
    - **What Holds Up:** StreamPro clearly shows why the training target should be a time-expanded response trajectory. A single-turn reward cannot capture whether the whole interaction is coherent, non-redundant, and properly ordered.
      claim_kind:: analyst_assessment
      evidence:: E6
    - **Most Useful Lesson For This Project:** In RL, streaming context is not just a longer prompt. It becomes a trajectory with timing, silence, response decisions, sequence constraints, and sometimes future-risk anticipation.
      claim_kind:: analyst_assessment
    - **Where The Long Tail Appears:** Long-tail rollout behavior comes from waiting for evidence, waiting for step completion, early-warning windows, and many silent timesteps. The paper addresses training signal design, but not rollout-resource scheduling or staleness.
      claim_kind:: analyst_assessment
    - **Limits:** The paper uses a simple sliding-window strategy rather than a dedicated memory mechanism, covers only video and text, and has no official code/data/model entry found yet.
      evidence:: E13
    - **Project Takeaway:** StreamPro confirms that recent work is already training proactive streaming behavior with GRPO. The open systems layer is how to standardize sample boundaries, version provenance, reward readiness, buffer admission, and trainer interfaces.
      claim_kind:: analyst_assessment

- ## Workflow Extraction
    - **Initial data:** 429K open-source data plus StreamPro-SFT-63K, with TimeChat-Online, VideoChat-Flash, and filtered Streamo-Instruct used in SFT.
    - **SFT sample:** Streaming video context plus per-step `</Silence>` / `</Response>` control token and answer text.
    - **RL data:** StreamPro-RL-3K, proactive tasks only, excluding Risk Forecasting.
    - **Rollout sample:** Generated trajectory of length K, including silence/response decisions, response text, and response timestamps.
    - **Reward:** Format reward, turn-level F1 reward, and trajectory-level rubric reward.
    - **Update algorithm:** GRPO.
    - **Architecture:** The paper describes a training framework, not a colocated or fully async rollout service architecture.

- ## Evidence Index
  collapsed:: true
    - **E1:** metadata | title block and abstract | high
      locator:: title block; arXiv header
      note:: arXiv v1 date, authors, affiliations, abstract.
    - **E2:** problem | Introduction | high
      locator:: Section 1
      note:: formulates proactive streaming video as decision-making under partial observations and identifies silence/response imbalance.
    - **E3:** benchmark | Task Taxonomy and Benchmark Construction | high
      locator:: Section 3.1; Section 3.2; Figure 2; Figure 3
      note:: defines three capability dimensions, seven tasks, 577 videos, and 1285 QA pairs.
    - **E4:** framework | Figure 1 and contributions | high
      locator:: Figure 1; Introduction contributions
      note:: StreamPro framework uses SFT and GRPO with StreamPro-SFT-63K and StreamPro-RL-3K.
    - **E5:** sft | Supervised Fine-Tuning with CB-Stream Loss | high
      locator:: Section 4.1
      note:: decision format and class-balanced reweighting for silence/response tokens.
    - **E6:** rl | Reinforcement Learning with Multi-Grained Rewards | high
      locator:: Section 4.2
      note:: GRPO reward combines format, turn-level F1, and trajectory-level rubric components.
    - **E7:** data | Training Data | high
      locator:: Section 4.3; Appendix B.2
      note:: SFT and RL data sources and task distributions.
    - **E8:** results | Proactive tasks | medium
      locator:: Table 2
      note:: StreamPro-GRPO-4B achieves the strongest reported StreamPro-Bench score among listed baselines.
    - **E9:** results | Real-time streaming and offline tasks | medium
      locator:: Table 3; Table 4
      note:: reports real-time streaming and offline benchmark trade-offs.
    - **E10:** data pipeline | Appendix A.1 | high
      locator:: Appendix A.1
      note:: video collection, caption generation, two-agent verification, human review.
    - **E11:** risk forecasting | Appendix A.1.4 | high
      locator:: Appendix A.1.4; Table 8
      note:: human annotation and 3-second risk-warning definition.
    - **E12:** ablation | Ablation Study | medium
      locator:: Section 5.3; Tables 5-7
      note:: validates CB-Stream Loss, temporal tolerance, and trajectory-level reward.
    - **E13:** limitation | Limitations | high
      locator:: Appendix F
      note:: no dedicated memory mechanism, simple sliding window, video-text only, no audio.
