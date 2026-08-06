# Headline: Metronome windowed-KV **over** vLLM-realtime (measured through the gateway)

The right baseline for this work is **vLLM's own realtime/streaming API** (resumable requests /
`StreamingInput` / append-to-resident-KV). That API is excellent and now runs the omni models on this
Blackwell box (see `patches/vllm_0.23_omni_blackwell.patch`). The question this experiment answers:
**does the Metronome policy layer add measurable real-time capacity *on top of* vanilla vLLM-realtime?**

Both sides are the **same** vLLM-0.23 append-to-resident-KV worker (`worker/stream_server.py`), driven
through the **same** stack — same real clients (`sustained_fd.py`, distinct phase-staggered audio), same
Go gateway, same model (Qwen3-Omni-30B-A3B-FP8), same N, same 2 s frame budget, same 90 s sustained
sessions, same metrics. The **only** difference is one policy:

- **vanilla vLLM-realtime** (`--window-frames 0`): one resident resumable request per session, context
  grows **unbounded** (the API's default behavior).
- **Metronome windowed-KV** (`--window-frames 15` = 30 s): bound per-session resident context to a 30 s
  window; free the epoch's KV at each window boundary so per-session KV stays **bounded** (N×W frames,
  not N×duration). Two variants: a **hard reset** (drop context at the boundary) and a **sliding window**
  (`--window-overlap`): carry the most recent OV frames into the next window and **re-encode them once**
  so context is preserved across the slide. Output tokens accumulate across windows.

Verified real audio→text both sides (e.g. "The capital of France is Paris." on the llama-questions clip;
the sliding variant still answers correctly *after* a window slide — continuity preserved).

> **⚠️ Correction (rigor): the differentiator is DURATION, not short-burst concurrency.** An earlier 90 s
> capacity *sweep* (N=64,96,128,160 run sequentially on one worker, while an external GPU job was also
> running) reported vanilla "collapsing" to ~1601 ms at N=128/160. **Re-verification with FRESH single-N
> workers shows that was a contamination artifact:** fresh vanilla is **flat to N=160/120 s (p50 4–6 ms)**
> — vLLM-realtime handles high concurrency fine in short bursts. The **real** vanilla failure is
> **long-duration context growth** (fresh N=96/300 s genuinely drifts to the 1.6 s wall — Experiment A),
> which is exactly what windowed-KV fixes. The headline is therefore the **minute-level memory wall**
> (clean, fresh, single-N), not a burst-capacity multiple. Evidence: `results/artifact_check.txt`.

## Panel 1 — short-burst capacity (90 s) is NOT where the win is

Fresh single-N, 90–120 s, through the gateway (p50 = steady-state per-frame latency):

| N | vanilla vLLM-realtime (fresh) | in-engine SWA | note |
|---:|---|---|---|
| 128 | p50 **4 ms · stable** (120 s) | 3 ms · stable | both fine — no windowed advantage in a short burst |
| 160 | p50 **5 ms · stable** | 4 ms · stable | both fine |

At 90–120 s, vanilla and windowed are **equivalent** — the resident context (≤60 frames) is small enough
that unbounded attention is cheap. The windowed advantage appears only as the context grows over **minutes**
(Experiment A). (The earlier sweep's 1601/1602 ms at N=128/160 was the contamination artifact above, not a
real burst limit.) In-engine SWA still bounds per-frame **attention compute** via vLLM's `SlidingWindowSpec`
+ a windowed FlashAttention mask (FIX 5),
on the resident streaming request — no app-level recycling. (Honest scope: on this build vLLM keeps the
windowed *compute* but its hybrid KV manager does not drop blocks *outside* the window, so KV *memory* is
not also bounded here; compute-bounding alone delivers the latency/capacity win. KV-memory dropping needs
uniform-spec or an enabled hybrid manager — noted as the remaining engine item.)

> **Update (2026-07-02): the scope note above is superseded.** On the current build the sliding-window
> spec does free out-of-window blocks: the in-engine stat logger shows windowed KV-pool occupancy
> **plateauing at ≈0.26** at N=128 over 300 s while vanilla climbs monotonically to 1.0 and hard-stalls
> (`results/preempt_stats_win.log` vs `results/preempt_stats_van.log`, Figure `kvpool` in the paper).
> KV *memory* is bounded in-engine, as the paper states.

