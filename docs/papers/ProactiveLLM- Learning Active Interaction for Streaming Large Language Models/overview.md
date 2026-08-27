- **Title:** ProactiveLLM: Learning Active Interaction for Streaming Large Language Models
- **Summary:** ProactiveLLM trains streaming large language models to sense when partial input is semantically sufficient, reducing latency and redundant context use without relying on external timing annotations.
- **Paper Type:** system
- **Venue:** ICML 2026
- **Authors:** Junlong Tong (Eastern Institute of Technology, Ningbo; Shanghai Jiao Tong University), Yao Zhang (Eastern Institute of Technology, Ningbo), Anhao Zhao (Eastern Institute of Technology, Ningbo; Hong Kong Polytechnic University), Yingqi Fan (Eastern Institute of Technology, Ningbo), Yunpu Ma (Munich Center for Machine Learning, LMU), Xiaoyu Shen (Eastern Institute of Technology, Ningbo)
- **Keywords:** streaming large language models, active interaction, semantic sufficiency, masked streaming language modeling, self-distillation, latency-quality tradeoff
- ## Orientation
    - **Background:** Streaming language work asks a model to listen and answer as input arrives, instead of waiting for the whole message. The key prerequisite is semantic sufficiency: the point where the partial input already contains enough meaning for a safe next output.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** In live speech, dialogue, or long text, a system that waits feels slow, but one that answers too early can guess from the wrong clue.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** Useful evidence does not always arrive at a steady pace; sometimes it appears early, sometimes late, and the model sees only a moving prefix.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Train the model on many partial views so its own uncertainty and attention become signals for when to keep reading or start writing.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a systems paper on models that answer while input is still arriving (streaming large language models), focused on the gap between fixed read/write schedules and content-aware interaction timing.
      claim_kind:: analyst_assessment
      evidence:: E1, E2
    - **One-Sentence Contribution:** ProactiveLLM improves streaming generation by training partial-input predictions to stay grounded in full-input behavior, so the model's own uncertainty can decide when to answer.
      evidence:: E3, E7
    - **Mental Model:** Picture a careful listener who keeps listening while several answers remain plausible and starts speaking when the right clue makes one answer snap into focus.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest support is that ProactiveLLM improves the quality-latency tradeoff across text and speech tasks, with the largest gains on non-monotonic question answering where fixed schedules fail.
      evidence:: E10, E11, E12
        - Supports C2: Qwen3-4B text streaming; wait-k and alignment-supervised baselines; BLEU/F1 with AIL/RCO; ProactiveLLM beats GPT-5.4-generated alignment data on short QA by 10.62 F1 at low latency and 8.15 F1 at high latency; medium support because repeat counts and variance are not reported.
          evidence:: E10, E11
        - Supports C3: Qwen2-Audio speech streaming; batch and wait-k baselines; WER/F1 with second-level AIL and RCO; Proactive-Entropy reaches 71.12 F1 on Spoken-SQuAD versus batch 72.15 while lowering AIL from 31.02s to 21.26s; medium support because uncertainty is not reported.
          evidence:: E12
        - Supports C4: component ablations; full model versus w/o MSLM and w/o Distill; quality-latency Pareto curves; removing components shifts curves down and right, while the KL coefficient is comparatively insensitive; medium support because figure values are partially summarized.
          evidence:: E13
    - **Main Caveat:** The method still needs threshold calibration: if a partial clue looks sufficient but later evidence overturns it, active writing can fail, and the paper's own case study fixes this by waiting more conservatively.
      claim_kind:: analyst_assessment
      evidence:: E17
