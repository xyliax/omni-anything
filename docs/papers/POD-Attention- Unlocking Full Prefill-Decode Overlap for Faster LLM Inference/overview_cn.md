- **标题:** POD-Attention：释放完全的 Prefill-Decode 重叠能力以加速 LLM 推理
- **一句话总结:** POD-Attention 在一个 SM 感知的 CUDA kernel 中融合 prefill 与 decode attention，使 hybrid batching LLM 服务能同时利用计算资源和 HBM 带宽，降低 attention 耗时，提升长上下文服务的吞吐量与延迟表现。
- **论文类型:** 系统
- **发表:** ASPLOS '25, March 30-April 3, 2025
- **作者:** Aditya K Kamath (University of Washington), Ramya Prabhu (Microsoft Research), Jayashree Mohan (Microsoft Research), Simon Peter (University of Washington), Ramachandran Ramjee (Microsoft Research), Ashish Panwar (Microsoft Research)
- **关键词:** LLM inference, attention kernel, hybrid batching, prefill-decode overlap, GPU scheduling, CUDA CTA, FlashAttention, Sarathi-Serve
- ## Quick Reference
    - **阅读价值:** 阅读本文可获得一个具体的 GPU kernel 层面方案来解决系统级不匹配问题：hybrid batching 已能在线性层实现阶段重叠，但 attention 仍以串行的、阶段特化 kernel 运行，在长上下文下浪费了互补的计算与带宽资源。
      claim_kind:: analyst_assessment
      evidence:: E2, E4, E5
    - **核心想法:** POD-Attention 为 hybrid batch 发射一个基于 FlashAttention 的融合 kernel，每个 CTA 落地到 SM 后再绑定为 prefill 或 decode 操作，并针对 tile 大小、shared memory、KV split 进行调优，使 decode 利用带宽而 prefill 利用 tensor core。
      evidence:: E8, E9, E10, E11
    - **记忆模型:** 把每个 SM 想象成一个小型异构引擎：将计算密集的 prefill CTA 与访存密集的 decode CTA 共置，让硬件 warp 调度器隐藏停顿，而无需在 warp 或线程级别做融合。
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E8
    - **关键结果:** POD 直接提升了 attention kernel 性能，并将这些增益转化为长上下文 hybrid batching 场景下更高的离线吞吐量和更低的在线延迟。
      evidence:: E15, E16, E17
        - 在 Yi-6B、Llama-2-7B 和 Llama-3-8B 上进行 hybrid-batch attention 性能扫描，上下文长度 4K-20K，chunk 大小 512-2K；基线为 FA_Serial 及 FI/streams/HFuse 等替代方案；指标为 attention 运行时间；加速最高达 59%，平均 28%，相比串行执行未观察到性能退化。
          evidence:: E7, E15
        - 离线 16K-token 长上下文服务；基线为 Sarathi；指标为请求吞吐量；Sarathi+POD 在 Yi-6B 上提升 22%，在 Llama-2-7B 上提升 20%，在 Llama-3-8B 上提升 19%，同时分别以 27%、13% 和 12% 的优势超越 vLLM。
          evidence:: E16
        - 在线高负载 Llama-3-8B 场景；基线为 vLLM；指标为 P99 请求延迟；Sarathi+POD 在内部工作负载上将延迟降低多达 42%，在 arXiv 数据集上降低 17%，同时避免了 vLLM 普遍存在的 500 ms 生成停顿。
          evidence:: E17
    - **核心边界:** 该收益要求 attention 占据可观的计算时间且存在有意义的 hybrid batch；在几乎纯 prefill 或纯 decode 的场景下收益递减。实验证据主要来自 A100 + FlashAttention v2.6.1/Sarathi 在三个 6B-8B 模型上的结果，Hopper/FA-3 的支持留待未来工作。
      claim_kind:: analyst_assessment
      evidence:: E13, E18
