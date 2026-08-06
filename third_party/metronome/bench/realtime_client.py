"""A small async client for the Metronome OpenAI-Realtime-compatible server.

This is the single surface every end-to-end benchmark drives: connect, stream real
audio and/or attach a real image, ask for a response, and collect the streamed answer.
No benchmark talks to the engine directly — they all go through the Realtime API, exactly
as a production developer would.
"""
from __future__ import annotations

import base64
import json
import time

import numpy as np


def pcm16_b64(arr: np.ndarray) -> str:
    a = np.clip(np.asarray(arr, dtype=np.float32), -1.0, 1.0)
    return base64.b64encode((a * 32767.0).astype("<i2").tobytes()).decode()


def image_data_uri(pil_img, fmt="PNG") -> str:
    import io
    buf = io.BytesIO(); pil_img.save(buf, format=fmt)
    return f"data:image/{fmt.lower()};base64," + base64.b64encode(buf.getvalue()).decode()


class RealtimeClient:
    def __init__(self, ws):
        self.ws = ws

    @classmethod
    async def connect(cls, uri):
        import websockets
        ws = await websockets.connect(uri, max_size=64 * 2**20)
        self = cls(ws)
        await self._recv_until({"session.created"})
        return self

    async def _send(self, type_, **kw):
        await self.ws.send(json.dumps({"type": type_, **kw}))

    async def _recv_until(self, types):
        while True:
            ev = json.loads(await self.ws.recv())
            if ev.get("type") in types:
                return ev

    async def configure(self, modalities=("text",), input_sample_rate=16000,
                        instructions="", turn_detection="none"):
        await self._send("session.update", session={
            "modalities": list(modalities), "input_sample_rate": int(input_sample_rate),
            "instructions": instructions,
            "turn_detection": ({"type": turn_detection} if turn_detection else None)})
        await self._recv_until({"session.updated"})

    async def append_audio(self, arr, sr, chunk_ms=200):
        """Stream PCM16 audio in chunks, like a real client mic feed."""
        n = max(1, int(sr * chunk_ms / 1000))
        for i in range(0, len(arr), n):
            await self._send("input_audio_buffer.append", audio=pcm16_b64(arr[i:i + n]))

    async def attach_image(self, pil_img, text=None):
        content = [{"type": "input_image", "image_url": image_data_uri(pil_img)}]
        if text:
            content.append({"type": "input_text", "text": text})
        await self._send("conversation.item.create",
                         item={"type": "message", "role": "user", "content": content})
        await self._recv_until({"conversation.item.created"})

    async def add_text(self, text):
        await self._send("conversation.item.create",
                         item={"type": "message", "role": "user",
                               "content": [{"type": "input_text", "text": text}]})
        await self._recv_until({"conversation.item.created"})

    async def respond(self, modalities=("text",), timeout_s=120.0):
        """Ask for a response and collect the streamed answer + timing. Captures TTFA
        (time-to-first-token/audio) and the per-tick latencies reported by the server."""
        import asyncio
        t0 = time.time()
        await self._send("response.create", response={"modalities": list(modalities)})
        text, ticks, missed, ttfa = "", 0, 0, None
        tick_ms, batch, sttfa = [], [], 0.0
        while True:
            ev = json.loads(await asyncio.wait_for(self.ws.recv(), timeout=timeout_s))
            ty = ev.get("type")
            if ty in ("response.text.delta", "response.audio.delta",
                      "response.audio_transcript.delta"):
                if ttfa is None:
                    ttfa = time.time() - t0
                if ty == "response.text.delta":
                    text += ev.get("delta", "")
            elif ty == "metronome.tick":
                ticks += 1
                tick_ms.append(float(ev.get("latency_ms", 0.0)))
                batch.append(int(ev.get("batch", 1)))
                if sttfa == 0.0:
                    sttfa = float(ev.get("server_ttfa_ms", 0.0))
                if not ev.get("deadline_met", True):
                    missed += 1
            elif ty == "response.done":
                break
            elif ty == "error":
                raise RuntimeError(ev.get("error"))
        return dict(text=text.strip(), latency_s=time.time() - t0,
                    ttfa_s=ttfa if ttfa is not None else (time.time() - t0),
                    server_ttfa_ms=sttfa,
                    ticks=ticks, missed=missed, tick_ms=tick_ms, batch=batch)

    async def close(self):
        try:
            await self.ws.close()
        except Exception:
            pass
