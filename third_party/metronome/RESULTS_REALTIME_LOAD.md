# Real-time serving capacity — end-to-end on real silicon

All numbers are measured on a real RTX PRO 6000 Blackwell GPU with real vLLM continuous batching,
real LibriSpeech audio, and N concurrent real WebSocket clients through the OpenAI-Realtime API —
never a synthetic kernel, never direct `engine.step()` (except the decode-roofline microbench,
which is explicitly a real-vLLM/real-weights `engine.step()` probe).

> **Reading order note.** This document was written as the investigation progressed and went
> through several corrections. This top section is the **final, reconciled understanding**;
> §"Superseded interpretations" at the end lists the wrong turns and why. Where an early
> hypothesis was overturned, the later evidence wins.

## SUSTAINED continuous full-duplex — the real operating mode (2026-06-23, AUTHORITATIVE)

This is the measurement that matters and **supersedes the turn-based section below**. A real
full-duplex application is *N sessions each streaming 20 ms audio chunks CONTINUOUSLY for minutes*,
with output flowing back every frame — never discrete turns. The question is not "how many clients
can issue an occasional short turn" (the turn-based numbers below conflate idle gaps with capacity)
but **how many continuous streams hold their deadline for the whole session, as the audio context
grows to minute scale**. Harness: `experiments/sustained_fd.py` + `run_sustained*.sh` driving the Go
gateway `full_duplex` mode; latency is bucketed by elapsed time to expose drift. Raw JSON in
`results/sustained_fd/`.

Capacities below are **pinned with a fine grid + ceiling search** (not just powers of 2): the
largest N holding the deadline for the full 120–200 s session is reported, with the marginal/failing
neighbours so the bound is explicit.

> **2026-06-24 — all four models re-measured with full rigor (distinct phase-staggered streams,
> p50/p90/p99, frame-delivery/cadence check, latency-SLO framing).** This fixed two artifacts: a
> **prefix-cache dedup** that inflated the 30B (a shared 64-clip pool let phase-aligned sessions reuse
> each other's audio prefill — see the 30B section), and a **frame-delivery blind spot** for Moshi (its
> self-reported `gpu_ms` is unsynchronized, so "0 % miss" hid a 2× cadence slip). The reliable
> real-time test is **frame-delivery completeness** (did each session actually get duration/period
> frames on cadence), not just the deadline flag. Capacities below are the corrected, distinct-stream
> numbers; the **production reading is the per-SLO table**, since a 2 s frame is a deadline, not a good
> user experience. Raw per-N p50/p90/p99: `results/sustained_fd/all_models_distinct_curve.csv`.

> **2026-06-24 (latest) — STREAMING SESSIONS in vLLM: the 8 s window is GONE; minute-level context
> at flat-then-plateau latency, verified correct.** Ported the TML "streaming sessions" idea into
> vLLM (SGLang 0.5.13 needs a CUDA-13 toolchain we don't have + has no Qwen2.5-Omni model; vLLM
> already serves all the models). Mechanism: feed audio as a GROWING LIST of stable 2 s chunks —
> vLLM's mm-processor cache reuses prior chunks' encoder output and prefix caching reuses their KV,
> so each frame only the NEW chunk is encoded+prefilled over a **resident minute-level context** (no
> re-encode window). `worker/server.py --streaming-sessions`; `fd_step_stream()`. **Verified:**
> resident context grew to **96 s (uncapped)**, **flat over 100 s** (drift +12 ms), and **correct
> full-duplex** (30B solo 1/1, load N=8 → 8/8 sessions answer their own question, every frame).
>
> **Windowed (8 s memory, flat) vs streaming (minute-level memory, drifts→plateaus) — the tradeoff:**
>
> | model (budget) | windowed-8 s capacity (flat) | **streaming minute-level capacity** | streaming drift over 90 s |
> |---|---|---|---|
> | **Qwen3-30B-A3B FP8** (2 s) | ~320 | **~128** (192 marginal) | +524 ms @128 (bounded by ctx cap) |
> | **MiniCPM-o-4.5** (1 s) | 48 | **~8** | +358 ms @8 (1 s budget is brutal for long ctx) |
> | **Qwen2.5-Omni-7B** (2 s) | ~16 | **~8** | ≈flat @8 (encoder-bound either way) |
> | **Moshi** (80 ms) | 16 (native incremental) | 16 — *already* streaming (Mimi) | flat |
>
> **This is the core law, now shown by toggling one engine:** minute-level resident context costs
> 2–6× capacity *and* introduces drift (per-frame attention grows with the context until the chunk
> cap, then plateaus), whereas the 8 s window is flat+high-capacity but forgets everything older than
> 8 s. The 30B holds up best (light Qwen3 encoder + MoE + 2 s budget → ~128 minute-level streams);
> MiniCPM/7B drop hard (tight budget / encoder-bound). Per-N p50/p90/p99 + drift:
> `results/sustained_fd/st{7b,mcpm,30b}*.json`. **Choose per use case:** windowed for max concurrency
> with short memory; streaming for true minute-level conversations at lower concurrency.

**Sustained capacity by latency SLO (distinct streams, 0 % miss + ≥90 % frame delivery, 60–120 s):**

> **2026-06-24 (later) — ALL serving is now vLLM; the HF-eager incremental path was deleted.** The
> 7B was moved from the eager incremental backend onto vLLM `fd_step` (same path as MiniCPM/30B), and
> `streaming_omni.py`, `streaming_worker.py`, `moe_fused.py`, `run_sustained.sh`, `streaming_capacity.py`,
> `incremental_window_scaling.py`, `admission_test.py`, `qwen_incremental_proto.py` were removed so only
> the vLLM path remains. The eager 7B was both slower (~5× engine penalty) **and incorrect** (6/16
> sessions under load); vLLM fixes correctness (8/8). One consequence: there is **no longer a
> minute-level incremental path** — all omni models are 8 s-windowed (the framework still has no
> incremental mm-KV on one GPU). The 7B number below is now its vLLM windowed capacity.

| model (frame budget) | path / context | p99 ≤ 500 ms | **p99 ≤ 1 s** | p99 ≤ 1.5 s | 2 s frame-deadline edge | bound by |
|---|---|---|---|---|---|---|
| **Moshi** (80 ms) | native Mimi, **voice-in→voice-out** | n/a | n/a | n/a | **16 @ its 80 ms budget** (cadence ~81 ms, 99 % delivery; cliff to 202 ms at N=20, starves ≥24) | per-frame I/O + fixed-batch worker |
| **MiniCPM-o-4.5** (1 s) | vLLM `fd_step`, 8 s window | 8 | **48** | (>budget) | (>budget) | dense-8B LLM + 1 s budget |
| **Qwen3-Omni-30B-A3B FP8** (2 s) | vLLM `fd_step`, 8 s window | 16 | ~120 | ~236 | **~320** (384 → 17 % miss; 512 collapses) | LLM (cheap: MoE 3B-active + FP8) |
| **Qwen2.5-Omni-7B** (2 s) | vLLM `fd_step`, 8 s window | ~4 | ~7 | ~12 | **~16** (24 → 67 % miss; 32 collapses) | **audio encoder** (LLM is tiny) |

**Headline production numbers (p99 ≤ 1 s, distinct streams): MiniCPM 48 · 30B ~120 · 7B ~7 · Moshi 16 (@80 ms).**

