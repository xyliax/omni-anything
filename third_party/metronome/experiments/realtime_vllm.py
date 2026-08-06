"""Real GPU batching through the Realtime API: the Metronome Realtime server driving
the vLLM backend with a real model, batching multiple sessions per frame."""
import os
os.environ.setdefault("VLLM_LOGGING_LEVEL", "ERROR")
import asyncio
import base64
import json
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import websockets

from bench.gpu_probe import wait_for_window
from metronome.realtime import RealtimeServer, SAMPLE_RATE
from metronome.backends.vllm_backend import VLLMBackend
from metronome.serve import MetronomeServer


async def client(uri, cid, period, seconds, res):
    audio = base64.b64encode(b"\x00\x00" * int(SAMPLE_RATE * period)).decode()
    text, ticks, met = "", 0, 0
    async with websockets.connect(uri) as ws:
        await ws.recv()

        async def snd():
            while True:
                await ws.send(json.dumps({"type": "input_audio_buffer.append", "audio": audio}))
                await asyncio.sleep(period)
        s = asyncio.create_task(snd())
        dl = asyncio.get_event_loop().time() + seconds
        while asyncio.get_event_loop().time() < dl:
            try:
                ev = json.loads(await asyncio.wait_for(ws.recv(), period * 4))
            except asyncio.TimeoutError:
                continue
            if ev["type"] == "response.audio_transcript.delta":
                text += ev["delta"]
            elif ev["type"] == "metronome.tick":
                ticks += 1; met += ev["deadline_met"]
        s.cancel()
    res[cid] = {"text": text.strip()[:60], "ticks": ticks, "met": met}


async def main(model="Qwen/Qwen3-0.6B", gpu_mem=0.055, period=0.2, n_clients=3,
               port=8810):
    wait_for_window(need_free_gib=6.5, max_util_pct=88, timeout_s=7200)
    b = VLLMBackend(model, gpu_memory_utilization=gpu_mem, max_model_len=2048)
    s0 = MetronomeServer(b, frame_budget_s=period, kv_budget_tokens=512, tokens_per_tick=8)
    s0.calibrate(probe_ns=(1, 2), reps=2, verbose=False)
    b.cost = s0.cost
    srv = RealtimeServer(b, frame_budget_s=period, kv_budget_tokens=512,
                         tokens_per_tick=8, host="127.0.0.1", port=port, capacity=16,
                         response_max_tokens=40)
    print(f"real-model Realtime server ({model}), deadline-aware capacity {srv.capacity}")
    async with websockets.serve(srv.handle, "127.0.0.1", port):
        loop = asyncio.create_task(srv.frame_loop())
        res = {}
        await asyncio.gather(*[
            client(f"ws://127.0.0.1:{port}", i, period, 2.5, res)
            for i in range(n_clients)])
        loop.cancel()
    for i in sorted(res):
        print(f"  session {i}: ticks={res[i]['ticks']} deadline_met={res[i]['met']} "
              f"REAL transcript={res[i]['text']!r}")
    print(f"total batched GPU frames (one step/frame over {n_clients} sessions): {srv.frames}")
    b.shutdown()
    print("OK: real GPU batching through the Realtime API")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen3-0.6B")
    ap.add_argument("--gpu-mem", type=float, default=0.055)
    ap.add_argument("--clients", type=int, default=3)
    a = ap.parse_args()
    asyncio.run(main(a.model, a.gpu_mem, n_clients=a.clients))
