"""Engine-occupancy timeline at increasing density (memory assumed infinite:
KV overflow is recorded, never enforced). One row per N: each column 10ms,
character = number of sessions in the running step (1-9, then a=10..z=35,
'@'=36-71, '#'>=72), '.' = engine idle.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from calib_model import load_default
from engine import Engine

cal = load_default(Path(__file__).parent.parent / "calibration" / "data",
                   "Qwen3-1.7B")

def enc(n):
    if n <= 9:
        return str(n)
    if n <= 35:
        return chr(ord('a') + n - 10)
    return '@' if n <= 71 else '#'

steps = []
orig_admit, orig_step = Engine._admit, Engine._one_step

def admit(self, force_idle=False):
    dec, pre, dt_, pt_ = orig_admit(self, force_idle)
    self._nm = len({q.sid for q in dec} | {q.sid for q, _ in pre})
    return dec, pre, dt_, pt_

def one_step(self, force_idle=False):
    t0 = self.now
    if orig_step(self, force_idle):
        steps.append((t0, self.now - t0, self._nm))
        return True
    return False

Engine._admit, Engine._one_step = admit, one_step

WIN, COL = 1440.0, 10.0
ncol = int(WIN / COL)
print("引擎占用时序 (0-1440ms, 每格10ms): 字符=该步内会话数, '.'=空转")
print("         " + "".join(str(int(c*COL//100)%10) if (c*COL)%100 < COL else " "
                            for c in range(ncol)))
for phase, Ns in (("random", [12, 24, 48, 96, 192]), ("aligned", [96, 192])):
    for N in Ns:
        steps.clear()
        e = Engine(cal, n_sessions=N, seed=1, sim_ms=60000,
                   tool_rate_per_min=0, phase=phase)
        r = e.run()
        row = ["."] * ncol
        for (t0, dt, nm) in steps:
            if t0 >= WIN:
                break
            for c in range(int(t0/COL), min(int((t0+dt)/COL)+1, ncol)):
                row[c] = enc(nm)
        beats = r["total_beats"]
        gpu_per_beat = r["utilisation"] * 60000 / max(1, beats)
        print(f"{phase[:3]} N={N:>3} " + "".join(row))
        print(f"          util={r['utilisation']:.3f} avgB={r['avg_decode_B']:>6.2f} "
              f"steps={r['steps']:>5} beat_p50={r['beat_p50_ms']:>6.1f}ms "
              f"p99={r['beat_p99_ms']:>6.1f}ms miss={r['miss_rate']:.4f} "
              f"GPU-ms/拍={gpu_per_beat:.2f}")
