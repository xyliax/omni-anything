- **Title:** VideoLLM Knows When to Speak: Enhancing Time-Sensitive Video Comprehension with Video-Text Duet Interaction Format
- **Summary:** The paper reframes video-language interaction as a streaming turn-taking problem, showing that a VideoLLM can answer time-sensitive questions more naturally by deciding when to speak during playback rather than after the whole video ends.
- **Paper Type:** system
- **Venue:** arXiv preprint 2025
- **Authors:** Yueqian Wang, Xiaojun Meng, Yuxuan Wang, Jianxin Liang, Jiansheng Wei, Huishuai Zhang, Dongyan Zhao; Peking University, Huawei Noah's Ark Lab, Beijing Institute for General Artificial Intelligence, State Key Laboratory of General Artificial Intelligence
- **Keywords:** video large language models, streaming video understanding, time-sensitive video comprehension, temporal grounding, dense video captioning, multi-answer grounded video QA
- ## Orientation
    - **Background:** Video-language systems try to describe and answer questions about moving scenes. The hard part is not only recognizing what appears, but linking words to the moment when an event happens.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** Most systems behave like a person who watches a whole clip, then answers. That is awkward when the video keeps going or when the answer should arrive at the relevant moment.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** The model must judge both what changed and whether that change matters to the user's question before seeing the future.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Treat the video as an active speaker and let the assistant interrupt playback when the current frames justify a reply.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a video large language model (VideoLLM) paper about interaction format: it argues that waiting for the whole video is the wrong interface for live or time-localized understanding.
      claim_kind:: analyst_assessment
      evidence:: E2, E3
    - **One-Sentence Contribution:** MMDuet improves time-sensitive video comprehension by letting the model watch frames as a stream and decide after each frame whether a response should be emitted.
      evidence:: E3, E4, E5
    - **Mental Model:** Think of the video as a third speaker in a conversation: it keeps taking turns by showing frames, while the user and assistant can interrupt when they have something useful to say.
      claim_kind:: analyst_assessment
      evidence:: E3
    - **Best Evidence:** The strongest support is that the same streaming representation improves multiple time-localized tasks, including frame relevance, dense captioning text quality, multi-answer real-time QA, and proactive output.
      evidence:: E8, E9, E11, E12
        - Supports C2: zero-shot QVHighlights and Charades-STA; closest controlled baseline LLaVA-OV-VT; mAP 31.3 vs 19.0 and R@IoU=0.5 42.4 vs 36.5; medium support because variance is not reported.
          evidence:: E8
        - Supports C4: YouCook2 dense captioning with previous assistant turns removed; strongest listed non-MMDuet text-quality baseline; CIDEr 8.8 vs 5.0; medium support because temporal F1 remains mixed.
          evidence:: E9
        - Supports C1: Shot2Story-MAGQA prolonged videos; closest controlled baselines LLaVA-OV-TC and LLaVA-OV-VT answer after the whole video; MMDuet t=0.3 in-span score 2.63/2.45 vs 1.67/1.62 and 1.64/1.60; medium support because it trades accuracy for many duplicate turns.
          evidence:: E11
        - Supports C4: StreamingBench Proactive Output; streaming baselines VideoLLM-Online and Dispider; MMDuet t=0.4 accuracy 31.85 vs 3.92 and 25.34; medium support because non-streaming proprietary systems score higher under a different protocol.
          evidence:: E12
    - **Main Caveat:** The paper shows a useful interaction pattern, not a fully settled real-time system: timing still depends on thresholds, smoothing, and duplicate-response suppression, and result tables do not report statistical uncertainty.
      claim_kind:: analyst_assessment
      evidence:: E10, E14
