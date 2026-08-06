# 问题定义

> **关于文中旧数字**：问题定义与三要素仍有效。文中部分具体数字来自早期模拟器试跑，已被真机实验（E1 及后续）的同向、更强结论取代；数字以 `PAPER-EXPERIMENTS.md` 的执行记录为准。

配套阅读：`FINDINGS.md`（E 系列发现与证据）、`STORY.md`（叙事与相关工作）、`IDEA-KV-CONVEYOR.md`（方案候选，未验证）、`results/`（运行证据）。文档入口见 `AGENTS.md`。

## 一句话

双工语音 serving 是 **capacity-bound**：KV cache 每 tick 都必须参与 attention，常驻显存只增不减，又没有 request 之间的空隙可以把历史换出。结果是 GPU utilization 只有约 13–32% 时，就已经 OOM 崩溃——容量是稀缺资源，而每一 tick 内的 H2D 带宽和计算时间却大量闲置。

我们的回答是**用闲置的数据搬运带宽，换更大的 concurrent capacity**：按时间表搬运 tail KV（KV conveyor，见 `IDEA-KV-CONVEYOR.md`）。等效 KV capacity = resident slots M + staging slots P；收益是纯硬件比值（PCIe 5 / 480 ms 一 tick，净增约 20%）。

## 负载的三要素

| 要素 | 内容 | 去掉它变成什么 |
|---|---|---|
| ① 硬周期 tick | 每 480 ms（谱系从 80 ms 到 2 s）做一次约 8 token 的增量 prefill 加 2–4 步 decode；deadline miss = 音频断裂 = 正确性事故 | 普通对话 serving（Sarathi / Niyama 已解决） |
| ② 弹性注入 | 后台 agent 的 tool 结果，数百到数千 token；约 10% 落在 4–8k 的长尾；40% 概率被用户打断而作废 | 纯双工锁步（moshi-server / Metronome 已解决） |
| ③ 单卡多路 | concurrent session 数 N 是目标函数（受成本约束），不是外部给定 | 单会话工程问题 |

三要素同时出现在产品层：GPT-Live（OpenAI，2026-07；tool call 是 tick 内决策，后台 GPT-5.5 结果回注）与 Seeduplex（字节，2026-04，豆包全量）都是 ①+②+③，服务侧均闭源——见 `STORY.md` §5(e)。

## 四个实测事实（本仓库 + Metronome 交叉验证）

1. **显存先成为瓶颈，大约早一个数量级**（早期模拟器试跑 S1）：KV cache 可行路数 N=12，远小于 deadline 瓶颈的 N=192 / 208（随机相位 / 对齐相位；判据为 deadline miss rate > 1%。deadline 瓶颈数字是历史模拟外推——真实 vanilla 引擎在 N>12 区间是显存直接装不下而硬崩溃，不是弹性排队；真机见 `FINDINGS.md` / `results/paper/`）。单会话 duty cycle 4–9%。Metronome 真机复现：vanilla 默认配置在 N=128 触达 memory cliff 时，GPU utilization 仅约 13–32%——"capacity 先因不足终止了那些算力完全扛得住的会话"。

2. **相位从没被当成可调度资源**（S1）：随机相位比对齐相位多花 4.96 倍 GPU 时间；因到达碰巧凑 batch 产生的额外开销，占全卡忙时的 64.7%。batch size 由会话到达的巧合决定，调度器没有话语权。

3. **整段注入与 tick deadline 正面冲突，伤害由相位 1:1 决定**（S3）：最坏相位下 L\*=6144 token 就打爆 deadline；tick 初注入 8192 token 都安全。冲击宽度正好一 tick。注入若走引擎 step，必然与 tick 内计算抢同一资源。

4. **打断后的 stale resident KV**（S2）：在 40% 打断先验下，峰值有 24.2% 的 resident KV 是已作废内容，平均驻留 35.6 s，每分钟发生 2.2 次 stale splice（正确性事故）；这些已作废但仍 resident 的 KV 每步 decode 仍按原价付带宽。

## 三类瓶颈与可行域

- **Capacity 瓶颈**：KV pool 字节数 / 单路 working set——在 vanilla 默认语义下最先触达（本仓库 N=12；Metronome N=128 memory cliff，且亚稳、silent failure）。
- **Deadline 瓶颈**：state 被 windowed 或换出后，才成为主导约束（Metronome 加 sliding window 后，临界路数 N\*≈209，小于显存外推的约 500；本仓库历史模拟外推 N=192 / 208，判据 miss > 1%）。
- **注入瓶颈**：效率地板上，一 tick 内计算加上注入的总需求 = 1 时，**N≈57**（历史模拟外推：baseline N=48 已两头坏；48→57 是调度器可争取的空间，超过 57 进入 admission control 领域；真机注入实验见 `PAPER-EXPERIMENTS.md`）。

瓶颈出现顺序是硬件与负载参数的函数，但**在所有现实配置下，capacity 瓶颈都远早于卡的计算能力耗尽**——这是全部机会所在。

