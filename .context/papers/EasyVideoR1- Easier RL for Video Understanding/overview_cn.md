- **标题:** EasyVideoR1: Easier RL for Video Understanding
- **一句话总结:** EasyVideoR1 是一个面向普通视频理解任务的 RLVR 训练框架，把视频预处理缓存、vLLM rollout、任务路由 reward、FSDP/GRPO 训练和异步评测串起来；它可以作为 JoyAI 的 RL 底座，但它本身不是 streaming interaction / streaming context RL 工作。
- **论文类型:** adjacent video RLVR framework / 非 core streaming RL
- **发表:** arXiv / GitHub report, 2026
- **作者:** Chuanyu Qin、Chenxu Yang、Qingyi Si、Naibin Gu、Dingyu Yao、Zheng Lin、Peng Fu、Nan Duan、Jiaqi Wang
- **单位:** Institute of Information Engineering, Chinese Academy of Sciences；University of Chinese Academy of Sciences；JD.COM
- **资源:** [Paper](https://arxiv.org/abs/2604.16893)；[GitHub](https://github.com/cyuQ1n/EasyVideoR1)；本地代码 `context/repos/EasyVideoR1`
- **关键词:** video RLVR、GRPO、vLLM rollout、FSDP、video tensor cache、task-aware reward、mix-policy、AsyncLLMEngine eval

- ## Orientation
    - **背景:** 文本 RLVR 已经比较成熟，但视频 RL 更麻烦：视频要解码、采帧、resize，输入 token 很长；任务类型也多，包括选择题、开放问答、时序定位、时空定位等。
      evidence:: E1, E2
    - **它解决的问题:** 让研究者更容易跑普通视频理解 RL。也就是给定一个视频/图片问题，让模型生成答案，用规则或 judge 打分，再用 GRPO/PPO 类算法更新。
      evidence:: E3, E4, E8
    - **它不解决的问题:** 它没有定义连续视频流里的每秒动作、沉默、何时开口、旧动作写回未来上下文、延迟 reward、policy version 或 stale rollout。那些是 JoyAI / streaming RL 才关心的语义。
      claim_kind:: analyst_assessment
    - **为什么仍然要读:** JoyAI 论文说 RL 阶段基于 EasyVideoR1 扩展。对我们来说，它是一个很好的“视频 RL 训练底座”参照，可以看普通 video RLVR 的 rollout、reward、trainer、eval 是怎么组织的。
      evidence:: E5, E8

- ## Quick Reference
    - **最值得读的点:** 这不是一篇提出新 streaming 算法的论文，而是把 video RL 训练流程工程化：缓存视频 tensor、减少重复解码、统一 reward 接口、用 vLLM 做 rollout、用 FSDP 做训练。
      evidence:: E1, E3, E10
    - **Rollout 包含什么:** 输入是一条普通样本：`problem`、`answer`、`videos/images`、`data_type`、`problem_type`。rollout engine 把 prompt token 和多模态数据送进 vLLM，对同一个 prompt 采样 `n` 个回答。
      evidence:: E4, E5, E6
    - **Trainer 吃什么:** trainer 吃的是 `prompt + response` 序列、response mask、reward tensor、old logprobs、ref logprobs、advantage 等。reward 通常只放在回答最后一个有效 token 上。
      evidence:: E7, E8, E9
    - **用什么算法更新:** 默认配置使用 GRPO：同一个问题生成多个回答，在组内比较分数，分数高的回答增加概率，分数低的回答降低概率。代码也继承了 DAPO、GSPO、ReMax、RLOO、GDPO 等算法入口。
      evidence:: E5, E9
    - **架构形态:** 这是 colocated / hybrid-engine 风格：Actor、vLLM Rollout、Reference 在同一批 GPU 上轮换使用。先加载 vLLM 生成，再释放 vLLM，随后 FSDP 计算 logprob 和更新模型。不是 fully async rollout-training 架构。
      evidence:: E8
    - **送到训练的样本是什么:** 一条训练样本本质上是“一个视频/图片问题 + 模型回答 + 规则 reward”。它不是“连续视频流里某个时间点的可见状态 + 动作 + 后续事件反馈”。
      claim_kind:: analyst_assessment
      evidence:: E4, E6, E7
    - **代码状态:** GitHub repo 有训练入口、配置、reward、视频预处理、eval 工具和 report。模型权重、训练数据和 benchmark 视频没有下载到本地。
      evidence:: E3, E5, E10, E11

- ## Argument Map
    - **问题:** 现有 RL 框架大多先服务文本或图片。视频任务会重复做解码、采帧和视觉预处理，导致 rollout、logprob、eval 都慢。
      evidence:: E2
    - **缺口:** 普通视频理解任务类型很多，reward 不能只有一个选择题 exact match；评测也很敏感，采帧、fps、分辨率、token budget、prompt template 都会影响结果。
      evidence:: E1, E2
    - **核心思路:** 把视频预处理从训练 loop 里拿出来，先离线解码成 `.pt` tensor cache；训练时直接读 cache。再把不同任务的 reward 统一路由，把 image/video 混合训练和 offline-online 混合数据接进同一个 pipeline。
      evidence:: E1, E10
    - **主张:** 如果把这些视频相关工程补齐，普通 video RLVR 会更快、更容易复现，也能在多个视频理解 benchmark 上稳定提升。
      evidence:: E1, E3, E11

- ## Mechanism and Design
    - **数据格式:** 最小样本就是 `problem`、`answer`、`videos`、`data_type`、`problem_type`。多选题再加 `options`。这说明 EasyVideoR1 的样本边界是“题目级”，不是“流式时间点级”。
      evidence:: E4
    - **视频缓存:** `scripts/preprocess_videos.py` 会离线处理视频，保存 `frames`、`metadata`、`sample_fps`、`preprocess_version` 到 `.pt` 文件。训练数据里再记录 `preprocessed_video`，训练时优先复用。
      evidence:: E10
    - **Rollout:** `generate_sequences()` 从 batch 里取 `raw_prompt_ids` 和 `multi_modal_data`，构造 vLLM 输入，调用 `generate`，得到多个 response token，然后拼成完整的 `prompt + response`。
      evidence:: E6
    - **Mix-policy:** 如果样本带 `has_offline_trajectory` 和 `offline_output`，框架可以让同一组里包含 `n-1` 个在线生成和 1 个离线轨迹。这对我们有启发：离线 trace / teacher trace 可以作为一类候选 rollout 混入训练。
      evidence:: E5, E6, E8
    - **Reward:** reward manager 把生成结果 decode 成文本，再把 `response`、`ground_truth`、`data_type`、`problem_type`、`problem`、`problem_id` 交给自定义 reward function。`video_reward.py` 默认用 `accuracy * 0.9 + format * 0.1`。
      evidence:: E7
    - **GRPO:** GRPO 先把每个 response 的 token reward 求和，再按同一个问题的 `index` 分组，组内做均值/方差归一化。代码里明确要求 `rollout.n > 1`。
      evidence:: E9
    - **训练 loop:** 每个 step 是：准备 rollout engine -> 生成 batch -> 释放 rollout engine -> token 长度均衡 -> 异步算 reward -> 重算 old logprobs -> 算 ref logprobs -> 算 advantage -> update actor -> eval/save。
      evidence:: E8
    - **评测:** eval 使用 vLLM `AsyncLLMEngine`，支持视频 cache、异步排队、open-ended LLM judge 和 22+ 视频理解 benchmark。
      evidence:: E11

- ## Evaluation and Evidence
    - **效率结果:** README/report 声称离线视频缓存让 rollout generation 加速约 1.5x、log-probability computation 加速约 2.9x，整体 wall-clock / token throughput 提升约 1.47x。
      evidence:: E1, E3
    - **效果结果:** README/report 声称用 EasyVideoR1 训练 Qwen3-VL-8B-Instruct 后，在 10 个视频理解 benchmark 上平均提升 +2.3%；report 还提到 32 张 H200 约 20 小时训练。
      evidence:: E1, E3
    - **评测范围:** eval 工具覆盖 LVBench、Video-MME、MVBench、MLVU、VideoMMMU、Charades-STA、STVG 等 22+ benchmark，并给出不同 task type 的 scoring 方式。
      evidence:: E11
    - **需要谨慎:** 这些结果证明的是普通 video RLVR pipeline 的效率和可用性，不证明 streaming interaction RL 的样本边界、staleness、旧动作污染 context 或 fully async 调度问题已经解决。
      claim_kind:: analyst_assessment

- ## Technical Judgment
    - **最 solid 的结论:** EasyVideoR1 把“视频作为 RL 输入”这件事做得比较完整：视频缓存、任务 reward、vLLM rollout、FSDP 训练、异步评测都有明确代码入口。
      claim_kind:: analyst_assessment
    - **对我们最有用的点:** 它给了普通 video RLVR 的清晰基线：如果只是静态视频问题，那么样本就是 `video + question + answer + reward`；如果我们做 streaming RL，就必须额外说明为什么这个样本定义不够。
      claim_kind:: analyst_assessment
    - **和 JoyAI 的关系:** JoyAI 可以在这个底座上扩展 streaming interaction reward pipeline，但 JoyAI 需要自己定义每秒动作、沉默、委托、answer-centered window、延迟结果和 timing reward。EasyVideoR1 本身不提供这些语义。
      claim_kind:: analyst_assessment
    - **对 streaming infra 的启发:** 视频 tensor cache 很重要，但 streaming 场景不能简单把整段视频离线 cache 后当一个 prompt。更接近的做法是维护可复用的视频 chunk / KV / metadata，并在有价值动作出现时把相关窗口打包成训练样本。
      claim_kind:: analyst_assessment
    - **不该怎么引用:** 不要说 EasyVideoR1 是 streaming RL 工作；更准确的说法是：它是普通 video RLVR 的开源训练框架，也是 JoyAI 这类 streaming RL 工作可能复用或扩展的训练底座。
      claim_kind:: analyst_assessment

- ## Workflow Extraction
    - **初始模型:** 示例配置使用 `Qwen/Qwen3-VL-8B-Instruct`。
    - **初始数据:** JSON/JSONL，每条包含视频/图片路径、问题、标准答案、任务类型；可选离线轨迹字段。
    - **训练前处理:** 视频可先离线解码成 `.pt` cache，减少训练时重复 decode / resize。
    - **Rollout 输入:** prompt token + 多模态数据；数据字段来自 `problem_key`、`answer_key`、`image_key`、`video_key`。
    - **Rollout 输出:** 对每个 prompt 采样 `n` 个 response，得到 `responses`、`response_mask`、`input_ids = prompt + response`、`position_ids`、`attention_mask`。
    - **Reward 输入:** decode 后的 response、ground truth、data type、problem type、problem text、problem id。
    - **Trainer 输入:** 带 reward、old logprob、ref logprob、advantage 的 `DataProto` batch。
    - **Trainer 更新:** 默认 GRPO；同一 prompt 的多个 response 构成 group，组内相对打分。
    - **资源架构:** Actor / Rollout / Ref colocate，同一批 GPU 分时运行；reward worker 在 CPU；eval 另有 AsyncLLMEngine 工具链。
    - **和 streaming RL 的差异:** EasyVideoR1 的 rollout 是题目级；streaming RL 的 rollout 更像一段因果时间窗口，里面要记录模型在什么时候沉默、什么时候说话、什么时候等未来事件。

- ## Glossary
  collapsed:: true
    - video RLVR: 用可验证 reward 训练视频理解模型，比如答案对不对、定位区间是否重合。
    - rollout: 模型自己生成回答的过程；在 EasyVideoR1 里主要是 vLLM 对 prompt 采样多个 response。
    - GRPO: 同一个问题生成多个回答，组内比较 reward 来更新模型，不需要单独 critic。
    - FSDP: 把模型参数切分到多张 GPU 上训练。
    - vLLM: 高效推理/生成引擎，用来做 rollout。
    - mix-policy: 同一组训练样本里混合在线生成和已有离线轨迹。
    - AsyncLLMEngine: vLLM 的异步推理接口，用于高吞吐评测。

- ## Evidence Index
  collapsed:: true
    - **E1:** paper | title block and abstract | high
      locator:: `paper.md`, abstract
      note:: states EasyVideoR1's five contributions: full video RL pipeline, 1.47x throughput, task-aware reward, mixed offline-online data, joint image-video training, async evaluation, 32 H200 / 20h result.
    - **E2:** paper | Introduction | high
      locator:: `paper.md`, Section 1
      note:: explains video RL challenges: diverse rewards, repeated video preprocessing, long contexts, sensitive evaluation hyperparameters.
    - **E3:** repo | README features and performance | high
      locator:: `context/repos/EasyVideoR1/README.md:16-42`
      note:: states optimization goals, task-aware reward, supported models/algorithms, async eval, benchmark gains, 1.47x cache speedup.
    - **E4:** repo | minimal data format | high
      locator:: `context/repos/EasyVideoR1/README.md:75-102`
      note:: sample fields are problem, answer, videos, data_type, problem_type, options.
    - **E5:** repo | training config | high
      locator:: `context/repos/EasyVideoR1/examples/video_rl/video_rl.yaml:1-118`
      note:: defines mix-policy data fields, prompt/answer/video keys, GRPO config, rollout `n`, reward function path.
    - **E6:** code | vLLM rollout | high
      locator:: `context/repos/EasyVideoR1/verl/workers/rollout/vllm_rollout_spmd.py:209-398`
      note:: builds vLLM inputs from prompt token ids and multimodal data, samples responses, repeats prompts for `n`, and optionally replaces one response with offline output.
    - **E7:** code | reward manager and reward function | high
      locator:: `context/repos/EasyVideoR1/verl/workers/reward/function.py:29-154`; `examples/video_rl/reward_function/video_reward.py:820-877`
      note:: reward input fields and final-token reward placement; default video reward combines accuracy and format.
    - **E8:** code | trainer loop | high
      locator:: `context/repos/EasyVideoR1/verl/trainer/ray_trainer.py:645-958`
      note:: rollout, batch balancing, async reward, old/ref logprob, advantage, actor update, validation/save.
    - **E9:** code | GRPO advantage | high
      locator:: `context/repos/EasyVideoR1/verl/trainer/core_algos.py:176-217`
      note:: sums token rewards, groups by index, normalizes by group mean/std, requires rollout.n > 1.
    - **E10:** code | video preprocessing cache | high
      locator:: `context/repos/EasyVideoR1/scripts/preprocess_videos.py:1-120`
      note:: offline decode, frame/metadata/sample_fps/preprocess_version artifact, hashed cache path.
    - **E11:** repo | eval toolkit | medium
      locator:: `context/repos/EasyVideoR1/eval/README.md:1-210`
      note:: AsyncLLMEngine eval, video cache, open-ended judge, supported task types and benchmarks.
