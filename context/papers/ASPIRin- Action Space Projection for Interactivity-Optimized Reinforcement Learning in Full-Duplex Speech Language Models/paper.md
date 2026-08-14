                                         ASPIRin: Action Space Projection for Interactivity-Optimized Reinforcement
                                                     Learning in Full-Duplex Speech Language Models
                                         Chi-Yuan Hsiao1,2 , Ke-Han Lu1 , Yu-Kuan Fu3 , Guan-Ting Lin1 , Hsiao-Tsung Hung2 , Hung-yi Lee1
                                                                                          1
                                                                                      National Taiwan University
                                                                          2
                                                                              ASUS Open Cloud Infrastructure Software Center
                                                                                   3
                                                                                     NVIDIA AI Technology Center
                                              r12942086@ntu.edu.tw, d12942024@ntu.edu.tw, ifu@nvidia.com, daniel094144@gmail.com,
                                                                AlexHT Hung@asus.com, tlkagkb93901106@gmail.com


                                                                   Abstract                                  forcement Learning (RL) to explicitly optimize interactive be-




arXiv:2604.10065v1 [cs.CL] 11 Apr 2026
                                                                                                             haviors and temporal dynamics of SLMs [51–54]. The standard
                                         End-to-end full-duplex Speech Language Models (SLMs) re-            paradigm, utilizing algorithms like Group Relative Policy Op-
                                         quire precise turn-taking for natural interaction. However, op-     timization (GRPO) [55], applies reward signals directly to the
                                         timizing temporal dynamics via standard raw-token reinforce-        fine-grained semantic token policy. We identify a critical flaw
                                         ment learning (RL) degrades semantic quality, causing severe        in this unified approach: it forces the model to simultaneously
                                         generative collapse and repetition. We propose ASPIRin, an          solve for conversational timing and semantic generation using
                                         interactivity-optimized RL framework that explicitly decouples      the same limited optimization capacity. Consequently, standard
                                         when to speak from what to say. Using Action Space Projection,      GRPO becomes overly aggressive in minimizing response la-
                                         ASPIRin maps the text vocabulary into a coarse-grained binary       tency, leading to catastrophic generative degradation. As the
                                         state (active speech vs. inactive silence). By applying Group       model chases temporal rewards, it loses its linguistic ground-
                                         Relative Policy Optimization (GRPO) with rule-based rewards,        ing, resulting in severe repetition loops, high n-gram repetition,
                                         it balances user interruption and response latency. Empirical       and a complete breakdown of semantic coherence.
                                         evaluations show ASPIRin optimizes interactivity across turn-
                                                                                                                  To resolve this tension between interaction timing and se-
                                         taking, backchanneling, and pause handling. Crucially, isolat-
                                                                                                             mantic coherence in full-duplex speech language models, we
                                         ing timing from token selection preserves semantic coherence
                                                                                                             propose ASPIRin (Action Space Projection for Interactivity-
                                         and reduces the portion of duplicate n-grams by over 50% com-
                                                                                                             Optimized Reinforcement Learning). ASPIRin decouples when
                                         pared to standard GRPO, effectively eliminating degenerative
                                                                                                             to speak from what to say by projecting the vast text vocabulary
                                         repetition.
                                                                                                             into a coarse-grained binary state: active speech (non-padding
                                         Index Terms: full-duplex, speech language model, reinforce-
                                                                                                             tokens) versus inactive silence (padding tokens). This pro-
                                         ment learning, dialogue system
                                                                                                             jected binary policy is optimized via GRPO, allowing indepen-
                                                                                                             dent learning of interaction timing without compromising lan-
                                                             1. Introduction                                 guage modeling capabilities. A joint rule-based reward, derived
                                         Traditional spoken dialogue systems have long relied on a cas-      from continuous ASR timestamps, balances prompt responsive-
                                         caded architecture, pipelining audio through independent Auto-      ness against interruption penalties. Evaluations on Full-Duplex-
                                         matic Speech Recognition (ASR) [1–9], Large Language Mod-           Bench show that ASPIRin substantially improves interaction
                                         els (LLMs) [10–16], and Text-to-Speech (TTS) [17–25] mod-           timing while fully preserving utterance quality.
                                         ules. While effective for basic information retrieval, this dis-         In summary, our main contributions are as follows:
                                         jointed pipeline introduces compounding latency and enforces        • A Novel Interactivity-Optimized RL Framework: We pro-
                                         a rigid, unnatural interaction paradigm. Recent advancements          pose ASPIRin, which explicitly decouples interaction timing
                                         have consolidated these modules into end-to-end Speech Lan-           from semantic generation in full-duplex Speech Language
                                         guage Models (SLMs) [26–42]. However, most SLMs remain                Models. By introducing Action Space Projection, we map
                                         fundamentally turn-based, operating in a half-duplex mode that        the fine-grained text vocabulary into a coarse-grained binary
                                         requires the user to yield the floor before the model can process     state (active speech vs. inactive silence), introducing a novel
                                         the input and begin generating a response.                            design space for optimization.
                                              To achieve natural human-machine interaction, the field
                                                                                                             • Superior Full-Duplex Temporal Dynamics: We demon-
                                         is now shifting toward Full-Duplex Speech Language Models
                                                                                                               strate that optimizing this projected binary policy with rule-
                                         (FD-SLMs) [43–45], such as Moshi [46], which process contin-
                                                                                                               based conversational rewards effectively balances prompt re-
                                         uous audio streams and generate interleaved speech in real time.
                                                                                                               sponsiveness with low interruption risk. ASPIRin outper-
                                         In these dynamic environments, listening and speaking are not
                                                                                                               forms standard GRPO on Full-Duplex-Bench across diverse
                                         mutually exclusive; models must simultaneously handle con-
                                                                                                               real-time scenarios, including pause handling, backchannel-
                                         versational pauses, deliver timely backchannels, and navigate
                                                                                                               ing, and user interruption.
                                         user interruptions, while managing overlaps such as background
                                         speech and addressee detection [47]. Yet, equipping these mod-      • Mitigation of Generative Collapse: ASPIRin decouples
                                         els with the precise temporal dynamics necessary for conversa-        timing from token selection, preserves semantic coherence,
                                         tional fluency and responsive interaction remains a significant       and reduces n-gram repetition by over 50% relative to stan-
                                         open challenge [48–50].                                               dard GRPO, thereby eliminating degenerative repetition aris-
                                              Recent alignment efforts have naturally turned to Rein-          ing from reward hacking on temporal rewards.
                                         Inactive/Padding Logit          Active/Non-padding Logit        Padding Token       Non-padding Token
                                      Inactive                     State Policy Optimization             User Input
                                            Active

                       State Logits                                               ...
                       Action                                                                                                                   Rule-based
                                                                                                         FD-SLM       > 1s
                                                                                                                                 Interruption
                   Space Projection         Sum                                                                                                  Rewards
                 Output Text Logits                                               ...


                                                                                                         Response Latency > 1s
                                                                FD-SLM

                                            Sum
                 Input Audio Tokens                                               ...
                                              Sample                                                                             Good Response
               Output Audio Tokens                                                ...
                 Output Text Tokens          <PAD>         <PAD>            (Hi) ...        (!)
                                        Step 0         Step 1           Step 2          Step N
                                                                  (a)                                                            (b)
