# EVIDENCE：实验证据索引（白名单版，2026-08）

**性质**：问题发现与方案前提的实验证据。所有结论来自真实 GPU 微基准 + 忠实复刻现有机制的离散事件模拟器；每个数字可回溯到数据文件，无任何数字来自估计或类推。

**本文档与 idea 的关系**：仓库已收敛到一个方案候选——`IDEA-KV-CONVEYOR.md`（带宽换显存的尾部 KV 传送带）。本文档只保留对该问题定位与该方案有支撑作用的实验；2026-08 白名单清理移除的实验（注入的计算侧安放策略对比、爆炸半径、分块 vs 整段等）属已放弃的研究线，数据与结论可在 git 历史（commit 5020583 及之前）找回，**不应再作为现状引用**。

**环境**：RTX 3090 (24GiB, driver 580.95.05, CUDA 12.6) · vLLM 0.9.2 V0 `LLMEngine`
(`VLLM_USE_V1=0`, CUDA graphs ON, paged attention) · Qwen3-1.7B fp16 ·
`max_num_batched_tokens=2048` · KV 池 44,336 token @ 112 KB/token（28 层 × 8 KV 头 × 128 × 2B × K/V 两份；**比 7B thinker 的 56 KiB 还大不是笔误**——Qwen2.5-Omni-7B 的 GQA 只有 4 个 KV 头，是 1.7B 的一半）
完整记录：`calibration/data/env_Qwen3-1.7B.json`
⚠️ 实验时点为 2026-07（vLLM V0）；此后 vLLM 已有 resumable requests、SGLang 有 streaming sessions。后续新实验的 baseline 应对齐新原语，参照 Metronome（arXiv:2607.02640）的开源 harness。

**模拟器保真度**：真机 vs 模拟，5 次独立尝试全部通过 15% 判据。累积时间线误差 min 2.47% / **中位 10.44%** / max 11.74%（中位那次作为报告口径）。逐 beat 平均绝对误差 4.48–14.23%。数据：`simulator/validation_runs/summary.json`

---

## 零、实验 → idea 的支撑地图

| 实验 | 结论一句话 | 支撑 IDEA-KV-CONVEYOR 的哪一环 |
|---|---|---|
| T1–T4 标定 | 步时定律 + 13ms 组成税 + 前缀重读线性项 | v1（重算方案）否证的成本基础；"重算=自我注入"的实测单价 |
| **S1 密度** | KV 可行 N=12 ≪ deadline 墙 N=192/208（16×）；随机相位比对齐多花 4.96× GPU 时间 | 问题前提①"显存先绑定一个数量级"；编排设计①"相位指派是调度资源" |
| **S2 作废** | 峰值 24.2% 常驻 KV 是死内容、驻留 35.6s、陈旧拼接 2.2 次/分 | 方案 3.4"提交语义 × 作废"：未提交注入停 DRAM，从源头消灭死 KV 驻留 |
| **S3 注入冲击** | 最坏相位 L\*=6144 打爆拍；伤害与相位 1:1；冲击仅一拍宽 | 注入不能走引擎步、必须走链路的动机；链路三级混合关键性里"注入 KV 搬运"这一级的负载模型 |

---

## 一、标定物理（T1–T4 + 诊断）

