# KV 管理与周期服务：比较笔记

外部文献笔记，不定义项目机制、实验结果或新颖性。条目来自 2026-09-21 的来源记录；Metronome、LiveServe、VoxServe 与 Cake 的相关段落于 2026-09-25 复核。比较限定到所列论文版本，不推断当前软件支持范围。

## 分层缓存与恢复

| 工作与来源 | 状态对象 | 逐出与恢复依据 |
| --- | --- | --- |
| [CachedAttention](https://arxiv.org/abs/2403.19708v3)，§3 | 多轮会话的历史 KV | 利用等待队列安排缓存与预取，逐层搬运；队列提供的提前量取决于已到达工作 |
| [Pensieve](https://arxiv.org/abs/2312.05516v3)，§4 | 可分布于 GPU、CPU 或待重算区域的历史块 | 按恢复成本与闲置时间选择块；在批次准备时恢复，支持部分驻留 |
| [HCache](https://arxiv.org/abs/2410.05004v1)，§3–4 | 用于重建 KV 的历史 hidden states | 请求恢复过程中组合加载、重建与重算；其存储对象和直接缓存 KV 不同 |
| [Strata](https://arxiv.org/abs/2508.18572v1)，§4 | 分层 radix tree 中的前缀页 | 根据命中、加载需求和计算需求组批，利用排队时间从慢层预取 |
| [LMCache](https://arxiv.org/abs/2510.09665v2)，§5–6 | 内容寻址的前缀块 | 为已到达查询匹配并加载 KV，支持分层存储及传输流水线 |
| [Mooncake](https://arxiv.org/abs/2407.00079v4)，§3–4 | 分布式缓存中的前缀块 | 请求调度时选择缓存和执行位置，协调加载与计算 |

缓存命中、恢复触发与实际使用是不同事件。排队期预取不能直接表述为知道尚未到达请求的释放时刻。

## 提前信号与模型内部预取

| 工作与来源 | 提前信息 | 比较时需保留的区别 |
| --- | --- | --- |
| [SYMPHONY，NSDI 2026](https://www.usenix.org/conference/nsdi26/presentation/agarwal) | 应用的 advisory request | 提示未来需求，不保证到达时间、顺序或所需容量；正式版本的题名与作者不同于早期预印本 |
| [KVFlow](https://arxiv.org/abs/2507.07400v1)，§3 | Agent Step Graph 中的执行距离 | 主要管理 agent 静态前缀；步骤距离不是墙钟时间 |
| [InfiniGen](https://arxiv.org/abs/2406.19707v1)，§4 | 上一层计算产生的 KV 重要性预测 | 获取注意力子集，需区分其近似选择与完整参考状态的恢复 |
| [ECHO 官方实现与论文入口](https://github.com/sjtu-zhao-lab/ECHO) | 原生稀疏注意力的 indexer 选择 | 预取与缺失项补取发生在模型内部；应以原生稀疏注意力作为语义参照 |

## 暂停与恢复

**InferCept。** [原论文](https://proceedings.mlr.press/v235/abhyankar24a.html)按交互暂停时长及恢复成本选择保留、换出或重算，并限制恢复对其他请求的干扰。暂停结束后的恢复与根据未来周期提前安排恢复是不同的时间条件。具体规则见 §3–4。

**Cake。** [论文 v2](https://arxiv.org/html/2410.03065v2)在请求到达后的前缀准备阶段，从前部重算、从后部加载，在运行中确定两者交会位置。其研究对象是加载阶段的计算与 I/O 协作，不包含完整的跨周期驻留规划。

**CacheFlow。** [论文 v1](https://arxiv.org/abs/2604.25080v1)研究 token、layer 与 GPU 维度上的并行恢复及批内资源分配。比较需核对恢复对象、并发假设和启动条件，不能仅因同时使用计算和传输就视为相同调度问题。

进一步的工具调用与复用预测工作包括 [TokenCake](https://arxiv.org/abs/2510.18586v4)、[Adaptive KV Retention](https://arxiv.org/abs/2608.30830)和 [Ask the Tool, Don't Guess](https://arxiv.org/abs/2609.18849)。这些是后续定向核验入口，不据此声明某类方法已被穷尽。

## 交互与语音服务

**Metronome。** [论文 v1](https://arxiv.org/html/2607.02640v1)通过窗口与 attention sinks 限制保留状态，并按延迟反馈控制准入。§2 将 frame period 设为 frame budget；§3 的 Qwen-Omni 实验采用 2 s。论文报告 phase-staggered 输入流，但这本身不证明恢复调度控制了会话 phase。其关于持续会话缺少空闲的论述，不能代替对相邻 KV 访问之间空闲区间的测量。

**LiveServe。** [论文 v1](https://arxiv.org/html/2606.22983v1)利用播放进度与打断信号控制生成。§5 以预计复用时间排列逐出候选，并在 speech start 或 barge-in 时尝试提前装入 KV；不能隐藏代价时沿常规路径恢复。该时间信息来自交互事件与估计，不能写成已知的周期释放表。

**VoxServe。** [论文 v1](https://arxiv.org/html/2602.00269v1)区分首音启动与持续播放阶段，并以播放期限安排流式语音生成。其逐请求执行与解码器状态管理，不直接证明已解决跨更新累积历史的驻留问题。

比较上述工作时，应分别核对保留语义、时间信息、phase 控制、逐出量、目标分配和服务指标。现有机制组合是否产生新的贡献，仍取决于具体算法与实验。
