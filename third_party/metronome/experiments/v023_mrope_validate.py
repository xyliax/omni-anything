"""Validate the vLLM-side mrope reconcile patch (qwen3_omni_moe_thinker.get_mrope_input_positions):
the ORIGINAL crashers must now (a) not crash and (b) decode coherently, WITHOUT the trailing-token
workaround. Compares against the known-good plain-audio output on the same clip.

C0 plain audio (non-streaming, control, must stay coherent)
C1 streaming, audio at end, NO trailing token (the V2 crasher)
C2 streaming, append a bare audio placeholder (the V3/append crasher)
"""
import asyncio, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from vllm import LLM, SamplingParams
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.v1.engine.async_llm import AsyncLLM
from vllm.engine.protocol import StreamingInput

MODEL = os.environ.get("MODEL", "sammysun0711/Qwen3-Omni-30B-A3B-Instruct-FP8-Dynamic")
PH = "<|audio_start|><|audio_pad|><|audio_end|>"
HEAD = "<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n"
TAIL = "<|im_end|>\n<|im_start|>assistant\n"


def aud(n=3):
    from experiments.realtime_load import load_audio_pool
    arr, sr = load_audio_pool(2)[0]
    arr = np.asarray(arr, dtype=np.float32)
    s = int(2.0 * sr)
    return [(arr[i * s:(i + 1) * s].copy() if (i + 1) * s <= len(arr) else arr[:s].copy(), sr)
            for i in range(n)]


async def stream(engine, name, frames):
    out = {"txt": "", "n": 0, "err": None, "dt": [], "go": asyncio.Event(), "pre": 0, "ta": 0.0}

    async def gen():
        for i, (pr, a) in enumerate(frames):
            out["pre"] = out["n"]; out["ta"] = time.perf_counter()
            sp = SamplingParams(temperature=0.0, max_tokens=8 * (i + 1), ignore_eos=True)
            yield StreamingInput(prompt={"prompt": pr, "multi_modal_data": {"audio": a}}, sampling_params=sp)
            await out["go"].wait(); out["go"].clear()
    sp0 = SamplingParams(temperature=0.0, max_tokens=8, ignore_eos=True)
    seen = False
    try:
        async for o in engine.generate(gen(), sp0, name):
            out["n"] = len(o.outputs[0].token_ids); out["txt"] = o.outputs[0].text
            if out["n"] > out["pre"] and not seen:
                out["dt"].append((time.perf_counter() - out["ta"]) * 1000.0); seen = True; out["go"].set(); seen = False
            if len(out["dt"]) >= len(frames):
                break
    except Exception as e:
        out["err"] = f"{type(e).__name__}: {str(e)[:100]}"
    return out


async def main():
    a = aud(3)
    engine = AsyncLLM.from_engine_args(AsyncEngineArgs(
        model=MODEL, trust_remote_code=True, gpu_memory_utilization=0.85, max_model_len=8192,
        enforce_eager=False, limit_mm_per_prompt={"audio": 8, "image": 0}, mm_processor_cache_gb=8))
    try:
        c1 = await stream(engine, "C1_audio_at_end", [(HEAD + PH, a[0])])
        print(f"  C1_audio_at_end (no trailing): {'CRASH ' + c1['err'] if c1['err'] else 'OK txt=' + repr(c1['txt'])}")
        c2 = await stream(engine, "C2_bare_append", [(HEAD + PH + TAIL, a[0]), (PH, a[1]), (PH, a[2])])
        print(f"  C2_bare_append:                {'CRASH ' + c2['err'] if c2['err'] else 'OK txt=' + repr(c2['txt']) + ' dt=' + str([round(x) for x in c2['dt']])}")
        print("MROPE_PATCH_VALIDATE_DONE", flush=True)
    finally:
        engine.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
