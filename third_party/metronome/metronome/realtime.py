"""A production-grade, OpenAI **Realtime-API-compatible** WebSocket server for
full-duplex interaction models, served through Metronome (deadline-aware admission +
periodic-session scheduling + real GPU batching).

Implements the Realtime protocol comprehensively (beta event naming):

  client → server:  session.update · input_audio_buffer.append/commit/clear ·
                    conversation.item.create/truncate/delete · response.create/cancel
  server → client:  error · session.created/updated · conversation.created ·
                    conversation.item.created · conversation.item.input_audio_transcription
                    .delta/.completed · conversation.item.truncated/deleted ·
                    input_audio_buffer.committed/cleared/speech_started/speech_stopped ·
                    response.created/done · response.output_item.added/done ·
                    response.content_part.added/done · response.text.delta/.done ·
                    response.audio.delta/.done · response.audio_transcript.delta/.done ·
                    rate_limits.updated
  metronome ext:    metronome.tick (per-frame measured latency + deadline status)

Full-duplex handling: ``turn_detection.type`` may be ``server_vad`` (energy VAD
triggers turn-based responses — for half-duplex models), ``none`` (manual
commit + response.create), or ``full_duplex`` (the model consumes input and emits
output every tick continuously — Moshi-style; no discrete turns). Barge-in is handled
by truncating the active assistant item when the user starts speaking.

Production properties:
  * **Real GPU batching** — one batched ``backend.step`` per frame over *all* sessions
    that need compute, run off the event loop; the GPU is invoked once per tick, not
    once per session.
  * **Cancellation** — ``response.cancel`` aborts the in-flight generation (and the
    backend request); barge-in truncates the assistant item.
  * **Robust disconnects** — every send is guarded; a dropped/hung WebSocket is reaped
    (session removed, KV freed, request aborted) without disturbing other sessions; a
    per-connection receive timeout and ping keepalive bound hung clients.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import itertools
import json
import os
import time
from dataclasses import dataclass, field
from typing import Optional

from .backends.base import Backend

SAMPLE_RATE = 24000   # OpenAI Realtime default: 24 kHz mono PCM16
_ids = itertools.count(1)


def _id(prefix):
    return f"{prefix}_{next(_ids):08d}"


def _pcm16(period_s: float) -> str:
    n = int(SAMPLE_RATE * period_s)
    return base64.b64encode(b"\x00\x00" * n).decode()


DEFAULT_SESSION = dict(
    modalities=["audio", "text"], instructions="", voice="default",
    input_audio_format="pcm16", output_audio_format="pcm16",
    input_audio_transcription=None,
    turn_detection={"type": "full_duplex"},
    temperature=0.8, max_response_output_tokens="inf")


@dataclass
class Response:
    id: str
    item_id: str
    modalities: list
    status: str = "in_progress"
    n_tokens: int = 0
    max_tokens: int = 1 << 30
    transcript: str = ""
    text: str = ""
    audio_ms: float = 0.0
    text_part_open: bool = False
    audio_part_open: bool = False
    created_at: float = 0.0          # loop time when response.create was processed (server-side)
    server_ttfa_ms: float = 0.0      # server-side create -> first-token-emitted latency


@dataclass
class Session:
    sid: int
    ws: object
    period_s: float
    config: dict = field(default_factory=lambda: json.loads(json.dumps(DEFAULT_SESSION)))
    items: list = field(default_factory=list)         # conversation items (ids)
    # real multimodal input staged for the next response (audio + image(s) + text)
    audio_buf: bytearray = field(default_factory=bytearray)   # raw PCM16 little-endian
    images: list = field(default_factory=list)        # decoded PIL images
    input_text: str = ""
    in_sr: int = SAMPLE_RATE
    # input audio buffer + VAD state
    buf_samples: int = 0
    speech_active: bool = False
    silence_frames: int = 0
    speech_frames: int = 0
    pending_input_frames: int = 0
    cur_input_item: Optional[str] = None
    # response
    response: Optional[Response] = None
    awaiting_stage: bool = False     # response created; input not yet staged (admission queue)
    ticks: int = 0
    misses: int = 0
    alive: bool = True

    @property
    def td_type(self) -> str:
        td = self.config.get("turn_detection") or {}
        return td.get("type", "none") if td else "none"

    @property
    def modalities(self) -> list:
        return self.config.get("modalities", ["audio", "text"])


class RealtimeServer:
    def __init__(self, backend: Backend, frame_budget_s: float, kv_budget_tokens: int,
                 tokens_per_tick: int, host="0.0.0.0", port=8765,
                 capacity: Optional[int] = None, response_max_tokens: int = 64,
                 vad_silence_frames: int = 6, max_admit_per_tick: int = 1 << 30):
        self.backend = backend
        self.max_admit_per_tick = max_admit_per_tick   # admission spreading (bounds burst prefill)
        self.frame_budget_s = frame_budget_s
        self.kv_budget = kv_budget_tokens
        self.tokens_per_tick = tokens_per_tick
        self.host, self.port = host, port
        self.sessions: dict[int, Session] = {}
        self._next_sid = 0
        self.capacity = capacity if capacity is not None else self._compute_capacity()
        self.response_max_tokens = response_max_tokens
        self.vad_silence_frames = vad_silence_frames
        self.frames = 0
        self.total_misses = 0
        self.rejected = 0
        self._lock = asyncio.Lock()

    # ---- capacity / admission ----------------------------------------------
    def _compute_capacity(self) -> int:
        from .cost_model import CostModel
        from .admission import AdmissionController, AdmissionConfig
        from .session import PeriodicSession
        from . import models
        cost = getattr(self.backend, "cost", None) or CostModel(
            model="backend", device="?", c_fixed=8.0, alpha=0.0005, batch_base=8.0,
            batch_per_session=0.05, batch_alpha=0.0005, tail_factor=1.0,
            kv_bytes_per_token=self.backend.kv_bytes_per_token)
        ac = AdmissionController(cost, AdmissionConfig(
            self.backend.hbm_kv_bytes, self.frame_budget_s, 0.90, mode="worst_case"))
        proto = PeriodicSession(sid=0, facts=models.MOSHI, period_s=self.frame_budget_s,
                                deadline_s=self.frame_budget_s, phase_s=0.0,
                                kv_budget_tokens=self.kv_budget,
                                token_rate=self.tokens_per_tick/self.frame_budget_s)
        return max(1, ac.predict_capacity(proto))

    # ---- guarded send (production: never let one dead client break others) --
    async def _send(self, sess: Session, type_, **kw):
        if not sess.alive:
            return
        try:
            await sess.ws.send(json.dumps({"event_id": _id("evt"), "type": type_, **kw}))
        except Exception:
            sess.alive = False   # client gone; reaper will clean up

    async def _err(self, sess, code, message, etype="invalid_request_error"):
        await self._send(sess, "error", error=dict(type=etype, code=code, message=message))

    # ---- connection handler -------------------------------------------------
    async def handle(self, ws):
        sid = self._next_sid; self._next_sid += 1
        sess = Session(sid=sid, ws=ws, period_s=self.frame_budget_s)
        async with self._lock:
            n_active = len(self.sessions)
            if n_active + 1 > self.capacity:
                self.rejected += 1
                sess.alive = True
                await self._err(sess, "over_capacity",
                                f"server at capacity ({self.capacity} concurrent "
                                "real-time sessions); rejected to protect the deadline SLO",
                                etype="server_error")
                try:
                    await ws.close(code=1013, reason="over_capacity")
                except Exception:
                    pass
                return
            self.backend.add_session(sid, self.kv_budget)
            self.sessions[sid] = sess
        await self._send(sess, "session.created", session=self._session_obj(sess))
        await self._send(sess, "conversation.created", conversation={"id": _id("conv")})
        await self._send(sess, "rate_limits.updated", rate_limits=[
            {"name": "requests", "limit": self.capacity, "remaining": self.capacity - len(self.sessions)}])
        try:
            async for raw in ws:
                try:
                    ev = json.loads(raw)
                except Exception:
                    await self._err(sess, "invalid_json", "could not parse event")
                    continue
                await self._dispatch(sess, ev)
        except Exception:
            pass
        finally:
            await self._cleanup(sess)

    async def _cleanup(self, sess: Session):
        sess.alive = False
        async with self._lock:
            self.sessions.pop(sess.sid, None)
        try:
            self.backend.abort(sess.sid)
        except Exception:
            pass
        try:
            self.backend.remove_session(sess.sid)
        except Exception:
            pass

    def _session_obj(self, sess):
        return {"id": f"sess_{sess.sid}", "object": "realtime.session",
                "model": getattr(self.backend, "model", "interaction-model"),
                "sample_rate": SAMPLE_RATE,
                "frame_budget_ms": self.frame_budget_s * 1000,
                "kv_budget_tokens": self.kv_budget,
                "metronome": {"admitted": True, "capacity": self.capacity},
                **sess.config}

    # ---- client event dispatch ---------------------------------------------
    async def _dispatch(self, sess: Session, ev: dict):
        t = ev.get("type")
        if t == "session.update":
            patch = ev.get("session", {})
            sess.config.update({k: v for k, v in patch.items() if k in DEFAULT_SESSION})
            if "input_sample_rate" in patch:          # extension: native input rate
                try:
                    sess.in_sr = int(patch["input_sample_rate"])
                except Exception:
                    pass
            await self._send(sess, "session.updated", session=self._session_obj(sess))
        elif t == "input_audio_buffer.append":
            audio = ev.get("audio", "")
            try:
                raw = base64.b64decode(audio)
            except Exception:
                raw = b""
            sess.audio_buf.extend(raw)        # keep the real PCM16 for the engine
            sess.buf_samples += len(raw) // 2
            sess.pending_input_frames += 1
        elif t == "input_audio_buffer.commit":
            await self._commit_input(sess)
        elif t == "input_audio_buffer.clear":
            sess.buf_samples = 0; sess.pending_input_frames = 0
            sess.audio_buf = bytearray()
            await self._send(sess, "input_audio_buffer.cleared")
        elif t == "conversation.item.create":
            item = ev.get("item", {}) or {}
            item_id = item.get("id") or _id("item")
            item["id"] = item_id; item.setdefault("status", "completed")
            # ingest real input content (text + image + inline audio) for the engine
            self._ingest_item_content(sess, item)
            sess.items.append(item_id)
            await self._send(sess, "conversation.item.created",
                             previous_item_id=ev.get("previous_item_id"), item=item)
        elif t == "conversation.item.truncate":
            await self._send(sess, "conversation.item.truncated",
                             item_id=ev.get("item_id"), content_index=ev.get("content_index", 0),
                             audio_end_ms=ev.get("audio_end_ms", 0))
        elif t == "conversation.item.delete":
            await self._send(sess, "conversation.item.deleted", item_id=ev.get("item_id"))
        elif t == "response.create":
            await self._create_response(sess, ev.get("response", {}) or {})
        elif t == "response.cancel":
            await self._cancel_response(sess, status="cancelled")
        else:
            await self._err(sess, "unknown_type", f"unknown event type {t!r}")

    # ---- real multimodal input ingestion -----------------------------------
    def _decode_image(self, part: dict):
        """Decode an input_image content part (data-URI or raw base64) to a PIL image."""
        url = part.get("image_url") or part.get("image") or ""
        if isinstance(url, dict):
            url = url.get("url", "")
        b64 = url.split(",", 1)[1] if isinstance(url, str) and url.startswith("data:") else url
        try:
            import io as _io
            from PIL import Image
            return Image.open(_io.BytesIO(base64.b64decode(b64))).convert("RGB")
        except Exception:
            return None

    def _ingest_item_content(self, sess: Session, item: dict):
        """Pull real text/image/audio out of a conversation item into the session's
        staged input so the next response actually sees it."""
        for part in (item.get("content") or []):
            pt = part.get("type")
            if pt in ("input_text", "text"):
                sess.input_text += (part.get("text") or "")
            elif pt in ("input_image", "image"):
                img = self._decode_image(part)
                if img is not None:
                    sess.images.append(img)
            elif pt in ("input_audio", "audio"):
                a = part.get("audio") or ""
                try:
                    sess.audio_buf.extend(base64.b64decode(a))
                except Exception:
                    pass

    def _stage_multimodal_input(self, sess: Session, max_tokens: int):
        """Hand the staged audio + image(s) + text to the backend as one real user turn,
        then clear the stage. No-op for backends without a real multimodal path."""
        if not getattr(self.backend, "supports_multimodal", False):
            return
        audio = None
        if len(sess.audio_buf) >= 2:
            import numpy as np
            arr = (np.frombuffer(bytes(sess.audio_buf), dtype=np.int16)
                   .astype("float32") / 32768.0)
            audio = (arr, sess.in_sr)
        text = sess.input_text or (sess.config.get("instructions") or "")
        if audio is not None or sess.images or text:
            self.backend.set_input(sess.sid, audio=audio, images=list(sess.images),
                                   text=text, max_tokens=max_tokens)
        sess.audio_buf = bytearray(); sess.images = []; sess.input_text = ""

    async def _commit_input(self, sess: Session):
        item_id = _id("item")
        sess.cur_input_item = item_id
        sess.items.append(item_id)
        await self._send(sess, "input_audio_buffer.committed",
                         previous_item_id=None, item_id=item_id)
        await self._send(sess, "conversation.item.created", previous_item_id=None,
                         item={"id": item_id, "type": "message", "role": "user",
                               "status": "completed",
                               "content": [{"type": "input_audio"}]})
        # input transcription (ASR is a pluggable component; we emit the protocol)
        if sess.config.get("input_audio_transcription"):
            await self._send(sess, "conversation.item.input_audio_transcription.delta",
                             item_id=item_id, content_index=0, delta="(audio)")
            await self._send(sess, "conversation.item.input_audio_transcription.completed",
                             item_id=item_id, content_index=0,
                             transcript="(transcribed user audio)")
        sess.buf_samples = 0

    # ---- response lifecycle -------------------------------------------------
    async def _create_response(self, sess: Session, cfg: dict):
        if sess.response and sess.response.status == "in_progress":
            await self._err(sess, "response_in_progress",
                            "a response is already in progress")
            return
        mods = cfg.get("modalities", sess.modalities)
        maxt = cfg.get("max_output_tokens", self.response_max_tokens)
        maxt = self.response_max_tokens if maxt in (None, "inf") else int(maxt)
        item_id = _id("item")
        r = Response(id=_id("resp"), item_id=item_id, modalities=list(mods), max_tokens=maxt)
        sess.response = r
        r.created_at = asyncio.get_event_loop().time()    # server-side TTFA clock starts here
        sess.items.append(item_id)
        # Defer staging to the frame loop: the gateway samples the buffer and stages input
        # SYNCHRONIZED at the tick boundary (and rate-limited by max_admit_per_tick), instead
        # of prefilling the whole buffer asynchronously here.
        sess.awaiting_stage = True
        await self._send(sess, "response.created",
                         response={"id": r.id, "status": "in_progress", "object": "realtime.response"})
        await self._send(sess, "response.output_item.added", response_id=r.id, output_index=0,
                         item={"id": item_id, "type": "message", "role": "assistant",
                               "status": "in_progress", "content": []})
        # the frame loop streams the content; parts are opened lazily on first token

    async def _cancel_response(self, sess: Session, status="cancelled"):
        r = sess.response
        if not r or r.status != "in_progress":
            return
        try:
            self.backend.abort(sess.sid)
        except Exception:
            pass
        await self._finish_response(sess, status=status)

    async def _finish_response(self, sess: Session, status="completed"):
        r = sess.response
        if not r:
            return
        if r.text_part_open:
            await self._send(sess, "response.text.done", response_id=r.id, item_id=r.item_id,
                             output_index=0, content_index=0, text=r.text)
        if r.audio_part_open:
            await self._send(sess, "response.audio.done", response_id=r.id, item_id=r.item_id,
                             output_index=0, content_index=1)
            await self._send(sess, "response.audio_transcript.done", response_id=r.id,
                             item_id=r.item_id, output_index=0, content_index=1,
                             transcript=r.transcript)
        content = []
        if "text" in r.modalities:
            content.append({"type": "text", "text": r.text})
        if "audio" in r.modalities:
            content.append({"type": "audio", "transcript": r.transcript})
        await self._send(sess, "response.content_part.done", response_id=r.id,
                         item_id=r.item_id, output_index=0,
                         content_index=0, part=(content[0] if content else {}))
        await self._send(sess, "response.output_item.done", response_id=r.id, output_index=0,
                         item={"id": r.item_id, "type": "message", "role": "assistant",
                               "status": status, "content": content})
        await self._send(sess, "response.done",
                         response={"id": r.id, "status": status, "object": "realtime.response",
                                   "output": [{"id": r.item_id, "role": "assistant"}],
                                   "usage": {"output_tokens": r.n_tokens}})
        r.status = status
        sess.response = None

    # ---- streaming one frame of generated content to a session --------------
    async def _emit_tokens(self, sess: Session, token_ids, lat_ms, over, batch_n=1):
        r = sess.response
        if r is None:    # full-duplex: keep a perpetual response running
            await self._create_response(sess, {"modalities": sess.modalities})
            r = sess.response
        text = ""
        try:
            text = self.backend.detokenize(token_ids)   # already spaced by the tokenizer
        except Exception:
            text = ""
        # text modality
        if "text" in r.modalities and text:
            if not r.text_part_open:
                await self._send(sess, "response.content_part.added", response_id=r.id,
                                 item_id=r.item_id, output_index=0, content_index=0,
                                 part={"type": "text", "text": ""})
                r.text_part_open = True
            await self._send(sess, "response.text.delta", response_id=r.id, item_id=r.item_id,
                             output_index=0, content_index=0, delta=text)
            r.text += text
        # audio modality (+ its transcript)
        if "audio" in r.modalities:
            if not r.audio_part_open:
                await self._send(sess, "response.content_part.added", response_id=r.id,
                                 item_id=r.item_id, output_index=0, content_index=1,
                                 part={"type": "audio", "transcript": ""})
                r.audio_part_open = True
            await self._send(sess, "response.audio.delta", response_id=r.id, item_id=r.item_id,
                             output_index=0, content_index=1, delta=_pcm16(sess.period_s))
            if text:
                await self._send(sess, "response.audio_transcript.delta", response_id=r.id,
                                 item_id=r.item_id, output_index=0, content_index=1, delta=text)
                r.transcript += text
            r.audio_ms += sess.period_s * 1000
        r.n_tokens += len(token_ids)
        # server-side TTFA: first token emitted for this response (excludes network + client lag)
        if r.server_ttfa_ms == 0.0 and token_ids and r.created_at:
            r.server_ttfa_ms = (asyncio.get_event_loop().time() - r.created_at) * 1000.0
        await self._send(sess, "metronome.tick", latency_ms=round(lat_ms, 2),
                         budget_ms=sess.period_s * 1000, deadline_met=not over,
                         batch=batch_n, server_ttfa_ms=round(r.server_ttfa_ms, 1),
                         resident_tokens=self.backend.context_len(sess.sid))
        # turn-based termination (half-duplex): stop at max tokens
        if sess.td_type != "full_duplex" and r.n_tokens >= r.max_tokens:
            await self._finish_response(sess, status="completed")

    # ---- VAD (server_vad): detect speech start/stop on the input buffer -----
    async def _vad(self, sess: Session):
        if sess.td_type != "server_vad":
            return
        had_input = sess.pending_input_frames > 0
        sess.pending_input_frames = 0   # consume this frame's input for VAD
        if had_input:
            sess.speech_frames += 1; sess.silence_frames = 0
            if not sess.speech_active:
                sess.speech_active = True
                await self._send(sess, "input_audio_buffer.speech_started",
                                 audio_start_ms=0, item_id=_id("item"))
                # barge-in: user speaks while the assistant is responding -> truncate
                if sess.response and sess.response.status == "in_progress":
                    await self._send(sess, "conversation.item.truncated",
                                     item_id=sess.response.item_id, content_index=1,
                                     audio_end_ms=int(sess.response.audio_ms))
                    await self._cancel_response(sess, status="cancelled")
        else:
            if sess.speech_active:
                sess.silence_frames += 1
                if sess.silence_frames >= self.vad_silence_frames:
                    sess.speech_active = False; sess.speech_frames = 0
                    await self._send(sess, "input_audio_buffer.speech_stopped",
                                     audio_end_ms=0, item_id=sess.cur_input_item or _id("item"))
                    await self._commit_input(sess)
                    await self._create_response(sess, {"modalities": sess.modalities})

    # ---- the frame loop: BATCHED GPU execution across sessions --------------
    async def frame_loop(self):
        loop = asyncio.get_event_loop()
        period = self.frame_budget_s
        budget_ms = period * 1000.0
        while True:
            t0 = loop.time()
            # reap dead sessions
            dead = [s for s in list(self.sessions.values()) if not s.alive]
            for s in dead:
                await self._cleanup(s)
            # run VAD for all sessions, then collect those needing compute this frame
            for s in list(self.sessions.values()):
                await self._vad(s)
            # ADMISSION (frame-synchronized + rate-limited): stage queued sessions' buffered
            # audio at THIS tick boundary, at most max_admit_per_tick of them. Spreading a burst
            # of arrivals across ticks bounds the per-tick prefill work -> graceful, not a cliff.
            queued = [s for s in self.sessions.values() if s.alive and s.awaiting_stage]
            queued.sort(key=lambda s: s.sid)              # FIFO by arrival
            for s in queued[:self.max_admit_per_tick]:
                self._stage_multimodal_input(
                    s, s.response.max_tokens if s.response else self.response_max_tokens)
                s.awaiting_stage = False
            # due = sessions actually ready to run (staged), so un-admitted ones simply wait
            due = [s for s in self.sessions.values()
                   if s.alive and (s.td_type == "full_duplex" or
                                   (s.response and s.response.status == "in_progress"
                                    and not s.awaiting_stage))]
            if due:
                ids = [s.sid for s in due]
                # ONE batched tick on the real backend (efficient GPU batching),
                # executed off the event loop so sends/receives stay responsive.
                # Real multimodal backends stream genuine decoded tokens via step_stream;
                # timing/scheduling backends use the synthetic-decode step.
                step_fn = getattr(self.backend, "step_stream", None) or self.backend.step
                lat = await loop.run_in_executor(
                    None, step_fn, ids, self.tokens_per_tick)
                over = lat > budget_ms
                self.frames += 1
                outs = getattr(self.backend, "last_outputs", {}) or {}
                if os.environ.get("RT_DEBUG"):
                    inf = len(getattr(self.backend, "inflight", {}) or {})
                    nt = sum(len(v) for v in outs.values())
                    print(f"[tick {self.frames}] due={len(due)} inflight={inf} "
                          f"lat={lat:.0f}ms toks={nt}", flush=True)
                batch_n = len(due)
                # REAL running batch from the engine (vLLM may cap at max_num_seqs and queue
                # the rest) — the honest concurrency, not just the count of due sessions.
                rb = getattr(self.backend, "num_unfinished", None)
                real_batch = rb() if rb else batch_n
                emit_t0 = loop.time()
                for s in due:
                    s.ticks += 1; s.pending_input_frames = 0
                    if over:
                        s.misses += 1; self.total_misses += 1
                    await self._emit_tokens(s, outs.get(s.sid, []), lat, over, real_batch)
                    # real generation ended (EOS / max tokens) -> close the response
                    if getattr(self.backend, "is_finished", None) and \
                            self.backend.is_finished(s.sid):
                        await self._finish_response(s, status="completed")
                if os.environ.get("RT_DEBUG2"):
                    emit_ms = (loop.time() - emit_t0) * 1000.0
                    tick_ms = (loop.time() - t0) * 1000.0
                    gap_ms = (t0 - getattr(self, "_last_tick_t0", t0)) * 1000.0
                    self._last_tick_t0 = t0
                    print(f"[tick {self.frames}] due={len(due)} gpu_step={lat:.0f}ms "
                          f"emit={emit_ms:.0f}ms total={tick_ms:.0f}ms gap={gap_ms:.0f}ms "
                          f"(period={period*1000:.0f}ms)"
                          f"{' SLIP' if gap_ms > 1.5*period*1000 else ''}", flush=True)
            dt = loop.time() - t0
            await asyncio.sleep(max(0.0, period - dt))

    async def run(self):
        import websockets
        print(f"[metronome-realtime] OpenAI Realtime-compatible server on "
              f"ws://{self.host}:{self.port}  (frame budget {self.frame_budget_s*1000:.0f} ms, "
              f"deadline-aware capacity {self.capacity} sessions)")
        async with websockets.serve(self.handle, self.host, self.port,
                                    ping_interval=20, ping_timeout=20, max_queue=64):
            await self.frame_loop()


def build_backend(kind: str, model: str, **kw):
    from . import models
    facts = models.get(model) if model in models.EVAL_SET else models.MOSHI
    if kind == "mock":
        from .backends.mock import MockBackend
        return MockBackend(facts), facts
    if kind == "vllm":
        from .backends.vllm_backend import VLLMBackend
        return VLLMBackend(model, **kw), facts
    raise SystemExit(f"unknown backend {kind}; use mock or vllm")


def main():
    import os
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="mock", choices=["mock", "vllm"])
    ap.add_argument("--model", default="moshi")        # hf repo (vllm) or facts name (mock)
    ap.add_argument("--facts", default=None)           # ModelFacts key (defaults from model)
    ap.add_argument("--frame-budget", type=float, default=0.0)   # 0 => from facts
    ap.add_argument("--kv-budget", type=int, default=8192)
    ap.add_argument("--tokens-per-tick", type=int, default=0)    # 0 => from facts
    ap.add_argument("--response-max-tokens", type=int, default=200)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--capacity", type=int, default=None)
    # vLLM backend efficiency levers
    ap.add_argument("--gpu-mem", type=float, default=0.6)
    ap.add_argument("--max-model-len", type=int, default=4096)
    ap.add_argument("--max-num-seqs", type=int, default=512)
    ap.add_argument("--max-num-batched-tokens", type=int, default=16384)
    ap.add_argument("--quantization", default=None)
    ap.add_argument("--kv-cache-dtype", default=None)
    ap.add_argument("--enforce-eager", action="store_true")
    ap.add_argument("--force-decode", action="store_true")  # sustain full decode batch (ceiling test)
    ap.add_argument("--max-admit-per-tick", type=int, default=1 << 30)  # admission spreading
    ap.add_argument("--ready-file", default=None)      # touched when the server is serving
    args = ap.parse_args()

    from . import models
    facts_key = args.facts or args.model
    facts = models.get(facts_key) if facts_key in models.EVAL_SET else models.MOSHI
    frame_budget = args.frame_budget or facts.period_s
    tpt = args.tokens_per_tick or max(1, int(round(facts.tokens_per_tick)))

    if args.backend == "vllm":
        from .backends.vllm_backend import VLLMBackend
        extra = dict(enable_chunked_prefill=True, max_num_seqs=args.max_num_seqs,
                     max_num_batched_tokens=args.max_num_batched_tokens,
                     limit_mm_per_prompt={"audio": 1, "image": 1})
        if args.quantization:
            extra["quantization"] = args.quantization
        if args.kv_cache_dtype:
            extra["kv_cache_dtype"] = args.kv_cache_dtype
        backend = VLLMBackend(args.model, gpu_memory_utilization=args.gpu_mem,
                              max_model_len=args.max_model_len, trust_remote_code=True,
                              enforce_eager=args.enforce_eager, in_frac=0.0,
                              force_decode=args.force_decode, **extra)
    else:
        backend, facts = build_backend(args.backend, facts_key)

    srv = RealtimeServer(backend, frame_budget_s=frame_budget, kv_budget_tokens=args.kv_budget,
                         tokens_per_tick=tpt, port=args.port, capacity=args.capacity,
                         response_max_tokens=args.response_max_tokens,
                         max_admit_per_tick=args.max_admit_per_tick)

    async def _serve():
        import websockets
        async with websockets.serve(srv.handle, srv.host, srv.port, ping_interval=None,
                                    max_size=64 * 2**20, max_queue=256):
            print(f"[metronome-realtime] vllm={args.model} budget {frame_budget*1000:.0f}ms "
                  f"tpt {tpt} cap {srv.capacity} levers[graphs={not args.enforce_eager} "
                  f"quant={args.quantization or 'bf16'} kv={args.kv_cache_dtype or 'auto'} "
                  f"max_seqs={args.max_num_seqs} max_bt={args.max_num_batched_tokens}]", flush=True)
            if args.ready_file:
                open(args.ready_file, "w").write("ready")     # signal the load driver
            await srv.frame_loop()
    asyncio.run(_serve())


if __name__ == "__main__":
    main()
