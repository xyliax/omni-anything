"""Smoke test: Qwen3-Omni-30B-A3B-FP8 fully LOADS + GENERATES on vLLM 0.23 / Blackwell (SM120).

This is the proof that the three Blackwell/omni blockers are resolved (see
docs/vllm_omni_streaming_triage.md + patches/vllm_0.23_omni_blackwell.patch):

  FIX 1  vLLM omni bug   — MMEncoderAttention.forward_cuda coerces cu_seqlens to query device
  FIX 2  capability gate — flashinfer get_cuda_version() prefers torch runtime CUDA
  FIX 3  flashinfer JIT  — NVCC_APPEND_FLAGS=-DCCCL_DISABLE_CTK_COMPATIBILITY_CHECK bypasses the
                           cccl-vs-CUDA-13.2 header check (set by run_v023_omni_smoke.sh)

Run via experiments/run_v023_omni_smoke.sh (it sets CUDA_HOME=cu13 + NVCC_APPEND_FLAGS and uses
the patched ~/vllm023-venv). Expected tail: "V023_SMOKE_OK".
"""
import os
os.environ.setdefault("VLLM_LOGGING_LEVEL", "WARNING")
from vllm import LLM, SamplingParams

MODEL = os.environ.get("MODEL", "sammysun0711/Qwen3-Omni-30B-A3B-Instruct-FP8-Dynamic")
llm = LLM(model=MODEL, trust_remote_code=True, gpu_memory_utilization=0.85,
          max_model_len=8192, enforce_eager=False,
          limit_mm_per_prompt={"audio": 1, "image": 0})  # exercises the omni audio encoder (FIX 1 path)
o = llm.generate(["The capital of France is"], SamplingParams(temperature=0, max_tokens=12))
print("SMOKE OUTPUT:", repr(o[0].outputs[0].text[:80]))
print("V023_SMOKE_OK")
