# Metronome

**Frame-budget serving for real-time interaction models.**

📄 Paper: [arXiv:2607.02640](https://arxiv.org/abs/2607.02640) · [PDF](https://arxiv.org/pdf/2607.02640)

Interaction models (Thinking Machines' TML-Interaction-Small, MiniCPM-o 4.5, Kyutai
Moshi, Qwen-Omni) do not behave like chatbots at the serving layer. They run a
*persistent, periodic session*: every tick (80 ms – 1 s) they ingest a new chunk of
audio/video as a small prefill and decode a short response, indefinitely. The hard
constraint is a recurring **wall-clock deadline** (a frame budget), not aggregate
throughput, and the per-session KV cache is both the dominant cost and the thing that
decides whether you hit the deadline.

Today's serving stacks (vLLM, SGLang) assume the opposite: ephemeral requests, a
throughput goal, and KV that can be swapped out during idle slack. There is no idle
slack inside an interaction session.

**Metronome** is a serving system + scheduling model that treats interaction sessions as
periodic real-time tasks and manages per-session KV as the joint cost/schedulability
knob:

- a **persistent periodic-session** abstraction (pinned, append-only KV),
- a **deadline-aware tick scheduler** with admission control over per-session KV budgets,
- a **tiered, model-aware KV manager** (hot HBM working set + eviction/offload), and
- a **real-time capacity/jitter benchmark** that replaces tokens/sec and TTFT with
  *max sustainable concurrent sessions at a target deadline-miss rate*.

## ▶ Headline: Metronome **over** vLLM-realtime

The strongest result, measured through the real gateway against vLLM's own realtime/streaming API
(append-to-resident-KV) as the baseline — same clients, gateway, model, budget; the only difference is
Metronome's bounded-KV policy ([`RESULTS_METRONOME_OVER_VLLM.md`](RESULTS_METRONOME_OVER_VLLM.md)).

**The differentiator is DURATION, not short-burst concurrency.** Fresh, vanilla vLLM-realtime handles high
concurrency fine in short bursts (flat ~4–6 ms to N=160/120 s). Its real failure is **minute-level**
unbounded-context growth:

**Panel 1 — minute-level memory wall** (fresh N=96, **300 s**, per-frame p50):

| elapsed | vanilla vLLM-realtime (unbounded) | **Metronome in-engine windowed-KV** |
|---|---|---|
| 0–30 s | 2–5 ms | 4 ms |
| 270–300 s | **1601 ms** (drift +1348, degrading) | **1–2 ms · flat** |

**Panel 2 — online admission** (open-system ramp, offer 384): the AIMD controller **discovers N\*≈175**
from per-frame latency, admits them at steady **p99 8 ms**, and cleanly rejects the 209 excess — vs
degrading everyone without admission.

vLLM-realtime supplies the *mechanism* (append-to-resident-KV); it has no bounded-KV policy (context grows
unbounded → per-frame latency drifts to the frame-budget wall over minutes) and no online admission.
Metronome's in-engine windowed-KV (vLLM `SlidingWindowSpec`, FIX 5) **removes the age-dependent drift**
(flat 1–2 ms for 5 min); its AIMD admission turns open-system overload into **bounded goodput**. The policy
layer is the contribution, measured as a delta over vanilla vLLM-realtime — not a strawman.
*(Rigor note: an earlier 90 s sweep that suggested a burst-capacity collapse at N=128 was a
sequential-sweep / external-GPU-contention artifact; fresh single-N runs are flat — see the doc.)*
Full results: [`RESULTS_METRONOME_OVER_VLLM.md`](RESULTS_METRONOME_OVER_VLLM.md).

## ▶ Authoritative validated evaluation

**[`SYSTEM_EVAL.md`](SYSTEM_EVAL.md)** is the consolidated, end-to-end reference: the *built* serving
system (real client → Go gateway `full_duplex` → gRPC → vLLM/Moshi worker → output) and its *validated*
results — sustained full-duplex capacity by latency SLO, correctness under load, and the analytical
capacity model — all measured through the real stack with real audio and sustained multi-client load.
Detailed sustained traces: [`RESULTS_REALTIME_LOAD.md`](RESULTS_REALTIME_LOAD.md). (The
engine/simulator sections below are the earlier synthetic-cost study, superseded by the real end-to-end
evaluation for the full-duplex operating mode.)

**Headline (p99 ≤ 1 s, distinct streams, one Blackwell GPU):** MiniCPM-o-4.5 **48** · Qwen3-Omni-30B-A3B-FP8
**~64–128** · Qwen2.5-Omni-7B **~7** (encoder-bound) · Moshi **16** @ its 80 ms budget (real voice-out).
> *Note:* these are the older **windowed-8 s `fd_step`** path (vLLM 0.19) and predate the **fresh-per-point**
> methodology — some came from sequential multi-N sweeps and may be sweep-affected. The authoritative,
> fresh-re-verified **streaming** (append-to-resident-KV) capacities are in
> [`RESULTS_METRONOME_OVER_VLLM.md`](RESULTS_METRONOME_OVER_VLLM.md) (e.g. fresh streaming: 30B ≥160, MiniCPM
> ~96, 7B ~16–24, Moshi ≥32 — all one-worker-per-N).

## Repository map

| Path | Contents |
|---|---|
| [`SYSTEM_EVAL.md`](SYSTEM_EVAL.md) | **Authoritative**: built system + validated end-to-end evaluation (capacity-by-SLO, correctness, analytical model). |
| [`RESULTS_REALTIME_LOAD.md`](RESULTS_REALTIME_LOAD.md) | Detailed sustained full-duplex traces (per-N p50/p90/p99, drift, windowed-vs-streaming). |
| [`RESULTS_METRONOME_OVER_VLLM.md`](RESULTS_METRONOME_OVER_VLLM.md) | **Headline**: Metronome windowed-KV vs vanilla vLLM-realtime through the gateway (>1.7× concurrency at production latency). |
| [`RESULTS_A2A.md`](RESULTS_A2A.md) | Apple-to-apple concurrency: windowed-8s vs resident-context streaming, same clients/gateway/model/N. |
| [`docs/vllm_omni_streaming_triage.md`](docs/vllm_omni_streaming_triage.md) · [`patches/`](patches/vllm_0.23_omni_blackwell.patch) | vLLM 0.23 omni-init on Blackwell: root-cause + **fixed/verified** (Qwen3-Omni loads + streaming session demonstrated, flat ~5 ms/frame). |
| [`docs/RESEARCH_PLAN.md`](docs/RESEARCH_PLAN.md) | The full plan: framing, formal model, system design, experiments, risks, design-decision log. |
| [`docs/RELATED_WORK.md`](docs/RELATED_WORK.md) | Annotated survey across 7 axes + positioning table. |
| [`docs/PIPELINE.md`](docs/PIPELINE.md) | The executable end-to-end pipeline with go/no-go gates. |
| [`docs/PAPER.md`](docs/PAPER.md) | **Paper draft** — abstract, contributions, results, limitations. |
| [`RESULTS_ENGINE.md`](RESULTS_ENGINE.md) | **Headline capacity numbers measured on the real serving engine** (`metronome/engine.py`) + real-model serving on vLLM. |
| [`docs/INTEGRATION.md`](docs/INTEGRATION.md) | **Developer guide**: `pip install`, the `MetronomeServer` API, and the vLLM integration (SGLang is a drop-in backend). |
| [`RESULTS.md`](RESULTS.md) | Simulator findings (closed population), validated against the engine — every number traced to a script + artifact. |
| [`docs/PRODUCTION.md`](docs/PRODUCTION.md) · [`RESULTS_PROD.md`](RESULTS_PROD.md) | **Production** workload cases, metrics, design + open-system results (churn, co-aging, turn-taking, heterogeneous SLAs, adaptive budget). |
| [`RESULTS_SCHED.md`](RESULTS_SCHED.md) | **Scheduling, scalability & systems**: live multi-tenant validation, sub-batching, co-aging-safe admission, heterogeneous periods, O(1) admission, multi-GPU, DVFS, paged KV. |
| `metronome/` | The system: periodic-session object, EDF scheduler, KV-budget admission, tiered KV manager, cost model. |
| `bench/` | The benchmark: per-tick GPU kernel, metrics (MSCS/jitter/cost), generator, GPU window guard ([`bench/README.md`](bench/README.md)). |
| `sim/` | Calibrated discrete-event multi-tenant simulator (cost = measured cost model). |
| `experiments/` | Reproducible experiments S0–S11; `run_all.py` drives them. |
| `results/` | Figures, raw curves, fitted cost models, leaderboard. |
| `tests/` | Unit tests (`python3 -m pytest tests/`). |

## Status: implemented and evaluated (small / open-model regime)

Built and evaluated on three open interaction models (Moshi, MiniCPM-o 4.5,
Qwen3-Omni) on an RTX PRO 6000 Blackwell. **A real serving engine
([`metronome/engine.py`](metronome/engine.py)) — a stateful multi-tenant GPU decode
loop using FlashAttention's paged-KV kernel — produces the headline capacity numbers
([`RESULTS_ENGINE.md`](RESULTS_ENGINE.md)); the calibrated simulator is a *predictor
validated against the engine*, used for sweeps too large to run live.**

- **Real measured MSCS gain** (windowed KV vs throughput-greedy full-KV, on the
  running engine): **3.2× Moshi, 4.0× MiniCPM-o, 2.67× Qwen3-Omni**; \$/session-hour
  down to \$0.016–0.031.
- **Real GATE A:** measured per-tick latency climbs with session age and crosses the
  deadline at the real concurrency onset (e.g. Moshi p99 89 ms at N=160 > 80 ms).
- **Engine vs simulator:** memory-bound capacities match exactly (Moshi B1 40=40);
  timing-bound capacities are *lower* than the cost-model formula (real FlashAttention
  + MoE-FFN overhead the linear model omits) — the gap only the real system exposes.
- **KV management essential (real 3.2–4.0×) for no-self-bounding Moshi/MiniCPM-o,
  complementary (2.67×) for self-windowing Qwen.** GATE B held-out cost-model error
  0.5–4.4% on a clean GPU.

**Use it** (developer API — wraps a real serving backend; see
[`docs/INTEGRATION.md`](docs/INTEGRATION.md)):

```python
from metronome import MetronomeServer
from metronome.backends.vllm_backend import VLLMBackend
backend = VLLMBackend("Qwen/Qwen3-8B", gpu_memory_utilization=0.6, max_model_len=32768)
server  = MetronomeServer(backend, frame_budget_s=0.2, kv_budget_tokens=2048, tokens_per_tick=25)
server.calibrate()                       # fit the cost model to this backend+model
if server.admit(sid): ...                # deadline-aware admission (else shed)
print(server.serve(32, 50)["miss_rate"], server.mscs())   # measured on real vLLM
```

**Serve it** — over an **OpenAI Realtime-compatible** WebSocket API (the right surface
for full-duplex audio; Metronome adds deadline-aware admission):

```bash
pip install -e ".[realtime]"
metronome-realtime --backend vllm --model Qwen/Qwen3-8B --frame-budget 0.2   # real audio API
metronome-realtime --backend mock --model moshi --frame-budget 0.08          # no GPU (protocol)
```

```bash
pip install -e ".[vllm]"                # install with the vLLM backend
python3 experiments/vllm_demo.py        # real-model serving demo (Qwen3)
python3 experiments/realtime_demo.py    # Realtime audio API + admission demo (no GPU)
python3 experiments/fit_cost_model.py   # GPU: fit C(L)=C_fixed+α·L per model
python3 experiments/run_all.py --gpu    # full pipeline (CPU sweeps + live stages)
python3 -m pytest tests/                # unit tests
```

Working title: *Metronome: Frame-Budget Scheduling and KV-Budget Admission Control for
Real-Time Serving of Interaction Models.* Target venues: MLSys / OSDI / EuroSys / NSDI.

## Citation

Paper: **Metronome: Bound the Cache, Keep the Beat for Real-Time Interaction Model
Serving** — [arXiv:2607.02640](https://arxiv.org/abs/2607.02640).

```bibtex
@article{metronome2026,
  title         = {Metronome: Bound the Cache, Keep the Beat for Real-Time Interaction Model Serving},
  author        = {Meng, Jiaying and Li, Bojie},
  year          = {2026},
  eprint        = {2607.02640},
  archivePrefix = {arXiv},
  primaryClass  = {cs.SD},
  url           = {https://arxiv.org/abs/2607.02640}
}
```
