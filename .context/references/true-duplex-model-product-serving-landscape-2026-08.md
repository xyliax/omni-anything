# 真双工模型、产品与 serving 版图（2026-08）

Updated: 2026-08-03

## 口径与先给结论

本文只把下面这种系统算作**模型级真双工**：模型在输出期间继续吸收输入，并把沉默、重叠、backchannel、打断或主动开口当作模型时间上下文/学习到的动作。以下两类不自动算：

- WebSocket 能同时收发，或用户说话时取消 TTS；
- `VAD 判停 → ASR → text LLM → TTS`，即使各模块都做成流式。

“一拍”指模型或调度器完成一次交互决策的原生时间量子，不是网络包长、首包延迟或 benchmark 给的 deadline。容量数字分为“实测”“配置 cap”“下界”“外推”；没有数据一律写“未披露”。

三个结论：

1. 截至 2026-08-03，公开证据能同时证明“模型级真双工 + 大规模生产上线”的只有 **GPT-Live** 和 **Seeduplex**；两家都不公开参数、一拍、上下文和单 GPU 容量。MiniCPM-o 4.5 已有官方 hosted Realtime API，但没有公开流量或 SLA。
2. 开源侧真正给出多会话 WebSocket/Ray/SGLang server 的 **Raon-SpeechChat** 最完整，但 `2 sessions/GPU` 只是默认配置 cap，不是测得的最大值。多数论文只有单会话 demo 或离线 inference。
3. 唯一系统性公开“单 GPU 能撑多少路、短测与长会话为何不同”的是 **Metronome**；它是 serving system，不是模型。其结果说明 `90 s burst capacity` 不能当作可持续容量。严格主表中的工作均未公开端到端 GPU/SM utilization 或 MFU。

## 1. 已上线或前沿闭源模型

| 工作 | 首次公开 | 是否用于上线 serving | 原生一拍 | 参数 | 单会话上下文 | 单 GPU 最多会话 | 量化 / 硬件 / 实现 |
| --- | --- | --- | ---: | ---: | --- | --- | --- |
| [GPT-Live][gpt-live] | **2026-07-08**，官方发布 | **是，生产**。GPT-Live-1 为 ChatGPT Voice 的 Go/Plus/Pro 默认，mini 为 Free 默认；API 尚未开放；官方称 Voice/Dictation 周用户超过1.5亿（不是并发数） | 未披露；仅称每秒多次决定 `speak/listen/pause/interrupt/tool` | 未披露 | 未披露 | 未披露 | 未披露 |
| [Seeduplex][seeduplex] | **2026-04-09**，官方发布 | **是，生产**。已 fully rolled out 到豆包 App，官方称服务数亿用户 | 未披露 | 未披露 | 未披露 | 未披露 | speculative decoding + quantization；bitwidth、GPU 未披露 |
| [TML-Interaction-Small][tml] | **2026-05-11**，research preview | **否**。页面仍称未来开放 limited preview | **200 ms** micro-turn | **276B MoE / 12B active** | 未披露；官方明确超长 session 仍是问题 | 未披露 | Blackwell、NVLS、自定义 MoE gather+gemv、batch-invariant kernels、persistent SGLang streaming session；GPU 数量/量化未披露 |

注意：GPT-Live 与 `GPT-Realtime-2.1` 不是同一个公开产品口径；后者见第 6 节边界表。

## 2. 公开模型与研究原型：规格和 serving 事实

