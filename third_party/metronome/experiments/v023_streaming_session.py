"""Prove the streaming-session (append-to-resident-KV) primitive on vLLM 0.23 / Qwen3-Omni / Blackwell.

The whole "minute-level full-duplex" thesis hinges on one property: when you append the new frame's
chunk to a RESIDENT request and reuse prior KV, the per-frame INGEST cost is FLAT as the context grows.
Our earlier fd_step_stream design instead re-submitted the whole growing prompt each frame, so its
per-frame `add` cost grew 60 -> 603 ms over 80 s (the measured drift). This script measures both, on the
same engine, back to back:

  A) STREAMING session  — ONE resumable request; each frame yields a StreamingInput with only the NEW
     chunk (processed resumable=True, same internal req id -> prior KV reused). Metric per frame i:
     time from appending chunk i to the FIRST new decoded token (= prefill of C new tokens; constant).

  B) RE-SUBMIT baseline — K independent requests; request i submits the CUMULATIVE prompt (i*C tokens),
     no KV reuse. Metric: time-to-first-token = prefill of i*C tokens (grows linearly). This is the
     fd_step_stream behavior.

Expected: A flat (~prefill(C)); B linear in i. Run via run_v023_omni_smoke.sh's env (CUDA_HOME=cu13 +
NVCC_APPEND_FLAGS) -- or experiments/run_v023_streaming.sh.
"""
import asyncio, os, time, statistics as st
from vllm import SamplingParams
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.v1.engine.async_llm import AsyncLLM
from vllm.engine.protocol import StreamingInput
from vllm.inputs import TokensPrompt

MODEL = os.environ.get("MODEL", "sammysun0711/Qwen3-Omni-30B-A3B-Instruct-FP8-Dynamic")
K = int(os.environ.get("FRAMES", "24"))      # number of frames (e.g. ~a minute at a 2 s frame budget)
C = int(os.environ.get("CHUNK_TOKS", "128")) # new tokens appended per frame
SEED_BASE = 1000


def chunk_tokens(i):
    # distinct, deterministic, non-special token ids per frame (avoid id 0 / specials)
    return [((i * C + j) * 131 % 90000) + 1000 for j in range(C)]


async def run_streaming(engine):
    rid = "stream-sess"
    sp = SamplingParams(temperature=0.0, max_tokens=K * 8 + 8)  # generous; we gate by token count
    state = {"out": 0, "pre": 0, "frame": 0, "t_append": [], "dt": [], "go": asyncio.Event()}

    async def gen():
        for i in range(K):
            state["pre"] = state["out"]
            state["t_append"] = state.get("t_append", [])
            state["_ta"] = time.perf_counter()
            yield StreamingInput(prompt=TokensPrompt(prompt_token_ids=chunk_tokens(i)))
            await state["go"].wait()
            state["go"].clear()

    seen_first = False
    async for out in engine.generate(gen(), sp, rid):
        n = len(out.outputs[0].token_ids)
        state["out"] = n
        if n > state["pre"] and not seen_first:
            state["dt"].append((time.perf_counter() - state["_ta"]) * 1000.0)
            seen_first = True
            state["go"].set()
            seen_first = False  # reset for next frame
        if len(state["dt"]) >= K:
            break
    return state["dt"]


async def run_resubmit(engine):
    dts = []
    for i in range(1, K + 1):
        toks = [t for j in range(i) for t in chunk_tokens(j)]  # cumulative i*C tokens
        sp = SamplingParams(temperature=0.0, max_tokens=1)
        t0 = time.perf_counter()
        async for out in engine.generate(TokensPrompt(prompt_token_ids=toks), sp, f"resub-{i}"):
            if len(out.outputs[0].token_ids) >= 1:
                dts.append((time.perf_counter() - t0) * 1000.0)
                break
    return dts


def summarize(tag, dts):
    if not dts:
        print(f"{tag}: NO DATA"); return
    first3 = st.mean(dts[:3]); last3 = st.mean(dts[-3:])
    print(f"{tag}: frames={len(dts)}  first3_avg={first3:.0f}ms  last3_avg={last3:.0f}ms  "
          f"growth={last3/max(first3,1e-9):.2f}x  p50={st.median(dts):.0f}ms")
    print(f"  per-frame ms: " + " ".join(f"{d:.0f}" for d in dts))


async def main():
    args = AsyncEngineArgs(model=MODEL, trust_remote_code=True, gpu_memory_utilization=0.85,
                           max_model_len=8192, enforce_eager=False,
                           limit_mm_per_prompt={"audio": 1, "image": 0})
    engine = AsyncLLM.from_engine_args(args)
    try:
        print(f"=== context grows to {K*C} tokens ({K} frames x {C} tok) ===", flush=True)
        s = await run_streaming(engine)
        summarize("STREAMING (resident-KV append)", s)
        r = await run_resubmit(engine)
        summarize("RE-SUBMIT  (growing prompt)    ", r)
        print("V023_STREAMING_OK", flush=True)
    finally:
        engine.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
