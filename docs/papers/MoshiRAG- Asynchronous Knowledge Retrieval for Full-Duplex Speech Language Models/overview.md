- **Title:** MoshiRAG: Asynchronous Knowledge Retrieval for Full-Duplex Speech Language Models
- **Summary:** MoshiRAG shows that a full-duplex speech language model can improve factual answers by starting external retrieval during the natural lead-in of a spoken response while keeping real-time interaction mostly intact.
- **Paper Type:** system
- **Venue:** arXiv preprint 2026
- **Authors:** Chung-Ming Chien (Toyota Technological Institute at Chicago; Kyutai), Manu Orsini (Kyutai), Eugene Kharitonov (Kyutai; Gradium), Neil Zeghidour (Kyutai; Gradium), Karen Livescu (Toyota Technological Institute at Chicago), Alexandre Defossez (Kyutai; Gradium)
- **Keywords:** full-duplex speech language models, retrieval-augmented generation, asynchronous retrieval, speech question answering, real-time voice agents, tool use
- ## Orientation
    - **Background:** Voice assistants can wait for a turn to finish or keep listening while speaking. The latter is full-duplex speech modeling: the model handles incoming and outgoing audio at the same time.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A spoken assistant can sound fast and natural but still answer factual questions poorly, because speech training carries less world knowledge than text.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** The assistant cannot simply stop talking whenever it needs knowledge; if the lookup finishes late, the useful part of the spoken answer has already passed.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Start with safe lead-in speech, fetch outside knowledge in parallel, then inject that knowledge before the answer reaches its substance.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a speech-systems view of retrieval-augmented generation, meaning fetching outside text before answering, for the gap where a voice assistant must keep listening and speaking while it looks up facts.
      claim_kind:: analyst_assessment
      evidence:: E1, E2
    - **One-Sentence Contribution:** MoshiRAG improves factual answering in real-time spoken conversation by predicting when a question needs outside knowledge and using the response's lead-in time to fetch that knowledge before the important answer words arrive.
      evidence:: E1, E3
    - **Mental Model:** Picture a speaker who starts with a harmless opening phrase while an assistant silently fetches a note, then folds the note into the rest of the answer without stopping the conversation.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is the combination of speech question-answering gains, maintained full-duplex behavior, and backend swaps that improve accuracy without retraining the speech model.
      evidence:: E9, E11, E12
        - Supports C1: Gemma 3 27B retrieval backend; baselines are vanilla Moshi and RAG-data fine-tuned Moshi; metric is response accuracy on speech QA; WebQ reaches 74.7 versus 26.6 and 37.0, and HaluEval reaches 36.3 versus 10.5 and 18.7; support status is positive but judge-based.
          evidence:: E9
        - Supports C2: Full-Duplex-Bench evaluation; baseline is vanilla Moshi; metrics include pause takeover rates and interruption quality; MoshiRAG lowers synthetic pause TOR to 0.32 from 0.99 and scores 3.75 on interruption GPT score versus 0.77; support status is positive but benchmark-limited.
          evidence:: E11
        - Supports C3: same trained MoshiRAG paired with different retrievers; baseline is the default Gemma backend; metric is response accuracy; GPT-4.1 improves TriviaQA from 73.2 to 82.9 and HaluEval from 36.3 to 51.3; support status is positive for backend modularity.
          evidence:: E12
    - **Main Caveat:** The design is only as strong as its transcript, trigger, retriever, and timing: the paper shows response quality drops with automatic speech recognition errors, imperfect reference integration, and retrieval delays beyond the useful window.
      claim_kind:: analyst_assessment
      evidence:: E14, E15, E16
- ## Argument Map
    - **Problem and Stakes:** Full-duplex speech language models, which listen and speak concurrently, are valuable because they preserve interruption handling and fast feedback, but the paper argues their factual question answering is weak and cannot be fixed only by making the real-time speech model larger.
      evidence:: E1, E2
    - **Prior Gap:** Earlier speech retrieval systems either avoid the full-duplex setting, depend on fixed pre-indexed corpora, or repeatedly call a large language model, meaning a text model trained to predict and generate text, on a schedule that can waste computation and ignore conversational need.
      evidence:: E17
    - **Key Insight:** The paper's systems insight is that spoken answers usually contain a lead-in before the answer-bearing words, and this time can hide retrieval latency if the model predicts a retrieval trigger early enough.
      evidence:: E2, E3
    - **Claims:** The paper's claim chain has four falsifiable parts: factuality improves, interaction remains full-duplex, backend changes transfer without retraining, and the same retrieval interface can act like a tool on unseen reasoning tasks.
      claim_kind:: analyst_assessment
        - C1: MoshiRAG improves factual response accuracy over vanilla Moshi and over a vanilla Moshi fine-tuned on the same RAG-style synthetic data, so the gain is attributed to retrieval use rather than only training-data style.
          evidence:: E9
        - C2: MoshiRAG preserves the real-time interaction profile expected from full-duplex systems because retrieval runs asynchronously while the speech front end continues to process incoming and outgoing audio.
          evidence:: E3, E10, E11
        - C3: The system is retrieval-backend agnostic because the trained speech model consumes textual references and can benefit from stronger large-language-model or search backends at inference time without retraining.
          evidence:: E6, E12
        - C4: The retrieval interface generalizes beyond the question-answering training distribution by letting the speech model use a backend as an external tool for mathematical reasoning datasets.
          evidence:: E12
