- **Title:** ProRL Agent: Rollout-as-a-Service for RL Training of Multi-Turn LLM Agents
- **Summary:** ProRL Agent makes multi-step agent training traces a standalone HTTP service so reinforcement learning trainers can use sandboxed tool-using agents without owning their execution lifecycle.
- **Paper Type:** system
- **Venue:** arXiv preprint 2026 (arXiv:2603.18815v1)
- **Authors:** Hao Zhang, Mingjie Liu, Shaokun Zhang, Songyang Han, Jian Hu, Zhenghui Jin, Yuchi Zhang, Shizhe Diao, Ximing Lu, Binfeng Xu, Zhiding Yu, Jan Kautz, Yi Dong; affiliations not reported in provided text
- **Keywords:** agent reinforcement learning, rollout-as-a-service, multi-turn LLM agents, sandboxed execution, HPC deployment, RL infrastructure
- ## Orientation
    - **Background:** In agent reinforcement learning, a model learns by trying tasks, using tools, and receiving rewards. A rollout is one complete try: the model acts, sees results, tries again, and leaves a trace that training can learn from.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** The trainer wants many finished practice attempts, but each attempt may need a fresh workspace, shell commands, web search, code execution, and a final check.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** The acting side waits on files, containers, tools, and tests, while the learning side wants steady GPU work; tying them together makes both sides harder to scale and change.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Put the messy acting loop behind a service boundary, so trainers request completed attempts instead of managing every tool interaction themselves.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a systems paper on agent reinforcement learning: it targets the engineering gap between GPU-heavy policy training and slow, tool-heavy agent execution, where existing frameworks keep too much rollout control inside the trainer.
      claim_kind:: analyst_assessment
      evidence:: E3, E4
    - **One-Sentence Contribution:** ProRL Agent improves multi-turn large language model agent reinforcement learning by moving the full rollout lifecycle into a standalone HTTP service that returns completed trajectories and rewards to any trainer.
      evidence:: E5
    - **Mental Model:** Picture a trainer as a kitchen that only asks for finished dishes: the rollout service runs the prep stations, tools, cleanup, and tasting, then hands back a scored recipe trace.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is a mix of end-to-end training gains on SWE-Bench Verified, cross-domain learning curves, node-scaling measurements, and component ablations.
      evidence:: E15, E16, E17, E18
        - Supports C4: Qwen3 8B software-engineering training on the SkyRL-v0 SWE-Gym subset; closest prior SkyRL-Agent-8B-v0 reported 9.4 on SWE-Bench Verified; ProRL Agent-8B reports 18.0; medium support because repeat counts and uncertainty are not reported.
          evidence:: E15
        - Supports C4: STEM, math, and code agents trained with different tool and reward setups; starting-to-final metrics improve across all three curves; medium support because the curves do not isolate infrastructure from task recipe effects.
          evidence:: E16
        - Supports C2: 14B DAPO rollout throughput with all components is 0.37 instance/sec versus 0.25 without load balancing, 0.29 without Efficient Bash, and 0.30 without stale job cleanup; medium support because no variance is reported.
          evidence:: E18
    - **Main Caveat:** The system boundary is compelling, but the paper mostly reports single-run aggregate results; it does not separate the effect of the service architecture from the ProRL recipe, DAPO scheduling, task design, and hardware budget.
      claim_kind:: analyst_assessment
      evidence:: E14, E15, E18
- ## Argument Map
    - **Problem and Stakes:** Multi-turn large language model agents, meaning models that solve tasks through repeated tool actions and observations, make reinforcement learning from verifiable rewards harder because each training sample requires a long rollout, meaning a full task attempt with environment interactions and final scoring. The paper frames rollout generation as a system bottleneck because it mixes heterogeneous sandboxes, variable tool latency, and delayed feedback before the trainer can update the policy.
      evidence:: E2, E3
    - **Prior Gap:** The reported gap is not that prior work lacks tools or environments, but that rollout orchestration remains embedded in trainer processes or trainer-owned libraries, so changing trainers, environments, or runtime constraints requires porting execution logic. Table 1 positions ProRL Agent as different from SkyRL-Agent, VeRL-Tool, Agent Lightning, rLLM, and GEM on three axes: training-rollout decoupling, rootless sandboxing, and scaffold independence.
      evidence:: E4
    - **Key Insight:** The paper's key insight is to treat rollout like inference-as-a-service: a trainer sends task instances over HTTP and receives completed token-level trajectories and rewards, while a separate server owns sandbox setup, agent execution, tool use, evaluation, and LLM inference coordination. This boundary matches the operational split between I/O-heavy rollout work and GPU-heavy policy optimization.
      evidence:: E5, E3
    - **Claims:** The paper's argument reduces to four falsifiable claims about the service boundary, the runtime design, token fidelity, and training/system outcomes.
      claim_kind:: analyst_assessment
        - C1: A rollout-as-a-service boundary can decouple agent execution from reinforcement learning trainers without removing the information trainers need for policy updates.
          evidence:: E5, E11
        - C2: A practical service needs a pluggable task lifecycle, rootless sandbox runtime, independent rollout-stage worker pools, and controllable LLM backend management.
          evidence:: E6, E7, E9, E10
        - C3: Token-in/token-out communication, where token IDs rather than text are the canonical trajectory representation, avoids re-tokenization drift between rollout and training.
          evidence:: E11
        - C4: The infrastructure supports effective end-to-end reinforcement learning across software engineering, STEM, math, and coding tasks while scaling rollout throughput and benefiting from the proposed system components.
          evidence:: E15, E16, E17, E18
