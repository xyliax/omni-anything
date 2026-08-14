# experiments：实验设计

## 现状

方案层由项目负责人设计、增量实现：原 conveyor 路线已于 2026-08-08 整体废除（历史在 git）；新 conveyor 引擎的三个机制增量（错开相位、取现货交付、park 驻留管理）均已验证，结论与证据指针见 `docs/findings.md` H 系列。取现货交付下的指标口径（2026-08-10 起）：`deadline_met` = 本 tick 交付 ≥ tpt 个 token（miss = 引擎未跟上生成节奏），TTFA 如实包含一片流水线滞后；client 侧 latency p50/p99 无意义（Step 不含 GPU 等待），延迟分布一律以 trace 侧（per_request.log）为准。warm start 为屏障式状态构造（全部 seed prefill 完成后 tick 才开始），启动期无需测量豁免——run `20260812_200208` 起 tick 首拍即稳态形状。本文持有 baseline 引擎定义与全仓实验方法论；主对比协议（主张表、验收门、里程碑）待容量 roofline 与 N 扫描设计定型后重建。

## baseline 引擎

**模型 Qwen2.5-Omni-7B、workload 2s 硬 tick × 8 路（增量 prefill + decode 配额、context 持续增长；常量在 `experiments/baseline/config/`）、metronome 的 vLLM 0.23 栈 + 本仓库 paringest 模式（`experiments/baseline/`）。**

- KV 全程常驻 GPU（全部页被活跃请求持有，没有任何释放路径）。
- 状态：可运行。正式 run `results/baseline/runs/20260807_145323_pilot-n8`：t≈234s 池占满 + silent failure。
- 产物：kv 池占用轨迹（kv.log）、容量墙 t_wall、per-tick miss、scheduler 逐步 trace。

## 已验证的主张

| # | 主张 | 状态 |
|---|---|---|
| C1 | 双工 serving capacity-bound：池占满即饱和，GPU 大量空闲 | 已复现（baseline） |
| C2 | DMA 与 decode 可并行，κ 小到可用 | 已实测（κ≤1.067；并发带宽≈空载） |

方案侧主张（原 C3–C5）随方案废除一并撤下，待新设计重新提出。

## 方法论（最低限度，对任何后续方案均有效）

- 每点新起进程；正式 run 前人工确认 GPU 空闲（共享卡，邻居竞争实测使 decode 步最多翻倍）。
- 每个数字可追溯到 `results/<experiment>/runs/` 的不可变 run。runner 从不删除任何 run（失败与中断同样保留）；淘汰无价值 run 是人的决定，且必须同步更新 `results/README.md` 索引——与索引及根契约的表述一致。
- 判读看 kv.log 的 starvation 信号，客户端 miss=0% 不作健康判据（silent failure，FINDINGS B1）。
- 饱和判据看滞后漂移（完工时刻逐 tick 后移），不看利用率（与 silent failure 纪律同源）。
- 注入负载冻结先验：泊松均值 30s、LogNormal 中位 512、40% cancellation。
- 主结果点乱序重复 ≥3 次报中位数。

## 论文外推配置（决策 D2）

Qwen3-1.7B（112KB/token）仅用于公式外推与论文配置（tick 480ms），不进真机主对比；真机栈是 Qwen2.5-Omni-7B（56KB/token）。两套口径引用时各带模型限定。

旧实验代号（E0–E6）属历史语境：E1→baseline，其余映射见 git 历史，不再维护。
