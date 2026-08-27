- **Title:** Multi-Faceted Interactivity Alignment in Full-Duplex Speech Models
- **Summary:** The paper shows that reinforcement learning over separately rewarded conversation events can make full-duplex speech models more responsive without forcing them to speak over users.
- **Paper Type:** application
- **Venue:** arXiv preprint 2026
- **Authors:** Atsumoto Ohashi (Kyutai), Neil Zeghidour (Gradium), Alexandre Defossez (Kyutai and Gradium), Eugene Kharitonov (Gradium)
- **Keywords:** full-duplex speech models, spoken dialogue, reinforcement learning, turn-taking, backchanneling, interactive evaluation
- ## Orientation
    - **Background:** Speech assistants often wait for a clear handoff before replying. A full-duplex speech model instead listens and speaks at the same time, closer to human conversation where people pause, overlap, and give short acknowledgments.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** The practical problem is deciding what a quiet or overlapping moment means: the user may be thinking, handing over the turn, asking a correction, or simply needing a quick sign that the system is following.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** Good behavior depends on timing and meaning together. Speaking too early feels interruptive, waiting too long feels broken, and optimizing one habit can damage another.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Train on short real conversation moments, reward the specific interaction choice each moment calls for, and add a content check so faster timing does not erase useful answers.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a speech-dialogue alignment paper: it turns vague conversational timing failures into a small set of rewardable interaction events, then tests whether that improves real-time speech agents rather than only offline clips.
      claim_kind:: analyst_assessment
      evidence:: E1, E2, E7
    - **One-Sentence Contribution:** The paper improves full-duplex spoken dialogue behavior by training models on short real conversation moments with rewards tied to the interaction decision each moment requires.
      evidence:: E3, E6
    - **Mental Model:** Picture a driving coach replaying short traffic moments: sometimes the right move is to wait, sometimes to go, sometimes to give a quick nod, and sometimes to stop and answer after being cut off.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is the paired static and interactive evaluation: the method improves timing metrics on Full-Duplex-Bench v1 and mostly carries those gains into Full-Duplex-Bench v2 multi-turn dialogue.
      evidence:: E9, E11, E12
        - Supports C1: Moshi trained on Fisher; baseline Moshi; Full-Duplex-Bench v1 pause, turn-taking, interruption, and backchannel metrics; pause Candor takeover rate 0.528 to 0.417, turn latency 0.162 to 0.121, interruption latency 1.377 to 0.461; broad support without reported variance.
          evidence:: E9, E11
        - Supports C2: PersonaPlex trained on Seamless; baseline PersonaPlex; Full-Duplex-Bench v2 LLM-judged scores; Daily turn score 3.327 to 4.017, Correction task 3.080 to 3.620, Entity Tracking task 3.200 to 3.840, Safety task 3.260 to 3.280; support is automated and benchmark-specific.
          evidence:: E12
        - Supports C3: Moshi trained on Fisher ablations; full model baseline; removing the LLM Judge reward drops interruption GPT-4o score 3.58 to 3.05 and Daily instruction score 2.50 to 2.18; supports the semantic-reward component but not statistical robustness.
          evidence:: E13
    - **Main Caveat:** The method is less general than the headline suggests: it assumes models expose a parallel text token stream, depends on manual rule rewards and automated judges, and can push safety behavior in the wrong direction when the interaction corpus is mismatched.
      claim_kind:: analyst_assessment
      evidence:: E14, E15
