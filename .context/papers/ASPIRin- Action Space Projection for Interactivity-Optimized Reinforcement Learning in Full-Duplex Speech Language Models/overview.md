- **Title:** ASPIRin: Action Space Projection for Interactivity-Optimized Reinforcement Learning in Full-Duplex Speech Language Models
- **Summary:** ASPIRin prevents timing-oriented GRPO from damaging language generation by projecting the text vocabulary into an active-speech versus inactive-silence policy and optimizing only that coarse state policy.
- **Paper Type:** reinforcement-learning method and speech-interaction application
- **Venue:** arXiv:2604.10065v1, 2026
- **Authors:** Chi-Yuan Hsiao, Ke-Han Lu, Yu-Kuan Fu, Guan-Ting Lin, Hsiao-Tsung Hung, Hung-yi Lee
- **Keywords:** full-duplex speech model, action-space projection, GRPO, turn timing, generative collapse
- ## Orientation
    - **Background:** Full-duplex models such as Moshi can listen while speaking, but the architecture alone does not guarantee natural timing. Models may interrupt pauses, respond too late, or fail to yield after a barge-in.
      evidence:: E1
    - **The Problem in Plain Words:** The goal is to teach the model when to speak without destroying what it already knows how to say. Direct token-level GRPO can exploit timing rewards by speaking aggressively, repeating phrases, and losing semantic coherence.
      evidence:: E1, E8, E10
    - **Why It Is Hard:** Timing rewards evaluate utterance boundaries and overlap intervals, while ordinary GRPO updates every fine-grained vocabulary decision. A low-dimensional control objective is therefore entangled with a high-dimensional language policy.
      claim_kind:: analyst_assessment
      evidence:: E2
    - **Key Idea in One Breath:** Map every text token to Active Speech or Inactive Silence and compute the GRPO ratio, KL, and advantage on this binary state policy rather than the raw-token policy.
      evidence:: E2, E3
- ## Quick Reference
    - **Why Read:** This is a focused answer to a reusable RL problem: how to optimize one coarse behavioral property of a generator without applying the reward indiscriminately to its content choices.
      claim_kind:: analyst_assessment
    - **One-Sentence Contribution:** Action Space Projection aggregates the vocabulary into speak/silence states so GRPO can optimize the response-latency versus interruption trade-off while largely preserving the base model's language behavior.
      evidence:: E2, E4
    - **Mental Model:** The language model writes the script; ASPIRin trains only the microphone switch that decides whether the script should be spoken now or remain silent.
      claim_kind:: analyst_assessment
    - **Best Evidence:** Relative to raw-token GRPO, ASPIRin lowers duplicate 2-grams from 0.117 to 0.054 and duplicate 3-grams from 0.072 to 0.029 while producing a more balanced Full-Duplex-Bench profile.
      evidence:: E7, E10
    - **Main Caveat:** The action space is only binary, the user stream is prerecorded, and the rollout has no playback-aware delivered frontier.
      claim_kind:: analyst_assessment
      evidence:: E5, E11, E12
- ## Argument Map
    - **Problem and Stakes:** SFT does not directly optimize pause handling, turn-taking, backchanneling, or interruption recovery. Raw-token RL can optimize timing but corrupt language quality.
      evidence:: E1, E8
    - **Prior Gap:** Standard GRPO applies an utterance-level timing reward through `pi_theta(y_t | x_<t,y_<t)`, changing particular word probabilities even when the actual error is merely that the model should have stayed silent.
      evidence:: E2
    - **Key Insight:** Timing needs only the probability of speaking versus silence. Grouping padding and non-padding tokens defines a lower-dimensional policy over that property without introducing a separate controller.
      evidence:: E2, E3
    - **Claims:**
        - C1: Projected-state GRPO improves the balance between responsiveness and interruption relative to SFT and raw-token GRPO.
          evidence:: E7, E8
        - C2: Projecting the policy reduces the semantic collapse and repetition caused by raw-token timing optimization.
          evidence:: E9, E10
        - C3: The product of interruption and response rewards is sufficient to improve a range of benchmark interaction scenarios.
          evidence:: E4, E7
- ## Mechanism and Design
    - **Core Mechanism:** Each output text token becomes `s_t=1` for a non-padding token, meaning Active Speech, or `s_t=0` for a padding token, meaning Inactive Silence.
      evidence:: E2
    - **Projection:** The paper sums raw logits within each token set and applies a two-way softmax:

      ```text
      z'_theta(s_t | x_<t,s_<t) = sum_{v in V_s} z_theta(v | x_<t,s_<t)
      pi'_theta(s_t | x_<t,s_<t) = softmax(z'_theta)_s
      ```

      The RL objective therefore asks whether to increase the aggregate active or inactive state instead of rewarding a particular word.
      evidence:: E2
    - **State-Policy GRPO:** Equation 3 computes the importance ratio and KL using `pi'`. The same underlying model still generates text and audio, so ASPIRin is an objective-level decoupling rather than a structurally independent timing head.
      evidence:: E3
    - **Temporal Notation:** Both policies are written as conditioning on `x_<t`, which excludes same-index `x_t` literally. The paper does not define the physical frame represented by `t`, compare `x_<t` with `x_<=t`, or implement a new temporal mask, so this notation is not evidence that ASPIRin designed and validated strict wall-clock causality.
      claim_kind:: analyst_assessment
      evidence:: E2, E3
    - **Rewards:** ASR timestamps define user speech intervals. `R_int` is the fraction of model utterances whose overlap is at most `tau_int`; `R_re` is the fraction that begin within `tau_re` of the preceding user utterance. `R_total=R_int*R_re`.
      evidence:: E4
    - **Training:** The study uses 43 hours of private dual-channel dialogue, roughly 1,300 two-minute clips, Moshi, eight V100 GPUs, three epochs, LoRA rank 256, group size two, `beta=0.001`, and one-second interruption/response thresholds.
      evidence:: E5, E6
    - **Design Risk:** Equation 1 sums raw logits rather than probability mass or log-sum-exp. Because the padding and non-padding sets differ greatly in size, the scaling is not self-evident; the paper provides no projection ablation.
      claim_kind:: analyst_assessment
      evidence:: E2
