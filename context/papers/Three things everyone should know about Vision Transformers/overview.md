- **Title:** Three things everyone should know about Vision Transformers
- **Summary:** Small, interface-preserving changes to Vision Transformers can trade depth for parallelism, reduce fine-tuning cost, and make patch preprocessing compatible with masked self-supervision without large accuracy loss.
- **Paper Type:** other
- **Venue:** arXiv preprint 2022
- **Authors:** Hugo Touvron, Matthieu Cord, Alaaeldin El-Nouby, Jakob Verbeek, Hervé Jégou; Meta AI, Sorbonne University, Inria
- **Keywords:** Vision Transformer, parallel ViT, attention-only fine-tuning, masked image modeling, patch preprocessing, hMLP stem
- ## Quick Reference
    - **Why Read:** Read this as an empirical Vision Transformer (ViT) design note: it probes three practical gaps in vanilla ViT recipes rather than proposing a new backbone family.
      claim_kind:: analyst_assessment
      evidence:: E1
    - **One-Sentence Contribution:** The paper improves practical Vision Transformer (ViT) design, fine-tuning, and masked pretraining by empirically showing that dependencies usually treated as fixed can be decoupled while keeping the vanilla ViT interface.
      evidence:: E1
    - **Mental Model:** Picture a ViT as an assembly line of token updates: this paper asks which stations truly need to wait for the previous one, which stations need retraining for a new job, and how to inspect patches in sealed envelopes before masked prediction.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest support is from controlled ImageNet-1k comparisons where the alternatives differ by one local design choice.
      evidence:: E5, E10, E17
        - Supports C1: ImageNet-1k fixed residual-module ViT-B36 and ViT-S60; one-branch sequential baseline; top-1 improves by +0.5 pp for B36 and +0.4 pp for S60 with two branches, with small-batch V100 gains up to 45-47% for B18x2; supported for deep/high-capacity and small-batch cases.
          evidence:: E5, E8
        - Supports C2: ImageNet 224-to-384 fine-tuning; full fine-tuning baseline; ViT-B AdamW top-1 is 84.3 versus 84.3 for attention-only and ViT-L is 85.5 versus 85.5; supported for resolution adaptation, with transfer caveats.
          evidence:: E10, E12
        - Supports C3: ViT-B12 with BERT pre-training of image transformers (BeiT) plus fine-tuning; linear and convolutional stem baselines; hMLP BN reaches 83.43±0.10 versus 83.05±0.08 linear and 83.04 convolutional; supported with repeated hMLP/linear runs, but conv appears single-seed.
          evidence:: E17
    - **Main Caveat:** The findings are recipe-bound: most experiments use ImageNet-1k, vanilla 16x16-patch ViTs, seed 0 for many tables, and limited V100 latency measurements, so generality to other backbones, training recipes, or deployment kernels is partial.
      claim_kind:: analyst_assessment
      evidence:: E2, E8, E12
- ## Argument Map
    - **Problem and Stakes:** ViTs had become central in vision, but the paper argues that their design and training procedures were still underexplored. The stakes are practical: obtain capacity, cheaper adaptation, and masked-pretraining compatibility without abandoning vanilla ViT structure.
      evidence:: E1, E2
    - **Prior Gap:** The paper targets three empirical blind spots: depth-versus-width tradeoffs for residual ViTs, whether vanilla ViTs need full fine-tuning, and whether patch preprocessing can coexist with masked image modeling when convolutions leak information across patches.
      evidence:: E1, E13
    - **Key Insight:** Across the three studies, the useful move is to relax a dependency while preserving the interface: residual updates need not always be serial, adaptation need not update all weights, and preprocessing must not mix masked and unmasked patches.
      claim_kind:: analyst_assessment
      evidence:: E4, E9, E14
    - **Claims:** The paper supports three empirical claims corresponding to its three advertised observations.
      evidence:: E1
        - C1: Parallelizing pairs of multi-head self-attention (MHSA) and feed-forward network (FFN) residual blocks preserves parameter and FLOP budgets and can match or improve accuracy for sufficiently deep/high-capacity ViTs, with latency gains mainly at small batch sizes.
          evidence:: E4, E5, E8
        - C2: Updating only MHSA weights is sufficient for resolution fine-tuning and often competitive for transfer, while reducing memory, compute, and storage; the limitation is reduced adaptation capacity on larger transfer datasets for smaller ViTs.
          evidence:: E9, E10, E12
        - C3: A patch-independent hierarchical MLP (hMLP) stem is compatible with BERT pre-training of image transformers (BeiT) masked pretraining and improves BeiT plus fine-tuned ImageNet accuracy over linear or convolutional stems with little compute overhead.
          evidence:: E14, E15, E17
