"""DE-RISK: can a vLLM 0.23 resumable request accept AUDIO chunks appended incrementally
(Qwen3-Omni), reuse KV (flat per-chunk ingest), and decode frame-bounded (a few tokens per chunk,
then wait for the next audio) -- the two prerequisites for wiring the append-to-resident-KV path
into the gateway's per-tick Step for a concurrent apple-to-apple sweep.

Tests: (1) single session, append 4 real audio chunks; (2) 2 concurrent sessions. Reports whether
it crashes, whether per-chunk ingest stays flat, and the decoded text. Run via run env (cu13 +
NVCC_APPEND_FLAGS)."""
import asyncio, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from vllm import SamplingParams
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.v1.engine.async_llm import AsyncLLM
from vllm.engine.protocol import StreamingInput

MODEL = os.environ.get("MODEL", "sammysun0711/Qwen3-Omni-30B-A3B-Instruct-FP8-Dynamic")
PH = "<|audio_start|><|audio_pad|><|audio_end|>"
HEAD = ("<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n")
TAIL = "<|im_end|>\n<|im_start|>assistant\n"
CHUNK_S = 2.0       # seconds of audio per appended frame
NFRAMES = 5
TPT = 8             # tokens to decode per frame (frame-bounded)


def audio_chunks():
    from experiments.realtime_load import load_audio_pool
    pool = load_audio_pool(4)
    arr, sr = pool[0]
    arr = np.asarray(arr, dtype=np.float32)
    n = int(CHUNK_S * sr)
    return [(arr[i * n:(i + 1) * n].copy(), sr) for i in range(NFRAMES)], sr


async def one_session(engine, rid, chunks):
    """Append chunks[0..] to ONE resumable request; per-frame: time append -> first new token."""
    state = {"out": 0, "pre": 0, "ta": 0.0, "dt": [], "go": asyncio.Event(), "txt": ""}

    async def gen():
        for i, ch in enumerate(chunks):
            state["pre"] = state["out"]
            state["ta"] = time.perf_counter()
            # first frame carries the chat header + user turn open; later frames append just audio.
            prompt = (HEAD + PH if i == 0 else PH)
            sp = SamplingParams(temperature=0.0, max_tokens=TPT * (i + 1), ignore_eos=True)
            yield StreamingInput(prompt={"prompt": prompt, "multi_modal_data": {"audio": ch}},
                                 sampling_params=sp)
            await state["go"].wait(); state["go"].clear()

    sp0 = SamplingParams(temperature=0.0, max_tokens=TPT, ignore_eos=True)
    seen = False
    async for out in engine.generate(gen(), sp0, rid):
        n = len(out.outputs[0].token_ids)
        state["out"] = n
        state["txt"] = out.outputs[0].text
        if n > state["pre"] and not seen:
            state["dt"].append((time.perf_counter() - state["ta"]) * 1000.0)
            seen = True; state["go"].set(); seen = False
        if len(state["dt"]) >= len(chunks):
            break
    return state["dt"], state["txt"]


async def main():
    args = AsyncEngineArgs(model=MODEL, trust_remote_code=True, gpu_memory_utilization=0.85,
                           max_model_len=8192, enforce_eager=False,
                           limit_mm_per_prompt={"audio": 32, "image": 0},
                           mm_processor_cache_gb=8)
    engine = AsyncLLM.from_engine_args(args)
    try:
        chunks, sr = audio_chunks()
        print(f"=== TEST 1: single session, {len(chunks)} x {CHUNK_S}s audio frames ===", flush=True)
        try:
            dt, txt = await one_session(engine, "s1", chunks)
            print(f"  per-frame ingest ms: " + " ".join(f"{d:.0f}" for d in dt))
            print(f"  decoded text: {txt!r}")
            print(f"  T1_RESULT: flat={'YES' if dt[-1] < 3*max(dt[1],1) else 'NO'}")
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"  T1_RESULT: CRASH {type(e).__name__}: {e}")

        print(f"=== TEST 2: 2 concurrent sessions ===", flush=True)
        try:
            r = await asyncio.gather(one_session(engine, "c1", chunks),
                                     one_session(engine, "c2", chunks))
            for k, (dt, txt) in enumerate(r):
                print(f"  sess{k}: ingest ms " + " ".join(f"{d:.0f}" for d in dt) + f" | {txt!r}")
            print("  T2_RESULT: OK")
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"  T2_RESULT: CRASH {type(e).__name__}: {e}")
        print("V023_AUDIO_DERISK_DONE", flush=True)
    finally:
        engine.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
