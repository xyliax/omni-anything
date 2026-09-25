# 交互与语音服务：外部系统索引

外部文献导航，不维护项目设计、实验结论或新颖性判断。下表限定到所链接论文版本；软件当前支持范围须查对应实现。

## 服务系统

| 工作与原始来源 | 论文研究的对象 | 可用于比较的属性 |
| --- | --- | --- |
| [VoxServe](https://arxiv.org/html/2602.00269v1) | 流式语音生成请求 | 将首音启动和持续播放分开调度，协调模型与解码阶段；论文中的请求调度不能直接等同于跨周期会话驻留 |
| [Metronome](https://arxiv.org/html/2607.02640v1) | 周期交互中的持续 KV 增长 | 窗口与 attention sinks 限制保留状态，按延迟反馈控制准入；其 Qwen-Omni 实验的 2 s 是服务负载配置 |
| [LiveServe](https://arxiv.org/html/2606.22983v1) | 支持播放与打断的多轮语音服务 | 利用播放进度安排生成，按预计复用排序逐出，在用户开始说话或打断时预装 KV |
| [vLLM-Omni](https://arxiv.org/html/2602.02204v1) | 多阶段多模态模型执行 | 阶段图、独立引擎与阶段间数据传输；论文版本和持续更新的软件支持范围应分开 |

VoxServe 与 LiveServe 的相关段落于 2026-09-25 复核。KV 管理的详细比较入口见[文献笔记](closest-work-gap-analysis-2026-09.md)。

<a id="realtime-ecosystem"></a>
## 实时接口与交互生成实例

以下一手来源于 2026-09-25 复核，记录公开接口与系统类型，不推定它们采用相同的历史状态模型。

| 外部系统 | 一手来源支持的属性 | 限定 |
| --- | --- | --- |
| vLLM streaming requests / Realtime API | 官方介绍流式输入以及基于它的 Realtime WebSocket API，提供 `/v1/realtime` 接口；流式输入通过持续存在的 anchor request 保留会话，后续输入扩展累计上下文并复用已有 KV；[官方说明](https://vllm.ai/blog/2026-01-31-streaming-realtime) | 流式接口本身不证明某项跨周期 KV 管理方案已被集成 |
| SGLang streaming sessions | 核心引擎具有跨请求保留会话 KV 的 streaming-session 实现；[源码](https://github.com/sgl-project/sglang/blob/main/python/sglang/srt/session/streaming_session.py)、[会话控制器](https://github.com/sgl-project/sglang/blob/main/python/sglang/srt/session/session_controller.py) | 这是引擎会话能力，不等同于单独命名的 Realtime 产品；具体模型的增量输入适配与 KV 操作接口须另行核对 |
| SGLang-Omni Realtime API | 官方模型使用文档提供 `--enable-realtime` 与 `/v1/realtime` WebSocket 的交互方式；[官方文档](https://sgl-project.github.io/sglang-omni/basic_usage/qwen3_omni.html) | Realtime 端点与完整原生双工、跨阶段持久状态能力不能画等号；[Full-Duplex Session Infrastructure RFC](https://github.com/sgl-project/sglang-omni/issues/2052) 中仍有进行中的集成工作 |


接口命名参考（2026-09-25 核验）：vLLM v0.23.0 的 [`AsyncLLM`](https://github.com/vllm-project/vllm/blob/v0.23.0/vllm/v1/engine/async_llm.py) 接受 `AsyncGenerator[StreamingInput, None]` 作为流式输入，并在内部按 resumable request 处理；[`StreamingInput`](https://github.com/vllm-project/vllm/blob/v0.23.0/vllm/engine/protocol.py) 是官方输入数据类型。流式引擎接口与基于它构建的 Realtime WebSocket API 是不同接入层次。

执行位置参考（2026-09-25 核验）：[vLLM 架构说明](https://docs.vllm.ai/en/latest/design/arch_overview/)区分 engine core 的请求调度循环与 GPU workers 的模型执行、GPU 内存管理职责；GPU 部署的推理后端包含主机端控制与设备端计算，不能把整个后端等同于一块 GPU memory。

标识来源（2026-09-25 核验）：[vLLM 官方 logo](https://raw.githubusercontent.com/vllm-project/vllm/main/docs/assets/logos/vllm-logo-text-light.png)、[vLLM-Omni 官方 logo](https://raw.githubusercontent.com/vllm-project/vllm-omni/main/docs/source/logos/vllm-omni-logo.png)、[SGLang-Omni 官方 logo](https://raw.githubusercontent.com/sgl-project/sglang-omni/main/docs/_static/image/sgl-omni-logo.svg)、[TensorRT-LLM 官方文档中的 NVIDIA 标识](https://nvidia.github.io/TensorRT-LLM/_static/nvidia-logo-horiz-rgb-blk-for-screen.svg)。vLLM-Omni 是面向多模态模型的推理与服务框架，见[官方仓库](https://github.com/vllm-project/vllm-omni)；TensorRT-LLM 提供推理运行时与优化组件，见[官方仓库](https://github.com/NVIDIA/TensorRT-LLM)。产品及标识本身不证明支持某项跨请求 KV 驻留策略。

## 工作负载来源

| 来源 | 数据或协议性质 | 使用限制 |
| --- | --- | --- |
| Metronome §5 | 音频流与口语问题构成的受控服务实验 | 不能作为真实生产流量的会话分布 |
| LiveServe §7 | 对话负载及模拟打断 | 模拟打断参数不能代替真实用户行为统计 |
| [FLEXI](https://arxiv.org/html/2509.22243v1) | 双工交互行为评测 | 模型行为评分不等于服务容量或真实并发分布 |
| [τ-Voice](https://arxiv.org/abs/2603.13686) | 带模拟用户的语音任务 | 模拟协议与实时服务压力需分别核验 |
| [Full-Duplex-Bench v3](https://arxiv.org/html/2604.04847) | 内容与交互行为评测 | 是否适合作为服务负载需核对输入时序与计量事件 |

这份索引不证明真实流量研究不存在，也不据检索覆盖判断某个研究问题尚无人处理。