Raw: `results/inengine_swa_long.txt`, `results/sustained_fd/{ineng_cap,hl_vanilla,hl_windowed,hl_sliding}_n*.json`.

## Panel 2 — online admission control (discovers N\* from latency feedback)

The right admission test is an **open system** (sessions arrive over time, as in production) with an
**online controller** — not a hand-set cap on a synchronized burst. The gateway's `--online-admit` runs an
**AIMD controller** that discovers N\* from per-frame latency: shed (multiplicative decrease) when latency
exceeds `admit-target × budget`, probe higher (additive increase) with headroom. Open-system ramp
(`experiments/fd_ramp.py`), arrivals up to the offered load:

| offered (ramp) | target | **admitted (≈ online N\*)** | rejected | admitted steady p99 |
|---:|---|---|---|---|
| 200 @ 4/s | 1000 ms | **200** | 0 | 689 ms (fit under target → no shed) |
| 384 @ 8/s | 600 ms | **175** | **209** | **8 ms** |

At offer 384 the controller **discovers N\*≈175 online** (no oracle cap), admits them holding the deadline
(steady p99 8 ms), and cleanly rejects the 209 excess arrivals. The static-cap variant
(`hl_admit`, cap 96) is *not* cited as the headline because its no-admission baseline used the contaminated
sweep number; the online controller above is the clean result. **Derived N\*** offline from the capacity
probe (`experiments/derive_nstar.py`): vanilla 96, in-engine SWA ≥160, MiniCPM ≥96, 7B 16 — and note the
**open-system ramp sustains more (175) than the closed burst (96–128)**, which the online controller adapts
to automatically.

Raw: `results/online_admission.txt`, `results/sustained_fd/ramp_admit{,384}.json`.

## Reading

- **vanilla vLLM-realtime handles high concurrency fine in short bursts.** Fresh, single-N, it holds
  ~4–6 ms/frame to **N=160 over 90–120 s** — the async engine decouples decode from the frame tick and the
  resident context (≤60 frames) is still cheap to attend over. There is **no** windowed advantage in a
  short burst.
- **The failure is time, not concurrency.** Over **minute-level** sessions the unbounded resident context
  grows until per-frame attention drifts to the frame-budget wall: fresh **N=96 / 300 s drifts 3 ms →
  1601 ms** (Experiment A). This is the real, clean degradation.
- **Metronome windowed-KV removes the drift.** In-engine SWA bounds per-frame attention compute, so
  latency stays **flat ~1–2 ms for the full 5 minutes** (and the app-level proxy 14–36 ms). The win is
  **eliminating the age-dependent drift / minute-level memory wall**, from the KV-management *policy* — the
  serving primitive (append-to-resident-KV) is shared with vanilla.
- **Online admission** turns open-system overload into bounded goodput: the AIMD controller discovers
  N\*≈175 from latency feedback and sheds the rest, vs degrading everyone.

## Why this is the right framing

vLLM-realtime supplies the **mechanism** (append-to-resident-KV); it has **no** deadline-aware bounded-KV
policy — resident context grows to `max_model_len` and there is no per-session KV budget or windowed
freeing. That is precisely the Metronome contribution, and here it is measured as a **delta over vanilla
vLLM-realtime on identical hardware/clients/gateway**, not against a strawman. Admission control (shedding
beyond the schedulable N\* so admitted sessions keep their deadline) is the complementary policy; with
windowed-KV raising N\* to ≥160, admission caps the offered load at that point.

## Generality — all four models on the streaming path (through the gateway)

The streaming (append-to-resident-KV) worker is model-aware (`model_prompts()`) and serves all four
real-time models through the same gateway + clients. Per-model **clean streaming capacity** = largest N
whose steady-state per-frame latency stays under the frame budget (real audio, 60 s sustained):

**Fresh-per-point** (one worker load per N — no sweep contamination):

| model | budget | streaming clean N\* (fresh) | windowed-8 s `fd_step` | note |
|---|---|---|---|---|
| **Qwen3-Omni-30B-A3B-FP8** | 2 s | **≥160** (flat to N=160 @ 90 s) | 64–128 | MoE 3 B active; headline model |
| **MiniCPM-o-4.5** | 1 s | **~96** (p90 ≈ budget) | ~48 | dense ~8 B; real-time to N=96 |
| **Qwen2.5-Omni-7B** | 2 s | **~16–24** (saturates N=32) | ~7 | encoder-bound — confirmed real |
| **Moshi** | 80 ms | **≥32** (worker OOM @ batch 64) | 16 | native Mimi stack, real **voice-out** |

