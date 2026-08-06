"""Metronome CTX-token sink: the [0,S) ∪ [t-W, t] union-mask half of the windowed-KV
attention (companion to qwen3_swa.py's window half).

WHY. The sliding window (qwen3_swa.py / METRONOME_SWA_TOKENS) bounds resident KV and
per-frame attention, but it also evicts the <CTX> hotword prefix once the session grows
past W — so context biasing decays on a minute-scale continuous-decode session (the
streaming-captions variant; the endpoint variant flushes per utterance and re-feeds CTX,
so it is unaffected — see streaming-vad-asr research/69, where application-level re-feed
holds biasing flat at +30pp across session age). The pinned-sink keeps the first S tokens
(the CTX block) attended AND resident, so biasing survives session length *without*
re-encoding CTX every frame — the in-engine efficiency version of that re-feed.

MECHANISM (StreamingLLM sinks, arXiv:2309.17453, in a paged engine). Two coupled changes,
shipped as metronome_sink_kernel.py (a full copy of vLLM 0.19's
v1/attention/ops/triton_unified_attention.py with the sink edits) + this module's block-pin:

  (1) KERNEL — the effective attention becomes the union [0,S) ∪ [t-W, t] (intersected with
      causal). The 2d unified kernel applies the window in THREE places; all three must be
      taught the sink (getting only the obvious one wrong silently corrupts the output):
        (a) the score mask:  seq_mask &= ((q_abs - k) < W) | (k < SINK_TOKENS)
        (b) the tile loop:   extend the window's tile range down to tile 0 when a sink is
            active (tile_start *= 0) so the [0,S) tiles are actually visited — the per-key
            mask excludes the middle. (kept Triton-typed to avoid a py-int/tl-value miscompile)
        (c) the V-side window filter: the kernel ALSO zeros V for keys older than the window,
            BEFORE the P@V accumulation. It must keep the sink too:
                V = tl.where(in_window | (k < SINK_TOKENS), V, 0.0)
            THIS was the subtle bug — without it, sink keys carry softmax weight (in the
            denominator L) but a zeroed V, under-normalizing the output into garbage that
            matches no mask. Caught only by a direct GPU kernel test (E9), never by the mask
            self_test below (which tests the pure-torch reference, not the Triton kernel).
      Requires the TRITON_ATTN backend (the default FLASH_ATTN kernel is compiled and cannot
      express the union — the constraint the Metronome paper flags). vLLM 0.19 dropped the
      VLLM_ATTENTION_BACKEND env var; force it with LLM(attention_backend="TRITON_ATTN").
      The dispatch forces the 2d path when a sink is active (the 3d segmented path is left
      unpatched and never runs with a sink).

  (2) KV MANAGER — the first ceil(S / block_size) blocks per request must be PINNED
      (never evicted), or the kernel attends to freed/garbage blocks. Under vLLM's
      SlidingWindowSpec the base manager frees everything behind the window; the sink blocks
      need an exception. _install_block_pin subclasses SlidingWindowManager and overrides
      remove_skipped_blocks to free only the MIDDLE [sink_blocks, window) — faithful to the
      base (same get_num_skipped_tokens, same top-down free with already-null early-break),
      differing only in keeping [0, sink_blocks).

WHAT THIS MODULE PROVIDES:
  * ``reference_union_attention`` — a pure-PyTorch reference of the union-mask attention,
    the ground truth the Triton kernel must match.
  * ``self_test`` — CPU sanity of the mask MATH (sink contributes where a window drops it;
    equals full causal when W+S cover the prefix). Note: this tests the REFERENCE, not the
    kernel — the kernel is validated separately on GPU (see below).
  * ``register(sink_tokens, window_tokens)`` — the plugin hook (METRONOME_SINK_TOKENS):
    installs the sink-aware Triton kernel + the block-pin, fail-closed (window-only, CTX
    re-fed per segment) if anything raises, so enabling the sink never silently ships a
    broken attention path.

VALIDATION (streaming-vad-asr worker_integration/):
  * E9 (e9_kernel_gpu_test.py) — drives the ACTUAL kernel entry point against the union
    reference on GPU: exact match (<2e-3 fp16) across prefill + decode, GQA 8:1/8:2/4:1,
    block 16/32, T=40..256, and window/sink combos incl. the middle-freed and sink>window
    regimes. This is what caught bug (1c).
  * E10 (e10_blockpin_test.py) — drives the shipped remove_skipped_blocks with mocked KV
    across a growing session: keeps the sink, frees the middle, keeps the window, differs
    from stock vLLM only in the pinned sink region.
  Both run on the contended shared box where full vLLM init OOMs behind the co-tenant.
"""
from __future__ import annotations
import logging

