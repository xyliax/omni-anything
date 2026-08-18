# 双工负载的执行形状特化：固定尺寸增量 prefill 的整步图化

未进入事实层的设计研究；快照日期：2026-08-18（取代 2026-08-07 的初版设想）。本文自包含，不预设读者了解任何讨论过程。实测数字标注出处等级：**【实测】**= 可由 `results/baseline/runs/`、`results/conveyor/runs/` 保留 run 的 artifact 重算；**【推导】**= 实测 + 硬件公开参数的算术；**【假设】**= 待「立项前置」（§六）实验裁决。立项前置未全部通过前，本设想不投入实现。

## 一、观察：引擎的图化机制在双工操作点上系统性错配

**负载形状**（实测栈：vLLM 0.23 + Qwen2.5-Omni-7B + RTX 3090，tick=2s，N=8）：全双工语音下，每会话每 tick 提交一片 2 秒音频，引擎为它执行一次**增量 prefill**——query 长度恒定（2 秒音频 ≈ 53 个音频 token + 固定模板文本，是负载的物理常数，不随任何东西变化）——随后 decode 精确 25 个 token。错开相位 gateway（conveyor 引擎机制之一）把 8 路的提交时刻均匀铺在周期内，因此**每个引擎步至多含一个 prefill**，与它共批的只有其他会话的零星 decode（实测共批 decode 数 k ∈ 0..4）。

**引擎的图化机制**：CUDA graph 把一步的全部 kernel 发射录制后整体回放（CPU 从 ~300 次发射降到 1 次），约束是录制与回放的张量形状一致。vLLM 用两种模式覆盖动态负载：**FULL**——整步录制（attention 在图内），只给「均匀 query 形状」的步（decode：每序列 q=1，形状仅由 batch 决定；KV 长度与 block table 作为持久 buffer 输入，不影响形状）；**PIECEWISE**——在每层 attention 处把模型切开，只录形状单态的稠密段（QKV 投影/MLP/norm 只认总 token 数），attention 留在图外逐层发射，吃掉任意的序列组成。

**三个实测错配**（同一保留 run 的 worker.log 配置转储与 scheduler trace）：

1. **图梯子被引擎几何截断**：PIECEWISE 的捕获上限由 `max_graph_size = min(max_num_seqs*2, 512)` 推导（vLLM 安装包 `vllm/config/vllm.py`）——本栈 `max_num_seqs=16` → 上限 **32 token**；而每 tick 的 prefill 步实测 p50 = **64 token**【实测】。
2. **PIECEWISE 图是死资产**：启动时捕获 7 张混合图，运行期命中 **0 次**【实测】。全部步的分派结果：88-90% 纯 decode 步走 FULL 图，**~10% 的步（恰好是每 tick 的关键路径步）完全无图**【实测】。
3. **多模态 encoder 被硬开关排除**：`cudagraph_mm_encoder=False` 的上游理由是「多模态输入变长」——本负载音频定长 2s，该理由不成立；音频塔每步全程 eager。

**错配的代价**【实测】：无图 prefill 步 p50=65ms / p95=77ms（n=480），对照已图化 decode 步 p50=23ms / p95=26ms（n=3789）。步长的可赎回部分估算【推导】：LM 权重读地板 ~17ms（15.6GB ÷ 936GB/s；64 token 位于 3090 ridge point 之下）+ encoder GPU 地板 ~3-8ms（~0.6B 参数 × ~100 帧）+ 步内 CPU ~5ms（同步调度税，decode 步 23ms − GPU 账 18ms 实测），其余 **~25-40ms** 为发射间隙、逐层 attention 元数据准备与 encoder 裸奔开销——这是本设想的候选奖池，确切归属由 G1 探针裁决。

## 二、主张：特化的分类轴应是 query 形状稳定性，而非 prefill/decode 相位

通用引擎不给 prefill 开 FULL 是理性的，三个原因：

1. **chunked prefill 固定的是上限不是取值**：长 prompt 按预算切分后每个请求的最后一片是任意长的余数，短 prompt 根本不切——q 的分布 ≈ prompt 长度分布本身；
2. **签名是组成不是标量**：一步可打包多个请求的片（如 200+112+173 + 若干 decode），需要冻结的是整个组成，组合空间爆炸；
3. **垫充经济学不对称**：decode 步是权重读主导的 memory-bound，垫充 batch 蹭同一次权重读 ≈ 免费（这是 decode FULL 梯子成立的根据）；prefill 成本 ∝ q，把余数垫到整片是烧真算力。