Figure 1: Overview of the ASPIRin framework. (a) Action Space Projection & State Policy Optimization: The fine-grained text
vocabulary is decoupled into a coarse-grained binary state (Active Speech vs. Inactive Silence) by grouping and summing non-padding
and padding logits. This projected state policy is then explicitly optimized. (b) Rule-Based Rewards: The state policy is guided
by continuous temporal constraints that penalize user interruption and excessive response latency. This explicit decoupling allows
ASPIRin to master conversational timing without compromising semantic generation.

                     2. Methodology                                                             Substituting this projected policy into the GRPO objective
                                                                                           for a group of sampled outputs {Y1 , . . . , YG } yields:
As illustrated in Figure 1, we propose ASPIRin, an alignment
framework designed to optimize the temporal dynamics of full-
                                                                                                                                         |si |
                                                                                                                                       G X
duplex speech models parameterized by θ. Unlike standard ap-                                                                 1         X
proaches that treat audio generation as a unified sequence task,                                  LASPIRin (θ) = − PG
ASPIRin decouples when to speak from what to say by replac-                                                              i=1 |si | i=1 t=1
                                                                                                   "                                                       #   (3)
ing fine-grained token optimization with a coarse-grained bi-                                           πθ′ (si,t |x<t , si,<t )                 ′ ′ 
nary action policy.                                                                                                                 Âi,t − βDKL πθ ||πref
                                                                                                       πθ′ old (si,t |x<t , si,<t )
2.1. Action Space Projection & State Policy Optimization                                                ′
                                                                                                Here, πref   is the reference model’s projected state proba-
Given a continuous stream of user audio input X and gener-                                 bility, and Âi,t is the advantage computed from rule-based re-
ated token sequences, standard models use text tokens to guide                             wards.
both semantic content and interaction timing [44–46]. To ex-
plicitly optimize turn-taking, we partition the vocabulary Vtext                           2.2. Rule-Based Reward Modeling
into Padding (Vpad ) and Non-padding (Vnon-pad ) sets. For any                             To guide this optimization, we design a reward function
generated token yt , we define a binary action state st = I(yt ∈                           R(S, U ) based on explicit conversational constraints, as con-
Vnon-pad ), where st ∈ {0, 1} represents Inactive Silence and Ac-                          ceptualized in Figure 1b. User voice activity U is defined as
tive Speech, respectively. This projects the raw token sequence                            continuous time intervals obtained via ASR timestamps. Con-
into a binary state sequence S.                                                            currently, the model’s action sequence S is segmented into K
      While standard GRPO optimizes the fine-grained token pol-                            discrete utterances. Assuming each token represents ∆t sec-
icy πθ (yt |x<t , y<t ), penalizing specific tokens for timing er-                         onds, we map these to continuous intervals and formulate two
rors is inefficient. Instead,as depicted in Figure 1a, we introduce                        rules:
Action Space Projection to construct and optimize a coarse-                                      Interruption Score (Rint ): Penalizes speaking while the
grained state policy πθ′ . Let zθ (v|x<t , s<t ) denote the raw out-                       user is active. Overlap duration ok is the time a model utter-
put logit for token v. We first compute the projected state logit                          ance              with any user utterance. The score is Rint =
zθ′ (st |x<t , s<t ) for the active and inactive states by summing                          1
                                                                                                Pintersects
                                                                                                  K
                                                                                           K      k=1 I(ok ≤ τint ), representing the proportion of utterances
the corresponding token logits:                                                            where overlap is below a tolerance threshold τint .
                                                                                                 Response Score (Rre ): Encourages promptness. Latency
                                      X                                                    lk is the time elapsed between the model’s utterance start and
           zθ′ (st |x<t , s<t ) =           zθ (v|x<t , s<t )               (1)            the end of thePmost recent preceding user utterance. The score
                                    v∈Vst                                                               1    K
                                                                                           is Rre = K        k=1 I(lk ≤ τre ), bounding acceptable delay by
                                                                                           τre .
    where V0 = Vpad and V1 = Vnon-pad . The projected state                                      To jointly optimize for low interruption risk and responsive-