- ## Argument Map
    - **Problem and Stakes:** The paper argues that token-level supervised learning, which trains a model to predict the next text or audio token, does not directly optimize interaction-level behavior such as when to wait, answer, yield, or backchannel. The stakes are user-visible: a model can sound semantically capable but still feel unnatural because its timing is wrong.
      evidence:: E1
    - **Prior Gap:** Prior reinforcement learning methods for full-duplex speech, where a model is updated from rewards rather than only from supervised targets, covered only part of the interaction space and often targeted one model family. The paper also identifies semantic degradation as a recurring risk when rewards focus mainly on timing.
      evidence:: E2, E7
    - **Key Insight:** The key insight is to decompose interactivity into four observable event types and train on short human-conversation segments where each event type has a simple reward target. This turns broad conversational alignment into repeated local decisions while preserving response content with an LLM Judge, an automatic evaluator that scores transcribed responses for relevance and naturalness.
      evidence:: E3, E6, E7
    - **Claims:** The paper's main claims are about multi-axis interactivity gains, transfer from short-segment training to longer dialogue, component necessity, and explicit applicability limits.
      claim_kind:: analyst_assessment
        - C1: Axis-specific reinforcement learning improves static full-duplex interactivity across pause handling, turn-taking, backchanneling, and user interruption for both Moshi and PersonaPlex.
          evidence:: E9, E10, E11
        - C2: Training on short extracted segments can improve real-time multi-turn dialogue behavior, especially turn-taking fluency, in Full-Duplex-Bench v2.
          evidence:: E12
        - C3: Joint rewards and the LLM Judge content reward are needed to balance competing interaction axes and preserve meaningful responses.
          evidence:: E7, E13
        - C4: The method's applicability is bounded by manual reward design, automated evaluation, safety drift, and model architectures that expose a parallel text token stream.
          evidence:: E14, E15
- ## Mechanism and Design
    - **Core Mechanism:** The method applies Group Relative Policy Optimization (GRPO), a reinforcement-learning update that compares multiple sampled answers for the same input, to a pretrained full-duplex speech model. Each batch samples one interaction axis, generates several candidate responses, scores them with the corresponding reward, and updates the model toward candidates that did better than their group.
      evidence:: E5, E6
    - **Data / Control Flow:** A voice activity detection (VAD) model, which marks where speech is present, converts two-speaker recordings into utterances and silences; the pipeline extracts event windows for pause handling, turn-taking, backchanneling, and user interruption. During training, the user side is encoded into discrete audio tokens, the model samples responses, generated speech is decoded, and reward scores drive the GRPO update.
      evidence:: E4, E5, E8
        - Extraction uses inter-pausal units (IPUs), speech chunks separated by short pauses, to decide whether an event is a hesitation, a turn handoff, a short listener response, or an interruption.
          evidence:: E6, E8
        - Pause handling rewards silence, turn-taking and interruption reward shorter response delay, and backchanneling rewards short acknowledgments near human backchannel positions while penalizing takeovers.
          evidence:: E6
        - The loss is computed over the segment while a randomly sampled preceding context window can be prepended and masked out, so the model conditions on recent conversation without being trained to reproduce that context.
          evidence:: E5, E8
    - **Design Decisions:** The design is deliberately narrow: it does not invent a new full-duplex architecture, but post-trains existing models with rewards tied to the benchmark's interaction axes. The closest alternative is a single timing objective or a smaller subset of behaviors, which the paper argues can shift rather than solve the interaction tradeoff.
      claim_kind:: analyst_assessment
      evidence:: E2, E3, E13
        - Need: realistic timing. Choice: extract short segments from Fisher and Seamless human conversations rather than synthesize artificial dialogues; tradeoff: corpus style can become a behavioral prior.
          evidence:: E8, E15
        - Need: prevent fast but irrelevant replies. Choice: add an LLM Judge reward to turn-taking and interruption; tradeoff: the content signal inherits automatic speech recognition and judge-model failure modes.
          claim_kind:: analyst_assessment
          evidence:: E7, E14
        - Need: make policy updates tractable. Choice: compute the importance ratio and objective only on the parallel text token stream because the paper says timing and content are primarily controlled there; tradeoff: models without such a stream are out of scope.
          evidence:: E4, E14
    - **Implementation Surface:** The implementation surface is a post-training recipe for existing open-source full-duplex models, tested on Moshi, a seven-billion-parameter speech-text language model, and PersonaPlex, a Moshi-derived model with prompt and voice control. It reports training on Fisher or Seamless with GRPO over 100 epochs, 16 completions per segment, and 32 H100 GPUs.
      evidence:: E8, E16
