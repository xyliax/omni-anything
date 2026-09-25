# 评估计划与复现

<a id="evaluation-questions"></a>
## 评估问题

评估围绕承载能力、服务代价与机制因果关系组织。表中是待执行的研究计划，不预设任何系统获胜。

| 问题 | 比较与观测 | 要检验的结论 | 不支持该结论的结果 |
| --- | --- | --- | --- |
| Q1：KV 容量何时先限制服务？ | 扫描并发与上下文，同时测容量、模型进度、排队和计算 | 存在明确的 KV 容量受限区间 | 输入处理或计算始终先饱和，容量动机未在该域成立 |
| Q2：能承载多少满足目标的会话？ | 同输入、参考语义和服务目标下比较全驻留与 Pilarius | 给定期限和负载分布下的容量收益 | 降低驻留却没有增加达标承载能力 |
| Q3：减少驻留付出什么延迟代价？ | 输入到结果的分布及恢复关键路径分解 | 收益与响应代价的可量化关系 | 延迟/落后违约抵消容量收益 |
| Q4：每项机制分别贡献什么？ | 偏移、主机副本、逐出、预取与组合对照 | 机制的独立作用及相互影响 | 收益来自未匹配的生成量或执行模式 |
| Q5：资源模型能否预测新配置？ | 独立标定、未参与标定的配置验证瓶颈与预测误差 | 对容量、计算和恢复边界的解释 | 依赖逐点回拟合，无法预测瓶颈变化 |
| Q6：搬运是否保持保留状态的语义？ | 相同输入参考执行、状态往返一致性 | 逐出与恢复对参考执行透明 | 状态不一致或输入丢失 |
| Q7：何时无益或失效？ | 短会话、低负载、迟到、覆盖缺口、带宽/主机容量压力 | 开销与适用边界 | 应如实报告，不从主图删除失败区域 |

先验证资源问题与正确性，再比较承载能力和代价；通过消融与独立配置验证解释原因。保留无收益和失败配置。

