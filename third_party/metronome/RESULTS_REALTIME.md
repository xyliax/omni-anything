# Real-time interaction serving — Realtime API + unified benchmarks

Everything here runs **through the Metronome OpenAI-Realtime-compatible WebSocket API**
(audio + image + text in), not via custom calls — the same surface a production developer
would use. Benchmarks are Realtime API clients (`bench/realtime_client.py`).

## The Realtime API is a real multimodal responder

`metronome/realtime.py` + `VLLMBackend` accept **simultaneous vision + audio + text** and
feed `multi_modal_data` to the engine, streaming genuine decoded tokens frame-by-frame
with deadline-aware batched scheduling.

Verified end-to-end (real image + real 15.9 s speech clip in one session):
> *"I see a street scene with a red stop sign in the foreground and a large red gate in
> the background. I hear applause and a man speaking."* — **6.3× real-time**.

## Unified audio benchmark across the three paper models

The three interaction models share only **speech**, so the cross-model axis is
audio-question-in → answer-out, scored on the benchmarks the model papers themselves used
(Moshi: Llama/Web Questions; Qwen2.5-Omni: LibriSpeech). Omni models run on vLLM; Moshi
runs in its own venv (needs torch<2.10) with the identical scorer.

| Model | Llama Questions (acc ↑) | Web Questions (acc ↑) | LibriSpeech WER (↓) |
|-------|-------------------------|-----------------------|---------------------|
| **Qwen2.5-Omni-7B** | 0.775 | 0.45 | **0.026** |
| **MiniCPM-o 4.5**   | **0.875** | 0.45 | 0.29 |
| **Moshi** | 0.775 | 0.175 | — (dialogue model) |

Reference points: Moshi's paper reports LlamaQ 0.623 / WebQ 0.266 (w/ inner monologue) —
ours: **0.775 / 0.175** (Moshi rambles conversationally but lands the answer; WebQ's
diverse answers hurt inclusion). Qwen2.5-Omni reports ~2% WER on LibriSpeech clean —
ours: **0.026**, matches. MiniCPM-o ASR is weaker here (0.29) — partly genuine, partly
its Qwen3 backbone wrapping transcripts in reasoning.

Metric: normalized inclusion match (spoken QA), WER (ASR). n = 40/dataset. All served
through the Realtime API with per-frame deadline accounting.

## Vision (omni models only — Moshi has no vision)

MMStar multiple-choice through the Realtime API image path (n=40): **Qwen2.5-Omni 0.325**,
**MiniCPM-o 0.375**. (MMStar is deliberately hard; this is the serving path, not a tuned
eval harness.)

## FD-Bench v1 — Moshi full-duplex turn-taking

Moshi served via native full-duplex streaming; its audio-token output is Mimi-decoded to
waveform, transcribed (whisper base.en, CPU), and scored by the FD-Bench evaluators:

| Task | Metric | Moshi |
|------|--------|-------|
| smooth_turn_taking (candor, 120) | take-turn rate (↑) | **1.0** — responds at every turn boundary |
| pause_handling (synthetic, 138)  | take-OVER rate (↓) | **1.0** — barges in at every pause (very interruptive) |

A faithful full-duplex result: Moshi is eager — it always takes the floor, which is great
for responsiveness (turn-taking) but poor for pause-handling (it interrupts).

## τ-interact-mm — simplified multimodal TauVoice (cross-model)

Voiced LLM user-sim (MMS-TTS) over 200 ms ticks → Realtime API → omni agent sees a real
image and answers; tool-free COMMUNICATE + NL-assertion judge:

| Agent | User-sim | Success | Turn latency | Deadline-met |
|-------|----------|---------|--------------|--------------|
| **MiniCPM-o** | Qwen3-1.7B | **4/4 = 100%** | 4.08 s | 96% |
| **Qwen2.5-Omni** | Qwen3-1.7B | 4/4 = 100% | 1.0 s | 73% |
| **Qwen2.5-Omni** | Qwen3-8B | 3/4 = 75% | 1.13 s | 77% |

(The stronger 8B user-sim asks harder/more-varied questions, lowering success — a sign the
benchmark discriminates.)

### Notes / gotchas found and fixed
- **MiniCPM-o audio** needs vLLM's literal placeholder `(<audio>./</audio>)` (not the
  `<|audio_start|>` special tokens) or the engine crashes on the first audio sample. Its
  Qwen3 backbone also emits `<think>` reasoning — disabled via `/no_think`.
- **ASR** scoring strips the model's "The original content of this audio is: …" preamble
  and gives 256 response tokens so long sentences aren't truncated (WER 0.41 → 0.026).
- **Window guard** auto-aligns to `gpu_memory_utilization × total` so a vLLM init never
  fails after the guard passes.

## τ-interact-mm — simplified multimodal TauVoice (interaction benchmark)

A simplified, multimodal version of tau2-bench's TauVoice for small real-time models
(`experiments/tau_interact_mm.py`). Keeps TauVoice's three load-bearing ideas — **200 ms
discrete ticks**, an **LLM-driven user simulator** (local Qwen3 via vLLM, voiced with
MMS-TTS), and **interaction-correctness eval** (tau2's tool-free `COMMUNICATE` +
`NL_ASSERTION`) — and adds **vision**: the agent sees a real image and the user asks about
it over multi-turn voice.

**Result (Qwen2.5-Omni agent, Qwen3-1.7B user-sim, MMS-TTS voice):** **4/4 tasks = 100%
success** (COMMUNICATE + every NL-assertion judged True), mean turn latency 1.0 s,
deadline-met 73%. Sample — the agent genuinely sees the image:
> User (spoken): *"Can you tell me what this traffic sign means?"* → Assistant: *"The
> traffic sign means STOP."* · User: *"What color and shape is the sign?"* → Assistant:
> *"The sign is red and octagonal."*

Engineering notes: the shared GPU thrashes, so the dual-model run retries on the memory
race and defaults to a Qwen3-1.7B user-sim (8B available via `--usersim-model` for a clean
window). Large images are downscaled (≤1024 px) to bound per-turn vision-token prefill;
the Qwen3 user-sim/judge run with thinking disabled so they emit clean JSON.
