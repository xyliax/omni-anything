"""Fig (for Sec 5.2): same memory horizon, three policies at N=96 over 300 s. Unbounded resident KV
hits the wall; the application-level recycle proxy stays safe but pays a growing re-encode toll
(p50 climbing to ~14-17 ms, p90 to 36 ms); the in-engine window stays at a flat few ms with no
re-encode. Data: results/long_duration_memory_wall.txt + results/inengine_swa_long.txt."""
import re
import numpy as np
from nstyle import apply, VAN, WIN, AMBER, DARK
import matplotlib.pyplot as plt

LINE = re.compile(r"^\s*(\d+)-(\d+)s\s+\d+\s+(\d+)ms\s+(\d+)ms")

def buckets(path, start_marker, stop_marker="OVERALL"):
    t, p50 = [], []
    active = start_marker is None
    for line in open(path):
        if start_marker and start_marker in line:
            active = True; continue
        if active and stop_marker in line:
            break
        m = LINE.match(line)
        if active and m:
            t.append((int(m.group(1)) + int(m.group(2))) / 2)
            p50.append(int(m.group(3)))
    return np.array(t), np.array(p50)

vt, vp = buckets("../../results/long_duration_memory_wall.txt", "[VANILLA unbounded]")
pt, pp = buckets("../../results/long_duration_memory_wall.txt", "[WINDOWED-KV")
it, ip = buckets("../../results/inengine_swa_long.txt", None)

apply()
fig, ax = plt.subplots(figsize=(4.6, 2.7))

BUDGET = 2000.0
ax.axhline(BUDGET, color="0.4", ls=":", lw=1.1)
ax.text(295, BUDGET * 1.16, "2 s frame budget", color="0.35", fontsize=7.2, ha="right", va="bottom")

ax.plot(vt, np.maximum(vp, 0.8), color=VAN, lw=2.0, label="unbounded KV (vLLM-realtime)")
ax.plot(pt, np.maximum(pp, 0.8), color=AMBER, lw=2.0, label="app-level recycle (re-encodes)")
ax.plot(it, np.maximum(ip, 0.8), color=WIN, lw=2.0, label="in-engine window (Metronome)")

ax.annotate("re-encode toll grows", xy=(212, 10), xytext=(135, 55),
            color=AMBER, fontsize=7.4, ha="center",
            arrowprops=dict(arrowstyle="->", color=AMBER, lw=1.0))
ax.text(160, 1.35, "no re-encode: flat", color=WIN, fontsize=7.4, ha="center")

ax.set_yscale("log"); ax.set_xlim(0, 300); ax.set_ylim(0.8, 5000)
ax.set_xlabel("elapsed session time (s), $N{=}96$")
ax.set_ylabel("per-frame $p_{50}$ (ms)")
ax.legend(fontsize=7.0, loc="upper left", framealpha=0.95)

fig.savefig("reencode.pdf")
fig.savefig("reencode.png", dpi=140)
print(f"wrote reencode.pdf  (vanilla end={vp[-1]}ms, proxy end={pp[-1]}ms, in-engine end={ip[-1]}ms)")
