# POD-Attention: Unlocking Full Prefill-Decode Overlap for Faster LLM Inference

## Meta
- **Authors**: Aditya K Kamath, Ramya Prabhu, Jayashree Mohan, Simon Peter, Ramachandran Ramjee, Ashish Panwar (University of Washington, Microsoft Research India)
- **Venue**: ASPLOS 2025
- **Keywords**: LLMs, GPUs, self-attention
- **Open Source**: https://github.com/microsoft/vattention/tree/main/pod_attn

## TL;DR (EN)
POD-Attention is the first GPU kernel that efficiently computes prefill and decode attention concurrently in hybrid batches. It uses SM-aware CTA scheduling to co-locate compute-bound prefill and memory-bound decode operations on the same streaming multiprocessor, achieving up to 59% attention speedup (mean 28%) and up to 22% end-to-end throughput improvement over independently optimized FlashAttention kernels.

## TL;DR (CN)
POD-Attention 是首个在混合批次中高效并行计算 prefill 和 decode 注意力的 GPU 内核。它使用 SM 感知的 CTA 调度将计算密集的 prefill 和内存密集的 decode 操作共置于同一流式多处理器上，实现最高 59% 的注意力加速（平均 28%）和最高 22% 的端到端吞吐提升。

## Problem
Hybrid batching (chunked prefills + ongoing decodes in the same iteration) is standard in LLM serving systems for balancing throughput and latency. While linear operations can be efficiently combined, attention computation uses independently optimized prefill (compute-bound) and decode (memory-bound) kernels executed serially. This creates GPU resource underutilization: prefill kernels leave memory bandwidth idle (<5% utilization), while decode kernels waste compute (<10% utilization). As context lengths grow, attention becomes >60% of iteration runtime, making this inefficiency increasingly costly.

## Key Insight / 核心洞察
Prefill attention is compute-bound while decode attention is memory-bandwidth-bound. When executed serially, neither operation can utilize the resource it doesn't need. By co-locating prefill and decode CTAs on the same SM, both compute (tensor cores) and memory bandwidth can be utilized simultaneously. The key challenge is that CUDA's hardware CTA scheduler provides no guarantee of SM-level co-location. SM-aware scheduling solves this by having CTAs query their SM ID at runtime and decide whether to perform prefill or decode based on what other CTAs on the same SM are doing.

## Method / 方法
- **SM-aware CTA scheduling**: Each CTA reads its SMID hardware counter, atomically increments a per-SM counter to get a "ticket", and decides prefill vs. decode based on a proportional ratio. Ensures co-location without relying on hardware scheduler guarantees.
- **Small decode tile sizes**: Uses QSL tile dimension of 16 (minimum for CUTLASS tensor operations) instead of 64-128, reducing redundant compute from zero-padded decode tiles from ~70% to ~10%, freeing tensor cores for prefill.
- **Virtual decode CTAs**: Splits each decode CTA into warp-level virtual CTAs with separate shared memory allocations, balancing shared memory usage between prefill and decode.
- **Configurable CTAs per SM**: 2 CTAs/SM for prefill-dominant batches (larger tile sizes for prefill), 4 CTAs/SM otherwise (finer-grained scheduling). Auto-selected at runtime.
- **Limiting prefill splits**: Caps FlashDecoding-style KV-dimension splits for chunked prefills to 2 full waves, preventing memory bandwidth contention with decode CTAs.
- Built atop FlashAttention v2.6.1, integrated into Sarathi-Serve.

## Results / 实验结果
- Attention computation: up to 59% faster, mean 28% over FlashAttention serial execution across 1000+ hybrid batch configurations.
- Never underperforms serial execution (unlike FA_HFuse which can be 13% slower due to straggler effect).
- 25% of cases within 10% of theoretical peak speedup (near-perfect overlap).
- Offline throughput: 19-22% improvement over Sarathi-Serve across Yi-6B, Llama-2-7B, Llama-3-8B.
- Online latency (Llama-3-8B): P99 TTFT reduced by up to 4.3x over Sarathi; P99 request latency reduced by up to 42% over vLLM.
- Energy consumption: up to 35% reduction (mean 20.5%) over FA_Serial.
- Peak gains at P:D ratio of 12-18 where most batches are hybrid.

## Limitations / 局限性
- Currently implemented only for A100 GPUs; extending to Hopper architecture (FA-3) is left as future work.
- Benefits diminish for workloads dominated by either prefills (high P:D ratio) or decodes (low P:D ratio), as fewer hybrid batches exist.
- Requires hand-tuning shared memory usage to balance prefill and decode CTA requirements.
- The proportional scheduling policy assumes relatively stable batch compositions; rapidly changing compositions may benefit from adaptive policies.
- Evaluated with models up to 8B parameters on 1-2 GPUs; behavior on larger multi-GPU deployments is not characterized.

## Relevance to MLSys Research
POD-Attention demonstrates that significant performance gains are available by co-designing GPU kernels for the specific workload characteristics of LLM serving (hybrid batches with heterogeneous resource needs). The SM-aware CTA scheduling technique is a general contribution to GPU programming that could benefit other workloads with complementary resource profiles. The work highlights that as context lengths grow, attention optimization becomes critical for LLM serving efficiency, and independently optimized kernels leave substantial performance on the table.
