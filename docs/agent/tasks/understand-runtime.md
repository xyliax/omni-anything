# Understand Runtime

## Read Set

1. 根 `AGENTS.md`；
2. `docs/problem.md`（研究问题、抽象 workload 和 canonical terminology）；
3. `docs/system.md`（拓扑、机制、KV 状态模型和 one-session cycle）；
4. `docs/experiments.md`（evaluated systems、配置域和测量语义）；
5. `docs/findings.md`（只在需要当前状态或结论时读取）；
6. `docs/agent/system-map.json` 与 `docs/agent/dynamic-edges.json`（定位组件和跨进程边）。

## Questions to Answer

- 一个 session 的周期、release time、release offset 与 latency target 分别是什么？
- 周期本身如何形成相邻两次 session use 之间的 reuse interval？
- release-offset scheduling 分散了哪些 demand，又没有创造什么资源？
- matched Metronome baseline 与 Conveyor 分别执行哪些路径？
- session activity、GPU block residency、host backing coverage、transfer state 与 request ownership 如何正交描述 KV 状态？
- partial KV eviction 后，GPU prefix reuse、host-backed reload 与 recomputation 分别在什么条件下发生？
- output cap \(M\)、实际输出量 \(m_{i,k}\)、未交付输出缓冲与 service-RPC latency 各表示什么？
- 当前 runner 为什么只能报告 Thinker text，不能声称测得 PCM playback stall？

## Stop Conditions

若答案依赖当前数字或性能状态，必须转到 `docs/findings.md` 并保留完整 `FINDING-*` 与 `EVIDENCE-*` ID。不要从冻结的 legacy log、旧 results schema 或 `.context/` 草稿生成当前 paper narrative。