**双工负载把三个条件全部翻转**：q 是物理常数（53，非预算切分产物，无余数问题）；签名被错开相位压缩为可枚举的 (q=53, k)，k∈0..4（**可枚举性是引擎机制制造的，不是负载白送的**——机制协同）；唯一要垫的是 k，属 decode 型免费垫充。因此双工增量 prefill 在图化经济学上**等价于一个 q=53 的胖 decode**，有资格享受 FULL 待遇——而现有引擎的分派器看到「含 prefill 的步」一律送 PIECEWISE，按相位而非形状稳定性分类，结构性看不见这一类负载。

**引擎内部的先例（待 G2 核实细节）**：vLLM 为投机解码的 verify 步（每序列 q = 推测数+1，均匀）已把 FULL 捕获从 q=1 推广到均匀 q>1（capture 尺寸推导含 `num_speculative_tokens`）。即：引擎已承认「稳定的 q>1 值得整步图化」，但只识别**引擎自己制造的**稳定性；负载制造的同等稳定性被 prefill 标签挡在门外。与 verify 步的差异即本设想的机制增量：混合签名（1×53 + k×1，非均匀）、多模态 embedding 注入（音频 placeholder 走 inputs_embeds）、encoder 前向在步内。

## 三、方案骨架（三级，各自独立开关，off = 现行行为逐字节不变）

- **L1 · 配置臂**：`cudagraph_capture_sizes` 显式扩到 ≥64——稠密段进 PIECEWISE。用现有机制、零新代码；**不是贡献，是消融下界**（同时回答「这不就是改个参数吗」：改参数只买到稠密段，28 道 attention 缝与 encoder 在配置能力边界之外）。
- **L2 · encoder 定长进图**：复用上游 encoder-cudagraph flags（`encoder_cudagraph_token_budgets` 等）按固定音频形状捕获音频塔；对 audio tower 的适用性未验证【假设】。
- **L3 · FULL-prefill（核心）**：按 (q, k) 签名整步捕获——attention 在图内，KV 长度 / block table / slot mapping 走持久 buffer（与 decode FULL 同一机制）；分派器扩展识别固定混合签名；**签名失配一律回退现行路径**（会话首片含系统模板、q 不同，单列签名或直接回退；warm-start seed 步排除在外）。工程可行性的关键验证点：所用 attention kernel 的网格维度不依赖 KV 长度（FlashAttention 系 varlen 的网格由 q 块数决定、KV 为循环边界）【推导，G2 验证】。

## 四、预期收益（按角度，出处等级标注）

**角度一 · 步级**：prefill 步 65 → ~35ms【假设，奖池区间见 §一】；步时方差 p95/p50 从 1.18 收敛至 ~1.1（已图化 decode 步为 1.13【实测】）——整步回放对主机 CPU 竞争脱敏，而该敏感性有实测事故背书（预取拷贝曾使 FE 从 221ms 膨胀至 270ms，见 `docs/findings.md` H7）。

**角度二 · 主收益：非周期注入的可容纳量（schedulable slack）**。用实时调度语汇：双工前台是周期性硬 deadline 任务；后台 agent/toolcall 结果注入（本项目问题定义的第二负载，冻结先验见 `docs/experiments.md`）是**非周期任务**，其调度方式是 slack stealing——塞进前台步链的空隙。每周期步链核账【实测】：72 步 = 63 decode×23ms + 8 prefill×65ms ≈ 1969ms / 2000ms 周期，**当前 slack ≈ 30ms/周期**——千 token 级注入（prefill 速率 ~0.2ms/token【实测，seed prefill】）需摊数十个周期或直接击穿 tick，**实际不可调度**。L3（−30ms × 8 prefill 步）叠加伴生工作项 async-compatible park（§五，回收 decode 步 ~4-5ms 同步税 × 63 步）后：**slack ≈ 520-580ms/周期 ≈ 可容纳 ~2.6-2.9k token/周期**，一个 4k token 的工具结果注入响应 ~2 个周期【推导】。这使注入负载首次从「不可行」变为「可调度」，且方差收敛（角度一）允许 slack-stealing 的准入判断收窄安全边界。

