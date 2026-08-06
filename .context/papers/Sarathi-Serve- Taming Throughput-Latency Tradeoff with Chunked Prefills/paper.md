# SARATHI / Sarathi-Serve Complete Text Extracts

Extraction date: 2026-07-12

This file contains text-layer extracts of both papers requested for the StreamingRL prior-art audit. Text is preserved in PDF reading order; figure and table captions are included when present in the PDF text layer, while image pixels are not reproduced. PDF page transitions are marked with HTML comments.

## Part I: SARATHI Mechanism Prototype

- Title: `SARATHI: Efficient LLM Inference by Piggybacking Decodes with Chunked Prefills`
- Source: arXiv:2308.16369v1, submitted 2023-08-31
- Landing page: https://arxiv.org/abs/2308.16369v1
- PDF: https://arxiv.org/pdf/2308.16369v1

S ARATHI: Efficient LLM Inference by Piggybacking Decodes with Chunked Prefills
Amey Agrawal* 2 , Ashish Panwar1 , Jayashree Mohan1 , Nipun Kwatra1 , Bhargav S. Gulavani1 , and
Ramachandran Ramjee1
1 Microsoft Research India

arXiv:2308.16369v1 [cs.LG] 31 Aug 2023

2 Georgia Institute of Technology

Abstract
Large Language Model (LLM) inference consists of two
distinct phases – prefill phase which processes the input
prompt and decode phase which generates output tokens autoregressively. While the prefill phase effectively saturates
GPU compute at small batch sizes, the decode phase results
in low compute utilization as it generates one token at a
time per request. The varying prefill and decode times also
lead to imbalance across micro-batches when using pipelineparallelism, resulting in further inefficiency due to bubbles.
We present S ARATHI to address these challenges. S ARATHI
employs chunked-prefills, which splits a prefill request into
equal sized chunks, and decode-maximal batching, which constructs a batch using a single prefill chunk and populates the
remaining slots with decodes. During inference, the prefill
chunk saturates GPU compute, while the decode requests ‘piggyback’ and cost up to an order of magnitude less compared
to a decode-only batch. Chunked-prefills allows constructing multiple decode-maximal batches from a single prefill
request, maximizing coverage of decodes that can piggyback.
Furthermore, the uniform compute design of these batches
ameliorates the imbalance between micro-batches, significantly reducing pipeline bubbles.
Our techniques yield significant improvements in inference performance across models and hardware. For the
LLaMA-13B model on A6000 GPU, S ARATHI improves decode throughput by up to 10×, and accelerates end-to-end
throughput by up to 1.33×. For LLaMa-33B on A100 GPU,
we achieve 1.25× higher end-to-end-throughput and up to
4.25× higher decode throughput. When used with pipeline
parallelism on GPT-3, S ARATHI reduces bubbles by 6.29×,
resulting in an end-to-end throughput improvement of 1.91×.

1

Figure 1: Example two-stage pipeline parallel schedule. (a)
In prior solutions like Orca [48], pipeline bubbles are common
due to varying prompt and decode compute times. Further,
decodes are highly inefficient (decode cost-per-token is orderof-magnitude higher than Prefill). (b) S ARATHI significantly
reduces pipeline bubbles and enables more efficient piggybacked decodes.

usage across applications spanning conversational engines [2,
4, 5, 38], search [3, 8, 9, 15, 22], code assistants [1, 7, 16], etc.
The significant GPU compute required for inference on these
large models, coupled with their widespread usage, has made
LLM inference the dominant GPU workload. Optimizing
LLM inference has thus become very important and has seen
significant interest recently [39, 42, 48].
In this paper, we first analyze a fundamental reason behind
the low efficiency of LLM inference. Each LLM inference
request goes through two phases – a prefill phase corresponding to the processing of the input prompt and a decode phase
which corresponds to the autoregressive token generation.
The prefill phase processes all tokens in the input sequence
in parallel, leading to high GPU utilization even with a small
batch size. For example, on an A6000 GPU, for the LLaMA13B model, a prefill with a sequence length of 512 tokens

Introduction

The scaling up of language models [25, 26, 35, 38] has led to
an emergence in their abilities [45] in a variety of complex
tasks — natural language processing, question answering,
code generation, etc. This has led to an explosion in their
* Work done as intern at Microsoft Research India

1



<!-- PDF page break -->

saturates GPU compute even at a batch size of just one. The
decode phase, on the other hand, processes only a single token in each autoregressive pass, resulting in very low GPU
utilization at low batch sizes. For example, our experiments
reveal that, at small batch sizes, the decode cost per token can
be as high as ∼ 200 times the prefill cost per token. Moreover,
since a request goes through only a single prefill pass, but
multiple decode passes (one for each generated token), the
overall inference efficiency is significantly impacted.
One strategy to improve LLM decode efficiency is to increase batch size using model parallelism. In servers with
high bandwidth connectivity such as NVIDIA DGX A100,
tensor-parallelism [43] can enable deployment of an LLM
on up to 8 GPUs, thereby supporting large batch sizes and
efficient decode. Pope et al. [39] show that tensor parallelism
can be scaled up to 256 devices on specialized TPUv4 pods.
However, tensor-parallelism at such a large scale can result
in poor performance when hyper-clusters are unavailable. In
such cases, pipeline parallelism [24, 37] can help increase
batch size. Thus, systems like Orca [48] rely on pipeline parallelism to scale LLM inference and adopt the well-known
solution of using micro-batches to mitigate pipeline stalls or
bubbles [34]. However, as we show in this paper, the standard micro-batch-based scheduling can still lead to pipeline
bubbles due to the unique characteristics of LLM inference.
Specifically, LLM inference consists of a mixture of varying
length prefills and decodes. This creates varying processing
times for the different micro-batches, resulting in significant
bubbles and wasted GPU-cycles as illustrated in Figure 1(a).
Note that the first bubble in the figure is due to varying prompt
sizes while the second bubble is due to mismatch between
prompt and decode compute times.
In this paper, we present the design and implementation of
S ARATHI, an efficient LLM inference technique. S ARATHI
uses chunked-prefills and decode-maximal batching to address
the problems of 1) inefficient decodes and 2) pipeline bubbles.
Chunked-prefills splits a prefill request into equal computesized chunks. Further, S ARATHI uses decode-maximal batching to construct a batch by using a single prefill chunk and
filling the remaining batch with decodes. This hybrid batch
provides units of work that are both compute saturating and
uniform, thereby addressing the problems of inefficient decodes and pipeline bubbles.
Since prefill and decode phases have different compute
requirements, the key insight of our method is that mixing
prefill and decode requests in a single batch can enable uniformly high compute utilization. However, since each request
has only a single prefill phase, followed by multiple decode
phases (for each generated token), we will not have enough
prefill requests to be able to always create a hybrid batch of
prefills and decodes. Chunked-prefills allows us to construct
multiple hybrid batches from a single prefill request, thereby
increasing the coverage of decodes that can piggyback with a
prefill. In our hybrid batch, the single prefill chunk ensures

high GPU utilization, while the decode phase requests ‘piggyback’ along. Given an average prefill-to-decode token ratio
for an LLM application, we select a prefill chunk size that
maximizes the overall performance.
The hybrid batches constructed in S ARATHI have a uniform compute requirement. Thus, when used with pipeline
parallelism, S ARATHI ensures that the micro-batches are well
balanced, which results in a significant reduction in pipeline
bubbles as shown in Figure 1(b).
We evaluate S ARATHI across different models and hardware — LLaMA-13B on A6000 GPU, LLaMA-33B on A100
GPU, and GPT-3 with 8-way pipeline and 8-way tensor
parallelism across a simulated cluster of 64 A100 GPUs.
For LLaMA-13B on A6000, S ARATHI improves decode
throughput by up to 10× and results in up to 1.33× endto-end throughput improvement. Similarly, for LLaMA-33B
on A100, our decode throughput improves by 4.25×, and results in a 1.25× end-to-end throughput improvement. When
used with pipeline parallelism, S ARATHI reduces bubbles by
6.29×, resulting in end-to-end speedup of 1.91×.
The main contributions of our paper include:
1. Chunked-prefills which allows the construction of work
units that are compute saturating and uniform.
2. Decode-maximal batching which allows inefficient decodes to ‘piggyback’ with efficient prefills.
3. Application of chunked-prefills and decode-maximal
batching to pipeline parallelism to significantly reduce
pipeline bubbles.
4. Extensive evaluation over multiple models, hardware,
and parallelism strategies demonstrating up to 1.91×
improvement in throughput.

2

Background

We first give an overview of the transformer architecture,
followed by a brief discussion of the two phases of LLM
inference, and pipeline parallelism.

2.1

The Transformer architecture

Figure 2 shows the architecture of a transformer decoder
block. Each decoder block consists of two primary modules:
self-attention and feed-forward network (FFN). These modules can be divided into the following six operations: preproj, attn, postproj (within the attention module), and ffn_ln1,
ffn_ln2 (within FFN) and others (e.g., layer normalization,
activation functions, residual connections etc.).

2.2

The prefill and decode phases

Transformer inference begins with the prefill phase that processes all the input tokens of a given batch in parallel. In
this phase, the input to a transformer block is a tensor X of
shape [B, L, H] where B denotes the batch size, L denotes the
2



<!-- PDF page break -->

Add

Decoder
Block

Dropout

Attention

FFN

WO[H->H]

Layer Norm

Concat
Self Attention
Q

Add
Attention

K

Layer Norm

WQ,K,V [H->3H]

(a)

(b)

FFN

Operation
preproj
attn
postproj
ffn_ln1
ffn_ln2

Dropout

W [H2->H]
V

GeLU

W [H->H2]

Table 1: Shapes of the input, weight, and output tensors in
a transformer decoder block. B, L and H denote batch size,
embedding (aka hidden) size and sequence length (L=1 during
decode, except for attention).

(c)

Figure 2: High-level architecture of a decoder block.

specifically that of the decode phase is limited by the maximum batch size we can fit on a GPU. Inference efficiency
can therefore benefit from model-parallelism which shards
the model weights across multiple GPUs freeing up memory to support larger batch sizes. Prior work has employed
both tensor-parallelism (TP) [43] (within node) and pipelineparallelism (PP) [6, 46, 48] (across nodes) for this purpose.
TP shards each layer across the participating GPUs. This
splits both the model weights and KV cache equally across
GPU workers, leading to linear scaling of per-GPU batch size.
However, it comes at a high communication cost due to two
all-reduce operations per layer – one in attention computation
and the other in FFN [43]. Moreover, since these communication operations are in the critical path, TP is preferred
only within a single node connected by high bandwidth interconnects like NVLink. PP is primarily used to facilitate
cross-node deployments for very large models, where the
model cannot fit within a single node.
Compared to TP, PP splits a model layer-wise, where each
GPU is responsible for a subset of layers. To keep all GPUs in
the ‘pipeline’ busy, micro-batching is employed. These microbatches move along the pipeline from one stage to the next at
each iteration. PP has the advantage of a much better computecommunication ratio compared to TP, as we only need to send
activations once for multiple layers of compute. Furthermore,
PP requires communication only via point-to-point communication operation, compared to the more expensive allreduces
required in TP. Thus, PP is the only viable model-parallelism
approach when high-bandwidth connectivity like NVlink is
unavailable at cluster-scale. In such settings, the use of PP
can help increase the maximum batch size supported in each
node by 2-3×, thereby improving LLM inference efficiency.

sequence length of each request (i.e., the number of input
tokens in the given query), and H is the model’s embedding
size (e.g., 5120 for LLaMA-13B).
Table 1 shows the shapes of input, output, and weight tensors of the various operations. Each transformer block first
computes self-attention on a given input X. Typically, multihead attention is used, but we consider only one head for
simplicity of exposition. A linear transformation preproj over
X (using the weight tensors W Q , W K and W V of shape [H, H])
produces the Q, K and V that are commonly known as queries,
keys, and values, each of shape [B, L, H]. Internally, preproj
is a single matrix-matrix multiplication of X with a combined
weight tensor of shape [H, 3H].
Next, the attn computation over Q, K and V produces a
tensor Y of shape [B, L, H]. Finally, postproj applies a linear transformation over Y (using weight matrix Wo of shape
[H, H]), returning a tensor Z of shape [B, L, H].
Next, the FFN module performs two batched matrix-matrix
multiplications. In ffn_ln1, Z is multiplied with a weight tensor of shape [H, H2 ] producing an output tensor of shape
[B, L, H2 ], which is then multiplied by a weight tensor of shape
[H2 , H] in ffn_ln2 to output a tensor of shape [B, L, H]. Here,
H2 refers to the second hidden dimension of the model.
The decode phase performs the same operations as prefill,
but only for the single token which was generated in the
last autoregressive iteration. Thus, the input tensor in decode
phase is of shape [B, 1, H] (as opposed to [B, L, H] of prefill).
Further, the attention computation for each new token depends
on the key (K), and value (V ) tensors of all prior tokens in the
same request. To avoid recomputing K and V of all tokens in
every iteration, most implementations cache these values in
GPU memory - which is referred to as the KV cache. Note
that each token’s K and V tensors are of shape [1, H].

2.3

Shapes of tensors
Input(s) Weight(s) Output(s)
[B, L, H]
[H, H]
[B, L, H]
[B, L, H]
[B, L, H]
[B, L, H]
[H, H]
[B, L, H]
[B, L, H]
[H, H2 ] [B, L, H2 ]
[B, L, H2 ]
[H2 , H]
[B, L, H]

3

Motivation

In this section, we show that LLM inference is inefficient for
two main reasons: (1) the decoding phase is memory-bound,
and (2) the use of pipeline parallelism leads to significant
pipeline bubbles for LLMs. Together, these factors lead to
poor GPU utilization for LLM inference.

Multi-GPU LLM Inference

As the model sizes of LLMs increase, it becomes necessary to scale them to multi-GPU as well as multi-node deployments [19, 39]. Furthermore, LLM inference throughput,
3



<!-- PDF page break -->

40

Time (ms)

Time (ms)

0.20

30

0.15

20

0.10
0.05

10

0.00

0

1

2

4

8 12 18

Batch size

1

2

4

Throughput (tokens/ms)

preproj
attn
postproj
ffn_ln1
ffn_ln2
others

8 12 18

Batch size

200
180
160
140
120
100
80
60
40
20
0 1

Prefill
Throughput (tokens/ms)

Decode

2

4

8 16 32 64 128 256 512

Batch Size

200
180
160
140
120
100
80
60
40
20
0 1

Decode

Sequence length: 64
Sequence length: 128
Sequence length: 256
Sequence length: 512
Sequence length: 1024

2

4

8 16 32 64 128 256 512

Batch Size

(a) Throughput of a single layer of LLaMA-13B on A6000 GPU.

Prefill

3000

Figure 3: Per-token prefill and decode time with different
batch sizes (sequence length = 1024) for LLaMa-13B on
A6000 GPU. Prefill saturates GPU compute even at batch
size of 1 and results in almost constant per-token time across
batch sizes. Decode under-utilizes GPU compute and costs
as much as 200× prefill for batch size 1. The incremental
cost of linear operators for decode is almost zero as batch size
increases. The attention cost does not benefit from batch size
as it is memory-bound.

250

Arithmetic intensity

2500

Arithmetic intensity

Prefill
0.25

200

2000

150

1500

Decode

100

1000
500
0

preproj
attn
postproj
ffn

1

2

4

Batch size

8

50
0

1

2

4

Batch size

8

256

(b) Arithmetic intensity with 1K sequence length (per-request).

Figure 4: Impact of the arithmetic intensity (bottom) on the
throughput (top) of prefills and decodes for LLaMA-13B on
A6000 GPU.

3.1 Analyzing Prefill and Decode Throughput
Figure 3 shows the per-token cost of each of the six transformer operations (§2.1) for prefill and decode at various
batch sizes for a fixed sequence length (prefill+decode) of
1024. First, we observe that prefill has almost constant pertoken cost across various batch sizes, indicating that prefill
saturates the GPU even at batch size of 1. Second, we see
that decode behaves very differently from prefill as the pertoken cost reduces significantly when the batch size increases.
Third, we see that the decode cost per-token is 200×, 100×,
and 16.7× that of prefill at batch size of 1, 2 and 18, respectively. Thus, it is clear that optimizing decodes is critical for
efficient LLM inference. Finally, we see that the operations
under others contribute less than 5% of the overall runtime of
the transformer block. Hence, we focus on only optimizing
the five major operations and ignore others.
Figure 4a shows the throughput of the prefill and decode
stages for different batch sizes (B) and sequence lengths (L).
We observe that the throughput of the prefill phase saturates
at about 180 tokens/millisecond when B × L ≥ 512: e.g., a
single prefill request can achieve peak throughput at L ≥ 512.
In contrast, the decode throughput increases linearly with
small batch sizes. To further understand the saturation point
of decode phase, we profile a single layer as opposed to the
40 layers of the full model. This enables us to fit 40× larger
batches on the GPU due to the reduced memory footprint of
model weights and KV caches. We find that decode saturates
at a much larger batch (e.g., 256 with 1024 sequence length).
Such large batches are infeasible to run with the full model.
To explain this behavior, we profile the arithmetic intensity
of individual operations: arithmetic intensity captures the
amount of compute per memory read/write that can be used
to distinguish between compute-bound and memory-bound

operations. Figure 4b shows the arithmetic intensity of each
operation separately for prefill (left) and decode phases (right).
As shown, in prefill phase, all operations have high arithmetic
intensity, even at a batch size of one. On the other hand, the
arithmetic intensity of these operations drop by more than
two orders of magnitude in the decode phase. Only at a very
large batch size of 256, the decode phase starts becoming
compute-intensive. However, scaling up the batch size to such
high values is infeasible due to the KV-cache footprint of
each request. For instance, we can fit a maximum batch size
of 18 requests at a sequence length of 1K for the LLaMA13B model on an A6000 GPU. Therefore, in the range of
batch sizes that are practical today, the decode phase remains
memory-bound.
The difference between the throughput scaling of these two
phases stems from the fact that the prefill phase computes
(batched) matrix-matrix multiplications as opposed to the
vector-matrix multiplications of the decode phase. It is wellknown that kernels with arithmetic intensity above a GPU’s
FLOPS:MemBandwidth ratio are compute-bound and can be
executed efficiently [11]. In contrast, kernels with a lower
arithmetic intensity fail to utilize GPUs well due to being
memory-bound.

3.2

Pipeline Bubbles in LLM Inference

Pipeline Parallelism (PP) is a popular strategy for cross-node
deployment of large models, owing to its lower communication overheads compared to Tensor Parallelism (TP). PP splits
a model layer-wise, where each GPU is responsible for a sub4



<!-- PDF page break -->

rate GPU compute even with a single request, while decodes
require a large batch size to be compute-efficient. However
large batches are impractical due to their high KV cache footprint. Such disproportionate resource utilization implies that
for every request, there are phases of high compute utilization
due to efficient prefills, followed by a potentially long tail
of inefficient decodes which results in poor overall GPU utilization. Furthermore, the non-uniformity in compute times
across micro-batches leads to pipeline bubbles, resulting in
inefficient pipeline parallel multi-GPU deployments.
This observation leads us to our key insight that it is possible to construct uniformly compute-intensive batches by (1)
slicing a large prefill request into smaller compute-efficient
and uniform chunks using chunked-prefills and (2) creating
a hybrid batch of a prefill chunk and piggybacking decodes
alongside this chunk. Consequently, creating such uniform
and compute-intensive batches ensures high GPU utilization
throughout, as well as, minimizes pipeline bubbles in multiGPU deployments by eliminating the runtime variance across
micro-batches in different stages of the pipeline.

