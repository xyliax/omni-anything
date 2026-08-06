- **Title:** Three things everyone should know about Vision Transformers
  **标题:** 人人都应该了解的 Vision Transformer 三件事
- **Summary:** Small, interface-preserving changes to Vision Transformers can trade depth for parallelism, reduce fine-tuning cost, and make patch preprocessing compatible with masked self-supervision without large accuracy loss.
  **一句话总结:** 对 Vision Transformer 做一些保持接口不变的小改动，即可用并行性换取深度、降低微调成本，并使 patch 预处理与掩码自监督兼容，且精度无明显下降。
- **Paper Type:** other
  **论文类型:** 其他
- **Venue:** arXiv preprint 2022
  **发表:** arXiv 预印本 2022
- **Authors:** Hugo Touvron, Matthieu Cord, Alaaeldin El-Nouby, Jakob Verbeek, Hervé Jégou; Meta AI, Sorbonne University, Inria
  **作者:** Hugo Touvron, Matthieu Cord, Alaaeldin El-Nouby, Jakob Verbeek, Hervé Jégou；Meta AI、索邦大学、Inria
- **Keywords:** Vision Transformer, parallel ViT, attention-only fine-tuning, masked image modeling, patch preprocessing, hMLP stem
  **关键词:** Vision Transformer、并行 ViT、仅注意力微调、掩码图像建模、patch 预处理、hMLP stem
- ## Quick Reference
    - **Why Read:** Read this as an empirical Vision Transformer (ViT) design note: it probes three practical gaps in vanilla ViT recipes rather than proposing a new backbone family.
      **阅读价值:** 将其作为一份经验性的 Vision Transformer (ViT) 设计笔记阅读：它探究了 vanilla ViT 方案中的三个实际缺口，而非提出新的骨干网络家族。
      claim_kind:: analyst_assessment
      evidence:: E1
    - **One-Sentence Contribution:** The paper improves practical Vision Transformer (ViT) design, fine-tuning, and masked pretraining by empirically showing that dependencies usually treated as fixed can be decoupled while keeping the vanilla ViT interface.
      **一句话贡献:** 该论文通过实验证明，通常被视为固定的依赖关系可以被解耦，同时保持 vanilla ViT 接口不变，从而改进了 Vision Transformer (ViT) 的设计、微调和掩码预训练。
      evidence:: E1
    - **Mental Model:** Picture a ViT as an assembly line of token updates: this paper asks which stations truly need to wait for the previous one, which stations need retraining for a new job, and how to inspect patches in sealed envelopes before masked prediction.
      **记忆模型:** 把 ViT 想象成一条 token 更新的流水线：本文要问的是，哪些工位确实需要等待前一个工位完成，哪些工位为新的任务需要重新训练，以及如何在掩码预测之前以密封信封的方式检查 patch。
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest support is from controlled ImageNet-1k comparisons where the alternatives differ by one local design choice.
      **最佳证据:** 最有力的证据来自 ImageNet-1k 上的受控对比实验，其中各替代方案仅在一个局部设计选择上有所不同。
      evidence:: E5, E10, E17
        - Supports C1: ImageNet-1k fixed residual-module ViT-B36 and ViT-S60; one-branch sequential baseline; top-1 improves by +0.5 pp for B36 and +0.4 pp for S60 with two branches, with small-batch V100 gains up to 45-47% for B18x2; supported for deep/high-capacity and small-batch cases.
          支持 C1：ImageNet-1k 固定 residual-module 的 ViT-B36 和 ViT-S60；单分支串行基线；双分支时 top-1 分别提升 +0.5 个百分点（B36）和 +0.4 个百分点（S60），小 batch 下 V100 延迟提升最高达 45-47%（B18x2）；在深层/高容量和小 batch 场景下得到支持。
          evidence:: E5, E8
        - Supports C2: ImageNet 224-to-384 fine-tuning; full fine-tuning baseline; ViT-B AdamW top-1 is 84.3 versus 84.3 for attention-only and ViT-L is 85.5 versus 85.5; supported for resolution adaptation, with transfer caveats.
          支持 C2：ImageNet 224 到 384 微调；full fine-tuning 基线；ViT-B AdamW top-1 为 84.3，attention-only 同样为 84.3；ViT-L 为 85.5 对 85.5；在分辨率适配方面得到支持，但迁移存在注意事项。
          evidence:: E10, E12
        - Supports C3: ViT-B12 with BERT pre-training of image transformers (BeiT) plus fine-tuning; linear and convolutional stem baselines; hMLP BN reaches 83.43±0.10 versus 83.05±0.08 linear and 83.04 convolutional; supported with repeated hMLP/linear runs, but conv appears single-seed.
          支持 C3：ViT-B12 采用 BERT pre-training of image transformers (BeiT) 加微调；linear 和 convolutional stem 基线；hMLP BN 达到 83.43±0.10，linear 为 83.05±0.08，convolutional 为 83.04；通过多次 hMLP/linear 运行得到支持，但 conv 似乎为单 seed。
          evidence:: E17
    - **Main Caveat:** The findings are recipe-bound: most experiments use ImageNet-1k, vanilla 16x16-patch ViTs, seed 0 for many tables, and limited V100 latency measurements, so generality to other backbones, training recipes, or deployment kernels is partial.
      **主要边界:** 这些发现受限于训练配方：大多数实验使用 ImageNet-1k、vanilla 16x16-patch ViT，许多表格仅用 seed 0，V100 延迟测量有限，因此对其他 backbone、训练配方或部署 kernel 的通用性仅部分成立。
      claim_kind:: analyst_assessment
      evidence:: E2, E8, E12
