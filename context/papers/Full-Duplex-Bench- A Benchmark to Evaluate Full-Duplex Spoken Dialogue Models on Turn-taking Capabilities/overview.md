- **Title:** Full-Duplex-Bench: A Benchmark to Evaluate Full-Duplex Spoken Dialogue Models on Turn-taking Capabilities
- **Summary:** Full-Duplex-Bench turns real-time turn-taking behavior in spoken dialogue models into an automatic benchmark, showing that models trade off waiting, timely takeover, backchannel timing, and interruption coherence in different ways.
- **Paper Type:** benchmark
- **Venue:** arXiv/preprint 2025
- **Authors:** Guan-Ting Lin (National Taiwan University), Jiachen Lian (UC Berkeley), Tingle Li (UC Berkeley), Qirui Wang (University of Washington), Gopala Anumanchipalli (UC Berkeley), Alexander H. Liu (MIT CSAIL), Hung-yi Lee (National Taiwan University)
- **Keywords:** full-duplex spoken dialogue, turn-taking, backchanneling, speech benchmark, spoken dialogue models, interruption handling
- ## Orientation
    - **Background:** Spoken dialogue models (SDMs) are voice systems that understand speech and respond with speech. Full-duplex means the system can listen while speaking, rather than waiting for one clean turn at a time.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A voice agent must decide when to stay quiet, when to say a tiny acknowledgment, when to answer, and what to do if the user cuts in.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** The same short silence can mean hesitation, a sentence break, or an invitation to speak, and the model must decide from timing and audio context.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Test the model with controlled conversational moments and score the observable audio behavior instead of asking only whether the answer content is good.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a speech-interaction benchmark for full-duplex spoken dialogue models, meaning voice systems that can listen while speaking; it targets the missing evaluation layer between task accuracy and the timing behaviors that make conversation feel natural.
      claim_kind:: analyst_assessment
      evidence:: E1, E2
    - **One-Sentence Contribution:** Full-Duplex-Bench improves evaluation of real-time spoken dialogue by turning listener timing, speaker handoff, and interruption recovery into automatically scored audio-stream tests.
      evidence:: E1, E4
    - **Mental Model:** Picture a driving test for voice agents: the benchmark creates awkward but realistic moments, records whether the agent cuts in, waits, nods briefly, or changes course, then scores the timing from the audio traces.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is the unified comparison of four systems across four interaction dimensions using the same streamed inputs and automatic timing metrics.
      evidence:: E9, E10, E11, E12, E13
        - Supports C3: Gemini Live on Table III; closest open-source baseline Freeze-Omni; lower pause Takeover Rate and lower backchannel Jensen-Shannon Divergence; 0.255 vs 0.642 synthetic pause TOR and 0.896 vs 0.997 backchannel JSD; medium support because no variance is reported.
          evidence:: E11
        - Supports C3: Candor smooth turn-taking; dGSLM and Moshi compared with Freeze-Omni and Gemini Live; response latency and Takeover Rate; Moshi is fastest at 0.265 seconds while Freeze-Omni and Gemini have lower takeover; medium support because speed and correctness trade off.
          evidence:: E12
        - Supports C3: synthetic interruption task; Freeze-Omni compared with Gemini Live, Moshi, and dGSLM; GPT-4o response-quality score and latency; Freeze-Omni scores 3.615 versus Gemini 3.376 with higher latency; medium support because the evaluator and repeat statistics are not audited.
          evidence:: E13
    - **Main Caveat:** The benchmark is diagnostic rather than preference-calibrated: it can say when a model interrupts, delays, or backchannels differently, but not whether that behavior is best for a user, language, or application.
      claim_kind:: analyst_assessment
      evidence:: E13, E14
