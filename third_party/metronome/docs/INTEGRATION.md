# Using Metronome — developer guide

Metronome is a **control layer for real-time interaction serving**: deadline-aware
admission control + periodic-session scheduling + KV-budget management. It sits on top
of an execution backend (vLLM today; SGLang is a drop-in) and turns a throughput
engine into a deadline-aware one.

You bring a serving backend and a per-tick **frame budget** (e.g. 80 ms for Moshi,
1 s for MiniCPM-o); Metronome decides **how many concurrent sessions to admit** so
every tick meets its deadline, and **how much KV each session keeps resident** (the
cost/quality knob).

## Install

```bash
pip install -e .                 # core (numpy)
pip install -e ".[vllm]"         # + the vLLM backend (real models)
pip install -e ".[engine]"       # + the native timing engine (torch + flash-attn)
pip install -e ".[bench]"        # + the benchmark/analysis stack
```

## Quick start — real models on vLLM

```python
from metronome import MetronomeServer
from metronome.backends.vllm_backend import VLLMBackend

# 1. any vLLM-served model becomes the execution backend
backend = VLLMBackend("Qwen/Qwen3-8B",          # e.g. the MiniCPM-o 4.5 backbone
                      gpu_memory_utilization=0.6,
                      max_model_len=32768)

# 2. wrap it with Metronome: a 200 ms frame budget, 2048-token KV window per session
server = MetronomeServer(backend, frame_budget_s=0.20,
                         kv_budget_tokens=2048, tokens_per_tick=25)

# 3. calibrate the cost model to THIS backend + model (measures real per-tick latency)
server.calibrate()
print("deadline-aware capacity:", server.predicted_capacity())

# 4. admit sessions (the schedulability test gates them) and serve
for sid in incoming_session_ids:
    if server.admit(sid):        # returns False if admitting it would break a deadline
        accept(sid)
    else:
        shed_or_queue(sid)       # graceful: reject rather than miss everyone's frames

metrics = server.serve(n_sessions=server.predicted_capacity(), n_frames=50)
print(metrics["miss_rate"], metrics["p99_ms"])      # measured on the real backend
print("measured MSCS:", server.mscs())
```

`server.admit()` runs the real schedulability test (`AdmissionController`): it admits a
new session only if the whole population — at the proposed KV budget — still meets its
per-tick deadline *and* fits HBM. That is the core of Metronome: the KV budget `B_i`
is the single knob that sets both the per-tick cost (schedulability) and the resident
footprint (cost).

## How a "tick" maps onto vLLM

Each periodic session is served as a **growing, prefix-cached sequence**. Every frame,
`VLLMBackend.step(due_sids, n_new)` prefills the new input chunk over the session's
cached context (a prefix-cache hit) and decodes the output tokens — the per-tick
prefill+decode of an interaction model. vLLM owns the paged KV and batching; Metronome
owns admission and the deadline accounting. KV budgeting is enforced as a per-session
resident-context cap (sliding window).

## Serving API — OpenAI **Realtime**-compatible (not Chat Completions)

Interaction models are full-duplex streaming audio, so the right API is the **OpenAI
Realtime API** (a persistent WebSocket session with audio streaming in and out), *not*
Chat Completions (one-shot request→response). Metronome ships a Realtime-compatible
server (`metronome/realtime.py`):

```bash
pip install -e ".[realtime]"
metronome-realtime --backend vllm --model Qwen/Qwen3-8B --frame-budget 0.2 --port 8765
# or, no GPU, for protocol development:
metronome-realtime --backend mock --model moshi --frame-budget 0.08
```

A client speaks the standard Realtime protocol:

```python
import websockets, json, base64, asyncio
async def main():
    async with websockets.connect("ws://localhost:8765") as ws:
        created = json.loads(await ws.recv())          # session.created (or error: over_capacity)
        # stream audio in; receive audio out
        await ws.send(json.dumps({"type": "input_audio_buffer.append",
                                  "audio": base64.b64encode(pcm16_chunk).decode()}))
        async for raw in ws:
            ev = json.loads(raw)
            if ev["type"] == "response.audio.delta":   # audio streaming back
                play(base64.b64decode(ev["delta"]))
            elif ev["type"] == "metronome.tick":        # per-frame deadline status
                ...                                     # ev["latency_ms"], ev["deadline_met"]
asyncio.run(main())
```

**The mapping is exact** — a Realtime *session* IS Metronome's persistent periodic
session; `input_audio_buffer.append` is the per-tick input chunk; `response.audio.delta`
is the per-tick decode output; server-side VAD is silence exploitation. On top of the
standard protocol Metronome adds the two things the Realtime API lacks:

1. **Deadline-aware admission** — a connecting session is accepted only if the
   schedulability test says every session still meets its per-tick deadline; otherwise
   it is rejected gracefully (`error.code = "over_capacity"`) instead of degrading
   everyone. *No "vLLM for Realtime audio" exists today; this is the gap Metronome
   fills.*
2. **Per-tick deadline accounting** — `metronome.tick` events report the measured
   per-frame latency and whether the deadline was met (a missed 80 ms frame is an
   audible glitch).

A single frame loop runs at the model's tick cadence: each frame it micro-batches the
active sessions, executes one tick on the backend (vLLM / native engine / mock), and
streams a frame of audio to each session.

### Feature coverage (all validated end-to-end, `experiments/realtime_features.py`)

| Feature | Status |
|---|---|
| Full-duplex continuous streaming (audio + transcript + text + `metronome.tick`) | ✓ |
| Text modality (`response.text.delta`) | ✓ |
| Half-duplex turns (`turn_detection: none` + `response.create` → `response.done`) | ✓ |
| **Cancellation** (`response.cancel`; barge-in → `conversation.item.truncated`) | ✓ |
| Turn detection: `server_vad` (energy VAD → speech_started/stopped → auto-response) | ✓ |
| Turn detection: `full_duplex` (continuous, no turns — Moshi-style) | ✓ |
| Input + output **transcription** (`*.input_audio_transcription.*`, `response.audio_transcript.*`) | ✓ |
| `conversation.item.create/truncate/delete` | ✓ |
| **GPU batching** — one `backend.step` per frame over *all* due sessions | ✓ |
| Production robustness — guarded sends, session reaping, abort-on-cancel/disconnect, ping keepalive | ✓ |

Events implemented (beta naming): `session.created/updated`, `conversation.created`,
`conversation.item.created/truncated/deleted`,
`conversation.item.input_audio_transcription.delta/completed`,
`input_audio_buffer.committed/cleared/speech_started/speech_stopped`,
`response.created/done`, `response.output_item.added/done`,
`response.content_part.added/done`, `response.text.delta/done`,
`response.audio.delta/done`, `response.audio_transcript.delta/done`,
`rate_limits.updated`, `error`, and the `metronome.tick` extension.

**Real GPU batching, measured:** 3 real sessions served through the Realtime API on
vLLM (Qwen3-0.6B) ran 39 session-ticks in **13 batched GPU frames** (one `step`/frame),
all deadlines met — `experiments/realtime_vllm.py`.

**Transcription / ASR note:** the model's *output* audio transcript is real (its
generated text). *Input* audio transcription is exposed as the protocol events with a
pluggable ASR hook (a Whisper-style model drops in); the full-duplex models we target
fold input directly into the decode loop.

## Other backends

- **Native engine** (`metronome.ServingEngine`): an architecture-faithful timing engine
  (FlashAttention paged-KV decode) used to measure serving capacity without loading
  weights — for capacity/jitter studies and for validating the cost model.
- **SGLang** (the plan's eventual substrate): implement the small `Backend` protocol
  (`metronome/backends/base.py`) — `add_session`, `step`, `remove_session`,
  `context_len`, and the `kv_bytes_per_token` / `num_layers` / `hbm_kv_bytes` facts —
  and Metronome drives it unchanged.

```python
from metronome.backends.base import Backend   # Protocol: 4 methods + 3 properties
```

## What Metronome gives you that a throughput engine doesn't

| Throughput engine (vLLM/SGLang) | + Metronome |
|---|---|
| request-scoped, throughput goal | **persistent periodic sessions** with per-tick deadlines |
| admits while KV fits HBM | admits while **every tick still meets its deadline** (schedulability) |
| KV grows to the context limit | **KV budget** = the joint cost/schedulability knob |
| overload → everyone's latency climbs | **graceful**: reject excess; admitted sessions keep the SLO |
| tokens/sec, TTFT | **MSCS, p999 jitter, \$/session-hour** (`metronome`/`bench`) |

## Measured results

- **Real engine** (`RESULTS_ENGINE.md`): MSCS gain 3.2× / 4.0× / 2.67×; admission holds
  0% miss vs greedy 82% at 2× overload.
- **Real vLLM** (`results/vllm/`): Metronome calibrates from vLLM's measured per-tick
  latency and admits a safe set that holds the deadline-miss SLO on real model weights.
- The calibrated simulator (`sim/`), validated against the real engine, extends to the
  large open-system / scheduling sweeps (`RESULTS.md`, `RESULTS_PROD.md`,
  `RESULTS_SCHED.md`).
