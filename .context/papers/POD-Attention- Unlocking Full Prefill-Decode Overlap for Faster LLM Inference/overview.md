- **Title:** POD-Attention: Unlocking Full Prefill-Decode Overlap for Faster LLM Inference
- **Summary:** POD-Attention fuses prefill and decode attention inside one SM-aware CUDA kernel so hybrid-batched LLM serving can use compute and HBM bandwidth simultaneously, reducing attention time and improving long-context serving throughput and latency.
- **Paper Type:** system
- **Venue:** ASPLOS '25, March 30-April 3, 2025
- **Authors:** Aditya K Kamath (University of Washington), Ramya Prabhu (Microsoft Research), Jayashree Mohan (Microsoft Research), Simon Peter (University of Washington), Ramachandran Ramjee (Microsoft Research), Ashish Panwar (Microsoft Research)
- **Keywords:** LLM inference, attention kernel, hybrid batching, prefill-decode overlap, GPU scheduling, CUDA CTA, FlashAttention, Sarathi-Serve
- ## Quick Reference
    - **Why Read:** Read this paper for a concrete GPU-kernel answer to a systems mismatch: hybrid batching already overlaps phases for linear layers, but attention still runs as serial phase-specialized kernels that waste complementary compute and bandwidth resources at long context.
      claim_kind:: analyst_assessment
      evidence:: E2, E4, E5
    - **Core Idea:** POD-Attention launches one FlashAttention-based fused kernel for a hybrid batch, binds each CTA to prefill or decode after it lands on an SM, and tunes tiles/shared memory/splits so decode uses bandwidth while prefill uses tensor cores.
      evidence:: E8, E9, E10, E11
    - **Mental Model:** Think of each SM as a small heterogeneous engine: place compute-hungry prefill CTAs beside memory-hungry decode CTAs, then let the hardware warp scheduler hide stalls without forcing warp-level or thread-level fusion.
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E8
    - **Key Results:** POD improves attention kernels directly and translates those gains into better offline throughput and online latency under long-context hybrid batching.
      evidence:: E15, E16, E17
        - Hybrid-batch attention sweep on Yi-6B, Llama-2-7B, and Llama-3-8B with 4K-20K contexts and 512-2K chunks; baseline FA_Serial plus FI/streams/HFuse alternatives; metric attention runtime; speedup up to 59%, mean 28%, with no observed slowdown versus serial.
          evidence:: E7, E15
        - Offline 16K-token long-context serving; baseline Sarathi; metric request throughput; Sarathi+POD improves by 22% on Yi-6B, 20% on Llama-2-7B, and 19% on Llama-3-8B, and also beats vLLM by 27%, 13%, and 12%.
          evidence:: E16
        - Online high-load Llama-3-8B; baseline vLLM; metric P99 request latency; Sarathi+POD reduces latency by up to 42% on the internal workload and 17% on arXiv while avoiding vLLM's pervasive 500 ms generation stalls.
          evidence:: E17
    - **Remember the Caveat:** The benefit requires substantial attention time and meaningful hybrid batches; it diminishes in mostly prefill-only or decode-only regimes, and the evidence is primarily A100 plus FlashAttention v2.6.1/Sarathi on three 6B-8B models, with Hopper/FA-3 support left to future work.
      claim_kind:: analyst_assessment
      evidence:: E13, E18
- ## Background and Motivation
    - **Problem:** LLM inference alternates a compute-bound prefill phase with a memory-bandwidth-bound decode phase; hybrid batching helps linear layers, but attention remains computed by separate phase-specialized kernels. This becomes costly for long contexts, where attention can exceed 60% of iteration runtime.
      evidence:: E2, E4
    - **Previous Work:** Prior serving systems use hybrid batching and chunked prefills to piggyback ongoing decodes with new prompt chunks, and they rely on highly optimized attention kernels such as FlashAttention/FlashInfer. Generic GPU concurrency options include streams, CTA-level fusion, warp-level fusion, and intra-thread fusion.
      evidence:: E3, E7, E14
        - Hybrid batching amortizes model-weight reads across prefill and decode tokens and is evaluated through Sarathi/vLLM-style baselines.
          evidence:: E3, E14
        - Existing attention libraries provide strong phase-specific kernels, but the evaluated baselines still execute prefill and decode attention as separate or poorly fused work.
          evidence:: E2, E15
        - Generic concurrency methods expose different tradeoffs: streams are easy, CTA-level fusion load-balances better, and warp/intra-thread fusion gives finer co-location but creates synchronization or straggler issues.
          evidence:: E7
    - **Gaps:** Serial phase-specific attention creates alternating periods of high compute/low bandwidth use and high bandwidth/low compute use. Readily available fusion/concurrency mechanisms fail to guarantee SM-level co-location or are limited by stragglers and CTA barriers.
      evidence:: E5, E7
        - Streams and naive CTA-parallel fusion may improve wave filling, but they do not force prefill and decode work onto the same SM.
          evidence:: E7
        - Warp-parallel fusion can co-locate operations but is vulnerable to stragglers, while intra-thread fusion is blocked by attention's CTA-level synchronization barriers.
          evidence:: E7