- ## Argument Map
    - **Problem and Stakes:** Full-duplex spoken dialogue models promise more natural interaction, but existing evaluation mostly measures content, instructions, or broad corpus statistics rather than whether the system respects live conversational timing.
      evidence:: E1, E2
    - **Prior Gap:** The prior gap is methodological: dGSLM-style corpus statistics are hard to interpret, Talking-Turns depends on a learned judge and user studies, and many speech benchmarks assume half-duplex interaction, meaning one side talks at a time.
      evidence:: E2
    - **Key Insight:** The paper's key insight is that turn-taking can be decomposed into scenario-specific observable events, then scored from time-aligned model output with descriptive metrics rather than one global conversational-quality score.
      evidence:: E1, E4, E5, E6, E7, E8
    - **Claims:** The paper's logical claims are these four falsifiable statements.
      claim_kind:: analyst_assessment
        - C1: A scenario-driven benchmark can cover the main real-time behaviors that distinguish full-duplex SDMs: pause handling, backchanneling, smooth turn-taking, and user interruption management.
          evidence:: E1, E4
        - C2: These behaviors can be operationalized with automatic metrics over synchronized user and model audio, including Takeover Rate, backchannel frequency, Jensen-Shannon Divergence, response latency, and GPT-4o interruption scoring.
          evidence:: E3, E4, E5, E6, E7, E8
        - C3: Applying the benchmark to dGSLM, Moshi, Freeze-Omni, and Gemini Live reveals different tradeoffs rather than a single best model across all turn-taking behaviors.
          evidence:: E10, E11, E12, E13
        - C4: The benchmark is a reproducible diagnostic tool, but its scores are not yet grounded in human preference or cross-lingual generality.
          evidence:: E14, E15
- ## Mechanism and Design
    - **Core Mechanism:** Full-Duplex-Bench feeds each model the same user audio stream, records its time-synchronous speech output, converts the output into word-level timestamps with automatic speech recognition (ASR, software that turns speech into timed text), and computes task-specific behavior metrics.
      evidence:: E4
        - Takeover Rate (TOR) turns the question 'did the model seize the conversational floor' into a binary signal averaged across samples.
          evidence:: E3
        - Jensen-Shannon Divergence (JSD, a bounded distance between two probability distributions) compares the timing of model backchannels with human backchannel timing.
          evidence:: E6
        - Interruption handling is split into whether the model answers, how good the answer is, and how long it takes after the user interrupts.
          evidence:: E8
    - **Data / Control Flow:** The flow is sample selection, user audio construction, model streaming, output alignment, behavior classification, and metric aggregation; this keeps model inference separate from the scoring rules.
      evidence:: E4, E9
        - Candor supplies natural two-channel conversations for pause and smooth-turn cases, with voice activity detection (VAD, software that marks when speech is present) and manual review used to filter candidate segments.
          evidence:: E9
        - The In Conversation Corpus (ICC) supplies human backchannel timing over small time windows, giving the benchmark a human timing distribution for the JSD comparison.
          evidence:: E9
        - Synthetic interruption and pause cases use GPT-4o text generation and text-to-speech (TTS, software that turns text into spoken audio) to create controlled events that are scarce in public dialogue data.
          evidence:: E9
    - **Design Decisions:** The benchmark chooses simple descriptive metrics so that each score corresponds to a visible behavior, trading away a direct human-preference verdict for reproducibility and diagnostic clarity.
      claim_kind:: analyst_assessment
      evidence:: E5, E6, E7, E8, E14
        - Need: avoid counting full responses as acknowledgments; design choice: define backchannels by short duration and very few words; tradeoff: richer listener signals outside that shape are excluded.
          evidence:: E3
        - Need: make timing errors diagnosable; design choice: use different metrics for pauses, backchannels, handoff, and interruption; alternative: one learned global judge, which the paper argues is less reproducible.
          claim_kind:: analyst_assessment
          evidence:: E2, E5, E6, E7, E8
        - Need: evaluate rare interruption cases; design choice: generate controlled synthetic dialogues; tradeoff: the event distribution may differ from natural user barge-ins.
          claim_kind:: analyst_assessment
          evidence:: E9
    - **Implementation Surface:** The implementation surface is deliberately external-model friendly: each tested system only needs to consume streamed user audio and emit audio that can be aligned back to the original timeline.
      evidence:: E4, E10, E15
        - dGSLM, Moshi, and Freeze-Omni are evaluated through released implementations or servers, while Gemini Live is evaluated through the vendor's live service with 16 kHz audio streaming.
          evidence:: E10
        - The authors report releasing the benchmark and code, which matters because many candidate full-duplex systems do not release full speech-to-speech pipelines.
          evidence:: E15