| # | 事实 | 量级 | 数据来源 |
|---|---|---|---|
| C1 | **步时定律**：decode 步时 = 固定项 + 批大小项 + 上下文字节项 | ≈ 6.52ms + 0.106ms×B + 0.155µs×Σctx（残差 <5%） | `calibration/data/T1_decode_Qwen3-1.7B.csv` |
| C2 | **eager-prefill 过路费（组成税）**：含 prefill 的 step 掉出 CUDA graph，付固定过路费 | B=8/ctx=4096 纯 decode 12.35ms → 只掺 **64** 个 prefill token 就变 25.41ms（**+12.81ms**）。过路费与 p 无关 | `calibration/data/T3_mixed_Qwen3-1.7B.csv` |
| C2b | **"免费搭车区间"边界 = p ≤ 256** | p=64/128/256 开销恒为 12.73–12.81ms；p=512 起才真正涨（27.98ms），此后线性 ~0.054ms/token | 同上 |
| C3 | **短 prefill 时间几乎与长度无关** | ctx=4096 下 L=8→128 平坦在 26.4–26.9ms（16× 长度差 <2% 时间差）；L=2048=161.8ms，L=8192=753.6ms | `calibration/data/T2_prefill_Qwen3-1.7B.csv` |
| C4 | **分块的每步边际成本随上下文恶化**（前缀重读）：每多一 step ≈ 10.52ms 固定 + 0.635ms/1k ctx | 4k ctx 边际 13.1ms/step，16k ctx 20.9ms/step（**+59%**）；相对惩罚口径（247%→231%）会误导 | `calibration/data/T4_chunk_Qwen3-1.7B.csv` |
| C5 | **prefix caching 是 park/wake 的承重墙** | 开：wake 中位 22.7ms；关：**112.2ms**（4.9×） | `calibration/data/diag_wake_growth.json` |
| C6 | **ctx 达到 8192 的 decode 台阶**（`max_seq_len_to_capture` 默认 8192） | 掉出 graph：B=1 p50 从 7.26ms（ctx=4096）跳到 17.44ms（ctx=8192，2.4×）。注意 `TIMELINES.md` L3/L4 的 ctx=8k 步时（~7.9ms）是**调大捕获上限后**所测，两者不矛盾 | `calibration/data/T1_decode_*_defaultcapture.csv` |
| C7 | **eager 步远比 graph replay 抖**（共享卡） | eager prefill 逐 beat 摆动 +58.6%；graph decode 单进程 spread 仅 0.6–0.8% | `calibration/data/diag_post_prefill_decode.json` |
| C8 | **观测者效应**（方法学）：循环内 `nvidia-smi` 探针自己制造 wake 爬升 | 移出循环（后台采样线程）后消失，5 次尝试中 4 次 wake 全程平坦 | `simulator/validate.py`（`ClockSampler`） |

对 idea 的直接用途：**v1（阈值提交 + 重算）的否证**建立在 C3（4k 重算 = 330ms prefill = 自我注入）与 C2（每发重算都是付过路费的混合步）之上；步时定律 C1 是模拟器扩展（验证计划第 1 条）的现成标定。

## 二、S1 密度：显存先绑定，相位是资源

N 扫描（随机/对齐两种相位，60s，5 seed）。数据：`results/S1_density.csv`，图：`results/figures/S1_density.png`。

1. **KV 可行密度 N=12**（最后一个工作集装得进 44,336 token 池的 N）；deadline 墙在 **N=192（随机）/ N=208（对齐）**——**16×**。墙的判据：**miss 率首次越过 1% 的最小 N**（随机 N=192 时 2.27%、前一格 N=176 仅 0.51%；对齐 N=208 时 11.79%、前一格 N=192 仅 0.48%；首次非零 miss 出现在随机 160 / 对齐 192——引用时请带判据）。1.7B 上密度是 KV 容量绑定，deadline 不是绑定约束。
2. **单会话占空比仅 4–9%**（每拍 1 个 micro-prefill 步 + 2–4 个 decode 步，~20–45ms/480ms）——卡装不下的时候远没跑满。
3. **相位错开导致严重欠批**：N=12 随机相位 avgB=1.46 / util=0.714，对齐相位 avgB=6.50 / util=0.144——同样的活多花 **4.96×** GPU 时间。欠批两成因：①相位错开（4.46×）②对齐后批内 m_t 异质仍限 fill=0.542（1.85×）。
4. 全卡忙时 **64.7%** 是各路分开付的 micro-prefill 过路费（含 prefill 步 1410 步 × 20.3ms vs 纯 decode 2164 步 × 7.2ms）——欠批浪费的主体是 prefill 税没人拼单。

→ idea 对应：问题定义第 1 条（显存绑定 + 大量空闲）；编排设计第 1 条（相位指派同时摊平计算与 DMA 两条需求曲线）。Metronome 在真栈（30B FP8/96G/2s 拍）上独立复现同一墙序（vanilla N=128 显存悬崖，windowed 后死线墙 N\*≈209 < 显存外推 ~500）。