- ## Background and Motivation
    - **问题:** LLM 推理在计算密集型的 prefill 阶段与访存密集型的 decode 阶段之间交替；hybrid batching 有助于线性层，但 attention 仍由各阶段专用的独立 kernel 计算。在长上下文场景中，attention 可占迭代运行时间的 60% 以上，使此问题尤为突出。
      evidence:: E2, E4
    - **已有工作:** 先前的服务系统使用 hybrid batching 和 chunked prefill 将新 prompt chunk 与正在进行的 decode 请求捆绑在同一迭代中处理，并依赖 FlashAttention/FlashInfer 等高度优化的 attention kernel。通用 GPU 并发方案包括 streams、CTA 级融合、warp 级融合和线程内融合。
      evidence:: E3, E7, E14
        - Hybrid batching 通过在 prefill 和 decode token 之间分摊模型权重读取来降低访存开销，并通过 Sarathi/vLLM 风格的基线进行评估。
          evidence:: E3, E14
        - 现有 attention 库提供了强大的阶段专用 kernel，但所评估的基线仍然将 prefill 和 decode attention 作为独立的或融合效果不佳的工作单元执行。
          evidence:: E2, E15
        - 通用并发方法暴露了不同的权衡：streams 实现简单，CTA 级融合具有更好的负载均衡能力，warp/线程内融合提供更精细的 SM 共置但引入同步开销或尾部 CTA 拖尾问题。
          evidence:: E7
    - **不足:** 串行执行阶段专用 attention 会产生交替出现的「高算力/低带宽利用」与「高带宽/低算力利用」时段。现有的融合/并发机制无法保证 SM 级共置，或受限于尾部拖尾和 CTA barrier 问题。
      evidence:: E5, E7
        - Streams 和朴素的 CTA 并行 fusion 可以改善 wave 填充率，但它们无法强制将 prefill 和 decode 工作调度到同一个 SM 上。
          evidence:: E7
        - Warp 级并行 fusion 可以将操作共置，但容易受到落后者（straggler）的影响；而线程内 fusion 则被 attention 的 CTA 级同步屏障所阻断。
          evidence:: E7
- ## Methodology
    - **方法:** POD-Attention 是一个基于 FlashAttention-v2.6.1 衍生的单一 CUDA kernel，面向 hybrid batch 场景，能够在每个 SM 上共置 prefill 和 decode CTA，同时最小化共享资源争用。它改变的是 kernel 调度与资源分配策略，而非 attention 的数学算子本身。
      evidence:: E8, E4
        - Attention 计算保持精确的序列级注意力，$Attention(Q,K,V)=softmax(QK^T/scale)V$；POD 改变的是 prefill/decode CTA 的放置与重叠方式，而非重新定义 attention 运算。
          evidence:: E4, E8
        - 在系统边界上，Sarathi-Serve 仍然负责构造 hybrid batch；POD 替换的是每次迭代内部的 attention kernel 调用，而非替换调度器或线性层。
          claim_kind:: analyst_assessment
          evidence:: E3, E8, E14
    - **核心观察/洞见:** Prefill attention 大量占用算力但 HBM 带宽基本空闲，而 decode attention 大量占用带宽但 tensor core 算力基本空闲。在 SM 粒度上将二者共置，可以利用硬件 warp scheduler 实现资源互补，而无需让每个 warp 或线程同时执行两种操作。
      evidence:: E5, E6, E8
        - CTA 级 fusion 是所选的折中方案：CTA 可以独立启动和结束，CTA barrier 是局部的，从而避免了案例研究中所识别的更细粒度 fusion 的病态问题。
          evidence:: E7, E8
    - **挑战:** 困难之处不在于简单地同时启动 kernel：CUDA 调度器可能将工作分配到不同的 SM 上；decode tile 尺寸可能浪费 tensor core 周期；prefill 和 decode 在 shared memory 需求和 KV 分片策略上存在差异。如果不显式管理，这些不匹配会使 fusion 反而引发资源争用。
      evidence:: E7, E10, E11
        - Decode attention 的 query 序列维度很小，若采用 prefill 风格的大 tile，会产生冗余的 tensor core 计算，干扰共驻在同一 SM 上的 prefill CTA。
          evidence:: E10
        - Fused kernel 必须为所有 CTA 分配统一形状的 shared memory；而 chunked prefill 产生的过多 KV split 会与 decode 争夺内存带宽。
          evidence:: E11, E12
    - **设计:** 在 kernel 启动前，POD 计算所需的 prefill 和 decode CTA 数量并以二者之和发起启动；硬件完成放置后，每个 CTA 利用基于 SM 感知的 runtime operation binding 决定自己执行哪种操作及对应的逻辑 CTA id。随后，wrapper 调用经过重映射的 prefill/decode device 函数。
      evidence:: E9, E12
        - 调度状态由 SM 本地的 ticket/计数器以及操作分配状态组成；所选操作与逻辑 CTA id 通过 shared memory 传递给该 CTA 内的所有线程。
          evidence:: E9
        - 资源调优采用 decode QSL tile 长度 16、2-CTA/SM 或 4-CTA/SM 配置、warp 大小的 virtual decode CTA，以及对 prefill KV split 数量设上限，以降低 tensor core、shared memory 和带宽方面的竞争。
          evidence:: E10, E11
        - 实现机制包括：wrapper device 函数对 CTA ID 进行重映射，virtual decode CTA 用 warp 级 barrier 替换 CTA 级 barrier。论文仅涉及推理阶段的 forward attention，未讨论 backward 及训练相关机制。
          claim_kind:: analyst_assessment
          evidence:: E12