Figure 5: Pipeline bubbles in LLM inference A 2-way
PP iteration-level schedule [48] across 4 requests (A,B,C,D)
shows the existence of pipeline bubbles due to non-uniform
batch execution times.
set of layers; compared to TP which shards each layer across
the participating GPUs. As discussed in §2.3, compared to
TP, PP has a much better compute-communication ratio and
does not require expensive interconnects.
A challenge with PP, however, is that it introduces pipeline
bubbles or periods of GPU inactivity as subsequent pipeline
stages have to wait for the completion of the corresponding
micro-batch in the prior stages. Pipeline bubbles is a known
problem in training jobs, where they arise between the forward and backward passes due to prior stages needing to wait
for the backward pass to arrive. Micro-batching is thus commonly employed in PP training jobs to amortize the bubbles
across the multiple micro-batches forming a batch [24,34,37].
Unlike training, since inference jobs only do forward passes
and do not have backward passes, one might expect that the
use of micro-batches will fully avoid pipeline bubbles during inference. In fact, prior work on transformer inference,
such as, FasterTransformer [6] and FastServe [46] use microbatches and do not consider the problem of bubbles with PP.
Orca [48] suggests that the use of iteration-level scheduling eliminates bubbles in pipeline scheduling (see Figure
8 in [48]). However, as we show in this paper, even with
iteration-level scheduling of requests, each micro-batch (or
iteration) in LLM inference can require a different amount
of compute (and consequently has varying execution time),
depending on the composition of prefill and decode tokens
in the micro-batch (see Figure 5). We identify three types
of bubbles during inference: (1) bubbles like PB1 that occur
due to the varying number of prefill tokens in two consecutive
micro-batches (2) bubbles like PB2 that occur due to different
compute times of prefill and decode stages when one is followed by the other, and (3) bubbles like PB3 that occur due to
difference in decode compute times between micro-batches
since the accumulated context length (KV cache length) varies
across requests. These pipeline bubbles are wasted GPU cycles and directly correspond to a loss in serving throughput
with pipeline parallelism. If we can ensure that each microbatch performs uniform computation, we can mitigate these
pipeline bubbles.

3.3

4

S ARATHI: Design and Implementation

In this section, we describe the design and implementation of
S ARATHI, which employs two techniques - chunked-prefills
and decode-maximal batching to improve the performance of
LLM inference.

4.1

Overview

Conventional inference engines like FasterTransformer [6]
perform request-level inference scheduling. They process
batches at request granularity; i.e., the they pick the next batch
of requests to execute on the model replica only when all the
requests in the current batch complete. While this reduces
the operational complexity of the scheduling framework, it is
inefficient in its use of resources. Shorter requests in a batch
have to be padded to match the length of the longest request,
and thus does wasteful work instead of exiting early. Alternatively, iteration-level scheduling has been proposed in more
recent systems like Orca [48], vLLM [20], and HuggingFace
TGI [17], where depending on the predetermined batch size
b, requests can dynamically enter and exit a batch.
However, today’s iteration-level scheduling systems do not
pay attention to the requests that comprise the batch, and the
varying execution time between batches. Specifically, a batch
could comprise of requests only in the prefill phase, requests
only in the decode phase, or mixed requests consisting of
a few prefills and decodes, with the only constraint that the
batch size is b at all times. As discussed in §3.3, such batch
formation results in non-uniform units of compute, resulting
in periods of bursty resource utilization, and pipeline bubbles. S ARATHI tackles this challenge by introducing two key
techniques: chunked-prefills and decode-maximal batching.

Insights

Our experiments show that the prefill and decode stages have
very different compute utilization patterns – prefill can satu5



<!-- PDF page break -->

k0
k1
k2
k3
q0 1
q1 1
1
q2 1
1
1
q3 1
1
1
1
attention mask during first chunk prefill

q4
q5
q6
q7

k0
1
1
1
1

q8
q9
q10
q11

k0
1
1
1
1

k1
k2
k3
k4
k5
k6
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
attention mask during second chunk prefill
k1
1
1
1
1

k2
1
1
1
1

sources of overhead. First, the arithmetic intensity of chunkedprefills computation decreases as the chunk size becomes
smaller. Therefore, smaller chunks can affect prefill efficiency
due to low GPU utilization. However, this can be addressed
easily with a one-time profiling of the prefill throughput for
various chunk sizes on a given model-hardware combination
and expected workloads and a chunk size can be chosen such
that the end-to-end throughput of the model is maximized.
Second, chunked-prefills pose a slight overhead in attention computation due to repeated memory accesses of the
KV cache of a request’s tokens from prior chunks. While
every chunked-prefills operation until the end of the prompt
will perform the same number of computations for FFNs, the
attention kernel in every subsequent chunk after the first will
have to reread all the KV pairs of the prior tokens from the
GPU memory, as shown in Figure 6. For example, if a prefill
sequence is split into N chunks, then the first chunk’s KV
cache is loaded N times, the second chunk’s KV cache is
loaded N − 1 times, and so on. However, the overhead due
to increased attention time does not significantly affect the
end-to-end prefill efficiency because attention computation is
a small fraction of the overall forward pass time as seen in
Table 2. We present a detailed analysis of the overheads of
chunked-prefills in §5.4.

k7
1

k3
k4
k5
k6
k7
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
attention mask during third chunk prefill

k8
1
1
1
1

k9
1
1
1

k10
1
1

k11
1

Figure 6: Example of how attention mask is set across different chunk prefill iterations in S ARATHI (q and k represent
“query" and “key" tokens, respectively). The attention mask
for v (“values") is set similarly.

4.2 Chunked-prefills
Chunked-prefills is a prefill splitting mechanism hinged on
two key insights. First, for a given model and GPU, increasing the number of prefill tokens shows diminishing returns in
throughput beyond a certain point as shown in Figure 4a. For
instance, the Llama-13B model achieves peak prefill throughput on an A6000 GPU when the number of prefill tokens is
512 or higher. At a chunk size of 256, we see a marginal reduction of 12.5% in the peak throughput. Further, as the size
of the hidden dimension in the model increases, the chunk
size needed to saturate the GPU compute drops; for example, the throughput of a single layer of GPT-3 (hidden size =
12288) peaks at a chunk size of 256 on an A100 GPU. This
implies that a compute-saturating batch can be formed with
a carefully sliced prefill chunk. Second, in many practical
scenarios, the size of prefill is reasonably large, ranging from
1K – 4K in production workloads, thereby opening the doors
for chunking a prefill request into smaller units of compute.
Implementing chunked-prefills requires carefully setting
the attention mask. If a request’s input prompt of say size
1K is split into four chunks of size 256 tokens each, we need
to ensure that the attention masks are appropriately set for
every subsequent prefill chunk until the end of the prompt.
For ease of exposition, using an example of chunk size of
four, Figure 6 shows how S ARATHI progressively sets the
attention mask for every successive chunk of a prefill prompt
in three consecutive iterations: each query token qi can peek
into the keys (and values) of all the tokens preceding it, but
not the ones that follow. Setting the attention mask this way
ensures that chunked-prefills computation is mathematically
equivalent to the full prefill.

4.3

Decode-Maximal Batching

Harnessing the benefits of chunked-prefills requires us to
carefully construct a hybrid batch consisting of a mix of prefill
and decode tokens, so as to maximize compute utilization
and ensure uniform compute time across all batches. We
propose decode-maximal batching to alleviate the imbalance
in compute and memory utilization in iterative scheduling by
exploiting the idea of chunked-prefills.
In decode-maximal batching, we construct a batch by using
a single prefill chunk and piggybacking the remaining slots
with decode tokens. This hybrid batch provides us with units
of work that are both compute saturating and uniform. We now
discuss how we construct a hybrid batch to achieve maximum
efficiency.
4.3.1

Piggybacking decodes with prefills

To piggyback decodes with a prefill, we need to take care of
two things. First, we need to identify the maximum possible batch size of decodes that can be piggybacked and also
identify the number of prefill tokens that comprise the prefill
chunk. Second, in order to actually utilize the GPU-saturating
prefill computation of the hybrid batch to make the decodes
efficient, we need to fuse the linear operation computations
for the prefill chunk and decodes of the batch into a single
operation.

Overhead of chunked-prefills. Splicing the input of a prefill sequence into multiple smaller chunks has two potential

Decode batch. The maximum decode batch size to be piggybacked with a prefill chunk is determined based on the
6



<!-- PDF page break -->

Operation(s)
Linear Attn
224.8
10
44.28 5.68
223.2 15.2

Total
Time
234.8
49.96
238.4

Per-token Time
Prefill Decode
0.229
12.49
0.229
1.2

preproj
postproj
ffn
total compute

250
200

Time (ms)

Batching
Scheme
Prefill-only
Decode-only
Decode-maximal

150
100

Table 2: Per-token prefill and decode time (in ms) For
LLaMA-13B on A6000 GPU, the rows show operation times
for 1) prefill-only requests of prompt size 1024 of batch size
4, 2) decode-only batch size of 4 with sequence length 1024,
and c) a mixed batch of a single 1021 prefills and 3 decodes.
Decode-maximal batching reduces the decode time per token
by an order of magnitude.

50
0

0

128

256

384

512

640

Sequence Length

768

896

1024

Figure 7: The effect of tile quantization on the runtime of one
iteration of LLaMA-13B on A6000 GPU.

available GPU memory (MG ), the model’s parameter memory requirement per GPU (MS ), and the maximum sequence
length L that the model supports. The total of prefill (P) and
decode (D) tokens per request cannot exceed this maximum
sequence length. Assuming the memory required per pair of
K and V for a token is mkv , the maximum permissible batch
size B is determined as follows


MG − MS
B=⌊
⌋
L ∗ mkv

maximal batching with that of the baseline scheme that computes prefill and decode iterations separately. With baseline
batching, a decode-only iteration spends 12.49 milliseconds
per token. In contrast, per-token decode time is only 1.2 milliseconds with decode-maximal batching. This shows that piggybacking decodes with prefills can improve decode throughput by up to an order to magnitude.

In the baseline scheme, decode-only batches can be of size
at most B. In S ARATHI, the number of decodes can be at most
B − 1 as they piggyback along with one prefill chunk (the
prefill’s KV cache also needs to be in GPU memory until its
corresponding decode iterations begin).
In decode-maximal batching, we fuse all the linear operations, while letting the attention computations for the prefill
and decodes happen separately. The attention operation for
decode requests is batched together, while the attention in
prefill chunk is processed separately.

An important design consideration in S ARATHI is how to pick
the most suitable chunk size. A straightforward choice is to
pick the smallest chunk size that saturates a model’s prefill
throughput. However, we find that this strategy is not the most
efficient in many cases.
To demonstrate the importance of chunk size, we introduce
a simple notation “P:D ratio" that is computed as the ratio of
the number of prefill tokens to the number of decode tokens
in a given batch. For example, a P:D ratio of 10 implies that
the number of prefill tokens is 10 times that of decode. For
a fixed P+D, a lower value of P:D ratio means that there are
more decode tokens in a batch compared to one with a higher
value of P:D ratio.
The size of prefill chunks in S ARATHI impacts the number
of decodes that can be piggybacked using decode-maximal
batching. For example, consider a batch size of four requests
(where one request is in the prefill phase and three are in the
decode phase) and a chunk size of 128. A prefill of size P will
then yield P/128 prefill-chunks, allowing P/128 ×3 ≈ P/42
decodes to piggyback. Thus, in this case, when the P:D ratio is
greater than 42, it allows us to overlap all decodes with prefills.
Similarly, if the chunk size is 256, then all decodes can be
piggybacked when the P:D ratio is greater than 84. Therefore,
a lower chunk size can help piggyback more decode tokens
for a given prefill sequence.
Note that decoding time increases as the the P:D ratio
goes down. Therefore, beyond a certain point, optimizing
decodes becomes more important than executing prefills at
peak efficiency. For example, if the prefill and decode phases
consume 10% and 90% of the total time, respectively, then

4.4

Decode efficiency. Recall that the prefill and decode phases
follow the same computation path, i.e., the linear operations
use the same weight tensors in both the prefill and decode
phases. However, compared to prefill, a decode iteration consists of only a few input tokens (equal to the batch size).
Therefore, most of the computation time in baseline decoding
is spent fetching model weights from GPU’s global memory.
In contrast, decode-maximal batching computes over the
decode tokens using matrix matrix multiplications, by combining decode tokens with the prefill tokens in a single matrix
multiplication operation. This, effectively eliminates the need
to load the model weights separately for decoding — i.e., once
the model weights are fetched for prefills, they are also reused
for decoding. As a result, decode-maximal batching converts
decoding from being in a memory-bound phase to being in a
compute-bound phase. This way, decodes, when piggybacked
with prefills come at a marginal cost in S ARATHI (note that
the attention cost remains unchanged).
To illustrate the various costs involved through an example,
Table 2 compares the runtime of one iteration of decode7

Identifying the ideal chunk size



<!-- PDF page break -->

Model

even a 5× overhead in prefills is acceptable if the decodes
can be optimized by 2× or more.
To sum it up, identifying a suitable chunk size involves a
trade-off: smaller chunks piggyback more decodes but at the
expense of lower prefill efficiency whereas larger chunks are
prefill efficient but piggyback fewer decodes. Therefore, the
ideal chunk size depends on the expected P:D ratio and the
split between prefill and decode times for a given application.

LLaMA-13B A6000
LLaMA-33B A100
GPT-3
A100

1
1
64

48
80
80

Mode
Deployment
Deployment
Simulation

Table 3: Models, GPUs, and mode of evaluation.

The tile quantization effect. Additionally, we observe an
intricate detail related to the chunk size. GPUs compute matmuls by partitioning the given matrices into tiles and assigning them to different thread blocks for parallel computation.
Here, each thread block refers to a group of threads and computes the same number of arithmetic operations. Therefore,
matmuls achieve maximum GPU utilization when the matrix dimensions are divisible by the tile size. Otherwise, due
to tile quantization, some thread blocks perform extraneous
(wasted) computation [11].
Notice that the time to compute a prefill sequence suddenly
increases when the sequence length is just higher than a multiple of 128 (tile size in our experiments). For example, as
shown in Figure 7, doubling the sequence length from 128 to
256 tokens increases iteration time by 27% — from 55ms to
69.8ms. However, adding only a single token further increases
the iteration time to 92.33ms — a dramatic 32% increase due
a only one additional token. This shows that the GPU is most
efficient at matmuls when the sequence length is a multiple
of the tile size.
Therefore, selecting the ideal chunk size is a two-fold decision. First, pick a chunk size based on the desired prefill
efficiency for the given workload. Next, ensure that the sum
of chunk size and the number of piggybacked decode tokens
is a multiple of the tile size. This ensures that the relevant
matrix dimension of the fused operations stays a multiple of
the tile size. For example, if the chosen chunk size is 256, the
tile size is 128, and the maximum permissible batch size is B,
then, the prefill chunk size should be 256 − (B − 1).

We support different model configurations in our codebase
to evaluate S ARATHI over different model and hardware combinations. For example, to evaluate LLaMA-13B, we set the
number of layers and attention heads to 40, and hidden size to
5120. For LLaMA-33B, we use 60 layers, 52 attention heads,
and hidden size of 6656. For GPT-3, we use 96 layers, 96
attention heads, and hidden size of 12288. The configurations
are as per the publicly available architectural parameters of
these models [10, 14].

5

Evaluation

We evaluate S ARATHI on a variety of models and GPUs using
physical deployments for single GPU experiments and profiledriven simulations for large-scale experiments as shown in Table 3. Our evaluation seeks to answer the following questions:
1. What is the impact of S ARATHI on the throughput of decodes as well as the end-to-end throughput of LLMs? In
addition, what is the impact of varying sequence lengths,
batch sizes, and P:D ratios (§5.1)?
2. How does S ARATHI compare to existing iteration-level
scheduling mechanisms like Orca (§5.2)?
3. What is the impact of our techniques on GPU bubbles and
the throughput of pipeline-parallel models (§5.3)?
4. What are the overheads of chunked-prefills (§5.4)?

5.1
4.5

GPU Num Per-GPU
GPUs Mem(GB)

Implementation

Evaluation on a Single GPU

In this section, we measure the decode speedup and the endto-end throughput of S ARATHI, on a single GPU, against that
of the baseline which executes the prefill and decode stages
separately via prefill-only and decode-only batches. Further,
we examine the effects of varying P : D ratio (ratio of prefill
to decode tokens), sequence lengths (total tokens per request
— P + D), and batch sizes on the overall throughput.

We implement S ARATHI on the nanoGPT codebase [12] with
support for both chunked-prefills and decode-maximal batching. To compare against Orcas’s iteration-level scheduling, we
use our mixed batching mechanism, with no constraint on the
number of prefills allowed per batch. This ensures that there is
no discrepancy in results between the baselines and S ARATHI
due to differences in implementation. To compute the attention operation, we use xformers implementation [21] as in our
setup, it outperformed PyTorch 2.0’s in-built attention implementations: i.e., flash attention, memory-efficient attention,
and math attention kernels. To avoid allocating memory for
KV caches in each decode iteration, we pre-allocate the KV
cache as per the maximum sequence length for each experiment and update respective KV pairs in place when required.

5.1.1

Decode speedup

We first show the impact of our techniques on decode phase
throughput that we calculate based on the average time spent
on decoding one token. For the baseline system, we compute
the average decode time per token by dividing the time to
process one decode iteration by the batch size. In S ARATHI,
8



<!-- PDF page break -->

10
9
8
7
6
5
4
3
2
1

Speedup (decode-only)

Sequence length: 1K
Sequence length: 2K
Sequence length: 3K

2

4

6

8

10

Batch Size

12

14

16

5.1.2

Table 4 shows the peak throughput gain that S ARATHI
achieves over the baseline. To demonstrate the generality
of our techniques, we evaluate S ARATHI on two model-GPU
combinations: (1) LLaMA-13B on an A6000 GPU and (2)
LLaMA-33B on an A100 GPU. Further, we investigate the
peak throughput gain with varying sequences of length 1K,
2K and 3K. Table 4 shows the batch sizes and P:D ratios
where we achieve the maximum speedup.
In the best case, our techniques improve the end-to-end
throughput by as much as 1.33× for LLaMA-13B and up
to 1.25× for LLaMA-33B. We observe that the speed up is
relatively higher on the A6000 GPU as compared to the A100
GPU. This is due to the higher FLOPs/MemBandwidth of the
A100 GPU compared to the A6000 GPU (≈ 156 vs. ≈ 53,
ignoring GPU caches). Therefore, we require a higher chunk
size on the A100 GPU (or a model with a higher embedding
size) to avoid losing the prefill efficiency. However, S ARATHI
still consistently outperforms the baseline by 1.14×-1.25× on
the A100 GPU. These results show that piggybacking decode
tokens with prefill chunks is useful across a wide range of
models and hardware. We note that although we improve
decode efficiency by up to an order of magnitude, the end-toend speedups and in turn monetary savings in inference cost
are in the order of 25%. This is because our technique only
improves decodes and not prefills.

18

Figure 8: Decode-only speedup with S ARATHI on an A6000
GPU with LLaMA-13B (chunk size = 256).

Model
(GPU)
LLaMA-13B
(A6000)
LLaMA-33B
(A100)

Sequence
Length
1K
2K
3K
1K
2K
3K

Batch
Size
6
6
6
10
5
3

P:D
Ratio
50:1
50:1
50:1
28:1
63:1
127:1

Decode
Speedup
5.45×
3.26×
2.51×
3.83×
4.25×
3.51×

Peak throughput gains with S ARATHI

Throughput
Gain
1.33×
1.26×
1.22×
1.25×
1.22×
1.14×

Table 4: Peak throughput gains with S ARATHI for different sequence lengths with two different model-GPU combinations
(chunk size = 256).

where decodes are piggybacked, for a batch with p + d tokens,
where p denotes the prefill chunk size and d denotes the
decode batch size, we find the difference in runtime between
the decode-maximal batch and a prefill-only batch of prefill
size p, and attribute the difference in time as the marginal
decode time for a batch of d requests. This marginal decode
time is then used to compute the decode time per token.

