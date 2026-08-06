# Triage: Qwen3-Omni / Qwen2.5-Omni / MiniCPM-o fail to initialize in vLLM 0.23.0 on Blackwell — `cu_seqlens_q must be on CUDA` in `MMEncoderAttention` during memory profiling

**Filed for upstream (vLLM).** Blocks adoption of vLLM's new **resumable-request / streaming-session**
API (`StreamingInput`, `_add_streaming_input_request`, `/v1/realtime`) for **audio full-duplex** serving,
because the omni models won't start.

## Summary

On an NVIDIA RTX PRO 6000 **Blackwell (SM 12.0)** GPU, vLLM **0.23.0** (torch 2.11.0+cu130, flashinfer
0.6.12) **crashes during EngineCore startup (memory profiling)** for the audio-omni models with:

```
RuntimeError: cu_seqlens_q must be on CUDA
  ... MMEncoderAttention.forward_cuda -> _forward_fa
      -> vit_flash_attn_wrapper -> flash_attn_maxseqlen_wrapper -> flash_attn_varlen_func
```

The model never loads, so the streaming/realtime feature cannot be exercised for these models.

## Environment

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition; capability `(12, 0)`; driver 595.x (CUDA 13.2).
- vLLM `0.23.0`; torch `2.11.0+cu130` (runtime CUDA 13.0); flashinfer-python/-cubin `0.6.12`.
- System CUDA **toolkit** is 12.8 (`/usr/local/cuda-12.8`); system `nvcc` 11.5. (No CUDA ≥12.9 toolkit.)
- torch itself is healthy: `torch.cuda.is_available()=True`, `get_device_capability()=(12,0)`, alloc works.

## Affected models (the four real-time models we benchmark)

| model | vLLM model file | uses `MMEncoderAttention` | status |
|---|---|---|---|
| **Qwen3-Omni-30B-A3B (FP8)** | `qwen3_omni_moe_thinker.py` | yes (audio + vision encoders) | **CONFIRMED crash** |
| **Qwen2.5-Omni-7B** | `qwen2_5_omni_thinker.py` | yes (same encoder pattern) | **Expected affected** (same code path) |
| **MiniCPM-o-4.5** | `minicpmv4_6.py` | yes | **Likely affected** (shares `MMEncoderAttention`) |
| **Moshi** | n/a (native `moshi` pkg, not a vLLM model) | n/a | Not applicable (separate stack) |

`MMEncoderAttention` is shared by ~40 multimodal models, so the fix is one place and broadly beneficial.

## Reproduction

```python
from vllm import LLM, SamplingParams
llm = LLM(model="sammysun0711/Qwen3-Omni-30B-A3B-Instruct-FP8-Dynamic",
          trust_remote_code=True, gpu_memory_utilization=0.85, max_model_len=8192,
          limit_mm_per_prompt={"audio": 1, "image": 0})  # crashes during init/profiling
```

Crashes identically with `attention_backend="FLASH_ATTN"` and with the flashinfer default.

## Root cause analysis

There are **two independent issues**; (B) is the blocker.

### (A) flashinfer SM-12.x capability check is gated on the *toolkit* CUDA version (secondary)
`flashinfer/compilation_context.py:56` — for SM 12.x, `_normalize_cuda_arch` calls
`is_cuda_version_at_least("12.9")` and `raise RuntimeError("SM 12.x requires CUDA >= 12.9")` otherwise.
That check reads the **toolkit/nvcc** version (12.8 here), not torch's **runtime** CUDA (13.0). It is
caught at line 81 (`logger.warning("Failed to get device capability: ...")`), leaving capability
detection incomplete.
- **Workaround (verified):** `FLASHINFER_CUDA_ARCH_LIST="12.0f"` bypasses the check (uses the prebuilt
  SM120 cubin) — the warning disappears. **But the crash (B) remains**, so (A) is not the blocker.
- Suggested upstream: gate on the **runtime** CUDA version, or treat a missing toolkit as "use prebuilt
  cubin" rather than failing capability detection.

### (B) `cu_seqlens_q` is on CPU during the omni-encoder profiling forward (the blocker)
Call chain: `vllm/model_executor/layers/attention/mm_encoder_attention.py::_forward_fa` →
`vllm/v1/attention/ops/vit_attn_wrappers.py::vit_flash_attn_wrapper` → `flash_attn_maxseqlen_wrapper`
→ `flash_attn_varlen_func(cu_seqlens_q=..., cu_seqlens_k=...)`, which requires CUDA tensors.

**[UPDATED — root cause confirmed and FIXED, see Resolution below.]** During EngineCore profiling the
omni encoder builds `cu_seqlens` on the **feature-length tensor's device (CPU)** while **q/k/v are on
CUDA** (an instrumented `forward_cuda` showed `query.is_cuda == True`). The varlen FA op then gets a CPU
`cu_seqlens_q` → crash.
- `qwen3_omni_moe_thinker.py:504-508` builds `cu_seqlens = async_tensor_h2d(cu_chunk_lens, device=aftercnn_lens.device)` — the *feature* tensor's device (CPU in the profiling path), not the query device.
- (legacy note, superseded) the entire encoder
  profiling forward is on CPU, and `flash_attn_varlen_func` is CUDA-only.

### Suggested fix directions
1. Ensure the multimodal **encoder profiling dummy inputs are created on the model device (CUDA)** for
   omni models (audio + vision towers), so the FA path runs on GPU during profiling; **or**
2. In `MMEncoderAttention.forward_cuda`, when the FA backend is selected but inputs are on CPU (profiling),
   fall back to `_forward_sdpa` (CPU-capable) instead of the CUDA-only varlen FA; **or**