- ## Results
    - **实验设置:** 评估涵盖 attention 微基准测试以及在 Yi-6B、Llama-2-7B 和 Llama-3-8B 上集成 Sarathi-Serve 的端到端实验，使用一块或两块 A100 80GB GPU。Serving 基线为原始 vLLM 和 Sarathi-Serve，均使用 FlashAttention v2.6.1 kernel。
      evidence:: E13, E14
        - 离线指标为长上下文服务场景下的每分钟处理请求数；在线指标包括 TTFT、TBT、请求延迟和 stall 占比，工作负载涵盖内部数据集和 arXiv 数据集，包含 2K 请求、4K–32K 上下文长度。
          evidence:: E14, E16, E17
        - 报告的可复现性信息包括模型/GPU 映射、A100 80GB 显存、CUDA 12.4、GCC 11.4、Ubuntu 22.04、Python 3.12 以及 PyTorch 2.4。
          evidence:: E13
        - 在所提供的评估文本中未报告以下内容：统计置信区间/噪声处理、Poisson 在线到达的随机种子，以及与基线 attention kernel 相比的数值误差容限或输出等价性测试。
          claim_kind:: analyst_assessment
    - **量化结果:** 定量结论在 kernel 层面和 serving 层面保持一致：当 attention 占运行时间比例较大且迭代中同时包含 prefill 与 decode 工作时，POD 的收益最为显著。论文报告了 kernel 速度、能耗、离线吞吐、在线延迟以及对工作负载混合比例的敏感性。
      evidence:: E15, E16, E17, E18
        - 在超过 1000 个 hybrid batch 上进行 attention kernel 扫描；基线为 FA_Serial，对比方案包括 FI/streams/HFuse；指标为 attention 运行时间；POD 加速比最高达 59%，均值 28%，相对于 serial 方式未观察到性能回退，能耗相比 FA_Serial 最多降低 35%。
          evidence:: E7, E15
        - 离线 16K-token 服务场景；基线为 Sarathi；指标为吞吐量；Sarathi+POD 在 Yi-6B 上提升 22%，在 Llama-2-7B 上提升 20%，在 Llama-3-8B 上提升 19%，同时相比 vLLM 分别提升 27%、13% 和 12%。
          evidence:: E16
        - 在线高负载 Llama-3-8B 场景；TTFT 基线为 Sarathi，P99 延迟基线为 vLLM；中位 TTFT 降至 internal 数据集 7.5s、arXiv 数据集 11.74s，P99 请求延迟相比 vLLM 在 internal 数据集上最多改善 42%，在 arXiv 数据集上改善 17%。
          evidence:: E17
    - **定性分析:** 定性来看，POD 将 Sarathi 式 hybrid batching 转化为完整的 kernel 重叠方案：linear 层本身已共享模型权重读取，而 attention 现在通过互补资源需求实现重叠，而非串行执行。服务实验结果也展示了预期的用户可感知权衡：Sarathi 式 batching 减少生成停顿，而 POD 恢复了吞吐量和 TTFT。
      claim_kind:: analyst_assessment
      evidence:: E3, E8, E17
        - 能耗行为与运行时间趋势一致：POD 将 attention kernel 能耗相比 FA_Serial 降低最多 35%，平均降低 20.5%。
          evidence:: E15
        - 敏感性实验支持其机制假设：有限的 prefill 分块数和工作负载混合比例具有显著影响，且收益在 P:D 为 12-18 时达到峰值，因为此时大多数迭代为 hybrid batch。
          evidence:: E11, E18
        - 质量和收敛指标在本文中并非核心关注点，因为这是精确推理 kernel 层面的工作，但显式的端到端输出等价性或数值漂移实验仍会增强论文的可信度。
          claim_kind:: analyst_assessment