- ## Mechanism and Design
    - **Core Mechanism:** ProRL Agent is a rollout server: an HTTP service receives a task instance, dispatches it to a task-specific handler, runs the agent inside a sandbox, evaluates the outcome, and returns trajectory plus reward. The trainer remains responsible for policy optimization, while the service owns the acting lifecycle.
      evidence:: E5, E6
        - Task-specific logic lives behind AgentHandler, an interface whose init, run, and eval methods prepare the environment, drive the multi-turn agent loop, and compute reward.
          evidence:: E6
        - The server maps those lifecycle stages to separate worker pools so container startup, agent execution, and evaluation can overlap across different jobs.
          evidence:: E9
        - LLM inference backends are managed dynamically through the service, with min-heap routing by assignment count to spread tasks across registered servers.
          evidence:: E10
    - **Data / Control Flow:** The trainer sends a process request with an instance and sampling parameters, the server enqueues the job through init, run, and eval, and the HTTP caller receives completed trajectory and evaluation results. During run, prompt_ids and response_ids keep the model-visible conversation in token IDs, while new environment observations are tokenized and appended.
      evidence:: E5, E9, E11
        - Init provisions a sandbox runtime and task configuration, which makes environment startup a server-side concern rather than trainer code.
          evidence:: E6, E7
        - Run alternates model completions with tool actions; Efficient Bash, direct IPython, and Unix domain sockets reduce per-action overhead inside the sandbox.
          evidence:: E8
        - Eval scores the task after rollout, while stage-specific exception callbacks and final serialization keep failed jobs from stalling the shared pipeline.
          evidence:: E6, E12
    - **Design Decisions:** The system repeatedly chooses a narrow lifecycle owner instead of a larger framework rewrite: task logic is owned by handlers, isolation by SingularityRuntime, concurrency by staged queues, and policy freshness by backend registration APIs. These choices buy portability and independent scaling at the cost of more explicit service-state management.
      claim_kind:: analyst_assessment
      evidence:: E5, E7, E9, E10
        - Need: support heterogeneous tasks on shared clusters; choice: SingularityRuntime with rootless execution, loopback IP allocation, fakeroot, and optional network isolation; alternative: Docker-centered sandboxes; tradeoff: the design fits HPC better but depends on Singularity-compatible images and cluster policy.
          claim_kind:: analyst_assessment
          evidence:: E7
        - Need: avoid one job worker waiting through slow, mismatched phases; choice: independent init, run, and eval pools; alternative: a single worker owns a full job; tradeoff: throughput improves when queues are balanced, but operators must size pools for the workload.
          claim_kind:: analyst_assessment
          evidence:: E9
        - Need: preserve the exact sequence used to compute log probabilities; choice: token IDs are canonical; alternative: pass text and re-tokenize in the trainer; tradeoff: stronger fidelity but tighter coupling to tokenizer-compatible inference responses.
          claim_kind:: analyst_assessment
          evidence:: E11
    - **Implementation Surface:** The exposed surface is intentionally small: HTTP endpoints submit and cancel jobs, register or clear LLM servers, start or stop the server, and report status. The client-side trainer integration adds locality-aware LLM server assignment and DAPO, Dynamic Sampling Policy Optimization, replenishment logic for informative prompts.
      evidence:: E10, E12, E13
        - Backend registration and clearing let the trainer swap model checkpoints without restarting the rollout server, so subsequent jobs use updated LLM endpoints.
          evidence:: E10
        - Cancellation marks jobs discarded, cancels active async work, closes the container runtime, and unblocks the waiting HTTP handler.
          evidence:: E12
        - The DAPO path replenishes jobs, terminates stale active jobs after enough informative prompts are collected, and carries unfinished jobs into the next iteration.
          evidence:: E13
