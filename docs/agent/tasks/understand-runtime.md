# Understand Runtime

## Read Set

1. 根 `AGENTS.md`；
2. `docs/problem.md`（研究问题、抽象 workload 和 canonical terminology）；
3. `docs/system.md`（设计与状态模型；不作为最新运行拓扑）；
4. `docs/experiments.md`（evaluated systems、配置域和测量语义）；
5. `docs/findings.md`（只在需要当前状态或结论时读取）；
6. `docs/agent/system-map.json` 与 `docs/agent/dynamic-edges.json`（定位组件和跨进程边）。

## Questions to Answer

- 一个 session 的周期、release time、release offset 与 latency target 分别是什么？
- 相邻两次 KV 使用之间在什么条件下存在空闲区间？规律释放与实际执行如何区分？
- release-offset scheduling 分散了哪些 demand，又没有创造什么资源？
- matched Metronome baseline 与 Pilarius 分别执行哪些路径？
- 会话活动、物理分配、有效内容、主机覆盖、双向传输和共享引用如何共同描述 KV 状态？
- partial KV eviction 后，GPU prefix reuse、host-backed reload 与 recomputation 分别在什么条件下发生？
- output cap `M`、模型生成量 `m(i,k)`、未交付输出缓冲与 service-RPC latency 各表示什么？
- 目标 run 实际执行和观测到哪个输出事件，哪些用户交付指标没有被测量？

## Stop Conditions

若答案依赖当前数字或性能状态，必须转到 `docs/findings.md` 并保留完整 `FINDING-*` 与 `EVIDENCE-*` ID。不要从冻结的 legacy log、旧 results schema 或历史草稿生成当前 paper narrative。