5.1.3

Effect of varying P : D ratio

In this subsection, using various sequence lengths and chunk
sizes, we investigate the effect of varying P : D ratios on
the end-to-end inference throughput to cover a wide range of
application scenarios. P : D ratio is an important parameter for
these experiments: a lower P : D ratio indicates that a request
constitutes more decode tokens compared to other requests
with a higher P : D ratio. Although a lower P : D ratio implies
that decodes will constitute a larger fraction of the inference
cost and thus S ARATHI will have more surface area of attack,
however, it also means there will be fewer prefill chunks for
piggybacking decodes. This trade-off results in a behavior
where the improvement from S ARATHI peaks at a particular
P : D ratio and then tapers off on either side. We discuss this
in more detail below.
Figure 9 plots the results of our experiments. We find that
the peak efficiency of our techniques occurs at different P : D
ratios for different prefill chunk size and batch size scenarios. If C is the chunk size and B is the batch size, then we
can show that this peak will occur when the decodes perfectly piggyback with the prefill chunks. This occurs when
the number of prefill chunks (= P/C) is the same as the required number of decode iterations (=D/(B − 1)), i.e., when
P : D = C/(B − 1). For example, using a chunk size of 256
at batch size of 18, S ARATHI achieves the peak throughput
improvement of 1.27× at P : D = 14 (≈ C/(B−1) = 256/17)

Figure 8 plots the results for a chunk size of 256 for LlaMa13B on A6000 GPU, as we vary the batch size, up to the
respective maximum value that fits, for three different prefill sequence lengths. We observe that chunked-prefills improves decode efficiency by up to an order of magnitude over
baseline. Decode throughput of S ARATHI is higher due to
decode-maximal batching that computes decode tokens with
matrix-multiplications, allowing reuse of the model weights
— for both prefills and decodes — once they are fetched from
the GPU’s global memory.
We observe that our decode speedup reduces as we increase
the batch size or sequence length. This behavior is expected
for the following reasons: (1) decodes in the baseline system
become more efficient as the batch size increases, and (2) the
cost of attention increases quadratically with the sequence
length: since all our improvements come from optimizing the
linear operations, a higher attention cost reduces our scope for
improvement. However, our decode throughput improvement
is still significant in all cases (2.8 × −10×).
9



<!-- PDF page break -->

1.25
1.20

1.35

Chunk size: 128
Chunk size: 256
Chunk size: 512

1.30
1.25

1.25
1.20

1.15

1.10

1.15

1.10

1.05

1.10

1.05

20

40

60

80 100 120 140 160 180 200

Prefill / Decode Ratio

(a) Sequence length = 1K, batch size = 18.

1.00 0

Chunk size: 128
Chunk size: 256
Chunk size: 512

1.30

1.20

1.15

1.00 0

1.35

Normalized Throughput

Normalized Throughput

Chunk size: 128
Chunk size: 256
Chunk size: 512

1.30

Normalized Throughput

1.35

1.05

20

40

60

1.00 0

80 100 120 140 160 180 200

Prefill / Decode Ratio

(b) Sequence length = 2K, batch size = 10.

20

40

60

80 100 120 140 160 180 200

Prefill / Decode Ratio

(c) Sequence length = 3K, batch size = 6.

2 4 6 8 10 12 14 16 18
Batch size

seq len: 1K, chunk size: 512

2 4 6 8 10 12 14 16 18
Batch size

postproj

Batch size

10
8 seq len: 2K, chunk size: 512
6
4
2
0 2
4
6
Batch size

ffn

8

10
8 seq len: 3K, chunk size: 256
6
4
2
0 2
4

6

8

10
8 seq len: 3K, chunk size: 512
6
4
2
0 2
4

6

Time (seconds)

seq len: 1K, chunk size: 256

attn

10
8 seq len: 2K, chunk size: 256
6
4
2
0 2
4
6

Batch size

Time (seconds)

10
8
6
4
2
0

preproj
Time (seconds)

10
8
6
4
2
0

Time (seconds)

Time (seconds)

Time (seconds)

Figure 9: Normalized throughput (tokens/ms) for LLaMa 13B on A6000 GPU with different sequence lengths, P:D ratios, and
chunk sizes.

Batch size

Figure 10: Breakdown of total time spent on different operations for LLaMa 13B on A6000 GPU with varying sequence lengths
and batch sizes, using prefill chunk sizes of 256 (top half) and 512 (bottom half). Orange and blue bars represent baseline and
S ARATHI, respectively.
for sequence length of 1K as shown in Figure 9a. Using the
chunk size of 512 for sequence length=1K at batch size of 18
also provides significant gains of up to 1.23× at P : D = 28
(≈ C/(B − 1) = 512/17) whereas the gains are much lower
with a chunk size of 128. While smaller chunks provide more
opportunity to overlap decodes, splitting prefills into very
small chunks leads to lower arithmetic intensity i.e. less efficient matmuls and higher overheads (due to multiple reads
of KV cache), resulting in reduced end-to-end performance.
Thus we obtain a much higher throughput with chunk size
of 256/512 compared to the smaller chunk size of 128. Note
that the peak gains occur at a higher value of P : D ratio when
using a larger chunk size.

S ARATHI either runs out of prefill tokens (if P : D is low) or
decode tokens (if P : D is high). In these cases, S ARATHI can
switch to a different chunk size, or operate similar to the standard baseline processing prefill-only or decode-only batches.
However, note that despite this variation, our improvements
are still around 10% over a large range of P : D ratios.
5.1.4

Effect of varying the batch and chunk sizes

In this section, we dive deeper to investigate the performance
of S ARATHI by varying the batch sizes and chunk sizes for
each sequence length. In all these experiments, we focus on
execution scenarios where the P : D ratio is balanced i.e.,
when P : D = C/(B − 1) and all decode tokens are perfectly
piggybacked with prefills. This allows us to measure the peak
performance of our system.
Figure 10 shows the results for these experiments. For each

We achieve peak performance when inference is not entirely dominated by either prefills or decodes (in other words,
when the P : D ratio is balanced). Such a state allows us to
overlap prefills and decodes efficiently for longer. Otherwise,
10



<!-- PDF page break -->

1.6
1.4
1.2
1.0
0.8
0.6
0.4
0.2
0.0

Normalized Throughput

Baseline
Orca (worst-case)

1K

5.2

Orca (best-case)
SARATHI

2K

In our evaluation thus far, we have considered a baseline
system that processes prefill-only or decode-only batches at a
time. This is how popular frameworks like FasterTransformer
deploy transformer models. In contrast, Orca’s iteration-level
scheduling [48] can add (or remove) a request to (or from) a
running batch at the granularity of individual iterations.
Iteration-level scheduling affects GPU utilization as well:
when requests arrive or depart at different times, some prefills
(of newly arriving requests) automatically overlap with the
decodes (of already running requests). Therefore, we expect
that iteration-level scheduling would do better than the baseline — at least in some cases. However, we emphasize that
the overlap between prefills and decodes is more of a sideeffect in iteration-level scheduling and its behavior can vary
significantly depending on the size and arrival or departure
time of requests. Even more importantly, current approaches
to iteration-level scheduling submit the entire input sequence
of a request in a single prefill phase. This significantly limits
the opportunity of piggybacking decode tokens with prefills.
To understand the effect on overall throughput, we evaluate
the state-of-the-art iteration-level scheduler, Orca [48], in two
scenarios: its best-case and worst-case. In the best case, Orca
scheduling overlaps the full prefill of one new request with the
ongoing decodes. In the worst-case, all the requests begin and
end at the same time. In the latter case, Orca scheduling behaves similar to our earlier baseline where there is no overlap
between the computation of prefill and decode tokens. Note
that in the average case of Orca, there could be more than one
full prefill (corresponding to multiple requests) overlapping
with some decodes – this would further limit Orca’s ability to
piggyback decodes tokens with prefills.
Figure 11 shows our results for these experiments. First
(Figure 11a), we show results for the optimal choice of
P : D = C/(B − 1), where C = 256 and B is the maximum
batch size that fits for the sequence length. As expected, worstcase Orca scheduling performs similar to the baseline. We
find that, for a small sequence length of 1K, the best-case Orca
scheduling achieves 1.11× higher throughput. This is due to
the incidental overlapping of the prefill and decode requests
in the best-case schedule. However, as sequence length increases, the performance of best-case Orca scheduling drops
close to the baseline. This is an artifact of our choice of
P : D = C/(B − 1). As we increase sequence length, the batch
size B reduces, resulting in a higher optimal P : D. Since Orca
submits the entire input sequence as a single prefill request,
a higher P : D means that it soon runs out of the prefill tokens, at which point it processes the remaining decode tokens
similar to the baseline, making even the best-case version
inefficient. S ARATHI consistently outperforms with overall
throughput gains of 1.27×, 1.25× and 1.23× for the three
sequence lengths.
Another aspect to consider in iteration-level scheduling is

3K

Sequence Length

(a) Varying sequence lengths (chunk size=256 for S ARATHI).
We choose the maximum batch size which fits for the sequence length (18, 10 and 6 for 1K, 2K and 3K sequence
lengths, respectively)
1.35

Normalized Throughput

SARATHI (chunk size = 128)
SARATHI (chunk size = 256)
SARATHI (chunk size = 512)
Orca (best-case)

1.30
1.25
1.20
1.15
1.10
1.05
1.000

10

20

30

40

50

60

70

Prefill / Decode Ratio

80

90

Comparison to Iteration-level Scheduling

100

(b) Varying P:D ratio (sequence length=1K, batch size=18).

Figure 11: Comparison with iteration-level scheduler Orca
for LLaMa 13B on A6000 GPU.

configuration of sequence length and chunk size, we show
the effect of varying batch sizes. Further, for each run, we
also show the runtime across different operations i.e., preproj,
attention, postproj, and ffn.
Note that decode-maximal batching batches the prefill and
decode tokens in linear operations to improve compute utilization. Therefore, the linear operations see a significant
runtime reduction of up to 1.6× (see ffn runtime in the first
row) compared to the baseline. However, note that the magnitude of improvement also depends on the P : D ratio (in
other words, it depends on what fraction of time is spent in
decodes). For example, using a chunk size of 256 doubles
the number of decodes that can be piggybacked compared to
using 512 as the chunk size. Therefore, in the optimal configurations (P : D = C/(B − 1)), for chunk size of 256, decodes
constitute a higher fraction of total runtime, compared to the
optimal configuration when chunk size is 512. Therefore, our
throughput gains are higher when using chunk size of 256.
We also observe that different linear operations see different speedups using our technique. Linear computation in the
ffn module sees the highest runtime reduction of 1.3×-1.6×.
In contrast, the runtime reduction for preproj and postproj is
1.05×-1.38×. For small batch sizes, we find that most of the
throughput improvement is due to the higher efficiency of ffn
computation in decode-maximal batching.
11



<!-- PDF page break -->

1.0

We first profile the runtime for each operation in Table 1
in the prefill and decode phase for various batch sizes and
sequence lengths for the GPT-3 model [25]. We further profile
the network communication cost to faithfully simulate tensorparallel and pipeline-parallel executions. Finally, we build
a regression model to extrapolate and predict these values
for missing data points that may be encountered during an
online simulated inference serving system. We confirmed that
the estimated runtimes by the simulator are within 5% of the
empirical values on an 8-GPU, 80GB A100 DGX box.
We report results for deployment over 64 A100 GPUs
across eight servers connected with InfiniBand. We evaluate three scenarios; (1) 8-way tensor-parallel (TP) within a
node with 8-way pipeline-parallel (PP) across nodes with the
best-case Orca-style scheduling, (2) the same TP-PP setup as
above with scheduling using S ARATHI’s chunked-prefills and
decode-maximal batching, (3) 8 parallel replicas, each with
8-way TP, serving simultaneously. For all scenarios, we use
the maximum batch size that fits the GPU — for TP+PP this
was 27 and for TP only this was 11. The P:D ratio is fixed
at 10 for this simulation with the minimum and maximum
sequence length of the requests set to 1K and 4K respectively.
Each request may have a different sequence length which is
sampled from a Zipf distribution (θ = 0.4), adhering to the
maximum sequence length. The number of prefill and decode
tokens is then calculated by satisfying the desired P:D ratio.
For this experiment, we set the chunk size to be 256.
Figure 12a plots the cdf of pipeline bubble time per request.
We define this as the sum of bubble time for all the microbatches across all iterations for a given request. S ARATHI
reduces the median bubble time per request by 6.29×, by
creating equal-compute units of work.
Next, we compare the overall request completion time for
the different scenarios in Figure 12b. This graph plots the
time to complete a given number of requests (our simulation considers a total of 10K requests). The TP-PP execution
requires less memory for storing parameters compared to
the TP-only setup, resulting in more room for the KV cache.
Thus the TP-PP deployment supports 2.45× higher batch
size compared to TP-only deployment, and yet, we observe
that the TP-only execution is 1.28× faster than the baseline
TP-PP with Orca scheduling, due to the large pipeline bubbles in the latter case. However, with chunked-prefills and
decode-maximal batching, S ARATHI enabled PP execution is
accelerated by 1.91× compared to the baseline TP-PP, and by
1.48× compared to the TP-only execution. Thus, S ARATHI
makes pipeline parallel execution an attractive option for
LLM inference by significantly minimizing pipeline bubbles.

0.8

CDF

0.6
0.4

SARATHI
TP+PP

0.2
0.00

20

40

60

80

Bubble Time (s)

(a) Comparison of bubble time

Time to complete (s)

3500
3000
2500
2000
1500
1000
500
00

SARATHI
TP+PP
TP (8 replicas)

2000

4000

6000

Num Requests

8000

10000

(b) End-to-end request completion time

Figure 12: Impact of S ARATHI on pipeline bubbles (top) and
request completion times (bottom) for GPT-3 deployed on
DGX A100(s) in simulation.

the effect of variable sequence lengths on request latencies.
Since the prefill time increases with the length of the input
sequence, adding a longer prefill sequence in a running batch
can delay the ongoing decodes, which in turn increases the latency of these ongoing requests in Orca scheduling. S ARATHI
avoids this due to the use of smaller chunk prefills.
Next, we evaluate the throughput gains at different P : D ratios for different chunk sizes in Figure 11b. We consider only
sequence length of 1K for this experiment as the best-case
Orca baseline achieves maximum performance in this regime.
Note that best-case Orca scheduling can be considered a special case of S ARATHI, where the chunk size, C, is set to the
maximum sequence length. As can be seen, the optimal P : D
shifts to the right as chunk-size increases. S ARATHI with
chunk size of 256 performs the best in lower P : D regimes,
reaching a peak throughput gain of 1.27× compared to baseline. S ARATHI with chunk size of 512 consistently outperforms Orca best-case and performs overall best in the higher
P : D regime, reaching a peak throughput gain of 1.23×. In
comparison, Orca best-case has much flatter gains and reaches
a peak throughput gain of 1.11× at a much higher P : D.

5.3

Pipeline Parallelism with S ARATHI
5.4

Next, we evaluate how S ARATHI reduces pipeline bubbles in
a multi-GPU pipeline-parallel setup and subsequently impacts
the overall runtime of inference jobs. For this experiment, we
report evaluations in a carefully simulated environment.

Ablation Study of Chunked-prefills

In this subsection, we evaluate how splitting a full prefill
computation into multiple smaller prefill chunks affects the
efficiency of the prefill stage in S ARATHI. To quantify this, we
12



<!-- PDF page break -->

1K

192
256

2K

Sequence length

320
384

448
512

3K

(a) Self-attention (prefill-only).

1.4
1.2
1.0
0.8
0.6
0.4
0.2
0.0

1.4
1.2
1.0
0.8
0.6
0.4
0.2
0.0

Speedup (overall)

64
128

Speedup (prefill)

Speedup (prefill-attention)

1.4
1.2
1.0
0.8
0.6
0.4
0.2
0.0

1K

2K

Sequence length

3K

(b) chunked-prefills vs. full prefill.

1K

2K

Sequence length

3K

(c) End-to-end speedup for the entire batch.

Figure 13: Ablation study: Effect of varying the chunk size on different components of the system for LLaMa 13B on A6000
GPU.

6

measure the time to compute the prefill phase for various sequence lengths using the full sequence at once - this represents
our baseline prefill performance. For each long sequence, we
then compute the prefill with chunked-prefills and compare its
end-to-end runtime with the baseline. The difference between
the two indicates the overhead of chunked-prefills.

Discussion

In this paper, we have comprehensively demonstrated how
S ARATHI improves the performance of LLM inference across
several models and hardware configurations. However, there
are multiple challenges that require further investigation.

Prefill chunking has two potential sources of overheads: (1)
it uses smaller chunk sizes compared to the baseline which
may lower the GPU utilization, and (2) it needs to load the
KV cache of each chunk multiple times, depending on the
number of chunks in a request. Therefore, to fully understand
the overhead of prefill chunking, we investigate the following:
(1) what is the impact of chunking on attention computation
for a prefill-only batch, (2) what is the effect of chunking
on the overall runtime of prefill-only batch, and (3) what is
the end-to-end throughput when chunked-prefills is used in
tandem with decode-maximal batching. We study these by
varying the chunk size from 64 to 512 as shown in Figure 13.

First, we focus only on an efficient scheduling mechanism
in S ARATHI to improve the throughput of LLM inference.
However, real-world deployments need to optimize an inference serving infrastructure simultaneously along multiple
dimensions e.g., latency, queuing delays, fairness, etc. Meeting these goals with S ARATHI requires revisiting scheduling
policies. Second, although we show what is an appropriate
chunk size for a given P:D ratio, we leave it to future work
to explore how to pick an optimal chunk size as it depends
on several factors like the hardware, model characteristics,
sequence length, and the composition of prefill-decode tokens,
especially in scenarios where the P:D ratio may not be known
ahead of time. Third, we make a simplistic assumption in this
paper that each request in a batch has the same number of
prefill and decode tokens (except the simulation experiments)
whereas, in the real world, the sequence lengths can vary significantly across different LLM inference requests. Finally,
we focused on sequence lengths of up to 3K, and P:D ratio in
the range of 1-200. We believe that these are representative of
many real-world deployments. However, there has also been
an increased interest in supporting very long sequences (e.g.,
10s-100s of thousands [18]). Such large sequence lengths may
pose new challenges as the cost of attention grows quadratically with the number of tokens. We are actively investigating
these challenges.

First, we observe that smaller chunk sizes can add significant overhead, for both attention and the overall prefill runtime. For example, the chunk size of 64 incurs 3× overhead
for attention (see Figure 13a) and about 5×(see Figure 13b)
in the overall prefill time. As one can expect, the overhead of
chunked-prefills is lower for large chunk sizes: this is a combined effect of higher GPU utilization and fewer KV cache
reloads with larger chunks. Overall, we find that chunk sizes
of 256 and 512 provide reasonable prefill efficiency, limiting
the end-to-end prefill computation loss to within 20% and
10%, respectively.
Second, S ARATHI can compensate for some loss in prefill efficiency by improving the decode throughput. For instance, we see from Figure 13c that a chunk size of 64 almost
matches the performance of our baseline despite being 5×
slower in prefill whereas a chunk size of 128 yields up to
1.16× higher throughput despite its prefill being more than
2× slower than the baseline, mainly due to piggybacking
more decodes. The tile-quantization effect is also evident
in Figure 13 as S ARATHI achieves higher improvement in
throughput when the chunk size is a multiple of 128; e.g.,
chunk size 256 shows better speedup than 320.

7

Related Work

In this section, we provide a brief summary of related work
along two dimensions: systems optimizations and model innovations.
13



<!-- PDF page break -->

7.1

Systems Optimizations