- ## Evaluation and Evidence
    - **Setup:** The default training setup uses Dynamic Sampling Policy Optimization (DAPO), which filters prompts whose rollouts give uniform rewards, with batch size 32, mini-batch size 8, 8 rollouts per instance, KL coefficient 1e-4, learning rate 1e-6, and 32 NVIDIA H100 GPUs. Software-engineering training uses Qwen3 4B, 8B, and 14B models on the 293-instance SWE-Gym subset used in SkyRL-v0 and evaluates on SWE-Bench Verified.
      evidence:: E14, E15
    - **Claim-Evidence Matrix:** The evidence is broad but not equally strong: service design claims are supported by concrete architecture descriptions, while performance claims rely on aggregate tables and curves without reported statistical uncertainty.
      claim_kind:: analyst_assessment
      evidence:: E5, E15, E18
        - C1: Supported by the HTTP service architecture and token trajectory interface, but not by a migration study across many trainer implementations.
          claim_kind:: analyst_assessment
          evidence:: E5, E11
        - C2: Supported by mechanism descriptions and ablations showing load balancing, Efficient Bash, and stale job cleanup each improve throughput in the reported DAPO setting.
          evidence:: E7, E9, E18
        - C4: Supported by SWE-Bench Verified tables, domain training curves, and node-scaling results, with the caveat that the reported numbers do not include repeat counts or confidence intervals.
          claim_kind:: analyst_assessment
          evidence:: E15, E16, E17
    - **Headline Results:** On SWE-Bench Verified, ProRL Agent reports improved reproduced scores across model sizes: 4B rises from 14.8 to 21.2, 8B from 9.6 to 18.0, and 14B from 15.4 to 23.6. Against the closest reported prior comparison in Table 2, the 8B ProRL Agent score of 18.0 is 8.6 points above SkyRL-Agent-8B-v0 at 9.4, while the 14B score of 23.6 is 2.0 points above SkyRL-Agent-14B-v0 at 21.6.
      evidence:: E15
        - Software engineering: supported claim C4; configuration Qwen3 4B/8B/14B with DAPO on SWE-Gym subset; baseline reproduced base models and reported SkyRL-Agent where available; metric SWE-Bench Verified score; direction positive; uncertainty not reported.
          evidence:: E15
        - General domains: supported claim C4; STEM mean reward, AMC math Pass@1, and Codeforces Pass@1 all improve over training; baselines are each curve's step-zero model; deltas are roughly STEM upward to the reported final region, math 0.40 to about 0.89, and code 0.23 to about 0.42.
          evidence:: E16
        - Scaling: supported claim C4; software-engineering rollout throughput increases from one to eight nodes for 4B, 8B, and 14B models, but the table is not perfectly monotone for every intermediate point and reports no variance.
          claim_kind:: analyst_assessment
          evidence:: E17
    - **Ablations and Sensitivity:** The component ablation removes one of load balancing, Efficient Bash, or stale job cleanup in DAPO training on Qwen3-14B-Instruct-2507 using 8 H100 GPUs. Full throughput is 0.37 instance/sec with 78 percent GPU utilization and 0.42 second action time; removing load balancing drops throughput to 0.25, removing Efficient Bash raises action time to 0.78 seconds and throughput to 0.29, and removing stale job cleanup gives 0.30.
      evidence:: E18
        - Load balancing appears to matter most for GPU utilization in the reported setting, dropping utilization from 78 percent to 42 percent when removed.
          evidence:: E18
        - Efficient Bash directly targets tool latency: the reported average shell-command action time is 0.42 seconds with the component and 0.78 seconds without it.
          evidence:: E18
        - Not reported: sensitivity to worker-pool sizes, container startup distribution, network topology, number of LLM backends, per-task timeout policy, or stochastic variation across training seeds.
          claim_kind:: analyst_assessment
    - **Reproducibility Gaps:** The paper reports that ProRL Agent is open sourced and integrated with NVIDIA NeMo Gym, and it gives enough architectural detail to understand the intended service boundary. Reproduction-critical fields remain thin in the provided text: exact repository URL or commit, Docker/Singularity image definitions, Slurm configuration, worker counts per stage, backend counts, training seeds, variance, and scripts for all reported curves are not specified.
      claim_kind:: analyst_assessment
      evidence:: E1, E14, E18