**Note on Moshi:** the p99-SLO columns (500 ms–2 s) apply only to the 1–2 s-budget omni models. Moshi's
frame interval *is* **80 ms**, so its only meaningful SLO is "frame completes within 80 ms," measured by
**frame-delivery cadence** — its self-reported `gpu_ms` (53–71 ms) is *unsynchronized* and is not the real
per-frame time (real cadence ~81 ms at N=16, 202 ms at N=20). Capacity = **16** at the 80 ms budget.

**Why the 7B is the smallest model but the lowest capacity — it is audio-ENCODER-bound, not LLM-bound.**
Its LLM is the lightest here (28 layers, 57 KB/token KV — *half* the 30B's), so its per-session cost
should be the *lowest*; instead it is the highest (α ≈ 91 ms/session vs the 30B's 4.4). The only large
per-session cost left is the **Qwen2.5-Omni audio encoder re-encoding the 8 s window every frame** (the
30B's Qwen3 encoder + FP8 is far cheaper). A shorter window or an incremental encoder would help the 7B
specifically — its bottleneck is the encoder, not the engine or the LLM.

### Correctness under load (verified end-to-end, not assumed)

Each session streams a real spoken question; we score whether it answers *its own* question
(`experiments/fd_correctness_probe.py`), solo vs at load:

| model | solo | under load | verdict |
|---|---|---|---|
| Qwen3-30B-A3B FP8 | correct | **128/128 @ N=128** | clean; answers directly |
| MiniCPM-o-4.5 | 1/1 (assembled) | **48/48 @ N=48** (assembled) | correct; per-frame score lower only because Qwen3 *thinking-mode* interleaves reasoning (same solo & loaded — not a load effect) |
| Qwen2.5-7B (vLLM) | 1/1 strict | **8/8 @ N=8 (strict ≥80 % of ticks)** | clean; **fixes the eager backend's 6/16** |
| Moshi | coherent | **coherent @ N=16, 0 err, voice every frame** | conversational (not QA): output stays real English under load, same character as solo |

No model showed load-induced correctness degradation; outputs at concurrency match solo.

### Analytical model — predict capacity from architecture + frame interval

Fit per model (`experiments/capacity_model.py`): per-frame wall time **T(N) = T_fixed + α·N**, so
**capacity N\*(B) = (B − T_fixed) / α** for frame budget B.

| model | T_fixed | α (ms/session) | α / active-param | N\* predicted | measured |
|---|---|---|---|---|---|
| MiniCPM-o-4.5 (dense 8B) | 335 ms | 13.3 | 1.66 | 50 @ 1 s | ~48 ✓ |
| Qwen3-30B-A3B (MoE 3B-act, FP8) | 454 ms | 4.4 | 1.48 | 349 @ 2 s | ~320 ✓ |
| Qwen2.5-7B (dense, encoder-bound) | 335 ms | 91 | 13.0 | 18 @ 2 s | ~16 ✓ |

The model and its mechanism:
- **α decomposes as α = α_LLM + α_enc.** α_LLM ≈ κ_engine · P_active · (L_window + tpt) — the
  window-prefill + decode through the LLM; α_enc ≈ the audio-encoder cost of re-encoding the window.
- **When LLM-bound, α ∝ *active* params:** α/P_active is ~constant (**~1.5**) for MiniCPM and the 30B on
  the same engine (vLLM). This is *the* reason a 30B MoE (3 B active) beats a dense 8 B — capacity tracks
  active params, and MoE sparsity is a 2–3× multiplier. (HF-eager inflated κ_engine ~5×, hence the
  deleted eager 7B's α/P_active ≈ 8.)
- **When encoder-bound, α is set by α_enc, not the LLM:** the 7B's α/P_active (13) is the outlier
  because its heavy audio encoder dominates — its tiny LLM is irrelevant.
- **Frame interval B enters linearly:** doubling the budget ~doubles capacity (minus T_fixed). This is
  why MiniCPM (1 s) tops out far below the 30B (2 s) even before the architecture difference.
- **Validity:** linear up to the collapse knee; beyond N\* the frame overruns and misses compound
  super-linearly (the cliff). Use it to *predict the knee*, not past it.

Predicted SLO capacities (from the law) match the measured table within the grid spacing.

#### Design implications — which architecture serves the most streams/GPU (for the survey)

Ranked by leverage on sustained capacity:
1. **Sparse MoE LLM (few *active* params) is the biggest LLM-side win.** Capacity ∝ active params, so a
   30B-A3B (3 B active) gets ~2–3× the LLM headroom of a dense 8 B — the MoE 30B is the most efficient
   here *despite* being nominally largest.
2. **A light / streaming audio encoder matters as much as the LLM and can erase its advantage.** The
   audio front-end (encoder forward + per-frame audio-token count) is α_enc; a heavy offline-style
   encoder (Whisper-large, full self-attention re-encoded every frame) makes a model encoder-bound.
3. **Use a real engine (vLLM): FP8 + fused kernels are ~5× on κ_engine** vs HF-eager.
4. **A bigger frame interval buys capacity linearly** — except tight-budget native-codec models (Moshi,
   80 ms) which instead rely on bounded streaming state.
5. **Incremental encoding** (encode only the new block, not re-encode the window) is the specific fix for
   encoder-bound models — would rescue the 7B; not yet available (vLLM has no incremental mm-KV).

**Most efficient design = sparse-MoE LLM + light/streaming audio encoder + low audio-token rate + FP8 +
the largest tolerable frame budget.** Qwen3-Omni-30B-A3B-FP8 hits most of these → highest capacity.

**Worked case — MiniCPM-o-4.5 (α=13) vs Qwen2.5-Omni-7B (α=91), both a Qwen ~7–8 B LLM.** MiniCPM's LLM
is the *bigger* one (36 vs 28 layers, 8 vs 4 KV-heads, 147 vs 57 KB/token KV), yet its per-session cost is
7× lower — so the cost is **not** the LLM. MiniCPM stays LLM-bound (encoder ≈ free); Qwen2.5-Omni is
encoder-bound (~80 of its 91 ms is the heavy audio front-end re-encoding the 8 s window). Pairing a good
LLM with a heavy audio encoder wastes the LLM — the audio front-end is a first-class capacity determinant.

The earlier single-number "pinned" table is superseded by the SLO table above. Key corrections vs. it:
**Moshi 48 → 16** (the 48 counted `gpu_ms` latency, not frame delivery; only 16 streams actually hold
the 80 ms cadence e2e — GPU-alone batched is higher, but the e2e/fixed-batch worker caps at 16), and
**30B "≥512" → ~128 @ p99 ≤ 1 s / ~320 @ the 2 s edge** (dedup artifact). MiniCPM (48) and the 7B
(~22–28, duration-dependent) held up. Per-model curves and the 30B detail follow.

| ~~Qwen3-Omni-30B-A3B FP8~~ *(superseded)* | ~~incremental (HF transformers eager)~~ | ~~infeasible (≈0)~~ | ~~17.3 s/frame at N=1~~ — **the backend, not the model; see below** | | |

### UPDATE (2026-06-24) — the 30B is NOT infeasible; the honest distinct-stream, production-SLO numbers

The "infeasible (≈0)" verdict was an artifact of the **execution backend** (HF-transformers eager
incremental), not of the 30B. Served through **vLLM** on the *same real end-to-end harness used for
every other model* — N concurrent clients streaming real LibriSpeech audio in 20 ms chunks
continuously through the Go gateway (`full_duplex`) → gRPC → vLLM `fd_step` worker → output, sustained
75–90 s, latency bucketed by elapsed time (`experiments/run_sustained_vllm.sh` with
`MODEL=sammysun0711/Qwen3-Omni-30B-A3B-Instruct-FP8-Dynamic PERIOD_MS=2000 WINDOW_S=8`) — the 30B is
real-time at very useful concurrency. Two corrections vs. the first cut of this update:

1. **Distinct streams, not a shared clip pool.** The first sweep drew audio from a 64-clip pool, so at
   N>64 multiple sessions streamed *identical, phase-aligned* 8 s windows → vLLM **prefix-cache dedups
   the audio encode+prefill** → optimistic capacity (it reported "≥512 @ 0 % miss"). Real users say
   *different* things. With a per-session phase offset so **no two windows ever coincide**
   (`FD_PHASE_STAGGER=1`), the dedup vanishes and **N=512 collapses to 100 % miss (2.6 s/frame)** and
   **N=384 fails (16.7 % miss)**. The numbers below are all distinct-stream.
2. **A 2 s frame is not a production latency.** Capacity "at the 2 s budget edge" is the scheduling
   deadline, not a good user experience — a marginal 2 s response is sluggish. We report p50/p90/p99
   and the capacity at several latency SLOs so the production number is explicit.

**Distinct-stream per-N latency (sustained, 0 % miss unless noted; `results/sustained_fd/sv30b_distinct_curve.csv`):**

| N | 1 | 8 | 16 | 32 | 64 | 128 | 256 | 320 | 384 | 512 |
|---|---|---|---|---|---|---|---|---|---|---|
| p50 (ms) | 143 | 295 | 381 | 462 | 650 | 922 | 1406 | 1683 | 1916 | 2425 |
| p90 (ms) | 144 | 312 | 391 | 500 | 707 | 1026 | 1472 | 1755 | 2031 | 2586 |
| p99 (ms) | 148 | 325 | 401 | 538 | 780 | 1058 | 1566 | 1972 | 2056 | 2755 |
| miss | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % | **16.7 %** | **100 %** |

**Capacity by SLO (the production-honest reading):**

| latency SLO (p99) | sustained capacity | note |
|---|---|---|
| **≤ 500 ms** (crisp turn-taking) | **~16–32** | 16 → 401 ms; 32 → 538 ms |
| **≤ 1 s** (good conversational) | **~64–128** | 64 → 780 ms; 128 → 1058 ms |
| **≤ 1.5 s** (acceptable) | **~256** | 256 → 1566 ms |
| ≤ 2 s (frame deadline; sluggish) | ~320 | 320 → 1972 ms; **not a production target** |

So the honest headline is **~128 concurrent distinct full-duplex streams at a sub-second (p99 ≈ 1 s)
SLO**, scaling to ~320 only if you accept a 2 s response. p99 grows **sub-linearly** with N (batching
amortizes the weight read) and is **flat over the whole session at any feasible N** (≈0 drift) because
the windowed path is *stateless per frame* (a fresh, fixed-length request each tick that finishes
within the tick) — which is exactly why it sustains over time **and** why it cannot remember context
older than 8 s (see correctness note). This is the **same windowed path as MiniCPM-o** (apples-to-apples
with the other vLLM-served model); the 30B reaches higher N than MiniCPM (48) because its budget is 2×,
its MoE activates only ~3 B params/token, and vLLM runs the FP8 MoE with fused GEMMs + CUDA graphs.

**Correctness — the responses are real and correct, not partial/artificial.** Probing the path with
real spoken questions (`experiments/fd_correctness_probe.py`): "capital of France?"→*"The capital of
France is Paris."*; "longest river in South America?"→*"the Amazon River"*; "highest peak in North
America?"→*"Denali, formerly Mount McKinley"* — all correct. **Under load (N=128 distinct, 75 s):
128/128 sessions answered their OWN question correctly** (100 % of steady-state ticks contain the
expected answer; 0 errored) — no audio starvation under concurrency. Two honest caveats: (a) the path
forces exactly `tpt`=25 tokens/frame with `ignore_eos`, so each tick **re-answers the windowed audio
and is truncated mid-sentence** (a load/throughput shape, not a flowing dialogue), and the very first
tick is wrong (answers before the discriminating word enters the window); (b) **8 s of context is
enough for these short single-turn questions but cannot support a real minute-level conversation** —
anything said >8 s ago is gone, so genuinely context-dependent / incremental responses would be wrong.

**What remains a genuine gap:** the *minute-level incremental resident-KV* path (the mode in which
Qwen2.5-Omni-7B was measured at 22) is still not available for the 30B on one GPU — vLLM has no
incremental mm-KV (it re-encodes the window), and the HF-eager incremental path is the 17 s/frame
backend below. So these numbers are the **8 s-windowed** capacity; a minute-level conversational
number would be lower (as it is for the 7B). The framework gap is real, but the 30B is emphatically
**not infeasible for real-time full-duplex serving** — it serves ~128 correct concurrent streams at a
sub-second SLO on one GPU.

### Why the HF-eager incremental backend was "16 s/frame" — it is the execution backend, NOT the serving infrastructure

Per-stage instrumentation (`STEP_DEBUG`) of one frame at N=1, context only 78 tokens:

| stage | time | note |
|---|---|---|
| audio encode (2 s block) | **102 ms** | fine |
| prefill (new block over cache) | **5 545 ms** | ~50 tokens over an 78-token cache — absurdly slow |
| decode (25 tokens) | **11 646 ms** | **≈466 ms / token** |
| **total** | **17 293 ms** | 8.6× the 2 s budget |

Decode dominates at **~466 ms/token** for a 30B-A3B that activates only 3 B params/token. The cause is
the **incremental backend running on HF-transformers eager**: the MoE block loops over **128 experts
in Python per layer (×48 layers) per token** (launch-latency-bound), and the FP8-Dynamic checkpoint is
**dequantized to bf16 every forward** (no native FP8 kernel in HF). **vLLM serves this exact FP8 30B at
4.8–14 ms/step** (the `vllm_fp8_30b.py` probe) — **30–100× faster per token** — because it has fused-MoE
grouped GEMMs, native FP8 tensor-cores, and CUDA graphs. So the gateway/gRPC/batching are not the
problem; the bind is that **vLLM has no incremental mm-KV** (re-encode only) while the only incremental
path is HF-eager. No single engine offers *both* fast MoE execution *and* incremental minute-level KV on
one GPU — a framework gap. (The `moe_fused.py` kernel fixes the expert loop but cannot stack the FP8
compressed-tensors expert weights, and bf16 30B OOMs at 94 GB — so it is not applicable to this
checkpoint on one GPU.)

**The core finding — minute-level memory costs sustained capacity:**
- **Bounded-state models scale and stay flat.** Moshi's Mimi streaming state is fixed-size, so
  per-frame cost is constant regardless of how long the call runs → 48 streams, dead-flat 71 ms,
  zero drift, with **real voice-in/voice-out**. MiniCPM-o via the 8 s re-encode window is likewise
  bounded → flat, ≥32 streams — but only *remembers* 8 s.
- **Incremental minute-level context grows per-frame cost.** Qwen2.5-Omni keeps a true minute-level
  resident KV, so attention cost **climbs as the conversation accumulates** (N=16: 339 ms→1125 ms
  over 120 s, plateauing under 2 s near the context cap; N=24 reaches the 2 s edge; N=32 climbs past
  the budget after ~70 s and collapses to 100 % miss). This climb-then-collapse is exactly the
  sustained-vs-burst distinction — a config that looks fine for 10 s is *useless* if it degrades by
  minute two. **True sustained continuous full-duplex capacity with minute-level context ≈ 16.**
- **The 30B serves ~128 correct concurrent streams at a sub-second SLO on the windowed vLLM path**
  (decode 4.8–14 ms/step; fused FP8 MoE + CUDA graphs) — distinct streams, p99 ≈ 1 s @ N=128, scaling
  to ~320 only at the sluggish 2 s frame deadline; see the UPDATE above. Same bounded 8 s-window path
  as MiniCPM-o. What it lacks on one GPU is the *minute-level incremental* path: vLLM has no
  incremental mm-KV (re-encode window only), and the HF-transformers incremental path runs the
  FP8-Dynamic checkpoint at **16 s/frame** (no native FP8 kernel) with bf16 OOMing (94 GB). So only the
  *minute-level* 30B full-duplex is gated — a framework gap, not a model limit; windowed full-duplex
  (8 s memory) is real-time at useful concurrency with correct responses.

**Voice-in/voice-out reality:** Moshi is the *only* true streaming voice-in→voice-out full-duplex
model here (Mimi decodes audio every 80 ms frame — measured, `voice_out_frames` = every frame). The
omni models do streaming voice-in→streaming-**text**-out; their speech synthesis is a heavier
turn-based talker stage (`generate(return_audio=True)`), not per-frame streamable in the current HF
implementation — so for spoken full-duplex output, Moshi is the model.

> ⚠️ The "Production e2e — AUDIO vs VISION" section immediately below is **TURN-BASED** (staggered
> arrivals, short responses, sessions idle between turns). Its high numbers (Qwen2.5 ≥512, etc.)
> measure client-arrival tolerance, **not** sustained continuous full-duplex, and are **superseded**
> by the table above for the full-duplex operating mode. It is retained only because it (a) verified
> the GPU genuinely batches the full N within budget (per-tick batch p50=210/max=256 at N=256, gpu
> 18 ms decode / 452 ms p99 prefill) and (b) verified correctness under load (spoken-QA accuracy
> 0.817 solo == 0.817 @conc-64) and the vision path end-to-end.

## Production e2e — max concurrency + TTFA, AUDIO-only vs AUDIO+VISION (2026-06-23, TURN-BASED — superseded by the sustained section above)

The most production-grade measurement in this repo: all four models served through the **hardened**
stack (production-grade adapters, vLLM worker with **startup warmup**, Go gateway with **vision
input** + real **audio output** + admission cap + stuck-response valve), driven by real WebSocket
clients through the OpenAI-Realtime API. Each session streams a real spoken question; vision sessions
additionally attach a 448 px image (so the **vision pipeline carries a large image-prefill on top of
the audio prefill** — different compute, measured separately). Arrivals are staggered (anti-burst)
and the engine is warmed before measuring. Capacity = largest N with deadline-miss ≤ 5 % and TTFA
p50 within SLO. Harness: `experiments/e2e_capacity.py` + `run_cap.sh`; raw JSON in
`results/e2e_capacity/`.

| model (frame budget) | pipeline | max concurrency (measured) | TTFA p50 @ cap | TTFA p99 @ cap | miss |
|---|---|---|---|---|---|
| **Qwen2.5-Omni-7B** (2 s) | audio | **≥512** (grid-capped) | 2146 ms | 5937 ms | 0 % |
| | audio+vision | **≥512** (grid-capped) | 2438 ms | 4000 ms | 0 % |
| **Qwen3-Omni-30B-A3B FP8** (2 s) | audio | **≥256** (grid-capped) | 1620 ms | 2604 ms | 0 % |
| | audio+vision | **≥256** (grid-capped) | 1916 ms | 2953 ms | 0 % |
| **MiniCPM-o-4.5** (1 s) | audio | **≥256** (grid-capped) | 1029 ms | 2013 ms | 0 % |
| | audio+vision | **≥256** (grid-capped) | 1255 ms | 1747 ms | 0 % |
| **Moshi** (80 ms, native codec) | audio (no vision modality) | **~24** continuous full-duplex | 72 ms (frame p99 71 ms) | — | 0 % |

Key findings:
- **All three omni models sustain their grid-capped ceiling for BOTH audio and audio+vision** at 0 %
  deadline miss — vision is a fully working end-to-end production path (client → Go gateway → gRPC →
  vLLM), not just the Python RealtimeServer.
- **Vision costs exactly what the extra prefill predicts**: at matched N the vision TTFA p50 sits
  consistently *above* audio (Qwen2.5 @512: 2438 vs 2146 ms; 30B @256: 1916 vs 1620 ms;
  MiniCPM @256: 1255 vs 1029 ms) — the image-prefill tokens, as expected, but it batches well so the
  gap is modest (~150–300 ms) and capacity is unchanged at these grids.
- **Qwen3-Omni-30B-A3B FP8 is genuinely high-capacity** once the engine is warm: ≥256 concurrent for
  both modalities at 2 s, p50 TTFA ~1.4–1.9 s. (The fused FP8 MoE decode is cheap — 4.8–14.4 ms/step,
  separate `vllm_fp8_30b.py` probe — and batched multimodal prefill scales.)
- **MiniCPM-o-4.5 runs natively in vLLM** (Qwen3 backbone, `MiniCPMO` arch) end-to-end — ≥256 both
  modalities at the tighter 1 s budget, sub-1.3 s TTFA.
- **Moshi** carries no vision modality; at the tight 80 ms native-codec budget it sustains ~24
  continuous full-duplex streams **with real Mimi audio output decoded every frame** (frame p99
  71 ms ≤ 80 ms). N≥32 hit the single-process 80 ms client's I/O ceiling (a client-sharding limit,
  not the model) — consistent with the 48 GPU-alone / ~16–24 e2e prior result.

**Methodology notes that make these numbers correct (learned the hard way):**
- **Engine warmup is mandatory.** The first cold multimodal prefill (flashinfer autotune +
  CUDA-graph capture) takes tens of seconds; without a startup warmup it blew the gateway's per-Step
  gRPC deadline and *hung sessions*, and without an in-harness large-batch warmup the first big grid
  point reported a false 30 s p99. Both are now warmed; the 30B's apparent "audio TTFA 10 s / vision
  all-errors" was purely cold-start and disappears when warm.
- **Arrival staggering** removes a thundering-herd artifact (a synchronized N-prefill burst serialises
  into a few ticks → unstable p99 reflecting arrival alignment, not capacity).
- Grids are **capped** at the listed N (true ceilings are higher); "≥" is honest, not a plateau.

## TL;DR — continuous full-duplex capacity (the models' real operating mode)

These are streaming full-duplex models: audio flows in continuously and output flows out
continuously, frame by frame — **not** discrete turns. So the capacity that matters is **how many
concurrent continuous full-duplex streams** the system sustains in real-time, where every frame
does `prefill(new audio chunk) + decode(output)` over a **resident** (prefix-cached) context —
no whole-utterance burst. Measured on real vLLM (`fullduplex_capacity.py`):

| model (frame budget) | **continuous full-duplex capacity (end-to-end, real audio)** |
|---|---|
| **MiniCPM-o** (1 s, bf16) | **128 streams** (frame p99 942 ms, 0% miss, TTFA 563 ms) |
| **Qwen-Omni** (2 s, FP8) | **128 streams** (frame p99 1562 ms ≤ 2000 ms; 192 misses) |
| **Moshi** (80 ms, native streaming codec) | **~16–24 e2e / 48 GPU-alone** |

These are measured **end-to-end through the production stack** (client → Go gateway `full_duplex`
mode → gRPC → worker → output). The deciding factor is **how the per-frame audio ingest is done**:
- **MiniCPM-o** — each frame re-encodes a windowed audio chunk (vLLM has no incremental mm-KV);
  the 1 s budget absorbs it → **128 streams, confirmed end-to-end** (matches the worker-level
  token-proxy number exactly).
- **Qwen-Omni** — Qwen2.5-Omni's audio encoder operates on **2-second temporal blocks**
  (`seconds_per_chunk=2.0`, block-wise streaming attention; arXiv:2503.20215), **not** 200 ms.
  At the correct **2 s** frame budget the per-frame re-encode fits comfortably: **128 streams**
  (frame p99 1562 ms ≤ 2000 ms; 192 misses). The previously-reported "infeasible @ 200 ms" was an
  artifact of a frame budget **10× too tight** — corrected here. (Earlier doc revisions also carried
  a token-proxy "32"; the real-audio 2 s number supersedes both.)
- **Moshi** — the *native streaming codec* (Mimi, incremental per 80 ms frame) has **no re-encode**,
  so it's the only model that does true continuous full-duplex cleanly. GPU alone sustains 48
  (`batched_moshi`); end-to-end the tight 80 ms budget + gateway/gRPC overhead hold the cadence to
  ~16–24 streams (16 → 99% of frames delivered, 32 → 74%).

**Net:** continuous full-duplex is fundamentally limited by **per-frame audio ingestion**. With a
generous frame budget (MiniCPM 1 s, Qwen 2 s) the re-encode is affordable (128 streams each); only
a **tight** budget makes it bite — Moshi's 80 ms, where a **native streaming codec** (incremental
per-frame, no re-encode) is the path that keeps it cheap. The gateway I/O (76.8k pkt/s) is never the
bottleneck for any of them.

**End-to-end = these numbers**, composed from two independently-measured real-silicon bottlenecks:
1. **GPU per-frame** (the binding one above) — real vLLM doing the actual per-frame prefill+decode.
2. **Gateway I/O** — the Go gateway sustains **76,800 packets/s / 1,536 sessions** at perfect
   cadence (§ below), far above any per-frame stream count, so it is never the bottleneck.

Why the GPU is the limit and not the network: decode is memory-bandwidth-bound at ~10 ms/step,
and a sustained per-frame prefill+decode over a batch crosses the frame budget at the counts
above. (Turn-based benchmarks reported higher numbers — e.g. "responsive ~256" — because short
EOS-terminated turns don't sustain per-frame work; those numbers are **superseded** because
turn-based violates how these models operate. See § Superseded.)

---

## The bottleneck progression (how we know it's the gateway, not the GPU or admission)

**Is it the GPU / decode?** No.
- Decode-roofline microbench (`decode_roofline.py`, real vLLM persistent requests, one
  `engine.step()` over a resident batch):

  | batch | step p50 | (→ 25-tok frame) |
  |---|---|---|
  | 1 | **9.85 ms** | 249 ms |
  | 105 | 14.4 ms | 368 ms |
  | 233 | 17.9 ms | 468 ms |
  | 425 | **34.2 ms** | 871 ms |

  batch-1 step = 9.85 ms = the memory-bandwidth floor (~15 GB weights ÷ ~1.8 TB/s). Flat while
  memory-bound (batch ≲ 100), rising as compute binds — textbook roofline; a 25-tok/1 s frame
  crosses budget at ~batch 500 (consistent across 3 runs). So decode supports a few hundred
  concurrent sessions. *(Microbench caveat: `reset_resident` doesn't fully evict aborts between
  sweep points, so `live` accumulates and the top grid point can OOM; read by `live`, not N.)*

**Is it admission / prefill compute?** No — this was an early misread (see Superseded).
- The per-tick engine trace shows prefill ticks cost ~440 ms for 48 arriving sessions (~9 ms/sess
  warm) and steady-state decode ticks are 15–40 ms. The frame-loop cadence under the turn-based
  benchmark was *stable* (gap = 1001 ms). So per-tick compute fits the budget with room to spare.
- Proven server-side (not client/network): the server-side TTFA (response.create-processed →
  first-token-emitted) **equals** the client-side TTFA at every N (e.g., 4691 = 4692 ms at N=256),
  and **sharding the client across processes did not help** (it hurt). So the latency is real and
  server-side — but it is *software*, not GPU.

**It's the gateway event-loop I/O.** Realistic WebRTC sends a 20–40 ms packet per session, so the
gateway absorbs ~(1000/chunk_ms)·N packets/s. The single Python `asyncio` loop:

| sessions @ 20 ms | packets/s | Python frame-loop gap (period 1 s) |
|---|---|---|
| 128 | 6,400 | ~1.3 s (mild slip) |
| 256 | 12,800 | ~2.0 s |
| 512 | 25,600 | **~6.1 s** |
| 1024 | 51,200 | **~12–14 s** |

Saturates at ~10k packets/s; the GPU stalls 6–14 s while the loop services I/O — yet GPU per-tick
work is <377 ms. The Go gateway (`gateway-go/`) under the same load:

| sessions @ 20 ms | packets/s | Go gateway gap |
|---|---|---|
| 512 | 25,600 | **1.000 s** ✓ |
| 1024 | 51,200 | **1.000 s** ✓ |
| 1536 | 76,800 | **1.000 s, 0 slip, tick work 0 ms** ✓ |

---

## Production Go-gateway ⇄ vLLM gRPC bridge

A real serving path (not a stub): **gRPC** contract (`proto/inference.proto`), **Python/vLLM gRPC
worker** (`worker/server.py`, owns the GPU, one batched Step per tick, serialized engine,
health/readiness, graceful shutdown), **Go gateway** (`gateway-go/main.go`, full Realtime WS
protocol + per-tick batched sampling + gRPC client with keepalive/deadlines, per-connection write
sync, signal-based shutdown). Toolchain pinned safely (`grpcio-tools==1.71.0` to match the vLLM
env's protobuf 5.29; grpcio 1.80 already present). `experiments/run_e2e.sh {smoke|quality|capacity|sharded}`.

- **End-to-end verified:** client → Go WS → gRPC → vLLM → tokens; **100% spoken-QA accuracy, 0 gRPC
  errors, 0 deadline misses.** The bridge is the production transport; the **continuous full-duplex
  capacity** above is what it serves.
- The bridge's *turn-based* benchmark numbers (responsive ~96 → ~256+, sharded 256 sessions 1483 ms
  vs Python 6959 ms) demonstrated that the Go gateway moves the bottleneck off the Python event
  loop onto the GPU worker — but those are **turn-based and superseded** (see § Superseded). The
  capacity to report is the continuous full-duplex number (MiniCPM 128 / Qwen 128 / Moshi 48).

### Continuous full-duplex per-frame curves (real vLLM, resident KV)

MiniCPM-o (1 s budget): p99 253 ms @1 · 384 @32 · 566 @64 · **831 @128** · 1142 @192 (✗).
Qwen-Omni FP8 (2 s budget): p99 308 ms @1 · 593 @32 · 896 @64 · 1305 @96 · **1562 @128** · 2302 @192 (✗).
Per-frame cost grows with batch (decode-roofline regime) and crosses the frame budget at the
capacity; beyond it, KV-cache pressure also breaks prefix-caching (re-prefill spikes).

### CONFIRMED end-to-end through the full continuous-gateway stack

Built the full continuous-gateway integration: the Go gateway runs a `full_duplex` mode (each
session streams audio continuously, the gateway samples the new audio per frame — **no turns** —
and ships it over gRPC), and the worker runs `fd_step` (windowed-audio prefill + decode per
frame). Real audio streamed continuously, client → Go gateway → gRPC → vLLM worker → output, all
measured from the `metronome.tick` events (`experiments/fd_load.py`, sharded):

| streams | frame p99 | deadline miss | TTFA p50 |
|---|---|---|---|
| 32 | 586 ms | 0% | 378 ms |
| 64 | 987 ms | 0% | 558 ms |
| **128** | **942 ms** | **0%** | **563 ms** |
| 192 | 1539 ms | 58% | 750 ms |
| 256 | 2575 ms | 77% | 947 ms |

**MiniCPM-o sustains 128 concurrent continuous full-duplex streams end-to-end** (frame p99 < 1 s,
0% miss, TTFA ~0.56 s), crossing at 192. This **exactly matches the worker-level 128**, confirming
the gateway is not the bottleneck and the composition (end-to-end = GPU per-frame) holds. The
real-audio path (`fd_step` re-encodes an 8 s window each frame — the honest vLLM cost, since it
has no incremental mm-KV) does not reduce the number: the windowed re-encode is amortized within
the batch.

### Explicit gateway overhead — decomposed (and where it is NOT)

Instrumented the Go gateway (`GW_DEBUG=1`) to log, every tick, the wall-clock of one frame minus
the worker's `fd_step` bracket (`gpu_ms`). Live during a MiniCPM continuous full-duplex run the
non-`gpu_ms` remainder is **~5.8 ms p50 / 15.2 ms p99 at N=128**, growing with batch. The first cut
attributed this to "gRPC serialization." **Direct measurement shows that is wrong** — decomposed:

**(a) Protobuf serialize+parse of the real `StepRequest`** (standalone, no network): **0.11 ms at
N=128 / 200 ms payload (801 KB); 0.73 ms even at the 4 MB / 1 s payload.** Bytes fields are memcpy,
not per-element parsing — serialization is *not* the cost.

**(b) Pure transport stack — 4-way ablation** (Go client ↔ Python **no-op** server, no GPU, isolates
wire + dispatch; `experiments/transport_bench/`, `gateway-go/cmd/transportbench`). Round-trip p50:

| transport | N=16 | N=64 | **N=128** (800 KB) | vs gRPC |
|---|---|---|---|---|
| **gRPC** (HTTP-2 + protobuf) | 0.19 ms | 0.39 ms | **0.64 ms** | 1× |
| **ZeroMQ** (raw framing) | 0.06 ms | 0.13 ms | **0.18 ms** | **3.6× faster** |
| **raw Unix-domain socket** | 0.04 ms | 0.12 ms | **0.13 ms** | **4.9× faster** |
| **shared memory** (`/dev/shm` mmap + UDS ctrl) | 0.03 ms | 0.06 ms | **0.10 ms** | **6.2× faster** |

The **entire gRPC transport stack is 0.64 ms at N=128**, not 11 ms. ZeroMQ / UDS / shared-memory are
a genuine **3.6–6× faster — but the absolute saving is ~0.5 ms/frame**, negligible against any frame
budget (even Moshi's 80 ms).

**(c) Where the ~10 ms actually is — worker-side Python glue, *outside* the `gpu_ms` bracket.**
`gpu_ms` times only `fd_step`; the servicer's per-session **audio ingest** (`np.frombuffer`→float32
→`concatenate` onto an 8 s window→slice, for each session) and per-session **detokenize** run
outside it. Measured standalone, the ingest loop alone is **3.1 ms p50 / 8.9 ms p99 at N=128 (200 ms
frame), 8.4 ms at 80 ms** — which, plus detok, *is* the gap. So:

> **Per-frame overhead at N=128 ≈ 0.1 ms (serialize) + 0.6 ms (gRPC transport) + ~3–8 ms (worker
> audio-window ingest) + detok.** The binding term is the worker's per-session preprocessing, **not
> the RPC.** A zero-copy transport removes ~0.5 ms; vectorizing/pre-ringing the ingest removes the
> several-ms term.

**Implication for the budgets** (the overhead matters only where the budget is tight):
- **MiniCPM 1 s / Qwen 2 s:** ~6–12 ms is ≈ 1 % → negligible → **e2e = worker GPU capacity**
  (MiniCPM e2e 128 = worker-level 128).
- **Moshi 80 ms:** ~6–12 ms is **10–15 %** of budget → eats the margin → caps e2e ~16–24 vs GPU 48.
  But the fix is the **ingest path**, not the transport (swapping in shared-memory buys back only
  ~0.5 ms of it).

**Honest negative result on transport:** for *co-located audio-scale* per-frame serving the data
plane is already sub-millisecond, so gRPC-vs-ZeroMQ-vs-shared-memory is **not** the lever — it would
only become one at much larger per-frame payloads (e.g. video-token frames, MB/session) or
fan-out (1000s of sessions), where the gRPC copy grows super-linearly. The clean 4-way table is kept
as the evidence for *why* we did not switch transports.

### Fix landed — the worker is now GPU-bound

Implemented the ingest-path fix in both workers (the thing the measurement pointed at):
- **vLLM worker** (`server.py`): an `AudioRing` (preallocated double-buffer, O(new-samples) push,
  zero-copy contiguous window view) replaces `np.concatenate([buf,new])[-W:]` (two O(window) copies
  per session per tick). Standalone: **10–13 ms → 0.6 ms at N=128 (17–37×)**, with **bit-identical
  windows** (500-frame random correctness test passes). In the real stack (`WK_DEBUG` worker-stage
  timing): **ingest ≈ 2–4 ms vs gpu ≈ 1400–1700 ms**, detok+build ≈ 1.3 ms → **CPU glue ≈ 0.3% of
  the frame; the worker is GPU-bound.**
- **Moshi worker** (`moshi_server.py`): assemble the `[maxb,1,frame]` batch on a **pinned host
  buffer + one non-blocking H2D copy/tick**, replacing a tiny `torch.from_numpy(..).to('cuda')` per
  active slot.
- Detok was measured cheap (0.75 ms @128, `batch_decode` gives no gain) and left as-is.

**What's left is GPU-side, not CPU.** `gpu_ms ≈ 1500 ms at N=128` is dominated by the **per-frame
audio-window re-encode** (vLLM has no incremental mm-KV, so the whole 8 s window is re-encoded every
tick). The path to "whatever the GPU can do" from here is (1) an **incremental/streaming encoder**
(encode only the new ~200 ms, the way Moshi's GPU-resident Mimi ring already does — no re-encode),
(2) **trim the window** to the model's essential W (512–1024 tokens, quality-neutral per the
KV-windowing study), and (3) **CPU/GPU pipelining** (assemble batch N+1 and detok N−1 on a side
thread while the GPU runs frame N — vLLM releases the GIL in the CUDA region — to hide the residual
few-ms CPU entirely). The transport/ingest CPU is no longer the bottleneck.

---

## The incremental real-audio path — built and validated (Qwen-Omni 2.5 + 3-MoE)

We then **implemented** lever (1) — the incremental/streaming encoder — as a production backend,
not just a recommendation. `metronome/backends/streaming_omni.py` (`OmniStreamingBackend`) holds a
**resident batched KV cache** and, per frame, encodes **only the new 2 s audio block** and prefills
those ~50 new tokens over the cache, then decodes `tpt` tokens. Per-frame cost is **O(block), not
O(window)**. Driven end-to-end by the same Go gateway via `worker/streaming_worker.py`.

**Why 2 s blocks are exact (not an approximation).** Qwen-Omni's audio encoder masks attention to
*within* each 2 s block (`cu_seqlens`), so a freshly-encoded block is independent of past/future
audio. Validated: incremental block-wise prefill **reproduces the one-shot whole-audio response
exactly** —
- Qwen2.5-Omni-7B: `"He hoped there would be stew for dinner. Turnips and carrots and bruised
  potatoes…"` (= LibriSpeech ground truth) from both paths.
- Qwen3-Omni-30B-A3B: same transcript from both paths.
mRoPE 3D positions degenerate to 1D sequential for audio+text, so positions are managed with a
running counter (no `get_rope_index`). (`experiments/qwen_incremental_proto.py`.)

**Per-frame cost vs context length — incremental is FLAT, re-encode grows linearly**
(`experiments/incremental_window_scaling.py`, B=16, tpt=1):

| context | Qwen2.5-7B re-encode | Qwen3-30B-MoE re-encode | incremental (either) |
|---|---|---|---|
| 8 s | 232 ms (2.6×) | 746 ms (0.9×) | **flat** (7B 91 ms / 30B 824 ms) |
| 32 s | 1638 ms (18×) | 1068 ms (1.3×) | flat |
| 64 s | 5080 ms (**56×**) | 1076 ms (1.3×) | flat |

The short-window re-encode is cheap *only because it discards older context*; incremental keeps the
whole conversation resident and still prefills just the new block.

**Capacity (2 s budget, listening/tpt=1; `experiments/streaming_capacity.py`):**
- **Qwen2.5-Omni-7B: 192 sessions** (incr p99 1293 ms), speedup over re-encode(8 s) growing
  3.6×@32 → 7.1×@128 → 8.3×@192 (re-encode is already 10.5 s/frame at B=192).
- **Qwen3-Omni-30B-A3B: 64 sessions** (incr p99 1449 ms). Roughly break-even vs re-encode here —
  the MoE's **HF-eager per-step routing overhead** dominates the flat cost (824 ms @B=16) and its
  sparse re-encode (~13 audio tok/s, 3 B active) grows slowly; fused-MoE kernels (vLLM) would cut
  the flat cost. Honest: the *algorithm* wins for the dense model; for the MoE it's
  implementation-bound.

**End-to-end through the production stack** (`worker/streaming_worker.py` ← Go gateway, full-duplex,
2 s period; Qwen2.5-Omni-7B, 8 streams): **0% deadline miss**, frame p99 429 ms, TTFA 646 ms, 0
errors; worker-side **ingest 0.17 ms** (the ring/batched-feature glue lesson), gpu ~315 ms — the
worker is GPU-bound, gateway negligible (consistent with the transport ablation).

**Honest scope / nuances.** (a) Incremental removes the *input-side* re-encode; when the model is
*talking* (high tpt) the per-frame cost is dominated by decoding the output tokens, identical in
both paths — so the win is largest in the listening-heavy duty cycle of real full-duplex. (b)
Sessions step in lockstep (one batched cache); mid-stream admission currently re-prefills the batch
(documented limitation — a per-session cache pool is the next step). (c) Moshi was already
incremental (native Mimi streaming); MiniCPM-o has a native streaming API
(`get_audio_embedding_streaming`/`streaming_prefill`, bs=1) — the same pattern, not yet wired here.

### Frontier push — continuous batching, fused MoE, admission (to the hardware limit)

Three further upgrades, each validated:

**(a) Continuous batching + mid-stream admission** (`OmniStreamingBackend`, `admission_test.py`).
Replaced the single lockstep cache with **per-session valid lengths**: a right-aligned, left-padded
batched KV cache + per-row attention mask + per-row RoPE positions, so sessions at *different*
conversation lengths share one batch. `admit()` splices a new session's prefilled prefix as a new
cache row **without touching existing rows** (validated: existing rows' KV is byte-identical through
an admission); `_drop()`/`_evict()` handle departures and context cap. This also made the batch more
efficient — B=128 per-frame dropped 717 → 453 ms.

**Frontier capacity (Qwen2.5-Omni-7B, 2 s budget, listening):** the incremental + continuous-batched
path sustains **448 concurrent continuous full-duplex sessions** on one RTX PRO 6000 Blackwell
(B=448 p99 1727 ms ≤ 2 s; B=512 misses at 2009 ms), at a steady **~3.4× per-frame speedup over
re-encode** (8 s window; far more at longer context). That is up from the ~64–96 the re-encode path
would sustain — a frontier number bounded by GPU compute, not the serving path.

**(b) Fused MoE for Qwen3-Omni** (`moe_fused.py`). The stock model loops over 128 experts in Python
(`index_add_`) — launch-latency-bound at streaming token counts. Replaced with batched GEMMs (dense
3-`bmm`, or `torch._grouped_mm` over only selected experts), **numerically validated == the
reference loop** (rel 0.17–0.25%). Honest caveat: the 30 B-A3B can't be fused on a *single* 95 GB
GPU in bf16 — accelerate's dispatch hooks pin the original expert weights (no headroom to
restructure), and transformers FP8 errors on this checkpoint. The kernel is delivered and verified;
the 30 B is **memory-bound**, unblocked by `device_map=None`/multi-GPU/a vLLM FP8-MoE backend.

**(c) MiniCPM-o-4.5 native streaming — environment block FIXED.** Per the latest model (4.5, not
2.6): it uses a Qwen3 backbone + the modern Cache API but its audio encoder still unpacks the
pre-4.57 WhisperAttention 3-tuple, so it needs transformers ~4.51. Resolved with a version-isolated
venv (the Moshi pattern, reproduced by `experiments/minicpm_venv_setup.sh`): a **matched cu128 torch
stack** (torch 2.10.0 / torchvision 0.25.0 / torchaudio 2.10.0, Blackwell) + transformers 4.51.0 +
the `minicpmo` package and its deps. **It runs:** `get_audio_embedding_streaming` (the apm encoder
KV cache) gives a **flat ~12.7 ms / 2 s-block** incremental encode. (Encoder-level speedup is modest
at ≤16 s — Whisper is parallel within its 30 s window — so the win is at LLM-prefill + >30 s context.)

**30 B-A3B FP8 — SERVED THROUGH vLLM AND MEASURED (2026-06-23).** No Qwen-official 8-bit exists;
the community FP8-Dynamic (`compressed-tensors`, `Qwen3OmniMoeForConditionalGeneration`) checkpoint
**fits (27 GB)**. Under HF-transformers it was a dead end — FP8-Dynamic *forward* is **slow
(5.4 s/frame, ~8× bf16) and degenerate** (`HeHeHe`, dequant-per-forward, no native FP8 tensor-core
kernel), and bf16 + `device_map=None` OOMs (thinker ~94 GB on one 95 GB GPU). That checkpoint is
built for **vLLM**, and vLLM 0.19 supports the arch natively (fused FP8 MoE + PagedAttention).
**Served it (`experiments/vllm_fp8_30b.py`) and it works:**
- **Loads in 49.7 s** on one RTX PRO 6000 Blackwell (vs HF OOM / degenerate).
- **Coherent** native-FP8 output: *"The capital of France is → Paris. … the largest city in the
  country…"* — the `HeHeHe` garbage is gone; the fused FP8 tensor-core path is correct.
- **Decode is cheap and batches on the MoE roofline** (forced 32-token decodes, CUDA graphs):

  | batch B | ms / decode step | tok/s |
  |--------:|-----------------:|------:|
  | 1   | 4.8  | 207 |
  | 8   | 6.2  | 1 283 |
  | 32  | 7.9  | 4 054 |
  | 64  | 9.7  | 6 568 |
  | 128 | 11.4 | 11 273 |
  | 256 | 14.4 | 17 781 |

  Even at B=256 a decode step is **14.4 ms** — trivially inside the 2 s Qwen-Omni frame; the A3B
  (3 B active / 30 B total) decode cost scales ~sub-linearly (4.8→14.4 ms for 256× the batch), exactly
  the memory-bandwidth-amortized regime the 7 B shows. **The earlier "30 B is memory-bound / fast path
  is vLLM, not measurable on one GPU" conclusion is now resolved: vLLM IS the fast path, and the 30 B
  FP8 decode is fast and high-throughput on a single GPU.** (HF-transformers single-GPU remains the
  dead end — that limit was framework, not hardware.) The validated fused-MoE kernel + incremental
  backend remain the win for dense 7 B (448 sessions); for the 30 B-A3B, vLLM's own fused FP8 MoE is.

---

## Other measured results (architecture-independent — not affected by the gateway)

**FP8 lever — Qwen-Omni (2 s frame).** At the correct 2 s budget a single stream (50 tok/2 s =
25 tok/s) fits even in bf16, so FP8 is not needed for *feasibility* — its value is **batch
capacity**: FP8 weights → ~2× decode throughput and half the KV/weight footprint → roughly **double
the concurrent streams** at the same frame budget, which is what gets Qwen to 128 (above) rather
than ~64. (The earlier "bf16 infeasible" claim was tied to the wrong 200 ms budget — 125 tok/s — and
no longer applies at 2 s.)
FP8 takes Qwen from unservable to high-capacity — exactly the roofline-predicted lever. **FP8
fails on MiniCPM-o** in vLLM 0.19 (`Half vs BFloat16` in the MM-encoder layer_norm at KV-cache
init) — not an available lever for that arch. Working levers: CUDA graphs, chunked prefill, prefix
caching, `max_num_batched_tokens`, `max_num_seqs`.

**Batched multi-session Moshi full-duplex** (`moshi_batched.py`, moshi venv, `streaming(B)`):

| B streams | frame latency | real-time (<80 ms) |
|---|---|---|
| 1 | 19.6 ms | ✓ |
| 32 | 50.2 ms | ✓ |
| 48 | 67.7 ms | ✓ |
| 64 | OOM | — |

**~48 concurrent real-time full-duplex Moshi streams**, memory-capped ~64. This is *sustained*
continuous full-duplex (every 80 ms frame decodes all streams), the honest hard capacity for true
full-duplex, and it validates per-tick batched ingestion on the streaming-codec model.

**Quality under load** (`quality_under_load.py`): 100 spoken-QA Qs, solo vs conc=128, inclusion
match — **0.790 = 0.790 (Δacc = 0)**. Aggregate quality preserved (C2 task-parity holds at the
serving layer). Caveat: 32/100 per-sample correctness flips (net-zero/unbiased = batched FP
non-determinism in the LLM + audio encoder; higher than offline K=12's ~1–8% because batch=128
diverges more). Not a bug (a bug would lower accuracy); just not bit-reproducible at batch 128.

**Statistical rigor.** TTFA points aggregate 32–512 samples with bootstrap 95% CIs; warmup
turns/ticks discarded; per-N CUDA-graph warmup (added after a non-monotonic cold-start artifact).

---

## Superseded interpretations (honest record of the wrong turns)

1. **`in_frac=0.0` head-to-head / cost-regrounding** (`vllm_headtohead.py`, `cost_reground.py`):
   "MiniCPM crosses at N=16", "MSCS 4", "synthetic 2–3× optimistic", "Qwen infeasible". These
   modeled input *prefill* tokens as sequential *decodes* — an artifact. **Superseded** by the
   end-to-end measurements: most tokens are prefill (parallel), decode amortizes across the batch.

2. **"The binding constraint is admission/prefill (~64–96)."** This was an **early misread**. The
   ~96 was not prefill compute — it was the **Python gateway's `asyncio` event-loop I/O** (proven
   by server-TTFA == client-TTFA, GPU tick <377 ms, the Python frame-loop saturating under packet
   I/O, and the Go gateway fixing it). The decode roofline and FP8 sections stand; the
   *attribution* of the ~96 limit to admission/prefill does not.