- ## Argument Map
    - **Problem and Stakes:** A streaming large language model (streaming LLM) generates output while the input is still arriving, controlled by an interaction scheduler phi(t), the boundary of input visible at output step t. The stake is reducing latency and redundant context processing without losing task quality.
      evidence:: E1, E4
    - **Prior Gap:** Prior streaming methods either hard-code when to read and write, such as wait-k schedules, or learn timing from task-specific annotations, timestamps, segmentation labels, or stronger teachers; this makes timing passive and expensive to adapt.
      evidence:: E2
    - **Key Insight:** The paper's core insight is to train the model's hidden states to expose sufficiency cues first, then attach a lightweight decision policy afterward; this separates streaming capability learning from the particular read/write rule used at inference.
      evidence:: E3, E8
    - **Claims:** The paper's claims are about endogenous timing cues, plug-and-play decision heads, cross-modal transfer, and component necessity.
      evidence:: E3, E10, E12, E13
        - C1: Mask-based streaming training plus synchronized privileged self-distillation can cultivate semantic-sufficiency cues from partial inputs without external timing labels or stronger teachers.
          evidence:: E3, E6, E7
        - C2: Decision heads using model-internal attention or entropy can turn those cues into read/write schedules that improve the quality-latency tradeoff over fixed wait-k baselines and costly alignment-supervised baselines on text tasks.
          evidence:: E8, E10, E11
        - C3: The framework transfers across backbones and modalities, including causal speech-input models, where it keeps near-batch quality with lower latency than batch or fixed schedules.
          evidence:: E5, E9, E12
        - C4: Both Masked Streaming Language Modeling and the batch-side anchor are needed for robust proactive behavior, while the exact KL-divergence coefficient is not the primary source of gains.
          evidence:: E13
- ## Mechanism and Design
    - **Core Mechanism:** Masked Streaming Language Modeling (MSLM) hides future input tokens behind monotonic read boundaries, so each output token learns from a realistic partial prefix. Synchronized Privileged Self-Distillation (SPSD) lets the same evolving model act as a full-context teacher and partial-context student, with small top-k logit alignment rather than a hard match.
      evidence:: E6, E7
    - **Data / Control Flow:** At inference, incoming text or causal speech features are added to separate input/output positions and a Key-Value cache (KV cache, stored attention state reused during decoding); before each output, a decision head chooses Read or Write.
      evidence:: E5, E8
        - Training first samples a monotonic trajectory phi(t), then masks output-to-input attention so output token t can only see input tokens up to phi(t).
          evidence:: E6
        - The batch pass sees the full input and supplies teacher logits, while the streaming pass sees only the partial prefix and learns next-token prediction plus a soft alignment to the batch view.
          evidence:: E7
        - The attention-driven head writes when attention concentrates on specific inputs, and the entropy-driven head writes when next-token uncertainty is low enough.
          evidence:: E8
    - **Design Decisions:** The main design choices all push toward one boundary: the backbone learns many plausible partial-context states, while the final read/write rule stays replaceable.
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E8
        - Need: expose partial-context states without impossible training noise; choice: budgeted polynomial or uniform multinomial allocation of reads; closest alternative: naive random masks; tradeoff: smoother trajectories may underrepresent bursty real streams.
          evidence:: E6, E14
        - Need: stop partial-context anticipation from drifting; choice: same-model full-context teacher; closest alternative: external or frozen teacher; tradeoff: soft top-k KL preserves anticipation but gives no independent teacher signal.
          evidence:: E7
        - Need: adapt timing without retraining the whole model; choice: attention and entropy heads over frozen LLM states; closest alternative: fixed wait-k or learned alignment labels; tradeoff: thresholds must be calibrated for reliability.
          evidence:: E8, E17
    - **Implementation Surface:** The text models use Qwen2.5-3B-Instruct and Qwen3-4B with Group Positional Encoding (GPE, separate input and output position streams) and decoupled attention/KV cache; the speech model uses Qwen2-Audio-7B-Instruct with a causal Whisper encoder. Reported settings include top-100 logit distillation, two training epochs, learning rate 5e-5, four H100 GPUs, and a main decision threshold at the 0.9 quantile.
      evidence:: E5, E18