| 工作 | 首次公开 | serving / 开源状态 | 原生一拍 | 参数 | 单会话上下文 | 单 GPU 会话数 | 量化 / 硬件 |
| --- | --- | --- | ---: | ---: | --- | --- | --- |
| [Moshi][moshi] | **2024-07-03** 首次介绍；09-17 论文 v1；09-18 开源 | `moshi.chat` 研究 demo + 自部署 server；无托管 API/SLA；官方主路径没有多会话容量报告 | **80 ms**（Mimi 12.5 Hz） | Helium **7B** backbone；完整 Moshi 总参数未汇总披露 | 3000 temporal steps，约 **4 min**；论文另称实验可到约 5 min | 官方未披露；Metronome 第三方在单 RTX PRO 6000 Blackwell 上测得 **≥32**，仅是 90 s 下界 | PyTorch BF16/实验 INT8；MLX INT4/INT8/BF16；Candle INT8/BF16 |
| [PersonaPlex][personaplex] | **2026-01-14**，论文 v1 | NVIDIA research demo + 自部署；无商业 API | **80 ms**，继承 Moshi | Moshi **7B** fine-tune；总参数未另报 | 3000 steps，约 **4 min** | 未披露 | 官方 checkpoint 为 BF16；支持 CPU offload；训练 8×A100、6 h 不是 serving 配置；无官方量化 checkpoint |
| [Human-1][human1] | **2026-04-25**，论文 v1 | 论文；未核验到公开 live server、权重或容量报告 | **80 ms**，继承 Moshi | Moshi/Helium **7B** 路径；总参数未另报 | **2048 steps ≈2.7 min** | 未披露 | bf16；训练 8×H100 80GB；这不是 serving 配置 |
| [MoshiRAG][moshirag] | **2026-04-14**，论文 v1；04-30 官方博客 | inference code / demo videos；非 live API | **80 ms** | 7B Moshi 前台 + 1B streaming ASR；默认后台 Gemma-3 27B，也可 GPT-4.1/Tavily | 继承 Moshi，约 **4 min** | 未披露 | 单流评测：前台在1×H100，本地 Gemma 后台另占1 GPU；量化未披露 |
| [MiniCPM-o 4.5][minicpmo] | **2026-02-03** 模型开源；04-30 论文 v1 | 官方 hosted [Realtime API][minicpmo-realtime-api] + web/local demo；05-17 公布 API 服务；无流量/SLA | **1.0 s**；0.2/0.1 s 仅为质量明显下降的 ablation | **9.34B total** | main LLM **40,960**；speech decoder **4096**；无经验证的墙钟 session 上限 | 官方未披露；Metronome 第三方：单 Blackwell 约 **96** 路 90 s fresh；windowed KV 在 N=96 维持 10 min | llama.cpp-omni INT4：RTX 4090 11GB、RTF 0.21；PyTorch INT4 约14GB；BF16 4090 OOM |
| [Raon-SpeechChat][raon] | **2026-04-08**，论文 v1 | 官方在线 demo；公开 WebSocket + Ray GPU pool + SGLang multi-session server；无生产流量/SLA | **80 ms**（12.5 Hz；网络帧也正好 1920 samples@24k） | 品牌称 9B；精确 full model 约 **9.8B**（8.8B shared + 约1.008B encoder/adaptor） | 论文训练 **4096 ≈2 min**；公开 runtime 默认 KV `8192`，约 4 min，后者不是长时质量证明 | **默认配置 cap=2/GPU，非实测最大值**；GPU 型号与压测曲线未披露 | BF16/FP16；权重约25GB；16GB+ VRAM recommended；无官方量化 checkpoint |
| [Fun-Audio-Chat-Duplex][funaudiochat] | **2025-12-23**，论文 v1 | **FD 版本没有公开权重/server**。已发布的 8B checkpoint、web demo 和约24GB inference 要求对应通用 Fun-Audio-Chat，不能当成 FD serving 证据 | shared backbone **5 Hz = 200 ms**；refined speech head 25 Hz | dense **8B**；MoE **30B total / 3B active** | **2048 tokens ≈6 min** | 未披露 | FD 量化/硬件未披露；已发布非 FD 8B 路径约24GB VRAM |
| [Covo-Audio-Chat-FD][covo] | **2026-02-10**，论文 v1 | **FD checkpoint 未发布**；只开源了 Covo-Audio-Chat（半双工）及 inference pipeline | **160 ms**；1 个 6.25Hz 输入 feature 对 4 个 25Hz 输出 token | **7B**，Qwen2.5-7B-Base 路径 | 训练/SFT sequence length **8192**；墙钟上限未披露 | 未披露 | FD 量化、serving GPU、容量未披露 |
| [DuplexSLA][duplexsla] | **2026-05-20**，论文 v1 | 只有技术报告和 demo 页；README 明确 checkpoint、inference/server、benchmark artifacts **coming soon** | **160 ms**；2×80ms 用户 feature + 4×40ms assistant token；每拍 action≤10 token | **7B**，从 Step-Audio 2 mini 初始化 | 未披露 | 未披露 | 每拍预算声称适配 mainstream accelerator，但未披露 GPU、量化或容量 |
| [DuplexOmni][duplexomni] | **2026-06-08**，论文 v1 | 公开数据/训练/modified-vLLM serving 代码，但数据和 checkpoint 仍是 external placeholder；当前 orchestrator 为单 session | **480 ms**，每拍 6 个 Mimi frames | Qwen3-Omni **30B total / 3B active** interaction base；完整系统还含 Talker/Code2Wav 与外部 S2，不能说全系统仅30B | thinker/talker runtime cap **32,386**；未给经验证的墙钟 session | 单 GPU不适用/未披露；公开默认拓扑是 **1 session / 8 GPUs**（thinker TP4 + talker TP4），不是容量 benchmark | dtype `auto`；无公开量化 |
| [BayLing-Duplex][bayling] | **2026-06-12**，论文 v1 | weights + offline audio-file CLI；未发现正式 live multiuser server | **800 ms 决策 block**；底层 speech token 80ms，但每10个 token 才决策一次 | **9B LLM**；tokenizer/decoder 额外参数未汇总 | config **32,768**；按每0.8s固定25 serialized tokens，空 prompt 理论约17.5min，**推导值、非长时实测** | 未披露 | BF16；GPU 型号/量化未披露 |
| [Wan-Streamer v0.1][wan] | **2026-06-23**，论文 v1 | proof-of-concept；未核验到 weights/code/live service | **160 ms** streaming unit；model-side signal-to-signal约200ms | 未披露 | 称 full-history KV，未给窗口数字 | 单 GPU未披露；论文路径是 **2 GPUs/1 session**（GPU0 thinker、GPU1 performer），GPU 型号未披露 | 量化未披露；当前输出192p |
| [RoboEgo / FLM-Ego][roboego] | **2025-06-02**，论文 v1 | system card + demos；未核验到 public weights/code/live serving | **80 ms theoretical** | **7B backbone**；模态 heads 的总参数未汇总 | 未披露 | 未披露 | 量化/serving hardware 未披露 |
| [SyncLLM][syncllm] | **2024-09-23**，论文 v1 | 论文与音频样例；无已核验生产 serving、容量或正式 checkpoint/server | **160/200/240 ms**，主设定160ms | Llama-3 **8B** | **8192 serialized tokens**；因 speech-token dedup，墙钟长度不固定 | 未披露 | serving dtype/硬件/量化未披露；128×A100 是训练硬件 |
| [OmniFlatten][omniflatten] | **2024-10-23**，论文 v1 | 论文；未核验到 production/live multiuser server | 10 个 speech-token/chunk；按其 CosyVoice2 25Hz tokenizer约 **400 ms（外部速率推导）**，论文没有直接写毫秒 | Qwen2 **0.5B backbone**；完整 audio 模块总参数未汇总 | **8192 tokens**；墙钟长度未披露 | 未披露 | 量化/serving hardware 未披露 |
| [SALMONN-omni][salmonn] | **2025-05-17**，论文 v1 | repo 有 demo conversations；未核验到 live server、公开 FD checkpoint 或容量报告 | **80 ms**；但 speech synthesizer 4 个 LLM token 才产480ms语音，启动另有320ms设计延迟 | Llama-3 **8B** + CosyVoice2 **0.5B** + Mamba encoder；总参数未汇总 | 未披露 | 未披露 | 量化/serving hardware 未披露；32×A100 是训练硬件 |
| [Voila-autonomous][voila] | **2025-04-28** 权重/推理代码；05-05 论文 v1 | 权重、离线 inference、Gradio/HF demo；公开 autonomous 路径输入的是预录音频，不是经验证的生产 live multiuser serving | **未披露**；195ms 是 response latency，不是原生拍 | 完整总参数未披露；HF config 是32层、4096 hidden 的 Llama-style backbone | HF config `max_position_embeddings=8192`；墙钟长度未披露 | 未披露 | BF16；无官方量化/容量数据 |
| [LSLM][lslm] | **2024-08-05**，论文 v1 | 早期研究原型；无生产 server。能力是“生成给定 TTS 内容时听取另一通道并发出 IRQ”，不是完整开放域 speech-to-speech agent | audio-token 拍未显式换算为毫秒；训练目标要求在 interruption 开始后 **0.5 s** 内 IRQ | 106M decoder + 34M vq-wav2vec encoder；vocoder未计入，故完整总参数未披露 | 未披露 | 未披露 | 未披露 |