- ## Reflection
    - **贡献:** 本文的贡献包括：对 hybrid batch 中分阶段 attention 资源利用不足的经验性诊断、一个 SM 感知的 CTA 并行融合 attention kernel，以及将其集成到 Sarathi-Serve 中并带来服务吞吐量和延迟收益。其核心思想是将 prefill/decode 重叠从单纯的调度器问题转化为 SM 内部的 attention kernel 问题。
      evidence:: E5, E8, E15, E16, E17
        - 该诊断具有资源针对性：prefill attention 带宽利用不足，decode attention 算力利用不足，尤其在 hybrid batch 中分阶段 kernel 背靠背串行执行时更为显著。
          evidence:: E5
        - 其机制将 SM 感知的 runtime operation binding 与 tile 大小、shared memory、CTA occupancy 和 KV-dimension split 的资源调优相结合。
          evidence:: E8, E9, E10, E11
        - 系统层面的贡献是端到端的：POD 被集成到 Sarathi-Serve 中，并同时与 Sarathi 和原始 vLLM 进行了对比评测。
          evidence:: E14, E16, E17
    - **优点:** 问题与机制之间的技术契合度很高：设计精准针对 streams、HFuse 和线程内融合的失败模式，并同时验证了微内核重叠效果和端到端调度器效应。论文还报告了足够的优化细节，使读者可以推理 tensor-core、HBM、shared memory 和同步方面的权衡。
      claim_kind:: analyst_assessment
      evidence:: E7, E8, E15, E17
        - Runtime operation binding 对未知的硬件调度具有鲁棒性，因为 CTA 只在观察到自己实际落在哪个 SM 上之后才选择工作。
          claim_kind:: analyst_assessment
          evidence:: E9
        - Kernel 层面的评估包含了比单纯串行执行更强的 baseline，包括 FlashInfer、stream 并行以及 HFuse 风格的水平融合。
          claim_kind:: analyst_assessment
          evidence:: E7, E15
        - 优化措施将资源权衡显式化：较小的 decode tile 减少了冗余的 tensor-core 运算，virtual CTA 解决了 shared memory 分配不均的问题，split 上限则管理了带宽争用。
          claim_kind:: analyst_assessment
          evidence:: E10, E11
    - **缺点:** 证据的覆盖面窄于「加速 LLM 推理」这一宽泛声明：在线延迟仅在 Llama-3-8B 上展示，硬件以 A100 为主，Hopper/FA-3 支持被明确列为未来工作。此外，该机制是围绕 FlashAttention/CUDA 细节手动调优的，而非作为可移植的编译器/运行时抽象来呈现。
      claim_kind:: analyst_assessment
      evidence:: E13, E17, E18
        - 论文提供的内容中未报告置信区间、方差分析或数值正确性容差，这使得区分 kernel 噪声、数值效应与系统效应变得更加困难。
          claim_kind:: analyst_assessment
        - 设计引入了 atomics、per-SM 计数器、tile 选择、CTA 数量选择和 shared memory 平衡等机制；这些各自的开销以及在差异较大的 GPU 调度器上的可移植性未被单独隔离分析。
          claim_kind:: analyst_assessment
          evidence:: E9, E10, E11
        - 收益对工作负载敏感，当工作负载产生大量仅含 decode 或仅含 prefill 的迭代（而非混合批次）时，收益会减小。
          claim_kind:: analyst_assessment
          evidence:: E18
    - **假设:** POD 假设 GPU 上 prefill 和 decode 可以在不产生破坏性争用的情况下有效共享 SM 资源，并且有足够多的 CTA 可以共驻以创造重叠机会。它还假设服务工作负载会产生 attention 开销不可忽略的混合迭代。
      claim_kind:: analyst_assessment
      evidence:: E6, E8, E10, E18
        - 架构假设：CUDA 暴露 SM 标识，并支持足够的 shared memory/寄存器容量以运行所选的 2-CTA/SM 或 4-CTA/SM 融合配置。
          claim_kind:: analyst_assessment
          evidence:: E6, E9, E11
        - 工作负载假设：请求混合必须产生具有有意义的 prefill 和 decode 工作量的 hybrid batch；否则缺乏互补的资源需求可供重叠利用。
          claim_kind:: analyst_assessment
          evidence:: E4, E18
        - 实验范围假设：所报告的结论在 6B-8B dense 模型、A100 80GB GPU、FlashAttention v2.6.1 以及 Sarathi/vLLM 风格的 serving 系统上得到验证。
          claim_kind:: analyst_assessment
          evidence:: E13, E14, E15
    - **与其他工作的关系:** POD 与先前 attention kernel 的区别在于跨越了 prefill/decode 的边界，而非孤立地进一步优化单一阶段；与通用 fusion 方案的区别在于以 SM 粒度保证 co-location，而非依赖 streams 或 warp 级锁步。它与 hybrid-batching scheduler 互补，因为它优化的是 scheduler 每次迭代内部的 attention 算子。
      claim_kind:: analyst_assessment
      evidence:: E2, E7, E8, E14, E15
        - 与 FlashAttention/FlashInfer 等针对单一阶段的 baseline 相比，POD 保持了 tiled exact attention，但在 hybrid batch 中将 prefill 和 decode 调度到同一个 fused kernel 内执行。
          claim_kind:: analyst_assessment
          evidence:: E2, E8, E15
        - 与 streams、CTA-parallel fusion 以及 HFuse 风格的 warp fusion 相比，POD 以牺牲通用性为代价，换取 SM 感知的 runtime operation binding 以及针对 attention 的资源调优。
          claim_kind:: analyst_assessment
          evidence:: E7, E9, E10
        - 与 Sarathi/vLLM 风格的 scheduler 工作相比，POD 是更底层的 kernel 替换，使 scheduler 构建的 hybrid batch 在 attention 层面（而不仅仅是线性层）也能高效执行。
          claim_kind:: analyst_assessment
          evidence:: E3, E14, E16, E17
    - **未来方向:** 自然的后续方向包括更广泛的硬件/kernel 后端支持、调度与 tiling 策略的自动调优，以及更完善的正确性与可复现性报告。论文最直接提出的未来工作是支持 FlashAttention-3 与 Hopper 架构。
      claim_kind:: analyst_assessment
      evidence:: E18
        - 论文明确提出的未来工作：将 POD-Attention 扩展到 FlashAttention-3 和 NVIDIA Hopper 架构。
          evidence:: E18
        - 分析者建议方向：在更大模型、更多 tensor-parallel 规模、Hopper 级 GPU 以及突发性生产 trace 上评估，以检验 A100/6B-8B 条件下的结论是否具有普适性。
          claim_kind:: analyst_assessment
          evidence:: E13, E18
        - 分析者建议方向：在变化的工作负载混合下暴露或自动调优 CTA 比例、tile 大小及 split 上限，而非仅依赖手工选定的配置。
          claim_kind:: analyst_assessment
          evidence:: E10, E11, E18
