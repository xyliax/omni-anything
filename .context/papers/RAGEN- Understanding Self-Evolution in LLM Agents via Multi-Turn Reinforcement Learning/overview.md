- **Title:** RAGEN: Understanding Self-Evolution in LLM Agents via Multi-Turn Reinforcement Learning
- **Summary:** RAGEN uses a trajectory-level reinforcement-learning framework to show that LLM agents can improve through interaction, but multi-turn self-training is fragile unless rollout selection, gradient shaping, and reasoning-aware rewards are handled carefully.
- **Paper Type:** system
- **Venue:** arXiv preprint 2025
- **Authors:** Zihan Wang, Kangrui Wang, Qineng Wang, Pingyue Zhang, Linjie Li, Zhengyuan Yang, Xing Jin, Kefan Yu, Minh Nhat Nguyen, Licheng Liu, Eli Gottlieb, Yiping Lu, Kyunghyun Cho, Jiajun Wu, Li Fei-Fei, Lijuan Wang, Yejin Choi, Manling Li; Northwestern University, University of Washington, Stanford University, Microsoft, New York University, University of British Columbia, Singapore Management University
- **Keywords:** LLM agents, multi-turn reinforcement learning, trajectory-level optimization, training stability, reasoning degradation
- ## Orientation
    - **Background:** This paper sits in reinforcement learning for language-model agents. Reinforcement learning means training by rewards from attempts; an agent is a model that acts in an environment, observes what happened, then chooses the next action.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A chat model can answer a one-shot question, but an agent must keep playing after each move and learn from its own successes and mistakes without being handed the correct path.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** The same final score can come from a good plan, a lucky accident, or a repeated shortcut, so feedback can reward behavior that looks useful but does not build robust reasoning.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Train and diagnose the whole interaction episode, then ask which rollout choices and reward signals keep learning diverse, stable, and genuinely reasoning-like.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as an agent-training study that asks why rule-based reinforcement learning, which can improve static reasoning tasks, becomes unstable when a language model must act, observe feedback, and continue acting over several turns.
      evidence:: E1, E4
    - **One-Sentence Contribution:** RAGEN improves the study of self-evolving LLM agents by treating each whole interaction episode as the learning object, so training signals can be analyzed across action, feedback, collapse, and reasoning behavior.
      evidence:: E2, E3
    - **Mental Model:** Picture a student repeatedly playing small games: the paper watches not only whether the student wins, but whether their habits become narrower, noisier, or more thoughtful after each round of practice.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is the cross-environment training trace: vanilla trajectory-level RL improves early, then often collapses, while selective and shaped variants delay or reduce collapse.
      evidence:: E6, E9
        - Supports C1: baseline StarPO on Bandit, Sokoban, Frozen Lake, and WebShop; PPO/GRPO single-turn-style adaptations; success and stability metrics; symbolic tasks collapse after early gains; partially supported because repeat counts and uncertainty bands are not reported.
          evidence:: E4, E6
        - Supports C2: StarPO-S uncertainty filtering on PPO/GRPO; all-rollouts and keep-rate baselines; success-rate stability; filtering low-variance prompts delays or avoids collapse; partially supported because default keep rate is acknowledged as task-dependent.
          evidence:: E7, E9
        - Supports C3: rollout-quality sweeps over prompt diversity, actions per turn, and Online-k reuse; fixed-budget comparisons; generalization success; moderate action budgets and fresher rollouts perform better; partially supported because the sweeps are mainly stylized environments.
          evidence:: E11, E12
        - Supports C4: reasoning/no-thinking comparison on Bandit and Sokoban plus reasoning-length tracking; task success and think-block length; reasoning helps Bandit generalization but shrinks in multi-turn tasks; partially supported because reasoning quality is judged with sparse outcome rewards and cases.
          evidence:: E13, E14
    - **Main Caveat:** The conclusions are strongest as controlled diagnostics, not as proof that the proposed recipe will scale to realistic agents: most evidence comes from small models, stylized tasks, sparse rewards, and limited reporting of variance or repeat structure.
      claim_kind:: analyst_assessment