language models or to take the next leap forward in model
architectures, beyond transformers. For example, multi-query
attention shares the same keys and values across all the attention heads to reduce the size of the KV cache [41], allowing larger batch sizes. Several recent works have also shown
that the model sizes can be compressed significantly using
quantization [30–32,47]. Mixture-of-expert models are aimed
primarily at reducing the number of model parameters that get
activated in an iteration [23, 33, 36]. More recently, retentive
networks have been proposed as a successor to transformers [44]. In this work, we focus on addressing the performance
issues of the most popular transformer models from a GPU’s
perspective. Model innovations are orthogonal to our work.

Memory management: In auto-regressive decoding, the
number of tokens that need to be generated for a given request is not known apriori. Therefore, conventional systems
pre-allocate memory for the KV cache based on a conservative estimation of the maximum number of tokens. Recently, vLLM showed that this approach is inefficient and
proposed a framework — motivated by the virtual memory
abstraction — that enables incremental memory allocation
for KV caches [20]. This helps improve the batch size, especially when the number of tokens varies significantly across
different requests. FlexGen [42] focuses on improving the
throughput of offline LLM inference in resource-constrained
scenarios e.g., running a large model on a single GPU. Toward this goal, FlexGen employs a judicious combination of
memory offloading, quantization, and scheduling.
Optimizing (self-)attention: In [40], the authors propose an
algorithm to reduce the memory requirement of self-attention
from O(n2 ) to O(1), with respect to the sequence length.
FlashAttention [29] proposed a tiling-based algorithm that
speeds up attention computation by minimizing the number of
bytes read/written between different levels of GPU memory.
Follow-up work [28] on FlashAttention further improved it
along parallelism and work partitioning [28]. In our experiments, we found the xformers memory efficient attention
implementation [21] to be the most efficient.
Kernel-level optimizations: FasterTransformer [6] proposed
optimized layers for the transformer’s encoder and decoder
blocks. These are based on low-level GPU optimizations such
as kernel fusion. We expect that such low-level optimizations
would equally benefit S ARATHI as well.
Scheduling optimizations: Orca proposed an iteration-level
scheduling framework that avoids wasting compute due to
token padding that was used earlier to batch together requests
with different sequence lengths [48]. Further, Orca reduces
latency by returning the response as soon as a request’s endof-sequence token gets generated. FastServe proposed a preemptive scheduling framework to minimize the job completion times [46]. Some other scheduling frameworks include
Triton [13] and Clipper [27] that separate the serving layer
from the execution engine of the model. Our current work
focuses on optimizing the execution layer and can be used
with different scheduling policies proposed by such systems.
The optimizations proposed by several of the prior works
can complement our optimizations e.g., more optimized attention implementations will enable scaling S ARATHI to longer
sequence lengths and dynamic memory allocation will help
in supporting larger batch sizes and so on.

7.2

8

Conclusion

In this paper, we identify two primary reasons for LLM inference inefficiency: 1) suboptimal GPU utilization due to lack
of parallelism and memory-bound nature of decode phase,
and 2) significant pipeline bubbles due to inconsistent prefill
and decode times across different iterations, leading to microbatch imbalance. To address these challenges, we introduce
S ARATHI, a novel approach that incorporates chunked-prefills
and decode-maximal batching. Decode-maximal batching improves GPU utilization by piggybacking decodes with prefills,
which converts the memory-bound decode phase to be compute bound. Chunked-prefills helps with making more prefills
available for decodes to piggyback, and also provides for a
uniform unit of work which helps significantly reduce pipeline
bubbles. We demonstrate that S ARATHI results in significant
improvements in end-to-end throughput across models and
hardware configurations.

Model Innovations

A significant body of work around model innovations has
attempted to address the shortcomings of transformer-based
14



<!-- PDF page break -->

References

[20] vllm: Easy, fast, and cheap llm serving for everyone.
https://github.com/vllm-project/vllm.

[1] Amazon codewhisperer. https://aws.amazon.com/
codewhisperer/.
[2] Anthropic claude. https://claude.ai.

[21] XFORMERS
OPTIMIZED
OPERATORS.
https://facebookresearch.github.io/xformers/
components/ops.html.

[3] Bing ai. https://www.bing.com/chat.

[22] You.com. https://you.com/.

[4] Character ai. https://character.ai.

[23] Mikel Artetxe, Shruti Bhosale, Naman Goyal, Todor Mihaylov, Myle Ott, Sam Shleifer, Xi Victoria Lin, Jingfei
Du, Srinivasan Iyer, Ramakanth Pasunuru, Giri Anantharaman, Xian Li, Shuohui Chen, Halil Akin, Mandeep Baines, Louis Martin, Xing Zhou, Punit Singh
Koura, Brian O’Horo, Jeff Wang, Luke Zettlemoyer,
Mona Diab, Zornitsa Kozareva, and Ves Stoyanov. Efficient large scale language modeling with mixtures of
experts, 2022.

[5] Chatgpt. https://chat.openai.com.
[6] Faster Transformer. https://github.com/NVIDIA/
FasterTransformer.
[7] Github copilot.
copilot.

https://github.com/features/

[8] Google bard. https://bard.google.com.

[24] Sanjith Athlur, Nitika Saran, Muthian Sivathanu, Ramachandran Ramjee, and Nipun Kwatra. Varuna: scalable, low-cost training of massive deep learning models.
In Proceedings of the Seventeenth European Conference
on Computer Systems, pages 472–487, 2022.

[9] Komo. https://komo.ai/.
https://huggingface.co/
[10] Llama model card.
decapoda-research/llama-13b-hf.
[11] Matrix multiplication background user’s
https://docs.nvidia.com/deeplearning/
performance/dl-performance-matrixmultiplication/index.html.

[25] Tom Brown, Benjamin Mann, Nick Ryder, Melanie
Subbiah, Jared D Kaplan, Prafulla Dhariwal, Arvind
Neelakantan, Pranav Shyam, Girish Sastry, Amanda
Askell, et al. Language models are few-shot learners. Advances in neural information processing systems,
33:1877–1901, 2020.

guide.

[12] nanogpt. https://github.com/karpathy/nanoGPT.

[26] Aakanksha Chowdhery, Sharan Narang, Jacob Devlin, Maarten Bosma, Gaurav Mishra, Adam Roberts,
Paul Barham, Hyung Won Chung, Charles Sutton, Sebastian Gehrmann, Parker Schuh, Kensen Shi, Sasha
Tsvyashchenko, Joshua Maynez, Abhishek Rao, Parker
Barnes, Yi Tay, Noam Shazeer, Vinodkumar Prabhakaran, Emily Reif, Nan Du, Ben Hutchinson, Reiner
Pope, James Bradbury, Jacob Austin, Michael Isard, Guy
Gur-Ari, Pengcheng Yin, Toju Duke, Anselm Levskaya,
Sanjay Ghemawat, Sunipa Dev, Henryk Michalewski,
Xavier Garcia, Vedant Misra, Kevin Robinson, Liam Fedus, Denny Zhou, Daphne Ippolito, David Luan, Hyeontaek Lim, Barret Zoph, Alexander Spiridonov, Ryan Sepassi, David Dohan, Shivani Agrawal, Mark Omernick,
Andrew M. Dai, Thanumalayan Sankaranarayana Pillai, Marie Pellat, Aitor Lewkowycz, Erica Moreira, Rewon Child, Oleksandr Polozov, Katherine Lee, Zongwei Zhou, Xuezhi Wang, Brennan Saeta, Mark Diaz,
Orhan Firat, Michele Catasta, Jason Wei, Kathy MeierHellstern, Douglas Eck, Jeff Dean, Slav Petrov, and
Noah Fiedel. Palm: Scaling language modeling with
pathways. CoRR, abs/2204.02311, 2022.

https:
[13] NVIDIA Triton Inference Server.
//developer.nvidia.com/nvidia-tritoninference-server.
[14] Openai gpt-3: Understanding the architecture.
https://www.theaidream.com/post/openai-gpt3-understanding-the-architecture.
[15] Perplexity ai. https://www.perplexity.ai/.
[16] Replit ghostwriter.
ghostwriter.

https://replit.com/site/

[17] Text generation inference. https://huggingface.co/
text-generation-inference.
[18] The Secret Sauce behind 100K context window in LLMs: all tricks in one place.
https:
//blog.gopenai.com/how-to-speed-up-llmsand-use-100k-context-window-all-tricks-inone-place-ffd40577b4c.
[19] Using NVIDIA’s AI/ML Frameworks for Generative AI on VMware vSphere.
https:
//core.vmware.com/blog/using-nvidias-aimlframeworks-generative-ai-vmware-vsphere.

[27] Daniel Crankshaw, Xin Wang, Guilio Zhou, Michael J
Franklin, Joseph E Gonzalez, and Ion Stoica. Clipper:
15



<!-- PDF page break -->

A {Low-Latency} online prediction serving system. In
14th USENIX Symposium on Networked Systems Design
and Implementation (NSDI 17), pages 613–627, 2017.

[39] Reiner Pope, Sholto Douglas, Aakanksha Chowdhery, Jacob Devlin, James Bradbury, Anselm Levskaya,
Jonathan Heek, Kefan Xiao, Shivani Agrawal, and Jeff
Dean. Efficiently scaling transformer inference, 2022.

[28] Tri Dao. Flashattention-2: Faster attention with better
parallelism and work partitioning, 2023.

[40] Markus N. Rabe and Charles Staats. Self-attention does
not need o(n2 ) memory, 2022.

[29] Tri Dao, Daniel Y. Fu, Stefano Ermon, Atri Rudra,
and Christopher Ré. Flashattention: Fast and memoryefficient exact attention with io-awareness, 2022.

[41] Noam Shazeer. Fast transformer decoding: One writehead is all you need, 2019.
[42] Ying Sheng, Lianmin Zheng, Binhang Yuan, Zhuohan
Li, Max Ryabinin, Daniel Y. Fu, Zhiqiang Xie, Beidi
Chen, Clark Barrett, Joseph E. Gonzalez, Percy Liang,
Christopher Ré, Ion Stoica, and Ce Zhang. Flexgen:
High-throughput generative inference of large language
models with a single gpu, 2023.

[30] Tim Dettmers, Mike Lewis, Younes Belkada, and Luke
Zettlemoyer. Llm.int8(): 8-bit matrix multiplication for
transformers at scale, 2022.
[31] Tim Dettmers, Artidoro Pagnoni, Ari Holtzman, and
Luke Zettlemoyer. Qlora: Efficient finetuning of quantized llms, 2023.
[32] Elias Frantar, Saleh Ashkboos, Torsten Hoefler, and Dan
Alistarh. Gptq: Accurate post-training quantization for
generative pre-trained transformers, 2023.

[43] Mohammad Shoeybi, Mostofa Patwary, Raul Puri,
Patrick LeGresley, Jared Casper, and Bryan Catanzaro.
Megatron-lm: Training multi-billion parameter language
models using gpu model parallelism. arXiv preprint
arXiv:1909.08053, 2019.

[33] Haiyang Huang, Newsha Ardalani, Anna Sun, Liu Ke,
Hsien-Hsin S. Lee, Anjali Sridhar, Shruti Bhosale,
Carole-Jean Wu, and Benjamin Lee. Towards moe deployment: Mitigating inefficiencies in mixture-of-expert
(moe) inference, 2023.

[44] Yutao Sun, Li Dong, Shaohan Huang, Shuming Ma,
Yuqing Xia, Jilong Xue, Jianyong Wang, and Furu Wei.
Retentive network: A successor to transformer for large
language models, 2023.

[34] Yanping Huang, Youlong Cheng, Ankur Bapna, Orhan
Firat, Dehao Chen, Mia Chen, HyoukJoong Lee, Jiquan
Ngiam, Quoc V Le, Yonghui Wu, et al. Gpipe: Efficient training of giant neural networks using pipeline
parallelism. Advances in neural information processing
systems, 32, 2019.

[45] Jason Wei, Yi Tay, Rishi Bommasani, Colin Raffel, Barret Zoph, Sebastian Borgeaud, Dani Yogatama, Maarten
Bosma, Denny Zhou, Donald Metzler, Ed H. Chi, Tatsunori Hashimoto, Oriol Vinyals, Percy Liang, Jeff Dean,
and William Fedus. Emergent abilities of large language
models. Trans. Mach. Learn. Res., 2022, 2022.
[46] Bingyang Wu, Yinmin Zhong, Zili Zhang, Gang Huang,
Xuanzhe Liu, and Xin Jin. Fast distributed inference
serving for large language models, 2023.

[35] Jared Kaplan, Sam McCandlish, Tom Henighan, Tom B.
Brown, Benjamin Chess, Rewon Child, Scott Gray, Alec
Radford, Jeffrey Wu, and Dario Amodei. Scaling laws
for neural language models. CoRR, abs/2001.08361,
2020.

[47] Guangxuan Xiao, Ji Lin, Mickael Seznec, Hao Wu,
Julien Demouth, and Song Han. Smoothquant: Accurate and efficient post-training quantization for large
language models, 2023.

[36] Jiamin Li, Yimin Jiang, Yibo Zhu, Cong Wang, and
Hong Xu. Accelerating distributed MoE training and
inference with lina. In 2023 USENIX Annual Technical
Conference (USENIX ATC 23), pages 945–959, Boston,
MA, July 2023. USENIX Association.

[48] Gyeong-In Yu, Joo Seong Jeong, Geon-Woo Kim, Soojeong Kim, and Byung-Gon Chun. Orca: A distributed
serving system for Transformer-Based generative models. In 16th USENIX Symposium on Operating Systems
Design and Implementation (OSDI 22), pages 521–538,
Carlsbad, CA, July 2022. USENIX Association.

[37] Deepak Narayanan, Aaron Harlap, Amar Phanishayee,
Vivek Seshadri, Nikhil R Devanur, Gregory R Ganger,
Phillip B Gibbons, and Matei Zaharia. Pipedream: generalized pipeline parallelism for dnn training. In Proceedings of the 27th ACM Symposium on Operating
Systems Principles, pages 1–15, 2019.
[38] OpenAI.
GPT-4 technical report.
abs/2303.08774, 2023.

CoRR,

16



<!-- PDF page break -->

## Part II: Sarathi-Serve Serving System

