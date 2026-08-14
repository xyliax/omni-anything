- **Title:** EasyVideoR1: Easier RL for Video Understanding
  **标题:** EasyVideoR1: Easier RL for Video Understanding
- **Summary:** EasyVideoR1 connects video tensor caching, vLLM rollout, task-aware reward, FSDP/GRPO training, and asynchronous evaluation for ordinary video-understanding RLVR.
  **一句话总结:** EasyVideoR1 把视频预处理缓存、vLLM rollout、任务路由 reward、FSDP/GRPO 训练和异步评测串起来，服务的是普通视频理解 RLVR。
- **Paper Type:** adjacent video RLVR framework / not core streaming RL
  **论文类型:** 邻近的视频 RLVR 框架 / 不是 core streaming RL
- **Venue:** arXiv / GitHub report, 2026
  **发表:** arXiv / GitHub report, 2026
- **Authors:** Chuanyu Qin, Chenxu Yang, Qingyi Si, Naibin Gu, Dingyu Yao, Zheng Lin, Peng Fu, Nan Duan, Jiaqi Wang
  **作者:** Chuanyu Qin、Chenxu Yang、Qingyi Si、Naibin Gu、Dingyu Yao、Zheng Lin、Peng Fu、Nan Duan、Jiaqi Wang
- **Resources:** [Paper](https://arxiv.org/abs/2604.16893); [GitHub](https://github.com/cyuQ1n/EasyVideoR1); local clone `context/repos/EasyVideoR1`
  **资源:** [Paper](https://arxiv.org/abs/2604.16893)；[GitHub](https://github.com/cyuQ1n/EasyVideoR1)；本地代码 `context/repos/EasyVideoR1`

- ## Orientation
    - **English:** EasyVideoR1 addresses the engineering gap between text/image RL frameworks and video RL: video inputs are expensive to decode and preprocess, reward types are diverse, and evaluation is sensitive to many hyperparameters.
      **中文:** EasyVideoR1 解决的是普通 RL 框架迁移到视频时的工程缺口：视频解码和预处理贵，reward 类型多，评测又对采帧、fps、分辨率和 prompt 很敏感。
      evidence:: E1, E2
    - **English:** It should be read as a video RLVR training substrate, not as a streaming interaction method.
      **中文:** 它应该被读作视频 RLVR 训练底座，而不是 streaming interaction 方法。
      claim_kind:: analyst_assessment
    - **English:** This distinction matters because JoyAI may extend EasyVideoR1, but JoyAI has to define the streaming semantics itself: per-second actions, silence, delegation, delayed results, and timing reward.
      **中文:** 这个区分很重要：JoyAI 可以基于 EasyVideoR1 扩展，但每秒动作、沉默、委托、延迟结果和 timing reward 是 JoyAI 自己定义的，不是 EasyVideoR1 原生提供的。
      claim_kind:: analyst_assessment

- ## Quick Reference
    - **English:** Rollout input is a problem-level sample: `problem`, `answer`, `videos/images`, `data_type`, and `problem_type`.
      **中文:** rollout 输入是题目级样本：`problem`、`answer`、`videos/images`、`data_type`、`problem_type`。
      evidence:: E4, E5
    - **English:** Rollout output is `n` sampled responses per prompt, produced by vLLM and packed with masks and position ids.
      **中文:** rollout 输出是同一个 prompt 的 `n` 个采样回答，由 vLLM 生成，并带上 mask 和 position id。
      evidence:: E6
    - **English:** Trainer input is a `DataProto` batch with `prompt + response`, response mask, reward, old logprobs, reference logprobs, and advantages.
      **中文:** trainer 输入是带有 `prompt + response`、response mask、reward、old logprobs、reference logprobs 和 advantage 的 `DataProto` batch。
      evidence:: E7, E8
    - **English:** Default update is GRPO: multiple responses for the same prompt are compared within a group.
      **中文:** 默认更新是 GRPO：同一个 prompt 的多个回答在组内比较分数。
      evidence:: E5, E9
    - **English:** The architecture is colocated: Actor, vLLM Rollout, and Reference share one GPU pool and run in phases. It is not fully async rollout-training.
      **中文:** 架构是 colocated：Actor、vLLM Rollout、Reference 共用一批 GPU，分阶段运行。它不是 fully async rollout-training。
      evidence:: E8

- ## Mechanism and Design
    - **English:** The most important systems idea is offline video cache. Videos are decoded, sampled, resized, and saved as `.pt` tensor artifacts before training.
      **中文:** 最重要的系统点是离线视频缓存。视频在训练前先解码、采帧、resize，并保存成 `.pt` tensor。
      evidence:: E10
    - **English:** The reward path is task-aware. The reward manager decodes the generated response and calls a configurable reward function with ground truth and task metadata.
      **中文:** reward 路径是按任务路由的。reward manager 会 decode 模型回答，再把标准答案和任务元数据交给可配置 reward function。
      evidence:: E7
    - **English:** Mix-policy allows a group to mix online generations with one pre-collected offline trajectory when the sample provides `offline_output`.
      **中文:** mix-policy 允许同一组里混合在线生成和一条预采集离线轨迹，只要样本提供 `offline_output`。
      evidence:: E5, E6
    - **English:** The training loop prepares vLLM rollout, generates a batch, releases rollout memory, balances token lengths, computes reward asynchronously, computes old/ref logprobs, computes advantages, and updates the actor.
      **中文:** 训练 loop 会先准备 vLLM rollout、生成 batch、释放 rollout 显存、按 token 长度均衡、异步算 reward、算 old/ref logprobs、算 advantage，再更新 actor。
      evidence:: E8

- ## Technical Judgment
    - **English:** EasyVideoR1 is a strong baseline for ordinary video RLVR. If a task is static VideoQA, its sample object is enough: video plus question plus generated answer plus reward.
      **中文:** EasyVideoR1 是普通 video RLVR 的强基线。如果任务是静态 VideoQA，它的样本对象就够了：视频、问题、模型回答、reward。
      claim_kind:: analyst_assessment
    - **English:** For streaming RL, the same object is not enough because the model's action timing, silence, delayed evidence, and visible context at decision time must be tracked.
      **中文:** 对 streaming RL 来说，这个对象不够，因为模型动作发生的时间、沉默、延迟证据、以及决策时真正可见的上下文都要被记录。
      claim_kind:: analyst_assessment
    - **English:** The safest citation is: EasyVideoR1 is an open video RLVR framework and a training substrate that JoyAI-like streaming systems can extend.
      **中文:** 最稳的引用方式是：EasyVideoR1 是开源 video RLVR 框架，也是 JoyAI 这类 streaming 系统可以扩展的训练底座。
      claim_kind:: analyst_assessment

- ## Workflow Extraction
    - **English:** Initial model: example config uses `Qwen/Qwen3-VL-8B-Instruct`.
      **中文:** 初始模型：示例配置使用 `Qwen/Qwen3-VL-8B-Instruct`。
    - **English:** Initial data: JSON/JSONL with video/image paths, problem, answer, task type, and optional offline trajectory fields.
      **中文:** 初始数据：JSON/JSONL，包含视频/图片路径、问题、答案、任务类型，以及可选离线轨迹字段。
    - **English:** Rollout: vLLM samples `n` responses per prompt.
      **中文:** Rollout：vLLM 对每个 prompt 采样 `n` 个回答。
    - **English:** Reward: custom reward functions score decoded responses using ground truth and task metadata.
      **中文:** Reward：自定义 reward function 根据标准答案和任务元数据给回答打分。
    - **English:** Training: GRPO groups responses by prompt and updates the actor through FSDP.
      **中文:** Training：GRPO 按 prompt 分组比较回答，并通过 FSDP 更新 actor。
    - **English:** Resource mode: Actor/Rollout/Reference colocated; CPU reward workers; separate async eval toolkit.
      **中文:** 资源模式：Actor/Rollout/Reference colocate；reward worker 在 CPU；eval 有单独异步工具链。

- ## Evidence Index
  collapsed:: true
    - **E1:** paper | abstract | high
      locator:: `paper.md`, abstract
      note:: contribution list, throughput, reward system, mixed offline-online data, joint image-video training, async evaluation.
    - **E2:** paper | Introduction | high
      locator:: `paper.md`, Section 1
      note:: video-specific RL challenges.
    - **E3:** repo | README features | high
      locator:: `context/repos/EasyVideoR1/README.md:16-42`
      note:: speedup and feature claims.
    - **E4:** repo | data format | high
      locator:: `context/repos/EasyVideoR1/README.md:75-102`
      note:: minimal sample schema.
    - **E5:** repo | config | high
      locator:: `context/repos/EasyVideoR1/examples/video_rl/video_rl.yaml:1-118`
      note:: GRPO, rollout n, mix-policy, reward function.
    - **E6:** code | rollout | high
      locator:: `context/repos/EasyVideoR1/verl/workers/rollout/vllm_rollout_spmd.py:209-398`
      note:: vLLM rollout and offline trajectory mixing.
    - **E7:** code | reward | high
      locator:: `context/repos/EasyVideoR1/verl/workers/reward/function.py:29-154`; `examples/video_rl/reward_function/video_reward.py:820-877`
      note:: reward input and scoring.
    - **E8:** code | training loop | high
      locator:: `context/repos/EasyVideoR1/verl/trainer/ray_trainer.py:645-958`
      note:: rollout, reward, logprob, advantage, actor update.
    - **E9:** code | GRPO | high
      locator:: `context/repos/EasyVideoR1/verl/trainer/core_algos.py:176-217`
      note:: group-normalized outcome advantage.
    - **E10:** code | preprocessing | high
      locator:: `context/repos/EasyVideoR1/scripts/preprocess_videos.py:1-120`
      note:: offline video tensor cache.