- ## Argument Map
    - **Problem and Stakes:** The paper targets time-sensitive video comprehension: tasks where a model must connect language to specific video moments, not just summarize after all frames are available. Whole-video interaction blocks live uses such as surveillance or broadcast assistance and forces temporal grounding into fragile text outputs.
      evidence:: E2
    - **Prior Gap:** Prior VideoLLM work mostly changed model architecture, training data, or textual time representations such as seconds, percentages, or special tokens; the interaction format itself remained underexplored. VideoLLM-Online is closest, but the authors claim it did not broadly test how streaming interaction changes zero-shot time-sensitive capabilities.
      evidence:: E16
    - **Key Insight:** If the video stream is represented as a conversation participant, response timing becomes part of the modeling problem rather than a post-processing timestamp string. This lets the model learn from local frame-level evidence and keeps generation close to the moment being described.
      evidence:: E3, E4
    - **Claims:** The paper's claim chain is that changing turn-taking creates a better supervision target for time-sensitive video reasoning, and that this can be added to a strong existing backbone with modest training.
      evidence:: E3, E4, E6, E8
        - C1: The video-text duet interaction format enables real-time responses because the model can interrupt after any consumed frame instead of waiting for an end-of-video turn.
          evidence:: E3, E5, E10
        - C2: Separate informative and relevance heads provide better response-timing signals than asking the language-model head alone to emit a special interruption token.
          evidence:: E4, E8
        - C3: MMDuetIT, a 109k-example instruction-tuning dataset reformatted from dense captioning, grounded QA, and temporal grounding sources, is sufficient to adapt a LLaVA-OneVision backbone to the duet format.
          evidence:: E6, E7
        - C4: MMDuet improves several time-sensitive tasks, but the gains are strongest where frame-level relevance or timely emission matters more than exact start-end span generation.
          evidence:: E8, E9, E11, E12
- ## Mechanism and Design
    - **Core Mechanism:** MMDuet keeps the usual VideoLLM stack, but adds two binary classifiers on the final hidden state of the last visual token for each frame. The informative head estimates whether the frame adds enough new content, while the relevance head estimates whether the frame relates to the user query.
      evidence:: E4
        - The informative score is trained from segment-caption timing: frames after enough of a segment has been seen and before the inserted response are labeled positive.
          evidence:: E13
        - The relevance score is trained from temporal grounding annotations and can be reused directly for highlight detection and temporal localization.
          evidence:: E4, E6, E8
    - **Data / Control Flow:** At inference time, MMDuet processes user text turns and frames in timestamp order, updating the key-value attention cache (KV cache), the saved transformer attention state that avoids recomputing prior tokens. After each frame it computes informative and relevance scores, calls a task-specific need_response rule, and generates a text turn only if that rule fires.
      evidence:: E5
        - For dense video captioning, need_response accumulates informative scores until a threshold is reached, emits a caption, then resets the sum.
          evidence:: E9
        - For multi-answer grounded video question answering (MAGQA), need_response fires when the sum of informative and relevance scores for the current frame exceeds threshold t.
          evidence:: E10
        - For highlight detection and temporal grounding, the relevance score sequence is normalized or thresholded and then smoothed with nearby frames.
          evidence:: E8
    - **Design Decisions:** The main design choice is to move temporal decisions from generated timestamp text into frame-level scores, while still using the language model for natural-language content. This is a practical compromise: it avoids forcing the model to count time precisely, but it introduces task-specific thresholds and smoothing.
      claim_kind:: analyst_assessment
      evidence:: E4, E8, E14
        - Need: support live streams; choice: make the stream a third role; closest alternative: whole-video query-answer interaction; tradeoff: the model loses access to future frames when speaking in time.
          claim_kind:: analyst_assessment
          evidence:: E2, E3, E14
        - Need: decide when to speak; choice: supervised informative and relevance heads; closest alternative: a special language token as in VideoLLM-Online; tradeoff: better controllability but additional labels and thresholds.
          evidence:: E4, E16
        - Need: teach timely but not premature responses; choice: randomly insert responses after the middle of each annotated segment and label multiple informative frames; tradeoff: empirical timing assumptions rather than learned future-aware boundaries.
          evidence:: E13
    - **Implementation Surface:** The implementation modifies a LLaVA-OneVision backbone with trainable projection, informative head, relevance head, and low-rank adaptation (LoRA), a small trainable update to selected language-model weights while most parameters stay frozen. It also reduces per-frame visual token count and caps sampled frames for memory-controlled training and inference.
      evidence:: E7
        - Training is reported as one epoch on MMDuetIT, about one day on eight Tesla V100 GPUs, with inference on one Tesla V100 GPU.
          evidence:: E7
        - The streaming loop relies on KV cache updates for both frames and text turns, which is necessary because the same growing conversation state is reused after each frame.
          evidence:: E5
