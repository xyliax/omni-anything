"""Make-or-break test for streaming-prefill via vLLM prefix caching: does prefilling a GROWING
audio clip reuse the KV/encoder work of the shared prefix? If yes, incremental audio prefill is
cheap on stock vLLM. If no (encoder is whole-item-hashed / re-encodes), true streaming prefill
needs a causal encoder + vLLM extension. We time real prefills on the real model."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")
import numpy as np
from bench.gpu_probe import wait_for_window


def prefill_ms(be, audio, reps=3):
    """Time set_input(audio)+one step_stream that prefills it and emits the first token."""
    best = 1e9
    for r in range(reps):
        sid = 90000 + r + int(len(audio[0]))   # distinct sid each time
        be.set_input(sid, audio=audio, text="Answer:", max_tokens=1)
        t0 = time.perf_counter()
        be.step_stream([sid], 1)
        best = min(best, (time.perf_counter() - t0) * 1000.0)
        be.remove_session(sid)
    return best


def main():
    wait_for_window(need_free_gib=0.6 * 97 + 2, max_util_pct=80, timeout_s=72000)
    from metronome.backends.vllm_backend import VLLMBackend
    be = VLLMBackend("openbmb/MiniCPM-o-2_6", gpu_memory_utilization=0.6, max_model_len=4096,
                     trust_remote_code=True, enforce_eager=False, in_frac=0.0,
                     enable_chunked_prefill=True, enable_prefix_caching=True,
                     limit_mm_per_prompt={"audio": 1, "image": 1})
    sr = 16000
    rng = np.random.default_rng(0)
    full = rng.standard_normal(sr * 4).astype("float32") * 0.05   # 4s
    a1 = (full[:sr * 1], sr)         # 0-1s
    a1b = (full[:sr * 1].copy(), sr) # identical 0-1s (tests whole-item cache hit)
    a2 = (full[:sr * 2], sr)         # 0-2s (cumulative: shares 0-1s prefix)
    a2_fresh = (rng.standard_normal(sr * 2).astype("float32") * 0.05, sr)  # different 2s

    print("=== audio prefix-reuse test (MiniCPM-o, real vLLM, prefix caching ON) ===", flush=True)
    t_1 = prefill_ms(be, a1)
    t_1b = prefill_ms(be, a1b)        # identical -> if whole-item cache works, should be << t_1
    t_2c = prefill_ms(be, a2)         # cumulative 2s
    t_2f = prefill_ms(be, a2_fresh)   # fresh 2s
    print(f"  prefill 1s (cold)            : {t_1:7.1f} ms", flush=True)
    print(f"  prefill 1s (identical again) : {t_1b:7.1f} ms  ({'CACHE HIT' if t_1b < 0.6*t_1 else 'no reuse'})", flush=True)
    print(f"  prefill 2s (cumulative w/1s) : {t_2c:7.1f} ms", flush=True)
    print(f"  prefill 2s (fresh)           : {t_2f:7.1f} ms", flush=True)
    reuse = t_2c < 0.75 * t_2f
    print(f"\n  growing-clip reuse: {'YES — incremental prefill is cheap on vLLM' if reuse else 'NO — 2s-cumulative ~= 2s-fresh; encoder re-encodes whole, no sub-chunk reuse'}", flush=True)
    print(f"  => streaming prefill {'is a config-level win' if reuse else 'needs a causal/streaming encoder + vLLM incremental-mm-KV support'}", flush=True)


if __name__ == "__main__":
    main()