Q1 的主证据是 KV 容量限制并发时，整组会话每周期仍有可用计算预算。测量该边界附近的整组执行时间和剩余时间比例，使用独立配置检验[条件分析](problem.md#slack-conditions)，包括预测无余量的区域。再通过额外会话工作验证余量是否可用，同时报告恢复干扰、完成进度和原服务目标；单会话空闲或较低设备利用率不足以支持该结论。

<a id="workload-and-platform-matrix"></a>
## 工作负载与平台矩阵

代表性工作负载与受控压力负载承担不同作用：前者评估实际服务价值，后者定位资源边界。两者都需给出生成过程和适用范围。

| 维度 | 应覆盖的变化 | 待补材料 |
| --- | --- | --- |
| 应用时间要求 | 固定更新、可容许抖动、不同周期；偏移是否可控 | 选定应用原始论文或协议，以及时间事件映射 |
| 会话生命周期 | 短/长会话、混合长度、加入退出、持续增长 | 数据来源、分布、种子、初始上下文和观测期限 |
| 输入与输出工作 | 输入内容/速率、生成量及保留历史、输出阶段 | 精确单位和各阶段工作量，避免只匹配 token/s |
| 保留策略与历史依赖 | 保留策略（完整历史或有上限的窗口/摘要状态）及跨更新复用程度 | 保留策略参数来源与状态规模依据 |
| KV 大小与布局 | 不同模型、上下文范围、KV 精度与共享比例 | 每种模型状态字节及计算成本映射 |
| 资源条件 | GPU 可用 KV 容量、主机容量、双向链路、拓扑 | 设备/互连清单、NUMA 与并发传输标定 |

Introduction 使用 MiniCPM-o 4.5 作为具体例子；周期、KV 大小与布局的来源见[外部参数核验](references/minicpm-o-4.5-kv-geometry.md)。本轮实验计划使用单 GPU；具体卡型、主机与互连配置待选，模型与负载矩阵仍待确定。单卡是本轮实验安排，不限制研究问题的适用范围。平台选择与条件估算见下节。

优先选择能够改变关键资源比例的配置，并据实际覆盖说明结果的适用范围。额外模型、输出路径或设备拓扑尚未覆盖时标明未测；最终矩阵确定前不据当前原型删减研究范围。

<a id="cross-hardware-projections"></a>
### 跨硬件条件估算

Background 的表框架比较 GPU、估计可用 KV 池、`L_mem`、预测完整周期占比 `C_hat_N(L_mem)/T` 的敏感性范围、证据类型及瓶颈判断。比较固定模型、权重与 KV 精度、周期 `T`、会话数 `N`、输入及时间对齐生成分布、执行/批处理策略和延迟统计口径。各卡 `G_KV` 扣除完整模型状态及运行开销；未测项明确标为假设。实测和经校准预测分别标注，校准与验证点分开，第二平台可采用少量独立验证点。峰值 FLOPS 和显存带宽只给出理想耗时下界，不能据此断言容量一定先受限；敏感性范围不是统计置信区间。填入有依据的数字和判断前各行保持 pending，不预设所有卡得到相同结论，最终实验矩阵仍未冻结。

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

<a id="evaluated-systems"></a>
## 被评估系统

<a id="comparison-families"></a>
### 比较系统与公平性

| 比较对象 | 目的 | 公平性要求 |
| --- | --- | --- |
| 完整历史、GPU 全驻留 | 容量与延迟参照（[问题定义的参照策略](problem.md#why-historical-kv-state-can-limit-capacity)） | 相同参考执行和输入管线；报告准入上限与失败 |
| 完整历史、缺失状态重算 | 衡量恢复所需计算代价 | 相同历史与目标工作，不把缩短生成当作优化 |
| 完整历史、按需主机回载 | 隔离提前恢复的价值 | 匹配副本策略、缓存预算与传输实现 |
| Pilarius 及其消融 | 验证时序与驻留策略 | 除目标变量外逐项对齐实现和工作量 |
| 最接近的持续会话/KV 管理系统 | 验证相对已有工作的增量 | **待选：** 原始论文、可执行实现、版本、适配与缺失能力 |
| 窗口、压缩或摘要等保留策略 | 作为负载参数改变单会话保留状态规模，检验驻留机制在不同保留策略下的可组合性 | 单列语义差异；不承担判定保留策略之间应用质量的义务 |

不可获得或无法适配的系统应说明原因，并区分重实现、分析参照和实测基线。窗口化等保留策略作为负载参数进入比较，而非作为必败基线；实验不设计使其失败的任务，也不判定保留策略之间的质量取舍。

<a id="fairness-checklist-for-the-protocol"></a>正式比较应固定模型与精度、输入内容及处理语义、实际生成工作、参考历史、调度模式、批处理预算、缓存与主机副本预算、输出交付定义和观测开关。若某项机制必须改变其中一项，增加对应控制组并单列代价。

端到端系统比较可以包含整体设计差异；声称某项机制造成收益时则需要控制变量。相同配置名称、offload 开关关闭或相同默认值均不能代替实际路径核对。

<a id="ablation-matrix"></a>
### 消融矩阵

下列配置是目标实验矩阵，尚不能从现有开关直接推定已具备全部控制组。

| 配置 | 释放策略 | 主机副本 | idle 逐出 | 恢复触发 |
| --- | --- | --- | --- | --- |
| 全驻留控制 | 同步/均匀偏移成对 | 无 | 无 | 无 |
| 副本开销控制 | 固定释放策略 | 有 | 无 | 无 |
| 按需恢复控制 | 同上 | 有 | 有 | 当前需求 |
| 提交后预取 | 同上 | 有 | 有 | 输入提交后、模型使用前 |
| 基于节奏预取 | 同上 | 有 | 有 | 预计未来需求 |

逐出组再配同步与偏移对照；扫描每会话逐出量、slot 分配、启动余量和资源压力。均匀 phase 下区分相同与异质恢复量，分别测每周期流量、平均驻留和峰值驻留；不能以满带宽代替容量收益。[主动重算扩展](system.md#future-recomputation)的传输、重算及混合对照留待后续研究，不作为当前机制消融的完成条件；重算作为独立比较基线的角色不变。

各组分别检查当前需求、提交后信息和计划释放时刻的作用；同步与偏移对照检查 phase 控制。固定参考历史、主机副本和传输路径，记录信息产生、恢复发起和计算开始时刻。若使用未来信息完全已知的参照，单列其额外信息优势。实现后逐一核对各组实际使用的信息，不能只比较开关名称。

<a id="measurement-semantics"></a>
## 测量语义

<a id="service-and-capacity-metrics"></a>
### 服务与容量指标

| 指标 | 定义要求 |
| --- | --- |
| 周期完成延迟 | `c(i,k)-r(i,k)`，从计划 tick 到本周期生成完成；目标为下一 tick 前完成 |
| 提交后服务时间 | `c(i,k)-a(i,k)`，仅作诊断；同时记录 `a-r`、首次对齐等待和输入积压 |
| 用户可见延迟 | 从原始输入内容的时间基准到相关结果；包含切块、缓冲与后处理 |
| 更新落后 | 根据已处理输入进度与已到达输入进度定义；不能从 RPC cadence 推断 |
| 违约率与延迟分布 | 给出目标、允许比例、分位数和窗口；失败/超时样本单独计数，不丢弃 |
| 达标承载能力 | 在指定期限、上下文/会话分布与服务标准下可接纳的负载；同时报告 offered、admitted 与 completed |
| KV 占用 | GPU 已分配空间、有效内容、可复用缓存和主机副本分别计数；共享块不重复计算 |
| 恢复开销 | 字节、发起排队、实际传输、完成上报及等待再次调度分别测量 |
| 计算开销 | 模型步数、批形状、有效生成与重算工作、kernel 活跃时间及 CPU 开销 |

**已确认的分析约定。** 第 `k` 周期 soft deadline 为下一 tick：`c(i,k) <= r(i,k+1)`，相对目标为 `D_i=T_i`。`c` 取本周期模型生成完成；对不同输出架构需给出对应事件。推迟提交不顺延 deadline，不能假定所有稳态运行都有 `a=r`。首次 phase 对齐等待单列，后续排队和积压保持可见。

网络传输暂按固定延迟处理；合成、播放和客户端处理不由这一假设覆盖。输入时间、模型完成和用户交付仍需分开。

**待定。** 允许违约比例、统计窗口、观察期限、持续落后和会话失败判定条件。落实前只报告已定义的量，不宣称达标承载上限。已有 RPC 和消费字段不是该目标的实现证明，映射限制见[实现诊断字段](#implementation-diagnostics)。

持续增长的完整历史通常使总体负载非平稳。必须报告随时间和上下文变化的轨迹；局部近稳态窗口需要说明选择规则，不能用其证明无限时长稳定。比较不同系统时使用相同的输入时间基准和观测期限。

针对[准入规划与低频修正](system.md#planning-updates)，测量每周期 KV 增长的分布及累计变化，并记录预测范围、预测误差、规划修正次数、计算开销和修正前后的服务表现。长期增长与会话加入退出分别评估，以检验计划能沿用多久、何时需要调整；不能从平均增长率直接推定不存在突发变化，也不能用单个预测范围内的成功代替持续运行评估。

<a id="profiling"></a>
### 关键路径分析

先分解关键路径，再解释资源瓶颈。scheduler 墙钟计时可以包含等待，不能等同 GPU kernel 忙时。H2D 发起至完成上报的窗口可以包含调度延迟，不能直接当作 DMA 时长或据此推导物理带宽。

**待补采集：** 跨层事件关联、传输 CUDA event、kernel 活跃区间、HBM 流量和探针开销。每项探针记录生产位置、时钟、开关与开销；带重型 profiling 的诊断 run 与主要性能采集分开，并验证扰动。

<a id="correctness-and-quality-protocol"></a>
## 正确性协议

1. 固定参考输入、模型配置和生成历史保留语义，比较有无状态搬运时的块内容与模型结果；非确定性路径报告容差及控制方法。
2. 覆盖共享前缀、未满块、主机覆盖缺口、在途传输、容量拒绝、会话停止/取消及输入失败。
3. 将语义一致与时限达标分开报告；运行未崩溃不能替代其中任何一项。保留策略之间的应用质量取舍属应用侧参数，不在本协议判定范围内。

**待补：** 数据集与许可、重复种子、非确定性容差、故障注入与判定规则。

<a id="resource-model-validation"></a>
## 资源模型验证

独立测量 KV 几何、批处理相关计算成本、有效 GPU KV 池、主机副本容量、双向及并发传输服务曲线。在部分配置上标定，用未参与标定的配置验证预测误差和瓶颈分类，并报告模型失效处。

多设备条件下依据实际互连、NUMA、主存和通信竞争建模；不能预设只有恢复带宽非线性，或增加设备必然不增加恢复能力。相同输出 token 率也不能自动跨模型/多阶段输出换算容量：需要状态字节和计算路径的明确映射。

**待补：** 参数表、标定/验证划分、误差指标、误差接受标准，以及不确定性传播。

<a id="run-protocol"></a>
## 运行协议

每个正式数据点使用固定版本和展开后的配置，记录实际初始状态、输入生成过程、随机种子、预热和观测区间。重复运行并报告运行级变异；同一 run 内多个会话不能自动当作独立重复。预先定义超时、失败、异常值和终止条件，并保留全部试验的归属。

主结果应同时给出承载能力、尾延迟及资源代价。容量提升没有通过服务目标时，仍报告驻留变化与失效原因，但不计为达标容量收益。

**待补：** 运行次数、置信区间方法、扫描粒度、并发边界搜索算法、总时程及停止规则。

<a id="reproducibility-appendix-current-prototype"></a>
## 复现附录：当前原型

以下保留已登记原型的配置与诊断解释。运行前核验可执行配置、实际路径和 run manifest；旧登记状态不证明新设计已实现。证据与比较资格见 [已有证据](findings.md#evidence-scope)。

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
| 输出上限 M | 25 | harness 与消费上限；worker 差异见下表 |
| `CONTEXT_GROWTH_TOKENS_PER_PERIOD` | 78 | 当前容量分析配置常数，非已确认净保留增长；定义差异（FINDING-E4）见 [已有证据](findings.md#diagnostic-appendix-fairness-and-measurement) 执行成本诊断 |
| 每 token KV 大小 | 56 KiB | 当前模型与精度的 KV 大小与布局 |

可执行常量位于 `experiments/shared/workload.py`、`model.py` 与 `platform.py`。实际分词、生成和保留历史需要分别记录；恢复重算工作也另计。

<a id="executed-decode-difference"></a>
### 生成工作量差异

| 登记系统 | 代码来源/用途 | worker 生成上限 | 其他需匹配的差异 |
| --- | --- | --- | --- |
| Upstream Metronome | 只读上游 pin，来源参照 | 上游行为 | 输入处理、runtime 与观测不同 |
| matched Metronome baseline | 默认 paringest，对比候选 | M+8 | 默认调度、输出等待与 connector 行为 |
| Pilarius | 机制原型 | M | 同步调度、无等待 Step、主机 connector |

登记路径中的两个 first-party worker 均使用 `ignore_eos=True`，正常路径运行到不同 cap；模型长度边界和异常仍可能提前停止。Pilarius 即使关闭逐出也建立主机 offload connector；登记 baseline 没有同等同步调度配置接口。生成与保留规则影响状态增长，调度及输出等待影响计算成本，失败处理影响统计样本。修正差异后须重新采集公平对照。

登记的 Pilarius 接口包括 gateway `--slots`、`--retained-prefix-blocks`、诊断用 `--evict-tail-blocks`、`--prefetch push` 和 `sync_scheduling`。它们不直接等于上文全部消融组；历史实现审计限制见 [已有证据](findings.md#implementation-audit-boundaries)，当前路径须在运行前核验。

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