- ## Argument Map
    - **Problem and Stakes:** ViTs had become central in vision, but the paper argues that their design and training procedures were still underexplored. The stakes are practical: obtain capacity, cheaper adaptation, and masked-pretraining compatibility without abandoning vanilla ViT structure.
      **问题与重要性:** ViT 已成为视觉领域的核心，但论文认为其设计和训练流程仍探索不足。实际意义在于：在不放弃 vanilla ViT 结构的前提下，获取更大容量、更低成本的适配方式以及与 masked pretraining 的兼容性。
      evidence:: E1, E2
    - **Prior Gap:** The paper targets three empirical blind spots: depth-versus-width tradeoffs for residual ViTs, whether vanilla ViTs need full fine-tuning, and whether patch preprocessing can coexist with masked image modeling when convolutions leak information across patches.
      **已有方法缺口:** 论文聚焦三个经验性盲区：residual ViT 的深度与宽度权衡、vanilla ViT 是否需要 full fine-tuning，以及当卷积跨 patch 泄漏信息时 patch preprocessing 能否与 masked image modeling 共存。
      evidence:: E1, E13
    - **Key Insight:** Across the three studies, the useful move is to relax a dependency while preserving the interface: residual updates need not always be serial, adaptation need not update all weights, and preprocessing must not mix masked and unmasked patches.
      **关键洞见:** 贯穿三项研究的核心思路是在保持接口不变的前提下放松依赖关系：residual 更新不必始终串行，适配不必更新所有权重，而 preprocessing 不得混合 masked 与 unmasked patch。
      claim_kind:: analyst_assessment
      evidence:: E4, E9, E14
    - **Claims:** The paper supports three empirical claims corresponding to its three advertised observations.
      **核心主张:** 论文支持三个经验性 claim，分别对应其三个 advertised observation。
      evidence:: E1
        - C1: Parallelizing pairs of multi-head self-attention (MHSA) and feed-forward network (FFN) residual blocks preserves parameter and FLOP budgets and can match or improve accuracy for sufficiently deep/high-capacity ViTs, with latency gains mainly at small batch sizes.
          将成对的 multi-head self-attention (MHSA) 和 feed-forward network (FFN) residual block 并行化，在保持参数量和 FLOP 预算不变的前提下，对于足够深/高容量的 ViT 可以匹配或提升精度，延迟增益主要出现在小 batch size 下。
          evidence:: E4, E5, E8
        - C2: Updating only MHSA weights is sufficient for resolution fine-tuning and often competitive for transfer, while reducing memory, compute, and storage; the limitation is reduced adaptation capacity on larger transfer datasets for smaller ViTs.
          仅更新 MHSA 权重即可满足分辨率微调需求，且在迁移任务中常具竞争力，同时降低内存、计算和存储开销；其局限在于对较小 ViT 在较大迁移数据集上适配能力下降。
          evidence:: E9, E10, E12
        - C3: A patch-independent hierarchical MLP (hMLP) stem is compatible with BERT pre-training of image transformers (BeiT) masked pretraining and improves BeiT plus fine-tuned ImageNet accuracy over linear or convolutional stems with little compute overhead.
          C3: 一个 patch-independent 的 hierarchical MLP (hMLP) stem 与 BERT pre-training of image transformers (BeiT) 的 masked pretraining 兼容，且在计算开销很小的条件下，相比 linear 或 convolutional stem 提升了 BeiT 加 fine-tuned ImageNet 的准确率。
          evidence:: E14, E15, E17