- ## Evaluation and Evidence
    - **Setup:** The evaluation covers highlight detection on QVHighlights, temporal grounding on Charades-STA, dense video captioning on YouCook2, MAGQA on Shot2Story-MAGQA-39k, and proactive output on StreamingBench. The paper compares against timestamp-style VideoLLMs, streaming baselines, and controlled LLaVA-OneVision variants trained on the same data but using TimeChat-like or VTimeLLM-like formats.
      evidence:: E7, E8, E10, E12
    - **Claim-Evidence Matrix:** The evidence is strongest for C2 and C4 on frame-level relevance and streaming output, moderate for C1 on real-time QA because the baselines get a simpler offline setting, and weakest for exact dense-caption temporal spans.
      claim_kind:: analyst_assessment
      evidence:: E8, E9, E11, E12
        - C1 is supported by MAGQA and StreamingBench because MMDuet emits during playback, but the MAGQA score increases as threshold t decreases at the cost of more duplicate turns and higher time per example.
          claim_kind:: analyst_assessment
          evidence:: E10, E11, E12
        - C2 is supported by QVHighlights and Charades-STA, where direct frame-level relevance scores outperform text-form span outputs from controlled baselines.
          evidence:: E8
        - C3 is partially supported: the paper reports small-data, one-epoch adaptation from a strong backbone, but does not isolate all benefits from backbone strength outside the controlled LLaVA-OneVision variants.
          claim_kind:: analyst_assessment
          evidence:: E6, E7
        - C4 is supported across several tasks, but dense captioning shows the boundary: text metrics improve after removing previous responses, while F1 for temporal segmentation is not clearly better.
          claim_kind:: analyst_assessment
          evidence:: E9
    - **Headline Results:** The cleanest quantitative win is frame relevance: MMDuet reports QVHighlights mAP/HIT@1 of 31.3/49.6 and Charades-STA R@IoU=0.5/0.7 of 42.4/18.0, beating the controlled LLaVA-OV-VT baseline on both datasets. On MAGQA, MMDuet is real-time and improves substantially on prolonged videos, while StreamingBench shows it competitive with or above streaming/proactive open baselines.
      evidence:: E8, E11, E12
        - Supported claim: C2; configuration: zero-shot frame relevance; baseline: LLaVA-OV-VT; metric and direction: higher QVHighlights mAP/HIT@1 and Charades-STA R@IoU; delta: +12.3 mAP and +5.9 R@0.5.
          evidence:: E8
        - Supported claim: C1; configuration: 5-time prolonged MAGQA; baseline: LLaVA-OV-TC; metric and direction: higher in-span score; delta at t=0.3: +0.96/+0.83, with no reported repeat count.
          evidence:: E11
        - Supported claim: C4; configuration: StreamingBench Proactive Output; baseline: Dispider among streaming systems; metric and direction: higher accuracy; delta: MMDuet t=0.4 is +6.51 points over Dispider.
          evidence:: E12
    - **Ablations and Sensitivity:** The ablation evidence is narrow but useful: on YouCook2, disabling random response positions or multi-frame informative labels hurts the reported dense-captioning metrics. The sensitivity figures also suggest smoothing window w and dense-caption threshold s have tolerable ranges, but these remain empirical knobs rather than learned policies.
      evidence:: E13, E14
        - Removing random response position changes YouCook2 from 2.9/8.8/21.7 to 2.1/7.3/19.0, supporting the claim that timing diversity matters.
          evidence:: E13
        - Removing multi-frame informative labels changes YouCook2 from 2.9/8.8/21.7 to 2.9/8.0/16.5, supporting the claim that the head should learn a response interval rather than a single trigger frame.
          evidence:: E13
    - **Reproducibility Gaps:** The paper reports backbone, training resources, hyperparameters, sampling settings, metric definitions, and a manual MAGQA quality check, but the supplied text does not report code, checkpoints, random seeds, repeat counts, confidence intervals, or full prompt/evaluator stability beyond using two scoring models for in-span score. That makes the direction of the results useful while leaving statistical reliability and end-to-end reproduction unresolved.
      claim_kind:: analyst_assessment
      evidence:: E7, E10, E15
