# 交互模型与接口：来源索引

外部资料，不定义项目 workload 或实验边界。这里按公开资料记录交互行为与时间结构，不维护产品上线状态、价格、用户规模、当前开放权限或未经复核的容量数字。

输入输出重叠、组件是否级联、目标模型如何获得更新，是不同属性。持续收音或支持打断不足以证明对话主干按固定周期执行；级联架构也可以采用固定时间片。

<a id="representative-request-families"></a>
## 更新触发与代表来源

| 路径或模型 | 来源支持的属性 | 一手来源 |
| --- | --- | --- |
| 消息式生成请求 | 提交 prompt 后生成有限响应；可采用流式返回与连续批处理 | [PagedAttention / vLLM 论文](https://arxiv.org/abs/2309.06180) |
| 端点检测驱动的语音管线 | 根据语音活动、内容及上下文判断发言结束 | [LiveKit EOU 说明](https://livekit.com/blog/using-a-transformer-to-improve-end-of-turn-detection) |
| Moshi | 并行建模用户与模型语音；音频帧率 12.5 Hz，对应 80 ms | [论文 v2](https://arxiv.org/html/2410.00037v2) |
| TML-Interaction-Small | 200 ms time-aligned micro-turns；服务端维持跨更新序列 | [官方说明](https://thinkingmachines.ai/blog/interaction-models/) |
| MiniCPM-o 4.5 | 双工路径采用时间对齐的输入输出块 | [报告 v1](https://arxiv.org/html/2604.27393v1)；[参数笔记](minicpm-o-4.5-kv-geometry.md) |
| DuplexCascade | ASR–LLM–TTS 级联中，LLM 按 micro-turn 接收部分转写并决定行为 | [论文 v1](https://arxiv.org/html/2603.09180v1) |
| SyncLLM | 同步时间块上的双路语音建模 | [论文](https://arxiv.org/abs/2409.15594) |
| PersonaPlex | 基于 Moshi 的双工语音交互，加入角色与声音条件 | [论文](https://arxiv.org/abs/2602.06053) |
| GPT-Live | 持续输入输出与交互会话接口；具体时序以接口文档为准 | [官方开发者指南](https://developers.openai.com/api/docs/guides/live) |
| Seeduplex | 同时听说、干扰抑制与打断处理 | [官方技术说明](https://seed.bytedance.com/en/blog/introducing-seed-full-duplex-speech-llm-attentive-listening-robust-interference-suppression-enabling-more-natural-interaction) |
| Freeze-Omni | 分块输入、状态判断与输出控制需按实际路径分别分析 | [论文](https://arxiv.org/abs/2411.00774) |

Moshi 与 TML 的时间粒度于 2026-09-25 复核。帧长、更新周期、计算耗时和端到端响应延迟不能互换。上述行为不单独证明 KV 增长速度、可用空闲窗口或并发服务容量。

## 进一步阅读

- 时间敏感任务与固定 micro-turn 的取舍：[交互时间结构](micro-turn-versus-endpoint-interaction.md)。
- TML 的序列与服务接口：[专门笔记](thinking-machines-interaction-model.md)。
- 持续会话、播放调度和 KV 管理：[服务系统索引](duplex-serving-systems-landscape-2026-09.md)。
- 多阶段输出的数据接口：[Qwen2.5-Omni 参考实现](qwen2.5-omni-thinker-talker-interface.md)。

其他模型的来源入口保留于对应[论文资料目录](../papers/)，不从遗漏或旧检索结果推断其能力或发布状态。