- ## Glossary
  collapsed:: true
    - Prefill：LLM 推理中的提示词处理阶段；大量 token 被并行处理，因此通常受计算能力限制，决定了 time-to-first-token。
    - Decode：自回归生成阶段；每个请求在每次迭代中只产生一个 token，需要反复读取权重和 KV cache，因此通常受显存带宽限制。
    - Hybrid batching / chunked prefill：一种服务策略，将一个请求的 prefill 分块与其他请求的 decode token 合并在同一次迭代中处理，从而摊销权重读取开销并减少生成停顿。
    - SM (Streaming Multiprocessor)：GPU 执行单元，包含 warp 调度器、tensor core、shared memory/L1 以及执行单元；POD 尝试将 prefill 和 decode 工作共置于同一 SM 上。
    - CTA (Cooperative Thread Array)：CUDA block 级别的 warp 组，保证在同一个 SM 上运行；POD 在 CTA 粒度而非 warp 或线程粒度上融合 attention 计算。
    - QSL tile：query-sequence-length 维度上的分块长度；POD 使用较小的 decode QSL tile（大小为 16），以避免 decode 阶段冗余的 tensor core 计算。
    - Runtime operation binding：POD 的调度技巧——CTA 在观察到自身被调度到哪个 SM 之后，才决定执行 prefill 还是 decode 操作。
    - Virtual decode CTA：将一个 decode CTA 细分为 warp 大小的虚拟 CTA，使 decode 实际使用的 shared memory 更接近其真实需求，同时满足融合 kernel 中 CTA 级别的资源分配约束。
    - KV-dimension split：FlashDecoding 风格的并行化方法，沿 key/value 位置维度拆分 attention 计算；有助于提高占用率，但可能增加显存访问量，并在融合 kernel 中与 decode 操作产生资源竞争。
    - Wave quantization：当 CTA 数量不是 SM 数量的整数倍时，最后一个调度 wave 中部分 SM 处于空闲状态，导致 GPU 利用率下降。
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata | ACM Reference Format | high
      locator:: front matter
      quote:: Aditya K Kamath, Ramya Prabhu, Jayashree Mohan, Simon Peter, Ramachandran Ramjee, and Ashish Panwar. 2025. POD-Attention: Unlocking Full Prefill-Decode Overlap for Faster LLM Inference. In Proceedings of the 30th ACM International Conference on Architectural Support for Progra...
    - **E2:** problem | Abstract | high
      locator:: abstract
      quote:: Each request in LLM inference goes through two phases: compute-bound prefill and memory-bandwidth-bound decode. To improve GPU utilization, recent systems use hybrid batching that combines the prefill and decode phases of different requests into the same batch. This approach o...
    - **E3:** prior_work | Introduction and Section 2.1 | high
      locator:: hybrid batching motivation
      quote:: Hybrid batching avoids the need to fetch model weights from GPU high-bandwidth memory separately for prefill and decode tokens. Instead, it allows the GPU to fetch model weights once and use them to compute over both prefill and decode inputs... chunked-prefills... combine ong...
    - **E4:** formula | Section 2.1 Large Language Model Inference | high
      locator:: attention formula and Figure 4 discussion
      quote:: attention is a sequence-level operator that is computed between three representations Q, K, V as: Attention(Q,K,V)=softmax(QK^T/scale)V... as the context length increases, attention computation dominates, becoming more than 60% of the total inference time in many cases as show...
    - **E5:** insight | Introduction | high
      locator:: Figure 1 discussion
      quote:: Figure 1 illustrates that memory bandwidth utilization of the prefill attention kernel is often below 5%, while compute utilization of the decode attention kernel is under 10%. The effect of using independently optimized kernels is particularly noticeable with hybrid batching...
    - **E6:** system_design | Section 2.2 GPU Execution Model | high
      locator:: CTA and scheduler paragraphs
      quote:: A Cooperative Thread Array (CTA) is a group of warps that share the L1 cache and shared memory. All warps in a CTA are guaranteed to execute within a single SM... The CTA scheduler selects CTAs from streams and assigns them to SMs when sufficient execution resources are availa...
    - **E7:** gap | Section 3.1 Methods of Concurrent Execution | high
      locator:: Table 2 discussion
      quote:: Streams alone guarantees neither concurrency nor SM-level co-location... CTA-parallel does not guarantee SM-level co-location. Warp-parallel fusion suffers from the straggler problem... attention kernels use CTA-level sync barriers to coordinate fetching data into shared memor...
    - **E8:** method | Section 4 POD-Attention | high
      locator:: opening paragraphs
      quote:: We introduce POD-Attention - a single GPU kernel that efficiently computes both prefill and decode attention... We build our kernel atop FA v2.6.1. Our primary goal is to ensure that each GPU SM computes both operations simultaneously while minimizing resource contention betwe...
    - **E9:** algorithm | Section 4.1 SM-aware CTA Scheduling | high
      locator:: runtime operation binding and Figure 9
      quote:: SM-aware CTA scheduling co-locates prefill and decode CTAs through runtime operation binding... Before launching the kernel, we determine how many CTAs are required for prefill and decode independently, and launch the kernel with CTAs matching the sum of both. When a CTA is sc...
    - **E10:** implementation | Section 4.2.1 Tile Sizes | high
      locator:: decode tile discussion and Figure 10
      quote:: In a fused kernel, any redundant compute performed by decodes interferes with co-located prefills since tensor cores are shared between them... we use a decode tile length of 16 for QSL, the minimum needed by CUTLASS for A100 tensor operations. This drops the compute utilizati...
    - **E11:** implementation | Section 4.2.2-4.2.4 Performance Optimizations | high
      locator:: CTA configs, virtual CTAs, limiting splits
      quote:: POD-Attention supports two configurations: 2 CTAs per SM for prefill-dominant hybrid batches and 4 CTAs per SM otherwise... To avoid over-allocating shared memory to decodes, we divide each decode CTA into virtual CTAs containing a warp of threads... we limit the number of spl...
    - **E12:** implementation | Section 4.3 Implementing CTA-parallel Fusion | high
      locator:: wrapper kernel and virtual CTA implementation
      quote:: To fuse the two kernels, we first convert them into generic device functions callable from within GPU code while removing all references to the CUDA-provided CTA ID... We build a wrapper kernel that calls these different functions using a calculated CTA ID... To implement virt...
    - **E13:** experiment_setup | Section 5 Evaluation and Appendix A.2 | high
      locator:: models/environment and artifact checklist
      quote:: We evaluate POD-Attention with Yi-6B, Llama-2-7B and Llama-3-8B, deploying Yi-6B on one A100 GPU, and others on two A100 GPUs with tensor parallelism... Each GPU has 80 GB HBM memory. Artifact check-list: Compilation: CUDA 12.4, GCC 11.4; run-time environment: Ubuntu 22.04, CU...
    - **E14:** experiment_setup | Section 5 Evaluation | high
      locator:: workloads, metrics, serving baselines
      quote:: We evaluate both offline and online inference scenarios. For offline inference, we report the number of requests processed per minute. For online inference, we report TTFT, TBT and request execution latency on two workloads consisting of 2K requests each, and context length ra...
    - **E15:** result | Section 5.1 Evaluating Attention Computation | high
      locator:: Figure 11 and energy paragraph
      quote:: we conducted a comprehensive sweep across over a thousand hybrid batches... context length from 4K to 20K and the prefill chunk size from 512 to 2K. In addition to FlashAttention kernels, we also compare the runtime of FlashInfer... POD-Attention reaches a peak speedup of 59%,...
    - **E16:** result | Section 5.2 Evaluating Throughput in Offline Inference | high
      locator:: Figure 12
      quote:: For evaluating offline inference scenarios, we run long context requests of 16K tokens each... Figure 12 shows that Sarathi+POD delivers the best throughput: 22%, 20% and 19% higher than Sarathi, and 27%, 13% and 12% higher than vLLM, for the three models.
    - **E17:** result | Section 5.3 Evaluating Latency in Online Inference | high
      locator:: Tables 5 and 6
      quote:: TTFT in Sarathi further increases with the load... median TTFT goes to 25.4 and 46.2 seconds for internal and arXiv-based workloads... Sarathi+POD significantly reduces TTFT over Sarathi, bringing median TTFT down to 7.5 and 11.74 seconds at higher load. Even if the TBT SLO is...
    - **E18:** limitation | Section 5.4 Sensitivity Studies and Section 6 Related Work | high
      locator:: Figure 15 and FA-3 paragraph
      quote:: The peak gains occur in the P:D range of 12 to 18 because most batches are hybrid batches... many iterations run decode-only batches when P:D ratio is lower than 12 or prefill-only batches when P:D ratio is higher than 18. FA-3 was under active development... we leave extendin...
