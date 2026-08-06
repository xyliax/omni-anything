- **Title:** Agent Lightning: Train ANY AI Agents with Reinforcement Learning
- **Summary:** Agent Lightning turns existing agent executions into transition-level reinforcement-learning data so training can be separated from the agent framework and reused across heterogeneous agent workflows.
- **Paper Type:** system
- **Venue:** arXiv preprint 2025
- **Authors:** Xufang Luo, Yuge Zhang, Zhiyuan He, Zilong Wang, Siyun Zhao, Dongsheng Li, Luna K. Qiu, Yuqing Yang; Microsoft Research
- **Keywords:** agent training, reinforcement learning, LLM agents, transition-based RL, training-agent disaggregation, observability
- ## Orientation
    - **Background:** AI agents are programs that call a large language model (LLM), a text model that turns prompts into responses, and tools, ordinary functions or services that act outside the model. Training such agents means improving the model inside a running program, not only improving a standalone chat prompt.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** A developer may already have an agent that searches, writes code, queries databases, or calls tools, and wants it to learn from success and failure without rewriting the whole agent inside a training system.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** The model may be called at different moments, see different context each time, and receive useful feedback only after the whole run finishes, while the surrounding program can branch, retry, or call tools.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Record each model call with its visible input, generated output, and reward signal, then train from those records while leaving the original agent program in place.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a systems view of reinforcement learning (RL), training by rewarding actions, for AI agents: it attacks the gap between real agent code and RL trainers that usually expect a simple prompt-response loop or a rebuilt rollout environment.
      claim_kind:: analyst_assessment
      evidence:: E2, E15
    - **One-Sentence Contribution:** Agent Lightning improves agent fine-tuning by recording each large language model (LLM), a text model that maps prompts to responses, call as a standalone training transition instead of forcing the whole agent run into one concatenated sequence.
      evidence:: E1, E7
    - **Mental Model:** Picture the agent as a busy workshop: Agent Lightning puts a receipt on every model call, then trains from the receipts without moving the workshop into the trainer.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is breadth: the same framework is demonstrated on three agent frameworks and task types with improving reported reward curves, although without variance or repeat-count reporting.
      evidence:: E11, E12, E13, E14
        - Supports C1: LangChain text-to-SQL, OpenAI Agents SDK retrieval-augmented generation, and AutoGen calculator agents; different frameworks and datasets; qualitative integration claim; partial support because code-change amount is not measured.
          evidence:: E11
        - Supports C4: Spider text-to-SQL with Llama-3.2-3B-Instruct; baseline step zero test reward 0.15; metric answer accuracy reward; final reported test reward 0.57; medium support due missing variance.
          evidence:: E12
        - Supports C4: Calc-X math tool-use with AutoGen and calculator; baseline step zero test reward 0.05; metric answer accuracy reward; final reported test reward 0.77; medium support due missing repeat counts.
          evidence:: E14
    - **Main Caveat:** The mechanism is convincing as a decoupling interface, but the reported algorithm uses equal final-return credit for every action and the evaluation does not isolate whether the interface, the runtime, or the RL update is responsible for each gain.
      claim_kind:: analyst_assessment
      evidence:: E8, E17