- ## Evaluation and Evidence
    - **Setup:** The evaluation covers text streams on IWSLT-17 En-De/En-Fr, DialogSum, SQuAD, and MCTest, plus speech streams on LibriSpeech and Spoken-SQuAD. It reports task quality plus read coverage per output token (RCO, average consumed input fraction) and average interaction lag (AIL, delay from an ideal streaming schedule).
      evidence:: E4, E9
    - **Claim-Evidence Matrix:** The evidence mostly supports the paper's relative tradeoff claims, but the absence of repeat counts, variance, and significance tests keeps the experimental support at medium strength.
      claim_kind:: analyst_assessment
      evidence:: E10, E11, E12, E13
        - C1 is mechanistically supported by the MSLM and SPSD objectives, and indirectly supported by ablations, but the paper does not isolate a direct measurement of semantic-sufficiency cues.
          claim_kind:: analyst_assessment
          evidence:: E6, E7, E13
        - C2 is supported by text tables against wait-k and alignment-supervised baselines, especially short QA, where content-dependent timing matters more than fixed latency.
          claim_kind:: analyst_assessment
          evidence:: E10, E11
        - C3 is supported by speech results and backbone coverage; C4 is supported by ablations, though the KL coefficient analysis weakens any claim that explicit KL matching alone drives the gains.
          claim_kind:: analyst_assessment
          evidence:: E12, E13
    - **Headline Results:** The headline pattern is that ProactiveLLM gives the clearest benefit when the task has sparse decisive evidence, while monotonic translation shows smaller but still useful quality-latency improvements.
      evidence:: E10, E11, E12, E16
        - On Qwen3-4B En-Fr, Proactive-Entropy scores 32.24 BLEU with RCO 0.88 versus Wait-9 at 24.33 BLEU and RCO 0.89; on short QA, ProactiveLLM beats the best GPT-5.4 alignment-supervised baseline by 8.15 F1 at high latency.
          evidence:: E10, E11
        - On Spoken-SQuAD, Proactive-Entropy reaches 71.12 F1 with AIL 21.26s and RCO 0.80, close to batch 72.15 F1 while using less context and lower latency.
          evidence:: E12
        - Variable attention FLOPs drop most on Choice QA (34.82%) and Short-form QA (21.67%), moderately on summarization (9.90%), and only slightly on MT En-De (2.27%), matching the claim that benefits depend on information density.
          evidence:: E16
    - **Ablations and Sensitivity:** Ablations indicate that both the streaming objective and the batch-side anchor matter, while lambda, the coefficient on KL divergence, is less sensitive across the reported range.
      evidence:: E13
        - Removing SPSD causes the largest reported collapse in reasoning-heavy short QA, while removing MSLM weakens quality under low-latency constraints.
          evidence:: E13
        - Polynomial allocation reduces high-variance mask trajectories relative to naive random masking, making training states closer to plausible streaming paths.
          evidence:: E14
        - Deploying wait-k on ProactiveLLM performs comparably to wait-k trained from scratch and is better in aggressive low-latency regimes, supporting the plug-and-play framing.
          evidence:: E15
    - **Reproducibility Gaps:** The paper reports backbones, datasets, hardware, major hyperparameters, and decision-threshold policy, but the provided text does not expose a concrete repository URL, seeds, data split details for every task, repeat counts, variance, or full scripts for the alignment-supervised baselines.
      claim_kind:: analyst_assessment
      evidence:: E9, E18
- ## Technical Judgment
    - **What Holds Up:** The strongest part is the separation between representation training and decision policy: MSLM and SPSD make the model useful under partial views, while attention or entropy thresholds can be swapped without rebuilding the backbone. The evidence aligns with this story because gains are largest where semantic sufficiency is sparse and input-dependent.
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E10, E16
    - **Where It May Fail:** The approach can fail when early evidence is plausible but not decisive, as shown by the Spoken-SQuAD Levi's Stadium example; more conservative thresholds mitigate this but give back latency. Benefits also diminish on tasks that truly need nearly every input token, consistent with the small MT FLOP reduction.
      claim_kind:: analyst_assessment
      evidence:: E16, E17
    - **Relation to Other Work:** Compared with wait-k and chunkwise decoding, ProactiveLLM makes timing depend on model state rather than a fixed clock; compared with alignment-supervised policies, it avoids task-specific timing labels. Compared with ordinary distillation, the teacher and student are the same evolving model under different context access, so the method is closer to privileged self-alignment than external teacher transfer.
      claim_kind:: analyst_assessment
      evidence:: E2, E7, E15
    - **Transferable Lesson:** For streaming systems, first train the model to behave under realistic partial observations, then keep the timing controller small, replaceable, and thresholded. This pattern turns latency into a deployment knob instead of baking one timing policy into the model.
      claim_kind:: analyst_assessment
      evidence:: E6, E8, E15
