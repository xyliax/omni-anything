# Related Work — Annotated Survey

Scope: serving/inference systems and the scheduling/KV/real-time theory they rest on, plus
the interaction models themselves. Organized into seven axes. The claim of the survey is
that **every existing system occupies at most two of the four properties that define the
interaction-model serving regime** — `{persistent periodic deadline, growing-then-bounded
KV as a first-class concern, multi-tenant batched, capacity-as-the-metric}` — and the
intersection of all four is empty. arXiv IDs are given where known; items marked
`[verify]` need their identifier/venue confirmed before submission.

---

## Axis 1 — Throughput-oriented LLM serving

The substrate everything builds on; optimizes aggregate throughput for bursty,
request-scoped traffic.

- **Orca** (OSDI'22) — iteration-level / continuous batching. Requests join and leave a
  running batch each step. Foundational, but request-scoped and throughput-oriented.
- **vLLM / PagedAttention** (SOSP'23, arXiv:2309.06180) — paged KV, near-zero
  fragmentation, prefix sharing, CPU swap on preemption. The swap path is the one our
  §1.3 argument rules out for active sessions.
- **SGLang / RadixAttention** — radix-tree prefix cache for shared prompts; our chosen
  substrate. Its persistent-sequence feature (upstreamed by Thinking Machines) is the
  primitive we extend into a periodic-session object.

*Gap:* request as the unit; no deadline; no persistent session; KV freed at request end.

## Axis 2 — SLO- / deadline-aware serving

Adds latency targets, but as **per-request static deadlines** in a still-bursty,
throughput-shaped setting.

- **Sarathi-Serve** (OSDI'24, arXiv:2403.02310) — chunked prefill interleaved with decode
  to bound inter-token latency. Conceptually adjacent (each tick ≈ a prefill chunk), but
  chunk size is a scheduler choice for throughput/latency trade-off, not a wall-clock
  arrival we cannot delay.
- **SLAI / optimal-scheduling line** (arXiv:2508.01002) — tracks per-decode-iteration TBT
  deadlines, delays batch inclusion until necessary. Per-request deadlines, not periodic
  sessions; our B2 baseline adapts this.
- **StreamWise** (arXiv:2603.05800) — deadline-aware serving of **finite** multi-modal
  generation (e.g. a 10-min podcast video); DAG critical-path deadline propagation,
  heterogeneous hardware, cost-latency trade-off. *Verified not to cover:* persistent
  sessions, per-tick recurring deadlines, unbounded/growing KV, fast/slow; it even reports
  batching as harmful in its setting. Closest on "deadline-aware multimodal," furthest on
  workload.
- **TetriServe** (arXiv:2510.01565) — deadline-aware round-based DiT (diffusion) serving,
  step-level parallelism. Image generation, not autoregressive streaming.
- **TokenFlow** (arXiv:2510.02758) — responsive text **output** streaming under burst via
  preemptive scheduling. Output smoothing in a bursty model, not periodic sessions.
- **Aladdin** (arXiv:2405.06856), **PolyServe** (arXiv:2507.17769), **Nexus**
  (arXiv:2507.06608), **HyGen** (arXiv:2501.14808), **ConServe** (arXiv:2410.01228) —
  SLO-aware placement/scaling, multi-SLO serving, intra-GPU prefill/decode disaggregation,
  online/offline co-location. All per-request SLOs; none model recurring per-tick deadlines.

*Gap:* deadlines are per-request and static; no periodic task model; no growing-WCET.

## Axis 3 — Incremental-context / streaming-input serving

"Streaming" here means feeding context in before a **single** answer — not decode-every-
tick.

- **Stream2LLM** (arXiv:2604.16395) — overlaps context/RAG retrieval with prefill to cut
  TTFT; append-mode (monotonic prefix) vs update-mode (LCP invalidation), cost-aware
  preemption. A one-shot request whose context streams in; no recurring deadline, no
  per-tick decode loop, no eviction.
- **ElasticMM** (arXiv:2507.10069) — elastic multimodal parallelism for MM-LLM serving;
  throughput/parallelism, not real-time session scheduling.

*Gap:* one-shot answer; no persistent decode cadence; no deadline.

## Axis 4 — KV-cache compression / eviction

The right *family* for bounding KV, but designed for memory/quality on offline text
benchmarks, never tied to a per-tick deadline or online tick-by-tick operation.

- **StreamingLLM** (arXiv:2309.17453) — attention sinks + sliding window for infinite
  streams; cheap, hardware-friendly; discards the middle. The closest match to a literally
  infinite stream and a strong default eviction policy in our KV manager; long-range recall
  must come from elsewhere.
- **H2O** (arXiv:2306.14048) — heavy-hitter eviction via accumulated attention scores.
  Assumes a scoring view; we adapt it to **online, deadline-bounded, modality/time-aware**
  operation.
- **SnapKV** (arXiv:2404.14469) — prefill-time importance via an observation window over a
  long prompt. Prompt-oriented; not a streaming-tick regime.
- **ShadowKV** (arXiv:2410.21465) — keeps low-rank KV "in the shadows" for high-throughput
  long-context; offload + on-the-fly reconstruction. Bridges to Axis 5.
- KV-compression surveys / recent eviction (e.g. CAOTE arXiv:2504.14051) — taxonomy of
  eviction, quantization, low-rank.

*Gap:* memory/quality goal, offline eval; never a latency/schedulability lever under a
recurring deadline.

## Axis 5 — Long-context KV-offload / sparse-attention serving

Handles huge KV with sparse access and host offload — but for **one-shot long-context
inference**, not real-time streaming with deadlines. This is the axis that matters for the
*large-model projection* (§1.4).

- **InfiniGen** (OSDI'24) `[verify id]` — speculative prefetch of important KV from host;
  offload cold KV. One-shot long-context decode.
- **Quest** (arXiv:2406.10774) — query-aware sparsity; estimate page importance, attend to
  top pages. Reduces per-step attention cost — directly relevant to our hot-set selection,
  but for a single long generation, not multi-tenant periodic sessions.
- **ShadowKV** (above) — offload + reconstruction for long-context throughput.

*Gap:* one-shot; no per-tick deadline; single-tenant; no admission control.

## Axis 6 — Full-duplex / streaming dialogue *models*

Architecture/modeling papers. They define the workload Metronome serves; none is a
multi-tenant serving system, and none documents KV-cache/serving (confirmed for Moshi,
MiniCPM-o, Qwen-Omni).

- **Kyutai Moshi** (arXiv:2410.00037) — 7B temporal transformer (32 L, **MHA**, d=4096) +
  small depth transformer over Mimi codec (12.5 Hz / 80 ms, 8 codebooks); 2 audio streams +
  text inner monologue; **4096-frame ≈ 5.46 min context, no windowing**; ~160–200 ms
  latency. Our tightest-deadline, fat-KV, no-self-bounding anchor.
- **MiniCPM-o 4.5** (arXiv:2604.27393) — ~9B, Qwen3-8B backbone (GQA); audio 10 tok/s,
  video 64 tok/frame, speech out ~25 tok/s; 1 Hz speak/no-speak (Omni-Flow, TDM). Our 1 s,
  thin-KV, video-driven anchor; context cap undocumented.
- **Qwen2.5-Omni** (arXiv:2503.20215) / **Qwen3-Omni** — Thinker-Talker, block-wise
  streaming encoders, sliding-window DiT; 7B / 30B-A3B MoE; streaming (barge-in
  unconfirmed). Our self-windowing + MoE anchor.
- **TML-Interaction-Small** (Thinking Machines, blog, closed) — 276B/12B MoE, 200 ms
  micro-turns, interaction + background dual model, 0.40 s latency; serving hints only
  (Split-KV 4096-token blocks, NVLS, gather+gemv MoE kernels, batch-invariant kernels,
  persistent-sequence in SGLang). Architecture undisclosed → motivation only.
- **Voxtral Realtime** (arXiv:2602.11298), **Full-Duplex-Bench-v2** (arXiv:2510.07838),
  LWS / neural-FSM duplex — additional duplex models and a *dialogue-quality* benchmark
  (not a serving-capacity benchmark, which is our gap).

*Gap:* model/architecture only; single-stream demos; no serving-capacity treatment.

## Axis 7 — Classical real-time scheduling

The theory we import — and adapt.

- **Rate-monotonic / EDF scheduling, schedulability analysis, admission control,
  mixed-criticality** (Liu & Layland and the RTSS/RTAS lineage). Periodic tasks with
  deadlines map cleanly onto ticks — but the classical theory assumes **fixed WCET**, which
  interaction sessions violate (§1.5: WCET is a saturating ramp ∝ KV length). Our admission
  test is the adaptation to bounded-but-non-stationary WCET.

*Gap:* not applied to LLM/interaction serving; fixed-WCET assumption broken by growing KV.

---

## Positioning table

| System / line | Persistent periodic deadline | Growing-then-bounded KV (1st-class) | Multi-tenant batched | Capacity-as-metric |
|---|---|---|---|---|
| Orca / vLLM / SGLang | ✗ | ✗ | ✓ | ✗ |
| Sarathi / SLAI / Aladdin | ✗ (per-req) | ✗ | ✓ | partial |
| StreamWise / TetriServe | ✗ | ✗ | ✗ | partial |
| Stream2LLM / ElasticMM | ✗ | ✗ (append only) | ✓ | ✗ |
| StreamingLLM / H2O / SnapKV | ✗ | ✓ (memory only) | ✗ | ✗ |
| ShadowKV / Quest / InfiniGen | ✗ | ✓ (one-shot) | ✗ | ✗ |
| Duplex model papers | ✓ (single stream) | ✗ | ✗ | ✗ |
| Classical RT (RMS/EDF) | ✓ (fixed WCET) | ✗ | n/a | ✓ (utilization) |
| **Metronome (ours)** | **✓** | **✓** | **✓** | **✓** |

---

## How Metronome differs, in one line per closest competitor

- **vs StreamWise:** they serve finite artifacts with per-request DAG deadlines; we serve
  indefinite periodic sessions with recurring per-tick deadlines and growing KV.
- **vs Stream2LLM:** they stream *input context* before one answer; we decode every tick
  forever and manage the KV that accumulates.
- **vs SLAI/Sarathi:** they bound per-request token latency; we bound *per-tick* latency
  across a mixed-age population of periodic tasks via KV-budget admission.
- **vs StreamingLLM/H2O/Quest/ShadowKV:** they reduce KV for memory/throughput offline or
  one-shot; we use KV budget as the *real-time schedulability and \$ knob* under a deadline,
  multi-tenant.
- **vs classical RT:** we extend fixed-WCET schedulability to the saturating-ramp WCET that
  KV growth induces.