- ## Argument Map
    - **Problem and Stakes:** The paper targets the mismatch between reinforcement learning (RL), training policies from reward feedback, and deployed AI agents whose behavior depends on multiple model calls, tool calls, and framework-specific orchestration. The stakes are practical: if RL requires rebuilding every agent inside a trainer, agent learning remains brittle and hard to scale across real applications.
      evidence:: E2, E3
    - **Prior Gap:** Prior multi-turn RL work often packs a full interaction into one long sequence and uses masking, a rule that hides tokens from loss or attention, while many RL systems assume the trainer knows the agent's execution logic. Agent Lightning's gap claim is that this coupling is incompatible with diverse agents built in LangChain, OpenAI Agents SDK, AutoGen, or custom code.
      evidence:: E15, E1
    - **Key Insight:** The key insight is to treat agent execution as a partially observable Markov decision process (POMDP), where the model sees only part of the current program state, and to train from transitions, records of one model input, one output, and an assigned reward. This makes the learning interface independent of how the agent constructed that input.
      evidence:: E4, E7
    - **Claims:** The paper's argument rests on four falsifiable claims about interface generality, algorithm compatibility, system integration, and empirical improvement.
      claim_kind:: analyst_assessment
        - C1: A unified transition interface decouples agent execution from RL training enough to support existing agents across multiple frameworks with almost no agent-code modification.
          evidence:: E1, E10, E11, E18
        - C2: LightningRL can reuse existing single-turn LLM RL algorithms by assigning episode returns to per-call transitions and then letting the single-turn algorithm handle token-level updates.
          evidence:: E7, E8, E9
        - C3: The Training-Agent Disaggregation architecture makes the trainer agent-agnostic and the client agent trainer-agnostic while still collecting traces, rewards, failures, and intermediate signals.
          evidence:: E10, E16
        - C4: Across text-to-SQL, retrieval-augmented generation, and calculator-assisted math QA, Agent Lightning produces continuous reported reward improvements from the same base LLM family.
          evidence:: E11, E12, E13, E14
- ## Mechanism and Design
    - **Core Mechanism:** Agent Lightning observes the agent at component boundaries: a state is the current program snapshot, semantic variables are the meaningful values used by model or tool calls, and each call records metadata, input, and output. For learning, it filters this richer trace down to policy-LLM transitions and rewards, which are the minimum data needed by the RL update.
      evidence:: E4, E5, E7
        - The unified interface keeps tool calls and model calls in the execution record, but the policy update can select only the transitions for the model or role being optimized.
          evidence:: E5, E7
        - Rewards can be terminal-only or intermediate; terminal-only feedback is treated as a valid special case rather than a separate interface.
          evidence:: E6
    - **Data / Control Flow:** The server receives tasks, exposes a task-specific OpenAI-like API endpoint to clients, the client runs the existing agent through that endpoint, captures traces and rewards, and returns transition data to the trainer for model updates. The updated model is then served back through the same API shape, closing the training loop without placing agent logic on GPU trainer machines.
      evidence:: E10, E16
        - Task batches are dispatched from the Lightning Server to available Lightning Clients, so rollout work can be spread across client workers and machines.
          evidence:: E10, E16
        - Trace capture can use OpenTelemetry, an observability standard for recording distributed execution events, AgentOps, or a lightweight tracer embedded in the model API endpoint.
          evidence:: E16
        - LightningRL groups transitions for the same task when adapting value-free methods such as Group Relative Policy Optimization (GRPO), which estimates advantages by comparing sampled responses for the same prompt.
          evidence:: E8
    - **Design Decisions:** The main design choice is transition decomposition instead of whole-trajectory concatenation: it preserves the agent's natural context construction and avoids custom masking while accepting a simpler, currently coarse credit-assignment rule. The system choice is disaggregation: keep heavy LLM training in the RL framework and keep flexible application logic in the client runtime.
      evidence:: E8, E9, E10
        - Need: avoid coupling to framework-specific agent traces; choice: train on per-call transitions; alternative: concatenate turns and mask; tradeoff: easier integration but credit assignment becomes an explicit module.
          evidence:: E8, E9, E15
        - Need: make existing single-turn RL algorithms usable; choice: assign the same final return to each action in the current implementation; alternative: learned or heuristic high-level value functions; tradeoff: simple and tested, but weak for long-horizon blame assignment.
          evidence:: E8, E17
        - Need: collect traces without invasive changes; choice: reuse observability instrumentation and an API tracer; alternative: framework-specific logging adapters; tradeoff: broad coverage, but trace quality depends on instrumentation and endpoint discipline.
          evidence:: E16
    - **Implementation Surface:** The exposed surface is a Lightning Server tied to an RL framework, a Lightning Client wrapping the agent runtime, an OpenAI-like model API, trace capture, task upload, worker parallelism, error handling, and optional Automatic Intermediate Rewarding (AIR), which turns monitoring events into intermediate reward signals. Appendix code sketches an adapter script rather than a rewrite of the original agent.
      evidence:: E10, E16, E18
