- **Title:** Beyond Turn-Based Interfaces: Synchronous LLMs as Full-Duplex Dialogue Agents
- **Summary:** SyncLLM turns a text-pretrained Llama3-8B model into a synchronous full-duplex speech dialogue agent by making time an explicit token-level structure, showing that language pretraining can improve spoken dialogue meaning without sacrificing much turn-taking naturalness.
- **Paper Type:** system
- **Venue:** arXiv preprint 2024
- **Authors:** Bandhav Veluri (Meta AI, University of Washington); Benjamin N. Peloquin (Meta AI); Bokai Yu (Meta AI); Hongyu Gong (Meta AI); Shyamnath Gollakota (University of Washington)
- **Keywords:** full-duplex dialogue, spoken dialogue agents, synchronous language modeling, speech tokens, turn-taking, synthetic speech training
- ## Orientation
    - **Background:** Spoken dialogue agents try to let machines converse by voice, not just read and write text. Full-duplex dialogue means both sides can listen and speak at the same time, as people do when they interrupt, overlap, or say brief listening signals like 'yeah'.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** Most voice agents wait for a clean turn before answering, but real conversations do not wait politely: people start early, pause mid-thought, overlap briefly, and give tiny signals while the other person is still talking.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** A model must know what time it is, keep listening while it speaks, work with scarce real speech conversations, and answer before delayed network audio has fully arrived.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Make the model speak in short clocked chunks, train it on both sides of the conversation, and let it guess the other side briefly when live input is late.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a speech-language-model systems paper about moving large language models (LLMs) from push-to-talk dialogue toward always-listening, always-ready voice agents, with the main gap being real-time synchrony rather than only speech recognition or speech synthesis.
      claim_kind:: analyst_assessment
    - **One-Sentence Contribution:** SyncLLM improves full-duplex spoken dialogue, where both speakers may talk and listen at once, by training a text-pretrained Llama3-8B to generate speech in clocked chunks that keep both speakers on a shared timeline.
      evidence:: E1, E5
    - **Mental Model:** Picture two people passing short audio cards across a table every instant: the model writes its own next card, guesses the other person's not-yet-arrived card when the network is late, then replaces the guess with the real card as soon as it arrives.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is the human Mean Opinion Score (MOS), a five-point listener rating, where SyncLLM is much more meaningful than dGSLM while naturalness remains close.
      evidence:: E13, E14
        - Supports C2: 160 ms SyncLLM-F continuation; dGSLM baseline; overall Meaningfulness-MOS; +2.19 points from 1.55 to 3.74 with standard errors reported; strong support for better dialogue content.
          evidence:: E13, E14
        - Supports C2: Fisher-trained continuation with 10 s prompts; dGSLM baseline; median transcription perplexity; SyncLLM stays roughly 15 above ground truth while dGSLM is roughly 70 above; medium support because variance is not reported.
          evidence:: E11
        - Supports C3: two SyncLLM agents with one-chunk delayed input; continuation and dGSLM references; ASR perplexity and MOS; interactive models remain far above dGSLM in meaningfulness but below single-model continuation; medium support for latency-tolerant interaction.
          evidence:: E15
    - **Main Caveat:** The paper proves the idea mostly through simulated LLM-to-LLM interaction and listener ratings, so deployment trust still depends on real user studies, better speech generation quality, safety controls, and longer-context handling.
      claim_kind:: analyst_assessment
      evidence:: E15, E16