**角度三 · 明确不主张的**：**N\* 容量**——容量的稀缺资源是显存，属 park / bandwidth-for-VRAM 主张的地盘；步链高占用是错开相位刻意铺开计算 + 同步调度税的产物，本设想的容量角色仅是移除这个自致天花板、**支撑而非竞争**显存主导的容量叙事。TTFA（取现货交付的结构性一片滞后）与显存占用均不受影响。

## 五、与主线机制的关系

- **依赖**：错开相位制造签名可枚举性——没有槽轮就没有 (53, k) 的小签名空间，特化可行性是引擎自身机制的产物（与「park 依赖同步调度」同型的机制互文）。
- **伴生工作项 · async-compatible park**：park 目前强制同步调度（异步下在途投机步对刚释放块存在 use-after-free 竞态），使每个 decode 步暴露 ~5ms CPU【实测】。将 auto-park 延迟一个引擎步即可关闭竞态窗口、恢复上游异步流水线（估 ~30 行）。它是 slack 收益中 decode 部分的**更便宜来源**——L3 的收益核算必须以它为基线净额扣除（G3）。
- **与预取（`docs/findings.md` H7）**：图化使 tick 关键步对 CPU 竞争脱敏，缩小预取拷贝与 FE 相互干扰的受害面——H7 遗留的「净收益被 FE 膨胀抵消」问题与本设想在同一根因上会师。

## 六、立项前置（gates；全部通过才投入 L3 实现）

- **G1 · 三臂探针 + 步分解**：eager / 现状 / L1 各一个 run；trace 采集器加 schedule() 时长站点（一行 wrapper）。产出：65ms 拆成稠密发射 / attention 缝 / encoder / 步内 CPU 四份，奖池归属定量。
- **G2 · 近亲排查**（约半天源码 + 文献）：vLLM spec-decode 均匀 q 捕获路径的分派语义、对混合签名的实际行为、inputs_embeds 与图的兼容性；TRT-LLM 静态 shape profile、SGLang 等的横向刷新。产出：related work 边界与贡献净额。
- **G3 · async-park 探针**：延迟一步释放 + 异步调度回开，一个 run 验证正确性与回收量。
- **判定规则**：G1/G3 之后 L3 的净奖池 < ~15ms/步，或 G2 发现混合签名捕获已有先例覆盖 → 本设想降级为工程注记 + 上游默认值修正建议，归档；否则 L3 原型立项。

## 七、已知麻烦与解法

| 麻烦 | 解法 |
| --- | --- |
| 会话首片签名不同（含系统模板，q=53+T） | 单列一档签名，或首片走回退路径（每会话仅一次，收益无关紧要） |
| 多模态 embedding 注入进图 | 音频特征经 inputs_embeds 持久 buffer 喂入（G2 验证该路径与图的兼容性） |
| park / prefix cache 与图共存 | block table 本就是 FULL 图的 buffer 输入，park 改变的是 buffer 内容不是形状——与 decode FULL 已有语义一致 |
| 捕获显存与启动时间 | 签名 ~5-10 档；现有 12 张图合计 0.10 GiB【实测】，量级可控 |
| 「开了但没生效」静默失效 | runner issue 扫描加步时分布断言（prefill 步 p50 超阈值即 issue），或启用 vLLM 自带 cudagraph_metrics |
| 会话死亡 / 签名漂移 | 失配回退现行路径 + 计数（与 park/prefetch 的拒绝计数同形） |

## 八、配置面与结构影响审计

配置：`ConveyorConfig.specialize: str = "off"`（`off | piecewise | full`）+ 签名表常量；CLI `--specialize`；manifest 完整记录。off = 现行行为逐字节不变，为消融对照臂。

| 触碰面 | 内容 | 不变量保持 |
| --- | --- | --- |
| `experiments/conveyor/worker/engine_patch/` | 新模块（签名分派 + 捕获管理），与 park/reload 同注入面 | park/reload/transfer 语义不动 |
| `experiments/conveyor/config/` | specialize 旋钮 + 校验 | 默认 off |
| `tracekit/` | schedule() 时长站点（行语法向后兼容） | 既有 grammar 不变 |
| runner issue 扫描 | 步时分布断言 | 与零 park / 零 prefetch 扫描同形 |
| `lab/`、baseline、pin | 零触碰 | — |

消融矩阵：`--specialize off|piecewise|full` 与既有机制开关（park / prefetch / 相位）正交，全组合可跑。