- ## Evaluation and Evidence
    - **Setup:** The evaluation uses three agent scenarios: Spider text-to-SQL with LangChain and an SQL executor, MuSiQue open-domain QA with OpenAI Agents SDK and a Wikipedia retriever, and Calc-X math QA with AutoGen and a calculator. All reported experiments use Llama-3.2-3B-Instruct as the base model, with different reward definitions per task.
      evidence:: E11, E12, E13, E14
    - **Claim-Evidence Matrix:** C1 and C3 are mainly supported by system design plus cross-framework demonstrations; C2 is supported by the formal data extraction and LightningRL description; C4 is supported by reward curves. The evidence is strongest for feasibility and weakest for causal attribution because no ablation separates interface, algorithm, and runtime effects.
      claim_kind:: analyst_assessment
      evidence:: E7, E8, E10, E11, E12, E13, E14
        - Supports C1: framework diversity and adapter-style appendix support the decoupling claim, but the paper does not quantify code modifications.
          claim_kind:: analyst_assessment
          evidence:: E1, E11, E18
        - Supports C2: transition extraction and LightningRL explain how single-turn methods are reused, but the current identical-credit rule leaves long-horizon credit quality under-tested.
          claim_kind:: analyst_assessment
          evidence:: E7, E8, E17
        - Supports C4: all three tasks show improved reported test rewards, but the paper does not report confidence intervals, seeds, or variance.
          claim_kind:: analyst_assessment
          evidence:: E12, E13, E14
    - **Headline Results:** Text-to-SQL test reward improves from 0.15 to 0.57, RAG test reward from 0.005 to 0.230, and calculator QA test reward from 0.05 to 0.77 in the reported curves. These are directional improvements, not statistically established effect sizes, because uncertainty and repeat counts are not reported.
      evidence:: E12, E13, E14
        - Supports C4: Spider; LangChain; answer accuracy reward; 0.15 to 0.57 on test reward; caveat: no variance or baseline trainer comparison beyond the training trajectory.
          evidence:: E12
        - Supports C4: MuSiQue over Wikipedia; OpenAI Agents SDK; 0.9 correctness plus 0.1 format reward; 0.005 to 0.230 on test reward; caveat: plateau and oscillation after early gains.
          evidence:: E13
        - Supports C4: Calc-X; AutoGen plus calculator; answer-accuracy reward; 0.05 to 0.77 on test reward; caveat: no ablation showing whether tool-call formatting or reasoning improved most.
          evidence:: E14
    - **Ablations and Sensitivity:** Not reported: the paper does not include ablations for equal versus learned credit assignment, transition decomposition versus masking under matched trainers, AIR on/off, telemetry method, worker scaling, or reward-weight sensitivity.
      claim_kind:: analyst_assessment
    - **Reproducibility Gaps:** The paper reports a GitHub repository, public datasets, base model, frameworks, tools, and an appendix adapter pattern, which lowers reuse friction. Missing trust fields include hardware budget, trainer hyperparameters, seeds, repeats, variance, exact train/test splits after task preprocessing, and stable API guarantees.
      claim_kind:: analyst_assessment
      evidence:: E1, E11, E18
- ## Technical Judgment
    - **What Holds Up:** The strongest part is the interface argument: per-call transitions are the right abstraction for agents whose context is built by arbitrary code, and the server-client split cleanly matches the different operational needs of trainers and agent runtimes. The cross-framework experiments support feasibility even if they do not prove optimality.
      claim_kind:: analyst_assessment
      evidence:: E7, E9, E10, E11
    - **Where It May Fail:** The approach may weaken when long-horizon tasks require precise blame assignment across many calls, when rewards are too sparse for equal final-return assignment, or when the agent's important state is not visible in captured model inputs and telemetry. It may also face engineering limits when tools or environments are slow, flaky, stateful, or hard to instrument.
      claim_kind:: analyst_assessment
      evidence:: E6, E8, E16, E17
    - **Relation to Other Work:** Compared with concatenation-and-masking multi-turn RL, Agent Lightning shifts the unit of training from a whole dialogue trace to a per-call transition, trading sequence-level simplicity for cleaner integration with arbitrary agent workflows. Compared with large-scale RL systems such as verl, OpenRLHF, TRL, ROLL, and AReaL, its novelty is less the trainer and more the boundary that lets existing agents act as rollout producers.
      claim_kind:: analyst_assessment
      evidence:: E8, E9, E15
    - **Transferable Lesson:** For learning over complex software systems, first choose the smallest stable observation boundary that preserves the decision and reward, then make the trainer consume that boundary instead of importing the whole application. This pattern generalizes beyond agent RL to prompt optimization, tool-policy learning, and other program-level feedback loops.
      claim_kind:: analyst_assessment
      evidence:: E4, E7, E10, E17