- ## Mechanism and Design
    - **Core Mechanism:** MoshiRAG keeps Moshi as the audio front end, meaning the component that directly handles user speech, and adds a special <ret> token that starts retrieval-augmented generation (RAG), where outside text is fetched and injected into the continuing response.
      evidence:: E3, E4, E5
    - **Data / Control Flow:** The system flows from audio to trigger to text retrieval to reference injection: the speech model keeps producing audio while a streaming automatic speech recognition (ASR) model produces text for the retrieval backend.
      evidence:: E3, E4
        - Step 1: Moshi receives user speech tokens and its own previous speech and text tokens, then predicts <ret> when the conversation appears to need external facts.
          evidence:: E3, E5
        - Step 2: the system waits for the ASR transcript, sends the aggregated user and assistant text context to an LLM-based or web-search backend, and receives a concise reference document.
          evidence:: E3, E6
        - Step 3: the reference text is encoded, compressed, projected, and streamed into the temporal Transformer input while the spoken response moves from pre-RAG lead-in content to grounded answer content.
          evidence:: E3, E5
    - **Design Decisions:** The central design tradeoff is to give the backend enough time and knowledge while keeping the foreground speech stream short, stable, and responsive.
      claim_kind:: analyst_assessment
      evidence:: E2, E8, E13
        - Need: avoid wasteful retrieval; design choice: predict <ret> only on knowledge-demanding turns; closest alternative reported: fixed-interval calls; tradeoff: trigger reliability now depends on training data and speech intelligibility.
          evidence:: E3, E16, E17
        - Need: preserve long conversations; design choice: additive injection, meaning adding reference embeddings to existing time steps; closest alternative reported: insertive injection; tradeoff: lower integration effectiveness for a fixed sequence-length budget.
          evidence:: E5, E13
        - Need: train timing without real retrieval traces; design choice: lead, body, and tail response segments plus sampled retrieval delays; tradeoff: robustness depends on synthetic script realism and the match between training and inference delay distributions.
          evidence:: E7, E8, E15
    - **Implementation Surface:** The implementation surface is deliberately modular: a 7B Moshi speech model, a 1B streaming ASR model, and a text-in/text-out retrieval backend communicate through transcripts and reference documents, with inference code released publicly.
      evidence:: E4, E6, E18
- ## Evaluation and Evidence
    - **Setup:** Evaluation covers factual speech question answering (QA), HaluEval audio, delay and compute, Full-Duplex-Bench interaction, and out-of-domain math reasoning, mostly using large-language-model judges rather than human raters.
      evidence:: E9, E10, E11, E12
    - **Claim-Evidence Matrix:** The evidence is strongest for C1 and C3, moderate for C2, and exploratory for C4 because the math setting shows tool-use potential but also exposes a large reference-to-speech integration gap.
      claim_kind:: analyst_assessment
      evidence:: E9, E11, E12, E14
        - C1 is backed by multiple speech QA datasets and comparisons to two Moshi baselines, but uncertainty is not reported and correctness depends on LLM judging.
          evidence:: E9
        - C2 is backed by delay analysis and Full-Duplex-Bench metrics, but the benchmark scenarios do not fully cover open-ended multi-turn factual conversation.
          evidence:: E10, E11
        - C3 and C4 are backed by backend-swap experiments and math datasets, with the caveat that response accuracy remains below reference accuracy when references are complex.
          evidence:: E12, E14
    - **Headline Results:** MoshiRAG's practical result is not that a 7B speech model becomes the best fact model, but that it can borrow stronger text or search backends while keeping the full-duplex speech interface.
      evidence:: E9, E11, E12
        - QA result: Gemma-backed MoshiRAG reaches 80.3 LlamaQ, 74.7 WebQ, 73.2 TriviaQA, and 36.3 HaluEval response accuracy; GPT-4.1 and Tavily improve difficult datasets further.
          evidence:: E9, E12
        - Interaction result: MoshiRAG reduces premature turn-taking relative to vanilla Moshi and improves interruption handling, while the authors attribute part of the interaction shift to longer knowledge-intensive training turns.
          evidence:: E11
        - Math result: on AddSub, MultiArith, SinglEq, SVAMP, and GSM8K, MoshiRAG improves greatly over vanilla Moshi but remains constrained by reference complexity and spoken integration.
          evidence:: E12, E14
    - **Ablations and Sensitivity:** Ablations make the system boundary clear: reference encoding, injection timing, ASR quality, and retrieval latency are all load-bearing rather than incidental implementation details.
      evidence:: E13, E14, E15
        - Architecture sensitivity: insertive injection is more accurate in controlled settings, but additive ARC-Encoder-four is chosen because it better preserves sequence length and streaming conversation.
          evidence:: E13
        - Context sensitivity: ground-truth user text improves retrieved and final answers, while ground-truth HaluEval references expose information loss between reference availability and spoken response production.
          evidence:: E14
        - Latency sensitivity: retrieval delays above 1.5 seconds sharply hurt accuracy, so backend speed is part of the method rather than a deployment afterthought.
          evidence:: E15
    - **Reproducibility Gaps:** Inference code and demos are reported, but the paper does not present a complete reproduction package for training data generation, full synthetic corpora, judge variance, repeated runs, or all backend API timing conditions.
      claim_kind:: analyst_assessment
      evidence:: E7, E9, E12, E18