These are **fresh single-N** numbers (`run_fresh_sweep.sh` / `run_fresh_moshi.sh`), which **corrected two
sweep-contamination artifacts**: the 30B "collapse at N=128/160" (fresh: flat to N=160) and Moshi's "cliff
at N=24" (fresh: real-time to N=32). The 7B (~16–24, encoder-bound) and MiniCPM (~96) were **confirmed**
real. Verified correct audio→text on all three omni models (e.g. "The capital of France is Paris.");
MiniCPM-o runs in thinking mode (`<think>…`) but generates real-time. Moshi is a native streaming model
(its own `worker/moshi_server.py`), so the vLLM-realtime/windowed-KV comparison doesn't apply — included for
completeness as the spoken-full-duplex point. At the 90 s burst these are **encoder/throughput**-bound (7B
lowest); the windowed-KV win is a **long-duration** effect (Experiment A), not burst capacity. Raw:
`results/fresh_{q7b,mcpm,30b_van}_summary.txt`, `results/fresh_moshi_summary.txt`.

## Experiment A — long-duration memory wall (N=96, **300 s**)

The 90 s sweeps understate the problem. At N=96 (which looked clean at 90 s), a **5-minute** session
exposes vanilla's unbounded-KV wall directly. Per-frame latency by 10 s bucket:

Fresh single-N, 300 s, per-frame latency:

| N | vanilla (unbounded): 0–30 s → 270–300 s | **in-engine SWA**: 270–300 s |
|---|---|---|
| 96 | 2–5 ms → **1601 ms** (drift +1348, DEGRADING) | **1–2 ms · flat** |
| 128 | 2–5 ms → **1602 ms** (drift +1296, DEGRADING) | **1–2 ms · flat** |

(app-level windowed proxy at N=96: flat 14–36 ms — works, but pays a re-encode overhead the in-engine path avoids.)