- ## Argument Map
    - **Problem and Stakes:** The paper targets the mismatch between human full-duplex conversation and half-duplex voice interfaces that wait for prompts, silence, or turn-end detection. The stakes are not only lower latency, but preserving backchannels, interruptions, overlaps, and timing cues that make spoken interaction feel cooperative.
      evidence:: E2, E3
    - **Prior Gap:** Prior spoken dialogue models either stay turn-based or, in the closest full-duplex baseline dGSLM, use speech-only modeling and assume immediate cross-speaker access; SyncLLM instead tries to preserve text-pretrained LLM knowledge while handling delayed input.
      evidence:: E4
    - **Key Insight:** The key insight is that synchrony can be represented as a token-sequence problem: periodically insert speaker timing tags, generate fixed-duration chunks for both speakers, and use short-horizon prediction of the user stream to bridge unavoidable latency.
      evidence:: E5, E6, E8
    - **Claims:** The paper's claim chain has three falsifiable claims: C1 about synchronous modeling, C2 about semantic and natural dialogue quality, and C3 about latency-tolerant interaction.
      evidence:: E5, E11, E14, E15
        - C1: A standard auto-regressive transformer decoder can model full-duplex speech when dialogue is encoded as interleaved, fixed-duration chunks with periodic speaker synchronization tokens.
          evidence:: E5, E7, E8
        - C2: Combining large synthetic speech-dialogue training with a smaller real dual-channel speech stage yields more meaningful generated dialogue than dGSLM while maintaining comparable turn-taking naturalness.
          evidence:: E9, E11, E12, E14
        - C3: Estimating the user's missing current chunk lets SyncLLM sustain simulated full-duplex interaction under one-chunk network delay, with evidence strongest up to 200 ms and weaker at 240 ms.
          evidence:: E6, E15
- ## Mechanism and Design
    - **Core Mechanism:** SyncLLM keeps the ordinary next-token prediction interface of an auto-regressive transformer, a model that predicts the next symbol from previous symbols, but changes the sequence so speech from both participants is interleaved by real-time chunks. Periodic speaker tags, special tokens naming each speaker, act as synchronization marks that make elapsed time visible to the model.
      evidence:: E5, E7
        - Each chunk covers a fixed duration, and the model predicts its own side's discrete speech units followed by the user's side's units, allowing overlap and silence to be represented in the same sequence.
          evidence:: E5
        - Speech is represented with HuBERT, a self-supervised speech tokenizer that maps audio into discrete units, at 25 Hz with a 501-unit vocabulary.
          evidence:: E7
    - **Data / Control Flow:** At runtime, the model receives interleaved past chunks, lacks the user's current chunk until that audio finishes and arrives, predicts an estimated current user chunk, uses it to produce its next own chunk, then replaces the estimate with real user input for later chunks.
      evidence:: E6
        - For training, each speaker's audio channel is tokenized separately, arranged into parallel streams, deduplicated within chunks, and interleaved with speaker tags.
          evidence:: E8, E10
        - For speech synthesis, deduplicated units are expanded back to the expected number of per-chunk tokens by interpolation before a vocoder converts units into audio.
          evidence:: E8, E16
    - **Design Decisions:** The design repeatedly trades exact acoustic timing for a representation that a text-pretrained LLM can learn: deduplicate speech units for semantics, keep coarse time with speaker tags, and bootstrap real full-duplex learning from synthetic turn-based speech.
      evidence:: E8, E9, E18
        - Need: raw speech tokens waste many positions on repeated silence or duration; choice: deduplicate HuBERT sequences; tradeoff: duration must be approximated later by interpolation.
          evidence:: E8
        - Need: real dual-channel spoken dialogue is scarce; choice: use synthetic text-to-speech stages before real Fisher full-duplex fine-tuning; tradeoff: early stages cannot teach true overlap or backchannels.
          evidence:: E9, E10
        - Need: align text and speech without destabilizing a text-only base model; choice: sentence-level text/speech interleaving rather than turn-level interleaving; ablation reports better zero-shot spoken language understanding.
          evidence:: E18
    - **Implementation Surface:** The reported system extends Llama3-8B with speech-unit and speaker-tag tokens, uses the original 8192 sequence length, trains on 128 A100 GPUs in stage one, and synthesizes generated speech with a simple HiFi-GAN vocoder.
      evidence:: E7, E17, E16
