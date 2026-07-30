"""Validation: replay ONE small scenario on the real GPU and on the simulator,
then compare timelines. Passing bar (per task spec): <15% error.

Scenario (deliberately reproducible by hand):
  1 session, initial context `ctx0`, `n_beats` beats.
  Each beat: 8-token micro-prefill, then m_t decode steps (fixed script).
  At beat `inject_at`, an L-token tool result is spliced in whole (baseline
  policy (a)), competing with that beat's decode work.

The GPU side executes exactly this sequence with the same engine mechanics
(one forward per step, FCFS, whole-splice) and records per-beat wall clock.
The simulator side runs the same script through the calibration model.
"""
import argparse
import csv
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "calibration"))

# fixed decode script so both sides do identical work
SCRIPT_M = [3, 2, 4, 2, 3, 2, 3, 4, 2, 3, 2, 4]


def gpu_probe(gpu):
    """SM clock / power / throttle sample, recorded per beat.

    The card is shared. A co-tenant ramping up mid-run inflates decode steps by
    up to 2x (see calibration/data/diag_post_prefill_decode.json, where 12.8ms
    decode steps appear at ctx=2081 while the same steps cost 6.7ms two beats
    earlier). Recording the clock alongside each beat makes that visible in the
    artifact instead of leaving it to be inferred from a failed comparison.
    """
    import subprocess
    q = "clocks.sm,power.draw,utilization.gpu,clocks_throttle_reasons.active"
    try:
        out = subprocess.run(
            ["nvidia-smi", f"--id={gpu}", f"--query-gpu={q}",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5).stdout.strip()
        f = [x.strip() for x in out.split(",")]
        return {"sm_mhz": float(f[0]), "power_w": float(f[1]),
                "util_pct": float(f[2]), "throttle": f[3]}
    except Exception:
        return {"sm_mhz": 0.0, "power_w": 0.0, "util_pct": 0.0, "throttle": "?"}


class ClockSampler:
    """Poll the GPU in a background thread, never on the beat loop.

    Calling nvidia-smi between beats costs ~55ms of wall time; that idle gap
    lets the card drop power state, and the next wake pays a ramp-up. It showed
    up as a reproducible 22.9->31.8ms climb in the wake step across 5 attempts
    (simulator/validation_runs/steps_*.csv) which vanished once the probe left
    the loop -- the instrument was creating the effect it was added to detect.
    """

    def __init__(self, gpu, period_s=0.5):
        import threading
        self.gpu, self.period = gpu, period_s
        self._last = {"sm_mhz": 0.0, "power_w": 0.0, "util_pct": 0.0,
                      "throttle": "?"}
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._loop, daemon=True)

    def _loop(self):
        while not self._stop.is_set():
            self._last = gpu_probe(self.gpu)
            self._stop.wait(self.period)

    def start(self):
        self._t.start()
        return self

    def latest(self):
        return dict(self._last)

    def stop(self):
        self._stop.set()