- ## Mechanism and Design
    - **Core Mechanism:** The paper is not one unified architecture; it is three local rewrites of the ViT computation graph or training graph. Each rewrite keeps the recognizable ViT scaffold so that comparisons against vanilla baselines remain clean.
      **核心机制:** 本文并非一个统一架构；它是对 ViT 计算图或训练图的三处局部改写。每处改写都保留了可辨识的 ViT 框架，使与 vanilla baseline 的对比保持干净。
      evidence:: E4, E9, E14
        - For C1, two same-type residual submodules read the same activation and their outputs are summed, halving serial layer count for the same inventory of residual modules.
          对于 C1，两个同类型 residual submodule 读取同一 activation，其输出相加，在 residual module 总数不变的前提下将串行层数减半。
          evidence:: E4
        - For C2, the forward architecture is unchanged but training updates are restricted to MHSA parameters, leaving FFN-dominated weights frozen and shareable.
          对于 C2，前向架构不变，但训练更新仅限于 MHSA 参数，使 FFN 主导的权重保持冻结且可跨任务共享。
          evidence:: E9, E11
        - For C3, preprocessing is made patch-independent so masked and visible patches cannot exchange information before the masked prediction task.
          对于 C3，预处理被设计为 patch-independent，使 masked patch 与 visible patch 在 masked prediction task 之前无法交换信息。
          evidence:: E13, E14
    - **Data / Control Flow:** Images become 16x16 patch tokens plus the standard class-token ViT path; the interventions change intra-block scheduling, gradient flow, or the patch-stem construction rather than the classifier interface. This makes the experiments mostly controlled at the level of parameter count, FLOPs, or fine-tuned parameter subset.
      **数据/控制流:** 图像变为 16x16 patch token 加上标准的 class-token ViT 路径；这些干预改变的是 block 内调度、梯度流或 patch-stem 构造，而非分类器接口。这使得实验在 parameter count、FLOPs 或 fine-tuned parameter subset 层面上基本受控。
      evidence:: E2, E4, E18
        - Parallel block flow: MHSA branches consume the same input activation and are summed into one residual update; FFN branches then do the analogous summed update.
          Parallel block 流程：MHSA 分支消费同一输入 activation 并相加为一次 residual update；FFN 分支随后执行类似的相加更新。
          evidence:: E4
        - Attention-only fine-tuning flow: inference is unchanged, while optimization computes useful gradients only for MHSA weights and reuses the frozen remainder across tasks or resolutions.
          Attention-only fine-tuning 流程：推理过程不变，优化仅对 MHSA 权重计算有效梯度，并在不同任务或分辨率间复用冻结的其余部分。
          evidence:: E9, E11
        - hMLP flow: non-overlapping convolution-equivalent stages progressively aggregate image regions into 16x16 patch tokens, flatten them, and pass them to the transformer.
          hMLP 流程：non-overlapping 的 convolution-equivalent stage 逐步将图像区域聚合为 16x16 patch token，将其展平后传递给 transformer。
          evidence:: E15, E18
    - **Design Decisions:** The design choices are deliberately minimal: change one dependency, preserve the ViT interface, and compare against the closest vanilla alternative. The tradeoffs are mostly about when a removed dependency was actually useful.
      **设计决策:** 设计选择刻意最小化：只改变一个依赖关系，保留 ViT 接口，并与最接近的 vanilla 替代方案对比。权衡主要在于被移除的依赖在何时实际上是有用的。
      claim_kind:: analyst_assessment
      evidence:: E4, E10, E14
        - Need less serial depth without increasing width; choose residual summation of same-size blocks instead of widening, because width raises quadratic parameter/FLOP and memory costs, but more than two branches and larger batch throughput weaken the benefit.
          需要在不增加宽度的情况下减少串行深度；选择相同尺寸 block 的残差求和而非加宽，因为宽度会带来参数/FLOP 和内存的二次方开销，但超过两个分支以及较大的 batch 吞吐量会削弱该收益。
          evidence:: E4, E5, E8
        - Need cheaper adaptation; choose MHSA-only updates instead of full or FFN-only updates, gaining memory/speed/storage savings but losing capacity on large transfer datasets for smaller ViTs.
          需要更低成本的适配；选择仅更新 MHSA 而非全量更新或仅 FFN 更新，获得内存/速度/存储的节省，但在大型迁移数据集上对较小的 ViT 会损失容量。
          evidence:: E10, E11, E12
        - Need patch preprocessing without masked-token leakage; choose patch-independent hMLP instead of overlapping convolutional stems, with batch normalization (BN) slightly stronger and layer normalization (LN) useful for small batches.
          需要不产生 masked token 泄漏的 patch 预处理；选择 patch 独立的 hMLP 而非重叠的 convolutional stem，其中 batch normalization (BN) 略强，layer normalization (LN) 适用于小 batch。
          evidence:: E13, E14, E17
    - **Implementation Surface:** The implementation surface is small: a block container can execute branch modules sequentially or in parallel, fine-tuning is a parameter-freezing policy, and hMLP is given as a short PyTorch-like stem. The paper does not require a new training objective except when reusing BeiT for masked pretraining.
      **实现边界:** 实现面很小：block 容器可以串行或并行执行分支模块，fine-tuning 是一种参数冻结策略，hMLP 以简短的类 PyTorch stem 形式给出。除复用 BeiT 进行 masked pretraining 外，论文不需要新的训练目标。
      evidence:: E8, E9, E18
        - The reported parallel implementation is simple and suboptimal; the authors explicitly state that specific hardware or kernels are needed for compelling throughput.
          报告的并行实现简单且非最优；作者明确指出需要特定硬件或 kernel 才能获得有说服力的吞吐量。
          evidence:: E8
        - Attention-only fine-tuning is a training-time parameter-selection change, so the resulting model can share the frozen majority of weights across multiple task or resolution variants.
          仅 attention 的 fine-tuning 是训练时的参数选择变更，因此所得模型可以在多个任务或分辨率变体之间共享冻结的大部分权重。
          evidence:: E11
        - The hMLP appendix implements the stem as three non-overlapping Conv2d stages with SyncBatchNorm and GELU before flattening to patch tokens.
          hMLP 附录将 stem 实现为三个非重叠 Conv2d 阶段，使用 SyncBatchNorm 和 GELU，然后展平为 patch tokens。
          evidence:: E18