- ## Evaluation and Evidence
    - **Setup:** The static benchmark is Full-Duplex-Bench v1, which feeds prerecorded audio and measures takeover rate (TOR), response latency, backchannel frequency, Jensen-Shannon divergence (JSD), and a GPT-4o semantic score for interruption responses. The dynamic benchmark is Full-Duplex-Bench v2, where GPT-Realtime acts as an automated speaking partner and Gemini 2.5 Flash judges turn-taking fluency, instruction following, and task competence.
      evidence:: E8, E12
    - **Claim-Evidence Matrix:** The evidence is strongest for C1 and moderate for C2 and C3: the paper reports broad metric improvements, but the main tables do not report confidence intervals, repeated seeds, or human-judged conversation quality.
      claim_kind:: analyst_assessment
      evidence:: E9, E10, E12, E13
        - C1: Table 1 supports multi-axis static improvement for both model families, with the caveat that benchmark metrics are automatic and variance is not reported.
          claim_kind:: analyst_assessment
          evidence:: E9, E10, E11
        - C2: Table 2 supports transfer to multi-turn dialogue for most conditions, but scoring is still automated and Fisher safety behavior shows a corpus-dependent regression.
          claim_kind:: analyst_assessment
          evidence:: E12, E15
        - C3 and C4: Table 3 and the Limitations section support the need for content reward and context while also exposing manual-reward, text-stream, automated-evaluation, and safety boundaries.
          claim_kind:: analyst_assessment
          evidence:: E13, E14, E15
    - **Headline Results:** On Full-Duplex-Bench v1, RL improves the target interaction metrics for both Moshi and PersonaPlex, including lower pause takeover, faster response latency, and better interruption response timing. On Full-Duplex-Bench v2, Seamless-trained variants are the clearest winners, especially PersonaPlex with Seamless across Daily, Correction, Entity Tracking, and most Safety metrics.
      evidence:: E9, E10, E12
        - Moshi plus Fisher shows the cleanest latency gain in Table 1, cutting interruption latency from 1.377 s to 0.461 s while also reducing pause Candor TOR from 0.528 to 0.417.
          evidence:: E9
        - PersonaPlex plus Seamless reduces backchannel TOR from 0.182 to 0.073 and turn-taking latency from 0.219 s to 0.086 s, while keeping the interruption GPT-4o score slightly above the base model.
          evidence:: E10
        - PersonaPlex plus Seamless improves the Daily, Correction, Entity Tracking, and Safety task-family scores in Table 2, but the largest gains are not uniformly in safety competence.
          evidence:: E12, E15
    - **Ablations and Sensitivity:** The ablations make the paper more credible because they reveal a real tradeoff: without pause data the model speaks too readily, without turn data it becomes too conservative, and without the LLM Judge reward the semantic scores fall. Context scheduling is less dramatic than the reward ablations but still helps multi-turn behavior.
      evidence:: E13
        - Without pause data, pause TOR worsens from 0.42 to 0.74 while turn latency falls to 0.05 s; without turn data, turn latency worsens to 0.30 s, showing the wait-versus-speak tradeoff.
          evidence:: E13
        - Without the LLM Judge reward, the interruption semantic score falls to 3.05 and Daily instruction-following to 2.18, supporting the claim that timing rewards alone are insufficient.
          evidence:: E13
        - Without context, Daily turn-taking and instruction scores fall relative to the full Fisher model, supporting the use of preceding audio even when the loss is only on short segments.
          evidence:: E13
    - **Reproducibility Gaps:** Checkpoints and audio samples are reported as available, but full reproduction still needs unreported details around exact extracted segment lists, evaluation-script patching, automated-judge prompts beyond the shown LLM reward prompt, and large hardware. The paper reports 32 H100 GPUs for training, making exact replication expensive even if model artifacts are public.
      claim_kind:: analyst_assessment
      evidence:: E8, E16
