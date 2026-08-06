- **Title:** AREAL: A Large-Scale Asynchronous Reinforcement Learning System for Language Reasoning
- **Summary:** AREAL shows that large language model reinforcement learning can trade strict freshness for bounded staleness, making generation and training run continuously while preserving reasoning-task accuracy.
- **Paper Type:** system
- **Venue:** NeurIPS 2025; arXiv v5 2026
- **Authors:** Wei Fu, Jiaxuan Gao, Xujie Shen, Chen Zhu, Zhiyu Mei, Chuyi He, Shusheng Xu, Guo Wei, Jun Mei, Jiashu Wang, Tongkai Yang, Binhang Yuan, Yi Wu; IIIS, Tsinghua University; Ant Group; HKUST
- **Keywords:** asynchronous reinforcement learning, large reasoning models, PPO, data staleness, LLM training systems, rollout generation
- ## Orientation
    - **Background:** Modern reasoning models learn by trying answers, receiving a reward, and updating the model. The expensive part is generating long attempts and then using them for training.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** If a training round waits for every attempted answer to finish, one unusually long answer can make many powerful machines sit idle.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** Fresh examples make learning more stable, but waiting for freshness wastes time; using old examples keeps machines busy but can teach from an outdated model.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Let generation and training run separately, then make the learning rule aware of how old each example is.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a systems view of reinforcement learning (RL, training a model from reward feedback) for large reasoning models (LRMs, language models trained to produce long reasoning traces): it exposes how the usual synchronous rollout loop wastes accelerators and how much algorithmic slack is needed to remove that barrier.
      claim_kind:: analyst_assessment
      evidence:: E2, E3
    - **One-Sentence Contribution:** AREAL improves large-scale RL training throughput for LRMs by letting rollout generation and model training run independently while training on samples whose age is explicitly bounded.
      evidence:: E4, E6
    - **Mental Model:** Picture two kitchens sharing orders: one keeps cooking new dishes, the other keeps tasting and updating the recipe, and a freshness rule decides when an old dish is still useful for improving the recipe.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is the combination of end-to-end time reduction, scaling behavior, and staleness ablations showing that the system gain is not only a faster implementation trick.
      claim_kind:: analyst_assessment
      evidence:: E11, E12, E13
        - Supports C1: math and coding RL runs on 16 to 48 H800 nodes; synchronous AREAL and verl-style baselines; training hours; up to 2.77x reduction with comparable final accuracy; supported, but single-trial.
          evidence:: E10, E11, E18
        - Supports C2: 1.5B math ablations across maximum staleness values; naive PPO and decoupled PPO; benchmark score and throughput; moderate staleness keeps near-oracle scores while throughput exceeds 2x; supported, but no error bars.
          evidence:: E13, E14, E18
        - Supports C3: scaling tests across model sizes, device counts, and context lengths; verl as synchronous baseline; effective training throughput; AREAL usually scales better and reaches up to 2.5x throughput speedup; supported, but benchmark surface is narrow.
          evidence:: E12, E19
        - Supports C4: system ablations on dynamic microbatch allocation and interruptible generation; normal batching and non-interruptible generation as baselines; throughput; about 30 percent training gain plus 12 to 17 percent generation gain; supported, but isolated from full-run variance.
          evidence:: E15, E18
    - **Main Caveat:** The evidence is strongest for single-turn math and code reasoning on large internal H800 clusters; the paper reports no error bars, uses fixed seeds, and leaves device partitioning and multi-turn agent settings open.
      claim_kind:: analyst_assessment
      evidence:: E10, E18, E19
