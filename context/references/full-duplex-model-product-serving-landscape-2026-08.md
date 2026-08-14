# 全双工模型、产品与 serving 版图（2026-08）

Updated: 2026-08-03
2026-08-07 快照：并入产品与文献查证的证据层；术语统一为全双工。

## 划界

本文整理外部公开规格与证据，不是本仓库结论。

只把下面这种系统算作**模型级全双工（model-level full-duplex）**：模型在输出期间继续吸收输入，并把 silence、overlap、backchannel、打断或主动开口当作模型时间上下文或学到的动作。以下两类不自动算：

- WebSocket 能同时收发，或用户说话时取消 TTS；
- `VAD 判停 → ASR → 文本 LLM → TTS`，即使各模块都做成 streaming。

**tick** 指模型或调度器完成一次交互决策的原生时间量子，不是网络包长、首包延迟或评测给定的 deadline。
容量数字分为「实测」「config cap」「下界」「外推」；没有数据一律写「未披露」。
**N\*** 指可调度并发数（schedulable concurrency），本文按 miss rate ≤ 1% 的判据读。

公开证据摘要（截至 2026-08-07）：

1. 能同时证明「模型级全双工 + 大规模生产上线」的只有 **GPT-Live** 和 **Seeduplex**；两家都不公开参数、tick、上下文和单 GPU 容量。MiniCPM-o 4.5 已有官方托管的 Realtime API，但没有公开流量或 SLA。
2. 开源侧给出多会话 WebSocket / Ray / SGLang 服务端较完整的是 **Raon-SpeechChat**，但 `2 sessions/GPU` 只是默认 config cap，不是测得的最大值。多数论文只有单会话演示或离线推理。
3. 系统性公开「单 GPU 能撑多少路、短测与长会话为何不同」的是 **Metronome**；它是 serving 系统，不是模型。其结果说明 `90 s` 突发容量不能当作可持续容量。严格主表中的工作均未公开端到端 GPU / SM util 或 MFU。

## 1. 已上线或前沿闭源模型

| 工作 | 首次公开 | 是否用于上线 serving | 原生 tick | 参数 | 单会话上下文 | 单 GPU 最多会话 | 量化精度 / 硬件 / 实现 |
| --- | --- | --- | ---: | ---: | --- | --- | --- |
| [GPT-Live][gpt-live] | **2026-07-08**，官方发布 | **是，生产**。GPT-Live-1 为 ChatGPT Voice 的 Go/Plus/Pro 默认，mini 为 Free 默认；API 尚未开放；官方称 Voice/Dictation 周用户超过 1.5 亿（不是并发数） | 未披露；仅称每秒多次决定 `speak/listen/pause/interrupt/tool` | 未披露 | 未披露 | 未披露 | 未披露 |
| [Seeduplex][seeduplex] | **2026-04-09**，官方发布 | **是，生产**。已 fully rolled out 到豆包 App，官方称服务数亿用户 | 未披露 | 未披露 | 未披露 | 未披露 | speculative decoding + 量化；量化精度、GPU 未披露 |
| [TML-Interaction-Small][tml] | **2026-05-11**，研究预览 | **否**。页面仍称未来开放 limited preview | **200 ms** micro-turn | **276B MoE / 12B active** | 未披露；官方明确超长 session 仍是问题 | 未披露 | Blackwell、NVLS、自定义 MoE gather+gemv、batch-invariant kernels、持久化 SGLang streaming session；GPU 数量/量化精度未披露 |

注意：GPT-Live 与 `GPT-Realtime-2.1` 不是同一个公开产品定义；后者见第 7 节边界表。

### 两家生产系统的官方措辞与公开数字

- **GPT-Live**：官方描述为 "continuously processes input while generating output"，每秒多次决定 "whether to speak, continue listening, pause, interrupt, **or invoke a tool**"；复杂问题委托 GPT-5.5 在后台执行，结果送回同一段对话。
  [系统卡][gpt-live-card]无架构数字，API 未开放。单次会话时长只有社区实测（Simon Willison 在 HN 报 ≥1 小时，轶事级）。
- **Seeduplex**：官方自称全球首个原生全双工语音大模型，"listen while speaking"，模型逐步决策 start replying / continue listening / respond to interruptions。
  公开数字全部是相对上一代的相对值：端点延迟约 −250ms、打断响应约 −300ms、误响应与误打断减半、抢话 −40%、流畅度 MOS +12%；tick 长、模型尺寸、API 均未给。
  工程侧自述用投机解码加量化控成本，并明确承认克服了「高并发下的延迟尖刺与稳定性问题」，解法未公开。

## 2. 公开模型与研究原型：规格和 serving 事实

### 2.1 tick 与参数