- ## Argument Map
    - **Problem and Stakes:** The paper targets self-evolving LLM agents: language models trained by reinforcement learning (RL), meaning reward-driven trial-and-error, while interacting over multiple turns with stochastic environment feedback. The stakes are practical because planning assistants, tutoring agents, robotics-style agents, and web agents need policies that improve from experience rather than only from static prompt-response data.
      evidence:: E1, E4
    - **Prior Gap:** Prior RL-for-LLM work largely optimizes one response for one prompt, while this paper argues that interactive agents require a Markov Decision Process (MDP), a formal loop where state, action, transition, and reward unfold across time. The gap is not just more turns, but the training dynamics created when the model learns from self-generated trajectories.
      evidence:: E1, E3
    - **Key Insight:** The key insight is that multi-turn agent RL must be studied at the trajectory level: a trajectory is the complete record of states, reasoning text, executable actions, rewards, and future observations. Once training material is the whole trajectory, collapse signals, rollout freshness, reward variability, and reasoning quality become first-class design variables rather than side effects.
      evidence:: E2, E3, E8
    - **Claims:** The paper's main claims are empirical and diagnostic rather than a single benchmark win.
      evidence:: E6, E9, E11, E13
        - C1: Single-turn policy-optimization recipes such as Proximal Policy Optimization (PPO), which clips policy updates using a learned value estimate, and Group Relative Policy Optimization (GRPO), which normalizes rewards within a group without a critic, do not transfer cleanly to multi-turn agent RL because they often produce early gains followed by collapse.
          evidence:: E6, E8
        - C2: StarPO-S stabilizes trajectory-level RL by filtering low-information prompts and shaping gradients, especially when repeated rollouts from the same prompt show low reward variability.
          evidence:: E9, E10
        - C3: Rollout quality depends on task diversity, action budget, and freshness: agents generalize better when rollouts cover varied initial states, allow enough but not excessive actions, and are regenerated frequently under the current policy.
          evidence:: E11, E12
        - C4: Reasoning traces can help in simple single-turn symbolic tasks, but in multi-turn tasks they fade or become spurious when rewards only score final outcomes rather than intermediate reasoning quality.
          evidence:: E13, E14
- ## Mechanism and Design
    - **Core Mechanism:** State-Thinking-Actions-Reward Policy Optimization (StarPO) optimizes the expected cumulative reward of a whole trajectory $\tau$, where $\tau$ contains the observed states, the model's reasoning-formatted action text, environment rewards, and later states. The mechanism is compatible with autoregressive LLMs because the trajectory probability is decomposed into token-level likelihoods, then optimized with PPO or GRPO-style objectives.
      evidence:: E3
        - The learning target changes from a single prompt-response reward $R(s,a)$, where $s$ is the prompt state and $a$ is one output, to a trajectory reward $R(\tau)$, where $\tau$ is the full interaction history.
          evidence:: E3
        - Each action is generated as reasoning plus an executable answer, so the model's hidden plan-like text and the environment action are both present in the training trajectory.
          evidence:: E3
    - **Data / Control Flow:** RAGEN runs a loop: sample initial states, generate several rollouts per state, execute model actions in the environment, assign trajectory rewards, then update the model on the resulting token sequences. The paper's main setting uses Qwen2.5-Instruct 0.5B for symbolic tasks and a 3B model for WebShop, with fixed validation prompts and metrics for success, entropy, reward variability, response length, and gradient norm.
      evidence:: E4, E5
        - Rollout generation may be on-policy, meaning sampled from the current model, or reused from an older policy through a replay-buffer-like source, although the paper later lists missing established replay-buffer practices as a limitation.
          evidence:: E3, E15
        - The evaluation surface deliberately mixes Bandit, Sokoban, Frozen Lake, and WebShop so the same training loop is exposed to risk-sensitive choice, irreversible planning, stochastic transitions, and language-grounded web interaction.
          evidence:: E4
    - **Design Decisions:** The most important design decision is to keep the framework modular: StarPO supplies the trajectory abstraction, while RAGEN supplies environments, rewards, rollout strategies, and optimization variants for diagnosis. StarPO-S then adds selective training data and less restrictive gradients because collapse is treated as a sampling-and-update problem, not only as a model-capacity problem.
      evidence:: E2, E9, E10
        - Need: avoid training on trivially solved or uniformly failed prompts; design choice: keep prompts with high reward standard deviation across repeated rollouts; tradeoff: the aggressive keep rate is not universally optimal.
          evidence:: E9
        - Need: prevent useful updates from being overconstrained; design choice: remove the Kullback-Leibler (KL) penalty, a term that keeps the new policy close to a reference policy, and use asymmetric clipping to allow stronger positive updates; tradeoff: looser constraints may increase drift outside tested settings.
          evidence:: E10
        - Need: keep optimization targets aligned with current behavior; design choice: use diverse prompts, multiple responses per prompt, moderate per-turn action budgets, and frequent rollout refresh; tradeoff: fresher rollouts cost more environment interaction.
          evidence:: E11, E12
    - **Implementation Surface:** The implementation surface is a research system rather than only a formula: RAGEN integrates structured prompts, environment execution, reward functions, multi-turn rollouts, PPO/GRPO updates, and diagnostic metrics. The paper also reports code and environment availability, but the note should treat exact reproducibility as partial because the paper does not provide a full statistical protocol for all headline results.
      evidence:: E2, E5, E15