- ## Evaluation and Evidence
    - **Setup:** Experiments use vanilla ViT-Ti/S/B/L with 16x16 patches, ImageNet-1k validation top-1 and ImageNet-V2 checks, plus transfer to six classification datasets and BeiT-style masked pretraining. Most experiments are reported with seed 0, while selected stem and baseline measurements report standard deviations over repeated runs.
      **实验设置:** 实验使用 vanilla ViT-Ti/S/B/L，patch 大小为 16x16，以 ImageNet-1k 验证集 top-1 和 ImageNet-V2 检查，加上六个分类数据集的迁移以及 BeiT 风格的 masked pretraining。大多数实验以 seed 0 报告，而选定的 stem 和基线测量报告了重复运行的标准差。
      evidence:: E2, E3, E16
    - **Claim-Evidence Matrix:** Evidence is strongest when the paper isolates one mechanism against a direct baseline, and weaker where hardware or transfer-task coverage is narrow. C2 is most cleanly supported for resolution fine-tuning; C1 and C3 are well motivated but more conditional on model size, kernels, and pretraining recipe.
      **主张-证据矩阵:** 当论文将单一机制与直接基线隔离对比时，证据最强；在硬件或迁移任务覆盖面较窄时，证据较弱。C2 在分辨率 fine-tuning 方面得到最干净的支持；C1 和 C3 动机充分但更依赖于模型大小、kernel 和 pretraining recipe。
      claim_kind:: analyst_assessment
      evidence:: E5, E10, E17
        - C1: fixed-block comparisons show two-branch parallel models match or beat sequential variants when optimization is hard, while V100 throughput improves only for small batches.
          C1：固定 block 数的比较表明，当优化困难时，双分支并行模型可匹配或超过串行变体，而 V100 吞吐量仅在小 batch 时有所改善。
          evidence:: E5, E6, E8
        - C2: 384-resolution fine-tuning shows attention-only equals full fine-tuning for ViT-B/L, but transfer experiments show substantial iNaturalist gaps for smaller ViTs.
          C2：384 分辨率微调表明，仅注意力微调在 ViT-B/L 上与全量微调持平，但迁移实验显示较小的 ViT 在 iNaturalist 上存在显著差距。
          evidence:: E10, E12
        - C3: hMLP is competitive with the best supervised convolutional stem while giving the clearest improvement in the BeiT plus fine-tuning setting.
          C3：hMLP 与最佳的有监督卷积 stem 具有竞争力，同时在 BeiT 加微调设置中给出最显著的提升。
          evidence:: E16, E17
    - **Headline Results:** The headline numbers are modest in absolute top-1 points but meaningful because the interventions either keep compute/parameters fixed or reduce trainable state. Missing repeat counts for many architecture and transfer tables should temper interpretation.
      **关键结果:** 核心数值在绝对 top-1 百分比上改善 modest，但因为这些干预措施要么保持计算量/参数量不变，要么减少了可训练状态，所以仍有意义。许多架构和迁移表格缺少重复实验次数，解读结果时需谨慎。
      claim_kind:: analyst_assessment
      evidence:: E5, E10, E17
        - C1 result: ImageNet-1k fixed-module B36, sequential 82.9 versus two-branch 83.4 top-1, delta +0.5 pp; uncertainty not reported and smaller T/S24 models favor sequential variants.
          C1 结果：ImageNet-1k 固定模块 B36，顺序结构 82.9 对双分支 83.4 top-1，差距 +0.5 pp；未报告不确定性，且更小的 T/S24 模型倾向于顺序变体。
          evidence:: E5, E6
        - C2 result: 224-to-384 fine-tuning, full versus attention-only; ViT-B AdamW gives 84.3 versus 84.3 on ImageNet-val and 73.7 versus 74.0 on V2, delta 0.0 and +0.3 pp; repeat count not reported.
          C2 结果：224 到 384 微调，全量对仅注意力；ViT-B AdamW 在 ImageNet-val 上 84.3 对 84.3，在 V2 上 73.7 对 74.0，差距分别为 0.0 和 +0.3 pp；未报告重复次数。
          evidence:: E10
        - C3 result: ViT-B12 BeiT plus fine-tuning, hMLP BN 83.43±0.10 versus linear 83.05±0.08 and convolutional 83.04, delta +0.38 and +0.39 pp; hMLP/linear have repeated-run std, convolutional appears single-seed.
          C3 结果：ViT-B12 BeiT 加微调，hMLP BN 83.43±0.10 对 linear 83.05±0.08 和 convolutional 83.04，差距 +0.38 和 +0.39 pp；hMLP/linear 有多轮重复标准差，convolutional 似为单次种子。
          evidence:: E17
    - **Ablations and Sensitivity:** The paper includes useful one-axis sensitivities: branch count, model width/depth, LayerScale, optimizer and tuned submodule for fine-tuning, and stem type/normalization for patch preprocessing. The ablations reveal that none of the three tricks is uniformly dominant.
      **消融与敏感性:** 论文包含有用的单轴敏感性分析：分支数、模型宽度/深度、LayerScale、优化器及微调时调优的子模块，以及 patch 预处理的 stem 类型/归一化方式。消融实验表明，三个 trick 中没有一个是普遍占优的。
      evidence:: E5, E10, E16
        - C1 sensitivity: more than two branches generally lowers accuracy, shallow/small models can prefer sequential depth, LayerScale narrows sequential-parallel gaps, and latency gains vanish at larger batch sizes.
          C1 敏感性：分支数超过两个通常降低精度，浅层/小模型可能更偏好顺序深度，LayerScale 缩小了顺序与并行之间的差距，且在较大 batch size 下延迟收益消失。
          evidence:: E5, E6, E8
        - C2 sensitivity: both AdamW and SGD show attention-only resolution fine-tuning near full fine-tuning, FFN-only is weaker, and transfer quality depends strongly on dataset size and model capacity.
          C2 敏感性：AdamW 和 SGD 均显示仅注意力分辨率微调接近全量微调，仅 FFN 微调较弱，迁移质量强烈依赖于数据集规模和模型容量。
          evidence:: E10, E12
        - C3 sensitivity: simple BN/GELU changes to a linear stem do not explain hMLP, convolutional stems help supervised accuracy but not BeiT, and hMLP BN is strongest while hMLP LN remains viable.
          C3 敏感性：对线性 stem 做简单的 BN/GELU 改动不足以解释 hMLP 的效果，卷积 stem 有助于有监督精度但对 BeiT 无益，hMLP BN 最强而 hMLP LN 仍然可行。
          evidence:: E16, E17
    - **Reproducibility Gaps:** Reported: public benchmark datasets, seed 0 for the main experimental setting, use of the released BeiT codebase, and PyTorch-like hMLP pseudocode. Not reported: complete experiment scripts/checkpoints, variance for most architecture/transfer/latency tables, exact latency harness details beyond V100 measurements, or custom kernels for the parallel block.
      **可复现性缺口:** 已报告：公开 benchmark 数据集、主实验设置使用 seed 0、采用已发布的 BeiT 代码库、以及类 PyTorch 的 hMLP 伪代码。未报告：完整的实验脚本/checkpoint、大多数 architecture/transfer/latency 表的方差、V100 测量之外的确切 latency harness 细节、或 parallel block 的自定义 kernel。
      claim_kind:: analyst_assessment
      evidence:: E2, E8, E17