| 工作 | 首次公开 | 原生 tick | 参数 |
| --- | --- | ---: | ---: |
| [Moshi][moshi] | **2024-07-03** 首次介绍；09-17 论文 v1；09-18 开源 | **80 ms**（Mimi 12.5 Hz） | Helium **7B** 主干；完整 Moshi 总参数未汇总披露 |
| [PersonaPlex][personaplex] | **2026-01-14**，论文 v1 | **80 ms**，继承 Moshi | Moshi **7B** 微调；总参数未另报 |
| [Human-1][human1] | **2026-04-25**，论文 v1 | **80 ms**，继承 Moshi | Moshi/Helium **7B** 路径；总参数未另报 |
| [MoshiRAG][moshirag] | **2026-04-14**，论文 v1；04-30 官方博客 | **80 ms** | 7B Moshi 前台 + 1B 流式 ASR；默认后台 Gemma-3 27B，也可 GPT-4.1/Tavily |
| [MiniCPM-o 4.5][minicpmo] | **2026-02-03** 模型开源；04-30 论文 v1 | **1.0 s**；0.2/0.1 s 仅为质量明显下降的消融实验 | **9.34B total** |
| [Raon-SpeechChat][raon] | **2026-04-08**，论文 v1 | **80 ms**（12.5 Hz；网络帧也正好 1920 samples@24k） | 品牌称 9B；精确 full model 约 **9.8B**（8.8B shared + 约 1.008B encoder/adaptor） |
| [Fun-Audio-Chat-Duplex][funaudiochat] | **2025-12-23**，论文 v1 | 共享主干 **5 Hz = 200 ms**；细化 speech head 25 Hz | dense **8B**；MoE **30B total / 3B active** |
| [Covo-Audio-Chat-FD][covo] | **2026-02-10**，论文 v1 | **160 ms**；1 个 6.25Hz 输入特征对 4 个 25Hz 输出 token | **7B**，Qwen2.5-7B-Base 路径 |
| [DuplexSLA][duplexsla] | **2026-05-20**，论文 v1 | **160 ms**；2×80ms 用户特征 + 4×40ms 助手 token；每 tick action ≤10 token | **7B**，从 Step-Audio 2 mini 初始化 |
| [DuplexOmni][duplexomni] | **2026-06-08**，论文 v1 | **480 ms**，每 tick 6 个 Mimi frames | Qwen3-Omni **30B total / 3B active** 交互基座；完整系统还含 Talker/Code2Wav 与外部 S2，不能说全系统仅 30B |
| [BayLing-Duplex][bayling] | **2026-06-12**，论文 v1 | **800 ms 决策块**；底层 speech token 80ms，但每 10 个 token 才决策一次 | **9B LLM**；tokenizer/decoder 额外参数未汇总 |
| [Wan-Streamer v0.1][wan] | **2026-06-23**，论文 v1 | **160 ms** 流式单元；模型侧 signal-to-signal 约 200ms | 未披露 |
| [RoboEgo / FLM-Ego][roboego] | **2025-06-02**，论文 v1 | **80 ms 理论值** | **7B 主干**；模态 heads 的总参数未汇总 |
| [SyncLLM][syncllm] | **2024-09-23**，论文 v1 | **160/200/240 ms**，主设定 160ms | Llama-3 **8B** |
| [OmniFlatten][omniflatten] | **2024-10-23**，论文 v1 | 10 个 speech-token/chunk；按其 CosyVoice2 25Hz tokenizer 约 **400 ms（外部速率推导）**，论文没有直接写毫秒 | Qwen2 **0.5B 主干**；完整 audio 模块总参数未汇总 |
| [SALMONN-omni][salmonn] | **2025-05-17**，论文 v1 | **80 ms**；但 speech synthesizer 4 个 LLM token 才产 480ms 语音，启动另有 320ms 设计延迟 | Llama-3 **8B** + CosyVoice2 **0.5B** + Mamba encoder；总参数未汇总 |
| [Voila-autonomous][voila] | **2025-04-28** 权重/推理代码；05-05 论文 v1 | **未披露**；195ms 是响应延迟，不是原生 tick | 完整总参数未披露；HF config 是 32 层、4096 hidden 的 Llama-style 主干 |
| [LSLM][lslm] | **2024-08-05**，论文 v1 | audio-token tick 未显式换算为毫秒；训练目标要求在打断开始后 **0.5 s** 内 IRQ | 106M decoder + 34M vq-wav2vec encoder；vocoder 未计入，故完整总参数未披露 |

### 2.2 serving / 开源状态与单会话上下文

| 工作 | serving / 开源状态 | 单会话上下文 |
| --- | --- | --- |
| Moshi | `moshi.chat` 研究演示 + 自部署服务端；无托管 API/SLA；官方主路径没有多会话容量报告 | 3000 时间步，约 **4 min**；论文另称实验可到约 5 min |
| PersonaPlex | NVIDIA 研究演示 + 自部署；无商业 API | 3000 步，约 **4 min** |
| Human-1 | 论文；未核验到公开 live 服务端、权重或容量报告 | **2048 步 ≈2.7 min** |
| MoshiRAG | 推理代码 / 演示视频；非 live API | 继承 Moshi，约 **4 min** |
| MiniCPM-o 4.5 | 官方托管 [Realtime API][minicpmo-realtime-api] + web/本地演示；05-17 公布 API 服务；无流量/SLA | 主 LLM **40,960**；speech decoder **4096**；无经验证的墙钟 session 上限 |
| Raon-SpeechChat | 官方在线演示；公开 WebSocket + Ray GPU 池 + SGLang 多会话服务端；无生产流量/SLA | 论文训练 **4096 ≈2 min**；公开 runtime 默认 KV `8192`，约 4 min，后者不是长时质量证明 |
| Fun-Audio-Chat-Duplex | **full-duplex（FD）版本没有公开权重/服务端**。已发布的 8B checkpoint、web 演示和约 24GB 推理要求对应通用 Fun-Audio-Chat，不能当成 FD serving 证据 | **2048 tokens ≈6 min** |
| Covo-Audio-Chat-FD | **FD checkpoint 未发布**；只开源了 Covo-Audio-Chat（半双工）及推理流水线 | 训练/SFT 序列长度 **8192**；墙钟上限未披露 |
| DuplexSLA | 只有技术报告和演示页；README 明确 checkpoint、推理/服务端、评测产物 **coming soon** | 未披露 |
| DuplexOmni | 公开数据/训练/改过的 vLLM serving 代码，但数据和 checkpoint 仍是 external placeholder；当前编排器为单 session | thinker/talker runtime 上限 **32,386**；未给经验证的墙钟 session |
| BayLing-Duplex | 权重 + 离线音频文件 CLI；未发现正式 live 多用户服务端 | config **32,768**；按每 0.8s 固定 25 个序列化 token，空 prompt 理论约 17.5min，**推导值、非长时实测** |
| Wan-Streamer v0.1 | 概念验证；未核验到权重/代码/live 服务 | 称 full-history KV，未给窗口数字 |
| RoboEgo / FLM-Ego | system card + 演示；未核验到公开权重/代码/live serving | 未披露 |
| SyncLLM | 论文与音频样例；无已核验生产 serving、容量或正式 checkpoint/服务端 | **8192 序列化 tokens**；因 speech-token 去重，墙钟长度不固定 |
| OmniFlatten | 论文；未核验到 production/live 多用户服务端 | **8192 tokens**；墙钟长度未披露 |
| SALMONN-omni | 仓库有 demo 对话；未核验到 live 服务端、公开 FD checkpoint 或容量报告 | 未披露 |
| Voila-autonomous | 权重、离线推理、Gradio/HF 演示；公开 autonomous 路径输入的是预录音频，不是经验证的生产 live 多用户 serving | HF config `max_position_embeddings=8192`；墙钟长度未披露 |
| LSLM | 早期研究原型；无生产服务端。能力是「生成给定 TTS 内容时听取另一通道并发出 IRQ」，不是完整开放域 speech-to-speech agent | 未披露 |

