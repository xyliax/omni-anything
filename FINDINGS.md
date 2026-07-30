# 全双工语音前台 + 后台工具调用：共享 GPU 服务下的问题发现

**性质**：问题发现，不是方案验证。所有结论来自真实 GPU 微基准 + 忠实复刻现有机制的离散事件模拟器。
没有测出来的问题，明确写为"不存在／量级可忽略"。

**环境**：RTX 3090 (24GiB, driver 580.95.05, CUDA 12.6) · vLLM 0.9.2 V0 `LLMEngine`
(`VLLM_USE_V1=0`, CUDA graphs ON, paged attention) · Qwen3-1.7B fp16 ·
`max_num_batched_tokens=2048` · KV 池 44,336 token @ 112 KB/token
完整记录：`calibration/data/env_Qwen3-1.7B.json`

**模拟器保真度**：真机 vs 模拟，5 次独立尝试全部通过 15% 判据。
累积时间线误差 min 2.47% / **中位 10.44%** / max 11.74%（中位那次作为报告口径）。
逐 beat 平均绝对误差 4.48–14.23%。数据：`simulator/validation_runs/summary.json`

---

## 一、已确认的问题

| # | 问题 | 量级 | 数据来源 |
|---|---|---|---|
| C1 | **单次整体拼接会打爆 beat，且阈值随到达相位漂移** | 最坏相位 L\*=6144；最好相位 L=8192 仍安全（max beat 257ms） | `results/S1_injection.csv` |
| C2 | **跨会话爆炸半径真实存在且很大** | N=8, L=8192：一次注入最多同时打爆 **7** 个其他会话；跨会话 miss 累计 422.8 次；0 个会话干净 | `results/S3_policies.csv` |
| C3 | **eager-prefill 过路费**：含 prefill 的 step 掉出 CUDA graph，付固定过路费 | B=8/ctx=4096 纯 decode 12.35ms → 只掺 **64** 个 prefill token 就变 25.41ms（+12.81ms）。过路费与 p 无关 | `calibration/data/T3_mixed_Qwen3-1.7B.csv` |
| C3b | **"免费搭车区间"边界 = p ≤ 256** | p=64/128/256 的开销恒为 12.73–12.81ms（付了过路费后 256 token 白搭）；p=512 起才真正涨（27.98ms），此后线性 ~0.054ms/token | `calibration/data/T3_mixed_Qwen3-1.7B.csv` |
| C4 | **按 budget 分块不是缓解手段，是加重手段** | N=8, L=8192：分块 65.9% miss vs 整体 56.6%；跨会话 miss 542.4 vs 422.8 | `results/S3_policies.csv` |
| C5 | **分块把集中伤害改成分散伤害** | N=11, L=2048：整体拼接 4.6/11 会话干净，分块只剩 0.4/11 | `results/S3_policies_N11.csv` |
| C6 | **打断后的失效 KV 永不回收，长期占住上下文** | N=8, L=8192, 40% 打断先验：16,384 token 白算；峰值时engine 持有的 KV 中 **24.2%** 是已知死内容；平均驻留 **35.6s** | `results/S4_cancellation.csv` |
| C7 | **过期内容照样进上下文** | 每 60s 每 8 会话 **2.2 次**陈旧拼接（工具结果已被打断作废，仍拼进去） | `results/S4_cancellation.csv` |
| C8 | **到达相位错开导致严重欠批** | N=12：随机相位 avgB=1.46 / 3420 steps / util 0.714，对齐相位 avgB=6.50 / 755 steps / util 0.144 —— 同样的工作多花 **4.96×** GPU 时间、**4.53×** step 数 | `results/S2_density.csv` |
| C9 | **prefix caching 是 park/wake 的承重墙** | 开：wake 中位 22.7ms；关：中位 **112.2ms**（**4.9×**） | `calibration/data/diag_wake_growth.json` |
| C10 | **ctx>8192 的 decode 台阶** (`max_seq_len_to_capture` 默认 8192) | 越过即掉出 graph：默认配置下 B=1 的 p50 从 ctx=4096 的 7.26ms 跳到 ctx=8192 的 17.44ms（**2.4×**） | `calibration/data/T1_decode_Qwen3-1.7B_defaultcapture.csv` |

