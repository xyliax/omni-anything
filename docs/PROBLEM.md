# Problem definition

The project asks how one GPU can serve many long-lived duplex voice sessions while also accepting
asynchronous agent-result injection. The current real stack is vLLM 0.23, Qwen2.5-Omni-7B,
Metronome's resumable streaming protocol, and one RTX 3090.

Current measured conclusions are in [`FINDINGS.md`](FINDINGS.md). This document defines the problem
and the boundary of the proposed solution; it does not duplicate the run ledger.

## Workload

Three properties must hold together:

| Property | Meaning | Why it matters |
| --- | --- | --- |
| Periodic foreground | Every active session receives a hard audio tick | Work has predictable release times and deadlines |
| Growing state | Each tick appends KV and every future tick attends to prior context | Resident memory grows for the life of a session |
| Elastic injection | Tool/agent results may add hundreds or thousands of tokens | Background work competes with hard foreground work |

Concurrent session count is the target variable. Admission control can reject overload, but it
cannot recover capacity wasted by an unnecessarily resident working set.

## Observed baseline failure

E1 runs eight 2-second sessions for 600 seconds with parallel host ingest. vLLM allocates a
73,728-token (`3.94 GiB`) KV pool. The first scheduler lane disappears at about 216 seconds as the
pool fills, followed by a capacity cascade while substantial wall-clock compute time remains.

The failure is silent at the client cadence layer: the worker's 1.6-second wait cap lets the client
report 100% frame delivery and 0% cadence misses after useful engine progress has already stopped
for some sessions. Correct diagnosis requires scheduler, request, KV, and GPU evidence together.

This establishes the opportunity but not the size of a solution: HBM capacity is scarce, and some
H2D bandwidth and wall-clock time are idle.

## Candidate: scheduled tail-KV conveyor

The candidate keeps a canonical tail of each session's KV in host DRAM. Before a scheduled compute
slot, the tail is copied into a bounded HBM staging area; after use, staging is released. Periodic
release times make prefetch deadlines predictable, and phase assignment can control how many tails
overlap.

The mechanism has four non-negotiable constraints:

1. A tail cannot move before the preceding tick finishes and freezes its content.
2. H2D jobs sharing one link must all meet their compute slots.
3. Phase splitting must remain compute-schedulable; smaller batches reread model weights more often.
4. Prefetching earlier creates deadline slack but increases simultaneous HBM staging.

The simple `M + P` bandwidth formula ignores constraints 3 and 4 and is only an upper bound.

## What E2/E3 changed

E0 confirms approximately 12.3 GB/s pinned H2D bandwidth with limited decode interference. E2/E3
then combine fresh transfers of the real Qwen2.5-Omni tail size with compute service times extracted
from the successful E1 scheduler trace.

The retained model/framework cannot rotate eight sessions one at a time: the measured batch-1
service demand is over 5 seconds per 2-second period. Compute-aware groups 6 or 7 are feasible, but
only reduce peak staging from eight tails to seven. The validated mechanism-level capacity wall
moves from 236 to 248 seconds, approximately `+5.1%`, not the old `2x` forecast.

Lead time is also narrow: 10-25 ms meets measured transfer deadlines while retaining seven-tail
staging; 50 ms or more stages all eight tails and erases the capacity gain. Random phase assignment
overloads compute and is not a valid control policy.

## Evidence boundary

E2/E3 are trace-driven CUDA mechanism experiments. They validate real byte movement, link timing,
content-release constraints, compute scheduling, staging accounting, and a modeled capacity wall.
They do not change vLLM's active block table and therefore do not prove:

- end-to-end active KV migration;
- D2H writeback integration for newly appended tokens;
- attention-output equivalence after repeated migration;
- production interaction with cancellation, injection, prefix caching, or block eviction.

vLLM 0.23's native `simple_kv_offload` is not a substitute: it stores an extra CPU copy but retains
the active request's GPU block ownership, so it cannot increase active-session capacity.

## Next engineering question

The next step is a project-owned worker/connector that actually transfers active KV ownership while
keeping the same E1 gateway, model, and client. It must compare resident and conveyor modes inside
one implementation and validate H2D, D2H, deadlines, attention correctness, and cancellation under
the same run artifact contract.

E4-E6 remain future work: injection priority/cancel semantics, long-horizon correctness against a
sliding window, and cross-hardware/model generalization.
