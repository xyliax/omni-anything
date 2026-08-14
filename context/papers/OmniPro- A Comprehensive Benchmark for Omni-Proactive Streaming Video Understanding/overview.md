- **Title:** OmniPro: A Comprehensive Benchmark for Omni-Proactive Streaming Video Understanding
- **Summary:** OMNIPRO turns proactive streaming video understanding into a time-triggered, audio-visual benchmark that exposes whether models can understand content, decide when to speak, and sustain performance over long streams.
- **Paper Type:** benchmark
- **Venue:** arXiv preprint 2026
- **Authors:** Ruixiang Zhao (Renmin University of China); Jie Yang (WeChat Vision, Tencent Inc.); Zijie Xin (Renmin University of China); Tianyi Wang (WeChat Vision, Tencent Inc.); Fengyun Rao (WeChat Vision, Tencent Inc.); Jing Lyu (WeChat Vision, Tencent Inc.); Xirong Li (Renmin University of China)
- **Keywords:** omni-proactive streaming video understanding, benchmark, audio-visual video understanding, proactive responding, long-horizon perception, multimodal evaluation
- ## Orientation
    - **Background:** Streaming video assistants watch a live feed rather than a finished clip. Useful behavior here means listening to speech and ambient sounds, watching visual changes, and remembering what has just happened.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A user gives a standing instruction, then the assistant must notice the right moment and speak without being pinged again.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** The useful signal may arrive through speech, background sound, visual motion, or their combination, and the assistant must avoid speaking too early, too late, or too often.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Test the assistant as a timed listener: give it a standing instruction, mark the moments where a response belongs, and score both timing and content.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a benchmark-design paper for proactive streaming video understanding, the setting where a model watches a live stream and decides when to answer; its useful lens is how to test modality, meaning input type such as vision, speech, or sound, without confusing offline question answering for real proactivity.
      claim_kind:: analyst_assessment
      evidence:: E2, E3, E17
    - **One-Sentence Contribution:** OMNIPRO improves evaluation of streaming video assistants by converting videos into standing-instruction tests with human-checked trigger times, expected responses, and a protocol that tests both content understanding and self-timed responding.
      evidence:: E1, E8
    - **Mental Model:** Picture a careful event monitor: it is given a rule at the start, watches and listens continuously, keeps track of what has changed, and should tap the user only when the rule has actually become true.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is not a single leaderboard win but the benchmark's diagnostic slices: model scores change sharply by response mode, input modality, trigger time, and sound type.
      evidence:: E10, E11, E12, E13
        - Supports C1: OMNIPRO versus prior proactive video benchmarks; baseline is StreamingBench-Pro, OVO-Bench-Pro, and OmniMMI-Pro; metric is capability coverage and audio dependency; delta is all six capabilities with speech and non-speech sound versus at most two capabilities and no non-speech sound; support status is strong for benchmark coverage.
          evidence:: E1, E17
        - Supports C2: Probe mode queries before and after each known trigger while Online mode streams frames and lets the model decide; baseline is fixed polling or preset query times; metric is accuracy versus F1 score, the harmonic mean of precision and recall; delta is separate tests for content and timing; support status is strong for protocol design.
          evidence:: E8
        - Supports C3: eleven-model evaluation; baseline is current open-source and proprietary systems; metric is mean accuracy, F1 score, audio plus video gain over video-only input, and late-trigger retention; delta includes Gemini-3-Flash at 40.4 mean accuracy, MiniCPM-o 4.5 at 20.9 online F1, A+V gains of 2.4 to 11.1 points, and average long-term retention of 37%; support status is descriptive but broad.
          evidence:: E9, E10, E11, E12
    - **Main Caveat:** The benchmark is most trustworthy as an English, time-triggered diagnostic for model comparison; it does not by itself prove multilingual robustness, real deployment behavior, or statistical stability across repeated runs.
      claim_kind:: analyst_assessment
      evidence:: E9, E14, E16