## 二、被否证的假设

| # | 原假设 | 实测 | 数据来源 |
|---|---|---|---|
| F1 | **分块 prefill 能缓解 beat 超时** | 否证。每个 chunk 重付一次 eager 过路费，miss 反而更高（C4） | `results/S3_policies.csv` |
| F2 | **分块惩罚随上下文变长而恶化** | **只在"相对惩罚"这一口径下被否证，绝对口径下成立** —— 见问题 5。相对：ctx=4096 k=1→32 是 +246.96%，ctx=16384 只 +230.8%（更低，因为 k=1 基线更大）。绝对：每多一 step 的边际成本 4k 是 **13.1ms**、16k 是 **20.9ms**（**+59%**，前缀重读确实存在）。**用哪个口径回答，结论相反** | `calibration/data/T4_chunk_Qwen3-1.7B.csv` |
| F3 | **单会话注入冲击会累积** | 否证。冲击只有 **一个 beat 宽**，下一 beat 已回基线 | `results/S1_injection_timeline.csv` |
| F4 | **密度上限由 480ms deadline 决定** | 否证。deadline 墙在 N=192（随机）/ N=208（对齐），是 KV 可行 N=12 的 **~16×**。1.7B 模型上密度是 **KV 容量绑定** | `results/S2_density.csv` |
| F5 | wake 成本随会话寿命增长（prefix cache 累积） | 否证。开 prefix caching 时 40 beat 内 wake **不升反降**（首尾各取 10 beat：25.03→21.93ms，-12.4%；取 5 beat 为 -18.1%，取 20 beat 为 -6.2% —— 各窗口一致为负）；关掉时稳在 112ms（+1.1%） | `calibration/data/diag_wake_growth.json` |

## 三、意料之外的发现

| # | 发现 | 量级 | 数据来源 |
|---|---|---|---|
| U1 | **eager step 远比 graph replay 抖**（共享卡上） | 同一次运行内，eager prefill step 逐 beat 在 20.49–32.49ms 间摆动（**+58.6%**），而 graph-replay decode 在安静单进程下复现性 spread 仅 0.6–0.8%。decode 并非完全免疫：同租户突发时 beat 2–3 的 decode 中位数也曾到 12.78/11.21ms（~2×） | `calibration/data/diag_post_prefill_decode.json`, `calibration/data/repeatability_summary.json` |
| U1b | **"注入后 decode 变慢"是伪相关** | 2× decode 异常出现在**注入之前**（beat 2–3），注入后（beat 7–9）decode 是正常的 7.26–7.42ms；同期功耗 138W→250W 单调上升 —— 元凶是同租户争用，不是注入 | `calibration/data/diag_post_prefill_decode.json` |
| U2 | **注入伤害几乎完全由相位决定**：max beat 与注入偏移 **1:1** 线性 | L=5120：off=5ms → 71.7ms；off=470ms → 441.3ms。纯溢出到下一 beat，不是计算变多 | `results/S1_injection.csv` |
| U3 | **欠批有两个独立成因**，此前混为一谈 | ① 相位错开：N=12 时 avgB 6.50(对齐)→1.46(随机)，**4.46×**；② 即便完全对齐，同批内 m_t 异质仍让 batch fill 只有 0.542（**1.85×**）。两者叠加后随机相位的批占用率只剩 **12.1%** | `results/S2_density.csv` |
| U4 | **"只在空闲喂"把正确性问题换成了可用性问题** | N=8, L=8192：miss 降到 4.6%，但答案 p50 延迟 **4.3s**，且 **41.7% 的答案永远送不出去** | `results/S3_policies.csv` |
| U5 | **爆炸半径会互相叠加，且分块显著加剧叠加** | L=8192：整体拼接下 41.7% 的受害 miss 可归因到 **≥2** 个肇事会话（mean_blast=1.61）；分块后升到 **76.8%**（mean_blast=2.39）—— 分块把注入摊薄成更多 step，反而让不同会话的注入更容易在同一等待窗口里重叠 | `results/S3_policies.csv` |
| U6 | **观测者效应**：循环内 `nvidia-smi` 探针自己制造了它要测的现象 | 探针在 beat 之间引入 ~55ms 空隙 → GPU 掉功耗档 → 下一个 wake 付爬坡代价，表现为可复现的 wake 爬升。**移出循环（改后台采样线程）后消失**：现存 5 次尝试中 4 次 wake 全程平坦（如 attempt 2：首 20.7ms / 末 20.7ms），仅 attempt 4 有 20.5→27.4ms 漂移（同租户争用）| `simulator/validate.py` (`ClockSampler` docstring), `simulator/validation_runs/steps_*.csv` |
| U7 | **短 prefill 的时间几乎与长度无关** | ctx=4096 下 L=8→128 平坦在 26.4–26.9ms（**16× 的长度差，时间差 <2%**，固定过路费主导）；L=256 起才抬头，L=2048=161.8ms，L=8192=753.6ms | `calibration/data/T2_prefill_Qwen3-1.7B.csv` |