- Title: `Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve`
- Source: 18th USENIX Symposium on Operating Systems Design and Implementation (OSDI '24), pages 117-134, July 2024
- Landing page: https://www.usenix.org/conference/osdi24/presentation/agrawal
- PDF: https://www.usenix.org/system/files/osdi24-agrawal.pdf

Taming Throughput-Latency Tradeoff
in LLM Inference with Sarathi-Serve
Amey Agrawal, Georgia Institute of Technology; Nitin Kedia, Ashish Panwar,
Jayashree Mohan, Nipun Kwatra, and Bhargav Gulavani, Microsoft Research India;
Alexey Tumanov, Georgia Institute of Technology; Ramachandran Ramjee,
Microsoft Research India
https://www.usenix.org/conference/osdi24/presentation/agrawal

This paper is included in the Proceedings of the
18th USENIX Symposium on Operating Systems
Design and Implementation.
July 10–12, 2024 • Santa Clara, CA, USA
978-1-939133-40-3
Open access to the Proceedings of the
18th USENIX Symposium on Operating
Systems Design and Implementation
is sponsored by



<!-- PDF page break -->

Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve
Amey Agrawal* 2 , Nitin Kedia1 , Ashish Panwar1 , Jayashree Mohan1 , Nipun Kwatra1 ,
Bhargav S. Gulavani1 , Alexey Tumanov2 , and Ramachandran Ramjee1
1 Microsoft Research India

Each LLM serving request goes through two phases. The
first is prefill which processes the entire input prompt and produces the first output token and the second is decode which
generates the rest of output tokens, one-at-a-time. Prefill iterations have high latency but saturate GPU compute due to
parallel processing of the input prompt. In contrast, decode
iterations have low latency but also low compute utilization
because a decode iteration processes only a single token per
request. This makes batching highly effective for decodes
and consequently for overall throughput. However, batching
multiple requests leads to an interleaving of prefill and decode
iterations which makes it challenging to achieve both high
throughput and low latency.
We introduce an efficient LLM inference scheduler, SarathiServe, to address this throughput-latency tradeoff. SarathiServe introduces chunked-prefills which splits a prefill request
into near equal sized chunks and creates stall-free schedules
that adds new requests in a batch without pausing ongoing
decodes. Stall-free scheduling unlocks the opportunity to improve throughput with large batch sizes while minimizing the
effect of batching on latency. Furthermore, uniform batches
in Sarathi-Serve ameliorate the imbalance between iterations,
resulting in minimal pipeline bubbles.
Our techniques yield significant improvements in inference
performance across models and hardware under tail latency
constraints. For Mistral-7B on single A100 GPUs, we achieve
2.6× higher serving capacity and up to 3.7× higher serving capacity for the Yi-34B model on two A100 GPUs as compared
to vLLM. When used with pipeline parallelism on Falcon180B, Sarathi-Serve provides up to 5.6× gain in the end-toend serving capacity. The source code for Sarathi-Serve is
available at https://github.com/microsoft/sarathi-serve.

* Part of this work was done during an internship at MSR India.

USENIX Association

30K
Sarathi-Serve
vLLM

20K
10K

Generation stall

0K

200

0

100

200

Time (s)

210

300

(a) Generation stall.

220

Time-between-tokens
(P99, seconds)

Abstract

Tokens Generated

2 Georgia Institute of Technology

vLLM
Sarathi-Serve

1.25
1.00
0.75
0.50
0.25
0.00

0.55

0.7

1.0

Queries per Second

(b) High tail latency.

Figure 1: Yi-34B running on two A100 GPUs serving 128
requests from arxiv-summarisation trace. 1a highlights one
of the many generation stalls lasting over several seconds in
vLLM [53]. 1b shows the impact of increasing load on tail
latency. Sarathi-Serve improves throughput while eliminating
generation stalls.

1

Introduction

Large language models (LLMs) [34,35,52,57,71] have shown
impressive abilities in a wide variety of tasks spanning natural language processing, question answering, code generation, etc. This has led to tremendous increase in their usage across many applications such as chatbots [2, 5, 6, 57],
search [4, 9, 11, 19, 25], code assistants [1, 8, 20], etc. The
significant GPU compute required for running inference on
large models, coupled with significant increase in their usage,
has made LLM inference a dominant GPU workload today.
Thus, optimizing LLM inference has been a key focus for
many recent systems [29, 53, 58, 59, 63, 75, 77].
Optimizing throughput and latency are both important objectives in LLM inference since the former helps keep serving
costs tractable while the latter is necessary to meet application requirements. In this paper, we show that current LLM
serving systems have to face a tradeoff between throughput
and latency. In particular, LLM inference throughput can be
increased significantly with batching. However, the way existing systems batch multiple requests leads to a compromise on
either throughput or latency. For example, Figure 1b shows

18th USENIX Symposium on Operating Systems Design and Implementation

117



<!-- PDF page break -->

1We classify recent schedulers Splitwise [58] and DistServe [77] under a

third category “disaggregated” and discuss them in §6.

118

Throughput

that increasing load can significantly increase tail latency in a
state-of-the-art LLM serving system vLLM [53].
Each LLM inference request goes through two phases – a
prefill phase followed by a decode phase. The prefill phase
corresponds to the processing of the input prompt and the
decode phase corresponds to the autoregressive token generation. The prefill phase is compute-bound because it processes
all tokens of an input prompt in parallel whereas the decode
phase is memory-bound because it processes only one token
per-request at a time. Therefore, decodes benefit significantly
from batching because larger batches can use GPUs more
efficiently whereas prefills do not benefit from batching.
Current LLM inference schedulers can be broadly classified
into two categories1 , namely, prefill-prioritizing and decodeprioritizing depending on how they schedule the prefill and
decode phases while batching requests. In this paper, we argue
that both strategies have fundamental pitfalls that make them
unsuitable for serving online inference (see Figure 2).
Traditional request-level batching systems such as FasterTransformer [7] employ decode-prioritizing scheduling.
These systems submit a batch of requests to the execution
engine that first computes the prefill phase of all requests and
then schedules their decode phase. The batch completes only
after all requests in it have finished their decode phase i.e.,
new prefills are not scheduled as long as one or more requests
are doing decodes. This strategy optimizes inference for latency metric time-between-tokens or TBT – an important
performance metric for LLMs. This is because new requests
do not affect the execution of ongoing requests in their decode phase. However, decode-prioritizing schedulers severely
compromise on throughput because even if some requests in a
batch finish early, the execution continues with reduced batch
size until the completion of the last request.
Orca [75] introduced iteration-level batching wherein requests can dynamically enter or exit a batch at the granularity of individual iterations. Iteration-level batching improves throughput by avoiding inefficiencies of request-level
batching systems. Orca and several other recent systems
like vLLM [23] combine iteration-level batching with prefillprioritizing scheduling wherein they eagerly schedule the
prefill phase of one or more requests first i.e., whenever GPU
memory becomes available. This way, prefill-prioritizing
schedulers have better throughput because computing prefills first allows subsequent decodes to operate at high batch
sizes. However, prioritizing prefills leads to high latency because it interferes with ongoing decodes. Since prefills can
take arbitrarily long time depending on the lengths of the
given prompts, prefill-prioritizing schedulers lead to an undesirable phenomenon that we refer to as generation stalls in
this paper. For example, Figure 1a shows that a generation
stall in vLLM can last over several seconds.
Another challenge introduced by traditional iteration-level

Sarathi-Serve
Stall-free
batching

vLLM
Prefill prioritizing
Paged
Attention

Orca
Prefill prioritizing

Iteration-level
batching

FasterTransformer
Decode prioritizing

TBT Latency

Figure 2: Current LLM serving systems involve a tradeoff between throughput and latency depending on their scheduling
policy. Prioritizing prefills optimizes throughput but sacrifices
TBT (time-between-tokens) tail latency whereas prioritizing
decodes has the opposite effect. Sarathi-Serve serves high
throughput with low TBT latency via stall-free batching. (The
figure is illustrative and actual values will depend on the
model and workload characteristics.)

scheduling systems like Orca [75] is pipeline stalls or bubbles [49]. These appear in pipeline-parallelism (PP) deployments that are needed to scale LLM inference across several
nodes. In servers with high bandwidth connectivity such as
NVIDIA DGX A100 [16], tensor-parallelism (TP) [64] can
enable deployment of an LLM on up to 8 GPUs, supporting
large batch sizes with low latencies. However, TP can have
prohibitively high latencies when hyper-clusters are unavailable [33]. Thus, as an alternative to TP, pipeline-parallelism
(PP) [33, 55] is typically used across commodity networks.
Existing systems rely on micro-batches to mitigate pipeline
stalls or bubbles [49]. However, the standard micro-batch
based scheduling can still lead to pipeline bubbles due to the
unique characteristics of LLM inference. Specifically, LLM
inference consists of a mixture of varying length prefills and
decodes. The resulting schedule can thus have wildly varying runtimes across different micro-batches that waste GPU
cycles and degrade the overall system throughput.
To address these challenges, we propose Sarathi-Serve, a
scheduler to balance the throughput-latency tradeoff for scalable online LLM inference serving. Sarathi-Serve is based
on two key ideas: chunked-prefills and stall-free scheduling.
Chunked-prefills splits a prefill request into equal computesized chunks and computes a prompt’s prefill phase over multiple iterations (each with a subset of the prompt tokens).
Stall-free scheduling allows new requests to join a running
batch without pausing ongoing decodes. This involves constructing a batch by coalescing all the on-going decodes with
one (or more) prefill chunks from new requests such that each
batch reaches the pre-configured chunk size. Sarathi-Serve
builds upon iteration-level batching but with an important
distinction: it throttles the number of prefill tokens in each it-

18th USENIX Symposium on Operating Systems Design and Implementation

USENIX Association



<!-- PDF page break -->

eration while admitting new requests in a running batch. This
not only bounds the latency of each iteration, but also makes it
nearly independent of the total length of input prompts. This
way, Sarathi-Serve minimizes the effect of computing new
prefills on the TBT of ongoing decodes enabling both high
throughput and low TBT latency.
In addition, hybrid batches (consisting of prefill and decode
tokens) constructed by Sarathi-Serve have a near-uniform
compute requirement. With pipeline-parallelism, this allows
us to create balanced micro-batching based schedules that
significantly reduce pipeline bubbles and improve GPU utilization, thus allowing efficient and scalable deployments.
We evaluate Sarathi-Serve across different models and hardware — Mistral-7B on a single A100, Yi-34B on 2 A100
GPUs with 2-way tensor parallelism, LLaMA2-70B on 8
A40 GPUs, and Falcon-180B with 2-way pipeline and 4-way
tensor parallelism across 8 A100 GPUs connected over commodity ethernet. For Yi-34B, Sarathi-Serve improves system
serving capacity by up to 3.7× under different SLO targets.
Similarly for Mistral-7B, we achieve up to 2.6× higher serving capacity. Sarathi-Serve also reduces pipeline bubbles,
resulting in up to 5.6× gains in end-to-end serving capacity
for Falcon-180B deployed with pipeline parallelism.
The main contributions of our paper include:
1. We identify a number of pitfalls in the current LLM
serving systems, particularly in the context of navigating
the throughput-latency tradeoff.
2. We introduce two simple-yet-effective techniques,
chunked-prefills and stall-free batching, to improve the
performance of an LLM serving system.
3. We show generality through extensive evaluation over
multiple models, hardware, and parallelism strategies
demonstrating that Sarathi-Serve improves model serving capacity by up to an order of magnitude.

2

Background

In this section, we describe the typical LLM model architecture along with their auto-regressive inference process. We
also provide an overview of the scheduling policies and important performance metrics.

2.1

The Transformer Architecture

Popular large language models, like, GPT-3 [18], LLaMA
[66], Yi [24] etc. are decoder-only transformer models trained
on next token prediction tasks. These models consist of a
stack of layers identical in structure. Each layer contains two
modules – self-attention and feed-forward network (FFN).
Self-attention module: The self-attention module is central
to the transformer architecture [67], enabling each part of
a sequence to consider all previous parts for generating a
contextual representation. During the computation of selfattention, first the Query (Q), Key (K) and Value (V ) vectors

USENIX Association

corresponding to each input token are obtained via a linear
transformation. Next, the attention operator computes a semantic relationship among all tokens of a sequence. This
involves computing a dot-product of each Q vector with K
vectors of all preceding tokens of the sequence, followed by
a softmax operation to obtain a weight vector, which is then
used to compute a weighted average of the V vectors. This attention computation can be performed across multiple heads,
whose outputs are combined using a linear transformation.
Feed-forward network (FFN): FFN typically consists of two
linear transformations with a non-linear activation in between.
The first linear layer transforms an input token embedding of
dimension h to a higher dimension h2. This is followed by an
activation function, typically ReLU or GELU [27,46]. Finally,
the second linear layer, transforms the token embedding back
to the original dimension h.

2.2

LLM Inference Process

Autoregressive decoding: LLM inference consists of two distinct phases – a prefill phase followed by a decode phase. The
prefill phase processes the user’s input prompt and produces
the first output token. Subsequently, the decode phase generates output tokens one at a time wherein the token generated
in the previous step is passed through the model to generate
the next token until a special end-of-sequence token is generated. Note that the decode phase requires access to all the
keys and values associated with all the previously processed
tokens to perform the attention operation. To avoid repeated
recomputation, contemporary LLM inference systems store
activations in KV-cache [7, 64, 75].
A typical LLM prompt contains 100s-1000s of input tokens
Table 2, [76]. During the prefill phase all these prompt tokens
are processed in parallel in a single iteration. The parallel
processing allows efficient utilization of GPU compute. On
the contrary, the decode phase involves a full forward pass of
the model over a single token generated in the previous iteration. This leads to low compute utilization making decodes
memory-bound.
Batched LLM inference in multi-tenant environment: A
production serving system must deal with concurrent requests
from multiple users. Naively processing requests in a sequential manner leads to a severe under-utilization of GPU compute. In order to achieve higher GPU utilization, LLM serving
systems leverage batching to process multiple requests concurrently. This is particularly effective for the decode phase
processing which has lower computational intensity at low
batch sizes. Higher batch sizes allows the cost of fetching
model parameters to be amortized across multiple requests.
Recently, several complementary techniques have been proposed to optimize throughput by enabling support for larger
batch sizes. Kwon et al. propose PagedAttention [53], which
allows more requests to concurrently execute, eliminating
fragmentation in KV-cache. The use of Multi Query Attention

18th USENIX Symposium on Operating Systems Design and Implementation

119



<!-- PDF page break -->

Algorithm 1 Request-level batching. New requests are admitted only if there are no decodes left (line 3). This optimizes
TBT but wastes GPU compute in many decode-only iterations
(line 10) with potentially small batch sizes.
1: Initialize current batch B ← 0/
2: while True do
3:
if B = /0 then
4:
Rnew ← get_next_request()
5:
while can_allocate_request(Rnew ) do
6:
B ← B + Rnew
7:
8:
9:
10:
11:

Rnew ← get_next_request()
prefill(B)
else
decode(B)
B ← filter_finished_requests(B)

Algorithm 2 Iteration-level batching (vLLM). Prefills are executed eagerly (lines 8-9), potentially introducing a generation
stall for ongoing decodes (line 12).
1: Initialize current batch B ← 0/
2: while True do
3:
Bnew ← 0/
4:
5:
6:
7:
8:
9:
10:
11:
12:
13:

Rnew ← get_next_request()
while can_allocate_request(Rnew ) do
Bnew ← Bnew + Rnew
Rnew ← get_next_request()
if Bnew ̸= 0/ then
prefill(Bnew )
B ← B + Bnew
else
decode(B)
B ← filter_finished_requests(B)

(MQA) [61], Group Query Attention (GQA) [30] in leading
edge LLM models like LLaMA2 [66], Falcon [31] and Yi [24]
has also significantly helped in alleviating memory bottleneck
in LLM inference. For instance, LLaMA2-70B model has a
8× smaller KV-cache footprint compared to LLaMA-65B.

2.3

Multi-GPU LLM Inference

With ever-increasing growth in model sizes, it becomes necessary to scale LLMs to multi-GPU or even multi-node deployments [22, 59]. Furthermore, LLM inference throughput,
specifically that of the decode phase is limited by the maximum batch size we can fit on a GPU. Inference efficiency can
therefore benefit from model-parallelism which allows larger
batch sizes by sharding model weights across multiple GPUs.
Prior work has employed both tensor-parallelism (TP) [64]
and pipeline-parallelism (PP) [7, 72, 75] for this purpose.
TP shards each layer across the participating GPUs by splitting the model weights and KV-cache equally across GPU

120

workers. This way, TP can linearly scale per-GPU batch size.
However, TP involves a high communication cost due to two
all-reduce operations per layer – one in attention computation
and the other in FFN [64]. Moreover, since these communication operations are in the critical path, TP is preferred
only within a single node where GPUs are connected via high
bandwidth interconnects like NVLink.
Compared to TP, PP splits a model layer-wise, where each
GPU is responsible for a subset of layers. To keep all GPUs in
the ‘pipeline’ busy, micro-batching is employed. These microbatches move along the pipeline from one stage to the next at
each iteration. PP has much better compute-communication
ratio compared to TP, as it only needs to send activations once
for multiple layers of compute. Furthermore, PP requires communication only via point-to-point communication operations,
compared to the more expensive allreduces in TP. Thus, PP is
more efficient than TP when high-bandwidth interconnects
are unavailable e.g., in cross-node deployments.

2.4

Performance Metrics

There are two primary latency metrics of interest for LLM
serving: TTFT (time-to-first-token) and TBT (time-betweentokens). For a given request, TTFT measures the latency of
generating the first output token from the moment a request
arrives in the system. This metric reflects the initial responsiveness of the model. TBT on the other hand measures the
interval between the generation of consecutive output tokens
of a request, and affects the overall perceived fluidity of the
response. When system is under load, low throughput can lead
to large scheduling delays and consequently higher TTFT.
In addition, we use a throughput metric, Capacity, defined
as the maximum request load (queries-per-second) a system
can sustain while meeting certain latency targets. Higher
capacity is desirable because it reduces the cost of serving.

2.5

Scheduling Policies for LLM Inference

The scheduler is responsible for admission control and batching policy. For the ease of exposition, we investigate existing
LLM inference schedulers by broadly classifying them under
two categories – prefill-prioritizing and decode-prioritizing.
Conventional inference engines like FasterTransformer [7],
Triton Inference Server [17] use decode-prioritizing schedules with request-level batching i.e., they pick a batch of
requests and execute it until all requests in the batch complete (Algorithm 1). This approach reduces the operational
complexity of the scheduling framework but at the expense of
inefficient resource utilization. Different requests in a batch
typically have a large variation in the number of input and
output tokens. Request-level schedulers pad shorter requests
with zeros to match their length with the longest request in
the batch which results in wasteful compute and longer wait
times for pending requests [75].

18th USENIX Symposium on Operating Systems Design and Implementation

USENIX Association



<!-- PDF page break -->

To avoid wasted compute of request-level batching,
Orca [75] introduced a fine-grained iteration-level batching
mechanism where requests can dynamically enter and exit
a batch after each model iteration.(Algorithm 2). This approach can significantly increase system throughput and is
being used in many LLM inference serving systems today
e.g., vLLM [23], TensorRT-LLM [21], and LightLLM [12].
Current iteration-level batching systems such as vLLM [23]
and Orca [75] use prefill-prioritizing schedules that eagerly
admit new requests in a running batch at the first available
opportunity, e.g., whenever GPU memory becomes available.
Prioritizing prefills can improve throughput because it increases the batch size of subsequent decode iterations.

Motivation

In this section, we first analyse the cost of prefill and decode
operations. We then highlight the throughput-latency trade-off
and pipeline bubbles that appear in serving LLMs.

3.1

Cost Analysis of Prefill and Decode

As discussed in §2.2, while the prefill phase processes all input
tokens in parallel and effectively saturates GPU compute, the
decode phase processes only a single token at a time and is
very inefficient. Figure 3 illustrates throughput as a function of
batch size, and we can observe that while for decode iterations
throughput increases roughly linearly with batch size, prefill
throughput almost saturates even with a single request.
Takeaway-1: The two phases of LLM inference – prefill and
decode – demonstrate contrasting behaviors wherein batching
boosts decode phase throughput immensely but has little effect
on prefill throughput.
Figure 4 breaks down the prefill and decode compute times

USENIX Association

Sequence Length

linear
attention
others

100

64

32

8

0

16

50
1

Time (ms)

2K

1K

64

32

Batch Size

512

0

0

Figure 3: Throughput of the prefill and decode phases with
different batch sizes for Mistral-7B running on a single A100
GPU. We use prompt length of 1024 for both prefill and
decode experiments. Note that different y-axis, showing prefills are much more efficient than decode. Further, note that
batching boosts decode throughput almost linearly but has a
marginal effect on prefill throughput.

3

50
256

200

Decode

150

100

128

Time (ms)

400

16

Batch Size

8

4

2

0

Prefill

150

600

8

2K

Decode
800

1

Tokens per Second

4K

1

Tokens per Second

Prefill

Batch Size

Figure 4: Prefill and decode time with different input sizes
for Mistral-7B running on single A100 GPU. Linear layers
contribute to the majority of runtime in both prefill and decode
phases. Due to the low arithmetic intensity in decode batches,
the cost of linear operation for 1 decode token is nearly same
as 128 prefill tokens.

into linear, attention and others, and shows their individual
contributions. From the figure, we see that linear operators
contribute to the majority of the runtime cost. While attention
cost grows quadratically with sequence length, linear operators still contribute more than 80% to the total time even at
high sequence lengths. Therefore, optimizing linear operators
is important for improving LLM inference.
Low Compute Utilization during Decodes: Low compute
utilization during the decode phase is a waste of GPU’s processing capacity. To understand this further, we analyze the
arithmetic intensity of prefill and decode iterations. Since
the majority of the time in LLM inference is spent in linear
operators, we focus our analysis on them.
Matrix multiplication kernels overlap memory accesses
along with computation of math operations. The total execution time of an operation can be approximated to T =
max(Tmath , Tmem ), where Tmath and Tmem represent the time
spent on math and memory fetch operations respectively.
An operation is considered memory-bound if Tmath < Tmem .
Memory-bound operations have low Model FLOPs Utilization (MFU) [35]. On the other hand, compute-bound operations have low Model Bandwidth Utilization (MBU). When
Tmath = Tmem , both compute and memory bandwidth utilization are maximized. Arithmetic intensity quantifies the number of math operations performed per byte of data fetched
from the memory. At the optimal point, the arithmetic intensity of operation matches the FLOPS-to-Bandwidth ratio
of the device. Figure 5 shows arithmetic intensity as a function of the number of tokens in the batch for linear layers in
LLaMA2-70B running on four A100 GPUs. Prefill batches
amortize the cost of fetching weights of the linear operators
from HBM memory to GPU cache over a large number of
tokens, allowing it to have high arithmetic intensity. In contrast, decode batches have very low computation intensity.
Figure 6 shows the total execution time of linear operators in

18th USENIX Symposium on Operating Systems Design and Implementation

121



<!-- PDF page break -->

TP-2
TP-4

800

1200

Time (ms)

Arithmetic Intensity (FLOPs/bytes)

1000

Compute Bound Region - Low MBU

1400

1000
800

Prefill

600
400
200

600

Balanced - Sarathi-Serve

400

0

128

256

0

250

500

750

1000

1250

1500

1750

2000

Figure 5: Arithmetic intensity trend for LLaMA2-70B linear operations with different number of token running on
four A100s. Decode batches have low arithmetic intensity
i.e., they are bottlenecked by memory fetch time, leading to
low compute utilization. Prefill batches are compute bound
with sub-optimal bandwidth utilization. Sarathi-Serve forms
balanced batches by combining decodes and prefill chunks to
maximize both compute and bandwidth utilization.

2048

4096

Figure 6: Linear layer execution time as function of number of
tokens in a batch for LLaMA2-70B on A100(s) with different
tensor parallel degrees. When the number of tokens is small,
execution time is dictated by the cost of fetching weights from
HBM memory. Hence, execution time is largely stagnant in
the 128-512 tokens range, especially for higher tensor parallel
degrees. Once the number of tokens in the batch cross a
critical threshold, the operation become compute bound and
the runtime increases linearly with number of tokens.
Timeline

an iteration for LLaMA2-70B as a function of the number of
tokens. Note that execution time increases only marginally in
the beginning i.e., as long as the batch is in a memory-bound
regime, but linearly afterwards i.e., when the batch becomes
compute-bound.2
Takeaway-2: Decode batches operate in memory-bound
regime leaving compute underutilized. This implies that more
tokens can be processed along with a decode batch without
significantly increasing its latency.

Throughput-Latency Trade-off

Iteration-level batching improves system throughput but we
show that it comes at the cost of high TBT latency due to a
phenomenon we call generation stalls.
Figure 7 compares different scheduling policies. The example shows a timeline (left to right) of requests A, B, C
and D. Requests A and B are in decode phase at the start of
the interval and after one iteration, requests C and D enter
the system. Orca and vLLM both use FCFS iteration-level
batching with eager admission of prefill requests but differ in
their batch composition policy. Orca supports hybrid batches
composed of both prefill and decode requests whereas vLLM
only supports batches that contain either all prefill or all decode requests. Irrespective of this difference, both Orca and
vLLM can improve throughput by maximizing the batch size
2 Theoretically, we expect the operators to become compute-bound at

∼200 tokens on A100 GPUs, however, in practice we observe that it happens at ∼500-600 tokens for higher tensor parallel dimensions due to fixed
overheads.

Ad , Bd

Decodes for A, B stalled

vLLM

C, D enter

122

1024

Memory Bound Region - Low MFU

Decode
0

Number of Tokens

3.2

512

Number of tokens

200

Cp

Ad , Bd, Cd, Dd

Dp

…
Prefill
Prioritized
Schedules

TBT with
prefill interference

TBT without
prefill interference

C, D enter

Decodes for A, B stalled

Orca

Ad , Bd

Ad , Bd, Cd, Dd

Cp, Dp, Ad, Bd

…

A exits
C, D enter
Ad , Bd

Ad , Bd

FasterTransformer
Ad , Bd

Bd

A exits
C, D enter
Ad , Bd

Ad , Bd, Cp1

Sarathi-Serve
Ad , Bd, Cp2

A exits

Bd, Cd, Dp1

Prefills for C, D stalled
Bd

Cp, Dp

B exits
No stalls
Bd, Cd, Dp2

B exits

…

…

Decode
Prioritized
Schedule

Stall-free
Schedule

Figure 7: A generation stall occurs when one or more prefills
are scheduled in between consecutive decode iterations of
a request. A, B, C and D represent different requests. Subscript d represents a decode iteration, p represents a full prefill
and p0, p1 represent two chunked prefills of a given prompt.
vLLM induces generation stalls by scheduling as many prefills as possible before resuming ongoing decodes. Despite
supporting hybrid batches, Orca cannot mitigate generation
stalls because the execution time of batches containing long
prompts remains high. FasterTransformer is free of generation
stalls as it finishes all ongoing decodes before scheduling a
new prefill but compromises on throughput due to low decode
batch size. In contrast, Sarathi-Serve generates a schedule
that eliminates generation stalls yet delivers high throughput.

in subsequent decode iterations. However, eagerly scheduling
prefills of requests C and D delays the decodes of already
running requests A and B because an iteration that computes
one or more prefills can take several seconds depending on the

18th USENIX Symposium on Operating Systems Design and Implementation

USENIX Association



<!-- PDF page break -->

Timeline

Inference jobs only require forward computation and therefore one might expect that micro-batching can eliminate
GPU0
pipeline bubbles during inference. In fact, prior work on
GPU1
transformer inference, such as, FasterTransformer [7] and
Orca
FastServe [72] use micro-batches but do not mention pipelineMinimal Bubbles
bubbles. Recently proposed Orca [75] also suggests that
GPU0
GPU1
iteration-level scheduling eliminates bubbles in pipeline
Sarathi-Serve
scheduling (see Figure 8 in [75]). However, our experiments
show that even with iteration-level scheduling, pipeline bubFigure 8: A 2-way pipeline parallel iteration-level schedule
bles can waste significant GPU cycles with PP (§5.3).
in Orca across 4 requests (A,B,C,D) shows the existence of
Each micro-batch (or iteration) in LLM inference can repipeline bubbles due to non-uniform batch execution times.
quire a different amount of compute (and consequently has
Sarathi-Serve is able to minimize these stalls by creating
varying execution time), depending on the composition of
Timeline
uniform-compute batches.
prefill and decode tokens in the micro-batch (see Figure 8).
Decodes for A, B stalled
C, D enter
vLLM
We identify
… three types of bubbles during inference: (1) bubPrefill due to the varying number of prefill
bles
like
PB
TBT
with
1 that occur
TBT
without
lengths of input prompts. Therefore, prefill-prioritizing
schedPrioritized
prefill interference
prefill interference
Schedules
tokens in two consecutive
micro-batches (2) bubbles like PB2
ulers can introduce generation stalls for C, D
ongoing
decodes
enter
Decodes
for
A,
B
stalled
Orca
that
occur
due
to
different
compute
times of prefill and decode
…
resulting in latency spikes caused by high TBT.
A
exits one is followed by the other, and (3) bubbles like
stages
when
In contrast to iteration-level batching, request-level batchFasterTransformer Prefills for C, D stalled
C, D enter
Decode
PB3 that occur due
difference in decode compute times
… toPrioritized
ing systems such as FasterTransformer [7] do not schedule
Schedule
between
micro-batches
since the attention cost depends on
A
exits
B
exits
new requests until all the already running requests complete
the
accumulated
context
length (size of the KV-cache) and
No
stalls
Sarathi-Serve
C,
D
enter
their decode phase (line 3 in Algorithm 1). In Figure 7, the
… across requests.Stall-free
varies
For
Falcon-180B, a single prompt of 4k
Schedule
prefills for requests C and D get stalled until requests AAexits
and
B exits
tokens
takes
≈
1150
ms
to
execute compared to a decode only
B both exit the system. Therefore, decode-prioritizing sysiteration
with
batch
size
32
which would take about ≈ 200
tems provide low TBT latency albeit at the cost of low system
ms
to
execute.
Interleaving
of
these iteration could result in a
throughput. For example, Kwon et al. [53] show that iterationbubble
of
≈
950
ms.
These
pipeline
bubbles are wasted GPU
level batching with PagedAttention can achieve an order of
cycles
and
directly
correspond
to
a
loss in serving throughmagnitude higher throughput compared to FasterTransformer.
put
and
increased
latency.
This
problem
is aggravated with
One way to reduce latency spikes in iteration-level batching
increase
in
prompt
lengths
and
batch
size,
due to longer and
systems is to use smaller batch sizes as recommended in
more
frequent
prefill
iterations
respectively.
If we can ensure
Orca [75]. However, lowering batch size adversely impacts
that
each
micro-batch
performs
uniform
computation,
we can
throughput as shown in §2.2. Therefore, existing systems are
mitigate these pipeline bubbles.
forced to trade-off between throughput and latency depending
Takeaway-4: There can be a large variance in compute time
on the desired SLOs.
of LLM iterations depending on composition of prefill- and
Takeaway-3: The interleaving of prefills and decodes indecode-tokens in the batch. This can lead to significant bubvolves a trade-off between throughput and latency for current
bles when using pipeline-parallelism.
LLM inference schedulers. State-of-the-art systems today use
Bubble due to prefill
length variation

Ap, Bp

Cp, Dp

Bubble due to prefill
decode interference

Ad1 , Bd1

Ap, Bp

Ap1

Cd1 , Dd1

Cp, Dp

Ad1 , Bd1

Bp1

Ap2

Bp2

Ad1 , Cp1

Bd1 , Dp1

Ad2 , Cd1

Bd2 , Dd1

Ad3 , Cd2

Ap1

Bp1

Ap2

Bp2

Ad1 , Cp1

Bd1 , Dp1

Ad2 , Cd1

Bd2 , Dd1

Ad , Bd

Ad , Bd

Cp

Ad , Bd

Ad , Bd

Ad , Bd

Ad , Bd

Ad , Bd

Ad , Bd, Cp1

Ad , Bd, Cp2

Bd

Bd, Cd, Dp1

Pipeline Bubbles waste GPU Cycles

Pipeline-parallelism (PP) is a popular strategy for cross-node
deployment of large models, owing to its lower communication overheads compared to Tensor Parallelism (TP). A challenge with PP, however, is that it introduces pipeline bubbles
or periods of GPU inactivity as subsequent pipeline stages
have to wait for the completion of the corresponding microbatch in the prior stages. Pipeline bubbles is a known problem in training jobs, where they arise between the forward
and backward passes due to prior stages needing to wait for
the backward pass to arrive. Micro-batching is a common
technique used in PP training jobs to mitigate pipeline bubbles [33, 49, 55].

USENIX Association

Ad , Bd, Cd, Dd

Cp, Dp, Ad, Bd

prefill-prioritizing schedules that trade TBT latency for high
throughput.

3.3

Ad , Bd, Cd, Dd

Dp

Bd

Cp, Dp

Bd, Cd, Dp2

4

Sarathi-Serve: Design and Implementation

We now discuss the design and implementation of SarathiServe — a system that provides high throughput with predictable tail latency via two key techniques – chunked-prefills
and stall-free batching.

4.1

Chunked-prefills

As we show in §3.1, decode batches are heavily memory
bound with low arithmetic intensity. This slack in arithmetic
intensity presents an opportunity to piggyback additional computation in decode batches. Naively, this can be done by creating hybrid batches which combine the memory bound decodes
along with compute bound prefills. However, in many practical scenarios, input prompts contain several thousand tokens

18th USENIX Symposium on Operating Systems Design and Implementation

123



<!-- PDF page break -->

(a) Mistral-7B on one A100s with token budget of 256.

(b) LLaMA2-70B on four A100s with token budget of 512.

Figure 9: The incremental cost of coalescing prefills with decode batches. We consider two batching schemes – (i) Decode +
Full Prefill represents the hybrid batching of Orca wherein the entire prefill is executed in a single iteration along with ongoing
decodes. (ii) Decode + Chunked Prefill represents Sarathi-Serve wherein prefills are chunked before being coalesced with
ongoing decodes with a fixed token budget. Sarathi-Serve processes prefill tokens with much lower impact on the latency of
decodes. Further, the relative impact of Sarathi-Serve on latency reduces with higher decode batch size and context lengths.
on average e.g., Table 2 shows that the median prompt size
in openchat_sharegpt4 and arxiv_summarization datasets is
1730 and 7059 respectively. Combining these long prefills
with decode iterations would lead to high TBT latency.
To tackle this challenge, we present a technique called
chunked-prefills which allows computing large prefills in
small chunks across several iterations. Chunked-prefills is a
prefill splitting mechanism hinged on two key insights. First,
as discussed in §3.1, a prefill request with modest sequence
length can effectively saturate GPU compute. For example,
in Figure 4, prefill throughput starts saturating around sequence length of 512 tokens. Second, in many practical scenarios, input prompts contain several thousand tokens on average
(Table 2). This provides an opportunity to break large prefill
requests into smaller units of compute which are still large
enough to saturate GPU compute. In Sarathi-Serve, we leverage this mechanism to form batches with appropriate number
of tokens such that we can utilize the compute potential in
decode batches without violating the TBT SLO.

4.2 Stall-free batching

slack in decode iterations to execute prefills without delaying the execution of decode requests in the system. We call
this approach stall-free batching (Algorithm 3). Sarathi-Serve
first calculates the budget of maximum number of tokens that
can be executed in a batch based on user specified SLO. We
describe the considerations involved in determining this token budget in depth in §4.3. In every scheduling iteration,
we first pack all the running decodes in the next batch (lines
6-8 in Algorithm 3). After that, we include any partially completed prefill (lines 9-12). Only after all the running requests
have been accommodated, we admit new requests (lines 1320). When adding prefill requests to the batch, we compute
the maximum chunk size that can be accommodated within
the leftover token budget for that batch (lines 11, 15). By restricting the computational load in every iteration, stall-free
batching ensures that decodes never experience a generation
stall due to a co-running prefill chunk. We compare the latency for hybrid batches with and without chunked prefills in
Figure 9. Naive hybrid batching leads to dramatic increase
of up to 28.3× in the TBT latency compared to a decodeonly batch. In contrast, Sarathi-Serve provides a much tighter
bound on latency with chunking.

The Sarathi-Serve scheduler is an iteration-level scheduler
that leverages chunked-prefills and coalescing of prefills and
decodes to improve throughput while minimizing latency.
Unlike Orca and vLLM which stall existing decodes to execute prefills, Sarathi-Serve leverages the arithmetic intensity

Figure 7 shows the scheduling policy of Sarathi-Serve in
action, for the same example used in §3.2. The first iteration is
decode-only as there are no prefills to be computed. However,
after a new request C enters the system, Sarathi-Serve first
splits the prefill of C into two chunks and schedules them in

124

18th USENIX Symposium on Operating Systems Design and Implementation

USENIX Association



<!-- PDF page break -->

Algorithm 3 Stall-free batching with Sarathi-Serve. First the
batch is filled with with ongoing decode tokens (lines 6-8)
and optionally one prefill chunk from ongoing (lines 10-12).
Finally, new requests are added (lines 13-20) within the token
budget so as to maximize throughput with minimal latency
impact on the TBT of delaying the ongoing decodes.
1: Input: Tmax , Application TBT SLO.
2: Initialize token_budget, τ ← compute_token_buget(Tmax )
3: Initialize batch_num_tokens, nt ← 0
4: Initialize current batch B ← 0/
5: while True do

19:
20:

for R in B do
if is_prefill_complete(R) then
nt ← nt + 1
for R in B do
if not is_prefill_complete(R) then
c ← get_next_chunk_size(R, τ, nt )
nt ← nt + c
Rnew ← get_next_request()
while can_allocate_request(Rnew ) ∧ nt < τ do
c ← get_next_chunk_size(Rnew , τ, nt )
if c > 0 then
nt ← nt + c
B ← Rnew
else
break

21:
22:
23:
24:

process_hybrid_batch(B)
B ← filter_finished_requests(B)
nt ← 0

6:
7:
8:
9:
10:
11:
12:
13:
14:
15:
16:
17:
18:

subsequent iterations. At the same time, with stall-free batching, it coalesces the chunked prefills with ongoing decodes
of A and B. This way, Sarathi-Serve stalls neither decodes
nor prefills unlike existing systems, allowing Sarathi-Serve to
be largely free of latency spikes in TBT without compromising throughput. Furthermore, stall-free batching combined
with chunked-prefills also ensures uniform compute hybrid
batches in most cases, which helps reduce bubbles when using
pipeline parallelism, thereby enabling efficient and scalable
deployments.

4.3

Determining Token Budget

The token budget is determined based on two competing factors — TBT SLO requirement and chunked-prefills overhead.
From a TBT minimization point of view, a smaller token budget is preferable because iterations with fewer prefill tokens
have lower latency. However, smaller token budget can result
in excessive chunking of prefills resulting in overheads due
to 1) lower GPU utilization and 2) repeated KV-cache access
in the attention operation which we discuss below.