- ## Evaluation and Evidence
    - **Setup:** The benchmark evaluates dGSLM, Moshi, Freeze-Omni, and Gemini Live on Candor, ICC, and synthetic data, using lower-is-better TOR for pauses, lower-is-better JSD for backchannel timing, lower-is-better latency for handoff, and higher-is-better GPT-4o scores for interruption response quality.
      evidence:: E5, E6, E7, E8, E9, E10
        - The reported sample counts are 216 Candor pause samples, 119 Candor smooth-turn samples, 55 ICC backchannel samples, 200 synthetic interruption samples, and 137 synthetic pause samples.
          evidence:: E9
        - Baseline fairness is partial: the same benchmark inputs and metrics are used, but model access differs across local open-source pipelines and the Gemini Live service.
          claim_kind:: analyst_assessment
          evidence:: E10
        - Statistical uncertainty is not reported: the table gives aggregate scores but no variance, confidence intervals, or repeat-count analysis.
          claim_kind:: analyst_assessment
          evidence:: E11, E12, E13
    - **Claim-Evidence Matrix:** C1 and C2 are supported mainly by the benchmark design; C3 is supported by the model comparison table; C4 is supported by the authors' own limitation statement and release discussion.
      claim_kind:: analyst_assessment
      evidence:: E1, E4, E11, E12, E13, E14, E15
        - C1-C2: scenario coverage and automatic metrics are directly described, but the paper does not prove these four dimensions exhaust all full-duplex conversation quality.
          claim_kind:: analyst_assessment
          evidence:: E1, E4, E5, E6, E7, E8
        - C3: Table III supports a tradeoff view because the best model changes by dimension and by metric direction.
          claim_kind:: analyst_assessment
          evidence:: E11, E12, E13
        - C4: reproducibility is helped by release and automatic metrics, but preference and language boundaries are explicitly left open.
          claim_kind:: analyst_assessment
          evidence:: E14, E15
    - **Headline Results:** The headline result is not a leaderboard win but a behavioral profile: end-to-end systems can be quick, explicit control helps interruption coherence, and the commercial service avoids premature takeover more often on the reported metrics.
      claim_kind:: analyst_assessment
      evidence:: E11, E12, E13
        - Supported claim: C3; configuration: Table III pause and backchannel tasks; closest baseline: Freeze-Omni for Gemini Live; metric and direction: lower TOR/JSD; delta: 0.255 vs 0.642 synthetic pause TOR and 0.896 vs 0.997 backchannel JSD; uncertainty: not reported; caveat: closed-service details are unavailable.
          evidence:: E11
        - Supported claim: C3; configuration: Candor smooth turn-taking; baseline: all evaluated systems; metric and direction: higher TOR but lower latency; delta: Moshi has 0.941 TOR and 0.265 second latency, while Gemini has 0.655 TOR and 1.301 second latency; uncertainty: not reported; caveat: promptness and willingness to take over conflict.
          evidence:: E12
        - Supported claim: C3; configuration: synthetic interruption; baseline: Gemini Live and end-to-end systems; metric and direction: higher GPT-4o quality score and lower latency; delta: Freeze-Omni scores 3.615 at 1.409 seconds versus Gemini 3.376 at 1.183 seconds; uncertainty: not reported; caveat: GPT-4o judging is not a human preference study.
          evidence:: E13
    - **Ablations and Sensitivity:** Not applicable: the paper reports cross-model and cross-dataset comparisons, but no ablation that removes benchmark components or varies metric definitions.
      claim_kind:: analyst_assessment
    - **Reproducibility Gaps:** The benchmark and code are released, but exact reproduction still depends on external model releases, closed-service behavior, the ASR pipeline, GPT-4o judging for interruption quality, and absent variance or repeat-count reporting.
      claim_kind:: analyst_assessment
      evidence:: E8, E10, E11, E12, E13, E15
        - Many compared full-duplex systems lack full public speech-to-speech releases or disclosed internals, so the benchmark is more reusable than the evaluated model set.
          claim_kind:: analyst_assessment
          evidence:: E15
        - The interruption quality metric uses GPT-4o as an evaluator, so its calibration, prompt sensitivity, and agreement with people remain unreported.
          claim_kind:: analyst_assessment
          evidence:: E8, E14
