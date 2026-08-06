# omni-anything：双工语音 serving 的显存墙与"带宽换显存"传送带

单卡上 serve"双工语音前台（硬拍）+ 后台 agent 工具结果回注"负载的研究：**真栈实测（vLLM 0.23 + Qwen2.5-Omni-7B + RTX 3090，E 系列实验）**收敛到一个方案候选——**时刻表化的尾部 KV 传送带（用 H2D 带宽换等效显存容量）**。

## 主线（一段话）

双工语音 serving 是显存绑定的：KV 每拍必被 attend、常驻单调涨、无轮次间隙可换出，GPU 在算力尚有约一半空闲时就因装不下而死（本仓库 E1 真栈三形态解剖 + Metronome 交叉验证，且撞墙 slack 有跨代际闭式）。既然容量稀缺而拍内 H2D 带宽和计算时间大量闲置，就用带宽赎回容量：尾部 KV 母本住 DRAM、按时刻表每拍 DMA 搬入、算完即释放——等效容量 = M + P，收益比 P/M 是纯硬件比值（PCIe5/480ms 净 ~20%，3090/PCIe3 +83%，2s 拍 ~+100%）。相位指派、传输时刻表、提交/作废语义、静默停泊四个编排对象构成方案主体。

## 文档地图（下一个读者从这里开始）

| 文档 | 状态 | 内容 |
|---|---|---|
| **`FINDINGS.md`** | ✅ 现行结论 | **E 系列全部发现的逐条清单**（病理/剖面/硬件闭式/生态对表/测量学教训），每条带证据指针。**看结论从这里开始。** |
| **`PROBLEM.md`** | ✅ 现行结论 | 问题定位收敛版：一句话、三要素、四个实测事实、三面墙、领域空白、方案摘要（数字口径见溯源注）。 |
| **`IDEA-KV-CONVEYOR.md`** | 🧪 方案候选（未验证） | 从问题定义到方案收敛的完整记录：否证的 v1（重算版）、闭式收益、编排设计、相关工作对比、验证计划 |
| **`PAPER-EXPERIMENTS.md`** | 📋 实验设计（执行中） | 以发 paper 为目的的正式实验设计：claim→实验映射（E0–E6）、平台决策、Metronome 代码复用地图、方法论规范、风险门。**全部数字新测；旧 S/T 模拟器系列已于 2026-08-06 深度清理中整体删除（git 可溯）。** |
| **`STORY.md`** | 📜 历史叙事（部分现行） | problem-discovery 叙事。⚠️ 其 P1–P4 数字源自已删除的模拟器 pilot，以 E1 真栈数据为准；§5 双工产品/文献查证仍为现行 |

> 2026-08 白名单清理：已放弃的研究线（注入的计算侧安放策略对比、爆炸半径、分块 vs 整段、旧 FINDINGS.md 等）已物理删除，git 历史（commit 5020583 及之前）可溯，**不应作为现状引用**。实验编号已重排：S1=密度、S2=作废、S3=注入冲击。**2026-08-06 深度清理：模拟器/标定谱系（simulator/、pilot/、EVIDENCE.md、TIMELINES.md、calibration 的 T1–T4）整体删除**——动机主张全部由 E1 真栈证据接管；E4 先验（40% 作废、LogNormal 注入）已固化于 PAPER-EXPERIMENTS §三。

## 目录

- `harness/` — E 系列真栈实验全部组件（worker/driver/仪器/可视化导出）：索引 `harness/README.md`，**使用手册 `harness/USAGE.md`**
- `calibration/` — E0 DMA 干扰微基准（工具 + 数据；PCIe 带宽标定）
- `results/paper/` — E 系列运行证据（五件套日志）；`results/figures/` — E1 图组；`results/viz/` — Perfetto trace（入库，双击可下载到 ui.perfetto.dev 打开）
- `metronome/` — **git submodule**（钉死 `2783a90`，只读纪律不变）：Metronome 论文开源 harness，用于复用其 baseline 谱系——为什么在这里、怎么用、引用时的坑，见 `METRONOME-NOTE.md`（`git clone --recursive` 获取）

## 快速事实（防止被过时信息带偏）

- 真双工产品已量产且均闭源 serving：Seeduplex（字节，2026-04）、GPT-Live（OpenAI，2026-07，含后台工具委托）——见 STORY.md §5(e)
- 真双工 GPU serving 公开文献截至 2026-08 仅 Metronome 一篇（无注入、无作废负载）——见 STORY §5 矩阵
- 本仓库所有"现状如何"类断言标注了查证日期；引用前留意时效（该领域以月为单位翻页）
