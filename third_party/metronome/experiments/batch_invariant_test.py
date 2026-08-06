"""Validate the batch-invariant-kernels borrow: does a request's output depend on BATCH COMPOSITION?

The documented nondeterminism: the same prompt can decode different tokens at batch=1 vs in a batch
of K (batched-FP nondeterminism), causing per-sample correctness flips under load. vLLM ships the TML
batch-invariant kernels (VLLM_BATCH_INVARIANT=1: batch-invariant matmul/attention + IEEE fp32). This
test runs K real spoken questions (a) each ALONE (batch=1) and (b) ALL TOGETHER (batch=K), greedy, and
counts how many produce DIFFERENT tokens. Expect: default > 0 flips; batch-invariant == 0 (bitwise
identical regardless of batch).

Run twice: BI=0 python ... and BI=1 python ...   (BI sets VLLM_BATCH_INVARIANT before engine init).
"""
import os, sys, time
if os.environ.get("BI") == "1":
    os.environ["VLLM_BATCH_INVARIANT"] = "1"
    # batch-invariant mode requires a supported attention backend; passed as an EngineArg below
    # (the VLLM_ATTENTION_BACKEND env var is not recognized in vLLM 0.19).
os.environ.setdefault("VLLM_LOGGING_LEVEL", "WARNING")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from bench.gpu_probe import wait_for_window

MODEL = os.environ.get("M", "Qwen/Qwen2.5-Omni-7B")
K = int(os.environ.get("K", "16"))


def main():
    from experiments.bench_spoken_qa import load_samples
    wait_for_window(need_free_gib=30, max_util_pct=101, timeout_s=7200)  # mem-gated; util can phantom-pin
    samples = load_samples("llama-questions", K)
    inputs = [dict(audio=(np.asarray(s["audio"][0], dtype=np.float32), int(s["audio"][1])),
                   images=[], text="") for s in samples]
    from metronome.backends.vllm_backend import VLLMBackend
    bi = os.environ.get("VLLM_BATCH_INVARIANT") == "1"
    print(f"=== batch-invariance test | {MODEL} | K={K} | VLLM_BATCH_INVARIANT={bi} ===", flush=True)
    extra = {"attention_backend": "FLASH_ATTN"} if bi else {}
    be = VLLMBackend(MODEL, gpu_memory_utilization=0.6, max_model_len=4096,
                     trust_remote_code=True, enforce_eager=False, **extra)
    # (a) each alone (batch=1)
    solo = [be.generate_batch([inp], max_tokens=48)[0] for inp in inputs]
    # (b) all together (batch=K)
    batched = be.generate_batch(inputs, max_tokens=48)
    flips, first_div = 0, []
    for i, (a, b) in enumerate(zip(solo, batched)):
        if list(a) != list(b):
            flips += 1
            # position of first divergence
            d = next((j for j in range(min(len(a), len(b))) if a[j] != b[j]), min(len(a), len(b)))
            first_div.append((i, d, len(a), len(b)))
    print(f"\nRESULT: {flips}/{K} requests changed tokens between batch=1 and batch={K} "
          f"(VLLM_BATCH_INVARIANT={bi})", flush=True)
    if flips:
        print("  first divergence (req, tok_pos, len_solo, len_batched):", first_div[:6], flush=True)
    print(f"  => {'DETERMINISTIC (batch-invariant works)' if flips == 0 else 'batch-dependent output'}",
          flush=True)


if __name__ == "__main__":
    main()