- ## Technical Judgment
    - **What Holds Up:** The benchmark's strongest part is its decomposition of messy conversation into auditable signals: who spoke, when they spoke, whether the speech was a short listener cue, and how quickly the model reacted.
      claim_kind:: analyst_assessment
      evidence:: E3, E4, E5, E6, E7, E8
        - The same framework exposes different failure modes across dGSLM, Moshi, Freeze-Omni, and Gemini Live, which is more useful than a single aggregate conversational score.
          claim_kind:: analyst_assessment
          evidence:: E11, E12, E13
    - **Where It May Fail:** It may fail when the task requires nuanced social preference rather than observable timing: a low TOR can mean patience or missed chances to answer, and a high backchannel frequency can be helpful or annoying depending on context.
      claim_kind:: analyst_assessment
      evidence:: E3, E6, E12, E14
        - The backchannel detector's duration and word-count rule is easy to reproduce but can miss longer acknowledgments, nonverbal cues, or language-specific listener signals.
          claim_kind:: analyst_assessment
          evidence:: E3, E14
        - Synthetic interruption and pause samples make controlled tests possible, but they may underrepresent messy real user barge-ins, speech repairs, and multilingual behavior.
          claim_kind:: analyst_assessment
          evidence:: E9, E14
    - **Relation to Other Work:** Compared with content or instruction-following speech benchmarks, this paper evaluates interaction timing; compared with dGSLM's voice-activity statistics or Talking-Turns' trained judge, it favors explicit scenarios and automatic metrics that are easier to rerun.
      claim_kind:: analyst_assessment
      evidence:: E2, E5, E6, E7, E8
        - The evaluated model categories matter technically: end-to-end systems directly model audio streams, while cascaded systems combine components such as ASR, text generation, and TTS, changing latency and control behavior.
          evidence:: E10, E12, E13
    - **Transferable Lesson:** For interactive AI systems, benchmark the micro-behaviors that users experience directly before collapsing them into a global score; separate descriptive diagnostics from preference judgments so developers can choose the behavior profile their application needs.
      claim_kind:: analyst_assessment
      evidence:: E1, E5, E6, E7, E8, E14