def gpu_side(model_path, gpu, ctx0, n_beats, inject_at, L, budget, max_len):
    """Replay the scenario on a real vLLM V0 engine.

    Mechanism mapping (same as the simulator's):
      * one beat = wake the session with its grown context, decode m tokens,
        park it again (request finishes) -> exactly the park/wake semantics of
        mechanism (3). Prefix caching makes the wake cost only the new tokens.
      * the tool result is appended to the context before the wake, so it is
        absorbed as one prefill chunked at max_num_batched_tokens -> mechanism
        (2) and (5).
      * every engine step is timed individually with CUDA sync.
    """
    from bench_vllm import VEngine

    q = gpu_probe(gpu)
    if q["util_pct"] > 5 or q["power_w"] > 160:
        print(f"  [gpu] WARNING: card is busy before we start "
              f"({q['util_pct']:.0f}% util, {q['power_w']:.0f}W). A co-tenant "
              f"inflates decode steps up to 2x; this run is not a clean test.")

    ve = VEngine(model_path, max_batched=budget, max_len=max_len, util=0.36,
                 prefix_caching=True, max_seqs=8)
    rng = __import__("random").Random(20240727)
    ctx = [rng.randrange(1000, 100000) for _ in range(ctx0)]

    # warmup: one throwaway wake/decode so allocator + graphs are hot
    ve.drain()
    ve.add_ids(ctx + [rng.randrange(1000, 100000) for _ in range(8)], 8)
    for _ in range(40):
        if not ve.has_work():
            break
        ve.step_timed()
    ve.drain()

    beats = []
    sampler = ClockSampler(gpu).start()
    t_start = time.perf_counter()
    for i in range(n_beats):
        m = SCRIPT_M[i % len(SCRIPT_M)]
        # new audio slice for this beat (8-token micro-prefill)
        ctx += [rng.randrange(1000, 100000) for _ in range(8)]
        # tool result arrives at the head of this beat -> whole splice
        if i == inject_at:
            ctx += [rng.randrange(1000, 100000) for _ in range(L)]
        t0 = time.perf_counter()
        ve.add_ids(ctx, m)
        wake_ms = (time.perf_counter() - t0) * 1e3   # scheduler/CPU-side cost
        steps = []
        gen = []
        while ve.has_work():
            dt, outs = ve.step_timed()
            ntok = 0
            for o in outs:
                if o.outputs and o.outputs[0].token_ids:
                    ntok = len(o.outputs[0].token_ids)
                    gen = list(o.outputs[0].token_ids)
            steps.append(("step", ntok, dt))
        beat_ms = (time.perf_counter() - t0) * 1e3
        t_end = (time.perf_counter() - t_start) * 1e3
        probe = sampler.latest()
        ctx += gen[:m]      # the model's own output joins the context
        beats.append({
            "beat": i, "m": m, "beat_ms": beat_ms,
            "t_end_ms": t_end,
            "injected": i == inject_at, "n_steps": len(steps), "steps": steps,
            "wake_ms": wake_ms,
            "step_sum_ms": sum(s[2] for s in steps),
            **probe,
        })
        print(f"  [gpu] beat {i:>2} m={m} ctx={len(ctx):>6} steps={len(steps):>2}"
              f" -> {beat_ms:8.1f}ms"
              + ("  <-- INJECTION" if i == inject_at else ""), flush=True)
    sampler.stop()
    ve.shutdown()
    return beats