policy πθ′ (st |x<t , s<t ) is then obtained by applying the soft-                         ness, the final sequence reward is the product of the two:Rtotal =
max function over these binary state logits:                                               Rint · Rre . To compute the advantage Âi,t for Equation (3),
                                                                                           Rtotal is normalized across the G samples such that Âi,t =
                                                                                           (Rtotal,i −µR )/σR , where µR and σR are the mean and standard
                               exp(zθ′ (st |x<t , s<t ))
    πθ′ (st |x<t , s<t ) = P                 ′
                                                                            (2)            deviation of Rtotal . By optimizing against this joint distribution,
                             s∈{0,1} exp(zθ (s|x<t , s<t ))                                ASPIRin effectively aligns model interactivity.
Table 1: Performance comparison of full-duplex models. We evaluate our proposed ASPIRin against Moshi baselines, Standard
SFT, and Standard GRPO across four conversational dimensions: Pause Handling, Backchanneling, Smooth Turn-Taking, and User
Interruption. Arrows (↓ / ↑) indicate whether lower or higher values indicate better performance. Latency is measured in seconds.

         Dimension                      Pause Handling            Backchannel           Smooth Turn Taking           User Interruption
         Data                          Synthetic Candor         ICC                   Candor                 Synthetic
         Metric                        TOR (↓) TOR (↓) TOR (↓) Freq (↑) JSD (↓) TOR (↑) Latency (↓) TOR (↑) GPT-4o(↑) Latency (↓)
         Moshi (w/o 3s prompt delay)    0.985    0.980    1.000      0.001      0.957   0.941      0.265     1.000       0.765       0.257
         Moshi                          0.467    0.495    0.436      0.044      0.705   0.748      0.161     0.901       3.894       1.159
         Standard SFT                   0.540    0.6389   0.927      0.0212     0.870   0.723      0.355     0.625       0.440       1.970
         Standard GRPO                  0.642    0.704    0.709       0.030     0.854   0.857      0.153     0.953       3.247       0.614
         ASPIRin (Ours)                 0.482    0.486    0.364       0.045     0.752   0.765      0.273     0.941       3.734       0.992

                     3. Experiments                                                              4. Results and Analysis
3.1. Experimental Setup                                                          4.1. Main Results

Training Data. We utilize a 43-hour in-house dataset of                          Establishing a Strong Baseline. We establish a strong heuris-
natural conversational speech (approx. 1,300 two-minute,                         tic baseline by introducing a 3-second prompt delay to the base
dual-channel clips). This dataset was collected with ex-                         Moshi model in Table 1. This simple modification yields sub-
plicit speaker consent and rigorously anonymized to en-                          stantial improvements: Takeover Rate (TOR) drops by 49% –
sure privacy compliance. We process the audio using the                          57% in pause handling and backchanneling scenarios, while the
nvidia/parakeet-tdt-0.6b-v3 ASR model [9] to ex-                                 GPT-4o semantic rating jumps by 3.1 in user interruption tasks.
tract precise utterance timestamps for reward modeling, apply-                   Despite minor trade-offs—such as a 10% – 20% TOR decrease
ing a density filter to discard examples where active speech con-                and a 0.9-second latency increase during turn-taking and inter-
stitutes less than 50% of the duration.                                          ruptions, the overall gains remain highly significant. We use
                                                                                 this delayed-prompt Moshi as our primary baseline and apply
     Evaluation Benchmark. To evaluate full-duplex inter-                        this 3-second heuristic across all subsequent experiments to en-
activity, we employ Full-Duplex-Bench [56], which system-                        sure rigorous comparison.
atically tests temporal dynamics across four critical scenar-
ios: Turn-Taking (smooth handoffs), Backchanneling (timely                            The Limitations of Standard SFT. Standard Supervised
acknowledgments), Pause Handling (respecting silences), and                      Fine-Tuning (SFT) fails to learn the temporal dynamics re-
User Interruption (recovering from barge-ins).                                   quired for full-duplex interaction and actively degrades base-
                                                                                 line performance. Across pause handling and backchanneling,
     Models and Baselines. We select Moshi as our founda-                        TOR worsens (increases) by 7% – 50%, while turn-taking and
tional end-to-end base model and compare ASPIRin against                         user interruption TOR drop by 2% – 28%. Furthermore, SFT
two primary baselines: Standard SFT (the base model fine-                        induces severe semantic degradation, evidenced by a 3.4-point
tuned on our dataset via supervised next-token prediction) and                   drop in the GPT-4o rating during interruptions. This suggests
Standard GRPO (the base model optimized via updates to the                       that SFT forces the model to over-index on semantic genera-
fine-grained raw token policy rather than our proposed coarse-                   tion, causing it to hallucinate irrelevant content while entirely
grained state policy).                                                           neglecting conversational timing.
     Training Details. All models are trained on 8 NVIDIA                             The Aggressiveness of Standard GRPO. While standard
V100 GPUs for 3 epochs using the AdamW optimizer (learn-                         GRPO optimizes the raw token policy to increase the model’s
ing rate 1e-5, per-GPU batch size 1). During SFT and GRPO                        eagerness to interact, it fails to promote conversational restraint.
phases, we apply LoRA [57] (r = 256) to all linear layers while                  It improves turn-taking and user interruption (TOR increases by
fully training the temporal transformer embeddings. For our                      5% – 11%; latency drops by 0.01 to 0.5 seconds), but becomes
state optimization phase, we set the GRPO group size to G = 2                    overly aggressive elsewhere. Backchanneling and pause han-
and the KL penalty to β = 0.001. Reward thresholds are set                       dling deteriorate significantly, with TOR rising by 18% – 27%.
to τint = 1.0s (interruption tolerance) and τre = 1.0s (latency                  GRPO essentially encourages the model to speak continuously
limit).                                                                          without yielding the floor to the user, while also causing a 0.6-
                                                                                 point drop in semantic coherence.
