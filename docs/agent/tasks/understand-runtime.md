# Understand Runtime

## Read Set

按顺序读取：

1. `docs/problem.md#workload-model`
2. `docs/system.md`（完整读取；包含 arms、机制、KV lifecycle、warm start、cycle 与 failure semantics）
3. `docs/agent/system-map.json`
4. `docs/agent/dynamic-edges.json`
5. `infra/run/AGENTS.md`
6. `infra/trace/AGENTS.md`

不需要先读 legacy experiment log 或完整 git 历史。

## Required Output

完整 walkthrough 必须覆盖：

- runner 启动的每个进程，以及 client controller 再启动的 shard；
- client → gateway → worker → EngineCore 的数据流；
- baseline 与 conveyor 的发射差异；
- resident / parked / materializing 控制阶段，以及它与 block-pool 真实 residency 的区别；
- subprocess、WebSocket、gRPC、ZMQ utility IPC 和 sitecustomize monkeypatch；
- 每次状态变化由哪个 artifact 证明；
- failure 与 fallback 路径。

如果只能画出目录/import 图而没有上述动态边，walkthrough 不完整。
