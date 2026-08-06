"""Sink-token retention (FIX 6, patches/vllm_0.23_omni_blackwell.patch) unit tests.

Must run under the patched vLLM 0.23 venv:
    ~/vllm023-venv/bin/python -m pytest tests/test_sink_retention.py -v

Covers the two halves of the mechanism independently of the model:
  - the Triton unified-attention kernel computes exact attention over the
    union mask  causal & ((q-k < W) | (k < SINK)); freed blocks are mapped to
    a NaN-filled physical block so any out-of-mask read poisons the output.
  - SlidingWindowManager keeps the first ceil(sink/block) blocks resident
    while still freeing everything between sink and window, and the admission
    cap counts the retained blocks.
"""
import math
import os

import pytest

torch = pytest.importorskip("torch")
vllm = pytest.importorskip("vllm")
if not vllm.__version__.startswith("0.23"):
    pytest.skip("sink-retention patch targets vLLM 0.23", allow_module_level=True)

SINK = 32
os.environ["METRONOME_SWA_SINK"] = str(SINK)

BLOCK = 16
HEADS_Q, HEADS_KV, HD = 32, 4, 128  # Qwen3-Omni-30B decoder config
W = 1024
SCALE = 1.0 / math.sqrt(HD)


@pytest.mark.skipif(not torch.cuda.is_available(), reason="needs CUDA")
@pytest.mark.parametrize(
    "name,seq_lens,query_lens,use_3d",
    [
        ("2d_decode_old", [3000, 5000], [1, 1], False),
        ("3d_decode_old", [3000, 5000], [1, 1], True),
        ("2d_decode_young", [500], [1], False),
        ("2d_boundary", [1100], [1], False),
        ("2d_prefill_chunk", [2064], [64], False),
        ("2d_mixed", [2064, 3000, 400], [64, 1, 5], False),
    ],
)
def test_sink_kernel_matches_reference(name, seq_lens, query_lens, use_3d):
    import vllm.v1.attention.ops.triton_unified_attention as tua

    assert tua._METRONOME_SINK_LEN == SINK
    torch.manual_seed(0)
    dev, dt = "cuda", torch.bfloat16
    nseq, total_q = len(seq_lens), sum(query_lens)
    max_blocks = max((L + BLOCK - 1) // BLOCK for L in seq_lens)
    total_blocks = 1 + sum((L + BLOCK - 1) // BLOCK for L in seq_lens)
    kc = torch.randn(total_blocks, BLOCK, HEADS_KV, HD, device=dev, dtype=dt)
    vc = torch.randn(total_blocks, BLOCK, HEADS_KV, HD, device=dev, dtype=dt)
    kc[0] = float("nan")  # the "freed" block: reading it poisons the output
    vc[0] = float("nan")

    block_table = torch.zeros(nseq, max_blocks, dtype=torch.int32, device=dev)
    k_log, v_log = [], []
    next_phys = 1
    n_sink_blocks = (SINK + BLOCK - 1) // BLOCK
    for i, L in enumerate(seq_lens):
        nb = (L + BLOCK - 1) // BLOCK
        ctx = L - query_lens[i]
        first_live = max(0, ctx - W + 1) // BLOCK
        kl = torch.full((L, HEADS_KV, HD), float("nan"), device=dev)
        vl = torch.full((L, HEADS_KV, HD), float("nan"), device=dev)
        for b in range(nb):
            if b >= first_live or b < n_sink_blocks:
                block_table[i, b] = next_phys
                lo, hi = b * BLOCK, min((b + 1) * BLOCK, L)
                kl[lo:hi] = kc[next_phys, : hi - lo].float()
                vl[lo:hi] = vc[next_phys, : hi - lo].float()
                next_phys += 1
        k_log.append(kl)
        v_log.append(vl)

    q = torch.randn(total_q, HEADS_Q, HD, device=dev, dtype=dt)
    out = torch.empty_like(q)
    cu = torch.tensor(
        [0] + list(torch.tensor(query_lens).cumsum(0)), dtype=torch.int32, device=dev
    )
    seqused_k = torch.tensor(seq_lens, dtype=torch.int32, device=dev)
    if use_3d:
        nseg = 16
        segm_out = torch.empty(total_q, HEADS_Q, nseg, 256, device=dev)
        segm_max = torch.empty(total_q, HEADS_Q, nseg, device=dev)
        segm_exp = torch.empty_like(segm_max)
        thresh = nseq + 1
    else:
        segm_out = segm_max = segm_exp = thresh = nseg = None

    tua.unified_attention(
        q=q, k=kc, v=vc, out=out, cu_seqlens_q=cu, max_seqlen_q=max(query_lens),
        seqused_k=seqused_k, max_seqlen_k=max(seq_lens), softmax_scale=SCALE,
        causal=True, window_size=(W - 1, 0), block_table=block_table, softcap=0,
        q_descale=None, k_descale=None, v_descale=None, seq_threshold_3D=thresh,
        num_par_softmax_segments=nseg, softmax_segm_output=segm_out,
        softmax_segm_max=segm_max, softmax_segm_expsum=segm_exp, alibi_slopes=None,
    )
    assert not torch.isnan(out.float()).any(), "kernel read a freed block"

    o = 0
    for i, L in enumerate(seq_lens):
        ql = query_lens[i]
        ctx = L - ql
        grp = HEADS_Q // HEADS_KV
        kx = torch.nan_to_num(k_log[i]).repeat_interleave(grp, dim=1)
        vx = torch.nan_to_num(v_log[i]).repeat_interleave(grp, dim=1)
        S = torch.einsum("qhd,khd->hqk", q[o : o + ql].float(), kx) * SCALE
        qpos = torch.arange(ctx, L, device=dev)[:, None]
        kpos = torch.arange(L, device=dev)[None, :]
        mask = (kpos <= qpos) & (((qpos - kpos) < W) | (kpos < SINK))
        S = S.masked_fill(~mask[None], float("-inf"))
        ref = torch.einsum("hqk,khd->qhd", torch.softmax(S, dim=-1), vx)
        err = (out[o : o + ql].float() - ref).abs().max().item()
        assert err < 3e-2, f"{name} seq{i}: max_abs_err={err}"
        o += ql


def test_sliding_window_manager_retains_sink_blocks():
    from unittest.mock import MagicMock

    from vllm.v1.core.single_type_kv_cache_manager import SlidingWindowManager
    from vllm.v1.kv_cache_interface import SlidingWindowSpec

    spec = SlidingWindowSpec(
        block_size=BLOCK, num_kv_heads=4, head_size=128,
        dtype=torch.bfloat16, sliding_window=W,
    )
    cap = spec.max_admission_blocks_per_request(
        max_num_batched_tokens=2048, max_model_len=16384)
    os.environ["METRONOME_SWA_SINK"] = "0"
    cap0 = spec.max_admission_blocks_per_request(
        max_num_batched_tokens=2048, max_model_len=16384)
    os.environ["METRONOME_SWA_SINK"] = str(SINK)
    assert cap == cap0 + 2  # two 16-token sink blocks counted

    class B:
        def __init__(self, i):
            self.id, self.block_hash = i, None

    null = B(-1)
    pool = MagicMock()
    freed = []
    pool.free_blocks = lambda blocks, prepend=False: freed.extend(blocks)
    mgr = SlidingWindowManager(
        spec, block_pool=pool, enable_caching=False, kv_cache_group_id=0,
        scheduler_block_size=BLOCK,
    )
    assert mgr._retain_first_blocks == 2
    mgr._null_block = null
    mgr.req_to_blocks["r0"] = [B(i) for i in range(188)]  # 3000-token session

    mgr.remove_skipped_blocks("r0", 3000)  # window start at token 1977
    blocks = mgr.req_to_blocks["r0"]
    assert blocks[0].id == 0 and blocks[1].id == 1
    assert all(b is null for b in blocks[2:123])
    assert all(b is not null for b in blocks[123:])
    assert len(freed) == 121

    # second pass stops at the previously nulled region, sinks still resident
    mgr.req_to_blocks["r0"].extend(B(200 + i) for i in range(60))
    freed.clear()
    mgr.remove_skipped_blocks("r0", 3000 + 60 * BLOCK)
    assert mgr.req_to_blocks["r0"][0].id == 0
    assert len(freed) == 60
