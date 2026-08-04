#!/usr/bin/env python3
"""E1 deadlock anatomy figure: five time-aligned panels from the perreq instrumented run
(results/paper/baseline/e1perreq_n8_d600_*). Clocks are aligned onto ONE experiment axis
(t=0 = first real gateway tick): perreq events are native; kv.log offset is derived from
the warmup anchor; smi/client offsets are fixed small constants from the driver's sequencing.
Output: results/figures/E1_deadlock_anatomy.{png,pdf}
"""
import json, re, collections
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = "results/paper/baseline/e1perreq_n8_d600"
KB_PER_TOK = 57344 / 2**20          # MiB per token: 2*4 KV heads*128*2B*28 layers

# palette (dataviz reference, light mode, pairs validated)
BLUE, ORANGE = "#2a78d6", "#eb6834"      # cohorts (starve 255.6s / 271.6s)
AQUA, VIOLET = "#1baf7a", "#4a3aa7"      # run / wait
GREEN, CRIT  = "#008300", "#d03b3b"      # SM util / preemption+deadlock accents
INK, SEC, MUT, GRID = "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
SURF, WARN = "#fcfcfb", "#fab219"

# ---- parse perreq events ----
P = collections.defaultdict(list); T = collections.defaultdict(list)
warm_P = None
for ln in open(f"{BASE}_perreq.log"):
    k, t, sid, *rest = ln.split()
    t, sid = float(t), int(sid)
    if sid == 10**9:
        if k == "P" and warm_P is None: warm_P = t
        continue
    if k == "P": P[sid].append(t)
    elif k == "T": T[sid].append((t, int(rest[0]), int(rest[1])))
T0 = min(v[0] for v in P.values())               # experiment t=0

# ---- kv.log, offset anchored on the warmup session (statlog t0 = warmup start - first line t) ----
kv_rows = []
for ln in open(f"{BASE}_kv.log"):
    m = re.match(r"([\d.]+) kv=([\d.]+) run=(\d+) wait=(\d+) evict=\d+ pre=(\d+)", ln)
    if m: kv_rows.append(tuple(float(x) for x in m.groups()))
kv_off = T0 - (warm_P - kv_rows[0][0])
kvt  = [r[0] - kv_off for r in kv_rows]
kv   = [r[1] for r in kv_rows]
run  = [r[2] for r in kv_rows]
wait = [r[3] for r in kv_rows]
pre_t = next(r[0] - kv_off for r in kv_rows if r[4] > 0)     # first sample with pre=1

# ---- client events & smi ----
ev = json.load(open(f"{BASE}.json"))["ev"]
ev0 = min(e[0] for e in ev)
lat_t = [e[0] - ev0 for e in ev]; lat = [max(e[1], 0.5) for e in ev]
smi = [int(ln.split()[0]) for ln in open(f"{BASE}_smi.log") if "%" in ln]
smi_t = [5*i - 2.5 for i in range(len(smi))]

# ---- session cohorts by starve time (last ntok growth) ----
def starve(sid):
    ts = T[sid]; last = ts[0][0]
    for a, b in zip(ts, ts[1:]):
        if b[1] > a[1]: last = b[0]
    return last - T0
cohA = [s for s in P if starve(s) < 260]         # 255.6s group
cohB = [s for s in P if starve(s) >= 260]        # 271.6s group
tA = max(starve(s) for s in cohA); tB = max(starve(s) for s in cohB)

# ---- figure ----
fig, axes = plt.subplots(5, 1, figsize=(10.5, 12.6), sharex=True,
                         gridspec_kw=dict(height_ratios=[3.2, 2.2, 1.6, 2.4, 1.6], hspace=0.34))
