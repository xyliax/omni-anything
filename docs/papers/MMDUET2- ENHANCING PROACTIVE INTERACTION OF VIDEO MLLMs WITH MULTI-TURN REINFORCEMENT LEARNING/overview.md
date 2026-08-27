- **Title:** MMDuet2: Enhancing Proactive Interaction of Video MLLMs with Multi-Turn Reinforcement Learning
- **Summary:** MMDuet2 turns the question of when a streaming video assistant should speak into an ordinary text action and trains it with multi-turn rewards that favor early correct answers while penalizing spammy repetition.
- **Paper Type:** application
- **Venue:** arXiv preprint 2025
- **Authors:** Yueqian Wang (Wangxuan Institute of Computer Technology, Peking University); Songxiang Liu, Disong Wang, Nuo Xu, Guanglu Wan (Meituan); Huishuai Zhang, Dongyan Zhao (Wangxuan Institute of Computer Technology, Peking University; State Key Laboratory of General Artificial Intelligence)
- **Keywords:** video multimodal large language models, proactive interaction, streaming video question answering, multi-turn reinforcement learning, PAUC, GRPO
- ## Orientation
    - **Background:** A video multimodal large language model is a chatbot-like model that reads both text and video frames. In streaming use, frames arrive over time, so the model sees only the past and present, not the whole video at once.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A user asks a question while a video is playing, and the assistant should speak up when the video actually contains something worth answering, rather than waiting for the video to end or interrupting constantly.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** The right moment to answer is fuzzy: the needed evidence may appear gradually, scene boundaries are coarse, and speaking too early, too late, or too often all feel wrong to a user.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Make silence an explicit text choice, then reward the model for answers that become correct as early as possible without repeating itself.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a video multimodal large language model (Video MLLM) post-training paper about proactive interaction: a video assistant must decide not only what to answer, but whether now is the right moment to speak.
      claim_kind:: analyst_assessment
      evidence:: E1, E2
    - **One-Sentence Contribution:** MMDuet2 improves streaming video question answering by making the model choose between answering and emitting NO REPLY at each step, then training that choice with reinforcement learning (RL), meaning learning from scalar rewards rather than only fixed target outputs.
      evidence:: E1, E4, E7
    - **Mental Model:** Picture a tour guide watching a live video with you: every few moments the guide either says something useful about what just happened or deliberately stays quiet, and training rewards the guide for speaking early but not for interrupting with repeats.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is that the RL-trained model improves proactive benchmark scores while the ablations show why anti-repetition and in-span penalties are needed.
      evidence:: E9, E10, E12
        - Supports C1: ProactiveVideoQA WEB split; baseline MMDuet; Proactive Area Under Curve (PAUC), where higher means earlier and more correct answers, improves from 38.9 to 53.3 and duplicate proportion drops from 81.3 to 4.2; supported, with no variance reported.
          evidence:: E9
        - Supports C1: StreamingBench proactive output task; baseline MMDuet; accuracy improves from 29.44 to 34.69; supported, with evaluation repeat count not reported.
          evidence:: E10
        - Supports C3: reward ablation on WEB and EGO; baseline full MMDuet2 reward; removing the repetition reward raises duplicate proportion from 4.2 to 17.3 on WEB and from 8.1 to 31.9 on EGO; supported, but statistical uncertainty is not reported.
          evidence:: E12
    - **Main Caveat:** The results are promising but thin on robustness: tables report point estimates without error bars, the LLM-judge details for reward scoring are under-specified, and the model still struggles on surveillance-style and long egocentric videos.
      claim_kind:: analyst_assessment
      evidence:: E9, E14