- ## Technical Judgment
    - **What Holds Up:** The core mechanism is convincing because it changes the object being predicted: frame-level usefulness and relevance are easier to supervise and consume than generated timestamp strings. The controlled baselines make the interaction-format argument stronger than a pure model-size comparison, especially for QVHighlights and Charades-STA.
      claim_kind:: analyst_assessment
      evidence:: E4, E7, E8
    - **Where It May Fail:** The approach is weakest when a correct response requires future evidence, exact segment starts, or suppression of near-duplicate turns. It also depends on hand-set need_response thresholds and smoothing windows, so deployment quality may vary by video pace and task.
      claim_kind:: analyst_assessment
      evidence:: E9, E10, E14
    - **Relation to Other Work:** Compared with timestamp-number or percentage-based VideoLLMs, MMDuet externalizes time as stream position and frame scores, reducing the burden on a language model to count and emit precise numbers. Compared with VideoLLM-Online, it separates why to speak into informative and relevance scores rather than a single generated interruption signal.
      claim_kind:: analyst_assessment
      evidence:: E4, E16
    - **Transferable Lesson:** For multimodal systems, interface format can be a learning target: when the task needs timely action, train explicit state signals at the lifecycle point where the system must decide, then let generation handle only the content. This pattern transfers beyond video to agents that must decide when to notify, ask, or act during a stream.
      claim_kind:: analyst_assessment
      evidence:: E3, E4, E5