3.2. Evaluation Metrics                                                               The Success of ASPIRin. Our proposed method success-
                                                                                 fully balances the latency-interruption trade-off while preserv-
We evaluate models across two dimensions to ensure interac-                      ing semantic quality. Compared to the strong Moshi baseline,
tivity improvements do not compromise semantic coherence.                        ASPIRin delivers well-rounded improvements: it appropriately
Temporal Metrics: Using Full-Duplex-Bench, we measure                            reduces TOR by 1% – 7% in pause handling and backchan-
Takeover Rate (TOR, the proportion of successful turn-takes.                     neling, while boosting it by 2% – 4% in turn-taking and user
The optimal TOR direction is task-dependent.) and response                       interruption. Interruption latency also drops by 0.2 seconds.
latency, extracting timestamps via parakeet-tdt ASR for                          The trade-offs are negligible (e.g., a mere 0.16 drop in GPT-4o
accuracy. Semantic Metrics: To assess generation quality, we                     score and a 0.1-second latency increase in turn-taking). By ab-
employ GPT-4o as an automated evaluator to score responses on                    stracting raw tokens into binary active/inactive states, ASPIRin
a 1–5 scale. We also compute the portion of duplicate n-grams                    explicitly teaches the model when to speak and when to yield.
(seq-rep-n) [58] and Self-BLEU (computed using 4-grams) [59]                     Ultimately, decoupling timing from content prevents the severe
on ASR transcriptions to explicitly detect and penalize repeti-                  semantic degradation seen in SFT and standard GRPO, yielding
tive generation patterns.                                                        a highly interactive and articulate full-duplex model.
0.9                                          1.2
0.8
                                                                                                 Table 2: Qualitative examples from the ”User Interruption”
                                               1
0.7
0.6                                          0.8
                                                                                                 task. While the Standard SFT baseline hallucinates irrelevant
0.5
                                             0.6
                                                                                                 vocabulary and Standard GRPO suffers from severe repetitive
0.4
0.3                                          0.4                                                 loops, ASPIRin successfully maintains semantic coherence and
0.2
0.1
                                             0.2                                                 contextually appropriate responses, achieving parity with the
 0
      1   101   201 Step   301   401   501
                                               0
                                                    1       101   201          301   401   501
                                                                                                 base Moshi model.
                                                                        Step


  (a) Interruption Score (GRPO)                         (b) Response Score (GRPO)                                   Example
0.9                                          0.45
0.8                                           0.4                                                Input Question     By the way, how about we discuss exercise routines in-
0.7                                          0.35
0.6                                           0.3
                                                                                                                    stead?
0.5                                          0.25
0.4                                           0.2
                                                                                                 Moshi              Sure, I’m good with that. What’s your routine look like?
0.3                                          0.15                                                                   I’ve been trying to incorporate more cardio and strength
0.2                                           0.1                                                                   framing into my routine. I’ve been doing a mix of running.
                                             0.05
0.1
                                               0
                                                                                                                    (Rating: 4)
 0
                                                    1       101   201          301   401   501
      1   101   201 Step   301   401   501                              Step                     Standard SFT       Joyful Veal Eh is beneficial But I work in diverse inventions,
                                                                                                                    so this actual definite divention of grapefish individual ...
 (c) Interruption Score (ASPIRin)                   (d) Response Score (ASPIRin)                                    (Rating: 0)
                                                                                                 Standard GRPO Hey, so I was just thinking, I have this friend, you know,
Figure 2: Comparison of training reward dynamics between                                                       who has a dog and you know, he says that his dog is uh you
standard GRPO and ASPIRin.                                                                                     know really good you know at tracking and you know I was
                                                                                                               just wondering you know what you know what kind of you
                                                                                                               know ... (Rating: 0)
                                                                                                 ASPIRin (Ours)     Sure, that sounds good. Let’s start with the basic question.
4.2. Analysis of Reward Dynamics                                                                                    What are some of the most common types of exercises?
                                                                                                                    Okay, so there are a lot of different types of exercises, but
Standard GRPO and ASPIRin both display an upward trend in                                                           some of the most common ones are ... (Rating: 5)
total reward throughout training, yet their Interruption Score
dynamics differ dramatically. As shown in Figures 2a and 2c,
standard GRPO exhibits severe instability, featuring rapid oscil-                                Table 3: Evaluation of degenerative repetition using seq-rep-n
lations and a consistent downward trend that signals clear degra-                                and Self-BLEU. By isolating timing optimization from semantic
dation, while ASPIRin preserves stable Interruption Score val-                                   token selection, ASPIRin effectively mitigates the degenerative
ues throughout the training process (Figure 2c) without observ-                                  repetition loops observed in standard GRPO, reducing 2-gram
able degradation. This problematic behavior in standard GRPO                                     and 3-gram repetition by over 50%.
severely undermines the reliability of using loss or total reward
convergence as a criterion for terminating training.                                                                               seq-rep-n
                                                                                                   Metric                                                     Self-BLEU (↓)
     The Interruption Score trajectories explain the main behav-                                                    1-gram (↓) 2-gram (↓) 3-gram (↓)
ioral gaps. Standard GRPO overprioritizes response scores, ig-
                                                                                                   Standard GRPO       0.303         0.117         0.072           0.369