- ## Evaluation and Evidence
    - **Setup:** The main experiments train small Qwen2.5-Instruct models on four environments and evaluate on fixed validation prompts with success rate plus diagnostics for exploration and update stability. This setup is well chosen for causal diagnosis of training dynamics, but it is not a broad agent benchmark suite.
      evidence:: E4, E5
        - Metrics include task success, token-level rollout entropy, in-group reward variance or standard deviation across repeated rollouts, response length, and gradient norm.
          evidence:: E5, E8
    - **Claim-Evidence Matrix:** The evidence is strongest when the paper links a claim to a controlled curve or ablation; it is weaker when the claim depends on qualitative reasoning traces or unstated variance across seeds.
      claim_kind:: analyst_assessment
        - C1 is supported by baseline PPO/GRPO curves and collapse diagnostics across tasks, with medium confidence because the paper emphasizes trajectories and figures more than statistical uncertainty.
          evidence:: E6, E8
        - C2 is supported by uncertainty-filtering and gradient-shaping ablations, with medium confidence because the best filtering threshold is task-dependent and not derived from a general rule.
          evidence:: E9, E10
        - C3 and C4 are supported by rollout-factor sweeps and reasoning/no-thinking comparisons, with medium confidence because they measure important proxies but do not fully isolate reasoning quality from action success.
          evidence:: E11, E12, E13, E14
    - **Headline Results:** The headline result is not that StarPO-S wins every environment, but that vanilla multi-turn RL has repeatable collapse signatures and that simple stabilizers can delay or reduce them. The most concrete result is uncertainty filtering in Frozen Lake PPO, where retaining 75% of rollouts extends stability from 100 to 140 steps and retaining 50% avoids collapse in the reported run.
      evidence:: E6, E9
        - A useful negative result is that supervised fine-tuning (SFT), direct training on ground-truth trajectories, beats StarPO-S on Sokoban in Appendix G, which bounds the current self-evolution claim.
          evidence:: E16
    - **Ablations and Sensitivity:** The paper ablates the parts most likely to affect trajectory learning: uncertainty filtering, KL removal, asymmetric clipping, prompt diversity, actions per turn, rollout reuse, reasoning tags, and scaling. The sensitivity story is coherent: learning improves when trajectories are informative and current, but degrades when rewards are sparse, stale, or easy to satisfy with shortcuts.
      evidence:: E9, E10, E11, E12, E14
    - **Reproducibility Gaps:** Code and environments are reported as available, and the paper gives model families, hardware class, update counts, rollout counts, and major hyperparameters. Not reported: a complete seed protocol, error bars for most curves, exact repeat counts for each ablation, and a full accounting of how environment-specific reward implementations affect reasoning traces.
      claim_kind:: analyst_assessment