USENIX Association

During the computation of chunked-prefills, the attention
operation for every chunk of a prompt needs to access the
KV-cache of all prior chunks of the same prompt. This results
in increased memory reads from the GPU HBM even though
the computational cost is unchanged. For example, if a prefill
sequence is split into N chunks, then the first chunk’s KVcache is loaded N − 1 times, the second chunk’s KV-cache is
loaded N − 2 times, and so on. However, we find that even
at small chunk sizes attention prefill operation is compute
bound operation. In practice, there can be small overhead
associated with chunking due to fixed overheads of kernel
launch, etc. We present a detailed study of the overheads of
chunked-prefills in §5.4.
Thus, one needs to take into account the trade-offs between
prefill overhead and decode latency while determining the
token budget. This can be handled with a one-time profiling of
batches with different number of tokens and setting the token
budget to maximum number of tokens that can be packed in a
batch without violating TBT SLO.
Another factor that influences the choice of token budget
is the tile-quantization effect [13]. GPUs compute matmuls
by partitioning the given matrices into tiles and assigning
them to different thread blocks for parallel computation. Here,
each thread block refers to a group of GPU threads and computes the same number of arithmetic operations. Therefore,
matmuls achieve maximum GPU utilization when the matrix dimensions are divisible by the tile size. Otherwise, due
to tile-quantization, some thread blocks perform extraneous
computation [13]. We observe that tile-quantization can dramatically increase prefill computation time e.g., in some cases,
using chunk size of 257 can increase prefill time by 32% compared to that with chunk size 256.
Finally, when using pipeline parallelism the effect of token
budget on pipeline bubbles should also be taken into account.
Larger chunks lead to higher inter-batch runtime variations
that result in pipeline bubbles which results in lower overall
system throughput. On the other hand, picking a very small
token budget can lead to higher overhead due to lower arithmetic intensity and other fixed overheads.
Therefore, selecting a suitable token budget is a complex
decision which depends on the desired TBT SLO, parallelism
configuration, and specific hardware properties. We leverage
Vidur [28], a LLM inference profiler and simulator to determine the token budget that maximizes system capacity under
specific deployment scenario.

4.4

Implementation

We implement Sarathi-Serve on top of the open-source implementation of vLLM [23, 53]. We added support for paged
chunk prefill using FlashAttention v2 [38] and FlashInfer [74]
kernels. We use FlashAttention backend for all the evaluations in this paper due to its support for wider set of models.
We also extend the base vLLM codebase to support various

18th USENIX Symposium on Operating Systems Design and Implementation

125



<!-- PDF page break -->

Model

Attention
Mechanism

GPU
Configuration

Memory
Total (per-GPU)

Mistral-7B GQA-SW
1 A100
80GB (80GB)
GQA
2 A100s (TP2)
160GB (80GB)
Yi-34B
LLaMA2-70B
GQA
8 A40s (TP4-PP2)
384GB (48GB)
GQA
4 A100s×2 nodes (TP4-PP2) 640GB (80GB)
Falcon-180B

Table 1: Models and GPU configurations (GQA: groupedquery attention, SW: sliding window).
Dataset
openchat_sharegpt4
arxiv_summarization

Prompt Tokens
Median
P90
Std.
1730
7059

5696
12985

2088
3638

Output Tokens
Median P90 Std.
415
208

834
371

101
265

Table 2: Datasets used for evaluation.
scheduling policies, chunked prefills, pipeline parallelism and
an extensive telemetry system. We use NCCL [15] for both
pipeline and tensor parallel communication. Source code for
the project is available at https://github.com/microsoft/sarathiserve.

5

Evaluation

We evaluate Sarathi-Serve on a variety of popular models and
GPU configurations (see Table 1) and two datasets (see Table 2). We consider vLLM and Orca as baseline because they
represent the state-of-the-art for LLM inference. Our evaluation seeks to answer the following questions:
1. What is the maximum load a model replica can serve under
specific Service Level Objective (SLO) constraints with
different inference serving systems (§5.1) and how does
this load vary with varying SLO constraints (§5.2)?
2. How does Sarathi-Serve perform under various deployments such as TP and PP? (§5.3)
3. What is the overhead of chunked-prefills? (§5.4.1)
4. What is the effect of each of chunked-prefills and stall-free
batching in isolation as opposed to using them in tandem?
(§5.4.2)
Models and Environment: We evaluate Sarathi-Serve across
four different models Mistral-7B [51], Yi-34B [24], LLaMA270B [66] and Falcon-180B [31] – these models are among

Model
Mistral-7B
Yi-34B
LLaMA2-70B
Falcon-180B

relaxed SLO strict SLO
P99 TBT (s) P99 TBT (s)
0.5
1
5
5

0.1
0.2
1
1

Table 3: SLOs for different model configurations.

126

the best in their model size categories. We use two different
server configurations. For all models except LLaMA2-70B we
use Azure NC96ads v4 VMs, each equipped with 4 NVIDIA
80GB A100 GPUs, connected with pairwise NVLINK. The
machines are connected with a 100 Gbps ethernet connection. For LLaMA2-70B, we use a server with eight pairwise
connected NVIDIA 48GB A40 GPUs. We run Yi-34B in a 2way tensor parallel configuration (TP-2), and LLaMA2-70B
and Falcon-180B in a hybrid parallel configuration with four
tensor parallel workers and two pipeline stages for (TP4-PP2).
Workloads: In order to emulate the real-world serving scenarios, we generate traces by using the request
length characteristics from the openchat_sharegpt4 [68] and
arxiv_summarization [36] datasets (Table 2). The openchat_sharegpt4 trace contains user-shared conversations with
ChatGPT-4 [6]. A conversation may contain multiple rounds
of interactions between the user and chatbot. Each such interaction round is performed as a separate request to the system.
This multi-round nature leads to high relative variance in
the prompt lengths. In contrast, arxiv_summarization is a
collection of scientific publications and their summaries (abstracts) on arXiv.org [3]. This dataset contains longer prompts
and lower variance in the number of output tokens, and is
representative of LLM workloads such as Microsoft M365
Copilot [14] and Google Duet AI [10] etc. The request arrival
times are generated using Poisson distribution. We filter outliers of these datasets by removing requests with total length
more than 8192 and 16384 tokens, respectively.
Metrics: We focus on the median value for the TTFT since
this metric is obtained only once per user request and on the
99th percentile (P99) for TBT values since every decode token
results in a TBT latency value.