- ## Glossary
  collapsed:: true
    - Spoken Dialogue Model: A system that takes speech as conversational input and produces a spoken response; in this note, SDM is the evaluated model family.
    - Full-duplex: A communication mode where listening and speaking can happen at the same time, unlike half-duplex turn-by-turn interaction.
    - Turn-taking: The timing problem of deciding who speaks next and when a speaker has yielded or kept the floor.
    - Backchannel: A short listener cue such as an acknowledgment that signals attention without taking over the conversation.
    - Takeover Rate: TOR averages a binary takeover signal; lower is better for pause and backchannel tasks, while higher is desired when the model should answer after a turn end or interruption.
    - Jensen-Shannon Divergence: A bounded measure of difference between two probability distributions; here it compares model backchannel timing with human backchannel timing.
    - Automatic Speech Recognition: Software that turns speech audio into text, often with timestamps used for alignment.
    - Voice Activity Detection: Software that marks when speech is present in an audio stream; used for filtering and segmentation.
    - Text-to-Speech: Software that synthesizes spoken audio from text; used to create synthetic benchmark inputs.
    - In Conversation Corpus: A dataset used here for human backchannel timing distributions.
    - End-to-end speech model: A model that directly models speech streams without relying primarily on an explicit text pipeline.
    - Cascaded speech system: A modular voice system that chains components such as ASR, a language model, and TTS; the modularity can improve control but add latency.
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/paper_statement | Abstract and Introduction | high
      locator:: Abstract; Introduction near contribution paragraph
      quote:: The paper introduces Full-Duplex-Bench for full-duplex spoken dialogue models and centers evaluation on pause handling, backchanneling, turn-taking, and interruption management with automatic metrics.
    - **E2:** gap/paper_statement | Introduction and Related Works | medium
      locator:: Introduction prior benchmark discussion; II.B Evaluation Benchmarks
      quote:: Prior speech benchmarks mainly cover content, instruction following, or paralinguistic perception under turn-based assumptions; dGSLM statistics and Talking-Turns expose reproducibility and generalization limits.
    - **E3:** method/paper_statement | Full-Duplex-Bench Framework | high
      locator:: III, key term definitions before III.A
      quote:: Backchanneling is operationalized as brief listener speech under one second and fewer than two words; takeover is non-silent non-backchannel speech, and TOR averages that binary variable.
    - **E4:** system_design/implementation_detail | Full-Duplex-Bench Framework | high
      locator:: III.A Overview; Figure 1
      quote:: The framework streams input.wav to each SDM, records output.wav, uses Nvidia parakeet-tdt-0.6b-v2 ASR for word-level timing, and applies dedicated metrics by dimension.
    - **E5:** method/paper_statement | Full-Duplex-Bench Framework | high
      locator:: III.B.1 Pause Handling
      quote:: Pause handling asks whether the model recognizes that the user still holds the floor; the metric is Takeover Rate, where lower values mean fewer premature interruptions.
    - **E6:** formula/paper_statement | Full-Duplex-Bench Framework | high
      locator:: III.B.2 Backchanneling
      quote:: Backchanneling is measured with TOR, backchannel events per second, and Jensen-Shannon Divergence between model and human timing distributions over aligned time windows.
    - **E7:** method/paper_statement | Full-Duplex-Bench Framework | high
      locator:: III.B.3 Smooth Turn Taking
      quote:: Smooth turn-taking measures average response latency from the end of user speech to the start of model speech, calculated only when takeover occurs.
    - **E8:** method/paper_statement | Full-Duplex-Bench Framework | medium
      locator:: III.B.4 User Interruption
      quote:: User interruption evaluation uses TOR, a GPT-4o score from 0 to 5 for coherence and relevance, and latency after interruption when the model takes the turn.
    - **E9:** experiment_setup/implementation_detail | Data Curation | high
      locator:: III.C; Table II
      quote:: The benchmark uses Candor for pause and smooth-turn data, ICC for backchannel timing, and synthetic GPT-4o plus ChatTTS data for interruptions and synthetic pauses.
    - **E10:** experiment_setup/implementation_detail | Models Under Evaluation | high
      locator:: IV Models Under Evaluation
      quote:: The evaluated systems are dGSLM, Moshi, Freeze-Omni, and Gemini Live, using official implementations or official service access where available.
    - **E11:** result/experiment_result | Results | medium
      locator:: V Results; Table III pause and backchannel columns
      quote:: Table III shows Gemini Live with the lowest pause TORs and best backchannel JSD; dGSLM has the highest open-source backchannel frequency, while Moshi often takes over.
    - **E12:** result/experiment_result | Results | medium
      locator:: V Results; Table III smooth turn-taking columns
      quote:: For Candor smooth turn-taking, dGSLM and Moshi have high TOR and low latency, while Freeze-Omni and Gemini Live have lower takeover rates and slower responses.
    - **E13:** result/experiment_result | Results | medium
      locator:: V Results; Table III user interruption columns
      quote:: On synthetic interruptions, Freeze-Omni gets the highest GPT-4o quality score, Gemini Live is close, and the end-to-end systems struggle with semantic coherence.
    - **E14:** limitation/limitation | Limitation and Future Work | high
      locator:: VII Limitation and Future Work
      quote:: The authors state that the framework does not yet connect measured behaviors to human preferences and that the present analysis is limited to English.
    - **E15:** implementation/paper_statement | Introduction and Related Works | medium
      locator:: Contribution footnote; Table I
      quote:: The paper reports a public data and code release, while Table I shows many full-duplex systems lack complete public speech-to-speech releases or architectural details.