- ## Mechanism and Design
    - **Core Mechanism:** The paper is not one unified architecture; it is three local rewrites of the ViT computation graph or training graph. Each rewrite keeps the recognizable ViT scaffold so that comparisons against vanilla baselines remain clean.
      evidence:: E4, E9, E14
        - For C1, two same-type residual submodules read the same activation and their outputs are summed, halving serial layer count for the same inventory of residual modules.
          evidence:: E4
        - For C2, the forward architecture is unchanged but training updates are restricted to MHSA parameters, leaving FFN-dominated weights frozen and shareable.
          evidence:: E9, E11
        - For C3, preprocessing is made patch-independent so masked and visible patches cannot exchange information before the masked prediction task.
          evidence:: E13, E14
    - **Data / Control Flow:** Images become 16x16 patch tokens plus the standard class-token ViT path; the interventions change intra-block scheduling, gradient flow, or the patch-stem construction rather than the classifier interface. This makes the experiments mostly controlled at the level of parameter count, FLOPs, or fine-tuned parameter subset.
      evidence:: E2, E4, E18
        - Parallel block flow: MHSA branches consume the same input activation and are summed into one residual update; FFN branches then do the analogous summed update.
          evidence:: E4
        - Attention-only fine-tuning flow: inference is unchanged, while optimization computes useful gradients only for MHSA weights and reuses the frozen remainder across tasks or resolutions.
          evidence:: E9, E11
        - hMLP flow: non-overlapping convolution-equivalent stages progressively aggregate image regions into 16x16 patch tokens, flatten them, and pass them to the transformer.
          evidence:: E15, E18
    - **Design Decisions:** The design choices are deliberately minimal: change one dependency, preserve the ViT interface, and compare against the closest vanilla alternative. The tradeoffs are mostly about when a removed dependency was actually useful.
      claim_kind:: analyst_assessment
      evidence:: E4, E10, E14
        - Need less serial depth without increasing width; choose residual summation of same-size blocks instead of widening, because width raises quadratic parameter/FLOP and memory costs, but more than two branches and larger batch throughput weaken the benefit.
          evidence:: E4, E5, E8
        - Need cheaper adaptation; choose MHSA-only updates instead of full or FFN-only updates, gaining memory/speed/storage savings but losing capacity on large transfer datasets for smaller ViTs.
          evidence:: E10, E11, E12
        - Need patch preprocessing without masked-token leakage; choose patch-independent hMLP instead of overlapping convolutional stems, with batch normalization (BN) slightly stronger and layer normalization (LN) useful for small batches.
          evidence:: E13, E14, E17
    - **Implementation Surface:** The implementation surface is small: a block container can execute branch modules sequentially or in parallel, fine-tuning is a parameter-freezing policy, and hMLP is given as a short PyTorch-like stem. The paper does not require a new training objective except when reusing BeiT for masked pretraining.
      evidence:: E8, E9, E18
        - The reported parallel implementation is simple and suboptimal; the authors explicitly state that specific hardware or kernels are needed for compelling throughput.
          evidence:: E8
        - Attention-only fine-tuning is a training-time parameter-selection change, so the resulting model can share the frozen majority of weights across multiple task or resolution variants.
          evidence:: E11
        - The hMLP appendix implements the stem as three non-overlapping Conv2d stages with SyncBatchNorm and GELU before flattening to patch tokens.
          evidence:: E18
- ## Evaluation and Evidence
    - **Setup:** Experiments use vanilla ViT-Ti/S/B/L with 16x16 patches, ImageNet-1k validation top-1 and ImageNet-V2 checks, plus transfer to six classification datasets and BeiT-style masked pretraining. Most experiments are reported with seed 0, while selected stem and baseline measurements report standard deviations over repeated runs.
      evidence:: E2, E3, E16
    - **Claim-Evidence Matrix:** Evidence is strongest when the paper isolates one mechanism against a direct baseline, and weaker where hardware or transfer-task coverage is narrow. C2 is most cleanly supported for resolution fine-tuning; C1 and C3 are well motivated but more conditional on model size, kernels, and pretraining recipe.
      claim_kind:: analyst_assessment
      evidence:: E5, E10, E17
        - C1: fixed-block comparisons show two-branch parallel models match or beat sequential variants when optimization is hard, while V100 throughput improves only for small batches.
          evidence:: E5, E6, E8
        - C2: 384-resolution fine-tuning shows attention-only equals full fine-tuning for ViT-B/L, but transfer experiments show substantial iNaturalist gaps for smaller ViTs.
          evidence:: E10, E12
        - C3: hMLP is competitive with the best supervised convolutional stem while giving the clearest improvement in the BeiT plus fine-tuning setting.
          evidence:: E16, E17
    - **Headline Results:** The headline numbers are modest in absolute top-1 points but meaningful because the interventions either keep compute/parameters fixed or reduce trainable state. Missing repeat counts for many architecture and transfer tables should temper interpretation.
      claim_kind:: analyst_assessment
      evidence:: E5, E10, E17
        - C1 result: ImageNet-1k fixed-module B36, sequential 82.9 versus two-branch 83.4 top-1, delta +0.5 pp; uncertainty not reported and smaller T/S24 models favor sequential variants.
          evidence:: E5, E6
        - C2 result: 224-to-384 fine-tuning, full versus attention-only; ViT-B AdamW gives 84.3 versus 84.3 on ImageNet-val and 73.7 versus 74.0 on V2, delta 0.0 and +0.3 pp; repeat count not reported.
          evidence:: E10
        - C3 result: ViT-B12 BeiT plus fine-tuning, hMLP BN 83.43±0.10 versus linear 83.05±0.08 and convolutional 83.04, delta +0.38 and +0.39 pp; hMLP/linear have repeated-run std, convolutional appears single-seed.
          evidence:: E17
    - **Ablations and Sensitivity:** The paper includes useful one-axis sensitivities: branch count, model width/depth, LayerScale, optimizer and tuned submodule for fine-tuning, and stem type/normalization for patch preprocessing. The ablations reveal that none of the three tricks is uniformly dominant.
      evidence:: E5, E10, E16
        - C1 sensitivity: more than two branches generally lowers accuracy, shallow/small models can prefer sequential depth, LayerScale narrows sequential-parallel gaps, and latency gains vanish at larger batch sizes.
          evidence:: E5, E6, E8
        - C2 sensitivity: both AdamW and SGD show attention-only resolution fine-tuning near full fine-tuning, FFN-only is weaker, and transfer quality depends strongly on dataset size and model capacity.
          evidence:: E10, E12
        - C3 sensitivity: simple BN/GELU changes to a linear stem do not explain hMLP, convolutional stems help supervised accuracy but not BeiT, and hMLP BN is strongest while hMLP LN remains viable.
          evidence:: E16, E17
    - **Reproducibility Gaps:** Reported: public benchmark datasets, seed 0 for the main experimental setting, use of the released BeiT codebase, and PyTorch-like hMLP pseudocode. Not reported: complete experiment scripts/checkpoints, variance for most architecture/transfer/latency tables, exact latency harness details beyond V100 measurements, or custom kernels for the parallel block.
      claim_kind:: analyst_assessment
      evidence:: E2, E8, E17