## 3. Serving 配置、并发和 GPU 指标审计

本轮没有找到任何一项严格真双工工作公开端到端 **GPU/SM utilization 或 MFU 百分比**。几个容易误读的量不是 GPU 利用率：TML 的 `<5%` 是 batch-invariant kernel 相对端到端 overhead；DuplexOmni 的 `gpu_memory_utilization=0.8/0.6/0.12` 是 vLLM 显存池预留比例；RTF、显存、tokens/s 和 frame latency 也不能换算成利用率。Wan-Streamer 只定性声称通过两卡流水重叠提高 hardware utilization，没有给数值。

| 工作 | 公开 serving 拓扑 / 常用配置 | 并发证据 | 公开效率、显存或延迟 | 证据性质 |
| --- | --- | --- | --- | --- |
| GPT-Live | 已在 ChatGPT Voice 生产 serving；GPU、卡数、精度、调度器均未披露 | 只披露周用户量，**不是并发** | 未披露 | 官方生产状态；无容量规格 |
| Seeduplex | 豆包生产；speculative decoding + quantization；bitwidth/GPU/卡数未披露 | 只称解决高并发 latency spike 和稳定性，未给每卡会话数 | 相对上一代 endpoint latency约−250ms、打断约−300ms；这是产品 A/B，不是 kernel/GPU 指标 | 官方生产状态与 A/B；无容量规格 |
| TML-Interaction-Small | Blackwell + NVLS；SGLang persistent streaming sequence；自定义 MoE gather+GEMV、通信和 batch-invariant kernels | 未披露 GPU 数或会话数 | 200ms micro-turn；batch-invariant kernels e2e overhead `<5%`，**不是利用率** | 官方 research preview |
| Moshi | 简单 Python server 固定 `batch_size=1`、`streaming_forever(1)` 且用全局 lock；Rust `moshi-server` 则有可配置 fixed batch slots、execution mask 和空槽复用 | Python 路径为 **1 active session/process 的代码 cap**；Rust 未发布正式 B/容量；Metronome 第三方单 Blackwell 90s测 **≥32** | L4 上整体 latency最低约200ms；PyTorch BF16约需24GB级 GPU。论文完整 Moshi model size：BF16A8 16.74GB、W8A8 9.20GB、W4A8 5.18GB；在线 demo 用8-bit，W4质量下降明显 | 官方代码/论文 + 第三方短测下界 |
| PersonaPlex | 官方 Python server 同样 `streaming_forever(1)` + global lock；BF16 checkpoint，可 CPU offload | **1 active session/process 的代码 cap**；未做容量压测 | 未披露 serving GPU、VRAM、RTF；8×A100/6h 是训练配置 | 官方代码；不能解释成模型最大并发1 |
| MoshiRAG | 单流评测时前台 Moshi + streaming ASR 在1×H100；本地 Gemma-3 27B retrieval backend 在另1 GPU。云 API/Tavily 路径不同 | 未披露；论文是两GPU单流评测拓扑，不是容量压测 | 大多数本地 retrieval在1.5s内；超过约1.5s后准确率明显下降；FLOPs/s表不是利用率 | 官方论文单流配置 |
| MiniCPM-o 4.5 | 官方 hosted Realtime WebSocket；本地 full-duplex 推荐 `llama.cpp-omni`；另支持 PyTorch/vLLM/SGLang | 官方未披露；Metronome 单 Blackwell：90s fresh约96路；windowed KV在N=96维持10min，unbounded不足2min stall | 见下表；官方 RTF/显存是单流效率。Metronome为第三方容量 | 官方单流效率 + 第三方容量 |
| Raon-SpeechChat | Browser WebSocket → CPU FastAPI/Uvicorn gateway → Ray router → 每GPU一个 SGLang worker actor；`FD_GPU_IDS` 选卡 | `FD_MAX_SESSIONS_PER_GPU=2` 默认，**只是配置 cap**；多卡按配置近似 `2×GPU数`，无极限压测 | CUDA 12.x、16GB+ VRAM recommended、BF16/FP16、模型下载约25GB。另有单GPU streaming TTS：RTX PRO 6000 Blackwell RTF 0.27/TTFT 617ms；L40S RTF 0.45/TTFT 887ms，**不是 SpeechChat duplex 容量** | 官方可部署多会话 server；cap非最大值 |
| DuplexOmni | 默认8 GPU：Thinker GPU0–3/TP4；Talker GPU4–7/TP4；MTP子进程共享GPU7。Thinker/Talker max model len均32386 | orchestrator 显式拒绝第二条 active session，故公开栈是 **1 session/8 GPUs 的代码 cap** | response latency约0.506s；`0.8/0.6/0.12` 分别是三引擎显存池配置，非实测利用率；GPU型号、实测显存、吞吐未披露 | 官方代码 proof-of-concept |
| Wan-Streamer v0.1 | GPU0 Thinker负责编码/KV更新/上一帧解码；GPU1 Performer负责 flow-matching latent generation，二者按帧交换 KV/latent；CUDA graph/compile/optimized kernels | 公开路径仅证明 **2 GPUs/1 session**，没有多会话压测 | 160ms unit、约200ms model-side、加350ms双向网络约550ms、25FPS；GPU型号/显存未披露 | 官方论文单流拓扑 |
| Metronome | 单 RTX PRO 6000 Blackwell；WebSocket client + Go gateway + vLLM-realtime GPU worker；20ms真实音频、不同且错相 session；bounded KV + sinks + AIMD admission | Moshi ≥32@80ms；MiniCPM约96@1s；Qwen3-Omni ≥160@2s；Qwen2.5-Omni 16–24@2s；详见第5节 | Qwen3 open-system稳定约209 live sessions、steady p99 per-frame约12ms；仍未报告GPU利用率 | 第三方、唯一系统性容量实测 |

