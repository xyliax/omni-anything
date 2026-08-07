# omni-anything

单张 GPU 上同时服务两类负载的 serving 研究：全双工 (full-duplex) 语音前台的硬 tick deadline 帧，与后台 agent 结果的弹性无损注入 (injection)。稀缺的是 KV 容量而非算力 (capacity-bound)，候选方案是 KV conveyor（scheduled tail-KV offloading）。

工作契约、文档地图与目录边界见 `AGENTS.md`；复现入口 `harness/AGENTS.md`。
