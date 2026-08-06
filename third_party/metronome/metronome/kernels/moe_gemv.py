"""Per-slot GEMV MoE for the DECODE regime — ported from SGLang's gather+gemv kernel.

Source ported: sglang/srt/layers/moe/fused_moe_triton/mxfp4_moe_sm120_triton.py
(`_mxfp4_slot_gemv_kernel` + its host wrapper). SGLang's kernel is for MXFP4 weights; the
GEMV / gather / scatter / graph-safe routing structure is quant-agnostic — we keep it verbatim and
swap only the dequant for FP8 (e4m3) per-channel weights (w8a16: fp8 weights, bf16 activations),
which is the simpler case (no 4-bit unpack / LUT).

WHY (the TML "gather+gemv instead of grouped gemm" point): at DECODE each expert sees ~1 token, so
the MoE is a batch of matrix-VECTORS, not matrix-matrices. A grouped GEMM pads the M (token) tile to
16/64 and wastes 93-98% of the slots + pays a permute/scatter; a per-slot GEMV reads each selected
expert's weights once and multiplies the single token vector — memory-bandwidth-optimal, no tiling
waste, no permute. Fixed grid (num_slots, cdiv(N,BLOCK_N)) => CUDA-graph safe (no .unique/.item).

This module is standalone + numerically validated (see experiments/moe_gemv_test.py). Wiring it into
vLLM's live compressed-tensors FusedMoE dispatch is the remaining integration step.
"""
from __future__ import annotations
import torch
import triton
import triton.language as tl


@triton.autotune(
    configs=[
        triton.Config({"BLOCK_N": 64, "BLOCK_K": 64}, num_warps=4, num_stages=2),
        triton.Config({"BLOCK_N": 32, "BLOCK_K": 128}, num_warps=4, num_stages=2),
        triton.Config({"BLOCK_N": 64, "BLOCK_K": 128}, num_warps=4, num_stages=2),
        triton.Config({"BLOCK_N": 128, "BLOCK_K": 64}, num_warps=8, num_stages=2),
    ],
    key=["N", "K"],
)
@triton.jit
def _fp8_slot_gemv_kernel(
    A_ptr,            # [M_total, K]  bf16 source rows (activations)
    B_ptr,            # [E, N, K]     fp8 e4m3 expert weights
    B_scale_ptr,      # [E, N]        f32 per-output-channel weight scale
    C_ptr,            # [num_slots, N] bf16 output
    token_ids_ptr,    # [num_slots] int32 — which A row for each slot
    expert_ids_ptr,   # [num_slots] int32 — which expert for each slot
    N: tl.int32, K: tl.int32,
    stride_am: tl.int32,
    stride_bn: tl.int32, stride_bk: tl.int32,
    stride_bsn: tl.int32,
    expert_b_stride: tl.int64, expert_s_stride: tl.int64,
    stride_cm: tl.int32,
    BLOCK_N: tl.constexpr, BLOCK_K: tl.constexpr,
):
    """One (token, expert) pair for a BLOCK_N slice of output. Ported structure; FP8 dequant."""
    slot_id = tl.program_id(0)
    n_block = tl.program_id(1)
    token_id = tl.load(token_ids_ptr + slot_id).to(tl.int64)
    expert_id = tl.load(expert_ids_ptr + slot_id).to(tl.int64)

    offs_n = n_block * BLOCK_N + tl.arange(0, BLOCK_N)
    n_mask = offs_n < N
    acc = tl.zeros([BLOCK_N], dtype=tl.float32)

    b_base = expert_id * expert_b_stride
    a_base = token_id * stride_am
    # per-output-channel weight scale (broadcast over K)
    scale = tl.load(B_scale_ptr + expert_id * expert_s_stride + offs_n * stride_bsn,
                    mask=n_mask, other=1.0)

    for k_start in range(0, K, BLOCK_K):
        offs_k = k_start + tl.arange(0, BLOCK_K)
        k_mask = offs_k < K
        # load fp8 weights [BLOCK_N, BLOCK_K] and dequant: w.to(f32) * scale[n]
        b = tl.load(B_ptr + b_base + offs_n[:, None] * stride_bn + offs_k[None, :] * stride_bk,
                    mask=n_mask[:, None] & k_mask[None, :], other=0.0)
        b_dq = b.to(tl.float32) * scale[:, None]
        a = tl.load(A_ptr + a_base + offs_k, mask=k_mask, other=0.0).to(tl.float32)
        acc += tl.sum(a[None, :] * b_dq, axis=1)

    tl.store(C_ptr + slot_id * stride_cm + offs_n, acc.to(tl.bfloat16), mask=n_mask)