## 三、S2 作废：死 KV 常驻且持续计税

N=8，40% 打断先验，60s，5 seed。数据：`results/S2_cancellation.csv`，图：`results/figures/S2_cancellation.png`。

| L | 白算 prefill token | 峰值失效上下文占常驻 KV | 平均驻留 | 陈旧拼接次数/分 | 白费 GPU 时间 |
|---|---|---|---|---|---|
| 2048 | 4,506 | 15.5% | 37.5s | 2.2 | 0.69% |
| 8192 | 16,384 | **24.2%** | 35.6s | 2.2 | 3.79% |

- 45.0 次工具调用里 8.8 次（**19.6%**）被打断作废，现状语义下一次都不回收：already-spliced KV 继续驻留、继续被每拍 attend——**每步 decode 都为死字节付带宽原价**。
- **每分钟 2.2 次陈旧拼接**是正确性事故：工具结果已被用户打断作废，仍拼进上下文，模型说出已否决的答案。

→ idea 对应：3.4"提交语义 × 作废"——注入以未提交态停 DRAM，确认说出才提交常驻；40% 被打断的从未进池，作废=DRAM 直接丢。

## 四、S3 注入冲击：伤害由相位决定，一拍宽

N=8 会话环境中、对其中一路注入的 L×相位扫描（其余 7 路正常跑拍）。数据：`results/S3_injection.csv`（56 行）+ `results/S3_injection_timeline.csv`（逐拍 505 行），图：`results/figures/S3_injection.png`、`results/figures/S3_timeline.png`。

1. **最坏相位 L\*=6144**：整段拼回在拍末注入时 6144 token 即打爆死线；拍初注入则 8192 都安全（max beat 257ms）——阈值是相位函数，不是常数。
2. **max beat 与注入偏移 1:1 线性**（L=5120：off=5ms→71.7ms，off=470ms→441.3ms）：纯溢出到下一拍，不是计算变多。
3. **冲击只有一拍宽**：下一拍已回基线，无累积（否证了"冲击会累积"假设）。

| 注入偏移 | 首次 miss 的 L | L=8192 max beat |
|---|---|---|
| +5ms | >8192 不 miss | 257ms |
| +240ms | >8192 不 miss | 463ms |
| +360ms | 7168 | 587ms（超时） |
| +470ms | **6144** | 697ms（超时） |

→ idea 对应：几千 token 的注入走引擎步必然与拍死线冲突（除非恰好落对相位）——这是"注入 KV 走 DMA 链路、不进引擎步"的动机；1:1 相位线性给出链路调度里注入级作业的死线余量模型。

## 五、被否证的假设（保留的部分）

| # | 原假设 | 实测 | 数据来源 |
|---|---|---|---|
| F1 | 密度上限由 480ms deadline 决定 | 否证。deadline 墙 N=192/208 是 KV 可行 N=12 的 ~16×，密度是 KV 容量绑定 | `results/S1_density.csv` |
| F2 | 单会话注入冲击会累积 | 否证。冲击一拍宽，下一拍回基线 | `results/S3_injection_timeline.csv` |
| F3 | wake 成本随会话寿命增长 | 否证。开 prefix caching 时 40 拍内 wake 不升反降（-12.4%）；关掉稳在 112ms | `calibration/data/diag_wake_growth.json` |
| F4 | "注入后 decode 变慢" | 伪相关。2× decode 异常出现在注入**之前**，元凶是同租户争用 | `calibration/data/diag_post_prefill_decode.json` |

## 六、简化与效度威胁（按影响从大到小）