- ## Argument Map
    - **Problem and Stakes:** The paper studies proactive streaming video understanding, meaning a model must process an ongoing audio-visual stream and decide when to respond without a fresh user query. The stakes are evaluation validity: a benchmark that only asks offline questions can miss whether a future assistant can notice, wait, and interrupt correctly.
      evidence:: E2, E3
    - **Prior Gap:** Prior proactive video benchmarks leave at least one required capability untested: some are visual-only, some poll or query at preset times, and the most proactive prior benchmark still lacks non-speech sound and multi-trigger decision-making.
      evidence:: E2, E17
    - **Key Insight:** A benchmark for this area has to bind the content answer to the response moment; otherwise a model can look good at recognizing video content while failing the real interaction problem of deciding when to speak.
      claim_kind:: analyst_assessment
      evidence:: E3, E8
    - **Claims:** The paper's central claims are about coverage, protocol separation, diagnostic findings, and bounded reuse.
      claim_kind:: analyst_assessment
        - C1: OMNIPRO fills an evaluation gap by jointly requiring audio-visual signals, autonomous response timing, and coverage of all six basic video-understanding capabilities.
          evidence:: E1, E2, E17
        - C2: The dual-mode protocol separates content-understanding evaluation from online proactive behavior, so non-streaming vision-language models and streaming models can be tested under different but related conditions.
          evidence:: E8
        - C3: OMNIPRO is discriminative: tested models remain far from solved and show visible weaknesses by modality, trigger time, generation burden, and non-speech sound.
          evidence:: E10, E11, E12, E13
        - C4: The dataset is human-checked and useful for English proactive streaming evaluation, but its English-only annotations bound claims about multilingual generality.
          evidence:: E6, E14
- ## Mechanism and Design
    - **Core Mechanism:** OMNIPRO turns each video into a standing instruction plus trigger times, where a trigger time is the moment a response should be produced, and expected responses with modality labels. The same samples support a non-streaming content test and a streaming self-timing test.
      evidence:: E1, E8
    - **Data / Control Flow:** The data flow is source videos from LongVALE and COIN, dense audio-visual captions from Gemini 3 Flash, task-specific QA synthesis, two human review rounds, then evaluation samples organized by task, modality labels, trigger timing, and expected response.
      evidence:: E4, E5, E6
        - Source selection supplies broad daily-life, sports, news, and instructional videos, with COIN used to cover tutorial-like sequential instruction.
          evidence:: E5
        - Captioning records visual content, ambient audio, and speech over time, then QA synthesis creates standing instructions, trigger times, responses, trigger modality, and audio dependency.
          evidence:: E5
        - Human review checks naturalness, timing, faithfulness, and modality annotations, then cross-validates sub-tasks to reduce inconsistent task standards.
          evidence:: E6
    - **Design Decisions:** The major design choices make the benchmark diagnostic rather than just larger: prioritize audio-rich triggers, split tasks by cognitive demand, and evaluate content separately from autonomous timing.
      claim_kind:: analyst_assessment
      evidence:: E3, E4, E8
        - Need: distinguish omni-modal models from vision-only models; choice: use an audio-first generation strategy; closest alternative: visual-only event selection; tradeoff: stronger audio diagnostics but a distribution shaped by benchmark intent.
          claim_kind:: analyst_assessment
          evidence:: E5, E7
        - Need: avoid a benchmark that only tests alerts; choice: organize samples into perception, comprehension, and reasoning levels across alerting, monitoring, grounding, counting, narration, and prediction-like guidance; tradeoff: broad coverage with heterogeneous task difficulty.
          claim_kind:: analyst_assessment
          evidence:: E4
        - Need: include models that cannot stream while still testing proactivity where possible; choice: Probe mode tests content around known triggers, while Online mode tests autonomous timing; tradeoff: scores across modes are related diagnostics, not a single interchangeable leaderboard.
          claim_kind:: analyst_assessment
          evidence:: E8
    - **Implementation Surface:** Probe mode gives each model cumulative video up to a query time and scores exact structured answers; Online mode streams frames with dialogue history, aligns predictions to ground-truth triggers within a tolerance window, and uses exact match or an LLM judge, a large language model used to score open-ended answers, for generation-heavy tasks.
      evidence:: E8, E16
        - Probe mode asks before and after each trigger; the trigger is correct only when the pre-probe is negative and the post-probe gives the task-specific correct answer.
          evidence:: E8
        - Online mode computes precision, recall, and F1 score after greedy temporal matching, with a default ±3 second response window.
          evidence:: E8, E16
        - The reported experiments sample videos at 1 fps and run open-source models on NVIDIA A800 80GB GPUs with greedy decoding and a 512-token maximum generation length.
          evidence:: E9
