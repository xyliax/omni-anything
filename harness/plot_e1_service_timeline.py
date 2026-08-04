#!/usr/bin/env python3
"""Per-request service timeline (Gantt) from the perreq run: does vanilla serve sessions
in phase? Top: the requested 2-tick (4 s) zoom. Bottom: one full rotation (~18 s) for context.
Bar segments = inter-F intervals within a session's service visit (F = engine front-end accepts
that session's next 2 s chunk; each segment is one chunk's encoder+prefill+decode-quota service).
The trailing chunk of each visit gets an estimated median-length tail (lighter). P = gateway push,
identical for all sessions (one batched Step per tick) — drawn as global tick lines.
Output: results/figures/E1_service_timeline.{png,pdf}
"""
import collections, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

TAG = sys.argv[1] if len(sys.argv) > 1 else "e1perreq_n8_d600"
ZLO = float(sys.argv[2]) if len(sys.argv) > 2 else 200.0
WLO = float(sys.argv[3]) if len(sys.argv) > 3 else 198.0
WLEN = float(sys.argv[4]) if len(sys.argv) > 4 else 20.0
BASE = f"results/paper/baseline/{TAG}"
SLOT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
INK, SEC, MUT, GRID, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"

P = collections.defaultdict(list); F = collections.defaultdict(list)
for ln in open(f"{BASE}_perreq.log"):
    k, t, sid, *r = ln.split(); t, sid = float(t), int(sid)
    if sid == 10**9: continue
    if k == "P": P[sid].append(t)
    elif k == "F": F[sid].append(t)
T0 = min(v[0] for v in P.values())
ptimes = sorted({round(t - T0, 2) for v in P.values() for t in v})

# visits: consecutive F runs of one session with gaps < 1.0 s
GAP = 1.0
visits = collections.defaultdict(list)          # sid -> [(start, end_est, nchunks)]
med = []
for sid in sorted(F):
    fs = sorted(t - T0 for t in F[sid])
    med += [b - a for a, b in zip(fs, fs[1:]) if b - a < GAP]
med_dt = sorted(med)[len(med)//2] if med else 0.25
for sid in sorted(F):
    fs = sorted(t - T0 for t in F[sid])
    cur = [fs[0]]
    for a, b in zip(fs, fs[1:]):
        if b - a < GAP: cur.append(b)
        else: visits[sid].append(cur); cur = [b]
    visits[sid].append(cur)

def draw(ax, lo, hi, tick_label=True):
    ax.set_facecolor(SURF)
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUT, labelsize=8.5)
    for pt in ptimes:
        if lo - 0.5 <= pt <= hi + 0.5:
            ax.axvline(pt, color=MUT, lw=0.9, ls=(0, (1, 2)), zorder=1)
    for row, sid in enumerate(sorted(F)):
        y = 8 - row
        c = SLOT[sid - 1]
        ax.axhline(y, color=GRID, lw=0.6, zorder=0)
        for vs in visits[sid]:
            segs = list(zip(vs, vs[1:])) + [(vs[-1], vs[-1] + med_dt)]
            for i, (a, b) in enumerate(segs):
                if b < lo or a > hi: continue
                est = (i == len(segs) - 1)
                ax.add_patch(Rectangle((a, y - 0.30), b - a - 0.012, 0.60, zorder=3,
                                       facecolor=c, alpha=0.45 if est else 0.95, lw=0))
    ax.set_yticks(range(1, 9), [f"sid {s}" for s in range(8, 0, -1)], fontsize=8.5)
    ax.set_ylim(0.3, 8.9); ax.set_xlim(lo, hi)
    if tick_label: ax.set_xlabel("experiment time (s)", fontsize=9, color=SEC)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10.5, 6.4),
                               gridspec_kw=dict(height_ratios=[1, 1.15], hspace=0.42))
fig.patch.set_facecolor(SURF)

PAR = "paringest" in TAG
ZHI = ZLO + 4.1
draw(ax1, ZLO, ZHI, tick_label=False)
if PAR:
    ax1.set_title("2-tick (4 s) zoom — audio still arrives for all 8 sessions at the same instant (dotted = batched gateway push);\n"
                  "with parallel ingest each session's chunk is processed within its own tick (block ≈ one chunk's service)",
                  fontsize=8.8, color=INK, loc="left", pad=8)
else:
    ax1.set_title("Requested 2-tick (4 s) zoom — audio for ALL 8 sessions arrives at the same instant (dotted = batched gateway push);\n"
                  "the engine is inside ONE session's service burst at a time (each block ≈ one 2 s chunk: encoder + prefill 53 tok + decode quota)",
                  fontsize=8.8, color=INK, loc="left", pad=8)

WHI = WLO + WLEN
draw(ax2, WLO, WHI)
if PAR:
    ax2.set_title("Wider window: every session served every tick — no rotation, no backlog; ingest overlaps across sessions (thread pool)",
                  fontsize=8.8, color=INK, loc="left", pad=8)
else:
    ax2.set_title("One full rotation (~15 s): emergent round-robin — each session gets a ≈1.9 s solo burst draining ≈7 backlogged chunks,\n"
                  "then waits ≈13 s for its next turn. No designed time-phase anywhere: this schedule is emergent, uncontrolled, and 7× coarser than the tick",
                  fontsize=8.8, color=INK, loc="left", pad=8)
ax2.add_patch(Rectangle((ZLO, 0.35), ZHI - ZLO, 8.5, facecolor="none",
                        edgecolor=INK, lw=0.9, ls=(0, (3, 2)), zorder=5))
ax2.annotate("panel above", (ZLO + 0.15, 0.62), fontsize=7.5, color=SEC)

fig.suptitle(("Parallel ingest (thread-pool patch): " if PAR else "Who is the engine actually serving? — ")
             + f"per-session service timeline, vanilla vLLM-realtime, N=8, steady state (t≈{ZLO:.0f} s)",
             fontsize=10.5, color=INK, x=0.055, ha="left", y=1.00)
OUT = "E1_service_timeline" if TAG == "e1perreq_n8_d600" else f"{TAG}_service_timeline"
for ext in ("png", "pdf"):
    fig.savefig(f"results/figures/{OUT}.{ext}", dpi=200,
                bbox_inches="tight", facecolor=SURF)
print(f"median inter-chunk service {med_dt*1000:.0f} ms; wrote results/figures/{OUT}.png/pdf")
