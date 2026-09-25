# 固定 micro-turn 与端点触发：来源和时间语义

外部来源笔记，不定义项目范围、机制或实验结果。周期数值于 2026-09-25 复核；其他条目保留所列论文版本的解释，正式引用时回到原文。

## 时间粒度

| 外部模型或负载 | 时间量 | 来源与限定 |
| --- | --- | --- |
| Moshi | 12.5 Hz，即 80 ms 音频帧 | [论文 §3.3–3.4](https://arxiv.org/html/2410.00037v2)，输入输出为平行流 |
| TML-Interaction-Small | 200 ms time-aligned micro-turn | [官方说明](https://thinkingmachines.ai/blog/interaction-models/)，输入输出在模型序列中交错 |
| Qwen2.5-Omni | 2 s 编码 attention block 与音视频分组 | [报告 §2.2、§2.4](https://arxiv.org/html/2503.20215v1)，不能据此推断完整对话模型的更新周期 |
| Metronome 的 Qwen-Omni 负载 | 2 s frame period / budget | [论文 §2–3](https://arxiv.org/html/2607.02640v1)，属于被评估服务负载的配置 |

帧长、服务更新周期和端到端响应延迟分别描述不同事件。表中数值是实例，不是全部交互模型的周期范围。

<a id="task-timing-examples"></a>
## 需要在话轮结束之外响应的任务

[Thinking Machines Lab 官方说明](https://thinkingmachines.ai/blog/interaction-models/)提供以下例子：

| 任务 | 触发依据 | 来源位置 |
| --- | --- | --- |
| 实时翻译 | 用户持续输入的语义内容 | Simultaneous speech |
| 发言中的语义提示 | 用户话语中的指定线索 | CueSpeak |
| 连续视频事件报告 | 画面中目标动作开始或结束 | Charades 评测说明 |
| 按指定时间发声 | 已经过的时间 | TimeSpeak |

这些任务同时要求内容与时机正确。厂商评测和演示支持任务需求及其实现实例，没有隔离固定 micro-turn 相对所有事件触发实现的收益。

## 组件架构与更新方式

端点触发描述对话模型何时启动更新；级联描述 ASR、LLM、TTS 等组件如何组合，两者不能互换。

[DuplexCascade v1](https://arxiv.org/html/2603.09180v1)在级联中持续运行 ASR，定期把部分转写送入 LLM，由控制 token 表达等待、回应和打断等行为。§4.4 扫描 micro-turn 长度，报告交互准确率与延迟的取舍；这证明级联也可采用固定时间片，不证明固定时间片普遍优于事件触发。

[EMNLP 2024 的 duplex 模型研究](https://aclanthology.org/2024.emnlp-main.644/)以固定时间片处理输入输出，并在小规模用户研究中比较响应性。其基线在完整话轮后启动有限响应，不能直接代表所有现代端点检测和打断系统。

## 固定周期提供的信息

固定时间片提供规律的更新机会；在输入按时到达且没有积压时，新事件到下一次更新释放的等待不超过一个周期。这个界限不包含网络、排队、计算和播放。

更短周期增加调用频率并缩短执行预算；更长周期可能积累更多语义信息，也增加反应等待。实际取舍需要匹配内容、工作量和交互目标后测量。模型选择沉默仍可能执行状态更新，不能从没有可播放输出推断没有计算。
