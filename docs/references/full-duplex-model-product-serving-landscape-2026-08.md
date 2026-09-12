# 全双工模型、产品与 serving 版图（2026-08）

Updated: 2026-08-03
2026-08-07 快照：并入产品与文献查证的证据层；术语统一为全双工。
2026-09-13 快照：增补级联与模型级全双工的 2026 比较口径（第 6 节）；复核主表 tick 数据无需修正。

## 划界

本文是有日期的外部公开规格整理，不是项目事实源，也不定义本项目的 workload、机制、术语或 contribution。任何内容进入 paper 前都必须重新核验原始来源，并按 [`docs/problem.md`](../problem.md#terminology) 与四份 human owner 重新表述；不得从本文件把外部系统的后台任务、音频播放链或指标定义套用到当前原型。

只把下面这种系统算作**模型级全双工（model-level full-duplex）**：模型在输出期间继续吸收输入，并把 silence、overlap、backchannel、打断或主动开口当作模型时间上下文或学到的动作。以下两类不自动算：

- WebSocket 能同时收发，或用户说话时取消 TTS；
- `VAD 判停 → ASR → 文本 LLM → TTS`，即使各模块都做成 streaming。

**约定**

- **tick**：模型或调度器完成一次交互决策的原生最小时间单位，不是网络包长、首包延迟或评测 deadline。
- 容量数字分为「实测」「config cap」「下界」「外推」；没有数据一律写「未披露」。**N\*** 只沿用本文所整理来源对 schedulable concurrency 的定义，不为本项目冻结验收阈值。
- 90 s 新会话数字只反映短时突发下的容量，不能替代长时稳态容量。
- config cap（如 Raon `FD_MAX_SESSIONS_PER_GPU=2`）**≠ 实测最大值**。
- 训练 GPU 配置**不计入** serving 配置。
- GPU memory utilization 配置（如 vLLM `gpu_memory_utilization=0.8`）、RTF、显存占用、tokens/s 和 frame latency 均**不是 GPU/SM utilization 或 MFU**。公开材料中没有找到任何严格全双工工作给出端到端 GPU/SM util 或 MFU。

**公开证据摘要**（截至 2026-08-07）：

1. 能同时证明「模型级全双工 + 大规模生产上线」的只有 **GPT-Live** 和 **Seeduplex**；两家都不公开参数、tick、上下文和单 GPU 容量。MiniCPM-o 4.5 已有官方托管 Realtime API，但没有公开流量或 SLA。
2. 开源侧给出多会话服务端较完整的是 **Raon-SpeechChat**，但其 `2 sessions/GPU` 只是 config cap。多数论文只有单会话演示或离线推理。
3. 系统性公开「单 GPU 能撑多少路、短测与长会话为何不同」的只有 **Metronome**（serving 系统，不是模型）。无界常驻 KV 在短测里延迟正常，随后所有 session 一起停滞；失效是 memory cliff 而非 compute drift，且崩溃是静默的。

## 1. 已上线或前沿闭源模型

| 工作 | 首次公开 | 上线状态 | 原生 tick | 参数 | 单会话上下文 | 单 GPU 容量 | 量化 / 硬件 / 效率 |
| --- | --- | --- | ---: | ---: | --- | --- | --- |
| [GPT-Live][gpt-live] | **2026-07-08** | **生产**。ChatGPT Voice Go/Plus/Pro 默认（Live-1），Free 默认（mini）；API 未开放；周用户超 1.5 亿（非并发） | 未披露；官方 "continuously processes input while generating output"，每秒多次决定 `speak/listen/pause/interrupt/tool`；复杂问题委托 GPT-5.5 后台 | 未披露 | 未披露；社区实测 ≥1 h（Simon Willison 个例报告，非系统测量）。[系统卡][gpt-live-card]无架构数字 | 未披露 | 未披露 |
| [Seeduplex][seeduplex] | **2026-04-09** | **生产**。fully rolled out 到豆包 App，称服务数亿用户 | 未披露；"listen while speaking"，逐步决策 start replying / continue listening / respond to interruptions | 未披露 | 未披露 | 未披露 | speculative decoding + 量化；精度/GPU 未披露。公开数字均为相对上一代 A/B：endpoint latency −250ms、打断 −300ms、误响应与误打断减半、抢话 −40%、MOS +12%。自述克服高并发延迟尖峰与稳定性问题，解法未公开 |
| [TML-Interaction-Small][tml] | **2026-05-11** | 研究预览，未来 limited preview | **200 ms** micro-turn | **276B MoE / 12B active** | 未披露；官方明确超长 session 仍是问题 | 未披露 | Blackwell + NVLS；自定义 MoE gather+GEMV + batch-invariant kernels（额外开销 <5%，非 utilization）；持久化 SGLang streaming session；GPU 数/量化未披露 |

GPT-Live 与 `GPT-Realtime-2.1` 不是同一公开产品定义；后者见第 4 节边界表。

## 2. 公开模型与研究原型

### 2.1 模型规格与可用性

| 工作 | 首次公开 | 原生 tick | 参数 | serving / 开源状态 | 单会话上下文 |
| --- | --- | ---: | ---: | --- | --- |
| [Moshi][moshi] | **2024-07-03** 介绍；09-17 论文；09-18 开源 | **80 ms**（Mimi 12.5 Hz） | Helium **7B** | `moshi.chat` 研究演示 + 自部署服务端；无托管 API/SLA | 3000 步 ≈ **4 min** |
| [PersonaPlex][personaplex] | **2026-01-14** | **80 ms** | Moshi **7B** 微调 | NVIDIA 研究演示 + 自部署；无商业 API | 3000 步 ≈ **4 min** |
| [Human-1][human1] | **2026-04-25** | **80 ms** | Moshi/Helium **7B** | 论文；未核验到权重/代码/live 服务 | **2048 步 ≈ 2.7 min** |
| [MoshiRAG][moshirag] | **2026-04-14** 论文；04-30 博客 | **80 ms** | 7B + 1B 流式 ASR；默认后台 Gemma-3 27B | 推理代码/演示视频；非 live API | 继承 Moshi ≈ **4 min** |
| [MiniCPM-o 4.5][minicpmo] | **2026-02-03** 开源；04-30 论文 | **1.0 s**（0.2/0.1 s 仅消融） | **9.34B** | 官方托管 [Realtime API][minicpmo-realtime-api] + 本地演示；无流量/SLA | LLM **40,960**；speech decoder **4096** |
| [Raon-SpeechChat][raon] | **2026-04-08** | **80 ms**（12.5 Hz） | ≈**9.8B**（8.8B shared + ≈1.0B encoder/adaptor） | 在线演示；公开 WebSocket + Ray + SGLang 多会话服务端；无生产 SLA | 训练 **4096 ≈ 2 min**；runtime 默认 KV `8192` ≈ 4 min |
| [Fun-Audio-Chat-Duplex][funaudiochat] | **2025-12-23** | 主干 **200 ms**（5 Hz）；speech head 25 Hz | dense **8B** / MoE **30B/3B active** | **FD 版无公开权重/服务端**；已发布为非 FD 8B | **2048 tokens ≈ 6 min** |
| [Covo-Audio-Chat-FD][covo] | **2026-02-10** | **160 ms**；1 个 6.25Hz 输入对 4 个 25Hz 输出 | **7B** | **FD checkpoint 未发布**；只开源半双工版 | 训练 **8192**；墙钟未披露 |
| [DuplexSLA][duplexsla] | **2026-05-20** | **160 ms**；2×80ms 输入 + 4×40ms 输出；每 tick action ≤10 token | **7B** | 技术报告 + 演示；checkpoint/服务端 coming soon | 未披露 |
| [DuplexOmni][duplexomni] | **2026-06-08** | **480 ms**（每 tick 6 Mimi frames）；thinker 产出 m_t assistant tokens/tick（论文只给符号未给数值）；输入率继承 Qwen3-Omni `position_id_per_seconds: 13` | Qwen3-Omni **30B/3B active** 交互基座 + Talker/Code2Wav + 外部 S2 | 公开训练/serving 代码，checkpoint 为 placeholder；单 session | thinker/talker **32,386** |
| [BayLing-Duplex][bayling] | **2026-06-12** | **800 ms 决策块**（底层 80ms，每 10 token 决策一次） | **9B LLM** | 权重 + 离线音频 CLI；无 live 多用户服务端 | config **32,768**；推导 ≈ 17.5 min |
| [Wan-Streamer v0.1][wan] | **2026-06-23** | **160 ms**；信号级 ≈ 200ms | 未披露 | 概念验证；无权重/代码 | full-history KV，未给窗口数字 |
| [RoboEgo / FLM-Ego][roboego] | **2025-06-02** | **80 ms** 理论值 | **7B** 主干 | system card + 演示；无权重/代码 | 未披露 |
| [SyncLLM][syncllm] | **2024-09-23** | **160/200/240 ms**（主 160） | Llama-3 **8B** | 论文 + 音频样例；无 checkpoint/服务端 | **8192 tokens**；speech-token 去重后墙钟不固定 |
| [OmniFlatten][omniflatten] | **2024-10-23** | ≈ **400 ms**（10 token/chunk @25Hz，外部推导） | Qwen2 **0.5B** | 论文；无 live 服务端 | **8192 tokens** |
| [SALMONN-omni][salmonn] | **2025-05-17** | **80 ms**；合成器 4 token → 480ms + 320ms 设计延迟 | Llama-3 **8B** + CosyVoice2 **0.5B** + Mamba | demo；无公开 FD checkpoint/live 服务 | 未披露 |
| [Voila-autonomous][voila] | **2025-04-28** 权重；05-05 论文 | 未披露（195ms 是响应延迟） | 32 层 4096 hidden Llama-style | 权重 + 离线推理/Gradio；autonomous 输入为预录音频 | `max_position_embeddings=8192` |
| [LSLM][lslm] | **2024-08-05** | 未披露；IRQ 目标 **0.5 s** | 106M decoder + 34M encoder | 早期原型；边合成边听 + IRQ，不是完整开放域 agent | 未披露 |

能换算墙钟长度的开源工作都落在 20 分钟量级以内。其他推导值：hertz-dev 2048 token ≈ 4.3 min；SyncLLM 8192 ≈ 4.5 min（论文自认 limitation）；GLM-4-Voice 8192 ≈ 10 min；Qwen2.5-Omni 32k ≈ 20 min。

### 2.2 Serving 容量与拓扑

下表仅列有公开 serving 数据的系统。其余（Human-1、Fun-Audio-Chat-Duplex、Covo-Audio-Chat-FD、DuplexSLA、BayLing-Duplex、RoboEgo、SyncLLM、OmniFlatten、SALMONN-omni、Voila、LSLM）均无已公开的容量、拓扑或效率数据。

| 工作 | 公开 serving 拓扑 | 单 GPU 容量 | 量化 / 硬件 | 证据性质 |
| --- | --- | --- | --- | --- |
| Moshi | Python 服务端 `batch_size=1` + `streaming_forever(1)` + 全局锁；Rust `moshi-server` 可配置 batch 只覆盖 ASR/TTS，FD LM `LmConfig` 无 `batch_size` 字段，每会话独立 B=1 | 官方未披露；Metronome 第三方 **≥32**@80ms（90 s 下界） | BF16A8 16.74GB / W8A8 9.20GB / W4A8 5.18GB；在线演示用 8-bit，W4 质量下降明显 | 官方代码 B=1 + 第三方短测下界。社区博客 4–10 路/H100 无方法学，仅为个例报告 |
| PersonaPlex | 同 Moshi `streaming_forever(1)` + 全局锁；**1 活跃 session/进程的代码上限**，不能解释成模型最大并发 1 | 未做容量压测 | BF16；可 CPU offload | 官方代码 |
| MoshiRAG | 前台 Moshi + 流式 ASR 在 1×H100；本地 Gemma-3 27B 后端另占 1 GPU | 未披露（2 GPU 单流评测拓扑） | 量化未披露。本地检索多在 1.5s 内，超过后准确率明显下降 | 官方论文单流配置 |
| MiniCPM-o 4.5 | 官方托管 Realtime WebSocket；本地推荐 `llama.cpp-omni`；另支持 PyTorch/vLLM/SGLang | Metronome 单 Blackwell 90 s 新会话 **≈96**；windowed KV 在 N=96 完整维持 10 min（中位数 ms 级），unbounded KV 不足 2 min 完全停滞 | 见效率子表 | 官方单流效率 + 第三方容量 |
| Raon-SpeechChat | WebSocket → FastAPI/Uvicorn 网关 → Ray 路由器 → 每 GPU 一个 SGLang worker actor；`FD_GPU_IDS` 选卡 | `FD_MAX_SESSIONS_PER_GPU=2`（config cap）；多卡 ≈ 2×GPU 数，无极限压测 | BF16/FP16；≈25GB；16GB+ recommended | 官方可部署多会话服务端 |
| DuplexOmni | Thinker GPU0–3 TP4 + Talker GPU4–7 TP4 + MTP 共享 GPU7；max model len 32,386；编排器拒绝第二条活跃 session。BF16 权重实测 **70.5GB**（HF 15 分片），80GB 卡接近吃满，FP8 是全双工部署起点。Thinking 层异步注入是官方设计 | **1 session / 8 GPUs** 代码上限 | dtype `auto`；无公开量化。响应延迟 ≈0.506s；`0.8/0.6/0.12` 是显存池配置，非 utilization | 官方代码概念验证 |
| Wan-Streamer v0.1 | GPU0 Thinker（编码/KV/解码）+ GPU1 Performer（flow-matching latent），按帧交换 KV/latent；CUDA graph/compile | **2 GPUs / 1 session**，无多会话压测 | GPU 型号/显存未披露；输出 192p。160ms 单元 + 350ms 双向网络 ≈ 550ms、25FPS | 官方论文单流拓扑 |
| Metronome | 单 RTX PRO 6000 Blackwell；WebSocket + Go 网关 + vLLM-realtime worker；20ms 真实音频，各路相位按时间表错开；有界 KV + sinks + AIMD 准入 | 见容量子表 | — | 第三方、唯一系统性容量实测 |

**Metronome 容量结果**（[Metronome][metronome]，**2026-07-02** 论文）

| 所服务的模型 | frame budget | 90 s 新会话 | 长会话证据 |
| --- | ---: | ---: | --- |
| Qwen3-Omni-30B-A3B FP8 | 2 s | **≥160**（下界） | W=1024 ≈40s + sinks；开放系统 AIMD 稳定 ≈**209 live sessions**，稳态 p99 每帧 ≈12ms。≈500 是 KV 线性外推，非实测 |
| MiniCPM-o 4.5 | 1 s | **≈96** | windowed KV 完整维持 10 min；unbounded KV 不足 2 min 停滞 |
| Moshi | 80 ms | **≥32**（下界） | 只报告 90 s，无同规模长会话 |
| Qwen2.5-Omni-7B | 2 s | **16–24** | 只报告 90 s |

**MiniCPM-o 4.5 官方单流效率**

| 路径 / 硬件 | 精度 | 结果 | 适用边界 |
| --- | --- | --- | --- |
| `llama.cpp-omni` / RTX 4090 | FP16 / INT4 | RTF 0.27、19GB / **0.21、11GB** | full-duplex 流式单流 |
| `llama.cpp-omni` / DGX Spark | FP16 / INT4 | RTF 0.46、19GB / **0.20、11GB** | full-duplex 流式单流 |
| PyTorch / RTX 4090 | BF16 / INT4 | OOM / RTF 1.26、14GB | full-duplex 流式单流 |
| PyTorch / DGX Spark | BF16 / INT4 | RTF 2.43、26GB / RTF 1.27、14GB | full-duplex 流式单流 |
| vLLM / RTX 4090 | BF16 / INT4 | 154.3 / 212.3 tokens/s；TTFT 0.59/0.58s；19/11GB | **仅文本**；不能当双工容量 |

**Kyutai 两条线**。[kyutai.org/unmute][unmute] 官方材料承认全双工与工具调用还不能兼得：Moshi 覆盖低延迟全双工但无 function-calling；Unmute 走级联 STT→任意 LLM→TTS（MIT 开源），工具调用在文本 LLM 侧。Unmute 的 STT/TTS 均为 DSM 12.5Hz 锁步（[arXiv:2509.08753][dsm]），每流每步的计算量恒定，因此可以 batch：ASR H100 batch 256 RTF 1.49 / 吞吐 380×；TTS H100 batch 64 RTF 2.1 / 首音频 403ms（B=1 时 150ms）；TTS 文本流设计延迟 16 步 = 1.28s。每片输出 token 数不定的全双工主干路径在 Kyutai 官方栈里没有 batch 实现。

## 3. 每个工作解决什么问题

| 工作 | 要解决的问题 / 真实性判断 | 训练与评测数据证据 |
| --- | --- | --- |
| GPT-Live | 旧 Advanced Voice Mode 虽端到端，交互仍按离散轮次；解决停顿误判、自然 overlap/backchannel、边聊边等待后台任务。**生产问题，证据最强** | 官方仅称公开、授权、人工提供/生成等多源数据；未披露语料规模。系统卡含生产分布评测 |
| Seeduplex | 高并发延迟尖峰与稳定性、背景人声/噪声误触发、犹豫被误判为 EOT。**真实生产问题**，有豆包 A/B 证据 | 只披露 speech-data 预训练 + 多能力/多任务后训练；来源与小时数未披露 |
| TML Interaction | 强智能与低延迟交互难以由一个模型同时满足；前台交互 + 异步后台分工。**真实需求，非生产验证** | 从零预训练数据未披露；部分 TTS 合成安全数据与自动 red-team 数据；评测含 FD-Bench/Audio MultiChallenge |
| Moshi | 把语音输入、输出和 inner monologue 对齐到同一条时间轴上，去掉 turn-taking gate。真实自然会话问题；有真实电话数据 | Helium 2.1T 公开英文文本；≈700 万 h unlabeled audio；Fisher ≈2000h 双声道电话；>20K h 合成指令语音 + 交互脚本 |
| PersonaPlex | Moshi 固定角色/声音，不适合可控服务角色。主要角色数据合成，时序部分有真实 Fisher | 105,410 客服/1840h + 39,322 QA/410h 合成；26,296 声音样本；Fisher 7303 conversations/1217h |
| Human-1 | 英语 Moshi 的 tokenizer/交互习惯不适合 Hindi。**数据真实性强，无 live serving** | 26,000h 真实双声道 Hindi 对话，14,695 speakers；≈990h 子集 fine-tune；130 位母语者 2,125 次人评 |
| MoshiRAG | 小型全双工前台事实性弱，检索/强 LLM 延迟不能阻塞交互。主要合成 speech-QA | 474K QA topics + 5.5K expert topics；≈1.9M conversation instances ≈47,770 合成 h |
| MiniCPM-o 4.5 | 单个 ≈9B omni 模型做视觉/语音实时交互，压低主 LLM 速率到 3–4 steps/s。全双工定量证据偏弱 | "millions of hours" unlabeled speech；FD 数据来自 web audio-video + 构造场景；主要 FD benchmark 是 audio-free LiveSports-3K-CC |
| Raon-SpeechChat | 英/韩端到端双工 + 可部署多 GPU session 服务端。有较大真实对话占比，无生产负载 | Raon raw 1.38M h；SpeechChat ≈119K h：13.21K h 真实 + 106.33K h 合成 |
| Fun-Audio-Chat-Duplex | 25Hz speech 与 ≈3Hz text 速率错配和 intelligence 遗忘；FD 版再处理 overlap/turn-taking。FD 训练/评测主要合成 | 总体 millions of hours；FD dialogue 由半双工增广合成，FD 小时数未披露 |
| Covo-Audio-Chat-FD | 兼顾 7B 语义、语音自然度、低延迟 FD，降低 intelligence-speaker coupling。FD 证据主要构造数据 | 200K h ASR；总预训练 ≈8M h audio + 3T text，2T training tokens；FD 预训练 5B tokens；双声道 dialogue 由半双工转换 |
| DuplexSLA | 现有 FD 主干无与语音同拍的 tool call 通道。**与 agent omni 最直接相关，未上线** | CPT ≈500K h + 1.92M text；后训练 ≈50K h（36K interaction +14K tool call）；自建 2100-case benchmark |
| DuplexOmni | 前台低延迟交互与后台推理/工具不能串行。当前仍为 8 卡单会话概念验证 | ≈620K seeds、≈3.02M conversations、10K video calls；70/30 中/英；主体合成（Qwen3.5-397B Writer） |
| BayLing-Duplex | 低成本把强轮次制 SpeechLM 改成 FD，不做百万小时预训练。**真实部署证据最弱之一** | 400K 合成：200K turn-taking + 200K interruption；来自 Alpaca/UltraChat + Llama-3.3-70B rewrite + CosyVoice；训练/评测均合成、单说话人、近场、无噪声 |
| Wan-Streamer v0.1 | 单因果 Transformer 做 text/audio/video 双向流式数字人。v0.1 只到 192p | 只给数据类别，来源/小时数/样本数均未披露 |
| RoboEgo / FLM-Ego | 全模态具身 agent 同时看/听/说/想/行动，避免 TDM ≈2s 延迟。只有演示/人评 | 只说 large-scale audio + multi-turn visually grounded dialogue；5 名标注员真实场景人评 |
| SyncLLM | LLM 无墙钟，且传输延迟造成当前 chunk 未到达；用预测+替换实现同步。只做双 agent 模拟 | 212K h 合成 dialogue；≈2K h Fisher；CANDOR 分布外 |
| OmniFlatten | 不改 GPT 架构，flatten 后学 silence/overlap/turn-taking。数据和评测以合成为主 | 模态对齐 ≈100K h（30% open 70% proprietary）；≈390K 文本对话经 TTS → 2000h 多通道 dialogue + MUSAN noise |
| SALMONN-omni | 用连续 embedding + 状态 tokens 做 FD，区分 barge-in/backchannel/回声。交互数据多为合成 | ASR 281K + 200K samples；QA ≈728K；multi-round ≈81K；大量 Llama-3-8B + CosyVoice2 合成 |
| Voila-autonomous | 端到端语音加入持续监听、角色和声音定制。FD 数据透明度低 | tokenizer 100K h audio；公开 benchmark 1580 条经 GPT-4o + Google TTS；FD 训练语料未披露 |
| LSLM | 证明单个生成模型能「边合成边听」+ IRQ。能力显著窄于现代交互模型 | 585h LibriTTS；Speech Commands 打断词；MUSAN 噪声 |

## 4. 已上线但不能据公开材料断言「模型级全双工」的边界产品

| 产品 | 已知上线/上下文 | 为什么不放进严格主表 |
| --- | --- | --- |
| [GPT-Realtime-2.1][gpt-realtime] | Realtime API；128K context、32K max output、session 最长 60 min；原生音频、barge-in；`turn_detection` 配合 truncate 对齐上下文 | 官方未说明 overlap/silence 是否像 GPT-Live 一样进入持续模型时间上下文 |
| [Gemini 3.1 Flash Live][gemini-live] | Live API；input 131,072、output 65,536；audio-only 无压缩 15 min，+video 2 min；sliding window 压缩 + 续传 | 有 barge-in，但模型内部是否持续建模 overlap/silence 未公开；不支持 proactive audio、affective dialogue、async tool |
| [Amazon Nova 2 Sonic][nova-sonic] | Bedrock 生产；双向 speech-to-speech、interrupt、async tool；最高 1M tokens；单连接 8 min 可续 | 官方仍强调 "intelligent turn-taking detects when user finishes speaking" |
| [Qwen3.5-Omni-Plus-Realtime][qwen-realtime] | Model Studio API；session 最长 120 min；history 100 audio turns / 累计 ≈600s，drop-oldest；语义打断；思考模式与音频输出互斥 | 模型内部时序与原生 tick 未公开 |

其他常被称为 full-duplex 的 FireRedChat、FlexDuo、DuplexCascade、Unmute 等，需要按其实际控制路径区分。若核心仍是外部 VAD/ASR/LLM/TTS/controller 或两套不能同时听说的 LLM 进程，属于系统级双向/级联方案，不应仅凭双向传输归入模型级全双工；但 DuplexCascade 明确提出了 **VAD-free cascaded ASR–LLM–TTS pipeline**，用固定 micro-turn 和控制 token 实现全双工，是“级联架构”和“全双工交互”可以组合的直接反例。Qwen2.5/3.x-Omni、GLM-4-Voice、Step-Audio 等普通流式语音模型也不能仅凭 streaming output 推断为模型级全双工。

明确剔除：dGSLM 是双路对话生成先驱但不是在线 agent；Mini-Omni2 的 duplex 主要是关键词打断；DuplexMamba 并行生成的是文本非 assistant speech；VITA/Freeze-Omni/MinMo/Nemotron VoiceChat 依赖双模型或外部控制。它们可作组件 baseline，但不应与模型级全双工混在同一规格表里。

## 5. 后台工作与结果注入的公开证据

- **MoshiRAG**：`⟨ret⟩` 触发检索，检索期间前台继续生成 pre-RAG 填充内容；检索文本 4× 压缩后按帧加法叠进输入嵌入（插入式注入精度更好但被弃用，理由为 "to constrain sequence length"）。检索预算 ≤2s，关键信息出现前留 ≥1.0s 缓冲，实测端到端关键词延迟 3.1s（vanilla 基线 2.1s）。
- **DuplexOmni**：thinking 层异步注入是官方设计，注入通道在模型侧标准化。
- **GPT-Live**：tool invoke 在 tick 内决策；复杂问题委托 GPT-5.5 后台执行。
- **KAME**（Sakana，[arXiv:2510.02327][kame]）：实时语音前台与后台 frontier 模型串联。

检索记录（2026-08-01）：除 Metronome 外未核验到全双工 GPU serving 论文；[Awesome-Full-Duplex-SDM][awesome-fd] 无 serving 条目。[Nemotron 3 VoiceChat][nemotron-voicechat]（2026-03，12B 开源）模型卡无并发或批量规格。

## 6. 级联与模型级全双工的 2026 比较口径（2026-09-13 增补）

- **产业分析的共识框架已从"谁更快"转为取舍**：级联胜在模块可替换、逐阶段可观测与审计、任意文本 LLM 与工具生态（[Coval 2026 指南][coval-2026]、[Gradium 对比][gradium-2026]，均为厂商/产业分析内容）；模型级全双工胜在重叠语音、backchannel、及时打断等双工行为与副语言信息（[2026 S2S 架构综述][ksopyla-2026]，个人技术博客）。"级联必然更慢"被明确否定：流式 TTS 首音频已降至 ~100 ms TTFB，级联端到端延迟主要由 LLM TTFT 决定（[Inworld 架构对比][inworld-arch]，厂商内容）。Gradium（Moshi 作者创业公司）自述当前研究问题是"把级联的模块化带进全双工架构"。
- **级联结构上的全双工决策粒度是秒级**：[DuplexCascade][duplexcascade]（arXiv:2603.09180）无任何 VAD——流式 ASR 的部分结果每 `Δt` 被 flush 成一个文本 micro-turn 送入 LLM，用户静音也照常运行（以 `<no voice>` token 表示），话轮决策由 LLM 通过控制 token（`<user is speaking>`/`<user finish speaking>`/`<user is interrupting>`/`<user backchannel>` 等）在每个 tick 作出；对话历史跨 micro-turn 持续增长（训练上限 4096 token），推理侧 KV 缓存实现未披露。`Δt` 消融（0.3–1.8 s，Full-Duplex-Bench）：话轮准确率在 1.2 s 最高后回落，延迟随 `Δt` 单调上升，作者取 0.6 s 为折中（模拟评测）。
- **交互基准对照**（自报，无独立复现）：PersonaPlex 自报 FullDuplexBench 用户打断成功率 100%（对照 Gemini Live 43.9%、Moshi 60.6%）、平均响应延迟 205 ms（[综述转述][ksopyla-2026]）。
- 检索复核（2026-09-13）：主表 2026-08 前的模型与 tick 数据无需修正；未发现 2026-08 之后新的模型级全双工生产上线声明。

## Sources

- 官方产品/系统说明：[GPT-Live 发布][gpt-live]、[system card][gpt-live-card]、[Seeduplex 页面][seeduplex]、[技术博客][seeduplex-blog]、[TML Interaction Models][tml]。
- 官方 API 文档：[GPT Realtime][gpt-realtime]、[Realtime guide][gpt-realtime-guide]、[Gemini Live][gemini-live]、[Live session guide][gemini-live-guide]、[Nova 2 Sonic][nova-sonic]、[Qwen Realtime][qwen-realtime]。
- 重点开源/serving 入口：[Moshi][moshi-repo]、[Unmute][unmute]、[PersonaPlex][personaplex-repo]、[MiniCPM-o][minicpmo-repo] / [Realtime API][minicpmo-realtime-api]、[Raon model][raon-repo] / [multi-session server][raon-server]。
- 其余开源入口：[Fun-Audio-Chat][funaudiochat-repo]、[Covo-Audio][covo-repo]、[DuplexSLA][duplexsla-repo]、[DuplexOmni][duplexomni-repo]、[BayLing-Duplex][bayling-repo]、[SALMONN][salmonn-repo]、[Voila][voila-repo]、[Nemotron 3 VoiceChat][nemotron-voicechat]；级联全双工反例见 [DuplexCascade][duplexcascade]。
- 各论文入口已链接在主表工作名上。
- 检索入口：[Awesome-Full-Duplex-SDM][awesome-fd]。

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
[duplexcascade]: https://arxiv.org/abs/2603.09180
[gpt-realtime]: https://developers.openai.com/api/docs/models/gpt-realtime-2.1
[gpt-realtime-guide]: https://developers.openai.com/api/docs/guides/realtime-conversations
[gemini-live]: https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-live-preview
[gemini-live-guide]: https://ai.google.dev/gemini-api/docs/live-session
[nova-sonic]: https://docs.aws.amazon.com/nova/latest/nova2-userguide/
[qwen-realtime]: https://www.alibabacloud.com/help/en/model-studio/realtime
[coval-2026]: https://www.coval.ai/blog/voice-ai-models-2026
[gradium-2026]: https://gradium.ai/content/cascaded-voice-agent-vs-speech-to-speech-2026
[ksopyla-2026]: https://ai.ksopyla.com/posts/voice-to-voice-models-2026-review
[inworld-arch]: https://inworld.ai/resources/cascaded-vs-speech-to-speech-voice-architecture