- ## Methodology
    - **Approach:** POD-Attention is a single FlashAttention-v2.6.1-derived CUDA kernel for hybrid batches that co-locates prefill and decode CTAs on each SM while minimizing shared-resource contention. It changes kernel scheduling and resource allocation, not the mathematical attention operator.
      evidence:: E8, E4
        - The attention computation remains exact sequence-level attention, Attention(Q,K,V)=softmax(QK^T/scale)V; POD changes placement and overlap of prefill/decode CTAs rather than redefining attention.
          evidence:: E4, E8
        - At the system boundary, Sarathi-Serve still forms hybrid batches; POD replaces the separate attention kernel calls inside those iterations rather than replacing the scheduler or linear layers.
          claim_kind:: analyst_assessment
          evidence:: E3, E8, E14
    - **Key Observation/Insight:** Prefill attention leaves HBM bandwidth mostly unused, while decode attention leaves tensor compute mostly unused. Co-locating them at SM granularity can exploit the hardware warp scheduler without forcing every warp or thread to execute both operations.
      evidence:: E5, E6, E8
        - CTA-level fusion is the chosen middle ground because CTAs can start and finish independently and CTA barriers are local, avoiding the finer-grained fusion pathologies identified in the case study.
          evidence:: E7, E8
    - **Challenges:** The hard part is not simply launching kernels together: CUDA scheduling may place work on different SMs, decode tile sizes can waste tensor-core cycles, and prefill/decode differ in shared-memory and KV-splitting needs. These mismatches can turn fusion into contention unless managed explicitly.
      evidence:: E7, E10, E11
        - Decode attention's small query-sequence dimension makes large prefill-style tiles produce redundant tensor-core work that interferes with co-resident prefills.
          evidence:: E10
        - A fused kernel must allocate one shared-memory shape for all CTAs, and excessive chunked-prefill KV splits can contend with decode for memory bandwidth.
          evidence:: E11, E12
    - **Design:** Before launch, POD computes required prefill and decode CTAs and launches their sum; after hardware placement, each CTA uses SM-aware runtime operation binding to decide which operation and logical CTA id to execute. The wrapper then calls remapped prefill/decode device functions.
      evidence:: E9, E12
        - Scheduling state consists of SM-local tickets/counters plus operation assignment state; the selected operation and logical CTA id are communicated through shared memory to the CTA's threads.
          evidence:: E9
        - Resource tuning uses decode QSL tile length 16, 2-CTA/SM or 4-CTA/SM configurations, virtual warp-sized decode CTAs, and capped prefill KV splits to reduce tensor-core, shared-memory, and bandwidth contention.
          evidence:: E10, E11
        - Implementation mechanics include wrapper device functions that remap CTA IDs and virtual decode CTAs that replace CTA-level barriers with warp-level barriers; the paper reports inference forward attention and does not discuss backward/training mechanics.
          claim_kind:: analyst_assessment
          evidence:: E12
