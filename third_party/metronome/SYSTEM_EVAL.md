# Interaction Serving System — End-to-End Architecture & Validated Evaluation

This is the authoritative, consolidated writeup of the **built interaction-serving system** and its
**end-to-end evaluation**, grounded only in *validated* measurements (real models, real audio, real
gateway, sustained multi-client load). It is the production reference; exploratory/blocked directions are
quarantined in "Limitations & future work."

---

## 1. The system (what runs end-to-end)

A real full-duplex interaction app = **N clients each streaming 20 ms audio chunks continuously for
minutes**, voice/text in, text (or voice) out, every frame, under a per-frame **wall-clock deadline**.
The system serves exactly that shape:

```
 real audio (20ms chunks, OpenAI-Realtime WS, continuous)
        │   N concurrent clients (sharded so client I/O is never the bottleneck)
        ▼
 Go gateway  (gateway-go/, full_duplex mode)
   • goroutine-per-connection + jitter buffer; isolated per-tick loop
   • absorbs I/O concurrency (holds 1.000 s cadence at 76.8k pkt/s / 1536 sessions)
   • per tick: gather the due batch → ONE gRPC Step → fan out tokens/audio
        │   gRPC (proto/inference.proto: batched Step)
        ▼
 GPU worker  (owns the GPU; one batched prefill+decode per tick)
   ├─ vLLM worker (worker/server.py) — the omni models
   │     fd_step: per frame, (re-)encode the recent audio window + decode tpt tokens,
   │     batched across all due sessions; CUDA graphs + chunked prefill + prefix caching.
   └─ Moshi worker (worker/moshi_server.py, moshi venv) — native Mimi codec,
         real voice-in → voice-out every 80 ms frame (the only true spoken full-duplex model).
        ▼
 outputs: response.text.delta / response.audio.delta + metronome.tick (per-frame latency, deadline)
```

**Models served (all on one RTX PRO 6000 Blackwell):**

| model | frame budget | path | output |
|---|---|---|---|
| Kyutai **Moshi** | 80 ms | native Mimi (worker/moshi_server.py) | **voice-in → voice-out** |
| **MiniCPM-o-4.5** | 1 s | vLLM `fd_step`, 8 s window | streaming text |
| **Qwen2.5-Omni-7B** | 2 s | vLLM `fd_step`, 8 s window | streaming text |
| **Qwen3-Omni-30B-A3B (FP8)** | 2 s | vLLM `fd_step`, 8 s window | streaming text |

---

## 2. End-to-end evaluation methodology (the validated approach)

Capacity is measured **only** through the real stack — never a synthetic kernel, never bare
`engine.step()`. Harness: `experiments/run_sustained_vllm.sh` + `experiments/sustained_fd.py` (omni),
`experiments/run_sustained_moshi.sh` (Moshi), `experiments/fd_correctness_probe.py` (correctness).

- **Real audio**, real LibriSpeech/llama-questions clips, 20 ms chunks, streamed continuously for 60–120 s.
- **Distinct phase-staggered streams** (`FD_PHASE_STAGGER`): every session presents a different audio
  window so prefix-cache dedup can't inflate capacity (this corrected an earlier optimistic "≥512").
