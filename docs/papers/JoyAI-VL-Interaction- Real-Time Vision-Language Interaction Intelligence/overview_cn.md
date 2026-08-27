- **标题:** JoyAI-VL-Interaction: Real-Time Vision-Language Interaction Intelligence
- **一句话总结:** JoyAI-VL-Interaction 把流式视频助手训练成一个每秒做选择的交互模型：继续沉默、直接回答，或把复杂问题委托给后台模型，同时保持实时观看。
- **论文类型:** core streaming RL / 交互模型系统发布
- **发表:** arXiv v1, 2026-06-10
- **作者:** Dingyu Yao、Junhao Zhou、Chenxu Yang、Chuanyu Qin、Haowen Hou、Zheming Liang、Congcong Wang、Yuhang Cao、Shenglong Ye、Shuai Xie、Shuhuan Gu、Haoyang Huang、Qingyi Si、Nan Duan、Jiaqi Wang
- **单位:** JD.com
- **资源:** [Paper](https://arxiv.org/abs/2606.14777)；[GitHub](https://github.com/jd-opensource/JoyAI-VL-Interaction)；[HF model](https://huggingface.co/jdopensource/JoyAI-VL-Interaction-Preview)；[HF data](https://huggingface.co/datasets/jdopensource/JoyAI-VL-Interaction)
- **关键词:** streaming video interaction、interaction model、silence/response/delegate、answer-centered rollout、GRPO、AdaCodec、vLLM、background model

- ## Orientation
    - **背景:** 传统 VLM 更像问答系统：用户问一句，模型答一句。JoyAI 要做的是“模型持续看世界，并自己判断现在要不要说话”。
      claim_kind:: analyst_assessment
    - **通俗问题:** 比如监控画面着火、直播里出现用户想买的商品、智能眼镜看到路牌。用户可能来不及问，模型必须自己决定是否开口。
      claim_kind:: analyst_assessment
    - **核心做法:** 把实时交互变成每秒一个动作选择：`</silence>` 表示继续看，`</response>` 表示回答，`</delegation>` 表示把慢问题交给后台模型处理。
      evidence:: E3, E4
    - **为什么和 streaming RL 相关:** 它不是离线视频 QA，也不是只做推理加速；它明确用 SFT + GRPO 训练“何时说、何时等、何时委托”。
      evidence:: E6, E7

- ## Quick Reference
    - **最值得读的点:** 这是目前最完整的公开 streaming interaction stack 之一：论文同时给模型动作空间、训练数据格式、RL 训练方式、长时程 memory、vLLM serving 和开源入口。
      evidence:: E1, E2, E8
    - **Rollout 包含什么:** 一个 rollout 不是单独一秒，而是一段按时间展开的流式轨迹。轨迹里有视频前缀、用户 query、每秒动作、模型回答、沉默、后台委托请求、后台延迟结果，以及这些动作发生的时间。
      evidence:: E4, E5, E7
    - **Trainer 吃什么:** RL 阶段采用 answer-centered window sampling。也就是围绕某个 gold response 取一小段仍然保持因果顺序的轨迹，把几百个沉默 step 压缩成少数关键 turn，让 credit 更集中。
      evidence:: E7
    - **用什么算法更新:** 先做带权 SFT，降低连续沉默 token 的权重、提高 response onset 的权重；再用 GRPO 根据 timing、正确性、沉默、委托是否合理来优化。
      evidence:: E6, E7
    - **架构形态:** 前台 interaction model 每秒决策；后台 model/API/agent 只处理慢任务；ASR、TTS、memory、UI 都是可替换模块。论文重点是系统设计，没有给出 trainer-rollout 是否 colocate 或 fully async 的资源调度细节。
      evidence:: E8, E9
    - **开源状态:** GitHub、HF model、HF dataset 链接在 2026-07-02 可访问。论文声称完整系统和训练 recipe 开源，但完整训练复现还需要按 repo 逐项核验。
      claim_kind:: analyst_assessment
      evidence:: E1

- ## Argument Map
    - **问题:** turn-based 模型只能在用户发问后回答，不能在事件自然发生时主动行动。视频流里的关键时刻可能很短，错过就没了。
      evidence:: E2
    - **缺口:** 现有实时 omni 产品主要优化语音 turn-taking；消费级 video call 往往靠周期 polling；很多 streaming-video 工作只解决低延迟、memory 或主动输出中的一部分，没有完整可部署交互模型。
      evidence:: E2
    - **关键洞见:** “是否开口”不应该由外部阈值或定时器决定，而应该是模型自己的动作。沉默也要作为显式训练标签，不是默认状态。
      evidence:: E3, E4
    - **核心主张:** 用统一的每秒动作格式和流式轨迹训练，模型可以学到主动提醒、实时解说、时间感、计数、后台委托等交互能力。
      evidence:: E4, E5, E10

- ## Mechanism and Design
    - **动作空间:** 每秒模型从三类动作中选一个：沉默、回答、委托。委托时，模型先给用户一个简短占位回复，然后发出隐藏委托请求；后台结果回来后再被放回上下文。
      evidence:: E3, E5
    - **视频编码:** JoyAI 使用 AdaCodec，把变化不大的帧编码成更少 token，只在场景变化时使用完整视觉 token，目标是让长视频流的 token 增长更慢。
      evidence:: E3
    - **数据构造:** 数据超过 4M 个 time-aligned streaming clips，覆盖 proactive alerting、time-aligned QA、counting/perception、live commentary、multi-turn chat、delegation episodes。所有来源最后都转成统一的 per-second action format。
      evidence:: E4
    - **训练样本:** 训练样本长得像一段 chat trajectory：用户消息中带时间戳和当前帧，assistant 输出 `</silence>` 或 `</response> ...`，必要时还包含 `</delegation> ...`。
      evidence:: E5
    - **SFT:** 因为多数 step 都是沉默，普通交叉熵会把模型训得太保守。论文给不同控制 token 加权：连续沉默降权，回答起点升权。
      evidence:: E6
    - **RL:** GRPO 直接优化流式动作策略。reward 奖励正确且及时的回答、合理沉默、合理委托；惩罚误报、时机错、无脑回答、把简单问题乱委托、以及拿到后台结果后用不好。
      evidence:: E7
    - **Serving:** 运行时维护 session 状态、视频上下文、问答轨迹和 memory。memory 分短期原始视觉 token、中期文本摘要、长期压缩摘要，并围绕 prefix reuse 设计，便于 vLLM 复用 KV cache。
      evidence:: E8, E9

- ## Evaluation and Evidence
    - **实验形式:** 论文没有主要拿离线视频 benchmark 做核心卖点，而是在 6 类真实 streaming 场景中做人类偏好评测，对比 Doubao 和 Gemini 的 video-call assistants。
      evidence:: E10
    - **结果摘要:** 论文报告 JoyAI 在质量和时机上分别对 Doubao、Gemini 有明显偏好胜率，尤其在监控提醒、实时翻译、计数、定时提醒、直播解说、后台委托等场景更强。
      evidence:: E10
    - **需要谨慎的地方:** 评测规模仍偏早期，论文自己说明只有 6 个场景、58 个 human-rated cases；数据配比和清洗也还未到最终版本。
      evidence:: E11

- ## Technical Judgment
    - **最 solid 的结论:** 这篇工作证明了“streaming context 可以被组织成可训练的动作轨迹”，而且动作不只是回答，还包括沉默和后台委托。
      claim_kind:: analyst_assessment
    - **对我们最有用的点:** 它给了一个很清楚的样本边界：不是每秒一个独立样本，而是围绕有价值 response 的因果窗口。这个点可以直接支撑我们讲“streaming rollout sample 不是静态 prompt”。
      claim_kind:: analyst_assessment
    - **长尾在哪里:** 长尾不只来自长回答，还来自等待未来事件、背景模型延迟、长视频上下文维护、以及大量沉默 step。论文用 answer-centered window 降低训练 horizon，但没有系统讨论 rollout/trainer 资源调度。
      claim_kind:: analyst_assessment
      evidence:: E5, E7, E9
    - **局限:** 论文更像模型和系统发布，不是 RL infra 论文。它没有回答在 fully async RL 里如何处理 policy version、staleness、buffer admission、group consistency 或 elastic rollout/training 资源切换。
      claim_kind:: analyst_assessment
    - **一句话给项目:** JoyAI 说明 streaming RL 已经可以训起来；我们的空间不是证明“能不能训”，而是把它的流式轨迹、延迟结果、版本信息、reward-ready 边界和 trainer admission 做成更通用、更可审计的系统控制面。
      claim_kind:: analyst_assessment

- ## Workflow Extraction
    - **初始模型:** JoyAI-VL 1.0，基于 Qwen3-8B、Qwen3-VL ViT 和投影层训练。
    - **初始数据:** 常规 turn-based VL 数据 + time-aligned streaming interaction 数据。
    - **SFT 数据:** 每秒带时间戳的用户输入和 assistant 控制 token，覆盖沉默、回答、委托。
    - **RL rollout:** answer-centered streaming trajectory，保留因果顺序，只截取和回答时机相关的关键 turns。
    - **Reward:** timing、correctness、silence appropriateness、delegation quality、false alarm penalty、mistimed response penalty、LLM judge content score。
    - **Trainer 更新:** GRPO，论文说基于 EasyVideoR1 扩展 streaming interaction reward pipeline。
    - **部署架构:** vLLM serving + hierarchical memory + foreground real-time loop + background async loop。

- ## Glossary
  collapsed:: true
    - interaction model: 能自己决定什么时候开口的模型，而不是只能等用户问。
    - background model: 后台慢模型、API 或 agent，用来处理前台模型不适合实时完成的复杂任务。
    - delegation: 前台模型把任务交给后台模型，并在后台返回后继续整合结果。
    - answer-centered window: 围绕一个有价值回答截取的短流式轨迹，用来避免训练时展开几百个沉默 step。
    - AdaCodec: 一种视频 token 压缩方式，变化小的帧用少量预测 token 表示。
    - prefix reuse: 让 serving engine 复用已经算过的上下文 KV cache，减少每秒重复 prefill。

- ## Evidence Index
  collapsed:: true
    - **E1:** metadata | title block and abstract | high
      locator:: title block; arXiv header; project/repository/release lines
      note:: arXiv v1 date, JD.com authorship, project page, GitHub, release statement.
    - **E2:** problem | Introduction and Related Work | high
      locator:: Section 1; Section 2
      note:: contrasts turn-based models, polling-based products, real-time omni models, and streaming-video research.
    - **E3:** model | Model overview and Section 3.1 | high
      locator:: Section 3; Figure 2
      note:: per-second speak/silence/delegate actions, JoyAI-VL 1.0 initialization, AdaCodec video encoding.
    - **E4:** data | Data Construction for VL-Interaction | high
      locator:: Section 3.2
      note:: 4M+ time-aligned clips, six data families, unified per-second action format.
    - **E5:** sample | Training Data Example | high
      locator:: Appendix 7.1
      note:: examples show timestamped user frames followed by assistant silence, response, or delegation outputs.
    - **E6:** sft | Training objective | high
      locator:: Section 3.3
      note:: weighted SFT down-weights repeated silence and up-weights response onset.
    - **E7:** rl | Reinforcement learning | high
      locator:: Section 3.3
      note:: GRPO with answer-centered window sampling and stream-level rewards.
    - **E8:** system | Long-Horizon Memory | high
      locator:: Section 4.3
      note:: short-term raw visual tokens, mid-term summaries, long-term compressed blocks, dialogue memory.
    - **E9:** serving | Serving and Runtime | high
      locator:: Section 4.4
      note:: vLLM-native serving, prefix reuse, stateful sessions, stale-frame drop/backfill behavior.
    - **E10:** evaluation | Experiments | medium
      locator:: Section 5
      note:: human preference evaluation across six real-world streaming scenarios.
    - **E11:** limitation | Discussion near end of experiments | medium
      locator:: Section 5
      note:: paper states the data mixture, cleaning, and evaluation are still early stage.