3. Build `cu_seqlens` on the compute device consistently (not the feature-length tensor's device).

(1) or (2) is the targeted, low-risk fix; both keep `MMEncoderAttention` robust for all ~40 consumers.

## Impact
Without this, vLLM 0.23's resumable-request streaming sessions — the correct primitive for incremental
audio full-duplex (append a chunk, reuse KV; no per-frame prompt re-submission) — cannot be used with any
audio-omni model, because the model fails to initialize. Fixing (B) unblocks Qwen3-Omni / Qwen2.5-Omni /
MiniCPM-o streaming serving on Blackwell.

---

## Resolution (fixed + verified, 2026-06-24)

I implemented and **verified** the fix in an isolated vLLM 0.23 venv (see `patches/vllm_0.23_omni_blackwell.patch`):

- **FIX 1 — the vLLM omni bug (cu_seqlens device).** In the shared `MMEncoderAttention.forward_cuda`,
  coerce `cu_seqlens` to the query device before dispatch:
  `if cu_seqlens is not None and cu_seqlens.device != query.device: cu_seqlens = cu_seqlens.to(query.device)`.
  **Verified:** the `cu_seqlens_q must be on CUDA` crash is gone — EngineCore proceeds past the omni
  encoder. (`query.is_cuda` was confirmed True via instrumentation; only `cu_seqlens` was on CPU.) This
  is the targeted, low-risk fix and benefits all ~40 `MMEncoderAttention` consumers
  (qwen3_omni_moe_thinker, qwen2_5_omni_thinker, minicpmv*).
- **FIX 2 — capability gate (secondary).** flashinfer gates SM12.x on the *toolkit* CUDA via
  `is_cuda_version_at_least("12.9")`; gate on the **runtime** CUDA (`torch.version.cuda`) so Blackwell is
  recognized when the local nvcc < 12.9. Verified: clears "SM 12.x requires CUDA >= 12.9" / "requires
  sm75+".

- **FIX 3 — flashinfer JIT toolchain (cccl vs CUDA-13.2).** With FIX 1+2, flashinfer 0.6.12 JIT-compiles
  its SM120f kernels (`sampling`) with the local CUDA-13.2 nvcc, and its **bundled cccl headers** abort
  with `cuda_toolkit.h: "CUDA compiler and CUDA toolkit headers are incompatible"`. That check is wrapped
  in `#ifndef CCCL_DISABLE_CTK_COMPATIBILITY_CHECK` (its own comment: "use a newer CTK than the compiler
  ships… on their own peril") — and across a CUDA *minor* (13.0 bundled vs 13.2 nvcc) the kernels are
  source/ABI-compatible. **Fix (no source edit): `export NVCC_APPEND_FLAGS="-DCCCL_DISABLE_CTK_COMPATIBILITY_CHECK"`**
  (+ `CUDA_HOME` → the venv's bundled cu13 nvcc). Verified: the JIT compiles and the kernel loads.

- **FIX 4 — Qwen3-Omni mrope off-by-one crashes STREAMING audio.** Plain audio works, but a
  resumable/streaming request whose chunk *ends at an audio block* crashed EngineCore with
  `RuntimeError: Position ids length mismatch with input ids length` (`qwen3_omni_moe_thinker.py`
  `get_mrope_input_positions`). The function models each mm block as text+bos+content+eos, but
  `mm_position.offset` already points to the first audio embedding (the `audio_start` token is counted
  in `text_len` *and* re-added as the explicit bos), so the position layout overshoots `seq_len` by 1 at
  the boundary. It is **masked by any trailing text** after the audio (so plain prompts work) and only
  fires when audio is the final content — exactly the per-frame append case. Empirically isolated:
  text-after-audio → OK; audio-at-end / bare-append → CRASH. **Fix:** reconcile the position count to
  `seq_len` instead of crashing — the guard only triggers on the mismatch, so every working input is
  byte-identical and only the crashing boundary case is repaired. **Verified:** audio-at-end and
  bare-append now decode coherently ("Hello! How") at **flat ~5 ms/frame** resident-KV append. (A worker
  can equivalently emit ≥1 trailing token after each audio placeholder.)

**RESOLVED — full end-to-end load + streaming AUDIO verified (2026-06-24).** With FIX 1 + FIX 2 + FIX 3 + FIX 4,
**Qwen3-Omni-30B-A3B-FP8 fully loads and generates** on this Blackwell (SM120) box under vLLM 0.23:
`experiments/run_v023_omni_smoke.sh` → `V023_SMOKE_OK` (loads all 8 shards, **passes memory profiling
through the omni audio encoder** — the FIX-1 path — JIT-compiles the SM120f flashinfer kernels, captures
CUDA graphs, decodes correctly). This unblocks vLLM 0.23's **resumable-request / streaming-session** API
(`StreamingInput`, `_add_streaming_input_request`, `/v1/realtime`) for the omni models on this hardware —
the primitive needed for true minute-level append-to-resident-KV full-duplex serving (vs the 8 s
re-encode window). With FIX 4, that primitive now runs for **audio**: a streaming session appends 2 s
audio chunks to one resident request at **flat ~5 ms/frame** ingest, decoding coherently
(`experiments/v023_audio_append_derisk.py`, `v023_mrope_validate.py`). FIX 1 is the upstream vLLM bug fix
(benefits all ~40 `MMEncoderAttention` consumers); FIX 2 + FIX 3 are local toolchain unblocks for running
on a CUDA-13.2 Blackwell box; FIX 4 is an upstream Qwen3-Omni mrope fix (benefits any streaming/realtime
audio use).