- ## Evaluation and Evidence
    - **Setup:** The evaluation covers proprietary and open-source omni-modal models, vision-language models (VLMs, models that answer from visual input and text), and native streaming models. Probe reports accuracy, while Online reports F1 score after timing and content correctness are both checked.
      evidence:: E8, E9
    - **Claim-Evidence Matrix:** The evidence base is strongest for benchmark coverage and diagnostic breadth, and weaker for statistical certainty because the paper reports descriptive model results without repeat counts, variances, or confidence intervals.
      claim_kind:: analyst_assessment
      evidence:: E1, E9, E10, E11, E12, E13
        - C1: Supported by direct benchmark construction evidence: task taxonomy, modality labels, audio dependency statistics, and prior-benchmark comparison all point to broader coverage than prior proactive video benchmarks.
          claim_kind:: analyst_assessment
          evidence:: E1, E4, E7, E17
        - C2: Supported by the formal Probe and Online definitions; the remaining caveat is that Probe and Online answer different questions, so their numeric scores should not be read as one unified metric.
          claim_kind:: analyst_assessment
          evidence:: E8
        - C3: Supported by broad model comparisons and ablations, but the strength is descriptive rather than statistical because the paper does not report repeated-run uncertainty.
          claim_kind:: analyst_assessment
          evidence:: E10, E11, E12, E13
    - **Headline Results:** The benchmark shows that current systems are far from solved: the best reported Probe scores are modest, the Online setting is harder, audio plus video usually helps over video-only input, late triggers degrade strongly, and visual plus non-speech sound is the weakest trigger category.
      evidence:: E10, E11, E12, E13
        - Overall capability: Gemini-3-Flash reaches 40.4 mean Probe accuracy, while MiniCPM-o 4.5 reaches 20.9 Online F1; this supports C3 but lacks reported uncertainty.
          evidence:: E10
        - Modality contribution: audio plus video (A+V) improves over video-only input by 2.4 to 11.1 points across five omni-modal models, supporting C3's modality-diagnostic claim.
          evidence:: E11
        - Temporal and audio bottlenecks: long-term triggers retain only 37% of short-term performance on average, and visual+sound triggers score lowest across models, supporting C3's long-horizon and non-speech-sound diagnosis.
          evidence:: E12, E13
    - **Ablations and Sensitivity:** The main ablation is modality isolation, which shows complementary audio and video cues and different model fusion patterns; the appendix also varies the Online temporal tolerance window and keeps ±3 seconds as the default. Not reported: statistical uncertainty, repeat counts, or sensitivity to frame rate beyond the stated 1 fps setting.
      evidence:: E9, E11, E16
    - **Reproducibility Gaps:** The paper reports the project page, source datasets, prompts, hardware class, sampling rate, dataset license, and code license, which helps reuse. Concrete gaps for independent reproduction are annotator agreement details, exact generation scripts or model versions beyond named Gemini variants, and repeated-run uncertainty for model evaluations.
      claim_kind:: analyst_assessment
      evidence:: E5, E6, E9, E15
