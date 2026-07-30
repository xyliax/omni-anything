"""What does one injection do to a saturated engine?

N=96 random (util=1.0, queue-equilibrium batching), single L=8192 tool result
at t=30s, current whole-splice semantics. Compare against the same injection
at N=12 (idle slack available). Measures: misses, distinct victim sessions,
lateness, and recovery time (beat latency back to pre-injection median).
Then a 30s Poisson run (spec workload rate) at N=96 for the sustained view.
"""
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from calib_model import load_default
from engine import Engine, Policy, BEAT_MS

cal = load_default(Path(__file__).parent.parent / "calibration" / "data",
                   "Qwen3-1.7B")

def single_shot(N):
    e = Engine(cal, n_sessions=N, seed=1, sim_ms=60000, tool_rate_per_min=0,
               phase="random", track_beats=True,
               fixed_tools=[(30000.0, 0, 8192, 1.0)])
    r = e.run()
    pre = [b["latency_ms"] for b in r["beat_log"] if b["arrival_ms"] < 29000]
    pre_p50 = statistics.median(pre)
    hit = [m for m in r["miss_events"] if m["t"] >= 30000]
    victims = {m["sid"] for m in hit}
    # recovery: first 480ms bucket after injection whose median latency is back
    # within 1.5x pre-injection median
    rec_ms = None
    for k in range(0, 40):
        lo = 30001 + k * BEAT_MS
        seg = [b["latency_ms"] for b in r["beat_log"]
               if lo <= b["arrival_ms"] < lo + BEAT_MS]
        if seg and statistics.median(seg) <= 1.5 * pre_p50:
            rec_ms = lo - 30001
            break
    worst = max((m["lateness_ms"] for m in hit), default=0)
    print(f"N={N:>3}: 注入前 beat_p50={pre_p50:6.1f}ms | 注入后 miss={len(hit):>3} 次 "
          f"受害会话={len(victims):>2}/{N} 最大迟到={worst:6.0f}ms "
          f"恢复用时≈{rec_ms if rec_ms is not None else '>19200'}ms "
          f"dropped_beats={r['dropped_beats']}")
    return r

print("== 单发 L=8192 注入 @30s，整段拼回 ==")
single_shot(12)
single_shot(48)
single_shot(96)

print("\n== 规格负载(每路泊松 6 次/分钟, L=2048, 整段) 持续 30s ==")
for N in (12, 48, 96):
    e = Engine(cal, n_sessions=N, seed=1, sim_ms=30000, tool_rate_per_min=6.0,
               tool_L=2048, policy=Policy.WHOLE, phase="random")
    r = e.run()
    ok = sum(1 for v in r["per_session"].values()
             if v["beats"] and v["misses"] / v["beats"] <= 0.01)
    print(f"N={N:>3}: miss率={r['miss_rate']*100:6.2f}%  beat_p99={r['beat_p99_ms']:>7.1f}ms "
          f"体验合格会话={ok}/{N}  跨会话miss={r['cross_session_misses']} "
          f"答案送达率={r['answers_delivered']}/{r['total_tools']}")