Vanilla climbs monotonically to the ~1.6 s frame-budget wall as the resident context grows over the
session; **in-engine SWA holds the flattest** (~1–2 ms for the full 5 minutes, better than the app-level
proxy's 14–36 ms since it pays no re-encode). This is the clearest statement of the thesis:
unbounded append-to-resident-KV is **not** safe for minute-level sessions even at "safe" concurrency;
bounded-KV is. Raw: `results/long_duration_memory_wall.txt`, `results/long_{vanilla,windowed}.log`.

## Experiment B — correctness under load (N=96, 75 s)

Does the windowing policy trade answer quality for latency? N=96 sessions each stream a known spoken
question (llama-questions); we score answer-in-output (`experiments/fd_correctness_probe.py`):

| policy | answer stated ≥once (`sess_ever`) | per-frame ≥80% (strict) |
|---|---|---|
| vanilla (unbounded) | 66/96 | 62/96 |
| **windowed-KV** | **96/96** | 0/96 |

Both produce **correct audio understanding** under load. The first pass used the continuous `ignore_eos`
streaming prompt, which dilutes answers with filler tokens (a harness artifact), so we re-ran with a
**turn-based, EOS-terminated** prompt (`--turn-eos`: accumulate the question, emit one answer to EOS, no
filler) for a clean per-frame number:

| N=96, EOS-terminated | answer stated ≥once | per-frame correct | strict ≥80 % |
|---|---|---|---|
| vanilla (unbounded) | **96/96** | **~70 %** | 32/96 |
| **windowed-KV** | **96/96** | **~68 %** | 32/96 |

**Windowed-KV and vanilla are statistically identical** — bounding KV does **not** degrade correctness.
Answers are clean and correct on all three questions (e.g. windowed: *"Mount Denali, formerly known as
Mount McKinley, is the highest mountain peak in North America."*; *"The longest river in South America is
the Amazon River."*). The ~70 % (not 100 %) per-frame figure is **real model behavior** on the looped
2 s audio (the model occasionally mis-answers a partial clip, e.g. "Mississippi" for the Amazon question)
— identical for both policies, i.e. not a serving effect. **Conclusion:** Metronome's latency / capacity /
memory wins come at **no correctness cost**. (For reference, the confounded `ignore_eos` pass read 66/96
vs 96/96 sess_ever — the EOS re-run removes that artifact and is the number to cite.) Raw:
`results/correctness_eos.txt`, `results/sustained_fd/corr_eos_{vanilla,windowed}_n96_n96.json`.

## Experiment C — the bound's two halves: sink ablation in free-running decode (N=32, 300 s)

Metronome's bound is **window + pinned attention sinks** (first 32 tokens, 2 KV blocks/session,
StreamingLLM-style; FIX 6 in `patches/vllm_0.23_omni_blackwell.patch`: Triton unified-attention union
mask `[0,S) ∪ [t−W,t]` + KV-manager block pinning + admission-cap accounting). The long-horizon probe
(`experiments/fd_longhorizon_probe.py`, N=32, 300 s, rotating spoken questions + espeak probes; runner
`experiments/run_sink_exps.sh`) ablates each half:

| condition (fresh worker each)         | answering, by session age            | espeak Q (240 s) | recall |
|---|---|---|---|
| vanilla unbounded (`lh_swa0`)         | steady ~22–32 %                      | 26 % | 18 % |
| window only, FA (`lh_swa1024`)        | 12 % → decays to ~0–8 %              | 6 %  | 0 % |
| window only, sink kernel (`lh_tri0`)  | 40 % → decays to 0 % (kernel control)| 0 %  | 0 % |
| **window + 32 sinks (`lh_sink32`)**   | **33–69 %, age-independent**         | **21 %** | 29 %* |

\* the recall *score* is the lenient keyword scorer crediting coherent in-window answers (the model
names the most recent question as "the first"); true beyond-horizon recall is impossible under any
fixed bound. Engine side: pool plateau 6.5 % vs 6.4 % (no sinks) at N=32; latency p50 <1 ms, p99 3 ms,
0 errs — the sink half is memory- and latency-neutral. The zero-sink control on the identical kernel
reproduces the decay ⇒ the recovery is the sinks, not the backend change. Kernel verified against a
float32 union-mask reference with NaN-poisoned freed blocks (`tests/test_sink_retention.py`). Raw:
`results/sustained_fd/lh_{sink32,tri0}.json`, `results/sink_stats_lh_sink32.log`.

**Sweep + boundary controls (6 more fresh-worker points) — the operating region has edges.**
Token layout: header [0,14), first audio [14,42), instruction [42,53), assistant-open [53,58),
generated from 58.

| condition | answering by age | espeak Q | verdict |
|---|---|---|---|
| `lh_s16` W=1024 S=16 | 90 % → steady ~50 % | 45 % | **best; pin = the chat header** |
| `lh_s42ctl` S=42 (full 1st audio) | 72 % → ~25 % | 21 % | pinned audio stays semantically live |
| `lh_s58ctl` S=58 (+instr+asst) | 60 % → ~30 % | 17 % | quotes pinned clip as "the audio" all call |
| `lh_s64` S=64 (+6 generated toks) | 52 % → 7 % | 7 % | template-echo collapse |
| `lh_w512s32` W=512 S=32 | 32 % → 0 % | 0 % | window too small; sinks can't rescue it |
| `lh_w2048s32` W=2048 S=32 | 68 % → steady 40–57 % | 42 % | recovers like W=1024 |

MECHANISM (controls refute the truncated-block conjecture — S=32 truncates mid-audio and works):
**pinned content stays semantically live** — sessions answer the pinned first question minutes
later; pinning the model's own output tokens is catastrophic. Rule: **pin structure (the header),
not content; keep W ≳ 1024 (~40 s).** KV plateaus track block arithmetic exactly
(6.5/6.6/3.5 % for S=16 / S=64 / W=512+S=32); latency flat everywhere (p99 ≤ 3 ms).

## Reproduce

```bash
# baseline (vanilla vLLM-realtime, unbounded KV):
WINDOW=0  DUR=90 MAXSEQS=192 TAG=hl_vanilla  bash experiments/run_stream_gateway.sh "64 96 128 160"
# Metronome windowed-KV (30 s window):
WINDOW=15 DUR=90 MAXSEQS=192 TAG=hl_windowed bash experiments/run_stream_gateway.sh "64 96 128 160"
```