- ## Glossary
  collapsed:: true
    - Video large language model: A model that combines visual video features with a language model so it can answer or describe video content in text.
    - Video-text duet interaction format: The paper's interaction rule where the video stream, user, and assistant take alternating turns, and text can be inserted during playback.
    - Time-sensitive video comprehension: Video understanding tasks where the answer must be tied to when something happens, such as grounding, highlight detection, or dense captioning.
    - MMDuetIT: The instruction-tuning dataset built by reformatting dense captioning, multi-answer grounded QA, and temporal grounding data into the duet interaction format.
    - Multi-Answer Grounded Video Question Answering: A task where one user question can require multiple answers at different relevant moments during the same video.
    - Informative head and relevance head: Two binary classifiers added to MMDuet: one estimates whether the current frame adds new information, and the other estimates whether it relates to the user query.
    - Key-value attention cache: Saved attention state from previous tokens or frames that lets a transformer continue a growing stream without recomputing all prior context.
    - need_response: The task-specific rule that converts current and previous informative or relevance scores into a decision about whether the assistant should speak.
    - Task metrics: The paper uses retrieval/localization, caption quality, and proactive-output metrics; higher is better for all metrics cited in this note.
    - In-span score: MAGQA metric that scores predicted answers only when their predicted time falls inside a ground-truth answer span, using a language model to rate text similarity.
    - Low-rank adaptation: A parameter-efficient fine-tuning method that trains small low-rank updates while leaving most model weights frozen.
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/metadata | Title and author block | high
      locator:: arXiv header and title block
      quote:: arXiv:2411.17991v2 [cs.CV] 23 Nov 2025. VideoLLM Knows When to Speak: Enhancing Time-Sensitive Video Comprehension with Video-Text Duet Interaction Format. Yueqian Wang, Xiaojun Meng, Yuxuan Wang, Jianxin Liang, Jiansheng Wei, Huishuai Zhang, Dongyan Zhao.
    - **E2:** problem/paper_statement | 1 Introduction | high
      locator:: intro discussion of whole video interaction
      quote:: this limits its usage in more scenarios like live broadcasts or surveillance videos, in which the video does not end at a specific time. Even if we can segment the video into multiple fixed-length clips for input, the model still cannot generate responses in a real-time manner when necessary
    - **E3:** method/paper_statement | 3 The Video-Text Duet Interaction Format | high
      locator:: Section 3 formal definition
      quote:: we consider the video stream as a conversation participant just like the role of user/assistant, and the input sequence consists of alternating turns among these three roles. When each single frame is consumed, both the user and the assistant role can interrupt the video stream at any time
    - **E4:** implementation/implementation_detail | 4.1 Model Structure | high
      locator:: two added heads paragraph
      quote:: The only difference in model structure between our MMDuet and existing VideoLLMs is that we add two more heads in addition to the language modeling head, namely the informative head and the relevance head, for determining whether to start a response after each frame.
    - **E5:** algorithm/implementation_detail | 4.2 Inference Procedure | high
      locator:: inference procedure paragraph and Listing 1
      quote:: When consuming every single sampled frame of the video, we first check if there is a user query happening at this time. Then the sampled frame is input to the model, after which the informative score and relevance score are calculated. We use a function need_response to estimate whether the model should generate an assistant response
    - **E6:** method/paper_statement | 5 MMDuetIT: Dataset for Training MMDuet | high
      locator:: Sections 5.1 to 5.4
      quote:: MMDuetIT is composed of three different types of tasks that benefit our model training: dense captioning, multi-answer grounded video question answering, and temporal video grounding. The data distribution of MMDuetIT is shown in Fig. 3. Note that this dataset only contains 109k examples
    - **E7:** experiment_setup/paper_statement | 6 Experiments | high
      locator:: implementation and baselines paragraphs
      quote:: MMDuet is initialized with LLaVA-OneVision. We train the model on MMDuetIT for one epoch. The training takes about one day on a node with 8 Tesla V100 GPUs, and the inference runs on 1 Tesla V100 GPU. Since the initialization of MMDuet is stronger than that of the baselines, for a fair comparison we also conduct a controlled experiment
    - **E8:** result/experiment_result | 6.1 Highlight Detection and Temporal Video Grounding | medium
      locator:: Table 1 and Section 6.1 discussion
      quote:: Table 1: Zero-shot performance on highlight detection, temporal video grounding, and dense video captioning. LLaVA-OV-VT reports QVHighlights 19.0/40.0 and Charades-STA 36.5/12.3, while MMDuet reports QVHighlights 31.3/49.6 and Charades-STA 42.4/18.0.
    - **E9:** result/experiment_result | 6.2 Dense Video Captioning | medium
      locator:: Table 1 and dense captioning discussion
      quote:: MMDuet does not show significant improvements on F1 metric, likely due to the simple solution we use to derive the start and end time based on responses. Even so, the CIDEr and SODA_c metric of MMDuet is still higher than all baselines. Table 1 reports + rm. prev. resp. as 2.9/8.8/21.7.
    - **E10:** experiment_setup/paper_statement | 6.3 Multi-Answer Grounded Video QA | high
      locator:: task and metric definition paragraphs
      quote:: MAGQA requires the answers to be both informative and related to the question, we set need_response as: if the sum of informative score and relevance score of a frame is larger than a threshold t, then the model needs to generate a response right after this frame.
    - **E11:** result/experiment_result | 6.3 Multi-Answer Grounded Video QA | medium
      locator:: Table 2 and prolonged-video discussion
      quote:: MMDuet t = 0.3 reports original in-span score 3.13/2.93 and 5-time prolonged video score 2.63/2.45. LLaVA-OV-TC reports 2.77/2.64 original and 1.67/1.62 prolonged, while LLaVA-OV-VT reports 2.54/2.42 original and 1.64/1.60 prolonged.
    - **E12:** result/experiment_result | 6.4 Proactive Output on StreamingBench | medium
      locator:: Tables 3 and 6
      quote:: Table 3: Performance on the Proactive Output task of StreamingBench. Flash-VStream 1.96, VLLM-Online 3.92, Dispider 25.34, MMDuet 29.44. Table 6 reports MMDuet t = 0.4 at 31.85.
    - **E13:** ablation/ablation | 6.5 Ablation Studies | medium
      locator:: Table 4 and ablation paragraph
      quote:: We conduct ablation studies on YouCook2 dense video captioning to assess two empirical yet important findings: randomly inserting the response at a position from 50% to 75% of the corresponding video segment, and setting informative head's label to TRUE for all frames between 50% of the segment and the response time. Table 4 reports MMDuet 2.9/8.8/21.7, w/o rand. resp. pos. 2.1/7.3/19.0, and w/o multi informative 2.9/8.0/16.5.
    - **E14:** limitation/limitation | Limitations | high
      locator:: Limitations paragraph
      quote:: Some hyperparameters are required during inference. Information from subsequent frames is not incorporated when generating in-time responses for the current frame. Slow inference speed. A better inference process is needed for avoid generating duplicate responses. Real-time response datasets with longer live-streaming videos are required
    - **E15:** experiment_setup/case_study | A Data Quality Check of Shot2Story-MAGQA-39k | medium
      locator:: Appendix A
      quote:: We sample 100 examples with 290 answers from our test set for manual quality assessment. Among the sampled examples, we find 1 example with a question unanswerable from the video, 5 examples have 6 answers that contradict the video content, and 5 examples have 7 answers unrelated to the question.
    - **E16:** prior_work/paper_statement | 2 Related Works | high
      locator:: related work comparison paragraphs
      quote:: Recent works attempt to empower VideoLLMs with the ability to localize and represent segments in videos. These works explore new ways on how to easily represent video clips with texts, such as second numbers of timestamp, timeline percentage or using special textual tokens. The work most similar to our motivation is VideoLLM-Online
