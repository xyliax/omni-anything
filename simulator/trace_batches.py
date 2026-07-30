"""Trace per-step batch membership for the S2 N=12 random-phase run (seed 1).

Wraps Engine._admit to record which sessions landed in each step, renders an
ASCII timeline of the first 3 beat periods, and aggregates pair co-batching
counts over the full 60s run.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from calib_model import load_default
from engine import Engine, BEAT_MS

cal = load_default(Path(__file__).parent.parent / "calibration" / "data",
                   "Qwen3-1.7B")

trace = []          # (t0, dt, set_of_sids) per executed step
_orig_admit = Engine._admit
_orig_step = Engine._one_step

def admit(self, force_idle=False):
    dec, pre, dt_, pt_ = _orig_admit(self, force_idle)
    self._trace_members = {q.sid for q in dec} | {q.sid for q, _ in pre}
    return dec, pre, dt_, pt_

def one_step(self, force_idle=False):
    t0 = self.now
    ok = _orig_step(self, force_idle)
    if ok:
        trace.append((t0, self.now - t0, frozenset(self._trace_members)))
    return ok

Engine._admit = admit
Engine._one_step = one_step

N, SEED, SIM_MS = 12, 1, 60000
e = Engine(cal, n_sessions=N, seed=SEED, sim_ms=SIM_MS, tool_rate_per_min=0,
           phase="random")
phases = {s.sid: s.phase_ms for s in e.sessions.values()}
rep = e.run()

# ---------------------------------------------------------------- timeline
WIN_MS, COL_MS = 3 * BEAT_MS, 10.0
ncol = int(WIN_MS / COL_MS)
print(f"N={N} seed={SEED} random phase | util={rep['utilisation']} "
      f"avgB={rep['avg_decode_B']} steps={rep['steps']}\n")
print(f"时间轴: 0..{WIN_MS:.0f}ms, 每格 {COL_MS:.0f}ms; "
      "数字=该步内共有几路会话, '|'=拍到达但尚未开跑")
hdr = " sid(phase) " + "".join(
    str(int(c * COL_MS // 100) % 10) if (c * COL_MS) % 100 < COL_MS else " "
    for c in range(ncol))
print(hdr)
order = sorted(phases, key=lambda s: phases[s])
for sid in order:
    row = ["."] * ncol
    for (t0, dt, mem) in trace:
        if t0 >= WIN_MS or sid not in mem:
            continue
        c0, c1 = int(t0 / COL_MS), max(int(t0 / COL_MS), int((t0 + dt) / COL_MS))
        for c in range(c0, min(c1 + 1, ncol)):
            row[c] = str(min(9, len(mem)))
    for k in range(3):
        arr = phases[sid] + k * BEAT_MS
        c = int(arr / COL_MS)
        if c < ncol and row[c] == ".":
            row[c] = "|"
    print(f" s{sid:<2}({phases[sid]:>5.0f}) " + "".join(row))

# ------------------------------------------------- shared steps in window
print("\n窗口内 (0-1440ms) 共批的步:")
for (t0, dt, mem) in trace:
    if t0 < WIN_MS and len(mem) > 1:
        print(f"  t={t0:7.1f}ms dt={dt:5.1f}ms  members={sorted(mem)}")

# ------------------------------------------------- full-run pair stats
from collections import Counter
pair = Counter()
bsz = Counter()
for (_, _, mem) in trace:
    bsz[len(mem)] += 1
    ms = sorted(mem)
    for i in range(len(ms)):
        for j in range(i + 1, len(ms)):
            pair[(ms[i], ms[j])] += 1
print(f"\n整个 60s ({len(trace)} 步) 的批大小分布:")
tot = sum(bsz.values())
for k in sorted(bsz):
    print(f"  {k} 路同批: {bsz[k]:5d} 步 ({100*bsz[k]/tot:.1f}%)")

def gap(a, b):
    d = abs(phases[a] - phases[b]) % BEAT_MS
    return min(d, BEAT_MS - d)

print("\n共批次数最多的前 12 对 (相位差 mod 480):")
for (a, b), n in pair.most_common(12):
    print(f"  s{a:<2}+s{b:<2}: {n:4d} 步   相位差 {gap(a, b):6.1f}ms")
never = [(a, b) for i, a in enumerate(order) for b in order[i+1:]
         if (min(a,b), max(a,b)) not in pair]
print(f"\n从未共批的会话对: {len(never)}/{N*(N-1)//2} 对")
