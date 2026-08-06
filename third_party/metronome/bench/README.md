# Metronome-Bench

A reusable **real-time serving-capacity benchmark for interaction (full-duplex
streaming) models** — Contribution 3 of the Metronome project. It replaces
tokens/sec and TTFT with the metrics that matter for persistent periodic sessions.

## What it measures

| Metric | Definition | Why |
|---|---|---|
| **MSCS** | max sustainable concurrent sessions at a target deadline-miss rate | the real capacity of an interaction server |
| **deadline-miss rate** | fraction of ticks that finish after the frame budget | the SLO; a missed frame is an audible glitch |
| **jitter** | p50 / p99 / **p999** per-tick latency | the tail is the story at an 80 ms budget |
| **\$/session-hour** | GPU rental ÷ MSCS | the cost of serving one live session |

It is **not** a dialogue-quality benchmark (that is Full-Duplex-Bench's job); it
measures *serving capacity*, the gap no existing benchmark fills.

## Components

- `models.py` (in `metronome/`) — confirmed serving facts (KV bytes/token, tick
  cadence, context ceiling, self-windowing) for Moshi, MiniCPM-o 4.5, Qwen3-Omni.
- `tick_kernel.py` — the faithful per-tick transformer kernel, timed on the GPU
  with CUDA graphs, producing the cost-model constants. **Everything in a figure
  traces to a measurement from here or to a primary source.**
- `generator.py` — parameterised synthetic session generator (arrival rate,
  session-length distribution, talk/silence ratio, phase jitter, video fps).
- `metrics.py` — MSCS, jitter percentiles, and the cost model.
- `gpu_probe.py` — shared-GPU window guard (politeness on a multi-tenant GPU).
- `../sim/simulator.py` — the calibrated discrete-event simulator; its per-tick
  cost is the *measured* cost model, validated live (`experiments/validate_sim.py`).

## Reproducing a headline number

```bash
# 1. fit the cost model on your GPU (measures KV-read cost vs context length)
python3 experiments/fit_cost_model.py --models moshi minicpm-o qwen3-omni

# 2. validate the simulator against the live GPU (G5)
python3 experiments/validate_sim.py

# 3. establish the problem (GATE A) and run the core eval (MSCS, jitter, cost)
python3 experiments/establish_problem.py
python3 experiments/core_eval.py
```

All constants are re-measured per machine, so the benchmark is portable across
A100 / H100 / RTX-class GPUs; only the fitted `alpha` (∝ 1/HBM-bandwidth) and the
fixed cost change.

## Leaderboard schema

`results/core/core_summary.json` is the leaderboard: for each model and policy
(B0/B1/B2/M), the MSCS @ 0.1 % miss rate and \$/session-hour. A third party
reproduces a row by re-running steps 1–3 on their hardware.
