# AGENTS.md

Agent 工作入口。先读本文件，再打开任务所需的那一份权威文档。

## 项目一句话

在单张 GPU 上同时跑两类负载：全双工语音前台 (full-duplex speech foreground) 的硬 tick（固定周期 T 的硬 deadline 帧，inelastic），与后台 agent 结果注入 (injection，delay-tolerant 弹性)。

当前候选方案是 **KV conveyor**：按 tick 时间表把每路会话的尾部 KV 母本 (authoritative host copy) 从 host DRAM DMA 预取入 HBM 暂存、算完即释放（scheduled tail-KV offloading），等效 KV 容量 = resident M + staging P；用闲置 H2D 带宽换更高的 N*（可调度并发数 schedulable concurrency，判据 deadline miss rate ≤ 1%）。

- **E1 实测栈**：vLLM 0.23 + Qwen2.5-Omni-7B + RTX 3090，tick = 2s
- **论文主配置（设计目标）**：文本代理双工与 tick 结构写在 `docs/experiments.md`；与 E1 栈是两套配置，数字各归各套

## 事实层与 `context/`

**`docs/` 是事实与决策层**（本项目结论、问题、方案、实验、纪律）。  
**根目录只留本文件与 `README.md`（入口）。**  
**`context/` 是思考原料与工作语境（讨论、设想、外部整理、表达草稿），不构成项目事实。**

归属测试：删掉该文件，项目正确性或可理解性是否受损？受损 → `docs/`；只是「重新收集要花时间」→ `context/`。

| 维度 | `docs/`（事实层） | `context/` |
| --- | --- | --- |
| 内容 | 本项目结论、问题、方案、实验、纪律 | 讨论与设想（ideas）、外部整理（references / papers）、表达草稿（slides） |
| 过时 | 过时是 bug | 允许滞后，快照打日期即可 |
| 内聚 | 一篇文档完整持有自己的主题；**兄弟文档之间少交叉引用** | 结论只住 `docs/`，此处只收原料 |

**交叉引用纪律**：本文件是唯一文档地图。`docs/` 各文自洽可读，跨主题由读者经本表跳转。允许的外指：`results/`、`calibration/`、`harness/`、`third_party/`、外部 URL、以及 `context/` 作证据原料（结论仍写在 `docs/`）。

提升通道（单向）：`context/ideas/` 被采纳 → 写入 `docs/`；digest 中项目依赖的结论上移，原文留 `context/papers/`。

## 权威文档（`docs/`）

| 文档 | 状态 | 完整持有 |
| --- | --- | --- |
| `docs/problem.md` | 结论 | 问题定义、负载三要素、实测事实、瓶颈与可行域、领域空白、与 Metronome 关系 |
| `docs/findings.md` | 结论 | E 系列一句话发现 + 证据指针；**看结论从这里开始** |
| `docs/design.md` | 方案候选 | 方案演化、公式与收益、编排、宿主决策、相关工作、边界与未决检验 |
| `docs/experiments.md` | 协议（冻结） | 主张→实验矩阵、平台决策与 Metronome 复用地图、负载协议、方法论、验收判据 |
| `docs/experiment-log.md` | 过程记录（append-only） | 真机 run 记录；新 run 只 append 这里 |
| `docs/metronome.md` | 纪律 | `third_party/metronome/` pin 的 baseline 角色、必继承方法论、引用纪律 |
| `docs/glossary.md` | 定义 | 全仓统一术语的完整定义与英文对照；各文首用只留短注 |

E4 冻结负载参数（40% cancellation、LogNormal 注入）写在 `docs/experiments.md` 负载协议节。

**FINDINGS ↔ 实验记录**：新 run 只 append `docs/experiment-log.md`；提炼结论只改 `docs/findings.md`。

## 目录边界

| 路径 | 角色 | 读写 |
| --- | --- | --- |
| `docs/` | 事实与决策 | 任务要求时改 |
| `harness/` | E 系列真机实验组件；运行手册见 `harness/AGENTS.md` | 任务要求时改 |
| `calibration/` | E0 DMA 微基准 | 任务要求时改 |
| `results/` | 运行证据 | 只增不删 |
| `third_party/` | git-subrepo pin；见 `third_party/AGENTS.md` | **只读** |
| `context/references/` | 外部公开信息原文或整理 | 按题打开 |
| `context/papers/` | 跨主题 digest 池 | 按题打开 |
| `context/ideas/` | 未进事实层的设想 | 按题打开 |
| `context/slides/` | 表达草稿 | 可滞后；仅幻灯片任务时打开 |

PDF/PPTX 默认不入库（根 `.gitignore`）。`third_party/metronome/` 是 harness 直接依赖的 baseline。

## 行为约束

- 进展、主线与数字以 `docs/findings.md`、`results/`、`docs/experiment-log.md` 为准。
- 每个数字带出处限定（实测 / 早期模拟器标定 / 线性外推 / 冻结负载参数）；引用与校准各在同一出处内进行。
- 标准术语全仓一致，完整定义与英文对照见 `docs/glossary.md`；各文首次使用留短注即可，不重复完整定义。
- 编号空间撞名：`docs/findings.md` 条目码引用时必须带前缀（如「FINDINGS E3」「FINDINGS C1」）；实验代号（E0–E6）与论文主张（C1–C7）裸写。
- 外部「现状如何」类断言注意查证日期。引用 Metronome 容量数字前读 `docs/metronome.md` 引用纪律节。
- `README.md` 只做对外定位（GitHub 落地页）；契约、地图与索引在 AGENTS.md 体系（根、`harness/`、`third_party/`）。
