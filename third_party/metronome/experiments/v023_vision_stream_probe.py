"""Does the vLLM 0.23 streaming (append-to-resident-KV) path support VISION (+ audio), like the
windowed path? Tests, on one resumable Qwen3-Omni request:

  P0 plain image (non-streaming control)            -> does 0.23 image work at all here?
  P1 streaming: append an IMAGE chunk               -> image in a resumable request
  P2 streaming: append IMAGE then AUDIO then IMAGE  -> mixed vision+audio resident KV

Each streaming chunk carries a trailing token after the placeholder (and FIX 4 reconcile is in place).
"""
import asyncio, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from PIL import Image
from vllm import LLM, SamplingParams
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.v1.engine.async_llm import AsyncLLM
from vllm.engine.protocol import StreamingInput

MODEL = os.environ.get("MODEL", "sammysun0711/Qwen3-Omni-30B-A3B-Instruct-FP8-Dynamic")
VPH = "<|vision_start|><|image_pad|><|vision_end|>"
APH = "<|audio_start|><|audio_pad|><|audio_end|>"
HEAD = "<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n"
TAIL = "<|im_end|>\n<|im_start|>assistant\n"


def img(color):
    return Image.new("RGB", (448, 448), color)


def aud():
    from experiments.realtime_load import load_audio_pool
    a, sr = load_audio_pool(2)[0]
    return (np.asarray(a, dtype=np.float32)[:int(2.0 * sr)].copy(), sr)


def plain_image_control():
    llm = LLM(model=MODEL, trust_remote_code=True, gpu_memory_utilization=0.85, max_model_len=8192,
              limit_mm_per_prompt={"audio": 0, "image": 1})
    pr = HEAD + VPH + "What color is this image?" + TAIL
    try:
        o = llm.generate([{"prompt": pr, "multi_modal_data": {"image": img((200, 30, 30))}}],
                         SamplingParams(temperature=0, max_tokens=16))
        print(f"  P0 plain_image: OK txt={o[0].outputs[0].text[:80]!r}")
    except Exception as e:
        import traceback; traceback.print_exc(); print(f"  P0 plain_image: CRASH {type(e).__name__}: {str(e)[:100]}")


async def stream(engine, name, frames):
    out = {"txt": "", "n": 0, "err": None, "dt": [], "go": asyncio.Event(), "pre": 0, "ta": 0.0}

    async def gen():
        for i, (pr, mm) in enumerate(frames):
            out["pre"] = out["n"]; out["ta"] = time.perf_counter()
            sp = SamplingParams(temperature=0.0, max_tokens=8 * (i + 1), ignore_eos=True)
            yield StreamingInput(prompt={"prompt": pr, "multi_modal_data": mm}, sampling_params=sp)
            await out["go"].wait(); out["go"].clear()
    seen = False
    try:
        async for o in engine.generate(gen(), SamplingParams(temperature=0, max_tokens=8, ignore_eos=True), name):
            out["n"] = len(o.outputs[0].token_ids); out["txt"] = o.outputs[0].text
            if out["n"] > out["pre"] and not seen:
                out["dt"].append((time.perf_counter() - out["ta"]) * 1000.0); seen = True; out["go"].set(); seen = False
            if len(out["dt"]) >= len(frames):
                break
    except Exception as e:
        out["err"] = f"{type(e).__name__}: {str(e)[:110]}"
    return out


async def streaming_tests():
    engine = AsyncLLM.from_engine_args(AsyncEngineArgs(
        model=MODEL, trust_remote_code=True, gpu_memory_utilization=0.85, max_model_len=8192,
        enforce_eager=False, limit_mm_per_prompt={"audio": 4, "image": 4}, mm_processor_cache_gb=8))
    try:
        p1 = await stream(engine, "P1_img", [(HEAD + VPH + "\n", {"image": img((30, 200, 30))})])
        print(f"  P1 stream_image:        {'CRASH ' + p1['err'] if p1['err'] else 'OK txt=' + repr(p1['txt'][:60])}")
        p2 = await stream(engine, "P2_mix", [
            (HEAD + VPH + "\n", {"image": img((30, 30, 200))}),
            (APH + "\n", {"audio": aud()}),
            (VPH + "\n", {"image": img((200, 200, 30))}),
        ])
        print(f"  P2 stream_image+audio:  {'CRASH ' + p2['err'] if p2['err'] else 'OK txt=' + repr(p2['txt'][:60]) + ' dt=' + str([round(x) for x in p2['dt']])}")
    finally:
        engine.shutdown()


if __name__ == "__main__":
    plain_image_control()
    asyncio.run(streaming_tests())
    print("V023_VISION_PROBE_DONE", flush=True)
