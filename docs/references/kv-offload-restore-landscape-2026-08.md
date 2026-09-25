# KV 驻留与恢复：文献导航

外部资料索引，不维护项目事实或新颖性结论。逐工作来源与比较属性见[核验笔记](closest-work-gap-analysis-2026-09.md)；出版状态和软件支持范围以原始来源为准。

| 研究对象 | 阅读入口 | 需要区分的属性 |
| --- | --- | --- |
| 多轮历史的分层存放 | CachedAttention、Pensieve、HCache | 存储对象、逐出粒度、恢复触发与重算 |
| 前缀共享与缓存传输 | Strata、LMCache、Mooncake | 前缀命中与会话身份；已到达请求与未来需求 |
| 提前信号与复用预测 | SYMPHONY、KVFlow、LiveServe、TokenCake | 行为提示、工作流顺序、预测时间及误差处理 |
| 模型内部的 KV 获取 | InfiniGen、ECHO | 按层或按步访问；参考注意力语义是否保持 |
| 加载与重算组合 | Cake、CacheFlow | 恢复区间、共享资源与启动时机 |
| 周期交互中的状态上限 | Metronome | 保留策略、GPU 驻留与周期服务目标 |

比较时应先确定状态对象和下一次使用信息，再检查时间、空间与执行约束。部分逐出、主机副本、预取或传输与重算组合本身均已有相关工作。

会议规则仅由[投稿清单](../../eurosys2027/planning/submission-checklist.md)维护，不从文献的发表状态推断可省略哪些比较。