1. **模型是 Qwen3-1.7B，不是 7–8B**（卡上仅 ~9GiB 可用）。8B 的 decode/prefill 更慢、KV 每 token 更大 → L\* 更小、KV 可行密度更低。**所有阈值应视为乐观上界**；无 4B 锚点，无实测缩放因子。
2. **共享 GPU**：同租户争用对 eager 步的影响（+58.6%）大于验证判据（15%）。缓解：`wait_quiet.sh` 静默门控 + 5 次取中位。残留方向：高估 step 时间。
3. **不建模语音头**：真实拍预算更紧，L\* 与安全密度更低。
4. **文本 token 代替音频 token**：m_t 按内容先验（说话 2–4、静音 1–2），KV 112KB/token 按文本模型实测。
5. **KV 池溢出只记录、不建模 preemption/swap**。N≥14 起溢出，N≥22 全程溢出。**S1 的 N>12 行（含 deadline 墙 N=192/208）描述的是该卡装不下的密度**，只用于"deadline 不是绑定约束"这一定性结论。S2/S3 用 N=8（KV 可行 12 的 70%），L=8192 格仍有 41–62% step 溢出，该格绝对数值打折看。真实 unbounded 引擎在此区间的行为是显存悬崖硬僵死（Metronome 实测），不是弹性排队——见 `TIMELINES.md` L1b 前提域标定。
6. **T3 双模取上分支**：在快速格子上最多高估 78%，但落点避开要害（实际只在 budget=2048 或 8-token micro-prefill 两处调度 prefill）。残差表：`simulator/calib_model.py:cross_check_t3()`。
7. **T1 有 14/35 格因 KV 装不下跳过**（大 B×大 ctx 角落靠插值）——限制可外推密度上限，S1 的 N>12 正落在此区。
8. **"安全密度"定义为 KV 可行 N**（=12），非 deadline 数（后者选到装不下的密度）。
9. **打断先验 40% 施加在会话级、每会话独立**，无时间聚集性。
10. **S3 网格增补**（3072/5120/6144/7168）超出原 spec 的 L∈{128,512,2048,8192}，为夹出 L\* 阈值；spec 网格点结果原样保留在同一 CSV。
11. **单卡、offline engine 库调用**（显式 `add_request`/`step` 循环），未测多卡/TP。
12. **观测者效应（C8）修复前数值不可回溯**：作为方法学教训记录，不作数据引用。
13. **S3 的 miss 判定基于 5 个离散注入偏移**，真实最坏相位可能落在采样点之间，实际 L\* 可能略低于 6144。

## 七、交付物索引

```
calibration/
  data/env_Qwen3-1.7B.json      环境记录（GPU/驱动/模型/精度/KV 池）
  data/T1_decode_*.csv          decode step vs (B, ctx)，35 格中 21 格可行
  data/T1_decode_*_defaultcapture.csv  vLLM 默认 capture 下的 2.4× 台阶（C6）
  data/repeatability_summary.json      同格重复 8 次 spread（0.6–5.2%）
  data/T2_prefill_*.csv         prefill vs (L, ctx)，40 格
  data/T3_mixed_*.csv           混批干扰 vs p，42 格
  data/T4_chunk_*.csv           分块惩罚 vs (k, ctx)，12 格
  data/diag_*.json              诊断（wake、注入前后 decode、T3 分块核查、beat 结构）
  figures/                      T1–T4 拟合图
simulator/
  engine.py                     六机制离散事件模拟器
  calib_model.py                T1–T4 查表/插值 + cross_check_t3()
  run_experiments.py            S1–S3 驱动
  trace_batches.py / trace_injection.py / trace_density.py / trace_composition.py / trace_saturation.py
                                TIMELINES.md 各时间线的生成脚本
  validate.py / wait_quiet.sh / validate_repeat.sh / summarise_validation.py
  validation_runs/summary.json  验证报告：5/5 通过，中位累积误差 10.44%
results/
  S1_density.csv                密度扫描至 deadline 墙（N=192/208），两种相位（73 行）
  S2_cancellation.csv           作废浪费 @ N=8（4 行）
  S3_injection.csv              相位 × L 扫描（56 行）
  S3_injection_timeline.csv     逐拍时间线（505 行）
  figures/                      S1–S3 图 + CONCLUSIONS.md（每图一句结论）
  meta.json                     标定摘要、seed、sim_ms、N_used
```