- **Metrics:** per-frame **p50/p90/p99** latency, **frame-delivery / cadence completeness** (the reliable
  real-time check — `miss` against a worker's self-reported `gpu_ms` can hide cadence slip), and **answer
  correctness** under load; everything **bucketed by elapsed time** to expose drift.
- **Capacity = largest N** that holds the budget for the whole session: p99 ≤ budget, < 2 % deadline miss,
  ≥ 90 % frame delivery, stable (no collapse).

---

## 3. Validated results

### 3.1 Sustained capacity by latency SLO (distinct streams, 0 % miss + full delivery)

| model (budget) | p99 ≤ 500 ms | **p99 ≤ 1 s** | p99 ≤ 1.5 s | 2 s frame-deadline edge |
|---|---|---|---|---|
| **Moshi** (80 ms) | n/a | n/a | n/a | **16 @ its 80 ms budget** (53 ms flat, cliff to 202 ms at N=20) |
| **MiniCPM-o-4.5** (1 s) | 8 | **48** | (>1 s budget) | (>budget) |
| **Qwen3-Omni-30B FP8** (2 s) | 16 | **~64–128** (p99 780 ms@64, 1058 ms@128) | ~256 | **~320** (384 → 17 % miss; 512 collapses) |
| **Qwen2.5-Omni-7B** (2 s) | ~4 | **~7** | ~12 | **~16** (audio-encoder-bound) |

Raw per-N p50/p90/p99: `results/sustained_fd/all_models_distinct_curve.csv`.
**A 2 s frame is a deadline, not a good UX** — the production reading is the sub-second SLO columns.
Moshi's only meaningful SLO is its 80 ms budget (frame-delivery cadence), not 500 ms–2 s.

### 3.2 Correctness under load (verified, not assumed — `fd_correctness_probe.py`)

| model | under load | verdict |
|---|---|---|
| Qwen3-30B FP8 | **128/128 @ N=128** answer their own question | clean |
| MiniCPM-o-4.5 | **48/48 @ N=48** (assembled); per-frame lower only from Qwen3 thinking-mode | clean |
| Qwen2.5-7B (vLLM) | **8/8 @ N=8** (strict ≥80 % of ticks) | clean |
| Moshi | coherent @ N=16, voice every frame | clean (conversational) |

No load-induced degradation; outputs at concurrency match solo.

### 3.3 Analytical capacity model (`experiments/capacity_model.py`)

Per-frame wall time **T(N) = T_fixed + α·N** ⇒ capacity **N\*(B) = (B − T_fixed)/α**. Validated:
MiniCPM N\*=50 (meas ~48), 30B N\*=349 (~320), 7B N\*=18 (~16).

- **α ∝ *active* params** when LLM-bound: α/active-param ≈ **1.5** for vLLM (MiniCPM 1.66, 30B 1.48). This
  is why a **sparse MoE (3 B active) beats a dense 8 B** — MoE sparsity is a 2–3× capacity multiplier.
- **The audio encoder is a first-class cost:** the 7B is *encoder-bound* (smallest LLM, yet α=91 — its
  Whisper-style encoder re-encoding the window dominates), so it caps lowest despite being small.
- **Frame budget B enters linearly:** 2× budget ≈ 2× capacity.
- **Most efficient design** for full-duplex serving: sparse-MoE LLM (few active params) + light/streaming
  audio encoder + low audio-token rate + FP8 + the largest tolerable frame budget. Qwen3-Omni-30B-A3B-FP8
  hits most of these → highest capacity; Qwen2.5-Omni-7B fails on the encoder axis. (See the same pattern
  in Thinking Machines' TML-Interaction-Small: 276B-MoE/12B-active + encoder-free early fusion.)

### 3.5 True streaming sessions — append-to-resident-KV (NOW UNBLOCKED + demonstrated)

The 8 s re-encode window (§3.1) is high-capacity but only *remembers* 8 s. Minute-level memory needs an
**append-to-resident-KV** path: append only the new frame's chunk to a *resident* request and reuse prior
KV, instead of re-submitting a growing prompt every frame. That primitive ships in **vLLM 0.23**
(resumable requests / `StreamingInput` / `_add_streaming_input_request`), and after fixing the
Blackwell/omni init blockers (see §5 + `patches/vllm_0.23_omni_blackwell.patch`) it now **loads and runs
Qwen3-Omni-30B-A3B-FP8 on this box** (`experiments/run_v023_omni_smoke.sh` → `V023_SMOKE_OK`).

Measured per-frame **ingest cost vs growing context** (`experiments/v023_streaming_session.py`, one
resumable request, context grown to 7600 tokens over 38 frames):

| approach | frame 1 | steady-state | trend as context grows | per-frame |
|---|---|---|---|---|
| **streaming (resident-KV append)** | 125 ms (initial prefill) | **~5 ms** | **flat** (0.10×) | prefill of only the new chunk |
| re-submit growing prompt (fd_step_stream) | 17 ms | 28–31 ms | **rises 1.57×** | re-hash + marginal prefill each frame |

The streaming session's per-frame cost is **flat ~5 ms** regardless of resident-context length — it
prefills only the new chunk and reuses KV — while re-submitting the growing prompt climbs monotonically
(and, with **audio** multimodal re-hashing rather than text tokens, climbs far more steeply — the earlier
fd_step_stream diagnostic measured 60 → 603 ms `add` over 80 s). This **confirms append-to-resident-KV is
the correct primitive for minute-level full-duplex**, and that it is now usable for the omni models on
this hardware. Raw: `results/v023_streaming_38x200.log` (a shorter 24×128 run showed the same flat ~5 ms).

**Audio streaming append now verified too.** The same primitive works for real **audio** chunks (not just
text): appending 2 s audio chunks to one resident Qwen3-Omni request runs at **flat ~5 ms/frame** and
decodes coherently (`experiments/v023_audio_append_derisk.py`). This required fixing a Qwen3-Omni mrope
off-by-one (FIX 4 in `patches/vllm_0.23_omni_blackwell.patch`) that crashed any audio chunk ending without
trailing text — see §5. Wiring this resident-KV-audio worker behind the gateway for an N-session capacity
sweep is the next step (see the apple-to-apple of the *deployable* paths in
[`RESULTS_A2A.md`](RESULTS_A2A.md)).

### 3.4 Determinism (optional)
Batch-invariant kernels (`worker/server.py --batch-invariant`) make output bitwise-independent of batch
size: 0/16 token flips vs 3/16 default. A reproducibility feature (slightly slower), not a perf lever.

---

## 4. Reproduce

```bash
# omni capacity sweep (distinct streams, p50/p90/p99, cadence), 30B example:
MODEL=sammysun0711/Qwen3-Omni-30B-A3B-Instruct-FP8-Dynamic PERIOD_MS=2000 GPU_MEM=0.85 \
  DUR=90 TAG=cap30b MAXSEQS=400 bash experiments/run_sustained_vllm.sh "1 8 32 64 128 256 320 384"
# correctness under load:
python3 experiments/fd_correctness_probe.py --uri ws://127.0.0.1:8904 --n-sessions 128 --duration 75
# Moshi (voice-out):  DUR=60 bash experiments/run_sustained_moshi.sh "1 8 16 20 24"
# analytical model:   python3 experiments/capacity_model.py
```

---

## 5. Limitations & future work (honest scope)

- **Validated capacity path's memory horizon = the 8 s window.** The vLLM `fd_step` path (the numbers in
  §3.1) re-encodes a fixed 8 s audio window each frame: flat latency + high capacity, but it only
  *remembers* 8 s. Minute-level context needs the append-to-resident-KV path below.
- **Streaming sessions: UNBLOCKED on this box and demonstrated (§3.5).** The correct primitive (append
  only the new chunk to a resident request; reuse prior KV) exists in **vLLM 0.23/main** (resumable
  requests, `StreamingInput`, `/v1/realtime`). It was previously blocked because vLLM 0.23 (torch
  2.11+cu130) failed to initialize the omni models on this Blackwell box (`cu_seqlens_q must be on CUDA`
  in `MMEncoderAttention`). That is now **fixed and verified** — three fixes (the vLLM cu_seqlens bug + a
  flashinfer capability gate + a flashinfer-cccl/CUDA-13.2 JIT bypass) in
  [`patches/vllm_0.23_omni_blackwell.patch`](patches/vllm_0.23_omni_blackwell.patch); Qwen3-Omni-30B-A3B-FP8
  now loads/generates (`run_v023_omni_smoke.sh`) and the streaming session shows **flat ~5 ms/frame**
  ingest (§3.5). Full root-cause + resolution: [`docs/vllm_omni_streaming_triage.md`](docs/vllm_omni_streaming_triage.md).
  **Remaining work to fold it into the *validated* capacity table:** a multi-session streaming sweep with
  windowed KV *freeing* (bound total KV across N sessions while keeping the resident request warm) and an
  audio-chunk (not text-token) ingest path — i.e. promote §3.5 from a single-session mechanism proof to a
  full N-session capacity-by-SLO measurement. The 8 s-window numbers in §3.1 remain the authoritative
  validated capacity until that sweep is run.
- The exploratory streaming code (`worker/server.py --streaming-sessions`, `--sliding-window-tokens`,
  `metronome/patches/`, `metronome_vllm_plugin`) is retained but **experimental** — not part of the
  validated serving path above.