- ## Results
    - **Setup:** Evaluation covers attention microbenchmarks and end-to-end Sarathi-Serve integration on Yi-6B, Llama-2-7B, and Llama-3-8B using one or two A100 80GB GPUs. Serving baselines are original vLLM and Sarathi-Serve, both using FlashAttention v2.6.1 kernels.
      evidence:: E13, E14
        - Offline metric is requests processed per minute for long-context serving; online metrics are TTFT, TBT, request latency, and stall fraction over internal and arXiv workloads with 2K requests and 4K-32K contexts.
          evidence:: E14, E16, E17
        - Reported reproducibility fields include model/GPU mapping, A100 80GB memory, CUDA 12.4, GCC 11.4, Ubuntu 22.04, Python 3.12, and PyTorch 2.4.
          evidence:: E13
        - Not reported in the provided evaluation text: statistical confidence intervals/noise treatment, random seeds for Poisson online arrivals, and numerical error tolerances or output-equivalence tests versus baseline attention kernels.
          claim_kind:: analyst_assessment
    - **Quantitative:** The quantitative story is consistent across kernel and serving levels: POD helps most when attention is a large fraction of runtime and iterations contain both prefill and decode work. The paper reports kernel speed, energy, offline throughput, online latency, and workload-mix sensitivity.
      evidence:: E15, E16, E17, E18
        - Attention-kernel sweep over more than 1000 hybrid batches; baseline FA_Serial plus FI/streams/HFuse alternatives; metric attention runtime; POD speedup is up to 59%, mean 28%, with no observed regression versus serial and energy reduction up to 35% over FA_Serial.
          evidence:: E7, E15
        - Offline 16K-token serving; baseline Sarathi; metric throughput; Sarathi+POD improves by 22% on Yi-6B, 20% on Llama-2-7B, and 19% on Llama-3-8B, and also improves over vLLM by 27%, 13%, and 12%.
          evidence:: E16
        - Online high-load Llama-3-8B; baseline Sarathi for TTFT and vLLM for P99 latency; median TTFT drops to 7.5s internal and 11.74s arXiv, while P99 request latency improves up to 42% internal and 17% arXiv versus vLLM.
          evidence:: E17
    - **Qualitative:** Qualitatively, POD turns Sarathi-style hybrid batching into a full-kernel overlap story: linear layers already share model-weight fetches, and attention now overlaps complementary resource demands instead of serializing them. The serving results also show the expected user-visible tradeoff: Sarathi-like batching reduces stalls, while POD recovers throughput and TTFT.
      claim_kind:: analyst_assessment
      evidence:: E3, E8, E17
        - Energy behavior tracks runtime: POD reduces attention-kernel energy by up to 35% over FA_Serial, with mean reduction 20.5%.
          evidence:: E15
        - Sensitivity evidence supports the mechanism: limited prefill splits and workload mix matter, and gains peak when P:D is 12-18 because most iterations are hybrid.
          evidence:: E11, E18
        - Quality and convergence metrics are not central here because this is exact inference-kernel work, but explicit end-to-end output-equivalence or numerical-drift results would still strengthen the artifact.
          claim_kind:: analyst_assessment
