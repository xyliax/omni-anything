#!/usr/bin/env python3
"""Cascade in execution-lane form (600s sched-trace run): three windows — healthy full house,
the instant of eviction #1 (a lane goes dark mid-run), and the late survivor phase with visibly
wider (slower) steps. Cell edges = real scheduler step timestamps from inside EngineCore.
Output: results/figures/E1_cascade_lanes.{png,pdf}"""
import re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

BLUE, ORANGE, CRIT = "#2a78d6", "#eb6834", "#d03b3b"
INK, SEC, MUT, GRID, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"

steps = []
for ln in open("results/paper/baseline/e1schtr_n8_d600_sched.log"):
    parts = ln.split(); t = float(parts[0]); d = {}
    for p in parts[1:]:
        rid, ntok = p.rsplit(":", 1)
        enc = ntok.endswith("E"); n = int(ntok[:-1] if enc else ntok)
        sid = int(re.match(r"s(\d+)e", rid).group(1))
        if sid != 10**9: d[sid] = (n, enc)
    if d: steps.append((t, d))
T0 = steps[0][0]
EV1 = 216.2   # sid3's last scheduled step (eviction #1 boundary, from analysis)

# TRUE tick boundaries: gateway P events (perf clock), anchored onto the sched axis by the
# physical invariant min(prefill_start - preceding_tick) = +3ms (same method as the viewer).
_pts = []; _p0 = None
for _ln in open("results/paper/baseline/e1schtr_n8_d600_perreq.log"):
    _k, _t, _sid, *_ = _ln.split()
    if _k == "P" and int(_sid) != 10**9:
        _t = float(_t)
        if _p0 is None: _p0 = _t
        _pts.append(_t - _p0)
_pts = sorted(set(round(x, 3) for x in _pts))
_pf = [t - T0 for t, d in steps if any(n >= 40 for n, _ in d.values())]
import bisect as _bi
_ds = []
for _s in _pf:
    _i = _bi.bisect_right(_pts, _s) - 1
    for _j in range(max(0, _i-1), min(_i+2, len(_pts))):
        _d = _s - _pts[_j]
        if -1.0 < _d < 1.0: _ds.append(_d)
TICKS = [round(x + min(_ds) - 0.003, 3) for x in _pts]

def draw(ax, lo, hi):
    ax.set_facecolor(SURF)
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUT, labelsize=8)
    seq = [(t, d) for t, d in steps if lo <= t - T0 <= hi]
    for i, (t, d) in enumerate(seq):
        t1 = seq[i+1][0] if i+1 < len(seq) else t + 0.021
        if t1 - t > 0.5: t1 = t + 0.021
        for sid, (n, enc) in d.items():
            ax.add_patch(Rectangle((t - T0 - lo, 8 - sid + 1 - 0.36), t1 - t, 0.72,
                                   facecolor=ORANGE if n >= 40 else BLUE,
                                   edgecolor=SURF, lw=0.15, zorder=3))
    ax.set_yticks(range(1, 9), [f"sid {s}" for s in range(8, 0, -1)], fontsize=8)
    ax.set_ylim(0.4, 8.8); ax.set_xlim(0, hi - lo)
    ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)
    ax.set_xlabel(f"seconds from t={lo:.0f}s · dotted = TRUE gateway tick boundaries (audio arrival)",
                  fontsize=8, color=SEC)
    for tk in TICKS:
        if lo <= tk <= hi:
            ax.axvline(tk - lo, color=MUT, lw=0.9, ls=(0, (1, 2.5)), zorder=2)

fig, axes = plt.subplots(3, 1, figsize=(11, 8.8),
                         gridspec_kw=dict(hspace=0.62))
fig.patch.set_facecolor(SURF)

draw(axes[0], 150, 158)
axes[0].set_title("t=150–158 s · healthy full house: 8 lanes tile every tick (orange = chunk prefill+encoder, blue = decode steps)",
                  fontsize=9, color=INK, loc="left", pad=8)

draw(axes[1], 210, 224)
axes[1].axvline(EV1 - 210, color=CRIT, lw=1.2, ls=(0, (4, 3)))
axes[1].annotate("eviction #1 (pool hit 100%):\nsid 3's lane goes dark mid-run — KV freed,\nreadmission ticket > free pool forever after",
                 (EV1 - 210 + 0.25, 6.9), fontsize=8, color=CRIT,
                 bbox=dict(facecolor=SURF, alpha=0.9, lw=0, pad=1.5))
axes[1].set_title("t=210–224 s · the first eviction, caught in lanes: deterministic WHEN (216.8±0.4 s across runs), arbitrary WHO (run 1 killed sid 7 here)",
                  fontsize=9, color=INK, loc="left", pad=8)

draw(axes[2], 580, 596)
axes[2].set_title("t=580–596 s · endgame after eviction #6 (sid 6 died at 577 s): two lanes left (sid 2, sid 4), steps visibly wider —\n"
                  "23.7→26.2 ms as 25k-token contexts make each step's KV read costlier", fontsize=9, color=INK, loc="left", pad=8)

axes[0].legend(handles=[Line2D([], [], color=ORANGE, lw=6, label="chunk prefill + encoder"),
                        Line2D([], [], color=BLUE, lw=6, label="decode (1 token/step)")],
               loc="upper left", bbox_to_anchor=(0.72, 1.42), ncols=2, fontsize=7.5,
               frameon=False, labelcolor=SEC)
fig.suptitle("The eviction cascade in execution lanes — scheduler-trace replay of the full 600 s parallel-ingest run (repeat 2/5: eviction clock reproduced to ±0.4 s)",
             fontsize=10.5, color=INK, x=0.06, ha="left", y=0.995)
for ext in ("png", "pdf"):
    fig.savefig(f"results/figures/E1_cascade_lanes.{ext}", dpi=200, bbox_inches="tight", facecolor=SURF)
print("wrote results/figures/E1_cascade_lanes.png/pdf")
