"""Part 1: step-type breakdown of the S2 N=12 trace (micro-prefill vs decode).
Part 2: same 12 sessions, but with one L=8192 tool result returning at t=1000ms
        (policy = whole splice, current semantics) -- the "real scenario" view.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from calib_model import load_default
from engine import Engine, BEAT_MS

cal = load_default(Path(__file__).parent.parent / "calibration" / "data",
                   "Qwen3-1.7B")

def instrument():
    trace = []
    orig_admit, orig_step = Engine._admit, Engine._one_step

    def admit(self, force_idle=False):
        dec, pre, dt_, pt_ = orig_admit(self, force_idle)
        self._tm = ({q.sid for q in dec} | {q.sid for q, _ in pre},
                    any(q.is_tool for q, _ in pre),
                    sum(n for _, n in pre))
        return dec, pre, dt_, pt_

    def one_step(self, force_idle=False):
        t0 = self.now
        if orig_step(self, force_idle):
            mem, tool, ptok = self._tm
            trace.append((t0, self.now - t0, mem, tool, ptok))
            return True
        return False

    Engine._admit, Engine._one_step = admit, one_step
    return trace

TRACE = instrument()

# ---------------------------------------------------------------- part 1
e = Engine(cal, n_sessions=12, seed=1, sim_ms=60000, tool_rate_per_min=0,
           phase="random")
rep = e.run()
pf_steps = [(dt) for (_, dt, _, _, p) in TRACE if p > 0]
dc_steps = [(dt) for (_, dt, _, _, p) in TRACE if p == 0]
busy = sum(dt for _, dt, *_ in TRACE)
print("== Part 1: S2 (无注入) 60s 的步型构成 ==")
print(f"  含 micro-prefill 的步: {len(pf_steps):5d} 步  平均 {sum(pf_steps)/len(pf_steps):5.1f}ms  "
      f"占忙时 {100*sum(pf_steps)/busy:.1f}%")
print(f"  纯 decode 的步:        {len(dc_steps):5d} 步  平均 {sum(dc_steps)/len(dc_steps):5.1f}ms  "
      f"占忙时 {100*sum(dc_steps)/busy:.1f}%")

# ---------------------------------------------------------------- part 2
TRACE.clear()
SIM = 6000
e2 = Engine(cal, n_sessions=12, seed=1, sim_ms=SIM, tool_rate_per_min=0,
            phase="random", track_beats=True,
            fixed_tools=[(999.0, 3, 8192, 1.0)])   # returns at t=1000ms to s3
phases = {s.sid: s.phase_ms for s in e2.sessions.values()}
rep2 = e2.run()

W0, W1, COL = 480.0, 2880.0, 20.0
ncol = int((W1 - W0) / COL)
print(f"\n== Part 2: 同样 12 路 + s3 的一次 L=8192 工具返回 @1000ms (整段拼回) ==")
print(f"miss 总数 {rep2['total_misses']} / {rep2['total_beats']} 拍, "
      f"跨会话 miss {rep2['cross_session_misses']}")
print(f"时间轴 {W0:.0f}..{W1:.0f}ms, 每格 {COL:.0f}ms; "
      "数字=同批路数, #=工具 prefill 步, |=到达在排队, !=该拍最终 miss")
hdr = " sid(phase) " + "".join(
    str(int((W0 + c * COL) // 100) % 10) if (W0 + c * COL) % 100 < COL else " "
    for c in range(ncol))
print(hdr)
misses = {(b["sid"], round(b["arrival_ms"], 1)) for b in rep2["beat_log"] if b["miss"]}
order = sorted(phases, key=lambda s: phases[s])
for sid in order:
    row = ["."] * ncol
    for (t0, dt, mem, tool, _p) in TRACE:
        if sid not in mem or t0 >= W1 or t0 + dt <= W0:
            continue
        ch = "#" if tool else str(min(9, len(mem)))
        for c in range(max(0, int((t0 - W0) / COL)),
                       min(int((t0 + dt - W0) / COL) + 1, ncol)):
            row[c] = ch
    for k in range(20):
        arr = phases[sid] + k * BEAT_MS
        if not (W0 <= arr < W1):
            continue
        c = int((arr - W0) / COL)
        mark = "!" if (sid, round(arr, 1)) in misses else "|"
        if row[c] == ".":
            row[c] = mark
        elif mark == "!":
            row[c] = "!"
    print(f" s{sid:<2}({phases[sid]:>5.0f}) " + "".join(row))

print("\n工具 prefill 步:")
for (t0, dt, mem, tool, p) in TRACE:
    if tool:
        print(f"  t={t0:7.1f}ms dt={dt:6.1f}ms  prefill_tok={p}  members={sorted(mem)}")
print("\nmiss 明细 (前 14 条):")
for m in rep2["miss_events"][:14]:
    print(f"  t={m['t']:7.1f}ms s{m['sid']} beat{m['beat']} 迟 {m['lateness_ms']:6.1f}ms "
          f"肇事={m['blamed_tool_sids']} 自己的工具={m['own_tool_involved']}")