MiniCPM-o 4.5 是严格主表里官方单流效率数据最完整的一项，但需要区分两组口径：

| 路径 / 硬件 | 精度 | 结果 | 适用边界 |
| --- | --- | --- | --- |
| `llama.cpp-omni` / RTX 4090 | FP16 / INT4 | RTF 0.27、19GB / **0.21、11GB** | full-duplex/streaming 单流 |
| `llama.cpp-omni` / DGX Spark | FP16 / INT4 | RTF 0.46、19GB / **0.20、11GB** | full-duplex/streaming 单流 |
| PyTorch / RTX 4090 | BF16 / INT4 | OOM / RTF 1.26、14GB | full-duplex/streaming 单流 |
| PyTorch / DGX Spark | BF16 / INT4 | RTF 2.43、26GB / RTF 1.27、14GB | full-duplex/streaming 单流 |
| vLLM / RTX 4090 | BF16 / INT4 | 154.3 / 212.3 tokens/s；TTFT 0.59 / 0.58s；19 / 11GB | throughput/显存是 **text-only**；TTFT用64帧视觉输入，不能当 duplex 容量 |

其余工作没有可用容量数据：Human-1、RoboEgo、SyncLLM、OmniFlatten、SALMONN-omni、Voila 和 LSLM 只有论文/demo/offline inference；BayLing 只有 audio-file CLI；Covo-Audio-Chat-FD、DuplexSLA 以及 Fun-Audio-Chat 的 FD artifact/server 尚未发布。论文中的训练 GPU 数不计入 serving 配置。