noring interruption costs and causing severe TOR degradation                                       ASPIRin (Ours)      0.202         0.054         0.029           0.343
in pauses and backchannels. ASPIRin, which advances more
conservatively, balances both constraints and delivers stable
TOR gains. This advantage stems directly from Action Space                                       overall Self-BLEU score from 0.369 to 0.343. These findings
Projection: mapping to a binary “speak or not” decision con-                                     confirm that isolating timing optimization from semantic token
centrates learning on timing alone. The model thus discovers                                     selection prevents the degenerative repetition characteristic of
that silence can be rewarding, enabling effective full-duplex op-                                standard raw-token RL.
timization.

4.3. Analysis of Semantic Quality and Repetition
                                                                                                                          5. Conclusion
To investigate the discrepancies in GPT-4o semantic ratings,                                     We introduced ASPIRin, an interactivity-optimized reinforce-
we qualitatively analyze examples from the ”User Interrup-                                       ment learning framework resolving the tension between tem-
tion” task (Table 2). Both the base Moshi model and AS-                                          poral dynamics and semantic coherence in full-duplex SLMs.
PIRin produce contextually appropriate responses and consis-                                     While standard GRPO burdens fine-grained token policies and
tently receive ratings between 4 and 5. In stark contrast, stan-                                 suffers from aggressive, repetitive generation, ASPIRin utilizes
dard GRPO fails completely. Its outputs are not only meaning-                                    Action Space Projection to map vocabulary into a binary ac-
less but also heavily affected by repetitive patterns, which is a                                tive/inactive state. Optimizing this coarse-grained policy with
well-documented symptom of generative degradation [58, 59].                                      rule-based rewards successfully balances prompt responsive-
     To quantify this degradation, we measure the severity of                                    ness with low interruption risk. Evaluations confirm ASPIRin
repetition using the portion of duplicate n-grams (seq-rep-                                      outperforms standard GRPO across diverse conversational sce-
n) and Self-BLEU for assessing intra-sequence repetition and                                     narios without sacrificing base linguistic quality.
inter-sample diversity, respectively. The corresponding quan-                                         Future work will investigate more expressive action spaces
titative results are presented in Table 3. The empirical met-                                    beyond the current binary “speak or not” decision. For in-
rics perfectly align with our qualitative observations: standard                                 stance, we can distinguish backchannel utterances (e.g., “uh-
GRPO exhibits severe generative collapse, yielding high repe-                                    huh”) as a dedicated class separate from full responses or in-
tition scores across all metrics. Crucially, ASPIRin effectively                                 terruptions. Such multi-class or hierarchical designs could en-
mitigates this issue, generating significantly more diverse con-                                 able finer-grained control over timing and content, facilitating
tent. Specifically, ASPIRin cuts 2-gram and 3-gram overlap by                                    the development of more natural and interactive full-duplex sys-
more than half compared to standard GRPO, and reduces the                                        tems.
         6. Generative AI Use Disclosure                                  [10] OpenAI et al., “Gpt-4o system card,” 2024. [Online]. Available:
                                                                               https://arxiv.org/abs/2410.21276
During the preparation of this work, the authors used Generative
AI tools exclusively for editing and polishing the manuscript to          [11] G. Team, R. Anil, S. Borgeaud, J.-B. Alayrac, J. Yu, R. Soricut,
                                                                               J. Schalkwyk, A. M. Dai, A. Hauth, K. Millican et al., “Gemini:
improve overall readability. Generative AI was not used to pro-                a family of highly capable multimodal models,” arXiv preprint
duce any significant portion of the manuscript’s original con-                 arXiv:2312.11805, 2023.
tent, ideas, or research findings. All co-authors consent to this
                                                                          [12] G. Comanici, E. Bieber, M. Schaekermann, I. Pasupat,
submission, take full responsibility and accountability for the
                                                                               N. Sachdeva, I. Dhillon, M. Blistein, O. Ram, D. Zhang, E. Rosen
final content of this paper, and confirm that no Generative AI                 et al., “Gemini 2.5: Pushing the frontier with advanced reasoning,
tool is listed as a co-author.                                                 multimodality, long context, and next generation agentic capabil-
                                                                               ities,” arXiv preprint arXiv:2507.06261, 2025.
                 7. Acknowledgements                                      [13] J. Bai, S. Bai, Y. Chu, Z. Cui, K. Dang, X. Deng, Y. Fan, W. Ge,
                                                                               Y. Han, F. Huang et al., “Qwen technical report,” arXiv preprint
We thank the ASUS Open Cloud Infrastructure Software Center                    arXiv:2309.16609, 2023.
for providing the essential resources that supported this work.
We are also grateful to Steve Chung-Cheng Chen, Tsung-Ying                [14] A. Grattafiori, A. Dubey, A. Jauhri, A. Pandey, A. Kadian, A. Al-
                                                                               Dahle, A. Letman, A. Mathur, A. Schelten, A. Vaughan et al.,
Yang, Jen-Hao Cheng, and Dau-Cheng Lyu for their insight-                      “The llama 3 herd of models,” arXiv preprint arXiv:2407.21783,
ful discussions and feedback. Additionally, this research was                  2024.
supported by the National Center for High-Performance Com-
                                                                          [15] A. Liu, B. Feng, B. Xue, B. Wang, B. Wu, C. Lu, C. Zhao,
puting (NCHC) of the National Applied Research Laboratories                    C. Deng, C. Zhang, C. Ruan et al., “Deepseek-v3 technical re-
(NARLabs), Taiwan, whose advanced infrastructure and aca-                      port,” arXiv preprint arXiv:2412.19437, 2024.
demic resources were instrumental to the completion of this
                                                                          [16] DeepSeek-AI, “Deepseek-r1: Incentivizing reasoning capability