- ## Argument Map
    - **Problem and Stakes:** The paper studies proactive interaction, where a video multimodal large language model (Video MLLM) watches an incoming visual stream and decides when to speak as well as what to say. The stake is real-time assistance: live analysis, surveillance, egocentric helpers, and social agents need timely responses rather than end-of-video answers.
      evidence:: E1, E2
    - **Prior Gap:** Prior proactive Video MLLMs usually made timing decisions with a predicted score and a manually chosen threshold, while supervised training needed exact reply timestamps that are expensive and ambiguous to annotate. The paper also positions existing reinforcement learning (RL) for video-language models as mostly not addressing real-time multi-turn interaction.
      evidence:: E2, E6, E17
    - **Key Insight:** The paper’s central insight is to recast the hidden timing decision as a visible dialogue action, NO REPLY, and train multi-turn rollouts with a reward shaped like an area under a correctness-over-time curve. This avoids needing a single annotated best timestamp while still preferring earlier correct responses.
      evidence:: E4, E6, E7
    - **Claims:** The paper makes four main falsifiable claims about proactive performance, the value of RL, reward-design necessity, and preservation of ordinary offline video understanding.
      evidence:: E1, E9, E11
        - C1: MMDuet2_rl improves proactive video interaction quality over open proactive baselines on the reported benchmark suite, especially on WEB, TV, VAD, and StreamingBench, while reducing duplicate replies compared with MMDuet; the EGO PAUC comparison is mixed because MMDuet has higher PAUC but extreme duplication.
          evidence:: E9, E10
        - C2: Multi-turn RL after supervised fine-tuning (SFT), meaning training first on target examples and then from rewards, improves the SFT-only model’s proactive timing and answer behavior.
          evidence:: E9, E10, E14
        - C3: The auxiliary repetition, in-span, and prefix penalties are necessary to prevent the PAUC-style reward from being exploited by redundant or irrelevant responses.
          evidence:: E7, E12
        - C4: The proactive post-training procedure mostly preserves offline video understanding performance relative to the authors’ Qwen2.5-VL 3B implementation baseline.
          evidence:: E11
- ## Mechanism and Design
    - **Core Mechanism:** At each user turn, the model receives a small number of video frames and optional text, then the assistant must either generate an answer or emit NO REPLY as a normal text output. RL uses Proactive Area Under Curve (PAUC), a metric that rewards high answer correctness earlier within a valid reply span, plus penalties for repeated, out-of-span, and prefix-copying replies.
      evidence:: E4, E7
    - **Data / Control Flow:** The data pipeline segments videos into scenes, captions scenes, uses a language model to generate questions and per-scene answers, and converts these into either one-question-many-answer or multi-question-many-answer proactive dialogues. Training then runs SFT with answers placed at the end of their spans, followed by short-span Group Relative Policy Optimization (GRPO), an RL method that compares multiple sampled outputs for the same prompt.
      evidence:: E3, E5, E8
    - **Design Decisions:** The design favors compatibility and reward shaping over architectural specialization: it uses ordinary chat messages for timing decisions, then compensates for the resulting tendency to over-speak with explicit reward penalties.
      claim_kind:: analyst_assessment
      evidence:: E4, E7, E12
        - Need: avoid threshold tuning and framework changes; choice: represent waiting as NO REPLY in the assistant stream; closest alternative: special timing modules or token-level stop/continue rules; tradeoff: more generate calls and extra context tokens.
          evidence:: E2, E4, E16
        - Need: build training targets without exact reply timestamps; choice: place SFT answers at the end of coarse reply timespans; tradeoff: avoids asking the model to answer before evidence appears but teaches late replies that RL must later correct.
          evidence:: E5, E6
        - Need: reward early useful speech without incentivizing spam; choice: weight PAUC slightly more than repetition, in-span, and prefix penalties; tradeoff: too little penalty yields redundant high-PAUC behavior, while too much penalty can suppress useful replies.
          evidence:: E7, E12
    - **Implementation Surface:** The model initializes from Qwen2.5-VL 3B, uses two-second frame sampling with two frames per user turn in training, and runs RL with four GRPO rollouts on short video spans using SGLang and verl. Reported resource use is 16 H800 GPUs for about 8 hours for SFT and 8 H800 GPUs for about 20 hours for RL.
      evidence:: E5, E8