log = logging.getLogger("metronome.sink")


def reference_union_attention(q, k, v, window: int, sink: int):
    """Ground-truth [0,sink) ∪ [t-window, t] causal attention (single head).

    q,k,v: [T, D] tensors. Returns [T, D]. Pure PyTorch — the reference the Triton
    kernel patch must reproduce.
    """
    import torch
    T, D = q.shape
    pos = torch.arange(T)
    qi = pos[:, None]          # query abs pos
    ki = pos[None, :]          # key abs pos
    causal = ki <= qi
    in_window = (qi - ki) < window
    in_sink = ki < sink
    mask = causal & (in_window | in_sink)
    scores = (q @ k.T) / (D ** 0.5)
    scores = scores.masked_fill(~mask, float("-inf"))
    w = torch.softmax(scores, dim=-1)
    return w @ v


def self_test() -> bool:
    """Validate the union-mask math without any engine/GPU. Returns True on pass."""
    import torch
    torch.manual_seed(0)
    T, D, W, S = 40, 16, 8, 4
    q, k, v = (torch.randn(T, D) for _ in range(3))

    def window_only(q, k, v, window):
        pos = torch.arange(T)
        mask = (pos[None, :] <= pos[:, None]) & ((pos[:, None] - pos[None, :]) < window)
        s = (q @ k.T) / (D ** 0.5)
        return torch.softmax(s.masked_fill(~mask, float("-inf")), -1) @ v

    def full_causal(q, k, v):
        pos = torch.arange(T)
        mask = pos[None, :] <= pos[:, None]
        s = (q @ k.T) / (D ** 0.5)
        return torch.softmax(s.masked_fill(~mask, float("-inf")), -1) @ v

    union = reference_union_attention(q, k, v, W, S)
    wonly = window_only(q, k, v, W)
    full = full_causal(q, k, v)

    # (a) For a late query (t well past window+sink), union != window-only — the sink
    #     tokens contribute where the pure window dropped them (biasing preserved).
    late = T - 1
    diff_sink = (union[late] - wonly[late]).abs().max().item()
    assert diff_sink > 1e-3, f"sink had no effect (diff={diff_sink}) — mask wrong"

    # (b) When window+sink covers the whole prefix, union == full causal attention.
    union_full = reference_union_attention(q, k, v, window=T, sink=T)
    diff_full = (union_full - full).abs().max().item()
    assert diff_full < 1e-5, f"union != full when W,S cover all (diff={diff_full})"

    # (c) The sink keys are actually in the union mask for a late query.
    pos = torch.arange(T)
    late_mask = (pos <= late) & (((late - pos) < W) | (pos < S))
    assert late_mask[:S].all(), "first S keys not attended by a late query"

    log.info("metronome_sink self_test PASS: sink-effect=%.4f, full-match=%.2e",
             diff_sink, diff_full)
    return True