study.
                                                                               in llms via reinforcement learning,” 2025. [Online]. Available:
                                                                               https://arxiv.org/abs/2501.12948
                        8. References                                     [17] Z. Du, Q. Chen, S. Zhang, K. Hu, H. Lu, Y. Yang, H. Hu,
 [1] A. Radford, J. W. Kim, T. Xu, G. Brockman, C. McLeavey,                   S. Zheng, Y. Gu, Z. Ma et al., “Cosyvoice: A scalable multi-
     and I. Sutskever, “Robust speech recognition via large-                   lingual zero-shot text-to-speech synthesizer based on supervised
     scale weak supervision,” 2022. [Online]. Available: https:                semantic tokens,” arXiv preprint arXiv:2407.05407, 2024.
     //arxiv.org/abs/2212.04356                                           [18] Z. Du, Y. Wang, Q. Chen, X. Shi, X. Lv, T. Zhao, Z. Gao,
 [2] X. Shi, X. Wang, Z. Guo, Y. Wang, P. Zhang, X. Zhang, Z. Guo,             Y. Yang, C. Gao, H. Wang et al., “Cosyvoice 2: Scalable stream-
     H. Hao, Y. Xi, B. Yang, J. Xu, J. Zhou, and J. Lin, “Qwen3-asr            ing speech synthesis with large language models,” arXiv preprint
     technical report,” arXiv preprint arXiv:2601.21337, 2026.                 arXiv:2412.10117, 2024.
 [3] L.-H. Tseng, Y.-K. Fu, H.-J. Chang, and H.-y. Lee, “Mandarin-        [19] Z. Du, C. Gao, Y. Wang, F. Yu, T. Zhao, H. Wang, X. Lv,
     english code-switching speech recognition with self-supervised            H. Wang, C. Ni, X. Shi et al., “Cosyvoice 3: Towards in-the-
     speech representation models,” arXiv preprint arXiv:2110.03504,           wild speech generation via scaling-up and post-training,” arXiv
     2021.                                                                     preprint arXiv:2505.17589, 2025.
 [4] L.-H. Tseng, E.-P. Hu, C.-H. Chiang, Y. Tseng, H.-y. Lee,            [20] H. Hu, X. Zhu, T. He, D. Guo, B. Zhang, X. Wang, Z. Guo,
     L.-s. Lee, and S.-H. Sun, “Reborn: Reinforcement-learned                  Z. Jiang, H. Hao, Z. Guo, X. Zhang, P. Zhang, B. Yang, J. Xu,
     boundary segmentation with iterative training for unsupervised            J. Zhou, and J. Lin, “Qwen3-tts technical report,” arXiv preprint
     asr,” in Advances in Neural Information Processing Systems,               arXiv:2601.15621, 2026.
     A. Globerson, L. Mackey, D. Belgrave, A. Fan, U. Pa-
     quet, J. Tomczak, and C. Zhang, Eds., vol. 37. Curran                [21] C. Wang, S. Chen, Y. Wu, Z. Zhang, L. Zhou, S. Liu, Z. Chen,
     Associates, Inc., 2024, pp. 129 357–129 383. [Online]. Avail-             Y. Liu, H. Wang, J. Li et al., “Neural codec language mod-
     able: https://proceedings.neurips.cc/paper files/paper/2024/file/         els are zero-shot text to speech synthesizers,” arXiv preprint
     e99ed1162e984a5f08cb57ecde2d2231-Paper-Conference.pdf                     arXiv:2301.02111, 2023.
 [5] C.-K. Yang, K.-P. Huang, K.-H. Lu, C.-Y. Kuan, C.-Y. Hsiao, and      [22] S. Chen, S. Liu, L. Zhou, Y. Liu, X. Tan, J. Li, S. Zhao, Y. Qian,
     H.-Y. Lee, “Investigating zero-shot generalizability on mandarin-         and F. Wei, “Vall-e 2: Neural codec language models are hu-
     english code-switched asr and speech-to-text translation of recent        man parity zero-shot text to speech synthesizers,” arXiv preprint
     foundation models with self-supervision and weak supervision,”            arXiv:2406.05370, 2024.
     in 2024 IEEE International Conference on Acoustics, Speech, and
                                                                          [23] E. Casanova, K. Davis, E. Gölge, G. Göknar, I. Gulea, L. Hart,
     Signal Processing Workshops (ICASSPW), 2024, pp. 540–544.
                                                                               A. Aljafari, J. Meyer, R. Morais, S. Olayemi, and J. We-
 [6] C.-K. Yang, K.-P. Huang, and H.-Y. Lee, “Do prompts really                ber, “XTTS: a Massively Multilingual Zero-Shot Text-to-Speech
     prompt? exploring the prompt understanding capability of whis-            Model,” in Interspeech 2024, 2024, pp. 4978–4982.
     per,” in 2024 IEEE Spoken Language Technology Workshop
     (SLT), 2024, pp. 1–8.                                                [24] C.-J. Hsu et al., “Breezyvoice: Adapting tts for taiwanese man-
                                                                               darin with enhanced polyphone disambiguation–challenges and
 [7] S.-S. Huang, K.-P. Huang, A. T. Liu, and H.-Y. Lee, “Enhanc-              insights,” arXiv preprint arXiv:2501.17790, 2025.
     ing multilingual asr for unseen languages via language embedding
     modeling,” in ICASSP 2025-2025 IEEE International Conference         [25] C.-J. Hsu, C.-S. Liu, M.-H. Chen, M. Chen, P.-C. Hsu, Y.-C. Chen,
     on Acoustics, Speech and Signal Processing (ICASSP). IEEE,                and D.-S. Shiu, “The breeze 2 herd of models: Traditional chinese
     2025, pp. 1–5.                                                            llms based on llama with vision-aware and function-calling capa-
                                                                               bilities,” arXiv preprint arXiv:2501.13921, 2025.
 [8] C.-K. Chou, C.-J. Hsu, H.-L. Chung, L.-H. Tseng, H.-C. Cheng,
     Y.-K. Fu, K. P. Huang, and H.-Y. Lee, “A self-refining frame-        [26] C.-K. Yang et al., “Building a taiwanese mandarin spoken lan-
     work for enhancing asr using tts-synthesized data,” arXiv preprint        guage model: A first attempt,” arXiv preprint arXiv:2411.07111,
     arXiv:2506.11130, 2025.                                                   2024.
 [9] M. Sekoyan et al., “Canary-1b-v2 & parakeet-tdt-0.6b-v3:             [27] C.-Y. Hsiao et al., “Analyzing Mitigation Strategies for Catas-
     Efficient and high-performance models for multilingual asr and            trophic Forgetting in End-to-End Training of Spoken Language
     ast,” 2025. [Online]. Available: https://arxiv.org/abs/2509.14128         Models,” in Interspeech 2025, 2025, pp. 3234–3238.
