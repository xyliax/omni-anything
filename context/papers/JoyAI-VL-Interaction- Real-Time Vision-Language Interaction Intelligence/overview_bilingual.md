# JoyAI-VL-Interaction

| Field | English | 中文 |
| --- | --- | --- |
| Core question | Can a video model decide by itself when to stay silent, respond, or delegate while watching a live stream? | 视频模型能不能在持续观看时自己决定沉默、回答，或把慢问题交给后台模型？ |
| Task type | Core streaming interaction RL. | 核心 streaming interaction RL。 |
| Date | arXiv v1, 2026-06-10. | arXiv v1，2026-06-10。 |
| Unit | JD.com. | 京东。 |
| Public resources | Paper, GitHub, HF model, HF dataset are available links. | 论文、GitHub、HF model、HF dataset 链接可访问。 |

## What The Paper Does / 这篇做了什么

- **English:** JoyAI trains an 8B vision-first interaction model that processes a live video stream and makes a per-second action decision: silence, response, or delegation to a background model/API/agent.
- **中文:** JoyAI 训练了一个 8B 级 vision-first 交互模型。它持续读取视频流，每秒选择一次动作：沉默、回答，或委托后台模型/API/agent。

- **English:** The important shift is that "when to speak" is not a polling timer or external threshold. It becomes a learned model action.
- **中文:** 关键变化是，“什么时候说话”不再由外部定时器或阈值决定，而是模型自己学出来的动作。

## Workflow / 训练流程

| Step | English | 中文 |
| --- | --- | --- |
| Data | 4M+ time-aligned streaming clips normalized into per-second action labels. | 超过 4M 个时间对齐的流式片段，统一成每秒动作标签。 |
| SFT | Weighted SFT reduces repeated-silence dominance and up-weights response onsets. | 带权 SFT 降低连续沉默的主导性，提高回答起点权重。 |
| Rollout | Answer-centered causal streaming windows rather than independent one-second samples. | 围绕有价值回答截取因果流式窗口，不是每秒一个独立样本。 |
| RL | GRPO rewards correct/timely response, proper silence, and good delegation. | GRPO 奖励正确且及时的回答、合理沉默和合理委托。 |
| Runtime | Foreground real-time loop plus background async loop, served through vLLM with hierarchical memory. | 前台实时 loop 加后台异步 loop，使用 vLLM 和分层 memory 部署。 |

## Why It Matters For Us / 对我们的意义

- **English:** JoyAI is evidence that streaming RL can train useful interaction behavior. The open problem is no longer simply "can streaming RL work?"
- **中文:** JoyAI 说明 streaming RL 已经可以训练出有用的交互行为。问题不再只是“能不能训起来”。

- **English:** The remaining systems gap is the control plane: how to track visible state, delayed background results, reward-ready boundaries, policy versions, logprobs, group consistency, and trainer admission across streaming trajectories.
- **中文:** 剩下的系统空间是控制面：如何在流式轨迹中追踪可见状态、延迟后台结果、reward-ready 边界、policy version、logprob、group consistency 和 trainer admission。

## Caveats / 注意边界

- **English:** This is not primarily an RL-infra paper. It does not specify a fully async rollout/trainer architecture or elastic resource scheduling policy.
- **中文:** 这不是一篇 RL infra 论文。它没有展开 fully async rollout/trainer 架构，也没有讨论弹性资源调度。

- **English:** The evaluation is early and mostly human-preference based across six scenarios. Full reproducibility still requires repo-level verification.
- **中文:** 评测还偏早期，主要是六类场景的人类偏好比较。完整复现需要继续核验 repo。

## Links

- Paper: https://arxiv.org/abs/2606.14777
- GitHub: https://github.com/jd-opensource/JoyAI-VL-Interaction
- HF model: https://huggingface.co/jdopensource/JoyAI-VL-Interaction-Preview
- HF data: https://huggingface.co/datasets/jdopensource/JoyAI-VL-Interaction