### 2.3 单 GPU 容量、量化与硬件、证据等级

| 工作 | 单 GPU 会话数 | 量化精度 / 硬件 | 证据等级 |
| --- | --- | --- | --- |
| Moshi | 官方未披露；Metronome 第三方在单 RTX PRO 6000 Blackwell 上测得 **≥32** | PyTorch BF16/实验 INT8；MLX INT4/INT8/BF16；Candle INT8/BF16 | 官方未披露 + 第三方 90 s 下界 |
| PersonaPlex | 未披露 | 官方 checkpoint 为 BF16；支持 CPU offload；训练 8×A100、6 h 不是 serving 配置；无官方量化 checkpoint | 未披露 |
| Human-1 | 未披露 | bf16；训练 8×H100 80GB，不是 serving 配置 | 未披露 |
| MoshiRAG | 未披露 | 单流评测：前台在 1×H100，本地 Gemma 后台另占 1 GPU；量化未披露 | 未披露（论文为两 GPU 单流拓扑） |
| MiniCPM-o 4.5 | 官方未披露；Metronome 第三方：单 Blackwell 约 **96** 路 90 s 新会话；windowed KV 在 N=96 维持 10 min | llama.cpp-omni INT4：RTX 4090 11GB、RTF 0.21；PyTorch INT4 约 14GB；BF16 4090 OOM | 官方未披露 + 第三方实测 |
| Raon-SpeechChat | **默认 config cap = 2/GPU，非实测最大值**；GPU 型号与压测曲线未披露 | BF16/FP16；权重约 25GB；16GB+ 显存 recommended；无官方量化 checkpoint | config cap |
| Fun-Audio-Chat-Duplex | 未披露 | FD 量化/硬件未披露；已发布非 FD 8B 路径约 24GB 显存 | 未披露 |
| Covo-Audio-Chat-FD | 未披露 | FD 量化、serving GPU、容量未披露 | 未披露 |
| DuplexSLA | 未披露 | 每 tick 预算声称适配主流加速器，但未披露 GPU、量化或容量 | 未披露 |
| DuplexOmni | 单 GPU 不适用/未披露；公开默认拓扑是 **1 session / 8 GPUs**（thinker TP4 + talker TP4），不是容量压测 | dtype `auto`；无公开量化 | 编排器代码上限（config cap） |
| BayLing-Duplex | 未披露 | BF16；GPU 型号/量化未披露 | 未披露 |
| Wan-Streamer v0.1 | 单 GPU 未披露；论文路径是 **2 GPUs / 1 session**（GPU0 thinker、GPU1 performer），GPU 型号未披露 | 量化未披露；当前输出 192p | 未披露（论文单流拓扑） |
| RoboEgo / FLM-Ego | 未披露 | 量化/serving 硬件未披露 | 未披露 |
| SyncLLM | 未披露 | serving 精度/硬件/量化未披露；128×A100 是训练硬件 | 未披露 |
| OmniFlatten | 未披露 | 量化/serving 硬件未披露 | 未披露 |
| SALMONN-omni | 未披露 | 量化/serving 硬件未披露；32×A100 是训练硬件 | 未披露 |
| Voila-autonomous | 未披露 | BF16；无官方量化/容量数据 | 未披露 |
| LSLM | 未披露 | 未披露 | 未披露 |

### 2.4 按官方配置换算的会话时长（推导值，不是长时实测）

hertz-dev 2048 token ≈ **4.3 分钟**；Moshi 环形 3000 步 ≈ **4 分钟**（FAQ 的 5 分钟上限即此）；SyncLLM 8192 ≈ **4.5 分钟**（论文自认 limitation，且 speech-token 去重后实际墙钟长度不固定）；GLM-4-Voice 8192 ≈ **10 分钟**；Qwen2.5-Omni 32k ≈ **20 分钟**。
能换算出墙钟长度的开源工作，单会话上下文都落在 20 分钟量级以内；产品侧的会话与上下文上限同构，见第 7 节。

### 2.5 DuplexOmni 的配置核验

论文 §3.1.2 用**固定 480ms 时间片**；每片 thinker 产出 "mₜ Assistant tokens"，**论文只给符号 m_t，没有给数值**。
talker 每片 6 个 codec 帧（12.5Hz，第 0 层自回归 + 多 token 预测 MTP）。
输入率继承 Qwen3-Omni 配置 `position_id_per_seconds: 13`，折合约 6 token/片。
thinking 层的异步注入是其官方设计，注入通道已在模型侧标准化（第 8 节）。
权重现实：Qwen3-Omni-30B-A3B bf16 实测 **70.5GB**（Hugging Face 15 个分片加总），80GB 卡上仅 bf16 权重就接近吃满，FP8 因此是全双工部署的起点而非优化（Metronome 亦用 FP8）。

## 3. Serving 配置、并发和 GPU 指标审计

公开材料中没有找到任何一项严格全双工工作给出端到端 **GPU/SM util 或 MFU 百分比**。
几个容易误读的量不是 GPU utilization：TML 的 `<5%` 是 batch-invariant kernel 相对端到端的额外开销；DuplexOmni 的 `gpu_memory_utilization=0.8/0.6/0.12` 是 vLLM 显存池预留比例；RTF、显存、tokens/s 和 frame latency 也不能换算成 utilization。
Wan-Streamer 只定性声称通过两卡 pipeline 重叠提高硬件利用率，没有给数值。

