"""Timeline of the orchestration-failure fingerprint: a long-tail tool
injection causing misses while the GPU sits idle moments before and after.

Scenario: N=8, realistic length mixture (trace_lmix), naive whole splice.
Renders the window around the largest injection of the run: an ENGINE row
(idle vs busy vs tool-prefill) plus one row per session.
"""
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from calib_model import load_default
from engine import Engine, Policy, BEAT_MS
from trace_lmix import MixEngine, MIX_TAIL

cal = load_default(Path(__file__).parent.parent / "calibration" / "data",
                   "Qwen3-1.7B")

steps = []
orig_admit, orig_step = Engine._admit, Engine._one_step

def admit(self, force_idle=False):
    dec, pre, dt_, pt_ = orig_admit(self, force_idle)
    self._tm = ({q.sid for q in dec} | {q.sid for q, _ in pre},
                any(q.is_tool for q, _ in pre))
    return dec, pre, dt_, pt_

def one_step(self, force_idle=False):
    t0 = self.now
    if orig_step(self, force_idle):
        mem, tool = self._tm
        steps.append((t0, self.now - t0, mem, tool))
        return True
    return False

Engine._admit, Engine._one_step = admit, one_step

N, SEED = 8, 1
e = MixEngine(cal, n_sessions=N, seed=SEED, sim_ms=60000, tool_rate_per_min=6.0,
              tool_L=1024, policy=Policy.WHOLE, lmix=MIX_TAIL,
              kv_pool_tokens=44336, track_beats=True)
phases = {s.sid: s.phase_ms for s in e.sessions.values()}
r = e.run()

big = max(e.tools.values(), key=lambda t: t.L if t.splice_start_ms >= 0 else 0)
W0 = (int(big.splice_start_ms // BEAT_MS) - 2) * BEAT_MS
W1 = W0 + 7 * BEAT_MS
COL = 20.0
ncol = int((W1 - W0) / COL)

print(f"util(全程)={r['utilisation']:.3f}  miss率={r['miss_rate']*100:.2f}%")
print(f"选中注入: s{big.sid} 的工具结果 L={big.L}, 进队@{big.splice_start_ms:.0f}ms, "
      f"KV算完@{big.splice_done_ms:.0f}ms")
win = [(t0, dt, m, tl) for (t0, dt, m, tl) in steps if t0 < W1 and t0 + dt > W0]
busy = sum(min(t1 := t0 + dt, W1) - max(t0, W0) for (t0, dt, _, _) in win)
print(f"窗口 {W0:.0f}-{W1:.0f}ms: 引擎忙 {busy:.0f}ms / {W1-W0:.0f}ms "
      f"(空闲 {100*(1-busy/(W1-W0)):.0f}%)\n")

hdr = "            " + "".join(
    str(int((W0 + c * COL) // 480) % 10) if (W0 + c * COL) % 480 < COL else " "
    for c in range(ncol))
print("时间轴: 每格 20ms, 数字行=拍编号; ENGINE 行: .=空转 #=工具prefill 数字=批内路数")
print(hdr)
row = ["."] * ncol
for (t0, dt, mem, tool) in win:
    ch = "#" if tool else str(min(9, len(mem)))
    for c in range(max(0, int((t0 - W0) / COL)),
                   min(int((t0 + dt - W0) / COL) + 1, ncol)):
        row[c] = ch
print("  ENGINE    " + "".join(row))

misses = {(b["sid"], round(b["arrival_ms"], 1)) for b in r["beat_log"] if b["miss"]}
for sid in sorted(phases, key=lambda s: phases[s]):
    row = ["."] * ncol
    for (t0, dt, mem, tool) in win:
        if sid not in mem:
            continue
        ch = "#" if tool else str(min(9, len(mem)))
        for c in range(max(0, int((t0 - W0) / COL)),
                       min(int((t0 + dt - W0) / COL) + 1, ncol)):
            row[c] = ch
    for k in range(-1, 9):
        arr = phases[sid] + (int(W0 // BEAT_MS) + k) * BEAT_MS
        if not (W0 <= arr < W1):
            continue
        c = int((arr - W0) / COL)
        mark = "!" if (sid, round(arr, 1)) in misses else "|"
        if row[c] == "." or mark == "!":
            row[c] = mark
    print(f"  s{sid:<2}({phases[sid]:>4.0f}) " + "".join(row))

print("\n窗口内 miss 明细:")
for m in r["miss_events"]:
    if W0 <= m["t"] <= W1 + 480:
        print(f"  t={m['t']:8.1f}ms s{m['sid']} 迟 {m['lateness_ms']:6.1f}ms "
              f"肇事={m['blamed_tool_sids']} 自己工具={m['own_tool_involved']}")