5.1

Capacity Evaluation

We evaluate Sarathi-Serve, Orca and vLLM on all four models
and both datasets under two different latency configurations:
relaxed and strict. Similar to Patel et al. [58], to account for
the intrinsic performance limitations of a model and hardware
pair, we define the SLO on P99 TBT to be equal to 5× and
25× the execution time of a decode iteration for a request
(with prefill length of 4k and 32 batch size) running without
any prefill interference for the strict and relaxed settings,
respectively. Table 3 shows a summary of the absolute SLO
thresholds. Note that the strict SLO represents the latency
target desired for interactive applications like chatbots. On
the other hand, the relaxed configuration is exemplary of
systems where the complete sequence of output tokens should
be generated within a predictable time limit but the TBT
constraints on individual tokens is not very strict. For all load
experiments, we ensure that the maximum load is sustainable,
i.e., the queuing delay does not blow up (we use a limit of 2
seconds on median scheduling delay).
Figure 10 and Figure 11 show the results of our capacity

18th USENIX Symposium on Operating Systems Design and Implementation

USENIX Association



<!-- PDF page break -->

2

2.78x

vLLM
2.15x

0

2.44x

4.00x

1

SLO-S

SLO-R

Mistral-7B

Orca

Sarathi-Serve

SLO-S

Max Capacity

Max Capacity

Orca

1.0
5.54x

SLO-S

1.97x
1.82x
1.94x

Max Capacity

Max Capacity

1.0

0.0

0.3

SLO-S

5.62x

SLO-R

SLO-S

SLO-R

Falcon-180B

4.60x

3.00x
4.20x

2.75x

0.2
0.1
0.0

SLO-S
SLO-R
Mistral-7B

4.69x

(a) Dataset: openchat_sharegpt4.

(a) Dataset: openchat_sharegpt4.

1.69x

6.31x

LLaMA2-70B

Yi-34B

0.5

Sarathi-Serve

0.5

0.0

SLO-R

vLLM

SLO-R

SLO-S

SLO-R

LLaMA2-70B

Yi-34B

SLO-S

SLO-R

Falcon-180B

(b) Dataset: arxiv_summarization.

(b) Dataset: arxiv_summarization.

Figure 10: Capacity (in queries per second) of Mistral-7B and
Yi-34B with different schedulers under strict (SLO-S) and
relaxed (SLO-R) latency SLOs.

Figure 11: Capacity of LLaMA2-70B and Falcon-180B (models with pipeline parallelism) with different schedulers under
strict (SLO-S) and relaxed (SLO-R) latency SLOs.

experiments. Sarathi-Serve consistently outperforms Orca
and vLLM in all cases across models and workloads. Under
strict SLO, Sarathi-Serve can sustain up to 4.0× higher load
compared to Orca and 3.7× higher load than vLLM under
strict SLO (Yi-34B, openchat_sharegpt4). For larger models
using pipeline parallelism, Sarathi-Serve achieves gains of up
to 6.3× and 4.3× compared to Orca and vLLM respectively
(LLaMA2-70B, openchat_sharegpt4) due to few pipeline bubbles.
We observe that in most scenarios, Orca and vLLM violate
the P99 TBT latency SLO before they can reach their maximum serviceable throughput. Thus, we observe relaxing the
latency target leads to considerable increase in their model
serving capacity. In Sarathi-Serve, one can adjust the chunk
size based on the desired SLO. Therefore, we use a strict
token budget and split prompts into smaller chunks when
operating under strict latency SLO. This reduces system efficiency marginally but allows us to achieve lower tail latency.
On the other hand, when the latency constraint is relaxed,
we increase the token budget to allow more efficient prefills.
We use token budget of 2048 and 512 for all models under
the relaxed and strict settings, respectively, except for the
LLaMA2-70B relaxed configuration where we use token budget of 1536 to reduce the impact of pipeline bubbles. The
system performance can be further enhanced by dynamically
varying the token budget based on workload characteristics.
We leave this exploration for future work.

USENIX Association

We further notice that vLLM significantly outperforms
Orca under relaxed setting. The reason for this is two-fold.
First, Orca batches prompts for multiple requests together
(max sequence length * batch size compared to max sequence
length in vLLM), which can lead to even higher tail latency
in some cases. Second, vLLM supports a much larger batch
size compared to Orca. The lower batch size in Orca is due to
the lack of PagedAttention and the large activation memory
footprint associated with processing batches with excessively
large number of tokens.
Finally, note that the capacity of each system is
higher for openchat_sharegpt4 dataset compared to the
arxiv_summarization dataset. This is expected because
prompts in the arxiv_summarization datasets are much longer
- 7059 vs 1730 median tokens as shown in Table 2. The larger
prompts makes Orca and vLLM more susceptible to latency
violations due to higher processing time of these longer prefills.

5.2

Throughput-Latency Tradeoff

To fully understand the throughput-latency tradeoff in LLM
serving systems, we vary the P99 TBT latency SLO and observe the impact on system capacity for vLLM and SarathiServe. Figure 12 shows the results for Mistral-7B and Yi34B models with five different SLO values for the openchat_sharegpt4 dataset.

18th USENIX Symposium on Operating Systems Design and Implementation

127



<!-- PDF page break -->

Mistral-7B

Max Capacity

2.5

1.25

0.2
0.1
0.0

1.5
1.0

8

16

32

64

Batch Size

128

(a) TBT (Falcon-180B).

0.5

0.10

0.15

0.20

0.25

0.30

0.35

P99 TBT SLO (s)

0.40

0.45

0.50

Yi-34B

1.4
1.2
1.0

1.00

vLLM TP8
vLLM TP4:PP2
Sarathi-Serve TP4:PP2

0.75
0.50
0.25
0.00

SLO-S

SLO

SLO-R

(b) Capacity (Falcon-180B).

Figure 13: TP scales poorly across nodes. (a) Median TBT for
decode-only batches: cross node TP increases median TBT
by more than 2× compared to a 4-way TP within node and
PP across nodes. (b) Capacity under strict (SLO-S) and relaxed (SLO-R) latency SLOs: Sarathi-Serve increases Falcon180B’s serving capacity by 4.3× and 3.6× over vLLM’s TPonly and hybrid-parallel configurations under strict SLOs.

0.8

5.3

0.6

Making Pipeline Parallel Viable

0.4
0.2
0.0

0.2

0.3

0.4

0.5

0.6

0.7

P99 TBT SLO (s)

0.8

0.9

1.0

Figure 12: Latency – Throughput tradeoff in vLLM and
Sarathi-Serve for Mistral-7B and Yi-34B models on openchat_sharegpt4 dataset. We evaluate vLLM with three different max batch sizes of 32, 64 and 128. For Sarathi-Serve, we
consider token budget of 512 and 2048 with max batch size
of 128. Sarathi-Serve delivers 3.5× higher capacity under
stringent SLOs for Yi-34B using Stall-free batching.

We evaluate vLLM with three different batch sizes in an
attempt to navigate the latency-throughput trade-off as prescribed by Yu et al. [75]. The maximum capacity of vLLM
gets capped due to generation stalls under stringent TBT
SLOs. Notably, the capacity of vLLM remains largely identical for all the three batch size settings. This implies that
even though PagedAttention enables large batch sizes with
efficient memory management – in practical situations with
latency constraints, vLLM cannot leverage the large batch
size due to the steep latency-throughput tradeoff made by it’s
prefill-prioritizing scheduler.
On the other hand, the latency-throughput tradeoff in
Sarathi-Serve can be precisely controlled by varying the token
budget. Sarathi-Serve achieves 3.5× higher capacity compared to vLLM under strict SLO (100ms, Mistral-7B) using a
small token budget of 512. For scenarios with more relaxed
SLO constraints, picking a larger token budget of 2048 allows
Sarathi-Serve to operate more efficiently resulting in 1.65×
higher capacity compared to vLLM (1s, Yi-34B).

128

TP8
TP4:PP2

0.3

2.0

0.0

Max Capacity

SS-2048

Max Capacity

vLLM-128
SS-512

P50 TBT (s)

vLLM-32
vLLM-64

We now show that Sarathi-Serve makes it feasible to efficiently serve LLM inference across commodity networks
with efficient pipeline parallelism. For these experiments, we
run Falcon-180B over two nodes, each with four A100 GPUs,
connected over 100 Gbps Ethernet. We evaluate model capacity under three configurations: vLLM with 8-way TP, vLLM
with our pipeline-parallel implementation and Sarathi-Serve
with pipeline-parallel. For PP configurations, we do 4-way
TP within node and 2-way PP across nodes.
Figure 13a shows the latency for decode-only batches for
Falcon-180B with purely tensor parallel TP-8 deployment
compared to a TP-4 PP-2 hybrid parallel configuration. We
observe that the median latency for tensor parallelism is ∼ 2×
higher than pipeline parallelism. This is because TP incurs
high communication overhead due to cross-node all-reduces.
Figure 13b shows the capacity for tensor and hybrid parallel configurations for Falcon-180B on openchat_sharegpt4
dataset. Note that unlike the hybrid parallel configuration, TP
achieves low capacity even under the relaxed SLO due to
high latency. Even though vLLM can support a fairly high
load with hybrid parallelism under relaxed SLO, it’s performance drops sharply under the strict regime due to pipeline
bubbles. Sarathi-Serve on the other hand, leverages chunkedprefills to reduce the variation in the execution time between
microbatches to avoid pipeline bubbles, resulting in a 1.48×
increase in capacity under relaxed SLOs and 3.6× increase
in capacity under strict SLOs.

5.4

Ablation Study

In this subsection, we conduct an ablation study on different
aspects on Sarathi-Serve. In particular, we are interested in
answering the following two questions: 1) what is the effect of

18th USENIX Symposium on Operating Systems Design and Implementation

USENIX Association



<!-- PDF page break -->

512

1024

stalls. When used together, Sarathi-Serve improves performance along both dimensions.

2048

Overhead

1.50
1.25
1.00
0.75

6

0.25
0.00

2K

4K

Prefill Length

8K

Figure 14: Overhead of chunked-prefills in prefill computation
for Yi-34B (TP-2) normalized to the cost of no-chunking,
shown for various prompt lengths using chunk lengths of 512,
1024 and 2048.
Scheduler
hybrid-batching-only
chunked-prefills-only
Sarathi-Serve (combined)

openchat_sharegpt4 arxiv_summarization
P50 TTFT P99 TBT P50 TTFT P99 TBT
0.53
1.04
0.76

0.68
0.17
0.14

3.78
5.38
3.90

1.38
0.20
0.17

Table 4: TTFT and TBT latency measured in seconds for
hybrid-batching and chunked-prefills used in isolation as well
as when they are used in tandem, evaluated over 128 requests
for Yi-34B running on two A100s with a token budget of
1024. By using both hybrid-batching and chunked-prefills,
Sarathi-Serve is able to lower both TTFT and TBT.
chunking on prefill throughput, and 2) analyzing the impact of
hybrid-batching and chunking on latency. While we provide
results only for a few experiments in this section, all the trends
discussed below are consistent across various model-hardware
combinations.
5.4.1

Overhead of chunked-prefills

Figure 14 shows how much overhead chunking adds in Yi34B – on overall prefill runtime. As expected, smaller chunks
introduce higher overhead as shown by the gradually decreasing bar heights in Figure 14. However, even with the smallest
chunk size of 512, we observe a moderate overhead of at
most ∼25%. Whereas with the larger token budget of 2048,
chunked prefills have almost negligible overhead.
5.4.2

Related Work

0.50

Impact of individual techniques

Finally, Table 4 shows the TTFT and TBT latency with
each component of Sarathi-Serve evaluated in isolation i.e.,
chunked-prefills-only, hybrid-batching-only (mixed batches
with both prefill and decode requests) and when they are used
in tandem. These results show that the two techniques work
best together: chunked-prefills-only increases TTFT as prefill
chunks are slightly inefficient whereas hybrid-batching-only
increases TBT because long prefills can still create generation

USENIX Association

Model serving systems: Systems such as Clipper [37],
TensorFlow-Serving [56], Clockwork [45] and BatchMaker [44] study various placement, caching and batching
strategies for model serving. However, these systems fail to
address the challenges of auto-regressive transformer inference. More recently, systems such as Orca [75], vLLM [53],
FlexGen [63], FasterTransformers [7], LightSeq [70], and
TurboTransformers [42] propose domain-specific optimizations for transformer inference. FlexGen [63] optimizes LLM
inference for throughput in resource-constrained offline scenarios i.e., it is not suitable for online serving. FastServe [72]
proposed a preemptive scheduling framework for LLM inference to minimize the job completion times. We present a
detailed comparison with Orca and vLLM as they represent
the state-of-the-art in LLM inference.
Another approach that has emerged recently is to disaggregate the prefill and decode phases on different replicas as
proposed in SplitWise, DistServe and TetriInfer [47, 58, 77].
These solutions can entirely eliminate the interference between prefills and decodes. However, disaggregation requires
migrating the KV cache of each request upon the completion of its prefill phase which could be challenging in the
absence of high-bandwidth interconnects between different
replicas. In addition, this approach also under-utilizes the
GPU memory capacity of the prefill replicas i.e., only the decode replicas are responsible for storing the KV cache. On the
positive side, disaggregated approaches can execute prefills
with maximum efficiency (and therefore yield better TTFT)
unlike chunked prefills that are somewhat slower than full
prefills. We leave a quantitative comparison between SarathiServe and disaggregation-based solutions for future work.
Recently, Sheng et al. [62] proposed modification to
iteration-level batching algorithm to ensure fairness among
clients in a multi-tenant environment. FastServe [72] uses a
preemption based scheduling mechanism to mitigate head-ofthe-line blocking. Such algorithmic optimizations are complimentary to our approach and can benefit from lower prefilldecode interference enabled by Sarathi-Serve. Another recent
system, APIServe [26] adopted chunked prefills from Sarathi
to utilize wasted compute in decode batches for ahead-of-time
prefill recomputation for multi-turn API serving.
Improving GPU utilization for transformers: Recent works
have proposed various optimizations to improve the hardware
utilization for transformers. FasterTransformer uses modelspecific GPU kernel implementations. CocoNet [50] and [69]
aim to overlap compute with communication to improve GPU
utilization: these techniques are specially useful while using a high degree of tensor-parallel for distributed models

18th USENIX Symposium on Operating Systems Design and Implementation

129



<!-- PDF page break -->

where communication time can dominate compute. Further,
the cost of computing self-attention grows quadratically with
sequence length and hence can become significant for long
contexts. [38,39,60] have proposed various techniques to minimize the memory bottlenecks of self-attention with careful
tiling and work partitioning. In addition, various parallelization strategies have been explore to optimize model placement.
These techniques are orthogonal to Sarathi-Serve.
Model optimizations: A significant body of work around
model innovations has attempted to address the shortcomings
of transformer-based language models or to take the next
leap forward in model architectures, beyond transformers. For
example, multi-query attention [61] shares the same keys
and values across all the attention heads to reduce the size
of the KV-cache, allowing to fit a larger batch size on the
GPUs. Several recent works have also shown that the model
sizes can be compressed significantly using quantization [40,
41, 43, 73]. Mixture-of-expert models are aimed primarily at
reducing the number of model parameters that get activated
in an iteration [32, 48, 54]. More recently, retentive networks
have been proposed as a successor to transformers [65]. In
contrast, we focus on addressing the performance issues of
popular transformer models from a GPU’s perspective.

References
[1] Amazon codewhisperer. https://aws.amazon.com/
codewhisperer/.
[2] Anthropic claude. https://claude.ai.
[3] arxiv.org e-print archive. https://arxiv.org/.
[4] Bing ai. https://www.bing.com/chat.
[5] Character ai. https://character.ai.
[6] Chatgpt. https://chat.openai.com.
[7] Faster Transformer. https://github.com/NVIDIA/
FasterTransformer.
[8] Github copilot.
copilot.

https://github.com/features/

[9] Google bard. https://bard.google.com.
[10] Google duet ai. https://workspace.google.com/
solutions/ai/.
[11] Komo. https://komo.ai/.

7

Conclusion

Optimizing LLM inference for high throughput and low latency is desirable but challenging. We presented a broad characterization of existing LLM inference schedulers by dividing
them into two categories – prefill-prioritizing and decodeprioritizing. In general, we argue that the former category is
better at optimizing throughput whereas the latter is better
at optimizing TBT latency. However, none of them is ideal
when optimizing throughput and latency are both important.
To address this tradeoff, we introduce Sarathi-Serve—
a system that instantiates a novel approach comprised of
chunked-prefills and stall-free batching. Sarathi-Serve chunks
input prompts into smaller units of work to create stall-free
schedules. This way, Sarathi-Serve can add new requests in a
running batch without pausing ongoing decodes. Our evaluation shows that Sarathi-Serve improves the serving capacity
of Mistral-7B by up to 2.6× on a single A100 GPU and up to
5.6× for Falcon-180B on 8 A100 GPUs.

8

Acknowledgement

We would like to thank OSDI reviewers and our shepherd for
their insightful feedback. This research is partly supported
by GT Cloud Hub, under the auspices of the Institute for
Data Engineering and Science (IDEaS), with funding from
Microsoft, and the Center for Research into Novel Compute
Hierarchies (CRNCH) at Georgia Tech.

130

[12] Lightllm: A light and fast inference service for llm.
https://github.com/ModelTC/lightllm.
[13] Matrix multiplication background user’s
https://docs.nvidia.com/deeplearning/
performance/dl-performance-matrixmultiplication/index.html.

guide.

[14] Microsoft copilot. https://www.microsoft.com/enus/microsoft-copilot.
[15] Nvidia collective communications library (nccl). https:
//developer.nvidia.com/nccl.
[16] Nvidia dgx platform. https://www.nvidia.com/enus/data-center/dgx-platform/.
[17] NVIDIA
Triton
Dynamic
Batching.
https://docs.nvidia.com/
deeplearning/triton-inferenceserver/user-guide/docs/user_guide/
model_configuration.html#dynamic-batcher.
[18] Openai gpt-3: Understanding the architecture.
https://www.theaidream.com/post/openai-gpt3-understanding-the-architecture.
[19] Perplexity ai. https://www.perplexity.ai/.
[20] Replit ghostwriter.
ghostwriter.

18th USENIX Symposium on Operating Systems Design and Implementation

https://replit.com/site/

USENIX Association



<!-- PDF page break -->

[21] Tensorrt-llm: A tensorrt toolbox for optimized large
language model inference. https://github.com/
NVIDIA/TensorRT-LLM.

Mona Diab, Zornitsa Kozareva, and Ves Stoyanov. Efficient large scale language modeling with mixtures of
experts, 2022.

[22] Using NVIDIA’s AI/ML Frameworks for Generative AI on VMware vSphere.
https:
//core.vmware.com/blog/using-nvidias-aimlframeworks-generative-ai-vmware-vsphere.

[33] Sanjith Athlur, Nitika Saran, Muthian Sivathanu, Ramachandran Ramjee, and Nipun Kwatra. Varuna: scalable, low-cost training of massive deep learning models.
In Proceedings of the Seventeenth European Conference
on Computer Systems, pages 472–487, 2022.

