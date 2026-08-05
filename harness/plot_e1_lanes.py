#!/usr/bin/env python3
"""Nsight-style per-request execution lanes from the scheduler trace (e1schtr run):
each engine step is a cell on its session's lane — orange = that session's 2s-audio
chunk prefill (encoder co-scheduled in the same step, marked E), blue = one decode
token. Cell edges are real step timestamps from inside the EngineCore scheduler.
Top: one tick fully resolved. Bottom: three consecutive ticks for context.
Output: results/figures/E1_exec_lanes.{png,pdf}"""
import re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, SEC, MUT, GRID, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"

steps = []
for ln in open("results/paper/baseline/e1schtr_n8_d60_sched.log"):
    parts = ln.split()
    t = float(parts[0]); d = {}
    for p in parts[1:]:
        rid, ntok = p.rsplit(":", 1)
        enc = ntok.endswith("E"); ntok = int(ntok[:-1] if enc else ntok)
        sid = int(re.match(r"s(\d+)e", rid).group(1))
        if sid == 10**9: continue
        d[sid] = (ntok, enc)
    if d: steps.append((t, d))
T0 = steps[0][0]

ticks = []; cur = [steps[0]]
for a, b in zip(steps, steps[1:]):
    if b[0] - a[0] > 0.5: ticks.append(cur); cur = [b]
    else: cur.append(b)
ticks.append(cur)
steady = [tk for tk in ticks if tk[0][0] - T0 > 20 and len(tk) > 5]
tk = steady[len(steady) // 2]                       # the zoom tick
i0 = ticks.index(tk)
ctx3 = [s for t in ticks[i0:i0+3] for s in t]       # three ticks

def draw(ax, seq, lo, hi, lw_edge=0.4):
    ax.set_facecolor(SURF)
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUT, labelsize=8.5)
    for i, (t, d) in enumerate(seq):
        t1 = seq[i+1][0] if i+1 < len(seq) else t + 0.021
        if t1 - t > 0.5: t1 = t + 0.021           # inter-tick gap: cap cell at one step
        for sid, (n, enc) in d.items():
            y = 8 - sid + 1
            ax.add_patch(Rectangle(((t-lo)*1000, y-0.36), (t1-t)*1000, 0.72,
                                   facecolor=ORANGE if n >= 40 else BLUE,
                                   edgecolor=SURF, lw=lw_edge, zorder=3))
    ax.set_yticks(range(1, 9), [f"sid {s}" for s in range(8, 0, -1)], fontsize=8.5)
    ax.set_ylim(0.4, 8.8); ax.set_xlim(0, (hi-lo)*1000)
    ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6.6),
                               gridspec_kw=dict(height_ratios=[1.15, 1], hspace=0.5))
fig.patch.set_facecolor(SURF)

lo, hi = tk[0][0], tk[-1][0] + 0.03
draw(ax1, tk, lo, hi)
ax1.set_xlabel("ms from first scheduled step of the tick", fontsize=8.5, color=SEC)
ax1.set_title("One tick fully resolved (cell = one engine step for that session; edges = real scheduler timestamps)\n"
              "orange = 53-token chunk prefill, encoder co-scheduled in the SAME step (152/152 in 20 ticks) · blue = one decode token",
              fontsize=8.8, color=INK, loc="left", pad=8)
_bb = dict(facecolor=SURF, alpha=0.88, lw=0, pad=1.5)
ax1.annotate("8 prefills land in 3–4 steps over ~110 ms:\nstagger = ingest-thread completion jitter, not engine queueing",
             (245, 7.55), fontsize=7.5, color="#a34317", bbox=_bb)
ax1.annotate("session decodes as soon as ITS OWN prefill is done (no cross-session barrier)",
             (245, 2.05), fontsize=7.5, color="#1c5cab", bbox=_bb)
ax1.annotate("batch-8 decode, 21 ms/step ×~34", (480, 5.35), fontsize=7.5, color="#1c5cab", bbox=_bb)
ax1.annotate("quota exhausted:\nbatch thins 8→0", ((tk[-1][0]-lo)*1000 - 60, 3.0), fontsize=7.5, color=SEC, ha="center", bbox=_bb)

lo2, hi2 = ctx3[0][0], ctx3[-1][0] + 0.03
draw(ax2, ctx3, lo2, hi2, lw_edge=0.15)
ax2.set_xlabel("ms (three consecutive ticks)", fontsize=8.5, color=SEC)
ax2.set_title("Three ticks: ~870 ms busy / ~1130 ms idle per 2 s tick — the idle stripe is the conveyor's transfer window",
              fontsize=8.8, color=INK, loc="left", pad=8)

ax1.legend(handles=[Line2D([], [], color=ORANGE, lw=6, label="chunk prefill + encoder (same step)"),
                    Line2D([], [], color=BLUE, lw=6, label="decode (1 token/step)")],
           loc="upper left", bbox_to_anchor=(0.0, -0.18), ncols=2, fontsize=7.5,
           frameon=False, labelcolor=SEC)
fig.suptitle("Per-request execution lanes inside the engine — scheduler-trace replay, vanilla vLLM-realtime + parallel ingest, N=8",
             fontsize=10.5, color=INK, x=0.06, ha="left", y=1.005)
for ext in ("png", "pdf"):
    fig.savefig(f"results/figures/E1_exec_lanes.{ext}", dpi=200, bbox_inches="tight", facecolor=SURF)
print("wrote results/figures/E1_exec_lanes.png/pdf; zoom tick at", f"{tk[0][0]-T0:.1f}s")