- ## Glossary
  collapsed:: true
    - AI agent: A software system that calls one or more LLMs and may also call tools, APIs, databases, or environments while solving a task.
    - Reinforcement learning: A training paradigm where a policy improves by receiving scalar rewards for actions rather than step-by-step labels.
    - Transition: In this paper, the learning record for one policy-LLM call: the current input or observation, the model output as action, and an assigned reward.
    - Markov Decision Process: A decision model with state, action, transition, and reward; the paper uses a partially observable version because the LLM only sees the input context, not the full program state.
    - Semantic variable: A meaningful program value, such as a user query, generated SQL, retrieved passages, or answer, that is used or modified by an LLM or tool call.
    - Credit assignment: The problem of deciding which earlier action deserves how much responsibility for a later reward; Agent Lightning currently uses equal final-return assignment.
    - LightningRL: The paper's hierarchical RL method: assign episode return across LLM-call transitions, then use existing single-turn LLM RL methods for token-level optimization.
    - Group Relative Policy Optimization: A value-free LLM RL method that estimates advantages by comparing multiple sampled outputs for the same task or prompt.
    - Masking: A training technique that hides selected tokens from loss or attention; the paper argues custom masks are brittle for heterogeneous agent traces.
    - Training-Agent Disaggregation: A system architecture that keeps RL training and GPU model serving on the server side while existing agent logic and tools run in client runtimes.
    - OpenTelemetry: An observability standard used to capture execution traces; Agent Lightning reuses it to collect agent trajectories without rewriting agent logic.
    - Automatic Intermediate Rewarding: A mechanism that converts monitoring signals, such as tool-call success or failure, into intermediate rewards for agent training.