- ## Argument Map
    - **Problem and Stakes:** Large reasoning model (LRM) RL needs many long rollouts, meaning generated answer traces used as training data, but synchronous systems wait for each generation batch before training. That waiting makes accelerator utilization and scaling the central systems bottleneck rather than only the learning algorithm.
      evidence:: E2, E3
    - **Prior Gap:** Prior synchronous frameworks preserve on-policy data, where examples come from the latest model, while overlap systems relax freshness by only a step or two but still keep batched generation. The unfilled gap is a system that streams generation continuously while giving the optimizer a principled way to use mixed-version data.
      evidence:: E3, E4
    - **Key Insight:** The paper's key insight is to treat data age as a controllable systems variable and to pair that control with decoupled Proximal Policy Optimization (PPO, an RL update rule that clips overly large policy changes around a reference policy). This changes strict freshness from a hard synchronization barrier into a tunable learning-system tradeoff.
      evidence:: E6, E7
    - **Claims:** The paper's claims separate system throughput, algorithmic stability under stale data, scaling, and individual implementation optimizations.
      claim_kind:: analyst_assessment
        - C1: Fully asynchronous generation and training reduces end-to-end RL training time for LRMs while matching or improving final math and coding benchmark accuracy.
          evidence:: E10, E11
        - C2: Bounded data staleness combined with decoupled PPO makes stale and interrupted rollouts usable, whereas naive PPO degrades as staleness increases.
          evidence:: E6, E7, E13
        - C3: AREAL scales more effectively than a synchronous verl-style RL system across larger device counts, model sizes, and longer context lengths.
          evidence:: E12
        - C4: Dynamic microbatch allocation and interruptible generation are measurable contributors to throughput beyond the high-level asynchronous architecture.
          evidence:: E9, E15
- ## Mechanism and Design
    - **Core Mechanism:** AREAL separates rollout workers that generate text from trainer workers that update model parameters, using a controller, reward service, replay buffer, and parameter updates to keep both sides active. Because batches may mix policy versions, it adds a staleness limit and a decoupled PPO objective that clips around a recent proximal policy rather than the old behavior policy that produced each sample.
      evidence:: E5, E6, E7
    - **Data / Control Flow:** The controller reads prompts, dispatches generation, sends responses to a reward service, places rewarded trajectories in a replay buffer, and triggers weight updates after trainers publish new parameters. Interruptible rollout workers can stop in-flight generation, reload parameters, discard old key-value attention state (KV cache, saved attention computations used to continue decoding efficiently), recompute needed state, and continue unfinished requests.
      evidence:: E5, E8
        - Generation is streaming rather than batch-barriered: rollout workers keep accepting generate requests and only pause when an update_weights request interrupts them.
          evidence:: E4, E5
        - Training workers sample once-used data from the replay buffer until the configured batch size is reached, run PPO updates, and write new model parameters to distributed storage.
          evidence:: E5
        - Reward evaluation is separated from GPU generation and training; math can use string matching and coding can execute unit tests before trajectories enter the buffer.
          evidence:: E5, E9
    - **Design Decisions:** The design choices are mostly small relaxations of strict synchronous RL: permit bounded age, make the optimizer know which policy produced the sample, and reduce the wasted work caused by long or uneven sequences. Each choice trades exact freshness or simple batching for higher utilization.
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E15
        - Need: avoid unbounded off-policy data, meaning samples from older policies; choice: reject new generation requests that would exceed maximum staleness eta; alternative: eta = 0 synchronous training; tradeoff: small eta can throttle generation when responses are long.
          evidence:: E6, E13
        - Need: train on samples produced by older or interrupted policies; choice: use behavior policy probabilities for importance weighting but clip updates around a recent proximal policy; alternative: standard PPO centered on the behavior policy; tradeoff: extra token-probability recomputation at batch arrival.
          evidence:: E7, E8
        - Need: variable sequence lengths waste memory and make long requests block progress; choice: padding-free dynamic microbatch allocation plus interruptible generation; alternative: fixed microbatches and non-interruptible generation; tradeoff: more runtime control complexity and KV-cache recomputation after updates.
          evidence:: E5, E9, E15
    - **Implementation Surface:** The implementation is a Python/PyTorch system built on ReaLHF, SGLang for serving, Megatron-Core for training, and SLURM (a cluster job scheduler) for resource scheduling. It overlaps CPU reward computation and network transfer with GPU generation, uses asyncio to avoid blocking among rollout requests, and packs variable-length sequences under memory constraints.
      evidence:: E9, E17
