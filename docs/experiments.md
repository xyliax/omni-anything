# 评估协议与复现

<a id="evaluation-questions"></a>
## 本轮评估

本轮采用三个主比较系统、三组实验。实验三复用主系统并增加两个变体，共五种配置；以下是已确认的实验协议，不表示实现已经齐备或收益已经测得。证据状态见 [Findings](findings.md#current-state)。

| 实验 | 比较对象 | 要回答的问题 |
| --- | --- | --- |
| 实验一：容量与服务代价 | 全驻留、按需回载、Pilarius | 降低 GPU KV 峰值驻留是否转化为更多按期完成的周期工作，延迟与搬运代价是多少 |
| 实验二：动态加入退出 | 全驻留、Pilarius | 用户自然错峰进入、历史长度不同且不断退出时，容量收益是否仍成立 |
| 实验三：机制消融 | Pilarius、自然 phase 变体、按需回载、提交后预取变体 | 主动 phase 安排与提前恢复分别贡献什么 |

核心结论需要同时满足“多服务会话”和“实际完成新增工作”。仅降低驻留支持资源节省；更多会话伴随更多超期或未完成，只支持容量与服务质量的取舍。准入保护本身不构成容量提升。

<a id="workload-and-platform-matrix"></a>
## 共同设置

本轮先固定一套模型、输入/输出路径、GPU 与主机配置完成三组实验。具体配置在正式运行前记录；当前原型、示例模型与硬件不是最终论文范围。配置资料见[平台记录](#single-gpu-selection)，现有实现见[复现附录](#reproducibility-appendix-current-prototype)。

**本次实施配置。** 作者已选择先用 MiniCPM-o 4.5 的现有音频输入／固定预算文本输出路径，Qwen2.5-Omni-7B 作第二模型；两者的 revision 和几何仍由 `experiments/shared/model.py` 单份持有。选择依据是周期/历史语义与可验证的执行路径，不按预期收益筛模型。MiniCPM 的[官方双工路径](https://huggingface.co/openbmb/MiniCPM-o-4_5)包含连续输入与语音输出，当前选择不包含该完整原生路径，所有结果须注明实际执行范围，不据此宣称原生双工或语音交付收益。其他模型按历史保留、周期余量、后端接入与完整输出成本筛选，不因已有适配器直接排除。

先完成实际平台的复制正确性、有效链路和模型工作量校准，再确定并发点及逐出预算。实现顺序为共同时间表与计量、最大上下文规划及计划切换、三个匹配系统与两个消融变体、恢复后模型语义核验，最后运行独立重复。运行环境安装与功能检查不计作正式比较；校准点、失败点和独立评估点均须按来源保留，不能承诺预定增益倍率。

比较固定模型及精度、最大上下文、参考历史保留语义、周期、输入内容与时间戳、每会话生成规则、后端批处理预算和观测设置。同并发控制核对实际输入、生成和保留量；容量比较固定外部提供的负载与每会话工作要求，完成的总工作量作为结果，不能要求两边相等。输入流使用固定素材与逐会话片段起点，避免所有会话播放完全相同的片段而形成意外共享。

最大上下文沿用模型/后端配置，计入输入与生成；实际历史不能越界或被隐式裁短。周期目标为下一 tick 前完成。会话在上限内增长时复用计划，加入退出时修正；不增加增长预测、续期或违约容忍参数。

<a id="evaluated-systems"></a>
<a id="comparison-families"></a>
## 三个主系统

| 系统 | 设置 | 比较目的 |
| --- | --- | --- |
| GPU 全驻留 | 相同历史保留在 GPU；按共同最大上下文及独立校准确定静态准入上限，超出则拒绝 | 相对合理配置的常规系统，是否提高承载能力 |
| 按需回载 | 复用主机备份与部分逐出实现，在当前工作需要缺失 KV 时恢复 | 普通卸载的容量与恢复等待代价 |
| Pilarius | 驻留规划、主动 phase 安排与下一 tick 前恢复 | 有计划的驻留和恢复能否增加及时完成的工作 |

<a id="fairness-checklist-for-the-protocol"></a>
全驻留与按需回载的准入上限在各自独立校准后固定，不能故意压低，也不能把无限制接入后崩溃作为唯一基线。Pilarius 按当前候选计划的可行性准入。各系统可承载的数量不同；输入时间表、资源和服务约定相同。全驻留使用自然错开的周期与合理的后端批处理设置。按需回载是匹配实现的控制组，不据此声称已经比较全部已有卸载系统。

端到端对照报告调度、批形状及执行量的实际差异。机制消融除目标变量外固定 phase、逐出量、主机副本策略、传输路径、调度模式和工作量。关闭一个开关不自动构成公平控制。

<a id="capacity-experiment"></a>
## 实验一：容量与服务代价

1. 选择约五个并发点，覆盖低负载、全驻留容量边界及更高负载。每点独立启动，三个系统各重复三次。校准数据与正式重复分开。
2. 使用固定会话集，按逐会话输入起点形成自然错开的周期；启动与初始化完成后，记录共同观测窗口内的执行。全驻留超过准入上限的会话正常拒绝，分别报告 offered 与 admitted。
3. 保留上下文随真实输入和生成增长的过程，覆盖接近上限的历史。记录时间与实际长度，不能只测会话刚开始时的状态。
4. 同一批运行同时提供同并发资源代价、并发扩展、上下文增长和低负载开销，不另设独立扫描。

输出会话接纳/拒绝数、按时/超期/未完成周期、完成延迟分布、GPU KV 峰值、主机内存、双向传输字节和恢复等待。容量边界附近结合整组周期工作与分配观察判断瓶颈；新增会话的实际完成检验计算余量是否可用，不能只凭 GPU 利用率推断。

长历史预置只用于能正确完成初始化的配置，各系统使用相同可重建内容并记录实际分词长度，排除初始化输出。现有预加载屏障期间暂停逐出，要求所有初始状态先驻留；若扫描中的高并发点装不下，则该扫描统一从共同的较短历史自然增长，不以初始化失败替代正式容量结果。同一条容量曲线固定初始历史和观测时长，避免把不同历史负担当成扩容收益。预留后续真实输入与生成空间，上下文到限单列记录。

<a id="dynamic-arrival-experiment"></a>
## 实验二：自然错峰的动态加入退出

### 时间表与输入

生成一份离线时间表，记录 `session_id, start_time_s, duration_s, input_stream_id, input_offset`。同时保存随机种子、平均新会话到达率 `lambda`、统一会话时长 `tau`、到达窗口 `H`、周期 `T` 和素材版本。时间表只定义外部输入，不保存系统为会话选择的 phase。

相邻新会话的间隔服从均值 `1/lambda` 的指数分布，累加得到上线时刻。所有会话使用相同 `tau`，从选定素材起点按原速持续输入；不同上线时间自然形成不同的会话年龄和周期起点，不额外给每轮输入添加随机抖动。

```python
rng = Random(seed)
start = 0.0
for session_id in count():
    start += rng.expovariate(lambda_per_second)
    if start >= arrival_window_s:
        break
    emit(session_id, start, duration_s, input_stream_id, input_offset)
```

上述为数据生成伪代码；素材及其起点由固定的逐会话映射选取，在各系统间一致。事件按绝对时间回放；新会话和后续输入不等待前一个请求完成。发生器记录计划与实际发送时刻，避免客户端发送落后被误认为系统接住了负载。

离线生成器 `experiments/conveyor/schedule.py` 已实现上述外部时间表：素材记录 SHA-256、采样格式与长度，offset 以 sample 计；到达与素材分配使用独立随机流，保留亚周期到达时刻，不写系统 phase 或准入结果。当前入口接受足以覆盖会话的真实 WAV，不循环短素材；同一 seed 的输入映射不随到达率改变。该格式由显式开放回放入口消费，不能直接交给准入后播放的旧客户端。开放回放在共同源时钟上发送，记录每段计划/实际发送时间，不顺延迟到输入的 deadline；超出准入能力拒绝一次，未完成周期保留在计量中。操作入口见 [runner 说明](../experiments/conveyor/AGENTS.md#exogenous-schedule)。

### 自然 phase 与主动 phase

自然错峰来自会话自身的输入时钟。例如上线时刻为 `s_i`，第一个周期输入在 `s_i + T` 齐备，则自然 tick 为 `s_i + T, s_i + 2T, ...`。保留亚周期精度，不把所有会话对齐到同一个全局 tick，也不人为让 baseline 同步开始。

Pilarius 回放同一份原始输入时间表，在应用允许的范围内分配 phase。原始输入片段及其就绪时间保持一致，缓冲与首次对齐等待单列记录；两系统的用户可见延迟均从同一输入时间基准计算。phase 确定后保留原 tick 与 deadline，排队或恢复等待不能顺延它们。自然 phase 变体保留各会话输入时钟，仅关闭主动重排。

### 运行与比较

只比较全驻留与 Pilarius。选择低负载、全驻留边界附近、更高负载三个到达率；以 `lambda * tau` 作为外部平均在线需求的参考量，在无拒绝且启动阶段过去后才可解释为平均活跃数。每个到达率使用三份独立种子的时间表，并在系统间配对回放。

到达窗口覆盖启动和会话更替，至少持续两个会话时长；停止产生新用户后，已有会话继续到各自预定输入结束时间。结束后按共同终止规则结算剩余工作、释放状态；排空时间单列，不计入负载期吞吐。提前到达上下文限制、错误与未完成工作分别记录。拒绝后不自动重试；发生器知道的未来到达与结束时间不提供给 planner。

输出各系统的 offered/admitted/rejected 会话、实际周期完成量与超期、延迟、输入积压，以及活跃会话数和 KV 占用的时间曲线。加入退出带来的计划切换等待计入服务代价。

<a id="ablation-matrix"></a>
## 实验三：简单成对消融

选择实验一中一到两个代表性资源边界点，固定并发、输入、历史范围和逐出预算，不做参数组合网格。

| 因果问题 | 比较 | 唯一改变的策略 |
| --- | --- | --- |
| 主动 phase 安排是否有额外作用 | 自然 phase 变体 vs. Pilarius | 自然输入时钟 vs. 主动 phase 分配；均保留提前恢复 |
| 提前恢复是否减少关键路径等待 | 按需回载 vs. 提交后预取变体 vs. Pilarius | 当前需求、输入提交后、下一 tick 前三个恢复触发时机；phase 和其他策略一致 |

只新增自然 phase、提交后预取两个配置，复用按需回载与 Pilarius 的匹配运行。记录峰值分配、周期完成情况和恢复等待，并关联目标分配、复制开始/完成、tick、计算开始与生成完成事件。只改变恢复触发时机时不同时改变逐出量或工作量；配置名不能代替触发时刻核验。

<a id="measurement-semantics"></a>
<a id="service-and-capacity-metrics"></a>
## 测量语义

| 指标 | 统一口径 |
| --- | --- |
| 会话服务 | 分开统计 offered、admitted、rejected、正常完成与异常结束；拒绝不算已接纳会话的 deadline miss，但属于未获得服务的需求 |
| 周期完成 | 以本次输入关联的模型生成完成事件 `c(i,k)` 计数；对原计划 tick `r(i,k)`，按时条件为 `c(i,k) <= r(i,k+1)`；分列按时、超期和未完成 |
| 周期完成延迟 | `c(i,k)-r(i,k)`；提交后时间 `c-a` 只作诊断，同时保留提交延迟、首次 phase 对齐等待和输入积压 |
| 用户可见延迟 | 从原始输入时间基准到相关结果交付；模型完成与交付分开，不能用空响应、旧缓冲结果或 RPC 返回代替新工作完成 |
| GPU KV | 统计不可供其他会话使用的物理块峰值；共享块只计一次，恢复目标从分配时即计入；有效内容与分配空间区分 |
| 主机与搬运 | 主机副本占用、H2D/D2H 字节和恢复等待；传输窗口与纯 DMA 时间区分 |
| 实际工作 | 输入量、生成量、保留历史、重算及实际 batch 形状；相同配置名不证明工作相同 |

报告完整曲线与运行间变异，不增加允许超期比例或自动服务等级判定。延迟分布与完成/失败计数一起报告；崩溃、超时和不再产生模型进度的运行不能删去，也不能以停止后的零工作作为低延迟。有限时长结果不构成无限时长保证。

网络暂按固定延迟分析；合成、播放与客户端处理不由这一假设覆盖。具体完成事件随所评估输出路径登记。最大上下文按输入与生成共同计量，上限内增长不触发滚动续期。

<a id="profiling"></a>
详细事件追踪用于解释实验一的边界点及实验三的成对差异；与主要性能采集分开并检查扰动。scheduler 墙钟时间不等同 kernel 忙时，H2D 发起到完成上报也不等同纯链路占用。

<a id="correctness-and-quality-protocol"></a>
## 正式运行前的核验

先对齐各系统的实际生成、保留语义、调度控制和模型完成事件；做短运行核验 KV 内容、逻辑块位置、历史覆盖、就绪依赖、会话退出与资源释放，记录非确定性控制。输出 token 哈希用于辅助诊断，不以逐 token 相等作为 KV 搬运正确性的独立门槛。具体状态安全要求由[设计验收场景](system.md#implementation-handoff)持有，不另加一组性能实验。

共用时间表回放、接纳/结束记录和未来 tick 恢复触发由开放回放入口执行；旧 `push` 预取不能代替未来 tick 策略，既有 `deadline_met` 不能直接代表本次模型完成。当前生成上限差异与初始化约束见[复现附录](#executed-decode-difference)。完成核验后才能执行正式比较。

<a id="run-protocol"></a>
## 运行与交付

实验一约五个并发点、三个系统、每点三次独立运行；实验二三个到达率、两个系统、每个到达率三份配对时间表；实验三仅在选定代表点补充两个变体，并复用条件匹配的主系统运行。

固定源版本与展开配置，记录素材、种子、初始状态、预热、输入与观测窗口、终止规则和实际事件。各数据点启动 fresh worker；已有会话或同一运行里的多个周期不当作独立重复。失败与超时保留原始记录，未完成工作按共同观测窗口结算。

论文依次呈现设置与公平性、容量及服务代价、动态加入退出、机制消融。同并发代价、上下文增长与低负载开销来自上述运行。正式结果登记到 [Findings](findings.md)，本文件只持有配置和协议。

## 配置资料

以下保存背景估算、平台配置与既有复现资料；它们不扩充上述三组评估，也不代表已经获得实测结果。

<a id="cross-hardware-projections"></a>
### 跨硬件条件估算

Background Table 1 使用 MiniCPM-o 4.5 的公开最大上下文，先计算各卡全驻留的内存会话上限，再将该会话数作为一个完整 batch，估算主干 prefill + decode 的执行时间与效率敏感性；周期占比在跨模型表中统一呈现。表内 GPU 选择覆盖不同容量与显存带宽；不列 PCIe 速度。模型与设备来源见[外部参数记录](references/minicpm-o-4.5-kv-geometry.md#table-one-sources)。以下均为**未标定的解析场景估计**，不是项目实测、可直接部署的准入上限或完整输出管线的时限保证。

**固定上下文与容量计算。** 主干 BF16 KV 每位置 144 KiB，公开配置 `L_max=40960`，所以每会话主干状态 `K=5.625 GiB`。另计公开 full-attention 语音解码器的最大 KV：`2*20*12*64*2*4096=0.234375 GiB`；这是辅助状态的保守预留，不把语音 token 按主干 KV 几何计算。每会话两类状态合计 `K_sess=5.859375 GiB`。再统一预留 `R=20 GiB` 给全部权重、其他状态、工作区和运行时；该合计预算仍是假设，实际后端须实测，未完整逐项覆盖的开销不能当作已验证。按名义容量近似 `M=80/96/141/192 GiB`，取 `N_mem=floor((M-R)/K_sess)`。这里不声称厂商 GB 标签严格等于 GiB，也不将名义容量视为驱动可分配字节数。

**周期负载与 batching。** `T=1s`；每会话增量 prefill 十个已经编码好的主干输入位置，随后执行四次单位置 decode forward。正常语速约三至四个文本 token/秒支持这一工作量级，不是 token 硬上界；四次 forward 是显式计账约定，可包含最后输出 token 的 KV 提交，不把 prefill 产生的首 token 再加成额外工作。所有会话同批执行，每卡 batch size 等于其 `N_mem`；不是将单会话延迟乘以并发，也不假设每张卡服务相同并发。容量预留按 `L_max`，最后一个近上限更新从至多 `L_max-14` 个已保留位置开始；时间估算统一用 `L_max` 近似 attention 长度，不让运行超过上限，也不表示达到上限后还能无限继续。prompt/control 位置需包含在实际长度中；本表十位置内容输入未额外计入控制 token，真实路径应补齐相应工作。

**计算与流量模型。** 将主干分为每层投影/MLP、输出 head 和 attention。设层数 `z=36`、hidden `h=4096`、MLP intermediate `i=12288`、query heads `a=32`、KV heads `v=8`、head dimension `d=128`、词表 `V=151748`。由公开配置推导：

- 投影与 MLP 参数 `P_body=z*(2*h*a*d+2*h*v*d+3*h*i)=6945767424`；包含 Q/K/V/O 和三组 gated MLP 矩阵。
- 输出 head 参数 `P_head=h*V=621559808`；BF16 矩阵字节 `W_body=2*P_body`、`W_head=2*P_head`，合计约 15.135 GB。输入 embedding 不是每个 forward 全表扫描，已由总权重容量预算覆盖，不重复作为整表读取流量。
- `q` 为当前 forward 中每会话新处理的位置数：prefill 用 `q=10`，每次 decode 用 `q=1`。body FLOPs 为 `2*N*q*P_body`；head 只计算末位置 logits，为 `2*N*P_head`；attention 两次矩阵乘 FLOPs 近似 `4*N*q*z*a*d*L_max`。
- 同批共享矩阵权重，每次 forward 的权重读取为 `W_body+W_head`，不是 `N*(W_body+W_head)`。不同会话各自的历史仍须读取，attention 字节近似 `N*K`。假设优化后的 GQA kernel 复用共享 KV heads，短增量 prefill 的十个 query 复用一次历史读取；额外读取需通过敏感性或实测修正。

对 body、head、attention **分别**取 `max(bytes/B_eff, FLOPs/F_eff)`，再相加；不能对整个网络只取一次 max 并假设不同阶段完全重叠。`B_eff=eta_B*B_GPU`、`F_eff=eta_F*F_GPU`。两张表的主场景统一取 **`eta_B=0.80, eta_F=0.25`**，作为显式效率假设；这两个数不是设备实测效率、经公开数据标定的参数、置信区间或新增系统参数。外部内核及模型利用率的定义与适用条件见[带宽效率参考](references/periodic-model-cost-sources.md#显存带宽效率的外部参考)。较低带宽效率仍在敏感性中报告；提高带宽效率不等于提高算力效率。带宽采用十进制 TB/s；算力采用 dense BF16/FP32 累加参考，禁止混用稀疏翻倍值、FP8/FP4 AI TOPS。

高效 attention 内核的显存带宽利用量级及其实现依赖见[外部参考](references/periodic-model-cost-sources.md#显存带宽效率的外部参考)；该来源支持高效率场景的合理性，不替代目标配置标定。

`F_GPU` 依次为 A100 SXM 312、H100 SXM 989.5、RTX PRO 6000 Server 约 240、H200 SXM 989.5、MI300X 1307.4 TFLOP/s。RTX 的约 240 是按官方 FP32 120 TFLOP/s 和同类 GB202 架构公开的 dense BF16/FP32-accumulation 与 FP32 约 2:1 比例推导的参考，不是该 SKU 已明确公布或实测的 BF16 峰值；不把官网未区分累加精度的 1 PFLOP 数字直接代入。不同软件内核是否达到假设效率须独立标定，跨厂商解析比较不表示原型已在这些设备运行。

令 `t(q)` 为上述三个部分的时间和，则 `t_prefill=t(10)`、`t_decode=4*t(1)`、`t_PD=t_prefill+t_decode`，周期占比为 `t_PD/T`，剩余预算为 `T-t_PD`。未显式建模的 activation 流量、KV 增量写入、norm/softmax/采样、kernel launch、输入编码、语音生成和调度等成本不因此变成零；剩余预算须覆盖它们及状态恢复，不能直接称为实测 GPU idle 或完整周期 compute slack。

| GPU（名义容量） | 显存带宽（TB/s） | 内存会话上限 = batch | 主干执行时间（ms） | 周期占比 |
| --- | ---: | ---: | ---: | ---: |
| A100 SXM（80GB） | 2.04 | 10 | 241 | 24.1% |
| H100 SXM（80GB） | 3.35 | 10 | 141 | 14.1% |
| RTX PRO 6000 Blackwell Server（96GB） | 1.60 | 12 | 360 | 36.0% |
| H200 SXM（141GB） | 4.80 | 20 | 185 | 18.5% |
| MI300X（192GB） | 5.30 | 29 | 233 | 23.3% |

主干执行时间合并 prefill 和四次 decode，包含模型化的矩阵计算与显存访问成本，不是纯 FLOPs 计算时间；不重复列合计或剩余时间。显示带宽保留两位小数、时间取整到 ms、占比保留一位小数；计算仍使用原始参数，各列从未舍入值独立取整。GPU 容量的上限与计算承载能力是不同量：`N_mem` 仅来自空间；即使主场景全部 `t_PD<T`，也未证明所有卡在真实完整管线中均先受容量限制。

**RTX 行的原因核算。** 该行使用 96GB RTX PRO 6000 Blackwell Server，不是 RTX 6000 Ada。主场景的有效显存带宽为 `0.8*1597=1277.6 GB/s`；batch 为 12，而 A100/H100 行为 10。单次 decode 的共享矩阵权重加独立历史 KV 约为 `W+12*K=87.6 GB`，三个分项均受带宽约束，因此一次 batch decode 约需 `87.6/1277.6=68.6 ms`；四次 decode 加 prefill 得 `274.3+85.5≈360 ms`。其中五次历史 KV 读取约占 284 ms，即总估计的 79%；batching 平摊权重读取，不能平摊不同会话的历史。把 RTX 的算力参考提高至 480 或 1,000 TFLOP/s 时，总估计分别降至约 346 或 343 ms；固定相同 batch 10 时，原参考下约为 308 ms。该核算说明本场景主要受显存流量影响，不构成设备实测排名；各卡在自身容量上限运行，工作量不同。

**敏感性。** 固定容量和工作量，将 `(eta_B,eta_F)` 从较快的 `(0.80,0.40)` 改到较慢的 `(0.40,0.15)`，五行的 `t_PD` 范围分别约为 `234–476 / 141–282 / 349–710 / 180–365 / 229–463 ms`。这些是假设变化，不是测量误差条；实际值也可能超出范围。下方代码还在 `eta_F=0.25` 下报告 70% 和 50% 带宽效率。保持主场景效率但将每个 attention 阶段 KV 读取流量加倍，五行变成约 `426 / 254 / 643 / 342 / 440 ms`；若同时降至 50% 带宽效率，RTX 行约为 1.01 s，会超过周期，说明效率与 KV 复用假设都必须验证。`R=18–22 GiB` 时，应重新取整 batch；辅助 TTS 缓存若使用窗口而非最大全注意力，也须按匹配配置重新计算，不能只保留有利结果。

以下标准库代码复算表内数值及敏感性，不运行模型、不产生性能证据：

```python
from math import floor

GiB = 2**30
layers, hidden, intermediate = 36, 4096, 12288
heads, kv_heads, head_dim, vocab = 32, 8, 128, 151748
limit, reserve = 40960, 20
body = layers * (2*hidden*heads*head_dim + 2*hidden*kv_heads*head_dim
                 + 3*hidden*intermediate)
head = hidden * vocab
main_kv = 2*layers*kv_heads*head_dim*2*limit
speech_kv = 2*20*12*64*2*4096
# capacity: assumed GiB; bandwidth: rated TB/s; matrix reference: TFLOP/s
# RTX matrix reference is inferred, rather than a verified SKU peak.
devices = [
    ("A100 SXM", 80, 2.039, 312),
    ("H100 SXM", 80, 3.350, 989.5),
    ("RTX PRO 6000 Blackwell Server", 96, 1.597, 240),
    ("H200 SXM", 141, 4.800, 989.5),
    ("MI300X", 192, 5.300, 1307.4),
]

def estimate(n, bandwidth, compute, eta_b=0.80, eta_f=0.25, kv_reads=1):
    B, F = eta_b*bandwidth*1e12, eta_f*compute*1e12
    def phase(q):
        dense = max(2*n*q*body/F, 2*body/B)
        logits = max(2*n*head/F, 2*head/B)
        attention = max(4*n*q*layers*heads*head_dim*limit/F,
                        kv_reads*n*main_kv/B)
        return 1000*(dense + logits + attention)
    return phase(10), 4*phase(1)

for name, capacity, bandwidth, compute in devices:
    n = floor((capacity-reserve)*GiB/(main_kv+speech_kv))
    prefill, decode = estimate(n, bandwidth, compute)
    total = prefill + decode
    faster = sum(estimate(n, bandwidth, compute, 0.80, 0.40))
    slower = sum(estimate(n, bandwidth, compute, 0.40, 0.15))
    bw70 = sum(estimate(n, bandwidth, compute, 0.70, 0.25))
    bw50 = sum(estimate(n, bandwidth, compute, 0.50, 0.25))
    double_kv = sum(estimate(n, bandwidth, compute, kv_reads=2))
    double_kv_bw50 = sum(estimate(n, bandwidth, compute, 0.50, 0.25, kv_reads=2))
    print(name, "batch", n, "prefill, decode, total ms, cycle %, remaining ms;"
          " faster, slower, BW70, BW50, double KV, double KV BW50 ms",
          *(round(x, 1) for x in
          (prefill, decode, total, total/10, 1000-total,
           faster, slower, bw70, bw50, double_kv, double_kv_bw50)))
```

**后续标定协议。** 用实际可分配显存和非 KV/辅助 KV 分配替换容量假设；在相同上下文、输入位置数、decode forward 数及 batch 下测 body、attention 和整段 prefill/decode，再加入其余模型和服务阶段。对独立配置验证效率、流量复用及瓶颈预测。窗口策略、分组/phase 或批处理方式变化后重新计账。解析估计、标定预测和实测结果分开标注；该表不冻结实验模型、平台或论文研究范围。

<a id="cross-model-projections"></a>
### 跨模型周期占比与公开实测核查

Background Table 2 扩展前表的容量计算和分阶段 roofline，行沿用同一组 GPU，列使用不同模型主干。每格先用模型自身的配置上下文计算 KV，再以该卡可容纳的会话上限形成 batch；括号报告 batch，主值为估算周期占比。参数和外部实测见[来源记录](references/periodic-model-cost-sources.md)。所有数字仍是**未标定的主干解析估算**，没有转换成完整多模态管线或部署准入保证。

**模型与工作量。** MiniCPM-o 完全沿用前节。Qwen2.5-Omni 使用 Thinker 的配置上下文 32768；每秒 25 个编码后音频位置来自报告中的 40 ms/位置，四次文本 decode 和一秒更新则是本表的受控工作量假设，不是模型原生双工协议或生成上界。预填充按增量执行、复用已有 KV，真实后端能否保留同语义前缀须验证。Moshi 使用原生每 80 ms 一次 temporal Transformer forward，保留配置中的 3000 个时间位置；多 codebook 不乘成多次 temporal forward。每种模型均只计长期历史所在主干：Qwen Talker、Moshi depth Transformer、各模型输入编码与波形输出不计入时间，但容量预留包含其权重与下述辅助 KV。

| 模型 | 主干上下文 | 周期（ms） | 每周期主干工作 | 主干 KV（GiB/会话） | 辅助 KV（GiB/会话） | 非逐会话 KV 预留 R（GiB） |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| MiniCPM-o 4.5 | 40960 | 1000 | 10 位置增量 prefill + 4 次 decode | 5.625 | 0.234375 | 20 |
| Qwen2.5-Omni-3B | 32768 | 1000 | 25 位置增量 prefill + 4 次 decode | 1.125 | 0.375 | 16 |
| Qwen2.5-Omni-7B | 32768 | 1000 | 25 位置增量 prefill + 4 次 decode | 1.75 | 1.5 | 28 |
| Moshi 7B | 3000 | 80 | 1 次 temporal forward | 1.46484375 | 0.0078125 | 20 |

此参数表保留复算所需精度，论文表内占比只保留一位小数。Qwen 的 R 分别高于其存储 dtype 下约 11.15/20.83 GiB 的完整权重；Moshi 的 R 另覆盖主 LM 之外的 Mimi 权重等。剩余工作区、非 KV 辅助状态和运行时预算仍为场景假设，不是实测容量。Qwen 两个模块分别预留其配置最大 KV，Moshi 另预留 8 MiB 的 Mimi/depth KV；这些不代表所有缓存必然同时到顶。容量近似与 Table 1 相同，将名义 GB 标签作为 GiB 预算。末次更新须留出新位置空间，不能在已到最大上下文后继续增长而越界。

统一沿用前表的 `eta_B=0.80, eta_F=0.25` 假设，对所有模型和 GPU 使用相同效率。主表报告这一场景，较低效率的结果见敏感性；公开实测对照也使用相同主场景参数重新计算，不将这一选择称为经实测标定。

| GPU（同 Table 1 的 SKU） | MiniCPM-o 4.5 | Qwen2.5-Omni-3B | Qwen2.5-Omni-7B | Moshi 7B |
| --- | ---: | ---: | ---: | ---: |
| A100 SXM 80GB | 24.1% (10) | 34.5% (42) | 24.3% (16) | 58.5% (40) |
| H100 SXM 80GB | 14.1% (10) | 15.0% (42) | 10.9% (16) | 35.6% (40) |
| RTX PRO 6000 Blackwell Server 96GB | 36.0% (12) | 55.9% (53) | 38.1% (20) | 92.7% (51) |
| H200 SXM 141GB | 18.5% (20) | 24.1% (83) | 17.2% (34) | 47.5% (82) |
| MI300X 192GB | 23.3% (29) | 27.9% (117) | 20.2% (50) | 59.7% (116) |

**解释口径。** 表用于检查假设场景中余量是否跨组合出现，同时在敏感性中保留不成立的组合。小主干或较少 KV heads 可容纳更多会话，并不自动缩短容量上限处的 batch 时间。Qwen 大量辅助 KV 预留也会降低 batch 和主干占比，不能被解释为完整模型的吞吐优势。主表所有主干占比均低于 100%，但 Moshi 的高更新频率仍提供边界例子：RTX 主场景约需 74.2 ms，仅余约 5.8 ms 给未计入阶段；92.7% 不能称为“一小部分”。跨模型主干估计不能证明所有硬件/模型与完整管线都存在余量，更不能通过删去不利模型来获得该结论。

沿用前表的效率敏感性 `(eta_B,eta_F)=(0.80,0.40)` 至 `(0.40,0.15)`，RTX 上 Qwen 3B 的占比约从 43.0% 到 100.0%，Moshi 约从 91.6% 到 183.2%。固定 `eta_F=0.25`，将带宽效率降至 70% 或 50%，RTX 上 Moshi 分别约为 104.7% 或 146.6%。接近周期的估计对假设敏感；全矩阵敏感性由下方代码复算，不把这些区间当成实测误差界。

**公开实测对照。** 先复算外部 benchmark 的实际工作量，再比较，不能把单会话短上下文延迟直接乘成表内数据。

1. Qwen 官方 BF16、A100 80GB、batch 1 测试包括初始 prefill 和 2048 个输出。取其 Qwen2.5-3B/7B-Instruct 作为相同相关矩阵/KV 几何的 Thinker 代理；不是 Omni 管线实测。初始 prefill 的因果 attention 使用平均长度 `(P+1)/2`，再逐位置累加 2047 次 decode。源未说明 A100 形态，分别使用 PCIe 1.935 TB/s 和 SXM 2.039 TB/s。预填充的 activation、重复读取和运行时仍未显式计入，此对照只能检查一阶模型的量级。

| 代理模型 | 输入 / 输出位置 | 估算吞吐范围（tok/s） | 官方 vLLM 实测（tok/s） | 估算相对实测偏差 |
| --- | --- | ---: | ---: | --- |
| Qwen2.5-3B-Instruct | 1 / 2048 | 249.3–262.7 | 127.61 | +95.4% 至 +105.9% |
| Qwen2.5-3B-Instruct | 30720 / 2048 | 149.7–155.4 | 105.88 | +41.4% 至 +46.7% |
| Qwen2.5-7B-Instruct | 1 / 2048 | 109.0–114.9 | 84.28 | +29.4% 至 +36.3% |
| Qwen2.5-7B-Instruct | 30720 / 2048 | 71.4–74.2 | 70.33 | +1.6% 至 +5.5% |

范围来自两种 A100 SKU，不是置信区间。中间输入长度 6144/14336 也复算并保留在下方代码输出中；八个模型/长度点、两种 SKU 的吞吐高估约为 1.6%–105.9%，短上下文 3B 的预测约为实测的两倍。当前代理对照不能将 80% 标定为本表配置已达到的效率。该偏差也不能作为 Table 2 每格的误差界：最大 batch、增量前缀复用、其他 GPU 与后端都未匹配。官方同页的 Transformers 速度更低，在上述四个端点约比该估算慢 2.7–8.5 倍，表明后端效率足以改变余量，不能只引用 vLLM 来声称普遍成立。

2. MiniCPM-o 的 RTX 4090 F16 公开值为约 38 ms/token。假设 batch 1、短历史，并按同一 80% 有效带宽估计矩阵读取，约为 `15.135 GB/(0.8*1008 GB/s)=19 ms/token`，约为公开值的一半。公开 batch/上下文不全，且这里只估计矩阵读取，不能称为同配置误差测量，也不能把它用作最大上下文校准或高效率假设的实测支持。
3. Moshi 的 L4 最低约 200 ms 是含算法延迟的整体交互延迟，不能等同 80 ms 更新的 GPU 服务时间。本轮未找到可直接校验其最大保留窗口、容量上限 batch 的公开主干计时，因此该列明确保留为未校验边界估计。

以下标准库代码**接在前节 Table 1 的代码后运行**，复用其 `devices`，计算 Table 2、效率敏感性和外部吞吐对照；不运行模型或生成性能证据：

```python
# name, layers, hidden, intermediate, query heads, KV heads, head dim,
# vocabulary, retained context, reserve GiB, auxiliary KV GiB, prefill, decode, period s
models = [
    ("MiniCPM-o 4.5", 36, 4096, 12288, 32, 8, 128, 151748,
     40960, 20, 0.234375, 10, 4, 1.0),
    ("Qwen2.5-Omni-3B", 36, 2048, 11008, 16, 2, 128, 151936,
     32768, 16, 0.375, 25, 4, 1.0),
    ("Qwen2.5-Omni-7B", 28, 3584, 18944, 28, 4, 128, 152064,
     32768, 28, 1.5, 25, 4, 1.0),
    ("Moshi 7B", 32, 4096, 11264, 32, 32, 128, 32000,
     3000, 20, 8/1024, 0, 1, 0.080),
]

def model_geometry(model):
    _, z, h, i, a, v, d, V, *_ = model
    return z*(2*h*a*d + 2*h*v*d + 3*h*i), h*V, 4*z*v*d

def model_phase(model, n, q, length, bw, tf, eta_b=0.80, eta_f=0.25):
    body_params, head_params, kv_per_position = model_geometry(model)
    _, z, h, i, a, v, d, *_ = model
    B, F = eta_b*bw*1e12, eta_f*tf*1e12
    return (max(2*n*q*body_params/F, 2*body_params/B)
            + max(2*n*head_params/F, 2*head_params/B)
            + max(4*n*q*z*a*d*length/F, n*kv_per_position*length/B))

for gpu, capacity, bw, tf in devices:
    for model in models:
        name, *_, L, R, auxiliary, p, d, T = model
        K = model_geometry(model)[2]*L
        n = floor((capacity-R)*GiB/(K + auxiliary*GiB))
        values = []
        for eta_b, eta_f in [(0.80, 0.25), (0.80, 0.40), (0.40, 0.15),
                             (0.70, 0.25), (0.50, 0.25)]:
            prefill_s = model_phase(model, n, p, L, bw, tf, eta_b, eta_f) if p else 0
            decode_s = d*model_phase(model, n, 1, L, bw, tf, eta_b, eta_f)
            values.append(100*(prefill_s + decode_s)/T)
        print(gpu, name, "batch", n, "cycle %: main, faster, slower, BW70, BW50",
              *(round(x, 1) for x in values))

observed_vllm = [[127.61, 123.15, 117.35, 105.88],
                 [84.28, 80.70, 77.69, 70.33]]
for model, measured in zip(models[1:3], observed_vllm):
    for prompt, observed in zip([1, 6144, 14336, 30720], measured):
        for bw in [1.935, 2.039]:  # A100 PCIe and SXM; published SKU unspecified
            elapsed = model_phase(model, 1, prompt, (prompt+1)/2, bw, 312)
            elapsed += sum(model_phase(model, 1, 1, prompt+j, bw, 312)
                           for j in range(1, 2048))
            predicted = 2048/elapsed
            print(model[0], prompt, bw, "predicted/observed tok/s",
                  round(predicted, 2), observed,
                  "relative speed error %", round(100*(predicted/observed-1), 1))
```

进一步验证应在表内每个 `N_mem`、最大保留长度和周期工作量下，分别测主干与完整管线，记录真实可分配容量、辅助状态、batch 执行和端到端完成时间。未达到周期的配置保留，并检查减小 batch 后是计算还是容量先限制承载；不得为维持预设结论改动周期或删去失败格子。

<a id="single-gpu-selection"></a>
### 平台选择与容量估算

**2026-09-25 最新要求：GPU 型号开放，不再限定 A100；GPU 必须完整独占，分配给实例的主机 RAM 必须足额、专用，不能因其他租户使用而被收回；允许同一物理主机的其余内存供其他租户使用。** 不要求整台物理服务器、全部 RAM 或内存控制器/通道独占。PCIe 仍按此前完整带宽和目标路径不受其他租户争用的要求核验，不能由内存容量保证推定链路性能。本轮重点核验 [AWS/GCP 的 Gen4 及更高带宽配置](#higher-bandwidth-candidates)，保留 Lambda 单卡测量线索。用户已有云额度，价格次要；按[资源分配与 PCIe 要求](#exclusive-a100-40gb)筛选普通单卡 VM 与整机备选，不因主机多租户直接排除。最终主卡还须通过正常全驻留容量边界、完整周期成本和实际恢复带宽校准；选型条件不冻结论文研究范围。

A100 也有在线 LLM 推理的公开部署先例：[NVIDIA 2022 年案例](https://blogs.nvidia.com/blog/ai-large-language-models-triton/)记录 Tabnine 与 NLP Cloud 使用 A100 和 Triton 服务语言模型。这支持平台的部署合理性，不表示 A100 是当前新增推理部署的主流份额或最佳性价比。

| 候选整卡 | 标称显存 | 峰值显存带宽 | 卡端主机接口 | 本轮角色与主要限制 |
| --- | --- | --- | --- | --- |
| [A100 40GB PCIe](https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/a100/pdf/A100-PCIE-Prduct-Brief.pdf) | 40 GB HBM2 | 1,555 GB/s | Gen4 x16 | 链路验收后校准；需确认完整模型和多会话组仍有足够 KV 空间 |
| [L40S](https://www.nvidia.com/en-us/data-center/l40s/) | 48 GB GDDR6 | 864 GB/s | Gen4 x16 | 资源比例对照；相对 A100 没有 PCIe 代际提升 |
| [RTX 5090](https://images.nvidia.com/aem-dam/Solutions/geforce/blackwell/nvidia-rtx-blackwell-gpu-architecture.pdf) | 32 GB GDDR7 | 1,792 GB/s | Gen5 x16 | 带宽扩展备选；较小 KV 池、主机 RAM、实际链路和后端兼容性须先过关 |
| [A100 80GB PCIe](https://www.nvidia.com/en-us/data-center/a100/) | 80 GB HBM2e | 1,935 GB/s | Gen4 x16 | 不优先首租；容量增大而主机链路不变，适合后续资源比例验证 |
| [H100 80GB PCIe](https://www.nvidia.com/content/dam/en-zz/Solutions/gtcs22/data-center/h100/PB-11133-001_v01.pdf) | 80 GB HBM2e | 2,000 GB/s | Gen5 x16 | 带宽扩展备选；先验证实例的完整 Gen5 路径与有效 H2D |
| [H100 80GB SXM](https://www.nvidia.com/en-us/data-center/h100/) | 80 GB HBM3 | 3,350 GB/s | Gen5 | 计算与显存带宽较高的同容量候选；仍需核验主机接口宽度和共享上行 |
| [H200 SXM / NVL](https://www.nvidia.com/en-us/data-center/h200/) | 141 GB HBM3e | 4,800 GB/s | Gen5 | 相对 H100 没有 PCIe 代际提升；仅为容量或计算需求升级，不因卡更新就优先 |
| [RTX PRO 6000 Blackwell Server Edition](https://www.nvidia.com/en-us/data-center/rtx-pro-6000-blackwell-server-edition/) | 96 GB GDDR7 | 1,597 GB/s | Gen5 | 有公开 Gen5 云实例入口；大池可能降低相对扩容空间，须与 H100 分别校准 |
| [RTX 4090](https://images.nvidia.com/aem-dam/Solutions/geforce/blackwell/nvidia-rtx-blackwell-gpu-architecture.pdf) | 24 GB GDDR6X | 1,008 GB/s | Gen4 x16 | 可作小规模调试；全模型开销可能使有效 KV 池过小，不优先主实验 |

表中是厂家规格，GB/s 是十进制单位；显存带宽不是 H2D 带宽。Gen4/Gen5 x16 的编码后单向理论上限约为 31.5/63.0 GB/s，即 29.3/58.7 GiB/s，应用有效值更低；厂商标注的 64/128 GB/s 双向总量不能直接用于恢复预算。SXM、PCIe 与 NVL 是不同 SKU，租到一张 GPU 不等于已确认其形态或主机链路。峰值 FLOPS 也不能预测完整周期：例如 A100 的 dense BF16 Tensor 峰值为 312 TFLOPS，而 L40S 约 362 TFLOPS，大小 batch、注意力、输入处理和输出阶段的实际成本仍需分别计入。[A100 规格](https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/a100/pdf/nvidia-a100-datasheet-us-nvidia-1758950-r4-web.pdf)、[L40S 规格](https://www.nvidia.com/en-us/data-center/l40s/)

**可核验租赁配置。** 以下为 2026-09-25 读取的公开按需价，美元/小时；不是库存承诺或已下单报价。存储、税费和额外资源以结算页为准，主机 RAM 的 GB/GiB 保留供应商单位。

| 平台与精确配置 | CPU / 主机 RAM | 公开价格 | 选择含义 |
| --- | --- | --- | --- |
| [Lambda：1× H100 PCIe 80GB](https://lambda.ai/pricing) | 26 vCPU / 225 GiB，1 TiB SSD | $3.29/h | 更高带宽备选；当前实例仍需通过隔离、拓扑与实际 KV 搬运验收 |
| [Lambda：1× H100 SXM 80GB](https://lambda.ai/pricing) | 26 vCPU / 225 GiB，2.75 TiB SSD | $4.29/h | 同容量、更高显存带宽候选；不能从 SXM 名称推定 H2D 更快 |
| [Lambda：1× A100 PCIe 40GB](https://lambda.ai/pricing) | 30 vCPU / 225 GiB，512 GiB SSD | $1.99/h | 待验候选；主机副本余量充足，H2D 与共享上行未获实例级保证 |
| [Runpod：1× L40S](https://www.runpod.io/pricing) | 16 vCPU / 94 GB | $1.09/h | 备选；主机 RAM 必须按目标会话数核算 |
| [Runpod：1× RTX 5090](https://www.runpod.io/pricing) | 9 vCPU / 35 GB | $0.99/h | 默认主机 RAM 对长历史副本过紧，不能仅凭卡型和低价选择 |
| [Runpod：1× A100 PCIe 80GB](https://www.runpod.io/pricing) | 8 vCPU / 117 GB | $1.59/h | 便宜不等于更适合动机验证；另查 CPU 预处理是否饱和 |
| [Runpod：1× H100 PCIe 80GB](https://www.runpod.io/pricing) | 16 vCPU / 188 GB | $2.89/h | Gen5 条件候选，不能假定实例已跑满卡端接口 |

Lambda 另列同价的单卡 A100 SXM 40GB、30 vCPU / 220 GiB RAM；它可作库存替代，但要独立标定主机路径。[Nebius](https://nebius.com/prices) 的 L40S Intel 配置从 $1.55/h 起、AMD 从 $1.82/h 起；最低价与最高 CPU/RAM 档不能拼成一个实例。RTX 5090 若能获得至少 96 GiB、优先 128 GiB 主机 RAM及实际 Gen5 x16，可挑战首选；目前核验到的 Runpod 默认配额不足，CloudRift [价目表](https://www.cloudrift.ai/pricing)列 $0.60/h，但[首页](https://www.cloudrift.ai/)标缺货，且未核实符合上述 RAM 的实例，因此暂不作为可直接执行的替代。未复核库存和配置的旧 Novita 文章价不作为采购依据。

**AWS、Lambda 与 Google Cloud 的服务器租赁入口。** 三者都提供可 SSH 登录的 GPU 虚拟机，可在获得管理员权限后安装依赖、运行 Docker 和自有实验代码；应选 EC2、Lambda On-Demand Cloud、Compute Engine 的 VM 产品。预装镜像只是环境起点，需要核验是否满足仓库的锁定依赖与观测权限。[AWS SSH 与 GPU 镜像](https://docs.aws.amazon.com/dlami/latest/devguide/setup-connect.html)、[Lambda SSH/sudo Docker 示例](https://docs.lambda.ai/education/large-language-models/serving-llama-3-1-docker/)、[GCP SSH/sudo 权限](https://docs.cloud.google.com/compute/docs/oslogin)

| VM 入口与 SKU | 整实例 GPU / CPU / 主机 RAM | 地区与整实例按需价（2026-09-25 核验） | 本轮使用判断 |
| --- | --- | --- | --- |
| Lambda On-Demand：1× A100 PCIe 40GB | 上表单卡配置；同平台另有单卡 SXM 40GB | 上表 $1.99/h；公开价不绑定某一区域，具体区域库存须登录核验 | 可做链路验收，未证明满 Gen4 |
| GCP Compute Engine：`a2-highgpu-1g` | 1× A100 40GB / 12 vCPU / 85 GiB | Iowa `us-central1` 公开表参考价 **$3.673385/h** | Cascade Lake 主机，不列为已满足链路要求的备选 |
| GCP Compute Engine：`a2-ultragpu-1g` | 1× A100 80GB / 12 vCPU / 170 GiB | 同地区公开表展示 **$5.06879789/h** | 同样存在主机链路限制；增大显存不能解决 |
| AWS EC2：`p4d.24xlarge` | **8×** A100 40GB / 96 vCPU / 1,152 GiB | Northern Virginia `us-east-1`、Linux：**$21.957642/h** | 官方静态拓扑为 Gen3 x16，不作满 Gen4 主卡 |
| AWS EC2：`p4de.24xlarge` | **8×** A100 80GB / 96 vCPU / 1,152 GiB | 同地区、Linux：**$27.44705/h** | 同样不作满 Gen4 主卡；仍按八卡整实例计费 |

GCP 配置及价来自[GPU VM 规格](https://docs.cloud.google.com/compute/docs/gpus)和[官方按需表](https://cloud.google.com/products/compute/pricing/accelerator-optimized)；A2 Ultra 必带 Local SSD，总价表说明已含捆绑 SSD，但两页对 1g 的容量分别写 375/275 GiB，故保留价目页展示总价，租前以创建页明细复核，不重复加算该捆绑盘。AWS 配置来自[P4 实例页](https://aws.amazon.com/ec2/instance-types/p4/)，费用直接核对[官方 us-east-1 Linux 定价数据](https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/ec2-ondemand-without-sec-sel/US%20East%20%28N.%20Virginia%29/Linux/index.json)；不能用每卡折算价当作只租一张卡的账单，也不能混用 Capacity Blocks 的预约价。附加磁盘、网络、IP、税费与收费镜像均按实际配置另计。[AWS](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-on-demand-instances.html)与[GCP](https://cloud.google.com/products/compute/pricing)标准 VM 按秒计费、最低一分钟；[Lambda](https://docs.lambda.ai/public-cloud/billing/)按一分钟增量计费，需在控制台/API 终止实例结束计算计费，不能靠退出 SSH 或来宾系统关机代替。

账户门槛尚未登录验证：Lambda 需绑定受支持的主要信用卡并通过 $10 预授权，新账户有实例数额度；其[付款支持地区列表](https://docs.lambda.ai/public-cloud/manage-billing/)目前不含中国大陆，[区域库存和账户额度](https://docs.lambda.ai/public-cloud/on-demand/creating-managing-instances/)另查。GCP 需已升级的[付费 Billing 账户](https://docs.cloud.google.com/free/docs/free-cloud-features)、目标区域对应 A100 40/80GB 配额及 `GPUs (all regions)` 配额；免费试用账户不能添加 GPU 或申请配额，配额获批也不保证可用区库存。[GCP 配额规则](https://docs.cloud.google.com/compute/resource-usage) AWS 需可计费账户、实例创建权限，以及目标区域至少 96 vCPU 的 `Running On-Demand P instances` 剩余额度；该项官方默认值为零，账户现值和可用区库存需分别核验。[AWS 配额规则](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-on-demand-instances.html) 用户已有额度，当前选择先看链路资格与实机验收；额度、配额和库存分别核验，不据公开价格决定优先级。本轮未登录、创建资源或付款。

**实例级 PCIe/H2D 证据（2026-09-25）。** 卡端规格、供应商静态拓扑、外部原始测量和本项目验收是不同证据层；目前三家都没有本项目实测或已核验的单实例 H2D 性能保证。AWS 的公开拓扑揭示 Gen3 主机路径，与此前完整 Gen4 偏好不符；带宽代际和跨租户隔离须分别判断。

| 实例 | 已公开的一手证据 | 尚未保证的部分与决定 |
| --- | --- | --- |
| AWS P4d / P4de | AWS 分别提供 [P4d](https://github.com/aws/aws-ofi-nccl/blob/master/topology/p4d-24xl-topo.xml)、[P4de](https://github.com/aws/aws-ofi-nccl/blob/master/topology/p4de-24xl-topo.xml) NCCL 静态拓扑：两 socket，每 socket 两组 PCIe switch，每组 2 GPU 和 1 NIC，GPU 和上行均标 `8 GT/s ×16`（Gen3） | 静态模型不是当前实机读数或带宽 SLA；但已有明确 Gen3 与上行共享证据，不以 A100 卡端 Gen4 规格覆盖它，不选作满 Gen4 主卡 |
| GCP A2 Standard / Ultra | [当前创建文档](https://docs.cloud.google.com/compute/docs/gpus/create-vm-with-gpus)分别限定两系列只能用 Cascade Lake CPU 平台 | 未核验到两种 1g 实例的完整物理桥接拓扑、协商宽度、共享比例或 pinned H2D 保证；不能由 GPU 规格推成全路径 Gen4，不列已通过候选 |
| Lambda 1× A100 PCIe / SXM 40GB | [ODC 文档](https://docs.lambda.ai/public-cloud/on-demand/)确认独立 SKU、Linux VM 和资源配额；SXM 描述的是 GPU 间连接优势 | 对这两个单卡 SKU，具体 CPU、物理上行、NUMA 映射、是否与其他 VM 共上行及 H2D 限速未公开到可保证的程度；两者均须验收，SXM 不自动代表 host 路径更快或更慢 |

Cascade Lake 是 Intel 第二代 Xeon Scalable CPU 平台代号；这一代主机 PCIe 控制器只支持 Gen3，例如 [Intel 8274 规格](https://www.intel.com/content/www/us/en/products/sku/192487/intel-xeon-platinum-8274-processor-35-75m-cache-3-10-ghz/specifications.html)同时列出 Cascade Lake 与 PCI Express 3.0（此处用于说明平台能力，不指认 GCP 的具体 CPU 型号）。[GCP 当前 A2 文档](https://docs.cloud.google.com/compute/docs/accelerator-optimized-machines#the_a2_machine_series)明确 Standard / Ultra 仅提供该平台，因此无法提供完整 Gen4 主机路径；A100 卡端能力或 sole-tenant 隔离均不能升级 CPU 的 PCIe 控制器。这是平台规格推断，不是本项目测得的 A2 H2D 数值。

外部原始测量提供了交叉核验：[HPC WORLD 2021-01-14 的 P4d 实验](https://hpcworld.jp/techcolumn/aws-p4d-instances/)公开 CUDA `bandwidthTest`、32,000,000-byte 锁页缓冲区的单卡 H2D **12.3 GB/s**、D2H **13.2 GB/s**，符合 Gen3 受限的量级；这是历史测量，不是当前所有区域的保证。Gen3 x16 编码后单向理论值约 15.75 GB/s，与 Gen4 x16 的 31.5 GB/s 区分；NVLink/NVSwitch 的 GPU 间速率、EFA/外网速率和 H2D 不能互代。VM 暴露整张 GPU 或支持直通也不证明 PCIe 上行独占、无带宽限制或 NUMA 局部性，须取得拓扑/分配信息并实测。

A100 的卡端上限就是 Gen4 x16，插入 Gen5 主机也不会升级为 Gen5；更高代际必须同时更换支持它的 GPU 和主机路径。更换到 H100/H200 仍不能跳过实例核验：[AWS 官方](https://aws.amazon.com/ec2/instance-types/accelerated-computing/)明确 P5/P5e 的 CPU–GPU 链路为 Gen4，P5en 才为 Gen5。H100 PCIe、RTX 5090 等 Gen5 卡只作为条件候选，另核算可用 KV 池和主机副本空间。

<a id="exclusive-a100-40gb"></a>
**资源分配与 PCIe 要求。** GPU 应是完整物理卡，计算与显存专用于本实例，不接受供应商切分的 MIG/vGPU 或与其他租户分时使用同一张卡。主机 RAM 按购买的实例容量足额分配，不因其他租户负载被回收或以超售、换页替代应有的物理容量；允许同机其他内存分给其他租户，不要求 CPU socket 或内存控制器/通道独占。实例内操作系统、驱动及本账户进程占用不属于被其他租户拿走。目标 GPU 到主机内存的 PCIe 路径仍须核验完整代际、宽度及上行争用；整机独占是可选实现方式，不能作为所有候选的采购前提。

PCIe 是[点对点互连](https://www.intel.com/content/www/us/en/io/pci-express/pci-express-architecture-general.html)，但卡到交换机的专用连接不等于到 CPU 的整条路径专用。上文 AWS 静态拓扑说明多 GPU/NIC 可以物理汇聚，不证明存在跨租户共置。主机内存容量保证可以在普通 VM 中成立：[AWS Nitro 文档](https://docs.aws.amazon.com/whitepapers/latest/security-design-of-aws-nitro-system/the-ec2-approach-to-preventing-side-channels.html)说明固定性能实例预分配并专用 CPU 和物理内存，实例间不共享内存页。[Intel 内存带宽说明](https://www.intel.com/content/www/us/en/developer/articles/technical/introduction-to-memory-bandwidth-allocation.html)指出同机多个 VM 仍可争用内存带宽；这属于 H2D 性能验收因素，不再是独立的整机隔离门槛。Lambda ODC 的公开规格确认 RAM 配额，官方答复确认 GPU 独占，但尚未取得其内存超售/回收策略与 PCIe 上行的明确保证，须区分已公开属性和待确认项。

| 平台与购买方式 | 租户隔离证据 | 硬件与当前判断 |
| --- | --- | --- |
| OCI `BM.GPU4.8`，8× A100 40GB SXM | [Compute FAQ](https://www.oracle.com/cloud/compute/faq/)明确 bare-metal 实例是专用于单客户的完整物理主机，无 hypervisor，客户控制主机资源 | [当前规格](https://docs.oracle.com/en-us/iaas/Content/Compute/References/computeshapes.htm)列 AMD EPYC 7542、64 OCPU、2048 GB 主机 RAM；下文有官方实例级 H2D 测量。保留为 A100 40GB、Gen4 级传输的整机备选；此 SKU 须租整台八卡服务器，整机隔离不再构成对普通 VM 的必然优先级 |
| Azure `Standard_NC96ads_A100_v4`，4× A100 PCIe 80GB | [当前 Isolated VM 列表](https://learn.microsoft.com/en-us/azure/virtual-machines/isolation)明确列出此 SKU，保证它是该物理服务器上唯一的 VM | [规格](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/gpu-accelerated/nca100v4-series)列 EPYC 7V13 Milan、96 核、880 GiB 主机 RAM；接受 80GB 时保留为隔离合格备选，尚未取得实例全路径 Gen4 x16 与 H2D 验收证据。单卡 `NC24ads_A100_v4` 不在该隔离列表，不能套用四卡保证 |
| AWS P4d Dedicated Host，8× A100 40GB | [实例支持表](https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html)列 P4d 支持 Dedicated Hosts；[产品契约](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/dedicated-hosts-overview.html)定义完整物理服务器专用于客户，需关闭跨账户共享 | 整机隔离覆盖其他租户对本地主机 RAM/PCIe 的使用；上文官方拓扑仍是 Gen3 x16，按隔离合格、带宽低于此前偏好分别记录 |
| GCP A2 sole-tenant，`a2-highgpu-node-96-680`（8× A100 40GB） | [sole-tenancy 文档](https://docs.cloud.google.com/compute/docs/nodes/sole-tenant-nodes)明确物理节点与服务器一一对应，仅承载指定项目 VM，可关闭跨项目共享；同页列出该 A100 节点 | 整机隔离覆盖本地主机 RAM/PCIe；同一节点表仍明确 Cascade Lake，满足独占与提供完整 Gen4 是两项独立判断 |
| Lambda ODC，1× / 4× A100 PCIe 40GB 或 1× / 8× A100 SXM 40GB | [官方 ODC 规格](https://docs.lambda.ai/public-cloud/on-demand/)确认这些 GPU VM 及其 RAM 配额；[Lambda Team 2025-08-20 官方论坛答复](https://deeptalk.lambda.ai/t/are-public-cloud-instances-resources-shared/4695)确认 GPU 在实例生命周期内专用、不与其他客户共享 | 单卡 SXM40 有下文 Gen4 x16 与 H2D 原始测量，优先核验；PCIe 板卡 SKU 单独验收。待确认 RAM 不超售/回收及实际 PCIe 上行分配，不要求整台物理主机独占 |
| Lambda Private Cloud | [官方隔离说明](https://docs.lambda.ai/private-cloud/security-posture/)明确专属于单客户的硬件，所有节点为与其他客户物理隔离的单租户 bare-metal 系统 | 已确认提供物理隔离；当前可供的 A100 40GB 配置、Gen4 拓扑、最低规模与租期须报价确认，保留为候选，不能把此保证套给 ODC |
| Lambda 1-Click Clusters（1CC）的 compute nodes | [官方隔离说明](https://docs.lambda.ai/public-cloud/1-click-clusters/security-posture/)明确 GPU 计算节点是单租户硬件，GPU、内存、本地存储和网卡不与其他客户共享 | 本地 KV 副本与模型计算均放在同一 compute node，避免把 head node 到 GPU 的网络路径混作本地 H2D。当前公开卡型是 H100/B200，不是 A100；非单卡实验的必选入口 |

1CC 是比 Private Cloud 更小的已公开隔离入口。[当前详细产品表](https://lambda.ai/1-click-clusters)展示 16 张 H100 或 B200、2 周起的套餐，并允许申请 POC 环境；[Cloud 总览](https://lambda.ai/cloud)仍写 1 周起，故不能把更短期限当成已确认可下单条件，实际以配置页/报价为准。POC 的规模、期限和收费未公开，不能假定免费或必然提供单节点。PCIe 代际/宽度、NUMA 与 H2D 性能仍按实际计算节点验收。

Private Cloud 的未知项是当前交付条件，不能写成供应商缺少能力。[公开产品文档](https://docs.lambda.ai/private-cloud/)展示 1,000+ B200、1–3 年预订等大规模方案，购买入口为[销售询价](https://lambda.ai/talk-to-our-team)，未列出 A100 40GB 的当前独占配置和起租条件；这些展示配置也不证明销售绝不接受其他规模。[2022 年官方案例](https://lambda.ai/blog/voltron-data-case-study-why-ml-teams-using-reserved-cloud-clusters)记录过 A100 40GB 裸金属集群租赁，仅说明历史交付能力，不代表当前库存或合同条件。单节点、短租属于实验便利偏好，用户未将其设为硬门槛；应同时保留 Private Cloud 与整机预订，按实际报价比较。

Lambda 当前优先核验单卡 A100 SXM 40GB 的实际 H2D，上表列其公开资源配额；单卡 PCIe 40GB 作为独立 SKU 核验，不套用 SXM 测量。多卡备选为 **4× A100 PCIe 40GB**（120 vCPU、900 GiB RAM，基础整实例价 **$7.96/h**）和 **8× A100 SXM 40GB**（124 vCPU、1,800 GiB RAM，**$15.92/h**）。整实例价由 2026-09-25 [官方价目表](https://lambda.ai/pricing)的 $1.99/GPU/h 乘卡数得到，未含税费；不是已获物理独占保证的包机报价。SXM 形态不排除通过 PCIe Gen4 进行 H2D，仍按实际 host 路径选择。

[外部 A100 SXM40 原始记录一](https://github.com/malaiwah/quant-fidelity-suite/blob/main/reports/provider-bench/lambda-a100-sxm4-40gb-s1.json)、[记录二](https://github.com/malaiwah/quant-fidelity-suite/blob/main/reports/provider-bench/lambda-a100-sxm4-40gb-s2.json)来自 2026-08-31、`us-east-1` 的两次 **单卡 `gpu_1x_a100_sxm4`** 租赁，GPU 查询均报告 Gen4 x16，冷启动 H2D 为 25.2/25.1 GB/s，预热后为 **26.1/26.2 GB/s**。依据[测量源码](https://github.com/malaiwah/quant-fidelity-suite/blob/main/bin/fidelity/cardbench_payload.py)，测试使用 256 MiB 锁页源、预分配 GPU 目标，计时前后同步 CUDA，预热后以 20 次复制的完成时间计算十进制 GB/s。这约为 Gen4 x16 编码后单向上限的 83%，超过 Gen3 x16 的理论上限，支持这些样本达到 Gen4 级有效带宽；理论接口速率不等于应用有效吞吐，不能以未达 31.5 GB/s 判断被限速。记录未附 CPU 型号、完整桥接拓扑、其他租户分配或多卡/模型并发结果，不同实例 ID 也不证明不同物理主机。不得把单卡 SXM 样本推广为 PCIe 板卡 SKU、多卡实例或持续带宽保证；隔离须由供应商产品/合同和分配信息证明，带宽由实机验收证明。

<a id="oci-gen4-rental"></a>
OCI 的带宽依据来自 [Oracle Japan 2026-02-16 官方 OSU 教程](https://oracle-japan.github.io/ocitutorials/hpc/benchmark/run-omb-gpu-ubuntu/)。教程明确实测实例为 `BM.GPU4.8`，使用 Ubuntu 24.04、CUDA 12.9.1、OpenMPI 5.0.8、OSU 7.5.1；256 MiB 消息的 `osu_bw -d cuda H D` 在本地 NUMA 测得 **23,744 MB/s（23.744 GB/s）**，同 socket 异 NUMA 为 23,736.96 MB/s，跨 socket 为 23,369.30 MB/s。这是供应商公开的 CUDA-aware MPI 端到端单向传输结果，不是本项目实测，也不是纯 pinned `cudaMemcpyAsync` 峰值。其吞吐超过 Gen3 x16 的单向理论上限，支持该实例达到 Gen4 级有效带宽；[AMD EPYC 7542 规格](https://www.amd.com/en/support/downloads/drivers.html/processors/epyc/epyc-7002-series/amd-epyc-7542.html)另支持 CPU 的 Gen4 能力。两者均不替代实际租赁服务器每段 PCIe 链路的协商状态和并发验收。

对 OCI 应先核查账户配额、区域库存及整机报价，再按下文协议测目标 GPU 的本地 NUMA pinned H2D 和模型并发 `B_eff`；不能用上述 MPI 口径直接判定纯 DMA 的 25 GB/s 筛选线通过或失败。可在独占整机上只使用一张 GPU 完成单卡实验，但计费仍覆盖整台八卡服务器；其余 GPU/NIC/NVMe 的本账户流量须受控。该采购优先级不改变论文平台范围，亦不构成已完成链路验收。

供应商确认需求（草案，未发送）：

> We need a single-GPU instance for CPU-to-GPU KV-cache transfer experiments; the GPU model is open. The complete physical GPU must be dedicated to our instance, without MIG/vGPU partitioning or time-sharing with other customers. The advertised host RAM allocation must be fully backed by physical memory and reserved for our instance, without overcommitment, ballooning, or host swapping to satisfy other tenants' demand. Other tenants may use the rest of the server's memory; we do not require the whole physical server or dedicated memory controllers/channels. Please confirm a full Gen4 x16 or faster host-to-GPU path without contention from other tenants on its PCIe upstream links, and provide the CPU model, NUMA/PCIe topology, any H2D bandwidth limits, and measured sustained pinned-memory H2D throughput. Please state the exact GPU and instance SKU, region, RAM allocation, instance price, and any guarantees during the rental or host replacement. We need SSH/admin access to run our own CUDA and model benchmarks. If ordinary single-GPU instances cannot meet these requirements, please identify the smallest suitable reserved or bare-metal option.

<a id="higher-bandwidth-candidates"></a>
**Gen4 及更高带宽云配置。** GPU 型号放开后，AWS P5 的 Gen4 和 GCP G4、AWS G7/G7e 的 Gen5 均纳入筛选。Gen5 x16 的接口单向理论上限是 Gen4 x16 的两倍；Gen5 x8 则与 Gen4 x16 相同。供应商对链路代际的说明不等于持续 H2D 保底或无上行争用保证，完整路径、宽度及锁页内存吞吐仍须验收。以下候选要求完整 GPU 独占、所分配 RAM 足额专用，不要求整机或主机内存控制器独占，也不是已测主实验平台。

| 入口 | 已核验配置或链路信息 | 本轮判断 |
| --- | --- | --- |
| Lambda 单卡 H100 PCIe / SXM | [公开规格](https://docs.lambda.ai/public-cloud/on-demand/)列两种单卡 80GB VM，资源见上表 | Gen5 校准备选；未取得当前实例上行隔离与最低 H2D 保证，分别验收 |
| GCP `a3-highgpu-1g` | [官方规格](https://docs.cloud.google.com/compute/docs/accelerator-optimized-machines)列 H100 SXM 80GB、26 vCPU、234 GB 主机内存，CPU 为 Sapphire Rapids；1/2/4 卡形状仅支持 Spot 或 Flex-start | 主机平台支持 Gen5 的候选，但公开 CPU 型号不等于端到端 H2D 保证；还须验证实际 x16 路径和共享上行 |
| GCP `g4-standard-48` | 同一[官方机器文档](https://docs.cloud.google.com/compute/docs/accelerator-optimized-machines)明确 G4 支持 CPU 内存到 GPU 的 PCIe Gen5；该形状为完整 RTX PRO 6000 Blackwell Server Edition 96GB、48 vCPU、180 GB 主机内存 | 单卡 Gen5 的明确供应商入口；[创建文档](https://docs.cloud.google.com/ai-hypercomputer/docs/create/create-vm-g4)支持 Standard/on-demand。仍需测宽度、带宽和周期成本；较小的 fractional-GPU 形状不作本轮整卡对照 |
| AWS `p5.4xlarge` | [官方规格](https://aws.amazon.com/ec2/instance-types/accelerated-computing/)列单 H100 80GB、16 vCPU、256 GiB 主机 RAM，并明确 P5/P5e 的 CPU–GPU 为 Gen4 | 单卡 Gen4 的直接产品依据，无需租八卡；H100 卡端支持 Gen5 不代表此实例为 Gen5。未取得该 SKU 原始 H2D 或完整 x16 路径测量 |
| AWS `g7e.4xlarge` / `g7e.8xlarge` | [产品页](https://aws.amazon.com/ec2/instance-types/g7e/)列单 RTX PRO 6000 Blackwell Server Edition 96GB，分别 16/32 vCPU、128/256 GiB 主机 RAM；[AWS Labs 指南](https://awslabs.github.io/accelerated-compute-tutorials/en/nvidia-gpu/instance-guide/#33-g7e)明确 CPU–GPU Gen5 x16 | 单卡 Gen5 候选；链路依据是供应商教程，未附实例拓扑或 H2D 原始输出，不把宣传倍率换算成实测 GB/s |
| AWS `g7.8xlarge` | [产品页](https://aws.amazon.com/ec2/instance-types/g7/)列单 RTX PRO 4500 Blackwell Server Edition 32GB、32 vCPU、128 GiB 主机 RAM；同一 [AWS Labs 指南](https://awslabs.github.io/accelerated-compute-tutorials/en/nvidia-gpu/instance-guide/#34-g7)明确 CPU–GPU Gen5 x16 | 较小显存配 Gen5 的校准候选，尚无本项目或本轮核验的实例 H2D；先检验完整模型、有效会话组和恢复目标能否同时容纳，以及计算余量 |
| AWS `g6e.4xlarge` / `g6e.8xlarge` | [产品页](https://aws.amazon.com/ec2/instance-types/g6e/)列单 L40S 48GB，分别 16/32 vCPU、128/256 GiB 主机 RAM；CPU 为 EPYC 7R13，CPU 与 GPU 均有 Gen4 能力 | 容量比例备选；本轮未取得实例完整 Gen4 x16 路径或 H2D 原始输出，不能仅由两端能力列为满带宽配置 |
| AWS `p5en.48xlarge` | [官方 P5 页面](https://aws.amazon.com/ec2/instance-types/p5/)明确 CPU–GPU Gen5；整实例 8× H200 | 确有 Gen5 的入口，但须接受八卡整实例并验收实际带宽；不因显存或卡名更高就替代单卡 H100 |

GCP G2 不作为 Gen4 入口：[官方机器文档](https://docs.cloud.google.com/compute/docs/accelerator-optimized-machines)在 G4 与 G2 的主机传输对比中直接写明 G2 使用 Gen3，不能由 L4 卡端能力覆盖。GCP 的单卡 A3 仅支持 Spot 或 Flex-start；普通按需采购优先核验上表 G4。AWS 的固定性能 GPU VM 可依据上文 Nitro 资源预分配保证核查 RAM，不需为容量专用而改租 Dedicated Host。新增候选均未验证账户配额、目标区域库存及带宽，不据公开规格承诺可立即创建或预设论文收益。

Lambda H100 PCIe 有可复核的外部正向线索：2026-08-31 在 `us-west-3` 的两次独立租机记录分别报告预热 H2D **55.5 / 55.4 GB/s**、冷启动阶段 **51.3 / 40.6 GB/s**，GPU 端报告 Gen5 x16（[原始记录一](https://github.com/malaiwah/quant-fidelity-suite/blob/main/reports/provider-bench/lambda-h100-pcie-s1.json)、[原始记录二](https://github.com/malaiwah/quant-fidelity-suite/blob/main/reports/provider-bench/lambda-h100-pcie-s2.json)）。[公开测量代码](https://github.com/malaiwah/quant-fidelity-suite/blob/main/bin/fidelity/cardbench_payload.py)使用 256 MiB 锁页源和预分配 GPU 目标、异步复制、计时前后 CUDA 同步；持续传输预热后计 20 次复制，以 wall-clock 完成时间计算十进制 GB/s。这是外部微基准，不是本项目实测、当前库存保证或模型并发速率；单尺寸、复用缓冲区、无 NUMA 对照、无完整上行核验及未嵌源码 hash 限制了可迁移性。它支持优先短租验收该 SKU，不能直接把 55 GB/s 写入论文收益预测。

H200 的 PCIe 与 H100 同代，增大显存或 HBM 带宽不等于再次增加 H2D。更新至带有 Gen6 宣传的系统也不能直接推成 Gen6 host 路径：例如 [DGX B300 文档](https://docs.nvidia.com/dgx/dgxb300-user-guide/introduction-to-dgxb300.html)把 Gen6 用于 ConnectX-8 到 GPU，而 [HGX B300 参考配置](https://docs.nvidia.com/enterprise-reference-architectures/hgx-ai-factory/latest/components.html)列的主机连接仍为八条 Gen5 x16；本轮不据网络侧 Gen6 为恢复预算加速。

若另行探索超出 PCIe 的主机带宽，[Lambda](https://docs.lambda.ai/public-cloud/on-demand/)可租单卡 GH200（96GB GPU、432 GiB 主机 RAM）；其 Grace CPU 与 GPU 使用 [NVLink-C2C](https://developer.nvidia.com/blog/inside-nvidia-grace-cpu-nvidia-amps-up-superchip-engineering-for-hpc-and-ai/)，900 GB/s 是双向原始链路总量，不是单向 H2D 实测。该平台涉及 Arm 环境及一致性内存访问方式，需另做依赖适配和匹配参照；不把它当作更高代际 PCIe，也不因当前运行环境限制而排除其研究适用性。

**筛选关系与空间约束。** 先实测扣除完整权重、其他模型状态、工作区和运行时保留后的 `G_KV`，不能用标称显存减主干权重代替。按[传输上界](problem.md#bandwidth-memory-bound)，在同周期、固定每会话状态 `M`、无共享的算例中，`N*M-G_KV <= peak_saving <= B_eff*T`，故仅受容量与传输预算约束的乐观上限为 `floor((G_KV+B_eff*T)/M)`；全驻留容量参照为 `floor(G_KV/M)`。忽略取整时相对上限是 `1+B_eff*T/G_KV`，不是性能预测，还须通过计算、恢复窗口和目标预分配检查。

例如只作敏感性分析，假设 A100 40GB、L40S、A100 80GB 可用池分别为 16、24、56 GiB，且有效 H2D 均为 24 GiB/s、周期为 1 秒，则上式为 2.50、2.00、1.43；H100 若池为 56 GiB且 H2D 实测能达 48 GiB/s，对应为 1.86。这些池大小和有效速率全部是假设，不是各卡标定结果。恢复早分配、有限释放窗口、更多周期工作都只会收紧上界。

小池也可能不利：若一组有两个 32K 历史的会话，该组完整主干 KV 就需 9 GiB；若当前组和下一组同时完整驻留，两组需 18 GiB，尚未计其他会话的保留部分。选择较小卡不能以组必然退化为单会话或放不下恢复目标为代价。分配边界仍按[未决设计](system.md#group-restoration-allocation)比较，不因硬件选型自行冻结。基线仅能容纳一个会话时必须同时报告绝对增量，避免整数倍率主导结论。

**容量与传输估算。** 每位置 KV 字节依据见[MiniCPM-o 参数笔记](references/minicpm-o-4.5-kv-geometry.md)。以下只计算主干 BF16 KV；上下文长度是算例条件，不是默认真实会话长度。

| 主干保留位置数 | 每会话主干 KV |
| --- | --- |
| 8,192 | 1.125 GiB |
| 16,384 | 2.25 GiB |
| 32,768 | 4.5 GiB |
| 40,960 | 5.625 GiB |

假设目标并发下可用 KV 池为 20–24 GiB，32K 历史的全驻留上限约为 4–5 个会话；该估算未验证计算和服务目标。

另假设有效 H2D 带宽为 24 GiB/s、周期为 1 秒：8 个 4.5 GiB 历史全量恢复需搬运 36 GiB，耗时 1.5 秒，超过周期；每会话只逐出 2 GiB 时合计 16 GiB，约需 0.67 秒。这只比较传输预算，部分恢复还须满足计算、单次恢复窗口与 GPU 预分配约束。8 个完整主机副本另占 36 GiB，尚需输入和运行缓冲。

主卡上先完成负载评估、消融及容量和带宽敏感性实验，再用未参与标定的配置验证预测。若增加硬件，优先选择资源比例不同的设备；同卡限制显存或带宽属于受控实验，不计为另一种硬件实测。

**短租校准与去留。** 先在有额度且符合候选条件的实例做约 15–30 分钟链路验收，通过后再投入完整模型和多会话校准。以下数值是本项目的筛选目标，不是厂家性能保证，也不替代尚待确定的正式服务目标。

1. 核验完整 GPU 的专用分配、主机 RAM 的足额物理容量与不因其他租户回收的保证，以及目标 PCIe 路径的分配和上行争用情况；不以整机单租户为前提。检查 GPU SKU、实际显存、MIG/虚拟化状态、功率/频率、PCIe 协商速率与宽度、CPU 型号与配额、NUMA 和主机 RAM，保留拓扑与软件清单。RAM 总量与应用可用量分别记录，正常 OS/驱动占用不算其他租户侵占；实测分配不能代替供应商的长期容量保证。可用空间须覆盖目标并发的完整副本、输入/运行缓冲和装载峰值，建议另留 25% 余量。共享内存带宽、PCIe 上行和远端 NUMA 的性能影响均纳入实测。
2. 用本地 NUMA 的锁页内存测单向 H2D：覆盖 1、16、64、512 MiB、1 GiB 及实际 KV 块大小，预热后重复至少三轮，记录有效字节、完成时间、单位和尾部；另测远端 NUMA 对照。空闲大块暂定筛选门槛为 **Gen4 x16：25 GB/s（约 23.3 GiB/s）；Gen5 x16：50 GB/s（约 46.6 GiB/s）**。这是本项目目标，不是厂家保证；达到门槛仍不替代完整路径与共享带宽检查。Gen4 只有约 10–13 GB/s 或 Gen5 只有 Gen4 量级时，先排查降代际/降宽、共享上行或远端内存，不能直接接受为本轮满链路主卡。随后测真实离散布局、并发增量 D2H、完整模型计算以及两者并发下的 H2D，分别记录 H2D 和 D2H，不能相加作恢复速率。候选计划须用受干扰后的保守 `B_eff` 满足 `E/(B_eff*T)<=0.8` 及各组恢复窗口；只有这些实测速率能计入收益。
3. 在模型支持的 8K、16K、32K 历史处扫描并发；分别测完整输入处理、主干、输出阶段和排队。固定真实输入及时间对齐生成行为，记录输出量分布，不另设更小 token cap。找到全驻留容量边界后，以完整周期时间 `p95<=0.7T`、`p99<T` 且无持续积压作为优先保留条件；若预热后已 `p95>=T`，该负载点不支持容量先受限。中间区域保留为边界配置，不能为了通过而删阶段或放宽周期。
4. 在同一负载下比较同步与分组 phase，覆盖每组 2/4 个 session 等可行组形状，记录实际 backend batch。校验全部 GPU 分配（含未完成的完整恢复目标）的峰值；初筛要求新增批处理成本、恢复干扰和等待合计不耗尽原有计算余量，并为尾部留出至少 `0.1T` 的时间余量。不能以平均 H2D 达标代替每组的时空可行性。
5. 候选主卡应在至少两个相邻的长历史/并发点观察到全驻留先触及容量、计算仍有余量，再进入正式实现比较。机制实现尚未完成时，以上只决定是否继续投入；增加达标会话数须由同精度、同输出、同历史、同后端的完整对照验证。短校准保留无收益点，不能据它宣称最终容量提升。

链路验收的最小命令入口如下；保留工具版本和原始输出，复制测试使用 [NVIDIA nvbandwidth](https://github.com/NVIDIA/nvbandwidth) 的 copy-engine H2D 项。示例 NUMA 节点 `0` 必须替换为目标 GPU 的本地节点，`-d` 禁止工具覆盖人工 affinity；先验证 VM 允许实际绑核、绑内存，失败或只暴露虚拟拓扑时记录未知项，不能声称已经证明物理局部性。

```bash
nvidia-smi -q
nvidia-smi topo -m
lscpu
numactl --hardware
lspci -tv
sudo lspci -vv
numactl --cpunodebind=0 --membind=0 ./nvbandwidth -d -b 512 -i 10 -t host_to_device_memcpy_ce
numactl --cpunodebind=0 --membind=0 ./nvbandwidth -d -b 512 -i 10 -t host_to_device_bidirectional_memcpy_ce
```

在传输负载下重读 PCIe 当前协商值，区别空闲省电降代际；同时检查 GPU、所有可见桥和上行，不能只读 GPU 的最大能力。多卡实例增加单卡/同时多卡 H2D 对照以定位共享上行；单卡 VM 还需供应商确认物理上行共享情况，并在不同时段重复测量。上述微基准之后仍要完成第 2 步的实际 KV/D2H/模型重叠测试，NVLink 测试不能代替它。

本轮将 AWS/GCP 单卡 Gen4/Gen5 配置与 Lambda 单卡 A100 SXM 的外部带宽线索一起纳入校准，不再固定主卡型号；OCI 整机等保留为备选。所有候选须容纳完整工作集、主机副本和有效会话组，通过资源分配及链路验收。较小 KV 池配较高 H2D 只提示值得测量，不保证容量先受限或收益更高；不能为了相对倍数把组退化成不可用形状。大池配慢 H2D、弱计算配长上下文、主机 RAM 不足或严重批处理损失，均可能压缩方法的收益；不人为削弱全驻留基线来消除这些区域。

<a id="reproducibility-appendix-current-prototype"></a>
## 复现附录：当前原型

以下保留已登记原型的配置与诊断解释。运行前核验可执行配置、实际路径和 run manifest；旧登记状态不证明新设计已实现。证据与比较资格见 [已有证据](findings.md#evidence-scope)。

<a id="machine-migration"></a>
新机器部署和实际运行检查命令由 [环境操作入口](../infra/env/AGENTS.md#new-machine-setup) 持有。该检查复用锁定依赖，检测实际 GPU、模型文件、物理复制与会话生命周期；不把换卡功能通过当成成本标定或正式容量结论。

<a id="finite-cohort-runner"></a><a id="stable-concurrency-runner"></a><a id="copy-submission-experiment"></a>
旧诊断工具包括有限 cohort、带显式 SLO 的配对并发扫描及 copy 提交实现对照，命令见 [runner 操作说明](../experiments/conveyor/AGENTS.md)。它们仍使用有限前瞻成本 profile、排队或准入后开始播放等历史语义，尚未完整实现前文最大上下文、开放到达与拒绝协议；不得直接作为本轮正式评估入口。后续代码对齐以前，已有成功运行只按 Findings 中的诊断范围解释。

<a id="configuration-domains"></a><a id="measured-stack"></a>
### 已登记原型配置

分析使用抽象资源与时间参数；当前运行使用锁定的软件/硬件实例；外部参数场景仅作分析参照。实际配置以配置文件和每次运行的 manifest 为准。

| 参数 | 登记值 |
| --- | --- |
| 模型 | Qwen2.5-Omni-7B |
| 执行路径 | Thinker text only，无 Talker、Code2Wav 或 PCM 输出 |
| 运行时 | vLLM 0.23 |
| 设备实例 | RTX 3090，24 GiB，PCIe Gen3 |

<a id="prototype-streaming-interface"></a>
当前原型通过 `AsyncLLM.generate()` 接收持续产生 `StreamingInput` 的异步生成器，同一 session 沿用同一请求标识。输入处理路径设置内部请求标记 `resumable=True`；该标记不作为 `generate()` 或 `StreamingInput` 的直接参数。调用入口见 [`_run_session`](../engines/conveyor/worker/stream_server.py)，内部流式输入适配也位于该文件。这里记录直接调用引擎的 streaming-input 路径，不等同于已调用 `/v1/realtime` WebSocket 服务；源码核对不构成端到端运行验证。

<a id="measured-workload"></a>

| 参数 | 登记值 | 解释 |
| --- | --- | --- |
| 周期 | 2000 ms | 应用更新目标间隔 |
| 默认会话数 | 8 | 默认配置点 |
| 默认运行时长 | 600 s | 有限观测期限 |
| 输入 | 20 ms PCM chunks 按周期累计 | offered input |
| 输出上限 M | 25 | 每周期预算、first-party worker 每段生成上限与交付上限一致；音频编码长度仍随输入变化 |
| `CONTEXT_GROWTH_TOKENS_PER_PERIOD` | 78 | 当前容量分析配置常数，非已确认净保留增长；定义差异（FINDING-E4）见 [已有证据](findings.md#diagnostic-appendix-fairness-and-measurement) 执行成本诊断 |
| 每 token KV 大小 | 56 KiB | 当前模型与精度的 KV 大小与布局 |

可执行常量位于 `experiments/shared/workload.py`、`model.py` 与 `platform.py`。实际分词、生成和保留历史需要分别记录；恢复重算工作也另计。

默认 cohort 输入由各条目 seed 生成确定性 PCM 噪声，用于系统负载与生命周期验证，不是双人对话数据集。`audio_path` 可指定真实 WAV，来源、采样、长度、offset 与 seed 记录在 cohort manifest。真实模型执行与合成输入须分别说明；固定噪声实验不能支持对话质量或真实交互分布的结论。

平台由 runner 在启动时记录实际 GPU 名称、UUID、显存和驱动，不能由默认 GPU 索引推定设备。当前实现依赖 Linux/NVIDIA CUDA、BF16 与锁定 vLLM 私有接口；copy descriptor 的字节和 stride 来自实际 tensors。换卡须重新检查运行环境、可用 KV pool、计算/传输成本 profile 与并发 SLO，不沿用旧设备标定值作为服务保证。

<a id="executed-decode-difference"></a>
### 生成工作量差异

| 登记系统 | 代码来源/用途 | worker 生成上限 | 其他需匹配的差异 |
| --- | --- | --- | --- |
| Upstream Metronome | 只读上游 pin，来源参照 | 上游行为 | 输入处理、runtime 与观测不同 |
| matched Metronome baseline | 默认 paringest，对比候选 | M | 默认调度、输出等待与 connector 行为 |
| Pilarius | 机制原型 | M | 同步调度、无等待 Step、主机 connector |

当前两个 first-party worker 的每段输入与流结束参数均使用同一输出预算，不再增加额外生成余量。二者均使用 `ignore_eos=True`；模型长度边界和异常仍可能提前停止，上限不构成最低交付要求。初始上下文预加载的单 token 输出属于测量前初始化，不计入周期交付。生成计算可以提前完成，周期节拍限制持续生产和消费的量；该预算不是音频编码长度或实测语音播放速率。

两个 first-party worker 还共用 `engines/audio_features.py`：对重采样后的本次音频，仅补齐到覆盖 STFT 右边界且对齐 hop 的长度，不超过模型原始输入上限。输入长度随实际缓冲变化，不硬截为名义周期。比较前后须检查有效特征、音频 token 数和初始化路径；带显式长度、归一化或 dither 的其他调用保持上游行为。该修正属于实现优化，不是 KV 研究机制；旧长窗口前处理运行不作为修正后性能点。

历史 baseline 使用更高生成上限的旧运行不因当前代码修正而成为公平对照，须重新采集。Pilarius 即使关闭逐出也建立主机 offload connector；登记 baseline 没有同等同步调度配置接口。生成与保留规则影响状态增长，调度及输出等待影响计算成本，失败处理影响统计样本，仍须分别控制。

登记的 Pilarius 接口包括 gateway `--slots`、`--retained-prefix-blocks`、诊断用 `--evict-tail-blocks`、`--prefetch push` 和 `sync_scheduling`。它们不直接等于上文全部消融组；历史实现审计限制见 [已有证据](findings.md#implementation-audit-boundaries)，当前路径须在运行前核验。

新增执行配置为 `--session-manager --retained-prefix-blocks K --restore-lead-s L`。该路径关闭 fixed-tail timer 与 legacy push prefetch，强制同步 scheduler；`L` 必须是周期内的正数。gateway 通过 gRPC metadata 传递计划下一 tick 与周期，缺少 metadata 的 managed input 会被拒绝。每会话区间与块数预算可由 `session_plan` utility 设置，当前 CLI 对各会话使用相同保留前缀；自动预算求解不在此配置内。

`--gpu-trace` 自动启用普通 trace，覆盖完整业务运行：客户端启动前完成 capture 启动，客户端结束后才停止并导出。没有按秒截断的选项；默认关闭以免影响主要性能测量。具体 artifact 集合以 `experiments/conveyor/config.py` 及 manifest 为准。启动与收尾控制属于 runner 生命周期，不能在有业务输入时执行 profiler 导出。

不传 `--gpu-trace` 时不启动 CUPTI/PyTorch GPU capture，`--trace` 可单独开启 CPU 日志。两者都不传也仍有运行状态、KV/transfer 日志以及 copy 正确性所需的 CUDA events/query；关闭 profiler 不等于删除异步完成依赖或保证零观测开销。正式容量实验须以统一的轻量完成指标计量，再用独立诊断 run 解释设备活动。

<a id="candidate-model-integration"></a>
### 候选模型接入：MiniCPM-o 4.5

模型选择通过 `--model-preset qwen25_omni|minicpm_o45` 完成；`experiments/shared/model.py` 分别锁定权重 revision、输入适配器和 BF16 KV geometry，`engines/model_inputs.py` 持有音频 placeholder 与流式追加模板。共享 worker、准入、manager 和 copy 后端保持同一执行入口，配对容量工具也传递相同 preset。MiniCPM 的实际验证状态由 findings 与 evidence 持有，配置可选不等于所有模式均通过验收。

第二模型验证入口为 [FINDING-T6](findings.md#finding-t6) 和 `EVIDENCE-MINICPM-PERIOD-BUDGET`；首个模型的长程分组与完整业务 GPU 观测分别由 FINDING-T4、FINDING-T5 持有。两种模型均未据这些诊断获得正式容量结论。

本机锁定 vLLM 的 `model_executor/models/minicpmo.py` 已有 `MiniCPMO4_5` 分派和音频输入实现，其权重加载路径跳过 `tts`。MiniCPM 前处理使用单实例 Whisper 代理按输入长度限制补零；不修改共享 extractor，也不套用 Qwen placeholder。Session Manager adapter 仍依赖同步 UniProc、单 KV group 和 vLLM 私有生命周期接口。因此新模型除 preset 与输入适配器外，必须核对实际 KV layout 和流式生命周期；不承诺任意模型只改 ID 即可运行。

当前第二模型接入目标是相同周期、固定文本预算的机制控制实验，不是原生双工模式。MiniCPM 的每周期上下文增长不沿用 Qwen 配置常数，需从实际编码、生成与保留历史测量。`--max-model-len`、`--max-num-seqs`、`--gpu-memory-utilization`、`--enforce-eager` 与 `--max-num-batched-tokens` 是显式记录的运行配置；不能为不同实验组暗中改变它们。

每周期文本生成预算由 `experiments/shared/workload.py` 按模型选择，worker 生成、gateway 下发/交付和 manifest 共用同一数值；同一模型的 Pilarius 与 matched resident control 保持一致。当前选择如下，属于实验工作量配置，不是模型的硬性输出限制：

| 模型 preset | 周期 | 每周期文本 token 预算 | 选择依据 |
| --- | --- | --- | --- |
| `qwen25_omni` | 2 秒 | 25 | 保留已确认的固定工作量 |
| `minicpm_o45` | 2 秒 | 8 | [技术报告 §2](https://arxiv.org/html/2604.27393v1#S2)报告正常语速约每秒 3–4 次文本 decode，取上端每秒 4 个，乘以当前周期 |

若修改周期，必须重新选择预算并记录；不能继续使用旧周期的每秒工作量解释。音频编码长度仍随输入变化。旧的第二模型接入诊断使用不同文本预算，其执行时间不作为当前配置的性能对照。

| 接入目标 | 可复用部分 | 需要落实的适配与验证 |
| --- | --- | --- |
| 音频输入、主干文本输出的第二模型 | 已安装 vLLM 模型类；符合相同 KV/执行约束时的 manager 策略与 copy 后端 | model profile 与 revision、模板/processor、KV 几何、流式追加语义、采样/完成与初始化；逐块内容一致和多周期恢复验证 |
| 原生语音双工 | [官方模型卡](https://huggingface.co/openbmb/MiniCPM-o-4_5)的 duplex 接口；[vLLM-Omni 示例](https://github.com/vllm-project/vllm-omni/blob/main/examples/online_serving/minicpmo/README.md)与[双工设计](https://github.com/vllm-project/vllm-omni/blob/main/docs/design/fullduplex.md) | 多阶段音频输出、长期 session/epoch/turn/取消及历史保留；对接各 KV owner 和最后访问/可逐出事件，重新校验 runtime patch 及异步生命周期 |

上游 MiniCPM-o duplex 具有自己的周期决策和 streaming prefill/generate 接口；其 native 模式不能通过当前 Qwen 的固定预算 text-only 工作量模拟后就宣称已支持。vLLM-Omni 上游已有对应 duplex 服务路径，但本地未安装，也不属于现有环境锁；选择固定版本并隔离环境验证，不能静默升级当前 vLLM 环境或假定上游默认并发/内存预算就是容量上限。

建议适配边界：model profile 持有模型与 processor、周期及输出语义；runtime adapter 提供 session/epoch、KV 几何、块分配、最后访问、主机覆盖和恢复完成；manager 消费这些事件与计划，不解析模型专有 token。首先验证上游 native 单会话，再在相同执行路径上接入全驻留和管理组，之后验证多会话、取消和逐出/恢复。语音 decoder/vocoder 等常驻开销及状态都计入资源预算；只管理主干 KV 时须明确其覆盖范围。参考实现存在滑动、压缩或截断时，两组保持同一保留语义，不能为制造容量优势单方关闭。

<a id="initial-context-preloading"></a>
### 初始上下文预加载

登记路径的 `--initial-context-tokens` 通过近似随机词构造和模板控制初始上下文，不能保证目标值等于实际分词长度。正式实验应记录每会话实际长度和所有预加载完成事件，并排除初始化输出。已登记路径在构造期间暂停自动逐出，解除屏障时不立即逐出，后续正常周期再执行策略；运行前核验该路径。

登记路径会记录初始化超时后继续执行，但验收会拒绝该 run 作为成功测量；不能把继续运行解释为状态构造已完成。

<a id="implementation-diagnostics"></a>
### 实现诊断字段

下列字段影响公平性和结果解释；其他日志字段见[运行分析](agent/tasks/analyze-results.md#field-semantics)。

| 字段 | 已登记定义及限制 |
| --- | --- |
| `deadline_met` | 系统间含义不同；Pilarius 表示 RPC 是否在周期内返回，不是模型完成 |
| `gpu_ms` | 路径相关字段；Pilarius 无等待返回不包含本次完整 GPU 工作 |

低于 cap 的交付量可以来自缓冲时序或服务落后，单独不构成失败，也不证明当前模型学会自然短输出或沉默。

<a id="repository-health-gates"></a>
### 运行门槛与证据资格

运行检查与科学判定分开：

- **执行状态：** 进程、RPC、会话和初始化是否正常，终态是否成功。
- **观测有效性：** 必要 artifact、可解析日志、hash 与来源是否完整。
- **机制是否被实际使用：** 逐出/预取事件是否出现；零事件还需判断没有需求、容量门控或实现异常。
- **研究目标：** 服务时限与承载能力是否满足预定标准。

登记 runner 对部分错误、缺失日志和启用机制无事件进行拒绝；这描述运行器规则，不是所有科学问题的通用验收，其跨 runner 差异与覆盖限度由 [contracts registry](agent/contracts.json) 的 CONTRACT-RUN-HEALTH 持有。失败 run 可以支持失效边界分析，但不能记为成功性能点。

<a id="evidence-acceptance"></a>正式性能比较使用可重建的 clean-source 运行、完整配置与有效观测；dirty 诊断需保留 patch。精确 run、hash 和来源由 [证据索引](agent/evidence.json) 解析，artifact 操作遵守 [results 规则](../results/README.md)。

源码无法重建与统计无法复算是不同缺陷。保留日志仍可支持有明确限制的复算，不能据此获得公平或正式证据资格；缺少原始日志则不能重新画成实测结果。历史 artifact 和已引用记录保留原状，纠正通过后续记录表达。

<a id="open-loop-runner"></a>
### 开放回放与匹配控制入口

`--open-loop --cohort-manifest <schedule>` 选择新回放；`replay_metrics.json` 报告 offered/admitted/rejected、按期/超期/未完成工作、从原定 release 与源端齐备时刻计算的延迟、首次 phase 对齐和发送迟到。`measurement_start_s` 是时间表中各系统共用的观测起点，不按每次执行是否成功挑选样本。运行验收拒绝身份、时钟、固定生成预算和事件链不一致；正常拒绝及超期不作为仪器错误掩掉。

`maximum_context` 成本配置使用活跃后端的最大上下文，适用于 assigned phase 与 pre-tick restore。`static_limit` 用独立校准的数量上限支持匹配回载和消融；自然 phase 消融使用固定相同已准入会话集，不将静态控制包装为自然 phase 的联合求解器。`on_demand` 在 CPU 前处理后触发恢复，`after_submit` 与前处理重叠，`pre_tick` 由独立定时器触发。全驻留不创建 host KV pool。旧 finite-horizon、SLO 容忍和全准入 barrier 不进入开放回放。

分配峰值来自物理 GPU block pool 的分配、取得缓存引用和释放事件，包含在途完整目的分配；可回收的无引用缓存不计为 allocated。该观测与旧 residency 快照分开。模型完成事件还保存实际上下文长度，不能用配置上限代替实际长历史覆盖。短运行或限定 KV pool 的机制检查须注明该配置，不能作为整卡容量结论。

输入准备可使用 [LibriSpeech dev-clean](https://www.openslr.org/12) 的录音语音（CC BY 4.0）：按 speaker 将原始片段依词典序直接拼接，保留采样率，不插静音、不循环；archive 官方校验值、逐片段 hash 和 WAV hash 随素材 provenance 保存。这是系统服务负载，不能据此宣称真实对话质量或原生双工交互效果。

`experiments.conveyor.evaluate` 先冻结各点时间表、成本文件 hash 和随机化运行顺序，再逐点启动独立 worker；formal 模式要求同一 clean commit。`infra.trace.calibration` 从校准 run 提取按组成本、整段恢复的有效服务率和备份成本，默认加安全余量；这些 CPU 观察包含排队及干扰，不是纯 DMA 上界。`infra.trace.evaluation` 校验全部来源 hash 后汇总，缺点不静默丢弃。模型、配置、观测窗口与 seeds 随冻结 plan 保存。

`--verify-copies` 是侵入式正确性诊断：每次物理 KV 复制完成后、引用释放及内容发布前，对所有层的源与目标做逐字节检查。它同步设备，formal 性能矩阵拒绝启用。输出 token hash 则用于检查相同输入的实际生成；差异须进一步隔离，不能单凭复制一致推断完整模型语义等价。

主机峰值当前统计 host pool 中已确认有效的物理 backing，包括已结束会话留下的可回收缓存；它不同于活跃会话必须保留的 backing 或固定预分配的主机池大小。两者在报告中分别标明。

首轮受控矩阵固定后端最大上下文为 2,048 token，以有限 KV pool 验证工具链和机制：MiniCPM-o 4.5 使用 1 GiB，Qwen 使用 `56/144 GiB`，使两个模型按各自 BF16 KV 几何具有相同量级的逻辑块容量；这不是跨模型同字节预算性能排名。模型内的三个系统使用完全相同资源。固定队列分别连续输入 72 和 50 秒，公共统计起点分别为 58 和 36 秒，同时保留全过程事件和实际历史长度。seed 1729 仅用于校准；重复评估使用独立 seeds 11、22、33。这些是首轮测量配置，不冻结最终论文上下文、设备或模态范围。更长历史与整卡预算仍需扩展覆盖。


首轮执行矩阵在上述受控条件下展开；系统内使用共同输入、三个独立评估 seeds，并为每点启动 fresh worker：

| 模型 | 容量 offered sessions | 动态到达 | 消融 offered sessions |
| --- | --- | --- | --- |
| MiniCPM-o 4.5 | 1、3、4、8、13 | 每秒 2/72、3/72、8/72 个会话；到达窗口 144 秒 | 8 |
| Qwen2.5-Omni-7B | 3、6、11 | 本轮不重复动态矩阵 | 6 |

容量比较三个系统，动态比较全驻留与 Pilarius，消融只补自然 phase 和提交后预取。合计 102 个独立点，先执行主模型边界点。该计数不包含校准或侵入式正确性检查；拒绝、超期或未完成属于各点结果，不因不利而删除。静态准入上限及所用成本的独立校准由 `EVIDENCE-CONTROLLED-CALIBRATION` 解析。


### 本轮正式补测设置与顺序

本轮在当前 H100 上先完成正确性与成本标定，再冻结三组正式矩阵；复用 MiniCPM-o 4.5 的共享音频输入／固定文本预算路径。主要容量证据使用真实长历史和可供模型使用的大 KV 池，小池历史仅作机制诊断。并发点、静态上限、预算及恢复提前量从独立校准选择；正式数据不反向调整同一矩阵的参数。每个正式点独立启动，共同 seeds 11、22、33；校准使用 seed 1729。

固定队列的初始历史采用可重建、逐会话不同的确切 token 数，初始化在共同输入时钟前完成；managed 初始化允许确认备份后的安全逐出，不要求所有最大历史同时常驻。动态队列使用 `preload_at_start=false`，每个已接纳会话在首次执行时构建相同规则的初始历史；预填充时间计入初次更新的等待，不预先构造未来会话，不推迟源时钟或 deadline。初始化产生的一个状态构造 token 不计入周期输出；完成事件用 frame 0 区分初始化。

GPU 正式测量串行执行，启动前检查其他 GPU 进程与网关端口；不能用显存尚有余量推断计算或复制不受干扰。独立物理搬运检查与侵入式逐字节模型检查单独运行，不计入性能。最终矩阵及证据登记后在此补充实际资源、历史、观察窗口和配置取值。