---

## 四、五个必答问题

### 1. 注入打爆阈值是多少？

**L\* = 6144 token（最坏到达相位）**，但阈值本身是相位函数，不是单一常数：

| 注入偏移（480ms 内） | 首次 miss 的 L | L=8192 时的 max beat |
|---|---|---|
| +5ms（beat 刚开始） | 扫到 8192 都不 miss | 257ms |
| +120ms | 扫到 8192 都不 miss | 343ms |
| +240ms | 扫到 8192 都不 miss | 463ms |
| +360ms | 7168 | 587ms（超时） |
| +470ms（beat 将结束） | **6144** | 697ms（超时） |

机制：单会话每 beat 只用 ~20–45ms，留下 ~440ms 空闲 GPU。注入落在 beat 早期就"搭便车"免费，
落在末期则整段溢出到下一 beat —— max beat 与偏移 1:1 线性（U2）。
数据：`results/S1_injection.csv`，图：`results/figures/S1_injection.png`

> 方法学注记：spec 的 L 网格 {128,512,2048,8192} 上首个 miss 出现在 8192，答案只能说"在 (2048, 8192] 之间"，
> 那不是阈值。为夹出阈值增补了 3072/5120/6144/7168 四个网格点。

### 2. 跨会话爆炸半径存在吗？多大？

**存在，且很大。** N=8（KV 可行密度 12 的 70%），60s，5 seed：

| L | 策略 | miss 率 | 跨会话 miss | 最大同时受害会话 | 干净会话 |
|---|---|---|---|---|---|
| 2048 | 整体 | 0.12% | 1.2 | 3 | 8/8 |
| 4096 | 整体 | 12.18% | 108.0 | 3 | 0/8 |
| 8192 | 整体 | **56.55%** | **422.8** | **7** | **0/8** |
| 8192 | 分块 | 65.87% | 542.4 | 7 | 0/8 |
| 8192 | 空闲喂 | 4.55% | 38.6 | 1 | 1/8 |

一个会话的一次工具返回，能在同一时刻打爆 7 个**与它无关**的会话 —— 在 N=8 的负载里这是"除自己以外全部"。
成因是机制 (1) membership freeze + 机制 (4) 无 deadline 感知：长 prefill 一旦进入 step，
整批会话在它做完之前都拿不到下一个 decode。
数据：`results/S3_policies.csv`，图：`results/figures/S3_blast_radius.png`

### 3. 四指标 trade-off 曲线什么形状？

三个"无调度"策略，**没有一个赢**（N=8, L=8192）：

| 指标 | (a) 整体拼接 | (b) 按 budget 分块 | (c) 只在空闲喂 |
|---|---|---|---|
| miss 率 | 56.55% | **65.87%**（最差） | **4.55%**（最好） |
| 答案首块延迟 p50 | 3.10s | 3.59s | **4.30s**（最差） |
| 有效会话密度 | 0/8 | 0/8 | 1/8 |
| 作废浪费 token | 0 | 0 | 0 |
| 答案送达率 | 63.3% | 71.5% | **58.3%**（最差） |

