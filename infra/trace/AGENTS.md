# infra/trace

独立 trace 套件，负责 raw-log 解析、时钟对齐、bundle 和 Perfetto。实验目录不得复制 trace 或画图实现。

## Contracts

- `collect.py` 与 `collectors/` 注入 EngineCore；指定的 collector 初始化失败时 exit 78。
- `parse.py` 把 `gateway_ticks.log` 和 `kv_events.log` 当作 epoch-clock artifacts 解析。`kv_events.log` 新 schema 为 `E` partial eviction、`B` host backing、`L` load issue、`R` load completion；`parse_kv_events` 按 `(request, trigger)` 配对 L/R。
- `bundle.py` 用 `C <perf> <epoch>` 精确对齐 worker perf clock；缺少配对行的历史 run 才回退到启发式对齐，并标记警告。
- `perfetto.py` 只呈现已有证据：engine scheduling lanes、input pipeline、KV eviction/backing/reload/prefetch、gateway releases 和 residency counters。相邻 `schedule()` 调用间距不是精确 GPU kernel duration。
- 新 parser 只解释当前 schema。不可变旧 run 需要重解析时使用产生该 evidence 的旧 commit，不在新代码中保留废弃术语 adapter。

## Usage

```bash
python -m infra.trace.perfetto <run-dir | experiment/run-id | unique-run-id>
python -m infra.trace.perfetto --all
```