- ## Technical Judgment
    - **What Holds Up:** The central service boundary is well motivated because rollout and training genuinely have different bottlenecks, failure modes, and lifecycle owners. The design is more than a box diagram: AgentHandler, SingularityRuntime, stage queues, LLM backend registration, token IDs, cancellation, and ablated throughput components make the boundary concrete enough to evaluate.
      claim_kind:: analyst_assessment
      evidence:: E3, E5, E6, E18
    - **Where It May Fail:** The approach may lose advantage when rollouts are short, environments are homogeneous, Docker-based infrastructure is already acceptable, or trainer integration needs tighter in-process control than HTTP provides. The empirical case is also vulnerable to confounding because training improvements are reported together with the ProRL recipe, DAPO filtering, task-specific tools, and a fixed 32-H100 setup rather than an architecture-only controlled comparison.
      claim_kind:: analyst_assessment
      evidence:: E14, E15, E16
    - **Relation to Other Work:** Compared with SkyRL-Agent, VeRL-Tool, Agent Lightning, rLLM, and GEM as described by the paper, ProRL Agent shifts the ownership boundary: the trainer no longer controls the full agent loop, environment lifecycle, and evaluation. Technically, this is closer to turning rollout into a remote runtime service than to adding a tool server or environment abstraction inside an existing trainer.
      claim_kind:: analyst_assessment
      evidence:: E4, E5
    - **Transferable Lesson:** The reusable pattern is to decouple by lifecycle ownership, not by process placement alone: if one side owns long-lived external state, failures, cleanup, and heterogeneous latency, make that side a service with a narrow canonical data contract. For agent RL, the canonical contract must include token-level trajectories and reward, not just text transcripts.
      claim_kind:: analyst_assessment
      evidence:: E5, E11, E12
