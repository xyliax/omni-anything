"""Headline figure: at a fixed 128 concurrent sessions over a five-minute call, vanilla resident-KV
serving (what engines do today) FALLS OFF A CLIFF -- per-frame latency holds at a few ms and then jumps in
one step to the ~1.6 s frame-budget wall. Metronome's windowed KV stays flat the whole time. One bold line
per system, big annotations, log-y. Reads in two seconds."""
import json
import numpy as np
from nstyle import apply, VAN, WIN, DARK, LABEL_VAN, LABEL_WIN
import matplotlib.pyplot as plt

BUCKET, DUR, BUDGET = 5.0, 300.0, 2000.0
EDGES = np.arange(0, DUR + BUCKET, BUCKET)
CENT = (EDGES[:-1] + EDGES[1:]) / 2

def bucketed(path):
    ev = json.load(open(path))["ev"]
    el = np.array([e[0] for e in ev]); la = np.array([e[1] for e in ev])
    idx = np.digitize(el, EDGES) - 1
    out = np.full(len(CENT), np.nan)
    for b in range(len(CENT)):
        m = idx == b
        if m.any():
            out[b] = np.median(la[m])
    return np.maximum(out, 0.5)

van = bucketed("../../results/sustained_fd/pdiag128.json")
win = bucketed("../../results/sustained_fd/pdiag128_win.json")

apply()
fig, ax = plt.subplots(figsize=(6.6, 3.2))

# frame budget / deadline band (headroom above the band so the label never clips)
ax.axhspan(BUDGET, 6000, color=DARK, alpha=0.06)
ax.axhline(BUDGET, color=DARK, ls="--", lw=1.0)
ax.text(234, BUDGET * 1.16, "2 s frame deadline (miss it and the call stutters)",
        color=DARK, fontsize=7.5, va="bottom", ha="center")

ax.plot(CENT, van, color=VAN, lw=2.6, label=LABEL_VAN)
ax.plot(CENT, win, color=WIN, lw=2.6, label=LABEL_WIN)

# cliff annotation on the vanilla curve -- text sits in the empty mid-left band,
# well clear of the legend (upper left) and both curves
knee = next((CENT[i] for i in range(1, len(CENT)) if van[i] > 100 and np.isfinite(van[i])), 170)
ax.annotate("latency cliff:\nthe call freezes", xy=(knee - 2, 250), xytext=(110, 48),
            color=VAN, fontsize=9.5, fontweight="bold", ha="center", va="center",
            arrowprops=dict(arrowstyle="-|>", color=VAN, lw=1.6))
ax.text(255, 900, "frozen at the wall", color=VAN, fontsize=8.5, ha="center")
ax.annotate("flat, a few ms: stays on beat", xy=(245, win[-12]), xytext=(216, 32),
            color=WIN, fontsize=9.5, fontweight="bold", ha="center",
            arrowprops=dict(arrowstyle="-|>", color=WIN, lw=1.4))

ax.set_yscale("log"); ax.set_ylim(0.6, 6000); ax.set_xlim(0, 300)
ax.set_xlabel("elapsed time in a single call (s), at 128 concurrent sessions")
ax.set_ylabel("per-frame latency (ms)")
ax.legend(loc="upper left", bbox_to_anchor=(0.012, 0.99), fontsize=9, framealpha=0.97)

fig.savefig("headline.pdf")
fig.savefig("headline.png", dpi=140)
print(f"wrote headline.pdf  (vanilla end={van[-1]:.0f}ms, windowed end={win[-1]:.0f}ms, knee@{knee:.0f}s)")
