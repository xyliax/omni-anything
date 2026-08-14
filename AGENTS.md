# AGENTS.md

Agent 工作入口。先读本文件，再打开任务所需的那一份权威文档。

## 项目一句话

在单张 GPU 上同时服务两类负载：双工语音前台 (duplex speech foreground) 的硬 tick（固定周期 T 的硬 deadline 帧，inelastic），与后台 agent 结果注入 (injection，delay-tolerant 弹性)。

方案层重建中：原候选方案（KV conveyor）已于 2026-08-08 整体废除（历史在 git），新方案由项目负责人设计、增量实现，已验证三个机制增量（结论在 `docs/findings.md` H 系列）：**错开相位**（gateway 槽轮 + 绝对网格）、**取现货交付**（含指标口径重建）、**KV 部分释放原语 park**（decode 结束瞬间引擎侧 auto-park + keep-K 底座，稳态驻留降 66%，vLLM 调度器轻量补丁）。全链路白盒可观测（单份 Perfetto 时间线覆盖全部机制，读图指南在 `docs/architecture.md`「一个会话的一个周期」）。容量主张（N 扫描 + roofline）待正式对比 run。问题定义与实测事实不受影响（`docs/problem.md`、`docs/findings.md`）。

- **真机实测栈**：vLLM 0.23 + Qwen2.5-Omni-7B + RTX 3090，tick = 2s（机器可读形态在 `experiments/baseline/config/`）
- **论文外推配置**：文本代理双工与 tick 结构写在 `docs/experiments.md`；与实测栈是两套配置，两套数字不得混用

## 实验体系

主实验（定义与协议的唯一权威是 `docs/experiments.md`）：**baseline 已冻结并有正式 run；conveyor 增量实现中，对比协议待机制齐备后重建**；旧 E0–E6 编号的映射见该文末行。

| 目录 | 一句话 | 状态 |
| --- | --- | --- |
| `experiments/baseline/` | baseline 引擎：metronome 的 vLLM 栈 + paringest 模式 | 可运行，有正式 run；已冻结 |
| `experiments/conveyor/` | 新引擎：错开相位 gateway（槽轮）+ 取现货 worker + 镜像/park/回载全链路（engine_patch） | 三个机制增量已验证（FINDINGS H 系列）；容量主张待正式 run |

横向设施：`lab/`（运行工作流 / run 目录 / 进程 / 探针——runner 只声明差异，时间线全仓一份）、`tracekit/`（trace 与可视化能力集中于此：采集、解析、对齐、Perfetto；临时画图属一次性行为，产物不入库）。配置是实验私有的：每个实验目录自带 `config/`（纯 Python 常量），不设全局配置层。

## 事实层与 `context/`

**`docs/` 是事实与决策层**（本项目结论、问题、方案、实验、纪律）。  
**根目录只留本文件与 `README.md`（入口）。**  
**`context/` 是思考原料与工作语境（讨论、设想、外部整理、表达草稿），不构成项目事实。**

归属测试：删除该文件，项目正确性或可理解性是否受损？受损 → `docs/`；只是「重新收集要花时间」→ `context/`。

| 维度 | `docs/`（事实层） | `context/` |
| --- | --- | --- |
| 内容 | 本项目结论、问题、方案、实验、纪律 | 讨论与设想（ideas）、外部整理（references / papers）、表达草稿（slides） |
| 过时 | 过时是 bug | 允许滞后，快照打日期即可 |
| 内聚 | 一篇文档完整持有自己的主题；**兄弟文档之间少交叉引用** | 结论只住 `docs/`，此处只收原料 |

**交叉引用纪律**：本文件是唯一文档地图。`docs/` 各文自洽可读，跨主题由读者经本表跳转。允许的外指：`results/`、`experiments/`、`lab/`、`tracekit/`、`third_party/`、外部 URL、以及 `context/` 作证据原料（结论仍写在 `docs/`）。

提升通道（单向）：`context/ideas/` 被采纳 → 写入 `docs/`；digest 中项目依赖的结论上移，原文留 `context/papers/`。

