"""Per-frame latency vs elapsed time (the minute-level memory wall). Bins each run's raw per-frame
events into 10 s buckets, plots median per-frame latency over the 300 s session: unbounded resident-KV
drifts into the frame-budget wall; in-engine windowed KV stays flat."""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

D = "../../results/sustained_fd"
BUCKET = 10.0
BUDGET = 2000.0

def curve(tag):
    d = json.load(open(os.path.join(D, tag + ".json")))
    ev = d["ev"]; dur = d.get("duration", 300.0)
    nb = int(np.ceil(dur / BUCKET))
    xs, ys = [], []
    for b in range(nb):
        lo, hi = b * BUCKET, (b + 1) * BUCKET
        lat = [l for (el, l, *_ ) in ev if lo <= el < hi]
        if lat:
            xs.append((lo + hi) / 2.0); ys.append(float(np.median(lat)))
    return np.array(xs), np.array(ys)

plt.figure(figsize=(6.4, 3.5))
series = [
    ("long_vanilla_n96",  "Unbounded KV, N=96",        "#c0392b", "-",  "o"),
    ("longp_van_n128",    "Unbounded KV, N=128",       "#e67e22", "-",  "s"),
    ("ineng_long_n96",    "In-engine windowed KV, N=96",  "#2471a3", "--", "^"),
    ("longp_ineng_n128",  "In-engine windowed KV, N=128", "#1e8449", "--", "v"),
]
for tag, label, color, ls, mk in series:
    try:
        x, y = curve(tag)
        plt.plot(x, np.maximum(y, 0.5), color=color, ls=ls, marker=mk, ms=3.5,
                 lw=1.6, label=label, markevery=3)
    except FileNotFoundError:
        pass

plt.axhline(BUDGET, color="0.4", ls=":", lw=1.2)
plt.text(150, BUDGET * 1.12, "2 s frame budget", color="0.35", fontsize=8, ha="center")
plt.yscale("log")
plt.xlabel("elapsed session time (s)")
plt.ylabel("per-frame latency (ms, median per 10 s)")
plt.xlim(0, 300)
plt.ylim(0.8, 3000)
plt.legend(fontsize=8, loc="center left", framealpha=0.9)
plt.grid(True, which="both", ls=":", alpha=0.4)
plt.tight_layout()
plt.savefig("drift_curve.pdf", bbox_inches="tight")
plt.savefig("drift_curve.png", dpi=140, bbox_inches="tight")
print("wrote drift_curve.pdf / .png")
