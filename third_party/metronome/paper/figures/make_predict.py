"""Fig: the cliff is predictable, and bounded state turns memory into a linear budget.
(a) Vanilla pool fill is linear in time: a straight-line fit on the early trace predicts the
saturation instant within a few percent on the 30B, ~13% on MiniCPM (30B N=128 pred 145s vs 148s stall;
MiniCPM N=96 pred 99s vs 114s stall). Windowed traces plateau far below capacity.
(b) Windowed plateau occupancy is linear in N (~0.2% of pool per session, W=1024): memory
becomes a budget you can provision, with an absolute ceiling ~500 sessions -- well above the
deadline-schedulable N*~209 that admission discovers, so compute (the deadline) binds first.
Data: results/preempt_stats_{van,win}.log, results/mcpm_stats_{van,win}.log,
results/ceil_stats_n{192,256}.log."""
import numpy as np
import matplotlib.pyplot as plt
from nstyle import apply, VAN, WIN, AMBER, GREY, DARK, LABEL_VAN, LABEL_WIN

def load(path):
    t, kv, run, wait = [], [], [], []
    for line in open(path):
        p = line.split()
        if len(p) < 4:
            continue
        t.append(float(p[0])); kv.append(float(p[1].split("=")[1]))
        run.append(int(p[2].split("=")[1])); wait.append(int(p[3].split("=")[1]))
    return np.array(t), np.array(kv), np.array(run), np.array(wait)

R = "../../results"
v30t, v30kv, v30run, _ = load(f"{R}/preempt_stats_van.log")
w30t, w30kv, _, _      = load(f"{R}/preempt_stats_win.log")
vmt, vmkv, vmrun, _    = load(f"{R}/mcpm_stats_van.log")
wmt, wmkv, _, _        = load(f"{R}/mcpm_stats_win.log")

def fit_and_pred(t, kv):
    m = (kv > 0.10) & (kv < 0.80)
    r, b = np.polyfit(t[m], kv[m], 1)
    return r, b, (1.0 - b) / r

def stall_time(t, kv, run):
    return next((t[i] for i in range(len(t)) if run[i] == 0 and kv[i] > 0.95), None)

r30, b30, pred30 = fit_and_pred(v30t, v30kv)
rm, bm, predm = fit_and_pred(vmt, vmkv)
stall30 = stall_time(v30t, v30kv, v30run)
stallm = stall_time(vmt, vmkv, vmrun)

apply()
fig, (ax, axb) = plt.subplots(1, 2, figsize=(7.2, 2.75), gridspec_kw={"width_ratios": [1.25, 1.0]})

# ---- (a) linear fill predicts saturation ----
XMAX = 300
ax.axhline(1.0, color=DARK, ls="--", lw=0.9)
ax.text(297, 1.015, "pool capacity", color=DARK, fontsize=7.5, ha="right", va="bottom")
# vanilla traces + extrapolated fits
ax.plot(v30t[v30t <= XMAX], v30kv[v30t <= XMAX], color=VAN, lw=1.8,
        label="unbounded, 30B ($N{=}128$)")
ax.plot(vmt[vmt <= XMAX], vmkv[vmt <= XMAX], color=VAN, lw=1.4, ls="--",
        label="unbounded, MiniCPM ($N{=}96$)")
for r, b, pred, stall in [(r30, b30, pred30, stall30), (rm, bm, predm, stallm)]:
    xs = np.linspace(0, pred, 40)
    ax.plot(xs, r * xs + b, color=GREY, lw=0.9, ls=":", zorder=1)
    ax.plot([pred], [1.0], marker="o", mfc="white", mec=DARK, ms=6, zorder=5)
    if stall is not None:
        ax.plot([stall], [1.0], marker="x", color=DARK, ms=7, mew=1.6, zorder=5)
# windowed traces
ax.plot(w30t[w30t <= XMAX], w30kv[w30t <= XMAX], color=WIN, lw=1.8,
        label="windowed, 30B ($N{=}128$)")
ax.plot(wmt[wmt <= XMAX], wmkv[wmt <= XMAX], color=WIN, lw=1.4, ls="--",
        label="windowed, MiniCPM ($N{=}96$)")
ax.annotate("$\\circ$ predicted / $\\times$ measured stall", xy=(0.99, 0.06),
            xycoords="axes fraction", fontsize=7.5, color=DARK, ha="right")
ax.set_xlabel("elapsed session time (s)")
ax.set_ylabel("KV-pool occupancy")
ax.set_xlim(0, XMAX); ax.set_ylim(0, 1.12)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
ax.legend(loc="center right", fontsize=6.8, handlelength=2.2, borderaxespad=0.3)
ax.set_title("(a) linear fill $\\Rightarrow$ saturation time is predictable", fontsize=9)

# ---- (b) windowed plateau is linear in N ----
def plateau(t, kv):
    return float(np.median(kv[t > 0.5 * t.max()]) * 100)

n192t, n192kv, _, _ = load(f"{R}/ceil_stats_n192.log")
n256t, n256kv, _, _ = load(f"{R}/ceil_stats_n256.log")
Ns = np.array([128, 192, 256])
pls = np.array([plateau(w30t, w30kv), plateau(n192t, n192kv), plateau(n256t, n256kv)])
a, c = np.polyfit(Ns, pls, 1)
nmax = (100 - c) / a
nstar = 209

axb.axhline(100, color=DARK, ls="--", lw=0.9)
axb.text(8, 101.5, "pool capacity", color=DARK, fontsize=7.5, va="bottom")
xs = np.linspace(0, nmax * 1.04, 50)
axb.plot(xs, a * xs + c, color=GREY, lw=0.9, ls=":")
axb.plot(Ns, pls, "o", color=WIN, ms=6, zorder=5, label="measured plateau ($W{=}1024$)")
axb.plot([nmax], [100], marker="o", mfc="white", mec=DARK, ms=6, zorder=5)
axb.annotate(f"memory ceiling\n$N_{{\\max}}\\approx{nmax:.0f}$", xy=(nmax, 100),
             xytext=(nmax - 150, 78), fontsize=7.5, color=DARK,
             arrowprops=dict(arrowstyle="->", color=DARK, lw=0.9))
axb.axvline(nstar, color=AMBER, lw=1.2, ls="--")
axb.text(nstar - 12, 55, "deadline binds first:\nadmission $N^\\star\\!\\approx\\!209$",
         color=AMBER, fontsize=7.5, ha="right")
axb.set_xlabel("concurrent sessions $N$")
axb.set_ylabel("plateau occupancy (%)")
axb.set_xlim(0, 560); axb.set_ylim(0, 112)
axb.legend(loc="upper left", fontsize=7.0)
axb.set_title("(b) bounded state: memory is a linear budget", fontsize=9)

fig.tight_layout()
fig.savefig("predict.pdf"); fig.savefig("predict.png", dpi=160)
print(f"wrote predict.pdf  30B pred={pred30:.0f}s stall={stall30:.0f}s | "
      f"MiniCPM pred={predm:.0f}s stall={stallm:.0f}s | plateau {a:.4f}%/N ceiling {nmax:.0f}")