- ## Evaluation and Evidence
    - **Setup:** The main experiments train DeepSeek-R1-distilled Qwen2-family models from 1.5B to 32B parameters on math and code RL tasks, then evaluate on AIME24 and LiveCodeBench with additional appendix benchmarks. Hardware is an H800 cluster with up to 64 nodes, and AREAL usually allocates three quarters of devices to inference based on early experiments.
      evidence:: E10, E17
    - **Claim-Evidence Matrix:** The evidence is organized by claim: full-run comparisons support C1, staleness and objective ablations support C2, scaling curves support C3, and isolated system ablations support C4.
      claim_kind:: analyst_assessment
      evidence:: E11, E12, E13, E15
        - C1 is supported by Table 1, where AREAL cuts hours versus synchronous baselines while final AIME24 and LiveCodeBench scores stay close or improve.
          evidence:: E11
        - C2 is supported by Figure 5 and Table 2, where decoupled PPO tolerates moderate eta values and naive PPO collapses in important settings such as eta = 4.
          evidence:: E13, E14
        - C3 and C4 are supported separately: Figure 4 shows stronger scaling than verl, while Figure 6 shows dynamic batching and interruptibility each add throughput.
          evidence:: E12, E15
    - **Headline Results:** The headline result is a large wall-clock reduction at comparable final quality: 1.5B math training goes from 41.0 hours under synchronous AREAL to 14.8 under AREAL, and 14B coding goes from 48.8 to 21.9 hours versus synchronous AREAL. Compared with external verl-derived baselines, the paper also reports up to 2.77x lower training hours and up to 2.5x throughput speedup in scaling experiments.
      evidence:: E11, E12
        - On 1.5B and 7B math, AREAL matches synchronous AREAL AIME24 scores within 0.2 points while cutting reported hours from 41.0 to 14.8 and from 57.7 to 25.4.
          evidence:: E11
        - On 14B and 32B coding, AREAL reports LiveCodeBench scores of 58.1 and 61.0 while reducing synchronous AREAL hours from 48.8 to 21.9 and from 51.1 to 31.1.
          evidence:: E11
    - **Ablations and Sensitivity:** The most important sensitivity is staleness: moderate eta improves throughput sharply, but unbounded staleness degrades accuracy even with decoupled PPO. System ablations show dynamic allocation and interruptible generation both matter, so the speedup is a compound effect rather than a single optimization.
      evidence:: E13, E14, E15
        - Eta = 4 is the clearest tradeoff point in the main math ablation: throughput rises to 356.6k tokens/s while decoupled PPO keeps AIME24 at 42.2, close to the eta = 0 oracle of 42.0.
          evidence:: E14
        - Unbounded staleness is not safe: the paper reports inferior final performance even with the decoupled objective, which makes eta a required control rather than a cosmetic knob.
          evidence:: E13
        - Dynamic microbatch allocation improves training throughput most for larger models in Figure 6a, while interruptible generation improves rollout throughput for both 1.5B and 7B models.
          evidence:: E15
    - **Reproducibility Gaps:** The paper provides a public code URL, open-source datasets and base models, fixed seed, and detailed hyperparameters, but the main large-scale claims still depend on an H800 cluster and single-trial results without error bars. Not reported: scripts for every table from a clean checkout, variance across seeds, and sensitivity to inference/training partition beyond the selected heuristic.
      claim_kind:: analyst_assessment
      evidence:: E10, E17, E18, E19
