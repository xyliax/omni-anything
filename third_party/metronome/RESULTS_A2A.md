# Apple-to-Apple: Windowed vs Streaming Full-Duplex Serving (concurrency)

A controlled concurrency comparison of the two **deployable** full-duplex serving paths, run through the
**identical** stack so the only variable is the worker's compute path:

- **Same clients** — `experiments/sustained_fd.py`, N distinct **phase-staggered** real-audio streams
  (no two sessions present the same audio window; prefix-cache dedup can't inflate capacity).
- **Same gateway** — the Go `gateway-go/gateway` in `full_duplex` mode (per-tick batched Step).
- **Same worker / model / engine** — `worker/server.py` on vLLM 0.19, Qwen3-Omni-30B-A3B-FP8, 2 s frame
  budget, `max_num_seqs=128`, `max_model_len=8192`, one RTX PRO 6000 Blackwell.
- **Same sweep / metrics** — N = 1,4,8,16,32,64; 60 s sustained; p50/p90/p99, deadline-miss, and
  **frame-delivery cadence** (the reliable real-time check); bucketed by elapsed time for drift.

The two paths (one worker flag, `--streaming-sessions`):

| path | what it does each frame | memory horizon |
|---|---|---|
| **WINDOWED** (previous, `fd_step`) | re-encode an **8 s** audio window, fresh bounded request | 8 s |
| **STREAMING** (`fd_step_stream`) | **append** the new chunk to a growing resident context; reuse encoder output (mm-processor cache) + LLM KV (prefix cache) | unbounded (grows) |

## Result (60 s sessions)

| N | WINDOWED p50/p90/p99 · deliv | STREAMING p50/p90/p99 · deliv |
|---:|---|---|
| 1  | 147 / 147 / **156** ms · 100% RT | 143 / 146 / **149** ms · 100% RT |
| 4  | 254 / 273 / **280** ms · 100% RT | 231 / 253 / **258** ms · 97% RT |
| 8  | 310 / 338 / **375** ms · 100% RT | 290 / 319 / **337** ms · 100% RT |
| 16 | 383 / 425 / **439** ms · 100% RT | 397 / 433 / **441** ms · 100% RT |
| 32 | 539 / 571 / **578** ms · 99% RT  | 495 / 599 / **649** ms · 100% RT |
| 64 | 687 / 836 / **868** ms · 99/98% RT | 678 / 861 / **931** ms · 98% RT |

Raw: `results/sustained_fd/a2a_{win,str}_n{N}.json`; summary: `python3 experiments/a2a_summary.py`.

## Reading

- **Both paths stay real-time through N=64** at the 2 s budget; neither collapses in this range.
- **Crossover near N≈16.** STREAMING is slightly *faster* at low N (early on the resident context is < 8 s,
  so it does less work than re-encoding a full 8 s window), and slightly *slower* at N≥32 (the growing
  resident context's per-frame re-submission + re-prefill starts to cost more than a fixed 8 s window).
  At N=64 STREAMING's p99 is ~7% higher (931 vs 868 ms).
- **Why they're so close here:** 60 s sessions (≈30 resident chunks), and the mm-processor + prefix
  caches keep `fd_step_stream`'s re-submission cheap at this scale. The growing-context drift that
  separates them (measured earlier at 60→603 ms `add` over 80 s) needs **longer sessions** (minutes) and/or
  higher N to dominate — at which point WINDOWED's flat 8 s cost wins on latency but loses on *memory*.
- **The real win is neither of these.** Both re-encode/re-submit per frame because vLLM 0.19 has no
  incremental mm-KV. The **append-to-resident-KV** path (vLLM 0.23 resumable requests) gives **flat
  ~5 ms/frame** ingest at any context length (SYSTEM_EVAL §3.5) — strictly better than both — but is
  gated for **audio** on this box by a vLLM-0.23 omni mrope bug (`docs/vllm_omni_streaming_triage.md`).
  This A2A is the comparison of what is *deployable today*; the 0.23 true-append is the next step once the
  mrope fix lands.

**Bottom line:** at production concurrency (≤64 sessions, 60 s), windowed-8 s and resident-context
streaming are within ~10% of each other and both real-time; pick **windowed** for bounded, flat latency
and **streaming** for longer memory — until the vLLM-0.23 true-append (flat-cost, unbounded memory)
supersedes both.