- ## Evaluation and Evidence
    - **Setup:** The proactive evaluation covers ProactiveVideoQA splits WEB, EGO, TV, and VAD using PAUC and duplicate proportion, plus the StreamingBench proactive output task using accuracy. Offline retention is checked on Video-MME, MVBench, and LongVideoBench, with proactive baselines limited partly by availability of open inference code.
      evidence:: E9, E10, E11
    - **Claim-Evidence Matrix:** The evidence supports the main direction of the paper, but the strength varies by claim because results are single reported point estimates and some comparisons are complicated by duplicate-heavy baselines.
      claim_kind:: analyst_assessment
      evidence:: E9, E10, E12
        - C1: Supported on WEB, TV, VAD, and StreamingBench; partially supported on EGO because MMDuet2_rl has far lower duplicate proportion but lower PAUC than MMDuet.
          claim_kind:: analyst_assessment
          evidence:: E9, E10
        - C2: Supported by MMDuet2_rl outperforming MMDuet2_sft on ProactiveVideoQA splits and StreamingBench, and by training dynamics showing a move from low-frequency replies to higher PAUC behavior.
          evidence:: E9, E10, E14
        - C3: Strongly supported qualitatively by ablations where removing r_rep or r_in_span increases duplicate or uncontrolled response density, including EGO failure without r_in_span.
          evidence:: E12
        - C4: Supported by near-baseline offline benchmark numbers, though the comparison is to the authors’ reproduced Qwen2.5-VL 3B rather than only the original reported checkpoint.
          evidence:: E11
    - **Headline Results:** The headline result is not a clean universal win on every metric, but a practical improvement in earlier useful responses with dramatically less duplication than MMDuet on several splits.
      claim_kind:: analyst_assessment
      evidence:: E9, E10, E11
        - ProactiveVideoQA WEB: MMDuet2_rl versus MMDuet improves PAUC from 38.9 to 53.3 and reduces duplicate proportion from 81.3 to 4.2; no confidence intervals or repeat counts are reported.
          evidence:: E9
        - StreamingBench proactive output: MMDuet2_rl reaches 34.69 accuracy versus 29.44 for MMDuet, 25.34 for Dispider, and 1.96 for VideoLLM-Online; support is point-estimate only.
          evidence:: E10
        - Offline benchmarks: relative to the authors’ Qwen2.5-VL 3B reproduction, MMDuet2_rl is similar on Video-MME, MVBench, and LongVideoBench, with LongVideoBench moving from 53.1 to 52.7.
          evidence:: E11
    - **Ablations and Sensitivity:** The ablations show the reward is doing real control work: removing anti-repetition or in-span rewards can raise PAUC while making outputs much worse as interactions. Frame-rate sensitivity is also important: dense SFT sampling collapses to NO REPLY, while denser inference improves timing because the model gets more chances to decide.
      evidence:: E12, E13
    - **Reproducibility Gaps:** The paper provides a project homepage, model/training framework names, hardware, and many hyperparameters, but does not report statistical uncertainty, repeat counts, the exact LLM judge identity and prompts for reward scoring, or full dataset release details in the supplied text.
      claim_kind:: analyst_assessment
      evidence:: E1, E7, E8
- ## Technical Judgment
    - **What Holds Up:** The paper’s strongest technical move is aligning the training signal with the real interaction tradeoff: a reply is better if it is correct and arrives earlier, but only if it is not redundant or irrelevant. The reward ablations make the main failure mode visible, showing that PAUC alone can be gamed by over-answering.
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E12
    - **Where It May Fail:** MMDuet2 may be less reliable on long or hard-to-interpret streams: the paper reports poor VAD performance for all models and increasing repetition on longer EGO videos late in RL training. The NO REPLY-as-generation design is easy to implement but less token-efficient than the appendix’s proposed stop/continue format.
      claim_kind:: analyst_assessment
      evidence:: E9, E14, E16
    - **Relation to Other Work:** Compared with threshold-based proactive systems such as VideoLLM-Online and MMDuet, MMDuet2 moves timing into the language-model action space instead of tuning an external response score. Compared with recent RL-enhanced video-language models, its distinguishing axis is multi-turn real-time interaction rather than static video reasoning alone.
      evidence:: E2, E17
    - **Transferable Lesson:** A useful systems pattern is to turn an awkward control decision into an ordinary model output when ecosystem compatibility matters, then add reward terms for the predictable degenerate behaviors that this output space enables. Here, silence-as-text made proactive timing trainable in standard chat infrastructure, but required explicit anti-spam rewards.
      claim_kind:: analyst_assessment
      evidence:: E4, E7, E12