- ## Evaluation and Evidence
    - **Setup:** The evaluation has continuation mode, where one model extends both sides of a prompt, and interaction mode, where two SyncLLM instances talk with one-chunk delayed input. It compares against dGSLM, uses Fisher as in-distribution data and CANDOR as out-of-distribution data, and measures text semantics, turn-taking timing, and human MOS ratings.
      evidence:: E10, E11, E12, E13, E15
    - **Claim-Evidence Matrix:** Evidence is strongest for C2 because it combines ASR-based semantic checks, turn-taking statistics, and human ratings; C1 is mainly supported by successful system behavior rather than isolated mechanism proof; C3 is supported by simulation rather than live human interaction.
      claim_kind:: analyst_assessment
      evidence:: E11, E12, E14, E15
        - C1: Method evidence is direct for the sequence format and runtime algorithm, but the paper does not isolate every synchronization component in a causal ablation.
          claim_kind:: analyst_assessment
          evidence:: E5, E6, E8
        - C2: Semantic and MOS evidence is strong relative to dGSLM, while naturalness evidence is moderate because correlation metrics and MOS standard errors are reported but not full statistical tests for every comparison.
          claim_kind:: analyst_assessment
          evidence:: E11, E12, E13, E14
        - C3: Interaction evidence shows useful degradation behavior across latency, but it is limited to model-model simulations and one reported interaction protocol.
          claim_kind:: analyst_assessment
          evidence:: E15
    - **Headline Results:** SyncLLM-F improves overall Meaningfulness-MOS from dGSLM's 1.55 to 3.74 at 160 ms chunks while Naturalness-MOS remains similar, 3.90 versus 3.95. In automatic semantic evaluation, SyncLLM's median transcription perplexity stays much closer to ground truth than dGSLM across generated durations and OOD prompts.
      evidence:: E11, E14
        - Turn-taking correlations in Table 2 favor SyncLLM over dGSLM on both Fisher and CANDOR, but the resynthesized ground-truth topline shows there remains substantial timing loss from tokenization and synthesis.
          evidence:: E12
        - In interaction mode, SyncLLM-F-C and SyncLLM-F-F retain higher Meaningfulness-MOS than dGSLM but fall below SyncLLM-F continuation, showing interaction is plausible but not free.
          evidence:: E15
    - **Ablations and Sensitivity:** The clearest ablation is training interleaving level: sentence-level text/speech interleaving beats turn-level interleaving on WUGGY, BLIMP, Topic-StoryCloze, and StoryCloze. Latency sensitivity shows little degradation at 160-200 ms interaction but worse performance at 240 ms.
      evidence:: E18, E15
    - **Reproducibility Gaps:** The paper reports model family, sequence length, hardware scale, learning rates, training iterations, data sources, evaluation protocols, and a project webpage; it does not provide enough information in the paper text alone to reproduce the exact synthetic TTS corpus, sampling recipes, model checkpoints, or all generation scripts.
      claim_kind:: analyst_assessment
      evidence:: E9, E13, E17
- ## Technical Judgment
    - **What Holds Up:** The central systems move is credible: expose time in the token stream while keeping the architecture close to a pretrained LLM, which lets the model inherit language knowledge that speech-only dGSLM lacks. The strongest empirical support is that semantics improve sharply while timing metrics and Naturalness-MOS do not collapse.
      claim_kind:: analyst_assessment
      evidence:: E4, E5, E11, E14
    - **Where It May Fail:** Benefits are likely to diminish when latency exceeds the chunk regime studied, when conversations need long memory beyond the inherited sequence length, when non-verbal expressivity matters, or when the simple vocoder dominates perceived quality. The method also assumes discrete semantic speech units are enough to carry dialogue behavior after interpolation.
      claim_kind:: analyst_assessment
      evidence:: E8, E15, E16, E17
    - **Relation to Other Work:** Compared with turn-based spoken LLMs such as SpeechGPT-style systems, SyncLLM changes the interaction contract rather than only adding speech input and output. Compared with dGSLM, it replaces a speech-only dual-channel architecture with a text-pretrained decoder plus a synchronous sequence format, so the technical bet is reuse of language knowledge under a real-time speech encoding.
      claim_kind:: analyst_assessment
      evidence:: E4, E5
    - **Transferable Lesson:** When adapting LLMs to a medium with continuous time, avoid building a new architecture first; instead, encode the missing physical variable as a small, regular structure in the sequence, then use staged synthetic-to-real training to bridge data scarcity.
      claim_kind:: analyst_assessment
      evidence:: E5, E8, E9