| 工作 | 公开 serving 拓扑 / 常用配置 | 并发证据 | 公开效率、显存或延迟 | 证据性质 |
| --- | --- | --- | --- | --- |
| GPT-Live | 已在 ChatGPT Voice 生产 serving；GPU、卡数、精度、调度器均未披露 | 只披露周用户量，**不是并发** | 未披露 | 官方生产状态；无容量规格 |
| Seeduplex | 豆包生产；speculative decoding + 量化；量化精度/GPU/卡数未披露 | 只称解决高并发延迟尖峰和稳定性，未给每卡会话数 | 相对上一代 endpoint latency 约 −250ms、打断约 −300ms；这是产品 A/B，不是 kernel/GPU 指标 | 官方生产状态与 A/B；无容量规格 |
| TML-Interaction-Small | Blackwell + NVLS；SGLang 持久化 streaming 序列；自定义 MoE gather+GEMV、通信和 batch-invariant kernels | 未披露 GPU 数或会话数 | 200ms micro-turn；batch-invariant kernels 端到端额外开销 `<5%`，**不是 utilization** | 官方研究预览 |
| Moshi | 简单 Python 服务端固定 `batch_size=1`、`streaming_forever(1)` 且用全局锁。Rust `moshi-server` 的可配置 batch 槽位 / execution mask 主要在 **ASR/TTS** 模块；全双工 LM 路径官方仍为每 websocket 会话独立状态、会话级 B=1，未见正式多会话 LM batch 容量报告 | Python 路径为 **1 活跃 session/进程 的代码上限**；Rust LM 路径同为会话级 B=1；Metronome 第三方单 Blackwell 90s 测 **≥32**（其栈，非官方 moshi-server 多会话 LM） | L4 上整体延迟最低约 200ms；PyTorch BF16 约需 24GB 级 GPU。论文完整 Moshi 模型体积：BF16A8 16.74GB、W8A8 9.20GB、W4A8 5.18GB；在线演示用 8-bit，W4 质量下降明显 | 官方代码/论文 + 第三方短测下界 |
| PersonaPlex | 官方 Python 服务端同样 `streaming_forever(1)` + 全局锁；BF16 checkpoint，可 CPU offload | **1 活跃 session/进程 的代码上限**；未做容量压测 | 未披露 serving GPU、显存、RTF；8×A100/6h 是训练配置 | 官方代码；不能解释成模型最大并发 1 |
| MoshiRAG | 单流评测时前台 Moshi + 流式 ASR 在 1×H100；本地 Gemma-3 27B 检索后端在另 1 GPU。云 API/Tavily 路径不同 | 未披露；论文是两 GPU 单流评测拓扑，不是容量压测 | 大多数本地检索在 1.5s 内；超过约 1.5s 后准确率明显下降；FLOPs/s 表不是 utilization | 官方论文单流配置 |
| MiniCPM-o 4.5 | 官方托管 Realtime WebSocket；本地 full-duplex 推荐 `llama.cpp-omni`；另支持 PyTorch/vLLM/SGLang | 官方未披露；Metronome 单 Blackwell：90s 新会话约 96 路；windowed KV 在 N=96 维持 10min，unbounded KV 不足 2min 完全停滞 | 见下表；官方 RTF/显存是单流效率。Metronome 为第三方容量 | 官方单流效率 + 第三方容量 |
| Raon-SpeechChat | 浏览器 WebSocket → CPU FastAPI/Uvicorn 网关 → Ray 路由器 → 每 GPU 一个 SGLang worker actor；`FD_GPU_IDS` 选卡 | `FD_MAX_SESSIONS_PER_GPU=2` 默认，**只是 config cap**；多卡按配置近似 `2×GPU 数`，无极限压测 | CUDA 12.x、16GB+ 显存 recommended、BF16/FP16、模型下载约 25GB。另有单 GPU 流式 TTS：RTX PRO 6000 Blackwell RTF 0.27 / TTFT 617ms；L40S RTF 0.45 / TTFT 887ms，**不是 SpeechChat 双工容量** | 官方可部署多会话服务端；cap 非最大值 |
| DuplexOmni | 默认 8 GPU：Thinker GPU0–3/TP4；Talker GPU4–7/TP4；MTP 子进程共享 GPU7。Thinker/Talker max model len 均 32386 | 编排器显式拒绝第二条活跃 session，故公开栈是 **1 session/8 GPUs 的代码上限** | 响应延迟约 0.506s；`0.8/0.6/0.12` 分别是三引擎显存池配置，非实测 utilization；GPU 型号、实测显存、吞吐未披露 | 官方代码概念验证 |
| Wan-Streamer v0.1 | GPU0 Thinker 负责编码/KV 更新/上一帧解码；GPU1 Performer 负责 flow-matching latent 生成，二者按帧交换 KV/latent；CUDA graph/compile/optimized kernels | 公开路径仅证明 **2 GPUs/1 session**，没有多会话压测 | 160ms 单元、约 200ms 模型侧、加 350ms 双向网络约 550ms、25FPS；GPU 型号/显存未披露 | 官方论文单流拓扑 |
| Metronome | 单 RTX PRO 6000 Blackwell；WebSocket 客户端 + Go 网关 + vLLM-realtime GPU worker；20ms 真实音频、各路起始相位按时间表错开；有界 KV + sinks + AIMD 准入 | Moshi ≥32@80ms；MiniCPM 约 96@1s；Qwen3-Omni ≥160@2s；Qwen2.5-Omni 16–24@2s；见第 6 节 | Qwen3 开放系统稳定约 209 live sessions、稳态 p99 每帧约 12ms；仍未报告 GPU utilization | 第三方、唯一系统性容量实测 |

MiniCPM-o 4.5 是严格主表里官方单流效率数据最完整的一项，但需要区分两组读法：

