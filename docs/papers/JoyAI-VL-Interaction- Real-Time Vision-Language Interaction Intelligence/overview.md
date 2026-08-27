- **Title:** JoyAI-VL-Interaction: Real-Time Vision-Language Interaction Intelligence
- **One-Sentence Summary:** JoyAI-VL-Interaction trains a streaming video assistant as a per-second interaction policy: stay silent, respond, or delegate a hard task to a background model while the live stream continues.
- **Paper Type:** core streaming RL / interaction-model system release
- **Date:** arXiv v1, 2026-06-10
- **Authors:** Dingyu Yao, Junhao Zhou, Chenxu Yang, Chuanyu Qin, Haowen Hou, Zheming Liang, Congcong Wang, Yuhang Cao, Shenglong Ye, Shuai Xie, Shuhuan Gu, Haoyang Huang, Qingyi Si, Nan Duan, Jiaqi Wang
- **Affiliation:** JD.com
- **Resources:** [Paper](https://arxiv.org/abs/2606.14777); [GitHub](https://github.com/jd-opensource/JoyAI-VL-Interaction); [HF model](https://huggingface.co/jdopensource/JoyAI-VL-Interaction-Preview); [HF data](https://huggingface.co/datasets/jdopensource/JoyAI-VL-Interaction)
- **Keywords:** streaming video interaction, interaction model, silence/response/delegate, answer-centered rollout, GRPO, AdaCodec, vLLM, background model

- ## Orientation
    - **Background:** Most VLMs are turn-based: the user asks, then the model answers. JoyAI targets a different setting where the model continuously watches a video stream and decides for itself whether the moment deserves a response.
      claim_kind:: analyst_assessment
    - **Plain Problem:** In monitoring, livestream shopping, accessibility, or AI-glasses scenarios, the important event may happen before the user asks. A useful assistant must act at the right moment, not merely answer quickly after being prompted.
      claim_kind:: analyst_assessment
    - **Core Idea:** Make interaction a model action. Every second, the assistant emits `</silence>`, `</response>` plus text, or a delegation request to a background model.
      evidence:: E3, E4
    - **Why It Matters For Streaming RL:** This is not offline video QA or only inference acceleration. The paper explicitly trains timing, silence, and delegation with SFT followed by GRPO.
      evidence:: E6, E7

- ## Quick Reference
    - **Why Read:** JoyAI is one of the most complete public streaming-interaction recipes available: action space, data format, RL stage, long-horizon memory, vLLM serving, and open resources are described in one work.
      evidence:: E1, E2, E8
    - **What The Rollout Contains:** A rollout is a time-expanded streaming trajectory rather than an isolated second. It contains the visible video prefix, user query, per-second action tokens, model responses, silence decisions, background delegation requests, delayed background results, and timestamps.
      evidence:: E4, E5, E7
    - **What The Trainer Consumes:** The RL stage uses answer-centered window sampling. For each gold response, the system builds a short causal trajectory around the timing-critical turns, reducing hundreds of mostly silent steps to a tractable training window.
      evidence:: E7
    - **How The Model Is Updated:** The recipe first uses weighted SFT, down-weighting repeated silence and up-weighting response onsets. It then uses GRPO with rewards over timing, correctness, appropriate silence, and delegation quality.
      evidence:: E6, E7
    - **Architecture:** A foreground interaction model makes the per-second decision. A background model/API/agent handles slow tasks. ASR, TTS, memory, UI, and background brain are replaceable modules. The paper is not a trainer-rollout resource-scheduling paper and does not specify colocated or fully async training architecture.
      evidence:: E8, E9
    - **Open Resource Status:** GitHub, HF model, and HF dataset links were reachable on 2026-07-02. Full post-training reproducibility still needs repo-level verification.
      claim_kind:: analyst_assessment
      evidence:: E1

- ## Argument Map
    - **Problem:** Turn-based models only answer after being addressed. In a live video stream, the key moment can be brief and cannot be recovered once missed.
      evidence:: E2
    - **Prior Gap:** Real-time omni products mainly optimize conversational turn-taking; consumer video-call products often rely on polling; many streaming-video papers solve latency, memory, or proactive output separately rather than releasing a deployable interaction model stack.
      evidence:: E2
    - **Insight:** The when-to-speak decision should live inside the model, not in an external threshold or timer. Silence must be a supervised action, not the absence of an action.
      evidence:: E3, E4
    - **Claim:** A unified per-second action format over streaming trajectories can teach proactive alerts, commentary, counting, time awareness, multi-turn interaction, and delegation.
      evidence:: E4, E5, E10

- ## Mechanism and Design
    - **Action Space:** At every second the model chooses silence, response, or delegation. During delegation it gives the user a brief holding response, sends a hidden request to the background, keeps watching, and later integrates the returned result.
      evidence:: E3, E5
    - **Video Encoding:** AdaCodec reduces token cost by encoding predictable frames compactly and spending full visual tokens mainly at scene changes.
      evidence:: E3
    - **Data:** The paper reports more than 4M time-aligned streaming clips across proactive alerting, time-aligned QA, counting/perception, live commentary, multi-turn casual chat, and delegation episodes. All are normalized into a shared per-second action format.
      evidence:: E4
    - **Training Sample Shape:** A sample looks like a chat trajectory: timestamped user messages with current frames, followed by assistant control tokens such as `</silence>`, `</response> ...`, and sometimes `</delegation> ...`.
      evidence:: E5
    - **SFT:** Because silence dominates, standard cross-entropy would make the model too conservative. The paper reweights control tokens to reduce repeated-silence dominance and strengthen response onsets.
      evidence:: E6
    - **RL:** GRPO optimizes the streaming action policy. Rewards favor correct and timely responses, appropriate silence, well-judged delegation, and good use of background results; penalties target false alarms, mistiming, degenerate always-respond behavior, and bad delegation.
      evidence:: E7
    - **Serving:** The runtime keeps server-side sessions with video context, QA trajectory, and memory. The memory has short-term raw visual tokens, mid-term summaries, and long-term compressed text, designed around prefix reuse in vLLM.
      evidence:: E8, E9

- ## Evaluation and Evidence
    - **Setup:** The paper evaluates in six real-world streaming scenarios against Doubao and Gemini video-call assistants with human preference judgments.
      evidence:: E10
    - **Headline Result:** JoyAI is reported to win strongly on both quality and timing, especially in monitoring, real-time translation, counting, time awareness, live commentary, and background delegation cases.
      evidence:: E10
    - **Caveat:** The evaluation is explicitly early: six scenarios and 58 human-rated cases, with data mixture and cleaning still not final.
      evidence:: E11

- ## Technical Judgment
    - **What Holds Up:** The strongest contribution is the explicit streaming trajectory contract: visible stream prefix plus per-second action tokens, including silence and delegation.
      claim_kind:: analyst_assessment
    - **Most Useful Lesson For This Project:** The training unit is not every second as an independent sample. It is a causal window around valuable responses, which is exactly the kind of sample boundary a streaming-RL control plane must track.
      claim_kind:: analyst_assessment
    - **Where The Long Tail Appears:** Long-tail behavior comes from delayed future evidence, background-model latency, long context maintenance, and mostly silent trajectories. The paper shortens RL horizons with answer-centered windows, but does not solve trainer-rollout scheduling.
      claim_kind:: analyst_assessment
      evidence:: E5, E7, E9
    - **Limits:** This is a model-and-system release, not an RL-infra paper. It does not define how fully async RL should handle policy versions, stale rollouts, buffer admission, group consistency, or elastic resource switching.
      claim_kind:: analyst_assessment
    - **Project Takeaway:** JoyAI shows that streaming RL can be made to work. The remaining systems opportunity is to make streaming trajectories, delayed results, policy/version provenance, reward-ready boundaries, and trainer admission reproducible and auditable across tasks.
      claim_kind:: analyst_assessment

- ## Workflow Extraction
    - **Initial model:** JoyAI-VL 1.0, initialized from Qwen3-8B with Qwen3-VL ViT and a projection layer.
    - **Initial data:** Conventional turn-based VL data plus time-aligned streaming interaction data.
    - **SFT data:** Timestamped user inputs and assistant control tokens for silence, response, and delegation.
    - **RL rollout:** Answer-centered causal streaming trajectory.
    - **Reward:** Timing, correctness, appropriate silence, delegation quality, false-alarm penalty, mistiming penalty, and LLM-judge content score.
    - **Trainer update:** GRPO, implemented by extending EasyVideoR1's video RL pipeline.
    - **Deployment architecture:** vLLM serving, hierarchical memory, foreground real-time loop, background async loop.

- ## Evidence Index
  collapsed:: true
    - **E1:** metadata | title block and abstract | high
      locator:: title block; arXiv header; project/repository/release lines
      note:: arXiv v1 date, JD.com authorship, project page, GitHub, and release statement.
    - **E2:** problem | Introduction and Related Work | high
      locator:: Section 1; Section 2
      note:: contrasts turn-based models, polling-based products, real-time omni models, and streaming-video research.
    - **E3:** model | Model overview and Section 3.1 | high
      locator:: Section 3; Figure 2
      note:: per-second speak/silence/delegate actions, JoyAI-VL 1.0 initialization, AdaCodec encoding.
    - **E4:** data | Data Construction for VL-Interaction | high
      locator:: Section 3.2
      note:: 4M+ time-aligned clips, six data families, unified per-second action format.
    - **E5:** sample | Training Data Example | high
      locator:: Appendix 7.1
      note:: examples show timestamped user frames followed by assistant silence, response, or delegation outputs.
    - **E6:** sft | Training objective | high
      locator:: Section 3.3
      note:: weighted SFT down-weights repeated silence and up-weights response onset.
    - **E7:** rl | Reinforcement learning | high
      locator:: Section 3.3
      note:: GRPO with answer-centered window sampling and stream-level rewards.
    - **E8:** system | Long-Horizon Memory | high
      locator:: Section 4.3
      note:: short-term raw visual tokens, mid-term summaries, long-term compressed blocks, dialogue memory.
    - **E9:** serving | Serving and Runtime | high
      locator:: Section 4.4
      note:: vLLM-native serving, prefix reuse, stateful sessions, stale-frame drop/backfill behavior.
    - **E10:** evaluation | Experiments | medium
      locator:: Section 5
      note:: human preference evaluation across six real-world streaming scenarios.
    - **E11:** limitation | Experiments discussion | medium
      locator:: Section 5
      note:: paper states the data mixture, cleaning, and evaluation are still early stage.