- ## Technical Judgment
    - **What Holds Up:** The durable contribution is methodological: make a minimal dependency rewrite and compare against the closest vanilla alternative under matched compute or trainable-state budgets. Attention-only resolution fine-tuning and hMLP for BeiT have the cleanest evidence because the baselines are direct and the deltas align with the hypothesized bottleneck.
      **站得住的结论:** 持久的贡献在于方法论：做一次最小依赖改写，并在匹配的 compute 或 trainable-state 预算下与最近的 vanilla 替代方案对比。Attention-only resolution fine-tuning 与 BeiT 的 hMLP 证据最为干净，因为 baseline 直接，且 delta 与假设的 bottleneck 一致。
      claim_kind:: analyst_assessment
      evidence:: E4, E10, E17
    - **Where It May Fail:** The benefits are falsifiably bounded: parallel ViT weakens for shallow/small models and high-batch throughput, attention-only fine-tuning weakens on large transfer datasets for small ViTs, and hMLP evidence is mainly ViT-B12 plus BeiT on ImageNet-1k. A different backbone, optimizer, masking objective, or optimized kernel could change the tradeoff.
      **可能失效之处:** 收益可证伪地有界：parallel ViT 在 shallow/small 模型与高 batch throughput 下减弱，attention-only fine-tuning 在 small ViT 的大 transfer 数据集上减弱，hMLP 证据主要集中在 ViT-B12 加 BeiT 在 ImageNet-1k 上。不同的 backbone、optimizer、masking objective 或优化后的 kernel 可能改变该 tradeoff。
      claim_kind:: analyst_assessment
      evidence:: E6, E8, E12
    - **Relation to Other Work:** Compared with LayerScale/deeper-ViT work, parallelization changes the residual dependency graph rather than only stabilizing optimization; compared with adapter-style adaptation, MHSA-only fine-tuning reuses existing parameters rather than adding modules; compared with convolutional stems such as LeViT-style preprocessing, hMLP sacrifices cross-patch mixing to preserve masked-patch independence.
      **与已有工作的关系:** 与 LayerScale/deeper-ViT 工作相比，parallelization 改变的是 residual dependency graph 而非仅稳定优化；与 adapter 风格 adaptation 相比，MHSA-only fine-tuning 复用已有参数而非新增模块；与 LeViT 风格 convolutional stem 相比，hMLP 牺牲跨 patch 混合以保持 masked-patch 独立性。
      claim_kind:: analyst_assessment
      evidence:: E6, E9, E13
    - **Transferable Lesson:** When a backbone is modular, first test whether the dependency that blocks efficiency or adaptation is actually necessary. Preserving the external interface and parameter budget turns such tests into clean empirical probes rather than new-architecture confounds.
      **可迁移启发:** 当 backbone 具有模块化结构时，首先测试阻碍效率或 adaptation 的依赖是否真的必要。保持外部接口与参数预算不变，可将此类测试变成干净的实证探针，而非新架构带来的 confound。
      claim_kind:: analyst_assessment
      evidence:: E4, E9, E14