- ## Technical Judgment
    - **What Holds Up:** The strongest part is the algorithm-system link: the paper does not merely overlap generation and training, but names the resulting data-age problem and tests the optimizer change needed to tolerate it. The proof that interrupted generation can be viewed as one behavior policy also gives a clean accounting story for mixed-version trajectories, even though it does not by itself prove good learning performance.
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E8, E13
    - **Where It May Fail:** Benefits should diminish when generation is short, training is the bottleneck, or the chosen inference/training split is wrong for the run; the paper itself notes shorter-context imbalance and leaves dynamic partitioning open. Trust also weakens outside single-turn math/code tasks and for claims requiring statistical robustness, because large-scale experiments are single-trial without error bars.
      claim_kind:: analyst_assessment
      evidence:: E12, E18, E19
    - **Relation to Other Work:** Compared with synchronous reinforcement learning from human feedback (RLHF) and RL systems such as verl-style pipelines, AREAL moves the key boundary from phase alternation to a streaming producer-consumer loop. Compared with limited-overlap or short-context asynchronous RLHF, its distinguishing technical dimension is allowing mixed-version batches and interrupted trajectories while using staleness control and decoupled PPO to keep the update meaningful.
      claim_kind:: analyst_assessment
      evidence:: E3, E7, E12
    - **Transferable Lesson:** A useful systems pattern is to turn an expensive correctness invariant into a measured budget: here, exact on-policy freshness becomes bounded staleness, and the learning rule is changed to spend that budget safely. The transferable warning is that systems slack only works when the algorithm consumes the slack explicitly rather than pretending the data are still fresh.
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E13, E14
- ## Glossary
  collapsed:: true
    - reinforcement learning: Training from reward feedback rather than fixed target answers; in this paper the reward is correctness at the final generated answer.
    - large reasoning model: A large language model trained or prompted to produce long reasoning traces before the final answer.
    - rollout: One generated answer trace used as RL training data, including tokens and reward.
    - Proximal Policy Optimization: An RL update that limits policy movement by clipping the probability ratio around a reference policy.
    - reinforcement learning from human feedback: A family of language-model RL methods that use human preference or feedback signals; AREAL compares against related systems in this broader category.
    - data staleness: How many training versions old a sample may be; AREAL controls it with a request-rate rule and older-first buffer use.
    - behavior policy: The policy distribution that actually generated a token or trajectory, possibly assembled from multiple interrupted model versions.
    - proximal policy: The recent policy used as the trust-region center for decoupled PPO instead of the older behavior policy.
    - key-value attention cache: Saved transformer attention state that makes continued decoding faster; AREAL discards and recomputes it when weights change during interrupted generation.
    - dynamic microbatch allocation: A sequence-packing method that groups variable-length training examples under a token budget to reduce padding and avoid memory overflows.
    - replay buffer: Temporary storage for rewarded trajectories before training; AREAL uses each item once and prioritizes older trajectories.
    - Simple Linux Utility for Resource Management: A cluster job scheduler used by the AREAL implementation for resource management.
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/metadata | Title and author block | high
      locator:: title page
      quote:: The title page identifies AREAL as a large-scale asynchronous reinforcement learning system for language reasoning, lists authors from Tsinghua University, Ant Group, and HKUST, and marks the paper as NeurIPS 2025 with arXiv version 5 in March 2026.
    - **E2:** problem/paper_statement | Abstract and Introduction | high
      locator:: Abstract; Section 1
      quote:: The paper says existing large-scale RL systems for LLMs are mostly synchronous, alternating generation and training. Generation waits for the longest output in a batch, which underutilizes GPUs when reasoning outputs have highly variable lengths.
    - **E3:** gap/paper_statement | Related Work and Motivation | high
      locator:: Section 2; Section 3.2
      quote:: The paper positions prior overlap systems as using outputs from one or two older model versions but still in batched generation, while synchronous systems distribute generation across all devices and can become memory-IO-bound at small per-GPU decode batches.
    - **E4:** insight/paper_statement | Introduction | high
      locator:: Section 1
      quote:: AREAL is described as fully asynchronous: rollout workers continuously generate without waiting, trainers update whenever enough data is collected, and each batch can contain samples produced by different model versions.
    - **E5:** system_design/implementation_detail | System Overview | high
      locator:: Section 4.1; Figure 2 and Figure 3
      quote:: The architecture contains interruptible rollout workers, a reward service, trainer workers, and a rollout controller. The controller sends prompts, obtains rewards, stores trajectories in a replay buffer, and updates rollout workers after trainers publish new parameters.
    - **E6:** algorithm/implementation_detail | Staleness-Aware Training | high
      locator:: Section 5.1
      quote:: The system introduces a maximum permitted staleness eta. The rollout controller tracks generated samples and policy version, rejects requests that could violate the constraint, and prioritizes older trajectories when forming training batches.
    - **E7:** algorithm/paper_statement | Decoupled PPO Objective | high
      locator:: Section 5.2
      quote:: The objective separates behavior policy from proximal policy. The paper argues that using a recent proximal policy prevents updates from being pulled toward old, lower-quality behavior policies, and recomputes token probabilities when the global batch arrives.
    - **E8:** other/proof | Decoupled PPO Objective and Proof | high
      locator:: Section 5.2; Appendix D
      quote:: Proposition 1 states that a sequence generated by multiple policy versions during interrupted generation has an equivalent single behavior policy. Appendix D constructs that behavior policy over the states encountered by the generated sequence.
    - **E9:** implementation/implementation_detail | Implementation | high
      locator:: Section 6; Appendix B
      quote:: AREAL is implemented in Python and PyTorch on ReaLHF, using SGLang v0.4.6 for generation, Megatron-Core v0.11.0 for training, SLURM, a cluster job scheduler, asyncio for rollout concurrency, and padding-free sequence packing with dynamic allocation.
    - **E10:** experiment_setup/paper_statement | Experiment Setup | high
      locator:: Section 7.1
      quote:: The evaluation covers math and coding tasks with distilled Qwen2 models from DeepSeek-R1 from 1.5B to 32B parameters, AIME24 and LiveCodeBench-style evaluation, fixed PPO steps, and an H800 cluster with 64 nodes and 8 GPUs per node.
    - **E11:** result/experiment_result | End-to-End Comparison | medium
      locator:: Section 7.2; Table 1
      quote:: Table 1 reports comparable or better final accuracy while reducing training hours: for example, 1.5B math synchronous AREAL takes 41.0 hours versus 14.8 for AREAL, and 14B coding verl takes 44.4 hours versus 21.9.
    - **E12:** result/experiment_result | Scalability | medium
      locator:: Section 7.3; Figure 4
      quote:: The scalability study compares AREAL with verl over model sizes and context lengths. The paper reports approximate linear scaling for AREAL, weaker scaling for the synchronous system, and at most 2.5x effective throughput speedup.
    - **E13:** ablation/ablation | Algorithm Ablations | medium
      locator:: Section 7.4; Figure 5; Table 2
      quote:: The ablation varies maximum staleness eta with and without the decoupled PPO objective. The paper says naive PPO degrades with staleness, while decoupled PPO with moderate staleness keeps final performance near the zero-staleness oracle and improves throughput.
    - **E14:** result/ablation | Algorithm Ablations | medium
      locator:: Table 2; Figure 5c
      quote:: At eta = 4, Table 2 reports AIME24 42.2 with decoupled PPO versus 23.3 without it, while Figure 5c shows effective throughput rising from 128.7k tokens/s at eta = 0 to 356.6k at eta = 4.
    - **E15:** ablation/ablation | System Ablations | medium
      locator:: Section 7.5; Figure 6
      quote:: Dynamic microbatch allocation improves PPO throughput by about 30 percent across model sizes. Interruptible generation increases generation throughput by 12 percent for 1.5B and 17 percent for 7B models on four nodes.
    - **E16:** result/experiment_result | Additional Results | medium
      locator:: Appendix C.1 to C.4; Tables 4 to 8
      quote:: The appendices add math and coding benchmark tables, a Llama-8B architecture test, small 8-GPU staleness-throughput experiments, and RLOO experiments, which the paper uses to argue that the conclusions extend beyond the main Qwen runs.
    - **E17:** experiment_setup/paper_statement | Reproducibility and Implementation Details | high
      locator:: Appendix A; Appendix B
      quote:: The paper states that AREAL code is available on GitHub, datasets and base models are from open-source sources, fixed random seed 1 is used, and Appendix B gives PPO, optimizer, precision, generation, dataset, batching, and baseline details.
    - **E18:** limitation/limitation | NeurIPS Checklist | high
      locator:: Checklist item 7
      quote:: For statistical significance, the authors answer No, explaining that large-scale end-to-end experiments are expensive, results are from a single trial, and the same fixed random seed is used across settings.
    - **E19:** limitation/limitation | Limitations and Future Work | high
      locator:: Appendix E
      quote:: The limitations note says the inference-to-training device ratio could be optimized or dynamically adjusted, and that evaluation focuses on single-step mathematical and coding tasks while multi-turn interactions and agentic scenarios remain future work.