- ## Technical Judgment
    - **What Holds Up:** The central engineering claim holds up better than a single-metric timing paper would: the method improves multiple competing static metrics, tests two model families, and includes ablations that show why the pause, turn, content, and context components matter. The evidence is still benchmark-centric, so the right reading is promising post-training recipe rather than settled human-conversation quality.
      claim_kind:: analyst_assessment
      evidence:: E9, E10, E12, E13
    - **Where It May Fail:** The method may fail when the target model does not expose a parallel text stream, when the desired behavior is not captured by hand-written VAD-based rewards, or when the interaction corpus teaches the wrong social prior. The Fisher safety regression is the clearest warning that responsiveness is not the same as policy alignment.
      claim_kind:: analyst_assessment
      evidence:: E14, E15
    - **Relation to Other Work:** Compared with prior preference-based and online-reinforcement-learning full-duplex alignment methods, this paper broadens the reward surface from barge-in or backchannel behavior to four benchmark-aligned axes; compared with ASPIRin, it keeps GRPO-style timing optimization but adds explicit semantic reward and multi-model evaluation. Compared with cascaded full-duplex systems, it stays inside end-to-end speech models rather than adding external turn-control modules.
      evidence:: E2, E3, E7
    - **Transferable Lesson:** For interactive agents, optimize the decision boundary that users feel, not just the content generator: split the interaction into concrete event windows, reward the local decision, and add a separate guardrail for content or safety so speed does not become blind compliance.
      claim_kind:: analyst_assessment
      evidence:: E3, E7, E13, E15
- ## Glossary
  collapsed:: true
    - full-duplex spoken dialogue model: A speech model that can listen to incoming user audio while also producing its own speech, instead of waiting for a strict turn boundary.
    - turn-taking: The ability to detect when the user has yielded the floor and begin responding promptly without speaking over an unfinished utterance.
    - backchanneling: Short listener feedback such as brief acknowledgments while the user continues speaking; in this paper it must be timed without becoming a takeover.
    - user interruption: A moment where the user starts speaking while the model is speaking; the desired behavior is to yield and then answer the interruption.
    - voice activity detection: A detector that marks which time intervals contain speech; the paper uses it to build training segments and compute rewards.
    - inter-pausal unit: A speech chunk separated by pauses; the paper groups these chunks into utterances when pauses are short enough.
    - Group Relative Policy Optimization: A reinforcement-learning method that samples several outputs for the same input, normalizes their rewards within the group, and updates the policy toward relatively better outputs.
    - Takeover Rate: The proportion of samples where the model produces a prolonged utterance rather than staying silent or giving only a short backchannel.
    - Jensen-Shannon divergence: A bounded distribution-distance metric; here it measures how far generated backchannel timing is from human backchannel timing.
    - LLM Judge: A large-language-model evaluator that scores transcribed model responses for contextual relevance and naturalness.
    - automatic speech recognition: A speech-to-text system used before LLM-based semantic scoring of generated speech.
    - context window: Audio immediately before a training segment that is prepended as conditioning context but masked out of the loss.