- ## Technical Judgment
    - **What Holds Up:** The paper's best contribution is the diagnostic framing: collapse is shown through reward variability, entropy, gradient norm, and qualitative trajectory changes rather than only final success. The trajectory-level abstraction is also well matched to LLM agents because it includes reasoning text, executable actions, and environment feedback in the same optimization object.
      claim_kind:: analyst_assessment
      evidence:: E3, E7, E8
    - **Where It May Fail:** StarPO-S may fail when reward variability is not a good proxy for useful learning, such as environments with naturally high outcome variance, deceptive rewards, or tasks where successful reasoning is rare but low-variance. The paper itself notes small-scale tasks, missing replay-buffer practices, and no multimodal tasks, so the recipe should not be assumed to transfer unchanged to richer agents.
      claim_kind:: analyst_assessment
      evidence:: E9, E15
    - **Relation to Other Work:** Compared with PPO and GRPO for static LLM reasoning, this work moves the unit of optimization from one answer to a full interaction trajectory. Compared with agent frameworks such as ReAct-style reason-and-act prompting, it studies training dynamics under environment rewards; compared with supervised fine-tuning on trajectories, it is weaker in reported Sokoban performance but more focused on self-generated learning.
      claim_kind:: analyst_assessment
      evidence:: E3, E6, E16
    - **Transferable Lesson:** For self-training agents, the training data generator is part of the algorithm: what states are sampled, how often rollouts are refreshed, which uncertain cases are kept, and whether rewards distinguish reasoning quality can matter as much as the policy optimizer. A reusable pattern is to instrument diversity and update stability before scaling the model or adding a larger reward model.
      claim_kind:: analyst_assessment
      evidence:: E8, E11, E12, E14
- ## Glossary
  collapsed:: true
    - reinforcement learning: Training by letting a policy try actions and updating it from reward signals; in this paper, rewards mostly come from task outcomes.
    - LLM agent: A language model used as an actor in an environment: it observes state text, emits actions, receives feedback, and continues over turns.
    - Markov Decision Process: A formal interaction loop with states, actions, transition dynamics, and rewards; useful here because agent behavior unfolds over time.
    - trajectory: The full episode record: initial state, model outputs, rewards, later states, and final outcome. StarPO treats this as the learning unit.
    - State-Thinking-Actions-Reward Policy Optimization: The paper's trajectory-level RL framework for optimizing multi-turn LLM-agent interactions.
    - StarPO-S: A stabilized StarPO variant using uncertainty-based filtering, critic or baseline choices, and gradient-shaping techniques.
    - Echo Trap: The paper's name for collapse where self-generated RL training reinforces repetitive reasoning templates and reduces behavioral diversity.
    - Group Relative Policy Optimization: A critic-free policy optimization method that normalizes a trajectory's reward against rewards from the same sampled group.
    - Proximal Policy Optimization: A policy-gradient method that clips update ratios and often uses a learned critic to estimate advantages.
    - rollout: One sampled episode or batch of episodes generated by running the current or older policy in an environment.
    - uncertainty-based filtering: Keeping prompts whose repeated rollouts have high reward variability, on the assumption that they provide more informative learning signals.
    - think-answer format: A structured output format where the model emits reasoning text inside a think block and executable actions inside an answer block.
