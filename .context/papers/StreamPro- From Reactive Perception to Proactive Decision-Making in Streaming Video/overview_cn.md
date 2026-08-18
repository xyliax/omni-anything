- **标题:** StreamPro: From Reactive Perception to Proactive Decision-Making in Streaming Video
- **一句话总结:** StreamPro 把 proactive streaming video 明确看成“只能看到过去和现在时，什么时候该回答”的决策问题，并用 SFT + GRPO 训练模型同时优化回答内容和回答时机。
- **论文类型:** core streaming RL / benchmark + training framework
- **发表:** arXiv v1, 2026-05-11
- **作者:** Ao Li、Zihan Xiao、Zihao Yue、Boshen Xu、Linli Yao、Jiaze Li、Pei Fu、Jianzhong Ju、Jian Luan、Qin Jin
- **单位:** AIM3 Lab, Renmin University of China；MiLM Plus, Xiaomi Inc.；Peking University
- **资源:** [Paper](https://arxiv.org/abs/2605.16381)；官方 GitHub/HF model/HF dataset 在 2026-07-02 暂未找到
- **关键词:** proactive streaming video、partial observation、CB-Stream Loss、GRPO、turn-level reward、trajectory-level reward、StreamPro-Bench

- ## Orientation
    - **背景:** 很多 streaming video 任务其实只是“看到证据以后回答”，模型不用真正提前判断。StreamPro 认为这不够，真正的 proactive assistant 要在信息还不完整时做及时决策。
      evidence:: E2
    - **通俗问题:** 如果用户让模型“指导我做蛋糕”或“提前提醒盲人前方风险”，模型不能等所有事情发生完再总结，而要根据当前进展给下一步建议或提前预警。
      claim_kind:: analyst_assessment
      evidence:: E3
    - **核心做法:** 先构造 StreamPro-Bench 和 StreamPro-SFT/RL 数据，再用 CB-Stream Loss 做 SFT，最后用 GRPO 加多粒度 reward 优化整段流式轨迹。
      evidence:: E4, E5, E6
    - **为什么和 streaming RL 相关:** 它明确训练模型输出 `</Silence>` 或 `</Response>`，并用 trajectory-level reward 评价整条流式回答序列，而不是只评价单个答案。
      evidence:: E5, E6

- ## Quick Reference
    - **最值得读的点:** 这篇的价值在于把 proactive streaming 从“晚点回答”推进到“部分可见下的决策”。它直接解释为什么 streaming RL 的 sample 应该是一段轨迹，而不是每一秒独立拆开。
      claim_kind:: analyst_assessment
      evidence:: E2, E6
    - **Rollout 包含什么:** 一条 rollout 是长度为 K 的 streaming trajectory。每个 time step 模型看当前已到达的视频上下文，然后输出 `</Silence>` 或 `</Response>` 加文本。
      evidence:: E5, E6
    - **Trainer 吃什么:** SFT 阶段吃带沉默/回答标签的流式样本；RL 阶段只用 proactive 任务数据 StreamPro-RL-3K，训练时对同一轨迹生成候选输出并根据多粒度 reward 做 GRPO。
      evidence:: E7
    - **Reward 怎么算:** reward 由三部分组成：format reward 保证输出格式；turn-level F1 reward 同时看每次回应的时机和语义；trajectory-level rubric reward 用 LLM evaluator 检查整条轨迹的粒度、顺序、覆盖度和幻觉。
      evidence:: E6
    - **模型和资源:** 论文报告 3B/4B 实验，公开论文里没有找到官方代码或公开模型/数据入口。它更适合作为流程和 reward 设计参考，不能当成可复现开源栈。
      claim_kind:: analyst_assessment
      evidence:: E1

- ## Argument Map
    - **问题:** 传统 streaming benchmark 往往让模型在证据出现后回答，因此测到的是 delayed perception，而不是提前规划或预警。
      evidence:: E2
    - **关键难点:** 流式轨迹里大多数时刻都应该沉默，少数时刻才需要回答。普通 SFT 会被沉默样本主导，把模型训得过于保守。
      evidence:: E2, E5
    - **第二个难点:** proactive 行为不是“答案对不对”一个目标，还包括“早不早、准不准、有没有乱说、整条轨迹顺不顺”。
      evidence:: E6
    - **核心主张:** 用 class-balanced streaming loss 解决 SFT 的 silence/response imbalance，再用 turn-level + trajectory-level rewards 做 GRPO，可以显著提升 proactive streaming performance。
      evidence:: E5, E6, E8

- ## Mechanism and Design
    - **Benchmark:** StreamPro-Bench 有 577 个视频、1285 个 QA，分成三类能力：Perception Understanding、Temporal Reasoning、Proactive Agency。
      evidence:: E3
    - **任务:** 7 个任务包括 Event Understanding、Object Understanding、Anomaly Alert、Temporal Perception、Temporal Grounding、Goal Planning、Risk Forecasting。
      evidence:: E3
    - **Proactive Agency:** Goal Planning 要在前一步完成时及时给下一步；Risk Forecasting 要在风险出现前约 3 秒预警。
      evidence:: E3, E11
    - **SFT 形式:** 每个时间步输出一个控制 token：`</Silence>` 或 `</Response>`。CB-Stream Loss 根据 batch 内决策 token 的有效样本数做 reweight，缓解沉默压倒回答的问题。
      evidence:: E5
    - **RL 形式:** GRPO 对完整 generated trajectory 评分。论文没有把每秒拆成独立 RL sample，而是把一整段输出序列作为 reward 对象。
      evidence:: E6
    - **Training data:** SFT 使用 TimeChat-Online-139K、VideoChat-Flash-3K、StreamPro-SFT-63K 和过滤后的 Streamo-Instruct-465K；RL 只关注 proactive tasks，使用 StreamPro-RL-3K。
      evidence:: E7
    - **数据构造:** benchmark 数据通过视频过滤、caption/QA 生成、多阶段验证和人工 review 构建；Risk Forecasting 完全依赖人工标注和复核。
      evidence:: E10, E11

- ## Evaluation and Evidence
    - **主结果:** StreamPro-GRPO-4B 在 StreamPro-Bench 上报告 W-Avg 41.5，显著超过论文列出的 open-source proactive baselines；在 StreamingBench-RTVU 上也保持较强结果。
      evidence:: E8, E9
    - **消融:** CB-Stream Loss 比普通 CE 和 focal loss 更好；RL 里更大的时间容忍窗口可以让 reward 更密；trajectory-level reward 和 turn-level reward 平衡时效果最好。
      evidence:: E12
    - **代价:** RL 阶段只优化 proactive data，所以某些 real-time streaming 或 offline 结果会有轻微下降，论文也明确报告了这个 trade-off。
      evidence:: E9

- ## Technical Judgment
    - **最 solid 的结论:** StreamPro 最清楚地说明，streaming RL 的训练对象应该是“时间展开的回答轨迹”，因为单个 turn 的 reward 无法评价整段交互是否顺、是否漏、是否过碎。
      claim_kind:: analyst_assessment
      evidence:: E6
    - **对我们最有用的点:** 它给我们的 slides 一个简单说法：streaming context 进入 RL 后，不只是 prompt 变长，而是样本从静态 QA 变成“带时间、沉默、回答、顺序和未来风险的轨迹”。
      claim_kind:: analyst_assessment
    - **长尾在哪里:** 长尾来自等待证据、等待上一步完成、提前风险预警窗口、以及大量沉默 step。它用 loss/reward 解决训练信号问题，但没有解决 rollout 侧的资源调度和 staleness。
      claim_kind:: analyst_assessment
    - **局限:** 论文没有 dedicated memory mechanism，只用 sliding-window 缓解 latency/GPU memory；只覆盖 video+text，没有 omni audio；官方代码和数据入口暂未找到。
      evidence:: E13
    - **一句话给项目:** StreamPro 说明最新工作已经开始用 GRPO 训练 proactive streaming 行为，但样本边界、版本追踪、reward-ready、buffer admission 和训练系统接口仍然是各做各的。
      claim_kind:: analyst_assessment

- ## Workflow Extraction
    - **初始数据:** 429K open-source data + StreamPro-SFT-63K；SFT 还混入 TimeChat-Online、VideoChat-Flash 和 Streamo-Instruct 过滤样本。
    - **SFT 样本:** 流式视频上下文 + 每个时间步的 `</Silence>` / `</Response>` 控制 token 和回答文本。
    - **RL 数据:** StreamPro-RL-3K，只包含 proactive tasks，不包含 Risk Forecasting。
    - **Rollout 样本:** 长度为 K 的 generated trajectory，包含每一步是否沉默、是否回答、回答内容、预测时间。
    - **Reward:** format reward + turn-level F1 reward + trajectory-level rubric reward。
    - **更新算法:** GRPO。
    - **架构:** 论文主要讲训练 framework，没有公开说明 colocate / fully async / rollout service 等系统架构。

- ## Glossary
  collapsed:: true
    - Proactive Agency: 在信息不完整时也能及时做合理决策，例如提前提醒风险或给下一步指导。
    - delayed perception: 等证据完全出现后才回答，本质上还是反应式感知。
    - CB-Stream Loss: 一种给沉默/回答控制 token 重新加权的 SFT loss，用来避免模型过度沉默。
    - turn-level reward: 评价单次回答的时机和内容。
    - trajectory-level reward: 评价整条流式回答序列是否连贯、覆盖关键点、顺序正确、没有明显幻觉。
    - StreamPro-F1: 同时考虑时间对齐和语义正确性的 proactive 评测指标。

- ## Evidence Index
  collapsed:: true
    - **E1:** metadata | title block and abstract | high
      locator:: title block; arXiv header
      note:: arXiv v1 date, authors, affiliations, abstract.
    - **E2:** problem | Introduction | high
      locator:: Section 1
      note:: frames proactive streaming video as decision-making under partial observations and identifies silence/response imbalance.
    - **E3:** benchmark | Task Taxonomy and Benchmark Construction | high
      locator:: Section 3.1; Section 3.2; Figure 2; Figure 3
      note:: defines three capability dimensions, seven tasks, 577 videos, and 1285 QA pairs.
    - **E4:** framework | Figure 1 and contributions | high
      locator:: Figure 1; Introduction contributions
      note:: StreamPro framework uses SFT and GRPO with StreamPro-SFT-63K and StreamPro-RL-3K.
    - **E5:** sft | Supervised Fine-Tuning with CB-Stream Loss | high
      locator:: Section 4.1
      note:: decision format and class-balanced reweighting for silence/response tokens.
    - **E6:** rl | Reinforcement Learning with Multi-Grained Rewards | high
      locator:: Section 4.2
      note:: GRPO reward combines format, turn-level F1, and trajectory-level rubric components.
    - **E7:** data | Training Data | high
      locator:: Section 4.3; Appendix B.2
      note:: SFT and RL data sources and task distributions.
    - **E8:** results | Proactive tasks | medium
      locator:: Table 2
      note:: StreamPro-GRPO-4B achieves strongest reported StreamPro-Bench score among listed baselines.
    - **E9:** results | Real-time streaming and offline tasks | medium
      locator:: Table 3; Table 4
      note:: reports real-time streaming and offline benchmark trade-offs.
    - **E10:** data pipeline | Appendix A.1 | high
      locator:: Appendix A.1
      note:: video collection, caption generation, two-agent verification, human review.
    - **E11:** risk forecasting | Appendix A.1.4 | high
      locator:: Appendix A.1.4; Table 8
      note:: human annotation and 3-second risk-warning definition.
    - **E12:** ablation | Ablation Study | medium
      locator:: Section 5.3; Tables 5-7
      note:: validates CB-Stream Loss, temporal tolerance, and trajectory-level reward.
    - **E13:** limitation | Limitations | high
      locator:: Appendix F
      note:: no dedicated memory mechanism, simple sliding window, video-text only, no audio.