- ## Glossary
  collapsed:: true
    - streaming large language model: A model that can generate output while the input stream is still arriving, rather than waiting for the full input.
    - semantic sufficiency: The point where the visible prefix contains enough meaning for the model to generate a reliable next output.
    - interaction scheduler: The rule or learned policy that decides how much input the model may read before producing each output token.
    - Masked Streaming Language Modeling: The training objective that hides future input tokens behind monotonic boundaries so generation learns from partial prefixes.
    - Synchronized Privileged Self-Distillation: A same-model teacher-student setup where the full-context view guides the partial-context streaming view during training.
    - read coverage per output token: A redundancy metric: the average fraction of the input stream consumed when producing output tokens; lower means less context was read.
    - average interaction lag: A relative latency metric: how delayed write decisions are compared with an ideal uniform streaming alignment.
    - wait-k: A fixed streaming policy that waits for a preset amount of input before writing, then follows a rigid read/write rhythm.
    - entropy-driven decision head: A controller that reads when the next-token distribution is uncertain and writes when the distribution is concentrated.
    - Group Positional Encoding and KV cache: GPE separates source and target position streams; a KV cache stores attention keys and values so new tokens can be processed incrementally.
- ## Evidence Index
  collapsed:: true
    - **E1:** problem/paper_statement | Abstract and Introduction | high
      locator:: Abstract; Sec. 1 Introduction
      quote:: Standard Large Language Models follow a read-then-generate paradigm, causing unnecessary latency and computation. Streaming LLMs alleviate this issue by generating while receiving inputs, but still struggle to decide when to interact with the stream.
    - **E2:** gap/paper_statement | Introduction | high
      locator:: Sec. 1, prior-methods paragraph
      quote:: Existing methodologies remain largely confined within a passive adaptation framework. They either rely on heuristic interaction schedules, such as fixed wait intervals or chunkwise decoding, or learn generation timing from task-specific alignment supervision.
    - **E3:** method/paper_statement | Abstract and Introduction | high
      locator:: Abstract; Sec. 1 contribution paragraph
      quote:: The model first learns to perceive semantic sufficiency from partial inputs through two complementary training mechanisms: mask-based streaming modeling and synchronized privileged self-distillation. Together, these mechanisms induce endogenous sufficiency cues without requiring external teachers or annotations.
    - **E4:** background/paper_statement | Preliminary | high
      locator:: Sec. 2, definition and metrics
      quote:: Given an input stream X and an output stream Y, the model generates tokens sequentially while the input continues to unfold. phi(t) denotes the interaction scheduler, representing the boundary of the input stream accessible to the model at output step t.
    - **E5:** implementation/implementation_detail | Streaming LLM Backbone | high
      locator:: Sec. 3.1 and Appendix B.1
      quote:: Prior research has demonstrated that group positional encoding effectively adapts batch-processed LLMs to streaming scenarios without requiring architectural modifications. Regarding the streaming speech LLM, we utilize a Whisper encoder to project audio features into the textual latent space.
    - **E6:** algorithm/implementation_detail | Proactive Streaming Training Framework | high
      locator:: Sec. 3.2, Masked Streaming Language Modeling
      quote:: During training, we simulate this dynamic availability by applying a randomized causal mask to the future input context. Each unique mask matrix corresponds to a specific interaction decision trajectory phi, effectively transforming a static full-input sample into a simulation of a dynamic streaming process.
    - **E7:** algorithm/implementation_detail | Proactive Streaming Training Framework | high
      locator:: Sec. 3.2, Synchronized Privileged Self-Distillation
      quote:: The streaming mode serves as the partial-context student, while the batch mode serves as the full-context teacher with privileged access to the complete input. Since both views are produced by the current model parameters and optimized jointly during training, the teacher signal is continuously synchronized.
    - **E8:** system_design/implementation_detail | Streaming Active Interaction Decision | high
      locator:: Sec. 3.3
      quote:: The decision head monitors the model's intrinsic states, such as token entropy or attention weights, to guide the interaction decision. High H(P) reflects an information deficit where the predictive mass is dispersed across multiple hypotheses, necessitating a Read.
    - **E9:** experiment_setup/paper_statement | Experimental Settings | high
      locator:: Sec. 4.1
      quote:: For text streaming, we select tasks representing monotonically aligned processes, specifically translation evaluated on IWSLT-17 En-De and En-Fr, as well as non-monotonically aligned processes, including summarization on Dialogue Summarization, short-form QA on SQuAD, and multiple-choice QA on MCTest.
    - **E10:** result/experiment_result | Text-input Results | medium
      locator:: Sec. 4.2, Table 1 and following text
      quote:: In monotonically aligned tasks, fixed-interval methods like wait-k face a rigid trade-off. Breaking this constraint, ProactiveLLM achieves generation quality superior to wait-9 while maintaining lower latency and redundancy than the wait-9 baseline.
    - **E11:** result/experiment_result | Text-input Results | medium
      locator:: Sec. 4.2, Table 2
      quote:: On non-monotonic short-form QA, ProactiveLLM outperforms the best learning-based baseline by 10.62 and 8.15 F1 points at the low- and high-latency levels, respectively, showing more robust decision making without external alignment data.
    - **E12:** result/experiment_result | Speech-input Results | medium
      locator:: Sec. 4.3, Table 3
      quote:: Table 3 suggests that the effectiveness of ProactiveLLM extends to speech streaming tasks. In monotonic ASR, our method appears to alleviate the strict latency-accuracy trade-off found in fixed strategies, achieving performance comparable to high-k baselines but with reduced latency.
    - **E13:** ablation/ablation | Ablation Studies | medium
      locator:: Sec. 4.4, Fig. 4 and Fig. 5
      quote:: The results clearly demonstrate that ProactiveLLM achieves the optimal Pareto frontier across all tasks. As components are systematically removed, the trade-off curves consistently shift towards the bottom-right, indicating a degradation in both latency and quality.
    - **E14:** ablation/profiling | Analysis | medium
      locator:: Sec. 5, Random Mask Analysis and Fig. 6
      quote:: The naive random method exhibits extremely high variance with paths frequently deviating from the ideal diagonal. In contrast, the polynomial allocation maintains smoother, stable trajectories, indicating that the budget-based mechanism successfully mitigates such extreme decision-making.
    - **E15:** result/experiment_result | Analysis | medium
      locator:: Sec. 5, Generalization Analysis and Table 4
      quote:: Table 4 demonstrates that directly deploying Wait-k logic on ProactiveLLM achieves performance fully comparable to a specialized Wait-k model trained from scratch. Notably, ProactiveLLM significantly surpasses the baseline in aggressive low-latency regimes.
    - **E16:** optimization/profiling | Analysis | medium
      locator:: Sec. 5, Redundancy and Latency Analysis and Table 5
      quote:: ProactiveLLM consistently reduces computation across benchmarks, with gains correlating to task-specific information density. Non-monotonic alignment streaming tasks like Multi-choice QA (34.82%) and short-form QA (21.67%) yield the highest savings.
    - **E17:** limitation/case_study | Case Study | medium
      locator:: Appendix E, Table 10
      quote:: Streaming settings reduce interaction latency, but generating from partial information is inherently risky. This limitation arises from the streaming setting itself rather than from a specific model: when the current prefix contains a plausible but incomplete clue, the model may generate prematurely.
    - **E18:** implementation/implementation_detail | Implementation and Hyperparameter Settings | high
      locator:: Appendix B.3, Table 6
      quote:: We summarize the main model, training, and inference hyperparameters in Table 6. These settings are shared across the reported ProactiveLLM experiments unless otherwise specified. Training epochs are 2, hardware is 4 x H100 GPUs, and the decision threshold is swept in [0, 1].