## 领域空白（为什么是现在、为什么没人做）

- **Serving 文献**：截至 2026-08，真正的双工 GPU serving 论文只有 Metronome 一篇（无注入、无作废，负载最温顺）；它对 KV 装不下的答案是 sliding window 截断（有损，与注入需要长期驻留冲突）。
- **模型层在为服务侧的缺位买单**：MoshiRAG 明知 mid-context 注入精度更好，却弃用，理由是 "to constrain sequence length"；全部开源双工模型的上下文折合会话时长 ≤20 分钟——领域对 KV 增长的现行答案是"忘掉"。
- **产品层证词**：Seeduplex 自述克服了"高并发下的延迟尖刺与稳定性问题"（解法不公开）；GPT-Live 单会话 ≥1 小时（手段不公开）。
- 五列能力矩阵（tick deadline / batching / KV cache / 注入调度 / 作废语义）中，**"注入的 deadline-aware 放置"与"输入侧作废回收"两列全场空白**——恰好是本负载要素 ② 的两半。

## 与 Metronome 的关系

Metronome（arXiv:2607.02640，2026）是截至 2026-08 唯一的真双工 GPU serving 论文。本仓库与它的关系有六重，性质各不相同——引用时不要混：

| # | 关系 | 内容 |
|---|---|---|
| 1 | **交叉验证**（增强本仓库结论） | 它在真机（Qwen3-Omni-30B FP8 / 96G / 每 2 s 一 tick）独立测得同一瓶颈出现顺序：vanilla 配置下 memory cliff 先到（N=128 亚稳崩溃，GPU utilization 仅约 13–32%）；KV 受限后 deadline 瓶颈 N\*≈209，小于显存外推约 500——与本仓库 S1 的 "N=12 ≪ 192/208" 形态一致（数值巧合不构成校准） |
| 2 | **对照负载**（划定它没覆盖的） | 它测的是双工场景最温顺的负载：每帧存活量恒定、无注入、无作废——本仓库要素 ② 的两半它全空 |
| 3 | **方案种子**（我们从它那里拿走的） | 它的刻意错相实验设置，被本方案升级为调度资源（相位指派 / TDMA）；它的 sliding-window KV 实现的 "state-bounded 世界"，正是已归档思想实验 L1b 的现实版 |
| 4 | **竞争方案**（我们与它正面对比的） | 它对 "KV 装不下" 的答案是 W=1024 sliding window 截断（**有损**，与注入驻留冲突）；conveyor **无损**保全上下文——见 `IDEA-KV-CONVEYOR.md` §四对比表第一行 |
| 5 | **互补可叠加** | 它管 capacity 上限之外（AIMD admission）与有损 cap；本方案在瓶颈约束内扩张 capacity——两者不排斥 |
| 6 | **未来 baseline** | 其开源实验架（vLLM-realtime resumable request + 共享 tick gateway）是本仓库走出模拟器后新实验的 baseline 参照 |

## 方案：用带宽换容量的 tail-KV conveyor

详见 `IDEA-KV-CONVEYOR.md`。

一句话：**每路 tail KV 的母本住在 host DRAM，按时间表每一 tick 用 DMA 搬入 HBM 暂存（H2D），算完即释放；攒满一个完整回合才 commit 为 resident。等效 KV capacity = resident slots M + staging slots P；收益比 P/M = η·B_link·T/M_bytes（模型参数被约掉，纯硬件比值）。**

- **为什么可行，且只在这个场景可行**：周期精确已知（下一 tick = 上一 tick + T）、相位可在 admission 时指派（TDMA）、内容按帧冻结（释放点 = 上一 tick 算完）——三个性质是通用对话 serving 都不具备的。
- **与四个事实的对应**：事实 1 是收益来源；事实 2 升级为编排设计的第一对象（相位指派摊平计算与 DMA 两条需求曲线）；事实 3 的注入 KV 走同一链路、第二优先级、不进引擎 step；事实 4 由 commit 语义从源头消灭（未 commit 的停在 host DRAM，作废直接丢）。
- **收益**：PCIe 5 / 480 ms 一 tick，+24%（净约 20%）；3090 / PCIe 3，+83%（原型信噪比最高）；每 2 s 一 tick（Metronome 口径），约 +100%；80 ms 一 tick 不值得做（+4%）——适用工作点区间是 200 ms 到 2 s 的 thinker 家族。
- **与 Metronome 正交且互补**：它解决 capacity 上限之外（admission）与有损 cap；本方案在瓶颈约束内扩张 capacity 且无损——两者可叠加。

## 明确不做什么（边界）

语音合成头与音频 tokenization；过载区 N 超过产能上限（admission control，Metronome 的地盘）；多卡 prefill/decode 分离（作 baseline 对比而非贡献）；80 ms 锁步家族（收益除以 6）。

效度前提见 `FINDINGS.md` / `PAPER-EXPERIMENTS.md`（最重要：标定模型 1.7B，增益是乐观上界）。