## 权威文档（`docs/`）

| 文档 | 状态 | 完整持有 |
| --- | --- | --- |
| `docs/problem.md` | 结论 | 问题定义、负载三要素、实测事实、瓶颈与可行域、领域空白、与 Metronome 关系 |
| `docs/findings.md` | 结论 | 一句话发现 + 证据指针（E 系列 = baseline 病理，H 系列 = conveyor 机制）；**看结论从这里开始** |
| `docs/architecture.md` | 事实（随代码同步） | 代码分层、进程拓扑、文件格式契约、新实验接入形状；**改代码结构时同步更新** |
| `docs/experiments.md` | 协议 | baseline 引擎定义、已验证主张、实验方法论；对比协议待新方案定型后重建 |
| `docs/experiment-log.md` | 过程记录（append-only） | 真机 run 记录；新 run 只 append 这里；旧条目引用的历史路径不回改 |
| `docs/metronome.md` | 纪律 | `third_party/metronome/` pin 的 baseline 角色、必继承方法论、引用订正 |

注入负载冻结先验（40% cancellation、LogNormal）写在 `docs/experiments.md` 方法论节。

**FINDINGS ↔ 实验记录**：新 run 只 append `docs/experiment-log.md`；提炼结论只改 `docs/findings.md`。

## 目录边界

| 路径 | 角色 | 读写 |
| --- | --- | --- |
| `docs/` | 事实与决策 | 任务要求时改 |
| `experiments/` | 实验目录（baseline / conveyor）；配置在各实验私有的 `config/` | 任务要求时改 |
| `lab/` | 共享运行基础设施 | 任务要求时改 |
| `tracekit/` | 独立 trace 套件；实验不得自带 trace/画图代码 | 任务要求时改 |
| `results/` | 运行证据；runner 从不删除 run（含失败 run），淘汰是人的决定且必须同步更新 `results/README.md` 索引 | 证据不改写结论 |
| `environment/` | 锁定运行时 profile 与校验 | 任务要求时改 |
| `third_party/` | git-subrepo pin；见 `third_party/AGENTS.md` | **只读** |
| `context/references/` | 外部公开信息原文或整理 | 按题打开 |
| `context/papers/` | 跨主题 digest 池 | 按题打开 |
| `context/ideas/` | 未进事实层的设想 | 按题打开 |
| `context/slides/` | 表达草稿 | 可滞后；仅幻灯片任务时打开 |

PDF/PPTX 默认不入库（根 `.gitignore`）。`third_party/metronome/` 是 baseline 直接依赖的 pin；本仓库的 worker（`experiments/baseline/worker/stream_server.py`，与 pin 内同名）复制自该 pin 后永久分道，不追上游更新。

## 行为约束

- 进展、主线与数字以 `docs/findings.md`、`results/`、`docs/experiment-log.md` 为准。
- 每个数字带出处限定（实测 / 早期模拟器标定 / 线性外推 / 冻结先验）；引用与校准各在同一出处内进行。标定模型（Qwen3-1.7B，112KB/token）与主模型（7B，56KB/token）各有口径，引用时带模型限定。
- 标准术语全仓一致：全双工 (full-duplex)、注入 (injection)、N* 可调度并发数 (schedulable concurrency)、饱和 (saturation)。
- 编号空间存在重名：`docs/findings.md` 条目码引用时必须带前缀（如「FINDINGS E3」「FINDINGS C1」）；论文主张（C1–C2）不带前缀；旧实验代号（E0–E6）属历史语境，映射见 `docs/experiments.md` 末行。
- 外部「现状如何」类断言注意查证日期。引用 Metronome 容量数字前读 `docs/metronome.md` 订正节。
- `README.md` 只做对外定位（GitHub 落地页）；契约、地图与索引在 AGENTS.md 体系（根、`experiments/` 各级、`third_party/`）。
- 守卫测试：`tests/test_repository_layout.py` 扫描包括 `docs/`、`README.md`、本文件在内的全部文本层（含反引号内联路径）；改动目录结构时同步改文档即可保持通过。
