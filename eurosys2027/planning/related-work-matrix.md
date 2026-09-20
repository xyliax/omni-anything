# Closest-Work Matrix

完成此表后再冻结 New Problem/Setting 与 Technique 的定位。每一行必须指向可核验的论文版本和日期。

| Work | Long-lived session | Growing KV | Predictable next use | Partial GPU residency | Restore prefetch | Real-time or periodic SLO | Difference from this paper |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LiveServe (arXiv 2606.22983, 2026-06-22; CUHK, Wuhan Univ.) | Yes: multi-turn voice sessions with playback state | Yes: multi-turn KV kept across turns | Estimated: next use ranked by remaining playback plus a per-session moving average of turn gap | Yes: suffix blocks evicted before prefix blocks; idle sessions ranked for eviction | Yes: asynchronous DRAM-to-HBM preload triggered by speech onset or barge-in, admitted only if the transfer can be hidden | Playback-buffer urgency classes over stage-aware buffers; no fixed period | Next use is predicted from observed turn gaps and triggered by an arrival event (speech onset); no committed release time, no release offsets; evaluated only on cascaded thinker-talker pipelines (Qwen3-Omni, Ming-Flash-Omni) over vLLM-Omni with Bernoulli barge-in |
| CachedAttention (USENIX ATC 2024) | Yes: multi-turn conversation sessions with KV kept across turns | Yes: session KV grows across turns | Estimated from the scheduler queue: waiting jobs reveal which sessions will run next, with lead time set by queue depth, not by the workload | No: eviction and restore are all-or-nothing per session | Yes: layer-wise DRAM-to-HBM preload overlapped with the previous job, plus SSD-to-DRAM staging by queue order | No: throughput-oriented, no per-turn deadline | Lead time is a by-product of queue depth that the system cannot plan; no partial residency, no committed next-use time, no phase control |
| Pensieve (EuroSys 2025) | Yes: multi-turn conversations | Yes: cached across turns in 32-token chunks | No: restore begins only once the next turn has arrived and entered the batch | Yes: chunk-level partial eviction ranked by rebuild cost over idle time, dropping leading chunks first | No: swap-in and recompute of dropped chunks start after batch formation | No | Restoration stays on the critical path of the arriving turn; eviction favours protecting the tail rather than the prefix; no next-use timing information is consumed |
| Metronome (arXiv 2607.02640, 2026-07-02) | Yes: continuous duplex sessions | Yes: identifies unbounded per-session KV as the failure cause | Implicit: recurring frame deadline, no per-session scheduling of next use | Bounded window: sink plus last W tokens, middle KV discarded, not offloaded | No | Yes: periodic real-time task framing, 80 ms to 1-2 s frame deadlines, deadline-aware AIMD admission | Discards context instead of preserving it; no host backing, restore or prefetch; patches model definitions per model rather than scheduling residency |
| VoxServe (arXiv 2602.00269, 2026-01-30; UW) | No: request-scoped generation | No: per-request caches scoped to one generation | No | No | No | Soft deadline per chunk from chunk duration plus accumulated lag; startup versus steady-state phases | Unified execution abstraction plus streaming scheduler for half-duplex speech LMs (7 TTS and speech-LM models, no duplex model); no session lifecycle, no idle state, no KV residency decisions |
| vLLM-Omni (arXiv 2602.02204, 2026-02-02; Huawei et al.) | Paper: no (offline batch prompts); repository: experimental full-duplex realtime runtime for MiniCPM-o 4.5 | Paper: no | No | No | No | No | Stage-graph substrate with per-stage engines and a unified inter-stage connector; the base system LiveServe and Pilarius both build on, not a residency policy |

## Search Buckets

- Interactive and streaming model serving.
- Full-duplex or continuous multimodal serving.
- KV cache allocation, prefix caching and long-context serving.
- GPU/CPU KV offload, tiering and prefetch.
- Periodic, deadline-aware and next-use-aware resource scheduling.
- GPU memory oversubscription and working-set management.

## Novelty Gate

- [ ] The single closest work is named.
- [ ] The difference is expressible in one sentence without marketing language.
- [ ] The comparison covers assumptions, mechanism and evidence, not only features.
- [ ] Any “first” claim has been checked against current literature immediately before submission.