- ## Technical Judgment
    - **What Holds Up:** The systems decomposition holds up: keeping the fast audio loop separate from the slower knowledge loop is a plausible way to improve factuality without making every audio frame depend on a large reasoning model.
      claim_kind:: analyst_assessment
      evidence:: E3, E4, E9, E10
    - **Where It May Fail:** Benefits should diminish when user speech is noisy, the query needs a long or symbolic reference, retrieval exceeds the lead-in window, or the learned trigger misses hard questions because it has no explicit difficulty estimator.
      claim_kind:: analyst_assessment
      evidence:: E14, E15, E16
    - **Relation to Other Work:** Technically, MoshiRAG sits between turn-based speech RAG and always-calling full-duplex tool systems: it keeps dual-stream audio interaction, but makes retrieval event-driven and backend-agnostic rather than fixed-corpus or fixed-interval.
      claim_kind:: analyst_assessment
      evidence:: E6, E17
    - **Transferable Lesson:** The reusable pattern is latency hiding with semantic slack: identify a period where the user needs conversational continuity more than final content, then run the expensive knowledge operation in that hidden window.
      claim_kind:: analyst_assessment
      evidence:: E2, E3, E13, E15
- ## Glossary
  collapsed:: true
    - full-duplex speech language model: A spoken dialogue model that can listen to user audio and generate its own speech at the same time, rather than waiting for strict turn boundaries.
    - retrieval-augmented generation: A generation pattern where the model receives external reference text retrieved from a database, search system, or language model before producing the answer.
    - keyword delay: Keyword delay is the time from response start to the answer-bearing word; E2EKD adds the delay before the first audio token.
    - time-to-first-audio-token: The delay between the end of the user's utterance and the model's first generated audio token, excluding codec or vocoder conversion.
    - retrieval trigger token: A special token generated by MoshiRAG when the current turn should start an external lookup.
    - automatic speech recognition: A model that converts user speech into text; in MoshiRAG it supplies the text context sent to the retriever while audio interaction continues.
    - pre-RAG content: The spoken content produced after retrieval is triggered but before retrieved information is available, usually a coarse answer or conversational lead-in.
    - ARC-Encoder: A text encoder used to compress retrieved reference text into a shorter embedding sequence before it is injected into Moshi.
    - additive injection: The design that adds reference embeddings to existing Moshi time-step inputs instead of inserting extra time steps into the sequence.
    - interaction metrics: TOR is takeover rate in Full-Duplex-Bench; JSD is Jensen-Shannon divergence, used there to compare backchannel timing distributions.
    - word error rate: The fraction of words transcribed incorrectly by ASR; the paper uses it to analyze how speech intelligibility affects retrieval triggering.
    - question answering: A factual evaluation setting where spoken user questions are paired with ground-truth text answers and model responses are judged for correctness.