## 4. 每个工作解决什么问题，问题是否来自真实场景，数据来自哪里

| 工作 | 要解决的问题 / 真实性判断 | 训练与评测数据证据 |
| --- | --- | --- |
| GPT-Live | 旧 Advanced Voice Mode 虽端到端，交互仍按离散 turn；解决停顿误判、自然 overlap/backchannel、边聊边等待后台任务。**生产问题，证据最强** | 官方仅称公开、授权、人工提供/生成等多源数据；未披露语料规模/清单。系统卡含 production distribution eval |
| Seeduplex | 高并发 latency spike、稳定性、背景人声/噪声误触发、犹豫被误判 EOT。**真实生产问题**，有豆包 A/B：相对上一代 endpoint约−250ms、打断约−300ms、premature response −40% 等 | 只披露 speech-data pretraining + multi-capability/multi-task post-training；来源、小时数未披露 |
| TML Interaction | 强 intelligence 与低延迟 interactivity 难以由一个模型同时满足；以前台 interaction model + 异步 background model 分工。**真实需求，尚非生产验证** | from-scratch 主预训练数据未披露；只公开部分 TTS 合成安全数据与自动多轮 red-team 数据；评测含 FD-Bench/Audio MultiChallenge/demos |
| Moshi | 把语音输入、语音/沉默输出和 inner-monologue 放进同一时钟，去掉 turn gate。真实自然会话问题；有真实电话数据，但产品流量未公开 | Helium 2.1T public English text tokens；约700万小时 unlabeled audio；Fisher约2000h双声道电话；>20K h synthetic instruction speech + interaction scripts |
| PersonaPlex | Moshi 固定角色/声音，不适合可控服务角色。真实产品需求；主要角色数据合成，时序部分有真实 Fisher | 105,410 customer-service dialogues/1840h + 39,322 QA/410h synthetic；26,296 voice samples；released checkpoint另训 Fisher 7303 conversations/1217h |
| Human-1 | 英语 Moshi 的 tokenizer/交互习惯不适合 Hindi。**数据真实性很强，但没有 live serving 证据** | 26,000h真实、自发、双声道 Hindi 对话，14,695 speakers，由受雇参与者采集；约990h高质量子集 fine-tune；130位母语者做2,125次人评 |
| MoshiRAG | 小型真双工前台 factuality弱，检索/强 LLM 延迟又不能阻塞交互。需求真实；实验证据主要是合成 speech-QA | 474K QA topics（NQ约307K、HotpotQA约90K、TriviaQA约76K）+5.5K expert topics；约1.9M conversation instances、约47,770 synthetic hours；Gemma 3 27B写脚本/reference，多通道TTS |
| MiniCPM-o 4.5 | 在单个约9B模型里做视觉/语音实时 omni interaction，并把主 LLM 速率压到3–4 text steps/s。需求真实；真双工定量证据仍偏弱 | “millions of hours” unlabeled speech，来源仅称 diverse/open pipeline；FD 数据来自 large-scale web audio-video + manually constructed scenarios，精确规模未披露；主要 FD benchmark 是 audio-free LiveSports-3K-CC，真实长时 robustness 未证实 |
| Raon-SpeechChat | 英/韩端到端双工，同时提供真正可部署的多 GPU session server。真实需求；有较大真实对话占比，但无生产 workload | Raon raw 1.38M h；SpeechChat约119K h：13.21K h real conversation +106.33K h synthetic；public + in-house English/Korean，audio-only经Whisper伪标、text-only经Qwen3-TTS |
| Fun-Audio-Chat-Duplex | 25Hz speech 与约3Hz text 的速率错配、算力开销和 text intelligence 遗忘；FD 版再处理 overlap/turn-taking。问题真实；FD 训练/评测主要合成 | 总体称 millions of hours，来自 DrVoice/Audio-Flamingo-3 recipe + in-house；FD dialogue 由 half-duplex dialogue 增广合成，未披露 FD 小时数；真实线上对话未验证 |
| Covo-Audio-Chat-FD | 兼顾7B语义智能、语音自然度、低延迟 FD，并降低 intelligence-speaker coupling 的换声成本。问题真实；FD 证据仍主要是构造数据/benchmark | 200K h ASR alignment；总预训练约8M h audio/speech +3T text，2T training tokens；FD pretraining占5B tokens；双声道 dialogue 由半双工数据转换并插入 barge-in/backchannel，精确真实/合成比例未披露 |
| DuplexSLA | 现有 FD backbone 没有与语音同拍的 planning/tool-call 通道；turn-final tool call 会迟一整轮。**与 agent omni 最直接相关，但未上线** | CPT约500K h（320K duplex dialogue +2×90K h双侧ASR）+1.92M text；posttrain约50K h（36K interaction control +14K tool call）；图示 pipeline 为LLM标注、TTS/voice cloning、force alignment，原始语料来源与真实比例未披露；自建2100-case benchmark |
| DuplexOmni | 前台低延迟交互与后台 reasoning/tool 不能串行，S1继续说/听，S2异步返回再注入。问题真实；当前 runtime 仍为8卡单会话 proof-of-concept | ~620K scenario seeds、~3.02M raw conversations、10K video calls，70%中文/30%英文；源文本含UltraChat/WildChat/BELLE/COIG/no-robots/OASST2；Qwen3.5-397B-A27B Writer/Director + Qwen3-TTS/Mimi，主体为合成 |
| BayLing-Duplex | 不做百万小时重新预训练，低成本把强 turn-based SpeechLM 改成 FD。工程动机真实；**真实部署证据最弱之一** | 400K synthetic samples：200K turn-taking +200K interruption；原始对话来自Alpaca/UltraChat，经Llama-3.3-70B rewrite、CosyVoice合成；论文明确训练/评测均为 synthetic、单说话人、近场、无噪声 |
| Wan-Streamer | 单个 causal Transformer 做 text/audio/video 双向流式数字人，去掉独立 VAD/ASR/LLM/TTS/avatar/video generation。应用真实；v0.1只到192p，production evidence不足 | 只给数据类别（理解、文本对话、ASR/TTS/audio dialogue、各类生成与end-to-end duplex AV interaction）；来源、小时数、样本数均未披露 |
| RoboEgo | omnimodal embodied agent 要同时看、听、说、想、行动，避免 TDM 带来的约2s延迟。真实具身场景；只有system-card级演示/人评 | 只说 large-scale audio 与多轮 visually grounded speech dialogue，并做 interruption/noise augmentation；规模、来源、真实/合成比例均未披露；有5名标注员真实场景人评和机器人demo |
| SyncLLM | 普通 LLM 没有墙钟，且互联网传输造成当前用户 chunk 尚未到达；用预测当前 chunk、下一拍再替换实现同步。真实网络问题；只做双 agent 模拟，未做 live-human serving | 212K h synthetic spoken dialogue；约2K h Fisher real dialogue；CANDOR作OOD；主要评测为模拟 agent-agent 交互 |
| OmniFlatten | 不改 GPT 架构，把多路 speech/text flatten 后学习 silence、overlap、turn-taking。需求真实；数据和评测以合成为主 | modality alignment约100K h（30% open、70% proprietary；open含AIShell-3/LibriTTS/TED-LIUM/VoxPopuli/LibriSpeech/MLS/WenetSpeech）；约390K文本对话经TTS，最终2000h simulated multi-channel dialogue + MUSAN noise |
| SALMONN-omni | codec injection 容易损伤 LLM 智能；用连续 embedding + single LLM state tokens做 standalone FD，并区分真正 barge-in、backchannel、自身 echo。问题真实；interaction 数据多为合成 | ASR：LibriSpeech 281K + GigaSpeech 200K samples；QA约728K；multi-round约81K；回答/对话大量由Llama-3-8B + CosyVoice2合成；barge-in/backchannel由提示模板生成；评测也有小规模人工/构造集 |
| Voila-autonomous | 端到端语音仍常是 reactive turn-based；加入持续监听、角色和声音定制。需求真实；FD 数据透明度低 | tokenizer训100K h audio，来源未披露；公开benchmark由MMLU/MATH/HumanEval/NQ/GSM8K共1580条经GPT-4o改写+Google TTS；FD训练语料规模/来源未披露 |
| LSLM | 证明单个生成模型能“边合成边听”，并在噪声中学习 IRQ；但只是在已知 TTS 内容生成过程中检测打断，能力显著窄于现代 interaction model | 585h LibriTTS；Speech Commands作打断词；MUSAN作噪声；训练时随机混入打断/噪声，非真实自由对话 |