| 路径 / 硬件 | 精度 | 结果 | 适用边界 |
| --- | --- | --- | --- |
| `llama.cpp-omni` / RTX 4090 | FP16 / INT4 | RTF 0.27、19GB / **0.21、11GB** | full-duplex/流式单流 |
| `llama.cpp-omni` / DGX Spark | FP16 / INT4 | RTF 0.46、19GB / **0.20、11GB** | full-duplex/流式单流 |
| PyTorch / RTX 4090 | BF16 / INT4 | OOM / RTF 1.26、14GB | full-duplex/流式单流 |
| PyTorch / DGX Spark | BF16 / INT4 | RTF 2.43、26GB / RTF 1.27、14GB | full-duplex/流式单流 |
| vLLM / RTX 4090 | BF16 / INT4 | 154.3 / 212.3 tokens/s；TTFT 0.59 / 0.58s；19 / 11GB | 吞吐/显存是 **仅文本**；TTFT 用 64 帧视觉输入，不能当双工容量 |

其余工作没有可用容量数据：Human-1、RoboEgo、SyncLLM、OmniFlatten、SALMONN-omni、Voila 和 LSLM 只有论文/演示/离线推理；BayLing 只有音频文件 CLI；Covo-Audio-Chat-FD、DuplexSLA 以及 Fun-Audio-Chat 的 FD 产物/服务端尚未发布。论文中的训练 GPU 数不计入 serving 配置。

## 4. Kyutai 两条线：全双工主干与级联各覆盖问题的一半

**(a) 全双工主干在官方栈里 B=1，有源码级证据。**
Kyutai 生产服务端 [moshi-server][moshi-repo]（Rust）中，batch 推理只实现在语音识别与语音合成模块：`batched_asr.rs` 带 `batch_size` 与 `StreamMask` 槽位管理，TTS 的 Python 模块同构。
全双工语言模型模块的 `LmConfig` **没有 `batch_size` 字段**，每条 websocket 会话独立 clone 流式状态、会话级 B=1 串行（`moshi-server/src/main.rs` 的模块枚举、`stream_both.rs` 的每会话采样配置与种子）。
演示用的 `moshi-backend` 独立部署同样是单会话固定缓冲。故第 3 节 Moshi 行的「可 batch」只覆盖 STT/TTS。

**(b) Kyutai 官方自证「双工 + 工具」是缺口。**
[kyutai.org/unmute][unmute] 原话：
"While Moshi provides unmatched latency and naturalness, it **doesn't yet match the extended abilities of text models such as function-calling**... Unmute allows us to directly bring all of these from text to real-time voice conversations."
两条产品线各覆盖一半：Moshi 走定长环形 KV、无注入、每 tick 恒定 1 步；Unmute 走级联 STT→任意 LLM→TTS（MIT 开源），对话按回合制、无硬 tick，工具调用发生在文本 LLM 侧，由 vLLM 当普通聊天负载处理。

**(c) Unmute 的 tick 只存在于组件内部。**
STT/TTS 均为延迟流模型（delayed streams modeling，DSM）12.5Hz 锁步，即 80ms/步（[arXiv:2509.08753][dsm] §3.1–3.2）：每流每步工作恒定，因此可 batch。

| 组件 / 配置 | 结果 | 口径 |
| --- | --- | --- |
| ASR，H100，batch 256 | RTF 1.49，吞吐 380× | 论文实测（Table 6/10） |
| TTS，H100，batch 64 | RTF 2.1，首音频 403ms | 论文实测（Table 6/10） |
| TTS 文本流设计延迟 | 16 步 = 1.28s | 设计值 |
| TTS，B=1 | 首音频 150ms | 论文实测 |

级联端到端为亚秒级。可 batch 的前提是每流每步工作量恒定；每片输出 token 数不定的全双工主干路径，以及外部结果注入路径，在 Kyutai 官方栈里都没有 batch 实现。

**(d) 全双工并发的社区数字只能作轶事引用。**
Moshi 7B 多路并发没有任何官方数字（论文全文、README、FAQ 均无）。
两个第三方博客给 4–10 路/H100（localaimaster、spheron），均无方法学，其中一篇把 4090 与 H100 并列同一数字。引用时按轶事级标注。

## 5. 每个工作解决什么问题，问题是否来自真实场景，数据来自哪里