- ## Technical Judgment
    - **What Holds Up:** The durable contribution is methodological: make a minimal dependency rewrite and compare against the closest vanilla alternative under matched compute or trainable-state budgets. Attention-only resolution fine-tuning and hMLP for BeiT have the cleanest evidence because the baselines are direct and the deltas align with the hypothesized bottleneck.
      claim_kind:: analyst_assessment
      evidence:: E4, E10, E17
    - **Where It May Fail:** The benefits are falsifiably bounded: parallel ViT weakens for shallow/small models and high-batch throughput, attention-only fine-tuning weakens on large transfer datasets for small ViTs, and hMLP evidence is mainly ViT-B12 plus BeiT on ImageNet-1k. A different backbone, optimizer, masking objective, or optimized kernel could change the tradeoff.
      claim_kind:: analyst_assessment
      evidence:: E6, E8, E12
    - **Relation to Other Work:** Compared with LayerScale/deeper-ViT work, parallelization changes the residual dependency graph rather than only stabilizing optimization; compared with adapter-style adaptation, MHSA-only fine-tuning reuses existing parameters rather than adding modules; compared with convolutional stems such as LeViT-style preprocessing, hMLP sacrifices cross-patch mixing to preserve masked-patch independence.
      claim_kind:: analyst_assessment
      evidence:: E6, E9, E13
    - **Transferable Lesson:** When a backbone is modular, first test whether the dependency that blocks efficiency or adaptation is actually necessary. Preserving the external interface and parameter budget turns such tests into clean empirical probes rather than new-architecture confounds.
      claim_kind:: analyst_assessment
      evidence:: E4, E9, E14
- ## Glossary
  collapsed:: true
    - Vision Transformer: Image model that splits an image into patch tokens and processes them with a transformer; this paper focuses on vanilla ViT with 16x16 patches.
    - Multi-head self-attention: Transformer sublayer that mixes information across tokens; the paper fine-tunes only MHSA weights in its parameter-efficient adaptation experiments.
    - Feed-forward network: Per-token transformer sublayer following attention; in ViT it dominates parameter count relative to MHSA and is frozen in attention-only fine-tuning.
    - Parallel ViT notation: The first number is serial depth in pairs of MHSA/FFN layers and the second is the number of parallel branches; total residual-module count is their product.
    - LayerScale: A training stabilization technique for deeper image transformers used as an optimization baseline and sensitivity factor.
    - BERT pre-training of image transformers: Masked image modeling method used here to test whether patch preprocessing is compatible with BERT-like self-supervised ViT pretraining.
    - hierarchical MLP stem: Patch preprocessing module introduced by the paper; it progressively aggregates subpatches with independent linear/nonlinear operations so final 16x16 patches do not communicate before masking.
    - patch masking: Self-supervised setup where some image patches are hidden and predicted; preprocessing that mixes patches can leak masked information.
    - convolutional stem: Pre-transformer image-processing layers based on convolutions; useful for supervised accuracy but problematic for masked pretraining when overlapping kernels communicate across patches.
    - normalization and activation in stems: BN means batch normalization, LN means layer normalization, and GELU is the nonlinearity used in the compared hMLP and convolutional stem variants.
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
