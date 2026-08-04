"""S1-S3 experiment matrix on the discrete-event simulator.

S1=density, S2=cancellation, S3=injection shock (renumbered 2026-08).

Every scenario runs multiple seeds; we report mean +/- stdev.
"""
import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from calib_model import Calibration, load_default  # noqa: E402
from engine import Engine, Policy, BEAT_MS  # noqa: E402

RES = Path(__file__).parent.parent / "results"
# Measured on the calibration card (calibration/data/env_Qwen3-1.7B.json):
# Qwen3-1.7B fp16, 28 layers x 8 KV heads x 128 dim x 2 (K+V) x 2 bytes.
KV_KB_PER_TOKEN = 112.0
KV_POOL_TOKENS = 44336


def agg(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return (None, None)
    m = statistics.fmean(vals)
    s = statistics.pstdev(vals) if len(vals) > 1 else 0.0
    return (round(m, 4), round(s, 4))


def write(name, rows):
    if not rows:
        return
    RES.mkdir(parents=True, exist_ok=True)
    p = RES / f"{name}.csv"
    keys = sorted({k for r in rows for k in r})
    pref = [k for k in ("scenario", "L", "N", "policy", "phase") if k in keys]
    keys = pref + [k for k in keys if k not in pref]
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print(f"[write] {p} ({len(rows)} rows)")


def run(cal, seeds, **kw):
    out = []
    kw.setdefault("kv_pool_tokens", KV_POOL_TOKENS)
    for sd in seeds:
        e = Engine(cal, seed=sd, **kw)
        out.append(e.run())
    return out


def kv_note(rs):
    """Fraction of steps where the modelled KV demand exceeded the real pool.

    Past that point a real engine would preempt or swap, which this simulator
    does not model, so any row with a non-zero value here is an upper bound on
    achievable density rather than a measurement of one.
    """
    return agg([r["kv_overflow_steps"] / max(1, r["steps"]) for r in rs])[0]


# ------------------------------------------------------------------ S1
def s1(cal, seeds, sim_ms, out):
    """Injection shock on a single session; sweep L. Find blow-up threshold.

    The injection is deterministic (one tool result landing mid-run) rather than
    Poisson, so the shock is attributable to a known beat and the before/after
    timeline is directly readable.
    """
    rows = []
    timeline = []
    # Beats are aligned so the injection can be placed at a known offset inside
    # the beat period. A lone session finishes its beat in ~20-45ms and then
    # leaves ~440ms of idle GPU, so a splice that starts early is partly free
    # while the same splice starting late spills entirely onto the next beat.
    # Sweeping the offset is the only way to separate L from that phase luck.
    beat0 = int(sim_ms / 2 // BEAT_MS) * BEAT_MS
    # 3072/5120/6144/7168 are off the spec's L grid, added only to bracket the
    # threshold: on the spec grid the first miss appears at 8192 and the answer
    # would be "somewhere in (4096, 8192]", which is not a threshold.
    for L in [0, 128, 256, 512, 1024, 2048, 3072, 4096, 5120, 6144, 7168, 8192]:
        for off in ([0] if L == 0 else S1_OFFSETS):
            inject_at_ms = beat0 + off
            tools = [] if L == 0 else [(inject_at_ms, 0, L, 1.0)]
            rows.append(_s1_cell(cal, seeds, sim_ms, L, off, inject_at_ms,
                                 tools, timeline))
    write(out, rows)
    write(out + "_timeline", timeline)
    return rows


S1_OFFSETS = [5, 120, 240, 360, 470]


def _s1_cell(cal, seeds, sim_ms, L, off, inject_at_ms, tools, timeline):
    rs = run(cal, seeds, n_sessions=1, sim_ms=sim_ms, tool_rate_per_min=0,
             tool_L=max(L, 1), policy=Policy.WHOLE, fixed_tools=tools,
             track_beats=True, phase="aligned")
    # per-beat completion times around the injection (first seed)
    for b in rs[0]["beat_log"]:
        rel = b["arrival_ms"] - inject_at_ms
        if -3 * BEAT_MS <= rel <= 6 * BEAT_MS:
            timeline.append({"L": L, "inject_offset_ms": off, **b,
                             "rel_to_injection_ms": round(rel, 2)})
    mr = agg([r["miss_rate"] for r in rs])
    mx = agg([r["beat_max_ms"] for r in rs])
    p99 = agg([r["beat_p99_ms"] for r in rs])
    nm = agg([r["total_misses"] for r in rs])
    ans = agg([r["answer_p50_ms"] for r in rs])
    # misses caused per injection
    per_inj = agg([r["total_misses"] / max(1, r["total_tools"]) for r in rs])
    # beats damaged per injection, and how long the damage lasts
    streak = []
    for r in rs:
        for m in r["miss_events"]:
            streak.append(m["lateness_ms"])
    row = {"scenario": "S3", "L": L, "inject_offset_ms": off,
                 "miss_rate": mr[0], "miss_rate_sd": mr[1],
                 "misses": nm[0], "misses_sd": nm[1],
                 "misses_per_injection": per_inj[0],
                 "mean_lateness_ms": round(statistics.fmean(streak), 2) if streak else 0,
                 "max_lateness_ms": round(max(streak), 2) if streak else 0,
                 "beat_p50_ms": agg([r["beat_p50_ms"] for r in rs])[0],
                 "beat_p99_ms": p99[0], "beat_max_ms": mx[0], "beat_max_sd": mx[1],
                 "answer_p50_ms": ans[0], "deadline_ms": BEAT_MS,
                 "splice_steps_expected": max(1, -(-L // 2048)) if L else 0,
                 "kv_overflow_step_frac": kv_note(rs),
                 "tools": agg([r["total_tools"] for r in rs])[0]}
    print(f"  S1 L={L:>5} off={off:>3}: misses={nm[0]:.1f} "
          f"max_beat={mx[0]:.0f}ms max_late={row['max_lateness_ms']:.0f}ms "
          f"answer_p50={ans[0]}")
    return row


# ------------------------------------------------------------------ S2
def s2(cal, seeds, sim_ms, out, nmax=320):
    """Density baseline, no injection: miss rate vs N, random vs aligned phase."""
    rows = []
    safe_n = {}
    kv_n = {}
    for phase in ["random", "aligned"]:
        found = None
        kv_last = None
        N = 1
        while N <= nmax:
            rs = run(cal, seeds, n_sessions=N, sim_ms=sim_ms,
                     tool_rate_per_min=0, phase=phase)
            mr = agg([r["miss_rate"] for r in rs])
            util = agg([r["utilisation"] for r in rs])
            fill = agg([r["batch_fill_ratio"] for r in rs])
            avgB = agg([r["avg_decode_B"] for r in rs])
            infl = agg([r["step_inflation_vs_ideal"] for r in rs])
            p99 = agg([r["beat_p99_ms"] for r in rs])
            rows.append({"scenario": "S1", "N": N, "phase": phase,
                         "miss_rate": mr[0], "miss_rate_sd": mr[1],
                         "utilisation": util[0], "avg_decode_B": avgB[0],
                         "batch_fill_ratio": fill[0],
                         "step_inflation_vs_ideal": infl[0],
                         "beat_p50_ms": agg([r["beat_p50_ms"] for r in rs])[0],
                         "beat_p99_ms": p99[0],
                         "steps": agg([r["steps"] for r in rs])[0],
                         "kv_peak_tokens": agg([r["kv_peak_tokens"] for r in rs])[0],
                         "kv_overflow_step_frac": kv_note(rs)})
            print(f"  S2 {phase:>7} N={N:>3}: miss={mr[0]:.4f} util={util[0]:.3f} "
                  f"avgB={avgB[0]:.2f} fill={fill[0]:.2f} infl={infl[0]:.2f}x "
                  f"kvof={kv_note(rs):.2f}")
            if kv_note(rs) == 0:
                kv_last = N
            if mr[0] > 0.01 and found is None:
                found = N
                break
            # Fine near the KV-feasible range (that is where the answer to
            # "safe density" lives), then coarse, because the deadline wall on
            # this model turns out to be an order of magnitude further out and
            # the brief asks the sweep to continue until misses exceed 1%.
            N = N + 1 if N < 12 else (N + 2 if N < 32 else
                                      (N + 8 if N < 96 else N + 16))
        safe_n[phase] = found
        kv_n[phase] = kv_last
    write(out, rows)
    return rows, safe_n, kv_n


# ------------------------------------------------------------------ S3
def s4(cal, seeds, sim_ms, out, N, tool_rate, Ls=(2048, 8192)):
    """Cancellation waste under 40% interrupt prior, current no-reclaim semantics."""
    rows = []
    for L in Ls:
        for ip in [0.0, 0.4]:
            rs = run(cal, seeds, n_sessions=N, sim_ms=sim_ms,
                     tool_rate_per_min=tool_rate, tool_L=L,
                     policy=Policy.WHOLE, interrupt_prob=ip)
            waste = agg([r["wasted_tokens"] for r in rs])
            stale = agg([r["stale_splices"] for r in rs])
            resid = agg([r["kv_residency_ms_mean"] for r in rs])
            residmx = agg([r["kv_residency_ms_max"] for r in rs])
            canc = agg([r["cancelled_tools"] for r in rs])
            tot = agg([r["total_tools"] for r in rs])
            mr = agg([r["miss_rate"] for r in rs])
            # Wasted KV footprint at the measured 112 KB/token for this model.
            occ = agg([r["wasted_tokens"] * KV_KB_PER_TOKEN / 1024**2 for r in rs])
            inv = agg([r["invalid_ctx_tokens"] for r in rs])
            invp = agg([r["invalid_ctx_peak_tokens"] for r in rs])
            # Peak stale context as a share of the context actually resident at
            # peak. At L=8192 the whole working set exceeds the pool (see
            # kv_overflow_step_frac), so the pool percentage overshoots 100% and
            # this ratio is the interpretable one: of the KV the engine is
            # holding, how much is known-dead.
            invres = agg([100 * r["invalid_ctx_peak_tokens"] / max(1, r["kv_peak_tokens"])
                          for r in rs])
            stages = {}
            for st in ("in_flight", "returned", "spliced"):
                stages[f"cancelled_{st}"] = agg([r["cancel_stages"][st] for r in rs])[0]
            rows.append({
                "scenario": "S2", "L": L, "interrupt_prob": ip, "N": N,
                "wasted_tokens": waste[0], "wasted_tokens_sd": waste[1],
                "wasted_KV_GiB": occ[0],
                # Cumulative across the run (nothing is reclaimed, so this can
                # exceed the pool) vs the peak resident at one instant, which is
                # the figure that has to fit in real memory.
                "invalid_ctx_tokens_cumulative": inv[0],
                "invalid_ctx_cumulative_pct_of_pool": round(
                    100 * (inv[0] or 0) / KV_POOL_TOKENS, 2),
                "invalid_ctx_peak_tokens": invp[0],
                "invalid_ctx_peak_pct_of_pool": round(
                    100 * (invp[0] or 0) / KV_POOL_TOKENS, 2),
                "invalid_ctx_peak_pct_of_resident": round(invres[0] or 0, 2),
                "stale_splices": stale[0],
                "cancelled_tools": canc[0], "total_tools": tot[0],
                "cancel_fraction": round((canc[0] or 0) / max(1, tot[0] or 1), 3),
                **stages,
                "kv_residency_ms_mean": resid[0],
                "kv_residency_ms_max": residmx[0],
                "miss_rate": mr[0],
                "wasted_gpu_ms": agg([r["wasted_gpu_ms"] for r in rs])[0],
                "wasted_gpu_pct": agg([100 * r["wasted_gpu_ms"] / max(1e-9, r["sim_ms"])
                                       for r in rs])[0],
                "kv_overflow_step_frac": kv_note(rs),
            })
            print(f"  S2 L={L:>5} ip={ip}: wasted={waste[0]:.0f}tok "
                  f"({occ[0]:.2f}GiB KV) stale_splices={stale[0]:.1f} "
                  f"cancelled={canc[0]:.1f}/{tot[0]:.1f} resid_mean={resid[0]:.0f}ms")
    write(out, rows)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calib-dir", default=str(Path(__file__).parent.parent /
                                              "calibration" / "data"))
    ap.add_argument("--tag", default="Qwen3-1.7B")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--suffix", default="")
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--sim-ms", type=float, default=60000)
    ap.add_argument("--scenarios", default="S1,S2,S3")
    ap.add_argument("--tool-rate", type=float, default=6.0)
    ap.add_argument("--force-n", type=int, default=0)
    args = ap.parse_args()

    cal = load_default(args.calib_dir, args.tag, args.scale)
    print("[calib]", json.dumps(cal.summary()))
    seeds = list(range(1, args.seeds + 1))
    sfx = args.suffix
    sc = args.scenarios.split(",")

    safe_n, kv_n = {}, {}
    # Renumbered 2026-08 whitelist: S1=density (was S2), S2=cancellation (was
    # S4), S3=injection shock (was S1). The policies matrix experiment was
    # removed from the repo scope.
    if "S1" in sc:
        print("[S1] density baseline")
        _, safe_n, kv_n = s2(cal, seeds, args.sim_ms, f"S1_density{sfx}")
        print("   deadline-safe N (first N with >1% miss):", safe_n)
        print("   KV-feasible N (last N fitting the measured pool):", kv_n)
    if "S3" in sc:
        print("[S3] injection shock, 1 session")
        s1(cal, seeds, args.sim_ms, f"S3_injection{sfx}")

    N = args.force_n
    if not N:
        # The binding constraint on this card is KV capacity, not the deadline:
        # the deadline sweep never reached 1% misses inside the KV-feasible
        # range, so "safe density" is the last N whose working set fits the
        # measured 44,336-token pool. Falling back on the deadline number would
        # silently pick a density the card cannot hold.
        base = kv_n.get("random") or safe_n.get("random") or 16
        N = max(1, int(0.7 * base))
    print(f"[S2] using N={N} (70% of safe density)")
    if "S2" in sc:
        s4(cal, seeds, args.sim_ms, f"S2_cancellation{sfx}", N, args.tool_rate)
    (RES / f"meta{sfx}.json").write_text(json.dumps({
        "calib": cal.summary(), "seeds": seeds, "sim_ms": args.sim_ms,
        "N_used": N, "tool_rate_per_min": args.tool_rate}, indent=2))


if __name__ == "__main__":
    main()
