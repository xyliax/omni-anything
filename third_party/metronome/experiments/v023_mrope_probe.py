"""Isolate the mrope 'Position ids length mismatch' crash in the vLLM 0.23 resumable AUDIO path.

Plain (non-streaming) audio works; the streaming/resumable de-risk crashed. Hypotheses:
  A) it was the truncated prompt (HEAD+PH, no <|im_end|>/assistant tail) -> fix = proper prompts
  B) it is the resumable path itself (any audio chunk) -> needs a vLLM get_mrope_input_positions fix

Variants (each a SINGLE-chunk resumable request unless noted):
  V1 full proper prompt (matches the working plain prompt)         -> isolates tail
  V2 minimal HEAD+PH (the original crasher)                        -> reproduces
  V3 two-chunk append, proper first chunk                          -> isolates append
"""
import asyncio, os, sys, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from vllm import SamplingParams
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.v1.engine.async_llm import AsyncLLM
from vllm.engine.protocol import StreamingInput

MODEL = os.environ.get("MODEL", "sammysun0711/Qwen3-Omni-30B-A3B-Instruct-FP8-Dynamic")
PH = "<|audio_start|><|audio_pad|><|audio_end|>"
HEAD = "<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n"
TAIL = "<|im_end|>\n<|im_start|>assistant\n"


def aud():
    from experiments.realtime_load import load_audio_pool
    arr, sr = load_audio_pool(2)[0]
    arr = np.asarray(arr, dtype=np.float32)
    return (arr[:int(2.0 * sr)].copy(), sr)


async def run_variant(engine, name, frames):
    """frames: list of (prompt_str, audio). Single resumable request; decode a few tokens/frame."""
    out = {"txt": "", "done": 0, "err": None}

    async def gen():
        for i, (pr, a) in enumerate(frames):
            sp = SamplingParams(temperature=0.0, max_tokens=8 * (i + 1), ignore_eos=True)
            yield StreamingInput(prompt={"prompt": pr, "multi_modal_data": {"audio": a}},
                                 sampling_params=sp)
            await asyncio.sleep(0.2)  # let the engine ingest before next append

    sp0 = SamplingParams(temperature=0.0, max_tokens=8, ignore_eos=True)
    try:
        async for o in engine.generate(gen(), sp0, f"v-{name}"):
            out["txt"] = o.outputs[0].text
            out["done"] = len(o.outputs[0].token_ids)
            if out["done"] >= 8 * len(frames):
                break
    except Exception as e:
        out["err"] = f"{type(e).__name__}: {str(e)[:120]}"
    return out


async def main():
    a = aud()
    args = AsyncEngineArgs(model=MODEL, trust_remote_code=True, gpu_memory_utilization=0.85,
                           max_model_len=8192, enforce_eager=False,
                           limit_mm_per_prompt={"audio": 8, "image": 0}, mm_processor_cache_gb=8)
    engine = AsyncLLM.from_engine_args(args)
    try:
        tests = {
            "V1_full_proper": [(HEAD + PH + "Describe the audio." + TAIL, a)],
            "V2_minimal_head_ph": [(HEAD + PH, a)],
            "V3_append_proper": [(HEAD + PH + TAIL, a), (PH, a)],
        }
        for name, frames in tests.items():
            r = await run_variant(engine, name, frames)
            verdict = "CRASH " + r["err"] if r["err"] else f"OK txt={r['txt']!r}"
            print(f"  {name}: {verdict}", flush=True)
        print("MROPE_PROBE_DONE", flush=True)
    finally:
        engine.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
