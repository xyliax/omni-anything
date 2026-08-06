"""Crux test for vLLM streaming sessions WITHOUT the 8s window: feed audio as a GROWING LIST of
stable 2s chunks (not one mutating clip). If vLLM's mm-processor cache (encoder-output reuse by
mm-item hash) + prefix caching (LLM KV reuse) work per-chunk, then each frame only encodes+prefills
the NEW chunk -> per-frame latency stays FLAT as the conversation grows to minute scale (incremental
streaming sessions). If it re-encodes the whole history, latency GROWS linearly (the failure mode).

Compares, over ~30 frames (≈60s of growing audio context):
  (A) GROWING-LIST  : chunks=[c0..cK], one new chunk/frame, prefix+mm cache on  -> hope: FLAT
  (B) WINDOW-8s     : the current fd_step (re-encode last 8s)                    -> baseline
Run with the base vLLM python. Polite to shared GPU.
"""
import os, sys, time
os.environ.setdefault("VLLM_LOGGING_LEVEL", "WARNING"); os.environ.setdefault("VLLM_USE_V1", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from bench.gpu_probe import wait_for_window

MODEL = os.environ.get("M", "sammysun0711/Qwen3-Omni-30B-A3B-Instruct-FP8-Dynamic")
CHUNK_S = 2.0; FRAMES = 30; TPT = 25; SR = 16000


def main():
    from vllm import LLM, SamplingParams
    from experiments.bench_spoken_qa import load_samples
    wait_for_window(need_free_gib=45, max_util_pct=80, timeout_s=7200)
    s = load_samples("llama-questions", 1)[0]
    full = np.asarray(s["audio"][0], dtype=np.float32)
    # make a long distinct audio stream by tiling with varied gain so each 2s chunk differs
    base = np.concatenate([full * (0.7 + 0.3*np.sin(i)) for i in range(40)])
    chunk_n = int(CHUNK_S * SR)

    llm = LLM(model=MODEL, trust_remote_code=True, gpu_memory_utilization=0.85,
              max_model_len=16384, enforce_eager=False, enable_prefix_caching=True,
              limit_mm_per_prompt={"audio": FRAMES + 2}, mm_processor_cache_gb=8,
              max_num_seqs=8)
    sp = SamplingParams(temperature=0.0, max_tokens=TPT, min_tokens=TPT, ignore_eos=True)
    tok_audio = "<|audio_start|><|audio_pad|><|audio_end|>"
    sys_u = "<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n"

    def frame(audios):
        prompt = sys_u + tok_audio * len(audios) + "<|im_end|>\n<|im_start|>assistant\n"
        t = time.time()
        llm.generate([{"prompt": prompt, "multi_modal_data": {"audio": audios}}], sp, use_tqdm=False)
        return (time.time() - t) * 1000

    print(f"=== vLLM streaming test {MODEL} | {CHUNK_S}s chunks, {FRAMES} frames ===", flush=True)
    # (A) GROWING LIST of stable chunks
    chunks = []
    for k in range(FRAMES):
        chunks.append((base[k*chunk_n:(k+1)*chunk_n], SR))
        if k < 3:
            frame(chunks)            # warmup the first few (cuda graph + cache fill)
    growA = []
    chunks = []
    for k in range(FRAMES):
        chunks.append((base[k*chunk_n:(k+1)*chunk_n], SR))
        growA.append((k+1, frame(chunks)))
    print("\n(A) GROWING-LIST (chunk count, ctx_s, frame_ms):", flush=True)
    for (n, ms) in growA:
        print(f"   chunks={n:2d}  ctx={n*CHUNK_S:4.0f}s  {ms:7.0f} ms", flush=True)
    a_first = np.median([m for n, m in growA[:3]]); a_last = np.median([m for n, m in growA[-3:]])
    print(f"   => first~{a_first:.0f}ms  last~{a_last:.0f}ms  "
          f"{'FLAT (incremental! cache reuse works)' if a_last < 1.8*a_first else 'GROWS (re-encodes history)'}",
          flush=True)

    # (B) WINDOW-8s baseline (re-encode last 8s = 4 chunks)
    growB = []
    for k in range(FRAMES):
        lo = max(0, (k+1) - 4)
        win = [(base[j*chunk_n:(j+1)*chunk_n], SR) for j in range(lo, k+1)]
        growB.append((k+1, frame(win)))
    b_last = np.median([m for n, m in growB[-3:]])
    print(f"\n(B) WINDOW-8s baseline: last~{b_last:.0f}ms (bounded by design)", flush=True)
    print(f"\nVERDICT: growing-list last {a_last:.0f}ms vs window-8s {b_last:.0f}ms — "
          f"{'streaming sessions VIABLE in vLLM' if a_last < 1.5*b_last else 'growing-list re-encodes; need manual incremental-encode'}",
          flush=True)


if __name__ == "__main__":
    main()