- ## Glossary
  collapsed:: true
    - video multimodal large language model: A language model that conditions on video frames as well as text, so it can answer questions or converse about video content.
    - proactive interaction: A streaming setting where the model decides when to respond during video playback, not only how to answer after a user turn.
    - supervised fine-tuning: Training a pretrained model on examples with target outputs; in this paper it teaches the chat format and initial proactive behavior before reward training.
    - reinforcement learning: Training from scalar rewards assigned to generated behavior rather than only from fixed target text; here it rewards early correct replies and penalizes bad speaking patterns.
    - Group Relative Policy Optimization: An RL optimization method that samples multiple outputs for the same input and updates the model using their relative rewards.
    - Proactive Area Under Curve: A proactive-video metric and reward shape that integrates answer correctness over time within a reply span, so earlier high-quality replies score better.
    - reply timespan: The interval in the video during which a certain ground-truth answer is considered appropriate; the paper avoids requiring a single exact timestamp inside it.
    - NO REPLY: The literal text output used by MMDuet2 when the assistant chooses not to answer at the current turn.
    - proactive dialogue types: 1QnA means one question with multiple possible answer turns across a video; nQnA means multiple questions and multiple answer streams in one dialogue.
    - auxiliary reward penalties: Extra reward terms that discourage duplicate replies, replies outside valid spans, and replies that copy a previous prefix before adding new content.
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/paper_statement | Abstract | high
      locator:: Abstract
      quote:: We train our model MMDuet2 on a dataset of 52k videos with two types of dialogues via SFT and RL. Experimental results demonstrate that MMDuet2 outperforms existing proactive Video MLLM baselines in response timing and quality, achieving state-of-the-art performance on the ProactiveVideoQA benchmark.
    - **E2:** gap/paper_statement | Introduction | high
      locator:: Section 1, prior methods and issues
      quote:: In previous works of proactive interaction... a video MLLM determines whether it should respond after a certain frame by predicting response probability scores... and compares the scores with a pre-defined threshold. However... A threshold must be manually set during inference, and the model may never reply or often reply with duplicated content if this threshold is not set properly.
    - **E3:** method/paper_statement | Dataset Construction | high
      locator:: Section 3 and Table 1
      quote:: The videos of our proposed dataset contain two major categories: web videos and ego-centric videos... Web Videos 50228... Ego Centic 2543... We prepare 2 different types of proactive dialogues: “one question, multiple answers” (1QnA) and “multiple questions, multiple answers” (nQnA), each type covers half the number of all videos.
    - **E4:** system_design/implementation_detail | Formulating Proactive Dialogue with Chat Template | high
      locator:: Section 4.1 and Figure 2
      quote:: The assistant can choose to output either a textual response or “NO REPLY” to indicate it does not want to reply right after this frame... a major advantage of the chat template used in MMDuet2 is that it formats the entire interaction process... into messages from the user or the assistant and is therefore compatible with almost all popular post-training and inference frameworks.
    - **E5:** implementation/implementation_detail | Supervised Fine-Tuning | high
      locator:: Section 4.2
      quote:: We use Qwen2.5-VL 3B... as initialization... The input frames are sampled at an interval of 2 seconds from the video and we use 128 tokens per frame, 2 frames per user turn. To build user-assistant conversations used in the SFT stage, we place model answers at the end of their reply timespans.
    - **E6:** insight/paper_statement | Motivation of Using RL | high
      locator:: Section 4.3.1
      quote:: Automatically annotating ground-truth response time has been an unsolved challenge... Although providing accurate ground truth reply times is difficult, it is much easier to determine which of the two given proactive interaction outputs is better. An ideal proactive interaction system should generate replies both correctly... and early.
    - **E7:** algorithm/implementation_detail | Reward Modeling | high
      locator:: Section 4.3.2
      quote:: The reward is inspired by the PAUC (Proactive Area Under Curve)... we made two minor modifications... Besides r_PAUC, we also use some additional reward to punish unwanted behaviors... Replication reward... In-span reward... Prefix reward... After some hyperparameter search we find that omega_PAUC = 3, omega_rep = 2, omega_in_span = 0.5, omega_pfx = 2 is good.
    - **E8:** implementation/implementation_detail | Training Details | high
      locator:: Section 4.3.3
      quote:: To alleviate this problem, in each step we only select a short span (from 20 to 60 seconds) from the video for training and provide ground truth model replies for the dialogue turns that happen before the selected span... We use GRPO... with a number of rollouts as 4, implemented with SGLang... and verl... conducted on 8 H800 GPUs and takes about 20 hours.
    - **E9:** result/experiment_result | Experiments on Proactive Benchmarks | medium
      locator:: Table 2 and surrounding text
      quote:: Table 2: Performance on ProactiveVideoQA. Metrics reported are PAUC (omega = 0.5) up / reply duplicate proportion down... MMDuet2_rl (Ours): WEB 53.3 / 4.2, EGO 33.6 / 8.1, TV 43.4 / 1.0, VAD 28.9 / 15.2... Results show that MMDuet2 outperforms existing proactive interaction models by a large margin.
    - **E10:** result/experiment_result | Experiments on Proactive Benchmarks | medium
      locator:: Table 5
      quote:: Table 5: Performance on Proactive Output task of Streaming-Bench. VideoLLM-Online 1.96; Dispider 25.34; MMDuet 29.44; MMDuet2_sft (Ours) 19.59; MMDuet2_rl (Ours) 34.69.
    - **E11:** result/experiment_result | Experiments on Offline Video-Text Benchmarks | medium
      locator:: Section 5.2 and Table 4
      quote:: After fine-tuning and reinforcement learning for enhancing proactive interaction, MMDuet2’s performance on offline video understanding benchmarks remains almost the same as the checkpoint before our post-training... Table 4... Qwen2.5-VL 3B dagger 66.5/57.3, 65.6, 53.1; MMDuet2_rl dagger 67.5/58.1, 66.4, 52.7.
    - **E12:** ablation/ablation | Ablation Studies | medium
      locator:: Section 5.3 and Table 6
      quote:: Results show that r_rep and r_in_span are indispensable: without any of these 2 rewards, the model generates more duplicated responses to achieve an unreasonably high PAUC metric... Table 6... MMDuet2 53.3/4.2/3.3 on WEB; -r_rep 55.5/17.3/4.9; -r_in_span 62.7/9.6/8.4; EGO -r_in_span FAIL.
    - **E13:** ablation/ablation | Ablation Studies | medium
      locator:: Section 5.3 and Table 7
      quote:: In SFT phase, when frame interval is set to 1 second, the model will collapse to always generating “NO REPLY”... In the RL phase, we found that setting different frame intervals does not have a significant impact... in the inference phase... reducing the frame interval from 2 seconds to 1 second leads to a significant performance improvement.
    - **E14:** limitation/paper_statement | Training Dynamics of the RL Process | medium
      locator:: Section 5.4 and Figure 5
      quote:: Stage 3... the model's performance on the [WEB] network video task stabilizes. However, on the [EGO] ego-centric video task which is longer and more challenging for content understanding, the model can have some generalization issues as we observe an increase in repetition.
    - **E15:** result/experiment_result | Experiments on Proactive Benchmarks | medium
      locator:: Inference Speed paragraph and Table 3
      quote:: Inference Speed. Here we report the actual inference speed... select 64 samples from the ProactiveVideoQA [WEB] task and test the inference wall time... Table 3... MMDuet 5.7 (3.4) reply turns, 2m27s; MMDuet2 3.3 (1.9), 2m52s.
    - **E16:** limitation/paper_statement | Appendix A: Discussion of Reply Timing Decision Methods | high
      locator:: Appendix A
      quote:: Here we describe a more efficient implementation of reply timing instead of generating “NO REPLY”... if the model chooses not to respond, no additional token will be added to the context... However, this requires introducing new rules into inference frameworks like SGLang or vLLM, which requires significant labor.
    - **E17:** prior_work/paper_statement | Related Works | high
      locator:: Section 2.2
      quote:: Reinforcement learning has begun to play a transformative role in post-training video-text multimodal language models... However, existing RL-enhanced VideoMLLMs have not explored real-time interaction or multi-turn dialogue, limiting their applicability in more interactive scenarios.