- ## Technical Judgment
    - **What Holds Up:** The benchmark design matches the capability definition: audio-visual triggers, autonomous response timing, multiple task forms, and modality-isolation labels make aggregate scores decomposable. The strongest technical contribution is the evaluation framing, not a new model or algorithm.
      claim_kind:: analyst_assessment
      evidence:: E1, E3, E7, E8
    - **Where It May Fail:** Generality may weaken when the language, domain distribution, timing tolerance, frame rate, or judge behavior changes. Because QA generation starts from Gemini-produced captions and synthesis before human filtering, the benchmark may reflect both real video difficulty and the biases of its generation pipeline.
      claim_kind:: analyst_assessment
      evidence:: E5, E6, E9, E14, E16
    - **Relation to Other Work:** Relative to StreamingBench-Pro and OVO-Bench-Pro, OMNIPRO moves from polling or preset queries toward autonomous timing; relative to OmniMMI-Pro, it adds multi-trigger responses, non-speech sound, and broader video-understanding task coverage.
      evidence:: E17
    - **Transferable Lesson:** For emerging interactive model abilities, benchmark the decision boundary directly: define when the model should act, what information is available at that moment, and which diagnostic labels let failures be sliced by input type, time horizon, and task demand.
      claim_kind:: analyst_assessment
      evidence:: E4, E7, E8