[23] vllm: Easy, fast, and cheap llm serving for everyone.
https://github.com/vllm-project/vllm.
[24] Yi series of large language models trained from scratch
by developers at 01.AI. https://huggingface.co/
01-ai/Yi-34B-200K.
[25] You.com. https://you.com/.
[26] Reyna Abhyankar, Zijian He, Vikranth Srivatsa, Hao
Zhang, and Yiying Zhang. Apiserve: Efficient api
support for large-language model inferencing. arXiv
preprint arXiv:2402.01869, 2024.
[27] Abien Fred Agarap. Deep learning using rectified linear
units (relu), 2019.
[28] Amey Agrawal, Nitin Kedia, Jayashree Mohan, Ashish
Panwar, Nipun Kwatra, Bhargav S Gulavani, Ramachandran Ramjee, and Alexey Tumanov. Vidur: A large-scale
simulation framework for llm inference. Proceedings of
The Seventh Annual Conference on Machine Learning
and Systems, 2024, Santa Clara, 2024.
[29] Amey Agrawal, Ashish Panwar, Jayashree Mohan,
Nipun Kwatra, Bhargav S. Gulavani, and Ramachandran
Ramjee. Sarathi: Efficient llm inference by piggybacking decodes with chunked prefills, 2023.
[30] Joshua Ainslie, James Lee-Thorp, Michiel de Jong, Yury
Zemlyanskiy, Federico Lebrón, and Sumit Sanghai. Gqa:
Training generalized multi-query transformer models
from multi-head checkpoints, 2023.
[31] Ebtesam Almazrouei, Hamza Alobeidli, Abdulaziz
Alshamsi, Alessandro Cappelli, Ruxandra Cojocaru,
Mérouane Debbah, Étienne Goffinet, Daniel Hesslow,
Julien Launay, Quentin Malartic, Daniele Mazzotta,
Badreddine Noune, Baptiste Pannier, and Guilherme
Penedo. The falcon series of open language models,
2023.
[32] Mikel Artetxe, Shruti Bhosale, Naman Goyal, Todor Mihaylov, Myle Ott, Sam Shleifer, Xi Victoria Lin, Jingfei
Du, Srinivasan Iyer, Ramakanth Pasunuru, Giri Anantharaman, Xian Li, Shuohui Chen, Halil Akin, Mandeep Baines, Louis Martin, Xing Zhou, Punit Singh
Koura, Brian O’Horo, Jeff Wang, Luke Zettlemoyer,

USENIX Association

[34] Tom Brown, Benjamin Mann, Nick Ryder, Melanie
Subbiah, Jared D Kaplan, Prafulla Dhariwal, Arvind
Neelakantan, Pranav Shyam, Girish Sastry, Amanda
Askell, et al. Language models are few-shot learners. Advances in neural information processing systems,
33:1877–1901, 2020.
[35] Aakanksha Chowdhery, Sharan Narang, Jacob Devlin, Maarten Bosma, Gaurav Mishra, Adam Roberts,
Paul Barham, Hyung Won Chung, Charles Sutton, Sebastian Gehrmann, Parker Schuh, Kensen Shi, Sasha
Tsvyashchenko, Joshua Maynez, Abhishek Rao, Parker
Barnes, Yi Tay, Noam Shazeer, Vinodkumar Prabhakaran, Emily Reif, Nan Du, Ben Hutchinson, Reiner
Pope, James Bradbury, Jacob Austin, Michael Isard, Guy
Gur-Ari, Pengcheng Yin, Toju Duke, Anselm Levskaya,
Sanjay Ghemawat, Sunipa Dev, Henryk Michalewski,
Xavier Garcia, Vedant Misra, Kevin Robinson, Liam Fedus, Denny Zhou, Daphne Ippolito, David Luan, Hyeontaek Lim, Barret Zoph, Alexander Spiridonov, Ryan Sepassi, David Dohan, Shivani Agrawal, Mark Omernick,
Andrew M. Dai, Thanumalayan Sankaranarayana Pillai, Marie Pellat, Aitor Lewkowycz, Erica Moreira, Rewon Child, Oleksandr Polozov, Katherine Lee, Zongwei Zhou, Xuezhi Wang, Brennan Saeta, Mark Diaz,
Orhan Firat, Michele Catasta, Jason Wei, Kathy MeierHellstern, Douglas Eck, Jeff Dean, Slav Petrov, and
Noah Fiedel. Palm: Scaling language modeling with
pathways. CoRR, abs/2204.02311, 2022.
[36] Arman Cohan, Franck Dernoncourt, Doo Soon Kim,
Trung Bui, Seokhwan Kim, Walter Chang, and Nazli
Goharian. A discourse-aware attention model for abstractive summarization of long documents. In Proceedings of the 2018 Conference of the North American
Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 2 (Short
Papers), pages 615–621, New Orleans, Louisiana, June
2018. Association for Computational Linguistics.
[37] Daniel Crankshaw, Xin Wang, Guilio Zhou, Michael J
Franklin, Joseph E Gonzalez, and Ion Stoica. Clipper:
A {Low-Latency} online prediction serving system. In
14th USENIX Symposium on Networked Systems Design
and Implementation (NSDI 17), pages 613–627, 2017.

18th USENIX Symposium on Operating Systems Design and Implementation

131



<!-- PDF page break -->

[38] Tri Dao. Flashattention-2: Faster attention with better
parallelism and work partitioning, 2023.

parallelism. Advances in neural information processing
systems, 32, 2019.

[39] Tri Dao, Daniel Y. Fu, Stefano Ermon, Atri Rudra,
and Christopher Ré. Flashattention: Fast and memoryefficient exact attention with io-awareness, 2022.

[50] Abhinav Jangda, Jun Huang, Guodong Liu, Amir
Hossein Nodehi Sabet, Saeed Maleki, Youshan Miao,
Madanlal Musuvathi, Todd Mytkowicz, and Olli
Saarikivi. Breaking the computation and communication abstraction barrier in distributed machine
learning workloads. In Proceedings of the 27th ACM
International Conference on Architectural Support
for Programming Languages and Operating Systems,
ASPLOS ’22, page 402–416, New York, NY, USA,
2022. Association for Computing Machinery.

[40] Tim Dettmers, Mike Lewis, Younes Belkada, and Luke
Zettlemoyer. Llm.int8(): 8-bit matrix multiplication for
transformers at scale, 2022.
[41] Tim Dettmers, Artidoro Pagnoni, Ari Holtzman, and
Luke Zettlemoyer. Qlora: Efficient finetuning of quantized llms, 2023.
[42] Jiarui Fang, Yang Yu, Chengduo Zhao, and Jie Zhou.
Turbotransformers: an efficient GPU serving system
for transformer models. In PPoPP ’21: 26th ACM SIGPLAN Symposium on Principles and Practice of Parallel
Programming, Virtual Event, Republic of Korea, February 27- March 3, 2021, pages 389–402. ACM, 2021.

[51] Albert Q Jiang, Alexandre Sablayrolles, Arthur Mensch,
Chris Bamford, Devendra Singh Chaplot, Diego de las
Casas, Florian Bressand, Gianna Lengyel, Guillaume
Lample, Lucile Saulnier, et al. Mistral 7b. arXiv preprint
arXiv:2310.06825, 2023.

[43] Elias Frantar, Saleh Ashkboos, Torsten Hoefler, and Dan
Alistarh. Gptq: Accurate post-training quantization for
generative pre-trained transformers, 2023.

[52] Jared Kaplan, Sam McCandlish, Tom Henighan, Tom B.
Brown, Benjamin Chess, Rewon Child, Scott Gray, Alec
Radford, Jeffrey Wu, and Dario Amodei. Scaling laws
for neural language models. CoRR, abs/2001.08361,
2020.

[44] Pin Gao, Lingfan Yu, Yongwei Wu, and Jinyang Li. Low
latency rnn inference with cellular batching. In Proceedings of the Thirteenth EuroSys Conference, EuroSys ’18,
New York, NY, USA, 2018. Association for Computing
Machinery.
[45] Arpan Gujarati, Reza Karimi, Safya Alzayat, Wei Hao,
Antoine Kaufmann, Ymir Vigfusson, and Jonathan
Mace. Serving {DNNs} like clockwork: Performance
predictability from the bottom up. In 14th USENIX
Symposium on Operating Systems Design and Implementation (OSDI 20), pages 443–462, 2020.
[46] Dan Hendrycks and Kevin Gimpel. Gaussian error linear
units (gelus), 2023.
[47] Cunchen Hu, Heyang Huang, Liangliang Xu, Xusheng
Chen, Jiang Xu, Shuang Chen, Hao Feng, Chenxi Wang,
Sa Wang, Yungang Bao, et al. Inference without interference: Disaggregate llm inference for mixed downstream
workloads. arXiv preprint arXiv:2401.11181, 2024.
[48] Haiyang Huang, Newsha Ardalani, Anna Sun, Liu Ke,
Hsien-Hsin S. Lee, Anjali Sridhar, Shruti Bhosale,
Carole-Jean Wu, and Benjamin Lee. Towards moe deployment: Mitigating inefficiencies in mixture-of-expert
(moe) inference, 2023.
[49] Yanping Huang, Youlong Cheng, Ankur Bapna, Orhan
Firat, Dehao Chen, Mia Chen, HyoukJoong Lee, Jiquan
Ngiam, Quoc V Le, Yonghui Wu, et al. Gpipe: Efficient training of giant neural networks using pipeline

132

[53] Woosuk Kwon, Zhuohan Li, Siyuan Zhuang, Ying
Sheng, Lianmin Zheng, Cody Hao Yu, Joseph Gonzalez,
Hao Zhang, and Ion Stoica. Efficient memory management for large language model serving with pagedattention. SOSP ’23, page 611–626, New York, NY, USA,
2023. Association for Computing Machinery.
[54] Jiamin Li, Yimin Jiang, Yibo Zhu, Cong Wang, and
Hong Xu. Accelerating distributed MoE training and
inference with lina. In 2023 USENIX Annual Technical
Conference (USENIX ATC 23), pages 945–959, Boston,
MA, July 2023. USENIX Association.
[55] Deepak Narayanan, Aaron Harlap, Amar Phanishayee,
Vivek Seshadri, Nikhil R Devanur, Gregory R Ganger,
Phillip B Gibbons, and Matei Zaharia. Pipedream: generalized pipeline parallelism for dnn training. In Proceedings of the 27th ACM Symposium on Operating
Systems Principles, pages 1–15, 2019.
[56] Christopher Olston, Noah Fiedel, Kiril Gorovoy,
Jeremiah Harmsen, Li Lao, Fangwei Li, Vinu
Rajashekhar, Sukriti Ramesh, and Jordan Soyke.
Tensorflow-serving: Flexible, high-performance ml
serving, 2017.
[57] OpenAI.
GPT-4 technical report.
abs/2303.08774, 2023.

18th USENIX Symposium on Operating Systems Design and Implementation

CoRR,

USENIX Association



<!-- PDF page break -->

[58] Pratyush Patel, Esha Choukse, Chaojie Zhang, Íñigo
Goiri, Aashaka Shah, Saeed Maleki, and Ricardo Bianchini. Splitwise: Efficient generative llm inference using
phase splitting, 2023.
[59] Reiner Pope, Sholto Douglas, Aakanksha Chowdhery, Jacob Devlin, James Bradbury, Anselm Levskaya,
Jonathan Heek, Kefan Xiao, Shivani Agrawal, and Jeff
Dean. Efficiently scaling transformer inference, 2022.
[60] Markus N. Rabe and Charles Staats. Self-attention does
not need o(n2 ) memory, 2022.
[61] Noam Shazeer. Fast transformer decoding: One writehead is all you need, 2019.
[62] Ying Sheng, Shiyi Cao, Dacheng Li, Banghua Zhu,
Zhuohan Li, Danyang Zhuo, Joseph E Gonzalez, and
Ion Stoica. Fairness in serving large language models.
arXiv preprint arXiv:2401.00588, 2023.
[63] Ying Sheng, Lianmin Zheng, Binhang Yuan, Zhuohan
Li, Max Ryabinin, Daniel Y. Fu, Zhiqiang Xie, Beidi
Chen, Clark Barrett, Joseph E. Gonzalez, Percy Liang,
Christopher Ré, Ion Stoica, and Ce Zhang. Flexgen:
High-throughput generative inference of large language
models with a single gpu, 2023.
[64] Mohammad Shoeybi, Mostofa Patwary, Raul Puri,
Patrick LeGresley, Jared Casper, and Bryan Catanzaro.
Megatron-lm: Training multi-billion parameter language
models using gpu model parallelism. arXiv preprint
arXiv:1909.08053, 2019.
[65] Yutao Sun, Li Dong, Shaohan Huang, Shuming Ma,
Yuqing Xia, Jilong Xue, Jianyong Wang, and Furu Wei.
Retentive network: A successor to transformer for large
language models, 2023.
[66] Hugo Touvron, Louis Martin, Kevin Stone, Peter Albert, Amjad Almahairi, Yasmine Babaei, Nikolay Bashlykov, Soumya Batra, Prajjwal Bhargava, Shruti Bhosale,
Dan Bikel, Lukas Blecher, Cristian Canton Ferrer, Moya
Chen, Guillem Cucurull, David Esiobu, Jude Fernandes, Jeremy Fu, Wenyin Fu, Brian Fuller, Cynthia Gao,
Vedanuj Goswami, Naman Goyal, Anthony Hartshorn,
Saghar Hosseini, Rui Hou, Hakan Inan, Marcin Kardas,
Viktor Kerkez, Madian Khabsa, Isabel Kloumann, Artem
Korenev, Punit Singh Koura, Marie-Anne Lachaux,
Thibaut Lavril, Jenya Lee, Diana Liskovich, Yinghai Lu,
Yuning Mao, Xavier Martinet, Todor Mihaylov, Pushkar
Mishra, Igor Molybog, Yixin Nie, Andrew Poulton,
Jeremy Reizenstein, Rashi Rungta, Kalyan Saladi, Alan
Schelten, Ruan Silva, Eric Michael Smith, Ranjan Subramanian, Xiaoqing Ellen Tan, Binh Tang, Ross Taylor,
Adina Williams, Jian Xiang Kuan, Puxin Xu, Zheng
Yan, Iliyan Zarov, Yuchen Zhang, Angela Fan, Melanie

USENIX Association

Kambadur, Sharan Narang, Aurelien Rodriguez, Robert
Stojnic, Sergey Edunov, and Thomas Scialom. Llama 2:
Open foundation and fine-tuned chat models, 2023.
[67] Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob
Uszkoreit, Llion Jones, Aidan N Gomez, Ł ukasz Kaiser,
and Illia Polosukhin. Attention is all you need. In
I. Guyon, U. Von Luxburg, S. Bengio, H. Wallach,
R. Fergus, S. Vishwanathan, and R. Garnett, editors,
Advances in Neural Information Processing Systems,
volume 30. Curran Associates, Inc., 2017.
[68] Guan Wang, Sijie Cheng, Xianyuan Zhan, Xiangang Li,
Sen Song, and Yang Liu. Openchat: Advancing opensource language models with mixed-quality data, 2023.
[69] Shibo Wang, Jinliang Wei, Amit Sabne, Andy
Davis, Berkin Ilbeyi, Blake Hechtman, Dehao Chen,
Karthik Srinivasa Murthy, Marcello Maggioni, Qiao
Zhang, Sameer Kumar, Tongfei Guo, Yuanzhong Xu,
and Zongwei Zhou. Overlap communication with
dependent computation via decomposition in large
deep learning models. In Proceedings of the 28th ACM
International Conference on Architectural Support
for Programming Languages and Operating Systems,
Volume 1, ASPLOS 2023, page 93–106, New York, NY,
USA, 2022. Association for Computing Machinery.
[70] Xiaohui Wang, Ying Xiong, Yang Wei, Mingxuan Wang,
and Lei Li. LightSeq: A high performance inference
library for transformers. In Proceedings of the 2021
Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies: Industry Papers (NAACL-HLT),
pages 113–120. Association for Computational Linguistics, June 2021.
[71] Jason Wei, Yi Tay, Rishi Bommasani, Colin Raffel, Barret Zoph, Sebastian Borgeaud, Dani Yogatama, Maarten
Bosma, Denny Zhou, Donald Metzler, Ed H. Chi, Tatsunori Hashimoto, Oriol Vinyals, Percy Liang, Jeff Dean,
and William Fedus. Emergent abilities of large language
models. Trans. Mach. Learn. Res., 2022, 2022.
[72] Bingyang Wu, Yinmin Zhong, Zili Zhang, Gang Huang,
Xuanzhe Liu, and Xin Jin. Fast distributed inference
serving for large language models, 2023.
[73] Guangxuan Xiao, Ji Lin, Mickael Seznec, Hao Wu,
Julien Demouth, and Song Han. Smoothquant: Accurate and efficient post-training quantization for large
language models, 2023.
[74] Zihao Ye, Lequn Chen, Ruihang Lai, Yilong Zhao, Size
Zheng, Junru Shao, Bohan Hou, Hongyi Jin, Yifei Zuo,
Liangsheng Yin, Tianqi Chen, and Luis Ceze. Accelerating self-attentions for llm serving with flashinfer,
February 2024.

18th USENIX Symposium on Operating Systems Design and Implementation

133



<!-- PDF page break -->

[75] Gyeong-In Yu, Joo Seong Jeong, Geon-Woo Kim, Soojeong Kim, and Byung-Gon Chun. Orca: A distributed
serving system for Transformer-Based generative models. In 16th USENIX Symposium on Operating Systems
Design and Implementation (OSDI 22), pages 521–538,
Carlsbad, CA, July 2022. USENIX Association.
[76] Lianmin Zheng, Wei-Lin Chiang, Ying Sheng, Tianle
Li, Siyuan Zhuang, Zhanghao Wu, Yonghao Zhuang,
Zhuohan Li, Zi Lin, Eric. P Xing, Joseph E. Gonzalez,
Ion Stoica, and Hao Zhang. Lmsys-chat-1m: A largescale real-world llm conversation dataset, 2023.
[77] Yinmin Zhong, Shengyu Liu, Junda Chen, Jianbo Hu,
Yibo Zhu, Xuanzhe Liu, Xin Jin, and Hao Zhang. Distserve: Disaggregating prefill and decoding for goodputoptimized large language model serving, 2024.

A

will maintain clear and accessible instructions about our artifacts in an easily identifiable README file. All the detailed
instructions and README files to reproduce the experiments
in the OSDI paper are available in the branch osdi-sarathiserve.

Requirements
Sarathi-Serve has been tested with CUDA 12.1 on A100 and
A40 GPUs. The specific GPU SKUs on which the experiments were performed and the parallelism strategies used
are clearly explained in the README corresponding to the
figures in the artifact, for ease of reproducibility.

Artifact Appendix

Abstract
Our open source artifact is available on GitHub. This repository contains our implementation of Sarathi-Serve as well as
the harnesses and scripts for running and plotting the experiments described in this paper.
This repository originally started as a fork of the vLLM
project. Sarathi-Serve is a lightweight high-performance research prototype and doesn’t have complete feature parity
with open-source vLLM. We have only retained the most
critical features and adopted the codebase for faster research
iterations.

Scope
This artifact allows the readers to validate the claims made in
the Sarathi-Serve paper (the figures) and provides a means to
replicate the experiments described. The artifact can be used
to set up the necessary environment, execute the main results,
and perform microbenchmarks, thus providing a comprehensive understanding of the key claims in Sarathi-Serve.

Contents
The repository is structured as follows, the primary source
code for the system is contained in directory /sarathi. The
implementations for custom CUDA kernels are within the
/csrc directory. All the scripts to reproduce the experiments
are in /osdi-experiments and finally, the trace files used for
the experiments are stored in /data.

Hosting
You can obtain our artifacts from GitHub: GitHub. The main
branch of the Github repository is actively updated, but we

134

18th USENIX Symposium on Operating Systems Design and Implementation

USENIX Association



<!-- PDF page break -->
