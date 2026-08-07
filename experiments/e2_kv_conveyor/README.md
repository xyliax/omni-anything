# E2: KV conveyor mechanism

E2 measures whether a tail-KV conveyor can turn the E1 pool's idle H2D bandwidth into additional
logical KV capacity. Both arms use compute service times extracted from the retained E1
Qwen2.5-Omni/vLLM scheduler trace. Every E2 run freshly measures pinned H2D service time on the
selected GPU.

## Evidence boundary

This is a trace-driven CUDA mechanism prototype. It validates byte accounting, transfer deadlines,
staging residency, phase overlap, and predicted time-to-capacity-wall. It does not yet modify
vLLM's active-request block ownership, so it is not an end-to-end serving result and must not be
reported as one. vLLM 0.23 native KV offload only caches active prefixes; it does not release their
GPU ownership and therefore is not a valid conveyor implementation.

## Arms

| Arm | KV placement | Phase |
| --- | --- | --- |
| `resident_sync` | Full context remains resident | E1 synchronized baseline |
| `conveyor_tdma` | A fixed tail lives in host DRAM and stages before use | Compute-constrained TDMA groups |

The default pool is the E1-reported 73,728 tokens. Qwen2.5-Omni thinker KV is 57,344 bytes/token
(28 layers, 4 KV heads, head dimension 128, bf16). The default growth rate is the E1-derived
78 tokens/session/tick.

TDMA grouping is constrained by the E1 compute profile. Uniform batch-one rotation is not
schedulable on this GPU: eight measured batch-one bursts require far more than one 2s period. The
default `7+1` grouping is therefore a measured compute-aware operating point, not a cosmetic
parameter. E3 scans neighboring group sizes instead of assuming it is universally optimal.

```bash
.venv-vllm023/bin/python -m experiments.e2_kv_conveyor.run --plan
.venv-vllm023/bin/python -m experiments.e2_kv_conveyor.run --gpu 3
.venv-vllm023/bin/python -m experiments.e2_kv_conveyor.aggregate --name <aggregate-id>
```

Each invocation creates `results/e2_kv_conveyor/runs/<run-id>/` with manifest, fresh link samples,
the complete transfer timeline, summary, terminal status, checksums, and an explicit claim boundary.

Inspect the complete source E1 view plus appended compute, H2D, queue, deadline, and capacity lanes
with the shared exporter:

```bash
python3 -m observability.export_perfetto <run-id>
```

It verifies the source E1 scheduler SHA-256, preserves E1's engine/gateway/KV/GPU lanes, verifies
stored transfers against deterministic replay, and writes the extended trace under that run's
`derived/` directory. See [`../../observability/README.md`](../../observability/README.md).

## Current result

Five 2026-08-06 repetitions measured 12.289-12.298 GB/s H2D, had zero transfer/output misses, and
moved the modeled capacity wall from 236s to 248s (`1.05085x`). The gain is only about 5.1% because
the measured compute profile permits a `7+1` split but not fine-grained one-session rotation. See
`results/e2_kv_conveyor/aggregates/20260806_main/`.

The model includes the previous-tick content-freeze release constraint. It does not simulate the
small D2H writeback of newly appended tokens; that remains an explicit end-to-end implementation
requirement.