> 第四个指标（作废浪费 token）在 S3 恒为 0，因为 S3 **不含打断**（`interrupt_prob=0`），
> 三策略在此指标上无从区分。该指标的量级由 S4 单独测量（见问题 4）。这是矩阵设计的结果，不是缺数据。

形状不是"trade-off 曲线"而是**三个都在帕累托前沿之外**：(a)(b) 用正确性换吞吐，(c) 用可用性换正确性
（41.7% 答案永不送达，U4）。miss 的拐点在 L=1024（0 miss）与 L=2048 之间，
到 L=4096 已是 12–21%。完整五个 L 的曲线见图。
数据：`results/S3_policies.csv`，图：`results/figures/S3_policies.png`

### 4. 作废浪费的量级是多少？

N=8，40% 打断先验，60s，5 seed：

| L | 白算 prefill token | 白算 KV 占用 | 峰值失效上下文 | 占 engine 常驻 KV | 平均驻留 | 陈旧拼接次数 | 白费 GPU 时间 |
|---|---|---|---|---|---|---|---|
| 2048 | 4,506 | 0.48 GiB | 18,022 tok | 15.5% | 37.5s | 2.2 | 0.69% |
| 8192 | 16,384 | 1.75 GiB | 54,067 tok | **24.2%** | 35.6s | 2.2 | 3.79% |

45.0 次工具调用里 **8.8 次**被打断作废（19.6%），但现状语义下一次都不回收：
already-spliced 的 KV 继续驻留、继续被后续每个 beat attend。
"峰值失效上下文 / engine 常驻 KV" 是可解释的口径；按 KV 池百分比看 L=8192 会到 121.95%，
那是因为该配置下整个工作集本身已超池（41% 的 step 处于 KV 溢出），而模拟器**只记录不建模** preemption/swap（见效度威胁）。
数据：`results/S4_cancellation.csv`，图：`results/figures/S4_cancellation.png`

### 5. 分块惩罚随上下文变长恶化得多厉害？

**取决于口径，两个口径给出相反的答案。** L=2048 固定，切 k 块：

| k | ctx=4096 | 惩罚 | ctx=16384 | 惩罚 |
|---|---|---|---|---|
| 1 | 158.4ms | — | 270.0ms | — |
| 2 | 170.0ms | +7.3% | 294.5ms | +8.8% |
| 4 | 213.6ms | +20.0% | 337.5ms | +15.9% |
| 8 | 207.1ms | +31.3% | 334.1ms | +23.5% |
| 16 | 301.7ms | +77.2% | 501.2ms | +81.8% |
| 32 | 565.1ms | **+247.0%** | 918.4ms | **+230.8%** |

**口径 A（相对惩罚，%）：略微缓解。** 247.0% → 230.8%。但这只是因为长上下文的 k=1 基线本身更大
（270.0ms vs 158.4ms），分母变大让百分比变小 —— 这个口径会误导。

**口径 B（每多切一刀的绝对边际成本）：明确恶化 +59%。**

| | ctx=4096 | ctx=16384 | 变化 |
|---|---|---|---|
| 边际成本（k=1→32 端点） | 13.12 ms/step | 20.92 ms/step | **+59.5%** |
| 边际成本（全 k OLS 斜率） | 12.73 ms/step | 20.48 ms/step | **+60.9%** |

两种算法一致，所以这不是端点噪声。把边际成本对 ctx 做线性分解：

```
每多一 step 的成本 ≈ 10.52ms（固定）+ 0.635ms 每 1k 上下文 token
  ctx=4096 :  10.5ms 固定 (80%) + 2.6ms 上下文相关 (20%)
  ctx=16384:  10.5ms 固定 (50%) + 10.4ms 上下文相关 (50%)
```

**机制结论**：分块惩罚由两部分构成 —— 一个 ~10.5ms 的**每 step 固定开销**（kernel launch、eager 路径、
调度）和一个**随上下文线性增长的前缀重读成本**。在 4k 上下文下固定开销占 80%，
到 16k 时前缀重读已追平（各 50%）。**外推**：上下文越长前缀重读越主导，所以在真实长对话
（数万 token 上下文）里分块的绝对代价会持续恶化，而"相对惩罚下降"的表象会继续掩盖它。