| 工作 | 要解决的问题 / 真实性判断 | 训练与评测数据证据 |
| --- | --- | --- |
| GPT-Live | 旧 Advanced Voice Mode 虽端到端，交互仍按离散轮次；解决停顿误判、自然 overlap/backchannel、边聊边等待后台任务。**生产问题，证据最强** | 官方仅称公开、授权、人工提供/生成等多源数据；未披露语料规模/清单。系统卡含生产分布评测 |
| Seeduplex | 高并发延迟尖峰、稳定性、背景人声/噪声误触发、犹豫被误判为 EOT。**真实生产问题**，有豆包 A/B：相对上一代 endpoint 约 −250ms、打断约 −300ms、过早响应 −40% 等 | 只披露 speech-data 预训练 + 多能力/多任务后训练；来源、小时数未披露 |
| TML Interaction | 强智能与低延迟交互难以由一个模型同时满足；以前台交互模型 + 异步后台模型分工。**真实需求，尚非生产验证** | 从零主预训练数据未披露；只公开部分 TTS 合成安全数据与自动多轮 red-team 数据；评测含 FD-Bench/Audio MultiChallenge/demos |
| Moshi | 把语音输入、语音/silence 输出和 inner monologue 放进同一时钟，去掉 turn-taking gate。真实自然会话问题；有真实电话数据，但产品流量未公开 | Helium 2.1T 公开英文文本 tokens；约 700 万小时 unlabeled audio；Fisher 约 2000h 双声道电话；>20K h 合成指令语音 + 交互脚本 |
| PersonaPlex | Moshi 固定角色/声音，不适合可控服务角色。真实产品需求；主要角色数据合成，时序部分有真实 Fisher | 105,410 客服对话/1840h + 39,322 QA/410h 合成；26,296 声音样本；released checkpoint 另训 Fisher 7303 conversations/1217h |
| Human-1 | 英语 Moshi 的 tokenizer/交互习惯不适合 Hindi。**数据真实性很强，但没有 live serving 证据** | 26,000h 真实、自发、双声道 Hindi 对话，14,695 speakers，由受雇参与者采集；约 990h 高质量子集 fine-tune；130 位母语者做 2,125 次人评 |
| MoshiRAG | 小型全双工前台事实性弱，检索/强 LLM 延迟又不能阻塞交互。需求真实；实验证据主要是合成 speech-QA | 474K QA topics（NQ 约 307K、HotpotQA 约 90K、TriviaQA 约 76K）+5.5K expert topics；约 1.9M conversation instances、约 47,770 synthetic hours；Gemma 3 27B 写脚本/reference，多通道 TTS |
| MiniCPM-o 4.5 | 在单个约 9B 模型里做视觉/语音实时 omni 交互，并把主 LLM 速率压到 3–4 text steps/s。需求真实；全双工定量证据仍偏弱 | “millions of hours” unlabeled speech，来源仅称 diverse/open pipeline；FD 数据来自 large-scale web audio-video + manually constructed scenarios，精确规模未披露；主要 FD benchmark 是 audio-free LiveSports-3K-CC，真实长时鲁棒性未证实 |
| Raon-SpeechChat | 英/韩端到端双工，同时提供真正可部署的多 GPU session 服务端。真实需求；有较大真实对话占比，但无生产工作负载 | Raon raw 1.38M h；SpeechChat 约 119K h：13.21K h 真实对话 +106.33K h 合成；public + in-house English/Korean，audio-only 经 Whisper 伪标、text-only 经 Qwen3-TTS |
| Fun-Audio-Chat-Duplex | 25Hz speech 与约 3Hz text 的速率错配、算力开销和 text intelligence 遗忘；FD 版再处理 overlap/turn-taking。问题真实；FD 训练/评测主要合成 | 总体称 millions of hours，来自 DrVoice/Audio-Flamingo-3 recipe + in-house；FD dialogue 由半双工对话增广合成，未披露 FD 小时数；真实线上对话未验证 |
| Covo-Audio-Chat-FD | 兼顾 7B 语义智能、语音自然度、低延迟 FD，并降低 intelligence-speaker coupling 的换声成本。问题真实；FD 证据仍主要是构造数据/benchmark | 200K h ASR alignment；总预训练约 8M h audio/speech +3T text，2T training tokens；FD 预训练占 5B tokens；双声道 dialogue 由半双工数据转换并插入 barge-in/backchannel，精确真实/合成比例未披露 |
| DuplexSLA | 现有 FD 主干没有与语音同拍的规划/tool call 通道；轮次末尾的 tool call 会迟一整轮。**与 agent omni 最直接相关，但未上线** | CPT 约 500K h（320K duplex dialogue +2×90K h 双侧 ASR）+1.92M text；后训练约 50K h（36K interaction control +14K tool call）；图示流水线为 LLM 标注、TTS/voice cloning、force alignment，原始语料来源与真实比例未披露；自建 2100-case benchmark |
| DuplexOmni | 前台低延迟交互与后台推理/工具不能串行，S1 继续说/听，S2 异步返回再注入。问题真实；当前 runtime 仍为 8 卡单会话概念验证 | ~620K scenario seeds、~3.02M raw conversations、10K video calls，70% 中文/30% 英文；源文本含 UltraChat/WildChat/BELLE/COIG/no-robots/OASST2；Qwen3.5-397B-A27B Writer/Director + Qwen3-TTS/Mimi，主体为合成 |
| BayLing-Duplex | 不做百万小时重新预训练，低成本把强轮次制 SpeechLM 改成 FD。工程动机真实；**真实部署证据最弱之一** | 400K 合成样本：200K turn-taking +200K interruption；原始对话来自 Alpaca/UltraChat，经 Llama-3.3-70B rewrite、CosyVoice 合成；论文明确训练/评测均为合成、单说话人、近场、无噪声 |
| Wan-Streamer | 单个因果 Transformer 做 text/audio/video 双向流式数字人，去掉独立 VAD/ASR/LLM/TTS/avatar/video generation。应用真实；v0.1 只到 192p，生产证据不足 | 只给数据类别（理解、文本对话、ASR/TTS/audio dialogue、各类生成与端到端双工 AV 交互）；来源、小时数、样本数均未披露 |
| RoboEgo | 全模态具身 agent 要同时看、听、说、想、行动，避免 TDM 带来的约 2s 延迟。真实具身场景；只有 system-card 级演示/人评 | 只说 large-scale audio 与多轮 visually grounded speech dialogue，并做 interruption/noise augmentation；规模、来源、真实/合成比例均未披露；有 5 名标注员真实场景人评和机器人 demo |
| SyncLLM | 普通 LLM 没有墙钟，且互联网传输造成当前用户 chunk 尚未到达；用预测当前 chunk、下一 tick 再替换实现同步。真实网络问题；只做双 agent 模拟，未做 live-human serving | 212K h 合成 spoken dialogue；约 2K h Fisher real dialogue；CANDOR 作分布外；主要评测为模拟 agent-agent 交互 |
| OmniFlatten | 不改 GPT 架构，把多路 speech/text flatten 后学习 silence、overlap、turn-taking。需求真实；数据和评测以合成为主 | 模态对齐约 100K h（30% open、70% proprietary；open 含 AIShell-3/LibriTTS/TED-LIUM/VoxPopuli/LibriSpeech/MLS/WenetSpeech）；约 390K 文本对话经 TTS，最终 2000h 模拟多通道 dialogue + MUSAN noise |
| SALMONN-omni | codec 注入容易损伤 LLM 智能；用连续 embedding + 单个 LLM 状态 tokens 做独立 FD，并区分真正 barge-in、backchannel、自身回声。问题真实；交互数据多为合成 | ASR：LibriSpeech 281K + GigaSpeech 200K samples；QA 约 728K；multi-round 约 81K；回答/对话大量由 Llama-3-8B + CosyVoice2 合成；barge-in/backchannel 由提示模板生成；评测也有小规模人工/构造集 |
| Voila-autonomous | 端到端语音仍常是被动轮次制；加入持续监听、角色和声音定制。需求真实；FD 数据透明度低 | tokenizer 训 100K h audio，来源未披露；公开 benchmark 由 MMLU/MATH/HumanEval/NQ/GSM8K 共 1580 条经 GPT-4o 改写 + Google TTS；FD 训练语料规模/来源未披露 |
| LSLM | 证明单个生成模型能「边合成边听」，并在噪声中学习 IRQ；但只是在已知 TTS 内容生成过程中检测打断，能力显著窄于现代交互模型 | 585h LibriTTS；Speech Commands 作打断词；MUSAN 作噪声；训练时随机混入打断/噪声，非真实自由对话 |