## 5. Metronome：不要把它误当模型

[Metronome][metronome]（**2026-07-02**，论文 v1）是 serving system：周期性将所有到期 session 的小 prefill + 短 decode 组成一批，用 bounded KV + attention sinks 避免长期 KV memory cliff，再用 AIMD admission 找可调度并发。所有实验均为**单张 NVIDIA RTX PRO 6000 Blackwell**、真实音频以20ms网络 chunk输入、不同且错相的 session；容量不是 prefix-cache 复用出来的。

| 被 serve 的模型 | 实验 frame budget | 90 s fresh 单 GPU 容量 | 长会话证据 |
| --- | ---: | ---: | --- |
| Qwen3-Omni-30B-A3B FP8 | 2 s | **≥160**，只测到160，故是下界 | W=1024约40s + sinks；open-system AIMD 稳定约 **209 live sessions**。约500只是 KV 内存线性外推，不是实测可服务数 |
| MiniCPM-o 4.5 | 1 s | **约96** | N=96 windowed KV 完整维持10min、median个位数ms；unbounded KV不足2min hard stall |
| Moshi | 80 ms | **≥32**，只测到32 | 只报告90s fresh下界，没有同等规模长会话最大值 |
| Qwen2.5-Omni-7B | 2 s | **16–24** | 只报告90s fresh capacity；audio encoder bound |