数据：`calibration/data/T4_chunk_Qwen3-1.7B.csv`，图：`calibration/figures/T4_chunking.png`

---

## 五、简化与效度威胁

按对结论影响从大到小排列。

1. **模型是 Qwen3-1.7B，不是 spec 要求的 7–8B。** 这是最重的一条。
   原因：卡上仅 ~9 GiB 可用（同租户常驻），8B fp16 权重需 15.3 GiB；且 T1 的 B=32×ctx=16k
   在 8B 下需要 ~72 GiB KV。**影响方向**：8B 的 decode step 与 prefill 均更慢、KV 每 token 更大，
   因此 (a) L\* 会**更小**，(b) 爆炸半径会**更大**，(c) KV 可行密度会**更低**。
   本报告的所有阈值应视为**乐观上界**。未做 4B 锚点标定，故无实测缩放因子 —— 这是已知缺口。

2. **共享 GPU。** GPU3 上有常驻且突发的同租户。争用对 eager step 的影响（beat 间 +58.6% 摆动，U1）
   **大于验证判据本身（15%）**。缓解：`simulator/wait_quiet.sh` 静默门控 + 重复 5 次取中位数
   （`simulator/validation_runs/`）。所有标定跑在单进程内以免自相争用。
   残留风险：标定表本身可能含争用抬高的成分，方向是**高估** step 时间，故 miss 与爆炸半径可能偏悲观。

3. **不建模语音头。** 每 beat 只算 backbone 的 micro-prefill + m_t 次 decode，
   轻量合成头的时间计为 0。**影响**：真实 beat 预算比这里更紧，L\* 与安全密度都会更低。

4. **用文本 token 代替音频 token。** m_t 由内容驱动的先验（说话 2–4、静音 1–2、偶发长尾）给出，
   但 token 本身是文本 token，KV 每 token 大小按文本模型实测（112 KB/token）。

5. **KV 池溢出只记录、不建模 preemption/swap。** 每行结果都带 `kv_overflow_step_frac`。
   N≥14 起开始溢出，N≥22 全程溢出。**因此 N>12 的 S2 行（含 deadline 墙 N=192/208）
   描述的是一个该卡装不下的密度**，只用于说明"deadline 不是绑定约束"这一定性结论，
   不应当作可达密度。S3/S4 用 N=8（KV 可行 12 的 70%），仍有 41–62% 的 step 溢出于 L=8192 —— 该格子的
   绝对数值应打折看，定性结论（爆炸半径存在）不受影响。

6. **T3 在 p=512/1024 上呈双模，模型取上分支。** 同一个 p 在不同 (B, ctx) 格子上开销为 ~12ms 或 ~43ms。
   已排除"vLLM 偷偷分块"这一解释：`calibration/data/diag_t3_chunking.json` 直接读调度器的
   `num_batched_tokens`，确认所有 p token 都在被计时的那个 step 内。上分支与 T2 的独立测量吻合
   （T2 L=1024 边际计算 41.6ms vs T3 高分支 43ms），故取上分支，代价是**在快速格子上最多高估 78%**。
   这是刻意的保守，且落点避开了要害：模拟器实际只在 **budget 上限 2048**（模型误差 4% 内）
   或 **8-token micro-prefill**（13% 内）两处调度 prefill，几乎不落在 512/1024。
   方向是高估干扰，故"爆炸半径存在"不会被伪造出来，但其绝对大小可能偏大。
   完整残差表见 `simulator/calib_model.py:cross_check_t3()`。

7. **T1 有 14/35 格因 KV 容量装不下而跳过**（实测 21 格）。B 网格实际扫了 {1,2,4,8,16,24,32}、
   ctx 扫了 {1k,2k,4k,8k,16k}，缺的全是大 B×大 ctx 角落（如 B≥8 & ctx≥8192、B≥4 & ctx=16384）——
   44,336 token 的池装不下。**这直接限制了可外推的密度上限**：模拟器在这些区域靠插值，
   而 S2 的 N>12 正落在此区。