- ## Glossary
  collapsed:: true
    - agent reinforcement learning: Training a model by letting it act in an environment, observe results, receive rewards, and update its policy from those experiences.
    - rollout: One complete attempt in which an agent interacts with an environment and produces the trace later used for training.
    - sandbox environment: An isolated execution environment for tools, files, tests, and external actions so one rollout does not corrupt another or the host.
    - rollout-as-a-service: A service boundary where trainers request completed rollouts through an API instead of running the agent execution lifecycle locally.
    - AgentHandler: The ProRL Agent task plugin interface with init, run, and eval methods for setup, agent execution, and reward scoring.
    - SingularityRuntime: The paper's rootless container runtime wrapper for HPC clusters where Docker daemons or root-equivalent access are often unavailable.
    - token-in/token-out: Representing prompts, responses, and prior turns as token IDs so the trainer consumes the same token sequence generated during rollout.
    - re-tokenization drift: A mismatch caused when text generated during rollout is tokenized again later and yields a different token sequence.
    - Dynamic Sampling Policy Optimization: The reinforcement learning algorithm used in the paper; it filters prompts whose rollouts all succeed or all fail because they provide little gradient signal.
    - stale job cleanup: Cancelling or discarding rollouts that are no longer useful once the trainer has enough valid samples for an iteration.
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/metadata | Abstract | high
      locator:: Abstract and title block
      quote:: Under the rollout-as-a-service philosophy, we present PRORL AGENT, a scalable infrastructure that serves the full agentic rollout lifecycle through an API service. PRORL AGENT is open-sourced at PRORL Agent and integrated as part of NVIDIA NeMo Gym.
    - **E2:** problem/paper_statement | Introduction | high
      locator:: Introduction, paragraphs 1-2
      quote:: RL training requires repeatedly rolling out policies in these environments and using the resulting trajectories for optimization. As task scale and complexity grow, rollout generation becomes a major bottleneck due to the heterogeneous environments and non-instantaneous feedback inherent in agentic tasks.
    - **E3:** gap/paper_statement | Introduction | high
      locator:: Introduction, coupling limitations
      quote:: Rollout is I/O-intensive, involving sandbox creation, long-lived tool sessions, and asynchronous coordination across hundreds of concurrent instances. Training, by contrast, is GPU-intensive, centered on forward and backward passes, and gradient synchronization.
    - **E4:** prior_work/paper_statement | Related Work | medium
      locator:: Table 1 and Agent RL Infrastructures
      quote:: Across these frameworks, rollout orchestration, including environment lifecycle management, tool execution, trajectory collection, and evaluation, remains implemented as an in-process library within the training loop. Under this design, adopting a new training backend often requires re-implementing or porting the entire rollout stack.
    - **E5:** system_design/implementation_detail | System Design: Training-Rollout Decoupling | high
      locator:: Section 3.1 Overview and Figure 2
      quote:: ProRL Agent Server runs as a standalone HTTP service that accepts a task instance, executes the full agent rollout internally, and returns a completed trajectory with a reward signal. The training framework interacts with the server only through this interface.
    - **E6:** implementation/implementation_detail | Extensible Sandbox Environments | high
      locator:: Section 3.2.1 Pluggable Task Abstraction
      quote:: We encapsulate all task-specific logic in an abstract interface called AgentHandler, which defines three core lifecycle methods corresponding to the three pipeline stages: init, run, eval.
    - **E7:** implementation/implementation_detail | Extensible Sandbox Environments | high
      locator:: Section 3.2.2 HPC-Compatible Container Runtime
      quote:: We implement SingularityRuntime, a container system that requires no persistent daemon and runs entirely as an unprivileged user process to serve sandbox environments. Each container is launched as a child process in its own session.
    - **E8:** optimization/implementation_detail | Extensible Sandbox Environments | high
      locator:: Section 3.2.3 Efficient tool backends
      quote:: We optimize three critical tool backends. Efficient Bash replaces tmux with a ptyprocess-based direct pseudo-terminal. IPython connects to the kernel directly via its in-process API. UDS replaces TCP loopback for action communication inside the container.
    - **E9:** system_design/implementation_detail | ProRL Agent Server | high
      locator:: Section 3.3.1 Three-Stage Rollout Pipeline
      quote:: The three lifecycle methods of AgentHandler map onto three independent worker pools, each with its own queue. Initialization workers start containers, rollout workers drive agent loops, and evaluation workers score results and return them to the caller.
    - **E10:** algorithm/implementation_detail | ProRL Agent Server | high
      locator:: Section 3.3.2 LLM Backend Management
      quote:: Each LLM backend is stored alongside an assignment counter in a min-heap. Every time the rollout stage needs to issue an LLM call, ProRL Agent server automatically selects the backend with the lowest counter and assigns that entire task to the selected LLM.
    - **E11:** method/implementation_detail | ProRL Agent Server | high
      locator:: Section 3.3.3 Token-in/Token-out
      quote:: PROL AGENT eliminates this re-tokenization drift by using token IDs as the canonical representation throughout the entire training process. The rollout worker sends prompt_ids directly to the LLM backend and receives response_ids with per-token log-probabilities.
    - **E12:** system_design/implementation_detail | ProRL Agent Server | high
      locator:: Section 3.3.4 Job Lifecycle and Cancellation
      quote:: The training framework can abort any in-flight job at any time via POST /cancel. Once received, ProRL Agent server will mark the job as discarded, cancel the currently executing async task, close the associated container runtime, and signal completion.
    - **E13:** algorithm/implementation_detail | Connecting to RL Trainers | high
      locator:: Section 3.4 Efficient DAPO
      quote:: To address these bottlenecks, we implement an asynchronous replenishment mechanism: Continuous Throughput replenishes the job queue as soon as it empties, Early Termination terminates remaining active jobs once the target number of Informative Prompts is reached, and Cross-Iteration Persistence carries unfinished jobs over.
    - **E14:** experiment_setup/paper_statement | Experiments | high
      locator:: Section 4.1 Experimental Setup
      quote:: Unless otherwise specified, we adopt DAPO as the default RL algorithm. We use a batch size of 32, a mini-batch size of 8, and generate 8 rollouts per instance. All RL training is performed on 32 NVIDIA H100 GPUs.
    - **E15:** result/experiment_result | Main Results on Software Engineering | medium
      locator:: Section 4.2 and Table 2
      quote:: PRORL AGENT consistently improves performance across all model sizes. Compared with SkyRL-v0, the gains are particularly notable for the 8B model, where PRORL AGENT achieves nearly a 2x improvement on SWE-Bench Verified.
    - **E16:** result/experiment_result | Generality Across Agent Domains | medium
      locator:: Section 4.3 and Figure 4
      quote:: Figure 4 reports training curves for PRORL AGENT across three agent domains: mean reward during RL training of the STEM agent, Pass@1 on AMC during RL training of the math agent, and Pass@1 on Codeforces during RL training of the code agent.
    - **E17:** result/experiment_result | System Analysis | medium
      locator:: Section 4.4.1 and Figure 5
      quote:: Throughput increases nearly linearly with the number of nodes, indicating that PRORL AGENT can effectively leverage additional compute resources with minimal scaling overhead. Figure 5 reports instances per second as compute nodes increase.
    - **E18:** ablation/ablation | System Analysis | medium
      locator:: Section 4.4.2 and Table 3
      quote:: The results in Tab. 3 show that each proposed component contributes to higher rollout throughput during DAPO training. Load Balancing and Stale Job Cleanup improve throughput by increasing GPU utilization, while Efficient Bash improves throughput by reducing action execution time.
