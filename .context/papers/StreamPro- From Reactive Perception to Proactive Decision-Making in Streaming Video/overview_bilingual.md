# StreamPro

| Field | English | 中文 |
| --- | --- | --- |
| Core question | How should a streaming video model decide when to respond under partial observation? | 流式视频模型在只能看到过去和现在时，应该如何决定什么时候回答？ |
| Task type | Core streaming RL: proactive decision-making with SFT + GRPO. | 核心 streaming RL：用 SFT + GRPO 训练 proactive decision-making。 |
| Date | arXiv v1, 2026-05-11. | arXiv v1，2026-05-11。 |
| Unit | Renmin University, MiLM Plus/Xiaomi, Peking University. | 中国人民大学、小米 MiLM Plus、北京大学。 |
| Public resources | Paper found; official code/model/data not found on 2026-07-02. | 已找到论文；2026-07-02 暂未找到官方代码、模型或数据入口。 |

## What The Paper Does / 这篇做了什么

- **English:** StreamPro argues that existing proactive video tasks often reduce to delayed perception: the model waits until evidence appears and then answers.
- **中文:** StreamPro 认为，很多已有 proactive video 任务其实只是 delayed perception：模型等证据出现后再回答。

- **English:** It builds StreamPro-Bench and trains models with CB-Stream Loss in SFT, then GRPO with format, turn-level, and trajectory-level rewards.
- **中文:** 它构建 StreamPro-Bench，并先用 CB-Stream Loss 做 SFT，再用带 format、turn-level、trajectory-level reward 的 GRPO 训练模型。

## Workflow / 训练流程

| Step | English | 中文 |
| --- | --- | --- |
| Decision format | Each timestep outputs `</Silence>` or `</Response>` plus text. | 每个时间步输出 `</Silence>` 或 `</Response>` 加文本。 |
| SFT | CB-Stream Loss reweights silence and response control tokens. | CB-Stream Loss 对沉默/回答控制 token 重新加权。 |
| RL data | StreamPro-RL-3K proactive trajectories. | StreamPro-RL-3K proactive 轨迹。 |
| Rollout | A generated trajectory of K streaming steps, not isolated seconds. | 长度 K 的流式生成轨迹，不是独立秒级样本。 |
| Reward | Format + turn-level F1 + trajectory-level rubric reward. | 格式 reward + turn-level F1 + trajectory-level rubric reward。 |
| Update | GRPO. | GRPO。 |

## Why It Matters For Us / 对我们的意义

- **English:** StreamPro makes the sample-boundary issue easy to explain: streaming RL is not static QA with more frames. The model's silence, timing, ordering, and repeated responses are part of the training object.
- **中文:** StreamPro 能帮我们解释样本边界问题：streaming RL 不是“静态 QA 加更多帧”。模型的沉默、时机、顺序和重复回答都属于训练对象。

- **English:** It also shows why turn-level rewards are not enough. A trajectory-level reward is needed when the whole sequence must be coherent and not overly fragmented.
- **中文:** 它也说明只看单次回答不够。只要整条回答序列需要连贯、不漏、不碎，就需要 trajectory-level reward。

## Caveats / 注意边界

- **English:** StreamPro is not an open deployment stack yet. No official repo, model, or dataset link was found during this digest.
- **中文:** StreamPro 还不是可直接复现的开源部署栈。这次整理时没有找到官方 repo、模型或数据链接。

- **English:** The paper uses sliding-window inference and does not propose a dedicated long-horizon memory or RL-infra scheduling design.
- **中文:** 论文使用 sliding-window inference，没有提出专门的长时程 memory 或 RL infra 调度方案。

## Links

- Paper: https://arxiv.org/abs/2605.16381
