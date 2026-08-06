"""Fig: the collapse mechanism, measured by an in-engine stat logger. Two stacked panels share
the session-time axis. TOP: KV-pool occupancy -- vanilla climbs to ~1.0 (pool saturates) while the
in-engine window plateaus at ~0.25 (blocks freed at the window boundary). BOTTOM: running vs waiting
request counts -- at saturation vanilla's running count collapses to 0 and all N sessions move to the
waiting queue (a hard scheduler stall); the windowed policy holds the full N running for the whole run.
This is the direct evidence that the trigger is KV-cache MEMORY exhaustion, not a compute drift."""
import numpy as np
from nstyle import apply, VAN, WIN, GREY, DARK, LABEL_VAN, LABEL_WIN
import matplotlib.pyplot as plt

def load(path):
    t, kv, run, wait = [], [], [], []
    for line in open(path):
        p = line.split()
        if len(p) < 4:
            continue
        t.append(float(p[0])); kv.append(float(p[1].split("=")[1]))
        run.append(int(p[2].split("=")[1])); wait.append(int(p[3].split("=")[1]))
    return np.array(t), np.array(kv), np.array(run), np.array(wait)

def smooth(t, y, win=8.0):
    """rolling mean over a +-win/2 second window -- the per-tick counts swing 0<->N between
    frames (sessions are periodic), so we plot the local average concurrency."""
    out = np.empty_like(y, dtype=float)
    for i, ti in enumerate(t):
        m = np.abs(t - ti) <= win / 2
        out[i] = y[m].mean()
    return out

vt, vkv, vrun, vwait = load("../../results/preempt_stats_van.log")
wt, wkv, wrun, wwait = load("../../results/preempt_stats_win.log")

# vanilla sustained-stall onset: first time run=0 while pool is essentially full
stall = next((vt[i] for i in range(len(vt)) if vrun[i] == 0 and vkv[i] > 0.95), None)

apply()
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.6, 4.3), sharex=True,
                               gridspec_kw={"height_ratios": [1.05, 1.0], "hspace": 0.12})

# ---- TOP: KV-pool occupancy ----
ax1.axhline(1.0, color=DARK, ls="--", lw=1.0)
ax1.text(2, 1.0, "KV pool capacity", color=DARK, fontsize=7.5, va="bottom")
if stall is not None:
    ax1.axvspan(stall, vt.max(), color=VAN, alpha=0.07)
ax1.plot(vt, vkv, color=VAN, label=LABEL_VAN)
ax1.plot(wt, wkv, color=WIN, label=LABEL_WIN)
ax1.axhline(np.median(wkv[wt > 80]), color=WIN, ls=":", lw=1.0)
ax1.text(vt.max()-2, np.median(wkv[wt > 80])+0.02,
         f"plateau $\\approx${np.median(wkv[wt>80]):.2f}", color=WIN, fontsize=7.5, ha="right", va="bottom")
if stall is not None:
    ax1.annotate("pool saturates\n$\\rightarrow$ scheduler stall", xy=(stall-2, 0.97),
                 xytext=(stall-95, 0.80), color=VAN, fontsize=8, ha="center", va="center",
                 arrowprops=dict(arrowstyle="->", color=VAN, lw=1.0))
ax1.set_ylabel("KV-pool occupancy")
ax1.set_ylim(0, 1.12); ax1.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
# one legend for both panels (same two policies, same colors throughout)
ax1.legend(loc="center left", bbox_to_anchor=(0.005, 0.42))

# ---- BOTTOM: waiting-queue depth (smoothed) -- the stall signal ----
# colors identify the same two policies as the top panel; no second legend
if stall is not None:
    ax2.axvspan(stall, vt.max(), color=VAN, alpha=0.07)
ax2.axhline(128, color=GREY, ls="--", lw=0.9)
ax2.text(2, 124, "$N$=128 sessions", color=GREY, fontsize=7.5, va="top")
ax2.plot(vt, smooth(vt, vwait), color=VAN)
ax2.plot(wt, smooth(wt, wwait), color=WIN)
if stall is not None:
    ax2.annotate("all $N$ sessions queued\n(scheduler stalled)", xy=(stall+30, 120),
                 xytext=(stall-118, 80), color=VAN, fontsize=8, ha="left",
                 arrowprops=dict(arrowstyle="->", color=VAN, lw=1.0))
ax2.set_ylabel("waiting requests")
ax2.set_xlabel("elapsed session time (s)")
ax2.set_xlim(0, min(vt.max(), wt.max())); ax2.set_ylim(-4, 140)

fig.savefig("kvpool.pdf")
fig.savefig("kvpool.png", dpi=140)
print(f"wrote kvpool.pdf  (vanilla peak kv={vkv.max():.3f}, stall@{stall:.0f}s; windowed plateau={np.median(wkv[wt>80]):.3f})")