- ## Glossary
  collapsed:: true
    - Vision Transformer: Image model that splits an image into patch tokens and processes them with a transformer; this paper focuses on vanilla ViT with 16x16 patches.
      Vision Transformer：将图像切分为 patch token 并用 transformer 处理的图像模型；本文聚焦于使用 16x16 patch 的 vanilla ViT。
    - Multi-head self-attention: Transformer sublayer that mixes information across tokens; the paper fine-tunes only MHSA weights in its parameter-efficient adaptation experiments.
      Multi-head self-attention：跨 token 混合信息的 transformer 子层；本文在 parameter-efficient adaptation 实验中仅 fine-tune MHSA 权重。
    - Feed-forward network: Per-token transformer sublayer following attention; in ViT it dominates parameter count relative to MHSA and is frozen in attention-only fine-tuning.
      Feed-forward network：attention 之后逐 token 的 transformer 子层；在 ViT 中其参数量相对 MHSA 占主导，并在 attention-only fine-tuning 中被冻结。
    - Parallel ViT notation: The first number is serial depth in pairs of MHSA/FFN layers and the second is the number of parallel branches; total residual-module count is their product.
      Parallel ViT notation：第一个数字是 MHSA/FFN 层对的串行深度，第二个数字是并行分支数；总 residual-module 数为二者乘积。
    - LayerScale: A training stabilization technique for deeper image transformers used as an optimization baseline and sensitivity factor.
      LayerScale：面向更深 image transformer 的训练稳定化技术，本文用作优化 baseline 与 sensitivity factor。
    - BERT pre-training of image transformers: Masked image modeling method used here to test whether patch preprocessing is compatible with BERT-like self-supervised ViT pretraining.
      BERT pre-training of image transformers：此处使用的 Masked image modeling 方法，用于测试 patch 预处理是否与类 BERT 的自监督 ViT 预训练兼容。
    - hierarchical MLP stem: Patch preprocessing module introduced by the paper; it progressively aggregates subpatches with independent linear/nonlinear operations so final 16x16 patches do not communicate before masking.
      hierarchical MLP stem：本文提出的 patch 预处理模块；它通过独立的线性/非线性操作逐步聚合 subpatches，以确保最终的 16x16 patches 在 masking 之前不会进行信息交互。
    - patch masking: Self-supervised setup where some image patches are hidden and predicted; preprocessing that mixes patches can leak masked information.
      patch masking：一种自监督设定，其中部分图像 patches 被隐藏并进行预测；混合 patches 的预处理可能会泄露被 mask 的信息。
    - convolutional stem: Pre-transformer image-processing layers based on convolutions; useful for supervised accuracy but problematic for masked pretraining when overlapping kernels communicate across patches.
      convolutional stem：位于 Transformer 之前的基于卷积的图像处理层；对有监督准确率有帮助，但当重叠的 kernels 跨 patches 通信时，会为 masked pretraining 带来问题。
    - normalization and activation in stems: BN means batch normalization, LN means layer normalization, and GELU is the nonlinearity used in the compared hMLP and convolutional stem variants.
      stems 中的归一化与激活：BN 表示 batch normalization，LN 表示 layer normalization，而 GELU 是所比较的 hMLP 和 convolutional stem 变体中使用的非线性函数。