fig.patch.set_facecolor(SURF)
for ax in axes:
    ax.set_facecolor(SURF)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUT, labelsize=8.5)
    ax.grid(axis="y", color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    # phase bands: collapse window (warning wash), deadlock (gray wash)
    ax.axvspan(tA, tB, color=WARN, alpha=0.10, lw=0)
    ax.axvspan(tB, 620, color="#f0efec", alpha=0.55, lw=0)
    ax.axvline(pre_t, color=CRIT, lw=1.0, ls=(0, (4, 3)), alpha=0.85)
    ax.set_xlim(-8, 620)

axes[0].set_title("Anatomy of the memory-wall deadlock — vanilla vLLM-realtime, N=8, Qwen2.5-Omni-7B, RTX 3090 (24 GB), 2 s tick",
                  fontsize=10.5, color=INK, loc="left", pad=32)
# phase captions above panel 1
for x, s, c in ((tA/2, "healthy: pipeline saturated, latency 1 ms", SEC),
                ((tA+tB)/2, "collapse\n(16 s)", "#8a6d00"),
                ((tB+600)/2, "deadlock: run=0, wait=8 — permanent", SEC)):
    axes[0].annotate(s, (x, 1.02), xycoords=("data", "axes fraction"),
                     ha="center", va="bottom", fontsize=8, color=c)

# P1: per-session resident context
ax = axes[0]
for sid in sorted(P):
    ts = T[sid]
    xs = [t - T0 for t, _, _ in ts]; ys = [(a + b) * KB_PER_TOK for _, a, b in ts]
    c = BLUE if sid in cohA else ORANGE
    ax.plot(xs, ys, color=c, lw=1.6)
    ax.plot([xs[-1], 600], [ys[-1], ys[-1]], color=c, lw=1.2, ls=(0, (2, 3)), alpha=0.8)
    ax.plot([xs[-1]], [ys[-1]], "o", ms=4.5, color=c, mec=SURF, mew=0.8)
ax.set_ylabel("resident KV per session (MiB)", fontsize=8.5, color=SEC)
ax.set_ylim(0, 640)
ax.annotate("+53 audio +≈25 gen tok / tick  ≈ 2.2 MB/s", (95, 330), fontsize=8, color=SEC, rotation=30)
ax.annotate("5 sessions starve at 255.6 s", (258, 405), fontsize=8, color=BLUE, ha="left")
ax.annotate("3 sessions at 271.6 s", (285, 560), fontsize=8, color=ORANGE, ha="left")
ax.annotate("dashed: KV stays resident — never evicted, never served again",
            (430, 455), fontsize=7.5, color=MUT, ha="center")
ax.annotate("single preemption (pre 0→1):\nvictim's KV freed, requeued at queue HEAD",
            (pre_t + 8, 120), fontsize=7.5, color=CRIT, ha="left")
from matplotlib.lines import Line2D
ax.legend(handles=[Line2D([], [], color=BLUE, lw=1.6, label="sessions 4–8 (starve 255.6 s)"),
                   Line2D([], [], color=ORANGE, lw=1.6, label="sessions 1–3 (starve 271.6 s)")],
          loc="upper left", fontsize=7.5, frameon=False, labelcolor=SEC, handlelength=1.6)

# P2: pool occupancy
ax = axes[1]
ax.fill_between(kvt, kv, color=GRID, alpha=0.5, lw=0)
ax.plot(kvt, kv, color=INK, lw=1.6)
ax.set_ylabel("KV block pool used", fontsize=8.5, color=SEC)
ax.set_ylim(0, 1.05); ax.set_yticks([0, .25, .5, .75, 1.0])
ax.axhline(1.0, color=MUT, lw=0.8, ls=(0, (1, 2)))
ax.annotate("peak 95.1%", (max(0, pre_t - 68), 0.99), fontsize=8, color=INK)
ax.annotate("frozen at 88.4% — 8.6k tokens free < victim's 9.7k-token readmission ticket",
            (pre_t + 12, 0.70), fontsize=8, color=SEC)

# P3: run / wait
ax = axes[2]
ax.step(kvt, run, where="post", color=AQUA, lw=1.6)
ax.step(kvt, wait, where="post", color=VIOLET, lw=1.6)
ax.set_ylabel("requests", fontsize=8.5, color=SEC)
ax.set_ylim(-0.4, 9); ax.set_yticks([0, 4, 8])
from matplotlib.lines import Line2D as _L2
ax.legend(handles=[_L2([], [], color=AQUA, lw=1.6, label="running"),
                   _L2([], [], color=VIOLET, lw=1.6, label="waiting (blocked on KV allocation)")],
          loc="center left", fontsize=8, frameon=False, labelcolor=SEC, handlelength=1.6)

# P4: client per-tick latency
ax = axes[3]
ax.scatter(lat_t, lat, s=3, color=MUT, alpha=0.35, lw=0)
ax.set_yscale("log"); ax.set_ylim(0.4, 4000)
ax.set_ylabel("client tick latency (ms)", fontsize=8.5, color=SEC)
ax.axhline(2000, color=INK, lw=0.9, ls=(0, (4, 3)))
ax.axhline(1600, color=CRIT, lw=0.9, ls=(0, (4, 3)))
ax.annotate("2000 ms deadline — never crossed: miss counter reads 0% throughout", (12, 2400), fontsize=8, color=INK)
ax.annotate("1600 ms = worker wait-budget cap (empty frames returned on time)", (12, 850), fontsize=8, color=CRIT)
ax.annotate("≈1 ms: tokens pre-buffered between ticks", (12, 2.2), fontsize=8, color=SEC)

# P5: SM util
ax = axes[4]
ax.plot(smi_t, smi, color=GREEN, lw=1.4)
ax.set_ylabel("GPU SM util (%)", fontsize=8.5, color=SEC)
ax.set_ylim(-4, 108); ax.set_yticks([0, 50, 100])
ax.set_xlabel("experiment time (s)", fontsize=9, color=SEC)
ax.annotate("79–100% busy: compute keeps pace to the last tick", (30, 40), fontsize=8, color="#005c00")
ax.annotate("0%: whole GPU idle — memory accounting, not compute, killed it", (300, 40), fontsize=8, color=SEC)

fig.align_ylabels(axes)
for ext in ("png", "pdf"):
    fig.savefig(f"results/figures/E1_deadlock_anatomy.{ext}", dpi=200, bbox_inches="tight",
                facecolor=SURF)
print("wrote results/figures/E1_deadlock_anatomy.{png,pdf}",
      f"cohorts A={sorted(cohA)} B={sorted(cohB)} tA={tA:.1f} tB={tB:.1f} pre_t={pre_t:.1f}")