## 6. Metronome：不要把它误当模型

[Metronome][metronome]（**2026-07-02**，论文 v1）是 serving 系统：周期性将所有到期 session 的小 prefill + 短 decode 组成一批，用有界 KV + attention sinks 避免长期 memory cliff，再用 AIMD 准入求可调度并发数 N\*。
所有实验均为**单张 NVIDIA RTX PRO 6000 Blackwell**、真实音频以 20ms 网络 chunk 输入、各路 session 起始相位按时间表错开；容量不是 prefix-cache 复用出来的。

口径注（本文一次性说明）：下表的 90 s 新会话数字属短爆发口径，上游仓库自认早期短爆发的墙钟数字受扫点污染，引用具体墙钟秒数前按 `docs/metronome.md` 的订正纪律核对。
可稳定引用的是「无界 KV 出现 memory cliff 且 GPU 时间占用偏低」与「KV 有界后 deadline 先于显存到达」这一层结论。

| 被 serve 的模型 | 实验 frame budget | 90 s 新会话单 GPU 容量 | 长会话证据 |
| --- | ---: | ---: | --- |
| Qwen3-Omni-30B-A3B FP8 | 2 s | **≥160**，只测到 160，故是下界 | W=1024 约 40s + sinks；开放系统 AIMD 稳定约 **209 live sessions**。约 500 只是 KV 内存线性外推，不是实测可服务数 |
| MiniCPM-o 4.5 | 1 s | **约 96** | N=96 windowed KV 完整维持 10min、中位数个位数 ms；unbounded KV 不足 2min 完全停滞 |
| Moshi | 80 ms | **≥32**，只测到 32 | 只报告 90s 新会话下界，没有同等规模长会话最大值 |
| Qwen2.5-Omni-7B | 2 s | **16–24** | 只报告 90s 新会话容量 |

这里最重要的系统事实不是某个孤立数字：无界常驻 KV 在短测里延迟可以一直健康，随后所有 session 一起停滞。
论文对这一失效的定性是「The failure is a memory cliff, not a compute drift」，并称崩溃是静默的。
故读任何一份容量报告，都要同时看**硬件、tick 长、session 年龄、KV 策略、是否真实音频、各路相位是否按时间表错开、给出的是测到的上限还是下界**。

## 7. 已上线，但不能据公开材料断言「模型级全双工」的边界产品

| 产品 | 已知上线/上下文 | 为什么不放进严格主表 |
| --- | --- | --- |
| [GPT-Realtime-2.1][gpt-realtime] | Realtime API 正式可用；128K context、32K max output、session 最长 60min；原生音频、barge-in；`turn_detection` 配合 truncate 对账，可快进生成囤缓冲 | 官方未说明 overlap/silence 是否像 GPT-Live 一样进入持续模型时间上下文；GPT-Live 发布材料反而把旧 Advanced Voice Mode 描述为轮次制 |
| [Gemini 3.1 Flash Live][gemini-live] | Live API；input 131,072、output 65,536；audio-only 无压缩 15min，audio+video 2min；sliding window 压缩 + 续传可延长 | 有 barge-in，但模型内部是否持续建模 overlap/silence 未公开；当前还不支持 proactive audio、affective dialogue、async tool call |
| [Amazon Nova 2 Sonic][nova-sonic] | Bedrock 生产服务；双向 speech-to-speech、interrupt、async tool；上下文最高 1M tokens；单连接 8min 可续，生产靠提前轮换 | 官方仍强调 “intelligent turn-taking detects when user finishes speaking”；传输层双向不等于已公开证实 interaction-model 语义 |
| [Qwen3.5-Omni-Plus-Realtime][qwen-realtime] | Model Studio API；WebSocket session 最长 120min；history 100 audio turns / 累计约 600s audio（公开表述 480–600s），最旧优先丢弃（drop-oldest）；语义打断；思考模式与音频输出互斥 | 支持 VAD/manual commit，但模型内部时序与原生 tick 未公开，不能从产品接口反推严格 full-duplex 架构 |

其他常被称为 full-duplex 的 FireRedChat、FlexDuo、DuplexCascade、Unmute 等，若核心仍是外部 VAD/ASR/LLM/TTS/controller 或两套不能同时听说的 LLM 进程，属于系统级双向/级联方案，不纳入本表。
Qwen2.5/3.x-Omni、GLM-4-Voice、Step-Audio 等普通流式语音模型也不能仅凭 streaming output 推断为模型级全双工。

几项容易混入但本次明确剔除的工作：dGSLM 是双路对话**生成**先驱，但不是持续接入外部真人流的在线 agent；Mini-Omni2 的公开 duplex 行为主要是 `Stop Omni` 关键词打断，不足以证明语义 backchannel/overlap 建模。
DuplexMamba 在接收语音时并行生成的是文本而非 assistant speech；VITA/Freeze-Omni/MinMo/Nemotron VoiceChat 公开方案依赖双模型、独立感知/TTS 或外部控制，属于非独立或混合系统。
它们仍可作组件/系统 baseline，但不应与 GPT-Live、Seeduplex、Moshi 这类模型级全双工混在同一张规格表里。

## 8. 后台工作与结果注入的公开证据

- **产品层**：GPT-Live 把 "invoke a tool" 放进每秒多次的 tick 内决策，复杂问题委托 GPT-5.5 后台执行、结果送回同一段对话（第 1 节）。
- **模型层，MoshiRAG**：`⟨ret⟩` 触发检索，检索期间前台继续生成 pre-RAG 填充内容；检索文本 4× 压缩后按帧**加法叠进输入嵌入**，附录 B.1.1 说明插入式注入精度更好但被弃用，理由原文为 "to constrain sequence length"。
  时序数字：检索预算 ≤2s，关键信息出现前留 ≥1.0s 缓冲，实测端到端关键词延迟 3.1s（vanilla 基线 2.1s）。这组数字给出了延迟类策略的语义可行上界。
