"""Timeline of collateral misses: injection chunks monopolise the per-step
prefill budget, starving whole cohorts' 8-token wakes, and the lateness
cascades into the next period.

Scenario: N=64, aligned, chunked, budget=320, short-only injection mixture.
Rows: ENGINE (what each step carries), WAITQ (how many beats' wakes are
starved), then selected sessions (tool owners + victims).
"""
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from calib_model import load_default
from engine import Engine, Policy, BEAT_MS
from trace_lmix import MixEngine, MIX_SHORT

cal = load_default(Path(__file__).parent.parent / "calibration" / "data",
                   "Qwen3-1.7B")

steps, firstpre, waitq = [], {}, []
orig_admit, orig_step = Engine._admit, Engine._one_step

def admit(self, force_idle=False):
    dec, pre, dt_, pt_ = orig_admit(self, force_idle)
    for q, _n in pre:
        if q.kind == "beat":
            firstpre.setdefault((q.sid, round(q.arrival_ms, 1)), self.now)
    starved = sum(1 for q in self.waiting
                  if q.kind == "beat" and q.prefill_done == 0)
    self._info = (
        sum(n for q, n in pre if q.is_tool),
        sum(n for q, n in pre if not q.is_tool),
        {q.sid for q in dec} | {q.sid for q, _ in pre},
        starved)
    return dec, pre, dt_, pt_

def one_step(self, force_idle=False):
    t0 = self.now
    if orig_step(self, force_idle):
        tool, wake, mem, starved = self._info
        steps.append((t0, self.now - t0, tool, wake, mem))
        waitq.append((t0, starved))
        return True
    return False

Engine._admit, Engine._one_step = admit, one_step
e = MixEngine(cal, n_sessions=64, seed=1, sim_ms=60000, tool_rate_per_min=6.0,
              tool_L=1024, policy=Policy.CHUNKED, lmix=MIX_SHORT,
              kv_pool_tokens=44336, phase="aligned", max_batched_tokens=320,
              track_beats=True)
r = e.run()

per_period = defaultdict(set)
for b in r["beat_log"]:
    if b["miss"]:
        per_period[int(b["arrival_ms"] // BEAT_MS)].add(b["sid"])
k = min(p for p, s in per_period.items() if len(s) >= 30 and p >= 2)
W0, W1, COL = (k - 1) * BEAT_MS, (k + 2) * BEAT_MS, 10.0
ncol = int((W1 - W0) / COL)
print(f"选中周期 {k}(@{k*480}ms): 该周期 {len(per_period[k])}/64 路 miss; "
      f"下一周期 {len(per_period.get(k+1, set()))}/64 路 miss")
tools_win = [t for t in e.tools.values()
             if t.splice_start_ms < W1 and (t.splice_done_ms < 0 or t.splice_done_ms > W0)]
print("窗口内在吸收的注入: " + ", ".join(
    f"s{t.sid}(L={t.L},{t.splice_start_ms:.0f}→{t.splice_done_ms:.0f}ms)"
    for t in sorted(tools_win, key=lambda t: t.splice_start_ms)))

def enc(n):
    return "." if n == 0 else (str(n) if n <= 9 else chr(ord('a') + min(25, n - 10)))

hdr = "             " + "".join(
    f"{'拍'+str(int((W0+c*COL)//480)):<24}" if (W0 + c * COL) % 480 < COL else ""
    for c in range(ncol))
print("\n每格10ms | ENGINE: #=运注入chunk的步 w=运唤醒的步 d=纯decode .=空转")
print("         | WAITQ: 唤醒被饿在门外的拍数(0-9,a-z) | 会话行: |=唤醒排队 数字=同批路数 !=miss")
print(hdr[:13 + ncol])
row_e, row_q = ["."] * ncol, ["."] * ncol
for (t0, dt, tool, wake, mem) in steps:
    if t0 >= W1 or t0 + dt <= W0:
        continue
    ch = "#" if tool else ("w" if wake else "d")
    for c in range(max(0, int((t0 - W0) / COL)), min(int((t0 + dt - W0) / COL) + 1, ncol)):
        row_e[c] = ch
for (t0, n) in waitq:
    if W0 <= t0 < W1:
        c = int((t0 - W0) / COL)
        row_q[c] = max(row_q[c], enc(n), key=lambda x: 0 if x == "." else (int(x, 36)))
print("  ENGINE     " + "".join(row_e))
print("  WAITQ      " + "".join(row_q))

owners = [t.sid for t in tools_win][:2]
victims = [s for s in per_period[k] if s in per_period.get(k + 1, set())
           and s not in owners][:3]
clean = [s for s in range(64) if s not in per_period[k]][:1]
misses = {(b["sid"], round(b["arrival_ms"], 1)) for b in r["beat_log"] if b["miss"]}
for sid in owners + victims + clean:
    tag = ("注入者" if sid in owners else ("幸存" if sid in clean else "受害"))
    row = ["."] * ncol
    for (t0, dt, tool, wake, mem) in steps:
        if sid not in mem or t0 >= W1 or t0 + dt <= W0:
            continue
        for c in range(max(0, int((t0 - W0) / COL)), min(int((t0 + dt - W0) / COL) + 1, ncol)):
            row[c] = str(min(9, len(mem))) if len(mem) <= 9 else "+"
    for kk in range(int(W0 // BEAT_MS), int(W1 // BEAT_MS) + 1):
        arr = kk * BEAT_MS
        if not (W0 <= arr < W1):
            continue
        fp = firstpre.get((sid, round(arr, 1)))
        c0 = int((arr - W0) / COL)
        c1 = int((min(fp, W1) - W0) / COL) if fp else ncol
        for c in range(c0, min(c1, ncol)):
            if row[c] == ".":
                row[c] = "|"
        mark = "!" if (sid, round(arr, 1)) in misses else None
        if mark:
            row[c0] = "!"
    print(f"  s{sid:<2}({tag}) " + "".join(row))