- ## Reflection
    - **Contributions:** The paper contributes an empirical diagnosis of phase-specialized attention underutilization in hybrid batches, an SM-aware CTA-parallel fused attention kernel, and an integration into Sarathi-Serve with serving throughput and latency gains. Its main conceptual move is to make prefill/decode overlap an intra-SM attention-kernel problem rather than only a scheduler problem.
      evidence:: E5, E8, E15, E16, E17
        - The diagnosis is resource-specific: prefill attention underuses bandwidth and decode attention underuses compute, especially when hybrid batches run phase-specific kernels back-to-back.
          evidence:: E5
        - The mechanism combines SM-aware operation binding with resource tuning for tile size, shared memory, CTA occupancy, and KV splitting.
          evidence:: E8, E9, E10, E11
        - The system contribution is end-to-end: POD is integrated into Sarathi-Serve and evaluated against both Sarathi and original vLLM.
          evidence:: E14, E16, E17
    - **Strengths:** The technical fit between problem and mechanism is strong: the design targets the exact failure modes of streams, HFuse, and intra-thread fusion, then validates both microkernel overlap and end-to-end scheduler effects. The paper also reports enough optimization detail to reason about tensor-core, HBM, shared-memory, and synchronization tradeoffs.
      claim_kind:: analyst_assessment
      evidence:: E7, E8, E15, E17
        - Runtime operation binding is robust to unknown hardware scheduling because CTAs choose work only after observing the actual SM they landed on.
          claim_kind:: analyst_assessment
          evidence:: E9
        - The kernel evaluation includes stronger baselines than serial execution alone, including FlashInfer, stream parallelism, and HFuse-style horizontal fusion.
          claim_kind:: analyst_assessment
          evidence:: E7, E15
        - The optimizations make resource tradeoffs explicit: smaller decode tiles reduce redundant tensor-core use, virtual CTAs address shared-memory imbalance, and split caps manage bandwidth contention.
          claim_kind:: analyst_assessment
          evidence:: E10, E11
    - **Weaknesses:** The evidence is narrower than the broad claim of faster LLM inference: online latency is shown for Llama-3-8B, hardware is A100-focused, and Hopper/FA-3 support is explicitly future work. The mechanism is also hand-tuned around FlashAttention/CUDA details rather than presented as a portable compiler/runtime abstraction.
      claim_kind:: analyst_assessment
      evidence:: E13, E17, E18
        - No confidence intervals, variance analysis, or numerical correctness tolerances are reported in the provided text, which makes it harder to separate kernel noise and numerical effects from systems effects.
          claim_kind:: analyst_assessment
        - The design introduces atomics, per-SM counters, tile choices, CTA-count choices, and shared-memory balancing; their individual overheads and portability to substantially different GPU schedulers are not isolated.
          claim_kind:: analyst_assessment
          evidence:: E9, E10, E11
        - Benefits are workload-sensitive and diminish when the workload creates many decode-only or prefill-only iterations rather than hybrid batches.
          claim_kind:: analyst_assessment
          evidence:: E18
    - **Assumptions:** POD assumes a GPU where prefill and decode can profitably share SM resources without destructive contention, and where enough CTAs can be co-resident to create overlap opportunities. It also assumes the serving workload produces hybrid iterations in which attention is nontrivial.
      claim_kind:: analyst_assessment
      evidence:: E6, E8, E10, E18
        - Architectural assumption: CUDA exposes SM identity and supports enough shared memory/register capacity for the selected 2-CTA/SM or 4-CTA/SM fused configurations.
          claim_kind:: analyst_assessment
          evidence:: E6, E9, E11
        - Workload assumption: the request mix must produce hybrid batches with meaningful prefill and decode work; otherwise there is little complementary resource demand to overlap.
          claim_kind:: analyst_assessment
          evidence:: E4, E18
        - Experimental-scope assumption: the reported claims are validated on 6B-8B dense models, A100 80GB GPUs, FlashAttention v2.6.1, and Sarathi/vLLM-style serving.
          claim_kind:: analyst_assessment
          evidence:: E13, E14, E15
    - **Connection to Other Work:** POD differs from prior attention kernels by crossing the prefill/decode boundary instead of further optimizing one phase in isolation, and differs from generic fusion by guaranteeing co-location at SM granularity rather than relying on streams or warp-level lockstep. It is complementary to hybrid-batching schedulers because it optimizes the attention operator inside their iterations.
      claim_kind:: analyst_assessment
      evidence:: E2, E7, E8, E14, E15
        - Compared with FlashAttention/FlashInfer phase-specific baselines, POD keeps tiled exact attention but schedules prefill and decode inside one fused kernel for hybrid batches.
          claim_kind:: analyst_assessment
          evidence:: E2, E8, E15
        - Compared with streams, CTA-parallel fusion, and HFuse-style warp fusion, POD trades genericity for SM-aware runtime operation binding plus attention-specific resource tuning.
          claim_kind:: analyst_assessment
          evidence:: E7, E9, E10
        - Compared with Sarathi/vLLM-style scheduler work, POD is a lower-level kernel substitution that makes the scheduler's hybrid batches efficient for attention as well as linear layers.
          claim_kind:: analyst_assessment
          evidence:: E3, E14, E16, E17
    - **Future Directions:** Natural next steps are broader hardware/kernel backends, automatic tuning of scheduling and tiling policies, and more complete correctness and reproducibility reporting. The most direct paper-stated future item is support for FlashAttention-3 and Hopper.
      claim_kind:: analyst_assessment
      evidence:: E18
        - Paper-stated future work: extend POD-Attention support to FlashAttention-3 and NVIDIA Hopper architecture.
          evidence:: E18
        - Analyst direction: evaluate larger models, more tensor-parallel scales, Hopper-class GPUs, and bursty production traces to test whether the A100/6B-8B conclusions generalize.
          claim_kind:: analyst_assessment
          evidence:: E13, E18
        - Analyst direction: expose or auto-tune CTA ratios, tile sizes, and split caps under changing workload mixes rather than relying only on hand-selected configurations.
          claim_kind:: analyst_assessment
          evidence:: E10, E11, E18
- ## Glossary
  collapsed:: true
    - Prefill: The prompt-processing phase of LLM inference; many tokens are processed in parallel, so it is typically compute-bound and determines time-to-first-token.
    - Decode: The autoregressive generation phase; each request produces one token per iteration and repeatedly reads weights/KV cache, so it is typically memory-bandwidth-bound.
    - Hybrid batching / chunked prefill: Serving strategy that combines a prefill chunk from one request with decode tokens from other requests in the same iteration, amortizing weight reads and reducing generation stalls.
    - SM (Streaming Multiprocessor): GPU execution unit containing warp schedulers, tensor cores, shared memory/L1, and execution units; POD tries to colocate prefill and decode work on each SM.
    - CTA (Cooperative Thread Array): CUDA block-level group of warps guaranteed to run on one SM; POD fuses attention at CTA granularity rather than at warp or thread granularity.
    - QSL tile: Tile length along the query-sequence-length dimension; POD uses a small decode QSL tile of 16 to avoid redundant decode tensor-core work.
    - Runtime operation binding: POD's scheduling trick where a CTA decides whether it will execute prefill or decode only after it observes the SM on which it was scheduled.
    - Virtual decode CTA: A decode CTA subdivided into warp-sized virtual CTAs so decode uses shared memory closer to its real needs while matching the fused kernel's CTA-level allocation constraints.
    - KV-dimension split: FlashDecoding-style parallelization that splits attention across key/value positions; useful for occupancy but can increase memory traffic and contend with decodes in a fused kernel.
    - Wave quantization: GPU underutilization when the number of CTAs is not a multiple of the number of SMs, leaving some SMs idle in the final scheduling wave.
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