- ## Evidence Index
  collapsed:: true
    - **E1:** problem/paper_statement | Abstract and Introduction | high
      locator:: Abstract; Section 1
      quote:: Full-duplex spoken dialogue models can listen and speak simultaneously, making them a promising architecture for natural conversation. However, current models are trained solely with supervised learning through token-level likelihood maximization, which does not directly optimize interaction-level behaviors.
    - **E2:** gap/paper_statement | Introduction and Related Work | high
      locator:: Section 1; Section 2.2
      quote:: Prior works have explored using reinforcement learning to improve the interactivity of full-duplex models, but covered only a subset of conversational dynamics such as handling user's barge-in and backchanneling, failing to comprehensively address all axes of interactivity.
    - **E3:** method/paper_statement | Method | high
      locator:: Section 3, Figure 1
      quote:: We target four core axes of interactivity: pause handling, turn-taking, backchanneling, and user interruption. These four axes have been established as a standard and comprehensive characterization of full-duplex interactivity.
    - **E4:** formula/implementation_detail | Full-Duplex Spoken Dialogue Modeling | high
      locator:: Section 3.1
      quote:: Given a two-channel dialogue between speakers X and Y, a speech tokenizer E maps each speaker's waveform into a sequence of discrete tokens from a vocabulary. The model learns to autoregressively predict speaker Y's tokens conditioned on speaker X's input stream and its own preceding outputs.
    - **E5:** algorithm/implementation_detail | Reinforcement Learning Pipeline | high
      locator:: Section 3.2
      quote:: For each sample in the batch, we first sample an interactivity axis, then draw a segment from the axis-specific training set. The current policy generates G completions, each completion is decoded into a waveform and scored by an axis-specific reward function.
    - **E6:** method/implementation_detail | Reward Design | high
      locator:: Section 3.4
      quote:: We design a dedicated reward function for each interactivity axis. Pause handling assigns a binary reward if generated audio contains speech longer than 1 s; turn-taking and user interruption use negative response delay; backchanneling uses an F1 score around ground-truth backchannel positions.
    - **E7:** method/implementation_detail | Reward Design | medium
      locator:: Section 3.4, LLM Judge
      quote:: To prevent semantic degradation caused by optimization with delay-based rewards alone, we add a content quality reward to the turn-taking and user-interruption axes. Transcriptions are scored by an LLM judge on a three-point scale for contextual relevance and naturalness.
    - **E8:** experiment_setup/paper_statement | Experiments | high
      locator:: Sections 4.1 and 4.3
      quote:: We adopt two datasets: Fisher, with 2,000 h of telephone conversations, and Seamless Interaction, with Improvised and Naturalistic subsets totaling 4,000 h. Training runs for 100 epochs with 32 segments per epoch and G = 16 completions on 32 H100 GPUs.
    - **E9:** result/experiment_result | Results and Analysis | medium
      locator:: Table 1, Moshi rows
      quote:: For Moshi, Table 1 reports that RL with Fisher changes pause Candor TOR from 0.528 to 0.417, backchannel TOR from 0.255 to 0.091, turn-taking latency from 0.162 to 0.121, and interruption latency from 1.377 to 0.461.
    - **E10:** result/experiment_result | Results and Analysis | medium
      locator:: Table 1, PersonaPlex rows
      quote:: For PersonaPlex, Table 1 reports that RL with Seamless changes pause Candor TOR from 0.444 to 0.356, backchannel TOR from 0.182 to 0.073, turn-taking latency from 0.219 to 0.086, and GPT-4o interruption score from 4.500 to 4.533.
    - **E11:** result/experiment_result | Results of Static Evaluation | medium
      locator:: Section 5.1
      quote:: Within both the Moshi and PersonaPlex families, RL training yields consistent improvements over the respective base models. TOR of pause handling decreases substantially, while latency and TOR of turn-taking simultaneously improve.
    - **E12:** result/experiment_result | Results of Interactive Evaluation | medium
      locator:: Table 2 and Section 5.2
      quote:: Table 2 evaluates real-time multi-turn dialogues. PersonaPlex with Seamless improves over PersonaPlex on Daily Turn 3.327 to 4.017, Correction Task 3.080 to 3.620, Entity Tracking Task 3.200 to 3.840, and Safety Task 3.260 to 3.280.
    - **E13:** ablation/ablation | Ablations | medium
      locator:: Table 3 and Section 5.3
      quote:: Removing the LLM Judge reward leads to the largest degradation across nearly all metrics. Table 3 reports that without the LLM reward, GPT-4o interruption score drops from 3.58 to 3.05 and Daily instruction-following drops from 2.50 to 2.18.
    - **E14:** limitation/limitation | Limitations | high
      locator:: Limitations
      quote:: The rule-based reward design for each interactivity axis requires manual engineering effort and may overlook other aspects of conversational dynamics. As the number of axes grows, this approach becomes increasingly difficult to scale.
    - **E15:** limitation/case_study | Limitations and Case Studies | medium
      locator:: Limitations; Appendix D.2
      quote:: Optimizing interactivity through RL can inadvertently degrade the model's safety behavior. Training on the Fisher dataset led to a decline in safety scores, as the cooperative interaction style of the training data conflicted with the ability to refuse or redirect harmful requests.
    - **E16:** result/experiment_result | Introduction and Appendix C | medium
      locator:: Footnote 1; Appendix C, Table 4
      quote:: The checkpoints of the models and audio samples are available on Hugging Face. Appendix C reports UTMOSv2 speech-quality scores and states that, for both Moshi and PersonaPlex, scores after RL remain comparable to the respective baselines.
