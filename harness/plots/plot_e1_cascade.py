#!/usr/bin/env python3
"""Survivor-takes-all cascade anatomy (parallel-ingest N=8 run): per-session KV with
eviction order, pool occupancy sawtooth, cumulative preemptions, SM util. Clocks aligned
via the warmup anchor. Output: results/figures/E1_cascade_anatomy.{png,pdf}"""
import re, collections
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

BASE = "results/paper/baseline/e1paringest_n8_d600"
KB = 57344 / 2**20
BLUE, ORANGE, CRIT = "#2a78d6", "#eb6834", "#d03b3b"
INK, SEC, MUT, GRID, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"
GREEN = "#008300"

P = collections.defaultdict(list); T = collections.defaultdict(list)
warm_P = None
for ln in open(f"{BASE}_perreq.log"):
    k, t, sid, *r = ln.split(); t, sid = float(t), int(sid)
    if sid == 10**9:
        if k == "P" and warm_P is None: warm_P = t
        continue
    if k == "P": P[sid].append(t)
    elif k == "T": T[sid].append((t, int(r[0]), int(r[1])))
T0 = min(v[0] for v in P.values())
rows = []
for ln in open(f"{BASE}_kv.log"):
    m = re.match(r"([\d.]+) kv=([\d.]+) run=(\d+) wait=(\d+) evict=\d+ pre=(\d+)", ln)
    if m: rows.append(tuple(float(x) for x in m.groups()))
off = T0 - (warm_P - rows[0][0])
kvt = [r[0] - off for r in rows]; kv = [r[1] for r in rows]; pre = [int(r[4]) for r in rows]
smi = [int(ln.split()[0]) for ln in open(f"{BASE}_smi.log") if "%" in ln]
smi_t = [5*i - 2.5 for i in range(len(smi))]

def starve(sid):
    ts = T[sid]; last = ts[0][0]
    for a, b in zip(ts, ts[1:]):
        if b[1] > a[1]: last = b[0]
    return last - T0
sv = {s: starve(s) for s in P}
victims = sorted((t, s) for s, t in sv.items() if t < 590)
survivors = [s for s, t in sv.items() if t >= 590]

fig, axes = plt.subplots(4, 1, figsize=(10.5, 10.2), sharex=True,
                         gridspec_kw=dict(height_ratios=[3.0, 2.2, 1.4, 1.4], hspace=0.36))
fig.patch.set_facecolor(SURF)
pre_times = [kvt[i] for i in range(1, len(pre)) if pre[i] > pre[i-1]]
for ax in axes:
    ax.set_facecolor(SURF)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUT, labelsize=8.5)
    ax.grid(axis="y", color=GRID, lw=0.7); ax.set_axisbelow(True)
    for pt in pre_times:
        ax.axvline(pt, color=CRIT, lw=0.9, ls=(0, (4, 3)), alpha=0.7)
    ax.set_xlim(-8, 620)

axes[0].set_title("Fix the ingest wall and the memory wall changes shape: survivor-takes-all eviction cascade\n"
                  "(parallel-ingest patch, otherwise identical vanilla stack — N=8, Qwen2.5-Omni-7B, RTX 3090, 2 s tick)",
                  fontsize=10.5, color=INK, loc="left", pad=10)

ax = axes[0]
for sid in sorted(P):
    ts = T[sid]
    xs = [t - T0 for t, _, _ in ts]; ys = [(a + b) * KB for _, a, b in ts]
    c = ORANGE if sid in survivors else BLUE
    ax.plot(xs, ys, color=c, lw=1.6)
    if sid not in survivors:
        i = min(range(len(xs)), key=lambda j: abs(xs[j] - sv[sid]))
        ax.plot([xs[i]], [ys[i]], "o", ms=5, color=CRIT, mec=SURF, mew=0.8, zorder=5)
ax.set_ylabel("resident KV per session (MiB)", fontsize=8.5, color=SEC)
ax.set_ylim(0, 1550)
for (t, s), y in zip(victims, (620, 700, 800, 930, 1120, 1420)):
    ax.annotate(f"#{victims.index((t,s))+1} sid{s}\n{t:.0f}s", (t, y), fontsize=7,
                color=CRIT, ha="center")
ax.legend(handles=[Line2D([], [], color=BLUE, lw=1.6, label="6 victims (evicted in order, KV freed, never readmitted)"),
                   Line2D([], [], color=ORANGE, lw=1.6, label="2 survivors (grow to end of run, 25.8k tok ≈ 1.4 GB each)"),
                   Line2D([], [], color=CRIT, marker="o", lw=0, label="eviction (preemption)")],
          loc="upper left", fontsize=7.5, frameon=False, labelcolor=SEC, handlelength=1.6)

ax = axes[1]
ax.fill_between(kvt, kv, color=GRID, alpha=0.5, lw=0)
ax.plot(kvt, kv, color=INK, lw=1.4)
ax.set_ylabel("KV pool used", fontsize=8.5, color=SEC)
ax.set_ylim(0, 1.06); ax.set_yticks([0, .5, 1.0])
ax.annotate("sawtooth: pool packs to 100%, one eviction frees a victim,\nsurvivors refill the space — interval stretches as 1/N_alive (30→41→58→87→144 s)",
            (250, 0.30), fontsize=8, color=SEC)

ax = axes[2]
ax.step(kvt, pre, where="post", color=CRIT, lw=1.6)
ax.set_ylabel("evictions (pre=)", fontsize=8.5, color=SEC)
ax.set_ylim(-0.3, 7); ax.set_yticks([0, 3, 6])

ax = axes[3]
ax.plot(smi_t, smi, color=GREEN, lw=0.9, alpha=0.55)
# phase-mean overlay: the readable signal under the burst/idle sampling alias
import numpy as _np
PH = [(30, 210, 8), (220, 285, 6.5), (290, 430, 4.5), (440, 575, 3), (578, 600, 2)]
for a, b, n in PH:
    seg = [u for t, u in zip(smi_t, smi) if a <= t <= b]
    m = sum(seg)/len(seg)
    ax.plot([a, b], [m, m], color="#005c00", lw=2.4)
    ax.annotate(f"{m:.0f}%", ((a+b)/2, m+7), fontsize=7.5, color="#005c00", ha="center")
ax.set_ylabel("GPU SM util (%)", fontsize=8.5, color=SEC)
ax.set_ylim(-4, 118); ax.set_yticks([0, 50, 100])
ax.set_xlabel("experiment time (s)", fontsize=9, color=SEC)
ax.annotate("phase means: fewer sessions but LONGER contexts — per-session cost grows ~6× (4.5%→25%/session)\n"
            "as ctx reaches 25k tok: the attention wall emerging inside the cascade (thin line aliases each tick's burst/idle)",
            (8, 100), fontsize=7.5, color=SEC, va="top")

fig.align_ylabels(axes)
for ext in ("png", "pdf"):
    fig.savefig(f"results/figures/E1_cascade_anatomy.{ext}", dpi=200, bbox_inches="tight", facecolor=SURF)
print("victims:", victims, "survivors:", survivors)