def sim_side(cal, ctx0, n_beats, inject_at, L, budget, wake_ms=0.0):
    """Same script through the calibration model, same step decomposition.

    Mirrors vLLM's chunked-prefill step accounting: the uncached suffix is
    absorbed in ceil(P/budget) prefill steps, the last of which emits the first
    output token, followed by m-1 pure decode steps.
    """
    beats = []
    ctx = ctx0
    t = 0.0
    for i in range(n_beats):
        m = SCRIPT_M[i % len(SCRIPT_M)]
        t0 = t
        steps = []
        t += wake_ms                      # add_request / block-alloc CPU cost
        pending = 8 + (L if i == inject_at else 0)
        while pending > 0:
            take = pending if budget <= 0 else min(pending, budget)
            dt = cal.step_ms(B=0, ctx=ctx, decode_tokens=0, prefill_tokens=take,
                             prefill_ctx=ctx)
            t += dt
            ctx += take
            pending -= take
            steps.append(("prefill", take, dt))
        # Measured (validation_steps.csv): the prefill step does NOT sample the
        # beat's first token -- a separate decode step does. So a beat of m
        # tokens costs 1 prefill step + m decode steps.
        for _ in range(m):
            dt = cal.step_ms(B=1, ctx=ctx, decode_tokens=1, prefill_tokens=0)
            t += dt
            ctx += 1
            steps.append(("decode", 1, dt))
        beats.append({"beat": i, "m": m, "beat_ms": t - t0, "t_end_ms": t,
                      "injected": i == inject_at, "n_steps": len(steps),
                      "steps": steps})
    return beats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--gpu", type=int, default=3)
    ap.add_argument("--tag", default="Qwen3-1.7B")
    ap.add_argument("--ctx0", type=int, default=2048)
    ap.add_argument("--beats", type=int, default=10)
    ap.add_argument("--inject-at", type=int, default=5)
    ap.add_argument("--L", type=int, default=2048)
    ap.add_argument("--budget", type=int, default=2048)
    ap.add_argument("--max-len", type=int, default=17000)
    ap.add_argument("--calib-dir", default=str(Path(__file__).parent.parent /
                                              "calibration" / "data"))
    args = ap.parse_args()

    from calib_model import load_default
    cal = load_default(args.calib_dir, args.tag)
    print("[calib]", json.dumps(cal.summary()))

    print("[gpu] replaying scenario on real hardware...")
    g = gpu_side(args.model, args.gpu, args.ctx0, args.beats,
                 args.inject_at, args.L, args.budget, args.max_len)
    # Per-step detail, so a timeline mismatch can be localised to a step rather
    # than guessed at from the beat total.
    with open(Path(__file__).parent / "validation_steps.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["beat", "m", "injected", "step_idx", "tokens_out", "ms"])
        for b in g:
            for j, (_k, nt, ms) in enumerate(b["steps"]):
                w.writerow([b["beat"], b["m"], int(b["injected"]), j, nt,
                            round(ms, 3)])

    wake = statistics.median(b["wake_ms"] for b in g)
    print(f"[gpu] median add_request (CPU-side wake) cost: {wake:.2f}ms")
    print("[sim] replaying same scenario in simulator...")
    s = sim_side(cal, args.ctx0, args.beats, args.inject_at, args.L, args.budget,
                 wake_ms=wake)

    rows = []
    for gb, sb in zip(g, s):
        err = 100 * (sb["beat_ms"] - gb["beat_ms"]) / gb["beat_ms"]
        cum_err = 100 * (sb["t_end_ms"] - gb["t_end_ms"]) / gb["t_end_ms"]
        rows.append({"beat": gb["beat"], "m": gb["m"], "injected": int(gb["injected"]),
                     "gpu_steps": gb["n_steps"], "sim_steps": sb["n_steps"],
                     "gpu_beat_ms": round(gb["beat_ms"], 2),
                     "sim_beat_ms": round(sb["beat_ms"], 2),
                     "beat_err_pct": round(err, 2),
                     "gpu_cum_ms": round(gb["t_end_ms"], 2),
                     "sim_cum_ms": round(sb["t_end_ms"], 2),
                     "cum_err_pct": round(cum_err, 2),
                     "sm_mhz": gb.get("sm_mhz"), "power_w": gb.get("power_w"),
                     "gpu_util_pct": gb.get("util_pct")})
        print(f"  beat {gb['beat']:>2}: gpu={gb['beat_ms']:>8.1f}ms "
              f"sim={sb['beat_ms']:>8.1f}ms err={err:>+7.1f}% "
              f"| cum err {cum_err:>+6.1f}%")

    t3res = cal.cross_check_t3()
    errs = [abs(r["beat_err_pct"]) for r in rows]
    final_cum = abs(rows[-1]["cum_err_pct"])
    verdict = {
        "mean_abs_beat_err_pct": round(statistics.fmean(errs), 2),
        "max_abs_beat_err_pct": round(max(errs), 2),
        "final_cumulative_err_pct": round(final_cum, 2),
        "pass_bar_pct": 15.0,
        # Contention witness: the card is shared, so a run where the co-tenant
        # was busy is not a verdict on the model. Reported so the PASS/FAIL can
        # be read together with the conditions it was taken under.
        "gpu_power_w_range": [min(b.get("power_w", 0) for b in g),
                              max(b.get("power_w", 0) for b in g)],
        "gpu_sm_mhz_min": min(b.get("sm_mhz", 0) for b in g),
        "PASS": bool(final_cum < 15.0 and statistics.fmean(errs) < 15.0),
        "gpu_median_wake_ms": round(wake, 3),
        "scenario": {"ctx0": args.ctx0, "beats": args.beats,
                     "inject_at": args.inject_at, "L": args.L,
                     "budget": args.budget, "model": args.model,
                     "decode_script": SCRIPT_M[:args.beats]},
    }
    out = Path(__file__).parent
    with open(out / "validation_timeline.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    (out / "validation_report.json").write_text(json.dumps(
        {"verdict": verdict, "calibration": cal.summary(), "timeline": rows,
         "t3_cross_check": t3res}, indent=2))
    print("\n" + json.dumps(verdict, indent=2))
    print("PASS" if verdict["PASS"] else "FAIL")


if __name__ == "__main__":
    main()
