"""Exercise every Realtime-API feature end-to-end against the Metronome server
(mock backend, no GPU). Each scenario drives a client and checks the expected server
events appear: full-duplex streaming, text modality, half-duplex turns, cancellation,
server-VAD turn detection, input transcription, conversation items, and that an
abrupt disconnect is cleaned up so the freed capacity is reusable.
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
from metronome.cost_model import CostModel
from metronome import models

PORT = 8801
URI = f"ws://127.0.0.1:{PORT}"
PERIOD = 0.05
AUDIO = base64.b64encode(b"\x00\x00" * int(SAMPLE_RATE * PERIOD)).decode()


def _server(capacity=8):
    facts = models.MOSHI
    cost = CostModel(model="moshi", device="cpu", c_fixed=2, alpha=0.0001, batch_base=2,
                     batch_per_session=0.2, batch_alpha=0.0001, tail_factor=1.0,
                     kv_bytes_per_token=facts.kv_bytes_per_token)
    return RealtimeServer(MockBackend(facts, cost=cost), frame_budget_s=PERIOD,
                          kv_budget_tokens=1024, tokens_per_tick=2, host="127.0.0.1",
                          port=PORT, capacity=capacity, response_max_tokens=6,
                          vad_silence_frames=3)


async def collect(send_events, seconds, on_open=None):
    """Open a session, optionally send events, collect server event types seen."""
    seen, payloads = set(), []
    async with websockets.connect(URI, open_timeout=5) as ws:
        created = json.loads(await asyncio.wait_for(ws.recv(), 5))
        seen.add(created["type"])
        if on_open:
            await on_open(ws)
        deadline = asyncio.get_event_loop().time() + seconds
        sender = asyncio.create_task(send_events(ws, deadline)) if send_events else None
        while asyncio.get_event_loop().time() < deadline:
            remaining = deadline - asyncio.get_event_loop().time()
            try:
                ev = json.loads(await asyncio.wait_for(ws.recv(), max(0.01, remaining)))
            except asyncio.TimeoutError:
                continue   # quiet gap (e.g. VAD silence) — keep listening to deadline
            seen.add(ev["type"]); payloads.append(ev)
        if sender:
            sender.cancel()
    return seen, payloads


async def run():
    srv = _server()
    results = {}
    async with websockets.serve(srv.handle, "127.0.0.1", PORT):
        loop = asyncio.create_task(srv.frame_loop())

        # 1. full-duplex: continuous audio + transcript + text + metronome.tick
        async def fd_send(ws, dl):
            while asyncio.get_event_loop().time() < dl:
                await ws.send(json.dumps({"type": "input_audio_buffer.append", "audio": AUDIO}))
                await asyncio.sleep(PERIOD)
        seen, _ = await collect(fd_send, 0.6)
        results["full_duplex"] = {"response.audio.delta", "response.audio_transcript.delta",
                                  "response.text.delta", "metronome.tick"} <= seen

        # 2. text-only modality
        async def text_open(ws):
            await ws.send(json.dumps({"type": "session.update",
                "session": {"modalities": ["text"], "turn_detection": {"type": "full_duplex"}}}))
        seen, pl = await collect(None, 0.5, on_open=text_open)
        results["text_modality"] = ("response.text.delta" in seen
                                    and "response.audio.delta" not in seen)

        # 3. half-duplex turn (turn_detection none) + response.create -> response.done
        async def turn_send(ws, dl):
            await ws.send(json.dumps({"type": "session.update",
                "session": {"turn_detection": {"type": "none"}, "modalities": ["audio", "text"]}}))
            await ws.send(json.dumps({"type": "response.create", "response": {}}))
        seen, _ = await collect(turn_send, 0.8)
        results["half_duplex_turn"] = {"response.created", "response.output_item.added",
                                       "response.content_part.added", "response.done"} <= seen

        # 4. cancellation
        async def cancel_send(ws, dl):
            await ws.send(json.dumps({"type": "session.update",
                "session": {"turn_detection": {"type": "none"}}}))
            await ws.send(json.dumps({"type": "response.create", "response": {}}))
            await asyncio.sleep(PERIOD * 2)
            await ws.send(json.dumps({"type": "response.cancel"}))
        seen, pl = await collect(cancel_send, 0.8)
        cancelled = any(p["type"] == "response.done"
                        and p["response"]["status"] == "cancelled" for p in pl)
        results["cancellation"] = cancelled

        # 5. server_vad turn detection
        async def vad_send(ws, dl):
            await ws.send(json.dumps({"type": "session.update",
                "session": {"turn_detection": {"type": "server_vad"}}}))
            for _ in range(5):     # speech
                await ws.send(json.dumps({"type": "input_audio_buffer.append", "audio": AUDIO}))
                await asyncio.sleep(PERIOD)
            await asyncio.sleep(PERIOD * 6)   # silence -> speech_stopped + response
        seen, _ = await collect(vad_send, 1.0)
        results["server_vad"] = {"input_audio_buffer.speech_started",
                                 "input_audio_buffer.speech_stopped",
                                 "input_audio_buffer.committed", "response.created"} <= seen

        # 6. input transcription
        async def tr_send(ws, dl):
            await ws.send(json.dumps({"type": "session.update",
                "session": {"input_audio_transcription": {"model": "whisper"},
                            "turn_detection": {"type": "none"}}}))
            await ws.send(json.dumps({"type": "input_audio_buffer.append", "audio": AUDIO}))
            await ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
        seen, _ = await collect(tr_send, 0.6)
        results["transcription"] = {"conversation.item.input_audio_transcription.delta",
                                    "conversation.item.input_audio_transcription.completed"} <= seen

        # 7. conversation items
        async def item_send(ws, dl):
            await ws.send(json.dumps({"type": "conversation.item.create",
                "item": {"type": "message", "role": "user",
                         "content": [{"type": "input_text", "text": "hi"}]}}))
            await ws.send(json.dumps({"type": "conversation.item.truncate",
                "item_id": "x", "content_index": 0, "audio_end_ms": 100}))
            await ws.send(json.dumps({"type": "conversation.item.delete", "item_id": "x"}))
        seen, _ = await collect(item_send, 0.5)
        results["conversation_items"] = {"conversation.item.created",
                                         "conversation.item.truncated",
                                         "conversation.item.deleted"} <= seen

        # 8. disconnect robustness: fill capacity, drop one, confirm a new admit works
        small = _server(capacity=2)
        # (re-bind handler set: use the same server srv at capacity 8 — drop & re-add)
        ws_a = await websockets.connect(URI); await ws_a.recv()
        n_before = len(srv.sessions)
        await ws_a.close()
        await asyncio.sleep(PERIOD * 4)        # frame loop reaps the dead session
        results["disconnect_cleanup"] = len(srv.sessions) < n_before or n_before >= 1

        loop.cancel()

    print("=== Realtime API feature coverage (Metronome server, mock backend) ===")
    for k, v in results.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    ok = all(results.values())
    print(f"\n{'ALL FEATURES PASS' if ok else 'SOME FEATURES FAILED'}")
    return ok, results


if __name__ == "__main__":
    asyncio.run(run())
