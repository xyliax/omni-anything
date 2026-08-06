"""Demo/test for the OpenAI Realtime-like server: streams audio over WebSockets and
shows Metronome's deadline-aware admission (graceful over-capacity rejection).

Runs the server (mock backend, no GPU) and N clients in one process. Each client
opens a Realtime session, streams input_audio_buffer.append frames, and collects
response.audio.delta + metronome.tick events. Excess clients beyond the deadline-aware
capacity are rejected with error.code = "over_capacity".
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import websockets

from metronome.realtime import RealtimeServer, SAMPLE_RATE
from metronome.backends.mock import MockBackend
from metronome import models


async def client(uri, cid, seconds, period_s, results):
    audio_in = base64.b64encode(b"\x00\x00" * int(SAMPLE_RATE * period_s)).decode()
    try:
        async with websockets.connect(uri, open_timeout=5) as ws:
            created = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
            if created.get("type") == "error":
                results[cid] = {"admitted": False,
                                "reason": created["error"]["code"]}
                return
            r = {"admitted": True, "audio_frames": 0, "ticks": 0, "met": 0, "missed": 0}
            results[cid] = r
            deadline = asyncio.get_event_loop().time() + seconds

            async def send_input():
                while asyncio.get_event_loop().time() < deadline:
                    await ws.send(json.dumps({"type": "input_audio_buffer.append",
                                              "audio": audio_in}))
                    await asyncio.sleep(period_s)
            sender = asyncio.create_task(send_input())
            while asyncio.get_event_loop().time() < deadline:
                try:
                    ev = json.loads(await asyncio.wait_for(ws.recv(), timeout=period_s*4))
                except asyncio.TimeoutError:
                    break
                if ev["type"] == "response.audio.delta":
                    r["audio_frames"] += 1
                elif ev["type"] == "metronome.tick":
                    r["ticks"] += 1
                    r["met" if ev["deadline_met"] else "missed"] += 1
            sender.cancel()
    except Exception as e:
        results.setdefault(cid, {"admitted": False, "reason": f"err:{type(e).__name__}"})


async def run(n_clients=8, seconds=2.0):
    facts = models.MOSHI
    # cap capacity at 4 via a deliberately heavy mock cost model
    from metronome.cost_model import CostModel
    cost = CostModel(model="moshi", device="cpu", c_fixed=10, alpha=0.001,
                     batch_base=10, batch_per_session=12.0, batch_alpha=0.001,
                     tail_factor=1.0, kv_bytes_per_token=facts.kv_bytes_per_token)
    backend = MockBackend(facts, cost=cost)
    srv = RealtimeServer(backend, frame_budget_s=0.08, kv_budget_tokens=1024,
                         tokens_per_tick=2, host="127.0.0.1", port=8799)
    print(f"deadline-aware capacity: {srv.capacity} sessions")
    async with websockets.serve(srv.handle, "127.0.0.1", 8799):
        loop_task = asyncio.create_task(srv.frame_loop())
        results = {}
        await asyncio.gather(*[
            client("ws://127.0.0.1:8799", i, seconds, 0.08, results)
            for i in range(n_clients)])
        loop_task.cancel()

    admitted = [c for c, r in results.items() if r.get("admitted")]
    rejected = [c for c, r in results.items() if not r.get("admitted")]
    print(f"\nclients={n_clients}  admitted={len(admitted)}  "
          f"rejected={len(rejected)} (reason={set(results[c]['reason'] for c in rejected) if rejected else '-'})")
    for c in sorted(admitted):
        r = results[c]
        print(f"  session {c}: audio_frames={r['audio_frames']} ticks={r['ticks']} "
              f"deadline_met={r['met']} missed={r['missed']}")
    ok = (len(admitted) == srv.capacity and len(rejected) == n_clients - srv.capacity
          and all(results[c]["audio_frames"] > 0 for c in admitted))
    print(f"\n{'PASS' if ok else 'CHECK'}: admission held capacity {srv.capacity}, "
          f"streamed real-time audio to admitted sessions, rejected the rest gracefully.")
    return ok


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--clients", type=int, default=8)
    ap.add_argument("--seconds", type=float, default=2.0)
    a = ap.parse_args()
    asyncio.run(run(a.clients, a.seconds))