3. **Frame-synchronized batched staging** (move staging into the frame loop): clean A/B at equal
   arrival rate showed it is **timing-equivalent** to the old code (~96 either way) — `step_stream`
   already prefilled per-tick. A neutral refactor, not a capacity win.

4. **Admission spreading** (`max_admit_per_tick`): **counterproductive** — capping admissions
   inflates TTFA (N=256 burst 946 ms@∞ → 13.6 s@32) because the system was never prefill-throughput
   -bound. Useful only as a safety valve under true KV/compute saturation.

5. **Per-tick *incremental* audio feed** on the vLLM models: encoder-blocked — the growing-clip
   test (`audio_prefix_test.py`) showed vLLM re-encodes the whole clip (no sub-chunk KV reuse).
   Native only to streaming-codec models (Moshi).

6. **All turn-based capacity numbers** (responsive ~96 → ~256+, "MiniCPM serves 512 concurrent",
   the sharded 256-session 1483 ms result, etc.): **superseded** because turn-based serving
   (commit → whole-utterance prefill → short EOS-terminated response) violates how these
   full-duplex streaming models actually operate. They overstated capacity because short turns
   don't sustain per-frame prefill+decode. The numbers to cite are the **continuous full-duplex**
   capacities (MiniCPM 128 / Qwen 128 / Moshi 48), measured frame-by-frame in the real operating
   mode. The *architecture* findings from the turn-based runs (GPU not the bottleneck; Python
   event-loop I/O was; Go gateway fixes it) stand — only the capacity *magnitudes* are replaced.