def _install_block_pin(S: int) -> bool:
    """Patch spec_manager_map[SlidingWindowSpec] to a subclass that keeps the first
    ceil(S/block) KV blocks resident (frees only the MIDDLE [S, t-W) blocks), so the
    sink KV is available for the kernel's [0,S) mask."""
    from vllm.v1.core import single_type_kv_cache_manager as m
    from vllm.v1.kv_cache_interface import SlidingWindowSpec

    Base = m.SlidingWindowManager
    if getattr(m.spec_manager_map.get(SlidingWindowSpec), "_metronome_sink", None) == S:
        return True

    class _PinnedSlidingWindowManager(Base):
        _metronome_sink = S

        def remove_skipped_blocks(self, request_id, total_computed_tokens):
            num_skipped = self.get_num_skipped_tokens(total_computed_tokens)
            if num_skipped <= 0:
                return
            blocks = self.req_to_blocks[request_id]
            num_skipped_blocks = min(num_skipped // self.block_size, len(blocks))
            # keep the first ceil(S/block) blocks (the CTX sink) resident
            sink_blocks = (S + self.block_size - 1) // self.block_size
            if sink_blocks >= num_skipped_blocks:
                return  # window has not yet advanced past the sink; free nothing
            removed = []
            # free the MIDDLE [sink_blocks, num_skipped_blocks); stop at the pinned sink
            for i in range(num_skipped_blocks - 1, sink_blocks - 1, -1):
                if blocks[i] == self._null_block:
                    break
                removed.append(blocks[i])
                blocks[i] = self._null_block
            self.block_pool.free_blocks(removed)

    m.spec_manager_map[SlidingWindowSpec] = _PinnedSlidingWindowManager
    return True


def _install_kernel() -> bool:
    """Route vLLM's TRITON_ATTN backend through the sink-aware unified_attention
    (union mask + sink-tile iteration). The kernel reads S from METRONOME_SINK_TOKENS.

    The import is LAZY (first attention call), not at install time: importing
    metronome_sink_kernel runs its module-level ``torch.finfo(current_platform.fp8_dtype())``
    and pulls in the Triton runtime, and doing that during EngineCore plugin-register —
    before the worker's device init — deadlocks vLLM's later CUDA setup (it hangs in
    gpu_input_batch during model-runner init). vLLM itself imports this kernel lazily for
    the same reason. The wrapper defers the import to the first forward, after device init."""
    from vllm.v1.attention.backends import triton_attn
    _cache = {}

    def _lazy_unified_attention(*args, **kwargs):
        fn = _cache.get("fn")
        if fn is None:
            import metronome_sink_kernel  # top-level module (shipped with the plugin)
            fn = _cache["fn"] = metronome_sink_kernel.unified_attention
        return fn(*args, **kwargs)

    triton_attn.unified_attention = _lazy_unified_attention
    return True


def register(sink_tokens: int, window_tokens: int) -> bool:
    """Plugin hook (METRONOME_SINK_TOKENS). Validate the mask math, then install the
    in-engine sink: (1) sink-aware Triton attention kernel (union mask [0,S)∪[t-W,t]),
    (2) a SlidingWindowManager that pins the first ceil(S/block) blocks. Requires the
    TRITON_ATTN backend (FLASH_ATTN can't express the union); the kernel force-selects
    the 2d Triton path when S>0.

    Fails closed: if the math self-test fails or either install raises, it does NOT
    patch (serving stays window-only, CTX re-fed per segment) rather than ship a
    possibly-wrong attention path.
    """
    S = int(sink_tokens)
    if S <= 0:
        return False
    # NOTE: do NOT run self_test() here. It calls torch.manual_seed(), which eagerly
    # initializes the CUDA context. register() runs during EngineCore plugin-load, BEFORE
    # the worker's own device init — a premature CUDA init there deadlocks the later device
    # setup (the engine hangs in gpu_input_batch during model-runner init). The mask math is
    # validated out-of-band anyway (E9 kernel test, E10 block-pin test); run self_test via
    # `python -m metronome_sink` for a dev-time check, not in the serving path.
    import os as _os
    _skip_k = _os.environ.get("METRONOME_SINK_SKIP_KERNEL") == "1"
    _skip_p = _os.environ.get("METRONOME_SINK_SKIP_PIN") == "1"
    try:
        if not _skip_k:
            _install_kernel()
        if not _skip_p:
            _install_block_pin(S)
        log.warning("metronome_sink install: kernel=%s pin=%s",
                    "skip" if _skip_k else "on", "skip" if _skip_p else "on")
    except Exception as e:  # noqa: BLE001
        log.warning("metronome_sink in-engine install failed (%s) — window-only; "
                    "ensure attention_backend=TRITON_ATTN", e)
        return False
    log.warning("metronome_sink INSTALLED: CTX-token sink S=%d, window W=%d "
                "(union-mask 2d Triton kernel + first-%d-block KV pin). Requires "
                "attention_backend=TRITON_ATTN.", S, window_tokens, S)
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ok = self_test()
    print("SELF_TEST", "PASS" if ok else "FAIL")