这里最重要的系统事实不是某个孤立数字，而是：unbounded resident KV 在短测里 latency 可以一直健康，随后所有 session 一起 stall；deadline-miss counter 甚至仍可能为0。故容量报告至少应同时给**硬件、拍长、session age、KV policy、是否真实音频、是否错相、测到的上限还是下界**。

## 6. 已上线，但不能据公开材料断言“模型级真双工”的边界产品

| 产品 | 已知上线/上下文 | 为什么不放进严格主表 |
| --- | --- | --- |
| [GPT-Realtime-2.1][gpt-realtime] | Realtime API GA；128K context、32K max output、session最长60min；native audio、barge-in | 官方未说明 overlap/silence 是否像 GPT-Live 一样进入持续模型时间上下文；GPT-Live发布材料反而把旧AVM描述为turn-based |
| [Gemini 3.1 Flash Live][gemini-live] | Live API；input 131,072、output 65,536；audio-only无压缩15min，audio+video 2min；压缩+resumption可延长 | 有 barge-in，但模型内部是否持续建模 overlap/silence 未公开；当前还不支持 proactive audio、affective dialogue、async tool call |
| [Amazon Nova 2 Sonic][nova-sonic] | Bedrock生产服务；双向speech-to-speech、interrupt、async tool；上下文最高1M tokens；单连接8min可续 | 官方仍强调“intelligent turn-taking detects when user finishes speaking”；transport双向不等于已公开证实 interaction-model semantics |
| [Qwen3.5-Omni-Plus-Realtime][qwen-realtime] | Model Studio API；WebSocket session最长120min；history 100 audio turns / 累计600s audio；semantic interruption | 支持 VAD/manual commit，但模型内部时序与原生拍未公开，不能从产品接口反推 strict FD architecture |