- ## Glossary
  collapsed:: true
    - full-duplex dialogue: A conversation mode where both sides can speak and listen at the same time; translate as quan shuang gong or simultaneous two-way dialogue depending on context.
    - half-duplex dialogue: A mode where one side effectively speaks at a time and the system waits for an explicit prompt, silence, or turn boundary before responding.
    - backchannel: Short listener feedback such as 'yeah' or 'uh-huh' that can overlap with the speaker and signals attention or understanding.
    - Synchronous LLM: The paper's model family: a large language model trained to generate speech-token chunks synchronized to a real-world clock.
    - HuBERT: A self-supervised speech representation model used here as a tokenizer that converts audio into discrete speech units.
    - speaker tag: Special tokens marking which speaker's speech units follow; [S0] also acts as the periodic synchronization anchor.
    - deduplication: Removing repeated consecutive speech tokens so the model spends capacity on semantic changes rather than silence or duration repetitions.
    - interpolation: The reconstruction step that repeats deduplicated speech units to fill the expected number of tokens in each chunk before audio synthesis.
    - Mean Opinion Score: A listener rating scale; this paper uses Naturalness-MOS for turn-taking and Meaningfulness-MOS for dialogue content.
    - floor-transfer offset: A turn-taking timing measure: negative values represent overlap between speakers and positive values represent gaps.
    - HiFi-GAN vocoder: The simple speech synthesizer used by the paper to convert generated speech units into audible waveform output; GAN expands to generative adversarial network.
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/metadata | Abstract | high
      locator:: Abstract, opening and contribution summary
      quote:: Beyond Turn-Based Interfaces: Synchronous LLMs as Full-Duplex Dialogue Agents. Bandhav Veluri, Benjamin N Peloquin, Bokai Yu, Hongyu Gong, Shyamnath Gollakota. Meta AI and University of Washington.
    - **E2:** problem/paper_statement | Abstract | high
      locator:: Abstract, problem statement
      quote:: Most approaches are inherently half-duplex - restricted to turn-based interaction with responses requiring explicit prompting by the user or implicit tracking of interruption or silence events. Human dialogue, by contrast, is full-duplex allowing for rich synchronicity.
    - **E3:** gap/paper_statement | 1 Introduction | high
      locator:: Introduction, four challenges paragraph
      quote:: Developing a full-duplex spoken dialog agent is challenging for four reasons: turn-taking cues require a common reference clock, spoken dialogue data is limited, the model must be streaming for the duration of dialogue, and cloud deployment must address Internet latency.
    - **E4:** prior_work/paper_statement | 2 Related work | high
      locator:: Related work, dGSLM comparison
      quote:: The closest work to ours is dGSLM, which models simultaneous dialogue using a dual-tower Transformer that attends to two channels. One weakness of dGSLM is its reliance on speech-only training, which does not fully utilize textual knowledge.
    - **E5:** method/implementation_detail | 3 SyncLLM | high
      locator:: Section 3, architecture overview
      quote:: SyncLLM is an auto-regressive transformer decoder architecture, that natively models discrete speech units in a wall-clock synchronous fashion. In each time step, the model predicts speech units corresponding to a fixed duration for its side followed by the user's side.
    - **E6:** algorithm/implementation_detail | 3.1 Latency tolerant interaction | high
      locator:: Section 3.1 and Figure 1
      quote:: The LLM's output for the next chunk is computed by first estimating the user's response for the current time chunk. We then append this estimated chunk to the LLM's context to generate the LLM's next chunk.
    - **E7:** implementation/implementation_detail | 3.2 Token sequence format | high
      locator:: Section 3.2, HuBERT tokenization
      quote:: Following prior works in spoken language modeling, we use HuBERT to represent speech, with a token sampling rate of 25 Hz - one token for every 40 ms of audio - and a vocabulary size of 501.
    - **E8:** optimization/implementation_detail | 3.2 Token sequence format | high
      locator:: Deduplication and Interpolation paragraphs
      quote:: SyncLLM is trained to predict deduplicated HuBERT sequences, with coarse timing information maintained by periodically interleaved special tokens. To generate token sequences suitable for speech synthesis, we use timing information to interpolate the deduplicated token sequence.
    - **E9:** method/implementation_detail | 4 Training | high
      locator:: Training overview and Table 1
      quote:: We use Llama3-8b as our base model and employ a three stage training procedure. The data table lists 193k hours of SFT synthetic speech, 20k hours of dialogue synthetic speech, and 1927 hours of real spoken dialogue.
    - **E10:** experiment_setup/implementation_detail | 4 Training | high
      locator:: Stage 3 paragraph
      quote:: Finally, we finetune the model to learn turn-taking cues from real-world spoken dialogue data. We use the Fisher dataset with 2000 hours of spoken dialogues, where each speaker's speech is separated into independent audio channels.
    - **E11:** result/experiment_result | 5.1 Semantic evaluation | medium
      locator:: Section 5.1, Figures 5 and 6
      quote:: We transcribe the generated spoken dialogues into turn-based text dialogues and compute median perplexity. dGSLM has a perplexity drop of approximately 70 relative to the ground-truth, while SyncLLM only has a drop of approximately 15.
    - **E12:** result/experiment_result | 5.2 Naturalness evaluation | medium
      locator:: Section 5.2 and Table 2
      quote:: Generations with our models achieve better turn-taking event correlation with ground-truth continuations compared to dGSLM for both in-distribution and out-of-distribution testsets. Resynth-GT serves as a topline for our method.
    - **E13:** experiment_setup/experiment_result | 5.3 Human Evaluation | high
      locator:: Human evaluation protocol paragraph
      quote:: In total, n_annot = 32 annotators provided ratings for n_items = 180 items divided evenly between the CANDOR and Fisher datasets. Each sample received a rating by three unique raters; 95 percent confidence intervals use bootstrapping.
    - **E14:** result/experiment_result | 5.3 Human Evaluation | high
      locator:: Table 3 and Overall results paragraph
      quote:: Nearly all models are at parity in perceived Naturalness of turn-taking, while SyncLLM-based models significantly outperform dGSLM in Meaningfulness, approaching re-synthesized ground-truth values. Table 3 reports SyncLLM-F overall Meaningfulness 3.74 versus dGSLM 1.55.
    - **E15:** result/experiment_result | 5.4 Full-duplex interaction | medium
      locator:: Section 5.4, Figure 7, Table 4, Appendix C
      quote:: SyncLLM in the LLM-LLM interaction setting is able to closely match the performance of the continuation setting and perform significantly better than dGSLM. Appendix C reports robustness to 200 ms latency but performance drops above that.
    - **E16:** limitation/limitation | 7 Limitations and Risks | high
      locator:: Limitations paragraph
      quote:: Performance could be further improved in terms of speech quality; the paper uses a simple HiFi-GAN vocoder. It has not studied expressivity and non-verbal sounds such as laughter, and Llama-3 sequence length limits long-context modeling.
    - **E17:** implementation/implementation_detail | A.1 Hyperparameters | high
      locator:: Appendix A.1
      quote:: We trained SyncLLM with the Llama3-8b's original sequence length 8192. Stage one uses 128 A100 GPUs and trains for 40k iterations; later stages reduce token batch sizes and train for 6000 and 2000 iterations.
    - **E18:** ablation/ablation | A.2 Benchmarking interleaving strategies | medium
      locator:: Appendix A.2 and Table 5
      quote:: We explore two text-speech interleaving strategies in stage 1: sentence-level and turn-level. Sentence-level interleaving outperforms turn-level interleaving across all spoken language understanding benchmarks in Table 5.