- ## Evaluation and Evidence
    - **Setup:** Full-Duplex-Bench covers pause handling, backchanneling, smooth turn-taking, and user interruption. Baselines are Moshi, a strong Moshi with a three-second prompt delay, standard SFT, and raw-token GRPO.
      evidence:: E5, E7
    - **Headline Results:** ASPIRin improves several timing metrics but does not dominate every cell. Versus strong Moshi, turn-taking TOR rises 0.748 to 0.765 while latency worsens 0.161 to 0.273 seconds; interruption TOR rises 0.901 to 0.941 and latency improves 1.159 to 0.992 seconds, while the GPT-4o score falls 3.894 to 3.734.
      evidence:: E7
    - **Raw-GRPO Failure:** Standard GRPO becomes more eager in turn-taking and interruption but worsens pause/backchannel takeover and semantic quality, consistent with a policy that speaks too continuously.
      evidence:: E8
    - **Repetition:** Standard GRPO versus ASPIRin 1/2/3-gram repetition is `0.303/0.117/0.072` versus `0.202/0.054/0.029`; Self-BLEU falls from 0.369 to 0.343.
      evidence:: E10
    - **Evidence Gaps:** No error bars, repeated seeds, significance tests, public training corpus, or real-user online evaluation are reported. Semantic evaluation depends on ASR and GPT-4o.
      claim_kind:: analyst_assessment
      evidence:: E5, E7
- ## Technical Judgment
    - **What Holds Up:** The paper identifies a credible optimization mismatch, and the repetition results directly support the claim that projected-state RL damages content less than raw-token timing RL.
      evidence:: E9, E10
    - **What Not to Overclaim:** Timing and content are not fully decoupled because the projected probabilities share the original logits and model parameters. The method coarsens the objective; it does not create an independent control plane.
      claim_kind:: analyst_assessment
      evidence:: E2, E3
    - **Reward Bias:** A one-second overlap can still count as successful, and the response reward only checks latency. Neither reward determines whether an interruption or backchannel is semantically appropriate.
      claim_kind:: analyst_assessment
      evidence:: E4
    - **StreamingRL Boundary:** ASPIRin is a direct full-duplex timing-policy-RL precedent. Its formulas use `x_<t`, but do not operationalize that notation as an attention, KV, or wall-clock mechanism. It replays prerecorded users and records generated states, not client playback, and has no delivered-output frontier or interruption-time KV, attention, and log-probability repair.
      claim_kind:: analyst_assessment
      evidence:: E3, E5, E12
    - **Transferable Lesson:** When a reward evaluates only a low-dimensional property of a high-dimensional action, optimize an explicitly projected policy over that property, then verify that the projection preserves within-class behavior and is numerically calibrated.
      claim_kind:: analyst_assessment
    - **Future Work:** The authors propose expanding the binary action into multi-class or hierarchical states for backchannels, full responses, and interruptions.
      evidence:: E11
- ## Glossary
  collapsed:: true
    - Action Space Projection: grouping the text vocabulary into inactive padding and active non-padding states.
    - State policy: the binary speak/silence probability derived from raw token logits.
    - GRPO: a policy update based on rewards normalized across multiple samples for the same input.
    - Takeover Rate: the rate at which the model takes the speaking floor; the desired direction depends on the task.
    - Nominal frame causality: a discrete-frame dependency such as `x_<t`, not a wall-clock capture/playback relation.
    - Delivered frontier: the output prefix actually played to the user; absent from this paper.
- ## Evidence Index
  collapsed:: true
    - **E1:** problem | Abstract; Section 1 | high
    - **E2:** projection formula | Section 2.1, Equations 1-2; Figure 1(a) | high
    - **E3:** projected GRPO | Section 2.1, Equation 3 | high
    - **E4:** rule rewards | Section 2.2; Figure 1(b) | high
    - **E5:** private data and benchmark | Section 3.1 | high
    - **E6:** training configuration | Section 3.1 | high
    - **E7:** main benchmark results | Table 1; Section 4.1 | medium
    - **E8:** standard-GRPO failure | Section 4.1; Figure 2 | medium
    - **E9:** qualitative interruption example | Table 2; Section 4.3 | low-medium
    - **E10:** repetition results | Table 3; Section 4.3 | medium
    - **E11:** binary-action limitation | Section 5 | high
    - **E12:** playback and closed-loop semantics absent | full-text audit | negative evidence