- ## Evidence Index
  collapsed:: true
    - **E1:** problem/paper_statement | Abstract and Introduction | high
      locator:: Abstract; Section 1
      quote:: Full-duplex models provide real-time interactivity but factuality remains open; the paper proposes MoshiRAG, combining a compact full-duplex interface with selective retrieval to access stronger knowledge sources.
    - **E2:** system_design/paper_statement | System Design | high
      locator:: Section 3.1; Figure 2
      quote:: For retrieval-augmented systems, retrieval delay must be shorter than end-to-end keyword delay so retrieved information can be integrated in time; the paper targets retrieval delay no more than two seconds.
    - **E3:** method/implementation_detail | System Design | high
      locator:: Section 3.2; Figures 3 and 4
      quote:: When the retrieval trigger token is predicted, conversation transcripts from ASR and Moshi outputs are sent to the retrieval backend; Moshi continues in full duplex until retrieved text is encoded and injected.
    - **E4:** implementation/implementation_detail | Building Blocks | high
      locator:: Section 3.3
      quote:: MoshiRAG consists of a 7B Moshi model fine-tuned with RAG data, a 1B streaming ASR model, and a retrieval backend; components communicate entirely in text format.
    - **E5:** algorithm/implementation_detail | RAG Augmented Moshi Model | high
      locator:: Section 3.3.1
      quote:: Retrieved reference text is encoded as embeddings, projected by a trainable linear layer, and summed into Moshi's temporal Transformer input in streaming fashion; ARC-Encoder compresses reference sequence length by four.
    - **E6:** system_design/implementation_detail | Retrieval Back End | high
      locator:: Section 3.3.3
      quote:: The paper evaluates LLM-based retrieval that generates concise factual references and search-based retrieval using Tavily, choosing general-purpose tools rather than standard fixed RAG databases.
    - **E7:** experiment_setup/paper_statement | Data Generation | high
      locator:: Sections 4.1.1 and 4.1.2; Tables 4 and 5
      quote:: Training uses synthetic spoken conversations from QA-derived topics, LLM-generated expert-domain topics, multi-turn prompt variants, and a single-turn QA subset totaling about 1.9M conversation instances.
    - **E8:** algorithm/implementation_detail | Training | high
      locator:: Section 4.2
      quote:: The retrieval token is placed before the first token of the lead portion, retrieval delay is sampled during training, reference dropout is used, and Moshi is trained for 100k updates with batch size 32.
    - **E9:** result/experiment_result | Factuality | medium
      locator:: Section 5.1; Tables 1 and 9
      quote:: With Gemma retrieval, MoshiRAG response accuracy reaches 80.3 on LlamaQ, 74.7 on WebQ, 73.2 on TriviaQA, and 36.3 on HaluEval, exceeding vanilla Moshi and RAG-data fine-tuned Moshi.
    - **E10:** result/experiment_result | Delay and Computation Consumption | medium
      locator:: Section 5.2; Table 1
      quote:: The paper reports that the conversational lead increases keyword delay by about one second, while MoshiRAG still has lower end-to-end keyword delay than nearly all competing systems and comparable computation.
    - **E11:** result/experiment_result | Interactivity | medium
      locator:: Section 5.3; Table 2
      quote:: On Full-Duplex-Bench, MoshiRAG has lower pause takeover rates than vanilla Moshi, low interruption latency, and a higher interruption GPT score; the authors attribute behavior partly to RAG data distribution.
    - **E12:** result/experiment_result | Experiments of Diverse Retrieval Back Ends | medium
      locator:: Sections 5.4 and B.3; Tables 3, 9, and 10
      quote:: Switching retrievers changes outcomes without retraining: GPT-4.1 improves TriviaQA and HaluEval response accuracy, and math datasets show MoshiRAG can use retrieved reasoning beyond QA-style training.
    - **E13:** ablation/ablation | Justification of Model Architecture | medium
      locator:: Appendix B.1; Tables 6 and 7
      quote:: Insertive injection outperforms additive injection but increases sequence length; ARC-Encoder with compression ratio four and additive injection is adopted to balance performance, timing, and long-form conversation.
    - **E14:** ablation/ablation | Sensitivity to ASR and Reference Correctness | medium
      locator:: Appendix B.2; Table 8
      quote:: Ground-truth user text improves retrieved references and final responses by up to about fifteen percent; HaluEval ground-truth references reveal a large gap between reference accuracy and spoken response accuracy.
    - **E15:** limitation/case_study | Further Analysis of Moshi Performance | medium
      locator:: Appendix C; Figure 6
      quote:: RAG trigger rates generally decline as WER increases, and response accuracy drops sharply when retrieval latency exceeds 1.5 seconds across almost all datasets.
    - **E16:** limitation/limitation | Conclusion and Impact Statement | high
      locator:: Section 6; Impact Statement
      quote:: The authors state that retrieval triggering currently relies on training data and future work should link retrieval decisions to query difficulty, diversify tools, and improve robustness against retrieval errors.
    - **E17:** prior_work/paper_statement | Related Work | high
      locator:: Section 2
      quote:: The paper contrasts MoshiRAG with StreamRAG, which is non-full-duplex and fixed-corpus, and KAME, which supports full duplex but relies on frequent fixed-interval LLM calls.
    - **E18:** metadata/metadata | Introduction | high
      locator:: Section 1 footnotes
      quote:: The authors say they release MoshiRAG inference code on GitHub together with demo videos for public access.
