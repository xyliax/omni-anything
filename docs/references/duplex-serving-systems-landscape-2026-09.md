# Duplex and Real-Time Speech Serving Systems Landscape (2026-09)

Dated survey of systems papers that target serving or inference efficiency for full-duplex and real-time speech models, and of what workload data exists for them, checked against primary sources on 2026-09-02. External reference only: it does not define this project's workload, mechanisms, terminology or contributions, and every item must be re-verified against its source before entering the paper. Model and product specifications live in [the full-duplex model and product landscape](full-duplex-model-product-serving-landscape-2026-08.md); KV offload and restore mechanisms live in [the KV offload and restore landscape](kv-offload-restore-landscape-2026-08.md). This file covers the serving-system layer between them; what that layer leaves open is recorded separately in [the open-problems note](duplex-serving-open-problems-2026-09.md).

## Systems papers on duplex and real-time speech serving

Four papers land squarely in scope, three of them from 2026.
Their citation graph is nearly empty:
Metronome cites neither VoxServe nor LiveServe, and LiveServe does not mention Metronome.

### VoxServe

[VoxServe](https://arxiv.org/html/2602.00269v1)
(Kamahori, Lee, Jha, Kadekodi, Wang, Krishnamurthy, Kasikci; University of Washington; 30 Jan 2026, [abs](https://arxiv.org/abs/2602.00269))
is the most dangerous prior work, because it takes the exact framing of a unified abstraction plus derived optimizations.

It proposes a model-execution abstraction that decouples model architecture from system-level optimization.
Every model implements the stages preprocess, LLM forward, sampling, and postprocess,
plus an optional depth-forward for architectures with a depth-wise LLM over multiple codebooks.
All models meet a standardized three-tensor contract of token IDs, a feature tensor, and a boolean mask,
with mask semantics left model-defined.

Its streaming scheduler splits each request into a startup phase that is time-to-first-audio critical
and a steady-state phase that is viability critical.
Steady-state requests receive a soft deadline from chunk duration plus accumulated timestamp lag,
and those within one second of the deadline are prioritized,
on the argument that viability is binary so slack on safe streams can be spent on urgent ones.
An asynchronous pipeline runs the LLM and the detokenizer as separate GPU tasks with explicit per-request dependencies.
CUDA graphs cover LLM forward and postprocess with fixed chunk sizes to raise the graph hit rate.

The paper claims to be "the first to unify these optimizations across multiple SpeechLM families under a single abstraction."
Seven models are supported: Chatterbox TTS, CosyVoice 2.0, CSM 1B, GLM-4-Voice, Orpheus 3B, Step-Audio 2, and Zonos-v0.1.
Roughly 20,000 lines of Python are released at [github.com/vox-serve/vox-serve](https://github.com/vox-serve/vox-serve).

| VoxServe headline, single H100 | Value |
| --- | --- |
| Throughput at comparable TTFA | 10-20x over official stacks |
| CosyVoice at 500 ms p90 TTFA | 0.4 req/s baseline, 4.0 req/s VoxServe |
| Data parallel 4 | 16 req/s versus 4 req/s |
| Offline throughput mode | 10x real-time baseline, 53x VoxServe, 134x optimized scheduler |

Three limits matter for positioning against it.
It supports no duplex model, and Moshi appears only as an example of a depth-wise design,
with Mimi cited as an example of a stateful detokenizer that needs cache state.
It never uses the term full-duplex, and discusses no idle frames, silence, barge-in, or turn-taking.
Caches are per-request and scoped to a single generation, so KV growth across a long conversation is absent.

### Metronome

[Metronome](https://arxiv.org/html/2607.02640)
(Meng, independent researcher; Li, Pine AI; 2 Jul 2026, [abs](https://arxiv.org/abs/2607.02640v1), code at [github.com/19PINE-AI/metronome](https://github.com/19PINE-AI/metronome))
frames duplex serving as a periodic real-time task in the Liu and Layland sense,
with recurring per-frame deadlines of 80 ms for Moshi and one to two seconds for omni models.
It names two departures from chatbot serving: deadlines recur so the tail compounds over thousands of frames,
and per-session KV is pinned and grows monotonically with no idle gap in which to swap or recompute it.

Its finding is that failure is a memory cliff rather than compute drift.
Latency sits at a few milliseconds, then jumps in one step to a roughly 1.6 second wall
when the block pool saturates and the scheduler stalls every session.
The failure is metastable, since identical five-minute runs collapse or survive on fill-rate variance,
and silent, because stalled ticks return empty frames on time so deadline-miss counters read zero.

The fix is windowed KV anchored by attention sinks, retaining the last W tokens plus the first S.
This required extending vLLM's Triton unified-attention kernel to mask the union of two ranges,
because FlashAttention's window primitive cannot express a union.
Deadline-aware AIMD admission control sits in a Go gateway, lowering the cap multiplicatively
as per-frame latency approaches a target fraction of the budget and raising it additively to probe.
The sizing rule is to pin structure rather than content: S=16 is best, W=1024 is comparable to 2048, and W=512 is too small.

| Metronome result | Value |
| --- | --- |
| Five-minute runs that wall | 14/20 unbounded, 0/20 windowed |
| Collapse-time prediction, 30B | 145 s predicted, 148 s measured |
| Admission convergence | N* about 209, steady p99 12 ms |
| Free-running answer accuracy mid-call | 38-57% bounded, 23-27% unbounded |
| Windowed memory plateau | about 0.2% of pool per session at W=1024 |

Evaluated on Qwen3-Omni-30B-A3B in FP8 as the headline, MiniCPM-o 4.5, Qwen2.5-Omni-7B for capacity only,
and Moshi for capacity on its own native stack,
all on a single NVIDIA RTX PRO 6000 Blackwell with vLLM 0.23.
It is not a unified abstraction across model families, and it installs its window by patching model definitions,
but its discussion argues that a per-session state bound should become a first-class engine API
rather than an emergent property of a maximum sequence length that acts as a crash boundary.
Turn-taking and barge-in are explicitly out of scope, and the wall is demonstrated on two models.

### LiveServe

[LiveServe](https://arxiv.org/html/2606.22983)
(Zhi and Yin, equal contribution, with Guan, Zheng, and Cheng at CUHK; Yan at Wuhan University; 22 Jun 2026, cs.DC, ACM format)
adds an interaction plane over vLLM-Omni's data plane.
A lightweight runtime monitor converts client signals into a compact runtime view
that exposes playback progress, speech activity, and barge-in events to per-engine schedulers and KV managers.

It diagnoses two failures in stage-local FCFS serving.
Excessive generation: stages decode far ahead of client playback,
with one long-context example finishing generation in about 8.2 seconds against about 65.9 seconds of playback,
so a barge-in discards the entire unplayed lead.
Passive cache management: LRU evicts the KV of sessions that look cold while the user is merely listening,
then reloads it on the next-turn critical path.

Requests receive one of three urgency classes based on a stage-aware playback buffer against a safe threshold.
Playback urgency covers sessions already playing whose buffer is at risk, sorted by ascending buffer.
First-audio urgency covers sessions with no first packet yet, sorted by ready age.
The efficiency class covers well-buffered sessions, ordered by a utility that penalizes generating ahead of playback
and favors finishing large resident requests under memory pressure.
Rather than filling idle time with computation, the design deliberately throttles well-buffered sessions
to free decode capacity for first-audio work, and overlaps KV transfer with user speaking time.
KV eviction is next-use aware, ranking idle sessions by remaining playback plus a per-session moving average of turn gap,
and evicting suffix blocks before prefix blocks to preserve shared prefixes.
Speech onset or barge-in triggers asynchronous KV preloading from DRAM to HBM, admitted only if the transfer can be hidden.
About 6,000 lines of Python on vLLM-Omni 0.20.1, with every mechanism optional and falling back to stock behavior.

| LiveServe result, 8x H200 | Value |
| --- | --- |
| p90 audio time-to-first-packet | 1.55x average, 2.21x peak |
| Completed throughput | 1.15x average, 1.56x peak |
| Interactive traces, Qwen3-Omni peak | plus 56-78% |
| Wasted tokens | 44.06% down to 12.38% or less |
| Text TTFP with warm prefetch | 302.1 ms to 127.8 ms |
| Peak LLM-stage KV residency | about minus 26% |

Evaluated only on Qwen3-Omni and Ming-Flash-Omni 2.0, both cascaded thinker-talker pipelines served through vLLM-Omni's stage graph,
with barge-in simulated as a Bernoulli draw rather than taken from real user traces.
It does not claim a unified abstraction across duplex families.
It cites VoxServe as closest, differentiating on multi-stage pipelines, barge-in, and multi-turn KV,
and names Andes and TokenFlow as the conceptual ancestors of pausing well-buffered requests.

### vLLM-Omni

[vLLM-Omni: Fully Disaggregated Serving for Any-to-Any Multimodal Models](https://arxiv.org/html/2602.02204v1)
(Yin et al., Huawei AI Framework and Data Technology Lab with CUHK, Institute of Software CAS, and others; 2 Feb 2026)
is the incumbent substrate that the other work builds on or competes against.

A model becomes a stage graph whose nodes are components such as an autoregressive LLM, a diffusion transformer, or a CNN,
and whose edges are user-defined stage-transfer functions such as Thinker2Talker and Talker2Vocoder.
Each stage exposes a step-centric forward written in vLLM style,
plus a preprocess function invoked at every iteration, for example to re-concatenate Thinker hidden states each decode step.
A unified connector generalizing vLLM's KV connector carries inter-stage data over shared memory, Ray, or Mooncake.
Each stage runs on an independent engine with its own scheduler, KV manager, and runner,
so continuous batching, chunked prefill, and graph compilation apply per stage.
Resource placement is user-specified rather than automatic.

Reported gains include an RTF reduction of 90.7% on Qwen3-Omni and 61.4% on Qwen2.5-Omni against reference implementations,
BAGEL text-to-image from 23.12 s to 9.64 s, and MiMo-Audio RTF from 1.39 to 0.12 with compilation.
Evaluation is single-node on two 80 GB accelerators over the first 100 queries per dataset, latency only.

The paper covers no full-duplex operation, no streaming audio input, and no continuous sessions,
treating inputs as fixed prompts under offline batch inference.
The shipping project has moved past the paper:
the [repository](https://github.com/vllm-project/vllm-omni) advertises an experimental full-duplex realtime runtime for MiniCPM-o 4.5
aligned with the vLLM 0.26 release line,
and the [documentation](https://docs.vllm.ai/projects/vllm-omni/) lists full-duplex realtime serving
with streaming audio input and output as an experimental feature.
This matters for positioning: the abstraction question is partly settled in code even where the paper is silent.

### Adjacent and position work

[The Model in the Middle: Toward AI-Native Real-Time Communication](https://arxiv.org/abs/2607.25792)
(Liu, Li, Qiu; 28 Jul 2026, cs.NI) is a position paper that treats the model as a stateful computational middlebox
inside a human-centered feedback loop, and proposes network-aware inference scheduling,
execution-aware transport prioritization, and playback control that adapts to both network and model variability.
Its system, Conflux, is described as under construction with preliminary results.

Adjacent KV and latency work that a reviewer may raise:
[Waxing-and-Waning KV Cache for Long-Form Speech LLMs](https://arxiv.org/html/2608.22704v1),
which allows evicted audio KV positions to be recovered rather than permanently discarded;
[KV Cache Eviction in Efficient Large Audio Language Models](https://arxiv.org/abs/2604.06694);
[Continuum](https://arxiv.org/pdf/2511.02230), which applies a KV cache time-to-live to multi-turn agent scheduling;
and [a low-latency continuous speech synthesis model for interactive agents](https://arxiv.org/html/2608.13831v1)
that supports mid-utterance interruption without resetting the KV cache.

## Workload characterizations

Nothing published.
Every artifact found is a benchmark driven by synthetic or simulated users, not a measurement study of real traffic.

[FLEXI](https://arxiv.org/html/2509.22243v1)
(Ge, Chen, Xiao, Liu, Xiao, Xiang, Yu, Zhu; Northeastern University and NiuTrans; 26 Sep 2025)
states outright that real full-duplex conversational data is scarce,
and generates queries with Qwen-plus synthesized through CosyVoice2.
It reports model behavior rates rather than workload structure, for example a jump-in rate of 0.785 for Moshi
against 0.120 for Freeze-Omni, and turn-taking latency of 0.696 for Moshi, 1.147 for Freeze-Omni,
4.878 for VITA-1.5, and 1.736 for Gemini-2.5-flash-live.
No session durations, talk-versus-listen ratios, silence fractions, or interruption frequencies appear.
Serving, concurrency, and GPU cost are not discussed;
the only adjacent remark is that an external control module nearly doubles latency.

[τ-Voice](https://arxiv.org/abs/2603.13686)
(Ray, Dhandhania, Barres, Narasimhan; 14 Mar 2026) extends τ²-bench to full-duplex voice agents over 278 tasks
in real-world domains, and is the closest thing to a realistic workload.
Its users are a simulator explicitly decoupled from wall-clock time so it can run on a stronger model without real-time constraints.
Voice agents reach 31-51% pass@1 under clean conditions and 26-38% with noise and diverse accents, against 85% for GPT-5 in text.
It reports no conversation-structure statistics and no throughput or hardware figures.

The same holds for [FD-Bench](https://arxiv.org/pdf/2507.19040),
[Full-Duplex-Bench v3](https://arxiv.org/html/2604.04847),
[VAmoS Bench](https://arxiv.org/pdf/2607.27453),
[EVA-Bench](https://arxiv.org/abs/2605.13841),
[VoiceAgentBench](https://arxiv.org/html/2510.07978v1),
and [post-interruption recovery evaluation](https://arxiv.org/abs/2606.19595).

The systems papers invent their own workloads rather than measuring one.
LiveServe draws barge-in from a Bernoulli distribution at p in {0, 0.3, 0.7, 1.0} over ShareGPT plus interactive traces;
Metronome streams LibriSpeech and spoken questions over WebSocket at 20 ms granularity.
Industry material discusses [load testing](https://hamming.ai/blog/voice-agent-load-testing-guide)
and [scaling and observability](https://picovoice.ai/guide/voice-agents/scaling-reliability-observability/)
for voice agents without publishing traces, and
[Building Enterprise Realtime Voice Agents from Scratch](https://arxiv.org/abs/2603.05413)
reports one stack's latency rather than a population of sessions.

A characterization with real session lengths, talk and listen ratios, interruption rates, and concurrency is genuinely unclaimed.

## Coverage summary

Three of the four serving papers appeared between February and July 2026 and their citation graph is nearly empty: Metronome cites neither VoxServe nor LiveServe, and LiveServe does not mention Metronome. Each occupies a distinct layer: VoxServe a request-scoped execution abstraction and streaming soft-deadline scheduler for half-duplex speech LMs; LiveServe interaction-aware scheduling, barge-in handling, playback-aware throttling and next-use-ranked KV eviction with speech-onset prefetch over vLLM-Omni; Metronome the periodic real-time-task framing with bounded per-session KV; vLLM-Omni the stage-graph substrate. How each relates to Conveyor is recorded in the closest-work matrix under `eurosys2027/planning/`, not here.