[28] K.-H. Lu, Z. Chen, S.-W. Fu, H. Huang, B. Ginsburg, Y.-C. F.           [45] R. Roy, J. Raiman, S. gil Lee, T.-D. Ene, R. Kirby, S. Kim,
     Wang, and H.-y. Lee, “Desta: Enhancing speech language models               J. Kim, and B. Catanzaro, “Personaplex: Voice and role control
     through descriptive speech-text alignment,” in Interspeech 2024,            for full duplex conversational speech models,” 2026. [Online].
     2024, pp. 4159–4163.                                                        Available: https://arxiv.org/abs/2602.06053
[29] K.-H. Lu et al., “Developing instruction-following speech lan-         [46] A. Défossez, L. Mazaré, M. Orsini, A. Royer, P. Pérez, H. Jégou,
     guage model without speech instruction-tuning data,” in ICASSP              E. Grave, and N. Zeghidour, “Moshi: a speech-text foundation
     2025 - 2025 IEEE International Conference on Acoustics, Speech              model for real-time dialogue,” arXiv preprint arXiv:2410.00037,
     and Signal Processing (ICASSP), 2025, pp. 1–5.                              2024.
[30] K.-H. Lu, Z. Chen, S.-W. Fu, C.-H. H. Yang, J. Balam, B. Gins-         [47] G.-T. Lin, S.-Y. S. Kuan, J. Shi, K.-W. Chang, S. Arora,
     burg, Y.-C. F. Wang, and H.-Y. Lee, “Desta2.5-audio: Toward                 S. Watanabe, and H. yi Lee, “Full-duplex-bench-v2: A
     general-purpose large audio language model with self-generated              multi-turn evaluation framework for duplex dialogue systems
     cross-modal alignment,” arXiv preprint arXiv:2507.02768, 2025.              with an automated examiner,” 2025. [Online]. Available:
                                                                                 https://arxiv.org/abs/2510.07838
[31] Y.-X. Lin et al., “A preliminary exploration with gpt-4o voice
     mode,” arXiv preprint arXiv:2502.09940, 2025.                          [48] C.-K. Yang et al., “Towards holistic evaluation of large audio-
                                                                                 language models: A comprehensive survey,” in Proceedings of
[32] T.-w. Hsu et al., “Reducing object hallucination in large audio-            the 2025 Conference on Empirical Methods in Natural Language
     language models via audio-aware decoding,” arXiv preprint                   Processing, C. Christodoulopoulos, T. Chakraborty, C. Rose, and
     arXiv:2506.07233, 2025.                                                     V. Peng, Eds. Suzhou, China: Association for Computational
[33] C.-Y. Kuan, C.-K. Yang, W.-P. Huang, K.-H. Lu, and H.-y. Lee,               Linguistics, Nov. 2025, pp. 10 144–10 170. [Online]. Available:
     “Speech-copilot: Leveraging large language models for speech                https://aclanthology.org/2025.emnlp-main.514/
     processing via task decomposition, modularization, and program         [49] K.-W. Chang et al., “Game-time: Evaluating temporal dynamics
     generation,” in 2024 IEEE Spoken Language Technology Work-                  in spoken language models,” 2025. [Online]. Available: https:
     shop (SLT). IEEE, 2024, pp. 1060–1067.                                      //arxiv.org/abs/2509.26388
[34] C.-H. Chiang, X. Wang, L. Li, C.-C. Lin, K. Lin, S. Liu, Z. Wang,      [50] G.-T. Lin, S.-Y. S. Kuan, Q. Wang, J. Lian, T. Li, S. Watanabe,
     Z. Yang, H.-y. Lee, and L. Wang, “Stitch: Simultaneous thinking             and H. yi Lee, “Full-duplex-bench v1.5: Evaluating overlap
     and talking with chunked reasoning for spoken language models,”             handling for full-duplex speech models,” 2026. [Online].
     arXiv preprint arXiv:2507.15375, 2025.                                      Available: https://arxiv.org/abs/2507.23159
[35] S. Arora et al., “On the landscape of spoken language models: A        [51] A. Wu et al., “Aligning spoken dialogue models from user in-
     comprehensive survey,” arXiv preprint arXiv:2504.08528, 2025.               teractions,” in International Conference on Machine Learning.