- ## Evidence Index
  collapsed:: true
    - **E1:** insight/paper_statement | Abstract and Introduction | high
      locator:: Abstract; Sec. 1
      quote:: We offer three insights based on simple and easy to implement variants of vision transformers. The residual layers of vision transformers can to some extent be processed efficiently in parallel; fine-tuning the weights of the attention layers is sufficient; adding MLP-based patch pre-processing layers improves Bert-like self-supervised training.
    - **E2:** experiment_setup/paper_statement | Experimental setting | high
      locator:: Sec. 2.2
      quote:: We consider the vanilla ViT models initially introduced by Dosovitskiy et al. as well as the smaller ones proposed by Touvron et al. We only consider transformers operating on 16x16 patches. Unless specified otherwise, we train our models on ImageNet-1k and evaluate top-1 accuracy. All experiments are carried with seed 0.
    - **E3:** result/experiment_result | Baselines | medium
      locator:: Table 1
      quote:: Baseline models at 224x224 include ViT-Ti/16 with 5.7M parameters and 72.7 validation top-1, ViT-S/16 with 22.1M and 79.7, ViT-B/16 with 86.6M and 82.2, and ViT-L/16 with 304.4M and 83.0 under the 300-epoch setting.
    - **E4:** method/implementation_detail | Parallelizing ViT | high
      locator:: Sec. 3.2
      quote:: Instead of sequentially processing the input in four steps, we replace this composition by two parallel operations. This reduces the number of layers by two for a given number of MHSA and FFN blocks. Conversely, there is twice the amount of processing in parallel. Our modification is neutral with respect to parameter and compute.
    - **E5:** result/experiment_result | Depth vs Width: Parallel ViT | medium
      locator:: Sec. 3.3; Figure 1
      quote:: The best performance is obtained with two parallel branches for all tested model capacities. Using more than two parallel branches is not favorable. Figure 1 reports B36 one/two/three/four branches as 82.9/83.4/82.6/82.4 and S60 as 82.4/82.8/82.7/82.5.
    - **E6:** ablation/experiment_result | Depth vs Width: Parallel ViT | medium
      locator:: Sec. 3.3; Figure 2 and Table 2
      quote:: The smallest models ViT-Ti and ViT-S are better in their sequential version. The B24x1 and B12x2 achieve comparable performance. In contrast, the ViT-L12x2 is stronger than its sequential counterpart. With LayerScale, sequential and parallel models end up approximately on par.
    - **E7:** result/experiment_result | Depth vs Width: Parallel ViT | medium
      locator:: Table 3
      quote:: Table 3 compares complexity-matched variants: B12x1 has 86.6M parameters, 17.6G FLOPS, 2077 MB, and 82.2±0.06 validation top-1; S24x2 has 85.9M, 18.3G, 1433 MB, and 82.6; B18x2 has 256.7M, 52.5G, 3217 MB, and 83.8.
    - **E8:** result/profiling | Depth vs Width: Parallel ViT | medium
      locator:: Table 4; Latency paragraph
      quote:: On V100 GPUs, ViT-B18x2 throughput at batch 1 is 42 images/s sequential versus 61 parallel, a 45% gain; at batch 2, 80 versus 117, a 47% gain; at batch 8, sequential 230 versus parallel 211, best gain 0%. The paper says specific hardware or kernels are required for compelling throughput.
    - **E9:** method/paper_statement | Fine-tuning attention is all you need | high
      locator:: Sec. 4
      quote:: We consider an approach where we only fine-tune the weights corresponding to the MHSA layer. A recent line of work explores adaptation of pre-trained models with various types of adapter modules. In our work, instead, we focus on fine-tuning vanilla ViTs.
    - **E10:** result/experiment_result | Fine-tuning at different resolutions | medium
      locator:: Table 5
      quote:: Table 5 adapts models at resolution 384x384 from 224x224. ViT-B with AdamW: full 84.3, attention 84.3, FFN 84.1 on ImageNet-val; ImageNet-V2: full 73.7, attention 74.0, FFN 73.6. ViT-L AdamW validation: full 85.5, attention 85.5, FFN 85.2.
    - **E11:** result/paper_statement | Fine-tuning at different resolutions | medium
      locator:: Sec. 4; Figure 4 discussion
      quote:: Fine-tuning the MHSA weights only requires 10% less memory on the GPU. The training is also 10% faster, as less gradients are computed. The attention weights correspond to approximately one third of the weights, so each additional model can save 66% of storage.
    - **E12:** result/experiment_result | Fine-tuning on different datasets | medium
      locator:: Table 6
      quote:: Table 6 reports ViT-S full versus attention-only: INAT-18 68.0 versus 60.6, INAT-19 73.9 versus 68.7, CARS 89.7 versus 89.8, Flowers 96.8 versus 96.9. ViT-L full versus attention-only: INAT-18 75.9 versus 75.3, CARS 93.8 versus 93.8, Flowers 98.3 versus 98.4.
    - **E13:** gap/paper_statement | Patch preprocessing for Bert-like self-supervised learning | high
      locator:: Sec. 5
      quote:: Preprocessing images with convolutions is a priori not compatible with mask-based self-supervised learning approaches like BeiT or MAE. The convolutions propagate information across patches, impeding the masked prediction task. The paper says no work addresses compatibility with self-supervised methods based on patch masking.
    - **E14:** method/implementation_detail | Patch preprocessing for Bert-like self-supervised learning | high
      locator:: Sec. 5; Figure 5
      quote:: Our hierarchical MLP stem processes all patches independently with linear layers interleaved with non-linearities and renormalization. Its design removes any interaction between the different 16x16 patches during preprocessing. With hMLP, we can equivalently mask the patches before or after the patch-processing stage.
    - **E15:** implementation/implementation_detail | Patch preprocessing for Bert-like self-supervised learning | high
      locator:: Sec. 5; Figure 5 discussion
      quote:: In short, we start from small 2x2 patches and gradually increase their size until they reach 16x16. The patches are projected with a linear projection and normalized before GELU. ViT-B requires 17.73 GFLOPS with our design, less than 1% extra compute.
    - **E16:** result/experiment_result | Stem comparison in supervised learning | high
      locator:: Table 7
      quote:: Table 7 reports linear ViT-B12 at 17.58 GFLOPS with supervised 82.20±0.06 and V2 71.0; convolutional Graham et al. BN/GELU at 19.07 GFLOPS with supervised 82.57 and V2 71.0; hMLP BN/GELU at 17.73 GFLOPS with supervised 82.54±0.09 and V2 71.5.
    - **E17:** result/experiment_result | Results with BeiT training | high
      locator:: Sec. 5; Table 7
      quote:: The paper uses the code of BeiT with its training procedure; models are pre-trained during 300 epochs and fine-tuned 100 epochs. BeiT+FT ImageNet-val results are linear 83.05±0.08, convolutional Graham et al. 83.04, local transformer 82.38, hMLP BN 83.43±0.10, and hMLP LN 83.24±0.09.
    - **E18:** implementation/implementation_detail | Pytorch code of our hMLP Stem | high
      locator:: Appendix C; Algorithm 1
      quote:: Appendix C pseudocode implements hMLP_stem with Conv2d to embed_dim/4 using kernel_size 4 and stride 4, SyncBatchNorm and GELU, then Conv2d kernel 2 stride 2 with SyncBatchNorm and GELU, then Conv2d to embed_dim kernel 2 stride 2, followed by flatten and transpose.