- ## Evidence Index
  collapsed:: true
    - **E1:** problem/paper_statement | Abstract | high
      locator:: abstract
      quote:: Training large language models (LLMs) as interactive agents presents unique challenges including long-horizon decision making and interacting with stochastic environment feedback. While reinforcement learning (RL) has enabled progress in static tasks, multi-turn agent RL training remains underexplored.
    - **E2:** method/paper_statement | Abstract | high
      locator:: abstract
      quote:: We propose StarPO (State-Thinking-Actions-Reward Policy Optimization), a general framework for trajectory-level agent RL, and introduce RAGEN, a modular system for training and evaluating LLM agents.
    - **E3:** algorithm/paper_statement | 2.2 StarPO | high
      locator:: section 2.2 and Figure 2
      quote:: StarPO treats the entire trajectory—including observations, reasoning traces, actions, and feedback—as a coherent unit for rollout and model optimization. The objective is to maximize expected trajectory reward.
    - **E4:** experiment_setup/paper_statement | 3. Experiment Setup | high
      locator:: sections 3.1-3.3
      quote:: We evaluate LLM agents on four environments spanning symbolic and realistic decision-making: Bandit tests risk-sensitive reasoning under noisy feedback; Sokoban requires irreversible symbolic planning; Frozen Lake combines planning with probabilistic transitions; and WebShop involves natural language grounding and web environment interaction.
    - **E5:** experiment_setup/paper_statement | 3. Experiment Setup | high
      locator:: section 3.2
      quote:: In our main experiments, we train Qwen-2.5 Instruct 0.5B models for three symbolic tasks and its 3B variant for the challenging WebShop. We also report various model performance in Appendix D.
    - **E6:** result/experiment_result | 4.1 Multi-turn Agent RL Training Introduces New Instability Pattern | medium
      locator:: section 4.1, Figures 3-4
      quote:: Vanilla adaptations from single-turn methods like PPO and GRPO achieve early gains in agent settings but often collapse. A critic in PPO may delay instability, but would not prevent reasoning degradation, highlighting the need for specialized stabilization in agent settings.
    - **E7:** result/case_study | 4.1 Multi-turn Agent RL Training Introduces New Instability Pattern | medium
      locator:: Finding 2 and Figure 4
      quote:: We find that early-stage agent respond with diverse symbolic reasoning, but collapse into deterministic, repetitive templates after training. Models converge to fixed phrasing, indicating that RL may reinforce superficial patterns instead of general reasoning and forms an "Echo Trap".
    - **E8:** result/experiment_result | 4.1 Multi-turn Agent RL Training Introduces New Instability Pattern | medium
      locator:: Finding 3 and Figure 4
      quote:: Reward standard deviation and entropy often fluctuate before performance degrades, while gradient norm spikes typically mark the point of irreversible collapse. These metrics provide early indicators and motivate the need for stabilization strategies.
    - **E9:** ablation/ablation | 4.2 StarPO-S | medium
      locator:: section 4.2 and Figure 5
      quote:: In PPO runs (Figure 5, left), filtering low-variability rollouts significantly delays collapse: retaining 75% of rollouts extends stability in FrozenLake from 100 to 140 steps, while 50% avoids collapse entirely.
    - **E10:** optimization/ablation | 4.2 StarPO-S | medium
      locator:: section 4.2 and Appendix D
      quote:: In addition to uncertainty-based filtering, we adopt two gradient shaping techniques inspired by DAPO designed for single-turn RL: KL Term Removal and Clip-Higher (Asymmetric Clipping). We extend and evaluate them in the multi-turn agent setting.
    - **E11:** ablation/ablation | 4.3 Generating Useful Trajectories for RL Training | medium
      locator:: section 4.3, Tables 1-2
      quote:: Diverse task instances enable better policy contrast and generalization across environments. Moderate action budgets provide enough planning space and avoid the noise introduced by overly long sequences. Up-to-date rollouts ensure optimization targets remain aligned with current policy behavior.
    - **E12:** ablation/ablation | 4.3 Generating Useful Trajectories for RL Training | medium
      locator:: section 4.3 and Figure 7
      quote:: As shown in Figure 7, agents trained with fresher rollouts (Online-1) achieve faster convergence and better generalization across tasks compared to those with delayed updates (e.g., Online-5 or Online-10).
    - **E13:** result/experiment_result | 4.4 Reasoning Improves Generalization | medium
      locator:: section 4.4, Tables 3-4
      quote:: As shown in Table 3, models trained with reasoning traces generalize better in Bandit and even in the counterintuitive BanditRev, suggesting that reasoning supervision helps internalize symbolic cues beyond memorization.
    - **E14:** result/experiment_result | 4.4 Reasoning Improves Generalization | medium
      locator:: section 4.4, Table 4 and Figure 14
      quote:: Even when the output format includes explicit <think> segments, removing them (no-think variant) often yields comparable or even better performance. To understand this degradation, we analyze average response length during training and find that reasoning traces consistently shrink over time.
    - **E15:** limitation/limitation | 6. Conclusions and Limitations | high
      locator:: section 6
      quote:: Limitations of our work include the focus on relatively small-scale tasks, the omission of established RL practices like replay buffers, and the absence of multimodal tasks—which we leave for future work.
    - **E16:** result/experiment_result | G. Comparing Agent RL with Supervised Fine-Tuning | medium
      locator:: appendix G
      quote:: SFT achieves 74.6% and 23% performance on Sokoban and Frozen Lake, respectively. Compared to the 20.3% and 21.8% performance with StarPO-S. The results indicate that SFT demonstrates superior performance to RL approaches.