def fused_moe_gemv(hidden_states: torch.Tensor,
                   w13: torch.Tensor, w2: torch.Tensor,
                   w13_scale: torch.Tensor, w2_scale: torch.Tensor,
                   topk_ids: torch.Tensor, topk_weights: torch.Tensor,
                   intermediate_size: int) -> torch.Tensor:
    """Decode-regime FP8 MoE via per-slot GEMV. Ported host wrapper from SGLang.

    hidden_states [M,K] bf16; w13 [E,2I,K] fp8, w13_scale [E,2I] f32; w2 [E,K,I] fp8, w2_scale [E,K].
    topk_ids/topk_weights [M,topk]. Returns [M,K] bf16.
    """
    M, K = hidden_states.shape
    topk = topk_ids.shape[1]
    I = intermediate_size
    num_slots = M * topk
    dev, dt = hidden_states.device, hidden_states.dtype

    # graph-safe flattened routing (verbatim from SGLang)
    flat_expert = topk_ids.reshape(-1).contiguous()
    invalid = flat_expert < 0
    flat_expert = flat_expert.clamp(min=0).to(torch.int32)
    token_ids = (torch.arange(M, device=dev, dtype=torch.int32)
                 .unsqueeze(1).expand(M, topk).reshape(-1).contiguous())
    if w13_scale.dtype != torch.float32: w13_scale = w13_scale.float()
    if w2_scale.dtype != torch.float32: w2_scale = w2_scale.float()

    # GEMM1: gate_up  hidden[token] @ w13[expert].T -> [num_slots, 2I]
    inter = torch.empty(num_slots, 2 * I, dtype=dt, device=dev)
    g1 = lambda m: (num_slots, triton.cdiv(2 * I, m["BLOCK_N"]))
    _fp8_slot_gemv_kernel[g1](hidden_states, w13, w13_scale, inter, token_ids, flat_expert,
                              2 * I, K, hidden_states.stride(0), w13.stride(1), w13.stride(2),
                              w13_scale.stride(1), w13.stride(0), w13_scale.stride(0), inter.stride(0))
    # SiLU(gate)*up
    gate, up = inter[:, :I].float(), inter[:, I:].float()
    activated = (torch.nn.functional.silu(gate) * up).to(dt)

    # GEMM2: down  activated[slot] @ w2[expert].T -> [num_slots, K]
    down = torch.empty(num_slots, K, dtype=dt, device=dev)
    slot_ids = torch.arange(num_slots, device=dev, dtype=torch.int32)
    g2 = lambda m: (num_slots, triton.cdiv(K, m["BLOCK_N"]))
    _fp8_slot_gemv_kernel[g2](activated, w2, w2_scale, down, slot_ids, flat_expert,
                              K, I, activated.stride(0), w2.stride(1), w2.stride(2),
                              w2_scale.stride(1), w2.stride(0), w2_scale.stride(0), down.stride(0))
    # zero invalid slots, weighted combine over topk
    down = down.view(M, topk, K)
    w = topk_weights.to(down.dtype).clone()
    w = w.masked_fill(invalid.view(M, topk), 0.0)
    return (down * w.unsqueeze(-1)).sum(dim=1).to(dt)
