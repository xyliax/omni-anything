# Duplex Serving: Open Problems Beyond the Current Scope (2026-09)

Dated reading of the systems literature on serving full-duplex speech models, checked against primary sources on 2026-09-02. Future-direction notes only: the current project studies KV residency for periodic interaction sessions (see [`docs/problem.md`](../problem.md)), and nothing here is a claim, mechanism or contribution of that work. Model, hardware and topology coverage must be read from the project owners rather than treated as frozen scope. The facts about each cited system live in [the duplex serving systems landscape](duplex-serving-systems-landscape-2026-09.md); this file records what that landscape leaves open.

## Claims already occupied

A broader paper on serving across duplex model families would find three framings taken:

- A unified execution abstraction over speech language model families with scheduling and pipelining derived from it: VoxServe (arXiv 2602.00269, 2026-01). Its abstraction is request-scoped and half-duplex; no duplex model is in its supported set.
- Interaction-aware scheduling for real-time speech, including barge-in handling, playback-aware throttling, multi-turn KV residency, next-use-ranked eviction and speech-onset prefetch: LiveServe (arXiv 2606.22983, 2026-06). Evaluated only on cascaded thinker-talker pipelines over vLLM-Omni.
- Bounded per-session KV under recurring frame deadlines, framed as a periodic real-time task: Metronome (arXiv 2607.02640, 2026-07). Patches model definitions one model at a time.

vLLM-Omni's stage graph (arXiv 2602.02204) already ships an experimental duplex runtime, so any new abstraction must state why a stage graph is insufficient. The throttle-well-buffered-streams idea traces to Andes and TokenFlow via LiveServe's own related work.

## Gaps with no published system

**Idle-listening compute.** Freeze-Omni gates its input stream on voice-activity detection and spends no LLM compute while the user is silent; Moshi at 12.5 Hz and MiniCPM-o 4.5 at 1 Hz run a full forward pass every frame regardless of who is talking or whether anyone is. No paper exploits silence to reduce duplex serving cost. Searching for adaptive frame rate, skipping, gating and silence-conditioned inference in duplex models finds only generic LLM layer skipping (Learning to Skip, arXiv 2311.15436; What Layers When, arXiv 2510.13876) and streaming ASR or enhancement skipping (fast-skip regularization, arXiv 2104.02882; Skip-RNN, arXiv 2207.11108).

**Cross-family runtime.** No published system spans the divergent duplex families in one runtime: parallel multi-stream with inner monologue (Moshi, SALM-Duplex), block-interleaved single stream (BayLing-Duplex, OmniFlatten, SyncLLM), time-division windows over an omni model (MiniCPM-o 4.5), and VAD-gated state machines over a half-duplex LLM (Freeze-Omni, VITA-1.5, FlexDuo). VoxServe covers none of them, LiveServe covers only cascaded pipelines, Metronome covers one model at a time.

Terminology clarification (2026-09-15): this inventory mixes architectural and execution properties, so it is not a set of mutually exclusive request classes. In particular, [DuplexCascade](https://arxiv.org/abs/2603.09180) combines an ASR–LLM–TTS cascade with fixed micro-turn updates of the dialogue LLM. Cascaded architecture does not imply endpoint-triggered dialogue updates; front-end VAD or ASR cadence does not establish the cadence of the model owning the managed KV. The project classification and resource conditions are maintained in [Problem](../problem.md#interaction-sessions-and-their-timing).

**Duplex-specific speculative or multi-stream decoding.** VADUSA (arXiv 2410.21951) and Speech Speculative Decoding (arXiv 2505.15380) accelerate turn-based autoregressive TTS; nothing addresses multi-stream decoding under a recurring frame deadline.

**Workload characterization.** No measurement study of real voice-agent traffic exists. FLEXI (arXiv 2509.22243) states that real full-duplex conversational data is scarce and synthesizes users; τ-Voice (arXiv 2603.13686) decouples its user simulator from wall-clock time; FD-Bench, Full-Duplex-Bench v3, VAmoS Bench, EVA-Bench and VoiceAgentBench report model behavior, not session structure. The serving papers invent workloads (LiveServe: Bernoulli barge-in over ShareGPT; Metronome: LibriSpeech streamed at 20 ms granularity). Session lengths, talk-to-listen ratios, silence fractions, interruption rates and concurrency remain unpublished.

## Reading of the space

The space is crowded but not closed, and it became crowded very recently: three of the four serving papers appeared between February and July 2026, and their citation graph is nearly empty, which signals a field still forming rather than one converging on a shared baseline. A paper whose primary contribution is a cross-family abstraction reads as VoxServe extended to duplex models. The abstraction earns its place only by expressing optimizations none of the four incumbents can, with idle-listening compute the strongest candidate and a real workload study the strongest supporting contribution.

One paper shape fits a space this heterogeneous, and Brainstorm (OSDI 2023, dynamic neural networks) is the precedent: organize the contribution as a matrix of mechanisms against duplex model families, with one figure enumerating the families, one figure stating each family's failure under a serving optimization designed for request-driven inference, one table marking which mechanism applies to which family, and one table mapping datasets to families, all held together by a thin core abstraction. The shape needs a sufficient number of mechanisms that survive the periodic deadline; the design-space table in the current project's paper outline (recompute, CPU attention, compression, windowing) is the starting inventory, and the shortage of duplex-specific mechanisms is what currently blocks this shape.
