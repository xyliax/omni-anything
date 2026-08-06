"""tau-interact-mm — a simplified, MULTIMODAL version of tau2-bench's TauVoice, for
benchmarking the interaction capability of small real-time models through the Realtime API.

Keeps TauVoice's three load-bearing ideas, drops what's too hard for small models, adds vision:
  * 200 ms discrete ticks                — the Realtime server's frame clock drives turns.
  * LLM-driven user simulator (voice)    — a local Qwen3 (vLLM, OpenAI API) plays a goal-directed
                                           user; its lines are spoken via MMS-TTS into the agent.
  * tool-free interaction correctness    — tau2's COMMUNICATE (required facts said) + NL_ASSERTION
                                           (LLM-judged), NO database/tool-calling.
  * + multimodality                      — the agent SEES a real image (Realtime input_image) and
                                           the user asks about it across turns.

Everything goes through the Metronome Realtime API (audio + image + text in), exactly as a
production client would. Reports per-task success, component pass rates, and real-time stats
(per-turn latency, frames, missed deadlines).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")

from bench.gpu_probe import wait_for_window
from bench.realtime_client import RealtimeClient
from bench.user_sim import UserSimulator, judge_assertion, communicate_ok
from experiments.bench_spoken_qa import OMNI

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "results", "tau_interact")


def load_image(name, max_side=1024):
    from vllm.assets.image import ImageAsset
    img = ImageAsset(name).pil_image
    m = max(img.size)                      # downscale: fewer vision tokens, faster prefill
    if m > max_side:
        s = max_side / m
        img = img.resize((int(img.width * s), int(img.height * s)))
    return img


async def run_task(uri, task, image, base_url, usersim_model, tts, max_turns):
    cli = await RealtimeClient.connect(uri)
    await cli.configure(modalities=["text"], input_sample_rate=tts.sr,
                        instructions="You are a helpful voice assistant who can see the "
                        "image the user is referring to. Answer briefly and specifically.")
    sim = UserSimulator(base_url, usersim_model, task["goal"], task.get("persona", "a user"))
    agent_turns, dialogue, rt = [], [], []
    utt, done = sim.first()
    for turn in range(min(max_turns, task.get("max_turns", max_turns))):
        ctx = ("You are a voice assistant looking at the attached image. Answer the user's "
               "spoken question based ONLY on what YOU actually see in the image; be specific "
               "and concise. Do not say 'the user mentioned' — describe what you see."
               + (" Recent context: " + " | ".join(dialogue[-2:]) if dialogue else ""))
        await cli.attach_image(image, text=ctx)
        wav, sr = tts.say(utt)
        await cli.append_audio(wav, sr)
        r = await cli.respond(modalities=["text"])
        atext = r["text"]
        agent_turns.append(atext)
        rt.append(dict(latency_s=round(r["latency_s"], 2), ticks=r["ticks"], missed=r["missed"]))
        dialogue.append(f"User: {utt}")
        dialogue.append(f"Assistant: {atext}")
        if done:
            break
        utt, done = sim.reply(atext)
    await cli.close()

    transcript = " ".join(agent_turns)
    comm = communicate_ok(task.get("communicate_info", []), transcript)
    nls = [judge_assertion(base_url, usersim_model, a, transcript)
           for a in task.get("nl_assertions", [])]
    success = (all(comm) if comm else True) and (all(nls) if nls else True)
    return dict(id=task["id"], image=task["image"], success=bool(success),
                communicate=comm, nl_assertions=nls, turns=len(agent_turns),
                dialogue=dialogue, rt=rt)


async def main_async(args):
    from metronome.backends.vllm_backend import VLLMBackend
    from metronome.realtime import RealtimeServer
    from bench.tts import MMSTTS
    import websockets

    hf, _, default_mem = OMNI[args.agent_model]
    gpu_mem = args.gpu_mem or default_mem
    print(f"[load] agent {hf} (gpu_mem={gpu_mem}) ...", flush=True)
    backend = VLLMBackend(hf, gpu_memory_utilization=gpu_mem, max_model_len=args.max_len,
                          trust_remote_code=True, enforce_eager=True,
                          limit_mm_per_prompt={"audio": 1, "image": 1})
    print("[load] MMS-TTS user voice ...", flush=True)
    tts = MMSTTS(device="cpu")
    srv = RealtimeServer(backend, frame_budget_s=args.frame_budget, kv_budget_tokens=2048,
                         tokens_per_tick=args.tokens_per_tick, port=args.port, capacity=8)
    tasks = json.load(open(os.path.join(HERE, "tau_interact_mm", "tasks.json")))
    if args.n_tasks:
        tasks = tasks[:args.n_tasks]
    images = {t["image"]: load_image(t["image"]) for t in tasks}
    uri = f"ws://127.0.0.1:{args.port}"
    print(f"[bench] tau-interact-mm: {len(tasks)} tasks, agent={args.agent_model}, "
          f"user-sim={args.usersim_model} @ {args.usersim_base_url}", flush=True)
    results = []
    async with websockets.serve(srv.handle, "127.0.0.1", args.port,
                                ping_interval=None, max_size=64 * 2**20):
        floop = asyncio.create_task(srv.frame_loop())
        for t in tasks:
            try:
                r = await run_task(uri, t, images[t["image"]], args.usersim_base_url,
                                   args.usersim_model, tts, args.max_turns)
            except Exception as e:
                import traceback; traceback.print_exc()
                r = dict(id=t["id"], image=t["image"], success=False,
                         error=f"{type(e).__name__}: {str(e)[:160]}")
            results.append(r)
            ok = "OK" if r.get("success") else "x"
            print(f"  [{ok}] {r['id']}: comm={r.get('communicate')} "
                  f"nl={r.get('nl_assertions')} turns={r.get('turns')}", flush=True)
            for d in r.get("dialogue", [])[:6]:
                print(f"        {d[:90]}")
        floop.cancel()
    backend.shutdown()

    n = len(results)
    succ = sum(r.get("success", False) for r in results)
    lat = [x["latency_s"] for r in results for x in r.get("rt", [])]
    missed = sum(x["missed"] for r in results for x in r.get("rt", []))
    ticks = sum(x["ticks"] for r in results for x in r.get("rt", []))
    agg = dict(benchmark="tau-interact-mm", agent_model=args.agent_model, served_hf=hf,
               usersim_model=args.usersim_model, n_tasks=n, success_rate=round(succ / max(1, n), 3),
               mean_turn_latency_s=round(sum(lat) / max(1, len(lat)), 2),
               deadline_met_rate=round(1 - missed / max(1, ticks), 3), via="realtime-api",
               tasks=results)
    os.makedirs(OUT, exist_ok=True)
    fn = os.path.join(OUT, f"{args.agent_model}.json")
    json.dump(agg, open(fn, "w"), indent=2)
    print(f"\n=== tau-interact-mm / {args.agent_model} via Realtime API ===")
    print(f"  success {succ}/{n} = {agg['success_rate']:.0%}  | mean turn latency "
          f"{agg['mean_turn_latency_s']}s | deadline-met {agg['deadline_met_rate']:.0%}")
    print(f"  saved {fn}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent-model", choices=list(OMNI), default="qwen-omni")
    ap.add_argument("--usersim-base-url", default="http://127.0.0.1:8000/v1")
    ap.add_argument("--usersim-model", default="Qwen/Qwen3-8B")
    ap.add_argument("--n-tasks", type=int, default=0)
    ap.add_argument("--max-turns", type=int, default=4)
    ap.add_argument("--gpu-mem", type=float, default=0.0)
    ap.add_argument("--need-free-gib", type=float, default=24.0)
    ap.add_argument("--max-util", type=int, default=98)
    ap.add_argument("--max-len", type=int, default=4096)
    ap.add_argument("--frame-budget", type=float, default=0.2)
    ap.add_argument("--tokens-per-tick", type=int, default=4)
    ap.add_argument("--port", type=int, default=8830)
    args = ap.parse_args()
    print(f"=== tau-interact-mm: waiting for GPU window (>= {args.need_free_gib} GiB) ===",
          flush=True)
    wait_for_window(need_free_gib=args.need_free_gib, max_util_pct=args.max_util, timeout_s=36000)
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
