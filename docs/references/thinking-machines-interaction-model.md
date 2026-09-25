# Thinking Machines 交互模型：时间结构与服务接口

外部来源笔记。依据 [Thinking Machines Lab 官方说明](https://thinkingmachines.ai/blog/interaction-models/)，相关段落于 2026-09-25 复核。本文不定义项目设计或实验范围。

## 可引用的属性

| 属性 | 官方说明的位置与内容 |
| --- | --- |
| 时间结构 | “Time-aligned micro-turns”：输入和输出按 200 ms 时间片交错进入模型序列，交互时间线保留沉默、重叠和打断 |
| 服务接口 | “Inference optimization”：客户端逐片提交，服务端将片段追加到 GPU 上的持久序列，以减少反复分配和元数据处理 |
| 前后台协作 | “System overview”：交互模型维持前台交流，后台模型异步承担较长推理、搜索和工具任务 |
| 长会话限制 | “Long sessions”：连续音视频使上下文增长，长会话仍需要上下文管理 |

持久序列说明跨更新保留状态的需求，不能单独证明 KV 空闲窗口、计算余量或特定显存管理策略的收益。前后台共享上下文是该模型架构的属性，不是所有 interaction session 的定义。

## 任务与评测

官方列举同时翻译、语义线索回应、视觉事件报告和按时间发声等行为。TimeSpeak 与 CueSpeak 同时检查内容和行动时机；这是厂商定义的评测，不是固定 micro-turn 相对所有事件触发方案的因果消融。具体任务来源见[交互时间结构笔记](micro-turn-versus-endpoint-interaction.md#task-timing-examples)。

公开视频展示给定轨迹上的行为。回放不能测量模型改变回答后用户会如何反应；评价这种反馈需要交互式协议。视频读回的逐句解释和不可访问的本地媒体不作为论文事实依据。