- **模型层，DuplexOmni**：thinking 层的异步注入是官方设计，注入通道已在模型侧标准化（第 2.5 节）。
- **同模式的串联系统**：KAME（Sakana，[arXiv:2510.02327][kame]）把实时语音到语音前台与后台 frontier 模型串联。
- **检索记录（2026-08-01）**：除 Metronome 外未核验到全双工 GPU serving 论文；[Awesome-Full-Duplex-SDM][awesome-fd] 的全列表里没有 serving 方向条目。
  NVIDIA [Nemotron 3 VoiceChat][nemotron-voicechat]（2026-03，12B 开源权重 + NeMo 官方推理管线 / NIM）的模型卡同样没有并发或批量规格；本文只记这一条 serving 规格缺位，不据此给它定级。

## Sources

- 官方产品/系统说明：[GPT-Live 发布][gpt-live]、[system card][gpt-live-card]、[Seeduplex 页面][seeduplex]、[技术博客][seeduplex-blog]、[TML Interaction Models][tml]。
- 官方 API 文档：[GPT Realtime][gpt-realtime]、[Realtime guide][gpt-realtime-guide]、[Gemini Live][gemini-live]、[Live session guide][gemini-live-guide]、[Nova 2 Sonic][nova-sonic]、[Qwen Realtime][qwen-realtime]。
- 重点开源/serving 入口：[Moshi][moshi-repo]、[Unmute][unmute]、[PersonaPlex][personaplex-repo]、[MiniCPM-o][minicpmo-repo] / [Realtime API][minicpmo-realtime-api]、[Raon model][raon-repo] / [multi-session server][raon-server]。
- 其余开源入口：[Fun-Audio-Chat][funaudiochat-repo]、[Covo-Audio][covo-repo]、[DuplexSLA][duplexsla-repo]、[DuplexOmni][duplexomni-repo]、[BayLing-Duplex][bayling-repo]、[SALMONN][salmonn-repo]、[Voila][voila-repo]、[Nemotron 3 VoiceChat][nemotron-voicechat]。
- 各论文入口已链接在主表工作名上。
- 检索面：[Awesome-Full-Duplex-SDM][awesome-fd]（全双工 speech dialogue model 列表）。

[gpt-live]: https://openai.com/index/introducing-gpt-live/
[gpt-live-card]: https://deploymentsafety.openai.com/gpt-live
[seeduplex]: https://seed.bytedance.com/en/seeduplex
[seeduplex-blog]: https://seed.bytedance.com/en/blog/introducing-seed-full-duplex-speech-llm-attentive-listening-robust-interference-suppression-enabling-more-natural-interaction
[tml]: https://thinkingmachines.ai/blog/interaction-models/
[moshi]: https://arxiv.org/abs/2410.00037
[moshi-repo]: https://github.com/kyutai-labs/moshi
[unmute]: https://kyutai.org/unmute
[dsm]: https://arxiv.org/html/2509.08753
[personaplex]: https://arxiv.org/abs/2602.06053
[personaplex-repo]: https://github.com/NVIDIA/personaplex
[human1]: https://arxiv.org/abs/2604.23295
[moshirag]: https://arxiv.org/abs/2604.12928
[minicpmo]: https://arxiv.org/abs/2604.27393
[minicpmo-repo]: https://github.com/OpenBMB/MiniCPM-o
[minicpmo-realtime-api]: https://minicpmo45.modelbest.cn/docs/en/realtime-api/overview/
[raon]: https://arxiv.org/abs/2605.23912
[raon-repo]: https://github.com/krafton-ai/Raon-Speech
[raon-server]: https://github.com/krafton-ai/Raon-SpeechChat-Demo
[funaudiochat]: https://arxiv.org/abs/2512.20156
[funaudiochat-repo]: https://github.com/FunAudioLLM/Fun-Audio-Chat
[covo]: https://arxiv.org/abs/2602.09823
[covo-repo]: https://github.com/Tencent/Covo-Audio
[duplexsla]: https://arxiv.org/abs/2605.20755
[duplexsla-repo]: https://github.com/hyzhang24/DuplexSLA
[duplexomni]: https://arxiv.org/abs/2606.09186
[duplexomni-repo]: https://github.com/MuyeHuang/DuplexOmni
[bayling]: https://arxiv.org/abs/2606.14528
[bayling-repo]: https://github.com/BayLing-Models/BayLing-Duplex
[wan]: https://arxiv.org/abs/2606.25041
[roboego]: https://arxiv.org/abs/2506.01934
[syncllm]: https://arxiv.org/abs/2409.15594
[omniflatten]: https://arxiv.org/abs/2410.17799
[salmonn]: https://arxiv.org/abs/2505.17060
[salmonn-repo]: https://github.com/bytedance/SALMONN
[voila]: https://arxiv.org/abs/2505.02707
[voila-repo]: https://github.com/maitrix-org/Voila
[lslm]: https://arxiv.org/abs/2408.02622
[kame]: https://arxiv.org/abs/2510.02327
[metronome]: https://arxiv.org/abs/2607.02640
[awesome-fd]: https://github.com/Ruiqi-Yan/Awesome-Full-Duplex-SDM
[nemotron-voicechat]: https://build.nvidia.com/nvidia/nemotron-voicechat/modelcard
[gpt-realtime]: https://developers.openai.com/api/docs/models/gpt-realtime-2.1
[gpt-realtime-guide]: https://developers.openai.com/api/docs/guides/realtime-conversations
[gemini-live]: https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-live-preview
[gemini-live-guide]: https://ai.google.dev/gemini-api/docs/live-session
[nova-sonic]: https://docs.aws.amazon.com/nova/latest/nova2-userguide/
[qwen-realtime]: https://www.alibabacloud.com/help/en/model-studio/realtime