- ## Evidence Index
  collapsed:: true
    - **E1:** method/paper_statement | Abstract | high
      locator:: Abstract, opening paragraph
      quote:: The abstract presents Agent Lightning as a framework for RL-based training of LLMs in arbitrary agents, emphasizing decoupled agent execution and training, integration with LangChain, OpenAI Agents SDK, AutoGen, and near-zero code modifications.
    - **E2:** problem/paper_statement | 1 Introduction | high
      locator:: Introduction, challenge paragraph
      quote:: The introduction contrasts static single-call RL settings with agents whose executions include multiple LLM invocations, distinct prompts and responses, external tools, APIs, environments, and diverse application-specific designs.
    - **E3:** background/paper_statement | 2 Modern AI Agents | high
      locator:: Sections 2.1-2.3
      quote:: The paper defines an AI agent broadly as software that includes LLM calls, built from models and tools, with orchestration that may be dynamic and implemented through frameworks or from scratch.
    - **E4:** insight/paper_statement | 3.1 Unified Data Interface | high
      locator:: Section 3.1, first two paragraphs
      quote:: Agent Lightning treats software execution as graph-like but argues that parsing a full execution graph is difficult and unnecessary; for RL it is enough to identify state and calls that drive state transitions.
    - **E5:** formula/paper_statement | 3.1.1 State and Call | high
      locator:: Section 3.1.1, equations for state and call
      quote:: State is described as a snapshot of execution variables, while a call contains metadata, input, and output for a component invocation, where the component can be an LLM or a tool.
    - **E6:** method/paper_statement | 3.1.2 Reward and Dataset | high
      locator:: Section 3.1.2
      quote:: Each execution is augmented with scalar rewards for component invocations; rewards may appear at intermediate steps or only at the end, with terminal-only rewards treated as a special case.
    - **E7:** algorithm/paper_statement | 3.2.2 Data Extraction for RL | high
      locator:: Section 3.2.2, extraction equations and summary paragraph
      quote:: For RL, the paper extracts only policy-LLM inputs, outputs, and rewards from executions, intentionally ignoring the detailed reasons and sources that constructed each input in the dynamic agent logic.
    - **E8:** algorithm/paper_statement | 3.3.2 Extend to Agent Scenarios via LightningRL | high
      locator:: Section 3.3.2, first mechanism paragraphs
      quote:: LightningRL decomposes trajectories into transitions, assigns episode-level return across actions with a credit assignment module, then relies on existing single-turn RL methods for token-level learning; the implementation assigns the same final return to each action.
    - **E9:** system_design/paper_statement | 3.3.2 Extend to Agent Scenarios via LightningRL | high
      locator:: Section 3.3.2, advantages over masking paragraphs
      quote:: The paper argues that transition data allows flexible observations, avoids concatenation-and-masking, avoids positional-continuity issues from masked sequences, and reduces excessively long contexts by breaking long trajectories into transition batches.
    - **E10:** system_design/implementation_detail | 3.4.1 Training-Agent Disaggregation Architecture | high
      locator:: Section 3.4.1 and Figure 4
      quote:: The system separates trainer and rollout-agent execution: the RL framework manages the model and exposes an OpenAI-like API, while client-side agent logic and tools run independently and report traces back to the server.
    - **E11:** experiment_setup/paper_statement | 4 Results | high
      locator:: Table 1 and task introductions
      quote:: The experiments cover text-to-SQL with LangChain on Spider, open-domain question answering with the OpenAI Agents SDK on MuSiQue, and math question answering with AutoGen on Calc-X, all using Llama-3.2-3B-Instruct.
    - **E12:** result/experiment_result | 4.1 Text-to-SQL via LangChain | medium
      locator:: Section 4.1 and Figure 5
      quote:: In Spider text-to-SQL, the paper reports a three-agent LangChain workflow, tunes SQL writing and rewriting agents, and shows test reward moving from 0.15 at step 0 to 0.57 at step 432.
    - **E13:** result/experiment_result | 4.2 Retrieval-Augmented Generation via OpenAI Agents SDK | medium
      locator:: Section 4.2 and Figure 6
      quote:: In MuSiQue retrieval-augmented generation over Wikipedia, the reward combines word-level F1 and format compliance; the test curve rises from 0.005 at step 0 to 0.230 at step 200.
    - **E14:** result/experiment_result | 4.3 Math QA with Tool Usage via AutoGen | medium
      locator:: Section 4.3 and Figure 7
      quote:: In Calc-X math tool-use, the AutoGen agent decides calculator calls and integrates tool outputs; the reported test reward rises from 0.05 at step 0 to 0.77 by later checkpoints.
    - **E15:** prior_work/paper_statement | 5.1 Related Work | high
      locator:: Related Work, multi-turn RL and RL systems paragraphs
      quote:: The related-work section says many multi-turn RL approaches concatenate turns and add masks, while RL training systems often require agent execution logic to be rebuilt or coupled inside the training framework.
    - **E16:** implementation/implementation_detail | 3.4.2 Agent Runtime | high
      locator:: Agent Runtime, data capture and robustness paragraphs
      quote:: The client runtime captures traces through OpenTelemetry and AgentOps or a lightweight API-endpoint tracer, supports concurrent workers across machines, handles failed tasks, and can convert monitoring signals into intermediate rewards.
    - **E17:** limitation/limitation | 5.2 Future Work | medium
      locator:: Future Work, optimization methods and RL algorithms
      quote:: The future-work section points to more optimization methods, long-horizon credit assignment, exploration, off-policy algorithms, and further system disaggregation, implying these areas are not fully solved in the current work.
    - **E18:** implementation/implementation_detail | Appendix A | medium
      locator:: Appendix A, training script note
      quote:: The appendix gives a minimal training-script pattern using Client, Resource, and Task, and notes that the open-source API may change, directing readers to the GitHub repository for current details.