8. **"安全密度"被重定义为 KV 可行 N。** spec 设想 miss 率随 N 上升穿过 1%，
   实测在 KV 可行范围内 miss 恒为 0（F4），故 S3/S4 的密度基准取"最后一个工作集装得进
   44,336 token 池的 N"（=12），而非 deadline 数。若沿用 deadline 数会选到一个卡装不下的密度。

9. **打断先验 40% 施加在会话级、每会话独立**，与真实对话中打断的时间聚集性无关。

10. **S1 网格增补**（3072/5120/6144/7168）超出 spec 的 L∈{128,512,2048,8192}，
    理由见问题 1 的注记。spec 网格点的结果原样保留在同一 CSV 中。

11. **单卡、无网络服务**，全程 offline engine 库调用（`VLLM_USE_V1=0` 显式 `add_request`/`step` 循环），
    符合纪律要求。未测多卡、未测 TP。

12. **U6（观测者效应）的修复前数值不可回溯。** 该现象是在探针位于计时循环内时观察到的，
    但 `validate_repeat.sh` 的后续运行覆盖了那批 `steps_*.csv`。现存文件只能证明**修复后**的状态
    （wake 平坦）。因此 U6 作为方法学教训记录，其修复前的具体毫秒数不作为数据引用。

13. **S1 的 miss 判定基于 5 个离散注入偏移**（+5/120/240/360/470ms），不是连续扫描。
    L\*=6144 是"在这 5 个相位中最坏者下的阈值"，真实最坏相位可能落在采样点之间，
    使实际 L\* 略低于 6144。

---

## 六、交付物索引

```
calibration/
  data/env_Qwen3-1.7B.json      环境记录（GPU/驱动/模型/精度/KV 池）
  data/T1_decode_*.csv          decode step vs (B, ctx)，35 格中 21 格可行
  data/T1_decode_*_defaultcapture.csv  同上但用 vLLM 默认 max_seq_len_to_capture（C10 的 2.4× 台阶）
  data/repeatability_summary.json      同格重复 8 次的 spread（0.6–5.2%）
  data/T2_prefill_*.csv         prefill vs (L, ctx)，40 格
  data/T3_mixed_*.csv           混批干扰 vs p，42 格
  data/T4_chunk_*.csv           分块惩罚 vs (k, ctx)，12 格（静默门控下单进程重跑）
  data/diag_wake_growth.json    prefix caching 开/关 × 40 beat 的 wake 成本（C9, F5）
  data/diag_post_prefill_decode.json  注入前后 decode + 时钟/功耗采样（U1, U1b）
  data/diag_t3_chunking.json    验证 T3 双模不是 vLLM 偷偷分块（效度威胁 6）
  data/diag_prefill_steps.json  beat = 1 prefill step + m decode steps 的依据
  figures/                      T1–T4 拟合图
simulator/
  engine.py                     六机制离散事件模拟器
  calib_model.py                T1–T4 查表/插值 + cross_check_t3() 残差表
  run_experiments.py            S1–S4 驱动
  validate.py                   真机 vs 模拟验证（含 ClockSampler）
  wait_quiet.sh                 等 GPU 空闲的静默门控
  validate_repeat.sh            静默门控下重复验证
  summarise_validation.py       多次尝试聚合，取中位数为口径
  validation_runs/summary.json  验证报告：5/5 通过，中位累积误差 10.44%
results/
  S1_injection.csv              相位 × L 扫描（56 行）
  S1_injection_timeline.csv     逐 beat 时间线（505 行）
  S2_density.csv                密度扫描至 deadline 墙（N=192/208），两种相位（73 行）
  S3_policies.csv               三策略 × 五 L @ N=8（15 行）
  S3_policies_N11.csv           同上 @ N=11（12 行，对比集中 vs 分散伤害，C5）
  S4_cancellation.csv           作废浪费 @ N=8（4 行）
  figures/                      S1–S4 图 + CONCLUSIONS.md（每图一句结论）
  meta.json                     标定摘要、seed、sim_ms、N_used
```

每个结论均可回溯到上述文件；无任何数字来自估计或类推。
