# Results index

代码与证据共享实验名：

```text
results/<experiment>/runs/<run-id>/          # 一次运行的不可变证据
results/<experiment>/aggregates/<id>/        # 跨 run 数据聚合（记录全部输入 run 与 hash）
```

Run ID 格式 `<YYYYMMDD>_<HHMMSS>_<label>`：短、可读、按时间排序；参数细节全部在该 run 的 `manifest.json` 里，不进目录名。

Perfetto 导出（写入 run 的 `derived/`，只写一次）：

```bash
python -m tracekit.perfetto <run-id-or-path>
```

## 证据边界

| Experiment | 证据性质 |
| --- | --- |
| baseline | 端到端 Qwen-Omni/vLLM/metronome 真实执行 |
| conveyor | 新引擎（错开相位 gateway + 取现货 worker），与 baseline 同模型同栈同 workload |

## 保留规则

- runner 创建唯一目录，从不复用既有路径；**runner 从不删除任何 run，失败与中断的 run 同样保留**（失败证据也是证据）。
- 正式 run 的判据是 `status.json` 的 `state=success` 且 validation 通过；exit 0 本身不构成成功。
- 终态有三种：`success` / `failed` / `interrupted`。操作者 SIGINT/SIGTERM 由 runner 自动落成 `interrupted`；只有 SIGKILL 级别的硬杀会把 run 遗留在 `running`——此时由人把 `status.json` 的 `state` 手工改成 `interrupted`（这是「证据不改写结论」纪律下唯一允许的 status 手工订正）。
- 淘汰过时 run 是人的决定，不是代码的行为；每次淘汰必须同步更新本索引。
- 跨 run 分析只住 `aggregates/`，且记录全部输入 run ID 与 hash；聚合拒绝混用不同 compute trace。
- docs 里引用的每个数字都必须能指回本目录下一个仍然保留的 run。

## Retained runs

### baseline

- `20260807_145323_pilot-n8` — paringest+trace，N=8，360s pilot：池占用线性上升，t≈234s 占满（预测 236s），随后 preemption 后 run=0/wait=1 全部会话滞留，而客户端 deliv_pct=100.5% 指标正常（silent failure 现场）。
- `20260809_144706_smoke-n8-120s` — paringest+trace，N=8，120s 冒烟：验证大重构后全链路（配置私有化、preflight 移除、worker 精简、GPU 采样 200ms）。全部通过：state=success、miss 0%、kv 升至 0.557（120s 不足以占满，符合预期）。

（原 conveyor 路线的全部 run 已于 2026-08-08 随方案废除一并淘汰，记录见 `docs/experiment-log.md` 同日条目。）

### conveyor

- `20260810_122257_stagger-golden` — **相位机制权威 run**（N=8，120s，trace）：双时钟配对精确刻度 + 首片守卫 + 死会话检测齐备，8/8 会话全部存活、零 issue，相位间距 247-252ms（设计 250ms），tick→prefill 真实刻度 med=291/p90=334ms。
- `20260810_183303_stagger-gwtrace` — **gateway 发射级 trace + 绝对网格权威 run**：每会话周期精确 2000.0ms（重锚漂移消除），源头晚醒 max 1.2ms/534 发射零离群，交付记录全额；gateway_ticks.log 自此为必需 artifact。
- `20260811_193634_park-onstop` — **park 机制与驻留核算权威 run**（N=8，seed 4096，K=128，auto-park-on-stop）：稳态池占用 0.296 vs 全驻留假设 0.860（66% 驻留换出），同时全驻留 3 会话占 79%，回载窗口 p50=70ms、CPU 覆盖 100%，交付零恶化；时间线含完整白盒泳道（ingest 三段/PARK/KV mirror/KV reload/驻留锯齿）。

- `20260812_200208_park-cleanwarm-r2` — **warm-start 终版权威 run，全部通过**（state=success）：seed 阶段零机制交错（auto-park 挂起、不做收尾 park）→ 第 1 周期全驻留 → 首次 auto-park 自然转入稳态（覆盖率 8/8 全部 100%）；miss=0.00%、TTFA 2002ms、tick 期零 LARGE、首段全部准点、**inv_backlog 恒 25 = 设计值（库存永久偏移问题就此关闭）**。取代同日 cleanwarm/seedbarrier 系列过程 run，根因链全在 experiment-log。

2026-08-12 淘汰（人的决定）：错开相位与 park 落地过程中的 13 个过程性 run（首个相位 run、detok 负结果探针 ×2、ingest 五站探针、clockfix、metricfix、park 冒烟 ×4、whitebox、driftfix、keepquota）——各自的发现与数字已全部沉淀于 `docs/experiment-log.md` 同日条目（该文件 append-only，历史路径不回改）；被取代关系见各条目。保留集为每个机制主张的现行权威证据。
