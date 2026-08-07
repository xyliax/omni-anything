# omni-anything

单张 GPU 上同时服务两类负载的 serving 研究。
全双工 (full-duplex) 语音前台按硬 tick 推进：固定周期 T 的硬 deadline 帧，交付晚了就是音频断裂。
后台 agent 的结果注入 (injection) 可以晚几拍落地，但必须无损进入同一条会话的上下文。
两者叠加后稀缺的不是算力而是容量 (capacity-bound)：KV pool 先饱和，算力大量闲置。

候选方案是 KV conveyor：按 tick 时间表把每路会话的尾部 KV 母本 (canonical copy) 从 host DRAM 经 DMA 预取入 HBM 暂存、算完即释放（scheduled tail-KV offloading，谱系为 FlexGen / InfiniGen / vLLM offloading connector / LMCache），等效 KV 容量 = resident M + staging P。

E 系列真机实验跑在 vLLM 0.23 + Qwen2.5-Omni-7B + RTX 3090 (24GB)，tick = 2s，N = 8 concurrent sessions。

工作契约、文档地图与目录边界见 `AGENTS.md`；复现入口 `harness/AGENTS.md`。