其他常被称为 full-duplex 的 FireRedChat、FlexDuo、DuplexCascade、Unmute 等，若核心仍是外部 VAD/ASR/LLM/TTS/controller 或两套不能同时听说的 LLM 进程，属于系统级双向/级联方案，不纳入本表。Qwen2.5/3.x-Omni、GLM-4-Voice、Step-Audio 等普通 streaming speech model 也不能仅凭 streaming output 推断为模型级真双工。

几项容易混入但本次明确剔除的工作：dGSLM 是双路对话**生成**先驱，但不是持续接入外部真人流的在线 agent；Mini-Omni2 的公开 duplex 行为主要是 `Stop Omni` 关键词打断，不足以证明语义 backchannel/overlap 建模；DuplexMamba 在接收语音时并行生成的是文本而非 assistant speech；VITA/Freeze-Omni/MinMo/Nemotron VoiceChat 公开方案依赖双模型、独立感知/TTS或外部控制，属于非 standalone 或 hybrid system。它们仍可作组件/系统 baseline，但不应与 GPT-Live、Seeduplex、Moshi 这类模型级真双工混在同一张规格表里。

## 7. 对 omni-anything 的直接启示

- 生产产品证明的是**能力必要性**，没有公开 serving 规格，不能用来做容量基线。
- Raon 是当前最接近“可复用开源 serving 外壳”的工作；Metronome 是容量与长 session 方法学基线。
- DuplexSLA 与 DuplexOmni 分别代表两条 agent 路线：前者把 action/tool 变成前台模型的同拍通道；后者保留前台交互模型，把强 agent/LLM 放到异步后台。当前项目关注的是后一种“前台持续交互 + 后台异步写回”的系统形态；这里不把是否 training-free 预设成研究结论。
- 所有“最大并发”讨论都必须绑定拍长和 session age。80ms Moshi 的32路下界、1s MiniCPM的96路与2s Qwen的160/209路不能横向当成模型效率排行榜。

## Sources

- 官方产品/系统说明：[GPT-Live 发布][gpt-live]、[system card][gpt-live-card]、[Seeduplex 页面][seeduplex]、[技术博客][seeduplex-blog]、[TML Interaction Models][tml]、[GPT Realtime][gpt-realtime]、[Realtime guide][gpt-realtime-guide]、[Gemini Live][gemini-live]、[Live session guide][gemini-live-guide]、[Nova 2 Sonic][nova-sonic]、[Qwen Realtime][qwen-realtime]。
- 重点开源/serving入口：[Moshi][moshi-repo]、[PersonaPlex][personaplex-repo]、[MiniCPM-o][minicpmo-repo] / [Realtime API][minicpmo-realtime-api]、[Raon model][raon-repo] / [multi-session server][raon-server]、[Fun-Audio-Chat][funaudiochat-repo]、[Covo-Audio][covo-repo]、[DuplexSLA][duplexsla-repo]、[DuplexOmni][duplexomni-repo]、[BayLing-Duplex][bayling-repo]、[SALMONN][salmonn-repo]、[Voila][voila-repo]。各论文入口已链接在主表工作名上。

[gpt-live]: https://openai.com/index/introducing-gpt-live/
[gpt-live-card]: https://deploymentsafety.openai.com/gpt-live
[seeduplex]: https://seed.bytedance.com/en/seeduplex
[seeduplex-blog]: https://seed.bytedance.com/en/blog/introducing-seed-full-duplex-speech-llm-attentive-listening-robust-interference-suppression-enabling-more-natural-interaction
[tml]: https://thinkingmachines.ai/blog/interaction-models/
[moshi]: https://arxiv.org/abs/2410.00037
[moshi-repo]: https://github.com/kyutai-labs/moshi
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
[metronome]: https://arxiv.org/abs/2607.02640
[gpt-realtime]: https://developers.openai.com/api/docs/models/gpt-realtime-2.1
[gpt-realtime-guide]: https://developers.openai.com/api/docs/guides/realtime-conversations
[gemini-live]: https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-live-preview
[gemini-live-guide]: https://ai.google.dev/gemini-api/docs/live-session
[nova-sonic]: https://docs.aws.amazon.com/nova/latest/nova2-userguide/
[qwen-realtime]: https://www.alibabacloud.com/help/en/model-studio/realtime