[36] K.-W. Chang, H. Wu, Y.-K. Wang, Y.-K. Wu, H. Shen, W.-                      PMLR, 2025, pp. 67 476–67 498.
     C. Tseng, I.-t. Kang, S.-W. Li, and H.-y. Lee, “Speechprompt:          [52] G.-T. Lin, P. G. Shivakumar, A. Gourav, Y. Gu, A. Gandhe,
     Prompting speech language models for speech processing tasks,”              H.-y. Lee, and I. Bulyko, “Align-SLM: Textless spoken language
     IEEE/ACM Transactions on Audio, Speech, and Language Pro-                   models with reinforcement learning from AI feedback,” in
     cessing, 2024.                                                              Proceedings of the 63rd Annual Meeting of the Association
[37] K.-W. Chang, W.-C. Tseng, S.-W. Li, and H.-y. Lee, “Speech-                 for Computational Linguistics (Volume 1: Long Papers),
     prompt: An exploration of prompt tuning on generative spo-                  W. Che, J. Nabende, E. Shutova, and M. T. Pilehvar, Eds.
     ken language model for speech processing tasks,” arXiv preprint             Vienna, Austria: Association for Computational Linguistics,
     arXiv:2203.16773, 2022.                                                     Jul. 2025, pp. 20 395–20 411. [Online]. Available: https:
                                                                                 //aclanthology.org/2025.acl-long.997/
[38] K.-W. Chang, Y.-K. Wang, H. Shen, I.-t. Kang, W.-C. Tseng,
     S.-W. Li, and H.-y. Lee, “Speechprompt v2: Prompt tuning for           [53] C. Chen, K. Hu, C.-H. H. Yang, A. Pasad, E. Casanova, W. Wang,
     speech classification tasks,” arXiv preprint arXiv:2303.00733,              S.-W. Fu, J. Li, Z. Chen, J. Balam et al., “Reinforcement learn-
     2023.                                                                       ing enhanced full-duplex spoken dialogue language models for
                                                                                 conversational interactions,” in Second Conference on Language
[39] Y. Chu, J. Xu, Q. Yang, H. Wei, X. Wei, Z. Guo, Y. Leng, Y. Lv,             Modeling, 2025.
     J. He, J. Lin et al., “Qwen2-audio technical report,” arXiv preprint
                                                                            [54] S. Arora, J. Tian, J. Shi, H. Futami, Y. Kashiwagi, E. Tsunoo,
     arXiv:2407.10759, 2024.
                                                                                 and S. Watanabe, “Optimizing conversational quality in spoken
[40] L.-H. Tseng, Y.-C. Chen, K.-Y. Lee, D.-S. Shiu, and H. yi Lee,              dialogue systems with reinforcement learning from ai feedback,”
     “Taste: Text-aligned speech tokenization and embedding                      arXiv preprint arXiv:2601.19063, 2026.
     for spoken language modeling,” 2026. [Online]. Available:
                                                                            [55] Z. Shao et al., “Deepseekmath: Pushing the limits of math-
     https://arxiv.org/abs/2504.07053
                                                                                 ematical reasoning in open language models,” arXiv preprint
[41] C. yu Huang et al., “Dynamic-SUPERB phase-2: A collabo-                     arXiv:2402.03300, 2024.
     ratively expanding benchmark for measuring the capabilities of         [56] G.-T. Lin et al., “Full-duplex-bench: A benchmark to evaluate
     spoken language models with 180 tasks,” in The Thirteenth In-               full-duplex spoken dialogue models on turn-taking capabilities,”
     ternational Conference on Learning Representations, 2025. [On-              2025. [Online]. Available: https://arxiv.org/abs/2503.04721
     line]. Available: https://openreview.net/forum?id=s7lzZpAW7T
                                                                            [57] E. J. Hu, yelong shen, P. Wallis, Z. Allen-Zhu, Y. Li,
[42] C.-y. Huang et al., “Dynamic-superb: Towards a dynamic, col-                S. Wang, L. Wang, and W. Chen, “LoRA: Low-rank adaptation
     laborative, and comprehensive instruction-tuning benchmark for              of large language models,” in International Conference on
     speech,” in ICASSP 2024-2024 IEEE International Conference on               Learning Representations, 2022. [Online]. Available: https:
     Acoustics, Speech and Signal Processing (ICASSP). IEEE, 2024,               //openreview.net/forum?id=nZeVKeeFYf9
     pp. 12 136–12 140.
                                                                            [58] S. Welleck, I. Kulikov, S. Roller, E. Dinan, K. Cho, and
[43] Z. Ma, Y. Song, C. Du, J. Cong, Z. Chen, Y. Wang, Y. Wang,                  J. Weston, “Neural text generation with unlikelihood training,”
     and X. Chen, “Language model can listen while speaking,” in                 in International Conference on Learning Representations,
     Proceedings of the AAAI Conference on Artificial Intelligence,              2020. [Online]. Available: https://openreview.net/forum?id=
     vol. 39, no. 23, 2025, pp. 24 831–24 839.                                   SJeYe0NtvH
[44] K. Hu, E. Hosseini-Asl, C. Chen, E. Casanova, S. Ghosh,                [59] Y. Zhu, S. Lu, L. Zheng, J. Guo, W. Zhang, J. Wang, and Y. Yu,
     P. Żelasko, Z. Chen, J. Li, J. Balam, and B. Ginsburg, “Effi-              “Texygen: A benchmarking platform for text generation models,”
     cient and Direct Duplex Modeling for Speech-to-Speech Lan-                  SIGIR, 2018.
     guage Model,” in Interspeech 2025, 2025, pp. 2715–2719.