- ## Glossary
  collapsed:: true
    - omni-proactive streaming video understanding: A setting where a model watches and listens to a continuous stream, decides when to respond, and produces the right content without being repeatedly prompted.
    - modality: A channel of information such as visual frames, speech, non-speech sound, or text.
    - proactive responding: The model initiates an answer when the stream warrants it, rather than waiting for a new query or fixed polling time.
    - trigger time: The annotated moment when the model should produce a response.
    - Probe mode: A non-streaming evaluation mode that queries a model before and after each annotated trigger to test whether it understands the event content.
    - Online mode: A streaming evaluation mode where the model receives frames over time and must decide by itself when to answer.
    - modality-isolation label: Annotation describing which input type is needed or helpful for detecting a trigger or answering a sample.
    - non-speech audio: Audio cues other than spoken language, such as alarms, music, whistles, or environmental sounds.
    - F1 score: The harmonic mean of precision and recall; in Online mode it counts a response only when timing and content are both correct.
    - long-horizon perception: The ability to keep useful perception and memory over long video streams so events late in the video are still detected correctly.
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/paper_statement | Abstract | high
      locator:: Abstract
      quote:: We present OMNIPRO, the first benchmark to jointly evaluate omni-modal perception, proactive responding, and diverse video understanding tasks. It comprises 2,700 human-verified samples spanning 9 sub-tasks and 3 cognitive levels, covering 6 basic video understanding capabilities.
    - **E2:** gap/paper_statement | Abstract | high
      locator:: Abstract
      quote:: Existing benchmarks fall short in three key aspects: they rely primarily on visual signals, adopt polling or fixed-timestamp protocols instead of true proactive evaluation, and cover only a limited range of tasks.
    - **E3:** problem/paper_statement | 1 Introduction | high
      locator:: paragraph defining three criteria
      quote:: We argue that such a model must satisfy three key criteria: (1) Omnimodal perception: it should jointly reason over visual signals, speech, and non-speech audio; (2) Proactive responding: it must decide when to respond without external polling or fixed schedules; (3) Diverse video understanding tasks.
    - **E4:** method/paper_statement | 3.1.1 Task Taxonomy | high
      locator:: task taxonomy paragraph
      quote:: We categorize tasks by cognitive ability into three levels, namely Perception, Comprehension, and Reasoning, with increasing difficulty. This yields 9 sub-tasks and 2,700 evaluation samples in total.
    - **E5:** method/implementation_detail | 3.1.2 Source Video Collection and 3.1.3 Automated QA Generation | high
      locator:: source collection and QA synthesis paragraphs
      quote:: Source videos were drawn from the test sets of two public datasets: LongVALE and COIN. For each source video, we employed Gemini 3 Flash to generate temporally aligned multi-modal dense captions with start and end timestamps for each segment.
    - **E6:** method/paper_statement | 3.1.4 Human Quality Control | high
      locator:: human review paragraph
      quote:: The auto-generated data underwent two rounds of human review. In the first round, 9 annotators each reviewed one sub-task using a dedicated tool, verifying question naturalness, trigger time accuracy, response faithfulness, and modality annotation correctness.
    - **E7:** metadata/paper_statement | 3.1.5 Dataset Statistics | high
      locator:: Figure 2 discussion
      quote:: Figure 2b breaks down the trigger modality composition, revealing that visual+speech is the dominant type and nearly half of all triggers exhibit cross-modal characteristics. Figure 2d depicts the distribution of first and last trigger times: the average first trigger occurs at 54.1 s and the last at 126.2 s.
    - **E8:** method/paper_statement | 3.2.1 Evaluation Protocol | high
      locator:: Probe and Online mode definitions
      quote:: Probe mode is compatible with any VLM and does not require streaming capability. For each ground-truth trigger, the evaluator queries the model twice: a pre-probe and a post-probe. Online mode targets streaming models. The model receives the user instruction at the start of the video, then processes subsequent frames one by one.
    - **E9:** experiment_setup/paper_statement | 4.1 Experimental Settings | high
      locator:: evaluated models and implementation details
      quote:: We evaluate 11 representative models spanning two evaluation modes. In Probe mode, we assess 9 models. In Online mode, we evaluate 3 streaming models. All models uniformly sample input video at 1 fps. All open-source model inference is conducted on NVIDIA A800 80GB GPUs.
    - **E10:** result/experiment_result | 4.2 Using OMNIPRO for Assessing Overall Model Capability | medium
      locator:: Table 2 discussion
      quote:: Gemini-3-Flash attains 40.4% average accuracy, nearly double the best open-source model (22.1%), indicating a substantial capability gap. Online mode is considerably harder: MiniCPM-o 4.5 reaches only 20.9% F1, with severe degradation on generation-intensive tasks.
    - **E11:** result/ablation | 4.3 Using OMNIPRO for Disentangling Modality Contributions | medium
      locator:: Table 3 discussion
      quote:: A+V consistently outperforms either single modality, with gains over V ranging from +2.4 (Qwen3-Omni) to +11.1 (video-SALMONN 2+), confirming that the two modalities provide complementary cues.
    - **E12:** result/experiment_result | 4.4 Using OMNIPRO for Evaluating Long-Horizon Perception | medium
      locator:: Figure 3 discussion
      quote:: All models show substantial degradation for later-occurring triggers, retaining on average only 37% of their Short-term performance at the Long-term. MiniCPM-o 4.5 nearly fails entirely on the Long-term (29.1 to 0.3).
    - **E13:** result/experiment_result | 4.5 Using OMNIPRO for Identifying Modality Bottlenecks | medium
      locator:: Figure 4 discussion
      quote:: All models perform weakest on visual+sound triggers (15.3-22.3), revealing that perceiving and utilizing non-speech audio (e.g., environmental sounds, sound effects) remains a shared bottleneck.
    - **E14:** limitation/limitation | C.1 Limitations | high
      locator:: limitations paragraph
      quote:: All questions and ground-truth annotations in OMNIPRO are written in English, which limits its applicability for evaluating multilingual or non-English proactive streaming models. Extending the benchmark to additional languages is left for future work.
    - **E15:** metadata/paper_statement | C.3 Licenses | high
      locator:: license list
      quote:: LongVALE: CC-BY-NC-SA-4.0. COIN: CC BY-NC 4.0. OMNIPRO (our benchmark): CC BY-NC 4.0. Evaluation code: MIT License.
    - **E16:** ablation/ablation | A.1 Tolerance Window Ablation | medium
      locator:: Figure 5 discussion
      quote:: Figure 5 shows the effect of varying the temporal matching tolerance on joint_F1 for three online-mode models. The tolerance window ranges from ±1 s to ±5 s. We adopt ±3 s as the default in all Online-mode evaluations.
    - **E17:** prior_work/paper_statement | 2.2 Proactive Streaming Video Benchmarks | high
      locator:: summary of prior benchmarks
      quote:: In summary, no existing benchmark simultaneously satisfies all three criteria: none involves non-speech sound, only OmniMMI-Pro supports proactive responding, limited to single-trigger, and at most 2/6 capabilities are covered.
