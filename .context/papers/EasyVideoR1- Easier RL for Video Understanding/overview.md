- **Title:** EasyVideoR1: Easier RL for Video Understanding
- **One-Sentence Summary:** EasyVideoR1 is a video RLVR framework that connects video tensor caching, vLLM rollout, task-aware rewards, FSDP/GRPO training, and asynchronous evaluation; it is useful as a JoyAI training substrate, but it is not itself a streaming interaction or streaming-context RL method.
- **Paper Type:** adjacent video RLVR framework / not core streaming RL
- **Venue:** arXiv / GitHub report, 2026
- **Authors:** Chuanyu Qin, Chenxu Yang, Qingyi Si, Naibin Gu, Dingyu Yao, Zheng Lin, Peng Fu, Nan Duan, Jiaqi Wang
- **Affiliations:** Institute of Information Engineering, Chinese Academy of Sciences; University of Chinese Academy of Sciences; JD.COM
- **Resources:** [Paper](https://arxiv.org/abs/2604.16893); [GitHub](https://github.com/cyuQ1n/EasyVideoR1); local clone `context/repos/EasyVideoR1`
- **Keywords:** video RLVR, GRPO, vLLM rollout, FSDP, video tensor cache, task-aware reward, mix-policy, AsyncLLMEngine evaluation

- ## Orientation
    - **Background:** Text RLVR is relatively mature, but video RL adds expensive decoding, frame sampling, resizing, long visual-token contexts, and many task-specific reward types.
      evidence:: E1, E2
    - **Problem Solved:** EasyVideoR1 makes ordinary video-understanding RL easier to run: given a video/image question, the model generates answers, a rule or judge scores them, and GRPO/PPO-style training updates the model.
      evidence:: E3, E4, E8
    - **Problem Not Solved:** The framework does not define per-second actions, silence, when to speak, old actions written back into future context, delayed rewards, policy versions, or stale streaming rollouts. Those belong to streaming interaction RL.
      claim_kind:: analyst_assessment
    - **Why Read It:** JoyAI reports extending EasyVideoR1 for its RL stage. For this project, EasyVideoR1 is the clean reference for how ordinary video RLVR organizes rollout, reward, trainer input, and evaluation.
      evidence:: E5, E8

- ## Quick Reference
    - **Main Value:** This is not a new streaming algorithm. It is an engineering framework for video RL training: cache video tensors, avoid repeated decoding, route rewards by task type, generate with vLLM, and train with FSDP.
      evidence:: E1, E3, E10
    - **Rollout Contents:** The input sample contains `problem`, `answer`, `videos/images`, `data_type`, and `problem_type`. The rollout engine feeds prompt tokens and multimodal data into vLLM and samples `n` responses per prompt.
      evidence:: E4, E5, E6
    - **Trainer Input:** The trainer consumes `prompt + response` sequences, response masks, reward tensors, old logprobs, reference logprobs, and advantages. The rule reward is usually written to the final valid response token.
      evidence:: E7, E8, E9
    - **Update Algorithm:** The default example uses GRPO: sample multiple answers for the same question, compare rewards within the group, increase probability for better answers, and decrease it for worse ones. The code also inherits DAPO, GSPO, ReMax, RLOO, GDPO, and other algorithm hooks.
      evidence:: E5, E9
    - **Architecture:** This is a colocated hybrid-engine setup. Actor, vLLM Rollout, and Reference share the same GPU pool and run in phases: load vLLM for generation, release it, then run FSDP logprob computation and actor update. It is not fully async rollout-training.
      evidence:: E8
    - **Training Sample Unit:** The unit is a video/image question plus generated answer plus reward. It is not a visible streaming state plus action plus later event feedback.
      claim_kind:: analyst_assessment
      evidence:: E4, E6, E7

- ## Argument Map
    - **Problem:** Existing RL frameworks were built mostly for text or image. Video introduces repeated decode/preprocess cost across rollout, logprob computation, and evaluation.
      evidence:: E2
    - **Gap:** Video-understanding tasks require many reward types, and evaluation is sensitive to frame sampling, fps, resolution, visual-token budget, and prompt templates.
      evidence:: E1, E2
    - **Key Idea:** Move video preprocessing out of the training loop, cache sampled/resized frames as `.pt` tensor artifacts, route task rewards through a unified interface, and support mixed image-video and offline-online data in one pipeline.
      evidence:: E1, E10
    - **Claim:** With these video-specific systems pieces in place, ordinary video RLVR becomes faster, easier to reproduce, and able to improve video benchmarks.
      evidence:: E1, E3, E11

- ## Mechanism and Design
    - **Data Format:** The minimal sample is `problem`, `answer`, `videos`, `data_type`, and `problem_type`; multiple-choice samples add `options`. This is a problem-level boundary, not a time-step boundary.
      evidence:: E4
    - **Video Cache:** `scripts/preprocess_videos.py` decodes videos offline and saves `frames`, `metadata`, `sample_fps`, and `preprocess_version` into `.pt` files that the training loader can reuse.
      evidence:: E10
    - **Rollout:** `generate_sequences()` takes `raw_prompt_ids` and `multi_modal_data`, builds vLLM inputs, calls `generate`, obtains response token ids, repeats prompts for `n`, and concatenates prompt and response.
      evidence:: E6
    - **Mix-Policy:** Samples may include `has_offline_trajectory` and `offline_output`; when enabled, one response in a group can be replaced by a pre-collected trajectory. This is useful inspiration for mixing replay or teacher traces.
      evidence:: E5, E6, E8
    - **Reward:** The reward manager decodes generated tokens and passes `response`, `ground_truth`, `data_type`, `problem_type`, `problem`, and `problem_id` to a custom reward function. The default video reward combines accuracy and format.
      evidence:: E7
    - **GRPO:** GRPO sums token rewards per response, groups by prompt index, normalizes by group mean/std, and writes the normalized score back over the response mask. The implementation requires `rollout.n > 1`.
      evidence:: E9
    - **Training Loop:** One step performs rollout engine preparation, batch generation, rollout release, token-length balancing, async reward, old logprob computation, ref logprob computation, advantage computation, actor update, validation, and checkpointing.
      evidence:: E8
    - **Evaluation:** The evaluation toolkit uses vLLM `AsyncLLMEngine`, video cache, async queues, optional LLM judge for open-ended tasks, and 22+ video benchmarks.
      evidence:: E11

- ## Evaluation and Evidence
    - **Efficiency:** The README/report claims about 1.5x faster rollout generation, about 2.9x faster log-probability computation, and about 1.47x overall wall-clock/token-throughput speedup from video caching.
      evidence:: E1, E3
    - **Model Quality:** The README/report claims +2.3% average gain over Qwen3-VL-8B base models across 10 video-understanding benchmarks, with a 32-H200, roughly 20-hour RL run reported in the paper abstract.
      evidence:: E1, E3
    - **Evaluation Coverage:** The eval toolkit covers LVBench, Video-MME, MVBench, MLVU, VideoMMMU, Charades-STA, STVG, and other benchmarks with task-specific scoring.
      evidence:: E11
    - **Caveat:** These results support the ordinary video RLVR pipeline, not streaming interaction sample boundaries, staleness, old-action context pollution, or fully async scheduling.
      claim_kind:: analyst_assessment

- ## Technical Judgment
    - **What Holds Up:** EasyVideoR1 gives a concrete, code-backed pipeline for video-as-RL-input: caching, reward routing, vLLM rollout, FSDP training, and async evaluation all have clear entry points.
      claim_kind:: analyst_assessment
    - **Most Useful Lesson:** It defines the ordinary baseline cleanly. If the task is static video QA, the training object is `video + question + answer + reward`. A streaming RL project must explain why that object is insufficient.
      claim_kind:: analyst_assessment
    - **Relation to JoyAI:** JoyAI can extend this substrate, but JoyAI must add its own semantics for per-second actions, silence, delegation, answer-centered windows, delayed results, and timing rewards.
      claim_kind:: analyst_assessment
    - **Streaming Infra Lesson:** Video tensor caching matters, but streaming cannot be reduced to caching a full video and treating it as one prompt. The closer design is reusable video chunks/KV/metadata plus sample packaging around valuable actions.
      claim_kind:: analyst_assessment
    - **How Not To Cite It:** Do not call EasyVideoR1 a streaming RL work. Call it an ordinary video RLVR framework and a training substrate that streaming RL systems may extend.
      claim_kind:: analyst_assessment

- ## Workflow Extraction
    - **Initial model:** Example config uses `Qwen/Qwen3-VL-8B-Instruct`.
    - **Initial data:** JSON/JSONL with video/image path, problem, answer, task type, and optional offline trajectory fields.
    - **Preprocessing:** Videos can be decoded offline into `.pt` cache artifacts.
    - **Rollout input:** Prompt tokens plus multimodal data, mapped by `problem_key`, `answer_key`, `image_key`, and `video_key`.
    - **Rollout output:** `n` sampled responses per prompt, with `responses`, `response_mask`, `input_ids = prompt + response`, `position_ids`, and `attention_mask`.
    - **Reward input:** Decoded response, ground truth, data type, problem type, problem text, and problem id.
    - **Trainer input:** A `DataProto` batch with rewards, old logprobs, reference logprobs, and advantages.
    - **Trainer update:** Default GRPO over multiple responses for the same prompt.
    - **Resource architecture:** Actor/Rollout/Reference colocated on one GPU pool; CPU reward workers; separate AsyncLLMEngine evaluation toolkit.
    - **Difference from streaming RL:** EasyVideoR1 rollout is problem-level. Streaming RL rollout is a causal time window that records when the model stayed silent, spoke, or waited for later events.

- ## Evidence Index
  collapsed:: true
    - **E1:** paper | title block and abstract | high
      locator:: `paper.md`, abstract
      note:: five contributions, 1.47x throughput, task-aware rewards, mixed offline-online data, joint image-video training, async evaluation, 32 H200 / 20h result.
    - **E2:** paper | Introduction | high
      locator:: `paper.md`, Section 1
      note:: explains video RL challenges: diverse rewards, repeated preprocessing, long contexts, and sensitive evaluation hyperparameters.
    - **E3:** repo | README features and performance | high
      locator:: `context/repos/EasyVideoR1/README.md:16-42`
      note:: optimization goals, reward support, supported models/algorithms, async eval, benchmark gains, 1.47x cache speedup.
    - **E4:** repo | minimal data format | high
      locator:: `context/repos/EasyVideoR1/README.md:75-102`
      note:: sample fields are problem, answer, videos, data_type, problem_type, options.
    - **E5:** repo | training config | high
      locator:: `context/repos/EasyVideoR1/examples/video_rl/video_rl.yaml:1-118`
      note:: mix-policy fields, prompt/answer/video keys, GRPO config, rollout `n`, reward path.
    - **E6:** code | vLLM rollout | high
      locator:: `context/repos/EasyVideoR1/verl/workers/rollout/vllm_rollout_spmd.py:209-398`
      note:: vLLM input construction, response sampling, prompt repetition for `n`, offline-output replacement.
    - **E7:** code | reward manager and reward function | high
      locator:: `context/repos/EasyVideoR1/verl/workers/reward/function.py:29-154`; `examples/video_rl/reward_function/video_reward.py:820-877`
      note:: reward input fields, final-token reward placement, default accuracy/format score.
    - **E8:** code | trainer loop | high
      locator:: `context/repos/EasyVideoR1/verl/trainer/ray_trainer.py:645-958`
      note:: rollout, balancing, async reward, old/ref logprob, advantage, actor update, validation/save.
    - **E9:** code | GRPO advantage | high
      locator:: `context/repos/EasyVideoR1/verl/trainer/core_algos.py:176-217`
      note:: group-normalized outcome reward, requires rollout.n > 1.
    - **E10:** code | video preprocessing cache | high
      locator:: `context/repos/EasyVideoR1/scripts/preprocess_videos.py:1-120`
      note:: offline decode, frame/metadata/sample_fps/preprocess_version artifact, hashed cache path.
    - **E11:** repo | eval toolkit | medium
      locator:: `context/repos/EasyVideoR1/eval/README.md:1-210`
      note:: AsyncLLMEngine eval, cache modes, open-ended judge, supported task types and benchmarks.
