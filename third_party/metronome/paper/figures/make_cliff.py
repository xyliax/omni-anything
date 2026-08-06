"""Two-panel diagnosis figure for Section 3 (replaces the separate burst + drift figures).
(a) 90 s burst: per-frame p50 is flat to N=160 for BOTH policies -- there is no short-burst
concurrency problem. (b) The SAME concurrencies over 300 s, pooling BOTH twenty-run batches
(fixed-order var_* + seeded randomized-order rvar_*): unbounded resident KV runs away to the
frame-budget wall in 14/20 runs (4/10 fixed-order day, 10/10 randomized day) while in-engine
windowed KV is flat in every run (0/20). Thin lines = individual runs, bold = per-policy median."""
import json, glob
import numpy as np
from nstyle import apply, VAN, WIN, LABEL_VAN, LABEL_WIN
import matplotlib.pyplot as plt

D = "../../results/sustained_fd"
BUCKET, BUDGET, DUR = 10.0, 2000.0, 300.0
EDGES = np.arange(0, DUR + BUCKET, BUCKET)
CENT = (EDGES[:-1] + EDGES[1:]) / 2
WALL = 500.0  # a run "drifted" if its end-of-session median exceeds this

def buckets(path):
    ev = json.load(open(path))["ev"]
    el = np.array([e[0] for e in ev]); la = np.array([e[1] for e in ev])
    out = np.full(len(CENT), np.nan); idx = np.digitize(el, EDGES) - 1
    for b in range(len(CENT)):
        m = idx == b
        if m.any(): out[b] = np.median(la[m])
    return out

def load_policy(prefixes):
    runs = []
    for pre in prefixes:
        for f in sorted(glob.glob(f"{D}/{pre}_r*_n*.json")):
            runs.append(buckets(f))
    return runs

apply()
fig, (axa, axb) = plt.subplots(1, 2, figsize=(6.6, 2.9),
                               gridspec_kw={"width_ratios": [1.0, 1.85], "wspace": 0.30})

# ---- (a) 90 s burst: flat for both, no concurrency problem ----
N = np.array([64, 96, 128, 160])
van_burst = np.array([2.0, 3.0, 3.0, 5.0])   # vanilla p50 (ms), measured fresh per N, 90 s
win_burst = np.array([2.1, 3.0, 3.1, 4.3])   # in-engine windowed p50 (ms), measured
axa.plot(N, van_burst, "o-", color=VAN, ms=5)
axa.plot(N, win_burst, "s-", color=WIN, ms=5)
axa.set_xlabel("concurrent sessions $N$")
axa.set_ylabel("per-frame $p_{50}$ (ms)")
axa.set_xticks(N); axa.set_ylim(0, 8)
axa.set_title("(a) 90 s burst: flat for both", fontsize=8.5)
axa.text(112, 6.9, "2 s budget $\\approx$400$\\times$\nabove this panel",
         color="0.45", fontsize=7.3, ha="center")

# ---- (b) same load, 300 s: both twenty-run batches pooled ----
policies = [
    (LABEL_VAN, ["var_van96", "var_van128", "rvar_van96", "rvar_van128"], VAN),
    (LABEL_WIN, ["var_ineng96", "var_ineng128", "rvar_ineng96", "rvar_ineng128"], WIN),
]
for label, prefixes, color in policies:
    runs = load_policy(prefixes)
    if not runs: continue
    drifted = sum(1 for r in runs if np.nanmedian(r[-3:]) > WALL)
    for r in runs:
        y = np.maximum(np.where(np.isnan(r), np.nan, r), 0.5)
        axb.plot(CENT, y, color=color, lw=0.7, alpha=0.25)
    med = np.nanmedian(np.vstack(runs), axis=0)
    axb.plot(CENT, np.maximum(med, 0.5), color=color, lw=2.2, label=label)

axb.axhline(BUDGET, color="0.4", ls=":", lw=1.2)
# level labels live OUTSIDE the axes (right margin) so they never overlap the traces
axb.text(305, BUDGET, "2 s frame\nbudget", color="0.35", fontsize=7.3,
         ha="left", va="bottom", clip_on=False)
axb.text(305, 1500, "14/20 runs\nhit the wall", color=VAN, fontsize=7.6,
         ha="left", va="top", fontweight="bold", clip_on=False)
axb.set_yscale("log"); axb.set_xlim(0, 300); axb.set_ylim(0.8, 3600)
axb.set_xlabel("elapsed session time (s)")
axb.set_ylabel("per-frame latency (ms)")
axb.set_title("(b) same $N$, 300 s: wall in 14/20 vs 0/20 runs", fontsize=8.5)
axb.legend(fontsize=7.2, loc="upper left", bbox_to_anchor=(0.005, 0.985), framealpha=0.95)
axb.grid(True, which="both", ls=":", alpha=0.4)

fig.savefig("cliff.pdf")
fig.savefig("cliff.png", dpi=140)
print("wrote cliff.pdf")
for label, prefixes, _ in policies:
    runs = load_policy(prefixes)
    d = sum(1 for r in runs if np.nanmedian(r[-3:]) > WALL)
    print(f"  {label}: drifted {d}/{len(runs)}")
